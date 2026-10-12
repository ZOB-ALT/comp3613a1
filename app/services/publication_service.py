from dataclasses import dataclass
from math import cos, pi, sin

from app.repositories.publication import PublicationRepository
from app.models.publication import Author, Publication, Publisher
from app.schemas.publication import PublicationForm
from app.utilities.pagination import Pagination


@dataclass(frozen=True)
class AuthorGraphNode:
    author: Author
    label: str
    x: float
    y: float
    publications: list[Publication]
    is_publication_author: bool
    matches_search: bool


@dataclass(frozen=True)
class AuthorGraphEdge:
    source_id: int
    target_id: int
    x1: float
    y1: float
    x2: float
    y2: float
    shared_publication_count: int


@dataclass(frozen=True)
class AuthorGraphData:
    nodes: list[AuthorGraphNode]
    edges: list[AuthorGraphEdge]
    publications: list[Publication]
    selected_publication_id: int | None
    initial_author_id: int | None
    author_query: str
    highlighted_author_count: int


class AuthorProfileRequiredError(Exception):
    pass


class PublicationFormError(ValueError):
    pass


class AuthorGraphPublicationNotFoundError(Exception):
    pass


class PublicationService:
    def __init__(self, publication_repo: PublicationRepository):
        self.publication_repo = publication_repo

    def search_publications(
        self,
        query: str,
        year: int | None,
        page: int,
        author_id: int | None = None,
    ) -> tuple[list[Publication], Pagination]:
        return self.publication_repo.search_publications(
            query=query,
            year=year,
            page=page,
            author_id=author_id,
        )

    def list_publication_years(self) -> list[int]:
        return self.publication_repo.list_years()

    def list_author_publications(self, user_id: int) -> list[Publication]:
        self.require_author_profile(user_id)
        return self.publication_repo.get_by_primary_author(user_id)

    def get_publication_details(self, publication_id: int) -> Publication | None:
        return self.publication_repo.get_by_id_with_related(publication_id)

    def get_author_by_id(self, author_id: int) -> Author | None:
        return self.publication_repo.get_author_by_id(author_id)

    def get_author_graph(
        self,
        publication_id: int | None,
        author_query: str,
    ) -> AuthorGraphData:
        authors, publications = self.publication_repo.get_author_graph_sources()
        publication_ids = {publication.id for publication in publications}
        if publication_id is not None and publication_id not in publication_ids:
            raise AuthorGraphPublicationNotFoundError

        author_publications: dict[int, list[Publication]] = {}
        for author in authors:
            if author.id is None:
                continue
            author_publications[author.id] = sorted(
                (
                    credit.publication
                    for credit in author.authored_records
                    if credit.publication.id is not None
                ),
                key=lambda publication: publication.title.casefold(),
            )

        graph_authors = [
            author
            for author in authors
            if author.id is not None and author_publications.get(author.id)
        ]
        selected_author_ids = {
            author.id
            for author in graph_authors
            if author.id is not None
            and any(
                publication.id == publication_id
                for publication in author_publications[author.id]
            )
        }
        normalized_query = author_query.strip().casefold()
        matching_author_ids = (
            {
                author.id
                for author in graph_authors
                if author.id is not None
                and normalized_query
                in f"{author.first_name} {author.last_name}".casefold()
            }
            if normalized_query
            else set()
        )

        positions: dict[int, tuple[float, float]] = {}
        total = len(graph_authors)
        for index, author in enumerate(graph_authors):
            if author.id is None:
                continue
            if total == 1:
                x, y = 450.0, 250.0
            else:
                angle = (2 * pi * index / total) - (pi / 2)
                x = 450.0 + 310.0 * cos(angle)
                y = 250.0 + 175.0 * sin(angle)
            positions[author.id] = (x, y)

        nodes = [
            AuthorGraphNode(
                author=author,
                label=f"{author.last_name} {author.first_name[:1]}.",
                x=positions[author.id][0],
                y=positions[author.id][1],
                publications=author_publications[author.id],
                is_publication_author=author.id in selected_author_ids,
                matches_search=author.id in matching_author_ids,
            )
            for author in graph_authors
            if author.id is not None
        ]

        edges: list[AuthorGraphEdge] = []
        for source_index, source in enumerate(graph_authors):
            if source.id is None:
                continue
            source_publications = {
                publication.id
                for publication in author_publications[source.id]
            }
            for target in graph_authors[source_index + 1 :]:
                if target.id is None:
                    continue
                shared_publications = source_publications.intersection(
                    publication.id
                    for publication in author_publications[target.id]
                )
                if not shared_publications:
                    continue
                x1, y1 = positions[source.id]
                x2, y2 = positions[target.id]
                edges.append(
                    AuthorGraphEdge(
                        source_id=source.id,
                        target_id=target.id,
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        shared_publication_count=len(shared_publications),
                    )
                )

        matching_nodes = [
            node for node in nodes if node.matches_search
        ]
        initial_author_id = (
            matching_nodes[0].author.id
            if normalized_query and matching_nodes
            else (
                None
                if normalized_query
                else (nodes[0].author.id if nodes else None)
            )
        )
        return AuthorGraphData(
            nodes=nodes,
            edges=edges,
            publications=publications,
            selected_publication_id=publication_id,
            initial_author_id=initial_author_id,
            author_query=author_query,
            highlighted_author_count=len(
                selected_author_ids | matching_author_ids
            ),
        )

    def require_author_profile(self, user_id: int) -> Author:
        author = self.publication_repo.get_author_by_user_id(user_id)
        if author is None:
            raise AuthorProfileRequiredError(
                "An author profile is required to manage publications."
            )
        return author

    def get_editable_publication(
        self,
        publication_id: int,
        user_id: int,
    ) -> Publication | None:
        self.require_author_profile(user_id)
        return self.publication_repo.get_managed_publication(
            publication_id=publication_id,
            user_id=user_id,
        )

    def get_management_form_options(
        self,
        user_id: int,
        exclude_publication_id: int | None = None,
    ) -> tuple[Author, list[Author], list[Publisher], list[Publication]]:
        current_author = self.require_author_profile(user_id)
        return (
            current_author,
            self.publication_repo.list_authors(),
            self.publication_repo.list_publishers(),
            self.publication_repo.list_citation_candidates(
                exclude_publication_id=exclude_publication_id
            ),
        )

    def create_publication(
        self,
        user_id: int,
        data: PublicationForm,
    ) -> Publication:
        current_author = self.require_author_profile(user_id)
        if current_author.id is None:
            raise RuntimeError("Author profile is missing its identifier.")
        author_ids = list(dict.fromkeys((current_author.id, *data.author_ids)))
        data = data.model_copy(update={"author_ids": author_ids})
        self._validate_form(data)
        return self.publication_repo.create_publication(data)

    def update_publication(
        self,
        publication_id: int,
        user_id: int,
        data: PublicationForm,
    ) -> Publication | None:
        self.require_author_profile(user_id)
        publication = self.publication_repo.get_managed_publication(
            publication_id=publication_id,
            user_id=user_id,
        )
        if publication is None:
            return None
        self._validate_form(data, exclude_publication_id=publication_id)
        return self.publication_repo.update_publication(publication, data)

    def delete_publication(self, publication_id: int, user_id: int) -> bool:
        self.require_author_profile(user_id)
        publication = self.publication_repo.get_managed_publication(
            publication_id=publication_id,
            user_id=user_id,
        )
        if publication is None:
            return False
        self.publication_repo.delete_publication(publication)
        return True

    def _validate_form(
        self,
        data: PublicationForm,
        exclude_publication_id: int | None = None,
    ) -> None:
        required_text = (
            data.title,
            data.abstract,
            data.doi,
            data.journal,
            data.conference,
            data.keywords,
        )
        if any(not value.strip() for value in required_text):
            raise PublicationFormError("Complete all required publication fields.")
        if not data.author_ids:
            raise PublicationFormError("A publication must have at least one author.")
        if len(data.author_ids) != len(set(data.author_ids)):
            raise PublicationFormError("An author can only be listed once.")
        if len(data.citation_ids) != len(set(data.citation_ids)):
            raise PublicationFormError("A citation can only be listed once.")
        if not self.publication_repo.publisher_exists(data.publisher_id):
            raise PublicationFormError("Select a valid publisher.")
        if self.publication_repo.author_ids_exist(data.author_ids) != set(
            data.author_ids
        ):
            raise PublicationFormError("Select valid authors.")
        if self.publication_repo.publication_ids_exist(
            data.citation_ids,
            exclude_publication_id=exclude_publication_id,
        ) != set(data.citation_ids):
            raise PublicationFormError("Select valid citation targets.")
        if self.publication_repo.doi_is_in_use(
            data.doi.strip(),
            exclude_publication_id=exclude_publication_id,
        ):
            raise PublicationFormError("That DOI is already in use.")
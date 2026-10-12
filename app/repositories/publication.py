import logging

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.publication import (
    Author,
    Authored,
    Citation,
    Publication,
    Publisher,
)
from app.schemas.publication import PublicationForm
from app.utilities.pagination import Pagination

logger = logging.getLogger(__name__)


class PublicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_publications(
        self,
        query: str,
        year: int | None,
        page: int,
        limit: int = 10,
        author_id: int | None = None,
    ) -> tuple[list[Publication], Pagination]:
        conditions = []
        if query.strip():
            term = f"%{query.strip()}%"
            conditions.append(
                or_(
                    Publication.title.ilike(term),
                    Publication.abstract.ilike(term),
                    Publication.doi.ilike(term),
                    Publication.keywords.ilike(term),
                    Publication.journal.ilike(term),
                    Publication.conference.ilike(term),
                )
            )
        if year is not None:
            conditions.append(Publication.year == year)
        if author_id is not None:
            conditions.append(
                Publication.authored_records.any(Authored.author_id == author_id)
            )

        total_count = self.db.exec(
            select(func.count(Publication.id)).where(*conditions)
        ).one()
        statement = (
            select(Publication)
            .options(
                selectinload(Publication.authored_records).selectinload(
                    Authored.author
                )
            )
            .where(*conditions)
            .order_by(Publication.title)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        publications = self.db.exec(statement).all()
        pagination = Pagination(
            total_count=total_count,
            current_page=page,
            limit=limit,
        )
        return publications, pagination

    def list_years(self) -> list[int]:
        return self.db.exec(
            select(Publication.year).distinct().order_by(Publication.year.desc())
        ).all()

    def get_by_primary_author(self, user_id: int) -> list[Publication]:
        statement = (
            select(Publication)
            .join(Authored)
            .join(Author)
            .where(
                Author.user_id == user_id,
                Authored.position == 1,
            )
            .distinct()
            .order_by(Publication.title)
        )
        return self.db.exec(statement).all()

    def get_author_by_user_id(self, user_id: int) -> Author | None:
        return self.db.exec(
            select(Author).where(Author.user_id == user_id)
        ).one_or_none()

    def get_author_by_id(self, author_id: int) -> Author | None:
        return self.db.get(Author, author_id)

    def get_managed_publication(
        self,
        publication_id: int,
        user_id: int,
    ) -> Publication | None:
        statement = (
            select(Publication)
            .join(Authored)
            .join(Author)
            .options(
                selectinload(Publication.authored_records).selectinload(
                    Authored.author
                ),
                selectinload(Publication.citations_made).selectinload(
                    Citation.cited_publication
                ),
            )
            .where(
                Publication.id == publication_id,
                Author.user_id == user_id,
                Authored.position == 1,
            )
        )
        return self.db.exec(statement).one_or_none()

    def list_publishers(self) -> list[Publisher]:
        return self.db.exec(select(Publisher).order_by(Publisher.name)).all()

    def list_authors(self) -> list[Author]:
        return self.db.exec(
            select(Author).order_by(Author.last_name, Author.first_name)
        ).all()

    def get_author_graph_sources(self) -> tuple[list[Author], list[Publication]]:
        authors = self.db.exec(
            select(Author)
            .options(
                selectinload(Author.authored_records).selectinload(
                    Authored.publication
                )
            )
            .order_by(Author.last_name, Author.first_name)
        ).all()
        publications = self.db.exec(
            select(Publication).order_by(Publication.title)
        ).all()
        return authors, publications

    def list_citation_candidates(
        self,
        exclude_publication_id: int | None = None,
    ) -> list[Publication]:
        statement = select(Publication)
        if exclude_publication_id is not None:
            statement = statement.where(Publication.id != exclude_publication_id)
        return self.db.exec(statement.order_by(Publication.title)).all()

    def publisher_exists(self, publisher_id: int) -> bool:
        return self.db.exec(
            select(Publisher.id).where(Publisher.id == publisher_id)
        ).first() is not None

    def author_ids_exist(self, author_ids: list[int]) -> set[int]:
        if not author_ids:
            return set()
        return set(
            self.db.exec(
                select(Author.id).where(Author.id.in_(author_ids))
            ).all()
        )

    def publication_ids_exist(
        self,
        publication_ids: list[int],
        exclude_publication_id: int | None = None,
    ) -> set[int]:
        if not publication_ids:
            return set()
        statement = select(Publication.id).where(
            Publication.id.in_(publication_ids)
        )
        if exclude_publication_id is not None:
            statement = statement.where(Publication.id != exclude_publication_id)
        return set(self.db.exec(statement).all())

    def doi_is_in_use(self, doi: str, exclude_publication_id: int | None = None) -> bool:
        statement = select(Publication.id).where(Publication.doi == doi)
        if exclude_publication_id is not None:
            statement = statement.where(Publication.id != exclude_publication_id)
        return self.db.exec(statement).first() is not None

    def create_publication(self, data: PublicationForm) -> Publication:
        publication = Publication(
            title=data.title.strip(),
            abstract=data.abstract.strip(),
            doi=data.doi.strip(),
            publisher_id=data.publisher_id,
            journal=data.journal.strip(),
            conference=data.conference.strip(),
            year=data.year,
            keywords=data.keywords.strip(),
        )
        try:
            self.db.add(publication)
            self.db.flush()
            self._replace_authors(publication, data.author_ids)
            self._replace_citations(publication, data.citation_ids)
            self.db.commit()
            self.db.refresh(publication)
            return publication
        except SQLAlchemyError:
            logger.exception("Database error while creating publication")
            self.db.rollback()
            raise

    def update_publication(
        self,
        publication: Publication,
        data: PublicationForm,
    ) -> Publication:
        publication.title = data.title.strip()
        publication.abstract = data.abstract.strip()
        publication.doi = data.doi.strip()
        publication.publisher_id = data.publisher_id
        publication.journal = data.journal.strip()
        publication.conference = data.conference.strip()
        publication.year = data.year
        publication.keywords = data.keywords.strip()
        try:
            self._replace_authors(publication, data.author_ids)
            self._replace_citations(publication, data.citation_ids)
            self.db.commit()
            self.db.refresh(publication)
            return publication
        except SQLAlchemyError:
            logger.exception("Database error while updating publication")
            self.db.rollback()
            raise

    def delete_publication(self, publication: Publication) -> None:
        try:
            authored_records = self.db.exec(
                select(Authored).where(
                    Authored.publication_id == publication.id
                )
            ).all()
            citations = self.db.exec(
                select(Citation).where(
                    or_(
                        Citation.citing_publication_id == publication.id,
                        Citation.cited_publication_id == publication.id,
                    )
                )
            ).all()
            for authored_record in authored_records:
                self.db.delete(authored_record)
            for citation in citations:
                self.db.delete(citation)
            self.db.delete(publication)
            self.db.commit()
        except SQLAlchemyError:
            logger.exception("Database error while deleting publication")
            self.db.rollback()
            raise

    def _replace_authors(self, publication: Publication, author_ids: list[int]) -> None:
        if publication.id is None:
            raise RuntimeError("Publication must be saved before assigning authors.")
        for authored_record in self.db.exec(
            select(Authored).where(Authored.publication_id == publication.id)
        ).all():
            self.db.delete(authored_record)
        self.db.flush()
        publication.authored_records = [
            Authored(author_id=author_id, position=position)
            for position, author_id in enumerate(author_ids, start=1)
        ]

    def _replace_citations(
        self,
        publication: Publication,
        citation_ids: list[int],
    ) -> None:
        if publication.id is None:
            raise RuntimeError("Publication must be saved before assigning citations.")
        for citation in self.db.exec(
            select(Citation).where(
                Citation.citing_publication_id == publication.id
            )
        ).all():
            self.db.delete(citation)
        self.db.flush()
        publication.citations_made = [
            Citation(cited_publication_id=cited_publication_id)
            for cited_publication_id in citation_ids
        ]

    def get_by_id_with_related(self, publication_id: int) -> Publication | None:
        statement = (
            select(Publication)
            .options(
                selectinload(Publication.publisher),
                selectinload(Publication.authored_records).selectinload(
                    Authored.author
                ),
                selectinload(Publication.citations_made)
                .selectinload(Citation.cited_publication)
                .selectinload(Publication.authored_records)
                .selectinload(Authored.author),
            )
            .where(Publication.id == publication_id)
        )
        return self.db.exec(statement).one_or_none()

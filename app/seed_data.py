"""Idempotent sample research records for local development."""

from sqlmodel import select

from app.database import get_cli_session
from app.models.publication import Author, Authored, Citation, Publication, Publisher
from app.repositories.user import UserRepository
from app.schemas.user import RegularUserCreate
from app.utilities.security import encrypt_password


def seed_research_demo_data() -> None:
    publishers = (
        "Northstar Academic Press",
        "Cedar Grove Publishing",
        "Meridian Scholarly Press",
    )
    authors = (
        ("Amina", "Shah", "Westbridge University"),
        ("Theo", "Park", "Harbor Institute"),
        ("Mara", "Ellis", "Westbridge University"),
        ("Niko", "Reyes", "Meridian Research Lab"),
        ("Elise", "Laurent", "North Coast College"),
    )
    publications = (
        {
            "title": "Mapping Knowledge Networks in Open Research",
            "abstract": "This sample study explores how open bibliographic records reveal connections between research topics and their authors.",
            "doi": "10.5555/scholarnet.2021.001",
            "keywords": "open research, knowledge networks",
            "journal": "Journal of Research Systems",
            "conference": "Research Data Forum",
            "year": 2021,
            "publisher": publishers[0],
            "authors": (0, 1),
            "cites": (),
        },
        {
            "title": "Citation Contexts for Interdisciplinary Discovery",
            "abstract": "A fictional example examining how citation context can help readers move between neighboring research areas.",
            "doi": "10.5555/scholarnet.2021.002",
            "keywords": "citations, discovery",
            "journal": "Studies in Digital Scholarship",
            "conference": "Open Knowledge Symposium",
            "year": 2021,
            "publisher": publishers[1],
            "authors": (1, 2),
            "cites": (),
        },
        {
            "title": "Finding Related Work with Transparent Signals",
            "abstract": "This sample paper describes transparent metadata signals for presenting related scholarly publications.",
            "doi": "10.5555/scholarnet.2022.001",
            "keywords": "search, metadata, transparency",
            "journal": "Journal of Research Systems",
            "conference": "Research Data Forum",
            "year": 2022,
            "publisher": publishers[2],
            "authors": (0, 2),
            "cites": ("10.5555/scholarnet.2021.001",),
        },
        {
            "title": "Open Bibliographic Data at Scale",
            "abstract": "A fictional evaluation of practical approaches to organizing growing collections of public bibliographic data.",
            "doi": "10.5555/scholarnet.2022.002",
            "keywords": "bibliographic data, open access",
            "journal": "Library Systems Review",
            "conference": "Digital Libraries Workshop",
            "year": 2022,
            "publisher": publishers[0],
            "authors": (2, 3),
            "cites": ("10.5555/scholarnet.2021.001",),
        },
        {
            "title": "Author Identity Resolution for Digital Libraries",
            "abstract": "This sample study considers ways to distinguish researchers with similar names in digital library records.",
            "doi": "10.5555/scholarnet.2023.001",
            "keywords": "author identity, digital libraries",
            "journal": "Studies in Digital Scholarship",
            "conference": "Open Knowledge Symposium",
            "year": 2023,
            "publisher": publishers[1],
            "authors": (1, 3),
            "cites": ("10.5555/scholarnet.2021.002",),
        },
        {
            "title": "Evaluating Scholarly Search Interfaces",
            "abstract": "A fictional usability study comparing ways to help readers search and browse scholarly collections.",
            "doi": "10.5555/scholarnet.2023.002",
            "keywords": "scholarly search, usability",
            "journal": "Journal of Research Systems",
            "conference": "Humanities Computing Exchange",
            "year": 2023,
            "publisher": publishers[2],
            "authors": (0, 4),
            "cites": ("10.5555/scholarnet.2022.001",),
        },
        {
            "title": "Research Graphs for Emerging Fields",
            "abstract": "This sample paper illustrates how a graph of researchers and publications can make an emerging topic easier to explore.",
            "doi": "10.5555/scholarnet.2023.003",
            "keywords": "research graphs, collaboration",
            "journal": "Library Systems Review",
            "conference": "Digital Libraries Workshop",
            "year": 2023,
            "publisher": publishers[0],
            "authors": (2, 4),
            "cites": ("10.5555/scholarnet.2022.002",),
        },
        {
            "title": "Responsible Ranking of Academic Results",
            "abstract": "A fictional discussion of understandable ranking signals for publication search results.",
            "doi": "10.5555/scholarnet.2024.001",
            "keywords": "ranking, responsible computing",
            "journal": "Responsible Information Quarterly",
            "conference": "Open Knowledge Symposium",
            "year": 2024,
            "publisher": publishers[1],
            "authors": (3, 4),
            "cites": ("10.5555/scholarnet.2022.002",),
        },
        {
            "title": "Metadata Quality in Community Archives",
            "abstract": "This sample study explores how consistent descriptive metadata supports discovery in community-run archives.",
            "doi": "10.5555/scholarnet.2024.002",
            "keywords": "metadata, archives, discovery",
            "journal": "Studies in Digital Scholarship",
            "conference": "Humanities Computing Exchange",
            "year": 2024,
            "publisher": publishers[2],
            "authors": (0, 1, 4),
            "cites": ("10.5555/scholarnet.2023.002",),
        },
        {
            "title": "Patterns of Collaboration Across Disciplines",
            "abstract": "A fictional longitudinal example of how co-authorship patterns vary among connected areas of study.",
            "doi": "10.5555/scholarnet.2024.003",
            "keywords": "collaboration, co-authorship",
            "journal": "Journal of Research Systems",
            "conference": "Research Data Forum",
            "year": 2024,
            "publisher": publishers[0],
            "authors": (1, 3),
            "cites": ("10.5555/scholarnet.2023.001",),
        },
        {
            "title": "Explainable Citation Recommendations",
            "abstract": "This sample paper presents an illustrative approach to explaining why two publications may be related.",
            "doi": "10.5555/scholarnet.2025.001",
            "keywords": "citations, explainability",
            "journal": "Responsible Information Quarterly",
            "conference": "Digital Libraries Workshop",
            "year": 2025,
            "publisher": publishers[2],
            "authors": (2, 3, 4),
            "cites": ("10.5555/scholarnet.2024.001",),
        },
        {
            "title": "A Practical Guide to Publication Discovery",
            "abstract": "A fictional overview of search, filters, and author connections for a sample scholarly discovery platform.",
            "doi": "10.5555/scholarnet.2025.002",
            "keywords": "publication discovery, search",
            "journal": "Library Systems Review",
            "conference": "Humanities Computing Exchange",
            "year": 2025,
            "publisher": publishers[1],
            "authors": (0, 2, 4),
            "cites": (
                "10.5555/scholarnet.2024.002",
                "10.5555/scholarnet.2024.003",
            ),
        },
    )

    with get_cli_session() as session:
        user_repo = UserRepository(session)
        author_ids: list[int] = []
        for index, (first_name, last_name, affiliation) in enumerate(authors, start=1):
            username = f"scholar{index:02}"
            email = f"{username}@example.com"
            user = user_repo.get_by_username(username)
            if user is None:
                user = user_repo.create(
                    RegularUserCreate(
                        username=username,
                        email=email,
                        password=encrypt_password("scholarpass"),
                        role="author",
                    )
                )
            elif user.role != "author":
                raise ValueError(
                    f"Cannot seed author profile: {username} already exists "
                    "with a non-author role."
                )

            author = session.exec(
                select(Author).where(Author.user_id == user.id)
            ).one_or_none()
            if author is None:
                author = Author(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    affiliation=affiliation,
                    email=email,
                )
                session.add(author)
            session.flush()
            author_ids.append(author.id)

        publisher_ids: dict[str, int] = {}
        for name in publishers:
            publisher = session.exec(
                select(Publisher).where(Publisher.name == name)
            ).first()
            if publisher is None:
                publisher = Publisher(name=name)
                session.add(publisher)
            session.flush()
            publisher_ids[name] = publisher.id
        session.commit()

        publication_by_doi: dict[str, Publication] = {}
        created_publications = 0
        for data in publications:
            publication = session.exec(
                select(Publication).where(Publication.doi == data["doi"])
            ).one_or_none()
            if publication is None:
                publication = Publication(
                    publisher_id=publisher_ids[data["publisher"]],
                    title=data["title"],
                    abstract=data["abstract"],
                    doi=data["doi"],
                    keywords=data["keywords"],
                    journal=data["journal"],
                    conference=data["conference"],
                    year=data["year"],
                )
                session.add(publication)
                created_publications += 1
            publication_by_doi[data["doi"]] = publication
        session.flush()

        for data in publications:
            publication = publication_by_doi[data["doi"]]
            for position, author_index in enumerate(data["authors"], start=1):
                existing_credit = session.exec(
                    select(Authored).where(
                        Authored.publication_id == publication.id,
                        Authored.author_id == author_ids[author_index],
                    )
                ).one_or_none()
                if existing_credit is None:
                    session.add(
                        Authored(
                            publication_id=publication.id,
                            author_id=author_ids[author_index],
                            position=position,
                        )
                    )
            for cited_doi in data["cites"]:
                cited_publication = publication_by_doi[cited_doi]
                existing_citation = session.exec(
                    select(Citation).where(
                        Citation.citing_publication_id == publication.id,
                        Citation.cited_publication_id == cited_publication.id,
                    )
                ).one_or_none()
                if existing_citation is None:
                    session.add(
                        Citation(
                            citing_publication_id=publication.id,
                            cited_publication_id=cited_publication.id,
                        )
                    )
        session.commit()

    print(
        "Research sample data ensured — "
        f"{created_publications} publication(s) created; safe to rerun."
    )

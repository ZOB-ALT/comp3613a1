from datetime import datetime, timezone

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Publisher(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    publications: list["Publication"] = Relationship(back_populates="publisher")


class Author(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    first_name: str
    last_name: str
    affiliation: str | None = None
    email: str
    authored_records: list["Authored"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Publication(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    publisher_id: int = Field(foreign_key="publisher.id")
    title: str = Field(index=True)
    abstract: str = Field(sa_column=Column(Text, nullable=False))
    doi: str = Field(unique=True, index=True)
    keywords: str
    journal: str
    conference: str
    year: int = Field(index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    publisher: Publisher = Relationship(back_populates="publications")
    authored_records: list["Authored"] = Relationship(
        back_populates="publication"
    )
    citations_made: list["Citation"] = Relationship(
        back_populates="citing_publication",
        sa_relationship_kwargs={"foreign_keys": "Citation.citing_publication_id"},
    )
    citations_received: list["Citation"] = Relationship(
        back_populates="cited_publication",
        sa_relationship_kwargs={"foreign_keys": "Citation.cited_publication_id"},
    )


class Authored(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("publication_id", "author_id", name="uq_authored_pair"),
    )

    id: int | None = Field(default=None, primary_key=True)
    publication_id: int = Field(foreign_key="publication.id")
    author_id: int = Field(foreign_key="author.id")
    position: int = Field(ge=1)
    publication: Publication = Relationship(back_populates="authored_records")
    author: Author = Relationship(back_populates="authored_records")


class Citation(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "citing_publication_id",
            "cited_publication_id",
            name="uq_citation_pair",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    citing_publication_id: int = Field(foreign_key="publication.id")
    cited_publication_id: int = Field(foreign_key="publication.id")
    citing_publication: Publication = Relationship(
        back_populates="citations_made",
        sa_relationship_kwargs={"foreign_keys": "Citation.citing_publication_id"},
    )
    cited_publication: Publication = Relationship(
        back_populates="citations_received",
        sa_relationship_kwargs={"foreign_keys": "Citation.cited_publication_id"},
    )
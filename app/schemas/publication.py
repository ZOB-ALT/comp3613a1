from pydantic import BaseModel, Field


class PublicationForm(BaseModel):
    title: str
    abstract: str
    doi: str
    publisher_id: int = Field(gt=0)
    journal: str
    conference: str
    year: int = Field(ge=1000, le=9999)
    keywords: str
    author_ids: list[int] = Field(default_factory=list)
    citation_ids: list[int] = Field(default_factory=list)

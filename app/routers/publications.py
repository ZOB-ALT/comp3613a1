from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.dependencies.session import SessionDep
from app.repositories.publication import PublicationRepository
from app.services.publication_service import (
    AuthorGraphPublicationNotFoundError,
    PublicationService,
)
from . import router, templates


@router.get("/publications", response_class=HTMLResponse, name="browse_publications")
async def browse_publications(
    request: Request,
    db: SessionDep,
    query: str = "",
    year: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    author_id: int | None = Query(default=None, gt=0),
):
    selected_year = None
    if year:
        try:
            selected_year = int(year)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail="Year filter must be a valid integer.",
            ) from exc

    publication_repo = PublicationRepository(db)
    publication_service = PublicationService(publication_repo)
    author_filter = (
        publication_service.get_author_by_id(author_id)
        if author_id is not None
        else None
    )
    if author_id is not None and author_filter is None:
        raise HTTPException(status_code=404, detail="Author not found.")
    publications, pagination = publication_service.search_publications(
        query=query,
        year=selected_year,
        page=page,
        author_id=author_id,
    )
    years = publication_service.list_publication_years()
    return templates.TemplateResponse(
        request=request,
        name="publications/browse.html",
        context={
            "publications": publications,
            "pagination": pagination,
            "query": query,
            "year": selected_year,
            "years": years,
            "author_id": author_id,
            "author_filter": author_filter,
        },
    )


@router.get(
    "/publications/{publication_id}",
    response_class=HTMLResponse,
    name="publication_details",
)
async def publication_details(
    publication_id: int,
    request: Request,
    db: SessionDep,
):
    publication_repo = PublicationRepository(db)
    publication_service = PublicationService(publication_repo)
    publication = publication_service.get_publication_details(publication_id)
    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found.")

    return templates.TemplateResponse(
        request=request,
        name="publications/details.html",
        context={"publication": publication},
    )


@router.get(
    "/authors/graph",
    response_class=HTMLResponse,
    name="author_graph",
)
async def author_graph(
    request: Request,
    db: SessionDep,
    publication_id: str | None = Query(default=None),
    author_query: str = Query(default=""),
):
    selected_publication_id = None
    if publication_id:
        try:
            selected_publication_id = int(publication_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail="Publication filter must be a valid integer.",
            ) from exc
        if selected_publication_id <= 0:
            raise HTTPException(
                status_code=422,
                detail="Publication filter must be a positive integer.",
            )

    publication_repo = PublicationRepository(db)
    publication_service = PublicationService(publication_repo)
    try:
        graph_data = publication_service.get_author_graph(
            publication_id=selected_publication_id,
            author_query=author_query,
        )
    except AuthorGraphPublicationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Publication not found.",
        ) from exc
    return templates.TemplateResponse(
        request=request,
        name="publications/author_graph.html",
        context={
            "graph_data": graph_data,
            "publication_id": selected_publication_id,
            "author_query": author_query,
        },
    )
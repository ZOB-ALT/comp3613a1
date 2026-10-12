from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.models.publication import Publication
from app.repositories.publication import PublicationRepository
from app.schemas.publication import PublicationForm
from app.services.publication_service import (
    AuthorProfileRequiredError,
    PublicationFormError,
    PublicationService,
)
from app.utilities.flash import flash
from . import router, templates


def _form_context(
    publication_service: PublicationService,
    user_id: int,
    publication: Publication | None = None,
) -> dict[str, object]:
    try:
        current_author, authors, publishers, citation_candidates = (
            publication_service.get_management_form_options(
                user_id=user_id,
                exclude_publication_id=publication.id if publication else None,
            )
        )
    except AuthorProfileRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if publication is None:
        selected_authors = [current_author]
        selected_citations = []
        selected_publisher_id = None
    else:
        selected_authors = [
            credit.author
            for credit in sorted(
                publication.authored_records,
                key=lambda credit: credit.position,
            )
        ]
        selected_citations = [
            citation.cited_publication
            for citation in publication.citations_made
        ]
        selected_publisher_id = publication.publisher_id

    return {
        "publication": publication,
        "current_author": current_author,
        "authors": authors,
        "publishers": publishers,
        "citation_candidates": citation_candidates,
        "selected_authors": selected_authors,
        "selected_citations": selected_citations,
        "selected_publisher_id": selected_publisher_id,
        "pin_owner": publication is None,
    }


@router.get(
    "/manage/publications",
    response_class=HTMLResponse,
    name="manage_publications",
)
async def manage_publications_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    publication_service = PublicationService(PublicationRepository(db))
    try:
        publications = publication_service.list_author_publications(user.id)
    except AuthorProfileRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="publications/manage.html",
        context={"user": user, "publications": publications},
    )


@router.get(
    "/manage/publications/new",
    response_class=HTMLResponse,
    name="new_publication",
)
async def new_publication_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    publication_service = PublicationService(PublicationRepository(db))
    context = _form_context(publication_service, user.id)
    context["user"] = user
    return templates.TemplateResponse(
        request=request,
        name="publications/upload.html",
        context=context,
    )


@router.post("/manage/publications/new", name="create_publication")
async def create_publication_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    title: str = Form(...),
    abstract: str = Form(...),
    doi: str = Form(...),
    publisher_id: int = Form(..., gt=0),
    journal: str = Form(...),
    conference: str = Form(...),
    year: int = Form(..., ge=1000, le=9999),
    keywords: str = Form(...),
    author_ids: list[int] = Form(default=[]),
    citation_ids: list[int] = Form(default=[]),
):
    publication_service = PublicationService(PublicationRepository(db))
    form = PublicationForm(
        title=title,
        abstract=abstract,
        doi=doi,
        publisher_id=publisher_id,
        journal=journal,
        conference=conference,
        year=year,
        keywords=keywords,
        author_ids=author_ids,
        citation_ids=citation_ids,
    )
    try:
        publication_service.create_publication(user.id, form)
    except AuthorProfileRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except PublicationFormError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for("new_publication"),
            status_code=303,
        )

    flash(
        request,
        "Publication saved. Management access follows the first-listed author.",
    )
    return RedirectResponse(
        url=request.url_for("manage_publications"),
        status_code=303,
    )


@router.get(
    "/manage/publications/{publication_id}/edit",
    response_class=HTMLResponse,
    name="edit_publication",
)
async def edit_publication_view(
    publication_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    publication_service = PublicationService(PublicationRepository(db))
    try:
        publication = publication_service.get_editable_publication(
            publication_id=publication_id,
            user_id=user.id,
        )
    except AuthorProfileRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found.")

    context = _form_context(publication_service, user.id, publication)
    context["user"] = user
    return templates.TemplateResponse(
        request=request,
        name="publications/upload.html",
        context=context,
    )


@router.post(
    "/manage/publications/{publication_id}/edit",
    name="update_publication",
)
async def update_publication_action(
    publication_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    title: str = Form(...),
    abstract: str = Form(...),
    doi: str = Form(...),
    publisher_id: int = Form(..., gt=0),
    journal: str = Form(...),
    conference: str = Form(...),
    year: int = Form(..., ge=1000, le=9999),
    keywords: str = Form(...),
    author_ids: list[int] = Form(default=[]),
    citation_ids: list[int] = Form(default=[]),
):
    publication_service = PublicationService(PublicationRepository(db))
    form = PublicationForm(
        title=title,
        abstract=abstract,
        doi=doi,
        publisher_id=publisher_id,
        journal=journal,
        conference=conference,
        year=year,
        keywords=keywords,
        author_ids=author_ids,
        citation_ids=citation_ids,
    )
    try:
        publication = publication_service.update_publication(
            publication_id=publication_id,
            user_id=user.id,
            data=form,
        )
    except AuthorProfileRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except PublicationFormError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(
            url=request.url_for("edit_publication", publication_id=publication_id),
            status_code=303,
        )
    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found.")

    flash(
        request,
        "Publication saved. Management access follows the first-listed author.",
    )
    return RedirectResponse(
        url=request.url_for("manage_publications"),
        status_code=303,
    )


@router.post(
    "/manage/publications/{publication_id}/delete",
    name="delete_publication",
)
async def delete_publication_action(
    publication_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    publication_service = PublicationService(PublicationRepository(db))
    try:
        deleted = publication_service.delete_publication(
            publication_id=publication_id,
            user_id=user.id,
        )
    except AuthorProfileRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Publication not found.")

    flash(request, "Publication deleted.")
    return RedirectResponse(
        url=request.url_for("manage_publications"),
        status_code=303,
    )
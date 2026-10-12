from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from . import router


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
):
    return RedirectResponse(
        url=request.url_for("browse_publications"),
        status_code=303,
    )

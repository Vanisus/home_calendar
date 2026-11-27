import secrets
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status
)
from fastapi.security import APIKeyHeader

from app.schemas.admin_schemas import (
    SourceCreate,
    SourceUpdate,
    SourceRead
)

token_header = APIKeyHeader(name='X-Admin-Token', auto_error=False)

def require_admin(
        request: Request,
        token: str | None = Depends(token_header)
) -> None:
    expected = request.app.state.settings.admin_token.get_secret_value()

    if not token or not secrets.compare_digest(
            token.encode("utf-8"),
            expected.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


router = APIRouter(
    prefix="/admin/calendars",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

@router.get("", response_model=list[SourceRead])
async def list_sources(
        request: Request,
):
    return await request.app.state.sources.list_all()

@router.post("", response_model=SourceRead, status_code=201)
async def create_source(payload: SourceCreate, request: Request):
    row = await request.app.state.sources.create(
        name=payload.name,
        url=str(payload.url),
        color=payload.color,
    )
    request.app.state.calendar_service.request_refresh()
    return row

@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
        source_id: UUID,
        payload: SourceUpdate,
        request: Request,
):
    fields = payload.model_dump(exclude_none=True)

    if "url" in fields:
        fields["url"] = str(fields["url"])

    row = await request.app.state.sources.update(
        source_id=source_id,
        **fields
    )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    request.app.state.calendar_service.request_refresh()
    return row

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
        source_id: UUID,
        request: Request,
):
    if not await request.app.state.sources.delete(source_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    request.app.state.calendar_service.request_refresh()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

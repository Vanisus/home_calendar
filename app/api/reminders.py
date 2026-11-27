import secrets
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status
)
from fastapi.security import APIKeyHeader
from app.schemas.reminder_schemas import (
    DoneUpdate,
    ReminderCreate,
    ReminderUpdate,
    ReminderRead
)

display_header = APIKeyHeader(name='X-Display-Token', auto_error=False)

def require_display(
        request: Request,
        token: str | None = Depends(display_header)
) -> None:
    secret = request.app.state.settings.display_token
    if secret is None:
        return

    expected = secret.get_secret_value().encode("utf-8")
    if not token or not secrets.compare_digest(
            expected,
            token.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

router = APIRouter(
    prefix="/reminders",
    tags=["reminders"],
)

@router.get(
    "",
    response_model=list[ReminderRead]
)
async def list_reminders(
        request: Request,
        done_without_minutes: int = Query(default=0, ge=0, le=60),
):
    return await request.app.state.reminders.list_active(
        done_without_minutes=done_without_minutes
    )

@router.post(
    "",
    response_model=ReminderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_display)]
)
async def create_reminder(
        payload: ReminderCreate,
        request: Request,
):
    return await request.app.state.reminders.create(**payload.model_dump())

@router.patch(
    "/{reminder_id}",
    response_model=ReminderRead,
    dependencies=[Depends(require_display)]
)
async def update_reminder(
        reminder_id: UUID,
        payload: ReminderUpdate,
        request: Request,
):
    row = await request.app.state.reminders.update(
        reminder_id=reminder_id,
        **payload.model_dump(exclude_unset=True)
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

@router.patch(
    "/{reminder_id}/done",
    response_model=ReminderRead,
    dependencies=[Depends(require_display)]
)
async def set_done(
        reminder_id: UUID,
        payload: DoneUpdate,
        request: Request,
):
    row = await request.app.state.reminders.set_done(
        reminder_id,
        payload.done
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_display)]
)
async def delete_reminder(
        reminder_id: UUID,
        request: Request,
):
    if not await request.app.state.reminders.delete(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

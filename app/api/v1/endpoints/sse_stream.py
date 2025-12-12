from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.sse import sse_broadcaster
from app.core.auth import current_active_user
from app.models.user import UserDB

router = APIRouter()


@router.get("/stream-sse")
async def stream(current_user: UserDB = Depends(current_active_user)):
    return StreamingResponse(
        sse_broadcaster.subscribe(current_user.id, current_user.email), media_type="text/event-stream"
    )

import jwt
from fastapi import (
    APIRouter,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from app.core.security import decode_token
from app.services.realtime import realtime_manager

router = APIRouter(
    prefix="/realtime",
    tags=["Realtime"],
)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return

        organization_id = payload.get("org")

        if not organization_id:
            await websocket.close(code=1008)
            return

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ):
        await websocket.close(code=1008)
        return

    from uuid import UUID

    try:
        organization_uuid = UUID(
            organization_id
        )
    except ValueError:
        await websocket.close(code=1008)
        return

    await realtime_manager.connect(
        organization_uuid,
        websocket,
    )

    try:
        while True:
            message = await websocket.receive_text()

            if message == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        pass

    finally:
        await realtime_manager.disconnect(
            organization_uuid,
            websocket,
        )
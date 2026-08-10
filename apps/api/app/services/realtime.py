import asyncio
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class RealtimeManager:
    """
    Organization-scoped WebSocket connection manager.

    Each organization has its own set of connected clients.
    Events are only delivered to clients belonging to the
    same organization.
    """

    def __init__(self) -> None:
        self._connections: dict[
            UUID,
            set[WebSocket],
        ] = defaultdict(set)

        self._lock = asyncio.Lock()

    async def connect(
        self,
        organization_id: UUID,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        async with self._lock:
            self._connections[
                organization_id
            ].add(websocket)

    async def disconnect(
        self,
        organization_id: UUID,
        websocket: WebSocket,
    ) -> None:
        async with self._lock:
            connections = self._connections.get(
                organization_id
            )

            if not connections:
                return

            connections.discard(websocket)

            if not connections:
                self._connections.pop(
                    organization_id,
                    None,
                )

    async def broadcast_to_organization(
        self,
        organization_id: UUID,
        event: dict,
    ) -> None:
        async with self._lock:
            connections = list(
                self._connections.get(
                    organization_id,
                    set(),
                )
            )

        disconnected: list[WebSocket] = []

        for websocket in connections:
            try:
                await websocket.send_json(event)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            await self.disconnect(
                organization_id,
                websocket,
            )


realtime_manager = RealtimeManager()
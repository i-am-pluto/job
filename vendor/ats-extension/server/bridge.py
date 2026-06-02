"""WebSocket bridge between the MCP server and the ATS Chrome extension.

Same pattern as linkedin-extension's bridge, on port 8766. The MCP server
process owns the WS server on localhost:8766. The extension's service worker
dials in as a client. Commands are correlated by an `id` field.
"""

import asyncio
import json
import uuid
from typing import Any, Optional

import websockets

HOST = "127.0.0.1"
PORT = 8766


class Bridge:
    def __init__(self) -> None:
        self._client: Optional[Any] = None
        self._pending: dict[str, asyncio.Future] = {}
        self._server = None
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._client is not None

    async def ensure_started(self) -> None:
        if self._server is not None:
            return
        async with self._lock:
            if self._server is None:
                self._server = await websockets.serve(self._on_conn, HOST, PORT)

    async def _on_conn(self, conn) -> None:
        self._client = conn
        try:
            async for raw in conn:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                mid = msg.get("id")
                if mid and mid in self._pending:
                    fut = self._pending.pop(mid)
                    if not fut.done():
                        fut.set_result(msg)
        finally:
            if self._client is conn:
                self._client = None

    async def send(self, action: str, params: dict, timeout: float = 60.0) -> dict:
        await self.ensure_started()
        if not self._client:
            for _ in range(20):
                if self._client:
                    break
                await asyncio.sleep(0.25)
        if not self._client:
            return {"success": False, "error": "Extension not connected. "
                    "Load the ATS extension and ensure a Chrome window is open."}
        mid = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[mid] = fut
        try:
            await self._client.send(json.dumps({"id": mid, "action": action,
                                                "params": params}))
        except Exception as e:
            self._pending.pop(mid, None)
            return {"success": False, "error": f"Send failed: {e}"}

        try:
            reply = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(mid, None)
            return {"success": False, "error": f"Timed out after {timeout}s "
                    f"waiting for '{action}'."}

        if not reply.get("ok"):
            return {"success": False, "error": reply.get("error", "Unknown error")}
        return reply.get("data", {})


bridge = Bridge()

import json
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

async def emit_log(msg: str):
    await ws_manager.broadcast(json.dumps({"type": "log", "data": msg}))

async def emit_progress(done: int, total: int):
    await ws_manager.broadcast(json.dumps({"type": "progress", "data": {"done": done, "total": total}}))

async def emit_stage(stage: str):
    await ws_manager.broadcast(json.dumps({"type": "stage", "data": stage}))

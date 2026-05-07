import os
import sys
import time
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.services.ai_engine import ai_engine
from app.services.ws_manager import ws_manager
from app.services.analytics_service import analytics_service
from app.api.routers import system, projects, engine

app = FastAPI(title="Sport Seeker Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    ai_engine.start_loading()

    posthog_key = os.environ.get("POSTHOG_API_KEY", "")
    posthog_host = os.environ.get("POSTHOG_API_HOST", "https://us.i.posthog.com")
    app_version = os.environ.get("SPORT_SEEKER_APP_VERSION", "")
    build_number = os.environ.get("SPORT_SEEKER_BUILD_NUMBER", "")

    extra = {}
    if app_version:
        extra["app_version"] = app_version
    if build_number:
        extra["build_number"] = build_number

    analytics_service.init(posthog_key, posthog_host, extra_properties=extra)


def zombie_killer(parent_pid: int):
    while True:
        try:
            if sys.platform == 'win32':
                import psutil  # type: ignore
                if not psutil.pid_exists(parent_pid):
                    analytics_service.end_session("parent_process_died")
                    time.sleep(0.5)
                    os._exit(0)
            else:
                if os.getppid() != parent_pid and os.getppid() == 1:
                    analytics_service.end_session("parent_process_died")
                    time.sleep(0.5)
                    os._exit(0)
        except Exception:
            pass
        time.sleep(2)


parent_pid_str = os.environ.get("SPORT_SEEKER_PARENT_PID")
if parent_pid_str and parent_pid_str.isdigit():
    threading.Thread(target=zombie_killer, args=(int(parent_pid_str),), daemon=True).start()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


app.include_router(system.router)
app.include_router(projects.router)
app.include_router(engine.router)

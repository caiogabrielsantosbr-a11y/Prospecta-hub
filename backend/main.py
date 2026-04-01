"""
Plataforma Prospect — FastAPI Backend
Main entry point with WebSocket support for real-time task updates.
"""
import os
import sys
import asyncio
from contextlib import asynccontextmanager

# Fix para Python 3.12+ no Windows com Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import socketio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

from services.task_manager import task_manager
from database.db import init_db

# ── CORS Configuration ──────────────────────────────────────
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
print(f"[CORS] Configured origins: {cors_origins}")

# ── Socket.IO ───────────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,
    logger=False,
    engineio_logger=False
)


async def broadcast_event(event: str, data: dict):
    """Broadcast to all connected Socket.IO clients."""
    await sio.emit(event, data)


task_manager.set_broadcast(broadcast_event)


@sio.on("connect")
async def sio_connect(sid, environ, auth=None):
    print(f"[WS] Client connected: {sid}")
    await sio.emit("tasks_snapshot", task_manager.get_all_tasks(), to=sid)


@sio.on("disconnect")
async def sio_disconnect(sid):
    print(f"[WS] Client disconnected: {sid}")


# ── FastAPI Lifespan ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/exports", exist_ok=True)
    await init_db()
    print("[APP] Application started - Using Supabase as primary database")
    yield
    print("[APP] Shutting down")


# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="Prospecta HUB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
from modules.emails.router import router as emails_router
from modules.gmap.router import router as gmap_router
from modules.facebook_ads.router import router as facebook_router
from modules.locations.router import router as locations_router
from modules.leads.router import router as leads_router

app.include_router(emails_router, prefix="/api/emails", tags=["Emails"])
app.include_router(gmap_router, prefix="/api/gmap", tags=["Google Maps"])
app.include_router(facebook_router, prefix="/api/facebook", tags=["Facebook ADS"])
app.include_router(locations_router)
app.include_router(leads_router, prefix="/api")

# ── Task Management Endpoints ────────────────────────────────
@app.get("/api/tasks")
async def get_all_tasks():
    return task_manager.get_all_tasks()


@app.get("/api/tasks/active")
async def get_active_tasks():
    return task_manager.get_active_tasks()


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    info = task_manager.get_task(task_id)
    if not info:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return info.to_dict()


@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    await task_manager.pause(task_id)
    return {"status": "paused"}


@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    await task_manager.resume(task_id)
    return {"status": "resumed"}


@app.post("/api/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    await task_manager.stop(task_id)
    return {"status": "stopped"}


# ── Dashboard Stats ──────────────────────────────────────────
@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics from Supabase."""
    from database.supabase_client import get_supabase_client
    try:
        client = get_supabase_client()
        if not client.is_available():
            raise Exception("Supabase unavailable")

        gmap_total = (client.client.table("gmap_leads").select("id", count="exact").execute()).count or 0
        fb_total = (client.client.table("facebook_ads_leads").select("id", count="exact").execute()).count or 0
        emails_total = (client.client.table("email_results").select("id", count="exact").execute()).count or 0

        return {
            "total_leads": gmap_total + fb_total,
            "gmap_leads": gmap_total,
            "facebook_leads": fb_total,
            "emails_found": emails_total,
            "active_tasks": len(task_manager.get_active_tasks()),
        }
    except Exception:
        return {
            "total_leads": 0,
            "gmap_leads": 0,
            "facebook_leads": 0,
            "emails_found": 0,
            "active_tasks": len(task_manager.get_active_tasks()),
        }


# ── Health ───────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Mount Socket.IO (deve ser o último passo) ────────────────
app = socketio.ASGIApp(sio, app)

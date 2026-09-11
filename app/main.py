"""FastAPI application factory and lifecycle."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.config import BASE_DIR, settings
from app.database.database import init_db
from app.services.accounts import current_user, initialize_accounts
from app.services.scheduler import scheduler
from app.utils.logger import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    initialize_accounts()
    if settings.scheduler_enabled:
        scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="Trade Analysis Bot", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(router)
app.include_router(admin_router)
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")


@app.get("/healthz", include_in_schema=False)
def healthz():
    """Public, non-sensitive liveness probe for the hosting platform."""
    return {"status": "ok"}


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(BASE_DIR / "frontend" / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(BASE_DIR / "frontend" / "sw.js", media_type="application/javascript",
                        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


@app.middleware("http")
async def development_cache_control(request, call_next):
    if request.url.path.startswith("/static/") and request.url.path.lower().endswith(".html"):
        return Response(status_code=404)
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.get("/", include_in_schema=False)
def dashboard(request: Request):
    try: current_user(request)
    except HTTPException: return RedirectResponse("/login", status_code=303)
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.get("/account", include_in_schema=False)
def account_page(request: Request):
    try: current_user(request)
    except HTTPException: return RedirectResponse("/login", status_code=303)
    return FileResponse(BASE_DIR / "frontend" / "account.html", headers={"Cache-Control": "no-store"})

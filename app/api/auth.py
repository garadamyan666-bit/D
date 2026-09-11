"""Registration, login, logout and account settings."""
from __future__ import annotations

import re
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from app.config import BASE_DIR
from app.database.database import session_scope
from app.database.models import User, UserSession
from app.services.accounts import COOKIE, create_session, current_user, digest, hash_password, limit, same_origin, verify_password
from app.services.telegram_links import create_link, disconnect

router = APIRouter()
USERNAME = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class ProfileUpdate(BaseModel):
    language: str | None = None
    balance: float | None = Field(default=None, ge=1, le=10_000_000)
    risk_percent: float | None = Field(default=None, ge=0.1, le=5)


def user_payload(user: User) -> dict:
    return {"id": user.id, "username": user.username, "is_admin": user.is_admin,
            "language": user.language, "telegram_connected": bool(user.telegram_chat_id),
            "balance": user.balance, "risk_percent": user.risk_percent}


@router.get("/login", include_in_schema=False)
def login_page(request: Request):
    try:
        current_user(request)
        return RedirectResponse("/", status_code=303)
    except HTTPException:
        return FileResponse(BASE_DIR / "frontend" / "login.html", headers={"Cache-Control": "no-store"})


@router.get("/register", include_in_schema=False)
def register_page(request: Request):
    try:
        current_user(request)
        return RedirectResponse("/", status_code=303)
    except HTTPException:
        return FileResponse(BASE_DIR / "frontend" / "register.html", headers={"Cache-Control": "no-store"})


@router.post("/api/auth/register")
def register(payload: Credentials, request: Request, response: Response):
    same_origin(request); limit(request, "register", 8, 900)
    username = payload.username.strip().lower()
    if not USERNAME.fullmatch(username):
        raise HTTPException(400, "Մուտքանունը կարող է պարունակել լատինատառ տառեր, թվեր, կետ, գիծ և ընդգծում։")
    with session_scope() as session:
        if session.scalar(select(User.id).where(func.lower(User.username) == username)):
            raise HTTPException(409, "Այս մուտքանունն արդեն զբաղված է։")
        user = User(username=username, password_hash=hash_password(payload.password))
        session.add(user); session.flush(); user_id = user.id
    create_session(user_id, response, request)
    return {"ok": True}


@router.post("/api/auth/login")
def login(payload: Credentials, request: Request, response: Response):
    same_origin(request); limit(request, "login", 15, 300)
    with session_scope() as session:
        user = session.scalar(select(User).where(func.lower(User.username) == payload.username.strip().lower()))
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(401, "Սխալ մուտքանուն կամ գաղտնաբառ։")
        user_id = user.id
    create_session(user_id, response, request)
    return {"ok": True}


@router.post("/api/auth/logout")
def logout(request: Request, response: Response):
    same_origin(request)
    token = request.cookies.get(COOKIE)
    if token:
        with session_scope() as session:
            session.execute(delete(UserSession).where(UserSession.token_hash == digest(token)))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/api/account")
def account(user: User = Depends(current_user)):
    return user_payload(user)


@router.patch("/api/account")
def update_account(payload: ProfileUpdate, request: Request, user: User = Depends(current_user)):
    same_origin(request)
    if payload.language is not None and payload.language not in {"hy", "ru", "en"}:
        raise HTTPException(400, "Unsupported language")
    with session_scope() as session:
        row = session.get(User, user.id)
        if payload.language is not None: row.language = payload.language
        if payload.balance is not None: row.balance = payload.balance
        if payload.risk_percent is not None: row.risk_percent = payload.risk_percent
        session.flush(); return user_payload(row)


@router.post("/api/account/telegram/link")
def telegram_link(request: Request, user: User = Depends(current_user)):
    same_origin(request); limit(request, "telegram-link", 10, 300)
    try:
        return {"url": create_link(user.id), "expires_in_seconds": 600}
    except ValueError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.delete("/api/account/telegram")
def telegram_disconnect(request: Request, user: User = Depends(current_user)):
    same_origin(request); disconnect(user.id); return {"disconnected": True}

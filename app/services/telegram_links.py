"""Connect Telegram chats to user accounts through one-time bot links."""
from __future__ import annotations

import hashlib
import logging
import secrets
import time
from urllib.parse import quote

import requests
from sqlalchemy import select

from app.config import settings
from app.database.database import session_scope
from app.database.models import AppSetting, User
from app.services.telegram import send_message

OFFSET_KEY = "telegram_updates_offset"
logger = logging.getLogger(__name__)


def create_link(user_id: int) -> str:
    if not settings.telegram_bot_token or not settings.telegram_bot_username:
        raise ValueError("Telegram bot-ը դեռ ամբողջությամբ կարգավորված չէ։")
    secret = secrets.token_urlsafe(24)
    with session_scope() as session:
        user = session.get(User, user_id)
        user.telegram_link_hash = hashlib.sha256(secret.encode()).hexdigest()
        user.telegram_link_expires = time.time() + 600
    return f"https://t.me/{quote(settings.telegram_bot_username)}?start={quote(secret)}"


def disconnect(user_id: int) -> None:
    with session_scope() as session:
        user = session.get(User, user_id)
        user.telegram_chat_id = None
        user.telegram_link_hash = None
        user.telegram_link_expires = None


def process_updates() -> int:
    if not settings.telegram_bot_token:
        return 0
    with session_scope() as session:
        row = session.get(AppSetting, OFFSET_KEY)
        offset = int(row.value) if row else 0
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates",
            params={"offset": offset, "limit": 100, "timeout": 0, "allowed_updates": '["message"]'}, timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        # Never log the exception object: Telegram embeds the secret bot token in its URL.
        logger.warning("Telegram account-link polling is temporarily unavailable")
        return 0
    updates = payload.get("result", []) if payload.get("ok") else []
    connected = 0
    for update in updates:
        offset = max(offset, int(update.get("update_id", 0)) + 1)
        message = update.get("message") or {}
        text = str(message.get("text", "")).strip()
        chat_id = str((message.get("chat") or {}).get("id", ""))
        if not text.startswith("/start ") or not chat_id:
            continue
        secret = text.split(maxsplit=1)[1].strip()
        token_hash = hashlib.sha256(secret.encode()).hexdigest()
        with session_scope() as session:
            user = session.scalar(select(User).where(User.telegram_link_hash == token_hash))
            used = session.scalar(select(User.id).where(User.telegram_chat_id == chat_id))
            if not user or not user.telegram_link_expires or user.telegram_link_expires < time.time() or (used and used != user.id):
                continue
            user.telegram_chat_id = chat_id
            user.telegram_link_hash = None
            user.telegram_link_expires = None
            language = user.language
            connected += 1
        confirmations = {"hy": "✅ Telegram-ը միացվեց ձեր անձնական հաշվին։", "ru": "✅ Telegram подключён к вашему личному аккаунту.", "en": "✅ Telegram is connected to your personal account."}
        send_message(confirmations.get(language, confirmations["en"]), chat_id)
    with session_scope() as session:
        row = session.get(AppSetting, OFFSET_KEY)
        if row: row.value = str(offset)
        else: session.add(AppSetting(key=OFFSET_KEY, value=str(offset)))
    return connected

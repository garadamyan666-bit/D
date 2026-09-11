"""User authentication, hashed persistent sessions and owner migration."""
import hashlib
import json
import secrets
import time
from threading import Lock
from fastapi import HTTPException, Request
from sqlalchemy import select, delete, inspect, text
from app.config import BASE_DIR, settings
from app.database.database import session_scope, engine
from app.database.models import User, UserSession, UserAlert, AlertSubscription, Signal, ForecastCheck, AppSetting

COOKIE = 'trade_session'
lock = Lock()
attempts = {}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    value = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()
    return salt + ':' + value


def verify_password(password, stored):
    return secrets.compare_digest(hash_password(password, stored.split(':')[0]), stored)


def limit(request, action, maximum=15, seconds=300):
    key = (action, request.client.host if request.client else 'unknown')
    now = time.time()
    with lock:
        for old in list(attempts):
            if not attempts[old] or attempts[old][-1] < now - 3600:
                del attempts[old]
        recent = [v for v in attempts.get(key, []) if v > now - seconds]
        if len(recent) >= maximum:
            raise HTTPException(429, 'Չափազանց շատ հարցումներ․ փորձեք ավելի ուշ։')
        attempts[key] = recent + [now]


def same_origin(request):
    origin = request.headers.get('origin')
    allowed = {settings.public_url, str(request.base_url).rstrip('/')}
    if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and origin not in allowed):
        raise HTTPException(403, 'Invalid origin')


def current_user(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, 'Մուտք գործեք ձեր հաշիվ։')
    with session_scope() as s:
        session = s.get(UserSession, digest(token))
        if not session or session.expires_at <= time.time():
            raise HTTPException(401, 'Մուտքի ժամկետն ավարտվել է։')
        user = s.get(User, session.user_id)
        if not user:
            raise HTTPException(401, 'Մուտք գործեք։')
        s.expunge(user)
        return user


def create_session(user_id, response, request):
    token = secrets.token_urlsafe(32)
    with session_scope() as s:
        s.execute(delete(UserSession).where(UserSession.expires_at < time.time()))
        old = request.cookies.get(COOKIE)
        if old:
            s.execute(delete(UserSession).where(UserSession.token_hash == digest(old)))
        s.add(UserSession(token_hash=digest(token), user_id=user_id, expires_at=time.time()+86400*7))
    forwarded_https = request.headers.get('x-forwarded-proto', '').split(',')[0].strip() == 'https'
    response.set_cookie(COOKIE, token, max_age=86400*7, httponly=True, samesite='strict',
        secure=settings.public_url.startswith('https://') or forwarded_https, path='/')
    response.headers['Cache-Control'] = 'no-store'


def initialize_accounts():
    # Additive migration: old records are explicitly assigned to the owner.
    with engine.begin() as connection:
        for table in ('signals', 'forecast_checks'):
            columns = {col['name'] for col in inspect(connection).get_columns(table)}
            if 'user_id' not in columns:
                connection.execute(text(f'ALTER TABLE {table} ADD COLUMN user_id INTEGER'))
    with session_scope() as s:
        if s.get(AppSetting, 'accounts_migrated_v1'):
            return
        owner = s.scalar(select(User).where(User.is_admin.is_(True)))
        if not owner:
            path = BASE_DIR/'data'/'admin-auth.json'
            if path.exists():
                auth = json.loads(path.read_text(encoding='utf-8'))
                password_hash = auth['salt']+':'+auth['digest']
            elif settings.admin_password:
                password_hash = hash_password(settings.admin_password)
            else:
                password = secrets.token_urlsafe(24)
                password_hash = hash_password(password)
                with (BASE_DIR/'admin-access.txt').open('x', encoding='utf-8') as file:
                    file.write('URL: '+settings.public_url+'/login\nUsername: admin\nPassword: '+password+'\n')
            language = s.get(AppSetting, 'telegram_alert_language')
            owner = User(username=settings.admin_username or 'admin', password_hash=password_hash, is_admin=True,
                language=language.value if language else 'hy', telegram_chat_id=settings.telegram_chat_id or None)
            s.add(owner); s.flush()
        for row in s.scalars(select(AlertSubscription)).all():
            if row.source == 'BINANCE':
                s.add(UserAlert(user_id=owner.id, symbol=row.symbol, timeframe=row.timeframe,
                    min_confidence=row.min_confidence, active=row.active, last_notified_at=row.last_notified_at,
                    last_checked_at=row.last_checked_at, last_signal=row.last_signal, last_confidence=row.last_confidence))
            s.delete(row)
        for row in s.scalars(select(Signal).where(Signal.user_id.is_(None))).all():
            try:
                source = json.loads(row.payload).get('market_source')
            except (ValueError, TypeError):
                source = None
            if source == 'BINANCE':
                row.user_id = owner.id
            else:
                s.delete(row)
        s.execute(text('UPDATE forecast_checks SET user_id=:id WHERE user_id IS NULL'), {'id': owner.id})
        s.add(AppSetting(key='accounts_migrated_v1', value='done'))

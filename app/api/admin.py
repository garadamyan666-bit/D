"""Owner-only forecast verification dashboard."""
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import delete, func, select

from app.config import BASE_DIR
from app.database.database import session_scope
from app.database.models import ForecastCheck, User
from app.services.accounts import current_user, same_origin

router = APIRouter()


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Այս բաժինը հասանելի է միայն ադմինին։")
    return user


def _check_payload(row):
    return {"id": row.id, "symbol": row.symbol, "timeframe": row.timeframe,
            "signal": row.signal, "confidence": row.confidence, "start_price": row.start_price,
            "issued_at": row.issued_at.replace(tzinfo=timezone.utc).isoformat(), "target_ms": row.target_ms,
            "end_price": row.end_price, "change_pct": row.change_pct, "status": row.status, "error": row.error}


@router.get("/admin/login", include_in_schema=False)
def old_login():
    return RedirectResponse("/login?next=/admin", status_code=303)


@router.get("/admin", include_in_schema=False)
def page(request: Request):
    try:
        user = current_user(request)
    except HTTPException:
        return RedirectResponse("/login?next=/admin", status_code=303)
    if not user.is_admin:
        raise HTTPException(403, "Այս բաժինը հասանելի է միայն ադմինին։")
    return FileResponse(BASE_DIR / "admin" / "index.html", headers={"Cache-Control": "no-store"})


@router.get("/api/admin/verification")
def report(response: Response, _: User = Depends(require_admin)):
    response.headers["Cache-Control"] = "no-store"
    tracked = ("M15", "H1")
    with session_scope() as session:
        counts = dict(session.execute(select(ForecastCheck.status, func.count()).where(ForecastCheck.timeframe.in_(tracked)).group_by(ForecastCheck.status)).all())
        evaluated = sum(counts.get(k, 0) for k in ("CORRECT", "INCORRECT", "FLAT"))
        rows = session.scalars(select(ForecastCheck).where(ForecastCheck.timeframe.in_(tracked)).order_by(ForecastCheck.id.desc()).limit(200)).all()
        by_timeframe = {}
        for timeframe in tracked:
            grouped = dict(session.execute(select(ForecastCheck.status, func.count()).where(ForecastCheck.timeframe == timeframe).group_by(ForecastCheck.status)).all())
            checked = sum(grouped.get(k, 0) for k in ("CORRECT", "INCORRECT", "FLAT"))
            recent = session.scalars(select(ForecastCheck).where(ForecastCheck.timeframe == timeframe).order_by(ForecastCheck.id.desc()).limit(100)).all()
            by_timeframe[timeframe] = {"counts": grouped, "evaluated": checked,
                "accuracy_pct": round(100 * grouped.get("CORRECT", 0) / checked, 2) if checked else None,
                "rows": [_check_payload(row) for row in recent]}
        return {"counts": counts, "evaluated": evaluated, "by_timeframe": by_timeframe,
                "accuracy_pct": round(100 * counts.get("CORRECT", 0) / evaluated, 2) if evaluated else None,
                "rows": [_check_payload(row) for row in rows]}


@router.delete("/api/admin/verification")
def reset_verification(request: Request, confirm: str = "", _: User = Depends(require_admin)):
    same_origin(request)
    if confirm != "RESET":
        raise HTTPException(400, "Reset confirmation is required")
    with session_scope() as session:
        deleted = session.execute(delete(ForecastCheck)).rowcount or 0
    return {"ok": True, "deleted": deleted}

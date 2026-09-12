"""Owner-only forecast verification dashboard."""
from datetime import timezone
import json
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
            "end_price": row.end_price, "change_pct": row.change_pct, "status": row.status, "error": row.error,
            "evaluation": json.loads(row.evaluation or 'null')}


def comparison(rows):
    # Deduplicate users' copies and overlapping horizons. This is a prospective
    # holdout: candidate criteria were frozen when the signal was recorded.
    groups, next_allowed = {}, {}
    for row in rows:
        frozen = json.loads(row.evaluation or 'null')
        if not frozen or 'net_pct' not in frozen:
            continue
        key = (row.symbol, row.timeframe)
        issued_ms = row.issued_at.replace(tzinfo=timezone.utc).timestamp() * 1000
        if issued_ms < next_allowed.get(key, 0):
            continue
        next_allowed[key] = row.target_ms + 1
        for version, include in [(frozen['version'], True), (frozen['candidate'], frozen['candidate_accepted'])]:
            label = (*key, version)
            values = groups.setdefault(label, [])
            if include:
                values.append(frozen['net_pct'])
    return [{'symbol': k[0], 'timeframe': k[1], 'version': k[2], 'samples': len(v),
             'profitable_pct': round(100 * sum(x > 0 for x in v) / len(v), 2) if v else None,
             'mean_net_pct': round(sum(v) / len(v), 4) if v else None,
             'enough_data': len(v) >= 100} for k, v in groups.items()]


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
        prospective = session.scalars(select(ForecastCheck).where(ForecastCheck.timeframe.in_(tracked), ForecastCheck.evaluation.is_not(None)).order_by(ForecastCheck.issued_at, ForecastCheck.id)).all()
        return {"counts": counts, "evaluated": evaluated, "by_timeframe": by_timeframe,
                "comparison": comparison(prospective),
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

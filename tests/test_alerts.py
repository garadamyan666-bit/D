from datetime import datetime, timedelta, timezone

from app.services.alerts import should_notify


def _item(signal="BUY", confidence=70):
    return {"signal": signal, "confidence": confidence}


def test_alert_requires_directional_signal_and_threshold():
    now = datetime.now(timezone.utc)
    assert should_notify(_item("WAIT", 99), 70, None, None, now) is True
    assert should_notify(_item("BUY", 69.9), 70, None, None, now) is False
    assert should_notify(_item("BUY", 70), 70, None, None, now) is True


def test_alert_respects_cooldown_but_allows_direction_change():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(minutes=1)
    assert should_notify(_item("BUY", 80), 70, recent, "BUY", now) is False
    assert should_notify(_item("SELL", 80), 70, recent, "BUY", now) is True

"""Lightweight background market-scan scheduler."""
from __future__ import annotations

import logging
from threading import Event, Thread

from app.config import settings
from app.services.alerts import scan_alert_subscriptions
from app.services.verification import verify_pending
from app.services.telegram_links import process_updates

logger = logging.getLogger(__name__)


class ScanScheduler:
    def __init__(self) -> None:
        self._stop = Event()
        self._thread: Thread | None = None
        self._verification_thread: Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._run, name="market-scanner", daemon=True)
        self._thread.start()
        self._verification_thread = Thread(target=self._verify, name='forecast-verifier', daemon=True)
        self._verification_thread.start()
        logger.info("Market scanner scheduled every %s minutes", settings.scan_interval_minutes)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                scan_alert_subscriptions()
            except Exception:
                logger.exception("Scheduled scan failed")
            if self._stop.wait(settings.scan_interval_minutes * 60):
                break

    def _verify(self):
        while not self._stop.is_set():
            try:
                verify_pending()
            except Exception:
                logger.exception('Forecast verification cycle failed')
            try:
                process_updates()
            except Exception:
                logger.exception('Telegram account-link cycle failed')
            if self._stop.wait(10):
                break

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)


scheduler = ScanScheduler()

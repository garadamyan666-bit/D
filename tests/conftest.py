"""Keep automated tests completely separate from the real user database."""
import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "test-trading.db"
os.environ["DATABASE_URL"] = "sqlite:///" + TEST_DB.as_posix()
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""


def pytest_sessionfinish(session, exitstatus):
    from app.database.database import engine
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)

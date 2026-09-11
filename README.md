# Trade Analysis Bot

A Binance Spot market-analysis dashboard with personal accounts, per-user history, risk settings and Telegram alerts. It is analysis-only: it does not place or manage trades.

## Features

- Registration and login with hashed passwords and secure persistent sessions
- Isolated analysis history and alert settings for every user
- Binance public market data (no Binance API key required)
- M1 and M15 forecast verification in an owner-only admin dashboard
- Per-user balance and risk percentage for position-size calculations
- Telegram account linking, language preference, threshold and periodic alerts
- Technical analysis, market intelligence, leaders and historical backtesting

## Local setup

```powershell
cd "C:\Users\user\Desktop\Trade Analize\trade-analysis-bot"
.\venv\Scripts\Activate.ps1
python run.py
```

Open `http://127.0.0.1:8000/register`. The original owner account remains available with the credentials stored in `admin-access.txt`.

Copy `.env.example` to `.env` and configure Telegram if needed. Never publish `.env`, `admin-access.txt` or the SQLite database.

## Tests

```powershell
python -m pytest -q
```

The tests use a separate temporary database and never modify the real application database.

## Production notes

Use HTTPS, set `PUBLIC_URL` to the final HTTPS address, keep one application worker for Telegram polling, store secrets as hosting-provider environment variables, and back up the database. A managed PostgreSQL database is recommended before serving many users.

"""Telegram Bot API notifications with safe error handling."""
from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def _number(value: Any) -> str:
    return "N/A" if value is None else f"{value:.6g}"


SIGNALS = {
    "hy": {"STRONG BUY": "ՈՒԺԵՂ ԳՆՈՒՄ", "BUY": "ԳՆԵԼ", "WAIT": "ՍՊԱՍԵԼ", "SELL": "ՎԱՃԱՌԵԼ", "STRONG SELL": "ՈՒԺԵՂ ՎԱՃԱՌՔ"},
    "ru": {"STRONG BUY": "СИЛЬНАЯ ПОКУПКА", "BUY": "ПОКУПАТЬ", "WAIT": "ЖДАТЬ", "SELL": "ПРОДАВАТЬ", "STRONG SELL": "СИЛЬНАЯ ПРОДАЖА"},
    "en": {},
}
TRENDS = {
    "hy": {"BULLISH": "ԱՃՈՂ", "BEARISH": "ՆՎԱԶՈՂ", "NEUTRAL": "ՉԵԶՈՔ"},
    "ru": {"BULLISH": "ВОСХОДЯЩИЙ", "BEARISH": "НИСХОДЯЩИЙ", "NEUTRAL": "НЕЙТРАЛЬНЫЙ"},
    "en": {},
}


def _translated(mapping: dict[str, dict[str, str]], language: str, value: Any) -> str:
    text = str(value)
    return mapping[language].get(text, text)


def _language_block(item: dict[str, Any], language: str) -> str:
    labels = {
        "hy": ("🇦🇲 ՀԱՅԵՐԵՆ", "Աղբյուր", "Շուկա", "Ժամանակահատված", "Ազդանշան", "Վստահություն", "Միտում", "Աջակցություն", "Դիմադրություն", "Մուտք", "Կորուստի սահման", "Շահույթի թիրախ", "Միայն վերլուծություն․ ավտոմատ գործարք չի կատարվում։"),
        "ru": ("🇷🇺 РУССКИЙ", "Источник", "Рынок", "Таймфрейм", "Сигнал", "Уверенность", "Тренд", "Поддержка", "Сопротивление", "Вход", "Стоп-лосс", "Тейк-профит", "Только анализ — автоматические сделки не выполняются."),
        "en": ("🇬🇧 ENGLISH", "Source", "Market", "Timeframe", "Signal", "Confidence", "Trend", "Support", "Resistance", "Entry", "Stop loss", "Take profit", "Analysis only — no automatic trades."),
    }[language]
    title, source, market, timeframe, signal, confidence, trend, support, resistance, entry, stop, target, warning = labels
    return (
        f"{title}\n"
        f"{source}: BINANCE\n{market}: {item['symbol']}\n{timeframe}: {item['timeframe']}\n"
        f"{signal}: {_translated(SIGNALS, language, item['signal'])}\n🎯 {confidence}: {_number(item.get('confidence'))}%\n"
        f"{trend}: {_translated(TRENDS, language, item.get('trend', 'NEUTRAL'))}\nRSI: {_number(item.get('rsi'))} · MACD: {_number(item.get('macd'))}\n"
        f"{support}: {_number(item.get('support'))} · {resistance}: {_number(item.get('resistance'))}\n"
        f"{entry}: {_number(item.get('entry'))} · {stop}: {_number(item.get('stop_loss'))} · {target}: {_number(item.get('take_profit'))}\n"
        f"⚠️ {warning}"
    )


def format_analysis(item: dict[str, Any], language: str = "hy") -> str:
    return "📊 TRADE ANALYSIS ALERT\n━━━━━━━━━━━━━━━━━━\n\n" + _language_block(item, language)


def format_test_message(language: str = "hy") -> str:
    return {
        "hy": "✅ Telegram ծանուցումները միացված են։\n⚠️ Միայն վերլուծություն․ ավտոմատ գործարք չի կատարվում։",
        "ru": "✅ Уведомления Telegram подключены.\n⚠️ Только анализ — автоматические сделки не выполняются.",
        "en": "✅ Telegram alerts are connected.\n⚠️ Analysis only — no automatic trades.",
    }.get(language, "✅ Telegram alerts are connected.")


def send_message(text: str, chat_id: str | None = None) -> bool:
    selected_chat = chat_id or settings.telegram_chat_id
    if not settings.telegram_bot_token or not selected_chat:
        logger.info("Telegram is not configured; notification skipped")
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": selected_chat, "text": text}, timeout=12,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        # Request exceptions can contain the full Bot API URL, which embeds the
        # secret token. Log only the exception type so credentials never leak.
        logger.warning("Telegram notification failed (%s)", type(exc).__name__)
        return False


def send_analysis(item: dict[str, Any], language: str, chat_id: str) -> bool:
    return send_message(format_analysis(item, language), chat_id)

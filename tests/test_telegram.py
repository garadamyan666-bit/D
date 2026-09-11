from app.services.telegram import format_analysis, format_test_message


def test_alert_message_uses_selected_language_only():
    item = {
        "market_source": "BINANCE", "symbol": "BTCUSDT", "timeframe": "M15",
        "signal": "BUY", "confidence": 72.5, "trend": "BULLISH", "rsi": 55,
        "macd": 1.2, "support": 100, "resistance": 120, "entry": 110,
        "stop_loss": 99, "take_profit": 132,
    }
    message = format_analysis(item, "ru")
    assert "🇷🇺 РУССКИЙ" in message and "ПОКУПАТЬ" in message
    assert "🇦🇲 ՀԱՅԵՐԵՆ" not in message and "🇬🇧 ENGLISH" not in message


def test_connection_message_uses_selected_language():
    assert "ծանուցումները" in format_test_message("hy")
    assert "Уведомления" in format_test_message("ru")
    assert "alerts" in format_test_message("en")

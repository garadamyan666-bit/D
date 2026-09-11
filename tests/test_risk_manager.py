import pytest

from app.core.risk_manager import calculate_risk, calculate_trade_levels


def test_long_levels_use_atr_and_rr():
    setup = calculate_trade_levels("LONG", 100, 2, atr_multiplier=1.5, risk_reward=2)
    assert setup["stop_loss"] == pytest.approx(97)
    assert setup["take_profit"] == pytest.approx(106)
    assert setup["risk_reward"] == 2


def test_short_levels_and_structure_stop():
    setup = calculate_trade_levels("SHORT", 100, 2, resistance=104, atr_multiplier=1.5, risk_reward=2)
    assert setup["stop_loss"] == pytest.approx(104.3)
    assert setup["take_profit"] == pytest.approx(91.4)


def test_risk_size_and_daily_cap():
    risk = calculate_risk(1000, 1, 100, 98, 104, max_daily_risk=8)
    assert risk["risk_amount"] == 8
    assert risk["position_size"] == 4
    assert risk["potential_loss"] == 8
    assert risk["potential_profit"] == 16


def test_wait_has_no_trade_levels():
    setup = calculate_trade_levels("WAIT", 100, 2)
    assert setup["stop_loss"] is None
    risk = calculate_risk(1000, 1, 100, None, None)
    assert risk["position_size"] == 0


@pytest.mark.parametrize("balance,percent", [(0, 1), (1000, 0), (1000, 101)])
def test_invalid_risk_input(balance, percent):
    with pytest.raises(ValueError):
        calculate_risk(balance, percent, 100, 99, 102)

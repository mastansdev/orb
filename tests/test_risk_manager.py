import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from risk_manager import RiskManager
from config import RISK_REWARD


def test_trade_creation():

    risk = RiskManager()

    trade = risk.create_trade(
        entry_price=100,
        stop_loss=95
    )

    assert trade is not None
    assert trade["risk"] == 5
    # Target follows the configured RISK_REWARD
    assert trade["target"] == 100 + (5 * RISK_REWARD)

    print("✅ Trade Creation Passed")


def test_stoploss():

    risk = RiskManager()

    trade = risk.create_trade(
        100,
        95
    )

    result = risk.update(
        trade,
        94,
        "10:00:00"
    )

    assert result == "STOPLOSS"

    print("✅ StopLoss Passed")


def test_target():

    risk = RiskManager()

    trade = risk.create_trade(
        100,
        95
    )

    result = risk.update(
        trade,
        100 + (5 * RISK_REWARD),
        "10:00:00"
    )

    assert result == "TARGET"

    print("✅ Target Passed")


def test_breakeven_before_target():
    """
    At 1R the breakeven ratchet must engage even when
    the target also sits at 1R (ordering bug fix).
    """

    risk = RiskManager()

    trade = risk.create_trade(
        100,
        95
    )

    risk.update(
        trade,
        105,
        "10:00:00"
    )

    assert trade["breakeven_done"] is True
    assert trade["trail_sl"] == 100

    print("✅ Breakeven Ratchet Passed")


def test_time_exit():

    risk = RiskManager()

    trade = risk.create_trade(
        100,
        95
    )

    result = risk.update(
        trade,
        103,
        "15:15:00"
    )

    assert result == "TIME_EXIT"

    print("✅ Time Exit Passed")


if __name__ == "__main__":

    test_trade_creation()
    test_stoploss()
    test_target()
    test_breakeven_before_target()
    test_time_exit()

    print("\n🎉 Risk Manager Tests Passed")

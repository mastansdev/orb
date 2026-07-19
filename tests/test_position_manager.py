import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from trading.capital_manager import CapitalManager
from trading.position_manager import PositionManager


def test_open_and_confirm_position():

    capital = CapitalManager()
    pm = PositionManager(capital)

    qty = pm.open_position(
        security_id="123",
        symbol="TEST",
        entry_price=100,
        stop_loss=95
    )

    assert qty > 0

    confirmed = pm.confirm_position(
        security_id="123",
        symbol="TEST",
        entry_price=100,
        stop_loss=95,
        qty=qty
    )

    assert confirmed is True
    assert pm.has_position("123")

    print("✅ Open + Confirm Position Passed")


def test_close_position():

    capital = CapitalManager()
    pm = PositionManager(capital)

    qty = pm.open_position(
        "123",
        "TEST",
        100,
        95
    )

    pm.confirm_position("123", "TEST", 100, 95, qty)

    pm.close_position(
        "123",
        pnl=500
    )

    assert not pm.has_position("123")

    print("✅ Close Position Passed")


def test_recovery():

    capital = CapitalManager()
    pm = PositionManager(capital)

    pm.recover_position(
        security_id="ABC",
        symbol="RECOVERED",
        entry_price=250,
        stop_loss=240,
        qty=100
    )

    assert pm.has_position("ABC")

    print("✅ Recovery Passed")


if __name__ == "__main__":

    test_open_and_confirm_position()
    test_close_position()
    test_recovery()

    print("\n🎉 Position Manager Tests Passed")

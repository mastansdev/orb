from capital_manager import CapitalManager
from position_manager import PositionManager


def test_open_position():

    capital = CapitalManager()
    pm = PositionManager(capital)

    qty = pm.open_position(
        security_id="123",
        entry_price=100,
        stop_loss=95
    )

    assert qty > 0
    assert pm.has_position("123")

    print("✅ Open Position Passed")


def test_close_position():

    capital = CapitalManager()
    pm = PositionManager(capital)

    pm.open_position(
        "123",
        100,
        95
    )

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
        entry_price=250,
        stop_loss=240,
        qty=100
    )

    assert pm.has_position("ABC")

    print("✅ Recovery Passed")


if __name__ == "__main__":

    test_open_position()
    test_close_position()
    test_recovery()

    print("\n🎉 Position Manager Tests Passed")
from risk_manager import RiskManager


def test_trade_creation():

    risk = RiskManager()

    trade = risk.create_trade(
        entry_price=100,
        stop_loss=95
    )

    assert trade is not None
    assert trade["risk"] == 5
    assert trade["target"] == 110

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
        110,
        "10:00:00"
    )

    assert result == "TARGET"

    print("✅ Target Passed")


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
    test_time_exit()

    print("\n🎉 Risk Manager Tests Passed")
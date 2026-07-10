from trade_selection_engine import TradeSelectionEngine


def test_score():

    engine = TradeSelectionEngine()

    score = engine.calculate_score(
        ltp=102,
        orb_high=100,
        orb_low=95
    )

    assert score > 0

    print("✅ Score Calculation Passed")


def test_best():

    engine = TradeSelectionEngine()

    engine.add_signal("ABC", 80)
    engine.add_signal("XYZ", 95)
    engine.add_signal("PQR", 60)

    assert engine.best() == "XYZ"

    print("✅ Best Signal Passed")


def test_remove():

    engine = TradeSelectionEngine()

    engine.add_signal("ABC", 90)

    engine.remove_signal("ABC")

    assert engine.best() is None

    print("✅ Remove Signal Passed")


if __name__ == "__main__":

    test_score()
    test_best()
    test_remove()

    print("\n🎉 Trade Selection Tests Passed")
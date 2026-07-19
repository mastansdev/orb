from core.engine import Engine


def test_engine_creation():

    engine = Engine()

    assert engine is not None
    assert engine.strategy is not None
    assert engine.risk_manager is not None
    assert engine.position_manager is not None
    assert engine.capital_manager is not None
    assert engine.trade_logger is not None

    print("✅ Engine Creation Passed")


def test_tick_cache():

    engine = Engine()

    engine.tick_cache.update(
        "123",
        100.5,
        "09:31:00"
    )

    tick = engine.get_tick("123")

    assert tick["ltp"] == 100.5

    print("✅ Tick Cache Integration Passed")


def test_orb_engine():

    engine = Engine()

    engine.orb_engine.update(
        "123",
        100,
        "09:15:00"
    )

    engine.orb_engine.update(
        "123",
        105,
        "09:20:00"
    )

    engine.orb_engine.update(
        "123",
        99,
        "09:29:00"
    )

    engine.orb_engine.update(
        "123",
        101,
        "09:30:00"
    )

    orb = engine.get_orb("123")

    assert orb is not None
    assert orb["completed"] is True

    print("✅ ORB Integration Passed")


if __name__ == "__main__":

    test_engine_creation()
    test_tick_cache()
    test_orb_engine()

    print("\n🎉 Engine Integration Tests Passed")
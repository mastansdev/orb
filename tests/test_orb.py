from core.orb_engine import ORBEngine


def test_orb_creation():

    orb = ORBEngine()

    orb.update("123", 100, "09:15:00")
    orb.update("123", 105, "09:18:00")
    orb.update("123", 98, "09:22:00")
    orb.update("123", 102, "09:29:59")
    orb.update("123", 101, "09:30:00")

    data = orb.get_orb("123")

    assert data is not None

    assert data["high"] == 105
    assert data["low"] == 98
    assert data["completed"] is True

    print("✅ ORB Creation Test Passed")


if __name__ == "__main__":
    test_orb_creation()
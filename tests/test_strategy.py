from strategy import Strategy


def test_buy_signal():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": False
    }

    assert strategy.is_buy_signal(101, orb, "09:35:00") is True

    print("✅ Buy Signal Test Passed")


def test_before_orb_complete():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": False,
        "entry_taken": False
    }

    assert strategy.is_buy_signal(101, orb, "09:20:00") is False

    print("✅ ORB Completion Test Passed")


def test_after_cutoff():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": False
    }

    assert strategy.is_buy_signal(101, orb, "15:01:00") is False

    print("✅ Time Cutoff Test Passed")


def test_entry_taken():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": True
    }

    assert strategy.is_buy_signal(101, orb, "09:35:00") is False

    print("✅ Single Entry Test Passed")


if __name__ == "__main__":

    test_buy_signal()
    test_before_orb_complete()
    test_after_cutoff()
    test_entry_taken()

    print("\n🎉 Strategy Tests Passed")
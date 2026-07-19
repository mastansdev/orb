import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from strategy import Strategy
from config import ENTRY_BUFFER_PCT


def make_candle(close):
    return {
        "minute": "09:34",
        "open": close - 1,
        "high": close + 0.5,
        "low": close - 1.5,
        "close": close,
    }


def breakout_close(orb_high):
    """Smallest close clearing the percentage buffer."""
    return orb_high * (1 + ENTRY_BUFFER_PCT / 100) + 0.01


def test_buy_signal():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": False
    }

    candle = make_candle(breakout_close(100))

    assert strategy.is_buy_signal(
        orb, "09:35:00", candle
    ) is True

    print("✅ Buy Signal Test Passed")


def test_before_orb_complete():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": False,
        "entry_taken": False
    }

    candle = make_candle(breakout_close(100))

    assert strategy.is_buy_signal(
        orb, "09:20:00", candle
    ) is False

    print("✅ ORB Completion Test Passed")


def test_after_cutoff():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": False
    }

    candle = make_candle(breakout_close(100))

    assert strategy.is_buy_signal(
        orb, "15:01:00", candle
    ) is False

    print("✅ Time Cutoff Test Passed")


def test_entry_taken():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": True
    }

    candle = make_candle(breakout_close(100))

    assert strategy.is_buy_signal(
        orb, "09:35:00", candle
    ) is False

    print("✅ Single Entry Test Passed")


def test_no_closed_candle():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": False
    }

    assert strategy.is_buy_signal(
        orb, "09:35:00", None
    ) is False

    print("✅ No Candle Test Passed")


def test_overextended_breakout():

    strategy = Strategy()

    orb = {
        "high": 100,
        "low": 95,
        "completed": True,
        "entry_taken": False
    }

    # Close far beyond MAX_BREAKOUT_PERCENT is rejected
    candle = make_candle(110)

    assert strategy.is_buy_signal(
        orb, "09:35:00", candle
    ) is False

    print("✅ Overextension Test Passed")


if __name__ == "__main__":

    test_buy_signal()
    test_before_orb_complete()
    test_after_cutoff()
    test_entry_taken()
    test_no_closed_candle()
    test_overextended_breakout()

    print("\n🎉 Strategy Tests Passed")

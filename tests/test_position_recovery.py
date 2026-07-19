import os

from position_recovery import PositionRecovery

print("=" * 60)
print("     ORB AUTO TRADER - POSITION RECOVERY TEST")
print("=" * 60)

recovery = PositionRecovery()

# --------------------------------------------------
# Dummy Trade
# --------------------------------------------------

test_trade = {

    "12345": {

        "symbol": "SBIN",

        "entry": 1027.00,

        "stop_loss": 1013.00,

        "target": 1055.00,

        "qty": 25,

        "trail_sl": 1013.00,

        "trail_active": False,

        "risk": 14.00,

        "active": True
    }

}

print("\nSaving Dummy Position...")

recovery.save(test_trade)

print("✓ Saved")

# --------------------------------------------------

print("\nLoading Position...")

loaded = recovery.load()

if loaded == test_trade:

    print("✓ Position Recovery PASS")

else:

    print("✗ Position Recovery FAILED")
    print()
    print("Expected:")
    print(test_trade)
    print()
    print("Loaded:")
    print(loaded)

# --------------------------------------------------

print("\nCleaning Recovery File...")

recovery.clear()

print("✓ Recovery Cleared")

print()

if not recovery.exists():

    print("✓ File Deleted Successfully")

else:

    print("✗ Recovery File Still Exists")
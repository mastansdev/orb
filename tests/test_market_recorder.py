"""
==========================================================
Market Recorder Test
==========================================================

Tests
-----
1. Database Connection
2. Session Creation
3. Snapshot Recording
4. Health Check
5. Session Close
==========================================================
"""

import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from market_recorder import MarketRecorder


print()

print("=" * 50)
print("MARKET RECORDER TEST")
print("=" * 50)

# --------------------------------------------------

recorder = MarketRecorder()

print("✅ Database Connected")

# --------------------------------------------------

print(
    f"✅ Session Created : {recorder.session_id}"
)

# --------------------------------------------------

print()

print("Recording 10 snapshots...")

for i in range(10):

    recorder.record(

        floating_mtm=1000 + i * 100,

        realized_pnl=i * 50,

        net_pnl=1000 + i * 150,

        open_positions=10 - i,

        capital_used=250000,

        available_capital=9750000

    )

print("✅ Snapshots Recorded")

# --------------------------------------------------

print()

health = recorder.health()

print("Health")

for key, value in health.items():

    print(f"{key:15} : {value}")

# --------------------------------------------------

assert health["database"] == "CONNECTED"

assert health["snapshots"] == 10

print()

print("✅ Health Check Passed")

# --------------------------------------------------

recorder.close()

print("✅ Session Closed")

# --------------------------------------------------

print()

print("=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)
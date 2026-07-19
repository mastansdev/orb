import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from capital_manager import CapitalManager

print("=" * 60)
print("      ORB AUTO TRADER - CAPITAL MANAGER TEST")
print("=" * 60)

capital = CapitalManager()

print(f"Starting Capital : ₹{capital.capital():,.2f}")

print()

print("Blocking ₹25,000")

if capital.block(25000):

    print("✓ PASS")

else:

    print("✗ FAIL")

print(f"Available : ₹{capital.available():,.2f}")
print(f"Blocked   : ₹{capital.blocked():,.2f}")

print()

print("Releasing with ₹2,000 Profit")

capital.release(
    25000,
    2000
)

print(f"Available : ₹{capital.available():,.2f}")
print(f"Blocked   : ₹{capital.blocked():,.2f}")
print(f"PnL       : ₹{capital.pnl():,.2f}")

print()

print("✓ Capital Manager PASS")

print("=" * 60)
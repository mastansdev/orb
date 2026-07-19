"""
Test suite runner.

Run from repo root:  py run_all_tests.py
"""

import subprocess
import sys

TESTS = [
    "tests/test_institutional_layer.py",
    "tests/test_risk_manager.py",
    "tests/test_strategy.py",
    "tests/test_capital_manager.py",
    "tests/test_position_manager.py",
    "tools/smoke_test.py",
]

print("=" * 60)
print("        ORB AUTO TRADER TEST SUITE")
print("=" * 60)

passed = 0
failed_names = []

for test in TESTS:
    print(f"\nRunning {test}...")

    result = subprocess.run(
        [sys.executable, test]
    )

    if result.returncode == 0:
        passed += 1
    else:
        failed_names.append(test)

print("\n" + "=" * 60)
print(f"Passed : {passed}/{len(TESTS)}")

if passed == len(TESTS):
    print("🎉 ALL TESTS PASSED")
else:
    print(f"❌ FAILED: {failed_names}")

print("=" * 60)

sys.exit(0 if passed == len(TESTS) else 1)

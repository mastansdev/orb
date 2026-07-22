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
    # Added 2026-07-22: judgment tests, not just mechanics --
    # runs real news scenarios (including the actual tariff
    # story that caused today's loss) through the real pipeline
    # and asserts the DECISION is correct, not just that the
    # code executes without crashing. This class of test was
    # completely missing before, which is exactly how the
    # always-WAIT recommendation stub and the always-STRENGTHENING
    # story_direction bug went unnoticed through 23/23 + 6/6
    # green runs.
    "tests/test_news_pipeline_scenarios.py",
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

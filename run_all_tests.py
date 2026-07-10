import subprocess

tests = [
    "test_orb.py",
    "test_strategy.py",
    "test_risk_manager.py",
    "test_capital_manager.py",
    "test_position_manager.py",
    "test_position_recovery.py",
    "test_trade_selection_engine.py"
]

print("=" * 60)
print("        ORB AUTO TRADER TEST SUITE")
print("=" * 60)

passed = 0

for test in tests:

    print(f"\nRunning {test}...")

    result = subprocess.run(
        ["py", test]
    )

    if result.returncode == 0:
        passed += 1

print("\n" + "=" * 60)
print(f"Passed : {passed}/{len(tests)}")

if passed == len(tests):
    print("🎉 ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")

print("=" * 60)

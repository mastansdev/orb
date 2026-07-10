import json

with open("open_positions.json") as f:
    positions = json.load(f)

print(f"Open Positions: {len(positions)}\n")

for i, p in enumerate(positions, 1):
    print(f"{i:2}. {p['symbol']:<15} Qty: {p['qty']}")


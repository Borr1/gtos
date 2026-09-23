"""Quick hourly density inspection for narrative content."""
import json
from pathlib import Path

DATA = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\instrument_expansion_2026-04-25\03_hourly_buckets.json")

with open(DATA) as f:
    data = json.load(f)

# Print hourly normalized share for selected instruments
selected = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD", "JP225", "BTCUSD",
            "GER40", "UK100", "EURGBP"]

for sym in selected:
    if sym not in data:
        continue
    h = data[sym]
    total = sum(h[str(i)]["mean_abs_ret"] * h[str(i)]["n"] for i in range(24))
    print(f"\n{sym}:")
    for i in range(24):
        share = (h[str(i)]["mean_abs_ret"] * h[str(i)]["n"]) / total * 100 if total > 0 else 0
        bar = "#" * int(share * 2)
        marker = ""
        if share > 1.3 * (100 / 24):
            marker = " [HIGH]"
        elif share < 0.5 * (100 / 24):
            marker = " [DEAD]"
        print(f"  {i:02d}: {share:5.2f}%  {bar}{marker}")

# Also print weekend/Sunday open behaviour for FX vs crypto
print("\n\n=== WEEKEND COVERAGE ===")
for sym in ["XAUUSD", "BTCUSD", "ETHUSD", "USDJPY", "US30_cash"]:
    if sym not in data:
        continue
    # check Sunday gap by seeing if hourly buckets have Sunday data
    # (Sunday = weekday 6, but hourly_buckets doesn't differentiate)
    pass

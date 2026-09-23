# SHORT Direction Validation Batch
# Submit to Claude Code to run the SHORT validation batch
# Estimated cost: $5-12 depending on API calls made
# DO NOT EXECUTE — manual submission only

---

## Objective

Validate whether SHORT trades on bearish D1 days produce a tradeable edge. The current system is long-only. This test determines if we should enable both directions.

## Steps

### 1. Extract Bearish D1 Dates

```python
import json

with open("knowledge_base_backtest/analysis/edge_discovery_d1unclear_20260405.json") as f:
    data = json.load(f)

dc = data["day_classifications"]
xau_bearish = [x["date"] for x in dc if x["symbol"] == "XAUUSD" and x["d1_direction"] == "bearish"]
print(f"Found {len(xau_bearish)} bearish D1 dates")

# Select 25-30 dates spread across the range for representativeness
# Take every other date to get ~28 dates
selected = xau_bearish[::2][:28]
print(f"Selected {len(selected)} dates for batch run")
print(selected)
```

### 2. Run Batch Backtest

Run the existing `batch_backtest.py` on the selected bearish dates. No modifications to the system — just point it at bearish dates.

```bash
python scripts/batch_backtest.py \
    --dates-file /tmp/short_validation_dates.txt \
    --symbol XAUUSD \
    --output-dir knowledge_base_backtest/short_validation
```

If `--dates-file` is not supported, modify the date range in config to cover the bearish dates and filter post-hoc.

Alternative: run the batch manually by setting `START_DATE` and `END_DATE` in the script to cover all bearish dates, then filter session results to only the bearish D1 dates.

### 3. Analyze Results

After the batch completes, analyze:

```python
import json
import glob

sessions = sorted(glob.glob("knowledge_base_backtest/short_validation/sessions/XAUUSD/*.json"))

results = {
    "total_dates": len(sessions),
    "dates_with_candidates": 0,
    "short_trades": [],
    "long_trades": [],
    "no_trade_dates": 0,
}

for sf in sessions:
    with open(sf) as f:
        session = json.load(f)

    trades = session.get("trade_summary", {}).get("trades", [])
    if not trades:
        results["no_trade_dates"] += 1
        continue

    results["dates_with_candidates"] += 1

    for t in trades:
        direction = t.get("direction")
        entry = {
            "date": session["date"],
            "direction": direction,
            "outcome": t.get("outcome"),
            "r_multiple": t.get("r_multiple"),
            "framework": t.get("framework"),
            "kill_zone": t.get("kill_zone"),
        }
        if direction == "SHORT":
            results["short_trades"].append(entry)
        else:
            results["long_trades"].append(entry)

# Compute stats
def stats(trades):
    if not trades:
        return {"n": 0, "wr": 0, "expectancy": 0}
    n = len(trades)
    wins = sum(1 for t in trades if t["outcome"] == "WIN")
    total_r = sum(t.get("r_multiple", 0) or 0 for t in trades)
    return {
        "n": n,
        "wins": wins,
        "wr": round(wins / n, 3),
        "expectancy": round(total_r / n, 4),
        "total_r": round(total_r, 2),
    }

short_stats = stats(results["short_trades"])
long_stats = stats(results["long_trades"])

print("=" * 50)
print("SHORT VALIDATION RESULTS")
print("=" * 50)
print(f"Dates tested: {results['total_dates']}")
print(f"Dates with candidates: {results['dates_with_candidates']}")
print(f"No-trade dates: {results['no_trade_dates']}")
print()
print(f"SHORT trades: {short_stats}")
print(f"LONG trades (against bearish D1): {long_stats}")
print()

# Decision
if short_stats["n"] < 10:
    print("DECISION: INCONCLUSIVE — fewer than 10 SHORT trades. Keep current long-only config.")
elif short_stats["wr"] > 0.5 and short_stats["expectancy"] > 0:
    print("DECISION: ENABLE BOTH DIRECTIONS — SHORT edge confirmed")
    print(f"  SHORT WR={short_stats['wr']:.1%}, Exp={short_stats['expectancy']:.4f}R")
elif short_stats["wr"] < 0.4 or short_stats["expectancy"] < 0:
    print("DECISION: KEEP LONG-ONLY — SHORT edge not viable")
    print(f"  SHORT WR={short_stats['wr']:.1%}, Exp={short_stats['expectancy']:.4f}R")
else:
    print("DECISION: MARGINAL — consider more data before enabling")
    print(f"  SHORT WR={short_stats['wr']:.1%}, Exp={short_stats['expectancy']:.4f}R")
```

### 4. Save Results

Save the full analysis to `knowledge_base_backtest/analysis/short_validation_20260405.json` and `.md`.

## Decision Criteria

| Condition | Action |
|-----------|--------|
| SHORT WR > 50% AND expectancy > 0 | Enable both directions |
| SHORT WR < 40% OR expectancy < 0 | Add `long_only: true` to config |
| < 10 SHORT trades | Inconclusive, keep current config |

## Important Notes

- This prompt runs the EXISTING batch_backtest.py with NO modifications
- The AI prompt already supports SHORT direction — we're testing if it produces viable SHORTs
- The safety check in `_safety_check()` allows SHORTs when D1 is bearish
- Bearish D1 dates are already classified in `edge_discovery_d1unclear_20260405.json`
- 55 bearish D1 dates available; we use 25-28 for cost efficiency

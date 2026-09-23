"""Can we condition the JPY-hour-23 SHORT edge on features to boost WR?

Candidates:
  - Day of week (Mon/Tue/Wed/Thu/Fri)
  - H1 trend direction
  - Proximity to PDH (SHORT at PDH vs SHORT elsewhere)
  - Asian session already started? (in KZ vs out)
  - Preceding 1h return (continuation vs reversal)
"""
import json
from collections import defaultdict
from pathlib import Path

from hour_specific_edges import _binomial_p

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")


def main():
    with open(OUT_DIR / "all_candles_features_outcomes.json", "r", encoding="utf-8") as f:
        d = json.load(f)

    # For each candidate edge, stratify by feature
    edges = [
        ("GBPJPY", 23, "SHORT"),
        ("USDJPY", 23, "SHORT"),
        ("GBPUSD", 23, "SHORT"),
        ("XAUUSD", 11, "SHORT"),
        ("GBPJPY", 22, "SHORT"),
    ]

    for inst, hr, direction in edges:
        print(f"\n=== {inst} hr={hr} {direction} ===")
        matching = [r for r in d["rows"] if r["symbol"] == inst and r["hour_utc"] == hr]

        # Get direction outcomes
        def outcome(r):
            return r["short_outcome"] if direction == "SHORT" else r["long_outcome"]

        resolved = [r for r in matching if outcome(r) in ("WIN", "LOSS")]
        total_w = sum(1 for r in resolved if outcome(r) == "WIN")
        print(f"  Unconditional: n={len(resolved)} WR={total_w/len(resolved):.3f}")

        # Day of week
        print(f"  By day of week:")
        per_dow = defaultdict(lambda: [0, 0])
        for r in resolved:
            per_dow[r["day_of_week"]][0] += 1
            if outcome(r) == "WIN":
                per_dow[r["day_of_week"]][1] += 1
        for dow_i, counts in sorted(per_dow.items()):
            n, w = counts
            wr = w / n if n else 0
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri"][dow_i] if dow_i < 5 else str(dow_i)
            print(f"    {day_name}: n={n} WR={wr:.3f}")

        # H1 dir
        print(f"  By H1 trend:")
        per_h1 = defaultdict(lambda: [0, 0])
        for r in resolved:
            k = r["h1_dir"] or "none"
            per_h1[k][0] += 1
            if outcome(r) == "WIN":
                per_h1[k][1] += 1
        for k, counts in sorted(per_h1.items()):
            n, w = counts
            wr = w / n if n else 0
            print(f"    {k}: n={n} WR={wr:.3f}")

        # D1 dir
        print(f"  By D1 trend:")
        per_d1 = defaultdict(lambda: [0, 0])
        for r in resolved:
            k = r["d1_dir"] or "none"
            per_d1[k][0] += 1
            if outcome(r) == "WIN":
                per_d1[k][1] += 1
        for k, counts in sorted(per_d1.items()):
            n, w = counts
            wr = w / n if n else 0
            print(f"    {k}: n={n} WR={wr:.3f}")

        # Alignment
        print(f"  By D1+H4+H1 alignment:")
        per_al = defaultdict(lambda: [0, 0])
        for r in resolved:
            k = r["alignment_trend"] or "none"
            per_al[k][0] += 1
            if outcome(r) == "WIN":
                per_al[k][1] += 1
        for k, counts in sorted(per_al.items()):
            n, w = counts
            wr = w / n if n else 0
            print(f"    {k}: n={n} WR={wr:.3f}")


if __name__ == "__main__":
    main()

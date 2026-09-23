"""Monthly stability of the strongest hour-specific edges.
If the edge is being arbitraged out, we'd expect WR to decline over 2026.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from hour_specific_edges import _binomial_p

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")


def main():
    with open(OUT_DIR / "all_candles_features_outcomes.json", "r", encoding="utf-8") as f:
        d = json.load(f)

    edges = [
        ("GBPJPY", 23, "SHORT"),
        ("USDJPY", 23, "SHORT"),
        ("GBPUSD", 23, "SHORT"),
        ("GBPJPY", 0, "LONG"),
        ("GBPJPY", 22, "SHORT"),
        ("USDJPY", 22, "SHORT"),
        ("USDJPY", 0, "LONG"),
        ("XAUUSD", 11, "SHORT"),
        ("XAUUSD", 12, "SHORT"),
        ("USDJPY", 19, "LONG"),
        ("EURUSD", 13, "LONG"),
        ("EURUSD", 15, "LONG"),
    ]

    print(f"{'Inst':8s} {'Hr':3s} {'Dir':5s} {'Jan':10s} {'Feb':10s} {'Mar':10s} {'Apr':10s}")
    out_rows = []
    for inst, hr, direction in edges:
        matching = []
        for r in d["rows"]:
            if r["symbol"] != inst or r["hour_utc"] != hr:
                continue
            try:
                dt = datetime.fromisoformat(r["candle_time"].replace(" ", "T"))
            except Exception:
                continue
            r["_dt"] = dt
            matching.append(r)

        by_month = {1: [], 2: [], 3: [], 4: []}
        for r in matching:
            if r["_dt"].month in by_month:
                by_month[r["_dt"].month].append(r)

        row_parts = []
        month_stats = {}
        for m in (1, 2, 3, 4):
            sub = by_month[m]
            if direction == "LONG":
                res = [r for r in sub if r["long_outcome"] in ("WIN", "LOSS")]
                w = sum(1 for r in res if r["long_outcome"] == "WIN")
            else:
                res = [r for r in sub if r["short_outcome"] in ("WIN", "LOSS")]
                w = sum(1 for r in res if r["short_outcome"] == "WIN")
            n = len(res)
            wr = w / n if n else 0
            month_stats[m] = {"n": n, "w": w, "wr": wr}
            row_parts.append(f"{wr:.2f}({n:3d})")
        print(f"{inst:8s} {hr:3d} {direction:5s} {row_parts[0]:10s} {row_parts[1]:10s} {row_parts[2]:10s} {row_parts[3]:10s}")
        out_rows.append({
            "instrument": inst, "hour_utc": hr, "direction": direction,
            "month_stats": month_stats,
        })

    with open(OUT_DIR / "monthly_stability.json", "w", encoding="utf-8") as f:
        json.dump({"rows": out_rows}, f, indent=2)


if __name__ == "__main__":
    main()

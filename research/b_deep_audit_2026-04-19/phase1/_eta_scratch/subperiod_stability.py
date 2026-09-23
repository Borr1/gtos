"""Stability check: do the strong hour-specific directional edges survive subperiod splits?

Split 2026-01-02 to 2026-04-17 into two halves:
  H1: 2026-01-02 → 2026-02-28
  H2: 2026-03-01 → 2026-04-17
If an edge holds in BOTH halves at raw p<0.10, it's much more robust than whole-sample only.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from hour_specific_edges import _binomial_p

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")


def main():
    with open(OUT_DIR / "all_candles_features_outcomes.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    rows = d["rows"]

    # Split
    split_date = datetime(2026, 3, 1, tzinfo=timezone.utc)
    for r in rows:
        t = r["candle_time"]
        if isinstance(t, str):
            # Parse '2026-01-02 01:00:00+00:00'
            try:
                dt = datetime.fromisoformat(t.replace(" ", "T"))
            except Exception:
                dt = None
            r["_dt"] = dt

    half1 = [r for r in rows if r.get("_dt") and r["_dt"] < split_date]
    half2 = [r for r in rows if r.get("_dt") and r["_dt"] >= split_date]
    print(f"H1 (pre-Mar) n={len(half1)}  H2 (Mar-Apr) n={len(half2)}")

    # Strong edges to check
    edges_to_verify = [
        ("GBPJPY", 23, "SHORT"),
        ("USDJPY", 23, "SHORT"),
        ("GBPUSD", 23, "SHORT"),
        ("GBPJPY", 0, "LONG"),
        ("GBPJPY", 22, "SHORT"),
        ("USDJPY", 22, "SHORT"),
        ("USDJPY", 0, "LONG"),
        ("XAUUSD", 11, "SHORT"),
        ("USDJPY", 19, "LONG"),
        ("EURUSD", 13, "LONG"),
        ("XAUUSD", 12, "SHORT"),
        ("EURUSD", 15, "LONG"),
    ]

    out = []
    for inst, hr, direction in edges_to_verify:
        for label, subset in (("H1", half1), ("H2", half2)):
            rs = [r for r in subset if r["symbol"] == inst and r["hour_utc"] == hr]
            if direction == "LONG":
                resolved = [r for r in rs if r["long_outcome"] in ("WIN", "LOSS")]
                wins = sum(1 for r in resolved if r["long_outcome"] == "WIN")
            else:
                resolved = [r for r in rs if r["short_outcome"] in ("WIN", "LOSS")]
                wins = sum(1 for r in resolved if r["short_outcome"] == "WIN")
            n = len(resolved)
            wr = wins / n if n else 0
            p_raw = _binomial_p(wins, n, 0.4) if n >= 20 else None
            out.append({
                "instrument": inst, "hour_utc": hr, "direction": direction, "period": label,
                "n": n, "wins": wins, "wr": wr,
                "p_raw_vs_0.40": p_raw,
            })

    print(f"\n{'Inst':8s} {'Hr':2s} {'Dir':5s} {'Per':3s} {'n':4s} {'W':4s} {'WR':6s} {'p(wr>0.40)':12s}")
    for r in out:
        p_str = f"{r['p_raw_vs_0.40']:.4f}" if r['p_raw_vs_0.40'] is not None else 'na'
        flag = '  '
        if r['n'] >= 50 and r['wr'] >= 0.46:
            flag = '**'
        elif r['n'] >= 20 and r['wr'] >= 0.46:
            flag = '* '
        print(f"{flag}{r['instrument']:8s} {r['hour_utc']:2d} {r['direction']:5s} {r['period']:3s} {r['n']:4d} {r['wins']:4d} {r['wr']:.3f}  {p_str}")

    with open(OUT_DIR / "subperiod_stability.json", "w", encoding="utf-8") as f:
        json.dump({"edges_verified": out}, f, indent=2)


if __name__ == "__main__":
    main()

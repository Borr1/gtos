"""Apply a realistic spread + slippage haircut.

For each hour-edge, compute the WR if:
  - Entry is slipped by 0.05 × ATR_m15 against us (typical limit-fill risk)
  - SL is expanded by 0.05 × ATR (spread widens at thin hours)
  - TP must be hit by close (more conservative than wick-touches)
We apply all three.

Compare to the original optimistic WR.
"""
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from hour_specific_edges import _binomial_p

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")


def main():
    import sys
    sys.path.insert(0, str(OUT_DIR))
    from load_data import load_m15
    from forward_replay import replay_hypothetical

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
    ]

    m15_cache = {}
    insts = set(e[0] for e in edges)
    for inst in insts:
        m15_cache[inst] = load_m15(inst)

    print(f"{'Inst':8s} {'Hr':3s} {'Dir':5s} {'Baseline WR':15s} {'Haircut WR (SL=1.1ATR, TP=1.4ATR)':40s}  delta")

    for inst, hr, direction in edges:
        m15 = m15_cache[inst]
        # Find all M15 candles at this hour
        matches = [i for i, c in enumerate(m15)
                   if c["time"].hour == hr and c["time"].weekday() < 5 and i >= 100 and i + 16 < len(m15)]
        if len(matches) < 30:
            continue

        # Baseline: SL=1.0 ATR / TP=1.5 ATR
        baseline_w, baseline_n = 0, 0
        hc_w, hc_n = 0, 0
        for idx in matches:
            base = replay_hypothetical(m15, idx, horizon_minutes=4 * 60,
                                       sl_atr_mult=1.0, tp_atr_mult=1.5)
            if base is None:
                continue
            oc = base["short_outcome"] if direction == "SHORT" else base["long_outcome"]
            if oc == "WIN":
                baseline_w += 1
                baseline_n += 1
            elif oc == "LOSS":
                baseline_n += 1

            # Haircut: SL 1.1 ATR (slightly wider due to spread widening), TP 1.4 ATR (require close-based confirmation, approximated by tighter TP)
            hc = replay_hypothetical(m15, idx, horizon_minutes=4 * 60,
                                     sl_atr_mult=1.1, tp_atr_mult=1.4)
            if hc is None:
                continue
            oc2 = hc["short_outcome"] if direction == "SHORT" else hc["long_outcome"]
            if oc2 == "WIN":
                hc_w += 1
                hc_n += 1
            elif oc2 == "LOSS":
                hc_n += 1

        base_wr = baseline_w / baseline_n if baseline_n else 0
        hc_wr = hc_w / hc_n if hc_n else 0
        delta = hc_wr - base_wr
        # ExpR on haircut geometry: WIN = 1.4/1.1 = 1.27R; LOSS = -1R
        exp_r_hc = (hc_w * (1.4 / 1.1) - (hc_n - hc_w) * 1.0) / hc_n if hc_n else 0
        exp_r_base = (baseline_w * 1.5 - (baseline_n - baseline_w) * 1.0) / baseline_n if baseline_n else 0

        print(f"{inst:8s} {hr:3d} {direction:5s} {base_wr:.3f}(n={baseline_n:3d},Exp={exp_r_base:+.2f}) {hc_wr:.3f}(n={hc_n:3d},Exp={exp_r_hc:+.2f})       d={delta:+.3f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""LIRA SL-geometry diagnostic.

Tests the DP4-extension hypothesis that LIRA places XAUUSD SHORT SLs more
correctly than V3. Compares LIRA + A2 candidates side-by-side at the same
candle_time + symbol + direction:

  - For each (slice, candle_time, direction) tuple where BOTH LIRA and A2
    emitted CANDIDATEs, compare the SL placement.
  - Report cases where SLs differ by >5% (geometry divergence).
  - Highlight cases where LIRA WIN + A2 LOSS or vice versa (outcome divergence
    with same setup).

Reads:
  research/lira_ab_backtest/slices/<slice>/all_results.json
  research/a2_v2_active_backtest/slices/<slice>/all_results.json

Usage:
  python research/lira_ab_backtest/sl_geometry_diagnostic.py \
    --out-md research/lira_ab_backtest/SL_GEOMETRY_DIAGNOSTIC.md
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path


def load_cands(slice_dir: str) -> dict:
    """Returns {(slice_name, candle_time, direction): result_dict}."""
    out = {}
    for s in sorted(os.listdir(slice_dir)):
        sdir = os.path.join(slice_dir, s)
        ar = os.path.join(sdir, "all_results.json")
        if not os.path.isfile(ar):
            continue
        with open(ar) as f:
            d = json.load(f)
        for r in d.get("results", []):
            if r.get("decision") != "CANDIDATE":
                continue
            key = (s, r.get("candle_time"), r.get("direction"))
            out[key] = r
    return out


def render_md(lira_cands: dict, a2_cands: dict) -> str:
    lines = ["# LIRA SHORT-SL Geometry Diagnostic", ""]
    lines.append("Tests DP4 extension hypothesis: LIRA places XAUUSD SHORT SLs "
                 "more correctly than V3 (which DP4 found misplaced 2/3 SHORTs "
                 "in xauusd_s7 — one wrong-side, one tight-sweep).")
    lines.append("")

    # Index by (slice, time) key — direction may differ between variants
    common_keys = set(lira_cands.keys()) & set(a2_cands.keys())
    only_lira = set(lira_cands.keys()) - set(a2_cands.keys())
    only_a2 = set(a2_cands.keys()) - set(lira_cands.keys())

    lines.append(f"## Coverage: LIRA={len(lira_cands)} CANDs / "
                 f"A2={len(a2_cands)} CANDs")
    lines.append("")
    lines.append(f"- Both produced CAND at same (slice, candle, direction): {len(common_keys)}")
    lines.append(f"- LIRA-only CANDs: {len(only_lira)}")
    lines.append(f"- A2-only CANDs: {len(only_a2)}")
    lines.append("")

    # Per-slice breakdown
    by_slice = defaultdict(lambda: {"common": 0, "lira_only": 0, "a2_only": 0,
                                    "lira_short": 0, "a2_short": 0,
                                    "lira_short_win": 0, "a2_short_win": 0})
    for k in lira_cands:
        s, _, d = k
        if k in a2_cands:
            by_slice[s]["common"] += 1
        else:
            by_slice[s]["lira_only"] += 1
        if d == "SHORT":
            by_slice[s]["lira_short"] += 1
            if lira_cands[k].get("outcome") == "WIN":
                by_slice[s]["lira_short_win"] += 1
    for k in a2_cands:
        s, _, d = k
        if k not in lira_cands:
            by_slice[s]["a2_only"] += 1
        if d == "SHORT":
            by_slice[s]["a2_short"] += 1
            if a2_cands[k].get("outcome") == "WIN":
                by_slice[s]["a2_short_win"] += 1

    lines.append("## Per-slice CAND coverage")
    lines.append("")
    lines.append("| Slice | Common | LIRA-only | A2-only | LIRA SHORT (WIN) | A2 SHORT (WIN) |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for s in sorted(by_slice):
        d = by_slice[s]
        lines.append(f"| {s} | {d['common']} | {d['lira_only']} | {d['a2_only']} | "
                     f"{d['lira_short']} ({d['lira_short_win']}) | "
                     f"{d['a2_short']} ({d['a2_short_win']}) |")
    lines.append("")

    # SL divergence analysis on common keys
    sl_diffs = []
    outcome_diffs = []
    for k in common_keys:
        lira = lira_cands[k]
        a2 = a2_cands[k]
        sl_lira = float(lira.get("stop_loss", 0))
        sl_a2 = float(a2.get("stop_loss", 0))
        entry_lira = float(lira.get("entry_price", 1) or 1)
        if entry_lira and abs(sl_lira - sl_a2) / entry_lira > 0.001:  # >0.1%
            sl_diffs.append((k, sl_lira, sl_a2, lira, a2))
        if lira.get("outcome") and a2.get("outcome") and lira.get("outcome") != a2.get("outcome"):
            outcome_diffs.append((k, lira, a2))

    lines.append(f"## SL-placement divergence (common CANDs, |SL_lira - SL_a2| / entry > 0.5%)")
    lines.append("")
    if not sl_diffs:
        lines.append("None — LIRA and A2 placed identical SLs on all shared CANDs.")
    else:
        lines.append("| Slice | Time | Dir | Entry | SL_LIRA | SL_A2 | Delta | LIRA outcome | A2 outcome |")
        lines.append("|---|---|---|---:|---:|---:|---:|---|---|")
        for k, sl_lira, sl_a2, lira, a2 in sl_diffs:
            entry = lira.get("entry_price", 0)
            delta_abs = abs(sl_lira - sl_a2)
            delta_pct = delta_abs / entry * 100 if entry else 0
            lines.append(f"| {k[0]} | {k[1]} | {k[2]} | {entry:.5f} | {sl_lira:.5f} | "
                         f"{sl_a2:.5f} | {delta_abs:.5f} ({delta_pct:.2f}%) | "
                         f"{lira.get('outcome', '?')} | {a2.get('outcome', '?')} |")
    lines.append("")

    lines.append(f"## Outcome divergence (same setup, different outcome)")
    lines.append("")
    if not outcome_diffs:
        lines.append("None — when both LIRA and A2 produced same CAND, outcomes matched.")
    else:
        lines.append("| Slice | Time | Dir | LIRA outcome | LIRA R | A2 outcome | A2 R |")
        lines.append("|---|---|---|---|---:|---|---:|")
        for k, lira, a2 in outcome_diffs:
            lines.append(f"| {k[0]} | {k[1]} | {k[2]} | "
                         f"{lira.get('outcome', '?')} | {lira.get('r_multiple', 0):+.2f} | "
                         f"{a2.get('outcome', '?')} | {a2.get('r_multiple', 0):+.2f} |")
    lines.append("")

    lines.append("## XAUUSD SHORT detail (DP4 hypothesis target)")
    lines.append("")
    lira_xau_shorts = [(k, v) for k, v in lira_cands.items() if k[2] == "SHORT" and "xauusd" in k[0]]
    a2_xau_shorts = [(k, v) for k, v in a2_cands.items() if k[2] == "SHORT" and "xauusd" in k[0]]
    lines.append(f"- LIRA XAUUSD SHORT CANDs: {len(lira_xau_shorts)}")
    lines.append(f"- A2 XAUUSD SHORT CANDs: {len(a2_xau_shorts)}")
    lines.append("")
    if lira_xau_shorts:
        lines.append("### LIRA XAUUSD SHORTs")
        lines.append("")
        lines.append("| Slice | Time | Entry | SL | TP1 | Outcome | R |")
        lines.append("|---|---|---:|---:|---:|---|---:|")
        for k, v in sorted(lira_xau_shorts):
            lines.append(f"| {k[0]} | {k[1]} | {float(v.get('entry_price', 0)):.2f} | "
                         f"{float(v.get('stop_loss', 0)):.2f} | "
                         f"{float(v.get('take_profit_1', 0)):.2f} | "
                         f"{v.get('outcome', 'pending')} | "
                         f"{v.get('r_multiple', 0):+.2f} |")
        lines.append("")
    if a2_xau_shorts:
        lines.append("### A2 XAUUSD SHORTs (V3 baseline)")
        lines.append("")
        lines.append("| Slice | Time | Entry | SL | TP1 | Outcome | R |")
        lines.append("|---|---|---:|---:|---:|---|---:|")
        for k, v in sorted(a2_xau_shorts):
            lines.append(f"| {k[0]} | {k[1]} | {float(v.get('entry_price', 0)):.2f} | "
                         f"{float(v.get('stop_loss', 0)):.2f} | "
                         f"{float(v.get('take_profit_1', 0)):.2f} | "
                         f"{v.get('outcome', 'pending')} | "
                         f"{v.get('r_multiple', 0):+.2f} |")
        lines.append("")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lira-slice-dir", default="research/lira_ab_backtest/slices")
    p.add_argument("--a2-slice-dir", default="research/a2_v2_active_backtest/slices")
    p.add_argument("--out-md", default="research/lira_ab_backtest/SL_GEOMETRY_DIAGNOSTIC.md")
    args = p.parse_args()

    lira_cands = load_cands(args.lira_slice_dir)
    a2_cands = load_cands(args.a2_slice_dir)

    md = render_md(lira_cands, a2_cands)
    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {args.out_md}")
    print(f"LIRA CANDs: {len(lira_cands)}, A2 CANDs: {len(a2_cands)}")


if __name__ == "__main__":
    main()

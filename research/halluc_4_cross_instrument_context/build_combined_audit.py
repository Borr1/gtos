"""HALLUC-4 combined audit — trade_records + live_evaluations.

Trade records give us the prompt + AI response and let us *directly* observe
ci_block presence. Live_evaluations are summary-only but a much larger sample
to read AI rationale citing XAU/gold even after the block was disabled
(checks for residual XAU bias from system prompt or training).

Adds to the trade-record audit:
  - GBPUSD daily breakdown of XAU citation rate before/after Apr 14 disable
  - All non-XAU instruments: XAU citation rate from live_evaluations
  - Verify: any non-GBPUSD instrument shows XAU citations? (would be unexpected)
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LE_BASE = REPO_ROOT / "knowledge_base" / "live_evaluations"
OUT_DIR = Path(__file__).resolve().parent

# Apr 14 == ci_block disabled per yaml comment
CI_BLOCK_DISABLED_FROM = "2026-04-14"

XAU_PAT = re.compile(
    r"\bXAU(?:USD)?\b|\bgold\b|\bdollar\s+(weak|strong|str|wk)|macro\s+head ?wind",
    re.I,
)


def main():
    # --- Live evaluations: per-symbol per-date XAU citation tally ---
    by_sym_date = defaultdict(lambda: defaultdict(lambda: {"total": 0, "xau_hits": 0}))

    for sym_dir in sorted(LE_BASE.iterdir()):
        if not sym_dir.is_dir():
            continue
        sym = sym_dir.name
        for fp in sorted(sym_dir.glob("*.jsonl")):
            date = fp.stem
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    by_sym_date[sym][date]["total"] += 1
                    texts = []
                    for k in ("overall_reasoning", "no_trade_reason", "wait_reason"):
                        v = d.get(k, "")
                        if isinstance(v, str):
                            texts.append(v)
                    full = " ".join(texts)
                    if XAU_PAT.search(full):
                        by_sym_date[sym][date]["xau_hits"] += 1

    # --- Aggregate ---
    sym_summary = {}
    for sym, dates in by_sym_date.items():
        total_total = 0
        total_hits = 0
        pre_total = 0
        pre_hits = 0
        post_total = 0
        post_hits = 0
        for date, st in dates.items():
            total_total += st["total"]
            total_hits += st["xau_hits"]
            if date < CI_BLOCK_DISABLED_FROM:
                pre_total += st["total"]
                pre_hits += st["xau_hits"]
            else:
                post_total += st["total"]
                post_hits += st["xau_hits"]
        sym_summary[sym] = {
            "total_evaluations": total_total,
            "total_xau_hits": total_hits,
            "total_xau_pct": (total_hits / total_total * 100) if total_total else 0,
            "pre_apr14_total": pre_total,
            "pre_apr14_xau_hits": pre_hits,
            "pre_apr14_xau_pct": (pre_hits / pre_total * 100) if pre_total else 0,
            "post_apr14_total": post_total,
            "post_apr14_xau_hits": post_hits,
            "post_apr14_xau_pct": (post_hits / post_total * 100) if post_total else 0,
        }

    # --- Write ---
    with open(OUT_DIR / "live_evaluations_xau_audit.json", "w", encoding="utf-8") as f:
        json.dump({
            "by_sym_date": {sym: dict(d) for sym, d in by_sym_date.items()},
            "sym_summary": sym_summary,
        }, f, indent=2)

    with open(OUT_DIR / "live_evaluations_xau_summary.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "symbol", "total_evaluations", "total_xau_hits", "total_xau_pct",
            "pre_apr14_total", "pre_apr14_xau_hits", "pre_apr14_xau_pct",
            "post_apr14_total", "post_apr14_xau_hits", "post_apr14_xau_pct",
        ])
        for sym, s in sorted(sym_summary.items()):
            w.writerow([
                sym, s["total_evaluations"], s["total_xau_hits"], f"{s['total_xau_pct']:.1f}",
                s["pre_apr14_total"], s["pre_apr14_xau_hits"], f"{s['pre_apr14_xau_pct']:.1f}",
                s["post_apr14_total"], s["post_apr14_xau_hits"], f"{s['post_apr14_xau_pct']:.1f}",
            ])

    # Print
    print(f"{'symbol':<12} {'pre':>15} {'post':>15} {'total':>15}")
    print("-" * 65)
    for sym, s in sorted(sym_summary.items()):
        pre_str = f"{s['pre_apr14_xau_hits']}/{s['pre_apr14_total']}={s['pre_apr14_xau_pct']:.1f}%"
        post_str = f"{s['post_apr14_xau_hits']}/{s['post_apr14_total']}={s['post_apr14_xau_pct']:.1f}%"
        tot_str = f"{s['total_xau_hits']}/{s['total_evaluations']}={s['total_xau_pct']:.1f}%"
        print(f"{sym:<12} {pre_str:>15} {post_str:>15} {tot_str:>15}")

    return sym_summary


if __name__ == "__main__":
    main()

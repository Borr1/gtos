#!/usr/bin/env python3
"""Compare vision A/B test results against Session 4 smoke test (JSON-only)."""

import json, statistics
from collections import Counter
from pathlib import Path
from datetime import datetime

KB = Path("knowledge_base_backtest")
ANALYSIS = KB / "analysis"
BATCH = KB / "batch_api"

def load_trades_from_batch(batch_id):
    """Load trades from a batch result file."""
    results = json.loads((BATCH / f"{batch_id}_results.json").read_text())
    responses_dir = BATCH / "responses"
    trades = []
    for r in results:
        if not r.get("trade_taken"):
            continue
        resp_file = responses_dir / f"{r['date']}_responses.json"
        responses = json.loads(resp_file.read_text()) if resp_file.exists() else {}
        for t in r.get("trades", []):
            trade = {
                "date": r["date"], "kill_zone": t.get("kill_zone"),
                "framework": t.get("framework"), "outcome": t.get("outcome"),
                "r_multiple": t.get("r_multiple", 0), "mfe_r": t.get("mfe_r"),
                "mae_r": t.get("mae_r"), "exit_substate": t.get("exit_substate"),
            }
            for key, resp in responses.items():
                if resp.get("decision") == "CANDIDATE" and resp.get("kill_zone") == t.get("kill_zone"):
                    trade["confidence_score"] = resp.get("confidence_score")
                    trade["confidence_computation"] = resp.get("confidence_computation")
                    trade["setup_grade"] = resp.get("reasoning", {}).get("setup_grade")
                    trade["direction"] = resp.get("trade_parameters", {}).get("direction") if resp.get("trade_parameters") else None
                    break
            trades.append(trade)
    return trades, results

# Find the two batches for Oct 2025
# Session 4 smoke test: msgbatch_01VCZZM7cCZhW9Nb9MybySZq
# Vision batch: latest with vision (the one we just ran)
print("=" * 72)
print("VISION A/B TEST COMPARISON — Oct 2025")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 72)

# Load JSON-only baseline (Session 4 smoke test)
json_batch = "msgbatch_01VCZZM7cCZhW9Nb9MybySZq"
json_trades, json_results = load_trades_from_batch(json_batch)
print(f"\nJSON-only batch: {json_batch}")
print(f"  Trades: {len(json_trades)}")

# Find the vision batch (most recent)
result_files = sorted(BATCH.glob("msgbatch_*_results.json"), key=lambda p: p.stat().st_mtime, reverse=True)
vision_batch_id = None
for rf in result_files:
    bid = rf.stem.replace("_results", "")
    if bid != json_batch:
        vision_batch_id = bid
        break

if not vision_batch_id:
    print("ERROR: No vision batch found!")
    exit(1)

vision_trades, vision_results = load_trades_from_batch(vision_batch_id)
print(f"Vision batch: {vision_batch_id}")
print(f"  Trades: {len(vision_trades)}")

# ═══ Overall comparison ═══
print(f"\n## Overall Comparison\n")
for label, trades in [("JSON-only", json_trades), ("JSON+Vision", vision_trades)]:
    n = len(trades)
    if n == 0:
        print(f"  {label}: 0 trades"); continue
    w = sum(1 for t in trades if t["outcome"] == "WIN")
    tr = sum(t["r_multiple"] for t in trades)
    confs = [t.get("confidence_score") for t in trades if t.get("confidence_score")]
    print(f"  {label}: {n} trades, {w}W/{n-w}L, WR {w/n*100:.1f}%, "
          f"Total {tr:+.2f}R, Exp {tr/n:+.3f}R")
    if confs:
        print(f"    Confidence: {Counter(confs).most_common(5)}, "
              f"std={statistics.stdev(confs):.1f}" if len(set(confs))>1 else f"    Confidence: all={confs[0]}")

# ═══ Trade-by-trade diff ═══
print(f"\n## Trade-by-Trade Diff\n")
json_by_date_kz = {(t["date"], t["kill_zone"]): t for t in json_trades}
vision_by_date_kz = {(t["date"], t["kill_zone"]): t for t in vision_trades}

all_keys = set(json_by_date_kz.keys()) | set(vision_by_date_kz.keys())
shared = set(json_by_date_kz.keys()) & set(vision_by_date_kz.keys())
json_only_keys = set(json_by_date_kz.keys()) - set(vision_by_date_kz.keys())
vision_only_keys = set(vision_by_date_kz.keys()) - set(json_by_date_kz.keys())

print(f"  Shared trades (both took): {len(shared)}")
print(f"  JSON-only trades (vision skipped): {len(json_only_keys)}")
print(f"  Vision-only trades (JSON skipped): {len(vision_only_keys)}")

for key in sorted(json_only_keys):
    t = json_by_date_kz[key]
    print(f"  LOST: {key[0]} {key[1]} — JSON had {t['outcome']} {t['r_multiple']:+.2f}R")

for key in sorted(vision_only_keys):
    t = vision_by_date_kz[key]
    print(f"  NEW:  {key[0]} {key[1]} — Vision produced {t['outcome']} {t['r_multiple']:+.2f}R")

# Shared trades comparison
if shared:
    print(f"\n## Shared Trade Outcomes\n")
    for key in sorted(shared):
        jt = json_by_date_kz[key]
        vt = vision_by_date_kz[key]
        diff = vt["r_multiple"] - jt["r_multiple"]
        marker = "  " if abs(diff) < 0.1 else ("▲ " if diff > 0 else "▼ ")
        print(f"  {marker}{key[0]} {key[1]:>7}: JSON {jt['r_multiple']:+.2f}R → Vision {vt['r_multiple']:+.2f}R ({diff:+.2f}R)")

# ═══ Confidence comparison ═══
print(f"\n## Confidence Score Comparison\n")
for label, trades in [("JSON-only", json_trades), ("JSON+Vision", vision_trades)]:
    confs = [t["confidence_score"] for t in trades if t.get("confidence_score") is not None]
    if confs:
        unique = len(set(confs))
        std = statistics.stdev(confs) if len(confs) > 1 and unique > 1 else 0
        print(f"  {label}: {Counter(confs).most_common(5)}, unique={unique}, std={std:.1f}")
        # Show computations
        comps = [t.get("confidence_computation", "") for t in trades if t.get("confidence_computation")]
        if comps:
            for c in comps[:3]:
                print(f"    → {c}")

# ═══ Verdict ═══
print(f"\n## Verdict\n")
json_exp = sum(t["r_multiple"] for t in json_trades) / len(json_trades) if json_trades else 0
vision_exp = sum(t["r_multiple"] for t in vision_trades) / len(vision_trades) if vision_trades else 0
json_wr = sum(1 for t in json_trades if t["outcome"]=="WIN") / len(json_trades) if json_trades else 0
vision_wr = sum(1 for t in vision_trades if t["outcome"]=="WIN") / len(vision_trades) if vision_trades else 0

print(f"  WR change: {json_wr*100:.1f}% → {vision_wr*100:.1f}% ({(vision_wr-json_wr)*100:+.1f}%)")
print(f"  Exp change: {json_exp:+.3f}R → {vision_exp:+.3f}R ({vision_exp-json_exp:+.3f}R)")

wr_threshold = 3.0  # percentage points
exp_threshold = 0.03
if (vision_wr - json_wr) * 100 >= wr_threshold or (vision_exp - json_exp) >= exp_threshold:
    print(f"  → INCLUDE VISION: Meaningful improvement detected")
else:
    print(f"  → DO NOT INCLUDE VISION: Improvement below threshold (WR +{wr_threshold}% or Exp +{exp_threshold}R)")
    print(f"  Note: This is based on a small sample (Oct 2025 only). A full-range test would be more conclusive.")

# Save report
report_path = ANALYSIS / "vision_ab_test_report.md"
# The stdout output IS the report — redirect when running
print(f"\nTo save: python3 scripts/vision_comparison.py > {report_path}")

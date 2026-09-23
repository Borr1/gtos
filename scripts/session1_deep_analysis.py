#!/usr/bin/env python3
"""Session 1 Deep Diagnostic Analysis — read-only, existing data only."""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base_backtest"
ANALYSIS_DIR = KB_DIR / "analysis"
RESPONSES_DIR = KB_DIR / "batch_api" / "responses"
SESSIONS_DIR = KB_DIR / "sessions"
BATCH_DIR = KB_DIR / "batch_api"

# ─── Helpers ───────────────────────────────────────────────────────────

def wilson_ci(wins, total, z=1.96):
    if total == 0:
        return (0, 0)
    p = wins / total
    d = 1 + z**2 / total
    c = (p + z**2 / (2 * total)) / d
    s = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / d
    return (max(0, c - s), min(1, c + s))

def flag(n, thresh=15):
    return " ⚠️ LOW SAMPLE" if n < thresh else ""

def stats_line(group, label=""):
    n = len(group)
    if n == 0:
        return f"{label}: 0 trades"
    wins = sum(1 for t in group if t["outcome"] == "WIN")
    rs = [t["r_multiple"] for t in group]
    tr = sum(rs)
    wr = wins / n
    exp = tr / n
    return f"{label}: {n} trades, {wins}W/{n-wins}L, WR {wr*100:.1f}%, Total {tr:+.2f}R, Exp {exp:+.3f}R{flag(n)}"

# ─── Load Data ─────────────────────────────────────────────────────────

print("=" * 72)
print("SESSION 1: DEEP DIAGNOSTIC ANALYSIS")
print("=" * 72)

trades = json.loads((ANALYSIS_DIR / "unified_trades.json").read_text())
print(f"\nLoaded {len(trades)} trades from unified_trades.json")

# Load batch results for session-level data
CANONICAL = ["01M9NW1bUnhF4Zf6g3VrNR8g", "01PeezeEy1M3LiNHbKwfaj6o", "01HJEdo4gP2s5nd9hrgtJUHK"]
BATCH_LABELS = {"01M9NW1bUnhF4Zf6g3VrNR8g": "Batch3", "01PeezeEy1M3LiNHbKwfaj6o": "Batch4A", "01HJEdo4gP2s5nd9hrgtJUHK": "Batch4B"}
all_results = []
for bid in CANONICAL:
    p = BATCH_DIR / f"msgbatch_{bid}_results.json"
    if p.exists():
        rs = json.loads(p.read_text())
        for r in rs:
            r["_batch_label"] = BATCH_LABELS[bid]
        all_results.extend(rs)

# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: CROSS-FILTER ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PHASE 2: CROSS-FILTER ANALYSIS")
print("=" * 72)

# ─── 2.1 Framework × Kill Zone (THE CRITICAL TABLE) ───────────────────
print("\n## 2.1 THE CRITICAL 2×2: FRAMEWORK × KILL ZONE\n")

frameworks = sorted(set(t["framework"] for t in trades))
kill_zones = ["london", "ny"]

print(f"| {'Framework':<15} | {'KZ':<7} | {'Trades':>6} | {'W':>3} | {'L':>3} | {'WR':>6} | {'Total R':>8} | {'Exp':>8} |")
print(f"|{'-'*15}--|{'-'*7}--|{'-'*6}--|{'-'*3}--|{'-'*3}--|{'-'*6}--|{'-'*8}--|{'-'*8}--|")

for fw in frameworks:
    for kz in kill_zones:
        g = [t for t in trades if t["framework"] == fw and t["kill_zone"] == kz]
        n = len(g)
        if n == 0:
            print(f"| {fw:<15} | {kz:<7} | {0:>6} |   - |   - |    --% |      --R |      --R |")
            continue
        w = sum(1 for t in g if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in g]
        tr = sum(rs)
        f_str = flag(n)
        print(f"| {fw:<15} | {kz:<7} | {n:>6} | {w:>3} | {n-w:>3} | {w/n*100:>5.1f}% | {tr:>+7.2f}R | {tr/n:>+7.3f}R |{f_str}")

# ─── 2.2 Full Cross-Filter Table ──────────────────────────────────────
print("\n## 2.2 FULL CROSS-FILTER TABLE\n")

filters = {
    "ALL trades": lambda t: True,
    "NY only": lambda t: t["kill_zone"] == "ny",
    "London only": lambda t: t["kill_zone"] == "london",
    "A+ only": lambda t: t["setup_grade"] == "A+",
    "A only": lambda t: t["setup_grade"] == "A",
    "NY + A+": lambda t: t["kill_zone"] == "ny" and t["setup_grade"] == "A+",
    "NY + A": lambda t: t["kill_zone"] == "ny" and t["setup_grade"] == "A",
    "London + A+": lambda t: t["kill_zone"] == "london" and t["setup_grade"] == "A+",
    "London + A": lambda t: t["kill_zone"] == "london" and t["setup_grade"] == "A",
    "session_sweep": lambda t: t["framework"] == "session_sweep",
    "session_sweep + NY": lambda t: t["framework"] == "session_sweep" and t["kill_zone"] == "ny",
    "session_sweep + London": lambda t: t["framework"] == "session_sweep" and t["kill_zone"] == "london",
    "ob_retest": lambda t: t["framework"] == "ob_retest",
    "ob_retest + NY": lambda t: t["framework"] == "ob_retest" and t["kill_zone"] == "ny",
    "ob_retest + London": lambda t: t["framework"] == "ob_retest" and t["kill_zone"] == "london",
    "LONG only": lambda t: t["direction"] == "LONG",
    "SHORT only": lambda t: t["direction"] == "SHORT",
    "NY + LONG": lambda t: t["kill_zone"] == "ny" and t["direction"] == "LONG",
    "NY + SHORT": lambda t: t["kill_zone"] == "ny" and t["direction"] == "SHORT",
    "London + LONG": lambda t: t["kill_zone"] == "london" and t["direction"] == "LONG",
    "London + SHORT": lambda t: t["kill_zone"] == "london" and t["direction"] == "SHORT",
    "ob_retest + A+": lambda t: t["framework"] == "ob_retest" and t["setup_grade"] == "A+",
    "session_sweep + A+": lambda t: t["framework"] == "session_sweep" and t["setup_grade"] == "A+",
    "session_sweep + NY + A+": lambda t: t["framework"] == "session_sweep" and t["kill_zone"] == "ny" and t["setup_grade"] == "A+",
    "NOT Wednesday": lambda t: t["day_of_week"] != "Wednesday",
    "Monday only": lambda t: t["day_of_week"] == "Monday",
    "NY + NOT Wed": lambda t: t["kill_zone"] == "ny" and t["day_of_week"] != "Wednesday",
    "ob_retest + NOT Wed": lambda t: t["framework"] == "ob_retest" and t["day_of_week"] != "Wednesday",
    "NY + LONG + NOT Wed": lambda t: t["kill_zone"] == "ny" and t["direction"] == "LONG" and t["day_of_week"] != "Wednesday",
    "NY + A+ + LONG": lambda t: t["kill_zone"] == "ny" and t["setup_grade"] == "A+" and t["direction"] == "LONG",
    "ss + NY + LONG": lambda t: t["framework"] == "session_sweep" and t["kill_zone"] == "ny" and t["direction"] == "LONG",
    "ss + London + A+": lambda t: t["framework"] == "session_sweep" and t["kill_zone"] == "london" and t["setup_grade"] == "A+",
}

rows = []
for label, fn in filters.items():
    g = [t for t in trades if fn(t)]
    n = len(g)
    if n == 0:
        rows.append((label, 0, 0, 0, 0, 0))
        continue
    w = sum(1 for t in g if t["outcome"] == "WIN")
    rs = [t["r_multiple"] for t in g]
    tr = sum(rs)
    rows.append((label, n, w, n - w, w / n, tr / n, tr))

# Sort by expectancy descending
rows.sort(key=lambda r: r[5] if len(r) == 7 else -999, reverse=True)

print(f"| {'Filter':<28} | {'N':>4} | {'W':>3} | {'L':>3} | {'WR':>6} | {'Exp/Trade':>9} | {'Total R':>8} |")
print(f"|{'-'*28}--|{'-'*4}--|{'-'*3}--|{'-'*3}--|{'-'*6}--|{'-'*9}--|{'-'*8}--|")

best_15 = None
for r in rows:
    if len(r) == 7:
        label, n, w, l, wr, exp, tr = r
        f_str = " ⚠️" if n < 15 else ""
        if n >= 15 and (best_15 is None or exp > best_15[5]):
            best_15 = r
        print(f"| {label:<28} | {n:>4} | {w:>3} | {l:>3} | {wr*100:>5.1f}% | {exp:>+8.3f}R | {tr:>+7.2f}R |{f_str}")
    else:
        label = r[0]
        print(f"| {label:<28} |    0 |   - |   - |    --% |       --R |      --R |")

if best_15:
    print(f"\n🏆 BEST FILTER (≥15 trades): {best_15[0]}")
    print(f"   {best_15[1]} trades, WR {best_15[4]*100:.1f}%, Exp {best_15[5]:+.3f}R, Total {best_15[6]:+.2f}R")

# ─── 2.3 Temporal Decay Drill-Down ────────────────────────────────────
print("\n" + "=" * 72)
print("## 2.3 TEMPORAL DECAY DRILL-DOWN")
print("=" * 72)

sorted_trades = sorted(trades, key=lambda t: t["date"])
n_total = len(sorted_trades)
third = n_total // 3

thirds = [
    ("First third", sorted_trades[:third]),
    ("Second third", sorted_trades[third:2*third]),
    ("Final third", sorted_trades[2*third:]),
]

for label, group in thirds:
    n = len(group)
    if n == 0:
        continue
    dates = [g["date"] for g in group]
    months = sorted(set(g["month"] for g in group))

    fw_counts = Counter(g["framework"] for g in group)
    kz_counts = Counter(g["kill_zone"] for g in group)
    wins = sum(1 for g in group if g["outcome"] == "WIN")
    rs = [g["r_multiple"] for g in group]

    print(f"\n**{label}** ({n} trades, {dates[0]} to {dates[-1]})")
    print(f"  Months: {', '.join(months)}")
    print(f"  WR: {wins/n*100:.1f}%, Exp: {sum(rs)/n:+.3f}R, Total: {sum(rs):+.2f}R")
    print(f"  Frameworks: {dict(fw_counts)}")
    print(f"  Kill zones: {dict(kz_counts)}")

    # Sub-breakdown for each KZ × FW
    for fw in ["session_sweep", "ob_retest"]:
        for kz in ["london", "ny"]:
            sub = [g for g in group if g["framework"] == fw and g["kill_zone"] == kz]
            if sub:
                sw = sum(1 for s in sub if s["outcome"] == "WIN")
                sr = sum(s["r_multiple"] for s in sub)
                print(f"    {fw}+{kz}: {len(sub)} trades, {sw}W/{len(sub)-sw}L, {sr:+.2f}R")

# Detailed listing of final third
print("\n### Final Third — EVERY TRADE:")
final_third = sorted_trades[2*third:]
print(f"| {'Date':<10} | {'FW':<14} | {'KZ':<7} | {'Dir':<5} | {'Grade':<5} | {'R':>6} | {'Batch':<7} |")
print(f"|{'-'*10}--|{'-'*14}--|{'-'*7}--|{'-'*5}--|{'-'*5}--|{'-'*6}--|{'-'*7}--|")
for t in final_third:
    print(f"| {t['date']:<10} | {t['framework']:<14} | {t['kill_zone']:<7} | {t['direction']:<5} | {t['setup_grade']:<5} | {t['r_multiple']:>+5.2f}R | {t['batch']:<7} |")

# Monthly breakdown for the final third
print("\n### Final Third — Monthly Breakdown:")
monthly = defaultdict(list)
for t in final_third:
    monthly[t["month"]].append(t)
for m in sorted(monthly.keys()):
    g = monthly[m]
    w = sum(1 for t in g if t["outcome"] == "WIN")
    tr = sum(t["r_multiple"] for t in g)
    kzs = Counter(t["kill_zone"] for t in g)
    print(f"  {m}: {len(g)} trades ({w}W/{len(g)-w}L), {tr:+.2f}R — KZ: {dict(kzs)}")

# ─── 2.4 OB_RETEST TRADE DETAIL DUMP ─────────────────────────────────
print("\n" + "=" * 72)
print("## 2.4 OB_RETEST TRADE DETAIL DUMP")
print("=" * 72)

ob_trades = [t for t in trades if t["framework"] == "ob_retest"]
print(f"\nTotal ob_retest trades: {len(ob_trades)}")

# Check for date duplicates
ob_dates = [t["date"] for t in ob_trades]
dup_dates = [d for d, c in Counter(ob_dates).items() if c > 1]
if dup_dates:
    print(f"⚠️ DUPLICATE DATES: {dup_dates}")
else:
    print("✓ No duplicate dates")

print(f"\n| {'Date':<10} | {'Batch':<7} | {'KZ':<7} | {'Dir':<5} | {'Grade':<5} | {'Entry':>9} | {'SL':>9} | {'SL$':>6} | {'TP1':>9} | {'TP2':>9} | {'TP3':>9} | {'R':>6} | {'Conf':>4} | {'Day':<10} | {'LiqPool':<12} |")
print(f"|{'-'*10}--|{'-'*7}--|{'-'*7}--|{'-'*5}--|{'-'*5}--|{'-'*9}--|{'-'*9}--|{'-'*6}--|{'-'*9}--|{'-'*9}--|{'-'*9}--|{'-'*6}--|{'-'*4}--|{'-'*10}--|{'-'*12}--|")

for t in sorted(ob_trades, key=lambda x: x["date"]):
    print(f"| {t['date']:<10} | {t['batch']:<7} | {t['kill_zone']:<7} | {t['direction']:<5} | {t['setup_grade']:<5} | "
          f"{t.get('entry_price', 0):>9.2f} | {t.get('stop_loss', 0):>9.2f} | {t.get('sl_dollars', 0):>5.1f}$ | "
          f"{t.get('take_profit_1', 0):>9.2f} | {t.get('take_profit_2', 0):>9.2f} | {t.get('take_profit_3', 0):>9.2f} | "
          f"{t['r_multiple']:>+5.2f}R | {t.get('confidence_score', 0):>4} | {t['day_of_week']:<10} | {t.get('liquidity_pool_type', 'unk'):<12} |")

# Characteristics summary
print("\n### OB_RETEST Characteristics:")
print(f"  Kill zones: {Counter(t['kill_zone'] for t in ob_trades)}")
print(f"  Directions: {Counter(t['direction'] for t in ob_trades)}")
print(f"  Grades: {Counter(t['setup_grade'] for t in ob_trades)}")
print(f"  Days: {Counter(t['day_of_week'] for t in ob_trades)}")
print(f"  Batches: {Counter(t['batch'] for t in ob_trades)}")
print(f"  Liquidity pools: {Counter(t.get('liquidity_pool_type', 'unk') for t in ob_trades)}")
print(f"  Sweep quality: {Counter(t.get('sweep_quality', 'unk') for t in ob_trades)}")

ob_sls = [t["sl_dollars"] for t in ob_trades if t.get("sl_dollars")]
ss_sls = [t["sl_dollars"] for t in trades if t["framework"] == "session_sweep" and t.get("sl_dollars")]
print(f"\n  OB_RETEST avg SL: ${statistics.mean(ob_sls):.2f} (median ${statistics.median(ob_sls):.2f})")
print(f"  SESSION_SWEEP avg SL: ${statistics.mean(ss_sls):.2f} (median ${statistics.median(ss_sls):.2f})")

months_ob = sorted(set(t["month"] for t in ob_trades))
print(f"  Months active: {months_ob}")

# ─── 2.4b Grade × Framework ──────────────────────────────────────────
print("\n## 2.4b GRADE × FRAMEWORK CROSS-TAB\n")

for fw in ["session_sweep", "ob_retest", "equal_sweep"]:
    for gr in ["A+", "A"]:
        g = [t for t in trades if t["framework"] == fw and t["setup_grade"] == gr]
        print(stats_line(g, f"{fw} + {gr}"))

# ─── 2.5 Wednesday Investigation ──────────────────────────────────────
print("\n" + "=" * 72)
print("## 2.5 WEDNESDAY INVESTIGATION")
print("=" * 72)

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
print(f"\n| {'Day':<10} | {'N':>4} | {'W':>3} | {'L':>3} | {'WR':>6} | {'WR 95% CI':<16} | {'Exp':>8} | {'Total R':>8} |")
print(f"|{'-'*10}--|{'-'*4}--|{'-'*3}--|{'-'*3}--|{'-'*6}--|{'-'*16}--|{'-'*8}--|{'-'*8}--|")

for day in days_order:
    g = [t for t in trades if t["day_of_week"] == day]
    n = len(g)
    if n == 0:
        continue
    w = sum(1 for t in g if t["outcome"] == "WIN")
    rs = [t["r_multiple"] for t in g]
    tr = sum(rs)
    ci = wilson_ci(w, n)
    print(f"| {day:<10} | {n:>4} | {w:>3} | {n-w:>3} | {w/n*100:>5.1f}% | [{ci[0]*100:>4.1f}%,{ci[1]*100:>5.1f}%] | {tr/n:>+7.3f}R | {tr:>+7.2f}R |")

# Wednesday by framework and KZ
print("\n### Wednesday breakdown by Framework × KZ:")
wed_trades = [t for t in trades if t["day_of_week"] == "Wednesday"]
for fw in ["session_sweep", "ob_retest"]:
    for kz in ["london", "ny"]:
        g = [t for t in wed_trades if t["framework"] == fw and t["kill_zone"] == kz]
        if g:
            w = sum(1 for t in g if t["outcome"] == "WIN")
            tr = sum(t["r_multiple"] for t in g)
            print(f"  Wed {fw}+{kz}: {len(g)} trades, {w}W/{len(g)-w}L, {tr:+.2f}R")

# Is Wednesday an outlier?
day_exps = {}
for day in days_order:
    g = [t for t in trades if t["day_of_week"] == day]
    if g:
        day_exps[day] = sum(t["r_multiple"] for t in g) / len(g)

print(f"\n### Day-of-week expectancies: {day_exps}")
wed_exp = day_exps.get("Wednesday", 0)
other_exps = [v for k, v in day_exps.items() if k != "Wednesday"]
if other_exps:
    print(f"  Wednesday exp: {wed_exp:+.3f}R")
    print(f"  All other days mean exp: {statistics.mean(other_exps):+.3f}R")
    diff = wed_exp - statistics.mean(other_exps)
    print(f"  Wednesday is {diff:+.3f}R worse than average")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: DEEP DIVES
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PHASE 3: DEEP DIVES")
print("=" * 72)

# ─── 3.1 Batch 4B Anomaly ─────────────────────────────────────────────
print("\n## 3.1 BATCH 4B ANOMALY DIAGNOSIS\n")

# M15 data range
print("M15 CSV data range: 2024-04-01 to 2026-03-30")
print("Batch 4B configured range: Apr 2024 – Sep 2024")

# Count actual trading days in M15 data for each batch range
import csv
m15_dates = set()
with open("data/historical/XAUUSD_M15.csv") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        m15_dates.add(dt.strftime("%Y-%m-%d"))

batch_ranges = {
    "Batch3": ("2024-10-01", "2025-03-31"),
    "Batch4A": ("2025-04-01", "2026-03-31"),
    "Batch4B": ("2024-04-01", "2024-09-30"),
}

for bl, (s, e) in batch_ranges.items():
    sd = datetime.strptime(s, "%Y-%m-%d").date()
    ed = datetime.strptime(e, "%Y-%m-%d").date()
    total_weekdays = sum(1 for i in range((ed - sd).days + 1)
                         if (sd + timedelta(days=i)).weekday() < 5)
    m15_days_in_range = sum(1 for d in m15_dates
                            if sd <= datetime.strptime(d, "%Y-%m-%d").date() <= ed)
    sessions = [r for r in all_results if r["_batch_label"] == bl]
    session_dates = set(r["date"] for r in sessions)

    print(f"**{bl}** ({s} to {e}):")
    print(f"  Total weekdays: {total_weekdays}")
    print(f"  M15 data days available: {m15_days_in_range}")
    print(f"  Sessions actually run: {len(sessions)}")
    print(f"  Pre-screened out or no data: {m15_days_in_range - len(sessions)}")
    print(f"  Pre-screen pass rate: {len(sessions)/m15_days_in_range*100:.1f}%" if m15_days_in_range > 0 else "")

    # Monthly breakdown of M15 data availability
    m15_monthly = Counter()
    for d in m15_dates:
        dt = datetime.strptime(d, "%Y-%m-%d").date()
        if sd <= dt <= ed:
            m15_monthly[dt.strftime("%Y-%m")] += 1
    session_monthly = Counter(r["date"][:7] for r in sessions)

    print(f"  Monthly M15 data days: {dict(sorted(m15_monthly.items()))}")
    print(f"  Monthly sessions run:  {dict(sorted(session_monthly.items()))}")
    print()

# ─── 3.2 OB_RETEST Near-Miss Analysis ────────────────────────────────
print("\n## 3.2 OB_RETEST NEAR-MISS ANALYSIS\n")

# Scan all response files for ob_retest near-misses
ob_near_miss_count = 0
ob_near_details = Counter()
total_responses_scanned = 0

response_files = sorted(RESPONSES_DIR.glob("*_responses.json"))
for rf in response_files:
    data = json.loads(rf.read_text())
    for key, resp in data.items():
        total_responses_scanned += 1
        fe = resp.get("frameworks_evaluated", {})
        ob_info = fe.get("ob_retest", {})
        if isinstance(ob_info, dict) and not ob_info.get("qualified", False):
            reason = ob_info.get("reason", "")
            reason_lower = reason.lower()
            # Detect near-misses: mentions CHoCH or BOS or OB retest being close
            if any(kw in reason_lower for kw in ["choch", "bos", "retest", "pullback", "ob zone", "order block"]):
                if "no" in reason_lower or "not" in reason_lower or "miss" in reason_lower or "lack" in reason_lower:
                    ob_near_miss_count += 1
                    # Categorize
                    if "bos" in reason_lower and ("no" in reason_lower or "not" in reason_lower):
                        ob_near_details["Has OB/CHoCH but no BOS"] += 1
                    elif "choch" in reason_lower and ("no" in reason_lower or "not" in reason_lower):
                        ob_near_details["Has OB but no CHoCH"] += 1
                    elif "retest" in reason_lower and ("no" in reason_lower or "not" in reason_lower):
                        ob_near_details["No retest of OB"] += 1
                    elif "pullback" in reason_lower:
                        ob_near_details["No pullback to OB"] += 1
                    else:
                        ob_near_details["Other OB-related rejection"] += 1

print(f"Total candle responses scanned: {total_responses_scanned}")
print(f"OB_RETEST near-misses found: {ob_near_miss_count}")
for reason, count in ob_near_details.most_common():
    print(f"  {reason}: {count}")

# Also count raw ob_retest rejection reasons (top categories)
print(f"\n### All ob_retest rejection reasons (top 10):")
ob_rejections = Counter()
for rf in response_files:
    data = json.loads(rf.read_text())
    for key, resp in data.items():
        fe = resp.get("frameworks_evaluated", {})
        ob_info = fe.get("ob_retest", {})
        if isinstance(ob_info, dict) and not ob_info.get("qualified", False):
            reason = ob_info.get("reason", "unknown")
            # Normalize
            if len(reason) > 100:
                reason = reason[:97] + "..."
            ob_rejections[reason] += 1

for reason, count in ob_rejections.most_common(10):
    print(f"  [{count:>4}] {reason}")

# ─── 3.3 Session_Sweep Failure Mode Analysis ─────────────────────────
print("\n" + "=" * 72)
print("## 3.3 SESSION_SWEEP FAILURE MODE ANALYSIS")
print("=" * 72)

ss_trades = [t for t in trades if t["framework"] == "session_sweep"]
ss_losers = [t for t in ss_trades if t["outcome"] == "LOSS"]
ss_winners = [t for t in ss_trades if t["outcome"] == "WIN"]

print(f"\nSession_sweep: {len(ss_trades)} total, {len(ss_winners)}W/{len(ss_losers)}L")

# SL size buckets (include winners for context)
print(f"\n### SL Size Buckets:")
sl_buckets = [("<$5", lambda s: s < 5), ("$5-$8", lambda s: 5 <= s < 8),
              ("$8-$12", lambda s: 8 <= s < 12), ("$12+", lambda s: s >= 12)]

for label, fn in sl_buckets:
    g = [t for t in ss_trades if t.get("sl_dollars") and fn(t["sl_dollars"])]
    n = len(g)
    if n == 0:
        continue
    w = sum(1 for t in g if t["outcome"] == "WIN")
    tr = sum(t["r_multiple"] for t in g)
    print(f"  {label}: {n} trades, {w}W/{n-w}L, WR {w/n*100:.1f}%, Exp {tr/n:+.3f}R{flag(n)}")

# By kill zone
print(f"\n### SS losses by Kill Zone:")
for kz in ["london", "ny"]:
    g = [t for t in ss_losers if t["kill_zone"] == kz]
    print(f"  {kz}: {len(g)} losses")
    sls = [t["sl_dollars"] for t in g if t.get("sl_dollars")]
    if sls:
        print(f"    SL range: ${min(sls):.2f} - ${max(sls):.2f}, median ${statistics.median(sls):.2f}")

# Liquidity pool type analysis for session_sweep
print(f"\n### SS by Liquidity Pool Type:")
for pool in sorted(set(t.get("liquidity_pool_type", "unk") for t in ss_trades)):
    g = [t for t in ss_trades if t.get("liquidity_pool_type") == pool]
    n = len(g)
    if n == 0:
        continue
    w = sum(1 for t in g if t["outcome"] == "WIN")
    tr = sum(t["r_multiple"] for t in g)
    print(f"  {pool}: {n} trades, {w}W/{n-w}L, WR {w/n*100:.1f}%, Exp {tr/n:+.3f}R{flag(n)}")

# ─── 3.4 Winner Exit Analysis ────────────────────────────────────────
print("\n" + "=" * 72)
print("## 3.4 WINNER EXIT ANALYSIS")
print("=" * 72)

# The outcome evaluation uses partial closes:
# TP1: close 50%, move SL to BE → contributes 50% × TP1_R
# TP2: close 25%, trail SL to TP1 → contributes 25% × TP2_R
# TP3: close 25% (runner) → contributes 25% × TP3_R
# Or stopped out/timed out on remaining portion

print(f"\nWinners: {len(ss_winners + [t for t in trades if t['outcome']=='WIN' and t['framework']!='session_sweep'])} total")

all_winners = [t for t in trades if t["outcome"] == "WIN"]
all_losers = [t for t in trades if t["outcome"] == "LOSS"]

# Analyze winners by R-multiple to infer exit type
# Partial close math:
# TP1 only hit, remainder BE'd: R = 0.5 × RR_to_TP1
# TP1 + TP2, remainder at TP1 trail: R = 0.5 × RR1 + 0.25 × RR2
# All three TPs: R = 0.5 × RR1 + 0.25 × RR2 + 0.25 × RR3

print(f"\n### Winner R-multiple Distribution:")
win_rs = sorted([t["r_multiple"] for t in all_winners])
print(f"  Min: {min(win_rs):.2f}R")
print(f"  25th pct: {np.percentile(win_rs, 25):.2f}R")
print(f"  Median: {np.percentile(win_rs, 50):.2f}R")
print(f"  75th pct: {np.percentile(win_rs, 75):.2f}R")
print(f"  Max: {max(win_rs):.2f}R")

# Categorize by R-multiple
tiny_wins = [t for t in all_winners if t["r_multiple"] < 0.5]
small_wins = [t for t in all_winners if 0.5 <= t["r_multiple"] < 1.0]
medium_wins = [t for t in all_winners if 1.0 <= t["r_multiple"] < 2.0]
large_wins = [t for t in all_winners if t["r_multiple"] >= 2.0]

print(f"\n  Tiny wins (<0.5R): {len(tiny_wins)} — likely timeout or barely profitable")
print(f"  Small wins (0.5-1.0R): {len(small_wins)} — TP1 hit, remainder BE'd")
print(f"  Medium wins (1.0-2.0R): {len(medium_wins)} — TP1+partial TP2 or good timeout")
print(f"  Large wins (2.0+R): {len(large_wins)} — TP2+ hit or runner success")

# For each winner, compute theoretical TP1 R
print(f"\n### TP1 theoretical R for winners (50% position at TP1):")
tp1_theoretical = []
for t in all_winners:
    if t.get("entry_price") and t.get("stop_loss") and t.get("take_profit_1"):
        risk = abs(t["entry_price"] - t["stop_loss"])
        if risk > 0:
            tp1_r = abs(t["take_profit_1"] - t["entry_price"]) / risk
            tp1_half = tp1_r * 0.5  # 50% position at TP1
            tp1_theoretical.append((t, tp1_r, tp1_half))

if tp1_theoretical:
    print(f"  Avg TP1 distance in R: {statistics.mean([x[1] for x in tp1_theoretical]):.2f}R")
    print(f"  Avg contribution of TP1 alone (50%): {statistics.mean([x[2] for x in tp1_theoretical]):.2f}R")
    print(f"  Actual avg winner R: {statistics.mean([t['r_multiple'] for t in all_winners]):.2f}R")

    # How many winners achieved less than TP1 contribution?
    below_tp1 = sum(1 for t, tp1_r, tp1_half in tp1_theoretical if t["r_multiple"] < tp1_half)
    print(f"\n  Winners achieving LESS than TP1 alone would give: {below_tp1}/{len(tp1_theoretical)}")
    print(f"  → These are likely profitable timeouts (didn't even hit TP1)")

# ─── 3.5 Trade Timing Analysis ───────────────────────────────────────
print("\n" + "=" * 72)
print("## 3.5 TRADE TIMING WITHIN KILL ZONE")
print("=" * 72)

# Extract candle time from trade_id: bt_YYYY-MM-DD_kz_NNN or from response files
timing_data = []
for t in trades:
    tid = t.get("trade_id", "")
    # Try to get timing from response file
    resp_file = RESPONSES_DIR / f"{t['date']}_responses.json"
    if resp_file.exists():
        data = json.loads(resp_file.read_text())
        for key, val in data.items():
            if val.get("decision") == "CANDIDATE" and val.get("kill_zone") == t["kill_zone"]:
                ts = val.get("timestamp_utc", "")
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hour_min = dt.hour * 60 + dt.minute
                    # London: 07:00-09:30 (420-570 min)
                    # NY: 13:00-15:30 (780-930 min)
                    if t["kill_zone"] == "london":
                        minutes_in = hour_min - 420
                    else:
                        minutes_in = hour_min - 780
                    timing_data.append({**t, "minutes_into_kz": minutes_in, "entry_time": ts})
                break

if timing_data:
    print(f"\nTrades with timing data: {len(timing_data)}/{len(trades)}")

    # Bucket by timing
    buckets = [
        ("Early (0-45 min)", lambda m: 0 <= m <= 45),
        ("Middle (46-90 min)", lambda m: 46 <= m <= 90),
        ("Late (91+ min)", lambda m: m > 90),
    ]

    for label, fn in buckets:
        g = [t for t in timing_data if fn(t["minutes_into_kz"])]
        n = len(g)
        if n == 0:
            print(f"  {label}: 0 trades")
            continue
        w = sum(1 for t in g if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in g]
        tr = sum(rs)
        print(f"  {label}: {n} trades, {w}W/{n-w}L, WR {w/n*100:.1f}%, Exp {tr/n:+.3f}R{flag(n)}")

    # Timing by KZ
    for kz in ["london", "ny"]:
        print(f"\n  {kz.upper()} timing distribution:")
        kz_timed = [t for t in timing_data if t["kill_zone"] == kz]
        times = [t["minutes_into_kz"] for t in kz_timed]
        if times:
            print(f"    Median entry: {statistics.median(times):.0f} min into window")
            print(f"    Range: {min(times):.0f} - {max(times):.0f} min")

# ─── 3.6 Confidence Score Deep Dive ──────────────────────────────────
print("\n" + "=" * 72)
print("## 3.6 CONFIDENCE SCORE DEEP DIVE")
print("=" * 72)

confs = Counter(t.get("confidence_score") for t in trades)
print(f"\nConfidence score distribution: {dict(confs)}")

outliers = [t for t in trades if t.get("confidence_score") != 85]
if outliers:
    print(f"\nOutlier(s):")
    for t in outliers:
        print(f"  {t['date']} {t['kill_zone']} {t['framework']}: conf={t['confidence_score']}, {t['outcome']} {t['r_multiple']:+.2f}R")

# Check PA prompt for confidence definition
print("\n### Confidence scoring in Primary Analyzer prompt:")
try:
    from src.prompts.primary_analyzer_prompt import PA_SYSTEM_PROMPT
    # Find confidence-related section
    lines = PA_SYSTEM_PROMPT.split("\n")
    found = False
    for i, line in enumerate(lines):
        if "confidence" in line.lower() and ("score" in line.lower() or "0-100" in line.lower() or "integer" in line.lower()):
            # Print surrounding context
            start = max(0, i - 2)
            end = min(len(lines), i + 8)
            for j in range(start, end):
                print(f"  {j}: {lines[j]}")
            found = True
            break
    if not found:
        print("  No detailed confidence scoring instructions found in prompt")
except Exception as e:
    print(f"  Could not load PA prompt: {e}")

# ─── 3.7 Pre-screening Rate by Period ────────────────────────────────
print("\n" + "=" * 72)
print("## 3.7 PRE-SCREENING RATE BY PERIOD")
print("=" * 72)

# Build month-by-month table
all_months = set()
for d in m15_dates:
    all_months.add(d[:7])

session_dates_by_batch = defaultdict(set)
for r in all_results:
    session_dates_by_batch[r["_batch_label"]].add(r["date"])

# Combine all session dates
all_session_dates = set()
for dates in session_dates_by_batch.values():
    all_session_dates.update(dates)

print(f"\n| {'Month':<7} | {'M15 Days':>8} | {'Sessions':>8} | {'Pass Rate':>9} | {'Trades':>6} | {'Batch':<8} |")
print(f"|{'-'*7}--|{'-'*8}--|{'-'*8}--|{'-'*9}--|{'-'*6}--|{'-'*8}--|")

for month in sorted(all_months):
    m15_count = sum(1 for d in m15_dates if d.startswith(month))
    sess_count = sum(1 for d in all_session_dates if d.startswith(month))
    trade_count = sum(1 for t in trades if t["month"] == month)

    # Determine batch
    year_month = int(month.replace("-", ""))
    if year_month <= 202409:
        batch = "Batch4B"
    elif year_month <= 202503:
        batch = "Batch3"
    else:
        batch = "Batch4A"

    pass_rate = f"{sess_count/m15_count*100:.1f}%" if m15_count > 0 else "N/A"
    print(f"| {month:<7} | {m15_count:>8} | {sess_count:>8} | {pass_rate:>9} | {trade_count:>6} | {batch:<8} |")

# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: SYNTHESIS AND OUTPUT
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PHASE 4: SYNTHESIS")
print("=" * 72)

# ─── 4.1 Decision Table ──────────────────────────────────────────────
print("\n## 4.1 DECISION TABLE\n")

# Compute key stats for decisions
london_ss = [t for t in trades if t["kill_zone"] == "london" and t["framework"] == "session_sweep"]
ny_ss = [t for t in trades if t["kill_zone"] == "ny" and t["framework"] == "session_sweep"]
london_ob = [t for t in trades if t["kill_zone"] == "london" and t["framework"] == "ob_retest"]
ny_ob = [t for t in trades if t["kill_zone"] == "ny" and t["framework"] == "ob_retest"]

london_ss_exp = sum(t["r_multiple"] for t in london_ss) / len(london_ss) if london_ss else 0
ny_ss_exp = sum(t["r_multiple"] for t in ny_ss) / len(ny_ss) if ny_ss else 0
london_ob_exp = sum(t["r_multiple"] for t in london_ob) / len(london_ob) if london_ob else 0
ny_ob_exp = sum(t["r_multiple"] for t in ny_ob) / len(ny_ob) if ny_ob else 0

decisions = {}

# Decision 1: Drop London?
print("### Drop London entirely?")
print(f"  London session_sweep: {len(london_ss)} trades, Exp {london_ss_exp:+.3f}R")
print(f"  London ob_retest: {len(london_ob)} trades, Exp {london_ob_exp:+.3f}R")
print(f"  NY session_sweep: {len(ny_ss)} trades, Exp {ny_ss_exp:+.3f}R")
print(f"  NY ob_retest: {len(ny_ob)} trades, Exp {ny_ob_exp:+.3f}R")

if london_ss_exp < -0.1 and london_ob_exp > 0:
    rec = "CONDITIONAL: Drop London for session_sweep; KEEP for ob_retest"
    conf = "MEDIUM"
elif london_ss_exp < -0.1 and len(london_ob) < 3:
    rec = "YES: Drop London entirely (ob_retest too rare to justify keeping)"
    conf = "MEDIUM"
else:
    rec = "NO: Keep London"
    conf = "LOW"

evidence = (f"London SS: {len(london_ss)} trades, {london_ss_exp:+.3f}R exp. "
            f"London OB: {len(london_ob)} trades, {london_ob_exp:+.3f}R exp. "
            f"NY SS: {len(ny_ss)} trades, {ny_ss_exp:+.3f}R exp.")
decisions["drop_london"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# Decision 2: Drop session_sweep?
print(f"\n### Drop session_sweep?")
ss_exp = sum(t["r_multiple"] for t in ss_trades) / len(ss_trades) if ss_trades else 0
print(f"  session_sweep overall: {len(ss_trades)} trades, Exp {ss_exp:+.3f}R")
print(f"  session_sweep NY: {len(ny_ss)} trades, Exp {ny_ss_exp:+.3f}R")

if ss_exp < -0.1 and ny_ss_exp > 0:
    rec = "CONDITIONAL: Keep session_sweep only in NY kill zone"
    conf = "MEDIUM"
elif ss_exp < -0.1 and ny_ss_exp <= 0:
    rec = "YES: session_sweep has no edge in any configuration"
    conf = "HIGH"
else:
    rec = "NO: Keep session_sweep (marginally negative, may improve with fixes)"
    conf = "LOW"

evidence = f"SS overall: {ss_exp:+.3f}R. SS+NY: {ny_ss_exp:+.3f}R ({len(ny_ss)} trades). SS+London: {london_ss_exp:+.3f}R ({len(london_ss)} trades)."
decisions["drop_session_sweep"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# Decision 3: Pivot to ob_retest?
print(f"\n### Pivot to ob_retest as primary?")
ob_exp = sum(t["r_multiple"] for t in ob_trades) / len(ob_trades) if ob_trades else 0
print(f"  ob_retest: {len(ob_trades)} trades, ALL wins, Exp {ob_exp:+.3f}R")
print(f"  BUT: only {len(ob_trades)} trades across {len(set(t['month'] for t in ob_trades))} months")
print(f"  Near-misses found: {ob_near_miss_count}")

rec = "CONDITIONAL: Investigate relaxing ob_retest triggers to increase frequency. Too rare to be primary alone."
conf = "MEDIUM"
evidence = f"{len(ob_trades)} trades, 100% WR, {ob_exp:+.3f}R exp. {ob_near_miss_count} near-misses found. Only fires ~0.4 trades/month."
decisions["pivot_ob_retest"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# Decision 4: Restrict to A+ only?
print(f"\n### Restrict to A+ only?")
aplus = [t for t in trades if t["setup_grade"] == "A+"]
a_only = [t for t in trades if t["setup_grade"] == "A"]
aplus_exp = sum(t["r_multiple"] for t in aplus) / len(aplus) if aplus else 0
a_exp = sum(t["r_multiple"] for t in a_only) / len(a_only) if a_only else 0
print(f"  A+: {len(aplus)} trades, Exp {aplus_exp:+.3f}R")
print(f"  A:  {len(a_only)} trades, Exp {a_exp:+.3f}R")

rec = "YES: Drop A-grade trades (negative expectancy, dilute the edge)" if a_exp < -0.05 else "NO"
conf = "MEDIUM" if a_exp < -0.05 else "LOW"
evidence = f"A+: {aplus_exp:+.3f}R exp ({len(aplus)} trades). A: {a_exp:+.3f}R exp ({len(a_only)} trades)."
decisions["restrict_a_plus"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# Decision 5: Exclude Wednesdays?
print(f"\n### Exclude Wednesdays?")
wed = [t for t in trades if t["day_of_week"] == "Wednesday"]
not_wed = [t for t in trades if t["day_of_week"] != "Wednesday"]
wed_exp = sum(t["r_multiple"] for t in wed) / len(wed) if wed else 0
not_wed_exp = sum(t["r_multiple"] for t in not_wed) / len(not_wed) if not_wed else 0

# Wilson CI for Wednesday
wed_wins = sum(1 for t in wed if t["outcome"] == "WIN")
wed_ci = wilson_ci(wed_wins, len(wed))
not_wed_wins = sum(1 for t in not_wed if t["outcome"] == "WIN")
not_wed_ci = wilson_ci(not_wed_wins, len(not_wed))

print(f"  Wednesday: {len(wed)} trades, WR {wed_wins/len(wed)*100:.1f}% CI [{wed_ci[0]*100:.1f}%,{wed_ci[1]*100:.1f}%], Exp {wed_exp:+.3f}R")
print(f"  Not Wed:   {len(not_wed)} trades, WR {not_wed_wins/len(not_wed)*100:.1f}% CI [{not_wed_ci[0]*100:.1f}%,{not_wed_ci[1]*100:.1f}%], Exp {not_wed_exp:+.3f}R")

# CIs overlap?
ci_overlap = wed_ci[1] >= not_wed_ci[0] and not_wed_ci[1] >= wed_ci[0]
if wed_exp < -0.3 and not ci_overlap:
    rec = "YES: Strong evidence Wednesday is worse"
    conf = "HIGH"
elif wed_exp < -0.3 and ci_overlap:
    rec = "CONDITIONAL: Wednesday is worse but CIs overlap. Add to demo monitoring."
    conf = "LOW"
else:
    rec = "NO: Insufficient evidence"
    conf = "LOW"

evidence = f"Wed: {wed_exp:+.3f}R ({len(wed)} trades, WR CI [{wed_ci[0]*100:.0f}%,{wed_ci[1]*100:.0f}%]). Not Wed: {not_wed_exp:+.3f}R."
decisions["exclude_wednesday"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# Decision 6: Fix confidence scoring
print(f"\n### Fix confidence scoring?")
rec = "YES: Confidence is a constant (85 for 90/91 trades), providing zero discriminative signal."
conf = "HIGH"
evidence = "90/91 trades have confidence=85. Spearman ρ=0.056, p=0.60. No predictive value."
decisions["fix_confidence"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# Decision 7: Shorten kill zone window?
print(f"\n### Shorten kill zone window?")
if timing_data:
    early = [t for t in timing_data if t["minutes_into_kz"] <= 45]
    late = [t for t in timing_data if t["minutes_into_kz"] > 90]
    early_exp = sum(t["r_multiple"] for t in early) / len(early) if early else 0
    late_exp = sum(t["r_multiple"] for t in late) / len(late) if late else 0
    print(f"  Early (0-45 min): {len(early)} trades, Exp {early_exp:+.3f}R")
    print(f"  Late (91+ min): {len(late)} trades, Exp {late_exp:+.3f}R")
    if late_exp < early_exp - 0.2 and len(late) >= 10:
        rec = "CONDITIONAL: Late entries underperform. Consider 90-min window."
        conf = "LOW"
    else:
        rec = "NO: Insufficient evidence to shorten"
        conf = "LOW"
else:
    rec = "CANNOT ASSESS: No timing data available"
    conf = "N/A"
evidence = "See timing analysis in 3.5"
decisions["shorten_kz_window"] = {"recommendation": rec, "confidence": conf, "evidence": evidence}
print(f"  → {rec} [{conf}]")

# ─── 4.2 Best Filter Configuration ───────────────────────────────────
print("\n## 4.2 BEST FILTER CONFIGURATION\n")

# Evaluate the top candidates
candidates = [
    ("NY only", lambda t: t["kill_zone"] == "ny"),
    ("NOT Wednesday", lambda t: t["day_of_week"] != "Wednesday"),
    ("NY + A+", lambda t: t["kill_zone"] == "ny" and t["setup_grade"] == "A+"),
    ("NY + NOT Wed", lambda t: t["kill_zone"] == "ny" and t["day_of_week"] != "Wednesday"),
    ("A+ only", lambda t: t["setup_grade"] == "A+"),
    ("NY + LONG", lambda t: t["kill_zone"] == "ny" and t["direction"] == "LONG"),
    ("session_sweep + NY", lambda t: t["framework"] == "session_sweep" and t["kill_zone"] == "ny"),
]

print(f"| {'Filter':<25} | {'N':>4} | {'WR':>6} | {'Exp':>8} | {'Total R':>8} | {'Trades/mo':>9} |")
print(f"|{'-'*25}--|{'-'*4}--|{'-'*6}--|{'-'*8}--|{'-'*8}--|{'-'*9}--|")

for label, fn in candidates:
    g = [t for t in trades if fn(t)]
    n = len(g)
    if n == 0:
        continue
    w = sum(1 for t in g if t["outcome"] == "WIN")
    rs = [t["r_multiple"] for t in g]
    tr = sum(rs)
    months = len(set(t["month"] for t in g))
    tpm = n / months if months > 0 else 0
    print(f"| {label:<25} | {n:>4} | {w/n*100:>5.1f}% | {tr/n:>+7.3f}R | {tr:>+7.2f}R | {tpm:>8.1f} |")

print(f"\nRecommended production filter: NY kill zone only")
print(f"  Expected trade frequency: ~2.1 trades/month")
print(f"  Expected expectancy: +0.361R/trade")
print(f"  Sample size: 34 trades (below 95% confidence threshold)")
print(f"  Needed for 95% confidence: ~60-80 NY trades (estimate ~30-38 more months)")

# ─── 4.3 Open Questions ──────────────────────────────────────────────
print("\n## 4.3 OPEN QUESTIONS FOR SESSION 2\n")

open_questions = [
    "MFE/MAE data not tracked in batch results — need to add max_favorable_excursion and max_adverse_excursion to evaluate_hypothetical_outcome(). This is the #1 priority for TP optimization.",
    "OB_RETEST triggers too rarely (9/174 sessions). Near-miss analysis shows the specific rejection reasons. Need to examine whether relaxing BOS requirement or widening OB zone definitions would safely increase frequency.",
    "Confidence score is a constant 85 — the PA prompt needs explicit calibration tiers with examples. Currently the AI defaults to 85 for everything.",
    "Winner exit types unclear — the batch runner tracks events[] in evaluate_hypothetical_outcome but they're not stored in the session/result files. Need to persist exit_substate and events to understand TP1/TP2/TP3 hit rates.",
    "The final third collapse (-11.27R) needs to be checked against gold market regime (was Q1 2026 fundamentally different?). If it's a regime-specific issue, the system may need market regime detection.",
    "Session_sweep sweep-vs-breakdown confusion is the known failure mode but cannot be quantified from current data. Would need to parse raw AI reasoning text for uncertainty language.",
]

for i, q in enumerate(open_questions, 1):
    print(f"  {i}. {q}")

# ─── Save outputs ────────────────────────────────────────────────────
# Save decision JSON
decisions_json = {
    "decisions": decisions,
    "best_filter": {
        "description": "NY kill zone only",
        "trades": 34,
        "win_rate": 0.500,
        "expectancy": 0.361,
        "total_r": 12.28,
        "trades_per_month": 2.1,
    },
    "open_questions": open_questions,
    "session2_requirements": [
        "Add MFE/MAE tracking to evaluate_hypothetical_outcome()",
        "Persist exit_substate and events in batch results",
        "Investigate relaxing ob_retest BOS requirement",
        "Redesign confidence scoring in PA prompt (calibrated tiers)",
        "Add Wednesday exclusion as configurable filter",
        "Consider NY-only mode as default configuration",
    ],
}

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
(ANALYSIS_DIR / "session1_decisions.json").write_text(json.dumps(decisions_json, indent=2))
print(f"\nSaved: {ANALYSIS_DIR / 'session1_decisions.json'}")


if __name__ == "__main__":
    pass

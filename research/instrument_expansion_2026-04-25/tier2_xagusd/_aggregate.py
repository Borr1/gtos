#!/usr/bin/env python3
"""Aggregate 12 XAGUSD F3-style backtest slices into a single synthesis.

Run after all slices complete. Reads each slice's all_results.json and
XAGUSD_t7_simulation.json + parses logs for cost. Emits aggregate.json,
all_results.json, and REPORT.md to research/instrument_expansion_2026-04-25/tier2_xagusd/.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parent
SLICES = [f"s{i}" for i in range(1, 13)]


# ── Statistical helpers ────────────────────────────────────────────────

def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((centre - spread) / denom, (centre + spread) / denom)


def bootstrap_mean_ci(values: list[float], n_iter: int = 5000, alpha: float = 0.05) -> tuple[float, float, float]:
    """Bootstrap CI for the mean of a list of values. Returns (mean, lo, hi)."""
    import random
    if not values:
        return (0.0, 0.0, 0.0)
    m = mean(values)
    means = []
    n = len(values)
    rng = random.Random(42)
    for _ in range(n_iter):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(mean(sample))
    means.sort()
    lo = means[int(n_iter * alpha / 2)]
    hi = means[int(n_iter * (1 - alpha / 2))]
    return (m, lo, hi)


# ── Load all slices ────────────────────────────────────────────────────

slice_data = {}
all_records = []
for s in SLICES:
    slice_dir = ROOT / s
    log_path = ROOT / f"{s}.log"
    combined_path = slice_dir / "all_results.json"
    sym_path = slice_dir / "XAGUSD_t7_simulation.json"

    info = {
        "slice": s,
        "ok": combined_path.exists() or sym_path.exists(),
        "n_records": 0,
        "n_cands": 0,
        "n_filled": 0,
        "cost": 0.0,
        "error": None,
    }

    # Cost from logs (most reliable)
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="ignore")
        # Try to extract from "Total API cost: $X.XX" or last "running cost: $X.XX"
        m = re.search(r"Total API cost:\s*\$([0-9.]+)", log_text)
        if m:
            info["cost"] = float(m.group(1))
        else:
            costs = re.findall(r"running cost:?\s*\$?([0-9.]+)", log_text, re.IGNORECASE)
            if costs:
                info["cost"] = float(costs[-1])

    # Records — prefer combined all_results.json (has total_cost too)
    if combined_path.exists():
        try:
            data = json.loads(combined_path.read_text(encoding="utf-8"))
            recs = data.get("results", [])
            info["n_records"] = len(recs)
            if "total_cost" in data and not info["cost"]:
                info["cost"] = float(data["total_cost"])
            for r in recs:
                r["_slice"] = s
            all_records.extend(recs)
        except Exception as e:
            info["error"] = f"combined parse: {e}"

    elif sym_path.exists():
        try:
            data = json.loads(sym_path.read_text(encoding="utf-8"))
            recs = data.get("results", [])
            info["n_records"] = len(recs)
            for r in recs:
                r["_slice"] = s
            all_records.extend(recs)
        except Exception as e:
            info["error"] = f"sym parse: {e}"

    cands = [r for r in all_records if r.get("_slice") == s and r.get("decision") == "CANDIDATE"]
    info["n_cands"] = len(cands)
    info["n_filled"] = len([c for c in cands if c.get("outcome") in ("WIN", "LOSS")])
    slice_data[s] = info


# ── Filter to actual filled CANDs (those with WIN/LOSS outcome) ────────

cands_all = [r for r in all_records if r.get("decision") == "CANDIDATE"]
cands_filled = [r for r in cands_all if r.get("outcome") in ("WIN", "LOSS")]

# Sort by candle_time for chronological MaxDD
cands_filled.sort(key=lambda r: r.get("candle_time", ""))

n_total_records = len(all_records)
n_cands_total = len(cands_all)
n_filled = len(cands_filled)

if n_filled == 0:
    print("ERROR: 0 filled CANDs — cannot compute fleet metrics. Slice diagnostics below.")
    for s, info in slice_data.items():
        print(f"  {s}: {info}")
    aggregate = {
        "symbol": "XAGUSD",
        "n_slices": len(slice_data),
        "n_total_records": n_total_records,
        "n_cands_total": n_cands_total,
        "n_filled": 0,
        "verdict": "INCONCLUSIVE_NO_FILLS",
        "slices": slice_data,
    }
    (ROOT / "aggregate.json").write_text(json.dumps(aggregate, indent=2))
    raise SystemExit(1)


# ── Fleet metrics ──────────────────────────────────────────────────────

r_multiples = [float(r.get("r_multiple", 0)) for r in cands_filled]
wins = sum(1 for r in r_multiples if r > 0)
wr = wins / n_filled
wr_lo, wr_hi = wilson_ci(wins, n_filled)
exp_r, exp_r_lo, exp_r_hi = bootstrap_mean_ci(r_multiples, n_iter=5000)
total_r = sum(r_multiples)


# MaxDD chronological
peak = 0.0
cumr = 0.0
max_dd = 0.0
running_curve = []
for r in r_multiples:
    cumr += r
    peak = max(peak, cumr)
    dd = peak - cumr
    max_dd = max(max_dd, dd)
    running_curve.append(round(cumr, 3))

# Max consecutive losses
max_consec_loss = 0
cur_loss = 0
for r in r_multiples:
    if r <= 0:
        cur_loss += 1
        max_consec_loss = max(max_consec_loss, cur_loss)
    else:
        cur_loss = 0


# ── Per-direction breakdown ────────────────────────────────────────────

longs = [r for r in cands_filled if r.get("direction") == "LONG"]
shorts = [r for r in cands_filled if r.get("direction") == "SHORT"]
long_r = [float(r.get("r_multiple", 0)) for r in longs]
short_r = [float(r.get("r_multiple", 0)) for r in shorts]
long_wins = sum(1 for r in long_r if r > 0)
short_wins = sum(1 for r in short_r if r > 0)
long_wr_lo, long_wr_hi = wilson_ci(long_wins, len(longs)) if longs else (0, 0)
short_wr_lo, short_wr_hi = wilson_ci(short_wins, len(shorts)) if shorts else (0, 0)
long_exp = sum(long_r) / len(long_r) if long_r else 0.0
short_exp = sum(short_r) / len(short_r) if short_r else 0.0


# ── Per-month decay ────────────────────────────────────────────────────

by_month = defaultdict(list)
for r in cands_filled:
    d = r.get("date", "")
    if d and len(d) >= 7:
        by_month[d[:7]].append(float(r.get("r_multiple", 0)))

monthly = {}
for m in sorted(by_month):
    rs = by_month[m]
    nm = len(rs)
    wins_m = sum(1 for r in rs if r > 0)
    monthly[m] = {
        "n": nm,
        "wins": wins_m,
        "wr": wins_m / nm if nm else 0.0,
        "exp_r": sum(rs) / nm if nm else 0.0,
        "total_r": sum(rs),
    }


# ── Per-KZ + per-slice breakdown ───────────────────────────────────────

by_kz = defaultdict(list)
for r in cands_filled:
    by_kz[r.get("kill_zone", "?")].append(float(r.get("r_multiple", 0)))

kz_summary = {}
for kz, rs in by_kz.items():
    nm = len(rs)
    wins_k = sum(1 for r in rs if r > 0)
    kz_summary[kz] = {
        "n": nm,
        "wr": wins_k / nm if nm else 0.0,
        "exp_r": sum(rs) / nm if nm else 0.0,
        "total_r": sum(rs),
    }

per_slice_metrics = {}
for s in SLICES:
    sf = [r for r in cands_filled if r.get("_slice") == s]
    if not sf:
        per_slice_metrics[s] = {"n_filled": 0, "wr": None, "exp_r": None, "total_r": 0.0}
        continue
    rs = [float(r.get("r_multiple", 0)) for r in sf]
    sw = sum(1 for r in rs if r > 0)
    per_slice_metrics[s] = {
        "n_filled": len(rs),
        "wr": sw / len(rs),
        "exp_r": sum(rs) / len(rs),
        "total_r": sum(rs),
    }


# ── Framework attribution ─────────────────────────────────────────────
# Look at h1_setup_framework / setup_framework field if present.

framework_breakdown = defaultdict(lambda: {"n_filled": 0, "wins": 0, "total_r": 0.0})
for r in cands_filled:
    fw = (r.get("h1_setup_framework")
          or r.get("setup_framework")
          or r.get("reasoning", {}).get("setup_framework", "unknown")
          if isinstance(r.get("reasoning"), dict) else r.get("setup_framework", "unknown"))
    if not fw or fw == "":
        # Try raw_response parse — best effort
        raw = r.get("raw_response", "")
        if isinstance(raw, str):
            m = re.search(r'"setup_framework"\s*:\s*"([^"]+)"', raw)
            if m:
                fw = m.group(1)
            else:
                fw = "unknown"
        else:
            fw = "unknown"
    fb = framework_breakdown[fw]
    fb["n_filled"] += 1
    fb["wins"] += 1 if float(r.get("r_multiple", 0)) > 0 else 0
    fb["total_r"] += float(r.get("r_multiple", 0))

for fw, fb in framework_breakdown.items():
    fb["wr"] = fb["wins"] / fb["n_filled"] if fb["n_filled"] else 0.0
    fb["exp_r"] = fb["total_r"] / fb["n_filled"] if fb["n_filled"] else 0.0


# ── Decision distribution ──────────────────────────────────────────────

decision_counter = Counter(r.get("decision", "?") for r in all_records)
no_trade_reasons = Counter()
for r in all_records:
    if r.get("decision") not in ("CANDIDATE",):
        nr = r.get("no_trade_reason") or r.get("decision")
        # Truncate prescreen reasons
        if isinstance(nr, str) and ":" in nr:
            nr = nr.split(":", 1)[0] + ":" + nr.split(":", 1)[1].split("_")[0]
        no_trade_reasons[nr] += 1


# ── Total cost ─────────────────────────────────────────────────────────

total_cost = sum(info["cost"] for info in slice_data.values())


# ── Pre-registered acceptance criteria ────────────────────────────────

criteria = {
    "wr_gte_55": wr >= 0.55,
    "exp_r_gte_010": exp_r >= 0.10,
    "n_gte_30": n_filled >= 30,
    "max_dd_lte_8r": max_dd <= 8.0,
}
n_passed = sum(1 for v in criteria.values() if v)


# ── Verdict logic ──────────────────────────────────────────────────────

if all(criteria.values()):
    verdict = "PROMOTE-LIVE"
    rationale = "All 4 pre-registered criteria PASS."
elif n_passed == 3 and not criteria["n_gte_30"] and n_filled >= 20:
    # Hit edge metrics but n was light — extra observation needed
    verdict = "3-DAY-LIVE-OBSERVE"
    rationale = f"3/4 criteria pass; n={n_filled} below 30 floor — short live observation to confirm signal."
elif n_passed == 3:
    verdict = "OBSERVER-14D"
    rationale = f"3/4 criteria pass — extended shadow before promotion. Failing: {[k for k,v in criteria.items() if not v]}"
elif n_passed >= 2 and exp_r > 0:
    verdict = "OBSERVER-14D"
    rationale = f"{n_passed}/4 criteria pass with positive expectancy — observe-only as Tier-3 candidate."
else:
    verdict = "REJECT"
    rationale = f"Only {n_passed}/4 criteria pass; ExpR={exp_r:+.3f}R fleet."


aggregate = {
    "symbol": "XAGUSD",
    "main_head": "d614c54",
    "config": {
        "model": "claude-sonnet-4-6",
        "effort": "max",
        "frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
        "touch_count_reject_threshold": 2,
        "detector_version": "v2",
    },
    "period": {"start": "2026-01-02", "end": "2026-04-13"},
    "n_slices": len(SLICES),
    "n_slices_ok": sum(1 for info in slice_data.values() if info["ok"]),
    "n_total_records": n_total_records,
    "n_cands_total": n_cands_total,
    "n_filled": n_filled,
    "wins": wins,
    "wr": round(wr, 4),
    "wr_ci_95": [round(wr_lo, 4), round(wr_hi, 4)],
    "exp_r": round(exp_r, 4),
    "exp_r_ci_95": [round(exp_r_lo, 4), round(exp_r_hi, 4)],
    "total_r": round(total_r, 2),
    "max_dd": round(max_dd, 2),
    "max_consec_loss": max_consec_loss,
    "total_cost_usd": round(total_cost, 2),
    "criteria": {
        "wr_gte_55": {"value": round(wr, 4), "threshold": 0.55, "pass": criteria["wr_gte_55"]},
        "exp_r_gte_010": {"value": round(exp_r, 4), "threshold": 0.10, "pass": criteria["exp_r_gte_010"]},
        "n_gte_30": {"value": n_filled, "threshold": 30, "pass": criteria["n_gte_30"]},
        "max_dd_lte_8r": {"value": round(max_dd, 2), "threshold": 8.0, "pass": criteria["max_dd_lte_8r"]},
    },
    "verdict": verdict,
    "rationale": rationale,
    "by_direction": {
        "LONG": {"n": len(longs), "wins": long_wins, "wr": round(long_wins/len(longs), 4) if longs else None,
                 "wr_ci_95": [round(long_wr_lo, 4), round(long_wr_hi, 4)] if longs else None,
                 "exp_r": round(long_exp, 4), "total_r": round(sum(long_r), 2)},
        "SHORT": {"n": len(shorts), "wins": short_wins, "wr": round(short_wins/len(shorts), 4) if shorts else None,
                  "wr_ci_95": [round(short_wr_lo, 4), round(short_wr_hi, 4)] if shorts else None,
                  "exp_r": round(short_exp, 4), "total_r": round(sum(short_r), 2)},
    },
    "by_month": monthly,
    "by_kill_zone": kz_summary,
    "by_slice": per_slice_metrics,
    "by_framework": dict(framework_breakdown),
    "decision_distribution": dict(decision_counter),
    "top_no_trade_reasons": dict(no_trade_reasons.most_common(15)),
    "running_curve_R": running_curve,
    "slices": slice_data,
}

(ROOT / "aggregate.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
print(f"aggregate.json written -> {ROOT / 'aggregate.json'}")

# Save unified all_results.json
(ROOT / "all_results.json").write_text(
    json.dumps({"symbol": "XAGUSD", "n_filled": n_filled, "results": cands_filled}, indent=2),
    encoding="utf-8",
)
print(f"all_results.json written ({n_filled} filled CANDs)")

print()
print(f"FLEET: n_filled={n_filled} wr={wr*100:.1f}% [{wr_lo*100:.1f}, {wr_hi*100:.1f}] "
      f"expR={exp_r:+.3f} [{exp_r_lo:+.3f}, {exp_r_hi:+.3f}] totalR={total_r:+.1f} "
      f"maxDD={max_dd:.1f}R cost=${total_cost:.2f}")
print(f"VERDICT: {verdict} — {rationale}")

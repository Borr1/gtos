#!/usr/bin/env python3
"""Tier 2 instrument-expansion aggregation: 5 instruments × 7 slices.

Reads each per-slice all_results.json and computes:
- Fleet WR + Wilson 95% CI, Bootstrap Exp-R 95% CI, MaxDD chronological
- Per-direction (LONG/SHORT), per-framework, per-month decay
- Per-instrument verdict against pre-registered acceptance criteria
- Cross-instrument fleet aggregate

Outputs:
- TIER2_AGGREGATE_VERDICT.md (~3500-4000 words)
- tier2_aggregate.csv (per-instrument metrics)
- tier2_per_slice.csv (per-slice metrics)
- tier2_aggregate.json (raw)
"""
from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
INSTRUMENTS = ["XAGUSD", "NAS100", "GER40", "UK100", "EURUSD"]
SLICES = [f"s{i}" for i in range(1, 8)]


def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((centre - spread) / denom, (centre + spread) / denom)


def bootstrap_mean_ci(values: list[float], n_iter: int = 5000, alpha: float = 0.05) -> tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    m = sum(values) / len(values)
    means = []
    n = len(values)
    rng = random.Random(42)
    for _ in range(n_iter):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(n_iter * alpha / 2)]
    hi = means[int(n_iter * (1 - alpha / 2))]
    return (m, lo, hi)


def chronological_max_dd(records_sorted: list[dict]) -> tuple[float, list[float]]:
    """Compute MaxDD on chronologically-sorted realized R cumsum (peak-to-trough).
    records_sorted must already be sorted by candle_time ascending.
    Returns (max_dd, equity_curve)."""
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    curve = []
    for r in records_sorted:
        cum += float(r.get("r_multiple", 0))
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)
        curve.append(round(cum, 3))
    return max_dd, curve


def parse_framework(rec: dict) -> str:
    """Extract framework from raw_response JSON string."""
    rr = rec.get("raw_response", "") or ""
    m = re.search(r'"framework"\s*:\s*"([^"]+)"', rr)
    return m.group(1) if m else "unknown"


def load_slice(symbol: str, slice_name: str) -> dict:
    """Load slice all_results.json + return diag info."""
    sym_lower = symbol.lower()
    slice_dir = ROOT / f"tier2_{sym_lower}" / slice_name
    combined_path = slice_dir / "all_results.json"
    log_path = ROOT / f"tier2_{sym_lower}" / f"{slice_name}.log"

    info = {
        "symbol": symbol,
        "slice": slice_name,
        "exists": combined_path.exists(),
        "n_records": 0,
        "n_cands": 0,
        "n_filled": 0,
        "cost": 0.0,
        "start": None,
        "end": None,
        "records": [],
        "budget_capped": False,
    }

    if not combined_path.exists():
        return info

    try:
        data = json.loads(combined_path.read_text(encoding="utf-8"))
    except Exception as e:
        info["error"] = f"parse: {e}"
        return info

    recs = data.get("results", [])
    info["n_records"] = len(recs)
    info["cost"] = float(data.get("total_cost", 0.0))
    info["start"] = data.get("start")
    info["end"] = data.get("end")

    for r in recs:
        r["_slice"] = slice_name
        r["_symbol"] = symbol
    info["records"] = recs
    info["n_cands"] = sum(1 for r in recs if r.get("decision") == "CANDIDATE")
    info["n_filled"] = sum(1 for r in recs if r.get("outcome") in ("WIN", "LOSS"))

    # Detect budget cap
    if log_path.exists():
        try:
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")
            if "Budget limit" in log_text and "Stopping" in log_text:
                info["budget_capped"] = True
        except Exception:
            pass

    return info


# ── Phase 1: load all 35 slices ───────────────────────────────────────

all_slice_info: list[dict] = []
for sym in INSTRUMENTS:
    for s in SLICES:
        all_slice_info.append(load_slice(sym, s))

# ── Phase 2: per-instrument aggregation ───────────────────────────────

per_instrument: dict[str, dict] = {}

for sym in INSTRUMENTS:
    sym_slices = [si for si in all_slice_info if si["symbol"] == sym]

    all_records = []
    n_cands_total = 0
    total_cost = 0.0
    n_records_total = 0
    n_capped = 0
    cost_per_slice = []
    coverage_days = 0

    for si in sym_slices:
        all_records.extend(si["records"])
        n_records_total += si["n_records"]
        n_cands_total += si["n_cands"]
        total_cost += si["cost"]
        cost_per_slice.append(si["cost"])
        if si["budget_capped"]:
            n_capped += 1

    # Decision distribution
    decisions = Counter(r.get("decision") for r in all_records)
    outcomes = Counter(r.get("outcome") for r in all_records if r.get("outcome"))

    # CANDIDATE-level (these are the actual CANDs that proceeded — BLOCKED_LIMIT means setup found
    # but blocked from filling at decision-time)
    cands_all = [r for r in all_records if r.get("decision") == "CANDIDATE"]
    blocked = [r for r in all_records if r.get("decision") == "BLOCKED_LIMIT"]
    rejected_l2 = [r for r in all_records if r.get("decision") == "REJECTED_L2"]
    parse_err = [r for r in all_records if r.get("decision") == "PARSE_ERROR"]

    # Filled CANDs are those with outcome WIN/LOSS (UNFILLED = limit placed, never triggered)
    cands_filled = [r for r in cands_all if r.get("outcome") in ("WIN", "LOSS")]
    cands_unfilled = [r for r in cands_all if r.get("outcome") == "UNFILLED"]

    # Sort chronologically
    cands_filled_sorted = sorted(cands_filled, key=lambda r: r.get("candle_time", ""))

    # WR + Exp R
    r_multiples = [float(r.get("r_multiple", 0)) for r in cands_filled_sorted]
    n_filled = len(cands_filled_sorted)
    wins = sum(1 for r in r_multiples if r > 0)
    wr = (wins / n_filled) if n_filled else 0.0
    wr_lo, wr_hi = wilson_ci(wins, n_filled)
    exp_r, exp_r_lo, exp_r_hi = bootstrap_mean_ci(r_multiples)
    total_r = sum(r_multiples)
    max_dd, equity_curve = chronological_max_dd(cands_filled_sorted)

    # Max consecutive losses
    max_consec_loss = 0
    cur = 0
    for r in r_multiples:
        if r <= 0:
            cur += 1
            max_consec_loss = max(max_consec_loss, cur)
        else:
            cur = 0

    # Per-direction breakdown
    longs = [r for r in cands_filled_sorted if r.get("direction") == "LONG"]
    shorts = [r for r in cands_filled_sorted if r.get("direction") == "SHORT"]
    long_r = [float(r.get("r_multiple", 0)) for r in longs]
    short_r = [float(r.get("r_multiple", 0)) for r in shorts]
    long_wins = sum(1 for v in long_r if v > 0)
    short_wins = sum(1 for v in short_r if v > 0)
    lw_lo, lw_hi = wilson_ci(long_wins, len(longs))
    sw_lo, sw_hi = wilson_ci(short_wins, len(shorts))

    # Per-framework breakdown (over filled CANDs only)
    fw_counts: Counter = Counter()
    fw_wins: Counter = Counter()
    fw_r: dict[str, list[float]] = defaultdict(list)
    for r in cands_filled_sorted:
        fw = parse_framework(r)
        fw_counts[fw] += 1
        rm = float(r.get("r_multiple", 0))
        fw_r[fw].append(rm)
        if rm > 0:
            fw_wins[fw] += 1
    # Also non-filled CAND framework distribution
    fw_all_cands: Counter = Counter()
    for r in cands_all:
        fw_all_cands[parse_framework(r)] += 1

    # Per-month decay (Jan / Feb / Mar / Apr) — by candle date
    by_month: dict[str, list[float]] = defaultdict(list)
    for r in cands_filled_sorted:
        d = r.get("date", "")
        if d and len(d) >= 7:
            by_month[d[:7]].append(float(r.get("r_multiple", 0)))

    monthly = {}
    for m in sorted(by_month):
        rs = by_month[m]
        nm = len(rs)
        wm = sum(1 for v in rs if v > 0)
        monthly[m] = {
            "n": nm, "wins": wm,
            "wr": wm / nm if nm else 0.0,
            "exp_r": sum(rs) / nm if nm else 0.0,
            "total_r": sum(rs),
        }

    # H1 (Jan+Feb) vs H2 (Mar+Apr)
    h1_r = [v for m, rs in by_month.items() if m in ("2026-01", "2026-02") for v in rs]
    h2_r = [v for m, rs in by_month.items() if m in ("2026-03", "2026-04") for v in rs]
    h1_wins = sum(1 for v in h1_r if v > 0)
    h2_wins = sum(1 for v in h2_r if v > 0)
    h1_lo, h1_hi = wilson_ci(h1_wins, len(h1_r))
    h2_lo, h2_hi = wilson_ci(h2_wins, len(h2_r))

    # Per-KZ
    by_kz: dict[str, list[float]] = defaultdict(list)
    for r in cands_filled_sorted:
        by_kz[r.get("kill_zone", "?")].append(float(r.get("r_multiple", 0)))
    kz_summary = {}
    for kz, rs in by_kz.items():
        nm = len(rs)
        wm = sum(1 for v in rs if v > 0)
        kz_summary[kz] = {
            "n": nm, "wr": wm / nm if nm else 0.0,
            "exp_r": sum(rs) / nm if nm else 0.0,
            "total_r": sum(rs),
        }

    # Per-slice
    per_slice = {}
    for s in SLICES:
        sf = [r for r in cands_filled_sorted if r.get("_slice") == s]
        si_info = next((x for x in sym_slices if x["slice"] == s), None)
        rs = [float(r.get("r_multiple", 0)) for r in sf]
        wm = sum(1 for v in rs if v > 0)
        per_slice[s] = {
            "n_records": si_info["n_records"] if si_info else 0,
            "n_cands_all": si_info["n_cands"] if si_info else 0,
            "n_filled": len(rs),
            "wins": wm,
            "wr": wm / len(rs) if rs else None,
            "exp_r": sum(rs) / len(rs) if rs else None,
            "total_r": sum(rs),
            "cost": si_info["cost"] if si_info else 0.0,
            "budget_capped": si_info["budget_capped"] if si_info else False,
            "start": si_info["start"] if si_info else None,
            "end": si_info["end"] if si_info else None,
        }

    # ── Pre-registered acceptance criteria ──
    # Promote: WR ≥55% AND Exp R ≥+0.10R AND n≥30 AND MaxDD ≤8R
    # 3-day-live observe: WR 50-55% OR n 20-30
    # Observer-14d: WR 45-50%
    # Reject: WR <45% OR negative Exp R OR MaxDD >8R
    pre_reg = {
        "wr_ge_55": wr >= 0.55,
        "exp_r_ge_0.10": exp_r >= 0.10,
        "n_ge_30": n_filled >= 30,
        "maxdd_le_8R": max_dd <= 8.0,
    }
    n_passed = sum(1 for v in pre_reg.values() if v)

    # Verdict logic
    if all(pre_reg.values()):
        verdict = "PROMOTE-LIVE"
        verdict_detail = "all 4 acceptance criteria pass"
    elif n_filled < 30 and n_filled >= 20 and wr >= 0.50:
        verdict = "3-DAY-LIVE-OBSERVE"
        verdict_detail = f"borderline n={n_filled}, WR {wr*100:.1f}% in 50-55% band"
    elif wr < 0.45 or exp_r < 0 or max_dd > 8.0:
        verdict = "REJECT"
        reasons = []
        if wr < 0.45:
            reasons.append(f"WR {wr*100:.1f}% <45%")
        if exp_r < 0:
            reasons.append(f"Exp R {exp_r:+.3f} negative")
        if max_dd > 8.0:
            reasons.append(f"MaxDD {max_dd:.2f}R >8R")
        verdict_detail = "; ".join(reasons)
    elif 0.45 <= wr < 0.50:
        verdict = "OBSERVER-14D"
        verdict_detail = f"WR {wr*100:.1f}% in 45-50% band"
    elif 0.50 <= wr < 0.55:
        verdict = "3-DAY-LIVE-OBSERVE"
        verdict_detail = f"WR {wr*100:.1f}% in 50-55% band"
    else:
        # WR ≥55 but exp_r or n or maxdd fail
        verdict = "OBSERVER-14D"
        bads = []
        if not pre_reg["exp_r_ge_0.10"]:
            bads.append(f"Exp R {exp_r:+.3f}")
        if not pre_reg["n_ge_30"]:
            bads.append(f"n={n_filled}")
        if not pre_reg["maxdd_le_8R"]:
            bads.append(f"MaxDD {max_dd:.2f}R")
        verdict_detail = "WR passes but: " + ", ".join(bads)

    per_instrument[sym] = {
        "symbol": sym,
        "n_records_total": n_records_total,
        "n_decisions": dict(decisions),
        "n_outcomes": dict(outcomes),
        "n_cands_total": n_cands_total,
        "n_blocked_limit": len(blocked),
        "n_rejected_l2": len(rejected_l2),
        "n_parse_error": len(parse_err),
        "n_filled": n_filled,
        "n_unfilled": len(cands_unfilled),
        "wins": wins,
        "wr": wr,
        "wr_ci": (wr_lo, wr_hi),
        "exp_r": exp_r,
        "exp_r_ci": (exp_r_lo, exp_r_hi),
        "total_r": total_r,
        "max_dd": max_dd,
        "max_consec_loss": max_consec_loss,
        "equity_curve": equity_curve,
        "per_direction": {
            "LONG": {
                "n": len(longs), "wins": long_wins,
                "wr": long_wins / len(longs) if longs else None,
                "wr_ci": (lw_lo, lw_hi),
                "exp_r": sum(long_r) / len(long_r) if long_r else None,
                "total_r": sum(long_r),
            },
            "SHORT": {
                "n": len(shorts), "wins": short_wins,
                "wr": short_wins / len(shorts) if shorts else None,
                "wr_ci": (sw_lo, sw_hi),
                "exp_r": sum(short_r) / len(short_r) if short_r else None,
                "total_r": sum(short_r),
            },
        },
        "per_framework": {
            fw: {
                "n_filled": fw_counts[fw],
                "wins": fw_wins[fw],
                "wr": fw_wins[fw] / fw_counts[fw] if fw_counts[fw] else None,
                "exp_r": sum(fw_r[fw]) / fw_counts[fw] if fw_counts[fw] else None,
                "total_r": sum(fw_r[fw]),
            } for fw in fw_counts
        },
        "per_framework_all_cands": dict(fw_all_cands),
        "monthly": monthly,
        "h1_h2": {
            "h1_n": len(h1_r),
            "h1_wins": h1_wins,
            "h1_wr": h1_wins / len(h1_r) if h1_r else None,
            "h1_wr_ci": (h1_lo, h1_hi),
            "h1_exp_r": sum(h1_r) / len(h1_r) if h1_r else None,
            "h2_n": len(h2_r),
            "h2_wins": h2_wins,
            "h2_wr": h2_wins / len(h2_r) if h2_r else None,
            "h2_wr_ci": (h2_lo, h2_hi),
            "h2_exp_r": sum(h2_r) / len(h2_r) if h2_r else None,
        },
        "kz_summary": kz_summary,
        "per_slice": per_slice,
        "total_cost": total_cost,
        "n_capped": n_capped,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "pre_reg_pass": pre_reg,
        "pre_reg_n_passed": n_passed,
    }


# ── Phase 3: Cross-instrument fleet aggregate ────────────────────────

fleet_filled = []
for sym in INSTRUMENTS:
    sym_slices = [si for si in all_slice_info if si["symbol"] == sym]
    for si in sym_slices:
        for r in si["records"]:
            if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS"):
                fleet_filled.append(r)

fleet_filled_sorted = sorted(fleet_filled, key=lambda r: r.get("candle_time", ""))
fleet_r = [float(r.get("r_multiple", 0)) for r in fleet_filled_sorted]
fleet_wins = sum(1 for v in fleet_r if v > 0)
fleet_n = len(fleet_filled_sorted)
fleet_wr = fleet_wins / fleet_n if fleet_n else 0.0
fleet_wr_lo, fleet_wr_hi = wilson_ci(fleet_wins, fleet_n)
fleet_exp_r, fleet_exp_lo, fleet_exp_hi = bootstrap_mean_ci(fleet_r)
fleet_total_r = sum(fleet_r)
fleet_max_dd, fleet_curve = chronological_max_dd(fleet_filled_sorted)

# Total fleet API cost
total_cost = sum(per_instrument[s]["total_cost"] for s in INSTRUMENTS)
total_cands = sum(per_instrument[s]["n_cands_total"] for s in INSTRUMENTS)
total_records = sum(per_instrument[s]["n_records_total"] for s in INSTRUMENTS)
total_capped = sum(per_instrument[s]["n_capped"] for s in INSTRUMENTS)

aggregate = {
    "instruments": per_instrument,
    "fleet": {
        "n_records_total": total_records,
        "n_cands_total": total_cands,
        "n_filled": fleet_n,
        "wins": fleet_wins,
        "wr": fleet_wr,
        "wr_ci": (fleet_wr_lo, fleet_wr_hi),
        "exp_r": fleet_exp_r,
        "exp_r_ci": (fleet_exp_lo, fleet_exp_hi),
        "total_r": fleet_total_r,
        "max_dd": fleet_max_dd,
        "total_cost": total_cost,
        "n_slices_capped": total_capped,
    },
}

# ── Phase 4: write artefacts ─────────────────────────────────────────

(ROOT / "tier2_aggregate.json").write_text(json.dumps(aggregate, indent=2, default=str))

# Per-instrument CSV
csv_path = ROOT / "tier2_aggregate.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "symbol", "n_records", "n_cands_total", "n_filled", "n_unfilled",
        "n_blocked_limit", "n_rejected_l2", "n_parse_error",
        "wins", "wr", "wr_ci_lo", "wr_ci_hi",
        "exp_r", "exp_r_ci_lo", "exp_r_ci_hi", "total_r",
        "max_dd", "max_consec_loss",
        "long_n", "long_wr", "long_exp_r",
        "short_n", "short_wr", "short_exp_r",
        "h1_n", "h1_wr", "h2_n", "h2_wr",
        "total_cost", "n_capped", "verdict", "verdict_detail",
    ])
    for sym in INSTRUMENTS:
        d = per_instrument[sym]
        ld = d["per_direction"]["LONG"]
        sd = d["per_direction"]["SHORT"]
        h = d["h1_h2"]
        w.writerow([
            sym, d["n_records_total"], d["n_cands_total"], d["n_filled"], d["n_unfilled"],
            d["n_blocked_limit"], d["n_rejected_l2"], d["n_parse_error"],
            d["wins"], f"{d['wr']:.4f}", f"{d['wr_ci'][0]:.4f}", f"{d['wr_ci'][1]:.4f}",
            f"{d['exp_r']:.4f}", f"{d['exp_r_ci'][0]:.4f}", f"{d['exp_r_ci'][1]:.4f}",
            f"{d['total_r']:.3f}",
            f"{d['max_dd']:.3f}", d["max_consec_loss"],
            ld["n"], f"{ld['wr']:.4f}" if ld['wr'] is not None else "",
            f"{ld['exp_r']:.4f}" if ld['exp_r'] is not None else "",
            sd["n"], f"{sd['wr']:.4f}" if sd['wr'] is not None else "",
            f"{sd['exp_r']:.4f}" if sd['exp_r'] is not None else "",
            h["h1_n"], f"{h['h1_wr']:.4f}" if h['h1_wr'] is not None else "",
            h["h2_n"], f"{h['h2_wr']:.4f}" if h['h2_wr'] is not None else "",
            f"{d['total_cost']:.2f}", d["n_capped"], d["verdict"], d["verdict_detail"],
        ])

# Per-slice CSV
slice_csv = ROOT / "tier2_per_slice.csv"
with open(slice_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "symbol", "slice", "start", "end", "n_records", "n_cands_all",
        "n_filled", "wins", "wr", "exp_r", "total_r", "cost", "budget_capped",
    ])
    for sym in INSTRUMENTS:
        for s in SLICES:
            d = per_instrument[sym]["per_slice"][s]
            w.writerow([
                sym, s, d["start"], d["end"], d["n_records"], d["n_cands_all"],
                d["n_filled"], d["wins"],
                f"{d['wr']:.4f}" if d['wr'] is not None else "",
                f"{d['exp_r']:.4f}" if d['exp_r'] is not None else "",
                f"{d['total_r']:.3f}", f"{d['cost']:.2f}", d["budget_capped"],
            ])

# Print summary
print("=" * 70)
print("TIER 2 AGGREGATE — 5 instruments × 7 slices")
print("=" * 70)
print()
print(f"FLEET TOTALS: n_records={total_records}  n_cands={total_cands}  "
      f"n_filled={fleet_n}  cost=${total_cost:.2f}  slices_capped={total_capped}/35")
print(f"FLEET WR: {fleet_wr*100:.2f}%  CI [{fleet_wr_lo*100:.2f}, {fleet_wr_hi*100:.2f}]  n={fleet_n}")
print(f"FLEET Exp R: {fleet_exp_r:+.4f}R  CI [{fleet_exp_lo:+.4f}, {fleet_exp_hi:+.4f}]")
print(f"FLEET Total R: {fleet_total_r:+.2f}R  MaxDD: {fleet_max_dd:.2f}R")
print()
for sym in INSTRUMENTS:
    d = per_instrument[sym]
    n = d["n_filled"]
    wr_pct = d["wr"] * 100
    print(f"{sym}: n_cands={d['n_cands_total']:3d}  filled={n:3d}  WR={wr_pct:5.1f}% "
          f"[{d['wr_ci'][0]*100:5.1f},{d['wr_ci'][1]*100:5.1f}]  "
          f"ExpR={d['exp_r']:+.3f}  TotR={d['total_r']:+.2f}  MaxDD={d['max_dd']:.2f}R  "
          f"=> {d['verdict']} ({d['verdict_detail']})")

print()
print(f"CSV: {csv_path}")
print(f"Slice CSV: {slice_csv}")
print(f"JSON: {ROOT / 'tier2_aggregate.json'}")

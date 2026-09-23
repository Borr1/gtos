#!/usr/bin/env python3
"""
SMC A6 — Sweep Clustering & Sequential Sweep Analysis (XAUUSD)

Analyzes double/triple sweeps, cross-session sequences, and timing patterns.
"""

import json
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

ATLAS = Path(__file__).resolve().parent.parent / "knowledge_base_backtest" / "analysis" / "microstructure_stream1_sweeps_20260405.json"
OUT   = Path(__file__).resolve().parent.parent / "knowledge_base_backtest" / "analysis" / "smc_sweep_clustering_20260405.json"
DISC_CUTOFF = "2025-07-01"

HIGH_LEVELS = {"asian_h", "pdh"}
LOW_LEVELS  = {"asian_l", "pdl"}


def flag(n, label=""):
    return f"LOW_N ({n})" if n < 30 else "OK"


def pct(num, denom):
    return round(100 * num / denom, 1) if denom else 0.0


def stats_dict(vals):
    if not vals:
        return {"n": 0, "mean": None, "median": None, "p25": None, "p75": None}
    vals_s = sorted(vals)
    n = len(vals_s)
    return {
        "n": n,
        "n_flag": flag(n),
        "mean": round(statistics.mean(vals_s), 1),
        "median": round(statistics.median(vals_s), 1),
        "p25": round(vals_s[max(0, int(n * 0.25))], 1),
        "p75": round(vals_s[min(n - 1, int(n * 0.75))], 1),
    }


def parse_time(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def sweep_direction(level):
    """Return 'high' or 'low' based on level_swept."""
    if level in HIGH_LEVELS:
        return "high"
    return "low"


def analyze_period(days, label):
    """Run all analyses on a list of daily records."""
    total_days = len(days)
    sweep_days = [d for d in days if d.get("sweeps")]
    n_sweep_days = len(sweep_days)

    # ── 1. Double sweeps ──────────────────────────────────────────
    double_asian = []      # asian_h AND asian_l both swept
    double_pd = []         # pdh AND pdl both swept
    double_any_hl = []     # any high AND any low swept
    multi_sweep_days = []  # days with 2+ sweeps

    for d in sweep_days:
        levels = {s["level_swept"] for s in d["sweeps"]}
        has_ah = "asian_h" in levels
        has_al = "asian_l" in levels
        has_pdh = "pdh" in levels
        has_pdl = "pdl" in levels
        has_any_high = bool(levels & HIGH_LEVELS)
        has_any_low  = bool(levels & LOW_LEVELS)

        if has_ah and has_al:
            double_asian.append(d)
        if has_pdh and has_pdl:
            double_pd.append(d)
        if has_any_high and has_any_low:
            double_any_hl.append(d)
        if len(d["sweeps"]) >= 2:
            multi_sweep_days.append(d)

    double_sweep_stats = {
        "total_days": total_days,
        "sweep_days": n_sweep_days,
        "double_asian_hl": {
            "n": len(double_asian),
            "pct_of_sweep_days": pct(len(double_asian), n_sweep_days),
            "n_flag": flag(len(double_asian)),
        },
        "double_pd_hl": {
            "n": len(double_pd),
            "pct_of_sweep_days": pct(len(double_pd), n_sweep_days),
            "n_flag": flag(len(double_pd)),
        },
        "double_any_high_and_low": {
            "n": len(double_any_hl),
            "pct_of_sweep_days": pct(len(double_any_hl), n_sweep_days),
            "n_flag": flag(len(double_any_hl)),
        },
    }

    # ── 2. Second sweep behavior ──────────────────────────────────
    # On days where both a high and low were swept, which came second?
    second_sweep_data = []
    time_gaps = []

    for d in double_any_hl:
        sweeps_sorted = sorted(d["sweeps"], key=lambda s: s["sweep_time"])
        # Find first high sweep and first low sweep
        first_high = next((s for s in sweeps_sorted if s["level_swept"] in HIGH_LEVELS), None)
        first_low  = next((s for s in sweeps_sorted if s["level_swept"] in LOW_LEVELS), None)
        if not first_high or not first_low:
            continue

        t_high = parse_time(first_high["sweep_time"])
        t_low  = parse_time(first_low["sweep_time"])

        if t_high < t_low:
            first_sw, second_sw = first_high, first_low
        else:
            first_sw, second_sw = first_low, first_high

        gap_mins = abs((t_high - t_low).total_seconds()) / 60
        time_gaps.append(gap_mins)

        second_sweep_data.append({
            "second_level": second_sw["level_swept"],
            "second_dir": sweep_direction(second_sw["level_swept"]),
            "second_type": second_sw["sweep_type"],
            "second_kz": second_sw["kz"],
            "next_candle_dir": second_sw.get("next_candle_dir"),
            "gap_mins": gap_mins,
        })

    # Tally second sweep next_candle_dir
    second_dir_counts = defaultdict(int)
    second_type_counts = defaultdict(int)
    second_reversal = 0  # second sweep is low + next candle up, or high + next candle down
    for sd in second_sweep_data:
        ncd = sd["next_candle_dir"]
        second_dir_counts[ncd] += 1
        second_type_counts[sd["second_type"]] += 1
        # Reversal = next candle opposes the sweep direction
        if sd["second_dir"] == "low" and ncd == "up":
            second_reversal += 1
        elif sd["second_dir"] == "high" and ncd == "down":
            second_reversal += 1

    n_second = len(second_sweep_data)
    second_sweep_behavior = {
        "n_double_hl_days_analyzed": n_second,
        "n_flag": flag(n_second),
        "second_sweep_next_candle": dict(second_dir_counts),
        "second_sweep_reversal_pct": pct(second_reversal, n_second),
        "second_sweep_type_breakdown": dict(second_type_counts),
        "theory": "second_sweep_is_real_reversal",
    }

    # ── 3. Time between sweeps ────────────────────────────────────
    time_between_sweeps = stats_dict(time_gaps)

    # Also compute gap for ALL multi-sweep days (first to last sweep)
    all_gaps = []
    for d in multi_sweep_days:
        sweeps_sorted = sorted(d["sweeps"], key=lambda s: s["sweep_time"])
        t0 = parse_time(sweeps_sorted[0]["sweep_time"])
        t1 = parse_time(sweeps_sorted[-1]["sweep_time"])
        gap = (t1 - t0).total_seconds() / 60
        if gap > 0:
            all_gaps.append(gap)

    time_between_sweeps_all = stats_dict(all_gaps)
    time_between_sweeps_all["description"] = "first_to_last_sweep_on_multi_sweep_days"

    # ── 4. Triple+ sweep days ─────────────────────────────────────
    triple_days = [d for d in sweep_days if len(d.get("sweeps", [])) >= 3]
    quad_days   = [d for d in sweep_days if len(d.get("sweeps", [])) >= 4]

    # What levels on triple days?
    triple_level_freq = defaultdict(int)
    for d in triple_days:
        for s in d["sweeps"]:
            triple_level_freq[s["level_swept"]] += 1

    # After 3rd sweep: next_candle_dir
    third_sweep_ncd = defaultdict(int)
    third_sweep_reversal = 0
    for d in triple_days:
        sweeps_sorted = sorted(d["sweeps"], key=lambda s: s["sweep_time"])
        third = sweeps_sorted[2]
        ncd = third.get("next_candle_dir")
        third_sweep_ncd[ncd] += 1
        d_dir = sweep_direction(third["level_swept"])
        if (d_dir == "low" and ncd == "up") or (d_dir == "high" and ncd == "down"):
            third_sweep_reversal += 1

    n_triple = len(triple_days)
    triple_sweep_stats = {
        "n_triple_plus_days": n_triple,
        "n_quad_plus_days": len(quad_days),
        "pct_of_sweep_days": pct(n_triple, n_sweep_days),
        "n_flag": flag(n_triple),
        "level_frequency_on_triple_days": dict(triple_level_freq),
        "third_sweep_next_candle": dict(third_sweep_ncd),
        "third_sweep_reversal_pct": pct(third_sweep_reversal, n_triple),
        "vs_second_sweep_reversal_pct": second_sweep_behavior["second_sweep_reversal_pct"],
        "verdict": (
            "third_sweep_better" if pct(third_sweep_reversal, n_triple) > second_sweep_behavior["second_sweep_reversal_pct"]
            else "second_sweep_better_or_equal"
        ),
    }

    # ── 5. Cross-session sequences ────────────────────────────────
    # London sweep X -> NY sweep Y patterns
    patterns = {
        "london_high_then_ny_high": 0,  # bullish continuation
        "london_high_then_ny_low": 0,   # reversal
        "london_low_then_ny_low": 0,    # bearish continuation
        "london_low_then_ny_high": 0,   # reversal
        "london_high_then_ny_pdh": 0,   # specific: london asian_h -> ny pdh
        "london_low_then_ny_pdl": 0,    # specific: london asian_l -> ny pdl
    }
    cross_session_days = 0

    for d in sweep_days:
        london_sweeps = [s for s in d["sweeps"] if s["kz"] == "london"]
        ny_sweeps     = [s for s in d["sweeps"] if s["kz"] == "ny"]
        if not london_sweeps or not ny_sweeps:
            continue

        cross_session_days += 1
        # First london sweep direction
        lon_first = sorted(london_sweeps, key=lambda s: s["sweep_time"])[0]
        lon_dir = sweep_direction(lon_first["level_swept"])

        # First ny sweep direction
        ny_first = sorted(ny_sweeps, key=lambda s: s["sweep_time"])[0]
        ny_dir = sweep_direction(ny_first["level_swept"])

        key = f"london_{lon_dir}_then_ny_{ny_dir}"
        patterns[key] = patterns.get(key, 0) + 1

        # Specific sub-patterns
        lon_levels = {s["level_swept"] for s in london_sweeps}
        ny_levels  = {s["level_swept"] for s in ny_sweeps}
        if "asian_h" in lon_levels and "pdh" in ny_levels:
            patterns["london_high_then_ny_pdh"] += 1
        if "asian_l" in lon_levels and "pdl" in ny_levels:
            patterns["london_low_then_ny_pdl"] += 1

    # Next candle direction for cross-session continuation vs reversal
    cross_ncd = {"continuation": defaultdict(int), "reversal": defaultdict(int)}
    for d in sweep_days:
        london_sweeps = [s for s in d["sweeps"] if s["kz"] == "london"]
        ny_sweeps     = [s for s in d["sweeps"] if s["kz"] == "ny"]
        if not london_sweeps or not ny_sweeps:
            continue

        lon_first = sorted(london_sweeps, key=lambda s: s["sweep_time"])[0]
        ny_first  = sorted(ny_sweeps, key=lambda s: s["sweep_time"])[0]
        lon_dir = sweep_direction(lon_first["level_swept"])
        ny_dir  = sweep_direction(ny_first["level_swept"])
        ncd = ny_first.get("next_candle_dir")

        if lon_dir == ny_dir:
            cross_ncd["continuation"][ncd] += 1
        else:
            cross_ncd["reversal"][ncd] += 1

    cross_session_sequences = {
        "n_cross_session_days": cross_session_days,
        "n_flag": flag(cross_session_days),
        "pattern_counts": patterns,
        "bullish_continuation_pct": pct(
            patterns.get("london_high_then_ny_high", 0), cross_session_days
        ),
        "bearish_continuation_pct": pct(
            patterns.get("london_low_then_ny_low", 0), cross_session_days
        ),
        "reversal_high_to_low_pct": pct(
            patterns.get("london_high_then_ny_low", 0), cross_session_days
        ),
        "reversal_low_to_high_pct": pct(
            patterns.get("london_low_then_ny_high", 0), cross_session_days
        ),
        "continuation_total_pct": pct(
            patterns.get("london_high_then_ny_high", 0) + patterns.get("london_low_then_ny_low", 0),
            cross_session_days,
        ),
        "reversal_total_pct": pct(
            patterns.get("london_high_then_ny_low", 0) + patterns.get("london_low_then_ny_high", 0),
            cross_session_days,
        ),
        "ny_next_candle_after_continuation": dict(cross_ncd["continuation"]),
        "ny_next_candle_after_reversal": dict(cross_ncd["reversal"]),
    }

    # ── 6. Timing within KZ ───────────────────────────────────────
    buckets = {"0-15": [], "15-30": [], "30-45": [], "45-60": [], "60+": []}

    def bucket_key(mins):
        if mins < 15:
            return "0-15"
        elif mins < 30:
            return "15-30"
        elif mins < 45:
            return "30-45"
        elif mins < 60:
            return "45-60"
        else:
            return "60+"

    for d in sweep_days:
        for s in d["sweeps"]:
            bk = bucket_key(s["mins_into_kz"])
            buckets[bk].append(s)

    timing_analysis = {}
    for bk, sweeps_list in buckets.items():
        n = len(sweeps_list)
        rej = sum(1 for s in sweeps_list if s["sweep_type"] == "rejection")
        rev = sum(
            1 for s in sweeps_list
            if (sweep_direction(s["level_swept"]) == "low" and s.get("next_candle_dir") == "up")
            or (sweep_direction(s["level_swept"]) == "high" and s.get("next_candle_dir") == "down")
        )
        timing_analysis[bk] = {
            "n": n,
            "n_flag": flag(n),
            "rejection_pct": pct(rej, n),
            "reversal_next_candle_pct": pct(rev, n),
        }

    return {
        "period": label,
        "double_sweep_stats": double_sweep_stats,
        "second_sweep_behavior": second_sweep_behavior,
        "time_between_sweeps": {
            "high_low_gap": time_between_sweeps,
            "first_to_last_any": time_between_sweeps_all,
        },
        "triple_sweep_stats": triple_sweep_stats,
        "cross_session_sequences": cross_session_sequences,
        "timing_analysis": timing_analysis,
    }


def main():
    with open(ATLAS) as f:
        data = json.load(f)

    xau = data["daily_data"]["XAUUSD"]
    print(f"Loaded {len(xau)} XAUUSD daily records")

    disc = [d for d in xau if d["date"] < DISC_CUTOFF]
    val  = [d for d in xau if d["date"] >= DISC_CUTOFF]
    print(f"Discovery: {len(disc)} days | Validation: {len(val)} days")

    res_all  = analyze_period(xau, "all")
    res_disc = analyze_period(disc, "discovery (<2025-07-01)")
    res_val  = analyze_period(val, "validation (>=2025-07-01)")

    # ── Verdict ───────────────────────────────────────────────────
    ds = res_all["double_sweep_stats"]
    ss = res_all["second_sweep_behavior"]
    cs = res_all["cross_session_sequences"]
    ts = res_all["triple_sweep_stats"]
    tm = res_all["timing_analysis"]

    verdict_lines = []

    # Double sweep frequency
    dbl_pct = ds["double_any_high_and_low"]["pct_of_sweep_days"]
    verdict_lines.append(f"Double-sweep (high+low same day) occurs on {dbl_pct}% of sweep days ({ds['double_any_high_and_low']['n']} days)")

    # Second sweep reversal
    rev_pct = ss["second_sweep_reversal_pct"]
    if rev_pct >= 55:
        verdict_lines.append(f"Second sweep shows {rev_pct}% reversal on next candle -> supports 'second sweep = real direction' theory")
    else:
        verdict_lines.append(f"Second sweep shows only {rev_pct}% reversal -> does NOT strongly support 'second sweep = real direction' theory")

    # Triple vs double
    verdict_lines.append(
        f"Triple-sweep days: 3rd sweep reversal {ts['third_sweep_reversal_pct']}% vs 2nd sweep {ss['second_sweep_reversal_pct']}% -> {ts['verdict']}"
    )

    # Cross-session
    cont_pct = cs["continuation_total_pct"]
    rev_cs_pct = cs["reversal_total_pct"]
    verdict_lines.append(
        f"Cross-session: continuation {cont_pct}% vs reversal {rev_cs_pct}% of days with both London + NY sweeps"
    )

    # Timing
    early = tm.get("0-15", {})
    late  = tm.get("60+", {})
    verdict_lines.append(
        f"Timing: 0-15 min into KZ -> {early.get('reversal_next_candle_pct', 'N/A')}% reversal (n={early.get('n',0)}) | 60+ min -> {late.get('reversal_next_candle_pct', 'N/A')}% reversal (n={late.get('n',0)})"
    )

    # Discovery vs validation stability
    disc_dbl = res_disc["double_sweep_stats"]["double_any_high_and_low"]["pct_of_sweep_days"]
    val_dbl  = res_val["double_sweep_stats"]["double_any_high_and_low"]["pct_of_sweep_days"]
    disc_rev = res_disc["second_sweep_behavior"]["second_sweep_reversal_pct"]
    val_rev  = res_val["second_sweep_behavior"]["second_sweep_reversal_pct"]
    verdict_lines.append(
        f"Stability: double-sweep % disc={disc_dbl} val={val_dbl} | 2nd-sweep reversal disc={disc_rev}% val={val_rev}%"
    )

    output = {
        "metadata": {
            "instrument": "XAUUSD",
            "source": str(ATLAS.name),
            "generated": datetime.now().isoformat(),
            "discovery_cutoff": DISC_CUTOFF,
            "total_days": len(xau),
        },
        "all_period": res_all,
        "discovery_vs_validation": {
            "discovery": res_disc,
            "validation": res_val,
        },
        "verdict": verdict_lines,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved -> {OUT}")

    print("\n=== VERDICT ===")
    for v in verdict_lines:
        print(f"  - {v}")


if __name__ == "__main__":
    main()

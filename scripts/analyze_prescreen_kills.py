"""Investigate pre-screened-out dates for missed ob_retest opportunities.

For every weekday killed by the D1/H4 pre-screen, recompute the MSO and
check whether ob_retest mechanical preconditions existed during kill zones.

Usage:
    python scripts/analyze_prescreen_kills.py --start 2024-04-01 --end 2026-03-13

Outputs:
    analysis/prescreen_killed_dates.csv
    analysis/prescreen_kill_details.json
    analysis/prescreen_loosening_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env", override=True)

import yaml

from scripts.historical_data_loader import (
    parse_tradingview_csv,
    replay_london_open,
    replay_ny_open,
)
import src.components.market_state as _ms_mod
from src.components.market_state import compute_market_state

# Monkey-patch write_pipeline to no-op for analysis (avoid file I/O on every MSO)
_ms_mod.write_pipeline = lambda filename, data: None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

HISTORICAL_DIR = _PROJECT_ROOT / "data" / "historical"
ANALYSIS_DIR = _PROJECT_ROOT / "analysis"

# KZ windows (UTC) — same as orchestrator / batch_backtest
LONDON_KZ_START = (7, 0)
LONDON_KZ_END = (10, 30)
NY_KZ_START = (13, 0)
NY_KZ_END = (15, 30)


# ═══════════════════════════════════════════════════════════════════════
# Step 1: Load config and historical data
# ═══════════════════════════════════════════════════════════════════════

def load_config() -> dict:
    with open(_PROJECT_ROOT / "config" / "agent_config.yaml") as f:
        return yaml.safe_load(f)


def load_all_candles() -> dict[str, list[dict]]:
    """Load all timeframe CSVs into the all_candles dict."""
    all_candles: dict[str, list[dict]] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        csv_path = HISTORICAL_DIR / f"XAUUSD_{tf}.csv"
        if csv_path.exists():
            all_candles[tf] = parse_tradingview_csv(str(csv_path))
        else:
            logger.warning("Missing %s CSV: %s", tf, csv_path)
            all_candles[tf] = []
    return all_candles


# ═══════════════════════════════════════════════════════════════════════
# Step 2: Identify pre-screened-out dates (recompute from data)
# ═══════════════════════════════════════════════════════════════════════

def prescreen_date(
    date_str: str,
    all_candles: dict[str, list[dict]],
    config: dict,
) -> tuple[bool, str, str, str]:
    """Recompute pre-screen for a date.

    Returns (passed, skip_reason, d1_direction, h4_direction).
    """
    try:
        candle_gen = replay_london_open(date_str, all_candles)
        first_raw = next(candle_gen)
    except (StopIteration, Exception):
        return False, "no_london_candles", "", ""

    mso = compute_market_state(first_raw, config)
    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}

    d1 = tfs.get("D1")
    d1_dir = d1.structure.direction if d1 else "insufficient_data"

    h4 = tfs.get("H4")
    h4_dir = h4.structure.direction if h4 else "insufficient_data"

    if d1_dir not in ("bullish", "bearish"):
        return False, f"L1_d1_{d1_dir}", d1_dir, h4_dir

    if h4_dir not in ("bullish", "bearish"):
        return False, f"L2_h4_{h4_dir}", d1_dir, h4_dir
    if h4_dir != d1_dir:
        return False, f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}", d1_dir, h4_dir

    return True, "", d1_dir, h4_dir


def collect_killed_dates(
    start_str: str,
    end_str: str,
    all_candles: dict[str, list[dict]],
    config: dict,
) -> list[dict]:
    """Return list of killed dates with reason and D1/H4 bias info."""
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    killed: list[dict] = []
    d = start
    total_weekdays = 0
    no_data_count = 0
    passed_count = 0

    while d <= end:
        if d.weekday() >= 5:
            d += timedelta(days=1)
            continue

        total_weekdays += 1
        date_str = d.isoformat()

        # Check M15 data availability
        has_data = any(
            c["time"].startswith(date_str)
            for c in all_candles.get("M15", [])
        )
        if not has_data:
            no_data_count += 1
            d += timedelta(days=1)
            continue

        passed, reason, d1_dir, h4_dir = prescreen_date(date_str, all_candles, config)

        if passed:
            passed_count += 1
        else:
            killed.append({
                "date": date_str,
                "kill_reason": reason,
                "d1_direction": d1_dir,
                "h4_direction": h4_dir,
            })

        d += timedelta(days=1)

    logger.info(
        "Pre-screen scan: %d weekdays, %d no data, %d passed, %d killed",
        total_weekdays, no_data_count, passed_count, len(killed),
    )
    return killed


# ═══════════════════════════════════════════════════════════════════════
# Step 3-4: Check ob_retest preconditions on killed dates
# ═══════════════════════════════════════════════════════════════════════

def _time_in_kz(candle_time_str: str, kz_start: tuple, kz_end: tuple) -> bool:
    """Check if a candle time falls within a kill zone window."""
    try:
        dt = datetime.fromisoformat(candle_time_str.replace("Z", "+00:00"))
    except ValueError:
        return False
    h, m = dt.hour, dt.minute
    start_minutes = kz_start[0] * 60 + kz_start[1]
    end_minutes = kz_end[0] * 60 + kz_end[1]
    candle_minutes = h * 60 + m
    return start_minutes <= candle_minutes <= end_minutes


def _check_ob_retest_preconditions(mso, raw_data: dict, kz_name: str) -> dict:
    """Check ob_retest mechanical preconditions from a single MSO snapshot.

    Uses the actual M15 candle from raw_data for price-at-OB detection
    (not the entire M15 swing history from lookback).

    Returns a dict with boolean flags for each condition.
    """
    tfs = mso.timeframes

    h1 = tfs.get("H1")
    m15 = tfs.get("M15")

    result = {
        "kz": kz_name,
        "h1_has_structural_break": False,
        "h1_structure_events": [],
        "h1_unmitigated_obs": [],
        "price_at_ob": False,
        "price_at_ob_details": [],
        "m15_structural_activity": False,
        "m15_structure_events": [],
        "all_preconditions_met": False,
    }

    if not h1 or not m15:
        return result

    # Condition 1: H1 structural break exists
    h1_events = h1.structure_events
    if h1_events:
        result["h1_has_structural_break"] = True
        result["h1_structure_events"] = [
            {
                "type": e.type,
                "direction": e.direction,
                "level": e.level_broken,
                "time": e.time,
                "displacement": e.displacement_present,
            }
            for e in h1_events
        ]

    # Condition 2: Unmitigated H1 OBs exist
    h1_obs = [ob for ob in h1.order_blocks if not ob.mitigated]
    if h1_obs:
        result["h1_unmitigated_obs"] = [
            {
                "type": ob.type,
                "high": ob.high,
                "low": ob.low,
                "formation_time": ob.formation_time,
                "causing_event": ob.causing_event_type,
            }
            for ob in h1_obs
        ]

    # Condition 3: Price reaches OB zone during KZ
    # Use the CURRENT M15 candle from raw_data (the candle that just closed)
    # This is the actual candle at this timestamp, not swings from lookback
    current_candle_time = raw_data.get("timestamp_utc", "")
    m15_candles = raw_data.get("candles", {}).get("M15", [])
    current_candle = None
    if m15_candles:
        # The last M15 candle in raw_data is the current one
        current_candle = m15_candles[-1]

    if current_candle:
        candle_high = current_candle["high"]
        candle_low = current_candle["low"]

        for ob in h1_obs:
            # For bullish OB: candle low must dip INTO the OB zone [ob.low, ob.high]
            if ob.type == "bullish":
                if candle_low <= ob.high and candle_high >= ob.low:
                    result["price_at_ob"] = True
                    result["price_at_ob_details"].append({
                        "ob_type": ob.type,
                        "ob_range": f"{ob.low:.2f}-{ob.high:.2f}",
                        "candle_low": f"{candle_low:.2f}",
                        "candle_high": f"{candle_high:.2f}",
                    })
            # For bearish OB: candle high must reach INTO the OB zone
            elif ob.type == "bearish":
                if candle_high >= ob.low and candle_low <= ob.high:
                    result["price_at_ob"] = True
                    result["price_at_ob_details"].append({
                        "ob_type": ob.type,
                        "ob_range": f"{ob.low:.2f}-{ob.high:.2f}",
                        "candle_low": f"{candle_low:.2f}",
                        "candle_high": f"{candle_high:.2f}",
                    })

    # Condition 4 (supplementary): M15 structural activity
    m15_events = m15.structure_events
    if m15_events:
        result["m15_structural_activity"] = True
        result["m15_structure_events"] = [
            {"type": e.type, "direction": e.direction, "time": e.time}
            for e in m15_events
        ]

    # All preconditions met if conditions 1-3 are true
    result["all_preconditions_met"] = (
        result["h1_has_structural_break"]
        and len(result["h1_unmitigated_obs"]) > 0
        and result["price_at_ob"]
    )

    return result


def analyze_killed_date(
    date_str: str,
    all_candles: dict[str, list[dict]],
    config: dict,
) -> dict:
    """Analyze a single killed date for ob_retest preconditions.

    Iterates through all M15 candles in both KZ windows,
    builds MSO at each candle, and checks preconditions.
    """
    result = {
        "date": date_str,
        "london_kz": {"any_preconditions_met": False, "best_snapshot": None, "candles_checked": 0},
        "ny_kz": {"any_preconditions_met": False, "best_snapshot": None, "candles_checked": 0},
        "classification": "CORRECT_KILL",
        "h1_direction": None,
    }

    # --- London KZ ---
    try:
        london_best = None
        london_count = 0
        for raw_data in replay_london_open(date_str, all_candles):
            london_count += 1
            mso = compute_market_state(raw_data, config)
            check = _check_ob_retest_preconditions(mso, raw_data, "london")

            # Track H1 direction from the MSO
            h1 = mso.timeframes.get("H1")
            if h1:
                result["h1_direction"] = h1.structure.direction

            if check["all_preconditions_met"]:
                result["london_kz"]["any_preconditions_met"] = True
                if london_best is None:
                    london_best = check
            elif not london_best and (check["h1_has_structural_break"] or check["price_at_ob"]):
                london_best = check  # best partial match

        result["london_kz"]["candles_checked"] = london_count
        result["london_kz"]["best_snapshot"] = london_best
    except Exception as e:
        logger.debug("London replay failed for %s: %s", date_str, e)

    # --- NY KZ ---
    try:
        ny_best = None
        ny_count = 0
        for raw_data in replay_ny_open(date_str, all_candles):
            ny_count += 1
            mso = compute_market_state(raw_data, config)
            check = _check_ob_retest_preconditions(mso, raw_data, "ny")

            h1 = mso.timeframes.get("H1")
            if h1:
                result["h1_direction"] = h1.structure.direction

            if check["all_preconditions_met"]:
                result["ny_kz"]["any_preconditions_met"] = True
                if ny_best is None:
                    ny_best = check
            elif not ny_best and (check["h1_has_structural_break"] or check["price_at_ob"]):
                ny_best = check

        result["ny_kz"]["candles_checked"] = ny_count
        result["ny_kz"]["best_snapshot"] = ny_best
    except Exception as e:
        logger.debug("NY replay failed for %s: %s", date_str, e)

    # --- Classification ---
    london_met = result["london_kz"]["any_preconditions_met"]
    ny_met = result["ny_kz"]["any_preconditions_met"]

    if london_met or ny_met:
        result["classification"] = "POTENTIAL_MISS"
    else:
        # Check for MARGINAL: partial conditions in either KZ
        london_snap = result["london_kz"]["best_snapshot"]
        ny_snap = result["ny_kz"]["best_snapshot"]
        has_partial = False
        if london_snap and (london_snap["h1_has_structural_break"] or london_snap["price_at_ob"]):
            has_partial = True
        if ny_snap and (ny_snap["h1_has_structural_break"] or ny_snap["price_at_ob"]):
            has_partial = True
        if has_partial:
            result["classification"] = "MARGINAL"

    return result


# ═══════════════════════════════════════════════════════════════════════
# Step 5-7: Generate outputs
# ═══════════════════════════════════════════════════════════════════════

def write_killed_dates_csv(killed_dates: list[dict], output_path: Path):
    """Write killed dates to CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "kill_reason", "d1_direction", "h4_direction"])
        writer.writeheader()
        writer.writerows(killed_dates)
    logger.info("Wrote %d killed dates to %s", len(killed_dates), output_path)


def write_details_json(details: list[dict], output_path: Path):
    """Write per-date analysis details to JSON."""
    # Convert any non-serializable objects
    with open(output_path, "w") as f:
        json.dump(details, f, indent=2, default=str)
    logger.info("Wrote %d date details to %s", len(details), output_path)


def generate_report(
    killed_dates: list[dict],
    details: list[dict],
    output_path: Path,
):
    """Generate the final markdown report."""
    total = len(killed_dates)

    # Kill reason breakdown
    reason_counter = Counter()
    for kd in killed_dates:
        r = kd["kill_reason"]
        if r.startswith("L1_"):
            reason_counter["D1 not clear (L1)"] += 1
        elif "conflict" in r:
            reason_counter["H4 conflicts with D1 (L2)"] += 1
        elif r.startswith("L2_"):
            reason_counter["H4 not clear (L2)"] += 1
        else:
            reason_counter["Other"] += 1

    # Classification counts
    class_counter = Counter(d["classification"] for d in details)
    correct = class_counter.get("CORRECT_KILL", 0)
    potential = class_counter.get("POTENTIAL_MISS", 0)
    marginal = class_counter.get("MARGINAL", 0)

    potential_pct = (potential / total * 100) if total > 0 else 0
    correct_pct = (correct / total * 100) if total > 0 else 0
    marginal_pct = (marginal / total * 100) if total > 0 else 0

    # POTENTIAL_MISS details
    pm_details = [d for d in details if d["classification"] == "POTENTIAL_MISS"]

    # Monthly distribution
    monthly_dist: dict[str, int] = defaultdict(int)
    for d in pm_details:
        month = d["date"][:7]
        monthly_dist[month] += 1

    # D1 state distribution for POTENTIAL_MISS
    pm_d1_states = Counter()
    for d in pm_details:
        # Find the killed_dates entry for this date
        kd = next((k for k in killed_dates if k["date"] == d["date"]), None)
        if kd:
            pm_d1_states[kd["d1_direction"]] += 1

    # KZ breakdown for POTENTIAL_MISS
    london_only = sum(1 for d in pm_details if d["london_kz"]["any_preconditions_met"] and not d["ny_kz"]["any_preconditions_met"])
    ny_only = sum(1 for d in pm_details if d["ny_kz"]["any_preconditions_met"] and not d["london_kz"]["any_preconditions_met"])
    both_kz = sum(1 for d in pm_details if d["london_kz"]["any_preconditions_met"] and d["ny_kz"]["any_preconditions_met"])

    lines = []
    lines.append("## Pre-Screen Loosening Investigation Results\n")
    lines.append(f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n")

    lines.append("### Summary\n")
    lines.append(f"- **Total killed dates:** {total}")
    lines.append(f"- Kill reason breakdown:")
    for reason, count in sorted(reason_counter.items(), key=lambda x: -x[1]):
        lines.append(f"  - {reason}: {count}")
    lines.append(f"- **CORRECT_KILL:** {correct} ({correct_pct:.1f}%)")
    lines.append(f"- **POTENTIAL_MISS:** {potential} ({potential_pct:.1f}%)")
    lines.append(f"- **MARGINAL:** {marginal} ({marginal_pct:.1f}%)\n")

    # Key finding
    lines.append("### Key Finding\n")
    if potential_pct < 10:
        lines.append(f"The pre-screen is well-calibrated. Only {potential_pct:.1f}% of killed dates "
                      "had ob_retest preconditions present. No change recommended.\n")
    elif potential_pct < 20:
        lines.append(f"**Moderate opportunity detected.** {potential_pct:.1f}% of killed dates "
                      "had ob_retest preconditions. Consider adding a targeted override rule.\n")
    else:
        lines.append(f"**Pre-screen is too aggressive.** {potential_pct:.1f}% of killed dates "
                      "had tradeable structure. Significant loosening recommended.\n")

    # POTENTIAL_MISS details table
    if pm_details:
        lines.append("### POTENTIAL_MISS Date Details\n")
        lines.append("| Date | D1 State | H4 State | H1 Direction | Kill Reason | KZ with Preconditions | H1 Events | Unmitigated OBs |")
        lines.append("|------|----------|----------|--------------|-------------|----------------------|-----------|-----------------|")

        for d in pm_details:
            kd = next((k for k in killed_dates if k["date"] == d["date"]), None)
            d1_st = kd["d1_direction"] if kd else "?"
            h4_st = kd["h4_direction"] if kd else "?"
            h1_dir = d.get("h1_direction", "?")
            kill_r = kd["kill_reason"] if kd else "?"

            kz_list = []
            if d["london_kz"]["any_preconditions_met"]:
                kz_list.append("London")
            if d["ny_kz"]["any_preconditions_met"]:
                kz_list.append("NY")
            kz_str = ", ".join(kz_list) if kz_list else "None"

            # Count H1 events from best snapshot
            h1_ev_count = 0
            ob_count = 0
            for kz_key in ("london_kz", "ny_kz"):
                snap = d[kz_key].get("best_snapshot")
                if snap:
                    h1_ev_count += len(snap.get("h1_structure_events", []))
                    ob_count += len(snap.get("h1_unmitigated_obs", []))

            lines.append(f"| {d['date']} | {d1_st} | {h4_st} | {h1_dir} | {kill_r} | {kz_str} | {h1_ev_count} | {ob_count} |")

        lines.append("")

    # D1 state analysis for POTENTIAL_MISS
    if pm_d1_states:
        lines.append("### D1 State Distribution (POTENTIAL_MISS dates)\n")
        for state, count in sorted(pm_d1_states.items(), key=lambda x: -x[1]):
            lines.append(f"- {state}: {count} dates")
        lines.append("")

    # KZ breakdown
    if pm_details:
        lines.append("### Kill Zone Breakdown (POTENTIAL_MISS)\n")
        lines.append(f"- London only: {london_only}")
        lines.append(f"- NY only: {ny_only}")
        lines.append(f"- Both KZs: {both_kz}")
        lines.append("")

    # Monthly distribution
    if monthly_dist:
        lines.append("### Monthly Distribution of POTENTIAL_MISS Dates\n")
        lines.append("| Month | Count |")
        lines.append("|-------|-------|")
        for month in sorted(monthly_dist.keys()):
            lines.append(f"| {month} | {monthly_dist[month]} |")
        lines.append("")

    # Recommended action
    lines.append("### Recommended Action\n")
    if potential_pct < 10:
        lines.append("**No change needed.** The pre-screen is correctly filtering out dates "
                      "without tradeable structure. The API cost savings justify the current approach.\n")
    elif potential_pct < 20:
        lines.append('**Consider adding a "D1 transitional but H4 clear" override.**\n')
        lines.append("Proposed rule: Allow D1 transitional IF:")
        lines.append("- H4 has clear bullish or bearish direction")
        lines.append("- H1 has at least one confirmed BOS in H4's direction\n")
        est_additional = potential
        est_cost = est_additional * 20 * 0.15  # ~20 candles/session × $0.15
        lines.append(f"This would have allowed ~{est_additional} additional dates through.")
        lines.append(f"Estimated A/B test cost: ~${est_cost:.2f} ({est_additional} sessions × ~20 candles × $0.15)\n")
    else:
        lines.append("**Pre-screen is too aggressive. Significant loosening recommended.**\n")
        lines.append("Proposed tiered loosening:")
        lines.append("1. **Tier 1:** Allow D1 transitional IF H4 is clear AND H1 has BOS in H4's direction")
        lines.append("2. **Tier 2:** Allow D1 transitional IF H1 has 2+ aligned BOS events (strong intraday trend)\n")
        est_additional = potential
        est_cost = est_additional * 20 * 0.15
        lines.append(f"This would have allowed ~{est_additional} additional dates through.")
        lines.append(f"Estimated A/B test cost: ~${est_cost:.2f}\n")

    # MARGINAL analysis
    if marginal > 0:
        lines.append("### MARGINAL Date Analysis\n")
        marginal_details = [d for d in details if d["classification"] == "MARGINAL"]
        has_break_count = 0
        has_ob_count = 0
        for d in marginal_details:
            for kz_key in ("london_kz", "ny_kz"):
                snap = d[kz_key].get("best_snapshot")
                if snap:
                    if snap.get("h1_has_structural_break"):
                        has_break_count += 1
                    if snap.get("h1_unmitigated_obs"):
                        has_ob_count += 1
        lines.append(f"- {marginal} dates with partial conditions")
        lines.append(f"- H1 structural break present: {has_break_count} snapshots")
        lines.append(f"- Unmitigated H1 OBs present: {has_ob_count} snapshots")
        lines.append("- These dates had some structure but price didn't reach the OB zone during KZ,")
        lines.append("  or OBs existed without a prior structural break.\n")

    report = "\n".join(lines)
    output_path.write_text(report, encoding="utf-8")
    logger.info("Report written to %s", output_path)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Analyze pre-screened-out dates")
    parser.add_argument("--start", default="2024-04-01", help="Start date (ISO)")
    parser.add_argument("--end", default="2026-03-13", help="End date (ISO)")
    args = parser.parse_args()

    ANALYSIS_DIR.mkdir(exist_ok=True)

    logger.info("Loading config and historical data...")
    config = load_config()
    all_candles = load_all_candles()

    # Step 2: Collect killed dates
    logger.info("Scanning for pre-screened-out dates: %s to %s", args.start, args.end)
    killed_dates = collect_killed_dates(args.start, args.end, all_candles, config)

    csv_path = ANALYSIS_DIR / "prescreen_killed_dates.csv"
    write_killed_dates_csv(killed_dates, csv_path)

    # Step 3-5: Analyze each killed date
    logger.info("Analyzing %d killed dates for ob_retest preconditions...", len(killed_dates))
    details = []
    for i, kd in enumerate(killed_dates):
        if (i + 1) % 10 == 0 or i == 0:
            logger.info("  Processing %d/%d: %s", i + 1, len(killed_dates), kd["date"])
        detail = analyze_killed_date(kd["date"], all_candles, config)
        detail["kill_reason"] = kd["kill_reason"]
        detail["d1_direction"] = kd["d1_direction"]
        detail["h4_direction"] = kd["h4_direction"]
        details.append(detail)

    # Write details JSON
    details_path = ANALYSIS_DIR / "prescreen_kill_details.json"
    write_details_json(details, details_path)

    # Step 6-7: Generate report
    report_path = ANALYSIS_DIR / "prescreen_loosening_report.md"
    generate_report(killed_dates, details, report_path)

    # Print summary
    class_counter = Counter(d["classification"] for d in details)
    print("\n" + "=" * 60)
    print("PRE-SCREEN LOOSENING INVESTIGATION COMPLETE")
    print("=" * 60)
    print(f"  Total killed dates analyzed: {len(killed_dates)}")
    print(f"  CORRECT_KILL:   {class_counter.get('CORRECT_KILL', 0)}")
    print(f"  POTENTIAL_MISS: {class_counter.get('POTENTIAL_MISS', 0)}")
    print(f"  MARGINAL:       {class_counter.get('MARGINAL', 0)}")
    print(f"\nOutputs:")
    print(f"  {csv_path}")
    print(f"  {details_path}")
    print(f"  {report_path}")


if __name__ == "__main__":
    main()

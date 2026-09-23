"""
Section 1: Extract REJECTED candidates and NO_TRADE candles from all backtest data sources.

Sources:
  - phase1_full_extraction/merged_data.jsonl  (XAUUSD + USDJPY, 1142 rows, with rich features)
  - instrument_expansion_2026-04-25/tier2_<inst>/s*/all_results.json  (5 instruments x 7 slices)

Output:
  rejected_rows.jsonl  - all NO_TRADE + REJECTED_L2 rows with normalized fields
  candidate_rows.jsonl - all CANDIDATE rows (for context)
"""
import json
import os
from pathlib import Path

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_phase1():
    """Load phase1 merged_data.jsonl rows."""
    rows = []
    with open(ROOT / "research/phase1_full_extraction/merged_data.jsonl", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                row["_source"] = "phase1"
                row["_instrument"] = row["symbol"]
                row["_slice"] = row["slice"]
                rows.append(row)
    return rows


def load_tier2():
    """Load all tier2 slice rows."""
    rows = []
    base = ROOT / "research/instrument_expansion_2026-04-25"
    for inst_dir in sorted(base.iterdir()):
        if not inst_dir.is_dir() or not inst_dir.name.startswith("tier2_"):
            continue
        inst_name = inst_dir.name.replace("tier2_", "").upper()
        for slice_dir in sorted(inst_dir.iterdir()):
            if not slice_dir.is_dir():
                continue
            results_file = slice_dir / "all_results.json"
            if not results_file.exists():
                continue
            with open(results_file, "r") as f:
                data = json.load(f)
            for row in data.get("results", []):
                row["_source"] = "tier2"
                row["_instrument"] = inst_name
                row["_slice"] = f"{inst_name.lower()}_{slice_dir.name}"
                row["_slice_start"] = data.get("start")
                row["_slice_end"] = data.get("end")
                rows.append(row)
    return rows


def normalize_row(row):
    """Common fields for downstream forward-resolution + bucketization.

    Some fields appear in phase1 with different names than tier2.
    """
    src = row.get("_source")
    inst = row.get("_instrument")
    if src == "phase1":
        out = {
            "_source": src,
            "_instrument": inst,
            "_slice": row.get("_slice"),
            "timestamp_utc": row.get("timestamp_utc"),
            "kill_zone": row.get("kill_zone"),
            "decision": row.get("out_decision"),
            "no_trade_reason": row.get("out_no_trade_reason") or row.get("ai_no_trade_reason"),
            "ai_decision": row.get("ai_decision"),
            "ai_no_trade_reason": row.get("ai_no_trade_reason"),
            "ai_direction_evaluated": row.get("ai_direction_evaluated"),
            "logger_decision": row.get("logger_decision"),
            "logger_framework": row.get("logger_framework"),
            "logger_setup_grade": row.get("logger_setup_grade"),
            "out_direction": row.get("out_direction"),
            "out_outcome": row.get("out_outcome"),
            "out_r_multiple": row.get("out_r_multiple"),
            "out_l2_passed": row.get("out_l2_passed"),
            "out_setup_grade": row.get("out_setup_grade"),
            "out_prescreen": row.get("out_prescreen"),
            "out_bias": row.get("out_bias"),
            "h1_direction": row.get("mso_h1_structure_direction") or row.get("out_bias"),
            # phase1 doesn't expose entry/SL/TP/raw_response (merged data dropped that)
            # but it has rich features
            "h1_opp_ob_touch": row.get("h1_opp_ob_touch"),
            "h1_opp_ob_touch_long": row.get("h1_opp_ob_touch_long"),
            "h1_opp_ob_touch_short": row.get("h1_opp_ob_touch_short"),
            "h1_fvg_unfilled_count": row.get("h1_fvg_unfilled_count"),
            "m15_fvg_unfilled_count": row.get("m15_fvg_unfilled_count"),
            "mso_h1_unmitigated_ob_count": row.get("mso_h1_unmitigated_ob_count"),
            "mso_h1_nearest_ob_distance_atr": row.get("mso_h1_nearest_ob_distance_atr"),
            "mso_detected_sweeps_count": row.get("mso_detected_sweeps_count"),
            "mso_m15_clv_current": row.get("mso_m15_clv_current"),
            "mso_m15_clv_avg_5": row.get("mso_m15_clv_avg_5"),
            "mso_m15_bvc_buy_fraction": row.get("mso_m15_bvc_buy_fraction"),
            "pre_ai_gate_skipped": row.get("pre_ai_gate_skipped"),
            "pre_ai_gate_reason": row.get("pre_ai_gate_reason"),
            "detector_version_at_eval": row.get("detector_version_at_eval"),
            "raw_response": None,  # not available
            "entry_price": None,
            "stop_loss": None,
            "take_profit_1": None,
            "l2_reason": row.get("l2_reason"),  # likely None in phase1 merged
            "candle_close": None,
        }
    else:
        # tier2
        out = {
            "_source": src,
            "_instrument": inst,
            "_slice": row.get("_slice"),
            "timestamp_utc": row.get("candle_time"),
            "kill_zone": row.get("kill_zone"),
            "decision": row.get("decision"),
            "no_trade_reason": row.get("no_trade_reason"),
            "h1_direction": row.get("h1_direction") or row.get("bias"),
            "out_direction": row.get("direction"),
            "entry_price": row.get("entry_price"),
            "stop_loss": row.get("stop_loss"),
            "take_profit_1": row.get("take_profit_1"),
            "raw_response": row.get("raw_response"),
            "l2_reason": row.get("l2_reason"),
            "out_l2_passed": row.get("l2_passed"),
            "out_outcome": row.get("outcome"),
            "out_r_multiple": row.get("r_multiple"),
            "out_setup_grade": row.get("setup_grade"),
            "out_prescreen": row.get("prescreen"),
            "out_bias": row.get("bias"),
            "candle_close": row.get("candle_close"),
            "logger_setup_grade": row.get("setup_grade"),
            "ai_decision": row.get("decision"),  # tier2 doesn't separate logger vs AI
            "ai_direction_evaluated": row.get("direction"),
            "ai_no_trade_reason": row.get("no_trade_reason") if row.get("decision") == "NO_TRADE" else None,
        }
    return out


if __name__ == "__main__":
    p1 = load_phase1()
    t2 = load_tier2()
    print(f"Phase1 rows: {len(p1)}")
    print(f"Tier2 rows:  {len(t2)}")

    all_normalized = [normalize_row(r) for r in p1 + t2]

    # Write rejected (NO_TRADE + REJECTED_L2 + BLOCKED_LIMIT + PARSE_ERROR)
    rejected_decisions = {"NO_TRADE", "REJECTED_L2", "BLOCKED_LIMIT", "PARSE_ERROR"}
    rejected_rows = [r for r in all_normalized if r["decision"] in rejected_decisions]
    candidate_rows = [r for r in all_normalized if r["decision"] == "CANDIDATE"]
    print(f"Rejected total: {len(rejected_rows)}")
    print(f"  NO_TRADE: {sum(1 for r in rejected_rows if r['decision']=='NO_TRADE')}")
    print(f"  REJECTED_L2: {sum(1 for r in rejected_rows if r['decision']=='REJECTED_L2')}")
    print(f"  BLOCKED_LIMIT: {sum(1 for r in rejected_rows if r['decision']=='BLOCKED_LIMIT')}")
    print(f"  PARSE_ERROR: {sum(1 for r in rejected_rows if r['decision']=='PARSE_ERROR')}")
    print(f"Candidates: {len(candidate_rows)}")

    with open(OUT_DIR / "rejected_rows.jsonl", "w") as f:
        for r in rejected_rows:
            f.write(json.dumps(r, default=str) + "\n")
    with open(OUT_DIR / "candidate_rows.jsonl", "w") as f:
        for r in candidate_rows:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Wrote {OUT_DIR / 'rejected_rows.jsonl'}")
    print(f"Wrote {OUT_DIR / 'candidate_rows.jsonl'}")

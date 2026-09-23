"""Merge all per-E* JSONs into a single extraction_output.json for machine consumers."""
import json
from pathlib import Path

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\phase1_full_extraction")

with open(OUT_DIR / "extraction_output.json") as f:
    main = json.load(f)
with open(OUT_DIR / "e9_output.json") as f:
    e9 = json.load(f)
with open(OUT_DIR / "e11_combined.json") as f:
    e11 = json.load(f)
with open(OUT_DIR / "e_extras.json") as f:
    ex = json.load(f)

consolidated = {
    "schema_version": "1.0",
    "generated_ts_utc": "2026-04-25",
    "meta": main.get("meta"),
    "joined_rows_matched": main.get("joined_rows_matched"),
    "E1_touch_strata": main["E1_touch"],
    "E2_fvg_strata": main["E2_fvg"],
    "E3_direction_breakdown": main["E3_direction"],
    "E4_short_share_diff": main["E4_short_share_diff"],
    "E4_diagnosis_additional": ex["e4_diagnosis"],
    "E5_pre_ai_gate_reasons": main["E5_pre_ai_gate_reasons"],
    "E6_per_instrument": main["E6_per_instrument"],
    "E7_per_slice_regime": main["E7_per_slice_regime"],
    "E8_c_gate_vs_l2": main["E8_c_gate_vs_l2"],
    "E9_anti_pattern_oos": e9,
    "E10_setup_grade_outcome": main["E10_setup_grade"],
    "E11_kz_bucket_a1_only": main["E11_kz_buckets"],
    "E11_kz_bucket_combined": e11,
    "E12_logger_verification": ex["e12_logger_verification"],
    "bonus_monthly_decay": ex["monthly_decay"],
}

with open(OUT_DIR / "extraction_output_consolidated.json", "w") as f:
    json.dump(consolidated, f, indent=2, default=str)
print("Wrote extraction_output_consolidated.json")

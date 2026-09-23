#!/usr/bin/env python3
"""Verify the market-expansion validation scoring route artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FILES = {
    "SCORING_INPUT_FREEZE_MANIFEST.json",
    "FROZEN_INPUT_MANIFEST.json",
    "RAW_EVENT_EXPORT_MANIFEST.json",
    "SYMBOL_TIMEFRAME_ELIGIBILITY_LEDGER.jsonl",
    "SOURCE_HASH_LEDGER.jsonl",
    "REPLAY_PACKET_LEDGER.jsonl",
    "EVENT_SCORE_LEDGER.jsonl",
    "CANDIDATE_MECHANISM_SCORE_LEDGER.jsonl",
    "CANDIDATE_RESULT_LEDGER.jsonl",
    "FAMILY_SCORE_LEDGER.jsonl",
    "COST_STRESS_AUDIT.json",
    "SPLIT_STABILITY_LEDGER.jsonl",
    "NULL_PLACEBO_LEDGER.jsonl",
    "CONCENTRATION_AUDIT.json",
    "CONCENTRATION_STRESS_AUDIT.json",
    "DECISION_LEDGER.jsonl",
    "FULL_BOOK_MC_INTERACTION_LEDGER.jsonl",
    "INSPIRE_NOT_KILL_LEDGER.jsonl",
    "MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json",
    "REPAIR_LEDGER.json",
    "SATURATION_AUDIT.json",
    "COMPLETION_AUDIT.json",
    "FOCUSED_TEST_RESULT.json",
    "OUTPUT_MANIFEST.json",
    "NEXT_PROMPT.md",
}
EXCLUDED_SYMBOLS = {"SPCX", "NATGAS_cash", "HEATOIL_c"}


def load_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    path = ROUTE / name
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    issues: list[dict[str, Any]] = []
    missing = sorted(name for name in REQUIRED_FILES if not (ROUTE / name).exists())
    if missing:
        issues.append({"code": "missing_required_files", "files": missing})

    result = load_json("MARKET_EXPANSION_VALIDATION_SCORING_RESULT.json")
    input_manifest = load_json("SCORING_INPUT_FREEZE_MANIFEST.json")
    raw_manifest = load_json("RAW_EVENT_EXPORT_MANIFEST.json")
    eligibility_rows = load_jsonl("SYMBOL_TIMEFRAME_ELIGIBILITY_LEDGER.jsonl")
    source_rows = load_jsonl("SOURCE_HASH_LEDGER.jsonl")
    event_rows = load_jsonl("EVENT_SCORE_LEDGER.jsonl")
    replay_rows = load_jsonl("REPLAY_PACKET_LEDGER.jsonl")
    candidate_rows = load_jsonl("CANDIDATE_RESULT_LEDGER.jsonl")
    candidate_alias_rows = load_jsonl("CANDIDATE_MECHANISM_SCORE_LEDGER.jsonl")
    family_rows = load_jsonl("FAMILY_SCORE_LEDGER.jsonl")
    split_rows = load_jsonl("SPLIT_STABILITY_LEDGER.jsonl")
    placebo_rows = load_jsonl("NULL_PLACEBO_LEDGER.jsonl")
    full_book_rows = load_jsonl("FULL_BOOK_MC_INTERACTION_LEDGER.jsonl")
    inspire_rows = load_jsonl("INSPIRE_NOT_KILL_LEDGER.jsonl")
    decision_rows = load_jsonl("DECISION_LEDGER.jsonl")
    concentration = load_json("CONCENTRATION_STRESS_AUDIT.json")
    cost_audit = load_json("COST_STRESS_AUDIT.json")
    repair = load_json("REPAIR_LEDGER.json")
    saturation = load_json("SATURATION_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")
    manifest = load_json("OUTPUT_MANIFEST.json")
    next_prompt = (ROUTE / "NEXT_PROMPT.md").read_text(encoding="utf-8")

    if result.get("ok") is not True:
        issues.append({"code": "result_not_ok"})
    if result.get("availability_coverage_gap_count") != 0:
        issues.append({"code": "availability_gap_not_zero", "value": result.get("availability_coverage_gap_count")})
    if result.get("priority_symbol_count") != 167:
        issues.append({"code": "priority_symbol_count_changed", "value": result.get("priority_symbol_count")})
    if result.get("scoring_eligible_symbol_count") != 164 or result.get("scoring_excluded_symbol_count") != 3:
        issues.append(
            {
                "code": "scoring_denominator_mismatch",
                "eligible": result.get("scoring_eligible_symbol_count"),
                "excluded": result.get("scoring_excluded_symbol_count"),
            }
        )
    raw_path = PROJECT_ROOT / raw_manifest.get("path", "")
    if raw_manifest.get("row_count") != result.get("event_count") or raw_manifest.get("row_count", 0) <= 100_000:
        issues.append(
            {
                "code": "raw_event_manifest_count_mismatch",
                "manifest_row_count": raw_manifest.get("row_count"),
                "result_event_count": result.get("event_count"),
            }
        )
    if not raw_manifest.get("path", "").startswith("data/mt5_research_exports/") or not raw_path.exists():
        issues.append({"code": "raw_event_export_missing_or_wrong_root", "path": raw_manifest.get("path")})
    if not raw_manifest.get("sha256") or len(raw_manifest.get("sha256", "")) != 64:
        issues.append({"code": "raw_event_export_sha_missing"})
    if result.get("event_count") != raw_manifest.get("row_count") or len(replay_rows) != len(event_rows):
        issues.append({"code": "event_replay_count_mismatch"})
    if result.get("candidate_result_count") != len(candidate_rows) or len(candidate_alias_rows) != len(candidate_rows):
        issues.append({"code": "candidate_count_mismatch"})
    if len(event_rows) != len(candidate_rows) or len(replay_rows) != len(candidate_rows):
        issues.append({"code": "compact_event_packet_count_mismatch"})
    if any(row.get("raw_event_export_sha256") != raw_manifest.get("sha256") for row in event_rows):
        issues.append({"code": "compact_event_packet_raw_hash_mismatch"})
    if result.get("family_result_count") != len(family_rows):
        issues.append({"code": "family_count_mismatch"})
    if len(split_rows) != len(candidate_rows) or len(placebo_rows) != len(candidate_rows):
        issues.append({"code": "split_or_placebo_count_mismatch"})

    excluded = {row["file_symbol"] for row in eligibility_rows if not row.get("scoring_eligible")}
    if excluded != EXCLUDED_SYMBOLS:
        issues.append({"code": "excluded_symbols_mismatch", "excluded": sorted(excluded)})
    bad_excluded_scores = sorted(EXCLUDED_SYMBOLS & {row.get("file_symbol") for row in candidate_rows})
    if bad_excluded_scores:
        issues.append({"code": "excluded_symbols_scored", "symbols": bad_excluded_scores})

    promoted = [row for row in candidate_rows if row.get("first_pass_promoted_for_followup")]
    if result.get("first_pass_promoted_for_followup_count") != len(promoted):
        issues.append({"code": "promoted_count_mismatch"})
    bad_promotions = [
        row.get("file_symbol")
        for row in promoted
        if row.get("family") == "single_stock_cfd"
        or row.get("summary", {}).get("populated_split_count", 0) < 2
        or row.get("summary", {}).get("every_populated_split_positive") is not True
        or row.get("placebo", {}).get("placebo_p_ge_observed") is not None
        and row.get("placebo", {}).get("placebo_p_ge_observed") > 0.25
    ]
    if bad_promotions:
        issues.append({"code": "bad_promotion_gate", "symbols": bad_promotions[:20]})

    for forbidden_key in ("orderflow_used", "broker_or_order_mutation", "config_or_live_activation_changed", "vps_process_touched", "live_authority"):
        expected = False
        if result.get(forbidden_key) is not expected:
            issues.append({"code": f"{forbidden_key}_boundary_broken", "value": result.get(forbidden_key)})
    if completion.get("runtime_effect") != "none_research_scoring_only":
        issues.append({"code": "completion_runtime_effect_changed"})
    if cost_audit.get("ok") is not True or "broker order lifecycle" not in " ".join(cost_audit.get("limitations", [])):
        issues.append({"code": "cost_audit_missing_limitations"})
    if concentration.get("hard_drops_not_scored") is not True or concentration.get("spcx_quarantine_not_scored") is not True:
        issues.append({"code": "concentration_exclusion_flags_false"})
    if not full_book_rows or full_book_rows[0].get("status") != "not_computed_in_this_route":
        issues.append({"code": "full_book_mc_boundary_missing"})
    if not inspire_rows or any(row.get("not_killed") is not True for row in inspire_rows):
        issues.append({"code": "inspire_not_kill_missing"})
    if not decision_rows or not any(row.get("decision") == result.get("decision") for row in decision_rows):
        issues.append({"code": "decision_ledger_missing_terminal_decision"})
    if repair.get("ok") is not True or repair.get("blockers"):
        issues.append({"code": "repair_ledger_not_clean"})
    if saturation.get("ok") is not True or saturation.get("no_arbitrary_top_n") is not True:
        issues.append({"code": "saturation_audit_not_clean"})
    if not source_rows or not any(row.get("source_used_for_scoring") for row in source_rows):
        issues.append({"code": "source_hash_rows_missing_scoring_sources"})
    if input_manifest.get("scoring_eligible_symbol_count") != result.get("scoring_eligible_symbol_count"):
        issues.append({"code": "input_manifest_denominator_mismatch"})
    for required_text in ("not live authority", "Do not use orderflow/depth", "no arbitrary top-N", "full-book"):
        if required_text not in next_prompt:
            issues.append({"code": "next_prompt_missing_text", "text": required_text})

    manifest_files = set(manifest.get("files") or [])
    missing_manifest = sorted(REQUIRED_FILES - manifest_files - {"OUTPUT_MANIFEST.json"})
    if missing_manifest:
        issues.append({"code": "manifest_missing_files", "files": missing_manifest})

    verification = {
        "schema": "gtos.final_moonshot.market_expansion_validation_scoring.verification.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "decision": result.get("decision"),
        "event_count": result.get("event_count"),
        "candidate_result_count": result.get("candidate_result_count"),
        "first_pass_promoted_for_followup_count": result.get("first_pass_promoted_for_followup_count"),
        "scoring_eligible_symbol_count": result.get("scoring_eligible_symbol_count"),
        "scoring_excluded_symbol_count": result.get("scoring_excluded_symbol_count"),
    }
    (ROUTE / "MARKET_EXPANSION_VALIDATION_SCORING_VERIFIER_RESULT.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": verification["ok"],
                "issue_count": verification["issue_count"],
                "event_count": verification["event_count"],
                "candidate_result_count": verification["candidate_result_count"],
                "first_pass_promoted_for_followup_count": verification["first_pass_promoted_for_followup_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

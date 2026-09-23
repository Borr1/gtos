#!/usr/bin/env python3
"""Verify the market-expansion G12 review route artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FILES = {
    "G12_INPUT_MANIFEST.json",
    "G12_CANDIDATE_DECISION_LEDGER.jsonl",
    "G12_DEEP_SELECTION_LEDGER.jsonl",
    "G12_ACCEPTED_DEFAULT_OFF_LEDGER.jsonl",
    "G12_EXACT_REPAIR_LEDGER.jsonl",
    "G12_IMPLEMENTATION_HANDOFF_LEDGER.jsonl",
    "INSPIRE_NOT_KILL_LEDGER.jsonl",
    "DECISION_LEDGER.jsonl",
    "FULL_BOOK_INTERACTION_AUDIT.json",
    "CONCENTRATION_NULL_PLACEBO_AUDIT.json",
    "REPAIR_LEDGER.json",
    "SATURATION_AUDIT.json",
    "MARKET_EXPANSION_G12_REVIEW_RESULT.json",
    "COMPLETION_AUDIT.json",
    "FOCUSED_TEST_RESULT.json",
    "OUTPUT_MANIFEST.json",
    "NEXT_PROMPT.md",
    "build_market_expansion_g12_review.py",
    "verify_market_expansion_g12_review.py",
}
EXPECTED_CLASS_COUNTS = {
    "context_only_single_stock_cfd": 290,
    "context_or_negative_proxy": 383,
    "first_pass_promoted": 33,
    "near_miss_positive_proxy": 42,
    "positive_proxy_underpowered_or_unstable": 72,
}
EXPECTED_DECISION_COUNTS = {
    "context_only_single_stock_portfolio_inventory": 290,
    "context_or_veto_inventory": 383,
    "default_off_m1_supported_candidate": 6,
    "default_off_proxy_supported_candidate_requires_m1_repair": 10,
    "exact_repair_or_negative_control_required": 6,
    "successor_experiment_inventory": 72,
    "transformed_context_or_sizing_feature": 53,
}
EXPECTED_ACCEPTED_FAMILY_COUNTS = {
    "crypto_alt_or_major": 3,
    "indices_context": 11,
    "jpy_fx": 2,
}
EXPECTED_ACCEPTED_MECHANISM_COUNTS = {
    "d1_atr_mean_reversion": 4,
    "d1_donchian_20_breakout": 4,
    "d1_volume_surge_reversal": 8,
}
EXCLUDED_SYMBOLS = {"SPCX", "NATGAS_cash", "HEATOIL_c"}
RAW_SHA = "36359117717250ae23a969d397b00fc6309da64c566944a9d15b18a55df2d265"
DEFAULT_OFF_DECISIONS = {
    "default_off_m1_supported_candidate",
    "default_off_proxy_supported_candidate_requires_m1_repair",
}


def load_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    issues: list[dict[str, Any]] = []
    missing = sorted(name for name in REQUIRED_FILES if not (ROUTE / name).exists())
    if missing:
        issues.append({"code": "missing_required_files", "files": missing})

    result = load_json("MARKET_EXPANSION_G12_REVIEW_RESULT.json")
    input_manifest = load_json("G12_INPUT_MANIFEST.json")
    candidate_rows = load_jsonl(ROUTE / "G12_CANDIDATE_DECISION_LEDGER.jsonl")
    deep_rows = load_jsonl(ROUTE / "G12_DEEP_SELECTION_LEDGER.jsonl")
    accepted_rows = load_jsonl(ROUTE / "G12_ACCEPTED_DEFAULT_OFF_LEDGER.jsonl")
    repair_rows = load_jsonl(ROUTE / "G12_EXACT_REPAIR_LEDGER.jsonl")
    implementation_rows = load_jsonl(ROUTE / "G12_IMPLEMENTATION_HANDOFF_LEDGER.jsonl")
    inspire_rows = load_jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl")
    decision_rows = load_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    full_book = load_json("FULL_BOOK_INTERACTION_AUDIT.json")
    concentration = load_json("CONCENTRATION_NULL_PLACEBO_AUDIT.json")
    repair = load_json("REPAIR_LEDGER.json")
    saturation = load_json("SATURATION_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")
    focused = load_json("FOCUSED_TEST_RESULT.json")
    manifest = load_json("OUTPUT_MANIFEST.json")
    next_prompt = (ROUTE / "NEXT_PROMPT.md").read_text(encoding="utf-8")

    class_counts = Counter(row.get("followup_class") for row in candidate_rows)
    decision_counts = Counter(row.get("g12_decision") for row in candidate_rows)
    deep_decision_counts = Counter(row.get("g12_decision") for row in deep_rows)
    accepted_family_counts = Counter(row.get("family") for row in accepted_rows)
    accepted_mechanism_counts = Counter(row.get("mechanism") for row in accepted_rows)

    if result.get("ok") is not True:
        issues.append({"code": "result_not_ok"})
    if result.get("candidate_result_count") != 820 or len(candidate_rows) != 820:
        issues.append({"code": "candidate_count_mismatch", "result": result.get("candidate_result_count"), "ledger": len(candidate_rows)})
    if dict(sorted(class_counts.items())) != EXPECTED_CLASS_COUNTS:
        issues.append({"code": "source_class_counts_changed", "counts": dict(sorted(class_counts.items()))})
    if dict(sorted(decision_counts.items())) != EXPECTED_DECISION_COUNTS:
        issues.append({"code": "g12_decision_counts_changed", "counts": dict(sorted(decision_counts.items()))})
    if len(deep_rows) != 75 or result.get("deep_review_count") != 75:
        issues.append({"code": "deep_review_count_mismatch", "result": result.get("deep_review_count"), "ledger": len(deep_rows)})
    if dict(sorted(deep_decision_counts.items())) != {
        "default_off_m1_supported_candidate": 6,
        "default_off_proxy_supported_candidate_requires_m1_repair": 10,
        "exact_repair_or_negative_control_required": 6,
        "transformed_context_or_sizing_feature": 53,
    }:
        issues.append({"code": "deep_decision_counts_changed", "counts": dict(sorted(deep_decision_counts.items()))})
    if len(accepted_rows) != 16 or result.get("default_off_candidate_count") != 16:
        issues.append({"code": "accepted_count_mismatch", "result": result.get("default_off_candidate_count"), "ledger": len(accepted_rows)})
    if result.get("default_off_m1_supported_count") != 6 or result.get("default_off_proxy_supported_count") != 10:
        issues.append({"code": "default_off_tier_counts_changed"})
    if dict(sorted(accepted_family_counts.items())) != EXPECTED_ACCEPTED_FAMILY_COUNTS:
        issues.append({"code": "accepted_family_counts_changed", "counts": dict(sorted(accepted_family_counts.items()))})
    if dict(sorted(accepted_mechanism_counts.items())) != EXPECTED_ACCEPTED_MECHANISM_COUNTS:
        issues.append({"code": "accepted_mechanism_counts_changed", "counts": dict(sorted(accepted_mechanism_counts.items()))})
    if len(implementation_rows) != len(accepted_rows):
        issues.append({"code": "implementation_handoff_count_mismatch"})
    if len(repair_rows) != 820 or repair.get("repair_row_count") != 820:
        issues.append({"code": "repair_row_count_mismatch", "repair_rows": len(repair_rows), "summary": repair.get("repair_row_count")})
    if len(inspire_rows) != 820 or any(row.get("not_killed") is not True for row in inspire_rows):
        issues.append({"code": "inspire_not_kill_missing_or_false"})
    if any(row.get("not_killed") is not True for row in candidate_rows):
        issues.append({"code": "candidate_not_killed_false"})
    if EXCLUDED_SYMBOLS & {row.get("file_symbol") for row in candidate_rows}:
        issues.append({"code": "excluded_symbols_present", "symbols": sorted(EXCLUDED_SYMBOLS & {row.get("file_symbol") for row in candidate_rows})})

    for row in accepted_rows:
        gates = row.get("gates") or {}
        if row.get("g12_decision") not in DEFAULT_OFF_DECISIONS:
            issues.append({"code": "non_default_off_in_accepted", "row": [row.get("file_symbol"), row.get("mechanism")]})
        for gate in (
            "deep_replay_class",
            "ordered_events_ge_75",
            "ordered_path_coverage_ge_0p95",
            "ordered_mean_ge_0p05",
            "populated_splits_ge_3",
            "every_populated_split_positive",
            "min_split_mean_ge_0p01",
            "median_nonnegative_or_win_rate_ge_0p52",
            "full_book_delta_ge_0p00010",
            "corr_abs_le_0p06",
            "matched_current_book_days_ge_60",
            "ordered_path_ready",
            "source_placebo_pass_or_missing",
        ):
            if gates.get(gate) is not True:
                issues.append({"code": "accepted_row_failed_core_gate", "gate": gate, "row": [row.get("file_symbol"), row.get("mechanism")]})
        if row.get("g12_decision") == "default_off_m1_supported_candidate" and gates.get("exact_m1_events_ge_20") is not True:
            issues.append({"code": "m1_supported_without_exact_m1_gate", "row": [row.get("file_symbol"), row.get("mechanism")]})
        if row.get("g12_decision") == "default_off_proxy_supported_candidate_requires_m1_repair":
            if gates.get("proxy_limited_m15_events_ge_75") is not True or gates.get("proxy_limited_mean_ge_0p10") is not True:
                issues.append({"code": "proxy_supported_without_proxy_gates", "row": [row.get("file_symbol"), row.get("mechanism")]})
            if gates.get("exact_m1_events_ge_20") is True:
                issues.append({"code": "proxy_supported_row_already_m1_supported", "row": [row.get("file_symbol"), row.get("mechanism")]})

    if full_book.get("ok") is not True or full_book.get("row_count") != 75 or full_book.get("computed_count") != 75:
        issues.append({"code": "full_book_audit_count_mismatch"})
    if full_book.get("positive_delta_count") != 60 or full_book.get("negative_delta_count") != 15:
        issues.append({"code": "full_book_delta_counts_changed"})
    if concentration.get("ok") is not True or concentration.get("accepted_count") != 16:
        issues.append({"code": "concentration_audit_not_clean"})
    if concentration.get("accepted_mechanism_budget_warning") is not True:
        issues.append({"code": "expected_concentration_budget_warning_missing"})
    if concentration.get("timing_null", {}).get("random_day_reps") != 200:
        issues.append({"code": "timing_null_reps_changed"})
    if concentration.get("timing_null", {}).get("p_value_summary", {}).get("n") != 75:
        issues.append({"code": "timing_null_p_count_mismatch"})
    if concentration.get("no_arbitrary_top_n") is not True or saturation.get("no_arbitrary_top_n") is not True:
        issues.append({"code": "no_arbitrary_top_n_flag_missing"})
    if saturation.get("ok") is not True or saturation.get("all_candidate_rows_processed") is not True or saturation.get("all_deep_rows_reviewed") is not True:
        issues.append({"code": "saturation_not_clean"})
    if completion.get("ok") is not True or completion.get("runtime_effect") != "none_research_review_only":
        issues.append({"code": "completion_not_clean"})
    if focused.get("ok") is not True:
        issues.append({"code": "focused_test_result_not_ok"})
    if not decision_rows or not any(row.get("decision") == result.get("decision") for row in decision_rows):
        issues.append({"code": "terminal_decision_missing"})

    raw_manifest = input_manifest.get("raw_path_event_manifest") or {}
    raw_path = PROJECT_ROOT / raw_manifest.get("path", "")
    if raw_manifest.get("sha256") != RAW_SHA:
        issues.append({"code": "raw_sha_changed", "value": raw_manifest.get("sha256")})
    if raw_manifest.get("row_count") != 19121:
        issues.append({"code": "raw_row_count_changed", "value": raw_manifest.get("row_count")})
    if not raw_path.exists() or sha256_file(raw_path) != RAW_SHA:
        issues.append({"code": "raw_export_missing_or_sha_mismatch", "path": raw_manifest.get("path")})
    if input_manifest.get("raw_path_event_sha256_verified") is not True:
        issues.append({"code": "input_manifest_raw_sha_not_verified"})

    for forbidden_key in ("orderflow_used", "broker_or_order_mutation", "config_or_live_activation_changed", "vps_process_touched", "live_authority"):
        if result.get(forbidden_key) is not False:
            issues.append({"code": f"{forbidden_key}_boundary_broken", "value": result.get(forbidden_key)})
    if any(row.get("live_authority") is not False for row in implementation_rows):
        issues.append({"code": "implementation_handoff_live_authority_not_false"})

    manifest_files = set(manifest.get("files") or [])
    missing_manifest = sorted(REQUIRED_FILES - manifest_files - {"OUTPUT_MANIFEST.json"})
    if missing_manifest:
        issues.append({"code": "manifest_missing_files", "files": missing_manifest})
    for required_text in (
        "not live authority",
        "Do not use orderflow/depth",
        "no arbitrary top-N",
        "full same-evidence-class pursuit",
        "inspire-not-kill preservation",
        "default-off implementation design",
    ):
        if required_text not in next_prompt:
            issues.append({"code": "next_prompt_missing_text", "text": required_text})

    verification = {
        "schema": "gtos.final_moonshot.market_expansion_g12_review.verification.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "decision": result.get("decision"),
        "candidate_result_count": result.get("candidate_result_count"),
        "deep_review_count": result.get("deep_review_count"),
        "default_off_candidate_count": result.get("default_off_candidate_count"),
        "default_off_m1_supported_count": result.get("default_off_m1_supported_count"),
        "default_off_proxy_supported_count": result.get("default_off_proxy_supported_count"),
        "decision_counts": dict(sorted(decision_counts.items())),
    }
    (ROUTE / "MARKET_EXPANSION_G12_REVIEW_VERIFIER_RESULT.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": verification["ok"],
                "issue_count": verification["issue_count"],
                "candidate_result_count": verification["candidate_result_count"],
                "deep_review_count": verification["deep_review_count"],
                "default_off_candidate_count": verification["default_off_candidate_count"],
                "default_off_m1_supported_count": verification["default_off_m1_supported_count"],
                "default_off_proxy_supported_count": verification["default_off_proxy_supported_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

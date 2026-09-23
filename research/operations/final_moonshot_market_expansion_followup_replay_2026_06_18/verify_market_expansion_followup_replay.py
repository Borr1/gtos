#!/usr/bin/env python3
"""Verify the market-expansion follow-up replay route artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FILES = {
    "FOLLOWUP_INPUT_MANIFEST.json",
    "PATH_REPLAY_EVENT_EXPORT_MANIFEST.json",
    "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl",
    "FAMILY_FOLLOWUP_REPLAY_LEDGER.jsonl",
    "FULL_BOOK_INTERACTION_LEDGER.jsonl",
    "GEOMETRY_STATUS_LEDGER.jsonl",
    "INSPIRE_NOT_KILL_LEDGER.jsonl",
    "DECISION_LEDGER.jsonl",
    "REPAIR_LEDGER.json",
    "SATURATION_AUDIT.json",
    "MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json",
    "COMPLETION_AUDIT.json",
    "FOCUSED_TEST_RESULT.json",
    "OUTPUT_MANIFEST.json",
    "NEXT_PROMPT.md",
    "build_market_expansion_followup_replay.py",
    "verify_market_expansion_followup_replay.py",
}
EXCLUDED_SYMBOLS = {"SPCX", "NATGAS_cash", "HEATOIL_c"}
EXPECTED_CLASS_COUNTS = {
    "context_only_single_stock_cfd": 290,
    "context_or_negative_proxy": 383,
    "first_pass_promoted": 33,
    "near_miss_positive_proxy": 42,
    "positive_proxy_underpowered_or_unstable": 72,
}
M1_SOURCE = "M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH"
M15_SOURCE = "M15_PROXY_PATH_NOT_BROKER_LIFECYCLE_TRUTH"


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

    result = load_json("MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json")
    input_manifest = load_json("FOLLOWUP_INPUT_MANIFEST.json")
    path_manifest = load_json("PATH_REPLAY_EVENT_EXPORT_MANIFEST.json")
    candidate_rows = load_jsonl(ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl")
    family_rows = load_jsonl(ROUTE / "FAMILY_FOLLOWUP_REPLAY_LEDGER.jsonl")
    full_book_rows = load_jsonl(ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl")
    geometry_rows = load_jsonl(ROUTE / "GEOMETRY_STATUS_LEDGER.jsonl")
    inspire_rows = load_jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl")
    decision_rows = load_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repair = load_json("REPAIR_LEDGER.json")
    saturation = load_json("SATURATION_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")
    focused = load_json("FOCUSED_TEST_RESULT.json")
    manifest = load_json("OUTPUT_MANIFEST.json")
    next_prompt = (ROUTE / "NEXT_PROMPT.md").read_text(encoding="utf-8")

    raw_path = PROJECT_ROOT / path_manifest.get("path", "")
    raw_rows = load_jsonl(raw_path)
    class_counts = Counter(row.get("followup_class") for row in candidate_rows)
    deep_rows = [row for row in candidate_rows if row.get("followup_class") in {"first_pass_promoted", "near_miss_positive_proxy"}]
    source_counts = Counter(row.get("target2_path_source") or "none" for row in raw_rows)
    target2_status_counts = Counter(row.get("target2_path_status") for row in raw_rows)
    geometry_counts = Counter(row.get("geometry_status") for row in raw_rows)

    if result.get("ok") is not True:
        issues.append({"code": "result_not_ok"})
    if result.get("candidate_result_count") != 820 or len(candidate_rows) != 820:
        issues.append(
            {
                "code": "candidate_count_mismatch",
                "result": result.get("candidate_result_count"),
                "ledger": len(candidate_rows),
            }
        )
    if dict(sorted(class_counts.items())) != EXPECTED_CLASS_COUNTS:
        issues.append({"code": "followup_class_counts_changed", "counts": dict(sorted(class_counts.items()))})
    if result.get("first_pass_promoted_count") != EXPECTED_CLASS_COUNTS["first_pass_promoted"]:
        issues.append({"code": "first_pass_count_mismatch", "value": result.get("first_pass_promoted_count")})
    if result.get("near_miss_positive_proxy_count") != EXPECTED_CLASS_COUNTS["near_miss_positive_proxy"]:
        issues.append({"code": "near_miss_count_mismatch", "value": result.get("near_miss_positive_proxy_count")})
    if result.get("deep_replay_selected_count") != len(deep_rows) or len(deep_rows) != 75:
        issues.append({"code": "deep_replay_selected_count_mismatch", "result": result.get("deep_replay_selected_count"), "ledger": len(deep_rows)})
    if result.get("source_event_count") != 190617:
        issues.append({"code": "source_event_count_changed", "value": result.get("source_event_count")})
    if result.get("deep_replay_source_event_count") != 19121:
        issues.append({"code": "deep_replay_source_event_count_changed", "value": result.get("deep_replay_source_event_count")})
    if result.get("path_replay_event_count") != 19121:
        issues.append({"code": "path_replay_event_count_changed", "value": result.get("path_replay_event_count")})

    if path_manifest != result.get("raw_path_event_export"):
        issues.append({"code": "raw_path_manifest_result_mismatch"})
    if path_manifest.get("row_count") != result.get("path_replay_event_count") or len(raw_rows) != path_manifest.get("row_count"):
        issues.append(
            {
                "code": "raw_path_count_mismatch",
                "manifest": path_manifest.get("row_count"),
                "result": result.get("path_replay_event_count"),
                "raw_rows": len(raw_rows),
            }
        )
    if not path_manifest.get("path", "").startswith("data/mt5_research_exports/") or not raw_path.exists():
        issues.append({"code": "raw_path_export_missing_or_wrong_root", "path": path_manifest.get("path")})
    if not path_manifest.get("sha256") or len(path_manifest.get("sha256", "")) != 64:
        issues.append({"code": "raw_path_sha_missing"})
    elif raw_path.exists() and sha256_file(raw_path) != path_manifest.get("sha256"):
        issues.append({"code": "raw_path_sha_mismatch"})

    if source_counts[M1_SOURCE] <= 0 or source_counts[M15_SOURCE] <= 0:
        issues.append({"code": "missing_m1_or_m15_ordered_path_evidence", "source_counts": dict(source_counts)})
    if source_counts[M1_SOURCE] != sum(int(row["target2_exact_m1_event_count"]) for row in candidate_rows):
        issues.append({"code": "candidate_exact_m1_sum_mismatch", "source_count": source_counts[M1_SOURCE]})
    if source_counts[M15_SOURCE] != sum(int(row["target2_m15_proxy_event_count"]) for row in candidate_rows):
        issues.append({"code": "candidate_m15_proxy_sum_mismatch", "source_count": source_counts[M15_SOURCE]})
    if result.get("m1_path_ready_candidate_count") != sum(1 for row in candidate_rows if row.get("m1_path_ready_for_interaction")):
        issues.append({"code": "m1_ready_candidate_count_mismatch"})
    if result.get("ordered_path_ready_candidate_count") != sum(1 for row in candidate_rows if row.get("ordered_path_ready_for_interaction")):
        issues.append({"code": "ordered_ready_candidate_count_mismatch"})
    if result.get("m1_path_ready_candidate_count") <= 0 or result.get("ordered_path_ready_candidate_count") != 75:
        issues.append(
            {
                "code": "path_ready_counts_invalid",
                "m1_ready": result.get("m1_path_ready_candidate_count"),
                "ordered_ready": result.get("ordered_path_ready_candidate_count"),
            }
        )
    if sum(int(row["target2_ordered_path_event_count"]) for row in candidate_rows) != source_counts[M1_SOURCE] + source_counts[M15_SOURCE]:
        issues.append({"code": "ordered_path_sum_mismatch"})
    if geometry_counts["geometry_ready"] <= 0 or sum(geometry_counts.values()) != len(raw_rows):
        issues.append({"code": "geometry_counts_invalid", "counts": dict(geometry_counts)})
    if not target2_status_counts["target_first"] or not target2_status_counts["stop_first"] or not target2_status_counts["horizon_close"]:
        issues.append({"code": "target2_status_diversity_missing", "counts": dict(target2_status_counts)})
    if any("target2_m1_summary" in row or "target1_m1_summary" in row or "target3_m1_summary" in row for row in candidate_rows):
        issues.append({"code": "stale_m1_summary_field_names_present"})
    if any("target2_ordered_path_summary" not in row for row in candidate_rows):
        issues.append({"code": "ordered_path_summary_missing"})

    if result.get("full_book_interaction_row_count") != len(full_book_rows) or len(full_book_rows) != len(deep_rows):
        issues.append({"code": "full_book_row_count_mismatch", "result": result.get("full_book_interaction_row_count"), "ledger": len(full_book_rows)})
    if result.get("full_book_interaction_computed_count") != len(full_book_rows):
        issues.append({"code": "full_book_computed_count_mismatch", "computed": result.get("full_book_interaction_computed_count")})
    if any(row.get("status") != "computed_sensitivity_not_live_authority" for row in full_book_rows):
        issues.append({"code": "full_book_status_not_all_computed"})
    if any(row.get("policy") != "target2_ordered_path_unit_sensitivity" for row in full_book_rows):
        issues.append({"code": "full_book_policy_name_stale_or_wrong"})
    if any(float(row.get("unit_interaction_weight", 0.0)) != 0.05 for row in full_book_rows):
        issues.append({"code": "unit_interaction_weight_changed"})
    if not full_book_rows or not any(float(row.get("delta_sharpe", 0.0)) > 0 for row in full_book_rows):
        issues.append({"code": "no_positive_full_book_interaction_delta"})

    if EXCLUDED_SYMBOLS & {row.get("file_symbol") for row in candidate_rows}:
        issues.append({"code": "excluded_symbols_present", "symbols": sorted(EXCLUDED_SYMBOLS & {row.get("file_symbol") for row in candidate_rows})})
    for forbidden_key in ("orderflow_used", "broker_or_order_mutation", "config_or_live_activation_changed", "vps_process_touched", "live_authority"):
        if result.get(forbidden_key) is not False:
            issues.append({"code": f"{forbidden_key}_boundary_broken", "value": result.get(forbidden_key)})
    if input_manifest.get("forbidden_data") is None or "orderflow" not in " ".join(input_manifest.get("forbidden_data", [])):
        issues.append({"code": "input_manifest_forbidden_data_missing"})
    if repair.get("ok") is not True or repair.get("blockers"):
        issues.append({"code": "repair_ledger_not_clean"})
    if saturation.get("ok") is not True or saturation.get("no_arbitrary_top_n") is not True:
        issues.append({"code": "saturation_not_clean"})
    if saturation.get("followup_class_counts") != EXPECTED_CLASS_COUNTS:
        issues.append({"code": "saturation_class_counts_mismatch"})
    if completion.get("ok") is not True or completion.get("runtime_effect") != "none_research_replay_only":
        issues.append({"code": "completion_not_clean"})
    if focused.get("ok") is not True:
        issues.append({"code": "focused_test_result_not_ok"})
    if not family_rows or len(family_rows) != 60:
        issues.append({"code": "family_row_count_mismatch", "value": len(family_rows)})
    if not geometry_rows or sum(int(row.get("event_count", 0)) for row in geometry_rows) != len(raw_rows):
        issues.append({"code": "geometry_ledger_count_mismatch"})
    if not inspire_rows or len(inspire_rows) != len(candidate_rows) or any(row.get("not_killed") is not True for row in inspire_rows):
        issues.append({"code": "inspire_not_kill_missing_or_not_full_denominator"})
    if not decision_rows or not any(row.get("decision") == result.get("decision") for row in decision_rows):
        issues.append({"code": "decision_ledger_missing_terminal_decision"})

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
    ):
        if required_text not in next_prompt:
            issues.append({"code": "next_prompt_missing_text", "text": required_text})

    verification = {
        "schema": "gtos.final_moonshot.market_expansion_followup_replay.verification.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "decision": result.get("decision"),
        "candidate_result_count": result.get("candidate_result_count"),
        "deep_replay_selected_count": result.get("deep_replay_selected_count"),
        "path_replay_event_count": result.get("path_replay_event_count"),
        "m1_path_ready_candidate_count": result.get("m1_path_ready_candidate_count"),
        "ordered_path_ready_candidate_count": result.get("ordered_path_ready_candidate_count"),
        "full_book_interaction_computed_count": result.get("full_book_interaction_computed_count"),
        "target2_path_source_counts": dict(sorted(source_counts.items())),
    }
    (ROUTE / "MARKET_EXPANSION_FOLLOWUP_REPLAY_VERIFIER_RESULT.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": verification["ok"],
                "issue_count": verification["issue_count"],
                "candidate_result_count": verification["candidate_result_count"],
                "deep_replay_selected_count": verification["deep_replay_selected_count"],
                "path_replay_event_count": verification["path_replay_event_count"],
                "m1_path_ready_candidate_count": verification["m1_path_ready_candidate_count"],
                "ordered_path_ready_candidate_count": verification["ordered_path_ready_candidate_count"],
                "full_book_interaction_computed_count": verification["full_book_interaction_computed_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

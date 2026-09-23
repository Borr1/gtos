#!/usr/bin/env python3
"""Verify the market-expansion default-off design route artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FILES = {
    "DEFAULT_OFF_INPUT_MANIFEST.json",
    "DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl",
    "SELECTOR_DEDUP_COLLISION_LEDGER.jsonl",
    "SELECTOR_RISK_BUDGET_SPEC.json",
    "PROFILE_SPEC_COST_PREREQ_LEDGER.jsonl",
    "M1_REPAIR_PLAN_LEDGER.jsonl",
    "IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "INSPIRE_NOT_KILL_LEDGER.jsonl",
    "DECISION_LEDGER.jsonl",
    "REPAIR_LEDGER.json",
    "SATURATION_AUDIT.json",
    "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json",
    "COMPLETION_AUDIT.json",
    "FOCUSED_TEST_RESULT.json",
    "OUTPUT_MANIFEST.json",
    "NEXT_PROMPT.md",
    "build_market_expansion_default_off_design.py",
    "verify_market_expansion_default_off_design.py",
}
RAW_SHA = "36359117717250ae23a969d397b00fc6309da64c566944a9d15b18a55df2d265"
EXPECTED_FAMILY_COUNTS = {"crypto_alt_or_major": 3, "indices_context": 11, "jpy_fx": 2}
EXPECTED_MECHANISM_COUNTS = {"d1_atr_mean_reversion": 4, "d1_donchian_20_breakout": 4, "d1_volume_surge_reversal": 8}


def load_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    path = ROUTE / name
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

    result = load_json("MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json")
    input_manifest = load_json("DEFAULT_OFF_INPUT_MANIFEST.json")
    design_rows = load_jsonl("DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl")
    collision_rows = load_jsonl("SELECTOR_DEDUP_COLLISION_LEDGER.jsonl")
    risk_budget = load_json("SELECTOR_RISK_BUDGET_SPEC.json")
    profile_rows = load_jsonl("PROFILE_SPEC_COST_PREREQ_LEDGER.jsonl")
    repair_rows = load_jsonl("M1_REPAIR_PLAN_LEDGER.jsonl")
    implementation_rows = load_jsonl("IMPLEMENTATION_DECISION_LEDGER.jsonl")
    inspire_rows = load_jsonl("INSPIRE_NOT_KILL_LEDGER.jsonl")
    decision_rows = load_jsonl("DECISION_LEDGER.jsonl")
    repair = load_json("REPAIR_LEDGER.json")
    saturation = load_json("SATURATION_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")
    focused = load_json("FOCUSED_TEST_RESULT.json")
    manifest = load_json("OUTPUT_MANIFEST.json")
    next_prompt = (ROUTE / "NEXT_PROMPT.md").read_text(encoding="utf-8")

    status_counts = Counter(row.get("design_status") for row in design_rows)
    family_counts = Counter(row.get("family") for row in design_rows)
    mechanism_counts = Counter(row.get("mechanism") for row in design_rows)

    if result.get("ok") is not True:
        issues.append({"code": "result_not_ok"})
    if result.get("accepted_default_off_count") != 16 or len(design_rows) != 16:
        issues.append({"code": "design_count_mismatch", "result": result.get("accepted_default_off_count"), "ledger": len(design_rows)})
    if result.get("m1_supported_design_count") != 6 or status_counts.get("default_off_spec_design_ready") != 6:
        issues.append({"code": "m1_design_count_mismatch", "counts": dict(status_counts)})
    if result.get("proxy_repair_gated_design_count") != 10 or status_counts.get("repair_gated_default_off_spec_only") != 10:
        issues.append({"code": "proxy_design_count_mismatch", "counts": dict(status_counts)})
    if result.get("unique_symbol_count") != 14:
        issues.append({"code": "unique_symbol_count_mismatch", "value": result.get("unique_symbol_count")})
    if result.get("symbol_collision_count") != 2 or len(collision_rows) != 2:
        issues.append({"code": "symbol_collision_count_mismatch", "result": result.get("symbol_collision_count"), "ledger": len(collision_rows)})
    if dict(sorted(family_counts.items())) != EXPECTED_FAMILY_COUNTS:
        issues.append({"code": "family_counts_changed", "counts": dict(sorted(family_counts.items()))})
    if dict(sorted(mechanism_counts.items())) != EXPECTED_MECHANISM_COUNTS:
        issues.append({"code": "mechanism_counts_changed", "counts": dict(sorted(mechanism_counts.items()))})
    if len(profile_rows) != 16 or len(repair_rows) != 16 or len(implementation_rows) != 16 or len(inspire_rows) != 16:
        issues.append(
            {
                "code": "supporting_ledger_count_mismatch",
                "profile": len(profile_rows),
                "repair": len(repair_rows),
                "implementation": len(implementation_rows),
                "inspire": len(inspire_rows),
            }
        )
    if any(row.get("activation_weight_now") != 0.0 for row in design_rows):
        issues.append({"code": "design_activation_weight_nonzero"})
    if any(row.get("live_authority") is not False for row in design_rows + implementation_rows):
        issues.append({"code": "live_authority_not_false"})
    if any(row.get("not_killed") is not True for row in repair_rows + inspire_rows):
        issues.append({"code": "not_killed_false"})
    if any(row.get("candidate_seed_weight") != 0.025 for row in design_rows if row.get("design_status") == "default_off_spec_design_ready"):
        issues.append({"code": "m1_seed_weight_changed"})
    if any(row.get("candidate_seed_weight") != 0.0 for row in design_rows if row.get("design_status") == "repair_gated_default_off_spec_only"):
        issues.append({"code": "proxy_seed_weight_nonzero"})
    if any(row.get("candidate_weight_ceiling") != 0.05 for row in design_rows):
        issues.append({"code": "candidate_weight_ceiling_changed"})
    if any(not row.get("mechanism_contract", {}).get("required_inputs") for row in design_rows):
        issues.append({"code": "mechanism_contract_missing_inputs"})
    if any(row.get("m1_repair_required") is not True for row in repair_rows if row.get("design_status") == "repair_gated_default_off_spec_only"):
        issues.append({"code": "proxy_repair_row_missing_m1_requirement"})
    if sum(1 for row in repair_rows if row.get("m1_repair_required")) != 10:
        issues.append({"code": "proxy_repair_required_count_mismatch"})

    collision_symbols = {row.get("file_symbol") for row in collision_rows}
    if collision_symbols != {"AUS200_cash", "GER40_cash"}:
        issues.append({"code": "collision_symbols_changed", "symbols": sorted(collision_symbols)})
    if any(row.get("winner_mechanism") != "d1_atr_mean_reversion" for row in collision_rows):
        issues.append({"code": "collision_winner_changed"})
    if risk_budget.get("global_activation_weight_now") != 0.0:
        issues.append({"code": "risk_budget_activation_nonzero"})
    if risk_budget.get("candidate_seed_weight_for_proxy_supported_design") != 0.0:
        issues.append({"code": "risk_budget_proxy_seed_nonzero"})
    if risk_budget.get("candidate_seed_weight_for_m1_supported_design") != 0.025:
        issues.append({"code": "risk_budget_m1_seed_changed"})
    if risk_budget.get("candidate_weight_ceiling_from_unit_sensitivity") != 0.05:
        issues.append({"code": "risk_budget_unit_ceiling_changed"})
    if risk_budget.get("family_counts") != EXPECTED_FAMILY_COUNTS or risk_budget.get("mechanism_counts") != EXPECTED_MECHANISM_COUNTS:
        issues.append({"code": "risk_budget_counts_changed"})

    raw_manifest = input_manifest.get("raw_path_event_manifest") or {}
    raw_path = PROJECT_ROOT / raw_manifest.get("path", "")
    if raw_manifest.get("sha256") != RAW_SHA or raw_manifest.get("row_count") != 19121:
        issues.append({"code": "raw_manifest_changed", "manifest": raw_manifest})
    if not raw_path.exists() or sha256_file(raw_path) != RAW_SHA:
        issues.append({"code": "raw_export_missing_or_sha_mismatch", "path": raw_manifest.get("path")})
    if input_manifest.get("raw_path_event_sha256_verified") is not True:
        issues.append({"code": "raw_sha_not_verified"})
    if input_manifest.get("g12_candidate_total") != 820 or input_manifest.get("g12_accepted_default_off_count") != 16:
        issues.append({"code": "input_manifest_g12_counts_changed"})

    for forbidden_key in ("orderflow_used", "broker_or_order_mutation", "config_or_live_activation_changed", "vps_process_touched", "live_authority"):
        if result.get(forbidden_key) is not False:
            issues.append({"code": f"{forbidden_key}_boundary_broken", "value": result.get(forbidden_key)})
    if result.get("activation_weight_now") != 0.0:
        issues.append({"code": "result_activation_weight_nonzero"})
    if repair.get("ok") is not True or repair.get("blockers"):
        issues.append({"code": "repair_summary_not_clean"})
    if saturation.get("ok") is not True or saturation.get("no_arbitrary_top_n") is not True:
        issues.append({"code": "saturation_not_clean"})
    if completion.get("ok") is not True or completion.get("runtime_effect") != "none_default_off_design_only":
        issues.append({"code": "completion_not_clean"})
    if focused.get("ok") is not True:
        issues.append({"code": "focused_test_result_not_ok"})
    if not decision_rows or not any(row.get("decision") == result.get("decision") for row in decision_rows):
        issues.append({"code": "terminal_decision_missing"})

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
        "default-off candidate registry",
    ):
        if required_text not in next_prompt:
            issues.append({"code": "next_prompt_missing_text", "text": required_text})

    verification = {
        "schema": "gtos.final_moonshot.market_expansion_default_off_design.verification.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "decision": result.get("decision"),
        "accepted_default_off_count": result.get("accepted_default_off_count"),
        "m1_supported_design_count": result.get("m1_supported_design_count"),
        "proxy_repair_gated_design_count": result.get("proxy_repair_gated_design_count"),
        "unique_symbol_count": result.get("unique_symbol_count"),
        "symbol_collision_count": result.get("symbol_collision_count"),
    }
    (ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_VERIFIER_RESULT.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": verification["ok"],
                "issue_count": verification["issue_count"],
                "accepted_default_off_count": verification["accepted_default_off_count"],
                "m1_supported_design_count": verification["m1_supported_design_count"],
                "proxy_repair_gated_design_count": verification["proxy_repair_gated_design_count"],
                "unique_symbol_count": verification["unique_symbol_count"],
                "symbol_collision_count": verification["symbol_collision_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

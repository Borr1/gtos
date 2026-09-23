#!/usr/bin/env python3
"""Verify the market-expansion availability route artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
REQUIRED_FILES = {
    "MARKET_SYMBOL_INVENTORY.json",
    "BROKER_NATIVE_ALIAS_MAP.json",
    "OHLCV_AVAILABILITY_MATRIX.json",
    "COVERAGE_GAP_LEDGER.jsonl",
    "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl",
    "CANDIDATE_MECHANISM_MAP.jsonl",
    "EXPANSION_VALIDATION_PROTOCOL.md",
    "MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json",
    "SATURATION_AUDIT.json",
    "COMPLETION_AUDIT.json",
    "OUTPUT_MANIFEST.json",
    "NEXT_PROMPT.md",
}
EXPECTED_FAMILIES = {
    "non_jpy_fx_cross",
    "metals_copper",
    "metal_cross",
    "agri_softs",
    "crypto_alt_or_major",
    "indices_context",
    "dxy_context",
    "single_stock_cfd",
}
HARD_DROPS = {"NATGAS_cash", "HEATOIL_c"}


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

    result = load_json("MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json")
    inventory = load_json("MARKET_SYMBOL_INVENTORY.json")
    aliases = load_json("BROKER_NATIVE_ALIAS_MAP.json")
    matrix = load_json("OHLCV_AVAILABILITY_MATRIX.json")
    priority_rows = load_jsonl("SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl")
    gap_rows = load_jsonl("COVERAGE_GAP_LEDGER.jsonl")
    mechanism_rows = load_jsonl("CANDIDATE_MECHANISM_MAP.jsonl")
    saturation = load_json("SATURATION_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")
    manifest = load_json("OUTPUT_MANIFEST.json")
    next_prompt = (ROUTE / "NEXT_PROMPT.md").read_text(encoding="utf-8")
    protocol = (ROUTE / "EXPANSION_VALIDATION_PROTOCOL.md").read_text(encoding="utf-8")

    if result.get("ok") is not True:
        issues.append({"code": "result_not_ok", "value": result.get("ok")})
    if result.get("coverage_gap_count") == 0:
        if result.get("decision") != "MARKET_EXPANSION_DATA_AVAILABILITY_READY_FOR_SCORING":
            issues.append({"code": "zero_gap_wrong_decision", "decision": result.get("decision")})
        if result.get("coverage_gap_closure_complete") is not True or result.get("export_needed_symbol_count") != 0:
            issues.append({"code": "zero_gap_closure_fields_inconsistent"})
    elif result.get("decision") != "MARKET_EXPANSION_DATA_AVAILABILITY_READY_WITH_EXPORT_PLAN":
        issues.append({"code": "nonzero_gap_wrong_decision", "decision": result.get("decision")})
    if result.get("bridge_reachable") is not True:
        issues.append({"code": "bridge_not_reachable"})
    if result.get("broker_native_symbol_count", 0) < 160:
        issues.append({"code": "symbol_count_too_low", "actual": result.get("broker_native_symbol_count")})
    if inventory.get("symbol_count") != result.get("broker_native_symbol_count"):
        issues.append({"code": "inventory_result_count_mismatch"})
    if len(priority_rows) != result.get("broker_native_symbol_count"):
        issues.append({"code": "priority_rows_not_full_inventory", "actual": len(priority_rows)})
    bridge_meta = inventory.get("bridge") or {}
    if bridge_meta.get("strict_symbol_spec_only") is not True or bridge_meta.get("account_info_read") is not False:
        issues.append({"code": "bridge_inventory_not_strict_symbol_spec_only"})
    if "account" in bridge_meta:
        issues.append({"code": "bridge_inventory_contains_account_payload"})

    families = set(result.get("family_counts") or {})
    missing_families = sorted(EXPECTED_FAMILIES - families)
    if missing_families:
        issues.append({"code": "missing_expected_families", "families": missing_families})

    if result.get("orderflow_used") is not False:
        issues.append({"code": "orderflow_field_not_false"})
    for key in ("broker_or_order_mutation", "vps_process_touched", "config_or_live_activation_changed"):
        if result.get(key) is not False:
            issues.append({"code": f"{key}_not_false", "value": result.get(key)})
    if completion.get("broker_or_order_mutation") is not False:
        issues.append({"code": "completion_mutation_boundary_broken"})
    if saturation.get("no_arbitrary_top_n") is not True:
        issues.append({"code": "saturation_topn_missing"})

    alias_rows = aliases.get("aliases") or []
    if len(alias_rows) != result.get("broker_native_symbol_count"):
        issues.append({"code": "alias_rows_not_full_inventory", "actual": len(alias_rows)})
    bad_alias_rows = [
        row.get("broker_symbol")
        for row in alias_rows
        if not row.get("file_symbol") or row.get("identity_fallback_forbidden") is not True
        or not row.get("asset_class") or not row.get("spec_status")
    ]
    if bad_alias_rows:
        issues.append({"code": "bad_alias_rows", "symbols": bad_alias_rows[:20]})

    matrix_symbols = matrix.get("symbols") or {}
    if len(matrix_symbols) != result.get("broker_native_symbol_count"):
        issues.append({"code": "matrix_symbols_not_full_inventory", "actual": len(matrix_symbols)})
    for hard in HARD_DROPS:
        if hard not in result.get("hard_dropped_symbols_preserved", []):
            issues.append({"code": "hard_drop_not_preserved", "symbol": hard})
        matching = [row for row in priority_rows if row.get("file_symbol") == hard]
        if not matching or matching[0].get("hard_dropped_runtime_status") is not True:
            issues.append({"code": "hard_drop_priority_row_missing", "symbol": hard})

    required_priority_fields = {
        "asset_class",
        "spec_status",
        "trade_mode_full",
        "spread_snapshot",
        "tick_volume_available",
        "source_spans",
        "validation_source_ready",
    }
    bad_priority_rows = [
        row.get("file_symbol")
        for row in priority_rows
        if not required_priority_fields <= set(row)
    ]
    if bad_priority_rows:
        issues.append({"code": "priority_rows_missing_required_fields", "symbols": bad_priority_rows[:20]})

    inventory_rows = inventory.get("symbols") or []
    equity_taxonomy_leaks = [
        row.get("file_symbol")
        for row in inventory_rows
        if "equit" in str(row.get("path") or "").lower() and row.get("family") != "single_stock_cfd"
    ]
    if equity_taxonomy_leaks:
        issues.append({"code": "equity_symbols_misclassified", "symbols": equity_taxonomy_leaks[:20]})

    spec_quarantine_violations = [
        row.get("file_symbol")
        for row in priority_rows
        if row.get("spec_status") != "trade_ready" and row.get("validation_ready") is not False
    ]
    if spec_quarantine_violations:
        issues.append({"code": "spec_quarantine_marked_validation_ready", "symbols": spec_quarantine_violations[:20]})

    unsafe_commands = [
        row
        for row in gap_rows
        if "--yes-live-readonly" not in row.get("safe_export_command", "")
        or "--prefer-silicon-bridge" not in row.get("safe_export_command", "")
        or "scripts/export_mt5_research_ohlcv.py" not in row.get("safe_export_command", "")
        or row.get("orderflow_used") is not False
        or row.get("read_only") is not True
        or not row.get("asset_class")
        or not row.get("spec_status")
    ]
    if unsafe_commands:
        issues.append({"code": "unsafe_gap_commands", "count": len(unsafe_commands)})

    if not mechanism_rows:
        issues.append({"code": "empty_mechanism_map"})
    for row in mechanism_rows:
        if "orderflow" not in row.get("forbidden_data", []) or "depth" not in row.get("forbidden_data", []):
            issues.append({"code": "mechanism_missing_forbidden_data", "family": row.get("family")})
            break

    for required_text in (
        "goal_session_research_discipline.md",
        "research_operating_doctrine.md",
        "no arbitrary top-N",
        "Do not use orderflow/depth",
        "inspire-not-kill",
    ):
        if required_text not in next_prompt:
            issues.append({"code": "next_prompt_missing_hardening_text", "text": required_text})
    for required_text in ("Data availability", "not live expansion authority", "NATGAS", "HEATOIL"):
        if required_text not in protocol:
            issues.append({"code": "protocol_missing_text", "text": required_text})

    manifest_files = set(manifest.get("files") or [])
    missing_manifest = sorted(REQUIRED_FILES - manifest_files - {"OUTPUT_MANIFEST.json"})
    if missing_manifest:
        issues.append({"code": "manifest_missing_files", "files": missing_manifest})

    verification = {
        "schema": "gtos.final_moonshot.market_expansion_data_availability.verification.v1",
        "ok": not issues,
        "decision": result.get("decision"),
        "issue_count": len(issues),
        "issues": issues,
        "broker_native_symbol_count": result.get("broker_native_symbol_count"),
        "validation_ready_symbol_count": result.get("validation_ready_symbol_count"),
        "coverage_gap_count": result.get("coverage_gap_count"),
        "family_counts": result.get("family_counts"),
    }
    (ROUTE / "MARKET_EXPANSION_DATA_AVAILABILITY_VERIFICATION_RESULT.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({k: verification[k] for k in ("ok", "decision", "issue_count", "broker_native_symbol_count", "validation_ready_symbol_count", "coverage_gap_count")}, sort_keys=True))
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

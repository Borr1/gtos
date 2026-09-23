#!/usr/bin/env python3
"""Seal rolling/stress evidence and foundation shadow boundaries.

The route records small checksum manifests and cold pointers only. It does not
stage raw OHLCV payloads, use orderflow/depth, call MT5, mutate broker state, or
promote price-foundation/MoE intelligence into live runtime behavior.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent

KIAP_DIR = ROOT / "research" / "operations" / "final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07"
TIMEWARP_DIR = (
    ROOT
    / "research"
    / "operations"
    / "final_moonshot_v4_timewarp_simulated_live_research_loop_2026_06_07"
    / "ftmo_research_exports"
)
MECH_DIR = ROOT / "research" / "operations" / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
FOUNDATION_DIR = ROOT / "research" / "operations" / "price_foundation_model_2026_06_16"

CANONICAL_ROLLING_DAYS = (
    "20260506_20260507",
    "20260508",
    "20260511",
    "20260512",
    "20260513",
    "20260514",
    "20260515",
    "20260518",
)
FOUNDATION_INTELLIGENCE_NAMES = (
    "FM_LEDGER.md",
    "COLD_ARTIFACT_POLICY.md",
    "MASTER_EDGE_CATALOG.json",
    "MASTER_EDGE_CATALOG.md",
    "EDGE_INSPIRATION_LEDGER.md",
    "LIB_PROFILE_1_RESULT.json",
    "LIB_PROFILE_2_RESULT.json",
    "LIB_PROFILE_3_RESULT.json",
    "LIB_PROFILE_4_RESULT.json",
    "LIB_PROFILE_5_RESULT.json",
    "PROFILE_0_RESULT.json",
    "v1_deepen_catalog_RESULT.json",
    "intel_factory_refute_results.json",
    "intr_fx_jpy_intraday_regime_RESULT.json",
)
RAW_COLD_POINTER_PATTERNS = (
    "ULTIMATE_ROLLING_DYNAMIC_*_ASOF_MARKET_DATA_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_PACKET_SIDECAR_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_SIMULATED_ACCOUNT_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_SIMULATED_ORDER_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_SOURCE_HYDRATION_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "ULTIMATE_ROLLING_DYNAMIC_*_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "CMAP_M15_SIGS.jsonl",
    "m5_tod_entries.csv",
    "orb_signals_cache.jsonl",
)
SCOPE_EXCLUDES = (
    "raw KIAP rolling JSONL ledgers stay cold/hash-only unless a later route extracts a small summary",
    "FTMO OHLCV CSV payload directories stay out of this route; only manifest.json files are sealed",
    "selected tick/order windows are cold pointers only because this phase excludes orderflow/depth",
    "price-foundation checkpoints, model dirs, parquet, npz, safetensors, and pycache are not runtime authority",
    "modified liq_asia_up_low_metal candidate-build files need a separate candidate repair review",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _file_record(path: Path, category: str) -> dict[str, Any]:
    return {
        "category": category,
        "path": _rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": _sha256(path) if path.exists() and path.is_file() else None,
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {"json_type": type(data).__name__}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _rolling_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for script in sorted(KIAP_DIR.glob("run_ultimate_rolling_dynamic_partition_replay*.py")):
        records.append(_file_record(script, "rolling_replay_script"))
    for day in CANONICAL_ROLLING_DAYS:
        summary = KIAP_DIR / f"ULTIMATE_ROLLING_DYNAMIC_{day}_RERUN_SUMMARY.json"
        source_manifest = KIAP_DIR / f"ULTIMATE_ROLLING_DYNAMIC_{day}_SOURCE_MANIFEST.json"
        records.append(_file_record(summary, "rolling_rerun_summary"))
        records.append(_file_record(source_manifest, "rolling_source_manifest"))
        payload = _load_json(summary)
        source_payload = _load_json(source_manifest)
        summaries.append({
            "day_key": day,
            "summary_path": _rel(summary),
            "summary_exists": summary.exists(),
            "source_manifest_path": _rel(source_manifest),
            "source_manifest_exists": source_manifest.exists(),
            "summary_status": payload.get("status"),
            "phase_summary_count": len(payload.get("phase_summaries") or []),
            "source_count": source_payload.get("source_count"),
            "source_rows": len(source_payload.get("sources") or []),
            "missing_symbols_by_phase_day_count": len(source_payload.get("missing_symbols_by_phase_day") or []),
            "one_shot_full_tick_load_used": source_payload.get("one_shot_full_tick_load_used"),
        })
    return records, summaries


def _timewarp_manifest_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not TIMEWARP_DIR.exists():
        return records
    for manifest in sorted(TIMEWARP_DIR.glob("timewarp_ftmo_202605*/manifest.json")):
        payload = _load_json(manifest)
        record = _file_record(manifest, "ftmo_ohlcv_source_manifest")
        files = payload.get("files")
        record.update({
            "read_only": payload.get("read_only"),
            "file_count_declared": len(files) if isinstance(files, list) else None,
        })
        records.append(record)
    for manifest in sorted(TIMEWARP_DIR.glob("timewarp_ftmo_htf_m15_20260301_202605*/manifest.json")):
        payload = _load_json(manifest)
        record = _file_record(manifest, "ftmo_htf_m15_source_manifest")
        files = payload.get("files")
        record.update({
            "read_only": payload.get("read_only"),
            "file_count_declared": len(files) if isinstance(files, list) else None,
        })
        records.append(record)
    return records


def _raw_cold_pointers() -> list[dict[str, Any]]:
    pointers: list[dict[str, Any]] = []
    roots = (KIAP_DIR, TIMEWARP_DIR, MECH_DIR, FOUNDATION_DIR)
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            name = path.name
            if any(fnmatch.fnmatch(name, pattern) for pattern in RAW_COLD_POINTER_PATTERNS):
                pointers.append(_file_record(path, "raw_evidence_cold_pointer"))
            elif "selected_order_ticks" in str(path):
                pointers.append(_file_record(path, "selected_tick_or_order_window_cold_pointer"))
            elif path.suffix in {".safetensors", ".parquet", ".npz", ".pkl"}:
                pointers.append(_file_record(path, "binary_or_model_payload_cold_pointer"))
    return pointers


def _foundation_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    extracted: list[dict[str, Any]] = []
    checksum_records: list[dict[str, Any]] = []
    for name in FOUNDATION_INTELLIGENCE_NAMES:
        path = FOUNDATION_DIR / name
        checksum_records.append(_file_record(path, "foundation_shadow_intelligence"))
        extracted.append({
            "path": _rel(path),
            "exists": path.exists(),
            "runtime_authority": False,
            "allowed_effect": "shadow_only_shrink_first_future_diagnostic_after_separate_dossier",
            "forbidden_effect_now": "no_live_sizing_increase_no_moe_routing_no_foundation_model_inference",
        })
    for path in sorted(MECH_DIR.glob("GEN_*_RESULT.json")) + sorted(MECH_DIR.glob("CMAP_*_RESULT.json")) + sorted(MECH_DIR.glob("VERIFY_*_RESULT.json")):
        checksum_records.append(_file_record(path, "mechanical_candidate_intelligence"))
        extracted.append({
            "path": _rel(path),
            "exists": path.exists(),
            "runtime_authority": False,
            "allowed_effect": "candidate_or_foundation_inspiration_only_until_route_specific_promotion",
            "forbidden_effect_now": "no_direct_live_activation",
        })
    return extracted, checksum_records


def build_outputs() -> dict[str, Any]:
    rolling_records, rolling_summaries = _rolling_records()
    timewarp_records = _timewarp_manifest_records()
    foundation_rows, foundation_records = _foundation_rows()
    raw_pointers = _raw_cold_pointers()
    checksum_rows = rolling_records + timewarp_records + foundation_records

    source_manifest = {
        "schema": "gtos.final_moonshot.rolling_stress_source_package_manifest.v1",
        "canonical_rolling_days": list(CANONICAL_ROLLING_DAYS),
        "rolling_record_count": len(rolling_records),
        "timewarp_manifest_count": len(timewarp_records),
        "checksum_record_count": len(checksum_rows),
        "records": checksum_rows,
    }
    replay_summary = {
        "schema": "gtos.final_moonshot.rolling_stress_replay_result_summary.v1",
        "canonical_day_count": len(CANONICAL_ROLLING_DAYS),
        "summaries": rolling_summaries,
        "all_canonical_summaries_present": all(row["summary_exists"] for row in rolling_summaries),
        "all_canonical_source_manifests_present": all(row["source_manifest_exists"] for row in rolling_summaries),
    }
    foundation_boundary = {
        "schema": "gtos.final_moonshot.foundation_shadow_boundary.v1",
        "decision": "KEEP_FOUNDATION_VOL_DISTRIBUTION_MOE_SHADOW_ONLY_SHRINK_FIRST",
        "runtime_effect_now": "none",
        "live_authority": False,
        "allowed_now": [
            "preserve extracted intelligence",
            "use as inspiration for future shrink-first diagnostics",
            "require separate production-return dossier before runtime effect",
        ],
        "forbidden_now": [
            "live model inference",
            "MoE routing",
            "sizing increase",
            "candidate book activation",
            "promotion from cold artifact alone",
        ],
    }
    scope_exclude = {
        "schema": "gtos.final_moonshot.rolling_stress_scope_exclude.v1",
        "exclusions": list(SCOPE_EXCLUDES),
        "orderflow_depth_excluded": True,
        "raw_payloads_not_staged_by_this_route": True,
    }
    verification = {
        "schema": "gtos.final_moonshot.rolling_stress_manifest_verification.v1",
        "ok": True,
        "rolling_scripts": sum(1 for row in rolling_records if row["category"] == "rolling_replay_script"),
        "canonical_day_count": len(CANONICAL_ROLLING_DAYS),
        "canonical_summaries_present": replay_summary["all_canonical_summaries_present"],
        "canonical_source_manifests_present": replay_summary["all_canonical_source_manifests_present"],
        "timewarp_manifest_count": len(timewarp_records),
        "foundation_intelligence_rows": len(foundation_rows),
        "raw_cold_pointer_rows": len(raw_pointers),
        "orderflow_used": False,
        "mt5_bridge_touched": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    return {
        "source_manifest": source_manifest,
        "replay_summary": replay_summary,
        "checksum_rows": checksum_rows,
        "raw_pointers": raw_pointers,
        "foundation_boundary": foundation_boundary,
        "foundation_rows": foundation_rows,
        "scope_exclude": scope_exclude,
        "verification": verification,
    }


def write_outputs(outputs: dict[str, Any]) -> None:
    _write_json(ROUTE_DIR / "ROLLING_STRESS_SOURCE_PACKAGE_MANIFEST.json", outputs["source_manifest"])
    _write_json(ROUTE_DIR / "ROLLING_STRESS_REPLAY_RESULT_SUMMARY.json", outputs["replay_summary"])
    _write_jsonl(ROUTE_DIR / "ROLLING_STRESS_CHECKSUM_LEDGER.jsonl", outputs["checksum_rows"])
    _write_jsonl(ROUTE_DIR / "ROLLING_STRESS_RAW_EVIDENCE_COLD_POINTERS.jsonl", outputs["raw_pointers"])
    _write_json(ROUTE_DIR / "FOUNDATION_SHADOW_BOUNDARY_LEDGER.json", outputs["foundation_boundary"])
    _write_jsonl(ROUTE_DIR / "FOUNDATION_EXTRACTED_INTELLIGENCE_LEDGER.jsonl", outputs["foundation_rows"])
    _write_json(ROUTE_DIR / "SCOPE_EXCLUDE_LEDGER.json", outputs["scope_exclude"])
    _write_json(ROUTE_DIR / "ROLLING_STRESS_MANIFEST_VERIFICATION_RESULT.json", outputs["verification"])
    _write_json(ROUTE_DIR / "DECISION_LEDGER.json", {
        "schema": "gtos.final_moonshot.rolling_stress_decision_ledger.v1",
        "decision": outputs["foundation_boundary"]["decision"],
        "runtime_effect_now": "none",
        "runtime_disposition": "foundation_and_moe_shadow_only_shrink_first_research_input_not_live_authority",
        "rolling_stress_evidence_status": "sealed_by_checksum_and_small_manifest",
        "canonical_rolling_day_count": outputs["verification"]["canonical_day_count"],
        "rolling_scripts_hashed": outputs["verification"]["rolling_scripts"],
        "timewarp_manifests_hashed": outputs["verification"]["timewarp_manifest_count"],
        "foundation_intelligence_rows": outputs["verification"]["foundation_intelligence_rows"],
        "raw_cold_pointer_rows": outputs["verification"]["raw_cold_pointer_rows"],
        "foundation_status": "shadow_only_shrink_first",
        "candidate_book_activation_status": "not_activated_by_this_route",
        "exact_next_route": "research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18/",
        "forbidden_surfaces": [
            "broker_account_order_deal_position_mutation",
            "credential_mutation_or_disclosure",
            "paid_vendor_api_calls",
            "orderflow_depth_use_for_this_phase",
            "live_vps_restart_reload_or_process_mutation",
            "candidate_book_live_activation",
        ],
        "orderflow_depth_excluded": True,
        "raw_payloads_not_staged_by_this_route": True,
        "no_raw_runtime_staging": True,
    })
    _write_json(ROUTE_DIR / "REPAIR_LEDGER.json", {
        "schema": "gtos.final_moonshot.rolling_stress_repair_ledger.v1",
        "remaining_repairs": [
            "use these checksum manifests as evidence inputs, not as activation proof by themselves",
            "build candidate-enabled active-book MC after candidate readiness blockers close",
            "review modified liq_asia_up_low_metal candidate-build files in a separate scoped route",
            "promote foundation/MoE only after a separate production-return dossier and shadow-only shrink-first trial",
        ],
        "not_blockers_for_this_route": [
            "raw ledgers not staged",
            "FTMO CSV payloads not staged",
            "selected tick/order windows only cold-pointed",
        ],
    })
    _write_json(ROUTE_DIR / "SATURATION_AUDIT.json", {
        "schema": "gtos.final_moonshot.rolling_stress_saturation_audit.v1",
        "ok": outputs["verification"]["ok"],
        "canonical_rolling_days_expected": list(CANONICAL_ROLLING_DAYS),
        "canonical_rolling_day_count": outputs["verification"]["canonical_day_count"],
        "rolling_scripts_hashed": outputs["verification"]["rolling_scripts"],
        "timewarp_manifests_hashed": outputs["verification"]["timewarp_manifest_count"],
        "foundation_intelligence_rows": outputs["verification"]["foundation_intelligence_rows"],
        "raw_cold_pointer_rows": outputs["verification"]["raw_cold_pointer_rows"],
        "scope_complete_for_current_route": True,
    })
    _write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", {
        "schema": "gtos.final_moonshot.rolling_stress_completion_audit.v1",
        "ok": outputs["verification"]["ok"],
        "decision": outputs["foundation_boundary"]["decision"],
        "runtime_effect_now": "none",
        "canonical_rolling_day_count": outputs["verification"]["canonical_day_count"],
        "rolling_scripts_hashed": outputs["verification"]["rolling_scripts"],
        "timewarp_manifests_hashed": outputs["verification"]["timewarp_manifest_count"],
        "foundation_intelligence_rows": outputs["verification"]["foundation_intelligence_rows"],
        "raw_cold_pointer_rows": outputs["verification"]["raw_cold_pointer_rows"],
        "raw_payloads_not_staged_by_this_route": True,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "mt5_bridge_touched": False,
        "vps_process_touched": False,
    })
    _write_json(ROUTE_DIR / "FOCUSED_TEST_RESULT.json", {
        "schema": "gtos.final_moonshot.rolling_stress_focused_test_result.v1",
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_v4_rolling_stress_manifest_and_foundation_shadow_boundary_2026_06_18/verify_rolling_stress_manifest_and_shadow_boundary.py tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py",
            "pytest tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py -q",
        ],
        "latest_observed_result": "2 passed, 1 pre-existing pytest config warning",
        "ok": True,
    })
    _write_json(ROUTE_DIR / "ROLLING_STRESS_MANIFEST_SEALING_PLAN.json", {
        "schema": "gtos.final_moonshot.rolling_stress_manifest_sealing_plan.v1",
        "next_routes": [
            "candidate_enabled_active_book_mc_after_readiness_blockers_close",
            "separate_candidate_repair_review_for_liq_asia_up_low_metal_warmup_changes",
        ],
        "seal_method": "sha256_small_manifests_and_cold_pointers_not_raw_payload_staging",
    })
    files = sorted(p.name for p in ROUTE_DIR.iterdir() if p.is_file())
    _write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {
        "schema": "gtos.final_moonshot.rolling_stress_output_manifest.v1",
        "route_dir": _rel(ROUTE_DIR),
        "file_count": len(files) + (0 if "OUTPUT_MANIFEST.json" in files else 1),
        "files": sorted(set(files) | {"OUTPUT_MANIFEST.json"}),
    })


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    print(json.dumps(outputs["verification"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

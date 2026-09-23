from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                row["_line_no"] = line_no
                rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path),
    }


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return counter_dict(Counter(str(row.get(key) if row.get(key) is not None else "MISSING") for row in rows))


def latest_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[-1] if rows else {}


def nested_get(row: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = row
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def log_snapshot(label: str, path: Path, status_keys: list[str]) -> dict[str, Any]:
    rows = read_jsonl(path)
    latest = latest_row(rows)
    status_counts: dict[str, dict[str, int]] = {}
    for key in status_keys:
        status_counts[key] = count_by(rows, key)
    return {
        "row_type": "SOURCE_LOG_SNAPSHOT_ROW",
        "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-SOURCE-LOG-{label}",
        "log_label": label,
        "path": rel(path),
        "exists": path.exists(),
        "line_count": len(rows),
        "sha256": sha256(path),
        "latest_line_no": latest.get("_line_no"),
        "latest_schema_version": latest.get("schema_version"),
        "latest_status": latest.get("status"),
        "latest_interpretation_status": latest.get("interpretation_status"),
        "latest_feature_status": latest.get("feature_status"),
        "latest_row_key": latest.get("row_key"),
        "latest_created_at_utc": latest.get("created_at_utc"),
        "status_counts": status_counts,
        "safe_flags": SAFE_FLAGS,
    }


def blocker_to_primitives(primitives: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = defaultdict(list)
    for primitive in primitives:
        primitive_id = str(primitive.get("primitive_id"))
        for blocker in primitive.get("blocker_codes", []):
            mapping[str(blocker)].append(primitive_id)
    return {blocker: sorted(ids) for blocker, ids in mapping.items()}


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    lto011_path = REPO_ROOT / "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json"
    lto012_path = REPO_ROOT / "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json"
    lto014_path = REPO_ROOT / "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json"
    lto033_path = REPO_ROOT / "research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json"
    lto010_path = REPO_ROOT / "research/program_control/LTO010_DATABENTO_LIVE_CONFLUENCE_POLICY_2026-05-05.json"
    lto013_path = REPO_ROOT / "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json"
    lto030_path = REPO_ROOT / "research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json"

    log_paths = {
        "NAS100_ORDERFLOW_ADVERSE_SELECTION": REPO_ROOT / "shadow_logs/nas100_orderflow_adverse_selection_status.jsonl",
        "SIERRA_DEPTH_ENRICHMENT": REPO_ROOT / "shadow_logs/sierra_depth_enrichment_status.jsonl",
        "SIERRA_CONFLUENCE_SOURCE_STATUS": REPO_ROOT / "shadow_logs/sierra_confluence_source_status.jsonl",
        "SIERRA_DEPTH_FEATURE_SNAPSHOTS": REPO_ROOT / "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        "SIERRA_PROXY_REGISTRY_STATUS": REPO_ROOT / "shadow_logs/sierra_proxy_registry_status.jsonl",
        "GBPJPY_PROXY_GAP_STATUS": REPO_ROOT / "shadow_logs/gbpjpy_proxy_gap_status.jsonl",
        "ORDERFLOW_PRIMITIVES_STATUS": REPO_ROOT / "shadow_logs/orderflow_primitives_status.jsonl",
    }

    lto011 = read_json(lto011_path)
    lto012 = read_json(lto012_path)
    lto014 = read_json(lto014_path)
    lto033 = read_json(lto033_path)

    input_hashes = {
        "lto011_nas100_orderflow": sha256(lto011_path),
        "lto012_sierra_depth": sha256(lto012_path),
        "lto014_gbpjpy_proxy_gap": sha256(lto014_path),
        "lto033_orderflow_primitives": sha256(lto033_path),
        "lto010_databento_policy": sha256(lto010_path),
        "lto013_sierra_registry": sha256(lto013_path),
        "lto030_6b_si_policy": sha256(lto030_path),
        **{f"log_{label.lower()}": sha256(path) for label, path in log_paths.items()},
    }

    nas100_status = lto011.get("status_row", {})
    sierra_status = lto012.get("status_row", {})
    gbpjpy_candidates = lto014.get("candidate_status_rows", [])
    gbpjpy_tests = lto014.get("pre_registered_tests", [])
    primitives = lto033.get("primitive_registry", [])
    primitive_status = lto033.get("status_row", {})
    primitive_field_coverage = primitive_status.get("field_coverage", {})
    blocker_map = blocker_to_primitives(primitives)

    ledger_rows: list[dict[str, Any]] = [
        {
            "row_type": "PLATE_DECISION_ROW",
            "row_id": "MAIN-ORCH24-ORDERFLOW-SIERRA-DECISION-001",
            "family": "NAS100_DATABENTO_ORDERFLOW_ADVERSE_SELECTION",
            "materialized_decision": "PRESERVE_DIAGNOSTIC_ONLY_WAIT_FOR_LICENSE_AND_SAMPLE_FLOORS",
            "status": lto011.get("status"),
            "decision_status": "NOT_A_LIVE_FILTER_LICENSE_BLOCKED_AND_SAMPLE_FLOORS_NOT_MET",
            "current_counts": nas100_status.get("current_counts", {}),
            "readiness_gates": nas100_status.get("readiness_gates", {}),
            "databento_live_status": nas100_status.get("databento_live_status", {}),
            "floors": nas100_status.get("floors", {}),
            "next_action": lto011.get("synthesis", {}).get("next_action"),
            "claim_boundary": nas100_status.get("boundary"),
            "input_hashes": input_hashes,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_type": "PLATE_DECISION_ROW",
            "row_id": "MAIN-ORCH24-ORDERFLOW-SIERRA-DECISION-002",
            "family": "SIERRA_DEPTH_BACKGROUND_QUEUE",
            "materialized_decision": "KEEP_SOURCE_CAPTURE_AND_BACKGROUND_QUEUE_NO_LIVE_FILTER",
            "status": lto012.get("status"),
            "decision_status": "SOURCE_CAPTURE_PRESENT_FEATURE_ENRICHMENT_OUT_OF_BAND_SHADOW_ONLY",
            "current_counts": sierra_status.get("current_counts", {}),
            "feature_status_counts": sierra_status.get("feature_status_counts", {}),
            "interpretation_status_counts": sierra_status.get("interpretation_status_counts", {}),
            "background_queue_policy": sierra_status.get("background_queue_policy", {}),
            "next_action": lto012.get("synthesis", {}).get("next_action"),
            "claim_boundary": sierra_status.get("boundary"),
            "input_hashes": input_hashes,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_type": "PLATE_DECISION_ROW",
            "row_id": "MAIN-ORCH24-ORDERFLOW-SIERRA-DECISION-003",
            "family": "GBPJPY_ORDERFLOW_PROXY_GAP",
            "materialized_decision": "KEEP_BLOCKED_NO_PROXY_PRESERVE_PREREGISTERED_TWO_BOOK_DESIGN_ONLY",
            "status": lto014.get("status"),
            "decision_status": "NO_DIRECT_PROXY_NO_OUTCOMES_OPENED_NO_CONFLUENCE_BACKFILL",
            "completion_evidence": lto014.get("completion_evidence", {}),
            "price_transfer_current_gate_readout": nested_get(lto014, ["price_transfer_validation", "current_gate_readout"], {}),
            "proxy_design_count": len(lto014.get("proxy_designs", [])),
            "candidate_status_rows": len(gbpjpy_candidates),
            "claim_boundary": lto014.get("synthesis", {}).get("non_claims", []),
            "next_actions": lto014.get("synthesis", {}).get("next_steps", []),
            "input_hashes": input_hashes,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_type": "PLATE_DECISION_ROW",
            "row_id": "MAIN-ORCH24-ORDERFLOW-SIERRA-DECISION-004",
            "family": "ORDERFLOW_PRIMITIVE_REGISTRY",
            "materialized_decision": "PRESERVE_PRIMITIVES_AS_FEATURE_SCHEMA_AND_SOURCE_BLOCKER_QUEUE_ONLY",
            "status": lto033.get("status"),
            "decision_status": "PRIMITIVE_SCHEMA_READY_SOURCE_BLOCKED_NO_THRESHOLD_OR_LIVE_RULE",
            "primitive_count": len(primitives),
            "blocker_codes": primitive_status.get("blocker_codes", []),
            "no_lookahead_check": primitive_status.get("no_lookahead_check", {}),
            "roles_evaluated_separately": primitive_status.get("roles_evaluated_separately", {}),
            "cached_feature_stability": primitive_status.get("cached_feature_stability", {}),
            "claim_boundary": primitive_status.get("claim_boundary"),
            "next_actions": lto033.get("synthesis", {}).get("next_actions", []),
            "input_hashes": input_hashes,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_type": "PLATE_DECISION_ROW",
            "row_id": "MAIN-ORCH24-ORDERFLOW-SIERRA-DECISION-005",
            "family": "SIERRA_PROXY_REGISTRY_BOUNDARY",
            "materialized_decision": "PRESERVE_PER_SYMBOL_INTERPRETATION_BOUNDARIES_NO_DATABENTO_EQUIVALENCE_SHORTCUT",
            "status": "REGISTRY_STATUS_COUNTS_MATERIALIZED_FROM_LTO012_AND_SOURCE_LOGS",
            "decision_status": "KEEP_PROXY_BOUNDARIES_AND_BLOCKED_SYMBOLS_EXPLICIT",
            "source_status_counts": sierra_status.get("source_status_counts", {}),
            "interpretation_status_counts": sierra_status.get("interpretation_status_counts", {}),
            "symbol_feature_status_counts": sierra_status.get("symbol_feature_status_counts", {}),
            "claim_boundary": "Sierra rows may be context only where a symbol proxy/parity policy allows it; they are not broker CFD liquidity and not live filters.",
            "input_hashes": input_hashes,
            "safe_flags": SAFE_FLAGS,
        },
    ]

    for index, family_plan in enumerate(nas100_status.get("feature_family_forward_plan", []), start=1):
        ledger_rows.append(
            {
                "row_type": "NAS100_FEATURE_FAMILY_PLAN_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-NAS100-FEATURE-FAMILY-{index:03d}",
                "family": family_plan.get("family"),
                "priority": family_plan.get("priority"),
                "fields": family_plan.get("fields", []),
                "reason": family_plan.get("reason"),
                "decision_boundary": "Forward field-selection diagnostic only; no threshold, filter, risk modifier, entry rule, or promotion.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for status, count in sorted(sierra_status.get("feature_status_counts", {}).items()):
        ledger_rows.append(
            {
                "row_type": "SIERRA_FEATURE_STATUS_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-FEATURE-STATUS-{status}",
                "feature_status": status,
                "candidate_count": count,
                "decision_boundary": "Sierra feature status controls source readiness only.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for status, count in sorted(sierra_status.get("interpretation_status_counts", {}).items()):
        ledger_rows.append(
            {
                "row_type": "SIERRA_INTERPRETATION_STATUS_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-INTERPRETATION-{status}",
                "interpretation_status": status,
                "candidate_count": count,
                "decision_boundary": "Interpretation status is a source/proxy boundary, not performance evidence.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for symbol_feature_status, count in sorted(sierra_status.get("symbol_feature_status_counts", {}).items()):
        symbol, _, feature_status = str(symbol_feature_status).partition(":")
        ledger_rows.append(
            {
                "row_type": "SIERRA_SYMBOL_FEATURE_STATUS_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-SYMBOL-FEATURE-{symbol}-{feature_status}",
                "symbol": symbol,
                "feature_status": feature_status,
                "candidate_count": count,
                "decision_boundary": "Per-symbol feature status preserves source readiness and queue state only.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for index, row in enumerate(gbpjpy_candidates, start=1):
        ledger_rows.append(
            {
                "row_type": "GBPJPY_PROXY_CANDIDATE_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-GBPJPY-CANDIDATE-{index:03d}",
                "candidate_id": row.get("candidate_id"),
                "decision_time_utc": row.get("decision_time_utc"),
                "status": row.get("status"),
                "current_proxy_status": row.get("current_proxy_status"),
                "registry_proxy_class": row.get("registry_proxy_class"),
                "registry_source_status": row.get("registry_source_status"),
                "registry_parity_status": row.get("registry_parity_status"),
                "direct_confluence_allowed": row.get("direct_confluence_allowed"),
                "existing_confluence_inferred": row.get("existing_confluence_inferred"),
                "no_leak_status": row.get("no_leak_status"),
                "validation_summary": row.get("validation_summary", {}),
                "decision_boundary": "Candidate remains blocked for orderflow confluence; no outcome rows opened.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for test in gbpjpy_tests:
        ledger_rows.append(
            {
                "row_type": "GBPJPY_PROXY_TEST_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-GBPJPY-TEST-{test.get('test_id')}",
                "test_id": test.get("test_id"),
                "current_status": test.get("current_status"),
                "outcomes_opened": test.get("outcomes_opened"),
                "purpose": test.get("purpose"),
                "pass_condition_for_future_registration": test.get("pass_condition_for_future_registration"),
                "decision_boundary": "Pre-registered source test only; no broker outcome transfer is opened.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for primitive in primitives:
        primitive_id = str(primitive.get("primitive_id"))
        coverage = primitive_field_coverage.get(primitive_id, {})
        ledger_rows.append(
            {
                "row_type": "ORDERFLOW_PRIMITIVE_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-PRIMITIVE-{primitive_id}",
                "primitive_id": primitive_id,
                "family": primitive.get("family"),
                "x_lane": primitive.get("x_lane"),
                "current_status": primitive.get("current_status"),
                "roles_to_evaluate": primitive.get("roles_to_evaluate", []),
                "schemas": primitive.get("schemas", []),
                "decision_feature_fields": primitive.get("decision_feature_fields", []),
                "coverage_ratio": coverage.get("coverage_ratio"),
                "available_decision_fields": coverage.get("available_decision_fields", []),
                "missing_decision_fields": coverage.get("missing_decision_fields", []),
                "blocker_codes": primitive.get("blocker_codes", []),
                "threshold_policy": primitive.get("threshold_policy"),
                "decision_boundary": "Primitive registration and field schema only; no threshold or live rule selected.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for blocker in sorted(primitive_status.get("blocker_codes", [])):
        ledger_rows.append(
            {
                "row_type": "ORDERFLOW_SOURCE_BLOCKER_ROW",
                "row_id": f"MAIN-ORCH24-ORDERFLOW-SIERRA-BLOCKER-{blocker}",
                "blocker_code": blocker,
                "affected_primitives": blocker_map.get(blocker, []),
                "decision_boundary": "Blocker remains source-readiness work only; no filter or promotion claim follows from it.",
                "input_hashes": input_hashes,
                "safe_flags": SAFE_FLAGS,
            }
        )

    log_specs = {
        "NAS100_ORDERFLOW_ADVERSE_SELECTION": ["status", "cached_feature_status", "promotion_verdict"],
        "SIERRA_DEPTH_ENRICHMENT": ["status", "promotion_verdict"],
        "SIERRA_CONFLUENCE_SOURCE_STATUS": ["source_status", "interpretation_status", "symbol"],
        "SIERRA_DEPTH_FEATURE_SNAPSHOTS": ["feature_status", "interpretation_status", "symbol"],
        "SIERRA_PROXY_REGISTRY_STATUS": ["proxy_class", "interpretation_status", "symbol"],
        "GBPJPY_PROXY_GAP_STATUS": ["status", "current_proxy_status", "registry_proxy_class"],
        "ORDERFLOW_PRIMITIVES_STATUS": ["status", "promotion_verdict"],
    }
    for label, path in log_paths.items():
        ledger_rows.append(log_snapshot(label, path, log_specs[label]))

    row_type_counts = counter_dict(Counter(row["row_type"] for row in ledger_rows))
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "plate": "orderflow_sierra_diagnostic_capability",
        "output_ledger_rows": len(ledger_rows),
        "row_type_counts": row_type_counts,
        "decision_rows": row_type_counts.get("PLATE_DECISION_ROW", 0),
        "nas100_databento_status": lto011.get("status"),
        "nas100_cached_mbp10_candidate_rows": nested_get(nas100_status, ["current_counts", "cached_mbp10_candidate_rows"]),
        "nas100_cached_mbo_candidate_rows": nested_get(nas100_status, ["current_counts", "cached_mbo_candidate_rows"]),
        "nas100_broker_actual_r_rows": nested_get(nas100_status, ["current_counts", "broker_actual_r_rows_nas100_unique"]),
        "nas100_license_blocker": nested_get(nas100_status, ["databento_live_status", "license_blocker"]),
        "nas100_live_record_rows": nested_get(nas100_status, ["databento_live_status", "live_record_rows"]),
        "sierra_depth_status": lto012.get("status"),
        "sierra_latest_candidate_rows": nested_get(sierra_status, ["current_counts", "latest_candidate_rows"]),
        "sierra_features_extracted": nested_get(sierra_status, ["current_counts", "features_extracted"]),
        "sierra_missing_feature_rows": nested_get(sierra_status, ["current_counts", "missing_feature_rows"]),
        "sierra_background_queue_candidates": nested_get(sierra_status, ["current_counts", "background_queue_candidates"]),
        "sierra_file_size_guard_candidates": nested_get(sierra_status, ["current_counts", "file_size_guard_candidates"]),
        "sierra_pending_heavy_scan_candidates": nested_get(sierra_status, ["current_counts", "pending_heavy_scan_candidates"]),
        "sierra_no_registered_proxy_candidates": nested_get(sierra_status, ["current_counts", "no_registered_proxy_candidates"]),
        "sierra_feature_status_counts": sierra_status.get("feature_status_counts", {}),
        "sierra_interpretation_status_counts": sierra_status.get("interpretation_status_counts", {}),
        "gbpjpy_proxy_status": lto014.get("status"),
        "gbpjpy_candidate_status_rows": len(gbpjpy_candidates),
        "gbpjpy_direct_proxy_registered": nested_get(lto014, ["completion_evidence", "direct_proxy_registered"]),
        "gbpjpy_existing_confluence_inferred": nested_get(lto014, ["completion_evidence", "existing_gbpjpy_confluence_inferred"]),
        "gbpjpy_zero_lag_corr": nested_get(lto014, ["price_transfer_validation", "current_gate_readout", "zero_lag_corr"]),
        "gbpjpy_best_lag_corr": nested_get(lto014, ["price_transfer_validation", "current_gate_readout", "best_lag_corr"]),
        "gbpjpy_best_lag_bars": nested_get(lto014, ["price_transfer_validation", "current_gate_readout", "best_lag_bars"]),
        "gbpjpy_outcomes_opened": nested_get(lto014, ["price_transfer_validation", "no_outcomes_opened"]) is False,
        "orderflow_primitives_status": lto033.get("status"),
        "orderflow_primitive_count": len(primitives),
        "orderflow_blocker_count": len(primitive_status.get("blocker_codes", [])),
        "orderflow_no_lookahead_status": nested_get(primitive_status, ["no_lookahead_check", "status"]),
        "orderflow_field_coverage": {
            primitive_id: coverage.get("coverage_ratio")
            for primitive_id, coverage in sorted(primitive_field_coverage.items())
        },
        "source_log_line_counts": {
            label: len(read_jsonl(path))
            for label, path in sorted(log_paths.items())
        },
        "materialized_decisions": {
            "NAS100_DATABENTO_ORDERFLOW_ADVERSE_SELECTION": "PRESERVE_DIAGNOSTIC_ONLY_WAIT_FOR_LICENSE_AND_SAMPLE_FLOORS",
            "SIERRA_DEPTH_BACKGROUND_QUEUE": "KEEP_SOURCE_CAPTURE_AND_BACKGROUND_QUEUE_NO_LIVE_FILTER",
            "GBPJPY_ORDERFLOW_PROXY_GAP": "KEEP_BLOCKED_NO_PROXY_PRESERVE_PREREGISTERED_TWO_BOOK_DESIGN_ONLY",
            "ORDERFLOW_PRIMITIVE_REGISTRY": "PRESERVE_PRIMITIVES_AS_FEATURE_SCHEMA_AND_SOURCE_BLOCKER_QUEUE_ONLY",
            "SIERRA_PROXY_REGISTRY_BOUNDARY": "PRESERVE_PER_SYMBOL_INTERPRETATION_BOUNDARIES_NO_DATABENTO_EQUIVALENCE_SHORTCUT",
        },
        "plate_decision": "ORDERFLOW_AND_SIERRA_SOURCE_READINESS_MATERIALIZED_AS_DIAGNOSTIC_CAPABILITY_ONLY",
        "next_use_boundary": (
            "Rows support source readiness, field-schema design, proxy boundaries, and future shadow/replay queues only. "
            "They do not authorize a live filter, entry rule, risk modifier, target rule, promotion, validation-safe claim, "
            "paid Databento call, or broker operation."
        ),
        "safe_flags": SAFE_FLAGS,
    }

    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_OUTPUT_MANIFEST_{DATE}.json"

    write_jsonl(ledger_path, ledger_rows)
    write_json(summary_path, summary)

    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 2,
        "artifacts": [
            artifact_record("diagnostic_capability_ledger", ledger_path),
            artifact_record("summary", summary_path),
        ],
        "input_artifacts": [
            artifact_record("lto011_nas100_orderflow_report", lto011_path),
            artifact_record("lto012_sierra_depth_report", lto012_path),
            artifact_record("lto014_gbpjpy_proxy_gap_report", lto014_path),
            artifact_record("lto033_orderflow_primitives_report", lto033_path),
            artifact_record("lto010_databento_policy", lto010_path),
            artifact_record("lto013_sierra_registry", lto013_path),
            artifact_record("lto030_6b_si_policy", lto030_path),
            *[artifact_record(label.lower(), path) for label, path in sorted(log_paths.items())],
        ],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)

    print(
        json.dumps(
            {
                "ok": True,
                "ledger_rows": len(ledger_rows),
                "summary": rel(summary_path),
                "manifest": rel(manifest_path),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

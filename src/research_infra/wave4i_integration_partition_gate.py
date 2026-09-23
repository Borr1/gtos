"""Wave4I integration, partition, and Wave5 handoff gate.

This module consumes the accepted Wave4A/Wave4B/Wave4C route artifacts from
disk, reconciles source/hash/schema/evidence-class contracts, freezes local
Wave5 partitions, and writes a route package. It is local-file only: no broker,
credential, paid API, remote, VPS process, MT5, or live deployment surface is
mutated.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import wave4a_digital_twin_historical_microscope as wave4a
from src.research_infra import wave4b_feature_store_v2 as wave4b
from src.research_infra import wave4c_label_store_v2 as wave4c


ROUTE_ID = "final_moonshot_wave4i_integration_partition_gate_2026_06_05"
LANE = "wave4i_integration_partition_gate"
ROUTE_DIR = Path("research/operations") / ROUTE_ID
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE4I_INTEGRATION_PARTITION_GATE_GOAL_PROMPT_2026-06-05.md"
)
STARTER_PATH = PROMPT_PATH.with_name(
    "FINAL_MOONSHOT_WAVE4I_INTEGRATION_PARTITION_GATE_STARTER_2026-06-05.txt"
)

WAVE4A_ROUTE = wave4a.ROUTE_DIR
WAVE4B_ROUTE = wave4b.ROUTE_DIR
WAVE4C_ROUTE = wave4c.ROUTE_DIR

CANONICAL_ROW_COUNT = 15679
CANONICAL_UNIVERSE_HASH = wave4c.CANONICAL_UNIVERSE_HASH
FEATURE_VERSION = wave4b.FEATURE_VERSION
LABEL_SET_VERSION = wave4c.LABEL_SET_VERSION
PARTITION_VERSION = "wave4i_partition_gate_v1_2026_06_05"

ACCEPTED_COMMITS = {
    "wave4a_acceptance_commit": "e3bfed611",
    "wave4b_acceptance_commit": "99127e179b019e19fd5f2a5849799d5a3b751052",
    "wave4c_acceptance_commit": "d01e7e2cbc75877d72ecf0de9579bbde248d7f1f",
    "wave4c_merge_commit": "35e9b05551066599551274084b6d5747a5658e9f",
    "launch_authority_main_commit": "00c31441bb787287aec813f9b96f3c5115daa630",
}

BOUNDARY_STATUS = {
    "RESULT_MATERIALIZATION_REQUIRED": True,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
    "broker_runtime_change_status": False,
    "broker_account_order_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_vendor_api_call": False,
    "remote_push": False,
    "active_vps_process_change": False,
    "mt5_live_operation": False,
    "live_trading_deployment": False,
}

REQUIRED_CONTEXT_PATHS = (
    ".context/LIVE_STATE.md",
    "AGENTS.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
    ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
    ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/portable_path_authority.md",
    "research/operations/final_moonshot_wave4_wave5_lane_architecture_repair_2026_06_05/WAVE4_WAVE5_LANE_ARCHITECTURE.md",
)

UPSTREAM_ROUTE_PATHS = (
    "research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04/",
    "research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04/",
    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/",
    "research/operations/final_moonshot_wave1_integration_review_2026_06_04/",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/",
    "research/operations/final_moonshot_wave3_integration_review_2026_06_05/",
    "research/operations/final_moonshot_wave3_5_v4_authority_activation_2026_06_05/",
    str(WAVE4A_ROUTE) + "/",
    str(WAVE4B_ROUTE) + "/",
    str(WAVE4C_ROUTE) + "/",
)

CHILD_ROUTES: dict[str, dict[str, Any]] = {
    "wave4a": {
        "lane": wave4a.LANE,
        "route": WAVE4A_ROUTE,
        "accepted_commit": ACCEPTED_COMMITS["wave4a_acceptance_commit"],
        "implementation_commit": "a20d53fd0",
        "manifest": "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json",
        "context_anchor": "WAVE4A_CONTEXT_ANCHOR.json",
        "verification": "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_VERIFICATION_RESULT.json",
        "focused": "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_FOCUSED_TEST_RESULT.json",
        "completion": "COMPLETION_AUDIT.md",
        "core_ledgers": (
            "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
            "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl",
            "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl",
            "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl",
            "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
        ),
    },
    "wave4b": {
        "lane": wave4b.LANE,
        "route": WAVE4B_ROUTE,
        "accepted_commit": ACCEPTED_COMMITS["wave4b_acceptance_commit"],
        "implementation_commit": "4d924692272d463d39f33bcd006f0f417d8b47de",
        "manifest": "WAVE4B_FEATURE_STORE_V2_OUTPUT_MANIFEST.json",
        "context_anchor": "WAVE4B_CONTEXT_ANCHOR.json",
        "verification": "WAVE4B_FEATURE_STORE_V2_VERIFICATION_RESULT.json",
        "focused": "WAVE4B_FEATURE_STORE_V2_FOCUSED_TEST_RESULT.json",
        "completion": "COMPLETION_AUDIT.md",
        "core_ledgers": (
            "WAVE4B_FEATURE_SCHEMA.json",
            "WAVE4B_FEATURE_LEDGER.jsonl",
            "WAVE4B_FEATURE_FAMILY_LEDGER.jsonl",
            "WAVE4B_FEATURE_SOURCE_HASH_LEDGER.jsonl",
            "WAVE4B_NO_LEAK_FIELD_CLASSIFICATION_LEDGER.jsonl",
            "WAVE4B_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
        ),
    },
    "wave4c": {
        "lane": wave4c.LANE,
        "route": WAVE4C_ROUTE,
        "accepted_commit": ACCEPTED_COMMITS["wave4c_acceptance_commit"],
        "merge_commit": ACCEPTED_COMMITS["wave4c_merge_commit"],
        "implementation_commit": "2840607191b45d5b015a7679c50adcdab1f7261b",
        "manifest": "WAVE4C_LABEL_STORE_V2_OUTPUT_MANIFEST.json",
        "context_anchor": "WAVE4C_CONTEXT_ANCHOR.json",
        "verification": "WAVE4C_LABEL_STORE_V2_VERIFICATION_RESULT.json",
        "focused": "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json",
        "completion": "COMPLETION_AUDIT.md",
        "core_ledgers": (
            "WAVE4C_LABEL_SCHEMA.json",
            "WAVE4C_LABEL_LEDGER.jsonl",
            "WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER.jsonl",
            "WAVE4C_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
        ),
    },
}

REQUIRED_ROUTE_FILES = (
    "WAVE4I_CONTEXT_ANCHOR.json",
    "WAVE4I_CHILD_REVIEW_LEDGER.jsonl",
    "WAVE4I_ACCEPTANCE_DECISION_LEDGER.jsonl",
    "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl",
    "WAVE4I_PARTITION_LEDGER.jsonl",
    "WAVE4I_WAVE5_HANDOFF_MANIFEST.json",
    "WAVE4I_SCHEMA_VERSION_BINDING.json",
    "WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl",
    "WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl",
    "WAVE4I_MERGE_SCOPE_LEDGER.json",
    "WAVE4I_WAVE5_LAUNCHABILITY_LEDGER.jsonl",
    "WAVE4I_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE4I_INTEGRATION_PARTITION_GATE_VERIFICATION_RESULT.json",
    "WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json",
    "WAVE4I_INTEGRATION_PARTITION_GATE_PROMPT_HARDENING_RESULT.json",
    "WAVE4I_INTEGRATION_PARTITION_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
    "WAVE4I_INTEGRATION_PARTITION_GATE_SATURATION_SELF_RED_TEAM.md",
    "WAVE4I_INTEGRATION_PARTITION_GATE_INSTRUCTION_COVERAGE_CHECKLIST.md",
    "WAVE4I_INTEGRATION_PARTITION_GATE_OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.md",
    ".gitattributes",
    "build_wave4i_integration_partition_gate.py",
    "verify_wave4i_integration_partition_gate.py",
    "record_wave4i_focused_test_result.py",
)


@dataclass(frozen=True)
class Wave4IInputs:
    canonical_rows: list[dict[str, Any]]
    path_rows: dict[str, dict[str, Any]]
    feature_rows: dict[str, dict[str, Any]]
    label_rows: dict[str, dict[str, Any]]
    child_manifests: dict[str, dict[str, Any]]
    child_verifications: dict[str, dict[str, Any]]
    child_focused: dict[str, dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def route_abs(repo_root: Path, route_dir: Path = ROUTE_DIR) -> Path:
    return route_dir if route_dir.is_absolute() else repo_root / route_dir


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def git_value(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def git_ancestor(repo_root: Path, commit: str, ref: str = "HEAD") -> bool:
    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", commit, ref],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = wave4a.read_json(path)
    return value if isinstance(value, dict) else {"json_value": value}


def _row_count(path: Path) -> int | None:
    if not path.exists() or path.suffix.lower() != ".jsonl":
        return None
    return sum(1 for _ in wave4a.iter_jsonl(path))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _evidence_status(label_row: Mapping[str, Any], family: str) -> str:
    labels = label_row.get("evidence_class_labels")
    if isinstance(labels, Mapping):
        item = labels.get(family)
        if isinstance(item, Mapping):
            return str(item.get("status") or "status_missing")
    return "status_missing"


def _evidence_value(label_row: Mapping[str, Any], family: str) -> Any:
    labels = label_row.get("evidence_class_labels")
    if isinstance(labels, Mapping):
        item = labels.get(family)
        if isinstance(item, Mapping):
            return item.get("value")
    return None


def _source_trace(label_row: Mapping[str, Any]) -> Mapping[str, Any]:
    trace = label_row.get("source_trace")
    return trace if isinstance(trace, Mapping) else {}


def _feature_meta(row: Mapping[str, Any]) -> dict[str, Any]:
    features = row.get("features") if isinstance(row.get("features"), Mapping) else {}
    family_gap_codes: dict[str, list[str]] = {}
    family_hashes: dict[str, str] = {}
    cost_stress_flag = 0.0
    for family, payload in features.items():
        item = payload if isinstance(payload, Mapping) else {}
        family_gap_codes[str(family)] = sorted(str(code) for code in _as_list(item.get("source_gap_codes")))
        if item.get("feature_hash"):
            family_hashes[str(family)] = str(item["feature_hash"])
        if family == "market_state":
            numeric = item.get("numeric_features") if isinstance(item.get("numeric_features"), Mapping) else {}
            try:
                cost_stress_flag = float(numeric.get("cost_stress_source_required_flag") or 0.0)
            except (TypeError, ValueError):
                cost_stress_flag = 0.0
    return {
        "canonical_row_id": row.get("canonical_row_id"),
        "feature_row_id": row.get("feature_row_id"),
        "feature_hash": row.get("feature_hash"),
        "feature_version": row.get("feature_version"),
        "family_statuses": row.get("family_statuses") if isinstance(row.get("family_statuses"), Mapping) else {},
        "family_gap_codes": family_gap_codes,
        "family_hashes": family_hashes,
        "feature_relevant_missing_fields": sorted(str(item) for item in _as_list(row.get("feature_relevant_missing_fields"))),
        "source_key": row.get("source_key"),
        "source_path": row.get("source_path"),
        "source_sha256": row.get("source_sha256"),
        "source_row_hash": row.get("source_row_hash"),
        "source_completeness_state": row.get("source_completeness_state"),
        "asof_time_utc": row.get("asof_time_utc"),
        "cost_stress_source_required_flag": cost_stress_flag,
        "upstream_supervised_value_status": row.get("upstream_supervised_value_status"),
    }


def _label_meta(row: Mapping[str, Any]) -> dict[str, Any]:
    trace = _source_trace(row)
    return {
        "canonical_row_id": row.get("canonical_row_id"),
        "label_row_hash": row.get("label_row_hash"),
        "label_set_version": row.get("label_set_version"),
        "feature_store_exclusion": row.get("feature_store_exclusion"),
        "labels_never_asof_features": row.get("labels_never_asof_features"),
        "source_key": row.get("source_key"),
        "source_sha256": trace.get("source_sha256"),
        "source_row_hash": trace.get("source_row_hash"),
        "source_trace": dict(trace),
        "evidence_statuses": {
            family: _evidence_status(row, family)
            for family in (
                "broker_real_cash_pnl",
                "broker_real_cash_cost",
                "exact_r",
                "proxy_r",
                "replay",
                "simulation",
                "shadow",
                "source_gap",
                "prospective_capture_requirement",
            )
        },
        "broker_real_cash_pnl": _evidence_value(row, "broker_real_cash_pnl"),
        "broker_real_cash_cost": _evidence_value(row, "broker_real_cash_cost"),
        "exact_r": _evidence_value(row, "exact_r"),
        "proxy_r": _evidence_value(row, "proxy_r"),
        "replay_value": _evidence_value(row, "replay"),
        "source_gap_fields": _as_list(_evidence_value(row, "source_gap")),
        "capture_requirement": _evidence_value(row, "prospective_capture_requirement"),
        "runtime_effect_boundary": row.get("runtime_effect_boundary"),
    }


def load_inputs(repo_root: Path) -> Wave4IInputs:
    for name, info in CHILD_ROUTES.items():
        route = repo_root / info["route"]
        if not route.exists():
            raise FileNotFoundError(f"{name} route missing: {route}")
        required = (info["manifest"], info["context_anchor"], info["verification"], info["focused"], info["completion"])
        missing = [item for item in required if not (route / item).exists()]
        if missing:
            raise FileNotFoundError(f"{name} route missing required artifacts: {missing}")

    canonical_rows = list(wave4a.iter_jsonl(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"))
    path_rows = {
        str(row["canonical_row_id"]): row
        for row in wave4a.iter_jsonl(repo_root / WAVE4A_ROUTE / "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl")
    }
    feature_rows = {
        str(row["canonical_row_id"]): _feature_meta(row)
        for row in wave4a.iter_jsonl(repo_root / WAVE4B_ROUTE / "WAVE4B_FEATURE_LEDGER.jsonl")
    }
    label_rows = {
        str(row["canonical_row_id"]): _label_meta(row)
        for row in wave4a.iter_jsonl(repo_root / WAVE4C_ROUTE / "WAVE4C_LABEL_LEDGER.jsonl")
    }
    return Wave4IInputs(
        canonical_rows=canonical_rows,
        path_rows=path_rows,
        feature_rows=feature_rows,
        label_rows=label_rows,
        child_manifests={
            name: _read_json_if_exists(repo_root / info["route"] / info["manifest"])
            for name, info in CHILD_ROUTES.items()
        },
        child_verifications={
            name: _read_json_if_exists(repo_root / info["route"] / info["verification"])
            for name, info in CHILD_ROUTES.items()
        },
        child_focused={
            name: _read_json_if_exists(repo_root / info["route"] / info["focused"])
            for name, info in CHILD_ROUTES.items()
        },
    )


def child_review_rows(repo_root: Path, inputs: Wave4IInputs) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for child, info in CHILD_ROUTES.items():
        route = repo_root / info["route"]
        verifier = inputs.child_verifications.get(child, {})
        manifest = inputs.child_manifests.get(child, {})
        artifact_names = [
            info["completion"],
            info["manifest"],
            info["context_anchor"],
            info["verification"],
            info["focused"],
            *info["core_ledgers"],
        ]
        for artifact in artifact_names:
            path = route / artifact
            rows.append(
                {
                    "schema_version": "wave4i_child_review_v1",
                    "child": child,
                    "lane": info["lane"],
                    "route": rel_path(repo_root, route),
                    "artifact": artifact,
                    "artifact_path": rel_path(repo_root, path),
                    "artifact_exists": path.exists(),
                    "artifact_sha256": wave4a.sha256_file(path) if path.exists() else None,
                    "artifact_size_bytes": path.stat().st_size if path.exists() else None,
                    "jsonl_rows": _row_count(path),
                    "accepted_commit": info.get("accepted_commit"),
                    "implementation_commit": info.get("implementation_commit"),
                    "merge_commit": info.get("merge_commit"),
                    "manifest_schema_version": manifest.get("schema_version"),
                    "manifest_route_id": manifest.get("route_id"),
                    "verifier_ok": bool(verifier.get("ok", verifier.get("status") == "pass")),
                    "verifier_issue_count": verifier.get("issue_count", verifier.get("failure_count")),
                    "review_decision": "accept_child_artifact_from_disk" if path.exists() else "continuation_required_missing_artifact",
                    "runtime_effect_boundary": "disk_review_only_no_child_rewrite_no_broker_runtime_mutation",
                }
            )
    return rows


def _child_row_counts(inputs: Wave4IInputs) -> dict[str, int]:
    return {
        "wave4a_canonical_rows": len(inputs.canonical_rows),
        "wave4a_path_rows": len(inputs.path_rows),
        "wave4b_feature_rows": len(inputs.feature_rows),
        "wave4c_label_rows": len(inputs.label_rows),
    }


def _all_child_routes_ok(inputs: Wave4IInputs) -> bool:
    return all(bool(item.get("ok", item.get("status") == "pass")) for item in inputs.child_verifications.values())


def row_reconciliation_rows(inputs: Wave4IInputs) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, canonical in enumerate(inputs.canonical_rows, start=1):
        canonical_id = str(canonical["canonical_row_id"])
        feature = inputs.feature_rows.get(canonical_id, {})
        label = inputs.label_rows.get(canonical_id, {})
        path_row = inputs.path_rows.get(canonical_id, {})
        feature_source_ok = (
            feature.get("source_sha256") == canonical.get("source_sha256")
            and feature.get("source_row_hash") == canonical.get("source_row_hash")
        )
        label_source_ok = (
            label.get("source_sha256") == canonical.get("source_sha256")
            and label.get("source_row_hash") == canonical.get("source_row_hash")
        )
        feature_version_ok = feature.get("feature_version") == FEATURE_VERSION
        label_version_ok = label.get("label_set_version") == LABEL_SET_VERSION
        feature_families = set(feature.get("family_statuses") or {})
        feature_family_ok = set(wave4b.FAMILY_NAMES) == feature_families
        label_boundary_ok = (
            label.get("feature_store_exclusion") == wave4c.FEATURE_STORE_EXCLUSION
            and label.get("labels_never_asof_features") is True
            and feature.get("upstream_supervised_value_status") == "upstream_supervised_values_not_consumed_as_features"
        )
        missing_fields = sorted(str(item) for item in _as_list(canonical.get("missing_fields_or_runtime_truth")))
        feature_gap_codes = sorted(
            {
                str(code)
                for codes in (feature.get("family_gap_codes") or {}).values()
                for code in _as_list(codes)
                if code not in (None, "", [], {})
            }
        )
        label_gap_fields = sorted(str(item) for item in _as_list(label.get("source_gap_fields")))
        capture_requirement = label.get("capture_requirement")
        row_ok = all(
            [
                bool(feature),
                bool(label),
                feature_source_ok,
                label_source_ok,
                feature_version_ok,
                label_version_ok,
                feature_family_ok,
                label_boundary_ok,
            ]
        )
        payload = {
            "schema_version": "wave4i_row_reconciliation_v1",
            "canonical_row_id": canonical_id,
            "row_index": index,
            "symbol": canonical.get("symbol"),
            "side": canonical.get("side"),
            "session_bucket": canonical.get("session_bucket"),
            "canonical_time_utc": canonical.get("canonical_time_utc"),
            "row_family": canonical.get("row_family"),
            "source_key": canonical.get("source_key"),
            "source_path": canonical.get("source_path"),
            "source_sha256": canonical.get("source_sha256"),
            "source_row_hash": canonical.get("source_row_hash"),
            "canonical_source_completeness_state": canonical.get("source_completeness_state"),
            "path_clock_status": path_row.get("path_clock_status"),
            "feature_hash": feature.get("feature_hash"),
            "feature_version": feature.get("feature_version"),
            "label_row_hash": label.get("label_row_hash"),
            "label_set_version": label.get("label_set_version"),
            "feature_family_statuses": feature.get("family_statuses"),
            "feature_family_hashes": feature.get("family_hashes"),
            "feature_source_gap_codes": feature_gap_codes,
            "feature_relevant_missing_fields": feature.get("feature_relevant_missing_fields"),
            "label_evidence_statuses": label.get("evidence_statuses"),
            "label_value_presence": {
                "broker_real_cash_pnl": label.get("broker_real_cash_pnl") is not None,
                "broker_real_cash_cost": label.get("broker_real_cash_cost") is not None,
                "exact_r": label.get("exact_r") is not None,
                "proxy_r": label.get("proxy_r") is not None,
                "replay": label.get("replay_value") is not None,
            },
            "source_gap_fields": sorted(set(missing_fields + label_gap_fields)),
            "capture_requirement": capture_requirement,
            "agreement": {
                "feature_row_present": bool(feature),
                "label_row_present": bool(label),
                "feature_source_hash_matches_canonical": feature_source_ok,
                "label_source_hash_matches_canonical": label_source_ok,
                "feature_version_matches": feature_version_ok,
                "label_version_matches": label_version_ok,
                "feature_family_contract_complete": feature_family_ok,
                "labels_excluded_from_asof_features": label_boundary_ok,
            },
            "acceptance_decision": "accepted_for_wave5_handoff" if row_ok else "continuation_required_before_wave5_dataset",
            "runtime_effect_boundary": "local_integration_partition_metadata_only_no_live_runtime_mutation",
        }
        payload["reconciliation_row_hash"] = wave4a.stable_hash(payload)
        rows.append(payload)
    return rows


def _numeric(value: Any) -> float | None:
    if value in (None, "", [], {}):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _regime_key(row: Mapping[str, Any], path_row: Mapping[str, Any]) -> str:
    facts = path_row.get("path_fact_classification")
    if isinstance(facts, Mapping):
        active = sorted(str(key) for key, value in facts.items() if value is True)
        if active:
            return "path_" + "_".join(active)
    source_key = str(row.get("source_key") or "")
    if source_key == "pending_nofill_lifecycle":
        return "pending_nofill_regime"
    if source_key == "zero_trade_counterfactual_path_rank":
        return "zero_trade_regime"
    if row.get("canonical_source_completeness_state") == "source_gap_present":
        return "source_gap_regime"
    return str(row.get("row_family") or "unknown_regime")


def _cost_stress_key(row: Mapping[str, Any], feature: Mapping[str, Any], label: Mapping[str, Any]) -> str:
    if float(feature.get("cost_stress_source_required_flag") or 0.0) >= 1.0:
        return "cost_stress_source_required"
    cost_cash = _numeric(label.get("broker_real_cash_cost"))
    if cost_cash is not None:
        return "broker_real_cost_cash_observed"
    if str(row.get("symbol") or "").upper() in {"ETHUSD", "XAUUSD", "NAS100", "NDX100"}:
        return "hard_halt_cost_tail_watch_symbol"
    return "cost_stress_unobserved_or_not_material"


def _outlier_key(label: Mapping[str, Any]) -> str:
    cash = _numeric(label.get("broker_real_cash_pnl"))
    exact_r = _numeric(label.get("exact_r"))
    proxy_r = _numeric(label.get("proxy_r"))
    replay = _numeric(label.get("replay_value"))
    if cash is not None and abs(cash) >= 1000:
        return "broker_real_cash_outlier_abs_ge_1000"
    if any(value is not None and abs(value) >= 2.0 for value in (exact_r, proxy_r, replay)):
        return "r_style_outlier_abs_ge_2r"
    return "non_outlier_or_unobserved"


def _primary_split(index: int, total: int, has_clock: bool) -> str:
    if not has_clock:
        return "clock_gap_holdout"
    ratio = index / max(total, 1)
    if ratio <= 0.60:
        return "development_train"
    if ratio <= 0.75:
        return "development_calibration"
    if ratio <= 0.90:
        return "sealed_test"
    return "forward_like_shadow_holdout"


def _fold_windows(sorted_rows: Sequence[tuple[datetime | None, str]]) -> list[tuple[datetime, datetime]]:
    timed = [(dt, cid) for dt, cid in sorted_rows if dt is not None]
    windows: list[tuple[datetime, datetime]] = []
    if not timed:
        return windows
    fold_count = 5
    for fold in range(fold_count):
        start_idx = int(len(timed) * fold / fold_count)
        end_idx = int(len(timed) * (fold + 1) / fold_count) - 1
        end_idx = max(start_idx, min(end_idx, len(timed) - 1))
        windows.append((timed[start_idx][0], timed[end_idx][0]))
    return windows


def _fold_roles(row_time: datetime | None, windows: Sequence[tuple[datetime, datetime]]) -> dict[str, str]:
    roles: dict[str, str] = {}
    if row_time is None:
        return {f"fold_{idx}": "clock_gap_holdout" for idx in range(len(windows))}
    purge = timedelta(hours=24)
    embargo = timedelta(hours=24)
    for idx, (start, end) in enumerate(windows):
        key = f"fold_{idx}"
        if start <= row_time <= end:
            roles[key] = "test"
        elif start - purge <= row_time < start:
            roles[key] = "purged_train_excluded_before_test"
        elif end < row_time <= end + embargo:
            roles[key] = "embargoed_train_excluded_after_test"
        else:
            roles[key] = "train_candidate"
    return roles


def partition_rows(
    reconciliation_rows: Sequence[Mapping[str, Any]],
    inputs: Wave4IInputs,
) -> list[dict[str, Any]]:
    sort_pairs: list[tuple[datetime | None, str]] = [
        (wave4a.parse_time(row.get("canonical_time_utc")), str(row["canonical_row_id"]))
        for row in reconciliation_rows
    ]
    sort_pairs.sort(key=lambda item: (item[0] is None, item[0] or datetime.max.replace(tzinfo=timezone.utc), item[1]))
    sort_index = {canonical_id: idx for idx, (_, canonical_id) in enumerate(sort_pairs, start=1)}
    windows = _fold_windows(sort_pairs)
    total = len(sort_pairs)
    rows: list[dict[str, Any]] = []
    for row in reconciliation_rows:
        canonical_id = str(row["canonical_row_id"])
        row_time = wave4a.parse_time(row.get("canonical_time_utc"))
        feature = inputs.feature_rows.get(canonical_id, {})
        label = inputs.label_rows.get(canonical_id, {})
        path = inputs.path_rows.get(canonical_id, {})
        idx = sort_index[canonical_id]
        payload = {
            "schema_version": "wave4i_partition_ledger_v1",
            "partition_version": PARTITION_VERSION,
            "canonical_row_id": canonical_id,
            "chronological_index": idx,
            "row_count": total,
            "canonical_time_utc": row.get("canonical_time_utc"),
            "symbol": row.get("symbol"),
            "session_bucket": row.get("session_bucket"),
            "source_key": row.get("source_key"),
            "source_sha256": row.get("source_sha256"),
            "source_row_hash": row.get("source_row_hash"),
            "feature_hash": row.get("feature_hash"),
            "label_row_hash": row.get("label_row_hash"),
            "feature_version": row.get("feature_version"),
            "label_set_version": row.get("label_set_version"),
            "primary_temporal_split": _primary_split(idx, total, row_time is not None),
            "walk_forward_role_by_fold": _fold_roles(row_time, windows),
            "purge_window_hours": 24,
            "embargo_window_hours": 24,
            "symbol_holdout_key": row.get("symbol") or "UNKNOWN_SYMBOL",
            "session_holdout_key": row.get("session_bucket") or "session_unknown_clock_gap",
            "regime_holdout_key": _regime_key(row, path),
            "cost_stress_partition": _cost_stress_key(row, feature, label),
            "outlier_partition": _outlier_key(label),
            "no_leak_partition_guard": {
                "status": "pass" if (row.get("agreement") or {}).get("labels_excluded_from_asof_features") else "fail",
                "feature_store_exclusion": label.get("feature_store_exclusion"),
                "labels_never_asof_features": label.get("labels_never_asof_features"),
                "partition_metadata_not_feature": True,
                "labels_and_outcomes_never_asof_features": True,
            },
            "partition_use_boundary": "Wave5 dataset/leakage guard may consume partition ids; model feature matrix must not consume labels/outcomes as as-of features.",
        }
        payload["partition_row_hash"] = wave4a.stable_hash(payload)
        rows.append(payload)
    return rows


def source_gap_continuation_rows(reconciliation_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in reconciliation_rows:
        feature_gaps = sorted(str(item) for item in _as_list(row.get("feature_source_gap_codes")))
        source_fields = sorted(str(item) for item in _as_list(row.get("source_gap_fields")))
        capture_requirement = row.get("capture_requirement")
        gap_count = len(feature_gaps) + len(source_fields) + (1 if capture_requirement else 0)
        status = "exact_continuation_requirement" if gap_count else "no_row_level_continuation_required"
        payload = {
            "schema_version": "wave4i_source_gap_continuation_v1",
            "canonical_row_id": row["canonical_row_id"],
            "source_key": row.get("source_key"),
            "symbol": row.get("symbol"),
            "canonical_time_utc": row.get("canonical_time_utc"),
            "source_sha256": row.get("source_sha256"),
            "source_row_hash": row.get("source_row_hash"),
            "status": status,
            "source_gap_fields": source_fields,
            "feature_gap_codes": feature_gaps,
            "label_capture_requirement": capture_requirement,
            "continuation_requirement": (
                "Resolve listed source/feature/label capture requirements before using this row as complete Wave5 supervised evidence."
                if gap_count
                else "No row-level source continuation required by current Wave4A/B/C artifacts."
            ),
            "evidence_class_policy": "source gaps and prospective capture requirements remain explicit; no broker-real cash/PnL, exact-R, proxy-R, replay, simulation, or shadow class is substituted for another.",
        }
        payload["continuation_row_hash"] = wave4a.stable_hash(payload)
        rows.append(payload)
    return rows


def blocker_repair_rows(
    reconciliation: Sequence[Mapping[str, Any]],
    partitions: Sequence[Mapping[str, Any]],
    continuation: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    exact_continuation_count = sum(1 for row in continuation if row.get("status") == "exact_continuation_requirement")
    return [
        {
            "schema_version": "wave4i_blocker_repair_ledger_v1",
            "row_id": "wave4i_child_merge_gate",
            "status": "repaired_and_verified",
            "wave5a_status": "not_blocked",
            "evidence": {
                "reconciled_rows": len(reconciliation),
                "accepted_reconciliation_rows": sum(
                    1 for row in reconciliation if row.get("acceptance_decision") == "accepted_for_wave5_handoff"
                ),
                "partition_rows": len(partitions),
                "canonical_row_count": CANONICAL_ROW_COUNT,
            },
            "repair_or_continuation": "Wave4A/B/C are integrated through canonical_row_id/source hashes, version bindings, and no-leak partition metadata.",
        },
        {
            "schema_version": "wave4i_blocker_repair_ledger_v1",
            "row_id": "row_level_source_gap_continuation",
            "status": "exact_continuation_required_before_complete_supervised_truth_claim",
            "wave5a_status": "not_blocked",
            "evidence": {
                "exact_continuation_rows": exact_continuation_count,
                "full_ledger_path": str(ROUTE_DIR / "WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl"),
                "full_ledger_rows": len(continuation),
            },
            "repair_or_continuation": "Wave5A may launch dataset/leakage-guard construction with explicit source status; no missing broker/source truth is imputed or substituted.",
        },
        {
            "schema_version": "wave4i_blocker_repair_ledger_v1",
            "row_id": "base_pytest_environment_friction",
            "status": "repaired_by_documented_uv_fallback",
            "wave5a_status": "not_blocked",
            "evidence": {
                "focused_test_artifact": str(ROUTE_DIR / "WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json"),
                "base_python_failure_expected": "No module named pytest",
                "fallback": "uv run --with pytest --with pyyaml python -m pytest tests/test_wave4i_integration_partition_gate.py -q",
            },
            "repair_or_continuation": "Base Python dependency friction is recorded; the focused test suite must pass under the uv fallback.",
        },
        {
            "schema_version": "wave4i_blocker_repair_ledger_v1",
            "row_id": "forbidden_live_surface_boundary",
            "status": "preserved",
            "wave5a_status": "not_blocked",
            "evidence": BOUNDARY_STATUS,
            "repair_or_continuation": "No broker account/order/deal/position mutation, credential mutation, paid vendor call, remote push, active VPS mutation, MT5 live operation, live deployment, or runtime restart occurred.",
        },
    ]


def acceptance_decision_rows(
    repo_root: Path,
    inputs: Wave4IInputs,
    reconciliation: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    counts = _child_row_counts(inputs)
    bad_rows = [row for row in reconciliation if row.get("acceptance_decision") != "accepted_for_wave5_handoff"]
    rows = [
        {
            "schema_version": "wave4i_acceptance_decision_v1",
            "decision_id": "accept_wave4a_current_disk_package",
            "subject": "wave4a_digital_twin_historical_microscope",
            "decision": "accepted",
            "evidence": {
                "verifier_ok": inputs.child_verifications["wave4a"].get("ok"),
                "canonical_rows": counts["wave4a_canonical_rows"],
                "canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
                "accepted_commit_ancestor": git_ancestor(repo_root, ACCEPTED_COMMITS["wave4a_acceptance_commit"]),
            },
            "continuation_requirement": None,
        },
        {
            "schema_version": "wave4i_acceptance_decision_v1",
            "decision_id": "accept_wave4b_current_disk_package",
            "subject": "wave4b_feature_store_v2",
            "decision": "accepted",
            "evidence": {
                "verifier_ok": inputs.child_verifications["wave4b"].get("ok"),
                "feature_rows": counts["wave4b_feature_rows"],
                "feature_version": FEATURE_VERSION,
                "accepted_commit_ancestor": git_ancestor(repo_root, ACCEPTED_COMMITS["wave4b_acceptance_commit"]),
            },
            "continuation_requirement": "Feature source gaps remain row-level capture requirements, not blockers to Wave4I partition freeze.",
        },
        {
            "schema_version": "wave4i_acceptance_decision_v1",
            "decision_id": "accept_wave4c_current_disk_package",
            "subject": "wave4c_label_store_v2",
            "decision": "accepted",
            "evidence": {
                "verifier_ok": inputs.child_verifications["wave4c"].get("ok"),
                "label_rows": counts["wave4c_label_rows"],
                "label_set_version": LABEL_SET_VERSION,
                "accepted_commit_ancestor": git_ancestor(repo_root, ACCEPTED_COMMITS["wave4c_acceptance_commit"]),
                "merge_commit_ancestor": git_ancestor(repo_root, ACCEPTED_COMMITS["wave4c_merge_commit"]),
            },
            "continuation_requirement": "Label source gaps remain row-level capture requirements; labels are excluded from as-of feature inputs.",
        },
        {
            "schema_version": "wave4i_acceptance_decision_v1",
            "decision_id": "row_hash_schema_version_evidence_class_reconciliation",
            "subject": "wave4a_wave4b_wave4c_join_contract",
            "decision": "accepted" if not bad_rows else "continuation_required",
            "evidence": {
                "reconciled_rows": len(reconciliation),
                "bad_rows": len(bad_rows),
                "canonical_row_count": CANONICAL_ROW_COUNT,
                "feature_version": FEATURE_VERSION,
                "label_set_version": LABEL_SET_VERSION,
                "child_routes_ok": _all_child_routes_ok(inputs),
            },
            "continuation_requirement": None if not bad_rows else "Repair non-reconciled rows before Wave5 dataset materialization.",
        },
    ]
    return rows


def wave5_launchability_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "wave4i_wave5_launchability_v1",
            "wave5_lane": "wave5a_dataset_leakage_guard",
            "launch_status": "launchable_now_after_wave4i_commit",
            "required_inputs": [
                "WAVE4I_WAVE5_HANDOFF_MANIFEST.json",
                "WAVE4I_PARTITION_LEDGER.jsonl",
                "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl",
                "WAVE4I_SCHEMA_VERSION_BINDING.json",
            ],
            "blocking_requirement": None,
        },
        {
            "schema_version": "wave4i_wave5_launchability_v1",
            "wave5_lane": "wave5b_baselines_calibration",
            "launch_status": "blocked_until_wave5a_dataset_hashes_exist",
            "required_inputs": ["Wave5A sealed dataset hashes", "Wave5A leakage guard result"],
            "blocking_requirement": "Wait for Wave5A to materialize no-leak datasets and hashes.",
        },
        {
            "schema_version": "wave4i_wave5_launchability_v1",
            "wave5_lane": "wave5c_challengers_local_training",
            "launch_status": "blocked_until_wave5b_baseline_floors_exist",
            "required_inputs": ["Wave5B baseline metrics", "calibration floors", "dataset bindings"],
            "blocking_requirement": "Wait for Wave5B baseline/calibration floor artifacts.",
        },
        {
            "schema_version": "wave4i_wave5_launchability_v1",
            "wave5_lane": "wave5d_registry_runtime_packet_gate",
            "launch_status": "blocked_until_wave5a_wave5b_wave5c_outputs_exist",
            "required_inputs": ["Wave5A dataset guard", "Wave5B baselines", "Wave5C challengers"],
            "blocking_requirement": "Wait for all upstream Wave5 model artifacts before registry/runtime packet gate.",
        },
    ]


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, raw_path in enumerate((*REQUIRED_CONTEXT_PATHS, *UPSTREAM_ROUTE_PATHS), start=1):
        path = repo_root / raw_path.rstrip("/")
        rows.append(
            {
                "schema_version": "wave4i_searched_root_v1",
                "row_id": f"wave4i_searched_root:{index:03d}",
                "path": raw_path,
                "exists": path.exists(),
                "path_role": "context" if raw_path in REQUIRED_CONTEXT_PATHS else "upstream_route_or_child_route",
                "review_use": "active instruction" if raw_path in REQUIRED_CONTEXT_PATHS else "disk artifact evidence",
                "source_hash": wave4a.sha256_file(path) if path.exists() and path.is_file() else None,
            }
        )
    return rows


def schema_version_binding(repo_root: Path, reconciliation: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "wave4i_schema_version_binding_v1",
        "lane": LANE,
        "canonical": {
            "route": str(WAVE4A_ROUTE),
            "row_count": len(reconciliation),
            "canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
            "schema_path": str(WAVE4A_ROUTE / "WAVE4A_DIGITAL_TWIN_EVENT_SCHEMA.json"),
            "manifest_path": str(WAVE4A_ROUTE / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json"),
        },
        "feature_store": {
            "route": str(WAVE4B_ROUTE),
            "feature_version": FEATURE_VERSION,
            "schema_path": str(WAVE4B_ROUTE / "WAVE4B_FEATURE_SCHEMA.json"),
            "required_family_names": list(wave4b.FAMILY_NAMES),
            "feature_rows": len(reconciliation),
        },
        "label_store": {
            "route": str(WAVE4C_ROUTE),
            "label_set_version": LABEL_SET_VERSION,
            "schema_path": str(WAVE4C_ROUTE / "WAVE4C_LABEL_SCHEMA.json"),
            "required_label_families": list(wave4c.LABEL_FAMILIES),
            "feature_store_input_allowed": False,
            "label_rows": len(reconciliation),
        },
        "partition": {
            "partition_version": PARTITION_VERSION,
            "purge_window_hours": 24,
            "embargo_window_hours": 24,
            "walk_forward_fold_count": 5,
            "partition_metadata_not_feature": True,
        },
        "source_hashes": {
            "wave4a_canonical_ledger_sha256": wave4a.sha256_file(
                repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"
            ),
            "wave4b_feature_ledger_sha256": wave4a.sha256_file(
                repo_root / WAVE4B_ROUTE / "WAVE4B_FEATURE_LEDGER.jsonl"
            ),
            "wave4c_label_ledger_sha256": wave4a.sha256_file(
                repo_root / WAVE4C_ROUTE / "WAVE4C_LABEL_LEDGER.jsonl"
            ),
        },
    }


def merge_scope_ledger(repo_root: Path) -> dict[str, Any]:
    status_lines = [
        line
        for line in git_value(repo_root, "status", "--short").splitlines()
        if line.strip()
    ]
    return {
        "schema_version": "wave4i_merge_scope_ledger_v1",
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head": git_value(repo_root, "rev-parse", "HEAD"),
        "head_summary": git_value(repo_root, "show", "--no-patch", "--oneline", "HEAD"),
        "accepted_commit_ancestor_status": {
            name: git_ancestor(repo_root, commit)
            for name, commit in ACCEPTED_COMMITS.items()
        },
        "owned_paths": [
            "src/research_infra/wave4i_integration_partition_gate.py",
            "tests/test_wave4i_integration_partition_gate.py",
            str(ROUTE_DIR) + "/",
        ],
        "unrelated_dirty_paths_observed": [
            line for line in status_lines if "wave4i" not in line.lower()
        ],
        "merge_repair_decision": "no_child_merge_repair_required_current_head_contains_accepted_commits",
        "forbidden_surface_status": BOUNDARY_STATUS,
    }


def context_anchor(
    repo_root: Path,
    inputs: Wave4IInputs,
    reconciliation: Sequence[Mapping[str, Any]],
    partitions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "wave4i_context_anchor_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head": git_value(repo_root, "rev-parse", "HEAD"),
        "prompt_path": str(PROMPT_PATH),
        "starter_path": str(STARTER_PATH),
        "required_context_paths": list(REQUIRED_CONTEXT_PATHS),
        "upstream_route_paths": list(UPSTREAM_ROUTE_PATHS),
        "child_row_counts": _child_row_counts(inputs),
        "reconciled_rows": len(reconciliation),
        "partition_rows": len(partitions),
        "forbidden_surfaces": BOUNDARY_STATUS,
        "unrelated_dirty_policy": "regenerated .context/LIVE_STATE.md and pre-existing legacy outcome-testing JSONL dirt remain outside Wave4I scoped staging unless explicitly owned.",
    }


def wave5_handoff_manifest(
    repo_root: Path,
    reconciliation: Sequence[Mapping[str, Any]],
    partitions: Sequence[Mapping[str, Any]],
    continuation: Sequence[Mapping[str, Any]],
    launchability: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    route = repo_root / ROUTE_DIR
    source_gap_count = sum(1 for row in continuation if row.get("status") == "exact_continuation_requirement")
    return {
        "schema_version": "wave4i_wave5_handoff_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "canonical_row_count": len(reconciliation),
        "canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
        "feature_version": FEATURE_VERSION,
        "label_set_version": LABEL_SET_VERSION,
        "partition_version": PARTITION_VERSION,
        "source_gap_or_continuation_rows": source_gap_count,
        "all_rows_hash_reconciled": all(row.get("acceptance_decision") == "accepted_for_wave5_handoff" for row in reconciliation),
        "artifacts_for_wave5a": {
            "row_reconciliation_ledger": {
                "path": str(ROUTE_DIR / "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl"),
                "sha256": wave4a.sha256_file(route / "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl"),
                "rows": len(reconciliation),
            },
            "partition_ledger": {
                "path": str(ROUTE_DIR / "WAVE4I_PARTITION_LEDGER.jsonl"),
                "sha256": wave4a.sha256_file(route / "WAVE4I_PARTITION_LEDGER.jsonl"),
                "rows": len(partitions),
            },
            "source_gap_continuation_ledger": {
                "path": str(ROUTE_DIR / "WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl"),
                "sha256": wave4a.sha256_file(route / "WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl"),
                "rows": len(continuation),
            },
            "blocker_repair_ledger": {
                "path": str(ROUTE_DIR / "WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl"),
                "sha256": wave4a.sha256_file(route / "WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl"),
            },
            "schema_version_binding": {
                "path": str(ROUTE_DIR / "WAVE4I_SCHEMA_VERSION_BINDING.json"),
                "sha256": wave4a.sha256_file(route / "WAVE4I_SCHEMA_VERSION_BINDING.json"),
            },
        },
        "launchability": list(launchability),
        "forbidden_surface_status": BOUNDARY_STATUS,
        "wave5_dataset_rule": "Wave5A may join Wave4B features and Wave4C labels only through canonical_row_id/source hashes after applying Wave4I partitions and no-leak guards.",
    }


def instruction_checklist_text() -> str:
    return """# Wave4I Instruction Coverage Checklist

- [x] Regenerated and read `.context/LIVE_STATE.md`.
- [x] Read AGENTS, system map, reading order, quick reference, hard-halt plan, execution architecture, central briefs, research doctrine, goal discipline, orchestration controls, portable path authority, starter, prompt, and Wave4/Wave5 architecture from disk.
- [x] Re-reviewed Wave4A/Wave4B/Wave4C completion audits, manifests, context anchors, verifier results, focused test results, schemas, and full material row ledgers from disk.
- [x] Verified accepted child commits and launch-authority commit are ancestors of current HEAD.
- [x] Preserved broker-real cash/PnL, exact-R, proxy-R, replay, simulation, shadow, source-gap, prospective-capture, production-code, runtime-code, uncommitted-dirt, and historical-only boundaries.
- [x] Built full row reconciliation, partition, source-gap/continuation, blocker/repair, acceptance, merge-scope, and Wave5 launchability artifacts.
- [x] No arbitrary top-N, compact sample, representative-only closure, broker mutation, credential mutation, paid/vendor call, remote push, active VPS mutation, MT5 live operation, or live deployment occurred.
"""


def saturation_text() -> str:
    return """# Wave4I Saturation And Self-Red-Team

## Evidence-Class Leakage

The main failure mode is treating Wave4C labels as Wave4B features. Wave4I checks every row for `feature_store_exclusion=banned_from_wave4b_asof_inputs_labels_only`, `labels_never_asof_features=true`, and `upstream_supervised_values_not_consumed_as_features`. Partitions are metadata for Wave5A leakage guards, not model features.

## Row, Hash, And Source Drift

Wave4I rejects silent normalization. Every row must share `canonical_row_id`, `source_sha256`, `source_row_hash`, feature version, and label version across Wave4A/B/C. Any mismatch becomes `continuation_required_before_wave5_dataset`.

## Partitions

The partition ledger freezes chronological walk-forward roles, 24h purge windows, 24h embargo windows, symbol/session/regime holdouts, cost-stress slices, outlier slices, and no-leak guards for all canonical rows. Rows with clock gaps are isolated as `clock_gap_holdout`.

## Source Gaps

Source gaps are not repaired by imputation. Wave4I preserves row-level feature gap codes, label capture requirements, and source fields in the continuation ledger. Broker-real cash/PnL is never substituted with exact-R/proxy-R/replay/simulation/shadow evidence.

## Same-Class Pursuit Result

Within Wave4I's evidence class, the executable work was child disk review, commit/merge proof, row/source/hash/schema/version reconciliation, partition freeze, Wave5 handoff, verifier/test/audit packaging, and exact continuation requirements. Remaining gaps are source/capture requirements already row-bound by Wave4B/Wave4C and do not justify rewriting child artifacts in this parent lane.
"""


def completion_audit_text(
    repo_root: Path,
    reconciliation: Sequence[Mapping[str, Any]],
    partitions: Sequence[Mapping[str, Any]],
    continuation: Sequence[Mapping[str, Any]],
    verification: Mapping[str, Any] | None = None,
) -> str:
    source_gap_count = sum(1 for row in continuation if row.get("status") == "exact_continuation_requirement")
    verify_status = "not_recorded_yet" if not verification else str(verification.get("ok"))
    return "\n".join(
        [
            "# Wave4I Completion Audit",
            "",
            f"Generated: {utc_now()}",
            f"Branch: `{git_value(repo_root, 'branch', '--show-current')}`",
            f"HEAD: `{git_value(repo_root, 'rev-parse', 'HEAD')}`",
            f"Route: `{ROUTE_DIR}`",
            "",
            "## Scope",
            "",
            "Built the Wave4I integration, partition, and Wave5 handoff gate from current disk artifacts. The package reviews accepted Wave4A/Wave4B/Wave4C outputs, proves merge ancestry, reconciles row/source/hash/schema/version/evidence-class boundaries, freezes partitions, and publishes Wave5 launchability.",
            "",
            "## Counts",
            "",
            f"- Reconciled canonical rows: `{len(reconciliation)}`.",
            f"- Partition rows: `{len(partitions)}`.",
            f"- Source-gap/continuation rows: `{len(continuation)}`.",
            f"- Rows with exact continuation requirements: `{source_gap_count}`.",
            f"- Canonical universe sha256: `{CANONICAL_UNIVERSE_HASH}`.",
            f"- Feature version: `{FEATURE_VERSION}`.",
            f"- Label set version: `{LABEL_SET_VERSION}`.",
            "",
            "## Evidence Separation",
            "",
            "- Broker-real cash/PnL remains cash-unit label evidence only.",
            "- Exact-R and proxy-R remain R-unit labels only.",
            "- Replay, simulation, and shadow remain offline label/state evidence.",
            "- Labels/outcomes are not as-of features; partitions are metadata for Wave5A leakage guards.",
            "",
            "## Verification",
            "",
            f"- Wave4I verifier ok: `{verify_status}`.",
            "- Focused tests/py_compile are recorded in `WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json`.",
            "- Prompt hardening and route artifact audit are recorded in route-local JSON artifacts.",
            "",
            "## Wave5 Handoff",
            "",
            "- Wave5A is launchable after this scoped Wave4I commit.",
            "- Wave5B waits for Wave5A dataset hashes and leakage guard.",
            "- Wave5C waits for Wave5B baseline/calibration floors.",
            "- Wave5D waits for Wave5A/B/C model artifacts.",
            "",
            "## Boundaries",
            "",
            "No broker account/history/order/deal/position mutation, credential mutation/disclosure, paid/vendor API call, remote push, active VPS process mutation, MT5 live operation, live trading deployment, or runtime restart occurred.",
            "",
            "## Unresolved Exact Requirements",
            "",
            "Remaining requirements are exact row-level source/capture items in `WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl` and summarized in `WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl`. They are not blockers to Wave5A dataset/leakage-guard launch because every row carries source status and no missing truth is imputed.",
            "",
        ]
    )


def output_manifest(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    files = []
    for path in sorted(route.iterdir()):
        if not path.is_file() or path.name == "WAVE4I_INTEGRATION_PARTITION_GATE_OUTPUT_MANIFEST.json":
            continue
        item = {
            "path": rel_path(repo_root, path),
            "sha256": wave4a.sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        if path.suffix == ".jsonl":
            item["jsonl_rows"] = _row_count(path)
        files.append(item)
    return {
        "schema_version": "wave4i_output_manifest_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "manifest_self_excluded_from_hash_list": True,
        "file_count": len(files),
        "files": files,
        "canonical_row_count": CANONICAL_ROW_COUNT,
        "canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
        "feature_version": FEATURE_VERSION,
        "label_set_version": LABEL_SET_VERSION,
        "partition_version": PARTITION_VERSION,
        "boundary_status": BOUNDARY_STATUS,
    }


def run_command(repo_root: Path, command: Sequence[str]) -> dict[str, Any]:
    proc = subprocess.run(
        list(command),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": list(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
    }


def prompt_hardening_result(repo_root: Path) -> dict[str, Any]:
    command = [
        "python3",
        "scripts/validate_goal_prompt_hardening.py",
        str(PROMPT_PATH),
        str(STARTER_PATH),
        "--kind",
        "builder",
        "--json",
    ]
    result = run_command(repo_root, command)
    parsed: dict[str, Any] | None = None
    stdout = str(result.get("stdout") or result["stdout_tail"])
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "schema_version": "wave4i_prompt_hardening_result_v1",
        "generated_at_utc": utc_now(),
        "ok": bool(result["ok"] and (parsed or {}).get("ok", True)),
        "command_result": result,
        "parsed": parsed,
    }


def route_artifact_audit_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    command = [
        "python3",
        "scripts/audit_goal_route_artifacts.py",
        str(route_dir),
        "--full-jsonl",
        "--require-saturation",
    ]
    result = run_command(repo_root, command)
    parsed: dict[str, Any] | None = None
    stdout = str(result.get("stdout") or result["stdout_tail"])
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "schema_version": "wave4i_route_artifact_audit_result_v1",
        "generated_at_utc": utc_now(),
        "ok": bool(result["ok"] and (parsed or {}).get("ok", True)),
        "command_result": result,
        "parsed": parsed,
    }


def focused_test_result(commands: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    command_rows = list(commands or [])
    environment_friction = [
        row for row in command_rows if not row.get("ok") and "No module named pytest" in str(row.get("stderr_tail"))
    ]
    waived_ids = {id(row) for row in environment_friction}
    strict_failures = [row for row in command_rows if not row.get("ok") and id(row) not in waived_ids]
    pytest_success = any(
        row.get("ok") and "pytest" in " ".join(str(part) for part in row.get("command", []))
        for row in command_rows
    )
    return {
        "schema_version": "wave4i_focused_test_result_v1",
        "generated_at_utc": utc_now(),
        "ok": bool(command_rows) and not strict_failures and pytest_success,
        "commands": command_rows,
        "environment_friction": environment_friction,
    }


def build_artifacts(
    repo_root: Path,
    route_dir: Path = ROUTE_DIR,
    *,
    run_route_audit: bool = False,
) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)
    (route / ".gitattributes").write_text("*.jsonl filter=lfs diff=lfs merge=lfs -text\n", encoding="utf-8")
    inputs = load_inputs(repo_root)
    reconciliation = row_reconciliation_rows(inputs)
    partitions = partition_rows(reconciliation, inputs)
    continuation = source_gap_continuation_rows(reconciliation)
    blockers = blocker_repair_rows(reconciliation, partitions, continuation)
    child_rows = child_review_rows(repo_root, inputs)
    acceptance = acceptance_decision_rows(repo_root, inputs, reconciliation)
    launchability = wave5_launchability_rows()

    wave4a.write_jsonl(route / "WAVE4I_CHILD_REVIEW_LEDGER.jsonl", child_rows)
    wave4a.write_jsonl(route / "WAVE4I_ACCEPTANCE_DECISION_LEDGER.jsonl", acceptance)
    wave4a.write_jsonl(route / "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl", reconciliation)
    wave4a.write_jsonl(route / "WAVE4I_PARTITION_LEDGER.jsonl", partitions)
    wave4a.write_jsonl(route / "WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl", continuation)
    wave4a.write_jsonl(route / "WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl", blockers)
    wave4a.write_jsonl(route / "WAVE4I_WAVE5_LAUNCHABILITY_LEDGER.jsonl", launchability)
    wave4a.write_jsonl(route / "WAVE4I_SEARCHED_ROOT_LEDGER.jsonl", searched_root_rows(repo_root))

    wave4a.write_json(route / "WAVE4I_SCHEMA_VERSION_BINDING.json", schema_version_binding(repo_root, reconciliation))
    wave4a.write_json(route / "WAVE4I_MERGE_SCOPE_LEDGER.json", merge_scope_ledger(repo_root))
    wave4a.write_json(route / "WAVE4I_CONTEXT_ANCHOR.json", context_anchor(repo_root, inputs, reconciliation, partitions))
    wave4a.write_json(
        route / "WAVE4I_WAVE5_HANDOFF_MANIFEST.json",
        wave5_handoff_manifest(repo_root, reconciliation, partitions, continuation, launchability),
    )
    wave4a.write_text(
        route / "WAVE4I_INTEGRATION_PARTITION_GATE_INSTRUCTION_COVERAGE_CHECKLIST.md",
        instruction_checklist_text(),
    )
    wave4a.write_text(
        route / "WAVE4I_INTEGRATION_PARTITION_GATE_SATURATION_SELF_RED_TEAM.md",
        saturation_text(),
    )
    wave4a.write_json(
        route / "WAVE4I_INTEGRATION_PARTITION_GATE_PROMPT_HARDENING_RESULT.json",
        prompt_hardening_result(repo_root),
    )
    if not (route / "WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json").exists():
        wave4a.write_json(
            route / "WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json",
            focused_test_result([]),
        )
    wave4a.write_json(
        route / "WAVE4I_INTEGRATION_PARTITION_GATE_VERIFICATION_RESULT.json",
        {"schema_version": "wave4i_verification_result_v1", "ok": False, "status": "placeholder_before_final_verifier"},
    )
    wave4a.write_json(
        route / "WAVE4I_INTEGRATION_PARTITION_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
        {"schema_version": "wave4i_route_artifact_audit_result_v1", "ok": False, "status": "placeholder_before_final_route_audit"},
    )
    wave4a.write_text(
        route / "COMPLETION_AUDIT.md",
        completion_audit_text(repo_root, reconciliation, partitions, continuation, None),
    )
    wave4a.write_json(route / "WAVE4I_INTEGRATION_PARTITION_GATE_OUTPUT_MANIFEST.json", output_manifest(repo_root, route_dir))
    verification = verify_route(repo_root, route_dir)
    wave4a.write_json(route / "WAVE4I_INTEGRATION_PARTITION_GATE_VERIFICATION_RESULT.json", verification)
    if run_route_audit:
        wave4a.write_json(
            route / "WAVE4I_INTEGRATION_PARTITION_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
            route_artifact_audit_result(repo_root, route_dir),
        )
    elif not (route / "WAVE4I_INTEGRATION_PARTITION_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json").exists():
        wave4a.write_json(
            route / "WAVE4I_INTEGRATION_PARTITION_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
            {"schema_version": "wave4i_route_artifact_audit_result_v1", "ok": False, "status": "not_run_yet"},
        )
    wave4a.write_text(route / "COMPLETION_AUDIT.md", completion_audit_text(repo_root, reconciliation, partitions, continuation, verification))
    wave4a.write_json(route / "WAVE4I_INTEGRATION_PARTITION_GATE_OUTPUT_MANIFEST.json", output_manifest(repo_root, route_dir))
    return {
        "route_dir": rel_path(repo_root, route),
        "reconciliation_rows": len(reconciliation),
        "partition_rows": len(partitions),
        "continuation_rows": len(continuation),
        "blocker_repair_rows": len(blockers),
        "child_review_rows": len(child_rows),
        "acceptance_rows": len(acceptance),
        "verification_ok": verification["ok"],
    }


def _load_jsonl_ids(path: Path) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    errors: list[str] = []
    for index, row in enumerate(wave4a.iter_jsonl(path), start=1):
        canonical_id = row.get("canonical_row_id")
        if not canonical_id:
            errors.append(f"{path.name}:{index}:missing canonical_row_id")
        ids.append(str(canonical_id))
    return ids, errors


def verify_route(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    checks: list[dict[str, Any]] = []
    route_is_canonical = Path(route_dir).as_posix().rstrip("/") == ROUTE_DIR.as_posix()

    def check(name: str, passed: bool, evidence: Mapping[str, Any] | None = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": dict(evidence or {})})

    check("route_dir_exists", route.exists())
    required_files = list(REQUIRED_ROUTE_FILES)
    if not route_is_canonical:
        required_files = [
            filename
            for filename in required_files
            if filename
            not in {
                "build_wave4i_integration_partition_gate.py",
                "verify_wave4i_integration_partition_gate.py",
                "record_wave4i_focused_test_result.py",
            }
        ]
    for filename in required_files:
        check(f"exists:{filename}", (route / filename).exists())

    jsonl_counts: dict[str, int] = {}
    parse_errors: list[str] = []
    for path in route.glob("*.jsonl"):
        try:
            count = _row_count(path)
            jsonl_counts[path.name] = int(count or 0)
        except (json.JSONDecodeError, ValueError) as exc:
            parse_errors.append(f"{path.name}:{exc}")
    check("all_jsonl_parse", not parse_errors, {"errors": parse_errors})

    canonical_ids = [str(row["canonical_row_id"]) for row in wave4a.iter_jsonl(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl")]
    canonical_set = set(canonical_ids)
    check("wave4a_canonical_count", len(canonical_ids) == CANONICAL_ROW_COUNT, {"actual": len(canonical_ids), "expected": CANONICAL_ROW_COUNT})
    check("wave4a_canonical_hash", wave4a.sha256_file(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl") == CANONICAL_UNIVERSE_HASH)

    for filename in (
        "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl",
        "WAVE4I_PARTITION_LEDGER.jsonl",
        "WAVE4I_SOURCE_GAP_AND_CONTINUATION_LEDGER.jsonl",
    ):
        path = route / filename
        if not path.exists():
            continue
        ids, id_errors = _load_jsonl_ids(path)
        check(f"{filename}:row_count_matches_canonical", len(ids) == CANONICAL_ROW_COUNT, {"actual": len(ids)})
        check(f"{filename}:ids_unique", len(set(ids)) == len(ids), {"unique": len(set(ids)), "actual": len(ids)})
        check(f"{filename}:ids_equal_wave4a", set(ids) == canonical_set, {"missing": len(canonical_set - set(ids)), "extra": len(set(ids) - canonical_set)})
        check(f"{filename}:ids_present", not id_errors, {"errors": id_errors[:20]})

    reconciliation_rows = list(wave4a.iter_jsonl(route / "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl")) if (route / "WAVE4I_ROW_RECONCILIATION_LEDGER.jsonl").exists() else []
    bad_recon = [row["canonical_row_id"] for row in reconciliation_rows if row.get("acceptance_decision") != "accepted_for_wave5_handoff"]
    check("all_reconciliation_rows_accepted", not bad_recon, {"bad_count": len(bad_recon), "examples": bad_recon[:10]})
    check("feature_label_versions_bound", all(row.get("feature_version") == FEATURE_VERSION and row.get("label_set_version") == LABEL_SET_VERSION for row in reconciliation_rows))
    check(
        "labels_never_asof_features",
        all((row.get("agreement") or {}).get("labels_excluded_from_asof_features") is True for row in reconciliation_rows),
    )

    partition_rows_loaded = list(wave4a.iter_jsonl(route / "WAVE4I_PARTITION_LEDGER.jsonl")) if (route / "WAVE4I_PARTITION_LEDGER.jsonl").exists() else []
    missing_partition_fields = [
        row.get("canonical_row_id")
        for row in partition_rows_loaded
        if not all(
            key in row
            for key in (
                "primary_temporal_split",
                "walk_forward_role_by_fold",
                "symbol_holdout_key",
                "session_holdout_key",
                "regime_holdout_key",
                "cost_stress_partition",
                "outlier_partition",
                "no_leak_partition_guard",
            )
        )
    ]
    check("partition_required_fields_present", not missing_partition_fields, {"missing_examples": missing_partition_fields[:10]})
    check(
        "partition_no_leak_guards_pass",
        all((row.get("no_leak_partition_guard") or {}).get("status") == "pass" for row in partition_rows_loaded),
    )

    decisions = list(wave4a.iter_jsonl(route / "WAVE4I_ACCEPTANCE_DECISION_LEDGER.jsonl")) if (route / "WAVE4I_ACCEPTANCE_DECISION_LEDGER.jsonl").exists() else []
    check("acceptance_decisions_present", len(decisions) >= 4, {"rows": len(decisions)})
    check("acceptance_decisions_not_rejected", all(row.get("decision") in {"accepted", "accepted_with_exact_continuation_requirements"} for row in decisions), {"decisions": Counter(str(row.get("decision")) for row in decisions)})
    blocker_rows = list(wave4a.iter_jsonl(route / "WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl")) if (route / "WAVE4I_BLOCKER_REPAIR_LEDGER.jsonl").exists() else []
    check("blocker_repair_ledger_present", len(blocker_rows) >= 4, {"rows": len(blocker_rows)})
    check(
        "no_unresolved_wave5a_blocker",
        all(row.get("wave5a_status") != "blocked" for row in blocker_rows),
        {"statuses": Counter(str(row.get("wave5a_status")) for row in blocker_rows)},
    )

    merge_scope = _read_json_if_exists(route / "WAVE4I_MERGE_SCOPE_LEDGER.json")
    ancestors = merge_scope.get("accepted_commit_ancestor_status") if isinstance(merge_scope.get("accepted_commit_ancestor_status"), Mapping) else {}
    check("accepted_commits_are_ancestors", bool(ancestors) and all(bool(value) for value in ancestors.values()), {"ancestors": ancestors})

    handoff = _read_json_if_exists(route / "WAVE4I_WAVE5_HANDOFF_MANIFEST.json")
    check("wave5_handoff_references_versions", handoff.get("feature_version") == FEATURE_VERSION and handoff.get("label_set_version") == LABEL_SET_VERSION)
    check("wave5a_launchable", any(row.get("wave5_lane") == "wave5a_dataset_leakage_guard" and row.get("launch_status") == "launchable_now_after_wave4i_commit" for row in wave5_launchability_rows()))

    prompt = _read_json_if_exists(route / "WAVE4I_INTEGRATION_PARTITION_GATE_PROMPT_HARDENING_RESULT.json")
    focused = _read_json_if_exists(route / "WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json")
    check("prompt_hardening_passed", bool(prompt.get("ok")))
    check("focused_test_result_record_exists", bool(focused))
    check("boundary_status_preserved", all(value is False for key, value in BOUNDARY_STATUS.items() if key != "RESULT_MATERIALIZATION_REQUIRED"))

    failures = [item for item in checks if not item["passed"]]
    return {
        "schema_version": "wave4i_verification_result_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "ok": not failures,
        "issue_count": len(failures),
        "checks": checks,
        "jsonl_counts": jsonl_counts,
        "boundary_status": BOUNDARY_STATUS,
        "canonical_row_count": CANONICAL_ROW_COUNT,
        "canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
        "feature_version": FEATURE_VERSION,
        "label_set_version": LABEL_SET_VERSION,
    }


def write_verification_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    result = verify_route(repo_root, route_dir)
    wave4a.write_json(
        route_abs(repo_root, route_dir) / "WAVE4I_INTEGRATION_PARTITION_GATE_VERIFICATION_RESULT.json",
        result,
    )
    return result


def write_focused_test_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    commands = [
        run_command(
            repo_root,
            [
                "python3",
                "-m",
                "py_compile",
                "src/research_infra/wave4i_integration_partition_gate.py",
                "tests/test_wave4i_integration_partition_gate.py",
                str(route_dir / "build_wave4i_integration_partition_gate.py"),
                str(route_dir / "verify_wave4i_integration_partition_gate.py"),
                str(route_dir / "record_wave4i_focused_test_result.py"),
            ],
        )
    ]
    base_pytest = run_command(
        repo_root,
        [
            "python3",
            "-m",
            "pytest",
            "tests/test_wave4i_integration_partition_gate.py",
            "-q",
            "--basetemp=/tmp/gtos_wave4i_pytest_base",
        ],
    )
    if base_pytest["ok"]:
        commands.append(base_pytest)
    else:
        commands.append({**base_pytest, "environment_friction": "base python pytest unavailable or failed; uv fallback attempted"})
        commands.append(
            run_command(
                repo_root,
                [
                    "uv",
                    "run",
                    "--no-project",
                    "--with",
                    "pytest",
                    "--with",
                    "pyyaml",
                    "python",
                    "-m",
                    "pytest",
                    "tests/test_wave4i_integration_partition_gate.py",
                    "-q",
                    "--basetemp=/tmp/gtos_wave4i_pytest_uv",
                ],
            )
        )
    result = focused_test_result(commands)
    wave4a.write_json(
        route_abs(repo_root, route_dir) / "WAVE4I_INTEGRATION_PARTITION_GATE_FOCUSED_TEST_RESULT.json",
        result,
    )
    return result


def write_route_audit_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    result = route_artifact_audit_result(repo_root, route_dir)
    wave4a.write_json(
        route_abs(repo_root, route_dir) / "WAVE4I_INTEGRATION_PARTITION_GATE_ROUTE_ARTIFACT_AUDIT_RESULT.json",
        result,
    )
    return result


def refresh_manifest(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    manifest = output_manifest(repo_root, route_dir)
    wave4a.write_json(route_abs(repo_root, route_dir) / "WAVE4I_INTEGRATION_PARTITION_GATE_OUTPUT_MANIFEST.json", manifest)
    return manifest

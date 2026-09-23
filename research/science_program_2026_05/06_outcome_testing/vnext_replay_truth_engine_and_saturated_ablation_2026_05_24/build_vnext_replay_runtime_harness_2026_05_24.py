"""Build the initial runtime truth-harness decision trace.

The harness calls the current ``src.components.gtos_vnext_runtime`` surfaces
directly. It does not reimplement the matcher and does not change production
config or live trading behavior.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    apply_vnext_risk_adjustment,
    evaluate_pre_ai_vnext,
    evaluate_vnext_event,
    evaluate_vnext_pending_policy,
    evaluate_vnext_route_event,
    load_vnext_evidence_index,
    normalize_event,
)
BUILDER_ROUTE = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)

CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
FREEZE_LEDGER_PATH = (
    REPO_ROOT
    / BUILDER_ROUTE
    / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_CLASSIFICATION_LEDGER_2026-05-23.jsonl"
)
DECISION_TRACE_PATH = ROUTE_DIR / "VNEXT_REPLAY_DECISION_TRACE_LEDGER_2026-05-24.jsonl"
HARNESS_VERIFY_PATH = ROUTE_DIR / "VNEXT_REPLAY_RUNTIME_HARNESS_VERIFY_2026-05-24.json"
RUNTIME_ARTIFACT_LOAD_PATH = (
    ROUTE_DIR / "VNEXT_REPLAY_RUNTIME_ARTIFACT_LOAD_LEDGER_2026-05-24.jsonl"
)
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"

FIXTURE_EVENTS = [
    {
        "event_id": "fixture_usdjpy_london_long_ob_retest",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "route_session": "london",
        "kill_zone": "london",
        "side": "LONG",
        "direction": "LONG",
        "framework": "ob_retest",
        "effective_framework": "ob_retest",
        "market_timeframe": "M15",
        "bias": "bullish",
    },
    {
        "event_id": "fixture_nas100_london_short_ob_retest",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "route_session": "london",
        "kill_zone": "london",
        "side": "SHORT",
        "direction": "SHORT",
        "framework": "ob_retest",
        "effective_framework": "ob_retest",
        "market_timeframe": "M15",
        "bias": "bearish",
    },
    {
        "event_id": "fixture_gbpjpy_tokyo_long_ob_retest",
        "symbol": "GBPJPY",
        "source_symbol": "GBPJPY",
        "route_session": "tokyo",
        "kill_zone": "tokyo",
        "side": "LONG",
        "direction": "LONG",
        "framework": "ob_retest",
        "effective_framework": "ob_retest",
        "market_timeframe": "M15",
        "bias": "bullish",
    },
    {
        "event_id": "fixture_xauusd_ny_long_ob_retest",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "route_session": "ny",
        "kill_zone": "ny",
        "side": "LONG",
        "direction": "LONG",
        "framework": "ob_retest",
        "effective_framework": "ob_retest",
        "market_timeframe": "M15",
        "bias": "bullish",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_freeze_rows() -> list[dict[str, Any]]:
    rows = []
    with FREEZE_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def activated_config(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    runtime_cfg = cfg.setdefault("gtos_vnext_runtime", {})
    runtime_cfg["enabled"] = True
    runtime_cfg["apply_to_execution"] = True
    runtime_cfg["pre_ai_enabled"] = True
    runtime_cfg["pre_ai_apply_to_ai_call"] = True
    runtime_cfg["risk_adjustment_enabled"] = True
    runtime_cfg["pending_policy_enabled"] = True
    runtime_cfg["exit_management_residue_apply_to_execution"] = True
    runtime_cfg["ready8_failure_control_residue_apply_to_execution"] = True
    return cfg


def fixture_slice_config(config: dict[str, Any], *, activated: bool = False) -> dict[str, Any]:
    """Return a harness-only config for sliced fixture rows.

    The full active artifact universe is loaded and counted separately. Fixture
    API calls use only rows matched from that universe, so the production
    ``min_loaded_evidence_rows`` denominator guard is lowered for this harness
    shard. Full replay must use the preregistered active config value.
    """
    cfg = activated_config(config) if activated else copy.deepcopy(config)
    cfg.setdefault("gtos_vnext_runtime", {})["min_loaded_evidence_rows"] = 1
    return cfg


def event_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in event.items()
        if key
        not in {
            "event_id",
            "bias",
        }
    }


def compact_decision(record: dict[str, Any]) -> dict[str, Any]:
    evidence = record.get("evidence", {}) if isinstance(record, dict) else {}
    return {
        "decision": record.get("decision"),
        "enabled": record.get("enabled"),
        "apply_to_execution": record.get("apply_to_execution"),
        "matched": record.get("matched"),
        "reason": record.get("reason"),
        "event": record.get("event"),
        "artifact_path_count": len(record.get("artifact_paths") or []),
        "evidence": {
            "matched_rows": evidence.get("matched_rows"),
            "decision_counts": evidence.get("decision_counts"),
            "source_component_counts": evidence.get("source_component_counts"),
            "evidence_family_counts": evidence.get("evidence_family_counts"),
            "action_class_counts": evidence.get("action_class_counts"),
            "route_event_count": evidence.get("route_event_count"),
            "matched_row_id_count": evidence.get("matched_row_id_count"),
            "matched_row_ids": evidence.get("matched_row_ids"),
            "matched_row_ids_truncated": evidence.get("matched_row_ids_truncated"),
            "source_row_id_count": evidence.get("source_row_id_count"),
            "source_row_ids": evidence.get("source_row_ids"),
            "source_row_ids_truncated": evidence.get("source_row_ids_truncated"),
            "scope_selection_policy": evidence.get("scope_selection_policy"),
            "decision_resolution": evidence.get("decision_resolution"),
            "metrics": evidence.get("metrics"),
            "row_detail_count": evidence.get("row_detail_count"),
            "rows": evidence.get("rows"),
            "rows_truncated": evidence.get("rows_truncated"),
        },
    }


def trace_row(
    *,
    fixture: dict[str, Any],
    mode: str,
    config: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    event = event_payload(fixture)
    direct_decision = evaluate_vnext_event(event, config, artifact_rows=artifact_rows)
    route_decision = evaluate_vnext_route_event(event, config, artifact_rows=artifact_rows)
    risk_pct = float((config.get("risk", {}) or {}).get("risk_per_trade_pct", 2.0))
    risk_adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=risk_pct,
        decision=route_decision,
        config=config,
    )
    pending_policy = evaluate_vnext_pending_policy(decision=route_decision, config=config)
    pre_ai_decision = evaluate_pre_ai_vnext(
        symbol=fixture["symbol"],
        source_symbol=fixture.get("source_symbol"),
        kill_zone=fixture["kill_zone"],
        config=config,
        bias=fixture.get("bias"),
        raw_data={"gtos_replay_fixture": True, "market_timeframe": fixture.get("market_timeframe")},
        artifact_rows=artifact_rows,
    )
    return {
        "schema_version": "vnext_replay_decision_trace_v1",
        "stage_id": "STAGE_03_RUNTIME_TRUTH_HARNESS",
        "trace_id": f"{fixture['event_id']}::{mode}",
        "event_id": fixture["event_id"],
        "replay_mode": mode,
        "activation_boundary": (
            "active_config_shadow"
            if mode == "current_config_shadow"
            else "hypothetical_no_production_config_mutation"
        ),
        "runtime_surface_calls": [
            "evaluate_vnext_event",
            "evaluate_vnext_route_event",
            "evaluate_pre_ai_vnext",
            "apply_vnext_risk_adjustment",
            "evaluate_vnext_pending_policy",
        ],
        "fixture_slice_config_boundary": {
            "uses_current_runtime_surfaces": True,
            "production_config_mutated": False,
            "full_replay_must_use_preregistered_min_loaded_evidence_rows": True,
            "fixture_only_min_loaded_evidence_rows": (
                (config.get("gtos_vnext_runtime", {}) or {}).get("min_loaded_evidence_rows")
            ),
        },
        "input_event": event,
        "direct_decision": compact_decision(direct_decision.to_record()),
        "route_decision": compact_decision(route_decision.to_record()),
        "pre_ai_decision": pre_ai_decision.to_record(),
        "risk_adjustment": risk_adjustment.to_record(),
        "pending_policy": pending_policy.to_record(),
        "no_live_trading_or_broker_mutation": True,
    }


def freeze_residue_verification(config: dict[str, Any]) -> dict[str, Any]:
    rows = load_freeze_rows()
    artifact_paths = set((config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or [])
    return {
        "freeze_ledger_path": rel(FREEZE_LEDGER_PATH),
        "freeze_ledger_rows": len(rows),
        "runtime_pressure_allowed_rows": sum(
            1 for row in rows if row.get("runtime_pressure_allowed") is True
        ),
        "legacy_support_override_allowed_rows": sum(
            1 for row in rows if row.get("legacy_support_override_allowed") is True
        ),
        "follow_avoid_mixed_pressure_allowed_rows": sum(
            1 for row in rows if row.get("follow_avoid_mixed_pressure_allowed") is True
        ),
        "freeze_ledger_is_configured_runtime_artifact": rel(FREEZE_LEDGER_PATH) in artifact_paths,
    }


def _row_identity(row: dict[str, Any]) -> str:
    identity_parts = [
        str(row.get("_gtos_vnext_loaded_from") or ""),
        str(row.get("row_id") or ""),
        str(row.get("source_row_id") or ""),
        str(row.get("source_artifact") or ""),
        str(row.get("source_component") or ""),
        str(row.get("symbol") or ""),
        str(row.get("source_symbol") or ""),
        str(row.get("route_session") or ""),
        str(row.get("side") or ""),
        str(row.get("framework") or ""),
        str(row.get("action_class") or ""),
    ]
    return "\u001f".join(identity_parts)


def _fixture_relevant_rows(index: Any, fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_identity: dict[str, dict[str, Any]] = {}
    for fixture in fixtures:
        normalized = normalize_event(event_payload(fixture))
        for row in index.match_event(normalized, min_scope_fields=1):
            rows_by_identity.setdefault(_row_identity(row), row)
    return list(rows_by_identity.values())


def load_runtime_artifact_shards(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load every configured artifact through the current runtime loader in shards."""
    runtime_paths = (config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or []
    load_rows: list[dict[str, Any]] = []
    fixture_rows_by_identity: dict[str, dict[str, Any]] = {}
    for index, artifact_path in enumerate(runtime_paths, start=1):
        artifact_index = load_vnext_evidence_index([artifact_path])
        relevant_rows = _fixture_relevant_rows(artifact_index, FIXTURE_EVENTS)
        for row in relevant_rows:
            fixture_rows_by_identity.setdefault(_row_identity(row), row)
        load_rows.append(
            {
                "schema_version": "vnext_replay_runtime_artifact_load_v1",
                "stage_id": "STAGE_03_RUNTIME_TRUTH_HARNESS",
                "artifact_index": index,
                "artifact_path": str(artifact_path),
                "rows_loaded": len(artifact_index.rows),
                "rows_loaded_by_path": artifact_index.rows_loaded_by_path,
                "missing_paths": list(artifact_index.missing_paths),
                "fixture_relevant_rows": len(relevant_rows),
                "load_status": "LOADED_WITH_CURRENT_RUNTIME_LOADER"
                if not artifact_index.missing_paths
                else "LOADED_WITH_MISSING_PATHS",
            }
        )
    return load_rows, list(fixture_rows_by_identity.values())


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    config = load_config()
    full_config_min_loaded = (
        (config.get("gtos_vnext_runtime", {}) or {}).get("min_loaded_evidence_rows")
    )
    runtime_paths = (config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or []
    artifact_load_rows, fixture_artifact_rows = load_runtime_artifact_shards(config)
    shadow_fixture_config = fixture_slice_config(config, activated=False)
    activated = fixture_slice_config(config, activated=True)
    rows = []
    for fixture in FIXTURE_EVENTS:
        rows.append(
            trace_row(
                fixture=fixture,
                mode="current_config_shadow",
                config=shadow_fixture_config,
                artifact_rows=fixture_artifact_rows,
            )
        )
        rows.append(
            trace_row(
                fixture=fixture,
                mode="hypothetical_activated_vnext",
                config=activated,
                artifact_rows=fixture_artifact_rows,
            )
        )
    route_decisions = Counter(row["route_decision"]["decision"] for row in rows)
    pre_ai_actions = Counter(row["pre_ai_decision"]["action"] for row in rows)
    risk_reasons = Counter(row["risk_adjustment"]["reason"] for row in rows)
    pending_actions = Counter(row["pending_policy"]["would_action"] for row in rows)
    freeze_check = freeze_residue_verification(config)
    verify = {
        "schema_version": "vnext_replay_runtime_harness_verify_v1",
        "generated_utc": utc_now(),
        "stage_id": "STAGE_03_RUNTIME_TRUTH_HARNESS",
        "fixture_count": len(FIXTURE_EVENTS),
        "trace_row_count": len(rows),
        "runtime_artifact_paths_loaded": len(runtime_paths),
        "full_config_min_loaded_evidence_rows": full_config_min_loaded,
        "fixture_slice_min_loaded_evidence_rows": 1,
        "fixture_slice_denominator_override_reason": (
            "runtime surfaces are tested on rows matched from the loaded full artifact universe; "
            "saturated replay must use full active config and full eligible data shards"
        ),
        "runtime_artifact_load_ledger_path": rel(RUNTIME_ARTIFACT_LOAD_PATH),
        "runtime_artifact_load_rows": len(artifact_load_rows),
        "runtime_artifact_missing_path_count": sum(
            len(row["missing_paths"]) for row in artifact_load_rows
        ),
        "runtime_index_rows_loaded_by_shard": sum(row["rows_loaded"] for row in artifact_load_rows),
        "fixture_relevant_runtime_rows": len(fixture_artifact_rows),
        "route_decision_counts": dict(sorted(route_decisions.items())),
        "pre_ai_action_counts": dict(sorted(pre_ai_actions.items())),
        "risk_reason_counts": dict(sorted(risk_reasons.items())),
        "pending_would_action_counts": dict(sorted(pending_actions.items())),
        "freeze_residue_verification": freeze_check,
        "harness_calls_current_runtime_surfaces": True,
        "production_config_mutated": False,
        "no_live_trading_or_broker_mutation": True,
        "pass": (
            len(rows) == len(FIXTURE_EVENTS) * 2
            and len(artifact_load_rows) == len(runtime_paths)
            and len(fixture_artifact_rows) > 0
            and sum(len(row["missing_paths"]) for row in artifact_load_rows) == 0
            and any(row["route_decision"]["matched"] for row in rows)
            and freeze_check["runtime_pressure_allowed_rows"] == 0
            and freeze_check["legacy_support_override_allowed_rows"] == 0
            and freeze_check["follow_avoid_mixed_pressure_allowed_rows"] == 0
            and not freeze_check["freeze_ledger_is_configured_runtime_artifact"]
        ),
    }
    return rows, verify, artifact_load_rows


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for path in [DECISION_TRACE_PATH, RUNTIME_ARTIFACT_LOAD_PATH, HARNESS_VERIFY_PATH]:
        existing_paths[rel(path)] = {
            "path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "lines": line_count(path),
            "sha256": sha256_file(path),
            "source_kind": "generated_replay_output",
        }
    write_json(
        OUTPUT_MANIFEST_PATH,
        {
            "schema_version": "vnext_replay_output_manifest_v1",
            "generated_utc": utc_now(),
            "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
            "outputs": [existing_paths[key] for key in sorted(existing_paths)],
            "next_stage": "STAGE_04_EVENT_AND_PATH_RECONSTRUCTION",
        },
    )


def build_outputs() -> dict[str, Any]:
    rows, verify, artifact_load_rows = build_rows()
    write_jsonl(DECISION_TRACE_PATH, rows)
    write_jsonl(RUNTIME_ARTIFACT_LOAD_PATH, artifact_load_rows)
    write_json(HARNESS_VERIFY_PATH, verify)
    update_output_manifest()
    if not verify["pass"]:
        raise SystemExit("runtime harness verification failed")
    return verify


def check_outputs() -> None:
    expected_rows, expected_verify, expected_artifact_load_rows = build_rows()
    existing_rows = read_jsonl(DECISION_TRACE_PATH)
    if existing_rows != expected_rows:
        raise AssertionError("Decision trace ledger is stale")
    existing_verify = read_json(HARNESS_VERIFY_PATH)
    existing_no_time = dict(existing_verify)
    expected_no_time = dict(expected_verify)
    existing_no_time.pop("generated_utc", None)
    expected_no_time.pop("generated_utc", None)
    if existing_no_time != expected_no_time:
        raise AssertionError("Runtime harness verifier is stale")
    if not existing_verify.get("pass"):
        raise AssertionError("Runtime harness verifier did not pass")
    existing_artifact_load_rows = read_jsonl(RUNTIME_ARTIFACT_LOAD_PATH)
    if existing_artifact_load_rows != expected_artifact_load_rows:
        raise AssertionError("Runtime artifact load ledger is stale")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext replay runtime harness check passed")
        return
    verify = build_outputs()
    print(json.dumps(verify, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

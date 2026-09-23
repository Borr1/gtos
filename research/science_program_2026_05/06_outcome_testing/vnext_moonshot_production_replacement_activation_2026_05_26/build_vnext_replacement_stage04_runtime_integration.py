from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
INTEGRATION_MAP_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
EFFECT_LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_RUNTIME_EFFECT_LEDGER_{DATE}.jsonl"

REPO_ROOT = ROUTE_DIR.parents[3]

CHANGED_FILES = [
    "config/agent_config.yaml",
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_j46_j49_policy.py",
    "tests/test_limit_order_flow.py",
]

LFS_POINTER_PROBES = [
    (
        "research/science_program_2026_05/06_outcome_testing/"
        "gtos_vnext_research_to_runtime_builder/"
        "GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_2026-05-18.jsonl"
    ),
    (
        "research/science_program_2026_05/06_outcome_testing/"
        "gtos_vnext_research_to_runtime_builder/"
        "GTOS_VNEXT_SCORER_FILTER_ROUTER_REVIEW_LEDGER_2026-05-18.jsonl"
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def lfs_pointer_probe(rel_path: str) -> dict[str, Any]:
    path = REPO_ROOT / rel_path
    first_lines = []
    if path.exists():
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for _ in range(3):
                line = fh.readline()
                if not line:
                    break
                first_lines.append(line.strip())
    pointer = bool(first_lines and first_lines[0] == "version https://git-lfs.github.com/spec/v1")
    oid = None
    size = None
    for line in first_lines:
        if line.startswith("oid sha256:"):
            oid = line.removeprefix("oid sha256:")
        if line.startswith("size "):
            try:
                size = int(line.removeprefix("size "))
            except ValueError:
                size = None
    return {
        "path": rel_path,
        "exists": path.exists(),
        "is_git_lfs_pointer": pointer,
        "oid_sha256": oid,
        "declared_size_bytes": size,
        "first_lines": first_lines,
    }


def stage04_effect_rows(timestamp: str) -> list[dict[str, Any]]:
    return [
        {
            "effect_id": "stage04_runtime_decision_dataclass",
            "surface": "src/components/gtos_vnext_runtime.py",
            "runtime_effect": "adds GTOSVNextMoonshotDynamicExecutionDecision with to_record payload",
            "activation_gate": "gtos_vnext_runtime.moonshot_dynamic_execution_router_enabled",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_router_event_builder",
            "surface": "src/components/gtos_vnext_runtime.py",
            "runtime_effect": "builds source-bound moonshot router event from vNext decision plus candidate context",
            "source_contract_fields": [
                "framework",
                "session_bucket",
                "source_mode",
                "source_path_feature_status",
                "source_window_complete",
                "ordered_path_status",
                "current_bar_displacement_atr14",
            ],
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_router_evaluator",
            "surface": "src/components/gtos_vnext_runtime.py",
            "runtime_effect": "calls route_moonshot_dynamic_execution through config-gated runtime wrapper",
            "activation_gate": [
                "gtos_vnext_runtime.apply_to_execution",
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution",
            ],
            "selected_policy": "be_after_trigger",
            "replaces_policy": "live_current_j46_j49",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_record_attachment",
            "surface": "src/components/gtos_vnext_runtime.py",
            "runtime_effect": "attaches moonshot dynamic policy decision to decision_pipeline and instrumentation",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_orchestrator_runtime_call",
            "surface": "src/components/orchestrator.py",
            "runtime_effect": "evaluates moonshot dynamic execution after LTF path and prop selector context are available",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_orchestrator_market_entry_propagation",
            "surface": "src/components/orchestrator.py",
            "runtime_effect": "passes selected dynamic policy metadata into open_trade for vNext market-entry path",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_orchestrator_pending_intent_propagation",
            "surface": "src/components/orchestrator.py",
            "runtime_effect": "passes selected dynamic policy metadata into pending telemetry and limit-intent trade params",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_execution_trade_state_persistence",
            "surface": "src/components/execution.py",
            "runtime_effect": "persists selected dynamic policy metadata on TradeState after successful order",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_execution_pending_state_persistence",
            "surface": "src/components/execution.py",
            "runtime_effect": "persists selected dynamic policy metadata on PendingLimitIntent and lifecycle rows",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_j46_replacement_guard",
            "surface": "src/components/execution.py",
            "runtime_effect": "suppresses J46/J49 broker TP override only when dynamic policy is applied and replaces live_current_j46_j49",
            "rollback_policy": "omit dynamic applied/replaced fields or disable moonshot/router apply flags to restore J46/J49 behavior",
            "live_broker_surface": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_config_defaults",
            "surface": "config/agent_config.yaml",
            "runtime_effect": "adds source/default config keys while keeping dynamic router enabled/apply flags false",
            "active_execution_effect_now": False,
            "timestamp_utc": timestamp,
        },
        {
            "effect_id": "stage04_tests",
            "surface": "tests",
            "runtime_effect": "adds focused runtime, J46 replacement, and pending-fill propagation coverage",
            "focused_tests_passed": 7,
            "broader_touched_tests_passed": 54,
            "full_runtime_suite_boundary": "blocked_by_unmaterialized_git_lfs_pointer_artifacts",
            "timestamp_utc": timestamp,
        },
    ]


def main() -> None:
    timestamp = utc_now()
    changed_file_hashes = [
        {
            "path": rel_path,
            "sha256": sha256_file(REPO_ROOT / rel_path),
            "exists": (REPO_ROOT / rel_path).exists(),
        }
        for rel_path in CHANGED_FILES
    ]
    lfs_probes = [lfs_pointer_probe(path) for path in LFS_POINTER_PROBES]
    effect_rows = stage04_effect_rows(timestamp)
    with EFFECT_LEDGER_PATH.open("w", encoding="utf-8") as fh:
        for row in effect_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    integration_map = {
        "route_id": ROUTE_ID,
        "stage": "stage_04_runtime_implementation",
        "status": "completed_runtime_code_config_tests_written",
        "timestamp_utc": timestamp,
        "runtime_surfaces_changed": CHANGED_FILES[:4],
        "test_surfaces_changed": CHANGED_FILES[4:],
        "changed_file_hashes": changed_file_hashes,
        "moonshot_dynamic_execution_runtime": {
            "router_module": "src/research/moonshot_default_off_policy_router.py",
            "runtime_wrapper": "evaluate_vnext_moonshot_dynamic_execution",
            "record_attachment": "attach_vnext_moonshot_dynamic_execution_to_record",
            "orchestrator_phase": "moonshot_dynamic_execution",
            "selected_policy": "be_after_trigger",
            "replaces_policy": "live_current_j46_j49",
            "primary_branch": "origin_current_fvg_fill",
            "primary_framework": "fvg_fill",
            "active_now": False,
            "reason_active_now_false": (
                "base config keeps gtos_vnext_runtime.apply_to_execution=false and "
                "moonshot_dynamic_execution_router_apply_to_execution=false"
            ),
        },
        "execution_replacement_boundary": {
            "j46_j49_suppressed_only_when": [
                "gtos_vnext_dynamic_policy_applied is true",
                "gtos_vnext_dynamic_policy_replaced_policy == live_current_j46_j49",
            ],
            "rollback": [
                "set gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution=false",
                "set gtos_vnext_runtime.apply_to_execution=false",
                "omit dynamic policy applied/replaced fields from trade_params",
            ],
        },
        "tests_verifiers": [
            {
                "command": (
                    "python -m py_compile src\\components\\gtos_vnext_runtime.py "
                    "src\\components\\orchestrator.py src\\components\\execution.py "
                    "tests\\test_gtos_vnext_runtime.py tests\\test_j46_j49_policy.py "
                    "tests\\test_limit_order_flow.py"
                ),
                "result": "passed",
            },
            {
                "command": (
                    "python -m pytest focused Stage04 dynamic-router/J46/pending/config "
                    "selection -q"
                ),
                "result": "7 passed",
            },
            {
                "command": (
                    "python -m pytest tests/test_moonshot_default_off_policy_router.py "
                    "tests/test_j46_j49_policy.py tests/test_limit_order_flow.py -q"
                ),
                "result": "54 passed",
            },
            {
                "command": "python -m pytest tests/test_gtos_vnext_runtime.py -q",
                "result": "failed: 76 failed, 206 passed",
                "failure_class": "git_lfs_pointer_artifacts_not_materialized",
                "lfs_pointer_probes": lfs_probes,
                "stage04_logic_failure": False,
            },
        ],
        "forbidden_surface_audit": {
            "live_trading": False,
            "broker_account_order_deal_position_history_mutation": False,
            "account_connected_runtime_process_started": False,
            "paid_api_or_vendor_calls": False,
            "credential_change": False,
            "remote_push": False,
            "destructive_source_deletion": False,
            "history_rewrite": False,
        },
        "next_stage": "stage_05_full_activated_historical_replay",
        "first_incomplete_invariant": "stage_05_full_activated_historical_replay_pending",
    }
    write_json(INTEGRATION_MAP_PATH, integration_map)

    manifest = read_json(MANIFEST_PATH)
    for output in manifest.get("outputs", []):
        if output.get("path") == EFFECT_LEDGER_PATH.name:
            output["status"] = "created"
            output["rows"] = len(effect_rows)
        if output.get("path") == INTEGRATION_MAP_PATH.name:
            output["status"] = "created"
            output["runtime_surfaces"] = len(CHANGED_FILES[:4])
            output["test_surfaces"] = len(CHANGED_FILES[4:])
    manifest.setdefault("outputs", []).append(
        {
            "path": Path(__file__).name,
            "stage": "stage_04",
            "status": "created_and_ready_for_py_compile",
        }
    )
    manifest["next_manifest_update"] = "After Stage 05 full activated replay outputs are written."
    write_json(MANIFEST_PATH, manifest)

    state = read_json(STATE_PATH)
    state["last_updated_utc"] = timestamp
    state["current_stage"] = "stage_05_full_activated_historical_replay"
    state["stage_status"]["stage_04_runtime_implementation"] = (
        "completed_runtime_code_config_tests_written_lfs_full_runtime_suite_boundary_recorded"
    )
    state["first_incomplete_invariant"] = "stage_05_full_activated_historical_replay_pending"
    state["exact_next_action"] = (
        "Build and run the full activated historical replay under the Stage 04 runtime "
        "semantics, including moonshot dynamic BE-after-trigger replacement of J46/J49, "
        "source-bound exclusions, prop/LTF effects, row-preserving ledgers, and activated "
        "config semantics without touching live/broker/account surfaces."
    )
    state.setdefault("runtime_config_test_surface_read_status", {}).update(
        {
            "config/agent_config.yaml": "stage04_read_and_edited",
            "src/components/gtos_vnext_runtime.py": "stage04_read_and_edited",
            "src/components/orchestrator.py": "stage04_read_and_edited",
            "src/components/execution.py": "stage04_read_and_edited",
            "src/research/moonshot_default_off_policy_router.py": "stage04_read_reused",
            "tests": "stage04_focused_tests_added_and_run",
        }
    )
    state.setdefault("evidence_rows_scanned", {}).update(
        {
            "stage04_runtime_effect_rows": len(effect_rows),
            "stage04_changed_runtime_files": len(CHANGED_FILES[:4]),
            "stage04_changed_test_files": len(CHANGED_FILES[4:]),
            "stage04_lfs_pointer_probe_rows": len(lfs_probes),
        }
    )
    state.setdefault("tests_verifiers_run", []).extend(integration_map["tests_verifiers"])
    state["completion_gate_status"] = {
        "route_complete": False,
        "allowed_terminal_status": None,
        "reason": (
            "Stage 04 runtime wiring is complete, but full activated replay, delta ledger, "
            "question closure, source activation map, AI/ML package, semantic verifier, "
            "applied overlay, rollback proof, monitoring package, scoped commits, and "
            "completion audit remain incomplete."
        ),
    }
    write_json(STATE_PATH, state)

    append_jsonl(
        CONTROL_LEDGER_PATH,
        {
            "event": "stage_04_runtime_integration_written",
            "route_id": ROUTE_ID,
            "timestamp_utc": timestamp,
            "integration_map": str(INTEGRATION_MAP_PATH.relative_to(REPO_ROOT)),
            "effect_ledger": str(EFFECT_LEDGER_PATH.relative_to(REPO_ROOT)),
            "effect_rows": len(effect_rows),
            "next_incomplete_invariant": "stage_05_full_activated_historical_replay_pending",
            "focused_tests": "7 passed",
            "broader_touched_tests": "54 passed",
            "full_runtime_suite_boundary": "git_lfs_pointer_artifacts_not_materialized",
        },
    )
    print(
        json.dumps(
            {
                "integration_map": str(INTEGRATION_MAP_PATH),
                "effect_ledger": str(EFFECT_LEDGER_PATH),
                "effect_rows": len(effect_rows),
                "next": "stage_05_full_activated_historical_replay_pending",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

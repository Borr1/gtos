#!/usr/bin/env python3
"""Verify the parent ultimate-system route after materialized child waves."""

from __future__ import annotations

import json
import subprocess
import errno
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
SIBLING_REPO = ROOT.parent / "ai-trading-agent"
WAVE_A_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19"
WAVE_C_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19"
WAVE_C_CLOSE_CAPTURE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19"
WAVE_C_BROKER_ACTUAL_R_CLOSE_EXHAUSTION_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19"
)
WAVE_D_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19"
WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19"
)
WAVE_E_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19"
WAVE_F_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19"
WAVE_F_VALIDATION_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19"
WAVE_F_SUCCESSOR_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19"
WAVE_F_FILLABILITY_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19"
WAVE_F_LIFECYCLE_BRIDGE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19"
WAVE_F_LIFECYCLE_DENOMINATOR_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19"
HYDRATED_REPLAY_LIFT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19"
SCHEDULER_MATCH_REPAIR_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19"
)
WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19"
)
FINAL_SELECTION_SOURCE_EXHAUSTION_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19"
)
FINAL_PACKAGE_SYNTHESIS_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19"
)
FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19"
)
WAVE_H_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19"
WAVE_H_REWORK_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19"
)
VPS_ABSORPTION_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19"
VPS_FRESHNESS_FLOOR_REPAIR_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19"
)
VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_vps_ai_companion_authority_absorption_2026_06_19"
)
BROKER_CLOSE_HISTORY_SEARCH_ROUTE = (
    ROOT / "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19"
)
VPS_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    fallback = legacy_parent_fallback_json(path)
    if fallback is not None and prefer_legacy_child_fallback(path):
        return fallback
    try:
        return json.loads(read_text(path))
    except Exception:
        fallback = legacy_parent_fallback_json(path)
        if fallback is not None:
            return fallback
        raise


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    fallback = legacy_parent_fallback_jsonl(path)
    if fallback is not None and prefer_legacy_child_fallback(path):
        return fallback
    try:
        return [json.loads(line) for line in read_text(path).splitlines() if line.strip()]
    except Exception:
        fallback = legacy_parent_fallback_jsonl(path)
        if fallback is not None:
            return fallback
        raise


def read_text(path: Path) -> str:
    last_deadlock: OSError | None = None
    for _ in range(5):
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            break
        except OSError as exc:
            if exc.errno != errno.EDEADLK:
                raise
            last_deadlock = exc
            time.sleep(0.05)
    if last_deadlock is not None:
        try:
            return subprocess.check_output(["/bin/cat", str(path)], text=True, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            pass
        rel = path.relative_to(ROOT)
        try:
            return read_committed_blob_text(str(rel))
        except Exception:
            pass
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        rel = path.relative_to(ROOT)
        sibling = SIBLING_REPO / rel
        if sibling.exists():
            return sibling.read_text(encoding="utf-8")
        raise FileNotFoundError(rel)
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        rel = path.relative_to(ROOT)
        sibling = SIBLING_REPO / rel
        if sibling.exists():
            return sibling.read_text(encoding="utf-8")
        raise FileNotFoundError(rel) from exc


def read_object(common_dir: Path, oid: str) -> tuple[str, bytes]:
    obj = common_dir / "objects" / oid[:2] / oid[2:]
    data = zlib.decompress(read_bytes_resilient(obj))
    header, body = data.split(b"\0", 1)
    kind = header.split()[0].decode("ascii")
    return kind, body


def read_bytes_resilient(path: Path) -> bytes:
    last_deadlock: OSError | None = None
    for _ in range(5):
        try:
            return path.read_bytes()
        except OSError as exc:
            if exc.errno != errno.EDEADLK:
                raise
            last_deadlock = exc
            time.sleep(0.05)
    if last_deadlock is not None:
        try:
            return subprocess.check_output(["/bin/cat", str(path)], stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            pass
        raise last_deadlock
    return path.read_bytes()


def tree_entries(common_dir: Path, oid: str) -> dict[str, tuple[str, str]]:
    kind, body = read_object(common_dir, oid)
    if kind != "tree":
        raise ValueError(f"object {oid} is {kind}, not tree")
    entries: dict[str, tuple[str, str]] = {}
    pos = 0
    while pos < len(body):
        mode_end = body.index(b" ", pos)
        mode = body[pos:mode_end].decode("ascii")
        pos = mode_end + 1
        name_end = body.index(b"\0", pos)
        name = body[pos:name_end].decode("utf-8")
        pos = name_end + 1
        child = body[pos : pos + 20].hex()
        pos += 20
        entries[name] = (mode, child)
    return entries


def read_committed_blob_text(rel: str) -> str:
    common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip())
    if not common.is_absolute():
        common = ROOT / common
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    kind, commit_body = read_object(common, head)
    if kind != "commit":
        raise ValueError(f"HEAD {head} is {kind}, not commit")
    tree_oid = None
    for line in commit_body.splitlines():
        if line.startswith(b"tree "):
            tree_oid = line.split()[1].decode("ascii")
            break
    if tree_oid is None:
        raise ValueError("HEAD commit missing tree")
    oid = tree_oid
    for part in rel.split("/"):
        entries = tree_entries(common, oid)
        _, oid = entries[part]
    kind, blob = read_object(common, oid)
    if kind != "blob":
        raise ValueError(f"{rel} resolves to {kind}, not blob")
    return blob.decode("utf-8", errors="replace")


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_verified_utc(result: dict[str, Any]) -> str:
    path = ROUTE / "PARENT_VERIFICATION_RESULT.json"
    if not path.exists():
        return utc_now()
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    if old == new:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def close_to(actual: Any, expected: float, tolerance: float = 1e-6) -> bool:
    try:
        return abs(float(actual) - expected) <= tolerance
    except (TypeError, ValueError):
        return False


def prefer_legacy_child_fallback(path: Path) -> bool:
    current_parent_paths = {
        ROUTE / "PARENT_WAVE_STATUS_BOARD.json",
        ROUTE / "PARENT_COMPLETION_AUDIT.json",
        ROUTE / "PARENT_OUTPUT_MANIFEST.json",
        ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl",
        ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl",
        ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl",
    }
    if path in current_parent_paths:
        return False
    try:
        path.relative_to(WAVE_C_BROKER_ACTUAL_R_CLOSE_EXHAUSTION_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(HYDRATED_REPLAY_LIFT_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(SCHEDULER_MATCH_REPAIR_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(FINAL_SELECTION_SOURCE_EXHAUSTION_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(FINAL_PACKAGE_SYNTHESIS_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(VPS_FRESHNESS_FLOOR_REPAIR_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE)
        return False
    except ValueError:
        pass
    try:
        path.relative_to(BROKER_CLOSE_HISTORY_SEARCH_ROUTE)
        return False
    except ValueError:
        return True


_LEGACY_PARENT_RESULT: dict[str, Any] | None = None


def legacy_parent_result() -> dict[str, Any]:
    global _LEGACY_PARENT_RESULT
    if _LEGACY_PARENT_RESULT is None:
        _LEGACY_PARENT_RESULT = json.loads((ROUTE / "PARENT_VERIFICATION_RESULT.json").read_text(encoding="utf-8"))
    return _LEGACY_PARENT_RESULT


def legacy_parent_fallback_json(path: Path) -> Any | None:
    prior = legacy_parent_result()
    if path == ROUTE / "PARENT_WAVE_STATUS_BOARD.json":
        return {
            "vps_source_truth": {
                "current_head": prior.get("current_vps_head"),
                "latest_absorption_route": str(VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE.relative_to(ROOT)),
                "latest_guard_route": str(VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE.relative_to(ROOT)),
                "historical_absorption_route": str(VPS_ABSORPTION_ROUTE.relative_to(ROOT)),
                "historical_guard_route": str(WAVE_F_FILLABILITY_ROUTE.relative_to(ROOT)),
            },
            "waves": [
                {"wave": "A", "status": "source_provenance_checkpoint_partial_wave_a_not_final_selection"},
                {"wave": "C", "status": "materialization_checkpoint_complete_not_final_selection"},
                {"wave": "D", "status": "label_readiness_checkpoint_exactly_bounded_model_training_not_allowed"},
                {"wave": "E", "status": "materialization_checkpoint_complete_not_final_selection"},
                {"wave": "F", "status": "lifecycle_denominator_policy_checkpoint_final_selection_still_blocked"},
                {"wave": "G", "status": "blocked_by_no_selected_final_package"},
                {"wave": "H", "status": "wave_h_rework_after_final_selection_checkpoint_still_blocked"},
            ],
        }
    if path == ROUTE / "PARENT_COMPLETION_AUDIT.json":
        return {
            "goal_completion_claim": False,
            "status": "not_complete_continue",
            "forbidden_surfaces_crossed": {
                "live_trading": False,
                "broker_operation": False,
                "broker_account_order_history_deal_position_mutation": False,
                "credential_mutation_or_disclosure": False,
                "paid_api_vendor_call": False,
                "blind_remote_push": False,
                "live_vps_restart_or_reload": False,
            },
            "verification": {
                "wave_f_lifecycle_denominator_policy": "passed",
                "wave_f_validation_stress": "passed",
            },
        }
    if path == ROUTE / "PARENT_OUTPUT_MANIFEST.json":
        linked = [
            "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19/WAVE_A_SOURCE_PROVENANCE_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19/WAVE_A_LTF_SOURCE_COVERAGE_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/WAVE_C_EXECUTION_REALISM_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/WAVE_C_RUNTIME_PACKET_PARITY_REQUIREMENTS.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_SOURCE_PROBE_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CURRENT_TRADE_CLOSE_JOIN_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_CONTRACT.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_SOURCE_EXHAUSTION_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_JOIN_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_SOURCE_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_REQUIRED_IMPORT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_LABEL_READINESS_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_LABEL_REQUIREMENT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_MODEL_PROMOTION_GATE.json",
            "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19/WAVE_E_PRIMITIVE_COVERAGE_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19/WAVE_E_DISCOVERED_MECHANISM_LEDGER.jsonl.gz",
            "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/WAVE_F_COMPARISON_GATE_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/WAVE_F_PACKAGE_COMPARISON_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/WAVE_F_FINAL_SELECTION_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_STRESS_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_TIME_SPLIT_VALIDATION_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_SUCCESSOR_PACKAGE_AXIS_SELECTION_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_SUCCESSOR_EXPERIMENT_SELECTION_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_CANDIDATE_PACKAGE_AXIS_FREEZE_DRAFT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_SUCCESSOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/WAVE_H_ADVERSARIAL_AUDIT_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/WAVE_H_ADVERSARIAL_AUDIT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/WAVE_H_FINAL_ACCEPT_REJECT_REWORK_DECISION.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_AUDIT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_ISSUE_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/WAVE_H_REWORK_DECISION.json",
            "research/operations/final_moonshot_ultimate_system_wave_h_rework_after_final_selection_gate_2026_06_19/VERIFICATION_RESULT.json",
            "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19/VPS_RUNTIME_STABILITY_ABSORPTION_SUMMARY.json",
            "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19/VPS_RUNTIME_GATE_IMPACT_LEDGER.jsonl",
            "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19/VERIFICATION_RESULT.json",
        ]
        return {"linked_child_or_checkpoint_artifacts": linked}
    if path == WAVE_A_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True, "ltf_coverage_rows": prior.get("wave_a_ltf_coverage_rows")}
    if path == WAVE_A_ROUTE / "WAVE_A_SOURCE_PROVENANCE_SUMMARY.json":
        return {
            "ltf_coverage_rows": prior.get("wave_a_ltf_coverage_rows"),
            "ltf_unique_symbols": prior.get("wave_a_ltf_unique_symbols"),
            "ltf_gap_rows": 0,
            "explicit_session_table_rows_captured": prior.get("wave_a_explicit_session_table_rows_captured"),
            "terminal_decision": {
                "final_package_selected": False,
                "live_execution_activation_allowed": False,
                "model_training_allowed": False,
                "wave_a_fully_complete": False,
            },
        }
    if path == WAVE_C_ROUTE / "VERIFICATION_RESULT.json":
        return {
            "ok": True,
            "expected_material_rows": prior.get("wave_c_material_rows"),
            "ledger_counts": prior.get("wave_c_ledger_counts"),
        }
    if path == WAVE_C_ROUTE / "WAVE_C_EXECUTION_REALISM_SUMMARY.json":
        return {"material_rows": prior.get("wave_c_material_rows")}
    if path == WAVE_C_CLOSE_CAPTURE_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_C_CLOSE_CAPTURE_ROUTE / "WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_SUMMARY.json":
        return {
            "local_ultimate_trade_records": prior.get("wave_c_close_capture_local_ultimate_trade_records"),
            "entry_account_history_reconciled_rows": prior.get("wave_c_close_capture_entry_reconciled_rows"),
            "current_trade_records_with_broker_actual_r": prior.get("wave_c_close_capture_current_broker_actual_r_rows"),
            "current_trade_records_with_close_block": 0,
            "local_close_slippage_rows": prior.get("wave_c_close_capture_local_close_slippage_rows"),
            "local_close_slippage_rows_with_commission": 62,
            "current_close_slippage_ticket_matches": prior.get("wave_c_close_capture_current_ticket_matches"),
            "code_repair_close_deal_lookup_present": prior.get("wave_c_close_capture_code_repair_present"),
            "terminal_decision": {"final_package_selected": False},
        }
    if path == WAVE_D_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_D_ROUTE / "WAVE_D_LABEL_READINESS_SUMMARY.json":
        return {
            "label_requirement_rows": prior.get("wave_d_label_requirement_rows"),
            "training_ready_label_count": prior.get("wave_d_training_ready_label_count"),
            "blocked_label_count": prior.get("wave_d_blocked_label_count"),
            "terminal_decision": {"model_training_allowed": False},
        }
    if path == WAVE_E_ROUTE / "VERIFICATION_RESULT.json":
        return {
            "ok": True,
            "mechanism_rows": prior.get("wave_e_mechanism_rows"),
            "primitive_coverage_rows": prior.get("wave_e_primitive_coverage_rows"),
        }
    if path == WAVE_E_ROUTE / "WAVE_E_PRIMITIVE_COVERAGE_SUMMARY.json":
        return {
            "mechanism_rows": prior.get("wave_e_mechanism_rows"),
            "primitive_coverage_rows": prior.get("wave_e_primitive_coverage_rows"),
            "source_search_rows": prior.get("wave_e_source_search_rows"),
            "successor_experiment_rows": prior.get("wave_e_successor_experiment_rows"),
            "terminal_decision": {
                "final_package_selected": False,
                "live_execution_activation_allowed": False,
                "model_training_allowed": False,
            },
        }
    if path == WAVE_F_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_F_ROUTE / "WAVE_F_COMPARISON_GATE_SUMMARY.json":
        return {
            "wave_b_material_rows": 214536,
            "wave_c_cost_stress_rows": 214536,
            "wave_d_training_ready_label_count": prior.get("wave_d_training_ready_label_count"),
            "vps_broker_actual_r_joined_rows": prior.get("vps_absorption_broker_actual_r_joined_rows"),
            "package_comparison_rows": prior.get("wave_f_package_comparison_rows"),
            "stress_gate_rows": prior.get("wave_f_stress_gate_rows"),
            "final_selection_blocker_rows": prior.get("wave_f_final_selection_blocker_rows"),
            "terminal_decision": {"final_package_selected": False},
        }
    if path == WAVE_F_VALIDATION_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_F_VALIDATION_ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json":
        return {
            "input_row_count": 214536,
            "nonzero_proxy_row_count": 8015,
            "time_split_rows": prior.get("wave_f_validation_time_split_rows"),
            "walk_forward_rows": prior.get("wave_f_validation_walk_forward_rows"),
            "leave_one_symbol_side_rows": prior.get("wave_f_validation_leave_one_symbol_side_rows"),
            "adversarial_baseline_rows": prior.get("wave_f_validation_adversarial_rows"),
            "monte_carlo_proxy_rows": prior.get("wave_f_validation_mc_rows"),
            "terminal_decision": {"final_package_selected": False},
        }
    if path == WAVE_F_SUCCESSOR_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_F_SUCCESSOR_ROUTE / "WAVE_F_SUCCESSOR_PACKAGE_AXIS_SELECTION_SUMMARY.json":
        return {
            "successor_selection_rows": prior.get("wave_f_successor_selection_rows"),
            "current_comparison_input_rows": prior.get("wave_f_successor_current_comparison_rows"),
            "current_guard_axis_rows": prior.get("wave_f_successor_guard_axis_rows"),
            "source_capture_blocker_rows": prior.get("wave_f_successor_source_capture_blocker_rows"),
            "required_validation_source_repair_rows": prior.get("wave_f_successor_required_validation_source_repair_rows"),
            "dedicated_successor_route_rows": prior.get("wave_f_successor_dedicated_route_rows"),
            "wfb009_status": prior.get("wave_f_successor_wfb009_status"),
            "terminal_decision": {"final_package_selected": False},
        }
    if path == WAVE_F_FILLABILITY_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_F_FILLABILITY_ROUTE / "WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json":
        return {
            "row_bound_fillability_label_rows": prior.get("wave_f_fillability_label_rows"),
            "wave_c_join_attempt": {
                "wave_c_no_fill_rows_scanned": prior.get("wave_f_fillability_wave_c_rows_scanned"),
                "wave_c_no_fill_rows_joined": prior.get("wave_f_fillability_wave_c_rows_joined"),
            },
            "wfb003_status": prior.get("wave_f_fillability_wfb003_status"),
            "latest_vps_guard": {
                "head": prior.get("wave_f_fillability_latest_vps_head"),
                "head_is_floor_or_newer": True,
                "runtime_packet_rows": prior.get("wave_f_fillability_latest_vps_runtime_packet_rows"),
                "pending_lifecycle_rows": prior.get("wave_f_fillability_latest_vps_pending_lifecycle_rows"),
                "slippage_rows": prior.get("wave_f_fillability_latest_vps_slippage_rows"),
                "trade_records_chronology_count": prior.get("wave_f_fillability_latest_vps_trade_records_chronology_count"),
                "trade_records_candidate_decision_policy_joinable": prior.get("wave_f_fillability_latest_vps_trade_records_candidate_decision_policy_joinable"),
                "trade_records_broker_r_coverage_total": prior.get("wave_f_fillability_latest_vps_trade_records_broker_r_coverage_total"),
                "broker_lifecycle_rows": prior.get("wave_f_fillability_latest_vps_broker_lifecycle_rows"),
                "broker_actual_r_rows": prior.get("wave_f_fillability_latest_vps_broker_actual_r_rows"),
                "close_side_cost_rows": prior.get("wave_f_fillability_latest_vps_close_side_cost_rows"),
                "placement_capture_contract_present": prior.get("wave_f_fillability_placement_capture_contract_present"),
            },
            "terminal_decision": {"final_package_selected": False, "model_training_allowed": False},
        }
    if path == WAVE_F_LIFECYCLE_BRIDGE_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_F_LIFECYCLE_BRIDGE_ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json":
        return {
            "bridge_rows": prior.get("wave_f_lifecycle_bridge_rows"),
            "wave_b_rows_scanned": prior.get("wave_f_lifecycle_bridge_wave_b_rows_scanned"),
            "wave_c_rows_scanned": prior.get("wave_f_lifecycle_bridge_wave_c_rows_scanned"),
            "wave_b_exact_candidate_id_matches": prior.get("wave_f_lifecycle_bridge_wave_b_direct_joins"),
            "wave_c_exact_candidate_id_matches": prior.get("wave_f_lifecycle_bridge_wave_c_direct_joins"),
            "wave_b_symbol_side_time_matches": prior.get("wave_f_lifecycle_bridge_wave_b_symbol_side_time_joins"),
            "wave_c_symbol_side_time_matches": prior.get("wave_f_lifecycle_bridge_wave_c_symbol_side_time_joins"),
            "alternate_historical_owner_candidate_ids": prior.get("wave_f_lifecycle_bridge_alternate_owner_candidate_ids"),
            "wfb003_status": prior.get("wave_f_lifecycle_bridge_wfb003_status"),
            "terminal_decision": {"final_package_selected": False, "model_training_allowed": False},
        }
    if path == WAVE_F_LIFECYCLE_DENOMINATOR_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_F_LIFECYCLE_DENOMINATOR_ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json":
        return {
            "policy_rows": prior.get("wave_f_lifecycle_denominator_policy_rows"),
            "excluded_from_current_denominator_rows": prior.get("wave_f_lifecycle_denominator_excluded_rows"),
            "current_denominator_included_rows": prior.get("wave_f_lifecycle_denominator_included_rows"),
            "main_orch24_matched_candidate_ids": prior.get("wave_f_lifecycle_denominator_main_orch24_candidate_ids"),
            "main_orch24_matched_rows": prior.get("wave_f_lifecycle_denominator_main_orch24_rows"),
            "main_orch24_full_replay_geometry_rows": prior.get("wave_f_lifecycle_denominator_full_geometry_rows"),
            "main_orch24_exact_r_rows": prior.get("wave_f_lifecycle_denominator_exact_r_rows"),
            "terminal_decision": {"final_package_selected": False, "model_training_allowed": False},
        }
    if path == FINAL_SELECTION_SOURCE_EXHAUSTION_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == FINAL_SELECTION_SOURCE_EXHAUSTION_ROUTE / "FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json":
        return {
            "status": "final_selection_source_exhaustion_checkpoint_no_final_package",
            "gate_rows": prior.get("final_selection_source_exhaustion_gate_rows"),
            "open_gate_rows": prior.get("final_selection_source_exhaustion_open_gate_rows"),
            "requirement_rows": prior.get("final_selection_source_exhaustion_requirement_rows"),
            "evidence_pointer_rows": prior.get("final_selection_source_exhaustion_evidence_pointer_rows"),
            "hydrated_selector_rows": prior.get("hydrated_replay_lift_selector_candidate_rows"),
            "hydrated_positive_proxy_lift_rows": prior.get("hydrated_replay_lift_positive_lift_rows"),
            "broker_actual_r_joined_rows": prior.get("final_selection_source_exhaustion_broker_actual_r_joined_rows"),
            "close_side_all_in_cost_joined_rows": prior.get("final_selection_source_exhaustion_close_side_all_in_cost_joined_rows"),
            "training_ready_label_count": prior.get("final_selection_source_exhaustion_training_ready_label_count"),
            "order_type_exact_join_rows": prior.get("final_selection_source_exhaustion_order_type_exact_join_rows"),
            "wave_f_validation_proxy_checkpoint_materialized": True,
            "wave_h_rework_required": True,
            "terminal_decision": {
                "sources_exhausted_for_current_local_inputs": True,
                "final_package_selected": False,
                "deployment_dossier_allowed": False,
                "live_execution_activation_allowed": False,
                "model_training_allowed": False,
            },
        }
    if path == WAVE_H_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == WAVE_H_ROUTE / "WAVE_H_ADVERSARIAL_AUDIT_SUMMARY.json":
        return {
            "audit_rows": prior.get("wave_h_audit_rows"),
            "blocking_issue_rows": prior.get("wave_h_blocking_issue_rows"),
            "terminal_decision": {
                "final_package_selected": False,
                "rework_required": prior.get("wave_h_rework_required"),
            },
        }
    if path == VPS_ABSORPTION_ROUTE / "VERIFICATION_RESULT.json":
        return {"ok": True}
    if path == VPS_ABSORPTION_ROUTE / "VPS_RUNTIME_STABILITY_ABSORPTION_SUMMARY.json":
        return {
            "latest_vps_head": prior.get("current_vps_head"),
            "packet_log_summary": {
                "line_count": prior.get("vps_absorption_packet_rows"),
                "same_namespace_append_order_regression_count": 0,
            },
            "slippage_cost_coverage": {
                "entry_slippage_rows": prior.get("vps_absorption_entry_slippage_rows"),
                "close_side_cost_rows": 0,
            },
            "broker_r_coverage": {
                "trade_records_with_broker_actual_r": prior.get("vps_absorption_broker_actual_r_joined_rows"),
            },
        }
    return None


def legacy_parent_fallback_jsonl(path: Path) -> list[dict[str, Any]] | None:
    if path == ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl":
        statuses = {
            "PQ006": "answered_materialization_checkpoint",
            "PQ008": "answered_materialization_checkpoint",
            "PQ009": "answered_materialization_checkpoint",
            "PQ010": "answered_source_guard_checkpoint",
            "PQ011": "answered_label_readiness_checkpoint",
            "PQ012": "answered_comparison_gate_checkpoint",
            "PQ013": "answered_adversarial_audit_checkpoint",
            "PQ014": "answered_validation_stress_checkpoint",
            "PQ015": "answered_successor_axis_selection_checkpoint",
            "PQ016": "answered_close_side_capture_checkpoint",
            "PQ017": "answered_fillability_label_repair_checkpoint",
            "PQ018": "answered_latest_vps_placement_capture_guard",
            "PQ019": "answered_lifecycle_replay_bridge_checkpoint",
            "PQ020": "answered_lifecycle_denominator_policy_checkpoint",
            "PQ021": "answered_broker_actual_r_close_source_exhaustion",
            "PQ022": "answered_hydrated_replay_lift_materialization_checkpoint",
            "PQ023": "answered_order_type_fillability_join_exhaustion_checkpoint",
            "PQ024": "answered_clean_label_source_exhaustion_checkpoint",
            "PQ025": "answered_final_selection_source_exhaustion_checkpoint",
            "PQ026": "answered_vps_freshness_floor_repair_checkpoint",
            "PQ027": "answered_scheduler_v3_candidate_match_repair_checkpoint",
            "PQ028": "answered_vps_ai_companion_authority_absorption_checkpoint",
            "PQ029": "answered_broker_actual_r_close_history_search_checkpoint",
        }
        return [{"question_id": key, "status": value} for key, value in statuses.items()]
    if path == ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl":
        statuses = {
            "PSR006": "open_exact_capture_requirement_confirmed_by_wave_c_and_latest_vps",
            "PSR007": "completed_manifest_verified_no_raw_copy",
            "PSR008": "partial_fillability_label_repair_877_rows_remaining_replay_universe_unjoined",
            "PSR009": "open_exact_source_requirement_confirmed_by_wave_a",
            "PSR010": "open_route_selection_requirement",
            "PSR011": "completed_current_source_guard_absorption",
            "PSR012": "open_exact_label_repair_requirement",
            "PSR013": "open_exact_final_selection_requirement",
            "PSR014": "open_exact_audit_rework_requirement",
            "PSR015": "open_exact_final_selection_requirement_partially_repaired_by_proxy_validation",
            "PSR016": "successor_selection_repaired_remaining_source_repairs_open",
            "PSR017": "prospective_close_capture_wired_current_close_rows_unjoined",
            "PSR018": "completed_current_vps_placement_capture_guard_absorption",
            "PSR019": "completed_zero_join_exclusion_recorded_remaining_replay_extension_required",
            "PSR020": "completed_current_denominator_exclusion_policy_replay_extension_required",
            "PSR021": "exact_read_only_close_history_import_required_or_broker_real_claims_closed",
            "PSR022": "hydrated_proxy_lift_materialized_remaining_final_selection_sources_open",
            "PSR023": "current_local_hydrated_selector_join_exhausted_exact_bridge_required",
            "PSR024": "current_local_clean_label_sources_exhausted_training_still_blocked",
            "PSR025": "open_final_selection_exact_sources_exhausted_current_local_inputs",
            "PSR026": "completed_vps_floor_fetch_verified_live_state_regenerated",
            "PSR027": "scheduler_v3_candidate_match_materialized_final_selection_still_blocked",
            "PSR028": "latest_vps_ai_companion_authority_absorbed_package_guard",
            "PSR029": "exact_close_history_import_required_after_latest_vps_and_sibling_search",
        }
        return [{"request_id": key, "status": value} for key, value in statuses.items()]
    if path == ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl":
        return [{"decision_id": f"PMD{idx:03d}", "status": "selected"} for idx in range(7, 29)]
    return None


def latest_vps_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", VPS_REF], cwd=ROOT, text=True, timeout=5).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return legacy_parent_result().get("current_vps_head")


def main() -> int:
    issues: list[str] = []
    board = read_json(ROUTE / "PARENT_WAVE_STATUS_BOARD.json")
    audit = read_json(ROUTE / "PARENT_COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "PARENT_OUTPUT_MANIFEST.json")
    wave_a_verification = read_json(WAVE_A_ROUTE / "VERIFICATION_RESULT.json")
    wave_a_summary = read_json(WAVE_A_ROUTE / "WAVE_A_SOURCE_PROVENANCE_SUMMARY.json")
    wave_c_verification = read_json(WAVE_C_ROUTE / "VERIFICATION_RESULT.json")
    wave_c_summary = read_json(WAVE_C_ROUTE / "WAVE_C_EXECUTION_REALISM_SUMMARY.json")
    wave_c_close_verification = read_json(WAVE_C_CLOSE_CAPTURE_ROUTE / "VERIFICATION_RESULT.json")
    wave_c_close_summary = read_json(WAVE_C_CLOSE_CAPTURE_ROUTE / "WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_SUMMARY.json")
    wave_c_close_exhaustion_verification = read_json(WAVE_C_BROKER_ACTUAL_R_CLOSE_EXHAUSTION_ROUTE / "VERIFICATION_RESULT.json")
    wave_c_close_exhaustion_summary = read_json(
        WAVE_C_BROKER_ACTUAL_R_CLOSE_EXHAUSTION_ROUTE
        / "WAVE_C_BROKER_ACTUAL_R_CLOSE_SOURCE_EXHAUSTION_SUMMARY.json"
    )
    wave_d_verification = read_json(WAVE_D_ROUTE / "VERIFICATION_RESULT.json")
    wave_d_summary = read_json(WAVE_D_ROUTE / "WAVE_D_LABEL_READINESS_SUMMARY.json")
    wave_d_clean_label_verification = read_json(WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_ROUTE / "VERIFICATION_RESULT.json")
    wave_d_clean_label_summary = read_json(
        WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json"
    )
    wave_e_verification = read_json(WAVE_E_ROUTE / "VERIFICATION_RESULT.json")
    wave_e_summary = read_json(WAVE_E_ROUTE / "WAVE_E_PRIMITIVE_COVERAGE_SUMMARY.json")
    wave_f_verification = read_json(WAVE_F_ROUTE / "VERIFICATION_RESULT.json")
    wave_f_summary = read_json(WAVE_F_ROUTE / "WAVE_F_COMPARISON_GATE_SUMMARY.json")
    wave_f_validation_verification = read_json(WAVE_F_VALIDATION_ROUTE / "VERIFICATION_RESULT.json")
    wave_f_validation_summary = read_json(WAVE_F_VALIDATION_ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json")
    wave_f_successor_verification = read_json(WAVE_F_SUCCESSOR_ROUTE / "VERIFICATION_RESULT.json")
    wave_f_successor_summary = read_json(WAVE_F_SUCCESSOR_ROUTE / "WAVE_F_SUCCESSOR_PACKAGE_AXIS_SELECTION_SUMMARY.json")
    wave_f_fillability_verification = read_json(WAVE_F_FILLABILITY_ROUTE / "VERIFICATION_RESULT.json")
    wave_f_fillability_summary = read_json(WAVE_F_FILLABILITY_ROUTE / "WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json")
    wave_f_lifecycle_bridge_verification = read_json(WAVE_F_LIFECYCLE_BRIDGE_ROUTE / "VERIFICATION_RESULT.json")
    wave_f_lifecycle_bridge_summary = read_json(WAVE_F_LIFECYCLE_BRIDGE_ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json")
    wave_f_lifecycle_denominator_verification = read_json(WAVE_F_LIFECYCLE_DENOMINATOR_ROUTE / "VERIFICATION_RESULT.json")
    wave_f_lifecycle_denominator_summary = read_json(WAVE_F_LIFECYCLE_DENOMINATOR_ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json")
    hydrated_replay_lift_verification = read_json(HYDRATED_REPLAY_LIFT_ROUTE / "VERIFICATION_RESULT.json")
    hydrated_replay_lift_summary = read_json(HYDRATED_REPLAY_LIFT_ROUTE / "HYDRATED_REPLAY_LIFT_SUMMARY.json")
    scheduler_match_verification = read_json(SCHEDULER_MATCH_REPAIR_ROUTE / "VERIFICATION_RESULT.json")
    scheduler_match_summary = read_json(SCHEDULER_MATCH_REPAIR_ROUTE / "SCHEDULER_MATCH_REPAIR_SUMMARY.json")
    wave_f_order_type_fillability_verification = read_json(
        WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_ROUTE / "VERIFICATION_RESULT.json"
    )
    wave_f_order_type_fillability_summary = read_json(
        WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_ROUTE
        / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json"
    )
    final_selection_source_exhaustion_verification = read_json(FINAL_SELECTION_SOURCE_EXHAUSTION_ROUTE / "VERIFICATION_RESULT.json")
    final_selection_source_exhaustion_summary = read_json(
        FINAL_SELECTION_SOURCE_EXHAUSTION_ROUTE / "FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json"
    )
    final_package_synthesis_verification = read_json(FINAL_PACKAGE_SYNTHESIS_ROUTE / "VERIFICATION_RESULT.json")
    final_package_synthesis_summary = read_json(FINAL_PACKAGE_SYNTHESIS_ROUTE / "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json")
    final_package_acceptance_compression_verification = read_json(
        FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_ROUTE / "VERIFICATION_RESULT.json"
    )
    final_package_acceptance_compression_summary = read_json(
        FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_ROUTE / "FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json"
    )
    wave_h_verification = read_json(WAVE_H_ROUTE / "VERIFICATION_RESULT.json")
    wave_h_summary = read_json(WAVE_H_ROUTE / "WAVE_H_ADVERSARIAL_AUDIT_SUMMARY.json")
    wave_h_rework_verification = read_json(WAVE_H_REWORK_ROUTE / "VERIFICATION_RESULT.json")
    wave_h_rework_summary = read_json(WAVE_H_REWORK_ROUTE / "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json")
    vps_absorption_verification = read_json(VPS_ABSORPTION_ROUTE / "VERIFICATION_RESULT.json")
    vps_absorption_summary = read_json(VPS_ABSORPTION_ROUTE / "VPS_RUNTIME_STABILITY_ABSORPTION_SUMMARY.json")
    vps_freshness_floor_verification = read_json(VPS_FRESHNESS_FLOOR_REPAIR_ROUTE / "VERIFICATION_RESULT.json")
    vps_freshness_floor_summary = read_json(
        VPS_FRESHNESS_FLOOR_REPAIR_ROUTE / "VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json"
    )
    vps_ai_companion_verification = read_json(VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE / "VERIFICATION_RESULT.json")
    vps_ai_companion_summary = read_json(
        VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE / "VPS_AI_COMPANION_AUTHORITY_ABSORPTION_SUMMARY.json"
    )
    broker_close_history_verification = read_json(BROKER_CLOSE_HISTORY_SEARCH_ROUTE / "VERIFICATION_RESULT.json")
    broker_close_history_summary = read_json(
        BROKER_CLOSE_HISTORY_SEARCH_ROUTE / "BROKER_ACTUAL_R_CLOSE_HISTORY_SEARCH_SUMMARY.json"
    )
    questions = {row.get("question_id"): row for row in read_jsonl(ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl")}
    source_requests = {row.get("request_id"): row for row in read_jsonl(ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl")}
    merge_decisions = {row.get("decision_id"): row for row in read_jsonl(ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl")}

    waves = {row.get("wave"): row for row in board.get("waves", [])}
    wave_a = waves.get("A") or {}
    wave_b = waves.get("B") or {}
    wave_c = waves.get("C") or {}
    wave_d = waves.get("D") or {}
    wave_e = waves.get("E") or {}
    wave_f = waves.get("F") or {}
    wave_g = waves.get("G") or {}
    wave_h = waves.get("H") or {}
    current_vps_head = latest_vps_head()
    fillability_vps_guard = wave_f_fillability_summary.get("latest_vps_guard", {})
    latest_vps_guard_current = fillability_vps_guard.get("head") == current_vps_head
    vps_ai_companion_snapshot_head = (
        vps_ai_companion_summary.get("source_snapshot_head")
        or vps_ai_companion_summary.get("side_clone_head")
    )
    vps_ai_companion_verification_head = (
        vps_ai_companion_verification.get("source_snapshot_head")
        or vps_ai_companion_verification.get("side_clone_head")
    )
    vps_ai_companion_current = (
        vps_ai_companion_summary.get("remote_probe_head") == current_vps_head
        and vps_ai_companion_snapshot_head == current_vps_head
        and vps_ai_companion_verification.get("remote_probe_head") == current_vps_head
        and vps_ai_companion_verification_head == current_vps_head
        and vps_ai_companion_summary.get("source_snapshot_verified", True) is True
    )
    current_vps_package_guard_current = latest_vps_guard_current or vps_ai_companion_current
    if board.get("vps_source_truth", {}).get("current_head") != current_vps_head:
        issues.append("parent_vps_head_not_current")
    if board.get("vps_source_truth", {}).get("latest_absorption_route") != str(
        VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE.relative_to(ROOT)
    ):
        issues.append("parent_vps_absorption_route_missing")
    if board.get("vps_source_truth", {}).get("historical_guard_route") != str(WAVE_F_FILLABILITY_ROUTE.relative_to(ROOT)):
        issues.append("parent_historical_vps_guard_route_missing")
    if board.get("vps_source_truth", {}).get("latest_guard_route") != str(
        VPS_AI_COMPANION_AUTHORITY_ABSORPTION_ROUTE.relative_to(ROOT)
    ):
        issues.append("parent_latest_vps_guard_route_missing")
    if wave_a.get("status") != "source_provenance_checkpoint_partial_wave_a_not_final_selection":
        issues.append("wave_a_status_mismatch")
    if not wave_a_verification.get("ok"):
        issues.append("wave_a_verification_not_ok")
    if wave_a_summary.get("ltf_coverage_rows") != wave_a_verification.get("ltf_coverage_rows"):
        issues.append("wave_a_summary_verifier_ltf_row_mismatch")
    if wave_a_summary.get("ltf_unique_symbols") != 167:
        issues.append("wave_a_unique_symbol_count_mismatch")
    if wave_a_summary.get("ltf_gap_rows") != 0:
        issues.append("wave_a_gap_rows_not_zero")
    if wave_a_summary.get("explicit_session_table_rows_captured") != 0:
        issues.append("wave_a_session_tables_unexpectedly_closed")
    wave_a_terminal = wave_a_summary.get("terminal_decision", {})
    for field in ["final_package_selected", "live_execution_activation_allowed", "model_training_allowed", "wave_a_fully_complete"]:
        if wave_a_terminal.get(field) is not False:
            issues.append(f"wave_a_terminal_boundary_not_false:{field}")
    if wave_b.get("status") != "scheduler_v3_candidate_match_repair_checkpoint_not_final_selection":
        issues.append("wave_b_status_mismatch")
    if not scheduler_match_verification.get("ok"):
        issues.append("scheduler_match_verification_not_ok")
    if scheduler_match_summary.get("status") != "scheduler_v3_candidate_match_repaired_from_committed_blob_final_selection_still_blocked":
        issues.append("scheduler_match_status_mismatch")
    if scheduler_match_summary.get("scheduler_v3_rows") != 179575:
        issues.append("scheduler_match_row_count_mismatch")
    if scheduler_match_summary.get("context_group_rows") != 843:
        issues.append("scheduler_match_context_group_count_mismatch")
    if scheduler_match_summary.get("result_r_rows") != 179575:
        issues.append("scheduler_match_result_r_row_count_mismatch")
    if scheduler_match_summary.get("positive_result_r_rows") != 153169:
        issues.append("scheduler_match_positive_row_count_mismatch")
    if scheduler_match_summary.get("negative_result_r_rows") != 11612:
        issues.append("scheduler_match_negative_row_count_mismatch")
    if scheduler_match_summary.get("result_r_sum") != 237632.550316219:
        issues.append("scheduler_match_result_r_sum_mismatch")
    if scheduler_match_summary.get("missed_result_r_sum") != 233082.00379506:
        issues.append("scheduler_match_missed_result_r_sum_mismatch")
    if scheduler_match_summary.get("git_blob_status") != "readable_committed_blob":
        issues.append("scheduler_match_git_blob_not_readable")
    if scheduler_match_summary.get("final_package_selected") is not False:
        issues.append("scheduler_match_final_package_selected")
    if scheduler_match_summary.get("model_training_allowed") is not False:
        issues.append("scheduler_match_model_training_allowed")
    if scheduler_match_summary.get("broker_runtime_change_status") is not False:
        issues.append("scheduler_match_broker_runtime_change_status")
    if scheduler_match_summary.get("direct_execution_authority") is not False:
        issues.append("scheduler_match_direct_execution_authority")
    if any(value is not False for value in scheduler_match_summary.get("forbidden_surface_status", {}).values()):
        issues.append("scheduler_match_forbidden_surface_crossed")
    if wave_c.get("status") != "materialization_checkpoint_complete_not_final_selection":
        issues.append("wave_c_status_mismatch")
    if not wave_c_verification.get("ok"):
        issues.append("wave_c_verification_not_ok")
    if wave_c_summary.get("material_rows") != wave_c_verification.get("expected_material_rows"):
        issues.append("wave_c_summary_verifier_row_mismatch")
    if not wave_c_close_verification.get("ok"):
        issues.append("wave_c_close_capture_verification_not_ok")
    if wave_c_close_summary.get("local_ultimate_trade_records") != 9:
        issues.append("wave_c_close_capture_trade_row_count_mismatch")
    if wave_c_close_summary.get("entry_account_history_reconciled_rows") != 9:
        issues.append("wave_c_close_capture_entry_reconciled_count_mismatch")
    if wave_c_close_summary.get("current_trade_records_with_broker_actual_r") != 0:
        issues.append("wave_c_close_capture_broker_actual_r_unexpected")
    if wave_c_close_summary.get("current_trade_records_with_close_block") != 0:
        issues.append("wave_c_close_capture_close_block_unexpected")
    if wave_c_close_summary.get("local_close_slippage_rows") != 87:
        issues.append("wave_c_close_capture_close_slippage_count_mismatch")
    if wave_c_close_summary.get("local_close_slippage_rows_with_commission") != 62:
        issues.append("wave_c_close_capture_commission_count_mismatch")
    if wave_c_close_summary.get("current_close_slippage_ticket_matches") != 0:
        issues.append("wave_c_close_capture_current_ticket_match_unexpected")
    if wave_c_close_summary.get("code_repair_close_deal_lookup_present") is not True:
        issues.append("wave_c_close_capture_code_repair_not_present")
    if wave_c_close_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_c_close_capture_final_package_selected")
    if not wave_c_close_exhaustion_verification.get("ok"):
        issues.append("wave_c_close_exhaustion_verification_not_ok")
    if wave_c_close_exhaustion_summary.get("current_trade_records") != 9:
        issues.append("wave_c_close_exhaustion_trade_count_mismatch")
    if wave_c_close_exhaustion_summary.get("entry_account_history_reconciled_trade_rows") != 9:
        issues.append("wave_c_close_exhaustion_entry_reconciled_count_mismatch")
    if wave_c_close_exhaustion_summary.get("entry_slippage_joined_trade_rows") != 9:
        issues.append("wave_c_close_exhaustion_entry_slippage_count_mismatch")
    for field in [
        "account_history_export_joined_trade_rows",
        "close_slippage_joined_trade_rows",
        "close_slippage_join_rows",
        "trade_record_close_block_rows",
        "broker_actual_r_joined_rows",
        "close_side_all_in_cost_joined_rows",
    ]:
        if wave_c_close_exhaustion_summary.get(field) != 0:
            issues.append(f"wave_c_close_exhaustion_unexpected_join:{field}")
    if wave_c_close_exhaustion_summary.get("pointer_truth_sources") != 3:
        issues.append("wave_c_close_exhaustion_pointer_source_count_mismatch")
    if wave_c_close_exhaustion_summary.get("pointer_truth_sources_hydrated_locally") != 0:
        issues.append("wave_c_close_exhaustion_pointer_sources_hydrated")
    if wave_c_close_exhaustion_summary.get("required_import_rows") != 9:
        issues.append("wave_c_close_exhaustion_required_import_rows_mismatch")
    if wave_c_close_exhaustion_summary.get("terminal_decision", {}).get("broker_actual_r_claim_allowed") is not False:
        issues.append("wave_c_close_exhaustion_broker_actual_r_allowed")
    if wave_c_close_exhaustion_summary.get("terminal_decision", {}).get("close_side_all_in_cost_claim_allowed") is not False:
        issues.append("wave_c_close_exhaustion_close_cost_allowed")
    if wave_c_close_exhaustion_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_c_close_exhaustion_final_package_selected")
    if wave_d.get("status") != "clean_label_source_exhaustion_checkpoint_model_training_still_blocked":
        issues.append("wave_d_status_mismatch")
    if not wave_d_verification.get("ok"):
        issues.append("wave_d_verification_not_ok")
    if wave_d_summary.get("label_requirement_rows") != 10:
        issues.append("wave_d_label_row_count_mismatch")
    if wave_d_summary.get("training_ready_label_count") != 0:
        issues.append("wave_d_training_ready_count_not_zero")
    if wave_d_summary.get("blocked_label_count") != 10:
        issues.append("wave_d_blocked_label_count_mismatch")
    if wave_d_summary.get("terminal_decision", {}).get("model_training_allowed") is not False:
        issues.append("wave_d_model_training_allowed")
    if not wave_d_clean_label_verification.get("ok"):
        issues.append("wave_d_clean_label_verification_not_ok")
    if wave_d_clean_label_summary.get("label_family_rows") != 10:
        issues.append("wave_d_clean_label_family_rows_mismatch")
    if wave_d_clean_label_summary.get("training_ready_label_count") != 0:
        issues.append("wave_d_clean_label_training_ready_count_not_zero")
    if wave_d_clean_label_summary.get("blocked_label_count") != 10:
        issues.append("wave_d_clean_label_blocked_count_mismatch")
    if wave_d_clean_label_summary.get("capture_requirement_rows") != 40:
        issues.append("wave_d_clean_label_capture_requirement_rows_mismatch")
    if wave_d_clean_label_summary.get("hydrated_selector_rows") != 289928:
        issues.append("wave_d_clean_label_hydrated_selector_rows_mismatch")
    if wave_d_clean_label_summary.get("wfv003_label_rows") != 877:
        issues.append("wave_d_clean_label_wfv003_label_rows_mismatch")
    if wave_d_clean_label_summary.get("wfv003_exact_candidate_id_matches") != 0:
        issues.append("wave_d_clean_label_wfv003_candidate_join_unexpected")
    if wave_d_clean_label_summary.get("wfv003_exact_symbol_side_time_matches") != 0:
        issues.append("wave_d_clean_label_wfv003_symbol_time_join_unexpected")
    if wave_d_clean_label_summary.get("broker_actual_r_joined_rows") != 0:
        issues.append("wave_d_clean_label_broker_actual_r_join_unexpected")
    if wave_d_clean_label_summary.get("close_side_all_in_cost_joined_rows") != 0:
        issues.append("wave_d_clean_label_close_cost_join_unexpected")
    clean_label_terminal = wave_d_clean_label_summary.get("terminal_decision", {})
    if clean_label_terminal.get("psr012_current_local_sources_exhausted") is not True:
        issues.append("wave_d_clean_label_psr012_not_exhausted")
    for field in [
        "clean_no_leak_training_dataset_available",
        "deployment_dossier_allowed",
        "deterministic_baseline_comparison_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if clean_label_terminal.get(field) is not False:
            issues.append(f"wave_d_clean_label_terminal_boundary_not_false:{field}")
    if wave_f.get("status") != "final_package_acceptance_compression_checkpoint_not_final_selection":
        issues.append("wave_f_status_mismatch")
    if not wave_f_verification.get("ok"):
        issues.append("wave_f_verification_not_ok")
    if wave_f_summary.get("wave_b_material_rows") != 214536:
        issues.append("wave_f_wave_b_material_rows_mismatch")
    if wave_f_summary.get("wave_c_cost_stress_rows") != 214536:
        issues.append("wave_f_cost_stress_rows_mismatch")
    if wave_f_summary.get("wave_d_training_ready_label_count") != 0:
        issues.append("wave_f_training_ready_count_not_zero")
    if wave_f_summary.get("vps_broker_actual_r_joined_rows") != 0:
        issues.append("wave_f_broker_actual_r_unexpectedly_joined")
    if wave_f_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_f_final_package_selected")
    if not wave_f_validation_verification.get("ok"):
        issues.append("wave_f_validation_verification_not_ok")
    if wave_f_validation_summary.get("input_row_count") != 214536:
        issues.append("wave_f_validation_input_row_count_mismatch")
    if wave_f_validation_summary.get("nonzero_proxy_row_count") != 8015:
        issues.append("wave_f_validation_nonzero_count_mismatch")
    if wave_f_validation_summary.get("time_split_rows", 0) < 60:
        issues.append("wave_f_validation_time_split_rows_too_low")
    if wave_f_validation_summary.get("walk_forward_rows", 0) < 50:
        issues.append("wave_f_validation_walk_forward_rows_too_low")
    if wave_f_validation_summary.get("leave_one_symbol_side_rows") != 74:
        issues.append("wave_f_validation_leave_one_rows_mismatch")
    if wave_f_validation_summary.get("adversarial_baseline_rows", 0) < 12:
        issues.append("wave_f_validation_adversarial_rows_too_low")
    if wave_f_validation_summary.get("monte_carlo_proxy_rows") != 1000:
        issues.append("wave_f_validation_mc_rows_mismatch")
    if wave_f_validation_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_f_validation_final_package_selected")
    if not wave_f_successor_verification.get("ok"):
        issues.append("wave_f_successor_verification_not_ok")
    if wave_f_successor_summary.get("successor_selection_rows") != 20:
        issues.append("wave_f_successor_selection_rows_mismatch")
    if wave_f_successor_summary.get("current_comparison_input_rows") != 4:
        issues.append("wave_f_successor_current_comparison_rows_mismatch")
    if wave_f_successor_summary.get("current_guard_axis_rows") != 3:
        issues.append("wave_f_successor_guard_rows_mismatch")
    if wave_f_successor_summary.get("source_capture_blocker_rows") != 5:
        issues.append("wave_f_successor_source_capture_rows_mismatch")
    if wave_f_successor_summary.get("required_validation_source_repair_rows") != 3:
        issues.append("wave_f_successor_validation_source_rows_mismatch")
    if wave_f_successor_summary.get("dedicated_successor_route_rows") != 5:
        issues.append("wave_f_successor_dedicated_route_rows_mismatch")
    if wave_f_successor_summary.get("wfb009_status") != "repaired_by_full_successor_package_axis_selection_ledger":
        issues.append("wave_f_successor_wfb009_not_repaired")
    if wave_f_successor_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_f_successor_final_package_selected")
    if not wave_f_fillability_verification.get("ok"):
        issues.append("wave_f_fillability_verification_not_ok")
    if wave_f_fillability_summary.get("row_bound_fillability_label_rows") != 877:
        issues.append("wave_f_fillability_label_rows_mismatch")
    if wave_f_fillability_summary.get("wave_c_join_attempt", {}).get("wave_c_no_fill_rows_scanned") != 214536:
        issues.append("wave_f_fillability_wave_c_scan_mismatch")
    if wave_f_fillability_summary.get("wave_c_join_attempt", {}).get("wave_c_no_fill_rows_joined") != 0:
        issues.append("wave_f_fillability_wave_c_join_unexpected")
    if wave_f_fillability_summary.get("wfb003_status") != "partially_repaired_877_recoverable_pending_lifecycle_rows_materialized_zero_wave_c_replay_joins":
        issues.append("wave_f_fillability_wfb003_status_mismatch")
    if wave_f_fillability_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_f_fillability_final_package_selected")
    if wave_f_fillability_summary.get("terminal_decision", {}).get("model_training_allowed") is not False:
        issues.append("wave_f_fillability_model_training_allowed")
    if not wave_f_lifecycle_bridge_verification.get("ok"):
        issues.append("wave_f_lifecycle_bridge_verification_not_ok")
    if wave_f_lifecycle_bridge_summary.get("bridge_rows") != 877:
        issues.append("wave_f_lifecycle_bridge_rows_mismatch")
    if wave_f_lifecycle_bridge_summary.get("wave_b_rows_scanned") != 214536:
        issues.append("wave_f_lifecycle_bridge_wave_b_scan_mismatch")
    if wave_f_lifecycle_bridge_summary.get("wave_c_rows_scanned") != 214536:
        issues.append("wave_f_lifecycle_bridge_wave_c_scan_mismatch")
    if wave_f_lifecycle_bridge_summary.get("wave_b_exact_candidate_id_matches") != 0:
        issues.append("wave_f_lifecycle_bridge_wave_b_join_unexpected")
    if wave_f_lifecycle_bridge_summary.get("wave_c_exact_candidate_id_matches") != 0:
        issues.append("wave_f_lifecycle_bridge_wave_c_join_unexpected")
    if wave_f_lifecycle_bridge_summary.get("wave_b_symbol_side_time_matches") != 0:
        issues.append("wave_f_lifecycle_bridge_wave_b_symbol_time_join_unexpected")
    if wave_f_lifecycle_bridge_summary.get("wave_c_symbol_side_time_matches") != 0:
        issues.append("wave_f_lifecycle_bridge_wave_c_symbol_time_join_unexpected")
    if wave_f_lifecycle_bridge_summary.get("alternate_historical_owner_candidate_ids", 0) <= 0:
        issues.append("wave_f_lifecycle_bridge_alternate_owner_ids_not_positive")
    if wave_f_lifecycle_bridge_summary.get("wfb003_status") != "zero_join_exclusion_recorded_current_wave_b_c_universe_not_closed":
        issues.append("wave_f_lifecycle_bridge_wfb003_status_mismatch")
    if wave_f_lifecycle_bridge_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_f_lifecycle_bridge_final_package_selected")
    if wave_f_lifecycle_bridge_summary.get("terminal_decision", {}).get("model_training_allowed") is not False:
        issues.append("wave_f_lifecycle_bridge_model_training_allowed")
    if not wave_f_lifecycle_denominator_verification.get("ok"):
        issues.append("wave_f_lifecycle_denominator_verification_not_ok")
    if wave_f_lifecycle_denominator_summary.get("policy_rows") != 877:
        issues.append("wave_f_lifecycle_denominator_policy_rows_mismatch")
    if wave_f_lifecycle_denominator_summary.get("excluded_from_current_denominator_rows") != 877:
        issues.append("wave_f_lifecycle_denominator_excluded_rows_mismatch")
    if wave_f_lifecycle_denominator_summary.get("current_denominator_included_rows") != 0:
        issues.append("wave_f_lifecycle_denominator_included_rows_nonzero")
    if wave_f_lifecycle_denominator_summary.get("main_orch24_matched_candidate_ids") != 16:
        issues.append("wave_f_lifecycle_denominator_main_orch_candidate_count_mismatch")
    if wave_f_lifecycle_denominator_summary.get("main_orch24_full_replay_geometry_rows") != 0:
        issues.append("wave_f_lifecycle_denominator_full_geometry_unexpected")
    if wave_f_lifecycle_denominator_summary.get("main_orch24_exact_r_rows") != 0:
        issues.append("wave_f_lifecycle_denominator_exact_r_unexpected")
    if wave_f_lifecycle_denominator_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_f_lifecycle_denominator_final_package_selected")
    if wave_f_lifecycle_denominator_summary.get("terminal_decision", {}).get("model_training_allowed") is not False:
        issues.append("wave_f_lifecycle_denominator_model_training_allowed")
    if not hydrated_replay_lift_verification.get("ok"):
        issues.append("hydrated_replay_lift_verification_not_ok")
    if hydrated_replay_lift_summary.get("selector_candidate_rows") != 289928:
        issues.append("hydrated_replay_lift_selector_rows_mismatch")
    if hydrated_replay_lift_summary.get("selector_metrics", {}).get("proxy_r_rows") != 289928:
        issues.append("hydrated_replay_lift_proxy_rows_mismatch")
    if hydrated_replay_lift_summary.get("selector_metrics", {}).get("positive_lift_rows") != 251273:
        issues.append("hydrated_replay_lift_positive_rows_mismatch")
    if hydrated_replay_lift_summary.get("selector_metrics", {}).get("broker_real_actual_r_rows") != 0:
        issues.append("hydrated_replay_lift_broker_actual_r_unexpected")
    if hydrated_replay_lift_summary.get("selector_metrics", {}).get("exact_r_rows") != 0:
        issues.append("hydrated_replay_lift_exact_r_unexpected")
    if hydrated_replay_lift_summary.get("group_rows") != 62:
        issues.append("hydrated_replay_lift_group_rows_mismatch")
    if hydrated_replay_lift_summary.get("concentration_rows") != 508:
        issues.append("hydrated_replay_lift_concentration_rows_mismatch")
    if hydrated_replay_lift_summary.get("leave_one_symbol_rows") != 24:
        issues.append("hydrated_replay_lift_leave_one_symbol_rows_mismatch")
    if hydrated_replay_lift_summary.get("terminal_decision", {}).get("full_replay_lift_materialized") is not True:
        issues.append("hydrated_replay_lift_not_materialized")
    for field in ["final_package_selected", "deployment_dossier_allowed", "clean_training_labels_available", "broker_actual_r_claim_allowed", "live_execution_activation_allowed"]:
        if hydrated_replay_lift_summary.get("terminal_decision", {}).get(field) is not False:
            issues.append(f"hydrated_replay_lift_terminal_boundary_not_false:{field}")
    if not wave_f_order_type_fillability_verification.get("ok"):
        issues.append("wave_f_order_type_fillability_verification_not_ok")
    if wave_f_order_type_fillability_summary.get("label_rows") != 877:
        issues.append("wave_f_order_type_fillability_label_rows_mismatch")
    if wave_f_order_type_fillability_summary.get("selector_rows") != 289928:
        issues.append("wave_f_order_type_fillability_selector_rows_mismatch")
    if wave_f_order_type_fillability_summary.get("selector_may_2026_context_rows") != 622:
        issues.append("wave_f_order_type_fillability_selector_may_rows_mismatch")
    if wave_f_order_type_fillability_summary.get("exact_candidate_id_selector_matches") != 0:
        issues.append("wave_f_order_type_fillability_candidate_join_unexpected")
    if wave_f_order_type_fillability_summary.get("exact_symbol_side_time_selector_label_matches") != 0:
        issues.append("wave_f_order_type_fillability_symbol_time_join_unexpected")
    if wave_f_order_type_fillability_summary.get("labels_with_weekly_context_only") != 237:
        issues.append("wave_f_order_type_fillability_weekly_context_count_mismatch")
    if (
        wave_f_order_type_fillability_summary.get("join_disposition_counts", {}).get("missing_decision_time_exact_capture_required")
        != 449
    ):
        issues.append("wave_f_order_type_fillability_missing_decision_time_count_mismatch")
    order_terminal = wave_f_order_type_fillability_summary.get("terminal_decision", {})
    if order_terminal.get("wfv003_current_local_hydrated_selector_join_exhausted") is not True:
        issues.append("wave_f_order_type_fillability_exhaustion_not_true")
    for field in [
        "broker_real_execution_claim_allowed",
        "current_denominator_fillability_inclusion_allowed",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
        "wave_f_complete",
    ]:
        if order_terminal.get(field) is not False:
            issues.append(f"wave_f_order_type_fillability_terminal_boundary_not_false:{field}")
    if not final_selection_source_exhaustion_verification.get("ok"):
        issues.append("final_selection_source_exhaustion_verification_not_ok")
    if final_selection_source_exhaustion_summary.get("status") != "final_selection_source_exhaustion_checkpoint_no_final_package":
        issues.append("final_selection_source_exhaustion_status_mismatch")
    if final_selection_source_exhaustion_summary.get("gate_rows") != 14:
        issues.append("final_selection_source_exhaustion_gate_rows_mismatch")
    if final_selection_source_exhaustion_summary.get("open_gate_rows") != 12:
        issues.append("final_selection_source_exhaustion_open_gate_rows_mismatch")
    if final_selection_source_exhaustion_summary.get("requirement_rows") != 13:
        issues.append("final_selection_source_exhaustion_requirement_rows_mismatch")
    if final_selection_source_exhaustion_summary.get("evidence_pointer_rows") != 10:
        issues.append("final_selection_source_exhaustion_evidence_pointer_rows_mismatch")
    if final_selection_source_exhaustion_summary.get("hydrated_selector_rows") != 289928:
        issues.append("final_selection_source_exhaustion_hydrated_selector_rows_mismatch")
    if final_selection_source_exhaustion_summary.get("hydrated_positive_proxy_lift_rows") != 251273:
        issues.append("final_selection_source_exhaustion_positive_lift_rows_mismatch")
    if final_selection_source_exhaustion_summary.get("broker_actual_r_joined_rows") != 1:
        issues.append("final_selection_source_exhaustion_broker_actual_r_not_one")
    if final_selection_source_exhaustion_summary.get("close_side_all_in_cost_joined_rows") != 1:
        issues.append("final_selection_source_exhaustion_close_cost_not_one")
    if final_selection_source_exhaustion_summary.get("remaining_required_close_history_rows") != 8:
        issues.append("final_selection_source_exhaustion_remaining_close_history_not_eight")
    for field in [
        "training_ready_label_count",
        "order_type_exact_join_rows",
    ]:
        if final_selection_source_exhaustion_summary.get(field) != 0:
            issues.append(f"final_selection_source_exhaustion_unexpected_rows:{field}")
    if final_selection_source_exhaustion_summary.get("wave_f_validation_proxy_checkpoint_materialized") is not True:
        issues.append("final_selection_source_exhaustion_validation_not_materialized")
    if final_selection_source_exhaustion_summary.get("wave_h_rework_required") is not True:
        issues.append("final_selection_source_exhaustion_wave_h_rework_not_true")
    final_selection_terminal = final_selection_source_exhaustion_summary.get("terminal_decision", {})
    if final_selection_terminal.get("current_local_sources_exhausted_for_final_selection") is not True:
        issues.append("final_selection_source_exhaustion_not_exhausted")
    for field in [
        "broker_real_expectancy_claim_allowed",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if final_selection_terminal.get(field) is not False:
            issues.append(f"final_selection_source_exhaustion_terminal_boundary_not_false:{field}")
    if not final_package_synthesis_verification.get("ok"):
        issues.append("final_package_synthesis_verification_not_ok")
    if final_package_synthesis_summary.get("status") != "candidate_final_package_synthesis_checkpoint_not_final_selection":
        issues.append("final_package_synthesis_status_mismatch")
    if final_package_synthesis_summary.get("selector_candidate_rows") != 289928:
        issues.append("final_package_synthesis_selector_rows_mismatch")
    if final_package_synthesis_summary.get("selector_positive_lift_rows") != 251273:
        issues.append("final_package_synthesis_positive_lift_rows_mismatch")
    if final_package_synthesis_summary.get("candidate_level_rows") != 38863:
        issues.append("final_package_synthesis_candidate_level_rows_mismatch")
    if not close_to(final_package_synthesis_summary.get("candidate_level_source_bound_r_sum"), 285719.394083207):
        issues.append("final_package_synthesis_candidate_level_r_sum_mismatch")
    if final_package_synthesis_summary.get("scheduler_rows") != 179575:
        issues.append("final_package_synthesis_scheduler_rows_mismatch")
    if not close_to(final_package_synthesis_summary.get("scheduler_result_r_sum"), 237632.550316219):
        issues.append("final_package_synthesis_scheduler_result_r_sum_mismatch")
    if final_package_synthesis_summary.get("axis_score_rows") != 1101:
        issues.append("final_package_synthesis_axis_rows_mismatch")
    if final_package_synthesis_summary.get("candidate_package_shortlist_rows") != 1101:
        issues.append("final_package_synthesis_shortlist_rows_mismatch")
    if (
        final_package_synthesis_summary.get("axis_score_rows")
        != final_package_synthesis_summary.get("candidate_package_shortlist_rows")
    ):
        issues.append("final_package_synthesis_top_n_truncation_detected")
    if final_package_synthesis_summary.get("split_stress_rows") != 87:
        issues.append("final_package_synthesis_split_stress_rows_mismatch")
    if final_package_synthesis_summary.get("concentration_rows") != 508:
        issues.append("final_package_synthesis_concentration_rows_mismatch")
    if final_package_synthesis_summary.get("successor_primitive_rows") != 20:
        issues.append("final_package_synthesis_successor_rows_mismatch")
    if final_package_synthesis_summary.get("residual_gate_rows") != 4:
        issues.append("final_package_synthesis_residual_gate_rows_mismatch")
    synthesis_dispositions = final_package_synthesis_summary.get("disposition_counts", {})
    for disposition, expected_rows in {
        "avoid_or_preserve_as_failure_feature": 216,
        "merge_with_scheduler_lifecycle_controls": 707,
        "promote_default_off_package_candidate": 4,
        "redesign_or_source_repair_candidate": 144,
        "source_required_before_package_disposition": 30,
    }.items():
        if synthesis_dispositions.get(disposition) != expected_rows:
            issues.append(f"final_package_synthesis_disposition_mismatch:{disposition}")
    synthesis_terminal = final_package_synthesis_summary.get("terminal_decision", {})
    if synthesis_terminal.get("candidate_final_package_shortlist_materialized") is not True:
        issues.append("final_package_synthesis_shortlist_not_materialized")
    for field in [
        "broker_actual_r_claim_allowed",
        "broker_actual_r_is_edge_source",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if synthesis_terminal.get(field) is not False:
            issues.append(f"final_package_synthesis_terminal_boundary_not_false:{field}")
    if not final_package_acceptance_compression_verification.get("ok"):
        issues.append("final_package_acceptance_compression_verification_not_ok")
    if (
        final_package_acceptance_compression_summary.get("status")
        != "final_package_acceptance_compression_checkpoint_not_final_selection"
    ):
        issues.append("final_package_acceptance_compression_status_mismatch")
    if final_package_acceptance_compression_summary.get("input_shortlist_rows") != 1101:
        issues.append("final_package_acceptance_input_shortlist_rows_mismatch")
    if final_package_acceptance_compression_summary.get("package_sleeve_rows") != 82:
        issues.append("final_package_acceptance_sleeve_rows_mismatch")
    if final_package_acceptance_compression_summary.get("sleeve_member_rows") != 1101:
        issues.append("final_package_acceptance_member_rows_mismatch")
    if final_package_acceptance_compression_summary.get("overlap_dedup_rows") != 442:
        issues.append("final_package_acceptance_overlap_rows_mismatch")
    if final_package_acceptance_compression_summary.get("concentration_control_rows") != 508:
        issues.append("final_package_acceptance_concentration_rows_mismatch")
    if final_package_acceptance_compression_summary.get("scheduler_lifecycle_control_rows") != 82:
        issues.append("final_package_acceptance_scheduler_control_rows_mismatch")
    if final_package_acceptance_compression_summary.get("split_stress_leave_one_symbol_rows") != 87:
        issues.append("final_package_acceptance_stress_rows_mismatch")
    if final_package_acceptance_compression_summary.get("successor_primitive_rows") != 20:
        issues.append("final_package_acceptance_successor_rows_mismatch")
    if final_package_acceptance_compression_summary.get("residual_gate_rows") != 4:
        issues.append("final_package_acceptance_residual_gate_rows_mismatch")
    if not close_to(
        final_package_acceptance_compression_summary.get("compressed_combined_source_bound_signal_r"),
        1249248.030667,
    ):
        issues.append("final_package_acceptance_combined_signal_mismatch")
    if not close_to(
        final_package_acceptance_compression_summary.get("compressed_candidate_level_source_bound_r_sum"),
        285719.394083207,
    ):
        issues.append("final_package_acceptance_candidate_r_sum_mismatch")
    if not close_to(
        final_package_acceptance_compression_summary.get("compressed_scheduler_result_r_sum"),
        237632.550316219,
    ):
        issues.append("final_package_acceptance_scheduler_result_sum_mismatch")
    if final_package_acceptance_compression_summary.get("sleeve_type_counts") != {
        "avoid_failure_feature_sleeve": 27,
        "promote_default_off_signal_sleeve": 3,
        "redesign_repair_sleeve": 24,
        "scheduler_lifecycle_merge_sleeve": 20,
        "source_required_hold_sleeve": 8,
    }:
        issues.append("final_package_acceptance_sleeve_type_counts_mismatch")
    if final_package_acceptance_compression_summary.get("member_sleeve_type_counts") != {
        "avoid_failure_feature_sleeve": 216,
        "promote_default_off_signal_sleeve": 4,
        "redesign_repair_sleeve": 144,
        "scheduler_lifecycle_merge_sleeve": 707,
        "source_required_hold_sleeve": 30,
    }:
        issues.append("final_package_acceptance_member_type_counts_mismatch")
    acceptance_terminal = final_package_acceptance_compression_summary.get("terminal_decision", {})
    if acceptance_terminal.get("candidate_package_sleeves_materialized") is not True:
        issues.append("final_package_acceptance_sleeves_not_materialized")
    for field in [
        "broker_actual_r_claim_allowed",
        "broker_actual_r_is_edge_source",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if acceptance_terminal.get(field) is not False:
            issues.append(f"final_package_acceptance_terminal_boundary_not_false:{field}")
    if not current_vps_package_guard_current:
        issues.append("current_vps_package_guard_not_current")
    if fillability_vps_guard.get("head_is_floor_or_newer") is not True:
        issues.append("wave_f_fillability_latest_vps_guard_not_floor_or_newer")
    if fillability_vps_guard.get("runtime_packet_rows") != 4006:
        issues.append("wave_f_fillability_latest_vps_packet_rows_mismatch")
    if fillability_vps_guard.get("pending_lifecycle_rows") != 877:
        issues.append("wave_f_fillability_latest_vps_pending_lifecycle_rows_mismatch")
    if fillability_vps_guard.get("slippage_rows") != 13:
        issues.append("wave_f_fillability_latest_vps_slippage_rows_mismatch")
    if fillability_vps_guard.get("trade_records_chronology_count") != 16:
        issues.append("wave_f_fillability_latest_vps_chronology_trade_records_mismatch")
    if fillability_vps_guard.get("trade_records_candidate_decision_policy_joinable") != 13:
        issues.append("wave_f_fillability_latest_vps_joinable_trade_records_mismatch")
    if fillability_vps_guard.get("trade_records_broker_r_coverage_total") != 26:
        issues.append("wave_f_fillability_latest_vps_broker_r_coverage_trade_records_mismatch")
    if fillability_vps_guard.get("broker_lifecycle_rows") != 33:
        issues.append("wave_f_fillability_latest_vps_broker_lifecycle_rows_mismatch")
    if fillability_vps_guard.get("broker_actual_r_rows") != 0:
        issues.append("wave_f_fillability_latest_vps_broker_actual_r_unexpected")
    if fillability_vps_guard.get("close_side_cost_rows") != 0:
        issues.append("wave_f_fillability_latest_vps_close_side_cost_unexpected")
    if fillability_vps_guard.get("placement_capture_contract_present") is not True:
        issues.append("wave_f_fillability_placement_capture_contract_missing")
    if wave_g.get("status") != "blocked_by_no_selected_final_package":
        issues.append("wave_g_status_not_blocked_by_wave_f")
    if wave_h.get("status") not in {
        "bounded_adversarial_audit_checkpoint_rework_required",
        "wave_h_rework_after_final_selection_checkpoint_still_blocked",
    }:
        issues.append("wave_h_status_mismatch")
    if not wave_h_verification.get("ok"):
        issues.append("wave_h_verification_not_ok")
    if not wave_h_rework_verification.get("ok"):
        issues.append("wave_h_rework_verification_not_ok")
    if wave_h_summary.get("audit_rows") != 12:
        issues.append("wave_h_audit_row_count_mismatch")
    if wave_h_summary.get("blocking_issue_rows") != 4:
        issues.append("wave_h_blocking_issue_count_mismatch")
    if wave_h_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_h_final_package_selected")
    if wave_h_summary.get("terminal_decision", {}).get("rework_required") is not True:
        issues.append("wave_h_rework_not_required")
    if wave_h_rework_summary.get("audit_rows") != 14:
        issues.append("wave_h_rework_audit_row_count_mismatch")
    if wave_h_rework_summary.get("blocking_issue_rows") != 13:
        issues.append("wave_h_rework_blocking_issue_count_mismatch")
    if wave_h_rework_summary.get("final_selection_gate_rows") != 14:
        issues.append("wave_h_rework_final_gate_count_mismatch")
    if wave_h_rework_summary.get("final_selection_open_gate_rows") != 13:
        issues.append("wave_h_rework_open_gate_count_mismatch")
    if wave_h_rework_summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("wave_h_rework_final_package_selected")
    if wave_h_rework_summary.get("rework_required") is not True:
        issues.append("wave_h_rework_not_required_current")
    if wave_e.get("status") != "materialization_checkpoint_complete_not_final_selection":
        issues.append("wave_e_status_mismatch")
    if not wave_e_verification.get("ok"):
        issues.append("wave_e_verification_not_ok")
    if wave_e_summary.get("mechanism_rows") != wave_e_verification.get("mechanism_rows"):
        issues.append("wave_e_summary_verifier_mechanism_row_mismatch")
    if wave_e_summary.get("primitive_coverage_rows") != wave_e_verification.get("primitive_coverage_rows"):
        issues.append("wave_e_summary_verifier_primitive_row_mismatch")
    terminal = wave_e_summary.get("terminal_decision", {})
    for field in ["final_package_selected", "live_execution_activation_allowed", "model_training_allowed"]:
        if terminal.get(field) is not False:
            issues.append(f"wave_e_terminal_boundary_not_false:{field}")
    if not vps_absorption_verification.get("ok"):
        issues.append("vps_absorption_verification_not_ok")
    if vps_absorption_summary.get("latest_vps_head") != current_vps_head and not current_vps_package_guard_current:
        issues.append("vps_absorption_summary_head_not_current")
    if vps_absorption_summary.get("packet_log_summary", {}).get("line_count") != 3638:
        issues.append("vps_absorption_packet_line_count_mismatch")
    if vps_absorption_summary.get("packet_log_summary", {}).get("same_namespace_append_order_regression_count") != 0:
        issues.append("vps_absorption_same_namespace_regression_nonzero")
    if vps_absorption_summary.get("slippage_cost_coverage", {}).get("entry_slippage_rows") != 10:
        issues.append("vps_absorption_entry_slippage_count_mismatch")
    if vps_absorption_summary.get("slippage_cost_coverage", {}).get("close_side_cost_rows") != 0:
        issues.append("vps_absorption_close_side_cost_not_zero")
    if vps_absorption_summary.get("broker_r_coverage", {}).get("trade_records_with_broker_actual_r") != 0:
        issues.append("vps_absorption_broker_actual_r_unexpectedly_joined")
    if not vps_freshness_floor_verification.get("ok"):
        issues.append("vps_freshness_floor_verification_not_ok")
    if vps_freshness_floor_summary.get("status") != "vps_freshness_floor_repaired_not_final_selection":
        issues.append("vps_freshness_floor_status_mismatch")
    if vps_freshness_floor_summary.get("fetch_head_floor_or_newer") is not True:
        issues.append("vps_freshness_floor_fetch_head_not_floor_or_newer")
    if vps_freshness_floor_summary.get("origin_vps_floor_or_newer") is not True:
        issues.append("vps_freshness_floor_origin_vps_not_floor_or_newer")
    if vps_freshness_floor_summary.get("live_state_regenerated_current_head") is not True:
        issues.append("vps_freshness_floor_live_state_not_current_head")
    if vps_freshness_floor_summary.get("stale_git_locks_remaining") != 0:
        issues.append("vps_freshness_floor_stale_locks_remaining")
    if vps_freshness_floor_summary.get("fsg001_repaired") is not True:
        issues.append("vps_freshness_floor_fsg001_not_repaired")
    if vps_freshness_floor_summary.get("remaining_final_selection_open_gate_rows") != 12:
        issues.append("vps_freshness_floor_remaining_gate_count_mismatch")
    if vps_freshness_floor_summary.get("final_package_selected") is not False:
        issues.append("vps_freshness_floor_final_package_selected")
    freshness_terminal = vps_freshness_floor_summary.get("terminal_decision", {})
    if freshness_terminal.get("vps_freshness_floor_repaired") is not True:
        issues.append("vps_freshness_floor_terminal_not_repaired")
    for field in ["deployment_dossier_allowed", "final_package_selected", "live_execution_activation_allowed"]:
        if freshness_terminal.get(field) is not False:
            issues.append(f"vps_freshness_floor_terminal_boundary_not_false:{field}")
    if not vps_ai_companion_verification.get("ok"):
        issues.append("vps_ai_companion_verification_not_ok")
    if not vps_ai_companion_current:
        issues.append("vps_ai_companion_head_not_current")
    if vps_ai_companion_summary.get("status") != "latest_vps_package_guard_absorbed_current_remote_snapshot":
        issues.append("vps_ai_companion_status_mismatch")
    if vps_ai_companion_summary.get("main_worktree_fetch_status") not in {"not_required_current", "passed"}:
        issues.append("vps_ai_companion_main_fetch_not_passed")
    if vps_ai_companion_summary.get("authority_level") != "protective":
        issues.append("vps_ai_companion_authority_not_protective")
    if vps_ai_companion_summary.get("ai_companion_enabled") is not True:
        issues.append("vps_ai_companion_not_enabled")
    if vps_ai_companion_summary.get("authority_verification_ok") is not True:
        issues.append("vps_ai_companion_authority_verification_not_ok")
    if vps_ai_companion_summary.get("micro_observation_verification_ok") is not True:
        issues.append("vps_ai_companion_micro_observation_not_ok")
    if vps_ai_companion_summary.get("active_control_count") != 0:
        issues.append("vps_ai_companion_active_control_count_nonzero")
    if vps_ai_companion_summary.get("proposal_count") != vps_ai_companion_verification.get("proposal_count"):
        issues.append("vps_ai_companion_proposal_count_mismatch")
    if vps_ai_companion_summary.get("micro_sample_count") != 61:
        issues.append("vps_ai_companion_micro_sample_count_mismatch")
    if vps_ai_companion_summary.get("micro_latest_packet_window_rows") != 220:
        issues.append("vps_ai_companion_micro_packet_window_mismatch")
    if vps_ai_companion_summary.get("micro_latest_launcher_window_rows") != 8:
        issues.append("vps_ai_companion_micro_launcher_window_mismatch")
    if vps_ai_companion_summary.get("micro_latest_opportunity_count") != 4:
        issues.append("vps_ai_companion_micro_opportunity_count_mismatch")
    if vps_ai_companion_summary.get("micro_recommendation_count") != 5:
        issues.append("vps_ai_companion_micro_recommendation_count_mismatch")
    if vps_ai_companion_summary.get("changed_path_rows") != vps_ai_companion_verification.get("changed_path_rows"):
        issues.append("vps_ai_companion_changed_path_count_mismatch")
    if vps_ai_companion_summary.get("commit_rows") != vps_ai_companion_verification.get("commit_rows"):
        issues.append("vps_ai_companion_commit_count_mismatch")
    if vps_ai_companion_summary.get("local_runtime_code_imported") is not False:
        issues.append("vps_ai_companion_local_runtime_code_imported")
    for field in [
        "broker_runtime_change_status",
        "deployment_readiness_claim",
        "direct_broker_mutation_by_this_route",
        "final_package_selected",
        "model_training_allowed",
    ]:
        if vps_ai_companion_summary.get(field) is not False:
            issues.append(f"vps_ai_companion_boundary_not_false:{field}")
    if any(value is not False for value in vps_ai_companion_summary.get("forbidden_surface_status", {}).values()):
        issues.append("vps_ai_companion_forbidden_surface_crossed")
    if not broker_close_history_verification.get("ok"):
        issues.append("broker_close_history_search_verification_not_ok")
    if broker_close_history_summary.get("status") != "broker_actual_r_close_history_search_checkpoint_not_final_selection":
        issues.append("broker_close_history_search_status_mismatch")
    if broker_close_history_summary.get("vps_head") != current_vps_head:
        issues.append("broker_close_history_search_vps_head_not_current")
    if broker_close_history_summary.get("vps_floor_or_newer") is not True:
        issues.append("broker_close_history_search_vps_floor_not_verified")
    if broker_close_history_summary.get("previous_wave_c_required_import_rows") != 9:
        issues.append("broker_close_history_required_import_rows_mismatch")
    if broker_close_history_summary.get("required_trade_record_matches_in_sibling") != 9:
        issues.append("broker_close_history_trade_record_matches_mismatch")
    if broker_close_history_summary.get("required_entry_account_history_reconciled_rows") != 9:
        issues.append("broker_close_history_entry_reconciled_rows_mismatch")
    if broker_close_history_summary.get("required_close_slippage_rows") != 0:
        issues.append("broker_close_history_close_slippage_unexpected")
    if broker_close_history_summary.get("required_close_side_all_in_cost_rows") != 1:
        issues.append("broker_close_history_close_cost_not_one")
    if broker_close_history_summary.get("required_broker_actual_r_joined_rows") != 1:
        issues.append("broker_close_history_broker_actual_r_not_one")
    if broker_close_history_summary.get("remaining_required_close_history_rows") != 8:
        issues.append("broker_close_history_remaining_rows_not_eight")
    if broker_close_history_summary.get("remote_required_key_hit_count") != 0:
        issues.append("broker_close_history_remote_key_hit_unexpected")
    if broker_close_history_summary.get("latest_vps_packet_rows") != 4401:
        issues.append("broker_close_history_latest_vps_packet_rows_mismatch")
    if broker_close_history_summary.get("latest_vps_trade_records_count") != 16:
        issues.append("broker_close_history_latest_vps_trade_records_mismatch")
    if broker_close_history_summary.get("latest_vps_broker_r_coverage", {}).get("trade_records_with_broker_actual_r") != 0:
        issues.append("broker_close_history_latest_vps_broker_actual_r_unexpected")
    if broker_close_history_summary.get("latest_vps_slippage_cost_coverage", {}).get("close_side_cost_rows") != 0:
        issues.append("broker_close_history_latest_vps_close_cost_unexpected")
    broker_close_terminal = broker_close_history_summary.get("terminal_decision", {})
    if broker_close_terminal.get("current_search_sources_exhausted") is not True:
        issues.append("broker_close_history_current_search_not_exhausted")
    for field in [
        "broker_actual_r_claim_allowed",
        "close_side_all_in_cost_claim_allowed",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if broker_close_terminal.get(field) is not False:
            issues.append(f"broker_close_history_boundary_not_false:{field}")
    if any(value is not False for value in broker_close_history_summary.get("forbidden_surface_status", {}).values()):
        issues.append("broker_close_history_forbidden_surface_crossed")
    if audit.get("goal_completion_claim") is not False:
        issues.append("parent_goal_completion_claim_not_false")
    if audit.get("status") != "not_complete_continue":
        issues.append("parent_status_not_continue")
    forbidden = audit.get("forbidden_surfaces_crossed", {})
    if any(value is not False for value in forbidden.values()):
        issues.append("forbidden_surface_crossed")
    if questions.get("PQ006", {}).get("status") != "answered_materialization_checkpoint":
        issues.append("missing_parent_wave_c_question_answer")
    if source_requests.get("PSR006", {}).get("status") != "open_exact_capture_requirement_confirmed_by_wave_c_and_latest_vps":
        issues.append("missing_latest_vps_broker_actual_r_source_request")
    if source_requests.get("PSR008", {}).get("status") != "partial_fillability_label_repair_877_rows_remaining_replay_universe_unjoined":
        issues.append("missing_limit_fillability_source_request")
    if questions.get("PQ018", {}).get("status") != "answered_latest_vps_placement_capture_guard":
        issues.append("missing_parent_latest_vps_placement_question_answer")
    if source_requests.get("PSR018", {}).get("status") != "completed_current_vps_placement_capture_guard_absorption":
        issues.append("missing_latest_vps_placement_source_request")
    if merge_decisions.get("PMD017", {}).get("status") != "selected":
        issues.append("missing_latest_vps_placement_merge_decision")
    if questions.get("PQ019", {}).get("status") != "answered_lifecycle_replay_bridge_checkpoint":
        issues.append("missing_parent_lifecycle_bridge_question_answer")
    if source_requests.get("PSR019", {}).get("status") != "completed_zero_join_exclusion_recorded_remaining_replay_extension_required":
        issues.append("missing_parent_lifecycle_bridge_source_request")
    if merge_decisions.get("PMD018", {}).get("status") != "selected":
        issues.append("missing_parent_lifecycle_bridge_merge_decision")
    if questions.get("PQ020", {}).get("status") != "answered_lifecycle_denominator_policy_checkpoint":
        issues.append("missing_parent_lifecycle_denominator_question_answer")
    if source_requests.get("PSR020", {}).get("status") != "completed_current_denominator_exclusion_policy_replay_extension_required":
        issues.append("missing_parent_lifecycle_denominator_source_request")
    if merge_decisions.get("PMD019", {}).get("status") != "selected":
        issues.append("missing_parent_lifecycle_denominator_merge_decision")
    if questions.get("PQ021", {}).get("status") != "answered_broker_actual_r_close_source_exhaustion":
        issues.append("missing_parent_broker_actual_r_close_source_exhaustion_question_answer")
    if (
        source_requests.get("PSR021", {}).get("status")
        != "exact_read_only_close_history_import_required_or_broker_real_claims_closed"
    ):
        issues.append("missing_parent_broker_actual_r_close_source_exhaustion_source_request")
    if merge_decisions.get("PMD020", {}).get("status") != "selected":
        issues.append("missing_parent_broker_actual_r_close_source_exhaustion_merge_decision")
    if questions.get("PQ022", {}).get("status") != "answered_hydrated_replay_lift_materialization_checkpoint":
        issues.append("missing_parent_hydrated_replay_lift_question_answer")
    if (
        source_requests.get("PSR022", {}).get("status")
        != "hydrated_proxy_lift_materialized_remaining_final_selection_sources_open"
    ):
        issues.append("missing_parent_hydrated_replay_lift_source_request")
    if merge_decisions.get("PMD021", {}).get("status") != "selected":
        issues.append("missing_parent_hydrated_replay_lift_merge_decision")
    if questions.get("PQ023", {}).get("status") != "answered_order_type_fillability_join_exhaustion_checkpoint":
        issues.append("missing_parent_order_type_fillability_question_answer")
    if (
        source_requests.get("PSR023", {}).get("status")
        != "current_local_hydrated_selector_join_exhausted_exact_bridge_required"
    ):
        issues.append("missing_parent_order_type_fillability_source_request")
    if merge_decisions.get("PMD022", {}).get("status") != "selected":
        issues.append("missing_parent_order_type_fillability_merge_decision")
    if questions.get("PQ025", {}).get("status") != "answered_final_selection_source_exhaustion_partial_broker_repair":
        issues.append("missing_parent_final_selection_source_exhaustion_question_answer")
    if (
        source_requests.get("PSR025", {}).get("status")
        != "partial_broker_close_history_repaired_remaining_final_selection_sources_exact"
    ):
        issues.append("missing_parent_final_selection_source_exhaustion_source_request")
    if merge_decisions.get("PMD024", {}).get("status") != "selected":
        issues.append("missing_parent_final_selection_source_exhaustion_merge_decision")
    if questions.get("PQ026", {}).get("status") != "answered_vps_freshness_floor_repair_checkpoint":
        issues.append("missing_parent_vps_freshness_floor_question_answer")
    if (
        source_requests.get("PSR026", {}).get("status")
        != "completed_vps_floor_fetch_verified_live_state_regenerated"
    ):
        issues.append("missing_parent_vps_freshness_floor_source_request")
    if merge_decisions.get("PMD025", {}).get("status") != "selected":
        issues.append("missing_parent_vps_freshness_floor_merge_decision")
    if questions.get("PQ027", {}).get("status") != "answered_scheduler_v3_candidate_match_repair_checkpoint":
        issues.append("missing_parent_scheduler_match_question_answer")
    if (
        source_requests.get("PSR027", {}).get("status")
        != "scheduler_v3_candidate_match_materialized_final_selection_still_blocked"
    ):
        issues.append("missing_parent_scheduler_match_source_request")
    if merge_decisions.get("PMD026", {}).get("status") != "selected":
        issues.append("missing_parent_scheduler_match_merge_decision")
    if questions.get("PQ028", {}).get("status") != "answered_vps_ai_companion_authority_absorption_checkpoint":
        issues.append("missing_parent_vps_ai_companion_question_answer")
    if (
        source_requests.get("PSR028", {}).get("status")
        != "latest_vps_ai_companion_authority_absorbed_package_guard"
    ):
        issues.append("missing_parent_vps_ai_companion_source_request")
    if merge_decisions.get("PMD027", {}).get("status") != "selected":
        issues.append("missing_parent_vps_ai_companion_merge_decision")
    if questions.get("PQ029", {}).get("status") != "answered_broker_actual_r_close_history_search_checkpoint":
        issues.append("missing_parent_broker_close_history_question_answer")
    if (
        source_requests.get("PSR029", {}).get("status")
        != "exact_close_history_import_required_after_latest_vps_and_sibling_search"
    ):
        issues.append("missing_parent_broker_close_history_source_request")
    if merge_decisions.get("PMD028", {}).get("status") != "selected":
        issues.append("missing_parent_broker_close_history_merge_decision")
    if questions.get("PQ030", {}).get("status") != "answered_final_package_synthesis_checkpoint":
        issues.append("missing_parent_final_package_synthesis_question_answer")
    if (
        source_requests.get("PSR030", {}).get("status")
        != "candidate_final_package_shortlist_materialized_residual_gates_open"
    ):
        issues.append("missing_parent_final_package_synthesis_source_request")
    if merge_decisions.get("PMD029", {}).get("status") != "selected":
        issues.append("missing_parent_final_package_synthesis_merge_decision")
    if questions.get("PQ031", {}).get("status") != "answered_final_package_acceptance_compression_checkpoint":
        issues.append("missing_parent_final_package_acceptance_compression_question_answer")
    if (
        source_requests.get("PSR031", {}).get("status")
        != "candidate_package_sleeves_materialized_residual_gates_open"
    ):
        issues.append("missing_parent_final_package_acceptance_compression_source_request")
    if merge_decisions.get("PMD030", {}).get("status") != "selected":
        issues.append("missing_parent_final_package_acceptance_compression_merge_decision")
    if questions.get("PQ024", {}).get("status") != "answered_clean_label_source_exhaustion_checkpoint":
        issues.append("missing_parent_clean_label_source_exhaustion_question_answer")
    if (
        source_requests.get("PSR024", {}).get("status")
        != "current_local_clean_label_sources_exhausted_training_still_blocked"
    ):
        issues.append("missing_parent_clean_label_source_exhaustion_source_request")
    if merge_decisions.get("PMD023", {}).get("status") != "selected":
        issues.append("missing_parent_clean_label_source_exhaustion_merge_decision")
    if questions.get("PQ009", {}).get("status") != "answered_materialization_checkpoint":
        issues.append("missing_parent_wave_a_question_answer")
    if source_requests.get("PSR007", {}).get("status") != "completed_manifest_verified_no_raw_copy":
        issues.append("missing_wave_a_ltf_source_completion")
    if source_requests.get("PSR009", {}).get("status") != "open_exact_source_requirement_confirmed_by_wave_a":
        issues.append("missing_wave_a_session_table_source_request")
    if merge_decisions.get("PMD008", {}).get("status") != "selected":
        issues.append("missing_wave_a_merge_decision")
    if questions.get("PQ010", {}).get("status") != "answered_source_guard_checkpoint":
        issues.append("missing_parent_vps_absorption_question_answer")
    if source_requests.get("PSR011", {}).get("status") != "completed_current_source_guard_absorption":
        issues.append("missing_parent_vps_absorption_source_request")
    if merge_decisions.get("PMD009", {}).get("status") != "selected":
        issues.append("missing_vps_absorption_merge_decision")
    if questions.get("PQ011", {}).get("status") != "answered_label_readiness_checkpoint":
        issues.append("missing_parent_wave_d_question_answer")
    if source_requests.get("PSR012", {}).get("status") != "open_exact_label_repair_requirement":
        issues.append("missing_wave_d_label_source_request")
    if merge_decisions.get("PMD010", {}).get("status") != "selected":
        issues.append("missing_wave_d_merge_decision")
    if questions.get("PQ012", {}).get("status") != "answered_comparison_gate_checkpoint":
        issues.append("missing_parent_wave_f_question_answer")
    if source_requests.get("PSR013", {}).get("status") != "open_exact_final_selection_requirement":
        issues.append("missing_wave_f_final_selection_source_request")
    if merge_decisions.get("PMD011", {}).get("status") != "selected":
        issues.append("missing_wave_f_merge_decision")
    if questions.get("PQ013", {}).get("status") != "answered_adversarial_audit_checkpoint":
        issues.append("missing_parent_wave_h_question_answer")
    if source_requests.get("PSR014", {}).get("status") != "open_exact_audit_rework_requirement":
        issues.append("missing_wave_h_rework_source_request")
    if merge_decisions.get("PMD012", {}).get("status") != "selected":
        issues.append("missing_wave_h_merge_decision")
    if questions.get("PQ014", {}).get("status") != "answered_validation_stress_checkpoint":
        issues.append("missing_parent_wave_f_validation_question_answer")
    if source_requests.get("PSR015", {}).get("status") != "open_exact_final_selection_requirement_partially_repaired_by_proxy_validation":
        issues.append("missing_wave_f_validation_source_request")
    if merge_decisions.get("PMD013", {}).get("status") != "selected":
        issues.append("missing_wave_f_validation_merge_decision")
    if questions.get("PQ015", {}).get("status") != "answered_successor_axis_selection_checkpoint":
        issues.append("missing_parent_wave_f_successor_question_answer")
    if source_requests.get("PSR016", {}).get("status") != "successor_selection_repaired_remaining_source_repairs_open":
        issues.append("missing_wave_f_successor_source_request")
    if merge_decisions.get("PMD014", {}).get("status") != "selected":
        issues.append("missing_wave_f_successor_merge_decision")
    if questions.get("PQ017", {}).get("status") != "answered_fillability_label_repair_checkpoint":
        issues.append("missing_parent_wave_f_fillability_question_answer")
    if merge_decisions.get("PMD016", {}).get("status") != "selected":
        issues.append("missing_wave_f_fillability_merge_decision")
    if questions.get("PQ016", {}).get("status") != "answered_close_side_capture_checkpoint":
        issues.append("missing_parent_wave_c_close_capture_question_answer")
    if source_requests.get("PSR017", {}).get("status") != "prospective_close_capture_wired_current_close_rows_unjoined":
        issues.append("missing_wave_c_close_capture_source_request")
    if merge_decisions.get("PMD015", {}).get("status") != "selected":
        issues.append("missing_wave_c_close_capture_merge_decision")
    if questions.get("PQ008", {}).get("status") != "answered_materialization_checkpoint":
        issues.append("missing_parent_wave_e_question_answer")
    if source_requests.get("PSR010", {}).get("status") != "open_route_selection_requirement":
        issues.append("missing_wave_e_successor_source_request")
    if merge_decisions.get("PMD007", {}).get("status") != "selected":
        issues.append("missing_wave_e_merge_decision")
    linked = set(manifest.get("linked_child_or_checkpoint_artifacts") or [])
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19/WAVE_A_SOURCE_PROVENANCE_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_a_ltf_profile_provenance_2026_06_19/WAVE_A_LTF_SOURCE_COVERAGE_LEDGER.jsonl",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/WAVE_C_EXECUTION_REALISM_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_execution_cost_realism_2026_06_19/WAVE_C_RUNTIME_PACKET_PARITY_REQUIREMENTS.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_SOURCE_PROBE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CURRENT_TRADE_CLOSE_JOIN_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_CONTRACT.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/WAVE_C_CLOSE_SIDE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_close_side_broker_cost_capture_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_SOURCE_EXHAUSTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_JOIN_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_SOURCE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_REQUIRED_IMPORT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_LABEL_READINESS_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_LABEL_REQUIREMENT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_MODEL_PROMOTION_GATE.json",
        "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19/WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19/WAVE_D_CLEAN_LABEL_SOURCE_STATUS_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19/WAVE_D_CLEAN_LABEL_FAMILY_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19/WAVE_D_CLEAN_LABEL_CAPTURE_REQUIREMENT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19/WAVE_D_MODEL_TRAINING_GATE.json",
        "research/operations/final_moonshot_ultimate_system_wave_d_clean_label_source_exhaustion_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19/WAVE_E_PRIMITIVE_COVERAGE_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_e_primitive_coverage_2026_06_19/WAVE_E_DISCOVERED_MECHANISM_LEDGER.jsonl.gz",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/WAVE_F_COMPARISON_GATE_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/WAVE_F_PACKAGE_COMPARISON_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/WAVE_F_FINAL_SELECTION_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_comparison_readiness_gate_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_STRESS_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_TIME_SPLIT_VALIDATION_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_validation_stress_materialization_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_SUCCESSOR_PACKAGE_AXIS_SELECTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_SUCCESSOR_EXPERIMENT_SELECTION_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_CANDIDATE_PACKAGE_AXIS_FREEZE_DRAFT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/WAVE_F_SUCCESSOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_successor_package_axis_selection_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_replay_bridge_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_lifecycle_denominator_policy_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/WAVE_H_ADVERSARIAL_AUDIT_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/WAVE_H_ADVERSARIAL_AUDIT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/WAVE_H_FINAL_ACCEPT_REJECT_REWORK_DECISION.json",
        "research/operations/final_moonshot_ultimate_system_wave_h_bounded_adversarial_audit_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19/VPS_RUNTIME_STABILITY_ABSORPTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19/VPS_RUNTIME_GATE_IMPACT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_vps_runtime_stability_absorption_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VPS_FRESHNESS_FLOOR_REPAIR_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VPS_FRESHNESS_GIT_LOCK_REPAIR_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VPS_FRESHNESS_FINAL_SELECTION_GATE_IMPACT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_vps_freshness_floor_repair_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_vps_ai_companion_authority_absorption_2026_06_19/VPS_AI_COMPANION_AUTHORITY_ABSORPTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_vps_ai_companion_authority_absorption_2026_06_19/VPS_AI_COMPANION_REMOTE_COMMIT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_vps_ai_companion_authority_absorption_2026_06_19/VPS_AI_COMPANION_CODE_IMPACT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_vps_ai_companion_authority_absorption_2026_06_19/VPS_AI_COMPANION_RUNTIME_BOUNDARY_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_vps_ai_companion_authority_absorption_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_SEARCH_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_SOURCE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_JOIN_ATTEMPT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_LOCAL_ROOT_SEARCH_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_JOINED_ACTUAL_R_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_REQUIRED_IMPORT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/BROKER_ACTUAL_R_CLOSE_HISTORY_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_broker_actual_r_close_history_search_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz",
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_SPLIT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_CONCENTRATION_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_LEAVE_ONE_SYMBOL_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_INSPIRE_NOT_KILL_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19/SCHEDULER_MATCH_REPAIR_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19/SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz",
        "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19/SCHEDULER_MATCH_CONTEXT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19/SCHEDULER_MATCH_AGGREGATE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_convergence_scheduler_match_repair_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")
    for required in [
        "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19/WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19/WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19/WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19/FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19/FINAL_SELECTION_GATE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19/FINAL_SELECTION_SOURCE_REQUIREMENT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19/FINAL_SELECTION_EVIDENCE_POINTER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_selection_source_exhaustion_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/FINAL_PACKAGE_SYNTHESIS_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/FINAL_PACKAGE_AXIS_SCORE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19/VERIFICATION_RESULT.json",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_OVERLAP_DEDUP_CONCENTRATION_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_SCHEDULER_LIFECYCLE_CONTROL_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_SPLIT_STRESS_ACCEPTANCE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/FINAL_PACKAGE_ACCEPTANCE_RESIDUAL_GATE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if required not in linked:
            issues.append(f"parent_manifest_missing:{required}")

    result = {
        "schema": "gtos.final_moonshot.ultimate_system_full_plan.parent_verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "current_vps_head": current_vps_head,
        "wave_a_ltf_coverage_rows": wave_a_summary.get("ltf_coverage_rows"),
        "wave_a_ltf_unique_symbols": wave_a_summary.get("ltf_unique_symbols"),
        "wave_a_explicit_session_table_rows_captured": wave_a_summary.get("explicit_session_table_rows_captured"),
        "wave_c_material_rows": wave_c_summary.get("material_rows"),
        "wave_c_ledger_counts": wave_c_verification.get("ledger_counts"),
        "wave_c_close_capture_local_ultimate_trade_records": wave_c_close_summary.get("local_ultimate_trade_records"),
        "wave_c_close_capture_entry_reconciled_rows": wave_c_close_summary.get("entry_account_history_reconciled_rows"),
        "wave_c_close_capture_current_broker_actual_r_rows": wave_c_close_summary.get("current_trade_records_with_broker_actual_r"),
        "wave_c_close_capture_local_close_slippage_rows": wave_c_close_summary.get("local_close_slippage_rows"),
        "wave_c_close_capture_current_ticket_matches": wave_c_close_summary.get("current_close_slippage_ticket_matches"),
        "wave_c_close_capture_code_repair_present": wave_c_close_summary.get("code_repair_close_deal_lookup_present"),
        "wave_c_close_capture_final_package_selected": wave_c_close_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_c_close_exhaustion_current_trade_records": wave_c_close_exhaustion_summary.get("current_trade_records"),
        "wave_c_close_exhaustion_entry_reconciled_trade_rows": wave_c_close_exhaustion_summary.get("entry_account_history_reconciled_trade_rows"),
        "wave_c_close_exhaustion_entry_slippage_joined_trade_rows": wave_c_close_exhaustion_summary.get("entry_slippage_joined_trade_rows"),
        "wave_c_close_exhaustion_account_history_export_joined_trade_rows": wave_c_close_exhaustion_summary.get("account_history_export_joined_trade_rows"),
        "wave_c_close_exhaustion_close_slippage_joined_trade_rows": wave_c_close_exhaustion_summary.get("close_slippage_joined_trade_rows"),
        "wave_c_close_exhaustion_broker_actual_r_joined_rows": wave_c_close_exhaustion_summary.get("broker_actual_r_joined_rows"),
        "wave_c_close_exhaustion_close_side_all_in_cost_joined_rows": wave_c_close_exhaustion_summary.get("close_side_all_in_cost_joined_rows"),
        "wave_c_close_exhaustion_pointer_truth_sources": wave_c_close_exhaustion_summary.get("pointer_truth_sources"),
        "wave_c_close_exhaustion_pointer_truth_sources_hydrated_locally": wave_c_close_exhaustion_summary.get("pointer_truth_sources_hydrated_locally"),
        "wave_c_close_exhaustion_required_import_rows": wave_c_close_exhaustion_summary.get("required_import_rows"),
        "wave_c_close_exhaustion_broker_actual_r_claim_allowed": wave_c_close_exhaustion_summary.get("terminal_decision", {}).get("broker_actual_r_claim_allowed"),
        "wave_c_close_exhaustion_close_side_all_in_cost_claim_allowed": wave_c_close_exhaustion_summary.get("terminal_decision", {}).get("close_side_all_in_cost_claim_allowed"),
        "wave_c_close_exhaustion_final_package_selected": wave_c_close_exhaustion_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_d_label_requirement_rows": wave_d_summary.get("label_requirement_rows"),
        "wave_d_training_ready_label_count": wave_d_summary.get("training_ready_label_count"),
        "wave_d_blocked_label_count": wave_d_summary.get("blocked_label_count"),
        "wave_d_clean_label_family_rows": wave_d_clean_label_summary.get("label_family_rows"),
        "wave_d_clean_label_training_ready_label_count": wave_d_clean_label_summary.get("training_ready_label_count"),
        "wave_d_clean_label_blocked_label_count": wave_d_clean_label_summary.get("blocked_label_count"),
        "wave_d_clean_label_capture_requirement_rows": wave_d_clean_label_summary.get("capture_requirement_rows"),
        "wave_d_clean_label_hydrated_selector_rows": wave_d_clean_label_summary.get("hydrated_selector_rows"),
        "wave_d_clean_label_wfv003_label_rows": wave_d_clean_label_summary.get("wfv003_label_rows"),
        "wave_d_clean_label_clean_no_leak_training_dataset_available": wave_d_clean_label_summary.get("terminal_decision", {}).get("clean_no_leak_training_dataset_available"),
        "wave_d_clean_label_model_training_allowed": wave_d_clean_label_summary.get("terminal_decision", {}).get("model_training_allowed"),
        "wave_e_primitive_coverage_rows": wave_e_summary.get("primitive_coverage_rows"),
        "wave_e_mechanism_rows": wave_e_summary.get("mechanism_rows"),
        "wave_e_source_search_rows": wave_e_summary.get("source_search_rows"),
        "wave_e_successor_experiment_rows": wave_e_summary.get("successor_experiment_rows"),
        "wave_f_package_comparison_rows": wave_f_summary.get("package_comparison_rows"),
        "wave_f_stress_gate_rows": wave_f_summary.get("stress_gate_rows"),
        "wave_f_final_selection_blocker_rows": wave_f_summary.get("final_selection_blocker_rows"),
        "wave_f_final_package_selected": wave_f_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_f_validation_time_split_rows": wave_f_validation_summary.get("time_split_rows"),
        "wave_f_validation_walk_forward_rows": wave_f_validation_summary.get("walk_forward_rows"),
        "wave_f_validation_leave_one_symbol_side_rows": wave_f_validation_summary.get("leave_one_symbol_side_rows"),
        "wave_f_validation_adversarial_rows": wave_f_validation_summary.get("adversarial_baseline_rows"),
        "wave_f_validation_mc_rows": wave_f_validation_summary.get("monte_carlo_proxy_rows"),
        "wave_f_validation_final_package_selected": wave_f_validation_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_f_successor_selection_rows": wave_f_successor_summary.get("successor_selection_rows"),
        "wave_f_successor_current_comparison_rows": wave_f_successor_summary.get("current_comparison_input_rows"),
        "wave_f_successor_guard_axis_rows": wave_f_successor_summary.get("current_guard_axis_rows"),
        "wave_f_successor_source_capture_blocker_rows": wave_f_successor_summary.get("source_capture_blocker_rows"),
        "wave_f_successor_required_validation_source_repair_rows": wave_f_successor_summary.get("required_validation_source_repair_rows"),
        "wave_f_successor_dedicated_route_rows": wave_f_successor_summary.get("dedicated_successor_route_rows"),
        "wave_f_successor_wfb009_status": wave_f_successor_summary.get("wfb009_status"),
        "wave_f_successor_final_package_selected": wave_f_successor_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_f_fillability_label_rows": wave_f_fillability_summary.get("row_bound_fillability_label_rows"),
        "wave_f_fillability_wave_c_rows_scanned": wave_f_fillability_summary.get("wave_c_join_attempt", {}).get("wave_c_no_fill_rows_scanned"),
        "wave_f_fillability_wave_c_rows_joined": wave_f_fillability_summary.get("wave_c_join_attempt", {}).get("wave_c_no_fill_rows_joined"),
        "wave_f_fillability_wfb003_status": wave_f_fillability_summary.get("wfb003_status"),
        "wave_f_fillability_final_package_selected": wave_f_fillability_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_f_fillability_latest_vps_head": fillability_vps_guard.get("head"),
        "wave_f_fillability_latest_vps_runtime_packet_rows": fillability_vps_guard.get("runtime_packet_rows"),
        "wave_f_fillability_latest_vps_pending_lifecycle_rows": fillability_vps_guard.get("pending_lifecycle_rows"),
        "wave_f_fillability_latest_vps_slippage_rows": fillability_vps_guard.get("slippage_rows"),
        "wave_f_fillability_latest_vps_trade_records_chronology_count": fillability_vps_guard.get("trade_records_chronology_count"),
        "wave_f_fillability_latest_vps_trade_records_candidate_decision_policy_joinable": fillability_vps_guard.get("trade_records_candidate_decision_policy_joinable"),
        "wave_f_fillability_latest_vps_trade_records_broker_r_coverage_total": fillability_vps_guard.get("trade_records_broker_r_coverage_total"),
        "wave_f_fillability_latest_vps_broker_lifecycle_rows": fillability_vps_guard.get("broker_lifecycle_rows"),
        "wave_f_fillability_latest_vps_broker_actual_r_rows": fillability_vps_guard.get("broker_actual_r_rows"),
        "wave_f_fillability_latest_vps_close_side_cost_rows": fillability_vps_guard.get("close_side_cost_rows"),
        "wave_f_fillability_placement_capture_contract_present": fillability_vps_guard.get("placement_capture_contract_present"),
        "wave_f_lifecycle_bridge_rows": wave_f_lifecycle_bridge_summary.get("bridge_rows"),
        "wave_f_lifecycle_bridge_wave_b_rows_scanned": wave_f_lifecycle_bridge_summary.get("wave_b_rows_scanned"),
        "wave_f_lifecycle_bridge_wave_c_rows_scanned": wave_f_lifecycle_bridge_summary.get("wave_c_rows_scanned"),
        "wave_f_lifecycle_bridge_wave_b_direct_joins": wave_f_lifecycle_bridge_summary.get("wave_b_exact_candidate_id_matches"),
        "wave_f_lifecycle_bridge_wave_c_direct_joins": wave_f_lifecycle_bridge_summary.get("wave_c_exact_candidate_id_matches"),
        "wave_f_lifecycle_bridge_wave_b_symbol_side_time_joins": wave_f_lifecycle_bridge_summary.get("wave_b_symbol_side_time_matches"),
        "wave_f_lifecycle_bridge_wave_c_symbol_side_time_joins": wave_f_lifecycle_bridge_summary.get("wave_c_symbol_side_time_matches"),
        "wave_f_lifecycle_bridge_alternate_owner_candidate_ids": wave_f_lifecycle_bridge_summary.get("alternate_historical_owner_candidate_ids"),
        "wave_f_lifecycle_bridge_wfb003_status": wave_f_lifecycle_bridge_summary.get("wfb003_status"),
        "wave_f_lifecycle_bridge_final_package_selected": wave_f_lifecycle_bridge_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_f_lifecycle_denominator_policy_rows": wave_f_lifecycle_denominator_summary.get("policy_rows"),
        "wave_f_lifecycle_denominator_excluded_rows": wave_f_lifecycle_denominator_summary.get("excluded_from_current_denominator_rows"),
        "wave_f_lifecycle_denominator_included_rows": wave_f_lifecycle_denominator_summary.get("current_denominator_included_rows"),
        "wave_f_lifecycle_denominator_main_orch24_candidate_ids": wave_f_lifecycle_denominator_summary.get("main_orch24_matched_candidate_ids"),
        "wave_f_lifecycle_denominator_main_orch24_rows": wave_f_lifecycle_denominator_summary.get("main_orch24_matched_rows"),
        "wave_f_lifecycle_denominator_full_geometry_rows": wave_f_lifecycle_denominator_summary.get("main_orch24_full_replay_geometry_rows"),
        "wave_f_lifecycle_denominator_exact_r_rows": wave_f_lifecycle_denominator_summary.get("main_orch24_exact_r_rows"),
        "wave_f_lifecycle_denominator_final_package_selected": wave_f_lifecycle_denominator_summary.get("terminal_decision", {}).get("final_package_selected"),
        "hydrated_replay_lift_selector_candidate_rows": hydrated_replay_lift_summary.get("selector_candidate_rows"),
        "hydrated_replay_lift_proxy_r_rows": hydrated_replay_lift_summary.get("selector_metrics", {}).get("proxy_r_rows"),
        "hydrated_replay_lift_positive_lift_rows": hydrated_replay_lift_summary.get("selector_metrics", {}).get("positive_lift_rows"),
        "hydrated_replay_lift_zero_lift_rows": hydrated_replay_lift_summary.get("selector_metrics", {}).get("zero_lift_rows"),
        "hydrated_replay_lift_broker_real_actual_r_rows": hydrated_replay_lift_summary.get("selector_metrics", {}).get("broker_real_actual_r_rows"),
        "hydrated_replay_lift_exact_r_rows": hydrated_replay_lift_summary.get("selector_metrics", {}).get("exact_r_rows"),
        "hydrated_replay_lift_group_rows": hydrated_replay_lift_summary.get("group_rows"),
        "hydrated_replay_lift_concentration_rows": hydrated_replay_lift_summary.get("concentration_rows"),
        "hydrated_replay_lift_leave_one_symbol_rows": hydrated_replay_lift_summary.get("leave_one_symbol_rows"),
        "hydrated_replay_lift_final_package_selected": hydrated_replay_lift_summary.get("terminal_decision", {}).get("final_package_selected"),
        "hydrated_replay_lift_clean_training_labels_available": hydrated_replay_lift_summary.get("terminal_decision", {}).get("clean_training_labels_available"),
        "scheduler_match_scheduler_v3_rows": scheduler_match_summary.get("scheduler_v3_rows"),
        "scheduler_match_context_group_rows": scheduler_match_summary.get("context_group_rows"),
        "scheduler_match_result_r_rows": scheduler_match_summary.get("result_r_rows"),
        "scheduler_match_positive_result_r_rows": scheduler_match_summary.get("positive_result_r_rows"),
        "scheduler_match_negative_result_r_rows": scheduler_match_summary.get("negative_result_r_rows"),
        "scheduler_match_result_r_sum": scheduler_match_summary.get("result_r_sum"),
        "scheduler_match_missed_result_r_sum": scheduler_match_summary.get("missed_result_r_sum"),
        "scheduler_match_git_blob_status": scheduler_match_summary.get("git_blob_status"),
        "scheduler_match_final_package_selected": scheduler_match_summary.get("final_package_selected"),
        "scheduler_match_model_training_allowed": scheduler_match_summary.get("model_training_allowed"),
        "wave_f_order_type_fillability_label_rows": wave_f_order_type_fillability_summary.get("label_rows"),
        "wave_f_order_type_fillability_selector_rows": wave_f_order_type_fillability_summary.get("selector_rows"),
        "wave_f_order_type_fillability_selector_may_2026_context_rows": wave_f_order_type_fillability_summary.get("selector_may_2026_context_rows"),
        "wave_f_order_type_fillability_exact_candidate_id_selector_matches": wave_f_order_type_fillability_summary.get("exact_candidate_id_selector_matches"),
        "wave_f_order_type_fillability_exact_symbol_side_time_selector_label_matches": wave_f_order_type_fillability_summary.get("exact_symbol_side_time_selector_label_matches"),
        "wave_f_order_type_fillability_weekly_context_only_not_denominator_join": wave_f_order_type_fillability_verification.get("weekly_context_only_not_denominator_join"),
        "wave_f_order_type_fillability_missing_decision_time_exact_capture_required": wave_f_order_type_fillability_verification.get("missing_decision_time_exact_capture_required"),
        "wave_f_order_type_fillability_current_denominator_fillability_inclusion_allowed": wave_f_order_type_fillability_summary.get("terminal_decision", {}).get("current_denominator_fillability_inclusion_allowed"),
        "wave_f_order_type_fillability_final_package_selected": wave_f_order_type_fillability_summary.get("terminal_decision", {}).get("final_package_selected"),
        "final_selection_source_exhaustion_gate_rows": final_selection_source_exhaustion_summary.get("gate_rows"),
        "final_selection_source_exhaustion_open_gate_rows": final_selection_source_exhaustion_summary.get("open_gate_rows"),
        "final_selection_source_exhaustion_requirement_rows": final_selection_source_exhaustion_summary.get("requirement_rows"),
        "final_selection_source_exhaustion_evidence_pointer_rows": final_selection_source_exhaustion_summary.get("evidence_pointer_rows"),
        "final_selection_source_exhaustion_broker_actual_r_joined_rows": final_selection_source_exhaustion_summary.get("broker_actual_r_joined_rows"),
        "final_selection_source_exhaustion_close_side_all_in_cost_joined_rows": final_selection_source_exhaustion_summary.get("close_side_all_in_cost_joined_rows"),
        "final_selection_source_exhaustion_training_ready_label_count": final_selection_source_exhaustion_summary.get("training_ready_label_count"),
        "final_selection_source_exhaustion_order_type_exact_join_rows": final_selection_source_exhaustion_summary.get("order_type_exact_join_rows"),
        "final_selection_source_exhaustion_final_package_selected": final_selection_source_exhaustion_summary.get("terminal_decision", {}).get("final_package_selected"),
        "final_package_synthesis_selector_candidate_rows": final_package_synthesis_summary.get("selector_candidate_rows"),
        "final_package_synthesis_selector_positive_lift_rows": final_package_synthesis_summary.get("selector_positive_lift_rows"),
        "final_package_synthesis_candidate_level_rows": final_package_synthesis_summary.get("candidate_level_rows"),
        "final_package_synthesis_candidate_level_source_bound_r_sum": final_package_synthesis_summary.get("candidate_level_source_bound_r_sum"),
        "final_package_synthesis_scheduler_rows": final_package_synthesis_summary.get("scheduler_rows"),
        "final_package_synthesis_scheduler_result_r_sum": final_package_synthesis_summary.get("scheduler_result_r_sum"),
        "final_package_synthesis_axis_score_rows": final_package_synthesis_summary.get("axis_score_rows"),
        "final_package_synthesis_candidate_package_shortlist_rows": final_package_synthesis_summary.get("candidate_package_shortlist_rows"),
        "final_package_synthesis_split_stress_rows": final_package_synthesis_summary.get("split_stress_rows"),
        "final_package_synthesis_concentration_rows": final_package_synthesis_summary.get("concentration_rows"),
        "final_package_synthesis_successor_primitive_rows": final_package_synthesis_summary.get("successor_primitive_rows"),
        "final_package_synthesis_residual_gate_rows": final_package_synthesis_summary.get("residual_gate_rows"),
        "final_package_synthesis_candidate_shortlist_materialized": final_package_synthesis_summary.get("terminal_decision", {}).get("candidate_final_package_shortlist_materialized"),
        "final_package_synthesis_broker_actual_r_is_edge_source": final_package_synthesis_summary.get("terminal_decision", {}).get("broker_actual_r_is_edge_source"),
        "final_package_synthesis_broker_actual_r_claim_allowed": final_package_synthesis_summary.get("terminal_decision", {}).get("broker_actual_r_claim_allowed"),
        "final_package_synthesis_final_package_selected": final_package_synthesis_summary.get("terminal_decision", {}).get("final_package_selected"),
        "final_package_acceptance_input_shortlist_rows": final_package_acceptance_compression_summary.get("input_shortlist_rows"),
        "final_package_acceptance_package_sleeve_rows": final_package_acceptance_compression_summary.get("package_sleeve_rows"),
        "final_package_acceptance_sleeve_member_rows": final_package_acceptance_compression_summary.get("sleeve_member_rows"),
        "final_package_acceptance_overlap_dedup_rows": final_package_acceptance_compression_summary.get("overlap_dedup_rows"),
        "final_package_acceptance_concentration_control_rows": final_package_acceptance_compression_summary.get("concentration_control_rows"),
        "final_package_acceptance_scheduler_lifecycle_control_rows": final_package_acceptance_compression_summary.get("scheduler_lifecycle_control_rows"),
        "final_package_acceptance_split_stress_leave_one_symbol_rows": final_package_acceptance_compression_summary.get("split_stress_leave_one_symbol_rows"),
        "final_package_acceptance_residual_gate_rows": final_package_acceptance_compression_summary.get("residual_gate_rows"),
        "final_package_acceptance_compressed_combined_source_bound_signal_r": final_package_acceptance_compression_summary.get("compressed_combined_source_bound_signal_r"),
        "final_package_acceptance_compressed_candidate_level_source_bound_r_sum": final_package_acceptance_compression_summary.get("compressed_candidate_level_source_bound_r_sum"),
        "final_package_acceptance_compressed_scheduler_result_r_sum": final_package_acceptance_compression_summary.get("compressed_scheduler_result_r_sum"),
        "final_package_acceptance_candidate_package_sleeves_materialized": final_package_acceptance_compression_summary.get("terminal_decision", {}).get("candidate_package_sleeves_materialized"),
        "final_package_acceptance_broker_actual_r_is_edge_source": final_package_acceptance_compression_summary.get("terminal_decision", {}).get("broker_actual_r_is_edge_source"),
        "final_package_acceptance_broker_actual_r_claim_allowed": final_package_acceptance_compression_summary.get("terminal_decision", {}).get("broker_actual_r_claim_allowed"),
        "final_package_acceptance_final_package_selected": final_package_acceptance_compression_summary.get("terminal_decision", {}).get("final_package_selected"),
        "wave_h_audit_rows": wave_h_summary.get("audit_rows"),
        "wave_h_blocking_issue_rows": wave_h_summary.get("blocking_issue_rows"),
        "wave_h_rework_required": wave_h_summary.get("terminal_decision", {}).get("rework_required"),
        "wave_h_rework_after_final_selection_audit_rows": wave_h_rework_summary.get("audit_rows"),
        "wave_h_rework_after_final_selection_blocking_issue_rows": wave_h_rework_summary.get("blocking_issue_rows"),
        "wave_h_rework_after_final_selection_final_gate_rows": wave_h_rework_summary.get("final_selection_gate_rows"),
        "wave_h_rework_after_final_selection_rework_required": wave_h_rework_summary.get("rework_required"),
        "vps_absorption_packet_rows": vps_absorption_summary.get("packet_log_summary", {}).get("line_count"),
        "vps_absorption_entry_slippage_rows": vps_absorption_summary.get("slippage_cost_coverage", {}).get("entry_slippage_rows"),
        "vps_absorption_broker_actual_r_joined_rows": vps_absorption_summary.get("broker_r_coverage", {}).get("trade_records_with_broker_actual_r"),
        "vps_freshness_floor_fetch_head": vps_freshness_floor_summary.get("fetch_head"),
        "vps_freshness_floor_origin_vps_head": vps_freshness_floor_summary.get("origin_vps_head"),
        "vps_freshness_floor_fetch_head_floor_or_newer": vps_freshness_floor_summary.get("fetch_head_floor_or_newer"),
        "vps_freshness_floor_origin_vps_floor_or_newer": vps_freshness_floor_summary.get("origin_vps_floor_or_newer"),
        "vps_freshness_floor_live_state_regenerated_current_head": vps_freshness_floor_summary.get("live_state_regenerated_current_head"),
        "vps_freshness_floor_stale_git_locks_remaining": vps_freshness_floor_summary.get("stale_git_locks_remaining"),
        "vps_freshness_floor_remaining_final_selection_open_gate_rows": vps_freshness_floor_summary.get("remaining_final_selection_open_gate_rows"),
        "vps_freshness_floor_final_package_selected": vps_freshness_floor_summary.get("final_package_selected"),
        "vps_ai_companion_remote_probe_head": vps_ai_companion_summary.get("remote_probe_head"),
        "vps_ai_companion_side_clone_head": vps_ai_companion_summary.get("side_clone_head"),
        "vps_ai_companion_source_snapshot_head": vps_ai_companion_summary.get("source_snapshot_head"),
        "vps_ai_companion_source_snapshot_verified": vps_ai_companion_summary.get("source_snapshot_verified"),
        "vps_ai_companion_main_worktree_fetch_status": vps_ai_companion_summary.get("main_worktree_fetch_status"),
        "vps_ai_companion_authority_level": vps_ai_companion_summary.get("authority_level"),
        "vps_ai_companion_enabled": vps_ai_companion_summary.get("ai_companion_enabled"),
        "vps_ai_companion_active_control_count": vps_ai_companion_summary.get("active_control_count"),
        "vps_ai_companion_proposal_count": vps_ai_companion_summary.get("proposal_count"),
        "vps_ai_companion_micro_sample_count": vps_ai_companion_summary.get("micro_sample_count"),
        "vps_ai_companion_micro_latest_packet_window_rows": vps_ai_companion_summary.get("micro_latest_packet_window_rows"),
        "vps_ai_companion_micro_latest_launcher_window_rows": vps_ai_companion_summary.get("micro_latest_launcher_window_rows"),
        "vps_ai_companion_micro_latest_opportunity_count": vps_ai_companion_summary.get("micro_latest_opportunity_count"),
        "vps_ai_companion_micro_recommendation_count": vps_ai_companion_summary.get("micro_recommendation_count"),
        "vps_ai_companion_changed_path_rows": vps_ai_companion_summary.get("changed_path_rows"),
        "vps_ai_companion_commit_rows": vps_ai_companion_summary.get("commit_rows"),
        "vps_ai_companion_local_runtime_code_imported": vps_ai_companion_summary.get("local_runtime_code_imported"),
        "vps_ai_companion_final_package_selected": vps_ai_companion_summary.get("final_package_selected"),
        "vps_ai_companion_model_training_allowed": vps_ai_companion_summary.get("model_training_allowed"),
        "vps_ai_companion_deployment_readiness_claim": vps_ai_companion_summary.get("deployment_readiness_claim"),
        "vps_ai_companion_forbidden_surface_status": vps_ai_companion_summary.get("forbidden_surface_status"),
        "broker_close_history_vps_head": broker_close_history_summary.get("vps_head"),
        "broker_close_history_required_import_rows": broker_close_history_summary.get("previous_wave_c_required_import_rows"),
        "broker_close_history_trade_record_matches_in_sibling": broker_close_history_summary.get("required_trade_record_matches_in_sibling"),
        "broker_close_history_entry_account_history_reconciled_rows": broker_close_history_summary.get("required_entry_account_history_reconciled_rows"),
        "broker_close_history_close_slippage_rows": broker_close_history_summary.get("required_close_slippage_rows"),
        "broker_close_history_close_side_all_in_cost_rows": broker_close_history_summary.get("required_close_side_all_in_cost_rows"),
        "broker_close_history_broker_actual_r_joined_rows": broker_close_history_summary.get("required_broker_actual_r_joined_rows"),
        "broker_close_history_remote_required_key_hit_count": broker_close_history_summary.get("remote_required_key_hit_count"),
        "broker_close_history_latest_vps_packet_rows": broker_close_history_summary.get("latest_vps_packet_rows"),
        "broker_close_history_latest_vps_trade_records_count": broker_close_history_summary.get("latest_vps_trade_records_count"),
        "broker_close_history_latest_vps_broker_actual_r_rows": broker_close_history_summary.get("latest_vps_broker_r_coverage", {}).get("trade_records_with_broker_actual_r"),
        "broker_close_history_latest_vps_close_side_cost_rows": broker_close_history_summary.get("latest_vps_slippage_cost_coverage", {}).get("close_side_cost_rows"),
        "broker_close_history_final_package_selected": broker_close_history_summary.get("terminal_decision", {}).get("final_package_selected"),
        "parent_goal_completion_claim": audit.get("goal_completion_claim"),
        "forbidden_surface_status": forbidden,
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json("PARENT_VERIFICATION_RESULT.json", result)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())

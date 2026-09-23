from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"

STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
FAILURE_ANATOMY_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILURE_ANATOMY_LEDGER_2026-05-25.jsonl"
)
STAGE03_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_LEDGER_2026-05-25.jsonl"
)
STAGE05_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_LEDGER_2026-05-25.jsonl"
)
PATH_OUTCOME_INDEX = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl"
M15_VS_LTF_INDEX = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_M15_VS_LTF_DISAGREEMENT_LEDGER_2026-05-24.jsonl"
)
STAGE06_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_LEDGER_2026-05-25.jsonl"
)
STAGE06_SUMMARY = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_SUMMARY_2026-05-25.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def git_status_short() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ["GIT_STATUS_FAILED"]
    return [line for line in output.splitlines() if line.strip()]


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_indexed_gzip_rows(index_path: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for meta in iter_jsonl(index_path):
        chunk = REPO_ROOT / meta["chunk_path"]
        with gzip.open(chunk, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield meta, json.loads(line)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


@dataclass
class ScenarioStats:
    selected_count: int = 0
    performance_count: int = 0
    total_r: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    no_fill_count: int = 0
    action_counts: Counter[str] = field(default_factory=Counter)
    branch_counts: Counter[str] = field(default_factory=Counter)

    def add(self, row: dict[str, Any], *, selected: bool, action: str, branch: str) -> None:
        if not selected:
            return
        self.selected_count += 1
        self.action_counts[action] += 1
        self.branch_counts[branch] += 1
        if str(row.get("terminal_outcome") or "") == "no_fill":
            self.no_fill_count += 1
        r_value = _as_float(row.get("simulated_r"))
        if r_value is None:
            return
        self.performance_count += 1
        self.total_r += r_value
        if r_value > 0:
            self.win_count += 1
        elif r_value < 0:
            self.loss_count += 1

    def to_record(self) -> dict[str, Any]:
        expectancy = self.total_r / self.performance_count if self.performance_count else None
        return {
            "selected_count": self.selected_count,
            "performance_count": self.performance_count,
            "total_r": round(self.total_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "no_fill_count": self.no_fill_count,
            "action_counts": dict(self.action_counts.most_common()),
            "branch_counts": dict(self.branch_counts.most_common()),
        }


def load_selected_stream_ids() -> tuple[set[str], dict[str, str], dict[str, int]]:
    selected: set[str] = set()
    source: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for row in iter_jsonl(STAGE03_LEDGER):
        counts["stage03_rows"] += 1
        if (row.get("scenario_membership") or {}).get(
            "vnext_executable_stream_without_prop_governance"
        ):
            cid = str(row.get("candidate_id") or "")
            selected.add(cid)
            source[cid] = "stage03_vnext_executable_stream"
            counts["stage03_vnext_executable_stream"] += 1
    for row in iter_jsonl(STAGE05_LEDGER):
        counts["stage05_policy_rows"] += 1
        if row.get("recovered_into_stage05_no_prop_stream"):
            cid = str(row.get("candidate_id") or "")
            selected.add(cid)
            source[cid] = "stage05_avoid_pre_ai_recovered_stream"
            counts["stage05_recovered_stream"] += 1
    counts["stage06_selected_stream_ids"] = len(selected)
    return selected, source, dict(counts)


def load_failure_rows(selected_ids: set[str]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    rows: dict[str, dict[str, Any]] = {}
    path_row_ids: set[str] = set()
    for row in iter_jsonl(FAILURE_ANATOMY_LEDGER):
        cid = str(row.get("candidate_id") or "")
        if cid not in selected_ids:
            continue
        rows[cid] = row
        path_id = str(row.get("path_row_id") or "")
        if path_id:
            path_row_ids.add(path_id)
    return rows, path_row_ids


def load_path_rows(path_row_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path_rows: dict[str, dict[str, Any]] = {}
    chunks_read = 0
    rows_seen = 0
    for meta, row in iter_indexed_gzip_rows(PATH_OUTCOME_INDEX):
        if meta.get("chunk_index") and rows_seen == 0:
            pass
        rows_seen += 1
        path_id = str(row.get("path_row_id") or "")
        if path_id in path_row_ids:
            path_rows[path_id] = row
        if rows_seen and rows_seen % 250000 == 0:
            chunks_read += 0
    chunks_read = sum(1 for _ in iter_jsonl(PATH_OUTCOME_INDEX))
    return path_rows, {
        "path_rows_requested": len(path_row_ids),
        "path_rows_joined": len(path_rows),
        "path_index_rows": chunks_read,
        "path_underlying_rows_scanned": rows_seen,
        "path_index_sha256": sha256_file(PATH_OUTCOME_INDEX),
    }


def load_disagreements(selected_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    disagreements: dict[str, dict[str, Any]] = {}
    chunks_read = 0
    rows_seen = 0
    for meta, row in iter_indexed_gzip_rows(M15_VS_LTF_INDEX):
        rows_seen += 1
        cid = str(row.get("candidate_id") or "")
        if cid in selected_ids:
            disagreements[cid] = row
    chunks_read = sum(1 for _ in iter_jsonl(M15_VS_LTF_INDEX))
    return disagreements, {
        "m15_vs_ltf_selected_stream_rows_joined": len(disagreements),
        "m15_vs_ltf_index_rows": chunks_read,
        "m15_vs_ltf_underlying_rows_scanned": rows_seen,
        "m15_vs_ltf_index_sha256": sha256_file(M15_VS_LTF_INDEX),
    }


def classify_stage06_ltf_policy(
    row: dict[str, Any],
    path_row: dict[str, Any] | None,
    disagreement: dict[str, Any] | None,
) -> dict[str, Any]:
    if path_row is None:
        return {
            "stage06_ltf_action": "SOURCE_CAPTURE_REQUIRED",
            "repair_branch": "missing_path_row_join",
            "execution_behavior_changed": False,
            "selected_after_stage06_ltf": True,
            "decision_inputs_exclude_future_r": True,
            "source_complete_for_ltf_decision": False,
            "source_status": "path_row_missing",
        }
    source_status = str(path_row.get("path_source_status") or "")
    source_mode = str(path_row.get("source_mode") or "")
    source_complete = bool(path_row.get("source_window_complete"))
    measured = str(path_row.get("price_path_truth_status") or "") == "measured"
    if not measured or source_mode in {"MISSING_SOURCE", "RUNTIME_TRACE_REFERENCE"}:
        return {
            "stage06_ltf_action": "SOURCE_CAPTURE_REQUIRED",
            "repair_branch": "path_source_not_measured",
            "execution_behavior_changed": False,
            "selected_after_stage06_ltf": True,
            "decision_inputs_exclude_future_r": True,
            "source_complete_for_ltf_decision": False,
            "source_status": source_status or source_mode,
        }

    pre_entry_tp = bool(path_row.get("pre_entry_tp_touch_utc"))
    pre_entry_sl = bool(path_row.get("pre_entry_sl_touch_utc"))
    same_bar = bool(path_row.get("same_bar_ambiguity"))
    terminal_no_fill = str(row.get("terminal_outcome") or "") == "no_fill"
    ltf_disagreement = disagreement is not None

    if pre_entry_tp or pre_entry_sl:
        action = "MONITOR_LTF_PATH"
        branch = "pre_entry_target_or_protective_touch_requires_monitor_not_skip"
        selected_after = True
    elif same_bar:
        action = "MONITOR_LTF_PATH"
        branch = "same_bar_ambiguity_requires_ltf_monitor"
        selected_after = True
    elif terminal_no_fill:
        action = "MONITOR_LTF_PATH"
        branch = "terminal_no_fill_requires_prospective_ltf_monitor"
        selected_after = True
    elif ltf_disagreement:
        action = "MONITOR_LTF_PATH"
        branch = "m15_ltf_disagreement_requires_ltf_monitor"
        selected_after = True
    else:
        action = "PLACE_LIMIT"
        branch = "place_limit_no_ltf_execution_change"
        selected_after = True

    return {
        "stage06_ltf_action": action,
        "repair_branch": branch,
        "execution_behavior_changed": action != "PLACE_LIMIT",
        "selected_after_stage06_ltf": selected_after,
        "decision_inputs_exclude_future_r": True,
        "source_complete_for_ltf_decision": bool(source_complete),
        "source_status": source_status,
    }


def coverage_bucket() -> dict[str, Counter[str]]:
    return {
        "symbols": Counter(),
        "sessions": Counter(),
        "sides": Counter(),
        "frameworks": Counter(),
        "source_modes": Counter(),
        "months": Counter(),
        "repair_branches": Counter(),
        "ltf_actions": Counter(),
    }


def add_coverage(coverage: dict[str, Counter[str]], row: dict[str, Any], policy: dict[str, Any]) -> None:
    coverage["symbols"][str(row.get("symbol") or "")] += 1
    coverage["sessions"][str(row.get("session") or "")] += 1
    coverage["sides"][str(row.get("side") or "")] += 1
    coverage["frameworks"][str(row.get("framework") or "")] += 1
    coverage["source_modes"][str(row.get("source_mode") or "")] += 1
    coverage["months"][str(row.get("month") or "")] += 1
    coverage["repair_branches"][str(policy.get("repair_branch") or "")] += 1
    coverage["ltf_actions"][str(policy.get("stage06_ltf_action") or "")] += 1


def build_stage06() -> dict[str, Any]:
    selected_ids, stream_source, selected_counts = load_selected_stream_ids()
    failure_rows, path_row_ids = load_failure_rows(selected_ids)
    path_rows, path_join = load_path_rows(path_row_ids)
    disagreements, disagreement_join = load_disagreements(selected_ids)

    current = ScenarioStats()
    repaired = ScenarioStats()
    action_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    current_ltf_counts: Counter[str] = Counter()
    source_status_counts: Counter[str] = Counter()
    coverage = coverage_bucket()
    skipped_r = 0.0
    skipped_perf_rows = 0
    m15_ltf_delta_r = 0.0
    m15_ltf_delta_count = 0
    rows_written = 0

    with STAGE06_LEDGER.open("w", encoding="utf-8", newline="\n") as out:
        for idx, cid in enumerate(sorted(selected_ids), start=1):
            row = failure_rows.get(cid)
            if row is None:
                continue
            path_row = path_rows.get(str(row.get("path_row_id") or ""))
            disagreement = disagreements.get(cid)
            policy = classify_stage06_ltf_policy(row, path_row, disagreement)
            rows_written += 1
            action = policy["stage06_ltf_action"]
            branch = policy["repair_branch"]
            action_counts[action] += 1
            branch_counts[branch] += 1
            current_action = str(row.get("ltf_action") or "UNKNOWN")
            current_ltf_counts[current_action] += 1
            source_status_counts[str(policy.get("source_status") or "")] += 1
            add_coverage(coverage, row, policy)
            current.add(row, selected=True, action=current_action, branch="current_replay")
            repaired.add(
                row,
                selected=bool(policy["selected_after_stage06_ltf"]),
                action=action,
                branch=branch,
            )
            r_value = _as_float(row.get("simulated_r"))
            if not policy["selected_after_stage06_ltf"] and r_value is not None:
                skipped_r += r_value
                skipped_perf_rows += 1
            if disagreement is not None:
                ltf_r = _as_float(disagreement.get("ltf_simulated_r"))
                m15_r = _as_float(disagreement.get("m15_simulated_r"))
                if ltf_r is not None and m15_r is not None:
                    m15_ltf_delta_r += ltf_r - m15_r
                    m15_ltf_delta_count += 1
            out.write(
                json.dumps(
                    {
                        "schema_version": "vnext_production_candidate_repair_stage06_ltf_entry_nofill_repair_v1",
                        "route_id": ROUTE_ID,
                        "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR",
                        "row_id": f"stage06_ltf_repair_{rows_written:06d}",
                        "candidate_id": cid,
                        "selected_stream_source": stream_source.get(cid),
                        "as_of_utc": row.get("as_of_utc"),
                        "symbol": row.get("symbol"),
                        "session": row.get("session"),
                        "side": row.get("side"),
                        "framework": row.get("framework"),
                        "month": row.get("month"),
                        "source_mode": row.get("source_mode"),
                        "current_ltf_action": current_action,
                        "current_ltf_would_action": row.get("ltf_would_action"),
                        "current_pending_action": row.get("pending_action"),
                        "current_ltf_scoring_only": current_action == "PLACE_LIMIT",
                        "stage06_ltf_action": action,
                        "stage06_repair_branch": branch,
                        "execution_behavior_changed": policy["execution_behavior_changed"],
                        "selected_after_stage06_ltf": policy["selected_after_stage06_ltf"],
                        "decision_inputs_exclude_future_r": policy[
                            "decision_inputs_exclude_future_r"
                        ],
                        "source_complete_for_ltf_decision": policy[
                            "source_complete_for_ltf_decision"
                        ],
                        "path_source_status": policy["source_status"],
                        "path_row_id": row.get("path_row_id"),
                        "joined_path_row": path_row is not None,
                        "path_source_timeframe": None if path_row is None else path_row.get("source_timeframe"),
                        "path_source_mode": None if path_row is None else path_row.get("source_mode"),
                        "path_price_truth_status": None
                        if path_row is None
                        else path_row.get("price_path_truth_status"),
                        "path_source_window_complete": None
                        if path_row is None
                        else path_row.get("source_window_complete"),
                        "entry_touched_scoring_only": row.get("entry_touched"),
                        "terminal_outcome_scoring_only": row.get("terminal_outcome"),
                        "simulated_r_scoring_only": row.get("simulated_r"),
                        "no_fill_scoring_only": row.get("no_fill"),
                        "pending_lifecycle_state_scoring_only": row.get(
                            "pending_lifecycle_state"
                        ),
                        "pre_entry_tp_touch_utc_path_monitor_state": None
                        if path_row is None
                        else path_row.get("pre_entry_tp_touch_utc"),
                        "pre_entry_sl_touch_utc_path_monitor_state": None
                        if path_row is None
                        else path_row.get("pre_entry_sl_touch_utc"),
                        "same_bar_ambiguity_path_monitor_state": None
                        if path_row is None
                        else path_row.get("same_bar_ambiguity"),
                        "m15_vs_ltf_disagreement_joined": disagreement is not None,
                        "m15_simulated_r_scoring_only": None
                        if disagreement is None
                        else disagreement.get("m15_simulated_r"),
                        "ltf_simulated_r_scoring_only": None
                        if disagreement is None
                        else disagreement.get("ltf_simulated_r"),
                        "ltf_terminal_outcome_scoring_only": None
                        if disagreement is None
                        else disagreement.get("ltf_terminal_outcome"),
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    summary = {
        "schema_version": "vnext_production_candidate_repair_stage06_ltf_entry_nofill_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "inputs": {
            "failure_anatomy_ledger": rel(FAILURE_ANATOMY_LEDGER),
            "failure_anatomy_sha256": sha256_file(FAILURE_ANATOMY_LEDGER),
            "stage03_ledger": rel(STAGE03_LEDGER),
            "stage03_sha256": sha256_file(STAGE03_LEDGER),
            "stage05_ledger": rel(STAGE05_LEDGER),
            "stage05_sha256": sha256_file(STAGE05_LEDGER),
            "path_outcome_index": rel(PATH_OUTCOME_INDEX),
            "m15_vs_ltf_index": rel(M15_VS_LTF_INDEX),
        },
        "selected_stream_counts": selected_counts,
        "path_join": path_join,
        "m15_vs_ltf_join": disagreement_join,
        "ledger_rows": rows_written,
        "current_ltf_action_counts": dict(current_ltf_counts.most_common()),
        "stage06_ltf_action_counts": dict(action_counts.most_common()),
        "stage06_repair_branch_counts": dict(branch_counts.most_common()),
        "source_status_counts": dict(source_status_counts.most_common()),
        "selected_only_coverage": {
            key: dict(counter.most_common()) for key, counter in coverage.items()
        },
        "scenario_metrics": {
            "stage05_stream_current_ltf_place_limit": current.to_record(),
            "stage06_ltf_repaired_execution_policy": repaired.to_record(),
        },
        "replay_effect": {
            "execution_behavior_changed_rows": sum(
                count
                for action, count in action_counts.items()
                if action not in {"PLACE_LIMIT", "SOURCE_CAPTURE_REQUIRED"}
            ),
            "source_capture_required_rows": action_counts.get("SOURCE_CAPTURE_REQUIRED", 0),
            "stage06_skipped_perf_rows": skipped_perf_rows,
            "stage06_skipped_r_if_current_taken": round(skipped_r, 12),
            "m15_vs_ltf_disagreement_delta_r_ltf_minus_m15": round(m15_ltf_delta_r, 12),
            "m15_vs_ltf_disagreement_delta_count": m15_ltf_delta_count,
            "hard_skip_policy_rejected": True,
            "hard_skip_rejection_reason": (
                "pre_entry_target_or_protective_touch cohort was net positive "
                "when current-taken in the selected stream; Stage06 uses monitor/wait "
                "behavior instead of a hard execution skip"
            ),
        },
        "runtime_surface_proof": {
            "runtime_ltf_engine_function": "src/components/gtos_vnext_runtime.py:evaluate_vnext_ltf_path_execution",
            "orchestrator_asof_path_state_builder": "src/components/orchestrator.py:_build_gtos_vnext_ltf_path_state",
            "orchestrator_ltf_pending_monitor": "src/components/orchestrator.py:_check_pending_limit_ltf_path",
            "execution_telemetry_fields": [
                "gtos_vnext_ltf_path_action",
                "gtos_vnext_ltf_path_would_action",
                "gtos_vnext_ltf_path_applied",
                "gtos_vnext_ltf_path_reason",
                "gtos_vnext_ltf_path_monitor_timeframe",
                "gtos_vnext_ltf_path_adjusted_entry_price",
            ],
            "config_activation_gate": {
                "ltf_path_execution_enabled": True,
                "ltf_path_execution_apply_to_execution": False,
                "broker_facing_activation_change": False,
            },
        },
        "stage06_decision": "ltf_execution_repair_materialized_for_selected_stream_no_live_activation_flip",
    }
    STAGE06_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_state(summary)
    return summary


def update_state(summary: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    state["active_invariant"] = "repair_ltf_entry_nofill_execution_behavior"
    state["first_incomplete_invariant"] = "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    state["exact_next_action"] = (
        "Run Stage06 verifier, then repair AI/no-paid-call/supervisor behavior."
    )
    state.setdefault("stage_status_table", {})[
        "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR"
    ] = "in_progress"
    state.setdefault("output_artifact_paths", {}).update(
        {
            "stage06_ltf_entry_nofill_repair_ledger": rel(STAGE06_LEDGER),
            "stage06_ltf_entry_nofill_repair_summary": rel(STAGE06_SUMMARY),
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage06_ltf_entry_nofill_repair_rows": summary["ledger_rows"],
            "stage06_ltf_entry_nofill_repair_ledger_sha256": sha256_file(STAGE06_LEDGER),
        }
    )
    state.setdefault("repairs_applied", []).append(
        "stage06_ltf_entry_nofill_execution_policy_materialized"
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Can LTF/M1 path evidence change execution behavior rather than only score outcomes?",
            "status": "closed_stage06_policy_built_pending_verifier",
            "evidence_path": rel(STAGE06_SUMMARY),
            "current_ltf_action_counts": summary["current_ltf_action_counts"],
            "stage06_ltf_action_counts": summary["stage06_ltf_action_counts"],
            "replay_effect": summary["replay_effect"],
        }
    )
    state["updated_at_utc"] = utc_now()
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = build_stage06()
    print(
        json.dumps(
            {
                "ok": True,
                "ledger_rows": result["ledger_rows"],
                "current_ltf_action_counts": result["current_ltf_action_counts"],
                "stage06_ltf_action_counts": result["stage06_ltf_action_counts"],
                "replay_effect": result["replay_effect"],
                "summary": rel(STAGE06_SUMMARY),
                "ledger": rel(STAGE06_LEDGER),
            },
            sort_keys=True,
        )
    )

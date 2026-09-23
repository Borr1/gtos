from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
NO_PAID_MECHANICAL_FOLLOW_ACTIONS = {"MECHANICAL_FOLLOW_NO_AI", "FOLLOW_WITHOUT_AI"}

FAILURE_ANATOMY_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILURE_ANATOMY_LEDGER_2026-05-25.jsonl"
)
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
STAGE03_LEDGER_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_LEDGER_2026-05-25.jsonl"
)
STAGE03_SUMMARY_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_SUMMARY_2026-05-25.json"
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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_repaired_semantics(row: dict[str, Any]) -> dict[str, Any]:
    route = str(row.get("new_route_decision") or "LEGACY").upper()
    session = str(row.get("session") or "")
    pre_ai = str(row.get("pre_ai_action") or "")
    ltf_action = str(row.get("ltf_action") or "")
    pending_action = str(row.get("pending_action") or "")

    if session == "off_kz":
        stream_class = "diagnostic_off_kz_generated_candidate"
        reason = "off_kz_diagnostic_non_executable"
        route_executable = False
        final_executable = False
        preserve_current = False
    elif pre_ai == "SKIP_AI_AVOID_ONLY":
        stream_class = "pre_ai_avoid_only_non_executable"
        reason = "pre_ai_skip_avoid_only"
        route_executable = False
        final_executable = False
        preserve_current = False
    elif route == "FOLLOW":
        stream_class = "vnext_follow_executable_stream"
        reason = "vnext_follow_executable_stream"
        route_executable = True
        final_executable = True
        preserve_current = False
    elif route == "LEGACY":
        stream_class = "legacy_preserve_current_system_behavior"
        reason = "route_legacy_not_vnext_executable_preserve_current_system"
        route_executable = False
        final_executable = False
        preserve_current = True
    elif route == "MIXED":
        stream_class = "mixed_requires_ai_or_policy_resolution"
        reason = "route_mixed_requires_resolution_not_prop_budget"
        route_executable = False
        final_executable = False
        preserve_current = True
    elif route == "AVOID":
        stream_class = "vnext_avoid_non_executable"
        reason = "vnext_decision_avoid"
        route_executable = False
        final_executable = False
        preserve_current = False
    else:
        stream_class = "unknown_route_non_executable"
        reason = f"route_{route.lower()}_not_vnext_executable"
        route_executable = False
        final_executable = False
        preserve_current = False

    ltf_blocks = ltf_action in {"SKIP_LTF_NOFILL_AVOID"}
    pending_blocks = pending_action in {"SKIP_PENDING_NOFILL_AVOID"}
    if final_executable and ltf_blocks:
        final_executable = False
        reason = str(row.get("ltf_reason") or "ltf_path_non_executable")
        stream_class = "ltf_path_blocked_executable_candidate"
    if final_executable and pending_blocks:
        final_executable = False
        reason = str(row.get("pending_reason") or "pending_policy_non_executable")
        stream_class = "pending_policy_blocked_executable_candidate"

    return {
        "route_decision": route,
        "session": session,
        "pre_ai_action": pre_ai,
        "stream_class": stream_class,
        "route_follow_in_kz_pre_ltf_executable": bool(route_executable),
        "vnext_executable_stream_without_prop": bool(final_executable),
        "prop_governance_eligible_after_stage03": bool(final_executable),
        "preserve_current_system_behavior": bool(preserve_current),
        "reason": reason,
        "legacy_or_mixed": route in {"LEGACY", "MIXED"},
        "off_kz": session == "off_kz",
    }


@dataclass
class ScenarioAccumulator:
    name: str
    candidate_count: int = 0
    selected_count: int = 0
    performance_count: int = 0
    total_r: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    zero_count: int = 0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0
    skip_reasons: Counter[str] = field(default_factory=Counter)
    selected_coverage: dict[str, Counter[str]] = field(
        default_factory=lambda: {
            "symbols": Counter(),
            "sessions": Counter(),
            "sides": Counter(),
            "frameworks": Counter(),
            "source_modes": Counter(),
            "months": Counter(),
        }
    )

    def add(self, row: dict[str, Any], *, selected: bool, reason: str) -> None:
        self.candidate_count += 1
        if not selected:
            self.skip_reasons[reason] += 1
            return
        self.selected_count += 1
        self.selected_coverage["symbols"][str(row.get("symbol") or "")] += 1
        self.selected_coverage["sessions"][str(row.get("session") or "")] += 1
        self.selected_coverage["sides"][str(row.get("side") or "")] += 1
        self.selected_coverage["frameworks"][str(row.get("framework") or "")] += 1
        self.selected_coverage["source_modes"][str(row.get("source_mode") or "")] += 1
        self.selected_coverage["months"][str(row.get("month") or "")] += 1
        r_value = _as_float(row.get("simulated_r"))
        if r_value is None:
            return
        self.performance_count += 1
        self.total_r += r_value
        if r_value > 0:
            self.win_count += 1
            self.gross_win_r += r_value
        elif r_value < 0:
            self.loss_count += 1
            self.gross_loss_r += abs(r_value)
        else:
            self.zero_count += 1

    def to_record(self) -> dict[str, Any]:
        expectancy = self.total_r / self.performance_count if self.performance_count else None
        win_rate = self.win_count / self.performance_count if self.performance_count else None
        profit_factor = None if self.gross_loss_r == 0 else self.gross_win_r / self.gross_loss_r
        return {
            "scenario": self.name,
            "candidate_count": self.candidate_count,
            "selected_count": self.selected_count,
            "performance_count": self.performance_count,
            "total_r": round(self.total_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "win_rate": round(win_rate, 12) if win_rate is not None else None,
            "profit_factor": round(profit_factor, 12) if profit_factor is not None else None,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "zero_count": self.zero_count,
            "skip_reasons": dict(self.skip_reasons.most_common()),
            "selected_only_coverage": {
                key: dict(counter.most_common())
                for key, counter in self.selected_coverage.items()
            },
        }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_stage03() -> dict[str, Any]:
    if not FAILURE_ANATOMY_LEDGER.exists():
        raise FileNotFoundError(FAILURE_ANATOMY_LEDGER)

    scenarios = {
        name: ScenarioAccumulator(name)
        for name in (
            "current_baseline_executable_stream",
            "baseline_executable_stream_plus_prop_contract",
            "vnext_route_pressure_without_prop_governance",
            "vnext_executable_stream_without_prop_governance",
            "vnext_executable_stream_with_ev_prop_governance_contract",
            "external_budget_only_prop_comparison_contract",
            "ai_no_paid_call_diagnostic",
            "ltf_entry_nofill_execution_change_diagnostic",
        )
    }
    universe_coverage = {
        "symbols": Counter(),
        "sessions": Counter(),
        "sides": Counter(),
        "frameworks": Counter(),
        "source_modes": Counter(),
        "months": Counter(),
    }
    stream_counts: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    old_prop_on_nonexecutable = 0
    legacy_mixed_removed_from_prop_budget = 0
    off_kz_removed_from_prop_budget = 0
    pre_ai_removed_from_prop_budget = 0
    old_selected_non_follow = 0
    ledger_count = 0

    with STAGE03_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as out:
        for row in iter_jsonl(FAILURE_ANATOMY_LEDGER):
            ledger_count += 1
            semantics = classify_repaired_semantics(row)
            route_counts[semantics["route_decision"]] += 1
            stream_counts[semantics["stream_class"]] += 1
            for key, source_key in (
                ("symbols", "symbol"),
                ("sessions", "session"),
                ("sides", "side"),
                ("frameworks", "framework"),
                ("source_modes", "source_mode"),
                ("months", "month"),
            ):
                universe_coverage[key][str(row.get(source_key) or "")] += 1

            old_prop_evaluated = bool(row.get("prop_reason"))
            if old_prop_evaluated and not semantics["prop_governance_eligible_after_stage03"]:
                old_prop_on_nonexecutable += 1
            if semantics["legacy_or_mixed"] and not semantics["prop_governance_eligible_after_stage03"]:
                legacy_mixed_removed_from_prop_budget += 1
            if semantics["off_kz"] and not semantics["prop_governance_eligible_after_stage03"]:
                off_kz_removed_from_prop_budget += 1
            if semantics["pre_ai_action"] == "SKIP_AI_AVOID_ONLY" and not semantics[
                "prop_governance_eligible_after_stage03"
            ]:
                pre_ai_removed_from_prop_budget += 1
            if _as_bool(row.get("new_mechanical_selected")) and semantics["route_decision"] != "FOLLOW":
                old_selected_non_follow += 1

            baseline_selected = _as_bool(row.get("baseline_selected"))
            route_pressure_selected = bool(semantics["route_follow_in_kz_pre_ltf_executable"])
            vnext_executable_selected = bool(semantics["vnext_executable_stream_without_prop"])
            ai_actions = {
                str(row.get("ai_policy_action") or ""),
                str(row.get("ai_policy_would_action") or ""),
            }
            no_paid_selected = bool(
                vnext_executable_selected
                and ai_actions.intersection(NO_PAID_MECHANICAL_FOLLOW_ACTIONS)
            )
            ltf_change_selected = _as_bool(row.get("would_change_decision_or_execution_with_ltf_source"))

            scenarios["current_baseline_executable_stream"].add(
                row,
                selected=baseline_selected,
                reason="selected_current_baseline" if baseline_selected else str(row.get("baseline_selection_reason") or "baseline_not_selected"),
            )
            scenarios["baseline_executable_stream_plus_prop_contract"].add(
                row,
                selected=baseline_selected,
                reason=(
                    "stage04_segmented_prop_contract_input_baseline"
                    if baseline_selected
                    else str(row.get("baseline_selection_reason") or "baseline_not_selected")
                ),
            )
            scenarios["vnext_route_pressure_without_prop_governance"].add(
                row,
                selected=route_pressure_selected,
                reason=(
                    "vnext_follow_in_kz_pre_ltf_route_pressure"
                    if route_pressure_selected
                    else semantics["reason"]
                ),
            )
            scenarios["vnext_executable_stream_without_prop_governance"].add(
                row,
                selected=vnext_executable_selected,
                reason=(
                    "vnext_executable_stream_without_prop"
                    if vnext_executable_selected
                    else semantics["reason"]
                ),
            )
            scenarios["vnext_executable_stream_with_ev_prop_governance_contract"].add(
                row,
                selected=vnext_executable_selected,
                reason=(
                    "stage04_ev_prop_contract_input_vnext_executable"
                    if vnext_executable_selected
                    else semantics["reason"]
                ),
            )
            scenarios["external_budget_only_prop_comparison_contract"].add(
                row,
                selected=vnext_executable_selected,
                reason=(
                    "stage04_external_budget_contract_input_vnext_executable"
                    if vnext_executable_selected
                    else semantics["reason"]
                ),
            )
            scenarios["ai_no_paid_call_diagnostic"].add(
                row,
                selected=no_paid_selected,
                reason=(
                    "selected_follow_without_ai"
                    if no_paid_selected
                    else f"no_paid_ai_{str(row.get('ai_policy_action') or 'UNKNOWN').lower()}"
                ),
            )
            scenarios["ltf_entry_nofill_execution_change_diagnostic"].add(
                row,
                selected=ltf_change_selected,
                reason=(
                    "ltf_source_would_change_decision_or_execution"
                    if ltf_change_selected
                    else "ltf_source_no_execution_change"
                ),
            )

            out_row = {
                "schema_version": "vnext_production_candidate_repair_stage03_executable_stream_semantics_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR",
                "row_id": f"stage03_exec_semantics_{ledger_count:06d}",
                "candidate_id": row.get("candidate_id"),
                "as_of_utc": row.get("as_of_utc"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "route_family": row.get("route_family"),
                "month": row.get("month"),
                "source_mode": row.get("source_mode"),
                "terminal_outcome": row.get("terminal_outcome"),
                "simulated_r": row.get("simulated_r"),
                "baseline_selected": baseline_selected,
                "old_new_mechanical_selected": _as_bool(row.get("new_mechanical_selected")),
                "old_new_mechanical_selection_reason": row.get("new_mechanical_selection_reason"),
                "old_prop_selector_evaluated": old_prop_evaluated,
                "old_prop_action": row.get("prop_action"),
                "old_prop_reason": row.get("prop_reason"),
                "repaired_route_semantics": semantics,
                "scenario_membership": {
                    "current_baseline_executable_stream": baseline_selected,
                    "baseline_executable_stream_plus_prop_contract": baseline_selected,
                    "vnext_route_pressure_without_prop_governance": route_pressure_selected,
                    "vnext_executable_stream_without_prop_governance": vnext_executable_selected,
                    "vnext_executable_stream_with_ev_prop_governance_contract": vnext_executable_selected,
                    "external_budget_only_prop_comparison_contract": vnext_executable_selected,
                    "ai_no_paid_call_diagnostic": no_paid_selected,
                    "ltf_entry_nofill_execution_change_diagnostic": ltf_change_selected,
                },
                "selected_only_coverage_scope": "per_scenario_selected_only_coverage_in_summary",
                "prop_budget_repair_effect": {
                    "old_prop_evaluated_on_nonexecutable": bool(
                        old_prop_evaluated
                        and not semantics["prop_governance_eligible_after_stage03"]
                    ),
                    "legacy_mixed_removed_from_prop_budget": bool(
                        semantics["legacy_or_mixed"]
                        and not semantics["prop_governance_eligible_after_stage03"]
                    ),
                    "off_kz_removed_from_prop_budget": bool(
                        semantics["off_kz"]
                        and not semantics["prop_governance_eligible_after_stage03"]
                    ),
                    "prop_governance_eligible_after_stage03": semantics[
                        "prop_governance_eligible_after_stage03"
                    ],
                },
            }
            out.write(json.dumps(out_row, sort_keys=True) + "\n")

    scenario_records = {name: acc.to_record() for name, acc in scenarios.items()}
    prop_input_count = scenario_records[
        "vnext_executable_stream_with_ev_prop_governance_contract"
    ]["selected_count"]
    summary = {
        "schema_version": "vnext_production_candidate_repair_stage03_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "input_failure_anatomy_ledger": rel(FAILURE_ANATOMY_LEDGER),
        "input_failure_anatomy_sha256": sha256_file(FAILURE_ANATOMY_LEDGER),
        "row_count": ledger_count,
        "route_decision_counts": dict(route_counts.most_common()),
        "stream_class_counts": dict(stream_counts.most_common()),
        "candidate_universe_coverage": {
            key: dict(counter.most_common()) for key, counter in universe_coverage.items()
        },
        "scenario_metrics": scenario_records,
        "prop_budget_application_repair": {
            "old_failed_replay_rows_with_prop_selector_evaluated": old_prop_on_nonexecutable
            + prop_input_count,
            "corrected_prop_governance_input_rows": prop_input_count,
            "rows_removed_from_prop_budget_before_stage04": old_prop_on_nonexecutable,
            "legacy_mixed_rows_removed_from_prop_budget": legacy_mixed_removed_from_prop_budget,
            "off_kz_rows_removed_from_prop_budget": off_kz_removed_from_prop_budget,
            "pre_ai_avoid_rows_removed_from_prop_budget": pre_ai_removed_from_prop_budget,
            "old_selected_non_follow_rows_now_nonexecutable": old_selected_non_follow,
            "prop_budget_applies_only_to_executable_stream": True,
        },
        "clean_scenario_status": {
            "current_baseline_executable_stream": "computed_stage03",
            "baseline_plus_segmented_prop_governance": "contract_input_ready_for_stage04",
            "vnext_route_pressure_without_prop_governance": "computed_stage03",
            "vnext_executable_stream_with_ev_prop_governance": "contract_input_ready_for_stage04",
            "external_budget_only_prop_comparison": "contract_input_ready_for_stage04",
            "ai_no_paid_call_diagnostic": "computed_diagnostic_stage03",
            "ltf_entry_nofill_execution_change_scenario": "diagnostic_membership_computed_stage03_stage06_owns_execution_repair",
            "layer_ablations": "scenario_contracts_ready_stage04_to_stage08",
        },
        "stage03_decision": (
            "replay_semantics_repaired_prop_governance_now_executable_stream_only"
        ),
    }
    write_json(STAGE03_SUMMARY_PATH, summary)
    update_state(summary)
    return summary


def update_state(summary: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR"
    state["active_invariant"] = "repair_executable_stream_and_follow_legacy_mixed_route_semantics"
    state["first_incomplete_invariant"] = "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR"
    state["exact_next_action"] = (
        "Run Stage03 verifier, then build Stage04 segmented EV prop challenge governor on the "
        "stage03 executable-stream contract inputs."
    )
    state.setdefault("stage_status_table", {})[
        "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR"
    ] = "in_progress"
    state.setdefault("output_artifact_paths", {}).update(
        {
            "stage03_executable_stream_semantics_ledger": rel(STAGE03_LEDGER_PATH),
            "stage03_executable_stream_semantics_summary": rel(STAGE03_SUMMARY_PATH),
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage03_executable_stream_semantics_rows": summary["row_count"],
            "stage03_corrected_prop_governance_input_rows": summary[
                "prop_budget_application_repair"
            ]["corrected_prop_governance_input_rows"],
            "stage03_legacy_mixed_removed_from_prop_budget": summary[
                "prop_budget_application_repair"
            ]["legacy_mixed_rows_removed_from_prop_budget"],
        }
    )
    state.setdefault("repairs_applied", []).append(
        "stage03_executable_stream_semantics_and_prop_budget_contract_materialized"
    )
    state.setdefault("failures_found", []).append(
        "stage03_failed_replay_prop_budget_applied_to_nonexecutable_rows"
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Which rows are allowed to consume prop governance after repairing route semantics?",
            "status": "closed_stage03_executable_stream_contract_built",
            "evidence_path": rel(STAGE03_SUMMARY_PATH),
            "corrected_prop_governance_input_rows": summary["prop_budget_application_repair"][
                "corrected_prop_governance_input_rows"
            ],
            "rows_removed_from_prop_budget_before_stage04": summary[
                "prop_budget_application_repair"
            ]["rows_removed_from_prop_budget_before_stage04"],
        }
    )
    state["updated_at_utc"] = utc_now()
    write_json(STATE_PATH, state)


if __name__ == "__main__":
    result = build_stage03()
    print(
        json.dumps(
            {
                "ok": True,
                "row_count": result["row_count"],
                "corrected_prop_governance_input_rows": result[
                    "prop_budget_application_repair"
                ]["corrected_prop_governance_input_rows"],
                "ledger": rel(STAGE03_LEDGER_PATH),
                "summary": rel(STAGE03_SUMMARY_PATH),
            },
            sort_keys=True,
        )
    )

from __future__ import annotations

from collections import Counter, defaultdict
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

FAILURE_ANATOMY_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILURE_ANATOMY_LEDGER_2026-05-25.jsonl"
)
STAGE03_LEDGER_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_LEDGER_2026-05-25.jsonl"
)
STAGE04_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_POLICY_COMPARISON_SUMMARY_2026-05-25.json"
)
STAGE04_DECISION_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE04_PROP_GOVERNOR_DECISION_LEDGER_2026-05-25.jsonl"
)
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
STAGE05_POLICY_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_LEDGER_2026-05-25.jsonl"
)
STAGE05_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_SUMMARY_2026-05-25.json"
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


def avoid_group_key(row: dict[str, Any]) -> tuple[str, str]:
    route = str(row.get("new_route_decision") or "")
    pre_ai = str(row.get("pre_ai_action") or "")
    family = str(row.get("avoid_evidence_family") or "")
    component = str(row.get("avoid_source_component") or "")
    if route == "AVOID":
        return (family or "__NULL_AVOID_EVIDENCE_FAMILY__", component or "__NULL__")
    if pre_ai == "SKIP_AI_AVOID_ONLY":
        return ("pre_ai_skip_avoid_only", "pre_ai_skip_avoid_only_no_route_avoid_join")
    return ("not_avoid_or_pre_ai", "not_avoid_or_pre_ai")


@dataclass
class EvStats:
    row_count: int = 0
    r_count: int = 0
    r_sum_if_taken: float = 0.0
    winners_blocked: int = 0
    losers_avoided: int = 0
    null_r_rows: int = 0

    def add_r(self, value: Any) -> None:
        self.row_count += 1
        r_value = _as_float(value)
        if r_value is None:
            self.null_r_rows += 1
            return
        self.r_count += 1
        self.r_sum_if_taken += r_value
        if r_value > 0:
            self.winners_blocked += 1
        elif r_value < 0:
            self.losers_avoided += 1

    def to_record(self) -> dict[str, Any]:
        mean_r = self.r_sum_if_taken / self.r_count if self.r_count else None
        return {
            "row_count": self.row_count,
            "r_count": self.r_count,
            "r_sum_if_taken": round(self.r_sum_if_taken, 12),
            "mean_r_if_taken": round(mean_r, 12) if mean_r is not None else None,
            "winners_blocked": self.winners_blocked,
            "losers_avoided": self.losers_avoided,
            "null_r_rows": self.null_r_rows,
        }


@dataclass
class GroupStats:
    evidence_family: str
    source_component: str
    row_count: int = 0
    r_count: int = 0
    r_sum_if_taken: float = 0.0
    winners_blocked: int = 0
    losers_avoided: int = 0
    null_r_rows: int = 0
    symbols: Counter[str] = field(default_factory=Counter)
    sessions: Counter[str] = field(default_factory=Counter)
    sides: Counter[str] = field(default_factory=Counter)
    frameworks: Counter[str] = field(default_factory=Counter)
    months: Counter[str] = field(default_factory=Counter)
    source_modes: Counter[str] = field(default_factory=Counter)
    route_families: Counter[str] = field(default_factory=Counter)
    partition_ev: dict[str, dict[str, EvStats]] = field(
        default_factory=lambda: {
            "symbols": defaultdict(EvStats),
            "sessions": defaultdict(EvStats),
            "sides": defaultdict(EvStats),
            "frameworks": defaultdict(EvStats),
            "months": defaultdict(EvStats),
            "source_modes": defaultdict(EvStats),
            "route_families": defaultdict(EvStats),
        }
    )

    def add(self, row: dict[str, Any]) -> None:
        self.row_count += 1
        r_value = _as_float(row.get("simulated_r"))
        if r_value is None:
            self.null_r_rows += 1
        else:
            self.r_count += 1
            self.r_sum_if_taken += r_value
            if r_value > 0:
                self.winners_blocked += 1
            elif r_value < 0:
                self.losers_avoided += 1
        self.symbols[str(row.get("symbol") or "")] += 1
        self.sessions[str(row.get("session") or "")] += 1
        self.sides[str(row.get("side") or "")] += 1
        self.frameworks[str(row.get("framework") or "")] += 1
        self.months[str(row.get("month") or "")] += 1
        self.source_modes[str(row.get("source_mode") or "")] += 1
        self.route_families[str(row.get("route_family") or "")] += 1
        partition_values = {
            "symbols": row.get("symbol"),
            "sessions": row.get("session"),
            "sides": row.get("side"),
            "frameworks": row.get("framework"),
            "months": row.get("month"),
            "source_modes": row.get("source_mode"),
            "route_families": row.get("route_family"),
        }
        for dimension, raw_value in partition_values.items():
            self.partition_ev[dimension][str(raw_value or "")].add_r(row.get("simulated_r"))

    def decision(self) -> dict[str, Any]:
        if self.source_component == "__NULL__":
            action = "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK"
            reason = "missing_source_component_attribution_and_net_harmful_or_unproven"
            classification = "context_only_missing_attribution"
        elif self.row_count < 20 or self.r_count < 20:
            action = "AI_OR_CONTEXT_RESOLUTION_REQUIRED"
            reason = "small_sample_avoid_family_not_hard_blockable"
            classification = "unresolved_small_sample"
        elif self.r_sum_if_taken < 0 and self.losers_avoided > self.winners_blocked:
            action = "PRESERVE_BOUNDED_AVOID_FILTER"
            reason = "negative_r_if_taken_losers_avoided_exceed_winners_blocked"
            classification = "useful_bounded_avoid_filter"
        elif self.r_sum_if_taken > 0:
            action = "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK"
            reason = "positive_r_if_taken_hard_block_is_harmful"
            classification = "harmful_broad_hard_block_context_only"
        else:
            action = "AI_OR_CONTEXT_RESOLUTION_REQUIRED"
            reason = "mixed_or_flat_ev_requires_resolution_not_hard_block"
            classification = "mixed_requires_ai_or_context_resolution"
        return {
            "implementation_decision": action,
            "evidence_classification": classification,
            "decision_reason": reason,
            "row_count": self.row_count,
            "r_count": self.r_count,
            "r_sum_if_taken": round(self.r_sum_if_taken, 12),
            "mean_r_if_taken": round(self.r_sum_if_taken / self.r_count, 12)
            if self.r_count
            else None,
            "winners_blocked": self.winners_blocked,
            "losers_avoided": self.losers_avoided,
            "null_r_rows": self.null_r_rows,
            "selected_only_repair_scope": "avoid_pre_ai_rows_recovered_only_if_demoted_and_in_kz",
        }

    def to_record(self) -> dict[str, Any]:
        decision = self.decision()
        return {
            "evidence_family": self.evidence_family,
            "source_component": self.source_component,
            **decision,
            "coverage": {
                "symbols": dict(self.symbols.most_common()),
                "sessions": dict(self.sessions.most_common()),
                "sides": dict(self.sides.most_common()),
                "frameworks": dict(self.frameworks.most_common()),
                "months": dict(self.months.most_common()),
                "source_modes": dict(self.source_modes.most_common()),
                "route_families": dict(self.route_families.most_common()),
            },
            "partition_ev": {
                dimension: {
                    value: stats.to_record()
                    for value, stats in sorted(values.items())
                }
                for dimension, values in self.partition_ev.items()
            },
        }


@dataclass
class ScenarioStats:
    selected_count: int = 0
    performance_count: int = 0
    total_r: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    recovered_count: int = 0
    recovered_r: float = 0.0
    source_decisions: Counter[str] = field(default_factory=Counter)

    def add(self, row: dict[str, Any], *, recovered: bool, decision: str) -> None:
        self.selected_count += 1
        self.source_decisions[decision] += 1
        if recovered:
            self.recovered_count += 1
        r_value = _as_float(row.get("simulated_r"))
        if r_value is None:
            return
        self.performance_count += 1
        self.total_r += r_value
        if recovered:
            self.recovered_r += r_value
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
            "recovered_count": self.recovered_count,
            "recovered_r": round(self.recovered_r, 12),
            "source_decision_counts": dict(self.source_decisions.most_common()),
        }


def is_avoid_or_pre_ai(row: dict[str, Any]) -> bool:
    return (
        str(row.get("new_route_decision") or "") == "AVOID"
        or str(row.get("pre_ai_action") or "") == "SKIP_AI_AVOID_ONLY"
    )


def build_group_decisions() -> tuple[dict[tuple[str, str], GroupStats], int]:
    groups: dict[tuple[str, str], GroupStats] = {}
    row_count = 0
    for row in iter_jsonl(FAILURE_ANATOMY_LEDGER):
        if not is_avoid_or_pre_ai(row):
            continue
        row_count += 1
        key = avoid_group_key(row)
        if key not in groups:
            groups[key] = GroupStats(evidence_family=key[0], source_component=key[1])
        groups[key].add(row)
    return groups, row_count


def group_decision_lookup(groups: dict[tuple[str, str], GroupStats]) -> dict[tuple[str, str], dict[str, Any]]:
    return {key: group.to_record() for key, group in groups.items()}


def load_stage03_membership() -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    membership: dict[str, dict[str, Any]] = {}
    counters: Counter[str] = Counter()
    duplicate_candidate_ids = 0
    for row in iter_jsonl(STAGE03_LEDGER_PATH):
        counters["rows"] += 1
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            counters["missing_candidate_id"] += 1
            continue
        if candidate_id in membership:
            duplicate_candidate_ids += 1
        scenario_membership = row.get("scenario_membership") or {}
        repaired_route = row.get("repaired_route_semantics") or {}
        membership[candidate_id] = {
            "vnext_executable_stream_without_prop_governance": _as_bool(
                scenario_membership.get("vnext_executable_stream_without_prop_governance")
            ),
            "vnext_executable_stream_with_ev_prop_governance_contract": _as_bool(
                scenario_membership.get(
                    "vnext_executable_stream_with_ev_prop_governance_contract"
                )
            ),
            "baseline_executable_stream_plus_prop_contract": _as_bool(
                scenario_membership.get("baseline_executable_stream_plus_prop_contract")
            ),
            "stream_class": repaired_route.get("stream_class"),
            "prop_governance_eligible_after_stage03": _as_bool(
                repaired_route.get("prop_governance_eligible_after_stage03")
            ),
        }
    counters["unique_candidate_ids"] = len(membership)
    counters["duplicate_candidate_ids"] = duplicate_candidate_ids
    return membership, dict(counters)


def load_stage04_selected_context() -> dict[str, Any]:
    if not STAGE04_SUMMARY_PATH.exists() or not STAGE04_DECISION_LEDGER_PATH.exists():
        return {
            "stage04_context_available": False,
            "reason": "stage04_summary_or_decision_ledger_missing",
        }
    summary = json.loads(STAGE04_SUMMARY_PATH.read_text(encoding="utf-8"))
    vnext = (summary.get("scenarios") or {}).get(
        "vnext_executable_stream_with_ev_prop_governance_contract", {}
    )
    best_policy = (
        vnext.get("best_policy_reference_fee_599_payout_8000", {}).get("policy")
    )
    context: dict[str, Any] = {
        "stage04_context_available": True,
        "input_stage04_summary": rel(STAGE04_SUMMARY_PATH),
        "input_stage04_summary_sha256": sha256_file(STAGE04_SUMMARY_PATH),
        "input_stage04_decision_ledger": rel(STAGE04_DECISION_LEDGER_PATH),
        "input_stage04_decision_ledger_sha256": sha256_file(STAGE04_DECISION_LEDGER_PATH),
        "vnext_best_policy_reference_fee_599_payout_8000": best_policy,
        "vnext_prop_policy_input_rows": vnext.get("input_rows"),
        "selected_candidate_ids_for_best_policy": 0,
        "blocked_candidate_ids_for_best_policy": 0,
    }
    if not best_policy:
        return context
    selected_ids: set[str] = set()
    blocked_ids: set[str] = set()
    for row in iter_jsonl(STAGE04_DECISION_LEDGER_PATH):
        if row.get("scenario") != "vnext_executable_stream_with_ev_prop_governance_contract":
            continue
        if row.get("policy") != best_policy:
            continue
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        if _as_bool(row.get("selected")):
            selected_ids.add(candidate_id)
        else:
            blocked_ids.add(candidate_id)
    context["selected_candidate_ids_for_best_policy"] = len(selected_ids)
    context["blocked_candidate_ids_for_best_policy"] = len(blocked_ids)
    return context


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_stage05() -> dict[str, Any]:
    groups, avoid_pre_ai_rows = build_group_decisions()
    decisions = group_decision_lookup(groups)
    stage03_membership, stage03_membership_counts = load_stage03_membership()
    stage04_selected_context = load_stage04_selected_context()
    base = ScenarioStats()
    repaired = ScenarioStats()
    policy_rows = 0
    decision_counts: Counter[str] = Counter()
    null_component_rows = 0
    useful_preserved_rows = 0
    harmful_demoted_rows = 0
    missing_stage03_membership_rows = 0

    with STAGE05_POLICY_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as out:
        for row in iter_jsonl(FAILURE_ANATOMY_LEDGER):
            candidate_id = row.get("candidate_id")
            stage03 = stage03_membership.get(str(candidate_id or ""))
            if stage03 is None:
                missing_stage03_membership_rows += 1
                stage03 = {}
            base_selected = _as_bool(
                stage03.get("vnext_executable_stream_without_prop_governance")
            )
            if base_selected:
                base.add(row, recovered=False, decision="stage03_vnext_executable")
                repaired.add(row, recovered=False, decision="stage03_vnext_executable")

            if not is_avoid_or_pre_ai(row):
                continue
            policy_rows += 1
            key = avoid_group_key(row)
            decision = decisions[key]
            action = decision["implementation_decision"]
            decision_counts[action] += 1
            if key[1] == "__NULL__":
                null_component_rows += 1
            if action == "PRESERVE_BOUNDED_AVOID_FILTER":
                useful_preserved_rows += 1
            if action == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK":
                harmful_demoted_rows += 1
            recoverable = (
                action == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK"
                and str(row.get("session") or "") != "off_kz"
                and str(row.get("terminal_outcome") or "") != "missing_source_denominator_excluded"
            )
            if recoverable and not base_selected:
                repaired.add(row, recovered=True, decision=action)
            out.write(
                json.dumps(
                    {
                        "schema_version": "vnext_production_candidate_repair_stage05_avoid_pre_ai_policy_v1",
                        "route_id": ROUTE_ID,
                        "stage_id": "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR",
                        "row_id": f"stage05_avoid_pre_ai_{policy_rows:06d}",
                        "candidate_id": candidate_id,
                        "as_of_utc": row.get("as_of_utc"),
                        "symbol": row.get("symbol"),
                        "session": row.get("session"),
                        "side": row.get("side"),
                        "framework": row.get("framework"),
                        "source_mode": row.get("source_mode"),
                        "month": row.get("month"),
                        "new_route_decision": row.get("new_route_decision"),
                        "pre_ai_action": row.get("pre_ai_action"),
                        "avoid_evidence_family": key[0],
                        "avoid_source_component": key[1],
                        "simulated_r_if_taken": row.get("simulated_r"),
                        "terminal_outcome": row.get("terminal_outcome"),
                        "stage03_stream_class": stage03.get("stream_class"),
                        "stage03_vnext_executable_stream_without_prop_governance": base_selected,
                        "stage03_prop_governance_eligible_after_stage03": _as_bool(
                            stage03.get("prop_governance_eligible_after_stage03")
                        ),
                        "implementation_decision": action,
                        "evidence_classification": decision["evidence_classification"],
                        "decision_reason": decision["decision_reason"],
                        "group_r_sum_if_taken": decision["r_sum_if_taken"],
                        "group_winners_blocked": decision["winners_blocked"],
                        "group_losers_avoided": decision["losers_avoided"],
                        "recovered_into_stage05_no_prop_stream": bool(recoverable and not base_selected),
                        "hard_block_allowed_after_repair": action == "PRESERVE_BOUNDED_AVOID_FILTER",
                        "missing_attribution_demoted": key[1] == "__NULL__"
                        and action == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK",
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    group_records = [record for _, record in sorted(decisions.items())]
    summary = {
        "schema_version": "vnext_production_candidate_repair_stage05_avoid_pre_ai_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "input_failure_anatomy_ledger": rel(FAILURE_ANATOMY_LEDGER),
        "input_failure_anatomy_sha256": sha256_file(FAILURE_ANATOMY_LEDGER),
        "input_stage03_ledger": rel(STAGE03_LEDGER_PATH),
        "input_stage03_sha256": sha256_file(STAGE03_LEDGER_PATH),
        "stage03_membership_counts": stage03_membership_counts,
        "missing_stage03_membership_rows": missing_stage03_membership_rows,
        "stage04_selected_stream_context": stage04_selected_context,
        "avoid_pre_ai_policy_rows": policy_rows,
        "avoid_pre_ai_input_rows": avoid_pre_ai_rows,
        "group_count": len(group_records),
        "decision_counts": dict(decision_counts.most_common()),
        "null_component_rows_demoted": null_component_rows,
        "useful_preserved_rows": useful_preserved_rows,
        "harmful_demoted_rows": harmful_demoted_rows,
        "group_decisions": group_records,
        "scenario_metrics": {
            "stage03_vnext_executable_without_prop_baseline": base.to_record(),
            "stage05_avoid_pre_ai_repaired_without_prop": repaired.to_record(),
        },
        "runtime_policy_recommendation": {
            "preserve_hard_avoid_components": [
                row["source_component"]
                for row in group_records
                if row["implementation_decision"] == "PRESERVE_BOUNDED_AVOID_FILTER"
            ],
            "demote_to_context_components": [
                row["source_component"]
                for row in group_records
                if row["implementation_decision"] == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK"
            ],
            "ai_or_context_resolution_components": [
                row["source_component"]
                for row in group_records
                if row["implementation_decision"] == "AI_OR_CONTEXT_RESOLUTION_REQUIRED"
            ],
            "broker_facing_activation_change": False,
            "owner_approval_required_before_runtime_config_change": True,
        },
        "stage05_decision": "harmful_avoid_pre_ai_blocks_demoted_or_bounded_from_full_row_ev",
    }
    write_json(STAGE05_SUMMARY_PATH, summary)
    update_state(summary)
    return summary


def update_state(summary: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    state["active_invariant"] = "repair_vnext_avoid_and_pre_ai_pressure_with_selected_only_ev"
    state["first_incomplete_invariant"] = "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    state["exact_next_action"] = (
        "Run Stage05 verifier, then repair LTF entry/no-fill execution behavior from selected-stream evidence."
    )
    state.setdefault("stage_status_table", {})[
        "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR"
    ] = "in_progress"
    state.setdefault("output_artifact_paths", {}).update(
        {
            "stage05_avoid_pre_ai_repair_ledger": rel(STAGE05_POLICY_LEDGER_PATH),
            "stage05_avoid_pre_ai_repair_summary": rel(STAGE05_SUMMARY_PATH),
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage05_avoid_pre_ai_policy_rows": summary["avoid_pre_ai_policy_rows"],
            "stage05_avoid_pre_ai_repair_ledger_sha256": sha256_file(
                STAGE05_POLICY_LEDGER_PATH
            ),
        }
    )
    state.setdefault("repairs_applied", []).append(
        "stage05_avoid_pre_ai_harmful_blocks_demoted_and_useful_blocks_bounded"
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Which vNext AVOID/pre-AI families should remain hard execution blocks?",
            "status": "closed_stage05_policy_built_pending_verifier",
            "evidence_path": rel(STAGE05_SUMMARY_PATH),
            "decision_counts": summary["decision_counts"],
            "scenario_delta_r": round(
                summary["scenario_metrics"]["stage05_avoid_pre_ai_repaired_without_prop"][
                    "total_r"
                ]
                - summary["scenario_metrics"]["stage03_vnext_executable_without_prop_baseline"][
                    "total_r"
                ],
                12,
            ),
        }
    )
    state["updated_at_utc"] = utc_now()
    write_json(STATE_PATH, state)


if __name__ == "__main__":
    result = build_stage05()
    print(
        json.dumps(
            {
                "ok": True,
                "policy_rows": result["avoid_pre_ai_policy_rows"],
                "group_count": result["group_count"],
                "decision_counts": result["decision_counts"],
                "summary": rel(STAGE05_SUMMARY_PATH),
                "ledger": rel(STAGE05_POLICY_LEDGER_PATH),
                "scenario_metrics": result["scenario_metrics"],
            },
            sort_keys=True,
        )
    )

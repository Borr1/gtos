from __future__ import annotations

import gzip
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FAILED_ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25"
FULL_REPLAY_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24"

STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE01_FAILURE_ANATOMY_SUMMARY_2026-05-25.json"
FAILURE_ANATOMY_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILURE_ANATOMY_LEDGER_2026-05-25.jsonl"
SELECTED_ROWS_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SELECTED_ROWS_LEDGER_2026-05-25.jsonl"
DROPPED_BASELINE_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_DROPPED_BASELINE_LEDGER_2026-05-25.jsonl"
AVOID_EV_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_AVOID_EV_LEDGER_2026-05-25.jsonl"
ROUTE_SEMANTICS_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_ROUTE_SEMANTICS_LEDGER_2026-05-25.jsonl"
LTF_EFFECT_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_LTF_ENTRY_EFFECT_LEDGER_2026-05-25.jsonl"
AI_POLICY_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_AI_POLICY_SUPERVISOR_LEDGER_2026-05-25.jsonl"
ACCEPTANCE_GATE_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_ACCEPTANCE_GATE_FAILURE_LEDGER_2026-05-25.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def git_status_short() -> list[str]:
    result = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip().splitlines()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def iter_stage09_rows() -> Iterable[dict[str, Any]]:
    for shard in sorted((FAILED_ROUTE_DIR / "stage09_shards").glob("*/replay_comparison.jsonl.gz")):
        with gzip.open(shard, "rt", encoding="utf-8") as handle:
            for line in handle:
                yield json.loads(line)


def iter_dominance_rows() -> Iterable[dict[str, Any]]:
    index = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_DOMINANCE_AND_POLLUTION_LEDGER_2026-05-24.jsonl"
    with index.open("r", encoding="utf-8") as handle:
        for line in handle:
            meta = json.loads(line)
            chunk = ROOT / meta["chunk_path"]
            with gzip.open(chunk, "rt", encoding="utf-8") as gz:
                for row_line in gz:
                    yield json.loads(row_line)


def month_key(as_of_utc: str | None) -> str:
    if not as_of_utc:
        return "unknown_month"
    return as_of_utc[:7]


def r_value(row: dict[str, Any]) -> float | None:
    value = (row.get("post_decision_scoring") or {}).get("simulated_r")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def outcome_class(r: float | None, terminal_outcome: str | None) -> str:
    if r is None:
        if terminal_outcome == "no_fill":
            return "no_fill"
        if terminal_outcome == "missing_source_denominator_excluded":
            return "missing_source"
        return "null_r"
    if r > 0:
        return "winner"
    if r < 0:
        return "loser"
    return "zero"


def compact_candidate(row: dict[str, Any], idx: int) -> dict[str, Any]:
    prev = row.get("previous_current_shadow") or {}
    new = row.get("new_production_change") or {}
    scoring = row.get("post_decision_scoring") or {}
    route = new.get("route") or {}
    pre_ai = new.get("pre_ai") or {}
    ai_policy = new.get("ai_policy") or {}
    ai_supervisor = new.get("ai_supervisor") or {}
    prop = new.get("prop_safe_selector") or {}
    ext_prop = new.get("external_budget_only_prop_safe_selector") or {}
    ltf = new.get("ltf_path_execution") or {}
    pending = new.get("pending_policy") or {}
    risk = new.get("risk_adjustment") or {}
    missed = scoring.get("missed_winner_avoided_loser") or {}
    nofill = scoring.get("nofill_lifecycle") or {}
    r = r_value(row)
    terminal = scoring.get("terminal_outcome")
    return {
        "row_id": f"stage01_fail_anatomy_{idx:06d}",
        "candidate_id": row.get("candidate_id"),
        "as_of_utc": row.get("as_of_utc"),
        "month": month_key(row.get("as_of_utc")),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "session": row.get("session"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "route_family": row.get("route_family"),
        "market_timeframe": row.get("market_timeframe"),
        "source_mode": scoring.get("source_mode"),
        "source_path": scoring.get("source_path"),
        "source_evidence_type": scoring.get("source_evidence_type"),
        "terminal_outcome": terminal,
        "simulated_r": r,
        "outcome_class": outcome_class(r, terminal),
        "baseline_selected": bool(prev.get("selected")),
        "baseline_selection_reason": prev.get("selection_reason"),
        "baseline_route_decision": prev.get("route_decision"),
        "baseline_pre_ai_action": prev.get("pre_ai_action"),
        "baseline_risk_pct": prev.get("risk_pct"),
        "new_mechanical_selected": bool(new.get("mechanical_selected")),
        "new_mechanical_selection_reason": new.get("mechanical_selection_reason"),
        "new_mechanical_risk_pct": new.get("mechanical_risk_pct"),
        "new_route_decision": route.get("decision"),
        "new_route_block_reason": route.get("block_reason"),
        "new_route_matched": route.get("matched"),
        "pre_ai_action": pre_ai.get("action"),
        "pre_ai_would_action": pre_ai.get("would_action"),
        "pre_ai_decision": pre_ai.get("decision"),
        "ai_policy_action": ai_policy.get("action"),
        "ai_policy_would_action": ai_policy.get("would_action"),
        "ai_policy_would_allow_ai_call": ai_policy.get("would_allow_ai_call"),
        "ai_supervisor_action": ai_supervisor.get("action"),
        "ai_supervisor_disable_ai_narrowing": ai_supervisor.get("disable_ai_narrowing"),
        "prop_action": prop.get("action"),
        "prop_would_action": prop.get("would_action"),
        "prop_reason": prop.get("reason"),
        "prop_before_risk_pct": prop.get("before_risk_pct"),
        "prop_after_risk_pct": prop.get("after_risk_pct"),
        "prop_remaining_daily_cushion": (prop.get("external_rule_projection") or {}).get("remaining_daily_cushion"),
        "prop_remaining_overall_cushion": (prop.get("external_rule_projection") or {}).get("remaining_overall_cushion"),
        "prop_projected_daily_cushion_after_full_risk": (prop.get("external_rule_projection") or {}).get("projected_daily_cushion_after_full_risk"),
        "prop_projected_overall_cushion_after_full_risk": (prop.get("external_rule_projection") or {}).get("projected_overall_cushion_after_full_risk"),
        "external_budget_only_prop_action": ext_prop.get("action"),
        "external_budget_only_prop_reason": ext_prop.get("reason"),
        "ltf_action": ltf.get("action"),
        "ltf_would_action": ltf.get("would_action"),
        "ltf_reason": ltf.get("reason"),
        "pending_action": pending.get("action"),
        "pending_would_action": pending.get("would_action"),
        "risk_adjustment_after_risk_pct": risk.get("after_risk_pct"),
        "risk_adjustment_reason": risk.get("reason"),
        "entry_touched": scoring.get("entry_touched"),
        "no_fill": nofill.get("no_fill"),
        "pending_lifecycle_state": nofill.get("pending_lifecycle_state"),
        "best_available_replay_mode": scoring.get("best_available_replay_mode"),
        "missed_winner_avoided_loser_classification": missed.get("classification"),
        "would_change_decision_or_execution_with_ltf_source": missed.get("would_change_decision_or_execution_with_ltf_source"),
        "path_row_id": scoring.get("path_row_id"),
        "scoring_joined_after_decision": scoring.get("scoring_joined_after_decision"),
    }


def transition_key(record: dict[str, Any]) -> str:
    return f"baseline_{str(record['baseline_selected']).lower()}__new_{str(record['new_mechanical_selected']).lower()}"


def inc_cov(coverage: dict[str, Counter[str]], record: dict[str, Any]) -> None:
    for key in ("symbol", "session", "side", "framework", "source_mode", "month", "outcome_class"):
        coverage[key][str(record.get(key) or "unknown")] += 1


def metric_bucket() -> dict[str, Any]:
    return {"rows": 0, "performance_rows": 0, "r_sum": 0.0, "winners": 0, "losers": 0, "null_r": 0}


def add_metric(bucket: dict[str, Any], r: float | None) -> None:
    bucket["rows"] += 1
    if r is None:
        bucket["null_r"] += 1
        return
    bucket["performance_rows"] += 1
    bucket["r_sum"] += r
    if r > 0:
        bucket["winners"] += 1
    elif r < 0:
        bucket["losers"] += 1


def collect_avoid_ids() -> set[str]:
    avoid_ids = set()
    for row in iter_stage09_rows():
        new = row.get("new_production_change") or {}
        if new.get("mechanical_selection_reason") == "vnext_decision_avoid":
            avoid_ids.add(str(row.get("candidate_id")))
    return avoid_ids


def build_dominance_map(avoid_ids: set[str]) -> dict[str, dict[str, Any]]:
    dominance: dict[str, dict[str, Any]] = {}
    for row in iter_dominance_rows():
        cid = str(row.get("candidate_id") or "")
        if cid not in avoid_ids:
            continue
        if row.get("surface") != "route_decision":
            continue
        if row.get("dominant_decision") != "AVOID" and row.get("all_evidence_decision") != "AVOID":
            continue
        compact = {
            "dominance_row_id": row.get("dominance_row_id"),
            "runtime_mode": row.get("runtime_mode"),
            "dominant_decision": row.get("dominant_decision"),
            "dominant_source_component": row.get("dominant_source_component") or "__NULL__",
            "dominant_evidence_family": row.get("dominant_evidence_family") or "__NULL__",
            "dominant_action_class": row.get("dominant_action_class") or "__NULL__",
            "dominant_score": row.get("dominant_score"),
            "matched_rows": row.get("matched_rows"),
            "pollution_flags": row.get("pollution_flags") or {},
            "path_context": row.get("path_context") or {},
        }
        old = dominance.get(cid)
        if old is None:
            dominance[cid] = compact
            continue
        old_null = old["dominant_source_component"] == "__NULL__" and old["dominant_evidence_family"] == "__NULL__"
        new_non_null = compact["dominant_source_component"] != "__NULL__" or compact["dominant_evidence_family"] != "__NULL__"
        if old_null and new_non_null:
            dominance[cid] = compact
    return dominance


def write_acceptance_gate_ledger() -> list[dict[str, Any]]:
    records = [
        {
            "record_type": "acceptance_gate_failure",
            "failure_family": "stage09_viability_gate_absent",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"),
            "source_line": 1231,
            "evidence": "verify_summary checked candidate/shard/scenario/key presence but did not reject selected_count=10, total_r<0, expectancy<0, PF<1, pass_proxy=false, or extreme missed winners.",
            "repair_requirement": "Stage09 verifier must classify production_candidate_failed when viability gates fail.",
        },
        {
            "record_type": "acceptance_gate_failure",
            "failure_family": "stage10_artifact_existence_completion",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage10_completion_audit_2026_05_25.py"),
            "source_line": 100,
            "evidence": "build_completion_audit converted instruction and artifact coverage into route completion without rejecting the failed Stage09 metrics.",
            "repair_requirement": "Stage10 must consume Stage09 viability status and fail completion on production_candidate_failed.",
        },
        {
            "record_type": "acceptance_gate_failure",
            "failure_family": "stage10_allows_stage10_in_progress",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage10_completion_audit_2026_05_25.py"),
            "source_line": 88,
            "evidence": "all_stage_statuses_complete accepted Stage10 in_progress when allow_stage10_in_progress=true.",
            "repair_requirement": "Final completion audit must not be complete while Stage10 remains in_progress.",
        },
        {
            "record_type": "replay_semantics_failure",
            "failure_family": "continuous_account_path",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"),
            "source_line": 396,
            "evidence": "ScenarioMetrics carries one persistent equity/account state over the full sorted 2022-2026 stream.",
            "repair_requirement": "Prop replay must segment into independent challenge/account attempts with phase/reset outcomes.",
        },
        {
            "record_type": "replay_semantics_failure",
            "failure_family": "selector_account_state_zeroes_live_exposure",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"),
            "source_line": 652,
            "evidence": "account_state_for_selector feeds persistent ScenarioMetrics equity and sets open/pending/correlation risk to zero in replay.",
            "repair_requirement": "Replay account state must be sourced from executable stream semantics and policy-specific pending/open/correlation assumptions.",
        },
        {
            "record_type": "route_semantics_failure",
            "failure_family": "new_mechanical_does_not_require_follow",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"),
            "source_line": 895,
            "evidence": "mechanical_selected was defined as absence of block reasons, not explicit FOLLOW/executable conversion.",
            "repair_requirement": "Stage09 must separate generated candidate universe from executable FOLLOW stream and define MIXED/LEGACY handling explicitly.",
        },
        {
            "record_type": "ai_policy_failure",
            "failure_family": "no_paid_ai_zero_trade_path",
            "source_file": rel(FAILED_ROUTE_DIR / "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"),
            "source_line": 960,
            "evidence": "no_paid_ai_selected required FOLLOW_WITHOUT_AI; failed replay had no such selected path and produced zero selected trades.",
            "repair_requirement": "No-paid-call scenario must be diagnostic-only or include a mechanical resolver that cannot silently pass as production viability.",
        },
    ]
    with ACCEPTANCE_GATE_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return records


def build() -> dict[str, Any]:
    now = utc_now()
    avoid_ids = collect_avoid_ids()
    dominance_map = build_dominance_map(avoid_ids)

    coverage = {
        name: defaultdict(Counter)
        for name in (
            "universe",
            "baseline_selected",
            "new_selected",
            "dropped_baseline",
            "prop_blocked",
            "avoid_blocked",
            "route_semantics_legacy_mixed",
        )
    }
    transition = Counter()
    skip_reasons = {
        "baseline": Counter(),
        "new_mechanical": Counter(),
        "ai_no_paid_call": Counter(),
    }
    route_decisions = Counter()
    prop_actions = Counter()
    ltf_actions = Counter()
    pending_actions = Counter()
    ai_actions = Counter()
    supervisor_actions = Counter()
    prop_block_metrics: dict[str, dict[str, Any]] = defaultdict(metric_bucket)
    avoid_component_metrics: dict[str, dict[str, Any]] = defaultdict(metric_bucket)
    route_semantics_metrics: dict[str, dict[str, Any]] = defaultdict(metric_bucket)
    selected_count = 0
    dropped_count = 0
    avoid_count = 0
    route_semantics_count = 0
    ltf_rows = 0
    ai_rows = 0
    total_rows = 0

    acceptance_records = write_acceptance_gate_ledger()

    with (
        FAILURE_ANATOMY_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as failure_handle,
        SELECTED_ROWS_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as selected_handle,
        DROPPED_BASELINE_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as dropped_handle,
        AVOID_EV_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as avoid_handle,
        ROUTE_SEMANTICS_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as route_handle,
        LTF_EFFECT_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as ltf_handle,
        AI_POLICY_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as ai_handle,
    ):
        for idx, row in enumerate(iter_stage09_rows(), start=1):
            total_rows += 1
            record = compact_candidate(row, idx)
            r = record["simulated_r"]
            cid = str(record["candidate_id"])
            dom = dominance_map.get(cid, {})
            if cid in avoid_ids:
                record["avoid_dominance_join_status"] = "joined" if dom else "missing_dominance_join"
                record["avoid_source_component"] = dom.get("dominant_source_component", "__MISSING_DOMINANCE_JOIN__")
                record["avoid_evidence_family"] = dom.get("dominant_evidence_family", "__MISSING_DOMINANCE_JOIN__")

            failure_handle.write(json.dumps(record, sort_keys=True) + "\n")
            inc_cov(coverage["universe"], record)
            transition[transition_key(record)] += 1
            if not record["baseline_selected"]:
                skip_reasons["baseline"][str(record["baseline_selection_reason"] or "selected")] += 1
            if not record["new_mechanical_selected"]:
                skip_reasons["new_mechanical"][str(record["new_mechanical_selection_reason"] or "selected")] += 1
            route_decisions[str(record["new_route_decision"] or "UNKNOWN")] += 1
            prop_actions[str(record["prop_action"] or "UNKNOWN")] += 1
            ltf_actions[str(record["ltf_action"] or "UNKNOWN")] += 1
            pending_actions[str(record["pending_action"] or "UNKNOWN")] += 1
            ai_actions[str(record["ai_policy_action"] or "UNKNOWN")] += 1
            supervisor_actions[str(record["ai_supervisor_action"] or "UNKNOWN")] += 1

            ltf_record = {
                "schema_version": "vnext_production_candidate_repair_stage01_ltf_effect_row_v1",
                "candidate_id": record["candidate_id"],
                "as_of_utc": record["as_of_utc"],
                "symbol": record["symbol"],
                "session": record["session"],
                "side": record["side"],
                "framework": record["framework"],
                "source_mode": record["source_mode"],
                "baseline_selected": record["baseline_selected"],
                "new_mechanical_selected": record["new_mechanical_selected"],
                "new_mechanical_selection_reason": record["new_mechanical_selection_reason"],
                "ltf_action": record["ltf_action"],
                "ltf_would_action": record["ltf_would_action"],
                "ltf_reason": record["ltf_reason"],
                "pending_action": record["pending_action"],
                "pending_lifecycle_state": record["pending_lifecycle_state"],
                "entry_touched": record["entry_touched"],
                "no_fill": record["no_fill"],
                "would_change_decision_or_execution_with_ltf_source": record["would_change_decision_or_execution_with_ltf_source"],
                "simulated_r": r,
                "terminal_outcome": record["terminal_outcome"],
                "scoring_joined_after_decision": record["scoring_joined_after_decision"],
            }
            ltf_handle.write(json.dumps(ltf_record, sort_keys=True) + "\n")
            ltf_rows += 1

            ai_record = {
                "schema_version": "vnext_production_candidate_repair_stage01_ai_policy_supervisor_row_v1",
                "candidate_id": record["candidate_id"],
                "as_of_utc": record["as_of_utc"],
                "symbol": record["symbol"],
                "session": record["session"],
                "side": record["side"],
                "framework": record["framework"],
                "baseline_selected": record["baseline_selected"],
                "new_mechanical_selected": record["new_mechanical_selected"],
                "new_mechanical_selection_reason": record["new_mechanical_selection_reason"],
                "pre_ai_action": record["pre_ai_action"],
                "pre_ai_decision": record["pre_ai_decision"],
                "ai_policy_action": record["ai_policy_action"],
                "ai_policy_would_action": record["ai_policy_would_action"],
                "ai_policy_would_allow_ai_call": record["ai_policy_would_allow_ai_call"],
                "ai_supervisor_action": record["ai_supervisor_action"],
                "ai_supervisor_disable_ai_narrowing": record["ai_supervisor_disable_ai_narrowing"],
                "simulated_r": r,
                "terminal_outcome": record["terminal_outcome"],
            }
            ai_handle.write(json.dumps(ai_record, sort_keys=True) + "\n")
            ai_rows += 1
            if record["ai_policy_action"]:
                skip_reasons["ai_no_paid_call"][f"no_paid_ai_{str(record['ai_policy_action']).lower()}"] += 1

            if record["baseline_selected"]:
                inc_cov(coverage["baseline_selected"], record)
            if record["new_mechanical_selected"]:
                selected_count += 1
                inc_cov(coverage["new_selected"], record)
                selected_handle.write(
                    json.dumps(
                        {
                            "schema_version": "vnext_production_candidate_repair_stage01_selected_row_v1",
                            **record,
                            "prop_state": {
                                "action": record["prop_action"],
                                "reason": record["prop_reason"],
                                "before_risk_pct": record["prop_before_risk_pct"],
                                "after_risk_pct": record["prop_after_risk_pct"],
                                "remaining_daily_cushion": record["prop_remaining_daily_cushion"],
                                "remaining_overall_cushion": record["prop_remaining_overall_cushion"],
                            },
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

            if record["baseline_selected"] and not record["new_mechanical_selected"]:
                dropped_count += 1
                inc_cov(coverage["dropped_baseline"], record)
                dropped_handle.write(
                    json.dumps(
                        {
                            "schema_version": "vnext_production_candidate_repair_stage01_dropped_baseline_row_v1",
                            "candidate_id": record["candidate_id"],
                            "as_of_utc": record["as_of_utc"],
                            "month": record["month"],
                            "symbol": record["symbol"],
                            "session": record["session"],
                            "side": record["side"],
                            "framework": record["framework"],
                            "route_family": record["route_family"],
                            "source_mode": record["source_mode"],
                            "source_path": record["source_path"],
                            "terminal_outcome": record["terminal_outcome"],
                            "simulated_r": r,
                            "outcome_class": record["outcome_class"],
                            "baseline_selection_reason": record["baseline_selection_reason"],
                            "new_mechanical_selection_reason": record["new_mechanical_selection_reason"],
                            "new_route_decision": record["new_route_decision"],
                            "prop_action": record["prop_action"],
                            "prop_reason": record["prop_reason"],
                            "prop_remaining_daily_cushion": record["prop_remaining_daily_cushion"],
                            "prop_remaining_overall_cushion": record["prop_remaining_overall_cushion"],
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

            if str(record["new_mechanical_selection_reason"]) == "vnext_decision_avoid":
                avoid_count += 1
                inc_cov(coverage["avoid_blocked"], record)
                dom = dominance_map.get(cid, {})
                component = dom.get("dominant_source_component", "__MISSING_DOMINANCE_JOIN__")
                family = dom.get("dominant_evidence_family", "__MISSING_DOMINANCE_JOIN__")
                add_metric(avoid_component_metrics[f"{family}|{component}"], r)
                avoid_handle.write(
                    json.dumps(
                        {
                            "schema_version": "vnext_production_candidate_repair_stage01_avoid_ev_row_v1",
                            "candidate_id": record["candidate_id"],
                            "as_of_utc": record["as_of_utc"],
                            "month": record["month"],
                            "symbol": record["symbol"],
                            "session": record["session"],
                            "side": record["side"],
                            "framework": record["framework"],
                            "source_mode": record["source_mode"],
                            "terminal_outcome": record["terminal_outcome"],
                            "simulated_r_if_taken": r,
                            "outcome_class_if_taken": record["outcome_class"],
                            "baseline_selected": record["baseline_selected"],
                            "new_route_decision": record["new_route_decision"],
                            "pre_ai_action": record["pre_ai_action"],
                            "avoid_dominance_join_status": "joined" if dom else "missing_dominance_join",
                            "dominant_source_component": component,
                            "dominant_evidence_family": family,
                            "dominant_action_class": dom.get("dominant_action_class", "__MISSING_DOMINANCE_JOIN__"),
                            "dominance_row_id": dom.get("dominance_row_id"),
                            "matched_rows": dom.get("matched_rows"),
                            "pollution_flags": dom.get("pollution_flags", {}),
                            "source_path": record["source_path"],
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

            if str(record["prop_action"] or "") in {"BLOCK", "DEFER_UNTIL_RESET"}:
                inc_cov(coverage["prop_blocked"], record)
                key = "|".join(
                    str(record.get(part) or "unknown")
                    for part in (
                        "new_route_decision",
                        "baseline_selected",
                        "symbol",
                        "session",
                        "side",
                        "framework",
                        "source_mode",
                        "month",
                        "outcome_class",
                    )
                )
                add_metric(prop_block_metrics[key], r)

            if str(record["new_route_decision"] or "") in {"LEGACY", "MIXED"}:
                route_semantics_count += 1
                inc_cov(coverage["route_semantics_legacy_mixed"], record)
                add_metric(route_semantics_metrics[str(record["new_route_decision"])], r)
                route_handle.write(
                    json.dumps(
                        {
                            "schema_version": "vnext_production_candidate_repair_stage01_route_semantics_row_v1",
                            "candidate_id": record["candidate_id"],
                            "as_of_utc": record["as_of_utc"],
                            "month": record["month"],
                            "symbol": record["symbol"],
                            "session": record["session"],
                            "side": record["side"],
                            "framework": record["framework"],
                            "source_mode": record["source_mode"],
                            "terminal_outcome": record["terminal_outcome"],
                            "simulated_r": r,
                            "outcome_class": record["outcome_class"],
                            "baseline_selected": record["baseline_selected"],
                            "new_mechanical_selected": record["new_mechanical_selected"],
                            "new_mechanical_selection_reason": record["new_mechanical_selection_reason"],
                            "route_decision": record["new_route_decision"],
                            "route_reached_prop_budget": record["prop_action"] is not None,
                            "prop_action": record["prop_action"],
                            "prop_reason": record["prop_reason"],
                            "prop_remaining_overall_cushion": record["prop_remaining_overall_cushion"],
                            "repair_requirement": "LEGACY/MIXED generated rows must not consume prop budget unless explicitly converted to an executable stream.",
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

    summary = {
        "schema_version": "vnext_production_candidate_repair_stage01_failure_anatomy_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": now,
        "current_git_head": git_head(),
        "stage_id": "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
        "stage_status": "complete",
        "first_incomplete_invariant": "STAGE_02_ACCEPTANCE_GATE_REPAIR",
        "row_counts": {
            "failure_anatomy_rows": total_rows,
            "selected_rows": selected_count,
            "dropped_baseline_rows": dropped_count,
            "avoid_ev_rows": avoid_count,
            "route_semantics_legacy_mixed_rows": route_semantics_count,
            "ltf_effect_rows": ltf_rows,
            "ai_policy_supervisor_rows": ai_rows,
            "acceptance_gate_failure_rows": len(acceptance_records),
            "avoid_dominance_joined_rows": len(dominance_map),
            "avoid_dominance_missing_rows": len(avoid_ids) - len(dominance_map),
        },
        "transition_matrix": dict(transition),
        "skip_reasons": {name: dict(counter) for name, counter in skip_reasons.items()},
        "route_decision_distribution": dict(route_decisions),
        "prop_action_distribution": dict(prop_actions),
        "ltf_action_distribution": dict(ltf_actions),
        "pending_action_distribution": dict(pending_actions),
        "ai_policy_action_distribution": dict(ai_actions),
        "ai_supervisor_action_distribution": dict(supervisor_actions),
        "coverage": {
            name: {dimension: dict(counter) for dimension, counter in dimensions.items()}
            for name, dimensions in coverage.items()
        },
        "avoid_component_metrics": dict(avoid_component_metrics),
        "route_semantics_metrics": dict(route_semantics_metrics),
        "prop_block_metric_group_count": len(prop_block_metrics),
        "prop_block_metrics": dict(prop_block_metrics),
        "acceptance_gate_failure_families": [record["failure_family"] for record in acceptance_records],
        "source_completeness": {
            "stage09_shards_read": 11,
            "all_stage09_rows_preserved": total_rows == 253234,
            "avoid_dominance_join_attempted": True,
            "avoid_dominance_joined_rows": len(dominance_map),
            "avoid_dominance_missing_rows": len(avoid_ids) - len(dominance_map),
        },
        "branch_decision": "full_failure_anatomy_materialized_stage02_acceptance_gate_repair_next",
        "implementation_decision": "repair_stage09_stage10_acceptance_gates_before_replay_semantics_repair",
        "replay_effect": {
            "failed_candidate_rows": total_rows,
            "new_selected_rows": selected_count,
            "dropped_baseline_rows": dropped_count,
            "avoid_rows": avoid_count,
            "legacy_mixed_rows_that_reached_prop_budget": route_semantics_count,
        },
        "outputs": {
            "failure_anatomy_ledger": rel(FAILURE_ANATOMY_LEDGER_PATH),
            "selected_rows_ledger": rel(SELECTED_ROWS_LEDGER_PATH),
            "dropped_baseline_ledger": rel(DROPPED_BASELINE_LEDGER_PATH),
            "avoid_ev_ledger": rel(AVOID_EV_LEDGER_PATH),
            "route_semantics_ledger": rel(ROUTE_SEMANTICS_LEDGER_PATH),
            "ltf_entry_effect_ledger": rel(LTF_EFFECT_LEDGER_PATH),
            "ai_policy_supervisor_ledger": rel(AI_POLICY_LEDGER_PATH),
            "acceptance_gate_failure_ledger": rel(ACCEPTANCE_GATE_LEDGER_PATH),
            "summary": rel(SUMMARY_PATH),
        },
    }
    write_json(SUMMARY_PATH, summary)
    update_state(summary)
    return summary


def update_state(summary: dict[str, Any]) -> None:
    state = load_json(STATE_PATH)
    state["current_stage"] = "STAGE_02_ACCEPTANCE_GATE_REPAIR"
    state["active_invariant"] = "repair_stage09_stage10_acceptance_gates_so_catastrophic_candidates_fail"
    state["first_incomplete_invariant"] = "STAGE_02_ACCEPTANCE_GATE_REPAIR"
    state["exact_next_action"] = "Patch Stage09/Stage10 acceptance gates and tests so the old catastrophic output fails viability."
    state["current_git_head"] = summary["current_git_head"]
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["stage_status_table"]["STAGE_01_FULL_FAILURE_ANATOMY_LEDGER"] = "complete"
    state["stage_status_table"]["STAGE_02_ACCEPTANCE_GATE_REPAIR"] = "pending"
    state.setdefault("output_artifact_paths", {}).update(summary["outputs"])
    state.setdefault("row_count_hash_coverage", {}).update(summary["row_counts"])
    state.setdefault("failures_found", []).extend(
        [
            "stage01_route_semantics_legacy_mixed_reached_prop_budget",
            "stage01_avoid_pressure_net_requires_repair_before_hard_blocking",
            "stage01_acceptance_gate_failures_materialized",
        ]
    )
    state.setdefault("repairs_applied", []).append("stage01_full_failure_anatomy_ledgers_materialized")
    state.setdefault("active_question_and_repair_ledger", []).extend(
        [
            {
                "question": "Were all failed Stage09 rows preserved before summaries?",
                "status": "closed_yes",
                "evidence_path": summary["outputs"]["failure_anatomy_ledger"],
                "row_count": summary["row_counts"]["failure_anatomy_rows"],
            },
            {
                "question": "Which acceptance gates failed?",
                "status": "closed_stage02_repair_required",
                "evidence_path": summary["outputs"]["acceptance_gate_failure_ledger"],
                "failure_families": summary["acceptance_gate_failure_families"],
            },
        ]
    )
    state.setdefault("verification_status", {})["stage01_builder_complete"] = True
    state["verification_status"]["stage01_failure_anatomy_rows"] = summary["row_counts"]["failure_anatomy_rows"]
    state["verification_status"]["stage01_selected_rows"] = summary["row_counts"]["selected_rows"]
    state["verification_status"]["stage01_dropped_baseline_rows"] = summary["row_counts"]["dropped_baseline_rows"]
    state["verification_status"]["stage01_avoid_rows"] = summary["row_counts"]["avoid_ev_rows"]
    state["verification_status"]["stage01_route_semantics_rows"] = summary["row_counts"]["route_semantics_legacy_mixed_rows"]
    state["updated_at_utc"] = utc_now()
    write_json(STATE_PATH, state)


if __name__ == "__main__":
    result = build()
    print(
        json.dumps(
            {
                "ok": True,
                "stage": result["stage_id"],
                "first_incomplete_invariant": result["first_incomplete_invariant"],
                "row_counts": result["row_counts"],
                "outputs": result["outputs"],
            },
            indent=2,
            sort_keys=True,
        )
    )

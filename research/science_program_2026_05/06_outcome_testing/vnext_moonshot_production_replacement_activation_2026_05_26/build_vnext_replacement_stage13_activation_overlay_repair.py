from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import yaml

from build_vnext_replacement_stage13_full_market_element_audit import (
    ACTIVATED_FRAMEWORKS,
    ACTIVATED_SELECTOR_NAME,
    kill_zone_bucket as repaired_kill_zone_bucket,
    load_broker_map,
    load_repo_schedules,
)


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_activation_overlay_repair"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

STAGE05_SHARD_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE}.jsonl"
)
STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
STAGE11_OVERLAY = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml"
STAGE12_PRE_REPAIR = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE12_PRE_REPAIR_SEMANTIC_VERIFICATION_RESULT_{DATE}.json"
)
ROUTER_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_{DATE}.jsonl"
FEATURE_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE}.jsonl"
CONDITION_MAP = (
    MOONSHOT_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json"
)

OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_REPAIRED_ACTIVATION_OVERLAY_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_REPAIRED_ACTIVATION_OVERLAY_SUMMARY_{DATE}.json"
OUTPUT_FAILURE_ENUMERATION = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_REPAIR_FAILURE_ENUMERATION_{DATE}.json"
)
FULL_MARKET_AUDIT_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_SUMMARY_{DATE}.json"
)
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def fnum(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class Stats:
    count: int = 0
    total_r: float = 0.0
    wins: int = 0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0

    def add(self, value: Any) -> None:
        number = fnum(value)
        if number is None:
            return
        self.count += 1
        self.total_r += number
        if number > 0:
            self.wins += 1
            self.gross_win_r += number
        elif number < 0:
            self.gross_loss_r += abs(number)

    def record(self) -> dict[str, Any]:
        return {
            "selected_count": self.count,
            "performance_count": self.count,
            "total_r": self.total_r,
            "expectancy_r": self.total_r / self.count if self.count else None,
            "win_rate": self.wins / self.count if self.count else None,
            "profit_factor": self.gross_win_r / self.gross_loss_r if self.gross_loss_r else None,
            "wins": self.wins,
            "gross_win_r": self.gross_win_r,
            "gross_loss_r": self.gross_loss_r,
        }


@dataclass
class RepairScan:
    candidate_rows_scanned: int = 0
    dynamic_rows_scanned: int = 0
    repaired_selected_rows: int = 0
    legacy_toxic_selected_rows: int = 0
    filter_counts: Counter[str] = field(default_factory=Counter)
    legacy_toxic_label_counts: Counter[str] = field(default_factory=Counter)
    repaired_symbol_counts: Counter[str] = field(default_factory=Counter)
    repaired_session_counts: Counter[str] = field(default_factory=Counter)
    repaired_kill_zone_position_counts: Counter[str] = field(default_factory=Counter)
    repaired_source_window_counts: Counter[str] = field(default_factory=Counter)
    repaired_source_quality_counts: Counter[str] = field(default_factory=Counter)
    repaired_branch_label_counts: Counter[str] = field(default_factory=Counter)
    market_filter_counts: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    scenario_stats: dict[str, Stats] = field(
        default_factory=lambda: {
            "old_gtos_live_current_j46_j49": Stats(),
            "fixed_1_5r": Stats(),
            "j46_j49": Stats(),
            "be_after_trigger_repaired_overlay": Stats(),
            "condition_router": Stats(),
            "no_overlay_current_live": Stats(),
        }
    )


def load_feature_map() -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(FEATURE_LEDGER):
        feature = row.get("feature_columns") or {}
        same_bar_map = row.get("label_policy_same_bar_by_policy") or {}
        features[str(row.get("candidate_id"))] = {
            "kill_zone_position": feature.get("kill_zone_position"),
            "selected_policy_same_bar_ambiguous": bool(same_bar_map.get("be_after_trigger")),
            "any_policy_same_bar_ambiguous": any(bool(value) for value in same_bar_map.values()),
            "source_window_complete": feature.get("source_window_complete"),
        }
    return features


def load_router_map() -> dict[str, dict[str, Any]]:
    routers: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(ROUTER_LEDGER):
        decision = row.get("router_decision") or {}
        dimensions = decision.get("route_dimensions") or {}
        routers[str(row.get("candidate_id"))] = {
            "selected_policy": decision.get("selected_policy"),
            "candidate_action": decision.get("candidate_action"),
            "decision_status": decision.get("decision_status"),
            "prop_action": decision.get("prop_action"),
            "source_quality_action": decision.get("source_quality_action"),
            "refusal_reasons": decision.get("refusal_reasons") or [],
            "kill_zone_position": row.get("kill_zone_position")
            or dimensions.get("kill_zone_position"),
            "selected_policy_ordered_path_status": row.get("selected_policy_ordered_path_status")
            or dimensions.get("selected_policy_ordered_path_status"),
            "selected_policy_same_bar_ambiguous": row.get(
                "selected_policy_same_bar_ambiguity_observed_in_replay"
            )
            if "selected_policy_same_bar_ambiguity_observed_in_replay" in row
            else dimensions.get("selected_policy_same_bar_ambiguous"),
        }
    return routers


def policy_value(row: dict[str, Any], policy: str) -> float | None:
    policies = ((row.get("dynamic_policy_replay") or {}).get("policy_results") or {})
    return fnum((policies.get(policy) or {}).get("final_r"))


def route_decision(row: dict[str, Any]) -> str | None:
    runtime = row.get("runtime_reference") or {}
    hyp = runtime.get("hypothetical_activated_vnext") or {}
    return hyp.get("route_decision")


def repair_exclusion_reasons(
    row: dict[str, Any],
    *,
    eligible_symbols: set[str],
    feature: dict[str, Any],
    router: dict[str, Any],
    repaired_kill_zone_position: str,
) -> list[str]:
    reasons: list[str] = []
    if (row.get("dynamic_policy_replay") or {}).get("available") is not True:
        reasons.append("dynamic_policy_replay_unavailable")
    if row.get("symbol") not in eligible_symbols:
        reasons.append("broker_native_contract_not_verified")
    if row.get("framework") not in ACTIVATED_FRAMEWORKS:
        reasons.append("framework_not_in_full_market_activated_set")
    if not str(repaired_kill_zone_position or "").startswith("in_"):
        reasons.append("outside_configured_kill_zone_or_missing_schedule")
    if route_decision(row) != "FOLLOW":
        reasons.append("branch_label_not_follow")
    if router.get("selected_policy") != "be_after_trigger":
        reasons.append("selected_policy_not_be_after_trigger")
    if bool(router.get("selected_policy_same_bar_ambiguous")):
        reasons.append("selected_policy_same_bar_ambiguous")
    if router.get("prop_action") != "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS":
        reasons.append("prop_action_not_allow")
    hard_refusals = [
        str(reason)
        for reason in router.get("refusal_reasons", [])
        if reason
        and reason
        not in {
            "source_window_incomplete_forward_capture_required",
        }
    ]
    if hard_refusals:
        reasons.append("router_hard_refusal:" + ",".join(sorted(hard_refusals)))
    if policy_value(row, "be_after_trigger") is None:
        reasons.append("selected_policy_r_missing")
    return reasons


def write_overlay_yaml(summary: dict[str, Any]) -> None:
    overlay = yaml.safe_load(STAGE11_OVERLAY.read_text(encoding="utf-8")) or {}
    repaired = summary["repaired_overlay_metrics"]["be_after_trigger_repaired_overlay"]
    comparator = summary["comparator_metrics"]
    selected = overlay.setdefault("selected_replacement", {})
    selected["repaired_activation_selected_rows"] = repaired["selected_count"]
    selected["repaired_activation_expectancy_r"] = repaired["expectancy_r"]
    selected["repaired_activation_total_r"] = repaired["total_r"]
    selected["repaired_activation_profit_factor"] = repaired["profit_factor"]
    selected["repaired_activation_win_rate"] = repaired["win_rate"]
    selected["repaired_condition_challenger_expectancy_r"] = comparator[
        "condition_router"
    ]["expectancy_r"]
    selected["condition_challenger_raw_subset_status"] = (
        "higher_raw_expectancy_but_not_prop_default; Stage11 prop-aware replay retains BE "
        "because ACCOUNT_ABANDON_OR_RESTART comparison has higher EV per terminal day and "
        "more accepted trades"
    )

    guardrails = overlay.setdefault("input_guardrails", {})
    guardrails["stage13_activation_repair_summary"] = rel(OUTPUT_SUMMARY)
    guardrails["stage13_activation_repair_ledger"] = rel(OUTPUT_LEDGER)
    guardrails["stage13_failure_enumeration"] = rel(OUTPUT_FAILURE_ENUMERATION)
    guardrails["repaired_production_activation_overlay_selected_count"] = repaired[
        "selected_count"
    ]
    guardrails["repaired_production_activation_overlay_expectancy_r"] = repaired[
        "expectancy_r"
    ]
    guardrails["repaired_production_activation_overlay_total_r"] = repaired["total_r"]
    guardrails["repaired_production_activation_overlay_profit_factor"] = repaired[
        "profit_factor"
    ]
    guardrails["repaired_production_activation_overlay_win_rate"] = repaired["win_rate"]
    guardrails["repaired_overlay_beats_old_gtos"] = repaired["expectancy_r"] > comparator[
        "old_gtos_live_current_j46_j49"
    ]["expectancy_r"]
    guardrails["repaired_overlay_beats_fixed_1_5r"] = repaired["expectancy_r"] > comparator[
        "fixed_1_5r"
    ]["expectancy_r"]
    guardrails["repaired_overlay_source_incomplete_rows_with_capture_monitoring"] = summary[
        "source_capture_monitoring"
    ]["selected_source_window_incomplete_rows"]

    candidate = overlay["semantic_gated_production_activation_overlay_candidate"]["config"][
        "gtos_vnext_runtime"
    ]
    candidate["moonshot_dynamic_execution_router_ordered_path_scope"] = "selected_policy"
    candidate["moonshot_dynamic_execution_router_source_window_complete_blocks_activation"] = False
    candidate["moonshot_dynamic_execution_router_require_configured_kill_zone"] = True
    candidate["moonshot_dynamic_execution_router_activated_frameworks"] = list(
        ACTIVATED_FRAMEWORKS
    )
    candidate["moonshot_dynamic_execution_router_repaired_overlay_selector"] = (
        ACTIVATED_SELECTOR_NAME
    )
    candidate["moonshot_dynamic_execution_router_stage13_repair_summary_path"] = rel(
        OUTPUT_SUMMARY
    )
    overlay["semantic_gated_production_activation_overlay_candidate"]["must_fail_if"] = [
        "repaired_production_activation_overlay_expectancy_r_below_zero",
        "repaired_production_activation_overlay_expectancy_r_below_old_gtos_without_positive_ev_proof",
        "branch_label_not_follow_receives_execution_effect",
        "selected_policy_same_bar_ambiguous_rows_receive_execution_effect",
        "outside_configured_kill_zone_or_broker_unavailable_rows_receive_execution_effect",
        "source_completeness_used_as_trade_selection_proxy",
        "prop_safe_selector_apply_to_execution_false",
        "ltf_path_execution_apply_to_execution_false",
        "monitoring_log_absent_or_missing_required_surfaces",
        "ml_apply_to_execution_true_without_sealed_validation",
    ]
    overlay["application_state"]["reason"] = (
        "Stage13 repaired the activation selector mechanically. The production overlay now "
        "maps to the row-level repaired all-framework/FOLLOW/broker-native/repaired-configured-KZ/"
        "selected-policy BE-after-trigger slice rather than the toxic source-bound default-primary "
        "or narrow FVG-only slice."
    )
    overlay["stage13_activation_repair"] = {
        "summary_path": rel(OUTPUT_SUMMARY),
        "ledger_path": rel(OUTPUT_LEDGER),
        "failure_enumeration_path": rel(OUTPUT_FAILURE_ENUMERATION),
        "repaired_overlay_metrics": repaired,
        "source_completeness_rule": (
            "source_window_complete is capture-readiness evidence, not a trade-selection rule; "
            "selected source-incomplete rows retain source-capture monitoring fields"
        ),
        "activated_frameworks": list(ACTIVATED_FRAMEWORKS),
        "full_market_element_audit_summary": rel(FULL_MARKET_AUDIT_SUMMARY),
        "branch_semantics_rule": "Only FOLLOW rows can receive execution effect; AVOID/MIXED/LEGACY remain inert.",
    }
    STAGE11_OVERLAY.write_text(
        yaml.safe_dump(overlay, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
        newline="\n",
    )


def update_state_and_manifest(summary: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    for path in (OUTPUT_SUMMARY, OUTPUT_LEDGER, OUTPUT_FAILURE_ENUMERATION, Path(__file__)):
        entry = {"path": path.name, "stage": "stage_13", "status": "created"}
        if path == OUTPUT_LEDGER:
            entry["rows"] = summary["repaired_overlay_metrics"][
                "be_after_trigger_repaired_overlay"
            ]["selected_count"]
        for index, existing in enumerate(outputs):
            if isinstance(existing, dict) and existing.get("path") == entry["path"]:
                outputs[index] = entry
                break
        else:
            outputs.append(entry)
    manifest["last_updated_utc"] = generated_at
    manifest["stage13_activation_repair_status"] = "completed_repaired_overlay_replay_written"
    write_json(OUTPUT_MANIFEST, manifest)

    state = read_json(OUTPUT_STATE)
    state["last_updated_utc"] = generated_at
    state["current_stage"] = "stage_12_semantic_verification_and_red_team"
    state["first_incomplete_invariant"] = (
        "stage_12_semantic_verifier_rerun_pending_after_stage13_activation_repair"
    )
    state["exact_next_action"] = (
        "Rerun Stage12 semantic verifier against the repaired Stage13 activation overlay evidence."
    )
    state.setdefault("stage_status", {})[
        "stage_13_commit_and_activation_config_application"
    ] = "activation_overlay_repair_completed_pending_stage12_rerun"
    rows = state.setdefault("evidence_rows_scanned", {})
    rows["stage13_repair_candidate_rows_scanned"] = summary["candidate_rows_scanned"]
    rows["stage13_repair_dynamic_rows_scanned"] = summary["dynamic_rows_scanned"]
    rows["stage13_repair_selected_rows"] = summary["repaired_overlay_metrics"][
        "be_after_trigger_repaired_overlay"
    ]["selected_count"]
    state.setdefault("tests_verifiers_run", []).append(
        {
            "command": rel(Path(__file__)),
            "result": "passed; wrote repaired Stage13 activation overlay replay and overlay evidence",
            "timestamp_utc": generated_at,
        }
    )
    write_json(OUTPUT_STATE, state)

    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage13_activation_overlay_repair_replay_written",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": "completed_repaired_overlay_replay_written",
            "selected_rows": summary["repaired_overlay_metrics"][
                "be_after_trigger_repaired_overlay"
            ]["selected_count"],
            "expectancy_r": summary["repaired_overlay_metrics"][
                "be_after_trigger_repaired_overlay"
            ]["expectancy_r"],
            "first_incomplete_invariant_after_stage": state["first_incomplete_invariant"],
        },
    )


def main() -> None:
    generated_at = utc_now()
    stage05_summary = read_json(STAGE05_SUMMARY)
    stage06 = read_json(STAGE06_VERIFIER)
    stage08 = read_json(STAGE08_MAP)
    condition_map = read_json(CONDITION_MAP)
    pre_repair = read_json(STAGE12_PRE_REPAIR)
    eligible_symbols = set(stage08["broker_native_activation_eligible_symbols"])
    exact_excluded_symbols = set(stage08.get("broker_native_exact_excluded_symbols", []))
    features = load_feature_map()
    routers = load_router_map()
    broker_map = load_broker_map()
    repo_schedules = load_repo_schedules()
    scan = RepairScan()

    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as output:
        for manifest_row in iter_jsonl(STAGE05_SHARD_MANIFEST):
            shard_path = REPO_ROOT / manifest_row["output_chunk_path"]
            for row in iter_gzip_jsonl(shard_path):
                scan.candidate_rows_scanned += 1
                if (row.get("dynamic_policy_replay") or {}).get("available") is True:
                    scan.dynamic_rows_scanned += 1
                candidate_id = str(row.get("candidate_id"))
                feature = features.get(candidate_id, {})
                router = routers.get(candidate_id, {})
                broker_info = broker_map.get(str(row.get("symbol")), {})
                repaired_kill_zone_position, schedule_evidence_class = repaired_kill_zone_bucket(
                    symbol=str(row.get("symbol")),
                    row=row,
                    feature=feature,
                    schedules=repo_schedules,
                    broker_session_hours_status=str(
                        broker_info.get("session_hours_status")
                        or "missing_session_hours_status"
                    ),
                )
                if (row.get("activated_default_router_projection") or {}).get(
                    "activated_runtime_effect_would_apply"
                ):
                    scan.legacy_toxic_selected_rows += 1
                    scan.legacy_toxic_label_counts[str(route_decision(row))] += 1
                reasons = repair_exclusion_reasons(
                    row,
                    eligible_symbols=eligible_symbols,
                    feature=feature,
                    router=router,
                    repaired_kill_zone_position=repaired_kill_zone_position,
                )
                primary_reason = reasons[0] if reasons else "repaired_overlay_selected"
                scan.filter_counts[primary_reason] += 1
                scan.market_filter_counts[str(row.get("symbol"))][primary_reason] += 1
                if reasons:
                    continue

                old_r = policy_value(row, "live_current_j46_j49")
                fixed_r = policy_value(row, "legacy_fixed_1.5r")
                be_r = policy_value(row, "be_after_trigger")
                condition_r = fnum(
                    (row.get("condition_router_projection") or {}).get(
                        "selected_policy_final_r"
                    )
                )
                scan.repaired_selected_rows += 1
                scan.scenario_stats["old_gtos_live_current_j46_j49"].add(old_r)
                scan.scenario_stats["fixed_1_5r"].add(fixed_r)
                scan.scenario_stats["j46_j49"].add(old_r)
                scan.scenario_stats["be_after_trigger_repaired_overlay"].add(be_r)
                scan.scenario_stats["condition_router"].add(condition_r)
                scan.scenario_stats["no_overlay_current_live"].add(old_r)
                symbol = str(row.get("symbol"))
                session = str(row.get("session_bucket"))
                kill_zone_position = str(repaired_kill_zone_position)
                source_window_complete = row.get("source_window_complete")
                scan.repaired_symbol_counts[symbol] += 1
                scan.repaired_session_counts[session] += 1
                scan.repaired_kill_zone_position_counts[kill_zone_position] += 1
                scan.repaired_source_window_counts[str(source_window_complete)] += 1
                scan.repaired_source_quality_counts[str(router.get("source_quality_action"))] += 1
                scan.repaired_branch_label_counts[str(route_decision(row))] += 1
                output.write(
                    json.dumps(
                        {
                            "route_id": ROUTE_ID,
                            "stage_id": STAGE_ID,
                            "schema_version": "vnext_replacement_stage13_repaired_activation_overlay_row_v1",
                            "candidate_id": candidate_id,
                            "symbol": symbol,
                            "side": row.get("side"),
                            "framework": row.get("framework"),
                            "session_bucket": session,
                            "kill_zone_position": kill_zone_position,
                            "schedule_evidence_class": schedule_evidence_class,
                            "candle_time_utc": row.get("candle_time_utc"),
                            "branch_label": route_decision(row),
                            "source_window_complete": source_window_complete,
                            "source_quality_action": router.get("source_quality_action"),
                            "selected_policy": router.get("selected_policy"),
                            "old_gtos_live_current_j46_j49_r": old_r,
                            "fixed_1_5r_r": fixed_r,
                            "j46_j49_r": old_r,
                            "be_after_trigger_repaired_overlay_r": be_r,
                            "condition_router_r": condition_r,
                            "no_overlay_current_live_r": old_r,
                            "delta_repaired_vs_old_gtos_r": (
                                be_r - old_r if be_r is not None and old_r is not None else None
                            ),
                            "delta_repaired_vs_fixed_1_5r_r": (
                                be_r - fixed_r
                                if be_r is not None and fixed_r is not None
                                else None
                            ),
                            "repaired_activation_selector": (
                                ACTIVATED_SELECTOR_NAME
                            ),
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

    repaired_metrics = {
        name: stats.record() for name, stats in sorted(scan.scenario_stats.items())
    }
    selected_metrics = repaired_metrics["be_after_trigger_repaired_overlay"]
    comparator_metrics = {
        name: metrics
        for name, metrics in repaired_metrics.items()
        if name != "be_after_trigger_repaired_overlay"
    }
    prop_terminal = condition_map["prop_aware_terminal_decision"]
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage13_activation_overlay_repair_summary_v1",
        "generated_at_utc": generated_at,
        "candidate_rows_scanned": scan.candidate_rows_scanned,
        "dynamic_rows_scanned": scan.dynamic_rows_scanned,
        "no_top_n_or_lossy_summary": True,
        "input_artifacts": {
            "stage05_shard_manifest": rel(STAGE05_SHARD_MANIFEST),
            "stage05_summary": rel(STAGE05_SUMMARY),
            "stage06_verifier": rel(STAGE06_VERIFIER),
            "stage08_market_map": rel(STAGE08_MAP),
            "stage12_pre_repair_result": rel(STAGE12_PRE_REPAIR),
            "router_ledger_after_patch": rel(ROUTER_LEDGER),
            "feature_ledger": rel(FEATURE_LEDGER),
        },
        "selector_contract": {
            "primary_frameworks": list(ACTIVATED_FRAMEWORKS),
            "branch_label_required": "FOLLOW",
            "broker_native_symbols_allowed": sorted(eligible_symbols),
            "broker_exact_excluded_symbols": sorted(exact_excluded_symbols),
            "configured_or_repo_repaired_kill_zone_required": True,
            "full_market_element_audit_summary": rel(FULL_MARKET_AUDIT_SUMMARY),
            "selected_policy": "be_after_trigger",
            "selected_policy_same_bar_ambiguous_allowed": False,
            "source_window_complete_required_for_selection": False,
            "source_window_rule": "source completeness is evidence/capture quality, not trade selection proxy",
            "prop_action_required": "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS",
        },
        "filter_funnel_counts": dict(sorted(scan.filter_counts.items())),
        "market_filter_counts": {
            symbol: dict(sorted(counter.items()))
            for symbol, counter in sorted(scan.market_filter_counts.items())
        },
        "legacy_toxic_pre_repair_activation": {
            "stage12_pre_repair_artifact": rel(STAGE12_PRE_REPAIR),
            "selected_rows": scan.legacy_toxic_selected_rows,
            "branch_label_counts": dict(sorted(scan.legacy_toxic_label_counts.items())),
            "expectancy_r": pre_repair["same_evidence_class_repair_pursuit"]["delta_scan"][
                "r_stats"
            ]["activated_default_source_bound_primary"]["expectancy_r"],
            "profit_factor": pre_repair["same_evidence_class_repair_pursuit"]["delta_scan"][
                "r_stats"
            ]["activated_default_source_bound_primary"]["profit_factor"],
            "win_rate": pre_repair["same_evidence_class_repair_pursuit"]["delta_scan"][
                "r_stats"
            ]["activated_default_source_bound_primary"]["win_rate"],
            "total_r": pre_repair["same_evidence_class_repair_pursuit"]["delta_scan"][
                "r_stats"
            ]["activated_default_source_bound_primary"]["total_r"],
            "mechanism": (
                "Stage12 selected TRADE_DEFAULT_OFF_PRIMARY_CANDIDATE rows as if that label "
                "were production executable, allowing AVOID/MIXED/LEGACY branch labels and "
                "source-complete/default-ready artifacts to define the overlay slice."
            ),
        },
        "repaired_overlay_metrics": {
            "be_after_trigger_repaired_overlay": selected_metrics
        },
        "comparator_metrics": comparator_metrics,
        "condition_router_prop_default_decision": prop_terminal,
        "coverage": {
            "selected_symbol_counts": dict(sorted(scan.repaired_symbol_counts.items())),
            "selected_session_counts": dict(sorted(scan.repaired_session_counts.items())),
            "selected_kill_zone_position_counts": dict(
                sorted(scan.repaired_kill_zone_position_counts.items())
            ),
            "selected_branch_label_counts": dict(sorted(scan.repaired_branch_label_counts.items())),
        },
        "source_capture_monitoring": {
            "selected_source_window_counts": dict(sorted(scan.repaired_source_window_counts.items())),
            "selected_source_window_incomplete_rows": scan.repaired_source_window_counts.get(
                "False", 0
            ),
            "selected_source_quality_action_counts": dict(
                sorted(scan.repaired_source_quality_counts.items())
            ),
            "forward_capture_requirement_rows_from_stage08": stage08["capture_requirement_rows"],
        },
        "comparison_verdict": {
            "beats_old_gtos": selected_metrics["expectancy_r"]
            > comparator_metrics["old_gtos_live_current_j46_j49"]["expectancy_r"],
            "beats_fixed_1_5r": selected_metrics["expectancy_r"]
            > comparator_metrics["fixed_1_5r"]["expectancy_r"],
            "beats_j46_j49": selected_metrics["expectancy_r"]
            > comparator_metrics["j46_j49"]["expectancy_r"],
            "beats_be_all_replayable_from_stage05": selected_metrics["expectancy_r"]
            > stage05_summary["coverage"]["scenario_expectancy_r"][
                "moonshot_be_after_trigger_all_replayable"
            ],
            "condition_router_raw_subset_expectancy_higher": comparator_metrics[
                "condition_router"
            ]["expectancy_r"]
            > selected_metrics["expectancy_r"],
            "condition_router_not_primary_prop_default_reason": prop_terminal[
                "terminal_classification"
            ],
        },
        "output_paths": {
            "ledger": rel(OUTPUT_LEDGER),
            "summary": rel(OUTPUT_SUMMARY),
            "failure_enumeration": rel(OUTPUT_FAILURE_ENUMERATION),
        },
    }

    failing_checks = [
        row
        for row in pre_repair["semantic_gate_results"]
        if row["status"] in {"failed_activation_blocker", "blocked_pending_semantic_repair"}
    ]
    enumeration = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage13_activation_repair_failure_enumeration_v1",
        "generated_at_utc": generated_at,
        "pre_repair_stage12_artifact": rel(STAGE12_PRE_REPAIR),
        "failing_stage12_semantic_gates": [
            {
                "failure_class": row["failure_class"],
                "verifier_assertion": row["decision"],
                "status": row["status"],
                "artifact_path": rel(STAGE12_PRE_REPAIR),
                "code_or_config_paths": [
                    "src/research/moonshot_default_off_policy_router.py",
                    "src/components/gtos_vnext_runtime.py",
                    "src/components/orchestrator.py",
                    rel(STAGE11_OVERLAY),
                    rel(STAGE05_SUMMARY),
                    rel(STAGE06_VERIFIER),
                ],
                "affected_row_counts": {
                    "pre_repair_activated_selected_rows": scan.legacy_toxic_selected_rows,
                    "pre_repair_branch_label_counts": dict(
                        sorted(scan.legacy_toxic_label_counts.items())
                    ),
                    "repaired_selected_rows": selected_metrics["selected_count"],
                    "repaired_source_incomplete_rows_with_capture_monitoring": summary[
                        "source_capture_monitoring"
                    ]["selected_source_window_incomplete_rows"],
                },
                "affected_markets_sessions_branches_source_modes": {
                    "repaired_symbol_counts": summary["coverage"]["selected_symbol_counts"],
                    "repaired_session_counts": summary["coverage"]["selected_session_counts"],
                    "repaired_branch_label_counts": summary["coverage"][
                        "selected_branch_label_counts"
                    ],
                    "repaired_source_window_counts": summary["source_capture_monitoring"][
                        "selected_source_window_counts"
                    ],
                },
                "expectancy_pf_wr_delta_impact": {
                    "pre_repair_toxic": summary["legacy_toxic_pre_repair_activation"],
                    "repaired_overlay": selected_metrics,
                    "old_gtos_on_repaired_slice": comparator_metrics[
                        "old_gtos_live_current_j46_j49"
                    ],
                    "fixed_1_5r_on_repaired_slice": comparator_metrics["fixed_1_5r"],
                    "condition_router_on_repaired_slice": comparator_metrics[
                        "condition_router"
                    ],
                },
                "precise_mechanism": summary["legacy_toxic_pre_repair_activation"]["mechanism"],
                "repair_applied": summary["selector_contract"],
            }
            for row in failing_checks
        ],
    }

    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_FAILURE_ENUMERATION, enumeration)
    write_overlay_yaml(summary)
    update_state_and_manifest(summary, generated_at)
    print(
        json.dumps(
            {
                "status": "completed_repaired_overlay_replay_written",
                "selected_rows": selected_metrics["selected_count"],
                "expectancy_r": selected_metrics["expectancy_r"],
                "profit_factor": selected_metrics["profit_factor"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

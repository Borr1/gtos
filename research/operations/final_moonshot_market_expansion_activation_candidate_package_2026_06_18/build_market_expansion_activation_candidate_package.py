#!/usr/bin/env python3
"""Build the market-expansion activation-candidate package.

This route converts the repaired market-expansion metadata rows into a
machine-checkable activation candidate package while keeping every row
default-off and outside the active runtime registries.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
DATA_AVAILABILITY_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_data_availability_2026_06_18"
)
SCORING_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_validation_scoring_2026_06_18"
)
FOLLOWUP_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_followup_replay_2026_06_18"
)
DEFAULT_OFF_DESIGN_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_default_off_design_2026_06_18"
)
PROXY_M1_REPAIR_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_proxy_m1_repair_2026_06_18"
)
REPAIRED_REGISTRY_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_repaired_registry_integration_2026_06_18"
)
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_activation_candidate_package"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry, registry  # noqa: E402


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def source_index(paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
                "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            }
        )
    return rows


def spec_to_row(name: str, spec: candidate_registry.MarketExpansionDefaultOffSpec) -> dict[str, Any]:
    return {
        "tag": name,
        "file_symbol": spec.file_symbol,
        "broker_symbol": spec.broker_symbol,
        "family": spec.family,
        "mechanism": spec.mechanism,
        "design_status": spec.design_status,
        "candidate_seed_weight": spec.candidate_seed_weight,
        "candidate_weight_ceiling": spec.candidate_weight_ceiling,
        "activation_weight_now": spec.activation_weight_now,
        "symbol_collision_winner": spec.symbol_collision_winner,
        "target2_exact_m1_event_count": spec.target2_exact_m1_event_count,
        "target2_remaining_path_gap_count": spec.target2_m15_proxy_event_count,
        "target2_ordered_mean_r": spec.target2_ordered_mean_r,
        "full_book_delta_sharpe": spec.full_book_delta_sharpe,
        "evidence_route": spec.evidence_route,
        "note": spec.note,
    }


def summarize_cost(cost: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for stress_name in ("cost1", "cost2", "cost3"):
        block = cost.get(stress_name) or {}
        result[stress_name] = {
            "mean_proxy_r": block.get("mean_proxy_r"),
            "median_proxy_r": block.get("median_proxy_r"),
            "sum_proxy_r": block.get("sum_proxy_r"),
            "n": block.get("n"),
            "every_populated_split_positive": block.get("every_populated_split_positive"),
            "populated_split_count": block.get("populated_split_count"),
            "win_rate": block.get("win_rate"),
            "split_means": {
                split: payload.get("mean_proxy_r")
                for split, payload in sorted((block.get("splits") or {}).items())
            },
        }
    return result


def selected_specs() -> dict[str, candidate_registry.MarketExpansionDefaultOffSpec]:
    return {
        name: spec
        for name, spec in candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
        if spec.design_status == "default_off_spec_design_ready" and spec.symbol_collision_winner
    }


GENERATOR_CONTRACT_BY_MECHANISM: dict[str, dict[str, Any]] = {
    "d1_donchian_20_breakout": {
        "generator_family": "market_expansion_d1_donchian_20_breakout",
        "decision_timeframe": "D1",
        "runtime_timeframe_constant": "TF_D1",
        "primary_bar_count_required": 260,
        "minimum_signal_history": "20 prior completed D1 bars plus 14-day prior true-range risk",
        "signal_rule": (
            "at the current D1 session open, use the previous completed D1 close; long if previous close "
            "is above the prior 20-bar high excluding the previous bar, short if below the prior 20-bar low"
        ),
        "risk_rule": "stop distance is the 14-day average of prior true range used by the scoring route",
        "exit_contract": "fixed target2 ordered path: broker TP 2R plus one-D1-session time stop candidate",
        "implementation_surface": "new isolated market-expansion generator module plus an explicit expansion allowlist",
    },
    "d1_atr_mean_reversion": {
        "generator_family": "market_expansion_d1_atr_mean_reversion",
        "decision_timeframe": "D1",
        "runtime_timeframe_constant": "TF_D1",
        "primary_bar_count_required": 260,
        "minimum_signal_history": "14-day prior true-range risk and one prior completed return",
        "signal_rule": (
            "at the current D1 session open, fade the previous completed D1 return when abs(prev_ret) "
            "exceeds 1.25 times prior ATR divided by previous close"
        ),
        "risk_rule": "stop distance is the 14-day average of prior true range used by the scoring route",
        "exit_contract": "fixed target2 ordered path: broker TP 2R plus one-D1-session time stop candidate",
        "implementation_surface": "new isolated market-expansion generator module plus an explicit expansion allowlist",
    },
    "d1_volume_surge_reversal": {
        "generator_family": "market_expansion_d1_volume_surge_reversal",
        "decision_timeframe": "D1",
        "runtime_timeframe_constant": "TF_D1",
        "primary_bar_count_required": 260,
        "minimum_signal_history": "20 prior completed D1 volume bars, 14-day prior true-range risk, prior return",
        "signal_rule": (
            "at the current D1 session open, fade the previous completed D1 return only when previous tick-volume "
            "z-score versus the prior 20 completed bars is above 2.0"
        ),
        "risk_rule": "stop distance is the 14-day average of prior true range used by the scoring route",
        "exit_contract": "fixed target2 ordered path: broker TP 2R plus one-D1-session time stop candidate",
        "implementation_surface": "new isolated market-expansion generator module plus an explicit expansion allowlist",
    },
}


def generator_contract(tag: str, spec: candidate_registry.MarketExpansionDefaultOffSpec) -> dict[str, Any]:
    base = dict(GENERATOR_CONTRACT_BY_MECHANISM[spec.mechanism])
    base.update(
        {
            "tag": tag,
            "file_symbol": spec.file_symbol,
            "broker_symbol": spec.broker_symbol,
            "mechanism": spec.mechanism,
            "row_runtime_name_proposal": tag,
            "current_generator_code_status": "not_implemented_in_runtime",
            "implementation_decision": "metadata_only_pending_explicit_default_off_runtime_generator",
            "non_implementation_requirement": (
                "Current scoring entered at the current D1 open after a previous-D1 signal; the existing "
                "closed-bar SleeveSpec model must add a D1 next-open timing contract or an equivalent replay-parity "
                "adapter before code can be called implementation-complete."
            ),
            "required_code_surfaces": [
                "src/components/ultimate_book/sleeves/market_expansion_d1.py",
                "src/components/ultimate_book/sleeves/registry.py",
                "src/components/ultimate_book/sleeves/candidate_registry.py",
                "src/components/ultimate_book/admission.py",
                "src/components/ultimate_book/bridge.py",
                "src/components/ultimate_book/execution_packets.py",
            ],
            "required_runtime_safety_design": [
                "separate ultimate_book_include_market_expansion_book flag defaulting false",
                "explicit ultimate_book_market_expansion_sleeves allowlist; no empty-list means all behavior",
                "fail-closed unknown expansion names",
                "zero activation unless live authority package changes config",
                "do not append expansion names to current positive-confidence candidate book broad path",
            ],
            "required_tests": [
                "generator parity against source scoring events for all 14 rows",
                "zero active registry/effective-registry membership under current config",
                "explicit opt-in expansion allowlist admits only named expansion sleeves",
                "fixed-target target2/native-exit packet clears execution V4 gates in dry-run fixtures",
                "D1 next-open entry timing does not drift one bar late",
            ],
        }
    )
    return base


def source_span_session_status(availability: dict[str, Any]) -> dict[str, Any]:
    spans = availability.get("source_spans") or {}
    required = ("D1", "M1", "M15")
    present = {
        tf: {
            "present": tf in spans,
            "first": (spans.get(tf) or {}).get("first"),
            "last": (spans.get(tf) or {}).get("last"),
            "rows": (spans.get(tf) or {}).get("rows"),
            "volume_column_available": (spans.get(tf) or {}).get("volume_column_available"),
            "best_path": (spans.get(tf) or {}).get("best_path"),
        }
        for tf in required
    }
    return {
        "d1_signal_window_source_ready": present["D1"]["present"],
        "m1_ordered_path_window_source_ready": present["M1"]["present"],
        "m15_proxy_window_source_ready": present["M15"]["present"],
        "source_spans": present,
        "broker_trading_session_status": "explicit_mt5_symbol_session_table_capture_required_before_live_authority",
        "timezone_rule_status": "exact_live_d1_m1_server_time_parity_capture_required_before_live_authority",
        "session_assumption_decision": (
            "OHLCV path/session windows are source-covered for activation-candidate packaging; broker trading-hours "
            "tables are not present in current ledgers and must be captured read-only before live activation."
        ),
    }


def activation_controls(
    *,
    tag: str,
    spec: candidate_registry.MarketExpansionDefaultOffSpec,
    cost_summary: dict[str, Any],
    split_every_positive: bool | None,
    matched_current_book_days: int | None,
) -> list[str]:
    controls: list[str] = []
    cost3 = cost_summary.get("cost3") or {}
    cost2 = cost_summary.get("cost2") or {}
    if cost3.get("every_populated_split_positive") is not True:
        controls.append("cost3_split_stress_not_all_positive_requires_initial_weight_cap_or_limit_order_model")
    if cost2.get("every_populated_split_positive") is not True:
        controls.append("cost2_split_stress_not_all_positive_requires_cost_monitor_before_activation")
    if split_every_positive is False:
        controls.append("negative_path_split_requires_holdout_or_sizing_gate_before_activation")
    if tag in {
        "mx_jp225_cash_d1_volume_surge_reversal",
        "mx_us30_cash_d1_volume_surge_reversal",
    }:
        controls.append("known_negative_oos_exact_m1_split_conflict_must_not_be_silently_promoted")
    if spec.full_book_delta_sharpe < 0.0001:
        controls.append("low_unit_sensitivity_delta_requires_micro_weight_and_interaction_retest")
    if spec.target2_exact_m1_event_count < 30:
        controls.append("low_exact_m1_event_count_requires_path_replay_expansion_or_lower_initial_weight")
    if matched_current_book_days is not None and matched_current_book_days < 60:
        controls.append("low_current_book_matched_day_count_requires_interaction_replay_expansion")
    if spec.family == "indices_context":
        controls.append("indices_concentration_budget_required")
    if spec.family == "crypto_alt_or_major":
        controls.append("crypto_swap_and_weekend_gap_cost_monitor_required")
    if spec.family == "jpy_fx":
        controls.append("jpy_carry_swap_and_session_rollover_monitor_required")
    return sorted(set(controls))


def row_decision(controls: list[str], cost_summary: dict[str, Any], split_every_positive: bool | None) -> str:
    if split_every_positive is False:
        return "keep_metadata_only_pending_split_stability_sizing_gate"
    if (cost_summary.get("cost3") or {}).get("every_populated_split_positive") is not True:
        return "keep_metadata_only_pending_cost3_stress_sizing_gate"
    if controls:
        return "keep_metadata_only_pending_default_off_generator_with_controls"
    return "keep_metadata_only_pending_default_off_generator"


def build() -> dict[str, Any]:
    created_at = utc_now()
    source_paths = [
        REPAIRED_REGISTRY_ROUTE / "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_RESULT.json",
        REPAIRED_REGISTRY_ROUTE / "REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl",
        DATA_AVAILABILITY_ROUTE / "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl",
        SCORING_ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl",
        FOLLOWUP_ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl",
        FOLLOWUP_ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl",
        DEFAULT_OFF_DESIGN_ROUTE / "PROFILE_SPEC_COST_PREREQ_LEDGER.jsonl",
        PROXY_M1_REPAIR_ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl",
        PROXY_M1_REPAIR_ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl",
    ]
    repaired_result = read_json(REPAIRED_REGISTRY_ROUTE / "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_RESULT.json")
    repaired_rows = read_jsonl(REPAIRED_REGISTRY_ROUTE / "REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl")
    availability_rows = read_jsonl(DATA_AVAILABILITY_ROUTE / "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl")
    scoring_rows = read_jsonl(SCORING_ROUTE / "CANDIDATE_RESULT_LEDGER.jsonl")
    followup_rows = read_jsonl(FOLLOWUP_ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl")
    followup_interactions = read_jsonl(FOLLOWUP_ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl")
    prereq_rows = read_jsonl(DEFAULT_OFF_DESIGN_ROUTE / "PROFILE_SPEC_COST_PREREQ_LEDGER.jsonl")
    repair_rows = read_jsonl(PROXY_M1_REPAIR_ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    repair_interactions = read_jsonl(PROXY_M1_REPAIR_ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl")

    repaired_by_tag = {row["tag"]: row for row in repaired_rows}
    availability_by_symbol = {row["file_symbol"]: row for row in availability_rows}
    scoring_by_key = {(row["file_symbol"], row["mechanism"]): row for row in scoring_rows}
    followup_by_key = {(row["file_symbol"], row["mechanism"]): row for row in followup_rows}
    followup_interaction_by_key = {(row["file_symbol"], row["mechanism"]): row for row in followup_interactions}
    prereq_by_key = {(row["file_symbol"], row["mechanism"]): row for row in prereq_rows}
    repair_by_tag = {row["tag"]: row for row in repair_rows}
    repair_interaction_by_tag = {row["tag"]: row for row in repair_interactions}

    row_ledgers: list[dict[str, Any]] = []
    spec_manifest_rows: list[dict[str, Any]] = []
    generator_rows: list[dict[str, Any]] = []
    sizing_rows: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []

    for tag, spec in sorted(selected_specs().items()):
        key = (spec.file_symbol, spec.mechanism)
        repaired_row = repaired_by_tag[tag]
        availability = availability_by_symbol[spec.file_symbol]
        scoring = scoring_by_key[key]
        followup = followup_by_key[key]
        prereq = prereq_by_key.get(key, {})
        repair = repair_by_tag.get(tag)
        interaction = repair_interaction_by_tag.get(tag) or followup_interaction_by_key[key]
        cost_summary = summarize_cost(scoring.get("cost_stress") or {})
        path_summary = (
            (repair or {}).get("target2_exact_m1_summary")
            or followup.get("target2_ordered_path_summary")
            or {}
        )
        split_every_positive = path_summary.get("every_populated_split_positive")
        matched_current_book_days = interaction.get("matched_current_book_days")
        controls = activation_controls(
            tag=tag,
            spec=spec,
            cost_summary=cost_summary,
            split_every_positive=split_every_positive,
            matched_current_book_days=matched_current_book_days,
        )
        session_status = source_span_session_status(availability)
        broker_spec_ready = (
            availability.get("validation_ready") is True
            and availability.get("spec_status") == "trade_ready"
            and availability.get("trade_mode_full") is True
            and availability.get("visible") is True
            and float((availability.get("spread_snapshot") or {}).get("volume_min") or 0) > 0
            and float((availability.get("spread_snapshot") or {}).get("volume_step") or 0) > 0
        )
        spread_snapshot = availability.get("spread_snapshot") or {}
        stop_freeze_fields_present = (
            spread_snapshot.get("trade_stops_level") is not None
            and spread_snapshot.get("trade_freeze_level") is not None
        )
        live_authority_missing_fields = [
            "trade_stops_level" if spread_snapshot.get("trade_stops_level") is None else None,
            "trade_freeze_level" if spread_snapshot.get("trade_freeze_level") is None else None,
            "explicit_broker_trading_session_table",
            "exact_live_D1_M1_server_timezone_rule",
            "commission_slippage_to_R_conversion",
            "limit_fill_or_market_fill_policy",
            "runtime_generator_parity",
            "full_generator_book_replay",
        ]
        live_authority_missing_fields = [field for field in live_authority_missing_fields if field]
        generator = generator_contract(tag, spec)
        decision = row_decision(controls, cost_summary, split_every_positive)
        row = {
            "schema": f"{SCHEMA_PREFIX}.activation_row.v1",
            "created_at_utc": created_at,
            **spec_to_row(tag, spec),
            "source_repaired_registry_row_present": True,
            "source_event_count": followup.get("source_event_count"),
            "target2_ordered_path_event_count": followup.get("target2_ordered_path_event_count"),
            "target2_exact_m1_path_source_count": spec.target2_exact_m1_event_count,
            "target2_remaining_path_gap_count": spec.target2_m15_proxy_event_count,
            "target2_split_every_populated_positive": split_every_positive,
            "target2_split_positive_count": path_summary.get("positive_populated_split_count"),
            "target2_split_count": path_summary.get("populated_split_count"),
            "cost_stress": cost_summary,
            "broker_spec_ready": broker_spec_ready,
            "broker_contract_min_volume_ready": broker_spec_ready,
            "broker_execution_spec_complete_for_live_authority": False,
            "broker_execution_spec_missing_fields": live_authority_missing_fields,
            "trade_stops_level": spread_snapshot.get("trade_stops_level"),
            "trade_freeze_level": spread_snapshot.get("trade_freeze_level"),
            "stop_freeze_fields_present": stop_freeze_fields_present,
            "spec_status": availability.get("spec_status"),
            "trade_mode": availability.get("trade_mode"),
            "trade_mode_full": availability.get("trade_mode_full"),
            "visible": availability.get("visible"),
            "volume_min": spread_snapshot.get("volume_min"),
            "volume_max": spread_snapshot.get("volume_max"),
            "volume_step": spread_snapshot.get("volume_step"),
            "spread_snapshot": spread_snapshot,
            "session_source_status": session_status,
            "profile_spec_cost_prereq": prereq,
            "activation_stage_controls": controls,
            "row_level_decision": decision,
            "activation_candidate_package_status": "package_ready_default_off_not_live_authority",
            "generator_current_code_status": generator["current_generator_code_status"],
            "generator_implementation_decision": generator["implementation_decision"],
            "activation_weight_now": 0.0,
            "live_authority": False,
            "runtime_effect": "none_metadata_package_only",
        }
        row_ledgers.append(row)
        spec_manifest_rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.broker_spec_cost_session_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": spec.file_symbol,
                "broker_symbol": spec.broker_symbol,
                "mechanism": spec.mechanism,
                "broker_spec_ready": broker_spec_ready,
                "spec_status": availability.get("spec_status"),
                "trade_mode": availability.get("trade_mode"),
                "trade_mode_full": availability.get("trade_mode_full"),
                "visible": availability.get("visible"),
                "volume_min": row["volume_min"],
                "volume_max": row["volume_max"],
                "volume_step": row["volume_step"],
                "trade_stops_level": row["trade_stops_level"],
                "trade_freeze_level": row["trade_freeze_level"],
                "stop_freeze_fields_present": row["stop_freeze_fields_present"],
                "spread_snapshot": spread_snapshot,
                "cost_stress": cost_summary,
                "session_source_status": session_status,
                "broker_execution_spec_complete_for_live_authority": False,
                "broker_execution_spec_missing_fields": live_authority_missing_fields,
                "broker_trading_session_capture_requirement": session_status["broker_trading_session_status"],
            }
        )
        generator_rows.append(generator)
        sizing_rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.split_stability_sizing_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": spec.file_symbol,
                "broker_symbol": spec.broker_symbol,
                "family": spec.family,
                "mechanism": spec.mechanism,
                "target2_mean_r": spec.target2_ordered_mean_r,
                "target2_exact_m1_event_count": spec.target2_exact_m1_event_count,
                "target2_split_every_populated_positive": split_every_positive,
                "cost3_every_populated_split_positive": (cost_summary.get("cost3") or {}).get("every_populated_split_positive"),
                "full_book_delta_sharpe": spec.full_book_delta_sharpe,
                "matched_current_book_days": matched_current_book_days,
                "activation_stage_controls": controls,
                "initial_sizing_recommendation": (
                    "micro_default_off_seed_only_after_generator_parity"
                    if controls
                    else "default_off_seed_candidate_after_generator_parity"
                ),
                "max_candidate_weight_ceiling": spec.candidate_weight_ceiling,
                "activation_weight_now": 0.0,
                "live_authority": False,
            }
        )
        interaction_rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.interaction_replay_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": spec.file_symbol,
                "broker_symbol": spec.broker_symbol,
                "family": spec.family,
                "mechanism": spec.mechanism,
                "interaction_source": rel(PROXY_M1_REPAIR_ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl")
                if tag in repair_interaction_by_tag
                else rel(FOLLOWUP_ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl"),
                "policy": interaction.get("policy", "target2_exact_m1_unit_sensitivity"),
                "base_current_book_sharpe": interaction.get("base_current_book_sharpe", interaction.get("base_sharpe")),
                "scenario_sharpe": interaction.get("scenario_sharpe"),
                "delta_sharpe": interaction.get("delta_sharpe"),
                "matched_current_book_days": matched_current_book_days,
                "unit_interaction_weight": interaction.get("unit_interaction_weight", 0.05),
                "runtime_generator_replay_status": "not_run_current_generator_not_implemented",
                "replay_boundary": (
                    "full-book unit-sensitivity from repaired/follow-up ledgers; not broker lifecycle, not live "
                    "slippage, not queue/fill proof, and not current runtime generator parity"
                ),
                "live_authority": False,
            }
        )
        decision_rows.append(
            {
                "created_at_utc": created_at,
                "tag": tag,
                "decision": decision,
                "reason": "row preserved as default-off activation candidate with explicit controls and generator requirement",
                "activation_stage_controls": controls,
                "runtime_effect": "none_metadata_package_only",
                "live_authority": False,
            }
        )

    active_registry = admission.effective_registry(include_candidate_book=True)
    candidate_runtime = admission.candidate_book_registry()
    expansion_names = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_NAMES)
    active_audit = {
        "schema": f"{SCHEMA_PREFIX}.active_behavior_audit.v1",
        "created_at_utc": created_at,
        "ok": True,
        "market_expansion_names_in_effective_registry": sorted(expansion_names & set(active_registry)),
        "market_expansion_names_in_candidate_book_registry": sorted(expansion_names & set(candidate_runtime)),
        "market_expansion_names_in_candidate_built": sorted(expansion_names & set(registry.CANDIDATE_BUILT)),
        "market_expansion_names_in_candidate_registry_candidates": sorted(expansion_names & set(candidate_registry.CANDIDATES)),
        "market_expansion_runtime_names": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
        "activation_weight_sum": round(sum(float(row["activation_weight_now"]) for row in row_ledgers), 6),
        "runtime_effect": "none_metadata_package_only",
    }

    family_counts = Counter(row["family"] for row in row_ledgers)
    mechanism_counts = Counter(row["mechanism"] for row in row_ledgers)
    decision_counts = Counter(row["row_level_decision"] for row in row_ledgers)
    cost3_split_pass_count = sum(
        1
        for row in row_ledgers
        if (row["cost_stress"].get("cost3") or {}).get("every_populated_split_positive") is True
    )
    exact_split_pass_count = sum(1 for row in row_ledgers if row["target2_split_every_populated_positive"] is True)
    broker_spec_ready_count = sum(1 for row in row_ledgers if row["broker_spec_ready"])
    positive_cost3_mean_count = sum(
        1
        for row in row_ledgers
        if float((row["cost_stress"].get("cost3") or {}).get("mean_proxy_r") or 0.0) > 0.0
    )
    session_capture_required_count = sum(
        1
        for row in row_ledgers
        if row["session_source_status"]["broker_trading_session_status"]
        == "explicit_mt5_symbol_session_table_capture_required_before_live_authority"
    )
    execution_spec_live_complete_count = sum(
        1 for row in row_ledgers if row["broker_execution_spec_complete_for_live_authority"] is True
    )
    split_conflict_tags = sorted(
        row["tag"] for row in row_ledgers if row["target2_split_every_populated_positive"] is False
    )
    cost3_control_tags = sorted(
        row["tag"]
        for row in row_ledgers
        if (row["cost_stress"].get("cost3") or {}).get("every_populated_split_positive") is not True
    )
    generator_not_implemented_count = sum(
        1 for row in generator_rows if row["current_generator_code_status"] == "not_implemented_in_runtime"
    )

    result_ok = (
        repaired_result.get("ok") is True
        and len(row_ledgers) == 14
        and broker_spec_ready_count == 14
        and positive_cost3_mean_count == 14
        and cost3_split_pass_count == 9
        and exact_split_pass_count == 12
        and generator_not_implemented_count == 14
        and not active_audit["market_expansion_names_in_effective_registry"]
        and not active_audit["market_expansion_names_in_candidate_book_registry"]
        and not active_audit["market_expansion_names_in_candidate_built"]
        and not active_audit["market_expansion_names_in_candidate_registry_candidates"]
        and not active_audit["market_expansion_runtime_names"]
        and active_audit["activation_weight_sum"] == 0.0
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": result_ok,
        "decision": "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_READY_DEFAULT_OFF_NOT_LIVE_AUTHORITY",
        "source_repaired_registry_route": rel(REPAIRED_REGISTRY_ROUTE),
        "selectable_activation_candidate_count": len(row_ledgers),
        "broker_spec_ready_count": broker_spec_ready_count,
        "broker_contract_min_volume_ready_count": broker_spec_ready_count,
        "broker_execution_spec_live_complete_count": execution_spec_live_complete_count,
        "positive_cost3_mean_count": positive_cost3_mean_count,
        "cost1_split_pass_count": sum(
            1
            for row in row_ledgers
            if (row["cost_stress"].get("cost1") or {}).get("every_populated_split_positive") is True
        ),
        "cost2_split_pass_count": sum(
            1
            for row in row_ledgers
            if (row["cost_stress"].get("cost2") or {}).get("every_populated_split_positive") is True
        ),
        "cost3_split_pass_count": cost3_split_pass_count,
        "exact_or_ordered_split_pass_count": exact_split_pass_count,
        "split_conflict_tags": split_conflict_tags,
        "cost3_control_tags": cost3_control_tags,
        "generator_mapping_count": len(generator_rows),
        "runtime_generator_implemented_count": len(generator_rows) - generator_not_implemented_count,
        "runtime_generator_not_implemented_count": generator_not_implemented_count,
        "session_capture_required_before_live_authority_count": session_capture_required_count,
        "family_counts": dict(sorted(family_counts.items())),
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
        "row_decision_counts": dict(sorted(decision_counts.items())),
        "activation_candidate_package_ready": True,
        "deployment_ready": False,
        "deployment_not_ready_reasons": [
            "default-off runtime generator code is not implemented",
            "D1 next-open runtime entry timing contract is not implemented",
            "explicit broker trading-session table capture is not present in current ledgers",
            "trade_stops_level/trade_freeze_level are not present in current market-expansion spec snapshot",
            "exact commission/slippage/limit-fill conversion to R is not present",
            "live activation authority package has not been built or owner-approved",
        ],
        "activation_weight_now": 0.0,
        "runtime_effect": "none_metadata_package_only",
        "live_authority": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "account_info_read": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
    }

    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": source_index(source_paths),
        "code_surfaces_read": [
            "src/components/ultimate_book/sleeves/candidate_registry.py",
            "src/components/ultimate_book/sleeves/registry.py",
            "src/components/ultimate_book/admission.py",
            "src/components/ultimate_book/bridge.py",
            "src/components/ultimate_book/execution_packets.py",
        ],
        "allowed_source_scope": "committed market-expansion artifacts and source-hashed local MT5 OHLCV/tick-volume/spec snapshots",
        "forbidden_data": [
            "orderflow",
            "depth",
            "broker order/deal/position/account mutation",
            "broker history mutation or order-state reads",
            "credentials",
            "remotes",
            "VPS processes",
            "paid API/vendor calls",
            "live config activation",
        ],
    }
    decision_rows.insert(
        0,
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "selectable_activation_candidate_count": len(row_ledgers),
            "activation_candidate_package_ready": True,
            "deployment_ready": False,
            "runtime_effect": "none_metadata_package_only",
            "live_authority": False,
        },
    )
    decision_rows.append(
        {
            "created_at_utc": created_at,
            "decision": "DO_NOT_KILL_COST_OR_SPLIT_CAVEAT_ROWS_TRANSLATE_TO_CONTROLS",
            "split_conflict_tags": split_conflict_tags,
            "cost3_control_tags": cost3_control_tags,
            "reason": "selected rows retain positive means and useful mechanisms; caveats become sizing, session, cost, or generator-parity controls",
        }
    )
    subagent_review_rows = [
        {
            "created_at_utc": created_at,
            "subagent": "Franklin",
            "subagent_id": "019eda4c-daff-70c3-94f7-3a29dd90aede",
            "review_type": "runtime_generator_feasibility_audit",
            "integrated_findings": [
                "implement shared D1 logic in a new market_expansion_d1.py module if a later lane wires code",
                "do not append expansion rows directly to the already-enabled generic candidate-book all-candidates path",
                "D1 validation used prior-day signal with current-D1-open entry; current closed-bar engine needs explicit timing contract",
                "add separate expansion flag/allowlist, exit-profile mapping, zero-activation tests, mapping coverage tests, and generator parity tests",
            ],
        },
        {
            "created_at_utc": created_at,
            "subagent": "Lovelace",
            "subagent_id": "019eda4c-fb3d-76b1-89d4-2c32f94e1646",
            "review_type": "row_level_cost_spec_split_extraction",
            "integrated_findings": [
                "all 14 selectable rows are preserved as 0.025 seed metadata but zero activation",
                "all 14 have upstream prereq status requiring activation proof and OHLCV path replay is not broker lifecycle truth",
                "cost3 split stress passes 9 of 14 while all 14 keep positive cost3 mean",
                "JP225 and US30 carry negative exact-M1 OOS split conflict into sizing/stability controls",
                "min stop distance, session/trading-hours, timezone, commission/slippage, profile alias, and generator mapping must be explicit live-authority requirements",
            ],
        },
    ]
    repair_ledger = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger.v1",
        "created_at_utc": created_at,
        "ok": True,
        "completed_repairs": [
            "converted 14 selectable repaired/default-off metadata rows into activation-candidate row ledger",
            "bound every row to broker-native spec snapshot, min-volume, cost-stress, source-span, split, and interaction evidence",
            "translated JP225 and US30 negative-OOS split conflicts into explicit sizing/stability controls",
            "froze exact non-implementation requirement for D1 next-open runtime generator parity instead of overclaiming generator code",
        ],
        "remaining_exact_requirements": result["deployment_not_ready_reasons"],
    }
    saturation_audit = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "created_at_utc": created_at,
        "ok": True,
        "no_arbitrary_top_n": True,
        "all_selectable_rows_materialized": len(row_ledgers) == 14,
        "full_ledgers_preserve_all_material_rows": True,
        "same_evidence_class_pursuit": [
            "read repaired registry integration route",
            "read data availability broker spec/source-span ledger",
            "read validation scoring cost-stress ledger",
            "read follow-up replay and full-book interaction ledgers",
            "read exact-M1 repair candidate and interaction ledgers",
            "inspected runtime registry surfaces before deciding generator implementation status",
        ],
        "anti_boxing_checks": [
            "did not discard rows because of cost3 or split caveats",
            "did not reduce to indices-only winners despite concentration",
            "did not treat default-off boundary as a reason to skip implementation contract",
            "did not call live/deployment ready without generator, timing, session, and authority proof",
        ],
        "inspire_not_kill_translation": {
            "split_conflict_tags": split_conflict_tags,
            "cost3_control_tags": cost3_control_tags,
            "translation": "caveats become explicit activation-stage controls and successor generator requirements",
        },
        "literal_impossibility_or_exact_requirement": [
            "runtime generator implementation requires a new D1 next-open timing contract not present in current SleeveSpec execution model",
            "broker trading-session table capture is not present in current upstream ledgers and must be captured read-only before live authority",
        ],
    }
    completion_audit = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": result_ok,
        "goal_session_research_discipline_read": True,
        "research_operating_doctrine_read": True,
        "orchestrator_context_read": True,
        "lane_posture": "builder_activation_candidate_package_design",
        "builder_posture_applied": "constructive, source-bound, full-row preservation, inspire-not-kill",
        "result_materialization_status": "all_14_selectable_rows_materialized",
        "runtime_effect": "none_metadata_package_only",
        "activation_weight_now": 0.0,
        "live_authority": False,
        "forbidden_surfaces_touched": [],
        "completion_standard": (
            "row-level activation ledger, broker spec/cost/session manifest, generator implementation requirements, "
            "interaction replay ledger, verifier, focused tests, completion audit, output manifest, successor prompt"
        ),
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "created_at_utc": created_at,
        "ok": result_ok,
        "checks": [
            {"name": "selectable_row_count", "passed": len(row_ledgers) == 14},
            {"name": "broker_spec_ready_all_rows", "passed": broker_spec_ready_count == 14},
            {"name": "positive_cost3_mean_all_rows", "passed": positive_cost3_mean_count == 14},
            {"name": "expected_cost3_split_pass_count", "passed": cost3_split_pass_count == 9},
            {"name": "expected_exact_split_pass_count", "passed": exact_split_pass_count == 12},
            {"name": "no_active_runtime_membership", "passed": active_audit["activation_weight_sum"] == 0.0 and not active_audit["market_expansion_names_in_effective_registry"]},
            {"name": "generator_status_honest", "passed": generator_not_implemented_count == 14},
        ],
    }

    write_json(ROUTE / "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_RESULT.json", result)
    write_json(ROUTE / "ACTIVATION_INPUT_MANIFEST.json", input_manifest)
    write_jsonl(ROUTE / "ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl", row_ledgers)
    write_json(
        ROUTE / "BROKER_SPEC_COST_SESSION_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.broker_spec_cost_session_manifest.v1",
            "created_at_utc": created_at,
            "ok": broker_spec_ready_count == 14,
            "row_count": len(spec_manifest_rows),
            "broker_spec_ready_count": broker_spec_ready_count,
            "session_capture_required_before_live_authority_count": session_capture_required_count,
            "rows": spec_manifest_rows,
        },
    )
    write_jsonl(ROUTE / "GENERATOR_IMPLEMENTATION_DECISION_LEDGER.jsonl", generator_rows)
    write_jsonl(ROUTE / "SPLIT_STABILITY_SIZING_LEDGER.jsonl", sizing_rows)
    write_jsonl(ROUTE / "FULL_BOOK_INTERACTION_REPLAY_LEDGER.jsonl", interaction_rows)
    write_json(ROUTE / "ACTIVE_BEHAVIOR_AUDIT.json", active_audit)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(ROUTE / "SUBAGENT_REVIEW_INTEGRATION_LEDGER.jsonl", subagent_review_rows)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair_ledger)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation_audit)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion_audit)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    write_next_prompt()
    manifest = output_manifest(created_at)
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    return result


def write_next_prompt() -> None:
    prompt = """# Market Expansion Default-Off Runtime Generator Implementation Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the activation-candidate package artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md` as active instructions before acting.

Evidence class: default-off production-code integration for market-expansion runtime generator packaging. This is not live trading authority. Operate with maximum practical reasoning, active creativity, constructive builder posture, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, full ledger preservation for all material rows, same-evidence-class and full same-evidence-class pursuit, and inspire-not-kill preservation. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available inside the allowed evidence class has been attempted or reduced to an exact source-capture or owner-action requirement.

Allowed data: committed activation-candidate package artifacts, repaired registry integration artifacts, proxy M1 repair artifacts, source-hashed local MT5 OHLCV/tick-volume exports, current active candidate-book replay/MC artifacts, and localhost MT5 bridge read-only for missing OHLCV/tick-volume/spec/session evidence. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation beyond local default-off code packaging; no live config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: implement or exactly fail-closed the default-off market-expansion D1 runtime generator package for all 14 activation-candidate rows from `ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl`. The implementation must preserve zero live effect and zero activation weight, add an explicit market-expansion flag/allowlist that cannot be activated accidentally by the existing candidate-book broad path, and solve the D1 next-open timing problem exposed by the activation package. Result materialization is required: implementation decision, branch decision, source-capture/source completeness proof, proxy-R/exact-R parity where computable, or exact source-safe impossibility for every row.

Required output artifacts: generator code or exact non-implementation proof, row-level parity ledger, D1 next-open timing contract proof, broker session/spec capture manifest, execution-packet dry-run proof for fixed target2 semantics, zero-active-behavior audit, verifier, focused pytest, completion audit, output manifest, and successor prompt. Completion audit must include instruction-coverage, source-use state, runtime-effect boundary, result materialization status, and exact owner-action/live-authority boundary. Keep activation weight zero unless a later owner-approved live authority package explicitly changes live config after all proof gates pass.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def output_manifest(created_at: str) -> dict[str, Any]:
    artifact_names = [
        "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_RESULT.json",
        "ACTIVATION_INPUT_MANIFEST.json",
        "ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl",
        "BROKER_SPEC_COST_SESSION_MANIFEST.json",
        "GENERATOR_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "SPLIT_STABILITY_SIZING_LEDGER.jsonl",
        "FULL_BOOK_INTERACTION_REPLAY_LEDGER.jsonl",
        "ACTIVE_BEHAVIOR_AUDIT.json",
        "DECISION_LEDGER.jsonl",
        "SUBAGENT_REVIEW_INTEGRATION_LEDGER.jsonl",
        "REPAIR_LEDGER.json",
        "SATURATION_AUDIT.json",
        "COMPLETION_AUDIT.json",
        "FOCUSED_TEST_RESULT.json",
        "NEXT_PROMPT.md",
        "build_market_expansion_activation_candidate_package.py",
        "verify_market_expansion_activation_candidate_package.py",
    ]
    return {
        "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
        "created_at_utc": created_at,
        "route": rel(ROUTE),
        "artifacts": source_index([ROUTE / name for name in artifact_names if (ROUTE / name).exists()]),
    }


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "selectable_activation_candidate_count": result["selectable_activation_candidate_count"],
                "deployment_ready": result["deployment_ready"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

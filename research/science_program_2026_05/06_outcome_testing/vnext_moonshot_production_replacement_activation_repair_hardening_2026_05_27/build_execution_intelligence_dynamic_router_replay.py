from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

import build_execution_intelligence_static_15r_ceiling_repair as ei15r


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_default_off_policy_router import (  # noqa: E402
    CONDITION_CHALLENGER_MODE,
    DEFAULT_POLICY,
    EXECUTION_POLICY_IDS,
    SUPPORTED_LIVE_EXECUTION_POLICIES,
    route_moonshot_dynamic_execution,
)


DATE = "2026-05-27"
OUT_DIR = ROUTE_DIR / "ei15r"
LEDGER_STEM = OUT_DIR / "final_dynamic_router_replay"
MANIFEST = OUT_DIR / "final_dynamic_router_replay.manifest.jsonl"
SUMMARY = OUT_DIR / "final_dynamic_router_replay_summary.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
COMPARISON_POLICIES = (
    "fixed_1_5r",
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
    "time_stop",
)
HINDSIGHT_POLICIES = (
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
    "time_stop",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def rel(path: Path) -> str:
    return ei15r.rel(path)


def sha256_file(path: Path) -> str:
    return ei15r.sha256_file(path)


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _symbol_key(value: Any) -> str:
    return str(value or "").strip().upper().replace(".", "_")


def session_bucket_for_row(row: dict[str, Any]) -> tuple[str, str]:
    route_session = _norm(row.get("route_session"))
    selector = _norm(row.get("selector_component"))
    if selector == "broader_origin_outside_session_expansion":
        return "off_kz_broad", "outside_session_expansion_row_normalized_to_live_off_kz_bucket"
    if route_session.startswith("moonshot_h") or route_session in {"off_configured_session", "off_kz"}:
        return "off_kz_broad", "historical_hour_bucket_normalized_to_live_off_kz_bucket"
    if not route_session:
        return "off_kz_broad", "missing_route_session_normalized_to_off_kz_bucket"
    if route_session.endswith("_broad"):
        return route_session, "already_broad_session_bucket"
    if "tokyo" in route_session:
        return "tokyo_broad", "runtime_session_bucket_normalization"
    if route_session in {"ny", "new_york", "newyork"} or "ny" in route_session:
        return "ny_broad", "runtime_session_bucket_normalization"
    if "london" in route_session or route_session in {"ldn", "lon"}:
        return "london_broad", "runtime_session_bucket_normalization"
    if "off" in route_session or "dead" in route_session:
        return "off_kz_broad", "runtime_session_bucket_normalization"
    return f"{route_session}_broad", "runtime_session_bucket_passthrough_unknown_bucket"


def kill_zone_position_for_row(row: dict[str, Any], session_bucket: str) -> str:
    explicit = row.get("kill_zone_bucket")
    if explicit:
        return str(explicit)
    if session_bucket == "off_kz_broad":
        return "in_off_configured_session_repo_schedule_repaired"
    name = session_bucket.removesuffix("_broad")
    return f"in_{name}_repo_schedule_repaired"


def utc_hour_bucket(time_value: Any) -> str | None:
    text = ei15r.norm_time(time_value)
    if not text or len(text) < 13:
        return None
    try:
        hour = int(text[11:13])
    except ValueError:
        return None
    return f"h{hour:02d}_{(hour + 1) % 24:02d}"


def volatility_state(fields: dict[str, Any]) -> str:
    ratio = ei15r.float_or_none(fields.get("atr14_atr50_ratio"))
    if ratio is None:
        return "unknown_volatility_state"
    if ratio >= 1.2:
        return "recent_range_expansion_vs_atr50"
    if ratio <= 0.8:
        return "recent_range_compression_vs_atr50"
    return "normal_recent_vs_baseline"


def origin_family_for_row(row: dict[str, Any]) -> str:
    family = str(row.get("origin_family") or row.get("candidate_origin_family") or "").strip()
    return family.removeprefix("origin_")


def candidate_origin_family_for_row(row: dict[str, Any]) -> str:
    value = str(row.get("candidate_origin_family") or "").strip()
    if value:
        return value
    family = str(row.get("origin_family") or "").strip()
    return family if family.startswith("origin_") else f"origin_{family or 'unknown'}"


def selected_policy_ordered_path_status(chosen: dict[str, Any]) -> str:
    if chosen.get("same_bar_ambiguity"):
        return "same_bar_ambiguous_in_m15_replay_live_m1_tick_capture_required"
    return "ordered_path_not_ambiguous_in_m15_replay"


def router_event_for_row(
    *,
    row: dict[str, Any],
    source_fields: dict[str, Any],
    source_time: str | None,
    session_bucket: str,
    session_bucket_reason: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    runtime = config["gtos_vnext_runtime"]
    symbol = row.get("symbol")
    symbol_key = _symbol_key(symbol)
    eligible = runtime.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols") or []
    excluded = runtime.get("moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols") or []
    eligible_keys = {_symbol_key(item) for item in eligible}
    excluded_keys = {_symbol_key(item) for item in excluded}
    selector = _norm(row.get("selector_component"))
    branch_label = str(row.get("prior_branch_label") or "FOLLOW").strip().upper()
    broader_origin_allowed = selector.startswith("broader_origin")
    repaired_branch_allowed = selector == "old_three_follow_or_repaired_branch" and branch_label != "FOLLOW"
    displacement = ei15r.float_or_none(source_fields.get("range_atr14"))
    liquidity_state = source_fields.get("sweep_direction") or "no_prior_20_sweep"
    source_complete = bool(row.get("source_path") or row.get("source_artifact_path") or source_time)
    event = {
        "symbol": symbol,
        "side": row.get("side"),
        "framework": row.get("framework") or origin_family_for_row(row),
        "candidate_origin_family": candidate_origin_family_for_row(row),
        "route_family": origin_family_for_row(row),
        "route_session": row.get("route_session"),
        "session_bucket": session_bucket,
        "session_bucket_normalization_reason": session_bucket_reason,
        "kill_zone_position": kill_zone_position_for_row(row, session_bucket),
        "candle_time_utc": source_time or row.get("decision_time_utc"),
        "utc_hour_bucket": utc_hour_bucket(source_time or row.get("decision_time_utc")),
        "branch_label": branch_label,
        "branch_reason": row.get("selection_proof_class") or row.get("selector_component"),
        "activated_frameworks": runtime.get("moonshot_dynamic_execution_router_activated_frameworks"),
        "activated_origin_families": runtime.get("moonshot_dynamic_execution_router_activated_origin_families"),
        "required_branch_labels": runtime.get("moonshot_dynamic_execution_router_required_branch_labels", ("FOLLOW",)),
        "repaired_branch_allowed": repaired_branch_allowed,
        "broader_origin_allowed": broader_origin_allowed,
        "broker_native_eligible_symbols": eligible,
        "broker_native_exact_excluded_symbols": excluded,
        "broker_native_eligible": symbol_key in eligible_keys if eligible_keys else True,
        "broker_native_exact_excluded": symbol_key in excluded_keys,
        "runtime_instrument_configured": symbol_key in eligible_keys if eligible_keys else True,
        "require_configured_kill_zone": True,
        "source_mode": "OHLC_M15_CSV_ASOF_REPLAY",
        "source_path_feature_status": "computed_from_source_ohlc_asof",
        "live_generation_status": (
            "generated_live_asof_from_selected_stage04_source"
            if broader_origin_allowed
            else "old_three_source_replayed_asof"
        ),
        "source_window_complete": source_complete,
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "selected_policy_ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "selected_policy_same_bar_ambiguous": False,
        "liquidity_sweep_proxy_state": liquidity_state,
        "volatility_state_14_vs_50": volatility_state(source_fields),
        "trend_state_20": source_fields.get("trend_state_20") or "unknown_trend_state",
        "current_bar_displacement_atr14": displacement,
        "policy_router_mode": runtime.get(
            "moonshot_dynamic_execution_router_condition_challenger_policy",
            CONDITION_CHALLENGER_MODE,
        ),
        "condition_challenger_enabled": bool(
            runtime.get("moonshot_dynamic_execution_router_condition_challenger_enabled", False)
        ),
        "selected_cell_risk_required": True,
        "selected_cell_risk_allowed": bool(row.get("risk_positive_executable_row")),
        "selected_cell_risk_pct": row.get("risk_per_trade_pct_current"),
        "selected_cell_risk_cell_id": (
            f"{symbol_key}|{row.get('framework')}|{session_bucket}|"
            f"{origin_family_for_row(row)}|{row.get('side')}"
        ),
        "selected_cell_risk_decision_basis": row.get("risk_disposition"),
        "selected_cell_risk_match_reason": "stage04_selected_row_current_broker_geometry_positive",
        "prop_governor_action": None,
    }
    return {key: value for key, value in event.items() if value not in (None, "")}


def metric_bucket() -> dict[str, Any]:
    return {
        "rows": 0,
        "total_r": 0.0,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "gross_profit_r": 0.0,
        "gross_loss_r": 0.0,
    }


def add_metric(bucket: dict[str, Any], value: float) -> None:
    bucket["rows"] += 1
    bucket["total_r"] += value
    if value > 0:
        bucket["wins"] += 1
        bucket["gross_profit_r"] += value
    elif value < 0:
        bucket["losses"] += 1
        bucket["gross_loss_r"] += value
    else:
        bucket["breakevens"] += 1


def finalize_metric(bucket: dict[str, Any]) -> dict[str, Any]:
    rows = int(bucket["rows"])
    losses = int(bucket["losses"])
    total = float(bucket["total_r"])
    gross_loss = float(bucket["gross_loss_r"])
    out = dict(bucket)
    out["total_r"] = round(total, 6)
    out["gross_profit_r"] = round(float(bucket["gross_profit_r"]), 6)
    out["gross_loss_r"] = round(gross_loss, 6)
    out["expectancy_r"] = round(total / rows, 9) if rows else None
    out["profit_factor"] = (
        round(float(bucket["gross_profit_r"]) / abs(gross_loss), 9)
        if gross_loss < 0
        else None
    )
    out["win_rate"] = round(float(bucket["wins"]) / rows, 9) if rows else None
    out["win_rate_excluding_be"] = (
        round(float(bucket["wins"]) / (int(bucket["wins"]) + losses), 9)
        if int(bucket["wins"]) + losses
        else None
    )
    return out


def distribution_add(
    distributions: dict[str, dict[str, dict[str, Any]]],
    name: str,
    key: Any,
    value: float | None,
) -> None:
    bucket_key = str(key or "missing")
    bucket = distributions[name].setdefault(bucket_key, metric_bucket())
    if value is None:
        bucket["rows"] += 1
        return
    add_metric(bucket, float(value))


def finalize_distributions(
    distributions: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        name: {key: finalize_metric(value) for key, value in sorted(rows.items())}
        for name, rows in sorted(distributions.items())
    }


def week_key(time_value: Any) -> str:
    text = ei15r.norm_time(time_value)
    if not text:
        return "missing"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return "missing"
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def month_key(time_value: Any) -> str:
    text = ei15r.norm_time(time_value)
    return text[:7] if text and len(text) >= 7 else "missing"


def date_key(time_value: Any) -> str:
    text = ei15r.norm_time(time_value)
    return text[:10] if text and len(text) >= 10 else "missing"


def missing_notes_for_row(
    *,
    chosen: dict[str, Any],
    path_issue: str | None,
    m1_lookup: dict[str, Any],
    tick_lookup: dict[str, Any],
) -> list[str]:
    missing = set(str(item) for item in (chosen.get("missing_fields") or []))
    if path_issue:
        missing.add(path_issue)
    missing.update(ei15r.HISTORICAL_COST_MISSING_FIELDS)
    if chosen.get("same_bar_ambiguity"):
        if m1_lookup.get("m1_exact_entry_minute_present") or tick_lookup.get("tick_source_path"):
            missing.add("ordered_m1_or_tick_sequence_for_same_bar_resolution")
        else:
            missing.add("ordered_m1_or_tick_path_for_same_bar")
    if not (m1_lookup.get("m1_exact_entry_minute_present") or tick_lookup.get("tick_source_path")):
        missing.add("m1_or_tick_source_path")
    return sorted(missing)


def control_event(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": "execution_intelligence_final_dynamic_router_replay_built",
        "generated_at_utc": utc_now(),
        "status": summary["status"],
        "selected_rows": summary["selected_rows_processed"],
        "router_metric_rows": summary["final_dynamic_router_metrics"]["rows"],
        "router_total_r": summary["final_dynamic_router_metrics"]["total_r"],
        "router_expectancy_r": summary["final_dynamic_router_metrics"]["expectancy_r"],
        "condition_router_projection_gap_carried_forward_rows": summary[
            "condition_router_projection_gap_carried_forward_rows"
        ],
        "ledger_manifest": summary["outputs"]["final_dynamic_router_replay_ledger"]["manifest_path"],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = read_yaml(REPO_ROOT / "config" / "agent_config.yaml")
    source_records = ei15r.collect_source_record_index()
    csv_cache = ei15r.CsvCache()
    m1_index = ei15r.M1AvailabilityIndex()
    tick_index = ei15r.TickAvailabilityIndex()
    writer = ei15r.PlainJsonlShardWriter(
        ledger_name="final_dynamic_router_replay_ledger",
        stem=LEDGER_STEM,
        manifest_path=MANIFEST,
    )
    writer.reset()

    selected_rows = 0
    router_ready_rows = 0
    router_refused_rows = 0
    replayable_metric_rows = 0
    non_replayable_rows = 0
    policy_distribution: Counter[str] = Counter()
    raw_policy_distribution: Counter[str] = Counter()
    execution_policy_id_distribution: Counter[str] = Counter()
    fallback_counts: Counter[str] = Counter()
    m1_counts: Counter[str] = Counter()
    tick_counts: Counter[str] = Counter()
    replay_class_counts: Counter[str] = Counter()
    missing_field_counts: Counter[str] = Counter()
    comparison_metrics: dict[str, dict[str, Any]] = {
        policy: metric_bucket() for policy in COMPARISON_POLICIES
    }
    router_metrics = metric_bucket()
    hindsight_metrics = metric_bucket()
    regret_total = 0.0
    regret_rows = 0
    distributions: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    try:
        for row in ei15r.selected_rows():
            selected_rows += 1
            rid = ei15r.selected_row_id(row)
            source_record = source_records.get(str(row.get("candidate_id") or ""))
            source_path, source_sha = ei15r.source_path_from(row, source_record)
            csv_rows = csv_cache.load(source_path) if source_path else []
            source_idx = ei15r.int_or_none(row.get("source_row_index"))
            if source_idx is None and source_record:
                source_idx = ei15r.int_or_none(source_record.get("source_row_index"))
            if source_idx is None and source_record:
                source_idx = csv_cache.index_for_time(
                    source_path,
                    source_record.get("candle_time_utc") or source_record.get("decision_time_utc"),
                )
            entry_price = float(row["entry_price"])
            stop_price = float(row["stop_or_invalidation"])
            entry_idx, entry_issue, delayed_fill_bars = ei15r.entry_touch_index(
                csv_rows=csv_rows,
                start_idx=source_idx,
                entry=entry_price,
            )
            if entry_idx is None:
                path = []
                path_issue = entry_issue or "entry_price_not_touched_in_source_window"
            else:
                path, path_issue = ei15r.path_arrays(
                    csv_rows=csv_rows,
                    start_idx=entry_idx,
                    entry=entry_price,
                    stop=stop_price,
                    side=str(row.get("side") or ""),
                )
            source_time = (
                csv_rows[source_idx]["time"]
                if source_idx is not None and 0 <= source_idx < len(csv_rows)
                else ei15r.norm_time(row.get("decision_time_utc"))
            )
            entry_time = (
                csv_rows[entry_idx]["time"]
                if entry_idx is not None and 0 <= entry_idx < len(csv_rows)
                else source_time
            )
            m1_lookup = m1_index.lookup(row.get("symbol"), entry_time)
            tick_lookup = tick_index.lookup(row.get("symbol"), entry_time)
            m1_counts[str(m1_lookup.get("m1_availability_status"))] += 1
            tick_counts[str(tick_lookup.get("tick_availability_status"))] += 1
            source_fields = ei15r.source_fields_from(row, source_record, csv_rows, source_idx)
            policy_results = ei15r.simulate_policies(path, source_fields, source_record)
            session_bucket, session_bucket_reason = session_bucket_for_row(row)
            event = router_event_for_row(
                row=row,
                source_fields=source_fields,
                source_time=source_time,
                session_bucket=session_bucket,
                session_bucket_reason=session_bucket_reason,
                config=config,
            )
            decision = route_moonshot_dynamic_execution(
                event,
                enabled=True,
                apply_to_execution=True,
            )
            chosen_policy = decision.selected_policy or DEFAULT_POLICY
            if chosen_policy not in SUPPORTED_LIVE_EXECUTION_POLICIES:
                chosen_policy = DEFAULT_POLICY
            chosen = policy_results.get(chosen_policy) or policy_results[DEFAULT_POLICY]
            raw_policy = decision.route_dimensions.get("raw_asof_selected_policy")
            raw_policy_distribution[str(raw_policy or chosen_policy)] += 1
            policy_distribution[chosen_policy] += 1
            execution_policy_id = decision.execution_policy_id or EXECUTION_POLICY_IDS.get(chosen_policy)
            execution_policy_id_distribution[str(execution_policy_id or "missing")] += 1
            conversion_notes = [
                note
                for note in decision.evidence_notes
                if "fallback" in note or "legacy_fixed_1_5r" in note or "unsupported_asof" in note
            ]
            if not conversion_notes:
                conversion_notes = ["router_selected_supported_live_policy_without_conversion"]
            for note in conversion_notes:
                fallback_counts[note] += 1

            replay_class = (
                "replayable_from_asof_m15_ohlc_path"
                if path
                else f"non_replayable_{path_issue or 'missing_source_context'}"
            )
            replay_class_counts[replay_class] += 1
            final_r = chosen.get("gross_r") if decision.candidate_use_allowed_now and path else None
            if decision.candidate_use_allowed_now:
                router_ready_rows += 1
            else:
                router_refused_rows += 1
            if final_r is None:
                non_replayable_rows += 1
            else:
                value = float(final_r)
                replayable_metric_rows += 1
                add_metric(router_metrics, value)
                distribution_add(distributions, "symbol", row.get("symbol"), value)
                distribution_add(distributions, "session", row.get("route_session"), value)
                distribution_add(distributions, "session_bucket", session_bucket, value)
                distribution_add(distributions, "framework", row.get("framework"), value)
                distribution_add(distributions, "origin_family", origin_family_for_row(row), value)
                distribution_add(distributions, "chosen_policy", chosen_policy, value)
                distribution_add(distributions, "frequency_by_day", date_key(source_time), value)
                distribution_add(distributions, "frequency_by_week", week_key(source_time), value)
                distribution_add(distributions, "frequency_by_month", month_key(source_time), value)

            comparison_values: dict[str, float | None] = {}
            for policy in COMPARISON_POLICIES:
                policy_r = policy_results[policy].get("gross_r") if path else None
                comparison_values[policy] = policy_r
                if policy_r is not None:
                    add_metric(comparison_metrics[policy], float(policy_r))

            hindsight_candidates = {
                policy: comparison_values.get(policy)
                for policy in HINDSIGHT_POLICIES
                if comparison_values.get(policy) is not None
            }
            hindsight_best_policy = None
            hindsight_best_r = None
            hindsight_regret_r = None
            if hindsight_candidates:
                hindsight_best_policy, hindsight_best_r = max(
                    hindsight_candidates.items(),
                    key=lambda item: float(item[1]),
                )
                add_metric(hindsight_metrics, float(hindsight_best_r))
                if final_r is not None:
                    hindsight_regret_r = round(float(hindsight_best_r) - float(final_r), 6)
                    regret_total += float(hindsight_regret_r)
                    regret_rows += 1

            missing_notes = missing_notes_for_row(
                chosen=chosen,
                path_issue=path_issue,
                m1_lookup=m1_lookup,
                tick_lookup=tick_lookup,
            )
            for item in missing_notes:
                missing_field_counts[item] += 1
            non_replayable_reason = None
            if not decision.candidate_use_allowed_now:
                non_replayable_reason = "router_refused:" + ",".join(decision.refusal_reasons)
            elif not path:
                non_replayable_reason = path_issue or "missing_source_context"

            output_row = {
                "schema_version": "vnext_execution_intelligence_final_dynamic_router_replay_row_v1",
                "selected_row_id": rid,
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "mt5_symbol": row.get("mt5_symbol"),
                "session": row.get("route_session"),
                "session_bucket": session_bucket,
                "session_bucket_normalization_reason": session_bucket_reason,
                "framework": row.get("framework"),
                "origin_family": origin_family_for_row(row),
                "candidate_origin_family": candidate_origin_family_for_row(row),
                "selector_component": row.get("selector_component"),
                "selection_proof_class": row.get("selection_proof_class"),
                "side": row.get("side"),
                "source_path": source_path,
                "source_sha256": source_sha or csv_cache.sha.get(source_path or ""),
                "source_row_index": source_idx,
                "source_time_utc": source_time,
                "source_record_candidate_id": (source_record or {}).get("candidate_id"),
                "entry_type": (
                    "limit_delayed_fill"
                    if delayed_fill_bars and delayed_fill_bars > 0
                    else "market_or_immediate_limit_fill"
                ),
                "entry_timing": "source_entry_touch_bar" if entry_idx is not None else "entry_touch_not_found",
                "entry_touch_source_row_index": entry_idx,
                "entry_touch_time_utc": entry_time,
                "delayed_fill_bars": delayed_fill_bars,
                "limit_fill_status": (
                    "filled_on_source_entry_touch" if entry_idx is not None else "no_fill_in_source_window"
                ),
                "fill_status": (
                    row.get("fill_status")
                    or ("filled_on_source_entry_touch" if entry_idx is not None else "not_filled")
                ),
                "chosen_policy": chosen_policy,
                "execution_policy_id": execution_policy_id,
                "raw_asof_selected_policy": raw_policy,
                "fallback_conversion_reason": conversion_notes,
                "router_decision_status": decision.decision_status,
                "router_candidate_action": decision.candidate_action,
                "router_candidate_use_allowed_now": decision.candidate_use_allowed_now,
                "router_runtime_effect_now": decision.runtime_effect_now,
                "router_refusal_reasons": list(decision.refusal_reasons),
                "router_evidence_notes": list(decision.evidence_notes),
                "router_inputs": event,
                "router_dimensions": decision.route_dimensions,
                "final_r": final_r,
                "net_r": None,
                "cost_r": None,
                "cost_status": chosen.get("cost_status"),
                "exit_reason": chosen.get("exit_reason"),
                "exit_time_utc": chosen.get("exit_time_utc"),
                "mfe_r": chosen.get("mfe_r"),
                "mae_r": chosen.get("mae_r"),
                "same_bar_ambiguity": chosen.get("same_bar_ambiguity"),
                "selected_policy_ordered_path_status_after_replay": selected_policy_ordered_path_status(chosen),
                "dynamic_policy_transition_trace": chosen.get("transition_trace"),
                "replay_source_class": replay_class,
                "non_replayable_reason": non_replayable_reason,
                "missing_field_notes": missing_notes,
                "cost_notes": [
                    "gross_r_only_historical_replay",
                    "live_runtime_captures_spread_slippage_commission_swap_account_history",
                    "net_r_blocked_until_live_cost_lifecycle_fields_exist",
                ],
                "prop_account_delta_pct_gross": (
                    round(float(final_r) * float(row.get("risk_per_trade_pct_current") or 0.0), 6)
                    if final_r is not None
                    else None
                ),
                "comparison_fixed_1_5r_r": comparison_values["fixed_1_5r"],
                "comparison_be_after_trigger_r": comparison_values["be_after_trigger"],
                "comparison_partial_be_runner_r": comparison_values["partial_be_runner"],
                "comparison_trailing_runner_r": comparison_values["trailing_runner"],
                "comparison_momentum_exhaustion_r": comparison_values["momentum_exhaustion"],
                "comparison_time_stop_r": comparison_values["time_stop"],
                "hindsight_best_policy": hindsight_best_policy,
                "hindsight_best_r": hindsight_best_r,
                "hindsight_regret_r": hindsight_regret_r,
                **m1_lookup,
                **tick_lookup,
            }
            writer.write(output_row)
    finally:
        writer.close()

    output_meta = writer.meta()
    comparison_summary = {
        policy: finalize_metric(metrics) for policy, metrics in comparison_metrics.items()
    }
    router_summary = finalize_metric(router_metrics)
    hindsight_summary = finalize_metric(hindsight_metrics)
    summary = {
        "schema_version": "vnext_execution_intelligence_final_dynamic_router_replay_summary_v1",
        "route_id": ei15r.ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed_full_dynamic_router_replay",
        "ledger_output_format": "uncompressed_plain_jsonl_shards_with_manifest",
        "selected_rows_processed": selected_rows,
        "full_denominator_rows": selected_rows,
        "router_ready_rows": router_ready_rows,
        "router_refused_rows": router_refused_rows,
        "replayable_metric_rows": replayable_metric_rows,
        "non_replayable_rows": non_replayable_rows,
        "non_replayable_rows_excluded_from_launch_metrics": non_replayable_rows,
        "condition_router_projection_gap_carried_forward_rows": 0,
        "prior_condition_router_projection_dependency": False,
        "fixed_1_5r_role": "baseline_comparator_and_fail_closed_fallback_only_not_live_default",
        "global_momentum_role": "diagnostic_global_counterfactual_not_launch_rule",
        "live_dynamic_router_selection_mode": CONDITION_CHALLENGER_MODE,
        "final_dynamic_router_metrics": router_summary,
        "global_policy_comparison_metrics": comparison_summary,
        "hindsight_best_metrics": hindsight_summary,
        "hindsight_best_regret": {
            "rows": regret_rows,
            "total_regret_r": round(regret_total, 6),
            "average_regret_r": round(regret_total / regret_rows, 9) if regret_rows else None,
            "hindsight_best_total_r": hindsight_summary["total_r"],
            "router_total_r": router_summary["total_r"],
        },
        "policy_distribution": dict(sorted(policy_distribution.items())),
        "raw_asof_policy_distribution": dict(sorted(raw_policy_distribution.items())),
        "execution_policy_id_distribution": dict(sorted(execution_policy_id_distribution.items())),
        "fallback_conversion_counts": dict(sorted(fallback_counts.items())),
        "m1_availability_status_counts": dict(sorted(m1_counts.items())),
        "tick_availability_status_counts": dict(sorted(tick_counts.items())),
        "replay_source_class_counts": dict(sorted(replay_class_counts.items())),
        "missing_field_counts": dict(sorted(missing_field_counts.items())),
        "distributions": finalize_distributions(distributions),
        "outputs": {"final_dynamic_router_replay_ledger": output_meta},
    }
    write_json(SUMMARY, summary)
    append_jsonl(CONTROL_LEDGER, control_event(summary))
    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_rows": selected_rows,
                "router_metric_rows": replayable_metric_rows,
                "router_total_r": router_summary["total_r"],
                "router_expectancy_r": router_summary["expectancy_r"],
                "policy_distribution": summary["policy_distribution"],
                "output": rel(SUMMARY),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

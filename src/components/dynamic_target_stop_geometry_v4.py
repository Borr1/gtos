"""Source-bound dynamic target/stop/thesis-horizon geometry contract.

The helpers in this module are pure runtime contract builders. They do not
read files, call MT5, call vendors, or mutate broker state. They bind the
already-selected moonshot execution policy to as-of target/stop geometry and
the prospective SLTP lifecycle capture requirements that Wave2 proved missing.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

TARGET_STOP_GEOMETRY_V4_SCHEMA_VERSION = (
    "gtos_dynamic_target_stop_thesis_horizon_geometry_v4"
)
TARGET_STOP_GEOMETRY_V4_POLICY_ID = (
    "wave3_dynamic_target_stop_thesis_horizon_geometry_v4"
)
TARGET_STOP_GEOMETRY_V4_EVIDENCE_CLASS = (
    "production_code_integration_source_bound_geometry_contract"
)
TARGET_STOP_GEOMETRY_V4_RESULT_USE_STATUS = (
    "runtime_geometry_contract_not_broker_real_outcome"
)

SLTP_LIFECYCLE_REQUIRED_EVENTS: tuple[str, ...] = (
    "broker_order_ticket",
    "broker_deal_ticket",
    "every_sltp_modify_event",
    "be_move_event",
    "trailing_stop_update_event",
    "partial_close_ticket_bound_trigger",
    "software_exit_policy_clock",
    "position_close_reason",
)

FORBIDDEN_GEOMETRY_V4_FUTURE_FIELDS: tuple[str, ...] = (
    "actual_r",
    "broker_real_pnl_cash",
    "broker_real_pnl",
    "comparison_be_after_trigger_r",
    "comparison_fixed_1_5r_r",
    "comparison_momentum_exhaustion_r",
    "comparison_partial_be_runner_r",
    "comparison_time_stop_r",
    "comparison_trailing_runner_r",
    "final_r",
    "gross_r",
    "hindsight_best_policy",
    "hindsight_best_r",
    "hindsight_regret_r",
    "mae_r",
    "mfe_r",
    "net_pnl",
    "pnl_cash",
    "pnl_dollars",
    "realized_r",
    "selected_policy_final_r",
    "static_stage04_r",
)

POLICY_DEFAULTS: dict[str, dict[str, Any]] = {
    "be_after_trigger": {
        "trigger_key": "moonshot_dynamic_execution_router_be_trigger_r",
        "final_key": "moonshot_dynamic_execution_router_be_final_target_r",
        "time_stop_key": "moonshot_dynamic_execution_router_be_time_stop_bars",
        "default_trigger_r": 1.0,
        "default_final_target_r": 1.5,
        "target_model": "breakeven_after_trigger_then_final_destination",
        "management_model": "move_stop_to_breakeven_after_trigger",
    },
    "partial_be_runner": {
        "trigger_key": "moonshot_dynamic_execution_router_partial_trigger_r",
        "final_key": "moonshot_dynamic_execution_router_partial_final_target_r",
        "time_stop_key": "moonshot_dynamic_execution_router_partial_time_stop_bars",
        "default_trigger_r": 1.0,
        "default_final_target_r": 3.0,
        "partial_ratio_key": "moonshot_dynamic_execution_router_partial_close_ratio",
        "default_partial_close_ratio": 0.5,
        "target_model": "partial_close_then_be_runner_destination",
        "management_model": "partial_close_then_move_stop_to_breakeven_runner",
    },
    "trailing_runner": {
        "trigger_key": "moonshot_dynamic_execution_router_trailing_trigger_r",
        "final_key": "moonshot_dynamic_execution_router_trailing_final_target_r",
        "time_stop_key": "moonshot_dynamic_execution_router_trailing_time_stop_bars",
        "default_trigger_r": 1.0,
        "default_final_target_r": 3.0,
        "trail_gap_key": "moonshot_dynamic_execution_router_trailing_gap_r",
        "default_trail_gap_r": 0.5,
        "target_model": "trailing_runner_with_final_cap_destination",
        "management_model": "raise_stop_by_mfe_trailing_gap_after_trigger",
    },
    "momentum_exhaustion": {
        "trigger_key": "moonshot_dynamic_execution_router_momentum_trigger_r",
        "final_key": "moonshot_dynamic_execution_router_momentum_final_target_r",
        "time_stop_key": "moonshot_dynamic_execution_router_momentum_time_stop_bars",
        "default_trigger_r": 1.0,
        "default_final_target_r": 2.0,
        "pullback_key": "moonshot_dynamic_execution_router_momentum_pullback_r",
        "default_pullback_r": 0.4,
        "target_model": "momentum_exhaustion_pullback_destination",
        "management_model": "exit_on_mfe_pullback_or_final_cap",
    },
    "time_stop": {
        "trigger_key": "moonshot_dynamic_execution_router_time_stop_target_r",
        "final_key": "moonshot_dynamic_execution_router_time_stop_target_r",
        "time_stop_key": "moonshot_dynamic_execution_router_time_stop_bars",
        "default_trigger_r": 1.5,
        "default_final_target_r": 1.5,
        "default_time_stop_bars": 32,
        "target_model": "time_stop_horizon_destination",
        "management_model": "time_stop_or_target_horizon",
    },
}


def _runtime_cfg(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    runtime = config.get("gtos_vnext_runtime", config)
    return runtime if isinstance(runtime, Mapping) else {}


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _as_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _lower_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _no_broker_take_profit(params: Mapping[str, Any]) -> bool:
    mode = _lower_text(params.get("gtos_vnext_dynamic_broker_take_profit_mode"))
    return mode in {"none", "no_tp", "targetless"} or _truthy(
        params.get("gtos_vnext_dynamic_no_broker_take_profit")
    )


def target_price_from_r(
    *,
    direction: Any,
    entry_price: Any,
    risk_distance: Any,
    target_r: Any,
) -> float | None:
    """Return the target price for an R multiple when inputs are source-bound."""
    direction_key = str(direction or "").strip().upper()
    entry = _safe_float(entry_price)
    distance = _safe_float(risk_distance)
    target = _safe_float(target_r)
    if direction_key not in {"LONG", "SHORT"}:
        return None
    if entry is None or distance is None or target is None or distance <= 0:
        return None
    if direction_key == "LONG":
        return entry + (target * distance)
    return entry - (target * distance)


def policy_geometry_defaults(
    config: Mapping[str, Any] | None,
    selected_policy: str | None,
) -> dict[str, Any]:
    """Resolve configured policy R defaults without using outcome fields."""
    cfg = _runtime_cfg(config)
    policy = _lower_text(selected_policy) or _lower_text(
        cfg.get("moonshot_dynamic_execution_router_policy")
    )
    definition = POLICY_DEFAULTS.get(policy, POLICY_DEFAULTS["momentum_exhaustion"])
    pending: list[tuple[str, str]] = []
    kinds = {
        "trigger_r": "float",
        "final_target_r": "float",
        "time_stop_bars": "int",
        "momentum_pullback_r": "float",
        "partial_close_ratio": "float",
        "trail_gap_r": "float",
    }
    resolved = {
        "trigger_r": _resolve_configured_number(
            cfg, definition["trigger_key"], definition["default_trigger_r"], "trigger_r", "float", pending
        ),
        "final_target_r": _resolve_configured_number(
            cfg,
            definition["final_key"],
            definition["default_final_target_r"],
            "final_target_r",
            "float",
            pending,
        ),
        "time_stop_bars": _resolve_configured_number(
            cfg,
            definition["time_stop_key"],
            definition.get("default_time_stop_bars"),
            "time_stop_bars",
            "int",
            pending,
        ),
        "momentum_pullback_r": _resolve_configured_number(
            cfg,
            definition.get("pullback_key"),
            definition.get("default_pullback_r"),
            "momentum_pullback_r",
            "float",
            pending,
        ),
        "partial_close_ratio": _resolve_configured_number(
            cfg,
            definition.get("partial_ratio_key"),
            definition.get("default_partial_close_ratio"),
            "partial_close_ratio",
            "float",
            pending,
        ),
        "trail_gap_r": _resolve_configured_number(
            cfg,
            definition.get("trail_gap_key"),
            definition.get("default_trail_gap_r"),
            "trail_gap_r",
            "float",
            pending,
        ),
    }
    unset = _fill_pending(
        resolved,
        pending,
        kinds,
        "dynamic_target_stop.policy_defaults",
        {"selected_policy": policy},
    )
    return {
        "selected_policy": policy,
        "trigger_r": resolved["trigger_r"],
        "final_target_r": resolved["final_target_r"],
        "time_stop_bars": resolved["time_stop_bars"],
        "target_model": definition["target_model"],
        "management_model": definition["management_model"],
        "momentum_pullback_r": resolved["momentum_pullback_r"],
        "partial_close_ratio": resolved["partial_close_ratio"],
        "trail_gap_r": resolved["trail_gap_r"],
        "bounds_unset": unset,
    }


def _geometry_on_challenge() -> bool:
    try:
        from src.components.broker_net_cost_engine import _on_challenge
    except Exception:
        return False
    try:
        return bool(_on_challenge())
    except Exception:
        return False


def _challenge_numbers(
    spot: str,
    facts: dict[str, Any],
    questions: dict[str, str],
) -> dict[str, float | None]:
    if not questions:
        return {}
    try:
        from src.components.broker_net_cost_engine import _challenge_scores
    except Exception:
        return {name: None for name in questions}
    try:
        return _challenge_scores(spot, facts, questions)
    except Exception:
        return {name: None for name in questions}


def _resolve_configured_number(
    cfg: Mapping[str, Any],
    key: str | None,
    default: Any,
    name: str,
    kind: str,
    pending: list[tuple[str, str]],
) -> Any:
    """Config value, else the historical constant off Challenge.

    On the Challenge writer a missing config value is one Score. An empty
    score stays None and is named later as a source gap.
    """

    if not key:
        return None
    if key in cfg and cfg.get(key) not in (None, ""):
        parsed = _safe_int(cfg.get(key)) if kind == "int" else _safe_float(cfg.get(key))
        return parsed
    if default is None or not _geometry_on_challenge():
        if kind == "int":
            return _safe_int(default)
        return _safe_float(default)
    pending.append(
        (
            name,
            f"The score you return is {name} for this geometry state. "
            "An empty score leaves it unset and is not a send.",
        )
    )
    return None


def _fill_pending(
    resolved: dict[str, Any],
    pending: list[tuple[str, str]],
    kinds: dict[str, str],
    spot: str,
    facts: dict[str, Any],
) -> tuple[str, ...]:
    if not pending:
        return ()
    got = _challenge_numbers(spot, facts, {name: text for name, text in pending})
    unset: list[str] = []
    for name, _text in pending:
        number = got.get(name)
        if number is None:
            unset.append(name)
            continue
        resolved[name] = int(number) if kinds.get(name) == "int" else float(number)
    return tuple(unset)


def _collect_forbidden_future_field_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    forbidden = set(FORBIDDEN_GEOMETRY_V4_FUTURE_FIELDS)
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if _lower_text(key) in forbidden:
                found.append(path)
            found.extend(_collect_forbidden_future_field_paths(child, path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        children = value if _geometry_on_challenge() else value[:100]
        for index, child in enumerate(children):
            found.extend(_collect_forbidden_future_field_paths(child, f"{prefix}[{index}]"))
    return sorted(dict.fromkeys(found))


def build_target_stop_geometry_v4_contract(
    *,
    config: Mapping[str, Any] | None,
    selected_policy: str | None,
    execution_policy_id: str | None = None,
    source_event: Mapping[str, Any] | None = None,
    router_record: Mapping[str, Any] | None = None,
    trade_params: Mapping[str, Any] | None = None,
    prior_contract: Mapping[str, Any] | None = None,
    entry_price: Any = None,
    stop_loss: Any = None,
    direction: Any = None,
    risk_distance: Any = None,
    trigger_r: Any = None,
    final_target_r: Any = None,
    trigger_price: Any = None,
    final_target_price: Any = None,
    stage: str = "router_decision",
) -> dict[str, Any]:
    """Build the Wave3 V4 dynamic target/stop/thesis-horizon contract."""
    cfg = _runtime_cfg(config)
    source = source_event if isinstance(source_event, Mapping) else {}
    router = router_record if isinstance(router_record, Mapping) else {}
    params = trade_params if isinstance(trade_params, Mapping) else {}
    prior = prior_contract if isinstance(prior_contract, Mapping) else {}
    prior_source = prior.get("source_completeness") if prior else {}
    if not isinstance(prior_source, Mapping):
        prior_source = {}
    policy_defaults = policy_geometry_defaults(config, selected_policy)
    policy = _lower_text(selected_policy) or policy_defaults["selected_policy"]
    no_broker_take_profit = _no_broker_take_profit(params)
    targetless_exit = no_broker_take_profit and policy in {"time_stop", "trailing_runner"}
    resolved_trigger_r = _safe_float(
        _first_present(trigger_r, params.get("gtos_vnext_dynamic_be_trigger_r"))
    )
    if resolved_trigger_r is None:
        resolved_trigger_r = policy_defaults["trigger_r"]
    resolved_final_target_r = _safe_float(
        _first_present(final_target_r, params.get("gtos_vnext_dynamic_final_target_r"))
    )
    if resolved_final_target_r is None and not targetless_exit:
        resolved_final_target_r = policy_defaults["final_target_r"]
    resolved_time_stop_bars = _safe_int(
        _first_present(
            params.get("gtos_vnext_dynamic_time_stop_bars"),
            policy_defaults["time_stop_bars"],
        )
    )
    resolved_momentum_pullback_r = _safe_float(
        _first_present(
            params.get("gtos_vnext_dynamic_momentum_pullback_r"),
            params.get("momentum_pullback_r"),
            policy_defaults["momentum_pullback_r"],
        )
    )
    resolved_partial_close_ratio = _safe_float(
        _first_present(
            params.get("gtos_vnext_dynamic_partial_close_ratio"),
            params.get("partial_close_ratio"),
            policy_defaults["partial_close_ratio"],
        )
    )
    resolved_trail_gap_r = _safe_float(
        _first_present(
            params.get("gtos_vnext_dynamic_trail_gap_r"),
            params.get("trail_gap_r"),
            policy_defaults["trail_gap_r"],
        )
    )
    horizon_pending: list[tuple[str, str]] = []
    horizon_resolved = {
        "thesis_horizon_m15_bars": _resolve_configured_number(
            cfg,
            "moonshot_dynamic_target_stop_geometry_v4_default_thesis_horizon_m15_bars",
            32,
            "thesis_horizon_m15_bars",
            "int",
            horizon_pending,
        ),
        "stale_review_m15_bars": _resolve_configured_number(
            cfg,
            "moonshot_dynamic_target_stop_geometry_v4_stale_review_m15_bars",
            24,
            "stale_review_m15_bars",
            "int",
            horizon_pending,
        ),
    }
    horizon_unset = _fill_pending(
        horizon_resolved,
        horizon_pending,
        {"thesis_horizon_m15_bars": "int", "stale_review_m15_bars": "int"},
        "dynamic_target_stop.horizon",
        {"selected_policy": policy},
    )
    thesis_horizon_m15_bars = horizon_resolved["thesis_horizon_m15_bars"]
    stale_review_m15_bars = horizon_resolved["stale_review_m15_bars"]

    resolved_entry = _safe_float(
        _first_present(entry_price, params.get("entry_price"), source.get("entry_price"))
    )
    resolved_stop = _safe_float(
        _first_present(stop_loss, params.get("stop_loss"), source.get("stop_loss"))
    )
    resolved_direction = str(
        _first_present(direction, params.get("direction"), source.get("direction"), source.get("side"))
        or ""
    ).strip().upper()
    resolved_risk_distance = _safe_float(risk_distance)
    if (
        resolved_risk_distance is None
        and resolved_entry is not None
        and resolved_stop is not None
    ):
        resolved_risk_distance = abs(resolved_entry - resolved_stop)

    resolved_trigger_price = _safe_float(
        _first_present(
            trigger_price,
            params.get("gtos_vnext_dynamic_be_trigger_price"),
        )
    )
    if resolved_trigger_price is None:
        resolved_trigger_price = target_price_from_r(
            direction=resolved_direction,
            entry_price=resolved_entry,
            risk_distance=resolved_risk_distance,
            target_r=resolved_trigger_r,
        )
    resolved_final_target_price = _safe_float(
        _first_present(
            final_target_price,
            params.get("gtos_vnext_dynamic_final_target_price"),
        )
    )
    if resolved_final_target_price is None and not targetless_exit:
        resolved_final_target_price = target_price_from_r(
            direction=resolved_direction,
            entry_price=resolved_entry,
            risk_distance=resolved_risk_distance,
            target_r=resolved_final_target_r,
        )

    source_status = str(
        source.get("source_path_feature_status")
        or prior_source.get("source_path_feature_status")
        or ""
    ).strip()
    source_window_complete = source.get("source_window_complete")
    if source_window_complete in (None, ""):
        source_window_complete = prior_source.get("source_window_complete")
    ordered_path_status = str(
        source.get("ordered_path_status")
        or prior_source.get("ordered_path_status")
        or ""
    ).strip()
    selected_path_status = str(
        source.get("selected_policy_ordered_path_status")
        or prior_source.get("selected_policy_ordered_path_status")
        or ordered_path_status
        or ""
    ).strip()
    same_bar_ambiguous = source.get("selected_policy_same_bar_ambiguous")
    if same_bar_ambiguous in (None, ""):
        same_bar_ambiguous = prior_source.get("selected_policy_same_bar_ambiguous")
    if same_bar_ambiguous in (None, ""):
        selected_key = selected_path_status.lower()
        same_bar_ambiguous = (
            "same_bar_ambiguous" in selected_key
            or "requires_ltf_or_tick" in selected_key
            or selected_key == "ambiguous"
        )
    else:
        same_bar_ambiguous = _truthy(same_bar_ambiguous)

    missing_source_fields: list[str] = []
    if not source_status or "asof" not in source_status.lower():
        missing_source_fields.append("source_path_feature_status_asof")
    if source_window_complete is False:
        missing_source_fields.append("complete_source_window")
    if same_bar_ambiguous:
        missing_source_fields.append("ordered_ltf_or_tick_selected_policy_path")
    if resolved_entry is None:
        missing_source_fields.append("entry_price")
    if resolved_stop is None:
        missing_source_fields.append("stop_loss")
    if resolved_risk_distance is None or resolved_risk_distance <= 0:
        missing_source_fields.append("positive_risk_distance")
    if resolved_direction not in {"LONG", "SHORT"}:
        missing_source_fields.append("direction")
    if (
        not targetless_exit
        and (resolved_final_target_r is None or resolved_final_target_r <= 0)
    ):
        missing_source_fields.append("positive_final_target_r")
    if policy == "momentum_exhaustion" and (
        resolved_momentum_pullback_r is None or resolved_momentum_pullback_r <= 0
    ):
        missing_source_fields.append("momentum_pullback_r")
    if policy == "partial_be_runner" and (
        resolved_partial_close_ratio is None
        or resolved_partial_close_ratio <= 0
        or resolved_partial_close_ratio >= 1
    ):
        missing_source_fields.append("partial_close_ratio")
    if policy == "trailing_runner" and (
        resolved_trail_gap_r is None or resolved_trail_gap_r <= 0
    ):
        missing_source_fields.append("trail_gap_r")
    for unset_name in tuple(policy_defaults.get("bounds_unset") or ()) + tuple(horizon_unset):
        missing_source_fields.append(unset_name)

    forbidden_paths = sorted(
        dict.fromkeys(
            _collect_forbidden_future_field_paths(source, "source_event")
            + _collect_forbidden_future_field_paths(params, "trade_params")
            + _collect_forbidden_future_field_paths(router, "router_record")
        )
    )
    source_complete = not missing_source_fields and not forbidden_paths
    status = (
        "source_bound_geometry_contract_ready"
        if source_complete
        else "geometry_source_gap_requires_repair"
    )
    if not policy:
        status = "dynamic_policy_not_selected"

    policy_id = str(
        cfg.get(
            "moonshot_dynamic_target_stop_geometry_v4_policy_id",
            TARGET_STOP_GEOMETRY_V4_POLICY_ID,
        )
        or TARGET_STOP_GEOMETRY_V4_POLICY_ID
    )
    execution_id = execution_policy_id or params.get("gtos_vnext_execution_policy_id")
    contract = {
        "schema_version": TARGET_STOP_GEOMETRY_V4_SCHEMA_VERSION,
        "policy_id": policy_id,
        "stage": stage,
        "status": status,
        "evidence_class": TARGET_STOP_GEOMETRY_V4_EVIDENCE_CLASS,
        "result_use_status": TARGET_STOP_GEOMETRY_V4_RESULT_USE_STATUS,
        "broker_runtime_change_status": False,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "selected_policy": policy or None,
        "execution_policy_id": execution_id,
        "source_completeness": {
            "source_mode": source.get("source_mode"),
            "source_path_feature_status": source_status or None,
            "source_window_complete": source_window_complete,
            "ordered_path_status": ordered_path_status or None,
            "selected_policy_ordered_path_status": selected_path_status or None,
            "selected_policy_same_bar_ambiguous": bool(same_bar_ambiguous),
            "future_outcome_fields_ignored": forbidden_paths,
            "missing_source_fields": sorted(dict.fromkeys(missing_source_fields)),
            "source_complete": source_complete,
        },
        "stop_invalidation": {
            "direction": resolved_direction or None,
            "entry_price": resolved_entry,
            "stop_loss": resolved_stop,
            "risk_distance": resolved_risk_distance,
            "invalidation_type": "broker_protective_stop_loss",
            "invalidation_role": "initial_thesis_invalidated_at_stop",
            "stop_evidence_class": "asof_trade_parameters_or_fill_bound_geometry",
            "broker_mutation_allowed_by_contract": False,
        },
        "target_destination": {
            "target_model": (
                "targetless_time_stop_horizon_no_broker_tp"
                if targetless_exit and policy == "time_stop"
                else (
                    "capless_trailing_runner_no_broker_tp"
                    if targetless_exit and policy == "trailing_runner"
                    else policy_defaults["target_model"]
                )
            ),
            "management_model": policy_defaults["management_model"],
            "promoted_policy_family": "momentum_primary_partial_exception_router",
            "trigger_r": resolved_trigger_r,
            "final_target_r": resolved_final_target_r,
            "broker_take_profit_mode": "none" if no_broker_take_profit else "final_target",
            "momentum_pullback_r": (
                resolved_momentum_pullback_r
                if policy == "momentum_exhaustion"
                else None
            ),
            "partial_close_ratio": (
                resolved_partial_close_ratio
                if policy == "partial_be_runner"
                else None
            ),
            "trail_gap_r": resolved_trail_gap_r if policy == "trailing_runner" else None,
            "trigger_price": resolved_trigger_price,
            "final_target_price": resolved_final_target_price,
            "target_family_id": (
                f"{policy or 'unselected'}:no_broker_tp"
                if targetless_exit
                else f"{policy or 'unselected'}:{resolved_final_target_r}R"
            ),
            "destination_role": (
                "targetless_dynamic_policy_managed_exit_not_realized_outcome"
                if targetless_exit
                else "dynamic_policy_destination_not_realized_outcome"
            ),
            "exit_management_contract_status": (
                "policy_specific_management_fields_bound"
                if policy
                and (
                    policy not in {"momentum_exhaustion", "partial_be_runner", "trailing_runner"}
                    or (
                        policy == "momentum_exhaustion"
                        and resolved_momentum_pullback_r is not None
                    )
                    or (
                        policy == "partial_be_runner"
                        and resolved_partial_close_ratio is not None
                    )
                    or (
                        policy == "trailing_runner"
                        and resolved_trail_gap_r is not None
                    )
                )
                else "policy_specific_management_field_gap"
            ),
            "static_fixed_r_boundary": (
                "retired_static_1_5r_or_3r_rows_are_comparator_context_not_runtime_authority"
            ),
        },
        "thesis_horizon": {
            "horizon_m15_bars": thesis_horizon_m15_bars,
            "stale_review_m15_bars": stale_review_m15_bars,
            "time_stop_bars": resolved_time_stop_bars,
            "timeout_action": (
                "review_or_exit_requires_ticket_bound_path_and_policy_clock_capture"
            ),
            "horizon_role": "asof_thesis_expiry_contract_not_hindsight_duration_label",
        },
        "modification_lifecycle_capture": {
            "capture_status": "prospective_capture_required",
            "required_events": list(SLTP_LIFECYCLE_REQUIRED_EVENTS),
            "ticket_bound": True,
            "source_gap_basis": (
                "Wave2 SLTP lifecycle audit found initial SLTP only; every modify "
                "event, BE, trailing, partial, and software clock require forward capture."
            ),
        },
        "semantic_owner_handoffs": {
            "same_symbol_same_instrument_lifecycle_v4": {
                "dependency_status": "handoff_required_ticket_bound_lifecycle_state",
                "handoff_fields": [
                    "broker_order_ticket",
                    "position_ticket",
                    "open_trade_competition",
                    "pending_partial_be_trailing_stale_state",
                ],
            },
            "probability_debate_team_engine_v4": {
                "dependency_status": "handoff_required_numeric_action_ev",
                "handoff_fields": [
                    "long_short_no_trade_wait_scale_reduce_close_reverse_theses",
                    "uncertainty",
                    "veto_logic",
                    "missing_source_penalty",
                ],
            },
            "follow_avoid_mixed_numeric_confluence_v4": {
                "dependency_status": "handoff_required_numeric_confluence",
                "handoff_fields": [
                    "direction",
                    "strength",
                    "confidence",
                    "freshness",
                    "cost_sensitivity",
                    "source_completeness",
                ],
            },
            "wave4_wave5_ml_feature_label_store": {
                "dependency_status": "capture_requirements_only_no_posthoc_labels",
                "handoff_fields": [
                    "mfe",
                    "mae",
                    "time_to_profit",
                    "time_to_destination",
                    "giveback",
                    "stale_thesis",
                    "stop_target_efficiency",
                    "opportunity_cost",
                ],
            },
        },
        "dual_broker_no_copy_boundary": {
            "status": "broker_local_truth_required",
            "rule": (
                "redacted_account geometry, fills, cash, costs, specs, and lifecycle truth "
                "must not be copied into FTMO broker-local truth."
            ),
        },
        "prior_contract_status": prior.get("status") if prior else None,
        "refusal_reasons": _as_list(router.get("refusal_reasons")),
    }
    source_hash_material = {
        "schema_version": contract["schema_version"],
        "policy_id": contract["policy_id"],
        "stage": contract["stage"],
        "selected_policy": contract["selected_policy"],
        "execution_policy_id": contract["execution_policy_id"],
        "source_completeness": contract["source_completeness"],
        "stop_invalidation": contract["stop_invalidation"],
        "target_destination": contract["target_destination"],
        "thesis_horizon": contract["thesis_horizon"],
    }
    contract["source_event_hash_sha256"] = _stable_sha256(source_hash_material)
    contract["source_event_hash_material"] = source_hash_material
    contract["packet_hash_sha256"] = _stable_sha256(contract)
    contract["packet_hash"] = contract["packet_hash_sha256"]
    return contract

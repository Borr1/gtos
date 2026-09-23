"""Default-off moonshot dynamic execution router.

This module is a pure research/runtime contract. It does not read files, call
MT5, call paid APIs, or mutate broker state. The caller must explicitly pass
``enabled=True`` and ``apply_to_execution=True`` for the returned decision to
permit live use. Current vNext production does that through the redacted_account
profile; execution remains momentum-primary with the configured partial runner
exceptions, while retired fixed-target rows are comparator evidence only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


PRIMARY_BRANCH = "origin_current_fvg_fill"
PRIMARY_FRAMEWORK = "fvg_fill"
DEFAULT_ACTIVATED_FRAMEWORKS = ("breaker_re_entry", "fvg_fill", "ob_retest")
DEFAULT_ACTIVATED_ORIGIN_FAMILIES: tuple[str, ...] = ()
DEFAULT_REQUIRED_BRANCH_LABELS = ("FOLLOW",)
REPAIRED_BRANCH_ACTION = "MOONSHOT_REPAIRED_FOLLOW"
RETIRED_STATIC_BASELINE_COMPARATOR = "retired_static_baseline_comparator"
REJECTED_LIVE_BASELINE = RETIRED_STATIC_BASELINE_COMPARATOR
BASELINE_FIXED_POLICY = "retired_static_baseline_policy"
CONDITION_CHALLENGER_POLICY = "condition_asof_displacement_v1"
CONDITION_CHALLENGER_MODE = "condition_asof_displacement_v1"
BE_AFTER_TRIGGER_POLICY = "be_after_trigger"
PARTIAL_BE_RUNNER_POLICY = "partial_be_runner"
TRAILING_RUNNER_POLICY = "trailing_runner"
MOMENTUM_EXHAUSTION_POLICY = "momentum_exhaustion"
TIME_STOP_POLICY = "time_stop"
DEFAULT_POLICY = MOMENTUM_EXHAUSTION_POLICY
SAFE_FALLBACK_POLICY = MOMENTUM_EXHAUSTION_POLICY
EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES = (
    "cross_asset_lead_lag",
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "regime_transition_break",
    "session_open_range_break",
    "volatility_compression_expansion",
)
SUPPORTED_LIVE_EXECUTION_POLICIES = (
    BE_AFTER_TRIGGER_POLICY,
    PARTIAL_BE_RUNNER_POLICY,
    TRAILING_RUNNER_POLICY,
    MOMENTUM_EXHAUSTION_POLICY,
    TIME_STOP_POLICY,
)
EXECUTION_POLICY_IDS = {
    BE_AFTER_TRIGGER_POLICY: "vnext_exec_be_after_trigger_1r_to_15r",
    PARTIAL_BE_RUNNER_POLICY: "vnext_exec_partial_50_at_1r_be_runner_to_3r",
    TRAILING_RUNNER_POLICY: "vnext_exec_trailing_1r_gap_05r_cap_3r",
    MOMENTUM_EXHAUSTION_POLICY: "vnext_exec_momentum_1r_pullback_04r_cap_2r",
    TIME_STOP_POLICY: "vnext_exec_time_stop_m15_bars",
    BASELINE_FIXED_POLICY: "fallback_static_baseline_comparator_only",
}

DEFAULT_CANDIDATE_QUALITY_SELECTOR_RULES: tuple[dict[str, Any], ...] = ()

# Frozen segment exit-policy tournament families -> currently wired live
# policy names. The tournament artifact (exit_policy_segment_table_v1) carries
# tournament policy ids/families; only promoted resolutions that map onto an
# already-supported live policy may steer the router, and tournament params
# travel as provenance via ``selected_policy_params`` (never as a new policy).
SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY = {
    "incumbent": MOMENTUM_EXHAUSTION_POLICY,
    "momentum": MOMENTUM_EXHAUSTION_POLICY,
    "trailing": TRAILING_RUNNER_POLICY,
    "fixed_target": BE_AFTER_TRIGGER_POLICY,
    "be_only": BE_AFTER_TRIGGER_POLICY,
    "time_stop": TIME_STOP_POLICY,
}

LEGACY_ASOF_DISPLACEMENT_POLICY_MAP = {
    ("breaker_re_entry", "london_broad", "low_disp"): BASELINE_FIXED_POLICY,
    ("breaker_re_entry", "ny_broad", "high_disp"): MOMENTUM_EXHAUSTION_POLICY,
    ("breaker_re_entry", "ny_broad", "low_disp"): PARTIAL_BE_RUNNER_POLICY,
    ("breaker_re_entry", "off_kz_broad", "low_disp"): PARTIAL_BE_RUNNER_POLICY,
    ("fvg_fill", "london_broad", "high_disp"): TRAILING_RUNNER_POLICY,
    ("fvg_fill", "ny_broad", "high_disp"): TRAILING_RUNNER_POLICY,
    ("fvg_fill", "off_kz_broad", "high_disp"): TRAILING_RUNNER_POLICY,
    ("fvg_fill", "tokyo_broad", "high_disp"): TRAILING_RUNNER_POLICY,
    ("ob_retest", "london_broad", "low_disp"): MOMENTUM_EXHAUSTION_POLICY,
    ("ob_retest", "ny_broad", "low_disp"): BASELINE_FIXED_POLICY,
    ("ob_retest", "off_kz_broad", "low_disp"): PARTIAL_BE_RUNNER_POLICY,
    ("ob_retest", "tokyo_broad", "high_disp"): BASELINE_FIXED_POLICY,
    ("ob_retest", "tokyo_broad", "low_disp"): MOMENTUM_EXHAUSTION_POLICY,
}
ASOF_DISPLACEMENT_POLICY_MAP = LEGACY_ASOF_DISPLACEMENT_POLICY_MAP

FORBIDDEN_FUTURE_OUTCOME_FIELDS = (
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
    "selected_policy_final_r",
    "static_stage04_r",
)


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _lower(value: Any) -> str:
    return _text(value).strip().lower()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _lower(value) in {"1", "true", "yes", "y"}


def _iter_text_values(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    try:
        return tuple(str(part).strip() for part in value if str(part).strip())
    except TypeError:
        text = str(value).strip()
        return (text,) if text else ()


def _upper_values(value: Any, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    values = _iter_text_values(value)
    if not values:
        values = default
    return tuple(dict.fromkeys(item.upper() for item in values if item))


def _lower_values(value: Any, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    values = _iter_text_values(value)
    if not values:
        values = default
    return tuple(dict.fromkeys(item.lower() for item in values if item))


def _symbol_values(value: Any) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            item.upper().replace(".", "_") for item in _iter_text_values(value) if item
        )
    )


def _float(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _symbol_key(value: Any) -> str:
    return _text(value).strip().upper().replace(".", "_")


def _session_bucket_key(value: Any) -> str:
    key = _lower(value).replace("-", "_").replace(" ", "_")
    if not key:
        return ""
    if key.endswith("_broad"):
        return key
    if key.startswith("moonshot_h"):
        hour_parts = key.removeprefix("moonshot_h").split("_")
        if len(hour_parts) == 2 and all(part.isdigit() for part in hour_parts):
            return "off_kz_broad"
    if "tokyo" in key:
        return "tokyo_broad"
    if key in {"ny", "new_york", "newyork"} or "ny" in key:
        return "ny_broad"
    if "london" in key or key in {"ldn", "lon"}:
        return "london_broad"
    if "off" in key or "dead" in key:
        return "off_kz_broad"
    return f"{key}_broad"


def _quality_rules(value: Any) -> tuple[dict[str, Any], ...]:
    if value in (None, ""):
        return tuple(dict(rule) for rule in DEFAULT_CANDIDATE_QUALITY_SELECTOR_RULES)
    if not isinstance(value, (list, tuple)):
        return tuple(dict(rule) for rule in DEFAULT_CANDIDATE_QUALITY_SELECTOR_RULES)
    rules: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        session = _session_bucket_key(
            item.get("session")
            or item.get("session_bucket")
            or item.get("route_session")
        )
        origin_family = _lower(
            item.get("origin_family") or item.get("candidate_origin_family")
        ).removeprefix("origin_").removeprefix("current_")
        framework = _lower(item.get("framework"))
        symbol = _symbol_key(item.get("symbol"))
        side = _text(item.get("side")).strip().upper()
        if not session and not origin_family and not framework and not symbol:
            continue
        rules.append(
            {
                **dict(item),
                "session": session,
                "origin_family": origin_family,
                "framework": framework,
                "symbol": symbol,
                "side": side,
            }
        )
    return tuple(rules)


def _quality_rule_action(rule: Mapping[str, Any] | None) -> str:
    if not isinstance(rule, Mapping):
        return ""
    return _lower(
        rule.get("action")
        or rule.get("candidate_quality_action")
        or rule.get("classification")
        or rule.get("selector_action")
        or "tradeable_now"
    )


def _quality_rule_specificity(rule: Mapping[str, Any]) -> int:
    return sum(
        1
        for field in ("symbol", "side", "framework", "origin_family", "session")
        if rule.get(field)
    )


def _quality_rule_priority(rule: Mapping[str, Any]) -> tuple[int, int]:
    action = _quality_rule_action(rule)
    if any(token in action for token in ("avoid", "reject", "block", "no_trade")):
        action_priority = 4
    elif "reduce" in action or "downweight" in action:
        action_priority = 3
    elif "capture" in action or "repair" in action:
        action_priority = 2
    else:
        action_priority = 1
    return action_priority, _quality_rule_specificity(rule)


def _quality_rule_matches(
    rule: Mapping[str, Any],
    *,
    event: Mapping[str, Any],
    origin_family: str,
    session_bucket: str,
    framework: str,
    symbol: str,
    side: str,
) -> bool:
    rule_session = _session_bucket_key(
        rule.get("session")
        or rule.get("session_bucket")
        or rule.get("route_session")
    )
    rule_origin = _lower(
        rule.get("origin_family") or rule.get("candidate_origin_family")
    ).removeprefix("origin_").removeprefix("current_")
    event_origin = _lower(origin_family).removeprefix("origin_").removeprefix("current_")
    rule_framework = _lower(rule.get("framework"))
    rule_symbol = _symbol_key(rule.get("symbol"))
    rule_side = _text(rule.get("side")).strip().upper()
    if rule_session and rule_session != session_bucket:
        return False
    if rule_origin and rule_origin != event_origin:
        return False
    if rule_framework and rule_framework != framework:
        return False
    if rule_symbol and rule_symbol != symbol:
        return False
    if rule_side and rule_side != side:
        return False

    risk_cell_id = _text(rule.get("risk_cell_id")).strip()
    if risk_cell_id and risk_cell_id != _text(event.get("risk_cell_id")).strip():
        return False
    return True


def _select_quality_rule(
    *,
    event: Mapping[str, Any],
    rules: tuple[dict[str, Any], ...],
    origin_family: str,
    session_bucket: str,
) -> dict[str, Any] | None:
    framework = _lower(event.get("framework") or event.get("route_family"))
    symbol = _symbol_key(event.get("symbol"))
    side = _text(event.get("side")).strip().upper()
    matches = [
        rule
        for rule in rules
        if _quality_rule_matches(
            rule,
            event=event,
            origin_family=origin_family,
            session_bucket=session_bucket,
            framework=framework,
            symbol=symbol,
            side=side,
        )
    ]
    if not matches:
        return None
    return max(matches, key=_quality_rule_priority)


def _candidate_quality_selector(
    *,
    event: Mapping[str, Any],
    origin_family: str,
    session_bucket: str,
) -> dict[str, Any]:
    enabled = _truthy(
        event.get("candidate_quality_selector_enabled")
        or event.get("moonshot_candidate_quality_selector_enabled")
    )
    apply_to_execution = _truthy(
        event.get("candidate_quality_selector_apply_to_execution")
        or event.get("moonshot_candidate_quality_selector_apply_to_execution")
    )
    rules = _quality_rules(
        event.get("candidate_quality_selector_tradeable_rules")
        or event.get("moonshot_candidate_quality_selector_tradeable_rules")
    )
    spread_r = _float(
        event.get("spread_r_at_candidate")
        or event.get("selected_cell_pretrade_spread_r")
        or event.get("pretrade_spread_r")
    )
    max_spread_r = _float(
        event.get("candidate_quality_selector_max_spread_r")
        or event.get("moonshot_candidate_quality_selector_max_spread_r")
    )
    if max_spread_r is None:
        max_spread_r = 0.20
    normalized_session_bucket = _session_bucket_key(session_bucket)
    matched_rule = _select_quality_rule(
        event=event,
        rules=rules,
        origin_family=origin_family,
        session_bucket=normalized_session_bucket,
    )
    matched_action = _quality_rule_action(matched_rule)
    if not enabled:
        classification = "not_enabled"
        refusal_reason = None
        allowed = True
    elif not rules:
        classification = "source_capture_required"
        refusal_reason = "candidate_quality_no_source_bound_selector_package"
        allowed = False
    elif matched_rule is None:
        classification = "source_capture_required"
        refusal_reason = "candidate_quality_session_origin_not_in_selected_denominator_package"
        allowed = False
    elif any(
        token in matched_action
        for token in ("avoid", "reject", "block", "no_trade")
    ):
        classification = "no_trade_by_evidence"
        refusal_reason = (
            matched_rule.get("refusal_reason")
            or "candidate_quality_negative_selected_denominator_rule"
        )
        allowed = False
    elif "capture" in matched_action or "repair" in matched_action:
        classification = "source_capture_required"
        refusal_reason = (
            matched_rule.get("refusal_reason")
            or "candidate_quality_source_capture_or_repair_required"
        )
        allowed = False
    elif spread_r is None:
        classification = "source_capture_required"
        refusal_reason = "candidate_quality_spread_r_missing_for_selected_denominator_rule"
        allowed = False
    elif spread_r >= max_spread_r:
        classification = "no_trade_by_evidence"
        refusal_reason = "candidate_quality_spread_r_exceeds_selected_denominator_limit"
        allowed = False
    elif "reduce" in matched_action or "downweight" in matched_action:
        classification = "reduce_risk_by_evidence"
        refusal_reason = None
        allowed = True
    else:
        classification = "tradeable_now"
        refusal_reason = None
        allowed = True
    return {
        "enabled": enabled,
        "apply_to_execution": apply_to_execution,
        "allowed": allowed,
        "classification": classification,
        "refusal_reason": refusal_reason,
        "matched_rule": matched_rule,
        "matched_rule_action": matched_action or None,
        "rule_count": len(rules),
        "session": normalized_session_bucket,
        "origin_family": origin_family,
        "spread_r_at_candidate": spread_r,
        "max_spread_r": max_spread_r,
        "risk_multiplier": (
            _float((matched_rule or {}).get("risk_multiplier"))
            if isinstance(matched_rule, Mapping)
            else None
        ),
        "evidence_path": event.get("candidate_quality_selector_evidence_path")
        or event.get("moonshot_candidate_quality_selector_evidence_path"),
        "package_path": event.get("candidate_quality_selector_package_path")
        or event.get("moonshot_candidate_quality_selector_package_path"),
    }


def _broker_net_cost_selector(event: Mapping[str, Any]) -> dict[str, Any]:
    packet = _mapping(
        event.get("gtos_v4_pretrade_broker_net_cost_packet")
        or event.get("gtos_vnext_pretrade_cost_model")
        or event.get("pretrade_cost_packet")
    )
    enabled = bool(packet) or _truthy(
        event.get("broker_net_cost_selector_enabled")
        or event.get("moonshot_broker_net_cost_selector_enabled")
    )
    apply_to_execution = _truthy(
        event.get("broker_net_cost_selector_apply_to_execution")
        or event.get("moonshot_broker_net_cost_selector_apply_to_execution")
    )
    packet_required = _truthy(
        event.get("broker_net_cost_packet_required")
        or event.get("moonshot_broker_net_cost_packet_required")
        or _mapping(packet.get("config_requirements")).get("packet_required")
    )
    if not enabled:
        return {
            "enabled": False,
            "apply_to_execution": False,
            "allowed": True,
            "classification": "not_enabled",
            "refusal_reason": None,
        }

    tick_cost = _mapping(packet.get("tick_cost"))
    spread_r = _float(
        event.get("broker_net_spread_r")
        or event.get("selected_cell_pretrade_spread_r")
        or packet.get("spread_r")
        or tick_cost.get("spread_r")
    )
    total_cost_r = _float(
        event.get("broker_net_total_cost_r")
        or event.get("pretrade_total_cost_r")
        or packet.get("total_cost_r")
    )
    max_spread_r = _float(
        event.get("broker_net_max_spread_r")
        or packet.get("max_spread_r")
    )
    max_total_cost_r = _float(
        event.get("broker_net_max_total_cost_r")
        or packet.get("max_total_cost_r")
    )
    packet_reasons = packet.get("refusal_reasons")
    if isinstance(packet_reasons, (list, tuple)):
        refusal_text = ";".join(str(reason) for reason in packet_reasons if reason)
    else:
        refusal_text = _text(packet.get("refusal_reason")).strip()
    packet_status = _text(packet.get("status")).strip().upper()
    cost_authority = _text(packet.get("authority") or packet.get("cost_authority"))
    cost_source_gap_status = _text(packet.get("cost_source_gap_status"))
    fallback_is_authority = _truthy(
        packet.get("candidate_cost_r_fallback_is_authority")
        or packet.get("source_gap_cost_fallback_is_authority")
    )
    source_gap_fallback_blocked = _truthy(
        packet.get("source_gap_cost_fallback_blocked")
    )

    if packet_required and not packet:
        classification = "source_capture_required"
        refusal_reason = "broker_net_pretrade_packet_missing_for_selector"
        allowed = False
    elif packet_status == "REFUSED" or refusal_text:
        classification = "no_trade_by_evidence"
        refusal_reason = f"broker_net_pretrade_packet_refused:{refusal_text or 'packet_refused'}"
        allowed = False
    elif packet and packet_status not in {"PASSED", "PASS", "OK"}:
        classification = "source_capture_required"
        refusal_reason = f"broker_net_pretrade_packet_status_not_passed:{packet_status or 'missing'}"
        allowed = False
    elif packet and cost_authority != "broker_calibrated_replay_cost":
        classification = "source_capture_required"
        refusal_reason = f"broker_net_cost_authority_not_executable:{cost_authority or 'missing'}"
        allowed = False
    elif packet and cost_source_gap_status != "source_bound_cost_authority_present":
        classification = "source_capture_required"
        refusal_reason = (
            "broker_net_cost_source_gap_not_executable:"
            f"{cost_source_gap_status or 'missing'}"
        )
        allowed = False
    elif packet and fallback_is_authority:
        classification = "source_capture_required"
        refusal_reason = "broker_net_candidate_cost_fallback_not_order_authority"
        allowed = False
    elif packet and source_gap_fallback_blocked:
        classification = "source_capture_required"
        refusal_reason = "broker_net_source_gap_cost_fallback_blocked"
        allowed = False
    elif total_cost_r is None:
        classification = "source_capture_required"
        refusal_reason = "broker_net_total_cost_r_missing_for_selector"
        allowed = False
    elif max_total_cost_r is not None and total_cost_r > max_total_cost_r:
        classification = "no_trade_by_evidence"
        refusal_reason = "broker_net_total_cost_r_exceeds_selector_limit"
        allowed = False
    elif spread_r is None:
        classification = "source_capture_required"
        refusal_reason = "broker_net_spread_r_missing_for_selector"
        allowed = False
    elif max_spread_r is not None and spread_r > max_spread_r:
        classification = "no_trade_by_evidence"
        refusal_reason = "broker_net_spread_r_exceeds_selector_limit"
        allowed = False
    else:
        classification = "tradeable_now"
        refusal_reason = None
        allowed = True

    return {
        "enabled": True,
        "apply_to_execution": apply_to_execution,
        "allowed": allowed,
        "classification": classification,
        "refusal_reason": refusal_reason,
        "packet_status": packet_status or None,
        "cost_authority": cost_authority or None,
        "cost_source_gap_status": cost_source_gap_status or None,
        "candidate_cost_r_fallback_is_authority": fallback_is_authority,
        "source_gap_cost_fallback_blocked": source_gap_fallback_blocked,
        "packet_schema_version": packet.get("schema_version"),
        "result_use_status": packet.get("result_use_status"),
        "spread_r": spread_r,
        "max_spread_r": max_spread_r,
        "total_cost_r": total_cost_r,
        "max_total_cost_r": max_total_cost_r,
        "profile_source_status": _mapping(packet.get("profile")).get("source_status"),
        "symbol_spec_source_status": _mapping(packet.get("symbol_spec")).get("source_status"),
        "swap_source_status": _mapping(packet.get("swap")).get("source_status"),
        "broker_hours_source_status": _mapping(packet.get("broker_hours")).get("source_status"),
        "runtime_effect_boundary": "selector_consumes_existing_packet_no_broker_io",
    }


def _source_status_is_live_asof_complete(value: Any) -> bool:
    source_status = _lower(value)
    if source_status.startswith("computed_from_source_ohlc_asof"):
        return True
    if source_status.startswith("raw_data_") and source_status.endswith("_asof_complete"):
        return True
    if source_status == "cross_asset_raw_data_asof_complete":
        return True
    return False


def _displacement_bucket(event: Mapping[str, Any]) -> str:
    displacement = _float(event.get("current_bar_displacement_atr14"))
    if displacement is None:
        return "missing_disp"
    return "high_disp" if displacement >= 1.0 else "low_disp"


def select_asof_displacement_policy(event: Mapping[str, Any]) -> tuple[str, str]:
    """Return the promoted as-of production policy and displacement bucket.

    The old Stage11 condition table is retained as diagnostic evidence only.
    Production routing is momentum-primary, with explicit origin-family
    exceptions that are supplied by config/event and backed by row-level replay.
    """

    framework = _lower(event.get("framework") or event.get("route_family"))
    session_bucket = _lower(event.get("session_bucket") or event.get("route_session"))
    candidate_origin_family = _lower(
        event.get("candidate_origin_family") or f"origin_current_{framework or 'unknown'}"
    )
    origin_family = candidate_origin_family.removeprefix("origin_")
    bucket = _displacement_bucket(event)
    primary_policy = _lower(
        event.get("primary_policy")
        or event.get("moonshot_dynamic_execution_router_policy")
        or DEFAULT_POLICY
    )
    if primary_policy == BASELINE_FIXED_POLICY or primary_policy not in SUPPORTED_LIVE_EXECUTION_POLICIES:
        primary_policy = DEFAULT_POLICY

    exception_policy = _lower(
        event.get("partial_exception_policy")
        or event.get("moonshot_dynamic_execution_router_momentum_exception_policy")
        or PARTIAL_BE_RUNNER_POLICY
    )
    if exception_policy not in SUPPORTED_LIVE_EXECUTION_POLICIES:
        exception_policy = PARTIAL_BE_RUNNER_POLICY
    exception_family_source = event.get("partial_exception_origin_families")
    if exception_family_source is None:
        exception_family_source = event.get(
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
        )
    exception_families = set(
        _lower_values(
            exception_family_source,
            (
                EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES
                if exception_family_source is None
                else ()
            ),
        )
    )
    if origin_family in exception_families:
        return exception_policy, bucket
    return primary_policy, bucket


def _segment_resolution_live_policy(resolution: Mapping[str, Any]) -> Optional[str]:
    """Map a frozen segment-table resolution onto a wired live policy name."""

    policy_id = _lower(resolution.get("policy_id"))
    if policy_id in SUPPORTED_LIVE_EXECUTION_POLICIES:
        return policy_id
    family = _lower(resolution.get("family"))
    if family in SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY:
        return SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY[family]
    for family_token, live_policy in SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY.items():
        if policy_id == family_token or policy_id.startswith(f"{family_token}_"):
            return live_policy
    return None


def _live_execution_policy(policy: str, evidence_notes: list[str]) -> str:
    """Normalize as-of router output to currently wired live policies."""

    normalized = _lower(policy)
    if normalized == BASELINE_FIXED_POLICY:
        evidence_notes.append(
            "retired_static_baseline_asof_cell_retained_as_comparator_only_routed_to_momentum_primary"
        )
        return SAFE_FALLBACK_POLICY
    if normalized not in SUPPORTED_LIVE_EXECUTION_POLICIES:
        evidence_notes.append(
            f"unsupported_asof_policy_{normalized or 'missing'}_routed_to_momentum_primary"
        )
        return SAFE_FALLBACK_POLICY
    return normalized


def execution_policy_id_for(policy: str | None) -> str | None:
    if not policy:
        return None
    return EXECUTION_POLICY_IDS.get(_lower(policy))


@dataclass(frozen=True)
class MoonshotPolicyRouterDecision:
    """One default-off router decision for a candidate/event."""

    enabled: bool
    apply_to_execution: bool
    decision_status: str
    candidate_action: str
    selected_branch: str
    selected_policy: Optional[str]
    execution_policy_id: Optional[str]
    replaced_policy: str
    fixed_target_role: str
    prop_action: str
    ai_role: str
    source_quality_action: str
    exit_management_action: str
    refusal_reasons: tuple[str, ...] = ()
    evidence_notes: tuple[str, ...] = ()
    router_family: str = "vnext_moonshot_default_off_dynamic_execution_router"
    runtime_effect_now: bool = False
    candidate_use_allowed_now: bool = False
    paid_api_or_vendor_call: bool = False
    broker_operation: bool = False
    owner_approval_required: bool = True
    route_dimensions: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["refusal_reasons"] = list(self.refusal_reasons)
        record["evidence_notes"] = list(self.evidence_notes)
        return record


def _prop_action(event: Mapping[str, Any]) -> str:
    """Return the default-off prop action without mutating account state."""

    governor_action = _text(event.get("prop_governor_action")).strip().upper()
    if governor_action == "BLOCK":
        return "OWNER_GATED_ACCOUNT_ABANDON_OR_RESTART"
    if governor_action == "DEFER_UNTIL_RESET":
        return "DEFER_UNTIL_RESET_OR_OWNER_RESTART"

    remaining_daily_r = _float(event.get("remaining_daily_cushion_r"))
    remaining_overall_r = _float(event.get("remaining_overall_cushion_r"))
    phase_profit_remaining_r = _float(event.get("phase_profit_remaining_r"))
    account_recovery_expectancy_r = _float(event.get("account_recovery_expectancy_r"))

    if phase_profit_remaining_r is not None and phase_profit_remaining_r <= 0:
        return "OWNER_GATED_STOP_TRADING_PHASE_TARGET_REACHED"
    if remaining_overall_r is not None and remaining_overall_r <= 0:
        return "OWNER_GATED_ACCOUNT_ABANDON_OR_RESTART"
    if remaining_daily_r is not None and remaining_daily_r <= 0:
        return "DEFER_UNTIL_RESET_OR_OWNER_RESTART"
    if (
        account_recovery_expectancy_r is not None
        and account_recovery_expectancy_r < 0
        and remaining_overall_r is not None
        and remaining_overall_r < 2.0
    ):
        return "OWNER_GATED_ACCOUNT_ABANDON_OR_RESTART"
    if (
        remaining_daily_r is not None
        and remaining_daily_r < 2.0
        or remaining_overall_r is not None
        and remaining_overall_r < 2.0
    ):
        return "REDUCE_RISK_OR_DEFER_UNTIL_RESET"
    return "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS"


def route_moonshot_dynamic_execution(
    event: Mapping[str, Any],
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> MoonshotPolicyRouterDecision:
    """Route a candidate into the default-off moonshot execution policy.

    The decision uses only as-of/event fields supplied by the caller. Research
    replay code may attach future-label outcomes after this decision for
    comparison, but this router never consumes outcome labels to choose a policy.
    """

    framework = _lower(event.get("framework") or event.get("route_family"))
    session_bucket = _lower(event.get("session_bucket") or event.get("route_session"))
    candidate_origin_family = _lower(
        event.get("candidate_origin_family") or f"origin_current_{framework or 'unknown'}"
    )
    origin_family = candidate_origin_family.removeprefix("origin_")
    branch_label = _text(
        event.get("branch_label")
        or event.get("route_decision")
        or event.get("post_l2_decision")
    ).strip().upper()
    required_branch_labels = _upper_values(
        event.get("required_branch_labels"),
        DEFAULT_REQUIRED_BRANCH_LABELS,
    )
    repaired_branch_allowed = _truthy(event.get("repaired_branch_allowed"))
    activated_frameworks = _lower_values(
        event.get("activated_frameworks"),
        DEFAULT_ACTIVATED_FRAMEWORKS,
    )
    activated_origin_families = _lower_values(
        event.get("activated_origin_families"),
        DEFAULT_ACTIVATED_ORIGIN_FAMILIES,
    )
    broader_origin_allowed = _truthy(event.get("broader_origin_allowed"))
    symbol = _text(event.get("symbol")).strip()
    symbol_key = symbol.upper().replace(".", "_")
    eligible_symbols = _symbol_values(event.get("broker_native_eligible_symbols"))
    exact_excluded_symbols = _symbol_values(event.get("broker_native_exact_excluded_symbols"))
    broker_native_eligible_value = event.get("broker_native_eligible")
    broker_native_exact_excluded = _truthy(event.get("broker_native_exact_excluded"))
    runtime_instrument_configured_value = event.get("runtime_instrument_configured")
    selected_cell_risk_required = _truthy(event.get("selected_cell_risk_required"))
    selected_cell_risk_allowed = _truthy(event.get("selected_cell_risk_allowed"))
    selected_cell_risk_pct = _float(event.get("selected_cell_risk_pct"))
    source_status = _lower(event.get("source_path_feature_status"))
    live_generation_status = _lower(event.get("live_generation_status"))
    source_mode = _text(event.get("source_mode"))
    source_window_complete = _truthy(event.get("source_window_complete"))
    ordered_path_status = _lower(event.get("ordered_path_status"))
    selected_policy_ordered_path_status = _lower(
        event.get("selected_policy_ordered_path_status") or ordered_path_status
    )
    selected_policy_same_bar_ambiguous = event.get("selected_policy_same_bar_ambiguous")
    if selected_policy_same_bar_ambiguous in (None, ""):
        selected_policy_same_bar_ambiguous = (
            "same_bar_ambiguous" in selected_policy_ordered_path_status
            or "requires_ltf_or_tick" in selected_policy_ordered_path_status
            or selected_policy_ordered_path_status == "ambiguous"
        )
    else:
        selected_policy_same_bar_ambiguous = _truthy(selected_policy_same_bar_ambiguous)
    kill_zone_position = _lower(event.get("kill_zone_position"))
    liquidity_state = _lower(event.get("liquidity_sweep_proxy_state"))
    volatility_state = _lower(event.get("volatility_state_14_vs_50"))
    trend_state = _lower(event.get("trend_state_20"))
    condition_challenger_enabled = _truthy(event.get("condition_challenger_enabled"))
    policy_router_mode = (
        _lower(event.get("policy_router_mode")) if condition_challenger_enabled else ""
    )
    require_configured_kill_zone = _truthy(event.get("require_configured_kill_zone"))
    displacement_bucket = _displacement_bucket(event)

    dimensions = {
        "symbol": event.get("symbol"),
        "side": event.get("side"),
        "framework": framework,
        "activated_frameworks": activated_frameworks,
        "activated_origin_families": activated_origin_families,
        "candidate_origin_family": candidate_origin_family,
        "origin_family": origin_family,
        "branch_label": branch_label,
        "required_branch_labels": required_branch_labels,
        "repaired_branch_allowed": repaired_branch_allowed,
        "broader_origin_allowed": broader_origin_allowed,
        "session_bucket": session_bucket,
        "current_bar_displacement_bucket": displacement_bucket,
        "source_window_complete": source_window_complete,
        "source_mode": source_mode,
        "live_generation_status": live_generation_status,
        "kill_zone_position": kill_zone_position,
        "ordered_path_status": ordered_path_status,
        "selected_policy_ordered_path_status": selected_policy_ordered_path_status,
        "selected_policy_same_bar_ambiguous": selected_policy_same_bar_ambiguous,
        "broker_native_eligible": broker_native_eligible_value,
        "broker_native_exact_excluded": broker_native_exact_excluded,
        "runtime_instrument_configured": runtime_instrument_configured_value,
        "selected_cell_risk_required": selected_cell_risk_required,
        "selected_cell_risk_allowed": selected_cell_risk_allowed,
        "selected_cell_risk_pct": selected_cell_risk_pct,
        "selected_cell_risk_cell_id": event.get("selected_cell_risk_cell_id"),
        "selected_cell_risk_decision_basis": event.get("selected_cell_risk_decision_basis"),
        "selected_cell_risk_match_reason": event.get("selected_cell_risk_match_reason"),
        "broker_native_eligible_symbols": eligible_symbols,
        "broker_native_exact_excluded_symbols": exact_excluded_symbols,
        "liquidity_sweep_proxy_state": liquidity_state,
        "volatility_state_14_vs_50": volatility_state,
        "trend_state_20": trend_state,
        "condition_challenger_enabled": condition_challenger_enabled,
        "production_primary_policy": DEFAULT_POLICY,
        "production_exception_origin_families": EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES,
        "prop_governor_action": event.get("prop_governor_action"),
    }
    future_outcome_fields_ignored = tuple(
        field for field in FORBIDDEN_FUTURE_OUTCOME_FIELDS if event.get(field) not in (None, "")
    )
    if future_outcome_fields_ignored:
        dimensions["future_outcome_fields_ignored"] = future_outcome_fields_ignored
    candidate_quality = _candidate_quality_selector(
        event=event,
        origin_family=origin_family,
        session_bucket=session_bucket,
    )
    dimensions["candidate_quality_selector"] = candidate_quality
    broker_net_cost = _broker_net_cost_selector(event)
    dimensions["broker_net_cost_selector"] = broker_net_cost

    if not enabled:
        return MoonshotPolicyRouterDecision(
            enabled=False,
            apply_to_execution=False,
            decision_status="disabled_vnext",
            candidate_action="NO_LIVE_EFFECT_VNEXT_DISABLED",
            selected_branch=PRIMARY_BRANCH,
            selected_policy=None,
            execution_policy_id=None,
            replaced_policy=REJECTED_LIVE_BASELINE,
            fixed_target_role="baseline_comparator_only",
            prop_action="NO_PROP_ACTION_DEFAULT_OFF",
            ai_role="NO_AI_CALL_DEFAULT_OFF",
            source_quality_action="NO_SOURCE_ACTION_DEFAULT_OFF",
            exit_management_action="NO_EXIT_CHANGE_DEFAULT_OFF",
            evidence_notes=("router_registered_default_off_only",),
            route_dimensions=dimensions,
        )

    refusal_reasons: list[str] = []
    evidence_notes: list[str] = [
        "retired_static_baseline_rejected_as_primary_policy_baseline",
        "retired_static_baseline_retained_as_comparator_not_target",
        "momentum_exhaustion_promoted_as_primary_production_execution_policy",
        "condition_router_reduced_to_evidence_backed_exception_layer",
        "be_after_trigger_retained_as_supported_policy_only_not_primary",
    ]
    if future_outcome_fields_ignored:
        evidence_notes.append("future_outcome_fields_present_but_ignored_by_live_router")
    if candidate_quality.get("enabled"):
        if candidate_quality.get("allowed"):
            evidence_notes.append("candidate_quality_selector_tradeable_subset_matched")
        else:
            evidence_notes.append("candidate_quality_selector_no_trade_or_repair_required")
            if candidate_quality.get("apply_to_execution"):
                refusal_reasons.append(str(candidate_quality.get("refusal_reason") or "candidate_quality_selector_refused"))
    if broker_net_cost.get("enabled"):
        if broker_net_cost.get("allowed"):
            evidence_notes.append("broker_net_cost_selector_packet_passed")
        else:
            evidence_notes.append("broker_net_cost_selector_no_trade_or_repair_required")
            if broker_net_cost.get("apply_to_execution"):
                refusal_reasons.append(
                    str(
                        broker_net_cost.get("refusal_reason")
                        or "broker_net_cost_selector_refused"
                    )
                )

    if framework not in activated_frameworks and not (
        origin_family in activated_origin_families and broader_origin_allowed
    ):
        refusal_reasons.append("framework_not_activated_in_stage13_full_moonshot_selector")
    if broker_native_exact_excluded or (symbol_key and symbol_key in exact_excluded_symbols):
        refusal_reasons.append("broker_contract_invalid_or_unavailable")
    if eligible_symbols and symbol_key and symbol_key not in eligible_symbols:
        refusal_reasons.append("symbol_not_in_broker_native_activation_map")
    if broker_native_eligible_value not in (None, "") and not _truthy(broker_native_eligible_value):
        refusal_reasons.append("broker_contract_invalid_or_unavailable")
    if runtime_instrument_configured_value not in (None, "") and not _truthy(
        runtime_instrument_configured_value
    ):
        refusal_reasons.append("runtime_instrument_not_configured_for_activation")
    if selected_cell_risk_required and not selected_cell_risk_allowed:
        refusal_reasons.append("selected_cell_risk_not_verified_or_zero")
    if selected_cell_risk_required and selected_cell_risk_allowed and (
        selected_cell_risk_pct is None or selected_cell_risk_pct <= 0
    ):
        refusal_reasons.append("selected_cell_risk_not_verified_or_zero")
    branch_label_allowed = bool(required_branch_labels and branch_label in required_branch_labels)
    if (
        required_branch_labels
        and not branch_label_allowed
        and not repaired_branch_allowed
        and not broader_origin_allowed
    ):
        refusal_reasons.append("branch_semantics_not_follow_or_repaired")
    if not _source_status_is_live_asof_complete(source_status):
        refusal_reasons.append("source_path_not_asof_computed")
    if origin_family in activated_origin_families and not live_generation_status.startswith(
        "generated_live_asof"
    ):
        refusal_reasons.append("broader_origin_not_live_generated_asof")
    if not source_mode:
        refusal_reasons.append("source_mode_missing")
    if selected_policy_same_bar_ambiguous:
        refusal_reasons.append("selected_policy_ordered_ltf_or_tick_path_required")
    elif (
        "same_bar_ambiguous" in ordered_path_status
        or "requires_ltf_or_tick" in ordered_path_status
        or ordered_path_status == "ambiguous"
    ):
        evidence_notes.append(
            "non_selected_policy_same_bar_ambiguity_observed_not_used_as_trade_selection_rule"
        )
    if (require_configured_kill_zone and not kill_zone_position.startswith("in_")) or (
        kill_zone_position and not kill_zone_position.startswith("in_")
    ):
        refusal_reasons.append("outside_configured_kill_zone_or_missing_schedule")

    source_quality_action = "SOURCE_OK_FOR_DEFAULT_OFF_REPLAY"
    if not source_window_complete:
        source_quality_action = (
            "SOURCE_REPLAY_OK_WITH_FORWARD_CAPTURE_MONITORING_REQUIRED"
        )
        evidence_notes.append(
            "source_window_completeness_is_evidence_quality_not_trade_selection_rule"
        )
    if "selected_policy_ordered_ltf_or_tick_path_required" in refusal_reasons:
        source_quality_action = "REQUIRE_ORDERED_LTF_OR_TICK_PATH_BEFORE_OWNER_ACTIVATION"
    if "outside_configured_kill_zone_or_missing_schedule" in refusal_reasons:
        source_quality_action = "REQUIRE_CONFIGURED_KILL_ZONE_BEFORE_ACTIVATION"

    selected_policy = DEFAULT_POLICY
    if policy_router_mode == CONDITION_CHALLENGER_MODE:
        raw_policy, displacement_bucket = select_asof_displacement_policy(event)
        selected_policy = _live_execution_policy(raw_policy, evidence_notes)
        dimensions["current_bar_displacement_bucket"] = displacement_bucket
        dimensions["raw_asof_selected_policy"] = raw_policy
        dimensions["retired_stage11_condition_policy"] = LEGACY_ASOF_DISPLACEMENT_POLICY_MAP.get(
            (framework, session_bucket, displacement_bucket),
            BE_AFTER_TRIGGER_POLICY,
        )
        evidence_notes.append("promoted_momentum_primary_exception_router_selected_live_policy")
        if selected_policy != DEFAULT_POLICY:
            evidence_notes.append("evidence_backed_exception_policy_differs_from_momentum_primary")

    # Purely additive frozen segment exit-policy branch: when the caller
    # attaches a ``segment_policy_resolution`` mapping (resolved from the
    # exit_policy_segment_table_v1 artifact), a promoted resolution that maps
    # onto an already-supported live policy may steer the selected policy and
    # leaves full provenance under route_dimensions['segment_exit_policy'].
    # Events without the key are byte-identical to pre-branch behavior.
    #
    # Evidence/deployment geometry guard: tournament evidence holds for the
    # exact tested PolicySpec params (params_fidelity 'exact_params_required'),
    # while the wired live policy families carry their own live geometry. The
    # branch therefore steers ONLY when the event also carries the explicit
    # opt-in ``segment_policy_params_consumer_ready=True`` — the caller's
    # assertion that it builds the per-trade exit config from the resolution
    # params via ``ExitPolicyConfigV4.from_policy_params``. Without that flag
    # the resolution is recorded as 'observed_not_applied' and the selected
    # policy is left unchanged, keeping even data-present paths inert until
    # execution-side param consumption is wired.
    segment_resolution = _mapping(event.get("segment_policy_resolution"))
    if segment_resolution:
        segment_promoted = _truthy(segment_resolution.get("promoted"))
        segment_live_policy = _segment_resolution_live_policy(segment_resolution)
        segment_params = _mapping(segment_resolution.get("params"))
        segment_params_consumer_ready = _truthy(
            event.get("segment_policy_params_consumer_ready")
        )
        segment_steerable = bool(segment_promoted and segment_live_policy)
        segment_applied = bool(segment_steerable and segment_params_consumer_ready)
        segment_not_applied_reason = None
        if segment_applied:
            selected_policy = segment_live_policy
            evidence_notes.append(
                "segment_exit_policy_promoted_tournament_resolution_applied_to_selected_policy"
            )
        elif segment_steerable:
            segment_not_applied_reason = (
                "segment_policy_params_consumer_not_ready_exact_params_required"
            )
            evidence_notes.append(
                "segment_exit_policy_resolution_observed_not_applied_params_consumer_not_ready"
            )
        else:
            segment_not_applied_reason = (
                "resolution_not_promoted"
                if not segment_promoted
                else "no_supported_live_policy_mapping"
            )
            evidence_notes.append(
                "segment_exit_policy_resolution_present_but_not_applied"
            )
        dimensions["segment_exit_policy"] = {
            "applied": segment_applied,
            "application_status": (
                "applied" if segment_applied else "observed_not_applied"
            ),
            "not_applied_reason": segment_not_applied_reason,
            "params_consumer_ready": segment_params_consumer_ready,
            "params_fidelity": segment_resolution.get("params_fidelity"),
            "promoted": segment_promoted,
            "policy_id": segment_resolution.get("policy_id"),
            "family": segment_resolution.get("family"),
            "segment_id": segment_resolution.get("segment_id"),
            "fallback_level": segment_resolution.get("fallback_level"),
            "resolution_reason": segment_resolution.get("reason"),
            "mapped_live_policy": segment_live_policy,
            "selected_policy_params": dict(segment_params) if segment_params else None,
            "table_sha256": segment_resolution.get("table_sha256"),
        }
        if segment_applied and segment_params:
            dimensions["selected_policy_params"] = dict(segment_params)
    selected_branch = candidate_origin_family
    candidate_action = "TRADE_VNEXT_ACTIVATED_CANDIDATE"
    ai_role = "CONSTRAINED_VALIDATOR_FOR_SOURCE_OR_POLICY_CONFLICTS"
    exit_management_action = (
        "ROUTE_EXIT_POLICY_BY_PROMOTED_MOMENTUM_PRIMARY_EXCEPTION_LAYER"
        if policy_router_mode == CONDITION_CHALLENGER_MODE
        else "REPLACE_RETIRED_STATIC_BASELINE_WITH_MOMENTUM_EXHAUSTION_PRIMARY"
    )

    if broader_origin_allowed:
        selected_branch = candidate_origin_family
        candidate_action = "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
        evidence_notes.append("broader_origin_group_allowed_by_stage13_positive_dynamic_replay_selector")
    elif repaired_branch_allowed and not branch_label_allowed:
        selected_branch = f"moonshot_repaired_{candidate_origin_family}"
        candidate_action = "TRADE_VNEXT_REPAIRED_BRANCH_CANDIDATE"
        evidence_notes.append("branch_label_repaired_by_stage13_positive_row_level_selector")

    if framework == PRIMARY_FRAMEWORK:
        ai_role = "MECHANICAL_PRIMARY_AI_VALIDATES_ONLY_AMBIGUOUS_SOURCE_OR_CONFLICT"
    elif framework in activated_frameworks:
        evidence_notes.append("non_fvg_framework_promoted_by_full_moonshot_stage13_selector")

    prop_action = _prop_action(event)
    if prop_action != "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS":
        evidence_notes.append("prop_boundary_action_is_owner_gated_or_risk_reducing_no_broker_mutation")

    if refusal_reasons:
        decision_status = "refuse_live_use_until_source_or_scope_repaired"
        candidate_action = "ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR"
    else:
        decision_status = "vnext_candidate_ready"

    allowed_now = bool(
        enabled
        and apply_to_execution
        and not refusal_reasons
        and candidate_action in {
            "TRADE_VNEXT_ACTIVATED_CANDIDATE",
            "TRADE_VNEXT_REPAIRED_BRANCH_CANDIDATE",
            "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
        }
        and prop_action == "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS"
    )
    runtime_effect_now = allowed_now
    execution_policy_id = execution_policy_id_for(selected_policy)

    return MoonshotPolicyRouterDecision(
        enabled=True,
        apply_to_execution=bool(apply_to_execution),
        decision_status=decision_status,
        candidate_action=candidate_action,
        selected_branch=selected_branch,
        selected_policy=selected_policy,
        execution_policy_id=execution_policy_id,
        replaced_policy=REJECTED_LIVE_BASELINE,
        fixed_target_role="baseline_comparator_only",
        prop_action=prop_action,
        ai_role=ai_role,
        source_quality_action=source_quality_action,
        exit_management_action=exit_management_action,
        refusal_reasons=tuple(refusal_reasons),
        evidence_notes=tuple(evidence_notes),
        runtime_effect_now=runtime_effect_now,
        candidate_use_allowed_now=allowed_now,
        route_dimensions=dimensions,
    )


__all__ = [
    "BASELINE_FIXED_POLICY",
    "ASOF_DISPLACEMENT_POLICY_MAP",
    "BE_AFTER_TRIGGER_POLICY",
    "CONDITION_CHALLENGER_MODE",
    "CONDITION_CHALLENGER_POLICY",
    "DEFAULT_ACTIVATED_FRAMEWORKS",
    "DEFAULT_ACTIVATED_ORIGIN_FAMILIES",
    "DEFAULT_CANDIDATE_QUALITY_SELECTOR_RULES",
    "DEFAULT_POLICY",
    "DEFAULT_REQUIRED_BRANCH_LABELS",
    "EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES",
    "EXECUTION_POLICY_IDS",
    "FORBIDDEN_FUTURE_OUTCOME_FIELDS",
    "LEGACY_ASOF_DISPLACEMENT_POLICY_MAP",
    "MOMENTUM_EXHAUSTION_POLICY",
    "MoonshotPolicyRouterDecision",
    "PARTIAL_BE_RUNNER_POLICY",
    "PRIMARY_BRANCH",
    "PRIMARY_FRAMEWORK",
    "REPAIRED_BRANCH_ACTION",
    "RETIRED_STATIC_BASELINE_COMPARATOR",
    "REJECTED_LIVE_BASELINE",
    "SAFE_FALLBACK_POLICY",
    "SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY",
    "SUPPORTED_LIVE_EXECUTION_POLICIES",
    "TIME_STOP_POLICY",
    "TRAILING_RUNNER_POLICY",
    "execution_policy_id_for",
    "route_moonshot_dynamic_execution",
    "select_asof_displacement_policy",
]

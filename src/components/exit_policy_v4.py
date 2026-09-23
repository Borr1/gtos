"""Wave3 V4 source-bound exit policy evaluator.

The evaluator is intentionally pure. It does not read files, call MT5, mutate
broker state, or infer historical lifecycle truth. Runtime callers must provide
ticket-bound state, current price/path state, and clock/source status.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from typing import Any, Literal, Mapping


def _exit_on_challenge() -> bool:
    try:
        from src.components.broker_net_cost_engine import _on_challenge
    except Exception:
        return False
    try:
        return bool(_on_challenge())
    except Exception:
        return False


def _raw_float(cfg: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = cfg.get(key)
        if value in (None, ""):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        return number
    return None


def _raw_int(cfg: Mapping[str, Any], key: str) -> int | None:
    value = cfg.get(key)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _challenge_exit_config(cls, cfg: Mapping[str, Any]):
    """Challenge bounds are the config value or one Score. No floor is put back.

    An empty score is named on ``bounds_unset`` and is not a close.
    """

    spec: list[tuple[str, tuple[str, ...], str]] = [
        (
            "partial_trigger_r",
            (
                "moonshot_exit_policy_v4_partial_trigger_r",
                "moonshot_dynamic_execution_router_partial_trigger_r",
            ),
            "float",
        ),
        (
            "partial_close_ratio",
            (
                "moonshot_exit_policy_v4_partial_close_ratio",
                "moonshot_dynamic_execution_router_partial_close_ratio",
            ),
            "float",
        ),
        (
            "be_trigger_r",
            (
                "moonshot_exit_policy_v4_be_trigger_r",
                "moonshot_dynamic_execution_router_be_trigger_r",
            ),
            "float",
        ),
        (
            "trailing_trigger_r",
            (
                "moonshot_exit_policy_v4_trailing_trigger_r",
                "moonshot_dynamic_execution_router_trailing_trigger_r",
            ),
            "float",
        ),
        (
            "trailing_gap_r",
            (
                "moonshot_exit_policy_v4_trailing_gap_r",
                "moonshot_dynamic_execution_router_trailing_gap_r",
            ),
            "float",
        ),
        ("trailing_min_locked_r", ("moonshot_exit_policy_v4_trailing_min_locked_r",), "float"),
        ("stale_thesis_bars", ("moonshot_exit_policy_v4_stale_thesis_bars",), "int"),
        ("stale_min_mfe_r", ("moonshot_exit_policy_v4_stale_min_mfe_r",), "float"),
        ("stale_max_progress_r", ("moonshot_exit_policy_v4_stale_max_progress_r",), "float"),
        ("stale_adverse_r", ("moonshot_exit_policy_v4_stale_adverse_r",), "float"),
        ("opportunity_cost_close_r", ("moonshot_exit_policy_v4_opportunity_cost_close_r",), "float"),
        ("scheduler_regret_close_r", ("moonshot_exit_policy_v4_scheduler_regret_close_r",), "float"),
        ("opportunity_cost_min_bars", ("moonshot_exit_policy_v4_opportunity_cost_min_bars",), "int"),
        (
            "opportunity_cost_max_progress_r",
            ("moonshot_exit_policy_v4_opportunity_cost_max_progress_r",),
            "float",
        ),
        ("giveback_trigger_r", ("moonshot_exit_policy_v4_giveback_trigger_r",), "float"),
        ("giveback_close_r", ("moonshot_exit_policy_v4_giveback_close_r",), "float"),
        ("time_stop_bars", ("moonshot_exit_policy_v4_time_stop_bars",), "int"),
    ]
    resolved: dict[str, Any] = {}
    missing: list[str] = []
    for name, keys, kind in spec:
        value = _raw_int(cfg, keys[0]) if kind == "int" else _raw_float(cfg, keys)
        if value is None:
            missing.append(name)
        else:
            resolved[name] = value
    if missing:
        try:
            from src.components.broker_net_cost_engine import _challenge_scores
        except Exception:
            _challenge_scores = None  # type: ignore[assignment]
        got: dict[str, float | None] = {}
        if _challenge_scores is not None:
            got = _challenge_scores(
                "exit_policy_v4.bounds",
                {"missing": list(missing)},
                {
                    name: (
                        f"The score you return is {name} for this exit state. "
                        "An empty score leaves it unset and is not a close."
                    )
                    for name in missing
                },
            )
        for name in missing:
            number = got.get(name)
            if number is None:
                continue
            if name.endswith("_bars"):
                resolved[name] = int(number)
            else:
                resolved[name] = number
    unset = tuple(name for name, _keys, _kind in spec if name not in resolved)
    enabled_raw = cfg.get("moonshot_exit_policy_v4_enabled", False)
    apply_raw = cfg.get("moonshot_exit_policy_v4_apply_to_execution", False)
    if isinstance(enabled_raw, str):
        enabled = enabled_raw.strip().lower() in {"1", "true", "yes", "on"}
    else:
        enabled = bool(enabled_raw)
    if isinstance(apply_raw, str):
        apply_to_execution = apply_raw.strip().lower() in {"1", "true", "yes", "on"}
    else:
        apply_to_execution = bool(apply_raw)

    def take(name: str, fallback: float | int) -> float | int:
        if name in resolved:
            return resolved[name]
        return fallback

    return cls(
        enabled=enabled,
        apply_to_execution=apply_to_execution,
        partial_trigger_r=float(take("partial_trigger_r", 0.0)),
        partial_close_ratio=float(take("partial_close_ratio", 0.0)),
        be_trigger_r=float(take("be_trigger_r", 0.0)),
        trailing_trigger_r=float(take("trailing_trigger_r", 0.0)),
        trailing_gap_r=float(take("trailing_gap_r", 0.0)),
        trailing_min_locked_r=float(take("trailing_min_locked_r", 0.0)),
        stale_thesis_bars=int(take("stale_thesis_bars", 0)),
        stale_min_mfe_r=float(take("stale_min_mfe_r", 0.0)),
        stale_max_progress_r=float(take("stale_max_progress_r", 0.0)),
        stale_adverse_r=float(take("stale_adverse_r", 0.0)),
        opportunity_cost_close_r=float(take("opportunity_cost_close_r", 0.0)),
        scheduler_regret_close_r=float(take("scheduler_regret_close_r", 0.0)),
        opportunity_cost_min_bars=int(take("opportunity_cost_min_bars", 0)),
        opportunity_cost_max_progress_r=float(take("opportunity_cost_max_progress_r", 0.0)),
        giveback_trigger_r=float(take("giveback_trigger_r", 0.0)),
        giveback_close_r=float(take("giveback_close_r", 0.0)),
        time_stop_bars=int(take("time_stop_bars", 0)),
        abort_adverse_r=_raw_float(cfg, ("moonshot_exit_policy_v4_abort_adverse_r",)),
        abort_adverse_max_mfe_r=_raw_float(cfg, ("moonshot_exit_policy_v4_abort_adverse_max_mfe_r",)),
        abort_stop_r=_raw_float(cfg, ("moonshot_exit_policy_v4_abort_stop_r",)),
        abort_no_progress_bars=_raw_int(cfg, "moonshot_exit_policy_v4_abort_no_progress_bars"),
        abort_min_mfe_r=_raw_float(cfg, ("moonshot_exit_policy_v4_abort_min_mfe_r",)),
        abort_close_below_r=_raw_float(cfg, ("moonshot_exit_policy_v4_abort_close_below_r",)),
        abort_consecutive_bars=_raw_int(cfg, "moonshot_exit_policy_v4_abort_consecutive_bars"),
        bounds_unset=unset,
    )


ExitActionV4 = Literal[
    "HOLD",
    "PARTIAL_CLOSE_TO_BE",
    "MOVE_STOP_TO_BE",
    "RAISE_TRAILING_STOP",
    "TIGHTEN_STOP_LOSS_ABORT",
    "CLOSE_EARLY_LOSS_ABORT",
    "CLOSE_GIVEBACK",
    "CLOSE_STALE_THESIS",
    "CLOSE_TIME_STOP",
]


@dataclass(frozen=True)
class ExitPolicyConfigV4:
    enabled: bool = False
    apply_to_execution: bool = False
    partial_trigger_r: float = 1.0
    partial_close_ratio: float = 0.5
    be_trigger_r: float = 1.0
    trailing_trigger_r: float = 1.0
    trailing_gap_r: float = 0.5
    trailing_min_locked_r: float = 0.0
    stale_thesis_bars: int = 12
    stale_min_mfe_r: float = 0.35
    stale_max_progress_r: float = 0.0
    stale_adverse_r: float = -0.25
    opportunity_cost_close_r: float = 1.0
    scheduler_regret_close_r: float = 0.75
    opportunity_cost_min_bars: int = 4
    opportunity_cost_max_progress_r: float = 0.25
    giveback_trigger_r: float = 1.0
    giveback_close_r: float = 0.65
    time_stop_bars: int = 32
    # Early-loss-abort primitives. All default ``None`` = disabled, so the
    # pre-abort decision ladder is unchanged unless a runtime key (or a
    # per-trade policy-params overlay) explicitly arms them.
    abort_adverse_r: float | None = None
    abort_adverse_max_mfe_r: float | None = None
    abort_stop_r: float | None = None
    abort_no_progress_bars: int | None = None
    abort_min_mfe_r: float | None = None
    abort_close_below_r: float | None = None
    abort_consecutive_bars: int | None = None
    bounds_unset: tuple[str, ...] = ()

    @classmethod
    def from_runtime_config(cls, runtime_cfg: dict | None) -> "ExitPolicyConfigV4":
        cfg = runtime_cfg or {}
        if _exit_on_challenge():
            return _challenge_exit_config(cls, cfg)

        def _bool(key: str, default: bool) -> bool:
            value = cfg.get(key, default)
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)

        def _float(key: str, default: float) -> float:
            value = cfg.get(key, default)
            try:
                return float(value if value not in (None, "") else default)
            except (TypeError, ValueError):
                return default

        def _int(key: str, default: int) -> int:
            value = cfg.get(key, default)
            try:
                parsed = int(value if value not in (None, "") else default)
            except (TypeError, ValueError):
                parsed = default
            return max(1, parsed)

        def _opt_float(key: str) -> float | None:
            value = cfg.get(key)
            if value in (None, ""):
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def _opt_int(key: str) -> int | None:
            value = cfg.get(key)
            if value in (None, ""):
                return None
            try:
                return max(1, int(value))
            except (TypeError, ValueError):
                return None

        return cls(
            enabled=_bool("moonshot_exit_policy_v4_enabled", False),
            apply_to_execution=_bool("moonshot_exit_policy_v4_apply_to_execution", False),
            partial_trigger_r=max(
                0.01,
                _float(
                    "moonshot_exit_policy_v4_partial_trigger_r",
                    _float("moonshot_dynamic_execution_router_partial_trigger_r", 1.0),
                ),
            ),
            partial_close_ratio=min(
                0.99,
                max(
                    0.01,
                    _float(
                        "moonshot_exit_policy_v4_partial_close_ratio",
                        _float(
                            "moonshot_dynamic_execution_router_partial_close_ratio",
                            0.5,
                        ),
                    ),
                ),
            ),
            be_trigger_r=max(
                0.01,
                _float(
                    "moonshot_exit_policy_v4_be_trigger_r",
                    _float("moonshot_dynamic_execution_router_be_trigger_r", 1.0),
                ),
            ),
            trailing_trigger_r=max(
                0.01,
                _float(
                    "moonshot_exit_policy_v4_trailing_trigger_r",
                    _float("moonshot_dynamic_execution_router_trailing_trigger_r", 1.0),
                ),
            ),
            trailing_gap_r=max(
                0.01,
                _float(
                    "moonshot_exit_policy_v4_trailing_gap_r",
                    _float("moonshot_dynamic_execution_router_trailing_gap_r", 0.5),
                ),
            ),
            trailing_min_locked_r=max(
                0.0,
                _float("moonshot_exit_policy_v4_trailing_min_locked_r", 0.0),
            ),
            stale_thesis_bars=_int("moonshot_exit_policy_v4_stale_thesis_bars", 12),
            stale_min_mfe_r=max(
                0.0,
                _float("moonshot_exit_policy_v4_stale_min_mfe_r", 0.35),
            ),
            stale_max_progress_r=_float(
                "moonshot_exit_policy_v4_stale_max_progress_r",
                0.0,
            ),
            stale_adverse_r=_float("moonshot_exit_policy_v4_stale_adverse_r", -0.25),
            opportunity_cost_close_r=max(
                0.01,
                _float("moonshot_exit_policy_v4_opportunity_cost_close_r", 1.0),
            ),
            scheduler_regret_close_r=max(
                0.01,
                _float("moonshot_exit_policy_v4_scheduler_regret_close_r", 0.75),
            ),
            opportunity_cost_min_bars=_int(
                "moonshot_exit_policy_v4_opportunity_cost_min_bars",
                4,
            ),
            opportunity_cost_max_progress_r=_float(
                "moonshot_exit_policy_v4_opportunity_cost_max_progress_r",
                0.25,
            ),
            giveback_trigger_r=max(
                0.01,
                _float("moonshot_exit_policy_v4_giveback_trigger_r", 1.0),
            ),
            giveback_close_r=max(
                0.01,
                _float("moonshot_exit_policy_v4_giveback_close_r", 0.65),
            ),
            time_stop_bars=_int("moonshot_exit_policy_v4_time_stop_bars", 32),
            abort_adverse_r=_opt_float("moonshot_exit_policy_v4_abort_adverse_r"),
            abort_adverse_max_mfe_r=_opt_float(
                "moonshot_exit_policy_v4_abort_adverse_max_mfe_r"
            ),
            abort_stop_r=_opt_float("moonshot_exit_policy_v4_abort_stop_r"),
            abort_no_progress_bars=_opt_int(
                "moonshot_exit_policy_v4_abort_no_progress_bars"
            ),
            abort_min_mfe_r=_opt_float("moonshot_exit_policy_v4_abort_min_mfe_r"),
            abort_close_below_r=_opt_float(
                "moonshot_exit_policy_v4_abort_close_below_r"
            ),
            abort_consecutive_bars=_opt_int(
                "moonshot_exit_policy_v4_abort_consecutive_bars"
            ),
        )

    @classmethod
    def from_policy_params(
        cls,
        params: Mapping[str, object] | None,
        base: "ExitPolicyConfigV4",
    ) -> "ExitPolicyConfigV4":
        """Overlay per-trade policy params over a base config.

        Built for the future per-segment policy table: a segment row carries
        threshold overrides (field names, optionally prefixed with
        ``moonshot_exit_policy_v4_``) that take precedence over ``base``.
        Activation stays owned by the runtime config: ``enabled`` and
        ``apply_to_execution`` can never be flipped by per-trade params.
        Unknown keys are ignored and unparseable values keep the base value so
        a malformed segment row degrades to base behavior instead of inventing
        thresholds.
        """

        if not params:
            return base
        prefix = "moonshot_exit_policy_v4_"
        protected_fields = {"enabled", "apply_to_execution", "bounds_unset"}
        field_names = {spec.name for spec in fields(cls)} - protected_fields
        required_int_fields = {
            "stale_thesis_bars",
            "opportunity_cost_min_bars",
            "time_stop_bars",
        }
        optional_int_fields = {"abort_no_progress_bars", "abort_consecutive_bars"}
        optional_float_fields = {
            "abort_adverse_r",
            "abort_adverse_max_mfe_r",
            "abort_stop_r",
            "abort_min_mfe_r",
            "abort_close_below_r",
        }
        overrides: dict[str, object] = {}
        for raw_key, raw_value in params.items():
            key = str(raw_key)
            if key.startswith(prefix):
                key = key[len(prefix):]
            if key not in field_names:
                continue
            if raw_value in (None, ""):
                if key in optional_int_fields or key in optional_float_fields:
                    overrides[key] = None
                continue
            try:
                if key in required_int_fields or key in optional_int_fields:
                    parsed_int = int(raw_value)
                    if not _exit_on_challenge():
                        parsed_int = max(1, parsed_int)
                    overrides[key] = parsed_int
                else:
                    overrides[key] = float(raw_value)
            except (TypeError, ValueError):
                continue
        if not overrides:
            return base
        return replace(base, **overrides)


@dataclass(frozen=True)
class ExitPolicyInputV4:
    ticket: int | None
    symbol: str
    direction: str
    entry_time_utc: str | None
    bars_elapsed: int | None
    current_progress_r: float | None
    mfe_r: float | None
    mae_r: float | None = None
    current_stop_r: float | None = None
    partial_closed: bool = False
    sl_at_breakeven: bool = False
    current_volume: float | None = None
    initial_volume: float | None = None
    partial_close_allowed: bool = False
    ticket_bound_state: bool = False
    broker_position_confirmed: bool = False
    path_source_status: str = "missing_path_source"
    clock_source_status: str = "missing_clock_source"
    lifecycle_source_status: str = "missing_lifecycle_source"
    cost_source_status: str = "not_owned_by_exit_policy_v4"
    thesis_invalidation_status: str = "source_not_available"
    opposite_signal_strength: float | None = None
    opportunity_cost_r: float | None = None
    scheduler_regret_r: float | None = None
    competing_candidate_ev_r: float | None = None
    opportunity_cost_source_status: str = "not_provided"
    scheduler_regret_source_status: str = "not_provided"
    # Caller-maintained count of CONSECUTIVE closed bars with close progress
    # <= abort_close_below_r (reset on any bar above). Replay-parity source for
    # the adverse-close abort: when the rule is armed and this is None the
    # rule fails closed (HOLD with explicit gap) instead of approximating.
    consecutive_closes_below_abort_r: int | None = None
    source_gaps: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExitPolicyDecisionV4:
    action: ExitActionV4
    reason: str
    status: str
    target_stop_r: float | None = None
    close_reason: str | None = None
    partial_close_ratio: float | None = None
    source_completeness_status: str = "unknown"
    source_gaps: tuple[str, ...] = field(default_factory=tuple)
    evidence_class: str = "source_bound_runtime_state"
    runtime_effect_boundary: str = "local_code_decision_only_until_called_by_runtime"
    semantic_handoffs: tuple[str, ...] = field(default_factory=tuple)


def _source_gaps(row: ExitPolicyInputV4) -> tuple[str, ...]:
    gaps = list(row.source_gaps)
    if not row.ticket:
        gaps.append("missing_ticket")
    if not row.symbol:
        gaps.append("missing_symbol")
    if row.direction not in {"LONG", "SHORT"}:
        gaps.append("missing_or_invalid_direction")
    if row.current_progress_r is None:
        gaps.append("missing_current_progress_r")
    if row.mfe_r is None:
        gaps.append("missing_mfe_r")
    if row.bars_elapsed is None:
        gaps.append("missing_bars_elapsed")
    if not row.ticket_bound_state:
        gaps.append("ticket_bound_state_not_confirmed")
    if not row.broker_position_confirmed:
        gaps.append("broker_position_not_confirmed")
    if not row.path_source_status or row.path_source_status.startswith("missing"):
        gaps.append("path_source_missing")
    if not row.clock_source_status or row.clock_source_status.startswith("missing"):
        gaps.append("clock_source_missing")
    if not row.lifecycle_source_status or row.lifecycle_source_status.startswith("missing"):
        gaps.append("lifecycle_source_missing")
    if row.opportunity_cost_r is not None and not _source_status_complete(
        row.opportunity_cost_source_status
    ):
        gaps.append("opportunity_cost_source_missing")
    if row.scheduler_regret_r is not None and not _source_status_complete(
        row.scheduler_regret_source_status
    ):
        gaps.append("scheduler_regret_source_missing")
    return tuple(dict.fromkeys(gaps))


def _source_status_complete(value: str | None) -> bool:
    text = str(value or "").strip().lower()
    return text in {
        "complete",
        "captured",
        "captured_complete",
        "replay",
        "replay_bound",
        "source_bound",
        "source_window_complete",
        "scheduler_regret_replay_bound",
        "opportunity_cost_replay_bound",
    }


def evaluate_exit_policy_v4(
    config: ExitPolicyConfigV4,
    row: ExitPolicyInputV4,
) -> ExitPolicyDecisionV4:
    """Return the V4 exit action from source-bound runtime state."""

    handoffs = (
        "same_symbol_same_instrument_lifecycle_v4_owns_competing_exposure",
        "probability_debate_team_engine_v4_owns_close_reverse_thesis_ev",
        "follow_avoid_mixed_numeric_confluence_v4_owns_signal_reliability",
        "cost_swap_slippage_broker_constraint_engine_owns_cost_drag_limits",
        "feature_label_store_owns_no_leak_ml_labels",
    )
    if not config.enabled or not config.apply_to_execution:
        return ExitPolicyDecisionV4(
            action="HOLD",
            reason="exit_policy_v4_disabled_or_not_applied",
            status="disabled",
            source_completeness_status="not_required_disabled",
            semantic_handoffs=handoffs,
        )
    unset = set(config.bounds_unset)

    def _ready(*names: str) -> bool:
        return not any(name in unset for name in names)

    gaps = _source_gaps(row)
    if gaps:
        return ExitPolicyDecisionV4(
            action="HOLD",
            reason="source_gap_fail_closed",
            status="source_gap_fail_closed",
            source_completeness_status="incomplete",
            source_gaps=gaps,
            semantic_handoffs=handoffs,
        )

    progress_r = float(row.current_progress_r)
    mfe_r = max(float(row.mfe_r), progress_r)
    mae_r = float(row.mae_r) if row.mae_r is not None else min(0.0, progress_r)
    bars_elapsed = int(row.bars_elapsed or 0)
    current_stop_r = float(row.current_stop_r) if row.current_stop_r is not None else -1.0
    opportunity_cost_r = (
        float(row.opportunity_cost_r) if row.opportunity_cost_r is not None else None
    )
    scheduler_regret_r = (
        float(row.scheduler_regret_r) if row.scheduler_regret_r is not None else None
    )

    opposite_dominates = False
    if row.opposite_signal_strength is not None:
        if _exit_on_challenge():
            winner = None
            try:
                from src.judgment.state_choices import side

                winner = side(
                    "exit_policy_v4.opposite_signal",
                    {
                        "opposite_signal_strength": float(row.opposite_signal_strength),
                        "progress_r": progress_r,
                        "mfe_r": mfe_r,
                        "giveback_close_r": float(config.giveback_close_r),
                    },
                    "dominates",
                    "not_dominates",
                    "Does this opposite signal dominate the open thesis for this state? "
                    "An empty answer is not a close.",
                )
            except Exception:
                winner = None
            opposite_dominates = winner == "dominates"
        else:
            opposite_dominates = float(row.opposite_signal_strength) >= 0.75
    if row.thesis_invalidation_status == "invalidated" or (
        opposite_dominates
        and _ready("giveback_close_r")
        and progress_r <= max(0.0, mfe_r - config.giveback_close_r)
    ):
        return ExitPolicyDecisionV4(
            action="CLOSE_STALE_THESIS",
            reason="thesis_invalidated_or_opposite_signal_dominates",
            status="actionable",
            close_reason="v4_stale_thesis_invalidated",
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    opportunity_close = (
        _ready("opportunity_cost_min_bars", "opportunity_cost_max_progress_r", "opportunity_cost_close_r")
        and opportunity_cost_r is not None
        and opportunity_cost_r >= config.opportunity_cost_close_r
    )
    regret_close = (
        _ready("opportunity_cost_min_bars", "opportunity_cost_max_progress_r", "scheduler_regret_close_r")
        and scheduler_regret_r is not None
        and scheduler_regret_r >= config.scheduler_regret_close_r
    )
    if (
        _ready("opportunity_cost_min_bars", "opportunity_cost_max_progress_r")
        and bars_elapsed >= config.opportunity_cost_min_bars
        and progress_r <= config.opportunity_cost_max_progress_r
        and (opportunity_close or regret_close)
    ):
        return ExitPolicyDecisionV4(
            action="CLOSE_STALE_THESIS",
            reason="opportunity_cost_or_scheduler_regret_dominates_stale_hold",
            status="actionable",
            close_reason="v4_stale_thesis_opportunity_cost_close",
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    if (
        _ready("giveback_trigger_r", "giveback_close_r")
        and mfe_r >= config.giveback_trigger_r
        and progress_r <= max(0.0, mfe_r - config.giveback_close_r)
    ):
        return ExitPolicyDecisionV4(
            action="CLOSE_GIVEBACK",
            reason="meaningful_mfe_giveback_exceeded",
            status="actionable",
            close_reason="v4_profit_giveback_exit",
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    # Early-loss-abort ladder slot: after stale-thesis/giveback closes, before
    # any profit-protection action (partial close / BE / trailing). All abort
    # config fields default ``None`` = disabled. Close decisions dominate the
    # stop-tighten when both arm on the same evaluation.
    if (
        config.abort_no_progress_bars is not None
        and config.abort_min_mfe_r is not None
        and bars_elapsed >= int(config.abort_no_progress_bars)
        and mfe_r < float(config.abort_min_mfe_r)
    ):
        return ExitPolicyDecisionV4(
            action="CLOSE_EARLY_LOSS_ABORT",
            reason="no_progress_by_abort_bar_budget",
            status="actionable",
            close_reason="v4_abort_no_progress",
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    # Replay-parity adverse-close abort: requires the caller-maintained
    # CONSECUTIVE below-threshold close counter (identical semantics to
    # simulate_policy's abort_consecutive_bars rule). abort_min_mfe_r must be
    # armed explicitly — no silent 0.0 default. Counter missing while the
    # rule is armed -> fail closed (HOLD with explicit gap), never approximate
    # with bars_elapsed.
    if (
        config.abort_close_below_r is not None
        and config.abort_consecutive_bars is not None
        and config.abort_min_mfe_r is not None
    ):
        consecutive = row.consecutive_closes_below_abort_r
        if consecutive is None:
            return ExitPolicyDecisionV4(
                action="HOLD",
                reason="abort_adverse_close_armed_but_consecutive_counter_missing",
                status="source_gap_fail_closed",
                source_completeness_status="incomplete",
                source_gaps=("consecutive_closes_below_abort_r_counter_required",),
                semantic_handoffs=handoffs,
            )
        if (
            int(consecutive) >= int(config.abort_consecutive_bars)
            and mfe_r < float(config.abort_min_mfe_r)
        ):
            return ExitPolicyDecisionV4(
                action="CLOSE_EARLY_LOSS_ABORT",
                reason="adverse_close_persistence_without_progress",
                status="actionable",
                close_reason="v4_abort_adverse_close",
                source_completeness_status="complete",
                semantic_handoffs=handoffs,
            )

    if (
        config.abort_adverse_r is not None
        and config.abort_adverse_max_mfe_r is not None
        and config.abort_stop_r is not None
        and mae_r <= -float(config.abort_adverse_r)
        and mfe_r < float(config.abort_adverse_max_mfe_r)
        and float(config.abort_stop_r) > current_stop_r + 1e-9
    ):
        return ExitPolicyDecisionV4(
            action="TIGHTEN_STOP_LOSS_ABORT",
            reason="adverse_excursion_without_progress_tighten_stop",
            status="actionable",
            target_stop_r=float(config.abort_stop_r),
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    if (
        _ready("partial_trigger_r", "partial_close_ratio")
        and not row.partial_closed
        and row.partial_close_allowed
        and mfe_r >= config.partial_trigger_r
    ):
        return ExitPolicyDecisionV4(
            action="PARTIAL_CLOSE_TO_BE",
            reason="partial_trigger_reached_before_full_target",
            status="actionable",
            partial_close_ratio=config.partial_close_ratio,
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    if _ready("be_trigger_r") and not row.sl_at_breakeven and mfe_r >= config.be_trigger_r:
        return ExitPolicyDecisionV4(
            action="MOVE_STOP_TO_BE",
            reason="be_trigger_reached_release_initial_risk",
            status="actionable",
            target_stop_r=0.0,
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    if _ready("trailing_trigger_r", "trailing_gap_r", "trailing_min_locked_r") and mfe_r >= config.trailing_trigger_r:
        desired_stop_r = max(
            config.trailing_min_locked_r,
            mfe_r - config.trailing_gap_r,
        )
        if desired_stop_r > current_stop_r + 1e-9:
            return ExitPolicyDecisionV4(
                action="RAISE_TRAILING_STOP",
                reason="mfe_supports_higher_trailing_stop",
                status="actionable",
                target_stop_r=desired_stop_r,
                source_completeness_status="complete",
                semantic_handoffs=handoffs,
            )

    if (
        _ready(
            "stale_thesis_bars",
            "stale_min_mfe_r",
            "stale_max_progress_r",
            "stale_adverse_r",
        )
        and bars_elapsed >= config.stale_thesis_bars
        and mfe_r < config.stale_min_mfe_r
        and progress_r <= config.stale_max_progress_r
        and mae_r <= config.stale_adverse_r
    ):
        return ExitPolicyDecisionV4(
            action="CLOSE_STALE_THESIS",
            reason="hold_time_no_progress_and_adverse_path",
            status="actionable",
            close_reason="v4_stale_thesis_no_progress",
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    if _ready("time_stop_bars") and bars_elapsed >= config.time_stop_bars:
        return ExitPolicyDecisionV4(
            action="CLOSE_TIME_STOP",
            reason="max_hold_bars_elapsed",
            status="actionable",
            close_reason="v4_time_stop",
            source_completeness_status="complete",
            semantic_handoffs=handoffs,
        )

    return ExitPolicyDecisionV4(
        action="HOLD",
        reason="no_exit_action_reached",
        status="monitoring",
        source_completeness_status="complete",
        semantic_handoffs=handoffs,
    )

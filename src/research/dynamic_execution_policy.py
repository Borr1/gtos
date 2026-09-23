"""Research-only dynamic execution policy replay.

This module is deliberately pure: no MT5, no broker state, no files, and no
runtime flag reads. It provides a state machine that can be fed source-bound
ordered price-path observations and can compare fixed-target replay with the
live-current J46/J49 style and other exit-management policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal, Mapping, Optional

SameBarPolicy = Literal["conservative", "optimistic", "ambiguous"]


@dataclass(frozen=True)
class PathObservation:
    """One ordered path observation expressed in R units from entry.

    ``high_r`` is the best favorable excursion reached during the observation.
    ``low_r`` is the worst adverse excursion reached during the observation.
    This convention is side-normalized: it is the same for LONG and SHORT once
    converted by ``observation_from_ohlc``.
    """

    index: int
    high_r: float
    low_r: float
    close_r: float
    open_r: Optional[float] = None
    time_utc: Optional[str] = None
    source_mode: Optional[str] = None


@dataclass(frozen=True)
class PolicySpec:
    """Execution policy parameters for replaying an already-filled trade."""

    name: str
    final_target_r: Optional[float]
    stop_r: float = -1.0
    tp1_r: Optional[float] = None
    partial_close_ratio: float = 0.0
    move_stop_to_be_on_tp1: bool = False
    be_stop_r: float = 0.0
    time_stop_bars: Optional[int] = None
    early_cut_bars: Optional[int] = None
    early_cut_min_mfe_r: Optional[float] = None
    trailing_trigger_r: Optional[float] = None
    trailing_gap_r: Optional[float] = None
    giveback_close_r: Optional[float] = None
    stale_thesis_bars: Optional[int] = None
    stale_thesis_min_mfe_r: Optional[float] = None
    stale_thesis_close_below_r: Optional[float] = None
    max_bars: Optional[int] = None
    # Early-loss-abort primitives. All default ``None`` so existing policy
    # factories replay byte-identically. Aborts evaluate on bar close AFTER the
    # stop/target checks; the stop-tighten applies from the NEXT bar.
    abort_adverse_r: Optional[float] = None
    abort_adverse_max_mfe_r: Optional[float] = None
    abort_stop_r: Optional[float] = None
    abort_no_progress_bars: Optional[int] = None
    abort_min_mfe_r: Optional[float] = None
    abort_close_below_r: Optional[float] = None
    abort_consecutive_bars: Optional[int] = None
    description: str = ""


@dataclass(frozen=True)
class PolicyReplayResult:
    policy_name: str
    replay_status: str
    final_r: Optional[float]
    exit_reason: str
    exit_index: Optional[int] = None
    exit_time_utc: Optional[str] = None
    mfe_r: Optional[float] = None
    mae_r: Optional[float] = None
    partial_realized_r: float = 0.0
    remaining_fraction: float = 1.0
    stop_r_at_exit: Optional[float] = None
    same_bar_ambiguity: bool = False
    source_gap_reason: Optional[str] = None
    transitions: list[dict] = field(default_factory=list)


def legacy_fixed_target_policy(target_r: float = 1.5) -> PolicySpec:
    return PolicySpec(
        name=f"legacy_fixed_{target_r:g}r",
        final_target_r=float(target_r),
        description="Fixed full close at configured R target or -1R stop.",
    )


def ai_target_policy(target_r: float) -> PolicySpec:
    return PolicySpec(
        name="ai_target",
        final_target_r=float(target_r),
        description="Full close at the AI-emitted target R or -1R stop.",
    )


def live_current_j46_j49_policy(
    *,
    tp1_r: float = 3.0,
    higher_target_r: float = 6.0,
    time_stop_bars: int = 12,
    partial_close_ratio: float = 0.0,
) -> PolicySpec:
    return PolicySpec(
        name="live_current_j46_j49",
        final_target_r=float(higher_target_r),
        tp1_r=float(tp1_r),
        partial_close_ratio=float(partial_close_ratio),
        move_stop_to_be_on_tp1=True,
        time_stop_bars=int(time_stop_bars),
        description=(
            "Live-current J46/J49: broker target at 6R, software TP1 at 3R, "
            "move stop to BE at TP1, no partial by default, 12 M15-bar time stop."
        ),
    )


def partial_be_policy(
    *,
    tp1_r: float = 1.0,
    final_target_r: float = 3.0,
    partial_close_ratio: float = 0.33,
) -> PolicySpec:
    return PolicySpec(
        name="partial_be_runner",
        final_target_r=float(final_target_r),
        tp1_r=float(tp1_r),
        partial_close_ratio=float(partial_close_ratio),
        move_stop_to_be_on_tp1=True,
        description="Partial at TP1, move remaining stop to BE, run to target.",
    )


def be_only_policy(*, trigger_r: float = 1.0, final_target_r: float = 1.5) -> PolicySpec:
    return PolicySpec(
        name="be_after_trigger",
        final_target_r=float(final_target_r),
        tp1_r=float(trigger_r),
        partial_close_ratio=0.0,
        move_stop_to_be_on_tp1=True,
        description="Move stop to BE after trigger R, no partial close.",
    )


def trailing_policy(
    *,
    trigger_r: float = 2.0,
    gap_r: float = 1.0,
    final_target_r: Optional[float] = 6.0,
) -> PolicySpec:
    return PolicySpec(
        name="trailing_runner",
        final_target_r=final_target_r,
        trailing_trigger_r=float(trigger_r),
        trailing_gap_r=float(gap_r),
        description="Trail stop by a fixed R gap after favorable trigger.",
    )


def momentum_exhaustion_policy(
    *,
    trigger_r: float = 1.0,
    pullback_r: float = 0.4,
    final_target_r: float = 2.0,
    time_stop_bars: Optional[int] = None,
) -> PolicySpec:
    return PolicySpec(
        name="momentum_exhaustion",
        final_target_r=float(final_target_r),
        trailing_trigger_r=float(trigger_r),
        giveback_close_r=float(pullback_r),
        time_stop_bars=int(time_stop_bars) if time_stop_bars is not None else None,
        description=(
            "Momentum primary: after trigger R, close on configured pullback "
            "from best MFE, capped by the final target."
        ),
    )


def time_stop_policy(*, bars: int = 12, final_target_r: Optional[float] = None) -> PolicySpec:
    return PolicySpec(
        name="time_stop_only" if final_target_r is None else "target_with_time_stop",
        final_target_r=final_target_r,
        time_stop_bars=int(bars),
        description="Close at mark-to-market R when time-stop bars elapse.",
    )


def early_cut_policy(
    *,
    bars: int = 4,
    min_mfe_r: float = 0.25,
    final_target_r: Optional[float] = 1.5,
) -> PolicySpec:
    return PolicySpec(
        name="early_cut_if_no_progress",
        final_target_r=final_target_r,
        early_cut_bars=int(bars),
        early_cut_min_mfe_r=float(min_mfe_r),
        description="Close early if path fails to make minimum favorable progress.",
    )


def path_aware_runner_policy(
    *,
    structural_target_r: Optional[float] = None,
    liquidity_target_r: Optional[float] = None,
    atr_expansion_target_r: Optional[float] = None,
    max_target_r: float = 6.0,
    time_stop_bars: Optional[int] = 12,
) -> PolicySpec:
    """Build a runner target from source-bound market references.

    The policy chooses the nearest positive supplied target, capped by
    ``max_target_r``. Missing references do not invent a target; they fall back
    to the cap so the replay remains explicit about source requirements.
    """

    candidates = [
        value
        for value in (structural_target_r, liquidity_target_r, atr_expansion_target_r)
        if value is not None and value > 0
    ]
    target = min(candidates) if candidates else float(max_target_r)
    target = min(float(target), float(max_target_r))
    return PolicySpec(
        name="path_aware_runner",
        final_target_r=target,
        tp1_r=min(3.0, target) if target > 3.0 else None,
        move_stop_to_be_on_tp1=target > 3.0,
        time_stop_bars=time_stop_bars,
        description="Runner using structural/liquidity/ATR target references.",
    )


def profit_harvest_mfe_capture_v4_policy(
    *,
    min_mfe_r: float = 0.25,
    micro_partial_trigger_r: float = 0.50,
    micro_partial_close_ratio: float = 0.33,
    trail_gap_r: float = 0.35,
    giveback_close_r: float = 0.50,
    stale_thesis_bars: int = 24,
    stale_thesis_min_mfe_r: float = 0.25,
    stale_thesis_close_below_r: float = 0.0,
    final_target_r: Optional[float] = 3.0,
) -> PolicySpec:
    return PolicySpec(
        name="profit_harvest_mfe_capture_v4",
        final_target_r=final_target_r,
        tp1_r=float(micro_partial_trigger_r),
        partial_close_ratio=float(micro_partial_close_ratio),
        move_stop_to_be_on_tp1=True,
        trailing_trigger_r=float(min_mfe_r),
        trailing_gap_r=float(trail_gap_r),
        giveback_close_r=float(giveback_close_r),
        stale_thesis_bars=int(stale_thesis_bars),
        stale_thesis_min_mfe_r=float(stale_thesis_min_mfe_r),
        stale_thesis_close_below_r=float(stale_thesis_close_below_r),
        description=(
            "Wave3 V4 source-bound harvest contract: micro-partial, BE/trail, "
            "giveback close, and stale-thesis close over ordered R-path rows."
        ),
    )


def required_policy_manifest() -> list[PolicySpec]:
    """Default policy set required by the moonshot dynamic-execution route."""

    return [
        live_current_j46_j49_policy(),
        legacy_fixed_target_policy(1.5),
        ai_target_policy(1.5),
        partial_be_policy(),
        be_only_policy(),
        momentum_exhaustion_policy(),
        trailing_policy(),
        time_stop_policy(bars=12),
        early_cut_policy(),
        profit_harvest_mfe_capture_v4_policy(),
        path_aware_runner_policy(),
    ]


def observation_from_ohlc(
    *,
    index: int,
    row: Mapping[str, object],
    entry: float,
    stop: float,
    side: str,
    time_key: str = "time",
) -> PathObservation:
    """Convert OHLC price bars to side-normalized R observations."""

    sl_distance = abs(float(entry) - float(stop))
    if sl_distance <= 0:
        raise ValueError("entry and stop must define a positive R distance")

    open_price = float(row.get("open", row.get("Open")))
    high_price = float(row.get("high", row.get("High")))
    low_price = float(row.get("low", row.get("Low")))
    close_price = float(row.get("close", row.get("Close")))
    normalized_side = side.upper()
    if normalized_side == "LONG":
        open_r = (open_price - entry) / sl_distance
        high_r = (high_price - entry) / sl_distance
        low_r = (low_price - entry) / sl_distance
        close_r = (close_price - entry) / sl_distance
    elif normalized_side == "SHORT":
        open_r = (entry - open_price) / sl_distance
        high_r = (entry - low_price) / sl_distance
        low_r = (entry - high_price) / sl_distance
        close_r = (entry - close_price) / sl_distance
    else:
        raise ValueError(f"side must be LONG or SHORT, got {side!r}")

    return PathObservation(
        index=index,
        open_r=open_r,
        high_r=high_r,
        low_r=low_r,
        close_r=close_r,
        time_utc=str(row.get(time_key)) if row.get(time_key) is not None else None,
    )


def simulate_policy(
    policy: PolicySpec,
    observations: Iterable[PathObservation],
    *,
    same_bar_policy: SameBarPolicy = "conservative",
) -> PolicyReplayResult:
    """Replay one policy over ordered source-bound path observations."""

    obs_list = sorted(observations, key=lambda obs: obs.index)
    if not obs_list:
        return PolicyReplayResult(
            policy_name=policy.name,
            replay_status="not_replayable",
            final_r=None,
            exit_reason="source_gap_no_ordered_path",
            source_gap_reason="no_path_observations",
        )

    if same_bar_policy not in {"conservative", "optimistic", "ambiguous"}:
        raise ValueError(f"unsupported same_bar_policy: {same_bar_policy}")

    remaining_fraction = 1.0
    partial_realized_r = 0.0
    stop_r = float(policy.stop_r)
    stop_reason = "stop_loss"
    tp1_done = False
    best_mfe = float("-inf")
    worst_mae = float("inf")
    transitions: list[dict] = []
    same_bar_ambiguity = False
    abort_stop_tighten_done = False
    abort_adverse_close_run = 0

    def close(
        *,
        reason: str,
        exit_r: float,
        obs: PathObservation,
        status: str = "replayed",
        ambiguous: bool = False,
    ) -> PolicyReplayResult:
        return PolicyReplayResult(
            policy_name=policy.name,
            replay_status=status,
            final_r=partial_realized_r + remaining_fraction * float(exit_r),
            exit_reason=reason,
            exit_index=obs.index,
            exit_time_utc=obs.time_utc,
            mfe_r=best_mfe,
            mae_r=worst_mae,
            partial_realized_r=partial_realized_r,
            remaining_fraction=remaining_fraction,
            stop_r_at_exit=stop_r,
            same_bar_ambiguity=same_bar_ambiguity or ambiguous,
            transitions=transitions.copy(),
        )

    for obs in obs_list:
        best_mfe = max(best_mfe, obs.high_r)
        worst_mae = min(worst_mae, obs.low_r)
        tp1_triggered_this_observation = False

        stop_hit = obs.low_r <= stop_r
        tp1_hit = (
            policy.tp1_r is not None
            and not tp1_done
            and obs.high_r >= float(policy.tp1_r)
        )
        final_hit = (
            policy.final_target_r is not None
            and obs.high_r >= float(policy.final_target_r)
        )

        if stop_hit and (tp1_hit or final_hit):
            same_bar_ambiguity = True
            if same_bar_policy == "ambiguous":
                return close(
                    reason="same_bar_stop_and_profit_trigger_ambiguous",
                    exit_r=0.0,
                    obs=obs,
                    status="ambiguous",
                    ambiguous=True,
                )
            if same_bar_policy == "conservative":
                return close(
                    reason="stop_first_same_bar_conservative",
                    exit_r=stop_r,
                    obs=obs,
                    ambiguous=True,
                )
            stop_hit = False

        if stop_hit:
            return close(reason=stop_reason, exit_r=stop_r, obs=obs)

        if tp1_hit:
            tp1_r = float(policy.tp1_r)
            close_ratio = max(0.0, min(1.0, float(policy.partial_close_ratio)))
            if close_ratio:
                partial_realized_r += close_ratio * tp1_r
                remaining_fraction = max(0.0, remaining_fraction - close_ratio)
            tp1_done = True
            tp1_triggered_this_observation = True
            transition = {
                "index": obs.index,
                "time_utc": obs.time_utc,
                "event": "tp1",
                "tp1_r": tp1_r,
                "partial_close_ratio": close_ratio,
                "remaining_fraction": remaining_fraction,
            }
            if policy.move_stop_to_be_on_tp1 and stop_r < float(policy.be_stop_r):
                stop_r = float(policy.be_stop_r)
                stop_reason = "breakeven_stop"
                transition["stop_moved_to_r"] = stop_r
            transitions.append(transition)

            if remaining_fraction <= 0.0:
                return close(reason="tp1_full_or_all_partial_close", exit_r=tp1_r, obs=obs)

            if final_hit:
                return close(
                    reason="final_target_after_tp1_same_bar",
                    exit_r=float(policy.final_target_r),
                    obs=obs,
                )

        if final_hit:
            return close(
                reason="final_target",
                exit_r=float(policy.final_target_r),
                obs=obs,
            )

        if (
            not tp1_triggered_this_observation
            and policy.trailing_trigger_r is not None
            and policy.trailing_gap_r is not None
            and obs.high_r >= float(policy.trailing_trigger_r)
        ):
            candidate_stop = obs.high_r - float(policy.trailing_gap_r)
            if candidate_stop > stop_r:
                stop_r = candidate_stop
                stop_reason = "trailing_stop"
                transitions.append(
                    {
                        "index": obs.index,
                        "time_utc": obs.time_utc,
                        "event": "trail_stop",
                        "stop_moved_to_r": stop_r,
                    }
                )
            if obs.low_r <= stop_r:
                same_bar_ambiguity = True
                if same_bar_policy == "ambiguous":
                    return close(
                        reason="same_bar_trailing_stop_ambiguous",
                        exit_r=0.0,
                        obs=obs,
                        status="ambiguous",
                        ambiguous=True,
                    )
                return close(
                    reason="trailing_stop",
                    exit_r=stop_r if same_bar_policy == "conservative" else obs.high_r,
                    obs=obs,
                    ambiguous=True,
                )

        if (
            not tp1_triggered_this_observation
            and policy.giveback_close_r is not None
            and best_mfe >= float(policy.trailing_trigger_r or 0.0)
        ):
            giveback_exit_r = best_mfe - float(policy.giveback_close_r)
            if obs.low_r <= giveback_exit_r:
                ambiguous = obs.high_r >= best_mfe and obs.low_r <= giveback_exit_r
                if ambiguous:
                    same_bar_ambiguity = True
                    if same_bar_policy == "ambiguous":
                        return close(
                            reason="same_bar_giveback_close_ambiguous",
                            exit_r=0.0,
                            obs=obs,
                            status="ambiguous",
                            ambiguous=True,
                        )
                transitions.append(
                    {
                        "index": obs.index,
                        "time_utc": obs.time_utc,
                        "event": "giveback_close",
                        "mfe_r": best_mfe,
                        "giveback_close_r": float(policy.giveback_close_r),
                        "exit_r": giveback_exit_r,
                    }
                )
                return close(
                    reason="giveback_close",
                    exit_r=giveback_exit_r,
                    obs=obs,
                    ambiguous=ambiguous,
                )

        if (
            not tp1_triggered_this_observation
            and policy.stale_thesis_bars is not None
            and obs.index >= int(policy.stale_thesis_bars)
            and best_mfe >= float(policy.stale_thesis_min_mfe_r or 0.0)
            and obs.close_r <= float(policy.stale_thesis_close_below_r or 0.0)
        ):
            transitions.append(
                {
                    "index": obs.index,
                    "time_utc": obs.time_utc,
                    "event": "stale_thesis_close",
                    "mfe_r": best_mfe,
                    "close_r": obs.close_r,
                    "stale_thesis_bars": int(policy.stale_thesis_bars),
                }
            )
            return close(reason="stale_thesis_close", exit_r=obs.close_r, obs=obs)

        # Early-loss-abort primitives: evaluated on bar close AFTER the
        # stop/target checks above. The stop-tighten mutates ``stop_r`` only,
        # so it takes effect at the NEXT bar's stop check (no same-bar exit).
        if (
            not abort_stop_tighten_done
            and policy.abort_adverse_r is not None
            and policy.abort_adverse_max_mfe_r is not None
            and policy.abort_stop_r is not None
            and worst_mae <= -float(policy.abort_adverse_r)
            and best_mfe < float(policy.abort_adverse_max_mfe_r)
        ):
            abort_stop_tighten_done = True
            if float(policy.abort_stop_r) > stop_r:
                stop_r = float(policy.abort_stop_r)
                stop_reason = "abort_tightened_stop"
                transitions.append(
                    {
                        "index": obs.index,
                        "time_utc": obs.time_utc,
                        "event": "abort_stop_tighten",
                        "mae_r": worst_mae,
                        "mfe_r": best_mfe,
                        "stop_moved_to_r": stop_r,
                    }
                )

        if (
            policy.abort_no_progress_bars is not None
            and policy.abort_min_mfe_r is not None
            and obs.index >= int(policy.abort_no_progress_bars)
            and best_mfe < float(policy.abort_min_mfe_r)
        ):
            transitions.append(
                {
                    "index": obs.index,
                    "time_utc": obs.time_utc,
                    "event": "abort_no_progress",
                    "mfe_r": best_mfe,
                    "close_r": obs.close_r,
                    "abort_no_progress_bars": int(policy.abort_no_progress_bars),
                }
            )
            return close(reason="abort_no_progress", exit_r=obs.close_r, obs=obs)

        if (
            policy.abort_close_below_r is not None
            and policy.abort_consecutive_bars is not None
        ):
            if obs.close_r <= float(policy.abort_close_below_r):
                abort_adverse_close_run += 1
            else:
                abort_adverse_close_run = 0
            if (
                abort_adverse_close_run >= int(policy.abort_consecutive_bars)
                and best_mfe < float(policy.abort_min_mfe_r or 0.0)
            ):
                transitions.append(
                    {
                        "index": obs.index,
                        "time_utc": obs.time_utc,
                        "event": "abort_adverse_close",
                        "mfe_r": best_mfe,
                        "close_r": obs.close_r,
                        "consecutive_adverse_closes": abort_adverse_close_run,
                    }
                )
                return close(reason="abort_adverse_close", exit_r=obs.close_r, obs=obs)

        if policy.time_stop_bars is not None and obs.index >= int(policy.time_stop_bars):
            return close(reason="time_stop", exit_r=obs.close_r, obs=obs)

        if (
            policy.early_cut_bars is not None
            and policy.early_cut_min_mfe_r is not None
            and obs.index >= int(policy.early_cut_bars)
            and best_mfe < float(policy.early_cut_min_mfe_r)
        ):
            return close(reason="early_cut_no_progress", exit_r=obs.close_r, obs=obs)

        if policy.max_bars is not None and obs.index >= int(policy.max_bars):
            return close(reason="max_bars_mark_to_market", exit_r=obs.close_r, obs=obs)

    last = obs_list[-1]
    return close(reason="path_end_mark_to_market", exit_r=last.close_r, obs=last)

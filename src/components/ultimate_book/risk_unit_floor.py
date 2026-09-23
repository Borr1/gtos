"""Adaptive Q1 minimum-risk-unit policy.

The priced rule is::

    risk' = max(risk0, bar_multiple * median_m15_range_24,
                       cost_multiple * round_trip_cost_price)

This module deliberately separates *observation* from *application*.  ``off`` performs no
work, ``shadow`` computes the proposal without changing a :class:`TradeIntent`, and
``apply`` permits the owner to replace the intent only after the pre-existing generation,
admission, and pre-send refusal sequence has completed.

No mode is inferred from a non-empty sleeve list.  A worker must name both a mode and its
effective launched sleeves, and every numeric option must be finite.  That keeps a stale or
misspelled supervisor row from reading as a healthy floor that is not actually running.
"""

from __future__ import annotations

import dataclasses
import math
import statistics
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from typing import Any, Callable, Mapping, Optional, Sequence

DEFAULT_BAR_MULTIPLE = 1.0
DEFAULT_COST_MULTIPLE = 5.0
LOOKBACK_BARS = 24
MIN_LOOKBACK_BARS = 12
MAX_PLAUSIBLE_BAR_MULTIPLE = 3.0
MAX_PLAUSIBLE_COST_MULTIPLE = 12.0
MODES = ("off", "shadow", "apply")
TARGET_POLICIES = ("preserve", "weld")

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _scores(cache_key: tuple, facts: dict, questions: dict[str, str]) -> dict[str, float | None]:
    """One post for this floor state. The same sleeve and options do not ask again."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    packed = {str(qid): {"type": "score", "instructions": str(text)} for qid, text in questions.items()}
    answers: dict = {}
    returned = None
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import returned_number

        returned = returned_number
        receipt = evaluate(payload, questions=packed, merge_sleeve=False)
    except Exception:
        receipt = None
    if (
        isinstance(receipt, dict)
        and receipt.get("ok") is not False
        and not receipt.get("error")
        and receipt.get("tie") is not True
        and isinstance(receipt.get("answers"), dict)
    ):
        answers = receipt["answers"]
    out = {qid: None if returned is None else _finite(returned(answers.get(qid))) for qid in packed}
    _HOP[cache_key] = dict(out)
    return out


class RiskUnitFloorError(ValueError):
    """Invalid launch-time Q1 policy."""


@dataclasses.dataclass(frozen=True)
class FloorParams:
    bar_multiple: float = DEFAULT_BAR_MULTIPLE
    cost_multiple: float = DEFAULT_COST_MULTIPLE
    cap_widen: Optional[float] = None
    # Preserve literal targets (notably vp_euidx_pocgrav's POC) unless the operator
    # explicitly asks to weld the target to the widened R-unit.
    target_policy: str = "preserve"

    def as_dict(self) -> dict[str, Any]:
        return {
            "bar_multiple": self.bar_multiple,
            "cost_multiple": self.cost_multiple,
            "cap_widen": self.cap_widen,
            "target_policy": self.target_policy,
        }


@dataclasses.dataclass(frozen=True)
class RiskUnitFloorPolicy:
    mode: str = "off"
    sleeves: Mapping[str, FloorParams] = dataclasses.field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return self.mode in ("shadow", "apply") and bool(self.sleeves)

    def params_for(self, sleeve: str) -> Optional[FloorParams]:
        return self.sleeves.get(str(sleeve)) if self.enabled else None


OFF_POLICY = RiskUnitFloorPolicy()


def _finite_positive(name: str, sleeve: str, raw: Any, *, maximum: float) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise RiskUnitFloorError(
            f"--risk-unit-floor {name} for {sleeve!r} is not a number: {raw!r}"
        ) from None
    if not math.isfinite(value):
        raise RiskUnitFloorError(
            f"--risk-unit-floor {name} for {sleeve!r} must be finite, got {raw!r}"
        )
    if value <= 0.0:
        raise RiskUnitFloorError(
            f"--risk-unit-floor {name} for {sleeve!r} must be > 0, got {value}"
        )
    if value > maximum:
        raise RiskUnitFloorError(
            f"--risk-unit-floor {name} for {sleeve!r} is {value}, above {maximum}"
        )
    return value


def parse_risk_unit_floor(
    raw: Any,
    *,
    known_sleeves: Any = None,
    effective_sleeves: Any = None,
) -> dict[str, FloorParams]:
    """Parse the per-sleeve selection without assigning it a runtime mode.

    ``effective_sleeves`` is the launcher's actual ``--tags`` surface.  When supplied, a
    registered-but-unlaunched sleeve is refused rather than accepted into a policy that can
    never fire.
    """
    if raw is None:
        return {}
    if not isinstance(raw, str):
        raise RiskUnitFloorError(
            f"--risk-unit-floor must be a string, got {type(raw).__name__}"
        )
    if not raw.strip():
        raise RiskUnitFloorError(
            "--risk-unit-floor was given an EMPTY selection; omit it when the policy is off"
        )
    known = {str(value) for value in known_sleeves} if known_sleeves is not None else None
    effective = (
        {str(value) for value in effective_sleeves}
        if effective_sleeves is not None
        else None
    )
    out: dict[str, FloorParams] = {}
    for chunk in raw.split(","):
        item = chunk.strip()
        if not item:
            raise RiskUnitFloorError(
                f"--risk-unit-floor has an empty entry in {raw!r}"
            )
        parts = [part.strip() for part in item.split(":")]
        sleeve = parts[0]
        if not sleeve:
            raise RiskUnitFloorError(f"--risk-unit-floor entry {item!r} names no sleeve")
        if known is not None and sleeve not in known:
            raise RiskUnitFloorError(
                f"--risk-unit-floor names unknown sleeve {sleeve!r}"
            )
        if effective is not None and sleeve not in effective:
            raise RiskUnitFloorError(
                f"--risk-unit-floor names {sleeve!r}, but it is not in the effective "
                f"--tags surface {sorted(effective)}"
            )
        if sleeve in out:
            raise RiskUnitFloorError(f"--risk-unit-floor names {sleeve!r} twice")

        bar_raw: Optional[str] = None
        cost_raw: Optional[str] = None
        cap: Optional[float] = None
        target = "preserve"
        seen: set[str] = set()
        for option in parts[1:]:
            if not option:
                raise RiskUnitFloorError(
                    f"--risk-unit-floor entry {item!r} has an empty option"
                )
            key, separator, value = option.partition("=")
            key = key.strip().lower()
            value = value.strip()
            if not separator:
                raise RiskUnitFloorError(
                    f"--risk-unit-floor option {option!r} needs key=value"
                )
            if key in seen:
                raise RiskUnitFloorError(
                    f"--risk-unit-floor names option {key!r} twice on {sleeve!r}"
                )
            seen.add(key)
            if key == "bar":
                bar_raw = value
            elif key == "cost":
                cost_raw = value
            elif key == "cap":
                cap = _finite_positive("cap", sleeve, value, maximum=100.0)
                if cap <= 1.0:
                    raise RiskUnitFloorError(
                        f"--risk-unit-floor cap for {sleeve!r} must be > 1.0"
                    )
            elif key == "target":
                target = value.lower()
                if target not in TARGET_POLICIES:
                    raise RiskUnitFloorError(
                        f"--risk-unit-floor target for {sleeve!r} must be one of "
                        f"{list(TARGET_POLICIES)}, got {target!r}"
                    )
            else:
                raise RiskUnitFloorError(
                    f"--risk-unit-floor option {key!r} on {sleeve!r} is unknown"
                )
        questions: dict[str, str] = {}
        if bar_raw is None:
            questions["bar_multiple"] = (
                "The score you return is the bar-range multiple this sleeve's risk floor uses. "
                "An empty score leaves that multiple unset. Do not send."
            )
        else:
            questions["max_plausible_bar_multiple"] = (
                "The score you return is the highest bar multiple this sleeve still accepts. "
                "An empty score leaves that cap unset. Do not send."
            )
        if cost_raw is None:
            questions["cost_multiple"] = (
                "The score you return is the round-trip-cost multiple this sleeve's risk floor uses. "
                "An empty score leaves that multiple unset. Do not send."
            )
        else:
            questions["max_plausible_cost_multiple"] = (
                "The score you return is the highest cost multiple this sleeve still accepts. "
                "An empty score leaves that cap unset. Do not send."
            )
        scores = _scores(
            ("risk_unit_floor", sleeve, tuple(sorted(seen))),
            {"sleeve": sleeve, "options": sorted(seen)},
            questions,
        )
        if bar_raw is None:
            bar = scores.get("bar_multiple")
            if bar is None or not (bar > 0.0):
                raise RiskUnitFloorError(
                    f"--risk-unit-floor bar for {sleeve!r} is unanswered. "
                    "Refused rather than filled with a planted multiple."
                )
        else:
            bar_cap = scores.get("max_plausible_bar_multiple")
            if bar_cap is None or not (bar_cap > 0.0):
                raise RiskUnitFloorError(
                    f"--risk-unit-floor bar cap for {sleeve!r} is unanswered. "
                    "Refused rather than compared with a planted cap."
                )
            bar = _finite_positive("bar", sleeve, bar_raw, maximum=bar_cap)
        if cost_raw is None:
            cost = scores.get("cost_multiple")
            if cost is None or not (cost > 0.0):
                raise RiskUnitFloorError(
                    f"--risk-unit-floor cost for {sleeve!r} is unanswered. "
                    "Refused rather than filled with a planted multiple."
                )
        else:
            cost_cap = scores.get("max_plausible_cost_multiple")
            if cost_cap is None or not (cost_cap > 0.0):
                raise RiskUnitFloorError(
                    f"--risk-unit-floor cost cap for {sleeve!r} is unanswered. "
                    "Refused rather than compared with a planted cap."
                )
            cost = _finite_positive("cost", sleeve, cost_raw, maximum=cost_cap)
        out[sleeve] = FloorParams(float(bar), float(cost), cap, target)
    return out


def policy_from_args(
    mode: Any,
    raw: Any,
    *,
    known_sleeves: Any,
    effective_sleeves: Any,
) -> RiskUnitFloorPolicy:
    """Build the complete launch policy and refuse inconsistent mode/selection pairs."""
    normalized_mode = str(mode or "off").strip().lower()
    if normalized_mode not in MODES:
        raise RiskUnitFloorError(
            f"--risk-unit-floor-mode must be one of {list(MODES)}, got {mode!r}"
        )
    if normalized_mode == "off":
        if raw is not None:
            raise RiskUnitFloorError(
                "--risk-unit-floor was supplied while --risk-unit-floor-mode is off"
            )
        return OFF_POLICY
    if raw is None:
        raise RiskUnitFloorError(
            f"--risk-unit-floor-mode {normalized_mode} requires --risk-unit-floor"
        )
    if effective_sleeves is None:
        raise RiskUnitFloorError(
            "an active risk-unit floor requires an explicit non-empty --tags surface"
        )
    effective = tuple(str(value) for value in effective_sleeves if str(value))
    if not effective:
        raise RiskUnitFloorError(
            "an active risk-unit floor requires an explicit non-empty --tags surface"
        )
    sleeves = parse_risk_unit_floor(
        raw,
        known_sleeves=known_sleeves,
        effective_sleeves=effective,
    )
    return RiskUnitFloorPolicy(normalized_mode, sleeves)


def _bar_range_median(
    bars: Sequence[Any], *, lookback: int = LOOKBACK_BARS, minimum: int = MIN_LOOKBACK_BARS
) -> tuple[Optional[float], dict[str, Any]]:
    detail: dict[str, Any] = {"lookback": int(lookback), "minimum": int(minimum)}
    try:
        window = list(bars)[-int(lookback) :]
    except TypeError:
        detail["reason"] = "bars_not_a_sequence"
        return None, detail
    ranges: list[float] = []
    for bar in window:
        try:
            value = float(getattr(bar, "h")) - float(getattr(bar, "l"))
        except (AttributeError, TypeError, ValueError):
            detail["reason"] = "bar_high_or_low_unreadable"
            return None, detail
        if not math.isfinite(value) or value < 0.0:
            detail["reason"] = f"bar_range_not_finite_or_negative:{value}"
            return None, detail
        ranges.append(value)
    detail["n"] = len(ranges)
    if len(ranges) < int(minimum):
        detail["reason"] = f"insufficient_closed_bars:{len(ranges)}<{minimum}"
        return None, detail
    value = float(statistics.median(ranges))
    if not math.isfinite(value) or value <= 0.0:
        detail["reason"] = f"nonpositive_bar_range_median:{value}"
        return None, detail
    detail["bar_range_median"] = value
    return value, detail


def bar_range_median_at_cutoff(
    bars: Sequence[Any],
    times: Sequence[datetime],
    *,
    decision_cutoff: datetime,
    interval_minutes: int = 15,
    lookback: int | None = None,
    minimum: int | None = None,
) -> tuple[Optional[float], dict[str, Any]]:
    """Median range of M15 bars completed by the decision cutoff, never evaluation time.

    An omitted lookback or minimum is one Score for this cutoff. An empty score
    returns no median, which the apply path already refuses rather than widening
    from a planted bar count.
    """
    detail: dict[str, Any] = {
        "decision_cutoff_utc": None,
        "interval_minutes": int(interval_minutes),
    }
    try:
        cutoff = decision_cutoff
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        cutoff = cutoff.astimezone(timezone.utc)
        detail["decision_cutoff_utc"] = cutoff.isoformat()
        if lookback is None or minimum is None:
            window = _scores(
                ("risk_floor_window", cutoff.date().isoformat(), int(interval_minutes)),
                {
                    "decision_day": cutoff.date().isoformat(),
                    "interval_minutes": int(interval_minutes),
                },
                {
                    "lookback_bars": (
                        "The score you return is how many completed bars this floor's median uses. "
                        "An empty score leaves that window unset. Do not send."
                    ),
                    "min_lookback_bars": (
                        "The score you return is how many completed bars this floor's median needs. "
                        "An empty score leaves that count unset. Do not send."
                    ),
                },
            )
            if lookback is None:
                lookback_n = window.get("lookback_bars")
            else:
                lookback_n = _finite(lookback)
            if minimum is None:
                minimum_n = window.get("min_lookback_bars")
            else:
                minimum_n = _finite(minimum)
        else:
            lookback_n = _finite(lookback)
            minimum_n = _finite(minimum)
        if (
            lookback_n is None
            or minimum_n is None
            or lookback_n <= 0
            or minimum_n <= 0
        ):
            detail["reason"] = "lookback_unanswered"
            return None, detail
        lookback = int(lookback_n)
        minimum = int(minimum_n)
        detail["lookback"] = lookback
        detail["minimum"] = minimum
        paired = list(zip(list(bars), list(times), strict=True))
    except (TypeError, ValueError, AttributeError):
        detail["reason"] = "bar_time_alignment_unreadable"
        return None, detail
    eligible: list[Any] = []
    interval = timedelta(minutes=int(interval_minutes))
    for bar, stamp in paired:
        if not isinstance(stamp, datetime):
            detail["reason"] = "bar_time_unreadable"
            return None, detail
        current = stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
        if current.astimezone(timezone.utc) + interval <= cutoff:
            eligible.append(bar)
    value, median_detail = _bar_range_median(
        eligible, lookback=lookback, minimum=minimum
    )
    detail.update(median_detail)
    detail["eligible_completed_bars"] = len(eligible)
    return value, detail


def round_trip_cost_price(
    symbol: str,
    tick: Any,
    *,
    server: Any = None,
    namespace: Any = None,
    entry_price: Any = None,
    costs: Any = None,
    broker_true_symbol: Any = None,
) -> tuple[Optional[float], dict[str, Any]]:
    """Resolve live spread plus broker-true round-turn commission in price units."""
    detail: dict[str, Any] = {"symbol": symbol}
    try:
        bid = float(getattr(tick, "bid"))
        ask = float(getattr(tick, "ask"))
    except (AttributeError, TypeError, ValueError):
        bid = ask = float("nan")
    if not all(math.isfinite(value) for value in (bid, ask)) or bid <= 0 or ask <= 0 or ask < bid:
        detail["reason"] = f"quote_unavailable:bid={bid}:ask={ask}"
        return None, detail
    spread_price = ask - bid
    try:
        reference_price = float(entry_price) if entry_price is not None else (bid + ask) / 2.0
    except (TypeError, ValueError):
        reference_price = (bid + ask) / 2.0
    detail.update(
        {"bid": bid, "ask": ask, "spread_price": spread_price, "reference_price": reference_price}
    )
    try:
        from src.costs.model import (
            CostTruthError,
            account_for,
            commission_usd_per_lot,
            load_broker_true_costs,
        )

        truth = costs if costs is not None else load_broker_true_costs()
        account = account_for(server=server, namespace=namespace)
        record = truth.instrument(account, str(broker_true_symbol or symbol))
        usd_per_price_unit = float(record.get("usd_per_price_unit_per_lot") or 0.0)
        if not math.isfinite(usd_per_price_unit) or usd_per_price_unit <= 0:
            raise CostTruthError(
                f"unusable usd_per_price_unit_per_lot={usd_per_price_unit!r}"
            )
        commission_usd, commission_detail = commission_usd_per_lot(
            record, reference_price
        )
        commission_price = float(commission_usd) / usd_per_price_unit
    except Exception as exc:  # an unresolved term must never be read as zero
        detail["reason"] = f"commission_unresolvable:{type(exc).__name__}:{exc}"
        return None, detail
    value = spread_price + commission_price
    if not math.isfinite(value) or value <= 0.0:
        detail["reason"] = f"nonpositive_round_trip_cost:{value}"
        return None, detail
    detail.update(
        {
            "account": account,
            "commission_usd_per_lot": float(commission_usd),
            "usd_per_price_unit_per_lot": usd_per_price_unit,
            "commission_price": commission_price,
            "commission_kind": commission_detail.get("kind"),
            "round_trip_cost_price": value,
        }
    )
    return value, detail


def floored_risk_distance(
    risk0: float, *, bar24: float, rt_cost_price: float, params: FloorParams
) -> tuple[float, dict[str, Any]]:
    """A2's scalar floor arithmetic, including its optional widening cap."""
    risk = float(risk0)
    bar_term = float(params.bar_multiple) * float(bar24)
    cost_term = float(params.cost_multiple) * float(rt_cost_price)
    if not all(math.isfinite(value) and value > 0 for value in (risk, bar_term, cost_term)):
        raise ValueError("risk, bar term, and cost term must be finite and positive")
    widened = max(risk, bar_term, cost_term)
    cap_applied = False
    if params.cap_widen is not None:
        ceiling = float(params.cap_widen) * risk
        if widened > ceiling:
            widened = ceiling
            cap_applied = True
    return widened, {
        "risk_distance_before": risk,
        "risk_distance_after": widened,
        "widening_factor": widened / risk,
        "bar_term": bar_term,
        "cost_term": cost_term,
        "binding_term": (
            "none"
            if widened <= risk
            else "bar"
            if bar_term >= cost_term
            else "cost"
        ),
        "cap_applied": cap_applied,
        "touched": widened > risk,
    }


def apply_floor(
    intent: Any,
    *,
    bar24: Optional[float],
    rt_cost_price: Optional[float],
    params: FloorParams,
) -> tuple[Any, dict[str, Any]]:
    """Return the proposed intent and a complete observation; never raise into a cycle."""
    observation: dict[str, Any] = {"applied": False, **params.as_dict()}
    try:
        risk0 = float(getattr(intent, "stop_dist"))
    except (AttributeError, TypeError, ValueError):
        observation["reason"] = "nonpositive_or_unreadable_stop"
        return intent, observation
    if not math.isfinite(risk0) or risk0 <= 0:
        observation["reason"] = f"nonpositive_or_unreadable_stop:{risk0}"
        return intent, observation
    if bar24 is None or rt_cost_price is None:
        observation["reason"] = "floor_inputs_unresolved"
        return intent, observation
    try:
        widened, detail = floored_risk_distance(
            risk0,
            bar24=float(bar24),
            rt_cost_price=float(rt_cost_price),
            params=params,
        )
        observation.update(detail)
        observation["bar24"] = float(bar24)
        observation["round_trip_cost_price"] = float(rt_cost_price)
        if not detail["touched"]:
            observation.update({"applied": True, "target_policy_effective": "none"})
            return intent, observation
        changes: dict[str, Any] = {"stop_dist": widened}
        target = getattr(intent, "target_dist", None)
        try:
            target_value = float(target) if target is not None else None
        except (TypeError, ValueError):
            target_value = None
        if params.target_policy == "weld" and target_value is not None and target_value > 0:
            changes["target_dist"] = target_value * (widened / risk0)
            observation["target_dist_before"] = target_value
            observation["target_dist_after"] = changes["target_dist"]
            observation["target_policy_effective"] = "weld"
        else:
            # Literal/POC price distance is unchanged.  Execution profiles that do not read
            # the intent target continue to derive their native R target exactly as before.
            observation["target_policy_effective"] = "preserve"
            if target_value is not None:
                observation["target_dist_before"] = target_value
                observation["target_dist_after"] = target_value
        if not dataclasses.is_dataclass(intent):
            observation["reason"] = f"intent_not_a_dataclass:{type(intent).__name__}"
            return intent, observation
        proposed = dataclasses.replace(intent, **changes)
        observation["applied"] = True
        return proposed, observation
    except Exception as exc:  # noqa: BLE001 - fail open while constructing a proposal
        observation["reason"] = f"floor_error:{type(exc).__name__}:{exc}"
        return intent, observation


def project_broker_grid(
    raw_lots: Any,
    symbol_info: Any,
    *,
    intended_risk_usd: Any,
    cash_risk_for_volume: Callable[[float], Optional[float]],
    allow_min_round_up: bool = False,
) -> dict[str, Any]:
    """Project a Q1-sized unit onto one broker's min/step/max lot grid.

    Production refuses a sub-minimum or risk-inflating projection.  F5 may round up only
    because its explicit minimal-size policy already authorizes that behavior; the exact
    resulting dollar-risk inflation is returned so it cannot be hidden in a fill count.
    """
    result: dict[str, Any] = {
        "placement_allowed": False,
        "status": "unresolved",
        "raw_lots": None,
        "normalized_lots": None,
        "intended_risk_usd": None,
        "actual_risk_usd": None,
        "risk_inflation_factor": None,
        "f5_min_round_up_authorized": bool(allow_min_round_up),
    }
    try:
        requested = float(raw_lots)
        intended = float(intended_risk_usd)
        minimum = float(symbol_info.volume_min)
        step = float(symbol_info.volume_step)
        maximum = float(symbol_info.volume_max)
    except (AttributeError, TypeError, ValueError):
        result["status"] = "broker_volume_geometry_unreadable"
        return result
    result.update(
        {
            "raw_lots": requested,
            "intended_risk_usd": intended,
            "volume_min": minimum,
            "volume_step": step,
            "volume_max": maximum,
        }
    )
    if not all(math.isfinite(value) and value > 0 for value in (
        requested, intended, minimum, step, maximum
    )) or maximum < minimum:
        result["status"] = "broker_volume_geometry_invalid"
        return result
    if requested > maximum:
        result["status"] = "requested_lots_above_broker_max"
        return result

    rounded_up = requested < minimum
    if rounded_up and not allow_min_round_up:
        result["status"] = "requested_lots_below_broker_min"
        return result
    if rounded_up:
        normalized = minimum
    else:
        d_requested = Decimal(str(requested))
        d_minimum = Decimal(str(minimum))
        d_step = Decimal(str(step))
        steps = ((d_requested - d_minimum) / d_step).to_integral_value(
            rounding=ROUND_FLOOR
        )
        normalized = float(d_minimum + steps * d_step)
    if normalized < minimum or normalized > maximum or normalized <= 0:
        result["status"] = "normalized_lots_outside_broker_bounds"
        return result
    if not rounded_up and normalized > requested + 1e-12:
        result["status"] = "normalization_would_round_up"
        return result
    try:
        actual = cash_risk_for_volume(float(normalized))
        actual = float(actual) if actual is not None else float("nan")
    except Exception:  # noqa: BLE001
        actual = float("nan")
    result["normalized_lots"] = normalized
    if not math.isfinite(actual) or actual <= 0:
        result["status"] = "broker_cash_risk_unresolved"
        return result
    inflation = actual / intended
    result.update(
        {
            "actual_risk_usd": actual,
            "risk_inflation_factor": inflation,
            "risk_shortfall_fraction": max(0.0, 1.0 - inflation),
        }
    )
    if inflation > 1.0 + 1e-6 and not (rounded_up and allow_min_round_up):
        result["status"] = "normalized_lot_would_inflate_risk"
        return result
    result["placement_allowed"] = True
    result["status"] = "f5_min_round_up_instrumented" if rounded_up else "representable"
    return result


__all__ = [
    "DEFAULT_BAR_MULTIPLE",
    "DEFAULT_COST_MULTIPLE",
    "FloorParams",
    "LOOKBACK_BARS",
    "MIN_LOOKBACK_BARS",
    "MODES",
    "OFF_POLICY",
    "RiskUnitFloorError",
    "RiskUnitFloorPolicy",
    "TARGET_POLICIES",
    "apply_floor",
    "bar_range_median_at_cutoff",
    "floored_risk_distance",
    "parse_risk_unit_floor",
    "policy_from_args",
    "project_broker_grid",
    "round_trip_cost_price",
]

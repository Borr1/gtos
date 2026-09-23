"""Fail-closed completeness contract for pretrade four-component cost packets.

Legacy replay code can retain its historical fallback outside truth mode.  A truth-mode
caller uses :func:`require_complete_cost_packet` before probability, selection or sizing.
This legacy packet is a pretrade expected-cost estimate and is never final economics;
post-exit callers use :mod:`src.costs.lifecycle` instead.  The check requires four finite
non-negative component values, independent nested producer witnesses, no fallback source
class, and the exact FD arithmetic identity.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real
from typing import Any

from src.costs.model import component_sum_r

__all__ = [
    "COST_PACKET_COMPONENT_FIELDS",
    "PRETRADE_EXPECTED_COST_ROLE",
    "CostPacketCompleteness",
    "CostPacketIncompleteError",
    "assess_cost_packet_completeness",
    "assess_pretrade_expected_cost_packet",
    "cost_packet_is_complete",
    "require_complete_cost_packet",
    "require_complete_pretrade_expected_cost_packet",
]

PRETRADE_EXPECTED_COST_ROLE = "pretrade_expected_cost"

COST_PACKET_COMPONENT_FIELDS = (
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
)


@dataclass(frozen=True)
class CostPacketCompleteness:
    status: str
    complete: bool
    component_values: dict[str, float]
    component_sum_r: float | None
    failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "complete": self.complete,
            "component_values": dict(self.component_values),
            "component_sum_r": self.component_sum_r,
            "failures": list(self.failures),
        }


class CostPacketIncompleteError(RuntimeError):
    """The packet cannot support truth-mode economics."""

    def __init__(self, assessment: CostPacketCompleteness):
        self.assessment = assessment
        super().__init__(
            "cost packet is NOT_EVALUABLE: " + ", ".join(assessment.failures)
        )


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nonempty_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return None
    return value


def _matches(component: float | None, witness: object) -> bool:
    witnessed = _number(witness)
    return bool(
        component is not None
        and witnessed is not None
        and math.isclose(component, witnessed, rel_tol=0.0, abs_tol=1e-12)
    )


def assess_cost_packet_completeness(packet: Mapping[str, Any]) -> CostPacketCompleteness:
    """Assess a legacy/pretrade packet without inventing a component or source.

    ``component_sum_r`` is populated only when the entire source/identity contract is
    complete.  An incomplete truth packet is terminal and non-numeric even when four
    plausible values happen to be present.
    """
    failures: list[str] = []
    role = packet.get("cost_role")
    if role not in (None, PRETRADE_EXPECTED_COST_ROLE):
        failures.append("wrong_cost_role_not_pretrade_expected")
    components = _mapping(packet.get("total_cost_components"))
    if not components:
        failures.append("missing_total_cost_components")

    values: dict[str, float] = {}
    for field in COST_PACKET_COMPONENT_FIELDS:
        if field not in components:
            failures.append(f"missing_component:{field}")
            continue
        number = _number(components[field])
        if number is None:
            failures.append(f"invalid_component:{field}")
        else:
            values[field] = number

    exact_sum = None
    if len(values) == len(COST_PACKET_COMPONENT_FIELDS):
        exact_sum = component_sum_r(*(values[field] for field in COST_PACKET_COMPONENT_FIELDS))

    if "authority_fallback_total_cost_r" in components:
        failures.append("legacy_authority_fallback_present")
    if packet.get("candidate_cost_r_fallback_is_authority") is True:
        failures.append("candidate_cost_fallback_marked_authority")
    if packet.get("cost_source_gap_status") != "source_bound_cost_authority_present":
        failures.append("cost_source_gap_not_source_bound")

    # Spread: the numeric child must match a captured tick/quote and the quote source
    # may not be the replay's conservative no-source fallback.
    tick = _mapping(packet.get("tick_cost"))
    spread = values.get("spread_r")
    if tick.get("source_status") != "captured":
        failures.append("spread_source_not_captured")
    if not _matches(spread, tick.get("spread_r")):
        failures.append("spread_component_witness_mismatch")
    quote = _mapping(packet.get("quote_authority"))
    quote_source = _nonempty_text(
        quote.get("quote_source") or packet.get("cost_quote_source")
    )
    if quote_source is None:
        failures.append("spread_source_missing")
    elif quote_source == "conservative_default_spread_r_no_tick_or_symbol_spec":
        failures.append("spread_source_is_conservative_default")

    # Slippage: a numeric component with no named source is not a zero observation.
    # Config/candidate fallbacks are explicitly rejected in truth mode; the Wave-21
    # exact account/profile-symbol artifact emits a non-fallback source name.
    slippage = values.get("expected_slippage_r")
    if not _matches(slippage, packet.get("expected_slippage_r")):
        failures.append("slippage_component_witness_mismatch")
    slippage_source = _nonempty_text(packet.get("expected_slippage_source"))
    if slippage_source is None:
        failures.append("slippage_source_missing")
    elif slippage_source in {
        "trade_params",
        "config.selected_cell_default_expected_slippage_r",
    } or any(token in slippage_source.lower() for token in ("fallback", "placeholder")):
        failures.append("slippage_source_is_legacy_default")

    # Swap: zero is complete only when the producer resolved the schedule and horizon
    # and emitted the zero as captured, rather than ``None or 0`` arithmetic.
    swap = _mapping(packet.get("swap_cost"))
    swap_value = values.get("swap_cost_r")
    if swap.get("source_status") != "captured":
        failures.append("swap_source_not_captured")
    if _nonempty_text(swap.get("model_version")) is None:
        failures.append("swap_source_missing")
    if not _matches(swap_value, swap.get("cost_r")):
        failures.append("swap_component_witness_mismatch")

    # Commission: require the broker-true source child, its provenance, and explicit
    # inclusion.  Comparator zero is never a complete truth packet.
    commission = _mapping(packet.get("commission_cost"))
    commission_value = values.get("commission_r")
    if commission.get("source_status") != "captured":
        failures.append("commission_source_not_captured")
    if commission.get("included_in_total_cost_r") is not True:
        failures.append("commission_not_included")
    if commission.get("comparator_only") is True:
        failures.append("commission_is_comparator")
    if _nonempty_text(commission.get("provenance")) is None:
        failures.append("commission_provenance_missing")
    if _nonempty_text(commission.get("artifact")) is None:
        failures.append("commission_artifact_missing")
    if not _matches(commission_value, commission.get("cost_r")):
        failures.append("commission_component_witness_mismatch")

    recorded_total = _number(packet.get("total_cost_r"))
    if recorded_total is None:
        failures.append("total_cost_r_invalid")
    elif exact_sum is not None and recorded_total != exact_sum:
        failures.append("total_cost_r_component_identity_mismatch")

    failures = list(dict.fromkeys(failures))
    complete = not failures
    return CostPacketCompleteness(
        status="COMPLETE" if complete else "NOT_EVALUABLE",
        complete=complete,
        component_values=values,
        component_sum_r=exact_sum if complete else None,
        failures=tuple(failures),
    )


def cost_packet_is_complete(packet: Mapping[str, Any]) -> bool:
    return assess_cost_packet_completeness(packet).complete


def require_complete_cost_packet(packet: Mapping[str, Any]) -> CostPacketCompleteness:
    assessment = assess_cost_packet_completeness(packet)
    if not assessment.complete:
        raise CostPacketIncompleteError(assessment)
    return assessment


# Explicit names for new callers.  The shorter historical names remain compatible for
# legacy code, but both assess only a pretrade expectation, never final economics.
assess_pretrade_expected_cost_packet = assess_cost_packet_completeness
require_complete_pretrade_expected_cost_packet = require_complete_cost_packet

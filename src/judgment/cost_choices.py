"""Spot-exact Choices for cost, spread, slippage, and swap withholds.

Each question is the two sides of one condition. The unique highest
probability is the decision. An empty map, a tie, or an error does not
restore the old boolean. This module does not send orders.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"

QUESTIONS: dict[str, dict[str, Any]] = {
    "cell_spread": {
        "id": "cell_spread",
        "withhold": "spread_above_the_cell",
        "instructions": (
            "Live spread_r is the spread divided by this stop. "
            "max_spread_r is the cell limit. "
            "spread_above_the_cell withholds the trade because spread_r is above that limit. "
            "spread_inside_the_cell does not withhold the trade for this comparison. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "spread_above_the_cell": "spread_r is above max_spread_r. Withhold the trade.",
            "spread_inside_the_cell": "spread_r is not above max_spread_r. Do not withhold for this comparison.",
        },
    },
    "geometry_spread": {
        "id": "geometry_spread",
        "withhold": "spread_above_the_limit",
        "instructions": (
            "spread_r is the spread divided by this stop. "
            "limit is the number already on this state. "
            "spread_above_the_limit withholds the intent because spread_r is above that limit. "
            "spread_inside_the_limit keeps the intent. "
            "Pick one. An empty answer or a tie leaves this unset. Do not close an open ticket."
        ),
        "criteria": {
            "spread_above_the_limit": "spread_r is above limit. Withhold the intent.",
            "spread_inside_the_limit": "spread_r is not above limit. Keep the intent.",
        },
    },
    "permissions_spread": {
        "id": "permissions_spread",
        "withhold": "cents_above_the_max",
        "instructions": (
            "spread_cents is the measured spread. max_spread_cents is the configured maximum. "
            "cents_above_the_max withholds the trade because spread_cents is above that maximum. "
            "cents_inside_the_max does not withhold for this comparison. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "cents_above_the_max": "spread_cents is above max_spread_cents. Withhold the trade.",
            "cents_inside_the_max": "spread_cents is not above max_spread_cents. Do not withhold for spread.",
        },
    },
    "pretrade_spread": {
        "id": "pretrade_spread",
        "withhold": "spread_r_above_the_cell",
        "instructions": (
            "spread_r minus max_spread_r is wider than the tolerance. "
            "spread_r_above_the_cell withholds the trade. "
            "spread_r_inside_the_cell does not withhold for this comparison. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "spread_r_above_the_cell": "spread_r is above the cell limit by more than the tolerance. Withhold.",
            "spread_r_inside_the_cell": "spread_r is not above the cell limit by more than the tolerance. Do not withhold.",
        },
    },
    "pretrade_total": {
        "id": "pretrade_total",
        "withhold": "total_cost_above_the_limit",
        "instructions": (
            "total_cost_r minus max_total_cost_r is wider than the tolerance. "
            "total_cost_above_the_limit withholds the trade. "
            "total_cost_inside_the_limit does not withhold for this comparison. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "total_cost_above_the_limit": "total_cost_r is above the limit by more than the tolerance. Withhold.",
            "total_cost_inside_the_limit": "total_cost_r is not above the limit by more than the tolerance. Do not withhold.",
        },
    },
    "pretrade_swap_schedule": {
        "id": "pretrade_swap_schedule",
        "withhold": "swap_schedule_withholds",
        "instructions": (
            "The side-aware swap schedule source_status is not captured. "
            "swap_schedule_withholds withholds the trade because that schedule is missing. "
            "swap_schedule_is_captured does not withhold for the schedule. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "swap_schedule_withholds": "The swap schedule is not captured. Withhold the trade.",
            "swap_schedule_is_captured": "The swap schedule status does not withhold the trade.",
        },
    },
    "pretrade_swap_cost": {
        "id": "pretrade_swap_cost",
        "withhold": "swap_cost_withholds",
        "instructions": (
            "The side-aware swap cost conversion source_status is not captured. "
            "swap_cost_withholds withholds the trade because that conversion is missing. "
            "swap_cost_is_captured does not withhold for the conversion. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "swap_cost_withholds": "The swap cost conversion is not captured. Withhold the trade.",
            "swap_cost_is_captured": "The swap cost status does not withhold the trade.",
        },
    },
    "pretrade_slippage": {
        "id": "pretrade_slippage",
        "withhold": "slippage_missing_withholds",
        "instructions": (
            "A slippage model is required and expected_slippage_r is missing. "
            "slippage_missing_withholds withholds the trade. "
            "slippage_is_present does not withhold for slippage. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "slippage_missing_withholds": "Expected slippage is missing. Withhold the trade.",
            "slippage_is_present": "The slippage figure does not withhold the trade.",
        },
    },
    "pretrade_commission": {
        "id": "pretrade_commission",
        "withhold": "commission_cost_withholds",
        "instructions": (
            "Broker true commission cost_r is missing. The missing field is named. "
            "Do not invent a commission number. "
            "commission_cost_withholds withholds the trade because that cost is missing. "
            "commission_cost_stays_on_the_ask does not withhold. The ask stays. "
            "Pick one. An empty answer or a tie does not withhold."
        ),
        "criteria": {
            "commission_cost_withholds": "The missing commission cost withholds the trade.",
            "commission_cost_stays_on_the_ask": "The missing commission cost does not withhold. The ask stays.",
        },
    },
}

_MINE = (
    ("spread_r_exceeds_selected_cell_limit", "pretrade_spread"),
    ("total_cost_r_exceeds_limit", "pretrade_total"),
    ("missing_side_aware_swap_schedule", "pretrade_swap_schedule"),
    ("missing_side_aware_swap_cost_r_conversion", "pretrade_swap_cost"),
    ("missing_expected_slippage_r", "pretrade_slippage"),
    ("missing_broker_true_commission_cost_r_conversion", "pretrade_commission"),
)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _ask(state: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    from .rung_choice import ask_choice

    return ask_choice(
        state,
        question_id=str(spec["id"]),
        instructions=str(spec["instructions"]),
        criteria=dict(spec["criteria"]),
        timeout_s=None,
    )


def withholds(
    question: str,
    facts: Mapping[str, Any] | None = None,
    *,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> bool | None:
    """True only when this condition's withhold side is the unique highest.

    False only when the other side is the unique highest. An empty map, a
    tie, a missing choice, or an error stays unset. Never raises. Never
    skips the ask with a stored boolean.
    """

    spec = QUESTIONS.get(question)
    if spec is None:
        withholds.last = {"question": question, "withholds": None, "error": "unknown_question"}
        return None
    withhold = str(spec["withhold"])
    state = {
        "model": MODEL,
        "question": question,
        "facts": dict(facts or {}),
    }
    if ask is None:
        try:
            from .jev_client import calls_enabled

            if not calls_enabled():
                withholds.last = {"question": question, "withholds": None, "error": "calls_off"}
                return None
        except Exception as exc:  # noqa: BLE001
            withholds.last = {"question": question, "withholds": None, "error": type(exc).__name__}
            return None
        try:
            hop = _ask(state, spec) or {}
        except Exception as exc:  # noqa: BLE001
            withholds.last = {"question": question, "withholds": None, "error": type(exc).__name__}
            return None
    else:
        try:
            hop = ask(state, question_id=spec["id"], instructions=spec["instructions"], criteria=spec["criteria"]) or {}
        except Exception as exc:  # noqa: BLE001
            withholds.last = {"question": question, "withholds": None, "error": type(exc).__name__}
            return None
    if not isinstance(hop, dict) or not hop.get("decision_emitted"):
        withholds.last = {
            "question": question,
            "withholds": None,
            "choice": None,
            "probabilities": hop.get("probabilities") if isinstance(hop, dict) else {},
            "error": (hop.get("error") if isinstance(hop, dict) else None) or "no_unique_highest",
        }
        return None
    choice = hop.get("choice")
    if choice == withhold:
        blocked: bool | None = True
    elif choice in spec["criteria"]:
        blocked = False
    else:
        blocked = None
    withholds.last = {
        "question": question,
        "withholds": blocked,
        "choice": choice,
        "probabilities": hop.get("probabilities") or {},
        "error": None if blocked is not None else "no_unique_highest",
    }
    return blocked


withholds.last = {}


def _pretrade_facts(packet: Mapping[str, Any], reason: str) -> dict[str, Any]:
    tick_cost = _mapping(packet.get("tick_cost"))
    swap = _mapping(packet.get("swap"))
    swap_cost = _mapping(packet.get("swap_cost"))
    return {
        "reason": reason,
        "spread_r": tick_cost.get("spread_r"),
        "max_spread_r": packet.get("max_spread_r"),
        "cost_limit_tolerance_r": packet.get("cost_limit_tolerance_r"),
        "total_cost_r": packet.get("total_cost_r"),
        "max_total_cost_r": packet.get("max_total_cost_r"),
        "swap_source_status": swap.get("source_status"),
        "swap_cost_source_status": swap_cost.get("source_status"),
        "expected_slippage_r": packet.get("expected_slippage_r"),
        "slippage_model_required": bool(_mapping(packet.get("config_requirements")).get("slippage_model_required")),
        "commission_source_status": _mapping(packet.get("commission_cost")).get("source_status"),
        "commission_cost_r": _mapping(packet.get("commission_cost")).get("cost_r"),
        "commission_missing_fields": list(_mapping(packet.get("commission_cost")).get("missing_fields") or []),
    }


def filter_pretrade_block(
    packet: Mapping[str, Any] | None,
    refusal: str | None,
    *,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> str | None:
    """Keep non-cost reasons. Cost, spread, slippage, and swap reasons stay only when their withhold side wins."""

    if not refusal:
        return None
    if not isinstance(packet, Mapping):
        return None
    reasons = packet.get("refusal_reasons")
    if not isinstance(reasons, list) or not reasons:
        parts = [part for part in str(refusal).split(";") if part]
    else:
        parts = [str(part) for part in reasons if str(part)]
    kept: list[str] = []
    for part in parts:
        question = None
        for prefix, name in _MINE:
            if part.startswith(prefix):
                question = name
                break
        if question is None:
            kept.append(part)
            continue
        if withholds(question, _pretrade_facts(packet, part), ask=ask):
            kept.append(part)
    if not kept:
        return None
    return ";".join(kept)

"""Canonical units for predecision executable expected-value scoring."""

from __future__ import annotations

import math
from typing import Any


EXPECTED_VALUE_ALREADY_FILL_ADJUSTED = "already_fill_adjusted_expected_value"
EXPECTED_VALUE_GIVEN_FILL = "expected_value_given_fill"
PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL = (
    "payoff_magnitude_requires_outcome_and_fill"
)
LEGACY_UNTYPED_EXPECTED_VALUE = "legacy_untyped_expected_value"
LEGACY_UNTYPED_EXPECTED_VALUE_SOURCE = (
    "legacy_explicit_probability_and_fill_contract"
)

KNOWN_EXPECTED_VALUE_SEMANTICS = frozenset(
    {
        EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
        EXPECTED_VALUE_GIVEN_FILL,
        PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL,
        LEGACY_UNTYPED_EXPECTED_VALUE,
    }
)


def canonical_expected_net_r_semantics(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "already_fill_adjusted": EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
        "fill_adjusted_expected_value": EXPECTED_VALUE_ALREADY_FILL_ADJUSTED,
        "expected_value_conditional_on_fill": EXPECTED_VALUE_GIVEN_FILL,
        "conditional_on_fill": EXPECTED_VALUE_GIVEN_FILL,
        "payoff_magnitude": PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL,
        "legacy": LEGACY_UNTYPED_EXPECTED_VALUE,
    }
    return aliases.get(text, text if text in KNOWN_EXPECTED_VALUE_SEMANTICS else "")


def executable_expected_value(
    *,
    expected_net_r: Any,
    semantics: Any,
    probability: Any,
    execution_fill_probability: Any,
    source_completeness: Any,
) -> dict[str, Any]:
    """Apply only the multipliers that the declared expected-value unit needs."""

    def number(value: Any) -> float | None:
        if value in (None, "") or isinstance(value, bool):
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if math.isfinite(parsed) else None

    expected = number(expected_net_r)
    probability_value = number(probability)
    fill_value = number(execution_fill_probability)
    completeness_value = number(source_completeness)
    unit = canonical_expected_net_r_semantics(semantics)
    failures: list[str] = []
    if expected is None:
        failures.append("expected_net_r_missing")
    if completeness_value is None:
        failures.append("source_completeness_missing")
    if not unit:
        unit = LEGACY_UNTYPED_EXPECTED_VALUE
        failures.append("expected_net_r_semantics_missing_legacy_fallback")

    probability_multiplier = 1.0
    fill_multiplier = 1.0
    if unit == EXPECTED_VALUE_GIVEN_FILL:
        if fill_value is None:
            failures.append("execution_fill_probability_missing_for_conditional_value")
        else:
            fill_multiplier = max(0.0, min(1.0, fill_value))
    elif unit in {
        PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL,
        LEGACY_UNTYPED_EXPECTED_VALUE,
    }:
        if probability_value is None:
            failures.append("probability_missing_for_payoff_value")
        else:
            probability_multiplier = max(0.0, min(1.0, probability_value))
        if fill_value is None:
            failures.append("execution_fill_probability_missing_for_payoff_value")
        else:
            fill_multiplier = max(0.0, min(1.0, fill_value))

    completeness_multiplier = (
        max(0.0, min(1.0, completeness_value))
        if completeness_value is not None
        else 0.0
    )
    score = (
        max(0.0, expected)
        * probability_multiplier
        * fill_multiplier
        * completeness_multiplier
        if expected is not None
        else 0.0
    )
    hard_failures = [
        failure
        for failure in failures
        if failure != "expected_net_r_semantics_missing_legacy_fallback"
    ]
    return {
        "expected_net_r": expected,
        "expected_net_r_semantics": unit,
        "probability_multiplier": probability_multiplier,
        "execution_fill_probability_multiplier": fill_multiplier,
        "source_completeness_multiplier": completeness_multiplier,
        "executable_expected_value": score if not hard_failures else 0.0,
        "failures": failures,
        "legacy_semantics_fallback_applied": (
            "expected_net_r_semantics_missing_legacy_fallback" in failures
        ),
        "uses_outcome_fields": False,
    }


__all__ = [
    "EXPECTED_VALUE_ALREADY_FILL_ADJUSTED",
    "EXPECTED_VALUE_GIVEN_FILL",
    "KNOWN_EXPECTED_VALUE_SEMANTICS",
    "LEGACY_UNTYPED_EXPECTED_VALUE",
    "LEGACY_UNTYPED_EXPECTED_VALUE_SOURCE",
    "PAYOFF_MAGNITUDE_REQUIRES_OUTCOME_AND_FILL",
    "canonical_expected_net_r_semantics",
    "executable_expected_value",
]

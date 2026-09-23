"""S14 REGIME_GATE_SHADOW facade — emit + one System One call + compose.

Composes with the PR #29 fluid-gate sidecar. Never places.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .regime_buckets import RegimeBucketState, emit_regime_buckets
from .regime_compose import (
    RESEARCH_CONFIDENCE_THRESHOLD,
    RESEARCH_HALF_SIZE_THRESHOLD,
    RegimeAnswers,
    RegimeComposeResult,
    compose_regime_gate,
)
from .regime_system_one import RegimeAnswerCache, SystemOneResult, call_system_one


def evaluate_s14(
    gold_state: Mapping[str, Any] | None,
    harvest: Mapping[str, Any] | None = None,
    *,
    injected_answers: Mapping[str, Any] | None = None,
    cache: RegimeAnswerCache | None = None,
    occupancy: Mapping[str, Any] | None = None,
    confidence_threshold: float | None = None,
    half_size_threshold: float | None = None,
    research_thresholds: bool = False,
    offline_stub: Callable[[RegimeBucketState], Mapping[str, Any]] | None = None,
    g4_applies: bool = False,
    chair_doc: Mapping[str, Any] | None = None,
    favored_table: Mapping[str, tuple[str, ...]] | None = None,
) -> tuple[RegimeBucketState, SystemOneResult, RegimeComposeResult]:
    """Shadow evaluation. Flags / writes are owned by ``run_fluid_gate_cycle``."""

    state = emit_regime_buckets(gold_state, harvest)
    occ = occupancy
    if occ is None and isinstance(gold_state, Mapping):
        raw = gold_state.get("occupancy")
        occ = raw if isinstance(raw, Mapping) else None

    call = call_system_one(
        state,
        cache=cache,
        injected=injected_answers,
        offline_stub=offline_stub,
    )
    conf_t = confidence_threshold
    half_t = half_size_threshold
    if research_thresholds:
        if conf_t is None:
            conf_t = RESEARCH_CONFIDENCE_THRESHOLD
        if half_t is None:
            half_t = RESEARCH_HALF_SIZE_THRESHOLD

    composed = compose_regime_gate(
        state,
        call.answers,
        occupancy=occ,
        confidence_threshold=conf_t,
        half_size_threshold=half_t,
        favored_table=favored_table,
        cache_hit=call.cache_hit,
        g4_applies=g4_applies,
        chair_doc=chair_doc,
    )
    return state, call, composed


def s14_answers_as_injected(answers: RegimeAnswers | None) -> dict[str, Any]:
    if answers is None:
        return {}
    return {
        "regime_type": {
            "choice": answers.regime_type,
            "confidence": answers.regime_max_p,
            "probabilities": dict(answers.probabilities),
        },
        "regime_change_likely": {"noul": answers.regime_change_likely},
        "strategy_viable": {"noul": answers.strategy_viable},
    }

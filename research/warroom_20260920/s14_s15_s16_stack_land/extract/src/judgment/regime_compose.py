"""S14 code compose — Matchstick applyGate → GTOS shadow labels.

Outcomes are labels only: stand_down | half_size | admit_ok_label.
``size_factor`` is logged (0 | 0.5 | 1.0). Never order_send / place / remint.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .chair_enforce import ChairEnforceStamp, stamp_chair_enforce
from .conf_gate import confidence_band
from .regime_buckets import REGIME_TYPE_OPTIONS, RegimeBucketState

FAVORED_PATH = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "s14_favored_regimes.json"
)

VIABLE_FLOOR = 0.4
CHANGE_CEILING = 0.6
# Production default: unset until S15. Prove/research may pass starters.
CONFIDENCE_THRESHOLD_DEFAULT: float | None = None
HALF_SIZE_THRESHOLD_DEFAULT: float | None = None
RESEARCH_CONFIDENCE_THRESHOLD = 0.85
RESEARCH_HALF_SIZE_THRESHOLD = 0.50

GATE_DECISIONS = frozenset({"stand_down", "half_size", "admit_ok_label"})
SIZE_FACTORS = frozenset({0.0, 0.5, 1.0})
# Descending so snap-down picks the largest allowed factor ≤ Chair ceiling.
_ALLOWED_SIZE_ORDER = (1.0, 0.5, 0.0)


def snap_size_factor(size: float, ceiling: float) -> float:
    """Never boost. Emit only {0.0, 0.5, 1.0} at or below the Chair ceiling.

    G6's 0.75 session cut is a Chair ceiling, not a legal ``size_factor``.
    Snap it down to ``0.5`` (half_size) rather than emit 0.75 or round up.
    """

    try:
        cap = min(float(size), float(ceiling))
    except (TypeError, ValueError):
        return 0.0
    for value in _ALLOWED_SIZE_ORDER:
        if value <= cap + 1e-12:
            return value
    return 0.0


def load_favored_regimes(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    target = path if path is not None else FAVORED_PATH
    if not target.is_file():
        return {}
    doc = json.loads(target.read_text(encoding="utf-8"))
    families = doc.get("families") if isinstance(doc.get("families"), Mapping) else {}
    out: dict[str, tuple[str, ...]] = {}
    for name, values in families.items():
        if isinstance(values, (list, tuple)):
            out[str(name)] = tuple(str(v) for v in values)
    return out


def favored_for(sleeve: str | None, table: Mapping[str, tuple[str, ...]] | None = None) -> tuple[str, ...] | None:
    if not sleeve:
        return None
    fams = table if table is not None else load_favored_regimes()
    if sleeve in fams:
        return fams[sleeve]
    # prefix / family match (dsp_spring_close → dsp_spring → spring)
    raw = sleeve.lower()
    for key, values in fams.items():
        k = key.lower()
        if raw == k or raw.startswith(k + "_") or raw.startswith(k):
            return values
    return None


def _max_p(probabilities: Mapping[str, Any] | None) -> float | None:
    if not probabilities:
        return None
    nums: list[float] = []
    for value in probabilities.values():
        try:
            nums.append(float(value))
        except (TypeError, ValueError):
            continue
    if not nums:
        return None
    return max(nums)


def _is_unclear_equal(probabilities: Mapping[str, Any] | None) -> bool:
    if not probabilities:
        return True
    nums: list[float] = []
    for opt in REGIME_TYPE_OPTIONS:
        try:
            nums.append(float(probabilities.get(opt)))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
    if len(nums) != 5:
        return False
    return max(nums) - min(nums) <= 1e-9


@dataclass(frozen=True)
class RegimeAnswers:
    regime_type: str | None
    probabilities: dict[str, float]
    regime_max_p: float | None
    regime_change_likely: float | None
    strategy_viable: float | None
    source: str
    malformed: bool
    unclear_equal: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "regime_type": self.regime_type,
            "probabilities": dict(self.probabilities),
            "regime_max_p": self.regime_max_p,
            "regime_change_likely": self.regime_change_likely,
            "strategy_viable": self.strategy_viable,
            "source": self.source,
            "malformed": self.malformed,
            "unclear_equal": self.unclear_equal,
        }


def parse_regime_answers(answers: Mapping[str, Any] | None, *, source: str = "injected") -> RegimeAnswers:
    if not answers:
        return RegimeAnswers(None, {}, None, None, None, source, True, True)
    choice_block = answers.get("regime_type")
    if not isinstance(choice_block, Mapping):
        return RegimeAnswers(None, {}, None, None, None, source, True, True)
    raw_choice = choice_block.get("choice")
    choice = str(raw_choice) if raw_choice is not None else None
    if choice is not None and choice not in REGIME_TYPE_OPTIONS:
        choice = None
    probs_in = choice_block.get("probabilities")
    probs: dict[str, float] = {}
    if isinstance(probs_in, Mapping):
        for key, val in probs_in.items():
            try:
                probs[str(key)] = float(val)
            except (TypeError, ValueError):
                continue
    max_p = _max_p(probs)
    if max_p is None:
        try:
            max_p = float(choice_block.get("confidence"))
        except (TypeError, ValueError):
            max_p = None
    change = None
    viable = None
    ch = answers.get("regime_change_likely")
    if isinstance(ch, Mapping) and "noul" in ch:
        try:
            change = float(ch["noul"])
        except (TypeError, ValueError):
            change = None
    sv = answers.get("strategy_viable")
    if isinstance(sv, Mapping) and "noul" in sv:
        try:
            viable = float(sv["noul"])
        except (TypeError, ValueError):
            viable = None
    malformed = choice is None or change is None or viable is None
    unclear = _is_unclear_equal(probs) or (choice == "unclear" and (max_p is None or max_p <= 0.25))
    return RegimeAnswers(
        regime_type=choice,
        probabilities=probs,
        regime_max_p=max_p,
        regime_change_likely=change,
        strategy_viable=viable,
        source=source,
        malformed=malformed,
        unclear_equal=unclear and malformed is False and (max_p is not None and abs((max_p or 0) - 0.2) < 1e-6),
    )


@dataclass(frozen=True)
class RegimeComposeResult:
    gate_decision: str | None
    size_factor: float | None
    reason: str
    decidable: bool
    consume: bool
    conf_band: str
    disposition_candidate: str | None
    favored_regimes: tuple[str, ...] | None
    chair: ChairEnforceStamp
    answers: RegimeAnswers | None
    cache_key: str
    cache_hit: bool
    thresholds: dict[str, object]
    notes: tuple[str, ...]
    broker_effect: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "steal": "S14",
            "label": "REGIME_GATE_SHADOW",
            "regime_type": None if self.answers is None else self.answers.regime_type,
            "regime_max_p": None if self.answers is None else self.answers.regime_max_p,
            "regime_change_likely": None if self.answers is None else self.answers.regime_change_likely,
            "strategy_viable": None if self.answers is None else self.answers.strategy_viable,
            "gate_decision": self.gate_decision,
            "size_factor": self.size_factor,
            "reason": self.reason,
            "decidable": self.decidable,
            "consume": self.consume,
            "conf_band": self.conf_band,
            "disposition_candidate": self.disposition_candidate,
            "favored_regimes": list(self.favored_regimes) if self.favored_regimes is not None else None,
            "chair_enforce": self.chair.as_dict(),
            "answers": None if self.answers is None else self.answers.as_dict(),
            "cache_key": self.cache_key,
            "cache_hit": self.cache_hit,
            "thresholds": dict(self.thresholds),
            "notes": list(self.notes),
            "broker_effect": False,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
        }


def _stand(
    reason: str,
    *,
    state: RegimeBucketState,
    answers: RegimeAnswers | None,
    chair: ChairEnforceStamp,
    notes: list[str],
    consume: bool,
    decidable: bool,
    cache_hit: bool,
    thresholds: dict[str, object],
    favored: tuple[str, ...] | None,
    band: str = "LOW",
) -> RegimeComposeResult:
    cand = None
    if consume and decidable:
        cand = "HOLD" if state.context.get("occupancy.corr_hold_named") else "ABSTAIN"
    return RegimeComposeResult(
        gate_decision="stand_down",
        size_factor=0.0,
        reason=reason,
        decidable=decidable,
        consume=consume,
        conf_band=band,
        disposition_candidate=cand,
        favored_regimes=favored,
        chair=chair,
        answers=answers,
        cache_key=state.cache_key,
        cache_hit=cache_hit,
        thresholds=thresholds,
        notes=tuple(notes),
    )


def compose_regime_gate(
    state: RegimeBucketState,
    answers: RegimeAnswers | None,
    *,
    occupancy: Mapping[str, Any] | None = None,
    viable_floor: float = VIABLE_FLOOR,
    change_ceiling: float = CHANGE_CEILING,
    confidence_threshold: float | None = CONFIDENCE_THRESHOLD_DEFAULT,
    half_size_threshold: float | None = HALF_SIZE_THRESHOLD_DEFAULT,
    favored_table: Mapping[str, tuple[str, ...]] | None = None,
    cache_hit: bool = False,
    g4_applies: bool = False,
    chair_doc: Mapping[str, Any] | None = None,
) -> RegimeComposeResult:
    """Fail-closed compose. Labels only."""

    notes = ["s14_regime_gate_shadow", "integers_own_place"]
    thresholds = {
        "viable_floor": viable_floor,
        "change_ceiling": change_ceiling,
        "confidence_threshold": confidence_threshold,
        "half_size_threshold": half_size_threshold,
        "thresholds_class": "research_starter" if confidence_threshold is not None else "s15_unset_fail_closed",
        "calibrate_via_s15": True,
    }
    sleeve = state.identity.get("sleeve")
    symbol = state.identity.get("symbol")
    session = state.context.get("sessions.named")
    occ = occupancy if occupancy is not None else {}
    chair = stamp_chair_enforce(
        sleeve=str(sleeve) if sleeve else None,
        symbol=str(symbol) if symbol else None,
        session_named=str(session) if session else None,
        occupancy=occ,
        chair_doc=chair_doc,
        g4_applies=g4_applies,
    )
    favored = favored_for(str(sleeve) if sleeve else None, favored_table)

    if not state.state_sufficient_for_live:
        notes.append("incomplete_state_log_only")
        return RegimeComposeResult(
            gate_decision=None,
            size_factor=None,
            reason="incomplete_state",
            decidable=False,
            consume=False,
            conf_band="LOW",
            disposition_candidate=None,
            favored_regimes=favored,
            chair=chair,
            answers=answers,
            cache_key=state.cache_key,
            cache_hit=cache_hit,
            thresholds=thresholds,
            notes=tuple(notes),
        )

    if answers is None or answers.malformed:
        notes.append("jev_down_or_malformed_no_move_credit")
        return RegimeComposeResult(
            gate_decision=None,
            size_factor=None,
            reason="non_decidable_malformed_or_missing_answers",
            decidable=False,
            consume=False,
            conf_band="LOW",
            disposition_candidate=None,
            favored_regimes=favored,
            chair=chair,
            answers=answers,
            cache_key=state.cache_key,
            cache_hit=cache_hit,
            thresholds=thresholds,
            notes=tuple(notes),
        )

    if answers.unclear_equal:
        notes.append("unclear_at_equal_no_move_credit")
        return RegimeComposeResult(
            gate_decision=None,
            size_factor=None,
            reason="non_decidable_unclear_equal",
            decidable=False,
            consume=False,
            conf_band="LOW",
            disposition_candidate=None,
            favored_regimes=favored,
            chair=chair,
            answers=answers,
            cache_key=state.cache_key,
            cache_hit=cache_hit,
            thresholds=thresholds,
            notes=tuple(notes),
        )

    band = confidence_band(answers.regime_max_p)
    max_p = answers.regime_max_p

    if chair.hard_off:
        notes.append("chair_hard_off_not_weakened")
        return _stand(
            chair.hard_off_reason or "chair_hard_off",
            state=state,
            answers=answers,
            chair=chair,
            notes=notes,
            consume=True,
            decidable=True,
            cache_hit=cache_hit,
            thresholds=thresholds,
            favored=favored,
            band="VETO" if band == "VETO" else band,
        )

    if chair.g8_block_reentry:
        notes.append("g8_block_reentry_same_sleeve")
        return _stand(
            "g8_block_reentry_same_sleeve",
            state=state,
            answers=answers,
            chair=chair,
            notes=notes,
            consume=True,
            decidable=True,
            cache_hit=cache_hit,
            thresholds=thresholds,
            favored=favored,
            band=band,
        )

    if favored is None:
        notes.append("favored_regimes_missing_fail_closed")
        return _stand(
            "favored_regimes_missing",
            state=state,
            answers=answers,
            chair=chair,
            notes=notes,
            consume=True,
            decidable=True,
            cache_hit=cache_hit,
            thresholds=thresholds,
            favored=None,
            band=band,
        )

    viable = answers.strategy_viable
    change = answers.regime_change_likely
    if viable is not None and viable < viable_floor:
        return _stand(
            "strategy_viable_below_floor",
            state=state,
            answers=answers,
            chair=chair,
            notes=notes,
            consume=True,
            decidable=True,
            cache_hit=cache_hit,
            thresholds=thresholds,
            favored=favored,
            band=band,
        )
    if change is not None and change > change_ceiling:
        return _stand(
            "regime_change_likely_above_ceiling",
            state=state,
            answers=answers,
            chair=chair,
            notes=notes,
            consume=True,
            decidable=True,
            cache_hit=cache_hit,
            thresholds=thresholds,
            favored=favored,
            band=band,
        )
    if answers.regime_type not in favored:
        return _stand(
            "regime_type_not_in_favored",
            state=state,
            answers=answers,
            chair=chair,
            notes=notes,
            consume=True,
            decidable=True,
            cache_hit=cache_hit,
            thresholds=thresholds,
            favored=favored,
            band=band,
        )

    decision = "stand_down"
    size = 0.0
    reason = "s15_thresholds_unset_prefer_stand_down"
    if confidence_threshold is not None and max_p is not None and max_p >= confidence_threshold:
        decision = "admit_ok_label"
        size = 1.0
        reason = "regime_match_high_conf_label_only"
        notes.append("admit_ok_label_never_maps_to_order_send")
    elif half_size_threshold is not None and max_p is not None and max_p >= half_size_threshold:
        decision = "half_size"
        size = 0.5
        reason = "regime_match_half_size_tilt_candidate"
        notes.append("half_size_shadow_only")
    else:
        notes.append("prefer_stand_down_until_s15")

    snapped = snap_size_factor(size, chair.size_ceiling)
    if snapped < size or size > chair.size_ceiling:
        notes.append("chair_size_ceiling_applied_no_boost")
        if chair.g6_size_ceiling is not None and chair.size_ceiling < 1.0:
            notes.append("g6_ceiling_snapped_to_allowed_size_factor")
        if chair.g4_size_ceiling is not None and snapped <= 0.5:
            notes.append("g4_allow_with_cut_snapped")
        if chair.keep_family:
            notes.append("g7_keep_no_boost")
        size = snapped
        if size <= 0.0:
            decision = "stand_down"
            reason = "chair_size_ceiling_stand_down"
        elif size <= 0.5 and decision == "admit_ok_label":
            decision = "half_size"
            reason = "chair_size_ceiling_cut_to_half_size"
    else:
        size = snapped

    assert decision in GATE_DECISIONS
    assert size in SIZE_FACTORS
    cand = None
    if decision == "stand_down":
        cand = "HOLD" if state.context.get("occupancy.corr_hold_named") else "ABSTAIN"
    return RegimeComposeResult(
        gate_decision=decision,
        size_factor=size,
        reason=reason,
        decidable=True,
        consume=True,
        conf_band=band,
        disposition_candidate=cand,
        favored_regimes=favored,
        chair=chair,
        answers=answers,
        cache_key=state.cache_key,
        cache_hit=cache_hit,
        thresholds=thresholds,
        notes=tuple(notes),
    )

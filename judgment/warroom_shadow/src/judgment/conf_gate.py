"""CONF_GATE — log LOW / MED / HIGH; never auto-broker.

Confidence is distribution concentration, not accuracy and not permission.
Starter bands (calibrate on labeled Challenge tape; not truth):

* LOW  < 0.50  → stay SHADOW
* MED  0.50–0.85 → SHADOW + REVIEW
* HIGH ≥ 0.85 → eligible for APPLY only if stake + prove + flag allow

Place / remint / flatten / order path is VETO at every band.
Noul has no separate confidence — use distance from 0.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from .veto import is_broker_or_payout_action

Band = Literal["LOW", "MED", "HIGH", "VETO"]

LOW_MAX = 0.50
HIGH_MIN = 0.85

#: V2 secondary abstain floor (lab starting). Logged, not a KEEP threshold.
V2_SECONDARY_ABSTAIN_FLOOR = 0.55

STAKE_REQUIRED_BAND: dict[str, str] = {
    "read_only": "MED",
    "label_assist": "MED",
    "review": "MED",
    "sleeve_admit": "HIGH",
    "corr_hold": "HIGH",
    "place": "VETO",
    "remint": "VETO",
    "flatten": "VETO",
    "broker": "VETO",
    "order": "VETO",
}


def confidence_band(confidence: float | None) -> Band:
    if confidence is None:
        return "LOW"
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return "LOW"
    if value < 0.0 or value > 1.0:
        return "LOW"
    if value < LOW_MAX:
        return "LOW"
    if value >= HIGH_MIN:
        return "HIGH"
    return "MED"


def noul_concentration(noul: float) -> float:
    """Noul has no separate confidence; distance from 0.5 scaled to ``[0, 1]``."""

    return abs(float(noul) - 0.5) * 2.0


def required_band_for_stake(stake: str) -> str:
    name = str(stake or "").strip().lower()
    if is_broker_or_payout_action(name):
        return "VETO"
    return STAKE_REQUIRED_BAND.get(name, "HIGH")


def extract_confidence(
    answers: Mapping[str, object] | None,
    *,
    key: str = "next_gate",
) -> tuple[float | None, str]:
    """Pull Choice/Score confidence, or Noul concentration, from injected answers."""

    if not answers:
        return None, "answers_absent"
    payload = answers.get(key)
    if payload is None and len(answers) == 1:
        payload = next(iter(answers.values()))
    if not isinstance(payload, Mapping):
        return None, "answers_unreadable"
    if "confidence" in payload:
        try:
            return float(payload["confidence"]), "choice_or_score_confidence"
        except (TypeError, ValueError):
            return None, "confidence_unreadable"
    if "noul" in payload:
        try:
            return noul_concentration(float(payload["noul"])), "noul_distance_from_half"
        except (TypeError, ValueError):
            return None, "noul_unreadable"
    return None, "no_confidence_field"


@dataclass(frozen=True)
class ConfGateLog:
    """Shadow log row for one judgment. ``broker_effect`` is always False."""

    confidence: float | None
    band: Band
    stake: str
    required_band: str
    source: str
    below_v2_secondary_floor: bool
    broker_effect: bool
    review_flag: bool
    disposition: str

    def as_dict(self) -> dict[str, object]:
        return {
            "confidence": self.confidence,
            "band": self.band,
            "stake": self.stake,
            "required_band": self.required_band,
            "source": self.source,
            "below_v2_secondary_floor": self.below_v2_secondary_floor,
            "broker_effect": self.broker_effect,
            "review_flag": self.review_flag,
            "disposition": self.disposition,
        }


def log_conf_gate(
    confidence: float | None,
    *,
    stake: str,
    source: str = "choice_or_score_confidence",
) -> ConfGateLog:
    """Band the number. Never sets broker_effect True."""

    required = required_band_for_stake(stake)
    if required == "VETO":
        band: Band = "VETO"
        disposition = "veto_place_path"
        review = True
    else:
        band = confidence_band(confidence)
        if band == "LOW":
            disposition = "shadow_only"
            review = False
        elif band == "MED":
            disposition = "shadow_review"
            review = True
        else:
            disposition = "shadow_high_eligible_if_prove"
            review = False
    below = confidence is None or float(confidence) < V2_SECONDARY_ABSTAIN_FLOOR
    return ConfGateLog(
        confidence=None if confidence is None else float(confidence),
        band=band,
        stake=stake,
        required_band=required,
        source=source,
        below_v2_secondary_floor=below,
        broker_effect=False,
        review_flag=review or band in {"MED", "VETO"},
        disposition=disposition,
    )

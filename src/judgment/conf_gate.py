"""CONF_GATE — log LOW / MED / HIGH plus S15 COST_OF_ERROR shadow.

Confidence is distribution concentration, not accuracy and not permission.

Vendor 0.50 / 0.85 bands are a **naive baseline for the 'moved' scorecard
only** — they are not Challenge truth (``vendor_0_85_forbidden_as_truth``).
S15 authors tape-authority costs beside ADM/SIZ rows and picks
YES / NO / UNSURE. Close Loop SHADOW bands (STRICT / SESSION / EVENT /
REVIEW) are labels; never APPLY.

* LOW  < 0.50  → naive NO (stay SHADOW)
* MED  0.50–0.85 → naive UNSURE (SHADOW + REVIEW)
* HIGH ≥ 0.85 → naive YES (still not permission)

Place / remint / flatten / order path is **infinity VETO** at every band.
Noul has no separate confidence — use distance from 0.5.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from .veto import is_broker_or_payout_action

Band = Literal["LOW", "MED", "HIGH", "VETO"]
CostPick = Literal["YES", "NO", "UNSURE", "VETO"]

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
    "size_tilt": "HIGH",
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


def noul_vs_choice_shape(
    *,
    choice_confidence: float | None,
    noul: float | None,
) -> dict[str, object]:
    """APPLY_CANDIDATE consume: Choice confidence vs Noul concentration.

    Disagreement is logged. It never authorizes a broker send.
    """

    if choice_confidence is None or noul is None:
        return {
            "schema": "gtos.judgment.noul_vs_choice_shape.v1",
            "consume": "noul_vs_choice_shape",
            "decidable": False,
            "agree": None,
            "choice_band": None if choice_confidence is None else confidence_band(choice_confidence),
            "noul_band": None if noul is None else confidence_band(noul_concentration(noul)),
            "never_place": True,
            "broker_effect": False,
        }
    choice_band = confidence_band(choice_confidence)
    noul_band = confidence_band(noul_concentration(noul))
    return {
        "schema": "gtos.judgment.noul_vs_choice_shape.v1",
        "consume": "noul_vs_choice_shape",
        "decidable": True,
        "agree": choice_band == noul_band,
        "choice_confidence": float(choice_confidence),
        "noul": float(noul),
        "noul_concentration": noul_concentration(noul),
        "choice_band": choice_band,
        "noul_band": noul_band,
        "never_place": True,
        "broker_effect": False,
    }


@dataclass(frozen=True)
class ConfOrderBlock:
    """CONF_ORDER_CONSUME already-live stamp. HIGH blocks; vendor det false → MED.

    ``broker_effect`` is always False. Dig never order_sends.
    """

    confidence: float | None
    band: Band
    vendor_deterministic: bool
    vendor_det_false_downgraded: bool
    blocked: bool
    disposition: str
    stake: str
    shape: dict[str, object]
    consume: str = "CONF_ORDER_CONSUME"
    never_place: bool = True
    broker_effect: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": "gtos.judgment.conf_gate_order_block.v1",
            "consume": self.consume,
            "already_live": True,
            "confidence": self.confidence,
            "band": self.band,
            "vendor_deterministic": self.vendor_deterministic,
            "vendor_det_false_downgraded": self.vendor_det_false_downgraded,
            "vendor_0_85_forbidden_as_truth": True,
            "blocked": self.blocked,
            "disposition": self.disposition,
            "stake": self.stake,
            "noul_vs_choice_shape": self.shape,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
            "broker_effect": False,
            "dig_never_broker_send": True,
        }


def conf_gate_order_block(
    confidence: float | None,
    *,
    vendor_deterministic: bool = False,
    stake: str = "sleeve_admit",
    choice_confidence: float | None = None,
    noul: float | None = None,
) -> ConfOrderBlock:
    """HIGH block on the conf/order path. Vendor det false → MED.

    Vendor 0.50 / 0.85 is not Challenge truth. A HIGH that is only a
    vendor number is downgraded to MED (review, not a hard block).
    Place / remint / flatten stakes stay VETO. Never sets broker_effect.
    """

    shape = noul_vs_choice_shape(choice_confidence=choice_confidence, noul=noul)
    if is_broker_or_payout_action(stake):
        return ConfOrderBlock(
            confidence=None if confidence is None else float(confidence),
            band="VETO",
            vendor_deterministic=bool(vendor_deterministic),
            vendor_det_false_downgraded=False,
            blocked=True,
            disposition="veto_place_path",
            stake=stake,
            shape=shape,
        )

    band = confidence_band(confidence)
    downgraded = False
    if not vendor_deterministic and band == "HIGH":
        band = "MED"
        downgraded = True
    if shape.get("decidable") and shape.get("agree") is False and band == "HIGH":
        band = "MED"
        downgraded = True

    if band == "HIGH":
        blocked = True
        disposition = "order_block_high"
    elif band == "MED":
        blocked = False
        disposition = "order_review_med"
    else:
        blocked = False
        disposition = "shadow_only"

    return ConfOrderBlock(
        confidence=None if confidence is None else float(confidence),
        band=band,
        vendor_deterministic=bool(vendor_deterministic),
        vendor_det_false_downgraded=downgraded,
        blocked=blocked,
        disposition=disposition,
        stake=stake,
        shape=shape,
    )


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
            "vendor_0_85_band": self.band,
            "vendor_0_85_forbidden_as_truth": True,
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


# --- S15 COST_OF_ERROR (same admit sidecar; never place) -------------------

COST_MATRIX_PATH = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "s15_cost_matrix.json"
)
CONF_GATE_BANDS_PATH = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "s15_conf_gate_bands.json"
)

TAPE_SUBCLASS_TO_GATE: dict[str, str] = {
    "fs_half_still_losing": "TAPE_FALSE_ADMIT.fs_half_still_losing",
    "event_gap_shadow": "TAPE_FALSE_ADMIT.event_gap_shadow",
    "session_cut_loss": "TAPE_FALSE_ADMIT.session_cut_loss",
    "full_size_loss": "TAPE_FALSE_ADMIT.full_size_loss",
    "false_admit": "TAPE_FALSE_ADMIT",
    "false_abstain": "TAPE_FALSE_ABSTAIN",
    "cost_avoided_by_reject": "TAPE_COST_AVOIDED_BY_REJECT",
    "review_keep_offhours_false_structure": "TAPE_REVIEW_KEEP_OFFHOURS_FS",
}

SHADOW_BAND_BY_SUBCLASS: dict[str, tuple[str, str]] = {
    "fs_half_still_losing": ("CONF_GATE_STRICT", "HIGH"),
    "session_cut_loss": ("CONF_GATE_SESSION", "MED_HIGH"),
    "event_gap_shadow": ("CONF_GATE_EVENT", "HIGH_EVENT_STAMP"),
    "full_size_loss": ("CONF_GATE_REVIEW", "KEEP_SURFACE"),
}

REVIEW_KEEP_TICKET = "291087142"
REVIEW_OFFHOURS_TICKET = "293128383"

#: Close Loop Challenge 0 ticket → false_admit subclass (tape authority).
TICKET_SUBCLASS: dict[str, str] = {
    "291072108": "fs_half_still_losing",
    "291096187": "fs_half_still_losing",
    "291210052": "fs_half_still_losing",
    "291234829": "fs_half_still_losing",
    "291486315": "fs_half_still_losing",
    "291549869": "fs_half_still_losing",
    "291713652": "fs_half_still_losing",
    "291758207": "fs_half_still_losing",
    "291778371": "fs_half_still_losing",
    "292513484": "fs_half_still_losing",
    "292524534": "fs_half_still_losing",
    "292876275": "fs_half_still_losing",
    "293024386": "fs_half_still_losing",
    "293437038": "fs_half_still_losing",
    "293564978": "fs_half_still_losing",
    "293592749": "fs_half_still_losing",
    "293414629": "fs_half_still_losing",
    "293650737": "fs_half_still_losing",
    "293669979": "fs_half_still_losing",
    "293707634": "fs_half_still_losing",
    "293765156": "fs_half_still_losing",
    "291383082": "event_gap_shadow",
    "293332188": "event_gap_shadow",
    "293611741": "event_gap_shadow",
    "291392252": "session_cut_loss",
    "283024183": "session_cut_loss",
    "285296282": "session_cut_loss",
    "293435759": "session_cut_loss",
    REVIEW_KEEP_TICKET: "full_size_loss",
    REVIEW_OFFHOURS_TICKET: "review_keep_offhours_false_structure",
}

_TIE_EPS = 1e-12
_matrix_cache: dict[str, Any] | None = None
_bands_cache: dict[str, Any] | None = None


def load_cost_matrix(path: Path | None = None) -> dict[str, Any]:
    """Tape-authority cost matrix. Research priors stay demoted."""

    global _matrix_cache
    target = path if path is not None else COST_MATRIX_PATH
    if path is None and _matrix_cache is not None:
        return _matrix_cache
    if not target.is_file():
        return {
            "schema": "gtos.dig.s15.cost_matrix.v2_tape_authority",
            "rows_tape_authority": [],
            "rows_research_priors_demoted": [],
            "key_facts": {"false_abstain": 0, "g4_x_g6_overshrink": False},
        }
    doc = json.loads(target.read_text(encoding="utf-8"))
    if path is None:
        _matrix_cache = doc
    return doc


def load_conf_gate_bands(path: Path | None = None) -> dict[str, Any]:
    global _bands_cache
    target = path if path is not None else CONF_GATE_BANDS_PATH
    if path is None and _bands_cache is not None:
        return _bands_cache
    if not target.is_file():
        return {"ranked_by_shadow_residual": []}
    doc = json.loads(target.read_text(encoding="utf-8"))
    if path is None:
        _bands_cache = doc
    return doc


def tape_authority_facts(matrix: Mapping[str, Any] | None = None) -> dict[str, object]:
    """Close Loop key facts that must appear on every S15 sidecar row."""

    doc = matrix if matrix is not None else load_cost_matrix()
    facts = doc.get("key_facts") if isinstance(doc.get("key_facts"), Mapping) else {}
    return {
        "schema": str(doc.get("schema") or "gtos.dig.s15.cost_matrix.v2_tape_authority"),
        "authority": "close_loop.s15_cost_matrix_from_tape.v1",
        "false_abstain": int(facts.get("false_abstain", 0)),
        "false_admit_n": int(facts.get("false_admit_n", 29)),
        "false_admit_tape_R": float(facts.get("false_admit_tape_R", -28.9172)),
        "false_admit_shadow_R": float(facts.get("false_admit_shadow_R", -13.5428)),
        "cost_avoided_by_reject_n": int(facts.get("cost_avoided_by_reject_n", 23)),
        "cost_avoided_by_reject_tape_R": float(facts.get("cost_avoided_by_reject_tape_R", -24.6586)),
        "g4_x_g6_overshrink": False,
        "place": "infinity_veto",
        "new_hard_off": False,
        "review_keep_ticket": REVIEW_KEEP_TICKET,
        "review_keep_offhours_ticket": REVIEW_OFFHOURS_TICKET,
        "review_keep_not_hard_off": True,
        "vendor_0_85_forbidden_as_truth": True,
    }


def _is_review_keep_offhours(subclass: str | None, ticket: str | None) -> bool:
    return subclass == "review_keep_offhours_false_structure" or ticket == REVIEW_OFFHOURS_TICKET


def _index_tape_rows(matrix: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    doc = matrix if matrix is not None else load_cost_matrix()
    out: dict[str, dict[str, Any]] = {}
    for row in doc.get("rows_tape_authority") or []:
        if isinstance(row, Mapping) and row.get("gate_id"):
            out[str(row["gate_id"])] = dict(row)
    return out


def resolve_tape_cost_row(
    gate_id: str | None,
    *,
    matrix: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Authority rows only. Demoted gut priors do not derive a pick or band."""

    if not gate_id:
        return None
    return _index_tape_rows(matrix).get(str(gate_id))


def naive_vendor_choice(p: float | None) -> str:
    """Vendor 0.85 / 0.50 baseline — comparison only, never truth."""

    band = confidence_band(p)
    if band == "HIGH":
        return "YES"
    if band == "MED":
        return "UNSURE"
    return "NO"


def pick_cost_of_error(
    p: float | None,
    *,
    cost_false_yes: float,
    cost_false_no: float,
    cost_human: float,
) -> tuple[CostPick, dict[str, float]]:
    """Gut rule: argmin E[YES]/E[NO]/E[HUMAN]; ties → UNSURE then NO."""

    if p is None:
        raise ValueError("p is required to pick")
    prob = float(p)
    if prob < 0.0 or prob > 1.0:
        raise ValueError("p must be in [0, 1]")
    e_yes = (1.0 - prob) * float(cost_false_yes)
    e_no = prob * float(cost_false_no)
    e_human = float(cost_human)
    scores = {"YES": e_yes, "NO": e_no, "UNSURE": e_human}
    min_e = min(scores.values())
    tied = [name for name, value in scores.items() if abs(value - min_e) <= _TIE_EPS]
    if "UNSURE" in tied:
        chosen: CostPick = "UNSURE"
    elif "NO" in tied:
        chosen = "NO"
    else:
        chosen = "YES"
    return chosen, {"e_yes": e_yes, "e_no": e_no, "e_human": e_human}


def extract_ticket(
    gold_state: Mapping[str, Any] | None = None,
    *,
    explicit: str | int | None = None,
) -> str | None:
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    if not gold_state:
        return None
    identity = gold_state.get("identity") if isinstance(gold_state.get("identity"), Mapping) else {}
    raw = identity.get("ticket") if isinstance(identity, Mapping) else None
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    cid = str(identity.get("candidate_id") or "") if isinstance(identity, Mapping) else ""
    parts = cid.split(":")
    if len(parts) >= 3 and parts[0] == "challenge":
        return parts[2]
    return None


def _stamped_event_proximity(gold_state: Mapping[str, Any] | None) -> bool:
    """EVENT band only from stamped proximity. Empty spine stays empty."""

    if not gold_state:
        return False
    news = gold_state.get("news") if isinstance(gold_state.get("news"), Mapping) else {}
    if not isinstance(news, Mapping):
        return False
    if news.get("spine_empty") is True:
        return False
    events = news.get("events") or []
    if not isinstance(events, (list, tuple)):
        return False
    for event in events:
        if not isinstance(event, Mapping):
            continue
        if event.get("source") == "stamped" or event.get("stamped") is True:
            return True
    return False


def classify_s15_subclass(
    *,
    stake: str,
    ticket: str | None = None,
    subclass: str | None = None,
    gold_state: Mapping[str, Any] | None = None,
    regime: Any | None = None,
) -> str | None:
    """Map a sidecar row to a tape subclass. Place stake is ANY_PLACE."""

    if is_broker_or_payout_action(stake):
        return "any_place"
    if subclass:
        return str(subclass)
    if ticket and str(ticket) in TICKET_SUBCLASS:
        return TICKET_SUBCLASS[str(ticket)]
    chair = getattr(regime, "chair", None) if regime is not None else None
    if chair is not None and getattr(chair, "hard_off", False):
        return "cost_avoided_by_reject"
    if _stamped_event_proximity(gold_state):
        return "event_gap_shadow"
    if chair is not None and getattr(chair, "g4_size_ceiling", None) is not None:
        if not getattr(chair, "keep_family", False):
            return "fs_half_still_losing"
    if chair is not None and getattr(chair, "g6_size_ceiling", None) is not None:
        if not getattr(chair, "keep_family", False):
            return "session_cut_loss"
    if chair is not None and getattr(chair, "keep_family", False):
        if ticket == REVIEW_KEEP_TICKET:
            return "full_size_loss"
        session = None
        if gold_state and isinstance(gold_state.get("sessions"), Mapping):
            session = gold_state["sessions"].get("named")
        sess = str(session or "").strip().lower()
        if sess in {"off_hours", "offhours"}:
            return "review_keep_offhours_false_structure"
    return None


def _triple(row: Mapping[str, Any] | None) -> tuple[float, float, float] | None:
    if not row:
        return None
    try:
        yes = row.get("cost_false_yes")
        no = row.get("cost_false_no")
        human = row.get("cost_human")
        if yes is None or no is None or human is None:
            return None
        return float(yes), float(no), float(human)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class CostOfErrorLog:
    """S15 shadow cost row. ``broker_effect`` is always False. Never place."""

    p: float | None
    stake: str
    gate_id: str | None
    subclass: str | None
    ticket: str | None
    cost_false_yes: float | None
    cost_false_no: float | None
    cost_human: float | None
    e_yes: float | None
    e_no: float | None
    e_human: float | None
    chosen: str | None
    naive_vendor_choice: str
    moved: bool
    conf_gate_band: str | None
    conf_floor: str | None
    conf_band_derived: str | None
    authority: str | None
    reason: str
    benefit_abs_R: float | None
    g4_x_g6_overshrink: bool
    keep_no_boost: bool
    label_only: bool
    place_veto: bool
    news_protocol: str
    new_hard_off: bool = False
    review_keep_offhours: bool = False
    broker_effect: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "steal": "S15",
            "label": "COST_OF_ERROR",
            "p": self.p,
            "stake": self.stake,
            "gate_id": self.gate_id,
            "subclass": self.subclass,
            "ticket": self.ticket,
            "cost_false_yes": self.cost_false_yes,
            "cost_false_no": self.cost_false_no,
            "cost_human": self.cost_human,
            "e_yes": self.e_yes,
            "e_no": self.e_no,
            "e_human": self.e_human,
            "chosen": self.chosen,
            "pick": self.chosen,
            "naive_vendor_choice": self.naive_vendor_choice,
            "vendor_0_85_forbidden_as_truth": True,
            "moved": self.moved,
            "conf_gate_band": self.conf_gate_band,
            "conf_floor": self.conf_floor,
            "conf_band_derived": self.conf_band_derived,
            "authority": self.authority,
            "reason": self.reason,
            "benefit_abs_R": self.benefit_abs_R,
            "g4_x_g6_overshrink": False,
            "keep_no_boost": self.keep_no_boost,
            "new_hard_off": False,
            "review_keep_offhours": self.review_keep_offhours,
            "review_keep": self.ticket == REVIEW_KEEP_TICKET or self.subclass == "full_size_loss",
            "label_only": True,
            "mode": "shadow_log_only",
            "never_place": True,
            "place_veto": self.place_veto,
            "news_protocol": "stamps_only_never_invent",
            "broker_effect": False,
            "tape": "historical_challenge_0",
            "tape_authority": tape_authority_facts(),
        }

    def conf_gate_overlay(self) -> dict[str, object]:
        """PR29 shadow stamps beside the existing CONF_GATE object."""

        out: dict[str, object] = {
            "vendor_0_85_forbidden_as_truth": True,
            "mode": "shadow_log_only",
            "never_place": True,
            "broker_effect": False,
            "new_hard_off": False,
            "g4_x_g6_overshrink": False,
        }
        if self.conf_gate_band:
            out["conf_gate_band"] = self.conf_gate_band
            out["conf_floor"] = self.conf_floor
        return out


def log_cost_of_error(
    p: float | None,
    *,
    stake: str,
    ticket: str | int | None = None,
    subclass: str | None = None,
    gate_id: str | None = None,
    gold_state: Mapping[str, Any] | None = None,
    regime: Any | None = None,
    matrix: Mapping[str, Any] | None = None,
) -> CostOfErrorLog:
    """Attach tape costs + pick beside a fluid-gate row. Never sets broker_effect."""

    resolved_ticket = extract_ticket(gold_state, explicit=ticket)
    naive = naive_vendor_choice(p)
    chair = getattr(regime, "chair", None) if regime is not None else None
    keep_no_boost = bool(getattr(chair, "keep_no_boost", True)) if chair is not None else True

    if is_broker_or_payout_action(stake):
        return CostOfErrorLog(
            p=None if p is None else float(p),
            stake=stake,
            gate_id="ANY_PLACE",
            subclass="any_place",
            ticket=resolved_ticket,
            cost_false_yes=None,
            cost_false_no=None,
            cost_human=None,
            e_yes=None,
            e_no=None,
            e_human=None,
            chosen="VETO",
            naive_vendor_choice=naive,
            moved=False,
            conf_gate_band=None,
            conf_floor=None,
            conf_band_derived=None,
            authority="infinity_veto",
            reason="infinity_veto_place_path",
            benefit_abs_R=None,
            g4_x_g6_overshrink=False,
            keep_no_boost=keep_no_boost,
            label_only=True,
            place_veto=True,
            news_protocol="stamps_only_never_invent",
        )

    resolved_sub = classify_s15_subclass(
        stake=stake,
        ticket=resolved_ticket,
        subclass=subclass,
        gold_state=gold_state,
        regime=regime,
    )
    resolved_gate = gate_id or (TAPE_SUBCLASS_TO_GATE.get(resolved_sub) if resolved_sub else None)
    row = resolve_tape_cost_row(resolved_gate, matrix=matrix)
    band_pair = SHADOW_BAND_BY_SUBCLASS.get(resolved_sub or "")
    conf_band = band_pair[0] if band_pair else None
    conf_floor = band_pair[1] if band_pair else None
    offhours = _is_review_keep_offhours(resolved_sub, resolved_ticket)

    if row is None:
        return CostOfErrorLog(
            p=None if p is None else float(p),
            stake=stake,
            gate_id=resolved_gate,
            subclass=resolved_sub,
            ticket=resolved_ticket,
            cost_false_yes=None,
            cost_false_no=None,
            cost_human=None,
            e_yes=None,
            e_no=None,
            e_human=None,
            chosen=None,
            naive_vendor_choice=naive,
            moved=False,
            conf_gate_band=None,
            conf_floor=None,
            conf_band_derived=None,
            authority=None,
            reason="missing_cost_triple_stay_shadow",
            benefit_abs_R=None,
            g4_x_g6_overshrink=False,
            keep_no_boost=keep_no_boost,
            label_only=True,
            place_veto=False,
            news_protocol="stamps_only_never_invent",
            review_keep_offhours=offhours,
        )

    benefit = None
    try:
        if row.get("benefit_abs_R") is not None:
            benefit = float(row["benefit_abs_R"])
    except (TypeError, ValueError):
        benefit = None

    triple = _triple(row)
    if triple is None or p is None:
        reason = "benefit_not_gut_cost" if benefit is not None else (
            "review_not_hard_cost" if resolved_sub == "review_keep_offhours_false_structure"
            else "missing_cost_triple_stay_shadow"
        )
        if resolved_sub == "full_size_loss":
            # REVIEW band still stamps; no APPLY.
            pass
        else:
            conf_band, conf_floor = None, None
        return CostOfErrorLog(
            p=None if p is None else float(p),
            stake=stake,
            gate_id=resolved_gate,
            subclass=resolved_sub,
            ticket=resolved_ticket,
            cost_false_yes=None,
            cost_false_no=None,
            cost_human=None,
            e_yes=None,
            e_no=None,
            e_human=None,
            chosen=None,
            naive_vendor_choice=naive,
            moved=False,
            conf_gate_band=conf_band if resolved_sub == "full_size_loss" else None,
            conf_floor=conf_floor if resolved_sub == "full_size_loss" else None,
            conf_band_derived=conf_band if resolved_sub == "full_size_loss" else None,
            authority=str(row.get("authority") or "close_loop_tape"),
            reason=reason,
            benefit_abs_R=benefit,
            g4_x_g6_overshrink=False,
            keep_no_boost=keep_no_boost,
            label_only=True,
            place_veto=False,
            news_protocol="stamps_only_never_invent",
            review_keep_offhours=offhours,
        )

    yes, no, human = triple
    chosen, expectations = pick_cost_of_error(
        float(p), cost_false_yes=yes, cost_false_no=no, cost_human=human
    )
    moved = chosen in {"YES", "NO", "UNSURE"} and naive in {"YES", "NO", "UNSURE"} and chosen != naive
    return CostOfErrorLog(
        p=float(p),
        stake=stake,
        gate_id=resolved_gate,
        subclass=resolved_sub,
        ticket=resolved_ticket,
        cost_false_yes=yes,
        cost_false_no=no,
        cost_human=human,
        e_yes=expectations["e_yes"],
        e_no=expectations["e_no"],
        e_human=expectations["e_human"],
        chosen=chosen,
        naive_vendor_choice=naive,
        moved=moved,
        conf_gate_band=conf_band,
        conf_floor=conf_floor,
        conf_band_derived=conf_band,
        authority=str(row.get("authority") or "close_loop_tape"),
        reason="cost_argmin_shadow",
        benefit_abs_R=benefit,
        g4_x_g6_overshrink=False,
        keep_no_boost=keep_no_boost,
        label_only=True,
        place_veto=False,
        news_protocol="stamps_only_never_invent",
        review_keep_offhours=offhours,
    )


def merge_conf_gate_s15(conf: ConfGateLog, cost: CostOfErrorLog) -> dict[str, object]:
    """CONF_GATE dict + S15 shadow band stamps. APPLY never follows."""

    merged = conf.as_dict()
    merged.update(cost.conf_gate_overlay())
    return merged

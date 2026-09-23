"""Jev-everywhere shadow fan-out on the existing ``jev_fluid_gate_v1`` sidecar.

One System One question pack over one state. Code consumes branches.
Labels only. Never place / remint / flatten / order_send / invent NEWS.

Enabled when ``GTOS_JEV_FLUID_GATES_SHADOW`` *or* ``GTOS_JEV_EVERYWHERE_SHADOW``
is on (or ``force``). This is sidecar fan-out, not a parallel place path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .cf_d import (
    ABLATION_ORDER,
    CHOICE_IDS,
    compose_cf_d,
)
from .cf_priority import (
    COST_BAND_LABELS,
    SIZE_X_CONF_POLICIES,
    SLEEVE_FAMILIES,
    label_cf_priority,
)
from .chair_enforce import hard_off_reason, is_keep_family
from .challenge import CHALLENGE_HARD_OFF_FAMILIES, CHALLENGE_KEEP_FAMILIES
from .conf_gate import ConfGateLog, CostOfErrorLog
from .inventory import LiveInventory
from .regime_compose import RegimeComposeResult
from .complete_judge import (
    COMPLETE_JUDGE_QUESTION_IDS,
    COMPLETE_JUDGE_QUESTION_PACK,
    compose_complete_judge,
    g4_applies_from_state,
)
from .sites import (
    COMPLETE_JUDGE_SITES,
    PRE_EVERYWHERE_SITES,
    DecisionSite,
    complete_judge_sites,
    pre_everywhere_gaps,
    safe_challenge_sites,
)
from .veto import (
    assert_answers_have_no_place_path,
    is_broker_or_payout_action,
    refuse_invented_news_protocol,
    refuse_raw_tick_dump_to_jev,
)

STEAL = "JEV_EVERYWHERE"
SCHEMA = "gtos.judgment.everywhere.v1"

ADMIT_CRITERIA = {
    "admit": "Surface law allows this candidate to stay on the slate as a label.",
    "abstain": "Not enough state or confidence; keep SHADOW; do not refuse the family.",
    "hard_refuse": "Writer / house law already refuses (bleed / orb_crypto / idxrev / xa_huge / mx_us30 / US30). Log only. INDEX/CRYPTO/xa size0 is revoked religion, not this verb.",
}

EXIT_CLASS_CRITERIA = {
    "tp": "Broker / packet facts look like a target fill.",
    "orig_stop": "Original stop or SL-like close.",
    "time_stop": "Horizon / session / time-stop close.",
    "manual_other": "Manual, other, or not classifiable from broker facts.",
}

ACTION_SCOPE_CRITERIA = {
    "audit_only": "Draft a corr-HOLD audit card. Do not block anything.",
    "block_sibling_prefills": "Draft a HOLD that blocks sibling prefills only.",
}

USAGE_SEAT_CRITERIA = {
    "cheap_label": "Local rules or Jev-only classify is enough.",
    "chair_read": "Chair prose / ENFORCE card needed.",
    "browser_scout": "Browser / web-fetch budget (still never place).",
    "deep_reason": "Expensive LLM / multi-agent.",
    "defer": "Wait, batch, or kill the spend.",
}

QUEUE_LANE_CRITERIA = {
    "research": "Queue a research note. No broker.",
    "write": "Queue a file / label write. No broker.",
    "review": "Queue Chair review. No broker.",
    "none": "No queue handoff this cycle.",
}

COMPLETION_CRITERIA = {
    "DONE": "Model believes the side-effect finished. Advisory only.",
    "CONTINUE": "Model believes work remains.",
    "BLOCKED": "Model believes the path is blocked.",
}

SIZE_LABEL_LEVELS = (
    "none — stand down; size_factor label 0.0; never place",
    "half — half-size label; never APPLY size_tilt",
    "full — full-size label at G7 no-boost ceiling; never boost",
)

GEOMETRY_LEVELS = (
    "Poor — stop too tight or TP unreachable vs tape",
    "Acceptable — house default with known fast-stop risk",
    "Good — stop width and TP fit current volatility",
)

LESSON_LEVELS = (
    "Noise — ignore for policy",
    "Useful single sample — study only",
    "Strong signal — consider sleeve pressure or HOLD timing repair",
)

HOLD_STRENGTH_LEVELS = (
    "Weak — n low or mixed directions",
    "Moderate — cluster forming",
    "Strong — multi-symbol same-dir cluster >=3",
)

URGENCY_LEVELS = (
    "routine — no session or risk clock",
    "session_sensitive — named session or occupancy matters",
    "immediate_risk — risk flags or two-stop circuit pressure",
)

SLEEVE_FIT_LEVELS = (
    "unrelated — sleeve does not fit the bucketed state",
    "adjacent — family-adjacent only",
    "direct — sleeve matches the named family",
    "deep — sleeve is a keep-family or favored-regime fit",
)

#: Independent questions over one state. Toxic remint is close-only (asked
#: here as remint_toxic, never as a LIVE remint verb).
EVERYWHERE_QUESTION_PACK: dict[str, dict[str, Any]] = {
    "next_gate": {
        "type": "choice",
        "instructions": (
            "Given `inventory` and `identity`, which next gate should the sidecar "
            "log? Escape hatches HOLD / ABSTAIN / ESCALATE_CHAIR / BLOCKED are "
            "always legal. Never choose place, remint, flatten, or order_send."
        ),
        "criteria": {
            "HOLD": "Stay in current book state; no new fire and no APPLY.",
            "ABSTAIN": "Not enough state; book unchanged.",
            "ESCALATE_CHAIR": "Draft a Chair-visible card; Chair still writes.",
            "BLOCKED": "Writer / house law already refuses.",
            "LABEL": "Shadow LABEL draft eligible if prove + APPLY flag later.",
            "RESEARCH": "Queue research; never place.",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How time-sensitive is this Challenge decision from `sessions` and `occupancy`?",
        "criteria": list(URGENCY_LEVELS),
    },
    "evidence_enough": {
        "type": "noul",
        "instructions": "Is `completeness.state_sufficient_for_live` plus bucketed features enough to decide a label?",
    },
    "corr_hold": {
        "type": "noul",
        "instructions": (
            "Does `occupancy` show a multi-symbol same-sleeve cluster that should "
            "draft a corr HOLD (audit / block sibling prefills only — never flatten)?"
        ),
    },
    "sleeve_fit": {
        "type": "score",
        "instructions": "How well does `identity.sleeve` fit the bucketed regime / family?",
        "criteria": list(SLEEVE_FIT_LEVELS),
    },
    "admit": {
        "type": "choice",
        "instructions": (
            "Should this candidate stay on the Challenge slate as a label? "
            "Use `surface_law` (hard-off families, keep families, US30). "
            "Never place."
        ),
        "criteria": dict(ADMIT_CRITERIA),
    },
    "surface_ok": {
        "type": "noul",
        "instructions": "Is `identity.sleeve` / `identity.symbol` inside the live Challenge surface (not hard-off, not US30)?",
    },
    "toxic_family": {
        "type": "noul",
        "instructions": "Is `identity.sleeve` in a house-law refuse family (bleed / orb_crypto / idxrev / xa_huge / mx_us30)?",
    },
    "geometry_quality": {
        "type": "score",
        "instructions": "How well does `geometry` (ATR / compression) fit a 1R-class stop on this tape row?",
        "criteria": list(GEOMETRY_LEVELS),
    },
    "exit_class": {
        "type": "choice",
        "instructions": (
            "Classify the close from `close.exit_class_raw`, `close.close_reason_raw`, "
            "and `close.subclass`. Accept only as a label. Never remint or flatten."
        ),
        "criteria": dict(EXIT_CLASS_CRITERIA),
    },
    "remint_toxic": {
        "type": "noul",
        "instructions": (
            "Does this close look toxic enough that a remint would be unwise? "
            "Score only — remint_authority is score_only_never_remint."
        ),
    },
    "prefill_hold_would_help": {
        "type": "noul",
        "instructions": "Would a prefill HOLD (block sibling prefills, never flatten) have helped this close?",
    },
    "lesson": {
        "type": "score",
        "instructions": "How much should this close move sleeve pressure or HOLD timing research?",
        "criteria": list(LESSON_LEVELS),
    },
    "speak_hold": {
        "type": "noul",
        "instructions": "Should Chair see a corr-HOLD draft from `occupancy` / `cluster`?",
    },
    "hold_strength": {
        "type": "score",
        "instructions": "How strong is the same-dir cluster in `cluster` / `occupancy`?",
        "criteria": list(HOLD_STRENGTH_LEVELS),
    },
    "action_scope": {
        "type": "choice",
        "instructions": (
            "If a HOLD draft is spoken, what is the action scope? "
            "flatten is a broken schema and is not an option."
        ),
        "criteria": dict(ACTION_SCOPE_CRITERIA),
    },
    "usage_seat": {
        "type": "choice",
        "instructions": (
            "Which seat should spend next on this Challenge decision? "
            "Honor defer. Never route to place / broker / order_send."
        ),
        "criteria": dict(USAGE_SEAT_CRITERIA),
    },
    "size_label": {
        "type": "score",
        "instructions": (
            "What size *label* fits Chair G4/G6/G7 on this row? "
            "Never APPLY size_tilt. Never boost above 1.0. Never place."
        ),
        "criteria": list(SIZE_LABEL_LEVELS),
    },
    "event_stamped": {
        "type": "noul",
        "instructions": (
            "Does `news` contain a stamped event (source=stamped)? "
            "If `news.spine_empty` is true, answer near 0.5 (abstain). "
            "Do not invent NEWS_PROTOCOL or unstamped HIGH events."
        ),
    },
    "shortlist_needed": {
        "type": "noul",
        "instructions": "Does `inventory` exceed a safe Choice cap so a Score shortlist should run first?",
    },
    "completion_advisory": {
        "type": "choice",
        "instructions": "Advisory only: does the model believe the sidecar write finished? Code owns DONE.",
        "criteria": dict(COMPLETION_CRITERIA),
    },
    "queue_lane": {
        "type": "choice",
        "instructions": "Which local queue lane should receive a JSON handoff? none is legal. Never broker.",
        "criteria": dict(QUEUE_LANE_CRITERIA),
    },
    "state_sufficient": {
        "type": "noul",
        "instructions": "Is `completeness.state_sufficient_for_live` true given `completeness.missing_fields`?",
    },
    "sleeve_family": {
        "type": "choice",
        "instructions": (
            "Name the CF sleeve family from `identity.sleeve`. "
            "spring / vss / sub / expand are the Chair-allow set. "
            "Code classifies; do not invent a family."
        ),
        "criteria": {name: f"CF family {name}" for name in SLEEVE_FAMILIES},
    },
    "sleeve_allow": {
        "type": "choice",
        "instructions": (
            "SHADOW policy from Challenge CF +8.70R: allow spring/vss/sub/expand. "
            "Not a hard-off. Writer house locks stay. Never place."
        ),
        "criteria": {
            "allow": "Family is spring, vss, sub, or expand. SHADOW allow label.",
            "shadow": "Family is outside the CF allow set. Stay SHADOW.",
        },
    },
    "size_x_conf": {
        "type": "choice",
        "instructions": (
            "Compose size_cf × conf_shadow. Never APPLY. "
            "Never encode INDEX/CRYPTO/xa size0 — Chair revoked that religion."
        ),
        "criteria": {name: f"Compose {name}" for name in SIZE_X_CONF_POLICIES},
    },
    "cost_band": {
        "type": "choice",
        "instructions": "CF cost_band SHADOW label from tape subclass. Never APPLY.",
        "criteria": {name: f"SHADOW {name}" for name in COST_BAND_LABELS},
    },
    "cf_d_choice": {
        "type": "choice",
        "instructions": (
            "Chair CF D primary soft policy (+11.17R Challenge-60): "
            "stand_down false_structure when not KEEP; KEEP exempt. "
            "Code composes. Never INDEX/CRYPTO/xa size0 religion. Never place."
        ),
        "criteria": {
            "A_STAND_DOWN": "Stand down — do not admit. miss=false_structure and not KEEP.",
            "B_SIZE_HALF": "Admit but size ×0.5 (event / STRICT remainder).",
            "C_SIZE_TRIM": "Admit size ×0.75 (session-cut nonkeep loss).",
            "D_FULL": "Admit full size. Residual when no earlier axis fires.",
            "E_KEEP_CAP": "KEEP surface: full size, max_concurrent=1, no boost. Exempt from stand_down.",
        },
    },
    "cf_d_score": {
        "type": "score",
        "instructions": (
            "How willing should Jev be to admit / full-size this row under CF D? "
            "false_structure non-KEEP scores low; KEEP wins high; KEEP losses medium."
        ),
        "criteria": [
            "0 — stand down / refuse admit",
            "0.5 — half or trim",
            "1 — KEEP cap or full",
        ],
    },
    "cf_d_keep": {
        "type": "noul",
        "instructions": (
            "Is this a CF D KEEP signature (house spring/vss or family sub_mid)? "
            "Expand is allow, not KEEP. Do not change house CHALLENGE_KEEP_FAMILIES."
        ),
    },
}
EVERYWHERE_QUESTION_PACK.update(COMPLETE_JUDGE_QUESTION_PACK)

EVERYWHERE_QUESTION_IDS: tuple[str, ...] = tuple(EVERYWHERE_QUESTION_PACK.keys())

SITE_QUESTION_IDS: dict[str, tuple[str, ...]] = {
    "alive_menu": ("next_gate",),
    "conf_gate": (),
    "fanout_book": ("next_gate", "urgency", "evidence_enough", "corr_hold", "sleeve_fit"),
    "done_outside": ("completion_advisory",),
    "s14_regime": ("regime_type", "regime_change_likely", "strategy_viable"),
    "s15_cost": (),
    "sleeve_family": ("sleeve_family", "sleeve_allow"),
    "size_x_conf": ("size_x_conf",),
    "cost_band": ("cost_band",),
    "cf_d": ("cf_d_choice", "cf_d_score", "cf_d_keep"),
    "admit": ("admit", "surface_ok", "toxic_family", "geometry_quality"),
    "close_label": ("exit_class", "remint_toxic", "prefill_hold_would_help", "lesson"),
    "corr_hold": ("speak_hold", "hold_strength", "action_scope"),
    "usage_router": ("usage_seat",),
    "size_tilt": ("size_label",),
    "event_stamp": ("event_stamped",),
    "score_then_choice": ("shortlist_needed",),
    "queue_handoff": ("queue_lane",),
    "state_shape": ("state_sufficient",),
    "admit_residual": ("admit_residual",),
    "chair_soft_g4": ("chair_soft_g4",),
    "chair_soft_g6": ("chair_soft_g6",),
    "chair_soft_g8": ("chair_soft_g8",),
}

NAIVE_LABELS = {
    "alive_menu": "HOLD",
    "admit": "admit",
    "close_label": "manual_other",
    "corr_hold": "audit_only",
    "usage_router": "cheap_label",
    "size_tilt": "full",
    "event_stamp": "invent_or_assume",
    "queue_handoff": "none",
    "done_outside": "DONE",
    "score_then_choice": "no_shortlist",
    "state_shape": "sufficient",
    "sleeve_family": "other",
    "size_x_conf": "SIZE_X_CONF_SHADOW",
    "cost_band": "COST_FS",
    "cf_d": "D_FULL",
    "admit_residual": "unanswered",
    "chair_soft_g4": "NOT_APPLICABLE",
    "chair_soft_g6": "NOT_APPLICABLE",
    "chair_soft_g8": "allow",
}


@dataclass(frozen=True)
class SiteShadowRow:
    """One structured shadow row. ``broker_effect`` is always False."""

    site_id: str
    steal: str | None
    primitive: str | None
    question_ids: tuple[str, ...]
    answers: dict[str, Any]
    label: str | None
    decidable: bool
    moved: bool
    status: str
    reason: str
    broker_effect: bool = False
    never_place: bool = True
    safe: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "site_id": self.site_id,
            "steal": self.steal,
            "primitive": self.primitive,
            "question_ids": list(self.question_ids),
            "answers": dict(self.answers),
            "label": self.label,
            "decidable": self.decidable,
            "moved": self.moved,
            "status": self.status,
            "reason": self.reason,
            "broker_effect": False,
            "never_place": True,
            "safe": self.safe,
        }


@dataclass
class EverywhereCompose:
    """Fan-out result attached to ``jev_fluid_gate_v1``."""

    schema: str
    steal: str
    sites: tuple[SiteShadowRow, ...]
    question_ids: tuple[str, ...]
    gaps_closed: tuple[str, ...]
    gaps_pre: tuple[str, ...]
    veto_sites: tuple[str, ...]
    new_hard_off: bool
    broker_effect: bool
    never_place: bool
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "steal": self.steal,
            "mode": "shadow_log_only",
            "sidecar": "jev_fluid_gate_v1",
            "same_admit_sidecar_not_parallel": True,
            "sites": [row.as_dict() for row in self.sites],
            "question_ids": list(self.question_ids),
            "gaps_closed": list(self.gaps_closed),
            "gaps_pre": list(self.gaps_pre),
            "veto_sites": list(self.veto_sites),
            "new_hard_off": False,
            "broker_effect": False,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
            "news_protocol": "stamps_only_never_invent",
            "religion_index_crypto_xa_size0": False,
            "religion_index_crypto_xa_size0_revoked": True,
            "regime_unknown": "honest_until_features",
            "notes": list(self.notes),
        }


def _payload(answers: Mapping[str, Any] | None, key: str) -> Mapping[str, Any] | None:
    if not answers:
        return None
    raw = answers.get(key)
    return raw if isinstance(raw, Mapping) else None


def _choice(answers: Mapping[str, Any] | None, key: str) -> tuple[str | None, float | None]:
    payload = _payload(answers, key)
    if payload is None:
        return None, None
    choice = payload.get("choice")
    conf = payload.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        conf_f = None
    return (str(choice) if choice is not None else None), conf_f


def _noul(answers: Mapping[str, Any] | None, key: str) -> float | None:
    payload = _payload(answers, key)
    if payload is None:
        return None
    try:
        return float(payload["noul"])
    except (KeyError, TypeError, ValueError):
        return None


def _score(answers: Mapping[str, Any] | None, key: str) -> tuple[float | None, float | None]:
    payload = _payload(answers, key)
    if payload is None:
        return None, None
    try:
        score = float(payload["score"]) if "score" in payload else None
    except (TypeError, ValueError):
        score = None
    try:
        conf = float(payload["confidence"]) if "confidence" in payload else None
    except (TypeError, ValueError):
        conf = None
    return score, conf


def _site_answers(answers: Mapping[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not answers:
        return out
    for key in keys:
        payload = answers.get(key)
        if isinstance(payload, Mapping):
            out[key] = dict(payload)
    return out


def _identity(gold: Mapping[str, Any] | None) -> dict[str, Any]:
    if not gold:
        return {}
    ident = gold.get("identity")
    return dict(ident) if isinstance(ident, Mapping) else {}


def _news(gold: Mapping[str, Any] | None) -> dict[str, Any]:
    if not gold:
        return {}
    news = gold.get("news")
    return dict(news) if isinstance(news, Mapping) else {}


def _row(
    spec: DecisionSite,
    *,
    answers: Mapping[str, Any] | None,
    label: str | None,
    decidable: bool,
    moved: bool,
    status: str,
    reason: str,
    extra_answers: Mapping[str, Any] | None = None,
) -> SiteShadowRow:
    qids = SITE_QUESTION_IDS.get(spec.site_id, spec.question_ids)
    merged = _site_answers(answers, qids)
    if extra_answers:
        merged.update(dict(extra_answers))
    return SiteShadowRow(
        site_id=spec.site_id,
        steal=spec.steal,
        primitive=spec.primitive,
        question_ids=qids,
        answers=merged,
        label=label,
        decidable=decidable,
        moved=moved,
        status=status,
        reason=reason,
        safe=spec.safe,
    )


def _spec(site_id: str) -> DecisionSite:
    for site in (*PRE_EVERYWHERE_SITES, *COMPLETE_JUDGE_SITES):
        if site.site_id == site_id:
            return site
    return DecisionSite(site_id, None, None, (), "gap", True, False, False, "")


def compose_everywhere(
    *,
    inventory: LiveInventory,
    answers: Mapping[str, Any] | None,
    gold_state: Mapping[str, Any] | None = None,
    close_state: Mapping[str, Any] | None = None,
    conf: ConfGateLog | None = None,
    cost: CostOfErrorLog | None = None,
    regime: RegimeComposeResult | None = None,
    stake: str = "sleeve_admit",
    jev_done_choice: str | None = None,
    invented_files: tuple[str, ...] = (),
) -> EverywhereCompose:
    """Build per-site shadow rows. Never sets broker_effect True."""

    refuse_invented_news_protocol(invented_files)
    assert_answers_have_no_place_path(dict(answers) if answers else None)
    if gold_state is not None:
        refuse_raw_tick_dump_to_jev(gold_state)
    if close_state is not None:
        refuse_raw_tick_dump_to_jev(close_state)

    notes = [
        "chair_compose_jev_everywhere_sidecar_fanout",
        "same_admit_sidecar_not_parallel",
        "no_new_hard_off",
        "writer_house_locks_untouched",
        "panic_hard_off_not_research_religion",
        "chair_cf_sleeve_family_first",
        "chair_cf_size_x_conf_compose",
        "chair_cf_cost_band_conf_gate_shadow",
        "chair_cf_d_primary_soft_policy",
        "chair_cf_d_stand_down_fs_when_not_keep",
        "chair_cf_d_keep_exempt",
        "chair_cf_d_ablation_miss_size_family_session_conf",
        "religion_index_crypto_xa_size0_revoked",
        "regime_unknown_honest_until_features",
        "place_infinity_veto",
        "news_protocol_stamps_only_never_invent",
        "complete_judge_shadow_labels_never_apply_fire_rate",
        "complete_judge_size_ceiling_stays_static",
    ]
    ident = _identity(gold_state)
    sleeve = ident.get("sleeve")
    symbol = ident.get("symbol")
    news = _news(gold_state)
    spine_empty = bool(news.get("spine_empty", True))
    events = news.get("events") if isinstance(news.get("events"), list) else []
    s15_band = None if cost is None else cost.conf_gate_band
    cf = label_cf_priority(
        gold_state=gold_state,
        sleeve=str(sleeve) if sleeve else None,
        s15_band=str(s15_band) if s15_band else None,
    )
    cfd = compose_cf_d(
        gold_state=gold_state,
        sleeve=str(sleeve) if sleeve else None,
        s15_band=str(s15_band) if s15_band else None,
    )

    rows: list[SiteShadowRow] = []

    next_gate, next_conf = _choice(answers, "next_gate")
    if next_gate and is_broker_or_payout_action(next_gate):
        next_gate, next_conf = None, None
    rows.append(
        _row(
            _spec("alive_menu"),
            answers=answers,
            label=next_gate or "HOLD",
            decidable=next_gate is not None,
            moved=bool(next_gate and next_gate != NAIVE_LABELS["alive_menu"]),
            status="shadow_logged",
            reason="alive_menu_next_gate" if next_gate else "default_hold",
        )
    )

    conf_label = cf.conf_shadow
    rows.append(
        _row(
            _spec("conf_gate"),
            answers=answers,
            label=conf_label,
            decidable=conf_label is not None or conf is not None,
            moved=bool(conf_label and conf_label != "CONF_GATE_STRICT"),
            status="shadow_logged" if (conf_label is not None or conf is not None) else "unanswered",
            reason="conf_gate_shadow_label_never_apply" if conf_label else "code_band_not_shadow",
            extra_answers={
                "conf_gate": None if conf is None else conf.as_dict(),
                "conf_gate_shadow": cf.conf_shadow,
                "code_band": None if conf is None else conf.band,
            },
        )
    )

    urgency, _ = _score(answers, "urgency")
    evidence = _noul(answers, "evidence_enough")
    fanout_decidable = any(v is not None for v in (next_gate, urgency, evidence))
    rows.append(
        _row(
            _spec("fanout_book"),
            answers=answers,
            label="fanout",
            decidable=fanout_decidable,
            moved=fanout_decidable,
            status="shadow_logged",
            reason="independent_questions_one_state",
        )
    )

    done_choice, _ = _choice(answers, "completion_advisory")
    advisory = done_choice or jev_done_choice
    rows.append(
        _row(
            _spec("done_outside"),
            answers=answers,
            label=advisory or "CONTINUE",
            decidable=True,
            moved=str(advisory or "").upper() in {"DONE", "COMPLETE"},
            status="shadow_logged",
            reason="jev_done_advisory_code_owns_truth",
        )
    )

    regime_honest = cf.regime_honest
    if regime_honest == "regime_unknown":
        regime_label, regime_dec, regime_reason = (
            "regime_unknown",
            True,
            "regime_features_unassembled_honest",
        )
        regime_moved = False
        regime_status = "shadow_logged"
    else:
        regime_label = None if regime is None else regime.gate_decision
        regime_dec = bool(regime and regime.decidable)
        regime_moved = bool(regime and regime.gate_decision in {"stand_down", "half_size"})
        regime_status = "shadow_logged" if regime is not None else "unanswered"
        regime_reason = "s14_same_sidecar" if regime is not None else "no_gold_state"
    rows.append(
        _row(
            _spec("s14_regime"),
            answers=answers,
            label=regime_label,
            decidable=regime_dec,
            moved=regime_moved,
            status=regime_status,
            reason=regime_reason,
            extra_answers={"regime_honest": regime_honest},
        )
    )

    cost_label = None if cost is None else cost.chosen
    rows.append(
        _row(
            _spec("s15_cost"),
            answers=answers,
            label=cost_label,
            decidable=bool(cost and cost.chosen in {"YES", "NO", "UNSURE"}),
            moved=bool(cost and cost.moved),
            status="shadow_logged",
            reason="s15_code_pick_tape_authority",
        )
    )

    family_choice, _ = _choice(answers, "sleeve_family")
    family_label = family_choice if family_choice in SLEEVE_FAMILIES else cf.family
    allow_choice, _ = _choice(answers, "sleeve_allow")
    if allow_choice == "allow":
        sleeve_policy = "SLEEVE_ALLOW"
    elif allow_choice == "shadow":
        sleeve_policy = "SLEEVE_SHADOW"
    else:
        sleeve_policy = cf.sleeve_policy
    rows.append(
        _row(
            _spec("sleeve_family"),
            answers=answers,
            label=f"{family_label}:{sleeve_policy}",
            decidable=True,
            moved=sleeve_policy == "SLEEVE_ALLOW",
            status="shadow_logged",
            reason="chair_cf_sleeve_allow_spring_vss_sub_expand",
            extra_answers={
                "cf_priority": cf.as_dict(),
                "sleeve_family_code": family_label,
                "sleeve_policy": sleeve_policy,
            },
        )
    )

    compose_choice, _ = _choice(answers, "size_x_conf")
    compose_label = compose_choice if compose_choice in SIZE_X_CONF_POLICIES else cf.size_x_conf
    rows.append(
        _row(
            _spec("size_x_conf"),
            answers=answers,
            label=compose_label,
            decidable=True,
            moved=compose_label not in {"SIZE_X_CONF_SHADOW", "SIZE_X_CONF_STRICT"},
            status="shadow_logged",
            reason="chair_cf_size_x_conf_never_religion_size0",
            extra_answers={
                "size_cf": cf.size_cf,
                "conf_shadow": cf.conf_shadow,
                "size_x_conf_join": cf.size_x_conf_join,
                "religion_index_crypto_xa_size0": False,
            },
        )
    )

    cost_choice, _ = _choice(answers, "cost_band")
    cost_band_label = cost_choice if cost_choice in COST_BAND_LABELS else cf.cost_band
    rows.append(
        _row(
            _spec("cost_band"),
            answers=answers,
            label=cost_band_label,
            decidable=cost_band_label is not None,
            moved=bool(cost_band_label and cost_band_label != NAIVE_LABELS["cost_band"]),
            status="shadow_logged" if cost_band_label is not None else "unanswered",
            reason="chair_cf_cost_band_shadow" if cost_band_label else "no_cost_band_fact",
            extra_answers={"conf_gate_shadow": cf.conf_shadow},
        )
    )

    cfd_choice, _ = _choice(answers, "cf_d_choice")
    # Code owns CF D. Injected Choice is logged, never overrides Chair compose.
    cfd_label = cfd.choice if cfd.choice in CHOICE_IDS else (cfd_choice if cfd_choice in CHOICE_IDS else "D_FULL")
    if cfd.keep:
        notes.append("cf_d_keep_exempt")
    if cfd.choice == "A_STAND_DOWN":
        notes.append("cf_d_stand_down_false_structure")
    rows.append(
        _row(
            _spec("cf_d"),
            answers=answers,
            label=cfd_label,
            decidable=True,
            moved=cfd_label != NAIVE_LABELS["cf_d"],
            status="shadow_logged",
            reason=f"chair_cf_d_decided_by_{cfd.decided_by}",
            extra_answers={
                "cf_d": cfd.as_dict(),
                "injected_cf_d_choice": cfd_choice,
                "religion_index_crypto_xa_size0": False,
                "ablation_order": list(ABLATION_ORDER),
            },
        )
    )

    admit_choice, admit_conf = _choice(answers, "admit")
    hard = hard_off_reason(sleeve=str(sleeve) if sleeve else None, symbol=str(symbol) if symbol else None)
    judge_sites = compose_complete_judge(
        gold_state,
        g4_applies=g4_applies_from_state(gold_state),
        admit_choice=admit_choice,
        admit_conf=admit_conf,
        answers=answers,
    )
    judge_by_id = {row.site_id: row for row in judge_sites}
    residual = None if judge_by_id.get("admit_residual") is None else judge_by_id["admit_residual"].label
    if hard:
        admit_label = "hard_refuse"
        admit_reason = residual or "envelope_hard_off"
        admit_dec = True
    elif residual == "conf_floor":
        admit_label = "abstain"
        admit_reason = "conf_floor"
        admit_dec = True
    elif admit_choice in ADMIT_CRITERIA:
        admit_label = admit_choice
        admit_reason = residual or "injected"
        admit_dec = True
    else:
        admit_label = None
        admit_reason = residual or "unanswered"
        admit_dec = False
    rows.append(
        _row(
            _spec("admit"),
            answers=answers,
            label=admit_label,
            decidable=admit_dec,
            moved=bool(admit_dec and admit_label != NAIVE_LABELS["admit"]),
            status="shadow_logged" if admit_dec else "unanswered",
            reason=admit_reason,
            extra_answers={"admit_residual": residual},
        )
    )

    exit_choice, exit_conf = _choice(answers, "exit_class")
    close_present = close_state is not None or bool((gold_state or {}).get("close"))
    if not close_present:
        close_label, close_dec, close_reason = None, False, "no_close_state"
    elif exit_choice in EXIT_CLASS_CRITERIA and (exit_conf is None or exit_conf >= 0.8):
        close_label, close_dec, close_reason = exit_choice, True, "accept_exit_class"
    elif exit_choice in EXIT_CLASS_CRITERIA:
        close_label, close_dec, close_reason = None, False, "chair_label_from_broker_facts_only"
    else:
        close_label, close_dec, close_reason = None, False, "exit_class_unanswered"
    remint_noul = _noul(answers, "remint_toxic")
    if remint_noul is not None and remint_noul >= 0.99 and close_label == "tp":
        notes.append("remint_toxic_score_only_never_remint")
    rows.append(
        _row(
            _spec("close_label"),
            answers=answers,
            label=close_label,
            decidable=close_dec,
            moved=bool(close_dec and close_label != NAIVE_LABELS["close_label"]),
            status="shadow_logged" if close_dec else "unanswered",
            reason=close_reason,
        )
    )

    speak = _noul(answers, "speak_hold")
    hold_s, _ = _score(answers, "hold_strength")
    scope, _ = _choice(answers, "action_scope")
    if scope == "flatten" or (scope and is_broker_or_payout_action(scope)):
        corr_label, corr_dec, corr_reason = "broken_schema_refuse", False, "flatten_forbidden"
    elif speak is not None and hold_s is not None and scope in ACTION_SCOPE_CRITERIA:
        if speak >= 0.6 and hold_s >= 1.5:
            corr_label = f"draft_hold_{scope}"
            corr_dec, corr_reason = True, "speak_hold_and_strength"
        else:
            corr_label, corr_dec, corr_reason = "log_only", True, "below_hold_floors"
    elif scope in ACTION_SCOPE_CRITERIA:
        corr_label, corr_dec, corr_reason = scope, True, "action_scope_only"
    else:
        corr_label, corr_dec, corr_reason = None, False, "corr_hold_unanswered"
    rows.append(
        _row(
            _spec("corr_hold"),
            answers=answers,
            label=corr_label,
            decidable=corr_dec,
            moved=bool(corr_dec and corr_label not in {NAIVE_LABELS["corr_hold"], "log_only"}),
            status="shadow_logged" if corr_dec else "unanswered",
            reason=corr_reason,
        )
    )

    usage, _ = _choice(answers, "usage_seat")
    if usage and is_broker_or_payout_action(usage):
        usage, usage_reason = None, "veto_place_path"
        usage_dec = False
    elif usage in USAGE_SEAT_CRITERIA:
        usage_reason, usage_dec = "usage_router", True
    else:
        usage_reason, usage_dec = "usage_unanswered", False
    rows.append(
        _row(
            _spec("usage_router"),
            answers=answers,
            label=usage,
            decidable=usage_dec,
            moved=bool(usage_dec and usage != NAIVE_LABELS["usage_router"]),
            status="shadow_logged" if usage_dec else "unanswered",
            reason=usage_reason,
        )
    )

    size_s, _ = _score(answers, "size_label")
    if size_s is None and regime is not None and regime.size_factor is not None:
        size_label = {0.0: "none", 0.5: "half", 1.0: "full"}.get(float(regime.size_factor))
        size_dec = size_label is not None
        size_reason = "s14_size_factor_label"
    elif size_s is None:
        size_label, size_dec, size_reason = None, False, "size_label_unanswered"
    else:
        if size_s < 0.5:
            size_label = "none"
        elif size_s < 1.5:
            size_label = "half"
        else:
            size_label = "full"
        size_dec, size_reason = True, "size_tilt_label_never_apply"
    rows.append(
        _row(
            _spec("size_tilt"),
            answers=answers,
            label=size_label,
            decidable=size_dec,
            moved=bool(size_dec and size_label != NAIVE_LABELS["size_tilt"]),
            status="shadow_logged" if size_dec else "unanswered",
            reason=size_reason,
        )
    )

    stamped = _noul(answers, "event_stamped")
    if spine_empty and events:
        event_label, event_dec, event_reason = "invented_high_veto", False, "spine_empty_with_events"
    elif spine_empty:
        event_label, event_dec, event_reason = "abstain_empty_spine", True, "never_invent_news_protocol"
    elif stamped is not None:
        event_label = "stamped" if stamped >= 0.6 else "not_stamped"
        event_dec, event_reason = True, "stamped_event_noul"
    else:
        event_label, event_dec, event_reason = "abstain_empty_spine" if spine_empty else None, spine_empty, (
            "never_invent_news_protocol" if spine_empty else "event_unanswered"
        )
    rows.append(
        _row(
            _spec("event_stamp"),
            answers=answers,
            label=event_label,
            decidable=event_dec,
            moved=bool(event_dec and event_label != NAIVE_LABELS["event_stamp"]),
            status="shadow_logged" if event_dec else "unanswered",
            reason=event_reason,
        )
    )

    short = _noul(answers, "shortlist_needed")
    n_opts = len(inventory.option_names())
    if short is None:
        short_label = "shortlist" if n_opts > 200 else "no_shortlist"
        short_dec, short_reason = True, "inventory_cardinality"
    else:
        short_label = "shortlist" if short >= 0.6 else "no_shortlist"
        short_dec, short_reason = True, "shortlist_noul"
    rows.append(
        _row(
            _spec("score_then_choice"),
            answers=answers,
            label=short_label,
            decidable=short_dec,
            moved=short_label == "shortlist",
            status="shadow_logged",
            reason=short_reason,
        )
    )

    lane, _ = _choice(answers, "queue_lane")
    if lane in QUEUE_LANE_CRITERIA:
        lane_dec, lane_reason = True, "queue_handoff"
    else:
        lane, lane_dec, lane_reason = "none", True, "default_none"
    rows.append(
        _row(
            _spec("queue_handoff"),
            answers=answers,
            label=lane,
            decidable=lane_dec,
            moved=lane != NAIVE_LABELS["queue_handoff"],
            status="shadow_logged",
            reason=lane_reason,
        )
    )

    suff = _noul(answers, "state_sufficient")
    completeness = (gold_state or {}).get("completeness") if gold_state else None
    code_suff = None
    if isinstance(completeness, Mapping):
        code_suff = completeness.get("state_sufficient_for_live")
    if suff is None and code_suff is None:
        state_label, state_dec, state_reason = None, False, "state_unanswered"
    else:
        yes = (suff is not None and suff >= 0.6) or (suff is None and bool(code_suff))
        state_label = "sufficient" if yes else "insufficient"
        state_dec, state_reason = True, "state_shape"
    rows.append(
        _row(
            _spec("state_shape"),
            answers=answers,
            label=state_label,
            decidable=state_dec,
            moved=bool(state_dec and state_label != NAIVE_LABELS["state_shape"]),
            status="shadow_logged" if state_dec else "unanswered",
            reason=state_reason,
        )
    )

    for judge in judge_sites:
        rows.append(
            _row(
                _spec(judge.site_id),
                answers=answers,
                label=judge.label,
                decidable=judge.decidable,
                moved=bool(judge.decidable and judge.label != NAIVE_LABELS.get(judge.site_id)),
                status="shadow_logged" if judge.decidable else "unanswered",
                reason=judge.reason,
            )
        )

    if is_broker_or_payout_action(stake):
        notes.append("stake_place_path_veto_logged")

    keep = is_keep_family(str(sleeve) if sleeve else None)
    if keep:
        notes.append("keep_family_not_hard_off")

    gaps_pre = tuple(s.site_id for s in pre_everywhere_gaps())
    return EverywhereCompose(
        schema=SCHEMA,
        steal=STEAL,
        sites=tuple(rows),
        question_ids=EVERYWHERE_QUESTION_IDS,
        gaps_closed=gaps_pre,
        gaps_pre=gaps_pre,
        veto_sites=("place", "remint", "flatten", "order_send", "news_protocol"),
        new_hard_off=False,
        broker_effect=False,
        never_place=True,
        notes=notes,
    )


def surface_map() -> dict[str, object]:
    """Owner-facing inventory: pre-everywhere gaps vs post-everywhere sit."""

    return {
        "schema": "gtos.judgment.everywhere.surface_map.v1",
        "login": "0",
        "sidecar": "jev_fluid_gate_v1",
        "hypothesis": "extend_jev_fluid_gate_v1_sidecar_fanout_not_parallel_place_path",
        "keep_families": list(CHALLENGE_KEEP_FAMILIES),
        "hard_off_families_untouched": list(CHALLENGE_HARD_OFF_FAMILIES),
        "new_hard_off": False,
        "safe_sites": [s.as_dict() for s in safe_challenge_sites()],
        "gaps_pre": [s.as_dict() for s in pre_everywhere_gaps()],
        "veto_sites": [
            s.as_dict()
            for s in PRE_EVERYWHERE_SITES
            if s.status == "veto"
        ],
        "question_ids": list(EVERYWHERE_QUESTION_IDS),
        "complete_judge": [s.as_dict() for s in complete_judge_sites()],
        "complete_judge_question_ids": list(COMPLETE_JUDGE_QUESTION_IDS),
        "s16": "observe_only_parallel_flags",
        "never_place": True,
        "chair_cf": {
            "primary_soft_policy": {
                "id": "CF_D",
                "sum_r": 11.1678,
                "n": 60,
                "login": "0",
                "rule": "stand_down false_structure when not KEEP; KEEP exempt",
                "ablation": list(ABLATION_ORDER),
                "keep_signature": ["spring", "vss_fxcross", "sub_mid"],
                "house_keep_families_untouched": list(CHALLENGE_KEEP_FAMILIES),
                "religion": False,
            },
            "priority": [
                "cf_d",
                "sleeve_family",
                "size_x_conf",
                "cost_band",
                "conf_gate_shadow",
            ],
            "best_cf": {
                "policy": "jev_cf_d_stand_down_fs_not_keep",
                "sum_r": 11.1678,
                "n": 60,
                "login": "0",
            },
            "sleeve_allow_cf": {
                "policy": "jev_sleeve_allow_spring_vss_sub_expand",
                "sum_r": 8.7013,
                "n": 60,
                "login": "0",
            },
            "religion_index_crypto_xa_size0": "revoked",
            "regime_unknown": "honest_until_features",
        },
    }


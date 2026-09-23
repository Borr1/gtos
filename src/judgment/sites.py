"""Decision-site inventory for Challenge fluid-gate / Jev coverage.

This is the surface map: every judgment or fluid-gate decision site, whether
a System One question already sits on it, and whether the site is safe
(never ``order_send`` / place / remint / flatten from Jev).

Gaps are safe sites with no Jev question *or* no structured shadow row.
Unsafe sites stay vetoed — they are listed so the map is complete, not so
Jev can sit on them.

Panic hard-offs are **not** code religion for research paths. This module
does not add new hard-off families. Writer house locks stay in
``challenge.CHALLENGE_HARD_OFF_FAMILIES`` / Chair G1–G8.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SiteStatus = Literal[
    "wired",
    "ids_only",
    "schema_only",
    "gap",
    "observe_only",
    "veto",
]
Primitive = Literal["choice", "score", "noul", "mixed", "code", None]


@dataclass(frozen=True)
class DecisionSite:
    """One decision site on the Challenge / Dig surface."""

    site_id: str
    steal: str | None
    primitive: Primitive
    question_ids: tuple[str, ...]
    status: SiteStatus
    safe: bool
    jev_sits: bool
    shadow_row: bool
    notes: str
    never_place: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "site_id": self.site_id,
            "steal": self.steal,
            "primitive": self.primitive,
            "question_ids": list(self.question_ids),
            "status": self.status,
            "safe": self.safe,
            "jev_sits": self.jev_sits,
            "shadow_row": self.shadow_row,
            "notes": self.notes,
            "never_place": self.never_place,
        }


#: Pre-everywhere snapshot (S14/S15/S16 + PR29). Used to name gaps.
PRE_EVERYWHERE_SITES: tuple[DecisionSite, ...] = (
    DecisionSite(
        "alive_menu",
        "S1",
        "choice",
        ("next_gate",),
        "wired",
        True,
        True,
        True,
        "Choice criteria rebuilt each cycle; next_gate is a fan-out ID.",
    ),
    DecisionSite(
        "conf_gate",
        "S2",
        "code",
        (),
        "wired",
        True,
        False,
        True,
        "Code bands LOW/MED/HIGH. Confidence is not a Jev question.",
    ),
    DecisionSite(
        "fanout_book",
        "S3",
        "mixed",
        ("next_gate", "urgency", "evidence_enough", "corr_hold", "sleeve_fit"),
        "ids_only",
        True,
        False,
        False,
        "Question IDs listed on the sidecar; no typed pack or per-site row.",
    ),
    DecisionSite(
        "done_outside",
        "S4",
        "choice",
        ("completion_advisory",),
        "wired",
        True,
        False,
        True,
        "Code verify owns DONE. Jev DONE is advisory and was not logged as a site.",
    ),
    DecisionSite(
        "s14_regime",
        "S14",
        "mixed",
        ("regime_type", "regime_change_likely", "strategy_viable"),
        "wired",
        True,
        True,
        True,
        "Same admit sidecar. Labels only.",
    ),
    DecisionSite(
        "s15_cost",
        "S15",
        "code",
        (),
        "wired",
        True,
        False,
        True,
        "Tape-authority YES/NO/UNSURE pick is code, not a System One question.",
    ),
    DecisionSite(
        "sleeve_family",
        "CF1",
        "code",
        ("sleeve_family", "sleeve_allow"),
        "gap",
        True,
        False,
        False,
        "Chair CF #1 — spring/vss/sub/expand allow. Best +8.70R on Challenge 60. SHADOW only.",
    ),
    DecisionSite(
        "size_x_conf",
        "CF2",
        "code",
        ("size_x_conf",),
        "gap",
        True,
        False,
        False,
        "Chair CF #2 — size × conf_shadow compose. Never INDEX/CRYPTO/xa size0 religion.",
    ),
    DecisionSite(
        "cost_band",
        "CF3",
        "code",
        ("cost_band",),
        "gap",
        True,
        False,
        False,
        "Chair CF #3 — cost_band / conf_gate SHADOW labels. Never APPLY.",
    ),
    DecisionSite(
        "cf_d",
        "CFD",
        "mixed",
        ("cf_d_choice", "cf_d_score", "cf_d_keep"),
        "gap",
        True,
        False,
        False,
        "Chair CF D primary soft policy +11.17R: stand_down FS when not KEEP; KEEP exempt. SHADOW compose, not asset-zero religion.",
    ),
    DecisionSite(
        "admit",
        None,
        "mixed",
        ("admit", "surface_ok", "toxic_family", "geometry_quality"),
        "schema_only",
        True,
        False,
        False,
        "jev_admit_v1 schema exists; cycle never asked or logged it.",
    ),
    DecisionSite(
        "close_label",
        None,
        "mixed",
        ("exit_class", "remint_toxic", "prefill_hold_would_help", "lesson"),
        "schema_only",
        True,
        False,
        False,
        "jev_close_label_v1 schema exists; no close-site fan-out on the sidecar.",
    ),
    DecisionSite(
        "corr_hold",
        None,
        "mixed",
        ("speak_hold", "hold_strength", "action_scope"),
        "schema_only",
        True,
        False,
        False,
        "jev_corr_hold_v1 schema exists; fan-out only had a speculative Noul id.",
    ),
    DecisionSite(
        "usage_router",
        "S5",
        "choice",
        ("usage_seat",),
        "gap",
        True,
        False,
        False,
        "SCORE_STEALS S5 — no question, no log.",
    ),
    DecisionSite(
        "size_tilt",
        "S15",
        "score",
        ("size_label",),
        "gap",
        True,
        False,
        False,
        "S15 logs costs beside size_tilt; no Score label. APPLY stays vetoed.",
    ),
    DecisionSite(
        "event_stamp",
        None,
        "noul",
        ("event_stamped",),
        "gap",
        True,
        False,
        False,
        "Stamped-event Noul. Empty spine abstains. Never invent NEWS_PROTOCOL.",
    ),
    DecisionSite(
        "score_then_choice",
        "S7",
        "noul",
        ("shortlist_needed",),
        "gap",
        True,
        False,
        False,
        "High-cardinality shortlist flag. No question.",
    ),
    DecisionSite(
        "queue_handoff",
        "S8",
        "choice",
        ("queue_lane",),
        "gap",
        True,
        False,
        False,
        "Local queue lane. No question.",
    ),
    DecisionSite(
        "state_shape",
        "S6",
        "noul",
        ("state_sufficient",),
        "gap",
        True,
        False,
        False,
        "gold_state completeness is a field, not a Jev question.",
    ),
    DecisionSite(
        "s16_multi_stage",
        "S16",
        "mixed",
        (),
        "observe_only",
        True,
        True,
        True,
        "Dig/Chair harness. Parallel flags. Off Challenge place scoreboard.",
    ),
    DecisionSite(
        "place",
        None,
        None,
        (),
        "veto",
        False,
        False,
        False,
        "Infinity VETO. Jev never sits here.",
        True,
    ),
    DecisionSite(
        "remint",
        None,
        None,
        (),
        "veto",
        False,
        False,
        False,
        "Infinity VETO. remint_toxic is a close-label Noul only.",
        True,
    ),
    DecisionSite(
        "flatten",
        None,
        None,
        (),
        "veto",
        False,
        False,
        False,
        "Infinity VETO. corr HOLD action_scope omits flatten.",
        True,
    ),
    DecisionSite(
        "order_send",
        None,
        None,
        (),
        "veto",
        False,
        False,
        False,
        "Infinity VETO. Never imported from src/judgment.",
        True,
    ),
    DecisionSite(
        "news_protocol",
        None,
        None,
        (),
        "veto",
        False,
        False,
        False,
        "Never invent NEWS_PROTOCOL. Event Noul abstains on empty spine.",
        True,
    ),
)


#: Complete-judge residual sites. Not a 49th fluid. Not pre-everywhere history.
#: SHADOW labels over COMPLETE_STATE. Fire rate / size_ceiling stay STATIC.
COMPLETE_JUDGE_SITES: tuple[DecisionSite, ...] = (
    DecisionSite(
        "admit_residual",
        "CJ1",
        "choice",
        ("admit_residual",),
        "wired",
        True,
        True,
        True,
        "Typed residual for STATIC admit reasons. Envelope hard-off / insufficient / "
        "conf_floor / last_refusal / injected / unanswered. SHADOW. Never place.",
    ),
    DecisionSite(
        "chair_soft_g4",
        "CJ2",
        "choice",
        ("chair_soft_g4",),
        "wired",
        True,
        True,
        True,
        "Chair G4 soft Choice. Label only — size_ceiling stays STATIC until hist+APPLY.",
    ),
    DecisionSite(
        "chair_soft_g6",
        "CJ3",
        "choice",
        ("chair_soft_g6",),
        "wired",
        True,
        True,
        True,
        "Chair G6 soft Choice. Label only — size_ceiling stays STATIC until hist+APPLY.",
    ),
    DecisionSite(
        "chair_soft_g8",
        "CJ4",
        "noul",
        ("chair_soft_g8",),
        "wired",
        True,
        True,
        True,
        "Chair G8 Noul P(block same-sleeve reentry). Occupancy walls stay envelope integers.",
    ),
)


def complete_judge_sites() -> tuple[DecisionSite, ...]:
    return COMPLETE_JUDGE_SITES


def pre_everywhere_gaps() -> tuple[DecisionSite, ...]:
    """Safe sites that lacked a Jev question and/or a structured shadow row."""

    return tuple(
        site
        for site in PRE_EVERYWHERE_SITES
        if site.safe and site.status in {"gap", "ids_only", "schema_only"}
    )


def unsafe_veto_sites() -> tuple[DecisionSite, ...]:
    return tuple(site for site in PRE_EVERYWHERE_SITES if not site.safe or site.status == "veto")


def safe_challenge_sites() -> tuple[DecisionSite, ...]:
    """Challenge sidecar sites Jev may sit on (S16 stays observe-only)."""

    return tuple(
        site
        for site in PRE_EVERYWHERE_SITES
        if site.safe and site.status != "observe_only" and site.status != "veto"
    )

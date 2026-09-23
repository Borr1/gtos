"""DRAFT — Policy C ablated System One pack. NOT live-landed.

Menu ids are REAL: A_STAND_DOWN | C_SIZE_TRIM | D_FULL.
Do not invent B_SIZE_HALF. Do not ask EXPOST on live_intent.
place Choice is default-off (owner path OPEN after hist-prove).
Empty news spine is not 'no HIGH'. Never invent NEWS_PROTOCOL.
"""
from __future__ import annotations

from typing import Any

MODEL = "jev-1.13.0"

POLICY_C_CHOICE_CRITERIA = {
    "A_STAND_DOWN": (
        "Named COMPLETE_STATE is dark, fights named tape, or is not evaluable. "
        "Code may refuse admit when APPLY is on. Not a house hard-off (those are integers). "
        "Not a place/remint/flatten verb."
    ),
    "C_SIZE_TRIM": (
        "Named state is thin or mixed: enough to consider the fire, not enough for full size. "
        "Size haircut only. Cannot zero a fire. Cannot refuse house keep-families."
    ),
    "D_FULL": (
        "Named tape, geometry, session, and completeness support full admit. "
        "This is not 'will it profit' and not permission to place."
    ),
}

INCOMPLETE_SEVERITY_CRITERIA = [
    "Named COMPLETE_STATE is dark or majority PENDING/missing — stand or skip territory",
    "Thin but usable — several named blocks present; trim territory",
    "Named blocks present enough for full admit",
]


def _core_questions() -> dict[str, Any]:
    return {
        "policy_c_choice": {
            "type": "choice",
            "instructions": (
                "Given COMPLETE_STATE (identity, alive_sleeves, regime_tag, conf_band, "
                "session_fit, phi, cost, occupancy, account, hard_off_hit, news_join, "
                "full_state_dark, n_incomplete, place_context) — pick the Policy C admit menu. "
                "Use only named fields. PENDING is incomplete, not a guess. "
                "House hard-off / token / 2-stop COUNT / occupancy keep-one / writer clock "
                "are code, not this answer. Empty news spine is not 'no HIGH'. "
                "Do not use miss, year_le0, R, MFE, or other EXPOST keys."
            ),
            "criteria": dict(POLICY_C_CHOICE_CRITERIA),
        },
        "incomplete_severity": {
            "type": "score",
            "instructions": (
                "How complete is named COMPLETE_STATE for a pre-entry admit? "
                "Do not invent missing regime_tag, news, or ATR. "
                "full_state_dark and n_incomplete are named inputs, not targets to rubber-stamp."
            ),
            "criteria": list(INCOMPLETE_SEVERITY_CRITERIA),
        },
        "state_sufficient": {
            "type": "noul",
            "instructions": (
                "Do completeness.missing_fields and named COMPLETE_STATE blocks contain "
                "enough to judge this fire as-of clock.as_of_utc? "
                "Yes = named tape/geometry/identity present. No = a required block missing. "
                "Empty news spine is not 'no HIGH'."
            ),
            "criteria": {
                "true": "Named blocks are present enough to judge the fire",
                "false": "A required named block is missing or unknown",
            },
        },
        "session_fitness": {
            "type": "score",
            "instructions": (
                "Is this sleeve in a clean session hour? Use sessions.named, "
                "session_bucket, clock.is_friday. Dead window and Friday cutoff are 0. "
                "Do not replace the writer clock — score fitness only. Do not invent volume."
            ),
            "criteria": [
                "Dead window, Friday cutoff, or wrong hour for the sleeve",
                "Ordinary session",
                "Sleeve's clean hour",
            ],
        },
        "flow_alignment": {
            "type": "score",
            "instructions": (
                "How aligned is identity.side with named HTF/session flow? "
                "Use only named timeframe / sleeve_features / phi. Unassembled is mixed, not a refuse."
            ),
            "criteria": [
                "Fighting named HTF/session flow",
                "Mixed or rotating flow",
                "Aligned with named HTF/session flow",
            ],
        },
        "cost_hurtful": {
            "type": "noul",
            "instructions": (
                "Is cost.spread_r / total_cost_r large versus geometry.plan_r so this fire "
                "is cost-dominated? Size-tilt context only — never a new refuse."
            ),
            "criteria": {
                "true": "Spread/cost eats a material fraction of the stop",
                "false": "Cost is ordinary versus the named stop",
            },
        },
        "calendar_honest": {
            "type": "noul",
            "instructions": (
                "Is news_join assembled (not STATE_MISSING) and news.spine_empty false "
                "with named events? Consistency only — not an invented HIGH."
            ),
            "criteria": {
                "true": "Spine is present and events are named",
                "false": "Spine empty, news_join STATE_MISSING, or events missing — abstain event questions",
            },
        },
        "spine_empty_honesty": {
            "type": "noul",
            "instructions": "Is news.spine_empty true OR news_join==STATE_MISSING? Empty spine ≠ no HIGH.",
            "criteria": {
                "true": "Spine empty or news_join STATE_MISSING — event questions abstain",
                "false": "Spine present",
            },
        },
        "family_study_vs_keep": {
            "type": "choice",
            "instructions": (
                "Given identity.family_class and identity.sleeve, confirm the named class. "
                "Do not discover bleed as a Noul. hard_off is already an integer."
            ),
            "criteria": {
                "study": "Named family is study",
                "keep": "Named family is house_keep",
                "hard_off": "Named family is house_hard_off — integer already decided",
            },
        },
    }


def _speculative_questions() -> dict[str, Any]:
    return {
        "flow_stance": {
            "type": "choice",
            "instructions": "Is this fire with named H4/D1 flow, against it, or unclear? Named fields only.",
            "criteria": {
                "with_flow": "Side agrees with named H4/D1 flow",
                "against_flow": "Side fights named H4/D1 flow",
                "no_clear_flow": "Named flow is mixed, flat, or missing",
            },
        },
        "geometry_vs_tape": {
            "type": "score",
            "instructions": "Does geometry.stop_dist / plan_r fit named M15 vol? Do not define 1 as house 1R/6R.",
            "criteria": [
                "Stop likely dies in the next 1–2 M15 prints",
                "Ordinary house risk versus named vol",
                "Stop and target fit named vol",
            ],
        },
        "level_respect": {
            "type": "score",
            "instructions": "Holding/reclaiming a named supporting PDH/PDL/FVG vs firing through opposing? Ignore unassembled levels.",
            "criteria": [
                "Firing through a named opposing PDH/PDL/FVG",
                "No relevant named level",
                "Holding or reclaiming a named supporting level",
            ],
        },
        "event_proximity": {
            "type": "noul",
            "instructions": (
                "Is a named HIGH inside the CODE window (news.high_in_f5_window)? "
                "If spine empty or news_join STATE_MISSING, you do not know (near 0.5). "
                "Do not invent NEWS_PROTOCOL."
            ),
            "criteria": {
                "true": "A named HIGH is inside the code window",
                "false": "Named events exist and none are inside the code window",
            },
        },
        "a8_agrees": {
            "type": "noul",
            "instructions": "Metals A8 consistency only. Ignore when not a metals sleeve.",
            "criteria": {
                "true": "Named A8 fields agree with the integer pass bit",
                "false": "Named A8 fields disagree or are missing",
            },
        },
        "admit": {
            "type": "choice",
            "instructions": (
                "Fluid-inventory admit label (admit/abstain/hard_refuse). "
                "NOT the Policy C A|C|D menu. Code must not write policy_c_stand_down from hard_refuse. "
                "House hard-off stays integer."
            ),
            "criteria": {
                "admit": "Named tape and geometry still support taking the fire as a label",
                "abstain": "State is thin or mixed; do not steer",
                "hard_refuse": "Named tape or cost argues against the fire — log only",
            },
        },
        "cost_vs_tape": {
            "type": "score",
            "instructions": "Does named spread_r fit named M15 vol, not just stop_dist?",
            "criteria": ["Spread dominates named vol", "Ordinary", "Cheap versus named vol"],
        },
        "stale_standing": {
            "type": "noul",
            "instructions": "Is the standing / slate row stale versus clock.as_of_utc?",
            "criteria": {"true": "Standing is stale versus as-of", "false": "Standing is current or unknown"},
        },
        "last_refusal_class": {
            "type": "choice",
            "instructions": "If a last refusal is named, classify it. Do not invent a refusal.",
            "criteria": {
                "none": "No named last refusal",
                "cost": "Last named refusal was cost",
                "other": "Last named refusal was something else",
            },
        },
        "friday_cutoff_label": {
            "type": "noul",
            "instructions": "LABEL: is clock.is_friday and sessions.named friday_cutoff? Writer clock stays integer.",
            "criteria": {"true": "Friday cutoff named", "false": "Not Friday cutoff"},
        },
        "high_in_f5_window": {
            "type": "noul",
            "instructions": "Is news.high_in_f5_window true? If spine_empty or news_join STATE_MISSING, you do not know.",
            "criteria": {"true": "Code says HIGH in F5 window", "false": "Code says not, or spine empty"},
        },
        "gold_usd_comove": {
            "type": "choice",
            "instructions": "Named gold vs USD proxy only. Do not invent DXY. Unassembled → no_clear.",
            "criteria": {
                "with_usd": "Named gold_with_usd",
                "against_usd": "Named gold_against_usd",
                "no_clear": "mixed or unassembled — do not guess",
            },
        },
        "session_liquidity": {
            "type": "score",
            "instructions": "Score session liquidity from clock only — do not invent volume.",
            "criteria": [
                "Thin session (asia / dead / Friday cutoff)",
                "Ordinary London or NY",
                "London-NY overlap",
            ],
        },
        "occupancy_world": {
            "type": "score",
            "instructions": "Score occupancy clusters. KEEP-one stays an integer. Label, not refuse.",
            "criteria": [
                "Empty or unknown book",
                "One named cluster open",
                "Two or more clusters open",
            ],
        },
    }


def _place_questions() -> dict[str, Any]:
    """Default-off. Owner path OPEN after hist-prove. Writer still prints. No order_send here."""
    return {
        "place_stand_delay": {
            "type": "choice",
            "instructions": (
                "Given place_context (writer_ready, authority, last_refusal_class, ticket_draft_fp) "
                "and COMPLETE_STATE, would a later Chair APPLY want PLACE, STAND, or DELAY? "
                "Default-off until Challenge hist-prove. You do not send. You do not remint. "
                "You do not flatten. This is not eternal never_place — it is a typed candidate."
            ),
            "criteria": {
                "PLACE": "Named state supports authorizing the writer to print this ticket after hist-prove APPLY",
                "STAND": "Named state supports not printing this ticket now",
                "DELAY": "Wait for named session/news/occupancy to resolve; do not send now",
            },
        },
    }


def policy_c_questions(*, ablation: str = "core_speculative", include_place: bool = False) -> dict[str, Any]:
    ablation = (ablation or "core_speculative").strip().lower()
    pack = dict(_core_questions())
    if ablation in {"core_speculative", "full_fanout"}:
        pack.update(_speculative_questions())
    if ablation == "full_fanout":
        # Research arm only. Importing the 49-q pack is intentional noise/control.
        from src.judgment.jev_questions import symbol_fanout_questions

        full = dict(symbol_fanout_questions())
        full.update(pack)  # Policy C ids win on collision
        pack = full
    if include_place:
        pack.update(_place_questions())
    return pack

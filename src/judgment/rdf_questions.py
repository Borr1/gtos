"""RATES / DXY / FUNDING Jev question pack.

Four Nouls. Missing Challenge-true feeds are *null*, not false easing,
not 'no stress'. Code compose never resizes and never APPLY.

Never place / remint / flatten. Chair LABEL only from this pack.
"""

from __future__ import annotations

from typing import Any

from .jev_questions import MODEL
from .rates_dxy_funding import PACK_ID, SCHEMA, rdf_noul_targets

RDF_NOUL_TARGETS = {
    "usd_impulse": {
        "yes": "Named USD FX basket prints a USD-strengthening impulse at the named threshold.",
        "challenge_true": (
            "rdf.usd_impulse.challenge_true_target is true. "
            "Lab/fixture books may set lab_target; Challenge-true stays null until multi FX lands."
        ),
        "chair": "LABEL",
        "effect": "label",
    },
    "rates_impulse": {
        "yes": "A named yield series (US10Y / TNX / DGS10, or owner-promoted ZN) rose by the named threshold.",
        "challenge_true": (
            "rdf.rates_impulse.challenge_true_target is true. "
            "Expect null on this clone — no Challenge-true yield tape. "
            "Sierra ZN_CONTROL is control_only and is not this Noul."
        ),
        "chair": "LABEL",
        "effect": "label",
    },
    "funding_stress": {
        "yes": "A named TED / SOFR / FRA-OIS (or owner-named funding) row is at or above its threshold.",
        "challenge_true": (
            "rdf.funding_stress.challenge_true_target is true. "
            "Expect null on this clone. Gold spread and Sierra VIX_VXM are not funding."
        ),
        "chair": "LABEL",
        "effect": "label",
    },
    "risk_on_off": {
        "yes": "Named NAS100 / US30 / UK100 impulse is risk_off (the caution event).",
        "challenge_true": (
            "rdf.risk_on_off.challenge_true_target is true. "
            "False means named risk_on. Null means mixed or unassembled. "
            "Challenge-true stays null until multi index tapes land."
        ),
        "chair": "LABEL",
        "effect": "label",
    },
}


def rdf_fanout_questions() -> dict[str, Any]:
    return {
        "usd_impulse": {
            "type": "noul",
            "instructions": (
                "Is rdf.usd_impulse.value true? Use only named EURUSD / GBPUSD / "
                "USDJPY last-bar returns mapped onto USD. "
                "rdf.dxy is rejected or unassembled on this clone — do not invent ICE DXY. "
                "If rdf.usd_impulse.value is null, you do not know (near 0.5). "
                "Lab books are not Challenge-true."
            ),
            "criteria": {
                "true": "Named USD FX impulse is USD-up at the named threshold",
                "false": "Named USD impulse is flat/down, or you were given a decided false",
            },
        },
        "rates_impulse": {
            "type": "noul",
            "instructions": (
                "Is rdf.rates_impulse.value true? Only a named yield series counts. "
                "The USD FX basket is not a yield print. Sierra ZN control_only is not a yield print. "
                "If rdf.rates_impulse.value is null, you do not know (near 0.5) — "
                "do not say 'rates easing'. Do not invent US10Y, TNX, FRED, or NEWS_PROTOCOL."
            ),
            "criteria": {
                "true": "Named yield impulse is higher",
                "false": "Named yield assembled and not higher",
            },
        },
        "funding_stress": {
            "type": "noul",
            "instructions": (
                "Is rdf.funding_stress.value true? Only a named TED / SOFR / FRA-OIS "
                "(or other owner-named funding row) counts. "
                "world.liquidity.spread_r_of_stop is not funding. Sierra VIX is not funding. "
                "Chat / X / AI-funding prose is forbidden. "
                "If rdf.funding_stress.value is null, you do not know (near 0.5)."
            ),
            "criteria": {
                "true": "Named funding row is at or above its threshold",
                "false": "Named funding row exists and is below threshold",
            },
        },
        "risk_on_off": {
            "type": "noul",
            "instructions": (
                "Is rdf.risk_on_off.value true? Yes means named index impulse is risk_off. "
                "False means named risk_on. "
                "If stance is mixed or unassembled, rdf.risk_on_off.value is null — "
                "you do not know (near 0.5). Do not invent a VIX print."
            ),
            "criteria": {
                "true": "Named NAS100/US30/UK100 impulse is risk_off",
                "false": "Named impulse is risk_on",
            },
        },
        "usd_impulse_stance": {
            "type": "choice",
            "instructions": "Classify rdf.usd_impulse.stance. Do not invent DXY.",
            "criteria": {
                "stronger": "Named USD impulse is up",
                "weaker": "Named USD impulse is down",
                "flat": "Named USD impulse is inside the threshold",
                "unassembled": "No named USD FX impulse",
            },
        },
        "risk_on_off_stance": {
            "type": "choice",
            "instructions": "Classify rdf.risk_on_off.stance from named index snaps only.",
            "criteria": {
                "risk_on": "Named index impulse is up",
                "risk_off": "Named index impulse is down",
                "mixed": "Named index impulse is inside the threshold",
                "unassembled": "No named index impulse",
            },
        },
        "rdf_chair_draft": {
            "type": "choice",
            "instructions": (
                "Draft only. This pack is LABEL. ABSTAIN when all four Noul values "
                "are null. Never ENFORCE. Never VETO from a missing rates/funding feed. "
                "You never place, remint, flatten, or resize."
            ),
            "criteria": {
                "enforce": "Not used by this pack",
                "veto": "Not used by this pack — missing feeds are not a veto",
                "label": "At least one named RDF Noul is decided",
                "abstain": "All four RDF Noul values are null",
            },
        },
    }


def rdf_systemone_payload(state: dict[str, Any], *, model: str = MODEL) -> dict[str, Any]:
    return {
        "state": state,
        "model": model,
        "questions": rdf_fanout_questions(),
        "pack": PACK_ID,
        "rdf_schema": SCHEMA,
    }


def rdf_noul_ids() -> list[str]:
    return list(RDF_NOUL_TARGETS)


def compose_rdf_shadow(rdf: dict[str, Any] | None, answers: dict[str, Any] | None = None) -> dict[str, Any]:
    """Local compose. Never changes size. Never APPLY. Never sends."""
    answers = answers or {}
    rdf = rdf or {}
    twins = rdf_noul_targets(rdf)
    decided = [name for name, value in twins.items() if value is not None]
    draft = "label" if decided else "abstain"
    return {
        "schema": "gtos.judgment.rdf_compose.v0",
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_resize": True,
        "never_apply_size": True,
        "pack": PACK_ID,
        "code_twins": twins,
        "decided_nouls": decided,
        "chair_draft": draft,
        "chair_land_later": True,
        "disposition": "rdf_label_only",
        "jev_chair_draft": (answers.get("rdf_chair_draft") or {}).get("choice")
        if isinstance(answers.get("rdf_chair_draft"), dict)
        else None,
        "dxy_usable": bool((rdf.get("dxy") or {}).get("usable_as_ice_dxy")),
        "rates_assembled": bool((rdf.get("rates_impulse") or {}).get("assembled")),
        "funding_assembled": bool((rdf.get("funding_stress") or {}).get("assembled")),
    }

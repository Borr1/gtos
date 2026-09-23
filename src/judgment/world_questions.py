"""WORLD_STATE_V0 Jev question pack.

IDs are for our code; instructions carry the meaning. One System One call
over ``{gold, world}``. Challenge-true scoring first — prove on the F5
tape before any Chair ENFORCE.

Noul targets are the *yes* event. Code compose may pre-compute the same
fact; Jev is asked so the living tissue can disagree and abstain.

Never place / remint / flatten. Chair ENFORCE / VETO / LABEL. Writer prints.
"""

from __future__ import annotations

from typing import Any

from .jev_questions import MODEL
from .world_state import SCHEMA as WORLD_SCHEMA

PACK_ID = "gtos.judgment.world_pack.v0"

# Noul-first pack. Targets are Challenge-true *labels*, not live P&L.
WORLD_NOUL_TARGETS = {
    "world_state_sufficient": {
        "yes": "Named world blocks are present enough to judge desk context at clock.as_of_utc.",
        "challenge_true": "completeness.state_sufficient_for_desk is true on the as-of row.",
        "chair": "LABEL",
        "effect": "label",
    },
    "usd_strength_named": {
        "yes": "Named USD FX proxies show USD stronger versus gold-as-of.",
        "challenge_true": "world.usd.stance == stronger (code vote from EURUSD/GBPUSD/USDJPY snaps).",
        "chair": "LABEL",
        "effect": "label",
    },
    "gold_sold_into_usd_strength": {
        "yes": "Focus gold fire is the hedge-fund shape: short into named USD strength, or long into named USD weakness.",
        "challenge_true": "world.corr.code_gold_sold_into_usd_strength is true.",
        "chair": "VETO",
        "effect": "chair_draft",
    },
    "rates_path_assembled": {
        "yes": "A named yield series (US10Y / TNX / ZN) is present for this as-of.",
        "challenge_true": "world.completeness.named_yield is true. Expect false until a yield tape lands.",
        "chair": "LABEL",
        "effect": "label",
    },
    "usd_proxy_only": {
        "yes": "The rates block is an FX USD basket, not a yield print.",
        "challenge_true": "world.rates.usd_proxy_only is true.",
        "chair": "LABEL",
        "effect": "label",
    },
    "event_proximity_world": {
        "yes": "A named HIGH in world.news.events sits inside the CODE window (F5 T-15..T+60 or W7 T-15..T+2).",
        "challenge_true": "world.news.high_in_f5_window or world.news.high_in_w7_window is true.",
        "chair": "VETO",
        "effect": "chair_draft",
    },
    "calendar_honest_world": {
        "yes": "Spine is present AND (no host writer row, or host_news_inventory_status == READ).",
        "challenge_true": "not news.spine_empty and (host_news_source unassembled or host status READ).",
        "chair": "LABEL",
        "effect": "label",
    },
    "corr_gold_vs_usd_against": {
        "yes": "Named 20d gold D1 returns move against the named USD proxy.",
        "challenge_true": "world.corr.gold_vs_usd.relation == against_usd.",
        "chair": "LABEL",
        "effect": "label",
    },
    "corr_regime_broken": {
        "yes": "Named 20d gold↔USD correlation sign disagrees with the 60d sign.",
        "challenge_true": "world.corr.gold_vs_usd.regime_broken is true.",
        "chair": "LABEL",
        "effect": "label",
    },
    "risk_on_named": {
        "yes": "Named NAS100 / US30 / UK100 snaps are risk-on.",
        "challenge_true": "world.risk.stance == risk_on.",
        "chair": "LABEL",
        "effect": "label",
    },
    "gold_fights_risk": {
        "yes": "Focus gold side fights the named risk tape (long gold vs risk_off, or short gold vs risk_on).",
        "challenge_true": "code: short+risk_on or long+risk_off when both named.",
        "chair": "LABEL",
        "effect": "label",
    },
    "liquidity_hurtful_world": {
        "yes": "Named spread / vol says liquidity is the trade.",
        "challenge_true": "world.liquidity.spread_r_of_stop >= 0.10 when assembled (same 0.10 as cost tilt).",
        "chair": "LABEL",
        "effect": "label",
    },
    "cluster_crowded": {
        "yes": "Focus correlation cluster has another named open symbol on the Challenge tape.",
        "challenge_true": "world.occupancy.focus_cluster_crowded is true.",
        "chair": "VETO",
        "effect": "chair_draft",
    },
    "narrative_state_absent": {
        "yes": "No named desk-brief / narrative fields exist. Do not invent funding/AI prose.",
        "challenge_true": "world.narrative.source == unassembled.",
        "chair": "LABEL",
        "effect": "label",
    },
    "world_veto_usd_rates": {
        "yes": "Draft a Chair VETO: gold fire fights named USD / rates-proxy context.",
        "challenge_true": "gold_sold_into_usd_strength is true AND (corr against OR regime_broken).",
        "chair": "VETO",
        "effect": "chair_draft",
    },
    "world_veto_event": {
        "yes": "Draft a Chair VETO: named HIGH is inside the code window.",
        "challenge_true": "event_proximity_world target is true. Spine empty → expect ~0.5, not a veto.",
        "chair": "VETO",
        "effect": "chair_draft",
    },
}


def world_fanout_questions() -> dict[str, Any]:
    """Desk questions. Empty news spine is not 'no HIGH'. Absent yield is not easing."""
    return {
        "world_state_sufficient": {
            "type": "noul",
            "instructions": (
                "Do world.completeness.missing_fields and the named world blocks "
                "contain enough to judge desk context as-of world.clock.as_of_utc? "
                "Yes means at least one of usd.proxy, news.events, or occupancy "
                "clusters is named. No means the desk is dark. Use only named fields. "
                "Empty news spine is not 'no HIGH'. Missing yield is not 'rates easing'."
            ),
            "criteria": {
                "true": "Named world blocks are present enough to judge desk context",
                "false": "Desk blocks are missing or unknown",
            },
        },
        "usd_strength_named": {
            "type": "noul",
            "instructions": (
                "Is world.usd.stance stronger? Use only named EURUSD / GBPUSD / "
                "USDJPY snaps. world.usd.dxy is unassembled on this clone — do not "
                "invent a DXY print."
            ),
            "criteria": {
                "true": "Named USD FX proxies show USD stronger",
                "false": "Named USD is weaker, mixed, or unassembled",
            },
        },
        "gold_sold_into_usd_strength": {
            "type": "noul",
            "instructions": (
                "Is this the hedge-fund shape: focus gold short into named USD "
                "strength, or gold long into named USD weakness? Use world.focus.side "
                "and world.usd.stance. If either is missing or mixed, you do not know."
            ),
            "criteria": {
                "true": "Named gold side is sold into USD strength or bought into USD weakness",
                "false": "Named gold side agrees with USD, or stance is mixed/unassembled",
            },
        },
        "rates_path_assembled": {
            "type": "noul",
            "instructions": (
                "Is a named yield series present in world.rates.named_yield? "
                "Sierra ZN is control_only_absent. Do not treat the USD FX basket "
                "as a yield print."
            ),
            "criteria": {
                "true": "Named US10Y / TNX / ZN series exists for this as-of",
                "false": "Yield tape is unassembled — expected on this clone",
            },
        },
        "usd_proxy_only": {
            "type": "noul",
            "instructions": (
                "Is world.rates.usd_proxy_only true? Honesty check: rates path is "
                "an FX USD basket, not a rates print."
            ),
            "criteria": {
                "true": "Rates block is usd_proxy_basket only",
                "false": "Yield assembled, or even the FX basket is missing",
            },
        },
        "event_proximity_world": {
            "type": "noul",
            "instructions": (
                "Is a named HIGH in world.news.events inside the window the CODE uses "
                "(world.news.high_in_f5_window for F5, world.news.high_in_w7_window for W7)? "
                "If world.news.spine_empty is true, this question should be near 0.5 — "
                "you do not know. Do not invent NEWS_PROTOCOL endpoints or HIGH rows."
            ),
            "criteria": {
                "true": "A named HIGH is inside the code window",
                "false": "Named events exist and none are inside the code window",
            },
        },
        "calendar_honest_world": {
            "type": "noul",
            "instructions": (
                "Is world.news.spine_empty false AND (world.host_news.host_news_source "
                "is unassembled OR world.host_news.host_news_inventory_status is READ)? "
                "Host unread / UNKNOWN / NOT_READ is not an honest calendar even when "
                "JSON covering exists."
            ),
            "criteria": {
                "true": "Spine present and host writer READ or absent",
                "false": "Spine empty, or host writer present and not READ",
            },
        },
        "corr_gold_vs_usd_against": {
            "type": "noul",
            "instructions": (
                "Is world.corr.gold_vs_usd.relation against_usd? Use only the named "
                "20d D1 return correlation. Unassembled means you do not know."
            ),
            "criteria": {
                "true": "Named 20d gold returns move against the USD proxy",
                "false": "With USD, uncorrelated, or unassembled",
            },
        },
        "corr_regime_broken": {
            "type": "noul",
            "instructions": (
                "Is world.corr.gold_vs_usd.regime_broken true? 20d sign disagrees "
                "with 60d on named overlapping D1 returns."
            ),
            "criteria": {
                "true": "Named short/long correlation signs disagree",
                "false": "They agree, or correlation is unassembled",
            },
        },
        "risk_on_named": {
            "type": "noul",
            "instructions": (
                "Is world.risk.stance risk_on from named NAS100 / US30 / UK100 snaps? "
                "Do not invent a VIX print."
            ),
            "criteria": {
                "true": "Named index tapes are risk-on",
                "false": "risk_off, mixed, or unassembled",
            },
        },
        "gold_fights_risk": {
            "type": "noul",
            "instructions": (
                "Does world.focus.side fight world.risk.stance? Short gold vs risk_on, "
                "or long gold vs risk_off. Mixed / unassembled → you do not know."
            ),
            "criteria": {
                "true": "Named gold side fights named risk tape",
                "false": "Agrees, mixed, or unassembled",
            },
        },
        "liquidity_hurtful_world": {
            "type": "noul",
            "instructions": (
                "Is world.liquidity.spread_r_of_stop large enough versus a 0.10 house "
                "fraction that liquidity is the trade? Unassembled liquidity → you do not know. "
                "This is a size-tilt / LABEL question, never a new refuse."
            ),
            "criteria": {
                "true": "Named spread/vol eats a material fraction of the stop",
                "false": "Cost is ordinary or unassembled",
            },
        },
        "cluster_crowded": {
            "type": "noul",
            "instructions": (
                "Is world.occupancy.focus_cluster_crowded true? Occupancy KEEP-one "
                "stays the writer integer. You only label the named cluster."
            ),
            "criteria": {
                "true": "Named focus cluster has another open symbol",
                "false": "Clear or unassembled",
            },
        },
        "narrative_state_absent": {
            "type": "noul",
            "instructions": (
                "Is world.narrative.source unassembled? Yes is the honest answer on "
                "this clone. Do not fill funding / AI / chat-X narratives."
            ),
            "criteria": {
                "true": "No named desk-brief — abstain narrative judgments",
                "false": "A named narrative block exists (not expected in V0)",
            },
        },
        "world_veto_usd_rates": {
            "type": "noul",
            "instructions": (
                "Draft-only Chair VETO: does named gold fight named USD / rates-proxy "
                "context (gold_sold_into_usd_strength plus against_usd or regime_broken)? "
                "You do not refuse. You do not send. Chair VETO / LABEL later."
            ),
            "criteria": {
                "true": "Named USD/rates-proxy context argues a VETO draft",
                "false": "No named USD/rates VETO, or state unassembled",
            },
        },
        "world_veto_event": {
            "type": "noul",
            "instructions": (
                "Draft-only Chair VETO: named HIGH in the code window? "
                "Spine empty → you do not know (near 0.5), not a veto. "
                "Do not invent NEWS_PROTOCOL."
            ),
            "criteria": {
                "true": "Named HIGH in the code window",
                "false": "No named HIGH in window, or spine empty",
            },
        },
        "usd_stance": {
            "type": "choice",
            "instructions": (
                "Classify world.usd.stance. Do not invent DXY. Confirm the named vote."
            ),
            "criteria": {
                "stronger": "Named USD FX proxies are stronger",
                "weaker": "Named USD FX proxies are weaker",
                "mixed": "Named proxies disagree",
                "unassembled": "No named USD proxy snap",
            },
        },
        "risk_stance": {
            "type": "choice",
            "instructions": "Classify world.risk.stance from named index snaps only.",
            "criteria": {
                "risk_on": "Named NAS100/US30/UK100 are up",
                "risk_off": "Named index snaps are down",
                "mixed": "Named index snaps disagree",
                "unassembled": "No named index snap",
            },
        },
        "gold_macro_fit": {
            "type": "choice",
            "instructions": (
                "Given world.focus.side, world.usd.stance, world.risk.stance, and "
                "world.corr.gold_vs_usd.relation, is this gold fire with the named "
                "macro tape, against it, or unclear? Missing yield is not a rates "
                "story. Missing narrative is not a funding story."
            ),
            "criteria": {
                "with_macro": "Named gold side agrees with named USD/risk/corr",
                "against_macro": "Named gold side fights named USD/risk/corr",
                "unclear": "Named macro is mixed or unassembled",
            },
        },
        "chair_draft": {
            "type": "choice",
            "instructions": (
                "Draft only. What should the Chair stamp on this world row? "
                "ENFORCE means the Chair may later apply a named fluid effect. "
                "VETO means the Chair may later block a pre-fill. LABEL means "
                "write the nouns and leave the writer alone. ABSTAIN when "
                "world_state_sufficient is no. You never place, remint, or flatten."
            ),
            "criteria": {
                "enforce": "Named world context supports a later Chair ENFORCE on a proved wire",
                "veto": "Named world context supports a later Chair VETO draft",
                "label": "Named world context is worth a noun, not a gate",
                "abstain": "Desk state is insufficient or mixed — do not steer",
            },
        },
        "usd_pressure": {
            "type": "score",
            "instructions": (
                "How strong is named USD pressure on gold? 0 = USD weaker / gold "
                "supported; 1 = mixed or unassembled; 2 = USD stronger / gold sold."
            ),
            "criteria": [
                "Named USD weaker or gold supported by the USD proxy",
                "Mixed, flat, or unassembled USD proxy",
                "Named USD stronger — gold sold-into-strength shape",
            ],
        },
        "risk_alignment": {
            "type": "score",
            "instructions": "How aligned is focus gold side with named risk tape?",
            "criteria": [
                "Gold side fights named risk tape",
                "Mixed or unassembled risk tape",
                "Gold side agrees with named risk tape",
            ],
        },
        "liquidity_quality": {
            "type": "score",
            "instructions": (
                "Named liquidity quality from world.liquidity only. Sierra depth "
                "is absent. Do not invent an order book."
            ),
            "criteria": [
                "Named spread/vol dominates the stop",
                "Ordinary or unassembled",
                "Named cost is cheap versus the stop",
            ],
        },
        "gold_rates_coherence": {
            "type": "score",
            "instructions": (
                "How coherent is gold versus the *named* USD/rates-proxy tape? "
                "Because yield is unassembled, this score is USD-proxy coherence, "
                "not a real rates-path score. Say so by sitting at 1 when "
                "world.rates.assembled is false and only the FX basket exists."
            ),
            "criteria": [
                "Named gold fights a named USD-proxy tape",
                "Yield unassembled — USD-proxy only / mixed",
                "Named gold agrees with a *yield* tape (not expected in V0)",
            ],
        },
    }


def world_systemone_payload(state: dict[str, Any], *, model: str = MODEL) -> dict[str, Any]:
    """Fan-out over gold+world or a bare world object."""
    return {
        "state": state,
        "model": model,
        "questions": world_fanout_questions(),
        "pack": PACK_ID,
        "world_schema": WORLD_SCHEMA,
    }


def noul_ids() -> list[str]:
    return list(WORLD_NOUL_TARGETS)


def gold_fights_risk_named(world: dict[str, Any] | None) -> bool | None:
    """Code twin of the gold_fights_risk Noul target."""
    if not world:
        return None
    side = str(((world.get("focus") or {}).get("side") or "")).lower()
    stance = (world.get("risk") or {}).get("stance")
    if stance in (None, "unassembled", "mixed"):
        return None
    if side not in {"long", "short", "buy", "sell"}:
        return None
    short = side in {"short", "sell"}
    if stance == "risk_on":
        return short
    if stance == "risk_off":
        return not short
    return None


def calendar_honest_world_named(world: dict[str, Any] | None) -> bool | None:
    if not world:
        return None
    news = world.get("news") or {}
    host = world.get("host_news") or {}
    if news.get("spine_empty"):
        return False
    source = host.get("host_news_source")
    status = host.get("host_news_inventory_status")
    if source in (None, "unassembled"):
        return not bool(news.get("spine_empty"))
    return status == "READ"


def world_veto_usd_rates_named(world: dict[str, Any] | None) -> bool | None:
    if not world:
        return None
    sold = (world.get("corr") or {}).get("code_gold_sold_into_usd_strength")
    rel = ((world.get("corr") or {}).get("gold_vs_usd") or {}).get("relation")
    broken = ((world.get("corr") or {}).get("gold_vs_usd") or {}).get("regime_broken")
    if sold is None:
        return None
    if sold and (rel == "against_usd" or broken is True):
        return True
    if sold is False:
        return False
    return False


def compose_world_shadow(world: dict[str, Any] | None, answers: dict[str, Any] | None = None) -> dict[str, Any]:
    """Local compose for WORLD pack. Never changes size. Never sends.

    Chair stamps ENFORCE / VETO / LABEL later. This row is a draft receipt.
    """
    answers = answers or {}
    world = world or {}
    completeness = world.get("completeness") or {}
    news = world.get("news") or {}
    sufficient = bool(completeness.get("state_sufficient_for_desk"))
    sold = (world.get("corr") or {}).get("code_gold_sold_into_usd_strength")
    event_hit = bool(news.get("high_in_f5_window") or news.get("high_in_w7_window")) if not news.get("spine_empty") else None
    crowded = (world.get("occupancy") or {}).get("focus_cluster_crowded")
    veto_usd = world_veto_usd_rates_named(world)
    honest = calendar_honest_world_named(world)
    draft = "abstain"
    if sufficient:
        if veto_usd or event_hit or crowded:
            draft = "veto"
        else:
            draft = "label"
    return {
        "schema": "gtos.judgment.world_compose.v0",
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_resize": True,
        "pack": PACK_ID,
        "state_sufficient_for_desk": sufficient,
        "code_gold_sold_into_usd_strength": sold,
        "code_event_in_window": event_hit,
        "code_cluster_crowded": crowded,
        "code_calendar_honest_world": honest,
        "code_world_veto_usd_rates": veto_usd,
        "code_gold_fights_risk": gold_fights_risk_named(world),
        "chair_draft": draft,
        "chair_land_later": True,
        "disposition": "world_label_only",
        "jev_chair_draft": (answers.get("chair_draft") or {}).get("choice")
        if isinstance(answers.get("chair_draft"), dict)
        else None,
        "news_spine_empty": bool(news.get("spine_empty")),
        "yield_assembled": bool(completeness.get("named_yield")),
    }

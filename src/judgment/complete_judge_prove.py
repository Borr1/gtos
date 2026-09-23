"""Historical prove for complete-judge residual sites.

Walks Challenge 0 S15 / everywhere tape. Overlays only mutate
COMPLETE_STATE fields already on gold_state.v0 (completeness, occupancy,
sessions, g4_applies). Does not invent NEWS_PROTOCOL, final_sl, Friday
16Z+, or empty spine.

APPLY_CANDIDATE labels stay SHADOW. This prove does not APPLY fire rate
or size_ceiling.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .chair_enforce import stamp_chair_enforce
from .challenge import CHALLENGE_LOGIN
from .complete_judge import (
    ADMIT_RESIDUAL_IDS,
    G4_SOFT_IDS,
    G6_SOFT_IDS,
    admit_residual_choice,
    complete_state_view,
    compose_complete_judge,
    inject_complete_judge_answers,
)
from .everywhere import compose_everywhere
from .everywhere_tape import everywhere_historical_close_rows, inject_everywhere_answers
from .fluid_gates import EXPECTED_ENVELOPE, EXPECTED_FLUID, assert_inventory_shape
from .inventory import collect_live_inventory

MIN_DECIDABLE = 20
MIN_POLES = 2

# Existing Challenge tickets — overlays reuse identities, do not mint news.
_OVERLAY_TICKET_INSUFFICIENT = "291072108"
_OVERLAY_TICKET_REFUSAL = "291072108"
_OVERLAY_TICKET_CONF = "291087142"
_OVERLAY_TICKET_G4_KEEP = "291087142"
_OVERLAY_TICKET_G6_KEEP = "291087142"
_OVERLAY_TICKET_G8 = "291392252"


def _inv():
    return collect_live_inventory(
        sleeves=("spring", "vss", "metals_core"),
        workers=(f"challenge:{CHALLENGE_LOGIN}",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )


def _clone_row(row: dict[str, Any], *, tape_id: str, note: str) -> dict[str, Any]:
    gold = dict(row.get("gold_state") or {})
    ident = dict(gold.get("identity") or {})
    gold["identity"] = ident
    return {
        "tape_id": tape_id,
        "login": row.get("login") or CHALLENGE_LOGIN,
        "ticket": row["ticket"],
        "subclass": row.get("subclass"),
        "g4_applies": row.get("g4_applies"),
        "note": note,
        "gold_state": gold,
        "close_state": row.get("close_state"),
        "overlay": True,
    }


def hist_overlays(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Named COMPLETE_STATE overlays on existing Challenge tickets."""

    by_ticket = {str(r["ticket"]): r for r in base_rows if r.get("ticket")}
    out: list[dict[str, Any]] = []

    src = by_ticket.get(_OVERLAY_TICKET_INSUFFICIENT)
    if src:
        row = _clone_row(src, tape_id="cj-overlay-insufficient", note="hist_overlay_state_insufficient")
        gold = row["gold_state"]
        gold["completeness"] = {"state_sufficient_for_live": False, "missing_fields": ["geometry.stop"]}
        out.append(row)

        row = _clone_row(src, tape_id="cj-overlay-last-refusal", note="hist_overlay_last_refusal_cost")
        gold = row["gold_state"]
        occ = dict(gold.get("occupancy") or {})
        occ["last_refusal_class"] = "cost"
        gold["occupancy"] = occ
        out.append(row)

    src = by_ticket.get(_OVERLAY_TICKET_CONF)
    if src:
        row = _clone_row(src, tape_id="cj-overlay-conf-floor", note="hist_overlay_conf_floor")
        row["admit_choice"] = "admit"
        row["admit_conf"] = 0.40
        out.append(row)

        row = _clone_row(src, tape_id="cj-overlay-g4-keep", note="hist_overlay_g4_keep_exempt")
        ident = dict(row["gold_state"].get("identity") or {})
        ident["g4_applies"] = True
        row["gold_state"]["identity"] = ident
        row["g4_applies"] = True
        out.append(row)

        row = _clone_row(src, tape_id="cj-overlay-g6-keep", note="hist_overlay_g6_keep_exempt")
        row["gold_state"]["sessions"] = {"named": "london", "source": "overlay"}
        out.append(row)

        row = _clone_row(src, tape_id="cj-overlay-g6-unnamed", note="hist_overlay_g6_not_applicable")
        row["gold_state"]["sessions"] = {"named": "", "source": "overlay"}
        out.append(row)

    src = by_ticket.get(_OVERLAY_TICKET_G8)
    if src:
        row = _clone_row(src, tape_id="cj-overlay-g8-placed", note="hist_overlay_g8_already_placed")
        occ = dict(row["gold_state"].get("occupancy") or {})
        occ["already_placed_today"] = True
        occ["minutes_since_flat"] = 5
        occ["same_sleeve_reentry"] = True
        occ["new_named_fire"] = False
        row["gold_state"]["occupancy"] = occ
        out.append(row)

        row = _clone_row(src, tape_id="cj-overlay-g8-allow", note="hist_overlay_g8_new_named_after_15m")
        occ = dict(row["gold_state"].get("occupancy") or {})
        occ["already_placed_today"] = False
        occ["minutes_since_flat"] = 30
        occ["same_sleeve_reentry"] = False
        occ["new_named_fire"] = True
        row["gold_state"]["occupancy"] = occ
        out.append(row)

    return out


def _score_one(row: dict[str, Any], inventory) -> dict[str, Any]:
    gold = row.get("gold_state") or {}
    admit_choice = row.get("admit_choice")
    admit_conf = row.get("admit_conf")
    answers = inject_everywhere_answers(
        {**row, "gold_state": gold, "g4_applies": row.get("g4_applies")}
    )
    if admit_choice:
        answers["admit"] = {
            "choice": admit_choice,
            "confidence": admit_conf,
            "probabilities": {str(admit_choice): float(admit_conf or 0.0)},
        }
    elif isinstance(answers.get("admit"), dict) and answers["admit"].get("choice"):
        admit_choice = str(answers["admit"]["choice"])
        try:
            admit_conf = float(answers["admit"].get("confidence"))
        except (TypeError, ValueError):
            admit_conf = None
    view = complete_state_view(
        gold,
        g4_applies=bool(row.get("g4_applies")),
        admit_choice=admit_choice,
        admit_conf=admit_conf,
    )
    sites = compose_complete_judge(
        gold,
        g4_applies=bool(row.get("g4_applies")),
        admit_choice=admit_choice,
        admit_conf=admit_conf,
        answers=answers,
    )
    answers.update(
        inject_complete_judge_answers(
            gold,
            g4_applies=bool(row.get("g4_applies")),
            admit_choice=admit_choice,
            admit_conf=admit_conf,
        )
    )
    composed = compose_everywhere(
        inventory=inventory,
        answers=answers,
        gold_state=gold,
        close_state=row.get("close_state"),
        stake="sleeve_admit",
    )
    by_id = {s.site_id: s for s in composed.sites}
    stamp = stamp_chair_enforce(
        sleeve=(gold.get("identity") or {}).get("sleeve"),
        symbol=(gold.get("identity") or {}).get("symbol"),
        session_named=((gold.get("sessions") or {}).get("named")),
        occupancy=gold.get("occupancy"),
        g4_applies=bool(row.get("g4_applies") or (gold.get("identity") or {}).get("g4_applies")),
    )
    return {
        "tape_id": row.get("tape_id"),
        "ticket": row.get("ticket"),
        "login": row.get("login") or CHALLENGE_LOGIN,
        "overlay": bool(row.get("overlay")),
        "admit_residual": view["admit_residual"],
        "chair_soft_g4": view["chair_soft_g4"],
        "chair_soft_g6": view["chair_soft_g6"],
        "chair_soft_g8": view["chair_soft_g8"],
        "decidable": all(s.decidable or s.site_id == "chair_soft_g8" for s in sites),
        "sidecar_admit_residual": None if by_id.get("admit_residual") is None else by_id["admit_residual"].label,
        "sidecar_g4": None if by_id.get("chair_soft_g4") is None else by_id["chair_soft_g4"].label,
        "sidecar_g6": None if by_id.get("chair_soft_g6") is None else by_id["chair_soft_g6"].label,
        "size_ceiling": stamp.size_ceiling,
        "g4_size_ceiling": stamp.g4_size_ceiling,
        "g6_size_ceiling": stamp.g6_size_ceiling,
        "stamp_g4_label": stamp.g4_soft_label,
        "stamp_g6_label": stamp.g6_soft_label,
        "broker_effect": False,
        "never_place": True,
        "note": row.get("note"),
        "code_residual": admit_residual_choice(gold, admit_choice=admit_choice, admit_conf=admit_conf)[0],
    }


def prove_complete_judge() -> dict[str, Any]:
    """Offline hist prove. Returns a scorecard. Never places."""

    inventory = _inv()
    base = everywhere_historical_close_rows()
    rows = list(base) + hist_overlays(base)
    scored = [_score_one(row, inventory) for row in rows if row.get("ticket")]

    residual_poles = Counter(r["admit_residual"] for r in scored)
    g4_poles = Counter(r["chair_soft_g4"] for r in scored)
    g6_poles = Counter(r["chair_soft_g6"] for r in scored)
    g8_high = sum(1 for r in scored if r["chair_soft_g8"] is not None and float(r["chair_soft_g8"]) >= 0.60)
    g8_low = sum(1 for r in scored if r["chair_soft_g8"] is not None and float(r["chair_soft_g8"]) < 0.60)
    sidecar_match = sum(
        1
        for r in scored
        if r["sidecar_admit_residual"] == r["admit_residual"]
        and r["sidecar_g4"] == r["chair_soft_g4"]
        and r["sidecar_g6"] == r["chair_soft_g6"]
    )
    stamp_match = sum(
        1
        for r in scored
        if r["stamp_g4_label"] == r["chair_soft_g4"] and r["stamp_g6_label"] == r["chair_soft_g6"]
    )
    shape = assert_inventory_shape()
    n_decidable = sum(1 for r in scored if r["decidable"])

    apply_ok = (
        n_decidable >= MIN_DECIDABLE
        and len(residual_poles) >= MIN_POLES
        and len(g4_poles) >= MIN_POLES
        and len(g6_poles) >= MIN_POLES
        and g8_high >= 1
        and g8_low >= 1
        and sidecar_match == len(scored)
        and stamp_match == len(scored)
        and shape["n_fluid"] == EXPECTED_FLUID
        and shape["n_envelope"] == EXPECTED_ENVELOPE
        and all(p in ADMIT_RESIDUAL_IDS for p in residual_poles)
        and all(p in G4_SOFT_IDS for p in g4_poles)
        and all(p in G6_SOFT_IDS for p in g6_poles)
    )
    return {
        "schema": "gtos.judgment.complete_judge_prove.v1",
        "login": CHALLENGE_LOGIN,
        "n_rows": len(scored),
        "n_base": len(base),
        "n_overlays": sum(1 for r in scored if r["overlay"]),
        "n_decidable": n_decidable,
        "min_decidable": MIN_DECIDABLE,
        "residual_poles": dict(residual_poles),
        "g4_poles": dict(g4_poles),
        "g6_poles": dict(g6_poles),
        "g8_high": g8_high,
        "g8_low": g8_low,
        "sidecar_match": sidecar_match,
        "stamp_match": stamp_match,
        "n_fluid": shape["n_fluid"],
        "n_envelope": shape["n_envelope"],
        "fire_rate_apply": False,
        "size_ceiling_apply": False,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "news_protocol": "stamps_only_never_invent",
        "pass": apply_ok,
        "rows": scored,
    }

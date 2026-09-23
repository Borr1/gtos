"""P0 top-3 SHADOW fan-out stamps for warroom_shadow cycle (apply=false).

Honest mode: until System One is on the Challenge path, stamp question schemas
plus heuristic Choice labels from CF_D / KEEP bit rules (instrument×sleeve scoped).
Never place. Never invent NEWS. Never touch apply_authorized.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ASTRA = Path(__file__).resolve().parents[2] / "judgment" / "astra"
RESEARCH = Path(r"host-local\redacted_host\repo\research\warroom_20260920")


def _load(name: str) -> Any:
    for base in (ASTRA, RESEARCH):
        p = base / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return None


def _heuristic_p0(bits: dict[str, Any] | None = None) -> dict[str, Any]:
    """Map bit evaluator outputs → P0 Choice labels (SHADOW research only)."""
    bits = bits or {}
    keep = bool(bits.get("shadow.jev.keep_signature"))
    stand = bool(bits.get("shadow.jev.cf_D_stand_down_bit"))
    review = bool(bits.get("shadow.jev.keep_review_bit"))
    allow = bool(bits.get("shadow.jev.sleeve_family_allow_bit"))
    mult = bits.get("shadow.jev.cf_D_mult")
    miss = bits.get("shadow.jev.miss")

    # CF D miss
    if stand:
        cfd_choice = "A_STAND_DOWN"
    elif review:
        cfd_choice = "E_KEEP_CAP"
    elif miss == "event_gap":
        cfd_choice = "C_SIZE_TRIM"
    elif keep:
        cfd_choice = "E_KEEP_CAP"
    elif allow:
        cfd_choice = "D_FULL"
    else:
        cfd_choice = "B_SIZE_HALF"

    # KEEP review
    if review:
        keep_choice = "KEEP_REVIEW_HOLD"
    elif keep and miss == "ok_win":
        keep_choice = "KEEP_PRESERVE"
    elif keep:
        keep_choice = "KEEP_REVIEW_HOLD"
    else:
        keep_choice = "ABSTAIN"

    # Size intent
    if stand:
        size_choice = "stand_down"
    elif cfd_choice == "C_SIZE_TRIM":
        size_choice = "quarter"
    elif cfd_choice in ("B_SIZE_HALF",):
        size_choice = "half"
    else:
        size_choice = "full"

    return {
        "P0_CFD_MISS_FALSE_STRUCTURE": {
            "Choice": cfd_choice,
            "stand_down": stand,
            "cf_D_mult": mult,
            "apply": False,
            "label_source": "heuristic_bits",
        },
        "P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER": {
            "Choice": keep_choice,
            "keep_review_bit": review,
            "apply": False,
            "label_source": "heuristic_bits",
            "note": "REVIEW not hard-off",
        },
        "P0_CFD_SIZE_INTENT": {
            "Choice": size_choice,
            "apply": False,
            "label_source": "heuristic_bits",
            "note": "size label only — never place",
        },
    }


def build_shadow_jev_p0(bits: dict[str, Any] | None = None) -> dict[str, Any]:
    recipes = _load("P0_TOP3_SYSTEM_ONE_SHADOW_RECIPES.json") or {}
    qids = [
        "P0_CFD_MISS_FALSE_STRUCTURE",
        "P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER",
        "P0_CFD_SIZE_INTENT",
    ]
    heuristics = _heuristic_p0(bits)
    out: dict[str, Any] = {
        "schema": "gtos.shadow.shadow_jev_p0.v1",
        "apply": False,
        "system_one_called": False,
        "mode": "heuristic_shadow_until_system_one",
        "affinity_law": "instrument_x_sleeve_not_portable",
        "claim_soft": "CF_D_hold_70_30_4.713",
        "questions": qids,
    }
    for qid in qids:
        rec = (recipes.get("recipes") or {}).get(qid) or {}
        out[qid] = {
            **heuristics.get(qid, {}),
            "question_id": qid,
            "primitive": rec.get("primitive"),
            "Choice_options": [
                o.get("id")
                for o in (
                    ((rec.get("system_one_payload") or {}).get("questions") or [{}])[0].get(
                        "options"
                    )
                    or []
                )
            ]
            or None,
            "forbid": rec.get("forbid"),
            "apply": False,
        }
    # path_scorecard SHADOW fields (PROVISIONAL stub when no fold metrics)
    symbol = str((bits or {}).get("shadow.jev.path_scorecard.instrument") or (bits or {}).get("symbol") or "XAUUSD")
    sleeve = str((bits or {}).get("shadow.jev.path_scorecard.sleeve_id") or (bits or {}).get("sleeve_id") or "unknown")
    out["path_scorecard"] = merge_path_scorecard_stub(bits, symbol=symbol, sleeve_id=sleeve)
    out["path_scorecard_apply"] = False
    out["path_scorecard_place"] = False
    out["path_scorecard_promote_grade_to_admit"] = False
    return out


def merge_path_scorecard_stub(bits: dict[str, Any] | None = None, *, symbol: str = "XAUUSD", sleeve_id: str = "unknown") -> dict[str, Any]:
    """Stamp path_scorecard fields onto bits (PROVISIONAL stub). apply/place/promote false."""
    bits = dict(bits or {})
    try:
        from path_scorecard_shadow import emit_path_scorecard_into
    except Exception:
        try:
            from judgment.path_scorecard_shadow import emit_path_scorecard_into  # type: ignore
        except Exception:
            # inline minimal stub so fields always exist
            cell = f"{symbol}|{sleeve_id}"
            bits.update({
                "shadow.jev.path_scorecard.score": None,
                "shadow.jev.path_scorecard.grade": "PROVISIONAL",
                "shadow.jev.path_scorecard.random_timing_p": None,
                "shadow.jev.path_scorecard.beta": None,
                "shadow.jev.path_scorecard.maxdd": None,
                "shadow.jev.path_scorecard.instrument": symbol,
                "shadow.jev.path_scorecard.sleeve_id": sleeve_id,
                "shadow.jev.path_scorecard.affinity_cell": cell,
                "shadow.jev.path_scorecard.place": False,
                "shadow.jev.path_scorecard.promote_grade_to_admit": False,
                "shadow.jev.path_scorecard.apply": False,
            })
            return bits
    return emit_path_scorecard_into(bits, symbol=symbol, sleeve_id=sleeve_id, card_or_none=None)


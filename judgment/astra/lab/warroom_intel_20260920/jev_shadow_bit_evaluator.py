#!/usr/bin/env python3
"""SHADOW-only per-ticket Jev bit evaluator from Close Loop train rows.
Chair: live stamps must not be static constants — evaluate from ticket/close fields.
apply=false always.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

ALLOW_FAMILIES = frozenset({"spring", "vss_fxcross", "sub_mid", "dsp_expand"})
KEEP_FAMS = frozenset({"spring", "vss_fxcross", "sub_mid"})

_ASTRA = Path(__file__).resolve().parents[2] / "judgment" / "astra"
_RESEARCH = Path(r"host-local\redacted_host\repo\research\warroom_20260920")
_BOX = Path("/workspace/gtos/close_loop/war_room_20260920")
def _default_train() -> Path:
    for p in (
        _ASTRA / "jev_everywhere_lessons_0.jsonl",
        _RESEARCH / "jev_everywhere_lessons_0.jsonl",
        _BOX / "jev_everywhere_lessons_0.jsonl",
    ):
        if p.exists():
            return p
    return _ASTRA / "jev_everywhere_lessons_0.jsonl"
DEFAULT_TRAIN = _default_train()

def _fam(row: Dict[str, Any]) -> str:
    return (row.get("jev_sleeve_family") or row.get("sleeve_family") or row.get("family") or "unknown")

def _sleeve(row: Dict[str, Any]) -> str:
    return (row.get("sleeve") or "").lower()

def is_keep_signature(row: Dict[str, Any]) -> bool:
    f = _fam(row)
    sl = _sleeve(row)
    if f in KEEP_FAMS:
        return True
    return any(k in sl for k in ("spring", "vss_fxcross", "vss_fxcross", "sub_mid", "sub_mid"))

def sleeve_family_allow_bit(row: Dict[str, Any]) -> bool:
    f = _fam(row)
    sl = _sleeve(row)
    if f in ALLOW_FAMILIES:
        return True
    return any(k in sl for k in ("spring", "vss_fxcross", "sub_mid", "expanding_up_staircase", "expand"))

def keep_review_bit(row: Dict[str, Any]) -> bool:
    """KEEP + false_structure + orig_stop → no_boost/review — NOT hard-off."""
    miss = row.get("miss") or row.get("miss_type")
    exit_c = row.get("exit") or row.get("exit_class")
    return bool(
        is_keep_signature(row)
        and miss == "false_structure"
        and exit_c in ("orig_stop", "orig_sl", "orig_stop")
    )

def cf_D_stand_down_bit(row: Dict[str, Any]) -> bool:
    """FS non-KEEP stand_down (CF D research). KEEP exempt."""
    miss = row.get("miss") or row.get("miss_type")
    return bool(miss == "false_structure" and not is_keep_signature(row))

def cf_D_mult(row: Dict[str, Any]) -> float:
    """Research multiplier only — not live size APPLY."""
    if cf_D_stand_down_bit(row):
        return 0.0
    if is_keep_signature(row):
        return 1.0
    R = float(row.get("R") or row.get("realised_r_unit150") or 0)
    m = 1.0
    miss = row.get("miss") or row.get("miss_type")
    if miss == "false_structure" and R < 0:
        m *= 0.5
    sess = row.get("jev_session") or row.get("session")
    if (not is_keep_signature(row)) and sess in ("London", "NY", "London_NY_overlap", "Asia") and R < 0:
        m *= 0.75
    return m

def evaluate_bits(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema": "gtos.warroom_shadow.jev_bits.v1",
        "apply": False,
        "shadow.jev.sleeve_family_allow_bit": sleeve_family_allow_bit(row),
        "shadow.jev.keep_review_bit": keep_review_bit(row),
        "shadow.jev.cf_D_stand_down_bit": cf_D_stand_down_bit(row),
        "shadow.jev.keep_signature": is_keep_signature(row),
        "shadow.jev.sleeve_family": _fam(row),
        "shadow.jev.miss": row.get("miss") or row.get("miss_type"),
        "shadow.jev.exit": row.get("exit") or row.get("exit_class"),
        "shadow.jev.cf_D_mult": cf_D_mult(row),
        "shadow.jev.apply": False,
        "claim_stack": {
            "conservative_hold_70_30": 4.713,
            "secondary_hold_40_20": 8.123,
            "full_oracle_caveat": 11.168,
        },
    }

def load_train_index(path: Optional[Path] = None) -> Dict[int, Dict[str, Any]]:
    path = path or DEFAULT_TRAIN
    out: Dict[int, Dict[str, Any]] = {}
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            L = json.loads(line)
            out[int(L["ticket"])] = L
    return out

def evaluate_ticket(ticket: int, train_index: Optional[Dict[int, Dict[str, Any]]] = None,
                    overlay: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Per-ticket evaluation from train row (+ optional live overlay fields).
    Live overlay may supply miss/exit/sleeve if hydrate ahead of train join.
    """
    idx = train_index if train_index is not None else load_train_index()
    row = dict(idx.get(int(ticket)) or {})
    if overlay:
        row.update({k: v for k, v in overlay.items() if v is not None})
    if not row:
        return {
            "schema": "gtos.warroom_shadow.jev_bits.v1",
            "ticket": int(ticket),
            "apply": False,
            "error": "ticket_not_in_train_rows",
            "shadow.jev.apply": False,
        }
    bits = evaluate_bits(row)
    bits["ticket"] = int(ticket)
    bits["source"] = "train_row_plus_overlay" if overlay else "train_row"
    return bits


def evaluate_expanding_full_state(row: Dict[str, Any]) -> Dict[str, Any]:
    """Extend live bits with expanding full-state shadow fields (apply=false).

    Compose alive_sleeves_for_symbol via Dig recipe; regime_tag null-ok; fanout
    Choice/Score/Noul KEEP|STAND|REVIEW. Does not stamp V2 Challenge advisory.
    """
    bits = evaluate_bits(row)
    try:
        from expanding_full_state_emitters import emit_expanding_full_state_stamp
        stamp = emit_expanding_full_state_stamp(row)
        # Merge named capture fields into bits surface (still apply=false)
        for k in (
            "inventory.alive_sleeves_for_symbol",
            "inventory.candidate_sleeve_alive",
            "regime_tag",
            "shadow.jev.Choice",
            "shadow.jev.Choice_verb",
            "shadow.jev.choice_reason",
            "shadow.jev.Score",
            "shadow.jev.Noul_tags",
            "shadow.jev.stand_down",
            "occupancy",
            "occupancy_status",
            "corr_cluster",
            "corr_status",
        ):
            if k in stamp:
                bits[k] = stamp[k]
        bits["expanding_full_state_schema"] = stamp.get("schema")
        bits["forbidden_respected"] = stamp.get("forbidden_respected")
    except Exception as exc:
        bits["expanding_full_state_error"] = f"{type(exc).__name__}:{exc}"
    bits["apply"] = False
    bits["shadow.jev.apply"] = False
    return bits



def evaluate_spring_full_state(row: Dict[str, Any]) -> Dict[str, Any]:
    """Extend live bits with spring full-state shadow fields (apply=false).

    Dig compose alive (same join as expanding); regime_tag null-ok; fanout
    KEEP|STAND|REVIEW for false-spring. spring_promote_status=RESEARCH_OPEN_GROSS.
    alive_false Dig honesty: may be compose/registry gap, not proof sleeve-dead.
    """
    bits = evaluate_bits(row)
    try:
        from spring_full_state_emitters import emit_spring_full_state_stamp
        stamp = emit_spring_full_state_stamp(row)
        for k in (
            "inventory.alive_sleeves_for_symbol",
            "inventory.candidate_sleeve_alive",
            "inventory.dig_alive_honesty",
            "regime_tag",
            "shadow.jev.Choice",
            "shadow.jev.Choice_verb",
            "shadow.jev.choice_reason",
            "shadow.jev.Score",
            "shadow.jev.Noul_tags",
            "shadow.jev.stand_down",
            "occupancy",
            "occupancy_status",
            "corr_cluster",
            "corr_status",
            "spring_promote_status",
            "live_promote",
            "choice_signals",
            "armed_source",
        ):
            if k in stamp:
                bits[k] = stamp[k]
        bits["spring_full_state_schema"] = stamp.get("schema")
        bits["forbidden_respected"] = stamp.get("forbidden_respected")
    except Exception as exc:
        bits["spring_full_state_error"] = f"{type(exc).__name__}:{exc}"
    bits["apply"] = False
    bits["shadow.jev.apply"] = False
    return bits


def evaluate_all(path: Optional[Path] = None) -> Dict[str, Any]:
    idx = load_train_index(path)
    rows = [evaluate_ticket(t, idx) for t in sorted(idx)]
    return {
        "schema": "gtos.warroom_shadow.jev_bits_batch.v1",
        "n": len(rows),
        "apply": False,
        "counts": {
            "sleeve_family_allow": sum(1 for r in rows if r.get("shadow.jev.sleeve_family_allow_bit")),
            "keep_review": sum(1 for r in rows if r.get("shadow.jev.keep_review_bit")),
            "cf_D_stand_down": sum(1 for r in rows if r.get("shadow.jev.cf_D_stand_down_bit")),
        },
        "rows": rows,
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print(json.dumps(evaluate_all(), indent=2))
    elif len(sys.argv) > 1:
        print(json.dumps(evaluate_ticket(int(sys.argv[1])), indent=2))
    else:
        print(json.dumps(evaluate_all()["counts"], indent=2))

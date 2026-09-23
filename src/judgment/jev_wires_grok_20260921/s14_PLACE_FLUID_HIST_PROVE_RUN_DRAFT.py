#!/usr/bin/env python3
"""DRAFT hist-prove runner — 14_place_fluid_hist_prove_apply.

Default: dry-run Phase A pairing from existing Challenge shadow.jsonl
(NO TypeSafe POST — place_now is not in symbol_fanout_questions yet).
Never order_send. Never broker. Writes only under this session OUT.

Module_ATR Phase B is documented; this draft does not replay yearfold
fills (geometry_proxy honesty — see HIST_PROVE_PLAN.md).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
SHADOW = Path(
    "/workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent"
    "/judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl"
)
DEALS = Path(
    "/workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent"
    "/judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl"
)
BLOTTERS = {
    "three_fresh": Path(
        "/workspace/gtos/close_loop/war_room_20260920/"
        "blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl"
    ),
    "spring": Path(
        "/workspace/gtos/close_loop/war_room_20260920/"
        "blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl"
    ),
    "gbpjpy_vss": Path(
        "/workspace/gtos/close_loop/war_room_20260920/"
        "blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl"
    ),
    "gbpjpy_sub_mid": Path(
        "/workspace/gtos/close_loop/war_room_20260920/"
        "blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl"
    ),
}
PLC_IDS = [f"FLUID-PLC-00{i}" for i in range(1, 8)]
HARD_OFF_MARKERS = ("bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30")
KEEP_MARKERS = ("spring", "vss")


def _iter_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _hard_off(sleeve: str) -> bool:
    raw = (sleeve or "").lower()
    return any(m in raw for m in HARD_OFF_MARKERS)


def _keep(sleeve: str) -> bool:
    raw = (sleeve or "").lower()
    return any(m in raw for m in KEEP_MARKERS)


def phase_a_dry() -> dict:
    """Pair existing PLC labels vs writer placed — not place_now (missing)."""
    n = 0
    kinds: Counter[str] = Counter()
    plc_decidable: Counter[str] = Counter()
    plc_moved: Counter[str] = Counter()
    writer_placed = 0
    hard_off_placed = 0
    keep_placed = 0
    n_news_empty = 0
    n_invented_high = 0
    for row in _iter_jsonl(SHADOW) or []:
        n += 1
        kind = str(row.get("kind") or "")
        kinds[kind] += 1
        if kind in {"deal_close", "open"}:
            writer_placed += 1
        sleeve = str(
            ((row.get("house") or {}).get("sleeve"))
            or ((row.get("state") or {}).get("identity") or {}).get("sleeve")
            or ""
        )
        if kind in {"deal_close", "open"} and _hard_off(sleeve):
            hard_off_placed += 1
        if kind in {"deal_close", "open"} and _keep(sleeve):
            keep_placed += 1
        news = (row.get("state") or {}).get("news") or {}
        if news.get("spine_empty"):
            n_news_empty += 1
            if news.get("high_in_f5_window") is True:
                n_invented_high += 1
        gates = ((row.get("compose") or {}).get("fluid") or {}).get("gates") or {}
        for gid in PLC_IDS:
            g = gates.get(gid) or {}
            if g.get("decidable"):
                plc_decidable[gid] += 1
            if g.get("moved"):
                plc_moved[gid] += 1
    fire_rate = (writer_placed / n) if n else None
    return {
        "phase": "A_dry_existing_shadow_no_place_now",
        "shadow_path": str(SHADOW),
        "shadow_present": SHADOW.is_file(),
        "n": n,
        "kinds": dict(kinds),
        "writer_placed": writer_placed,
        "fire_rate_writer": fire_rate,
        "hard_off_placed": hard_off_placed,
        "keep_placed": keep_placed,
        "n_news_empty": n_news_empty,
        "n_invented_high": n_invented_high,
        "plc_decidable": dict(plc_decidable),
        "plc_moved": dict(plc_moved),
        "place_now_question_present": False,
        "cannot_pass_apply": True,
        "reason": "place_now not in symbol_fanout_questions; local STAND-only cannot PASS",
        "never_broker_place": True,
    }


def blotter_counts() -> dict:
    out = {}
    for name, path in BLOTTERS.items():
        n = 0
        if path.is_file():
            for _ in _iter_jsonl(path):
                n += 1
        out[name] = {"path": str(path), "present": path.is_file(), "n_rows": n}
    return {
        "lens": "Module_ATR",
        "never_merge_dig_edge": True,
        "honesty": "geometry_proxy_ohlc_touch ≠ live module TradeIntent",
        "blotters": out,
        "phase_b_status": "NOT_RUN_this_session",
    }


def main() -> None:
    receipt = {
        "schema": "gtos.jev.place_fluid.hist_prove.draft.v0",
        "session": "14_place_fluid_hist_prove_apply",
        "proven": False,
        "pass": False,
        "apply": False,
        "place": False,
        "broker_effect": False,
        "never_place_default": True,
        "owner_override_20260921_place_when_proved": True,
        "phase_a": phase_a_dry(),
        "phase_b_module_atr": blotter_counts(),
        "deals_present": DEALS.is_file(),
        "gate_to_apply": "see HIST_PROVE_PLAN.md — Chair NAME after PASS",
        "do_not_flip_GTOS_JEV_SLEEVE_SELECT_APPLY": True,
        "do_not_flip_GTOS_JEV_FLUID_GATES_APPLY_for_place": True,
    }
    dest = OUT / "HIST_PROVE_DRY_RECEIPT.json"
    dest.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(dest), "pass": False, "place": False}, indent=2))


if __name__ == "__main__":
    main()

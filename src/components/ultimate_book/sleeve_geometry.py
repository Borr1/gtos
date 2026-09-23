#!/usr/bin/env python3
"""Load measured ATR geometry per (tag, symbol class). Fable 5.1 J1 / B3.

Side is an OUTPUT of geometry.best_both_halves. Never up>=0.5.
FX keeps stop 1.0 ATR unless the FX class cell is ≥ 1.0 (0.75 ATR is the 5–8 pip bleed).
Filled tickets keep broker SL/TP — this only scales NEW intents.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Optional

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _scores(
    cache_key: tuple,
    facts: dict,
    questions: dict[str, str],
    anchors: dict | None = None,
) -> dict[str, float | None]:
    """One nineteen.score per question. Fewer than two anchors does not post."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    levels = anchors if isinstance(anchors, dict) else {}
    out = {str(qid): None for qid in questions}
    ask = None
    try:
        from src.judgment.nineteen import score as ask
    except Exception:
        ask = None
    if ask is not None:
        for qid, text in questions.items():
            try:
                out[str(qid)] = _finite(
                    ask(
                        payload,
                        question_id=str(qid),
                        instructions=str(text),
                        anchors=levels.get(str(qid)),
                    )
                )
            except Exception:
                out[str(qid)] = None
    _HOP[cache_key] = dict(out)
    return out

CLASS_FX = "fx_majors"
CLASS_METAL = "xau_xag"
CLASS_IDX = "idx_us30_us500_ger40_uk100_jp225"

FX_MAJORS = frozenset({
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "EURGBP",
    "GBPJPY", "EURJPY", "AUDUSD", "NZDUSD", "AUDJPY", "NZDJPY",
    "CADJPY", "CHFJPY", "EURCHF", "GBPCHF",
})
METALS = frozenset({"XAUUSD", "XAGUSD"})
INDICES = frozenset({
    "US30", "US500", "SPX500", "GER40", "UK100", "JP225",
    "NAS100", "US100", "FRA40", "EU50",
})

# Live module _STOP_ATR so we can recover ATR from intent.stop_dist.
MODULE_STOP_ATR: dict[str, float] = {'dsp_accepted_20low_then_second_flush': 0.75, 'dsp_bleed_accept_fresh_20low_second_push': 1.0, 'dsp_cascade_two_down_bars_then_third': 0.75, 'dsp_climax_2atr_onto_20high_then_fade': 1.0, 'dsp_climax_flush_to_96low_then_snap': 0.75, 'dsp_climax_onto_20high_then_fade': 0.75, 'dsp_close_on_20low_not_a_cascade_then_up': 1.0, 'dsp_descending_lows_accepted': 0.75, 'dsp_expanding_two_bar_run_tokyo': 1.0, 'dsp_expanding_up_staircase': 0.75, 'dsp_first_cash_bar_spike_and_flush': 1.0, 'dsp_first_crack_failed_reclaim': 0.75, 'dsp_high_vol_doji_after_reclaimed_flush': 1.0, 'dsp_huge_down_hold_then_spring': 1.0, 'dsp_isolated_20h_spike_then_fade': 0.75, 'dsp_isolated_spike_high': 1.0, 'dsp_london_bounce_fails_overnight_midpoint': 1.0, 'dsp_london_cascade_into_20low_springs': 0.75, 'dsp_london_two_up_into_20high_reverses': 0.75, 'dsp_reclaim_then_giveback': 0.75, 'dsp_rejection_wick_then_through': 0.75, 'dsp_shakeout_holds_run_lows': 0.75, 'dsp_small_bar_on_thrust_high': 0.75, 'dsp_spring_close_on_20low_through_the_box': 0.75, 'dsp_spring_first_print_of_range_low': 0.75, 'dsp_take_of_low_already_falling_continues': 0.75, 'dsp_three_bar_squeeze_into_high': 0.75, 'dsp_three_fresh_lower_lows': 0.75, 'dsp_two_bar_thrust_into_20high_continues': 0.75, 'dsp_volume_ramp_into_unrepaired_low': 0.75, 'dsp_walked_high_accepted_through': 1.0, 'dsp_weekend_gap_then_bleed_into_20low': 1.0, 'dsp_wide_bar_takes_both_extremes_then_reverse': 0.75, 'dsp_wide_down_then_micro_bounce_then_through': 1.0, 'xa_climax_spring': 1.0, 'xa_huge_20_extreme': 1.0, 'xa_huge_same_way': 0.75, 'xa_isolated_opposite': 1.0, 'xa_prior_huge': 1.0, 'xa_second_leg': 1.0, 'xa_second_rth': 0.75, 'xa_wave_two_standing': 0.75, 'xa_wide_extreme': 1.0}


def symbol_class(symbol: object) -> Optional[str]:
    s = str(symbol or "").strip().upper().replace(".CASH", "").replace("_CASH", "")
    if not s:
        return None
    if s in FX_MAJORS or (len(s) == 6 and s.isalpha() and s[:3] != "XAU" and s[:3] != "XAG"
                          and not any(k in s for k in ("US30", "US50", "GER", "UK10", "JP22"))):
        if s in FX_MAJORS:
            return CLASS_FX
        # 6-letter FX that isn't a metal/index name
        if s[:3] not in {"XAU", "XAG", "BTC", "ETH", "XRP"} and s[3:] in {
            "USD", "JPY", "GBP", "EUR", "CHF", "CAD", "AUD", "NZD",
        }:
            return CLASS_FX
    if s in METALS or s.startswith("XAU") or s.startswith("XAG"):
        return CLASS_METAL
    if s in INDICES or any(k in s for k in ("US30", "US500", "SPX", "GER40", "UK100", "JP225", "NAS100", "US100")):
        return CLASS_IDX
    return None


def _default_paths() -> list[Path]:
    here = Path(__file__).resolve().parent
    return [
        here / "data" / "SLEEVE_GEOMETRY_V1.json",
        here.parents[3] / "fable-pack" / "studies" / "redacted_host" / "jobs" / "j1" / "SLEEVE_GEOMETRY_V1.json",
        Path("/Users/borr/GTOSActive/fable-live/fable-pack/studies/redacted_host/jobs/j1/SLEEVE_GEOMETRY_V1.json"),
    ]


@lru_cache(maxsize=1)
def load_table(path: str | None = None) -> dict[str, Any]:
    candidates = [Path(path)] if path else _default_paths()
    for p in candidates:
        try:
            if p and p.is_file():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def lookup(tag: str, cls: str | None, *, table: Mapping[str, Any] | None = None) -> Optional[dict]:
    if not tag or not cls:
        return None
    doc = table if table is not None else load_table()
    rows = doc.get("rows") if isinstance(doc, Mapping) else None
    if not isinstance(rows, Mapping):
        return None
    row = rows.get(f"{tag}|{cls}")
    return dict(row) if isinstance(row, Mapping) else None


def resolved_stop_target(tag: str, cls: str | None, row: Mapping[str, Any]) -> tuple[float, float]:
    stop = float(row["stop_atr"])
    target = float(row["target_atr"])
    if cls == CLASS_FX:
        # One ATR is the unit. The cell stop is the other fact. The cell target
        # is a different distance and is not a level of this stop.
        one_atr = 1.0
        levels: list[tuple[str, float]] = [("one ATR", one_atr)]
        if math.isfinite(stop) and stop > 0 and stop != one_atr:
            levels.append(("this cell's stop in ATR", stop))
        floor = _scores(
            ("fx_stop_floor", str(tag), str(cls), round(stop, 6)),
            {
                "tag": tag,
                "class": cls,
                "stop_atr": stop,
                "one_atr": one_atr,
            },
            {
                "fx_stop_floor_atr": (
                    "The score you return is the lowest stop in ATR this FX state still uses. "
                    "An empty score leaves the cell's own stop. Do not send."
                ),
            },
            {"fx_stop_floor_atr": levels},
        ).get("fx_stop_floor_atr")
        if floor is not None and stop < floor:
            stop = floor
    return stop, target


def apply_class_geometry(intent, *, table: Mapping[str, Any] | None = None):
    """Resolve class geometry only for the generator's actual side.

    A missing, malformed, or opposite-side class cell preserves the valid native
    contract with an explicit receipt. It neither flips the setup nor blocks it.
    Invalid native geometry raises for the caller's per-slot invalid-data result.
    """
    tag = str(getattr(intent, "sleeve", "") or "")
    cls = symbol_class(getattr(intent, "symbol", None))
    old_stop = float(intent.stop_dist)
    old_target = None if intent.target_dist is None else float(intent.target_dist)
    direction = int(intent.direction)
    if isinstance(intent.direction, bool) or intent.direction not in (-1, 1) or not math.isfinite(old_stop) or old_stop <= 0:
        raise ValueError("invalid native geometry")
    if old_target is not None and (not math.isfinite(old_target) or old_target <= 0):
        raise ValueError("invalid native target")
    record = {"version":"geometry_v2", "tag":tag, "class":cls,
              "direction":direction, "parent_stop_dist":old_stop, "parent_target_dist":old_target}
    row = lookup(tag, cls, table=table)
    new_stop, new_target = old_stop, old_target
    if not row:
        record["resolution"] = "native_no_class_cell"
    elif tag not in MODULE_STOP_ATR:
        record["resolution"] = "native_unknown_atr_basis"
    else:
        try:
            raw_direction = row["direction"]
            if isinstance(raw_direction, bool) or raw_direction not in (-1, 1):
                raise ValueError("invalid measured class direction")
            measured_direction = int(raw_direction)
            if measured_direction != direction:
                record["resolution"] = "native_class_direction_mismatch"
            else:
                stop_atr, target_atr = resolved_stop_target(tag, cls, row)
                if not all(math.isfinite(x) and x > 0 for x in (stop_atr, target_atr)):
                    raise ValueError("invalid class geometry")
                atr = old_stop / MODULE_STOP_ATR[tag]
                new_stop, new_target = stop_atr*atr, target_atr*atr
                if not all(math.isfinite(x) and x > 0 for x in (new_stop,new_target)):
                    raise ValueError("invalid scaled geometry")
                record.update(resolution="matching_class", module_stop_atr=MODULE_STOP_ATR[tag],
                              stop_atr=stop_atr,target_atr=target_atr)
        except (KeyError, TypeError, ValueError, OverflowError):
            record["resolution"] = "native_invalid_class_cell"
            new_stop, new_target = old_stop, old_target
    record.update(stop_dist=new_stop, target_dist=new_target)
    return replace(intent, stop_dist=new_stop, target_dist=new_target,
                   geometry_provenance_json=json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False))

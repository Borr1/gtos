"""Gold-only hierarchical seats for Challenge 0.

PR #70 (`sleeve_ifs.py` / `sleeve_jev.py`) owns the generic sleeve tree.
This file asks gold-displacement questions that tree does not: stance
inside the named displacement, freshness vs a spent remint, geometry vs
the gold tape, THIS sleeve vs a named sibling on the same symbol, and
Score include-depth on the gold chunks *this* fire uses.

Founder shape: nested labels + log(n) tree dump, Score include-depth
hide/short/long/full, one completeness Noul on *this* gold object. Not
a linear keep/drop of the 45 DSP catalog, and not a Noul every tick.

`--tags`, HARD_OFF, FX-DSP drop, US30 standdown, ON_SURFACE, digest,
2-stop count, and the prop wall stay integers. Missing answers POST
THIS hop; a skip receipt is not the architecture. Untagged metals_core
/ ob_micro do not gain a fire. Do not remint. Do not leftover-ship.

Pin model ``jev-1.13.0``. One POST https://api.typesafe.ai/v1/systemone
via ``jev_client.evaluate`` (``merge_sleeve=False``). Every decision,
including each parameter, is that return: a Noul, a Choice, or a Score.
Prior outcomes are on that ask. An empty answer, a tie, or an error
leaves the return unset. Book ``0`` / ns ``operator``.
A missing score does not restore a persistence weight. This module
does not send. Never flatten ticket **294215389**.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

from .challenge import (
    CHALLENGE_HARD_OFF_FAMILIES,
    CHALLENGE_KEEP_FAMILIES,
    CHALLENGE_LOGIN,
    CHALLENGE_MAGIC,
    CHALLENGE_NS,
)
from .family import family_class_for, hard_off_family, keep_family
from .jev_questions import MODEL

GOLD_SLEEVE_ENV = "GTOS_JEV_GOLD_SLEEVE"
INCLUDE_DEPTH_LEVELS = ("hide", "short", "long", "full")
SIBLING_ORDER = ("keep_this", "yield_sibling", "abstain")
STANCE_ORDER = ("with_displacement", "against_displacement", "no_clear_displacement")
_PARAMETER_LEVELS = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
    "floor_room",
    "to_pass",
})
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
KIND_READ = "read"
FORBIDDEN_INSTRUCTION_TOKENS = ("jev", "system one", "choice")
OPEN_GOLD_SLEEVE = "dsp_descending_lows_accepted"

GOLD_SYMBOLS = frozenset({"XAUUSD", "XAUEUR", "XAUAUD"})
F5_FX_DSP_DROP_SYMBOLS = frozenset({"EURUSD", "GBPUSD", "USDJPY"})

# Launch contract `operator.json` token-bound 51 tags (as_of 2026-09-13).
CHALLENGE_TAGS_51: frozenset[str] = frozenset(
    {
        "crypto",
        "dsp_climax_2atr_onto_20high_then_fade",
        "dsp_close_on_20low_not_a_cascade_then_up",
        "dsp_expanding_two_bar_run_tokyo",
        "dsp_expanding_up_staircase",
        "dsp_first_cash_bar_spike_and_flush",
        "dsp_huge_down_hold_then_spring",
        "dsp_isolated_spike_high",
        "dsp_london_two_up_into_20high_reverses",
        "dsp_walked_high_accepted_through",
        "dsp_weekend_gap_then_bleed_into_20low",
        "dsp_wide_down_then_micro_bounce_then_through",
        "kz_london_crypto_low",
        "liq_asia_up_low_metal",
        "metals_softband",
        "mx_avausd_d1_donchian_20_breakout",
        "mx_btcusd_d1_donchian_20_breakout",
        "mx_ethusd_d1_donchian_20_breakout",
        "mx_ger40_cash_d1_volume_surge_reversal",
        "sub_mid_dn_revert",
        "vol_compression",
        "vp_euidx_pocgrav",
        "vss_fxcross_london_up_low",
        "xa_climax_spring",
        "xa_isolated_opposite",
        "xa_prior_huge",
        "xa_second_leg",
        "xa_wide_extreme",
        "xa_second_rth",
        "xa_wave_two_standing",
        "dsp_high_vol_doji_after_reclaimed_flush",
        "dsp_two_bar_thrust_into_20high_continues",
        "dsp_climax_onto_20high_then_fade",
        "dsp_first_crack_failed_reclaim",
        "dsp_three_fresh_lower_lows",
        "dsp_descending_lows_accepted",
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_volume_ramp_into_unrepaired_low",
        "dsp_small_bar_on_thrust_high",
        "dsp_wide_bar_takes_both_extremes_then_reverse",
        "dsp_three_bar_squeeze_into_high",
        "dsp_isolated_20h_spike_then_fade",
        "dsp_london_cascade_into_20low_springs",
        "dsp_rejection_wick_then_through",
        "dsp_shakeout_holds_run_lows",
        "dsp_cascade_two_down_bars_then_third",
        "dsp_take_of_low_already_falling_continues",
        "dsp_spring_first_print_of_range_low",
        "dsp_reclaim_then_giveback",
        "dsp_accepted_20low_then_second_flush",
        "dsp_london_bounce_fails_overnight_midpoint",
    }
)

# Writer belt-and-suspenders (`minimal_size.F5_HARD_OFF_SLEEVES`) plus launch
# `hard_off_sleeves_absent_from_tags`. Tags remain the integer; this set is
# the named surface, not a second `--tags`.
NAMED_HARD_OFF_SLEEVES: frozenset[str] = frozenset(
    {
        "asia_pdl_fade",
        "asian_fade",
        "asian_fade_widen",
        "metal_session_reversion",
        "dsp_climax_flush_to_96low_then_snap",
        "dsp_isolated_flush_to_20low_snap",
        "dsp_small_bar_sit_on_20high_rejects",
        "dsp_already_wide_down_bar_second_wave",
        "dsp_overnight_box_failed_floor_probe",
        "dsp_cascade_last_two_not_yet_four",
        "dsp_session_open_already_live",
        "dsp_two_open_bars_down_then_cascade",
        "dsp_climax_into_high_then_dump",
        "dsp_bleed_accept_fresh_20low_second_push",
        "idxrev",
        "orb_crypto_london",
        "orb_crypto_london_widen",
        "xa_huge_20_extreme",
        "xa_huge_same_way",
        "mx_us30_cash_d1_volume_surge_reversal",
    }
)

# DSP/XA leftover ON_SURFACE still lists FX+US30+XAU. After J6 FX drop and
# the US30 standdown the live gold print is XAUUSD-only.
TAGGED_DSP_GOLD: frozenset[str] = frozenset(
    t for t in CHALLENGE_TAGS_51 if t.startswith("dsp_")
)
TAGGED_XA_GOLD: frozenset[str] = frozenset(
    t for t in CHALLENGE_TAGS_51 if t.startswith("xa_")
)
TAGGED_W7_GOLD: frozenset[str] = frozenset(
    {
        "metals_softband",
        "liq_asia_up_low_metal",
        "sub_mid_dn_revert",
    }
)
GOLD_CAPABLE_TAGS: frozenset[str] = TAGGED_DSP_GOLD | TAGGED_XA_GOLD | TAGGED_W7_GOLD
assert len(CHALLENGE_TAGS_51) == 51
assert len(GOLD_CAPABLE_TAGS) == 42

# Generators that can print XAUUSD but cannot fire on this book (not tagged,
# HARD_OFF, or both). Inventory, not an arm list.
MISSING_GOLD_SLEEVES: tuple[tuple[str, str], ...] = (
    ("metals_core", "built_not_tagged"),
    ("metals_ob_micro", "built_not_tagged"),
    ("metal_session_reversion", "hard_off_and_not_tagged"),
    ("asia_pdl_fade", "hard_off_gold_in_pool"),
    ("sub_xvol_pullback", "clean3_gold_surface_not_tagged"),
    ("dsp_already_wide_down_bar_second_wave", "kill_dsp"),
    ("dsp_bleed_accept_fresh_20low_second_push", "kill_dsp"),
    ("dsp_cascade_last_two_not_yet_four", "kill_dsp"),
    ("dsp_climax_flush_to_96low_then_snap", "kill_dsp"),
    ("dsp_climax_into_high_then_dump", "kill_dsp"),
    ("dsp_isolated_flush_to_20low_snap", "kill_dsp"),
    ("dsp_overnight_box_failed_floor_probe", "kill_dsp"),
    ("dsp_session_open_already_live", "kill_dsp"),
    ("dsp_small_bar_sit_on_20high_rejects", "kill_dsp"),
    ("dsp_two_open_bars_down_then_cascade", "kill_dsp"),
    ("dsp_climax_onto_20high_then_fade_cashhole", "absent_dsp"),
    ("dsp_climax_onto_20high_then_fade_london", "absent_dsp"),
    ("dsp_high_vol_doji_after_reclaimed_flush_fx", "absent_dsp"),
    ("xa_huge_20_extreme", "kill_xa"),
    ("xa_huge_same_way", "kill_xa"),
)

INTEGER_FACTS: tuple[str, ...] = (
    "tags_intersection",
    "named_hard_off",
    "f5_fx_dsp_drop",
    "us30_standdown",
    "on_surface_remaining_xau",
    "include_clean3",
    "token_digest_match",
    "two_stop_count",
    "prop_wall",
    "operator_flatten_flag",
)

_CHUNKS_DSP = ("displacement", "geometry", "session", "vol", "occupancy")
_CHUNKS_XA = ("displacement", "geometry", "session", "occupancy")
_CHUNKS_METALS = ("session", "vol", "geometry")
_CHUNKS_LIQ = ("session", "pdl", "vol")
_CHUNKS_SUB = ("session", "cell", "occupancy")


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _symbol_key(symbol: str) -> str:
    raw = _norm(symbol).replace(".", "_")
    upper = raw.upper()
    if upper in {"US30", "US30_CASH"}:
        return "US30_cash"
    if upper in GOLD_SYMBOLS:
        return upper
    return raw


def gold_sleeve_env_on() -> bool:
    """Default ON. ``0`` / ``false`` / ``no`` / ``off`` restores no gold seats."""
    raw = os.environ.get(GOLD_SLEEVE_ENV, "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def is_gold_symbol(symbol: str) -> bool:
    return _symbol_key(symbol) in GOLD_SYMBOLS


def live_gold_positions(raw: Any = None) -> list[dict[str, Any]] | None:
    """Gold rows from the lock-wrapped read. ``None`` when that read failed."""
    from src.components.ultimate_book.open_tickets import read_open_positions, writer_terminal

    rows = read_open_positions(writer_terminal() if raw is None else raw)
    if rows is None:
        return None
    return [row for row in rows if is_gold_symbol(str(row.get("symbol") or ""))]


def gold_node_for(sleeve: str, *, symbol: str = "XAUUSD") -> str:
    """First hop of the *gold* tree. Not PR #70's generic family node."""
    sl = _norm(sleeve)
    if keep_family(sl):
        return "house_keep"
    if sl.startswith("dsp_"):
        return "displacement"
    if sl.startswith("xa_"):
        return "xa_timing"
    if sl in {"metals_softband", "metals_core", "metals_ob_micro"}:
        return "metals"
    if sl == "liq_asia_up_low_metal":
        return "liquidity"
    if sl.startswith("sub_"):
        return "substrate"
    if hard_off_family(sl, symbol):
        return "house_hard_off"
    if sl:
        return "other"
    return "other"


def used_gold_chunks(sleeve: str) -> tuple[str, ...]:
    """Query-aware chunks for THIS gold fire. Not the 45-DSP catalog."""
    sl = _norm(sleeve)
    if sl.startswith("dsp_"):
        return _CHUNKS_DSP
    if sl.startswith("xa_"):
        return _CHUNKS_XA
    if sl == "liq_asia_up_low_metal":
        return _CHUNKS_LIQ
    if sl.startswith("sub_"):
        return _CHUNKS_SUB
    if sl.startswith("metals_") or sl.startswith("metal_"):
        return _CHUNKS_METALS
    return ("session", "geometry")


def hierarchical_labels(
    sleeve: str,
    *,
    symbol: str = "XAUUSD",
    side: str = "",
    branch: str = "fire",
) -> dict[str, Any]:
    """Nested labels for log(n) tree search. Not a flat transcript."""
    node = gold_node_for(sleeve, symbol=symbol)
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "origin": "f5_challenge",
        "family_node": node,
        "sleeve": _norm(sleeve),
        "symbol": _symbol_key(symbol),
        "side": _norm(side).lower(),
        "branch": branch,
        "keep_families": CHALLENGE_KEEP_FAMILIES,
        "hard_off_families": CHALLENGE_HARD_OFF_FAMILIES,
        "family_class": family_class_for(
            sleeve, symbol=symbol, origin="f5_challenge"
        ),
    }


def can_fire_gold_on_challenge(
    sleeve: str, symbol: str = "XAUUSD"
) -> tuple[bool, str]:
    """Integer predicate. Semantic overlay does not override this."""
    sl = _norm(sleeve)
    sy = _symbol_key(symbol)
    if sy == "US30_cash" or sy.upper().startswith("US30"):
        return False, "us30_standdown"
    if sy not in GOLD_SYMBOLS:
        return False, "not_gold_symbol"
    if sl.startswith("dsp_") and sy in F5_FX_DSP_DROP_SYMBOLS:
        return False, "f5_fx_dsp_drop"
    if sl in NAMED_HARD_OFF_SLEEVES:
        return False, "named_hard_off"
    if sl not in CHALLENGE_TAGS_51:
        return False, "not_tagged"
    if sl not in GOLD_CAPABLE_TAGS:
        return False, "sleeve_surface_has_no_gold"
    return True, "ok"


def gold_capable_tags() -> tuple[str, ...]:
    return tuple(sorted(GOLD_CAPABLE_TAGS))


def _limit_key(name: Any) -> bool:
    token = str(name).strip().lower().replace("-", "_")
    return token in _LIMIT_KEYS


def _plain(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(key):
                continue
            out[str(key)] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _plain(value)
    return value


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


def _score_q(instructions: str, criteria: list[str]) -> dict[str, Any]:
    return {
        "type": "score",
        "instructions": _plain(instructions),
        "criteria": [_plain(item) for item in criteria],
    }


def _choice_q(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    return {
        "type": "choice",
        "instructions": _plain(instructions),
        "criteria": {str(key): _plain(text) for key, text in criteria.items()},
    }


def _noul_q(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": _plain(instructions),
        "criteria": {str(key): _plain(text) for key, text in criteria.items()},
    }


def _include_q(chunk: str) -> dict[str, Any]:
    return _score_q(
        (
            f"For this gold fire's query, how much of the named `{chunk}` chunk "
            "of gold_state should occupy context? hide / short / long / full. "
            "Not a keep/drop of the sleeve catalog. Do not compact the Challenge "
            "session. Clock facts (dead 21–00Z, Friday 16Z, FX-DSP drop, US30 "
            "off) stay integers — they are not this Score."
        ),
        [
            "Hide this chunk — not needed for this gold fire",
            "Short summary of the named fields in this chunk",
            "Longer summary of the named fields in this chunk",
            "Include the whole named chunk",
        ],
    )


def gold_subtree_questions(
    sleeve: str,
    *,
    symbol: str = "XAUUSD",
    side: str = "",
    branch: str = "fire",
    raw: Any = None,
) -> dict[str, Any]:
    """Dump the gold subtree for THIS sleeve only.

    Empty questions + ``ask=False`` when the integer surface cannot fire gold.
    Missing gold seats (metals_core, HARD_OFF DSP) never get a completeness
    Noul that could be misread as a PASS.
    """
    ok, reason = can_fire_gold_on_challenge(sleeve, symbol)
    labels = hierarchical_labels(sleeve, symbol=symbol, side=side, branch=branch)
    if not ok:
        return {
            "ask": False,
            "reason": reason,
            "labels": labels,
            "questions": {},
            "integer_facts": INTEGER_FACTS,
            "extra_pass": False,
        }

    sl = _norm(sleeve)
    node = labels["family_node"]
    chunks = used_gold_chunks(sl)
    questions: dict[str, dict[str, Any]] = {
        "gold_sleeve_state_sufficient": _noul_q(
            (
                "Is THIS gold_state object complete enough to judge this named "
                f"`{sl}` fire on `{_symbol_key(symbol)}` as-of clock.as_of_utc? "
                "One Noul on this object. Nulls stay null. Empty news spine is "
                "not 'no HIGH'. Family unknown (Challenge ticket 292427064) is "
                "low. Do not Noul every DSP every tick."
            ),
            {
                "true": "Named gold blocks are present enough to judge this fire",
                "false": "A required named gold block is missing or unknown",
            },
        ),
    }
    for chunk in chunks:
        questions[f"gold_include_{chunk}"] = _include_q(chunk)

    if sl.startswith("dsp_") or sl.startswith("xa_"):
        questions["dsp_gold_stance"] = _choice_q(
            (
                "Given identity.side and the named displacement on this gold "
                "bar (M15 range / H4 flow / session), is this fire *in* the "
                "displacement, against it, or is the displacement unclear? "
                "Owner destination: up with up, down with down. House 0.75/6 "
                "or 1/6 is not this named stance."
            ),
            {
                "with_displacement": "Side agrees with the named gold displacement",
                "against_displacement": "Side fades or fights the named displacement",
                "no_clear_displacement": "Named displacement is mixed, spent, or missing",
            },
        )
        questions["dsp_gold_fresh"] = _noul_q(
            (
                "Do writer integers plus occupancy say this is a *new* named "
                "gold displacement on a flat symbol (isolated ≥15m), not the "
                "spent ticket? Challenge walked_hi 291072108 remint-of "
                "291096187 is the live shape of a spent fire. Occupancy HOLD "
                "is dead; this Noul is the decision."
            ),
            {
                "true": "New named gold fire on a flat symbol",
                "false": "Same spent displacement / remint of a closed ticket",
            },
        )
        questions["dsp_gold_geometry"] = _score_q(
            (
                "Does this stop/target fit the named gold tape, or does the "
                "stop die in the next 1–2 M15 prints? Do not define 1 as "
                "house 1R/6R. G-FULL unsigned 2R: lo vol p_target 0.267 vs "
                "xhi 0.087. Challenge 5/5 XAU winners were time_stop, not "
                "broker_tp. High-vol DSP needs this Score, not a louder vr."
            ),
            [
                "0 — stop likely dies next 1–2 M15 on this gold tape",
                "1 — ordinary fit; not a house 1R/6R echo",
                "2 — stop/target fit named gold vol and session",
            ],
        )

    if sl.startswith("xa_"):
        questions["xa_gold_timing"] = _score_q(
            (
                "Is this xasset timing still a gold displacement seat, or a "
                "restart on a spent XA print? Session × vol stay separate. "
                "xa_huge is HARD_OFF integer — this Score is not asked there."
            ),
            [
                "0 — spent / wrong session / xhi gold vol",
                "1 — ordinary XA timing on gold",
                "2 — clean gold hour and named displacement still live",
            ],
        )

    from src.components.ultimate_book.open_tickets import (
        question_with_open_tickets,
        writer_terminal,
    )

    sibling_text, open_card = question_with_open_tickets(
        (
            f"On `{_symbol_key(symbol)}`, does THIS named sleeve `{sl}` still "
            "own the fire versus named siblings on the same symbol, or should "
            "THIS sleeve stand for a sibling? Occupancy keep-one stays integer. "
            "Do not invent a second unit."
        ),
        writer_terminal() if raw is None else raw,
    )
    questions["gold_vs_sibling"] = _choice_q(
        sibling_text,
        {
            "keep_this": (
                "THIS named gold sleeve still owns the fire versus siblings "
                "on this symbol"
            ),
            "yield_sibling": (
                "A named sibling on this symbol is the fire; THIS sleeve stands"
            ),
            "abstain": "Siblings unassembled or mixed; do not steer",
        },
    )
    questions["gold_size_tilt"] = _score_q(
        (
            "The score you return is the size tilt for this named gold sleeve "
            "on this state. It may sit between the levels. An empty score "
            "leaves the tilt unset. Do not send. Do not flatten."
        ),
        list(_PARAMETER_LEVELS),
    )
    questions["gold_threshold"] = _score_q(
        (
            "The score you return is the threshold for this named gold sleeve "
            "on this state. It may sit between the levels. An empty score "
            "leaves the threshold unset. Do not send. Do not flatten."
        ),
        list(_PARAMETER_LEVELS),
    )
    questions["gold_loop_bound"] = _score_q(
        (
            "How many named chunks of this gold fire are in view? "
            "The score you return is that bound. It may sit between the levels. "
            "An empty score leaves the bound unset. Do not send. Do not flatten."
        ),
        list(_PARAMETER_LEVELS),
    )

    return {
        "ask": True,
        "reason": "ok",
        "labels": labels,
        "node": node,
        "chunks": chunks,
        "questions": questions,
        "integer_facts": INTEGER_FACTS,
        "extra_pass": False,
        "open_ticket_card": open_card,
        "snippet": (
            f"Gold seat `{sl}` on `{_symbol_key(symbol)}`; "
            "displacement stance/fresh/geometry are ranges, not KEEP-OFF"
        ),
    }


def _score_of(block: Any) -> float | None:
    """The Score on this block. It is not snapped to a level."""

    if isinstance(block, Mapping):
        if block.get("error"):
            return None
        parsed: float | None = None
        try:
            from .jev_questions import returned_number

            parsed = _finite(returned_number(block))
        except Exception:
            parsed = None
        if parsed is not None:
            return parsed
        if "score" in block:
            return _finite(block.get("score"))
        if "value" in block:
            return _finite(block.get("value"))
        return None
    return _finite(block)


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays a miss."""

    if isinstance(block, Mapping):
        if block.get("error") or "noul" not in block:
            return None
        raw = block.get("noul")
    else:
        raw = block
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _local_unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie or an empty block is not a decision."""

    if not isinstance(probabilities, Mapping) or not probabilities or not order:
        return None
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in probabilities.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _finite(value)
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return None
    best = max(numeric.values())
    winners = [
        name
        for name in order
        if name in numeric and numeric[name] == best
    ]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or not order:
        return None
    raw = block.get("probabilities")
    probs = raw if isinstance(raw, Mapping) else None
    local = _local_unique(probs, order)
    if local is None:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(probs) if isinstance(probs, Mapping) else None, order)
    except Exception:
        return local
    if picked is None or str(picked) != local:
        return None
    return local


def _order_for(qid: str, block: Mapping[str, Any]) -> tuple[str, ...]:
    if qid == "gold_vs_sibling":
        return SIBLING_ORDER
    if qid == "dsp_gold_stance":
        return STANCE_ORDER
    criteria = block.get("criteria")
    if isinstance(criteria, Mapping):
        return tuple(str(key) for key in criteria)
    return ()


def _confidence(block: Any) -> float | None:
    if not isinstance(block, Mapping) or "confidence" not in block:
        return None
    return _finite(block.get("confidence"))


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float] | None:
    if not isinstance(block, Mapping):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return None
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _finite(value)
        if number is None:
            continue
        numeric[name] = number
    return numeric or None


def include_depth_questions(
    sleeve: str,
    *,
    symbol: str = "XAUUSD",
    side: str = "",
    branch: str = "fire",
) -> dict[str, Any]:
    pack = gold_subtree_questions(sleeve, symbol=symbol, side=side, branch=branch)
    return {
        qid: q
        for qid, q in (pack.get("questions") or {}).items()
        if str(qid).startswith("gold_include_")
    }


def decision_questions(
    sleeve: str,
    *,
    symbol: str = "XAUUSD",
    side: str = "",
    branch: str = "fire",
) -> dict[str, Any]:
    pack = gold_subtree_questions(sleeve, symbol=symbol, side=side, branch=branch)
    return {
        qid: q
        for qid, q in (pack.get("questions") or {}).items()
        if not str(qid).startswith("gold_include_")
    }


def intent_packs(
    sleeve: str,
    *,
    symbol: str = "XAUUSD",
    side: str = "",
    branch: str = "fire",
) -> dict[str, dict[str, Any]]:
    return {
        "include_depth": include_depth_questions(
            sleeve, symbol=symbol, side=side, branch=branch
        ),
        "decision": decision_questions(
            sleeve, symbol=symbol, side=side, branch=branch
        ),
    }


def _answers_missing(answers: Mapping[str, Any] | None) -> bool:
    return answers is None or (isinstance(answers, Mapping) and not answers)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = []


def _remember(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    answers: Mapping[str, Any],
    error: Any,
) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    err = None if error in (None, "") else str(error)
    for qid, block in questions.items():
        qtype = str(block.get("type") or "") if isinstance(block, Mapping) else ""
        if qtype == "choice":
            order = _order_for(str(qid), block if isinstance(block, Mapping) else {})
            value: Any = _choice_of(answers.get(qid), order)
        elif qtype == "noul":
            value = _noul_of(answers.get(qid))
        else:
            value = _score_of(answers.get(qid))
        try:
            append_outcome(
                str(qid),
                value,
                logged,
                error=None if value is not None else err,
            )
        except Exception:
            return


def _question_blob(qid: str, spec: Mapping[str, Any]) -> str:
    parts = [str(qid), str(spec.get("instructions") or "")]
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        for key, value in criteria.items():
            parts.append(str(key))
            parts.append(str(value))
    elif isinstance(criteria, (list, tuple)) and not isinstance(criteria, (str, bytes)):
        parts.extend(str(item) for item in criteria)
    return " ".join(parts)


def _asks_limit(qid: str, spec: Mapping[str, Any]) -> bool:
    """Floor and baseline are not a question. Only Noul, Choice, or Score are asked."""

    if str(spec.get("type") or "") not in {"noul", "choice", "score"}:
        return True
    blob = _question_blob(qid, spec).lower()
    if "floor" in blob or "baseline" in blob:
        return True
    compact = blob.replace(",", "").replace("_", "")
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe and probe in compact:
            return True
    return False


def _askable(questions: Mapping[str, Any]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    for qid, spec in questions.items():
        if isinstance(spec, Mapping) and not _asks_limit(str(qid), spec):
            pack[str(qid)] = dict(spec)
    return pack


def evaluate_pack(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One System One evaluate. Empty and error leave the answers unset."""

    pack = _askable(questions)
    if not pack:
        return {
            "ok": False,
            "skipped": "no_questions",
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "merge_sleeve": False,
        }
    cleaned = _scrub(dict(state))
    posted: dict[str, Any] = cleaned if isinstance(cleaned, dict) else {}
    _attach_priors(posted, pack)
    posted["model"] = MODEL
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            posted,
            questions=pack,
            merge_sleeve=False,
            model=MODEL,
            timeout_s=timeout_s,
        ) or {}
    except Exception as exc:  # noqa: BLE001 — fire-path must never raise
        receipt = {
            "ok": False,
            "skipped": type(exc).__name__,
            "model": MODEL,
            "answers": {},
        }
    out = dict(receipt) if isinstance(receipt, Mapping) else {"ok": False, "answers": {}}
    answers = out.get("answers") if out.get("ok") is True else None
    out["answers"] = dict(answers) if isinstance(answers, Mapping) else {}
    if not out["answers"]:
        out["ok"] = False
    out.setdefault("kind", KIND_READ)
    out["model"] = out.get("model") or MODEL
    out["merge_sleeve"] = False
    error = out.get("error") or out.get("skipped")
    if not out["answers"]:
        error = error or "empty"
    _remember(posted, pack, out["answers"], None if out["answers"] else error)
    return out


def fanout_gold_sleeve(
    state: dict[str, Any],
    *,
    sleeve: str,
    symbol: str = "XAUUSD",
    side: str = "",
    branch: str = "fire",
    evaluate_jev: bool = True,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One System One read. Include-depth and this sleeve travel together."""

    packs = intent_packs(sleeve, symbol=symbol, side=side, branch=branch)
    questions: dict[str, Any] = {}
    questions.update(packs.get("include_depth") or {})
    questions.update(packs.get("decision") or {})
    if not evaluate_jev or not questions:
        return {
            "ok": False,
            "skipped": "evaluate_jev_false" if not evaluate_jev else "no_questions",
            "answers": {},
            "n_calls": 0,
            "kind": KIND_READ,
            "merge_sleeve": False,
            "model": MODEL,
        }
    receipt = evaluate_pack(dict(state), questions, timeout_s=timeout_s)
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), Mapping) else {}
    ok = receipt.get("ok") is True and bool(answers)
    return {
        "ok": ok,
        "skipped": None if ok else (receipt.get("skipped") or receipt.get("error") or "empty"),
        "answers": dict(answers),
        "include_receipt": receipt,
        "decision_receipt": receipt,
        "n_calls": 1,
        "kind": KIND_READ,
        "merge_sleeve": False,
        "never_second_llm_hop": True,
        "model": MODEL,
    }


def _hop_state(
    *,
    sleeve: str,
    symbol: str,
    side: str = "",
    extra: Mapping[str, Any] | None = None,
    raw: Any = None,
) -> dict[str, Any]:
    st = dict(extra or {})
    identity = dict(st.get("identity") or {})
    identity.setdefault("login", CHALLENGE_LOGIN)
    identity.setdefault("ns", CHALLENGE_NS)
    identity.setdefault("sleeve", _norm(sleeve))
    identity.setdefault("symbol", _symbol_key(symbol))
    if side:
        identity.setdefault("side", _norm(side).lower())
    st["identity"] = identity
    st.setdefault("account", CHALLENGE_LOGIN)
    st.setdefault("namespace", CHALLENGE_NS)
    st.setdefault("login", CHALLENGE_LOGIN)
    st.setdefault("occupancy_hold_dead", True)
    st.pop("open_gold_sleeve", None)
    gold = live_gold_positions(raw)
    if gold is not None and len(gold) == 1:
        comment = str(gold[0].get("comment") or "").strip()
        if comment:
            st["open_gold_sleeve"] = comment
    cleaned = _scrub(st)
    return cleaned if isinstance(cleaned, dict) else st


def _unset_decision(
    base: dict[str, Any],
    pack: Mapping[str, Any],
    integer_emit: Any,
    *,
    missing_jev: bool,
) -> dict[str, Any]:
    """No return. Fields stay empty. Nothing here writes a stand-in."""

    return {
        **base,
        "hop": "gold_sleeve",
        "disposition": None,
        "choice": None,
        "reason": None,
        "extra_pass": False,
        "size_tilt": None,
        "parameter": None,
        "threshold": None,
        "loop_bound": None,
        "integer_emit": integer_emit,
        "labels": pack.get("labels"),
        "asked": tuple(pack.get("questions") or ()),
        "missing_jev": missing_jev,
        "jev_no_decision": True,
        "gold_vs_sibling": None,
        "probabilities": None,
        "confidence": None,
        "dsp_gold_stance": None,
        "dsp_gold_fresh": None,
        "dsp_gold_geometry": None,
        "xa_gold_timing": None,
        "gold_sleeve_state_sufficient": None,
        "completeness_noul": None,
        "component_exists": None,
        "include_depth": None,
        "thin_state": None,
        "mill_url": None,
        "posted": bool(base.get("live_fanout_ok")),
        "may_send": None,
        "flatten": False,
        "place": False,
        "apply": False,
        "broker_effect": False,
    }


def compose_gold_sleeve(
    *,
    sleeve: str,
    symbol: str = "XAUUSD",
    answers: Mapping[str, Any] | None,
    integer_emit: Any,
    side: str = "",
    evaluate_jev: bool = True,
    timeout_s: float | None = None,
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Code owns workflow. The return owns the decision.

    A low geometry score does not drop an integer emit and does not
    resurrect an empty field. Untagged metals_core never becomes a fire
    here. Sibling yield stands THIS sleeve; it does not extra-PASS a sibling.
    """
    pack = gold_subtree_questions(sleeve, symbol=symbol, side=side)
    base = {
        "schema": "gtos.judgment.gold_sleeve_ifs.v1",
        "kind": KIND_READ,
        "extra_pass": False,
        "flatten": False,
        "place": False,
        "apply": False,
        "persist_weight": None,
        "persist_apply": None,
        "may_send": None,
        "occupancy_hold_dead": True,
        "live_hop": f"gold_sleeve:{_norm(sleeve)}",
        "broker_effect": False,
        "model": MODEL,
    }
    if not pack["ask"]:
        return {
            **base,
            "disposition": pack["reason"],
            "reason": pack["reason"],
            "choice": None,
            "extra_pass": False,
            "size_tilt": None,
            "parameter": None,
            "threshold": None,
            "loop_bound": None,
            "integer_emit": integer_emit,
            "labels": pack["labels"],
            "asked": (),
            "missing_jev": False,
            "jev_no_decision": False,
            "may_send": None,
            "flatten": False,
            "place": False,
            "apply": False,
        }
    live_state = _hop_state(sleeve=sleeve, symbol=symbol, side=side, extra=state)
    live_state.pop("never_flatten_tickets", None)
    live_state.pop("open_gold_ticket", None)
    card = pack.get("open_ticket_card")
    if isinstance(card, dict):
        live_state.update(card)
        base.update(card)
    if evaluate_jev and _answers_missing(answers):
        fanout = fanout_gold_sleeve(
            live_state,
            sleeve=sleeve,
            symbol=symbol,
            side=side,
            evaluate_jev=True,
            timeout_s=timeout_s,
        )
        answers = fanout.get("answers") or None
        base["live_fanout_ok"] = fanout.get("ok")
        base["live_fanout_skipped"] = fanout.get("skipped")
        base["live_n_calls"] = fanout.get("n_calls")
    if _answers_missing(answers):
        return _unset_decision(base, pack, integer_emit, missing_jev=True)
    asked = pack.get("questions") or {}
    got = answers if isinstance(answers, Mapping) else {}
    sibling_block = got.get("gold_vs_sibling")
    sibling = _choice_of(sibling_block, SIBLING_ORDER)
    stance = None
    if "dsp_gold_stance" in asked:
        stance = _choice_of(got.get("dsp_gold_stance"), STANCE_ORDER)
    sufficient = None
    if "gold_sleeve_state_sufficient" in asked:
        sufficient = _noul_of(got.get("gold_sleeve_state_sufficient"))
    fresh = _noul_of(got.get("dsp_gold_fresh")) if "dsp_gold_fresh" in asked else None
    geometry = _score_of(got.get("dsp_gold_geometry")) if "dsp_gold_geometry" in asked else None
    timing = _score_of(got.get("xa_gold_timing")) if "xa_gold_timing" in asked else None
    size_tilt = _score_of(got.get("gold_size_tilt")) if "gold_size_tilt" in asked else None
    threshold = _score_of(got.get("gold_threshold")) if "gold_threshold" in asked else None
    loop_bound = _score_of(got.get("gold_loop_bound")) if "gold_loop_bound" in asked else None
    include: dict[str, float | None] = {}
    for qid in asked:
        name = str(qid)
        if name.startswith("gold_include_"):
            include[name[len("gold_include_"):]] = _score_of(got.get(qid))
    thin_state = None
    if sufficient is True:
        thin_state = False
    elif sufficient is False:
        thin_state = True
    return {
        **base,
        "kind": "choice" if sibling is not None else KIND_READ,
        "hop": "gold_sleeve",
        "disposition": sibling,
        "choice": sibling,
        "reason": sibling,
        "extra_pass": False,
        "size_tilt": size_tilt,
        "parameter": size_tilt,
        "threshold": threshold,
        "loop_bound": loop_bound,
        "integer_emit": integer_emit,
        "labels": pack["labels"],
        "asked": tuple(asked),
        "missing_jev": False,
        "jev_no_decision": sibling is None,
        "gold_vs_sibling": sibling,
        "probabilities": _probabilities(sibling_block, SIBLING_ORDER),
        "confidence": _confidence(sibling_block),
        "dsp_gold_stance": stance,
        "dsp_gold_fresh": fresh,
        "dsp_gold_geometry": geometry,
        "xa_gold_timing": timing,
        "gold_sleeve_state_sufficient": sufficient,
        "completeness_noul": sufficient,
        "component_exists": sufficient,
        "include_depth": include or None,
        "thin_state": thin_state,
        "mill_url": None,
        "posted": bool(base.get("live_fanout_ok")),
        "may_send": (
            True if sibling == "keep_this" else (False if sibling == "yield_sibling" else None)
        ),
        "flatten": False,
        "place": False,
        "apply": False,
        "broker_effect": False,
    }


def decide_gold_sleeve_live(
    *,
    sleeve: str | None = None,
    symbol: str = "XAUUSD",
    side: str = "",
    integer_emit: Any = None,
    state: Mapping[str, Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """THIS gold sleeve vs sibling. Does not flatten 294215389. A missing score stays unset."""
    return compose_gold_sleeve(
        sleeve=_norm(sleeve),
        symbol=symbol,
        answers=None,
        integer_emit=integer_emit,
        side=side,
        evaluate_jev=True,
        timeout_s=timeout_s,
        state=state,
    )


def for_send_choke(
    state: Mapping[str, Any] | None = None,
    *,
    intent: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Gold sleeve vs sibling. This choke does not send and does not flatten."""
    del intent, environ
    st = dict(state or {})
    identity = st.get("identity") if isinstance(st.get("identity"), Mapping) else {}
    symbol = _norm(st.get("symbol") or st.get("instrument") or identity.get("symbol"))
    sleeve = _norm(st.get("sleeve") or identity.get("sleeve"))
    row = decide_gold_sleeve_live(
        sleeve=sleeve, symbol=symbol, state=st, timeout_s=timeout_s
    )
    row["hop"] = "gold_sleeve"
    row["extra_pass"] = False
    row["place"] = False
    row["apply"] = False
    row["flatten"] = False
    choice = row.get("choice")
    if choice == "keep_this":
        row["may_send"] = True
        row["blocks_send"] = False
    elif choice == "yield_sibling":
        row["may_send"] = False
        row["blocks_send"] = True
    else:
        row["may_send"] = None
        row["blocks_send"] = None
    row["persist_apply"] = row.get("parameter")
    row["persist_weight"] = row.get("parameter")
    row["mill_url"] = None
    row["broker_effect"] = False
    return row

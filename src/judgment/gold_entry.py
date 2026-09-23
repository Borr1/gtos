"""Gold entry geometries as a hierarchical TypeSafe question tree.

One piece. One ``jev_client.evaluate`` for this state: model ``jev-1.13.0``,
POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``. Questions
are only Noul, Choice, or Score. The choice, each include-depth score, the
quality score, and each geometry parameter are the value that call returns.
Prior outcomes are attached on the ask, and the return is stored for the
next ask. An empty answer, a tie, a missing score, or an error leaves that
field unset and does not restore a constant. A score may sit between levels.
Floor and baseline are not a question.

Nested labels and include-depth stay on this family's chunks. This is not a
linear keep/drop of the catalog. Code still names which emitter fired and
the zone facts. This module does not send an order.

Pin model ``jev-1.13.0``. Challenge book ``0``.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.gold_entry.v1"
_FIRE_ORDER = ("fire", "abstain", "hard_refuse")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LEVEL_KEYS = frozenset({
    "entry",
    "stop",
    "target",
    "stop_dist",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "atr14",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
})
_SKIP_WALK = frozenset({
    "account",
    "books",
    "peer_books",
    "bars",
    "candles",
    "prior_outcomes",
})
_PARAMETER_QUESTIONS = (
    ("entry_stop_parameter", "stop"),
    ("entry_target_parameter", "target"),
    ("entry_hold_parameter", "hold"),
)

# History only when jev_questions cannot be imported. Not copied back into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

INCLUDE_DEPTH_LEVELS = ("hide", "short", "long", "full")
INCLUDE_DEPTH_CRITERIA = [
    "Hide this chunk — not needed for this fire's query",
    "Short summary of the named fields in this chunk",
    "Longer summary of the named fields in this chunk",
    "Include the whole named chunk",
]

# First hop of the entry tree. Leaves are named emitters, not a 48-way catalog.
ENTRY_FAMILIES: tuple[str, ...] = (
    "sweep_reclaim",
    "ob_retest",
    "fvg_fill",
    "breaker",
    "displacement_continuation",
    "session_open",
    "news_fade",
)

# Named emitters that actually exist in this repository. Empty tuple = no
# generator (honest: news_fade is a calendar window, not an origin family).
FAMILY_EMITTERS: dict[str, tuple[str, ...]] = {
    "sweep_reclaim": (
        "liquidity_sweep_reclaim",
        "asia_pdl_fade",
        "liq_asia_up_low_metal",
        "structural_retest_swp",
    ),
    "ob_retest": (
        "current_ob_retest",
        "metals_ob_micro",
        "structural_retest_ob",
        "fb_ob_retest_0p25d_1p5d",
    ),
    "fvg_fill": (
        "current_fvg_fill",
        "metals_core",
        "metals_softband",
        "structural_retest_fvg",
    ),
    "breaker": (
        "current_breaker_re_entry",
        "structural_retest_brk",
        "cq_breaker_inverted_5d_0p25d",
    ),
    "displacement_continuation": (
        "displacement_continuation",
        "structural_retest_disp",
    ),
    "session_open": (
        "session_open_range_break",
        "metal_session_reversion",
    ),
    "news_fade": (),
}

# Query-aware chunks. Only THIS family's used chunks enter the question set.
FAMILY_CHUNKS: dict[str, tuple[str, ...]] = {
    "sweep_reclaim": ("wick", "level", "session"),
    "ob_retest": ("zone", "impulse", "vol"),
    "fvg_fill": ("gap", "freshness", "vol"),
    "breaker": ("zone", "flip"),
    "displacement_continuation": ("range", "body"),
    "session_open": ("open_range", "session"),
    "news_fade": ("calendar", "window"),
}

# Emitter names. Stop, target, and hold are the parameter scores on the ask.
FAMILY_GEOMETRY: dict[str, dict[str, Any]] = {
    "sweep_reclaim": {
        "broad_origin": {
            "emitter": "liquidity_sweep_reclaim",
            "path": "src/components/broader_origin_generators.py",
        },
        "asia_pdl_fade": {
            "emitter": "asia_pdl_fade",
            "path": "src/components/ultimate_book/sleeves/asia_pdl_fade.py",
        },
        "liq_asia_up_low_metal": {
            "emitter": "liq_asia_up_low_metal",
            "path": "src/components/ultimate_book/sleeves/liq_asia_up_low_metal.py",
        },
        "structural_retest_swp": {
            "emitter": "structural_retest",
            "path": "src/components/ultimate_book/sleeves/structural_retest.py",
        },
    },
    "ob_retest": {
        "current_ob_retest": {
            "emitter": "current_ob_retest",
            "path": "src/components/broader_origin_generators.py",
        },
        "metals_ob_micro": {
            "emitter": "metals_ob_micro",
            "path": "src/components/ultimate_book/sleeves/metals_ob_micro.py",
        },
        "fb_transform": {
            "emitter": "fb_current_ob_retest_as_declared_target_1p5d_stop_0p25d_v1",
            "path": "src/research_infra/current_ob_retest_geometry_candidate.py",
        },
    },
    "fvg_fill": {
        "current_fvg_fill": {
            "emitter": "current_fvg_fill",
            "path": "src/components/broader_origin_generators.py",
        },
        "metals_fvg_retest": {
            "emitter": "metals_core / metals_softband",
            "path": "src/components/ultimate_book/sleeves/metals.py",
        },
    },
    "breaker": {
        "current_breaker_re_entry": {
            "emitter": "current_breaker_re_entry",
            "path": "src/components/broader_origin_generators.py",
        },
        "cq_transform": {
            "emitter": "cq_current_breaker_inverted_target_5d_stop_0p25d_v1",
            "path": "src/components/current_breaker_re_entry_repair.py",
        },
    },
    "displacement_continuation": {
        "broad_origin": {
            "emitter": "displacement_continuation",
            "path": "src/components/broader_origin_generators.py",
        },
    },
    "session_open": {
        "session_open_range_break": {
            "emitter": "session_open_range_break",
            "path": "src/components/broader_origin_generators.py",
        },
        "metal_session_reversion": {
            "emitter": "metal_session_reversion",
            "path": "src/components/ultimate_book/sleeves/metal_session_reversion.py",
        },
    },
    "news_fade": {
        "generator": None,
        "honest": "No origin_family or sleeve named news_fade exists in this repository.",
    },
}

INTEGER_FACTS: tuple[str, ...] = (
    "origin_family",
    "framework",
    "sleeve",
    "zone_low",
    "zone_high",
    "atr14",
    "stop_buffer_atr",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "poi_filled",
    "poi_invalidated",
    "ob_mitigated",
    "breaker_is_retested",
    "touch_count",
    "first_of_day_count",
    "or_bar_count",
    "bars_since_session_open",
    "session_open_range_width_atr",
    "w7_pre_block_minutes",
    "w7_post_block_minutes",
    "f5_pre_block_minutes",
    "f5_post_block_minutes",
    "news_spine_empty",
    "ac60_value",
    "vol_ratio_value",
    "same_bar_fvg_presence",
    "on_surface_membership",
    "warmup_bar_count",
    "atr_nonpositive",
    "named_hard_off",
    "token_digest_match",
    "two_stop_count",
    "prop_wall",
    "operator_flatten_flag",
)

_SNIPPETS: dict[str, str] = {
    "sweep_reclaim": "wick through a named level then close back; stop beyond the wick",
    "ob_retest": "retest of an unmitigated order-block zone; stop beyond the far side",
    "fvg_fill": "retest of an unfilled FVG; stop beyond the gap far side",
    "breaker": "re-entry at an unretested breaker zone; stop beyond the far side",
    "displacement_continuation": "impulse bar (range+body in ATR) continues; stop beyond the bar",
    "session_open": "first close beyond the named session open-range, or NY-anchor fade",
    "news_fade": "no emitter — named HIGH inside the code window is a fact, fade quality is Score",
}

_EMITTER_TO_FAMILY: dict[str, str] = {}
for _fam, _ems in FAMILY_EMITTERS.items():
    for _em in _ems:
        _EMITTER_TO_FAMILY[_em] = _fam
_EMITTER_TO_FAMILY.update(
    {
        "liquidity_sweep_reclaim": "sweep_reclaim",
        "asia_pdl_fade": "sweep_reclaim",
        "liq_asia_up_low_metal": "sweep_reclaim",
        "current_ob_retest": "ob_retest",
        "metals_ob_micro": "ob_retest",
        "current_fvg_fill": "fvg_fill",
        "metals_core": "fvg_fill",
        "metals_softband": "fvg_fill",
        "current_breaker_re_entry": "breaker",
        "displacement_continuation": "displacement_continuation",
        "session_open_range_break": "session_open",
        "metal_session_reversion": "session_open",
        "ob_retest": "ob_retest",
        "fvg_fill": "fvg_fill",
        "breaker_re_entry": "breaker",
    }
)

_QUALITY_IDS: dict[str, str] = {
    "sweep_reclaim": "sweep_reclaim_quality",
    "ob_retest": "ob_retest_quality",
    "fvg_fill": "fvg_fill_quality",
    "breaker": "breaker_quality",
    "displacement_continuation": "disp_quality",
    "session_open": "session_or_quality",
    "news_fade": "news_fade_quality",
}

_QUALITY_INSTRUCTIONS: dict[str, str] = {
    "sweep_reclaim": (
        "Given named wick depth vs ATR, close relative to the swept PDH/PDL/"
        "prior-20 level, and identity.side, is this reclaim holding the level "
        "as a range? First-of-day is a count on the card. "
        "The score you return may sit between the levels. "
        "An empty score leaves it unset."
    ),
    "ob_retest": (
        "Given named OB zone, distance_to_midpoint_atr, touch_count as a range, "
        "and named vol, does this retest fit the tape? Mitigated is an integer "
        "(already denied). ac60 is an integer fact, not a line this score redraws."
    ),
    "fvg_fill": (
        "Given named FVG gap, freshness on the card, and named vol, "
        "does this fill/retest fit the tape? Filled/invalidated are integers "
        "(already denied). ac60 is an integer fact, not a line this score redraws."
    ),
    "breaker": (
        "Given named breaker zone, original_ob_direction vs repaired side, and "
        "named vol, does this re-entry fit the tape? is_retested is a fact on the card. "
        "The score you return is the live geometry. "
        "An empty score leaves it unset."
    ),
    "displacement_continuation": (
        "Given range/ATR and body/ATR as ranges, does this impulse still fit "
        "named vol? The stop and the target are the parameter scores on this "
        "same ask. Pair with geometry_vs_tape in the same request."
    ),
    "session_open": (
        "Given session_open_range_width_atr and bars_since_session_open as "
        "ranges, is this the sleeve's clean first-break / NY-anchor fade, or "
        "just 'a session bar'? First-break-of-day is a count. UTC clock stays "
        "a fact. Static session buckets are not this score."
    ),
    "news_fade": (
        "Given a named HIGH in news.events and the minutes on this card, is a fade "
        "of the print a range on this bar? An empty spine is a fact, not a filled "
        "answer. An empty score leaves it unset."
    ),
}

_QUALITY_CRITERIA: dict[str, list[str]] = {
    "sweep_reclaim": [
        "No reclaim / still through the opposing level",
        "Ordinary wick-and-close-back",
        "Reclaim holding the named supporting level",
    ],
    "ob_retest": [
        "Zone does not fit named vol / stop dies on the next bars",
        "Ordinary OB retest",
        "Retest holding the named OB with stop/target fit",
    ],
    "fvg_fill": [
        "Gap does not fit named vol / stale or fighting flow",
        "Ordinary FVG retest",
        "Fresh named FVG with stop/target fit",
    ],
    "breaker": [
        "Zone does not fit named vol / flip fights named flow",
        "Ordinary breaker re-entry",
        "Unretested named breaker with stop/target fit",
    ],
    "displacement_continuation": [
        "Impulse bar, stop likely dies on the next bars",
        "Ordinary displacement",
        "Impulse fits named vol; continuation with the side",
    ],
    "session_open": [
        "Wrong hour / OR too wide vs ATR / chase of a spent break",
        "Ordinary session-open geometry",
        "Clean first-break or NY-anchor fade for this sleeve",
    ],
    "news_fade": [
        "Named HIGH is in the hard window and a fade would be a restart chase",
        "Ordinary proximity; size-tilt not a fire",
        "Named print already in, fade geometry fits named vol",
    ],
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _identity(state: Mapping[str, Any]) -> dict[str, Any]:
    ident = state.get("identity")
    return dict(ident) if isinstance(ident, Mapping) else {}


def family_node_for(
    *,
    origin_family: str = "",
    sleeve: str = "",
    framework: str = "",
    family: str = "",
) -> str:
    """First hop of the entry tree. Code routes; this names the node."""
    explicit = _norm(family)
    if explicit in ENTRY_FAMILIES:
        return explicit
    for raw in (origin_family, framework, sleeve):
        key = _norm(raw)
        if key in ENTRY_FAMILIES:
            return key
        if key in _EMITTER_TO_FAMILY:
            return _EMITTER_TO_FAMILY[key]
        if key.startswith("dsp_"):
            return "unlisted"
    if _norm(sleeve).startswith("dsp_"):
        return "unlisted"
    return "unlisted"


def used_chunks(family: str) -> tuple[str, ...]:
    """Query-aware chunks for THIS family. Not the seven-family catalog."""
    return FAMILY_CHUNKS.get(_norm(family), ())


def directional_snippet(family: str) -> str:
    """Two-layer catalog: a short line so a model can *suggest* the family exists."""
    return _SNIPPETS.get(_norm(family), "named gold entry geometry")


def emitters_for(family: str) -> tuple[str, ...]:
    return FAMILY_EMITTERS.get(_norm(family), ())


def hierarchical_labels(state: Mapping[str, Any]) -> dict[str, str]:
    """Nested labels for log(n) tree search. Not a flat transcript."""
    ident = _identity(state)
    sleeve = str(ident.get("sleeve") or "")
    origin = str(ident.get("origin_organism") or ident.get("origin") or "")
    framework = str(ident.get("framework") or ident.get("current_framework") or "")
    origin_family = str(
        ident.get("origin_family")
        or ident.get("family")
        or state.get("origin_family")
        or ""
    )
    family = family_node_for(
        origin_family=origin_family,
        sleeve=sleeve,
        framework=framework,
        family=str(ident.get("entry_family") or ""),
    )
    symbol = str(ident.get("symbol") or "XAUUSD")
    side = str(ident.get("side") or "")
    as_of = ""
    clock = state.get("clock")
    if isinstance(clock, Mapping):
        as_of = str(clock.get("as_of_utc") or "")
    ticket = str(ident.get("candidate_id") or ident.get("ticket") or "")
    day = str(ident.get("decision_day") or "")
    return {
        "book": str(CHALLENGE_LOGIN),
        "ns": str(CHALLENGE_NS),
        "magic": str(CHALLENGE_MAGIC),
        "origin": origin or "historical_lab",
        "entry_family": family,
        "sleeve": sleeve,
        "emitter": origin_family or framework or sleeve,
        "symbol": symbol,
        "side": side,
        "as_of_utc": as_of,
        "decision_day": day,
        "ticket": ticket,
        "subgoal": f"entry:{family}:{sleeve or origin_family or framework or 'none'}:{symbol}:{side}",
        "model": MODEL,
    }


def ignore_if(family: str, state: Mapping[str, Any]) -> str | None:
    """Fact label for a thin card. It does not skip the ask and does not name a score."""

    fam = _norm(family)
    news = state.get("news") if isinstance(state.get("news"), Mapping) else {}
    levels = state.get("levels") if isinstance(state.get("levels"), Mapping) else {}
    geometry = state.get("geometry") if isinstance(state.get("geometry"), Mapping) else {}
    sessions = state.get("sessions") if isinstance(state.get("sessions"), Mapping) else {}
    if fam == "news_fade":
        if news.get("spine_empty") is True or news.get("source") == "unassembled":
            return "news.spine_empty"
        return None
    if fam in {"sweep_reclaim", "ob_retest", "fvg_fill", "breaker"}:
        if levels.get("source") == "unassembled" and not (
            geometry.get("stop") or geometry.get("stop_dist") or geometry.get("entry")
        ):
            return "levels.source==unassembled and geometry missing"
    if fam == "session_open" and sessions.get("source") == "unassembled":
        return "sessions.source==unassembled"
    if fam == "displacement_continuation" and not (
        geometry.get("trigger_bar_range_atr")
        or geometry.get("stop_atr")
        or geometry.get("stop_dist")
    ):
        return "geometry missing"
    return None


def integer_facts() -> tuple[str, ...]:
    return INTEGER_FACTS


def converted_ifs() -> tuple[dict[str, str], ...]:
    """Cliffs this tree replaces as ranges. Integers stay integers."""
    return (
        {
            "was": "liquidity_sweep_reclaim emit on wick+close (binary)",
            "now": "sweep_reclaim_quality Score on named wick/level",
            "still_integer": "prior-20 high/low, wick beyond, close back",
        },
        {
            "was": "asia_pdl_fade / liq_asia fire or None",
            "now": "same Score; first-of-day and Asia hour stay counts/clock",
            "still_integer": "server hour, PDL/PDH, pierce depth, first-of-day",
        },
        {
            "was": "current_ob_retest admit_poi binary; metals_ob_micro ac60 line",
            "now": "ob_retest_quality Score; ac60 on the card is a fact",
            "still_integer": "mitigated, zone math, same-bar FVG presence, vol-gate ATR ratio",
        },
        {
            "was": "current_fvg_fill filled/invalidated continue; metals ac60 line",
            "now": "fvg_fill_quality Score; freshness and ac60 on the card are facts",
            "still_integer": "filled, invalidated, gap, zone midpoint",
        },
        {
            "was": "current_breaker is_retested continue",
            "now": "breaker_quality Score; is_retested stays an integer deny",
            "still_integer": "is_retested, zone math, CQ transform enabled bit",
        },
        {
            "was": "displacement_continuation if range and body cleared a fixed ATR line",
            "now": "disp_quality Score on those ratios as ranges",
            "still_integer": "range, body, ATR, side from close vs open",
        },
        {
            "was": "session_open_range_break first close beyond OR",
            "now": "session_or_quality Score; first-break count stays integer",
            "still_integer": "OR high/low, session name, previous_break_seen",
        },
        {
            "was": "news_filter.should_skip binary; no fade generator",
            "now": "news_fade_quality Score + news_fade_present Noul; spine_empty stays a fact",
            "still_integer": "impact, currency, minutes on the card",
        },
    )


def _blocked(text: str) -> bool:
    low = str(text).lower()
    if "floor" in low or "baseline" in low:
        return True
    compact = low.replace(",", "").replace("_", "").replace(" ", "")
    return "90000" in compact or "110000" in compact or "90k" in compact or "110k" in compact


def _limit_key(key: str) -> bool:
    low = str(key).lower()
    return "floor" in low or "baseline" in low


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


def _routed_family(state: Mapping[str, Any], family: str | None = None) -> str:
    ident = _identity(state)
    return family_node_for(
        origin_family=str(ident.get("origin_family") or state.get("origin_family") or ""),
        sleeve=str(ident.get("sleeve") or ""),
        framework=str(ident.get("framework") or ident.get("current_framework") or ""),
        family=str(family or ident.get("entry_family") or ""),
    )


def _parameter_criteria(state: Mapping[str, Any]) -> list[str]:
    """Levels already on this state. The catalog's old numbers are not levels."""

    found: list[float] = []

    def walk(key: str, value: Any, seen: set[int] | None = None) -> None:
        if _limit_key(key):
            return
        trail = seen if seen is not None else set()
        if isinstance(value, Mapping):
            ident = id(value)
            if ident in trail:
                return
            trail.add(ident)
            for child_key, child in value.items():
                name = str(child_key)
                if name.lower() in _SKIP_WALK or _limit_key(name):
                    continue
                walk(name, child, trail)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            return
        if key.lower() not in _LEVEL_KEYS:
            return
        number = _finite(value)
        if number is None:
            return
        rendered = format(number, ".10g")
        if _blocked(rendered):
            return
        found.append(number)

    for key, value in dict(state or {}).items():
        name = str(key)
        if name.lower() in _SKIP_WALK or _limit_key(name):
            continue
        walk(name, value)
    levels = [format(number, ".10g") for number in sorted(set(found))]
    return list(_BETWEEN) + levels


def _score(
    *,
    qid: str,
    instructions: str,
    criteria: list[str],
    ignore: str | None = None,
) -> dict[str, Any] | None:
    """Include-depth and quality stay an order. A price uses the card. A hold with no unit stays off the post."""

    if _blocked(instructions) or (ignore is not None and _blocked(ignore)):
        return None
    name = str(qid)
    words = None
    if name.startswith("include_") or name.endswith("_quality"):
        words = [str(item) for item in criteria if str(item) and not _blocked(str(item))]
        if len(words) < 2:
            return None
    row = _pending_score(name, instructions, words)
    if not isinstance(row, dict):
        return None
    if ignore:
        row["ignore_if"] = ignore
    return row



def _noul(
    *,
    instructions: str,
    ignore: str | None = None,
    criteria: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    if _blocked(instructions) or (ignore is not None and _blocked(ignore)):
        return None
    sides = criteria or {
        "true": "Named object is complete enough to judge this fire",
        "false": "A required named block is missing or unknown",
    }
    kept = {
        str(key): str(text)
        for key, text in sides.items()
        if not _blocked(str(key)) and not _blocked(str(text))
    }
    if "true" not in kept or "false" not in kept:
        return None
    row: dict[str, Any] = {
        "type": "noul",
        "instructions": instructions,
        "criteria": kept,
    }
    if ignore:
        row["ignore_if"] = ignore
    return row


def _choice(
    *,
    qid: str,
    instructions: str,
    criteria: dict[str, str],
    ignore: str | None = None,
) -> dict[str, Any] | None:
    if _blocked(instructions) or (ignore is not None and _blocked(ignore)):
        return None
    kept = {
        str(key): str(text)
        for key, text in criteria.items()
        if not _blocked(str(key)) and not _blocked(str(text))
    }
    if not kept:
        return None
    row: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": kept,
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, kept)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            row = dict(block)
    except Exception:
        pass
    row["type"] = "choice"
    row["instructions"] = instructions
    row["criteria"] = kept
    if ignore:
        row["ignore_if"] = ignore
    else:
        row.pop("ignore_if", None)
    return row


def _put(questions: dict[str, Any], key: str, row: dict[str, Any] | None) -> None:
    if row is not None:
        questions[key] = row


def entry_subtree_questions(
    state: Mapping[str, Any],
    *,
    standalone: bool = True,
    family: str | None = None,
) -> dict[str, Any]:
    """This family's subtree for the one POST. Not the seven-family catalog.

    ``standalone=False`` reuses gold ``state_sufficient``. ``standalone=True``
    adds ``entry_state_sufficient``. A thin card stays on the ask. It does not
    drop the fire, the parameters, or the broker noul.
    """
    fam = _routed_family(state, family)
    named = fam if fam in ENTRY_FAMILIES else "the entry"
    questions: dict[str, Any] = {}
    if standalone:
        _put(questions, "entry_state_sufficient", _noul(
            instructions=(
                "Do completeness.missing_fields and the named geometry/level/"
                "session/news blocks contain enough to judge this ENTRY fire "
                "as-of clock.as_of_utc? Unknown family_class is a fact. "
                "An empty news spine is a fact, not a filled answer."
            )
        ))
    _put(questions, "entry_broker_effect", _noul(
        instructions=(
            "Is a broker effect open on this entry state? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. Do not send an order."
        ),
        criteria={
            "true": "A broker effect is open on this state.",
            "false": "A broker effect is not open on this state.",
        },
    ))
    if fam in ENTRY_FAMILIES:
        for chunk in used_chunks(fam):
            _put(questions, f"include_{chunk}", _score(
                qid=f"include_{chunk}",
                instructions=(
                    f"How much of the named `{chunk}` chunk does THIS {named} fire "
                    "need? hide / short / long / full. Not a yes/no keep of "
                    "a different family."
                ),
                criteria=list(INCLUDE_DEPTH_CRITERIA),
            ))

        quality_id = _QUALITY_IDS[fam]
        _put(questions, quality_id, _score(
            qid=quality_id,
            instructions=_QUALITY_INSTRUCTIONS[fam],
            criteria=list(_QUALITY_CRITERIA[fam]),
        ))

        if fam == "news_fade":
            _put(questions, "news_fade_present", _noul(
                instructions=(
                    "Is a named HIGH in news.events on this as-of? "
                    "The minutes on the card are a fact. "
                    "An empty spine is a fact, not a filled answer. "
                    "The noul you return is that presence."
                ),
                criteria={
                    "true": "A named HIGH is on this as-of.",
                    "false": "No named HIGH is on this as-of.",
                },
            ))

        emitters = {
            name: f"{name} is the emitter on this state."
            for name in emitters_for(fam)
            if not _blocked(name)
        }
        if emitters:
            _put(questions, "entry_emitter", _choice(
                qid="entry_emitter",
                instructions=(
                    f"Which emitter is this {named} geometry on this state? "
                    "The option you return is that emitter. "
                    "An empty answer or a tie is not an emitter. "
                    "Do not send an order."
                ),
                criteria=emitters,
            ))
            _put(questions, "entry_emitter_present", _noul(
                instructions=(
                    f"Does that {named} emitter exist on this state? "
                    "An empty answer leaves it unset. Do not send an order."
                ),
                criteria={
                    "true": "That emitter exists on this state.",
                    "false": "That emitter does not exist on this state.",
                },
            ))

    levels = _parameter_criteria(state)
    for qid, noun in _PARAMETER_QUESTIONS:
        _put(questions, qid, _score(
            qid=qid,
            instructions=(
                f"The score you return is the {noun} parameter for this {named} geometry. "
                "It may sit between the levels on this state. "
                "An empty score leaves it unset. Do not send an order."
            ),
            criteria=levels,
        ))

    _put(questions, "entry_fire", _choice(
        qid="entry_fire",
        instructions=(
            f"Given the facts on this {named} card, is this a fire? "
            "The choice you return is that answer. "
            "An empty answer or a tie leaves it unset. Do not send an order."
        ),
        criteria={
            "fire": "The facts on this card support a fire.",
            "abstain": "The facts on this card do not support a fire.",
            "hard_refuse": "The facts on this card refuse the fire.",
        },
    ))
    return questions


def noul_question_ids(questions: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        key
        for key, spec in questions.items()
        if isinstance(spec, Mapping) and spec.get("type") == "noul"
    )


def family_has_emitter(family: str) -> bool:
    return bool(emitters_for(family))


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    """Drop limit facts before the ask. A repeated container is a cycle.

    The walk stops on a cycle. No depth cap.
    """

    if seen is None:
        seen = set()
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        number = _finite(value)
        if number is None or _blocked(format(number, ".10g")):
            return None
        return int(value) if isinstance(value, int) and not isinstance(value, bool) else number
    if isinstance(value, str):
        return None if _blocked(value) else value
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item, seen)
            if cleaned is None and item is not None:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        kept: list[Any] = []
        for item in value:
            cleaned = _scrub(item, seen)
            if cleaned is None and item is not None:
                continue
            kept.append(cleaned)
        return kept
    return None


def _scrub_state(state: Mapping[str, Any] | None) -> dict[str, Any]:
    cleaned = _scrub(dict(state or {}))
    payload = cleaned if isinstance(cleaned, dict) else {}
    payload.pop("prior_outcomes", None)
    return payload


def _question_ok(spec: Any) -> bool:
    if not isinstance(spec, Mapping):
        return False
    if str(spec.get("type") or "").lower() not in {"noul", "choice", "score"}:
        return False
    try:
        import json

        blob = json.dumps(spec, default=str)
    except Exception:
        return False
    return not _blocked(blob)


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if not order:
        return None
    probs = _probs(block)
    local = _unique(probs, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(probs) if probs else None, order)
    except Exception:
        picked = local
    if local is None or picked is None:
        return None
    if str(picked) != local or local not in order:
        return None
    return local


def _score_of(block: Any) -> float | None:
    """The score that came back. A tie or a missing score stays unset."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = _probs(block)
    if probs and _unique(probs, tuple(probs)) is None:
        return None
    if "score" in block:
        return _finite(block.get("score"))
    if "value" in block:
        return _finite(block.get("value"))
    return None


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. It is not cut at a line."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _unique(_probs(block), ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: str | None) -> str | None:
    if value is not None:
        return None
    if receipt_error not in (None, ""):
        return str(receipt_error)
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _blank(family: str, error: str | None) -> dict[str, Any]:
    known = family in ENTRY_FAMILIES
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "entry_family": family,
        "state_sufficient": None,
        "emitter": None,
        "emitter_present": None,
        "include_depth": {chunk: None for chunk in (used_chunks(family) if known else ())},
        "quality_id": _QUALITY_IDS.get(family) if known else None,
        "quality": None,
        "entry_fire": None,
        "news_fade_present": None,
        "stop_parameter": None,
        "target_parameter": None,
        "hold_parameter": None,
        "broker_effect": None,
        "error": error,
    }


def _fill(
    card: dict[str, Any],
    questions: Mapping[str, Any],
    answers: Mapping[str, Any],
    receipt_error: str | None,
    family: str,
) -> list[tuple[str, Any, str | None]]:
    rows: list[tuple[str, Any, str | None]] = []

    def keep(qid: str, value: Any, order: tuple[str, ...]) -> None:
        rows.append((qid, value, _miss(answers.get(qid), value, order, receipt_error)))

    if "entry_state_sufficient" in questions:
        value = _noul_of(answers.get("entry_state_sufficient"))
        card["state_sufficient"] = value
        keep("entry_state_sufficient", value, ("true", "false"))
    if "entry_emitter" in questions:
        order = tuple(emitters_for(family))
        value = _choice_of(answers.get("entry_emitter"), order)
        card["emitter"] = value
        keep("entry_emitter", value, order)
    if "entry_emitter_present" in questions:
        value = _noul_of(answers.get("entry_emitter_present"))
        card["emitter_present"] = value
        keep("entry_emitter_present", value, ("true", "false"))
    depths = card.get("include_depth")
    if not isinstance(depths, dict):
        depths = {}
        card["include_depth"] = depths
    for chunk in used_chunks(family) if family in ENTRY_FAMILIES else ():
        qid = f"include_{chunk}"
        if qid not in questions:
            continue
        raw = answers.get(qid)
        value = _snap_if_ordinal(qid, raw, _score_of(raw))
        depths[chunk] = value
        keep(qid, value, ())
    quality_id = _QUALITY_IDS.get(family)
    if quality_id and quality_id in questions:
        raw = answers.get(quality_id)
        value = _snap_if_ordinal(quality_id, raw, _score_of(raw))
        card["quality_id"] = quality_id
        card["quality"] = value
        keep(quality_id, value, ())
    if "entry_fire" in questions:
        value = _choice_of(answers.get("entry_fire"), _FIRE_ORDER)
        card["entry_fire"] = value
        keep("entry_fire", value, _FIRE_ORDER)
    if "news_fade_present" in questions:
        value = _noul_of(answers.get("news_fade_present"))
        card["news_fade_present"] = value
        keep("news_fade_present", value, ("true", "false"))
    if "entry_stop_parameter" in questions:
        value = _score_of(answers.get("entry_stop_parameter"))
        card["stop_parameter"] = value
        keep("entry_stop_parameter", value, ())
    if "entry_target_parameter" in questions:
        value = _score_of(answers.get("entry_target_parameter"))
        card["target_parameter"] = value
        keep("entry_target_parameter", value, ())
    if "entry_hold_parameter" in questions:
        value = _score_of(answers.get("entry_hold_parameter"))
        card["hold_parameter"] = value
        keep("entry_hold_parameter", value, ())
    if "entry_broker_effect" in questions:
        value = _noul_of(answers.get("entry_broker_effect"))
        card["broker_effect"] = value
        keep("entry_broker_effect", value, ("true", "false"))
    return rows


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({"key": key, "value": value, "error": error})
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _post(
    payload: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate as call
    questions = _anchor_questions(questions, payload)
    receipt = call(payload, questions=dict(questions), merge_sleeve=False)
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict", {}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        error = receipt.get("error") or receipt.get("skipped") or "empty"
    return answers, (str(error) if error else None), receipt


def evaluate_gold_entry(
    state: Mapping[str, Any] | None = None,
    *,
    standalone: bool = True,
    family: str | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One ask. The returns are the decision and the parameters.

    An empty answer, a tie, a missing score, or an error leaves that field
    unset. This hop does not send.
    """

    src = dict(state or {})
    routed = _routed_family(src, family)
    try:
        built = entry_subtree_questions(src, standalone=standalone, family=family)
        questions = {
            key: spec
            for key, spec in built.items()
            if _question_ok(spec)
        }
    except Exception as exc:  # noqa: BLE001 — a failed pack stays unset
        return _blank(routed, type(exc).__name__)
    if not questions:
        return _blank(routed, "empty")
    payload = _scrub_state(src)
    payload["model"] = MODEL
    try:
        payload["labels"] = hierarchical_labels(payload)
    except Exception:
        pass
    payload.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
        payload["prior_outcomes"] = loaded if isinstance(loaded, list) else []
    except Exception:
        payload["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
    try:
        answers, error, receipt = _post(payload, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        card = _blank(routed, type(exc).__name__)
        _remember(payload, _fill(card, questions, {}, type(exc).__name__, routed))
        card["questions"] = list(questions)
        return card
    card = _blank(routed, error if not answers else None)
    rows = _fill(card, questions, answers, error, routed)
    _remember(payload, rows)
    card["model"] = receipt.get("model") or MODEL
    card["questions"] = list(questions)
    card["answers"] = answers
    return card


_BOUND_CARD = None

_SKIP_FACT_KEYS = frozenset({
    "login",
    "magic",
    "model",
    "prior_outcomes",
    "reason_ids",
    "scoped_xau_names",
    "windows",
    "order_send",
    "flatten",
    "namespace",
    "ns",
    "api_url",
    "schema",
    "questions",
    "answers",
    "criteria",
    "instructions",
})
_PRICE_KEYS = frozenset({
    "entry",
    "stop",
    "target",
    "entry_price",
    "stop_loss",
    "take_profit",
    "take_profit_1",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "deal_final",
    "event_stop_now",
    "inv_entry",
    "inv_stop",
})
_PRICE_QIDS = frozenset({
    "inv_entry",
    "inv_stop",
    "entry_stop_parameter",
    "entry_target_parameter",
    "host_named_sl",
})
_WEIGHT_QIDS = frozenset({
    "geometry_vs_tape",
    "session_fitness",
    "level_respect",
    "flow_alignment",
    "persistence",
})
_UNIX_QIDS = frozenset({"gfull_start", "gfull_end", "cutoff_unix"})
_COUNT_LISTS = frozenset({
    "events",
    "rows",
    "candidates",
    "peers",
    "sites",
    "stubs",
    "recipe_rows",
    "recipes",
})
_ORDINAL_EXACT = frozenset({
    "wall_pressure",
    "fill_realism",
    "paper_live_parity",
    "protection_still_earns",
    "session_liquidity",
})


def _bind_card(card):
    global _BOUND_CARD
    if isinstance(card, Mapping):
        _BOUND_CARD = card


def _finite_fact(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _ordinal_words(qid):
    name = str(qid)
    if name == "session_liquidity":
        return ("thin liquidity", "ordinary liquidity", "deep liquidity")
    if name == "include_depth" or name.startswith("include_"):
        return ("hide", "short", "long", "full")
    if name in _ORDINAL_EXACT or name.endswith("_quality"):
        return ("poor", "ordinary", "clean")
    return None


def _qid_unit(qid):
    name = str(qid).lower()
    if _ordinal_words(name):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_QIDS:
        return "price"
    if name.endswith("_s") or "second" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or "percent" in name:
        return "pct"
    if name.endswith("_r") or "spread_r" in name:
        return "r"
    if name in _WEIGHT_QIDS or "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or "_tilt" in name
        or name.endswith("_tilt")
    ):
        return "mult"
    if name in _UNIX_QIDS or name.endswith("_unix"):
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net"):
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or "nth" in name
        or "candidate" in name
        or "occupancy" in name
        or "corr_window" in name
        or name.endswith("_shadow")
        or "shadow" in name
    ):
        return "count"
    return ""


def _key_unit(key):
    name = str(key).lower()
    if name in _SKIP_FACT_KEYS or name.startswith("_"):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_KEYS:
        return "price"
    if name.endswith("_seconds") or name.endswith("_s") or "delta_s" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or name.endswith("_percent") or "percent" in name:
        return "pct"
    if name.endswith("_r") or name in {"spread_r", "locked_r"}:
        return "r"
    if "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or name.endswith("_tilt")
        or name in {"tilt", "shadow_tilt"}
    ):
        return "mult"
    if name.endswith("_unix") or name in {"gfull_start", "gfull_end", "cutoff_unix"}:
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net") or name in {"equity", "balance", "profit", "pnl", "open_pnl", "net"}:
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or name.endswith("_hits")
        or name.endswith("_anchors")
        or "candidate" in name
        or "nth" in name
        or name == "occupancy_world"
    ):
        return "count"
    return ""


def _fact_label(key, used):
    text = "the " + str(key) + " named on this card"
    if text not in used:
        used.add(text)
        return text
    index = 2
    while True:
        alt = "another " + str(key) + " named on this card (" + str(index) + ")"
        if alt not in used:
            used.add(alt)
            return alt
        index += 1


def _walk_facts(value, key, unit, pairs, labels, seen):
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        for child_key, child in value.items():
            if not isinstance(child_key, str) or child_key.lower() in _SKIP_FACT_KEYS:
                continue
            _walk_facts(child, child_key, unit, pairs, labels, seen)
        return
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        if unit == "count" and str(key).lower() in _COUNT_LISTS:
            pairs.append((_fact_label("count of " + str(key), labels), float(len(value))))
        for item in value:
            if isinstance(item, Mapping):
                _walk_facts(item, key, unit, pairs, labels, seen)
        return
    if _key_unit(key) != unit:
        return
    number = _finite_fact(value)
    if number is None:
        return
    pairs.append((_fact_label(key, labels), number))


def _distance_gap(card, pairs, labels):
    left = None
    right = None

    def walk(node, seen):
        nonlocal left, right
        if not isinstance(node, Mapping):
            return
        ident = id(node)
        if ident in seen:
            return
        seen.add(ident)
        if left is None:
            left = _finite_fact(node.get("left"))
        if right is None:
            right = _finite_fact(node.get("right"))
        for child in node.values():
            if isinstance(child, Mapping):
                walk(child, seen)

    if isinstance(card, Mapping):
        walk(card, set())
    if left is None or right is None:
        return
    pairs.append((_fact_label("stop gap", labels), abs(left - right)))


def _anchors_for(unit, card):
    if not unit or not isinstance(card, Mapping):
        return []
    pairs = []
    labels = set()
    if unit == "weight":
        try:
            from .jev_questions import weight_anchors

            for label, number in weight_anchors(card):
                pairs.append((str(label), number))
                labels.add(str(label))
        except Exception:
            pairs = []
            labels = set()
    _walk_facts(card, "", unit, pairs, labels, set())
    if unit == "distance":
        _distance_gap(card, pairs, labels)
    return pairs


def _pending_score(qid, instructions, words=None):
    text = "" if instructions is None else str(instructions)
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return None
        if cleaned is None:
            return None
        if isinstance(cleaned, str):
            text = cleaned
    text = text.strip()
    if not text:
        return None
    for guard_name in ("_limit_key", "_skip_key", "_blocked", "_blocked_text", "_bad_text"):
        guard = globals().get(guard_name)
        if not callable(guard):
            continue
        try:
            if guard(str(qid)) or guard(text):
                return None
        except Exception:
            return None
    row = {"type": "score", "instructions": text}
    if words:
        kept = [str(item).strip() for item in words if str(item).strip()]
        if len(kept) >= 2:
            row["_words"] = kept
    return row


def _anchor_questions(questions, card):
    """Rebuild each Score from this card. Fewer than two levels drops that Score."""

    if not isinstance(questions, Mapping):
        return questions
    _bind_card(card)
    out = {}
    for key, block in questions.items():
        if not isinstance(block, dict) or str(block.get("type") or "") != "score":
            out[key] = block
            continue
        name = str(key)
        words = block.get("_words")
        if not isinstance(words, (list, tuple)):
            words = _ordinal_words(name)
        try:
            if words:
                from .jev_questions import ordinal_question

                built = ordinal_question(name, str(block.get("instructions") or ""), words)
            else:
                from .jev_questions import amount_question

                built = amount_question(
                    name,
                    str(block.get("instructions") or ""),
                    _anchors_for(_qid_unit(name), card),
                )
        except Exception:
            continue
        row = built.get(name) if isinstance(built, dict) else None
        if not isinstance(row, dict) or not row.get("criteria"):
            continue
        if block.get("ignore_if"):
            row = dict(row)
            row["ignore_if"] = block.get("ignore_if")
        out[key] = row
    return out


def _snap_ordinal(block, n_levels):
    try:
        count = int(n_levels)
    except (TypeError, ValueError):
        return None
    if count < 2:
        return None
    try:
        from .jev_questions import ordinal_index

        return ordinal_index(block, count)
    except Exception:
        return None


def _snap_if_ordinal(qid, block, fallback):
    words = _ordinal_words(qid)
    if not words:
        return fallback
    return _snap_ordinal(block, len(words))

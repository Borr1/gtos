"""Challenge generation, filter, and include-flag decisions are one Choice each.

Each question is the sides of that condition. The decision is the
alternative with the unique highest probability. A tie is not a decision.
An empty answer is not a decision. This module never calls order_send
and never labels an unanswered hop. Persist is the returned weight,
or it is absent. An empty answer does not write 0.00. Friends copy
the recorded result. An open ticket is not closed from here.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.judgment.nineteen import DENOMINATOR, write_import_stamp

write_import_stamp()

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.book_engine_choices.v1"

QUESTIONS: dict[str, dict[str, Any]] = {
    "include_clean3": {
        "id": "be_include_clean3",
        "instructions": (
            "Include-flag question for the clean3 sleeve surface. "
            "Pick one option. clean3_out removes that surface only when it "
            "is the single highest probability. clean3_in_the_book keeps it "
            "in generation. An empty answer or a tie does not remove it. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "clean3_in_the_book": "Generate the clean3 surface.",
            "clean3_out": "Leave the clean3 surface out of generation.",
        },
        "out": "clean3_out",
    },
    "include_clean4": {
        "id": "be_include_clean4",
        "instructions": (
            "Include-flag question for the clean4 sleeve surface. "
            "Pick one option. clean4_out removes that surface only when it "
            "is the single highest probability. clean4_in_the_book keeps it "
            "in generation. An empty answer or a tie does not remove it. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "clean4_in_the_book": "Generate the clean4 surface.",
            "clean4_out": "Leave the clean4 surface out of generation.",
        },
        "out": "clean4_out",
    },
    "include_candidate_book": {
        "id": "be_include_candidate_book",
        "instructions": (
            "Include-flag question for the candidate-book surface. "
            "Pick one option. candidate_book_out removes that surface only "
            "when it is the single highest probability. candidate_book_in "
            "keeps the whole candidate book in generation. An empty answer "
            "or a tie does not remove it. Do not close an open ticket."
        ),
        "criteria": {
            "candidate_book_in": "Generate the whole candidate book.",
            "candidate_book_out": "Leave the candidate book out of generation.",
        },
        "out": "candidate_book_out",
    },
    "include_market_expansion": {
        "id": "be_include_market_expansion",
        "instructions": (
            "Include-flag question for the market-expansion surface. "
            "Pick one option. market_expansion_out removes that surface only "
            "when it is the single highest probability. market_expansion_in "
            "keeps the whole expansion market in generation. An empty answer "
            "or a tie does not remove it. Do not close an open ticket."
        ),
        "criteria": {
            "market_expansion_in": "Generate the whole expansion market.",
            "market_expansion_out": "Leave the expansion market out of generation.",
        },
        "out": "market_expansion_out",
    },
    "instrument_spec": {
        "id": "be_instrument_spec",
        "instructions": (
            "Generation question: the broker spec for this symbol. "
            "Pick one option. The slot is skipped only when "
            "instrument_spec_missing is the single highest probability. "
            "instrument_spec_present keeps the slot in generation. "
            "An empty answer or a tie does not skip it. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "instrument_spec_present": "The broker spec for this symbol is loaded.",
            "instrument_spec_missing": "The broker spec for this symbol is missing.",
        },
    },
    "feed_lookback": {
        "id": "be_feed_lookback",
        "instructions": (
            "Generation question: the feed versus the lookback this generator "
            "just named. Pick one option. The slot is skipped only when "
            "feed_short is the single highest probability. "
            "feed_has_the_lookback keeps the slot. An empty answer or a tie "
            "does not skip it. Do not close an open ticket."
        ),
        "criteria": {
            "feed_has_the_lookback": "The feed covers the lookback the generator named.",
            "feed_short": "The feed is short of that lookback.",
        },
    },
    "future_bar": {
        "id": "be_future_bar",
        "instructions": (
            "Generation question: this symbol's bar close is more than thirty "
            "seconds ahead of the clock. Pick one option. The slot is skipped "
            "only when bar_close_ahead_of_clock is the single highest "
            "probability. bar_close_not_ahead keeps the slot. An empty answer "
            "or a tie does not skip it. Do not close an open ticket."
        ),
        "criteria": {
            "bar_close_not_ahead": "This close is the bar to judge.",
            "bar_close_ahead_of_clock": "This close is still ahead of the clock.",
        },
    },
    "stale_bar": {
        "id": "be_stale_bar",
        "instructions": (
            "Generation question: the decision bar is older than two of its "
            "intervals. Pick one option. The slot is skipped only when "
            "restart_chase is the single highest probability. "
            "still_the_close keeps the slot. An empty answer or a tie does "
            "not skip it. Do not close an open ticket."
        ),
        "criteria": {
            "still_the_close": "The order is still this bar's close.",
            "restart_chase": "This is a chase of a price the pattern did not enter.",
        },
    },
    "spread_floor": {
        "id": "be_spread_floor",
        "instructions": (
            "Filter question: the spread-geometry floor produced a reading "
            "for this intent. Pick one option. The intent is refused only "
            "when floor_refuses is the single highest probability. "
            "spread_geometry_is_the_plan keeps the intent. A bug in the floor "
            "is not itself a refusal. An empty answer or a tie does not "
            "refuse it. Do not close an open ticket."
        ),
        "criteria": {
            "spread_geometry_is_the_plan": "The spread-geometry reading is a fact. This intent stays.",
            "floor_refuses": "The spread-geometry floor refuses this intent.",
        },
    },
    "entry_hour": {
        "id": "be_entry_hour",
        "instructions": (
            "Filter question: an entry-hour rule produced a deferral for this "
            "sleeve. Pick one option. The intent is deferred only when "
            "defer_the_hour is the single highest probability. fire_this_hour "
            "emits the intent. An empty answer or a tie does not defer it. "
            "Do not arm a new hour cliff. Do not close an open ticket."
        ),
        "criteria": {
            "fire_this_hour": "This hour is a fact. Emit the intent.",
            "defer_the_hour": "Defer this intent because of the hour.",
        },
    },
    "generation_surface": {
        "id": "be_generation_surface",
        "instructions": (
            "Filter question: this sleeve is outside the admission intersection. "
            "Pick one option. The sleeve is left out of generation only when "
            "off_generation_surface is the single highest probability. "
            "on_generation_surface keeps it. An empty answer or a tie does "
            "not drop it. Do not close an open ticket."
        ),
        "criteria": {
            "on_generation_surface": "This sleeve stays on the generation surface.",
            "off_generation_surface": "This sleeve is off the generation surface.",
        },
    },
    "news_t60": {
        "id": "be_news_t60",
        "instructions": (
            "Filter question: the t60 pass marked this intent outside its "
            "scope. Pick one option. The intent is dropped only when "
            "t60_scope_rejects is the single highest probability. "
            "keep_for_admission keeps it. An empty answer or a tie does not "
            "drop it. Do not close an open ticket."
        ),
        "criteria": {
            "keep_for_admission": "Keep this intent for admission.",
            "t60_scope_rejects": "The t60 scope rejects this intent.",
        },
    },
    "drop_w7": {
        "id": "be_drop_w7",
        "instructions": (
            "Filter question: the W7 symbol drop. Pick one option. Symbols "
            "are dropped only when drop_w7_symbols is the single highest "
            "probability. w7_symbols_stay leaves them in the count. An empty "
            "answer or a tie does not drop them. Do not close an open ticket."
        ),
        "criteria": {
            "w7_symbols_stay": "W7 symbols stay in the filter input.",
            "drop_w7_symbols": "Drop the W7 symbols.",
        },
    },
    "vp_acceptance": {
        "id": "be_vp_acceptance",
        "instructions": (
            "Filter question: the volume-profile acceptance filter. "
            "Pick one option. The filter runs only when vp_acceptance_on is "
            "the single highest probability. vp_acceptance_off leaves the "
            "intents in the count. An empty answer or a tie does not run the "
            "filter. Do not close an open ticket."
        ),
        "criteria": {
            "vp_acceptance_off": "Do not apply the volume-profile acceptance filter.",
            "vp_acceptance_on": "Apply the volume-profile acceptance filter.",
        },
    },
    "metals_confluence": {
        "id": "be_metals_confluence",
        "instructions": (
            "Filter question: the metals confluence filter. Pick one option. "
            "The filter runs only when metals_confluence_on is the single "
            "highest probability. metals_confluence_off leaves the intents. "
            "An empty answer or a tie does not run the filter. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "metals_confluence_off": "Do not apply the metals confluence filter.",
            "metals_confluence_on": "Apply the metals confluence filter.",
        },
    },
    "symbol_damage": {
        "id": "be_symbol_damage",
        "instructions": (
            "Filter question: the symbol-damage filter. Pick one option. "
            "The filter runs only when symbol_damage_on is the single highest "
            "probability. symbol_damage_off leaves the intents. An empty "
            "answer or a tie does not run the filter. Do not close an open ticket."
        ),
        "criteria": {
            "symbol_damage_off": "Do not apply the symbol-damage filter.",
            "symbol_damage_on": "Apply the symbol-damage filter.",
        },
    },
    "last_bar": {
        "id": "be_last_bar",
        "instructions": (
            "Last-bar question: this bar. The card names symbol, sleeve, "
            "open, high, low, close, the range each side, direction when one is "
            "present, bid, ask, bid_from_open, ask_from_open, and the seconds "
            "from this close to the clock. bid_from_open and ask_from_open are "
            "the live quote against the open, the move before the close prints. "
            "They do not pick a side. Pick one option. closed_bar_reaches names "
            "this bar, including a bar whose close has not printed when the live "
            "quote has left the open, only when it is the single highest "
            "probability. use_previous_close names the previous close when this "
            "row is still forming and the live quote has not left the open. "
            "closed_bar_does_not_reach does not hand this bar to a new unit. "
            "An empty answer or a tie does not restore the previous close and "
            "does not invent a direction. Do not close an open ticket."
        ),
        "criteria": {
            "closed_bar_reaches": "This close is the bar the sleeve judges.",
            "use_previous_close": "This row is still forming. The previous close is the bar.",
            "closed_bar_does_not_reach": "This close is not the bar to judge.",
        },
    },
    "unit": {
        "id": "be_unit",
        "instructions": (
            "Unit question: this closed bar reached the sleeve and the sleeve "
            "did not fire. The closed bar is named here: open, high, low, "
            "close, the range each side, symbol, sleeve, direction when one "
            "is present, bid, ask, and the last bar. Pick one option. A limit "
            "unit is produced only when unit_long or unit_short is the single "
            "highest probability. sleeve_stays_out produces no unit. An empty "
            "answer or a tie does not invent a direction and does not restore "
            "a skip. Entry is the close. The stop is that bar's own range on "
            "the chosen side. Do not close an open ticket."
        ),
        "criteria": {
            "unit_long": (
                "This closed bar is a long limit. Entry is the close. "
                "Stop is the range to the low."
            ),
            "unit_short": (
                "This closed bar is a short limit. Entry is the close. "
                "Stop is the range to the high."
            ),
            "sleeve_stays_out": "This closed bar does not become a unit.",
        },
    },
}


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _returned_persist(hop: Mapping[str, Any]) -> float | None:
    """The weight this hop returned. An empty answer does not become 0.00."""

    for key in ("persist_weight", "persist"):
        if key not in hop:
            continue
        number = _finite(hop.get(key))
        if number is not None:
            return number
    return None


def _shown(value: Any) -> str:
    if value is None or value == "":
        return "absent"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".10g")
    return str(value)


_CHOICE_TAIL: dict[tuple[str, str, str], str] = {}
_CHOICE_OFFSET = 0
_CHOICE_PATH: str | None = None
_STATE_MEMO: dict[str, str] = {}


def _state_key(question: str, facts: Mapping[str, Any] | None) -> str:
    """The question and the card. A moving clock is not a different state."""

    card = dict(facts or {})
    card.pop("seconds_from_clock", None)
    return question + "\n" + json.dumps(card, sort_keys=True, default=str)


def _refresh_choice_tail() -> None:
    """Read new lines of the choice record. A partial line stays for the next read."""

    global _CHOICE_OFFSET, _CHOICE_PATH
    path = record_path()
    key = str(path)
    if _CHOICE_PATH != key:
        _CHOICE_PATH = key
        _CHOICE_OFFSET = 0
        _CHOICE_TAIL.clear()
    try:
        size = path.stat().st_size
    except OSError:
        return
    if size < _CHOICE_OFFSET:
        _CHOICE_OFFSET = 0
        _CHOICE_TAIL.clear()
    if size == _CHOICE_OFFSET:
        return
    try:
        with path.open("rb") as handle:
            handle.seek(_CHOICE_OFFSET)
            blob = handle.read()
    except OSError:
        return
    if not blob.endswith(b"\n"):
        cut = blob.rfind(b"\n")
        if cut < 0:
            return
        blob = blob[: cut + 1]
    _CHOICE_OFFSET += len(blob)
    lines = blob.decode("utf-8", errors="replace").splitlines()
    found: dict[tuple[str, str, str], str] = {}
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        choice = row.get("choice")
        if not isinstance(choice, str) or not choice:
            continue
        question = str(row.get("question") or "")
        parts = str(row.get("spot") or "").split("|")
        sleeve = parts[0] if parts else ""
        symbol = parts[1] if len(parts) > 1 else ""
        facts = row.get("facts")
        if isinstance(facts, dict):
            sleeve = str(facts.get("sleeve") or sleeve)
            symbol = str(facts.get("symbol") or symbol)
        if not symbol:
            continue
        bar_iso = parts[2] if len(parts) > 2 else ""
        found[(question, sleeve, symbol)] = f"{choice}\n{bar_iso}"
        found[(question, "", symbol)] = f"{choice}\n{bar_iso}"
    _CHOICE_TAIL.update(found)


def latest_recorded_choice(
    question: str,
    *,
    symbol: Any,
    sleeve: Any = None,
    bar_iso: Any = None,
) -> str | None:
    """The newest recorded choice for this symbol and bar. None when the record has none."""

    if symbol in (None, ""):
        return None
    _refresh_choice_tail()
    sleeve_s = "" if sleeve in (None, "") else str(sleeve)
    symbol_s = str(symbol)
    packed = _CHOICE_TAIL.get((question, sleeve_s, symbol_s))
    if packed is None and sleeve_s:
        packed = _CHOICE_TAIL.get((question, "", symbol_s))
    if not packed:
        return None
    choice, _, recorded_iso = packed.partition("\n")
    if bar_iso not in (None, "") and recorded_iso and str(bar_iso) != recorded_iso:
        return None
    return choice or None


def last_bar_question_text(facts: Mapping[str, Any] | None = None) -> str:
    """The last-bar question with this close on the card.

    The legal answers are closed_bar_reaches, use_previous_close, and
    closed_bar_does_not_reach. A missing price stays absent. This text
    does not pick a side.
    """

    card = dict(facts or {})
    return (
        "Last-bar question: this closed bar. "
        f"Symbol {_shown(card.get('symbol'))}. "
        f"Sleeve {_shown(card.get('sleeve'))}. "
        f"Open {_shown(card.get('open'))}. "
        f"High {_shown(card.get('high'))}. "
        f"Low {_shown(card.get('low'))}. "
        f"Close {_shown(card.get('close'))}. "
        f"Range to the low {_shown(card.get('range_to_low'))}. "
        f"Range to the high {_shown(card.get('range_to_high'))}. "
        f"Direction {_shown(card.get('direction'))}. "
        f"Bid {_shown(card.get('bid'))}. "
        f"Ask {_shown(card.get('ask'))}. "
        f"Bid from the open {_shown(card.get('bid_from_open'))}. "
        f"Ask from the open {_shown(card.get('ask_from_open'))}. "
        f"Decision bar {_shown(card.get('decision_bar_iso'))}. "
        f"Seconds from the clock {_shown(card.get('seconds_from_clock'))}. "
        "Pick one option. closed_bar_reaches names this bar, including a bar "
        "whose close has not printed when the live quote has left the open, "
        "only when it is the single highest probability. "
        "use_previous_close names the previous close when this row is still "
        "forming and the live quote has not left the open. "
        "closed_bar_does_not_reach does not hand this bar to a new "
        "unit. An empty answer or a tie does not restore the previous close "
        "and does not invent a direction. Do not close an open ticket."
    )


def unit_question_text(facts: Mapping[str, Any] | None = None) -> str:
    """The unit question with this closed bar in the text.

    The legal answers are unit_long, unit_short, and sleeve_stays_out.
    A missing price stays absent. This text does not pick a side.
    """

    card = dict(facts or {})
    if card.get("last_bar_choice") in (None, ""):
        found = latest_recorded_choice(
            "last_bar",
            symbol=card.get("symbol"),
            sleeve=card.get("sleeve"),
            bar_iso=card.get("decision_bar_iso"),
        )
        if found:
            card["last_bar_choice"] = found
    return (
        "Unit question: this closed bar. "
        f"Symbol {_shown(card.get('symbol'))}. "
        f"Sleeve {_shown(card.get('sleeve'))}. "
        f"Open {_shown(card.get('open'))}. "
        f"High {_shown(card.get('high'))}. "
        f"Low {_shown(card.get('low'))}. "
        f"Close {_shown(card.get('close'))}. "
        f"Range to the low {_shown(card.get('range_to_low'))}. "
        f"Range to the high {_shown(card.get('range_to_high'))}. "
        f"Direction {_shown(card.get('direction'))}. "
        f"Bid {_shown(card.get('bid'))}. "
        f"Ask {_shown(card.get('ask'))}. "
        f"Decision bar {_shown(card.get('decision_bar_iso'))}. "
        f"Last bar {_shown(card.get('last_bar_choice'))}. "
        "Pick one option. A limit at this close is produced only when "
        "unit_long or unit_short is the single highest probability. "
        "Entry is this close. The stop is this bar's own range on the "
        "chosen side. sleeve_stays_out produces no unit. An empty answer "
        "or a tie does not invent a direction and does not restore a skip. "
        "Do not close an open ticket."
    )


def limit_unit_spec(winner: str | None, *, close: Any, high: Any, low: Any) -> dict[str, float | int] | None:
    """Limit geometry from the closed bar and the unit Choice.

    The stop is that bar's range on the chosen side. A missing side, a tie,
    an empty answer, or a zero range leaves the unit unset. No planted distance.
    """

    close_n = _finite(close)
    if winner == "unit_long":
        side = _finite(low)
        if close_n is None or side is None:
            return None
        direction = 1
        stop_dist = close_n - side
    elif winner == "unit_short":
        side = _finite(high)
        if close_n is None or side is None:
            return None
        direction = -1
        stop_dist = side - close_n
    else:
        return None
    if not (stop_dist > 0):
        return None
    return {
        "direction": direction,
        "stop_dist": stop_dist,
        "entry_price": close_n,
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def record_path() -> Path:
    override = (os.environ.get("GTOS_BOOK_ENGINE_CHOICES_RECORD") or "").strip()
    if override:
        return Path(override)
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "book_engine_choices.jsonl"
    )


def _append(row: Mapping[str, Any]) -> None:
    try:
        path = record_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(row), sort_keys=True, default=str) + "\n")
    except OSError:
        return


def spot(question: str, *, spot: str, facts: Mapping[str, Any] | None = None) -> str | None:
    """Return the unique highest alternative, or None when there is no decision.

    None does not restore a config boolean and does not name an unanswered hop.
    A previous answer is not reused. A miss does not delay the next ask.
    """

    spec = QUESTIONS.get(question)
    if spec is None:
        return None
    options = tuple(spec["criteria"])
    remembered = _STATE_MEMO.get(_state_key(question, facts))
    if remembered in options:
        return remembered
    instructions = spec["instructions"]
    if question == "unit":
        instructions = unit_question_text(facts)
    elif question == "last_bar":
        instructions = last_bar_question_text(facts)
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "question_id": spec["id"],
        "spot": str(spot),
        "choice": None,
        "decision_emitted": False,
        "order_send": False,
        "model": MODEL,
        "error": None,
    }
    if question in {"unit", "last_bar"}:
        row["question_text"] = instructions
        row["facts"] = dict(facts or {})
    winner: str | None = None
    try:
        from src.judgment.jev_client import calls_enabled
        from src.judgment.rung_choice import ask_choice

        if not calls_enabled():
            row["error"] = "call_not_made"
        else:
            hop = ask_choice(
                {
                    "login": CHALLENGE_LOGIN,
                    "ns": CHALLENGE_NS,
                    "question": question,
                    "spot": str(spot),
                    "facts": dict(facts or {}),
                },
                question_id=spec["id"],
                instructions=instructions,
                criteria=spec["criteria"],
            ) or {}
            weight = _returned_persist(hop)
            if weight is not None:
                row["persist"] = weight
            choice = hop.get("choice")
            if hop.get("decision_emitted") and choice in options:
                winner = str(choice)
                row["choice"] = winner
                row["probability"] = hop.get("probability")
                row["probabilities"] = hop.get("probabilities") or {}
                row["decision_emitted"] = True
                row["model"] = hop.get("model") or MODEL
                _STATE_MEMO[_state_key(question, facts)] = winner
            else:
                row["error"] = hop.get("error") or "no_unique_highest"
                row["probabilities"] = hop.get("probabilities") or {}
    except Exception as exc:  # noqa: BLE001 — generation must not raise
        row["error"] = type(exc).__name__
        winner = None
    _append(row)
    return winner

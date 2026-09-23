"""A1 / Alive fan-out questions. IDs are for our code; instructions carry the meaning.

One System One call per candidate. Stamp every fluid gate from the inventory.
Envelope walls are not asked — they stay integers.
A choice is the unique highest probability. A parameter is the returned score.
An empty answer, a tie, or an error does not restore a constant.
"""

from __future__ import annotations

from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS

MODEL = "jev-1.13.0"


def spot_question(
    spot: str,
    instructions: str,
    criteria: Mapping[str, str],
) -> dict[str, Any]:
    """One Choice. The question id is the spot. Criteria are the sides of that spot."""
    return {
        str(spot): {
            "type": "choice",
            "instructions": str(instructions).strip(),
            "criteria": {str(key): str(text) for key, text in criteria.items()},
        }
    }


def unique_highest(
    probabilities: Mapping[str, Any] | None,
    order: tuple[str, ...] | list[str] | None = None,
) -> str | None:
    """The decision is the unique highest probability.

    An empty map is not a decision. A tie is not a decision. A missing
    probability is not zero. A bare label is not a probability.
    """
    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    names = tuple(str(name) for name in order) if order else tuple(str(name) for name in probabilities)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probabilities:
            continue
        raw = probabilities.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            p = float(raw)
        except (TypeError, ValueError):
            continue
        if p != p:
            continue
        seen = True
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def returned_number(block: Any) -> float | None:
    """The parameter is the number this hop returned.

    An empty answer, a tie, or an error is not a number. Nothing here
    puts a printed constant back.
    """
    if not isinstance(block, Mapping):
        return None
    if block.get("error"):
        return None
    if "score" in block and block.get("score") is not None:
        try:
            number = float(block.get("score"))
        except (TypeError, ValueError):
            return None
        if number != number:
            return None
        return number
    if "noul" in block and block.get("noul") is not None and not isinstance(block.get("noul"), bool):
        try:
            number = float(block.get("noul"))
        except (TypeError, ValueError):
            return None
        if number != number:
            return None
        return number
    probabilities = block.get("probabilities")
    if isinstance(probabilities, Mapping) and probabilities:
        name = unique_highest(probabilities)
        if name is None:
            return None
        try:
            number = float(probabilities.get(name))
        except (TypeError, ValueError):
            return None
        if number != number:
            return None
        return number
    return None


_PARAMETER_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")


def parameter_question(spot: str, instructions: str) -> dict[str, Any]:
    """One ordinal Score. The six words name no amount.

    The return is a level position. A caller that needs an amount uses
    ``amount_question`` and reads the value on those anchors.
    """
    return {
        str(spot): {
            "type": "score",
            "instructions": str(instructions).strip(),
            "criteria": list(_PARAMETER_LEVELS),
        }
    }


_ANCHOR_KEY = "_anchor_values"
_USD_FIELDS = (
    ("equity", "the equity named on this card"),
    ("balance", "the balance named on this card"),
    ("open_pnl", "the open profit named on this card"),
    ("profit", "the open profit named on this card"),
    ("day_start_balance", "the day-start balance named on this card"),
    ("day_start_equity", "the day-start equity named on this card"),
    ("realized_closed_profit", "the realized profit named on this card"),
    ("day_equity", "the day equity named on this card"),
)


def _finite_anchor(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _anchor_pair(item: Any) -> tuple[Any, Any] | None:
    if isinstance(item, (str, bytes, Mapping)):
        return None
    try:
        parts = list(item)
    except TypeError:
        return None
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def anchor_levels(anchors: Any) -> list[tuple[str, float]] | None:
    """Ordered (label, value) levels. Fewer than two is not a Score."""

    if anchors is None or isinstance(anchors, (str, bytes)):
        return None
    if isinstance(anchors, Mapping):
        raw_items = list(anchors.items())
    else:
        try:
            raw_items = list(anchors)
        except TypeError:
            return None
    found: list[tuple[str, float]] = []
    seen: list[float] = []
    labels: set[str] = set()
    for item in raw_items:
        pair = _anchor_pair(item)
        if pair is None:
            number = _finite_anchor(item)
            text = "" if number is None else str(number).strip()
        else:
            label, raw = pair
            number = _finite_anchor(raw)
            text = "" if label is None else str(label).strip()
        if number is None or not text or number in seen or text in labels:
            continue
        seen.append(number)
        labels.add(text)
        found.append((text, number))
    found.sort(key=lambda pair: pair[1])
    if len(found) < 2:
        return None
    return found


def interpolate(position: Any, levels: list[tuple[str, float]]) -> float | None:
    """The anchor value at this level position. The position may sit between levels."""

    number = _finite_anchor(position)
    if number is None or not levels:
        return None
    low_index = None
    low_value = None
    for index, pair in enumerate(levels):
        value = pair[1]
        if number < index or number == index:
            if number == index or low_value is None:
                return value
            span = index - low_index
            if not span:
                return low_value
            frac = (number - low_index) / span
            return low_value + (frac * (value - low_value))
        low_index = index
        low_value = value
    return low_value


def amount_question(spot: str, instructions: str, anchors: Any) -> dict[str, Any]:
    """A Score whose levels are the card's own amounts. Fewer than two does not post.

    The block is the spine's Score builder: criteria are label (value), and the
    level count is the maximum the API has already stated.
    """

    from .nineteen import score_question

    return score_question(spot, instructions, anchors)


def ordinal_question(spot: str, instructions: str, levels: Any) -> dict[str, Any]:
    """A Score whose words are an order. The position is not an amount."""

    if isinstance(levels, (str, bytes)) or levels is None:
        return {}
    try:
        raw = list(levels)
    except TypeError:
        return {}
    words = []
    seen: set[str] = set()
    for item in raw:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        words.append(text)
    if len(words) < 2:
        return {}
    from .nineteen import kept_indexes

    ranks = kept_indexes(len(words))
    if ranks:
        words = [words[index] for index in ranks]
    return {
        str(spot): {
            "type": "score",
            "instructions": str(instructions).strip(),
            "criteria": words,
        }
    }


def ordinal_index(block: Any, n_levels: int) -> int | None:
    """Nearest level. The index is an ordinal, not an amount."""

    number = returned_number(block)
    if number is None:
        return None
    try:
        count = int(n_levels)
    except (TypeError, ValueError):
        return None
    if count < 2:
        return None
    if number < 0 or number > (count - 1):
        return None
    nearest = int(round(number))
    if nearest < 0 or nearest >= count:
        return None
    return nearest


def _cards(card: Any) -> list[Mapping[str, Any]]:
    if not isinstance(card, Mapping):
        return []
    found = [card]
    for key in ("account", "facts", "pair", "news"):
        inner = card.get(key)
        if isinstance(inner, Mapping) and inner is not card:
            found.append(inner)
    return found


def usd_anchors(card: Any) -> list[tuple[str, float]]:
    """Broker money already on the card, in account currency. Not a prior score."""

    pairs: list[tuple[str, float]] = []
    for source in _cards(card):
        for key, label in _USD_FIELDS:
            number = _finite_anchor(source.get(key))
            if number is None:
                continue
            pairs.append((label, number))
    return anchor_levels(pairs) or []


def weight_anchors(card: Any) -> list[tuple[str, float]]:
    """Weights and R multiples already named on the card. Not dollars."""

    pairs: list[tuple[str, float]] = []
    for source in _cards(card):
        for key, value in source.items():
            if not isinstance(key, str):
                continue
            name = key.lower()
            if name in {"persist_weight", "unit_usd", "prior_outcomes"}:
                continue
            if not (name.endswith("_weight") or name.endswith("_r") or name in {"weight", "locked_r"}):
                continue
            number = _finite_anchor(value)
            if number is None:
                continue
            pairs.append((f"the {name} named on this card", number))
    return anchor_levels(pairs) or []


def minute_anchors(card: Any) -> list[tuple[str, float]]:
    """Minute distances of named events already on the card."""

    pairs: list[tuple[str, float]] = []
    seen_events: list[Any] = []
    for source in _cards(card):
        for key in ("events",):
            rows = source.get(key)
            if isinstance(rows, list):
                seen_events.append(rows)
    for rows in seen_events:
        for item in rows:
            if not isinstance(item, Mapping):
                continue
            number = _finite_anchor(item.get("minutes_from_as_of"))
            if number is None:
                continue
            name = str(item.get("event") or item.get("name") or item.get("scheduled_utc") or "").strip()
            if not name:
                continue
            pairs.append((f"minutes from as-of of {name}", number))
    return anchor_levels(pairs) or []


def mult_anchors(card: Any) -> list[tuple[str, float]]:
    """Multiples already named on the card."""

    pairs: list[tuple[str, float]] = []
    for source in _cards(card):
        blobs = [source]
        facts = source.get("facts")
        if isinstance(facts, Mapping):
            blobs.append(facts)
        for blob in blobs:
            for key, value in blob.items():
                if not isinstance(key, str):
                    continue
                if not (key.endswith("_mult") or key.endswith("_multiple")):
                    continue
                number = _finite_anchor(value)
                if number is None:
                    continue
                pairs.append((f"the {key} named on this card", number))
    return anchor_levels(pairs) or []


def count_anchors(card: Any) -> list[tuple[str, float]]:
    """Counts already named on the card."""

    pairs: list[tuple[str, float]] = []
    for source in _cards(card):
        for key in ("n_candidates", "n_events", "n_sleeves"):
            number = _finite_anchor(source.get(key))
            if number is None:
                continue
            pairs.append((f"the {key} named on this card", number))
        for key in ("prior_outcomes", "candidates", "events", "sleeve_members", "lengths"):
            seq = source.get(key)
            if isinstance(seq, (list, tuple)):
                pairs.append((f"the count of {key} named on this card", float(len(seq))))
    return anchor_levels(pairs) or []


_ROW_LOCK = __import__("threading").Lock()
_ROW_OFFSET = 0
_ROW_PATH: str | None = None
_ROWS: list[dict[str, Any]] = []


def _logged_rows() -> list[dict[str, Any]]:
    """Outcome rows so far. New bytes are read once. A partial line waits."""

    import json

    global _ROW_OFFSET, _ROW_PATH, _ROWS
    path = _outcome_log()
    with _ROW_LOCK:
        key = str(path)
        if _ROW_PATH != key:
            _ROW_PATH = key
            _ROW_OFFSET = 0
            _ROWS = []
        try:
            size = path.stat().st_size
        except OSError:
            return list(_ROWS)
        if size < _ROW_OFFSET:
            _ROW_OFFSET = 0
            _ROWS = []
        if size == _ROW_OFFSET:
            return list(_ROWS)
        try:
            with path.open("rb") as handle:
                handle.seek(_ROW_OFFSET)
                blob = handle.read()
        except OSError:
            return list(_ROWS)
        if not blob.endswith(b"\n"):
            cut = blob.rfind(b"\n")
            if cut < 0:
                return list(_ROWS)
            blob = blob[: cut + 1]
        _ROW_OFFSET += len(blob)
        for line in blob.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                _ROWS.append(row)
        return list(_ROWS)


def last_logged_value(spot: str) -> float | None:
    """Previous returned number for this spot.

    The latest row wins. A miss on that row is empty. An older hit is not
    put back in its place.
    """
    found = False
    value: float | None = None
    for row in _logged_rows():
        if str(row.get("spot") or "") != str(spot):
            continue
        found = True
        raw = row.get("value")
        if raw is None or raw == "":
            value = None
            continue
        try:
            number = float(raw)
        except (TypeError, ValueError):
            value = None
            continue
        value = None if number != number else number
    if not found:
        return None
    return value


def priors_within(bound: Any, spots: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    """Prior rows the loop bound still covers. An empty bound reads nothing."""
    if bound is None or bound == "":
        return []
    try:
        number = float(bound)
    except (TypeError, ValueError):
        return []
    if number != number:
        return []
    wanted = None if spots is None else {str(name) for name in spots}
    kept: list[dict[str, Any]] = []
    for row in _logged_rows():
        spot = str(row.get("spot") or "")
        if wanted is not None and spot not in wanted:
            continue
        kept.append(
            {
                "spot": row.get("spot"),
                "value": row.get("value"),
                "at_utc": row.get("at_utc"),
            }
        )
        while kept and not (len(kept) <= number):
            del kept[0]
    return kept


def _outcome_log():
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[2]
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "parameter_outcomes.jsonl"
    )


def loop_count(spot: str, lengths: list[int] | tuple[int, ...]) -> int | None:
    """Steps in this loop. The score on this state is that count.

    Measured lengths ride the state as facts. An empty score, a tie, or an
    error is not a count. Nothing here puts a printed window back.
    """
    usable = [
        int(n)
        for n in lengths
        if isinstance(n, (int, float)) and not isinstance(n, bool) and int(n) >= 0
    ]
    qid = str(spot)
    rank = (
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
    )
    measured = []
    for index, length in enumerate(usable):
        if index >= len(rank):
            break
        measured.append((f"the {rank[index]} measured length named on this state", float(length)))
    questions = amount_question(
        qid,
        "How many steps does this loop take on this state? "
        "The score you return is that count. It may sit between the levels. "
        "Measured lengths on this state are facts. "
        "An empty score leaves the count unset.",
        measured,
    )
    if not questions:
        return None
    state: dict[str, Any] = {"spot": qid, "lengths": usable}
    try:
        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        loaded = []
    state["prior_outcomes"] = loaded if loaded is not None else []
    try:
        from .jev_client import evaluate

        receipt = evaluate(state, questions=questions, merge_sleeve=False)
    except Exception:
        return None
    if not isinstance(receipt, Mapping) or not receipt.get("ok"):
        return None
    answers = receipt.get("answers")
    block = answers.get(qid) if isinstance(answers, Mapping) else None
    number = returned_number(block)
    if number is None:
        return None
    whole = int(round(number))
    if whole < 0:
        return None
    try:
        append_outcome(qid, number, state, error=None)
    except Exception:
        return whole
    return whole


def prior_outcomes(
    spot: str | None = None,
    limit: int | None = None,
    *,
    state: Mapping[str, Any] | None = None,
    questions: Mapping[str, Any] | None = None,
) -> Any:
    """Folded outcome history. The next call reads this.

    A passed limit is not a window. The file is not cut to a line count.
    An empty file stays empty. A null value stays null.
    """
    del limit
    rows = _logged_rows()
    if spot is not None:
        wanted = str(spot)
        return [
            _slim_outcome(row)
            for row in rows
            if str(row.get("spot") or "") == wanted
        ]
    return _folded_history(rows, state, questions)


_GOLD_SPOTS = frozenset({"distance", "limit", "walk"})

_WALK_CODE = {
    "until_print": "p",
    "following_bar": "f",
    "until_next_same": "n",
    "through_last_row": "e",
}
_PATH_CODE = {
    "limit_first": "L",
    "distance_first": "D",
    "same_bar": "S",
    "wick_already": "W",
    "not_resting": "R",
    "open": "O",
    "unanswered": "U",
}
_AFTER_CODE = {
    "favorable": "+",
    "adverse": "-",
    "same": "=",
    "not_filled": ".",
    None: ".",
}
_EARLIER_LEGEND = (
    "earlier is one group per prior bar, in order, three characters. "
    "walk: p until the distance prints, f the next row, n the next bar of this kind, "
    "e through the last row. "
    "path: L limit printed first, D distance printed first, S both on one row, "
    "W the bar already traded the distance, R the limit was not resting, "
    "O neither printed, U unanswered. "
    "after: + favorable, - adverse, = both on one row, . no fill. "
    "recent lists the newest bars with the returned distance and the returned limit."
)


def _slim_outcome(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "spot": row.get("spot"),
        "value": row.get("value"),
        "at_utc": row.get("at_utc"),
    }


def _outcome_code(record: Mapping[str, Any]) -> str:
    if record.get("distance") is None or record.get("path") == "unanswered":
        return "UU."
    walk = _WALK_CODE.get(record.get("walk"), "?")
    path = _PATH_CODE.get(record.get("path"), "?")
    after = _AFTER_CODE.get(record.get("after_fill"), ".")
    return f"{walk}{path}{after}"


def _outcome_full(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "time": record.get("time"),
        "distance": record.get("distance"),
        "limit": record.get("limit"),
        "walk": record.get("walk"),
        "path": record.get("path"),
        "after_fill": record.get("after_fill"),
        "rows_walked": record.get("rows_walked"),
    }


def _bars_and_scores(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bars: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    scores: list[dict[str, Any]] = []
    for row in rows:
        spot = str(row.get("spot") or "")
        if spot not in _GOLD_SPOTS:
            scores.append(_slim_outcome(row))
            continue
        clock = row.get("at_utc")
        key = "" if clock is None else str(clock)
        slot = index.get(key)
        if slot is None:
            index[key] = len(bars)
            bars.append(
                {
                    "time": clock,
                    "distance": None,
                    "limit": None,
                    "walk": None,
                    "path": row.get("path"),
                    "after_fill": row.get("after_fill"),
                    "rows_walked": row.get("rows_walked"),
                }
            )
            slot = index[key]
        record = bars[slot]
        value = row.get("value")
        current = record.get(spot)
        if value is not None or current is None:
            record[spot] = value
        for extra in ("path", "after_fill", "rows_walked"):
            if record.get(extra) is None and row.get(extra) is not None:
                record[extra] = row.get(extra)
    return bars, scores


def _with_history(
    base: Mapping[str, Any],
    history: Any,
) -> dict[str, Any]:
    state = dict(base)
    for key in ("prior_outcomes", "earlier", "earlier_legend", "recent"):
        state.pop(key, None)
    state["prior_outcomes"] = history
    return state


def _folded_history(
    rows: list[dict[str, Any]],
    state: Mapping[str, Any] | None,
    questions: Mapping[str, Any] | None,
) -> Any:
    """Gold bars stay in order. Each other spot keeps its latest return.

    The API's refusal still shortens a later post. No planted row count.
    """

    del state, questions
    if not rows:
        return []
    bars, scores = _bars_and_scores(rows)
    latest: dict[str, dict[str, Any]] = {}
    for row in scores:
        latest[str(row.get("spot") or "")] = row
    return [_outcome_full(item) for item in bars] + list(latest.values())


def append_outcome(spot: str, value: float | None, facts: Mapping[str, Any] | None = None, error: str | None = None) -> None:
    """Append this hop so the next call sees it. A miss is stored as a miss."""
    import json
    from datetime import datetime, timezone

    path = _outcome_log()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        card = facts if isinstance(facts, Mapping) else {}
        payload = {
            "spot": str(spot),
            "value": value,
            "error": error,
            "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "equity": card.get("equity"),
            "balance": card.get("balance"),
            "realized_closed_profit": card.get("realized_closed_profit"),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        return



# Score include-depth (founder memo). Not a Noul keep/drop.
INCLUDE_DEPTH = ("hide", "short", "long", "full")

# JEV_EVERYWHERE.md §3 gate seat. One System One request. Do not add a second call.
GATE_SEAT_IDS = (
    "state_sufficient",
    "include_depth",
    "equity_to_pass",
    "money_decision",
    "flow_stance",
    "session_fitness",
    "geometry_vs_tape",
    "level_respect",
    "persistence",
    "signal_presence",
    "tape_fresh",
    "event_proximity",
    "admit",
    "isolated_reentry_is_new",
    "chase_toxicity",
)

# Weight ids on the gate post. The weight is the score returned for that id.
# A missing score stays missing. Admit Choice is the fire; this is not a cliff.
_WEIGHT_LEVELS = (
    "none of it",
    "a light share",
    "a middle share",
    "a heavy share",
)
GATE_WEIGHT_IDS = (
    "w_geometry",
    "w_session",
    "w_level",
    "w_flow",
    "w_persist",
)
_WEIGHT_SUBJECT = {
    "w_geometry": "geometry_vs_tape",
    "w_session": "session_fitness",
    "w_level": "level_respect",
    "w_flow": "flow_alignment",
    "w_persist": "persistence",
}


def _weight_questions() -> dict[str, Any]:
    """One score per weight. The levels name no share."""
    packed: dict[str, Any] = {}
    for qid in GATE_WEIGHT_IDS:
        subject = _WEIGHT_SUBJECT[qid]
        packed[qid] = {
            "type": "score",
            "instructions": (
                f"What weight does the returned {subject} score carry on this state? "
                "The score you return is that weight. It may sit between the levels. "
                "An empty score leaves the weight unset."
            ),
            "criteria": list(_WEIGHT_LEVELS),
        }
    return packed


def gate_composite_weights(answers: Mapping[str, Any] | None) -> dict[str, float]:
    """Each weight is the score on this return. A missing score stays out."""
    if not isinstance(answers, Mapping):
        return {}
    weights: dict[str, float] = {}
    for qid in GATE_WEIGHT_IDS:
        number = returned_number(answers.get(qid))
        if number is None:
            continue
        weights[qid] = number
    return weights


A1_GATE_IDS = (
    "SEL-V4-002",
    "UB-AUTH-010",
    "UB-PLC-017",
    "F5-JEV-004",
    "F5-JEV-LIVE",
    "f5_xau_flow_alignment_size_tilt",
)

#: Admission-seat consume IDs (JEV_EVERYWHERE §3). One System One call still
#: fans the full gold book; this tuple is what admission_place composes.
ADMISSION_SEAT_IDS = (
    "state_sufficient",
    "include_depth",
    "equity_to_pass",
    "money_decision",
    "flow_alignment",
    "persistence",
    "a8_quality",
    "a8_agrees",
    "geometry_vs_tape",
    "level_respect",
    "cost_hurtful",
    "admit",
)

#: Size-seat consume IDs (JEV_EVERYWHERE §3). Same Score atoms as the gate.
SIZE_SEAT_IDS = (
    "include_depth",
    "equity_to_pass",
    "money_decision",
    "persistence",
    "geometry_vs_tape",
    "session_fitness",
    "cost_hurtful",
    "conviction_vs_tape",
    "event_proximity",
)

#: Close-seat gold IDs. Pack-only Choices (move_sl / time_stop / …) sit on the
#: size_exit schema dump, not in the gold catalog.
CLOSE_SEAT_IDS = ("exit_class",)

# Nested seats. Code picks a node, then dumps that schema (hierarchical
# function-calling). This is not a linear catalog to keep/drop.
# Gate dump includes GATE_SEAT_IDS plus the Scores compose actually consumes
# (flow_alignment, cost_hurtful) — those rode the old full-catalog POST.
def _tree_ids(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for qid in group:
            if qid in seen:
                continue
            seen.add(qid)
            out.append(qid)
    return tuple(out)


QUESTION_TREE: dict[str, Any] = {
    "gate": {"ids": _tree_ids(GATE_SEAT_IDS, ("flow_alignment", "cost_hurtful"), GATE_WEIGHT_IDS)},
    "admission": {"ids": ADMISSION_SEAT_IDS},
    "size": {"ids": _tree_ids(SIZE_SEAT_IDS, ("ac60_size",))},
    "close": {"ids": CLOSE_SEAT_IDS},
    # Dynamic subtree: this fire's sleeve schema, not a gold-catalog ID list.
    # Dumped via sleeve_subtree_questions(..., standalone=False) into the same
    # POST — reuse gold state_sufficient; never a second hop or keep/drop wall.
    "sleeve": {"ids": (), "source": "sleeve_subtree_questions", "standalone": False},
    # Remaining walls: two hierarchical packs per intent (include-depth, then
    # the named decision pack). Not a catalog keep/drop. Dumped via
    # remaining_seats.evaluate_pack → evaluate(questions=).
    "remaining": {
        "ids": (),
        "packs": ("place_wall", "restart_chase", "remint", "sleeve_emit"),
        "hops": ("include_depth", "decision"),
        "standalone": False,
    },
}

# Query-aware compression. Compose-side only. An empty spine still asks
# event_proximity. An empty answer is not a filled middle. Never a payload drop wall.
QUESTION_IGNORE_IF = {
    "level_respect": "levels.source==unassembled",
    "session_fitness": "sessions.source==unassembled",
    "event_proximity": "news.spine_empty",
    "persistence": "sleeve_features.ac60 is null",
    "tape_fresh": "no named timestamps",
    "a8_quality": "not a metals sleeve",
    "a8_agrees": "not a metals sleeve",
    "flow_stance": "state_sufficient low",
    "flow_alignment": "state_sufficient low",
    "admit": "state_sufficient low",
}


def gold_fanout_questions() -> dict[str, Any]:
    """Full fluid question set. One request. Empty news spine is not 'no HIGH'.

    Questions path-reference gold_state / symbol_state fields and are not
    XAU-only. The name is historical. Prefer ``symbol_fanout_questions``.
    """
    questions = {
        "state_sufficient": {
            "type": "noul",
            "instructions": (
                "Do completeness.missing_fields and the named blocks contain enough "
                "to judge this fire as-of clock.as_of_utc? Yes means the named tape, "
                "geometry, and identity are present. No means a state is missing. "
                "Use only named fields. Empty news spine is not 'no HIGH'."
            ),
            "criteria": {
                "true": "Named blocks are present enough to judge the fire",
                "false": "A required named block is missing or unknown",
            },
        },
        "equity_to_pass": {
            "type": "score",
            "instructions": (
                "Does this fire help this login's live equity? "
                "Read `account.equity`, `account.balance`, `account.day_equity`, "
                "`account.day_start_balance`, `account.day_start_equity`, and "
                "`account.day_start_max` when those numbers were recorded. "
                "`account.terminal_read` = missing means this card has no terminal "
                "number. That is a fact on the card. Still judge the hop. "
                "Do not invent equity. "
                "`geometry.plan_r` describes the ticket vs its stop. It is not "
                "the mission score. This score is not a boolean and not a cutoff. "
                "The money decision is `money_decision`, the choice with the "
                "highest probability. The cash parameter is the returned score, "
                "not a printed unit."
            ),
            "criteria": [
                "Cash outcome does not help this equity",
                "Ordinary versus this login's live equity",
                "Named cash outcome helps this equity",
            ],
        },
        "money_decision": {
            "type": "choice",
            "instructions": (
                "Money decision for this hop. `account.equity` and "
                "`account.balance` are facts in the state, not a boolean and "
                "not a threshold. "
                "Pick the action with the highest probability. "
                "`leave_size` keeps the cash the last returned score named. "
                "`cut` is a smaller cash than that returned score. "
                "`stand` adds no risk. "
                "The cash number is the returned score, not a printed unit."
            ),
            "criteria": {
                "leave_size": "Keep the cash the last returned score named",
                "cut": "Smaller cash than that returned score",
                "stand": "Do not add risk",
            },
        },
        "include_depth": {
            "type": "score",
            "instructions": (
                "How much of the surrounding named tree belongs with this fire? "
                "hide = this query does not need the chunk; short = a directional "
                "snippet so the action could exist; long = instructions without the "
                "rest of the schema; full = the whole subtree. "
                "The score you return is that depth. It may sit between the levels. "
                "Do not scan every named block as keep-or-drop."
            ),
            "criteria": [
                "hide",
                "short summary",
                "longer summary",
                "whole subtree",
            ],
        },
        "flow_stance": {
            "type": "choice",
            "instructions": (
                "Given timeframes.h4.trend, timeframes.d1, sleeve_features.htf_slope_norm, "
                "sleeve_features.mom_20_atr, and identity.side, is this fire with the "
                "named flow, against it, or is flow unclear?"
            ),
            "criteria": {
                "with_flow": "Side agrees with named H4/D1 flow",
                "against_flow": "Side fights named H4/D1 flow",
                "no_clear_flow": "Named flow is mixed, flat, or missing",
            },
        },
        "flow_alignment": {
            "type": "score",
            "instructions": (
                "How aligned is identity.side with named HTF/session flow? "
                "Use named timeframe and sleeve_features fields, and assembled "
                "chair usd-proxy / corr / dual-leg labels when present. "
                "Unassembled chair or pack fields are not a vote. "
                "`info.risk_on_off_bundle` is information only and cannot refuse."
            ),
            "criteria": [
                "Fighting named HTF/session flow",
                "Mixed or rotating flow",
                "Aligned with named HTF/session flow",
            ],
        },
        "session_fitness": {
            "type": "score",
            "instructions": (
                "Is this the sleeve's clean hour, or merely not the dead clock? "
                "Use sessions.named, sessions.broker_hour, clock.is_friday, "
                "and assembled chair/session labels when present. "
                "The score you return is that fitness. It may sit between the levels. "
                "Do not replace the writer clock. ENV-US30 stays an integer. "
                "Do not invent overlap volume. Unassembled session stubs are inputs, not refuse walls."
            ),
            "criteria": [
                "Dead window, Friday cutoff, or wrong hour for the sleeve",
                "Ordinary session",
                "Sleeve's clean hour",
            ],
        },
        "geometry_vs_tape": {
            "type": "score",
            "instructions": (
                "Does geometry.stop_dist / plan_r fit named M15 vol? "
                "The score you return is that fit. It may sit between the levels. "
                "Do not define a level as a printed house R."
            ),
            "criteria": [
                "Stop likely dies in the next 1–2 M15 prints",
                "Ordinary house risk versus named vol",
                "Stop and target fit named vol",
            ],
        },
        "level_respect": {
            "type": "score",
            "instructions": (
                "Is the fire holding or reclaiming a named supporting PDH/PDL/FVG, "
                "or firing through a named opposing level? Ignore when levels.source "
                "is unassembled. Do not invent FVG when unassembled."
            ),
            "criteria": [
                "Firing through a named opposing PDH/PDL/FVG",
                "No relevant named level",
                "Holding or reclaiming a named supporting level",
            ],
        },
        "persistence": {
            "type": "score",
            "instructions": (
                "Is persistence with named gold flow a range on this bar? "
                "Read sleeve_features.ac60 with identity.side and "
                "the flow_stance answer in this same request. "
                "The score you return is that persistence. It may sit between the levels. "
                "Do not treat a printed ac60 line as a wall. "
                "Missing ac60 leaves the score unset. "
                "This score is the size range, not a second cliff."
            ),
            "criteria": [
                "Fighting or mean-reverting versus the named side",
                "No persistence edge on this bar",
                "Persistent with the named side",
            ],
        },
        "signal_presence": {
            "type": "score",
            "instructions": (
                "Does this bar deserve a candidate as a range, not generator-none? "
                "The integer still emits or does not. This score is the case for a candidate. "
                "An empty score leaves this unset. Do not re-encode an ac60 cliff."
            ),
            "criteria": [
                "No named tape reason to emit a candidate",
                "Ordinary bar — generator-None would be a guess",
                "Named tape + geometry argue a candidate belongs here",
            ],
        },
        "tape_fresh": {
            "type": "noul",
            "instructions": (
                "Is the market clock alive — bar/tick age versus the named interval? "
                "Use clock.as_of_utc and named bar/tick timestamps only. "
                "Ignore-if no timestamps. Stale tape is missing state, not a refuse wall."
            ),
            "criteria": {
                "true": "Named bar/tick age is inside the interval",
                "false": "Named age is stale versus the interval",
            },
        },
        "chase_toxicity": {
            "type": "score",
            "instructions": (
                "Is this still the same setup, or a restart chase? "
                "Read bars since decision, pending age, and sessions.named. "
                "Do not call a legal isolated reprint a remint."
            ),
            "criteria": [
                "Restart chase / aged pending on a dead or wrong hour",
                "Ordinary continuation of the same named setup",
                "Fresh named setup, not a chase",
            ],
        },
        "cost_hurtful": {
            "type": "noul",
            "instructions": (
                "Is cost.spread_r_of_stop large enough versus geometry.plan_r / stop "
                "that this fire is cost-dominated? This is a size-tilt question, "
                "never a new refuse."
            ),
            "criteria": {
                "true": "Spread/cost eats a material fraction of the stop",
                "false": "Cost is ordinary versus the named stop",
            },
        },
        "event_proximity": {
            "type": "noul",
            "instructions": (
                "Is a named HIGH in news.events inside the window the code uses "
                "(news.high_in_f5_window for F5, news.high_in_w7_window for W7)? "
                "Assembled BOJ/Warsh labels on this same window are named timing, not a new refuse. "
                "Empty spine stays unassembled. "
                "If news.spine_empty is true, you do not know. "
                "An empty spine is not a decision and is not a filled probability. "
                "Empty spine is not 'no HIGH'."
            ),
            "criteria": {
                "true": "A named HIGH is inside the code window",
                "false": "Named events exist and none are inside the code window",
            },
        },
        "calendar_honest": {
            "type": "noul",
            "instructions": (
                "Is news.spine_empty false and news.events non-empty for this as-of? "
                "This is consistency, not an invented HIGH."
            ),
            "criteria": {
                "true": "Spine is present and events are named",
                "false": "Spine empty or events missing — abstain event questions",
            },
        },
        "a8_quality": {
            "type": "score",
            "instructions": (
                "Is A8 confluence a range on this bar? Read sleeve_features "
                "htf_slope_norm, mom_20_atr, fvg_freshness_bars, session_hour, "
                "and the integer a8_k_of_4_pass when named. Also news.* and levels.* "
                "when assembled. Integer K=3-of-4 still computes as a fact — this "
                "Score may move the K. Do not re-vote the integer as a cliff. "
                "Ignore when this is not a metals sleeve."
            ),
            "criteria": [
                "0–1 of the named A8 fields, or news/levels contradict",
                "2-of-4 named A8 fields",
                "3–4-of-4 and news/levels do not contradict",
            ],
        },
        "a8_agrees": {
            "type": "noul",
            "instructions": (
                "Does sleeve_features.a8_k_of_4_pass agree with the named A8 fields? "
                "Consistency only — not a re-vote of the integer gate. Ignore when "
                "this is not a metals sleeve."
            ),
            "criteria": {
                "true": "Named A8 fields agree with the integer pass bit",
                "false": "Named A8 fields disagree or are missing",
            },
        },
        "admit": {
            "type": "choice",
            "instructions": (
                "Given remaining intelligence — not house integers — would this fire "
                "still be scored admit? This is not 'will it profit'. "
                "hard_refuse only when named state says the fire fights tape or is "
                "cost-dominated. House hard-off / token / 2-stop COUNT are code, not this answer. "
                "Assembled gbpjpy/dsp readiness labels are a separate family — "
                "none of them is this admit answer."
            ),
            "criteria": {
                "admit": "Named tape and geometry still support taking the fire",
                "abstain": "State is thin or mixed; do not steer",
                "hard_refuse": "Named tape or cost argues against the fire",
            },
        },
        "family_study_vs_keep": {
            "type": "choice",
            "instructions": (
                "Given identity.family_class and identity.sleeve, is this a study "
                "row, a house keep, or a house hard-off? Confirm the named class; "
                "do not discover bleed as a Noul."
            ),
            "criteria": {
                "study": "Named family is study",
                "keep": "Named family is house_keep",
                "hard_off": "Named family is house_hard_off — integer already decided",
            },
        },
        "session_size": {
            "type": "score",
            "instructions": (
                "Size tilt from session_fitness only. "
                "The score you return is that tilt. It may sit between the levels. "
                "An empty score leaves the tilt unset. This score cannot zero a fire."
            ),
            "criteria": ["Haircut", "Ordinary", "Sleeve clean hour"],
        },
        "geo_size": {
            "type": "score",
            "instructions": "Size tilt from geometry_vs_tape only. Cannot zero a fire.",
            "criteria": ["Stop likely dies — haircut", "Ordinary", "Stop/target fit vol"],
        },
        "level_size": {
            "type": "score",
            "instructions": (
                "Size tilt from level_respect only. "
                "The score you return is that tilt. It may sit between the levels. "
                "Unassembled levels leave the score unset."
            ),
            "criteria": ["Through opposing level", "No relevant level", "Supporting reclaim"],
        },
        "event_size": {
            "type": "score",
            "instructions": (
                "Size tilt from named HIGH proximity. "
                "The score you return is that tilt. It may sit between the levels. "
                "An empty spine leaves the score unset. "
                "This tilt is never a refuse. "
                "Assembled `gate.event_boj_window` is an input to this tilt, not a wall."
            ),
            "criteria": ["Named HIGH inside the code window", "Nearby but outside", "No named HIGH in window"],
        },
        "ac60_size": {
            "type": "score",
            "instructions": (
                "Size tilt from sleeve_features.ac60 as a range, not a printed cliff. "
                "The score you return is that tilt. It may sit between the levels. "
                "Missing ac60 leaves the score unset. "
                "Same atom as persistence. This score cannot zero a fire."
            ),
            "criteria": [
                "ac60 fights the named side",
                "No persistence edge",
                "ac60 supports the named side",
            ],
        },
        "combined_size": {
            "type": "score",
            "instructions": (
                "How strong is the combined living size case? Code multiplies live_flow "
                "× live_cost. You do not send. You do not refuse."
            ),
            "criteria": ["Haircut case", "Ordinary", "Aligned and cheap"],
        },
        "conviction_vs_tape": {
            "type": "score",
            "instructions": (
                "Which unit deserves remaining headroom / what multiplier fits named "
                "tape? Read geometry_vs_tape and flow_alignment. Orders the shed and "
                "tilts size. Cannot invent headroom past the prop wall. Cannot refuse."
            ),
            "criteria": [
                "Named tape argues a haircut versus remaining headroom",
                "Ordinary / mixed tape",
                "Named tape supports the remaining unit",
            ],
        },
        "veto_corr": {
            "type": "noul",
            "instructions": (
                "Draft-only: would a correlation HOLD be scored? Occupancy KEEP is code, not this. "
                "When assembled, read `aplus.chair_fields.corr.eur_gbp_usd_co_move`, "
                "`aplus.chair_fields.corr.xau_vs_eur_proxy_usd`, and PACK 3 "
                "`corr.eur_gbp_usd_co_move`, `corr.xau_vs_eur_proxy_usd`, "
                "`corr.gbpjpy_risk_cross`. Unassembled peers are not HOLD."
            ),
            "criteria": {"true": "Named correlation argues HOLD draft", "false": "No named correlation HOLD"},
        },
        "veto_event": {
            "type": "noul",
            "instructions": "Draft-only: named HIGH in the code window argues a pre-fill VETO draft?",
            "criteria": {"true": "Named HIGH in window", "false": "No named HIGH in window or spine empty"},
        },
        "veto_cost": {
            "type": "noul",
            "instructions": "Draft-only cost VETO. Must not become a new cost_skip / refuse.",
            "criteria": {"true": "Cost-dominated versus named stop", "false": "Cost ordinary"},
        },
        "veto_occupancy_label": {
            "type": "noul",
            "instructions": (
                "Label whether occupancy looks crowded. The keep-one writer integer "
                "stays code. Do not HOLD a legal 15m reprint as remint."
            ),
            "criteria": {"true": "Named occupancy is crowded", "false": "Named occupancy is clear or unknown"},
        },
        "cost_vs_tape": {
            "type": "score",
            "instructions": "Does named spread_r fit named M15 vol, not just stop_dist?",
            "criteria": ["Spread dominates named vol", "Ordinary", "Cheap versus named vol"],
        },
        "stale_standing": {
            "type": "noul",
            "instructions": "Is the standing / slate row stale versus clock.as_of_utc?",
            "criteria": {"true": "Standing is stale versus as-of", "false": "Standing is current or unknown"},
        },
        "last_refusal_class": {
            "type": "choice",
            "instructions": "If a last refusal is named, classify it. Do not invent a refusal.",
            "criteria": {
                "none": "No named last refusal",
                "cost": "Last named refusal was cost",
                "other": "Last named refusal was something else",
            },
        },
        "close_label": {
            "type": "choice",
            "instructions": (
                "LABEL only. Name the close class from named fields. time_stop is "
                "first-class. Do not accept manual_other at high confidence on winners. "
                "Illegal on live_intent objects that forbid EXPOST."
            ),
            "criteria": {
                "orig_stop": "Named exit is orig_stop",
                "broker_tp": "Named exit is broker_tp",
                "time_stop": "Named exit is time_stop",
                "breach_flatten": "Named exit is breach_flatten",
                "other": "Named exit is other / unknown",
            },
        },
        "exit_class": {
            "type": "choice",
            "instructions": (
                "What noun is this exit? time_stop is first-class. "
                "Do not label a paying time-stop as other. "
                "Close-label after the exit exists is a second object. On an open "
                "ticket this names the exit noun. "
                "An empty answer leaves the noun unset. Do not flatten a position."
            ),
            "criteria": {
                "orig_stop": "Original broker stop.",
                "broker_tp": "Broker target fill.",
                "time_stop": (
                    "Horizon / time-stop close. "
                    "First-class — never fold this into other / manual_other."
                ),
                "breach_flatten": "Governor flatten is the named exit. This question does not flatten a position.",
                "other": "Other / unknown. Do not prefer this for a paying time-stop.",
            },
        },
        "time_stop_vs_orig": {
            "type": "noul",
            "instructions": "LABEL: does named time-stop horizon disagree with orig stop geometry?",
            "criteria": {"true": "Time-stop and orig disagree", "false": "They agree or are unassembled"},
        },
        "hold_too_late": {
            "type": "noul",
            "instructions": "LABEL: named hold looks late versus sleeve horizon? Do not flatten.",
            "criteria": {"true": "Hold looks late on named fields", "false": "Hold is ordinary or unknown"},
        },
        "mfe_shape": {
            "type": "score",
            "instructions": "LABEL only. Score named MFE shape when EXPOST is legal. Else abstain.",
            "criteria": ["No named excursion", "Ordinary", "Clean runner shape"],
        },
        "trail_vs_orig": {
            "type": "noul",
            "instructions": "LABEL: named trail versus orig stop. Do not remint.",
            "criteria": {"true": "Trail disagrees with orig", "false": "Agree or unassembled"},
        },
        "leave_orig_293332188": {
            "type": "noul",
            "instructions": (
                "Is this ticket 293332188 or an already-open leave-orig row? "
                "If yes, this hop does not manage it. Writer still prints. "
                "Do not invent a tilt."
            ),
            "criteria": {
                "true": "Leave orig — do not manage from APPLY",
                "false": "Not the leave-orig ticket / already-open exception",
            },
        },
        "runner_r": {
            "type": "score",
            "instructions": "LABEL: named runner R quality when legal. Do not flatten.",
            "criteria": ["No runner", "Ordinary", "Clean runner"],
        },
        "friday_cutoff_label": {
            "type": "noul",
            "instructions": "LABEL: is clock.is_friday and sessions.named friday_cutoff? Writer clock stays integer.",
            "criteria": {"true": "Friday cutoff named", "false": "Not Friday cutoff"},
        },
        "isolated_reentry": {
            "type": "noul",
            "instructions": (
                "Confirm writer integers: flat symbol and isolated re-entry legal. "
                "Do not call a legal 15m reprint a remint. Gate ID "
                "`isolated_reentry_is_new` is the same atom with gold-walk wording."
            ),
            "criteria": {"true": "Named isolated re-entry is a new fire", "false": "Not isolated or unknown"},
        },
        "isolated_reentry_is_new": {
            "type": "noul",
            "instructions": (
                "Do occupancy integers say this is a new named fire on a flat symbol "
                "(isolated ≥15m), not the spent ticket? "
                "Read occupancy.symbol_open, occupancy.isolated_reentry_legal, "
                "occupancy.minutes_since_flat, occupancy.two_stop_exhausted. "
                "2-stop COUNT stays an integer. Do not invent a remint."
            ),
            "criteria": {
                "true": "Named isolated re-entry is a new fire on a flat symbol",
                "false": "Spent ticket / not isolated / unknown",
            },
        },
        "sibling_cooldown": {
            "type": "noul",
            "instructions": "LABEL: named sibling cooldown still live? 2-stop COUNT stays integer.",
            "criteria": {"true": "Named cooldown still binds", "false": "Clear or unknown"},
        },
        "spring_reprint": {
            "type": "noul",
            "instructions": "LABEL: does named state look like a spring reprint, not a remint?",
            "criteria": {"true": "Named spring reprint", "false": "Not a spring reprint"},
        },
        "minutes_since_flat": {
            "type": "score",
            "instructions": "LABEL: how clean is minutes-since-flat when named?",
            "criteria": ["Just flat / too soon", "Ordinary", "Clean isolated gap"],
        },
        "two_stop_would_be_third": {
            "type": "noul",
            "instructions": (
                "LABEL a would-be third same-sleeve orig_stop. You are not the counter. "
                "The 2-stop COUNT stays an integer on closed[]."
            ),
            "criteria": {"true": "Would be a third orig_stop", "false": "Would not, or unknown"},
        },
        "cluster_same_day": {
            "type": "noul",
            "instructions": "LABEL: named same-day cluster on this sleeve/symbol?",
            "criteria": {"true": "Named cluster", "false": "No named cluster"},
        },
        "high_in_f5_window": {
            "type": "noul",
            "instructions": "Is news.high_in_f5_window true? If spine_empty, you do not know.",
            "criteria": {"true": "Code says HIGH in F5 window", "false": "Code says not, or spine empty"},
        },
        "minutes_to_nearest": {
            "type": "score",
            "instructions": (
                "Score news.minutes_to_nearest_high. "
                "The score you return is that distance. It may sit between the levels. "
                "An empty spine leaves the score unset."
            ),
            "criteria": ["Inside the code window or overdue", "Nearby same session", "Far or unknown"],
        },
        "warsh_class": {
            "type": "choice",
            "instructions": (
                "Classify the nearest named HIGH when present. Do not invent. "
                "Assembled BOJ/Warsh labels on this same window are named timing, not a new refuse."
            ),
            "criteria": {
                "boe_fomc_nfp_cpi": "Named BOE / FOMC / NFP / CPI / Warsh-class",
                "other_high": "Named HIGH of another class",
                "none": "Spine empty or no named HIGH",
            },
        },
        "spine_empty_honesty": {
            "type": "noul",
            "instructions": "Is news.spine_empty true? Empty spine ≠ no HIGH.",
            "criteria": {"true": "Spine empty — event questions abstain", "false": "Spine present"},
        },
        "past_flag": {
            "type": "noul",
            "instructions": "Is the nearest named HIGH already past this as-of?",
            "criteria": {"true": "Nearest named HIGH is past", "false": "Future, missing, or spine empty"},
        },
        "gold_usd_comove": {
            "type": "choice",
            "instructions": (
                "Does named world.gold_vs_usd say gold is moving with the FX USD "
                "proxy, against it, or is the block unassembled/mixed? Use only "
                "world.gold_vs_usd. Do not invent DXY. Unassembled → no_clear."
            ),
            "criteria": {
                "with_usd": "Named gold_with_usd",
                "against_usd": "Named gold_against_usd",
                "no_clear": "mixed or unassembled — do not guess",
            },
        },
        "gold_index_comove": {
            "type": "choice",
            "instructions": (
                "Does named world.gold_vs_index say gold is moving with US30, "
                "against it, or is the block unassembled? Missing US30 tape → no_clear."
            ),
            "criteria": {
                "with_us30": "Named gold_with_us30",
                "against_us30": "Named gold_against_us30",
                "no_clear": "mixed or unassembled",
            },
        },
        "risk_on_funding": {
            "type": "choice",
            "instructions": (
                "Read world.risk_on only. Risk-on needs US30 plus USDJPY yen_offered. "
                "USDJPY alone is rates_proxy, not risk_on. Unassembled → do not guess."
            ),
            "criteria": {
                "risk_on": "Named risk_on (US30 up and yen offered)",
                "risk_off": "Named risk_off (US30 down and yen bid)",
                "mixed": "Named mixed or unassembled",
            },
        },
        "session_liquidity": {
            "type": "score",
            "instructions": (
                "Score world.session_liquidity. "
                "The score you return is that liquidity. It may sit between the levels. "
                "Clock only — do not invent volume."
            ),
            "criteria": [
                "Thin session (asia / dead / Friday cutoff)",
                "Ordinary London or NY",
                "London-NY overlap",
            ],
        },
        "occupancy_world": {
            "type": "score",
            "instructions": (
                "Score world.occupancy_book.n_clusters_open. "
                "The score you return is that occupancy. It may sit between the levels. "
                "Unknown occupancy leaves the score unset. Occupancy KEEP-one "
                "stays an integer. This is a label, not a refuse."
            ),
            "criteria": [
                "Empty book",
                "One named cluster open",
                "Two or more clusters open",
            ],
        },
    }
    questions.update(_weight_questions())
    return questions


def symbol_fanout_questions() -> dict[str, Any]:
    """Instrument-neutral alias. Same IDs / instructions as ``gold_fanout_questions``."""
    return gold_fanout_questions()


def sleeve_select_question(members: list[str] | tuple[str, ...] | None) -> dict[str, Any]:
    """Choice among the named sleeves on this unit, plus none. Same POST.

    The bound is the sleeve_select_cap score on this post. This function
    does not cut the list at a printed count.
    """
    names: list[str] = []
    seen: set[str] = set()
    for raw in members or ():
        name = str(raw or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    if not names:
        return {}
    criteria = {name: f"Named sleeve {name} wins this unit" for name in names}
    criteria["none"] = "No named sleeve in this unit deserves the fire"
    packed = spot_question(
        "sleeve_select",
        "Which named sleeve in this unit takes the fire? The criteria keys are the sleeves on this unit. "
        "The unique highest probability is the sleeve. An empty answer or a tie leaves the sleeve unset.",
        criteria,
    )
    counted = count_anchors({"n_sleeves": len(names), "sleeve_members": list(names)})
    packed.update(amount_question(
        "sleeve_select_cap",
        "How many named sleeves belong on this choice? "
        "The score you return is that bound. It may sit between the levels. "
        "An empty score leaves the bound unset.",
        counted,
    ))
    return packed


def schema_at_depth(question: Mapping[str, Any], depth: str) -> dict[str, Any] | None:
    """Score include-depth on one schema. hide / short / long / full.

    Not a Noul keep/drop: hide means this *query* does not need the chunk.
    """
    if depth not in INCLUDE_DEPTH:
        raise ValueError(f"include_depth must be one of {INCLUDE_DEPTH}, got {depth!r}")
    if depth == "hide":
        return None
    if depth == "full":
        return dict(question)
    if depth == "long":
        out: dict[str, Any] = {}
        if "type" in question:
            out["type"] = question["type"]
        if "instructions" in question:
            out["instructions"] = question["instructions"]
        return out
    # short — directional snippet so the model knows the action *could* exist
    instr = str(question.get("instructions") or "").strip()
    first = instr.split(".")[0].strip() if instr else ""
    snippet: dict[str, Any] = {}
    if "type" in question:
        snippet["type"] = question["type"]
    if first:
        snippet["instructions"] = first
    return snippet


def question_subtree(
    *nodes: str,
    depth: str = "full",
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Dump schema for nested seats or leaf IDs (hierarchical function-calling).

    Code picks the subtree (the query). This does not score each ID and drop
    the rest — that linear keep/drop is the founder anti-pattern.
    ``depth`` is Score include-depth for the dumped schema.
    """
    if depth not in INCLUDE_DEPTH:
        raise ValueError(f"include_depth must be one of {INCLUDE_DEPTH}, got {depth!r}")
    if depth == "hide":
        return {}
    gold = dict(catalog) if catalog is not None else gold_fanout_questions()
    ids: list[str] = []
    seen: set[str] = set()
    for node in nodes:
        name = str(node or "").strip()
        if not name:
            continue
        branch = QUESTION_TREE.get(name)
        if isinstance(branch, dict) and "ids" in branch:
            leaves = list(branch["ids"] or ())
        else:
            leaves = (name,)
        for qid in leaves:
            if qid in seen:
                continue
            if qid not in gold:
                continue
            seen.add(qid)
            ids.append(qid)
    packed: dict[str, Any] = {}
    for qid in ids:
        rendered = schema_at_depth(gold[qid], depth)
        if rendered is not None:
            packed[qid] = rendered
    return packed


def hierarchical_labels(
    state: Mapping[str, Any] | None = None,
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Nested labels of the current fire. Tree-search, not a flat transcript."""
    state = state or {}
    identity = state.get("identity") if isinstance(state.get("identity"), Mapping) else {}
    clock = state.get("clock") if isinstance(state.get("clock"), Mapping) else {}
    extra = dict(extra or {})
    ticket = extra.get("ticket")
    if ticket is None:
        ticket = identity.get("ticket")
    account = state.get("account") if isinstance(state.get("account"), Mapping) else {}
    occupancy = state.get("occupancy") if isinstance(state.get("occupancy"), Mapping) else {}
    if extra.get("occupancy") and isinstance(extra.get("occupancy"), Mapping):
        occupancy = {**occupancy, **dict(extra.get("occupancy") or {})}
    return {
        "book": {
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "equity": account.get("equity"),
            "terminal_read": account.get("terminal_read"),
            "day_equity": account.get("day_equity"),
            "day_start_balance": account.get("day_start_balance"),
            "day_start_equity": account.get("day_start_equity"),
            "day_start_max": account.get("day_start_max"),
        },
        "fire": {
            "sleeve": identity.get("sleeve"),
            "symbol": identity.get("symbol"),
            "side": identity.get("side"),
            "family_class": identity.get("family_class"),
            "candidate_id": identity.get("candidate_id"),
        },
        "when": {
            "as_of_utc": clock.get("as_of_utc"),
            "decision_day": identity.get("decision_day"),
            "decision_bar_iso": identity.get("decision_bar_iso"),
        },
        "occupancy": {
            "symbol_open": occupancy.get("symbol_open"),
            "symbol_pending": occupancy.get("symbol_pending") or occupancy.get("pending"),
            "already_placed_today": occupancy.get("already_placed_today"),
            "isolated_reentry_legal": occupancy.get("isolated_reentry_legal"),
            "minutes_since_flat": occupancy.get("minutes_since_flat"),
            "two_stop_exhausted": occupancy.get("two_stop_exhausted"),
            "keep_one_symbol": occupancy.get("keep_one_symbol"),
        },
        "ticket": ticket,
        "subgoal": extra.get("subgoal") or identity.get("subgoal"),
    }


def _sleeve_branches(
    seat: str | tuple[str, ...] | None,
    questions: dict[str, Any] | None,
) -> tuple[str, ...]:
    """Pick the sleeve schema branch for this POST. Fire does not dump exit.

    Remaining packs (place-wall / remint / sleeve_emit) dump THAT subtree
    only — occupancy is not a second keep/drop of the sleeve fire schema.
    """
    if isinstance(seat, tuple):
        out: list[str] = []
        if any(name in seat for name in ("gate", "admission", "sleeve")):
            out.append("fire")
        if "size" in seat:
            out.append("size")
        if "close" in seat:
            out.append("exit")
        if "remaining" in seat and not out:
            return ()
        return tuple(out) or ("fire",)
    if seat == "size":
        return ("size",)
    if seat == "close":
        return ("exit",)
    if seat == "remaining":
        return ()
    if seat in {"gate", "admission", "sleeve"}:
        return ("fire",)
    if questions:
        keys = set(questions)
        remaining_keys = {
            "isolated_reentry_is_new",
            "cluster_same_day",
            "restart_chase",
            "remint_authorize",
            "sleeve_emit",
        }
        if keys & remaining_keys:
            return ()
        branches: list[str] = []
        if keys & {"conviction_vs_tape", "ac60_size", "sleeve_size_depth"}:
            branches.append("size")
        if "exit_class" in keys or "exit_profile_fit" in keys:
            branches.append("exit")
        if branches:
            return tuple(branches)
    return ("fire",)


def _merge_sleeve_subtree(
    state: Mapping[str, Any] | None,
    packed: dict[str, Any],
    *,
    include_depth: str,
    seat: str | tuple[str, ...] | None,
    questions: dict[str, Any] | None,
    merge_sleeve: bool | None = None,
) -> dict[str, Any]:
    """Fold this fire's sleeve schema into the same POST (standalone=False).

    Live seats / explicit packs only. Unlabeled dumps are the gate subtree.
    Gold IDs win on collision; caller extra_questions still overlay after.
    Hide is hide — do not sneak sleeve Scores back in.
    Branch is hierarchical function-calling: fire does not dump exit schema.
    Remaining include-depth hops pass ``merge_sleeve=False`` so occupancy
    packs stay that subtree, not a second keep/drop of the sleeve catalog.
    """
    if merge_sleeve is False:
        return packed
    if include_depth == "hide":
        return packed
    resolved_seat: str | tuple[str, ...] | None = seat
    if resolved_seat is None and questions is None:
        resolved_seat = "gate"
    if questions and all(str(key).startswith("include_") for key in questions):
        return packed
    identity = state.get("identity") if isinstance(state, Mapping) else None
    if not isinstance(identity, Mapping):
        return packed
    if not str(identity.get("sleeve") or "").strip():
        return packed
    from .sleeve_ifs import sleeve_subtree_questions

    for branch in _sleeve_branches(resolved_seat, questions):
        extra = sleeve_subtree_questions(state, standalone=False, branch=branch)
        for qid, spec in extra.items():
            if qid in packed:
                continue
            if not isinstance(spec, Mapping):
                continue
            rendered = spec if include_depth == "full" else schema_at_depth(spec, include_depth)
            if rendered is not None:
                packed[qid] = rendered
    return packed


def systemone_payload(
    state: dict[str, Any],
    *,
    model: str = MODEL,
    extra_questions: dict[str, Any] | None = None,
    questions: dict[str, Any] | None = None,
    seat: str | tuple[str, ...] | None = None,
    include_depth: str = "full",
    merge_sleeve: bool | None = None,
) -> dict[str, Any]:
    """One POST /v1/systemone body.

    ``seat`` picks a QUESTION_TREE subtree and dumps that schema.
    ``questions`` is an explicit subtree dump (size/close packs).
    ``extra_questions`` merge into the same call (sleeve_select overlays).
    Named-sleeve live seats also fold ``sleeve_subtree_questions(..., standalone=False)``
    into that same packed body — hierarchical Noul/Score, not a second hop.
    ``include_depth`` is Score hide/short/long/full, not a Noul keep/drop.
    Remaining packs pass ``merge_sleeve=False`` so include-depth / decision
    hops dump THAT subtree only.
    With neither seat nor questions, dump the gate subtree (named hop
    outcomes), not the linear gold catalog.
    The POST ``state`` carries ``account.equity`` and ``account.balance``.
    A missing terminal number stays on that card. The cash parameter is the returned score.
    """
    try:
        from .equity_frame import attach_account

        if isinstance(state, dict):
            state = attach_account(state)
    except Exception:
        state = dict(state or {})
    account = state.get("account") if isinstance(state.get("account"), dict) else {}
    if not all(key in account for key in ("equity", "to_pass", "floor_room")):
        account = dict(account)
        account.setdefault("login", CHALLENGE_LOGIN)
        account.setdefault("equity", None)
        account.setdefault("to_pass", None)
        account.setdefault("floor_room", None)
        account.setdefault("terminal_read", "missing")
        account.setdefault("cash_unit_usd", None)
        account["reason"] = None
        account["invented"] = False
        state["account"] = account
    resolved_seat: str | tuple[str, ...] | None = seat
    if questions is not None:
        if include_depth == "hide":
            packed: dict[str, Any] = {}
        elif include_depth == "full":
            packed = dict(questions)
        else:
            packed = {}
            for key, block in questions.items():
                if isinstance(block, Mapping):
                    rendered = schema_at_depth(block, include_depth)
                    if rendered is not None:
                        packed[key] = rendered
    elif seat:
        nodes = (seat,) if isinstance(seat, str) else tuple(seat)
        packed = question_subtree(*nodes, depth=include_depth)
    else:
        packed = question_subtree("gate", depth=include_depth)
        resolved_seat = "gate"
    packed = _merge_sleeve_subtree(
        state,
        packed,
        include_depth=include_depth,
        seat=resolved_seat,
        questions=questions,
        merge_sleeve=merge_sleeve,
    )
    if extra_questions:
        packed.update(extra_questions)
    if isinstance(state, dict) and "labels" not in state:
        state = {**state, "labels": hierarchical_labels(state)}
    return {"state": state, "model": model, "questions": packed}

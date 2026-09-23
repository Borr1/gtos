"""One Choice hop for a learning rung.

The choice is the unique highest probability System One returns for this
state. Persistence weight and unit cash are the scores on that same ask.
The call is ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only Choice or Score. Prior outcomes are attached on the
ask. An empty answer, a tie, a missing score, or an error leaves that
return unset.

This hop does not build a question whose only purpose is the account floor
or the pass target. A name that only contains those words is still asked.
This hop does not send an order.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"


def read_json(path: Path | str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    file_path = Path(path)
    if not file_path.is_file():
        return None
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def namespace_root(repo_root: Path, namespace: str) -> Path:
    return repo_root / "pipeline_state" / "ultimate_book" / namespace


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _copy_tree(value: Any) -> Any:
    """A copy of the facts. Every key stays, including a name that only contains a limit word."""

    if isinstance(value, dict):
        return {str(key): _copy_tree(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy_tree(item) for item in value]
    return value


def probabilities(answer: Any, criteria: Mapping[str, str]) -> tuple[dict[str, float], str]:
    """Return option → probability and where it was read.

    A bare label is not a probability. An unreadable block stays empty.
    """

    names = {str(name) for name in criteria}
    if not isinstance(answer, dict):
        return {}, "unreadable"
    for key in ("distribution", "probabilities", "probs"):
        raw = answer.get(key)
        if isinstance(raw, dict) and raw:
            out: dict[str, float] = {}
            for name, val in raw.items():
                if str(name) in names:
                    number = _as_float(val)
                    if number is not None:
                        out[str(name)] = number
            if out:
                return out, key
    options = answer.get("options") or answer.get("choices")
    if isinstance(options, list):
        out = {}
        for opt in options:
            if not isinstance(opt, dict):
                continue
            name = opt.get("value") if opt.get("value") is not None else opt.get("name")
            number = _as_float(opt.get("probability", opt.get("prob", opt.get("p"))))
            if name is not None and str(name) in names and number is not None:
                out[str(name)] = number
        if out:
            return out, "options"
    return {}, "unreadable"


def highest(probs: Mapping[str, float]) -> str | None:
    """The single highest-probability option. A tie is not a decision."""

    if not probs:
        return None
    top = max(probs.values())
    winners = [name for name, prob in probs.items() if prob == top]
    if len(winners) != 1:
        return None
    return winners[0]


def _winner(probs: Mapping[str, float], criteria: Mapping[str, str]) -> str | None:
    """Unique highest probability. A tie or a bare label is not a decision."""

    if not probs:
        return None
    order = tuple(str(name) for name in criteria)
    try:
        from .jev_questions import unique_highest

        name = unique_highest(probs, order)
    except Exception:
        name = highest(probs)
    if name is None or str(name) not in probs or str(name) not in {str(item) for item in order}:
        return None
    return str(name)


def _score_of(block: Any) -> float | None:
    """The returned score. A missing score stays missing. It is not snapped to a level."""

    parsed: float | None = None
    try:
        from .jev_questions import returned_number

        parsed = _as_float(returned_number(block))
    except Exception:
        parsed = None
    if parsed is not None:
        return parsed
    if not isinstance(block, dict) or block.get("error"):
        return None
    for key in ("score", "value"):
        if key not in block:
            continue
        number = _as_float(block.get(key))
        if number is not None:
            return number
    return None


def _choice_block(question_id: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any] | None:
    kept = {
        str(key): str(text)
        for key, text in criteria.items()
    }
    if not kept:
        return None
    text = str(instructions).strip()
    block: dict[str, Any] = {
        "type": "choice",
        "instructions": text,
        "criteria": kept,
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(question_id, text, kept)
        row = built.get(question_id) if isinstance(built, dict) else None
        if isinstance(row, dict):
            block = dict(row)
    except Exception:
        pass
    block["type"] = "choice"
    block["instructions"] = text
    block["criteria"] = kept
    return block


def _amount_block(spot: str, instructions: str, anchors: Any) -> dict[str, Any] | None:
    """Amount Score. Fewer than two anchors in that unit does not post."""

    try:
        from .jev_questions import amount_question

        built = amount_question(spot, instructions, anchors)
    except Exception:
        return None
    row = built.get(spot) if isinstance(built, dict) else None
    if not isinstance(row, dict):
        return None
    criteria = row.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return None
    return dict(row)


def rung_questions(
    question_id: str,
    instructions: str,
    criteria: Mapping[str, str],
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The rung Choice plus the weight and the cash. One piece.

    Cash is anchored to the card's own money. The weight is anchored to the
    card's own weights. A missing scale leaves that Score off the post.
    """

    pack: dict[str, Any] = {}
    choice = _choice_block(str(question_id), instructions, criteria)
    if choice is not None:
        pack[str(question_id)] = choice
    try:
        from .jev_questions import usd_anchors, weight_anchors

        money = usd_anchors(state)
        weights = weight_anchors(state)
    except Exception:
        money = []
        weights = []
    weight = _amount_block(
        "persist_weight",
        "Given the facts and prior_outcomes on this state, what weight does "
        "persistence carry on this learning rung? The score you return is that "
        "weight. It may sit between levels. An empty score leaves the weight "
        "unset. Do not send.",
        weights,
    )
    if weight is not None:
        pack["persist_weight"] = weight
    cash = _amount_block(
        "unit_usd",
        "Given the facts and prior_outcomes on this state, what cash does this "
        "learning unit name? The score you return is that cash. It may sit "
        "between levels. An empty score leaves the cash unset. Do not send.",
        money,
    )
    if cash is not None:
        pack["unit_usd"] = cash
    return {
        key: value
        for key, value in pack.items()
        if isinstance(value, dict) and value.get("type") in {"choice", "score", "noul"}
    }


def _posted_state(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """Facts for the ask. Prior outcomes are history. Every key on the card stays."""

    raw = dict(state) if isinstance(state, Mapping) else {}
    posted = _copy_tree(raw)
    if not isinstance(posted, dict):
        posted = {}
    posted.pop("persist_weight", None)
    posted.pop("unit_usd", None)
    posted.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=posted, questions=questions)
    except Exception:
        loaded = []
    posted["prior_outcomes"] = loaded if isinstance(loaded, list) else []
    plain = jsonable(posted)
    return plain if isinstance(plain, dict) else {}


def _remember(
    state: Mapping[str, Any],
    question_id: str,
    choice: Any,
    persist: float | None,
    unit: float | None,
    error: str | None,
    *,
    asked_choice: bool,
) -> None:
    """The return is the next ask's history. A miss is stored as a miss."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    pairs: list[tuple[str, Any, bool]] = []
    if asked_choice:
        pairs.append((question_id, choice, choice is None))
    pairs.append(("persist_weight", persist, persist is None))
    pairs.append(("unit_usd", unit, unit is None))
    for key, value, failed in pairs:
        try:
            append_outcome(key, value, state, error=error if failed else None)
        except Exception:
            return


def ask_choice(
    state: Mapping[str, Any],
    *,
    question_id: str,
    instructions: str,
    criteria: Mapping[str, str],
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One evaluate call. The choice and the parameters are that return.

    A parameter already returned for these facts is not a second call. It
    comes back on this receipt. An empty answer, a tie, or an error does
    not restore a constant. The deadline is the expiry already on the state.
    This hop does not send.
    """

    del timeout_s
    base = {
        "asked": True,
        "ok": False,
        "question_id": question_id,
        "model": MODEL,
        "choice": None,
        "probability": None,
        "probabilities": {},
        "probability_source": None,
        "order_send": False,
        "never_place": True,
        "persist_weight": None,
        "unit_usd": None,
        "extra_pass": False,
        "decision_emitted": False,
        "http_status": None,
        "error": None,
        "key_source": None,
    }
    questions = rung_questions(question_id, instructions, criteria, state)
    asked_choice = str(question_id) in questions
    try:
        posted = _posted_state(state, questions)
    except Exception as exc:  # noqa: BLE001 — hop must not raise into a writer
        base["error"] = type(exc).__name__
        return base
    try:
        from .jev_client import evaluate
    except Exception as exc:  # noqa: BLE001
        base["error"] = type(exc).__name__
        return base
    try:
        receipt = evaluate(
            posted,
            questions=questions,
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001
        base["error"] = type(exc).__name__
        _remember(posted, str(question_id), None, None, None, base["error"], asked_choice=asked_choice)
        return base
    if not isinstance(receipt, dict):
        receipt = {}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    base["http_status"] = receipt.get("http_status")
    base["key_source"] = receipt.get("key_source")
    base["model"] = receipt.get("model") or MODEL
    error = receipt.get("error") or receipt.get("skipped")
    probs, source_name = probabilities(answers.get(question_id), criteria)
    winner = _winner(probs, criteria) if asked_choice else None
    persist = _score_of(answers.get("persist_weight"))
    unit = _score_of(answers.get("unit_usd"))
    base["probabilities"] = probs
    base["probability_source"] = source_name if probs else None
    base["persist_weight"] = persist
    base["unit_usd"] = unit
    if winner is None:
        if error:
            base["error"] = str(error)
        elif not answers:
            base["error"] = "empty"
        else:
            base["error"] = "no_unique_highest"
        _remember(
            posted,
            str(question_id),
            None,
            persist,
            unit,
            base["error"],
            asked_choice=asked_choice,
        )
        return base
    base["ok"] = True
    base["choice"] = winner
    base["probability"] = probs.get(winner)
    base["decision_emitted"] = True
    base["error"] = None
    _remember(posted, str(question_id), winner, persist, unit, None, asked_choice=True)
    return base


_FILE_CACHE: dict[str, tuple[int, int, dict[str, Any] | None]] = {}


def _cached_json(path: Path) -> dict[str, Any] | None:
    """The parsed file. An unchanged size and mtime is not read again."""

    key = str(path)
    try:
        stat = path.stat()
    except OSError:
        _FILE_CACHE.pop(key, None)
        return None
    stamp = (stat.st_mtime_ns, stat.st_size)
    hit = _FILE_CACHE.get(key)
    if hit is not None and hit[0] == stamp[0] and hit[1] == stamp[1]:
        return hit[2]
    row = read_json(path)
    parsed = row if isinstance(row, dict) else None
    _FILE_CACHE[key] = (stamp[0], stamp[1], parsed)
    return parsed


def open_pair(root: Path) -> dict[str, Any]:
    """Facts about an open position. Does not close or resize it."""

    records = root / "trade_records"
    if records.is_dir():
        files = list(records.glob("*.json"))
        present = {str(path) for path in files}
        for cached in list(_FILE_CACHE):
            if cached.startswith(str(records)) and cached not in present:
                _FILE_CACHE.pop(cached, None)
        newest: dict[str, Any] | None = None
        newest_ticket: Any = None
        newest_mtime: int | None = None
        for file_path in files:
            try:
                mtime = file_path.stat().st_mtime_ns
            except OSError:
                continue
            row = _cached_json(file_path)
            if not isinstance(row, dict):
                continue
            status = str(row.get("trade_lifecycle_status") or row.get("status") or "").lower()
            if status != "open":
                continue
            if newest_mtime is not None and mtime < newest_mtime:
                continue
            newest_mtime = mtime
            newest = row
            newest_ticket = row.get("ticket") or file_path.stem
        if newest is not None:
            return {
                "pair_present": True,
                "symbol": newest.get("symbol"),
                "sleeve": newest.get("sleeve") or newest.get("sleeve_name"),
                "ticket": newest_ticket,
                "status": "open",
            }
    found: list[dict[str, Any]] = []

    def walk(node: Any, seen: set[int]) -> None:
        if isinstance(node, (dict, list)):
            ident = id(node)
            if ident in seen:
                return
            seen.add(ident)
        if isinstance(node, dict):
            symbol = node.get("symbol")
            sleeve = node.get("sleeve") or node.get("sleeve_name") or node.get("tag")
            ticket = node.get("ticket") or node.get("position_id") or node.get("position")
            status = str(
                node.get("trade_lifecycle_status") or node.get("status") or ""
            ).lower()
            if symbol and (sleeve or status in {"open", "occupied"} or node.get("occupied") is True):
                found.append(
                    {
                        "symbol": symbol,
                        "sleeve": sleeve,
                        "ticket": ticket,
                        "status": status or None,
                    }
                )
            for value in node.values():
                walk(value, seen)
        elif isinstance(node, list):
            for item in node:
                walk(item, seen)

    for name in ("chair_health.json", "heartbeat.json"):
        walk(_cached_json(root / name), set())
    open_rows = [
        row
        for row in found
        if row.get("status") in {"open", "occupied"} or row.get("sleeve")
    ]
    chosen = open_rows[0] if open_rows else None
    if chosen is None:
        return {"pair_present": False}
    return {
        "pair_present": True,
        "symbol": chosen.get("symbol"),
        "sleeve": chosen.get("sleeve"),
        "ticket": chosen.get("ticket"),
        "status": chosen.get("status"),
    }


def append_record(path: Path, row: Mapping[str, Any]) -> bool:
    """Append a real Choice. Returns False when nothing was written."""

    if not row.get("decision_emitted"):
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(jsonable(dict(row)), sort_keys=True) + "\n")
    except OSError:
        return False
    return True


CHALLENGE_LOGIN_TEXT = "0"
CHALLENGE_NS_TEXT = "operator"


def learning_unit_state(rung: str, repo_root: Path | None = None) -> tuple[Path, dict[str, Any]]:
    """Facts for one learning-rung Choice. Does not decide and does not send."""

    root = repo_root or Path(__file__).resolve().parents[2]
    ns_root = namespace_root(root, CHALLENGE_NS_TEXT)
    heartbeat = read_json(ns_root / "heartbeat.json") or {}
    pointer = read_json(ns_root / "judgment" / "state" / "latest_slate.json") or {}
    slate = read_json(pointer.get("path")) if pointer.get("path") else None
    slate_dict = slate if isinstance(slate, dict) else None
    n_candidates = len((slate_dict or {}).get("candidates") or [])
    pair = _pair_facts(ns_root, slate_dict)
    state = {
        "rung": rung,
        "login": CHALLENGE_LOGIN_TEXT,
        "namespace": heartbeat.get("namespace") or CHALLENGE_NS_TEXT,
        "writer_pid": heartbeat.get("pid"),
        "writer_healthy": heartbeat.get("healthy"),
        "writer_heartbeat_ts": heartbeat.get("ts"),
        "friends_role": "copy_only",
        "redacted_account": "idle",
        "slate_id": pointer.get("slate_id"),
        "fingerprint": pointer.get("fingerprint"),
        "n_candidates": n_candidates,
        "pair": pair,
    }
    cleaned = _copy_tree(state)
    return ns_root, cleaned if isinstance(cleaned, dict) else {}


def _pair_facts(ns_root: Path, slate: dict[str, Any] | None) -> dict[str, Any]:
    base = open_pair(ns_root)
    ticket = base.get("ticket")
    rec = read_json(ns_root / "trade_records" / f"{ticket}.json") if ticket else None
    rec = rec if isinstance(rec, dict) else {}
    execution = rec.get("execution") if isinstance(rec.get("execution"), dict) else {}
    inst = rec.get("instrumentation") if isinstance(rec.get("instrumentation"), dict) else {}
    geo = inst.get("gtos_live_flow_broker_geometry")
    geo = geo if isinstance(geo, dict) else {}
    slate_open: dict[str, Any] = {}
    if isinstance(slate, dict):
        for row in slate.get("open_positions") or []:
            if isinstance(row, dict) and str(row.get("ticket")) == str(ticket):
                slate_open = row
                break
    volume = geo.get("lots_normalized")
    if volume is None:
        volume = slate_open.get("current_volume")
    stop = execution.get("broker_position_sl")
    if stop is None:
        stop = slate_open.get("stop_now")
    entry = execution.get("broker_position_price_open")
    if entry is None:
        entry = slate_open.get("entry_price")
    take_profit = execution.get("broker_position_tp")
    if take_profit is None:
        take_profit = slate_open.get("take_profit_1")
    return {
        "pair_present": bool(base.get("pair_present")),
        "ticket": ticket,
        "symbol": rec.get("symbol") or base.get("symbol") or slate_open.get("symbol"),
        "sleeve": rec.get("sleeve") or base.get("sleeve") or slate_open.get("sleeve"),
        "status": rec.get("trade_lifecycle_status") or base.get("status"),
        "direction": inst.get("direction") or slate_open.get("direction"),
        "volume": volume,
        "stop": stop,
        "entry": entry,
        "take_profit": take_profit,
        "locked_r": slate_open.get("locked_r"),
    }


def note_load_error(rung: str, exc: BaseException) -> None:
    """A failed ask is not a label."""

    try:
        path = namespace_root(Path(__file__).resolve().parents[2], CHALLENGE_NS_TEXT) / "judgment" / "rung_choice" / "load_error.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {"rung": rung, "error": type(exc).__name__, "detail": str(exc), "choice": None}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
    except OSError:
        return


def finish_learning_choice(
    ns_root: Path,
    rung: str,
    question_id: str,
    hop: Mapping[str, Any],
    allowed: Mapping[str, str],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The unique highest probability is the decision. Weight and cash are the scores on that hop."""

    choice = hop.get("choice")
    emitted = bool(hop.get("decision_emitted")) and choice in set(allowed)
    row = dict(hop)
    row.update(
        {
            "rung": rung,
            "question_id": question_id,
            "choice": choice if emitted else None,
            "probability": hop.get("probability") if emitted else None,
            "login": CHALLENGE_LOGIN_TEXT,
            "namespace": CHALLENGE_NS_TEXT,
            "persist_weight": hop.get("persist_weight"),
            "unit_usd": hop.get("unit_usd"),
            "friends_role": "copy_only",
            "decision_emitted": emitted,
            "pid": __import__("os").getpid(),
        }
    )
    if extra:
        row.update(dict(extra))
    if emitted and "apply" in str(choice).lower():
        row["apply"] = True
    if not emitted:
        row["ok"] = False
    else:
        append_record(ns_root / "judgment" / "rung_choice" / f"{rung}.jsonl", row)
    return row

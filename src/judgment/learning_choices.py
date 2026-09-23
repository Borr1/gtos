"""Learning decisions are the System One return for that state.

Each choice is the unique highest probability. Each parameter is the Score
on that state and may sit between the levels. One hop per state is
``jev_client.evaluate`` with model ``jev-1.13.0`` and ``merge_sleeve=False``
(POST https://api.typesafe.ai/v1/systemone). Questions are only Choice or
Score. Every closed Challenge outcome is on the card, and the return is
appended for the next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset and does not restore a constant. A floor and a baseline are facts
on the card, not a cap and not a refusal. This module does not send an
order and does not flatten open gold 294215389.
"""

from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.learning_choices.v1"
NEVER_FLATTEN_TICKET = "294215389"

# Importers still compare with ``is LEGACY``. A miss is None, not this sentinel.
LEGACY = object()

_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
# Column order for the compact close card. Named dicts of every close do not
# fit one post. A missing realized number stays null and is not written as 0.
_LIVE_FIELDS = ("ticket", "symbol", "sleeve", "close_action", "realized", "plan_r")

_SPECS: dict[str, dict[str, Any]] = {
    "learn_loop.asset_class": {
        "order": ("XAU", "CRYPTO", "INDEX", "FX", "OTHER"),
        "parameter": "asset-class parameter",
        "instructions": (
            "Learning question: the asset class of the symbol on this state. "
            "The symbol is a fact. Closed outcomes on this state are facts."
        ),
        "criteria": {
            "XAU": "The symbol is XAU, GOLD, or an XAU stem.",
            "CRYPTO": "The symbol is BTC or ETH.",
            "INDEX": (
                "The symbol is a cash index stem "
                "(US30, UK100, US500, NAS100, US100, USTEC, GER40, DE40, JP225)."
            ),
            "FX": "The symbol is a six-letter alphabetic FX pair.",
            "OTHER": "The symbol is empty or outside XAU, crypto, index, and FX.",
        },
    },
    "learn_loop.exit_other": {
        "order": ("other", "locked_exit"),
        "parameter": "exit parameter",
        "instructions": (
            "Learning question: the named exit on this state. "
            "Closed outcomes on this state are facts. "
            "A tie does not relabel the exit."
        ),
        "criteria": {
            "other": (
                "The named exit is outside orig_stop, orig_tp, time_stop, "
                "and breach_flatten."
            ),
            "locked_exit": (
                "The named exit is orig_stop, orig_tp, time_stop, or breach_flatten."
            ),
        },
    },
    "learn_loop.promotion": {
        "order": (
            "event_gap",
            "ok_win",
            "false_structure",
            "time_stop",
            "orig_tp",
            "orig_stop",
        ),
        "parameter": "promotion parameter",
        "instructions": (
            "Learning question: the promotion branch for the miss type and "
            "exit class on this state. Closed outcomes on this state are facts."
        ),
        "criteria": {
            "event_gap": "miss_type is event_gap.",
            "ok_win": "miss_type is ok_win.",
            "false_structure": "miss_type is false_structure.",
            "time_stop": "exit_class is time_stop.",
            "orig_tp": "exit_class is orig_tp.",
            "orig_stop": "exit_class is orig_stop.",
        },
    },
    "trained_models.asset_bucket": {
        "order": ("XAU", "other"),
        "parameter": "bucket parameter",
        "instructions": (
            "Trained-model question: the asset bucket of the symbol on this state. "
            "Closed outcomes on this state are facts."
        ),
        "criteria": {
            "XAU": "The symbol starts with XAU or equals GOLD.",
            "other": "The symbol does not start with XAU and is not GOLD.",
        },
    },
    "trained_models.plan_r_bin": {
        "order": ("missing", "ge4", "ge2", "lt2"),
        "parameter": "plan_r edge",
        "instructions": (
            "Trained-model question: which plan_r bin this state is in. "
            "The edge is the paired score, not a printed cut. "
            "Closed outcomes on this state are facts."
        ),
        "criteria": {
            "missing": "plan_r is missing on this state.",
            "ge4": "plan_r sits in the upper bin. The edge is the returned score.",
            "ge2": "plan_r sits in the middle bin. The edge is the returned score.",
            "lt2": "plan_r is present and sits in the lower bin. The edge is the returned score.",
        },
    },
    "trained_models.chair_label": {
        "order": ("HARD_OFF", "KEEP", "STUDY", "STARVE", "WATCH"),
        "parameter": "chair-label parameter",
        "instructions": (
            "Trained-model question: the chair label for the family, the "
            "hard-off fact, and the symbol on this state. "
            "Closed outcomes on this state are facts."
        ),
        "criteria": {
            "HARD_OFF": (
                "The family is house_hard_off, or hard_off_family is set, "
                "or the symbol starts with US30."
            ),
            "KEEP": "The family is house_keep.",
            "STUDY": "The family is study.",
            "STARVE": "The family is starve_watch.",
            "WATCH": "This geometry is outside hard-off, house-keep, study, and starve-watch.",
        },
    },
    "daily_loop.quiet_action": {
        "order": (
            "keep_family",
            "hard_off_family",
            "quiet_study",
            "dsp_starve",
            "house_keep",
            "house_hard_off",
            "starve_watch",
            "a_plus_study",
            "watch_residual",
        ),
        "parameter": "quiet-action parameter",
        "instructions": (
            "Daily-path question: the quiet action for the sleeve, symbol, "
            "and family class on this state. Closed outcomes on this state are facts."
        ),
        "criteria": {
            "keep_family": "This sleeve is a house keep-family or a Challenge keep-family prefix.",
            "hard_off_family": "This sleeve is a house hard-off family for this symbol.",
            "quiet_study": "This sleeve starts with dsp_three_fre or dsp_three_fresh.",
            "dsp_starve": "This sleeve starts with dsp_ and sits outside the quiet-study prefixes.",
            "house_keep": "The family class is house_keep.",
            "house_hard_off": "The family class is house_hard_off.",
            "starve_watch": "The family class is starve_watch.",
            "a_plus_study": "The family class is a_plus_study.",
            "watch_residual": (
                "This sleeve is outside keep, hard-off, quiet-study, "
                "dsp-starve, and the named family classes."
            ),
        },
    },
    "trained_models.keep_surface": {
        "order": ("KEEP", "other"),
        "parameter": "keep-surface parameter",
        "instructions": "Trained-model question: whether this sleeve or family is a keep surface.",
        "criteria": {
            "KEEP": "The sleeve or family is a spring, vss, vss_fxcross, or sub_mid keep surface.",
            "other": "The sleeve and family are outside those keep surfaces.",
        },
    },
}

_LIVE_LOCK = threading.Lock()
_LIVE_CACHE: dict[str, Any] = {"stamp": None, "cards": []}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _copy(value: Any) -> Any:
    """Copy the card. Keys and text stay. Nothing is dropped for its name."""

    if isinstance(value, Mapping):
        return {str(key): _copy(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy(item) for item in value]
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


def _count(value: Any) -> int | float | None:
    number = _finite(value)
    if number is None:
        return None
    if number.is_integer():
        return int(number)
    return number


def _parameter_levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on the facts. A score may sit between them."""

    found: list[float] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for child in value.values():
                walk(child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(item)
            return
        number = _finite(value)
        if number is not None:
            found.append(number)

    for value in dict(facts or {}).values():
        walk(value)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_text(spec: Mapping[str, Any]) -> str:
    return (
        str(spec["instructions"]).strip()
        + " Pick one option. The unique highest probability is the decision."
        + " The parameter is the score on the paired question and may sit between the levels."
        + " An empty answer or a tie leaves the choice unset."
        + " A floor and a baseline are not a question."
        + " Do not send an order. Do not flatten the open gold ticket."
    )


def _score_text(spec: Mapping[str, Any]) -> str:
    noun = str(spec["parameter"])
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the parameter unset. "
        "A floor and a baseline are not a question. "
        "Do not send an order. Do not flatten the open gold ticket."
    )


def _question_pack(spot: str) -> dict[str, Any]:
    spec = _SPECS[spot]
    order = tuple(spec["order"])
    criteria = {str(name): str(spec["criteria"][name]) for name in order}
    choice_text = _choice_text(spec)
    score_text = _score_text(spec)
    param_id = spot + "_parameter"
    pack: dict[str, Any] | None = None
    try:
        from .jev_questions import parameter_question, spot_question

        built = spot_question(spot, choice_text, criteria)
        extra = parameter_question(param_id, score_text)
        if isinstance(built, Mapping) and isinstance(extra, Mapping):
            pack = {}
            for key, value in dict(built).items():
                pack[str(key)] = dict(value) if isinstance(value, Mapping) else value
            for key, value in dict(extra).items():
                pack[str(key)] = dict(value) if isinstance(value, Mapping) else value
    except Exception:
        pack = None
    if not isinstance(pack, dict):
        pack = {}
    choice_q = pack.get(spot)
    if not isinstance(choice_q, dict):
        choice_q = {}
        pack[spot] = choice_q
    choice_q["type"] = "choice"
    choice_q["instructions"] = choice_text
    choice_q["criteria"] = criteria
    param_q = pack.get(param_id)
    if not isinstance(param_q, dict):
        param_q = {}
        pack[param_id] = param_q
    param_q["type"] = "score"
    param_q["instructions"] = score_text
    param_q["criteria"] = list(_BETWEEN)
    return pack


def _local_unique(probabilities: Mapping[str, Any], order: tuple[str, ...]) -> str | None:
    numeric: dict[str, float] = {}
    for name in order:
        if name not in probabilities:
            continue
        number = _finite(probabilities.get(name))
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return None
    best_p: float | None = None
    winners: list[str] = []
    for name in order:
        if name not in numeric:
            continue
        number = numeric[name]
        if best_p is None or number > best_p:
            best_p = number
            winners = [name]
        elif number == best_p:
            winners.append(name)
    if len(winners) != 1:
        return None
    return winners[0]


def _unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    try:
        from .jev_questions import unique_highest
    except Exception:
        return _local_unique(probabilities, order)
    try:
        picked = unique_highest(probabilities, order)
    except Exception:
        return _local_unique(probabilities, order)
    if picked is None or str(picked) not in order:
        return None
    return str(picked)


def _score(block: Any) -> float | None:
    if not isinstance(block, Mapping) or not block:
        return None
    number: Any = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    parsed = _finite(number)
    if parsed is not None:
        return parsed
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _finite(raw)


def _blank() -> dict[str, Any]:
    return {
        "choice": None,
        "parameter": None,
        "probabilities": {},
        "decision_emitted": False,
        "error": None,
        "model": MODEL,
    }


def _answers_of(hop: Mapping[str, Any], spot: str) -> dict[str, Any]:
    answers = hop.get("answers")
    if isinstance(answers, dict):
        return answers
    if isinstance(hop.get("probabilities"), dict) or "score" in hop or "value" in hop:
        return {spot: dict(hop)}
    return {}


def _read_return(hop: Mapping[str, Any], spot: str, order: tuple[str, ...]) -> dict[str, Any]:
    """Choice and parameter from this hop. A miss stays unset."""

    row = _blank()
    if hop.get("model"):
        row["model"] = hop.get("model")
    if hop.get("ok") is False:
        row["error"] = str(hop.get("error") or hop.get("skipped") or "empty")
        return row
    answers = _answers_of(hop, spot)
    if not answers:
        row["error"] = str(hop.get("error") or hop.get("skipped") or "empty")
        return row
    choice_block = answers.get(spot)
    score_block = answers.get(spot + "_parameter")
    if not isinstance(choice_block, dict):
        choice_block = {}
    if not isinstance(score_block, dict):
        score_block = {}
    probs_raw = choice_block.get("probabilities")
    probs = probs_raw if isinstance(probs_raw, Mapping) else {}
    kept = {
        str(name): value
        for name, value in probs.items()
        if str(name) in order and _finite(value) is not None
    }
    choice = _unique(probs, order)
    row["probabilities"] = kept
    row["choice"] = choice
    row["parameter"] = _score(score_block) if score_block else None
    row["decision_emitted"] = choice is not None
    if choice is None:
        row["error"] = "tie_or_empty"
    return row


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = []


def _remember(state: Mapping[str, Any], spot: str, row: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    choice_error = None if row.get("choice") is not None else (row.get("error") or "tie_or_empty")
    score_error = None if row.get("parameter") is not None else (row.get("error") or "score_missing")
    with _LIVE_LOCK:
        try:
            append_outcome(spot, row.get("choice"), state, error=choice_error)
            append_outcome(spot + "_parameter", row.get("parameter"), state, error=score_error)
        except Exception:
            return


def _ns_root(root: Path) -> Path:
    return root / "pipeline_state" / "ultimate_book" / CHALLENGE_NS


def _pick(rec: Mapping[str, Any], *keys: str) -> Any:
    sources: list[Mapping[str, Any]] = [rec]
    for name in ("execution", "instrumentation"):
        block = rec.get(name)
        if isinstance(block, Mapping):
            sources.append(block)
    for source in sources:
        for key in keys:
            if key not in source:
                continue
            value = source.get(key)
            if value not in (None, ""):
                return value
    return None


def _close_card(rec: Mapping[str, Any], ticket: str) -> dict[str, Any] | None:
    status = rec.get("trade_lifecycle_status")
    closed_at = _pick(rec, "closed_at_utc", "closed_utc", "broker_exit_time_utc")
    if status != "closed" and closed_at in (None, ""):
        return None
    realized = _finite(
        _pick(
            rec,
            "broker_realized_pnl",
            "broker_position_realized_pnl",
            "broker_selected_exit_realized_pnl",
            "broker_net_pnl_usd",
        )
    )
    card: dict[str, Any] = {
        "ticket": str(ticket),
        "symbol": _pick(rec, "symbol", "broker_symbol"),
        "sleeve": _pick(rec, "sleeve", "sleeve_name"),
        "close_action": _pick(rec, "close_action", "reason"),
        "closed_at_utc": closed_at,
        "realized": realized,
        "realised_r": _finite(_pick(rec, "realised_r", "R")),
        "plan_r": _finite(_pick(rec, "plan_r", "broker_position_planned_target_r")),
        "miss_type": _pick(rec, "miss_type"),
        "exit_class": _pick(rec, "exit_class"),
        "family_class": _pick(rec, "family_class"),
        "hard_off_family": _pick(rec, "hard_off_family"),
    }
    return {key: value for key, value in card.items() if value is not None}


def _sibling_cards(root: Path) -> list[dict[str, Any]]:
    path = _ns_root(root) / "judgment" / "state" / "just_closed_siblings.json"
    doc = _read_json(path) or {}
    rows = doc.get("closed") if isinstance(doc.get("closed"), list) else []
    cards: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        ticket = item.get("ticket")
        if ticket in (None, "", 0, "0"):
            continue
        card = _close_card(item, str(ticket))
        if card is None:
            card = {
                "ticket": str(ticket),
                "symbol": item.get("symbol"),
                "sleeve": item.get("sleeve"),
                "close_action": item.get("close_action") or item.get("reason"),
                "closed_at_utc": item.get("closed_utc"),
                "realized": _finite(item.get("broker_net_pnl_usd")),
                "realised_r": _finite(item.get("realised_r")),
            }
            card = {key: value for key, value in card.items() if value is not None}
        if card:
            cards.append(card)
    return cards


def _record_cards(root: Path) -> list[dict[str, Any]]:
    folder = _ns_root(root) / "trade_records"
    if not folder.is_dir():
        return []
    cards: list[dict[str, Any]] = []
    for path in folder.glob("*.json"):
        rec = _read_json(path)
        if not isinstance(rec, dict):
            continue
        card = _close_card(rec, path.stem)
        if card is not None:
            cards.append(card)
    return cards


def _merge_cards(records: list[dict[str, Any]], siblings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_ticket: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for card in records + siblings:
        ticket = str(card.get("ticket") or "")
        if not ticket:
            continue
        current = by_ticket.get(ticket)
        if current is None:
            by_ticket[ticket] = dict(card)
            order.append(ticket)
            continue
        for key, value in card.items():
            if current.get(key) is None and value is not None:
                current[key] = value
    cards = [by_ticket[ticket] for ticket in order]
    cards.sort(key=lambda card: str(card.get("closed_at_utc") or ""))
    return cards


def _live_stamp(root: Path) -> tuple[Any, ...]:
    folder = _ns_root(root) / "trade_records"
    sibling = _ns_root(root) / "judgment" / "state" / "just_closed_siblings.json"
    newest = 0.0
    count = 0
    if folder.is_dir():
        for path in folder.glob("*.json"):
            count += 1
            try:
                newest = max(newest, path.stat().st_mtime)
            except OSError:
                continue
    sib_mtime = 0.0
    if sibling.is_file():
        try:
            sib_mtime = sibling.stat().st_mtime
        except OSError:
            sib_mtime = 0.0
    return (count, newest, sib_mtime)


def _live_spot(card: Mapping[str, Any]) -> str:
    return "live_close:%s:%s:%s:%s" % (
        card.get("ticket") or "",
        card.get("symbol") or "",
        card.get("sleeve") or "",
        card.get("close_action") or "",
    )


def _value_token(value: Any) -> str:
    number = _finite(value)
    if number is None:
        return ""
    return format(number, ".10g")


def _logged_live(root: Path) -> set[tuple[str, str]]:
    path = _ns_root(root) / "judgment" / "parameter_outcomes.jsonl"
    found: set[tuple[str, str]] = set()
    if not path.is_file():
        return found
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return found
    for line in lines:
        line = line.strip()
        if not line.startswith("{") or ("live_close:" not in line and "live_plan:" not in line):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        spot = str(row.get("spot") or "")
        if not (spot.startswith("live_close:") or spot.startswith("live_plan:")):
            continue
        found.add((spot, _value_token(row.get("value"))))
    return found


def _remember_live(root: Path, cards: list[dict[str, Any]]) -> None:
    """Append a close the log does not already hold. A miss stays a miss."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    try:
        seen = _logged_live(root)
    except Exception:
        return
    for card in cards:
        spot = _live_spot(card)
        realized = _finite(card.get("realized"))
        token = _value_token(realized)
        if (spot, token) in seen:
            continue
        facts = {
            "realized_closed_profit": realized,
            "ticket": card.get("ticket"),
            "symbol": card.get("symbol"),
        }
        try:
            append_outcome(
                spot,
                realized,
                facts,
                error=None if realized is not None else "unpriced",
            )
        except Exception:
            continue
        seen.add((spot, token))
        plan = _finite(card.get("plan_r"))
        if plan is None:
            continue
        plan_spot = "live_plan:%s" % (card.get("ticket") or "",)
        plan_token = _value_token(plan)
        if (plan_spot, plan_token) in seen:
            continue
        try:
            append_outcome(plan_spot, plan, facts, error=None)
        except Exception:
            continue
        seen.add((plan_spot, plan_token))


def _load_live(root: Path) -> list[dict[str, Any]]:
    stamp = _live_stamp(root)
    with _LIVE_LOCK:
        if _LIVE_CACHE.get("stamp") == stamp and isinstance(_LIVE_CACHE.get("cards"), list):
            return list(_LIVE_CACHE["cards"])
        cards = _merge_cards(_record_cards(root), _sibling_cards(root))
        _remember_live(root, cards)
        _LIVE_CACHE["stamp"] = stamp
        _LIVE_CACHE["cards"] = cards
        return list(cards)


def _compact_outcomes(cards: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for card in cards:
        rows.append(
            [
                card.get("ticket"),
                card.get("symbol"),
                card.get("sleeve"),
                card.get("close_action"),
                card.get("realized"),
                card.get("plan_r"),
            ]
        )
    return rows


def _latest_close(cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    dated = [card for card in cards if card.get("closed_at_utc")]
    if dated:
        return dict(dated[-1])
    if cards:
        return dict(cards[-1])
    return None


def _decide(spot: str, facts: Mapping[str, Any]) -> dict[str, Any]:
    """One System One ask. The choice and the parameter are that return."""

    spec = _SPECS[spot]
    order = tuple(spec["order"])
    clean = _copy(dict(facts))
    if not isinstance(clean, dict):
        clean = {}
    levels = _parameter_levels(clean)
    questions = _question_pack(spot)
    try:
        cards = _load_live(_repo_root())
    except Exception:
        cards = []
    latest = _latest_close(cards)
    state: dict[str, Any] = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "model": MODEL,
        "spot": spot,
        "facts": clean,
        "levels": levels,
        "live_outcome_fields": list(_LIVE_FIELDS),
        "live_outcomes": _compact_outcomes(cards),
        "latest_close": latest,
        "ticket": NEVER_FLATTEN_TICKET,
        "flatten": False,
    }
    _attach_priors(state, questions)
    try:
        from .jev_client import evaluate
    except Exception as exc:
        row = _blank()
        row["error"] = type(exc).__name__
        _remember(state, spot, row)
        return row
    try:
        hop = evaluate(
            state,
            questions=questions,
            model=MODEL,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001 — learning must not raise into the writer
        hop = {"ok": False, "error": type(exc).__name__, "answers": {}}
    if not isinstance(hop, dict):
        hop = {"ok": False, "error": "evaluate_not_a_dict", "answers": {}}
    row = _read_return(hop, spot, order)
    _remember(state, spot, row)
    return row


def _choice(spot: str, facts: Mapping[str, Any]) -> Any:
    decided = _decide(spot, facts)
    if decided.get("choice") is LEGACY:
        return None
    return decided.get("choice")


def asset_class_choice(symbol: str | None) -> Any:
    return _choice("learn_loop.asset_class", {"symbol": symbol})


def exit_other_choice(named: str | None) -> Any:
    """``other`` or ``locked_exit``. A tie does not relabel."""

    return _choice("learn_loop.exit_other", {"named_exit": named})


def promotion_branch_choice(miss: str | None, exit_class: str | None) -> Any:
    return _choice(
        "learn_loop.promotion",
        {"miss_type": miss, "exit_class": exit_class},
    )


def asset_bucket_choice(symbol: Any) -> Any:
    return _choice("trained_models.asset_bucket", {"symbol": symbol})


def plan_r_bin_choice(plan: Any) -> Any:
    return _choice("trained_models.plan_r_bin", {"plan_r": plan})


def chair_label_choice(family: str, hard_off: Any, symbol: str) -> Any:
    return _choice(
        "trained_models.chair_label",
        {"family_class": family, "hard_off_family": hard_off, "symbol": symbol},
    )


def quiet_action_choice(sleeve: str, symbol: str, family_class: str | None) -> Any:
    return _choice(
        "daily_loop.quiet_action",
        {"sleeve": sleeve, "symbol": symbol, "family_class": family_class},
    )


def keep_surface_choice(sleeve: str | None, family: str | None) -> Any:
    return _choice(
        "trained_models.keep_surface",
        {"sleeve": sleeve, "family": family},
    )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _open_gold_facts(root: Path) -> dict[str, Any]:
    """Read the open gold ticket. Do not write it and do not flatten it."""

    path = (
        root
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "trade_records"
        / f"{NEVER_FLATTEN_TICKET}.json"
    )
    rec = _read_json(path) or {}
    inst = rec.get("instrumentation") if isinstance(rec.get("instrumentation"), dict) else {}
    return {
        "ticket": NEVER_FLATTEN_TICKET,
        "present": path.is_file(),
        "symbol": rec.get("symbol"),
        "sleeve": rec.get("sleeve") or rec.get("sleeve_name"),
        "family_class": inst.get("family_class") or rec.get("family_class"),
        "status": rec.get("trade_lifecycle_status") or rec.get("status"),
        "flatten": False,
    }


def _count_map(block: Any) -> dict[str, Any] | None:
    if not isinstance(block, dict):
        return None
    out: dict[str, Any] = {}
    for key, value in block.items():
        number = _count(value)
        if number is None:
            continue
        out[str(key)] = number
    return out


def historical_counts(root: Path | None = None) -> dict[str, Any]:
    """Count sealed Challenge history. Measurement only. Not a decision."""

    repo = root or _repo_root()
    batch_path = repo / "judgment" / "astra" / "lab" / "learn_loop_v0" / "CLOSE_LOOP_BATCH_V1.json"
    batch = _read_json(batch_path)
    if batch is None:
        return {
            "source": str(batch_path),
            "n": None,
            "asset_class": None,
            "exit_class": None,
            "exit_other": None,
            "miss_type": None,
            "decision_emitted": False,
        }
    exits = _count_map(batch.get("exit_class"))
    assets_raw = batch.get("by_asset_class") if isinstance(batch.get("by_asset_class"), dict) else None
    assets: dict[str, Any] | None = None
    if isinstance(assets_raw, dict):
        assets = {}
        for name, block in assets_raw.items():
            if isinstance(block, dict):
                assets[str(name)] = _count(block.get("n"))
            else:
                assets[str(name)] = _count(block)
    misses = _count_map(batch.get("miss_type"))
    locked = {"orig_stop", "orig_tp", "time_stop", "breach_flatten"}
    other_exits: int | None
    if exits is None:
        other_exits = None
    else:
        other_exits = 0
        for key, value in exits.items():
            if key in locked:
                continue
            number = _count(value)
            if isinstance(number, int):
                other_exits += number
    return {
        "source": str(batch_path),
        "n": _count(batch.get("n")),
        "asset_class": assets,
        "exit_class": exits,
        "exit_other": other_exits,
        "miss_type": misses,
        "decision_emitted": False,
    }


def _subject_facts(
    gold: Mapping[str, Any],
    latest: Mapping[str, Any] | None,
    namespace: str,
) -> dict[str, Any]:
    """Facts for this ask. The open ticket and the latest close both stay."""

    close = latest or {}
    symbol = gold.get("symbol")
    if symbol is None:
        symbol = close.get("symbol")
    sleeve = gold.get("sleeve")
    if sleeve is None:
        sleeve = close.get("sleeve")
    family = gold.get("family_class")
    if family is None:
        family = close.get("family_class")
    return {
        "namespace": namespace,
        "symbol": symbol,
        "close_symbol": close.get("symbol"),
        "sleeve": sleeve,
        "family_class": family,
        "hard_off_family": close.get("hard_off_family"),
        "named_exit": close.get("close_action"),
        "miss_type": close.get("miss_type"),
        "exit_class": close.get("exit_class"),
        "plan_r": close.get("plan_r"),
        "realized": close.get("realized"),
        "realised_r": close.get("realised_r"),
        "open_gold": dict(gold),
        "latest_close": dict(close) if close else None,
        "flatten": False,
    }


def _ask_all(facts: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Independent spots run together. Each spot is one ask."""

    jobs = (
        ("asset_class", "learn_loop.asset_class"),
        ("exit_other", "learn_loop.exit_other"),
        ("promotion", "learn_loop.promotion"),
        ("asset_bucket", "trained_models.asset_bucket"),
        ("plan_r_bin", "trained_models.plan_r_bin"),
        ("chair_label", "trained_models.chair_label"),
        ("quiet_action", "daily_loop.quiet_action"),
        ("keep_surface", "trained_models.keep_surface"),
    )

    def run(job: tuple[str, str]) -> tuple[str, dict[str, Any]]:
        name, spot = job
        try:
            return name, _decide(spot, facts)
        except Exception as exc:  # noqa: BLE001 — one spot must not drop the others
            row = _blank()
            row["error"] = type(exc).__name__
            return name, row

    asked: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for name, row in pool.map(run, jobs):
            asked[name] = row
    return asked


def maybe_ask_learning(*, namespace: str | None = None) -> dict[str, Any]:
    """Ask each learning decision once. Does not send or flatten."""

    root = _repo_root()
    gold = _open_gold_facts(root)
    history = historical_counts(root)
    try:
        cards = _load_live(root)
    except Exception:
        cards = []
    latest = _latest_close(cards)
    ns = namespace or CHALLENGE_NS
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "namespace": ns,
        "pid": os.getpid(),
        "asked": False,
        "flatten": False,
        "ticket": NEVER_FLATTEN_TICKET,
        "open_gold": gold,
        "latest_close": latest,
        "live_n": len(cards),
        "spots": {},
        "parameters": {},
        "n_decided": 0,
        "historical": history,
        "last_error": None,
    }
    facts = _subject_facts(gold, latest, str(ns))
    asked = _ask_all(facts)
    spots = {name: rec.get("choice") for name, rec in asked.items()}
    parameters = {name: rec.get("parameter") for name, rec in asked.items()}
    errors = [str(rec.get("error")) for rec in asked.values() if rec.get("error")]
    decided = sum(1 for value in spots.values() if value is not None and value is not LEGACY)
    scored = sum(1 for value in parameters.values() if value is not None)
    row["asked"] = True
    row["spots"] = spots
    row["parameters"] = parameters
    row["n_decided"] = decided
    row["decision_emitted"] = bool(decided or scored)
    row["last_error"] = errors[-1] if errors else None
    row["historical_only"] = not row["decision_emitted"]
    _write(root, row)
    return row


def _write(root: Path, row: Mapping[str, Any]) -> None:
    folder = root / "pipeline_state" / "ultimate_book" / CHALLENGE_NS / "judgment"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "learning_choices.json").write_text(
            json.dumps(row, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return

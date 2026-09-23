"""CROSS_ASSET_FEATURES_V0 — typed fields, not prose.

One ask per deciding state: ``jev_client.evaluate`` with model ``jev-1.13.0``
and ``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
The return is a Noul, a Choice, or a Score. Prior outcomes are attached on
that ask, and the return is stored for the next ask.

Every decision in this module, including each parameter, is that return.
A Choice is the unique highest probability. A Score is the returned number
and may sit between levels. A Noul is a bool or a probability. An empty
answer, a tie, or an error leaves that field unset and does not restore a
constant.

Window ids w16, w32, and w96 are the measured slots of this block. The
sample minimum, the align slack, the naming band, the USD flat band, the
session cuts, and the F5 window are scores on the ask. A missing score is
not filled from a printed minute count or a printed band.

A floor and a baseline are not a question. Missing peer tape stays null.
This module does not send an order. April ``data/historical*`` is not
Challenge-true. ``data/DXY_D1.csv`` is not a prove source.

USD proxy is the FX-major basket already MT5-exportable:
``-EURUSD -GBPUSD +USDJPY``. Rates/funding stand-in is USDJPY (no FRED).
Risk-on needs US30; USDJPY alone is rates_proxy, not risk_on.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.judgment.cross_asset.v0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

# Measured slots this block reports. The length parameter is the score.
CORR_WINDOWS = (16, 32, 96)

USD_PROXY_SIGN = {"EURUSD": -1.0, "GBPUSD": -1.0, "USDJPY": 1.0}
USD_PROXY_MEMBERS = tuple(USD_PROXY_SIGN)
PEER_PRIORITY = ("EURUSD", "GBPUSD", "USDJPY", "US30", "UK100", "EURGBP")
# BTC/ETH may ride as optional risk-on peers if Challenge-landed. Not a fire surface.
OPTIONAL_RISK_PEERS = ("BTCUSD", "ETHUSD")

EVENT_CURRENCIES = ("USD", "GBP", "JPY", "EUR")

_USD_ORDER = ("usd_up", "usd_down", "usd_flat", "unassembled")
_GOLD_USD_ORDER = ("gold_with_usd", "gold_against_usd", "mixed", "unassembled")
_SESSION_ORDER = (
    "friday_cutoff",
    "dead",
    "overlap_london_ny",
    "ny",
    "london",
    "asia",
    "unknown",
)
_RATES_ORDER = ("yen_offered", "yen_bid", "flat", "unassembled")
_RISK_ORDER = ("risk_on", "risk_off", "mixed", "unassembled")
_COMOVE_USD_ORDER = ("with_usd", "against_usd", "no_clear")
_COMOVE_INDEX_ORDER = ("with_us30", "against_us30", "no_clear")
_FUNDING_ORDER = ("risk_on", "risk_off", "mixed")
_NOUL_ORDER = ("true", "false")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_KEYS = frozenset(
    {
        "floor",
        "baseline",
        "day_start_baseline",
        "static_floor",
        "pass_line",
        "flatten_floor_usd",
        "daily_loss_pct",
        "floor_room",
    }
)
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
_SKIP_LEVEL_KEYS = frozenset({"login", "magic", "model"})
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_UNSET = "An empty answer leaves it unset. This ask does not transmit an order."


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    lowered = cleaned.lower()
    kept: list[str] = []
    index = 0
    while index < len(cleaned):
        if lowered.startswith("baseline", index):
            index += len("baseline")
            continue
        if lowered.startswith("floor", index):
            index += len("floor")
            continue
        kept.append(cleaned[index])
        index += 1
    return "".join(kept)


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
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


def _unique(probs: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is unset."""

    if not isinstance(probs, Mapping) or not probs:
        return None
    names = tuple(order) if order else tuple(str(name) for name in probs)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        raw = probs.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        number = _finite(raw)
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p + 1e-12:
            best = str(name)
            best_p = number
            tied = False
        elif abs(number - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    picked: str | None = None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probs, order)
        if agreed in order:
            picked = str(agreed)
    except Exception:
        picked = None
    if picked not in order:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The score that came back. A missing score is not a constant."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "score" not in block or block.get("score") is None:
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: tuple[str, ...] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: tuple[str, ...] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = order or (tuple(str(name) for name in probs) if isinstance(probs, Mapping) else ())
    if isinstance(probs, Mapping) and probs and _unique(probs, menu or None) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    cleaned = {
        str(key): _scrub_text(str(value))
        for key, value in criteria.items()
        if not _limit_key(str(key))
    }
    body: dict[str, Any] = {"type": "choice", "instructions": instructions, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str, levels: Sequence[str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    criteria = [_scrub_text(str(item)) for item in levels] if levels else [str(item) for item in _BETWEEN]
    body: dict[str, Any] = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = criteria
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_question(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _score_line(qid: str, noun: str, levels: Sequence[str]) -> dict[str, Any]:
    return _score_question(
        qid,
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "This ask does not transmit an order.",
        levels,
    )


def _levels_from(facts: Mapping[str, Any]) -> list[str]:
    found: list[float] = []
    for key, value in dict(facts).items():
        if _limit_key(str(key)) or str(key) in _SKIP_LEVEL_KEYS:
            continue
        number = _finite(value)
        if number is not None:
            found.append(number)
    if not found:
        return list(_BETWEEN)
    unique = sorted(set(found))
    if len(unique) > 12:
        unique = unique[:12]
    return [format(number, ".10g") for number in unique]


def _base_state(facts: Mapping[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": MODEL,
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "magic": CHALLENGE_MAGIC,
        "schema": SCHEMA,
    }
    for key, value in dict(facts).items():
        if _limit_key(str(key)):
            continue
        body[str(key)] = value
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else {}


def _attach_priors(payload: dict[str, Any], questions: Mapping[str, Any]) -> None:
    payload.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = [dict(item) for item in _LOCAL_OUTCOMES]
    if loaded is None:
        loaded = []
    payload["prior_outcomes"] = loaded


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})
        return
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})


def _load_evaluate() -> Any:
    from .jev_client import evaluate

    return evaluate


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    _attach_priors(payload, questions)
    try:
        evaluate = _load_evaluate()
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "state": payload, "model": MODEL}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
        "api_url": API_URL,
    }


def _questions_ok(questions: Mapping[str, Any]) -> bool:
    allowed = {"noul", "choice", "score"}
    if not questions:
        return False
    for block in questions.values():
        if not isinstance(block, dict) or block.get("type") not in allowed:
            return False
        if _limit_key(str(block.get("type") or "")):
            return False
    return True


def _decide(
    facts: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    blank = {field: None for field, _kind, _qid, _order in spec}
    if not _questions_ok(questions):
        return blank
    asked = _ask(_base_state(facts), questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    posted = asked.get("state") if isinstance(asked.get("state"), Mapping) else {}
    _remember(posted, rows)
    return out


def _bar_api() -> Any:
    try:
        from . import bars as bars_mod
    except Exception:
        return None
    return bars_mod


def _normalize_symbol(symbol: str) -> str:
    api = _bar_api()
    if api is not None:
        try:
            return str(api.normalize_symbol(symbol))
        except Exception:
            pass
    return str(symbol or "").strip().upper()


def _as_utc(as_of_utc: datetime) -> datetime:
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    return as_of.astimezone(timezone.utc)


def _bar_utc(bar: Any) -> datetime | None:
    utc = getattr(bar, "utc", None)
    if not isinstance(utc, datetime):
        return None
    if utc.tzinfo is None:
        return utc.replace(tzinfo=timezone.utc)
    return utc.astimezone(timezone.utc)


def _last_index(rows: Sequence[Any], as_of_utc: datetime) -> int | None:
    api = _bar_api()
    if api is not None:
        try:
            found = api.last_closed_at_or_before(list(rows), as_of_utc)
        except Exception:
            found = None
        if isinstance(found, int):
            return found
        return None
    as_of = _as_utc(as_of_utc)
    idx = None
    for i, row in enumerate(rows):
        utc = _bar_utc(row)
        if utc is not None and utc <= as_of:
            idx = i
    return idx


def _log_returns(closes: Sequence[float]) -> list[float]:
    out: list[float] = []
    for prev, cur in zip(closes, closes[1:]):
        if prev and prev > 0 and cur and cur > 0:
            out.append(math.log(cur / prev))
    return out


def pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    """Pearson on paired log-returns.

    Fewer than two pairs, or a side with no variance, is undefined and stays
    None. A printed sample minimum is not applied. Never a stand-in zero.
    """

    n = min(len(left), len(right))
    if n < 2:
        return None
    xs = list(left)[-n:]
    ys = list(right)[-n:]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0 or var_y <= 0:
        return None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return round(cov / math.sqrt(var_x * var_y), 6)


def _closes_at_or_before(rows: Sequence[Any], as_of_utc: datetime, n: int) -> list[Any]:
    idx = _last_index(rows, as_of_utc)
    if idx is None:
        return []
    start = max(0, idx - n + 1)
    return list(rows[start : idx + 1])


def _nearest_peer(rows: Sequence[Any], target: datetime) -> tuple[Any, float] | None:
    """Nearest peer print and the absolute gap in seconds. No printed slack."""

    if not rows:
        return None
    idx = _last_index(rows, target)
    cands: list[Any] = []
    if idx is None:
        cands.append(rows[0])
    else:
        cands.append(rows[idx])
        if idx + 1 < len(rows):
            cands.append(rows[idx + 1])
    best: Any = None
    best_gap: float | None = None
    for cand in cands:
        utc = _bar_utc(cand)
        if utc is None:
            continue
        gap = abs((utc - _as_utc(target)).total_seconds())
        if best_gap is None or gap < best_gap:
            best = cand
            best_gap = gap
    if best is None or best_gap is None:
        return None
    return best, best_gap


def _close_of(bar: Any) -> float | None:
    inner = getattr(bar, "bar", None)
    if inner is None:
        return None
    return _finite(getattr(inner, "c", None))


def aligned_closes(
    anchor: Sequence[Any],
    peer: Sequence[Any],
    as_of_utc: datetime,
    n: int,
    slack_seconds: float | None = None,
) -> tuple[list[float], list[float]] | None:
    """Last n closed anchor bars whose peer gap is within the returned slack.

    ``slack_seconds`` is that score. A missing slack does not use a printed
    minute count, and the alignment stays unset.
    """

    slack = _finite(slack_seconds)
    if slack is None or slack < 0:
        return None
    as_of = _as_utc(as_of_utc)
    want = n + 1  # n returns need n+1 closes
    anchors = _closes_at_or_before(anchor, as_of, want)
    if len(anchors) < want:
        return None
    a_closes: list[float] = []
    p_closes: list[float] = []
    for bar in anchors:
        utc = _bar_utc(bar)
        if utc is None:
            continue
        hit = _nearest_peer(peer, utc)
        if hit is None or hit[1] > slack:
            continue
        a_px = _close_of(bar)
        p_px = _close_of(hit[0])
        if a_px is None or p_px is None or a_px <= 0 or p_px <= 0:
            continue
        a_closes.append(a_px)
        p_closes.append(p_px)
    if len(a_closes) < want:
        return None
    return a_closes[-want:], p_closes[-want:]


def _gap_summary(
    anchor: Sequence[Any],
    peer: Sequence[Any],
    as_of_utc: datetime,
    n: int,
) -> dict[str, Any]:
    as_of = _as_utc(as_of_utc)
    anchors = _closes_at_or_before(anchor, as_of, n + 1)
    gaps: list[float] = []
    for bar in anchors:
        utc = _bar_utc(bar)
        if utc is None:
            continue
        hit = _nearest_peer(peer, utc)
        if hit is not None:
            gaps.append(hit[1])
    return {
        "anchor_bars": len(anchors),
        "peer_hits": len(gaps),
        "max_gap_seconds": max(gaps) if gaps else None,
    }


def _window_questions(facts: Mapping[str, Any]) -> dict[str, Any]:
    levels = _levels_from(facts)
    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        "ca_corr_sufficient",
        "Is the paired sample enough to read this correlation? " + _UNSET,
        "The paired sample is enough.",
        "The paired sample is not enough.",
    ))
    pack.update(_noul_question(
        "ca_peer_within_slack",
        "Is the peer print inside the align slack for this state? " + _UNSET,
        "The peer print is inside the align slack.",
        "The peer print is outside the align slack.",
    ))
    pack.update(_score_line("ca_min_corr_n", "minimum paired sample for this correlation", levels))
    pack.update(_score_line("ca_align_slack_minutes", "align slack in minutes", levels))
    pack.update(_score_line("ca_corr_named_eps", "correlation naming band", levels))
    for window in CORR_WINDOWS:
        pack.update(_score_line(
            f"ca_corr_window_w{window}",
            f"length of the measured w{window} slot",
            levels,
        ))
    return pack


_WINDOW_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("corr_sufficient", "noul", "ca_corr_sufficient", _NOUL_ORDER),
    ("peer_within_slack", "noul", "ca_peer_within_slack", _NOUL_ORDER),
    ("min_corr_n", "score", "ca_min_corr_n", None),
    ("align_slack_minutes", "score", "ca_align_slack_minutes", None),
    ("corr_named_eps", "score", "ca_corr_named_eps", None),
    *(
        (f"corr_window_w{window}", "score", f"ca_corr_window_w{window}", None)
        for window in CORR_WINDOWS
    ),
)


def _blank_windows() -> dict[str, Any]:
    out: dict[str, Any] = {
        "n": None,
        "source": "unassembled",
        "corr_sufficient": None,
        "peer_within_slack": None,
        "min_corr_n": None,
        "align_slack_minutes": None,
        "corr_named_eps": None,
    }
    for window in CORR_WINDOWS:
        out[f"w{window}"] = None
        out[f"corr_window_w{window}"] = None
    return out


def _slack_seconds(minutes: Any) -> float | None:
    number = _finite(minutes)
    if number is None or number < 0:
        return None
    return number * 60.0


def _sample_ok(n_returns: int, min_corr_n: Any) -> bool:
    """A returned minimum binds. A missing minimum does not become a printed count."""

    bound = _finite(min_corr_n)
    if bound is None:
        return True
    return float(n_returns) >= bound


def window_corr(
    anchor: Sequence[Any],
    peer: Sequence[Any],
    as_of_utc: datetime,
    windows: Sequence[int] = CORR_WINDOWS,
) -> dict[str, Any]:
    """Measured slot corrs. Sufficiency, slack, and the bands are the return."""

    out = _blank_windows()
    if not anchor or not peer:
        return out
    facts: dict[str, Any] = {"windows": [int(window) for window in windows]}
    for window in windows:
        summary = _gap_summary(anchor, peer, as_of_utc, int(window))
        facts[f"w{window}_anchors"] = summary.get("anchor_bars")
        facts[f"w{window}_peer_hits"] = summary.get("peer_hits")
        facts[f"w{window}_max_gap_seconds"] = summary.get("max_gap_seconds")
    if not any(_finite(facts.get(f"w{window}_peer_hits")) for window in windows):
        return out
    decided = _decide(facts, _window_questions(facts), _WINDOW_SPEC)
    for key, value in decided.items():
        out[key] = value
    slack = _slack_seconds(decided.get("align_slack_minutes"))
    if slack is None:
        return out
    best_n = 0
    published = False
    for window in windows:
        aligned = aligned_closes(anchor, peer, as_of_utc, int(window), slack_seconds=slack)
        if aligned is None:
            continue
        a_rets = _log_returns(aligned[0])
        p_rets = _log_returns(aligned[1])
        n_ret = min(len(a_rets), len(p_rets))
        if not _sample_ok(n_ret, decided.get("min_corr_n")):
            continue
        value = pearson(a_rets, p_rets)
        if window in CORR_WINDOWS:
            out[f"w{window}"] = value
        if value is not None:
            published = True
            best_n = max(best_n, n_ret)
    if published:
        out["n"] = best_n or None
        out["source"] = "aligned_m15_log_return"
    return out


def _relation_questions(facts: Mapping[str, Any], qid: str, order: Sequence[str], text: str) -> dict[str, Any]:
    levels = _levels_from(facts)
    criteria = {name: f"The reading is {name}." for name in order}
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        qid,
        text + " The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        criteria,
    ))
    pack.update(_noul_question(
        "ca_corr_sufficient",
        "Is the paired sample enough to read this correlation? " + _UNSET,
        "The paired sample is enough.",
        "The paired sample is not enough.",
    ))
    pack.update(_score_line("ca_min_corr_n", "minimum paired sample for this correlation", levels))
    pack.update(_score_line("ca_corr_named_eps", "correlation naming band", levels))
    return pack


def _usd_missing(present: Sequence[str]) -> dict[str, Any]:
    return {
        "named": "unassembled",
        "ret": None,
        "n": None,
        "members_present": list(present),
        "source": "unassembled",
        "dxy_used": False,
        "usd_flat_eps": None,
        "usd_proxy_bars": None,
        "align_slack_minutes": None,
        "min_corr_n": None,
    }


def _usd_questions(facts: Mapping[str, Any]) -> dict[str, Any]:
    levels = _levels_from(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "ca_usd_named",
        "Name the FX-major USD proxy on this state. Do not invent DXY. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {name: f"The proxy reads {name}." for name in _USD_ORDER},
    ))
    pack.update(_score_line("ca_usd_flat_eps", "USD flat band for this proxy", levels))
    pack.update(_score_line("ca_usd_proxy_bars", "USD proxy bar count", levels))
    pack.update(_score_line("ca_align_slack_minutes", "align slack in minutes", levels))
    pack.update(_score_line("ca_min_corr_n", "minimum paired sample for this proxy", levels))
    return pack


_USD_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("usd_named", "choice", "ca_usd_named", _USD_ORDER),
    ("usd_flat_eps", "score", "ca_usd_flat_eps", None),
    ("usd_proxy_bars", "score", "ca_usd_proxy_bars", None),
    ("align_slack_minutes", "score", "ca_align_slack_minutes", None),
    ("min_corr_n", "score", "ca_min_corr_n", None),
)


def usd_proxy_returns(
    peer_books: Mapping[str, Mapping[str, Sequence[Any]]],
    as_of_utc: datetime,
    n: int | None = None,
) -> dict[str, Any]:
    """Equal-weight FX-implied USD: -EUR -GBP +USDJPY.

    The basket needs two members or there is no series. The name, the flat
    band, the bar count, and the align slack are the return. ``n`` is only
    proposed on the ask.
    """

    as_of = _as_utc(as_of_utc)
    series: dict[str, list[Any]] = {}
    for symbol in USD_PROXY_MEMBERS:
        books = peer_books.get(symbol) or {}
        m15 = books.get("m15") or []
        if m15:
            series[symbol] = list(m15)
    present = list(series)
    if len(present) < 2:
        return _usd_missing(present)
    anchor_sym = present[0]
    anchors = _closes_at_or_before(series[anchor_sym], as_of, len(series[anchor_sym]))
    if len(anchors) < 2:
        return _usd_missing(present)
    steps: list[dict[str, float]] = []
    for i in range(1, len(anchors)):
        prev_t = _bar_utc(anchors[i - 1])
        cur_t = _bar_utc(anchors[i])
        if prev_t is None or cur_t is None:
            continue
        piece: list[float] = []
        gaps: list[float] = []
        for symbol, sign in USD_PROXY_SIGN.items():
            rows = series.get(symbol)
            if not rows:
                continue
            prev = _nearest_peer(rows, prev_t)
            cur = _nearest_peer(rows, cur_t)
            if prev is None or cur is None:
                continue
            prev_px = _close_of(prev[0])
            cur_px = _close_of(cur[0])
            if prev_px is None or cur_px is None or prev_px <= 0 or cur_px <= 0:
                continue
            piece.append(float(sign) * math.log(cur_px / prev_px))
            gaps.append(max(prev[1], cur[1]))
        if len(piece) >= 2 and gaps:
            steps.append({"mean": sum(piece) / len(piece), "gap": max(gaps)})
    if not steps:
        return _usd_missing(present)
    unfiltered = sum(step["mean"] for step in steps) / len(steps)
    facts: dict[str, Any] = {
        "measured_steps": len(steps),
        "unfiltered_mean": unfiltered,
        "max_gap_seconds": max(step["gap"] for step in steps),
        "members_present": present,
        "proposed_bars": _finite(n),
        "dxy_used": False,
    }
    decided = _decide(facts, _usd_questions(facts), _USD_SPEC)
    slack = _slack_seconds(decided.get("align_slack_minutes"))
    filtered = [step for step in steps if slack is not None and step["gap"] <= slack]
    if not _sample_ok(len(filtered), decided.get("min_corr_n")):
        filtered = []
    named = decided.get("usd_named")
    if len(filtered) < 1:
        return {
            "named": named,
            "ret": None,
            "n": None,
            "members_present": present,
            "source": "unassembled",
            "dxy_used": False,
            "usd_flat_eps": decided.get("usd_flat_eps"),
            "usd_proxy_bars": decided.get("usd_proxy_bars"),
            "align_slack_minutes": decided.get("align_slack_minutes"),
            "min_corr_n": decided.get("min_corr_n"),
        }
    proxy_rets = [step["mean"] for step in filtered]
    mean_ret = sum(proxy_rets) / len(proxy_rets)
    return {
        "named": named,
        "ret": round(mean_ret, 8),
        "n": len(proxy_rets),
        "members_present": present,
        "source": "fx_majors_equal_weight",
        "dxy_used": False,
        "returns": proxy_rets,
        "usd_flat_eps": decided.get("usd_flat_eps"),
        "usd_proxy_bars": decided.get("usd_proxy_bars"),
        "align_slack_minutes": decided.get("align_slack_minutes"),
        "min_corr_n": decided.get("min_corr_n"),
    }


def _measured_corr_slots(
    gold_rets: Sequence[float],
    proxy_rets: Sequence[float],
    min_corr_n: Any,
) -> dict[str, Any]:
    corr: dict[str, Any] = {"source": "unassembled", "n": None}
    best_n = 0
    published = False
    for window in CORR_WINDOWS:
        key = f"w{window}"
        if len(gold_rets) < window or len(proxy_rets) < window:
            corr[key] = None
            continue
        if not _sample_ok(window, min_corr_n):
            corr[key] = None
            continue
        value = pearson(list(gold_rets)[-window:], list(proxy_rets)[-window:])
        corr[key] = value
        if value is not None:
            published = True
            best_n = max(best_n, window)
    if published:
        corr["n"] = best_n
        corr["source"] = "aligned_m15_log_return"
    return corr


def gold_vs_usd_corr(
    xau_m15: Sequence[Any],
    peer_books: Mapping[str, Mapping[str, Sequence[Any]]],
    as_of_utc: datetime,
) -> dict[str, Any]:
    """XAU versus the FX USD proxy. The name and the bands are the return."""

    proxy = usd_proxy_returns(peer_books, as_of_utc)
    usd_view = {
        k: proxy.get(k)
        for k in (
            "named",
            "ret",
            "n",
            "members_present",
            "source",
            "dxy_used",
            "usd_flat_eps",
            "usd_proxy_bars",
            "align_slack_minutes",
            "min_corr_n",
        )
    }
    empty = {
        "named": "unassembled",
        "corr": _blank_windows(),
        "usd_proxy": usd_view,
        "corr_named_eps": None,
        "min_corr_n": None,
        "corr_sufficient": None,
    }
    if proxy.get("source") != "fx_majors_equal_weight" or not proxy.get("returns"):
        return empty
    as_of = _as_utc(as_of_utc)
    proxy_rets = list(proxy["returns"])
    gold = _closes_at_or_before(xau_m15, as_of, len(proxy_rets) + 1)
    gold_rets = _log_returns([px for px in (_close_of(bar) for bar in gold) if px is not None and px > 0])
    preview = _measured_corr_slots(gold_rets, proxy_rets, None)
    if preview.get("source") != "aligned_m15_log_return":
        return empty
    facts = {
        "w16": preview.get("w16"),
        "w32": preview.get("w32"),
        "w96": preview.get("w96"),
        "measured_n": preview.get("n"),
        "proxy_ret": proxy.get("ret"),
        "proxy_named": proxy.get("named"),
    }
    questions = _relation_questions(
        facts,
        "ca_gold_usd_named",
        _GOLD_USD_ORDER,
        "Name gold against the FX USD proxy on this state. Do not invent DXY.",
    )
    decided = _decide(
        facts,
        questions,
        (
            ("named", "choice", "ca_gold_usd_named", _GOLD_USD_ORDER),
            ("corr_sufficient", "noul", "ca_corr_sufficient", _NOUL_ORDER),
            ("min_corr_n", "score", "ca_min_corr_n", None),
            ("corr_named_eps", "score", "ca_corr_named_eps", None),
        ),
    )
    corr = _measured_corr_slots(gold_rets, proxy_rets, decided.get("min_corr_n"))
    corr["corr_sufficient"] = decided.get("corr_sufficient")
    corr["min_corr_n"] = decided.get("min_corr_n")
    corr["corr_named_eps"] = decided.get("corr_named_eps")
    return {
        "named": decided.get("named"),
        "corr": {k: corr.get(k) for k in ("w16", "w32", "w96", "n", "source", "corr_sufficient", "min_corr_n", "corr_named_eps")},
        "usd_proxy": usd_view,
        "corr_named_eps": decided.get("corr_named_eps"),
        "min_corr_n": decided.get("min_corr_n"),
        "corr_sufficient": decided.get("corr_sufficient"),
    }


def gold_vs_peer_corr(
    xau_m15: Sequence[Any],
    peer_m15: Sequence[Any],
    as_of_utc: datetime,
    *,
    with_name: str,
    against_name: str,
) -> dict[str, Any]:
    """Gold versus one peer. The name is the choice for this pair."""

    packed = window_corr(xau_m15, peer_m15, as_of_utc)
    order = (str(with_name), str(against_name), "mixed", "unassembled")
    if packed.get("source") != "aligned_m15_log_return":
        return {"named": "unassembled", "corr": packed}
    facts = {
        "w16": packed.get("w16"),
        "w32": packed.get("w32"),
        "w96": packed.get("w96"),
        "measured_n": packed.get("n"),
        "with_name": with_name,
        "against_name": against_name,
    }
    criteria = {name: f"The reading is {name}." for name in order}
    questions: dict[str, Any] = {}
    questions.update(_choice_question(
        "ca_gold_peer_named",
        "Name gold against this peer tape. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        criteria,
    ))
    decided = _decide(
        facts,
        questions,
        (("named", "choice", "ca_gold_peer_named", order),),
    )
    return {"named": decided.get("named"), "corr": packed}


def _tf_snap(rows: Sequence[Any], as_of_utc: datetime) -> Mapping[str, Any] | None:
    api = _bar_api()
    if api is None:
        return None
    try:
        snap = api.tf_snap(list(rows), as_of_utc, "M15")
    except Exception:
        return None
    if isinstance(snap, Mapping):
        return snap
    return None


def peer_snap(
    books: Mapping[str, Sequence[Any]] | None,
    as_of_utc: datetime,
    symbol: str,
) -> dict[str, Any]:
    absent = {
        "symbol": _normalize_symbol(symbol),
        "present": False,
        "last_close": None,
        "last_utc": None,
        "trend": None,
        "close_vs_close_n_atr": None,
        "atr14": None,
        "source_path": None,
        "tf": "M15",
    }
    if not books or not books.get("m15"):
        return absent
    snap = _tf_snap(list(books["m15"]), as_of_utc)
    if snap is None:
        return absent
    return {
        "symbol": _normalize_symbol(symbol),
        "present": True,
        "last_close": snap.get("last_close"),
        "last_utc": snap.get("last_utc"),
        "trend": snap.get("trend"),
        "close_vs_close_n_atr": snap.get("close_vs_close_n_atr"),
        "atr14": snap.get("atr14"),
        "source_path": snap.get("source_path"),
        "tf": "M15",
        "bars_available": snap.get("bars_available"),
    }


def _session_questions(facts: Mapping[str, Any]) -> dict[str, Any]:
    levels = _levels_from(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "ca_session_named",
        "Which session is this clock? Do not invent volume. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {name: f"The session reads {name}." for name in _SESSION_ORDER},
    ))
    pack.update(_noul_question(
        "ca_session_overlap",
        "Is this clock the London-New York overlap? " + _UNSET,
        "This clock is the overlap.",
        "This clock is not the overlap.",
    ))
    pack.update(_noul_question(
        "ca_session_thin",
        "Is this clock a thin session? " + _UNSET,
        "This clock is thin.",
        "This clock is not thin.",
    ))
    for qid, noun in (
        ("ca_session_friday_hour", "Friday cutoff hour"),
        ("ca_session_dead_hour", "dead-session hour"),
        ("ca_session_overlap_start_hour", "overlap start hour"),
        ("ca_session_ny_hour", "New York start hour"),
        ("ca_session_london_hour", "London start hour"),
    ):
        pack.update(_score_line(qid, noun, levels))
    return pack


_SESSION_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("named", "choice", "ca_session_named", _SESSION_ORDER),
    ("overlap", "noul", "ca_session_overlap", _NOUL_ORDER),
    ("thin", "noul", "ca_session_thin", _NOUL_ORDER),
    ("friday_hour", "score", "ca_session_friday_hour", None),
    ("dead_hour", "score", "ca_session_dead_hour", None),
    ("overlap_start_hour", "score", "ca_session_overlap_start_hour", None),
    ("ny_hour", "score", "ca_session_ny_hour", None),
    ("london_hour", "score", "ca_session_london_hour", None),
)


def session_liquidity_flags(utc_hour: int | None, is_friday: bool) -> dict[str, Any]:
    """Session labels for this clock. The name, the flags, and the hours are the return."""

    if utc_hour is None:
        return {
            "named": None,
            "overlap": None,
            "thin": None,
            "source": "unassembled",
            "friday_hour": None,
            "dead_hour": None,
            "overlap_start_hour": None,
            "ny_hour": None,
            "london_hour": None,
        }
    facts = {"utc_hour": int(utc_hour), "is_friday": bool(is_friday)}
    decided = _decide(facts, _session_questions(facts), _SESSION_SPEC)
    decided["source"] = "clock_utc_hour"
    return decided


def _event_minutes(rows: Sequence[Mapping[str, Any]]) -> list[int]:
    minutes: list[int] = []
    for event in rows:
        try:
            minutes.append(int(event.get("minutes_from_as_of")))
        except (TypeError, ValueError):
            continue
    return minutes


def event_join_features(news: Mapping[str, Any] | None) -> dict[str, Any]:
    """Join named HIGH events by currency.

    An empty spine is not no HIGH. In-window flags and the pre/post minutes
    are the return. A missing return stays unset.
    """

    packed = dict(news or {})
    empty = {
        "usd_high_in_window": None,
        "gbp_high_in_window": None,
        "jpy_high_in_window": None,
        "eur_high_in_window": None,
        "minutes_to_nearest_usd": None,
        "joined_currencies": [],
        "spine_empty": True if news is None or packed.get("spine_empty") else False,
        "source": "news_spine_empty" if news is None or packed.get("spine_empty") else "news_spine",
        "f5_pre_minutes": None,
        "f5_post_minutes": None,
    }
    if news is None or packed.get("spine_empty"):
        empty["spine_empty"] = True
        empty["source"] = "news_spine_empty"
        return empty
    events = [e for e in (packed.get("events") or []) if isinstance(e, dict)]
    by_ccy: dict[str, list[dict[str, Any]]] = {c: [] for c in EVENT_CURRENCIES}
    for event in events:
        if str(event.get("impact") or "").upper() != "HIGH":
            continue
        ccy = str(event.get("currency") or "").upper()
        if ccy in {"US", "USA", "XAU", "ALL"}:
            ccy = "USD"
        if ccy == "GB":
            ccy = "GBP"
        if ccy == "JP":
            ccy = "JPY"
        if ccy in by_ccy:
            by_ccy[ccy].append(event)
    usd_mins = _event_minutes(by_ccy["USD"])
    joined = [c for c, rows in by_ccy.items() if rows]
    flags: dict[str, Any] = {}
    facts: dict[str, Any] = {
        "spine_empty": False,
        "joined_currencies": joined,
        "minutes_to_nearest_usd": min(usd_mins) if usd_mins else None,
    }
    any_high = False
    for ccy, rows in by_ccy.items():
        key = f"{ccy.lower()}_high_rows"
        facts[key] = len(rows)
        mins = _event_minutes(rows)
        if mins:
            facts[f"{ccy.lower()}_nearest_minutes"] = min(mins)
            any_high = True
        flags[f"{ccy.lower()}_high_in_window"] = False if not rows else None
    if not any_high:
        return {
            "usd_high_in_window": flags["usd_high_in_window"],
            "gbp_high_in_window": flags["gbp_high_in_window"],
            "jpy_high_in_window": flags["jpy_high_in_window"],
            "eur_high_in_window": flags["eur_high_in_window"],
            "minutes_to_nearest_usd": facts.get("minutes_to_nearest_usd"),
            "joined_currencies": joined,
            "spine_empty": False,
            "source": "news_spine",
            "f5_pre_minutes": None,
            "f5_post_minutes": None,
        }
    levels = _levels_from(facts)
    questions: dict[str, Any] = {}
    spec: list[tuple[str, str, str, tuple[str, ...] | None]] = []
    for ccy in EVENT_CURRENCIES:
        if not by_ccy[ccy]:
            continue
        qid = f"ca_{ccy.lower()}_high_in_window"
        field = f"{ccy.lower()}_high_in_window"
        questions.update(_noul_question(
            qid,
            f"Is a named {ccy} HIGH inside the window this state carries? " + _UNSET,
            f"A named {ccy} HIGH is inside the window.",
            f"Named {ccy} highs are outside the window.",
        ))
        spec.append((field, "noul", qid, _NOUL_ORDER))
    questions.update(_score_line("ca_f5_pre_minutes", "F5 pre-window minutes", levels))
    questions.update(_score_line("ca_f5_post_minutes", "F5 post-window minutes", levels))
    spec.append(("f5_pre_minutes", "score", "ca_f5_pre_minutes", None))
    spec.append(("f5_post_minutes", "score", "ca_f5_post_minutes", None))
    decided = _decide(facts, questions, tuple(spec))
    for ccy in EVENT_CURRENCIES:
        field = f"{ccy.lower()}_high_in_window"
        if by_ccy[ccy]:
            flags[field] = decided.get(field)
    return {
        "usd_high_in_window": flags.get("usd_high_in_window"),
        "gbp_high_in_window": flags.get("gbp_high_in_window"),
        "jpy_high_in_window": flags.get("jpy_high_in_window"),
        "eur_high_in_window": flags.get("eur_high_in_window"),
        "minutes_to_nearest_usd": facts.get("minutes_to_nearest_usd"),
        "joined_currencies": joined,
        "spine_empty": False,
        "source": "news_spine",
        "f5_pre_minutes": decided.get("f5_pre_minutes"),
        "f5_post_minutes": decided.get("f5_post_minutes"),
    }


def rates_proxy_from_usdjpy(usdjpy_snap: Mapping[str, Any] | None) -> dict[str, Any]:
    """USDJPY is the rates/funding stand-in. The name is the choice. No FRED / DXY."""

    if not usdjpy_snap or not usdjpy_snap.get("present"):
        return {
            "named": "unassembled",
            "usdjpy_trend": None,
            "source": "unassembled",
        }
    trend = usdjpy_snap.get("trend")
    if trend is None:
        return {
            "named": "unassembled",
            "usdjpy_trend": None,
            "source": "unassembled",
        }
    facts = {"usdjpy_trend": trend, "present": True}
    questions = _choice_question(
        "ca_rates_named",
        "Name the USDJPY rates stand-in on this state. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {name: f"The stand-in reads {name}." for name in _RATES_ORDER},
    )
    decided = _decide(facts, questions, (("named", "choice", "ca_rates_named", _RATES_ORDER),))
    named = decided.get("named")
    return {
        "named": named,
        "usdjpy_trend": trend,
        "source": "usdjpy_m15" if named is not None else "unassembled",
    }


def risk_on_named(us30_snap: Mapping[str, Any] | None, rates: Mapping[str, Any] | None) -> dict[str, Any]:
    """Risk-on needs US30. The name is the choice. USDJPY alone stays rates_proxy."""

    funding = (rates or {}).get("named")
    if not us30_snap or not us30_snap.get("present"):
        return {
            "named": "unassembled",
            "us30_trend": None,
            "funding": funding if funding is not None else "unassembled",
            "source": "unassembled",
        }
    us30_trend = us30_snap.get("trend")
    facts = {"us30_trend": us30_trend, "funding": funding, "us30_present": True}
    questions = _choice_question(
        "ca_risk_named",
        "Name risk-on for this state. Risk-on needs US30. USDJPY alone is the rates stand-in. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {name: f"The tape reads {name}." for name in _RISK_ORDER},
    )
    decided = _decide(facts, questions, (("named", "choice", "ca_risk_named", _RISK_ORDER),))
    named = decided.get("named")
    return {
        "named": named,
        "us30_trend": us30_trend,
        "funding": funding if funding is not None else None,
        "source": "us30_m15_plus_usdjpy" if named is not None else "unassembled",
    }


def iter_peer_symbols(peer_books: Mapping[str, Any] | None) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for symbol in list(PEER_PRIORITY) + list(OPTIONAL_RISK_PEERS):
        books = (peer_books or {}).get(symbol)
        if books and books.get("m15") and symbol not in seen:
            seen.add(symbol)
            found.append(symbol)
    if peer_books:
        for key in peer_books:
            sym = _normalize_symbol(str(key))
            if sym in seen or sym == "XAUUSD":
                continue
            books = peer_books.get(key)
            if books and books.get("m15"):
                seen.add(sym)
                found.append(sym)
    return found


def _blank_corr() -> dict[str, Any]:
    return {"w16": None, "w32": None, "w96": None, "n": None, "source": "unassembled"}


def assemble_cross_asset_v0(
    *,
    as_of_utc: datetime,
    symbol: str = "XAUUSD",
    peer_books: Mapping[str, Mapping[str, Sequence[Any]]] | None = None,
    xau_books: Mapping[str, Sequence[Any]] | None = None,
    news: Mapping[str, Any] | None = None,
    occupancy_book: Mapping[str, Any] | None = None,
    utc_hour: int | None = None,
    is_friday: bool = False,
    challenge_true: bool = True,
) -> dict[str, Any]:
    """Build the typed CROSS_ASSET_FEATURES_V0 block. Decisions are the returns."""

    peers_in = dict(peer_books or {})
    xau = xau_books or peers_in.get("XAUUSD")
    xau_m15 = list((xau or {}).get("m15") or [])
    peer_snaps = {sym: peer_snap(peers_in.get(sym), as_of_utc, sym) for sym in iter_peer_symbols(peers_in)}
    for sym in PEER_PRIORITY:
        peer_snaps.setdefault(sym, peer_snap(None, as_of_utc, sym))

    usd = usd_proxy_returns(peers_in, as_of_utc)
    if xau_m15:
        gold_usd = gold_vs_usd_corr(xau_m15, peers_in, as_of_utc)
    else:
        gold_usd = {
            "named": "unassembled",
            "corr": _blank_corr(),
            "usd_proxy": {k: usd.get(k) for k in ("named", "ret", "n", "members_present", "source", "dxy_used")},
        }
    us30 = peer_snaps.get("US30") or peer_snap(peers_in.get("US30"), as_of_utc, "US30")
    usdjpy = peer_snaps.get("USDJPY") or peer_snap(peers_in.get("USDJPY"), as_of_utc, "USDJPY")
    rates = rates_proxy_from_usdjpy(usdjpy)
    risk = risk_on_named(us30, rates)
    if xau_m15 and us30.get("present") and peers_in.get("US30", {}).get("m15"):
        gold_idx = gold_vs_peer_corr(
            xau_m15,
            list(peers_in["US30"]["m15"]),
            as_of_utc,
            with_name="gold_with_us30",
            against_name="gold_against_us30",
        )
    else:
        gold_idx = {"named": "unassembled", "corr": _blank_corr()}
    liq = session_liquidity_flags(utc_hour, is_friday)
    events = event_join_features(news)
    occ = dict(occupancy_book or {})
    if "occupancy_source" not in occ:
        occ = {
            "clusters_open": None,
            "book_open_n": None,
            "n_clusters_open": None,
            "symbols_open": None,
            "occupancy_source": "unassembled",
        }

    n_peers = sum(1 for snap in peer_snaps.values() if snap.get("present"))
    missing: list[str] = []
    if n_peers == 0:
        missing.append("world.peers")
    if usd.get("source") == "unassembled" or usd.get("named") is None:
        missing.append("world.usd_proxy")
    if gold_usd.get("named") in {None, "unassembled"}:
        missing.append("world.gold_vs_usd")
    if gold_idx.get("named") in {None, "unassembled"}:
        missing.append("world.gold_vs_index")
    if rates.get("named") in {None, "unassembled"}:
        missing.append("world.rates_proxy")
    if risk.get("named") in {None, "unassembled"}:
        missing.append("world.risk_on")
    if occ.get("occupancy_source") in {None, "unassembled", "deal_tape_absent"}:
        missing.append("world.occupancy_book")
    if events.get("spine_empty"):
        missing.append("world.event_join")

    return {
        "schema": SCHEMA,
        "symbol": _normalize_symbol(symbol),
        "challenge_true": bool(challenge_true),
        "april_historical_used": False,
        "dxy_used": False,
        "peers": peer_snaps,
        "n_peers_present": n_peers,
        "usd_proxy": {
            k: usd.get(k)
            for k in (
                "named",
                "ret",
                "n",
                "members_present",
                "source",
                "dxy_used",
                "usd_flat_eps",
                "usd_proxy_bars",
                "align_slack_minutes",
                "min_corr_n",
            )
        },
        "rates_proxy": rates,
        "risk_on": risk,
        "gold_vs_usd": gold_usd,
        "gold_vs_index": gold_idx,
        "session_liquidity": liq,
        "event_join": events,
        "occupancy_book": occ,
        "completeness": {
            "peers_m15": n_peers > 0,
            "usd_proxy": usd.get("source") == "fx_majors_equal_weight" and usd.get("named") is not None,
            "rates_proxy": rates.get("source") == "usdjpy_m15" and rates.get("named") is not None,
            "risk_on": risk.get("named") not in {None, "unassembled"},
            "gold_vs_usd": gold_usd.get("named") not in {None, "unassembled"},
            "gold_vs_index": gold_idx.get("named") not in {None, "unassembled"},
            "session_liquidity": liq.get("source") == "clock_utc_hour" and liq.get("named") is not None,
            "event_join": not bool(events.get("spine_empty")),
            "occupancy_book": occ.get("occupancy_source") == "challenge_deals",
            "challenge_true": bool(challenge_true),
            "april_historical_used": False,
            "dxy_used": False,
            "missing_fields": missing,
        },
    }


def _answer_questions(facts: Mapping[str, Any]) -> dict[str, Any]:
    levels = _levels_from(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "gold_usd_comove",
        "Does this state say gold is moving with the FX USD proxy, against it, or with no clear read? "
        "Do not invent DXY. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {
            "with_usd": "Gold is with the FX USD proxy.",
            "against_usd": "Gold is against the FX USD proxy.",
            "no_clear": "The gold-USD read is mixed or unassembled.",
        },
    ))
    pack.update(_choice_question(
        "gold_index_comove",
        "Does this state say gold is moving with US30, against it, or with no clear read? "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {
            "with_us30": "Gold is with US30.",
            "against_us30": "Gold is against US30.",
            "no_clear": "The gold-index read is mixed or unassembled.",
        },
    ))
    pack.update(_choice_question(
        "risk_on_funding",
        "Read the risk-on funding on this state. Risk-on needs US30. USDJPY alone is the rates stand-in. "
        "The option you return is the unique highest probability. "
        "A tie or an empty answer leaves it unset. "
        "This ask does not transmit an order.",
        {
            "risk_on": "The tape reads risk_on.",
            "risk_off": "The tape reads risk_off.",
            "mixed": "The tape reads mixed.",
        },
    ))
    pack.update(_score_line("session_liquidity", "session liquidity", levels))
    pack.update(_score_line("occupancy_world", "open-cluster occupancy", levels))
    return pack


_ANSWER_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("gold_usd_comove", "choice", "gold_usd_comove", _COMOVE_USD_ORDER),
    ("gold_index_comove", "choice", "gold_index_comove", _COMOVE_INDEX_ORDER),
    ("risk_on_funding", "choice", "risk_on_funding", _FUNDING_ORDER),
    ("session_liquidity", "score", "session_liquidity", None),
    ("occupancy_world", "score", "occupancy_world", None),
)


def local_cross_asset_answers(world: Mapping[str, Any] | None) -> dict[str, Any]:
    """Typed answers for this world. Each choice and each score is the return.

    A miss, a tie, or an error leaves that field unset. The world block is
    evidence on the ask, not a table that fills the answer.
    """

    packed = _scrub(dict(world or {}))
    if not isinstance(packed, dict):
        packed = {}
    gold_usd = packed.get("gold_vs_usd") if isinstance(packed.get("gold_vs_usd"), Mapping) else {}
    gold_idx = packed.get("gold_vs_index") if isinstance(packed.get("gold_vs_index"), Mapping) else {}
    risk = packed.get("risk_on") if isinstance(packed.get("risk_on"), Mapping) else {}
    liq = packed.get("session_liquidity") if isinstance(packed.get("session_liquidity"), Mapping) else {}
    occ = packed.get("occupancy_book") if isinstance(packed.get("occupancy_book"), Mapping) else {}
    facts: dict[str, Any] = {
        "gold_usd_named": gold_usd.get("named"),
        "gold_index_named": gold_idx.get("named"),
        "risk_named": risk.get("named"),
        "session_named": liq.get("named"),
        "session_source": liq.get("source"),
        "n_clusters_open": occ.get("n_clusters_open"),
        "occupancy_source": occ.get("occupancy_source"),
    }
    decided = _decide(facts, _answer_questions(facts), _ANSWER_SPEC)
    usd_choice = decided.get("gold_usd_comove")
    idx_choice = decided.get("gold_index_comove")
    risk_choice = decided.get("risk_on_funding")
    liq_score = decided.get("session_liquidity")
    occ_score = decided.get("occupancy_world")
    return {
        "gold_usd_comove": {
            "type": "choice",
            "choice": usd_choice,
            "source": "world.gold_vs_usd",
            "decidable": usd_choice is not None,
        },
        "gold_index_comove": {
            "type": "choice",
            "choice": idx_choice,
            "source": "world.gold_vs_index",
            "decidable": idx_choice is not None,
        },
        "risk_on_funding": {
            "type": "choice",
            "choice": risk_choice,
            "source": "world.risk_on",
            "decidable": risk_choice is not None,
        },
        "session_liquidity": {
            "type": "score",
            "score": liq_score,
            "source": "world.session_liquidity",
            "decidable": liq_score is not None,
        },
        "occupancy_world": {
            "type": "score",
            "score": occ_score,
            "source": "world.occupancy_book",
            "decidable": occ_score is not None,
        },
    }

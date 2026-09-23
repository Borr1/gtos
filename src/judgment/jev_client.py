"""TypeSafe System One client.

Key sources (first non-empty wins; never print the value):
  env ``TYPESAFE_API_KEY``, env ``TYPESAFE_KEY``,
  ``TYPESAFE_KEY_FILE`` if set, ``~/.config/typesafe/api_key``,
  ``/run/secrets/TYPESAFE_API_KEY``, ``/run/secrets/TYPESAFE_KEY``,
  repo ``secrets/TYPESAFE_API_KEY.txt`` (host-local),
  repo ``.env.typesafe`` (gitignored).

When a key is present, POST is default-on. Explicit ``GTOS_JEV_A1_CALL=0``
turns calls off. The deadline is the expiry already on the state: the
seconds until the bar prints, or until the next cycle. An ask with no
expiry has no timeout and does not hold another ask. The same question
and the same facts return the remembered answer. No token-budget field
is sent. Model ``jev-1.13.0``. POST
https://api.typesafe.ai/v1/systemone. The return is a Noul, a Choice, or
a Score. An empty answer, a tie, or an error leaves that parameter unset
and does not restore a constant. An exception names itself on the skip
receipt and does not stand in for a decision. The key was already provided
on redacted_account (fingerprint sha256[:8]=00000000). This module does not send
and does not flatten.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .jev_questions import systemone_payload

API_URL = "https://api.typesafe.ai/v1/systemone"
_MODEL = "jev-1.13.0"
_DEPTHS = ("hide", "short", "long", "full")
_ALLOWED_TYPES = {"noul", "choice", "score"}
_PARAM_SPOTS: tuple[str, ...] = ()
_ACCOUNT_IDS = frozenset({
    "score_is",
    "never_enlarge_because_to_pass",
    "friends_copy_lots",
    "never_book_owner",
    "day_start_max",
    "day_net",
    "open_pnl",
    "cash_unit_usd",
})
_ACCOUNT_FACTS = (
    "login",
    "ns",
    "equity",
    "balance",
    "open_pnl",
    "to_pass",
    "floor_room",
    "day_start_balance",
    "day_start_equity",
    "day_start_reset_utc",
    "terminal_read",
    "source",
)
_EXPIRY_KEYS = ("seconds_from_clock", "seconds_until_cycle", "cycle_wait")
_CLOCK_KEYS = {
    "seconds_from_clock",
    "prior_outcomes",
    "as_of_utc",
    "writer_heartbeat_ts",
    "logged_at_utc",
    "ts",
}
_BANNED_QIDS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "flatten_floor_usd",
})
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
)
redacted_account_KEY_FINGERPRINT = "00000000"
VPS_HOST = "redacted_host"

REPO_ROOT = Path(__file__).resolve().parents[2]
_HOME_KEY = Path.home() / ".config" / "typesafe" / "api_key"
_SECRET_FILES = (
    Path("/run/secrets/TYPESAFE_API_KEY"),
    Path("/run/secrets/TYPESAFE_KEY"),
)

_budget_lock = threading.Lock()
_calls_used = 0
_mem_lock = threading.Lock()
_mem_values: dict[str, Any] = {}
_mem_set: set[str] = set()


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


def _logged_value(spot: str) -> Any:
    """Latest logged return for this spot. A miss on that row stays a miss."""
    try:
        from .jev_questions import prior_outcomes

        rows = prior_outcomes(spot=spot)
    except Exception:
        return None
    if not isinstance(rows, list) or not rows:
        return None
    last = rows[-1]
    if not isinstance(last, dict):
        return None
    return last.get("value")


def _stored(spot: str) -> Any:
    with _mem_lock:
        if spot in _mem_set:
            return _mem_values.get(spot)
    return _logged_value(spot)


def _store(spot: str, value: Any) -> None:
    with _mem_lock:
        _mem_values[spot] = value
        _mem_set.add(spot)


def _stored_score(spot: str) -> float | None:
    return _finite(_stored(spot))


def max_calls() -> float | None:
    """The post count this state returned. It does not refuse a post.

    An empty score stays empty. No replacement number is written.
    """
    return _stored_score("jev_max_calls")


def calls_used() -> int:
    with _budget_lock:
        return _calls_used


def calls_remaining() -> float | None:
    cap = max_calls()
    if cap is None:
        return None
    return cap - calls_used()


def reset_call_budget() -> None:
    global _calls_used
    with _budget_lock:
        _calls_used = 0


def _consume_call() -> bool:
    """Count this post. A stored score does not refuse it."""
    global _calls_used
    with _budget_lock:
        _calls_used += 1
        return True


def _read_key_file(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" not in line:
            return line
    return None


def _key_from_env_file(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip("'").strip('"')
        if name in {"TYPESAFE_API_KEY", "TYPESAFE_KEY"} and value:
            found[name] = value
    return found.get("TYPESAFE_API_KEY") or found.get("TYPESAFE_KEY")


def host_key_candidates() -> list[tuple[Path, str]]:
    """VPS/repo drops. Existence only — never read into logs."""
    return [
        (REPO_ROOT / "secrets" / "TYPESAFE_API_KEY.txt", "file:secrets/TYPESAFE_API_KEY.txt"),
        (REPO_ROOT / "secrets" / "TYPESAFE_KEY.txt", "file:secrets/TYPESAFE_KEY.txt"),
        (REPO_ROOT / ".env.typesafe", "file:.env.typesafe"),
        (_HOME_KEY, "file:~/.config/typesafe/api_key"),
        *_SECRET_FILES_LABELED(),
    ]


def _SECRET_FILES_LABELED() -> list[tuple[Path, str]]:
    return [(path, f"file:{path}") for path in _SECRET_FILES]


def host_paths_present() -> list[str]:
    return [label for path, label in host_key_candidates() if path.is_file()]


def resolve_key() -> tuple[str | None, str | None]:
    """Return (key, source_label). Never include the key in receipts."""
    env_api = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if env_api:
        return env_api, "env:TYPESAFE_API_KEY"
    env_key = (os.environ.get("TYPESAFE_KEY") or "").strip()
    if env_key:
        return env_key, "env:TYPESAFE_KEY"
    override = (os.environ.get("TYPESAFE_KEY_FILE") or "").strip()
    if override:
        path = Path(override)
        got = _key_from_env_file(path) or _read_key_file(path)
        if got:
            return got, "file:TYPESAFE_KEY_FILE"
    home = _read_key_file(_HOME_KEY)
    if home:
        return home, "file:~/.config/typesafe/api_key"
    for path in _SECRET_FILES:
        got = _read_key_file(path)
        if got:
            return got, f"file:{path}"
    secrets_txt = REPO_ROOT / "secrets" / "TYPESAFE_API_KEY.txt"
    got = _read_key_file(secrets_txt)
    if got:
        return got, "file:secrets/TYPESAFE_API_KEY.txt"
    secrets_key = REPO_ROOT / "secrets" / "TYPESAFE_KEY.txt"
    got = _read_key_file(secrets_key)
    if got:
        return got, "file:secrets/TYPESAFE_KEY.txt"
    env_file = REPO_ROOT / ".env.typesafe"
    got = _key_from_env_file(env_file)
    if got:
        return got, "file:.env.typesafe"
    return None, None


def api_key() -> str | None:
    key, _source = resolve_key()
    return key


def key_source() -> str | None:
    _key, source = resolve_key()
    return source


def key_fingerprint(key: str | None = None) -> str | None:
    value = key if key is not None else api_key()
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def key_present() -> bool:
    return api_key() is not None


def calls_explicit_off() -> bool:
    return os.environ.get("GTOS_JEV_A1_CALL", "").strip().lower() in {"0", "false", "no", "off"}


def calls_enabled() -> bool:
    if calls_explicit_off():
        return False
    flag = os.environ.get("GTOS_JEV_A1_CALL", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    return key_present()


def _banned_question(qid: str, block: Any) -> bool:
    name = str(qid).strip().lower()
    if name in _BANNED_QIDS or "baseline" in name:
        return True
    try:
        text = json.dumps(block, default=str).lower()
    except Exception:
        text = str(block).lower()
    return any(bit.lower() in text for bit in _BANNED_TEXT)


def _kept_questions(questions: Any) -> dict[str, Any]:
    if not isinstance(questions, dict):
        return {}
    kept: dict[str, Any] = {}
    for key, block in questions.items():
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "").strip().lower()
        if kind not in _ALLOWED_TYPES:
            continue
        if _banned_question(str(key), block):
            continue
        kept[str(key)] = block
    return kept


def _choice_question(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {str(key): str(text) for key, text in criteria.items()}
    return {qid: body}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    body: dict[str, Any] = {"type": "score", "instructions": instructions}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "score"
    body["instructions"] = instructions
    criteria = body.get("criteria")
    if isinstance(criteria, list):
        kept = [item for item in criteria if not _banned_question(str(item), item)]
        body["criteria"] = kept
    return {qid: body}


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes, for this state.",
                "false": "No, for this state.",
            },
        }
    }


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        raw = block.get("Probabilities")
    if not isinstance(raw, dict):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _finite(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: dict[str, float], order: tuple[str, ...]) -> str | None:
    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if abs(probabilities[name] - best) <= 1e-12]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    local = _unique(probabilities, order)
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probabilities, order)
    except Exception:
        agreed = local
    if local is None or agreed is None or str(agreed) != local:
        return None
    return local


def _noul(block: Any) -> bool | float | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is None:
            return None
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    raw = None
    if "score" in block and block.get("score") is not None:
        raw = block.get("score")
    elif "Score" in block and block.get("Score") is not None:
        raw = block.get("Score")
    elif "value" in block and block.get("value") is not None:
        raw = block.get("value")
    number = _finite(raw)
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
    except Exception:
        parsed = number
    if number is None or parsed is None or parsed != number:
        return None
    return number


def _unset_params() -> dict[str, Any]:
    return {spot: None for spot in _PARAM_SPOTS}


def _read_params(answers: Any) -> dict[str, Any]:
    del answers
    return _unset_params()


_history_fit: int | None = None
_MEMO: dict[str, dict[str, Any]] = {}
_MEMO_LOCK = threading.Lock()
_ACCOUNT_MEMO: dict[str, dict[str, Any]] = {}
_ACCOUNT_FLIGHT: set[str] = set()
_ACCOUNT_LOCK = threading.Lock()


def _strip_clocks(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _strip_clocks(item)
            for key, item in value.items()
            if str(key) not in _CLOCK_KEYS
        }
    if isinstance(value, list):
        return [_strip_clocks(item) for item in value]
    return value


def _memo_key(state: Any, questions: Any) -> str:
    body = {"questions": _strip_clocks(questions), "state": _strip_clocks(state)}
    return json.dumps(body, sort_keys=True, default=str)


def _account_key(account: Any) -> str:
    card = account if isinstance(account, dict) else {}
    facts = {key: card.get(key) for key in _ACCOUNT_FACTS}
    return json.dumps(facts, sort_keys=True, default=str)


def _account_pack(questions: Any) -> bool:
    if not isinstance(questions, dict) or not questions:
        return False
    return set(str(key) for key in questions) <= _ACCOUNT_IDS


def _apply_account(account: dict[str, Any], receipt: Mapping[str, Any]) -> None:
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        return
    try:
        from .equity_frame import _NOULS, _SCORE_IS_ORDER
    except Exception:
        _NOULS = {}
        _SCORE_IS_ORDER = ()
    picked = _choice(answers.get("score_is"), tuple(_SCORE_IS_ORDER))
    if picked is not None:
        account["score_is"] = picked
    for qid in ("day_start_max", "day_net", "cash_unit_usd"):
        number = _score(answers.get(qid))
        if number is not None:
            account[qid] = number
    if account.get("open_pnl") is None:
        number = _score(answers.get("open_pnl"))
        if number is not None:
            account["open_pnl"] = number
    for qid in _NOULS:
        value = _noul(answers.get(qid))
        if value is not None:
            account[qid] = value


def _attach_priors(state: dict[str, Any], questions: dict[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state.setdefault("prior_outcomes", [])
        return
    if isinstance(loaded, list) and _history_fit is not None and len(loaded) > _history_fit:
        loaded = loaded[-_history_fit:]
    state["prior_outcomes"] = loaded if loaded is not None else []


def _remember(state: dict[str, Any], params: dict[str, Any], error: str | None) -> None:
    account = state.get("account") if isinstance(state.get("account"), dict) else {}
    facts = {
        "equity": account.get("equity"),
        "balance": account.get("balance"),
        "realized_closed_profit": account.get("realized_closed_profit"),
    }
    try:
        from .jev_questions import append_outcome
    except Exception:
        append_outcome = None  # type: ignore[assignment]
    for spot in _PARAM_SPOTS:
        value = params.get(spot)
        _store(spot, value)
        if append_outcome is None:
            continue
        miss = error if value is None else None
        if value is None and miss is None:
            miss = "unset"
        try:
            append_outcome(spot, value, facts, error=None if value is not None else miss)
        except Exception:
            continue


def _systemone_payload(state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Build one POST body. A nested card stamp stays facts."""
    asking = None
    prior = False
    try:
        from . import equity_frame

        asking = getattr(equity_frame, "_ASK", None)
    except Exception:
        asking = None
    if asking is not None:
        prior = bool(getattr(asking, "on", False))
        asking.on = True
    try:
        payload = systemone_payload(state, **kwargs)
    finally:
        if asking is not None:
            asking.on = prior
    if not isinstance(payload, dict):
        raise TypeError("payload")
    return payload


def _expiry_seconds(state: Any) -> float | None:
    """Seconds until this state expires. None when the ask has no expiry."""

    nodes: list[dict[str, Any]] = []
    if isinstance(state, dict):
        nodes.append(state)
        for key in ("facts", "account", "pair"):
            child = state.get(key)
            if isinstance(child, dict):
                nodes.append(child)
    found: list[float] = []
    for node in nodes:
        for key in _EXPIRY_KEYS:
            number = _finite(node.get(key))
            if number is not None and number > 0:
                found.append(number)
    if not found:
        return None
    return min(found)


def _note_fit(state: Any) -> None:
    global _history_fit
    if not isinstance(state, dict):
        return
    history = state.get("prior_outcomes")
    if isinstance(history, list):
        _history_fit = len(history)


def _shrink_prior(state: dict[str, Any]) -> bool:
    """The older part of this request's history comes off. An empty history stays empty.

    The API names the fit. No planted token count is written.
    """

    if not isinstance(state, dict):
        return False
    history = state.get("prior_outcomes")
    if history in (None, [], {}, ""):
        return False
    before = json.dumps(history, default=str)

    def _tail(items: list[Any]) -> list[Any]:
        if len(items) <= 1:
            return []
        return items[len(items) // 2 :]

    if isinstance(history, list):
        state["prior_outcomes"] = _tail(history)
    elif isinstance(history, str):
        state["prior_outcomes"] = "" if len(history) <= 1 else history[len(history) // 2 :]
    elif isinstance(history, dict):
        recent = history.get("recent")
        earlier = history.get("earlier")
        cut = False
        if isinstance(recent, list) and recent:
            history["recent"] = _tail(recent)
            cut = True
        if isinstance(earlier, str) and earlier:
            history["earlier"] = "" if len(earlier) <= 1 else earlier[len(earlier) // 2 :]
            cut = True
        if not cut:
            state["prior_outcomes"] = []
    else:
        state["prior_outcomes"] = []
    after = json.dumps(state.get("prior_outcomes"), default=str)
    if after == before:
        state["prior_outcomes"] = []
        after = json.dumps(state.get("prior_outcomes"), default=str)
        if after == before:
            return False
    return True


def _skip(reason: str, model: str, **extra: Any) -> dict[str, Any]:
    row = {
        "ok": False,
        "skipped": reason,
        "model": model,
        "answers": {},
        "key_source": key_source(),
        "key_fingerprint": key_fingerprint(),
        "calls_used": calls_used(),
        "calls_remaining": calls_remaining(),
    }
    row.update(extra)
    for spot in _PARAM_SPOTS:
        row.setdefault(spot, None)
    return row


def _remember_scores(account: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        return
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    facts = {
        "equity": account.get("equity"),
        "balance": account.get("balance"),
    }
    for qid in _ACCOUNT_IDS:
        block = answers.get(qid)
        value = _score(block)
        if value is None:
            value = _noul(block)
        if value is None:
            picked = _choice(block, ("live_equity", "balance", "open_pnl", "day_net"))
            value = picked
        try:
            append_outcome(qid, value, facts, error=None if value is not None else "unset")
        except Exception:
            continue


def _start_account(account: Mapping[str, Any]) -> None:
    """One account ask for these facts. It does not hold the decision ask."""

    key = _account_key(account)
    with _ACCOUNT_LOCK:
        if key in _ACCOUNT_MEMO or key in _ACCOUNT_FLIGHT:
            return
        _ACCOUNT_FLIGHT.add(key)
    facts = {name: account.get(name) for name in _ACCOUNT_FACTS}

    def run() -> None:
        try:
            from . import equity_frame
            from .equity_frame import equity_questions

            equity_frame._ASK.on = True
            posted = {
                "login": facts.get("login"),
                "ns": facts.get("ns"),
                "account": dict(facts),
                "order_send": False,
            }
            receipt = _dispatch(posted, equity_questions())
            if isinstance(receipt, dict) and receipt.get("ok") and receipt.get("answers"):
                with _ACCOUNT_LOCK:
                    _ACCOUNT_MEMO[key] = receipt
                _remember_scores(facts, receipt)
        finally:
            with _ACCOUNT_LOCK:
                _ACCOUNT_FLIGHT.discard(key)

    threading.Thread(target=run, name="jev-account", daemon=True).start()


def _dispatch(
    state: dict[str, Any],
    questions: dict[str, Any] | None,
    *,
    extra_questions: dict[str, Any] | None = None,
    seat: str | tuple[str, ...] | None = None,
    merge_sleeve: bool | None = None,
    model: str = _MODEL,
) -> dict[str, Any]:
    """One POST. The wait is the state's expiry. No expiry means no timeout."""

    sent = model or _MODEL
    key, source = resolve_key()
    try:
        payload = _systemone_payload(
            state,
            model=sent,
            extra_questions=extra_questions,
            questions=questions,
            seat=seat,
            merge_sleeve=merge_sleeve,
        )
    except Exception as exc:
        return _skip(type(exc).__name__, sent, invented=False)
    asked = _kept_questions(payload.get("questions"))
    payload["questions"] = asked
    payload["model"] = sent
    body_state = payload.get("state")
    if not isinstance(body_state, dict):
        body_state = dict(state) if isinstance(state, dict) else {}
        payload["state"] = body_state
    _attach_priors(body_state, asked)
    payload_keys = list(asked)
    if not key:
        return _skip("TYPESAFE_key_absent", sent, would_payload_keys=payload_keys)
    if not calls_enabled():
        return _skip("GTOS_JEV_A1_CALL_off", sent, would_payload_keys=payload_keys)
    _consume_call()
    wait = _expiry_seconds(state)
    try:
        parsed: Any = None
        status = None
        while True:
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                API_URL,
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": "gtos-judgment/0.1",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=wait) as resp:
                    parsed = json.loads(resp.read().decode("utf-8"))
                    status = getattr(resp, "status", None)
                break
            except urllib.error.HTTPError as exc:
                try:
                    detail = exc.read()
                except Exception:
                    detail = b""
                if isinstance(detail, str):
                    detail = detail.encode("utf-8", errors="replace")
                refused = exc.code == 400 and b"max_tokens_exceeded" in detail
                if refused and isinstance(body_state, dict) and _shrink_prior(body_state):
                    continue
                params = _unset_params()
                _remember(body_state, params, f"http_{exc.code}")
                return {
                    "ok": False,
                    "skipped": None,
                    "error": f"http_{exc.code}",
                    "http_status": exc.code,
                    "model": sent,
                    "answers": {},
                    "key_source": source,
                    "key_fingerprint": key_fingerprint(key),
                    "calls_used": calls_used(),
                    "calls_remaining": calls_remaining(),
                    **params,
                }
        answers = parsed.get("answers") if isinstance(parsed, dict) else None
        if not isinstance(answers, dict):
            answers = {}
        _note_fit(body_state)
        params = _read_params(answers)
        _remember(body_state, params, None if answers else "empty")
        reported = parsed.get("model") if isinstance(parsed, dict) else None
        usage = parsed.get("usage") if isinstance(parsed, dict) else None
        return {
            "ok": True,
            "skipped": None,
            "model": reported if isinstance(reported, str) and reported.strip() else sent,
            "answers": answers,
            "usage": usage if isinstance(usage, dict) else {},
            "key_source": source,
            "key_fingerprint": key_fingerprint(key),
            "http_status": status,
            "calls_used": calls_used(),
            "calls_remaining": calls_remaining(),
            **params,
        }
    except Exception as exc:  # noqa: BLE001 — fire-path must never raise
        params = _unset_params()
        _remember(body_state, params, type(exc).__name__)
        return {
            "ok": False,
            "skipped": None,
            "error": type(exc).__name__,
            "http_status": None,
            "model": sent,
            "answers": {},
            "key_source": source,
            "key_fingerprint": key_fingerprint(key),
            "calls_used": calls_used(),
            "calls_remaining": calls_remaining(),
            **params,
        }


def evaluate(
    state: dict[str, Any],
    *,
    timeout_s: float | None = None,
    model: str = _MODEL,
    extra_questions: dict[str, Any] | None = None,
    questions: dict[str, Any] | None = None,
    seat: str | tuple[str, ...] | None = None,
    include_depth: str | None = None,
    merge_sleeve: bool | None = None,
    require_equity: bool | None = None,
) -> dict[str, Any]:
    """POST /v1/systemone. The decision ask does not wait on another ask.

    Questions on the wire are Noul, Choice, or Score. The same question and
    the same facts return the remembered answer. Account scores are asked
    once for an account state, beside the decision, not before it. The wait
    is the expiry on the state. An ask with no expiry has no timeout.
    ``timeout_s``, ``include_depth``, and ``require_equity`` do not cap this
    post. This post does not send.
    """

    del timeout_s, include_depth, require_equity
    sent = model or _MODEL
    if not isinstance(state, dict):
        state = {}
    if _account_pack(questions) and not extra_questions and seat is None:
        card = state.get("account") if isinstance(state.get("account"), dict) else state
        key = _account_key(card)
        with _ACCOUNT_LOCK:
            hit = _ACCOUNT_MEMO.get(key)
        if hit is not None:
            return dict(hit)
        receipt = _dispatch(state, questions, merge_sleeve=merge_sleeve, model=sent)
        if receipt.get("ok") and receipt.get("answers"):
            with _ACCOUNT_LOCK:
                _ACCOUNT_MEMO[key] = receipt
        return receipt
    try:
        from . import equity_frame
        from .equity_frame import attach_account

        asking = equity_frame._ASK
        prior_on = bool(getattr(asking, "on", False))
        asking.on = True
        try:
            state = attach_account(state)
        finally:
            asking.on = prior_on
    except Exception as exc:
        return _skip(type(exc).__name__, sent, invented=False)
    account = state.get("account") if isinstance(state.get("account"), dict) else None
    if isinstance(account, dict):
        key = _account_key(account)
        with _ACCOUNT_LOCK:
            hit = _ACCOUNT_MEMO.get(key)
        if hit is not None:
            _apply_account(account, hit)
        else:
            _start_account(account)
    memo_key = _memo_key(state, questions)
    with _MEMO_LOCK:
        cached = _MEMO.get(memo_key)
    if cached is not None:
        return dict(cached)
    receipt = _dispatch(
        state,
        questions,
        extra_questions=extra_questions,
        seat=seat,
        merge_sleeve=merge_sleeve,
        model=sent,
    )
    if receipt.get("ok") and receipt.get("answers"):
        with _MEMO_LOCK:
            _MEMO[memo_key] = receipt
    return receipt

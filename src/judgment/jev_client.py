"""TypeSafe System One client.

Key sources (first non-empty wins; never print the value):
  env ``TYPESAFE_API_KEY``, env ``TYPESAFE_KEY``,
  ``TYPESAFE_KEY_FILE`` if set, ``~/.config/typesafe/api_key``,
  ``/run/secrets/TYPESAFE_API_KEY``, ``/run/secrets/TYPESAFE_KEY``,
  repo ``secrets/TYPESAFE_API_KEY.txt`` (host-local),
  repo ``.env.typesafe`` (gitignored).

When a key is present, POST is default-on. Explicit ``GTOS_JEV_A1_CALL=0``
turns calls off. One POST carries the decision. Account questions for a
snapshot that has no frame yet, and any parameter not yet returned for
these facts, are heads on that same POST. A later ask with the same facts
does not send them again. The deadline is the expiry already on the state:
the seconds until the bar prints, or until the next cycle. An ask with no
expiry has no timeout. A returned score is not that deadline. A 429, 503,
or 529 is asked again only when Retry-After fits before that deadline.
The same card is one in-flight post. Waiters share that receipt. Only an
ok receipt with answers is remembered. Every ask is a stream on the one
shared connection. A dead connection settles only the ask that noticed it.
The account pack runs on its own thread and a decision does not join it.
A Score with no criteria does not post. No token-budget field is sent. Model
``jev-1.13.0``. POST https://api.typesafe.ai/v1/systemone. The return is a
Noul, a Choice, or a Score. An empty answer, a tie, or an error leaves
that parameter unset and does not restore a constant. An exception names
itself on the skip receipt and does not stand in for a decision. The key
was already provided on redacted_account (fingerprint sha256[:8]=00000000). This
module does not send and does not flatten.
"""

from __future__ import annotations

import hashlib
import http.client
import io
import json
import os
import threading
import time
import urllib.error
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

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
# Asked once for the facts they see. A trade Choice is not in this set.
_PARAM_IDS = frozenset({
    "jev_call_timeout",
    "jev_max_calls",
    "jev_require_equity",
    "jev_include_depth",
    "persist_weight",
    "unit_usd",
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
    "earlier",
    "recent",
    "earlier_legend",
    "as_of_utc",
    "writer_heartbeat_ts",
    "logged_at_utc",
    "ts",
}
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
    """A planted floor or target dollar in the question text does not post.

    The question id is not a filter. A name that only contains those words
    still posts. ``qid`` is unused here and stays in the signature so callers
    keep the question they built.
    """

    del qid
    if isinstance(block, dict):
        parts = [str(block.get("instructions") or "")]
        kind = str(block.get("type") or "").strip().lower()
        criteria = block.get("criteria")
        # A Score level is the card's own amount. 90000 there is that amount,
        # not a planted floor written into the question.
        if kind != "score":
            if isinstance(criteria, dict):
                parts.extend(str(value) for value in criteria.values())
            elif isinstance(criteria, list):
                parts.extend(str(value) for value in criteria)
        text = "\n".join(parts).lower()
    else:
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


def _score_question(qid: str, instructions: str, anchors: Any = None) -> dict[str, Any]:
    """An amount Score. No anchors means no criteria, so this does not post."""

    try:
        from .jev_questions import amount_question

        return amount_question(qid, instructions, anchors)
    except Exception:
        return {}


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
_FIT_LOCK = threading.Lock()
_MEMO: dict[str, dict[str, Any]] = {}
_MEMO_LOCK = threading.Lock()
_ACCOUNT_MEMO: dict[str, dict[str, Any]] = {}
_ACCOUNT_FLIGHT: dict[str, "_Gate"] = {}
_ACCOUNT_LOCK = threading.Lock()
_ASK_LOCK = threading.RLock()
_OWNED = threading.local()


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


def _memo_key(
    state: Any,
    questions: Any,
    extra: Any = None,
    seat: Any = None,
) -> str:
    seat_key: Any
    if isinstance(seat, str) or seat is None:
        seat_key = seat
    else:
        seat_key = [str(item) for item in seat]
    body = {
        "questions": _strip_clocks(questions),
        "extra": _strip_clocks(extra),
        "seat": seat_key,
        "state": _strip_clocks(state),
    }
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
    if isinstance(loaded, list):
        with _FIT_LOCK:
            fit = _history_fit
        if fit is not None and len(loaded) > fit:
            loaded = loaded[-fit:]
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


def _call_under_ask(fn: Callable[[], Any]) -> Any:
    """Run ``fn`` while this thread's card stamp is on.

    The flag is restored before the call returns. The lock keeps one
    evaluate from clearing the flag another evaluate is inside. The POST
    itself is outside this lock.
    """

    try:
        from . import equity_frame

        asking = getattr(equity_frame, "_ASK", None)
    except Exception:
        asking = None
    if asking is None:
        return fn()
    with _ASK_LOCK:
        prior = bool(getattr(asking, "on", False))
        asking.on = True
        try:
            return fn()
        finally:
            asking.on = prior


def _systemone_payload(state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Build one POST body. A nested card stamp stays facts."""

    payload = _call_under_ask(lambda: systemone_payload(state, **kwargs))
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
        with _FIT_LOCK:
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


_PARAM_ANSWERS: dict[str, Any] = {}
_PARAM_LOCK = threading.Lock()
_HTTP: Any = None
_HTTP_LOCK = threading.Lock()
_OVERLOADED = frozenset({429, 503, 529})


class _Gate:
    """One in-flight ask. Waiters block on the event. Other cards do not."""

    def __init__(self) -> None:
        self.event = threading.Event()
        self.receipt: Any = None


_FLIGHT: dict[str, _Gate] = {}


class _UrllibConn:
    """One HTTP/1.1 connection. A failed request closes it for the next ask."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn: http.client.HTTPSConnection | None = None

    def close(self) -> None:
        with self._lock:
            self._close_raw()

    def _close_raw(self) -> None:
        conn = self._conn
        self._conn = None
        if conn is None:
            return
        try:
            conn.close()
        except Exception:
            return

    def post(self, key: str, payload: Mapping[str, Any], timeout: float | None) -> tuple[Any, int | None, Any]:
        parsed = urlparse(API_URL)
        path = parsed.path or "/"
        if parsed.query:
            path = path + "?" + parsed.query
        host = parsed.hostname or ""
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "User-Agent": "gtos-judgment/0.1",
        }
        with self._lock:
            if self._conn is None:
                self._conn = http.client.HTTPSConnection(host, timeout=timeout)
            sock = getattr(self._conn, "sock", None)
            if sock is not None:
                sock.settimeout(timeout)
            try:
                self._conn.request("POST", path, body=data, headers=headers)
                resp = self._conn.getresponse()
                raw = resp.read()
                status = getattr(resp, "status", None)
                hdrs = getattr(resp, "headers", None)
            except Exception:
                self._close_raw()
                raise
        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        return json.loads(text), status, hdrs


def _open_client() -> Any:
    """One client. HTTP/2 when that package is present, else one urllib connection."""

    try:
        import httpx
    except Exception:
        return _UrllibConn()
    try:
        return httpx.Client(http2=True, timeout=None)
    except ImportError:
        return httpx.Client(http2=False, timeout=None)
    except Exception:
        return _UrllibConn()


def _http() -> Any:
    """The shared client. Tasks do not construct one."""

    global _HTTP
    with _HTTP_LOCK:
        if _HTTP is None:
            _HTTP = _open_client()
        return _HTTP


def _retire(client: Any) -> None:
    """Drop a dead client. The ask that noticed it is the only one settled here."""

    global _HTTP
    with _HTTP_LOCK:
        if _HTTP is not client:
            return
        _HTTP = None
    if isinstance(client, _UrllibConn):
        client.close()


def _dead_connection(exc: BaseException) -> bool:
    """A transport failure. An HTTP status and an expired ask are not this."""

    if isinstance(exc, (TimeoutError, urllib.error.HTTPError)):
        return False
    if "Timeout" in type(exc).__name__:
        return False
    if isinstance(exc, (ConnectionError, http.client.HTTPException)):
        return True
    if isinstance(exc, urllib.error.URLError):
        return True
    return type(exc).__name__ in {
        "ConnectError",
        "ReadError",
        "WriteError",
        "CloseError",
        "RemoteProtocolError",
        "NetworkError",
    }


def _send(client: Any, key: str, payload: Mapping[str, Any], timeout: float | None) -> tuple[Any, int | None, Any]:
    if isinstance(client, _UrllibConn):
        return client.post(key, payload, timeout)
    response = client.post(
        API_URL,
        json=dict(payload),
        headers={
            "Authorization": "Bearer " + key,
            "User-Agent": "gtos-judgment/0.1",
        },
        timeout=timeout,
    )
    status = int(response.status_code)
    return response.json(), status, response.headers


def _owns(key: str) -> bool:
    owned = getattr(_OWNED, "keys", None)
    return isinstance(owned, set) and key in owned


def _claim(key: str) -> None:
    owned = getattr(_OWNED, "keys", None)
    if not isinstance(owned, set):
        owned = set()
        _OWNED.keys = owned
    owned.add(key)


def _release(key: str) -> None:
    owned = getattr(_OWNED, "keys", None)
    if isinstance(owned, set):
        owned.discard(key)


def _remember_ok(store: dict[str, dict[str, Any]], key: str, receipt: Any, lock: threading.Lock) -> None:
    if isinstance(receipt, dict) and receipt.get("ok") and receipt.get("answers"):
        with lock:
            store[key] = receipt


def _fact_key(state: Mapping[str, Any], qid: str) -> str:
    if qid in _ACCOUNT_IDS:
        account = state.get("account") if isinstance(state.get("account"), Mapping) else {}
        return "account\n" + _account_key(account)
    return "state\n" + json.dumps(_strip_clocks(state), sort_keys=True, default=str)


def _param_slot(qid: str, state: Mapping[str, Any]) -> str:
    return str(qid) + "\n" + _fact_key(state, qid)


def _known_blocks(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """Answer blocks already returned for these facts. A trade question is not known."""

    known: dict[str, Any] = {}
    with _PARAM_LOCK:
        for qid in questions:
            if qid not in _PARAM_IDS and qid not in _ACCOUNT_IDS:
                continue
            slot = _param_slot(str(qid), state)
            if slot in _PARAM_ANSWERS:
                known[str(qid)] = _PARAM_ANSWERS[slot]
    return known


def _store_asked(state: Mapping[str, Any], wire: Mapping[str, Any], answers: Mapping[str, Any]) -> None:
    """A successful post is the answer, including an empty score. An error never arrives here."""

    with _PARAM_LOCK:
        for qid in wire:
            if qid not in _PARAM_IDS and qid not in _ACCOUNT_IDS:
                continue
            block = answers.get(qid)
            _PARAM_ANSWERS[_param_slot(str(qid), state)] = block if isinstance(block, dict) else {}


def _has_decision(questions: Mapping[str, Any]) -> bool:
    for block in questions.values():
        if isinstance(block, dict) and str(block.get("type") or "").lower() in {"choice", "noul"}:
            return True
    return False


def _account_ready(account: Mapping[str, Any]) -> bool:
    try:
        from .equity_frame import frame_ready

        return bool(frame_ready(account))
    except Exception:
        key = _account_key(account)
        with _ACCOUNT_LOCK:
            return key in _ACCOUNT_MEMO


def _with_account_heads(
    state: Mapping[str, Any],
    wire: dict[str, Any],
    known: Mapping[str, Any],
) -> dict[str, Any]:
    """Account questions ride on this post when the snapshot has no frame."""

    account = state.get("account") if isinstance(state.get("account"), Mapping) else None
    if not isinstance(account, Mapping) or _account_ready(account):
        return wire
    try:
        from .equity_frame import equity_questions
    except Exception:
        return wire
    merged = dict(wire)
    for qid, block in equity_questions(account).items():
        if qid in merged or qid in known:
            continue
        if not isinstance(block, dict) or _banned_question(str(qid), block):
            continue
        merged[str(qid)] = block
    return merged


def _note_account(state: Mapping[str, Any], receipt: Mapping[str, Any], wire: Mapping[str, Any]) -> None:
    if not any(qid in wire for qid in _ACCOUNT_IDS):
        return
    account = state.get("account")
    if not isinstance(account, dict):
        return
    try:
        from .equity_frame import note_receipt

        note_receipt(account, receipt)
    except Exception:
        return


def _header(headers: Any, name: str) -> Any:
    if headers is None:
        return None
    try:
        return headers.get(name)
    except Exception:
        return None


def _retry_after_seconds(raw: Any, now: float) -> float | None:
    """Seconds named by Retry-After. A missing header names no pause."""

    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime

        moment = parsedate_to_datetime(text)
    except Exception:
        return None
    if moment is None:
        return None
    if moment.tzinfo is None:
        from datetime import timezone

        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp() - now


def _retry_pause(headers: Any, deadline: float | None) -> float | None:
    """Pause from Retry-After when it still fits before the state's expiry."""

    now = time.time()
    if deadline is not None and now >= deadline:
        return None
    pause = _retry_after_seconds(_header(headers, "Retry-After"), now)
    if pause is None:
        return None
    if pause < 0:
        pause = 0.0
    if deadline is not None and now + pause > deadline:
        return None
    return pause


def _remaining(deadline: float | None, wait: float | None) -> float | None:
    if deadline is None:
        return wait
    remaining = deadline - time.time()
    if remaining < 0:
        return 0.0
    return remaining


def _criteria_labels(block: Mapping[str, Any]) -> list[str] | None:
    criteria = block.get("criteria")
    if not isinstance(criteria, list):
        return None
    labels = [str(item).strip() for item in criteria if str(item).strip()]
    if len(labels) < 2:
        return None
    return labels


def _split_questions(questions: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, list[tuple[str, float]]], bool]:
    """Drop a Score that has no criteria. Keep anchor values off the wire."""

    postable: dict[str, Any] = {}
    anchors: dict[str, list[tuple[str, float]]] = {}
    bare = False
    for qid, block in questions.items():
        if not isinstance(block, dict):
            continue
        body = dict(block)
        values = body.pop("_anchor_values", None)
        kind = str(body.get("type") or "").strip().lower()
        if kind == "score":
            labels = _criteria_labels(body)
            if not labels:
                bare = True
                continue
            if values is not None:
                ok = isinstance(values, list) and len(values) == len(labels)
                nums: list[float] = []
                if ok:
                    for item in values:
                        number = _finite(item)
                        if number is None:
                            ok = False
                            break
                        nums.append(number)
                if not ok:
                    bare = True
                    continue
                anchors[str(qid)] = list(zip(labels, nums))
            body["criteria"] = labels
        postable[str(qid)] = body
    return postable, anchors, bare


def _rewrite_anchors(answers: dict[str, Any], anchors: Mapping[str, list[tuple[str, float]]]) -> dict[str, Any]:
    """Replace a level position with the value on the card's anchors."""

    if not anchors:
        return answers
    from .jev_questions import interpolate, unique_highest

    out = dict(answers)
    for qid, levels in anchors.items():
        block = out.get(qid)
        if not isinstance(block, dict):
            continue
        body = dict(block)
        if body.get("error") or body.get("tie") is True:
            body["score"] = None
            out[qid] = body
            continue
        probabilities = body.get("probabilities")
        if isinstance(probabilities, dict) and probabilities and unique_highest(probabilities) is None:
            body["score"] = None
            out[qid] = body
            continue
        body["score"] = interpolate(_score(body), list(levels))
        out[qid] = body
    return out


def _transmit(key: str, payload: Mapping[str, Any], wait: float | None) -> tuple[Any, int | None]:
    """One stream on the shared connection.

    429, 503, and 529 follow Retry-After when it fits the deadline. No expiry
    means no timeout. A returned score is never this wait. A missing
    Retry-After does not invent a pause. A dead connection is raised here.
    The caller settles this ask and leaves every other ask on the replacement.
    """

    deadline = None if wait is None else time.time() + float(wait)
    while True:
        timeout = _remaining(deadline, wait)
        if deadline is not None and timeout == 0:
            raise TimeoutError("deadline")
        client = _http()
        try:
            parsed, status, headers = _send(client, key, payload, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in _OVERLOADED:
                pause = _retry_pause(exc.headers, deadline)
                if pause is not None:
                    time.sleep(pause)
                    continue
            raise
        except Exception as exc:
            if _dead_connection(exc):
                _retire(client)
            raise
        if status in _OVERLOADED:
            pause = _retry_pause(headers, deadline)
            if pause is not None:
                time.sleep(pause)
                continue
        if status is not None and status >= 400:
            raise urllib.error.HTTPError(
                API_URL,
                int(status),
                "",
                hdrs=headers,
                fp=io.BytesIO(json.dumps(parsed, default=str).encode("utf-8")),
            )
        return parsed, status


def _http_error(exc: urllib.error.HTTPError) -> tuple[int, bytes]:
    detail = b""
    try:
        raw = exc.read() if exc.fp is not None else b""
    except Exception:
        raw = b""
    if isinstance(raw, str):
        raw = raw.encode("utf-8", errors="replace")
    if isinstance(raw, (bytes, bytearray)):
        detail = bytes(raw)
    return int(exc.code), detail


def _filled(sent: str, source: str | None, key: str | None, answers: dict[str, Any], *, status: int | None, usage: Any, reported: Any) -> dict[str, Any]:
    params = _unset_params()
    return {
        "ok": True,
        "skipped": None,
        "model": reported if isinstance(reported, str) and reported.strip() else sent,
        "answers": answers,
        "usage": usage if isinstance(usage, dict) else {},
        "key_source": source,
        "key_fingerprint": key_fingerprint(key) if key else None,
        "http_status": status,
        "calls_used": calls_used(),
        "calls_remaining": calls_remaining(),
        **params,
    }


def _thin_posted_scores(wire: Mapping[str, Any], anchors: dict[str, list[tuple[str, float]]]) -> dict[str, Any] | None:
    """Drop Score levels to the maximum a refusal just named. One pass."""

    from .nineteen import kept_indexes

    rebuilt: dict[str, Any] = {}
    changed = False
    for qid, block in wire.items():
        if not isinstance(block, dict) or str(block.get("type") or "").lower() != "score":
            rebuilt[str(qid)] = block
            continue
        criteria = block.get("criteria")
        if not isinstance(criteria, list):
            rebuilt[str(qid)] = block
            continue
        ranks = kept_indexes(len(criteria))
        if not ranks or len(ranks) == len(criteria):
            rebuilt[str(qid)] = block
            continue
        body = dict(block)
        body["criteria"] = [criteria[index] for index in ranks]
        levels = anchors.get(str(qid))
        if isinstance(levels, list) and len(levels) == len(criteria):
            anchors[str(qid)] = [levels[index] for index in ranks]
        changed = True
        rebuilt[str(qid)] = body
    if not changed:
        return None
    return rebuilt


def _dispatch(
    state: dict[str, Any],
    questions: dict[str, Any] | None,
    *,
    extra_questions: dict[str, Any] | None = None,
    seat: str | tuple[str, ...] | None = None,
    merge_sleeve: bool | None = None,
    model: str = _MODEL,
    stamp_account: bool = True,
) -> dict[str, Any]:
    """One POST. Known parameters stay off the wire. The wait is the state's expiry."""

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
    payload["model"] = sent
    body_state = payload.get("state")
    if not isinstance(body_state, dict):
        body_state = dict(state) if isinstance(state, dict) else {}
        payload["state"] = body_state
    known = _known_blocks(body_state, asked)
    wire = {qid: block for qid, block in asked.items() if qid not in known}
    if _has_decision(asked):
        wire = _with_account_heads(body_state, wire, known)
    wire, anchors, bare = _split_questions(wire)
    payload["questions"] = wire
    _attach_priors(body_state, wire or asked)
    if not wire:
        if bare and not known:
            return None
        return _filled(sent, source, key, dict(known), status=None, usage={}, reported=sent)
    payload_keys = list(wire)
    if not key:
        return _skip("TYPESAFE_key_absent", sent, would_payload_keys=payload_keys)
    if not calls_enabled():
        return _skip("GTOS_JEV_A1_CALL_off", sent, would_payload_keys=payload_keys)
    _consume_call()
    wait = _expiry_seconds(body_state)
    if wait is None:
        wait = _expiry_seconds(state)
    try:
        parsed: Any = None
        status = None
        while True:
            try:
                parsed, status = _transmit(key, payload, wait)
                break
            except urllib.error.HTTPError as exc:
                code, detail = _http_error(exc)
                text = detail.decode("utf-8", errors="replace")
                refused = code == 400 and b"max_tokens_exceeded" in detail
                if refused and isinstance(body_state, dict) and _shrink_prior(body_state):
                    continue
                from .nineteen import learned_score_level_cap, note_score_level_cap

                known = learned_score_level_cap()
                note_score_level_cap(text)
                learned = learned_score_level_cap()
                if learned is not None and learned != known:
                    thinned = _thin_posted_scores(wire, anchors)
                    if thinned is not None:
                        wire = thinned
                        payload["questions"] = wire
                        continue
                params = _unset_params()
                _remember(body_state, params, f"http_{code}")
                return {
                    "ok": False,
                    "skipped": None,
                    "error": f"http_{code}",
                    "detail": text,
                    "http_status": code,
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
        _store_asked(body_state, wire, answers)
        merged = dict(known)
        merged.update(answers)
        merged = _rewrite_anchors(merged, anchors)
        reported = parsed.get("model") if isinstance(parsed, dict) else None
        usage = parsed.get("usage") if isinstance(parsed, dict) else None
        params = _read_params(merged)
        _remember(body_state, params, None if merged else "empty")
        receipt = _filled(
            sent,
            source,
            key,
            merged,
            status=status,
            usage=usage,
            reported=reported,
        )
        if stamp_account:
            _note_account(body_state, receipt, wire)
        return receipt
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


def _account_on_thread(
    state: dict[str, Any],
    questions: dict[str, Any] | None,
    key: str,
    *,
    merge_sleeve: bool | None,
    model: str,
) -> Any:
    """One daemon for this account card. A decision does not call this and does not join it."""

    with _ACCOUNT_LOCK:
        hit = _ACCOUNT_MEMO.get(key)
        if hit is not None:
            return dict(hit)
        gate = _ACCOUNT_FLIGHT.get(key)
        if gate is None:
            gate = _Gate()
            _ACCOUNT_FLIGHT[key] = gate
            leader = True
        else:
            leader = False
    if not leader:
        if _owns(key):
            return None
        gate.event.wait()
        receipt = gate.receipt
        if receipt is None:
            return None
        return dict(receipt) if isinstance(receipt, dict) else _skip("empty", model)

    def run() -> None:
        _claim(key)
        try:
            receipt = _dispatch(
                state,
                questions,
                merge_sleeve=merge_sleeve,
                model=model,
                stamp_account=False,
            )
            gate.receipt = receipt
            _remember_ok(_ACCOUNT_MEMO, key, receipt, _ACCOUNT_LOCK)
        finally:
            _release(key)
            gate.event.set()
            with _ACCOUNT_LOCK:
                if _ACCOUNT_FLIGHT.get(key) is gate:
                    _ACCOUNT_FLIGHT.pop(key, None)

    worker = threading.Thread(target=run, name="jev-account", daemon=True)
    try:
        worker.start()
    except Exception as exc:
        gate.receipt = _skip(type(exc).__name__, model, invented=False)
        gate.event.set()
        with _ACCOUNT_LOCK:
            if _ACCOUNT_FLIGHT.get(key) is gate:
                _ACCOUNT_FLIGHT.pop(key, None)
        return gate.receipt
    gate.event.wait()
    receipt = gate.receipt
    if receipt is None:
        return None
    return dict(receipt) if isinstance(receipt, dict) else receipt


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
    """POST /v1/systemone. The decision question is the critical-path call.

    Questions on the wire are Noul, Choice, or Score. Independent heads share
    that post. A parameter already returned for these facts is left off the
    wire and copied onto the receipt. The same question and the same facts
    return the remembered answer. The wait is the expiry on the state. An ask
    with no expiry has no timeout. A returned score is not that wait.
    ``timeout_s``, ``include_depth``, and ``require_equity`` do not cap this
    post. This post does not send.
    """

    del timeout_s, include_depth, require_equity
    sent = model or _MODEL
    if not isinstance(state, dict):
        state = {}
    if _account_pack(questions) and not extra_questions and seat is None:
        card = state.get("account") if isinstance(state.get("account"), dict) else state
        return _account_on_thread(
            state,
            questions,
            _account_key(card),
            merge_sleeve=merge_sleeve,
            model=sent,
        )
    try:
        from .equity_frame import attach_account

        state = _call_under_ask(lambda: attach_account(state))
    except Exception as exc:
        return _skip(type(exc).__name__, sent, invented=False)
    account = state.get("account") if isinstance(state.get("account"), dict) else None
    if isinstance(account, dict) and _account_ready(account):
        with _ACCOUNT_LOCK:
            hit = _ACCOUNT_MEMO.get(_account_key(account))
        if hit is not None:
            _apply_account(account, hit)
    memo_key = _memo_key(state, questions, extra_questions, seat)
    with _MEMO_LOCK:
        cached = _MEMO.get(memo_key)
        if cached is not None:
            return dict(cached)
        gate = _FLIGHT.get(memo_key)
        if gate is None:
            gate = _Gate()
            _FLIGHT[memo_key] = gate
            leader = True
        else:
            leader = False
    if not leader:
        if _owns(memo_key):
            return None
        gate.event.wait()
        receipt = gate.receipt
        if receipt is None:
            return None
        return dict(receipt) if isinstance(receipt, dict) else _skip("empty", sent)

    def run() -> Any:
        return _dispatch(
            state,
            questions,
            extra_questions=extra_questions,
            seat=seat,
            merge_sleeve=merge_sleeve,
            model=sent,
        )

    _claim(memo_key)
    try:
        receipt = run()
        gate.receipt = receipt
        _remember_ok(_MEMO, memo_key, receipt, _MEMO_LOCK)
        return receipt
    finally:
        _release(memo_key)
        gate.event.set()
        with _MEMO_LOCK:
            if _FLIGHT.get(memo_key) is gate:
                _FLIGHT.pop(memo_key, None)

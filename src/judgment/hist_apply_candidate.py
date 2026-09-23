"""HIST_APPLY_CANDIDATE_V0 — measured FTMO M15 names, default-OFF.

Unique file. Unset env skips the ask. Chair label only.

The verdict and each parameter are the System One return for that state.
The call is ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only a Noul, a Choice, or a Score. Prior outcomes are on
the ask. An empty answer, a tie, or an error leaves that return unset.
A floor and a baseline are not a question. This module does not send.

Measured names and keep-set rows ride the state as facts. The label is
the returned choice.

Host hook (observer, env-gate BEFORE import)::

    if os.environ.get("GTOS_JEV_HIST_APPLY", "").strip().lower() in {"1", "true", "yes"}:
        from src.judgment.hist_apply_candidate import maybe_label
        maybe_label(candidates=..., login=0)

Absence of the env is off. This module does not place, flatten, or tag.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from .rung_choice import append_record, namespace_root, open_pair, read_json

MappingLike = Mapping[str, Any]

SCHEMA = "gtos.judgment.hist_apply_candidate.v0"
HIST_APPLY_ENV = "GTOS_JEV_HIST_APPLY"
HIST_APPLY_PATH_ENV = "GTOS_JEV_HIST_APPLY_PATH"
MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

CHALLENGE_LOGIN = "0"
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "hist_apply_candidate" / "fixtures"
)
DEFAULT_KEEP_SET = DEFAULT_FIXTURE_DIR / "keep_set.json"
DEFAULT_STORE = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "hist_apply_candidate" / "store.jsonl"
)

W7_ARMED_TAGS = frozenset({"crypto", "energy_agri", "sub_xvol_pullback"})
US30_STEMS = frozenset({"US30", "US30_CASH", "US30CASH"})
NAMED_FX_MID_DN = frozenset({"EURUSD", "GBPJPY", "EURGBP", "GBPUSD", "EURJPY"})
MID_DN_SLEEVE = "sub_mid_dn_revert"
CRYPTO_NY_SLEEVE = "ny_crypto_momentum"
CRYPTO_H4_SLEEVE = "crypto"
BTC_SYMBOL = "BTCUSD"

# Chair 2026-09-21 named tickets. The list is a fact. This module never flattens.
CHAIR_NAMED_OPEN_TICKETS = frozenset({294092360, 294088097})
CHAIR_NAMED_CLOSED_NO_TOUCH = frozenset({294069721})
LEAVE_ORIG_TICKETS = frozenset({293332188}) | CHAIR_NAMED_OPEN_TICKETS | CHAIR_NAMED_CLOSED_NO_TOUCH

# Measured name menu from the walk. Membership is a fact on the state.
APPLY_KEEP_KEYS: tuple[tuple[str, str], ...] = (
    ("EURUSD", "asian_fade"),
    ("GBPUSD", "asian_fade"),
    ("NZDUSD", "asian_fade"),
    ("USDJPY", "asian_fade"),
    ("GBPJPY", "fx_jpy"),
    ("USDJPY", "fx_jpy"),
    ("USDJPY", "fx_jpy_ny"),
)
APPLY_KEEP = frozenset(APPLY_KEEP_KEYS)

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")
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
_VERDICT_ORDER = ("APPLY_CANDIDATE", "KILL")
_IDENTITY_ORDER = (
    "challenge",
    "verification_quarantined",
    "study_not_challenge",
    "w7_other_organism",
    "namespace_not_challenge",
    "login_not_challenge",
    "identity_missing",
)
_COMPONENT_ORDER = (
    "apply_keep",
    "us30",
    "named_fx_mid_dn",
    "crypto_ny",
    "notable_kill",
    "other",
)
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

# field, kind, question id, choice order
_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("verdict", "choice", "hist_verdict", _VERDICT_ORDER),
    ("identity", "choice", "hist_identity", _IDENTITY_ORDER),
    ("component", "choice", "hist_component", _COMPONENT_ORDER),
    ("identity_ok", "noul", "hist_identity_ok", ("true", "false")),
    ("apply", "noul", "hist_apply", ("true", "false")),
    ("silent_apply", "noul", "hist_silent_apply", ("true", "false")),
    ("writer_tag", "noul", "hist_writer_tag", ("true", "false")),
    ("extra_pass", "noul", "hist_extra_pass", ("true", "false")),
    ("flatten", "noul", "hist_flatten", ("true", "false")),
    ("size_up", "noul", "hist_size_up", ("true", "false")),
    ("pin_ok", "noul", "hist_pin_ok", ("true", "false")),
    ("fail_closed", "noul", "hist_fail_closed", ("true", "false")),
    ("on_surface", "noul", "hist_on_surface", ("true", "false")),
    ("ci_includes_zero", "noul", "hist_ci_includes_zero", ("true", "false")),
    ("headline", "noul", "hist_headline", ("true", "false")),
    ("off_surface", "noul", "hist_off_surface", ("true", "false")),
    ("cost_kill", "noul", "hist_cost_kill", ("true", "false")),
    ("walked", "noul", "hist_walked", ("true", "false")),
    ("component_exists", "noul", "hist_component_exists", ("true", "false")),
    ("overlay_copied", "noul", "hist_overlay_copied", ("true", "false")),
    ("state_sufficient", "noul", "hist_state_sufficient", ("true", "false")),
    ("not_an_arm", "noul", "hist_not_an_arm", ("true", "false")),
    ("occupancy_not_keep", "noul", "hist_occupancy_not_keep", ("true", "false")),
    ("persist_weight", "score", "hist_persist_weight", None),
    ("n_apply", "score", "hist_n_apply", None),
    ("n_kill", "score", "hist_n_kill", None),
    ("n_pairs", "score", "hist_n_pairs", None),
    ("min_n", "score", "hist_min_n", None),
    ("year_n", "score", "hist_year_n", None),
    ("min_pos_years", "score", "hist_min_pos_years", None),
    ("threshold", "score", "hist_threshold", None),
    ("loop_bound", "score", "hist_loop_bound", None),
    ("parameter", "score", "hist_parameter", None),
)

_CHOICE_TEXT: dict[str, dict[str, str]] = {
    "hist_verdict": {
        "APPLY_CANDIDATE": "The symbol and sleeve earn a historical apply-candidate label.",
        "KILL": "The symbol and sleeve do not earn a historical apply-candidate label.",
    },
    "hist_identity": {
        "challenge": "The login and namespace are the challenge book.",
        "verification_quarantined": "The login is the quarantined verification book.",
        "study_not_challenge": "The study login is outside the challenge book.",
        "w7_other_organism": "The tags or namespace are the other organism.",
        "namespace_not_challenge": "The namespace is outside the challenge book.",
        "login_not_challenge": "The login is outside the challenge book.",
        "identity_missing": "Login and namespace are both absent.",
    },
    "hist_component": {
        "apply_keep": "The measured keep-name menu contains this symbol and sleeve.",
        "us30": "The symbol stem is US30.",
        "named_fx_mid_dn": "The symbol is a named FX pair on sub_mid_dn_revert.",
        "crypto_ny": "The symbol is BTC on a crypto sleeve.",
        "notable_kill": "The measured notable-kill rows contain this symbol and sleeve.",
        "other": "No named measured component contains this symbol and sleeve.",
    },
}
_NOUL_TEXT: dict[str, tuple[str, str]] = {
    "hist_identity_ok": (
        "The login and namespace on this state are the challenge book.",
        "The login and namespace on this state are outside the challenge book.",
    ),
    "hist_apply": (
        "This state carries an apply mark.",
        "This state carries no apply mark.",
    ),
    "hist_silent_apply": (
        "This state carries a silent apply mark.",
        "This state carries no silent apply mark.",
    ),
    "hist_writer_tag": (
        "This state carries a writer tag.",
        "This state carries no writer tag.",
    ),
    "hist_extra_pass": (
        "This state carries an extra pass.",
        "This state carries no extra pass.",
    ),
    "hist_flatten": (
        "This state carries a flatten mark.",
        "This state carries no flatten mark.",
    ),
    "hist_size_up": (
        "This state carries a size-up mark.",
        "This state carries no size-up mark.",
    ),
    "hist_pin_ok": (
        "The recorded pin facts on this state are acceptable.",
        "The recorded pin facts on this state are not acceptable.",
    ),
    "hist_fail_closed": (
        "This state is fail-closed.",
        "This state is not fail-closed.",
    ),
    "hist_on_surface": (
        "This symbol and sleeve are on the measured surface.",
        "This symbol and sleeve are off the measured surface.",
    ),
    "hist_ci_includes_zero": (
        "The measured interval on this state includes zero.",
        "The measured interval on this state excludes zero.",
    ),
    "hist_headline": (
        "This symbol and sleeve are a headline measured name.",
        "This symbol and sleeve are not a headline measured name.",
    ),
    "hist_off_surface": (
        "This symbol and sleeve are an off-surface measured name.",
        "This symbol and sleeve are not an off-surface measured name.",
    ),
    "hist_cost_kill": (
        "Cost is a kill on this state.",
        "Cost is not a kill on this state.",
    ),
    "hist_walked": (
        "This symbol and sleeve were on the measured walk.",
        "This symbol and sleeve were absent from the measured walk.",
    ),
    "hist_component_exists": (
        "The named component is present on this state.",
        "The named component is absent on this state.",
    ),
    "hist_overlay_copied": (
        "An overlay copy is present on this state.",
        "An overlay copy is absent on this state.",
    ),
    "hist_state_sufficient": (
        "The named facts are enough to label this state.",
        "The named facts are not enough to label this state.",
    ),
    "hist_not_an_arm": (
        "This label is not an arm.",
        "This label is an arm.",
    ),
    "hist_occupancy_not_keep": (
        "Occupancy is not the keep rule on this state.",
        "Occupancy is the keep rule on this state.",
    ),
}
_SCORE_NOUN = {
    "hist_persist_weight": "persist weight",
    "hist_n_apply": "apply count",
    "hist_n_kill": "kill count",
    "hist_n_pairs": "pair count",
    "hist_min_n": "minimum sample count",
    "hist_year_n": "year count",
    "hist_min_pos_years": "minimum positive-year count",
    "hist_threshold": "threshold",
    "hist_loop_bound": "loop bound",
    "hist_parameter": "parameter",
}


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def hist_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Host gate. Unset, empty, or 0 stays off and does not ask."""

    return _env_on(HIST_APPLY_ENV, environ)


def default_store_path() -> Path:
    override = (os.environ.get(HIST_APPLY_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_STORE


def normalize_symbol(value: Any) -> str:
    raw = str(value or "").strip().upper().replace(".", "_").replace(" ", "")
    if raw.endswith("_CASH"):
        raw = raw[: -len("_CASH")]
    if raw.endswith("_C"):
        raw = raw[: -len("_C")]
    return raw


def normalize_sleeve(value: Any) -> str:
    return str(value or "").strip()


def is_us30(symbol: str) -> bool:
    stem = normalize_symbol(symbol)
    return stem in US30_STEMS or stem.startswith("US30")


def _login_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value).strip()


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


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for bit in _BANNED_TEXT:
        cleaned = cleaned.replace(bit, "")
    return cleaned


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys. They are not a question."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _inert() -> dict[str, Any]:
    """This module has no send path."""

    return {
        "order_send": False,
        "never_place": True,
        "never_flatten": True,
        "never_remint": True,
        "tags_csv": None,
    }


def _pass_target() -> Any:
    try:
        from .challenge import CHALLENGE_PASS_TARGET

        return CHALLENGE_PASS_TARGET
    except Exception:
        return None


def _verification_login() -> Any:
    """Verification book id. A fact on the ask. Import failure keeps the known id."""

    try:
        from .challenge import VERIFICATION_QUARANTINED

        if VERIFICATION_QUARANTINED not in (None, ""):
            return VERIFICATION_QUARANTINED
    except Exception:
        pass
    return "0"


def _safe_surface() -> Any:
    try:
        from .challenge import account_surface

        return account_surface()
    except Exception:
        return None


def load_json(path: Path | str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    if not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_keep_set(path: Path | str | None = None) -> dict[str, Any]:
    payload = load_json(path or DEFAULT_KEEP_SET)
    if payload is None:
        return {"schema": SCHEMA, "apply_candidate": []}
    return payload


def _keep_index(keep_set: MappingLike | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    payload = dict(keep_set) if keep_set is not None else load_keep_set()
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in payload.get("apply_candidate") or []:
        if not isinstance(row, dict):
            continue
        key = (normalize_symbol(row.get("symbol")), normalize_sleeve(row.get("sleeve")))
        out[key] = dict(row)
    return out


def _row_match(rows: Any, symbol: str, sleeve: str | None) -> dict[str, Any] | None:
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if normalize_symbol(row.get("symbol")) != symbol:
            continue
        if sleeve is not None and normalize_sleeve(row.get("sleeve")) != sleeve:
            continue
        return dict(row)
    return None


def _measured(symbol: Any, sleeve: Any, keep_set: MappingLike | None) -> dict[str, Any]:
    """Fixture rows for this name. The rows are facts."""

    sy = normalize_symbol(symbol)
    sl = normalize_sleeve(sleeve)
    payload = dict(keep_set) if keep_set is not None else load_keep_set()
    key = (sy, sl)
    keep_row = _keep_index(payload).get(key)
    notable = _row_match(payload.get("notable_kill"), sy, sl)
    named = None
    if sl == MID_DN_SLEEVE and sy in NAMED_FX_MID_DN:
        named = _row_match(payload.get("named_fx_sub_mid_dn_revert"), sy, None)
    crypto = None
    if sy == BTC_SYMBOL and sl in {CRYPTO_NY_SLEEVE, CRYPTO_H4_SLEEVE}:
        crypto = _row_match(payload.get("crypto_ny_btc"), sy, sl)
    return {
        "symbol": sy,
        "sleeve": sl,
        "symbol_is_us30": is_us30(sy),
        "named_fx_mid_dn": bool(sl == MID_DN_SLEEVE and sy in NAMED_FX_MID_DN),
        "crypto_ny_name": bool(sy == BTC_SYMBOL and sl in {CRYPTO_NY_SLEEVE, CRYPTO_H4_SLEEVE}),
        "measured_keep_name": key in APPLY_KEEP,
        "keep_row": keep_row,
        "notable_row": notable,
        "named_fx_row": named,
        "crypto_row": crypto,
        "recorded_n_apply": payload.get("n_apply"),
        "recorded_n_kill": payload.get("n_kill"),
        "recorded_n_pairs": payload.get("n_pairs"),
    }


def _primary_row(measured: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("keep_row", "named_fx_row", "crypto_row", "notable_row"):
        row = measured.get(key)
        if isinstance(row, dict) and row:
            return row
    return {}


def _measured_reasons(measured: Mapping[str, Any]) -> list[Any] | None:
    for key in ("keep_row", "named_fx_row", "crypto_row", "notable_row"):
        row = measured.get(key)
        if isinstance(row, dict) and row.get("kill_reasons"):
            return list(row.get("kill_reasons") or [])
    return None


def _pin_facts() -> dict[str, Any]:
    """Recorded pin attributes. They are facts, and the pin mark is the return."""

    try:
        from .gold_priors import GATE_COMPOSITE_WEIGHTS, PIN_WINDOW
    except Exception as exc:
        return {
            "recorded_pin_window": None,
            "recorded_pin_persist": None,
            "pin_source": type(exc).__name__,
        }
    persist = None
    if isinstance(GATE_COMPOSITE_WEIGHTS, Mapping):
        persist = _finite(GATE_COMPOSITE_WEIGHTS.get("persistence"))
    window = PIN_WINDOW if isinstance(PIN_WINDOW, str) else None
    return {
        "recorded_pin_window": window,
        "recorded_pin_persist": persist,
        "pin_source": "gold_priors",
    }


def _identity_facts(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    heartbeat: MappingLike | None = None,
    study: MappingLike | None = None,
) -> dict[str, Any]:
    hb = dict(heartbeat or {})
    study_doc = dict(study or {})
    ns = str(namespace or hb.get("namespace") or "").strip()
    raw_login = _login_text(login)
    if not raw_login:
        raw_login = _login_text(
            study_doc.get("login")
            or study_doc.get("account")
            or hb.get("login")
            or hb.get("account")
        )
    tag_set = {str(item).strip() for item in (tags or hb.get("tags") or []) if str(item).strip()}
    study_login = _login_text(study_doc.get("login") or study_doc.get("account"))
    return {
        "login": raw_login,
        "namespace": ns,
        "tags": sorted(tag_set),
        "study_login": study_login,
        "book_login": CHALLENGE_LOGIN,
        "book_namespace": CHALLENGE_NS,
        "book_magic": CHALLENGE_MAGIC,
        "verification_login": _verification_login(),
        "w7_tags": sorted(W7_ARMED_TAGS),
    }


def _choice_instructions(qid: str) -> str:
    if qid == "hist_verdict":
        noun = "historical label for the symbol and sleeve"
    elif qid == "hist_identity":
        noun = "identity label for the login, namespace, and tags"
    else:
        noun = "measured component for the symbol and sleeve"
    return _scrub_text(
        f"Which {noun} is this state? "
        "The option with the single highest probability is that label. "
        "An empty answer or a tie leaves it unset. "
        "A floor and a baseline are not a question. "
        "This question does not send."
    )


def _noul_instructions(qid: str) -> str:
    yes, _no = _NOUL_TEXT.get(qid, ("Yes, for this state.", "No, for this state."))
    return _scrub_text(
        f"{yes} "
        "The noul you return is that answer for this state. "
        "An empty noul leaves it unset. "
        "A floor and a baseline are not a question. "
        "This question does not send."
    )


def _score_instructions(qid: str) -> str:
    noun = _SCORE_NOUN.get(qid, "parameter")
    return _scrub_text(
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "A floor and a baseline are not a question. "
        "This question does not send."
    )


def _questions() -> dict[str, Any]:
    """One pack. Every entry is a Noul, a Choice, or a Score."""

    pack: dict[str, Any] = {}
    for _field, kind, qid, order in _SPEC:
        if _limit_key(qid):
            continue
        if kind == "choice":
            criteria = {
                str(key): _scrub_text(text)
                for key, text in _CHOICE_TEXT.get(qid, {}).items()
                if not _limit_key(str(key))
            }
            if order:
                criteria = {name: criteria.get(name, name) for name in order}
            pack[qid] = {
                "type": "choice",
                "instructions": _choice_instructions(qid),
                "criteria": criteria,
            }
        elif kind == "noul":
            yes, no = _NOUL_TEXT.get(qid, ("Yes, for this state.", "No, for this state."))
            pack[qid] = {
                "type": "noul",
                "instructions": _noul_instructions(qid),
                "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
            }
        else:
            pack[qid] = {
                "type": "score",
                "instructions": _score_instructions(qid),
                "criteria": [item for item in _LEVELS if not _limit_key(item)],
            }
    return pack


def _numeric_probs(raw: Mapping[str, Any], order: tuple[str, ...] | None) -> dict[str, float]:
    names = tuple(str(name) for name in order) if order else tuple(str(name) for name in raw)
    out: dict[str, float] = {}
    for name in names:
        if name not in raw:
            continue
        number = _finite(raw.get(name))
        if number is None:
            continue
        out[name] = number
    return out


def _local_unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is unset."""

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
        number = _finite(probabilities.get(name))
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p:
            best = name
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...] | None) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        raw = block.get("distribution") if isinstance(block.get("distribution"), Mapping) else None
    if not isinstance(raw, Mapping):
        return None
    numeric = _numeric_probs(raw, order)
    if not numeric:
        return None
    local = _local_unique(numeric, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(numeric, order)
    except Exception:
        picked = local
    if picked is None or local is None or str(picked) != local:
        return None
    if order and str(picked) not in order:
        return None
    return str(picked)


def _noul_of(block: Any) -> bool | float | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice_of(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score_of(block: Any) -> float | None:
    """The returned score. A miss stays missing and is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number
    except Exception:
        returned_number = None
    if returned_number is not None:
        return _finite(returned_number(block))
    if block.get("score") is not None:
        return _finite(block.get("score"))
    if block.get("value") is not None:
        return _finite(block.get("value"))
    raw_noul = block.get("noul")
    if "noul" in block and not isinstance(raw_noul, bool):
        return _finite(raw_noul)
    picked = _choice_of(block, None)
    raw = block.get("probabilities")
    if picked is None or not isinstance(raw, Mapping):
        return None
    return _finite(raw.get(picked))


def _pull(block: Any, kind: str, order: tuple[str, ...] | None) -> Any:
    if kind == "choice":
        return _choice_of(block, order)
    if kind == "noul":
        return _noul_of(block)
    return _score_of(block)


def _tied(block: Any, order: tuple[str, ...] | None) -> bool:
    if not isinstance(block, Mapping):
        return False
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return False
    numeric = _numeric_probs(raw, order)
    if len(numeric) < 2:
        return False
    best = max(numeric.values())
    winners = [name for name, number in numeric.items() if number == best]
    return len(winners) != 1


def _why(block: Any, value: Any, order: tuple[str, ...] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    if _tied(block, order):
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _prob(block: Any, name: str | None) -> float | None:
    if not name or not isinstance(block, Mapping):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or name not in raw:
        return None
    return _finite(raw.get(name))


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], qid: str, value: Any, error: str | None) -> None:
    """The return is history for the next ask. A miss stays a miss."""

    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, state, error=error)
    except Exception:
        _LOCAL_OUTCOMES.append({"spot": qid, "value": value, "error": error})


def _post(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. A failed import leaves the answers empty."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    for key in (
        "verdict",
        "choice",
        "persist_weight",
        "apply",
        "silent_apply",
        "writer_tag",
        "extra_pass",
        "flatten",
        "size_up",
        "n_apply",
        "n_kill",
        "n_pairs",
        "fail_closed",
        "pin_ok",
        "identity_ok",
        "prior_outcomes",
    ):
        payload.pop(key, None)
    payload["model"] = MODEL
    payload["api_url"] = API_URL
    _attach_priors(payload, questions)
    try:
        from .jev_client import evaluate
    except Exception as exc:
        return {
            "answers": {},
            "error": type(exc).__name__,
            "http_status": None,
            "model": MODEL,
            "state": payload,
        }
    try:
        receipt = evaluate(payload, questions=dict(questions), merge_sleeve=False, model=MODEL)
    except Exception as exc:
        return {
            "answers": {},
            "error": type(exc).__name__,
            "http_status": None,
            "model": MODEL,
            "state": payload,
        }
    if not isinstance(receipt, dict):
        return {
            "answers": {},
            "error": "evaluate_not_a_dict",
            "http_status": None,
            "model": MODEL,
            "state": payload,
        }
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        error = receipt.get("error") or receipt.get("skipped") or "empty"
    return {
        "answers": answers,
        "error": None if error in (None, "") else str(error),
        "http_status": receipt.get("http_status"),
        "model": receipt.get("model") or MODEL,
        "state": payload,
    }


def _decide(state: Mapping[str, Any]) -> dict[str, Any]:
    """One ask. Each field is that return, or unset."""

    questions = _questions()
    posted = _post(state, questions)
    answers = posted.get("answers") if isinstance(posted.get("answers"), dict) else {}
    error = posted.get("error")
    fields: dict[str, Any] = {}
    blocks: dict[str, Any] = {}
    for field, kind, qid, order in _SPEC:
        block = answers.get(qid)
        blocks[qid] = block
        fields[field] = _pull(block, kind, order)
    verdict_block = blocks.get("hist_verdict")
    for field, _kind, qid, order in _SPEC:
        value = fields[field]
        _remember(posted.get("state") or {}, qid, value, _why(blocks.get(qid), value, order, error))
    verdict_why = _why(verdict_block, fields.get("verdict"), _VERDICT_ORDER, error)
    return {
        "fields": fields,
        "probability": _prob(verdict_block, fields.get("verdict")),
        "probabilities": _numeric_probs(
            verdict_block.get("probabilities") if isinstance(verdict_block, Mapping) else {},
            _VERDICT_ORDER,
        ),
        "error": verdict_why,
        "http_status": posted.get("http_status"),
        "model": posted.get("model") or MODEL,
        "asked": True,
    }


def _blank_fields() -> dict[str, Any]:
    return {field: None for field, _kind, _qid, _order in _SPEC}


def persist_pin_ok() -> tuple[bool | float | None, str | None, dict[str, Any]]:
    """Pin mark for this state. The noul and the persist weight are that return."""

    facts = _pin_facts()
    decided = _decide({"rung": "hist_apply", "pin": facts, **facts})
    fields = decided.get("fields") or {}
    meta = {
        **facts,
        "persist_weight": fields.get("persist_weight"),
        "pin_ok": fields.get("pin_ok"),
        "model": decided.get("model"),
        "asked": True,
    }
    return fields.get("pin_ok"), None, meta


def identity_ok(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    heartbeat: MappingLike | None = None,
    study: MappingLike | None = None,
) -> tuple[bool | float | None, str | None]:
    """Identity for this state. The noul and the identity choice are that return."""

    facts = _identity_facts(
        login=login,
        namespace=namespace,
        tags=tags,
        heartbeat=heartbeat,
        study=study,
    )
    decided = _decide({"rung": "hist_apply", "identity_facts": facts, **facts})
    fields = decided.get("fields") or {}
    label = fields.get("identity")
    return fields.get("identity_ok"), label if isinstance(label, str) else None


def lookup(
    symbol: Any,
    sleeve: Any,
    *,
    keep_set: MappingLike | None = None,
) -> dict[str, Any]:
    """Label for one symbol and sleeve. Measured rows stay facts."""

    measured = _measured(symbol, sleeve, keep_set)
    primary = _primary_row(measured)
    state = {
        "rung": "hist_apply",
        "book_login": CHALLENGE_LOGIN,
        "book_namespace": CHALLENGE_NS,
        "measured_keep_pairs": [list(key) for key in APPLY_KEEP_KEYS],
        **measured,
        **_pin_facts(),
    }
    decided = _decide(state)
    fields = decided.get("fields") or _blank_fields()
    return {
        "schema": SCHEMA,
        "symbol": measured["symbol"],
        "sleeve": measured["sleeve"],
        "measured": measured,
        "n": primary.get("n"),
        "mean_R": primary.get("mean_R"),
        "mean_R_ci95": primary.get("mean_R_ci95"),
        "pos_years": primary.get("pos_years"),
        "packs": primary.get("packs"),
        "years": primary.get("years"),
        "kill_reasons": _measured_reasons(measured),
        "recorded_on_surface": primary.get("on_surface"),
        "probability": decided.get("probability"),
        "probabilities": decided.get("probabilities") or {},
        "asked": True,
        "model": decided.get("model"),
        "hop_error": decided.get("error"),
        "http_status": decided.get("http_status"),
        **fields,
        **_inert(),
    }


def label_candidates(
    candidates: Iterable[MappingLike],
    *,
    keep_set: MappingLike | None = None,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    for raw in candidates:
        if not isinstance(raw, dict):
            continue
        hit = lookup(raw.get("symbol"), raw.get("sleeve"), keep_set=keep_set)
        recs.append(
            {
                "sleeve": hit["sleeve"],
                "symbol": hit["symbol"],
                "candidate_id": raw.get("candidate_id"),
                "verdict": hit.get("verdict"),
                "kill_reasons": hit.get("kill_reasons"),
                "n": hit.get("n"),
                "mean_R": hit.get("mean_R"),
                "on_surface": hit.get("on_surface"),
                "ci_includes_zero": hit.get("ci_includes_zero"),
                "headline": hit.get("headline"),
                "apply": hit.get("apply"),
                "silent_apply": hit.get("silent_apply"),
                "writer_tag": hit.get("writer_tag"),
                "flatten": hit.get("flatten"),
                "size_up": hit.get("size_up"),
                "persist_weight": hit.get("persist_weight"),
                "probability": hit.get("probability"),
                **_inert(),
            }
        )

    def _rank(row: Mapping[str, Any]) -> tuple[int, str, str]:
        verdict = row.get("verdict")
        if verdict == "APPLY_CANDIDATE":
            rank = 0
        elif verdict == "KILL":
            rank = 1
        else:
            rank = 2
        return (rank, str(row.get("sleeve") or ""), str(row.get("symbol") or ""))

    recs.sort(key=_rank)
    return recs


def _hist_rows(candidates, candidates_path):
    if candidates is not None:
        return [row for row in candidates if isinstance(row, dict)], "given"
    if candidates_path is not None:
        body = load_json(candidates_path)
        raw = body.get("candidates") if isinstance(body, dict) else None
        if isinstance(raw, list):
            return [row for row in raw if isinstance(row, dict)], "path"
    pointer = namespace_root(REPO_ROOT, CHALLENGE_NS) / "judgment" / "state" / "latest_slate.json"
    body = read_json(pointer)
    dest = None
    if isinstance(body, dict):
        dest = body.get("path") or body.get("slate_path")
    slate = read_json(dest) if dest else body
    raw = slate.get("candidates") if isinstance(slate, dict) else None
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)], "latest_slate"
    return [], "none"


def _pair_facts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        root = namespace_root(REPO_ROOT, CHALLENGE_NS)
        pair = open_pair(root)
    except Exception:
        pair = {"pair_present": False}
    if not isinstance(pair, dict):
        pair = {"pair_present": False}
    if not pair.get("pair_present") and rows:
        first = rows[0]
        pair = {
            "pair_present": True,
            "symbol": first.get("symbol"),
            "sleeve": first.get("sleeve"),
            "ticket": first.get("ticket"),
            "status": "slate_row",
        }
    return pair


def _decision_text(verdict: str | None) -> str | None:
    if verdict not in _VERDICT_ORDER:
        return None
    return (
        "The historical label is the returned choice. "
        "This module does not place, flatten, or send."
    )


def _receipt(
    *,
    enabled: bool,
    skipped: str | None,
    asked: bool,
    fields: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "account": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "pass_target": _pass_target(),
        "surface": _safe_surface() if asked else None,
        "enabled": enabled,
        "skipped": skipped,
        "asked": asked,
        "model": MODEL,
        "api_url": API_URL,
        "question_id": "hist_verdict",
        "do_not_flatten_tickets": sorted(LEAVE_ORIG_TICKETS),
        **_blank_fields(),
        **dict(fields),
        **_inert(),
    }
    if extra:
        row.update(dict(extra))
    return row


def run_hist_apply(
    *,
    candidates: Iterable[MappingLike] | None = None,
    candidates_path: Path | str | None = None,
    login: Any = None,
    namespace: Any = None,
    heartbeat_path: Path | str | None = None,
    study_path: Path | str | None = None,
    keep_set_path: Path | str | None = None,
    as_of: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """One ask for this slate. The choice and the parameters are that return."""

    del environ
    heartbeat = load_json(heartbeat_path) if heartbeat_path is not None else None
    study = load_json(study_path) if study_path is not None else None
    rows, row_kind = _hist_rows(candidates, candidates_path)
    pair = _pair_facts(rows)
    keep = load_keep_set(keep_set_path)
    identity = _identity_facts(
        login=login,
        namespace=namespace if namespace is not None else (heartbeat or {}).get("namespace"),
        heartbeat=heartbeat,
        study=study,
    )
    pin = _pin_facts()
    measured = _measured(pair.get("symbol"), pair.get("sleeve"), keep)
    state = {
        "rung": "hist_apply",
        "identity_facts": identity,
        "pin": pin,
        "pair": pair,
        "row_kind": row_kind,
        "n_rows": len(rows),
        "rows": [
            {
                "symbol": row.get("symbol"),
                "sleeve": row.get("sleeve"),
                "candidate_id": row.get("candidate_id"),
                "ticket": row.get("ticket"),
            }
            for row in rows
        ],
        "measured_keep_pairs": [list(key) for key in APPLY_KEEP_KEYS],
        "as_of": as_of,
        **identity,
        **pin,
        **measured,
    }
    decided = _decide(state)
    fields = decided.get("fields") or _blank_fields()
    verdict = fields.get("verdict")
    emitted = verdict in _VERDICT_ORDER
    recs: list[dict[str, Any]] = []
    if emitted:
        recs.append(
            {
                "sleeve": pair.get("sleeve"),
                "symbol": pair.get("symbol"),
                "ticket": pair.get("ticket"),
                "verdict": verdict,
                "probability": decided.get("probability"),
                "apply": fields.get("apply"),
                "silent_apply": fields.get("silent_apply"),
                "writer_tag": fields.get("writer_tag"),
                "flatten": fields.get("flatten"),
                "size_up": fields.get("size_up"),
                "persist_weight": fields.get("persist_weight"),
                **_inert(),
            }
        )
        try:
            root = namespace_root(REPO_ROOT, CHALLENGE_NS)
            append_record(
                root / "judgment" / "rung_choice" / "hist_apply.jsonl",
                {
                    "decision_emitted": True,
                    "rung": "hist_apply",
                    "login": CHALLENGE_LOGIN,
                    "namespace": CHALLENGE_NS,
                    "symbol": pair.get("symbol"),
                    "sleeve": pair.get("sleeve"),
                    "question_id": "hist_verdict",
                    "choice": verdict,
                    "probability": decided.get("probability"),
                    "model": decided.get("model"),
                    **{key: fields.get(key) for key, _kind, _qid, _order in _SPEC},
                    **_inert(),
                },
            )
        except Exception:
            pass
    return _receipt(
        enabled=True,
        skipped=None,
        asked=True,
        fields=fields,
        extra={
            "choice": verdict if emitted else None,
            "probability": decided.get("probability") if emitted else None,
            "probabilities": decided.get("probabilities") or {},
            "decision_emitted": emitted,
            "recommendation_emitted": emitted,
            "recommendations": recs,
            "n_recommendations": len(recs),
            "identity": fields.get("identity"),
            "gold_pin": None,
            "row_kind": row_kind,
            "symbol": pair.get("symbol"),
            "sleeve": pair.get("sleeve"),
            "ticket": pair.get("ticket"),
            "n_rows": len(rows),
            "as_of": as_of,
            "recorded_pin_window": pin.get("recorded_pin_window"),
            "recorded_pin_persist": pin.get("recorded_pin_persist"),
            "hop_error": decided.get("error"),
            "http_status": decided.get("http_status"),
            "model": decided.get("model") or MODEL,
            "decision": _decision_text(verdict if isinstance(verdict, str) else None),
        },
    )


def maybe_label(
    *,
    candidates: Iterable[MappingLike] | None = None,
    candidates_path: Path | str | None = None,
    login: Any = None,
    namespace: Any = None,
    heartbeat_path: Path | str | None = None,
    study_path: Path | str | None = None,
    keep_set_path: Path | str | None = None,
    as_of: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Host-safe observer. Default off. The enabled path asks once."""

    if not hist_apply_enabled(environ=environ):
        return _receipt(
            enabled=False,
            skipped="GTOS_JEV_HIST_APPLY_off",
            asked=False,
            fields={},
            extra={
                "choice": None,
                "probability": None,
                "probabilities": {},
                "decision_emitted": False,
                "recommendation_emitted": False,
                "recommendations": [],
                "n_recommendations": 0,
                "hop_error": None,
                "http_status": None,
                "decision": None,
            },
        )
    return run_hist_apply(
        candidates=candidates,
        candidates_path=candidates_path,
        login=login,
        namespace=namespace,
        heartbeat_path=heartbeat_path,
        study_path=study_path,
        keep_set_path=keep_set_path,
        as_of=as_of,
        environ=environ,
    )

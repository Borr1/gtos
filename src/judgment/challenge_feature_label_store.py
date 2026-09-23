"""Challenge-history feature and label slice.

Every decision on a state, including each parameter, is the System One
return for that state. The call is ``jev_client.evaluate`` with model
``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only a Noul, a Choice, or a Score.
Prior outcomes are attached on the ask, and the return is stored for the
next ask.

An empty answer, a tie, or an error leaves that field unset. A floor and
a baseline are not a question. This module does not send and does not flatten.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CHALLENGE_LOGIN = "0"
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = "0"
VERIFICATION_LOGIN = "0"
MODEL = "jev-1.13.0"

FEATURE_SCHEMA = "gtos.judgment.challenge_history_features.v0"
LABEL_SCHEMA = "gtos.judgment.challenge_history_labels.v0"
SLICE_SCHEMA = "gtos.judgment.challenge_history_slice.v0"
STORE_ENV = "GTOS_JEV_FEATURE_LABEL_STORE"
STORE_PATH_ENV = "GTOS_JEV_FEATURE_LABEL_STORE_PATH"
FEATURE_STORE_EXCLUSION = "banned_from_asof_open_features_labels_only"

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "judgment"
    / "astra"
    / "lab"
    / "challenge_feature_label_store"
    / "fixtures"
)
DEFAULT_STORE = (
    REPO_ROOT
    / "judgment"
    / "astra"
    / "lab"
    / "challenge_feature_label_store"
    / "store.jsonl"
)

STORE_GOLD = Path("/cursor/stores/bc-63b92356-64bd-4046-81a3-99a1f7a637d2/internal/gold")
STORE_REPLAY = Path(
    "/cursor/stores/bc-63b92356-64bd-4046-81a3-99a1f7a637d2"
    "/context/chair_bridge/JEV_REPLAY_PACK/challenge_replay_rows.jsonl"
)
WORKSPACE_EXPORTS = Path("/workspace/exports/multi_instrument")

_SESSION_ORDER = (
    "asia",
    "asia_london",
    "london",
    "london_ny",
    "ny",
    "late_ny",
    "dead_21_00z",
    "friday_cutoff",
    "weekend",
    "unknown",
)
_OCCUPANCY_ORDER = ("with_session", "out_of_session", "in_session")
_FAMILY_ORDER = (
    "house_keep",
    "house_hard_off",
    "starve_watch",
    "a_plus_study",
    "other_tagged",
)
_SIDE_ORDER = ("long", "short", "other")
_GRAIN_ORDER = ("named_session", "occupancy", "vol_bucket", "house_cell")
_DEPTH_ORDER = ("hide", "short", "long", "full")
_ORDER_TYPE_ORDER = ("MARKET", "PENDING", "OTHER")
_NEWS_SOURCE_ORDER = ("unassembled", "assembled", "other")
_CLOCK_ORDER = ("new_york_plus_7", "other")
_SOURCE_ORDER = ("metals_a8_server_local", "unassembled", "other")
_REASON_ORDER = (
    "clear",
    "verification_quarantined",
    "other_login",
    "other_namespace",
    "w7_other_organism",
    "overlay_77_y2025",
    "persist_withheld",
)
_PIN_ORDER = (
    "G-FULL",
    "Y2025",
    "G-LAB",
    "G-2M",
    "2022",
    "2023",
    "2024_lab_apr_dec",
    "2025",
    "2026",
)

WITH_SESSION = frozenset({"asia", "asia_london", "london", "london_ny", "ny"})
OUT_SESSION = frozenset({"late_ny", "dead_21_00z", "friday_cutoff", "weekend"})
NAMED_SESSIONS = frozenset(_SESSION_ORDER)
OCCUPANCY_KEYS = frozenset(_OCCUPANCY_ORDER)
VOL_KEYS = frozenset({"lo", "mid", "hi", "xhi"})
SKIP_PATH_TOKENS = frozenset(
    {
        "utc_sensitivity",
        "year_2025_utc_sensitivity",
        "G-2W",
        "G-10M",
        "G-MATCH_second_pass",
        "sidecar",
        "sidecar_2026",
        "sidecar_2025",
        "sidecar_2025_tail",
        "hist_2026",
        "lab_2025",
        "gfull_same_file",
        "months_2025_broker",
        "months",
        "flow",
        "persist",
        "level",
        "cliff_ac60_long",
        "occupancy_x_flow",
        "named_x_flow",
        "tree_side_x_session_x_flow",
        "persist_x_session_group",
        "vol_x_session_group",
        "vol_x_session_long_p_target",
        "session_given_metals_vr_ge_1p2",
        "wave6_h4_hours_on_m15_grid",
        "2024_early_h2223",
        "compose_session_group_x_flow",
        "compose_named_x_flow",
        "compose_session_group_x_flow_last_closed",
        "flow_last_closed",
        "coverage",
        "coverage_2025",
        "sources",
        "pins",
        "clock_probe",
        "file",
        "labels",
        "hole",
        "not_done",
        "spreads",
        "chi2_session_vs_long_target_uncond",
        "chi2_session_vs_long_target_vr_ge_1p2",
        "chi2_vol_vs_long_target",
        "london_ny_minus_ny_pp_by_vol",
    }
)
SKIP_YEAR_KEYS = frozenset({"2024"})
NAMED_PARENTS = frozenset({"named", "named_session", "session"})
OCC_PARENTS = frozenset({"occupancy", "session_group"})
VOL_PARENTS = frozenset({"vol"})
HOUSE_LAST = frozenset(
    {
        "year_2025_broker",
        "lab_2026",
        "house",
        "floor",
        "G-LAB",
        "G-2M",
        "2024_lab_apr_dec",
    }
)
WINDOW_KEYS = frozenset(_PIN_ORDER) | frozenset(
    {
        "year_2025_broker",
        "lab_2026",
        "G-LAB",
        "G-2M",
        "2022",
        "2023",
        "2025",
        "2026",
        "2024_lab_apr_dec",
    }
)
_WINDOW_ORDER = tuple(name for name in _PIN_ORDER if name in WINDOW_KEYS) + tuple(
    sorted(WINDOW_KEYS - frozenset(_PIN_ORDER))
)
CHALLENGE_REPLAY_REPO = (
    REPO_ROOT
    / "judgment"
    / "astra"
    / "lab"
    / "challenge_replay_20260917"
    / "challenge_replay_rows.jsonl"
)

FEATURE_PATHS = (
    "identity.candidate_id",
    "identity.symbol",
    "identity.side",
    "identity.sleeve",
    "identity.family_class",
    "identity.origin_organism",
    "clock.as_of_utc",
    "clock.rule",
    "clock.weekday",
    "clock.is_friday",
    "sessions.named",
    "sessions.broker_hour",
    "sessions.utc_hour",
    "sessions.source",
    "sessions.occupancy_label",
    "geometry.plan_r",
    "geometry.stop_dist",
    "geometry.target_dist",
    "geometry.stop_atr",
    "geometry.target_atr",
    "geometry.order_type",
    "sleeve_features.ac60",
    "sleeve_features.vol_ratio",
    "sleeve_features.tag",
    "regime.vol_bucket",
    "cost.spread_r",
    "news.spine_empty",
    "news.source",
    "news.high_in_f5_window",
    "surface.us30_off",
    "surface.hard_off_family",
    "completeness.missing_fields",
    "completeness.state_sufficient_for_live",
)

NEVER_FLATTEN_TICKETS = (294092360, 294088097, 294069721)
_FIREHOSE_KEYS = frozenset({"events", "bars", "rows", "ohlc", "close", "high", "low", "open"})
_RATE_TAILS = frozenset({"long", "short", "p_target", "long_p_target", "short_p_target"})

_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
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
_TAIL = (
    " An empty answer, a tie, or an error leaves this unset."
    " A floor and a baseline are not a question."
    " Do not send an order."
)


def store_enabled() -> bool:
    return os.environ.get(STORE_ENV, "").strip().lower() in {"1", "true", "yes"}


def default_store_path() -> Path:
    override = (os.environ.get(STORE_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_STORE


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _f(value: Any) -> float | None:
    if value == "":
        return None
    return _finite(value)


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


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
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _local_unique(probabilities: Mapping[str, Any], order: Sequence[str]) -> str | None:
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
    best = max(numeric.values())
    winners = [name for name in order if name in numeric and abs(numeric[name] - best) <= 1e-12]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: Sequence[str]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
    names = tuple(order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(raw, names)
    except Exception:
        picked = _local_unique(raw, names)
    if picked is None or str(picked) not in names:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block:
        raw = block.get("noul")
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
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
    if block.get("score") is None:
        return None
    return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: Sequence[str] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: Sequence[str] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = tuple(order or ()) or (tuple(str(name) for name in probs) if isinstance(probs, Mapping) else ())
    if isinstance(probs, Mapping) and probs and _local_unique(probs, menu) is None and menu:
        present = [name for name in menu if name in probs and _finite(probs.get(name)) is not None]
        if len(present) >= 2:
            return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _limit_key(key):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _finite(value)
        if number is not None:
            found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _menu(order: Sequence[str], text: str) -> dict[str, str]:
    return {str(name): _scrub_text(text.format(name=name)) for name in order}


def _choice_q(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(str(text).strip() + _TAIL)
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): _scrub_text(str(value)) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, body["criteria"])
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = dict(body["criteria"])
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_q(qid: str, noun: str, levels: Sequence[str]) -> dict[str, Any]:
    instructions = _scrub_text(
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset."
        + _TAIL
    )
    criteria = [str(item) for item in levels] if levels else list(_BETWEEN)
    body: dict[str, Any] = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = list(criteria)
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_q(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    instructions = _scrub_text(str(text).strip() + _TAIL)
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _book(facts: dict[str, Any]) -> dict[str, Any]:
    facts.setdefault("challenge_login", CHALLENGE_LOGIN)
    facts.setdefault("challenge_ns", CHALLENGE_NS)
    facts.setdefault("verification_login", VERIFICATION_LOGIN)
    facts["model"] = MODEL
    facts["do_not_flatten_tickets"] = list(NEVER_FLATTEN_TICKETS)
    return facts


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _book(_scrub(dict(state)))
    payload.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        payload["prior_outcomes"] = prior_outcomes(state=payload, questions=questions)
    except Exception:
        payload["prior_outcomes"] = []
    try:
        from .jev_client import evaluate

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
    }


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _decide(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {"model": asked.get("model") or MODEL}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    _remember(asked.get("state") or {}, rows)
    return out


def _is_true(value: Any) -> bool:
    return value is True


def _width(score: Any) -> int | None:
    number = _finite(score)
    if number is None or number < 0:
        return None
    return int(round(number))


def _path_facts(path: Sequence[str]) -> dict[str, Any]:
    tokens = [str(tok) for tok in path]
    return {
        "json_path": tokens,
        "banned_tokens": sorted({tok for tok in tokens if tok in SKIP_PATH_TOKENS}),
        "sidecar_tokens": sorted({tok for tok in tokens if tok.startswith("sidecar")}),
        "cross_tokens": sorted({tok for tok in tokens if "_x_" in tok}),
        "year_stub": "years" in tokens and any(tok in SKIP_YEAR_KEYS for tok in tokens),
    }


def _measured_ratio(entry: Any, stop: Any, target: Any) -> float | None:
    got_entry, got_stop, got_target = _f(entry), _f(stop), _f(target)
    if got_entry is None or got_stop is None or got_target is None:
        return None
    risk = abs(got_entry - got_stop)
    if risk <= 0:
        return None
    return abs(got_target - got_entry) / risk


def _parse_mt5_time(raw: str | None) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _broker_open_to_utc(naive: datetime) -> datetime | None:
    try:
        from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

        return broker_naive_to_utc(naive, resolve_rule("FTMO-Server"))
    except Exception:
        return None


def _missing(state: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for dotted in FEATURE_PATHS:
        cur: Any = state
        for part in dotted.split("."):
            if not isinstance(cur, Mapping) or part not in cur:
                cur = None
                break
            cur = cur[part]
        if cur is None:
            missing.append(dotted)
    return missing


def named_session(
    broker_hour: int | None,
    utc_hour: int | None,
    utc_weekday: int | None,
) -> str | None:
    """Session Choice for these clock facts. A miss stays unset."""

    facts = {
        "broker_hour": broker_hour,
        "utc_hour": utc_hour,
        "utc_weekday": utc_weekday,
        "session_menu": list(_SESSION_ORDER),
    }
    levels = _levels(facts)
    questions = _choice_q(
        "cfl_named_session",
        "Which named session is this clock? The hours and the weekday are facts.",
        _menu(_SESSION_ORDER, "The named session is {name}."),
    )
    questions.update(_score_q("cfl_named_session_parameter", "named-session parameter", levels))
    decided = _decide(
        facts,
        questions,
        (
            ("named", "choice", "cfl_named_session", _SESSION_ORDER),
            ("parameter", "score", "cfl_named_session_parameter", None),
        ),
    )
    return decided.get("named") if isinstance(decided.get("named"), str) else None


def occupancy_label(named: str | None) -> str | None:
    """Occupancy Choice. Set membership is a fact. A miss stays unset."""

    facts = {
        "named": named,
        "with_session": sorted(WITH_SESSION),
        "out_of_session": sorted(OUT_SESSION),
        "occupancy_menu": list(_OCCUPANCY_ORDER),
    }
    levels = _levels(facts)
    questions = _choice_q(
        "cfl_occupancy",
        "Which occupancy label fits the named session on this state?",
        _menu(_OCCUPANCY_ORDER, "The occupancy label is {name}."),
    )
    questions.update(_score_q("cfl_occupancy_parameter", "occupancy parameter", levels))
    decided = _decide(
        facts,
        questions,
        (
            ("occupancy", "choice", "cfl_occupancy", _OCCUPANCY_ORDER),
            ("parameter", "score", "cfl_occupancy_parameter", None),
        ),
    )
    picked = decided.get("occupancy")
    return picked if isinstance(picked, str) else None


def plan_r(entry: Any, stop: Any, target: Any) -> float | None:
    """Plan-r Score. The measured ratio is a fact on the ask, not the return."""

    measured = _measured_ratio(entry, stop, target)
    facts = {
        "entry": _f(entry),
        "stop": _f(stop),
        "target": _f(target),
        "measured_plan_r": measured,
    }
    questions = _score_q("cfl_plan_r", "plan_r", _levels(facts))
    decided = _decide(facts, questions, (("plan_r", "score", "cfl_plan_r", None),))
    return _finite(decided.get("plan_r"))


def _gate_questions(facts: Mapping[str, Any]) -> tuple[dict[str, Any], tuple]:
    levels = _levels(facts)
    questions: dict[str, Any] = {}
    questions.update(_noul_q(
        "cfl_row_reaches",
        "Does this login, namespace, origin, and pin reach the challenge feature store?",
        "This state reaches the challenge feature store.",
        "This state stays out of the challenge feature store.",
    ))
    questions.update(_choice_q(
        "cfl_fail_reason",
        "Which closure reason fits the login, namespace, origin, and pin on this state?",
        _menu(_REASON_ORDER, "The closure reason is {name}."),
    ))
    questions.update(_noul_q(
        "cfl_persist_ok",
        "Does the persist pin on this state hold?",
        "The persist pin holds.",
        "The persist pin does not hold.",
    ))
    questions.update(_score_q("cfl_persist", "persist parameter", levels))
    questions.update(_choice_q(
        "cfl_pin",
        "Which pin window is this state?",
        _menu(_PIN_ORDER, "The pin window is {name}."),
    ))
    questions.update(_noul_q("cfl_apply", "Does this state apply?", "Apply.", "Do not apply."))
    questions.update(_noul_q(
        "cfl_silent_apply",
        "Does this state silent-apply?",
        "Silent-apply.",
        "Do not silent-apply.",
    ))
    questions.update(_noul_q(
        "cfl_extra_pass",
        "Does this state take an extra pass?",
        "Extra pass.",
        "No extra pass.",
    ))
    questions.update(_noul_q(
        "cfl_never_place",
        "Is place withheld on this state?",
        "Place is withheld.",
        "Place is not withheld.",
    ))
    questions.update(_noul_q(
        "cfl_never_flatten",
        "Is flatten withheld on this state?",
        "Flatten is withheld.",
        "Flatten is not withheld.",
    ))
    questions.update(_noul_q(
        "cfl_never_remint",
        "Is remint withheld on this state?",
        "Remint is withheld.",
        "Remint is not withheld.",
    ))
    questions.update(_noul_q(
        "cfl_news_protocol",
        "Is the news protocol applied on this state?",
        "The news protocol is applied.",
        "The news protocol is not applied.",
    ))
    questions.update(_score_q("cfl_loop_bound", "loop bound", levels))
    spec = (
        ("reaches", "noul", "cfl_row_reaches", None),
        ("reason", "choice", "cfl_fail_reason", _REASON_ORDER),
        ("persist_ok", "noul", "cfl_persist_ok", None),
        ("persist", "score", "cfl_persist", None),
        ("pin", "choice", "cfl_pin", _PIN_ORDER),
        ("apply", "noul", "cfl_apply", None),
        ("silent_apply", "noul", "cfl_silent_apply", None),
        ("extra_pass", "noul", "cfl_extra_pass", None),
        ("never_place", "noul", "cfl_never_place", None),
        ("never_flatten", "noul", "cfl_never_flatten", None),
        ("never_remint", "noul", "cfl_never_remint", None),
        ("news_protocol", "noul", "cfl_news_protocol", None),
        ("loop_bound", "score", "cfl_loop_bound", None),
    )
    return questions, spec


def _gate_ask(
    *,
    login: Any = None,
    ns: Any = None,
    origin: Any = None,
    pin_window: Any = None,
) -> dict[str, Any]:
    facts = {
        "login": None if login in (None, "") else str(login),
        "ns": None if ns in (None, "") else str(ns),
        "origin": None if origin in (None, "") else str(origin),
        "pin_window": None if pin_window in (None, "") else str(pin_window),
    }
    questions, spec = _gate_questions(facts)
    return _decide(facts, questions, spec)


def persist_pin_ok() -> bool | float | None:
    """Persist-pin Noul. A miss stays unset."""

    decided = _gate_ask(login=CHALLENGE_LOGIN, ns=CHALLENGE_NS)
    value = decided.get("persist_ok")
    if value is True or value is False:
        return value
    return _finite(value)


def fail_closed_reason(
    *,
    login: Any = None,
    ns: Any = None,
    origin: Any = None,
    pin_window: Any = None,
) -> str | None:
    """Closure-reason Choice when reach is not true. A miss stays unset."""

    decided = _gate_ask(login=login, ns=ns, origin=origin, pin_window=pin_window)
    if _is_true(decided.get("reaches")):
        return None
    reason = decided.get("reason")
    if reason in (None, "clear"):
        return None
    return str(reason)


def _feature_questions(facts: Mapping[str, Any]) -> tuple[dict[str, Any], tuple]:
    levels = _levels(facts)
    questions: dict[str, Any] = {}
    questions.update(_choice_q(
        "cfl_side",
        "Which side is the side fact on this state?",
        _menu(_SIDE_ORDER, "The side is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_family",
        "Which family class fits the sleeve and symbol on this state?",
        _menu(_FAMILY_ORDER, "The family class is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_named_session",
        "Which named session is this clock? The hours and the weekday are facts.",
        _menu(_SESSION_ORDER, "The named session is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_occupancy",
        "Which occupancy label fits the named session on this state?",
        _menu(_OCCUPANCY_ORDER, "The occupancy label is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_order_type",
        "Which order type fits this state?",
        _menu(_ORDER_TYPE_ORDER, "The order type is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_news_source",
        "Which news source fits this state?",
        _menu(_NEWS_SOURCE_ORDER, "The news source is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_clock_rule",
        "Which clock rule fits this state?",
        _menu(_CLOCK_ORDER, "The clock rule is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_session_source",
        "Which session source fits this state?",
        _menu(_SOURCE_ORDER, "The session source is {name}."),
    ))
    questions.update(_noul_q(
        "cfl_hard_off",
        "Is this sleeve and symbol a hard-off family?",
        "Hard-off.",
        "Not hard-off.",
    ))
    questions.update(_noul_q(
        "cfl_us30_off",
        "Is US30 off on this state?",
        "US30 is off.",
        "US30 is not off.",
    ))
    questions.update(_noul_q(
        "cfl_sufficient",
        "Is this state sufficient for live?",
        "Sufficient for live.",
        "Not sufficient for live.",
    ))
    questions.update(_noul_q(
        "cfl_spine_empty",
        "Is the news spine empty on this state?",
        "The news spine is empty.",
        "The news spine is not empty.",
    ))
    questions.update(_noul_q(
        "cfl_news_protocol",
        "Is the news protocol applied on this state?",
        "The news protocol is applied.",
        "The news protocol is not applied.",
    ))
    questions.update(_noul_q(
        "cfl_high_news",
        "Is a high-impact event inside the window on this state?",
        "A high-impact event is inside the window.",
        "No high-impact event is inside the window.",
    ))
    questions.update(_noul_q(
        "cfl_bar_join",
        "Does this state join a bar?",
        "The state joins a bar.",
        "The state does not join a bar.",
    ))
    for qid, noun in (
        ("cfl_plan_r", "plan_r"),
        ("cfl_stop_dist", "stop distance"),
        ("cfl_target_dist", "target distance"),
        ("cfl_stop_atr", "stop atr"),
        ("cfl_target_atr", "target atr"),
        ("cfl_spread_r", "spread"),
        ("cfl_vol_ratio", "vol ratio"),
        ("cfl_ac60", "ac60"),
    ):
        questions.update(_score_q(qid, noun, levels))
    spec = (
        ("side", "choice", "cfl_side", _SIDE_ORDER),
        ("family", "choice", "cfl_family", _FAMILY_ORDER),
        ("named", "choice", "cfl_named_session", _SESSION_ORDER),
        ("occupancy", "choice", "cfl_occupancy", _OCCUPANCY_ORDER),
        ("order_type", "choice", "cfl_order_type", _ORDER_TYPE_ORDER),
        ("news_source", "choice", "cfl_news_source", _NEWS_SOURCE_ORDER),
        ("clock_rule", "choice", "cfl_clock_rule", _CLOCK_ORDER),
        ("session_source", "choice", "cfl_session_source", _SOURCE_ORDER),
        ("hard_off", "noul", "cfl_hard_off", None),
        ("us30_off", "noul", "cfl_us30_off", None),
        ("sufficient", "noul", "cfl_sufficient", None),
        ("spine_empty", "noul", "cfl_spine_empty", None),
        ("news_protocol", "noul", "cfl_news_protocol", None),
        ("high_news", "noul", "cfl_high_news", None),
        ("bar_join", "noul", "cfl_bar_join", None),
        ("plan_r", "score", "cfl_plan_r", None),
        ("stop_dist", "score", "cfl_stop_dist", None),
        ("target_dist", "score", "cfl_target_dist", None),
        ("stop_atr", "score", "cfl_stop_atr", None),
        ("target_atr", "score", "cfl_target_atr", None),
        ("spread_r", "score", "cfl_spread_r", None),
        ("vol_ratio", "score", "cfl_vol_ratio", None),
        ("ac60", "score", "cfl_ac60", None),
    )
    return questions, spec


def _leak_keys(leaked: Any) -> list[str]:
    if not leaked:
        return []
    if isinstance(leaked, str):
        return [leaked]
    if isinstance(leaked, (list, tuple, set)):
        return [str(item) for item in leaked]
    return [str(leaked)]


def _expost_fact(deal_input: Mapping[str, Any]) -> list[str] | None:
    try:
        from .gold_state import reject_expost
    except Exception:
        return None
    try:
        leaked = reject_expost(deal_input, "live_intent")
    except Exception:
        return None
    if leaked is None:
        return None
    return _leak_keys(leaked)


def feature_row_from_challenge(deal_input: Mapping[str, Any]) -> dict[str, Any]:
    """As-of-open fields. Decision fields are this state's return."""

    ticket = deal_input.get("ticket")
    symbol = str(deal_input.get("symbol") or "")
    raw_side = str(deal_input.get("side") or "")
    sleeve = str(deal_input.get("sleeve") or deal_input.get("tag") or "")
    naive = _parse_mt5_time(str(deal_input.get("open_time") or ""))
    as_of = _broker_open_to_utc(naive) if naive else None
    broker_hour = naive.hour if naive else None
    utc_hour = as_of.hour if as_of else None
    weekday = as_of.weekday() if as_of else None
    entry = deal_input.get("open_price")
    stop = deal_input.get("sl")
    target = deal_input.get("tp")
    leaked = _expost_fact(deal_input)
    facts: dict[str, Any] = {
        "ticket": None if ticket is None else str(ticket),
        "symbol": symbol,
        "raw_side": raw_side,
        "sleeve": sleeve,
        "broker_hour": broker_hour,
        "utc_hour": utc_hour,
        "utc_weekday": weekday,
        "entry": _f(entry),
        "stop": _f(stop),
        "target": _f(target),
        "measured_plan_r": _measured_ratio(entry, stop, target),
        "measured_stop_dist": (
            abs(_f(entry) - _f(stop)) if _f(entry) is not None and _f(stop) is not None else None
        ),
        "measured_target_dist": (
            abs(_f(target) - _f(entry)) if _f(entry) is not None and _f(target) is not None else None
        ),
        "login": None if deal_input.get("login") in (None, "") else str(deal_input.get("login")),
        "ns": None if deal_input.get("ns") in (None, "") else str(deal_input.get("ns")),
        "origin": "f5_challenge",
        "keys": sorted(str(key) for key in deal_input.keys()),
        "expost_keys": leaked,
        "with_session": sorted(WITH_SESSION),
        "out_of_session": sorted(OUT_SESSION),
    }
    questions, spec = _feature_questions(facts)
    questions.update(_noul_q(
        "cfl_row_reaches",
        "Does this deal reach the challenge feature store?",
        "This deal reaches.",
        "This deal stays out.",
    ))
    questions.update(_choice_q(
        "cfl_fail_reason",
        "Which closure reason fits this deal?",
        _menu(_REASON_ORDER, "The closure reason is {name}."),
    ))
    questions.update(_noul_q(
        "cfl_asof_reaches",
        "Do the as-of features reach given the keys on this state?",
        "The as-of features reach.",
        "The as-of features stay off.",
    ))
    spec = spec + (
        ("reaches", "noul", "cfl_row_reaches", None),
        ("reason", "choice", "cfl_fail_reason", _REASON_ORDER),
        ("asof_reaches", "noul", "cfl_asof_reaches", None),
    )
    decided = _decide(facts, questions, spec)
    state: dict[str, Any] = {
        "schema": FEATURE_SCHEMA,
        "as_of_clock": "as_of_open_study",
        "identity": {
            "candidate_id": str(ticket) if ticket is not None else None,
            "symbol": symbol,
            "side": decided.get("side"),
            "sleeve": sleeve,
            "family_class": decided.get("family"),
            "origin_organism": "f5_challenge",
            "login": facts["login"],
            "ns": facts["ns"],
            "magic": None if deal_input.get("magic") in (None, "") else str(deal_input.get("magic")),
        },
        "clock": {
            "as_of_utc": as_of.isoformat() if as_of else None,
            "rule": decided.get("clock_rule"),
            "weekday": weekday,
            "is_friday": weekday == 4 if weekday is not None else None,
        },
        "sessions": {
            "named": decided.get("named"),
            "broker_hour": broker_hour,
            "utc_hour": utc_hour,
            "source": decided.get("session_source"),
            "occupancy_label": decided.get("occupancy"),
        },
        "geometry": {
            "entry": _f(entry),
            "stop": _f(stop),
            "target": _f(target),
            "stop_dist": decided.get("stop_dist"),
            "target_dist": decided.get("target_dist"),
            "plan_r": decided.get("plan_r"),
            "stop_atr": decided.get("stop_atr"),
            "target_atr": decided.get("target_atr"),
            "order_type": decided.get("order_type"),
        },
        "sleeve_features": {
            "ac60": decided.get("ac60"),
            "vol_ratio": decided.get("vol_ratio"),
            "tag": deal_input.get("tag") or sleeve or None,
        },
        "regime": {"vol_bucket": None},
        "cost": {"spread_r": decided.get("spread_r")},
        "news": {
            "spine_empty": decided.get("spine_empty"),
            "source": decided.get("news_source"),
            "high_in_f5_window": decided.get("high_news"),
            "events": deal_input.get("events") if isinstance(deal_input.get("events"), list) else None,
            "NEWS_PROTOCOL_APPLIED": decided.get("news_protocol"),
        },
        "surface": {
            "us30_off": decided.get("us30_off"),
            "hard_off_family": decided.get("hard_off"),
        },
        "completeness": {
            "row_reaches": decided.get("reaches"),
            "fail_reason": decided.get("reason"),
            "asof_reaches": decided.get("asof_reaches"),
            "state_sufficient_for_live": decided.get("sufficient"),
            "bar_join": decided.get("bar_join"),
        },
        "grain": "challenge_ticket",
    }
    state["completeness"]["missing_fields"] = _missing(state)
    return state


def label_row_from_challenge(deal: Mapping[str, Any]) -> dict[str, Any]:
    inp = deal.get("input") if isinstance(deal.get("input"), Mapping) else deal
    close = deal.get("close_label") if isinstance(deal.get("close_label"), Mapping) else {}
    answers = (close.get("answers") or {}) if isinstance(close, Mapping) else {}
    exit_choice = ((answers.get("exit_class") or {}) if isinstance(answers, Mapping) else {}).get("choice")
    admit_then = ((deal.get("admit_then") or {}).get("answers") or {}).get("admit") or {}
    admit_now = ((deal.get("admit_now") or {}).get("answers") or {}).get("admit") or {}
    return {
        "schema": LABEL_SCHEMA,
        "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
        "labels_never_asof_features": True,
        "grain": "challenge_ticket",
        "ticket": inp.get("ticket"),
        "symbol": inp.get("symbol"),
        "exit_class": inp.get("exit_class") or exit_choice,
        "close_reason": inp.get("close_reason"),
        "R": _f(inp.get("R")),
        "broker_net": _f(inp.get("broker_net")),
        "hold_min": _f(inp.get("hold_min")),
        "remint_of": inp.get("remint_of"),
        "admit_then": admit_then.get("choice") if isinstance(admit_then, Mapping) else None,
        "admit_now": admit_now.get("choice") if isinstance(admit_now, Mapping) else None,
        "close_label_exit_class": exit_choice,
        "pre_cut": inp.get("pre_cut"),
    }


def _walk_feature_from(
    *,
    named: str | None,
    occupancy: str | None,
    vol_bucket: str | None,
    window: str | None,
    symbol: str,
    decided: Mapping[str, Any],
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": FEATURE_SCHEMA,
        "as_of_clock": "as_of_open_study",
        "identity": {
            "candidate_id": f"walk:{window}:{occupancy or named or vol_bucket}",
            "symbol": symbol,
            "side": decided.get("side"),
            "sleeve": "unsigned_every_bar",
            "family_class": decided.get("family"),
            "origin_organism": "historical_lab",
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
        },
        "clock": {
            "as_of_utc": None,
            "rule": decided.get("clock_rule"),
            "weekday": None,
            "is_friday": None,
        },
        "sessions": {
            "named": decided.get("named"),
            "broker_hour": None,
            "utc_hour": None,
            "source": decided.get("session_source"),
            "occupancy_label": decided.get("occupancy"),
        },
        "geometry": {
            "plan_r": decided.get("plan_r"),
            "stop_atr": decided.get("stop_atr"),
            "target_atr": decided.get("target_atr"),
            "order_type": decided.get("order_type"),
            "stop_dist": decided.get("stop_dist"),
            "target_dist": decided.get("target_dist"),
        },
        "sleeve_features": {
            "ac60": decided.get("ac60"),
            "vol_ratio": decided.get("vol_ratio"),
            "tag": None,
        },
        "regime": {"vol_bucket": vol_bucket},
        "cost": {"spread_r": decided.get("spread_r")},
        "news": {
            "spine_empty": decided.get("spine_empty"),
            "source": decided.get("news_source"),
            "high_in_f5_window": decided.get("high_news"),
            "events": None,
            "NEWS_PROTOCOL_APPLIED": decided.get("news_protocol"),
        },
        "surface": {
            "us30_off": decided.get("us30_off"),
            "hard_off_family": decided.get("hard_off"),
        },
        "completeness": {
            "state_sufficient_for_live": decided.get("sufficient"),
            "bar_join": decided.get("bar_join"),
        },
        "grain": "unsigned_m15_cell",
        "window": window,
    }
    state["completeness"]["missing_fields"] = _missing(state)
    return state


def _ask_walk_feature(facts: Mapping[str, Any]) -> dict[str, Any]:
    questions, spec = _feature_questions(facts)
    return _decide(facts, questions, spec)


def feature_state_from_walk_cell(
    *,
    named: str | None,
    occupancy: str | None,
    vol_bucket: str | None,
    window: str,
    symbol: str = "XAUUSD",
) -> dict[str, Any]:
    """Walk-cell feature. Geometry parameters are Scores on this state."""

    facts = {
        "named": named,
        "occupancy": occupancy,
        "vol_bucket": vol_bucket,
        "window": window,
        "symbol": symbol,
        "with_session": sorted(WITH_SESSION),
        "out_of_session": sorted(OUT_SESSION),
    }
    decided = _ask_walk_feature(facts)
    return _walk_feature_from(
        named=named,
        occupancy=occupancy,
        vol_bucket=vol_bucket,
        window=window,
        symbol=symbol,
        decided=decided,
    )


def _p_target_block(block: Mapping[str, Any] | None, side: str) -> dict[str, Any] | None:
    if not isinstance(block, Mapping):
        return None
    if side == "long" and isinstance(block.get("long_p_target"), Mapping):
        src = block["long_p_target"]
    elif side == "short" and isinstance(block.get("short_p_target"), Mapping):
        src = block["short_p_target"]
    else:
        nested = block.get(side)
        if isinstance(nested, Mapping) and isinstance(nested.get("p_target"), Mapping):
            src = nested["p_target"]
        elif isinstance(block.get("p_target"), Mapping) and side == "long":
            src = block["p_target"]
        else:
            return None
    try:
        count = int(src.get("n") or 0)
    except (TypeError, ValueError):
        count = 0
    probability = _f(src.get("p"))
    if count <= 0 or probability is None:
        return None
    ev = None
    if isinstance(block.get(side), Mapping):
        ev = _f(block[side].get("ev_r") or block[side].get("mean_R"))
    if ev is None:
        ev = _f(block.get("ev_r") or block.get("mean_R"))
    return {"n": count, "k": src.get("k"), "p": probability, "ci95": src.get("ci95"), "ev_r": ev}


def _cell_n(block: Mapping[str, Any]) -> int:
    count = block.get("n")
    if count is not None:
        try:
            return int(count)
        except (TypeError, ValueError):
            return 0
    long = _p_target_block(block, "long")
    return int(long["n"]) if long else 0


def _cell_questions(facts: Mapping[str, Any]) -> tuple[dict[str, Any], tuple]:
    questions, spec = _feature_questions(facts)
    levels = _levels(facts)
    questions.update(_noul_q(
        "cfl_banned_reaches",
        "Does this path reach on the banned-token fact?",
        "The path reaches on that fact.",
        "The path stays out on that fact.",
    ))
    questions.update(_noul_q(
        "cfl_sidecar_reaches",
        "Does this path reach on the sidecar-token fact?",
        "The path reaches on that fact.",
        "The path stays out on that fact.",
    ))
    questions.update(_noul_q(
        "cfl_cross_reaches",
        "Does this path reach on the cross-token fact?",
        "The path reaches on that fact.",
        "The path stays out on that fact.",
    ))
    questions.update(_noul_q(
        "cfl_year_reaches",
        "Does this path reach on the year-stub fact?",
        "The path reaches on that fact.",
        "The path stays out on that fact.",
    ))
    questions.update(_noul_q(
        "cfl_typed_reaches",
        "Does this path reach as a named session, an occupancy, a vol bucket, or a house cell?",
        "The typed cell reaches.",
        "The path stays out.",
    ))
    questions.update(_noul_q(
        "cfl_rate_reaches",
        "Does this label have a rate on this state?",
        "The label has a rate.",
        "The label stays out.",
    ))
    questions.update(_noul_q(
        "cfl_house_cell",
        "Is this path a house cell?",
        "This path is a house cell.",
        "This path is not a house cell.",
    ))
    questions.update(_choice_q(
        "cfl_grain",
        "Which grain is this cell?",
        _menu(_GRAIN_ORDER, "The grain is {name}."),
    ))
    questions.update(_choice_q(
        "cfl_window",
        "Which window token is this cell?",
        _menu(_WINDOW_ORDER, "The window is {name}."),
    ))
    questions.update(_score_q("cfl_cell_parameter", "cell parameter", levels))
    spec = spec + (
        ("banned_reaches", "noul", "cfl_banned_reaches", None),
        ("sidecar_reaches", "noul", "cfl_sidecar_reaches", None),
        ("cross_reaches", "noul", "cfl_cross_reaches", None),
        ("year_reaches", "noul", "cfl_year_reaches", None),
        ("typed_reaches", "noul", "cfl_typed_reaches", None),
        ("rate_reaches", "noul", "cfl_rate_reaches", None),
        ("house_cell", "noul", "cfl_house_cell", None),
        ("grain", "choice", "cfl_grain", _GRAIN_ORDER),
        ("window", "choice", "cfl_window", _WINDOW_ORDER),
        ("parameter", "score", "cfl_cell_parameter", None),
    )
    return questions, spec


def _cell_reaches(decided: Mapping[str, Any]) -> bool:
    flags = (
        "banned_reaches",
        "sidecar_reaches",
        "cross_reaches",
        "year_reaches",
        "typed_reaches",
        "rate_reaches",
    )
    return all(_is_true(decided.get(name)) for name in flags) and isinstance(decided.get("grain"), str)


def _book_reaches(book: Any) -> bool:
    questions = _noul_q(
        "cfl_book_reaches",
        "Does this walk book reach the challenge feature store?",
        "This book reaches.",
        "This book stays out.",
    )
    decided = _decide(
        {"book": None if book is None else str(book)},
        questions,
        (("reaches", "noul", "cfl_book_reaches", None),),
    )
    return _is_true(decided.get("reaches"))


def _iter_rate_cells(
    obj: Any, path: tuple[str, ...] = ()
) -> Iterable[tuple[tuple[str, ...], Mapping[str, Any]]]:
    if isinstance(obj, list):
        for index, child in enumerate(obj):
            ident = None
            if isinstance(child, Mapping):
                ident = child.get("id") or child.get("symbol")
            yield from _iter_rate_cells(child, path + (str(ident if ident is not None else index),))
        return
    if not isinstance(obj, Mapping):
        return
    long = _p_target_block(obj, "long")
    if long and path:
        yield path, obj
    for key, child in obj.items():
        key_s = str(key)
        if key_s in _FIREHOSE_KEYS:
            continue
        yield from _iter_rate_cells(child, path + (key_s,))


def label_from_walk_cell(
    block: Mapping[str, Any],
    *,
    grain: str | None,
    window: str | None,
    house_cell: bool | float | None = None,
) -> dict[str, Any]:
    long = _p_target_block(block, "long") or {}
    short = _p_target_block(block, "short") or {}
    return {
        "schema": LABEL_SCHEMA,
        "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
        "labels_never_asof_features": True,
        "grain": grain,
        "window": window,
        "n": _cell_n(block),
        "long_p_target": long.get("p"),
        "long_n": long.get("n"),
        "long_k": long.get("k"),
        "long_ev_r": long.get("ev_r"),
        "short_p_target": short.get("p"),
        "short_n": short.get("n"),
        "short_k": short.get("k"),
        "short_ev_r": short.get("ev_r"),
        "house_cell": house_cell,
    }


def extract_walk_cells(
    payload: Mapping[str, Any],
    *,
    source_path: str,
    source_sha256: str | None,
) -> list[dict[str, Any]]:
    """Typed cells whose reach Nouls are true. A miss does not emit the cell."""

    rows: list[dict[str, Any]] = []
    schema = str(payload.get("schema") or "")
    if not _book_reaches(payload.get("book")):
        return rows
    for path, block in _iter_rate_cells(payload):
        if not path or path[-1] in _RATE_TAILS:
            continue
        last = path[-1]
        parent = path[-2] if len(path) >= 2 else ""
        named = last if last in NAMED_SESSIONS and parent in NAMED_PARENTS else None
        occupancy = last if last in OCCUPANCY_KEYS and parent in OCC_PARENTS else None
        vol = last if last in VOL_KEYS and parent in VOL_PARENTS else None
        long = _p_target_block(block, "long")
        try:
            count = int(block.get("n") or 0)
        except (TypeError, ValueError):
            count = 0
        facts = {
            **_path_facts(path),
            "named": named,
            "occupancy": occupancy,
            "vol": vol,
            "house_menu_hit": last in HOUSE_LAST,
            "long_p_target": None if long is None else long.get("p"),
            "n": block.get("n"),
            "empty_rate": long is None and count <= 0,
            "symbol": "XAUUSD",
            "with_session": sorted(WITH_SESSION),
            "out_of_session": sorted(OUT_SESSION),
        }
        questions, spec = _cell_questions(facts)
        decided = _decide(facts, questions, spec)
        if not _cell_reaches(decided):
            continue
        window = decided.get("window") if isinstance(decided.get("window"), str) else None
        feat = _walk_feature_from(
            named=named,
            occupancy=occupancy,
            vol_bucket=vol,
            window=window,
            symbol="XAUUSD",
            decided=decided,
        )
        lab = label_from_walk_cell(
            block,
            grain=decided.get("grain"),
            window=window,
            house_cell=decided.get("house_cell"),
        )
        rows.append(
            {
                "feature": feat,
                "label": lab,
                "source": {
                    "path": source_path,
                    "sha256": source_sha256,
                    "schema": schema,
                    "json_path": ".".join(path),
                },
            }
        )
    return rows


def feature_from_screening(row: Mapping[str, Any]) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "")
    facts = {
        "symbol": symbol,
        "verdict": row.get("verdict"),
        "corr_with_xau": _f(row.get("corr_with_xau")),
        "ob_cont_pct": _f(row.get("ob_cont_pct")),
        "n_obs": row.get("n_obs"),
        "spread_sl_pct": _f(row.get("spread_sl_pct")),
    }
    questions, spec = _feature_questions(facts)
    decided = _decide(facts, questions, spec)
    state: dict[str, Any] = {
        "schema": FEATURE_SCHEMA,
        "as_of_clock": "as_of_open_study",
        "identity": {
            "candidate_id": f"screening:{symbol}",
            "symbol": symbol,
            "side": decided.get("side"),
            "sleeve": None,
            "family_class": decided.get("family"),
            "origin_organism": "historical_lab",
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
        },
        "clock": {"rule": decided.get("clock_rule")},
        "sessions": {
            "named": decided.get("named"),
            "source": decided.get("session_source"),
            "occupancy_label": decided.get("occupancy"),
        },
        "geometry": {
            "plan_r": decided.get("plan_r"),
            "stop_atr": decided.get("stop_atr"),
            "target_atr": decided.get("target_atr"),
        },
        "sleeve_features": {"ac60": decided.get("ac60"), "vol_ratio": decided.get("vol_ratio")},
        "regime": {"vol_bucket": None},
        "affinity": {
            "corr_with_xau": _f(row.get("corr_with_xau")),
            "ob_cont_pct": _f(row.get("ob_cont_pct")),
            "n_obs": row.get("n_obs"),
            "best_kz": row.get("best_kz"),
            "spread_sl_pct": _f(row.get("spread_sl_pct")),
        },
        "news": {
            "spine_empty": decided.get("spine_empty"),
            "source": decided.get("news_source"),
            "events": None,
            "NEWS_PROTOCOL_APPLIED": decided.get("news_protocol"),
        },
        "surface": {
            "us30_off": decided.get("us30_off"),
            "hard_off_family": decided.get("hard_off"),
        },
        "completeness": {
            "state_sufficient_for_live": decided.get("sufficient"),
        },
        "grain": "multi_instrument_screening",
    }
    state["completeness"]["missing_fields"] = _missing(state)
    return state


def label_from_screening(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": LABEL_SCHEMA,
        "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
        "labels_never_asof_features": True,
        "grain": "multi_instrument_screening",
        "symbol": row.get("symbol"),
        "verdict": row.get("verdict"),
        "n_obs": row.get("n_obs"),
        "corr_with_xau": _f(row.get("corr_with_xau")),
        "ob_cont_pct": _f(row.get("ob_cont_pct")),
        "kz_cont_pct": _f(row.get("kz_cont_pct")),
        "fvg_cont_pct": _f(row.get("fvg_cont_pct")),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def load_json(path: Path) -> Any:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def discover_sources(
    *,
    challenge_path: Path | None = None,
    walk_paths: Iterable[Path] | None = None,
    screening_path: Path | None = None,
) -> dict[str, Any]:
    """Prefer live gold and multi-instrument walks when those files are present."""

    challenge = challenge_path or next(
        (
            path
            for path in (
                CHALLENGE_REPLAY_REPO,
                STORE_REPLAY,
                FIXTURE_DIR / "challenge_replay_trim.jsonl",
            )
            if path.is_file()
        ),
        FIXTURE_DIR / "challenge_replay_trim.jsonl",
    )
    live_walks = [
        STORE_GOLD / "walk-m15-last-year.json",
        STORE_GOLD / "walk-m15-this-year.json",
        STORE_GOLD / "walk-m15-four-years.json",
        STORE_GOLD / "walk-m15-2024-receipt.json",
        STORE_GOLD / "vol-regimes.json",
    ]
    fixture_walks = [
        FIXTURE_DIR / "gold_walk_cells.json",
        FIXTURE_DIR / "vol_cells.json",
    ]
    if walk_paths is not None:
        default_walks = list(walk_paths)
    else:
        present_live = [path for path in live_walks if path.is_file()]
        default_walks = present_live if present_live else fixture_walks
    walks = [path for path in default_walks if path.is_file()]
    screening = screening_path or next(
        (
            path
            for path in (
                WORKSPACE_EXPORTS / "screening_results" / "screening_table.json",
                FIXTURE_DIR / "screening_trim.json",
            )
            if path.is_file()
        ),
        FIXTURE_DIR / "screening_trim.json",
    )
    return {"challenge": challenge, "walks": walks, "screening": screening}


def score_payload(feature_state: Mapping[str, Any], *, seat: str = "gate") -> dict[str, Any]:
    """One System One post. Include-depth and the seat scores are that return."""

    dumped = json.dumps(feature_state, default=str)
    facts = {
        "seat": seat,
        "firehose_tokens_present": any(
            token in dumped for token in ('"open":', '"high":', '"low":', '"close":', "ohlc")
        ),
        "feature": _scrub(feature_state),
    }
    levels = _levels(facts)
    questions: dict[str, Any] = {}
    questions.update(_choice_q(
        "include_depth",
        "Which include depth is this feature state?",
        _menu(_DEPTH_ORDER, "The include depth is {name}."),
    ))
    questions.update(_noul_q(
        "state_sufficient",
        "Is this feature state sufficient?",
        "Sufficient.",
        "Not sufficient.",
    ))
    questions.update(_score_q("session_fitness", "session fitness", levels))
    questions.update(_score_q("geometry_parameter", "geometry parameter", levels))
    questions.update(_score_q("persistence", "persistence parameter", levels))
    questions.update(_noul_q(
        "cfl_firehose",
        "Is this feature state a price firehose?",
        "This state is a firehose.",
        "This state is not a firehose.",
    ))
    questions.update(_noul_q(
        "cfl_noul_every_tick",
        "Does this state ask a noul on every tick?",
        "Ask on every tick.",
        "Do not ask on every tick.",
    ))
    questions.update(_noul_q(
        "cfl_ask_together",
        "Do these questions go in one post?",
        "One post.",
        "Not one post.",
    ))
    questions.update(_noul_q(
        "cfl_one_post",
        "Is this seat one post?",
        "One post.",
        "Not one post.",
    ))
    questions.update(_noul_q("cfl_extra_pass", "Does this state take an extra pass?", "Extra pass.", "No extra pass."))
    questions.update(_noul_q("cfl_apply", "Does this state apply?", "Apply.", "Do not apply."))
    questions.update(_noul_q(
        "cfl_silent_apply",
        "Does this state silent-apply?",
        "Silent-apply.",
        "Do not silent-apply.",
    ))
    questions.update(_noul_q(
        "cfl_never_place",
        "Is place withheld on this state?",
        "Place is withheld.",
        "Place is not withheld.",
    ))
    questions.update(_noul_q(
        "cfl_never_flatten",
        "Is flatten withheld on this state?",
        "Flatten is withheld.",
        "Flatten is not withheld.",
    ))
    questions.update(_noul_q(
        "cfl_never_remint",
        "Is remint withheld on this state?",
        "Remint is withheld.",
        "Remint is not withheld.",
    ))
    questions.update(_noul_q(
        "cfl_news_protocol",
        "Is the news protocol applied on this state?",
        "The news protocol is applied.",
        "The news protocol is not applied.",
    ))
    spec = (
        ("include_depth", "choice", "include_depth", _DEPTH_ORDER),
        ("state_sufficient", "noul", "state_sufficient", None),
        ("session_fitness", "score", "session_fitness", None),
        ("geometry_parameter", "score", "geometry_parameter", None),
        ("persistence", "score", "persistence", None),
        ("firehose", "noul", "cfl_firehose", None),
        ("noul_every_tick", "noul", "cfl_noul_every_tick", None),
        ("ask_together", "noul", "cfl_ask_together", None),
        ("one_post", "noul", "cfl_one_post", None),
        ("extra_pass", "noul", "cfl_extra_pass", None),
        ("apply", "noul", "cfl_apply", None),
        ("silent_apply", "noul", "cfl_silent_apply", None),
        ("never_place", "noul", "cfl_never_place", None),
        ("never_flatten", "noul", "cfl_never_flatten", None),
        ("never_remint", "noul", "cfl_never_remint", None),
        ("news_protocol", "noul", "cfl_news_protocol", None),
    )
    decided = _decide(facts, questions, spec)
    return {
        "state": facts,
        "model": decided.get("model") or MODEL,
        "questions": questions,
        "seat": seat,
        "include_depth": decided.get("include_depth"),
        "state_sufficient": decided.get("state_sufficient"),
        "session_fitness": decided.get("session_fitness"),
        "geometry_parameter": decided.get("geometry_parameter"),
        "persistence": decided.get("persistence"),
        "firehose": decided.get("firehose"),
        "noul_every_tick": decided.get("noul_every_tick"),
        "ask_together": decided.get("ask_together"),
        "one_post": decided.get("one_post"),
        "extra_pass": decided.get("extra_pass"),
        "apply": decided.get("apply"),
        "silent_apply": decided.get("silent_apply"),
        "never_place": decided.get("never_place"),
        "never_flatten": decided.get("never_flatten"),
        "never_remint": decided.get("never_remint"),
        "NEWS_PROTOCOL_APPLIED": decided.get("news_protocol"),
    }


def ingest_challenge(path: Path) -> dict[str, Any]:
    deals = load_jsonl(path)
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for deal in deals:
        inp = deal.get("input") if isinstance(deal.get("input"), Mapping) else deal
        feat = feature_row_from_challenge(inp)
        completeness = feat.get("completeness") if isinstance(feat.get("completeness"), Mapping) else {}
        if not _is_true(completeness.get("row_reaches")) or not _is_true(completeness.get("asof_reaches")):
            skipped.append(
                {
                    "ticket": inp.get("ticket"),
                    "reason": completeness.get("fail_reason"),
                    "keys": completeness.get("asof_reaches"),
                }
            )
            continue
        rows.append(
            {
                "feature": feat,
                "label": label_row_from_challenge(deal),
                "source": {"path": str(path), "sha256": sha256_file(path), "grain": "challenge_ticket"},
            }
        )
    return {
        "n_deals": len(deals),
        "n_rows": len(rows),
        "n_skipped": len(skipped),
        "skipped": skipped,
        "rows": rows,
        "path": str(path),
        "sha256": sha256_file(path),
    }


def ingest_walks(paths: Iterable[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for path in paths:
        payload = load_json(path)
        if not isinstance(payload, Mapping):
            continue
        sha = sha256_file(path)
        cells = extract_walk_cells(payload, source_path=str(path), source_sha256=sha)
        files.append(
            {
                "path": str(path),
                "sha256": sha,
                "schema": payload.get("schema"),
                "n_cells": len(cells),
                "bytes": path.stat().st_size if path.is_file() else 0,
            }
        )
        rows.extend(cells)
    return {"n_files": len(files), "n_rows": len(rows), "files": files, "rows": rows}


def ingest_screening(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    table = payload if isinstance(payload, list) else []
    rows = []
    for row in table:
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "feature": feature_from_screening(row),
                "label": label_from_screening(row),
                "source": {"path": str(path), "sha256": sha256_file(path), "grain": "multi_instrument_screening"},
            }
        )
    return {
        "n_rows": len(rows),
        "path": str(path),
        "sha256": sha256_file(path),
        "rows": rows,
        "symbols": [row["feature"]["identity"]["symbol"] for row in rows],
    }


def _compact_row(row: Mapping[str, Any]) -> dict[str, Any]:
    feat = row.get("feature") or {}
    lab = row.get("label") or {}
    ident = feat.get("identity") or {}
    sess = feat.get("sessions") or {}
    return {
        "schema": SLICE_SCHEMA,
        "grain": feat.get("grain") or lab.get("grain"),
        "symbol": ident.get("symbol"),
        "sleeve": ident.get("sleeve"),
        "family_class": ident.get("family_class"),
        "named": sess.get("named"),
        "occupancy": sess.get("occupancy_label"),
        "vol_bucket": (feat.get("regime") or {}).get("vol_bucket"),
        "plan_r": (feat.get("geometry") or {}).get("plan_r"),
        "exit_class": lab.get("exit_class"),
        "long_p_target": lab.get("long_p_target"),
        "n": lab.get("n") or lab.get("n_obs"),
        "ticket": ident.get("candidate_id"),
        "feature_store_exclusion": lab.get("feature_store_exclusion"),
        "news_spine_empty": (feat.get("news") or {}).get("spine_empty"),
        "NEWS_PROTOCOL_APPLIED": (feat.get("news") or {}).get("NEWS_PROTOCOL_APPLIED"),
        "source": row.get("source"),
    }


def _slice_flags(gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "apply": gate.get("apply"),
        "silent_apply": gate.get("silent_apply"),
        "extra_pass": gate.get("extra_pass"),
        "never_place": gate.get("never_place"),
        "never_flatten": gate.get("never_flatten"),
        "never_remint": gate.get("never_remint"),
        "NEWS_PROTOCOL_APPLIED": gate.get("news_protocol"),
        "apply_persist": gate.get("persist"),
        "pin_window": gate.get("pin"),
        "loop_bound": gate.get("loop_bound"),
        "row_reaches": gate.get("reaches"),
        "fail_reason": gate.get("reason"),
        "model": gate.get("model") or MODEL,
    }


def build_slice(
    *,
    challenge_path: Path | None = None,
    walk_paths: Iterable[Path] | None = None,
    screening_path: Path | None = None,
    enabled: bool | None = None,
) -> dict[str, Any]:
    """Observer ingest. The env gate skips before an ask."""

    on = store_enabled() if enabled is None else enabled
    base = {
        "schema": SLICE_SCHEMA,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "invented_rows": 0,
        "do_not_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "feature_paths": list(FEATURE_PATHS),
        "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
    }
    if not on:
        return {**base, "skipped": True, "skip_reason": "GTOS_JEV_FEATURE_LABEL_STORE_off"}
    gate = _gate_ask(login=CHALLENGE_LOGIN, ns=CHALLENGE_NS)
    flagged = _slice_flags(gate)
    if not _is_true(gate.get("reaches")):
        return {
            **base,
            **flagged,
            "skipped": True,
            "skip_reason": gate.get("reason"),
            "fail_closed": gate.get("reaches"),
        }
    sources = discover_sources(
        challenge_path=challenge_path,
        walk_paths=walk_paths,
        screening_path=screening_path,
    )
    challenge = ingest_challenge(Path(sources["challenge"]))
    walks = ingest_walks(sources["walks"])
    screening = ingest_screening(Path(sources["screening"]))
    score_rows = []
    for row in challenge["rows"][:3]:
        pack = score_payload(row["feature"], seat="gate")
        score_rows.append(
            {
                "ticket": row["feature"]["identity"]["candidate_id"],
                "seat": "gate",
                "n_questions": len(pack.get("questions") or {}),
                "include_depth": pack.get("include_depth"),
                "firehose": pack.get("firehose"),
                "noul_every_tick": pack.get("noul_every_tick"),
                "ask_together": pack.get("ask_together"),
                "one_post": pack.get("one_post"),
            }
        )
    walk_score = None
    for row in walks["rows"]:
        if row["feature"].get("grain") == "unsigned_m15_cell" and (
            row["feature"].get("sessions") or {}
        ).get("named") == "london_ny":
            walk_score = score_payload(row["feature"], seat="gate")
            break
    compact = [_compact_row(row) for row in challenge["rows"] + walks["rows"] + screening["rows"]]
    width = _width(gate.get("loop_bound"))
    if width is not None:
        compact = compact[:width]
    return {
        **base,
        **flagged,
        "skipped": False,
        "sources": {
            "challenge": str(sources["challenge"]),
            "walks": [str(path) for path in sources["walks"]],
            "screening": str(sources["screening"]),
        },
        "challenge": {
            "n_deals": challenge["n_deals"],
            "n_rows": challenge["n_rows"],
            "n_skipped": challenge["n_skipped"],
            "skipped": challenge["skipped"],
            "sha256": challenge["sha256"],
            "path": challenge["path"],
        },
        "walks": {
            "n_files": walks["n_files"],
            "n_rows": walks["n_rows"],
            "files": walks["files"],
        },
        "screening": {
            "n_rows": screening["n_rows"],
            "symbols": screening["symbols"],
            "sha256": screening["sha256"],
            "path": screening["path"],
        },
        "n_feature_rows": challenge["n_rows"] + walks["n_rows"] + screening["n_rows"],
        "score_samples": score_rows,
        "walk_score_named": (
            {
                "named": "london_ny",
                "n_questions": len((walk_score or {}).get("questions") or {}),
                "firehose": (walk_score or {}).get("firehose"),
                "session_fitness_present": "session_fitness" in ((walk_score or {}).get("questions") or {}),
            }
            if walk_score
            else None
        ),
        "rows": compact,
        "challenge_rows": challenge["rows"],
        "walk_rows": walks["rows"],
        "screening_rows": screening["rows"],
    }


def write_store(pack: Mapping[str, Any], path: Path | None = None) -> Path:
    target = path or default_store_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    slim = {key: value for key, value in pack.items() if key not in {"challenge_rows", "walk_rows", "screening_rows"}}
    target.write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8")
    return target

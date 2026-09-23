"""Labels for market state. One post per state.

The unique highest probability is the decision. A tie or an empty
probability map is not a decision. A bare label is not a probability. An empty answer, a tie,
or an error is None. It does not restore a cutoff.

The wait on the post is the expiry on the facts. No expiry means no
timeout. The cache key is the facts. The same facts return the stored
answer. Off the Challenge writer the return is LEGACY and this module
does not fill a label.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
CHALLENGE_NS = "operator"
_ASK = (
    "The facts are on the card. "
    "The unique highest probability is the decision. "
    "An empty answer or a tie is not a decision. "
    "Do not send."
)
_SCORE_ASK = (
    "The score you return is the bound for this state. "
    "An empty score leaves the bound unset. "
    "Do not send."
)

_CACHE: dict[str, Any] = {}
_INFLIGHT: set[str] = set()
_LOCK = threading.Lock()
_LAST_ERROR: str | None = None


class _Legacy:
    """Caller keeps its own comparison. Not a decision."""


LEGACY = _Legacy()

Step = tuple[str, str, str]


def on_challenge(namespace: str | None = None) -> bool:
    if os.environ.get("GTOS_UNIQUE_LOADER_SIDE_TEST") == "1":
        return False
    if namespace is not None and str(namespace).strip() not in ("", CHALLENGE_NS):
        return False
    argv = " ".join(sys.argv).replace("\\", "/").lower()
    return "operator" in argv and "run_book" in argv


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _qid(spot: str, positive: str) -> str:
    raw = f"{spot}.{positive}"
    return "".join(ch if ch.isalnum() or ch in "._" else "_" for ch in raw)


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _probs(answer: Any, names: set[str]) -> dict[str, float]:
    """Probability map only. A bare label is not a vote."""

    if not isinstance(answer, dict):
        return {}
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
                return out
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
            return out
    return {}


def _unique(probs: Mapping[str, float]) -> str | None:
    if not probs:
        return None
    best = max(probs.values())
    winners = [name for name, value in probs.items() if value == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _cache_key(spot: str, facts: Mapping[str, Any], steps: Sequence[Step], *, either: bool) -> str:
    blob = json.dumps(
        {"spot": spot, "facts": _jsonable(dict(facts)), "steps": list(steps), "either": either},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _expiry_s(facts: Mapping[str, Any]) -> float | None:
    """Seconds until this state expires. No expiry means the ask does not wait."""

    if not isinstance(facts, Mapping):
        return None
    for key in ("expires_in_s", "seconds_to_print", "seconds_to_cycle"):
        number = _as_float(facts.get(key))
        if number is not None and number > 0:
            return number
    return None


def _post(
    spot: str,
    facts: Mapping[str, Any],
    steps: Sequence[Step],
    timeout_s: float | None = None,
) -> dict[str, str | None]:
    global _LAST_ERROR
    winners: dict[str, str | None] = {}
    try:
        from .jev_client import resolve_key
    except Exception as exc:  # noqa: BLE001
        _LAST_ERROR = type(exc).__name__
        return { _qid(spot, positive): None for positive, _neg, _ins in steps }
    key, _source = resolve_key()
    if not key:
        _LAST_ERROR = "key_unreadable"
        return { _qid(spot, positive): None for positive, _neg, _ins in steps }
    questions = {}
    meta = []
    for positive, negative, instructions in steps:
        qid = _qid(spot, positive)
        questions[qid] = {
            "type": "choice",
            "instructions": instructions,
            "criteria": {
                positive: instructions,
                negative: "That condition is not met.",
            },
        }
        meta.append((qid, positive, negative))
    payload = {
        "model": MODEL,
        "state": _jsonable({"spot": spot, "facts": dict(facts)}),
        "questions": questions,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-judgment/0.1",
        },
    )
    try:
        opener = urllib.request.urlopen(req) if timeout_s is None else urllib.request.urlopen(req, timeout=timeout_s)
        with opener as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _LAST_ERROR = f"http_{exc.code}"
        return {qid: None for qid, _p, _n in meta}
    except Exception as exc:  # noqa: BLE001
        _LAST_ERROR = type(exc).__name__
        return {qid: None for qid, _p, _n in meta}
    answers = body.get("answers") if isinstance(body, dict) else None
    if not isinstance(answers, dict):
        _LAST_ERROR = "no_answers"
        return {qid: None for qid, _p, _n in meta}
    _LAST_ERROR = None
    for qid, positive, negative in meta:
        names = {positive, negative}
        winners[qid] = _unique(_probs(answers.get(qid), names))
    return winners


def _concurrent(key: str, facts: Mapping[str, Any], run: Any) -> str | None:
    """Return a cached label. A cold ask with no expiry does not hold the caller.

    ``run`` receives the expiry seconds, or None when the state has no deadline.
    Only a real label is stored. An empty answer is not cached and is not a cutoff.
    """

    with _LOCK:
        cached = _CACHE.get(key)
        if isinstance(cached, str) and cached:
            return cached
        if key in _INFLIGHT:
            return None
        _INFLIGHT.add(key)
    expiry = _expiry_s(facts)

    def wrapped() -> str | None:
        try:
            chosen = run(expiry)
            if isinstance(chosen, str) and chosen:
                with _LOCK:
                    _CACHE[key] = chosen
            return chosen if isinstance(chosen, str) else None
        finally:
            with _LOCK:
                _INFLIGHT.discard(key)

    if expiry is None:
        threading.Thread(target=wrapped, name="state-choice", daemon=True).start()
        return None
    box: dict[str, Any] = {}

    def wait() -> None:
        box["v"] = wrapped()

    thread = threading.Thread(target=wait, name="state-choice", daemon=True)
    thread.start()
    thread.join(expiry)
    value = box.get("v")
    return value if isinstance(value, str) else None


def first_positive(
    spot: str,
    facts: Mapping[str, Any],
    steps: Sequence[Step],
    *,
    either: bool = False,
) -> str | None:
    """First step whose positive side is the unique highest.

    ``either`` returns the negative side too, for a single two-label condition.
    A step that is tied or empty is skipped. No step win returns None.
    The same facts return the stored label. No expiry does not wait.
    """

    key = _cache_key(spot, facts, steps, either=either)

    def run(timeout_s: float | None) -> str | None:
        winners = _post(spot, facts, steps, timeout_s=timeout_s)
        for positive, negative, _instructions in steps:
            winner = winners.get(_qid(spot, positive))
            if winner == positive:
                return positive
            if either and winner == negative:
                return negative
        return None

    return _concurrent(key, facts, run)


def _post_label(
    spot: str,
    facts: Mapping[str, Any],
    labels: Sequence[str],
    instructions: str,
    timeout_s: float | None,
) -> str | None:
    """One choice among the labels. The unique highest probability is the label."""

    global _LAST_ERROR
    names = {str(label) for label in labels if str(label)}
    if not names:
        return None
    try:
        from .jev_client import resolve_key
    except Exception as exc:  # noqa: BLE001
        _LAST_ERROR = type(exc).__name__
        return None
    key, _source = resolve_key()
    if not key:
        _LAST_ERROR = "key_unreadable"
        return None
    qid = _qid(spot, "label")
    payload = {
        "model": MODEL,
        "state": _jsonable({"spot": spot, "facts": dict(facts)}),
        "questions": {
            qid: {
                "type": "choice",
                "instructions": instructions,
                "criteria": {name: f"This state is {name}." for name in names},
            }
        },
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-judgment/0.1",
        },
    )
    try:
        opener = urllib.request.urlopen(req) if timeout_s is None else urllib.request.urlopen(req, timeout=timeout_s)
        with opener as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _LAST_ERROR = f"http_{exc.code}"
        return None
    except Exception as exc:  # noqa: BLE001
        _LAST_ERROR = type(exc).__name__
        return None
    answers = body.get("answers") if isinstance(body, dict) else None
    if not isinstance(answers, dict):
        _LAST_ERROR = "no_answers"
        return None
    _LAST_ERROR = None
    return _unique(_probs(answers.get(qid), names))


def label_choice(
    spot: str,
    facts: Mapping[str, Any],
    labels: Sequence[str],
    instructions: str,
) -> Any:
    """The label for this state. Empty, tie, and error stay unset."""

    def ask() -> str | None:
        key = _cache_key(
            spot,
            facts,
            tuple((str(name), "", instructions) for name in labels),
            either=False,
        )
        return _concurrent(
            key,
            facts,
            lambda timeout_s: _post_label(spot, facts, labels, instructions, timeout_s),
        )

    return _gate(ask)


def side(spot: str, facts: Mapping[str, Any], positive: str, negative: str, instructions: str) -> str | None:
    return first_positive(spot, facts, [(positive, negative, instructions)], either=True)


def _gate(fn):
    if not on_challenge():
        return LEGACY
    return fn()


def session_named_choice(utc_hour: int, is_friday: bool) -> Any:
    return label_choice(
        "sessions.named",
        {"utc_hour": int(utc_hour), "is_friday": bool(is_friday)},
        ("friday_cutoff", "dead_21_00z", "asia", "london", "ny"),
        _ASK,
    )


def asset_class_choice(symbol: str) -> Any:
    def ask():
        from .symbol_class import CRYPTO, ENERGY, FX_CCY, INDEX, METALS

        return first_positive(
            "symbol_class.asset_class",
            {
                "symbol": symbol,
                "metals": sorted(METALS),
                "index": sorted(INDEX),
                "crypto": sorted(CRYPTO),
                "energy": sorted(ENERGY),
                "fx_ccy": sorted(FX_CCY),
            },
            [
                ("metal", "not_metal", "Is symbol a member of metals?"),
                ("index", "not_index", "Is symbol a member of index?"),
                ("crypto", "not_crypto", "Is symbol a member of crypto?"),
                ("energy", "not_energy", "Is symbol a member of energy?"),
                (
                    "fx",
                    "not_fx",
                    "Is symbol a pair whose base and quote are both in fx_ccy, with base not XAU or XAG?",
                ),
            ],
        )

    return _gate(ask)


def usd_leg_choice(base: str | None, quote: str | None) -> Any:
    def ask():
        return first_positive(
            "symbol_class.usd_leg",
            {"base": base, "quote": quote},
            [
                ("base", "not_base", "Is base exactly USD?"),
                ("quote", "not_quote", "Is quote exactly USD?"),
            ],
        )

    return _gate(ask)


def session_bias_choice(symbol: str, asset: str | None, named: str | None) -> Any:
    labels: list[str] = []
    for name in (named, "ny", "tokyo_ny", "london"):
        text = str(name or "").strip()
        if text and text not in labels:
            labels.append(text)
    return label_choice(
        "symbol_class.session_bias",
        {"symbol": symbol, "asset_class": asset, "named_session": named},
        tuple(labels),
        _ASK,
    )


def _threshold_choice(spot: str, facts: dict, steps: list[Step]) -> Any:
    return _gate(lambda: first_positive(spot, facts, steps))


def bucket_return_choice(ret: float) -> Any:
    return label_choice(
        "regime.bucket_return",
        {"ret": ret},
        ("strong_up", "up", "flat", "down", "strong_down"),
        _ASK,
    )


def bucket_vol_choice(ratio: float) -> Any:
    return label_choice(
        "regime.bucket_vol",
        {"ratio": ratio},
        ("compressed", "normal", "elevated", "extreme"),
        _ASK,
    )


def bucket_atr_choice(ratio: float) -> Any:
    return label_choice(
        "regime.bucket_atr_expansion",
        {"ratio": ratio},
        ("contracting", "flat", "expanding", "spiking"),
        _ASK,
    )


def bucket_sma_choice(frac: float) -> Any:
    return label_choice(
        "regime.bucket_price_vs_sma",
        {"frac": frac},
        ("well_above", "above", "near", "below", "well_below"),
        _ASK,
    )


def bucket_trend_choice(
    *,
    slope: float | None,
    mom: float | None,
    green_ratio: float | None,
) -> Any:
    return label_choice(
        "regime.bucket_trend_persistence",
        {"slope": slope, "mom": mom, "green_ratio": green_ratio},
        ("strong_up", "weak_up", "mixed", "weak_down", "strong_down"),
        _ASK,
    )


def trend_choice(close_vs: float) -> Any:
    label = label_choice(
        "bars.tf_snap.trend",
        {"close_vs_close_n_atr": close_vs},
        ("up", "down", "flat"),
        _ASK,
    )
    if label is LEGACY:
        return LEGACY
    return {"up": 1, "down": -1, "flat": 0}.get(label) if isinstance(label, str) else None


def window_bool(spot: str, facts: Mapping[str, Any], instructions: str) -> Any:
    def ask():
        winner = side(spot, facts, "inside", "outside", instructions)
        if winner == "inside":
            return True
        if winner == "outside":
            return False
        return None

    return _gate(ask)


def london_expand_choice(value: float) -> Any:
    return label_choice(
        "pack3.london_expand",
        {"value": value},
        ("pass", "fail", "mid"),
        _ASK,
    )


def ny_impulse_choice(value: float) -> Any:
    return label_choice(
        "pack3.ny_impulse",
        {"value": value},
        ("impulse", "chop", "mid"),
        _ASK,
    )


def gj_residual_choice(magnitude: float, cap: float) -> Any:
    def ask():
        return side(
            "pack3.gj_residual",
            {"abs_residual": magnitude, "resid_cap": cap},
            "fail",
            "pass",
            "Is abs_residual greater than resid_cap?",
        )

    return _gate(ask)


def stance_choice(trend: int) -> Any:
    return _threshold_choice(
        "world.stance",
        {"trend": int(trend)},
        [
            ("up", "not_up", "Is trend exactly 1?"),
            ("down", "not_down", "Is trend exactly -1?"),
            ("flat", "not_flat", "Is trend exactly 0?"),
        ],
    )


def combine_choice(ups: int, downs: int) -> Any:
    return _threshold_choice(
        "world.combine_signed",
        {"ups": int(ups), "downs": int(downs)},
        [
            ("mixed", "not_mixed", "Are ups and downs both greater than 0?"),
            ("stronger", "not_stronger", "Is ups greater than 0 and downs equal to 0?"),
            ("weaker", "not_weaker", "Is downs greater than 0 and ups equal to 0?"),
        ],
    )


def relation_choice(c20: float) -> Any:
    return label_choice(
        "world.corr_relation",
        {"corr_20d": c20},
        ("against_usd", "with_usd", "uncorrelated"),
        _ASK,
    )


def broken_choice(c20: float, c60: float) -> Any:
    def ask():
        winner = side(
            "world.corr_regime_broken",
            {"corr_20d": c20, "corr_60d": c60},
            "broken",
            "not_broken",
            "Do these two correlations describe different regimes? The option you return is the branch. An empty answer or a tie leaves it unset.",
        )
        if winner == "broken":
            return True
        if winner == "not_broken":
            return False
        return None

    return _gate(ask)


def sold_into_choice(side_name: str, stance: str) -> Any:
    def ask():
        winner = side(
            "world.gold_sold_into_usd_strength",
            {"side": side_name, "usd_stance": stance},
            "sold_into",
            "not_sold_into",
            "Is side short or sell while usd_stance is stronger, or side long or buy while usd_stance is weaker?",
        )
        if winner == "sold_into":
            return True
        if winner == "not_sold_into":
            return False
        return None

    return _gate(ask)


def structure_direction_choice(hh: int, hl: int, ll: int, lh: int, recent_pairs: int) -> Any:
    return _threshold_choice(
        "market_state.structure_direction",
        {
            "hh_count": hh,
            "hl_count": hl,
            "ll_count": ll,
            "lh_count": lh,
            "recent_pairs": recent_pairs,
        },
        [
            (
                "bullish",
                "not_bullish",
                "Are hh_count and hl_count both at least recent_pairs?",
            ),
            (
                "bearish",
                "not_bearish",
                "Are ll_count and lh_count both at least recent_pairs?",
            ),
        ],
    )


def swing_bar_choice(
    *,
    index: int,
    center_high: float,
    max_left_high: float,
    max_right_high: float,
    center_low: float,
    min_left_low: float,
    min_right_low: float,
) -> Any:
    def ask():
        high = side(
            "market_state.swing_high",
            {
                "index": index,
                "center_high": center_high,
                "max_left_high": max_left_high,
                "max_right_high": max_right_high,
            },
            "swing_high",
            "not_swing_high",
            "Is center_high strictly greater than max_left_high and strictly greater than max_right_high?",
        )
        low = side(
            "market_state.swing_low",
            {
                "index": index,
                "center_low": center_low,
                "min_left_low": min_left_low,
                "min_right_low": min_right_low,
            },
            "swing_low",
            "not_swing_low",
            "Is center_low strictly less than min_left_low and strictly less than min_right_low?",
        )
        return (
            True if high == "swing_high" else False if high == "not_swing_high" else None,
            True if low == "swing_low" else False if low == "not_swing_low" else None,
        )

    return _gate(ask)


def swing_label_choice(kind: str, price: float, previous: float) -> Any:
    spot = f"market_state.swing_label.{kind}"
    if kind == "high":
        steps = [
            ("HH", "not_HH", "Is price strictly greater than previous?"),
            ("LH", "not_LH", "Is price strictly less than previous?"),
            ("EH", "not_EH", "Is price equal to previous?"),
        ]
    else:
        steps = [
            ("HL", "not_HL", "Is price strictly greater than previous?"),
            ("LL", "not_LL", "Is price strictly less than previous?"),
            ("EL", "not_EL", "Is price equal to previous?"),
        ]
    return _threshold_choice(spot, {"kind": kind, "price": price, "previous": previous}, steps)


def displacement_flags(ratios: Sequence[float]) -> Any:
    def ask():
        out: list[bool | None] = [None] * len(ratios)

        def one(i: int, ratio: float) -> tuple[int, bool | None]:
            winner = side(
                "market_state.displacement",
                {"index": i, "disp_ratio": ratio},
                "displacement",
                "no_displacement",
                "Is this bar a displacement? The option you return is the branch. An empty answer or a tie leaves it unset.",
            )
            if winner == "displacement":
                return i, True
            if winner == "no_displacement":
                return i, False
            return i, None

        if not ratios:
            return []
        workers = len(ratios)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(one, i, float(ratio)) for i, ratio in enumerate(ratios)]
            for fut in as_completed(futs):
                i, flag = fut.result()
                out[i] = flag
        return out

    return _gate(ask)


def session_atr_choice(hour: int) -> Any:
    return label_choice(
        "market_state.session_atr_window",
        {"utc_hour": int(hour)},
        ("london", "ny"),
        _ASK,
    )


def gbpjpy_verdict_choice(dual: bool, resid: float | None, cap: float) -> Any:
    def ask():
        hit = first_positive(
            "pack3.gbpjpy_verdict",
            {"dual_leg_agree": bool(dual), "residual": resid, "resid_cap": cap},
            [
                ("dual_split", "dual_ok", "Is dual_leg_agree false?"),
                ("residual", "residual_ok", "Is residual greater than resid_cap?"),
                (
                    "pass",
                    "not_pass",
                    "Is dual_leg_agree true and is residual missing or at most resid_cap?",
                ),
            ],
        )
        if hit == "dual_split":
            return ("fail", "dual_split")
        if hit == "residual":
            return ("fail", "residual")
        if hit == "pass":
            return ("pass", None)
        return (None, None)

    return _gate(ask)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _file_facts(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _receipt_dir() -> Path:
    return _repo_root() / "pipeline_state" / "ultimate_book" / CHALLENGE_NS / "judgment"


def note_import() -> dict[str, Any]:
    """Write the pid and these bytes as soon as the Challenge writer imports them."""

    if not on_challenge():
        return {"imported": False, "reason": "not_challenge"}
    path = Path(__file__).resolve()
    facts = _file_facts(path)
    payload = {
        "schema": "gtos.judgment.state_choices.import.v1",
        "pid": os.getpid(),
        "imported": True,
        "order_send": False,
        "persist": None,
        "module": facts,
        "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        folder = _receipt_dir()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"state_choices_loaded.{os.getpid()}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        payload["receipt_error"] = type(exc).__name__
    return payload


def maybe_ask_surface(*, namespace: str | None = None) -> dict[str, Any]:
    """Ask the open book's spots once per heavy rung. Does not send, flatten, or remint."""

    if not on_challenge(namespace):
        return {
            "asked": False,
            "reason": "not_challenge",
            "order_send": False,
            "persist": None,
        }
    note_import()
    from . import pack3_fields, symbol_class
    from .gold_state import _session_named

    now = datetime.now(timezone.utc)
    names = ("XAUUSD", "EURUSD", "USDJPY", "US30", "BTCUSD", "USOIL")
    named = _session_named(now.hour, now.weekday() == 4)
    classes = {sym: symbol_class.asset_class_for(sym) for sym in names}
    biases = {sym: symbol_class.session_bias(sym, named) for sym in names}
    legs = {sym: symbol_class.usd_leg(sym) for sym in names}
    windows = {
        "london_open": pack3_fields.in_london_open(now),
        "us30_cash_open": pack3_fields.in_us30_cash_open(now),
        "ldn_ny_overlap": pack3_fields.in_ldn_ny_overlap(now),
    }
    modules = [
        Path(__file__).resolve(),
        Path(symbol_class.__file__).resolve(),
        Path(pack3_fields.__file__).resolve(),
        Path(_session_named.__code__.co_filename).resolve(),
    ]
    for extra in (
        "bars.py",
        "regime_buckets.py",
        "world_state.py",
        "symbol_state.py",
        "unique_loader.py",
    ):
        modules.append(Path(__file__).resolve().parent / extra)
    modules.append(_repo_root() / "src" / "components" / "market_state.py")
    modules.append(_repo_root() / "src" / "models" / "market_state_models.py")
    files = [_file_facts(path) for path in modules if path.is_file()]
    payload = {
        "schema": "gtos.judgment.state_choices.v1",
        "asked": True,
        "model": MODEL,
        "namespace": CHALLENGE_NS,
        "pid": os.getpid(),
        "as_of_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "order_send": False,
        "persist": None,
        "flatten": False,
        "sessions_named": named,
        "asset_class": classes,
        "session_bias": biases,
        "usd_leg": legs,
        "windows": windows,
        "last_error": _LAST_ERROR,
        "modules": files,
        "wired_not_priced_here": [
            "regime.bucket_return",
            "regime.bucket_vol",
            "regime.bucket_atr_expansion",
            "regime.bucket_price_vs_sma",
            "regime.bucket_trend_persistence",
            "bars.tf_snap.trend",
            "pack3.london_expand",
            "pack3.ny_impulse",
            "pack3.gj_residual",
            "pack3.gbpjpy_verdict",
            "world.stance",
            "world.combine_signed",
            "world.corr_relation",
            "world.corr_regime_broken",
            "world.gold_sold_into_usd_strength",
            "market_state.structure_direction",
            "market_state.swing_high",
            "market_state.swing_low",
            "market_state.swing_label",
            "market_state.displacement",
            "market_state.session_atr_window",
        ],
    }
    try:
        folder = _receipt_dir()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "state_choices.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        (folder / f"state_choices_loaded.{os.getpid()}.json").write_text(
            json.dumps(
                {"pid": os.getpid(), "modules": files, "as_of_utc": payload["as_of_utc"]},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        payload["receipt_error"] = type(exc).__name__
    return payload

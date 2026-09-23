"""OSS-harvest typed extras for gold_state. Research-only. Never places.

Re-expresses surveyed architecture as named fields on our object — not a
vendor tree. Attach is opt-in via ``attach_harvest_blocks``. Does not import
``mt5`` / ``execution``. Does not invent NEWS_PROTOCOL / HIGH events.
Does not remint, flatten, or lift an envelope wall.

Every decision, including every parameter, is the System One return for
that state. One call: ``jev_client.evaluate`` with model ``jev-1.13.0``,
``merge_sleeve=False``, POST https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
that ask, and the return is stored for the next ask.

An empty answer, a tie, a missing score, or an error leaves that field
unset and does not restore a constant. A floor and a baseline are not a
question. This module does not send.

Chair NAME 2026-09-18: keep ``harvest.*`` extras on ``gold_state.v0``.
Do not cut ``v0.1``. The live multiplier is the returned score.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
SURVEY_PATH = REPO_ROOT / "judgment" / "astra" / "oss_harvest" / "SURVEYED_REPOS.json"

SCHEMA_EXTRAS = "gtos.judgment.gold_state.v0.harvest.v0"
SCHEMA_LOCK = "gold_state.v0_harvest_extras"
NEVER_VENDOR = True
NEVER_PLACE = True
NEVER_INVENT_NEWS = True

MODEL = "jev-1.13.0"
# Challenge-true pack of record. Verification login stays quarantined.
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
QUARANTINE_LOGIN = 0

TF_ROUTES = frozenset({"M15", "H4", "D1", "multi_m15_h4", "unknown"})
PROTECTION_KINDS = frozenset(
    {"cooldown", "stoploss_guard", "maxdd", "occupancy", "two_stop", "cluster"}
)
FILL_MODELS = frozenset({"bar_close", "next_open", "tick", "unknown"})
MAXDD_RULES = frozenset({"static_floor", "trailing"})
RESET_CLOCKS = frozenset({"cest_midnight", "server_midnight"})
ENVELOPE_PHASES = frozenset({"1", "2", "funded", "unknown"})
LEARN_LABELS = frozenset({"target", "stop", "time_stop", "manual_other", "unknown"})
REQUIRED_SURVEY_FIELDS = ("full_name", "stars", "license", "class")
PIT_VALUE_KEYS = (
    "ac60",
    "vol_ratio",
    "htf_slope_norm",
    "mom_20_atr",
    "fvg_freshness_bars",
    "session_hour",
    "a8_k_of_4_pass",
)
PIT_SKIP_KEYS = frozenset(
    {"tag", "cluster", "a8_source", "ac60_source", "atr_ratio", "intra_size"}
)

# Question catalog. ignore_if does not skip an ask and does not fill a value.
PROPOSED_QUESTIONS: dict[str, dict[str, str]] = {
    "feature_as_of_honest": {
        "primitive": "noul",
        "ignore_if": "",
        "gist": "Per-field as-of versus clock.as_of_utc. The noul is the return.",
    },
    "route_class": {
        "primitive": "choice",
        "ignore_if": "",
        "gist": "metal, fx_major, fx_cross, index, multi, or unknown.",
    },
    "protection_still_earns": {
        "primitive": "score",
        "ignore_if": "",
        "gist": "How this protection still earns. The score is the return.",
    },
    "would_be_nth_stop": {
        "primitive": "noul",
        "ignore_if": "",
        "gist": "Label only. The integer count stays the counter.",
    },
    "cost_complete": {
        "primitive": "noul",
        "ignore_if": "",
        "gist": "Named spread, slip, and commission. The noul is the return.",
    },
    "fill_realism": {
        "primitive": "score",
        "ignore_if": "",
        "gist": "Fill realism for the named model. The score is the return.",
    },
    "wall_pressure": {
        "primitive": "score",
        "ignore_if": "",
        "gist": "Pressure near the prop wall. Label only. The score is the return.",
    },
    "instrument_known": {
        "primitive": "noul",
        "ignore_if": "",
        "gist": "A spec is present for this symbol. The noul is the return.",
    },
    "paper_live_parity": {
        "primitive": "score",
        "ignore_if": "",
        "gist": "Shadow fill against the Challenge fill. The score is the return.",
    },
    "exit_class": {
        "primitive": "choice",
        "ignore_if": "",
        "gist": "Includes time_stop. The choice is the return.",
    },
}

CHAIR_NEXT_ACTIONS = (
    "do_not_vendor",
    "schema_locked_v0_extras",
    "p0_1_proved_shadow_0",
    "p0_2_chair_named_route_class_table_shadow_only",
    "p0_5_proved_shadow_fill_realism",
    "p0_3_p0_4_idle_until_asked",
    "do_not_invent_route_class_outside_chair_table",
    "learn_via_actuator_not_gym",
    "envelope_walls_stay_integers",
    "reject_chat_llm_place",
)
XAU_SYMBOLS = frozenset({"XAUUSD", "XAU", "GOLD"})
ROUTE_CLASS_CHOICES = frozenset({"metal", "fx_major", "fx_cross", "index", "unknown"})
# Chair NAME 2026-09-18 — the table is a fact on the ask. SHADOW labels only.
# XAUUSD → metal is the table fact (tf_route may still be multi_m15_h4).
# UK100 / BTC / ETH stay unnamed on the table until Chair names them after books land.
CHAIR_ROUTE_CLASS_TABLE = {
    "XAUUSD": "metal",
    "EURUSD": "fx_major",
    "GBPUSD": "fx_major",
    "USDJPY": "fx_major",
    "EURGBP": "fx_major",
    "GBPJPY": "fx_cross",
    "US30": "index",
}
CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED = frozenset({"UK100", "BTCUSD", "ETHUSD"})
ROUTE_CLASS_FROM_TF = {
    "multi_m15_h4": "multi",
    "M15": "m15_sleeve",
    "H4": "h4_sleeve",
    "D1": "d1_sleeve",
    "unknown": "unknown",
}

_ROUTE_ORDER = ("metal", "fx_major", "fx_cross", "index", "unknown", "multi")
_EXIT_ORDER = ("target", "stop", "time_stop", "manual_other", "unknown")
_PHASE_ORDER = ("1", "2", "funded", "unknown")
_RESET_ORDER = ("cest_midnight", "server_midnight")
_REASON_ORDER = (
    "missing_symbol",
    "unknown_until_landed",
    "not_in_chair_table",
    "chair_named_metal",
    "chair_named_fx_major",
    "chair_named_fx_cross",
    "chair_named_index",
    "chair_named_index_house_hard_off",
    "chair_named_unknown",
)
_COMPONENT_ORDER = ("route", "pit", "protection", "envelope", "fill", "learn")
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
_ALLOWED_TYPES = frozenset({"noul", "choice", "score"})
_EXPOST_FALLBACK = (
    "miss_type",
    "exit_class",
    "close_reason",
    "R",
    "realized_r",
    "broker_net",
    "profit",
    "mfe",
    "mae",
    "won",
    "why_lost",
    "why_lost_text",
)
_UNSET = "An empty answer, a tie, or an error leaves it unset. This ask does not transmit an order."
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

_ROUTE_CRITERIA = {
    "metal": "The route class is metal.",
    "fx_major": "The route class is fx major.",
    "fx_cross": "The route class is an fx cross.",
    "index": "The route class is an index.",
    "unknown": "The route class is unknown.",
    "multi": "The route class is the legacy multi label.",
}
_EXIT_CRITERIA = {
    "target": "The exit class is target.",
    "stop": "The exit class is stop.",
    "time_stop": "The exit class is time_stop.",
    "manual_other": "The exit class is manual or other.",
    "unknown": "The exit class is unknown.",
}
_PHASE_CRITERIA = {
    "1": "The envelope phase is 1.",
    "2": "The envelope phase is 2.",
    "funded": "The envelope phase is funded.",
    "unknown": "The envelope phase is unknown.",
}
_RESET_CRITERIA = {
    "cest_midnight": "The reset clock is cest midnight.",
    "server_midnight": "The reset clock is server midnight.",
}
_REASON_CRITERIA = {name: f"The route reason is {name}." for name in _REASON_ORDER}
_COMPONENT_CRITERIA = {
    "route": "The harvest component is the route.",
    "pit": "The harvest component is the point-in-time contract.",
    "protection": "The harvest component is protection.",
    "envelope": "The harvest component is the envelope.",
    "fill": "The harvest component is the fill.",
    "learn": "The harvest component is the close label.",
}

# field, kind, order. The field name is the question id.
_SPEC: tuple[tuple[str, str, tuple[str, ...] | None], ...] = (
    ("feature_as_of_honest", "noul", _NOUL_ORDER),
    ("feature_as_of_parameter", "score", None),
    ("route_class", "choice", _ROUTE_ORDER),
    ("route_class_parameter", "score", None),
    ("route_decidable", "noul", _NOUL_ORDER),
    ("route_abstain", "noul", _NOUL_ORDER),
    ("route_moved", "noul", _NOUL_ORDER),
    ("route_left_unknown", "noul", _NOUL_ORDER),
    ("route_house_hard_off", "noul", _NOUL_ORDER),
    ("route_chair_named", "noul", _NOUL_ORDER),
    ("route_reason", "choice", _REASON_ORDER),
    ("protection_still_earns", "score", None),
    ("protection_still_earns_parameter", "score", None),
    ("would_be_nth_stop", "noul", _NOUL_ORDER),
    ("would_be_nth_stop_parameter", "score", None),
    ("two_stop_cap", "score", None),
    ("cost_complete", "noul", _NOUL_ORDER),
    ("cost_complete_parameter", "score", None),
    ("cost_decidable", "noul", _NOUL_ORDER),
    ("cost_abstain", "noul", _NOUL_ORDER),
    ("cost_moved", "noul", _NOUL_ORDER),
    ("fill_realism", "score", None),
    ("fill_realism_parameter", "score", None),
    ("fill_decidable", "noul", _NOUL_ORDER),
    ("fill_abstain", "noul", _NOUL_ORDER),
    ("fill_moved", "noul", _NOUL_ORDER),
    ("wall_pressure", "score", None),
    ("wall_pressure_parameter", "score", None),
    ("instrument_known", "noul", _NOUL_ORDER),
    ("instrument_known_parameter", "score", None),
    ("paper_live_parity", "score", None),
    ("paper_live_parity_parameter", "score", None),
    ("exit_class", "choice", _EXIT_ORDER),
    ("exit_class_parameter", "score", None),
    ("pit_decidable", "noul", _NOUL_ORDER),
    ("pit_abstain", "noul", _NOUL_ORDER),
    ("pit_moved", "noul", _NOUL_ORDER),
    ("envelope_phase", "choice", _PHASE_ORDER),
    ("envelope_phase_parameter", "score", None),
    ("envelope_reset", "choice", _RESET_ORDER),
    ("envelope_reset_parameter", "score", None),
    ("live_multiplier", "score", None),
    ("chair_named", "noul", _NOUL_ORDER),
    ("harvest_component", "choice", _COMPONENT_ORDER),
    ("component_exists", "noul", _NOUL_ORDER),
    ("harvest_threshold", "score", None),
    ("harvest_loop", "score", None),
    ("harvest_parameter", "score", None),
)
_ALL_FIELDS = tuple(row[0] for row in _SPEC)
_COMMON_FIELDS = ("harvest_threshold", "harvest_loop", "harvest_parameter")
_ROUTE_FIELDS = (
    "route_class",
    "route_class_parameter",
    "route_decidable",
    "route_abstain",
    "route_moved",
    "route_left_unknown",
    "route_house_hard_off",
    "route_chair_named",
    "route_reason",
    "live_multiplier",
) + _COMMON_FIELDS
_FILL_FIELDS = (
    "fill_realism",
    "fill_realism_parameter",
    "fill_decidable",
    "fill_abstain",
    "fill_moved",
) + _COMMON_FIELDS
_COST_FIELDS = (
    "cost_complete",
    "cost_complete_parameter",
    "cost_decidable",
    "cost_abstain",
    "cost_moved",
) + _COMMON_FIELDS
_PIT_FIELDS = (
    "feature_as_of_honest",
    "feature_as_of_parameter",
    "pit_decidable",
    "pit_abstain",
    "pit_moved",
) + _COMMON_FIELDS
_ENVELOPE_FIELDS = (
    "envelope_phase",
    "envelope_phase_parameter",
    "envelope_reset",
    "envelope_reset_parameter",
) + _COMMON_FIELDS

_NOUL_TEXT = {
    "feature_as_of_honest": (
        "Are the named feature as-of stamps honest against the clock on this state?",
        "The as-of stamps are honest against the clock.",
        "The as-of stamps are not honest against the clock.",
    ),
    "route_decidable": (
        "Is the route class decidable on this state?",
        "The route class is decidable.",
        "The route class is not decidable.",
    ),
    "route_abstain": (
        "Does the route class abstain on this state?",
        "Abstain the route class.",
        "Do not abstain the route class.",
    ),
    "route_moved": (
        "Did the route class move on this state?",
        "The route class moved.",
        "The route class did not move.",
    ),
    "route_left_unknown": (
        "Did the route class leave unknown on this state?",
        "The route class left unknown.",
        "The route class did not leave unknown.",
    ),
    "route_house_hard_off": (
        "Is this route house-hard-off on this state?",
        "This route is house-hard-off.",
        "This route is not house-hard-off.",
    ),
    "route_chair_named": (
        "Is this route class chair-named on this state?",
        "This route class is chair-named.",
        "This route class is not chair-named.",
    ),
    "would_be_nth_stop": (
        "Would this be the next same-sleeve stop on this state? "
        "The closed count on the state is the counter. This noul is only the label.",
        "This would be that next stop.",
        "This would not be that next stop.",
    ),
    "cost_complete": (
        "Are named spread, slip, and commission present on this fill?",
        "Named cost fields are present.",
        "Named cost fields are not present.",
    ),
    "cost_decidable": (
        "Is cost completeness decidable on this state?",
        "Cost completeness is decidable.",
        "Cost completeness is not decidable.",
    ),
    "cost_abstain": (
        "Does cost completeness abstain on this state?",
        "Abstain cost completeness.",
        "Do not abstain cost completeness.",
    ),
    "cost_moved": (
        "Did cost completeness move on this state?",
        "Cost completeness moved.",
        "Cost completeness did not move.",
    ),
    "fill_decidable": (
        "Is fill realism decidable on this state?",
        "Fill realism is decidable.",
        "Fill realism is not decidable.",
    ),
    "fill_abstain": (
        "Does fill realism abstain on this state?",
        "Abstain fill realism.",
        "Do not abstain fill realism.",
    ),
    "fill_moved": (
        "Did fill realism move on this state?",
        "Fill realism moved.",
        "Fill realism did not move.",
    ),
    "instrument_known": (
        "Is a spec present for this symbol?",
        "A spec is present for this symbol.",
        "A spec is not present for this symbol.",
    ),
    "pit_decidable": (
        "Is the point-in-time contract decidable on this state?",
        "The point-in-time contract is decidable.",
        "The point-in-time contract is not decidable.",
    ),
    "pit_abstain": (
        "Does the point-in-time contract abstain on this state?",
        "Abstain the point-in-time contract.",
        "Do not abstain the point-in-time contract.",
    ),
    "pit_moved": (
        "Did the point-in-time contract move on this state?",
        "The point-in-time contract moved.",
        "The point-in-time contract did not move.",
    ),
    "chair_named": (
        "Is this harvest block chair-named on this state?",
        "This harvest block is chair-named.",
        "This harvest block is not chair-named.",
    ),
    "component_exists": (
        "Does the named harvest component exist on this state?",
        "The named harvest component exists.",
        "The named harvest component does not exist.",
    ),
}
_SCORE_NOUN = {
    "feature_as_of_parameter": "feature as-of parameter",
    "route_class_parameter": "route-class parameter",
    "protection_still_earns": "protection-still-earns score",
    "protection_still_earns_parameter": "protection-still-earns parameter",
    "would_be_nth_stop_parameter": "would-be-nth-stop parameter",
    "two_stop_cap": "two-stop cap",
    "cost_complete_parameter": "cost-complete parameter",
    "fill_realism": "fill-realism score",
    "fill_realism_parameter": "fill-realism parameter",
    "wall_pressure": "wall-pressure score",
    "wall_pressure_parameter": "wall-pressure parameter",
    "instrument_known_parameter": "instrument-known parameter",
    "paper_live_parity": "paper-live parity",
    "paper_live_parity_parameter": "paper-live parity parameter",
    "exit_class_parameter": "exit-class parameter",
    "envelope_phase_parameter": "envelope-phase parameter",
    "envelope_reset_parameter": "envelope-reset parameter",
    "live_multiplier": "live multiplier",
    "harvest_threshold": "threshold",
    "harvest_loop": "loop bound",
    "harvest_parameter": "harvest parameter",
}
_CHOICE_TEXT = {
    "route_class": (
        "Which route class is this state? "
        "The chair table label on this state is a fact, not the decision. "
        "The option you return is the unique highest probability. "
    ),
    "route_reason": "Which route reason is this state? The option you return is the unique highest probability. ",
    "exit_class": (
        "Which exit class is this state? time_stop is one of the options. "
        "The option you return is the unique highest probability. "
    ),
    "envelope_phase": "Which envelope phase is this state? The option you return is the unique highest probability. ",
    "envelope_reset": "Which reset clock is this state? The option you return is the unique highest probability. ",
    "harvest_component": "Which harvest component is this state? The option you return is the unique highest probability. ",
}
_CHOICE_CRITERIA = {
    "route_class": _ROUTE_CRITERIA,
    "route_reason": _REASON_CRITERIA,
    "exit_class": _EXIT_CRITERIA,
    "envelope_phase": _PHASE_CRITERIA,
    "envelope_reset": _RESET_CRITERIA,
    "harvest_component": _COMPONENT_CRITERIA,
}


@dataclass(frozen=True)
class RouteIdentity:
    """Jesse-route pattern: sleeve × symbol × TF as one research unit."""

    sleeve: str
    symbol: str
    tf_route: str
    route_id: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PitFeatureContract:
    """Qlib / Feast point-in-time rule. Leak on live_intent is a code raise."""

    feature_as_of: dict[str, str | None]
    leakage_keys: tuple[str, ...]
    honest: bool | None
    assembled: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "feature_as_of": dict(self.feature_as_of),
            "leakage_keys": list(self.leakage_keys),
            "honest": self.honest,
            "assembled": self.assembled,
        }


@dataclass(frozen=True)
class ProtectionAtom:
    """Freqtrade-shaped named wall. The integer count stays on the tape."""

    kind: str
    fired: bool | None
    remaining: int | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChallengeEnvelopeSnapshot:
    """Firm-true walls. No OSS peer. Compose Nautilus/Lean *shape* + our MC."""

    login: int | None
    ns: str | None
    magic: int | None
    pass_line: float | None
    daily_loss_rule: str | None
    maxdd_rule: str | None
    reset_clock: str | None
    phase: str | None
    quarantine_login: int
    assembled: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FillRealism:
    """hftbacktest honesty: a fill is not 'next bar open' unless named so."""

    model: str
    latency_ms: float | None
    cost_complete: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OnlineLabelAtom:
    """River-shaped incremental label. Illegal on live_intent."""

    label: str | None
    R: float | None
    day: str | None
    attached: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HarvestLaw:
    never_vendor: bool = True
    never_place: bool = True
    never_remint: bool = True
    never_flatten: bool = True
    never_invent_news: bool = True
    envelope_walls_stay_integers: bool = True
    live_multiplier_stays_one_until_named: bool = True
    schema_lock: str = SCHEMA_LOCK
    preauth_effects: tuple[str, ...] | None = None
    forbidden_effects: tuple[str, ...] | None = None
    prove_bars: dict[str, Any] | None = None
    envelope_wall_ids: tuple[str, ...] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "never_vendor": self.never_vendor,
            "never_place": self.never_place,
            "never_remint": self.never_remint,
            "never_flatten": self.never_flatten,
            "never_invent_news": self.never_invent_news,
            "envelope_walls_stay_integers": self.envelope_walls_stay_integers,
            "live_multiplier_stays_one_until_named": self.live_multiplier_stays_one_until_named,
            "schema_lock": self.schema_lock,
            "preauth_effects": None if self.preauth_effects is None else list(self.preauth_effects),
            "forbidden_effects": None if self.forbidden_effects is None else list(self.forbidden_effects),
            "prove_bars": None if self.prove_bars is None else dict(self.prove_bars),
            "envelope_wall_ids": None if self.envelope_wall_ids is None else list(self.envelope_wall_ids),
        }


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
    """Drop limit keys and banned dollar tokens before the ask."""

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
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return _scrub_text(str(value))


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
    cleaned = {str(key): _scrub_text(str(value)) for key, value in criteria.items() if not _limit_key(str(key))}
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


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "This ask does not transmit an order."
    )


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on these facts. A score may sit between them."""

    found: list[float] = []
    for key, value in dict(facts or {}).items():
        if _limit_key(str(key)):
            continue
        number = _finite(value)
        if number is not None:
            found.append(number)
    if not found:
        return [str(item) for item in _BETWEEN]
    return [format(number, ".10g") for number in sorted(set(found))]


def _questions(names: Sequence[str], levels: Sequence[str]) -> dict[str, Any]:
    """One pack. Every block is a noul, a choice, or a score."""

    wanted = tuple(str(name) for name in names)
    known = {row[0]: row for row in _SPEC}
    pack: dict[str, Any] = {}
    for name in wanted:
        row = known.get(name)
        if row is None:
            continue
        kind = row[1]
        if kind == "noul":
            text, yes, no = _NOUL_TEXT[name]
            pack.update(_noul_question(name, f"{text} {_UNSET}", yes, no))
        elif kind == "choice":
            pack.update(
                _choice_question(
                    name,
                    f"{_CHOICE_TEXT[name]}{_UNSET}",
                    _CHOICE_CRITERIA[name],
                )
            )
        else:
            pack.update(_score_question(name, _score_text(_SCORE_NOUN[name]), levels))
    return pack


def _usable(questions: Mapping[str, Any]) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for qid, block in questions.items():
        if _limit_key(str(qid)) or not isinstance(block, dict):
            continue
        if block.get("type") not in _ALLOWED_TYPES:
            continue
        kept[str(qid)] = block
    return kept


def _book(base: Mapping[str, Any] | None, facts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    body = dict(base or {})
    body.pop("prior_outcomes", None)
    for key, value in dict(facts or {}).items():
        body[str(key)] = value
    body.setdefault("model", MODEL)
    body.setdefault("namespace", CHALLENGE_NS)
    body.setdefault("login", CHALLENGE_LOGIN)
    body.setdefault("magic", CHALLENGE_MAGIC)
    return body


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


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    asked = _usable(questions)
    _attach_priors(payload, asked)
    if not asked:
        return {"error": "empty", "answers": {}, "state": payload, "model": MODEL}
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            payload,
            questions=asked,
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


def _run(state: Mapping[str, Any], names: Sequence[str], levels: Sequence[str]) -> dict[str, Any]:
    questions = _questions(names, levels)
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    wanted = set(str(name) for name in names)
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field_name, kind, order in _SPEC:
        if field_name not in wanted:
            continue
        block = answers.get(field_name)
        value = _pull(block, kind, order)
        out[field_name] = value
        rows.append((field_name, value, _why(block, value, order, error)))
    posted = asked.get("state") if isinstance(asked.get("state"), Mapping) else {}
    _remember(posted, rows)
    return out


def _route_view(tf_route: str, decisions: Mapping[str, Any]) -> dict[str, Any]:
    choice = decisions.get("route_class")
    if choice not in _ROUTE_ORDER:
        choice = None
    reason = decisions.get("route_reason")
    if reason not in _REASON_ORDER:
        reason = None
    return {
        "decidable": decisions.get("route_decidable"),
        "choice": choice,
        "moved": decisions.get("route_moved"),
        "abstain": decisions.get("route_abstain"),
        "tf_route": tf_route,
        "left_unknown": decisions.get("route_left_unknown"),
        "house_hard_off": decisions.get("route_house_hard_off"),
        "chair_named_table": decisions.get("route_chair_named"),
        "reason": reason,
        "parameter": decisions.get("route_class_parameter"),
        "live_multiplier": decisions.get("live_multiplier"),
        "threshold": decisions.get("harvest_threshold"),
        "loop_bound": decisions.get("harvest_loop"),
        "harvest_parameter": decisions.get("harvest_parameter"),
    }


def _fill_view(fill: Mapping[str, Any] | None, decisions: Mapping[str, Any]) -> dict[str, Any]:
    raw = dict(fill or {})
    model = raw.get("model")
    complete = raw.get("cost_complete")
    return {
        "decidable": decisions.get("fill_decidable"),
        "score": decisions.get("fill_realism"),
        "moved": decisions.get("fill_moved"),
        "abstain": decisions.get("fill_abstain"),
        "model": None if model is None else str(model),
        "cost_complete": None if complete is None else bool(complete),
        "parameter": decisions.get("fill_realism_parameter"),
        "threshold": decisions.get("harvest_threshold"),
        "loop_bound": decisions.get("harvest_loop"),
        "harvest_parameter": decisions.get("harvest_parameter"),
    }


def _noul_view(
    decisions: Mapping[str, Any],
    *,
    noul_key: str,
    decidable_key: str,
    abstain_key: str,
    moved_key: str,
    parameter_key: str,
) -> dict[str, Any]:
    return {
        "decidable": decisions.get(decidable_key),
        "noul": decisions.get(noul_key),
        "moved": decisions.get(moved_key),
        "abstain": decisions.get(abstain_key),
        "parameter": decisions.get(parameter_key),
        "threshold": decisions.get("harvest_threshold"),
        "loop_bound": decisions.get("harvest_loop"),
        "harvest_parameter": decisions.get("harvest_parameter"),
    }


def _picked(value: Any, order: tuple[str, ...]) -> str | None:
    if value not in order:
        return None
    return str(value)


def _lock_names() -> dict[str, Any]:
    """Process-lock catalogs when that module is present. A miss stays missing."""

    try:
        from .process_lock import (
            ENVELOPE_WALL_IDS,
            FORBIDDEN_AUTO_EFFECTS,
            PREAUTH_EFFECTS,
            PROVE_BARS_FLUID_SIZE,
        )
    except Exception:
        return {
            "envelope_wall_ids": None,
            "preauth_effects": None,
            "forbidden_effects": None,
            "prove_bars": None,
        }

    def _as_tuple(values: Any) -> tuple[str, ...] | None:
        if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple, set, frozenset)):
            return None
        return tuple(sorted(str(item) for item in values))

    prove = dict(PROVE_BARS_FLUID_SIZE) if isinstance(PROVE_BARS_FLUID_SIZE, dict) else None
    return {
        "envelope_wall_ids": _as_tuple(ENVELOPE_WALL_IDS),
        "preauth_effects": _as_tuple(PREAUTH_EFFECTS),
        "forbidden_effects": _as_tuple(FORBIDDEN_AUTO_EFFECTS),
        "prove_bars": prove,
    }


def _law() -> HarvestLaw:
    names = _lock_names()
    return HarvestLaw(
        preauth_effects=names["preauth_effects"],
        forbidden_effects=names["forbidden_effects"],
        prove_bars=names["prove_bars"],
        envelope_wall_ids=names["envelope_wall_ids"],
    )


def _reject_expost(payload: Mapping[str, Any] | None, clock: str) -> list[str]:
    if not payload:
        return []
    try:
        from .gold_state import reject_expost
    except Exception:
        reject_expost = None
    if reject_expost is not None:
        found = reject_expost(payload, clock)
        return [str(item) for item in found] if found else []
    return sorted(str(key) for key in _EXPOST_FALLBACK if payload.get(key) is not None)


def _parse_iso(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def route_symbol(symbol: str) -> str:
    """Normalize a route symbol. Empty stays empty — never default to XAU."""
    raw = (symbol or "").strip().upper().replace("/", "").replace(".", "_")
    if not raw:
        return ""
    aliases = {
        "XAU": "XAUUSD",
        "GOLD": "XAUUSD",
        "US30_CASH": "US30",
        "US30CASH": "US30",
        "UK100_CASH": "UK100",
        "UK100CASH": "UK100",
        "BTC": "BTCUSD",
        "ETH": "ETHUSD",
    }
    return aliases.get(raw, raw)


def _is_xau_symbol(symbol: str) -> bool:
    return route_symbol(symbol) in XAU_SYMBOLS or route_symbol(symbol) == "XAUUSD"


def _is_us30_symbol(symbol: str) -> bool:
    return route_symbol(symbol) == "US30" or route_symbol(symbol).startswith("US30")


def _table_label(symbol: str) -> str | None:
    """Chair-table fact. Absent from the table stays absent."""

    mapped = CHAIR_ROUTE_CLASS_TABLE.get(route_symbol(symbol))
    if mapped in ROUTE_CLASS_CHOICES:
        return str(mapped)
    return None


def chair_route_class_for(symbol: str) -> str | None:
    """Route class for this symbol. The choice is the return. A miss stays unset."""

    choice = choice_route_class(symbol, "").get("choice")
    if choice not in _ROUTE_ORDER:
        return None
    return str(choice)


def allowed_route_classes(symbol: str) -> frozenset[str]:
    """Legal choice menu. Menu building does not post."""

    if _is_xau_symbol(symbol):
        return frozenset({"metal", "multi"})
    mapped = _table_label(symbol)
    if mapped is None:
        return frozenset({"unknown"})
    return frozenset({mapped})


def choice_route_class(symbol: str, tf_route: str) -> dict[str, Any]:
    """Route-class Choice for this symbol. The table on the ask is a fact.

    Live multiplier, threshold, loop bound, and the route parameter are the
    scores on this same ask. An empty answer, a tie, or an error leaves the
    choice unset.
    """

    sym = route_symbol(symbol)
    tf = tf_route if tf_route in TF_ROUTES else str(tf_route or "")
    book = _book(
        {},
        {
            "symbol": sym,
            "tf_route": tf,
            "chair_table_label": _table_label(sym),
            "unknown_until_landed": sym in CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED,
            "is_xau": _is_xau_symbol(sym),
            "is_us30": _is_us30_symbol(sym),
        },
    )
    try:
        decisions = _run(book, _ROUTE_FIELDS, _levels({}))
    except Exception:
        decisions = {}
    return _route_view(tf, decisions)


def score_fill_realism(fill: Mapping[str, Any] | None) -> dict[str, Any]:
    """Fill-realism score for this fill. The model name is a fact.

    An empty score or an error leaves the score unset.
    """

    raw = dict(fill or {})
    book = _book(
        {},
        {
            "model_name": None if raw.get("model") is None else str(raw.get("model")),
            "cost_named": None if raw.get("cost_complete") is None else bool(raw.get("cost_complete")),
            "latency_ms": _finite(raw.get("latency_ms")),
        },
    )
    try:
        decisions = _run(book, _FILL_FIELDS, _levels({"latency_ms": raw.get("latency_ms")}))
    except Exception:
        decisions = {}
    return _fill_view(raw, decisions)


def noul_cost_complete(fill: Mapping[str, Any] | None) -> dict[str, Any]:
    """Cost-complete noul for this fill. A miss stays unset."""

    raw = dict(fill or {})
    book = _book(
        {},
        {
            "model_name": None if raw.get("model") is None else str(raw.get("model")),
            "cost_named": None if raw.get("cost_complete") is None else bool(raw.get("cost_complete")),
        },
    )
    try:
        decisions = _run(book, _COST_FIELDS, _levels({}))
    except Exception:
        decisions = {}
    return _noul_view(
        decisions,
        noul_key="cost_complete",
        decidable_key="cost_decidable",
        abstain_key="cost_abstain",
        moved_key="cost_moved",
        parameter_key="cost_complete_parameter",
    )


def infer_tf_route(state: Mapping[str, Any]) -> str:
    tfs = state.get("timeframes") or {}
    has_m15 = bool(tfs.get("m15"))
    has_h4 = bool(tfs.get("h4"))
    has_d1 = bool(tfs.get("d1"))
    if has_m15 and has_h4:
        return "multi_m15_h4"
    if has_m15:
        return "M15"
    if has_h4:
        return "H4"
    if has_d1:
        return "D1"
    return "unknown"


def route_from_state(state: Mapping[str, Any]) -> RouteIdentity:
    identity = state.get("identity") or {}
    sleeve = str(identity.get("sleeve") or "")
    symbol = str(identity.get("symbol") or "")
    tf_route = infer_tf_route(state)
    route_id = f"{sleeve}|{symbol}|{tf_route}" if sleeve and symbol else f"|{symbol}|{tf_route}"
    return RouteIdentity(sleeve=sleeve, symbol=symbol, tf_route=tf_route, route_id=route_id)


def pit_from_state(
    state: Mapping[str, Any],
    feature_as_of: Mapping[str, Any] | None = None,
) -> PitFeatureContract:
    """Point-in-time stamps and leak keys. Honesty is not decided here."""

    feats = state.get("sleeve_features") or {}
    named = [k for k, v in feats.items() if v is not None and k not in PIT_SKIP_KEYS]
    as_of_map: dict[str, str | None] = {}
    supplied = dict(feature_as_of or {})
    for key in named:
        raw = supplied.get(key)
        as_of_map[key] = str(raw) if raw else None
    for key, raw in supplied.items():
        if key not in as_of_map:
            as_of_map[key] = str(raw) if raw else None

    clock = (state.get("clock") or {}).get("as_of_utc")
    decision = _parse_iso(clock)
    leaked: list[str] = []
    for key, stamp in as_of_map.items():
        if stamp is None:
            continue
        feat_dt = _parse_iso(stamp)
        if feat_dt is None or decision is None:
            continue
        if feat_dt > decision:
            leaked.append(key)
    assembled = bool(named) or bool(supplied)
    return PitFeatureContract(
        feature_as_of=as_of_map,
        leakage_keys=tuple(sorted(leaked)),
        honest=None,
        assembled=assembled,
    )


def feature_as_of_from_books(
    books: Mapping[str, Sequence[Any]] | None,
    as_of_utc: datetime,
    feats: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Stamp M15-derived features with the last closed bar UTC. Never invent bars."""

    m15 = list((books or {}).get("m15") or [])
    if not m15:
        return {}
    try:
        from .bars import last_closed_at_or_before
    except Exception:
        return {}
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    idx = last_closed_at_or_before(m15, as_of)
    if idx is None:
        return {}
    stamp = m15[idx].utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    keys = PIT_VALUE_KEYS
    if feats is not None:
        keys = tuple(k for k in PIT_VALUE_KEYS if feats.get(k) is not None)
    return {k: stamp for k in keys}


def noul_feature_as_of_honest(pit: Mapping[str, Any] | None) -> dict[str, Any]:
    """Feature as-of noul. Leak keys stay facts. A miss stays unset."""

    raw = dict(pit or {})
    leakage = list(raw.get("leakage_keys") or [])
    book = _book(
        {},
        {
            "assembled": raw.get("assembled"),
            "leakage_keys": leakage,
            "feature_as_of": dict(raw.get("feature_as_of") or {}),
            "supplied_honest": raw.get("honest"),
        },
    )
    try:
        decisions = _run(book, _PIT_FIELDS, _levels({}))
    except Exception:
        decisions = {}
    view = _noul_view(
        decisions,
        noul_key="feature_as_of_honest",
        decidable_key="pit_decidable",
        abstain_key="pit_abstain",
        moved_key="pit_moved",
        parameter_key="feature_as_of_parameter",
    )
    view["leakage_keys"] = leakage
    return view


def protections_from_state(
    state: Mapping[str, Any],
    override: list[Mapping[str, Any]] | None = None,
) -> list[ProtectionAtom]:
    """Protection atoms from tape facts.

    The same-sleeve orig-stop count stays the integer on occupancy.
    The cap is the ``two_stop_cap`` score, not a remainder computed here.
    The one-seat occupancy remainder is the envelope integer.
    """

    if override:
        out: list[ProtectionAtom] = []
        for row in override:
            kind = str(row.get("kind") or "")
            if kind not in PROTECTION_KINDS:
                raise ValueError(f"unknown protection kind: {kind}")
            remaining = row.get("remaining")
            fired = row.get("fired")
            out.append(
                ProtectionAtom(
                    kind=kind,
                    fired=None if fired is None else bool(fired),
                    remaining=int(remaining) if remaining is not None else None,
                )
            )
        return out

    occ = state.get("occupancy") or {}
    gov = state.get("governor") or {}
    atoms: list[ProtectionAtom] = []

    exhausted = occ.get("two_stop_exhausted")
    if exhausted is True or exhausted is False:
        two_stop_fired: bool | None = bool(exhausted)
    else:
        two_stop_fired = None
    atoms.append(ProtectionAtom(kind="two_stop", fired=two_stop_fired, remaining=None))

    open_n = occ.get("symbol_open")
    if open_n is None:
        atoms.append(ProtectionAtom(kind="occupancy", fired=None, remaining=None))
    else:
        count = int(open_n)
        atoms.append(
            ProtectionAtom(
                kind="occupancy",
                fired=count > 0,
                remaining=max(0, 1 - count),
            )
        )

    cluster = occ.get("cluster_placed_today")
    atoms.append(
        ProtectionAtom(
            kind="cluster",
            fired=None if cluster is None else bool(cluster),
            remaining=None,
        )
    )

    allow_new = gov.get("allow_new")
    if allow_new is None:
        maxdd_fired: bool | None = None
    else:
        maxdd_fired = allow_new is False
    atoms.append(ProtectionAtom(kind="maxdd", fired=maxdd_fired, remaining=None))
    return atoms


def _envelope_facts(
    state: Mapping[str, Any],
    override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Identity facts. Phase and reset are not filled from a constant."""

    identity = state.get("identity") or {}
    origin = str(identity.get("origin_organism") or "")
    challenge = origin == "f5_challenge"
    proposed_phase: str | None = None
    proposed_reset: str | None = None
    if override:
        if override.get("phase") is not None:
            proposed_phase = str(override.get("phase"))
            if proposed_phase not in ENVELOPE_PHASES:
                raise ValueError(f"unknown envelope phase: {proposed_phase}")
        maxdd = override.get("maxdd_rule")
        if override.get("reset_clock") is not None:
            proposed_reset = str(override.get("reset_clock"))
            if proposed_reset not in RESET_CLOCKS:
                raise ValueError(f"unknown reset_clock: {proposed_reset}")
        if maxdd is not None and maxdd not in MAXDD_RULES:
            raise ValueError(f"unknown maxdd_rule: {maxdd}")
        login = int(override["login"]) if override.get("login") is not None else (
            CHALLENGE_LOGIN if challenge else None
        )
        ns = str(override["ns"]) if override.get("ns") is not None else (
            CHALLENGE_NS if challenge else None
        )
        magic = int(override["magic"]) if override.get("magic") is not None else (
            CHALLENGE_MAGIC if challenge else None
        )
        pass_line = float(override["pass_line"]) if override.get("pass_line") is not None else None
        daily = str(override["daily_loss_rule"]) if override.get("daily_loss_rule") else None
        return {
            "login": login,
            "ns": ns,
            "magic": magic,
            "pass_line": pass_line,
            "daily_loss_rule": daily,
            "maxdd_rule": None if maxdd is None else str(maxdd),
            "proposed_phase": proposed_phase,
            "proposed_reset": proposed_reset,
            "quarantine_login": QUARANTINE_LOGIN,
            "assembled": True,
        }
    if not challenge:
        return {
            "login": None,
            "ns": None,
            "magic": None,
            "pass_line": None,
            "daily_loss_rule": None,
            "maxdd_rule": None,
            "proposed_phase": None,
            "proposed_reset": None,
            "quarantine_login": QUARANTINE_LOGIN,
            "assembled": False,
        }
    return {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "pass_line": None,
        "daily_loss_rule": None,
        "maxdd_rule": None,
        "proposed_phase": None,
        "proposed_reset": None,
        "quarantine_login": QUARANTINE_LOGIN,
        "assembled": True,
    }


def _snapshot(facts: Mapping[str, Any], decisions: Mapping[str, Any]) -> ChallengeEnvelopeSnapshot:
    return ChallengeEnvelopeSnapshot(
        login=facts.get("login"),
        ns=facts.get("ns"),
        magic=facts.get("magic"),
        pass_line=facts.get("pass_line"),
        daily_loss_rule=facts.get("daily_loss_rule"),
        maxdd_rule=facts.get("maxdd_rule"),
        reset_clock=_picked(decisions.get("envelope_reset"), _RESET_ORDER),
        phase=_picked(decisions.get("envelope_phase"), _PHASE_ORDER),
        quarantine_login=QUARANTINE_LOGIN,
        assembled=bool(facts.get("assembled")),
    )


def envelope_from_state(
    state: Mapping[str, Any],
    override: Mapping[str, Any] | None = None,
) -> ChallengeEnvelopeSnapshot:
    """Envelope snapshot. Phase and reset are the return. A miss stays unset."""

    facts = _envelope_facts(state, override)
    book = _book(
        state,
        {
            "proposed_phase": facts.get("proposed_phase"),
            "proposed_reset": facts.get("proposed_reset"),
            "envelope_assembled": facts.get("assembled"),
            "quarantine_login": QUARANTINE_LOGIN,
        },
    )
    try:
        decisions = _run(book, _ENVELOPE_FIELDS, _levels({}))
    except Exception:
        decisions = {}
    return _snapshot(facts, decisions)


def fill_from_state(
    state: Mapping[str, Any],
    override: Mapping[str, Any] | None = None,
) -> FillRealism:
    cost = state.get("cost") or {}
    source = str(cost.get("source") or "unassembled")
    model = "unknown"
    if override and override.get("model"):
        model = str(override["model"])
    elif source == "tick":
        model = "tick"
    elif source in FILL_MODELS:
        model = source
    if model not in FILL_MODELS:
        raise ValueError(f"unknown fill model: {model}")
    latency = None
    if override and override.get("latency_ms") is not None:
        latency = float(override["latency_ms"])
    named = (
        cost.get("spread_r_of_stop") is not None
        or cost.get("cost_r") is not None
        or (
            cost.get("spread_r") is not None
            and cost.get("expected_slippage_r") is not None
            and cost.get("commission_r") is not None
        )
    )
    return FillRealism(model=model, latency_ms=latency, cost_complete=bool(named))


def learn_from_payload(
    state: Mapping[str, Any],
    learn: Mapping[str, Any] | None,
) -> OnlineLabelAtom:
    clock = str(state.get("as_of_clock") or "")
    if clock != "as_of_close_illegal_for_live":
        if learn and any(learn.get(k) is not None for k in ("label", "R", "exit_class", "close_reason")):
            raise ValueError("OnlineLabelAtom illegal except on as_of_close_illegal_for_live")
        return OnlineLabelAtom(label=None, R=None, day=None, attached=False)
    payload = dict(learn or {})
    label = payload.get("label") or payload.get("exit_class")
    if label is not None:
        label = str(label)
        if label not in LEARN_LABELS:
            raise ValueError(f"unknown learn label: {label}")
    r_val = payload.get("R")
    day = payload.get("day") or (state.get("identity") or {}).get("decision_day")
    return OnlineLabelAtom(
        label=label,
        R=float(r_val) if r_val is not None else None,
        day=str(day) if day else None,
        attached=bool(label or r_val is not None),
    )


def _refuse_invented_news(extra: Mapping[str, Any] | None) -> None:
    if not extra:
        return
    forbidden = ("NEWS_PROTOCOL", "invent_high", "invented_high", "news_protocol")
    for key in forbidden:
        if extra.get(key):
            raise ValueError("invented news / NEWS_PROTOCOL forbidden on harvest attach")
    news = extra.get("news")
    if news:
        raise ValueError("harvest must not invent news.events; empty spine stays empty")
    events = extra.get("events")
    if events:
        raise ValueError("harvest must not invent news.events; empty spine stays empty")


def _json_copy(state: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(state, default=str))


def _returns(decisions: Mapping[str, Any]) -> dict[str, Any]:
    return {name: decisions.get(name) for name in _ALL_FIELDS}


def attach_harvest_blocks(
    state: Mapping[str, Any],
    *,
    extra: Mapping[str, Any] | None = None,
    feature_as_of: Mapping[str, Any] | None = None,
    protection: list[Mapping[str, Any]] | None = None,
    envelope: Mapping[str, Any] | None = None,
    fill: Mapping[str, Any] | None = None,
    learn: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach harvest extras. Every decision on this state is one return.

    Does not mutate ``news.events``. Does not place. A miss leaves that
    field unset.
    """

    extra = extra or {}
    _refuse_invented_news(extra)
    clock = str(state.get("as_of_clock") or "")
    leaked = _reject_expost(extra, clock)
    leaked += _reject_expost(learn or {}, clock)
    leaked += _reject_expost(fill or {}, clock)
    leaked = sorted(set(leaked))
    if leaked and clock == "live_intent":
        raise ValueError(f"EXPOST keys illegal on live_intent: {leaked}")
    if clock == "live_intent" and learn:
        raise ValueError("OnlineLabelAtom illegal on live_intent")
    news = state.get("news") or {}
    if extra.get("high_in_f5_window") is True and news.get("spine_empty"):
        raise ValueError("empty spine stays empty; cannot invent HIGH")

    out = _json_copy(state)
    route = route_from_state(out)
    pit = pit_from_state(out, feature_as_of)
    atoms = protections_from_state(out, protection)
    env_facts = _envelope_facts(out, envelope)
    fill_atom = fill_from_state(out, fill)
    label = learn_from_payload(out, learn)
    identity = dict(out.get("identity") or {})
    identity.setdefault("tf_route", route.tf_route)
    identity.setdefault("route_id", route.route_id)
    out["identity"] = identity

    occ = out.get("occupancy") or {}
    levels = _levels(
        {
            "latency_ms": fill_atom.latency_ms,
            "same_sleeve_orig_stops_utc_day": occ.get("same_sleeve_orig_stops_utc_day"),
            "symbol_open": occ.get("symbol_open"),
            "R": label.R,
        }
    )
    book = _book(
        out,
        {
            "route": route.as_dict(),
            "pit": pit.as_dict(),
            "protection": [atom.as_dict() for atom in atoms],
            "fill_fact": fill_atom.as_dict(),
            "learn_fact": label.as_dict(),
            "chair_table_label": _table_label(route.symbol),
            "unknown_until_landed": route_symbol(route.symbol) in CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED,
            "proposed_phase": env_facts.get("proposed_phase"),
            "proposed_reset": env_facts.get("proposed_reset"),
            "envelope_assembled": env_facts.get("assembled"),
            "same_sleeve_orig_stops_utc_day": occ.get("same_sleeve_orig_stops_utc_day"),
        },
    )
    try:
        decisions = _run(book, _ALL_FIELDS, levels)
    except Exception:
        decisions = {}
    env = _snapshot(env_facts, decisions)
    route_class = _route_view(route.tf_route, decisions)
    fill_realism = _fill_view(fill_atom.as_dict(), decisions)
    law = _law()

    completeness = dict(out.get("completeness") or {})
    honest = decisions.get("feature_as_of_honest")
    if honest is True or honest is False or isinstance(honest, float):
        completeness["pit"] = honest
    else:
        completeness["pit"] = None
    completeness["envelope"] = bool(env.assembled)
    completeness["harvest"] = True
    if pit.leakage_keys:
        completeness["pit_leakage_keys"] = list(pit.leakage_keys)
    if leaked:
        completeness["expost_rejected"] = sorted(
            set(list(completeness.get("expost_rejected") or []) + leaked)
        )
    out["completeness"] = completeness

    out["harvest"] = {
        "schema": SCHEMA_EXTRAS,
        "law": law.as_dict(),
        "route": route.as_dict(),
        "pit": pit.as_dict(),
        "protection": [atom.as_dict() for atom in atoms],
        "envelope": env.as_dict(),
        "fill": fill_atom.as_dict(),
        "fill_realism": fill_realism,
        "route_class": route_class,
        "learn": label.as_dict(),
        "returns": _returns(decisions),
        "feature_as_of_honest": decisions.get("feature_as_of_honest"),
        "would_be_nth_stop": decisions.get("would_be_nth_stop"),
        "cost_complete": decisions.get("cost_complete"),
        "instrument_known": decisions.get("instrument_known"),
        "protection_still_earns": decisions.get("protection_still_earns"),
        "wall_pressure": decisions.get("wall_pressure"),
        "paper_live_parity": decisions.get("paper_live_parity"),
        "exit_class": _picked(decisions.get("exit_class"), _EXIT_ORDER),
        "two_stop_cap": decisions.get("two_stop_cap"),
        "live_multiplier": decisions.get("live_multiplier"),
        "chair_named": decisions.get("chair_named"),
        "proposed_questions": {key: value["primitive"] for key, value in PROPOSED_QUESTIONS.items()},
    }
    return out


def load_survey(path: Path | None = None) -> dict[str, Any]:
    payload = json.loads((path or SURVEY_PATH).read_text(encoding="utf-8"))
    if payload.get("schema") != "gtos.judgment.oss_harvest.survey.v0":
        raise ValueError("survey schema mismatch")
    repos = payload.get("repos") or []
    for row in repos:
        missing = [key for key in REQUIRED_SURVEY_FIELDS if key not in row]
        if missing:
            raise ValueError(f"survey row missing {missing}: {row}")
    return payload


def catalog_repos(*, classes: frozenset[str] | None = None) -> list[dict[str, Any]]:
    rows = list(load_survey().get("repos") or [])
    if classes is None:
        return rows
    return [row for row in rows if row.get("class") in classes]


def catalog_reject_chat_llm() -> list[str]:
    return [
        row["full_name"]
        for row in catalog_repos(classes=frozenset({"reject_chat_llm", "reject_place_path"}))
    ]

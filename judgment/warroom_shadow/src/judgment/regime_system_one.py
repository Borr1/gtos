"""S14 System One question pack + cache. No network by default.

One call: regime_type (Choice) + regime_change_likely (Noul) + strategy_viable (Noul).
Questions cannot see sibling answers. Cache key = sha256(bucket state).

A live TypeSafe call is **not** made from this module. Historical prove uses
injected / cached answers. An optional offline stub is explicitly labeled and
never claims to be jev-1.13.0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .regime_buckets import REGIME_TYPE_OPTIONS, RegimeBucketState
from .regime_compose import RegimeAnswers, parse_regime_answers
from .veto import assert_answers_have_no_place_path, refuse_raw_tick_dump_to_jev

MODEL_NAME = "jev-1.13.0"

REGIME_TYPE_CRITERIA = {
    "trend_up": "Sustained upward persistence; price/levels above baseline",
    "trend_down": "Sustained downward persistence; price/levels below baseline",
    "range": "Oscillating; mixed persistence; no clear bias",
    "chop": "Erratic; elevated vol; no follow-through",
    "unclear": "Conflicting buckets; do not force a regime",
}

QUESTION_PACK = {
    "regime_type": {
        "type": "choice",
        "instructions": (
            "Classify the current market regime from the bucketed features only. "
            "Do not invent missing buckets. Prefer unclear when features conflict."
        ),
        "criteria": dict(REGIME_TYPE_CRITERIA),
    },
    "regime_change_likely": {
        "type": "noul",
        "instructions": (
            "Given the bucketed features, is a regime transition likely happening "
            "right now? Weight atr_expansion, vol_vs_baseline, and trend_persistence "
            "shifts as transition signals."
        ),
    },
    "strategy_viable": {
        "type": "noul",
        "instructions": (
            "Is sleeve {identity.sleeve} strategy family compatible with this regime? "
            "Directional sleeves suffer in chop/range. Name the strategy family only — "
            "never a broker verb (no place, remint, flatten, order_send)."
        ),
    },
}

S14_QUESTION_IDS = ("regime_type", "regime_change_likely", "strategy_viable")


def build_question_pack(sleeve: str | None = None) -> dict[str, Any]:
    pack = json.loads(json.dumps(QUESTION_PACK))
    if sleeve:
        pack["strategy_viable"]["instructions"] = pack["strategy_viable"]["instructions"].replace(
            "{identity.sleeve}", str(sleeve)
        )
    return pack


class RegimeAnswerCache:
    """SHA-256(bucket_state) → typed answers. Replay-safe for Challenge tape."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def get(self, cache_key: str) -> dict[str, Any] | None:
        row = self._rows.get(cache_key)
        return dict(row) if row is not None else None

    def put(self, cache_key: str, answers: Mapping[str, Any]) -> None:
        self._rows[cache_key] = dict(answers)

    def load_json(self, path: Path | str) -> int:
        target = Path(path)
        if not target.is_file():
            return 0
        doc = json.loads(target.read_text(encoding="utf-8"))
        rows = doc.get("rows") if isinstance(doc, Mapping) else None
        if not isinstance(rows, Mapping):
            return 0
        n = 0
        for key, payload in rows.items():
            if isinstance(payload, Mapping):
                self._rows[str(key)] = dict(payload)
                n += 1
        return n

    def dump_json(self, path: Path | str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps({"schema": "gtos.s14.answer_cache.v1", "rows": self._rows}, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

    def __len__(self) -> int:
        return len(self._rows)


@dataclass(frozen=True)
class SystemOneResult:
    answers: RegimeAnswers | None
    raw: dict[str, Any]
    cache_hit: bool
    cache_key: str
    source: str
    question_ids: tuple[str, ...]
    model: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "answers": None if self.answers is None else self.answers.as_dict(),
            "raw": dict(self.raw),
            "cache_hit": self.cache_hit,
            "cache_key": self.cache_key,
            "source": self.source,
            "question_ids": list(self.question_ids),
            "model": self.model,
            "single_call": True,
        }


def call_system_one(
    state: RegimeBucketState,
    *,
    cache: RegimeAnswerCache | None = None,
    injected: Mapping[str, Any] | None = None,
    offline_stub: Callable[[RegimeBucketState], Mapping[str, Any]] | None = None,
) -> SystemOneResult:
    """One System One *interface* call. Default: cache or injected; no network.

    Never imports mt5 / execution. Never maps a choice to order_send.
    """

    refuse_raw_tick_dump_to_jev(state.jev_state)
    store = cache if cache is not None else RegimeAnswerCache()
    hit = store.get(state.cache_key)
    if hit is not None:
        assert_answers_have_no_place_path(hit)
        parsed = parse_regime_answers(hit, source="cache")
        return SystemOneResult(parsed, dict(hit), True, state.cache_key, "cache", S14_QUESTION_IDS, MODEL_NAME)

    if injected:
        raw = dict(injected)
        assert_answers_have_no_place_path(raw)
        store.put(state.cache_key, raw)
        parsed = parse_regime_answers(raw, source="injected")
        return SystemOneResult(parsed, raw, False, state.cache_key, "injected", S14_QUESTION_IDS, MODEL_NAME)

    if offline_stub is not None:
        raw = dict(offline_stub(state))
        assert_answers_have_no_place_path(raw)
        store.put(state.cache_key, raw)
        parsed = parse_regime_answers(raw, source="offline_stub_not_jev")
        return SystemOneResult(
            parsed, raw, False, state.cache_key, "offline_stub_not_jev", S14_QUESTION_IDS, None
        )

    # Fail closed: no TypeSafe client in this stub. Unclear@equal is non-decidable.
    fallback = {
        "regime_type": {
            "choice": "unclear",
            "confidence": 0.2,
            "probabilities": {opt: 0.2 for opt in REGIME_TYPE_OPTIONS},
        },
        "regime_change_likely": {"noul": 0.5},
        "strategy_viable": {"noul": 0.5},
    }
    parsed = parse_regime_answers(fallback, source="unclear_equal_fallback")
    return SystemOneResult(
        parsed, fallback, False, state.cache_key, "unclear_equal_fallback", S14_QUESTION_IDS, None
    )

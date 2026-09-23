"""The generation-side spread-geometry floor (Session AY, B1800-B1849). DEFAULT-OFF.

WHAT IT IS
----------
`spread_r = spread_price / stop_dist`. A value above the sleeve's limit means the proposed
stop is a small multiple of the round-trip spread — at `spread_r > 1`, narrower than it — so
the trade is paying more to enter than it can lose by being wrong. Session AW measured
4,701 such rows (16.5 %) carrying **49.6 % of the whole B7.5 diagnostic pool's loss**, with a
maximum of 18.856 R, and named it a GENERATOR defect: a stop that narrow should never have
been proposed.

WHY THIS IS NOT A DUPLICATE OF THE GATE THAT ALREADY EXISTS
------------------------------------------------------------
The live book already refuses these trades. It refuses them at the SEND layer, twice:

  * `broker_net_cost_engine.pretrade_cost_refusal_reasons:718-727` — the authoritative
    pre-trade gate, `spread_r > selected_cell_pretrade_max_spread_r` (0.10, or a per-sleeve
    override), reached on every W7 placement because `build_book_trade_params` stamps
    `gtos_vnext_production_execution_path: True`;
  * `book_owner._spread_cost_screen:4232-4270` — a deterministic pre-send mirror of it.

It fires: 136 legs in the read-only 2026-07-25 VPS export's own launcher log, at observed
`spread_r` up to **16.543**.

**Between generation and send, a doomed intent has already been counted.**
`book_engine._running_conviction_override:865-915` builds the day's distinct-firing-sleeve
count from INTENTS, after `precount_intent_filter`'s five drop rules — and the cost screen is
not one of them, because it runs later and needs a tick. `admission.py:1188` then takes
`na = max(na, override)`, **monotone upward**. So a sleeve whose every leg the cost gate will
refuse still raises the day's Kelly-lite multiplier for every sleeve that does place.
Measured on the export: 16 account-days counted a doomed sleeve and **on 3 of them the
multiplier moved, by up to +25.2 % on every unit that day** (`AY_LIVE_SCREEN_EVIDENCE_V1`).

That is the same defect class the D3 repair closed on 2026-07-27 for the metals confluence
gate, and `_running_conviction_override`'s own docstring calls it CORRECTNESS-CRITICAL.
Refusing at generation closes it for this filter, and closes the two lesser costs with it: a
sizing slot spent on a trade that cannot place, and an operator card for a non-event.

THE LIMIT IS THE LIVE GATE'S OWN, WHICH IS THE POINT
-----------------------------------------------------
A sleeve named without an explicit threshold uses **the limit the send gate will apply to
it**, read from the same two config keys the send gate reads. The two layers then agree by
construction rather than by a constant copied into a second place — and when the owner moves
the config, both move together. An explicit `sleeve:0.075` is accepted for the case where the
owner wants generation stricter than the send gate; the reverse (looser than the send gate)
is accepted too and logged as inert, because a floor looser than the authority cannot admit
anything the authority will refuse.

FAIL-CLOSED, AND THAT MATCHES THE AUTHORITY
--------------------------------------------
An opted-in sleeve whose spread cannot be read is REFUSED, not admitted. That is not a
preference: `pretrade_cost_refusal_reasons` already answers the identical question with
`missing_current_quote_spread_or_sl_distance`, a refusal. The pre-send mirror in
`book_owner` fails OPEN, but its own docstring says why — it defers to the authoritative
gate, which does not. A generation-side floor that failed open would be the only layer of
the three that let an unpriceable leg through.

Every refusal — including one caused by a bug in this module — lands in the engine's
`generation_skips` with a precise reason. Silent nulls fall loudly.
"""

from __future__ import annotations

from typing import Any

_HOP: dict[tuple, dict[str, float | None]] = {}


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


def _scores(cache_key: tuple, facts: dict, questions: dict[str, str]) -> dict[str, float | None]:
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    packed = {str(qid): {"type": "score", "instructions": str(text)} for qid, text in questions.items()}
    answers: dict = {}
    returned = None
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import returned_number

        returned = returned_number
        receipt = evaluate(payload, questions=packed, merge_sleeve=False)
    except Exception:
        receipt = None
    if (
        isinstance(receipt, dict)
        and receipt.get("ok") is not False
        and not receipt.get("error")
        and receipt.get("tie") is not True
        and isinstance(receipt.get("answers"), dict)
    ):
        answers = receipt["answers"]
    out = {qid: None if returned is None else _finite(returned(answers.get(qid))) for qid in packed}
    _HOP[cache_key] = dict(out)
    return out

from typing import Mapping

__all__ = [
    "SpreadGeometryFloorError",
    "parse_spread_geometry_floor",
    "resolve_floor_limit",
    "evaluate_intent",
    "SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT",
    "MAX_PLAUSIBLE_LIMIT",
]

#: The fallback when neither the selection nor the config names a limit. Identical to
#: `broker_net_cost_engine`'s own literal default at `:574`, deliberately: if the config key
#: is ever absent, both layers must fall back to the same number or the send gate would
#: refuse what generation admitted.
SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT = 0.10

#: A `spread_r` limit at or above 1.0 permits a stop narrower than the round-trip spread,
#: which is the defect this module exists to prevent. Refused at parse time rather than
#: honoured, because a floor that permits the pathology is worse than no floor: it reads as
#: protection in the launcher's own command line.
MAX_PLAUSIBLE_LIMIT = 1.0


class SpreadGeometryFloorError(ValueError):
    """A malformed `--spread-geometry-floor` selection. Raised at LAUNCH, never per tick.

    Same shape as `FrontierExitSelectionError` and for the same reason: an unparseable
    selection must stop the worker rather than degrade — in silence, at every tick — to a
    book that is not running the floor its operator believes it is running.
    """


def parse_spread_geometry_floor(raw: Any, *, known_sleeves: Any = None) -> dict[str, float | None]:
    """`"a,b:0.075"` -> `{"a": None, "b": 0.075}`. `None`/absent -> `{}` (the default: OFF).

    `None` as a value means "use the limit the send gate will apply to this sleeve", resolved
    per tick by `resolve_floor_limit` so a config edit reaches both layers at once.

    REFUSES, rather than degrading:
      * the empty string — `--tags ""` is falsy at `run_book.py:340` and therefore means ALL
        sleeves, a fail-OPEN this estate has already filed twice. An empty selection here
        would mean the opposite (no sleeves), and two flags whose empty string means opposite
        things is a trap. So neither reading is offered.
      * an unknown sleeve name — `registry.py:144` drops unknown `--tags` silently and the
        book then stands down every tick with a healthy log. A typo must be loud.
      * a limit that is not a positive number below `MAX_PLAUSIBLE_LIMIT`.
      * a sleeve named twice, which would otherwise resolve by dict-update order.
    """
    if raw is None:
        return {}
    if not isinstance(raw, str):
        raise SpreadGeometryFloorError(
            f"--spread-geometry-floor must be a string, got {type(raw).__name__}")
    if not raw.strip():
        raise SpreadGeometryFloorError(
            "--spread-geometry-floor was given an EMPTY selection. It is refused rather "
            "than read as 'all sleeves' or as 'no sleeves': --tags reads its empty string "
            "as ALL (run_book.py:340) and this flag would have to mean NONE, so an empty "
            "string here can only be a mistake. Omit the flag to leave the floor off.")
    known = None
    if known_sleeves is not None:
        known = {str(s) for s in known_sleeves}
    out: dict[str, float | None] = {}
    for chunk in raw.split(","):
        item = chunk.strip()
        if not item:
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor has an empty entry in {raw!r} (a stray comma). "
                "Refused rather than skipped: the operator's list and the book's list must "
                "be the same length.")
        name, sep, limit_s = item.partition(":")
        name = name.strip()
        if not name:
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor entry {item!r} names no sleeve")
        if known is not None and name not in known:
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor names unknown sleeve {name!r}. Known: "
                f"{sorted(known)}. Refused rather than dropped — an unknown tag is dropped "
                "silently elsewhere in this launcher and the result is a book that looks "
                "healthy and is not running what you asked for.")
        if name in out:
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor names {name!r} twice; which limit applies would "
                "be decided by argument order rather than by the operator")
        if not sep:
            out[name] = None
            continue
        try:
            limit = float(limit_s.strip())
        except (TypeError, ValueError):
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor limit for {name!r} is not a number: "
                f"{limit_s!r}") from None
        if not (limit > 0.0):
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor limit for {name!r} must be > 0, got {limit}. "
                "A limit of 0 would refuse every trade on that sleeve.")
        cap = _scores(
            ("spread_cap", name),
            {"sleeve": name, "offered_limit": limit},
            {
                "max_plausible_limit": (
                    "The score you return is the spread_r at or above which this sleeve's "
                    "floor stops being protection. An empty score leaves that cap unset. Do not send."
                ),
            },
        ).get("max_plausible_limit")
        if cap is None:
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor limit for {name!r} has no plausible cap. "
                "Refused rather than compared with a planted cap."
            )
        if limit >= cap:
            raise SpreadGeometryFloorError(
                f"--spread-geometry-floor limit for {name!r} is {limit}, at or above "
                f"{cap}. At a spread_r that high the stop is narrower than the "
                "round-trip spread, which is the exact defect this floor exists to "
                "prevent — a limit there would read as protection and be none.")
        out[name] = limit
    return out


def resolve_floor_limit(
    runtime_cfg: Mapping[str, Any] | None,
    sleeve: str,
    selection: Mapping[str, float | None] | None,
) -> float | None:
    """The `spread_r` limit for one sleeve, or None when the floor does not apply to it.

    Resolution order, and each step is deliberate:
      1. not in the selection -> None. The floor is per-sleeve opt-in; nothing else.
      2. an explicit limit in the selection -> that.
      3. the send gate's own per-sleeve override for this sleeve, then its global limit.
      4. the spread-floor score for this sleeve. An empty score returns 0.0, which refuses the leg.

    Steps 3 and 4 are what make the two layers agree without a copied constant.
    """
    if not selection or sleeve not in selection:
        return None
    explicit = selection.get(sleeve)
    if explicit is not None:
        return float(explicit)
    cfg = runtime_cfg or {}
    by_sleeve = cfg.get("selected_cell_pretrade_max_spread_r_by_sleeve")
    if isinstance(by_sleeve, Mapping) and sleeve in by_sleeve:
        try:
            return float(by_sleeve[sleeve])
        except (TypeError, ValueError):
            pass
    try:
        value = cfg.get("selected_cell_pretrade_max_spread_r")
        if value is not None:
            return float(value)
    except (TypeError, ValueError):
        pass
    asked = _scores(
        ("spread_default", str(sleeve)),
        {"sleeve": str(sleeve)},
        {
            "spread_floor_limit": (
                "The score you return is the spread_r limit for this sleeve when the "
                "selection names no number. An empty score does not pass the leg. Do not send."
            ),
        },
    ).get("spread_floor_limit")
    if asked is None or not (asked > 0.0):
        return 0.0
    return float(asked)


def evaluate_intent(intent: Any, tick: Any, limit: float | None) -> tuple[str | None, dict]:
    """`(refusal_reason_or_None, observation)` for one generated intent.

    `observation` is recorded whether the intent passes or fails — building the spread
    record out of a refusal log is the derive-don't-accumulate trap `book_owner`'s own
    `_record_spread_observation` comment names, and the passing legs are most of the
    distribution.
    """
    obs: dict[str, Any] = {"limit": limit}
    if limit is None:
        return None, obs
    stop = getattr(intent, "stop_dist", None)
    bid = getattr(tick, "bid", None)
    ask = getattr(tick, "ask", None)
    try:
        stop_f = float(stop) if stop is not None else None
        bid_f = float(bid) if bid is not None else None
        ask_f = float(ask) if ask is not None else None
    except (TypeError, ValueError):
        stop_f = bid_f = ask_f = None
    obs.update({"stop_dist": stop_f, "bid": bid_f, "ask": ask_f})
    if stop_f is None or not (stop_f > 0):
        # Not this module's failure to diagnose: `admission.py:1190-1191` already refuses a
        # non-positive stop downstream. Refused here so the intent never reaches the count.
        return f"spread_geometry_floor_nonpositive_stop:{stop_f}", obs
    if bid_f is None or ask_f is None or bid_f <= 0 or ask_f <= 0 or ask_f < bid_f:
        return (
            "spread_geometry_floor_quote_unavailable:"
            f"bid={bid_f}:ask={ask_f} (fail-closed, matching "
            "broker_net_cost_engine's missing_current_quote_spread_or_sl_distance)"
        ), obs
    spread_price = ask_f - bid_f
    spread_r = spread_price / stop_f
    obs.update({"spread_price": spread_price, "spread_r": spread_r})
    if spread_r > float(limit):
        return (
            f"spread_geometry_floor:{spread_r:.4f}>{float(limit):.4f} "
            f"(spread {spread_price:.5f} vs stop {stop_f:.5f}; a stop this narrow is "
            "refused at generation so it never enters the day's conviction count)"
        ), obs
    return None, obs

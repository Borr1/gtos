"""The ratified entry-hour convention, on the live generation path (Session CE, B2314). DEFAULT-OFF.

WHAT IT IS
----------
`phase9/OWNER_DECISION_ENTRY_HOUR.md`, ratified by Borhen 2026-07-30: a sleeve whose decision
bar closes at the daily rollover enters at **the first bar after it — broker hour 01** — rather
than at the close itself. AM measured the rollover premium as a ONE-HOUR spike (16.67x median
spread at broker hour 00, already 1.33x at 01); waiting one hour captures 94-98 % of the
achievable saving and the net frontier peaks at 1-2 h, so AH's original 4 h convention is past
the peak.

The mechanism is a DEFERRAL AT GENERATION, not a change of decision timeframe, and that choice
is forced by the data rather than preferred: an hour-01 fill needs a bar closing at broker
01:00, and on the matched FTMO feed the D1 grid closes at 00:00 and H4 at 00/04/08/12/16/20 --
neither contains one at any date. Only M15 does. So the live book cannot "generate on an
hour-01 bar"; what it can do is generate on the same decision bar it uses today and decline to
emit the intent until the broker clock reaches the target hour. The launcher already polls
every 60 s, and between 00:00 and the next rollover the decision bar does not change, so the
same intent is re-proposed and emitted on the first tick at or after the target. The
idempotency key (`decision_bar_iso`) makes it place exactly once.

WHY IT IS PER-SLEEVE AND SCOPED BY THE SPREAD PROFILE, NOT BY THE TIMEFRAME
---------------------------------------------------------------------------
The ratified decision scopes its cohort as "the FX D1 generating sleeves", and its own note
says *"the armed three sleeves are not in this cohort, so nothing armed changes."* Session CE
measured both halves of that and both have moved (`phase15/receipts/CE_ENTRY_HOUR_V1.json`):

  * `mx_btcusd_d1_donchian_20_breakout` is a D1 sleeve, was ARMED on FTMO on 2026-07-31, and
    fills at broker hour 00 on **318 of 318** trades -- but BTCUSD's median M15 spread is
    identical at every broker hour (premium **x1.000**), because the instrument quotes 24/7 and
    has no rollover. The lever has nothing to work on there, and the measured entry
    displacement is **-0.019 R/trade**. Selecting it would cost a little and save nothing.
  * `sub_mid_dn_revert` is an **H4** sleeve -- outside the ratified cohort entirely -- is ARMED
    on BOTH accounts, and puts **235 of 533** fills at broker hour 00, of which **147** are on
    the five JPY crosses whose hour-00 premium runs **x8.0 (EURJPY) to x19.9 (CHFJPY)**. An H4
    bar closes at the rollover too. Scoping by timeframe missed the only armed sleeve the lever
    can actually help.

So the selection is a per-sleeve map, like `--frontier-exits` and `--spread-geometry-floor`, and
for the same reason: the members are in opposite states and one boolean would arm the harmful
case with the helpful one.

FAIL-OPEN, AND THAT IS THE OPPOSITE OF THE SPREAD FLOOR ON PURPOSE
-------------------------------------------------------------------
`spread_geometry` fails CLOSED because the thing it cannot evaluate is the pathology it exists
to prevent: an unpriceable leg is exactly the leg that must not be placed. This module fails
OPEN -- an unresolvable broker clock emits the intent unchanged, which is precisely what the
book does today. The failure mode here is "the improvement did not apply", not "a rule was
breached", and deferring forever on a dark clock would be a silent disarm of an armed sleeve.
The distinction is stated because both are defensible and picking the wrong one is invisible:
**fail closed when the failure mode is a breach; fail open to the committed contract when it is
a missed improvement.** Every fail-open is counted in the cycle telemetry, never silent.

THE LATENESS INTERACTION, WHICH IS A LAUNCH-TIME REFUSAL
---------------------------------------------------------
`book_owner._entry_too_late` shadows any entry more than `ultimate_book_max_entry_lateness_frac`
(default 0.5) of a bar period past the close -- 12 h for D1, **2 h for H4**, 7.5 min for M15. A
deferral at or past that window would be generated, deferred, emitted, and then silently
SHADOWED as a restart-late chase: the sleeve would stop trading while every log read healthy.
`parse_entry_hour` therefore refuses at LAUNCH any selection whose worst-case deferral reaches
that window for the sleeve's own timeframe. Target 1 on H4 defers the 00:00 bar by 1 h against
a 2 h window and is legal; target 3 on H4 would be 3 h and is refused.
"""

from __future__ import annotations

from typing import Any, Mapping

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
    """One post for this sleeve. The same sleeve does not ask again."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    packed = {
        str(qid): {"type": "score", "instructions": str(text)}
        for qid, text in questions.items()
    }
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
    out = {
        qid: None if returned is None else _finite(returned(answers.get(qid)))
        for qid in packed
    }
    _HOP[cache_key] = dict(out)
    return out

__all__ = [
    "EntryHourSelectionError",
    "parse_entry_hour",
    "deferral_reason",
    "RATIFIED_TARGET_HOUR",
    "TF_MINUTES",
]

#: The ratified convention: the first bar after the rollover hour.
RATIFIED_TARGET_HOUR = 1

#: MT5 timeframe constant -> bar interval in minutes. A local copy of `book_engine._TF_MINUTES`
#: so this module imports nothing from the engine (the engine imports it, not the reverse).
TF_MINUTES = {1: 1, 5: 5, 15: 15, 30: 30, 16385: 60, 16388: 240, 16408: 1440}


class EntryHourSelectionError(ValueError):
    """A malformed `--entry-hour` selection. Raised at LAUNCH, never per tick."""


def parse_entry_hour(
    raw: Any,
    *,
    known_sleeves: Any = None,
    timeframe_of: Mapping[str, Any] | None = None,
    lateness_frac: float | None = None,
) -> dict[str, int]:
    """`"a,b:2"` -> `{"a": 1, "b": 2}`. `None`/absent -> `{}` (the default: OFF).

    A sleeve named without an hour asks for that hour. An empty score refuses the launch.
    `RATIFIED_TARGET_HOUR` stays exported and is not the hour this function fills in.

    REFUSES, rather than degrading:
      * the empty string -- `--tags ""` is falsy at `run_book.py` and therefore means ALL
        sleeves, a fail-OPEN this estate has filed twice. Two flags whose empty string means
        opposite things is a trap, so neither reading is offered.
      * an unknown sleeve name -- `registry.py` drops unknown `--tags` silently and the book
        then stands down every tick with a healthy log. A typo must be loud.
      * an hour outside 0..23, or a non-integer.
      * hour 0, which is the committed behaviour spelled as a change -- an operator who writes
        it believes something is happening and nothing is.
      * a sleeve named twice, which would otherwise resolve by dict-update order.
      * **a target whose worst-case deferral reaches the entry-lateness window for that
        sleeve's timeframe.** This is the refusal that matters: past it the book generates,
        defers, emits, and `_entry_too_late` shadows the entry as a restart-late chase, so the
        sleeve silently stops trading. Checked only when `timeframe_of` is supplied.
    """
    if raw is None:
        return {}
    if not isinstance(raw, str):
        raise EntryHourSelectionError(
            f"--entry-hour must be a string, got {type(raw).__name__}")
    if not raw.strip():
        raise EntryHourSelectionError(
            "--entry-hour was given an EMPTY selection. It is refused rather than read as "
            "'all sleeves' or as 'no sleeves': --tags reads its empty string as ALL and this "
            "flag would have to mean NONE. Omit the flag to leave the convention off.")
    known = {str(s) for s in known_sleeves} if known_sleeves is not None else None
    out: dict[str, int] = {}
    for chunk in raw.split(","):
        item = chunk.strip()
        if not item:
            raise EntryHourSelectionError(
                f"--entry-hour has an empty entry in {raw!r} (a stray comma). Refused rather "
                "than skipped: the operator's list and the book's list must be the same length.")
        name, sep, hour_s = item.partition(":")
        name = name.strip()
        if not name:
            raise EntryHourSelectionError(f"--entry-hour entry {item!r} names no sleeve")
        if known is not None and name not in known:
            raise EntryHourSelectionError(
                f"--entry-hour names unknown sleeve {name!r}. Known: {sorted(known)}. Refused "
                "rather than dropped -- an unknown tag is dropped silently elsewhere in this "
                "launcher and the result is a book that looks healthy and is not running what "
                "you asked for.")
        if name in out:
            raise EntryHourSelectionError(
                f"--entry-hour names {name!r} twice; which hour applies would be decided by "
                "argument order rather than by the operator")
        if not sep:
            asked = _scores(
                ("entry_hour", name),
                {"sleeve": name},
                {
                    "entry_hour": (
                        "The score you return is the broker hour this sleeve waits for "
                        "after its rollover bar. An empty score leaves the hour unset. Do not send."
                    ),
                },
            ).get("entry_hour")
            if asked is None:
                raise EntryHourSelectionError(
                    f"--entry-hour names {name!r} without an hour and the hour score is empty. "
                    "Refused rather than filled with a planted hour."
                )
            hour = int(round(asked))
        else:
            try:
                hour = int(str(hour_s).strip())
            except (TypeError, ValueError):
                raise EntryHourSelectionError(
                    f"--entry-hour target for {name!r} is not an integer: {hour_s!r}") from None
        if not (0 <= hour <= 23):
            raise EntryHourSelectionError(
                f"--entry-hour target for {name!r} is {hour}; broker hours are 0..23")
        if hour == 0:
            raise EntryHourSelectionError(
                f"--entry-hour target for {name!r} is 0, which IS the committed behaviour "
                "(the decision bar's own close). Refused rather than accepted as a no-op: an "
                "operator who writes it believes the entry moved and it has not.")
        if timeframe_of is not None:
            tf = timeframe_of.get(name)
            per = TF_MINUTES.get(tf)
            if per:
                frac = _finite(lateness_frac)
                if frac is None:
                    frac = _scores(
                        ("entry_lateness", name, tf),
                        {"sleeve": name, "timeframe": tf},
                        {
                            "lateness_frac": (
                                "The score you return is the fraction of this bar an entry may "
                                "still be late. An empty score leaves that window unset. Do not send."
                            ),
                        },
                    ).get("lateness_frac")
                if frac is None:
                    raise EntryHourSelectionError(
                        f"--entry-hour lateness window for {name!r} is unset. "
                        "Refused rather than filled with a planted fraction."
                    )
                # Worst case: the decision bar closed at hour 0 and we defer to `hour`.
                worst_min = hour * 60
                window_min = float(frac) * per
                lateness_frac = frac
                if worst_min >= window_min:
                    raise EntryHourSelectionError(
                        f"--entry-hour target {hour} for {name!r} would defer its "
                        f"{'D1' if per == 1440 else ('H4' if per == 240 else f'{per}m')} "
                        f"entry by up to {hour} h, at or past the "
                        f"{window_min / 60:.2f} h entry-lateness window "
                        f"(ultimate_book_max_entry_lateness_frac={lateness_frac} x {per} min). "
                        "`book_owner._entry_too_late` would SHADOW that entry as a "
                        "restart-late chase, so the sleeve would stop trading while every log "
                        "read healthy.")
        out[name] = hour
    return out


def deferral_reason(
    sleeve: str,
    decision_bar_broker: Any,
    now_broker: Any,
    selection: Mapping[str, int] | None,
) -> str | None:
    """`None` == emit this intent. A string == defer it, with the reason, this tick.

    Both timestamps are BROKER WALL CLOCK (naive). The rule, stated so it is checkable:

      defer  <=>  the sleeve is selected
                  AND the decision bar CLOSED at an hour strictly before the target
                  AND `now` is on the SAME broker day as that close
                  AND `now`'s hour is strictly before the target.

    The middle two clauses are what make it well defined for every timeframe. An H4 bar
    closing at broker 04:00 is not deferred toward hour 01 (that would mean 21 hours, or
    yesterday); only the bar that closes at 00:00 is. A bar whose close is already past the
    target emits unchanged, which is the committed behaviour.

    The same-day clause is also the safety bound: the deferral can never exceed
    `target - close_hour` hours, which `parse_entry_hour` has already checked against the
    entry-lateness window. It cannot run into the next day and it cannot accumulate.
    """
    if not selection or sleeve not in selection:
        return None
    target = int(selection[sleeve])
    close_h = getattr(decision_bar_broker, "hour", None)
    now_h = getattr(now_broker, "hour", None)
    if close_h is None or now_h is None:
        return None
    if close_h >= target:
        return None
    if getattr(decision_bar_broker, "date", None) and getattr(now_broker, "date", None):
        if decision_bar_broker.date() != now_broker.date():
            # A different broker day: either we are past the window entirely (emit, the
            # committed behaviour) or the clock is doing something this rule does not model.
            # Either way, do not hold an intent across a day boundary.
            return None
    if now_h >= target:
        return None
    return (f"entry_hour_deferred:{sleeve}:bar_closed_{close_h:02d}:now_{now_h:02d}:"
            f"target_{target:02d} (ratified 2026-07-30 -- the rollover spread premium is a "
            "one-hour spike; this intent is re-proposed every tick and emitted at the target)")

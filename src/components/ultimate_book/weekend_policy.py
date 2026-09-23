"""weekend_policy.py — the redacted_account funded-account weekend prohibition, as a runnable policy.

Pure: stdlib + `src.utils.broker_clock`. NO MT5, NO broker, NO order, no config read. The book
owner calls `flatten_due` on every managed position and `entry_blocked` on every intent; this
module only knows what the clock says.

WHY THIS EXISTS
---------------
`research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json` ->
`firms.redacted_account.rules.weekend_holding`:

    "allowed in Challenge, PROHIBITED on the funded account. Requires a post-pass config
     change that does not exist."

and, from the same artifact's `absent` list, the same fact stated as a gap: *"Any
weekend-flatten policy for redacted_account's funded phase"*. redacted_account is armed and trading a
CHALLENGE today, where weekend holding is legal, so the prohibition binds at the moment the
account PASSES — the one blocker in this programme whose trigger is success. Session BA
(B1900-B1949) prices it and this module is the mechanism.

FTMO carries **no** weekend rule at all (its own captured page; `FIRM_RULES_V1.json` ->
`firms.FTMO.rules` has no `weekend_holding` key), so this policy is per account and
default-OFF everywhere. Arming it on FTMO would pay a measured cost for no rule.

PROVENANCE, STATED HONESTLY. The prohibition's `provenance_kind` is `secondary_audit`
(`.context/05_operations/redacted_account_terms_audit_2026-04-20.md:38`), which grades its own
confidence HIGH and quotes redacted_account's marketing page for the CHALLENGE half — *"Hold your
trades as long as you want, even on weekends"* — while the funded half rests on two
help-centre articles that are not byte-captured in this repository. That is enough to BUILD
against and not enough to arm on: the capture is one owner-side fetch and it is named in the
owner package as the precondition.

THE DEADLINE IS A CALENDAR FACT, AND IT IS MEASURED
---------------------------------------------------
The instant the trading week ends is **broker-local Saturday 00:00**. Measured, not assumed:
across the 18 non-crypto symbols the armed four trade, 99.65-99.93 % of calendar weeks in
`vps-bars-20260727` contain exactly one weekend gap, and the last H4 bar before it OPENS at
broker Friday 20:00 — closing exactly at Saturday 00:00 (Session BA census,
`phase13/receipts/BA_WEEKEND_V1.json` -> `census.symbols.*.modal_last_bar_open_local`).

Both live servers agree on that instant on every day of 2026 (`census.clock`:
`days_of_2026_where_the_two_servers_disagree == 0`), because both resolve to
`America/New_York + 7 h` in `broker_clock.SERVER_CLOCK_RULES`. So a policy measured on the
FTMO bar archive is a policy about the redacted_account account, and that had to be checked rather
than assumed — `broker_clock`'s own header exists because a +3 h guess was wrong for three
weeks of the sealed March window.

`flatten_before_hours` is hours BEFORE that instant. The default 4.0 is one H4 bar, which
makes the live flatten instant exactly the close of the last H4 bar of the week — the same
instant the research cell `m0` exits at, which is what lets the two be compared at all
(`tests/ultimate_book/test_ba_weekend_policy.py` pins the mapping). It fails closed on an
unregistered server: `resolve_rule` raises, and a policy that cannot locate the weekend must
not decide that nothing is due.

CRYPTO IS AN OPEN QUESTION WITH A NUMBER ON IT, NOT A MODELLING CHOICE
----------------------------------------------------------------------
`BTCUSD` and `DASHUSD` carry Saturday and Sunday bars for part of their history and none for
the rest: BTCUSD gapped the weekend in 43.8 % of its weeks and quoted through the other
56.2 %. So "the weekend" is a property of (symbol, week), not of the calendar, and the
`crypto` sleeve's bill depends on which reading the firm means:

    CALENDAR   flat by Saturday 00:00 whatever the instrument does -- 45.9 % of `crypto`
               trades affected
    GRID       flat only when the market actually closes -- 15.5 % affected

Both are priced in `BA_WEEKEND_V1.json`. This module implements CALENDAR (`exempt_sleeves`
empty) because it is the conservative reading of a rule that names no instrument class, and
exposes `exempt_sleeves` so the GRID reading is a selection an owner makes on the evidence
rather than an assumption a module makes silently. Nothing is exempt by default.

THE THREE FAIL-OPEN SHAPES THIS CLOSES
--------------------------------------
Inherited from `--tags` (B359) and closed by `parse_weekend_flat` in the same way
`parse_frontier_exits` closes them:

  * an EMPTY selection is refused, never read as "all sleeves"
  * an UNKNOWN sleeve name is refused, never silently dropped
  * a selection that is a no-op because the named sleeve is not in `--tags` is ALLOWED but
    reported, because a compliance policy armed on a sleeve the book does not trade is the
    operator error that reads as safety

and one that is this module's own: a **negative or zero** `flatten_before_hours` would mean
"flatten after the market has already closed", which cannot execute. Refused.

WHAT THIS POLICY CANNOT DO, AND IT IS H8 ONE LAYER UP
-----------------------------------------------------
The flatten runs inside `book_owner._manage_engine`, which returns early with
`live_broker_authority_false_observe_only` when `ultimate_book_live_broker_authority` is false
(`CLAUDE.md` H8, `book_owner.py:2526`). So shutting that gate does not only leave positions open
and unmanaged — on a funded redacted_account account it also **stops this compliance close from
firing**, and the account holds through the weekend. Nothing here can fix that from inside the
gate; the operating rule is the one H8 already states, with one more reason behind it:
**flatten first, confirm flat, then shut the gate.**
"""
from __future__ import annotations

import datetime as _dt
import pathlib as _pathlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

__all__ = [
    "WeekendPolicy",
    "WeekendPolicySelectionError",
    "DEFAULT_FLATTEN_BEFORE_HOURS",
    "DEFAULT_ENTRY_EMBARGO_HOURS",
    "next_weekend_boundary_utc",
    "parse_weekend_flat",
    "parse_early_close_dates",
    "policy_from_args",
]

#: Field defaults so `OFF = WeekendPolicy()` can be built at import without an ask.
#: The launcher path does not read these. An unnamed hour is a Score.
DEFAULT_FLATTEN_BEFORE_HOURS: float = 4.0
DEFAULT_ENTRY_EMBARGO_HOURS: float = 0.0

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


def _scores(
    cache_key: tuple,
    facts: dict,
    questions: dict[str, str],
    anchors: dict | None = None,
) -> dict[str, float | None]:
    """One nineteen.score per question. Fewer than two anchors does not post. Never raises."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    levels = anchors if isinstance(anchors, dict) else {}
    out = {str(qid): None for qid in questions}
    ask = None
    try:
        from src.judgment.nineteen import score as ask
    except Exception:
        ask = None
    if ask is not None:
        for qid, text in questions.items():
            try:
                out[str(qid)] = _finite(
                    ask(
                        payload,
                        question_id=str(qid),
                        instructions=str(text),
                        anchors=levels.get(str(qid)),
                    )
                )
            except Exception:
                out[str(qid)] = None
    _HOP[cache_key] = dict(out)
    return out


class WeekendPolicySelectionError(ValueError):
    """A weekend-policy selection that cannot be honoured. Raised at LAUNCH, never at a tick.

    Same doctrine as `FrontierExitSelectionError`: the shapes forbidden here are the ones the
    estate has already measured as fail-open on `--tags`.
    """


def next_weekend_boundary_utc(now_utc: _dt.datetime, server: str,
                              early_close_dates: Iterable[str] = ()) -> _dt.datetime:
    """The first broker-local Saturday 00:00 strictly after `now_utc`, in true UTC.

    Raises on an unregistered server (`broker_clock.resolve_rule`). Failing closed is
    deliberate and is the same choice `exits._rollover_cutoff_index` makes: a weekend
    computed on a guessed offset would move the flatten by hours and look like a policy.

    `early_close_dates` are broker-local `YYYY-MM-DD` days on which the market does NOT
    trade. Each one at the END of a week pulls the boundary back a day, because the last
    close of a week whose Friday is a holiday is that **Friday 00:00 broker** and not
    Saturday's — MEASURED: all 7 archive weeks where the two disagree are Christmas or New
    Year (`BA_WEEKEND_V1.json` -> `identity`), and in every one of them the last H4 bar of
    the week closed at exactly Friday 00:00 broker. Without this the policy would aim its
    flatten at an instant the market had already been shut for a day, which under the
    redacted_account rule is a BREACH and not a cost. The list is operator-supplied because this
    repository has no trading-session calendar: `broker_net_cost_engine.py:44-45` names
    `symbol_info_session_trade` / `symbol_info_session_quote` as source authority it does not
    have, and `src/mt5/mt5_real.py` exposes no sessions API. Capturing that table is the
    durable fix and is filed as one.
    """
    from src.utils.broker_clock import (
        broker_naive_to_utc,
        resolve_rule,
        utc_to_broker_naive,
    )

    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=_dt.timezone.utc)
    rule = resolve_rule(server)
    local = utc_to_broker_naive(now_utc, rule)
    days = (5 - local.weekday()) % 7            # Mon=0 .. Sat=5
    cand = (local + _dt.timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    if cand <= local:
        cand += _dt.timedelta(days=7)
    holidays = {str(d).strip()[:10] for d in early_close_dates if str(d).strip()}
    if holidays:
        # Walk back over consecutive non-trading days at the END of the week. `cand` is a
        # 00:00 boundary, so the day it CLOSES is `cand - 1 day`. Bounded at 5 steps: a whole
        # week of holidays is not a weekend rule's problem, and an unbounded loop on a bad
        # list must not walk into the previous weekend.
        #
        # The `nxt > local` guard is on the RESULT of the step, not on the current value, and
        # that distinction is the whole correctness of this loop: checking the current value
        # let the last decrement land BEFORE `now`, which broke this function's one invariant
        # (the boundary is strictly in the future) and would have made `flatten_due` compare
        # against a window that had already closed. Caught by
        # `test_a_pathological_list_cannot_walk_into_the_previous_weekend`.
        #
        # When the walk stops because the next step is not in the future, the caller is being
        # asked mid-holiday: the market shut before `now` and this week's close cannot be met.
        # The boundary returned is then the earliest holiday-adjusted one still ahead, which
        # makes the flatten fire as soon as possible rather than not at all.
        for _ in range(5):
            if (cand - _dt.timedelta(days=1)).date().isoformat() not in holidays:
                break
            nxt = cand - _dt.timedelta(days=1)
            if nxt <= local:
                break
            cand = nxt
    return broker_naive_to_utc(cand, rule)


@dataclass(frozen=True)
class WeekendPolicy:
    """One account's weekend-holding policy. Empty `sleeves` == the policy is OFF."""

    #: Sleeves this policy governs. EMPTY means off — nothing is flattened, nothing embargoed.
    sleeves: tuple[str, ...] = ()
    #: Hours before broker Saturday 00:00 at which an open position must be closed.
    flatten_before_hours: float = DEFAULT_FLATTEN_BEFORE_HOURS
    #: Hours before the same instant inside which a NEW entry is refused. 0 == no embargo.
    entry_embargo_hours: float = DEFAULT_ENTRY_EMBARGO_HOURS
    #: Sleeves inside `sleeves` that the GRID reading exempts (their market never closes).
    #: Empty by default: the CALENDAR reading is the conservative one.
    exempt_sleeves: tuple[str, ...] = ()
    #: Broker-local `YYYY-MM-DD` days the market does not trade. A holiday at the end of a
    #: week pulls the whole deadline back a day; see `next_weekend_boundary_utc`. Empty by
    #: default, and empty is a MEASURED exposure rather than a safe default: 2.6 % of the
    #: archive's weekend-flat exits fall in a week this list would have to name.
    early_close_dates: tuple[str, ...] = ()
    #: Provenance carried into every ledger row the policy causes.
    evidence: str = "docs/audits/fable5-vision-audit-20260725/phase13/receipts/BA_WEEKEND_V1.json"

    def __post_init__(self) -> None:
        flatten = _finite(self.flatten_before_hours)
        if flatten is None or not (flatten > 0.0):
            raise WeekendPolicySelectionError(
                f"flatten_before_hours must be a finite hour count above 0, got "
                f"{self.flatten_before_hours!r}. Zero or negative means 'flatten after the "
                f"market has closed', which cannot execute."
            )
        if float(self.entry_embargo_hours) < 0.0:
            raise WeekendPolicySelectionError(
                f"entry_embargo_hours must be >= 0, got {self.entry_embargo_hours!r}")
        for d in self.early_close_dates:
            try:
                _dt.date.fromisoformat(str(d)[:10])
            except ValueError:
                raise WeekendPolicySelectionError(
                    f"early_close_dates must be YYYY-MM-DD broker-local days, got {d!r}. A "
                    f"date this module cannot parse would be silently ignored, which is a "
                    f"holiday week the flatten aims into a shut market."
                ) from None
        stray = sorted(set(self.exempt_sleeves) - set(self.sleeves))
        if stray:
            raise WeekendPolicySelectionError(
                f"exempt_sleeves names {stray!r}, which the policy does not govern. An "
                f"exemption from a policy that does not apply is an operator believing a "
                f"sleeve is handled when nothing reads it."
            )

    @property
    def enabled(self) -> bool:
        return bool(self.sleeves)

    def governs(self, sleeve: Any) -> bool:
        s = str(sleeve or "")
        return bool(self.sleeves) and s in self.sleeves and s not in self.exempt_sleeves

    # ---- the two decisions -----------------------------------------------------------

    def boundary_utc(self, now_utc: _dt.datetime, server: str) -> _dt.datetime:
        """The instant the trading week ends, holiday list applied."""
        return next_weekend_boundary_utc(now_utc, server, self.early_close_dates)

    def flatten_deadline_utc(self, now_utc: _dt.datetime, server: str) -> _dt.datetime:
        """The instant a governed position must already be closed by."""
        return (self.boundary_utc(now_utc, server)
                - _dt.timedelta(hours=float(self.flatten_before_hours)))

    def flatten_due(self, sleeve: Any, now_utc: _dt.datetime, server: str) -> bool:
        """Is a governed open position past its flatten deadline right now?

        The deadline is computed from `now_utc`, so once `now` passes it the NEXT boundary is
        a week away and this would read False again. The window is therefore closed
        explicitly: due iff `now` is inside `[deadline, boundary)` of the boundary it belongs
        to. Anything at or after the boundary is a market that has already closed — nothing
        can be sent, and reporting `True` there would spin a close attempt every tick all
        weekend.
        """
        if not self.governs(sleeve):
            return False
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=_dt.timezone.utc)
        boundary = self.boundary_utc(now_utc, server)
        deadline = boundary - _dt.timedelta(hours=float(self.flatten_before_hours))
        return deadline <= now_utc < boundary

    def entry_blocked(self, sleeve: Any, now_utc: _dt.datetime, server: str) -> bool:
        """Would a new entry now be refused by the embargo, or by the flatten itself?

        Two reasons, and both are the same decision the research replay makes:
        `entry_embargo_hours` before the boundary, and — always, whatever the embargo — an
        entry taken at or after the flatten deadline, which would be closed on the same tick
        it was opened.
        """
        if not self.governs(sleeve):
            return False
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=_dt.timezone.utc)
        boundary = self.boundary_utc(now_utc, server)
        block_hours = max(float(self.entry_embargo_hours), float(self.flatten_before_hours))
        return (boundary - now_utc) <= _dt.timedelta(hours=block_hours)

    def as_dict(self) -> dict[str, Any]:
        return {
            "sleeves": list(self.sleeves),
            "flatten_before_hours": float(self.flatten_before_hours),
            "entry_embargo_hours": float(self.entry_embargo_hours),
            "exempt_sleeves": list(self.exempt_sleeves),
            "n_early_close_dates": len(self.early_close_dates),
            "early_close_dates": list(self.early_close_dates),
            "evidence": self.evidence,
        }


#: Off. `WeekendPolicy()` with no sleeves governs nothing; `governs()` is False for every
#: name, so both decisions are False and the default code path is the committed one.
OFF = WeekendPolicy()


def parse_weekend_flat(raw, *, known_sleeves: Iterable[str] | None = None) -> tuple[str, ...]:
    """`"a,b"` / `("a",)` / None -> the validated sleeve tuple. Raises on empty or unknown.

    `known_sleeves` defaults to every sleeve with a declared exit profile, which is the
    widest set the book can place. A caller that knows the account's `--tags` should pass
    it — but this must NOT reject a name outside `--tags`, because arming the policy before
    arming the sleeve is a legitimate and safer order of operations.
    """
    if raw is None:
        return ()
    items = ([s.strip() for s in raw.split(",")] if isinstance(raw, str)
             else [str(s).strip() for s in raw])
    named = [s for s in items if s]
    if not named:
        raise WeekendPolicySelectionError(
            "--weekend-flat was given but names no sleeve. An empty selection is refused "
            "rather than read as 'all': the same shape on --tags means 'every BUILT sleeve' "
            "and is a fail-open the book already carries (B359)."
        )
    if known_sleeves is None:
        from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES
        known = set(SLEEVE_EXIT_PROFILES)
    else:
        known = set(known_sleeves)
    unknown = [s for s in named if s not in known]
    if unknown:
        raise WeekendPolicySelectionError(
            f"unknown sleeve(s) {unknown!r} in --weekend-flat. A typo must not resolve to "
            f"'no policy' in silence -- that is an operator believing a funded account is "
            f"compliant while it holds over the weekend. Known: {sorted(known)}"
        )
    return tuple(dict.fromkeys(named))


def parse_early_close_dates(raw) -> tuple[str, ...]:
    """`"2026-12-25,2027-01-01"` / an iterable / None -> validated broker-local dates.

    A path is accepted too, so the list can live in a file the operator maintains rather than
    in a supervisor command line that nobody diffs. Refuses an empty selection for the same
    reason `parse_weekend_flat` does.
    """
    if raw is None:
        return ()
    if isinstance(raw, str) and raw.strip() and not any(c in raw for c in ",") \
            and _pathlib.Path(raw.strip()).is_file():
        text = _pathlib.Path(raw.strip()).read_text(encoding="utf-8")
        items = [ln.split("#", 1)[0].strip() for ln in text.splitlines()]
    elif isinstance(raw, str):
        items = [s.strip() for s in raw.split(",")]
    else:
        items = [str(s).strip() for s in raw]
    named = [s for s in items if s]
    if not named:
        raise WeekendPolicySelectionError(
            "--weekend-early-close was given but names no date. An empty list is refused "
            "rather than read as 'no holidays': the whole point of the argument is that the "
            "empty case is a MEASURED exposure."
        )
    for s in named:
        try:
            _dt.date.fromisoformat(s[:10])
        except ValueError:
            raise WeekendPolicySelectionError(
                f"--weekend-early-close: {s!r} is not a YYYY-MM-DD broker-local date."
            ) from None
    return tuple(dict.fromkeys(s[:10] for s in named))


def policy_from_args(weekend_flat, *, flatten_before_hours=None, entry_embargo_hours=None,
                     exempt=None, early_close=None, known_sleeves=None) -> WeekendPolicy:
    """Build the policy from launcher arguments, or `OFF` when no sleeve is named."""
    sleeves = parse_weekend_flat(weekend_flat, known_sleeves=known_sleeves)
    if not sleeves:
        return OFF
    ex = parse_weekend_flat(exempt, known_sleeves=known_sleeves) if exempt else ()
    offered_flatten = None if flatten_before_hours is None else _finite(flatten_before_hours)
    offered_embargo = None if entry_embargo_hours is None else _finite(entry_embargo_hours)
    if flatten_before_hours is not None and offered_flatten is None:
        raise WeekendPolicySelectionError(
            f"flatten_before_hours is not a finite number: {flatten_before_hours!r}"
        )
    if entry_embargo_hours is not None and offered_embargo is None:
        raise WeekendPolicySelectionError(
            f"entry_embargo_hours is not a finite number: {entry_embargo_hours!r}"
        )
    questions: dict[str, str] = {}
    if offered_flatten is None:
        questions["flatten_before_hours"] = (
            "The score you return is how many hours before the weekend boundary a governed "
            "position must already be closed. An empty score leaves that lead unset. Do not send."
        )
    if offered_embargo is None:
        questions["entry_embargo_hours"] = (
            "The score you return is how many hours before the weekend boundary a new entry "
            "is refused. An empty score leaves that embargo unset. Do not send."
        )
    hour_levels = []
    if offered_flatten is not None:
        hour_levels.append(("the offered flatten lead in hours", offered_flatten))
    if offered_embargo is not None:
        hour_levels.append(("the offered entry embargo in hours", offered_embargo))
    scores = (
        _scores(
            ("weekend_policy", tuple(sleeves), offered_flatten, offered_embargo),
            {
                "sleeves": list(sleeves),
                "offered_flatten_before_hours": offered_flatten,
                "offered_entry_embargo_hours": offered_embargo,
            },
            questions,
            {name: list(hour_levels) for name in questions},
        )
        if questions
        else {}
    )
    flatten = offered_flatten if offered_flatten is not None else scores.get("flatten_before_hours")
    embargo = offered_embargo if offered_embargo is not None else scores.get("entry_embargo_hours")
    if offered_flatten is not None and not (offered_flatten > 0.0):
        raise WeekendPolicySelectionError(
            f"flatten_before_hours must be > 0, got {offered_flatten!r}"
        )
    if flatten is None or not (float(flatten) > 0.0):
        return OFF
    if offered_embargo is not None and offered_embargo < 0.0:
        raise WeekendPolicySelectionError(
            f"entry_embargo_hours must be >= 0, got {offered_embargo!r}"
        )
    if embargo is None or float(embargo) < 0.0:
        embargo = 0.0
    return WeekendPolicy(
        sleeves=sleeves,
        flatten_before_hours=float(flatten),
        entry_embargo_hours=float(embargo),
        exempt_sleeves=ex,
        early_close_dates=parse_early_close_dates(early_close),
    )

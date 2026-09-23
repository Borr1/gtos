"""GTOS minimal-size live experiment: NOMINAL decisions, SCALED lots, NOTIONAL governor.

Reached from ``run_book.py --f5-minimal-size-usd``. With that flag absent every seam this
module owns is a no-op and the live path is unchanged -- ``test_f5_default_path_unchanged``
is what pins that, not this sentence.

================================ THE ONE IDEA =================================
The whole decision pipeline runs at NOMINAL risk (the production dial, 2.0 %) and produces
the same decisions production would. Only the final lot is scaled.

If the allocator saw $1 candidates it would be a different system:
``admission._enforce_gross_open_risk_cap`` sheds against a 4 % gross budget expressed as a
PERCENT OF EQUITY, ``_governor_decision`` de-risks on drawdown percentages, the Kelly-lite
conviction multiplier keys on the running count of firing sleeves, and
``book_engine._open_risk_pct`` sums worst-case-stop loss over OPEN BROKER POSITIONS. Scale
the lots and leave those alone and every one of them silently stops binding: at 1/200th
size the 4 % gross cap NEVER binds, so the book would run 20+ concurrent units where
production runs 2 (``F_LAW_AND_LADDER_V1.json`` -> ``max_concurrent_units_by_dial["2.0%"]
== 2.0``), and the experiment would measure a system that will never be deployed.

So there are FOUR surfaces and only ONE is scaled:

  NOTIONAL (N1) realized balance + scaled floating P&L -> broker-position-reconciled ledger
  NOTIONAL (N2) open_risk_pct                           -> CURRENT nominal volume/SL exposure
  NOTIONAL (N3) realized_today_pct                      -> from the notional ledger
  SCALED   (S1) risk_amount -> lots                     -> execution.py, the LAST step

plus one behaviour change:

  ROUND-UP (S2) sub-minimum lots round UP to volume_min, never shed.

============================== WHY ROUND-UP ===================================
``open_trade`` sheds a sub-minimum unit as TERMINAL (``return None`` with
``below_min_lot``) and ``_normalize_volume`` returns ``None`` below ``volume_min`` as well.
That is correct for production -- a sub-minimum unit is a real breadth loss -- and
catastrophic here: it would silently delete exactly the expensive-stop instruments
(BTCUSD, XAGUSD, XAUUSD, ETHUSD on FTMO; those plus the 10x-contract indices on
redacted_account) and the surviving sample would answer no cost question.

MEASURED (``F5_MIN_LOT_FLOOR_V1.json``, 9,083 throttled estate trades 2024-2026): at a $10
target, 5.7 % of FTMO trades and 10.0 % of redacted_account trades round up, and they carry
13.4 % / 24.3 % of total dollar risk. It biases NO R-denominated result and every trade is
present; it biases DOLLAR-weighted aggregates by exactly those shares, correctable with the
weight ``f5_intended_risk_usd / f5_actual_risk_usd``. Both are recorded per fill so the
reweighting is exact rather than modelled.

============================== EPOCHS =========================================
When the NOTIONAL book breaches, production would be dead. This experiment must observe the
stand-down AND survive it. So: the stand-down executes for real (the production flatten
path, on real positions), a numbered ``f5_notional_standdown`` event is written, and only
then does the ledger open a new epoch at the initial balance. Never silent. Analysis slices
by epoch.

============================== NO LOSS BUDGET =================================
Owner decision, 2026-08-12: no automatic cumulative-loss brake. The experiment runs inside
the firm's own limits and the production governor exactly as the armed book does -- the
soft daily stop, ``breach_flatten_check``, the firm's -5 %/-10 % lines, the per-account kill
flag and the activation token are all untouched and none is bypassed. What replaces the
budget is visibility: ``scripts/f5_status.py``.

``real_pnl_usd_cumulative`` is accumulated for that view, NOT for a gate. Nothing in this
module or in ``book_owner`` reads it to decide anything. Adding a threshold here is a policy
change and needs the owner's word.

======================== TWO SURFACES, ONE ACCOUNT ===========================
The experiment runs alongside the armed book on the SAME account. Namespace isolates every
file surface and no broker surface, so the experiment takes its own broker identity
(``mt5_interface.magic_for_namespace`` -> 0, comment prefix ``F5:``). See
``tests/safety/test_f5_isolation.py``. The one coupling no design removes is shared real
equity, and it is measured, instrumented and reported -- never gated.
"""

from __future__ import annotations

import json
import math
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

_HELD_ANCHORS: dict[str, float] = {}


def held_anchor_facts() -> dict[str, float]:
    """Account numbers this module already holds. Empty until a ledger has loaded."""

    return dict(_HELD_ANCHORS)


def _hold_anchor_facts(facts: Mapping[str, Any]) -> None:
    for key, value in facts.items():
        if isinstance(value, bool) or value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number != number or number in (float("inf"), float("-inf")):
            continue
        _HELD_ANCHORS[str(key)] = number


def _returned(qid: str) -> float | None:
    """Score for this state. None when it has not returned. Does not restore a number."""

    try:
        from src.components.ultimate_book.launcher_facts import launcher_return

        number = launcher_return(qid)
    except Exception:
        return None
    if isinstance(number, bool) or number is None:
        return None
    try:
        value = float(number)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")) or value < 0:
        return None
    return value


class _Score:
    """A name other modules float. Unset until the score for this state returns."""

    def __init__(self, qid: str, unit: str):
        self.qid = qid
        self.unit = unit

    def value(self) -> float | None:
        return _returned(self.qid)

    def __float__(self) -> float:
        number = self.value()
        if number is None:
            raise ValueError("unset")
        return float(number)

    def __int__(self) -> int:
        number = self.value()
        if number is None:
            raise ValueError("unset")
        return int(number)

    def __repr__(self) -> str:
        number = self.value()
        if number is None:
            return "unset"
        return repr(number)


class _DeadHours:
    """UTC hours of the thin window. Empty until the start hour returns."""

    def _start(self) -> int | None:
        number = _returned("dead_window_start_hour")
        if number is None:
            return None
        whole = int(number)
        if whole != number or not 0 <= whole <= 23:
            return None
        return whole

    def __contains__(self, item: object) -> bool:
        start = self._start()
        if start is None:
            return False
        try:
            hour = int(item)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
        return start <= hour <= 23

    def __iter__(self):
        start = self._start()
        if start is None:
            return iter(())
        return iter(range(start, 24))

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        return self._start() is not None


def _clock_pair(value: object) -> tuple[int, int] | None:
    if not isinstance(value, tuple) or len(value) != 2:
        return None
    try:
        hour = int(value[0])
        minute = int(value[1])
    except (TypeError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def _friday_cutoff_pair() -> tuple[int, int] | None:
    try:
        from src.components.ultimate_book.launcher_facts import clock_from_minutes, launcher_return

        pair = clock_from_minutes(launcher_return("friday_cutoff_minute"))
        if pair is not None:
            return pair
    except Exception:
        pass
    return _clock_pair(F5_WEEKEND_NEW_RISK_CUTOFF_UTC_HHMM)


def _weekend_flat_pair() -> tuple[int, int] | None:
    try:
        from src.components.ultimate_book.launcher_facts import clock_from_minutes, launcher_return

        pair = clock_from_minutes(launcher_return("weekend_flat_minute"))
        if pair is not None:
            return pair
    except Exception:
        pass
    return _clock_pair(F5_WEEKEND_FLAT_UTC_HHMM)


SCHEMA = "gtos.ultimate_book.minimal_size.v1"
EVENT_SCHEMA = "gtos.f5.minimal_size_event.v1"

#: Filename of the notional ledger inside the namespace's pipeline_state directory.
LEDGER_FILENAME = "f5_notional_ledger.json"

# --------------------------------------------------------------------------------------------
# F5 guard constants (2026-08-25). ALL of these are consumed by `book_owner` behind an explicit
# `namespace == "operator"` gate -- they are POLICY for the one F5 experiment book and
# they are declared here, in the F5 module, so the policy has one home. No production namespace
# reads any of them.
# --------------------------------------------------------------------------------------------

#: POST-FILL DEVIATION GUARD (the LTCUSD 178351323 fix, broker-truth 2026-08-24): a market fill
#: whose adverse entry slippage exceeds this many R (R = the intent's own stop distance) is
#: closed immediately -- the position was born at a materially different risk than the one that
#: was sized ($74.93 intended, $184 actual on LTCUSD: fill 1.48R through the intended entry,
#: 2.46x intended risk, net -4.10R). Median |entry slippage| across 52 joined fills is 0.002R
#: and the max normal is 0.138R, so 0.5R tags only the pathological tail.
F5_MAX_FILL_DEVIATION_R = _Score("fill_deviation_r", "r")

#: THIN-HOUR PLACEMENT: sleeves routed through limit-at-level placement instead of a market
#: order (all symbols). `asia_pdl_fade` decides during broker hours 0..6 (the thin Asian
#: session) and enters "at close[i]" -- a market order there crosses a thin book (the LTCUSD
#: fill above WAS this sleeve). A resting limit at the level either fills at the intended
#: price or does not fill at all; NO_FILL is an acceptable outcome, a 2.46x-risk fill is not.
THIN_HOUR_LIMIT_SLEEVES = frozenset({"asia_pdl_fade"})

#: How many decision-timeframe bars a thin-hour resting limit may live before the existing
#: native-pending expiry machinery cancels it. Short deliberately: the level was decided on
#: one closed bar; half an hour later the setup is a different market.
F5_THIN_HOUR_LIMIT_EXPIRY_BARS = _Score("thin_hour_limit_expiry_bars", "bars")

#: CONTRACT V2 (Fable 5.1, 2026-09-02): every F5 limit-at-level intent rests at most this many
#: closed M15 bars. Measured on the 77 limit fills of 24 Aug -> 2 Sep: fills inside 60 min were
#: +50.9R held to orig (n=70); fills later than 60 min were -5.7R actual and -4.6R even held to
#: orig (n=7). Stale GTC limits also kept the symbol 'occupied' and refused 31 flat-symbol
#: re-fires worth +18.0R held to orig. Broker-side sweep: book_owner._f5_sweep_stale_pending_orders.
F5_LIMIT_EXPIRY_BARS = _Score("limit_expiry_bars", "bars")
#: Broker ORDER_TIME_SPECIFIED. The seconds are the score. Unset leaves the limit without a planted life.
F5_LIMIT_EXPIRY_SECONDS = _Score("limit_expiry_seconds", "seconds")
#: MetaTrader5 SYMBOL_EXPIRATION_SPECIFIED bit. Honour expiration_mode & 4 or stay GTC.
SYMBOL_EXPIRATION_SPECIFIED = 4


def f5_raw_mt5(engine_or_wrapper) -> object | None:
    """RAW MetaTrader5 module. Never the GTOS wrapper.

    The engine's wrapper is ``self.mt5``; its raw module is ``self.mt5._mt5``.
    The v2 leftover called ``self._mt5`` (AttributeError → GTC, order 180770382).
    """
    wrapper = getattr(engine_or_wrapper, "mt5", engine_or_wrapper)
    if wrapper is None:
        return None
    return getattr(wrapper, "_mt5", None)


def f5_native_limit_expiration(raw_module, symbol) -> tuple[int, int | None]:
    """(type_time, expiration). type_time=1 only through the RAW module.

    A test that passes the GTOS wrapper (no ``_mt5``, no tick.time) MUST get (0, None).
    Positions are not limits — callers only use this on TRADE_ACTION_PENDING.
    """
    if raw_module is None:
        return 0, None
    try:
        tick = raw_module.symbol_info_tick(symbol)
        t0 = int(getattr(tick, "time", 0) or 0)
        si = raw_module.symbol_info(symbol)
        mode = int(getattr(si, "expiration_mode", 0) or 0)
        if mode and not (mode & SYMBOL_EXPIRATION_SPECIFIED):
            return 0, None
        if t0 <= 0:
            return 0, None
        try:
            expiry = int(F5_LIMIT_EXPIRY_SECONDS)
        except (TypeError, ValueError):
            return 0, None
        if expiry < 0:
            return 0, None
        return 1, t0 + expiry
    except Exception:
        return 0, None

#: CONTRACT V3: the last-resort flatten watches the real account.
#: A floor and a baseline do not size the next unit. The cash is the returned parameter.
#: The notional governor no longer flattens F5.

#: WEEKEND-CARRY RULE: a non-24/7 symbol still open at/after Friday this UTC time is closed
#: (weekend gap risk on an open unit was measured: weekend-carry FX holds are
#: one of the two concentrations of the -$549 beyond--1R loser tail).
F5_WEEKEND_FLAT_UTC_HHMM = None

#: ... unless the stop is already trailed to lock at least this many R -- a locked winner may
#: ride its broker stop through the weekend.
F5_WEEKEND_LOCKED_R_EXEMPT = None

#: Symbols that quote (near-)24/7 on the funded brokers -- the weekend flatten exempts these.
#: Union of the crypto surfaces declared by this tree's sleeves (crypto.py, orb_crypto_london,
#: structural_retest._CRYPTO, asia_pdl_fade.ON_SURFACE crypto rows).
F5_ALWAYS_OPEN_SYMBOLS = frozenset({
    "BTCUSD", "ETHUSD", "XRPUSD", "XTZUSD", "LTCUSD", "DASHUSD", "DOTUSD", "ADAUSD",
})

#: DEAD WINDOW (WEEK-STUDY-2): 21:00-00:00 UTC is post-NY-cash / pre-Tokyo.
#: 16 fills, 1 win, -$2,124, -1.09R. Writer refuses NEW risk. Occupied stays.
F5_DEAD_WINDOW_UTC_HOUR_START = _Score("dead_window_start_hour", "hour_of_day")
F5_DEAD_WINDOW_UTC_HOUR_END = None

#: Named HIGH window around Fed/CPI/NFP/rates/Warsh-class prints.
#: WEEK-STUDY-2: sit NEW fills T-15 / T+60 of named Fed speakers. Occupied
#: thesis that has already paid may stay. Gate by candidate SYMBOL, not occupancy.
F5_HIGH_PRE_MINUTES = _Score("high_pre_minutes", "minutes")
F5_HIGH_POST_MINUTES = _Score("high_post_minutes", "minutes")
#: Calendar PRIME amplifier T−45..T−0. NOT a gate. NOT the 23 cal_* stubs.
#: HIGH block stays T−15..T+60. Size-2 hook stays dark until J4 PRIMED_V1.md.
F5_CAL_AMPLIFIER_PRE_MINUTES = _Score("calendar_prime_pre_minutes", "minutes")
F5_CAL_PRIME_SIZE_MULT = None

#: WEEKEND-FLAT TAX: flatten is Friday 20:30 UTC. Overlap (the paid window)
#: ends 16:00 UTC. Do not enter Friday NY so late that flatten is the plan.
#: Crypto is already 24/7 (F5_ALWAYS_OPEN_SYMBOLS).
F5_WEEKEND_NEW_RISK_CUTOFF_UTC_HHMM = None

#: Reload the live calendar at most this often. File mtime changes invalidate
#: immediately so a spine refresh does not need a writer restart.
F5_CALENDAR_TTL_S = None

#: Intel-layer live brief/spine (not news_tape: that tape is occupancy+Walter
#: and went stale 2026-08-27 07:38 UTC with result_count 0).
F5_INTEL_CALENDAR_DIR = Path(r"C:\Users\trader\intel-layer\calendar")

#: event_type values that are Warsh-class even without a speaker name.
F5_WARSH_CLASS_EVENT_TYPES = frozenset({
    "fomc_decision", "fomc_presser", "fomc_unscheduled", "fomc_notation_vote",
    "cpi", "nfp", "fed_speech",
    "ecb_decision", "ecb_presser", "boe_decision", "boj_decision",
    "rate_decision",
})

#: USD HIGH (Fed/CPI/NFP) also touches these non-USD-leg risk indices.
#: Warsh news_brief tickets were US30/EURUSD/GER40; GBPUSD still ate -$354.
F5_USD_HIGH_EXTRA_SYMBOLS = frozenset({
    "GER40", "UK100", "EU50", "FRA40", "JP225",
})

F5_INDEX_CCY = {
    "UK100": "GBP", "GER40": "EUR", "EU50": "EUR", "FRA40": "EUR",
    "US30": "USD", "US100": "USD", "US500": "USD", "NAS100": "USD",
    "SPX500": "USD", "JP225": "JPY", "AUS200": "AUD", "HK50": "HKD",
}
_F5_CCY_CODES = frozenset({
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "CNH", "SGD",
    "XAU", "XAG", "XPT", "XPD", "HKD", "NOK", "SEK", "MXN", "ZAR", "PLN",
})
_F5_CRYPTO_BASES = frozenset({
    "BTC", "ETH", "LTC", "XRP", "ADA", "SOL", "DOG", "DOGE", "XTZ", "AVA",
    "AVAX", "DOT", "BCH", "LNK", "LINK", "UNI", "EOS", "XLM", "TRX", "DASH",
})
_F5_WARSH_EXCLUDE = (
    "agenda published", "agenda drop", "meeting account",
    "weekly claims", "chicago pmi", "unemployment insurance",
    "ces preliminary", "prelim benchmark",
)
_F5_WARSH_NEEDLES = (
    "warsh", "powell", "fomc", "fed chair", "federal reserve chair",
    "fed governor", "fomc member", "jackson hole remarks",
    "jackson hole speech", "jackson hole address", "jackson hole speaker",
    "non-farm", "nonfarm", "nfp", "payrolls",
    "interest rate decision", "rate decision",
)

#: THE MANAGE CONSUME SEAM (schema gtos.judgment.manage.v1): bounds for a row's ttl_s.
#: A missing ttl is the returned default. Unset does not restore a lifetime.
#: A returned min and max are the actionable band. Unset does not restore a band.
#: Consume cursor persist: judgment/state/manage_consume_cursor.json so a book
#: restart does not re-emit expired (178427810 class).
F5_MANAGE_TTL_MIN_S = _Score("manage_ttl_min_s", "seconds")
F5_MANAGE_TTL_MAX_S = _Score("manage_ttl_max_s", "seconds")
F5_MANAGE_TTL_DEFAULT_S = _Score("manage_ttl_default_s", "seconds")
F5_MANAGE_SCHEMA = "gtos.judgment.manage.v1"
F5_MANAGE_CONSUME_CURSOR_SCHEMA = "gtos.judgment.manage_consume_cursor.v1"

# Ghost 10011 close storm (WEEK-STUDY-4): RealMT5 wraps order_send None as
# retcode 10011 / comment "MT5 returned None". That is broker-unknown, not a
# fill, not TRADE_RETCODE_DONE, and not a disk `closed` stamp. The ~60s manage
# poll retried dead tickets (1,808 Nones; Friday 912). Backoff + max retries +
# dead-ticket cache stop the hammer. Disk closed is the positions_get sit door
# (broker_closed_absent_on_reconcile). Do not flatten live positions to "fix" it.
F5_CLOSE_SEND_NONE_RETCODE = 10011
F5_CLOSE_SEND_NONE_MAX_RETRIES = _Score("close_none_max_retries", "count")
F5_CLOSE_SEND_NONE_BACKOFF_S = _Score("close_none_backoff_s", "seconds")
F5_CLOSE_SEND_NONE_CACHE_MAX = _Score("close_none_cache_max", "count")

_CLOSE_SEND_NONE_LOCK = threading.Lock()
_CLOSE_SEND_NONE: dict[int, dict[str, Any]] = {}


def _close_send_none_now(now: Optional[datetime] = None) -> datetime:
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now


def _close_send_none_ticket(ticket) -> int | None:
    try:
        ticket_i = int(ticket)
    except (TypeError, ValueError):
        return None
    if ticket_i <= 0:
        return None
    return ticket_i


def _close_send_none_prune_locked() -> None:
    try:
        cap = int(F5_CLOSE_SEND_NONE_CACHE_MAX)
    except (TypeError, ValueError):
        return
    extra = len(_CLOSE_SEND_NONE) - cap
    if extra <= 0:
        return
    ranked = sorted(
        _CLOSE_SEND_NONE.items(),
        key=lambda item: str(item[1].get("last_utc") or ""),
    )
    for old_ticket, _state in ranked[:extra]:
        _CLOSE_SEND_NONE.pop(old_ticket, None)


def f5_close_send_none_reset() -> None:
    """Test helper. Production never needs to wipe the dead-ticket cache."""
    with _CLOSE_SEND_NONE_LOCK:
        _CLOSE_SEND_NONE.clear()


def f5_close_send_none_seen(ticket) -> bool:
    ticket_i = _close_send_none_ticket(ticket)
    if ticket_i is None:
        return False
    with _CLOSE_SEND_NONE_LOCK:
        return ticket_i in _CLOSE_SEND_NONE


def f5_close_send_none_is_dead(ticket) -> bool:
    ticket_i = _close_send_none_ticket(ticket)
    if ticket_i is None:
        return False
    with _CLOSE_SEND_NONE_LOCK:
        state = _CLOSE_SEND_NONE.get(ticket_i)
        return bool(state and state.get("dead"))


def f5_close_send_none_should_defer_disk_closed(ticket) -> bool:
    """True after a 10011/None close: do not stamp disk closed from the writer.

    The sit door is positions_get absence (book_owner reconcile, two confirms).
    """
    return f5_close_send_none_seen(ticket)


def f5_close_send_none_allow_order_send(
    ticket,
    now: Optional[datetime] = None,
) -> bool:
    """False while backing off, dead, or absent-on-sit. First sight is allowed."""
    ticket_i = _close_send_none_ticket(ticket)
    if ticket_i is None:
        return False
    now = _close_send_none_now(now)
    with _CLOSE_SEND_NONE_LOCK:
        state = _CLOSE_SEND_NONE.get(ticket_i)
        if not state:
            return True
        if state.get("absent_sit") or state.get("dead"):
            return False
        nxt = state.get("next_allowed_utc")
        if isinstance(nxt, datetime):
            if nxt.tzinfo is None:
                nxt = nxt.replace(tzinfo=timezone.utc)
            if now < nxt:
                return False
        return True


def f5_close_send_none_note_none(
    ticket,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Record an order_send None / 10011. Does not stamp closed."""
    ticket_i = _close_send_none_ticket(ticket)
    now = _close_send_none_now(now)
    empty = {"attempts": 0, "dead": False, "absent_sit": False, "next_allowed_utc": None}
    if ticket_i is None:
        return empty
    try:
        delay = float(F5_CLOSE_SEND_NONE_BACKOFF_S)
    except (TypeError, ValueError):
        delay = None
    try:
        retry_cap = int(F5_CLOSE_SEND_NONE_MAX_RETRIES)
    except (TypeError, ValueError):
        retry_cap = None
    with _CLOSE_SEND_NONE_LOCK:
        state = _CLOSE_SEND_NONE.get(ticket_i) or {
            "attempts": 0, "dead": False, "absent_sit": False,
            "next_allowed_utc": None, "last_utc": None,
        }
        attempts = int(state.get("attempts") or 0) + 1
        state["attempts"] = attempts
        state["last_utc"] = now
        if delay is None or delay < 0:
            state["next_allowed_utc"] = None
        else:
            state["next_allowed_utc"] = now + timedelta(seconds=delay)
        state["dead"] = False if retry_cap is None else attempts >= retry_cap
        _CLOSE_SEND_NONE[ticket_i] = state
        _close_send_none_prune_locked()
        return dict(state)


def f5_close_send_none_mark_absent(
    ticket,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Ticket missing from a successful positions_get sit: never send again until present."""
    ticket_i = _close_send_none_ticket(ticket)
    now = _close_send_none_now(now)
    empty = {"attempts": 0, "dead": True, "absent_sit": True}
    if ticket_i is None:
        return empty
    with _CLOSE_SEND_NONE_LOCK:
        state = _CLOSE_SEND_NONE.get(ticket_i) or {
            "attempts": 0, "next_allowed_utc": None, "last_utc": None,
        }
        state["last_utc"] = now
        state["dead"] = True
        state["absent_sit"] = True
        _CLOSE_SEND_NONE[ticket_i] = state
        _close_send_none_prune_locked()
        return dict(state)


def f5_close_send_none_note_present(ticket, now: Optional[datetime] = None) -> None:
    """Sit found the ticket still live. May un-dead; backoff stays."""
    ticket_i = _close_send_none_ticket(ticket)
    if ticket_i is None:
        return
    now = _close_send_none_now(now)
    with _CLOSE_SEND_NONE_LOCK:
        state = _CLOSE_SEND_NONE.get(ticket_i)
        if not state:
            return
        state["absent_sit"] = False
        state["dead"] = False
        state["last_utc"] = now


def f5_close_send_none_clear(ticket) -> None:
    """Successful close, or ticket left the engine via the sit door."""
    ticket_i = _close_send_none_ticket(ticket)
    if ticket_i is None:
        return
    with _CLOSE_SEND_NONE_LOCK:
        _CLOSE_SEND_NONE.pop(ticket_i, None)


#: AUTO-BREAKEVEN (2026-08-25, owner-directed: encode the live chair's measured behaviour).
#: When an open position's favourable excursion TOUCHES this many R of its own initial stop
#: distance, the stop moves to an *economic* breakeven — past round-trip cost plus a little
#: room — while the target stays. Price-at-entry is not net-zero: commission and the exit
#: spread still charge. The mining verify DEMOTED a blanket +1.0R rule (forfeit 25–33%) so
#: the trigger sits at +1.5R, past the straddle.
#: CONTRACT V1. Measured on the closed tickets of that window:
#: the +1.5R one-shot lock (0.05-0.20R) plus chair takes turned a hold-to-orig contract worth +9.4R at the
#: researched 8h horizon into -30.4R realised. Owner word 2026-08-31 20:16 ICT: do not BE/trail on first MFE;
#: let it breathe. The writer manages nothing between fill and broker SL/TP/time-stop on F5 until a paired
#: nightly measurement says a specific exit beats hold-to-orig. Flip here, not by editing the trigger.
F5_AUTO_BE_ENABLED = False
F5_AUTO_BE_TRIGGER_R = None
#: Floor / cap of the lock past entry, in R of the original stop. Floor so a 1-tick
#: "BE" still loses fees to slippage; cap so this stays a one-shot lock, not a trail.
F5_AUTO_BE_MIN_LOCK_R = _Score("auto_be_min_lock_r", "r")
F5_AUTO_BE_MAX_LOCK_R = _Score("auto_be_max_lock_r", "r")
#: Extra spread of room on top of the known round-trip cost.
F5_AUTO_BE_EXTRA_SPREADS = _Score("auto_be_extra_spreads", "spreads")

#: NULL-RULE sleeves (MANAGE_FRONTIER_VERIFY, CONFIRMED): long-target runner sleeves whose
#: only live-measured management EV is NEGATIVE (-0.23..-0.31 R/day scale-out cost, n=67 live
#: + three walked corroborations). The auto-breakeven NEVER touches these; their exits are
#: contract-owned. `mx_*` covered by prefix.
F5_AUTO_BE_EXCLUDED_SLEEVES = frozenset({
    "crypto", "energy_agri", "sub_xvol_pullback", "metals_softband", "vol_compression",
})
F5_AUTO_BE_EXCLUDED_PREFIXES = ("mx_",)


def f5_economic_be_stop(
    direction: str,
    entry: float,
    init_stop: float,
    bid: float,
    ask: float,
    round_trip_cost_price: float | None = None,
) -> float | None:
    """Stop that is net-flat after fees, with a little room. Not price-at-entry.

    Offset = known round-trip cost (spread + commission in price; live spread if
    cost is unknown) plus one extra spread of room, floored at
    ``F5_AUTO_BE_MIN_LOCK_R`` of the original stop and capped at
    ``F5_AUTO_BE_MAX_LOCK_R`` so this stays a one-shot lock, not a trail.
    Returns None if the inputs cannot support a lock.
    """
    side = str(direction or "").upper()
    if side not in ("LONG", "SHORT"):
        return None
    try:
        entry_f = float(entry)
        init_f = float(init_stop)
        bid_f = float(bid)
        ask_f = float(ask)
    except (TypeError, ValueError):
        return None
    denom = abs(entry_f - init_f)
    spread = ask_f - bid_f
    if not all(math.isfinite(v) for v in (entry_f, init_f, bid_f, ask_f, denom, spread)):
        return None
    if entry_f <= 0 or denom <= 0 or bid_f <= 0 or ask_f <= 0 or spread < 0:
        return None
    cost = float("nan")
    if round_trip_cost_price is not None:
        try:
            cost = float(round_trip_cost_price)
        except (TypeError, ValueError):
            cost = float("nan")
    if not (math.isfinite(cost) and cost > 0):
        cost = spread
    extra = _returned("auto_be_extra_spreads")
    lo_r = _returned("auto_be_min_lock_r")
    hi_r = _returned("auto_be_max_lock_r")
    if extra is None or lo_r is None or hi_r is None:
        return None
    room = max(spread * float(extra), float(lo_r) * denom)
    offset = cost + room
    lo = float(lo_r) * denom
    hi = float(hi_r) * denom
    offset = min(max(offset, lo), hi)
    if not (math.isfinite(offset) and offset > 0):
        return None
    if side == "LONG":
        return entry_f + offset
    return entry_f - offset


F5_NAMESPACE = "operator"
#: USDJPY is held for the rest of this verification (microstructure, not a mood).
#: Occupied-symbol HOLD is computed at the call site from live engines / pendings.
F5_STANDING_HOLD_SYMBOLS = frozenset({"USDJPY"})

# --------------------------------------------------------------------------------------------
# WEEK-REPAIR 2026-08-29. Writer admission. --tags stay token-bound; these names cannot place.
# --------------------------------------------------------------------------------------------
F5_HARD_OFF_SLEEVES = frozenset({
    "asia_pdl_fade",
    "asian_fade",
    "asian_fade_widen",
    "metal_session_reversion",
    "dsp_climax_flush_to_96low_then_snap",
    "dsp_isolated_flush_to_20low_snap",
    "dsp_small_bar_sit_on_20high_rejects",
    "dsp_already_wide_down_bar_second_wave",
    "dsp_overnight_box_failed_floor_probe",
    "dsp_cascade_last_two_not_yet_four",
    "dsp_session_open_already_live",
    "dsp_two_open_bars_down_then_cascade",
    "dsp_climax_into_high_then_dump",
    "dsp_bleed_accept_fresh_20low_second_push",
    "idxrev",
    "orb_crypto_london",
    "orb_crypto_london_widen",
    "xa_huge_20_extreme",
    "xa_huge_same_way",
})

#: Thin window hours. Empty until the start hour returns. Occupied may stay.
F5_DEAD_WINDOW_UTC_HOURS = _DeadHours()

#: Named HIGH window. The minutes are the score. Occupied thesis may stay.
F5_HIGH_PRE_MIN = F5_HIGH_PRE_MINUTES
F5_HIGH_POST_MIN = F5_HIGH_POST_MINUTES

#: Weekend flatten is 20:30 UTC. Do not open Friday NY so late that flatten is the plan.
#: Overlap edge ends 16:00 UTC. Crypto 24/7 is exempt from this entry cutoff.
F5_FRIDAY_NEW_RISK_CUTOFF_UTC = None

#: After an SL-class close: FX DSP majors wait 4h (26 Aug GBP/USDJPY stacks). Metals/index
#: keep the 15-minute microstructure sibling only (gold/US30 isolated re-entry paid).
F5_FX_SL_COOLDOWN_HOURS = _Score("fx_sl_cooldown_hours", "hours")
F5_METAL_INDEX_SIBLING_MINUTES = _Score("sibling_window_minutes", "minutes")
#: The week-repair pick, not every FX major. AUD/NZD crosses stay on the 15-minute sibling.
F5_FX_DSP_SL_COOLDOWN_SYMBOLS = frozenset({
    "USDJPY", "GBPUSD", "EURUSD", "USDCHF", "USDCAD", "EURGBP", "GBPJPY", "EURJPY",
})

#: 5-pip preorder floor still fired. 58 FX tickets with stop <=8 pip = -$4,387.
F5_FX_DSP_MIN_STOP_PIPS = _Score("fx_min_stop_pips", "pips")

#: J6 2026-09-02: EUR/GBP/USDJPY dsp at 8-pip floor, 2y, spread-adjusted mean R < 0.
#: Drop those three from dsp. Live EURUSD/GBPUSD tickets are xa_*, not dsp — do not flatten.
#: USDJPY is already a standing HOLD. Other FX still hit the 8-pip floor.
F5_FX_DSP_DROP_SYMBOLS = frozenset({"EURUSD", "GBPUSD", "USDJPY"})

#: J5 idxrev H4 2019–2026: GER40 and US30 mean R < 0 at 0.75R. OFF those symbols.
#: Keep idxrev tag (US500 live 180622571, UK100/JP225 KEEP). Do not ban US500 from mood.
#: Live GER40 is mx_ger40_cash, not idxrev — do not remint around that ticket.
F5_IDXREV_OFF_SYMBOLS = frozenset({"GER40", "US30"})

F5_PAID_CLUSTER_SYMBOLS = frozenset({"US30", "XAUUSD"})
F5_PAID_CLUSTER_SLEEVES = frozenset({
    "dsp_expanding_up_staircase",
    "dsp_wide_down_then_micro_bounce_then_through",
    "dsp_bleed_accept_fresh_20low_second_push",
    "metal_session_reversion",
    "liq_asia_up_low_metal",
    "xa_isolated_opposite",
    "dsp_close_on_20low_not_a_cascade_then_up",
    "dsp_london_two_up_into_20high_reverses",
})
F5_MIN_STOP_TICKS = _Score("min_stop_ticks", "ticks")

F5_FX_MAJOR_SYMBOLS = frozenset({
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "EURGBP",
    "GBPJPY", "EURJPY", "AUDUSD", "NZDUSD", "AUDJPY", "NZDJPY",
    "CADJPY", "CHFJPY", "EURCHF", "GBPCHF",
})
F5_METAL_INDEX_SYMBOLS = frozenset({
    "XAUUSD", "XAGUSD", "US30", "UK100", "GER40", "SPX500", "US500",
    "US100", "NAS100", "JP225", "FRA40", "EU50",
})
F5_USD_HIGH_SYMBOLS = frozenset({
    "US30", "US500", "SPX500", "US100", "NAS100", "XAUUSD", "XAGUSD",
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "GER40", "UK100", "JP225",
})
F5_EUR_HIGH_SYMBOLS = frozenset({
    "EURUSD", "EURGBP", "EURJPY", "GER40", "FRA40", "EU50",
})
F5_JPY_HIGH_SYMBOLS = frozenset({
    "USDJPY", "EURJPY", "GBPJPY", "CADJPY", "CHFJPY", "NZDJPY", "AUDJPY", "JP225",
})
F5_GBP_HIGH_SYMBOLS = frozenset({
    "GBPUSD", "EURGBP", "GBPJPY", "UK100",
})
F5_HIGH_NAME_NEEDLES = (
    "warsh", "jackson hole", "fed chair", "fomc", "powell",
    "cpi", "nfp", "nonfarm", "non-farm", "payroll",
    "rate decision", "interest rate", "ecb rate", "boj rate",
)
F5_SL_CLOSE_MARKERS = (
    "sl", "[sl", "stop_loss", "stop-out", "stopped",
    "broker_closed_absent_on_reconcile",
)

_F5_HIGH_CACHE: dict[str, Any] = {"mtime": None, "rows": ()}
_F5_LIVE_CAL_CACHE: dict[str, Any] = {"key": None, "rows": None}


def f5_norm_symbol(symbol: object) -> str:
    """Canonical F5 symbol id. ``US30.cash``, ``US30_cash`` and ``US30`` are one symbol."""
    raw = str(symbol or "").upper().strip()
    for suffix in (".CASH", "_CASH"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)]
    return raw.replace(".", "")


def f5_aware_utc(value: object) -> Optional[datetime]:
    """datetime or ISO -> aware UTC. None on garbage. Never raises."""
    try:
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        text = str(value or "").strip()
        if not text:
            return None
        if "T" in text:
            text = text.split()[0]
        text = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def f5_event_scheduled_utc(row: Mapping[str, Any] | None) -> Optional[datetime]:
    """Parse a calendar/brief/spine row. Handles scheduled_utc ISO, date+HH:MM, and brief ``next``."""
    if not isinstance(row, Mapping):
        return None
    for key in ("scheduled_utc", "datetime_utc", "released_utc"):
        parsed = f5_aware_utc(row.get(key))
        if parsed is not None:
            return parsed
    raw_time = row.get("time_utc") or row.get("time") or row.get("datetime")
    parsed = f5_aware_utc(raw_time)
    if parsed is not None:
        return parsed
    date = str(row.get("date") or "").strip()
    clock = str(raw_time or "").strip()
    if date and clock:
        if len(clock) == 5:
            clock = clock + ":00"
        parsed = f5_aware_utc(f"{date}T{clock}Z")
        if parsed is not None:
            return parsed
    nxt = str(row.get("next") or "").strip()
    if nxt:
        head = nxt.split()[0] if nxt else ""
        # Date ranges like 2026-09-09/10 are not a clock. Need a real ISO instant.
        if "T" in head:
            parsed = f5_aware_utc(head)
            if parsed is not None:
                return parsed
    return None


def f5_symbol_currencies(symbol: object) -> frozenset:
    """Calendar-relevant currencies for one candidate symbol."""
    sym = f5_norm_symbol(symbol)
    if not sym:
        return frozenset()
    if sym in F5_INDEX_CCY:
        return frozenset({F5_INDEX_CCY[sym]})
    if sym.startswith(("UKOIL", "USOIL", "XBR", "XTI", "WTI", "BRENT", "NGAS", "XNG")):
        return frozenset({"USD"})
    out: set[str] = set()
    if len(sym) >= 6:
        base, quote = sym[:3], sym[3:6]
        if base in _F5_CRYPTO_BASES or sym[:4] in _F5_CRYPTO_BASES:
            out.add("USD")
        else:
            if base in _F5_CCY_CODES:
                out.add(base)
            if quote in _F5_CCY_CODES:
                out.add(quote)
    if not out and len(sym) >= 3 and sym[-3:] in _F5_CCY_CODES:
        out.add(sym[-3:])
    return frozenset(out)


def f5_in_dead_window(now: object) -> bool:
    """True when the hour is inside the returned thin window. Unset is not a window."""
    clock = f5_aware_utc(now)
    if clock is None:
        return False
    return clock.hour in F5_DEAD_WINDOW_UTC_HOURS


def f5_friday_weekend_cutoff_reason(symbol: object, now: object) -> Optional[str]:
    """Friday past the returned new-risk clock. Unset does not restore a clock.

    Crypto (``F5_ALWAYS_OPEN_SYMBOLS``) is exempt — the market does not close.
    """
    clock = f5_aware_utc(now)
    if clock is None or clock.weekday() != 4:
        return None
    if f5_norm_symbol(symbol) in F5_ALWAYS_OPEN_SYMBOLS:
        return None
    pair = _friday_cutoff_pair()
    if pair is None:
        return None
    hh, mm = pair
    if (clock.hour, clock.minute, clock.second, clock.microsecond) >= (int(hh), int(mm), 0, 0):
        return "f5_friday_weekend_cutoff"
    return None


def _f5_event_blob(row: Mapping[str, Any]) -> str:
    parts = (
        row.get("event_type"), row.get("event"), row.get("name"),
        row.get("what"), row.get("role"), row.get("family"),
    )
    return " ".join(str(p or "") for p in parts).lower()


def f5_event_is_warsh_class(row: Mapping[str, Any] | None) -> bool:
    """Fed speakers / FOMC / CPI / NFP / rates. Not GDP, not claims, not agenda drop."""
    if not isinstance(row, Mapping):
        return False
    blob = _f5_event_blob(row)
    if any(tok in blob for tok in _F5_WARSH_EXCLUDE):
        return False
    et = str(row.get("event_type") or "").strip().lower()
    if et in F5_WARSH_CLASS_EVENT_TYPES:
        return True
    if "cpi" in blob or "hicp" in blob:
        impact = str(row.get("impact") or "").strip().lower()
        if bool(row.get("official_high")) or impact in {"high", "3", "red"} or et == "cpi":
            return True
    impact = str(row.get("impact") or "").strip().lower()
    official = bool(row.get("official_high"))
    if official or impact in {"high", "3", "red"}:
        if any(tok in blob for tok in _F5_WARSH_NEEDLES):
            return True
    # news_brief.absent_next_48h rows have a `what` and often no impact flag.
    what = str(row.get("what") or "").lower()
    if what and any(tok in what for tok in ("nfp", "non-farm", "nonfarm", "cpi", "fomc", "fed chair", "rate decision")):
        if f5_event_scheduled_utc(row) is not None:
            return True
    return False


def f5_event_touches_symbol(row: Mapping[str, Any] | None, symbol: object) -> bool:
    """Gate by THIS candidate symbol. Occupancy of other names is irrelevant."""
    if not isinstance(row, Mapping):
        return False
    sym = f5_norm_symbol(symbol)
    if not sym:
        return False
    named: list[str] = []
    for key in ("tickets", "symbols", "touches_symbols", "symbols_guess"):
        val = row.get(key)
        if isinstance(val, list):
            named.extend(f5_norm_symbol(s) for s in val)
    if sym in {s for s in named if s}:
        return True
    ccy = str(row.get("currency") or "").strip().upper()
    if ccy == "ALL":
        return True
    if ccy and ccy in f5_symbol_currencies(sym):
        return True
    if ccy == "USD" and f5_event_is_warsh_class(row) and sym in F5_USD_HIGH_EXTRA_SYMBOLS:
        return True
    # USD Warsh-class with no currency (brief rows): still USD-risk via extra + USD legs.
    if not ccy and f5_event_is_warsh_class(row):
        if "USD" in f5_symbol_currencies(sym) or sym in F5_USD_HIGH_EXTRA_SYMBOLS:
            return True
    return False


def f5_named_high_window_reason(
    symbol: object,
    now: object,
    events: Iterable[Mapping[str, Any]] | None,
) -> Optional[str]:
    """Block NEW fills inside the returned pre/post of a Warsh-class event that touches ``symbol``.

    An unset pre or post does not restore a window.
    """
    clock = f5_aware_utc(now)
    if clock is None:
        return None
    pre = _returned("high_pre_minutes")
    post = _returned("high_post_minutes")
    if pre is None or post is None:
        return None
    closest = None
    closest_name = None
    closest_delta = None
    for row in events or ():
        if not isinstance(row, Mapping):
            continue
        if not f5_event_is_warsh_class(row):
            continue
        when = f5_event_scheduled_utc(row)
        if when is None:
            continue
        if not f5_event_touches_symbol(row, symbol):
            continue
        delta_min = (clock - when).total_seconds() / 60.0
        if -pre <= delta_min <= post:
            mag = abs(delta_min)
            if closest is None or mag < abs(closest_delta or 0.0):
                closest = row
                closest_delta = delta_min
                closest_name = str(row.get("event") or row.get("name") or row.get("what") or "high")
    if closest is None:
        return None
    return "f5_named_high_window"


def f5_calendar_prime_window_reason(
    symbol: object,
    now: object,
    events: Iterable[Mapping[str, Any]] | None,
) -> Optional[str]:
    """Amplifier, not a gate. Warsh-class print in T−45 .. T−0 that touches ``symbol``.

    Does not block. An unset pre does not restore a window and does not size.
    """
    clock = f5_aware_utc(now)
    if clock is None:
        return None
    pre = _returned("calendar_prime_pre_minutes")
    if pre is None:
        return None
    closest = None
    closest_delta = None
    for row in events or ():
        if not isinstance(row, Mapping):
            continue
        if not f5_event_is_warsh_class(row):
            continue
        when = f5_event_scheduled_utc(row)
        if when is None:
            continue
        if not f5_event_touches_symbol(row, symbol):
            continue
        delta_min = (clock - when).total_seconds() / 60.0
        if -pre <= delta_min <= 0.0:
            mag = abs(delta_min)
            if closest is None or mag < abs(closest_delta or 0.0):
                closest = row
                closest_delta = delta_min
    if closest is None:
        return None
    return "f5_calendar_prime_window"


def _closest_high(
    symbol: object,
    now: object,
    events: Iterable[Mapping[str, Any]] | None,
) -> tuple[float, str] | None:
    """Nearest Warsh-class event that touches ``symbol``, as minutes from the clock."""

    clock = f5_aware_utc(now)
    if clock is None:
        return None
    closest_delta = None
    closest_name = None
    for row in events or ():
        if not isinstance(row, Mapping):
            continue
        if not f5_event_is_warsh_class(row):
            continue
        when = f5_event_scheduled_utc(row)
        if when is None or not f5_event_touches_symbol(row, symbol):
            continue
        delta_min = (clock - when).total_seconds() / 60.0
        mag = abs(delta_min)
        if closest_delta is None or mag < abs(closest_delta):
            closest_delta = delta_min
            closest_name = str(row.get("event") or row.get("name") or row.get("what") or "high")
    if closest_delta is None:
        return None
    return float(closest_delta), str(closest_name or "high")


def f5_new_risk_clock_block_reason(
    symbol: object,
    now: object,
    events: Iterable[Mapping[str, Any]] | None = None,
) -> Optional[str]:
    """Writer NEW-risk clock. Each blocking fact is a Choice. Positions stay open."""
    try:
        clock = f5_aware_utc(now)
        hour = None if clock is None else int(clock.hour)
        minute = None if clock is None else int(clock.minute)
        dead_state: dict[str, object] = {
            "hour_utc": hour,
            "minute_utc": minute,
            "namespace": "operator",
        }
        start = _returned("dead_window_start_hour")
        if start is not None:
            dead_state["returned_dead_window_start_hour"] = int(start)
            dead_state["dead_window_fact"] = f5_in_dead_window(now)
        if fear_withholds(
            "f5_dead_window",
            dead_state,
            {
                "hour_is_a_fact": "The hour is a clock fact. It does not by itself mute the candidate.",
                "dead_hour_mute": "Do not send this candidate because the hour is in the thin window.",
            },
            "dead_hour_mute",
            f"f5_dead_window|{hour}",
            "The clock hour is on the card. A returned start hour is a fact only when it is present. Is this hour only a fact, or a reason not to send this candidate? Do not close an open ticket.",
        ):
            return "f5_dead_window"
        friday = clock is not None and clock.weekday() == 4
        if friday and f5_norm_symbol(symbol) not in F5_ALWAYS_OPEN_SYMBOLS:
            friday_state: dict[str, object] = {
                "symbol": str(symbol or ""),
                "friday_fact": True,
                "hour_utc": hour,
                "minute_utc": minute,
                "namespace": "operator",
            }
            pair = _friday_cutoff_pair()
            if pair is not None:
                friday_state["returned_friday_cutoff_utc"] = f"{pair[0]:02d}:{pair[1]:02d}"
                friday_state["past_returned_cutoff"] = (
                    f5_friday_weekend_cutoff_reason(symbol, now) is not None
                )
            if fear_withholds(
                "f5_friday_weekend_cutoff",
                friday_state,
                {
                    "friday_is_a_fact": "Friday is a calendar fact. The candidate can still be the fire.",
                    "weekend_cutoff_mute": "Do not send this candidate because Friday is past the cutoff.",
                },
                "weekend_cutoff_mute",
                f"f5_friday|{symbol}|{hour}",
                "It is Friday for this symbol. A returned cutoff is a fact only when it is present. Is that only a calendar fact, or a reason not to send? Do not flatten an open ticket.",
            ):
                return "f5_friday_weekend_cutoff"
        closest = _closest_high(symbol, now, events)
        if closest is not None:
            delta, _name = closest
            high_state: dict[str, object] = {
                "symbol": str(symbol or ""),
                "nearest_high_delta_min": float(delta),
                "namespace": "operator",
            }
            pre = _returned("high_pre_minutes")
            post = _returned("high_post_minutes")
            if pre is not None and post is not None:
                high_state["returned_pre_minutes"] = float(pre)
                high_state["returned_post_minutes"] = float(post)
                high_state["inside_returned_window"] = (
                    -float(pre) <= float(delta) <= float(post)
                )
            if fear_withholds(
                "f5_named_high_window",
                high_state,
                {
                    "send_through_the_window": "A named high is on the card and this candidate is still the fire.",
                    "named_high_inside_window": "Do not send this candidate because a named high for this symbol withholds.",
                },
                "named_high_inside_window",
                f"f5_named_high|{symbol}|{hour}",
                "A named high for this symbol is on the card, with the minutes from the clock. A returned window is a fact only when it is present. Is this candidate still the fire, or does that high withhold the send? An empty calendar is not this question. Do not close an open ticket.",
            ):
                return "f5_named_high_window"
        return None
    except Exception:
        return None




def f5_live_calendar_paths(repo_root: object | None = None) -> list[Path]:
    """Live sources the writer reads. news_tape is intentionally absent."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    intel = F5_INTEL_CALENDAR_DIR
    return [
        intel / "news_brief.json",
        intel / "official_high_spine.json",
        root / "data" / "official_high_spine.json",
        root / "data" / "news_brief.json",
        root / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "news_brief.json",
        # CONTRACT V2: the chair's HIGH calendar was written for the judge only; the writer reads it too.
        root / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "state" / "f5_high_calendar.json",
        root / "data" / "news_calendar.json",
    ]


def _f5_iter_raw_calendar_rows(doc: object) -> Iterable[Mapping[str, Any]]:
    if isinstance(doc, list):
        for row in doc:
            if isinstance(row, Mapping):
                yield row
        return
    if not isinstance(doc, Mapping):
        return
    for key in ("events", "calendar", "rows", "data"):
        val = doc.get(key)
        if isinstance(val, list):
            for row in val:
                if isinstance(row, Mapping):
                    yield row
    absent = doc.get("absent_next_48h")
    if isinstance(absent, list):
        for row in absent:
            if isinstance(row, Mapping):
                yield row


def f5_normalize_calendar_row(row: Mapping[str, Any], *, source: str = "") -> Optional[dict]:
    """One writer-readable event. None if untimed."""
    when = f5_event_scheduled_utc(row)
    if when is None:
        return None
    name = str(row.get("event") or row.get("name") or row.get("what") or "unknown")
    impact = str(row.get("impact") or "").strip() or ("HIGH" if row.get("official_high") else "")
    tickets = []
    for key in ("tickets", "symbols", "touches_symbols"):
        val = row.get(key)
        if isinstance(val, list):
            tickets.extend(f5_norm_symbol(s) for s in val if f5_norm_symbol(s))
    seen: set[str] = set()
    uniq = []
    for t in tickets:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    et = str(row.get("event_type") or "").strip()
    if not et and row.get("what"):
        blob = str(row.get("what") or "").lower()
        if "nfp" in blob or "non-farm" in blob or "nonfarm" in blob:
            et = "nfp"
        elif "cpi" in blob:
            et = "cpi"
        elif "fomc" in blob:
            et = "fomc_decision"
    iso = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    official = bool(row.get("official_high")) or str(impact).upper() == "HIGH"
    return {
        "name": name,
        "event": name,
        "scheduled_utc": iso,
        "time_utc": iso,
        "date": when.date().isoformat(),
        "impact": impact.upper() if impact else ("HIGH" if official else ""),
        "currency": str(row.get("currency") or "").upper(),
        "event_type": et,
        "official_high": official,
        "tickets": uniq,
        "source": source or str(row.get("source") or ""),
        "source_url": row.get("source_url") or row.get("url"),
        "what": row.get("what"),
        "role": row.get("role"),
        "family": row.get("family"),
    }


def f5_load_live_calendar_events(
    repo_root: object | None = None,
    extra_paths: Iterable[object] | None = None,
) -> list[dict]:
    """Merge news_brief + official_high_spine + news_calendar. Deduped. Never raises."""
    paths: list[Path] = []
    seen_path: set[str] = set()
    for raw in list(f5_live_calendar_paths(repo_root)) + list(extra_paths or ()):
        try:
            p = Path(raw)
        except (TypeError, ValueError):
            continue
        key = str(p)
        if key in seen_path:
            continue
        seen_path.add(key)
        paths.append(p)
    mtimes: list[float] = []
    for path in paths:
        try:
            mtimes.append(path.stat().st_mtime)
        except OSError:
            mtimes.append(-1.0)
    cache_key = (tuple(str(p) for p in paths), tuple(mtimes))
    if extra_paths is None and _F5_LIVE_CAL_CACHE.get("key") == cache_key:
        return list(_F5_LIVE_CAL_CACHE.get("rows") or [])
    out: dict[tuple[str, str], dict] = {}
    for path in paths:
        try:
            if not path.is_file():
                continue
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        source = path.name
        for raw in _f5_iter_raw_calendar_rows(doc):
            row = f5_normalize_calendar_row(raw, source=source)
            if row is None:
                continue
            key = (str(row.get("scheduled_utc")), str(row.get("name") or "").lower())
            prev = out.get(key)
            if prev is None:
                out[key] = row
                continue
            # Prefer news_brief (live speakers) over frozen news_calendar.
            if prev.get("source") == "news_calendar.json" and source == "news_brief.json":
                out[key] = row
            elif source == "news_brief.json" and not prev.get("tickets") and row.get("tickets"):
                prev["tickets"] = row["tickets"]
                if not prev.get("official_high"):
                    prev["official_high"] = row.get("official_high")
    rows = sorted(out.values(), key=lambda r: str(r.get("scheduled_utc")))
    if extra_paths is None:
        _F5_LIVE_CAL_CACHE["key"] = cache_key
        _F5_LIVE_CAL_CACHE["rows"] = rows
    return list(rows)


def f5_compose_official_high_spine(
    repo_root: object | None = None,
    *,
    now: object = None,
    extra_paths: Iterable[object] | None = None,
) -> dict:
    """Warsh-class HIGH spine the writer actually reads. Merges brief + calendar.

    Does not read official_high_spine.json (that file is the OUTPUT). Recycling
    it would keep invented clocks (ECB ``2026-09-09/10`` stamped 10:00Z).
    """
    clock = f5_aware_utc(now) or datetime.now(timezone.utc)
    lookback_days = _returned("calendar_lookback_days")
    horizon_days = _returned("calendar_horizon_days")
    lookback = None if lookback_days is None else clock - timedelta(days=float(lookback_days))
    horizon = None if horizon_days is None else clock + timedelta(days=float(horizon_days))
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    intel = F5_INTEL_CALENDAR_DIR
    compose_paths = [
        intel / "news_brief.json",
        root / "data" / "news_brief.json",
        root / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "news_brief.json",
        root / "data" / "news_calendar.json",
    ]
    if extra_paths:
        compose_paths.extend(Path(p) for p in extra_paths)
    events = []
    seen: set[tuple] = set()
    raw_rows: list[dict] = []
    seen_path: set[str] = set()
    for path in compose_paths:
        key = str(path)
        if key in seen_path or not path.is_file():
            continue
        seen_path.add(key)
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        for raw in _f5_iter_raw_calendar_rows(doc):
            row = f5_normalize_calendar_row(raw, source=path.name)
            if row is not None:
                raw_rows.append(row)
    for row in raw_rows:
        if not f5_event_is_warsh_class(row):
            continue
        when = f5_event_scheduled_utc(row)
        if when is None:
            continue
        if lookback is not None and when < lookback:
            continue
        if horizon is not None and when > horizon:
            continue
        ident = (str(row.get("scheduled_utc")), str(row.get("name") or "").lower())
        if ident in seen:
            continue
        seen.add(ident)
        events.append({
            "name": row.get("name"),
            "impact": row.get("impact") or "HIGH",
            "official_high": True,
            "scheduled_utc": row.get("scheduled_utc"),
            "currency": row.get("currency") or None,
            "event_type": row.get("event_type") or None,
            "family": row.get("family") or "economic",
            "role": row.get("role") or "print",
            "source_url": row.get("source_url"),
            "source": row.get("source") or "live_merge",
            "tickets": row.get("tickets") or [],
        })
    events.sort(key=lambda e: str(e.get("scheduled_utc") or ""))
    return {
        "schema": "gtos.news.official_high_spine.v1",
        "extracted_utc": clock.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "composer": "f5_compose_official_high_spine",
        "note": (
            "Warsh-class merge: news_brief official_high + Fed/CPI/NFP/rates "
            "from news_calendar. news_tape is not a source."
        ),
        "events": events,
    }


def f5_sleeve_name(family: object) -> str:
    text = str(family or "").strip()
    if not text:
        return ""
    lower = text.lower()
    for name in F5_HARD_OFF_SLEEVES:
        if name in lower:
            return name
    if text.startswith("F5:") or text.startswith("f5:"):
        text = text.split(":", 1)[-1]
    if "::" in text:
        parts = [p for p in text.split("::") if p]
        if text.upper().startswith("LAUNCHER::") and len(parts) >= 3:
            return parts[2]
        return parts[-1]
    if ":" in text:
        text = text.split(":")[-1]
    return text.strip()


def f5_hard_off_sleeve_reason(family: object, namespace: object = None) -> str | None:
    """Membership in the hard-off set is a fact. On Challenge the Choice decides."""
    sleeve = f5_sleeve_name(family)
    lower = str(family or "").lower()
    fact = False
    if sleeve in F5_HARD_OFF_SLEEVES:
        fact = True
    elif "asia_pdl_fade" in lower:
        fact = True
    elif "climax" in lower and "flush" in lower:
        fact = True
    elif "isolated_flush" in lower:
        fact = True
    elif sleeve.startswith("dsp_bleed") or "dsp_bleed" in lower:
        fact = True
    elif sleeve.startswith("orb_crypto") or "orb_crypto" in lower:
        fact = True
    elif sleeve.startswith("xa_huge") or "xa_huge" in lower:
        fact = True
    elif sleeve == "idxrev" or lower.strip() == "idxrev" or lower.endswith(":idxrev"):
        fact = True
    if not fact:
        return None
    if str(namespace or "") != "operator":
        return "hard_off_sleeve"
    if fear_withholds(
        "f5_hard_off_sleeve",
        {"sleeve": sleeve, "hard_off_fact": True, "namespace": "operator"},
        {
            "sleeve_is_the_fire": "This sleeve's pattern on this bar is the fire. The hard-off name is only a fact.",
            "hard_off_stands": "Do not send this sleeve. The hard-off fact stands for this bar.",
        },
        "hard_off_stands",
        f"f5_hard_off_sleeve|{sleeve}|{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%d%H')}",
        "This sleeve is on the hard-off list. Is the sleeve the fire on this bar, or does that list stand? Do not close an open ticket.",
    ):
        return "hard_off_sleeve"
    return None




def f5_is_fx_major(symbol: object) -> bool:
    return f5_norm_symbol(symbol) in F5_FX_MAJOR_SYMBOLS


def f5_is_metal_or_index(symbol: object) -> bool:
    return f5_norm_symbol(symbol) in F5_METAL_INDEX_SYMBOLS


def f5_is_sl_class_close(close_action: object) -> bool:
    """True for stop-outs. Picks the 4h FX cooldown vs the 15-minute sibling."""
    row = close_action if isinstance(close_action, Mapping) else None
    if row is not None:
        parts = [
            str(row.get(key) or "")
            for key in ("close_action", "reason", "action", "comment", "deal_comment")
        ]
        blob = " ".join(parts).strip().lower()
        if "take_profit" in blob or "target hit" in blob:
            return False
        try:
            realised = row.get("realised_r")
            adverse = _returned("sl_class_adverse_r")
            if (
                realised is not None
                and adverse is not None
                and float(realised) <= -float(adverse)
            ):
                return True
        except (TypeError, ValueError):
            pass
        try:
            pnl = row.get("broker_net_pnl_usd")
            if pnl is not None and float(pnl) < 0 and "weekend" not in blob:
                return True
        except (TypeError, ValueError):
            pass
        text = blob
    else:
        text = str(close_action or "").strip().lower()
    if not text:
        return False
    if "take_profit" in text or "weekend_flat" in text:
        return False
    return any(marker in text for marker in F5_SL_CLOSE_MARKERS)


def f5_intended_risk_usd(symbol: object = None, sleeve: object = None, default: float | None = None) -> float:
    """Launch may pass a printed number so the process can start.

    That number is not the decision. A missing or non-finite default is
    not replaced with a printed cash amount.
    """
    try:
        fallback = float(default) if default is not None else None
    except (TypeError, ValueError):
        return 0.0
    if fallback is None or not math.isfinite(fallback) or fallback <= 0:
        return 0.0
    return fallback


def _f5_as_utc(now: object) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if isinstance(now, datetime):
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def f5_is_cash_fx(symbol: object) -> bool:
    if f5_is_fx_major(symbol):
        return True
    sym = f5_norm_symbol(symbol)
    if len(sym) != 6 or not sym.isalpha():
        return False
    return not any(tag in sym for tag in ("XAU", "XAG", "XPT", "XPD"))


def f5_fx_dsp_stop_pips(symbol: object, stop_dist: object, pip: object = None) -> float | None:
    try:
        dist = float(stop_dist)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(dist) or dist <= 0:
        return None
    pip_size = None
    if pip is not None:
        try:
            pip_size = float(pip)
        except (TypeError, ValueError):
            pip_size = None
    if pip_size is None or not math.isfinite(pip_size) or pip_size <= 0:
        if not f5_is_cash_fx(symbol):
            return None
        pip_size = 0.01 if f5_norm_symbol(symbol).endswith("JPY") else 0.0001
    elif not f5_is_cash_fx(symbol):
        return None
    return dist / pip_size


def _spot_withholds(question, state, withhold, allow, cache_key, instructions):
    """Two sides of one condition. The unique highest probability decides.

    ``withhold`` is the side that used to be the true branch. An empty answer,
    a tie, or any other winner does not restore that branch. There is no
    absent side.
    """
    withhold_name, withhold_text = withhold
    allow_name, allow_text = allow
    return fear_withholds(
        question,
        state,
        {allow_name: allow_text, withhold_name: withhold_text},
        withhold_name,
        cache_key,
        instructions + " Do not flatten ticket 294215389.",
    )


def f5_idxrev_symbol_off_reason(
    namespace: str,
    symbol: object,
    family: object = None,
) -> str | None:
    """J5: idxrev stays on tags. GER40 and US30 are a fact. The Choice decides."""
    if str(namespace or "") != F5_NAMESPACE:
        return None
    fam = str(family or "").lower()
    if "idxrev" not in fam:
        return None
    sym = f5_norm_symbol(symbol)
    if not sym:
        return None
    if sym in F5_IDXREV_OFF_SYMBOLS or any(sym.startswith(s) for s in F5_IDXREV_OFF_SYMBOLS):
        if _spot_withholds(
            "idxrev_j5_off",
            {"symbol": sym, "sleeve": str(family or ""), "idxrev_off_fact": True, "namespace": F5_NAMESPACE},
            ("idxrev_off_stands", "Do not send idxrev on this symbol. The off-list fact stands for this bar."),
            ("symbol_is_the_fire", "This symbol is on the idxrev off list. That list is only a fact. This bar can still be the fire."),
            f"idxrev_j5_off|{sym}|{family}",
            "idxrev printed on GER40 or US30. Is the off list the decision, or is this bar the fire?",
        ):
            return "idxrev_j5_off"
    return None


def f5_fx_dsp_tight_stop_reason(
    namespace: str,
    symbol: object,
    family: object = None,
    stop_dist: object = None,
    sl: object = None,
    entry: object = None,
) -> str | None:
    if str(namespace or "") != F5_NAMESPACE:
        return None
    if not f5_is_dsp_family(family):
        return None
    sym = f5_norm_symbol(symbol)
    if sym in F5_FX_DSP_DROP_SYMBOLS:
        if fear_withholds(
            "fx_dsp_dropped_j6",
            {
                "symbol": sym,
                "sleeve": str(family or ""),
                "in_drop_set": True,
                "namespace": "operator",
            },
            {
                "pattern_is_the_fire": "This sleeve's pattern on this symbol is the fire on this bar.",
                "pattern_absent": "The pattern this sleeve requires is not on this bar.",
            },
            "pattern_absent",
            f"fx_dsp_dropped_j6|{sym}|{family}",
            "A DSP sleeve printed on a symbol that an old study dropped. Is this bar's pattern the fire, or is the pattern absent? Do not close ticket 294215389.",
        ):
            return "fx_dsp_dropped_j6"
    dist = stop_dist
    if dist in (None, "", 0, "0"):
        try:
            entry_f = float(entry)
            sl_f = float(sl)
            dist = abs(entry_f - sl_f)
        except (TypeError, ValueError):
            dist = None
    pips = f5_fx_dsp_stop_pips(symbol, dist)
    if pips is None:
        return None
    stop_state: dict[str, object] = {
        "symbol": sym,
        "sleeve": str(family or ""),
        "stop_pips": float(pips),
        "namespace": "operator",
    }
    floor = _returned("fx_min_stop_pips")
    if floor is None:
        return None
    stop_state["returned_min_stop_pips"] = float(floor)
    stop_state["at_or_under_returned"] = float(pips) <= float(floor)
    if fear_withholds(
        "fx_dsp_stop_le_8pip",
        stop_state,
        {
            "stop_is_the_plan": "This stop width is the plan for this bar.",
            "eight_pip_cliff": "This stop sits on the cliff. Do not send.",
        },
        "eight_pip_cliff",
        f"fx_dsp_stop_le_8pip|{sym}|{family}|{round(float(pips), 4)}",
        "This DSP stop width in pips is on the card. A returned minimum is a fact only when it is present. Is this stop the plan, or is the cliff the decision? Do not close ticket 294215389.",
    ):
        return "fx_dsp_stop_le_8pip"
    return None




def f5_trade_symbol(trade_params: Mapping | None) -> str:
    if not isinstance(trade_params, Mapping):
        return ""
    raw = trade_params.get("symbol")
    if raw:
        return str(raw)
    details = trade_params.get("gtos_vnext_source_event_details")
    if isinstance(details, Mapping) and details.get("symbol"):
        return str(details.get("symbol"))
    return ""


def f5_trade_sleeve(trade_params: Mapping | None) -> str:
    if not isinstance(trade_params, Mapping):
        return ""
    raw = trade_params.get("sleeve")
    if raw:
        return str(raw)
    details = trade_params.get("gtos_vnext_source_event_details")
    if isinstance(details, Mapping) and details.get("sleeve"):
        return str(details.get("sleeve"))
    return ""


def f5_trade_stop_dist(trade_params: Mapping | None) -> float | None:
    if not isinstance(trade_params, Mapping):
        return None
    try:
        entry = float(trade_params.get("entry_price"))
        stop = float(trade_params.get("stop_loss"))
    except (TypeError, ValueError):
        return None
    dist = abs(entry - stop)
    if not math.isfinite(dist) or dist <= 0:
        return None
    return dist


def f5_lots_or_ticks_refuse_reason(
    *,
    lots: object = None,
    stop_dist: object = None,
    tick_size: object = None,
) -> str | None:
    try:
        lot_n = float(lots)
    except (TypeError, ValueError):
        lot_n = None
    try:
        dist = float(stop_dist)
        tick = float(tick_size)
    except (TypeError, ValueError):
        return None
    if dist <= 0 or tick <= 0 or not math.isfinite(dist) or not math.isfinite(tick):
        return None
    ticks = dist / tick
    tick_state: dict[str, object] = {
        "stop_ticks": float(ticks),
        "namespace": F5_NAMESPACE,
    }
    floor = _returned("min_stop_ticks")
    if floor is None:
        return None
    tick_state["returned_min_stop_ticks"] = float(floor)
    tick_state["at_or_under_returned"] = float(ticks) <= float(floor)
    if _spot_withholds(
        "f5_stop_ticks_le_8",
        tick_state,
        ("eight_tick_cliff", "This stop sits on the cliff. Do not send."),
        ("stop_is_the_plan", "This stop width in ticks is the plan for this bar."),
        f"f5_stop_ticks_le_8|{round(float(ticks), 4)}",
        "This stop width in ticks is on the card. A returned minimum is a fact only when it is present. Is this stop the plan, or is the cliff the decision?",
    ):
        return "f5_stop_ticks_le_8"
    return None


def _f5_parse_event_time(row: Mapping[str, Any]) -> datetime | None:
    """ISO, date+HH:MM, or brief ``next``. HH:MM alone is not a clock."""
    return f5_event_scheduled_utc(row)


def _f5_event_is_high(row: Mapping[str, Any]) -> bool:
    if row.get("official_high") is True:
        return True
    impact = str(row.get("impact") or row.get("importance") or "").strip().lower()
    if impact in ("high", "3", "red", "official_high"):
        return True
    name = str(row.get("name") or row.get("event") or row.get("title") or "").lower()
    return any(needle in name for needle in F5_HIGH_NAME_NEEDLES)


def _f5_event_affected_symbols(row: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    for key in ("tickets", "symbols", "affected_symbols"):
        val = row.get(key)
        if isinstance(val, (list, tuple, set)):
            out.update(f5_norm_symbol(x) for x in val if f5_norm_symbol(x))
        elif val:
            out.add(f5_norm_symbol(val))
    currency = str(row.get("currency") or row.get("ccy") or "").upper()
    name = str(row.get("name") or row.get("event") or row.get("title") or "").lower()
    event_type = str(row.get("event_type") or row.get("family") or "").lower()
    blob = " ".join((currency.lower(), name, event_type))
    usdish = any(n in blob for n in (
        "usd", "fomc", "fed", "warsh", "powell", "cpi", "nfp", "payroll",
        "jackson hole", "ces", "uom",
    ))
    eurish = any(n in blob for n in ("eur", "ecb"))
    jpyish = any(n in blob for n in ("jpy", "boj"))
    gbpish = any(n in blob for n in ("gbp", "boe", "uk "))
    if usdish or currency in {"USD", "US"}:
        out.update(F5_USD_HIGH_SYMBOLS)
    if eurish or currency == "EUR":
        out.update(F5_EUR_HIGH_SYMBOLS)
    if jpyish or currency == "JPY":
        out.update(F5_JPY_HIGH_SYMBOLS)
    if gbpish or currency == "GBP":
        out.update(F5_GBP_HIGH_SYMBOLS)
    return {s for s in out if s}


def _f5_load_json_rows(path: Path) -> list:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        rows: list = []
        for key in ("events", "calendar", "rows", "data", "absent_next_48h"):
            val = raw.get(key)
            if isinstance(val, list):
                rows.extend(r for r in val if isinstance(r, dict))
        return rows
    return []


def f5_high_calendar_paths(repo_root: object | None = None) -> list[Path]:
    if repo_root is None:
        root = Path(__file__).resolve().parents[3]
    else:
        root = Path(repo_root)
    return [
        Path(r"C:\Users\trader\intel-layer\calendar\official_high_spine.json"),
        Path(r"C:\Users\trader\intel-layer\calendar\news_brief.json"),
        root / "data" / "news_calendar.json",
        root / "pipeline_state" / "ultimate_book" / F5_NAMESPACE
        / "judgment" / "state" / "f5_high_calendar.json",
    ]


def f5_load_high_events(repo_root: object | None = None) -> list[dict]:
    """Warsh-class HIGH rows from brief + spine + VPS calendar. Reloads on mtime."""
    rows: list[dict] = []
    seen: set[tuple] = set()
    for row in f5_load_live_calendar_events(repo_root):
        if not f5_event_is_warsh_class(row):
            continue
        ts = f5_event_scheduled_utc(row)
        if ts is None:
            continue
        name = str(row.get("name") or row.get("event") or "")
        ident = (name.lower(), ts.isoformat())
        if ident in seen:
            continue
        seen.add(ident)
        rows.append({
            "name": name,
            "scheduled_utc": ts,
            "symbols": sorted(_f5_event_affected_symbols(row)),
            "source": row.get("source"),
            "impact": row.get("impact") or "HIGH",
            "official_high": True,
            "time_utc": row.get("time_utc") or row.get("scheduled_utc"),
            "event": name,
            "event_type": row.get("event_type"),
            "currency": row.get("currency"),
            "tickets": row.get("tickets") or [],
            "what": row.get("what"),
        })
    return rows


def f5_high_print_hold_reason(
    namespace: str,
    symbol: object,
    now: object = None,
    repo_root: object | None = None,
) -> str | None:
    """Named HIGH is a fact. The same Choice as the new-risk clock decides. No restored boolean."""
    if str(namespace or "") != F5_NAMESPACE:
        return None
    try:
        events = f5_load_live_calendar_events(repo_root)
    except Exception:
        return None
    closest = _closest_high(symbol, now, events)
    if closest is None:
        return None
    delta, _name = closest
    clock = f5_aware_utc(now)
    hour = None if clock is None else int(clock.hour)
    high_state: dict[str, object] = {
        "symbol": str(symbol or ""),
        "nearest_high_delta_min": float(delta),
        "namespace": "operator",
    }
    pre = _returned("high_pre_minutes")
    post = _returned("high_post_minutes")
    if pre is not None and post is not None:
        high_state["returned_pre_minutes"] = float(pre)
        high_state["returned_post_minutes"] = float(post)
        high_state["inside_returned_window"] = -float(pre) <= float(delta) <= float(post)
    if fear_withholds(
        "f5_named_high_window",
        high_state,
        {
            "send_through_the_window": "A named high is inside the window and this candidate is still the fire.",
            "named_high_inside_window": "Do not send this candidate because a named high for this symbol is inside the window.",
        },
        "named_high_inside_window",
        f"f5_named_high|{symbol}|{hour}",
        "A named high event for this symbol sits inside the pre/post window. Is this candidate still the fire, or does that window withhold the send? An empty calendar is not this question. Do not close an open ticket. Do not flatten ticket 294215389.",
    ):
        return "f5_named_high_window"
    return None


def f5_clock_hold_reason(
    namespace: str,
    symbol: object,
    now: object = None,
) -> str | None:
    """Dead window and Friday cutoff. The Choice decides. The old boolean does not return."""
    if str(namespace or "") != F5_NAMESPACE:
        return None
    try:
        return f5_new_risk_clock_block_reason(symbol, now, events=())
    except Exception:
        return None


def f5_r_versus_original(
    side: str,
    entry: float,
    orig_sl: float,
    mark: float,
) -> float | None:
    """Favourable R vs the *original* stop. Never vs a BE lock."""
    d = str(side or "").upper()
    try:
        entry_f = float(entry)
        orig_f = float(orig_sl)
        mark_f = float(mark)
    except (TypeError, ValueError):
        return None
    denom = abs(entry_f - orig_f)
    if not all(math.isfinite(v) for v in (entry_f, orig_f, mark_f, denom)):
        return None
    if denom <= 0:
        return None
    if d == "LONG":
        return (mark_f - entry_f) / denom
    if d == "SHORT":
        return (entry_f - mark_f) / denom
    return None


def f5_latch_orig_sl(
    side: str,
    entry: float,
    live_sl: float | None = None,
    stored: float | None = None,
) -> float | None:
    """Keep the first risk-side stop. Never treat a BE lock as the original.

    A stop on the profit side of entry is a lock. If we only see the lock
    (restart after BE, no ledger), refuse rather than print R=17.
    """
    d = str(side or "").upper()

    def _risk_side(sl: object) -> float | None:
        try:
            sl_f = float(sl)
            entry_f = float(entry)
        except (TypeError, ValueError):
            return None
        if not (math.isfinite(sl_f) and math.isfinite(entry_f) and sl_f > 0 and entry_f > 0):
            return None
        if d == "LONG" and sl_f < entry_f:
            return sl_f
        if d == "SHORT" and sl_f > entry_f:
            return sl_f
        return None

    kept = _risk_side(stored)
    if kept is not None:
        return kept
    return _risk_side(live_sl)


#: On-disk chair_card.py allowlist (scripts/f5_desk/chair_card.py). Writer cannot
#: import that package (chair_card already imports this module). Keep in lockstep.
F5_NULL_RULE_SLEEVES = frozenset({
    "crypto", "energy_agri", "sub_xvol_pullback", "metals_softband", "vol_compression",
})
F5_NULL_RULE_PREFIXES = ("mx_",)
F5_FAST_FAMILY_PREFIXES = ("dsp_", "xa_")
F5_FAST_FAMILY_SLEEVES = frozenset({"idxrev"})
F5_FX_FAMILY_SLEEVES = frozenset({"asian_fade", "asian_fade_widen"})
F5_FX_FAMILY_PREFIXES = ("fx_",)
F5_LEFTOVER_OPEN_STAY_REASON = "leftover-open_atlas_stay"


def f5_leftover_open_stay_ledger_path(
    repo_root: object | None = None,
    namespace: str = "operator",
) -> Path:
    """Same family as chair_orig_sl.json: judgment/state on the book namespace."""
    if repo_root is None:
        root = Path(__file__).resolve().parents[3]
    else:
        root = Path(repo_root)
    return (
        root / "pipeline_state" / "ultimate_book" / str(namespace)
        / "judgment" / "state" / "chair_leftover_open_stay.json"
    )


def f5_leftover_open_stay(ticket, ledger_path: object | None = None) -> bool:
    """True iff ticket is on the leftover-open Atlas-stay ledger.

    Writer-visible. Those tickets must not be flattened. Missing/unreadable
    ledger => False (cannot claim stay without the file). The take-off GATE
    still fails closed via good_level / tape_stopped.
    """
    try:
        if ticket in (None, "", 0, "0"):
            return False
        path = Path(ledger_path) if ledger_path is not None else f5_leftover_open_stay_ledger_path()
        if not path.is_file():
            return False
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        raw = doc.get("tickets") if isinstance(doc, dict) else None
        if not isinstance(raw, dict):
            return False
        try:
            key = str(int(ticket))
        except (TypeError, ValueError):
            key = str(ticket)
        entry = raw.get(key)
        if entry is None:
            return False
        if isinstance(entry, dict):
            reason = str(entry.get("reason") or "")
            if reason and reason != F5_LEFTOVER_OPEN_STAY_REASON:
                return False
            return True
        return bool(entry)
    except Exception:
        return False


def f5_is_fast_family(sleeve: object) -> bool:
    """Same allowlist as chair_card.is_fast_family. NULL-RULE is never fast."""
    s = str(sleeve or "")
    if s in F5_NULL_RULE_SLEEVES or s.startswith(F5_NULL_RULE_PREFIXES):
        return False
    if s.startswith(F5_FAST_FAMILY_PREFIXES) or s in F5_FAST_FAMILY_SLEEVES:
        return True
    if s.startswith(F5_FX_FAMILY_PREFIXES) or s in F5_FX_FAMILY_SLEEVES:
        return True
    return False


is_fast_family = f5_is_fast_family


def f5_good_level(*_args, **_kwargs) -> bool:
    """Symbol-units vs TF extreme/stall, still short of broker TP.

    FAIL CLOSED until a real implementation exists. Do not infer from R dump
    or quote age. Do not invent from entry CHoCH.
    """
    return False


def f5_tape_stopped(*_args, **_kwargs) -> bool:
    """Family range / displacement spent — move no longer extending.

    FAIL CLOSED until a real implementation exists. Do not use
    chair_card.tape_state (quote age). Do not use time_stop_bars.
    """
    return False


def f5_fast_family_takeoff_may_close(
    ticket=None,
    sleeve=None,
    symbol=None,
    *,
    ledger_path=None,
    **_kwargs,
) -> bool:
    """May come off ONLY if fast-family AND not leftover-open stay AND good_level AND tape_stopped.

    A may, not a must. Fail closed. Does not send. Does not call close.
    """
    if not f5_is_fast_family(sleeve):
        return False
    if f5_leftover_open_stay(ticket, ledger_path=ledger_path):
        return False
    if not f5_good_level(symbol=symbol, sleeve=sleeve, ticket=ticket):
        return False
    if not f5_tape_stopped(symbol=symbol, sleeve=sleeve, ticket=ticket):
        return False
    return True


def f5_norm_direction(direction: object) -> str | None:
    """LONG / SHORT or None. Intent uses +1/-1. Broker type 0 is buy."""
    if direction is None:
        return None
    if isinstance(direction, str):
        u = direction.strip().upper()
        if u in {"LONG", "BUY"}:
            return "LONG"
        if u in {"SHORT", "SELL"}:
            return "SHORT"
        return None
    try:
        i = int(direction)
    except (TypeError, ValueError):
        return None
    if i > 0:
        return "LONG"
    if i < 0:
        return "SHORT"
    return None


def f5_is_dsp_family(family: object) -> bool:
    text = str(family or "").lower()
    return "dsp_" in text or text.startswith("dsp")


def f5_is_eur_gbp_fx(symbol: object) -> bool:
    """Cash FX pair with an EUR or GBP leg. Not metals, not indices."""
    sym = f5_norm_symbol(symbol)
    if not sym:
        return False
    if any(tag in sym for tag in ("XAU", "XAG", "US30", "US500", "NAS", "GER40", "UK100", "JPN", "WS30", "SPX")):
        return False
    letters = "".join(c for c in sym if c.isalpha())
    if len(letters) < 6:
        return False
    a, b = letters[:3], letters[3:6]
    return a in {"EUR", "GBP"} or b in {"EUR", "GBP"}


def _f5_finite_level(value: object) -> float | None:
    """Broker 0.0 means unset. Refuse non-finite / non-positive prices."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v <= 0:
        return None
    return v


def f5_levels_lock(new: Mapping[str, Any], live: Mapping[str, Any]) -> bool:
    """True when a new ticket's SL/TP and a live/pending ticket lock.

    Same normalized symbol, opposite direction, all four of
    {new_tp, live_sl, live_tp, new_sl} finite. Conflict if reaching
    the new TP crosses the live SL (LONG new: new_tp >= live_sl;
    SHORT new: new_tp <= live_sl). Gold opposite live+limit is the case.
    """
    if not isinstance(new, Mapping) or not isinstance(live, Mapping):
        return False
    n_sym = f5_norm_symbol(new.get("symbol"))
    l_sym = f5_norm_symbol(live.get("symbol"))
    if not n_sym or n_sym != l_sym:
        return False
    n_dir = f5_norm_direction(new.get("direction") or new.get("side"))
    l_dir = f5_norm_direction(live.get("direction") or live.get("side"))
    if not n_dir or not l_dir or n_dir == l_dir:
        return False
    new_tp = _f5_finite_level(new.get("tp"))
    live_sl = _f5_finite_level(live.get("sl"))
    live_tp = _f5_finite_level(live.get("tp"))
    new_sl = _f5_finite_level(new.get("sl"))
    if None in (new_tp, live_sl, live_tp, new_sl):
        return False
    if n_dir == "LONG":
        return new_tp >= live_sl
    return new_tp <= live_sl


def f5_is_crypto_or_oil_symbol(symbol: object) -> bool:
    """F5 always-open crypto set, or oil (USOIL/UKOIL/WTI/BRENT/OIL)."""
    sym = f5_norm_symbol(symbol)
    if not sym:
        return False
    if sym in F5_ALWAYS_OPEN_SYMBOLS:
        return True
    return sym in {"USOIL", "UKOIL", "WTI", "BRENT", "OIL"}



F5_JUST_CLOSED_WINDOW_MINUTES = F5_METAL_INDEX_SIBLING_MINUTES


def f5_just_closed_siblings_path(
    repo_root: object | None = None,
    namespace: str = "operator",
) -> Path:
    """Same family as chair_orig_sl.json. Writer-readable twin of the chair file."""
    if repo_root is None:
        root = Path(__file__).resolve().parents[3]
    else:
        root = Path(repo_root)
    return (
        root / "pipeline_state" / "ultimate_book" / str(namespace)
        / "judgment" / "state" / "just_closed_siblings.json"
    )


def f5_record_just_closed(
    symbol: object,
    ticket: object = None,
    closed_utc: object = None,
    path: object | None = None,
    sleeve: object = None,
    extra: object = None,
) -> None:
    """Append a same-symbol close. Never raises. Isolated re-entry after 15m is wanted."""
    try:
        sym = f5_norm_symbol(symbol)
        if not sym:
            return
        dest = Path(path) if path is not None else f5_just_closed_siblings_path()
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc: dict = {}
        if dest.is_file():
            try:
                loaded = json.loads(dest.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    doc = loaded
            except (OSError, ValueError):
                doc = {}
        closed = list(doc.get("closed") or [])
        ts = str(closed_utc or datetime.now(timezone.utc).isoformat())
        extra_d = extra if isinstance(extra, dict) else {}
        close_action = extra_d.get("close_action") or extra_d.get("reason") or "broker_close"
        ticket_s = str(ticket) if ticket not in (None, "", 0, "0") else None
        if ticket_s:
            closed = [
                item for item in closed
                if not (isinstance(item, dict) and str(item.get("ticket") or "") == ticket_s)
            ]
        row = {
            "symbol": sym,
            "ticket": ticket_s,
            "closed_utc": ts,
            "sleeve": str(sleeve) if sleeve else None,
            "reason": str(close_action),
            "close_action": str(close_action),
        }
        row.update({k: v for k, v in extra_d.items() if v is not None})
        row = {k: v for k, v in row.items() if v is not None}
        closed.append(row)
        kept = []
        now = datetime.now(timezone.utc)
        retain = _returned("sibling_retain_seconds")
        for item in closed:
            if not isinstance(item, dict):
                continue
            t = item.get("closed_utc")
            try:
                parsed = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                age = (now - parsed).total_seconds()
                if retain is None or age <= float(retain):
                    kept.append(item)
            except (TypeError, ValueError):
                kept.append(item)
        sibling_minutes = _returned("sibling_window_minutes")
        if sibling_minutes is not None:
            doc["window_minutes"] = float(sibling_minutes)
            doc["metal_index_sibling_minutes"] = float(sibling_minutes)
        cooldown_hours = _returned("fx_sl_cooldown_hours")
        if cooldown_hours is not None:
            doc["fx_sl_cooldown_hours"] = float(cooldown_hours)
        doc["law"] = (
            "Same-symbol re-entry waits the returned sibling window. "
            "An FX major after an SL-class close waits the returned cooldown. "
            "An empty score leaves the window unset. Isolated re-entry after the window is wanted. "
            "USDJPY stays a standing hold. Hard-off sleeves cannot fire. "
            "Owner-closed gold 179380936 and EURUSD 179272692 spent tonight, do not remint."
        )
        doc["spent_tonight"] = list(doc.get("spent_tonight") or [
            {"symbol": "XAUUSD", "ticket": "179380936", "reason": "owner-close night room-save"},
            {"symbol": "EURUSD", "ticket": "179272692", "reason": "owner-close night room-save"},
        ])
        doc["closed"] = kept
        doc["updated_utc"] = now.isoformat()
        dest.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    except Exception:
        return


def f5_cooldown_minutes_for_close(symbol: object, close_action: object = None) -> float | None:
    """Returned cooldown in minutes. Unset does not restore a window."""
    if f5_norm_symbol(symbol) in F5_FX_DSP_SL_COOLDOWN_SYMBOLS and f5_is_sl_class_close(close_action):
        hours = _returned("fx_sl_cooldown_hours")
        if hours is None:
            return None
        return float(hours) * 60.0
    return _returned("sibling_window_minutes")


def f5_just_closed_sibling_reason(
    symbol: object,
    now: object = None,
    path: object | None = None,
    window_minutes: object = None,
) -> str | None:
    """Writer block: 15-min sibling, plus 4h FX after an SL-class close."""
    try:
        sym = f5_norm_symbol(symbol)
        if not sym:
            return None
        dest = Path(path) if path is not None else f5_just_closed_siblings_path()
        if not dest.is_file():
            return None
        doc = json.loads(dest.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            return None
        clock = _f5_as_utc(now)
        forced = None
        if window_minutes is not None:
            try:
                forced = float(window_minutes)
            except (TypeError, ValueError):
                forced = None
        for item in doc.get("closed") or ():
            if not isinstance(item, dict):
                continue
            if f5_norm_symbol(item.get("symbol")) != sym:
                continue
            t = item.get("closed_utc") or item.get("ts_utc")
            try:
                parsed = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
            age = (clock - parsed).total_seconds()
            sl_fx = (
                sym in F5_FX_DSP_SL_COOLDOWN_SYMBOLS
                and f5_is_sl_class_close(item)
            )
            window = forced if forced is not None else f5_cooldown_minutes_for_close(sym, item)
            if window is not None and not (0 <= age <= float(window) * 60.0):
                continue
            closed_key = parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            age_state: dict[str, object] = {
                "symbol": sym,
                "age_seconds": float(age),
                "namespace": F5_NAMESPACE,
            }
            if window is not None:
                age_state["window_minutes"] = float(window)
            if sl_fx:
                age_state["fx_sl_cooldown_fact"] = True
                if _spot_withholds(
                    "fx_sl_same_symbol_cooldown",
                    age_state,
                    (
                        "fx_sl_cooldown_stands",
                        "Do not send this symbol. The SL cooldown stands.",
                    ),
                    (
                        "sl_age_is_a_fact",
                        "An SL-class close is on the card. That age is only a fact. This candidate can still be the fire.",
                    ),
                    f"fx_sl_same_symbol_cooldown|{sym}|{closed_key}",
                    "This FX symbol had an SL-class close. The age is on the card. A returned window is a fact only when it is present. Is that age only a fact, or a reason not to send?",
                ):
                    return "fx_sl_same_symbol_cooldown"
            elif _spot_withholds(
                "just_closed_sibling",
                age_state,
                (
                    "sibling_window_stands",
                    "Do not send this symbol. The just-closed sibling window stands.",
                ),
                (
                    "close_is_a_fact",
                    "A same-symbol close is on the card. That close is only a fact. Isolated re-entry can still be the fire.",
                ),
                f"just_closed_sibling|{sym}|{closed_key}",
                "This symbol closed. The age is on the card. A returned window is a fact only when it is present. Is that close only a fact, or a reason not to send?",
            ):
                return "just_closed_sibling"
        return None
    except Exception:
        return None


def f5_standing_hold_reason(
    namespace: str,
    symbol: str,
    occupied_symbols: Iterable[str] = (),
    direction: object = None,
    family: object = None,
    occupied_book: Iterable[Mapping[str, Any]] = (),
    sl: object = None,
    tp: object = None,
    entry: object = None,
    now: object = None,
    stop_dist: object = None,
    repo_root: object | None = None,
    path: object | None = None,
) -> str | None:
    """Why a new intent must not place. None = not a standing hold.

    USDJPY is held for the rest of verification at the WRITER, not as an
    inbox why_code. Hard-off sleeves cannot fire even if still listed on
    the token-bound --tags surface. Dead window 21:00-00:00 UTC and Friday
    after 16:00 UTC take no NEW risk. Named HIGH (Fed/CPI/NFP/rates/
    Warsh-class) blocks NEW fills T-15..T+60 by candidate symbol. FX DSP
    stops <=8 pip are refused. FX DSP majors wait 4h after an SL;
    metals/index keep the 15-minute sibling.

    Occupied keep-one is a script, not intelligence. Isolated re-entry on a
    *flat* symbol after the cooldown is not a hold.
    """
    if str(namespace or "") != F5_NAMESPACE:
        return None
    sym = f5_norm_symbol(symbol)
    if not sym:
        return None
    for standing in F5_STANDING_HOLD_SYMBOLS:
        if sym == standing or sym.startswith(standing):
            if _spot_withholds(
                "usdjpy_verification_hold",
                {"symbol": sym, "standing_symbol_fact": True, "namespace": F5_NAMESPACE},
                (
                    "usdjpy_hold",
                    "Do not send this USDJPY candidate. The standing hold stands for this bar.",
                ),
                (
                    "standing_list_is_a_fact",
                    "USDJPY is on the standing list. That list is only a fact. This candidate can still be the fire.",
                ),
                f"usdjpy_hold|{sym}",
                "This symbol is USDJPY, the standing hold for verification. Is that list only a fact, or a reason not to send?",
            ):
                return "usdjpy_verification_hold_5pip_dsp_stop"
    hard = f5_hard_off_sleeve_reason(family, namespace)
    if hard:
        return hard
    fam_text = str(family or "").lower()
    clock_reason = f5_clock_hold_reason(namespace, sym, now=now)
    if clock_reason:
        return clock_reason
    high_reason = f5_high_print_hold_reason(namespace, sym, now=now, repo_root=repo_root)
    if high_reason:
        return high_reason
    idxrev_off = f5_idxrev_symbol_off_reason(namespace, sym, family=family)
    if idxrev_off:
        return idxrev_off
    tight = f5_fx_dsp_tight_stop_reason(
        namespace, sym, family=family, stop_dist=stop_dist, sl=sl, entry=entry,
    )
    if tight:
        return tight
    if "asia_pdl_fade" in fam_text and f5_is_crypto_or_oil_symbol(sym):
        hour = _f5_as_utc(now).hour
        thin_state: dict[str, object] = {
            "symbol": sym,
            "sleeve": fam_text,
            "hour_utc": hour,
            "namespace": F5_NAMESPACE,
        }
        end = _returned("thin_hour_end_hour")
        if end is not None:
            thin_state["returned_thin_hour_end"] = int(end)
            thin_state["before_returned_end"] = hour < int(end)
        if _spot_withholds(
            "thin_hour_crypto_asia_pdl_book_hold",
            thin_state,
            (
                "thin_hour_mute",
                "Do not send this asia_pdl_fade candidate. The thin hour stands.",
            ),
            (
                "hour_is_a_fact",
                "The hour is a clock fact. This fade can still be the fire.",
            ),
            f"thin_hour_crypto_asia_pdl|{sym}|{hour}",
            "asia_pdl_fade on crypto or oil. The hour is on the card. A returned end hour is a fact only when it is present. Is that hour only a fact, or a reason not to send?",
        ):
            return "thin_hour_crypto_asia_pdl_book_hold"
    occupied = {f5_norm_symbol(s) for s in occupied_symbols if f5_norm_symbol(s)}
    new_row = {
        "symbol": sym,
        "direction": direction,
        "sl": sl,
        "tp": tp,
        "entry": entry,
    }
    d = f5_norm_direction(direction)
    stop = _f5_finite_level(sl)
    sibling_path = path
    if sibling_path is None and repo_root is not None:
        sibling_path = f5_just_closed_siblings_path(repo_root=repo_root, namespace=namespace)
    jc = f5_just_closed_sibling_reason(sym, now=now, path=sibling_path)
    if jc:
        return jc
    # A row without direction AND stop is not holdable and must not PASS.
    # Not an occupied HOLD. Isolated re-entry after a close is not this.
    if not d and stop is None:
        return "standing_intent_unholdable_no_geometry"
    # Structural pre-fill HOLD only when the NEW candidate HAS direction.
    if d and sym in occupied:
        for row in occupied_book or ():
            if not isinstance(row, Mapping):
                continue
            if f5_norm_symbol(row.get("symbol")) != sym:
                continue
            o_dir = f5_norm_direction(row.get("direction") or row.get("side"))
            if d and o_dir and d != o_dir:
                if f5_levels_lock(new_row, row):
                    return "locking_sl_tp_geometry"
                return "same_symbol_opposite_lock"
        return "same_symbol_stack_keep_working_ticket"
    if d and f5_is_dsp_family(family) and f5_is_eur_gbp_fx(sym):
        for row in occupied_book or ():
            if not isinstance(row, Mapping):
                continue
            o_sym = f5_norm_symbol(row.get("symbol"))
            o_dir = f5_norm_direction(row.get("direction") or row.get("side"))
            o_fam = row.get("family") or row.get("sleeve") or row.get("comment")
            if not o_sym or o_sym == sym:
                continue
            if not f5_is_eur_gbp_fx(o_sym) or not f5_is_dsp_family(o_fam):
                continue
            if o_dir == d:
                if _spot_withholds(
                    "same_currency_dsp_stack_one_bet",
                    {
                        "symbol": sym,
                        "other_symbol": o_sym,
                        "direction": d,
                        "same_currency_stack_fact": True,
                        "namespace": F5_NAMESPACE,
                    },
                    (
                        "one_bet_stands",
                        "Do not send this second EUR/GBP DSP bet. One bet already stands.",
                    ),
                    (
                        "second_bet_is_the_fire",
                        "Another EUR/GBP DSP ticket is already the same way. That occupancy is only a fact. This candidate can still be the fire.",
                    ),
                    f"same_currency_dsp|{sym}|{o_sym}|{d}",
                    "A same-direction DSP bet is already open on the other EUR/GBP symbol. Is that one bet the decision, or is this candidate the fire?",
                ):
                    return "same_currency_dsp_stack_one_bet"
    return None


F5_H4_DAILY_UNIT_CAP_SLEEVES = frozenset({
    "idxrev",
    "orb_crypto_london",
    "orb_crypto_london_widen",
})



# The orig-stop count is the integer read from closed[]. Whether that count
# refuses a remint is the Choice. An empty answer does not refuse.


def f5_session_day_key(value: object = None) -> str:
    """UTC calendar day used as the F5 session-day key for the 2-stop circuit."""
    dt = f5_aware_utc(value)
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def f5_is_orig_stop_close(close_action: object = None, row: object = None) -> bool:
    """True for orig_stop / SL-class closes that count toward the 2-stop day circuit."""
    blob_parts = []
    src = row if isinstance(row, Mapping) else None
    if src is not None:
        for key in ("exit_class", "close_action", "reason", "action", "comment"):
            blob_parts.append(str(src.get(key) or ""))
        try:
            realised = src.get("realised_r")
            if realised is not None and float(realised) <= -0.7:
                return True
        except (TypeError, ValueError):
            pass
        try:
            pnl = src.get("broker_net_pnl_usd")
            if pnl is not None and float(pnl) < 0:
                # negative broker close with no TP marker counts
                blob = " ".join(blob_parts).lower()
                if "take_profit" not in blob and "broker_tp" not in blob:
                    if f5_is_sl_class_close(src) or "orig_stop" in blob or "broker_closed" in blob:
                        return True
        except (TypeError, ValueError):
            pass
    if close_action is not None and not isinstance(close_action, Mapping):
        blob_parts.append(str(close_action))
    elif isinstance(close_action, Mapping):
        for key in ("exit_class", "close_action", "reason", "action"):
            blob_parts.append(str(close_action.get(key) or ""))
    blob = " ".join(blob_parts).strip().lower()
    if not blob:
        return False
    if "take_profit" in blob or "broker_tp" in blob or "weekend_flat" in blob:
        return False
    if "orig_stop" in blob:
        return True
    return f5_is_sl_class_close(close_action if close_action is not None else row)


def f5_same_sleeve_orig_stop_count_session_day(
    symbol: object,
    sleeve: object = None,
    now: object = None,
    path: object | None = None,
) -> int:
    """Count same-symbol same-sleeve orig_stops already recorded for this session day."""
    sym = f5_norm_symbol(symbol)
    sle = f5_sleeve_name(sleeve)
    if not sym or not sle:
        return 0
    day = f5_session_day_key(now)
    dest = Path(path) if path is not None else f5_just_closed_siblings_path()
    try:
        if not dest.is_file():
            return 0
        doc = json.loads(dest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if not isinstance(doc, dict):
        return 0
    count = 0
    seen_tickets: set[str] = set()
    for item in list(doc.get("closed") or []):
        if not isinstance(item, dict):
            continue
        if f5_norm_symbol(item.get("symbol")) != sym:
            continue
        if f5_sleeve_name(item.get("sleeve")) != sle:
            continue
        if not f5_is_orig_stop_close(row=item, close_action=item.get("close_action") or item.get("exit_class") or item.get("reason")):
            continue
        ts = item.get("closed_utc") or item.get("closed_at_utc")
        if f5_session_day_key(ts) != day:
            continue
        ticket_s = str(item.get("ticket") or "")
        if ticket_s and ticket_s in seen_tickets:
            continue
        if ticket_s:
            seen_tickets.add(ticket_s)
        count += 1
    return count


def f5_same_sleeve_two_stop_refuse_reason(
    symbol: object,
    sleeve: object = None,
    now: object = None,
    path: object | None = None,
    namespace: object = None,
) -> str | None:
    """The orig-stop count is a fact. It refuses only when that side is unique.

    An empty answer, a tie, or an error does not refuse and does not restore a count.
    """
    if namespace is not None and str(namespace) != F5_NAMESPACE:
        return None
    n = f5_same_sleeve_orig_stop_count_session_day(symbol, sleeve=sleeve, now=now, path=path)
    day = f5_session_day_key(now)
    if _spot_withholds(
        "same_sleeve_orig_stops_session_day",
        {
            "symbol": f5_norm_symbol(symbol),
            "sleeve": f5_sleeve_name(sleeve),
            "orig_stop_count": int(n),
            "day": day,
            "namespace": F5_NAMESPACE,
        },
        (
            "orig_stops_stand",
            "Do not remint this sleeve on this symbol. The orig-stop count on this state stands.",
        ),
        (
            "count_is_a_fact",
            "The orig-stop count is only a fact. This candidate can still be the fire.",
        ),
        f"orig_stops|{f5_norm_symbol(symbol)}|{f5_sleeve_name(sleeve)}|{day}|{n}",
        "The orig-stop count for this symbol and sleeve on this session day is a fact on this state. "
        "Is that count the decision, or is this candidate the fire? "
        "An empty answer or a tie does not refuse. Do not flatten an open ticket.",
    ):
        return "same_sleeve_orig_stops_session_day"
    return None



def f5_daily_cap_yields_isolated_reentry(
    namespace: str,
    symbol: str,
    sleeve: object = None,
    occupied_symbols: Iterable[str] = (),
    now: object = None,
    path: object | None = None,
    repo_root: object | None = None,
) -> bool:
    """True when already_placed_today / cluster later-bar cap must yield.

    Occupied keep-one is a script, not intelligence. Isolated re-entry on a
    *flat* symbol after the just-closed window is wanted. Not a remint of a
    spent ticket. H4 crypto/idxrev keep the certified one-unit-per-day cap.
    USDJPY stays writer HOLD. Live occupancy still keep-works the open ticket.
    """
    if str(namespace or "") != F5_NAMESPACE:
        return False
    sym = f5_norm_symbol(symbol)
    if not sym:
        return False
    for standing in F5_STANDING_HOLD_SYMBOLS:
        if sym == standing or sym.startswith(standing):
            if _spot_withholds(
                "usdjpy_verification_hold",
                {"symbol": sym, "standing_symbol_fact": True, "namespace": F5_NAMESPACE},
                (
                    "usdjpy_hold",
                    "Do not send this USDJPY candidate. The standing hold stands for this bar.",
                ),
                (
                    "standing_list_is_a_fact",
                    "USDJPY is on the standing list. That list is only a fact. This candidate can still be the fire.",
                ),
                f"usdjpy_hold|{sym}",
                "This symbol is USDJPY, the standing hold for verification. Is that list only a fact, or a reason not to send?",
            ):
                return False
    if str(sleeve or "") in F5_H4_DAILY_UNIT_CAP_SLEEVES:
        return False
    occupied = {f5_norm_symbol(s) for s in occupied_symbols if f5_norm_symbol(s)}
    if sym in occupied:
        return False
    # The orig-stop count refuses the yield only when that Choice is unique.
    _two_stop_path = path
    if _two_stop_path is None and repo_root is not None:
        _two_stop_path = f5_just_closed_siblings_path(
            repo_root=repo_root, namespace=namespace,
        )
    if f5_same_sleeve_two_stop_refuse_reason(
        sym, sleeve=sleeve, now=now, path=_two_stop_path, namespace=namespace,
    ):
        return False
    sibling_path = path
    if sibling_path is None and repo_root is not None:
        sibling_path = f5_just_closed_siblings_path(
            repo_root=repo_root, namespace=namespace,
        )
    if f5_just_closed_sibling_reason(sym, now=now, path=sibling_path):
        return False
    return True


F5_DUP_STACK_DEDUP_ENABLED = True


# --------------------------------------------------------------------------------------------
# configuration, parsed from run_book.py CLI flags ONLY.
#
# It is a HARD REQUIREMENT that this never touches config/agent_config.yaml: that file is bound
# by the R2 decision contract (common_behavior_inputs) AND its bytes enter the activation-token
# config digest, so a single byte would invalidate both armed accounts' tokens and the book would
# refuse to place until they were re-minted. The CLI-flag route is the established precedent --
# see book_engine on --vol-level-tilt: "the launcher flag reaches the bridge as an injected key
# on a COPY of the runtime dict, never as a byte of agent_config.yaml".
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class MinimalSizeConfig:
    enabled: bool = False
    target_risk_usd: float = 10.0           # --f5-minimal-size-usd
    notional_initial_usd: float = 100000.0  # --f5-notional-initial-usd
    round_up_to_min_lot: bool = True        # False would bias the sample; see WHY ROUND-UP
    # NO loss_budget field, by owner decision. See NO LOSS BUDGET in the module docstring.

    def validate(self) -> None:
        """Raise on anything a live worker must not start with.

        Called at LAUNCH, before any engine exists, for the same reason
        ``parse_frontier_exits`` is: a mis-sized book that degrades silently every tick is
        worse than a worker that refuses to start.
        """
        if not self.enabled:
            return
        if not isinstance(self.target_risk_usd, (int, float)) or self.target_risk_usd != self.target_risk_usd:
            raise ValueError("f5 target_risk_usd must be a number")
        if not isinstance(self.notional_initial_usd, (int, float)) or self.notional_initial_usd <= 0:
            raise ValueError(
                f"f5 notional_initial_usd must be > 0, got {self.notional_initial_usd}")


# --------------------------------------------------------------------------------------------
# the notional ledger
# --------------------------------------------------------------------------------------------
@dataclass
class _OpenUnit:
    ticket: int
    sleeve: str
    symbol: str
    nominal_risk_usd: float     # what production WOULD have risked
    actual_risk_usd: float      # what the broker actually holds (post round-up)
    intended_risk_usd: float    # the target before round-up
    opened_utc: str
    decision_day: str


class NotionalLedger:
    """The equity curve production WOULD have had, driven by scale-free R.

    R is scale-invariant, which is the whole reason this works::

        realised_R   = broker_net_pnl_usd / actual_cash_risk_usd
        notional_pnl = realised_R * nominal_risk_usd

    ``actual_cash_risk_usd`` is not guessed: ``execution.open_trade`` already computes
    ``pre_send_cash_risk_amount`` from the broker's own ``order_calc_profit`` on the
    NORMALIZED volume, and the trade record persists it per ticket.

    State is a single JSON file under the namespace's pipeline_state directory, so a restart
    resumes the same epoch rather than silently starting a new one.
    """

    def __init__(self, path: Path, cfg: MinimalSizeConfig, clock=None):
        self._path = Path(path)
        self._cfg = cfg
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = threading.RLock()
        self._load_status = "not_loaded"
        self._persistence_healthy = True
        self._reconciliation_complete = False
        self._reconciliation_status = "broker_positions_not_reconciled"
        self._floating_notional_pnl_usd = 0.0
        self._state = self._load()
        self._publish_held()

    def _publish_held(self) -> None:
        """Loaded ledger numbers are account facts. A blank start is not."""

        if self._load_status != "loaded":
            return
        _hold_anchor_facts({
            "notional_equity": self._state.get("notional_equity"),
            "notional_initial": self._state.get("notional_initial"),
            "day_start_notional": self._state.get("day_start_notional"),
            "notional_high_water": self._state.get("notional_high_water"),
            "floating_notional_pnl_usd": self._floating_notional_pnl_usd,
        })

    # ---- persistence -----------------------------------------------------------------------
    def _blank(self) -> dict:
        init = float(self._cfg.notional_initial_usd)
        return {
            "schema": SCHEMA,
            "epoch": 1,
            "epoch_opened_utc": self._clock().isoformat(),
            "notional_equity": init,
            "notional_high_water": init,
            "notional_initial": init,
            "day_key": None,
            "day_start_notional": init,
            "open_units": {},
            # REAL money, across ALL epochs, never reset. REPORTING ONLY.
            "real_pnl_usd_cumulative": 0.0,
            "epochs_closed": [],
            "trades_recorded": 0,
            "trades_recorded_all_epochs": 0,
        }

    def _load(self) -> dict:
        try:
            if self._path.is_file():
                st = json.loads(self._path.read_text(encoding="utf-8-sig"))
                required_numbers = (
                    "notional_equity", "notional_high_water", "notional_initial",
                    "day_start_notional", "real_pnl_usd_cumulative",
                )
                structurally_valid = (
                    isinstance(st, dict)
                    and st.get("schema") == SCHEMA
                    and isinstance(st.get("open_units"), dict)
                    and all(
                        isinstance(st.get(key), (int, float))
                        and math.isfinite(float(st.get(key)))
                        for key in required_numbers
                    )
                )
                if structurally_valid:
                    self._load_status = "loaded"
                    return st
                self._load_status = "invalid_existing_ledger"
                return self._blank()
        except (OSError, ValueError):
            self._load_status = "invalid_existing_ledger"
            return self._blank()
        self._load_status = "new"
        return self._blank()

    def _save(self) -> bool:
        # Never overwrite the only evidence of a corrupt ledger with a fresh blank state.  The
        # F5 governor stays unavailable until the damaged file is recovered or replaced explicitly.
        if self._load_status == "invalid_existing_ledger":
            self._persistence_healthy = False
            return False
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_name(self._path.name + ".tmp")
            tmp.write_text(json.dumps(self._state, indent=1, sort_keys=True), encoding="utf-8")
            tmp.replace(self._path)
            self._persistence_healthy = True
            if self._load_status == "new":
                self._load_status = "loaded"
            return True
        except OSError:
            # Do not raise into management, but do make the next entry decision fail closed.
            self._persistence_healthy = False
            return False

    # ---- the three notional surfaces the governor reads -------------------------------------
    def equity(self) -> float:
        """Realized notional balance (immutable basis for close accounting and sizing)."""
        self._publish_held()
        return float(self._state["notional_equity"])

    def governor_equity(self) -> "float | None":
        """N1 mark-to-market equity, or None until every broker position is source-bound."""
        if not self.governor_ready():
            return None
        return float(self._state["notional_equity"]) + float(self._floating_notional_pnl_usd)

    def governor_ready(self) -> bool:
        return bool(
            self._reconciliation_complete
            and self._persistence_healthy
            and self._load_status != "invalid_existing_ledger"
        )

    def reconciliation_status(self) -> dict:
        return {
            "complete": self.governor_ready(),
            "status": self._reconciliation_status,
            "load_status": self._load_status,
            "persistence_healthy": bool(self._persistence_healthy),
            "floating_notional_pnl_usd": float(self._floating_notional_pnl_usd),
        }

    def mark_reconciliation_unavailable(self, reason: str) -> dict:
        self._reconciliation_complete = False
        self._reconciliation_status = str(reason or "broker_positions_unavailable")
        return self.reconciliation_status()

    def high_water(self) -> float:
        return float(self._state["notional_high_water"])

    def day_start_balance(self, day_key: str) -> float:
        """N3. Keyed on the governor's own broker-correct reset-window date, so the notional
        day rolls on the same clock the firm uses."""
        with self._lock:
            if self._state.get("day_key") != day_key:
                self._state["day_key"] = day_key
                self._state["day_start_notional"] = float(self._state["notional_equity"])
                self._save()
            return float(self._state["day_start_notional"])

    def open_risk_pct(self) -> float:
        """N2, and the hunk that makes the experiment valid rather than a different strategy.

        ``book_engine._open_risk_pct`` computes ``vol * |entry-sl| * value_per_point`` from the
        BROKER's positions. At 1/200th lot size that returns ~0.0002 against a 0.04 cap, so the
        cap can never bind and the book would run 20+ concurrent units where production runs 2.
        This returns what production would have seen.
        """
        eq = self.governor_equity()
        if eq is None:
            # Raw diagnostics/tests may ask before the owner has a broker snapshot.  The live
            # engine checks governor_ready() and refuses before this value reaches admission.
            eq = self.equity()
        if eq <= 0:
            return 0.0
        total = 0.0
        for u in self._state["open_units"].values():
            try:
                # Entry risk stays immutable for R/P&L evidence.  The governor alone follows
                # the current broker exposure after a partial close or protective-SL move.
                total += float(
                    u.get("current_nominal_risk_usd", u.get("nominal_risk_usd")) or 0.0
                )
            except (TypeError, ValueError):
                continue
        return max(0.0, total / eq)

    # ---- lifecycle -------------------------------------------------------------------------
    def on_open(self, *, ticket: int, sleeve: str, symbol: str, nominal_risk_usd: float,
                actual_risk_usd: float, intended_risk_usd: float, decision_day: str) -> dict:
        with self._lock:
            row = asdict(_OpenUnit(
                ticket=int(ticket), sleeve=str(sleeve), symbol=str(symbol),
                nominal_risk_usd=float(nominal_risk_usd or 0.0),
                actual_risk_usd=float(actual_risk_usd or 0.0),
                intended_risk_usd=float(intended_risk_usd or 0.0),
                opened_utc=self._clock().isoformat(), decision_day=str(decision_day)))
            row["current_nominal_risk_usd"] = float(nominal_risk_usd or 0.0)
            row["current_actual_risk_usd"] = float(actual_risk_usd or 0.0)
            row["current_notional_floating_pnl_usd"] = 0.0
            self._state["open_units"][str(int(ticket))] = row
            self._save()
            return dict(row)

    def reconcile_broker_positions(self, rows: list[Mapping[str, Any]]) -> dict:
        """Bind every open broker position to immutable entry evidence and refresh N1/N2.

        Each row carries current broker geometry/P&L plus optional immutable F5 entry fields
        recovered from the ticket trade record.  A missing ledger unit is adopted from those
        three values when present; if they are absent, recover intended=actual=nominal from
        broker geometry (volume * |entry-sl| * vpp).  A ticket that still cannot bind is
        isolated so it cannot fail-close governor_ready for the rest of the book.  A corrupt
        existing ledger still fails closed.
        """
        with self._lock:
            if self._load_status == "invalid_existing_ledger":
                return self.mark_reconciliation_unavailable("invalid_existing_ledger")

            unresolved: list[str] = []
            seen: set[str] = set()
            floating_total = 0.0
            recovered: list[int] = []
            position_rows = list(rows or [])
            for raw in position_rows:
                try:
                    ticket = int(raw.get("ticket") or 0)
                except (TypeError, ValueError, AttributeError):
                    ticket = 0
                if ticket <= 0:
                    unresolved.append("position_ticket_unavailable")
                    continue
                key = str(ticket)
                seen.add(key)
                unit = self._state["open_units"].get(key)
                if not isinstance(unit, dict):
                    try:
                        nominal = float(raw.get("nominal_risk_usd") or 0.0)
                        actual = float(raw.get("actual_risk_usd") or 0.0)
                        intended = float(raw.get("intended_risk_usd") or 0.0)
                    except (TypeError, ValueError, AttributeError):
                        nominal = actual = intended = 0.0
                    recovered_from_geometry = False
                    if (
                        not all(math.isfinite(value) for value in (nominal, actual, intended))
                        or nominal <= 0 or actual <= 0 or intended <= 0
                    ):
                        try:
                            g_volume = float(raw.get("current_volume"))
                            g_entry = float(raw.get("price_open"))
                            g_sl = float(raw.get("stop_loss"))
                            g_vpp = float(raw.get("value_per_point"))
                            g_risk = g_volume * abs(g_entry - g_sl) * g_vpp
                        except (TypeError, ValueError, AttributeError):
                            g_risk = 0.0
                            g_volume = g_entry = g_sl = g_vpp = 0.0
                        if (
                            math.isfinite(g_risk) and g_risk > 0
                            and g_volume >= 0 and g_entry > 0 and g_sl > 0 and g_vpp > 0
                        ):
                            nominal = actual = intended = float(g_risk)
                            recovered_from_geometry = True
                        else:
                            # Isolate: do not fail-close the book; recon continues.
                            unresolved.append(f"ticket:{ticket}:immutable_entry_risk_unavailable")
                            continue
                    unit = asdict(_OpenUnit(
                        ticket=ticket,
                        sleeve=str(raw.get("sleeve") or ""),
                        symbol=str(raw.get("symbol") or ""),
                        nominal_risk_usd=nominal,
                        actual_risk_usd=actual,
                        intended_risk_usd=intended,
                        opened_utc=str(raw.get("opened_utc") or self._clock().isoformat()),
                        decision_day=str(raw.get("decision_day") or ""),
                    ))
                    if recovered_from_geometry:
                        unit["recovered_from_broker_geometry"] = True
                    else:
                        unit["recovered_from_trade_record"] = True
                    self._state["open_units"][key] = unit
                    recovered.append(ticket)

                try:
                    entry_actual = float(unit.get("actual_risk_usd") or 0.0)
                    entry_nominal = float(unit.get("nominal_risk_usd") or 0.0)
                    entry_intended = float(unit.get("intended_risk_usd") or 0.0)
                    volume = float(raw.get("current_volume"))
                    entry = float(raw.get("price_open"))
                    sl = float(raw.get("stop_loss"))
                    vpp = float(raw.get("value_per_point"))
                    floating_actual = float(raw.get("broker_floating_pnl_usd"))
                except (TypeError, ValueError, AttributeError):
                    unresolved.append(f"ticket:{ticket}:current_broker_exposure_unavailable")
                    continue
                numbers = (
                    entry_actual, entry_nominal, entry_intended, volume, entry, sl, vpp,
                    floating_actual,
                )
                if (
                    not all(math.isfinite(value) for value in numbers)
                    or entry_actual <= 0 or entry_nominal <= 0 or entry_intended <= 0
                    or volume < 0 or entry <= 0 or sl <= 0 or vpp <= 0
                ):
                    unresolved.append(f"ticket:{ticket}:current_broker_exposure_invalid")
                    continue

                scale = entry_nominal / entry_actual
                current_actual = volume * abs(entry - sl) * vpp
                current_nominal = current_actual * scale
                floating_notional = floating_actual * scale
                unit.update({
                    "current_actual_risk_usd": float(current_actual),
                    "current_nominal_risk_usd": float(current_nominal),
                    "current_notional_floating_pnl_usd": float(floating_notional),
                    "current_volume": float(volume),
                    "current_stop_loss": float(sl),
                })
                floating_total += float(floating_notional)

            for key in self._state["open_units"]:
                if key not in seen:
                    unresolved.append(f"ticket:{key}:ledger_open_unit_absent_from_broker")

            self._floating_notional_pnl_usd = float(floating_total)
            # Ticket-scoped holes stay visible but must not park governor_ready.
            systemic = [u for u in unresolved if not str(u).startswith("ticket:")]
            self._reconciliation_complete = not systemic
            if not unresolved:
                self._reconciliation_status = "broker_positions_reconciled"
            elif not systemic:
                self._reconciliation_status = "isolated:" + ",".join(sorted(unresolved))
            else:
                self._reconciliation_status = "unresolved:" + ",".join(sorted(unresolved))
            if not self._save():
                self._reconciliation_complete = False
                self._reconciliation_status = "ledger_persist_failed"
            out = self.reconciliation_status()
            out["recovered_tickets"] = recovered
            out["broker_position_count"] = len(position_rows)
            return out

    def on_close(self, *, ticket: int, broker_net_pnl_usd: float,
                 realised_r: Optional[float] = None) -> dict:
        """Fold a closed trade into BOTH ledgers. Returns the recorded row for the capture log."""
        with self._lock:
            u = self._state["open_units"].pop(str(int(ticket)), None)
            self._floating_notional_pnl_usd = sum(
                float(row.get("current_notional_floating_pnl_usd") or 0.0)
                for row in self._state["open_units"].values()
                if isinstance(row, dict)
            )
            self._state["real_pnl_usd_cumulative"] += float(broker_net_pnl_usd or 0.0)
            if u is None:
                # An adopted position with no F5 record: count the REAL money (it is real) but
                # do not fabricate a notional leg. FAIL-VISIBLE, not fail-silent.
                self._save()
                return {"ticket": int(ticket), "f5_unmatched_close": True,
                        "broker_net_pnl_usd": float(broker_net_pnl_usd or 0.0),
                        "real_pnl_usd_cumulative": float(self._state["real_pnl_usd_cumulative"])}
            r = realised_r
            if r is None:
                ar = float(u.get("actual_risk_usd") or 0.0)
                r = (float(broker_net_pnl_usd or 0.0) / ar) if ar > 0 else 0.0
            notional_pnl = float(r) * float(u["nominal_risk_usd"])
            self._state["notional_equity"] = float(self._state["notional_equity"]) + notional_pnl
            self._state["notional_high_water"] = max(
                float(self._state["notional_high_water"]), float(self._state["notional_equity"]))
            self._state["trades_recorded"] = int(self._state["trades_recorded"]) + 1
            self._state["trades_recorded_all_epochs"] = int(
                self._state.get("trades_recorded_all_epochs", 0)) + 1
            intended = float(u["intended_risk_usd"])
            nominal = float(u["nominal_risk_usd"])
            actual = float(u["actual_risk_usd"])
            row = {
                "ticket": int(ticket), "sleeve": u["sleeve"], "symbol": u["symbol"],
                "realised_r": float(r),
                "broker_net_pnl_usd": float(broker_net_pnl_usd or 0.0),
                "notional_pnl_usd": float(notional_pnl),
                "f5_nominal_risk_usd": nominal,
                "f5_actual_risk_usd": actual,
                "f5_intended_risk_usd": intended,
                # > 1.0 == this trade was rounded up; the exact dollar-reweighting factor.
                "f5_size_ratio_actual_over_intended": (actual / intended) if intended > 0 else None,
                # Ratio of notional to actual. The invalidation canary:
                # if this tracks the actual, the notional ledger is not wired.
                "f5_notional_over_actual": (nominal / actual) if actual > 0 else None,
                "epoch": int(self._state["epoch"]),
                "notional_equity_after": float(self._state["notional_equity"]),
                "real_pnl_usd_cumulative": float(self._state["real_pnl_usd_cumulative"]),
            }
            self._save()
            return row

    # ---- reporting only. THERE IS NO BUDGET GATE. -------------------------------------------
    # `real_pnl_usd_cumulative` exists so `scripts/f5_status.py` can show the owner what the
    # experiment has actually cost. NOTHING in this module or in book_owner reads it to decide
    # anything. If a future session adds a threshold here, that is a policy change and needs the
    # owner's word -- he removed the budget deliberately on 2026-08-12.

    def open_new_epoch(self, reason: str) -> dict:
        """A NOTIONAL breach stands the book down exactly as production would, is logged as a
        first-class numbered event, and only then does the notional equity reset so collection
        continues. Explicit and numbered -- never silent."""
        with self._lock:
            closed = {
                "epoch": int(self._state["epoch"]),
                "opened_utc": self._state["epoch_opened_utc"],
                "closed_utc": self._clock().isoformat(),
                "reason": str(reason),
                "notional_equity_at_close": float(self._state["notional_equity"]),
                "notional_drawdown_usd": (float(self._state["notional_equity"])
                                          - float(self._state["notional_initial"])),
                "trades_in_epoch": int(self._state["trades_recorded"]),
            }
            init = float(self._cfg.notional_initial_usd)
            self._state["epochs_closed"].append(closed)
            self._state["epoch"] = int(self._state["epoch"]) + 1
            self._state["epoch_opened_utc"] = self._clock().isoformat()
            self._state["notional_equity"] = init
            self._state["notional_high_water"] = init
            self._state["day_start_notional"] = init
            self._state["day_key"] = None
            self._state["trades_recorded"] = 0
            # open_units are deliberately NOT cleared: the real positions are being flattened by
            # the caller, and their closes must still fold into the real-money ledger.
            self._save()
            return closed

    def snapshot(self) -> dict:
        with self._lock:
            return json.loads(json.dumps(self._state))


# --------------------------------------------------------------------------------------------
# the scaler -- the ONLY thing that touches money size
# --------------------------------------------------------------------------------------------
class MinimalSizeScaler:
    """Applied at the LAST step of ``open_trade``, AFTER every gate has run at nominal.

    Everything upstream is untouched and provably so: the pre-trade cost model and Execution
    Manager V4 both receive the NOMINAL ``risk_pct``; admission, the conviction multiplier, the
    cluster cap, the gross-risk cap and the governor all ran before ``open_trade`` was called.
    The scaler cannot reach them. ``test_f5_scalar_is_last`` asserts that on the recorded call
    arguments rather than on source text.
    """

    def __init__(self, cfg: MinimalSizeConfig, ledger: NotionalLedger):
        self._cfg = cfg
        self._ledger = ledger
        self.last: dict[str, Any] = {}

    @property
    def round_up_enabled(self) -> bool:
        return bool(self._cfg.round_up_to_min_lot)

    @property
    def target_risk_usd(self) -> float:
        return float(self._cfg.target_risk_usd)

    def risk_usd_for(self, symbol: object = None, sleeve: object = None) -> float:
        return f5_intended_risk_usd(
            symbol, sleeve, default=float(self._cfg.target_risk_usd),
        )

    @property
    def ledger(self) -> NotionalLedger:
        return self._ledger

    def scaled_risk_amount(self, nominal_risk_amount: float, trade_params: Mapping) -> float | None:
        """``nominal_risk_amount`` is production's own number.

        Returns the cash the size hop returned. An empty answer stays empty.
        The min-lot round-up happens later, inside the volume
        normalisation, because only there is the broker's volume geometry known.
        """
        sleeve = f5_trade_sleeve(trade_params)
        symbol = f5_trade_symbol(trade_params)
        target = self.risk_usd_for(symbol, sleeve)
        refuse = f5_fx_dsp_tight_stop_reason(
            F5_NAMESPACE,
            symbol,
            family=sleeve,
            stop_dist=f5_trade_stop_dist(trade_params),
            sl=trade_params.get("stop_loss") if isinstance(trade_params, Mapping) else None,
            entry=trade_params.get("entry_price") if isinstance(trade_params, Mapping) else None,
        ) or f5_idxrev_symbol_off_reason(F5_NAMESPACE, symbol, family=sleeve)
        nominal = float(nominal_risk_amount or 0.0)
        self.last = {
            "f5_nominal_risk_usd": nominal,
            "f5_intended_risk_usd": target,
            "f5_cli_risk_usd": float(self._cfg.target_risk_usd),
            "f5_scalar_requested": (target / nominal) if nominal > 0 else None,
            "f5_symbol": symbol or trade_params.get("symbol"),
            "f5_sleeve": sleeve or None,
            "f5_candidate_id": trade_params.get("candidate_id"),
            "f5_refuse_reason": refuse,
        }
        if refuse:
            return None
        try:
            from src.judgment.apply_size import honor_f5_scaler_risk
            params = dict(trade_params) if isinstance(trade_params, Mapping) else {}
            honored, stamp = honor_f5_scaler_risk(
                nominal,
                scaler=self,
                trade_params=params,
                login=getattr(self, "login", None) or 0,
                ns=getattr(self, "ns", None) or F5_NAMESPACE or "operator",
                target_risk_usd=target,
            )
            if honored is None or not isinstance(stamp, dict):
                return None
            try:
                cash = float(honored)
                ceiling = float(stamp.get("binding_room_usd"))
            except (TypeError, ValueError):
                return None
            if (
                cash != cash
                or ceiling != ceiling
                or cash in (float("inf"), float("-inf"))
                or ceiling in (float("inf"), float("-inf"))
                or cash <= 0
                or cash > ceiling
            ):
                return None
            return cash
        except Exception:
            return None

def round_up_to_min_lot(lots: float, sym_info) -> "tuple[float, dict]":
    """Replace the sub-minimum SHED with a round-up, UNDER THE FLAG ONLY.

    Returns ``(lots, provenance)``. On success ``lots`` is ``volume_min`` -- guaranteed
    ``>= volume_min`` and on the ``volume_step`` grid, because every traded spec on both funded
    accounts has ``volume_min == volume_step``. Provenance records the inflation so the analysis
    reweights exactly; nothing is ever dropped.

    A provenance value other than ``applied``/``not_needed`` means the caller must REFUSE the
    trade -- an unreadable or pathological geometry must not produce an off-grid lot.
    """
    try:
        requested = float(lots)
        vmin = float(sym_info.volume_min)
        vstep = float(sym_info.volume_step)
        vmax = float(sym_info.volume_max)
    except (TypeError, ValueError, AttributeError):
        return lots, {"f5_round_up": "geometry_unreadable"}
    if not math.isfinite(requested):
        return lots, {"f5_round_up": "refused_nonfinite_lots"}
    if requested <= 0:
        return lots, {"f5_round_up": "refused_nonpositive_lots"}
    if not all(math.isfinite(value) for value in (vmin, vstep, vmax)) or vmin <= 0 or vstep <= 0 or vmax <= 0:
        return lots, {"f5_round_up": "geometry_invalid"}
    if requested >= vmin:
        return lots, {"f5_round_up": "not_needed", "f5_lot_inflation": 1.0}
    if vmin > vmax:
        # The pre-existing (min > max) pathology -- unreachable on either funded account (all 42
        # traded specs are min 0.01 / step 0.01) but it must not silently produce an off-grid lot.
        return lots, {"f5_round_up": "refused_vmin_above_vmax"}
    inflation = vmin / requested
    return round(vmin, 8), {
        "f5_round_up": "applied",
        "f5_lots_requested": requested,
        "f5_lots_placed": float(vmin),
        "f5_lot_inflation": inflation,
    }


# --------------------------------------------------------------------------------------------
# capture: one append-only JSONL, one row per decision-affecting event
# --------------------------------------------------------------------------------------------
class MinimalSizeCapture:
    """``shadow_logs/f5_minimal/<namespace>/events.jsonl``.

    NAMESPACED ON PURPOSE. ``shadow_logs/slippage.jsonl`` carries no namespace and no account
    field on any row, so with FOUR books writing (two accounts x two surfaces) its fill rows are
    indistinguishable except by symbol and ticket. Every row here stamps ``namespace`` and
    ``account_login``, and every row carries ``broker_mutation`` so a reader can tell an
    observation from a fill without knowing the event vocabulary.
    """

    def __init__(self, path: Path, namespace: str, account_login: Optional[int] = None):
        self._path = Path(path)
        self._ns = str(namespace)
        self._login = account_login
        self._lock = threading.RLock()

    @property
    def path(self) -> Path:
        return self._path

    def emit(self, event: str, payload: Mapping) -> None:
        row = {
            "schema": EVENT_SCHEMA,
            "event": str(event),
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "namespace": self._ns,
            "account_login": self._login,
            "broker_mutation": False,
        }
        row.update(payload or {})
        try:
            with self._lock:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                with self._path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
        except Exception:  # noqa: BLE001
            # Capture must NEVER break the live path. Deliberately broad: `default=str` calls
            # `str()` on anything unserialisable, and `str()` runs arbitrary `__repr__` code
            # that can raise ANY exception -- so a narrow tuple here would let a payload
            # object's own bug propagate into the tick loop of a book trading real money.
            # A lost row costs one line of analysis.
            pass


# --------------------------------------------------------------------------------------------
# news proximity -- §7.2 gap 5, free, and it decides whether a fill is analysable
# --------------------------------------------------------------------------------------------
def minutes_to_nearest_high_impact_event(when_utc: datetime, calendar_rows) -> Optional[float]:
    """Signed-magnitude minutes from ``when_utc`` to the nearest HIGH-impact calendar event.

    redacted_account recognises only 40 % of profit and 100 % of losses inside +/-5 min of a listed
    high-impact event, and the shipped news filter's post-event window is 2 minutes
    (``agent_config.yaml`` -- R2-bound and inside the activation-token digest, so it is NOT
    changed here; it is fixed at the next scheduled re-mint). Stamping the distance is free and
    lets the analysis EXCLUDE tainted fills instead of arguing about them later.

    Returns ``None`` when no HIGH event is parseable -- absence of a stamp is honest, a zero
    would be a lie.

    Parses ``scheduled_utc`` ISO, ``date``+``time_utc`` (HH:MM as in
    ``data/news_calendar.json``), and brief ``time_utc`` ISO. The old ISO-only
    ``time_utc`` path left ``f5_minutes_to_high_impact_event`` null on every
    live fill because the VPS calendar stores ``time_utc`` as HH:MM.
    """
    clock = f5_aware_utc(when_utc)
    if clock is None:
        return None
    best: Optional[float] = None
    for row in (calendar_rows or []):
        try:
            if not isinstance(row, Mapping):
                continue
            impact = str((row.get("impact") or row.get("importance") or "")).strip().lower()
            if impact not in ("high", "3", "red") and not row.get("official_high"):
                continue
            ts = f5_event_scheduled_utc(row)
            if ts is None:
                continue
            delta = abs((clock - ts).total_seconds()) / 60.0
            if best is None or delta < best:
                best = delta
        except (AttributeError, TypeError, ValueError):
            continue
    return best




# Challenge refuses are Choices. The unique highest probability decides.
# An empty answer does not restore the old boolean. There is no absent branch.
_FEAR_MODEL = "jev-1.13.0"
_FEAR_NS = "operator"
_FEAR_CACHE: dict = {}
_FEAR_INFLIGHT: set = set()


def fear_withholds(question, state, criteria, withhold, cache_key, instructions):
    """Choice for this state. A cached answer returns at once.

    A miss starts the post beside the caller and returns None. None does not
    restore the old boolean. The post's deadline is the next watched-bar print
    when that print is known, and no timeout when it is not.
    """

    cached = _FEAR_CACHE.get(cache_key)
    if cached is not None:
        fear_withholds.last = cached
        return question if cached.get("blocks") else None
    if cache_key in _FEAR_INFLIGHT:
        return None
    _FEAR_INFLIGHT.add(cache_key)

    def run() -> None:
        try:
            _fear_execute(question, state, criteria, withhold, cache_key, instructions)
        finally:
            _FEAR_INFLIGHT.discard(cache_key)

    threading.Thread(target=run, name="fear-choice", daemon=True).start()
    return None


def _fear_execute(question, state, criteria, withhold, cache_key, instructions):
    """Return ``question`` only when ``withhold`` is the unique highest probability.

    None means the old boolean does not fire: empty, tie, error, and every
    other alternative. Never raises. Never labels an unanswered hop as a mode.
    """
    import json
    import urllib.error
    import urllib.request
    from datetime import datetime, timezone

    order = tuple(criteria)
    if withhold not in criteria:
        fear_withholds.last = {"question": question, "blocks": False, "unanswered": True, "error": "withhold_not_in_criteria"}
        return None
    row = {
        "question": question,
        "alternative": None,
        "unanswered": True,
        "blocks": False,
        "probabilities": {},
        "flatten": False,
        "model": _FEAR_MODEL,
        "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    cached = _FEAR_CACHE.get(cache_key)
    if cached is not None:
        fear_withholds.last = cached
        return question if cached.get("blocks") else None
    try:
        from src.judgment.jev_client import (
            API_URL,
            _consume_call,
            calls_enabled,
            key_fingerprint,
            resolve_key,
        )
    except Exception as exc:
        row["error"] = type(exc).__name__
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    if not calls_enabled():
        row["error"] = "calls_off"
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    key, source = resolve_key()
    if not key:
        row["error"] = "key_missing"
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    if not _consume_call():
        row["error"] = "call_budget_exhausted"
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    payload = {
        "state": state,
        "model": _FEAR_MODEL,
        "questions": {
            question: {
                "type": "choice",
                "instructions": instructions,
                "criteria": dict(criteria),
            }
        },
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, default=str).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-fear-choice/1",
        },
    )
    deadline = None
    try:
        from src.components.ultimate_book.launcher_facts import ask_deadline_seconds

        deadline = ask_deadline_seconds()
    except Exception:
        deadline = None
    if deadline is not None and deadline <= 0:
        row["error"] = "state_expired"
        row["key_fingerprint"] = key_fingerprint(key)
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    try:
        if deadline is None:
            resp_ctx = urllib.request.urlopen(req)
        else:
            resp_ctx = urllib.request.urlopen(req, timeout=deadline)
        with resp_ctx as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        row["error"] = f"http_{exc.code}"
        row["key_fingerprint"] = key_fingerprint(key)
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    except Exception as exc:
        row["error"] = type(exc).__name__
        row["key_fingerprint"] = key_fingerprint(key)
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    answer = (body.get("answers") or {}).get(question) or {}
    probs = answer.get("probabilities") if isinstance(answer, dict) else None
    if not isinstance(probs, dict) or not probs:
        row["error"] = "probabilities_missing"
        row["key_fingerprint"] = key_fingerprint(key)
        fear_withholds.last = row
        _fear_receipt(row)
        return None
    best = None
    best_p = -1.0
    tied = False
    for name in order:
        try:
            raw = probs.get(name)
            if raw is None:
                continue
            p = float(raw)
        except (TypeError, ValueError):
            continue
        if best is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    alternative = None if tied or best is None else best
    row.update({
        "alternative": alternative,
        "unanswered": alternative is None,
        "blocks": alternative == withhold,
        "probabilities": {str(k): float(v) for k, v in probs.items()},
        "confidence": answer.get("confidence"),
        "model": body.get("model") or _FEAR_MODEL,
        "key_fingerprint": key_fingerprint(key),
        "key_source": source,
        "error": None if alternative else "tie",
    })
    if alternative is not None:
        _FEAR_CACHE[cache_key] = row
    fear_withholds.last = row
    _fear_receipt(row)
    return question if row["blocks"] else None


def _fear_receipt(row):
    try:
        import json
        from pathlib import Path
        path = (
            Path(__file__).resolve().parents[3]
            / "pipeline_state"
            / "ultimate_book"
            / _FEAR_NS
            / "judgment"
            / "fear_choices.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return


def _fear_boot_stamp():
    try:
        import json
        import os
        import sys
        argv = " ".join(sys.argv).replace("\\", "/").lower()
        if "operator" not in argv or "run_book" not in argv:
            return
        from datetime import datetime, timezone
        from pathlib import Path
        path = (
            Path(__file__).resolve().parents[3]
            / "pipeline_state"
            / "ultimate_book"
            / _FEAR_NS
            / "judgment"
            / "fear_gates_loaded.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "gtos.fear_gates.loaded.v0",
            "model": _FEAR_MODEL,
            "pid": os.getpid(),
            "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "empty_restores_old_boolean": False,
            "absent_branch": False,
            "flatten": False,
        }, indent=2) + "\n", encoding="utf-8")
    except Exception:
        return


def _cap_boot_stamp():
    try:
        import json
        import os
        import sys
        argv = " ".join(sys.argv).replace("\\", "/").lower()
        if "--namespace operator" not in argv or "run_book" not in argv:
            return
        if any(tok in argv for tok in ("friend_a", "redacted_account", "redacted_account", "redacted_account", "run_book_supervisor")):
            return
        from datetime import datetime, timezone
        from pathlib import Path
        path = (
            Path(__file__).resolve().parents[3]
            / "pipeline_state"
            / "ultimate_book"
            / _FEAR_NS
            / "judgment"
            / "trade_cap_loaded.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "gtos.trade_cap.loaded.v1",
            "pid": os.getpid(),
            "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "planted_stop_cap": False,
            "planted_stack_count": False,
            "empty_refuses": False,
        }, indent=2) + "\n", encoding="utf-8")
    except Exception:
        return


_fear_boot_stamp()
_cap_boot_stamp()

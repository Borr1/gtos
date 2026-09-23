"""Builds the book's GovernorState from live account facts, with persisted high-water + start-of-day
equity anchor. A WRONG high_water silently shifts the DD-derisk band and the max-DD wall
(admission.evaluate_governor), so it is persisted monotonically across the challenge.

State files (per namespace) under pipeline_state/ultimate_book/<namespace>/:
  high_water.json  {"high_water": float}                  -- monotonic peak equity
  day_anchor.json  {"date": "YYYY-MM-DD", "equity": float} -- start-of-(reset-window)-day equity

No order path. realized_today_pct uses the broker reset-window anchor. open_risk_pct is supplied by
the caller (the engine sums worst-case-stop risk over live book positions); defaults to 0.0 when none.

TWO broker-correctness anchors (both opt-in; defaults preserve pure-trailing/UTC behavior so existing
callers are unchanged — the LIVE book passes them explicitly via book_engine):

  static_initial_balance  -- the broker max-DD floor is STATIC from the INITIAL challenge balance
    (FTMO/FN: initial-10% => a FIXED 90k floor for a 100k account; it does NOT trail up with profit
    nor down). It is passed through to GovernorState.max_dd_reference_equity so admission.evaluate_governor
    computes the max-DD wall + de-risk band from this fixed reference (wall always = ref*(1-maxdd) = 90k),
    NOT from the trailing high-water. This both fixes the seeded-low case (an account that first-ran in
    drawdown no longer gets a sub-90k wall) AND removes the over-conservative trailing wall that crept
    ABOVE 90k once an account profited. NOTE: the validated MC (INTEG_portfolio_build) modelled a
    TRAILING peak DD ((peak-eq)/peak), which is STRICTER than the real static rule once in profit, so
    the static governor matches the true broker failure point and is safe vs the MC headline (the MC's
    fail-DD prob is a conservative upper bound on the real static-rule prob). high_water is retained as
    the >=equity sanity invariant only.

  daily_reset_offset_hours -- the broker daily-loss window resets at SERVER midnight, not UTC midnight
    (FTMO/FN server = UTC+3 => reset at 21:00 UTC). The start-of-day anchor keys on the server-local
    date so realized_today_pct tracks the broker's actual daily budget (consistent with monitor_books).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.utils.broker_accounting import (
    BrokerDealAccountingError,
    trade_deal_cash_delta,
)

from .admission import GovernorState
# Aliased: the constructor takes a float parameter of the same name, and a shadowed
# function that silently resolves to a float would be a very quiet bug.
from ...utils.broker_clock import UnknownBrokerClockError
from ...utils.broker_clock import daily_reset_offset_hours as _reset_calendar_offset_hours

LOGGER = logging.getLogger(__name__)


class GovernorStateBuilder:
    def __init__(self, repo_root: str, namespace: str = "ftmo_primary", *,
                 static_initial_balance: Optional[float] = None,
                 daily_reset_offset_hours: float = 0.0,
                 offset_provider=None,
                 reset_rule: Optional[str] = None):
        self._dir = os.path.join(repo_root, "pipeline_state", "ultimate_book", namespace)
        os.makedirs(self._dir, exist_ok=True)
        self._hw_path = os.path.join(self._dir, "high_water.json")
        self._anchor_path = os.path.join(self._dir, "day_anchor.json")
        # static max-DD floor reference (None => pure trailing high-water, backward-compatible)
        self._static_floor = (float(static_initial_balance)
                              if isinstance(static_initial_balance, (int, float))
                              and static_initial_balance > 0 else None)
        # broker daily-reset window offset from UTC in hours (0 => UTC midnight, backward-compatible).
        # This is the STATIC config fallback; when an offset_provider is supplied (the live book passes one
        # reading the broker-detected offset) the reset window is DST-correct -- see _effective_offset_h.
        self._reset_offset_h = float(daily_reset_offset_hours or 0.0)
        # The account's DECLARED daily-reset calendar, e.g. "europe_prague" for FTMO. None (or
        # "server") means the firm resets at its own server midnight, which is redacted_account's rule
        # and is what the detected offset already gives. See _effective_offset_h.
        self._reset_rule = (str(reset_rule).strip() or None) if reset_rule else None
        self._offset_provider = offset_provider

    def _effective_offset_h(self, now_utc: Optional[datetime] = None) -> float:
        """The offset in hours whose midnight is THIS ACCOUNT'S daily-loss reset instant.

        Two brokers, two different rules, and they are not interchangeable:

        * **redacted_account** resets at **00:00 SERVER time**, GMT+3 under DST and GMT+2 otherwise
          (help.redacted_account.com/en/articles/8394309). The live-detected broker offset IS that
          rule, so it is used directly and tracks the server's own DST flip automatically.
        * **FTMO** resets at **00:00 CE(S)T** -- Central European time, NOT its server clock
          (academy.ftmo.com/lesson/maximum-daily-loss/; recorded at config/profiles/ftmo.yaml:102
          as ``daily_reset_time: 00:00 CE(S)T``). FTMO's MT5 server follows the **US** DST
          calendar (measured -- see broker_clock.NEW_YORK_PLUS_7) while CE(S)T follows the
          **EU** one, so server midnight is 1 h before the real reset normally and **2 h
          before it during the ~4 weeks a year the two calendars disagree** (which includes
          2026-03-08..03-28, inside the sealed March window).

        Corrected 2026-07-26 (B56). Before this, every account used the detected server offset,
        which is right for redacted_account and **early** for FTMO -- the dangerous direction, since
        for that 1-2 h each night the governor believed the daily-loss budget had reset while
        FTMO was still counting losses against the previous day.

        When ``reset_rule`` names a calendar it wins, because it is the firm's stated rule.
        Otherwise the live-detected server offset is the clock fact and is used as returned.
        The static config offset is used only when detection is absent. The offset is stable
        within a server-day -- both DST flips happen at ~02:00-03:00
        local, far from the ~21:00-23:00 UTC day boundary -- so the reset DATE never advances
        spuriously mid-flip.
        """
        if self._reset_rule:
            try:
                hours = _reset_calendar_offset_hours(
                    now_utc or datetime.now(timezone.utc), self._reset_rule)
                if hours is not None:
                    return float(hours)
            except UnknownBrokerClockError:
                # An unrecognised rule name is a configuration error, not a runtime condition.
                # Fall through to the detected offset rather than raise into the decision path,
                # but do not stay silent about it.
                LOGGER.error("unknown daily-reset rule %r; falling back to the detected broker "
                             "offset. The reset window may be wrong for this account.",
                             self._reset_rule)
        prov = self._offset_provider
        if prov is not None:
            try:
                h = prov()
                if h is not None:
                    detected = float(h)
                    if detected == detected and detected not in (float("inf"), float("-inf")):
                        return detected
            except Exception:
                pass
        return self._reset_offset_h

    # ---- persistence (best-effort; never raises into the decision path) ----
    def _read(self, path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _write(self, path: str, obj: dict) -> None:
        try:
            # UNIQUE temp per write (pid+uuid): in the documented restart-race window two same-namespace
            # workers must NOT do concurrent truncating writes to ONE shared `high_water.json.tmp` /
            # `day_anchor.json.tmp` -> interleaved bytes produce corrupt JSON that os.replace publishes. A
            # wrong high_water silently shifts the max-DD wall + de-risk band, so each writer uses its OWN
            # tmp + atomic rename to keep every published state file well-formed.
            tmp = f"{path}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            os.replace(tmp, path)
        except OSError:
            pass

    def update_high_water(self, equity: float) -> float:
        # Pure trailing peak (>= equity). It is the max-DD SANITY invariant only — the max-DD WALL is
        # computed from the STATIC initial-balance reference (max_dd_reference_equity), not from this
        # peak, because the FTMO/FN floor is static (initial-10% = a fixed 90k), NOT trailing.
        stored = self._read(self._hw_path).get("high_water")
        hw = max(float(stored), float(equity)) if isinstance(stored, (int, float)) else float(equity)
        self._write(self._hw_path, {"high_water": hw})
        return hw

    def _reset_window_date(self, now_utc: datetime) -> str:
        """The broker reset-window date (server-local): UTC shifted by the (DST-correct) daily-reset offset."""
        now = now_utc.astimezone(timezone.utc)
        return (now + timedelta(hours=self._effective_offset_h(now))).strftime("%Y-%m-%d")

    def _reset_window_start_utc(self, now_utc: Optional[datetime] = None) -> datetime:
        """UTC instant at which the CURRENT reset-window (account-local day) began. local = UTC +
        offset, so local midnight today == (local midnight) converted back to UTC by subtracting the
        offset that was in force AT THAT MIDNIGHT (e.g. offset +3h => the day boundary is 21:00 UTC).

        The second conversion is the subtle one, and it was wrong. Subtracting the offset at ``now``
        assumes the offset has not changed since midnight -- true on 363 days a year and false on the
        two the reset calendar shifts. Measured on the CE(S)T rule: at the autumn seam
        (2026-10-25T01:00Z) the naive form moved the window START forward by an hour, which SHORTENS
        the window and drops an hour of realized loss out of the daily budget. That is the same
        direction as the defect this rule exists to fix, so it is repaired here rather than noted.

        One correction pass converges for a one-hour transition: re-evaluate the offset at the
        candidate instant, and if it disagrees with the offset at ``now``, redo the subtraction with
        it. Verified at all four EU seams in 2026-2027 and hourly across two years. The detected-offset
        path is unaffected by construction -- ``offset_provider`` takes no instant, so it returns the
        same value for both evaluations and the correction is a no-op.
        """
        now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
        off = self._effective_offset_h(now)
        local_now = now + timedelta(hours=off)
        local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = local_midnight - timedelta(hours=off)
        off_at_start = self._effective_offset_h(start)
        if off_at_start != off:
            start = local_midnight - timedelta(hours=off_at_start)
        return start

    def reconstruct_day_start_balance(self, mt5, now_utc: Optional[datetime] = None) -> Optional[float]:
        """Broker-correct daily-loss baseline = current balance - trading cash delta since the server-day
        boundary. It EXCLUDES floating P&L (so a position open across the boundary cannot corrupt the
        baseline) and is recoverable after a mid-day restart (when the persisted anchor is gone) — the two
        cases where anchoring to first-observed equity let a real -5% daily breach slip past the soft stop.
        Every BUY/SELL deal side is included because entry-side commission and fees change the account
        balance before a position closes. Non-trading balance operations are excluded and reconciled
        separately. Mirrors monitor_books.py. Returns None when balance, account-wide deal history, or a
        trading deal cannot be read exactly -> the caller must FAIL CLOSED rather than trust a wrong baseline.

        Baseline note: balance (vs broker max(balance, equity) at day start) is the only value recoverable
        from realized history; it is exactly right in the dangerous loss-carry case and matches the broker
        in the common case. A position carried across the boundary at large floating PROFIT is the one edge
        where this is slightly loose; the -3% soft daily stop + de-risk band (both < the -5% wall) hold the
        margin there."""
        try:
            bal = mt5.get_account_balance()
        except Exception:
            return None
        if not isinstance(bal, (int, float)) or bal <= 0:
            return None
        now = now_utc or datetime.now(timezone.utc)
        boundary = self._reset_window_start_utc(now)
        try:
            deals = mt5.get_account_history_deals(boundary, now)
        except Exception:
            return None
        if deals is None:
            return None
        realized = 0.0
        for d in deals:
            try:
                t = d.get("time")
                if t is None:
                    return None
                if t < boundary:                       # precise boundary guard (no off-by-one at the edge)
                    continue
                realized += trade_deal_cash_delta(d)
            except (BrokerDealAccountingError, TypeError, ValueError):
                return None
        return float(bal) - float(realized)

    def _balance_anchor(self, day_start_balance: float, equity: float,
                        now_utc: Optional[datetime] = None) -> float:
        """Persisted start-of-(server)-day daily-loss BASELINE = max(day_start_balance, day_start_equity).

        Two corrections vs a bare stored balance:
          - daily-baseline-balance-vs-max-balance-equity: FTMO/FN measure the daily window from
            max(balance, equity) at day start, so a position carried across the boundary at floating PROFIT
            makes the broker reference equity (> balance); using balance alone under-measures the loss and
            could let the broker breach -5% while the governor thinks it is fine. Persist the day-start
            EQUITY too and take the max.
          - day-anchor-no-selfheal: never trust a STALE-low stored anchor over a fresh reconstruction --
            take max(stored, fresh). A higher day-start reference = stricter daily-loss measure = SAFE."""
        now = now_utc or datetime.now(timezone.utc)
        today = self._reset_window_date(now)
        rec = self._read(self._anchor_path)
        if rec.get("date") == today and isinstance(rec.get("balance"), (int, float)):
            base = max(float(rec["balance"]), float(day_start_balance))       # self-heal vs a stale-low anchor
            if isinstance(rec.get("equity"), (int, float)):
                base = max(base, float(rec["equity"]))                        # broker max(balance, equity) ref
            return base
        # first cycle of the window: persist the day-start balance AND the current equity as the references
        self._write(self._anchor_path, {"date": today, "balance": float(day_start_balance),
                                        "equity": float(equity)})
        return max(float(day_start_balance), float(equity))

    def _equity_anchor(self, equity: float, now_utc: Optional[datetime] = None) -> float:
        """LEGACY/backward-compatible anchor (keys on current equity). Used only when no day-start balance
        is supplied (non-live callers/tests). The LIVE book always supplies a reconstructed balance."""
        now = now_utc or datetime.now(timezone.utc)
        today = self._reset_window_date(now)
        rec = self._read(self._anchor_path)
        if rec.get("date") == today and isinstance(rec.get("equity"), (int, float)):
            return float(rec["equity"])
        self._write(self._anchor_path, {"date": today, "equity": float(equity)})
        return float(equity)

    def day_anchor(self, equity: float, now_utc: Optional[datetime] = None) -> float:
        """Public alias preserved for external callers: the legacy equity anchor."""
        return self._equity_anchor(equity, now_utc)

    def reset_window_date(self, now_utc: Optional[datetime] = None) -> str:
        """Public: the broker reset-window (server-local) date string for `now` — the offset-aware day key
        the daily baseline uses, so callers stamp a matching provenance window-id (not a pure-UTC date)."""
        return self._reset_window_date(now_utc or datetime.now(timezone.utc))

    # ---- the build ----
    def build(self, *, equity: float, day_start_balance: Optional[float] = None,
              open_risk_pct: float = 0.0, now_utc: Optional[datetime] = None,
              circuit_breaker: bool = False) -> GovernorState:
        equity = float(equity)
        hw = self.update_high_water(equity)
        # daily baseline: the broker-correct day-start BALANCE when supplied (excludes floating P&L), else
        # the legacy equity anchor (backward-compatible for non-live callers/tests).
        if isinstance(day_start_balance, (int, float)) and day_start_balance > 0:
            anchor = self._balance_anchor(float(day_start_balance), equity, now_utc)
        else:
            anchor = self._equity_anchor(equity, now_utc)
        realized_today_pct = ((equity - anchor) / anchor) if anchor > 0 else 0.0
        return GovernorState(
            equity=equity,
            high_water=hw,
            realized_today_pct=realized_today_pct,
            open_risk_pct=float(open_risk_pct),
            operator_circuit_breaker=bool(circuit_breaker),
            # STATIC max-DD basis: the broker floor is initial-10% (a fixed 90k for 100k), so the wall
            # is pinned to the initial balance and does NOT trail up with profit.
            max_dd_reference_equity=float(self._static_floor or 0.0),
        )

    def from_mt5(self, mt5, *, open_risk_pct: float = 0.0, now_utc: Optional[datetime] = None,
                 circuit_breaker: bool = False) -> Optional[GovernorState]:
        """Build from a live mt5 interface. Returns None (fail-closed) if equity is unreadable. When the
        mt5 exposes account-wide deal history, the daily baseline is the reconstructed day-start BALANCE
        (broker-correct); otherwise it falls back to the legacy equity anchor."""
        try:
            equity = mt5.get_account_equity()
        except Exception:
            return None
        if not isinstance(equity, (int, float)) or equity <= 0:
            return None
        dsb = self.reconstruct_day_start_balance(mt5, now_utc)
        return self.build(equity=float(equity), day_start_balance=dsb, open_risk_pct=open_risk_pct,
                          now_utc=now_utc, circuit_breaker=circuit_breaker)

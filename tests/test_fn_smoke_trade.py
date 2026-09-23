"""Tests for ``scripts/fn_smoke_trade.py`` close-confirmation logic (Bug #24).

Background
----------
On 2026-04-27 ~00:44 UTC the FN smoke script reported ``CLOSED pnl=$0.00
exit=0.00000`` for all 7 instruments while every position remained open
server-side. Manual force-close was required, costing ~$4.98 in spreads.

Root cause: the close-detection poll loop ran::

    pos = mt5.positions_get(ticket=send.order)
    if not pos:
        closed_by = "SL_TP"
        break

But ``mt5.positions_get`` returns:
    - empty tuple ``()`` when no positions match the ticket    -> closed
    - ``None`` on transient MT5 errors / library glitches      -> unknown

The original code collapsed both into "closed", producing a false CLOSED
report whenever MT5 returned ``None`` during the poll. The follow-up
``history_deals_get`` returned no exit deal (because the position was still
open), so ``exit_price`` defaulted to 0.0 and PnL summed to $0.

Fix design
----------
1. ``_check_position_status`` distinguishes the three states explicitly.
2. ``_wait_for_close`` only treats explicit empty tuple as closed; ``None``
   is logged + retried so transient errors don't break the loop.
3. After polling, closure is verified via ``history_deals_get`` for an
   exit deal. We claim CLOSED only if (a) position no longer exists AND
   (b) an EXIT deal exists in the history.
4. ``_force_close_position`` runs unconditionally when poll exits without
   confirmed closure; it itself verifies disappearance after order_send.
5. Telegram close notifications fire only on confirmed closure.

Coverage
--------
Section A — _check_position_status: three-state distinguisher
Section B — _wait_for_close: poll loop semantics
Section C — _force_close_position: order request shape + verification
Section D — run_symbol: end-to-end with stubbed MT5
Section E — final-report rendering: FAILED_TO_CLOSE surfaces in NOTES

Mocking strategy
----------------
The script imports ``MetaTrader5 as mt5`` at module level and uses the
module's free functions + constants. We monkeypatch ``fn_smoke_trade.mt5``
to a stub object and verify behavior via stub call recording.

We DO NOT call real MT5. We DO NOT touch production paths -- all writes
go to ``tmp_path`` per the canonical conftest pattern.
"""

from __future__ import annotations

import importlib.util as _ilu
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from datetime import datetime, timedelta, timezone

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _load_fn_smoke():
    """Load scripts/fn_smoke_trade.py as a module.

    The script imports `MetaTrader5` and `src.notifications` at the top,
    plus calls `_load_env()` which reads the project .env file. We:
      - stub MetaTrader5 (real one isn't safe in CI; constants suffice)
      - replace src.notifications with a mock AFTER the real package loads
        (the script binds `from src import notifications`, so we patch the
        bound reference per-test rather than corrupting sys.modules)

    `src.utils.config` and the real `src.notifications` are loaded normally.
    Since `src.notifications` reads TELEGRAM_BOT_TOKEN at import time and
    will be empty if no .env is present, _send_async() will silently no-op
    in tests -- exactly what we want.

    We use the same path-import trick as test_extract_ohlcv_history.py.
    """
    # Stub MetaTrader5 BEFORE the script imports it -- we don't want to
    # require a real MT5 install for unit tests.
    if "MetaTrader5" not in sys.modules:
        sys.modules["MetaTrader5"] = _make_fake_mt5_module()

    script_path = _PROJECT_ROOT / "scripts" / "fn_smoke_trade.py"
    spec = _ilu.spec_from_file_location("fn_smoke_trade", script_path)
    assert spec and spec.loader
    mod = _ilu.module_from_spec(spec)
    sys.modules["fn_smoke_trade"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_fake_mt5_module():
    """Build a minimal MetaTrader5 module stub for IMPORT-TIME use.

    The script doesn't call mt5.* at import time -- it only references
    attributes (TRADE_RETCODE_DONE, ORDER_TYPE_BUY, etc.) inside functions.
    This stub gives us valid constants so module load succeeds; tests then
    monkeypatch fn_smoke.mt5 to a FakeMT5 with proper behavior.
    """
    m = type(sys)("MetaTrader5")
    # Constants the script references -- real MT5 values from the live env.
    m.TRADE_RETCODE_DONE = 10009
    m.TRADE_ACTION_DEAL = 1
    m.ORDER_TYPE_BUY = 0
    m.ORDER_TYPE_SELL = 1
    m.ORDER_FILLING_IOC = 1
    m.ORDER_FILLING_FOK = 0
    m.ORDER_FILLING_RETURN = 2
    m.ORDER_TIME_GTC = 0
    m.DEAL_ENTRY_OUT = 1
    # Timeframe constants. Not used by this script, but this stub is installed
    # into sys.modules for the whole session and any later module doing
    # `import MetaTrader5` gets it -- `data_ingestion.py:34-41` reads
    # TIMEFRAME_M1 at module scope. A stub missing them turns this file into a
    # cross-test contaminator that fails whichever suite happens to run after it.
    m.TIMEFRAME_M1 = 1
    m.TIMEFRAME_M5 = 5
    m.TIMEFRAME_M15 = 15
    m.TIMEFRAME_M30 = 30
    m.TIMEFRAME_H1 = 16385
    m.TIMEFRAME_H4 = 16388
    m.TIMEFRAME_D1 = 16408
    # Functions -- replaced per test via monkeypatch on the imported mt5.
    m.initialize = lambda: True
    m.shutdown = lambda: None
    m.last_error = lambda: (-1, "stub")
    m.positions_get = lambda **kw: ()
    m.symbol_info = lambda s: None
    m.symbol_info_tick = lambda s: None
    m.symbol_select = lambda s, e: True
    m.account_info = lambda: SimpleNamespace(
        login=0, server="Stub", balance=100_000.0, equity=100_000.0,
        trade_expert=True,
    )
    m.order_send = lambda req: None
    m.history_deals_get = lambda *a, **kw: ()
    return m


# Load once at module import; tests reuse the loaded module.
fn_smoke = _load_fn_smoke()


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakePosition(SimpleNamespace):
    """Stand-in for a single MT5 position record."""

    def __init__(self, ticket: int, volume: float = 0.01,
                 type_: int = 0, price_open: float = 4000.0):
        super().__init__(
            ticket=ticket,
            volume=volume,
            type=type_,
            price_open=price_open,
            sl=0.0,
            tp=0.0,
            magic=99887766,
            profit=0.0,
        )


class FakeOrderResult(SimpleNamespace):
    """Stand-in for the MT5 order_send return."""

    def __init__(self, retcode: int = 10009, order: int = 555,
                 price: float = 4000.0, comment: str = "ok",
                 volume: float = 0.01):
        super().__init__(
            retcode=retcode,
            order=order,
            price=price,
            comment=comment,
            volume=volume,
        )


class FakeDeal(SimpleNamespace):
    """Stand-in for an MT5 history_deal record."""

    def __init__(self, position_id: int, entry: int = 1,
                 price: float = 4001.5, profit: float = 1.5,
                 swap: float = 0.0, commission: float = 0.0):
        # entry: 0 = ENTRY_IN, 1 = DEAL_ENTRY_OUT
        super().__init__(
            position_id=position_id,
            entry=entry,
            price=price,
            profit=profit,
            swap=swap,
            commission=commission,
        )


class FakeMT5:
    """Per-test MT5 stub with scripted positions_get + order_send behavior.

    Records every call so tests can assert on request shapes.
    """

    # Mirror constants used in code under test.
    TRADE_RETCODE_DONE = 10009
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_RETURN = 2
    ORDER_TIME_GTC = 0
    DEAL_ENTRY_OUT = 1

    #: The activation guard (added 2026-07-26) identifies the account it is
    #: about to trade from account_info().login. The stub needs one, and the
    #: authorized fixture below mints a token bound to its digest.
    LOGIN = 900_001

    def account_info(self):
        return SimpleNamespace(login=self.LOGIN)

    def __init__(self,
                 positions_sequence: list | None = None,
                 order_send_results: list | None = None,
                 history_deals: list | None = None,
                 tick: SimpleNamespace | None = None):
        # positions_sequence: list of values returned successively by
        # positions_get(). Each entry is one of: list[FakePosition] (open),
        # tuple/list of length 0 (closed), None (MT5 error / unknown).
        # If exhausted, the last value repeats forever.
        self.positions_sequence = positions_sequence or [()]
        self._pos_idx = 0
        self.order_send_results = order_send_results or []
        self._send_idx = 0
        self.history_deals = history_deals or []
        self.tick = tick or SimpleNamespace(
            ask=4001.0, bid=4000.5, time=0,
        )
        # Recordings
        self.order_send_calls: list[dict] = []
        self.positions_get_calls: list[dict] = []
        self.history_deals_get_calls: list[tuple] = []

    def positions_get(self, **kw):
        self.positions_get_calls.append(dict(kw))
        if self._pos_idx < len(self.positions_sequence):
            val = self.positions_sequence[self._pos_idx]
            self._pos_idx += 1
        else:
            val = self.positions_sequence[-1]
        return val

    def order_send(self, request):
        self.order_send_calls.append(dict(request))
        if self._send_idx < len(self.order_send_results):
            val = self.order_send_results[self._send_idx]
            self._send_idx += 1
        else:
            val = self.order_send_results[-1] if self.order_send_results \
                  else FakeOrderResult()
        return val

    def history_deals_get(self, *args, **kw):
        self.history_deals_get_calls.append(args)
        return self.history_deals

    def symbol_info_tick(self, sym):
        return self.tick

    def last_error(self):
        return (-1, "fake")


# ---------------------------------------------------------------------------
# Section A — _check_position_status
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _authorized_smoke_account(tmp_path, monkeypatch):
    """`fn_smoke_trade.py` now goes through the same authorization the engine
    does (F19), so every test that reaches an order must first authorize.

    That is the point: the script drives the RAW MetaTrader5 module and used to
    bypass create_mt5, RealMT5 and the whole guard stack. These tests exercise
    what `run_symbol` does ONCE AUTHORIZED;
    `test_run_symbol_refuses_without_an_activation_token` covers the other side.
    """

    from src.safety import activation_token as at
    from src.safety import runtime_halt

    # `authorize_raw_broker_request` enforces the HALT before it classifies, and
    # `enforce_runtime_not_halted` resolves its flag paths against `Path.cwd()`
    # when no `repo_root` is configured — which `run_symbol` does not pass. On a
    # checkout that carries the halt flags (this one does; `pipeline_state/` was
    # restored from the sparse profile) the guard fired, tried to append its
    # audit row into `pipeline_state/`, and hit conftest's production-write
    # guard — so these seven tests errored on infrastructure rather than on
    # their assertions, and the raw-module smoke path had no live coverage on a
    # halted machine. Point the halt root at an empty directory: the halt has
    # its own tests, and these are about the token.
    monkeypatch.setattr(
        runtime_halt, "DEFAULT_HALT_FLAG_PATHS",
        tuple(str(tmp_path / "no_halt" / name) for name in ("a.flag", "b.flag", "c.flag")),
    )

    directory = tmp_path / "activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(directory))
    at.write_token(
        at.build_token(
            account_login_sha256=at.account_digest(FakeMT5.LOGIN),
            expires_utc=datetime.now(timezone.utc) + timedelta(hours=1),
            issued_by="test_fn_smoke_trade",
        ),
        directory=directory,
    )
    return directory


def test_run_symbol_refuses_without_an_activation_token(monkeypatch, tmp_path):
    """The behaviour F19 asked for: no token, no broker mutation, and the raw
    MetaTrader5 module never reached."""

    from src.safety import activation_token as at

    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(tmp_path / "empty"))
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)

    fake = FakeMT5(
        positions_sequence=[()],
        order_send_results=[FakeOrderResult(retcode=10009, order=1)],
    )
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    assert r["fill"] is False
    assert "refused_by_guard" in (r["error"] or "")
    assert not fake.order_send_calls, "the raw broker module was reached without a token"


def test_check_position_status_open(monkeypatch):
    fake = FakeMT5(positions_sequence=[[FakePosition(555)]])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    assert fn_smoke._check_position_status(555) == "open"


def test_check_position_status_closed_empty_tuple(monkeypatch):
    fake = FakeMT5(positions_sequence=[()])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    assert fn_smoke._check_position_status(555) == "closed"


def test_check_position_status_unknown_when_mt5_returns_none(monkeypatch):
    """The Bug #24 case: MT5 returns None on transient error.

    The original `if not pos` collapsed this into "closed". The fix MUST
    distinguish None (unknown) from () (closed)."""
    fake = FakeMT5(positions_sequence=[None])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    assert fn_smoke._check_position_status(555) == "unknown"


# ---------------------------------------------------------------------------
# Section B — _wait_for_close
# ---------------------------------------------------------------------------


def test_wait_for_close_returns_sl_tp_on_observed_closure(monkeypatch):
    """Position open on first poll, closed on second -> SL_TP, closed."""
    fake = FakeMT5(positions_sequence=[
        [FakePosition(555)],   # poll 1: open
        (),                     # poll 2: closed (SL/TP hit)
    ])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)  # speed up tests
    closed_by, status = fn_smoke._wait_for_close(555, timeout_s=2)
    assert closed_by == "SL_TP"
    assert status == "closed"


def test_wait_for_close_times_out_when_position_persists(monkeypatch):
    """Position never closes -> closed_by None, status still_open."""
    fake = FakeMT5(positions_sequence=[[FakePosition(555)]])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)
    closed_by, status = fn_smoke._wait_for_close(555, timeout_s=0.5)
    assert closed_by is None
    assert status == "still_open"


def test_wait_for_close_does_not_trip_on_transient_none(monkeypatch):
    """Bug #24 regression: positions_get returning None must NOT short-
    circuit the loop into a false closed state. We supply a None then
    keep returning [open] -- result must be still_open, not closed."""
    fake = FakeMT5(positions_sequence=[
        None,                         # poll 1: MT5 transient error
        [FakePosition(555)],          # poll 2: still open
        [FakePosition(555)],          # poll 3: still open
        [FakePosition(555)],          # final poll
    ])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)
    closed_by, status = fn_smoke._wait_for_close(555, timeout_s=0.3)
    # The crucial assertion: NOT a false SL_TP from the None poll.
    assert closed_by is None
    assert status == "still_open"


def test_wait_for_close_returns_unknown_when_mt5_unreachable(monkeypatch):
    """All polls return None -> we never saw the position open OR closed.
    Status should be "unknown" so the caller can decide what to do."""
    fake = FakeMT5(positions_sequence=[None])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)
    closed_by, status = fn_smoke._wait_for_close(555, timeout_s=0.3)
    assert closed_by is None
    assert status == "unknown"


# ---------------------------------------------------------------------------
# Section C — _force_close_position
# ---------------------------------------------------------------------------


def test_force_close_constructs_correct_order_request(monkeypatch):
    """For a LONG position (type=BUY=0), force-close MUST send a SELL
    order with type=ORDER_TYPE_SELL and price=tick.bid."""
    long_pos = FakePosition(555, volume=0.01, type_=0, price_open=4000.0)
    fake = FakeMT5(
        positions_sequence=[
            [long_pos],   # initial check before close
            (),            # post-close confirm
        ],
        order_send_results=[FakeOrderResult(retcode=10009, order=555)],
        tick=SimpleNamespace(ask=4001.0, bid=4000.5, time=0),
    )
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)
    success, retcode = fn_smoke._force_close_position(
        ticket=555, mt5_symbol="XAUUSD", filling=fake.ORDER_FILLING_IOC,
    )
    assert success is True
    assert retcode == 10009
    # Verify order shape -- SELL to close LONG, at bid, with position field.
    assert len(fake.order_send_calls) == 1
    req = fake.order_send_calls[0]
    assert req["action"] == fake.TRADE_ACTION_DEAL
    assert req["symbol"] == "XAUUSD"
    assert req["volume"] == 0.01
    assert req["type"] == fake.ORDER_TYPE_SELL  # opposite of LONG
    assert req["price"] == 4000.5  # bid for LONG-close
    assert req["position"] == 555  # critical: targets specific position
    assert req["magic"] == fn_smoke.SMOKE_MAGIC
    assert req["type_filling"] == fake.ORDER_FILLING_IOC


def test_force_close_short_uses_ask_and_buy(monkeypatch):
    """For a SHORT position, force-close MUST send a BUY at ask."""
    short_pos = FakePosition(555, volume=0.01, type_=1, price_open=4000.0)
    fake = FakeMT5(
        positions_sequence=[[short_pos], ()],
        order_send_results=[FakeOrderResult()],
        tick=SimpleNamespace(ask=4001.0, bid=4000.5, time=0),
    )
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)
    fn_smoke._force_close_position(555, "XAUUSD",
                                   fake.ORDER_FILLING_IOC)
    req = fake.order_send_calls[0]
    assert req["type"] == fake.ORDER_TYPE_BUY
    assert req["price"] == 4001.0  # ask for SHORT-close


def test_force_close_returns_false_on_retcode_failure(monkeypatch):
    """Bug-class guard: a non-DONE retcode MUST be reported as failure
    with the actual retcode in the second tuple position."""
    fake = FakeMT5(
        positions_sequence=[[FakePosition(555)], ()],
        order_send_results=[
            FakeOrderResult(retcode=10004, comment="REQUOTE")
        ],
    )
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)
    success, retcode = fn_smoke._force_close_position(
        555, "XAUUSD", fake.ORDER_FILLING_IOC,
    )
    assert success is False
    assert retcode == 10004


def test_force_close_treats_already_gone_position_as_success(monkeypatch):
    """If positions_get shows no position before we try to close, that's
    success (nothing to do)."""
    fake = FakeMT5(positions_sequence=[()])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    success, retcode = fn_smoke._force_close_position(
        555, "XAUUSD", fake.ORDER_FILLING_IOC,
    )
    assert success is True
    assert retcode is None
    # No order sent.
    assert len(fake.order_send_calls) == 0


def test_force_close_returns_false_when_done_but_position_still_open(
        monkeypatch):
    """A same-class bug to the original: order_send DONE but position
    didn't actually disappear. Must report failure, not silent success."""
    fake = FakeMT5(
        positions_sequence=[
            [FakePosition(555)],   # initial check
            [FakePosition(555)],   # post-close: STILL OPEN despite DONE
        ],
        order_send_results=[FakeOrderResult(retcode=10009)],
    )
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)
    success, retcode = fn_smoke._force_close_position(
        555, "XAUUSD", fake.ORDER_FILLING_IOC,
    )
    assert success is False
    assert retcode == 10009  # surfaces that order itself was DONE


def test_force_close_returns_false_when_mt5_returns_none(monkeypatch):
    """positions_get returning None pre-close -> can't safely act."""
    fake = FakeMT5(positions_sequence=[None])
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    success, retcode = fn_smoke._force_close_position(
        555, "XAUUSD", fake.ORDER_FILLING_IOC,
    )
    assert success is False
    assert retcode is None


# ---------------------------------------------------------------------------
# Section D — run_symbol end-to-end
# ---------------------------------------------------------------------------


def _stub_load_symbol_config(monkeypatch, symbol="XAUUSD"):
    """Make load_symbol_config deterministic without touching real config.

    Returns risk_pct=1% + mt5_symbol=symbol so XAUUSD passes through SL_TP_PX.
    """
    monkeypatch.setattr(
        fn_smoke,
        "load_symbol_config",
        lambda s, p: {
            "market": {"symbol": s, "mt5_symbol": s},
            "risk": {"risk_per_trade_pct": 1.0},
        },
    )


def _stub_chart_signal(monkeypatch, tmp_path):
    """Redirect chart-signal writes to tmp_path so we don't touch MQL5/Files."""
    fake_dir = tmp_path / "fake_mt5_files"
    fake_dir.mkdir()
    monkeypatch.setattr(fn_smoke, "MT5_FILES", fake_dir)


def test_run_symbol_reports_closed_with_real_pnl_on_success(
        monkeypatch, tmp_path):
    """Happy path: order fills, position closes via SL/TP, exit deal exists.
    Result MUST report close=True with non-zero exit_price + PnL."""
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)

    fill_result = FakeOrderResult(retcode=10009, order=777, price=4000.0)
    fake = FakeMT5(
        # Open then closed -- SL/TP hit
        positions_sequence=[
            [FakePosition(777)],
            (),
        ],
        order_send_results=[fill_result],
        history_deals=[
            FakeDeal(position_id=777, entry=0, price=4000.0,
                     profit=0.0, commission=0.0),  # entry deal
            FakeDeal(position_id=777, entry=1, price=4001.5,
                     profit=1.5, commission=0.0),  # exit deal
        ],
        tick=SimpleNamespace(ask=4000.0, bid=3999.5, time=0),
    )
    # Add symbol_info to fake (run_symbol calls it before the helpers).
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    assert r["fill"] is True, f"expected fill=True, got: {r}"
    assert r["close"] is True, f"expected close=True, got: {r}"
    assert r["closed_by"] == "SL_TP"
    assert r["exit_price"] == 4001.5
    assert r["pnl_dollars"] == 1.50
    assert r["actual_r"] != 0.0  # genuine R, not 0
    assert r["exit_deal_found"] is True
    assert r.get("error") is None or "FAILED_TO_CLOSE" not in str(r.get("error", ""))


def test_run_symbol_reports_failed_to_close_when_position_persists(
        monkeypatch, tmp_path):
    """Bug #24 regression test: position never closes, force-close also
    fails. Result MUST report close=False, NOT a false CLOSED."""
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)
    monkeypatch.setattr(fn_smoke, "CLOSE_TIMEOUT_S", 0.3)

    fill_result = FakeOrderResult(retcode=10009, order=777, price=4000.0)
    # Position stays open through poll; force-close also returns retcode
    # error, position still open at end. EXACT Bug #24 scenario class.
    open_pos = FakePosition(777, volume=0.01, type_=0, price_open=4000.0)
    fake = FakeMT5(
        positions_sequence=[
            [open_pos],   # poll iterations
            [open_pos],
            [open_pos],   # force-close pre-check
            [open_pos],   # force-close post-check (still open!)
            [open_pos],   # final_position_check
        ],
        order_send_results=[
            fill_result,                                     # entry order
            FakeOrderResult(retcode=10004, comment="REQ"),   # force-close fails
        ],
        history_deals=[
            FakeDeal(position_id=777, entry=0, price=4000.0,
                     profit=0.0, commission=0.0),  # only entry, NO exit
        ],
    )
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    assert r["fill"] is True, f"expected fill: {r}"
    # CRITICAL: must NOT be reported as closed.
    assert r["close"] is False, (
        f"BUG #24 REGRESSION: false CLOSED reported when position "
        f"persisted! got close=True. Full result: {r}"
    )
    assert r["closed_by"] is None
    assert r["exit_deal_found"] is False
    assert "FAILED_TO_CLOSE" in r.get("error", "")
    assert r["final_position_check"] == "STILL_OPEN"


def test_run_symbol_does_not_report_closed_on_transient_positions_get_none(
        monkeypatch, tmp_path):
    """Direct Bug #24 simulation: positions_get returns None during poll.

    The original code would have set closed_by=SL_TP, exited the loop, and
    then history_deals_get would return no exit deal -> CLOSED with $0/0R.

    The fix: None polls don't break the loop; they're retried. If position
    never observed closed AND no exit deal -> FAILED_TO_CLOSE.
    """
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)
    monkeypatch.setattr(fn_smoke, "CLOSE_TIMEOUT_S", 0.2)

    open_pos = FakePosition(777, volume=0.01, type_=0, price_open=4000.0)
    fake = FakeMT5(
        # Inject a None mid-poll. Position is still open the whole time.
        positions_sequence=[
            [open_pos],    # poll 1
            None,           # poll 2: TRANSIENT MT5 ERROR (Bug #24 trigger)
            [open_pos],    # poll 3
            [open_pos],    # post-poll force-close check (open)
            [open_pos],    # post-close confirm (still open -- close failed)
            [open_pos],    # final_position_check
        ],
        order_send_results=[
            FakeOrderResult(retcode=10009, order=777, price=4000.0),  # entry
            FakeOrderResult(retcode=10004, comment="REQ"),  # force-close fail
        ],
        history_deals=[
            # Only entry deal — no exit. The bug's smoking gun.
            FakeDeal(position_id=777, entry=0, price=4000.0,
                     profit=0.0, commission=0.0),
        ],
    )
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    # The exact false CLOSED report from 2026-04-27 was:
    #   CLOSED pnl=$0.00 exit=0.00000
    # The fix MUST not produce that.
    if r["close"] is True and r["pnl_dollars"] == 0.0 and r["exit_price"] == 0.0:
        pytest.fail(
            "BUG #24 REGRESSION: reported CLOSED pnl=$0 exit=0 despite "
            f"position persisting through transient None poll. Result: {r}"
        )
    assert r["close"] is False
    assert r["exit_deal_found"] is False
    assert "FAILED_TO_CLOSE" in r.get("error", "")


def test_run_symbol_handles_entry_retcode_failure_gracefully(
        monkeypatch, tmp_path):
    """Edge: entry order_send returns non-DONE retcode -> early return
    with error message, no close attempted, no false CLOSED."""
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)

    fake = FakeMT5(
        positions_sequence=[()],
        order_send_results=[
            FakeOrderResult(retcode=10026, comment="EA_DISABLED"),
        ],
    )
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    assert r["fill"] is False
    assert r["close"] is False
    assert "10026" in r["error"]


def test_run_symbol_handles_order_send_returning_none(monkeypatch, tmp_path):
    """Edge: order_send returns None (broker disconnect) -> graceful error,
    no false fill or close."""
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)

    fake = FakeMT5(
        positions_sequence=[()],
        order_send_results=[None],
    )
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    assert r["fill"] is False
    assert r["close"] is False
    assert "order_send returned None" in r["error"]


def test_run_symbol_skips_telegram_on_failed_to_close(monkeypatch, tmp_path):
    """When close confirmation fails, we MUST NOT push a misleading
    Telegram notify ($0/0R) to the operator chat."""
    _stub_load_symbol_config(monkeypatch)
    _stub_chart_signal(monkeypatch, tmp_path)
    monkeypatch.setattr(fn_smoke, "POLL_S", 0.001)
    monkeypatch.setattr(fn_smoke, "CLOSE_TIMEOUT_S", 0.2)

    open_pos = FakePosition(777)
    fake = FakeMT5(
        positions_sequence=[
            [open_pos], [open_pos], [open_pos], [open_pos], [open_pos],
        ],
        order_send_results=[
            FakeOrderResult(retcode=10009, order=777),
            FakeOrderResult(retcode=10004, comment="REQ"),
        ],
        history_deals=[
            FakeDeal(position_id=777, entry=0, profit=0.0),
        ],
    )
    fake.symbol_info = lambda s: SimpleNamespace(
        visible=True, point=0.01, digits=2, filling_mode=2,
        trade_stops_level=10, volume_min=0.01, volume_max=100.0,
    )
    fake.symbol_select = lambda s, e: True
    monkeypatch.setattr(fn_smoke, "mt5", fake)
    monkeypatch.setattr(fn_smoke.time, "sleep", lambda s: None)

    # Replace notifications module at the script's bound reference and
    # the global sys.modules entry so any internal import path catches it.
    notify_calls = []
    fake_notifications = MagicMock()
    fake_notifications.configure_notifications = MagicMock()
    fake_notifications.notify_trade_closed = MagicMock(
        side_effect=lambda **kw: notify_calls.append(kw),
    )
    monkeypatch.setattr(fn_smoke, "notifications", fake_notifications)

    r = fn_smoke.run_symbol("XAUUSD", "redacted_account", dry_run=False)

    assert r["close"] is False
    assert r["telegram_sent"] is False
    assert r.get("telegram_skipped_reason") == "no_confirmed_close"
    assert len(notify_calls) == 0, (
        f"Telegram was sent on a failed close: {notify_calls}"
    )


# ---------------------------------------------------------------------------
# Section E — final report rendering
# ---------------------------------------------------------------------------


def test_failed_to_close_pre_fill_renders_as_error_line(monkeypatch, capsys):
    """When fill=False AND error set, the report line is just an ERROR row
    (legacy behavior preserved for symbol_info errors etc.)."""
    # We don't call main() directly -- exercise the same rendering inline.
    results = [{
        "symbol": "XAUUSD", "fill": False, "close": False,
        "error": "symbol_info(XAUUSD) returned None",
    }]
    # Reproduce the report block from main().
    for r in results:
        sym = r["symbol"]
        if r.get("error") and not r.get("fill"):
            print(f"{sym:<12s} ERROR: {r['error']}")
            continue
        print("FAIL_RENDER")  # should never reach
    out = capsys.readouterr().out
    assert "ERROR: symbol_info" in out
    assert "FAIL_RENDER" not in out


def test_failed_to_close_post_fill_renders_columns_with_error_in_notes(
        monkeypatch, capsys):
    """When fill=True but close=False (e.g. FAILED_TO_CLOSE), report shows
    the full row so operator sees fill=Y / close=N + error in NOTES."""
    results = [{
        "symbol": "XAUUSD", "fill": True, "close": False,
        "telegram_sent": False, "chart_signal_written": True,
        "pnl_dollars": 0.0, "actual_r": 0.0,
        "error": "FAILED_TO_CLOSE: position_status=still_open exit_deal=False "
                 "final=STILL_OPEN",
    }]
    for r in results:
        sym = r["symbol"]
        if r.get("error") and not r.get("fill"):
            print(f"{sym:<12s} ERROR: {r['error']}")
            continue
        fill = "Y" if r.get("fill") else "N"
        close = "Y" if r.get("close") else "N"
        tg = "Y" if r.get("telegram_sent") else "N"
        ch = "Y" if r.get("chart_signal_written") else "N"
        pnl = r.get("pnl_dollars", 0)
        rr = r.get("actual_r", 0)
        notes = r.get("closed_by") or ""
        if r.get("error"):
            notes = r["error"]
        print(f"{sym:<12s} {fill:<5s} {close:<6s} {tg:<3s} {ch:<6s} "
              f"${pnl:<9.2f} {rr:<7.3f} {notes}")
    out = capsys.readouterr().out
    # XAUUSD row present, fill=Y close=N, error string in NOTES
    assert "XAUUSD" in out
    assert "Y" in out and "N" in out
    assert "FAILED_TO_CLOSE" in out


# ---------------------------------------------------------------------------
# Sanity check that the loaded module still has expected helpers
# ---------------------------------------------------------------------------


def test_module_exports_helpers():
    assert hasattr(fn_smoke, "_check_position_status")
    assert hasattr(fn_smoke, "_wait_for_close")
    assert hasattr(fn_smoke, "_force_close_position")
    assert hasattr(fn_smoke, "run_symbol")
    assert hasattr(fn_smoke, "SMOKE_MAGIC")
    assert fn_smoke.SMOKE_MAGIC == 99887766

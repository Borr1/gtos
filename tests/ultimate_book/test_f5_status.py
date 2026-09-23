"""`scripts/f5_status.py` — the operator view, which with no loss budget IS the control.

Two things are tested and they are the two that matter: it never mutates the broker, and its
CHECK line fires on each of the conditions it exists to catch. A status tool that reports "OK"
while the notional ledger is unwired would silently waste the whole month, and one that could
place an order would be a second uncontrolled path to real money.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mt5.mt5_interface import MAGIC_F5_MINIMAL, MAGIC_NUMBER

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def f5_status():
    spec = importlib.util.spec_from_file_location(
        "_f5_status", REPO / "scripts" / "f5_status.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeMT5:
    """Records every attribute touched, so 'read-only' is measured rather than asserted."""

    def __init__(self, equity, balance, login, positions):
        self._equity, self._balance, self._login = equity, balance, login
        self._positions = positions
        self.calls: list[str] = []

    def initialize(self, path=None):
        self.calls.append("initialize")
        return True

    def account_info(self):
        self.calls.append("account_info")
        return SimpleNamespace(equity=self._equity, balance=self._balance, login=self._login)

    def positions_get(self):
        self.calls.append("positions_get")
        return list(self._positions)

    def shutdown(self):
        self.calls.append("shutdown")

    def last_error(self):
        return (0, "ok")


def _pos(magic):
    return SimpleNamespace(magic=magic, symbol="XAUUSD", ticket=1, volume=0.01)


def test_f5_status_is_read_only(f5_status):
    """It opens MT5 for `account_info()` and `positions_get()` and NOTHING else. Any order
    verb reaching this module would be a second uncontrolled path to real money."""
    fake = _FakeMT5(108342.47, 108000.0, 531325516, [_pos(MAGIC_NUMBER)])
    block = f5_status.account_block("FTMO", "term", "ns_armed", "ns_f5", 90000.0, 100000.0,
                                    mt5_module=fake)
    assert block["error"] is None if "error" in block else True
    assert set(fake.calls) == {"initialize", "account_info", "positions_get", "shutdown"}
    for verb in ("order_send", "order_check", "order_calc_margin", "positions_close"):
        assert verb not in fake.calls

    src = (REPO / "scripts" / "f5_status.py").read_text()
    assert "order_send" not in src
    # and it imports no execution code, so it cannot reach a broker mutation transitively
    assert "from src.components" not in src


def test_f5_status_splits_positions_by_magic(f5_status):
    """The isolation invariant, checked live every time anyone looks. `other > 0` means
    something is placing under an unexpected identity."""
    fake = _FakeMT5(100000.0, 100000.0, 1, [
        _pos(MAGIC_NUMBER), _pos(MAGIC_NUMBER),
        _pos(MAGIC_F5_MINIMAL), _pos(MAGIC_F5_MINIMAL), _pos(MAGIC_F5_MINIMAL),
        _pos(0),
    ])
    b = f5_status.account_block("FTMO", "t", "a", "f", 90000.0, 100000.0, mt5_module=fake)
    assert (b["open_armed"], b["open_f5"], b["open_other"]) == (2, 3, 1)
    assert any("UNEXPECTED magic" in c for c in f5_status.checks(b))


def test_f5_status_prices_the_derisk_knee(f5_status):
    """The one channel through which the experiment can touch the ARMED book, and the reason
    the number to watch is 'distance to $93,000' rather than 'how much have I lost'."""
    above = f5_status.account_block("FTMO", "t", "a", "f", 90000.0, 100000.0,
                                    mt5_module=_FakeMT5(108342.47, 108342.47, 1, []))
    assert above["armed_size_multiplier_now"] == pytest.approx(1.0)
    assert above["to_derisk_knee_usd"] == pytest.approx(15342.47)
    assert above["armed_pp_cost_per_100usd"] == 0.0        # exactly zero, not "small"
    assert not [c for c in f5_status.checks(above) if "DE-RISK" in c]

    inside = f5_status.account_block("FN", "t", "a", "f", 90000.0, 100000.0,
                                     mt5_module=_FakeMT5(91500.0, 91500.0, 2, []))
    assert inside["armed_size_multiplier_now"] == pytest.approx(0.5)   # dd 8.5 % of a 7-10 band
    assert inside["to_derisk_knee_usd"] == pytest.approx(-1500.0)
    assert inside["armed_pp_cost_per_100usd"] == pytest.approx(3.3333, rel=1e-3)
    assert any("DE-RISK BAND" in c for c in f5_status.checks(inside))


def test_f5_status_flags_an_unwired_notional_ledger(f5_status, tmp_path, monkeypatch):
    """THE invalidation canary. If a close's notional/actual ratio is ~1 the scaler is out
    of the path and the book is risking the FULL DIAL in real dollars -- silently, for a
    whole month, with every other indicator green.

    ROOT-CAUSE REWRITE 2026-08-25 (stale expectation). The check contract moved from a
    fixed median-ratio band to a PER-CLOSE, scale-free verdict (`_ratio_verdict`,
    scripts/f5_status.py:185-240): the first live fill selected a 0.2244 % cell whose
    honest ratio is 22.6x, so a fixed 50-500x band called perfect wiring a failure. Each
    close row carries its own `f5_nominal/actual/intended_risk_usd` (emitted at
    minimal_size.py:577-584, copied onto the close at book_owner.py:583), the unwired
    canary is observed < 1.5 while nominal/intended >= 3, and the check line now reads
    "MINIMAL-SIZE SCALER IS NOT IN THE PATH" rather than "NOTIONAL". Rows are modelled
    with the fields real closes always carry."""
    monkeypatch.setattr(f5_status, "REPO", tmp_path)
    ev = tmp_path / "shadow_logs" / "f5_minimal" / "f" / "events.jsonl"
    ev.parent.mkdir(parents=True, exist_ok=True)

    def _close(actual):
        # dial-sized nominal $1,500 against the fixed $75 unit; `actual` is what was risked
        return json.dumps({
            "event": "f5_trade_closed", "ticket": 1, "sleeve": "s", "symbol": "XAUUSD",
            "f5_nominal_risk_usd": 1500.0, "f5_intended_risk_usd": 75.0,
            "f5_actual_risk_usd": actual, "f5_notional_over_actual": 1500.0 / actual})

    # scaler dropped out: actual == nominal, observed ratio collapses to 1.0
    ev.write_text("\n".join(_close(1500.0) for _ in range(6)))
    b = f5_status.account_block("FTMO", "t", "a", "f", 90000.0, 100000.0,
                                mt5_module=_FakeMT5(100000.0, 100000.0, 1, []))
    assert b["f5_notional_actual_ratio_median"] == pytest.approx(1.0)
    assert b["f5_ratio_unwired"] == 6
    assert any("SCALER IS NOT IN THE PATH" in c for c in f5_status.checks(b))

    # ...and a correctly wired ledger sits on its own per-cell expectation and is silent
    ev.write_text("\n".join(_close(75.0) for _ in range(6)))
    ok = f5_status.account_block("FTMO", "t", "a", "f", 90000.0, 100000.0,
                                 mt5_module=_FakeMT5(100000.0, 100000.0, 1, []))
    assert ok["f5_notional_actual_ratio_median"] == pytest.approx(20.0)
    assert ok["f5_ratio_unwired"] == 0 and ok["f5_ratio_offband"] == 0
    assert not [c for c in f5_status.checks(ok) if "notional" in c.lower() or "SCALER" in c]


def test_f5_status_renders_without_a_ledger(f5_status, tmp_path, monkeypatch):
    """Day zero: no ledger, no events, no fills. It must render rather than raise -- an
    operator view that crashes before the first trade is not a control."""
    monkeypatch.setattr(f5_status, "REPO", tmp_path)
    b = f5_status.account_block("FTMO", "t", "a", "f", 90000.0, 100000.0,
                                mt5_module=_FakeMT5(108342.47, 108000.0, 1, []))
    text = f5_status.render([b])
    assert "F5 STATUS" in text
    assert "to $90,000 floor" in text
    assert "notional/actual n/a" in text
    assert "CHECK     OK" in text


def test_f5_status_surfaces_a_broker_error_instead_of_pretending(f5_status):
    class _Dead(_FakeMT5):
        def initialize(self, path=None):
            return False

    b = f5_status.account_block("FTMO", "t", "a", "f", 90000.0, 100000.0,
                                mt5_module=_Dead(0, 0, 0, []))
    assert "mt5.initialize failed" in b["error"]
    assert "** " in f5_status.render([b])

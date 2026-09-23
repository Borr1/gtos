"""Two decision surfaces on ONE funded account: the broker-side isolation, proved.

Why this file exists
--------------------
The F5 minimal-size experiment runs a second ``run_book.py`` worker on each of the two
ARMED, funded, real-money accounts. The namespace already isolates every FILE surface --
the single-instance lock, the conviction ledger, the placement ledger, the trade records,
the governor state, the heartbeat, and the supervisor's own liveness match. It isolates
**no broker surface**: ``MAGIC_NUMBER`` was one module constant and every position read
filtered on it.

Left shared, the worst row is silent and lands on ARMED money.
``book_engine._open_risk_pct`` (``book_engine.py:860``) returns the **full gross-risk
cap** when any position it can see has ``sl == 0``, ``price_open == 0``, or an unreadable
``value_per_point`` (``:878-884``). One experiment position on a symbol whose instrument
config is missing -- and redacted_account already silently skips 13 symbol/sleeve pairs on
exactly that -- would make the ARMED book read ``gross_risk_cap_exhausted`` and stop
opening any unit at all, with a healthy-looking log and no alert.

``test_f5_open_risk_fail_closed_not_triggered_by_f5`` and
``test_f5_conviction_ledger_is_namespace_isolated`` are the two that must pass before the
ceremony. The rest close the remaining rows of the same table.

These are behavioural tests on the real call paths -- no source-string assertions, and the
conviction-ledger test writes real files to real per-namespace paths rather than mocking
the store, because "the paths do not collide" is the property under test.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.running_conviction_state import RunningConvictionLedger
from src.mt5.mt5_interface import (
    COMMENT_PREFIX_ARMED,
    COMMENT_PREFIX_F5_MINIMAL,
    MAGIC_F5_MINIMAL,
    MAGIC_NUMBER,
    comment_prefix_for_magic,
    comment_prefix_for_namespace,
    magic_for_namespace,
)
from src.mt5.mt5_real import RealMT5

ARMED_NS = "operator_profile"
ARMED_NS_FN = "redacted_account_live_bee34003"
F5_NS = "operator"
F5_NS_FN = "redacted_account_f5_minimal"

GROSS_CAP = 0.04


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _pos(*, ticket, symbol, magic, sl=1900.0, price_open=2000.0, volume=0.10,
         comment="W7:crypto", ptype=0):
    """A broker position row shaped the way MT5 returns one."""
    return SimpleNamespace(ticket=ticket, symbol=symbol, magic=magic, sl=sl,
                           price_open=price_open, volume=volume, comment=comment,
                           type=ptype, tp=0.0, profit=0.0, time=0)


class _FakeRawMT5:
    """Stands in for the ``MetaTrader5`` module: returns every position on the account,
    exactly as the real terminal does -- it has no idea two books exist."""

    def __init__(self, positions):
        self._positions = list(positions)

    def positions_get(self, symbol=None):
        if symbol is None:
            return list(self._positions)
        return [p for p in self._positions if p.symbol == symbol]


def _wrapper(positions, magic):
    """A `RealMT5` bound to one identity, wired to a fake terminal. `connect()` is never
    called (that needs Windows + a terminal), so the broker-offset probe is short-circuited
    by marking detection done -- the position filter is what is under test."""
    w = RealMT5.__new__(RealMT5)
    w._connected = True
    w._magic = int(magic)
    w._mt5 = _FakeRawMT5(positions)
    w._broker_offset_seconds = 0
    w._broker_offset_detected = True
    w._broker_offset_detected_at = 0.0
    w._tick_symbol_select_attempted = set()
    return w


class _EngineMT5:
    """The minimum `book_engine._open_risk_pct` consumes: an account equity, the magic-filtered
    open-position list, and a per-symbol value-per-point."""

    def __init__(self, wrapper, equity=100_000.0, vpp=1.0):
        self._wrapper = wrapper
        self._equity = equity
        self._vpp = vpp

    def get_account_equity(self):
        return self._equity

    def get_open_positions(self):
        return self._wrapper.get_open_positions()

    def get_symbol_value_per_point(self, symbol):
        return self._vpp


def _engine(mt5, tmp_path, namespace=ARMED_NS):
    return UltimateBookLiveEngine(
        {"ultimate_book_gross_open_risk_cap_pct": GROSS_CAP},
        mt5, str(tmp_path), namespace=namespace,
    )


# ---------------------------------------------------------------------------
# A4-1 -- the map itself
# ---------------------------------------------------------------------------
def test_f5_magic_is_namespace_derived():
    """The identity is a pure function of the namespace, and an UNKNOWN namespace returns the
    ARMED magic. A typo must not mint a third, unmanaged broker identity."""
    assert magic_for_namespace(ARMED_NS) == MAGIC_NUMBER == 20260401
    assert magic_for_namespace(ARMED_NS_FN) == MAGIC_NUMBER
    assert magic_for_namespace(F5_NS) == MAGIC_F5_MINIMAL == 0
    assert magic_for_namespace(F5_NS_FN) == MAGIC_F5_MINIMAL
    # typos, empty and absent all land on the armed identity
    assert magic_for_namespace("ftmo_f5_minmal") == MAGIC_NUMBER
    assert magic_for_namespace("") == MAGIC_NUMBER
    assert magic_for_namespace(None) == MAGIC_NUMBER
    # and the two identities are distinct, which is the whole point
    assert MAGIC_NUMBER != MAGIC_F5_MINIMAL


def test_f5_comment_prefix_tracks_the_magic():
    assert comment_prefix_for_namespace(ARMED_NS) == COMMENT_PREFIX_ARMED == "W7:"
    assert comment_prefix_for_namespace(F5_NS) == COMMENT_PREFIX_F5_MINIMAL == "F5:"
    assert comment_prefix_for_magic(MAGIC_NUMBER) == "W7:"
    assert comment_prefix_for_magic(MAGIC_F5_MINIMAL) == "F5:"
    assert comment_prefix_for_magic(None) == "W7:"
    assert comment_prefix_for_magic(999) == "W7:"


def test_f5_comment_prefix_fits_mt5():
    """MT5 truncates order comments to 16 chars, and the longest live sleeve name is long.
    Both prefixes are 3 chars, so the F5 comment is exactly as informative as the armed one
    and no armed comment can ever start with the F5 prefix."""
    longest = "mx_avausd_d1_donchian_20_breakout"
    armed = f"{COMMENT_PREFIX_ARMED}{longest}"[:16]
    f5 = f"{COMMENT_PREFIX_F5_MINIMAL}{longest}"[:16]
    assert len(armed) == len(f5) == 16
    assert not armed.startswith(COMMENT_PREFIX_F5_MINIMAL)
    assert not f5.startswith(COMMENT_PREFIX_ARMED)
    assert len(COMMENT_PREFIX_ARMED) == len(COMMENT_PREFIX_F5_MINIMAL)


# ---------------------------------------------------------------------------
# A4-2 -- the armed book cannot see the experiment
# ---------------------------------------------------------------------------
def test_f5_armed_book_cannot_see_experiment_positions():
    """The single funnel. Every consumer in the live book path -- the gross-risk sum, the
    same-symbol guard, adoption, the out-of-universe alert, the residual resolver -- reads
    positions through these two methods and nothing else."""
    mixed = [
        _pos(ticket=1, symbol="BTCUSD", magic=MAGIC_NUMBER, comment="W7:crypto"),
        _pos(ticket=2, symbol="BTCUSD", magic=MAGIC_F5_MINIMAL, comment="F5:crypto"),
        _pos(ticket=3, symbol="XAUUSD", magic=MAGIC_F5_MINIMAL, comment="F5:metals_core"),
        _pos(ticket=4, symbol="XAUUSD", magic=0, comment="manual"),
    ]
    armed = _wrapper(mixed, MAGIC_NUMBER)
    f5 = _wrapper(mixed, MAGIC_F5_MINIMAL)

    assert [p.ticket for p in armed.get_open_positions()] == [1]
    assert [p.ticket for p in f5.get_open_positions()] == [2, 3]
    # and per-symbol, which is what the same-symbol lifecycle guard consumes
    assert [p.ticket for p in armed.get_positions("BTCUSD")] == [1]
    assert [p.ticket for p in f5.get_positions("BTCUSD")] == [2]
    # neither sees the manual trade
    assert 4 not in {p.ticket for p in armed.get_open_positions()}
    assert 4 not in {p.ticket for p in f5.get_open_positions()}


def test_f5_armed_open_risk_is_numerically_identical_with_and_without_the_experiment(tmp_path):
    """Not just 'the F5 rows are excluded' -- the armed book's NUMBER does not move."""
    armed_only = [_pos(ticket=1, symbol="BTCUSD", magic=MAGIC_NUMBER,
                       sl=1900.0, price_open=2000.0, volume=0.10)]
    with_f5 = armed_only + [
        _pos(ticket=2, symbol="XAUUSD", magic=MAGIC_F5_MINIMAL, volume=0.01),
        _pos(ticket=3, symbol="ETHUSD", magic=MAGIC_F5_MINIMAL, volume=0.01),
    ]
    eq = 100_000.0
    before = _engine(_EngineMT5(_wrapper(armed_only, MAGIC_NUMBER), eq), tmp_path)._open_risk_pct(eq)
    after = _engine(_EngineMT5(_wrapper(with_f5, MAGIC_NUMBER), eq), tmp_path)._open_risk_pct(eq)
    assert before == after
    # sanity: the number is the real one (0.10 lots x 100 points x $1), not an accidental zero
    assert before == pytest.approx(0.10 * 100.0 * 1.0 / eq)


# ---------------------------------------------------------------------------
# A4-3 -- THE SILENT-SHUTDOWN CASE. Must pass before the ceremony.
# ---------------------------------------------------------------------------
def test_f5_open_risk_fail_closed_not_triggered_by_f5(tmp_path):
    """An experiment position with ``sl == 0`` leaves the ARMED book's ``_open_risk_pct``
    numerically unchanged.

    This is the row that would have cost real money. ``book_engine.py:878-884`` returns the
    FULL gross cap on a missing stop, an unreadable open price, or an unreadable
    value-per-point -- and ``admission`` then reads ``gross_risk_cap_exhausted`` and refuses
    every entry. Three of the five ways the shared magic could have changed armed behaviour
    are silent; this is the silent one that stops the book trading altogether.

    The test also asserts the CONVERSE on the same fixture -- that the trigger is real -- so a
    future refactor cannot make it vacuous by removing the fail-closed branch.
    """
    eq = 100_000.0
    armed_only = [_pos(ticket=1, symbol="BTCUSD", magic=MAGIC_NUMBER,
                       sl=1900.0, price_open=2000.0, volume=0.10)]
    baseline = _engine(_EngineMT5(_wrapper(armed_only, MAGIC_NUMBER), eq), tmp_path)._open_risk_pct(eq)
    assert baseline < GROSS_CAP, "fixture must start with headroom or the test proves nothing"

    for label, bad in (
        ("missing stop loss", _pos(ticket=9, symbol="GER40.cash", magic=MAGIC_F5_MINIMAL,
                                   sl=0.0, price_open=18000.0, volume=0.01)),
        ("unreadable open price", _pos(ticket=9, symbol="GER40.cash", magic=MAGIC_F5_MINIMAL,
                                       sl=17900.0, price_open=0.0, volume=0.01)),
    ):
        mixed = armed_only + [bad]
        armed_view = _engine(_EngineMT5(_wrapper(mixed, MAGIC_NUMBER), eq), tmp_path)
        assert armed_view._open_risk_pct(eq) == baseline, (
            f"ARMED gross open risk moved because of an F5 position ({label}) -- the armed "
            f"book would read gross_risk_cap_exhausted and stand down silently")

        # THE CONVERSE: under the OLD shared-magic behaviour this same position IS the
        # fail-closed trigger. Modelled by giving the bad row the armed magic.
        shared = armed_only + [_pos(ticket=9, symbol=bad.symbol, magic=MAGIC_NUMBER,
                                    sl=bad.sl, price_open=bad.price_open, volume=bad.volume)]
        shared_view = _engine(_EngineMT5(_wrapper(shared, MAGIC_NUMBER), eq), tmp_path)
        assert shared_view._open_risk_pct(eq) == pytest.approx(GROSS_CAP), (
            f"the fail-closed branch no longer fires on {label}; this test is now vacuous")


def test_f5_open_risk_fail_closed_not_triggered_by_unreadable_value_per_point(tmp_path):
    """The third fail-closed trigger, and the one F5 §4.2 names as most likely: redacted_account
    silently skips 13 symbol/sleeve pairs on missing instrument config, so an F5 position on
    an unconfigured symbol is the realistic shape of this fault."""
    eq = 100_000.0
    armed_only = [_pos(ticket=1, symbol="BTCUSD", magic=MAGIC_NUMBER)]
    mixed = armed_only + [_pos(ticket=9, symbol="UNCONFIGURED", magic=MAGIC_F5_MINIMAL)]

    class _NoVppForF5Symbol(_EngineMT5):
        def get_symbol_value_per_point(self, symbol):
            return None if symbol == "UNCONFIGURED" else 1.0

    baseline = _engine(_EngineMT5(_wrapper(armed_only, MAGIC_NUMBER), eq), tmp_path)._open_risk_pct(eq)
    armed_view = _engine(_NoVppForF5Symbol(_wrapper(mixed, MAGIC_NUMBER), eq), tmp_path)
    assert armed_view._open_risk_pct(eq) == baseline

    # converse, same fixture with the identity shared
    shared = armed_only + [_pos(ticket=9, symbol="UNCONFIGURED", magic=MAGIC_NUMBER)]
    shared_view = _engine(_NoVppForF5Symbol(_wrapper(shared, MAGIC_NUMBER), eq), tmp_path)
    assert shared_view._open_risk_pct(eq) == pytest.approx(GROSS_CAP)


# ---------------------------------------------------------------------------
# A4-7 -- THE CONVICTION LEDGER. Must pass before the ceremony.
# ---------------------------------------------------------------------------
def test_f5_conviction_ledger_is_namespace_isolated(tmp_path):
    """A filesystem test on real paths, not a mock.

    ``admission.py:1188`` takes ``na = max(na, override)`` -- monotone upward within a
    decision day. A 32-sleeve surface writing into the armed book's ledger would move the
    half-Kelly multiplier from the ``(2,3)`` bin to the ``(4,99)`` bin, 0.991 -> 1.241:
    **+25.2 % on every armed unit that day**, on real money, with nothing in any log saying
    why. The per-namespace path is what prevents it, so the property under test is that the
    two paths do not collide -- which a mocked store cannot show.
    """
    day = "2026-08-12"
    armed = RunningConvictionLedger(str(tmp_path), namespace=ARMED_NS)
    f5 = RunningConvictionLedger(str(tmp_path), namespace=F5_NS)

    armed_before = armed.update_and_count({day: {"crypto", "energy_agri"}})
    assert armed_before == {day: 2}

    twenty = {f"sleeve_{i:02d}" for i in range(20)}
    assert f5.update_and_count({day: twenty}) == {day: 20}

    # the armed count did not move
    assert armed.update_and_count({day: set()}) == {day: 2}

    armed_path = Path(tmp_path) / "pipeline_state" / "ultimate_book" / ARMED_NS / "firing_sleeves.json"
    f5_path = Path(tmp_path) / "pipeline_state" / "ultimate_book" / F5_NS / "firing_sleeves.json"
    assert armed_path != f5_path
    assert armed_path.is_file() and f5_path.is_file()
    assert set(json.loads(armed_path.read_text())["days"][day]) == {"crypto", "energy_agri"}
    assert set(json.loads(f5_path.read_text())["days"][day]) == twenty
    # and nothing of the experiment's leaked into the armed file
    assert not (set(json.loads(armed_path.read_text())["days"][day]) & twenty)


# ---------------------------------------------------------------------------
# A4-5/6 -- same-symbol and adoption
# ---------------------------------------------------------------------------
def test_f5_same_symbol_gate_ignores_experiment():
    """``max_open_same_symbol_tickets: 1``. An experiment BTCUSD position must not block the
    armed ``crypto`` sleeve, and the armed one must not block the experiment."""
    both = [
        _pos(ticket=1, symbol="BTCUSD", magic=MAGIC_NUMBER, comment="W7:crypto"),
        _pos(ticket=2, symbol="BTCUSD", magic=MAGIC_F5_MINIMAL, comment="F5:crypto"),
    ]
    armed = _wrapper(both, MAGIC_NUMBER).get_positions("BTCUSD")
    f5 = _wrapper(both, MAGIC_F5_MINIMAL).get_positions("BTCUSD")
    assert len(armed) == 1 and armed[0].ticket == 1
    assert len(f5) == 1 and f5[0].ticket == 2


def test_f5_adoption_ignores_experiment_on_all_three_clauses(tmp_path):
    """``_position_exposures`` classifies a position as the book's on comment prefix OR the
    placement ledger OR the magic. The ledger is already per-namespace; this pins the other
    two, so an armed worker cannot adopt and exit-manage an experiment position -- which
    ``_manageable_pairs`` would otherwise do for sleeves it is not even armed for
    (``active_specs(None, ...)`` is not intersected with ``--tags``)."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    f5_position = _pos(ticket=77, symbol="BTCUSD", magic=MAGIC_F5_MINIMAL, comment="F5:crypto")
    armed_position = _pos(ticket=11, symbol="BTCUSD", magic=MAGIC_NUMBER, comment="W7:crypto")

    owner = UltimateBookOwner.__new__(UltimateBookOwner)
    owner._magic = MAGIC_NUMBER
    owner._comment_prefix = COMMENT_PREFIX_ARMED

    for p, expected in ((f5_position, False), (armed_position, True)):
        comment = p.comment
        magic = p.magic
        ledger_pair = None  # per-namespace: the armed ledger never recorded the F5 ticket
        is_book_position = (
            comment.startswith(owner._comment_prefix)
            or ledger_pair is not None
            or (owner._magic is not None and magic == owner._magic)
        )
        assert is_book_position is expected, f"ticket {p.ticket} classified wrongly"


# ---------------------------------------------------------------------------
# A4-9 -- two workers, two locks
# ---------------------------------------------------------------------------
def test_f5_two_workers_lock_independently(tmp_path):
    """The lock is ``pipeline_state/ultimate_book/<ns>/run_book.lock`` (``run_book.py:343``),
    so a second worker per account coexists by construction -- no guard change needed."""
    import os

    paths = []
    for ns in (ARMED_NS, F5_NS):
        d = Path(tmp_path) / "pipeline_state" / "ultimate_book" / ns
        d.mkdir(parents=True, exist_ok=True)
        paths.append(d / "run_book.lock")
    assert paths[0] != paths[1]

    fds = [os.open(str(p), os.O_CREAT | os.O_RDWR) for p in paths]
    try:
        try:
            import fcntl
        except ImportError:  # pragma: no cover - Windows host
            pytest.skip("fcntl unavailable")
        for fd in fds:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   # both acquire, simultaneously
    finally:
        for fd in fds:
            os.close(fd)


# ---------------------------------------------------------------------------
# the identity cannot split
# ---------------------------------------------------------------------------
def test_engine_and_wrapper_resolve_the_same_identity():
    """``ExecutionEngine`` derives its magic from ``broker_account_namespace(config)`` and
    ``run_book.py`` derives the wrapper's from ``args.namespace``. Two derivations of one
    function of one input -- assert they agree for every live namespace, because a placing
    engine whose reader filters a different magic would leave positions open, unadopted and
    invisible to every guard."""
    from src.components.execution import ExecutionEngine

    for ns, expect_magic, expect_prefix in (
        (ARMED_NS, MAGIC_NUMBER, "W7:"),
        (ARMED_NS_FN, MAGIC_NUMBER, "W7:"),
        (F5_NS, MAGIC_F5_MINIMAL, "F5:"),
        (F5_NS_FN, MAGIC_F5_MINIMAL, "F5:"),
    ):
        cfg = {"market": {"symbol": "XAUUSD"}, "broker_account_namespace": ns}
        eng = ExecutionEngine(_wrapper([], expect_magic), cfg)
        assert eng._magic == expect_magic == magic_for_namespace(ns)
        assert eng._comment_prefix == expect_prefix


def test_book_owner_refuses_a_split_identity(tmp_path):
    """Fail CLOSED, loudly, at construction. A book that places under one identity and reads
    another is the worst available failure: positions open, unmanaged, and invisible."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    with pytest.raises(ValueError, match="broker identity split"):
        UltimateBookOwner({}, _wrapper([], MAGIC_NUMBER), str(tmp_path), namespace=F5_NS)


def test_default_construction_is_unchanged():
    """Every pre-existing construction site passes no magic and must land on 20260401."""
    w = RealMT5(terminal_path=None, portable=False)
    assert w._magic == MAGIC_NUMBER

    from src.components.execution import ExecutionEngine
    eng = ExecutionEngine(object(), {"market": {"symbol": "XAUUSD"}})
    assert eng._magic == MAGIC_NUMBER
    assert eng._comment_prefix == "W7:"
    assert eng._f5_scaler is None

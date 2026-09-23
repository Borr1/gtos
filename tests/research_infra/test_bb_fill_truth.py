"""Session BB — behavioural pins on the fill-truth machinery and the silence check.

Every test here asserts BEHAVIOUR, never a source string: a grep-for-substring test passes
against a wrong implementation, which is the failure mode `CLAUDE.md` §6 names.

The three things worth pinning, and why each:

  1. **The outcome-blind projection.** `bb_fill_truth.project()` is the only path from the
     estate artifact into the cadence stages, and the whole reason this session's fire-rate
     half costs the multiplicity family nothing is that no return field crosses it. A future
     edit that adds `r_gross` "for convenience" would silently turn a free measurement into a
     charged one, so the key set is asserted rather than trusted.

  2. **The occupancy guard's semantics.** One position per BROKER SYMBOL across sleeves, a
     blocked decision DROPPED and never deferred, and per-(sleeve, symbol, day) dedup. These
     are claims about `book_owner.py:1727-1735` and `:1793-1850`; if the model drifts from
     them the published fill prior stops describing the live book.

  3. **The silence counter's weekday axis.** The one design choice that makes the alarm
     honest is that a weekend is not silence. It is easy to "simplify" into calendar days and
     the result reads plausible while firing ~40 % early over long weekends.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
P13 = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FT = _load("bb_fill_truth_undertest", P13 / "bb_fill_truth.py")
SIL = _load("book_silence_check_undertest", REPO / "scripts/book_silence_check.py")


def _row(sleeve, symbol, entry, exit_, **extra):
    return {"sleeve": sleeve, "symbol": symbol, "entry_utc": entry, "exit_utc": exit_,
            "decision_day": entry[:10], **extra}


# ---------------------------------------------------------------- 1. outcome-blind
def test_projection_emits_exactly_five_keys_and_drops_every_return_field():
    src = _row("crypto", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-08T04:00:00+00:00",
               r_gross=3.5, r_net=3.1, mfe_r=4.0, mae_r=-0.5, exit_reason="target")
    out = FT.project([src])
    assert len(out) == 1
    assert set(out[0]) == {"sleeve", "symbol", "entry_utc", "exit_utc", "decision_day"}
    for leaked in ("r_gross", "r_net", "mfe_r", "mae_r", "exit_reason"):
        assert leaked not in out[0], f"{leaked} reached the outcome-blind stage"


def test_projection_builds_new_dicts_rather_than_aliasing_the_source():
    """A filter over the original dict would let a later key ride along. It BUILDS."""
    src = _row("crypto", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-08T04:00:00+00:00")
    out = FT.project([src])[0]
    src["r_gross"] = 99.0
    assert "r_gross" not in out


# ---------------------------------------------------------------- 2. the occupancy guard
def test_second_decision_while_symbol_is_held_is_dropped_not_deferred():
    rows = FT.project([
        _row("crypto", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-10T04:00:00+00:00"),
        # fires two days later, while the first is still open -> live `continue`s
        _row("crypto", "BTCUSD", "2025-01-08T04:00:00+00:00", "2025-01-09T04:00:00+00:00"),
    ])
    occ = FT.occupancy(rows, ("crypto",))
    assert occ["n_archive_decisions"] == 2
    assert occ["n_live_equivalent_fills"] == 1
    # and it is DROPPED: the queue does not re-place it after the holder exits
    assert occ["suppressed_by_reason"].get("symbol_occupied") == 1


def test_guard_is_cross_sleeve_because_it_is_scoped_to_the_broker_symbol():
    """`_same_broker_symbol_open_exposures` (book_owner.py:386-399) is symbol-scoped."""
    rows = FT.project([
        _row("sub_mid_dn_revert", "XAUUSD",
             "2025-01-06T04:00:00+00:00", "2025-01-10T04:00:00+00:00"),
        _row("sub_xvol_pullback", "XAUUSD",
             "2025-01-07T04:00:00+00:00", "2025-01-08T04:00:00+00:00"),
    ])
    occ = FT.occupancy(rows, ("sub_mid_dn_revert", "sub_xvol_pullback"))
    assert occ["n_live_equivalent_fills"] == 1
    assert occ["cross_sleeve_blocks"] == {"sub_xvol_pullback<-sub_mid_dn_revert": 1}


def test_a_different_symbol_is_never_blocked():
    rows = FT.project([
        _row("crypto", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-10T04:00:00+00:00"),
        _row("crypto", "DASHUSD", "2025-01-07T04:00:00+00:00", "2025-01-09T04:00:00+00:00"),
    ])
    assert FT.occupancy(rows, ("crypto",))["n_live_equivalent_fills"] == 2


def test_same_sleeve_symbol_day_is_deduped_even_after_the_position_closed():
    """`already_placed_today` (book_owner.py:1727-1735) is a DAY key, not an open-position key."""
    rows = FT.project([
        _row("crypto", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-06T08:00:00+00:00"),
        _row("crypto", "BTCUSD", "2025-01-06T12:00:00+00:00", "2025-01-06T16:00:00+00:00"),
    ])
    occ = FT.occupancy(rows, ("crypto",))
    assert occ["n_live_equivalent_fills"] == 1
    assert occ["suppressed_by_reason"].get("already_placed_today") == 1


def test_a_decision_after_the_holder_exits_fills_on_a_later_day():
    rows = FT.project([
        _row("crypto", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-07T04:00:00+00:00"),
        _row("crypto", "BTCUSD", "2025-01-08T04:00:00+00:00", "2025-01-09T04:00:00+00:00"),
    ])
    assert FT.occupancy(rows, ("crypto",))["n_live_equivalent_fills"] == 2


def test_dotted_and_underscored_broker_names_are_one_occupancy_key():
    """`US30.cash` in the estate and `US30_cash` in the bar archive are one broker symbol."""
    rows = FT.project([
        _row("a", "US30.cash", "2025-01-06T04:00:00+00:00", "2025-01-10T04:00:00+00:00"),
        _row("b", "US30_cash", "2025-01-07T04:00:00+00:00", "2025-01-08T04:00:00+00:00"),
    ])
    assert FT.occupancy(rows, ("a", "b"))["n_live_equivalent_fills"] == 1


def test_sleeves_outside_the_book_neither_fill_nor_block():
    """`--tags` bounds generation, so an unarmed sleeve cannot occupy a symbol."""
    rows = FT.project([
        _row("not_armed", "BTCUSD", "2025-01-06T04:00:00+00:00", "2025-01-10T04:00:00+00:00"),
        _row("crypto", "BTCUSD", "2025-01-07T04:00:00+00:00", "2025-01-08T04:00:00+00:00"),
    ])
    occ = FT.occupancy(rows, ("crypto",))
    assert occ["n_archive_decisions"] == 1
    assert occ["n_live_equivalent_fills"] == 1


# ---------------------------------------------------------------- 3. the silence counter
@pytest.fixture
def th():
    return {"warn_sessions": 15, "alert_sessions": 22, "source": "test",
            "expected_false_alarms_per_year": {"warn": 1.1, "alert": 0.0}}


def test_weekend_is_not_silence():
    # Fri 2026-07-24 -> Mon 2026-07-27 is 3 calendar days and ONE weekday session.
    assert SIL.weekday_sessions_between(dt.date(2026, 7, 24), dt.date(2026, 7, 27)) == 1


def test_the_day_of_the_last_fill_is_not_counted():
    assert SIL.weekday_sessions_between(dt.date(2026, 7, 27), dt.date(2026, 7, 27)) == 0


def test_a_future_or_equal_today_never_goes_negative():
    assert SIL.weekday_sessions_between(dt.date(2026, 7, 27), dt.date(2026, 7, 20)) == 0


def test_state_ladder_is_ok_warn_alert_at_the_measured_boundaries(th):
    last = dt.date(2026, 1, 1)

    def state_at(sessions):
        d, n = last, 0
        while n < sessions:
            d += dt.timedelta(days=1)
            if d.weekday() < 5:
                n += 1
        return SIL.silence_state(last, d, th)["state"]

    assert state_at(14) == SIL.OK
    assert state_at(15) == SIL.WARN
    assert state_at(21) == SIL.WARN
    assert state_at(22) == SIL.ALERT


def test_silence_state_reports_the_weekday_axis_not_the_calendar_axis(th):
    st = SIL.silence_state(dt.date(2026, 7, 24), dt.date(2026, 7, 27), th)
    assert st["silent_weekday_sessions"] == 1
    assert st["silent_calendar_days"] == 3
    assert st["state"] == SIL.OK


def test_the_tool_refuses_a_literal_threshold_when_the_receipt_is_absent(tmp_path):
    with pytest.raises(SystemExit) as e:
        SIL.load_thresholds("FTMO", tmp_path / "nope.json")
    assert "threshold receipt not found" in str(e.value)


def test_thresholds_load_from_the_committed_receipt_and_are_ordered():
    t = SIL.load_thresholds("FTMO")
    assert 0 < t["warn_sessions"] <= t["alert_sessions"]
    assert t["armed_set"] == ["crypto", "energy_agri", "sub_xvol_pullback",
                              "sub_mid_dn_revert", "mx_btcusd_d1_donchian_20_breakout"]


def test_redacted_account_loads_its_own_current_four_sleeve_threshold():
    t = SIL.load_thresholds("redacted_account")
    assert t["account"] == "redacted_account"
    assert t["armed_set"] == ["crypto", "energy_agri", "sub_xvol_pullback",
                              "sub_mid_dn_revert"]


def test_exit_code_carries_the_state(capsys, th):
    """0 OK / 1 WARN / 2 ALERT, so a scheduler branches without parsing text."""
    rc = SIL.main(["--account", "FTMO", "--last-fill", "2026-07-27",
                   "--today", "2026-07-28"])
    assert rc == 0
    rc = SIL.main(["--account", "FTMO", "--last-fill", "2026-05-01",
                   "--today", "2026-07-28"])
    assert rc == 2

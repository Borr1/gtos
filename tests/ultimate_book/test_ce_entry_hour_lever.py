"""Session CE (B2314-B2318) — the ratified entry-hour convention on the live generation path.

Behavioural throughout. The two properties that matter most are the ones a source-grep cannot
see: that the default path is INERT (an armed book must not change because a flag exists), and
that the lever FAILS OPEN to the committed contract rather than deferring forever on a dark
clock — the opposite of `spread_geometry`'s fail-closed, on purpose and for a stated reason.
"""
from __future__ import annotations

import datetime as dt

import pytest

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.entry_hour import (
    RATIFIED_TARGET_HOUR, EntryHourSelectionError, deferral_reason, parse_entry_hour,
)

UTC = dt.timezone.utc
H4, D1, M15 = 16388, 16408, 15
TF_OF = {"h4_sleeve": H4, "d1_sleeve": D1, "m15_sleeve": M15}
KNOWN = set(TF_OF)


class _Spec:
    def __init__(self, tag, timeframe=H4):
        self.tag, self.cluster, self.timeframe = tag, "substrate", timeframe


class _Intent:
    def __init__(self, sleeve="h4_sleeve"):
        self.sleeve, self.stop_dist, self.direction = sleeve, 1.0, 1
        self.decision_day = "2026-07-31"


class _MT5:
    def get_tick(self, symbol):        # pragma: no cover - the lever never fetches a tick
        raise AssertionError("the entry-hour lever must not touch the broker")


def _engine(tmp_path, **kw):
    return UltimateBookLiveEngine({}, _MT5(), str(tmp_path), namespace="ce_test", **kw)


# --------------------------------------------------------------------------- parse


def test_absent_selection_is_off_and_is_the_default():
    assert parse_entry_hour(None) == {}


def test_a_bare_sleeve_name_gets_the_ratified_hour():
    assert parse_entry_hour("h4_sleeve", known_sleeves=KNOWN) == {
        "h4_sleeve": RATIFIED_TARGET_HOUR}
    assert RATIFIED_TARGET_HOUR == 1, "the ratified convention is broker hour 01"


def test_an_explicit_hour_is_honoured():
    assert parse_entry_hour("d1_sleeve:3", known_sleeves=KNOWN,
                            timeframe_of=TF_OF) == {"d1_sleeve": 3}


@pytest.mark.parametrize("raw", ["", "   "])
def test_the_empty_string_is_refused_not_read_as_all(raw):
    # `--tags ""` is falsy and therefore means ALL sleeves. Two flags whose empty string means
    # opposite things is the trap; neither reading is offered here.
    with pytest.raises(EntryHourSelectionError, match="EMPTY"):
        parse_entry_hour(raw, known_sleeves=KNOWN)


def test_an_unknown_sleeve_is_refused_not_dropped():
    with pytest.raises(EntryHourSelectionError, match="unknown sleeve"):
        parse_entry_hour("no_such_sleeve", known_sleeves=KNOWN)


def test_hour_zero_is_refused_as_a_no_op_spelled_as_a_change():
    with pytest.raises(EntryHourSelectionError, match="committed behaviour"):
        parse_entry_hour("h4_sleeve:0", known_sleeves=KNOWN, timeframe_of=TF_OF)


@pytest.mark.parametrize("raw", ["h4_sleeve:24", "h4_sleeve:-1"])
def test_an_out_of_range_hour_is_refused(raw):
    with pytest.raises(EntryHourSelectionError, match="broker hours are 0..23"):
        parse_entry_hour(raw, known_sleeves=KNOWN, timeframe_of=TF_OF)


def test_a_non_integer_hour_is_refused():
    with pytest.raises(EntryHourSelectionError, match="not an integer"):
        parse_entry_hour("h4_sleeve:one", known_sleeves=KNOWN)


def test_a_sleeve_named_twice_is_refused():
    with pytest.raises(EntryHourSelectionError, match="twice"):
        parse_entry_hour("h4_sleeve,h4_sleeve:2", known_sleeves=KNOWN, timeframe_of=TF_OF)


def test_a_stray_comma_is_refused():
    with pytest.raises(EntryHourSelectionError, match="stray comma"):
        parse_entry_hour("h4_sleeve,,d1_sleeve", known_sleeves=KNOWN, timeframe_of=TF_OF)


# ---------------------------------------------- the lateness interaction (the real trap)


def test_a_deferral_past_the_h4_lateness_window_is_refused_at_launch():
    """3 h on an H4 sleeve is inside every other check and would be SHADOWED at placement.

    `book_owner._entry_too_late` shadows an entry more than `frac * bar_period` past the close
    — 0.5 x 240 min = 2 h on H4. A 3 h deferral is generated, deferred, emitted, and then
    dropped as `stale_late_entry_after_restart`: the sleeve stops trading and every log reads
    healthy. That must be a LAUNCH refusal.
    """
    with pytest.raises(EntryHourSelectionError, match="entry-lateness window"):
        parse_entry_hour("h4_sleeve:3", known_sleeves=KNOWN, timeframe_of=TF_OF)


def test_the_ratified_hour_is_legal_on_both_h4_and_d1():
    got = parse_entry_hour("h4_sleeve,d1_sleeve", known_sleeves=KNOWN, timeframe_of=TF_OF)
    assert got == {"h4_sleeve": 1, "d1_sleeve": 1}


def test_the_ratified_hour_is_refused_on_m15_because_its_window_is_seven_minutes():
    # 0.5 x 15 min = 7.5 min. Deferring an M15 entry by an hour is nonsense and is refused
    # rather than silently shadowed.
    with pytest.raises(EntryHourSelectionError, match="entry-lateness window"):
        parse_entry_hour("m15_sleeve", known_sleeves=KNOWN, timeframe_of=TF_OF)


def test_a_tighter_lateness_frac_tightens_the_refusal():
    # frac 0.2 x 1440 = 288 min = 4.8 h, so 5 on D1 is refused where 4 is not.
    assert parse_entry_hour("d1_sleeve:4", known_sleeves=KNOWN, timeframe_of=TF_OF,
                            lateness_frac=0.2) == {"d1_sleeve": 4}
    with pytest.raises(EntryHourSelectionError, match="entry-lateness window"):
        parse_entry_hour("d1_sleeve:5", known_sleeves=KNOWN, timeframe_of=TF_OF,
                         lateness_frac=0.2)


# --------------------------------------------------------------------------- the rule


def _b(h, day=31):
    return dt.datetime(2026, 7, day, h, 0)


def test_a_bar_closing_at_the_rollover_defers_until_the_target():
    sel = {"s": 1}
    assert deferral_reason("s", _b(0), _b(0), sel) is not None
    assert deferral_reason("s", _b(0), _b(1), sel) is None


def test_a_bar_closing_after_the_target_is_never_deferred():
    """An H4 bar closing at 04:00 must not be held toward "hour 01" — that would mean 21 hours,
    or yesterday. Only bars that close BEFORE the target on the same broker day are deferred."""
    for close_h in (4, 8, 12, 16, 20):
        assert deferral_reason("s", _b(close_h), _b(close_h), {"s": 1}) is None


def test_the_deferral_never_crosses_a_broker_day():
    # `now` a day later than the bar's close: emit, never hold.
    assert deferral_reason("s", _b(0, day=30), _b(0, day=31), {"s": 1}) is None


def test_an_unselected_sleeve_is_never_deferred():
    assert deferral_reason("other", _b(0), _b(0), {"s": 1}) is None
    assert deferral_reason("s", _b(0), _b(0), {}) is None
    assert deferral_reason("s", _b(0), _b(0), None) is None


def test_the_reason_names_the_bar_hour_the_clock_hour_and_the_target():
    r = deferral_reason("s", _b(0), _b(0), {"s": 2})
    assert "bar_closed_00" in r and "now_00" in r and "target_02" in r


# --------------------------------------------------------- engine wiring and inertness


def test_the_default_engine_has_no_entry_hour_selection(tmp_path):
    eng = _engine(tmp_path)
    assert eng._entry_hour == {}


def test_the_default_path_never_evaluates_and_writes_no_telemetry(tmp_path):
    """OFF must be byte-identical: no clock read, no broker call, no telemetry key. A flag that
    leaves a footprint when it is off is a flag that changed the book by existing."""
    eng = _engine(tmp_path)
    gen: dict = {}
    assert eng._entry_hour_deferral(_Intent(), _Spec("h4_sleeve"), "XAUUSD",
                                    dt.datetime(2026, 7, 31, 20, 0, tzinfo=UTC),
                                    dt.datetime(2026, 7, 31, 20, 1, tzinfo=UTC), gen) is None
    assert gen == {}


def test_an_unselected_sleeve_is_not_even_counted(tmp_path):
    eng = _engine(tmp_path, entry_hour={"other": 1}, broker_server="FTMO-Server3")
    gen: dict = {}
    assert eng._entry_hour_deferral(_Intent(), _Spec("h4_sleeve"), "XAUUSD",
                                    dt.datetime(2026, 7, 31, 20, 0, tzinfo=UTC),
                                    dt.datetime(2026, 7, 31, 20, 1, tzinfo=UTC), gen) is None
    assert gen == {}


def test_a_selected_sleeve_at_the_rollover_is_deferred_and_counted(tmp_path):
    """FTMO-Server3 is America/New_York + 7 h. On 2026-07-31 (EDT, UTC-4) that is UTC+3, so a
    bar CLOSING at 21:00 UTC closes at broker 00:00 — the rollover. The H4 bar that closes then
    OPENS at 17:00 UTC."""
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server="FTMO-Server3")
    gen: dict = {}
    row = eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve"), "GBPJPY",
        dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),     # opens 17:00 UTC -> closes 21:00 UTC
        dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC),     # broker 00:01 — before the target
        gen)
    assert row is not None
    assert row["reason"].startswith("entry_hour_deferred:h4_sleeve:bar_closed_00")
    assert gen["entry_hour"] == {"evaluated": 1, "deferred": 1, "fail_open": 0,
                                 "sleeves": ["h4_sleeve"]}


def test_the_same_intent_is_emitted_once_the_broker_clock_reaches_the_target(tmp_path):
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server="FTMO-Server3")
    gen: dict = {}
    assert eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve"), "GBPJPY",
        dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
        dt.datetime(2026, 7, 31, 22, 5, tzinfo=UTC),     # broker 01:05 — at the target
        gen) is None
    assert gen["entry_hour"]["evaluated"] == 1
    assert gen["entry_hour"]["deferred"] == 0


def test_a_bar_that_does_not_close_at_the_rollover_is_untouched(tmp_path):
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server="FTMO-Server3")
    gen: dict = {}
    # opens 05:00 UTC -> closes 09:00 UTC -> broker 12:00, well past the target
    assert eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve"), "XAUUSD",
        dt.datetime(2026, 7, 31, 5, 0, tzinfo=UTC),
        dt.datetime(2026, 7, 31, 9, 1, tzinfo=UTC), gen) is None
    assert gen["entry_hour"]["deferred"] == 0


# --------------------------------------------------------------------- fail-OPEN


def test_an_unresolvable_server_emits_the_intent_and_counts_the_fail_open(tmp_path):
    """The opposite of the spread floor, and stated so nobody 'fixes' it: deferring forever on
    a dark clock is a silent disarm of an armed sleeve, while emitting is exactly what the book
    does today."""
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server=None)
    gen: dict = {}
    assert eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve"), "GBPJPY",
        dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
        dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC), gen) is None
    assert gen["entry_hour"]["fail_open"] == 1
    assert gen["entry_hour"]["deferred"] == 0


def test_an_unregistered_server_fails_open_and_names_the_exception(tmp_path):
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server="Nobody-Server9")
    gen: dict = {}
    assert eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve"), "GBPJPY",
        dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
        dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC), gen) is None
    assert gen["entry_hour"]["fail_open"] == 1
    assert any("UnknownBrokerClockError" in e for e in gen["entry_hour"]["errors"])


def test_the_server_resolver_may_be_a_callable(tmp_path):
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1},
                  broker_server=lambda: "FTMO-Server3")
    gen: dict = {}
    assert eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve"), "GBPJPY",
        dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
        dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC), gen) is not None


def test_the_error_list_is_capped_so_a_per_tick_fault_cannot_grow_without_bound(tmp_path):
    eng = _engine(tmp_path, entry_hour={f"s{i}": 1 for i in range(20)},
                  broker_server="Nobody-Server9")
    gen: dict = {}
    for i in range(20):
        eng._entry_hour_deferral(_Intent(), _Spec(f"s{i}"), "GBPJPY",
                                 dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
                                 dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC), gen)
    assert gen["entry_hour"]["fail_open"] == 20
    assert len(gen["entry_hour"]["errors"]) <= 8


def test_an_unknown_timeframe_fails_open_rather_than_guessing_a_bar_period(tmp_path):
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server="FTMO-Server3")
    gen: dict = {}
    assert eng._entry_hour_deferral(
        _Intent(), _Spec("h4_sleeve", timeframe=99999), "GBPJPY",
        dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
        dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC), gen) is None
    assert gen["entry_hour"]["fail_open"] == 1


# ------------------------------------------------------- composition and no-config-key


def test_the_owner_threads_all_four_selections_without_overwriting_any(tmp_path):
    """The wave-13 train hand-merged these signatures and left a duplicate assignment pair
    behind (B2315). This asserts the whole set survives one constructor."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    from src.components.ultimate_book.weekend_policy import policy_from_args
    owner = UltimateBookOwner(
        {"gtos_vnext_runtime": {}}, _MT5(), str(tmp_path), namespace="ce_test",
        frontier_exits=("mx_btcusd_d1_donchian_20_breakout",),
        spread_geometry_floor={"sub_mid_dn_revert": None},
        weekend_policy=policy_from_args("sub_xvol_pullback"),
        entry_hour={"sub_mid_dn_revert": 1},
    )
    assert tuple(owner._frontier_exits) == ("mx_btcusd_d1_donchian_20_breakout",)
    assert owner._spread_geometry_floor == {"sub_mid_dn_revert": None}
    assert owner._entry_hour == {"sub_mid_dn_revert": 1}
    assert owner._weekend_policy.enabled
    # and each reached the layer that consumes it
    assert owner.engine._spread_geometry_floor == {"sub_mid_dn_revert": None}
    assert owner.engine._entry_hour == {"sub_mid_dn_revert": 1}
    assert callable(owner.engine._broker_server)


def test_the_lever_adds_no_runtime_config_key(tmp_path):
    """AR's hardening (`test_runtime_flag_defaults_complete.py`) exists because a runtime key
    read without a `DEFAULT_CONFIG` entry is an armed book standing down with a healthy
    heartbeat. This lever is a launcher argument and reads no config key of its own, so it is
    compliant by construction — asserted rather than assumed."""
    import inspect

    from src.components.ultimate_book import entry_hour as mod
    src = inspect.getsource(mod)
    assert "DEFAULT_CONFIG" not in src
    assert "agent_config" not in src
    # and it imports nothing from the config layer
    assert "import yaml" not in src


def test_the_lever_never_touches_the_broker(tmp_path):
    """`_MT5.get_tick` raises. The spread floor fetches a tick by design; this must not."""
    eng = _engine(tmp_path, entry_hour={"h4_sleeve": 1}, broker_server="FTMO-Server3")
    gen: dict = {}
    eng._entry_hour_deferral(_Intent(), _Spec("h4_sleeve"), "GBPJPY",
                             dt.datetime(2026, 7, 31, 17, 0, tzinfo=UTC),
                             dt.datetime(2026, 7, 31, 21, 1, tzinfo=UTC), gen)
    assert gen["entry_hour"]["deferred"] == 1

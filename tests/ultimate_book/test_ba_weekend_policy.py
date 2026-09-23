"""Session BA (B1900) — the redacted_account weekend-holding policy: OFF by default, and correct when armed.

WHAT IS BEING PINNED, AND WHY BEHAVIOURALLY

The policy closes live positions on a schedule and refuses live entries. Two opposite properties
therefore matter, and both are asserted through the code paths the live book actually runs
(`UltimateBookOwner._weekend_flat_close`, `._weekend_entry_block`, `.weekend_policy_preflight`)
rather than on the source text:

  1. with no selection, NOTHING changes -- no sleeve is governed, no close is attempted, no entry
     is refused, and every decision function is False for every declared sleeve at every instant;
  2. with a selection, the close fires at the measured instant and ONLY for the named sleeve.

THE INSTANT IS THE POINT. `flatten_before_hours=4.0` must put the flatten at broker-local Friday
20:00 -- the close of the last H4 bar of the week, which is the instant Session BA's headline
research cell `m0` exits at. If that mapping breaks, the published cost (-0.0180 to -0.5139 R/day
per armed sleeve, `BA_WEEKEND_V1.json` -> `flat`) stops being the cost of this switch. It is
asserted against `broker_clock` in both US DST seasons, on both live servers.

THE ARGUMENT-ORDER TEST. `_weekend_flat_close(ee, sym, sleeve)` takes two strings a type checker
cannot tell apart, and a swap is silent: the policy would govern the SYMBOL name, which is in no
selection, so the guard would never fire and every log would read healthy. `test_the_guard_is_keyed_on_the_sleeve_not_the_symbol` passes a symbol that IS a valid sleeve name
and asserts nothing closes.
"""
import datetime as dt
import pathlib
from types import SimpleNamespace

import pytest
import yaml

from src.components.ultimate_book import weekend_policy as WP
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive
from src.utils.config import apply_instrument_overrides, apply_profile_overrides

REPO = pathlib.Path(__file__).resolve().parents[2]

FTMO = "FTMO-Server3"
FN = "redacted_account-Server 2"
#: The armed four as of 2026-07-30 ~14:57Z on both accounts.
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")

#: A Friday in US EDT (broker == UTC+3) and a Friday in EST (broker == UTC+2). Both seasons are
#: exercised because a fixed +3 assumption is the defect `broker_clock` exists to prevent, and it
#: would show up here as a one-hour error in the flatten instant.
FRI_EDT = dt.datetime(2026, 7, 31, 12, 0, tzinfo=dt.timezone.utc)
FRI_EST = dt.datetime(2026, 1, 30, 12, 0, tzinfo=dt.timezone.utc)


# =====================================================================================
# the deadline is a measured calendar fact
# =====================================================================================

@pytest.mark.parametrize("server", [FTMO, FN])
@pytest.mark.parametrize("now", [FRI_EDT, FRI_EST])
def test_the_boundary_is_broker_local_saturday_midnight(server, now):
    b = WP.next_weekend_boundary_utc(now, server)
    local = utc_to_broker_naive(b, resolve_rule(server))
    assert (local.weekday(), local.hour, local.minute) == (5, 0, 0), local


@pytest.mark.parametrize("server", [FTMO, FN])
@pytest.mark.parametrize("now", [FRI_EDT, FRI_EST])
def test_the_default_flatten_lands_on_the_last_h4_bar_close_of_the_week(server, now):
    """broker Friday 20:00 -- the close of the H4 bar that OPENS at 20:00, i.e. research `m0`."""
    pol = WP.WeekendPolicy(sleeves=("crypto",))
    assert pol.flatten_before_hours == 4.0
    local = utc_to_broker_naive(pol.flatten_deadline_utc(now, server), resolve_rule(server))
    assert (local.weekday(), local.hour, local.minute) == (4, 20, 0), local


def test_both_live_servers_agree_on_the_boundary_every_day_of_2026():
    """The R measurement is on the FTMO archive; the policy runs on redacted_account."""
    d = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)
    for _ in range(365):
        assert (WP.next_weekend_boundary_utc(d, FTMO)
                == WP.next_weekend_boundary_utc(d, FN)), d
        d += dt.timedelta(days=1)


def test_the_boundary_is_strictly_after_now_even_when_now_is_the_boundary():
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    assert WP.next_weekend_boundary_utc(b, FTMO) == b + dt.timedelta(days=7)


def test_an_unregistered_server_fails_closed_rather_than_returning_no_weekend():
    with pytest.raises(Exception):
        WP.next_weekend_boundary_utc(FRI_EDT, "Some-Other-Server7")


# =====================================================================================
# OFF by default
# =====================================================================================

def test_off_governs_nothing():
    assert WP.OFF.enabled is False
    assert WP.OFF.sleeves == ()
    for s in sorted(SLEEVE_EXIT_PROFILES):
        assert WP.OFF.governs(s) is False


@pytest.mark.parametrize("hours_before_boundary", [0.0, 0.5, 1.0, 4.0, 8.0, 24.0, 72.0])
def test_off_never_flattens_and_never_blocks_at_any_instant(hours_before_boundary):
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    now = b - dt.timedelta(hours=hours_before_boundary)
    for s in ARMED:
        assert WP.OFF.flatten_due(s, now, FTMO) is False
        assert WP.OFF.entry_blocked(s, now, FTMO) is False


def test_policy_from_args_with_no_selection_is_off():
    assert WP.policy_from_args(None) is WP.OFF
    # ...and the numeric knobs cannot arm it on their own.
    assert WP.policy_from_args(None, flatten_before_hours=12.0,
                              entry_embargo_hours=48.0) is WP.OFF


# =====================================================================================
# the selection parser — the three fail-open shapes
# =====================================================================================

def test_no_selection_is_the_empty_selection():
    assert WP.parse_weekend_flat(None) == ()


def test_an_empty_string_is_refused_rather_than_read_as_all():
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.parse_weekend_flat("")
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.parse_weekend_flat(" , ")


def test_an_unknown_sleeve_is_refused_rather_than_dropped():
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.parse_weekend_flat("crypto,cryptoo")


def test_the_selection_dedupes_and_keeps_order():
    assert WP.parse_weekend_flat("crypto,energy_agri,crypto") == ("crypto", "energy_agri")


def test_a_known_sleeve_outside_this_workers_tags_is_ALLOWED():
    """Arming the guard before arming the sleeve is the safe order and must not be refused."""
    assert WP.parse_weekend_flat("mx_btcusd_d1_donchian_20_breakout") == (
        "mx_btcusd_d1_donchian_20_breakout",)


@pytest.mark.parametrize("bad", [0.0, -1.0, -0.001, 121.0, 10_000.0])
def test_a_nonsense_flatten_margin_is_refused(bad):
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.WeekendPolicy(sleeves=("crypto",), flatten_before_hours=bad)


def test_a_negative_embargo_is_refused():
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.WeekendPolicy(sleeves=("crypto",), entry_embargo_hours=-1.0)


def test_an_exemption_for_a_sleeve_the_policy_does_not_govern_is_refused():
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.WeekendPolicy(sleeves=("crypto",), exempt_sleeves=("energy_agri",))


# =====================================================================================
# the early-close list — the one shape where a fixed Saturday anchor is a BREACH
# =====================================================================================

#: The archive's own worst case: Christmas Day 2020 was a Friday, the market's last H4 bar of
#: that week closed at broker Friday 00:00, and a Saturday-anchored deadline aims 20 h into a
#: shut market. Session BA measured 7 such exits out of 271 (2.6 %).
XMAS20 = dt.datetime(2020, 12, 23, 10, 0, tzinfo=dt.timezone.utc)
DERIVED_LIST = (REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts/"
                       "BA_EARLY_CLOSE_DATES_V1.txt")


def test_a_holiday_friday_pulls_the_boundary_back_a_day():
    plain = WP.next_weekend_boundary_utc(XMAS20, FTMO)
    withl = WP.next_weekend_boundary_utc(XMAS20, FTMO, ("2020-12-25",))
    assert (plain - withl) == dt.timedelta(days=1)
    local = utc_to_broker_naive(withl, resolve_rule(FTMO))
    assert (local.weekday(), local.hour) == (4, 0), local     # Friday 00:00 broker


def test_two_consecutive_holidays_pull_it_back_two_days():
    b = WP.next_weekend_boundary_utc(XMAS20, FTMO, ("2020-12-25", "2020-12-24"))
    assert (WP.next_weekend_boundary_utc(XMAS20, FTMO) - b) == dt.timedelta(days=2)


def test_a_holiday_in_the_MIDDLE_of_the_week_moves_nothing():
    """Only a non-trading day at the END of the week changes the weekly close."""
    assert (WP.next_weekend_boundary_utc(XMAS20, FTMO, ("2020-12-23",))
            == WP.next_weekend_boundary_utc(XMAS20, FTMO))


@pytest.mark.parametrize("hours", [0, 6, 25, 49, 73, 121, 145])
def test_the_boundary_is_always_strictly_in_the_future_whatever_the_list(hours):
    """The one invariant. A list that walked it into the past would make `flatten_due` compare
    against a window that had already closed, so the guard would never fire."""
    every = tuple((dt.date(2020, 12, 14) + dt.timedelta(days=k)).isoformat() for k in range(21))
    now = XMAS20 - dt.timedelta(hours=hours)
    for lst in ((), ("2020-12-25",), ("2020-12-25", "2020-12-24"), every):
        assert WP.next_weekend_boundary_utc(now, FTMO, lst) > now, (hours, lst)


def test_the_flatten_deadline_moves_with_the_list():
    pol = WP.WeekendPolicy(sleeves=("sub_xvol_pullback",), early_close_dates=("2020-12-25",))
    d = pol.flatten_deadline_utc(XMAS20, FTMO)
    assert d == dt.datetime(2020, 12, 24, 18, 0, tzinfo=dt.timezone.utc)
    # ...and the replay's own exit for those trades was 2020-12-24T22:00Z, so the live rule is
    # EARLIER: the safe direction, and the reason the published cost is a lower bound.
    assert d < dt.datetime(2020, 12, 24, 22, 0, tzinfo=dt.timezone.utc)


def test_the_committed_derived_list_parses_and_is_all_recognisable_holidays():
    dates = WP.parse_early_close_dates(str(DERIVED_LIST))
    assert len(dates) == 13, dates
    for s in dates:
        d = dt.date.fromisoformat(s)
        # Christmas / New Year window, or a Friday (every Good Friday in the list).
        assert (d.month, d.day) in {(12, 24), (12, 25), (12, 31), (1, 1)} or d.weekday() == 4, s
    assert "2020-12-25" in dates and "2021-01-01" in dates


def test_the_early_close_list_refuses_the_two_bad_shapes():
    assert WP.parse_early_close_dates(None) == ()
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.parse_early_close_dates("")
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.parse_early_close_dates("2026-12-25,not-a-date")
    with pytest.raises(WP.WeekendPolicySelectionError):
        WP.WeekendPolicy(sleeves=("crypto",), early_close_dates=("2026-13-45",))


def test_the_list_is_historical_and_says_so():
    """A list with no future date cannot protect a live account, and the file must warn."""
    text = DERIVED_LIST.read_text(encoding="utf-8")
    assert "HISTORICAL" in text
    dates = WP.parse_early_close_dates(str(DERIVED_LIST))
    assert max(dates) < "2026-07-31"


# =====================================================================================
# armed: the window, the scoping, the exemption
# =====================================================================================

def _armed(**kw):
    return WP.WeekendPolicy(sleeves=("crypto", "energy_agri"), **kw)


def test_the_flatten_window_opens_at_the_deadline_and_closes_at_the_boundary():
    pol = _armed()
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    assert pol.flatten_due("crypto", b - dt.timedelta(hours=4, minutes=1), FTMO) is False
    assert pol.flatten_due("crypto", b - dt.timedelta(hours=4), FTMO) is True
    assert pol.flatten_due("crypto", b - dt.timedelta(minutes=1), FTMO) is True
    # At and after the boundary the market is shut: a True here would spin a close attempt every
    # tick for 48 h against a closed market.
    assert pol.flatten_due("crypto", b, FTMO) is False
    assert pol.flatten_due("crypto", b + dt.timedelta(hours=24), FTMO) is False


def test_the_policy_is_scoped_to_the_named_sleeves_only():
    pol = _armed()
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    inside = b - dt.timedelta(hours=1)
    assert pol.flatten_due("crypto", inside, FTMO) is True
    for other in ("sub_xvol_pullback", "sub_mid_dn_revert", "metals_core", "fx_jpy"):
        assert pol.flatten_due(other, inside, FTMO) is False
        assert pol.entry_blocked(other, inside, FTMO) is False


def test_an_exempt_sleeve_is_not_governed_even_though_it_is_named():
    pol = WP.WeekendPolicy(sleeves=("crypto", "energy_agri"), exempt_sleeves=("crypto",))
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    inside = b - dt.timedelta(hours=1)
    assert pol.governs("crypto") is False
    assert pol.flatten_due("crypto", inside, FTMO) is False
    assert pol.flatten_due("energy_agri", inside, FTMO) is True


def test_an_entry_inside_the_flatten_window_is_always_refused_even_with_no_embargo():
    """It would be closed on the tick that opened it."""
    pol = _armed(entry_embargo_hours=0.0)
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    assert pol.entry_blocked("crypto", b - dt.timedelta(hours=3), FTMO) is True
    assert pol.entry_blocked("crypto", b - dt.timedelta(hours=5), FTMO) is False


def test_the_embargo_widens_the_entry_refusal_and_nothing_else():
    pol = _armed(entry_embargo_hours=24.0)
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    at20 = b - dt.timedelta(hours=20)
    assert pol.entry_blocked("crypto", at20, FTMO) is True
    # ...and it does NOT bring the close forward: the flatten margin is the only exit dial.
    assert pol.flatten_due("crypto", at20, FTMO) is False


def test_a_naive_datetime_is_read_as_utc_rather_than_crashing():
    pol = _armed()
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    naive = (b - dt.timedelta(hours=1)).replace(tzinfo=None)
    assert pol.flatten_due("crypto", naive, FTMO) is True


# =====================================================================================
# the owner wiring
# =====================================================================================

class _Tick:
    def __init__(self, bid, ask):
        self.bid, self.ask = bid, ask


class _StubMT5:
    _INFO = SimpleNamespace(trade_tick_size=0.01, trade_tick_value=1.0, volume_min=0.01,
                            volume_step=0.01, volume_max=100.0, filling_mode=3, spread=12)

    def __init__(self):
        self._mt5 = SimpleNamespace(symbol_info=lambda _s: self._INFO)

    def get_tick(self, symbol): return _Tick(2999.7, 3000.0)
    def get_account_balance(self): return 100000.0
    def get_account_equity(self): return 100000.0
    def get_positions(self, symbol=None): return []
    def get_open_positions(self): return []
    def is_connected(self): return True
    def get_margin_mode(self): return "hedging"


class _FakeEngine:
    """The narrowest thing `_weekend_flat_close` touches: an engine with a position."""

    def __init__(self, *, closes_ok=True, open_position=True):
        self.active_trade = SimpleNamespace(ticket=123) if open_position else None
        self.closes_ok = closes_ok
        self.close_calls: list[str] = []

    def close_position(self, reason="manual"):
        self.close_calls.append(reason)
        if self.closes_ok:
            self.active_trade = None
            return True
        return False


@pytest.fixture(scope="module")
def merged_cfg():
    cfg = yaml.safe_load(open(REPO / "config/agent_config.yaml", encoding="utf-8"))
    cfg = apply_profile_overrides(cfg, "operator_profile")
    return apply_instrument_overrides(cfg, "XAUUSD")


def _owner(merged_cfg, policy=None, *, server=FTMO):
    o = UltimateBookOwner(merged_cfg, _StubMT5(), ".", namespace="operator_profile",
                          weekend_policy=policy)
    o._broker_server_name = lambda: server           # test-only: pin the clock rule
    return o


@pytest.fixture(autouse=True)
def _restore_book_owner_clock():
    """Session BA's `_freeze_module_clock` assigns `BO.datetime` RAW (no monkeypatch), which
    leaked a weekend-frozen clock into every later `book_owner` test in the same process --
    twelve order-dependent failures at the wave-13 train, invisible when this file ran alone.
    Restore unconditionally around every test in this module so no helper here can leak."""
    import src.components.ultimate_book.book_owner as BO
    orig = BO.datetime
    yield
    BO.datetime = orig


def _inside(server=FTMO):
    return WP.next_weekend_boundary_utc(FRI_EDT, server) - dt.timedelta(hours=1)


def _freeze(monkeypatch, when):
    """Freeze the clock `book_owner` reads. It imports `datetime` from the stdlib module, so the
    patch has to land on the class the module holds -- patching `datetime.datetime` globally would
    also move every other consumer in the process."""
    import src.components.ultimate_book.book_owner as BO

    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return when if tz is not None else when.replace(tzinfo=None)

    monkeypatch.setattr(BO, "datetime", _Frozen)


def test_the_owner_defaults_to_off(merged_cfg):
    o = _owner(merged_cfg)
    assert o._weekend_policy is WP.OFF
    assert o.weekend_policy_preflight() == {"ok": True, "status": "off"}


def test_off_attempts_no_close_inside_the_window(merged_cfg, monkeypatch):
    o = _owner(merged_cfg)
    _freeze(monkeypatch, _inside())
    ee = _FakeEngine()
    assert o._weekend_flat_close(ee, "BTCUSD", "crypto") is None
    assert ee.close_calls == []
    assert ee.active_trade is not None


def test_armed_closes_the_governed_position_inside_the_window(merged_cfg, monkeypatch):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, _inside())
    ee = _FakeEngine()
    assert o._weekend_flat_close(ee, "BTCUSD", "crypto") == "weekend_flat"
    assert ee.close_calls == ["weekend_flat"]
    assert ee.active_trade is None


def test_armed_leaves_an_ungoverned_sleeve_alone(merged_cfg, monkeypatch):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, _inside())
    ee = _FakeEngine()
    assert o._weekend_flat_close(ee, "XAUUSD", "sub_xvol_pullback") is None
    assert ee.close_calls == []


def test_the_guard_is_keyed_on_the_sleeve_not_the_symbol(merged_cfg, monkeypatch):
    """`crypto` passed as the SYMBOL must not fire a policy armed on the sleeve `crypto`."""
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, _inside())
    ee = _FakeEngine()
    assert o._weekend_flat_close(ee, "crypto", "BTCUSD") is None
    assert ee.close_calls == []


def test_armed_attempts_nothing_outside_the_window(merged_cfg, monkeypatch):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, WP.next_weekend_boundary_utc(FRI_EDT, FTMO) - dt.timedelta(hours=30))
    ee = _FakeEngine()
    assert o._weekend_flat_close(ee, "BTCUSD", "crypto") is None
    assert ee.close_calls == []


def test_armed_with_no_open_position_does_nothing(merged_cfg, monkeypatch):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, _inside())
    ee = _FakeEngine(open_position=False)
    assert o._weekend_flat_close(ee, "BTCUSD", "crypto") is None
    assert ee.close_calls == []


def test_a_failed_close_is_reported_as_not_closed_rather_than_as_closed(merged_cfg, monkeypatch):
    """A False from the broker path must not be recorded as a weekend close -- the position is
    still open and the account is still out of compliance."""
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, _inside())
    ee = _FakeEngine(closes_ok=False)
    assert o._weekend_flat_close(ee, "BTCUSD", "crypto") is None
    assert ee.close_calls == ["weekend_flat"]
    assert ee.active_trade is not None


def test_a_raising_close_does_not_propagate(merged_cfg, monkeypatch):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    _freeze(monkeypatch, _inside())

    class _Boom(_FakeEngine):
        def close_position(self, reason="manual"):
            raise RuntimeError("broker down")

    assert o._weekend_flat_close(_Boom(), "BTCUSD", "crypto") is None


# ---- the entry side, and its OPPOSITE degradation ------------------------------------

def test_the_entry_block_reasons(merged_cfg, monkeypatch):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",), entry_embargo_hours=24.0))
    b = WP.next_weekend_boundary_utc(FRI_EDT, FTMO)
    _freeze(monkeypatch, b - dt.timedelta(hours=20))
    assert o._weekend_entry_block("crypto") == "weekend_entry_embargo"
    assert o._weekend_entry_block("sub_xvol_pullback") is None
    _freeze(monkeypatch, b - dt.timedelta(hours=30))
    assert o._weekend_entry_block("crypto") is None


def test_a_dark_clock_refuses_entries_but_does_not_invent_a_close(merged_cfg, monkeypatch):
    """The two decisions degrade in OPPOSITE directions on purpose."""
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)), server=None)
    _freeze(monkeypatch, _inside())
    assert o._weekend_entry_block("crypto") == "weekend_policy_clock_unavailable"
    ee = _FakeEngine()
    assert o._weekend_flat_close(ee, "BTCUSD", "crypto") is None
    assert ee.close_calls == []


def test_off_never_blocks_an_entry(merged_cfg, monkeypatch):
    o = _owner(merged_cfg)
    _freeze(monkeypatch, _inside())
    for s in ARMED:
        assert o._weekend_entry_block(s) is None


# ---- preflight -----------------------------------------------------------------------

def test_preflight_refuses_an_armed_policy_with_no_server(merged_cfg):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)), server=None)
    r = o.weekend_policy_preflight()
    assert r["ok"] is False and r["status"] == "unresolved_server"


def test_preflight_refuses_an_armed_policy_on_an_unregistered_server(merged_cfg):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)), server="Some-Other-Server7")
    r = o.weekend_policy_preflight()
    assert r["ok"] is False and r["status"] == "clock_unavailable"


def test_preflight_publishes_the_two_instants_and_the_policy(merged_cfg):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    r = o.weekend_policy_preflight()
    assert r["ok"] is True and r["status"] == "armed"
    b = dt.datetime.fromisoformat(r["next_weekend_boundary_utc"])
    d = dt.datetime.fromisoformat(r["next_flatten_deadline_utc"])
    assert (b - d) == dt.timedelta(hours=4.0)
    assert r["policy"]["sleeves"] == ["crypto"]


def test_preflight_names_a_governed_sleeve_this_worker_cannot_trade(merged_cfg):
    """A guard armed on a sleeve the registry does not generate is legal, safe, and inert -- and
    reads exactly like one that works, so it has to be published."""
    o = _owner(merged_cfg, WP.WeekendPolicy(
        sleeves=("mx_spn35_cash_d1_volume_surge_reversal",)))
    r = o.weekend_policy_preflight()
    assert r["ok"] is True
    assert r["governs_sleeves_this_worker_does_not_trade"] == [
        "mx_spn35_cash_d1_volume_surge_reversal"]


def test_preflight_reports_nothing_ungoverned_for_a_generated_sleeve(merged_cfg):
    o = _owner(merged_cfg, WP.WeekendPolicy(sleeves=("crypto",)))
    assert o.weekend_policy_preflight()["governs_sleeves_this_worker_does_not_trade"] == []


def test_preflight_surfaces_the_include_clean3_dependence_of_two_armed_sleeves(merged_cfg):
    """MEASURED, and it is the reason this field exists rather than a nicety.

    `sub_xvol_pullback` and `sub_mid_dn_revert` are two of the FOUR armed sleeves and both are
    clean_3, so `book_engine._active_sleeve_names()` drops them whenever
    `ultimate_book_include_clean3` is false -- which is what this repository's mainline config
    carries and what the live host does NOT (verified true on the host, `phase8/receipts/
    VPS_STEP_ZERO_VERIFIED.md`). A weekend guard armed on them against a `false` config governs
    nothing at all, and the preflight is what says so out loud.
    """
    o = _owner(merged_cfg, WP.WeekendPolicy(
        sleeves=("sub_xvol_pullback", "sub_mid_dn_revert")))
    r = o.weekend_policy_preflight()
    from src.components.ultimate_book.bridge import config_bool_value
    rt = merged_cfg.get("gtos_vnext_runtime", merged_cfg)
    inc3 = config_bool_value(rt.get("ultimate_book_include_clean3", False), False)
    if inc3:
        assert r["governs_sleeves_this_worker_does_not_trade"] == []
    else:
        assert set(r["governs_sleeves_this_worker_does_not_trade"]) == {
            "sub_xvol_pullback", "sub_mid_dn_revert"}


# =====================================================================================
# the entry side, end to end through the real run_cycle
# =====================================================================================
# `test_book_owner.py` already has the only working `run_cycle` harness in the suite (a fake
# broker, a fake bar feed and a recording engine that never sends). Reusing it is what makes
# this an END-TO-END pin rather than one more unit test of the same predicate: the guard sits
# in the intent loop, and a guard that is unit-correct and mis-wired reads exactly like a guard
# that works.

def _cycle_owner(policy, when):
    """An owner whose fake feed is anchored on `when`, so `run_cycle(now_utc=when)` is in date.

    `_FakeMT5` anchors its forming bar on the real `now`, so passing an arbitrary `now_utc` to
    `run_cycle` puts the decision bar weeks in the past and the entry-lateness guard drops it —
    which looked exactly like the weekend guard working and is why the control below exists.
    Moving the feed's anchor with the clock is what makes the two comparable.
    """
    import tempfile

    from tests.ultimate_book import test_book_owner as TBO

    engines: dict = {}

    def factory(symbol):
        engines.setdefault(symbol, TBO._RecordingEngine())
        return engines[symbol]

    mt5 = TBO._FakeMT5()
    mt5._anchor_forming = when - dt.timedelta(seconds=1)
    owner = UltimateBookOwner(TBO._cfg(True), mt5, tempfile.mkdtemp(),
                              engine_factory=factory, weekend_policy=policy)
    owner._broker_server_name = lambda: FTMO
    return owner, engines


def _placed_and_skipped(summary):
    return ([p["sleeve"] for p in summary["placed"]],
            [s.get("reason") for s in summary["skipped"] if isinstance(s, dict)])


@pytest.mark.parametrize("hours_before_boundary", [1, 30])
def test_the_cycle_places_crypto_when_the_policy_is_off(hours_before_boundary):
    """The control, at BOTH instants the tests below use. If this stops placing, they prove
    nothing — and the first version of it did stop placing, for a reason that had nothing to do
    with weekends (see `_cycle_owner`)."""
    when = WP.next_weekend_boundary_utc(FRI_EDT, FTMO) - dt.timedelta(hours=hours_before_boundary)
    owner, _ = _cycle_owner(None, when)
    placed, _sk = _placed_and_skipped(owner.run_cycle(tags=("crypto",), now_utc=when))
    assert "crypto" in placed


def test_the_cycle_refuses_the_governed_entry_inside_the_window():
    when = _inside()
    owner, engines = _cycle_owner(WP.WeekendPolicy(sleeves=("crypto",)), when)
    placed, skipped = _placed_and_skipped(
        owner.run_cycle(tags=("crypto",), now_utc=when))
    assert placed == []
    assert "weekend_entry_embargo" in skipped
    assert all(len(e.calls) == 0 for e in engines.values())     # nothing reached open_trade


def test_the_cycle_places_the_same_entry_outside_the_window():
    mid_week = WP.next_weekend_boundary_utc(FRI_EDT, FTMO) - dt.timedelta(hours=30)
    owner, _ = _cycle_owner(WP.WeekendPolicy(sleeves=("crypto",)), mid_week)
    placed, skipped = _placed_and_skipped(owner.run_cycle(tags=("crypto",), now_utc=mid_week))
    assert "crypto" in placed
    assert "weekend_entry_embargo" not in skipped


def test_the_cycle_leaves_an_ungoverned_sleeve_placing_inside_the_window():
    when = _inside()
    owner, _ = _cycle_owner(WP.WeekendPolicy(sleeves=("energy_agri",)), when)
    placed, skipped = _placed_and_skipped(
        owner.run_cycle(tags=("crypto",), now_utc=when))
    assert "crypto" in placed
    assert "weekend_entry_embargo" not in skipped


def test_the_entry_decision_uses_the_CYCLE_clock_not_a_fresh_read():
    """Both directions on ONE owner, which is what the `now` parameter buys.

    A guard reading `datetime.now()` inside the loop would answer about the wall clock rather
    than about the decision bar, and the second assertion could not be written at all — the same
    owner would have to give two answers at two simulated instants.
    """
    pol = WP.WeekendPolicy(sleeves=("crypto",))
    inside = _inside()
    outside = WP.next_weekend_boundary_utc(FRI_EDT, FTMO) - dt.timedelta(hours=30)
    owner, _ = _cycle_owner(pol, inside)
    assert _placed_and_skipped(owner.run_cycle(tags=("crypto",), now_utc=inside))[0] == []
    owner._mt5._anchor_forming = outside - dt.timedelta(seconds=1)
    assert "crypto" in _placed_and_skipped(
        owner.run_cycle(tags=("crypto",), now_utc=outside))[0]


# =====================================================================================
# the H8 interaction — shutting the gate shuts this policy too
# =====================================================================================

def test_the_flatten_does_not_fire_while_live_broker_authority_is_false(tmp_path):
    """CLAUDE.md H8, one layer up, and it is a HAZARD rather than a feature.

    `_manage_engine` returns `live_broker_authority_false_observe_only` before reaching the
    weekend check, so shutting the gate on a funded redacted_account account stops the compliance
    close as well as everything else. Nothing inside the gate can fix it; the operating rule is
    flatten first, confirm flat, then shut the gate. Pinned so the ordering cannot drift
    silently into 'the policy fires but the close is suppressed', which would log a weekend flat
    that never happened.
    """
    import tempfile

    from tests.ultimate_book import test_book_owner as TBO

    owner = UltimateBookOwner(TBO._cfg(False), TBO._FakeMT5(), tempfile.mkdtemp(),
                              weekend_policy=WP.WeekendPolicy(sleeves=("crypto",)))
    owner._broker_server_name = lambda: FTMO
    assert owner._live_broker_authority() is False
    ee = _FakeEngine()
    summary = {"managed": [], "closed": [], "errors": [], "adopted": []}
    _freeze_module_clock(owner, _inside())
    owner._manage_engine(ee, "BTCUSD", "crypto", summary)
    assert ee.close_calls == []
    assert summary["managed"][0]["action"] == "live_broker_authority_false_observe_only"
    assert summary["closed"] == []


def _freeze_module_clock(owner, when):
    """Freeze `book_owner`'s `datetime` for the management path, which has no cycle clock."""
    import src.components.ultimate_book.book_owner as BO

    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return when if tz is not None else when.replace(tzinfo=None)

    BO.datetime = _Frozen


# =====================================================================================
# the launcher surface
# =====================================================================================

def test_run_book_exposes_the_flags_and_defaults_them_off():
    import ast

    src = (REPO / "run_book.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    flags = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument" and node.args
                and isinstance(node.args[0], ast.Constant)):
            name = node.args[0].value
            if isinstance(name, str) and name.startswith("--weekend"):
                kw = {k.arg: k.value for k in node.keywords}
                dflt = kw.get("default")
                flags[name] = (dflt.value if isinstance(dflt, ast.Constant) else "?")
    assert set(flags) == {"--weekend-flat", "--weekend-flatten-before-hours",
                          "--weekend-entry-embargo-hours", "--weekend-exempt",
                          "--weekend-early-close"}
    assert flags["--weekend-flat"] is None
    assert flags["--weekend-exempt"] is None
    assert flags["--weekend-early-close"] is None
    assert flags["--weekend-flatten-before-hours"] is None
    assert flags["--weekend-entry-embargo-hours"] == 0.0


def test_no_weekend_key_reaches_a_config_file():
    """`agent_config.yaml` and `profiles/redacted_account.yaml` are hashed into live activation tokens;
    a key there would stop an armed book placing until the token was re-minted."""
    for p in ("config/agent_config.yaml", "config/profiles/redacted_account.yaml",
              "config/profiles/operator_profile.yaml"):
        text = (REPO / p).read_text(encoding="utf-8")
        assert "weekend_flat" not in text, p
        assert "ultimate_book_weekend" not in text, p


def test_the_research_receipt_is_committed_and_carries_the_headline_cell():
    """The switch's help text quotes a measured cost; the artifact it quotes has to exist."""
    import json

    art = (REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts/"
                  "BA_WEEKEND_V1.json")
    doc = json.loads(art.read_text(encoding="utf-8"))
    assert doc["headline_cutoff"] == "m0"
    cells = doc["flat"]["cells"]
    got = {(c["sleeve"], c["arm"]) for c in cells if c["band"] == "mid"}
    for s in ARMED:
        assert (s, "as_walked") in got and (s, "flat_calendar_m0") in got
    # ...and the baseline control that makes every delta a delta.
    ctl = doc["flat"]["control_reproduces_as_walked"]
    assert all(v["identical"] for v in ctl.values()), ctl

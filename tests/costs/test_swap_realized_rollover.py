"""Swap must behave like a financing charge: levied at rollover, not by elapsed time.

These are behavioural.  They drive `_swap_cost_packet` and assert on the money it books,
and the central one replays the invariant against the real broker deal records rather
than against the model's own output.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
from pathlib import Path

import pytest

from src.components.broker_net_cost_engine import _swap_cost_packet

SERVER = "FTMO-Server3"
# EURUSD on FTMO: swap mode 1 (points), swap_long -9.38, point 1e-05.
SPEC = {"fields": {"swap_mode": 1.0, "point": 1e-05, "swap_rollover3days": 3.0}}
SWAP_LONG = -9.38
SL = 0.0005          # 50 pip stop
# Broker wall clock is America/New_York + 7 h, so broker midnight is 21:00 UTC in US DST
# and 22:00 UTC outside it.
JUN = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)   # EDT -> rollover 21:00 UTC
FEB = dt.datetime(2026, 2, 10, tzinfo=dt.timezone.utc)   # EST -> rollover 22:00 UTC


def _packet(entry, exit_=None, *, bars=32.0):
    return _swap_cost_packet(
        runtime_cfg={"selected_cell_swap_cost_minutes_per_bar": 15},
        trade_params={"gtos_vnext_dynamic_time_stop_bars": bars},
        spec=SPEC,
        swap_value=SWAP_LONG,
        entry_price=1.08,
        sl_distance=SL,
        entry_utc=entry,
        exit_utc=exit_,
        server=SERVER,
    )


def _at(day, hh, mm=0):
    return day + dt.timedelta(hours=hh, minutes=mm)


class TestRealizedHoldDecidesTheCharge:
    def test_short_hold_away_from_rollover_costs_exactly_zero(self):
        """A 3-minute trade at 18:00 UTC pays no financing.  The old model charged a night."""
        p = _packet(_at(JUN, 18), _at(JUN, 18, 3))
        assert p["cost_r"] == 0.0
        assert p["swap_charge_units"] == 0
        assert p["swap_charge_basis"] == "broker_wall_midnight_crossings_realized"

    def test_the_same_entry_without_an_exit_still_charges_a_full_night(self):
        """The defect, pinned: the forecast path charges 18:00 UTC a night it never incurs."""
        p = _packet(_at(JUN, 18))            # no exit -> pretrade forecast, 32 bars = 8 h
        assert p["swap_charge_units"] == 1
        assert p["cost_r"] > 0
        assert p["swap_charge_basis"] == "broker_wall_midnight_crossings"
        assert p["swap_horizon_source"] == "forecast_planned_time_stop"
        assert p["swap_horizon_hours_used"] == pytest.approx(8.0)

    def test_a_long_hold_that_never_crosses_is_still_free(self):
        """20 hours of holding, no rollover crossed, no charge.  Duration is not the rule."""
        p = _packet(_at(JUN, 22), _at(JUN + dt.timedelta(days=1), 18))
        assert (p["exit_utc"] is not None) and p["swap_charge_units"] == 0
        assert p["cost_r"] == 0.0

    def test_a_two_minute_hold_that_does_cross_pays_one_full_night(self):
        """Two minutes across 21:00 UTC costs a whole night.  Crossing is the rule."""
        p = _packet(_at(JUN, 20, 59), _at(JUN, 21, 1))
        assert p["swap_charge_units"] == 1
        assert p["cost_r"] == pytest.approx(abs(SWAP_LONG) * 1e-05 / SL)

    def test_charge_scales_with_nights_not_with_hours(self):
        one = _packet(_at(JUN, 20), _at(JUN + dt.timedelta(days=1), 1))
        two = _packet(_at(JUN, 20), _at(JUN + dt.timedelta(days=2), 1))
        assert one["swap_charge_units"] == 1 and two["swap_charge_units"] == 2
        assert two["cost_r"] == pytest.approx(2 * one["cost_r"])

    def test_rollover_boundary_follows_the_us_dst_calendar_not_a_fixed_offset(self):
        """21:00 UTC is the rollover in June and 22:00 UTC in February.

        The same 20:50->21:10 UTC hold is charged a night in June and nothing in February.
        A fixed +3 offset -- which this repo has been burned by before -- would charge both.
        """
        feb_mon = dt.datetime(2026, 2, 9, tzinfo=dt.timezone.utc)   # -> crosses into Tue, weight 1
        assert _packet(_at(JUN, 20, 50), _at(JUN, 21, 10))["swap_charge_units"] == 1
        assert _packet(_at(feb_mon, 20, 50), _at(feb_mon, 21, 10))["swap_charge_units"] == 0
        assert _packet(_at(feb_mon, 21, 50), _at(feb_mon, 22, 10))["swap_charge_units"] == 1
        # and an entry already past the rollover waits for tomorrow's
        assert _packet(_at(JUN, 21, 20), _at(JUN, 21, 40))["swap_charge_units"] == 0

    def test_the_triple_swap_weekday_is_charged_three_nights(self):
        """Broker Wednesday collects the weekend: 2026-02-11 is a Wednesday, weight 3."""
        feb_tue = dt.datetime(2026, 2, 10, tzinfo=dt.timezone.utc)
        p = _packet(_at(feb_tue, 21, 50), _at(feb_tue, 22, 10))
        assert p["swap_charge_units"] == 3
        assert p["cost_r"] == pytest.approx(3 * abs(SWAP_LONG) * 1e-05 / SL)

    def test_weekend_midnights_are_not_charged_separately(self):
        """Saturday 2026-06-13 broker-wall midnight carries no charge."""
        sat = dt.datetime(2026, 6, 12, tzinfo=dt.timezone.utc)   # broker Fri -> Sat crossing
        p = _packet(_at(sat, 20), _at(sat + dt.timedelta(days=1), 1))
        assert p["swap_charge_units"] == 0


class TestPretradePathIsUnchanged:
    """Live accounts are armed; the forecast path must not move by a single float."""

    def test_absent_exit_reproduces_the_legacy_packet_exactly(self):
        legacy_fields = (
            "cost_r", "daily_cost_r", "daily_price_drag", "swap_charge_units",
            "swap_charge_basis", "model_version", "source_status", "rollover_nights_charged",
        )
        p = _packet(_at(JUN, 13), None)
        assert p["swap_charge_basis"] == "broker_wall_midnight_crossings"
        assert p["swap_charge_is_realized"] is False
        assert all(k in p for k in legacy_fields)
        assert p["cost_r"] == pytest.approx(abs(SWAP_LONG) * 1e-05 / SL)

    def test_exit_before_entry_falls_back_to_the_forecast_and_says_so(self):
        p = _packet(_at(JUN, 18), _at(JUN, 17))
        assert p["swap_horizon_source"] == "source_gap_exit_before_entry"
        assert p["swap_charge_is_realized"] is False


DEALS = Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")


@pytest.mark.parametrize(
    "acct,server", [("ftmo", "FTMO-Server3"), ("redacted_account", "redacted_account-Server 2")]
)
def test_broker_charged_no_swap_without_a_crossing_on_any_real_deal(acct, server):
    """The rule, checked against real money rather than against our own model.

    Across every closed position in the 2026-07-25 export, the broker charges swap if and
    only if the position was open across a broker-wall midnight.  Holds of 14.7 h (FTMO)
    and 17.9 h (redacted_account) with no crossing were charged exactly 0.00.
    """
    from src.utils.broker_clock import (
        broker_epoch_to_utc,
        resolve_rule,
        utc_to_broker_naive,
    )

    path = DEALS / f"{acct}_history_deals_get.jsonl"
    if not path.is_file():
        pytest.skip(f"VPS export not present on this machine: {path}")

    rule = resolve_rule(server)
    positions: dict[int, dict] = collections.defaultdict(dict)
    for line in path.read_text().splitlines():
        d = json.loads(line)
        if not d.get("symbol"):
            continue
        if d["entry"] == 0:
            positions[d["position_id"]]["in"] = d
        elif d["entry"] == 1:
            positions[d["position_id"]].setdefault("out", []).append(d)

    charged_without_crossing = []
    n_closed = n_crossed_and_charged = 0
    for pid, v in positions.items():
        if "in" not in v or "out" not in v:
            continue
        n_closed += 1
        entry = broker_epoch_to_utc(v["in"]["time"], rule)
        exit_ = broker_epoch_to_utc(max(o["time"] for o in v["out"]), rule)
        swap = sum(o["swap"] for o in v["out"])
        crossings = (
            utc_to_broker_naive(exit_, rule).date() - utc_to_broker_naive(entry, rule).date()
        ).days
        if crossings == 0 and abs(swap) > 1e-9:
            charged_without_crossing.append((pid, swap, (exit_ - entry).total_seconds() / 3600))
        if crossings > 0 and abs(swap) > 1e-9:
            n_crossed_and_charged += 1

    assert n_closed > 100, f"expected a usable deal population, got {n_closed}"
    assert not charged_without_crossing, (
        f"{acct}: broker charged swap without a rollover crossing on "
        f"{len(charged_without_crossing)} positions: {charged_without_crossing[:5]}"
    )
    assert n_crossed_and_charged > 0, "no crossing position carried swap; check the pairing"

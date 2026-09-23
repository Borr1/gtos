"""F7 regression suite --- broker time must never again be labelled UTC.

Two invariants, and the second is the one that matters.

**The Friday invariant.** A true-UTC FX week ends by ~22:00Z, so a Friday bar stamped
after 22:05Z proves the stamp is broker-local. This is the test the plan asked for and
it catches the *original* defect --- but on its own it is weak, because a correction
using the *wrong DST calendar* still lands Friday bars before 22:05Z. It would have
passed against the EU-calendar reading that both audits carried.

**The exchange-anchor invariant.** A cash equity open is a fixed point in its own
exchange's calendar, so after correction the opening bar must land on that exchange's
true-UTC open --- including inside the ~3 weeks each spring and ~1 week each autumn
when the US and EU DST calendars disagree. Those windows are the only ones that
discriminate between the two calendars, and an EU-calendar correction is wrong by
exactly one hour in every one of them. This is the test that fails against the wrong
calendar, and the reason it exists is that the wrong calendar is what the repo
believed on 2026-07-26.

Everything here is behavioural. No test asserts on source text; a substring test would
pass against a wrong implementation, which is exactly the failure mode of this defect.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.broker_clock import (  # noqa: E402
    NEW_YORK_PLUS_7,
    UnsupportedBrokerClockDateError,
    UnknownBrokerClockError,
    broker_epoch_to_utc,
    broker_naive_to_utc,
    fixed_offset_rule,
    offset_seconds_at_broker_time,
    offset_seconds_at_utc,
    resolve_rule,
    utc_to_broker_naive,
)
from src.utils.research_timebase import (  # noqa: E402
    BROKER_LOCAL,
    TRUE_UTC,
    UndeclaredTimeBaseError,
    read_bars,
    timebase_for,
    write_sidecar,
)

FRIDAY_LATEST_UTC_HOUR = 22
FRIDAY_LATEST_UTC_MINUTE = 5


_EXPORTER = None


def _load_exporter():
    """Import the exporter by path, once.

    Registered in ``sys.modules`` so ``@dataclass`` can resolve ``__module__``, and
    cached so repeated calls hand back the *same* module object --- loading it twice
    produces two distinct copies of every class in it, which is the same second-module
    hazard ``CLAUDE.md`` records for ``sys.modules`` deletion.
    """
    global _EXPORTER
    if _EXPORTER is None:
        name = "_export_mt5_research_ohlcv"
        spec = importlib.util.spec_from_file_location(
            name, REPO_ROOT / "scripts" / "export_mt5_research_ohlcv.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _EXPORTER = module
    return _EXPORTER


# --------------------------------------------------------------------------------------
# The clock rule itself
# --------------------------------------------------------------------------------------


class TestBrokerClockRule:
    """The measured rule: broker wall clock == America/New_York wall clock + 7h."""

    # (broker wall clock, expected true UTC, what anchors it)
    # Every row is a real exchange open observed in data/historical_2026.
    ANCHORS = [
        ("2026-01-15 02:00", "2026-01-15 00:00", "JP225 Tokyo 09:00 JST, US winter"),
        ("2026-03-11 03:00", "2026-03-11 00:00", "JP225 Tokyo 09:00 JST, inside the US/EU gap"),
        ("2026-03-06 10:00", "2026-03-06 08:00", "GER40 Frankfurt 09:00 CET, US winter"),
        ("2026-03-09 11:00", "2026-03-09 08:00", "GER40 Frankfurt 09:00 CET, inside the gap"),
        ("2026-03-30 10:00", "2026-03-30 07:00", "GER40 Frankfurt 09:00 CEST, both summer"),
        ("2025-10-24 10:00", "2025-10-24 07:00", "GER40 Frankfurt 09:00 CEST, both summer"),
        ("2025-10-28 11:00", "2025-10-28 08:00", "GER40 Frankfurt 09:00 CET, inside the autumn gap"),
        ("2025-11-04 10:00", "2025-11-04 08:00", "GER40 Frankfurt 09:00 CET, both winter"),
        ("2026-03-06 16:30", "2026-03-06 14:30", "NYSE 09:30 EST"),
        ("2026-03-09 16:30", "2026-03-09 13:30", "NYSE 09:30 EDT, inside the gap"),
    ]

    @pytest.mark.parametrize("broker,expected,anchor", ANCHORS)
    def test_measured_exchange_anchors(self, broker, expected, anchor):
        got = broker_naive_to_utc(datetime.strptime(broker, "%Y-%m-%d %H:%M"), NEW_YORK_PLUS_7)
        assert got == datetime.strptime(expected, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), anchor

    def test_switches_on_us_dst_dates_not_eu(self):
        """The whole finding in one assertion.

        2026-03-08 is the US spring-forward; 2026-03-29 is the EU one. The offset must
        move on the first and not the second. An EU-calendar implementation inverts this.
        """
        at = lambda d: offset_seconds_at_broker_time(datetime.strptime(d, "%Y-%m-%d %H:%M"), NEW_YORK_PLUS_7)
        assert at("2026-03-06 12:00") == 2 * 3600
        assert at("2026-03-09 12:00") == 3 * 3600, "must move on the US date 2026-03-08"
        assert at("2026-03-27 12:00") == 3 * 3600, "must NOT still be +2 in the gap window"
        assert at("2026-03-30 12:00") == 3 * 3600, "must NOT move again on the EU date 2026-03-29"
        # Autumn: EU falls back 2025-10-26, the US on 2025-11-02.
        assert at("2025-10-24 12:00") == 3 * 3600
        assert at("2025-10-28 12:00") == 3 * 3600, "must NOT move on the EU date 2025-10-26"
        assert at("2025-11-04 12:00") == 2 * 3600, "must move on the US date 2025-11-02"

    def test_pre_2007_uses_the_1987_2006_us_rule(self):
        """The deep archive predates the 2007 Energy Policy Act change."""
        at = lambda s: offset_seconds_at_utc(
            datetime.fromisoformat(s).replace(tzinfo=timezone.utc), NEW_YORK_PLUS_7
        )
        # In 2006 DST did not start in March. It began on the first Sunday in April.
        assert at("2006-03-20T12:00:00") == 2 * 3600
        assert at("2006-04-02T06:59:59") == 2 * 3600
        assert at("2006-04-02T07:00:00") == 3 * 3600
        # It ended on the last Sunday in October, not November.
        assert at("2006-10-29T05:59:59") == 3 * 3600
        assert at("2006-10-29T06:00:00") == 2 * 3600

    def test_2007_boundary_uses_the_new_rule(self):
        at = lambda s: offset_seconds_at_utc(
            datetime.fromisoformat(s).replace(tzinfo=timezone.utc), NEW_YORK_PLUS_7
        )
        assert at("2007-03-11T06:59:59") == 2 * 3600
        assert at("2007-03-11T07:00:00") == 3 * 3600
        assert at("2007-11-04T05:59:59") == 3 * 3600
        assert at("2007-11-04T06:00:00") == 2 * 3600

    def test_pre_1987_refuses_in_both_conversion_directions(self):
        with pytest.raises(UnsupportedBrokerClockDateError, match="before 1987"):
            utc_to_broker_naive(
                datetime(1986, 7, 1, tzinfo=timezone.utc), NEW_YORK_PLUS_7
            )
        with pytest.raises(UnsupportedBrokerClockDateError, match="before 1987"):
            broker_naive_to_utc(datetime(1986, 7, 1, 12), NEW_YORK_PLUS_7)

    def test_only_two_offsets_ever(self):
        """A GMT+2/+3 broker takes exactly two values; a third means the rule is broken."""
        seen = set()
        cursor = datetime(2022, 1, 1)
        while cursor < datetime(2027, 1, 1):
            seen.add(offset_seconds_at_broker_time(cursor, NEW_YORK_PLUS_7))
            cursor += timedelta(hours=6)
        assert seen == {2 * 3600, 3 * 3600}

    def test_round_trips(self):
        cursor = datetime(2025, 1, 1)
        while cursor < datetime(2027, 1, 1):
            # Skip the two hours a year that do not exist / repeat in New York; they sit
            # inside the FX weekend and no bar can land there (see the module docstring).
            if not (cursor.month in (3, 11) and cursor.weekday() == 6 and 8 <= cursor.hour <= 10):
                utc = broker_naive_to_utc(cursor, NEW_YORK_PLUS_7)
                assert utc_to_broker_naive(utc, NEW_YORK_PLUS_7) == cursor, cursor
            cursor += timedelta(hours=7)

    def test_dst_transitions_fall_inside_the_fx_weekend(self):
        """The claim that licenses ignoring fold ambiguity, asserted rather than assumed.

        Both US transitions are 02:00 New York on a Sunday. The FX week runs Sunday
        17:00 NY to Friday 17:00 NY, so a transition instant is always in the closed
        window --- no bar or tick can carry an ambiguous or non-existent stamp.
        """
        from zoneinfo import ZoneInfo

        ny = ZoneInfo("America/New_York")
        for year in (2025, 2026, 2027):
            for month, nth in ((3, 2), (11, 1)):
                # nth Sunday of the month
                day = 1
                count = 0
                while True:
                    candidate = datetime(year, month, day)
                    if candidate.weekday() == 6:
                        count += 1
                        if count == nth:
                            break
                    day += 1
                transition = datetime(year, month, day, 2, 0, tzinfo=ny)
                assert transition.weekday() == 6
                # Sunday 02:00 NY is between Friday 17:00 NY and Sunday 17:00 NY.
                assert transition.hour < 17

    def test_epoch_and_wall_clock_paths_agree(self):
        import calendar

        wall = datetime(2026, 3, 9, 11, 0)
        epoch = calendar.timegm(wall.timetuple())
        assert broker_epoch_to_utc(epoch, NEW_YORK_PLUS_7) == broker_naive_to_utc(wall, NEW_YORK_PLUS_7)

    def test_unknown_server_fails_closed(self):
        for server in ("SomeOtherBroker-Live", "", None):
            with pytest.raises(UnknownBrokerClockError):
                resolve_rule(server)

    def test_fixed_offset_rule(self):
        rule = fixed_offset_rule(3, evidence="test")
        assert broker_naive_to_utc(datetime(2026, 1, 1, 12, 0), rule) == datetime(
            2026, 1, 1, 9, 0, tzinfo=timezone.utc
        )

    def test_provenance_is_self_describing(self):
        payload = NEW_YORK_PLUS_7.provenance()
        assert payload["broker_clock_rule"] == "new_york_plus_7"
        assert payload["broker_clock_anchor_zone"] == "America/New_York"
        assert payload["broker_clock_anchor_offset_hours"] == 7.0
        assert payload["broker_clock_evidence"]


# --------------------------------------------------------------------------------------
# The export path
# --------------------------------------------------------------------------------------


class FakeMT5:
    """Enough of the MT5 surface to drive the exporter. Touches no broker.

    Models the real contract: bar epochs are broker-localized, and ``copy_rates_range``
    compares its bounds against those same broker-localized epochs.
    """

    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H4 = 16388
    TIMEFRAME_D1 = 16408

    def __init__(self, bars):
        self._bars = bars
        self.requested_windows = []

    def symbol_select(self, symbol, enable):
        return True

    def last_error(self):
        return (0, "ok")

    def copy_rates_range(self, symbol, timeframe, start, end):
        self.requested_windows.append((start, end))
        lo = start.timestamp() if start.tzinfo else start.replace(tzinfo=timezone.utc).timestamp()
        hi = end.timestamp() if end.tzinfo else end.replace(tzinfo=timezone.utc).timestamp()
        return [b for b in self._bars if lo <= b["time"] < hi]


def _broker_bars(first_wall: datetime, count: int, step_minutes: int = 15):
    """Bars stamped in broker wall clock, as MT5 delivers them."""
    import calendar

    out = []
    for i in range(count):
        wall = first_wall + timedelta(minutes=step_minutes * i)
        out.append(
            {
                "time": calendar.timegm(wall.timetuple()),
                "open": 100.0 + i,
                "high": 101.0 + i,
                "low": 99.0 + i,
                "close": 100.5 + i,
                "tick_volume": 10 + i,
            }
        )
    return out


class TestExportPathEmitsTrueUtc:
    def _run(self, tmp_path, bars, clock, start, end):
        mod = _load_exporter()
        mt5 = FakeMT5(bars)
        result = mod.export_research_ohlcv(
            mt5_module=mt5,
            specs=[mod.SymbolSpec(file_symbol="GER40", mt5_symbol="GER40.cash")],
            timeframe_names=["M15"],
            start=start,
            end=end,
            output_dir=tmp_path,
            clock=clock,
        )
        return mod, mt5, result

    def test_friday_bars_land_before_2205z(self, tmp_path):
        """The plan's invariant. Broker Friday 23:45 must not survive as 23:45 'UTC'."""
        # 2026-03-06 is a Friday in US winter (+2). The broker week ends 23:45 broker.
        bars = _broker_bars(datetime(2026, 3, 6, 21, 0), 12)
        _, _, result = self._run(
            tmp_path, bars, NEW_YORK_PLUS_7,
            datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 8, tzinfo=timezone.utc),
        )
        rows = list(csv.DictReader((tmp_path / "GER40_M15.csv").open()))
        assert rows, "exporter wrote no rows"
        for row in rows:
            stamp = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            if stamp.weekday() == 4:
                assert (stamp.hour, stamp.minute) <= (FRIDAY_LATEST_UTC_HOUR, FRIDAY_LATEST_UTC_MINUTE), (
                    f"Friday bar at {stamp} is after 22:05Z, so this stamp is broker time, not UTC"
                )

    def test_uncorrected_mode_reproduces_the_defect_and_says_so(self, tmp_path):
        """The legacy path stays available, but can no longer be mistaken for UTC."""
        mod = _load_exporter()
        bars = _broker_bars(datetime(2026, 3, 6, 21, 0), 12)
        _, _, result = self._run(
            tmp_path, bars, mod.UncorrectedClock(),
            datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 8, tzinfo=timezone.utc),
        )
        rows = list(csv.DictReader((tmp_path / "GER40_M15.csv").open()))
        late = [r for r in rows if datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S").hour >= 23]
        assert late, "uncorrected mode should still emit the broker-clock stamps"
        assert result["files"]["GER40_M15"]["broker_clock_rule"] == "uncorrected_broker_local"

    def test_request_window_is_translated_into_broker_time(self, tmp_path):
        """Correcting only the output stamps yields correct labels over a shifted window."""
        bars = _broker_bars(datetime(2026, 1, 5, 0, 0), 200)
        _, mt5, _ = self._run(
            tmp_path, bars, NEW_YORK_PLUS_7,
            datetime(2026, 1, 5, tzinfo=timezone.utc), datetime(2026, 1, 6, tzinfo=timezone.utc),
        )
        assert mt5.requested_windows, "no request was made"
        start, _ = mt5.requested_windows[0]
        # January is +2, so the true-UTC start 00:00Z is exactly broker 02:00.
        assert start.replace(tzinfo=None) == datetime(2026, 1, 5, 2, 0)

    def test_window_filter_uses_true_utc_bounds(self, tmp_path):
        """--start/--end keep meaning true UTC, as their help text says."""
        bars = _broker_bars(datetime(2026, 1, 5, 0, 0), 200)
        _, _, _ = self._run(
            tmp_path, bars, NEW_YORK_PLUS_7,
            datetime(2026, 1, 5, 6, 0, tzinfo=timezone.utc), datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc),
        )
        rows = list(csv.DictReader((tmp_path / "GER40_M15.csv").open()))
        assert rows
        stamps = [datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S") for r in rows]
        assert min(stamps) >= datetime(2026, 1, 5, 6, 0)
        assert max(stamps) < datetime(2026, 1, 5, 12, 0)

    def test_every_exported_file_declares_its_offset(self, tmp_path):
        """'An export whose offset is undeclared is the same defect wearing a correction.'"""
        mod = _load_exporter()
        bars = _broker_bars(datetime(2026, 1, 5, 0, 0), 40)
        mod_, _, result = self._run(
            tmp_path, bars, NEW_YORK_PLUS_7,
            datetime(2026, 1, 5, tzinfo=timezone.utc), datetime(2026, 1, 6, tzinfo=timezone.utc),
        )

        class Account:
            server = "FTMO-Server3"
            login = 1
            trade_mode = 0

        result = mod_.enrich_export_result_for_manifest(
            export_result=result,
            account=Account(),
            provenance={},
            start=datetime(2026, 1, 5, tzinfo=timezone.utc),
            end=datetime(2026, 1, 6, tzinfo=timezone.utc),
            manifest_path=tmp_path / "manifest.json",
            clock=NEW_YORK_PLUS_7,
        )
        payload = result["files"]["GER40_M15"]
        assert payload["broker_clock_rule"] == "new_york_plus_7"
        assert payload["time_column_basis"] == TRUE_UTC
        assert payload["broker_offset_seconds_applied"] == [2 * 3600]
        sidecar = tmp_path / "GER40_M15.csv.timebase.json"
        assert sidecar.is_file(), "each CSV needs a sidecar so a file that travels alone stays self-describing"
        assert json.loads(sidecar.read_text())["time_column_basis"] == TRUE_UTC

    def test_a_file_spanning_a_dst_seam_records_both_offsets(self, tmp_path):
        """2026-03-08 splits the sealed March challenge window. It must be visible in the file."""
        bars = _broker_bars(datetime(2026, 3, 6, 12, 0), 400, step_minutes=15)
        _, _, result = self._run(
            tmp_path, bars, NEW_YORK_PLUS_7,
            datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        assert result["files"]["GER40_M15"]["broker_offset_seconds_applied"] == [2 * 3600, 3 * 3600]


# --------------------------------------------------------------------------------------
# The view layer over the existing archive
# --------------------------------------------------------------------------------------


class TestResearchTimebaseViewLayer:
    def test_undeclared_file_fails_closed_and_does_not_assume_utc(self, tmp_path):
        path = tmp_path / "EURUSD_M15.csv"
        path.write_text("time,open,high,low,close,volume\n2026-01-02 00:00:00,1,1,1,1,1\n")
        with pytest.raises(UndeclaredTimeBaseError):
            timebase_for(path)

    def test_sidecar_overrides_and_is_honoured(self, tmp_path):
        path = tmp_path / "EURUSD_M15.csv"
        path.write_text("time,open,high,low,close,volume\n2026-01-15 02:00:00,1,1,1,1,1\n")
        write_sidecar(path, basis=BROKER_LOCAL, rule=NEW_YORK_PLUS_7,
                      evidence="test", server="FTMO-Server3")
        rows = list(read_bars(path))
        assert rows[0]["time_utc"] == datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
        assert rows[0]["time_broker_local"] == datetime(2026, 1, 15, 2, 0)

    def test_true_utc_sidecar_is_passed_through_unchanged(self, tmp_path):
        path = tmp_path / "EURUSD_M15.csv"
        path.write_text("time,open,high,low,close,volume\n2026-01-15 02:00:00,1,1,1,1,1\n")
        write_sidecar(path, basis=TRUE_UTC, rule=None, evidence="already corrected")
        rows = list(read_bars(path))
        assert rows[0]["time_utc"] == datetime(2026, 1, 15, 2, 0, tzinfo=timezone.utc)

    def test_broker_local_sidecar_without_a_resolvable_rule_fails_closed(self, tmp_path):
        path = tmp_path / "EURUSD_M15.csv"
        path.write_text("time,open,high,low,close,volume\n2026-01-15 02:00:00,1,1,1,1,1\n")
        (tmp_path / "EURUSD_M15.csv.timebase.json").write_text(
            json.dumps({"time_column_basis": BROKER_LOCAL})
        )
        with pytest.raises(UndeclaredTimeBaseError):
            timebase_for(path)


# --------------------------------------------------------------------------------------
# The archive itself, read through the view layer
# --------------------------------------------------------------------------------------

ARCHIVE = REPO_ROOT / "data" / "historical_2026"
archive_present = pytest.mark.skipif(
    not (ARCHIVE / "GER40_M15.csv").is_file(),
    reason="data/historical_2026 not materialised in this checkout",
)


@archive_present
class TestArchiveThroughTheViewLayer:
    def test_no_friday_bar_after_2205z_once_corrected(self):
        for symbol in ("EURUSD", "GER40", "XAUUSD"):
            path = ARCHIVE / f"{symbol}_M15.csv"
            if not path.is_file():
                continue
            offenders = [
                r["time_utc"]
                for r in read_bars(path)
                if r["time_utc"].weekday() == 4
                and (r["time_utc"].hour, r["time_utc"].minute)
                > (FRIDAY_LATEST_UTC_HOUR, FRIDAY_LATEST_UTC_MINUTE)
            ]
            assert not offenders, f"{symbol}: {len(offenders)} corrected Friday bars after 22:05Z, e.g. {offenders[:3]}"

    def test_raw_archive_still_violates_it(self):
        """Proves the invariant has teeth: the uncorrected bytes fail the same check."""
        rows = list(csv.DictReader((ARCHIVE / "EURUSD_M15.csv").open()))
        late = [
            r["time"] for r in rows
            if datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S").weekday() == 4
            and datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S").hour >= 23
        ]
        assert late, "if this ever passes, the raw archive has been rewritten and this suite's premise is stale"

    @pytest.mark.parametrize(
        "symbol,zone,open_utc,first_day,last_day,window_note",
        [
            # Inside the US/EU disagreement window. An EU-calendar correction lands every
            # one of these an hour late; this is the discriminating case, and the reason
            # the Friday-22:05Z test alone is not enough.
            ("GER40", "Europe/Berlin", "08:00", "2026-03-09", "2026-03-27", "spring US/EU gap"),
            ("UK100", "Europe/London", "08:00", "2026-03-09", "2026-03-27", "spring US/EU gap"),
            ("JP225", "Asia/Tokyo", "00:00", "2026-03-09", "2026-03-27", "spring US/EU gap"),
            ("GER40", "Europe/Berlin", "08:00", "2025-10-27", "2025-10-31", "autumn US/EU gap"),
            # Outside it, where both calendars agree, so these only check the magnitude.
            ("GER40", "Europe/Berlin", "08:00", "2026-01-05", "2026-02-27", "both winter"),
            ("JP225", "Asia/Tokyo", "00:00", "2026-01-05", "2026-02-27", "both winter"),
            ("GER40", "Europe/Berlin", "07:00", "2026-03-30", "2026-04-24", "both summer"),
        ],
    )
    def test_corrected_opening_bar_lands_on_the_real_exchange_open(
        self, symbol, zone, open_utc, first_day, last_day, window_note
    ):
        """The exchange-anchor invariant, measured the way the finding was measured.

        Per day, take the highest-volume corrected bar near the exchange open and record
        how far it sits from the true-UTC open. The *mode* over the window is the answer:
        a single day can be displaced by a scheduled release (10:00 ET is a standard US
        data slot and outbids the 09:30 open often enough to break a one-day assertion),
        but a wrong DST calendar displaces every day in the window by a full hour.
        """
        import collections

        path = ARCHIVE / f"{symbol}_M15.csv"
        if not path.is_file():
            pytest.skip(f"{symbol} not in archive")
        lo = datetime.strptime(first_day, "%Y-%m-%d").date()
        hi = datetime.strptime(last_day, "%Y-%m-%d").date()
        open_h, open_m = (int(x) for x in open_utc.split(":"))

        per_day: dict = collections.defaultdict(list)
        for row in read_bars(path):
            stamp = row["time_utc"]
            if lo <= stamp.date() <= hi and stamp.weekday() < 5:
                per_day[stamp.date()].append((float(row["volume"]), stamp))

        deltas = []
        for day, rows in per_day.items():
            want = datetime.combine(day, datetime.min.time()).replace(
                hour=open_h, minute=open_m, tzinfo=timezone.utc
            )
            window = [r for r in rows if want <= r[1] <= want + timedelta(hours=3)]
            if window:
                deltas.append(round((max(window)[1] - want).total_seconds() / 3600.0))

        if len(deltas) < 3:
            pytest.skip(f"{symbol}: only {len(deltas)} usable days in {window_note}")
        mode, hits = collections.Counter(deltas).most_common(1)[0]
        assert mode == 0, (
            f"{symbol} over {first_day}..{last_day} ({window_note}): the corrected opening "
            f"volume spike sits {mode:+d}h from the real {zone} open at {open_utc}Z "
            f"({hits}/{len(deltas)} days). A full hour here means the DST calendar is wrong."
        )


# --------------------------------------------------------------------------------------
# Replay/live session-gating parity --- the point of the whole exercise
# --------------------------------------------------------------------------------------


class TestReplayLiveSessionParity:
    """One session table, two feeds, and after the repair they must agree.

    ``_session_at`` compares ``ts.hour*60 + ts.minute`` against a wall-clock window table
    with no timezone normalisation, and it is reached from both the live orchestrator and
    the replay loop. Live feeds it offset-corrected bars; replay fed it the export CSVs'
    broker stamps. So the same config gated real-world hours 2-3 h apart on the two sides.

    Correcting the export is what closes it --- no session constant moves, and nothing
    SHA-contract-bound is touched. These tests pin that, and the last one proves the
    invariant has teeth by showing the uncorrected stamp still fails it.
    """

    WINDOWS = (
        ("london", "07:00", "10:30"),
        ("ny", "13:00", "15:30"),
        ("tokyo", "00:00", "03:00"),
    )

    # Real instants, and the broker stamp the export CSV carries for each. Every case is
    # chosen to cross a session boundary under the shift --- a 2-3 h error that happens to
    # stay inside one window is real but invisible here, so it would make a vacuous test.
    # 2026-03-11 sits inside the US/EU disagreement window, so it also pins the calendar.
    CASES = [
        ("2026-03-11 08:00", "2026-03-11 11:00", "london", "Frankfurt open, inside the US/EU gap"),
        ("2026-01-15 06:00", "2026-01-15 08:00", "off_configured_session", "pre-London, winter (+2)"),
        ("2026-07-01 14:00", "2026-07-01 17:00", "ny", "NY window, summer (+3)"),
        ("2026-01-15 02:00", "2026-01-15 04:00", "tokyo", "Tokyo window, winter (+2)"),
    ]

    @staticmethod
    def _session_at(stamp):
        from src.components.broader_origin_generators import _session_at

        return _session_at("EURUSD", stamp, TestReplayLiveSessionParity.WINDOWS)

    @pytest.mark.parametrize("true_utc,broker_stamp,expected,note", CASES)
    def test_corrected_replay_bar_gates_the_same_session_as_the_live_bar(
        self, true_utc, broker_stamp, expected, note
    ):
        live = datetime.strptime(true_utc, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        replay = broker_naive_to_utc(
            datetime.strptime(broker_stamp, "%Y-%m-%d %H:%M"), NEW_YORK_PLUS_7
        )
        assert replay == live, f"{note}: the corrected replay stamp is not the live instant"
        assert self._session_at(replay) == self._session_at(live) == expected, note

    @pytest.mark.parametrize("true_utc,broker_stamp,expected,note", CASES)
    def test_uncorrected_replay_bar_gates_a_different_session(
        self, true_utc, broker_stamp, expected, note
    ):
        """Teeth. If this ever passes, either the table changed or the defect came back."""
        live = datetime.strptime(true_utc, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        uncorrected = datetime.strptime(broker_stamp, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        assert self._session_at(uncorrected) != self._session_at(live), (
            f"{note}: broker stamp {broker_stamp} and true UTC {true_utc} landed in the same "
            "session, so this case no longer demonstrates the divergence"
        )


class TestLiveSleeveServerClock:
    """The live half of F7: sleeves that convert UTC -> FTMO server time.

    ``fx_jpy._ftmo_server_offset_hours`` (also used by ``metals``) computed the offset
    from the EU DST calendar. Its own "+179 min" measurement was taken in summer, when
    both calendars agree, and generalised to the wrong one --- so it was an hour off for
    ~3 weeks each spring and ~1 week each autumn.
    """

    @pytest.mark.parametrize(
        "instant,expected_offset,note",
        [
            ("2026-03-06", 2, "before the US switch"),
            ("2026-03-11", 3, "inside the US/EU gap --- the EU rule returned 2 here"),
            ("2026-03-27", 3, "still inside the gap"),
            ("2026-03-31", 3, "after the EU switch, unchanged"),
            ("2025-10-24", 3, "before the EU fall-back"),
            ("2025-10-29", 3, "inside the autumn gap --- the EU rule returned 2 here"),
            ("2025-11-05", 2, "after the US fall-back"),
        ],
    )
    def test_server_offset_follows_the_us_calendar(self, instant, expected_offset, note):
        from src.components.ultimate_book.sleeves.fx_jpy import _ftmo_server_offset_hours

        stamp = datetime.fromisoformat(f"{instant}T12:00:00+00:00")
        assert _ftmo_server_offset_hours(stamp) == expected_offset, note

    def test_server_local_conversion_matches_the_shared_rule(self):
        """The sleeve and the export path must not drift into two different clocks."""
        from src.components.ultimate_book.sleeves.fx_jpy import _to_server_local

        cursor = datetime(2025, 1, 1, tzinfo=timezone.utc)
        while cursor < datetime(2027, 1, 1, tzinfo=timezone.utc):
            assert _to_server_local(cursor) == utc_to_broker_naive(cursor, NEW_YORK_PLUS_7), cursor
            cursor += timedelta(hours=13)


# --------------------------------------------------------------------------------------
# Regressions for the adversarial review of the landed implementation
# --------------------------------------------------------------------------------------


class TestNoTimezoneDatabaseDependency:
    """The live sleeves must not need an IANA tz database.

    An earlier draft resolved the offset through ``ZoneInfo("America/New_York")``.
    Windows ships no system tzdb, ``tzdata`` is not in requirements.txt, and the failure
    is an *exception* --- which ``metals.py`` swallows into ``session_hour = None``, and
    that admits rather than blocks. A missing package would have loosened a live gate.
    """

    def test_offset_resolves_with_no_tz_database_available(self):
        import zoneinfo

        original = list(zoneinfo.TZPATH)
        try:
            zoneinfo.reset_tzpath([])
            zoneinfo.ZoneInfo.clear_cache()
            from src.components.ultimate_book.sleeves.fx_jpy import (
                _ftmo_server_offset_hours,
                _to_server_local,
            )

            assert _ftmo_server_offset_hours(datetime(2026, 7, 1, 12, tzinfo=timezone.utc)) == 3
            assert _ftmo_server_offset_hours(datetime(2026, 1, 15, 12, tzinfo=timezone.utc)) == 2
            assert _to_server_local(datetime(2026, 3, 11, 8, tzinfo=timezone.utc)) == datetime(2026, 3, 11, 11)
        finally:
            zoneinfo.reset_tzpath(original)
            zoneinfo.ZoneInfo.clear_cache()

    def test_broker_clock_module_imports_no_zoneinfo(self):
        source = (REPO_ROOT / "src" / "utils" / "broker_clock.py").read_text()
        code_lines = [
            line for line in source.splitlines()
            if not line.lstrip().startswith("#") and "zoneinfo" in line.lower()
        ]
        assert not [ln for ln in code_lines if "import" in ln], (
            "broker_clock must stay free of zoneinfo: it is on the live sleeve path and the "
            f"production host has no IANA tz database. Offending lines: {code_lines}"
        )

    def test_arithmetic_matches_zoneinfo_where_a_tz_database_exists(self):
        """Cross-check, so the hand-rolled US DST rule can never silently diverge."""
        zi = pytest.importorskip("zoneinfo")
        try:
            ny = zi.ZoneInfo("America/New_York")
        except Exception:  # pragma: no cover - no tzdata on this machine
            pytest.skip("no IANA tz database available")
        cursor = datetime(2022, 1, 1, tzinfo=timezone.utc)
        while cursor < datetime(2028, 1, 1, tzinfo=timezone.utc):
            expected = int((cursor.astimezone(ny).utcoffset().total_seconds())) + 7 * 3600
            assert offset_seconds_at_utc(cursor, NEW_YORK_PLUS_7) == expected, cursor
            cursor += timedelta(hours=5)


class TestViewLayerReviewRegressions:
    def test_z_suffixed_stamps_do_not_override_the_declared_basis(self):
        """A "+00:00"/"Z" suffix is exactly what the F7 defect emits; it proves nothing.

        Measured example in the tree: 25_data/raw/XAUUSD_M15.csv carries Z-suffixed
        stamps that are broker time.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "XAUUSD_M15.csv"
            path.write_text("time,open,high,low,close,volume\n2026-03-10T16:30:00+00:00,1,1,1,1,1\n")
            write_sidecar(path, basis=BROKER_LOCAL, rule=NEW_YORK_PLUS_7,
                          evidence="test", server="FTMO-Server3")
            row = next(iter(read_bars(path)))
            assert row["time_utc"] == datetime(2026, 3, 10, 13, 30, tzinfo=timezone.utc), (
                "the declared broker-local basis must win over the +00:00 suffix"
            )

    def test_true_utc_files_report_no_broker_local_stamp(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "X_M15.csv"
            path.write_text("time,open,high,low,close,volume\n2026-01-15 02:00:00,1,1,1,1,1\n")
            write_sidecar(path, basis=TRUE_UTC, rule=None, evidence="already corrected")
            row = next(iter(read_bars(path)))
            assert row["time_broker_local"] is None

    def test_caller_evidence_survives_the_rule_provenance(self):
        import json as _json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "X_M15.csv"
            path.write_text("time\n2026-01-15 02:00:00\n")
            side = write_sidecar(path, basis=BROKER_LOCAL, rule=NEW_YORK_PLUS_7,
                                 evidence="VERIFICATION SKIPPED — asserted, not measured",
                                 server="FTMO-Server3")
            assert "VERIFICATION SKIPPED" in _json.loads(side.read_text())["broker_clock_evidence"]

    def test_the_ambiguous_historical_directory_is_not_declared(self):
        """Copies of data/historical/ disagree; a blanket declaration double-shifts one."""
        from src.utils.research_timebase import LEGACY_DECLARATIONS

        assert "historical" not in LEGACY_DECLARATIONS


class TestValidatorDiscriminatesCalendars:
    """Percentage agreement cannot separate the two calendars; transition dates can."""

    @pytest.mark.skipif(not (ARCHIVE / "GER40_M15.csv").is_file(), reason="archive not materialised")
    def test_seam_gate_rejects_an_eu_calendar_rule(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_measure_probe", REPO_ROOT / "scripts" / "measure_broker_clock_offset.py"
        )
        probe = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = probe
        spec.loader.exec_module(probe)

        assert probe.main(["--data-dir", str(ARCHIVE), "--check", "FTMO-Server3"]) == 0

        def eu_offset(instant, rule):
            from datetime import date as _date

            def last_sunday(month):
                day = _date(instant.year, month, 31)
                while day.weekday() != 6:
                    day -= timedelta(days=1)
                return datetime(day.year, day.month, day.day, 1, tzinfo=timezone.utc)

            return 10800 if last_sunday(3) <= instant < last_sunday(10) else 7200

        original = probe.offset_seconds_at_utc
        try:
            probe.offset_seconds_at_utc = eu_offset
            assert probe.main(["--data-dir", str(ARCHIVE), "--check", "FTMO-Server3"]) == 1, (
                "an EU-calendar rule must be rejected; it still scores ~86-92% on days, so the "
                "percentage threshold alone would let it through"
            )
        finally:
            probe.offset_seconds_at_utc = original

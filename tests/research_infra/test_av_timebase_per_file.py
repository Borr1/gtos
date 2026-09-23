"""Session AV — per-file time-base proof, the third basis, and the interop defect it exposed.

Behavioural throughout: every test builds a file whose stamps ARE in a known clock and
asserts what the machinery concludes from those bytes. Nothing greps a source string --- a
substring assertion would pass against a wrong implementation, which is the one thing this
subsystem cannot afford (F7).
"""

from __future__ import annotations

import datetime as dt
import importlib.util as ilu
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.replay_policy.generation import CsvBarSource, GenerationError  # noqa: E402
from src.utils.broker_clock import NEW_YORK_PLUS_7, broker_naive_to_utc  # noqa: E402
from src.utils.research_timebase import (  # noqa: E402
    BROKER_LOCAL,
    BROKER_LOCAL_EU_CORRECTED,
    TRUE_UTC,
    TimeBaseOutOfDeclaredRangeError,
    in_us_eu_dst_disagreement,
    read_bars,
    timebase_for,
    to_true_utc,
    write_sidecar,
)

VERIFY_PATH = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_timebase_verify.py"


def _load_verifier():
    spec = ilu.spec_from_file_location("av_timebase_verify", VERIFY_PATH)
    module = ilu.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AV = _load_verifier()


# --------------------------------------------------------------------------------------
# Synthetic bar files whose clock is known BY CONSTRUCTION
# --------------------------------------------------------------------------------------

NY = AV.NY


def _ny_1700(day: dt.date) -> dt.datetime:
    return (
        dt.datetime.combine(day, dt.time(17, 0), tzinfo=NY)
        .astimezone(dt.timezone.utc)
        .replace(tzinfo=None)
    )


def _true_utc_hourly_bars(first: dt.date, last: dt.date) -> list[dt.datetime]:
    """Hourly spot-FX bars in TRUE UTC: week opens at NY 17:00 Sunday, closes NY 17:00 Friday."""
    out: list[dt.datetime] = []
    day = first - dt.timedelta(days=first.weekday() + 1)  # step back to a Sunday
    while day <= last:
        start = _ny_1700(day)
        end = _ny_1700(day + dt.timedelta(days=5))  # the Friday close
        t = start
        while t < end:
            if first <= t.date() <= last:
                out.append(t)
            t += dt.timedelta(hours=1)
        day += dt.timedelta(days=7)
    return sorted(out)


def _write_csv(path: Path, stamps, fmt="%Y-%m-%d %H:%M:%S") -> Path:
    lines = ["time,open,high,low,close,volume"]
    for i, s in enumerate(stamps):
        lines.append(f"{s.strftime(fmt)},1.0,1.1,0.9,1.05,{100 + i % 7}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _stamps_in(basis: str, first: dt.date, last: dt.date) -> list[dt.datetime]:
    utc = _true_utc_hourly_bars(first, last)
    if basis == TRUE_UTC:
        return utc
    if basis == BROKER_LOCAL:
        # invert broker_naive_to_utc: broker wall clock = UTC + (7h - NY offset)
        out = []
        for u in utc:
            aware = u.replace(tzinfo=dt.timezone.utc)
            offset = aware.astimezone(NY).utcoffset() + dt.timedelta(hours=7)
            out.append(u + offset)
        return out
    if basis == BROKER_LOCAL_EU_CORRECTED:
        return [u + dt.timedelta(hours=1) if in_us_eu_dst_disagreement(u.date()) else u for u in utc]
    raise AssertionError(basis)


SPAN = (dt.date(2024, 1, 1), dt.date(2025, 6, 30))  # spans four disagreement windows


# --------------------------------------------------------------------------------------
# The disagreement-window primitive
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "day,expected",
    [
        (dt.date(2025, 1, 15), False),   # deep winter, both calendars agree
        (dt.date(2025, 7, 15), False),   # deep summer, both agree
        (dt.date(2025, 3, 12), True),    # US sprang 03-09, EU not until 03-30
        (dt.date(2025, 3, 29), True),    # last day before the EU spring-forward
        (dt.date(2025, 3, 31), False),   # EU has caught up
        (dt.date(2025, 10, 28), True),   # EU fell back 10-26, US not until 11-02
        (dt.date(2025, 11, 3), False),   # US has caught up
    ],
)
def test_disagreement_window_is_computed_not_tabulated(day, expected):
    assert in_us_eu_dst_disagreement(day) is expected


def test_verifier_and_library_agree_on_the_window():
    """Two implementations of the same predicate must not drift apart."""
    day = dt.date(2024, 1, 1)
    while day < dt.date(2027, 1, 1):
        assert AV.in_disagreement_window(day) == in_us_eu_dst_disagreement(day), day
        day += dt.timedelta(days=1)


# --------------------------------------------------------------------------------------
# The classifier recovers the clock it was given
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "basis,verdict",
    [
        (TRUE_UTC, "STAMP_TRUE_UTC"),
        (BROKER_LOCAL, "STAMP_BROKER_LOCAL"),
        (BROKER_LOCAL_EU_CORRECTED, "STAMP_EU_CALENDAR_CORRECTED"),
    ],
)
def test_classifier_recovers_the_clock_it_was_given(tmp_path, basis, verdict):
    path = _write_csv(tmp_path / "SYN_H1.csv", _stamps_in(basis, *SPAN))
    result = AV.classify(path)
    assert result["verdict"] == verdict, result["reason"]
    assert result["hypotheses_passing"] == [
        {"STAMP_TRUE_UTC": AV.TRUE_UTC_H,
         "STAMP_BROKER_LOCAL": AV.BROKER_LOCAL_H,
         "STAMP_EU_CALENDAR_CORRECTED": AV.EU_CORRECTED}[verdict]
    ]


def test_classifier_refuses_a_span_that_cannot_discriminate(tmp_path):
    """Deep-winter-only bytes satisfy all three maps, so no verdict is earned."""
    span = (dt.date(2025, 4, 7), dt.date(2025, 6, 30))  # entirely outside any window
    path = _write_csv(tmp_path / "SHORT_H1.csv", _stamps_in(TRUE_UTC, *span))
    result = AV.classify(path)
    assert result["verdict"] == "REFUSE_SPAN_TOO_SHORT_TO_DISCRIMINATE"


def test_classifier_refuses_date_only_stamps(tmp_path):
    stamps = _true_utc_hourly_bars(*SPAN)[::24]
    path = _write_csv(tmp_path / "DATEONLY_D1.csv", stamps, fmt="%Y-%m-%d")
    assert AV.classify(path)["verdict"] == "REFUSE_DATE_ONLY_STAMPS"


def test_bounded_classifier_finds_the_prefix_and_bounds_it(tmp_path):
    """A file spliced from two captures is declared over its body and bounded before the seam."""
    body = _stamps_in(BROKER_LOCAL_EU_CORRECTED, dt.date(2024, 1, 1), dt.date(2025, 6, 30))
    tail_utc = _true_utc_hourly_bars(dt.date(2025, 7, 1), dt.date(2025, 12, 31))
    tail = [u + dt.timedelta(hours=3) for u in tail_utc]  # a different, wrong clock
    path = _write_csv(tmp_path / "SPLICED_H1.csv", sorted(body + tail))

    whole = AV.classify(path)
    assert whole["verdict"] == "REFUSE_UNRESOLVED"

    bounded = AV.classify_bounded(path)
    assert bounded["verdict"] == "STAMP_EU_CALENDAR_CORRECTED"
    assert bounded["bounded"] is True
    assert dt.date.fromisoformat(bounded["valid_through"]) < dt.date(2025, 7, 1)
    assert bounded["rows_outside_bound"] > 0


def test_bounded_bound_never_exceeds_the_first_seam(tmp_path):
    """The bisect is not monotone; the bound must come from the observed seam, not from it."""
    body = _stamps_in(BROKER_LOCAL, dt.date(2024, 1, 1), dt.date(2025, 6, 30))
    tail_utc = _true_utc_hourly_bars(dt.date(2025, 7, 1), dt.date(2025, 12, 31))
    path = _write_csv(tmp_path / "SPLICED2_H1.csv", sorted(body + tail_utc))
    bounded = AV.classify_bounded(path)
    if bounded.get("bounded"):
        seam = bounded["first_seam_week_over_whole_file"]
        assert seam is None or bounded["valid_through"] < seam


# --------------------------------------------------------------------------------------
# The third basis, end to end through the view layer
# --------------------------------------------------------------------------------------

def test_eu_corrected_round_trips_to_true_utc(tmp_path):
    utc = _true_utc_hourly_bars(*SPAN)
    stamps = _stamps_in(BROKER_LOCAL_EU_CORRECTED, *SPAN)
    path = _write_csv(tmp_path / "EU_H1.csv", stamps)
    write_sidecar(path, basis=BROKER_LOCAL_EU_CORRECTED, rule=None, evidence="synthetic")

    base = timebase_for(path)
    assert base.basis == BROKER_LOCAL_EU_CORRECTED
    assert base.needs_correction is True

    recovered = [row["time_utc"].replace(tzinfo=None) for row in read_bars(path)]
    assert recovered == utc


def test_eu_correction_is_a_one_hour_shift_only_inside_the_window():
    from src.utils.research_timebase import TimeBase

    tb = TimeBase(basis=BROKER_LOCAL_EU_CORRECTED, rule=None, source="test", evidence="")
    inside = dt.datetime(2025, 3, 20, 12, 0)
    outside = dt.datetime(2025, 1, 20, 12, 0)
    assert (inside - to_true_utc(inside, tb).replace(tzinfo=None)) == dt.timedelta(hours=1)
    assert (outside - to_true_utc(outside, tb).replace(tzinfo=None)) == dt.timedelta(0)


def test_write_sidecar_refuses_an_unknown_basis(tmp_path):
    path = _write_csv(tmp_path / "X_H1.csv", _true_utc_hourly_bars(*SPAN)[:100])
    with pytest.raises(ValueError, match="unrecognised time_column_basis"):
        write_sidecar(path, basis="vibes", rule=None, evidence="")


# --------------------------------------------------------------------------------------
# The declared validity window
# --------------------------------------------------------------------------------------

def test_read_bars_fails_closed_outside_the_declared_window(tmp_path):
    stamps = _true_utc_hourly_bars(dt.date(2024, 1, 1), dt.date(2024, 6, 30))
    path = _write_csv(tmp_path / "BOUND_H1.csv", stamps)
    write_sidecar(path, basis=TRUE_UTC, rule=None, evidence="synthetic",
                  valid_through=dt.date(2024, 3, 31))
    with pytest.raises(TimeBaseOutOfDeclaredRangeError):
        list(read_bars(path))


def test_csv_bar_source_drops_out_of_window_rows_and_says_so(tmp_path):
    stamps = _true_utc_hourly_bars(dt.date(2024, 1, 1), dt.date(2024, 6, 30))
    path = _write_csv(tmp_path / "BOUND2_H1.csv", stamps)
    write_sidecar(path, basis=TRUE_UTC, rule=None, evidence="synthetic",
                  valid_through=dt.date(2024, 3, 31))
    source = CsvBarSource({("SYN", 16385): path})
    rows = source.candles("SYN", 16385, 10_000, dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc))
    assert rows, "the in-window body must still load"
    assert max(r["time"] for r in rows)[:10] <= "2024-03-31"
    described = source.describe()["rows_dropped_outside_declared_timebase_window"]
    assert described["SYN:16385"] > 0, "a silent drop is the failure mode, not the fix"


# --------------------------------------------------------------------------------------
# The interop defect: "true_utc" is what the sanctioned writer emits, and CsvBarSource
# used to accept only "utc" --- so it fell through and corrected an already-UTC file.
# --------------------------------------------------------------------------------------

def test_csv_bar_source_does_not_double_correct_a_true_utc_sidecar(tmp_path):
    utc = _true_utc_hourly_bars(dt.date(2024, 1, 1), dt.date(2024, 3, 31))
    path = _write_csv(tmp_path / "UTC_H1.csv", utc)
    written = write_sidecar(path, basis=TRUE_UTC, rule=None, evidence="synthetic")
    assert json.loads(written.read_text())["time_column_basis"] == TRUE_UTC

    source = CsvBarSource({("SYN", 16385): path})
    rows = source.candles("SYN", 16385, 10_000, dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc))
    got = [dt.datetime.fromisoformat(r["time"]).replace(tzinfo=None) for r in rows]
    assert got == utc, "stamps declared true UTC must come back unmoved"


def test_csv_bar_source_reads_the_eu_corrected_basis(tmp_path):
    utc = _true_utc_hourly_bars(*SPAN)
    path = _write_csv(tmp_path / "EU2_H1.csv", _stamps_in(BROKER_LOCAL_EU_CORRECTED, *SPAN))
    write_sidecar(path, basis=BROKER_LOCAL_EU_CORRECTED, rule=None, evidence="synthetic")
    source = CsvBarSource({("SYN", 16385): path})
    rows = source.candles("SYN", 16385, 10 ** 6, dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
    got = [dt.datetime.fromisoformat(r["time"]).replace(tzinfo=None) for r in rows]
    assert got == utc


def test_csv_bar_source_refuses_an_unrecognised_basis(tmp_path):
    path = _write_csv(tmp_path / "BAD_H1.csv", _true_utc_hourly_bars(*SPAN)[:100])
    (Path(str(path) + ".timebase.json")).write_text(
        json.dumps({"time_column_basis": "eastern_standard_vibes"}), encoding="utf-8")
    source = CsvBarSource({("SYN", 16385): path})
    with pytest.raises(GenerationError, match="unrecognised time_column_basis"):
        source.candles("SYN", 16385, 10, dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc))


def test_csv_bar_source_still_corrects_a_broker_local_sidecar(tmp_path):
    """The pre-existing path must not move: this is the one every sealed archive uses."""
    utc = _true_utc_hourly_bars(dt.date(2024, 1, 1), dt.date(2024, 3, 31))
    path = _write_csv(tmp_path / "BL_H1.csv", _stamps_in(BROKER_LOCAL, dt.date(2024, 1, 1), dt.date(2024, 3, 31)))
    write_sidecar(path, basis=BROKER_LOCAL, rule=NEW_YORK_PLUS_7, evidence="synthetic",
                  server="FTMO-Server3")
    source = CsvBarSource({("SYN", 16385): path})
    rows = source.candles("SYN", 16385, 10 ** 6, dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc))
    got = [dt.datetime.fromisoformat(r["time"]).replace(tzinfo=None) for r in rows]
    assert got == utc


# --------------------------------------------------------------------------------------
# The control: a directory whose clock is independently established
# --------------------------------------------------------------------------------------

CONTROL_DIR = REPO / "data/historical_2026"


@pytest.mark.skipif(not CONTROL_DIR.is_dir(), reason="control archive not on this machine")
def test_control_directory_is_never_contradicted():
    """`data/historical_2026/` is FTMO broker-local, established by the exchange-anchor probe.

    The per-file probe is allowed to under-claim on it (a 24/7 instrument has no weekly
    rollover, a European index's Friday close moves with EU DST). It is NOT allowed to
    claim a DIFFERENT clock: that would be a false positive in the one direction F7 cannot
    tolerate.
    """
    verdicts = {}
    for path in sorted(CONTROL_DIR.glob("*.csv")):
        verdicts[path.name] = AV.classify(path)["verdict"]
    wrong = {k: v for k, v in verdicts.items()
             if v in ("STAMP_TRUE_UTC", "STAMP_EU_CALENDAR_CORRECTED")}
    assert not wrong, f"probe contradicted the established clock on {wrong}"
    assert sum(1 for v in verdicts.values() if v == "STAMP_BROKER_LOCAL") >= 40


@pytest.mark.skipif(not (REPO / "data/historical").is_dir(), reason="archive not on this machine")
def test_measured_verdicts_never_contradict_the_legacy_registry():
    """Where a directory IS registered, the per-file measurement must agree with it."""
    from src.utils.research_timebase import LEGACY_DECLARATIONS

    for dirname, (basis, _server, _evidence) in LEGACY_DECLARATIONS.items():
        d = REPO / "data" / dirname
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.csv"))[:12]:
            verdict = AV.classify(path)["verdict"]
            if not verdict.startswith("STAMP_"):
                continue
            expected = {"STAMP_TRUE_UTC": TRUE_UTC, "STAMP_BROKER_LOCAL": BROKER_LOCAL,
                        "STAMP_EU_CALENDAR_CORRECTED": BROKER_LOCAL_EU_CORRECTED}[verdict]
            assert expected == basis, f"{path} measured {expected}, registry says {basis}"

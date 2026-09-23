"""OD-AI-7's premise-reader, tested on synthetic worlds where the answer is known.

The reader decides whether a candle the engine dropped as forming was actually closed. It is
an input to changing what an ARMED book trades, so the properties that matter are the refusals:

  * it must say CONFIRMED only when a real closed bar sat in a slot the engine skipped;
  * it must say BENIGN when the market really was shut, and never confuse the two;
  * it must not reach CONFIRMED on confounded witnesses alone;
  * it must fail closed on missing fields, an unmeasured broker clock, or a missing archive;
  * it must convert bar epochs through `broker_clock`, because the archive is broker wall
    clock and a silent +7 h would move every slot comparison.

Each test builds its own packet file and its own one-symbol bar archive, so the assertions are
about the reader rather than about the 2026-07-25 export.
"""

from __future__ import annotations

import datetime as dt
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "pre_gap_bar_premise", REPO / "scripts/pre_gap_bar_premise.py")
PG = importlib.util.module_from_spec(_spec)
sys.modules["pre_gap_bar_premise"] = PG
_spec.loader.exec_module(PG)

from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

NS = "operator_profile"
H4 = 16388
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)


def _broker_epoch(at_utc: dt.datetime) -> int:
    """The inverse of what the reader does: UTC -> the raw MT5 epoch the archive stores."""
    naive = utc_to_broker_naive(at_utc, resolve_rule("FTMO-Server3"))
    return int((naive.replace(tzinfo=dt.timezone.utc) - EPOCH).total_seconds())


def _packets(tmp: Path, rows: list[dict]) -> Path:
    p = tmp / "packets.jsonl.gz"
    with gzip.open(p, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return p


def _archive(tmp: Path, symbol: str, tf_name: str, opens_utc: list[dt.datetime]) -> Path:
    d = tmp / "bars"
    d.mkdir(exist_ok=True)
    with gzip.open(d / f"FTMO_{symbol}_{tf_name}.csv.gz", "wt") as fh:
        fh.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
        for o in opens_utc:
            fh.write(f"{_broker_epoch(o)},1,2,0.5,1.5,10,0,0\n")
    return d


def _row(*, bar: dt.datetime, cycle: dt.datetime, symbol="GER40", tf=H4,
         event="unit_shadow", skip=None, sleeve="idxrev") -> dict:
    return {"namespace": NS, "symbol": symbol, "sleeve": sleeve, "timeframe": tf,
            "decision_bar_iso": bar.isoformat(), "created_at_utc": cycle.isoformat(),
            "event_type": event, "skip_reason": skip}


D = dt.datetime(2026, 6, 24, tzinfo=dt.timezone.utc)
BAR13 = D.replace(hour=13)
BAR17 = D.replace(hour=17)
CYCLE21 = D.replace(hour=21, minute=5)


def test_confirmed_when_a_closed_bar_sat_in_the_skipped_slot(tmp_path):
    """The live signature: cycle at 21:05 used the 13:00 bar, and a 17:00 bar exists."""
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21)])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    res = PG.analyse(*PG.read_observations([pk])[:1], PG.BarArchive(bars),
                     PG.DEFAULT_STALE_INTERVALS)
    assert res["verdict"] == "CONFIRMED"
    assert res["counts"]["confirmed_dropped_closed_bar"] == 1
    assert res["counts"]["confirmed_unconfounded"] == 1
    o = res["observations"][0]
    assert o["slots_with_a_real_closed_bar"] == [BAR17.isoformat()]
    assert o["witness"] == "UNCONFOUNDED"


def test_benign_when_the_market_really_was_shut(tmp_path):
    """Same 2-interval lag, no 17:00 bar in the archive: nothing was dropped."""
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21)])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13])
    res = PG.analyse(*PG.read_observations([pk])[:1], PG.BarArchive(bars),
                     PG.DEFAULT_STALE_INTERVALS)
    assert res["verdict"] == "REFUTED"
    assert res["counts"]["benign_market_was_shut"] == 1
    assert res["counts"]["confirmed_dropped_closed_bar"] == 0
    assert res["observations"][0]["slots_with_a_real_closed_bar"] == []


def test_a_normal_one_interval_lag_is_not_a_candidate_at_all(tmp_path):
    pk = _packets(tmp_path, [_row(bar=BAR17, cycle=CYCLE21)])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    res = PG.analyse(*PG.read_observations([pk])[:1], PG.BarArchive(bars),
                     PG.DEFAULT_STALE_INTERVALS)
    assert res["verdict"] == "SIGNATURE_ABSENT"
    assert res["counts"]["stale_candidates"] == 0


def test_confounded_witnesses_alone_cannot_reach_CONFIRMED(tmp_path):
    """A row the engine skipped on its placement ledger is a weaker witness, and the verdict
    says so rather than quietly counting it."""
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21, event="unit_skipped",
                                  skip="already_placed_this_bar")])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    res = PG.analyse(*PG.read_observations([pk])[:1], PG.BarArchive(bars),
                     PG.DEFAULT_STALE_INTERVALS)
    assert res["verdict"] == "CONFIRMED_CONFOUNDED_WITNESSES_ONLY"
    assert res["counts"]["confirmed_dropped_closed_bar"] == 1
    assert res["counts"]["confirmed_unconfounded"] == 0


def test_no_archive_is_unresolved_never_confirmed(tmp_path):
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21)])
    res = PG.analyse(*PG.read_observations([pk])[:1], None, PG.DEFAULT_STALE_INTERVALS)
    assert res["verdict"] == "SIGNATURE_PRESENT_BARS_UNAVAILABLE"
    assert res["counts"]["unresolved"] == 1
    assert res["observations"][0]["resolution"] == "UNRESOLVED_NO_ARCHIVE"


def test_a_missing_archive_file_is_reported_not_swallowed(tmp_path):
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21, symbol="NOSUCH")])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    arc = PG.BarArchive(bars)
    res = PG.analyse(*PG.read_observations([pk])[:1], arc, PG.DEFAULT_STALE_INTERVALS)
    assert res["counts"]["unresolved"] == 1
    assert any("NOSUCH" in m for m in res["archive_misses"]), res["archive_misses"]


def test_an_unmeasured_broker_clock_fails_closed(tmp_path):
    """A namespace with no registered server must yield UNRESOLVED, not a guessed offset."""
    rows = [{"namespace": "someone_elses_book", "symbol": "GER40", "sleeve": "idxrev",
             "timeframe": H4, "decision_bar_iso": BAR13.isoformat(),
             "created_at_utc": CYCLE21.isoformat(), "event_type": "unit_shadow"}]
    pk = _packets(tmp_path, rows)
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    res = PG.analyse(*PG.read_observations([pk])[:1], PG.BarArchive(bars),
                     PG.DEFAULT_STALE_INTERVALS)
    assert res["counts"]["confirmed_dropped_closed_bar"] == 0
    assert res["counts"]["unresolved"] == 1


def test_the_clock_conversion_is_real_and_a_utc_reading_would_break_it(tmp_path):
    """Guard the hazard: if the reader treated archive epochs as UTC, the 17:00 slot would not
    match and this CONFIRMED would silently become BENIGN."""
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21)])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    ok = PG.analyse(*PG.read_observations([pk])[:1], PG.BarArchive(bars),
                    PG.DEFAULT_STALE_INTERVALS)
    assert ok["verdict"] == "CONFIRMED"
    # The offset is genuinely non-zero, so the two readings are genuinely different.
    off = (_broker_epoch(BAR17) - int((BAR17 - EPOCH).total_seconds()))
    assert off != 0, "this test proves nothing if the broker clock happens to be UTC"


def test_missing_fields_are_counted_and_yield_INSUFFICIENT_FIELDS(tmp_path):
    pk = _packets(tmp_path, [
        {"namespace": NS, "created_at_utc": CYCLE21.isoformat()},               # no bar
        {"namespace": NS, "decision_bar_iso": BAR13.isoformat()},               # no cycle
        {"namespace": NS, "decision_bar_iso": BAR13.isoformat(),
         "created_at_utc": CYCLE21.isoformat()},                               # no timeframe
        {"namespace": NS, "decision_bar_iso": BAR13.isoformat(),
         "created_at_utc": CYCLE21.isoformat(), "timeframe": 999999},           # unknown tf
    ])
    obs, cov = PG.read_observations([pk])
    assert obs == []
    assert cov["rows_read"] == 4
    assert cov["no_decision_bar_iso"] == 1
    assert cov["no_created_at_utc"] == 1
    assert cov["no_timeframe"] == 1
    assert cov["unknown_timeframe"] == 1
    res = PG.analyse(obs, None, PG.DEFAULT_STALE_INTERVALS)
    assert res["verdict"] == "INSUFFICIENT_FIELDS"


def test_a_future_dated_decision_bar_is_counted_and_is_never_a_candidate(tmp_path):
    """`skip_reason: future_decision_bar_time` exists in the live stream (919 rows). A negative
    lag must not be read as a stale bar."""
    pk = _packets(tmp_path, [_row(bar=CYCLE21 + dt.timedelta(days=2), cycle=CYCLE21)])
    res = PG.analyse(*PG.read_observations([pk])[:1], None, PG.DEFAULT_STALE_INTERVALS)
    assert res["counts"]["future_dated_decision_bars"] == 1
    assert res["counts"]["stale_candidates"] == 0


@pytest.mark.parametrize("iv,tf", [(15, 15), (240, H4), (1440, 16408)])
def test_the_grid_walk_uses_the_bars_own_interval(iv, tf):
    bar = dt.datetime(2026, 6, 24, tzinfo=dt.timezone.utc)
    cycle = bar + dt.timedelta(minutes=iv * 3)
    slots = PG.last_provably_closed_open(cycle, bar, iv)
    assert slots == [bar + dt.timedelta(minutes=iv), bar + dt.timedelta(minutes=iv * 2)]
    assert PG.TF_MINUTES[tf] == iv


def test_cli_end_to_end_writes_json_and_exits_zero(tmp_path):
    pk = _packets(tmp_path, [_row(bar=BAR13, cycle=CYCLE21)])
    bars = _archive(tmp_path, "GER40", "H4", [BAR13, BAR17])
    out = tmp_path / "res.json"
    rc = PG.main(["--packets", str(pk), "--bars", str(bars), "-o", str(out)])
    assert rc == 0
    doc = json.loads(out.read_text())
    assert doc["verdict"] == "CONFIRMED"
    assert doc["decision"] == "OD-AI-7"
    assert doc["field_coverage"]["usable"] == 1
    # It must say what it cannot answer, including that existence is not value.
    assert any("PROFITABLE" in s for s in doc["what_this_cannot_answer"])
    assert "OFF" in doc["fails_closed"]


def test_cli_refuses_a_missing_packet_file(tmp_path):
    assert PG.main(["--packets", str(tmp_path / "nope.jsonl")]) == 2


def test_the_reader_imports_no_broker_module():
    """It runs on a research laptop against exported files. It must not be able to reach MT5."""
    src = (REPO / "scripts/pre_gap_bar_premise.py").read_text()
    for forbidden in ("import MetaTrader5", "mt5_real", "order_send", "RealMT5"):
        assert forbidden not in src, forbidden

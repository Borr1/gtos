from datetime import datetime, timezone

from src.judgment.challenge_shadow import challenge_as_of, score_deals
from src.judgment.hold_from_tape import classify_close, runner_score
from src.judgment.occupancy import (
    ISOLATED_REENTRY_MINUTES,
    occupancy_at,
    last_refusal_class,
    trades_from_dicts,
)


def _stamp(row):
    return challenge_as_of(row)


def test_occupancy_absent_tape_does_not_hardcode_crowded():
    occ = occupancy_at(
        None,
        symbol="XAUUSD",
        as_of_utc=datetime(2026, 9, 17, 7, 30, tzinfo=timezone.utc),
        kind="slate",
    )
    assert occ["symbol_open"] is None
    assert occ["occupancy_source"] == "deal_tape_absent"


def test_occupancy_from_challenge_deals_varies_by_symbol():
    trades = trades_from_dicts(
        [
            {
                "ticket": 293332188,
                "symbol": "XAUUSD",
                "sleeve": "dsp_two_bar_t",
                "open_time_utc": "2026-09-17T07:30:55Z",
                "open_time_server": "2026.09.17 10:30:55",
                "still_open": True,
                "_kind": "open",
            },
            {
                "ticket": 291072108,
                "symbol": "XAUUSD",
                "sleeve": "dsp_walked_hi",
                "open_time_utc": "2026-09-09T09:03:48+00:00",
                "open_time_server": "2026-09-09 09:03:48",
                "close_time_utc": "2026-09-09T10:14:01+00:00",
                "close_time_server": "2026-09-09 10:14:01",
                "still_open": False,
            },
        ],
        stamp=_stamp,
    )
    xau = occupancy_at(
        trades,
        symbol="XAUUSD",
        as_of_utc=datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc),
        this_ticket="slate-xau",
        kind="slate",
    )
    eurusd = occupancy_at(
        trades,
        symbol="EURUSD",
        as_of_utc=datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc),
        this_ticket="slate-eu",
        kind="slate",
    )
    assert xau["symbol_open"] is True
    assert eurusd["symbol_open"] is False
    assert eurusd["isolated_reentry_legal"] is True
    assert xau["minutes_since_flat"] is not None
    assert ISOLATED_REENTRY_MINUTES == 15.0


def test_corr_hold_true_when_cluster_sibling_open():
    trades = trades_from_dicts(
        [
            {
                "ticket": 10,
                "symbol": "US30.cash",
                "sleeve": "dsp_bleed_acc",
                "open_time_utc": "2026-09-09T11:00:00+00:00",
                "open_time_server": "2026-09-09 11:00:00",
                "close_time_utc": "2026-09-09T12:00:00+00:00",
                "close_time_server": "2026-09-09 12:00:00",
                "still_open": False,
            },
            {
                "ticket": 11,
                "symbol": "UK100.cash",
                "sleeve": "idxrev",
                "open_time_utc": "2026-09-09T11:10:00+00:00",
                "open_time_server": "2026-09-09 11:10:00",
                "still_open": True,
                "_kind": "open",
            },
        ],
        stamp=_stamp,
    )
    as_of = datetime(2026, 9, 9, 11, 30, tzinfo=timezone.utc)
    us30 = occupancy_at(trades, symbol="US30.cash", as_of_utc=as_of, this_ticket=10)
    xau = occupancy_at(trades, symbol="XAUUSD", as_of_utc=as_of, this_ticket="x")
    assert us30["corr_hold_named"] is True
    assert xau["corr_hold_named"] is False


def test_mfe_includes_overlapping_m15():
    from src.components.ultimate_book.primitives import Bar
    from src.judgment.bars import StampedBar
    from src.judgment.hold_from_tape import mfe_mae_r

    bar = StampedBar(
        broker_naive=datetime(2026, 9, 9, 10, 30),
        utc=datetime(2026, 9, 9, 7, 30, tzinfo=timezone.utc),
        bar=Bar(o=4400.0, h=4408.0, l=4398.0, c=4402.0, v=1),
        source_path="test",
    )
    mfe, mae = mfe_mae_r(
        [bar],
        side="short",
        entry=4401.15,
        stop_dist=5.74,
        open_utc=datetime(2026, 9, 9, 7, 30, 50, tzinfo=timezone.utc),
        close_utc=datetime(2026, 9, 9, 7, 40, 0, tzinfo=timezone.utc),
    )
    assert mfe is not None
    assert mae is not None
    assert mfe > 0


def test_last_refusal_none_only_after_search():
    assert last_refusal_class(None, symbol="XAUUSD", as_of_utc=None) is None
    assert last_refusal_class([], symbol="XAUUSD", as_of_utc=None) == "none"
    assert (
        last_refusal_class(
            [{"symbol": "XAUUSD", "reason": "native_limit_would_cross", "ts_utc": "2026-09-17T07:30:50Z"}],
            symbol="XAUUSD",
            as_of_utc=datetime(2026, 9, 17, 8, 0, tzinfo=timezone.utc),
        )
        == "other"
    )
    assert last_refusal_class(None, symbol="XAUUSD", as_of_utc=None, named="STRUCTURAL") == "other"


def test_classify_close_vnext_t_is_time_stop():
    assert classify_close("EXPERT|close_vnext_t") == "time_stop"
    assert classify_close("SL|[sl 4406.89]") == "orig_stop"
    assert classify_close("TP|[tp 0.85824]") == "broker_tp"
    assert runner_score(-1.0) == 0.0
    assert runner_score(0.4) == 1.0
    assert runner_score(2.0) == 2.0


def test_score_deals_builds_occupancy_without_inventing_two_stop():
    rows = score_deals(
        [
            {
                "ticket": 1,
                "symbol": "XAUUSD",
                "side": "SELL",
                "sleeve": "dsp_walked_hi",
                "entry": 4401.15,
                "orig_sl": 4406.89,
                "exit": 4407.07,
                "spread_at_entry": 0.45,
                "stop_dist": 5.74,
                "close_reason": "SL|[sl 4406.89]",
                "open_time_utc": "2026-09-09T09:03:48+00:00",
                "open_time_server": "2026-09-09 09:03:48",
                "close_time_utc": "2026-09-09T10:14:01+00:00",
                "close_time_server": "2026-09-09 10:14:01",
                "still_open": False,
            }
        ],
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
    )
    occ = rows[0]["state"]["occupancy"]
    # Own close is after as-of — label count is 0, not a leaked future stop.
    assert occ["same_sleeve_orig_stops_utc_day"] == 0
    assert occ["two_stop_exhausted"] is False
    assert occ["two_stop_source"] == "challenge_deals_label_not_count"
    assert occ["symbol_open"] is False
    assert occ["corr_hold_named"] is False
    fluid = rows[0]["compose"]["fluid"]["gates"]
    assert fluid["FLUID-HLD-001"]["shadow"] == "orig_stop"
    assert fluid["FLUID-HLD-002"]["decidable"] is True
    assert fluid["FLUID-HLD-002"]["shadow"] is False
    assert fluid["FLUID-HLD-003"]["decidable"] is True
    assert fluid["FLUID-HLD-003"]["shadow"] is False
    assert fluid["FLUID-PLC-001"]["decidable"] is True
    assert fluid["FLUID-PLC-001"]["shadow"] is False

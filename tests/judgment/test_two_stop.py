from datetime import datetime, timezone

from src.judgment.two_stop import (
    F5_SAME_SLEEVE_ORIG_STOP_DAY_CAP,
    closed_rows,
    legacy_symbol_keys,
    occupancy_from_closed,
    same_sleeve_orig_stop_count_session_day,
    two_stop_exhausted,
)


def _doc():
    return {
        "updated_utc": "2026-09-17T09:48:46.927338+00:00",
        "updated_ict": "2026-09-08 21:13 ICT",
        "XAUUSD": {"closed_utc": "2026-09-08T06:12:34Z", "ticket": 182187173},
        "US30.cash": {"closed_utc": "2026-09-08T14:02:20Z", "ticket": 182380951},
        "EURGBP": {"closed_utc": "2026-09-03T11:46:50Z", "ticket": 181134535},
        "closed": [
            {
                "ticket": 293362731,
                "symbol": "BTCUSD",
                "sleeve": "kz_london_cry",
                "closed_utc": "2026-09-17T09:48:46Z",
                "exit_class": "orig_stop",
            },
            {
                "ticket": 1,
                "symbol": "XAUUSD",
                "sleeve": "dsp_two_bar_t",
                "closed_utc": "2026-09-17T08:00:00Z",
                "exit_class": "orig_stop",
            },
            {
                "ticket": 2,
                "symbol": "XAUUSD",
                "sleeve": "dsp_two_bar_t",
                "closed_utc": "2026-09-17T09:00:00Z",
                "exit_class": "orig_stop",
            },
            {
                "ticket": 3,
                "symbol": "XAUUSD",
                "sleeve": "dsp_two_bar_t",
                "closed_utc": "2026-09-16T22:00:00Z",
                "exit_class": "orig_stop",
            },
        ],
    }


def test_reads_closed_only_ignores_legacy_0908_keys():
    doc = _doc()
    assert F5_SAME_SLEEVE_ORIG_STOP_DAY_CAP == 2
    assert len(closed_rows(doc)) == 4
    assert "XAUUSD" in legacy_symbol_keys(doc)
    assert "US30.cash" in legacy_symbol_keys(doc)
    assert same_sleeve_orig_stop_count_session_day(
        doc, sleeve="dsp_two_bar_t", session_day="2026-09-17"
    ) == 2
    assert same_sleeve_orig_stop_count_session_day(
        doc, sleeve="dsp_two_bar_t", session_day="2026-09-08"
    ) == 0
    assert two_stop_exhausted(doc, sleeve="dsp_two_bar_t", session_day="2026-09-17") is True
    occ = occupancy_from_closed(
        doc,
        sleeve="dsp_two_bar_t",
        as_of_utc=datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc),
    )
    assert occ["same_sleeve_orig_stops_utc_day"] == 2
    assert occ["two_stop_exhausted"] is True
    assert occ["two_stop_source"] == "closed[]"


def test_absent_doc_does_not_invent_stops():
    occ = occupancy_from_closed(
        None,
        sleeve="dsp_two_bar_t",
        as_of_utc=datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc),
    )
    assert occ["same_sleeve_orig_stops_utc_day"] is None
    assert occ["two_stop_exhausted"] is None
    assert occ["two_stop_source"] == "closed_absent"


def test_as_of_excludes_later_same_day_stops():
    doc = _doc()
    n = same_sleeve_orig_stop_count_session_day(
        doc,
        sleeve="dsp_two_bar_t",
        session_day="2026-09-17",
        as_of_utc=datetime(2026, 9, 17, 8, 30, tzinfo=timezone.utc),
    )
    assert n == 1


def test_closed_doc_from_deals_is_label_not_count():
    from src.judgment.challenge_shadow import challenge_as_of
    from src.judgment.two_stop import closed_doc_from_deals

    doc = closed_doc_from_deals(
        [
            {
                "ticket": 1,
                "symbol": "XAUUSD",
                "sleeve": "dsp_walked_hi",
                "close_reason": "SL|[sl 1]",
                "open_time_utc": "2026-09-09T09:03:48+00:00",
                "open_time_server": "2026-09-09 09:03:48",
                "close_time_utc": "2026-09-09T10:14:01+00:00",
                "close_time_server": "2026-09-09 10:14:01",
                "still_open": False,
            },
            {
                "ticket": 2,
                "symbol": "XAUUSD",
                "sleeve": "dsp_walked_hi",
                "close_reason": "EXPERT|close_vnext_time_stop",
                "open_time_utc": "2026-09-09T11:00:00+00:00",
                "open_time_server": "2026-09-09 11:00:00",
                "close_time_utc": "2026-09-09T12:00:00+00:00",
                "close_time_server": "2026-09-09 12:00:00",
                "still_open": False,
            },
        ],
        stamp=challenge_as_of,
    )
    assert doc is not None
    assert doc["two_stop_source"] == "challenge_deals_label_not_count"
    assert doc["n_closed"] == 1
    occ = occupancy_from_closed(
        doc,
        sleeve="dsp_walked_hi",
        as_of_utc=datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc),
    )
    assert occ["same_sleeve_orig_stops_utc_day"] == 1
    assert occ["two_stop_exhausted"] is False

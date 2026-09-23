from datetime import datetime, timezone
from pathlib import Path

from src.judgment.a1_log import a1_enabled, maybe_observe_ub_plc_017, observe_sel_v4_002
from src.judgment.bars import (
    books_for_symbol,
    challenge_tape_present,
    landed_challenge_symbols,
    load_challenge_books,
    load_ohlc_csv,
)
from src.judgment.challenge_shadow import (
    challenge_as_of,
    is_slate_pointer,
    score_deals,
    score_position,
    score_slate,
)
from src.judgment.compose import TILT_MAX, TILT_MIN, flow_alignment_size_tilt
from src.judgment.process_lock import WIRE_COST
from src.judgment.bars import CHALLENGE_BAR_DIR
from tests.judgment.cages import assert_live_cages


def test_open_ticket_scores_without_place():
    row = score_position(
        {
            "ticket": 293332188,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "dsp_two_bar_t",
            "entry": 4331.45,
            "orig_sl": 4336.9,
            "tp": 4288.19,
            "stop_dist": 5.45,
            "spread_R": 0.080734,
            "open_time_utc": "2026-09-17T07:30:55Z",
            "_kind": "open",
        },
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={"bal": 95348.42, "eq": 95920.82, "to_pass": 14651.58},
    )
    assert_live_cages(row["compose"], ticket=293332188)
    assert row["ticket"] == 293332188
    assert row["house"]["family_class"] == "study"
    assert row["house"]["leave_orig"] is True
    assert row["state"]["completeness"]["state_sufficient_for_live"] is False
    assert "timeframes.m15" in row["missing_state"]
    assert row["compose"]["disposition"] == "log_only"
    # Missing tape must not invent a refuse fence. Leave-orig live stays 1.0.
    assert row["compose"]["size_tilt"] == 1.0
    assert row["compose"]["live_size_tilt"] == 1.0
    assert row["compose"]["shadow_size_tilt"] == 1.0
    assert row["compose"]["shadow_cost_tilt"] == 0.7578
    assert row["compose"]["live_cost_tilt"] == 1.0
    assert row["compose"]["wires"][WIRE_COST]["cannot_refuse"] is True
    assert row["house"]["leave_orig"] is True
    assert row["compose"]["leave_orig"] is True
    assert row["compose"]["process_lock"] == "shadow_score_then_wire"
    assert row["compose"]["apply_this_row"] is False


def test_tilt_cannot_zero_or_explode():
    assert flow_alignment_size_tilt(0) == TILT_MIN
    assert flow_alignment_size_tilt(2) == TILT_MAX
    assert flow_alignment_size_tilt(None) == 1.0
    assert TILT_MIN > 0


def test_a1_off_does_not_write_and_does_not_raise():
    assert a1_enabled() is False
    class _I:
        symbol = "XAUUSD"
        sleeve = "metals_core"
        stop_dist = 5.0
    class _T:
        bid = 1.0
        ask = 1.01
    maybe_observe_ub_plc_017(_I(), _T(), None)  # must be a no-op
    row = observe_sel_v4_002({"foo": 1})
    assert row["skipped"] == "GTOS_JEV_A1_LOG_off"
    assert row["never_place"] is True


def test_score_slate_logs_without_place():
    empty = score_slate(
        {"slate_id": "x", "candidates": []},
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
    )
    assert empty == []
    rows = score_slate(
        {
            "slate_id": "abc",
            "candidates": [
                {
                    "candidate_id": "c1",
                    "symbol": "XAUUSD",
                    "side": "short",
                    "sleeve": "dsp_two_bar_t",
                    "entry": 4331.45,
                    "sl": 4336.9,
                    "tp": 4288.19,
                }
            ],
        },
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
    )
    assert len(rows) == 1
    assert rows[0]["kind"] == "slate"
    assert_live_cages(rows[0]["compose"])
    assert rows[0]["house"]["leave_orig"] is False
    # No tape + no spread → both shadows 1.0, live 1.0 even in APPLY era.
    assert rows[0]["compose"]["size_tilt"] == 1.0


def test_slate_pointer_does_not_invent_candidates():
    pointer = {
        "built_at_utc": "2026-09-17T10:26:06.607697+00:00",
        "fingerprint": "04181efb34725738",
        "path": "C:\\\\Users\\\\Administrator\\\\redacted_host\\\\repo\\\\pipeline_state\\\\ultimate_book\\\\operator\\\\judgment\\\\slates\\\\slate_20260917T102606Z_21a8b9034f43e82a.json",
        "slate_id": "21a8b9034f43e82a",
    }
    assert is_slate_pointer(pointer) is True
    rows = score_slate(pointer, books={}, spines={"spine_id": None, "sources": [], "events": [], "n_files": 0})
    assert len(rows) == 1
    assert rows[0]["kind"] == "slate_pointer"
    assert rows[0]["body_present"] is False
    assert rows[0]["compose"]["live_size_tilt"] == 1.0
    assert rows[0]["house"]["leave_orig"] is True
    assert "do not invent" in rows[0]["diagnosis"]


def test_challenge_as_of_trusts_corrected_sit_and_rewinds_same_clock_deals():
    sit = challenge_as_of(
        {
            "open_time_utc": "2026-09-17T07:30:55Z",
            "open_time_server": "2026.09.17 10:30:55",
        }
    )
    assert sit == datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc)
    deal = challenge_as_of(
        {
            "open_time_utc": "2026-09-17T10:30:55+00:00",
            "open_time_server": "2026-09-17 10:30:55",
        }
    )
    assert deal == datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc)
    slate = challenge_as_of({"direction": "SHORT", "last_seen_utc": "2026-09-17T07:45:39+00:00"})
    assert slate == datetime(2026, 9, 17, 7, 45, 39, tzinfo=timezone.utc)
    # Host last_seen carries microseconds. Dot-smash used to invent now().
    slate_us = challenge_as_of(
        {"direction": "SHORT", "last_seen_utc": "2026-09-17T07:45:39.416839+00:00"}
    )
    assert slate_us == datetime(2026, 9, 17, 7, 45, 39, 416839, tzinfo=timezone.utc)


def test_challenge_tape_is_true_utc_and_covers_ticket_open():
    m15 = load_ohlc_csv(CHALLENGE_BAR_DIR / "XAUUSD_M15.csv")
    assert m15, "Challenge M15 must be landed"
    src = Path(m15[0].source_path)
    assert src.name == "XAUUSD_M15.csv"
    assert "\\" not in m15[0].source_path
    assert src.as_posix().endswith("challenge_shadow_20260917/XAUUSD_M15.csv")
    # Chair 2026-09-18 refresh: time_utc already −3h, not NY+7-shifted.
    assert m15[0].utc == datetime(2026, 8, 19, 8, 0, tzinfo=timezone.utc)
    assert m15[0].broker_naive.hour == 11
    assert m15[-1].utc == datetime(2026, 9, 18, 4, 15, tzinfo=timezone.utc)
    assert len(m15) == 2000
    books = load_challenge_books()
    row = score_position(
        {
            "ticket": 293332188,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "dsp_two_bar_t",
            "entry": 4331.45,
            "orig_sl": 4336.9,
            "tp": 4288.19,
            "stop_dist": 5.45,
            "spread_R": 0.080734,
            "open_time_utc": "2026-09-17T07:30:55Z",
            "open_time_server": "2026.09.17 10:30:55",
            "_kind": "open",
        },
        books=books,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={},
    )
    assert row["state"]["completeness"]["state_sufficient_for_live"] is True
    assert row["state"]["timeframes"]["m15"]["last_utc"] == "2026-09-17T07:30:00Z"
    assert row["compose"]["live_size_tilt"] == 1.0
    assert row["compose"]["apply_this_row"] is False
    assert row["house"]["leave_orig"] is True


def test_deal_cost_uses_spread_over_stop_not_cost_R_label():
    rows = score_deals(
        [
            {
                "ticket": 1,
                "symbol": "XAUUSD",
                "side": "SELL",
                "sleeve": "dsp_walked_hi",
                "entry": 4401.15,
                "orig_sl": 4406.89,
                "tp": 4363.56,
                "spread_at_entry": 0.45,
                "stop_dist": 5.74,
                "cost_R": 0.0107,
                "open_time_utc": "2026-09-09T09:03:48+00:00",
                "open_time_server": "2026-09-09 09:03:48",
                "still_open": False,
            }
        ],
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        skip_tickets={"293332188"},
    )
    assert len(rows) == 1
    spread_r = rows[0]["state"]["cost"]["spread_r_of_stop"]
    assert abs(spread_r - (0.45 / 5.74)) < 1e-9
    assert rows[0]["compose"]["shadow_cost_tilt"] != 1.0
    assert rows[0]["compose"]["live_cost_tilt"] == rows[0]["compose"]["shadow_cost_tilt"]
    assert rows[0]["compose"]["live_cost_tilt"] <= 1.0
    assert rows[0]["house"]["leave_orig"] is False


def test_score_deals_skips_only_named_tickets():
    deals = [
        {"ticket": 293332188, "symbol": "XAUUSD", "side": "SELL", "sleeve": "dsp_two_bar_t", "still_open": True},
        {
            "ticket": 292667008,
            "symbol": "XAUUSD",
            "side": "BUY",
            "sleeve": "dsp_three_fre",
            "entry": 4276.91,
            "orig_sl": 4270.0,
            "spread_at_entry": 0.45,
            "stop_dist": 6.91,
            "open_time_utc": "2026-09-15T15:30:52+00:00",
            "open_time_server": "2026-09-15 15:30:52",
            "still_open": False,
        },
    ]
    rows = score_deals(
        deals,
        books={},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        skip_tickets={"293332188"},
    )
    assert [r["ticket"] for r in rows] == [292667008]
    assert rows[0]["state"]["cost"]["spread_r_of_stop"] is not None


def test_non_xau_does_not_wear_xau_tape():
    xau = load_challenge_books()
    xau_close = xau["m15"][-1].bar.c
    assert challenge_tape_present("XAUUSD") is True
    assert books_for_symbol("XAUUSD", xau) is xau
    gbp = books_for_symbol("GBPUSD", xau)
    assert gbp is not xau
    row = score_position(
        {
            "ticket": 1,
            "symbol": "GBPUSD",
            "side": "long",
            "sleeve": "vss_fxcross_london_up_low",
            "entry": 1.34,
            "orig_sl": 1.338,
            "open_time_utc": "2026-09-17T07:30:55Z",
            "_kind": "slate",
        },
        books=xau,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={},
    )
    if challenge_tape_present("GBPUSD"):
        assert gbp is not None
        assert "GBPUSD" in gbp["m15"][-1].source_path or gbp["m15"][-1].bar.c != xau_close
        assert "timeframes.m15" not in row["missing_state"]
        assert row["state"]["completeness"]["timeframes_m15_h4"] is True
    else:
        assert gbp is None
        assert "GBPUSD" not in landed_challenge_symbols()
        assert "timeframes.m15" in row["missing_state"]
        assert row["state"]["completeness"]["timeframes_m15_h4"] is False
        assert "GBPUSD" in row["diagnosis"]
    assert row["state"]["identity"]["symbol"] == "GBPUSD"


def test_slate_xau_live_moves_except_leave_orig_ticket():
    books = load_challenge_books()
    slate = score_position(
        {
            "ticket": 292667008,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "dsp_two_bar_t",
            "entry": 4331.45,
            "orig_sl": 4336.9,
            "tp": 4288.19,
            "stop_dist": 5.45,
            "spread_R": 0.080734,
            "open_time_utc": "2026-09-17T07:30:55Z",
            "open_time_server": "2026.09.17 10:30:55",
            "_kind": "slate",
        },
        books=books,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={},
    )
    assert slate["house"]["leave_orig"] is False
    assert slate["state"]["completeness"]["state_sufficient_for_live"] is True
    assert slate["compose"]["apply_this_row"] is True
    assert slate["compose"]["disposition"] == "named_apply"
    assert slate["compose"]["live_size_tilt"] != 1.0 or slate["compose"]["live_cost_tilt"] != 1.0
    assert slate["compose"]["live_cost_tilt"] <= 1.0
    assert_live_cages(slate["compose"])
    held = score_position(
        {
            "ticket": 293332188,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "dsp_two_bar_t",
            "entry": 4331.45,
            "orig_sl": 4336.9,
            "tp": 4288.19,
            "stop_dist": 5.45,
            "spread_R": 0.080734,
            "open_time_utc": "2026-09-17T07:30:55Z",
            "_kind": "slate",
        },
        books=books,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={},
    )
    assert held["house"]["leave_orig"] is True
    assert held["compose"]["live_size_tilt"] == 1.0
    assert held["compose"]["live_cost_tilt"] == 1.0


def test_slate_without_last_seen_uses_built_at_not_now():
    """Frozen slate clock. Re-score a day later must not wear now() onto M15 lag."""
    books = load_challenge_books()
    rows = score_slate(
        {
            "built_at_utc": "2026-09-17T10:41:05.126377+00:00",
            "candidates": [
                {
                    "candidate_id": "W7_BOOK::dsp_c_walkhigh::XAUUSD::2026-09-17::SHORT::dsp_walked_high_accepted_through",
                    "symbol": "XAUUSD",
                    "direction": "SHORT",
                    "sleeve": "dsp_walked_high_accepted_through",
                }
            ],
        },
        books={"XAUUSD": books},
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
    )
    assert len(rows) == 1
    clock = rows[0]["state"]["clock"]["as_of_utc"]
    assert clock.startswith("2026-09-17T10:41:05")
    assert not clock.startswith("2026-09-18")
    assert rows[0]["state"]["completeness"]["timeframes_m15_h4"] is True

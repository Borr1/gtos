from __future__ import annotations

from src.research_infra.candidate_path_contract import (
    ACTION_REQUIRED,
    COMPLETE_WITH_LIMITATIONS,
    build_candidate_path_contract_row,
)


def _path(**overrides):
    row = {
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "bars_elapsed": 4,
        "min_low": 101.0,
        "max_high": 104.0,
        "trade_parameters": {"direction": "LONG", "entry_price": 100, "stop_loss": 98, "take_profit_1": 103},
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_no_entry_touch_tp_area_is_documented_not_fill():
    row = build_candidate_path_contract_row(
        1,
        _path(),
        generated_at_utc="2026-05-05T00:00:00+00:00",
        ltf_row={"tp1_first_touch_utc": "2026-05-04T07:30:00+00:00", "ltf_status": "M1_PATH_RECOVERED"},
    )

    assert row["path_contract_status"] == COMPLETE_WITH_LIMITATIONS
    assert row["path_ambiguity_status"] == "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL"
    assert row["first_touch_times"]["tp1_first_touch_utc"] == "2026-05-04T07:30:00+00:00"
    assert row["tick_order_claim_status"] == "LOWER_TF_M1_ORDER_OBSERVED"


def test_same_m15_tp_sl_ambiguity_preserves_no_tick_claim():
    row = build_candidate_path_contract_row(
        1,
        _path(path_label="entry_touched_tp_and_sl_m15_ambiguous", touched_entry=True, hit_tp1=True, hit_sl=True),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["path_contract_status"] == COMPLETE_WITH_LIMITATIONS
    assert row["path_ambiguity_status"] == "M15_TP1_SL_ORDER_AMBIGUOUS_NO_TICK_ORDER_CLAIM"
    assert row["tick_order_claim_status"] == "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY"


def test_path_label_geometry_conflict_is_action_required():
    row = build_candidate_path_contract_row(
        1,
        _path(path_label="entry_touched_then_reached_tp1", touched_entry=False),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert row["path_contract_status"] == ACTION_REQUIRED
    assert "PATH_LABEL_TOUCH_CONFLICT" in row["action_required_codes"]

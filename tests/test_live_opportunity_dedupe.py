from __future__ import annotations

from src.research_infra.live_opportunity_dedupe import (
    build_opportunity_index,
    candidate_lifecycle_signature,
    candidate_level_key,
    candidate_setup_signature,
)


def _candidate(
    candidate_id: str,
    decision_time_utc: str,
    *,
    symbol: str = "XAGUSD",
    side: str = "SHORT",
    framework: str = "ob_retest",
    entry: float = 75.471,
    sl: float = 75.971,
    tp1: float = 74.721,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "broker_symbol": symbol,
        "side": side,
        "framework": framework,
        "decision_time_utc": decision_time_utc,
        "trade_parameters": {
            "direction": side,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit_1": tp1,
        },
    }


def _ltf(candidate_id: str, *, entry_touch: str | None = None, tp: str | None = None) -> dict:
    return {
        "candidate_id": candidate_id,
        "asof_latest_candle_utc": "2026-05-04T08:15:00+00:00",
        "entry_first_touch_utc": entry_touch,
        "tp1_first_touch_utc": tp,
        "sl_first_touch_utc": None,
        "terminal_outcome_status": "ENTRY_THEN_TP1" if entry_touch and tp else "NO_ENTRY_TOUCH_BY_LTF_ASOF",
        "terminal_event_utc": tp if entry_touch and tp else None,
        "path_order_label": "entry_then_tp1_before_sl" if entry_touch and tp else "no_entry_touch_by_ltf_asof",
    }


def test_setup_signature_separates_level_from_full_geometry():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")

    assert candidate_level_key(candidate) == "XAGUSD|SHORT|ob_retest|entry=75.471"
    assert candidate_setup_signature(candidate).endswith("|sl=75.971|tp1=74.721")
    assert candidate_lifecycle_signature({**candidate, "session": "london"}).startswith(
        "XAGUSD|session=london|side=SHORT|framework=ob_retest"
    )


def test_consecutive_same_setup_before_terminal_is_one_opportunity():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00")
    second = _candidate("c2", "2026-05-04T07:30:00+00:00")

    index = build_opportunity_index(
        [first, second],
        latest_ltf={
            "c1": _ltf("c1", entry_touch="2026-05-04T07:40:00+00:00", tp="2026-05-04T07:50:00+00:00")
        },
    )

    assert index["c1"]["opportunity_id"] == index["c2"]["opportunity_id"]
    assert index["c1"]["opportunity_duplicate_status"] == "PRIMARY_UNIQUE_OPPORTUNITY"
    assert index["c2"]["opportunity_duplicate_status"] == "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP"
    assert index["c2"]["opportunity_counting_status"] == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"
    assert index["c2"]["opportunity_lifecycle_state"] == "DUPLICATE_ACTIVE_SETUP"
    assert index["c1"]["opportunity_candidate_count"] == 2


def test_same_setup_after_prior_terminal_can_start_new_opportunity():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00")
    second = _candidate("c2", "2026-05-04T07:30:00+00:00")
    third = _candidate("c3", "2026-05-04T08:00:00+00:00")

    index = build_opportunity_index(
        [first, second, third],
        latest_ltf={
            "c1": _ltf("c1", entry_touch="2026-05-04T07:35:00+00:00", tp="2026-05-04T07:50:00+00:00")
        },
    )

    assert index["c1"]["opportunity_id"] == index["c2"]["opportunity_id"]
    assert index["c3"]["opportunity_id"] != index["c1"]["opportunity_id"]
    assert index["c3"]["opportunity_duplicate_status"] == "PRIMARY_UNIQUE_OPPORTUNITY"
    assert index["c3"]["opportunity_counting_status"] == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    assert index["c3"]["opportunity_lifecycle_state"] == "REOPENED_AFTER_TERMINAL"


def test_no_entry_tp_area_move_does_not_reset_as_trade_happened():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00")
    second = _candidate("c2", "2026-05-04T08:00:00+00:00")
    path = {
        "candidate_id": "c1",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "asof_latest_candle_utc": "2026-05-04T07:45:00+00:00",
    }

    index = build_opportunity_index([first, second], latest_paths={"c1": path})

    assert index["c1"]["opportunity_id"] == index["c2"]["opportunity_id"]
    assert index["c2"]["opportunity_duplicate_status"] == "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP"
    assert index["c2"]["opportunity_counting_status"] == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"


def test_tp_before_entry_does_not_reset_until_post_entry_terminal():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00", symbol="NAS100", side="LONG", entry=100.0, sl=90.0, tp1=110.0)
    second = _candidate("c2", "2026-05-04T07:30:00+00:00", symbol="NAS100", side="LONG", entry=100.0, sl=90.0, tp1=110.0)

    index = build_opportunity_index(
        [first, second],
        latest_ltf={
            "c1": {
                "candidate_id": "c1",
                "entry_first_touch_utc": "2026-05-04T13:02:00+00:00",
                "tp1_first_touch_utc": "2026-05-04T07:35:00+00:00",
                "sl_first_touch_utc": None,
                "terminal_outcome_status": "ENTRY_TOUCHED_UNRESOLVED_BY_LTF_ASOF",
                "terminal_event_utc": None,
            }
        },
    )

    assert index["c1"]["opportunity_id"] == index["c2"]["opportunity_id"]
    assert index["c2"]["opportunity_counting_status"] == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"


def test_post_entry_sl_terminal_resets_same_setup():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00", symbol="NAS100", side="LONG", entry=100.0, sl=90.0, tp1=110.0)
    second = _candidate("c2", "2026-05-04T14:00:00+00:00", symbol="NAS100", side="LONG", entry=100.0, sl=90.0, tp1=110.0)

    index = build_opportunity_index(
        [first, second],
        latest_ltf={
            "c1": {
                "candidate_id": "c1",
                "entry_first_touch_utc": "2026-05-04T13:02:00+00:00",
                "tp1_first_touch_utc": "2026-05-04T07:35:00+00:00",
                "sl_first_touch_utc": "2026-05-04T13:04:00+00:00",
                "terminal_outcome_status": "ENTRY_THEN_SL",
                "terminal_event_utc": "2026-05-04T13:04:00+00:00",
            }
        },
    )

    assert index["c2"]["opportunity_id"] != index["c1"]["opportunity_id"]
    assert index["c2"]["opportunity_counting_status"] == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"


def test_same_entry_different_side_or_framework_is_not_merged():
    long_ob = _candidate("c1", "2026-05-04T07:15:00+00:00", side="LONG")
    short_ob = _candidate("c2", "2026-05-04T07:30:00+00:00", side="SHORT")
    short_breaker = _candidate("c3", "2026-05-04T07:45:00+00:00", side="SHORT", framework="breaker_re_entry")

    index = build_opportunity_index([long_ob, short_ob, short_breaker])

    assert len({row["opportunity_id"] for row in index.values()}) == 3


def test_near_level_duplicate_is_collapsed_until_terminal_reset():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00", entry=75.471, sl=75.971, tp1=74.721)
    drifted = _candidate("c2", "2026-05-04T07:30:00+00:00", entry=75.472, sl=75.972, tp1=74.72)

    index = build_opportunity_index([first, drifted])

    assert index["c1"]["opportunity_id"] == index["c2"]["opportunity_id"]
    assert index["c2"]["opportunity_duplicate_status"] == "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP"
    assert index["c2"]["opportunity_counting_status"] == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"
    assert index["c2"]["opportunity_similarity"]["entry_delta"] == 0.001
    assert index["c2"]["opportunity_similarity"]["materially_same_setup"] is True


def test_materially_different_level_is_not_collapsed():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00", entry=75.471, sl=75.971, tp1=74.721)
    far = _candidate("c2", "2026-05-04T07:30:00+00:00", entry=75.60, sl=76.10, tp1=74.85)

    index = build_opportunity_index([first, far])

    assert index["c1"]["opportunity_id"] != index["c2"]["opportunity_id"]
    assert index["c2"]["opportunity_lifecycle_state"] == "NEW_AFTER_COOLDOWN"


def test_same_symbol_new_level_is_counting_blocked_when_prior_trade_is_open():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00", entry=75.471, sl=75.971, tp1=74.721)
    different_level = _candidate("c2", "2026-05-04T07:45:00+00:00", entry=75.60, sl=76.10, tp1=74.85)

    index = build_opportunity_index(
        [first, different_level],
        latest_ltf={
            "c1": _ltf("c1", entry_touch="2026-05-04T07:35:00+00:00", tp=None)
        },
    )

    assert index["c1"]["opportunity_id"] != index["c2"]["opportunity_id"]
    assert index["c2"]["opportunity_duplicate_status"] == "PRIMARY_UNIQUE_OPPORTUNITY"
    assert index["c2"]["opportunity_counting_status"] == "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP"
    assert index["c2"]["opportunity_lifecycle_state"] == "BLOCKED_SAME_SYMBOL_OVERLAP"
    assert index["c2"]["same_symbol_overlap_status"] == "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE"

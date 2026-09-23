from types import SimpleNamespace

from src.components.expired_poi_watch import (
    archive_expired_pending_intent,
    build_expired_poi_watch,
    evaluate_and_log_active_watches,
    evaluate_expired_poi_watch,
    load_active_watches,
    should_archive_cancel_reason,
    watch_registry_path,
)


def _config() -> dict:
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"min_rr": 1.5, "sl_absolute_min": 5.0},
        "expired_poi_watch": {
            "enabled": True,
            "mode": "shadow",
            "max_watch_hours": 72,
            "approach_threshold_r": 0.25,
            "min_rearm_rr": 1.5,
            "require_kill_zone_for_rearm": True,
            "execution_override_enabled": False,
            "archive_cancel_reasons": ["new_day", "48h clock expiry", "expired_48h"],
        },
    }


def _record() -> dict:
    return {
        "metadata": {
            "symbol": "XAUUSD",
            "kill_zone": "london",
            "candle_time": "2026-05-05T08:15:00+00:00",
            "candle_close_utc": "2026-05-05T08:15:00+00:00",
        },
        "decision_pipeline": {
            "ai_grade": "A+",
            "ai_direction": "SHORT",
            "ai_framework": "ob_retest",
            "final_outcome": "LIMIT_PLACED",
            "level2_verification": {
                "passed": True,
                "checks": [
                    {
                        "name": "h1_poi_exists",
                        "status": "PASS",
                        "mso_value": {"zone": "4668.45-4675.72"},
                    }
                ],
            },
        },
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": 4668.45,
            "stop_loss": 4679.89,
            "take_profit_1": 4651.28,
        },
        "limit_intent": {
            "trade_id": "lim_XAUUSD_2026-05-05_081526",
            "limit_price": 4668.45,
            "stop_loss": 4679.89,
            "take_profit_1": 4651.28,
        },
    }


def _intent() -> SimpleNamespace:
    return SimpleNamespace(
        direction="SHORT",
        limit_price=4668.45,
        stop_loss=4679.89,
        take_profit_1=4651.28,
        trade_id="lim_XAUUSD_2026-05-05_081526",
        placed_time="2026-05-05T08:15:26.485637+00:00",
        candidate_id="XAUUSD_2026-05-05T08:15:00+00:00",
        decision_time_utc="2026-05-05T08:15:00+00:00",
        source_symbol="XAUUSD",
        session="london",
        kill_zone="london",
    )


def test_new_day_cancel_is_watch_eligible_but_drawdown_cancel_is_not():
    assert should_archive_cancel_reason("new_day", _config()) is True
    assert should_archive_cancel_reason("portfolio_drawdown_stop", _config()) is False


def test_archive_expired_pending_intent_persists_structural_watch(tmp_path):
    watch = archive_expired_pending_intent(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
        record_path="knowledge_base/trade_records/XAUUSD/2026-05-05_london_0815.json",
        registry_dir=tmp_path,
    )

    assert watch is not None
    assert watch["status"] == "ACTIVE_WATCH"
    assert watch["side"] == "SHORT"
    assert watch["entry_price"] == 4668.45
    assert watch["stop_loss"] == 4679.89
    assert watch["take_profit_1"] == 4651.28
    assert round(watch["risk_reward_at_entry"], 2) == 1.50
    assert watch["poi_low"] == 4668.45
    assert watch["poi_high"] == 4675.72
    assert watch["execution_override_enabled"] is False

    path = watch_registry_path("XAUUSD", tmp_path)
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1

    archive_expired_pending_intent(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
        registry_dir=tmp_path,
    )
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_non_limit_placed_records_are_not_archived():
    record = _record()
    record["decision_pipeline"]["final_outcome"] = "REJECTED_L2"

    watch = build_expired_poi_watch(
        record=record,
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
    )

    assert watch is None


def test_approaching_entry_is_watch_only_not_execution():
    watch = build_expired_poi_watch(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
    )

    row = evaluate_expired_poi_watch(
        watch,
        candle={
            "time": "2026-05-06T07:15:00+00:00",
            "open": 4665.80,
            "high": 4666.55,
            "low": 4657.45,
            "close": 4666.12,
        },
        bid=4666.12,
        ask=4666.65,
        config=_config(),
        kill_zone="london",
    )

    assert row["status"] == "APPROACHING_ENTRY"
    assert row["entry_touched"] is False
    assert row["execution_allowed"] is False
    assert row["requires_fresh_approval"] is True


def test_touched_but_market_reentry_rr_decayed_has_no_rearm():
    watch = build_expired_poi_watch(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
    )

    row = evaluate_expired_poi_watch(
        watch,
        candle={
            "time": "2026-05-06T06:35:00+00:00",
            "open": 4664.80,
            "high": 4668.82,
            "low": 4660.50,
            "close": 4666.12,
        },
        bid=4666.12,
        ask=4666.65,
        config=_config(),
        kill_zone="london",
    )

    assert row["entry_touched"] is True
    assert row["status"] == "TOUCHED_RR_DECAYED_NO_REARM"
    assert row["risk_reward_at_current"] < 1.5
    assert row["execution_allowed"] is False


def test_touched_near_poi_geometry_is_shadow_eligible_not_executable():
    watch = build_expired_poi_watch(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
    )

    row = evaluate_expired_poi_watch(
        watch,
        candle={
            "time": "2026-05-06T07:30:00+00:00",
            "open": 4666.00,
            "high": 4670.10,
            "low": 4665.80,
            "close": 4670.00,
        },
        bid=4670.00,
        ask=4670.52,
        config=_config(),
        kill_zone="london",
    )

    assert row["status"] == "TOUCHED_REVALIDATION_ELIGIBLE_SHADOW"
    assert row["risk_reward_at_current"] >= 1.5
    assert row["inside_kill_zone"] is True
    assert row["execution_allowed"] is False


def test_touched_rr_ok_but_sl_distance_too_tight_has_no_rearm():
    watch = build_expired_poi_watch(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
    )

    row = evaluate_expired_poi_watch(
        watch,
        candle={
            "time": "2026-05-06T07:45:00+00:00",
            "open": 4669.99,
            "high": 4677.41,
            "low": 4669.99,
            "close": 4674.95,
        },
        bid=4674.95,
        ask=4675.52,
        config=_config(),
        kill_zone="london",
    )

    assert row["entry_touched"] is True
    assert row["risk_reward_at_current"] >= 1.5
    assert row["current_sl_distance"] < row["sl_absolute_min"]
    assert row["sl_distance_ok"] is False
    assert row["status"] == "TOUCHED_SL_DISTANCE_TOO_TIGHT_NO_REARM"
    assert row["execution_allowed"] is False


def test_original_sl_touch_invalidates_watch():
    watch = build_expired_poi_watch(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
    )

    row = evaluate_expired_poi_watch(
        watch,
        candle={
            "time": "2026-05-06T07:45:00+00:00",
            "open": 4672.00,
            "high": 4680.00,
            "low": 4671.00,
            "close": 4679.90,
        },
        bid=4679.90,
        ask=4680.30,
        config=_config(),
        kill_zone="london",
    )

    assert row["status"] == "INVALIDATED_BY_SL"
    assert row["invalidated_by_sl"] is True


def test_evaluate_and_log_active_watches_writes_shadow_rows_only(tmp_path):
    watch = archive_expired_pending_intent(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
        registry_dir=tmp_path / "registry",
    )
    assert watch is not None

    rows = evaluate_and_log_active_watches(
        symbol="XAUUSD",
        candle={
            "time": "2026-05-06T07:15:00+00:00",
            "open": 4665.80,
            "high": 4666.55,
            "low": 4657.45,
            "close": 4666.12,
        },
        bid=4666.12,
        ask=4666.65,
        config=_config(),
        kill_zone="london",
        registry_dir=tmp_path / "registry",
        log_path=tmp_path / "expired_poi_revalidation.jsonl",
    )

    assert len(rows) == 1
    assert rows[0]["execution_allowed"] is False
    assert (tmp_path / "expired_poi_revalidation.jsonl").exists()


def test_terminal_watch_status_closes_registry_watch(tmp_path):
    registry_dir = tmp_path / "registry"
    log_path = tmp_path / "expired_poi_revalidation.jsonl"

    watch = archive_expired_pending_intent(
        record=_record(),
        intent=_intent(),
        cancel_reason="new_day",
        config=_config(),
        registry_dir=registry_dir,
    )
    assert watch is not None

    rows = evaluate_and_log_active_watches(
        symbol="XAUUSD",
        candle={
            "time": "2026-05-06T08:00:00+00:00",
            "open": 4675.00,
            "high": 4681.81,
            "low": 4669.99,
            "close": 4681.60,
        },
        bid=4680.92,
        ask=4681.49,
        config=_config(),
        kill_zone="london",
        registry_dir=registry_dir,
        log_path=log_path,
    )

    assert rows[0]["status"] == "INVALIDATED_BY_SL"
    assert load_active_watches("XAUUSD", registry_dir=registry_dir) == []

    registry_lines = watch_registry_path("XAUUSD", registry_dir).read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(registry_lines) == 2

    rows_after_close = evaluate_and_log_active_watches(
        symbol="XAUUSD",
        candle={
            "time": "2026-05-06T08:15:00+00:00",
            "open": 4681.00,
            "high": 4683.00,
            "low": 4678.00,
            "close": 4682.00,
        },
        bid=4682.00,
        ask=4682.50,
        config=_config(),
        kill_zone="london",
        registry_dir=registry_dir,
        log_path=log_path,
    )

    assert rows_after_close == []

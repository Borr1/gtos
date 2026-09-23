from __future__ import annotations

import importlib.util
import pytest
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_g0_scid_ready8_numerical_screen_2026_05_13.py")
SPEC = importlib.util.spec_from_file_location("ready8_builder", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules["ready8_builder"] = builder
SPEC.loader.exec_module(builder)


def test_metrics_from_close_to_close_row_derives_signed_and_absolute() -> None:
    row = {
        "terminal_status": "COMPUTABLE",
        "target_family_id": builder.CLOSE_FAMILY,
        "close_to_close_percent_return": -0.0125,
        "close_to_close_absolute_delta": -2.5,
    }
    metrics = builder.metrics_from_row(row)
    assert metrics["close_to_close_percent_return"] == -0.0125
    assert metrics["absolute_close_to_close_percent_return"] == 0.0125
    assert metrics["close_to_close_absolute_delta"] == -2.5
    assert metrics["absolute_close_to_close_absolute_delta"] == 2.5


def test_metrics_from_high_low_row_derives_excursion_anatomy() -> None:
    row = {
        "terminal_status": "COMPUTABLE",
        "target_family_id": builder.HIGH_LOW_FAMILY,
        "upside_excursion_percent": 0.03,
        "downside_excursion_percent": 0.01,
    }
    metrics = builder.metrics_from_row(row)
    assert metrics["high_low_excursion_asymmetry_percent"] == pytest.approx(0.02)
    assert metrics["absolute_high_low_excursion_asymmetry_percent"] == pytest.approx(0.02)
    assert metrics["high_low_total_excursion_percent"] == pytest.approx(0.04)
    assert metrics["high_low_max_excursion_percent"] == pytest.approx(0.03)


def test_group_agg_preserves_fail_closed_denominator() -> None:
    agg = builder.GroupAgg()
    ok_row = {
        "terminal_status": "COMPUTABLE",
        "duplicate_proxy_denominator_key": "dup1",
        "rowset_row_id": "row1",
    }
    fail_row = {
        "terminal_status": "FAIL_CLOSED_NOT_COMPUTABLE",
        "fail_closed_primary_reason": "FAIL_CLOSED_PATH_BAR_MISSING",
        "duplicate_proxy_denominator_key": "dup2",
        "rowset_row_id": "row2",
    }
    agg.add(ok_row, {"close_to_close_percent_return": 0.1})
    agg.add(fail_row, {})
    summary = agg.summary()
    assert summary["total_rows"] == 2
    assert summary["computable_rows"] == 1
    assert summary["fail_closed_rows"] == 1
    assert summary["unique_duplicate_proxy_denominator_keys"] == 2
    assert summary["fail_closed_primary_reason_counts"]["FAIL_CLOSED_PATH_BAR_MISSING"] == 1


def test_fingerprint_payload_ignores_card_specific_names() -> None:
    base = {
        "duplicate_proxy_denominator_key": "dup1",
        "terminal_status": "COMPUTABLE",
        "fail_closed_primary_reason": None,
        "horizon_m15_bars": 4,
        "target_family_id": builder.CLOSE_FAMILY,
        "card_id": "ADV-001",
    }
    other = dict(base)
    other["card_id"] = "BEH-001"
    metrics = {"close_to_close_percent_return": 0.001}
    assert builder.fingerprint_payload(base, metrics) == builder.fingerprint_payload(other, metrics)


def test_completion_safe_base_preserves_required_flags() -> None:
    payload = builder.safe_base("unit")
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["validation_safe"] is False
    assert payload["outcome_review_opened"] is False
    assert payload["live_effect"] is False
    assert payload["opens_ai_api"] is False
    assert payload["opens_broker_account_order_history_deal_position_evidence"] is False

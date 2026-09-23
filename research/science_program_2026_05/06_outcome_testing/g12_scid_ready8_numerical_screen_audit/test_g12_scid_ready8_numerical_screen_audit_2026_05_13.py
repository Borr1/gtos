from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent

BUILDER_SPEC = importlib.util.spec_from_file_location(
    "g12_ready8_numeric_audit_builder",
    ROUTE_DIR / "build_g12_scid_ready8_numerical_screen_audit_2026_05_13.py",
)
assert BUILDER_SPEC and BUILDER_SPEC.loader
builder = importlib.util.module_from_spec(BUILDER_SPEC)
sys.modules["g12_ready8_numeric_audit_builder"] = builder
BUILDER_SPEC.loader.exec_module(builder)

VERIFIER_SPEC = importlib.util.spec_from_file_location(
    "g12_ready8_numeric_audit_verifier",
    ROUTE_DIR / "verify_g12_scid_ready8_numerical_screen_audit_2026_05_13.py",
)
assert VERIFIER_SPEC and VERIFIER_SPEC.loader
verifier = importlib.util.module_from_spec(VERIFIER_SPEC)
sys.modules["g12_ready8_numeric_audit_verifier"] = verifier
VERIFIER_SPEC.loader.exec_module(verifier)


def test_fingerprint_payload_ignores_card_identity() -> None:
    row = {
        "duplicate_proxy_denominator_key": "dup",
        "terminal_status": "COMPUTABLE",
        "fail_closed_primary_reason": None,
        "horizon_m15_bars": 4,
        "target_family_id": builder.CLOSE_FAMILY,
        "card_id": "ADV-001",
    }
    other = dict(row)
    other["card_id"] = "BEH-001"
    metrics = {"close_to_close_percent_return": 0.0090123456}
    assert builder.fingerprint_payload(row, metrics) == builder.fingerprint_payload(other, metrics)


def test_metrics_from_target_row_derives_high_low_total_and_asymmetry() -> None:
    row = {
        "terminal_status": "COMPUTABLE",
        "target_family_id": builder.HIGH_LOW_FAMILY,
        "upside_excursion_percent": 0.03,
        "downside_excursion_percent": 0.01,
    }
    metrics = builder.metrics_from_target_row(row)
    assert metrics["high_low_total_excursion_percent"] == 0.04
    assert metrics["high_low_excursion_asymmetry_percent"] == 0.019999999999999997


def test_safe_base_preserves_forbidden_surface_flags() -> None:
    payload = builder.safe_base("unit")
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["validation_safe"] is False
    assert payload["outcome_review_opened"] is False
    assert payload["live_effect"] is False
    assert payload["opens_ai_api"] is False
    assert payload["opens_live_trading_behavior"] is False
    assert payload["opens_broker_account_order_history_deal_position_evidence"] is False


def test_required_output_paths_are_versioned() -> None:
    paths = verifier.required_paths()
    assert "decision" in paths
    assert all("2026_05_13" in path.name or "2026-05-13" in path.name for path in paths.values())


def test_built_artifacts_verify_cleanly() -> None:
    result = verifier.verify(write_result=False)
    assert result["ok"], result["issues"]
    assert result["can_mark_goal_complete"] is True

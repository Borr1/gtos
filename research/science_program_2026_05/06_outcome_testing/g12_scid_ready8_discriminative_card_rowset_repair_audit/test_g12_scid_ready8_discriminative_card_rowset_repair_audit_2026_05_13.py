from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent

BUILDER_SPEC = importlib.util.spec_from_file_location(
    "g12_ready8_discriminative_audit_builder",
    ROUTE_DIR / "build_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py",
)
assert BUILDER_SPEC and BUILDER_SPEC.loader
builder = importlib.util.module_from_spec(BUILDER_SPEC)
sys.modules["g12_ready8_discriminative_audit_builder"] = builder
BUILDER_SPEC.loader.exec_module(builder)

VERIFIER_SPEC = importlib.util.spec_from_file_location(
    "g12_ready8_discriminative_audit_verifier",
    ROUTE_DIR / "verify_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py",
)
assert VERIFIER_SPEC and VERIFIER_SPEC.loader
verifier = importlib.util.module_from_spec(VERIFIER_SPEC)
sys.modules["g12_ready8_discriminative_audit_verifier"] = verifier
VERIFIER_SPEC.loader.exec_module(verifier)


def test_safe_base_preserves_closed_surfaces() -> None:
    payload = builder.safe_base("unit")
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["validation_safe"] is False
    assert payload["outcome_review_opened"] is False
    assert payload["live_effect"] is False
    assert payload["opens_result_scoring"] is False
    assert payload["opens_broker_account_order_history_deal_position_evidence"] is False
    assert payload["opens_live_trading_behavior"] is False


def test_safe_flags_ok_rejects_open_surface() -> None:
    payload = builder.safe_base("unit")
    assert builder.safe_flags_ok(payload)
    payload["opens_validation"] = True
    assert not builder.safe_flags_ok(payload)


def test_counter_to_dict_is_stable_sorted() -> None:
    assert list(builder.counter_to_dict(Counter({"b": 1, "a": 2})).keys()) == ["a", "b"]


def test_required_output_paths_are_versioned() -> None:
    paths = verifier.required_paths()
    assert "decision" in paths
    assert "next_prompt" in paths
    assert all("2026_05_13" in path.name or "2026-05-13" in path.name for path in paths.values())


def test_built_artifacts_verify_cleanly() -> None:
    result = verifier.verify(write_result=False)
    assert result["ok"], result["issues"]
    assert result["can_mark_goal_complete"] is True


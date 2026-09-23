from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_g0_ready8_disc_screen.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("g0_ready8_disc_builder_under_test", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def test_close_to_close_metric_uses_signed_percent_and_absolute_magnitude():
    row = {
        "terminal_status": "COMPUTABLE",
        "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
        "close_to_close_percent_return": -0.0125,
    }
    signed, magnitude = builder.signed_and_magnitude(row)
    assert signed == -0.0125
    assert magnitude == 0.0125


def test_high_low_metric_uses_excursion_asymmetry_and_total_excursion():
    row = {
        "terminal_status": "COMPUTABLE",
        "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
        "upside_excursion_percent": 0.03,
        "downside_excursion_percent": 0.01,
    }
    signed, magnitude = builder.signed_and_magnitude(row)
    assert math.isclose(signed, 0.02)
    assert math.isclose(magnitude, 0.04)


def test_stats_preserves_computable_and_fail_closed_counts():
    stats = builder.Stats()
    stats.add(
        {
            "terminal_status": "COMPUTABLE",
            "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
            "close_to_close_percent_return": 0.02,
            "rowset_fail_closed_reasons": [],
        }
    )
    stats.add(
        {
            "terminal_status": "FAIL_CLOSED_NOT_COMPUTABLE",
            "fail_closed_primary_reason": "FAIL_CLOSED_HORIZON_BAR_MISSING",
            "rowset_fail_closed_reasons": ["FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE"],
        }
    )
    payload = stats.as_dict()
    assert payload["total_rows"] == 2
    assert payload["computable_rows"] == 1
    assert payload["fail_closed_rows"] == 1
    assert payload["target_fail_closed_primary_reason_counts"]["FAIL_CLOSED_HORIZON_BAR_MISSING"] == 1
    assert payload["rowset_fail_closed_reason_counts"]["FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE"] == 1


def test_contrast_classifies_pass_control_delta_and_inversion():
    pass_stats = builder.Stats()
    control_stats = builder.Stats()
    pass_stats.add(
        {
            "terminal_status": "COMPUTABLE",
            "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
            "close_to_close_percent_return": 0.01,
            "rowset_fail_closed_reasons": [],
        }
    )
    control_stats.add(
        {
            "terminal_status": "COMPUTABLE",
            "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
            "close_to_close_percent_return": -0.02,
            "rowset_fail_closed_reasons": [],
        }
    )
    classified = builder.classify_contrast(pass_stats, control_stats)
    assert classified["comparison_status"] == "PASS_CONTROL_COMPARABLE"
    assert classified["movement_shift_class"] == "PASS_HIGHER_NEUTRAL_SIGNED_MOVEMENT_THAN_CONTROL"
    assert classified["inversion_flag"] is True


def test_enriched_row_computes_duplicate_and_fail_closed_families():
    row = {
        "duplicate_proxy_denominator_key": "dup-1",
        "fail_closed_primary_reason": None,
        "rowset_fail_closed_reasons": ["FAIL_CLOSED_MISSING_PRIOR_CANDIDATE"],
        "partition_assignment": None,
        "validation_partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
    }
    enriched = builder.enriched_row(row, {"dup-1": 3})
    assert enriched["duplicate_concentration_bucket"] == "PASS_CARD_COUNT_3"
    assert enriched["combined_fail_closed_family"] == "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE"
    assert enriched["partition_assignment"] == "SEALED_VALIDATION_CANDIDATE_DESIGN"


def test_next_prompt_text_embeds_required_context_paths(monkeypatch):
    prompt_path = ROUTE_DIR / "_tmp_prompt_hardening_test.md"
    starter_path = ROUTE_DIR / "_tmp_prompt_hardening_test.txt"
    monkeypatch.setattr(builder, "NEXT_G12_PROMPT", prompt_path)
    monkeypatch.setattr(builder, "NEXT_G12_STARTER", starter_path)
    try:
        builder.write_next_g12_prompt()
        builder.write_next_g12_starter()
        prompt = prompt_path.read_text(encoding="utf-8")
        starter = starter_path.read_text(encoding="utf-8")
        assert "goal_session_research_discipline.md" in prompt
        assert "research_operating_doctrine.md" in prompt
        assert "NO_PROMOTION_VERDICT" in prompt
        assert "_tmp_prompt_hardening_test.md" in starter
        assert "NO_PROMOTION_VERDICT" in starter
    finally:
        prompt_path.unlink(missing_ok=True)
        starter_path.unlink(missing_ok=True)

import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_haz001_density_waiting_time_concentration_expansion_and_sealed_retest_2026_05_15.py"
VERIFIER_PATH = HERE / "verify_haz001_density_waiting_time_concentration_expansion_and_sealed_retest_2026_05_15.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_primary_movement_value_uses_upside_minus_downside_for_high_low():
    builder = load_module(BUILDER_PATH, "haz001_builder")
    row = {
        "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
        "upside_excursion_percent": 0.012,
        "downside_excursion_percent": 0.005,
    }
    assert builder.primary_movement_value(row) == 0.007


def test_wait_gap_and_prior_count_buckets_are_source_descriptor_only():
    builder = load_module(BUILDER_PATH, "haz001_builder_bucket")
    row = {"descriptor_values": {"previous_candidate_gap_minutes": 90.0, "prior_24h_candidate_count": 3}}
    assert builder.wait_gap_bucket(row) == "WAIT_GAP_GE_60M"
    assert builder.prior_24h_count_bucket(row) == "PRIOR_24H_COUNT_GE_3"


def test_verifier_accepts_generated_artifacts():
    verifier = load_module(VERIFIER_PATH, "haz001_verifier")
    assert verifier.main() == 0
    result_path = HERE / "HAZ001_VERIFICATION_RESULT_2026-05-15.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True


def test_retest_packet_excludes_target_outcome_fields():
    packet = HERE / "HAZ001_DECONCENTRATED_RETEST_INPUT_PACKET_SOURCE_CONTROL_ONLY_2026-05-15.jsonl"
    forbidden = {
        "close_to_close_percent_return",
        "upside_excursion_percent",
        "downside_excursion_percent",
        "target_result_row_id",
        "horizon_close",
        "terminal_status",
    }
    with packet.open("r", encoding="utf-8") as fh:
        first = json.loads(next(fh))
    assert not forbidden.intersection(first)
    assert first["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert first["validation_safe"] is False

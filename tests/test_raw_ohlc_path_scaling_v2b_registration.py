from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest


SPEC = Path(
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2B_OB_BOUNDARY_VALIDATION_SPEC_V1.json"
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"raw_ohlc_v2b_registration_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_v2b_spec_registers_ob_boundary_without_promotion():
    payload = json.loads(SPEC.read_text(encoding="utf-8"))

    assert payload["status"] == "REGISTERED_BEFORE_FUTURE_VALIDATION_RUN"
    assert payload["required_promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["promotion_verdict_allowed"] is False
    assert payload["primary_candidate"]["variant_id"] == "STRUCT_OB_BOUNDARY_V2"
    assert payload["primary_candidate"]["selector_ids"] == ["OB_PROTECTIVE_BOUNDARY"]
    assert "blocked" in payload["blocked_next_layers"]["v3_reentry"]


def test_v2b_spec_has_concentration_and_control_gates():
    payload = json.loads(SPEC.read_text(encoding="utf-8"))
    gates = {row["gate"]: row["rule"] for row in payload["acceptance_gates_research_only"]}

    assert "all_major_groups_nonnegative" in gates
    assert "target_not_weaker_than_negative_controls" in gates
    assert "blocked_controls_not_driver" in gates
    assert "cohort_breadth" in gates
    assert "single_cohort_cap" in gates
    assert "no_leak" in gates


def test_v2b_spec_blocks_v3_and_live_logic():
    payload = json.loads(SPEC.read_text(encoding="utf-8"))

    assert "blocked" in payload["blocked_next_layers"]["v3_reentry"]
    assert "blocked" in payload["blocked_next_layers"]["live_logic"]
    assert "orderflow" in payload["blocked_next_layers"]["orderflow_integration"]

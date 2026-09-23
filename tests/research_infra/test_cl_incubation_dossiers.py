"""Behavioural checks for Session CL's pre-registration dossiers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
DRIVER = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase17/receipts/cl_incubation_dossiers.py"
)


@pytest.fixture(scope="module")
def cl_incubation():
    spec = importlib.util.spec_from_file_location("test_cl_incubation_driver", DRIVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_proposals_validate_at_bounded_weight_and_do_not_claim_admission(cl_incubation) -> None:
    incubants, _ = cl_incubation.proposals()
    assert len(incubants) == 2
    assert all(row.proposed_weight == 0.025 for row in incubants)
    assert all(row.admission_basis == "OWNER_RISK_ACCEPTED" for row in incubants)
    assert all(row.stop_rules and row.promotion_rules for row in incubants)


def test_runtime_mismatch_vetoes_both_proposals(cl_incubation) -> None:
    doc = cl_incubation.build()
    assert doc["approved_for_arming_now"] == []
    assert all(not row["ready_to_arm"] for row in doc["proposals"])
    by_sleeve = {row["sleeve"]: row for row in doc["proposals"]}
    assert not by_sleeve[cl_incubation.ETH]["runtime_checks"][
        "target5_frontier_override_present"
    ]
    assert by_sleeve[cl_incubation.ASIA]["runtime_checks"]["runtime_confidence"] == 0.25
    assert by_sleeve[cl_incubation.ASIA]["proposed_weight"] == 0.025
    assert all(row["official_registry_state"] == "PROPOSED" for row in doc["proposals"])
    assert all(row["iteration_disclosure"]["billed"] is False for row in doc["proposals"])


def test_parent_threshold_variant_is_not_misregistered_as_a_sleeve(cl_incubation) -> None:
    doc = cl_incubation.build()
    reason = doc["screened_not_proposed"]["thr_sub_xvol_pullback_vr14_s125_ac015"]
    assert "not a distinct runtime sleeve" in reason
    assert "already armed" in reason

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import audit_phase3_research_claim_ledger as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"phase3_claim_ledger_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_variant_finds_requested_row():
    summary = {"variant_summary": [{"variant_id": "A", "net_mean_r_cost_0.05": 0.1}]}
    assert mod.variant(summary, "A")["net_mean_r_cost_0.05"] == 0.1


def test_best_structural_ignores_non_struct_variants():
    summary = {
        "variant_summary": [
            {"variant_id": "J46_J49_ONLY", "net_mean_r_cost_0.05": 0.5},
            {"variant_id": "STRUCT_A", "net_mean_r_cost_0.05": 0.2},
            {"variant_id": "STRUCT_B", "net_mean_r_cost_0.05": 0.3},
        ]
    }
    assert mod.best_structural(summary)["variant_id"] == "STRUCT_B"

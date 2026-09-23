from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
    / "cp_true_utc_candidate_factory.py"
)
SPEC = importlib.util.spec_from_file_location("cp_true_utc_candidate_factory", TOOL_PATH)
assert SPEC and SPEC.loader
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def test_declaration_is_data_free_and_exactly_1092_cells() -> None:
    protocol = tool.build_protocol(declared_utc="2026-08-01T00:00:00+00:00")
    assert protocol["declared_before_conditional_outcome_evaluation"] is True
    assert protocol["family_construction"]["cross_product"] == "28 x 39"
    assert len(protocol["cells"]) == 1092
    assert len({cell["cell_id"] for cell in protocol["cells"]}) == 1092
    core = dict(protocol)
    root = core.pop("protocol_root_sha256")
    assert root == tool.stable_sha(core)


def test_policy_mask_uses_only_declared_pretrade_fields() -> None:
    frame = pd.DataFrame(
        {
            "utc_hour_bucket": ["h14_15", "h14_15", "h15_16"],
            "cost_r": [0.20, 0.30, 0.10],
            "candidate_ev_r": [0.75, 0.75, 0.75],
            "broker_pretrade_cost_executable": [True, True, True],
        }
    )
    cell = {
        "time": {
            "all": [tool.predicate("utc_hour_bucket", "eq", "h14_15")]
        },
        "condition": {
            "all": [
                tool.predicate("broker_pretrade_cost_executable", "eq", True),
                tool.predicate("cost_r", "lte", 0.25),
                tool.predicate("candidate_ev_r", "gte", 0.5),
            ]
        },
    }
    assert tool.cell_mask(frame, cell).tolist() == [True, False, False]


def test_train_gate_requires_every_robust_check() -> None:
    passing = {
        "n": 250,
        "n_days": 13,
        "mean_r_lower": 0.10,
        "precision_lower": 0.60,
        "positive_day_share_lower": 0.70,
    }
    survived, checks = tool.train_gate(passing)
    assert survived and all(checks.values())
    straddle = {**passing, "mean_r_lower": -0.001}
    survived, checks = tool.train_gate(straddle)
    assert not survived
    assert checks["mean_positive_at_f31_lower_bound"] is False

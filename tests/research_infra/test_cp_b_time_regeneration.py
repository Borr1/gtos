from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
    / "cp_b_time_regeneration.py"
)
SPEC = importlib.util.spec_from_file_location("cp_b_time_regeneration", TOOL_PATH)
assert SPEC and SPEC.loader
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def test_aw_contract_has_exactly_83_predeclared_b_time_looks() -> None:
    protocol = tool._json(tool.DEFAULT_AW_PROTOCOL)
    cells = tool.declared_b_time_cells(protocol)
    assert len(cells) == 83
    assert len({cell["cell_id"] for cell in cells}) == 83


def test_categorical_and_tertile_membership_use_regenerated_values() -> None:
    frame = pd.DataFrame(
        {
            "utc_hour_bucket": ["h22_23", "h00_01", "h01_02"],
            "decision_hour_utc": [22.0, 0.0, 1.0],
        }
    )
    categorical = {
        "axis": "utc_hour_bucket",
        "cut": "level_wise",
        "level": "h00_01",
    }
    tertile = {
        "axis": "decision_hour_utc",
        "cut": "train_tertiles",
        "lower": None,
        "upper": 7.0,
    }
    assert tool.cell_mask(frame, categorical).tolist() == [False, True, False]
    assert tool.cell_mask(frame, tertile).tolist() == [False, True, True]


def test_f31_interval_verdict_never_promotes_a_sign_straddle() -> None:
    base = {
        "n": 300,
        "mean_r_upper": 0.01,
        "mean_r_lower": -0.02,
        "day_positive_frac_upper": 0.75,
        "day_positive_frac_lower": 0.75,
    }
    assert tool.interval_january_verdict(base, base) == "UNRESOLVED_F31_AT_F1"
    negative = {**base, "mean_r_upper": -0.01, "mean_r_lower": -0.05}
    assert tool.interval_january_verdict(negative, base) == "F1_TRAIN"
    robust = {**base, "mean_r_upper": 0.10, "mean_r_lower": 0.05}
    assert tool.interval_january_verdict(robust, robust) == (
        "JANUARY_SURVIVOR_ROBUST_TO_F31_BOUND"
    )

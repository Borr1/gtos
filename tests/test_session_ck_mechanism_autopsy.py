from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/ck_mechanism_autopsy.py"
)
SPEC = importlib.util.spec_from_file_location("ck_mechanism_autopsy", SCRIPT)
assert SPEC and SPEC.loader
CK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CK)

CD_SCRIPT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/cd_pool.py"
)
CD_SPEC = importlib.util.spec_from_file_location("cd_pool_for_ck_test", CD_SCRIPT)
assert CD_SPEC and CD_SPEC.loader
CD = importlib.util.module_from_spec(CD_SPEC)
CD_SPEC.loader.exec_module(CD)


def _frame() -> pd.DataFrame:
    # Target, stop, and horizon rows under the source 2D/1D geometry.
    return pd.DataFrame(
        {
            "cost_r": [0.2, 0.2, 0.2],
            "recorded_gross_r": [2.0, -1.0, 0.25],
            "recorded_target_distance": [2.0, 2.0, 2.0],
            "recorded_terminal_class": ["target", "stop", "other"],
        }
    )


def _masks() -> dict[str, np.ndarray]:
    all_rows = np.ones(3, dtype=bool)
    return {"TRAIN": all_rows, "HOLDOUT": all_rows, "FULL": all_rows}


def test_recorded_geometry_is_exact_for_all_terminal_classes() -> None:
    cell = CK.geometry_cell(
        _frame(), _masks(), target_d=2.0, stop_d=1.0, orientation="as_declared"
    )
    full = cell["splits"]["FULL"]
    assert full["exact_rows"] == 3
    assert full["mean_net_lower"] == full["mean_net_upper"]
    assert np.isclose(full["mean_net_lower"], (1.8 - 1.2 + 0.05) / 3)


def test_direct_monotonic_rectangles_do_not_invent_unknown_rows() -> None:
    cell = CK.geometry_cell(
        _frame(), _masks(), target_d=1.0, stop_d=1.0, orientation="as_declared"
    )
    full = cell["splits"]["FULL"]
    # The source target identifies the closer target; the source stop and horizon do not.
    assert full["exact_rows"] == 1
    assert full["mean_net_lower"] < full["mean_net_upper"]
    assert cell["classification"] == "NOT_IDENTIFIED"


def test_inversion_keeps_source_stop_ambiguous_in_strict_bounds() -> None:
    cell = CK.geometry_cell(
        _frame(), _masks(), target_d=1.0, stop_d=2.0, orientation="inverted"
    )
    strict = cell["splits"]["FULL"]
    sensitivity = cell["inverted_zero_ambiguity_sensitivity"]["FULL"]
    assert strict["exact_rows"] == 1  # source target -> inverted stop
    assert sensitivity["exact_rows"] == 2  # source stop maps only under the sensitivity
    assert strict["bound_width"] > sensitivity["bound_width"]


def test_protocol_is_the_preoutcome_committed_hash() -> None:
    assert CK._sha256_file(CK.PROTOCOL) == CK.EXPECTED_PROTOCOL_SHA256


def test_compact_pool_projection_retains_autopsy_oracle_contract() -> None:
    row = {
        "candidate_id": "x",
        "same_bar_ambiguity": True,
        "ambiguity_resolution": "conservative_stop",
        "terminal_outcome": "same_bar_ambiguous",
        "target_first_touch_utc": "2026-01-02T01:00:00Z",
        "stop_first_touch_utc": "2026-01-02T01:00:00Z",
        "path_index_source_path": "/bound/source.csv",
        "path_index_source_sha256": "a" * 64,
        "path_row_count": 121,
    }
    projected = CD.project(row)
    for key in (
        "same_bar_ambiguity", "ambiguity_resolution", "terminal_outcome",
        "target_first_touch_utc", "stop_first_touch_utc", "path_index_source_path",
        "path_index_source_sha256", "path_row_count",
    ):
        assert projected[key] == row[key]


def test_compact_pool_projection_preserves_direction_as_side() -> None:
    assert CD.project({"direction": "LONG", "side": None})["side"] == "LONG"
    assert CD.project({"direction": "SHORT"})["side"] == "SHORT"
    assert CD.project({"direction": "LONG", "side": "SHORT"})["side"] == "SHORT"

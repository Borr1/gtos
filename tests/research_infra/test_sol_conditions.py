from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.research_infra.sol_conditions import (
    CellSpec,
    CompactPool,
    _cost_width_summary,
    _membership_structure,
    _permutation_index,
    build_cells,
    describe,
    load_feb_gross_reconciliation,
    load_protocol,
    row_axes,
    sha256_file,
    spearman,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = (
    REPO_ROOT
    / "research/operations/wave19_sol_repair_2026_08_01/conditions/CONDITIONS_PROTOCOL.json"
)
RECONCILIATION = PROTOCOL.parent / "FEB_GROSS_IDENTITY_RECONCILIATION.json"
FROZEN = PROTOCOL.parent / "FROZEN_JAN_SELECTIONS.json"


def _pool() -> CompactPool:
    return CompactPool(
        identities=["a", "b", "c"],
        days=["2026-01-02", "2026-01-02", "2026-01-05"],
        splits=["TRAIN", "TRAIN", "HOLDOUT"],
        symbols=["XAUUSD", "XAUUSD", "XAUUSD"],
        gross=np.asarray([1.0, -0.5, -0.2]),
        net=np.asarray([0.8, -0.7, -0.4]),
        cost=np.asarray([0.2, 0.2, 0.2]),
        slippage=np.asarray([0.02, 0.02, 0.02]),
        members=[],
    )


def test_protocol_materializes_exact_declared_cell_space() -> None:
    protocol = load_protocol(PROTOCOL)
    cells = build_cells(protocol)

    assert len(cells) == 884
    assert len({cell.cell_id for cell in cells}) == 884
    assert sum(cell.axis == "family_direction_session" for cell in cells) == 540
    assert sum(cell.axis == "family_hour" for cell in cells) == 240
    assert protocol["repair_decision"]["if_none"]["default_on"] is False


def test_row_axes_uses_true_utc_and_frozen_symbol_map() -> None:
    protocol = load_protocol(PROTOCOL)
    row = {
        "decision_time_utc": "2026-01-02T13:15:00+00:00",
        "origin_family": "current_fvg_fill",
        "direction": "LONG",
        "side": "LONG",
        "session_bucket": "ny",
        "utc_hour_bucket": "h13_14",
        "kill_zone": "ny",
        "route_session": "ny",
        "symbol": "XAUUSD",
    }

    axes = row_axes(row, protocol)

    assert axes["family_direction_session"] == ("current_fvg_fill", "LONG", "ny")
    assert axes["family_hour"] == ("current_fvg_fill", "h13_14")
    assert axes["symbol_class"] == ("metal",)
    assert axes["day_of_week"] == ("FRI",)
    assert len(axes) == 10


def test_row_axes_fails_closed_on_side_disagreement_or_undeclared_symbol() -> None:
    protocol = load_protocol(PROTOCOL)
    base = {
        "decision_time_utc": "2026-01-02T13:15:00+00:00",
        "origin_family": "current_fvg_fill",
        "direction": "LONG",
        "side": "SHORT",
        "session_bucket": "ny",
        "utc_hour_bucket": "h13_14",
        "kill_zone": "ny",
        "route_session": "ny",
        "symbol": "XAUUSD",
    }
    with pytest.raises(ValueError, match="side_direction_disagreement"):
        row_axes(base, protocol)
    base["side"] = "LONG"
    base["symbol"] = "NOT_DECLARED"
    with pytest.raises(ValueError, match="undeclared_symbol"):
        row_axes(base, protocol)


def test_describe_reports_row_and_day_positive_shares() -> None:
    pool = _pool()
    metrics = describe(pool, [0, 1, 2])

    assert metrics["n"] == 3
    assert metrics["day_count"] == 2
    assert metrics["gross_mean_r"] == pytest.approx(0.1)
    assert metrics["gross_positive_share"] == pytest.approx(1 / 3)
    assert metrics["gross_day_positive_share"] == pytest.approx(0.5)
    assert metrics["net_mean_r"] == pytest.approx(-0.1)
    assert metrics["net_day_positive_share"] == pytest.approx(0.5)


def test_within_day_permutation_is_seeded_and_never_crosses_days() -> None:
    groups = [np.asarray([0, 1, 2]), np.asarray([3, 4])]
    first = _permutation_index(5, groups, 19032651)
    second = _permutation_index(5, groups, 19032651)

    assert first.tolist() == second.tolist()
    assert sorted(first[:3].tolist()) == [0, 1, 2]
    assert sorted(first[3:].tolist()) == [3, 4]


def test_spearman_uses_average_tie_ranks() -> None:
    assert spearman([1.0, 2.0, 2.0, 4.0], [10.0, 20.0, 20.0, 40.0]) == pytest.approx(1.0)
    assert spearman([1.0], [1.0]) is None
    assert spearman([1.0, 1.0], [2.0, 3.0]) is None


def test_alias_collapse_is_feature_membership_based() -> None:
    pool = _pool()
    pool.splits = ["TRAIN", "TRAIN", "TRAIN"]
    pool.members = [[0, 1, 2], [0, 1, 2]]
    cells = [
        CellSpec(index=0, axis="family", values=("same",)),
        CellSpec(index=1, axis="route_session", values=("same",)),
    ]
    protocol = {
        "cell_space": {
            "minimum_train_rows": 1,
            "feature_only_expectations": {
                "eligible_cells_before_alias_collapse": 2,
                "unique_eligible_partitions": 1,
            },
        }
    }

    metadata, canonical = _membership_structure(pool, cells, protocol)

    assert canonical == [0]
    assert metadata[0]["canonical"] is True
    assert metadata[0]["aliases"] == [cells[1].cell_id]
    assert metadata[1]["alias_of"] == cells[0].cell_id


def test_cost_width_burden_keeps_fixed_slippage_explicit() -> None:
    pool = _pool()
    pool.cost = np.asarray([0.15, 0.30, 0.20])
    pool.slippage = np.asarray([0.02, 0.15, 0.02])

    burden = _cost_width_summary(pool, [0, 1, 2])

    assert burden["share_cost_at_or_below_0p15r"] == pytest.approx(1 / 3)
    assert burden["required_width_multiple_all_costs_scale"]["max"] == pytest.approx(2.0)
    assert burden["required_width_multiple_fixed_slippage"]["infinite_rows"] == 1
    assert burden["arithmetic_only"] is True
    assert burden["path_outcomes_recomputed"] is False


def test_protocol_contains_no_open_ended_cell_discovery() -> None:
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["cell_space"]["declared_cells_total"] == 884
    assert protocol["cell_space"]["subfloor_rule"].startswith("Every declared cell")
    assert protocol["february_transfer"]["rule"].startswith("Evaluate exactly the frozen")


def test_february_rounding_reconciliation_is_narrow_and_content_bound(
    tmp_path: Path,
) -> None:
    receipt = load_feb_gross_reconciliation(
        RECONCILIATION,
        protocol_sha256=sha256_file(PROTOCOL),
        frozen_selection_sha256=sha256_file(FROZEN),
        february_source_sha256=(
            load_protocol(PROTOCOL)["inputs"]["february"]["sha256"]
        ),
    )
    assert receipt["bounded_repair"]["identity_tolerance_r"] == 5e-9
    assert receipt["bounded_repair"]["gross_metric_unchanged"] == (
        "opportunity_net_proxy_r + cost_r"
    )
    assert receipt["identity_residual_census"]["rows_over_5e_9"] == 0

    widened = json.loads(RECONCILIATION.read_text())
    widened["bounded_repair"]["identity_tolerance_r"] = 1e-8
    widened_path = tmp_path / "widened.json"
    widened_path.write_text(json.dumps(widened))
    with pytest.raises(ValueError, match="tolerance_not_bounded"):
        load_feb_gross_reconciliation(
            widened_path,
            protocol_sha256=sha256_file(PROTOCOL),
            frozen_selection_sha256=sha256_file(FROZEN),
            february_source_sha256=(
                load_protocol(PROTOCOL)["inputs"]["february"]["sha256"]
            ),
        )

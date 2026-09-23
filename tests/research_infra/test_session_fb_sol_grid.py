from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL = (
    REPO
    / "research/operations/wave19_sol_repair_2026_08_01/grid/"
    "session_fb_sol_grid.py"
)
SPEC = importlib.util.spec_from_file_location("session_fb_sol_grid", TOOL)
assert SPEC and SPEC.loader
fb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fb
SPEC.loader.exec_module(fb)


def _pool_row(
    candidate_id: str,
    *,
    minute: int = 0,
    symbol: str = "EURUSD",
    side: str = "LONG",
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "decision_time_utc": f"2026-01-02T10:{minute:02d}:00+00:00",
        "symbol": symbol,
        "side": side,
        "direction": side,
        "origin_family": "family_a",
    }


def _sidecar_row(pool: dict[str, object]) -> dict[str, object]:
    return {
        "arm_id": "S0R0",
        "candidate_id": pool["candidate_id"],
        "decision_time_utc": pool["decision_time_utc"],
        "symbol": pool["symbol"],
        "side": pool["side"],
    }


def _leader(
    train_net: float,
    holdout_net: float,
    train_gross: float,
    holdout_gross: float,
) -> dict[str, object]:
    return {
        "splits": {
            "TRAIN": {"mean_net_r": train_net, "mean_gross_r": train_gross},
            "HOLDOUT": {
                "mean_net_r": holdout_net,
                "mean_gross_r": holdout_gross,
            },
            "FULL": {
                "mean_net_r": (train_net + holdout_net) / 2,
                "mean_gross_r": (train_gross + holdout_gross) / 2,
            },
        }
    }


def test_protocol_is_frozen_unbilled_and_forbids_march_and_live_forward() -> None:
    protocol = fb.load_protocol()

    assert protocol["evidence_boundary"]["billed"] is False
    assert protocol["evidence_boundary"]["march_2026_outcomes"] == "UNREAD_AND_FORBIDDEN"
    assert protocol["evidence_boundary"]["live_forward_outcomes"] == "UNREAD_AND_FORBIDDEN"
    assert protocol["look_accounting"]["expected_geometry_looks"] == 198
    assert protocol["breaker_and_null_control"]["draws"] == 999
    assert protocol["breaker_and_null_control"]["seed"] == 20260801


def test_composite_key_includes_symbol_and_side_not_candidate_id_alone() -> None:
    left = _pool_row("duplicate-id", symbol="EURUSD", side="LONG")
    right = _pool_row("duplicate-id", symbol="USDJPY", side="SHORT")

    assert fb.composite_key(left) != fb.composite_key(right)
    assert fb.composite_key(left)[0] == fb.composite_key(right)[0]


def test_composite_sidecar_accepts_candidate_id_multiplicity_when_full_keys_match(
    tmp_path: Path,
) -> None:
    rows = [
        _pool_row("duplicate-id", symbol="EURUSD", side="LONG"),
        _pool_row("duplicate-id", symbol="USDJPY", side="SHORT"),
    ]
    sidecar = tmp_path / "sidecar.jsonl.gz"
    with gzip.open(sidecar, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_sidecar_row(row)) + "\n")

    receipt = fb.validate_composite_sidecar(rows, sidecar)

    assert receipt["pool_unique_composite_keys"] == 2
    assert receipt["sidecar_unique_composite_keys"] == 2
    assert receipt["candidate_ids_with_multiplicity"] == 1
    assert receipt["rows_whose_candidate_id_is_not_unique"] == 2
    assert receipt["candidate_id_duplicate_excess_rows"] == 1
    assert receipt["candidate_id_alone_used_as_join"] is False


def test_composite_sidecar_rejects_symbol_misalignment(tmp_path: Path) -> None:
    row = _pool_row("candidate")
    wrong = _sidecar_row(row)
    wrong["symbol"] = "USDJPY"
    sidecar = tmp_path / "sidecar.jsonl.gz"
    with gzip.open(sidecar, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(wrong) + "\n")

    with pytest.raises(fb.FBRefusal, match="sidecar_composite_alignment_mismatch"):
        fb.validate_composite_sidecar([row], sidecar)


@pytest.mark.parametrize(
    ("declared", "inverted", "expected"),
    [
        (
            _leader(0.2, 0.1, 0.4, 0.3),
            _leader(-0.1, -0.2, 0.1, 0.1),
            "PERSISTENT_AS_DECLARED_REPAIR",
        ),
        (
            _leader(-0.2, -0.1, -0.1, -0.1),
            _leader(0.3, 0.2, 0.5, 0.4),
            "ANTI_PREDICTIVE_INVERTIBLE",
        ),
        (
            _leader(-0.2, -0.1, 0.2, 0.1),
            _leader(-0.3, -0.2, -0.1, -0.1),
            "GROSS_POSITIVE_COST_KILLED",
        ),
        (
            _leader(-0.2, -0.1, -0.1, -0.2),
            _leader(-0.3, -0.2, -0.2, -0.1),
            "DEAD_UNDER_BOTH_ORIENTATIONS",
        ),
        (
            _leader(-0.2, -0.1, 0.1, -0.1),
            _leader(-0.3, -0.2, -0.2, 0.1),
            "NOISE",
        ),
    ],
)
def test_classification_precedence_is_total_and_deterministic(
    declared: dict[str, object], inverted: dict[str, object], expected: str
) -> None:
    assert fb.classify_orientation_leaders(declared, inverted) == expected


def test_geometry_uses_conservative_ambiguity_and_reprices_cost_by_stop() -> None:
    inf = fb.cq.INF_INDEX
    summary = {
        "target_index": np.asarray([[0], [0], [inf]], dtype=np.int32),
        "stop_index": np.asarray([[1], [0], [inf]], dtype=np.int32),
        "terminal_signed_d": np.asarray([2.0, 0.0, 0.5]),
    }

    vectors = fb.geometry_vectors(
        summary,
        target_position=0,
        stop_position=0,
        target_d=2.0,
        stop_d=0.5,
        costs=np.asarray([1.0, 1.0, 1.0]),
    )

    assert vectors["gross"].tolist() == [4.0, -1.0, 1.0]
    assert vectors["net"].tolist() == [2.0, -3.0, -1.0]
    assert vectors["outcome"].tolist() == ["TARGET", "AMBIGUOUS", "HORIZON"]
    assert vectors["optimistic_gross"].tolist() == [4.0, 4.0, 1.0]


def test_decomposition_preserves_positive_offsets_and_complete_identity() -> None:
    rows = [
        _pool_row("a", side="LONG"),
        _pool_row("b", minute=1, side="SHORT"),
        {
            **_pool_row("c", minute=2, side="LONG"),
            "origin_family": "family_b",
        },
    ]
    arrays = {
        "gross": np.asarray([-2.0, -1.0, 0.5]),
        "cost": np.asarray([0.2, 0.2, 0.1]),
        "net": np.asarray([-2.2, -1.2, 0.4]),
    }

    result = fb.decomposition_rows(rows, arrays)

    assert sum(row["gross_sum_r"] for row in result) == pytest.approx(-2.5)
    assert sum(row["gross_deficit_contribution_r"] for row in result) == pytest.approx(2.5)
    assert sum(row["share_of_signed_total_gross_deficit"] for row in result) == pytest.approx(1.0)
    positive = next(row for row in result if row["family"] == "family_b")
    assert positive["gross_deficit_contribution_r"] == pytest.approx(-0.5)


def test_normalize_side_fails_closed_on_side_direction_disagreement() -> None:
    with pytest.raises(fb.FBRefusal, match="side_direction_disagreement"):
        fb.normalize_side({"side": "LONG", "direction": "SHORT"})

"""Focused tests for the learned-edge walk-forward acceptance gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.learned_edge_trainer import train_learned_edge_artifact
from src.research_infra.learned_edge_walkforward_gate import (
    GATE_SCHEMA_VERSION,
    evaluate_walkforward_gate,
    heuristic_admits,
    overlap_stats,
)

TRAIN_DAYS = [f"2026-03-{d:02d}" for d in (2, 3, 4, 5, 6, 9, 10, 11)]
VALIDATION_DAYS = [f"2026-03-{d:02d}" for d in (16, 17, 18, 19)]

EXPECTED_GATES = {
    "outcome_brier_max",
    "outcome_ece_max",
    "learned_admitted_net_r_ge_heuristic",
    "capture_ratio_min",
    "admitted_loser_rate_le_heuristic",
    "adds_information_overlap_max",
    "refusal_rate_max",
}


def _frame_row(idx: int, day: str, *, role: str, win: bool, signal: float,
               heur_admit: bool, symbol: str = "EURUSD") -> dict:
    # Mirrors tests/research_infra/test_learned_edge_trainer.py::_frame_row.
    # f_thesis_uncalibrated_probability is the informative feature; the
    # heuristic scores (f_heuristic_*) drive the static-floor comparator.
    return {
        "row_key": f"rk_{day}_{idx}",
        "candidate_id": f"cand_{day}_{idx}",
        "trading_day": day,
        "fold_key": day,
        "partition_role": role,
        "partition_trainable": role in ("TRAIN", "TRAIN_DEVELOPMENT_GRADE"),
        "label_span_start_utc": f"{day}T09:00:00+00:00",
        "label_span_end_utc": f"{day}T11:00:00+00:00",
        "label_span_status": "measured",
        "disposition": "selector_or_scheduler_missed",
        "label_fill": 1,
        "label_target_before_stop": 1 if win else 0,
        "label_net_r": 1.5 if win else -1.0,
        "label_outcome_valid": True,
        "label_truth_tier": "m1_proxy_clean",
        "weight_fill_head": 0.7,
        "weight_outcome_head": 0.7,
        "weight_duplicate_group": 1.0,
        "f_origin_family": "displacement_continuation",
        "f_symbol": symbol,
        "f_asset_class": "fx",
        "f_side": "LONG" if (idx // 7) % 2 == 0 else "SHORT",
        "f_session_bucket": "london",
        "f_utc_hour_bucket": "h07_08",
        "f_day_of_week": "mon",
        "f_dynamic_execution_policy_id": "policy_a",
        "f_disagreement_state": "low",
        "f_heuristic_probability": 0.7 if heur_admit else 0.5,
        "f_heuristic_ev_r": 0.2 if heur_admit else 0.05,
        "f_thesis_probability": 0.5,
        "f_thesis_uncalibrated_probability": signal,
        "f_thesis_uncertainty": 0.2,
        "f_thesis_missing_source_penalty": 0.05,
        "f_thesis_source_completeness": 0.8,
        "f_expected_cost_r": 0.12,
        "f_risk_reward_ratio": 1.5,
        "f_limit_offset_r": 0.1,
        "f_stop_distance_rel": 0.004,
        "f_n_competing_in_group": 1.0,
        "f_open_positions_seen": 0.0,
        "f_pending_orders_seen": 0.0,
    }


def _world_rows(days: list[str], *, role: str, start_idx: int = 0,
                invert: bool = False, heuristic_tracks_signal: bool = False) -> list[dict]:
    """Deterministic synthetic world.

    Signal-high rows (idx even) win 80% of the time; signal-low rows win 20%.
    The heuristic static floors admit an orthogonal third of rows
    (idx % 3 == 0) unless ``heuristic_tracks_signal`` makes them mimic the
    learned admissions. ``invert`` flips outcomes (anti-correlated world).
    """

    rows: list[dict] = []
    idx = start_idx
    for day in days:
        for _ in range(30):
            high = idx % 2 == 0
            follow = idx % 5 != 0
            win = high if follow else (not high)
            if invert:
                win = not win
            heur = high if heuristic_tracks_signal else (idx % 3 == 0)
            rows.append(
                _frame_row(idx, day, role=role, win=win,
                           signal=0.85 if high else 0.15, heur_admit=heur)
            )
            idx += 1
        # A few non-fills so the fill head has two classes.
        for _ in range(4):
            row = _frame_row(idx, day, role=role, win=False, signal=0.15,
                             heur_admit=False)
            row["label_fill"] = 0
            row["label_target_before_stop"] = 0
            row["label_net_r"] = None
            row["label_outcome_valid"] = False
            row["weight_outcome_head"] = 0.0
            rows.append(row)
            idx += 1
    return rows


def _write_frame(path: Path, rows: list[dict]) -> None:
    header = {"row_kind": "frame_header", "total_rows": len(rows)}
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(header) + "\n")
        for row in rows:
            handle.write(json.dumps(row) + "\n")


@pytest.fixture(scope="module")
def world(tmp_path_factory) -> dict:
    """Combined TRAIN+VALIDATION frame and a frozen artifact trained on TRAIN."""

    root = tmp_path_factory.mktemp("wf_gate_world")
    rows = _world_rows(TRAIN_DAYS, role="TRAIN") + _world_rows(
        VALIDATION_DAYS, role="VALIDATION", start_idx=10000
    )
    frame = root / "frame.jsonl"
    _write_frame(frame, rows)
    artifact = train_learned_edge_artifact(frame, repo_root=root)
    artifact_path = root / "artifact.json"
    artifact_path.write_text(json.dumps(artifact, default=str), encoding="utf-8")
    return {"root": root, "frame": frame, "artifact_path": artifact_path,
            "artifact": artifact}


@pytest.fixture(scope="module")
def anti_artifact_path(tmp_path_factory) -> Path:
    """Artifact trained on an ANTI-correlated world (signal flipped)."""

    root = tmp_path_factory.mktemp("wf_gate_anti")
    rows = _world_rows(TRAIN_DAYS, role="TRAIN", invert=True)
    frame = root / "anti_frame.jsonl"
    _write_frame(frame, rows)
    artifact = train_learned_edge_artifact(frame, repo_root=root)
    path = root / "anti_artifact.json"
    path.write_text(json.dumps(artifact, default=str), encoding="utf-8")
    return path


def _gate(report: dict, name: str) -> dict:
    matches = [g for g in report["gate_table"] if g["gate"] == name]
    assert len(matches) == 1, f"gate {name} missing or duplicated"
    return matches[0]


def test_gate_passes_in_well_separated_world(world, tmp_path):
    out = tmp_path / "gate_report.json"
    report = evaluate_walkforward_gate(
        world["frame"], world["artifact_path"], out_path=out
    )
    assert report["schema_version"] == GATE_SCHEMA_VERSION
    assert report["status"] == "evaluated"
    # All gate rows present exactly once.
    assert {g["gate"] for g in report["gate_table"]} == EXPECTED_GATES
    for gate in report["gate_table"]:
        assert set(gate) == {"gate", "value", "threshold", "pass"}
    # Calibration gates pass in the well-separated world.
    assert _gate(report, "outcome_brier_max")["pass"] is True
    assert _gate(report, "outcome_ece_max")["pass"] is True
    assert _gate(report, "refusal_rate_max")["pass"] is True
    assert report["refusals"]["count"] == 0
    # Economics: learned admissions beat the orthogonal heuristic floors.
    assert _gate(report, "learned_admitted_net_r_ge_heuristic")["pass"] is True
    assert _gate(report, "capture_ratio_min")["pass"] is True
    assert _gate(report, "admitted_loser_rate_le_heuristic")["pass"] is True
    assert _gate(report, "adds_information_overlap_max")["pass"] is True
    assert report["overall_pass"] is True
    # Fold table covers every validation day; pooled capture is meaningful.
    assert [f["fold_key"] for f in report["fold_table"]] == VALIDATION_DAYS
    assert report["pooled"]["capture_learned"]["capture_ratio"] > 0.5
    assert report["pbo"]["n_strategies"] == 2
    # Provenance + boundary stamps.
    assert report["artifact_hash_sha256"] == world["artifact"]["artifact_hash_sha256"]
    assert report["frame_header_sha256"]
    for stamp in ("broker_operation", "paid_api_or_vendor_call",
                  "broker_runtime_change_status", "validation_result_status",
                  "outcome_result_rows_status"):
        assert report[stamp] is False
    # Report written to disk and parseable.
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk["overall_pass"] is True


def test_anti_correlated_artifact_fails(world, anti_artifact_path):
    report = evaluate_walkforward_gate(world["frame"], anti_artifact_path)
    assert report["status"] == "evaluated"
    assert report["overall_pass"] is False
    # The anti-correlated model is badly calibrated against the true world...
    brier_gate = _gate(report, "outcome_brier_max")
    assert brier_gate["pass"] is False
    assert brier_gate["value"] > 0.24
    # ...and its admissions lose money relative to the heuristic floors.
    assert _gate(report, "learned_admitted_net_r_ge_heuristic")["pass"] is False
    assert _gate(report, "capture_ratio_min")["pass"] is False


def test_overlap_gate_fails_when_learned_mimics_heuristic(world, tmp_path):
    # Same validation world, but the heuristic floors now admit exactly the
    # signal-high rows the learned layer admits -> no added information.
    frame = tmp_path / "mimic_frame.jsonl"
    _write_frame(
        frame,
        _world_rows(VALIDATION_DAYS, role="VALIDATION", start_idx=10000,
                    heuristic_tracks_signal=True),
    )
    report = evaluate_walkforward_gate(frame, world["artifact_path"])
    overlap_gate = _gate(report, "adds_information_overlap_max")
    assert overlap_gate["pass"] is False
    assert overlap_gate["value"] >= 0.80
    assert report["overall_pass"] is False
    # Identical admission sets keep the relative gates passing: the failure
    # is isolated to incrementality.
    assert _gate(report, "outcome_brier_max")["pass"] is True
    assert _gate(report, "learned_admitted_net_r_ge_heuristic")["pass"] is True
    assert _gate(report, "admitted_loser_rate_le_heuristic")["pass"] is True


def test_overlap_stats_pure_function():
    stats = overlap_stats({"a", "b", "c"}, {"b", "c", "d"})
    assert stats["overlap_of_learned"] == pytest.approx(2 / 3)
    assert stats["jaccard"] == pytest.approx(2 / 4)
    assert stats["intersection_n"] == 2
    # Fail-closed: no learned admissions -> overlap not computable.
    empty = overlap_stats(set(), {"x"})
    assert empty["overlap_of_learned"] is None
    assert overlap_stats(set(), set())["jaccard"] is None


def test_heuristic_admission_floors():
    base = {"probability_feature": "f_heuristic_probability",
            "ev_feature": "f_heuristic_ev_r",
            "probability_floor": 0.58, "ev_floor": 0.10}
    assert heuristic_admits({"f_heuristic_probability": 0.60,
                             "f_heuristic_ev_r": 0.12}, base) is True
    assert heuristic_admits({"f_heuristic_probability": 0.57,
                             "f_heuristic_ev_r": 0.12}, base) is False
    assert heuristic_admits({"f_heuristic_probability": 0.60,
                             "f_heuristic_ev_r": 0.09}, base) is False
    # Fail closed on missing source.
    assert heuristic_admits({"f_heuristic_ev_r": 0.12}, base) is False


def test_corrupt_artifact_fails_closed_with_reason(world, tmp_path):
    corrupt = tmp_path / "corrupt_artifact.json"
    corrupt.write_text("{this is not json", encoding="utf-8")
    out = tmp_path / "refused_report.json"
    report = evaluate_walkforward_gate(world["frame"], corrupt, out_path=out)
    assert report["overall_pass"] is False
    assert report["status"] == "refused_fail_closed"
    assert report["failure_reason"].startswith("artifact_load_failed:")
    # Refused reports are still persisted with boundary stamps.
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk["overall_pass"] is False
    assert on_disk["broker_operation"] is False


def test_invalid_schema_artifact_fails_refusal_gate(world, tmp_path):
    wrong = tmp_path / "wrong_schema_artifact.json"
    wrong.write_text(json.dumps({"schema_version": "other"}), encoding="utf-8")
    report = evaluate_walkforward_gate(world["frame"], wrong)
    assert report["status"] == "evaluated"
    assert report["refusals"]["rate"] == 1.0
    assert "refused_artifact_invalid" in report["refusals"]["statuses"]
    refusal_gate = _gate(report, "refusal_rate_max")
    assert refusal_gate["pass"] is False
    assert report["overall_pass"] is False


def test_no_validation_rows_fails_closed(world, tmp_path):
    frame = tmp_path / "train_only_frame.jsonl"
    _write_frame(frame, _world_rows(TRAIN_DAYS[:1], role="TRAIN"))
    report = evaluate_walkforward_gate(frame, world["artifact_path"])
    assert report["overall_pass"] is False
    assert report["status"] == "refused_fail_closed"
    assert report["failure_reason"].startswith("no_validation_rows")

"""Focused tests for the learned edge trainer + pure-python scorer pair."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from src.components.learned_edge_layer_v4 import (
    ARTIFACT_SCHEMA_VERSION,
    artifact_validation_errors,
    score_learned_edge,
)
from src.research_infra.learned_edge_trainer import (
    _auc,
    _eb_target_encoding,
    _fit_beta_calibration,
    train_learned_edge_artifact,
)


def _frame_row(idx: int, day: str, *, win: bool, symbol: str = "EURUSD",
               strong_signal: float | None = None) -> dict:
    # f_thesis_uncalibrated_probability is the informative feature in this
    # synthetic world: high -> win, low -> loss.
    signal = strong_signal if strong_signal is not None else (0.8 if win else 0.2)
    return {
        "row_key": f"rk_{day}_{idx}",
        "candidate_id": f"cand_{day}_{idx}",
        "trading_day": day,
        "fold_key": day,
        "partition_role": "TRAIN",
        # Emitted by the fail-closed builder since 2026-07-29 (Session Z). The trainer
        # REFUSES a frame without these: `partition_trainable` because a frame that cannot
        # show it excluded SEALED/RESERVED days is not safe to fit, and the label span
        # because without it no purge is possible.
        "partition_trainable": True,
        "partition_id": "train_february_2026_unclaimed",
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
        # Decorrelated from the signal feature (idx parity) to avoid
        # collinearity between the categorical and numeric channels.
        "f_side": "LONG" if (idx // 7) % 2 == 0 else "SHORT",
        "f_session_bucket": "london",
        "f_utc_hour_bucket": "h07_08",
        "f_day_of_week": "mon",
        "f_dynamic_execution_policy_id": "policy_a",
        "f_disagreement_state": "low",
        "f_heuristic_probability": 0.5,
        "f_heuristic_ev_r": 0.1,
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


def _write_frame(path: Path, rows: list[dict]) -> None:
    header = {"row_kind": "frame_header", "total_rows": len(rows)}
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(header) + "\n")
        for row in rows:
            handle.write(json.dumps(row) + "\n")


@pytest.fixture()
def synthetic_frame(tmp_path) -> Path:
    # Feb 2026 weekdays. Wider than the original 8 days because the folds are now an
    # EXPANDING walk-forward with a purge and an embargo, not leave-one-day-out: the
    # early folds need a real past to train on. Feb 2026 is TRAIN in the partition
    # registry (train_february_2026_unclaimed).
    days = [f"2026-02-{d:02d}" for d in
            (2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27)]
    rows = []
    idx = 0
    for day in days:
        for _ in range(30):
            # 60% of high-signal rows win; 20% of low-signal rows win.
            win_signal = idx % 5 != 0      # 80% follow the signal
            high = idx % 2 == 0
            win = high if win_signal else (not high)
            rows.append(_frame_row(idx, day, win=win,
                                   strong_signal=0.85 if high else 0.15))
            idx += 1
        # a few non-fills so the fill head has two classes
        for j in range(4):
            row = _frame_row(1000 + idx + j, day, win=False)
            row["label_fill"] = 0
            row["label_target_before_stop"] = 0
            row["label_net_r"] = None
            row["label_outcome_valid"] = False
            row["weight_outcome_head"] = 0.0
            rows.append(row)
        idx += 4
    frame = tmp_path / "frame.jsonl"
    _write_frame(frame, rows)
    return frame


def test_train_produces_valid_artifact_and_scorer_roundtrip(synthetic_frame, tmp_path):
    artifact = train_learned_edge_artifact(synthetic_frame, repo_root=tmp_path)
    assert artifact["schema_version"] == ARTIFACT_SCHEMA_VERSION
    assert artifact_validation_errors(artifact) == []
    # The informative feature must dominate discriminative performance.
    outcome = artifact["training_diagnostics"]["outcome"]["pooled_oof_metrics"]
    assert outcome["auc"] > 0.65
    assert outcome["brier"] < 0.25
    # Canary recorded and inside tolerance.
    assert abs(artifact["leakage_canary"]["label_shuffle_auc"] - 0.5) <= 0.07
    # Scorer parity recorded as pass.
    assert artifact["scorer_parity_check"]["status"] == "pass"
    # Round-trip: a high-signal row scores higher than a low-signal row.
    hi = score_learned_edge(_frame_row(1, "2026-02-12", win=True, strong_signal=0.85), artifact)
    lo = score_learned_edge(_frame_row(2, "2026-02-12", win=False, strong_signal=0.15), artifact)
    assert hi["status"] == "scored" and lo["status"] == "scored"
    assert hi["probability"] > lo["probability"]
    assert hi["expected_net_r"] is not None and lo["expected_net_r"] is not None
    assert hi["expected_net_r"] > lo["expected_net_r"]


def test_scorer_refuses_stale_and_mismatched_artifacts(synthetic_frame, tmp_path):
    artifact = train_learned_edge_artifact(synthetic_frame, repo_root=tmp_path)
    stale = dict(artifact)
    stale["valid_through_utc"] = "2020-01-01T00:00:00+00:00"
    result = score_learned_edge(_frame_row(1, "2026-02-12", win=True), stale)
    assert result["status"] == "refused_artifact_invalid"
    assert any("artifact_stale" in e for e in result["errors"])

    mismatched = dict(artifact)
    mismatched["generator_code_sha"] = "deadbeef" * 5
    result = score_learned_edge(
        _frame_row(1, "2026-02-12", win=True),
        mismatched,
        expected_generator_sha="cafebabe" * 5,
    )
    assert result["status"] == "refused_artifact_invalid"
    assert any("generator_code_sha_mismatch" in e for e in result["errors"])

    wrong_schema = dict(artifact)
    wrong_schema["schema_version"] = "other"
    result = score_learned_edge(_frame_row(1, "2026-02-12", win=True), wrong_schema)
    assert result["status"] == "refused_artifact_invalid"


def test_eb_encoding_shrinks_small_levels():
    rows = (
        [{"f": "big", "y": 1, "w": 1.0}] * 80
        + [{"f": "big", "y": 0, "w": 1.0}] * 20
        + [{"f": "tiny", "y": 1, "w": 1.0}] * 2
        + [{"f": "other", "y": 0, "w": 1.0}] * 98
    )
    enc = _eb_target_encoding(rows, feature="f", label_key="y", weight_key="w", k=25.0)
    prior = enc["__prior__"]
    # big level (n=100, 80% win) sits well above prior; tiny level (n=2,
    # 100% win) is shrunk close to prior despite a perfect empirical rate.
    assert enc["big"] > prior + 0.5
    assert abs(enc["tiny"] - prior) < abs(enc["big"] - prior)


def test_beta_calibration_fixes_systematic_bias():
    # Predictions systematically over-confident: true rate is 0.5 when p=0.8.
    preds = [0.8] * 50 + [0.2] * 50
    labels = [1] * 25 + [0] * 25 + [1] * 25 + [0] * 25
    cal = _fit_beta_calibration(preds, labels)
    p = 0.8
    calibrated = 1.0 / (1.0 + math.exp(-(cal["a"] * math.log(p) - cal["b"] * math.log(1 - p) + cal["c"])))
    assert abs(calibrated - 0.5) < 0.1


def test_auc_helper():
    assert _auc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0
    assert _auc([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]) == 0.0
    assert abs(_auc([0.5, 0.5, 0.5, 0.5], [1, 0, 1, 0]) - 0.5) < 1e-9

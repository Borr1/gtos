"""End-to-end wiring tests for the geometry-bound outcome model in the
Wave 21 truth-mode timewarp path.

Both directions, behaviorally:

* With the explicit runtime supply (``wave21_geometry_bound_outcome_model``)
  and a valid hash-sealed artifact, a covered candidate flows to an ACCEPTED
  disposition -- packet attached, live packet hash-bound, quality fields
  truthful, authority allowed.
* With the key absent the refusal path is byte-identical to today (no model
  load is even attempted), and a broken supply fails loud rather than
  degrading to a silent refusal run.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

import src.research_infra.v4_timewarp_simulated_live_research_loop as timewarp
from src.components.live_decision_packet_v4 import validate_live_decision_packet_v4
from src.research_infra.geometry_bound_outcome_model import (
    EVALUATED_STATUS,
    fit_geometry_bound_outcome_model,
)
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    ResolvedSource,
    SourceSpec,
)
from src.research_infra.wave21_full_flow_truth import (
    GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON,
    GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS,
    PROBABILITY_TRUTH_STATUS,
)
from tests.research_infra.test_geometry_bound_outcome_model import (
    _LIMIT_FAMILIES,
    _PREREGISTRATION,
    _hand_count_corpus,
)
from tests.test_v4_timewarp_simulated_live_research_loop import (
    _source_safe_occurrence_candidate,
)


@pytest.fixture(scope="module")
def model_artifact(tmp_path_factory) -> tuple[dict, Path, str]:
    rows_by_day, corpus_days = _hand_count_corpus()
    model = fit_geometry_bound_outcome_model(
        rows_by_day,
        corpus_days=corpus_days,
        limit_origin_families=_LIMIT_FAMILIES,
        preregistration=_PREREGISTRATION,
        created_utc="2026-08-11T00:00:00Z",
    )
    path = tmp_path_factory.mktemp("w21-outcome-model") / "model.json"
    path.write_text(
        json.dumps(model, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    return model, path, hashlib.sha256(path.read_bytes()).hexdigest()


def _truth_scaffolding(monkeypatch) -> None:
    debate_record = {
        "schema_version": "probability_debate_team_engine_v4",
        "selected_action": "long",
        "theses": [
            {
                "action": "long",
                "probability": 0.91,
                "EV": 1.31,
                "confidence_calibration": {
                    "score": 0.91,
                    "calibrated_probability": 0.91,
                    "calibration_source_status": (
                        "runtime_reliability_prior_no_outcome_calibration_claim"
                    ),
                },
            }
        ],
    }

    class DebateDecision:
        def to_record(self):
            return copy.deepcopy(debate_record)

    monkeypatch.setattr(
        timewarp,
        "broker_calibrated_replay_cost_packet",
        lambda **_kwargs: {
            "status": "PASSED",
            "authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "total_cost_r": 0.04,
        },
    )
    monkeypatch.setattr(
        timewarp,
        "build_probability_context",
        lambda *_args, **_kwargs: {"base_probability": 0.91},
    )
    monkeypatch.setattr(
        timewarp,
        "evaluate_probability_debate_team_v4",
        lambda *_args, **_kwargs: DebateDecision(),
    )
    monkeypatch.setattr(
        timewarp,
        "build_lifecycle_packet",
        lambda **_kwargs: {"action": "new_position", "permitted_order_intent": False},
    )
    monkeypatch.setattr(
        timewarp,
        "dynamic_policy_router_record",
        lambda **_kwargs: {
            "selected_policy": "momentum_exhaustion",
            "execution_policy_id": "fixture-policy",
        },
    )
    monkeypatch.setattr(
        timewarp,
        "selected_policy_params_from_router_record",
        lambda _record: {"final_target_r": 2.0},
    )
    monkeypatch.setattr(
        timewarp, "scheduler_package_parity_fields", lambda _record: {}
    )
    monkeypatch.setattr(
        timewarp,
        "owner_approved_reconstructed_proxy_selected_policy_expected_net_fields",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("truth mode must not regenerate expected-net aliases")
        ),
    )
    monkeypatch.setattr(
        timewarp,
        "build_target_stop_geometry_v4_contract",
        lambda **_kwargs: {
            "status": "source_bound_geometry_contract_ready",
            "selected_policy": "momentum_exhaustion",
            "execution_policy_id": "fixture-policy",
            "source_event_hash_sha256": "b" * 64,
            "packet_hash_sha256": "b" * 64,
            "target_destination": {"final_target_r": 2.0},
            "final_target_r": 2.0,
        },
    )
    monkeypatch.setattr(
        timewarp,
        "canonicalize_candidate_geometry",
        lambda candidate, **_kwargs: dict(candidate),
    )
    monkeypatch.setattr(
        timewarp, "risk_pct_for_symbol", lambda *_args, **_kwargs: (0.25, "fixture")
    )
    monkeypatch.setattr(
        timewarp,
        "configured_runtime_risk_limits",
        lambda *_args, **_kwargs: {
            "portfolio_ceiling_pct": 2.0,
            "cluster_correlation_ceiling_pct": 1.0,
        },
    )


def _fixture_source(tmp_path: Path) -> ResolvedSource:
    return ResolvedSource(
        spec=SourceSpec(
            symbol="XAUUSD",
            mapped_symbol="XAUUSD",
            timeframe="M15",
            path=tmp_path / "source.csv",
            source_family="fixture",
            source_broker="FTMO",
            source_role="owner_authorized_research_hydration",
        ),
        rows=(),
        rows_by_day={},
        sha256="c" * 64,
        day_counts={},
        selected_status="fixture",
        min_required_rows_per_day=0,
    )


def _truth_config(extra_runtime: dict | None = None) -> dict:
    runtime = {
        "wave21_full_flow_truth_mode_enabled": True,
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": True,
        "selector_v4_live_activation_allowed": True,
        "selector_v4_min_broker_net_trade_ev_r": 0.10,
        "selector_v4_min_no_trade_ev_r": 0.02,
        "selector_v4_min_confluence_score": 0.15,
    }
    if extra_runtime:
        runtime.update(extra_runtime)
    return {"gtos_vnext_runtime": runtime}


def _covered_candidate() -> dict:
    candidate = _source_safe_occurrence_candidate(stop_loss=98.0)
    # The hand-count model covers displacement_continuation/moonshot_h00_01
    # (both already on the fixture candidate) with 140 MARKET fills.
    candidate["limit_first_expiry_utc"] = "2026-05-14T02:00:00+00:00"
    return candidate


def test_supplied_valid_model_yields_accepted_disposition_end_to_end(
    monkeypatch, tmp_path: Path, model_artifact
) -> None:
    model, model_path, file_sha = model_artifact
    _truth_scaffolding(monkeypatch)
    result = timewarp.evaluate_candidate_v4(
        candidate=_covered_candidate(),
        config=_truth_config(
            {
                "wave21_geometry_bound_outcome_model": {
                    "path": str(model_path),
                    "artifact_sha256": file_sha,
                }
            }
        ),
        source=_fixture_source(tmp_path),
        risk_pct=0.25,
        asof_utc="2026-05-14T00:00:00+00:00",
        mso={},
    )

    assert result["probability_truth_status"] == (
        GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS
    )
    assert result["probability_truth_reason"] == (
        GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON
    )
    assert result["probability_truth_economic_authority_allowed"] is True

    candidate_after = result["candidate_after_geometry"]
    wrapper = candidate_after["geometry_bound_outcome_calibration"]
    packet = wrapper["packet"]
    assert wrapper["disposition"]["economic_authority_allowed"] is True
    assert packet["probability_status"] == EVALUATED_STATUS
    assert packet["model_artifact_sha256"] == file_sha
    assert packet["model_payload_sha256"] == model["payload_sha256"]
    assert packet["geometry_contract_hash_sha256"] == "b" * 64
    assert packet["decision_action"] == "LONG"
    assert packet["cell"] == {
        "proposed_order_type": "MARKET",
        "origin_family": "displacement_continuation",
        "utc_session": "moonshot_h00_01",
    }
    strict = packet["p_target_before_stop_given_filled_terminal_target_or_stop"]
    assert (strict["numerator"], strict["denominator"]) == (81, 222)

    # The attached wrapper survives the terminal truth-mode strip because it
    # revalidates; nothing else probability-shaped does.
    assert (
        timewarp.strip_probability_economic_authority(candidate_after)[
            "geometry_bound_outcome_calibration"
        ]
        == wrapper
    )
    for forbidden in ("probability", "candidate_ev_r", "expected_net_r"):
        assert forbidden not in result

    # The accepted disposition rides the hash-bound live packet and the
    # quality surface echoes it truthfully.
    live_packet = result["live_decision_packet_v4"]
    assert validate_live_decision_packet_v4(live_packet) == []
    truth_group = live_packet["field_groups"]["probability_debate_numeric_theses"]
    assert truth_group["probability_truth_status"] == (
        GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS
    )
    assert truth_group["probability_truth_economic_authority_allowed"] is True
    quality = timewarp.candidate_decision_quality_fields(candidate_after, result)
    assert quality["probability_truth_status"] == (
        GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS
    )
    assert quality["probability_truth_economic_authority_allowed"] is True
    assert quality["candidate_decision_quality_alias_status"] == (
        "geometry_bound_outcome_probability_available_no_ev_admission"
    )

    # Tampering authority into the live packet without re-hashing is caught.
    tampered = copy.deepcopy(live_packet)
    tampered["field_groups"]["probability_debate_numeric_theses"][
        "probability_truth_reason"
    ] = "self_declared"
    assert "packet_hash_mismatch" in {
        issue["code"] for issue in validate_live_decision_packet_v4(tampered)
    }
    tampered_quality = timewarp.candidate_decision_quality_fields(
        {}, {"live_decision_packet_v4": tampered}
    )
    assert tampered_quality["probability_truth_status"] == PROBABILITY_TRUTH_STATUS
    assert tampered_quality["probability_truth_reason"] == (
        "hash_bound_probability_truth_disposition_invalid"
    )


def test_uncovered_cell_refuses_out_of_support_never_a_default(
    monkeypatch, tmp_path: Path
) -> None:
    # A LIMIT-only corpus: the fixture candidate's MARKET order-type root does
    # not exist in this model, so its cell is genuinely missing at every
    # hierarchy level and the disposition must refuse -- never default.
    from tests.research_infra.test_geometry_bound_outcome_model import _row

    rows_by_day = {
        "2025-12-01": [
            _row(
                f"limit-only-{index}",
                "2025-12-01",
                "current_fvg_fill",
                "london",
                status,
            )
            for index, status in enumerate(
                ["RESOLVED_NO_FILL"] * 40
                + ["RESOLVED_FILLED_TARGET"] * 30
                + ["RESOLVED_FILLED_STOP"] * 40
                + ["RESOLVED_FILLED_TIME_STOP"] * 10
            )
        ]
    }
    corpus_days = [
        {
            "trading_day": "2025-12-01",
            "window_id": "test_window",
            "compact_root": "/tmp/fixture/limit-only",
            "authority_root_sha256": "5" * 64,
            "source_manifest_root_sha256": "6" * 64,
        }
    ]
    limit_only = fit_geometry_bound_outcome_model(
        rows_by_day,
        corpus_days=corpus_days,
        limit_origin_families=_LIMIT_FAMILIES,
        preregistration=_PREREGISTRATION,
        created_utc="2026-08-11T00:00:00Z",
    )
    model_path = tmp_path / "limit-only-model.json"
    model_path.write_text(
        json.dumps(limit_only, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    file_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()

    _truth_scaffolding(monkeypatch)
    result = timewarp.evaluate_candidate_v4(
        candidate=_covered_candidate(),
        config=_truth_config(
            {
                "wave21_geometry_bound_outcome_model": {
                    "path": str(model_path),
                    "artifact_sha256": file_sha,
                }
            }
        ),
        source=_fixture_source(tmp_path),
        risk_pct=0.25,
        asof_utc="2026-05-14T00:00:00+00:00",
        mso={},
    )
    assert result["probability_truth_status"] == PROBABILITY_TRUTH_STATUS
    assert result["probability_truth_reason"] == (
        "geometry_bound_outcome_calibration_out_of_support"
    )
    assert result["probability_truth_economic_authority_allowed"] is False
    assert "geometry_bound_outcome_calibration" not in result[
        "candidate_after_geometry"
    ]


def test_absent_key_never_loads_a_model_and_keeps_refusal_path(
    monkeypatch, tmp_path: Path
) -> None:
    _truth_scaffolding(monkeypatch)
    monkeypatch.setattr(
        timewarp,
        "load_geometry_bound_outcome_model",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("model must not be loaded when the key is absent")
        ),
    )
    result = timewarp.evaluate_candidate_v4(
        candidate=_covered_candidate(),
        config=_truth_config(),
        source=_fixture_source(tmp_path),
        risk_pct=0.25,
        asof_utc="2026-05-14T00:00:00+00:00",
        mso={},
    )
    assert result["probability_truth_status"] == PROBABILITY_TRUTH_STATUS
    assert result["probability_truth_reason"] == (
        "geometry_bound_outcome_calibration_source_required"
    )
    assert result["probability_truth_economic_authority_allowed"] is False
    assert "geometry_bound_outcome_calibration" not in result[
        "candidate_after_geometry"
    ]


def test_wrong_artifact_sha_fails_loud_not_silent(
    monkeypatch, tmp_path: Path, model_artifact
) -> None:
    _model, model_path, _file_sha = model_artifact
    _truth_scaffolding(monkeypatch)
    with pytest.raises(ValueError, match="sha256 mismatch"):
        timewarp.evaluate_candidate_v4(
            candidate=_covered_candidate(),
            config=_truth_config(
                {
                    "wave21_geometry_bound_outcome_model": {
                        "path": str(model_path),
                        "artifact_sha256": "f" * 64,
                    }
                }
            ),
            source=_fixture_source(tmp_path),
            risk_pct=0.25,
            asof_utc="2026-05-14T00:00:00+00:00",
            mso={},
        )
    with pytest.raises(ValueError, match="incomplete"):
        timewarp.evaluate_candidate_v4(
            candidate=_covered_candidate(),
            config=_truth_config(
                {"wave21_geometry_bound_outcome_model": {"path": str(model_path)}}
            ),
            source=_fixture_source(tmp_path),
            risk_pct=0.25,
            asof_utc="2026-05-14T00:00:00+00:00",
            mso={},
        )


def test_candidate_supplied_accepted_wrapper_cannot_ride_through(
    monkeypatch, tmp_path: Path, model_artifact
) -> None:
    """A replayed previously-accepted wrapper on the candidate is dropped.

    Only the wiring's own disposition may place the calibration key; without
    the runtime supply the stamps are refusals, and a self-consistent wrapper
    smuggled on the candidate must not survive to the output surfaces.
    """

    model, _model_path, file_sha = model_artifact
    from src.research_infra.geometry_bound_outcome_model import (
        build_geometry_bound_outcome_calibration_packet,
    )
    from src.research_infra.wave21_full_flow_truth import (
        geometry_bound_outcome_calibration_disposition,
        is_preserved_geometry_bound_outcome_calibration,
    )

    packet = build_geometry_bound_outcome_calibration_packet(
        model,
        origin_family="displacement_continuation",
        utc_session="moonshot_h00_01",
        decision_action="LONG",
        decision_time_utc="2026-05-14T00:00:00+00:00",
        outcome_horizon_utc="2026-05-14T02:00:00+00:00",
        geometry_contract_hash_sha256="b" * 64,
        model_artifact_sha256=file_sha,
    )
    wrapper = {
        "packet": packet,
        "disposition": geometry_bound_outcome_calibration_disposition(
            packet,
            {"packet_hash_sha256": "b" * 64},
            expected_model_artifact_sha256=file_sha,
        ),
    }
    # The wrapper is self-consistent -- it would survive a bare strip -- yet
    # the wiring must still refuse to carry it without the runtime supply.
    assert is_preserved_geometry_bound_outcome_calibration(wrapper) is True

    _truth_scaffolding(monkeypatch)
    candidate = _covered_candidate()
    candidate["geometry_bound_outcome_calibration"] = wrapper
    result = timewarp.evaluate_candidate_v4(
        candidate=candidate,
        config=_truth_config(),
        source=_fixture_source(tmp_path),
        risk_pct=0.25,
        asof_utc="2026-05-14T00:00:00+00:00",
        mso={},
    )
    assert result["probability_truth_economic_authority_allowed"] is False
    assert "geometry_bound_outcome_calibration" not in result[
        "candidate_after_geometry"
    ]


def test_runtime_key_is_absent_from_every_committed_config() -> None:
    repo = Path(__file__).resolve().parents[1]
    config_paths = [repo / "config/agent_config.yaml"] + sorted(
        (repo / "config/profiles").glob("*.yaml")
    )
    assert config_paths, "config surfaces must exist"
    for path in config_paths:
        assert (
            "wave21_geometry_bound_outcome_model"
            not in path.read_text(encoding="utf-8")
        ), f"runtime supply key must stay out of committed config: {path}"

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROUTE = (
    ROOT
    / "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
BUILDER_PATH = ROUTE / "build_b7_5_extended_history_source_window_contract.py"


def load_builder():
    name = "build_b7_5_extended_history_source_window_contract"
    spec = importlib.util.spec_from_file_location(name, BUILDER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_gzip_jsonl(path: Path, rows: list[dict]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def member_rows() -> list[dict]:
    return [
        {
            "stable_member_axis_id": "member_axis:one",
            "source_axis_row_index": 1,
            "sleeve_id": "sleeve-one",
            "sleeve_type": "test",
            "framework": "framework-a",
            "origin_family": "origin-a",
            "normalized_symbol": "XAUUSD",
            "session_bucket": "london_broad",
            "side": "LONG",
            "combined_source_bound_signal_r": 4.5,
        },
        {
            "stable_member_axis_id": "member_axis:two",
            "source_axis_row_index": 2,
            "sleeve_id": "sleeve-two",
            "sleeve_type": "test",
            "framework": "framework-b",
            "origin_family": "origin-b",
            "normalized_symbol": "EURUSD",
            "session_bucket": "ny_broad",
            "side": "SHORT",
            "combined_source_bound_signal_r": -1.25,
        },
    ]


def selector_rows() -> list[dict]:
    return [
        {
            "candidate_id": "jan-one",
            "decision_asof_utc": "2026-01-01T08:00:00+00:00",
            "framework": "framework-a",
            "origin_family": "origin-a",
            "symbol": "XAUUSD",
            "session_bucket": "london_broad",
            "side": "LONG",
        },
        {
            "candidate_id": "apr-two",
            "decision_asof_utc": "2026-04-01T14:00:00+00:00",
            "framework": "framework-b",
            "origin_family": "origin-b",
            "symbol": "EURUSD",
            "session_bucket": "ny_broad",
            "side": "SHORT",
        },
    ]


def test_selector_dispositions_cover_every_axis_and_keep_absence_explicit(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    selector_path = tmp_path / "selector.jsonl.gz"
    write_gzip_jsonl(selector_path, selector_rows())
    windows = (
        {
            "window_id": "jan",
            "start_day": "2026-01-01",
            "end_day": "2026-01-01",
        },
        {
            "window_id": "apr",
            "start_day": "2026-04-01",
            "end_day": "2026-04-01",
        },
    )

    result = builder.selector_window_dispositions(
        members=member_rows(),
        selector_path=selector_path,
        windows=windows,
    )

    assert result["jan"]["summary"]["member_axis_disposition_rows"] == 2
    assert result["jan"]["summary"]["member_axes_present"] == 1
    assert result["jan"]["summary"]["member_axes_absent"] == 1
    assert result["jan"]["summary"][
        "window_present_member_axis_combined_source_bound_signal_r_non_additive"
    ] == 4.5
    assert result["apr"]["summary"][
        "window_present_member_axis_combined_source_bound_signal_r_non_additive"
    ] == -1.25
    assert result["jan"]["summary"]["window_available_source_bound_r"] == 4.5
    assert result["jan"]["summary"]["source_bound_r_additive_allowed"] is False
    assert result["jan"]["summary"][
        "executable_r_to_source_bound_r_percentage_allowed"
    ] is False
    assert all(
        row["combined_source_bound_signal_r_additive_allowed"] is False
        for row in result["jan"]["dispositions"]
    )
    assert {
        row["disposition"] for row in result["jan"]["dispositions"]
    } == {
        "selector_axis_present_in_window",
        "selector_axis_absent_in_window",
    }


def test_contract_is_deterministic_replay_free_and_fails_on_unmatched_axis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    monkeypatch.setattr(
        builder.harness,
        "ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS",
        2,
    )
    monkeypatch.setattr(
        builder.harness,
        "ULTIMATE_PACKAGE_EXPECTED_REGISTRY_ROWS",
        1,
    )
    members_path = tmp_path / "members.jsonl"
    selector_path = tmp_path / "selector.jsonl.gz"
    write_jsonl(members_path, member_rows())
    write_gzip_jsonl(selector_path, selector_rows())
    windows = (
        {
            "window_id": "jan",
            "start_day": "2026-01-01",
            "end_day": "2026-01-01",
        },
        {
            "window_id": "apr",
            "start_day": "2026-04-01",
            "end_day": "2026-04-01",
        },
    )
    shared = {
        "valid": True,
        "shared_execution_contract_digest_sha256": "a" * 64,
        "ultimate_package_runtime_input_contract": {"valid": True},
        "code_authority": [
            {"path": path, "sha256": "1" * 64}
            for path in sorted(builder.POSTRUN_PROOF_CONSUMER_CODE_PATHS)
        ],
        "missing_code_paths": [],
    }
    source_plans = {
        window["window_id"]: {
            "day_count": 1,
            "source_authority_plan": {
                "valid": True,
                "plan_digest_sha256": ("b" if index == 0 else "c") * 64,
            },
            "source_resolution_row_count": 1,
            "source_resolution_rows_digest_sha256": "d" * 64,
            "source_cache_cleanup_valid": True,
        }
        for index, window in enumerate(windows)
    }
    monkeypatch.setattr(builder, "shared_replay_execution_contract", lambda: shared)
    monkeypatch.setattr(
        builder,
        "source_authority_plans",
        lambda **_kwargs: source_plans,
    )
    monkeypatch.setattr(
        builder,
        "capacity_projection",
        lambda **_kwargs: {"valid": True, "status": "capacity_projection_passed"},
    )
    run_campaign_calls = []
    monkeypatch.setattr(
        builder.harness,
        "run_campaign",
        lambda **kwargs: run_campaign_calls.append(kwargs),
    )

    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = builder.build_contract(
        output_path=first_path,
        member_path=members_path,
        selector_path=selector_path,
        windows=windows,
    )
    second = builder.build_contract(
        output_path=second_path,
        member_path=members_path,
        selector_path=selector_path,
        windows=windows,
    )

    assert first["valid"] is True
    assert first["run_campaign_call_count"] == 0
    assert run_campaign_calls == []
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["contract_digest_sha256"] == second["contract_digest_sha256"]
    assert first["source_bound_signal_semantics"]["additive_allowed"] is False
    assert first["source_bound_signal_semantics"][
        "executable_r_percentage_allowed"
    ] is False
    assert first["pair_binding_payload"][
        "source_bound_signal_semantics_sha256"
    ] == builder.harness.stable_sha256(builder.SOURCE_BOUND_SIGNAL_SEMANTICS)
    partition = first["execution_contract_authority_partition"]
    assert partition["valid"] is True
    assert first["pair_binding_payload"][
        "behavioral_execution_contract_digest_sha256"
    ] == partition["behavioral_execution_contract_digest_sha256"]
    assert first["pair_binding_payload"][
        "postrun_proof_consumer_contract_digest_sha256"
    ] == partition["postrun_proof_consumer_contract_digest_sha256"]

    monkeypatch.setattr(
        builder,
        "capacity_projection",
        lambda **_kwargs: {
            "valid": False,
            "status": "capacity_projection_failed",
        },
    )
    capacity_limited = builder.build_contract(
        output_path=tmp_path / "capacity-limited.json",
        member_path=members_path,
        selector_path=selector_path,
        windows=windows,
    )
    assert capacity_limited["valid"] is True
    assert capacity_limited["new_replay_capacity_ready"] is False
    assert capacity_limited["replay_launch_claim"] is False

    unmatched = selector_rows()
    unmatched[0]["symbol"] = "GBPUSD"
    write_gzip_jsonl(selector_path, unmatched)
    failed = builder.build_contract(
        output_path=tmp_path / "failed.json",
        member_path=members_path,
        selector_path=selector_path,
        windows=windows,
    )
    assert failed["valid"] is False
    assert failed["windows"][0]["selector_disposition_valid"] is False


def test_behavioral_execution_digest_ignores_only_postrun_proof_consumer_drift() -> None:
    builder = load_builder()
    behavior_path = "src/components/selector_v4.py"
    proof_paths = sorted(builder.POSTRUN_PROOF_CONSUMER_CODE_PATHS)
    shared = {
        "schema": "shared",
        "code_authority": [
            {"path": behavior_path, "sha256": "a" * 64},
            *[
                {"path": path, "sha256": "b" * 64}
                for path in proof_paths
            ],
        ],
        "missing_code_paths": [],
        "effective_profile_config_hashes": {"profile": "c" * 64},
        "effective_profile_config_hash_semantics": {"projection": "test"},
        "config_file_hashes": {"config": "d" * 64},
        "ultimate_package_runtime_input_contract": {"valid": True},
        "active_replay_symbol_universe": ["XAUUSD"],
        "execution_options": {"chunk_size": 1},
        "window_identity_excluded_from_shared_digest": True,
        "broker_live_final_authority": {"live_broker_authority": False},
        "shared_execution_contract_digest_sha256": "e" * 64,
    }
    proof_drift = json.loads(json.dumps(shared))
    proof_drift["code_authority"][1]["sha256"] = "f" * 64
    behavior_drift = json.loads(json.dumps(shared))
    behavior_drift["code_authority"][0]["sha256"] = "0" * 64

    baseline = builder.execution_contract_authority_partition(shared)
    proof_changed = builder.execution_contract_authority_partition(proof_drift)
    behavior_changed = builder.execution_contract_authority_partition(
        behavior_drift
    )

    assert baseline["behavioral_execution_contract_digest_sha256"] == (
        proof_changed["behavioral_execution_contract_digest_sha256"]
    )
    assert baseline["postrun_proof_consumer_contract_digest_sha256"] != (
        proof_changed["postrun_proof_consumer_contract_digest_sha256"]
    )
    assert baseline["behavioral_execution_contract_digest_sha256"] != (
        behavior_changed["behavioral_execution_contract_digest_sha256"]
    )


def test_capacity_projection_uses_v258_bytes_and_preserves_reserve(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    (tmp_path / f"{builder.V258_PREFIX}_SUMMARY.json").write_bytes(b"x" * 190)
    windows = (
        {
            "window_id": "jan",
            "start_day": "2026-01-01",
            "end_day": "2026-01-02",
        },
        {
            "window_id": "apr",
            "start_day": "2026-04-01",
            "end_day": "2026-04-03",
        },
    )
    enough = builder.MINIMUM_POST_REPLAY_RESERVE_BYTES + 1000

    passed = builder.capacity_projection(windows=windows, free_bytes=enough)
    failed = builder.capacity_projection(windows=windows, free_bytes=1)

    assert passed["valid"] is True
    assert passed["planned_chunk_count_total"] == 5
    assert passed["v258_bytes_per_day_ceiling"] == 10
    assert passed["projected_retained_bytes_total"] == 50
    assert failed["valid"] is False


def test_b7_5_harness_requires_both_contract_hashes_before_source_resolution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    harness = builder.harness
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    monkeypatch.setattr(
        harness,
        "ultimate_package_runtime_input_contract",
        lambda: {"valid": True, "failure_reasons": []},
    )
    monkeypatch.setattr(
        harness,
        "broad_replay_shared_execution_contract",
        lambda **_kwargs: {
            "valid": True,
            "shared_execution_contract_digest_sha256": "a" * 64,
        },
    )
    source_resolution_calls = []

    class Resolver:
        def __init__(self, **_kwargs):
            source_resolution_calls.append("constructed")

    monkeypatch.setattr(harness, "BroadSourceResolver", Resolver)
    args = SimpleNamespace(
        output_prefix="BROAD_LIVE_AS_IF_REPLAY_B7_5_UNIT",
        use_native_h1=False,
        verbose=False,
        start="2026-01-01",
        end="2026-01-01",
        max_days=None,
        chunk_size=1,
        profiles=(harness.PROFILE_REPAIRED,),
        omit_candidate_ledger=True,
        omit_candidate_index_ledger=True,
        omit_packet_sidecar_ledger=True,
        compact_missed_ledger=True,
        compact_decision_ledger=True,
        compact_scorecard_ledger=True,
        candidate_ledger_packet_max_bytes=1024,
        scorecard_ledger_packet_max_bytes=4096,
        compact_scorecard_symbol_risk_config=True,
        scorecard_probe_row_limit=12,
        max_candidates_per_symbol_window=0,
        smoke_subset=False,
        gc_between_chunks=True,
        skip_tick_source=False,
        symbols=None,
        expected_shared_execution_contract_sha256=None,
        expected_source_plan_digest_sha256=None,
    )

    with pytest.raises(ValueError, match="b7_5_expected_contract_binding_missing"):
        harness._run_harness(args)
    assert source_resolution_calls == []

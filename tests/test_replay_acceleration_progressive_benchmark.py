from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_progressive_benchmark as progressive
from src.research_infra import replay_acceleration_progressive_benchmark_verifier as verifier


EXPECTED_SYMBOLS = tuple(sorted(progressive.timewarp.INCLUDED_SYMBOLS))


def test_prospective_two_day_receipt_is_allowlisted_and_outcome_blind() -> None:
    receipt = progressive.verify_prospective_selection_receipt(
        progressive.SELECTION_RECEIPT_PATH
    )

    assert receipt["prospectively_selected_days"] == ["2026-01-02", "2026-01-05"]
    assert receipt["source_structural_metadata_only"] is True
    assert receipt["treatment_output_fields_read"] == []
    assert receipt["forbidden_output_classes_read"] == []


def test_cross_symbol_barrier_requires_exact_all_24_surface() -> None:
    barrier = progressive.CrossSymbolBarrier(EXPECTED_SYMBOLS)
    roots = {symbol: progressive.stable_sha256({"symbol": symbol}) for symbol in EXPECTED_SYMBOLS}
    sealed = barrier.seal(roots)

    assert sealed["symbol_count"] == 24
    assert sealed["symbols"] == list(EXPECTED_SYMBOLS)
    with pytest.raises(progressive.ProgressiveBenchmarkError, match="cross_symbol_barrier_incomplete"):
        barrier.seal(dict(list(roots.items())[:-1]))


def test_candidate_projection_reads_only_allowlisted_structure() -> None:
    candidate = {
        "candidate_id": "opaque-id",
        "symbol": "XAUUSD",
        "origin_family": "structural-origin",
        "candle_open_utc": "2026-01-02T07:00:00+00:00",
        "entry_price": 123.0,
        "candidate_ev_r": 99.0,
        "probability": 0.99,
    }
    projection = progressive.project_candidate_structure(candidate)

    assert projection == {
        "candidate_id": "opaque-id",
        "symbol": "XAUUSD",
        "origin_family": "structural-origin",
        "candle_open_utc": "2026-01-02T07:00:00+00:00",
    }
    assert not (set(projection) & progressive.FORBIDDEN_ECONOMIC_FIELDS)


def test_stage_profiler_records_nested_fixed_schema_and_safe_counters() -> None:
    clock_values = iter((100, 120, 160, 220))
    resource_snapshots = (
            {
                "cpu_user_ns": 10,
                "cpu_system_ns": 20,
                "peak_rss_bytes": 100,
                "block_input_operations": 1,
                "block_output_operations": 2,
            },
            {
                "cpu_user_ns": 15,
                "cpu_system_ns": 25,
                "peak_rss_bytes": 110,
                "block_input_operations": 2,
                "block_output_operations": 3,
            },
            {
                "cpu_user_ns": 35,
                "cpu_system_ns": 45,
                "peak_rss_bytes": 130,
                "block_input_operations": 5,
                "block_output_operations": 7,
            },
            {
                "cpu_user_ns": 50,
                "cpu_system_ns": 70,
                "peak_rss_bytes": 140,
                "block_input_operations": 8,
                "block_output_operations": 11,
            },
    )
    resource_values = iter(resource_snapshots)
    profiler = progressive.ReplayStageProfiler(
        enabled=True,
        clock_ns=lambda: next(clock_values),
        resource_snapshot=lambda: next(resource_values),
    )

    with profiler.stage("startup"):
        profiler.count_call("config_load")
        with profiler.stage("source_slicing"):
            profiler.count_call("partition_slice", amount=2)
            profiler.count_output("source_rows", rows=3, byte_count=17)

    payload = profiler.to_payload()

    assert set(payload) == {
        "schema",
        "enabled",
        "clock",
        "stage_order",
        "stages",
        "call_counters",
        "output_counters",
        "timing_counters",
        "resource_bounds",
    }
    assert payload["schema"] == "gtos.replay_acceleration.stage_profile.v2"
    assert payload["clock"] == "perf_counter_ns"
    expected_stage_order = (
        "startup",
        "source_slicing",
        "snapshots",
        "market_state",
        "generation",
        "evaluation",
        "scheduler_risk",
        "path_oracle",
        "broker_mutation",
        "proof_emission",
        "archive_seal",
        "verification",
    )
    assert progressive.REPLAY_STAGE_ORDER == expected_stage_order
    assert payload["stage_order"] == list(expected_stage_order)
    assert [row["name"] for row in payload["stages"]] == list(
        progressive.REPLAY_STAGE_ORDER
    )
    assert payload["call_counters"] == {"config_load": 1, "partition_slice": 2}
    assert payload["output_counters"] == {
        "source_rows": {"rows": 3, "bytes": 17}
    }
    assert payload["timing_counters"] == {}
    by_name = {row["name"]: row for row in payload["stages"]}
    assert by_name["startup"]["entered_count"] == 1
    assert by_name["startup"]["wall_ns"] == 120
    assert by_name["startup"]["self_wall_ns"] == 80
    assert by_name["source_slicing"]["entered_count"] == 1
    assert by_name["source_slicing"]["wall_ns"] == 40
    assert by_name["source_slicing"]["self_wall_ns"] == 40
    assert by_name["source_slicing"]["output_rows"] == 3
    assert by_name["source_slicing"]["output_bytes"] == 17
    assert by_name["source_slicing"]["cpu_user_ns"] == 20
    assert by_name["source_slicing"]["cpu_system_ns"] == 20
    assert by_name["source_slicing"]["peak_rss_bytes"] == 130
    assert by_name["source_slicing"]["block_input_operations"] == 3
    assert by_name["source_slicing"]["block_output_operations"] == 4
    assert payload["resource_bounds"] == {
        "first": resource_snapshots[0],
        "last": resource_snapshots[-1],
    }


def test_stage_profiler_records_fixed_coarse_timings() -> None:
    clock_values = iter((100, 145, 200, 275))
    profiler = progressive.ReplayStageProfiler(
        enabled=True,
        clock_ns=lambda: next(clock_values),
    )

    candidate_started = profiler.start_timing()
    profiler.record_timing(
        "candidate_pipeline_total",
        started_ns=candidate_started,
    )
    candidate_started = profiler.start_timing()
    profiler.record_timing(
        "candidate_pipeline_total",
        started_ns=candidate_started,
    )

    payload = profiler.to_payload()

    assert payload["timing_counters"] == {
        "candidate_pipeline_total": {
            "entered_count": 2,
            "wall_ns": 120,
        }
    }
    with pytest.raises(
        progressive.ProgressiveBenchmarkError,
        match="stage_timing_name_not_allowlisted",
    ):
        profiler.record_timing("not_a_replay_block", started_ns=300)


def test_run_campaign_profiler_is_opt_in_and_preserves_legacy_result() -> None:
    campaign = progressive.timewarp.CampaignConfig(
        name="instrumentation-empty-campaign",
        phase="unit",
        days=(),
        pending_expiry_minutes=1,
        use_repaired_pending_expiry=False,
    )
    legacy = progressive.timewarp.run_campaign(
        campaign=campaign,
        config={},
        sources={},
        broker=progressive.timewarp.SimulatedBroker(),
    )
    profiler = progressive.ReplayStageProfiler(enabled=True)
    instrumented = progressive.timewarp.run_campaign(
        campaign=campaign,
        config={},
        sources={},
        broker=progressive.timewarp.SimulatedBroker(),
        stage_profiler=profiler,
    )

    assert set(instrumented) == set(legacy)
    assert instrumented["selected_order_sequence"] == legacy["selected_order_sequence"]
    assert instrumented["terminal_execution_truth_reconciliation"] == legacy[
        "terminal_execution_truth_reconciliation"
    ]
    assert dict(instrumented["ledgers"]) == dict(legacy["ledgers"])
    profile = profiler.to_payload()
    by_name = {row["name"]: row for row in profile["stages"]}
    assert by_name["startup"]["entered_count"] == 1
    assert by_name["proof_emission"]["entered_count"] == 1


def test_disabled_stage_profiler_is_a_true_no_op() -> None:
    def fail_if_sampled() -> int:
        raise AssertionError("disabled profiler sampled the clock")

    profiler = progressive.ReplayStageProfiler(
        enabled=False,
        clock_ns=fail_if_sampled,
        resource_snapshot=lambda: (_ for _ in ()).throw(
            AssertionError("disabled profiler sampled resources")
        ),
    )
    with profiler.stage("startup"):
        profiler.count_call("ignored")
        profiler.count_output("ignored", rows=1, byte_count=1)

    payload = profiler.to_payload()
    assert payload["enabled"] is False
    assert payload["call_counters"] == {}
    assert payload["output_counters"] == {}
    assert payload["resource_bounds"] == {"first": None, "last": None}
    assert all(row["entered_count"] == 0 for row in payload["stages"])


def _rooted_payload(payload: dict[str, object], root_field: str) -> dict[str, object]:
    rooted = dict(payload)
    rooted[root_field] = progressive.stable_sha256(rooted)
    return rooted


def _write_canonical(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(progressive.canonical_bytes(payload) + b"\n")


def _empty_source_identity_root() -> str:
    return progressive.stable_sha256([])


def _cache_manifest(source_identity_root: str) -> dict[str, object]:
    payload_root = progressive.stable_sha256({"cache": "sealed-payload"})
    payload: dict[str, object] = {
        "schema": progressive.FULL_REPLAY_CACHE_MANIFEST_SCHEMA,
        "sealed": True,
        "source_identity_root_sha256": source_identity_root,
        "payload_root_sha256": payload_root,
        "cache_identity_root_sha256": progressive.stable_sha256(
            {
                "schema": progressive.FULL_REPLAY_CACHE_MANIFEST_SCHEMA,
                "source_identity_root_sha256": source_identity_root,
                "payload_root_sha256": payload_root,
            }
        ),
    }
    return _rooted_payload(payload, "manifest_root_sha256")


def _cache_precondition(
    *,
    source_identity_root: str,
    cache_path: Path,
    launch_nonce: str,
    cache_manifest_path: Path | None = None,
    priming_receipt_path: Path | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": progressive.FULL_REPLAY_CACHE_PRECONDITION_SCHEMA,
        "source_identity_root_sha256": source_identity_root,
        "cache_path": cache_path.as_posix(),
        "cache_manifest_path": (
            cache_manifest_path.as_posix()
            if cache_manifest_path is not None
            else None
        ),
        "cache_manifest_file_sha256": (
            hashlib.sha256(cache_manifest_path.read_bytes()).hexdigest()
            if cache_manifest_path is not None
            else None
        ),
        "priming_receipt_path": (
            priming_receipt_path.as_posix()
            if priming_receipt_path is not None
            else None
        ),
        "priming_receipt_file_sha256": (
            hashlib.sha256(priming_receipt_path.read_bytes()).hexdigest()
            if priming_receipt_path is not None
            else None
        ),
        "launch_nonce_sha256": hashlib.sha256(
            launch_nonce.encode("ascii")
        ).hexdigest(),
    }
    return _rooted_payload(payload, "precondition_root_sha256")


def _priming_receipt(
    *,
    source_identity_root: str,
    cache_manifest: dict[str, object],
    cache_manifest_file_sha256: str,
    launch_nonce: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": progressive.FULL_REPLAY_PRIMING_RECEIPT_SCHEMA,
        "status": "COMPLETE",
        "source_identity_root_sha256": source_identity_root,
        "cache_identity_root_sha256": cache_manifest[
            "cache_identity_root_sha256"
        ],
        "cache_manifest_file_sha256": cache_manifest_file_sha256,
        "benchmark_receipt_root_sha256": "b" * 64,
        "benchmark_result_root_sha256": "c" * 64,
        "measurement_process": {
            "pid": 101,
            "parent_pid": 100,
            "launch_nonce_sha256": hashlib.sha256(
                launch_nonce.encode("ascii")
            ).hexdigest(),
        },
    }
    return _rooted_payload(payload, "receipt_root_sha256")


def _recursive_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            nested
            for child in value.values()
            for nested in _recursive_keys(child)
        }
    if isinstance(value, list):
        return {
            nested
            for child in value
            for nested in _recursive_keys(child)
        }
    return set()


def test_bounded_full_replay_benchmark_returns_only_outcome_blind_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    campaign = progressive.timewarp.CampaignConfig(
        name="bounded-full-replay-fixture",
        phase="unit",
        days=(),
        pending_expiry_minutes=1,
        use_repaired_pending_expiry=False,
    )
    launch_nonce = "1" * 64
    monkeypatch.setattr(
        progressive,
        "_FULL_REPLAY_PROCESS_LAUNCH_NONCE",
        launch_nonce,
    )
    source_identity_root = _empty_source_identity_root()
    precondition = _cache_precondition(
        source_identity_root=source_identity_root,
        cache_path=tmp_path / "absent-derived-cache",
        launch_nonce=launch_nonce,
    )

    class StubBroker:
        def mutation_boundary(self) -> dict[str, object]:
            return {
                "broker_mutation_enabled": False,
                "balance": 10_000.0,
                "pnl": 17.0,
            }

    raw_result = {
        "account": {"balance": 10_000.0, "r_total": 4.5},
        "broker": StubBroker(),
        "ledgers": {
            "orders": [
                {"candidate_id": "opaque", "pnl": 17.0, "cost_r": 0.25}
            ]
        },
        "selected_order_sequence": 1,
        "terminal_execution_truth_reconciliation": {
            "pnl": 17.0,
            "r_total": 4.5,
        },
    }
    monkeypatch.setattr(
        progressive.timewarp,
        "run_campaign",
        lambda **_: raw_result,
    )

    receipt = progressive.run_bounded_full_replay_benchmark(
        campaign=campaign,
        config={},
        sources={},
        cache_precondition=precondition,
    )

    assert isinstance(receipt, dict)
    assert receipt["schema"] == (
        "gtos.replay_acceleration.bounded_full_replay_benchmark.v1"
    )
    assert receipt["status"] == "MEASURED_PARITY_PENDING"
    assert receipt["cache_state"] == "derived_cold"
    assert receipt["cache_state_contract"] == {
        "derived_cache_preexisting": False,
        "fresh_process_required": True,
        "warm_filesystem_expected": False,
    }
    assert receipt["measurement"]["end_to_end_wall_ns"] > 0
    assert receipt["measurement"]["stage_profile"]["schema"] == (
        "gtos.replay_acceleration.stage_profile.v2"
    )
    assert receipt["output"] == {
        "ledger_role_counts": {"orders": 1},
        "ledger_row_count": 1,
        "canonical_bytes": receipt["output"]["canonical_bytes"],
        "result_root_sha256": receipt["output"]["result_root_sha256"],
    }
    assert receipt["output"]["canonical_bytes"] > 0
    assert len(receipt["output"]["result_root_sha256"]) == 64
    assert receipt["parity_status"] == "NOT_EVALUATED"
    assert receipt["economic_values_exposed"] is False
    assert receipt["receipt_root_sha256"]
    forbidden = progressive.FORBIDDEN_ECONOMIC_FIELDS | {
        "account",
        "broker",
        "ledgers",
        "terminal_execution_truth_reconciliation",
    }
    assert not (_recursive_keys(receipt) & forbidden)

    persisted = tmp_path / "benchmark-receipt.json"
    _write_canonical(persisted, receipt)
    reloaded = json.loads(persisted.read_bytes())
    assert not (_recursive_keys(reloaded) & forbidden)


def test_full_replay_cache_state_is_derived_not_caller_labeled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assert "cache_state" not in inspect.signature(
        progressive.run_bounded_full_replay_benchmark
    ).parameters
    launch_nonce = "2" * 64
    monkeypatch.setattr(
        progressive,
        "_FULL_REPLAY_PROCESS_LAUNCH_NONCE",
        launch_nonce,
    )
    precondition = _cache_precondition(
        source_identity_root=_empty_source_identity_root(),
        cache_path=tmp_path / "same-absent-cache",
        launch_nonce=launch_nonce,
    )

    evidence = progressive.verify_full_replay_cache_precondition(
        precondition,
        expected_source_identity_root=_empty_source_identity_root(),
    )
    assert evidence["cache_state"] == "derived_cold"

    for claimed_state in progressive.FULL_REPLAY_CACHE_STATE_CONTRACTS:
        relabeled = dict(precondition)
        relabeled["cache_state"] = claimed_state
        relabeled.pop("precondition_root_sha256")
        relabeled = _rooted_payload(relabeled, "precondition_root_sha256")
        with pytest.raises(
            progressive.ProgressiveBenchmarkError,
            match="full_replay_cache_precondition_schema_invalid",
        ):
            progressive.verify_full_replay_cache_precondition(
                relabeled,
                expected_source_identity_root=_empty_source_identity_root(),
            )


def test_sealed_cache_cold_process_requires_fresh_launch_and_exact_cache_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_identity_root = _empty_source_identity_root()
    manifest = _cache_manifest(source_identity_root)
    manifest_path = tmp_path / "cache" / "manifest.json"
    _write_canonical(manifest_path, manifest)
    launch_nonce = "3" * 64
    precondition = _cache_precondition(
        source_identity_root=source_identity_root,
        cache_path=manifest_path.parent,
        cache_manifest_path=manifest_path,
        launch_nonce=launch_nonce,
    )

    monkeypatch.setattr(
        progressive,
        "_FULL_REPLAY_PROCESS_LAUNCH_NONCE",
        None,
    )
    with pytest.raises(
        progressive.ProgressiveBenchmarkError,
        match="full_replay_fresh_process_evidence_missing",
    ):
        progressive.verify_full_replay_cache_precondition(
            precondition,
            expected_source_identity_root=source_identity_root,
        )

    monkeypatch.setattr(
        progressive,
        "_FULL_REPLAY_PROCESS_LAUNCH_NONCE",
        launch_nonce,
    )
    wrong_identity = dict(precondition)
    wrong_identity["cache_manifest_file_sha256"] = "0" * 64
    wrong_identity.pop("precondition_root_sha256")
    wrong_identity = _rooted_payload(
        wrong_identity,
        "precondition_root_sha256",
    )
    with pytest.raises(
        progressive.ProgressiveBenchmarkError,
        match="full_replay_cache_manifest_file_sha256_mismatch",
    ):
        progressive.verify_full_replay_cache_precondition(
            wrong_identity,
            expected_source_identity_root=source_identity_root,
        )

    evidence = progressive.verify_full_replay_cache_precondition(
        precondition,
        expected_source_identity_root=source_identity_root,
    )
    assert evidence["cache_state"] == "sealed_cache_cold_process"
    assert evidence["fresh_process_verified"] is True
    assert evidence["cache_identity_root_sha256"] == manifest[
        "cache_identity_root_sha256"
    ]
    assert evidence["cache_manifest_file_sha256"] == hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()


def test_warm_filesystem_requires_authenticated_matching_priming_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_identity_root = _empty_source_identity_root()
    manifest = _cache_manifest(source_identity_root)
    manifest_path = tmp_path / "cache" / "manifest.json"
    _write_canonical(manifest_path, manifest)
    manifest_file_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    priming = _priming_receipt(
        source_identity_root=source_identity_root,
        cache_manifest=manifest,
        cache_manifest_file_sha256=manifest_file_sha256,
        launch_nonce="4" * 64,
    )
    priming_path = tmp_path / "priming.json"
    _write_canonical(priming_path, priming)
    launch_nonce = "5" * 64
    monkeypatch.setattr(
        progressive,
        "_FULL_REPLAY_PROCESS_LAUNCH_NONCE",
        launch_nonce,
    )
    precondition = _cache_precondition(
        source_identity_root=source_identity_root,
        cache_path=manifest_path.parent,
        cache_manifest_path=manifest_path,
        priming_receipt_path=priming_path,
        launch_nonce=launch_nonce,
    )

    mismatched_priming = dict(priming)
    mismatched_priming["source_identity_root_sha256"] = "9" * 64
    mismatched_priming.pop("receipt_root_sha256")
    mismatched_priming = _rooted_payload(
        mismatched_priming,
        "receipt_root_sha256",
    )
    _write_canonical(priming_path, mismatched_priming)
    mismatched_precondition = _cache_precondition(
        source_identity_root=source_identity_root,
        cache_path=manifest_path.parent,
        cache_manifest_path=manifest_path,
        priming_receipt_path=priming_path,
        launch_nonce=launch_nonce,
    )
    with pytest.raises(
        progressive.ProgressiveBenchmarkError,
        match="full_replay_priming_source_identity_mismatch",
    ):
        progressive.verify_full_replay_cache_precondition(
            mismatched_precondition,
            expected_source_identity_root=source_identity_root,
        )

    _write_canonical(priming_path, priming)
    precondition = _cache_precondition(
        source_identity_root=source_identity_root,
        cache_path=manifest_path.parent,
        cache_manifest_path=manifest_path,
        priming_receipt_path=priming_path,
        launch_nonce=launch_nonce,
    )
    evidence = progressive.verify_full_replay_cache_precondition(
        precondition,
        expected_source_identity_root=source_identity_root,
    )
    assert evidence["cache_state"] == "warm_filesystem"
    assert evidence["priming_receipt_root_sha256"] == priming[
        "receipt_root_sha256"
    ]
    assert evidence["priming_source_identity_root_sha256"] == (
        source_identity_root
    )
    assert evidence["priming_cache_identity_root_sha256"] == manifest[
        "cache_identity_root_sha256"
    ]


def test_full_replay_instrumentation_has_every_required_active_stage_hook() -> None:
    campaign_source = inspect.getsource(progressive.timewarp.run_campaign)
    candidate_helper_source = inspect.getsource(
        progressive.timewarp.evaluate_symbol_candidates_with_batched_proof_hashes
    )
    campaign_and_candidate_source = campaign_source + candidate_helper_source
    feed_source = inspect.getsource(progressive.timewarp.ReplayFeed.snapshot)
    benchmark_source = inspect.getsource(
        progressive.run_bounded_full_replay_benchmark
    )

    for stage in (
        "startup",
        "source_slicing",
        "generation",
        "evaluation",
        "scheduler_risk",
        "path_oracle",
        "broker_mutation",
        "proof_emission",
    ):
        assert f'stage_profiler, "{stage}"' in campaign_and_candidate_source
    for stage in ("snapshots", "market_state"):
        assert f'stage_profiler, "{stage}"' in feed_source
    for stage in ("archive_seal", "verification"):
        assert f'profiler.stage("{stage}")' in benchmark_source


def test_worker_contract_parallelizes_only_immutable_prebarrier_stage() -> None:
    progressive.validate_worker_count(1, "candidate_generation")
    progressive.validate_worker_count(2, "immutable_partition_verification")
    with pytest.raises(progressive.ProgressiveBenchmarkError, match="worker_count_not_legal"):
        progressive.validate_worker_count(2, "candidate_generation")


def test_normalized_schema_preserves_h1_derivation_width() -> None:
    base = {"close", "high", "low", "open", "symbol", "time", "time_utc", "volume"}

    assert progressive.normalized_row_keys("M15") == base
    assert progressive.normalized_row_keys("H1") == base | {"source_records"}


def test_read_only_config_disables_pipeline_and_shadow_log_writes() -> None:
    original = {"market_state": {"detector_version": "v2_shadow"}}

    sanitized = progressive.read_only_replay_config(original)

    assert original == {"market_state": {"detector_version": "v2_shadow"}}
    assert sanitized["market_state"]["detector_version"] == "v2_shadow"
    assert sanitized["market_state"]["side_effect_writes_enabled"] is False
    assert sanitized["market_state"]["structure_shadow_log_enabled"] is False


def test_progressive_failure_matrix_names_required_rejections() -> None:
    verdicts = progressive.run_failure_injection_contract_probe()

    assert len(verdicts) >= 13
    assert {row["status"] for row in verdicts} == {"REJECTED_AS_REQUIRED"}
    assert {
        "bit_flip",
        "truncation",
        "append",
        "partition_reorder",
        "source_mismatch",
        "normalized_manifest_mismatch",
        "config_mismatch",
        "code_mismatch",
        "stale_cache",
        "interruption_before_seal",
        "interruption_after_seal",
        "barrier_missing_symbol",
        "day_reorder",
    }.issubset({row["case"] for row in verdicts})


def test_persisted_progressive_result_is_verified_independently() -> None:
    result_path = (
        progressive.OUTPUT_DIR / "PROGRESSIVE_EQUIVALENCE_RESULT.json"
    )
    if not result_path.exists():
        pytest.skip("result is materialized by the measured integration command")

    receipt = verifier.verify_progressive_result(result_path)
    result = json.loads(result_path.read_bytes())
    assert receipt["status"] == "VERIFIED"
    assert receipt["result_root_sha256"] == result["result_root_sha256"]
    assert result["policy_execution_entered"] is False
    assert result["successor_arm_execution_launched"] is False
    assert result["whole_replay_claim"] is False


def test_independent_verifier_rejects_persisted_result_tamper(tmp_path: Path) -> None:
    result_path = progressive.OUTPUT_DIR / "PROGRESSIVE_EQUIVALENCE_RESULT.json"
    if not result_path.exists():
        pytest.skip("result is materialized by the measured integration command")
    tampered = json.loads(result_path.read_bytes())
    tampered["policy_execution_entered"] = True
    target = tmp_path / "tampered.json"
    target.write_text(json.dumps(tampered) + "\n", encoding="ascii")
    with pytest.raises(verifier.VerificationError):
        verifier.verify_progressive_result(target)


def test_independent_verifier_measures_its_persisted_byte_pass() -> None:
    result_path = progressive.OUTPUT_DIR / "PROGRESSIVE_EQUIVALENCE_RESULT.json"
    if not result_path.exists():
        pytest.skip("result is materialized by the measured integration command")

    receipt = verifier.verify_progressive_result_measured(result_path)
    measurement = receipt["verification_measurement"]
    assert measurement["wall_seconds"] > 0
    assert measurement["cpu_user_seconds"] >= 0
    assert measurement["cpu_system_seconds"] >= 0
    assert measurement["peak_rss_bytes"] > 0
    assert measurement["explicit_bytes_read"] > 0
    assert receipt["receipt_root_sha256"]

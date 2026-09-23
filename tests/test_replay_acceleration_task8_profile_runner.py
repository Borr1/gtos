from __future__ import annotations

import json
import threading
import time
from argparse import Namespace
from contextlib import nullcontext
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_task8_profile_runner as task8
from src.research_infra import replay_acceleration_progressive_benchmark as progressive


def test_task8_profile_args_consume_exact_factor_neutral_jan1_2_packs(
    tmp_path: Path,
) -> None:
    args = task8.task8_args(tmp_path / "profile")

    assert args.engineering_stop_after_day == "2026-01-02"
    assert args.build_prepared_day_pack_root is None
    assert args.prepared_day_pack_root == task8.task7.TASK6_CORRECTED_PACK_ROOT
    assert args.expected_prepared_day_pack_roots == task8.TASK8_PACK_ROOTS
    assert args.arm_id == "S0R0"
    assert args.expected_arm_fingerprint_sha256 == task8.semantic.EXPECTED_ARM_FINGERPRINT
    assert args.tick_sparse_cache_root == task8.replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
    assert args.tick_sparse_cache_window_end_after_day == "2026-01-02"


def test_task8_sampling_profiler_captures_target_thread_without_trace_hooks() -> None:
    profiler = task8.SamplingProfiler(
        target_thread_id=threading.get_ident(),
        interval_seconds=0.001,
    )
    profiler.start()
    deadline = time.monotonic() + 0.08
    value = 0
    while time.monotonic() < deadline:
        value = (value * 33 + 17) % 1_000_003
    profiler.stop()

    receipt = profiler.receipt()
    assert value >= 0
    assert receipt["sample_count"] > 0
    assert any(
        "test_task8_sampling_profiler_captures_target_thread_without_trace_hooks"
        in row["frame"]
        for row in receipt["top_leaf_functions"]
    )
    assert profiler.collapsed_bytes()


def test_task8_profile_path_rendering_resolves_each_filename_once() -> None:
    task8._render_profile_path.cache_clear()
    filename = str(Path(task8.__file__))

    first = task8._frame_label(filename, "first_function", 10)
    second = task8._frame_label(filename, "second_function", 20)

    assert first.endswith(":10:first_function")
    assert second.endswith(":20:second_function")
    assert task8._render_profile_path.cache_info().misses == 1
    assert task8._render_profile_path.cache_info().hits == 1


def test_task8_sampling_profiler_checkpoints_before_completion(tmp_path: Path) -> None:
    checkpoint = tmp_path / "sampling.partial.json"
    profiler = task8.SamplingProfiler(
        target_thread_id=threading.get_ident(),
        interval_seconds=0.001,
        checkpoint_path=checkpoint,
        checkpoint_interval_seconds=0.01,
    )
    profiler.start()
    deadline = time.monotonic() + 0.08
    while time.monotonic() < deadline:
        pass
    profiler.stop()

    payload = json.loads(checkpoint.read_bytes())
    core = {
        key: value
        for key, value in payload.items()
        if key != "checkpoint_root_sha256"
    }
    assert payload["status"] == "TASK8_SAMPLING_PROFILE_IN_PROGRESS"
    assert payload["checkpoint_sequence"] >= 1
    assert payload["sampling_profile"]["sample_count"] > 0
    assert payload["acceptance_authorized"] is False
    assert payload["checkpoint_root_sha256"] == task8.replay.stable_sha256(core)


def test_task8_existing_output_fails_before_profile_launch(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()

    with pytest.raises(task8.Task8ProfileRejected, match="task8_output_dir_must_be_new"):
        task8.run_task8_profile(output)


def test_task8_exact_execution_accepts_read_only_complete_cache_and_stage_profiler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "trial"
    shared_cache = tmp_path / "sealed-cache"
    shared_cache.mkdir()
    class StageProfiler:
        def stage(self, _name: str):
            return nullcontext()

    stage_profiler = StageProfiler()
    observed: dict[str, object] = {}
    args = Namespace(source_acceleration_cache_root=output / "typed-cache")

    monkeypatch.setattr(task8, "task8_args", lambda _output: args)
    monkeypatch.setattr(task8.replay, "bind_attempt5_finalizer_conflict_key_order", lambda: None)
    monkeypatch.setattr(
        task8.replay,
        "configure_runtime_evidence_root",
        lambda _root: {"contract_root_sha256": "a" * 64},
    )
    monkeypatch.setattr(
        task8.replay,
        "source_bundle_consumer_rebind_authority_from_args",
        lambda _args: {"binding_root_sha256": "b" * 64},
    )

    def configure_namespace(path: Path) -> Path:
        path.mkdir()
        return path

    monkeypatch.setattr(task8.replay, "configure_output_namespace", configure_namespace)
    monkeypatch.setattr(task8.semantic, "bind_source_acceleration_authority", lambda _args: None)
    monkeypatch.setattr(
        task8.task6,
        "_bind_current_shared_contract",
        lambda _args: {"shared_execution_contract_digest_sha256": "c" * 64},
    )

    def run_engine(received: Namespace) -> dict:
        observed["cache"] = received.source_acceleration_cache_root
        observed["profiler"] = received.replay_stage_profiler
        return {"progress_rows": []}

    monkeypatch.setattr(task8.replay, "run_replay_engine", run_engine)
    monkeypatch.setattr(
        task8,
        "_validate_profiled_execution",
        lambda _partial, *, namespace: {"namespace": str(namespace)},
    )
    monkeypatch.setattr(
        task8.task7,
        "_seed_private_typed_cache",
        lambda _destination: pytest.fail("shared cache must not be copied or seeded"),
    )

    result = task8.run_task8_exact_execution(
        output,
        typed_cache_authority_root=shared_cache,
        stage_profiler=stage_profiler,
    )

    assert observed == {"cache": shared_cache, "profiler": stage_profiler}
    assert result["typed_cache_seed"] is None
    assert result["namespace"] == output
    assert result["parity"] == {"namespace": str(output)}


def test_task8_stage_profile_runs_from_module_backed_entrypoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "stage-profile"

    class StageProfiler:
        def to_payload(self) -> dict:
            return {
                "schema": "gtos.replay_acceleration.stage_profile.v1",
                "enabled": True,
                "stages": [{"name": "evaluation", "wall_ns": 123}],
            }

    profiler = StageProfiler()
    monkeypatch.setattr(
        progressive,
        "ReplayStageProfiler",
        lambda *, enabled: profiler,
    )

    def run_exact(
        output_dir: Path,
        *,
        stage_profiler: object,
    ) -> dict:
        assert output_dir == output
        assert stage_profiler is profiler
        output.mkdir()
        return {
            "namespace": output,
            "runtime_contract": {"contract_root_sha256": "a" * 64},
            "shared_contract": {
                "shared_execution_contract_digest_sha256": "b" * 64,
            },
            "partial": {
                "progress_rows": [
                    {
                        "start_day": task8.DAY1,
                        "end_day": task8.DAY1,
                        "economic_hot_path_seconds": 1.0,
                        "proof_finalization_seconds": 2.0,
                        "summary": {"candidate_rows": 0, "filled_trades": 0},
                        "compact_event_sink": {
                            "authority": {
                                "authority_root_sha256": "c" * 64,
                                "manifest_sha256": "d" * 64,
                                "row_counts": {"decision": 1},
                                "raw_byte_counts": {"decision": 2},
                            }
                        },
                    },
                    {
                        "start_day": task8.DAY2,
                        "end_day": task8.DAY2,
                        "economic_hot_path_seconds": 3.0,
                        "proof_finalization_seconds": 4.0,
                        "summary": {"candidate_rows": 5, "filled_trades": 1},
                        "compact_event_sink": {
                            "authority": {
                                "authority_root_sha256": "e" * 64,
                                "manifest_sha256": "f" * 64,
                                "row_counts": {"decision": 6},
                                "raw_byte_counts": {"decision": 7},
                            }
                        },
                    },
                ]
            },
            "parity": {
                "status": "TASK8_PROFILED_EXECUTION_TASK6_SEMANTIC_PARITY",
                "days": {
                    task8.DAY1: {"projection_root_sha256": "1" * 64},
                    task8.DAY2: {"projection_root_sha256": "2" * 64},
                },
                "meaningful_difference_count": 0,
                "unknown_difference_count": 0,
                "tick_sparse_cache_raw_source_full_hash_count": 0,
                "tick_sparse_cache_sealed_reuse_count": 24,
            },
            "engine_wall_seconds": 10.0,
            "engine_cpu_seconds": 9.0,
            "parity_verification_seconds": 1.0,
        }

    monkeypatch.setattr(task8, "run_task8_exact_execution", run_exact)

    receipt_path = task8.run_task8_stage_profile(output)
    payload = json.loads(receipt_path.read_bytes())

    assert receipt_path == output / task8.STAGE_PROFILE_RECEIPT_NAME
    assert payload["status"] == task8.STAGE_PROFILE_STATUS
    assert payload["parity"]["meaningful_difference_count"] == 0
    assert payload["parity"]["unknown_difference_count"] == 0
    assert payload["measurement"]["no_event_total_seconds"] == 3.0
    assert payload["measurement"]["dense_total_seconds"] == 7.0
    assert payload["progress"][1]["summary"] == {
        "candidate_rows": 5,
        "filled_trades": 1,
    }
    assert payload["progress"][1]["compact_event_authority"][
        "authority_root_sha256"
    ] == "e" * 64
    assert payload["stage_profile"] == profiler.to_payload()
    assert payload["broker_live_authority"] is False
    assert payload["acceptance_authorized"] is False
    core = {
        key: value
        for key, value in payload.items()
        if key != "receipt_root_sha256"
    }
    assert payload["receipt_root_sha256"] == task8.replay.stable_sha256(core)


def test_task8_runtime_clock_closure_is_finite_and_noncausal() -> None:
    contract = task8.task8_runtime_clock_closure_contract()

    assert contract["schema"] == task8.TASK8_VOLATILITY_CONTRACT_SCHEMA
    assert len(contract["exclusions"]) == 16
    assert contract["broad_recursive_deletion"] is False
    assert contract["result_specific_exception"] is False
    assert contract["causal_or_economic_field_excluded"] is False
    assert contract["meaningful_difference_allowed"] is False
    assert contract["unknown_difference_allowed"] is False
    assert contract["acceptance_authorized"] is False
    assert {row["value_class"] for row in contract["exclusions"]} == {
        "wall_clock_timestamp",
        "derived_hash",
    }
    core = {
        key: value
        for key, value in contract.items()
        if key != "contract_root_sha256"
    }
    assert contract["contract_root_sha256"] == task8.replay.stable_sha256(core)


def test_task8_profile_validation_keeps_non_order_roles_byte_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = tmp_path / "profile"
    namespace.mkdir()
    (namespace / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json").write_text(
        json.dumps(
            {
                "raw_source_full_hash_count": 0,
                "sealed_cache_reuse_count": 24,
            }
        ),
        encoding="utf-8",
    )
    base_roles = {
        role: {"row_count": 0, "ordered_bytes_sha256": "a" * 64}
        for role in task8.task7.ROLE_SUFFIXES
    }

    def fake_day_projection(root: Path, day: str) -> dict:
        projection = {
            role: dict(value) for role, value in base_roles.items()
        }
        if Path(root) == namespace:
            projection["order"]["ordered_bytes_sha256"] = "b" * 64
            projection["semantic_order_preimage"]["ordered_bytes_sha256"] = (
                "c" * 64
            )
        return projection

    monkeypatch.setattr(task8, "_day_projection", fake_day_projection)
    monkeypatch.setattr(
        task8.task7,
        "validate_tick_cache_superset_reuse",
        lambda _receipt: None,
    )
    monkeypatch.setattr(
        task8.task3_acceptance.semantic,
        "compare_role_rows",
        lambda *_args, **_kwargs: {
            "status": "SEMANTICALLY_EQUIVALENT",
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
        },
    )
    monkeypatch.setattr(
        task8.task3_acceptance,
        "compare_order_preimages",
        lambda *_args, **_kwargs: {
            "status": "TASK3_ORDER_PREIMAGES_SEMANTICALLY_EQUIVALENT",
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
        },
    )
    partial = {
        "progress_rows": [
            {"start_day": task8.DAY1, "end_day": task8.DAY1},
            {"start_day": task8.DAY2, "end_day": task8.DAY2},
        ],
        "prepared_day_pack_checkpoints": [
            {
                "pack_root_sha256": task8.task7.TASK6_JAN1_PACK_ROOT_SHA256,
                "external_root_authenticated": True,
                "broker_mutation_enabled": False,
                "live_authority_touched": False,
            },
            {
                "pack_root_sha256": task8.JAN2_PACK_ROOT_SHA256,
                "external_root_authenticated": True,
                "broker_mutation_enabled": False,
                "live_authority_touched": False,
            },
        ],
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
    }

    result = task8._validate_profiled_execution(partial, namespace=namespace)

    assert result["status"] == "TASK8_PROFILED_EXECUTION_TASK6_SEMANTIC_PARITY"
    assert result["meaningful_difference_count"] == 0
    assert result["unknown_difference_count"] == 0
    assert result["semantic_parity"]["acceptance_authorized"] is False

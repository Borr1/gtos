from __future__ import annotations

from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_task2_semantic_slice_runner as semantic_slice,
)


def test_semantic_slice_cli_exposes_only_fresh_output_namespace(
    tmp_path: Path,
) -> None:
    args = semantic_slice.parse_args(["--output-dir", str(tmp_path / "slice")])
    assert args.output_dir == tmp_path / "slice"
    with pytest.raises(SystemExit):
        semantic_slice.parse_args(
            [
                "--output-dir",
                str(tmp_path / "slice"),
                "--start",
                "2026-01-03",
            ]
        )


def test_semantic_slice_args_are_exact_cache_enabled_jan1_2(
    tmp_path: Path,
) -> None:
    output = tmp_path / "slice"
    args = semantic_slice.semantic_slice_args(output)

    assert args.start == replay.ATTEMPT5_START_DAY
    assert args.end == replay.ATTEMPT5_CONTRACT_END_DAY
    assert args.max_days is None
    assert args.chunk_size == 1
    assert args.profiles == [replay.PROFILE_REPAIRED]
    assert args.symbols is None
    assert args.arm_id == "S0R0"
    assert args.accepted_physical_reference is False
    assert args.physical_reference_checkpoint_after_day is None
    assert args.task2_semantic_checkpoint_after_day == "2026-01-02"
    assert args.runtime_evidence_root == replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    assert args.parity_gate_after_day is None
    assert args.source_acceleration_cache_root == output / "typed-cache"
    assert args.tick_sparse_cache_root == replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
    assert args.source_prewarm_workers == 4
    assert args.streaming_proof_archive_root is None
    assert args.max_streaming_proof_archive_bytes == 0
    assert args.source_acceleration_bundle_dir == semantic_slice.SOURCE_BUNDLE_DIR
    assert args.source_acceleration_selection == semantic_slice.SOURCE_SELECTION


def test_semantic_slice_rejects_noncontiguous_checkpoint(monkeypatch, tmp_path: Path) -> None:
    def _run_with_bound_source(args):
        assert args.bound_source_bundle_consumer_rebind_authority == {
            "binding_root_sha256": "c" * 64
        }
        return {
            "status": "partial_in_progress_not_final_proof",
            "progress_rows": [
                {"start_day": "2026-01-01", "end_day": "2026-01-01"}
            ],
        }

    monkeypatch.setattr(
        semantic_slice.replay,
        "bind_attempt5_finalizer_conflict_key_order",
        lambda: (),
    )
    monkeypatch.setattr(
        semantic_slice.replay,
        "configure_runtime_evidence_root",
        lambda _root: {"contract_root_sha256": "a" * 64},
    )
    monkeypatch.setattr(
        semantic_slice.replay,
        "source_bundle_consumer_rebind_authority_from_args",
        lambda _args: {"binding_root_sha256": "c" * 64},
    )
    def _bind_shared_with_source_authority(args):
        assert args.source_acceleration_authority == {
            "schema": "bound-source-authority"
        }
        return {
            "valid": True,
            "shared_execution_contract_digest_sha256": "b" * 64,
        }

    monkeypatch.setattr(
        semantic_slice,
        "bind_source_acceleration_authority",
        lambda args: setattr(
            args,
            "source_acceleration_authority",
            {"schema": "bound-source-authority"},
        ),
    )
    monkeypatch.setattr(
        semantic_slice.physical,
        "_bind_shared_contract",
        _bind_shared_with_source_authority,
    )
    monkeypatch.setattr(
        semantic_slice,
        "validate_shared_contract_preflight",
        lambda args, shared: (
            None
            if (
                args.source_acceleration_authority
                == {"schema": "bound-source-authority"}
                and shared["shared_execution_contract_digest_sha256"] == "b" * 64
            )
            else (_ for _ in ()).throw(AssertionError("preflight mismatch"))
        ),
    )
    monkeypatch.setattr(
        semantic_slice.replay,
        "configure_output_namespace",
        lambda path: path,
    )
    monkeypatch.setattr(
        semantic_slice.replay,
        "run_replay_engine",
        _run_with_bound_source,
    )

    with pytest.raises(
        semantic_slice.SemanticSliceRejected,
        match="semantic_slice_checkpoint_result_invalid",
    ):
        semantic_slice.run_semantic_slice(tmp_path / "slice")


def test_direct_semantic_manifest_binds_every_evidence_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import (
        replay_acceleration_task2_semantic_acceptance as acceptance,
    )

    monkeypatch.setattr(acceptance, "ROOT", tmp_path)

    namespace = tmp_path / "slice"
    namespace.mkdir()
    semantic_root = namespace.with_name(namespace.name + ".semantic-diagnostic")
    semantic_root.mkdir()
    outputs = {
        role: namespace / f"{semantic_slice.replay.ATTEMPT5_OUTPUT_PREFIX}_{suffix}"
        for role, suffix in acceptance.ROLE_SUFFIXES.items()
    }
    outputs["partial_summary"] = namespace / (
        f"{semantic_slice.replay.ATTEMPT5_OUTPUT_PREFIX}_PARTIAL_SUMMARY.json"
    )
    semantic_outputs = {
        "semantic_candidate": semantic_root / (
            f"{semantic_slice.replay.ATTEMPT5_OUTPUT_PREFIX}_"
            "SEMANTIC_CANDIDATE_LEDGER.jsonl"
        ),
        "semantic_state_checkpoint": semantic_root / (
            f"{semantic_slice.replay.ATTEMPT5_OUTPUT_PREFIX}_"
            "SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl"
        ),
        "semantic_order_preimage": semantic_root / (
            f"{semantic_slice.replay.ATTEMPT5_OUTPUT_PREFIX}_"
            "SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl"
        ),
        "semantic_source_manifest": semantic_root / (
            f"{semantic_slice.replay.ATTEMPT5_OUTPUT_PREFIX}_"
            "SEMANTIC_SOURCE_MANIFEST.json"
        ),
    }
    for path in (
        *(outputs[role] for role in acceptance.ROLE_SUFFIXES),
        semantic_outputs["semantic_candidate"],
        semantic_outputs["semantic_state_checkpoint"],
        semantic_outputs["semantic_order_preimage"],
    ):
        path.write_text('{"row":1}\n', encoding="utf-8")
    outputs["partial_summary"].write_text(
        '{"status":"partial_in_progress_not_final_proof"}\n',
        encoding="utf-8",
    )

    semantic_slice.write_direct_semantic_source_manifest(
        namespace=namespace,
        outputs=outputs,
        semantic_outputs=semantic_outputs,
        runtime_input_contract_root_sha256="a" * 64,
        shared_execution_contract_digest_sha256="b" * 64,
    )

    validated = acceptance.validate_semantic_source_manifest(namespace)
    assert validated["schema"] == (
        "gtos.replay_acceleration.task2_direct_semantic_source_manifest.v1"
    )
    assert validated["direct_hot_file_count"] == 12

    outputs["trade"].write_text('{"row":2}\n', encoding="utf-8")
    with pytest.raises(
        acceptance.SemanticAcceptanceError,
        match="semantic_source_file_invalid:trade",
    ):
        acceptance.validate_semantic_source_manifest(namespace)

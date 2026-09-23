from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _root(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _shared_execution_contract(
    *,
    code_path: str,
    code_hash: str,
) -> tuple[dict[str, object], str]:
    payload: dict[str, object] = {
        "schema": "gtos.final_moonshot.broad_replay.shared_execution_contract.v1",
        "code_authority": [{"path": code_path, "sha256": code_hash}],
        "missing_code_paths": [],
        "effective_profile_config_hashes": {"profile": "d" * 64},
        "effective_profile_config_hash_semantics": {
            "projection": "synthetic_test_projection",
            "excluded_runtime_fields": [],
            "raw_artifact_sha256_retained_in_runtime_and_ledgers": True,
        },
        "config_file_hashes": {},
        "ultimate_package_runtime_input_contract": {"valid": True},
        "active_replay_symbol_universe": ["XAUUSD"],
        "execution_options": {
            "profiles": ["profile"],
            "chunk_size": 1,
            "max_candidates_per_symbol_window": 0,
            "smoke_subset": False,
            "skip_tick_source": False,
            "use_native_h1": False,
            "omit_candidate_ledger": True,
            "omit_candidate_index_ledger": True,
            "omit_packet_sidecar_ledger": True,
            "compact_missed_ledger": True,
            "compact_decision_ledger": True,
            "compact_scorecard_ledger": True,
            "candidate_ledger_packet_max_bytes": 1024,
            "scorecard_ledger_packet_max_bytes": 4096,
            "compact_scorecard_symbol_risk_config": True,
            "scorecard_probe_row_limit": 12,
            "gc_between_chunks": True,
            "b7_5_selection_sizing_factorial_arm": {
                "arm_id": "S0R0",
                "arm_fingerprint_sha256": "3" * 64,
            },
        },
        "window_identity_excluded_from_shared_digest": True,
        "broker_live_final_authority": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
    }
    digest = _root(payload)
    return {
        **payload,
        "valid": True,
        "status": "shared_execution_contract_bound",
        "shared_execution_contract_digest_sha256": digest,
    }, digest


def _golden_manifest_root(value: object) -> str:
    return hashlib.sha256(_canonical(value) + b"\n").hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))


def _seal(
    archive,
    *,
    start_day: str,
    end_day: str,
    current_summary_contract_root_sha256: str,
):
    del current_summary_contract_root_sha256
    partial_path = archive.hot_outputs["decision"].parent / (
        f"{archive.output_prefix}_PARTIAL_SUMMARY.json"
    )
    partial = json.loads(partial_path.read_bytes())
    shared = partial["shared_execution_contract"]
    checkpoint_partial_path = partial_path
    if partial.get("last_completed_end_day") != end_day:
        checkpoint_partial_path = archive.root.parent / (
            f"{archive.output_prefix}_{end_day}_PRE_ARCHIVE.json"
        )
        checkpoint_partial = dict(partial)
        checkpoint_partial["last_completed_end_day"] = end_day
        checkpoint_partial_path.write_text(
            json.dumps(checkpoint_partial, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return archive.seal_and_reclaim(
        start_day=start_day,
        end_day=end_day,
        pre_archive_partial_summary_path=checkpoint_partial_path,
        checkpoint_authority={
            "schema": "gtos.replay_acceleration.streaming_checkpoint_authority.v1",
            "output_prefix": archive.output_prefix,
            "run_identity_root_sha256": partial[
                "attempt5_execution_identity"
            ]["identity_root_sha256"],
            "source_plan_digest_sha256": partial["b7_5_contract_binding"][
                "actual_source_plan_digests_sha256"
            ][0],
            "arm_fingerprint_sha256": partial[
                "b7_5_selection_sizing_factorial_arm_binding"
            ]["arm_fingerprint_sha256"],
            "shared_execution_contract_sha256": shared[
                "shared_execution_contract_digest_sha256"
            ],
            "accelerated_code_config_authority_root_sha256": _root(
                {
                    "code_authority": shared["code_authority"],
                    "config_file_hashes": shared["config_file_hashes"],
                }
            ),
        },
    )


def _synthetic_names(prefix: str) -> dict[str, str]:
    return {
        "source": f"{prefix}_SOURCE_UNIVERSE_LEDGER.jsonl",
        "decision": f"{prefix}_DECISION_LEDGER.jsonl",
        "scorecard": f"{prefix}_SCORECARD_LEDGER.jsonl",
        "order": f"{prefix}_ORDER_LEDGER.jsonl",
        "trade": f"{prefix}_TRADE_LEDGER.jsonl",
        "oracle": f"{prefix}_ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "missed": f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        "bucket": f"{prefix}_BUCKET_LEDGER.jsonl",
    }


def _make_equal_namespaces(tmp_path: Path):
    from src.research_infra.replay_acceleration_partial_golden import (
        build_partial_golden_manifest,
        write_partial_golden_manifest,
    )

    prefix = "BOUNDED_S0R0"
    golden = tmp_path / "golden"
    accelerated = tmp_path / "accelerated"
    golden.mkdir()
    accelerated.mkdir()
    names = _synthetic_names(prefix)
    ledger_bytes: dict[str, int | None] = {
        role: None
        for role in (
            "source",
            "decision",
            "candidate",
            "candidate_index",
            "scorecard",
            "order",
            "trade",
            "oracle",
            "missed",
            "bucket",
            "comparison",
            "packet_sidecar",
            "summary",
        )
    }
    archived_row_types = {
        "decision": "asof_decision",
        "scorecard": "scheduler_scorecard",
        "missed": "missed_opportunity",
    }
    for index, (role, name) in enumerate(names.items()):
        rows = [
            {
                "row_type": archived_row_types.get(role, role),
                "canonical_replay_candidate_instance_key": f"candidate-{index}",
                "selected_order_sequence": index,
                "lifecycle_status": "synthetic",
                "trading_day": "2026-01-01",
                "profile": "profile",
                "broad_replay_profile": "profile",
                "split": "development",
                "chunk_id": (
                    "profile:development:2026-01-01:2026-01-07"
                ),
                "chunk_start_day": "2026-01-01",
                "chunk_end_day": "2026-01-07",
                "chunk_day_count": 7,
                "row_provenance_schema": (
                    "broad_live_as_if_replay_row_provenance_v1"
                ),
            }
        ]
        _write_jsonl(golden / name, rows)
        _write_jsonl(accelerated / name, rows)
        ledger_bytes[role] = (golden / name).stat().st_size

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    code_path = "pyproject.toml"
    code_blob = subprocess.run(
        ["git", "show", f"{head}:{code_path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    code_hash = hashlib.sha256(code_blob).hexdigest()
    shared_contract, shared_digest = _shared_execution_contract(
        code_path=code_path,
        code_hash=code_hash,
    )

    days = [f"2026-01-{day:02d}" for day in range(1, 8)]
    progress_rows = []
    capacity_checkpoints = []
    source_checkpoints = []
    sequence = 0
    for day in days:
        chunk_id = f"profile:development:{day}:{day}"
        progress_rows.append(
            {
                "chunk_id": chunk_id,
                "profile": "profile",
                "split": "development",
                "start_day": day,
                "end_day": day,
                "day_count": 1,
            }
        )
        capacity_checkpoints.append(
            {
                "chunk_id": chunk_id,
                "profile": "profile",
                "split": "development",
                "start_day": day,
                "end_day": day,
                "day_count": 1,
                "cleanup_status": "completed",
                "account_object_continuity": True,
                "broker_object_continuity": True,
                "selected_order_sequence_monotonic": True,
                "starting_order_sequence": sequence,
                "ending_order_sequence": sequence + 1,
                "explicit_gc_completed": True,
            }
        )
        source_checkpoints.append(
            {
                "profile": "profile",
                "split": "development",
                "execution_days": [day],
                "execution_days_subset_of_source_authority": True,
                "source_plan_valid": True,
                "source_plan_matches_canonical": True,
                "static_sources_match_canonical": True,
                "tick_component_sources_match_canonical": True,
                "m1_execution_day_authority_matches_canonical": True,
                "source_plan_resolved_symbol_count": 24,
                "source_plan_missing_symbols": [],
                "canonical_source_plan_digest_sha256": "1" * 64,
                "source_plan_digest_sha256": "1" * 64,
            }
        )
        sequence += 1

    identity_core = {
        "schema": "synthetic.attempt5_execution_identity.v1",
        "output_prefix": prefix,
    }
    identity = {
        **identity_core,
        "identity_root_sha256": _root(identity_core),
    }
    arm_binding = {
        "arm_id": "S0R0",
        "arm_fingerprint_sha256": "3" * 64,
        "selection_factor": "S0",
        "sizing_factor": "R0",
        "selection_mode": "neutral_hash_hard_eligible",
        "sizing_mode": "fixed_equal_account_risk",
    }
    partial = {
        "schema": "gtos.final_moonshot.broad_live_as_if_replay_harness.partial_summary.v1",
        "status": "partial_in_progress_not_final_proof",
        "output_prefix": prefix,
        "profiles_requested": ["profile"],
        "last_completed_end_day": "2026-01-07",
        "progress_rows": progress_rows,
        "ledger_write_row_counts_so_far": {role: 1 for role in names},
        "ledger_file_bytes_flushed_before_partial_summary": ledger_bytes,
        "attempt5_execution_identity": identity,
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "packet_sidecar_ledger_omitted": True,
        "capacity_safe_chunk_execution_contract": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "capacity_safe_chunk_execution.v2"
            ),
            "status": "capacity_safe_chunk_execution_in_progress",
            "valid": False,
            "planned_chunk_count": 31,
            "completed_chunk_count": 7,
            "cleanup_checkpoint_count": 7,
            "current_chunk_cleanup_pending": False,
            "cleanup_complete_for_all_completed_chunks": True,
            "same_account_state_reused_across_chunks": True,
            "same_simulated_broker_reused_across_chunks": True,
            "selected_order_sequence_monotonic_across_chunks": True,
            "completed_chunk_day_scoped_source_caches_released": True,
            "completed_replay_source_caches_released": True,
            "completed_source_authority_scoped_caches_released": True,
            "checkpoints": capacity_checkpoints,
        },
        "source_authority_chunk_invariance_contract": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "source_authority_chunk_invariance.v2"
            ),
            "status": "source_authority_chunk_invariance_incomplete",
            "valid": False,
            "planned_chunk_count": 31,
            "completed_chunk_count": 7,
            "checkpoint_count": 7,
            "current_chunk_pending": False,
            "all_source_plans_valid": True,
            "all_chunk_source_plans_match_canonical": True,
            "all_execution_days_inside_authority_scope": True,
            "checkpoints": source_checkpoints,
        },
        "b7_5_contract_binding": {
            "required": True,
            "valid": True,
            "actual_shared_execution_contract_digest_sha256": shared_digest,
            "actual_source_plan_digests_sha256": ["1" * 64],
            "expected_shared_execution_contract_digest_sha256": shared_digest,
            "expected_source_plan_digest_sha256": "1" * 64,
            "selection_sizing_factorial_arm_binding": arm_binding,
        },
        "b7_5_selection_sizing_factorial_arm_binding": arm_binding,
        "shared_execution_contract": shared_contract,
        "semantic_contract_evidence": {
            "candidate_identity": "opaque",
            "selected_order_sequence": 7,
            "decision_status": "opaque",
            "scorecard_status": "opaque",
            "missed_status": "opaque",
            "lifecycle_status": "opaque",
            "replacement_status": "opaque",
            "account_terminal_status": "opaque",
            "broker_terminal_status": "opaque",
            "cost_contract": "opaque",
            "reservation_status": "opaque",
        },
        "generated_at_utc": "legacy-time",
    }
    partial_name = f"{prefix}_PARTIAL_SUMMARY.json"
    (golden / partial_name).write_text(
        json.dumps(partial, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    partial["generated_at_utc"] = "accelerated-time"
    (accelerated / partial_name).write_text(
        json.dumps(partial, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest_value = build_partial_golden_manifest(
        namespace=golden,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=head,
        git_root=ROOT,
        sealed_at_utc="2026-07-20T00:00:00Z",
    )
    manifest = tmp_path / "golden_manifest.json"
    write_partial_golden_manifest(manifest, manifest_value)
    return prefix, golden, accelerated, names, manifest


def _prospective_golden_authority(manifest_path: Path) -> dict[str, object]:
    from src.research_infra.replay_acceleration_partial_golden import (
        build_prospective_amendment,
        write_partial_golden_manifest,
    )

    manifest = json.loads(manifest_path.read_bytes())
    amendment_path = manifest_path.with_name("golden_amendment.json")
    amendment = build_prospective_amendment(manifest)
    write_partial_golden_manifest(amendment_path, amendment)
    verifier_path = (
        ROOT
        / "src/research_infra/replay_acceleration_real_parity_verifier.py"
    ).resolve()
    return {
        "golden_manifest_path": str(manifest_path.resolve()),
        "golden_manifest_file_sha256": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
        "golden_manifest_self_root_sha256": manifest[
            "manifest_self_root_sha256"
        ],
        "golden_root_sha256": manifest["golden_root_sha256"],
        "opaque_result_surface_root_sha256": manifest[
            "opaque_result_surface_root_sha256"
        ],
        "golden_amendment_path": str(amendment_path.resolve()),
        "golden_amendment_file_sha256": hashlib.sha256(
            amendment_path.read_bytes()
        ).hexdigest(),
        "golden_amendment_self_root_sha256": amendment[
            "amendment_self_root_sha256"
        ],
        "fixed_verifier_module": (
            "src.research_infra.replay_acceleration_real_parity_verifier"
        ),
        "fixed_verifier_path": str(verifier_path),
        "fixed_verifier_file_sha256": hashlib.sha256(
            verifier_path.read_bytes()
        ).hexdigest(),
    }


def _build_bound_gate_request(**kwargs: object) -> dict[str, object]:
    from src.research_infra.replay_acceleration_real_gate import (
        build_gate_request,
    )

    outputs = kwargs["outputs"]
    assert isinstance(outputs, dict)
    accelerated_namespace = Path(next(iter(outputs.values()))).parent
    partial_summary = json.loads(
        Path(outputs["partial_summary"]).read_bytes()
    )
    kwargs["shared_execution_contract_sha256"] = partial_summary[
        "shared_execution_contract"
    ]["shared_execution_contract_digest_sha256"]
    manifest_path = accelerated_namespace.parent / "golden_manifest.json"
    if "prospective_golden_authority" not in kwargs:
        kwargs["prospective_golden_authority"] = (
            _prospective_golden_authority(manifest_path)
        )
    return build_gate_request(**kwargs)


def _make_archived_gate_request(
    tmp_path: Path,
    *,
    archive_envelope: dict[str, object] | None = None,
):
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    hot_outputs = {
        role: accelerated / names[role]
        for role in ("decision", "scorecard", "missed")
    }
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix=prefix,
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    partial_path = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    if archive_envelope is not None:
        partial = json.loads(partial_path.read_bytes())
        partial.update(archive_envelope)
        partial_path.write_text(
            json.dumps(partial, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = partial_path
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        archived_result_surfaces=archive.gate_surface_contracts(),
    )
    return prefix, accelerated, manifest, archive, partial_path, request


def _rebind_post_archive_partial_request(
    request: dict[str, object],
    partial_path: Path,
) -> None:
    raw = partial_path.read_bytes()
    partial_contract = request["partial_summary"]
    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(partial_contract, dict)
    assert isinstance(transformation, dict)
    post_contract = transformation["post_archive_partial_summary"]
    assert isinstance(post_contract, dict)
    partial_contract.update(
        {
            "bytes": len(raw),
            "rows": raw.count(b"\n"),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    post_contract.update(
        {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    transformation.pop("transformation_root_sha256")
    transformation["transformation_root_sha256"] = _root(transformation)
    request.pop("gate_request_root_sha256")
    request["gate_request_root_sha256"] = _root(request)


def _reroot_archive_transformation_request(request: dict[str, object]) -> None:
    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(transformation, dict)
    transformation.pop("transformation_root_sha256")
    transformation["transformation_root_sha256"] = _root(transformation)
    request.pop("gate_request_root_sha256")
    request["gate_request_root_sha256"] = _root(request)


def test_gate_request_is_structural_and_receipt_validation_is_fail_closed(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        GateRejected,
        build_gate_request,
        validate_parity_receipt,
    )

    prefix, _golden, accelerated, names, _manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    assert request["policy_execution_entered"] is True
    assert request["economic_values_exposed"] is False
    assert len(request["persisted_result_surfaces"]) == 8

    receipt_core = {
        "schema": "gtos.replay_acceleration.real_s0r0_parity_receipt.v1",
        "status": "EXACT_FULL_RESULT_PARITY_ACCEPTED",
        "parity_accepted": True,
        "gate_request_root_sha256": request["gate_request_root_sha256"],
        "output_prefix": prefix,
        "completed_through_day": "2026-01-07",
        "other_arms_launched": False,
        "broker_live_authority": False,
    }
    receipt = {**receipt_core, "receipt_root_sha256": _root(receipt_core)}
    with pytest.raises(GateRejected, match="parity_report_required"):
        validate_parity_receipt(receipt, gate_request=request)


def test_gate_rejects_semantic_diagnostic_as_acceptance_receipt(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        GateRejected,
        build_gate_request,
        validate_parity_receipt,
    )

    prefix, _golden, accelerated, names, _manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    receipt_core = {
        "schema": "gtos.replay_acceleration.real_s0r0_parity_receipt.v1",
        "status": "DECLARED_RUNTIME_ENVELOPE_SEMANTIC_DIAGNOSTIC_PASS",
        "parity_accepted": False,
        "gate_request_root_sha256": request["gate_request_root_sha256"],
        "output_prefix": prefix,
        "completed_through_day": "2026-01-07",
        "other_arms_launched": False,
        "broker_live_authority": False,
    }
    receipt = {**receipt_core, "receipt_root_sha256": _root(receipt_core)}

    with pytest.raises(GateRejected, match="parity_receipt_invalid"):
        validate_parity_receipt(receipt, gate_request=request)


def test_independent_verifier_accepts_exact_bytes_and_rejects_bit_flip(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        build_gate_request,
        validate_parity_receipt,
    )
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    report, receipt = verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    assert report["valid"] is True
    assert report["all_persisted_ledger_bytes_equal"] is True
    assert report["semantic_category_equality"]["account_broker_terminal"] is True
    assert receipt["status"] == "EXACT_FULL_RESULT_PARITY_ACCEPTED"
    assert validate_parity_receipt(
        receipt,
        gate_request=request,
        parity_report=report,
    )["parity_accepted"] is True

    target = accelerated / names["decision"]
    raw = bytearray(target.read_bytes())
    raw[-2] ^= 1
    target.write_bytes(raw)
    with pytest.raises(ValueError, match="persisted_ledger_byte_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_verifier_rejects_manifest_swap_after_bound_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_real_parity_verifier as verifier

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    duplicate = tmp_path / "duplicate-golden-manifest.json"
    duplicate.write_bytes(manifest.read_bytes())
    original_file_sha256 = verifier.file_sha256
    swapped = False

    def swap_after_bound_hash(path: object) -> str:
        nonlocal swapped
        digest = original_file_sha256(path)
        actual_path = Path(getattr(path, "path", path))
        if actual_path == manifest and not swapped:
            manifest.unlink()
            manifest.symlink_to(duplicate)
            swapped = True
        return digest

    monkeypatch.setattr(verifier, "file_sha256", swap_after_bound_hash)

    with pytest.raises(ValueError, match="parity_evidence_path_changed"):
        verifier.verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )
    assert swapped is True


def test_verifier_rejects_direct_surface_swap_before_union_consumption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_real_parity_verifier as verifier

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    target = accelerated / names["order"]
    duplicate = tmp_path / "duplicate-order.jsonl"
    duplicate.write_bytes(target.read_bytes())
    original_stream_contract = verifier.stream_contract
    swapped = False

    def swap_after_contract(path: object) -> dict[str, object]:
        nonlocal swapped
        contract = original_stream_contract(path)
        actual_path = Path(getattr(path, "path", path))
        if actual_path == target and not swapped:
            target.unlink()
            target.symlink_to(duplicate)
            swapped = True
        return contract

    monkeypatch.setattr(verifier, "stream_contract", swap_after_contract)

    with pytest.raises(ValueError, match="parity_evidence_path_changed"):
        verifier.verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )
    assert swapped is True


def test_rejects_same_prefix_namespace_contamination_before_surface_reads(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    (golden / f"{prefix}_UNDECLARED_SEMANTIC_PROOF.jsonl").write_bytes(
        _canonical({"schema": "undeclared"}) + b"\n"
    )
    direct_surface = accelerated / names["decision"]
    changed = bytearray(direct_surface.read_bytes())
    changed[-2] ^= 1
    direct_surface.write_bytes(changed)

    with pytest.raises(ValueError, match="golden_namespace_inventory_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_incomplete_self_rooted_golden_manifest(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    full_manifest = json.loads(manifest.read_bytes())
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    incomplete_manifest = {
        "schema": full_manifest["schema"],
        "namespace": full_manifest["namespace"],
        "scope": {
            "start_day": full_manifest["scope"]["start_day"],
            "end_day": full_manifest["scope"]["end_day"],
        },
        "persisted_result_surfaces": full_manifest["persisted_result_surfaces"],
        "partial_summary": {"name": full_manifest["partial_summary"]["name"]},
        "golden_root_sha256": full_manifest["golden_root_sha256"],
    }
    incomplete_manifest["manifest_self_root_sha256"] = _golden_manifest_root(
        incomplete_manifest
    )
    manifest.write_bytes(_canonical(incomplete_manifest) + b"\n")

    with pytest.raises(
        ValueError,
        match="gate_request_golden_authority_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


@pytest.mark.parametrize("alias_kind", ["symlink", "hardlink"])
def test_independent_verifier_rejects_direct_surface_aliases_to_golden(
    tmp_path: Path,
    alias_kind: str,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    for name in names.values():
        accelerated_path = accelerated / name
        accelerated_path.unlink()
        golden_path = golden / name
        if alias_kind == "symlink":
            accelerated_path.symlink_to(golden_path)
        else:
            os.link(golden_path, accelerated_path)
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )

    expected_error = (
        "accelerated_surface_aliases_golden"
        if alias_kind == "symlink"
        else "partial_golden_authority_invalid"
    )
    with pytest.raises(ValueError, match=expected_error):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


@pytest.mark.parametrize("alias_kind", ["symlink", "hardlink"])
def test_independent_verifier_rejects_partial_summary_alias_to_golden(
    tmp_path: Path,
    alias_kind: str,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    partial_name = f"{prefix}_PARTIAL_SUMMARY.json"
    accelerated_partial = accelerated / partial_name
    accelerated_partial.unlink()
    golden_partial = golden / partial_name
    if alias_kind == "symlink":
        accelerated_partial.symlink_to(golden_partial)
    else:
        os.link(golden_partial, accelerated_partial)
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated_partial
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )

    expected_error = (
        "accelerated_surface_aliases_golden"
        if alias_kind == "symlink"
        else "partial_golden_authority_invalid"
    )
    with pytest.raises(ValueError, match=expected_error):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_accepts_bound_pretty_partial_summary(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    partial_name = f"{prefix}_PARTIAL_SUMMARY.json"
    for namespace in (golden, accelerated):
        partial_path = namespace / partial_name
        partial = json.loads(partial_path.read_bytes())
        partial_path.write_text(
            json.dumps(partial, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / partial_name
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )

    report, receipt = verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    assert report["valid"] is True
    assert receipt["parity_accepted"] is True


def test_independent_verifier_rejects_accelerated_namespace_contamination(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    (accelerated / f"{prefix}_UNDECLARED_SEMANTIC_PROOF.jsonl").write_bytes(
        _canonical({"schema": "undeclared"}) + b"\n"
    )

    with pytest.raises(ValueError, match="accelerated_namespace_inventory_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_golden_as_accelerated_namespace(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, golden, _accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    outputs = {role: golden / name for role, name in names.items()}
    outputs["partial_summary"] = golden / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )

    with pytest.raises(ValueError, match="parity_namespace_not_separate"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=golden,
            gate_request=request,
        )


def test_independent_verifier_rejects_partial_snapshot_outside_namespace(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    outputs = {role: accelerated / name for role, name in names.items()}
    partial = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    outputs["partial_summary"] = partial
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )
    escaped = tmp_path / "escaped-partial-summary.json"
    escaped.write_bytes(partial.read_bytes())
    request["partial_summary"]["snapshot_path"] = str(escaped)
    request.pop("gate_request_root_sha256")
    request["gate_request_root_sha256"] = _root(request)

    with pytest.raises(
        ValueError,
        match="partial_summary_snapshot_outside_namespace",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_accepts_hot_surfaces_from_verified_day_shards(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    hot_outputs = {
        role: accelerated / names[role]
        for role in ("decision", "scorecard", "missed")
    }
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix=prefix,
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        archived_result_surfaces=archive.gate_surface_contracts(),
    )

    report, receipt = verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    assert report["valid"] is True
    assert report["all_persisted_ledger_bytes_equal"] is True
    assert receipt["parity_accepted"] is True
    archive_verification = report["archive_campaign_verifications"][0]
    campaign_raw = archive.campaign_manifest_path.read_bytes()
    assert archive_verification["campaign_manifest_path"] == str(
        archive.campaign_manifest_path
    )
    assert archive_verification["campaign_manifest_sha256"] == hashlib.sha256(
        campaign_raw
    ).hexdigest()
    assert {
        row["role"] for row in request["persisted_result_surfaces"]
        if row.get("storage") == "verified_zstd_campaign"
    } == {"decision", "scorecard", "missed"}


def test_archive_envelope_only_partial_summary_changes_pass_independent_gate(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        validate_parity_receipt,
    )
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    (
        _prefix,
        accelerated,
        manifest,
        _archive,
        _partial_path,
        request,
    ) = _make_archived_gate_request(
        tmp_path,
        archive_envelope={
            "generated_at_utc": "post-archive-time",
            "streaming_proof_archive": {"status": "sealed"},
            "streaming_proof_archive_shards": [{"segment_id": "001"}],
            "streaming_capacity_checks": [{"status": "pass"}],
        },
    )

    report, receipt = verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )

    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(transformation, dict)
    transformation_root = transformation["transformation_root_sha256"]
    assert report[
        "partial_summary_archive_transformation_root_sha256"
    ] == transformation_root
    assert receipt[
        "partial_summary_archive_transformation_root_sha256"
    ] == transformation_root
    validated = validate_parity_receipt(
        receipt,
        gate_request=request,
        parity_report=report,
    )
    assert validated["receipt_root_sha256"] == receipt["receipt_root_sha256"]


def test_independent_verifier_rejects_non_allowlisted_archive_snapshot_change(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    (
        _prefix,
        accelerated,
        manifest,
        _archive,
        partial_path,
        request,
    ) = _make_archived_gate_request(
        tmp_path,
        archive_envelope={"streaming_proof_archive": {"status": "sealed"}},
    )
    partial = json.loads(partial_path.read_bytes())
    partial["semantic_contract_evidence"]["cost_contract"] = "changed"
    partial_path.write_text(
        json.dumps(partial, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    _rebind_post_archive_partial_request(request, partial_path)

    with pytest.raises(
        ValueError,
        match="partial_summary_archive_transformation_semantic_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_forged_archive_stable_projection_root(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    (
        _prefix,
        accelerated,
        manifest,
        _archive,
        _partial_path,
        request,
    ) = _make_archived_gate_request(tmp_path)
    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(transformation, dict)
    transformation["stable_projection_root_sha256"] = "f" * 64
    _reroot_archive_transformation_request(request)

    with pytest.raises(
        ValueError,
        match="partial_summary_archive_transformation_semantic_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_wrong_pre_archive_snapshot_path(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    (
        _prefix,
        accelerated,
        manifest,
        _archive,
        _partial_path,
        request,
    ) = _make_archived_gate_request(tmp_path)
    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(transformation, dict)
    pre_contract = transformation["pre_archive_partial_summary"]
    assert isinstance(pre_contract, dict)
    copied_snapshot = tmp_path / "copied-pre-archive-summary.json"
    copied_snapshot.write_bytes(Path(pre_contract["path"]).read_bytes())
    pre_contract["path"] = str(copied_snapshot)
    _reroot_archive_transformation_request(request)

    with pytest.raises(
        ValueError,
        match="partial_summary_archive_transformation_identity_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_wrong_pre_archive_snapshot_hash(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    (
        _prefix,
        accelerated,
        manifest,
        _archive,
        _partial_path,
        request,
    ) = _make_archived_gate_request(tmp_path)
    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(transformation, dict)
    pre_contract = transformation["pre_archive_partial_summary"]
    assert isinstance(pre_contract, dict)
    pre_contract["sha256"] = "e" * 64
    _reroot_archive_transformation_request(request)

    with pytest.raises(
        ValueError,
        match="partial_summary_archive_transformation_identity_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_wrong_terminal_checkpoint_chain_root(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    (
        _prefix,
        accelerated,
        manifest,
        _archive,
        _partial_path,
        request,
    ) = _make_archived_gate_request(tmp_path)
    transformation = request["partial_summary_archive_transformation"]
    assert isinstance(transformation, dict)
    transformation["terminal_checkpoint_chain_root_sha256"] = "d" * 64
    _reroot_archive_transformation_request(request)

    with pytest.raises(
        ValueError,
        match="partial_summary_archive_transformation_campaign_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_real_parity_rejects_unaccounted_hot_bytes_for_archived_role(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        GateRejected,
        build_gate_request,
    )
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, _golden, accelerated, names, _manifest = _make_equal_namespaces(
        tmp_path
    )
    hot_outputs = {
        role: accelerated / names[role]
        for role in ("decision", "scorecard", "missed")
    }
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix=prefix,
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    hot_outputs["decision"].write_bytes(
        _canonical(
            {
                "row_type": "rogue",
                "canonical_replay_candidate_instance_key": "candidate-rogue",
            }
        )
        + b"\n"
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"

    with pytest.raises(GateRejected, match="archived_hot_surface_not_empty"):
        build_gate_request(
            output_prefix=prefix,
            outputs=outputs,
            ledger_row_counts={role: 1 for role in names},
            completed_through_day="2026-01-07",
            source_plan_digest_sha256="1" * 64,
            shared_execution_contract_sha256="2" * 64,
            arm_id="S0R0",
            arm_fingerprint_sha256="3" * 64,
            prospective_golden_authority=_prospective_golden_authority(
                tmp_path / "golden_manifest.json"
            ),
            archived_result_surfaces=archive.gate_surface_contracts(),
        )


def test_independent_verifier_rejects_archive_outside_request_calendar(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    hot_outputs = {
        role: accelerated / names[role]
        for role in ("decision", "scorecard", "missed")
    }
    archive = StreamingProofArchive(
        root=tmp_path / "archive-wrong-calendar",
        output_prefix=prefix,
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    for path in hot_outputs.values():
        rows = [json.loads(line) for line in path.read_bytes().splitlines()]
        for row in rows:
            row.update(
                {
                    "trading_day": "2030-01-01",
                    "chunk_id": (
                        "profile:development:2030-01-01:2030-01-07"
                    ),
                    "chunk_start_day": "2030-01-01",
                    "chunk_end_day": "2030-01-07",
                    "chunk_day_count": 7,
                }
            )
        _write_jsonl(path, rows)
    _seal(archive,
        start_day="2030-01-01",
        end_day="2030-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    post_archive_partial = json.loads(outputs["partial_summary"].read_bytes())
    post_archive_partial["last_completed_end_day"] = "2030-01-07"
    outputs["partial_summary"].write_text(
        json.dumps(post_archive_partial, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        archived_result_surfaces=archive.gate_surface_contracts(),
    )

    with pytest.raises(ValueError, match="archive_campaign_scope_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_mixed_archive_campaigns(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    hot_outputs = {
        role: accelerated / names[role]
        for role in ("decision", "scorecard", "missed")
    }
    first = StreamingProofArchive(
        root=tmp_path / "archive-first-campaign",
        output_prefix=prefix,
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(first,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    for role, path in hot_outputs.items():
        path.write_bytes((golden / names[role]).read_bytes())
    second = StreamingProofArchive(
        root=tmp_path / "archive-second-campaign",
        output_prefix=prefix,
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(second,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="b" * 64,
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        archived_result_surfaces=first.gate_surface_contracts(),
    )
    second_scorecard = second.gate_surface_contracts()["scorecard"]
    request_surfaces = request["persisted_result_surfaces"]
    assert isinstance(request_surfaces, list)
    scorecard = next(
        row for row in request_surfaces if row["role"] == "scorecard"
    )
    scorecard["archive_campaign_manifest_path"] = second_scorecard[
        "archive_campaign_manifest_path"
    ]
    scorecard["archive_campaign_manifest_root_sha256"] = second_scorecard[
        "archive_campaign_manifest_root_sha256"
    ]
    request.pop("gate_request_root_sha256")
    request["gate_request_root_sha256"] = _root(request)

    with pytest.raises(ValueError, match="archive_campaign_coherence_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_rejects_duplicate_surface_inventory(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest_path = _make_equal_namespaces(
        tmp_path
    )
    manifest = json.loads(manifest_path.read_bytes())
    manifest["persisted_result_surfaces"].append(
        dict(manifest["persisted_result_surfaces"][0])
    )
    manifest.pop("manifest_self_root_sha256")
    manifest["manifest_self_root_sha256"] = _golden_manifest_root(manifest)
    manifest_path.write_bytes(_canonical(manifest) + b"\n")
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
    )

    with pytest.raises(ValueError, match="persisted_surface_inventory_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest_path,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_candidate_identity_root_preserves_role_order_and_duplicates() -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        candidate_union_root_from_lines,
    )

    first = _canonical(
        {
            "profile": "S0R0",
            "canonical_replay_candidate_instance_key": "candidate-a",
        }
    ) + b"\n"
    second = _canonical(
        {
            "profile": "S0R0",
            "canonical_replay_candidate_instance_key": "candidate-b",
        }
    ) + b"\n"

    ordered = candidate_union_root_from_lines([[first, second]])
    reordered = candidate_union_root_from_lines([[second, first]])
    duplicated = candidate_union_root_from_lines([[first, first, second]])
    first_role = candidate_union_root_from_lines([[first], []])
    second_role = candidate_union_root_from_lines([[], [first]])

    assert ordered[0] != reordered[0]
    assert ordered[0] != duplicated[0]
    assert first_role[0] != second_role[0]
    assert ordered[1:] == (2, 0)
    assert duplicated[1:] == (3, 0)


def test_independent_verifier_checks_all_archives_before_direct_surfaces(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    archive = StreamingProofArchive(
        root=tmp_path / "archive-first",
        output_prefix=prefix,
        hot_outputs={
            role: accelerated / names[role]
            for role in ("decision", "scorecard", "missed")
        },
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        archived_result_surfaces=archive.gate_surface_contracts(),
    )
    source_path = accelerated / names["source"]
    source_raw = bytearray(source_path.read_bytes())
    source_raw[-2] ^= 1
    source_path.write_bytes(source_raw)
    campaign = json.loads(archive.campaign_manifest_path.read_bytes())
    shard = json.loads(Path(campaign["shards"][0]["manifest_path"]).read_bytes())
    compressed_path = Path(shard["surfaces"][0]["compressed_path"])
    compressed_raw = bytearray(compressed_path.read_bytes())
    compressed_raw[len(compressed_raw) // 2] ^= 1
    compressed_path.write_bytes(compressed_raw)

    with pytest.raises(ValueError, match="archive_compressed_identity_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_independent_verifier_checks_archive_root_for_every_role(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import build_gate_request
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(tmp_path)
    archive = StreamingProofArchive(
        root=tmp_path / "archive-role-root",
        output_prefix=prefix,
        hot_outputs={
            role: accelerated / names[role]
            for role in ("decision", "scorecard", "missed")
        },
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        archived_result_surfaces=archive.gate_surface_contracts(),
    )
    scorecard = next(
        row
        for row in request["persisted_result_surfaces"]
        if row["role"] == "scorecard"
    )
    scorecard["archive_campaign_manifest_root_sha256"] = "f" * 64
    request.pop("gate_request_root_sha256")
    request["gate_request_root_sha256"] = _root(request)

    with pytest.raises(ValueError, match="archive_campaign_identity_mismatch"):
        verify_real_parity(
            golden_manifest_path=manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_real_parity_verifier_does_not_import_writer_runner_or_gate() -> None:
    verifier = Path(
        "src/research_infra/replay_acceleration_real_parity_verifier.py"
    )
    tree = ast.parse(verifier.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = (
        "replay_acceleration_real_gate",
        "replay_semantic_parity",
        "replay_semantic_diagnostic",
        "run_broad_live_as_if_replay_harness",
        "replay_acceleration_attempt5_typed_sparse_runner",
        "v4_timewarp_simulated_live_research_loop",
    )
    assert not any(any(item in value for item in forbidden) for value in imports)


def test_exact_gate_and_verifier_remain_independent_from_semantic_diagnostics() -> None:
    forbidden = ("replay_semantic_parity", "replay_semantic_diagnostic")
    for path in (
        Path("src/research_infra/replay_acceleration_real_gate.py"),
        Path("src/research_infra/replay_acceleration_real_parity_verifier.py"),
    ):
        source = path.read_text(encoding="utf-8")
        assert not any(module in source for module in forbidden)


def test_partial_summary_projection_is_top_level_allowlisted_and_fail_closed() -> None:
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        partial_semantic_contract,
    )

    reference = {
        "schema": "synthetic.partial.v1",
        "output_prefix": "synthetic-prefix",
        "status": "partial",
        "generated_at_utc": "runtime-a",
        "source_acceleration_authority": {"mode": "reference"},
        "progress_rows": [
            {
                "generated_at_utc": "causal-nested-a",
                "selected_order_sequence": 1,
            }
        ],
        "runtime_evidence_contract": {"identity": "exact-a"},
        "future_semantic_field": {"status": "exact-a"},
    }
    top_level_runtime_only = copy.deepcopy(reference)
    top_level_runtime_only["generated_at_utc"] = "runtime-b"
    assert partial_semantic_contract(reference) == partial_semantic_contract(
        top_level_runtime_only
    )

    acceleration_authority = copy.deepcopy(reference)
    acceleration_authority["source_acceleration_authority"] = {
        "mode": "accelerated"
    }
    assert partial_semantic_contract(reference) != partial_semantic_contract(
        acceleration_authority
    )

    nested_timestamp = copy.deepcopy(reference)
    nested_timestamp["progress_rows"][0]["generated_at_utc"] = "causal-nested-b"
    assert partial_semantic_contract(reference) != partial_semantic_contract(
        nested_timestamp
    )

    runtime_contract = copy.deepcopy(reference)
    runtime_contract["runtime_evidence_contract"]["identity"] = "exact-b"
    assert partial_semantic_contract(reference) != partial_semantic_contract(
        runtime_contract
    )

    unknown = copy.deepcopy(reference)
    unknown["future_semantic_field"]["status"] = "exact-b"
    assert partial_semantic_contract(reference) != partial_semantic_contract(unknown)


def test_gate_request_binds_prospective_golden_amendment_and_fixed_verifier(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        build_gate_request,
    )
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    authority = _prospective_golden_authority(manifest)
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        prospective_golden_authority=authority,
    )

    assert request["prospective_golden_authority"] == authority
    assert request["accelerated_namespace_path"] == str(accelerated.resolve())
    substituted_manifest = tmp_path / "substituted-golden-manifest.json"
    substituted_manifest.write_bytes(manifest.read_bytes())
    with pytest.raises(
        ValueError,
        match="gate_request_golden_authority_mismatch",
    ):
        verify_real_parity(
            golden_manifest_path=substituted_manifest,
            accelerated_namespace=accelerated,
            gate_request=request,
        )


def test_gate_recomputes_fixed_verifier_before_authorizing_persisted_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_real_parity_verifier
    from src.research_infra.replay_acceleration_real_gate import (
        GateRejected,
        build_gate_request,
        wait_for_parity_receipt,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        prospective_golden_authority=_prospective_golden_authority(manifest),
    )
    report, receipt = replay_acceleration_real_parity_verifier.verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    report_path = accelerated / "PARITY_REPORT.json"
    receipt_path = accelerated / "PARITY_RECEIPT.json"
    report_path.write_bytes(_canonical(report) + b"\n")
    receipt_path.write_bytes(_canonical(receipt) + b"\n")

    def fail_recomputation(**_: object) -> object:
        raise AssertionError("fixed verifier recomputation was required")

    monkeypatch.setattr(
        replay_acceleration_real_parity_verifier,
        "verify_real_parity",
        fail_recomputation,
    )
    with pytest.raises(
        GateRejected,
        match="parity_verifier_recompute_failed",
    ):
        wait_for_parity_receipt(
            receipt_path=receipt_path,
            report_path=report_path,
            gate_request=request,
            timeout_seconds=1,
            poll_seconds=0.01,
        )


def test_gate_rejects_report_surfaces_that_differ_from_request(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        GateRejected,
        build_gate_request,
        validate_parity_receipt,
    )
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        prospective_golden_authority=_prospective_golden_authority(manifest),
    )
    report, receipt = verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    report = copy.deepcopy(report)
    report["persisted_result_surfaces"][0]["bytes"] += 1
    report["persisted_result_surface_root_sha256"] = _root(
        report["persisted_result_surfaces"]
    )
    report.pop("report_root_sha256")
    report["report_root_sha256"] = _root(report)
    receipt = dict(receipt)
    receipt["persisted_result_surface_root_sha256"] = report[
        "persisted_result_surface_root_sha256"
    ]
    receipt["parity_report_root_sha256"] = report["report_root_sha256"]
    receipt.pop("receipt_root_sha256")
    receipt["receipt_root_sha256"] = _root(receipt)

    with pytest.raises(
        GateRejected,
        match="parity_report_surface_request_mismatch",
    ):
        validate_parity_receipt(
            receipt,
            gate_request=request,
            parity_report=report,
        )


def test_gate_nofollow_read_rejects_report_swap_after_regular_file_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra.replay_acceleration_real_gate import (
        GateRejected,
        build_gate_request,
        wait_for_parity_receipt,
    )
    from src.research_infra.replay_acceleration_real_parity_verifier import (
        verify_real_parity,
    )

    prefix, _golden, accelerated, names, manifest = _make_equal_namespaces(
        tmp_path
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated / f"{prefix}_PARTIAL_SUMMARY.json"
    request = _build_bound_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256="2" * 64,
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        prospective_golden_authority=_prospective_golden_authority(manifest),
    )
    report, receipt = verify_real_parity(
        golden_manifest_path=manifest,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    report_path = accelerated / "PARITY_REPORT.json"
    receipt_path = accelerated / "PARITY_RECEIPT.json"
    outside_report = tmp_path / "outside-valid-report.json"
    outside_report.write_bytes(_canonical(report) + b"\n")
    report_path.write_bytes(outside_report.read_bytes())
    receipt_path.write_bytes(_canonical(receipt) + b"\n")

    original_is_file = Path.is_file
    swapped = False

    def swap_after_check(path: Path) -> bool:
        nonlocal swapped
        result = original_is_file(path)
        if path == report_path and result and not swapped:
            path.unlink()
            path.symlink_to(outside_report)
            swapped = True
        return result

    monkeypatch.setattr(Path, "is_file", swap_after_check)
    with pytest.raises(
        GateRejected,
        match=(
            "parity_evidence_(symlink_forbidden|invalid|changed_during_read)"
        ),
    ):
        wait_for_parity_receipt(
            receipt_path=receipt_path,
            report_path=report_path,
            gate_request=request,
            timeout_seconds=1,
            poll_seconds=0.01,
        )


def _reroot_shared_contract(contract: dict[str, object]) -> None:
    projection = {
        key: item
        for key, item in contract.items()
        if key
        not in {
            "exact_profile_config_roots_sha256",
            "exact_risk_profile_bindings",
            "valid",
            "status",
            "shared_execution_contract_digest_sha256",
        }
    }
    contract["shared_execution_contract_digest_sha256"] = _root(projection)


def _proof_only_successor_contracts() -> tuple[
    dict[str, object],
    dict[str, object],
]:
    legacy, _legacy_digest = _shared_execution_contract(
        code_path="runner.py",
        code_hash="a" * 64,
    )
    legacy["exact_profile_config_roots_sha256"] = {"profile": "f" * 64}
    legacy["exact_risk_profile_bindings"] = {
        "profile": {
            "path": "synthetic-risk-profile.json",
            "sha256": "e" * 64,
        }
    }
    accelerated = copy.deepcopy(legacy)
    accelerated["code_authority"] = [
        {"path": "runner.py", "sha256": "b" * 64},
        {"path": "verifier.py", "sha256": "c" * 64},
    ]
    accelerated["execution_options"].update(
        {
            "parity_gate_after_day": "2026-01-07",
            "parity_gate_requires_independent_receipt": True,
            "streaming_proof_archive_enabled": True,
            "streaming_proof_archive_hot_roles": [
                "decision",
                "scorecard",
                "missed",
            ],
            "max_streaming_proof_archive_bytes": 1024,
            "source_acceleration": {
                "source_bundle_root_sha256": "d" * 64,
                "policy_execution_entered": False,
            },
        }
    )
    _reroot_shared_contract(accelerated)
    return legacy, accelerated


def test_no_replay_preflight_accepts_only_proof_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_real_gate as gate
    from src.research_infra.replay_acceleration_contract_split import (
        split_shared_execution_contract,
    )

    legacy, accelerated = _proof_only_successor_contracts()
    economic_digest = split_shared_execution_contract(legacy)[
        "economic_execution_contract_digest_sha256"
    ]
    authority = {
        key: "a" * 64
        for key in gate.PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS
    }
    authority.update(
        {
            "fixed_verifier_module": gate.FIXED_VERIFIER_MODULE,
            "fixed_verifier_code_authority": {},
            "economic_execution_contract_digest_sha256": economic_digest,
        }
    )
    golden_partial = {"shared_execution_contract": legacy}
    golden_raw = (
        json.dumps(golden_partial, sort_keys=True).encode("utf-8") + b"\n"
    )
    monkeypatch.setattr(
        gate,
        "_validated_prospective_golden_authority",
        lambda _authority: authority,
    )
    monkeypatch.setattr(
        gate,
        "_golden_partial_from_authority",
        lambda _authority: (
            golden_partial,
            tmp_path / "golden-partial.json",
            golden_raw,
        ),
    )

    receipt = gate.no_replay_contract_preflight(
        prospective_golden_authority=authority,
        current_shared_execution_contract=accelerated,
    )

    assert receipt["gate"] == (
        "LATEST_GOLDEN_ECONOMIC_CONTRACT_PREFLIGHT_ACCEPTED"
    )
    assert receipt["policy_execution_entered"] is False
    assert receipt["continuation_authorized"] is False
    assert receipt["economic_values_exposed"] is False
    changed_economics = copy.deepcopy(accelerated)
    changed_economics["execution_options"][
        "max_candidates_per_symbol_window"
    ] = 1
    _reroot_shared_contract(changed_economics)
    with pytest.raises(
        gate.GateRejected,
        match="economic_execution_contract_mismatch",
    ):
        gate.no_replay_contract_preflight(
            prospective_golden_authority=authority,
            current_shared_execution_contract=changed_economics,
        )


def test_no_replay_preflight_binds_source_consumer_rebind_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_real_gate as gate
    from src.research_infra.replay_acceleration_contract_split import (
        split_shared_execution_contract,
    )

    legacy, accelerated = _proof_only_successor_contracts()
    rebind_core = {
        "schema": (
            "gtos.replay_acceleration."
            "bound_source_bundle_consumer_rebind_authority.v1"
        ),
        "authority_root_sha256": "8" * 64,
        "policy_execution_entered": False,
        "continuation_authorized": False,
        "broker_live_authority": False,
        "economic_values_exposed": False,
    }
    rebind = {
        **rebind_core,
        "binding_root_sha256": _root(rebind_core),
    }
    accelerated["execution_options"]["source_acceleration"][
        "source_bundle_consumer_rebind_authority"
    ] = rebind
    _reroot_shared_contract(accelerated)
    economic_digest = split_shared_execution_contract(legacy)[
        "economic_execution_contract_digest_sha256"
    ]
    authority = {
        key: "a" * 64
        for key in gate.PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS
    }
    authority.update(
        {
            "fixed_verifier_module": gate.FIXED_VERIFIER_MODULE,
            "fixed_verifier_code_authority": {},
            "economic_execution_contract_digest_sha256": economic_digest,
        }
    )
    golden_partial = {"shared_execution_contract": legacy}
    golden_raw = (
        json.dumps(golden_partial, sort_keys=True).encode("utf-8") + b"\n"
    )
    monkeypatch.setattr(
        gate,
        "_validated_prospective_golden_authority",
        lambda _authority: authority,
    )
    monkeypatch.setattr(
        gate,
        "_golden_partial_from_authority",
        lambda _authority: (
            golden_partial,
            tmp_path / "golden-partial.json",
            golden_raw,
        ),
    )

    receipt = gate.no_replay_contract_preflight(
        prospective_golden_authority=authority,
        current_shared_execution_contract=accelerated,
        source_bundle_consumer_rebind_authority=rebind,
    )

    assert receipt["source_bundle_consumer_rebind_authority"] == rebind
    mismatched = dict(rebind)
    mismatched["authority_root_sha256"] = "9" * 64
    with pytest.raises(
        gate.GateRejected,
        match="source_consumer_rebind_authority_mismatch",
    ):
        gate.no_replay_contract_preflight(
            prospective_golden_authority=authority,
            current_shared_execution_contract=accelerated,
            source_bundle_consumer_rebind_authority=mismatched,
        )


def test_v2_fixed_verifier_accepts_narrow_acceleration_envelope_and_rejects_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_real_gate as gate
    from src.research_infra import replay_acceleration_real_parity_verifier as verifier
    from src.research_infra.replay_acceleration_contract_split import (
        split_shared_execution_contract,
    )

    legacy_contract, accelerated_contract = _proof_only_successor_contracts()
    runner_code_path = (
        "src/research_infra/"
        "replay_acceleration_attempt5_typed_sparse_runner.py"
    )
    runner_path = ROOT / runner_code_path
    runner_sha256 = hashlib.sha256(runner_path.read_bytes()).hexdigest()
    accelerated_contract["code_authority"][0]["path"] = runner_code_path
    accelerated_contract["code_authority"][0]["sha256"] = runner_sha256
    source_rebind_core = {
        "schema": (
            "gtos.replay_acceleration."
            "bound_source_bundle_consumer_rebind_authority.v1"
        ),
        "authority": {
            "authority_root_sha256": "8" * 64,
            "policy_execution_entered": False,
            "continuation_authorized": False,
            "broker_live_authority": False,
            "economic_values_exposed": False,
        },
        "authority_path": str(tmp_path / "source-rebind-authority.json"),
        "authority_file_sha256": "0" * 64,
        "authority_root_sha256": "8" * 64,
        "source_plan_digest_sha256": "2" * 64,
        "verified_successor_bundle": {
            "path": str(tmp_path / "source-bundle.json"),
            "file_sha256": "1" * 64,
            "bundle_root_sha256": "d" * 64,
            "implementation_root_sha256": "2" * 64,
        },
        "verified_successor_selection": {
            "path": str(tmp_path / "source-selection.json"),
            "file_sha256": "3" * 64,
            "selection_root_sha256": "e" * 64,
        },
        "policy_execution_entered": False,
        "continuation_authorized": False,
        "broker_live_authority": False,
        "economic_values_exposed": False,
    }
    source_rebind = {
        **source_rebind_core,
        "binding_root_sha256": _root(source_rebind_core),
    }
    shared_source_authority = {
        "schema": "gtos.replay_acceleration.real_source_authority.v1",
        "source_bundle_root_sha256": "d" * 64,
        "selection_root_sha256": "e" * 64,
        "source_plan_digest_sha256": "2" * 64,
        "config_projection_root_sha256": "f" * 64,
        "normalizer_code_root_sha256": "4" * 64,
        "partition_count": 1,
        "symbol_count": 1,
        "policy_execution_entered": False,
        "candidate_cache_enabled": False,
        "policy_state_cache_enabled": False,
        "source_bundle_consumer_rebind_authority": source_rebind,
        "prewarm_worker_count": 2,
    }
    accelerated_contract["execution_options"]["source_acceleration"] = (
        shared_source_authority
    )
    _reroot_shared_contract(accelerated_contract)
    legacy_digest = legacy_contract[
        "shared_execution_contract_digest_sha256"
    ]
    accelerated_digest = accelerated_contract[
        "shared_execution_contract_digest_sha256"
    ]
    golden_partial = {
        "schema": "synthetic.partial.v1",
        "output_prefix": "synthetic-prefix",
        "semantic_identity": {"candidate_root": "1" * 64},
        "route_id": "sealed-legacy-route",
        "generated_at_utc": "legacy",
        "ledger_file_bytes_flushed_before_partial_summary": {
            "decision": 873_489_469,
            "scorecard": 734_994_050,
            "missed": 1_578_738_408,
            "order": 21_882_447,
        },
        "capacity_safe_chunk_execution_contract": {
            "completed_chunk_count": 1,
            "checkpoints": [
                {
                    "chunk_id": "profile:development:2026-01-01:2026-01-01",
                    "account_object_continuity": True,
                    "broker_object_continuity": True,
                    "gc_collected_objects": 7,
                }
            ],
        },
        "shared_execution_contract": legacy_contract,
        "b7_5_contract_binding": {
            "actual_shared_execution_contract_digest_sha256": legacy_digest,
            "expected_shared_execution_contract_digest_sha256": legacy_digest,
            "source_plan_digest_sha256": "2" * 64,
        },
    }
    accelerated_partial = copy.deepcopy(golden_partial)
    accelerated_partial.update(
        {
            "route_id": "ATTEMPT5_S0R0_JAN1_7_PARITY_20260721T150408Z",
            "generated_at_utc": "accelerated",
            "real_s0r0_parity_gate": None,
            "ledger_file_bytes_flushed_before_partial_summary": {
                **golden_partial[
                    "ledger_file_bytes_flushed_before_partial_summary"
                ],
                "decision": 157_398_478,
                "scorecard": 195_407_187,
                "missed": 415_712_442,
            },
            "capacity_safe_chunk_execution_contract": {
                **golden_partial["capacity_safe_chunk_execution_contract"],
                "checkpoints": [
                    {
                        **golden_partial[
                            "capacity_safe_chunk_execution_contract"
                        ]["checkpoints"][0],
                        "gc_collected_objects": 36_732_125,
                    }
                ],
            },
            "shared_execution_contract": accelerated_contract,
            "b7_5_contract_binding": {
                **golden_partial["b7_5_contract_binding"],
                "actual_shared_execution_contract_digest_sha256": (
                    accelerated_digest
                ),
                "expected_shared_execution_contract_digest_sha256": (
                    accelerated_digest
                ),
            },
        }
    )
    golden_path = tmp_path / "golden-partial.json"
    accelerated_path = tmp_path / "accelerated-partial.json"
    golden_path.write_text(
        json.dumps(golden_partial, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    accelerated_path.write_text(
        json.dumps(accelerated_partial, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    golden_raw = golden_path.read_bytes()
    split = split_shared_execution_contract(accelerated_contract)
    economic_digest = split[
        "economic_execution_contract_digest_sha256"
    ]
    implementation_root = split[
        "accelerator_implementation_authority_root_sha256"
    ]
    runtime_inputs = {}
    required_runtime_inputs = {
        "member_axis",
        "sleeve_registry",
        "reconstructed_selection",
        "accepted_member_ledger",
        "fillability_labels",
    }
    for name in (
        "accepted_member_ledger",
        "fillability_labels",
        "member_axis",
        "pending_source_coverage",
        "reconstructed_selection",
        "sleeve_registry",
        "source_materializer",
    ):
        path = tmp_path / f"{name}.jsonl"
        if name in required_runtime_inputs:
            runtime_inputs[name] = {
                "path": str(path),
                "present": True,
                "required_by_actual_replay_path": True,
                "bytes": 1,
                "sha256": "5" * 64,
            }
        else:
            runtime_inputs[name] = {
                "path": str(path),
                "present": False,
                "required_by_actual_replay_path": False,
            }
    runtime_core = {
        "schema": "gtos.replay_acceleration.runtime_evidence_root.v1",
        "root": str(tmp_path),
        "integration_repo_root": str(tmp_path),
        "data_roots": [str(tmp_path / "data")],
        "inputs": runtime_inputs,
        "legacy_evidence_mutation_enabled": False,
        "read_only_existing_evidence": True,
    }
    accelerated_partial["runtime_evidence_contract"] = {
        **runtime_core,
        "contract_root_sha256": _root(runtime_core),
    }
    accelerated_partial["source_acceleration_authority"] = {
        **{
            key: copy.deepcopy(value)
            for key, value in shared_source_authority.items()
            if key != "prewarm_worker_count"
        },
        "cross_symbol_prewarm_barrier": {
            "requested": True,
            "worker_count": 2,
            "barrier_complete": True,
            "seconds": 0.25,
            "partition_count": 1,
            "partition_set_root_sha256": "6" * 64,
        },
        "bundle_validation_seconds": 0.125,
        "typed_cache_metrics": {
            "bytes_read": 10,
            "bytes_written": 5,
            "cold_partition_count": 1,
            "hashing_seconds": 0.01,
            "normalization_seconds": 0.02,
            "normalized_row_count": 3,
            "serialization_seconds": 0.03,
            "verification_seconds": 0.04,
            "warm_partition_count": 2,
        },
    }
    prospective_authority = {"fixture_authority_root_sha256": "7" * 64}
    tick_manifest_path = tmp_path / "tick-manifest.json"
    diagnostic_manifest_path = tmp_path / "diagnostic-manifest.json"

    def write_tick_manifest(
        path: Path,
        *,
        start: str,
        end: str,
        label: str,
    ) -> str:
        payload = {
            "schema_version": "mt5_research_tick_export_v1",
            "read_only": True,
            "account": {},
            "chunk_minutes": 60,
            "created_at_utc": "2026-07-20T00:00:00+00:00",
            "errors": [],
            "files": {"XAUUSD_window_TICK": {"sha256": "1" * 64}},
            "label": label,
            "manifest_path": path.name,
            "mt5_client_kind": "synthetic_read_only_test",
            "output_dir": ".",
            "source_provenance": {
                "source_role": "owner_authorized_research_hydration"
            },
            "symbols": [{"file_symbol": "XAUUSD", "mt5_symbol": "XAUUSD"}],
            "terminal": {},
            "windows": [{"start": start, "end": end, "label": "window"}],
        }
        path.write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return hashlib.sha256(path.read_bytes()).hexdigest()

    tick_manifest_sha256 = write_tick_manifest(
        tick_manifest_path,
        start="2025-10-01T00:00:00+00:00",
        end="2026-04-30T00:00:00+00:00",
        label="main-tick-source",
    )
    diagnostic_manifest_sha256 = write_tick_manifest(
        diagnostic_manifest_path,
        start="2026-04-20T00:00:00+00:00",
        end="2026-04-21T00:00:00+00:00",
        label="diagnostic-tick-source",
    )
    identity_core = {
        "schema": "gtos.replay_acceleration.attempt5_typed_sparse_identity.v1",
        "status": "ATTEMPT5_TYPED_SPARSE_S0R0_JAN1_7_BOUND",
        "output_namespace": str(accelerated_path.parent),
        "output_prefix": "synthetic-prefix",
        "start_day": "2026-01-01",
        "parity_day": "2026-01-07",
        "contract_end_day": "2026-01-31",
        "arm_id": "S0R0",
        "expected_shared_execution_contract_sha256": accelerated_digest,
        "expected_source_plan_digest_sha256": "2" * 64,
        "expected_arm_fingerprint_sha256": "3" * 64,
        "expected_source_bundle_root_sha256": "d" * 64,
        "expected_tick_source_manifest_sha256": tick_manifest_sha256,
        "prospective_golden_authority": prospective_authority,
        "runner_path": str(runner_path),
        "runner_sha256": runner_sha256,
        "source_bundle_consumer_rebind_authority": source_rebind,
        "source_prewarm_workers": 2,
        "tick_diagnostic_manifest_bindings": [
            {
                "path": str(tmp_path / "diagnostic-manifest.json"),
                "sha256": diagnostic_manifest_sha256,
            }
        ],
        "tick_source_manifest": str(tick_manifest_path),
        "tick_sparse_cache": {
            "schema": "gtos.replay_acceleration.sparse_tick_window_cache.v1",
            "root": str(tmp_path / "tick-cache"),
            "window_start_utc": "2025-12-31T00:00:00+00:00",
            "window_end_utc": "2026-01-09T00:00:00+00:00",
            "source_plan_or_replay_semantics_changed": False,
        },
        "policy_execution_entered": False,
        "legacy_replay_route_invoked": False,
        "other_arms_launched": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    accelerated_partial["attempt5_execution_identity"] = {
        **identity_core,
        "identity_root_sha256": _root(identity_core),
    }
    accelerated_partial["route_id"] = accelerated_path.parent.name
    accelerated_path.write_text(
        json.dumps(accelerated_partial, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        gate,
        "_golden_partial_from_authority",
        lambda _authority: (golden_partial, golden_path, golden_raw),
    )
    transformation = gate._partial_summary_acceleration_envelope_transformation(
        authority=prospective_authority,
        accelerated_partial_path=accelerated_path,
        output_prefix="synthetic-prefix",
        shared_execution_contract_sha256=accelerated_digest,
        economic_execution_contract_sha256=economic_digest,
        accelerator_implementation_authority_root_sha256=implementation_root,
        source_plan_digest_sha256="2" * 64,
        arm_fingerprint_sha256="3" * 64,
        archived_result_surface_roles=frozenset(
            {"decision", "scorecard", "missed"}
        ),
    )
    request = {
        "output_prefix": "synthetic-prefix",
        "prospective_golden_authority": prospective_authority,
        "shared_execution_contract_sha256": accelerated_digest,
        "economic_execution_contract_sha256": economic_digest,
        "accelerator_implementation_authority_root_sha256": implementation_root,
        "source_plan_digest_sha256": "2" * 64,
        "arm_fingerprint_sha256": "3" * 64,
        "persisted_result_surfaces": [
            {"role": role, "storage": "verified_zstd_campaign"}
            for role in ("decision", "scorecard", "missed")
        ],
    }
    with verifier.BoundEvidence() as evidence:
        observed_root, allowed, golden_projection, accelerated_projection = (
            verifier._verify_partial_summary_acceleration_envelope(
                transformation=transformation,
                golden_partial_path=evidence.bind(
                    golden_path,
                    code="golden_partial_invalid",
                ),
                accelerated_partial_path=evidence.bind(
                    accelerated_path,
                    code="accelerated_partial_invalid",
                ),
                golden_partial=golden_partial,
                accelerated_partial=accelerated_partial,
                request=request,
                evidence=evidence,
            )
        )
    assert observed_root == transformation["transformation_root_sha256"]
    assert "shared_execution_contract" in allowed
    assert golden_projection == accelerated_projection
    assert transformation["allowed_nested_changes"] == [
        "capacity_safe_chunk_execution_contract.checkpoints[*].gc_collected_objects",
        "ledger_file_bytes_flushed_before_partial_summary.decision",
        "ledger_file_bytes_flushed_before_partial_summary.scorecard",
        "ledger_file_bytes_flushed_before_partial_summary.missed",
    ]

    def assert_envelope_rejected(
        value: dict[str, object],
        *,
        suffix: str,
        match: str,
    ) -> None:
        path = tmp_path / f"accelerated-{suffix}.json"
        path.write_text(
            json.dumps(value, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        forged = copy.deepcopy(transformation)
        raw = path.read_bytes()
        forged["accelerated_partial_summary"] = {
            "path": str(path),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        forged["transformation_root_sha256"] = verifier.self_root(
            forged,
            "transformation_root_sha256",
        )
        with verifier.BoundEvidence() as evidence:
            with pytest.raises(ValueError, match=match):
                verifier._verify_partial_summary_acceleration_envelope(
                    transformation=forged,
                    golden_partial_path=evidence.bind(
                        golden_path,
                        code="golden_partial_invalid",
                    ),
                    accelerated_partial_path=evidence.bind(
                        path,
                        code="accelerated_partial_invalid",
                    ),
                    golden_partial=golden_partial,
                    accelerated_partial=value,
                    request=request,
                    evidence=evidence,
                )

    missing_identity = copy.deepcopy(accelerated_partial)
    missing_identity.pop("attempt5_execution_identity")
    assert_envelope_rejected(
        missing_identity,
        suffix="missing-identity",
        match="acceleration_envelope_identity_invalid",
    )

    unknown_identity = copy.deepcopy(accelerated_partial)
    unknown_identity["attempt5_execution_identity"]["unknown_key"] = True
    unknown_identity_core = dict(
        unknown_identity["attempt5_execution_identity"]
    )
    unknown_identity_core.pop("identity_root_sha256")
    unknown_identity["attempt5_execution_identity"][
        "identity_root_sha256"
    ] = _root(unknown_identity_core)
    assert_envelope_rejected(
        unknown_identity,
        suffix="unknown-identity",
        match="acceleration_envelope_identity_invalid",
    )

    route_mismatch = copy.deepcopy(accelerated_partial)
    route_mismatch["route_id"] = "another-route"
    assert_envelope_rejected(
        route_mismatch,
        suffix="route-mismatch",
        match="acceleration_envelope_identity_invalid",
    )

    authority_mismatch = copy.deepcopy(accelerated_partial)
    authority_mismatch["attempt5_execution_identity"][
        "prospective_golden_authority"
    ] = {"fixture_authority_root_sha256": "8" * 64}
    authority_identity_core = dict(
        authority_mismatch["attempt5_execution_identity"]
    )
    authority_identity_core.pop("identity_root_sha256")
    authority_mismatch["attempt5_execution_identity"][
        "identity_root_sha256"
    ] = _root(authority_identity_core)
    assert_envelope_rejected(
        authority_mismatch,
        suffix="authority-mismatch",
        match="acceleration_envelope_identity_invalid",
    )

    unknown_runtime = copy.deepcopy(accelerated_partial)
    unknown_runtime["runtime_evidence_contract"]["unknown_key"] = 1
    runtime_projection = dict(unknown_runtime["runtime_evidence_contract"])
    runtime_projection.pop("contract_root_sha256")
    unknown_runtime["runtime_evidence_contract"][
        "contract_root_sha256"
    ] = _root(runtime_projection)
    assert_envelope_rejected(
        unknown_runtime,
        suffix="unknown-runtime",
        match="acceleration_envelope_runtime_evidence_invalid",
    )

    unknown_source = copy.deepcopy(accelerated_partial)
    unknown_source["source_acceleration_authority"]["unknown_key"] = 1
    assert_envelope_rejected(
        unknown_source,
        suffix="unknown-source",
        match="acceleration_envelope_source_authority_invalid",
    )

    tampered_tick_path = tmp_path / "tampered-tick-manifest.json"
    tampered_tick = json.loads(tick_manifest_path.read_bytes())
    tampered_tick["label"] = "tampered"
    tampered_tick_path.write_text(
        json.dumps(tampered_tick, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tampered_tick_identity = copy.deepcopy(accelerated_partial)
    tampered_tick_identity["attempt5_execution_identity"][
        "tick_source_manifest"
    ] = str(tampered_tick_path)
    tampered_tick_core = dict(
        tampered_tick_identity["attempt5_execution_identity"]
    )
    tampered_tick_core.pop("identity_root_sha256")
    tampered_tick_identity["attempt5_execution_identity"][
        "identity_root_sha256"
    ] = _root(tampered_tick_core)
    assert_envelope_rejected(
        tampered_tick_identity,
        suffix="tampered-tick-manifest",
        match="acceleration_envelope_tick_manifest_invalid",
    )

    bad_diagnostic_hash = copy.deepcopy(accelerated_partial)
    bad_diagnostic_hash["attempt5_execution_identity"][
        "tick_diagnostic_manifest_bindings"
    ][0]["sha256"] = "a" * 64
    bad_diagnostic_core = dict(
        bad_diagnostic_hash["attempt5_execution_identity"]
    )
    bad_diagnostic_core.pop("identity_root_sha256")
    bad_diagnostic_hash["attempt5_execution_identity"][
        "identity_root_sha256"
    ] = _root(bad_diagnostic_core)
    assert_envelope_rejected(
        bad_diagnostic_hash,
        suffix="bad-diagnostic-hash",
        match="acceleration_envelope_tick_manifest_invalid",
    )

    copied_runner_path = tmp_path / runner_path.name
    copied_runner_path.write_bytes(runner_path.read_bytes())
    noncanonical_runner = copy.deepcopy(accelerated_partial)
    noncanonical_runner["attempt5_execution_identity"]["runner_path"] = str(
        copied_runner_path
    )
    noncanonical_runner_core = dict(
        noncanonical_runner["attempt5_execution_identity"]
    )
    noncanonical_runner_core.pop("identity_root_sha256")
    noncanonical_runner["attempt5_execution_identity"][
        "identity_root_sha256"
    ] = _root(noncanonical_runner_core)
    assert_envelope_rejected(
        noncanonical_runner,
        suffix="noncanonical-runner",
        match="acceleration_envelope_runner_invalid",
    )

    unknown_partial = copy.deepcopy(accelerated_partial)
    unknown_partial["unclassified_future_surface"] = {"value": 1}
    unknown_path = tmp_path / "accelerated-unknown.json"
    unknown_path.write_text(
        json.dumps(unknown_partial, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    forged = copy.deepcopy(transformation)
    unknown_raw = unknown_path.read_bytes()
    forged["accelerated_partial_summary"] = {
        "path": str(unknown_path),
        "bytes": len(unknown_raw),
        "sha256": hashlib.sha256(unknown_raw).hexdigest(),
    }
    forged["transformation_root_sha256"] = verifier.self_root(
        forged,
        "transformation_root_sha256",
    )
    with verifier.BoundEvidence() as evidence:
        with pytest.raises(
            ValueError,
            match="acceleration_envelope_semantic_mismatch",
        ):
            verifier._verify_partial_summary_acceleration_envelope(
                transformation=forged,
                golden_partial_path=evidence.bind(
                    golden_path,
                    code="golden_partial_invalid",
                ),
                accelerated_partial_path=evidence.bind(
                    unknown_path,
                    code="accelerated_partial_invalid",
                ),
                golden_partial=golden_partial,
                accelerated_partial=unknown_partial,
                request=request,
                evidence=evidence,
            )

    unknown_nested_partial = copy.deepcopy(accelerated_partial)
    unknown_nested_partial["capacity_safe_chunk_execution_contract"][
        "checkpoints"
    ][0]["selected_order_sequence_monotonic"] = False
    unknown_nested_path = tmp_path / "accelerated-unknown-nested.json"
    unknown_nested_path.write_text(
        json.dumps(unknown_nested_partial, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    forged = copy.deepcopy(transformation)
    unknown_nested_raw = unknown_nested_path.read_bytes()
    forged["accelerated_partial_summary"] = {
        "path": str(unknown_nested_path),
        "bytes": len(unknown_nested_raw),
        "sha256": hashlib.sha256(unknown_nested_raw).hexdigest(),
    }
    forged["transformation_root_sha256"] = verifier.self_root(
        forged,
        "transformation_root_sha256",
    )
    with verifier.BoundEvidence() as evidence:
        with pytest.raises(
            ValueError,
            match="acceleration_envelope_semantic_mismatch",
        ):
            verifier._verify_partial_summary_acceleration_envelope(
                transformation=forged,
                golden_partial_path=evidence.bind(
                    golden_path,
                    code="golden_partial_invalid",
                ),
                accelerated_partial_path=evidence.bind(
                    unknown_nested_path,
                    code="accelerated_partial_invalid",
                ),
                golden_partial=golden_partial,
                accelerated_partial=unknown_nested_partial,
                request=request,
                evidence=evidence,
            )


def test_v2_verify_real_parity_consumes_validated_normalized_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_partial_golden as golden
    from src.research_infra import replay_acceleration_real_gate as gate
    from src.research_infra import replay_acceleration_real_parity_verifier as verifier
    from src.research_infra.replay_acceleration_contract_split import (
        split_shared_execution_contract,
    )

    prefix, golden_namespace, accelerated, names, manifest_path = (
        _make_equal_namespaces(tmp_path)
    )
    partial_name = f"{prefix}_PARTIAL_SUMMARY.json"
    golden_partial_path = golden_namespace / partial_name
    accelerated_partial_path = accelerated / partial_name
    golden_partial = json.loads(golden_partial_path.read_bytes())
    accelerated_partial = json.loads(accelerated_partial_path.read_bytes())
    golden_partial["capacity_safe_chunk_execution_contract"]["checkpoints"][0][
        "gc_collected_objects"
    ] = 7
    accelerated_partial["capacity_safe_chunk_execution_contract"][
        "checkpoints"
    ][0]["gc_collected_objects"] = 7007
    golden_partial_path.write_text(
        json.dumps(golden_partial, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    accelerated_partial_path.write_text(
        json.dumps(accelerated_partial, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    manifest = golden.build_partial_golden_manifest(
        namespace=golden_namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=head,
        git_root=ROOT,
        sealed_at_utc="2026-07-20T00:00:00Z",
    )
    successor_shared = copy.deepcopy(
        golden_partial["shared_execution_contract"]
    )
    successor_shared["exact_profile_config_roots_sha256"] = {
        "profile": "f" * 64
    }
    successor_shared["exact_risk_profile_bindings"] = {
        "profile": {
            "path": "synthetic-risk-profile.json",
            "sha256": "e" * 64,
        }
    }
    contract_split = split_shared_execution_contract(successor_shared)
    economic_digest = contract_split[
        "economic_execution_contract_digest_sha256"
    ]
    implementation_root = contract_split[
        "accelerator_implementation_authority_root_sha256"
    ]
    successor_authority_path = tmp_path / "successor-authority.json"
    successor_authority_path.write_bytes(b"{}\n")
    successor_authority_file_sha256 = hashlib.sha256(
        successor_authority_path.read_bytes()
    ).hexdigest()
    successor_authority_root = "a" * 64
    successor_verification_root = "b" * 64
    manifest["schema"] = "gtos.replay_acceleration.partial_golden_manifest.v2"
    manifest["contract_identity"][
        "economic_execution_contract_digest_sha256"
    ] = economic_digest
    manifest["successor_authority"] = {
        "path": str(successor_authority_path),
        "file_sha256": successor_authority_file_sha256,
        "authority_root_sha256": successor_authority_root,
        "verification_root_sha256": successor_verification_root,
        "predecessor_golden_root_sha256": "c" * 64,
    }
    golden_projection = {
        "scope": manifest["scope"],
        "contract_identity": manifest["contract_identity"],
        "legacy_code_authority_root_sha256": manifest[
            "legacy_code_authority"
        ]["authority_root_sha256"],
        "partial_summary": manifest["partial_summary"],
        "checkpoint_projection_root_sha256": manifest[
            "checkpoint_projection_root_sha256"
        ],
        "opaque_result_surface_root_sha256": manifest[
            "opaque_result_surface_root_sha256"
        ],
        "successor_authority_root_sha256": successor_authority_root,
    }
    manifest["golden_root_sha256"] = golden._root(golden_projection)
    manifest["manifest_self_root_sha256"] = golden._self_root(
        manifest,
        "manifest_self_root_sha256",
    )
    manifest_path.write_bytes(golden._canonical_bytes(manifest))
    authority = _prospective_golden_authority(manifest_path)
    fixed_code_authority_root = "d" * 64
    authority.update(
        {
            "successor_authority_path": str(successor_authority_path),
            "successor_authority_file_sha256": (
                successor_authority_file_sha256
            ),
            "successor_authority_root_sha256": successor_authority_root,
            "successor_authority_verification_root_sha256": (
                successor_verification_root
            ),
            "economic_execution_contract_digest_sha256": economic_digest,
            "fixed_verifier_code_authority": {
                "authority_root_sha256": fixed_code_authority_root,
            },
            "fixed_verifier_code_authority_root_sha256": (
                fixed_code_authority_root
            ),
        }
    )
    envelope_root = "e" * 64
    monkeypatch.setattr(
        gate,
        "_validated_prospective_golden_authority",
        lambda _authority: authority,
    )
    monkeypatch.setattr(
        gate,
        "_partial_summary_acceleration_envelope_transformation",
        lambda **_kwargs: {"transformation_root_sha256": envelope_root},
    )
    outputs = {role: accelerated / name for role, name in names.items()}
    outputs["partial_summary"] = accelerated_partial_path
    request = gate.build_gate_request(
        output_prefix=prefix,
        outputs=outputs,
        ledger_row_counts={role: 1 for role in names},
        completed_through_day="2026-01-07",
        source_plan_digest_sha256="1" * 64,
        shared_execution_contract_sha256=golden_partial[
            "shared_execution_contract"
        ]["shared_execution_contract_digest_sha256"],
        arm_id="S0R0",
        arm_fingerprint_sha256="3" * 64,
        prospective_golden_authority=authority,
        economic_execution_contract_sha256=economic_digest,
        accelerator_implementation_authority_root_sha256=implementation_root,
    )

    monkeypatch.setattr(
        verifier,
        "verify_successor_authority",
        lambda _path: {
            "authority_file_sha256": successor_authority_file_sha256,
            "authority_root_sha256": successor_authority_root,
            "verification_root_sha256": successor_verification_root,
        },
    )
    monkeypatch.setattr(
        verifier,
        "_verify_fixed_verifier_code_authority",
        lambda _authority, evidence: fixed_code_authority_root,
    )
    monkeypatch.setattr(
        verifier,
        "verify_partial_golden_manifest",
        lambda _path, git_root: {
            "gate": "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED",
            "semantic_result_values_emitted": False,
            "legacy_evidence_modified": False,
            "manifest_sha256": hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest(),
            "manifest_self_root_sha256": manifest[
                "manifest_self_root_sha256"
            ],
            "golden_root_sha256": manifest["golden_root_sha256"],
            "successor_authority_root_sha256": successor_authority_root,
            "successor_authority_verification_root_sha256": (
                successor_verification_root
            ),
        },
    )

    def normalized_envelope(**_kwargs: object):
        normalized = {
            "semantic_contract_evidence": copy.deepcopy(
                golden_partial["semantic_contract_evidence"]
            )
        }
        return (
            envelope_root,
            frozenset(verifier.ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS),
            copy.deepcopy(normalized),
            copy.deepcopy(normalized),
        )

    monkeypatch.setattr(
        verifier,
        "_verify_partial_summary_acceleration_envelope",
        normalized_envelope,
    )
    report, receipt = verifier.verify_real_parity(
        golden_manifest_path=manifest_path,
        accelerated_namespace=accelerated,
        gate_request=request,
    )
    assert report["gate"] == "EXACT_FULL_RESULT_PARITY_ACCEPTED"
    assert receipt["parity_accepted"] is True


def test_fixed_verifier_output_writer_is_no_clobber(tmp_path: Path) -> None:
    from src.research_infra import replay_acceleration_real_parity_verifier as verifier

    output = tmp_path / "receipt.json"
    verifier.atomic_write(output, {"status": "first"})
    original = output.read_bytes()
    with pytest.raises(
        ValueError,
        match="immutable_parity_output_exists_or_invalid",
    ):
        verifier.atomic_write(output, {"status": "replacement"})
    assert output.read_bytes() == original
    assert output.stat().st_nlink == 1

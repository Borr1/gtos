from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from src.research_infra.replay_acceleration_partial_golden import (
    PartialGoldenError,
    build_partial_golden_manifest,
    build_prospective_amendment,
    write_partial_golden_manifest,
)
from src.research_infra.replay_acceleration_partial_golden_verifier import (
    PartialGoldenVerificationError,
    verify_partial_golden_manifest,
    verify_prospective_amendment,
)
from src.research_infra.replay_acceleration_partial_golden_successor import (
    rebind_partial_summary_source_plan_digest,
)
from src.research_infra.replay_acceleration_partial_golden_successor_authority import (
    SuccessorAuthorityError,
    build_successor_authority,
    verify_successor_authority,
    write_successor_authority,
)


ROOT = Path(__file__).resolve().parents[1]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _manifest_root(value: object) -> str:
    return _sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _reroot(value: dict[str, object], field: str) -> None:
    projection = dict(value)
    projection.pop(field, None)
    value[field] = _manifest_root(projection)


def _reroot_manifest(manifest: dict[str, object]) -> None:
    manifest["checkpoint_projection_root_sha256"] = _manifest_root(
        manifest["bounded_checkpoint_contract"]
    )
    manifest["opaque_result_surface_root_sha256"] = _manifest_root(
        manifest["persisted_result_surfaces"]
    )
    manifest["golden_root_sha256"] = _manifest_root(
        {
            "contract_identity": manifest["contract_identity"],
            "legacy_code_authority_root_sha256": manifest[
                "legacy_code_authority"
            ]["authority_root_sha256"],
            "partial_summary_sha256": manifest["partial_summary"]["sha256"],
            "checkpoint_projection_root_sha256": manifest[
                "checkpoint_projection_root_sha256"
            ],
            "opaque_result_surface_root_sha256": manifest[
                "opaque_result_surface_root_sha256"
            ],
        }
    )
    _reroot(manifest, "manifest_self_root_sha256")


def _git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


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
            "b7_5_selection_sizing_factorial_arm": {
                "arm_id": "S0R0",
                "arm_fingerprint_sha256": "c" * 64,
            },
        },
        "window_identity_excluded_from_shared_digest": True,
        "broker_live_final_authority": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
    }
    digest = _sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return {
        **payload,
        "valid": True,
        "status": "shared_execution_contract_bound",
        "shared_execution_contract_digest_sha256": digest,
    }, digest


def _fixture(
    tmp_path: Path,
    *,
    days: list[str] | None = None,
) -> tuple[Path, str, str]:
    prefix = "BOUNDED_S0R0"
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    code_path = "pyproject.toml"
    code_hash = _sha256(_git_blob(commit, code_path))
    shared_contract, shared_digest = _shared_execution_contract(
        code_path=code_path,
        code_hash=code_hash,
    )

    ledger_rows = {
        "source": [{"day": "2026-01-01"}, {"day": "2026-01-02"}],
        "trade": [{"opaque": "a"}, {"opaque": "b"}],
    }
    sizes: dict[str, int | None] = {
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
    counts: dict[str, int] = {}
    suffix = {
        "source": "SOURCE_UNIVERSE_LEDGER.jsonl",
        "trade": "TRADE_LEDGER.jsonl",
    }
    for role, rows in ledger_rows.items():
        payload = b"".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
            for row in rows
        )
        (tmp_path / f"{prefix}_{suffix[role]}").write_bytes(payload)
        sizes[role] = len(payload)
        counts[role] = len(rows)

    days = days or [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
        "2026-01-05",
        "2026-01-06",
        "2026-01-07",
    ]
    progress = []
    capacity_checkpoints = []
    source_checkpoints = []
    sequence = 0
    for index, day in enumerate(days, start=1):
        next_sequence = sequence + index
        chunk_id = f"profile:development:{day}:{day}"
        progress.append(
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
                "ending_order_sequence": next_sequence,
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
                "canonical_source_plan_digest_sha256": "a" * 64,
                "source_plan_digest_sha256": "a" * 64,
            }
        )
        sequence = next_sequence

    partial = {
        "schema": "gtos.final_moonshot.broad_live_as_if_replay_harness.partial_summary.v1",
        "status": "partial_in_progress_not_final_proof",
        "output_prefix": prefix,
        "profiles_requested": ["profile"],
        "progress_rows": progress,
        "ledger_write_row_counts_so_far": counts,
        "ledger_file_bytes_flushed_before_partial_summary": sizes,
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
            "completed_chunk_count": len(days),
            "cleanup_checkpoint_count": len(days),
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
            "completed_chunk_count": len(days),
            "checkpoint_count": len(days),
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
            "actual_source_plan_digests_sha256": ["a" * 64],
            "expected_shared_execution_contract_digest_sha256": shared_digest,
            "expected_source_plan_digest_sha256": "a" * 64,
        },
        "b7_5_selection_sizing_factorial_arm_binding": {
            "arm_id": "S0R0",
            "arm_fingerprint_sha256": "c" * 64,
            "selection_factor": "S0",
            "sizing_factor": "R0",
            "selection_mode": "neutral_hash_hard_eligible",
            "sizing_mode": "fixed_equal_account_risk",
        },
        "shared_execution_contract": shared_contract,
    }
    partial_path = tmp_path / f"{prefix}_PARTIAL_SUMMARY.json"
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")
    return tmp_path, prefix, commit


def _built_manifest(
    tmp_path: Path,
    *,
    days: list[str] | None = None,
) -> tuple[Path, str, str, dict[str, object], Path]:
    namespace, prefix, commit = _fixture(tmp_path, days=days)
    authorized_days = days or [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
        "2026-01-05",
        "2026-01-06",
        "2026-01-07",
    ]
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day=authorized_days[0],
        end_day=authorized_days[-1],
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    manifest_path = tmp_path / "manifest.json"
    write_partial_golden_manifest(manifest_path, manifest)
    return namespace, prefix, commit, manifest, manifest_path


def test_writer_and_independent_verifier_accept_bounded_complete_checkpoint(
    tmp_path: Path,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    path = tmp_path / "manifest.json"
    write_partial_golden_manifest(path, manifest)

    receipt = verify_partial_golden_manifest(path, git_root=ROOT)

    assert manifest["gate"] == "PARTIAL_GOLDEN_SEALED_FOR_BOUNDED_EQUIVALENCE"
    assert receipt["gate"] == "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED"
    assert receipt["golden_root_sha256"] == manifest["golden_root_sha256"]
    with pytest.raises(
        PartialGoldenError,
        match="immutable_output_exists_or_storage_invalid",
    ):
        write_partial_golden_manifest(path, manifest)


def test_structural_successor_is_accepted_as_latest_exact_golden(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    namespace, prefix, commit = _fixture(source_root)
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    fixture_partial = json.loads(partial_path.read_bytes())
    for role, suffix in {
        "decision": "DECISION_LEDGER.jsonl",
        "scorecard": "SCORECARD_LEDGER.jsonl",
        "order": "ORDER_LEDGER.jsonl",
        "oracle": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "missed": "MISSED_OPPORTUNITY_LEDGER.jsonl",
        "bucket": "BUCKET_LEDGER.jsonl",
    }.items():
        (namespace / f"{prefix}_{suffix}").write_bytes(b"")
        fixture_partial["ledger_file_bytes_flushed_before_partial_summary"][
            role
        ] = 0
        fixture_partial["ledger_write_row_counts_so_far"][role] = 0
    partial_path.write_text(json.dumps(fixture_partial, sort_keys=True) + "\n")
    bound_manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    predecessor = json.loads(partial_path.read_bytes())
    transient_digests: list[str] = []
    for index, day in enumerate(
        [f"2026-01-{value:02d}" for value in range(1, 8)]
    ):
        transient_digest = _sha256(day.encode("ascii"))
        transient_digests.append(transient_digest)
        source_authority = predecessor[
            "source_authority_chunk_invariance_contract"
        ]["checkpoints"][index]
        source_authority["source_plan_digest_sha256"] = transient_digest
        predecessor["progress_rows"][index]["source_authority"] = (
            copy.deepcopy(source_authority)
        )
        predecessor["capacity_safe_chunk_execution_contract"]["checkpoints"][
            index
        ]["source_authority"] = copy.deepcopy(source_authority)
    predecessor_bytes = (
        json.dumps(predecessor, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    partial_path.write_bytes(predecessor_bytes)
    predecessor_manifest = copy.deepcopy(bound_manifest)
    predecessor_manifest["partial_summary"]["bytes"] = len(predecessor_bytes)
    predecessor_manifest["partial_summary"]["sha256"] = _sha256(
        predecessor_bytes
    )
    for index, transient_digest in enumerate(transient_digests):
        predecessor_manifest["bounded_checkpoint_contract"]["source"][
            "checkpoints"
        ][index]["source_plan_digest_sha256"] = transient_digest
    predecessor_manifest["checkpoint_projection_root_sha256"] = _manifest_root(
        predecessor_manifest["bounded_checkpoint_contract"]
    )
    predecessor_manifest["golden_root_sha256"] = _manifest_root(
        {
            "contract_identity": predecessor_manifest["contract_identity"],
            "legacy_code_authority_root_sha256": predecessor_manifest[
                "legacy_code_authority"
            ]["authority_root_sha256"],
            "partial_summary_sha256": predecessor_manifest[
                "partial_summary"
            ]["sha256"],
            "checkpoint_projection_root_sha256": predecessor_manifest[
                "checkpoint_projection_root_sha256"
            ],
            "opaque_result_surface_root_sha256": predecessor_manifest[
                "opaque_result_surface_root_sha256"
            ],
        }
    )
    _reroot(predecessor_manifest, "manifest_self_root_sha256")
    predecessor_manifest_path = tmp_path / "predecessor_manifest.json"
    predecessor_amendment_path = tmp_path / "predecessor_amendment.json"
    predecessor_manifest_receipt_path = (
        tmp_path / "predecessor_manifest_verification.json"
    )
    predecessor_amendment_receipt_path = (
        tmp_path / "predecessor_amendment_verification.json"
    )
    write_partial_golden_manifest(
        predecessor_manifest_path, predecessor_manifest
    )
    predecessor_amendment = build_prospective_amendment(
        predecessor_manifest
    )
    write_partial_golden_manifest(
        predecessor_amendment_path, predecessor_amendment
    )
    predecessor_manifest_raw = predecessor_manifest_path.read_bytes()
    predecessor_amendment_raw = predecessor_amendment_path.read_bytes()
    write_partial_golden_manifest(
        predecessor_manifest_receipt_path,
        {
            "schema": "gtos.replay_acceleration.partial_golden_verification.v1",
            "gate": "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED",
            "manifest_sha256": _sha256(predecessor_manifest_raw),
            "manifest_self_root_sha256": predecessor_manifest[
                "manifest_self_root_sha256"
            ],
            "golden_root_sha256": predecessor_manifest[
                "golden_root_sha256"
            ],
            "opaque_result_surface_root_sha256": predecessor_manifest[
                "opaque_result_surface_root_sha256"
            ],
            "semantic_result_values_emitted": False,
            "legacy_evidence_modified": False,
        },
    )
    write_partial_golden_manifest(
        predecessor_amendment_receipt_path,
        {
            "schema": "gtos.replay_acceleration.partial_golden_amendment_verification.v1",
            "gate": "PROSPECTIVE_AMENDMENT_INDEPENDENTLY_ACCEPTED",
            "manifest_sha256": _sha256(predecessor_manifest_raw),
            "manifest_self_root_sha256": predecessor_manifest[
                "manifest_self_root_sha256"
            ],
            "golden_root_sha256": predecessor_manifest[
                "golden_root_sha256"
            ],
            "amendment_sha256": _sha256(predecessor_amendment_raw),
            "amendment_self_root_sha256": predecessor_amendment[
                "amendment_self_root_sha256"
            ],
            "continuation_authority_active": False,
            "other_arms_authorized": False,
            "broker_live_vps_deployment_authorized": False,
        },
    )
    predecessor_snapshot = tmp_path / "predecessor_snapshot"
    successor_namespace = tmp_path / "successor_namespace"
    predecessor_snapshot.mkdir()
    successor_namespace.mkdir()
    names = {
        predecessor_manifest["partial_summary"]["name"],
        *(
            row["name"]
            for row in predecessor_manifest["persisted_result_surfaces"]
        ),
    }
    for name in names:
        shutil.copy2(namespace / name, predecessor_snapshot / name)
        if name != predecessor_manifest["partial_summary"]["name"]:
            shutil.copy2(namespace / name, successor_namespace / name)
    successor_bytes, successor_receipt = (
        rebind_partial_summary_source_plan_digest(
            predecessor_bytes,
            bound_source_plan_digest_sha256="a" * 64,
        )
    )
    successor_partial_path = (
        successor_namespace / predecessor_manifest["partial_summary"]["name"]
    )
    successor_partial_path.write_bytes(successor_bytes)
    structural_receipt = {
        **successor_receipt,
        "predecessor_partial_summary": str(
            (predecessor_snapshot / predecessor_manifest["partial_summary"]["name"])
            .resolve()
        ),
        "successor_partial_summary": str(successor_partial_path.resolve()),
        "command": [
            "python3",
            "-m",
            "src.research_infra.replay_acceleration_partial_golden_successor",
        ],
    }
    structural_receipt["receipt_root_sha256"] = _manifest_root(
        structural_receipt
    )
    structural_receipt_path = tmp_path / "structural_receipt.json"
    write_partial_golden_manifest(
        structural_receipt_path, structural_receipt
    )
    authority = build_successor_authority(
        predecessor_manifest_path=predecessor_manifest_path.resolve(),
        predecessor_amendment_path=predecessor_amendment_path.resolve(),
        predecessor_manifest_receipt_path=(
            predecessor_manifest_receipt_path.resolve()
        ),
        predecessor_amendment_receipt_path=(
            predecessor_amendment_receipt_path.resolve()
        ),
        structural_successor_receipt_path=structural_receipt_path.resolve(),
        predecessor_snapshot_namespace=predecessor_snapshot.resolve(),
        successor_namespace=successor_namespace.resolve(),
        output_prefix=prefix,
    )
    authority_path = tmp_path / "successor_authority.json"
    write_successor_authority(authority_path, authority)

    verification = verify_successor_authority(authority_path.resolve())
    assert successor_receipt["changed_leaf_count"] == 21
    assert verification["gate"] == (
        "PARTIAL_GOLDEN_SUCCESSOR_AUTHORITY_INDEPENDENTLY_ACCEPTED"
    )
    assert verification["copied_ledger_count"] == 8
    assert verification["economic_values_exposed"] is False

    successor_manifest = build_partial_golden_manifest(
        namespace=successor_namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-21T00:00:00Z",
        successor_authority_path=authority_path.resolve(),
    )
    successor_manifest_path = tmp_path / "successor_manifest.json"
    successor_amendment_path = tmp_path / "successor_amendment.json"
    write_partial_golden_manifest(
        successor_manifest_path, successor_manifest
    )
    successor_amendment = build_prospective_amendment(successor_manifest)
    write_partial_golden_manifest(
        successor_amendment_path, successor_amendment
    )
    manifest_verification = verify_partial_golden_manifest(
        successor_manifest_path,
        git_root=ROOT,
    )
    amendment_verification = verify_prospective_amendment(
        successor_amendment_path,
        successor_manifest_path,
        git_root=ROOT,
    )
    assert successor_manifest["schema"].endswith(".v2")
    assert manifest_verification["successor_authority_verification_root_sha256"]
    assert amendment_verification["successor_authority_root_sha256"] == authority[
        "authority_root_sha256"
    ]

    trade_path = next(
        successor_namespace / row["name"]
        for row in predecessor_manifest["persisted_result_surfaces"]
        if row["role"] == "trade"
    )
    trade_path.write_bytes(trade_path.read_bytes() + b"{}\n")
    with pytest.raises(
        SuccessorAuthorityError,
        match="copied_ledger_identity_mismatch:trade",
    ):
        verify_successor_authority(authority_path.resolve())


def test_writer_rejects_repeated_but_unrecomputed_shared_digest(
    tmp_path: Path,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_bytes())
    drifted_digest = "e" * 64
    partial["shared_execution_contract"][
        "shared_execution_contract_digest_sha256"
    ] = drifted_digest
    partial["b7_5_contract_binding"][
        "actual_shared_execution_contract_digest_sha256"
    ] = drifted_digest
    partial["b7_5_contract_binding"][
        "expected_shared_execution_contract_digest_sha256"
    ] = drifted_digest
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")

    with pytest.raises(
        PartialGoldenError,
        match="shared_execution_digest_recompute_mismatch",
    ):
        build_partial_golden_manifest(
            namespace=namespace,
            output_prefix=prefix,
            start_day="2026-01-01",
            end_day="2026-01-07",
            legacy_code_commit=commit,
            git_root=ROOT,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_writer_rejects_symbolic_legacy_code_commit(tmp_path: Path) -> None:
    namespace, prefix, _commit = _fixture(tmp_path)

    with pytest.raises(
        PartialGoldenError,
        match="legacy_code_commit_not_immutable",
    ):
        build_partial_golden_manifest(
            namespace=namespace,
            output_prefix=prefix,
            start_day="2026-01-01",
            end_day="2026-01-07",
            legacy_code_commit="HEAD",
            git_root=ROOT,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_verifier_rejects_symbolic_legacy_code_commit(tmp_path: Path) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    authority = manifest["legacy_code_authority"]
    authority["legacy_code_commit"] = "HEAD"
    authority_projection = dict(authority)
    authority_projection.pop("authority_root_sha256")
    authority["authority_root_sha256"] = _manifest_root(
        authority_projection
    )
    golden_projection = {
        "contract_identity": manifest["contract_identity"],
        "legacy_code_authority_root_sha256": authority[
            "authority_root_sha256"
        ],
        "partial_summary_sha256": manifest["partial_summary"]["sha256"],
        "checkpoint_projection_root_sha256": manifest[
            "checkpoint_projection_root_sha256"
        ],
        "opaque_result_surface_root_sha256": manifest[
            "opaque_result_surface_root_sha256"
        ],
    }
    manifest["golden_root_sha256"] = _manifest_root(golden_projection)
    manifest_projection = dict(manifest)
    manifest_projection.pop("manifest_self_root_sha256")
    manifest["manifest_self_root_sha256"] = _manifest_root(
        manifest_projection
    )
    path = tmp_path / "symbolic-commit-manifest.json"
    write_partial_golden_manifest(path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="legacy_code_commit_not_immutable",
    ):
        verify_partial_golden_manifest(path, git_root=ROOT)


def test_writer_rejects_noncontiguous_progress(tmp_path: Path) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_text())
    partial["progress_rows"][1]["start_day"] = "2026-01-03"
    partial_path.write_text(json.dumps(partial) + "\n")

    with pytest.raises(PartialGoldenError, match="progress_scope_mismatch"):
        build_partial_golden_manifest(
            namespace=namespace,
            output_prefix=prefix,
            start_day="2026-01-01",
            end_day="2026-01-07",
            legacy_code_commit=commit,
            git_root=ROOT,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_verifier_rejects_undeclared_same_prefix_semantic_proof(
    tmp_path: Path,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    path = tmp_path / "manifest.json"
    write_partial_golden_manifest(path, manifest)
    (namespace / f"{prefix}_SEMANTIC_PROOF.jsonl").write_text(
        '{"schema":"undeclared"}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        PartialGoldenVerificationError,
        match="namespace_inventory_mismatch",
    ):
        verify_partial_golden_manifest(path, git_root=ROOT)


def test_verifier_rejects_opaque_ledger_bit_flip(tmp_path: Path) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    path = tmp_path / "manifest.json"
    write_partial_golden_manifest(path, manifest)
    ledger = namespace / f"{prefix}_TRADE_LEDGER.jsonl"
    payload = bytearray(ledger.read_bytes())
    payload[5] ^= 1
    ledger.write_bytes(payload)

    with pytest.raises(PartialGoldenVerificationError, match="ledger_hash_mismatch"):
        verify_partial_golden_manifest(path, git_root=ROOT)


def test_verifier_rejects_manifest_with_forbidden_result_field(tmp_path: Path) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    manifest["forbidden_pnl_value"] = 1
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest) + "\n")

    with pytest.raises(
        PartialGoldenVerificationError,
        match="manifest_unknown_fields",
    ):
        verify_partial_golden_manifest(path, git_root=ROOT)


@pytest.mark.parametrize(
    ("location", "field", "error_code"),
    [
        ("manifest", "gross_r", "manifest_unknown_fields"),
        ("manifest", "expectancy_r", "manifest_unknown_fields"),
        (
            "outcome_blindness",
            "ending_balance",
            "outcome_blindness_unknown_fields",
        ),
        (
            "outcome_blindness",
            "ending_equity",
            "outcome_blindness_unknown_fields",
        ),
        ("surface", "win_count", "result_surface_unknown_fields"),
        ("surface", "drawdown", "result_surface_unknown_fields"),
    ],
)
def test_verifier_rejects_unknown_economic_fields_fail_closed(
    tmp_path: Path,
    location: str,
    field: str,
    error_code: str,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    if location == "manifest":
        manifest[field] = 1
    elif location == "outcome_blindness":
        manifest["outcome_blindness"][field] = 1
    else:
        manifest["persisted_result_surfaces"][0][field] = 1
    projection = dict(manifest)
    projection.pop("manifest_self_root_sha256")
    manifest["manifest_self_root_sha256"] = _sha256(
        json.dumps(
            projection,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    path = tmp_path / "manifest.json"
    write_partial_golden_manifest(path, manifest)

    with pytest.raises(PartialGoldenVerificationError, match=error_code):
        verify_partial_golden_manifest(path, git_root=ROOT)


@pytest.mark.parametrize(
    ("field", "value", "error_code"),
    [
        ("semantic_result_values_emitted", True, "outcome_blindness_invalid"),
        (
            "persisted_result_files_hashed_as_opaque_bytes",
            False,
            "outcome_blindness_invalid",
        ),
        (
            "manifest_contains_only_structural_counts_and_identities",
            False,
            "outcome_blindness_invalid",
        ),
    ],
)
def test_verifier_rejects_false_outcome_blindness_declarations(
    tmp_path: Path,
    field: str,
    value: bool,
    error_code: str,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    manifest["outcome_blindness"][field] = value
    projection = dict(manifest)
    projection.pop("manifest_self_root_sha256")
    manifest["manifest_self_root_sha256"] = _sha256(
        json.dumps(
            projection,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    path = tmp_path / "manifest.json"
    write_partial_golden_manifest(path, manifest)

    with pytest.raises(PartialGoldenVerificationError, match=error_code):
        verify_partial_golden_manifest(path, git_root=ROOT)


def test_independent_verifier_accepts_only_manifest_bound_amendment(
    tmp_path: Path,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    amendment = build_prospective_amendment(manifest)
    manifest_path = tmp_path / "manifest.json"
    amendment_path = tmp_path / "amendment.json"
    write_partial_golden_manifest(manifest_path, manifest)
    write_partial_golden_manifest(amendment_path, amendment)

    receipt = verify_prospective_amendment(amendment_path, manifest_path)
    assert receipt["gate"] == "PROSPECTIVE_AMENDMENT_INDEPENDENTLY_ACCEPTED"

    amendment["activation"]["jan_8_31_continuation"] = "ACTIVE"
    reroot = dict(amendment)
    reroot.pop("amendment_self_root_sha256")
    amendment["amendment_self_root_sha256"] = _sha256(
        json.dumps(reroot, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    )
    amendment_path.unlink()
    write_partial_golden_manifest(amendment_path, amendment)
    with pytest.raises(PartialGoldenVerificationError, match="continuation_activation_open"):
        verify_prospective_amendment(amendment_path, manifest_path)


def test_amendment_verifier_rejects_unknown_economic_field(
    tmp_path: Path,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    manifest = build_partial_golden_manifest(
        namespace=namespace,
        output_prefix=prefix,
        start_day="2026-01-01",
        end_day="2026-01-07",
        legacy_code_commit=commit,
        git_root=ROOT,
        sealed_at_utc="2026-07-19T00:00:00Z",
    )
    amendment = build_prospective_amendment(manifest)
    amendment["permissions"]["ending_equity"] = 1
    projection = dict(amendment)
    projection.pop("amendment_self_root_sha256")
    amendment["amendment_self_root_sha256"] = _sha256(
        json.dumps(
            projection,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    manifest_path = tmp_path / "manifest.json"
    amendment_path = tmp_path / "amendment.json"
    write_partial_golden_manifest(manifest_path, manifest)
    write_partial_golden_manifest(amendment_path, amendment)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="amendment_permissions_unknown_fields",
    ):
        verify_prospective_amendment(amendment_path, manifest_path)


def test_amendment_verifier_requires_full_manifest_verification(
    tmp_path: Path,
) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    amendment = build_prospective_amendment(manifest)
    manifest["partial_summary"]["sha256"] = "f" * 64
    _reroot(manifest, "manifest_self_root_sha256")
    amendment["partial_golden"]["manifest_self_root_sha256"] = manifest[
        "manifest_self_root_sha256"
    ]
    _reroot(amendment, "amendment_self_root_sha256")
    amendment_path = tmp_path / "amendment.json"
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)
    write_partial_golden_manifest(amendment_path, amendment)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="partial_summary_hash_mismatch",
    ):
        verify_prospective_amendment(amendment_path, manifest_path)


def test_writer_rejects_non_authorized_partial_golden_scope(
    tmp_path: Path,
) -> None:
    days = ["2026-01-01", "2026-01-02"]
    namespace, prefix, commit = _fixture(tmp_path, days=days)

    with pytest.raises(PartialGoldenError, match="authorized_scope_mismatch"):
        build_partial_golden_manifest(
            namespace=namespace,
            output_prefix=prefix,
            start_day=days[0],
            end_day=days[-1],
            legacy_code_commit=commit,
            git_root=ROOT,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_amendment_builder_rejects_non_authorized_scope(
    tmp_path: Path,
) -> None:
    _namespace, _prefix, _commit, manifest, _manifest_path = _built_manifest(
        tmp_path
    )
    manifest["scope"] = {
        **manifest["scope"],
        "start_day": "2026-01-02",
        "end_day": "2026-01-08",
        "days": [
            "2026-01-02",
            "2026-01-03",
            "2026-01-04",
            "2026-01-05",
            "2026-01-06",
            "2026-01-07",
            "2026-01-08",
        ],
    }

    with pytest.raises(PartialGoldenError, match="authorized_scope_mismatch"):
        build_prospective_amendment(manifest)


def test_writer_rejects_checkpoint_source_digest_different_from_bound(
    tmp_path: Path,
) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_bytes())
    partial["source_authority_chunk_invariance_contract"]["checkpoints"][0][
        "source_plan_digest_sha256"
    ] = "b" * 64
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")

    with pytest.raises(
        PartialGoldenError,
        match="source_checkpoint_digest_mismatch",
    ):
        build_partial_golden_manifest(
            namespace=namespace,
            output_prefix=prefix,
            start_day="2026-01-01",
            end_day="2026-01-07",
            legacy_code_commit=commit,
            git_root=ROOT,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_verifier_rejects_checkpoint_source_digest_different_from_bound(
    tmp_path: Path,
) -> None:
    namespace, prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_bytes())
    partial["source_authority_chunk_invariance_contract"]["checkpoints"][0][
        "source_plan_digest_sha256"
    ] = "b" * 64
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")
    partial_raw = partial_path.read_bytes()
    manifest["partial_summary"]["bytes"] = len(partial_raw)
    manifest["partial_summary"]["sha256"] = _sha256(partial_raw)
    manifest["bounded_checkpoint_contract"]["source"]["checkpoints"][0][
        "source_plan_digest_sha256"
    ] = "b" * 64
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="source_checkpoint_digest_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_derives_required_surface_inventory_from_partial_summary(
    tmp_path: Path,
) -> None:
    namespace, prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    manifest["persisted_result_surfaces"] = [
        row
        for row in manifest["persisted_result_surfaces"]
        if row["role"] != "trade"
    ]
    (namespace / f"{prefix}_TRADE_LEDGER.jsonl").unlink()
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="result_surface_inventory_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_rejects_duplicate_surface_role_and_name(
    tmp_path: Path,
) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    manifest["persisted_result_surfaces"].append(
        dict(manifest["persisted_result_surfaces"][0])
    )
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="result_surface_inventory_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_rejects_surface_path_escape_with_basename_decoy(
    tmp_path: Path,
) -> None:
    namespace, prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    trade_path = namespace / f"{prefix}_TRADE_LEDGER.jsonl"
    payload = trade_path.read_bytes()
    trade_path.unlink()
    escaped_name = f"{prefix}_ESCAPED_TRADE_LEDGER.jsonl"
    (namespace.parent / escaped_name).write_bytes(payload)
    (namespace / escaped_name).write_bytes(payload)
    trade_row = next(
        row
        for row in manifest["persisted_result_surfaces"]
        if row["role"] == "trade"
    )
    trade_row["name"] = f"../{escaped_name}"
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="result_surface_name_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_rejects_symlinked_result_surface(tmp_path: Path) -> None:
    namespace, prefix, _commit, _manifest, manifest_path = _built_manifest(
        tmp_path
    )
    trade_path = namespace / f"{prefix}_TRADE_LEDGER.jsonl"
    outside = namespace.parent / f"{namespace.name}-trade-target.jsonl"
    outside.write_bytes(trade_path.read_bytes())
    trade_path.unlink()
    trade_path.symlink_to(outside)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="result_surface_storage_invalid",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_rejects_hardlinked_cross_role_alias(tmp_path: Path) -> None:
    namespace, prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    source_path = namespace / f"{prefix}_SOURCE_UNIVERSE_LEDGER.jsonl"
    trade_path = namespace / f"{prefix}_TRADE_LEDGER.jsonl"
    trade_path.unlink()
    os.link(source_path, trade_path)
    source_row = next(
        row
        for row in manifest["persisted_result_surfaces"]
        if row["role"] == "source"
    )
    trade_row = next(
        row
        for row in manifest["persisted_result_surfaces"]
        if row["role"] == "trade"
    )
    for field in ("bytes", "rows", "sha256"):
        trade_row[field] = source_row[field]
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_bytes())
    partial["ledger_file_bytes_flushed_before_partial_summary"]["trade"] = (
        source_row["bytes"]
    )
    partial["ledger_write_row_counts_so_far"]["trade"] = source_row["rows"]
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")
    partial_raw = partial_path.read_bytes()
    manifest["partial_summary"]["bytes"] = len(partial_raw)
    manifest["partial_summary"]["sha256"] = _sha256(partial_raw)
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="result_surface_storage_invalid",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_requires_canonical_surface_order(tmp_path: Path) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    manifest["persisted_result_surfaces"] = list(
        reversed(manifest["persisted_result_surfaces"])
    )
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="result_surface_inventory_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_rejects_mapping_in_allowed_scalar_slot(
    tmp_path: Path,
) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    manifest["authority_update"] = {"ending_equity": 1}
    _reroot(manifest, "manifest_self_root_sha256")
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="authority_update_invalid",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_writer_rejects_nonhex_arm_fingerprint(tmp_path: Path) -> None:
    namespace, prefix, commit = _fixture(tmp_path)
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_bytes())
    partial["b7_5_selection_sizing_factorial_arm_binding"][
        "arm_fingerprint_sha256"
    ] = "g" * 64
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")

    with pytest.raises(PartialGoldenError, match="arm_fingerprint_invalid"):
        build_partial_golden_manifest(
            namespace=namespace,
            output_prefix=prefix,
            start_day="2026-01-01",
            end_day="2026-01-07",
            legacy_code_commit=commit,
            git_root=ROOT,
            sealed_at_utc="2026-07-19T00:00:00Z",
        )


def test_verifier_cross_binds_scope_profile_to_progress(
    tmp_path: Path,
) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    manifest["scope"]["profile"] = "other-profile"
    _reroot(manifest, "manifest_self_root_sha256")
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="scope_identity_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_cross_binds_partial_summary_name(tmp_path: Path) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    manifest["partial_summary"]["name"] = "OTHER_PARTIAL_SUMMARY.json"
    _reroot(manifest, "manifest_self_root_sha256")
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="partial_summary_identity_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


def test_verifier_cross_binds_capacity_checkpoint_identity(
    tmp_path: Path,
) -> None:
    namespace, prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    partial_path = namespace / f"{prefix}_PARTIAL_SUMMARY.json"
    partial = json.loads(partial_path.read_bytes())
    partial["capacity_safe_chunk_execution_contract"]["checkpoints"][0][
        "split"
    ] = "holdout"
    partial_path.write_text(json.dumps(partial, sort_keys=True) + "\n")
    partial_raw = partial_path.read_bytes()
    manifest["partial_summary"]["bytes"] = len(partial_raw)
    manifest["partial_summary"]["sha256"] = _sha256(partial_raw)
    manifest["bounded_checkpoint_contract"]["capacity"]["checkpoints"][0][
        "split"
    ] = "holdout"
    _reroot_manifest(manifest)
    manifest_path.unlink()
    write_partial_golden_manifest(manifest_path, manifest)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="capacity_identity_mismatch",
    ):
        verify_partial_golden_manifest(manifest_path, git_root=ROOT)


@pytest.mark.parametrize("mutation", ["reverse", "duplicate"])
def test_amendment_required_surfaces_are_exactly_ordered(
    tmp_path: Path,
    mutation: str,
) -> None:
    _namespace, _prefix, _commit, manifest, manifest_path = _built_manifest(
        tmp_path
    )
    amendment = build_prospective_amendment(manifest)
    surfaces = amendment["parity_required_surfaces"]
    if mutation == "reverse":
        amendment["parity_required_surfaces"] = list(reversed(surfaces))
    else:
        amendment["parity_required_surfaces"] = [*surfaces, surfaces[0]]
    _reroot(amendment, "amendment_self_root_sha256")
    amendment_path = tmp_path / "amendment.json"
    write_partial_golden_manifest(amendment_path, amendment)

    with pytest.raises(
        PartialGoldenVerificationError,
        match="parity_surface_contract_mismatch",
    ):
        verify_prospective_amendment(amendment_path, manifest_path)


def test_verifier_does_not_import_writer() -> None:
    source = (
        ROOT
        / "src/research_infra/replay_acceleration_partial_golden_verifier.py"
    ).read_text()
    assert "replay_acceleration_partial_golden import" not in source

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

from compression import zstd
import pytest


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = (
    ROOT
    / "research"
    / "operations"
    / "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
    / "verify_b7_5_post_acceleration_arm.py"
)
SPEC = importlib.util.spec_from_file_location(
    "verify_b7_5_post_acceleration_arm",
    VERIFIER_PATH,
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)
ARCHIVER = importlib.import_module("archive_b7_5_cold_evidence")
DIVERGENCE = importlib.import_module("src.research_infra.divergence_matrix")


def _canonical_sha256(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sealed(value: dict[str, object], field: str) -> dict[str, object]:
    return {**value, field: _canonical_sha256(value)}


def _fixture(tmp_path: Path) -> dict[str, Path]:
    namespace = tmp_path / "arm"
    namespace.mkdir(parents=True)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_B7_5_TEST"
    artifacts: dict[str, dict[str, object]] = {}
    for role in VERIFIER.JSONL_ROLES:
        path = namespace / f"{prefix}{VERIFIER.ROLE_SUFFIXES[role]}"
        path.write_text('{"identity":"opaque"}\n', encoding="utf-8")
        artifacts[role] = {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": _file_sha256(path),
            "rows": 1,
        }
    for role in VERIFIER.JSON_ROLES:
        path = namespace / f"{prefix}{VERIFIER.ROLE_SUFFIXES[role]}"
        _write_json(path, {"status": "opaque"})
        artifacts[role] = {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": _file_sha256(path),
            "status": "opaque",
        }

    decision: dict[str, object] = {
        "schema": VERIFIER.DECISION_SCHEMA,
        "status": VERIFIER.DECISION_STATUS,
        "authority_boundary": {
            "decision_contract_only": True,
            "replay_launched": False,
            "outcomes_evaluated": False,
            "broker_live_final_authority": False,
            "broker_mutation_enabled": False,
            "real_order_transmission_possible": False,
        },
        "self_hash": {
            "algorithm": "sha256",
            "canonicalization": (
                "utf8_json_sort_keys_compact_separators_ensure_ascii"
            ),
            "excluded_path": "self_hash.sha256",
            "sha256": "",
        },
    }
    decision_projection = json.loads(json.dumps(decision))
    decision_projection["self_hash"].pop("sha256")
    decision["self_hash"]["sha256"] = _canonical_sha256(
        decision_projection
    )
    decision_path = tmp_path / "decision.json"
    _write_json(decision_path, decision)

    arm_id = "S0R0"
    source_plan = "9" * 64
    selection_core: dict[str, object] = {
        "schema": "gtos.replay_acceleration.slice_selection.v1",
        "status": "PROSPECTIVE_SOURCE_SELECTION_SEALED",
    }
    selection = _sealed(selection_core, "selection_root_sha256")
    selection_path = tmp_path / "selection.json"
    _write_json(selection_path, selection)
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    bundle_core: dict[str, object] = {
        "schema": "gtos.replay_acceleration.persisted_source_bundle.v1",
        "status": "SEALED",
    }
    bundle = _sealed(bundle_core, "bundle_root_sha256")
    bundle_path = bundle_dir / "bundle.json"
    _write_json(bundle_path, bundle)
    source_core: dict[str, object] = {
        "schema": VERIFIER.SOURCE_AUTHORITY_SCHEMA,
        "status": VERIFIER.SOURCE_AUTHORITY_STATUS,
        "source_plan_digest_sha256": source_plan,
        "bundle": {
            "directory": str(bundle_dir),
            "path": str(bundle_path),
            "file_sha256": _file_sha256(bundle_path),
            "bundle_root_sha256": bundle["bundle_root_sha256"],
            "accepted_cache_implementation_root": "8" * 64,
        },
        "selection": {
            "path": str(selection_path),
            "file_sha256": _file_sha256(selection_path),
            "selection_root_sha256": selection["selection_root_sha256"],
        },
        "source_only": True,
        "policy_execution_entered": False,
        "economic_values_exposed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
    }
    source = _sealed(source_core, "authority_root_sha256")
    source_path = tmp_path / "source-authority.json"
    _write_json(source_path, source)
    source_binding_core = {
        "schema": VERIFIER.BOUND_SOURCE_SCHEMA,
        "authority_path": str(source_path.resolve()),
        "authority_file_sha256": _file_sha256(source_path),
        "authority_root_sha256": source["authority_root_sha256"],
        "authority": source,
        "verified_successor_bundle": {
            "path": str(bundle_path.resolve()),
            "file_sha256": _file_sha256(bundle_path),
            "bundle_root_sha256": bundle["bundle_root_sha256"],
            "implementation_root_sha256": "8" * 64,
        },
        "verified_successor_selection": {
            "path": str(selection_path.resolve()),
            "file_sha256": _file_sha256(selection_path),
            "selection_root_sha256": selection[
                "selection_root_sha256"
            ],
        },
        "source_plan_digest_sha256": source_plan,
        "policy_execution_entered": False,
        "continuation_authorized": False,
        "broker_live_authority": False,
        "economic_values_exposed": False,
    }
    source_binding = {
        "path": str(source_path.resolve()),
        "file_sha256": _file_sha256(source_path),
        "authority_root_sha256": source["authority_root_sha256"],
        "bundle_root_sha256": bundle["bundle_root_sha256"],
        "selection_root_sha256": selection["selection_root_sha256"],
        "source_plan_digest_sha256": source_plan,
        "binding_root_sha256": _canonical_sha256(source_binding_core),
    }

    packs_root = tmp_path / "packs"
    pack_scope = packs_root / "development" / "2026-01-01_2026-01-01"
    shard_dir = pack_scope / "shards"
    shard_dir.mkdir(parents=True)
    raw = b'{"identity":"opaque_prepared"}\n'
    compressed = zstd.compress(raw, level=1)
    shard_path = shard_dir / "shard-00000.jsonl.zst"
    shard_path.write_bytes(compressed)
    record_sha256 = hashlib.sha256(raw[:-1]).hexdigest()
    pack_manifest_core: dict[str, object] = {
        "schema": VERIFIER.PREPARED_PACK_SCHEMA,
        "status": "SEALED",
        "format": "ordered_canonical_jsonl_shards",
        "compression": "zstd_level_1",
        "max_shard_bytes": 128 * 1024 * 1024,
        "max_record_bytes": 128 * 1024 * 1024,
        "target_raw_shard_bytes": 32 * 1024 * 1024,
        "bindings": {
            "days": ["2026-01-01"],
            "symbols": ["XAUUSD"],
            "factor_neutral_config_root_sha256": "6" * 64,
            "source_identity_root_sha256": "7" * 64,
            "max_candidates_per_symbol_window": 0,
        },
        "window_inventory": [
            {
                "record_ordinal": 0,
                "trading_day": "2026-01-01",
                "window_ordinal": 0,
                "decision_time_utc": "2026-01-01T00:00:00Z",
                "record_sha256": record_sha256,
            }
        ],
        "record_count": 1,
        "ordered_record_root_sha256": _canonical_sha256([record_sha256]),
        "shards": [
            {
                "path": "shards/shard-00000.jsonl.zst",
                "shard_index": 0,
                "row_count": 1,
                "first_record_ordinal": 0,
                "last_record_ordinal": 0,
                "raw_bytes": len(raw),
                "compressed_bytes": len(compressed),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
            }
        ],
    }
    pack_manifest = _sealed(
        pack_manifest_core,
        "pack_root_sha256",
    )
    manifest_path = pack_scope / "PREPARED_DAY_PACK_MANIFEST.json"
    _write_json(manifest_path, pack_manifest)
    (pack_scope / "SEALED").write_text(
        f"{pack_manifest['pack_root_sha256']}\n",
        encoding="ascii",
    )
    scope_id = "development:2026-01-01:2026-01-01"
    window = {
        "window_id": "development_january",
        "start": "2026-01-01",
        "end": "2026-01-31",
        "source_plan_digest_sha256": source_plan,
    }
    pack_core: dict[str, object] = {
        "schema": VERIFIER.PACK_AUTHORITY_SCHEMA,
        "status": VERIFIER.PACK_AUTHORITY_STATUS,
        "valid": True,
        "decision_contract_binding": {
            "path": str(decision_path),
            "file_sha256": _file_sha256(decision_path),
            "self_hash_sha256": decision["self_hash"]["sha256"],
        },
        "window_binding": window,
        "source_authority_binding": source_binding,
        "source_selection_semantic_equivalence": {
            "status": "EXACT_RETAINED_FIELDS_EQUAL",
            "meaningful_source_difference_count": 0,
            "unknown_difference_count": 0,
        },
        "prepared_day_pack_root": str(packs_root),
        "prepared_day_pack_roots": {
            scope_id: pack_manifest["pack_root_sha256"]
        },
        "prepared_day_packs": [
            {
                "split": "development",
                "days": ["2026-01-01"],
                "pack_root_sha256": pack_manifest[
                    "pack_root_sha256"
                ],
                "record_count": 1,
                "shard_count": 1,
                "raw_bytes": len(raw),
                "compressed_bytes": len(compressed),
                "factor_reads_detected": False,
                "all_persisted_bytes_authenticated": True,
            }
        ],
        "manifest_bindings": [
            {
                "split": "development",
                "days": ["2026-01-01"],
                "path": str(manifest_path),
                "file_sha256": _file_sha256(manifest_path),
                "bytes": manifest_path.stat().st_size,
                "pack_root_sha256": pack_manifest[
                    "pack_root_sha256"
                ],
                "source_identity_root_sha256": "7" * 64,
                "factor_neutral_config_root_sha256": "6" * 64,
            }
        ],
        "prepared_pack_source_identity_binding": {
            "roots_by_scope": {scope_id: "7" * 64},
            "scope_count": 1,
            "all_scope_roots_explicitly_bound": True,
            "binding_root_sha256": _canonical_sha256(
                {scope_id: "7" * 64}
            ),
        },
        "predecessor_pack_build_transport_reconciliation": {
            "status": "LEGACY_PACK_BUILD_TRANSPORT_EXACTLY_RECONCILED",
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
            "original_seal_relabelled": False,
        },
        "all_persisted_pack_bytes_authenticated": True,
        "factor_reads_forbidden_and_audited": True,
        "factorial_values_present_in_preparation_config": False,
        "policy_execution_entered": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    pack = _sealed(pack_core, "authority_root_sha256")
    pack_path = tmp_path / "pack-authority.json"
    _write_json(pack_path, pack)

    execution_core: dict[str, object] = {
        "schema": VERIFIER.EXECUTION_SCHEMA,
        "status": VERIFIER.EXECUTION_STATUS,
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
        "decision_contract_binding": {
            "path": str(decision_path),
            "file_sha256": _file_sha256(decision_path),
            "self_hash_sha256": decision["self_hash"]["sha256"],
            "schema": decision["schema"],
            "status": decision["status"],
        },
        "window_binding": window,
        "source_authority_binding": {
            **source_binding,
            "fresh_current_bundle": True,
            "policy_execution_entered": False,
        },
        "runner_options": VERIFIER.RUNNER_OPTIONS,
        "arms": {
            current_arm: {
                "arm_fingerprint_sha256": ("a", "b", "c", "d")[
                    index
                ]
                * 64,
                "factorial_binding_payload_sha256": ("1", "2", "3", "4")[
                    index
                ]
                * 64,
                "shared_execution_contract_digest_sha256": (
                    "5",
                    "6",
                    "7",
                    "8",
                )[index]
                * 64,
                "code_authority_root_sha256": "9" * 64,
                "exact_profile_config_root_sha256": (
                    "a",
                    "b",
                    "c",
                    "d",
                )[index]
                * 64,
            }
            for index, current_arm in enumerate(VERIFIER.ARM_ORDER)
        },
        "all_four_arm_shared_digests_unique": True,
        "prepared_day_pack_binding": {
            "required": True,
            "arm_neutral": True,
            "factor_reads_forbidden": True,
            "authority_path": str(pack_path),
            "authority_file_sha256": _file_sha256(pack_path),
            "authority_root_sha256": pack["authority_root_sha256"],
            "prepared_day_pack_root": str(packs_root),
            "prepared_day_pack_roots": pack_core["prepared_day_pack_roots"],
            "source_authority_binding": source_binding,
            "all_persisted_pack_bytes_authenticated_before_seal": True,
            "old_contract_identities_are_provenance_only": True,
        },
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    execution = _sealed(execution_core, "execution_seal_root_sha256")
    execution_path = tmp_path / "execution.json"
    _write_json(execution_path, execution)
    receipt_pack = {
        "path": str(pack_path),
        "file_sha256": _file_sha256(pack_path),
        "authority_root_sha256": pack["authority_root_sha256"],
        "prepared_day_pack_root": str(packs_root),
        "prepared_day_pack_roots": pack_core["prepared_day_pack_roots"],
    }

    inventory_core: dict[str, object] = {
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "ledger_row_counts": {
            role: 1 for role in VERIFIER.JSONL_ROLES
        },
        "completed_summary_status": "opaque",
        "partial_summary_status": "opaque",
        "order_send_attempts_by_profile": {"test": 0},
        "zero_real_order_send_attempts_reconciled": True,
        "all_expected_artifacts_present": True,
        "all_artifacts_regular_non_symlink_files": True,
        "ledger_counts_reconciled_to_completed_summary": True,
    }
    inventory = {
        **inventory_core,
        "inventory_root_sha256": _canonical_sha256(inventory_core),
    }
    receipt_core: dict[str, object] = {
        "schema": "gtos.b7_5.post_acceleration_arm_execution.v1",
        "status": "POST_ACCELERATION_ARM_EXECUTION_COMPLETE",
        "arm_id": arm_id,
        "window": window,
        "namespace": str(namespace),
        "output_prefix": prefix,
        "decision_contract_self_hash_sha256": decision["self_hash"]["sha256"],
        "execution_seal_root_sha256": execution["execution_seal_root_sha256"],
        "arm_fingerprint_sha256": execution_core["arms"][arm_id][
            "arm_fingerprint_sha256"
        ],
        "shared_execution_contract_digest_sha256": execution_core["arms"][
            arm_id
        ]["shared_execution_contract_digest_sha256"],
        "source_authority_binding_root_sha256": source_binding[
            "binding_root_sha256"
        ],
        "prepared_pack_authority": receipt_pack,
        "artifact_inventory": inventory,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    receipt = _sealed(receipt_core, "receipt_root_sha256")
    receipt_path = namespace / "B7_5_POST_ACCELERATION_ARM_RECEIPT.json"
    _write_json(receipt_path, receipt)

    # The divergence matrix is a required acceptance input as of 2026-07-26.  It is
    # written OUTSIDE the arm namespace on purpose: build_arm_artifact_inventory
    # asserts the namespace holds exactly the eleven expected artifact roles, so a
    # twelfth file there would fail the arm.
    matrix_path = tmp_path / "DIVERGENCE_MATRIX.json"
    _write_json(
        matrix_path,
        DIVERGENCE.build_matrix(arm_receipt_path=receipt_path, root=ROOT),
    )
    return {
        "namespace": namespace,
        "decision": decision_path,
        "execution": execution_path,
        "pack": pack_path,
        "receipt": receipt_path,
        "matrix": matrix_path,
        "output": tmp_path / "verification.json",
    }


def test_verifier_authenticates_exact_raw_artifacts_without_economic_rows(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    result = VERIFIER.verify_arm(
        arm_receipt_path=paths["receipt"],
        decision_contract_path=paths["decision"],
        execution_seal_path=paths["execution"],
        divergence_matrix_path=paths["matrix"],
    )

    assert result["status"] == VERIFIER.PASS_STATUS
    assert result["artifact_count"] == len(VERIFIER.REQUIRED_ROLES)
    assert result["economic_values_decoded_or_emitted"] is False
    assert result["all_logical_bytes_verified"] is True
    assert "artifacts" not in result
    assert "verified_artifact_identity_root_sha256" in result
    assert result["outcome_bearing_counts_emitted"] is False


def test_the_verification_receipt_carries_the_transfer_verdict(tmp_path: Path) -> None:
    """An accepted arm now states, in its own receipt, that replay R is not live R."""

    paths = _fixture(tmp_path)
    result = VERIFIER.verify_arm(
        arm_receipt_path=paths["receipt"],
        decision_contract_path=paths["decision"],
        execution_seal_path=paths["execution"],
        divergence_matrix_path=paths["matrix"],
    )
    matrix_block = result["divergence_matrix"]
    assert matrix_block["transfer_verdict"] == DIVERGENCE.VERDICT_BLOCKED
    assert matrix_block["row_count"] > 0
    assert matrix_block["blocks_transfer_count"] > 0
    # The verdict is inside the sealed core, so it cannot be edited out of an
    # accepted arm without changing the verification root.
    core = {k: v for k, v in result.items() if k != "verification_root_sha256"}
    assert VERIFIER._stable_sha256(core) == result["verification_root_sha256"]


def test_verifier_refuses_an_arm_with_no_divergence_matrix(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["matrix"].unlink()
    with pytest.raises(
        VERIFIER.ArmVerificationError, match="divergence_matrix_invalid"
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_refuses_a_divergence_matrix_from_another_arm(tmp_path: Path) -> None:
    """The matrix must be about THIS arm, not any arm."""

    paths = _fixture(tmp_path)
    other = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    other["arm_id"] = "S1R1"
    other = _sealed(
        {k: v for k, v in other.items() if k != "receipt_root_sha256"},
        "receipt_root_sha256",
    )
    other_path = tmp_path / "other_receipt.json"
    _write_json(other_path, other)
    _write_json(
        paths["matrix"],
        DIVERGENCE.build_matrix(arm_receipt_path=other_path, root=ROOT),
    )
    with pytest.raises(
        VERIFIER.ArmVerificationError, match="arm_binding_mismatch"
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_refuses_a_matrix_whose_verdict_was_laundered(tmp_path: Path) -> None:
    """The failure mode this whole artifact exists to stop.

    Someone wants the arm to read as transferable, so they edit the verdict and
    recompute the matrix root so the hash check passes.  The verdict is recomputed
    from the rows at acceptance time, so it still fails.
    """

    paths = _fixture(tmp_path)
    matrix = json.loads(paths["matrix"].read_text(encoding="utf-8"))
    matrix["transfer_verdict"] = DIVERGENCE.VERDICT_CLEAR
    core = {k: v for k, v in matrix.items() if k != "matrix_root_sha256"}
    matrix["matrix_root_sha256"] = DIVERGENCE.stable_sha256(core)
    _write_json(paths["matrix"], matrix)
    with pytest.raises(
        VERIFIER.ArmVerificationError, match="verdict_mismatch"
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_refuses_a_matrix_with_the_wrong_schema(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    matrix = json.loads(paths["matrix"].read_text(encoding="utf-8"))
    matrix["schema"] = "gtos.something.else.v1"
    _write_json(paths["matrix"], matrix)
    with pytest.raises(
        VERIFIER.ArmVerificationError, match="divergence_matrix_schema_invalid"
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_the_cli_cannot_be_invoked_without_a_matrix(tmp_path: Path) -> None:
    """argparse is the outermost gate: no flag, no run."""

    paths = _fixture(tmp_path)
    parser = VERIFIER._parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--arm-receipt",
                str(paths["receipt"]),
                "--decision-contract",
                str(paths["decision"]),
                "--execution-seal",
                str(paths["execution"]),
                "--output",
                str(paths["output"]),
            ]
        )


def test_decision_self_hash_retains_declared_metadata() -> None:
    decision: dict[str, object] = {
        "schema": "gtos.b7_5.post_acceleration_decision_contract.v1",
        "status": (
            "SEALED_POST_ACCELERATION_REPLAY_FREE_DECISION_CONTRACT_VALID"
        ),
        "self_hash": {
            "algorithm": "sha256",
            "canonicalization": (
                "utf8_json_sort_keys_compact_separators_ensure_ascii"
            ),
            "excluded_path": "self_hash.sha256",
            "sha256": "",
        },
    }
    projection = json.loads(json.dumps(decision))
    projection["self_hash"].pop("sha256")
    decision["self_hash"]["sha256"] = _canonical_sha256(projection)

    assert VERIFIER._verify_decision_self_hash(decision) == (
        decision["self_hash"]["sha256"]
    )
    decision["self_hash"]["canonicalization"] = "substitute"
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="decision_contract_self_hash_invalid",
    ):
        VERIFIER._verify_decision_self_hash(decision)


def test_verifier_rejects_substitute_execution_schema(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    execution = json.loads(paths["execution"].read_text(encoding="utf-8"))
    execution.pop("execution_seal_root_sha256")
    execution["schema"] = "substitute.execution"
    execution = _sealed(execution, "execution_seal_root_sha256")
    _write_json(paths["execution"], execution)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt.pop("receipt_root_sha256")
    receipt["execution_seal_root_sha256"] = execution[
        "execution_seal_root_sha256"
    ]
    receipt = _sealed(receipt, "receipt_root_sha256")
    _write_json(paths["receipt"], receipt)
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="execution_seal_contract_invalid",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_rejects_missing_prepared_pack_bytes(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    shard = next((tmp_path / "packs").rglob("*.jsonl.zst"))
    shard.unlink()
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="prepared_pack_shard_tree_invalid",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_rejects_extra_prepared_pack_bytes(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    (tmp_path / "packs" / "unexpected.bin").write_bytes(b"unexpected")
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="prepared_pack_root_tree_invalid",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_requires_receipt_source_binding_root(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt.pop("receipt_root_sha256")
    receipt["source_authority_binding_root_sha256"] = "0" * 64
    receipt = _sealed(receipt, "receipt_root_sha256")
    _write_json(paths["receipt"], receipt)
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="arm_receipt_execution_seal_mismatch",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_rejects_substitute_pack_authority_schema(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    pack = json.loads(paths["pack"].read_text(encoding="utf-8"))
    pack.pop("authority_root_sha256")
    pack["schema"] = "substitute.pack"
    pack = _sealed(pack, "authority_root_sha256")
    _write_json(paths["pack"], pack)

    execution = json.loads(paths["execution"].read_text(encoding="utf-8"))
    execution.pop("execution_seal_root_sha256")
    execution["prepared_day_pack_binding"]["authority_file_sha256"] = (
        _file_sha256(paths["pack"])
    )
    execution["prepared_day_pack_binding"]["authority_root_sha256"] = pack[
        "authority_root_sha256"
    ]
    execution = _sealed(execution, "execution_seal_root_sha256")
    _write_json(paths["execution"], execution)

    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt.pop("receipt_root_sha256")
    receipt["execution_seal_root_sha256"] = execution[
        "execution_seal_root_sha256"
    ]
    receipt["prepared_pack_authority"]["file_sha256"] = _file_sha256(
        paths["pack"]
    )
    receipt["prepared_pack_authority"]["authority_root_sha256"] = pack[
        "authority_root_sha256"
    ]
    receipt = _sealed(receipt, "receipt_root_sha256")
    _write_json(paths["receipt"], receipt)
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="prepared_pack_authority_binding_invalid",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_fails_closed_on_receipt_or_artifact_drift(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt["arm_fingerprint_sha256"] = "d" * 64
    _write_json(paths["receipt"], receipt)
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="arm_receipt_root_invalid",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )

    paths = _fixture(tmp_path / "artifact-drift")
    decision_path = next(paths["namespace"].glob("*_DECISION_LEDGER.jsonl"))
    decision_path.write_text('{"identity":"changed"}\n', encoding="utf-8")
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="artifact_logical_identity_mismatch:decision",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_rejects_raw_and_cold_ambiguity(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    decision_path = next(paths["namespace"].glob("*_DECISION_LEDGER.jsonl"))
    cold_dir = decision_path.with_name(decision_path.name + ".cold")
    cold_dir.mkdir()
    with pytest.raises(
        VERIFIER.ArmVerificationError,
        match="artifact_verification_failed:decision:raw_and_cold_evidence_ambiguous",
    ):
        VERIFIER.verify_arm(
            arm_receipt_path=paths["receipt"],
            decision_contract_path=paths["decision"],
            execution_seal_path=paths["execution"],
            divergence_matrix_path=paths["matrix"],
        )


def test_verifier_recomputes_same_identity_after_cold_demotion(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)
    before = VERIFIER.verify_arm(
        arm_receipt_path=paths["receipt"],
        decision_contract_path=paths["decision"],
        execution_seal_path=paths["execution"],
        divergence_matrix_path=paths["matrix"],
    )
    decision_path = next(paths["namespace"].glob("*_DECISION_LEDGER.jsonl"))
    operation_path = tmp_path / "cold-operation.json"
    result = ARCHIVER.demote_jsonl_paths(
        paths=[decision_path],
        repo_root=tmp_path,
        allowed_root=paths["namespace"],
        operation_manifest_path=operation_path,
        apply=True,
        shard_max_bytes=4096,
        minimum_free_reserve_bytes=0,
    )
    assert result["status"] == ARCHIVER.OPERATION_PASS

    after = VERIFIER.verify_arm(
        arm_receipt_path=paths["receipt"],
        decision_contract_path=paths["decision"],
        execution_seal_path=paths["execution"],
        divergence_matrix_path=paths["matrix"],
    )
    assert (
        before["verified_artifact_identity_root_sha256"]
        == after["verified_artifact_identity_root_sha256"]
    )
    assert "artifacts" not in before
    assert "artifacts" not in after

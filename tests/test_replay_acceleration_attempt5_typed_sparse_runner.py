from __future__ import annotations

import argparse
import errno
import gzip
import hashlib
import inspect
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.research_infra import replay_acceleration_attempt5_typed_sparse_runner as runner


def test_bounded_row_transforms_are_lazy_and_exact() -> None:
    decision = {
        "symbol": "XAUUSD",
        "current_fvg_poi_generation": {"status": "complete", "count": 2},
        "candidate_generation_audit": {
            "producer_generation_audit": {
                "current_fvg_poi_generation": {
                    "status": "complete",
                    "count": 2,
                }
            }
        },
    }
    scorecard = {
        "candidate_id": "candidate-1",
        "scheduler_option_trace": [{"candidate_id": "candidate-1"}],
        "pre_risk_finalizer_scheduler_option_trace": [
            {"candidate_id": "candidate-1"}
        ],
        "post_risk_finalizer_scheduler_option_trace": [
            {"candidate_id": "candidate-1"}
        ],
    }
    candidate = {
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": "instance-1",
        "symbol": "XAUUSD",
    }
    missed = {
        **candidate,
        "missed_opportunity_accounting_scope": "non_executable_diagnostic",
    }
    consumed: list[str] = []

    def source() -> object:
        consumed.append("decision")
        yield decision

    lazy = runner.iter_compact_asof_decision_rows(source())
    assert consumed == []
    assert next(iter(lazy)) == runner.compact_asof_decision_rows([decision])[0]
    assert consumed == ["decision"]
    assert list(runner.iter_compact_scorecard_rows([scorecard])) == (
        runner.compact_scorecard_rows([scorecard])
    )
    assert list(runner.iter_compact_candidate_index_rows([candidate])) == (
        runner.compact_candidate_index_rows([candidate])
    )
    assert list(runner.iter_compact_missed_opportunity_rows([missed])) == (
        runner.compact_missed_opportunity_rows([missed])
    )


def test_streaming_annotation_and_projection_count_match_legacy_lists(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "symbol": "XAUUSD",
            "trading_day": "2026-01-02",
            "current_fvg_poi_generation": {"status": "complete", "count": 1},
        },
        {"symbol": "EURUSD", "trading_day": "2026-01-02"},
    ]
    compact = runner.compact_asof_decision_rows(rows)
    legacy = runner.annotate_rows(
        compact,
        profile="S0R0",
        split="development",
        chunk_id="S0R0:development:2026-01-02:2026-01-02",
        row_type="asof_decision",
    )
    counts: Counter[str] = Counter()
    streamed = runner.iter_annotated_rows(
        runner.iter_counted_compact_projection_rows(
            runner.iter_compact_asof_decision_rows(rows),
            role="decision",
            counts=counts,
        ),
        profile="S0R0",
        split="development",
        chunk_id="S0R0:development:2026-01-02:2026-01-02",
        row_type="asof_decision",
    )
    legacy_path = tmp_path / "legacy.jsonl"
    streamed_path = tmp_path / "streamed.jsonl"
    assert runner.append_jsonl(legacy_path, legacy) == 2
    assert runner.append_jsonl(streamed_path, streamed) == 2
    assert streamed_path.read_bytes() == legacy_path.read_bytes()
    assert counts == Counter(
        {
            "decision_input_rows": 2,
            "decision_rows": 2,
            "decision_projection_eligible_rows": 1,
            "decision_status::canonical_top_level_preserved_no_nested_alias": 1,
            "decision_status::projection_missing": 1,
        }
    )


def test_compact_projection_counter_rejects_unknown_role() -> None:
    with pytest.raises(ValueError, match="compact_projection_role_unknown:missed"):
        list(
            runner.iter_counted_compact_projection_rows(
                [],
                role="missed",
                counts=Counter(),
            )
        )


def test_attempt5_binds_golden_finalizer_conflict_order_without_source_cache_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = tuple(runner.timewarp_loop.FINALIZER_CANONICAL_AUTHORITY_KEYS)
    source_identity_before = runner.accepted_source_implementation_root()

    expected = runner.attempt5_finalizer_conflict_key_order(original)
    runner.bind_attempt5_finalizer_conflict_key_order()

    assert tuple(runner.timewarp_loop.FINALIZER_CANONICAL_AUTHORITY_KEYS) == expected
    assert expected.index("ultimate_package_matched_sleeve_count") < expected.index(
        "ultimate_package_admission_sleeve_match_count"
    )
    assert expected.index("ultimate_package_admission_sleeve_match_count") < (
        expected.index("source_boundary")
    )
    assert runner.accepted_source_implementation_root() == source_identity_before
    monkeypatch.setattr(
        runner.timewarp_loop,
        "FINALIZER_CANONICAL_AUTHORITY_KEYS",
        original,
    )


def test_attempt5_source_successor_identity_is_reviewed_literal() -> None:
    assert runner.ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256 == (
        "519d4d4f9054d5c19aae3575fa6018e09760e488d3b9274beeed36f48baf2bb4"
    )
    assert runner.ATTEMPT5_PREDECESSOR_SOURCE_BUNDLE_ROOT_SHA256 == (
        "7b1ae5d4b614f64ca8c2632e058d28535793fa847efcdba0331ef3c9c34d3d25"
    )
    assert runner.ATTEMPT5_SOURCE_REBIND_AUTHORITY_SHA256 == (
        "ff90833d6f1cf5a99cbc0f3277614e0904add3ce18a4f76df203410ba2286793"
    )
    assert runner.ATTEMPT5_SOURCE_REBIND_AUTHORITY_ROOT_SHA256 == (
        "2cdacbe6aa6ba5be58635faf35df9f4c90145d89f3595cf59f0e4b58a260f574"
    )
    assert runner.ATTEMPT5_SOURCE_SELECTION_SHA256 == (
        "0eb4828655cf2a1c8693c16b864271bd9c7561fb5ecd39387e386f1f8c36473a"
    )
    assert runner.ATTEMPT5_SOURCE_SELECTION_ROOT_SHA256 == (
        "1a3a57413a3b8b42d31542198954e1e72bb9ab28fbb0e8b9cf24773400dea80a"
    )
    assert runner.ATTEMPT5_SOURCE_BUNDLE_FILE_SHA256 == (
        "7d3465343311aa5d2783780bc4654e8888cb5c6587523df25d4ac93faa2965fd"
    )
    assert runner.ATTEMPT5_SOURCE_IMPLEMENTATION_ROOT_SHA256 == (
        "160cc0e4955f6bc4d038379119787e16cb5c61b0d63926acceb7edcd3ba73b7a"
    )


def test_source_rebind_authority_is_part_of_shared_proof_options() -> None:
    rebind = {
        "schema": runner.BOUND_SOURCE_REBIND_AUTHORITY_SCHEMA,
        "binding_root_sha256": "b" * 64,
    }
    args = SimpleNamespace(
        profiles=[runner.PROFILE_REPAIRED],
        chunk_size=1,
        max_candidates_per_symbol_window=0,
        smoke_subset=False,
        skip_tick_source=False,
        use_native_h1=False,
        omit_candidate_ledger=True,
        omit_candidate_index_ledger=True,
        omit_packet_sidecar_ledger=True,
        compact_missed_ledger=True,
        compact_decision_ledger=True,
        compact_scorecard_ledger=True,
        candidate_ledger_packet_max_bytes=1024,
        scorecard_ledger_packet_max_bytes=1024,
        compact_scorecard_symbol_risk_config=True,
        scorecard_probe_row_limit=1,
        gc_between_chunks=True,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        task2_semantic_checkpoint_after_day="2026-01-02",
        streaming_proof_archive_root=Path("proof"),
        max_streaming_proof_archive_bytes=1024,
        source_prewarm_workers=4,
        source_acceleration_authority={
            "schema": "gtos.replay_acceleration.real_source_authority.v1",
            "source_bundle_root_sha256": "c" * 64,
            "selection_root_sha256": "d" * 64,
            "source_plan_digest_sha256": "e" * 64,
            "config_projection_root_sha256": "f" * 64,
            "normalizer_code_root_sha256": "1" * 64,
            "partition_count": 96,
            "symbol_count": 24,
            "policy_execution_entered": False,
            "candidate_cache_enabled": False,
            "policy_state_cache_enabled": False,
            "source_bundle_consumer_rebind_authority": rebind,
        },
    )

    options = runner.broad_replay_execution_options_from_args(args)

    assert options["source_acceleration"][
        "source_bundle_consumer_rebind_authority"
    ] == rebind
    assert options["task2_semantic_checkpoint_after_day"] == "2026-01-02"


def _write_rooted_json(
    path: Path,
    payload: dict[str, object],
    root_field: str,
) -> dict[str, object]:
    rooted = dict(payload)
    rooted[root_field] = hashlib.sha256(
        (
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    path.write_text(
        json.dumps(
            rooted,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return rooted


def _write_stable_rooted_json(
    path: Path,
    payload: dict[str, object],
    root_field: str,
) -> dict[str, object]:
    rooted = dict(payload)
    rooted[root_field] = runner.stable_sha256(payload)
    path.write_text(
        json.dumps(
            rooted,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return rooted


def _prospective_golden_args(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    economic_digest = "d" * 64
    successor_authority_root = "e" * 64
    successor_verification_root = "f" * 64
    successor_authority_path = tmp_path / "successor-authority.json"
    successor_authority_path.write_text("{}\n", encoding="ascii")
    successor_authority_sha256 = runner.file_sha256(successor_authority_path)
    manifest_path = tmp_path / "golden-manifest.json"
    manifest = _write_rooted_json(
        manifest_path,
        {
            "schema": "gtos.replay_acceleration.partial_golden_manifest.v2",
            "golden_root_sha256": "b" * 64,
            "opaque_result_surface_root_sha256": "c" * 64,
            "contract_identity": {
                "economic_execution_contract_digest_sha256": economic_digest,
            },
            "successor_authority": {
                "file_sha256": successor_authority_sha256,
                "authority_root_sha256": successor_authority_root,
                "verification_root_sha256": successor_verification_root,
            },
        },
        "manifest_self_root_sha256",
    )
    amendment_path = tmp_path / "golden-amendment.json"
    amendment = _write_rooted_json(
        amendment_path,
        {
            "schema": "gtos.replay_acceleration.partial_golden_amendment.v2",
            "partial_golden": {
                "manifest_self_root_sha256": manifest[
                    "manifest_self_root_sha256"
                ],
                "golden_root_sha256": manifest["golden_root_sha256"],
                "successor_authority_root_sha256": successor_authority_root,
            },
        },
        "amendment_self_root_sha256",
    )
    from src.research_infra import replay_acceleration_real_gate as real_gate

    monkeypatch.setattr(
        real_gate,
        "verify_successor_authority",
        lambda path: {
            "authority_file_sha256": runner.file_sha256(Path(path)),
            "authority_root_sha256": successor_authority_root,
            "verification_root_sha256": successor_verification_root,
        },
    )
    verifier_path = Path(runner.__file__).with_name(
        "replay_acceleration_real_parity_verifier.py"
    )
    fixed_code_authority, _identities = (
        runner.build_fixed_verifier_code_authority(Path(runner.__file__).parent)
    )
    return {
        "golden_manifest": manifest_path,
        "expected_golden_manifest_sha256": runner.file_sha256(manifest_path),
        "expected_golden_manifest_self_root_sha256": manifest[
            "manifest_self_root_sha256"
        ],
        "expected_golden_root_sha256": manifest["golden_root_sha256"],
        "expected_opaque_result_surface_root_sha256": manifest[
            "opaque_result_surface_root_sha256"
        ],
        "golden_amendment": amendment_path,
        "expected_golden_amendment_sha256": runner.file_sha256(amendment_path),
        "expected_golden_amendment_self_root_sha256": amendment[
            "amendment_self_root_sha256"
        ],
        "expected_fixed_parity_verifier_sha256": runner.file_sha256(
            verifier_path
        ),
        "golden_successor_authority": successor_authority_path,
        "expected_golden_successor_authority_sha256": (
            successor_authority_sha256
        ),
        "expected_golden_successor_authority_root_sha256": (
            successor_authority_root
        ),
        "expected_golden_successor_authority_verification_root_sha256": (
            successor_verification_root
        ),
        "expected_economic_execution_contract_sha256": economic_digest,
        "expected_fixed_verifier_code_authority_root_sha256": (
            fixed_code_authority["authority_root_sha256"]
        ),
    }


def _source_rebind_args(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    bundle_dir: Path,
    selection_path: Path,
) -> dict[str, object]:
    source_plan_digest = (
        "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
    )
    implementation_root = runner.accepted_source_implementation_root()
    selection = _write_stable_rooted_json(
        selection_path,
        {
            "schema": "gtos.replay_acceleration.slice_selection.v1",
            "expected_source_plan_digest_sha256": source_plan_digest,
            "policy_execution_entered": False,
        },
        "selection_root_sha256",
    )
    bundle_path = bundle_dir / "bundle.json"
    bundle = _write_stable_rooted_json(
        bundle_path,
        {
            "schema": "gtos.replay_acceleration.persisted_source_bundle.v1",
            "expected_source_plan_digest_sha256": source_plan_digest,
            "selection_root_sha256": selection["selection_root_sha256"],
            "accepted_cache_implementation_root": implementation_root,
            "status": "SEALED_SOURCE_EQUIVALENCE_BUNDLE",
            "policy_execution_entered": False,
        },
        "bundle_root_sha256",
    )
    (bundle_dir / "SEALED").write_text(
        f"{bundle['bundle_root_sha256']}\n",
        encoding="ascii",
    )
    predecessor_root = "9" * 64
    authority_path = tmp_path / "source-rebind-authority.json"
    authority = _write_stable_rooted_json(
        authority_path,
        {
            "schema": runner.SOURCE_REBIND_AUTHORITY_SCHEMA,
            "status": "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR",
            "reason": "unit_test_byte_exact_consumer_successor",
            "broker_live_authority": False,
            "continuation_authorized": False,
            "economic_values_exposed": False,
            "policy_execution_entered": False,
            "bundle_transformation": {},
            "selection_transformation": {
                "source_plan_digest_sha256": source_plan_digest,
            },
            "fresh_cold_runs": [],
            "independent_verifiers": [],
            "predecessor_bundle": {
                "bundle_root_sha256": predecessor_root,
            },
            "predecessor_selection": {},
            "successor_bundle": {
                "path": str(bundle_path.resolve()),
                "sha256": runner.file_sha256(bundle_path),
                "bundle_root_sha256": bundle["bundle_root_sha256"],
                "implementation_root_sha256": implementation_root,
            },
            "successor_selection": {
                "path": str(selection_path.resolve()),
                "sha256": runner.file_sha256(selection_path),
                "selection_root_sha256": selection["selection_root_sha256"],
            },
        },
        "authority_root_sha256",
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256",
        bundle["bundle_root_sha256"],
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_PREDECESSOR_SOURCE_BUNDLE_ROOT_SHA256",
        predecessor_root,
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_REBIND_AUTHORITY_SHA256",
        runner.file_sha256(authority_path),
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_REBIND_AUTHORITY_ROOT_SHA256",
        authority["authority_root_sha256"],
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_SELECTION_SHA256",
        runner.file_sha256(selection_path),
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_SELECTION_ROOT_SHA256",
        selection["selection_root_sha256"],
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_BUNDLE_FILE_SHA256",
        runner.file_sha256(bundle_path),
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_IMPLEMENTATION_ROOT_SHA256",
        implementation_root,
    )
    return {
        "source_bundle_consumer_rebind_authority": authority_path,
        "expected_source_bundle_consumer_rebind_authority_sha256": (
            runner.file_sha256(authority_path)
        ),
        "expected_source_bundle_consumer_rebind_authority_root_sha256": (
            authority["authority_root_sha256"]
        ),
        "expected_source_bundle_root_sha256": bundle["bundle_root_sha256"],
        "expected_source_plan_digest_sha256": source_plan_digest,
    }


def _args(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    namespace_root = tmp_path / "attempt5"
    runtime_root = tmp_path / "runtime"
    bundle = tmp_path / "bundle"
    runtime_root.mkdir()
    bundle.mkdir()
    selection = tmp_path / "selection.json"
    decision = tmp_path / "decision.json"
    tick_manifest = tmp_path / "tick-manifest.json"
    tick_sparse_cache_root = tmp_path / "tick-sparse-cache"
    source_rebind = _source_rebind_args(
        tmp_path,
        monkeypatch,
        bundle_dir=bundle,
        selection_path=selection,
    )
    decision.write_text("{}\n", encoding="ascii")
    tick_manifest.write_text("{}\n", encoding="ascii")
    monkeypatch.setattr(runner, "ATTEMPT5_NAMESPACE_ROOT", namespace_root)
    monkeypatch.setattr(runner, "ATTEMPT5_RUNTIME_EVIDENCE_ROOT", runtime_root)
    monkeypatch.setattr(runner, "ATTEMPT5_TICK_SOURCE_MANIFEST", tick_manifest)
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_TICK_SPARSE_CACHE_ROOT",
        tick_sparse_cache_root,
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_TICK_SOURCE_MANIFEST_SHA256",
        runner.file_sha256(tick_manifest),
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_TICK_DIAGNOSTIC_MANIFEST_BINDINGS",
        (),
    )
    monkeypatch.setattr(runner.shutil, "which", lambda name: "/opt/homebrew/bin/zstd")
    output_dir = namespace_root / "run-identity"
    return SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        max_days=None,
        chunk_size=1,
        output_prefix=runner.ATTEMPT5_OUTPUT_PREFIX,
        output_dir=output_dir,
        profiles=[runner.PROFILE_REPAIRED],
        max_candidates_per_symbol_window=0,
        smoke_subset=False,
        symbols=None,
        skip_tick_source=False,
        use_native_h1=False,
        omit_candidate_ledger=True,
        omit_candidate_index_ledger=True,
        omit_packet_sidecar_ledger=True,
        compact_missed_ledger=True,
        compact_decision_ledger=True,
        compact_scorecard_ledger=True,
        gc_between_chunks=True,
        finalize_existing_prefix=False,
        expected_shared_execution_contract_sha256="a" * 64,
        runtime_evidence_root=runtime_root,
        tick_source_manifest=tick_manifest,
        expected_tick_source_manifest_sha256=runner.file_sha256(tick_manifest),
        tick_diagnostic_manifests=[],
        expected_tick_diagnostic_manifest_sha256s=[],
        source_acceleration_bundle_dir=bundle,
        source_acceleration_selection=selection,
        source_acceleration_cache_root=output_dir / "typed-cache",
        tick_sparse_cache_root=tick_sparse_cache_root,
        source_prewarm_workers=4,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        parity_gate_request=output_dir / "GATE_REQUEST.json",
        parity_report=output_dir / "PARITY_REPORT.json",
        parity_receipt=output_dir / "PARITY_RECEIPT.json",
        parity_wait_timeout_seconds=604800,
        stop_after_parity_gate=True,
        streaming_proof_archive_root=output_dir / "proof-archive",
        max_streaming_proof_archive_bytes=1024 * 1024 * 1024,
        decision_contract=decision,
        arm_id="S0R0",
        expected_arm_fingerprint_sha256=(
            "2ece240b5fc9434a7ec20919e95cdf549bcd46f1c0311f130458fd4804c6d447"
        ),
        **source_rebind,
        **_prospective_golden_args(tmp_path, monkeypatch),
    )


def test_semantic_source_manifest_binds_archive_and_direct_surfaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact_root = tmp_path / "exact-run"
    monkeypatch.setattr(runner, "ROUTE", exact_root)
    outputs = {
        **runner.output_paths("UNIT"),
        **runner.semantic_output_paths("UNIT"),
    }
    observed: dict[str, object] = {}

    def fake_seal(**kwargs: object) -> dict[str, object]:
        observed.update(kwargs)
        return {
            "schema": "gtos.replay_acceleration.semantic_source_manifest.v1",
            "acceptance_authorized": False,
        }

    monkeypatch.setattr(runner, "seal_semantic_source_manifest", fake_seal)
    archive_manifest = exact_root / "proof-archive" / "CAMPAIGN_MANIFEST.json"
    archive_receipt = exact_root / "proof-archive" / "VERIFY_RECEIPT.json"

    manifest = runner.write_attempt5_semantic_source_manifest(
        outputs=outputs,
        campaign_days_by_profile={"S0R0": ("2026-01-02",)},
        archive_manifest_path=archive_manifest,
        archive_verification_receipt_path=archive_receipt,
        arm_id="S0R0",
    )

    assert manifest["acceptance_authorized"] is False
    assert observed["source_manifest_path"] == outputs[
        "semantic_source_manifest"
    ]
    assert observed["archive_manifest_path"] == archive_manifest
    assert observed["archive_verification_receipt_path"] == archive_receipt
    assert observed["campaign_id"] == "unit_S0R0"
    assert observed["profile"] == "S0R0"
    assert observed["arm_id"] == "S0R0"
    assert observed["campaign_days"] == ("2026-01-02",)
    evidence_paths = observed["evidence_paths"]
    assert isinstance(evidence_paths, dict)
    assert set(evidence_paths) == {
        "candidate",
        "order",
        "trade",
        "oracle",
        "state_checkpoint",
        "order_preimage",
    }
    assert "candidate_index" not in evidence_paths
    assert "packet_sidecar" not in evidence_paths


def test_semantic_outputs_are_isolated_from_exact_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact_root = tmp_path / "exact-run"
    monkeypatch.setattr(runner, "ROUTE", exact_root)

    exact_outputs = runner.output_paths("UNIT")
    semantic_outputs = runner.semantic_output_paths("UNIT")

    assert not set(exact_outputs).intersection(semantic_outputs)
    assert all(path.parent == exact_root for path in exact_outputs.values())
    assert all(
        path.parent == runner.semantic_diagnostic_root(exact_root)
        for path in semantic_outputs.values()
    )
    assert runner.semantic_diagnostic_root(exact_root) != exact_root


def test_shared_contract_binds_semantic_diagnostic_implementation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "build_config",
        lambda _profile, *, factorial_arm_binding=None: {},
    )

    contract = runner.broad_replay_shared_execution_contract(
        profiles=("repaired_package_conversion_v3",),
        active_symbols=("XAUUSD",),
        execution_options={},
        runtime_input_contract={"valid": True},
    )
    code_authority = {
        row["path"]: row["sha256"] for row in contract["code_authority"]
    }

    assert code_authority[
        "src/research_infra/replay_semantic_diagnostic.py"
    ] == "ab409f509ffd4c482970ac2fac2f6d7108b77fbcdc21af0916cd8579ea5d0079"


def test_semantic_order_binding_does_not_mutate_exact_order() -> None:
    sidecar_id = "a" * 64
    producer_order = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "order-1",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "execution_packet_sidecar_id": sidecar_id,
    }
    preimage = {
        "producer_order_stream_index": 0,
        "producer_order_row_sha256": runner.stable_sha256(producer_order),
        "execution_packet_sidecar_id": sidecar_id,
        "owner": {
            "campaign": "campaign-1",
            "profile": "S0R0",
            "decision_window_id": "window-1",
            "canonical_replay_candidate_instance_key": "candidate-instance-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "order-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
            "payload_root_sha256": "b" * 64,
        },
    }
    prebindings = runner.prebind_semantic_order_preimages_to_final_producer_rows(
        preimage_rows=[preimage],
        producer_order_rows=[producer_order],
    )
    runner.normalize_replay_result_ledgers(
        {"ledgers": {"order": [producer_order]}}
    )
    persisted_order = {
        **producer_order,
        "profile": "S0R0",
    }
    exact_before = dict(persisted_order)

    bound = runner.bind_semantic_order_preimages_to_persisted_rows(
        preimage_rows=[preimage],
        prebindings=prebindings,
        producer_order_rows=[producer_order],
        persisted_order_rows=[persisted_order],
        persisted_order_stream_offset=11,
    )

    assert persisted_order == exact_before
    assert bound[0]["persisted_order_stream_index"] == 11
    assert bound[0]["persisted_order_row_sha256"] == runner.stable_sha256(
        persisted_order
    )


def test_semantic_order_binding_resolves_final_event_sort_by_exact_preimage() -> None:
    sidecar_id = "a" * 64
    primary = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "order-1",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "execution_packet_sidecar_id": sidecar_id,
    }
    later_capture_but_earlier_event = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-2",
        "simulated_order_id": "order-2",
        "decision_window_id": "window-2",
        "canonical_replay_candidate_instance_key": "candidate-instance-2",
        "decision_time_utc": "2026-01-02T07:00:00+00:00",
        "execution_packet_sidecar_id": "c" * 64,
    }
    producer_rows_after_event_sort = [later_capture_but_earlier_event, primary]
    preimage = {
        # The primary was index zero when captured, before sort_event_ledgers.
        "producer_order_stream_index": 0,
        "producer_order_row_sha256": runner.stable_sha256(primary),
        "execution_packet_sidecar_id": sidecar_id,
        "owner": {
            "campaign": "campaign-1",
            "profile": "S0R0",
            "decision_window_id": "window-1",
            "canonical_replay_candidate_instance_key": "candidate-instance-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "order-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
            "payload_root_sha256": "b" * 64,
        },
    }
    prebindings = runner.prebind_semantic_order_preimages_to_final_producer_rows(
        preimage_rows=[preimage],
        producer_order_rows=producer_rows_after_event_sort,
    )
    runner.normalize_replay_result_ledgers(
        {"ledgers": {"order": producer_rows_after_event_sort}}
    )
    persisted_rows = [
        {**row, "profile": "S0R0"}
        for row in producer_rows_after_event_sort
    ]

    bound = runner.bind_semantic_order_preimages_to_persisted_rows(
        preimage_rows=[preimage],
        prebindings=prebindings,
        producer_order_rows=producer_rows_after_event_sort,
        persisted_order_rows=persisted_rows,
        persisted_order_stream_offset=11,
    )

    assert bound[0]["producer_order_stream_index"] == 0
    assert bound[0]["final_producer_order_stream_index"] == 1
    assert bound[0]["producer_order_stream_index_rebound_after_final_sort"] is True
    assert bound[0]["persisted_order_stream_index"] == 12
    assert bound[0]["persisted_order_row_sha256"] == runner.stable_sha256(
        persisted_rows[1]
    )


def test_semantic_order_prebinding_survives_post_capture_normalization() -> None:
    sidecar_id = "a" * 64
    producer_order = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "order-1",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "execution_packet_sidecar_id": sidecar_id,
        "selected_cell_risk_pct": 0.10,
        "scheduler_approved_risk_pct": 0.10,
    }
    capture_sha256 = runner.stable_sha256(producer_order)
    preimage = {
        "semantic_order_preimage_id": "b" * 64,
        "producer_order_stream_index": 0,
        "producer_order_row_sha256": capture_sha256,
        "execution_packet_sidecar_id": sidecar_id,
        "owner": {
            "campaign": "campaign-1",
            "profile": "S0R0",
            "decision_window_id": "window-1",
            "canonical_replay_candidate_instance_key": "candidate-instance-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "order-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
        },
    }

    prebindings = (
        runner.prebind_semantic_order_preimages_to_final_producer_rows(
            preimage_rows=[preimage],
            producer_order_rows=[producer_order],
        )
    )
    result = {"ledgers": {"order": [producer_order]}}
    runner.normalize_replay_result_ledgers(result)

    assert producer_order["sizing_haircut_applied"] is False
    assert producer_order["sizing_haircut_factor"] == 1.0
    assert producer_order["sizing_haircut_reason"] == (
        "approved_risk_pct_matches_or_exceeds_selected_cell_risk_pct"
    )
    assert runner.stable_sha256(producer_order) != capture_sha256
    persisted_orders = runner.annotate_rows(
        [producer_order],
        profile="S0R0",
        split="development",
        chunk_id="S0R0:development:2026-01-02:2026-01-02",
        row_type="simulated_order",
    )
    persisted_before = [dict(row) for row in persisted_orders]

    bound = runner.bind_semantic_order_preimages_to_persisted_rows(
        preimage_rows=[preimage],
        prebindings=prebindings,
        producer_order_rows=[producer_order],
        persisted_order_rows=persisted_orders,
        persisted_order_stream_offset=0,
    )

    assert persisted_orders == persisted_before
    assert bound[0]["producer_order_row_sha256"] == capture_sha256
    assert bound[0]["final_producer_order_stream_index"] == 0
    assert bound[0]["producer_order_row_mutated_after_capture"] is True
    assert bound[0]["producer_order_row_sha256_matches_final_order"] is False
    assert bound[0]["final_producer_order_row_sha256"] == runner.stable_sha256(
        producer_order
    )


def test_semantic_order_binding_rejects_tampered_prebinding() -> None:
    order = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "order-1",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "execution_packet_sidecar_id": "a" * 64,
    }
    preimage = {
        "semantic_order_preimage_id": "b" * 64,
        "producer_order_stream_index": 0,
        "producer_order_row_sha256": runner.stable_sha256(order),
        "execution_packet_sidecar_id": "a" * 64,
        "owner": {
            "campaign": "campaign-1",
            "profile": "S0R0",
            "decision_window_id": "window-1",
            "canonical_replay_candidate_instance_key": "candidate-instance-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "order-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
        },
    }
    prebindings = runner.prebind_semantic_order_preimages_to_final_producer_rows(
        preimage_rows=[preimage],
        producer_order_rows=[order],
    )
    prebindings[0]["semantic_order_preimage_row_sha256"] = "c" * 64

    with pytest.raises(ValueError, match="semantic_order_prebinding_mismatch:0"):
        runner.bind_semantic_order_preimages_to_persisted_rows(
            preimage_rows=[preimage],
            prebindings=prebindings,
            producer_order_rows=[order],
            persisted_order_rows=[{**order, "profile": "S0R0"}],
            persisted_order_stream_offset=0,
        )


def test_semantic_order_binding_rejects_unexpected_economic_mutation() -> None:
    order = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "order-1",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "execution_packet_sidecar_id": "a" * 64,
        "selected_cell_risk_pct": 0.10,
        "scheduler_approved_risk_pct": 0.10,
        "risk_pct": 0.10,
    }
    preimage = {
        "semantic_order_preimage_id": "b" * 64,
        "producer_order_stream_index": 0,
        "producer_order_row_sha256": runner.stable_sha256(order),
        "execution_packet_sidecar_id": "a" * 64,
        "owner": {
            "campaign": "campaign-1",
            "profile": "S0R0",
            "decision_window_id": "window-1",
            "canonical_replay_candidate_instance_key": "candidate-instance-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "order-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
        },
    }
    prebindings = runner.prebind_semantic_order_preimages_to_final_producer_rows(
        preimage_rows=[preimage],
        producer_order_rows=[order],
    )
    result = {"ledgers": {"order": [order]}}
    runner.normalize_replay_result_ledgers(result)
    order["risk_pct"] = 0.20

    with pytest.raises(
        ValueError,
        match="semantic_order_binding_unexpected_post_normalization_mutation:0",
    ):
        runner.bind_semantic_order_preimages_to_persisted_rows(
            preimage_rows=[preimage],
            prebindings=prebindings,
            producer_order_rows=[order],
            persisted_order_rows=[{**order, "profile": "S0R0"}],
            persisted_order_stream_offset=0,
        )


def test_semantic_order_binding_rejects_ambiguous_exact_preimage() -> None:
    order = {
        "campaign": "campaign-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "order-1",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "execution_packet_sidecar_id": "a" * 64,
    }
    persisted = {**order, "profile": "S0R0"}
    preimage = {
        "producer_order_stream_index": 0,
        "producer_order_row_sha256": runner.stable_sha256(order),
        "execution_packet_sidecar_id": "a" * 64,
        "owner": {
            "campaign": "campaign-1",
            "profile": "S0R0",
            "decision_window_id": "window-1",
            "canonical_replay_candidate_instance_key": "candidate-instance-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "order-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
        },
    }

    with pytest.raises(
        ValueError,
        match="semantic_order_prebinding_ambiguous_exact_preimage:0",
    ):
        runner.prebind_semantic_order_preimages_to_final_producer_rows(
            preimage_rows=[preimage],
            producer_order_rows=[order, dict(order)],
        )


def test_real_route_prebinds_semantic_orders_before_accumulator_normalization() -> None:
    source = inspect.getsource(runner._run_typed_sparse_attempt5)
    prebind = source.index(
        "prebind_semantic_order_preimages_to_final_producer_rows("
    )
    accumulator_normalization = source.index("accumulator.add_result(", prebind)
    final_bind = source.index(
        "bind_semantic_order_preimages_to_persisted_rows(",
        accumulator_normalization,
    )

    assert prebind < accumulator_normalization < final_bind


def test_bounded_parity_route_verifies_archive_and_writes_source_before_gate() -> None:
    source = inspect.getsource(runner._run_typed_sparse_attempt5)
    parity_archive_verify = source.index(
        "streaming_archive.independent_verify_campaign("
    )
    source_manifest = source.index(
        "write_attempt5_semantic_source_manifest(",
        parity_archive_verify,
    )
    gate_request = source.index(
        "gate_request = build_gate_request",
        source_manifest,
    )
    bounded_return = source.index(
        'if bool(getattr(args, "stop_after_parity_gate", False)):',
        gate_request,
    )

    assert parity_archive_verify < source_manifest < gate_request < bounded_return


@pytest.mark.parametrize(
    "campaign_days_by_profile",
    [
        {},
        {"S0R0": ()},
        {"S0R0": ("2026-01-02", "2026-01-02")},
        {"S0R0": ("2026-01-03", "2026-01-02")},
        {"S0R0": ("2026-1-2",)},
        {"S0R0": (True,)},
    ],
)
def test_semantic_source_manifest_rejects_invalid_campaign_calendar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    campaign_days_by_profile: dict[str, tuple[object, ...]],
) -> None:
    monkeypatch.setattr(runner, "ROUTE", tmp_path)
    outputs = {
        **runner.output_paths("UNIT"),
        **runner.semantic_output_paths("UNIT"),
    }

    with pytest.raises(ValueError, match="semantic_"):
        runner.write_attempt5_semantic_source_manifest(
            outputs=outputs,
            campaign_days_by_profile=campaign_days_by_profile,
            archive_manifest_path=tmp_path / "CAMPAIGN_MANIFEST.json",
            archive_verification_receipt_path=tmp_path / "VERIFY_RECEIPT.json",
            arm_id="S0R0",
        )


def test_attempt5_authority_accepts_only_fresh_bound_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path, monkeypatch)
    runner.require_attempt5_execution_authority(args)

    authority = runner.prospective_golden_authority_from_args(args)
    assert args.prospective_golden_authority == authority
    assert args.bound_source_bundle_consumer_rebind_authority[
        "authority_file_sha256"
    ] == args.expected_source_bundle_consumer_rebind_authority_sha256
    assert args.bound_source_bundle_consumer_rebind_authority[
        "authority_root_sha256"
    ] == args.expected_source_bundle_consumer_rebind_authority_root_sha256
    assert args.bound_source_bundle_consumer_rebind_authority[
        "verified_successor_bundle"
    ]["bundle_root_sha256"] == args.expected_source_bundle_root_sha256
    assert authority == {
        "golden_manifest_path": str(args.golden_manifest.resolve()),
        "golden_manifest_file_sha256": args.expected_golden_manifest_sha256,
        "golden_manifest_self_root_sha256": (
            args.expected_golden_manifest_self_root_sha256
        ),
        "golden_root_sha256": args.expected_golden_root_sha256,
        "opaque_result_surface_root_sha256": (
            args.expected_opaque_result_surface_root_sha256
        ),
        "golden_amendment_path": str(args.golden_amendment.resolve()),
        "golden_amendment_file_sha256": args.expected_golden_amendment_sha256,
        "golden_amendment_self_root_sha256": (
            args.expected_golden_amendment_self_root_sha256
        ),
        "fixed_verifier_module": (
            "src.research_infra.replay_acceleration_real_parity_verifier"
        ),
        "fixed_verifier_path": str(
            Path(runner.__file__)
            .with_name("replay_acceleration_real_parity_verifier.py")
            .resolve()
        ),
        "fixed_verifier_file_sha256": (
            args.expected_fixed_parity_verifier_sha256
        ),
        "successor_authority_path": str(
            args.golden_successor_authority.resolve()
        ),
        "successor_authority_file_sha256": (
            args.expected_golden_successor_authority_sha256
        ),
        "successor_authority_root_sha256": (
            args.expected_golden_successor_authority_root_sha256
        ),
        "successor_authority_verification_root_sha256": (
            args.expected_golden_successor_authority_verification_root_sha256
        ),
        "economic_execution_contract_digest_sha256": (
            args.expected_economic_execution_contract_sha256
        ),
        "fixed_verifier_code_authority": (
            runner.build_fixed_verifier_code_authority(
                Path(runner.__file__).parent
            )[0]
        ),
        "fixed_verifier_code_authority_root_sha256": (
            args.expected_fixed_verifier_code_authority_root_sha256
        ),
    }


def test_attempt5_authority_rejects_predecessor_source_bundle_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _args(tmp_path, monkeypatch)
    args.expected_source_bundle_root_sha256 = (
        runner.ATTEMPT5_PREDECESSOR_SOURCE_BUNDLE_ROOT_SHA256
    )

    with pytest.raises(
        ValueError,
        match="attempt5_expected_source_bundle_root_sha256_mismatch",
    ):
        runner.require_attempt5_execution_authority(args)


def test_attempt5_authority_rejects_mismatched_source_rebind_successor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _args(tmp_path, monkeypatch)
    authority_path = args.source_bundle_consumer_rebind_authority
    authority = json.loads(authority_path.read_text(encoding="ascii"))
    authority.pop("authority_root_sha256")
    authority["successor_selection"]["sha256"] = "0" * 64
    authority = _write_stable_rooted_json(
        authority_path,
        authority,
        "authority_root_sha256",
    )
    authority_sha256 = runner.file_sha256(authority_path)
    args.expected_source_bundle_consumer_rebind_authority_sha256 = (
        authority_sha256
    )
    args.expected_source_bundle_consumer_rebind_authority_root_sha256 = (
        authority["authority_root_sha256"]
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_REBIND_AUTHORITY_SHA256",
        authority_sha256,
    )
    monkeypatch.setattr(
        runner,
        "ATTEMPT5_SOURCE_REBIND_AUTHORITY_ROOT_SHA256",
        authority["authority_root_sha256"],
    )

    with pytest.raises(
        ValueError,
        match="attempt5_source_rebind_authority_successor_mismatch",
    ):
        runner.require_attempt5_execution_authority(args)


@pytest.mark.parametrize(
    "source_input",
    ("authority_leaf", "selection_leaf", "bundle_parent"),
)
def test_attempt5_authority_rejects_source_rebind_symlink_components(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_input: str,
) -> None:
    args = _args(tmp_path, monkeypatch)
    if source_input == "authority_leaf":
        path = args.source_bundle_consumer_rebind_authority
        target = tmp_path / "real-source-rebind-authority.json"
        path.rename(target)
        path.symlink_to(target)
    elif source_input == "selection_leaf":
        path = args.source_acceleration_selection
        target = tmp_path / "real-selection.json"
        path.rename(target)
        path.symlink_to(target)
    else:
        path = args.source_acceleration_bundle_dir
        target = tmp_path / "real-bundle"
        path.rename(target)
        path.symlink_to(target, target_is_directory=True)

    with pytest.raises(
        ValueError,
        match="attempt5_source_rebind_authority_symlink_forbidden",
    ):
        runner.require_attempt5_execution_authority(args)


@pytest.mark.parametrize(
    "field",
    (
        "expected_golden_manifest_sha256",
        "expected_golden_manifest_self_root_sha256",
        "expected_golden_root_sha256",
        "expected_opaque_result_surface_root_sha256",
        "expected_golden_amendment_sha256",
        "expected_golden_amendment_self_root_sha256",
        "expected_fixed_parity_verifier_sha256",
    ),
)
def test_attempt5_authority_rejects_prospective_golden_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    args = _args(tmp_path, monkeypatch)
    setattr(args, field, "0" * 64)

    with pytest.raises(
        ValueError,
        match="attempt5_prospective_golden_authority",
    ):
        runner.require_attempt5_execution_authority(args)

    assert not args.output_dir.exists()


@pytest.mark.parametrize(
    "collision",
    ("reserved_partial_summary", "report_receipt_alias"),
)
def test_attempt5_authority_rejects_parity_evidence_path_collisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    collision: str,
) -> None:
    args = _args(tmp_path, monkeypatch)
    if collision == "reserved_partial_summary":
        args.parity_gate_request = (
            args.output_dir
            / f"{args.output_prefix}_PARTIAL_SUMMARY.json"
        )
    else:
        args.parity_report = args.parity_receipt

    with pytest.raises(
        ValueError,
        match="attempt5_evidence_path_collision",
    ):
        runner.require_attempt5_execution_authority(args)

    assert not args.output_dir.exists()


def test_runtime_evidence_root_rebinds_integration_and_data_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale_root = Path("/Users/borr/Documents/gtos/repo/ai-trading-agent")
    monkeypatch.setattr(runner, "MAIN_REPO_ROOT", stale_root)
    monkeypatch.setattr(
        runner,
        "DATA_ROOTS",
        (runner.ROOT / "data/mt5_research_exports", stale_root / "data/mt5_research_exports"),
    )

    contract = runner.configure_runtime_evidence_root(
        runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )

    assert runner.MAIN_REPO_ROOT == runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    assert runner.DATA_ROOTS == (
        runner.ROOT / "data/mt5_research_exports",
        runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT / "data/mt5_research_exports",
    )
    assert contract["integration_repo_root"] == str(
        runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    assert all("/Users/borr/Documents/gtos" not in path for path in contract["data_roots"])

    expected_source_identity = (
        runner.CODE_ROUTE.relative_to(runner.ROOT)
        / "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json"
    ).as_posix()
    config = runner.build_config(runner.PROFILE_REPAIRED)
    runtime = config["gtos_vnext_runtime"]
    assert (
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
            "selected_policy_expected_net_source_path"
        ]
        == expected_source_identity
    )
    assert (
        runner.selected_package_bridge.RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_PATH
        == runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
        / expected_source_identity
    )

    candidate = {
        "candidate_id": "attempt5-source-path-identity",
        "decision_time_utc": "2026-01-02T07:15:00+00:00",
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_source_bound_candidate_use_allowed": True,
    }

    def calibration_hash(source_path: str) -> str:
        fields = runner.timewarp_loop.owner_approved_reconstructed_proxy_selected_policy_expected_net_fields(
            candidate=candidate,
            expected_net_r=1.18,
            selected_policy="momentum_exhaustion",
            enabled=True,
            source_boundary_note=runtime[
                "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
                "selected_policy_expected_net_boundary"
            ],
            source_path=source_path,
            source_semantic_sha256=runtime[
                "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
                "selected_policy_expected_net_source_semantic_sha256"
            ],
            source_artifact_sha256=runtime[
                "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
                "selected_policy_expected_net_source_artifact_sha256"
            ],
            source_digest_semantics=runtime[
                "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
                "selected_policy_expected_net_source_digest_semantics"
            ],
        )
        return str(fields["selected_policy_expected_net_calibration_hash"])

    assert calibration_hash(
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
            "selected_policy_expected_net_source_path"
        ]
    ) == calibration_hash(expected_source_identity)
    assert calibration_hash(
        str(
            runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
            / expected_source_identity
        )
    ) != calibration_hash(expected_source_identity)


def test_tick_discovery_uses_only_worktree_and_bound_runtime_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_roots: list[Path] = []

    def fake_resolve_tick_source(
        _symbol: str, *, repo_root: Path
    ) -> tuple[None, tuple[str, ...]]:
        captured_roots.append(Path(repo_root))
        return None, ()

    monkeypatch.setattr(runner, "MAIN_REPO_ROOT", runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    monkeypatch.setattr(runner, "resolve_ftmo_tick_source", fake_resolve_tick_source)

    resolver = runner.BroadSourceResolver()
    assert (
        resolver.resolve_tick(
            "XAUUSD",
            source_authority_days=("2026-01-01",),
        )
        is None
    )
    assert captured_roots == [runner.ROOT, runner.ATTEMPT5_RUNTIME_EVIDENCE_ROOT]


def test_bound_tick_source_authority_resolves_manifest_repo_relative_payload(
    tmp_path: Path,
) -> None:
    archive_repo = tmp_path / "archive-repo"
    export_dir = (
        archive_repo
        / "data/mt5_research_exports/bridge_ftmo_ticks_micro_archive"
    )
    tick_path = export_dir / "ticks/XAUUSD/microstructure_ticks.jsonl"
    tick_path.parent.mkdir(parents=True)
    tick_path.write_text(
        '{"time_utc":"2026-01-01T00:00:01+00:00","bid":100.0,'
        '"ask":100.1,"volume":1}\n',
        encoding="utf-8",
    )
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "source_provenance": {
                    "source_broker": "FTMO",
                    "source_role": "owner_authorized_research_hydration",
                    "source_truth_scope": runner.SOURCE_TRUTH_SCOPE,
                    "not_redacted_account_native": True,
                },
                "files": {
                    "XAUUSD_TICK": {
                        "file_symbol": "XAUUSD",
                        "mt5_symbol": "XAUUSD",
                        "timeframe": "TICK",
                        "path": (
                            "data/mt5_research_exports/"
                            "bridge_ftmo_ticks_micro_archive/"
                            "ticks/XAUUSD/microstructure_ticks.jsonl"
                        ),
                        "row_count": 1,
                        "sha256": runner.file_sha256(tick_path),
                        "source_server_hash": "b" * 64,
                        "source_account_hash": "c" * 64,
                        "first": "2026-01-01T00:00:01+00:00",
                        "last": "2026-01-01T00:00:01+00:00",
                    }
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    specs, contract = runner.bound_tick_source_authority(
        manifest_path=manifest_path,
        expected_manifest_sha256=runner.file_sha256(manifest_path),
    )

    assert tuple(specs) == ("XAUUSD",)
    assert specs["XAUUSD"][0].path == tick_path
    assert contract["logical_repo_root"] == str(archive_repo)
    assert contract["broad_retired_repo_scan_enabled"] is False


def test_bound_tick_authorities_reuse_authenticated_replay_cache_without_manifest_read(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive_repo = tmp_path / "archive-repo"
    export_dir = archive_repo / "data/mt5_research_exports/ticks"
    tick_path = export_dir / "ticks/XAUUSD/microstructure_ticks.jsonl"
    tick_path.parent.mkdir(parents=True)
    tick_path.write_text('{"time_utc":"2026-01-01T00:00:01+00:00"}\n')
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text("dataless-placeholder\n")
    manifest_sha256 = "a" * 64
    source_row = {
        "row_type": "tick_symbol_source",
        "selected_status": "selected_priority_tick_source",
        "symbol": "XAUUSD",
        "mapped_symbol": "XAUUSD",
        "timeframe": "TICK",
        "path": str(tick_path),
        "source_path": str(tick_path),
        "source_family": "ftmo_mt5_research_export",
        "source_broker": "FTMO",
        "source_role": "owner_authorized_research_hydration",
        "start_utc": "2025-10-01T00:00:00+00:00",
        "end_utc": "2026-04-30T00:00:00+00:00",
        "row_count": 1,
        "rows": 1,
        "sha256": "b" * 64,
        "source_sha256": "b" * 64,
        "export_tool": "scripts/export_mt5_research_ticks.py",
        "manifest_path": str(manifest_path),
        "source_server_redacted": "redacted:server",
        "source_server_hash": "c" * 64,
        "source_account_redacted": "redacted:account",
        "source_account_hash": "d" * 64,
        "diagnostic_fallback_only": False,
        "source_truth_scope": runner.SOURCE_TRUTH_SCOPE,
        "not_redacted_account_native": True,
        "replaces_missing_frozen_path_source": False,
        "broker_lifecycle_truth_satisfied": False,
        "ordered_tick_truth_satisfied": True,
    }
    source_ledger = tmp_path / "source.jsonl"
    source_ledger.write_text(
        json.dumps(source_row, sort_keys=True) + "\n", encoding="utf-8"
    )
    source_core = {
        "schema": "gtos.replay_acceleration.bound_tick_source_authority.v1",
        "status": "exact_manifest_bound_tick_source_authority",
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha256,
        "logical_repo_root": str(archive_repo),
        "source_count": 1,
        "symbols": ["XAUUSD"],
        "sources": [
            {
                "symbol": "XAUUSD",
                "source_path": str(tick_path),
                "source_bytes": tick_path.stat().st_size,
                "declared_row_count": 1,
                "declared_sha256": "b" * 64,
                "start_utc": source_row["start_utc"],
                "end_utc": source_row["end_utc"],
            }
        ],
        "broad_retired_repo_scan_enabled": False,
        "payload_hash_verification_stage": "canonical_source_authority_preflight",
    }
    source_contract = {
        **source_core,
        "contract_root_sha256": runner.stable_sha256(source_core),
    }
    diagnostic_core = {
        "schema": "gtos.replay_acceleration.bound_tick_diagnostic_authority.v1",
        "status": "exact_named_manifest_diagnostics_bound",
        "manifest_count": 0,
        "manifests": [],
        "symbols_with_gaps": [],
        "gap_count": 0,
        "gaps_by_symbol": {},
        "january_overlap_allowed": False,
        "broad_retired_repo_scan_enabled": False,
    }
    diagnostic_contract = {
        **diagnostic_core,
        "contract_root_sha256": runner.stable_sha256(diagnostic_core),
    }
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "status": "partial_in_progress_not_final_proof",
                "broker_mutation_enabled": False,
                "bound_tick_source_authority": source_contract,
                "bound_tick_diagnostic_authority": diagnostic_contract,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    real_file_sha256 = runner.file_sha256

    def guarded_file_sha256(path: Path) -> str:
        if Path(path).resolve() == manifest_path.resolve():
            raise AssertionError("raw manifest must not be read on cache reuse")
        return real_file_sha256(Path(path))

    monkeypatch.setattr(runner, "file_sha256", guarded_file_sha256)

    specs, actual_source, gaps, actual_diagnostic = (
        runner.bound_tick_authorities_from_replay_cache(
            authority_summary_path=summary_path,
            expected_authority_summary_sha256=real_file_sha256(summary_path),
            source_ledger_path=source_ledger,
            expected_source_ledger_sha256=real_file_sha256(source_ledger),
            manifest_path=manifest_path,
            expected_manifest_sha256=manifest_sha256,
            expected_source_contract_root_sha256=source_contract[
                "contract_root_sha256"
            ],
            diagnostic_manifest_bindings=(),
            expected_diagnostic_contract_root_sha256=diagnostic_contract[
                "contract_root_sha256"
            ],
        )
    )

    assert specs["XAUUSD"][0].path == tick_path
    assert actual_source == source_contract
    assert gaps == {}
    assert actual_diagnostic == diagnostic_contract


def test_bound_tick_resolver_scans_only_active_root_and_preserves_logical_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "archive/data/ticks/XAUUSD.jsonl"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("{}\n", encoding="utf-8")
    logical_root = tmp_path / "archive"
    active_root = tmp_path / "active"
    active_root.mkdir()
    spec = runner.SourceSpec(
        symbol="XAUUSD",
        mapped_symbol="XAUUSD",
        timeframe="TICK",
        path=source_path,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2025-10-01T00:00:00+00:00",
        end_utc="2026-04-30T00:00:00+00:00",
        row_count=1,
        sha256="a" * 64,
        manifest_path=str(tmp_path / "archive/manifest.json"),
        source_server_hash="b" * 64,
        source_account_hash="c" * 64,
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )
    captured_roots: list[Path] = []

    def fake_resolve_tick_source(
        _symbol: str, *, repo_root: Path
    ) -> tuple[None, tuple[str, ...]]:
        captured_roots.append(Path(repo_root))
        return None, ()

    monkeypatch.setattr(runner, "MAIN_REPO_ROOT", active_root)
    monkeypatch.setattr(runner, "resolve_ftmo_tick_source", fake_resolve_tick_source)
    resolver = runner.BroadSourceResolver(
        bound_tick_source_specs={"XAUUSD": (spec,)},
        bound_tick_logical_repo_root=logical_root,
    )

    source = resolver.resolve_tick(
        "XAUUSD",
        source_authority_days=("2026-01-01",),
    )

    assert source is not None
    assert tuple(source.rows_by_day.specs) == (spec,)
    assert captured_roots == [active_root]


def _sealed_tick_source_row(
    *,
    source_path: Path,
    manifest_path: Path,
    start_utc: str,
    end_utc: str,
) -> dict[str, object]:
    source_sha256 = runner.file_sha256(source_path)
    return {
        "row_type": "tick_symbol_source",
        "symbol": "XAUUSD",
        "mapped_symbol": "XAUUSD",
        "timeframe": "TICK",
        "path": str(source_path),
        "source_path": str(source_path),
        "source_family": "ftmo_mt5_research_export",
        "source_broker": "FTMO",
        "source_role": "owner_authorized_research_hydration",
        "start_utc": start_utc,
        "end_utc": end_utc,
        "row_count": 1,
        "rows": 1,
        "sha256": source_sha256,
        "source_sha256": source_sha256,
        "export_tool": "scripts/export_mt5_research_ticks.py",
        "manifest_path": str(manifest_path),
        "source_server_redacted": "redacted:test",
        "source_server_hash": "b" * 64,
        "source_account_redacted": "redacted:test",
        "source_account_hash": "c" * 64,
        "source_truth_scope": runner.SOURCE_TRUTH_SCOPE,
        "not_redacted_account_native": True,
        "broker_lifecycle_truth_satisfied": False,
        "ordered_tick_truth_satisfied": True,
        "replaces_missing_frozen_path_source": False,
        "diagnostic_fallback_only": False,
        "selected_status": "selected_priority_tick_source",
        "status": "selected_priority_tick_source",
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "evidence_class": runner.SOURCE_BOUND_EVIDENCE_CLASS,
    }


def test_sealed_source_ledger_tick_authority_preserves_full_component_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    in_window = tmp_path / "in-window.jsonl"
    out_of_window = tmp_path / "out-of-window.jsonl"
    in_window.write_text('{"tick":"in"}\n', encoding="utf-8")
    out_of_window.write_text('{"tick":"out"}\n', encoding="utf-8")
    ledger = tmp_path / "SOURCE_UNIVERSE_LEDGER.jsonl"
    rows = [
        _sealed_tick_source_row(
            source_path=in_window,
            manifest_path=manifest,
            start_utc="2026-04-01T00:00:00+00:00",
            end_utc="2026-04-01T01:00:00+00:00",
        ),
        _sealed_tick_source_row(
            source_path=out_of_window,
            manifest_path=manifest,
            start_utc="2026-05-13T00:00:00+00:00",
            end_utc="2026-05-13T01:00:00+00:00",
        ),
    ]
    ledger.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

    specs, authority = (
        runner.bound_tick_source_authority_from_sealed_source_ledger(
            ledger_path=ledger,
            expected_ledger_sha256=runner.file_sha256(ledger),
        )
    )

    def unexpected_repo_scan(
        _symbol: str, *, repo_root: Path
    ) -> tuple[None, tuple[str, ...]]:
        raise AssertionError(f"ambient repository scan entered: {repo_root}")

    monkeypatch.setattr(
        runner,
        "resolve_ftmo_tick_source",
        unexpected_repo_scan,
    )
    resolver = runner.BroadSourceResolver(
        bound_tick_source_specs=specs,
        sealed_tick_full_component_set=True,
    )
    source = resolver.resolve_tick(
        "XAUUSD",
        source_authority_days=("2026-04-01",),
    )

    assert source is not None
    assert tuple(spec.path for spec in source.rows_by_day.specs) == (
        in_window,
        out_of_window,
    )
    assert authority["source_count"] == 2
    assert authority["symbol_count"] == 1
    assert authority["full_component_set_preserved"] is True
    assert authority["ambient_repository_scan_enabled"] is False


def test_sealed_source_ledger_tick_authority_fails_closed(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    source = tmp_path / "ticks.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    row = _sealed_tick_source_row(
        source_path=source,
        manifest_path=manifest,
        start_utc="2026-04-01T00:00:00+00:00",
        end_utc="2026-04-01T01:00:00+00:00",
    )
    ledger = tmp_path / "SOURCE_UNIVERSE_LEDGER.jsonl"
    ledger.write_text(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="sealed_tick_source_ledger_sha256_mismatch",
    ):
        runner.bound_tick_source_authority_from_sealed_source_ledger(
            ledger_path=ledger,
            expected_ledger_sha256="0" * 64,
        )

    ledger.write_text(
        (
            json.dumps(row, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        * 2,
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match="sealed_tick_source_ledger_duplicate_source",
    ):
        runner.bound_tick_source_authority_from_sealed_source_ledger(
            ledger_path=ledger,
            expected_ledger_sha256=runner.file_sha256(ledger),
        )

    row["live_broker_authority"] = True
    ledger.write_text(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match="sealed_tick_source_ledger_authority_invalid",
    ):
        runner.bound_tick_source_authority_from_sealed_source_ledger(
            ledger_path=ledger,
            expected_ledger_sha256=runner.file_sha256(ledger),
        )


@pytest.mark.parametrize(
    ("stop_after_parity_gate", "expected_window_end_utc"),
    [
        (True, "2026-01-09T00:00:00+00:00"),
        (False, "2026-02-02T00:00:00+00:00"),
    ],
)
def test_attempt5_effective_tick_sparse_cache_window_tracks_executed_days(
    stop_after_parity_gate: bool,
    expected_window_end_utc: str,
) -> None:
    args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=stop_after_parity_gate,
    )

    window_start, window_end = (
        runner.attempt5_effective_execution_tick_sparse_cache_window(args)
    )

    assert window_start.isoformat() == "2025-12-31T00:00:00+00:00"
    assert window_end.isoformat() == expected_window_end_utc
    assert args.end == runner.ATTEMPT5_CONTRACT_END_DAY


def test_attempt5_effective_tick_sparse_cache_window_honors_bounded_checkpoint() -> None:
    args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=False,
        task2_semantic_checkpoint_after_day="2026-01-02",
        physical_reference_checkpoint_after_day=None,
    )

    window_start, window_end = (
        runner.attempt5_effective_execution_tick_sparse_cache_window(args)
    )

    assert window_start.isoformat() == "2025-12-31T00:00:00+00:00"
    assert window_end.isoformat() == "2026-01-04T00:00:00+00:00"


def test_attempt5_effective_tick_sparse_cache_window_honors_engineering_stop() -> None:
    args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=False,
        task2_semantic_checkpoint_after_day=None,
        physical_reference_checkpoint_after_day=None,
        engineering_stop_after_day="2026-01-02",
    )

    window_start, window_end = (
        runner.attempt5_effective_execution_tick_sparse_cache_window(args)
    )

    assert window_start.isoformat() == "2025-12-31T00:00:00+00:00"
    assert window_end.isoformat() == "2026-01-04T00:00:00+00:00"


def test_attempt5_tick_sparse_cache_window_can_reuse_bound_execution_superset() -> None:
    args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=False,
        task2_semantic_checkpoint_after_day=None,
        physical_reference_checkpoint_after_day=None,
        engineering_stop_after_day="2026-01-01",
        tick_sparse_cache_window_end_after_day="2026-01-02",
    )

    window_start, window_end = (
        runner.attempt5_effective_execution_tick_sparse_cache_window(args)
    )

    assert window_start.isoformat() == "2025-12-31T00:00:00+00:00"
    assert window_end.isoformat() == "2026-01-04T00:00:00+00:00"


def test_attempt5_tick_sparse_cache_window_rejects_nonsuperset_override() -> None:
    args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=False,
        task2_semantic_checkpoint_after_day=None,
        physical_reference_checkpoint_after_day=None,
        engineering_stop_after_day="2026-01-02",
        tick_sparse_cache_window_end_after_day="2026-01-01",
    )

    with pytest.raises(
        ValueError, match="attempt5_tick_sparse_cache_window_override_invalid"
    ):
        runner.attempt5_effective_execution_tick_sparse_cache_window(args)


def test_arm_neutral_preparation_source_emission_reset_is_exact() -> None:
    resolver = runner.BroadSourceResolver(skip_tick_source=True)
    first = {
        "row_type": "source_selection",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "source_path": "/immutable/source.csv",
    }
    second = {
        "row_type": "m1_symbol_day_source",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "source_path": "/immutable/m1.csv",
        "trading_day": "2026-01-02",
    }
    resolver.emit_source_row(first)
    resolver.emit_source_row(second)

    assert resolver.reset_source_row_emission() == {
        "discarded_preparation_rows": 2,
        "discarded_preparation_keys": 2,
        "source_or_economic_payload_changed": False,
    }
    assert resolver.drain_source_rows() == []

    resolver.emit_source_row(first)
    resolver.emit_source_row(second)
    assert resolver.drain_source_rows() == [first, second]


def test_attempt5_runtime_and_identity_bind_the_same_tick_sparse_window() -> None:
    effective_call = (
        "attempt5_effective_execution_tick_sparse_cache_window(args)"
    )
    raw_contract_call = "attempt5_tick_sparse_cache_window(args.start, args.end)"
    runtime_source = inspect.getsource(runner._run_typed_sparse_attempt5)
    identity_source = inspect.getsource(runner.run_typed_sparse_attempt5)

    assert runtime_source.count(effective_call) == 1
    assert identity_source.count(effective_call) == 1
    assert raw_contract_call not in runtime_source
    assert raw_contract_call not in identity_source


def test_attempt5_pre_and_post_day_capacity_gates_scope_bounded_settlement() -> None:
    runtime_source = inspect.getsource(runner._run_typed_sparse_attempt5)
    bounded_args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=True,
    )
    continuing_args = SimpleNamespace(
        start=runner.ATTEMPT5_START_DAY,
        end=runner.ATTEMPT5_CONTRACT_END_DAY,
        parity_gate_after_day=runner.ATTEMPT5_PARITY_DAY,
        stop_after_parity_gate=False,
    )

    assert runner.ATTEMPT5_STREAMING_HARD_FLOOR_BYTES == 0
    assert runner.ATTEMPT5_STREAMING_DAY_TRANSIENT_HEADROOM_BYTES == 768 * 1024**2
    assert runner.ATTEMPT5_STREAMING_BOUNDED_WARNING_FLOOR_BYTES == 0
    assert (
        runner.ATTEMPT5_STREAMING_BOUNDED_WARNING_FLOOR_BYTES
        + runner.ATTEMPT5_STREAMING_DAY_TRANSIENT_HEADROOM_BYTES
        == runner.ATTEMPT5_STREAMING_DAY_TRANSIENT_HEADROOM_BYTES
    )
    assert runner.B7_5_MANDATORY_POST_REPLAY_RESERVE_BYTES == 0
    assert runner.attempt5_streaming_warning_floor_bytes(
        bounded_args,
        parity_gate_requested=True,
    ) == runner.ATTEMPT5_STREAMING_BOUNDED_WARNING_FLOOR_BYTES
    assert runner.attempt5_streaming_warning_floor_bytes(
        continuing_args,
        parity_gate_requested=True,
    ) == runner.B7_5_MANDATORY_POST_REPLAY_RESERVE_BYTES
    assert runner.attempt5_streaming_warning_floor_bytes(
        bounded_args,
        parity_gate_requested=False,
    ) == runner.B7_5_MANDATORY_POST_REPLAY_RESERVE_BYTES
    assert (
        "warning_floor_free_bytes="
        "attempt5_streaming_warning_floor_bytes("
    ) in runtime_source
    assert (
        "hard_floor_free_bytes=ATTEMPT5_STREAMING_HARD_FLOOR_BYTES"
    ) in runtime_source
    assert (
        "min_transient_headroom_bytes="
        "ATTEMPT5_STREAMING_DAY_TRANSIENT_HEADROOM_BYTES"
    ) in runtime_source
    assert runtime_source.count("streaming_archive.require_day_capacity(") == 2
    assert runtime_source.count("settle_timeout_seconds=300") == 3
    assert runtime_source.count("settle_poll_seconds=5") == 3
    assert runtime_source.count(
        "on_advisory_miss=lambda: reclaim_runtime_memory_pressure("
    ) == 3
    assert runtime_source.count("darwin_allocator_pressure_relief()") == 2
    assert (
        "post_archive_capacity = streaming_archive.require_day_capacity("
        in runtime_source
    )
    assert "archive_shard = streaming_archive.seal_and_reclaim(" in runtime_source
    assert (
        "post_archive_capacity = streaming_archive.day_capacity_contract("
        not in runtime_source
    )


def test_darwin_allocator_pressure_relief_releases_all_malloc_zones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, int]] = []

    class PressureRelief:
        argtypes: object = None
        restype: object = None

        def __call__(self, zone: object, goal: int) -> int:
            calls.append((zone, goal))
            return 987_654_321

    pressure_relief = PressureRelief()

    class Library:
        malloc_zone_pressure_relief = pressure_relief

    monkeypatch.setattr(runner.sys, "platform", "darwin")
    monkeypatch.setattr(runner.ctypes, "CDLL", lambda _name: Library())

    released = runner.darwin_allocator_pressure_relief()

    assert released == 987_654_321
    assert calls == [(None, 0)]
    assert pressure_relief.argtypes == [
        runner.ctypes.c_void_p,
        runner.ctypes.c_size_t,
    ]
    assert pressure_relief.restype is runner.ctypes.c_size_t


@pytest.mark.parametrize("platform", ("linux", "win32"))
def test_allocator_pressure_relief_is_noop_off_darwin(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
) -> None:
    monkeypatch.setattr(runner.sys, "platform", platform)
    monkeypatch.setattr(
        runner.ctypes,
        "CDLL",
        lambda _name: pytest.fail("non-Darwin allocator library opened"),
    )

    assert runner.darwin_allocator_pressure_relief() == 0


def test_resolver_tick_pressure_release_preserves_bound_wrapper_identity() -> None:
    class LoadedRows:
        def __init__(self) -> None:
            self.calls = 0

        def release_all_loaded_days(self) -> int:
            self.calls += 1
            return 42

    rows_by_day = LoadedRows()
    source = SimpleNamespace(rows_by_day=rows_by_day)
    resolver = runner.BroadSourceResolver(skip_tick_source=True)
    cache_key = ("XAUUSD", ("2026-01-01", "2026-01-07"))
    resolver._tick_cache[cache_key] = source  # type: ignore[assignment]

    assert resolver.release_all_loaded_tick_days() == 42
    assert resolver._tick_cache[cache_key] is source
    assert resolver._tick_cache[cache_key].rows_by_day is rows_by_day
    assert rows_by_day.calls == 1


def test_runtime_memory_pressure_reclaim_orders_live_tick_eviction_before_gc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class Resolver:
        def release_all_loaded_tick_days(self) -> int:
            events.append("tick")
            return 1_057_892

    monkeypatch.setattr(
        runner,
        "clear_replay_source_caches",
        lambda: events.append("replay"),
    )
    monkeypatch.setattr(
        runner,
        "replay_source_cache_counts",
        lambda: {"closed_bar_index": 0, "predecision_tick_query": 0},
    )
    monkeypatch.setattr(
        runner.gc,
        "collect",
        lambda: events.append("gc") or 34_919_646,
    )
    monkeypatch.setattr(
        runner,
        "darwin_allocator_pressure_relief",
        lambda: events.append("allocator") or 612_345_678,
    )

    result = runner.reclaim_runtime_memory_pressure(Resolver())  # type: ignore[arg-type]

    assert events == ["tick", "replay", "gc", "allocator"]
    assert result == {
        "released_loaded_tick_rows": 1_057_892,
        "replay_source_cache_entries_remaining": 0,
        "gc_collected_objects": 34_919_646,
        "allocator_released_bytes": 612_345_678,
    }


def test_sparse_tick_window_cache_preserves_legacy_rows_and_scans_gzip_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "XAUUSD.jsonl.gz"
    payloads = [
        {"time_utc": "2025-12-31T23:59:59+00:00", "bid": 99.9, "ask": 100.0},
        {"time_utc": "2026-01-01T00:00:00+00:00", "bid": 99.95, "ask": 100.05},
        {
            "time_utc": "2026-01-01T00:00:01+00:00",
            "bid": 100.0,
            "ask": 100.1,
            "last": 100.05,
            "volume": 1,
        },
        {
            "time_utc": "2026-01-01T00:00:01+00:00",
            "bid": 100.0,
            "ask": 100.1,
            "last": 100.05,
            "volume": 1,
        },
        {
            "time_utc": "2026-01-01T00:30:00+00:00",
            "bid": 100.2,
            "ask": 100.3,
            "last": 100.25,
            "volume": 2,
        },
        {
            "time_utc": "2026-01-01T00:30:00+00:00",
            "bid": "100.15",
            "ask": "100.25",
            "last": "100.20",
            "volume": "2",
        },
        {
            "time_utc": "2026-01-01T01:00:00+00:00",
            "bid": 100.4,
            "ask": 100.5,
            "last": 100.45,
            "volume": 4,
        },
        {
            "time_utc": "2026-01-02T00:15:00+00:00",
            "bid": 101.0,
            "ask": 101.1,
            "last": 101.05,
            "volume": 3,
        },
        {"time_utc": "2026-01-04T00:00:01+00:00", "bid": 102.0, "ask": 102.1},
    ]
    with gzip.open(source_path, "wt", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    spec = runner.SourceSpec(
        symbol="XAUUSD",
        mapped_symbol="XAUUSD",
        timeframe="TICK",
        path=source_path,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2025-12-31T23:59:59+00:00",
        end_utc="2026-01-04T00:00:01+00:00",
        row_count=len(payloads),
        sha256=runner.file_sha256(source_path),
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )
    first_after = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first_until = first_after + timedelta(hours=1)
    second_after = datetime(2026, 1, 2, tzinfo=timezone.utc)
    second_until = second_after + timedelta(hours=1)
    legacy = runner.LazyTickRowsByDay(symbol="XAUUSD", specs=(spec,))
    expected_first = legacy.query(after=first_after, until=first_until)
    expected_second = legacy.query(after=second_after, until=second_until)

    source_gzip_open_count = 0
    real_gzip_open = runner.gzip.open

    def counting_gzip_open(path: object, *args: object, **kwargs: object):
        nonlocal source_gzip_open_count
        if Path(path) == source_path:
            source_gzip_open_count += 1
        return real_gzip_open(path, *args, **kwargs)

    monkeypatch.setattr(runner.gzip, "open", counting_gzip_open)
    sparse = runner.SparseTickWindowRowsByDay(
        symbol="XAUUSD",
        spec=spec,
        cache_root=tmp_path / "cache",
        window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )

    assert sparse.query(after=first_after, until=first_until) == expected_first
    assert sparse.query(after=second_after, until=second_until) == expected_second
    assert source_gzip_open_count == 1
    assert sparse.last_validation_events == legacy.last_validation_events
    assert (sparse.entry / "manifest.json").is_file()
    assert (sparse.entry / "SEALED").is_file()

    sparse_identity = sparse.identity
    sparse_identity_root = sparse.identity_root_sha256
    sparse_entry = sparse.entry
    loaded_row_count = sum(
        len(rows) for rows, _timestamps in sparse._day_cache.values()
    )

    assert sparse.release_all_loaded_days() == loaded_row_count
    assert not sparse._day_cache
    assert sparse.identity is sparse_identity
    assert sparse.identity_root_sha256 == sparse_identity_root
    assert sparse.entry == sparse_entry
    assert sparse.query(after=first_after, until=first_until) == expected_first
    assert sparse.query(after=second_after, until=second_until) == expected_second
    assert source_gzip_open_count == 1

    parse_count = 0
    real_parse_row_time = runner.parse_row_time

    def counting_parse_row_time(row: object):
        nonlocal parse_count
        parse_count += 1
        return real_parse_row_time(row)  # type: ignore[arg-type]

    monkeypatch.setattr(runner, "parse_row_time", counting_parse_row_time)
    assert sparse.query(after=first_after, until=first_until) == expected_first
    assert parse_count == 0
    monkeypatch.setattr(runner, "parse_row_time", real_parse_row_time)

    warm = runner.SparseTickWindowRowsByDay(
        symbol="XAUUSD",
        spec=spec,
        cache_root=tmp_path / "cache",
        window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    assert warm.query(after=first_after, until=first_until) == expected_first
    assert source_gzip_open_count == 1

    def resolved(rows_by_day: object) -> runner.ResolvedSource:
        return runner.ResolvedSource(
            spec=spec,
            rows=(),
            rows_by_day=rows_by_day,  # type: ignore[arg-type]
            sha256=str(spec.sha256),
            day_counts={},
            selected_status="selected_priority_tick_sources_lazy_window_load",
            min_required_rows_per_day=1,
        )

    legacy_query = runner.timewarp_loop.PathTruthIndex(
        resolved(
            runner.ConflictCheckedLazyTickRowsByDay(
                symbol="XAUUSD",
                specs=(spec,),
            )
        )
    ).query(after=first_after, until=first_until)
    sparse_query = runner.timewarp_loop.PathTruthIndex(
        resolved(
            runner.ConflictCheckedLazyTickRowsByDay(
                symbol="XAUUSD",
                specs=(spec,),
                sparse_cache_root=tmp_path / "cache",
                sparse_window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
                sparse_window_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
            )
        )
    ).query(after=first_after, until=first_until)
    assert json.dumps(
        {"rows": legacy_query.rows, "metadata": legacy_query.metadata},
        sort_keys=True,
    ) == json.dumps(
        {"rows": sparse_query.rows, "metadata": sparse_query.metadata},
        sort_keys=True,
    )


def test_sparse_tick_filesystem_compression_preserves_exact_bytes(
    tmp_path: Path,
) -> None:
    partition = tmp_path / "partition.jsonl"
    partition.write_bytes(
        (
            b'{"ask":2000.1,"bid":2000.0,'
            b'"time_utc":"2026-01-02T00:00:01+00:00"}\n'
        )
        * 20_000
    )
    expected_sha256 = runner.file_sha256(partition)
    expected_bytes = partition.stat().st_size

    result = runner.compress_sparse_tick_partition_losslessly(
        partition,
        expected_sha256=expected_sha256,
    )

    assert partition.stat().st_size == expected_bytes
    assert runner.file_sha256(partition) == expected_sha256
    assert result["logical_bytes"] == expected_bytes
    assert result["sha256"] == expected_sha256
    assert result["allocated_bytes_after"] <= result["allocated_bytes_before"]
    assert result["status"] in {
        "APFS_TRANSPARENT_COMPRESSION_APPLIED",
        "FILESYSTEM_COMPRESSION_UNAVAILABLE",
    }
    if runner.sys.platform == "darwin" and runner.shutil.which("ditto"):
        assert result["status"] == "APFS_TRANSPARENT_COMPRESSION_APPLIED"
        assert result["allocated_bytes_after"] < result["allocated_bytes_before"]


def test_sparse_tick_cache_manifest_ignores_filesystem_storage_telemetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "EURUSD.jsonl"
    source_path.write_text(
        '{"time_utc":"2026-01-01T00:00:01+00:00",'
        '"bid":1.1,"ask":1.2,"volume":1}\n',
        encoding="utf-8",
    )
    spec = runner.SourceSpec(
        symbol="EURUSD",
        mapped_symbol="EURUSD",
        timeframe="TICK",
        path=source_path,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2026-01-01T00:00:01+00:00",
        end_utc="2026-01-01T00:00:01+00:00",
        row_count=1,
        sha256=runner.file_sha256(source_path),
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )

    def build(cache_root: Path, *, allocated_after: int, status: str):
        def fake_compress(path: Path, *, expected_sha256: str) -> dict[str, object]:
            return {
                "schema": runner.SPARSE_TICK_FILESYSTEM_STORAGE_SCHEMA,
                "status": status,
                "logical_bytes": path.stat().st_size,
                "allocated_bytes_before": path.stat().st_size,
                "allocated_bytes_after": allocated_after,
                "sha256": expected_sha256,
            }

        monkeypatch.setattr(
            runner,
            "compress_sparse_tick_partition_losslessly",
            fake_compress,
        )
        sparse = runner.SparseTickWindowRowsByDay(
            symbol="EURUSD",
            spec=spec,
            cache_root=cache_root,
            window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
            window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        sparse._ensure_entry()
        manifest_path = sparse.entry / "manifest.json"
        return (
            manifest_path.read_bytes(),
            json.loads(manifest_path.read_text(encoding="ascii")),
            sparse._filesystem_storage_telemetry,
        )

    first_bytes, first_manifest, first_telemetry = build(
        tmp_path / "cache-a",
        allocated_after=4096,
        status="APFS_TRANSPARENT_COMPRESSION_APPLIED",
    )
    second_bytes, second_manifest, second_telemetry = build(
        tmp_path / "cache-b",
        allocated_after=8192,
        status="FILESYSTEM_COMPRESSION_UNAVAILABLE",
    )

    assert first_bytes == second_bytes
    assert first_manifest["manifest_root_sha256"] == second_manifest[
        "manifest_root_sha256"
    ]
    assert all(
        "filesystem_storage" not in partition
        for partition in first_manifest["partitions"]
    )
    assert first_telemetry != second_telemetry


def test_sparse_tick_window_cache_rejects_partition_drift(tmp_path: Path) -> None:
    source_path = tmp_path / "EURUSD.jsonl.gz"
    with gzip.open(source_path, "wt", encoding="utf-8") as handle:
        handle.write(
            '{"time_utc":"2026-01-01T00:00:01+00:00",'
            '"bid":1.1,"ask":1.2,"volume":1}\n'
        )
    spec = runner.SourceSpec(
        symbol="EURUSD",
        mapped_symbol="EURUSD",
        timeframe="TICK",
        path=source_path,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2026-01-01T00:00:01+00:00",
        end_utc="2026-01-01T00:00:01+00:00",
        row_count=1,
        sha256=runner.file_sha256(source_path),
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )
    sparse = runner.SparseTickWindowRowsByDay(
        symbol="EURUSD",
        spec=spec,
        cache_root=tmp_path / "cache",
        window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    after = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sparse.query(after=after, until=after + timedelta(minutes=1))
    partition = next((sparse.entry / "partitions").glob("*.jsonl"))
    partition.write_bytes(partition.read_bytes() + b"{}\n")
    cold = runner.SparseTickWindowRowsByDay(
        symbol="EURUSD",
        spec=spec,
        cache_root=tmp_path / "cache",
        window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    with pytest.raises(RuntimeError, match="sparse_tick_cache_partition_invalid"):
        cold.query(after=after, until=after + timedelta(minutes=1))


def test_sparse_tick_conflicts_remain_query_scoped(tmp_path: Path) -> None:
    paths = (tmp_path / "component-a.jsonl", tmp_path / "component-b.jsonl")
    rows_by_path = (
        (
            {"time_utc": "2026-01-01T00:00:01+00:00", "bid": 1.0, "ask": 1.1},
            {"time_utc": "2026-01-02T00:00:01+00:00", "bid": 1.2, "ask": 1.3},
        ),
        (
            {"time_utc": "2026-01-01T00:00:01+00:00", "bid": 1.0, "ask": 1.1},
            {"time_utc": "2026-01-02T00:00:01+00:00", "bid": 1.4, "ask": 1.5},
        ),
    )
    specs = []
    for index, path in enumerate(paths):
        with path.open("w", encoding="utf-8") as handle:
            for payload in rows_by_path[index]:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        specs.append(
            runner.SourceSpec(
                symbol="EURUSD",
                mapped_symbol="EURUSD",
                timeframe="TICK",
                path=path,
                source_family="ftmo_mt5_research_export",
                source_broker="FTMO",
                source_role="owner_authorized_research_hydration",
                start_utc="2026-01-01T00:00:01+00:00",
                end_utc="2026-01-02T00:00:01+00:00",
                row_count=2,
                sha256=runner.file_sha256(path),
                source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
                not_redacted_account_native=True,
                ordered_tick_truth_satisfied=True,
            )
        )
    rows_by_day = runner.ConflictCheckedLazyTickRowsByDay(
        symbol="EURUSD",
        specs=tuple(specs),
        sparse_cache_root=tmp_path / "cache",
        sparse_window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        sparse_window_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    jan1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    jan2 = datetime(2026, 1, 2, tzinfo=timezone.utc)

    rows, days = rows_by_day.query(after=jan1, until=jan1 + timedelta(minutes=1))
    assert len(rows) == 1
    assert days == ["2026-01-01"]
    with pytest.raises(
        RuntimeError,
        match="conflicting_overlapping_tick_observations:EURUSD:2026-01-02",
    ):
        rows_by_day.query(after=jan2, until=jan2 + timedelta(minutes=1))


def test_sparse_tick_prewarm_is_structural_and_rejects_out_of_order_source(
    tmp_path: Path,
) -> None:
    valid_path = tmp_path / "valid.jsonl"
    valid_path.write_text(
        '\n'.join(
            (
                '{"time_utc":"2026-01-01T00:00:01+00:00","bid":1.0,"ask":1.1}',
                '{"time_utc":"2026-01-02T00:00:01+00:00","bid":1.1,"ask":1.2}',
            )
        )
        + "\n",
        encoding="utf-8",
    )

    second_valid_path = tmp_path / "valid-xau.jsonl"
    second_valid_path.write_bytes(valid_path.read_bytes())

    def spec(path: Path, symbol: str = "EURUSD") -> runner.SourceSpec:
        return runner.SourceSpec(
            symbol=symbol,
            mapped_symbol=symbol,
            timeframe="TICK",
            path=path,
            source_family="ftmo_mt5_research_export",
            source_broker="FTMO",
            source_role="owner_authorized_research_hydration",
            start_utc="2026-01-01T00:00:01+00:00",
            end_utc="2026-01-02T00:00:01+00:00",
            row_count=2,
            sha256=runner.file_sha256(path),
            source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            ordered_tick_truth_satisfied=True,
        )

    start = datetime(2025, 12, 31, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, tzinfo=timezone.utc)
    receipt = runner.prewarm_sparse_tick_sources(
        specs_by_symbol={
            "EURUSD": (spec(valid_path),),
            "XAUUSD": (spec(second_valid_path, "XAUUSD"),),
        },
        cache_root=tmp_path / "cache",
        window_start=start,
        window_end=end,
        workers=2,
    )
    assert receipt["status"] == "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE"
    assert receipt["entry_count"] == 2
    assert receipt["partition_count"] == 4
    assert receipt["retained_row_count"] == 4
    assert receipt["economic_values_exposed"] is False

    invalid_path = tmp_path / "out-of-order.jsonl"
    invalid_path.write_text(
        '\n'.join(
            (
                '{"time_utc":"2026-01-02T00:00:01+00:00","bid":1.1,"ask":1.2}',
                '{"time_utc":"2026-01-01T00:00:01+00:00","bid":1.0,"ask":1.1}',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="sparse_tick_cache_source_not_time_ordered"):
        runner.prewarm_sparse_tick_sources(
            specs_by_symbol={"EURUSD": (spec(invalid_path),)},
            cache_root=tmp_path / "invalid-cache",
            window_start=start,
            window_end=end,
            workers=1,
        )


def test_sparse_tick_prewarm_retries_serially_only_after_dataless_deadlock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources: dict[str, tuple[runner.SourceSpec, ...]] = {}
    for symbol in ("EURUSD", "XAUUSD"):
        path = tmp_path / f"{symbol}.jsonl"
        path.write_text(
            '{"time_utc":"2026-01-01T00:00:01+00:00","bid":1.0,"ask":1.1}\n',
            encoding="utf-8",
        )
        sources[symbol] = (
            runner.SourceSpec(
                symbol=symbol,
                mapped_symbol=symbol,
                timeframe="TICK",
                path=path,
                source_family="ftmo_mt5_research_export",
                source_broker="FTMO",
                source_role="owner_authorized_research_hydration",
                start_utc="2026-01-01T00:00:01+00:00",
                end_utc="2026-01-01T00:00:01+00:00",
                row_count=1,
                sha256=runner.file_sha256(path),
                source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
                not_redacted_account_native=True,
                ordered_tick_truth_satisfied=True,
            ),
        )

    class DeadlockingPool:
        def __init__(self, *, max_workers: int) -> None:
            self.max_workers = max_workers

        def __enter__(self) -> "DeadlockingPool":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def map(self, *_args: object) -> object:
            raise OSError(errno.EDEADLK, "Resource deadlock avoided")

    monkeypatch.setattr(runner, "ProcessPoolExecutor", DeadlockingPool)
    receipt = runner.prewarm_sparse_tick_sources(
        specs_by_symbol=sources,
        cache_root=tmp_path / "cache",
        window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
        workers=2,
    )

    assert receipt["status"] == "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE"
    assert receipt["entry_count"] == 2
    assert receipt["worker_count"] == 2


def test_sparse_tick_prewarm_reuses_only_stat_bound_verified_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "ticks.jsonl"
    source.write_text(
        '\n'.join(
            (
                '{"time_utc":"2026-01-01T00:00:01+00:00","bid":1.0,"ask":1.1}',
                '{"time_utc":"2026-01-02T00:00:01+00:00","bid":1.1,"ask":1.2}',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    spec = runner.SourceSpec(
        symbol="EURUSD",
        mapped_symbol="EURUSD",
        timeframe="TICK",
        path=source,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2026-01-01T00:00:01+00:00",
        end_utc="2026-01-02T00:00:01+00:00",
        row_count=2,
        sha256=runner.file_sha256(source),
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )
    start = datetime(2025, 12, 31, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, tzinfo=timezone.utc)
    first = runner.prewarm_sparse_tick_sources(
        specs_by_symbol={"EURUSD": (spec,)},
        cache_root=tmp_path / "cache",
        window_start=start,
        window_end=end,
        workers=1,
    )
    assert first["raw_source_full_hash_count"] == 1
    assert first["sealed_cache_reuse_count"] == 0

    original_cached = runner.file_sha256_cached

    def forbid_raw_source_rehash(path: Path) -> str:
        if Path(path).resolve() == source.resolve():
            raise AssertionError("raw tick source was rehashed despite sealed reuse")
        return original_cached(path)

    monkeypatch.setattr(runner, "file_sha256_cached", forbid_raw_source_rehash)
    second = runner.prewarm_sparse_tick_sources(
        specs_by_symbol={"EURUSD": (spec,)},
        cache_root=tmp_path / "cache",
        window_start=start,
        window_end=end,
        workers=1,
    )
    assert second["raw_source_full_hash_count"] == 0
    assert second["sealed_cache_reuse_count"] == 1
    assert second["entries"][0]["source_validation"]["status"] == (
        "SEALED_CACHE_REUSED_AFTER_EXACT_SOURCE_STAT_AND_PARTITION_VALIDATION"
    )


def test_sparse_tick_prewarm_rejects_same_size_partition_corruption(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ticks.jsonl"
    source.write_text(
        '{"time_utc":"2026-01-01T00:00:01+00:00","bid":1.0,"ask":1.1}\n',
        encoding="utf-8",
    )
    spec = runner.SourceSpec(
        symbol="EURUSD",
        mapped_symbol="EURUSD",
        timeframe="TICK",
        path=source,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2026-01-01T00:00:01+00:00",
        end_utc="2026-01-01T00:00:01+00:00",
        row_count=1,
        sha256=runner.file_sha256(source),
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )
    cache_root = tmp_path / "cache"
    start = datetime(2025, 12, 31, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, tzinfo=timezone.utc)
    first = runner.prewarm_sparse_tick_sources(
        specs_by_symbol={"EURUSD": (spec,)},
        cache_root=cache_root,
        window_start=start,
        window_end=end,
        workers=1,
    )
    entry = cache_root / first["entries"][0]["identity_root_sha256"]
    manifest = json.loads((entry / "manifest.json").read_text(encoding="ascii"))
    partition = entry / manifest["partitions"][0]["path"]
    damaged = bytearray(partition.read_bytes())
    damaged[-2] = ord("9") if damaged[-2] != ord("9") else ord("8")
    partition.write_bytes(bytes(damaged))

    with pytest.raises(
        RuntimeError,
        match="sparse_tick_cache_partition_sha256_mismatch",
    ):
        runner.prewarm_sparse_tick_sources(
            specs_by_symbol={"EURUSD": (spec,)},
            cache_root=cache_root,
            window_start=start,
            window_end=end,
            workers=1,
        )


def test_tick_window_authority_reuses_exact_sparse_source_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "ticks.jsonl"
    source_path.write_text(
        '{"time_utc":"2026-01-01T00:00:01+00:00","bid":1.0,"ask":1.1}\n',
        encoding="utf-8",
    )
    source_sha256 = runner.file_sha256(source_path)
    spec = runner.SourceSpec(
        symbol="EURUSD",
        mapped_symbol="EURUSD",
        timeframe="TICK",
        path=source_path,
        source_family="ftmo_mt5_research_export",
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc="2026-01-01T00:00:01+00:00",
        end_utc="2026-01-02T00:00:01+00:00",
        row_count=1,
        sha256=source_sha256,
        source_truth_scope=runner.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        ordered_tick_truth_satisfied=True,
    )
    resolved = runner.ResolvedSource(
        spec=spec,
        rows=(),
        rows_by_day={},
        sha256=source_sha256,
        day_counts={},
        selected_status="selected_priority_tick_sources_lazy_window_load",
        min_required_rows_per_day=1,
        component_source_labels=(
            {
                "path": str(source_path),
                "start_utc": spec.start_utc,
                "end_utc": spec.end_utc,
                "row_count": spec.row_count,
                "sha256": source_sha256,
            },
        ),
    )
    receipt = runner.prewarm_sparse_tick_sources(
        specs_by_symbol={"EURUSD": (spec,)},
        cache_root=tmp_path / "cache",
        window_start=datetime(2025, 12, 31, tzinfo=timezone.utc),
        window_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
        workers=1,
    )
    expected = runner.tick_window_source_authority(
        symbol="EURUSD",
        source=resolved,
        source_authority_days=("2026-01-01",),
    )
    attestations = runner.sparse_tick_source_attestations(receipt)
    original_hash = runner.file_sha256_cached

    def forbid_raw_source_rehash(path: Path) -> str:
        if Path(path).resolve() == source_path.resolve():
            raise AssertionError("raw tick source was rehashed after exact prewarm")
        return original_hash(path)

    monkeypatch.setattr(runner, "file_sha256_cached", forbid_raw_source_rehash)
    actual = runner.tick_window_source_authority(
        symbol="EURUSD",
        source=resolved,
        source_authority_days=("2026-01-01",),
        integrity_attestations=attestations,
    )

    assert actual == expected

    source_path.write_bytes(source_path.read_bytes().replace(b'"bid":1.0', b'"bid":2.0'))
    drift = runner.tick_window_source_authority(
        symbol="EURUSD",
        source=resolved,
        source_authority_days=("2026-01-01",),
        integrity_attestations=attestations,
    )
    assert drift["integrity_valid"] is False
    assert drift["components"][0]["actual_sha256"] is None


def test_bound_tick_diagnostics_preserve_named_gaps_without_repo_scan(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "archive"
    route = repo_root / "research/operations/tick-proof"
    valid_path = route / "ticks/BTCUSD/valid.jsonl"
    zero_path = route / "ticks/BTCUSD/zero.jsonl"
    valid_path.parent.mkdir(parents=True)
    valid_path.write_text("{}\n", encoding="utf-8")
    zero_path.write_text("{}\n", encoding="utf-8")
    manifest_path = route / "manifest.json"

    def payload(path: str, *, rows: int) -> dict[str, object]:
        return {
            "file_symbol": "BTCUSD",
            "mt5_symbol": "BTCUSD",
            "timeframe": "TICK",
            "path": path,
            "manifest_path": "research/operations/tick-proof/manifest.json",
            "row_count": rows,
            "sha256": "a" * 64,
            "source_broker": "FTMO",
            "source_role": "owner_authorized_research_hydration",
            "source_truth_scope": runner.SOURCE_TRUTH_SCOPE,
            "not_redacted_account_native": True,
            "first": "2026-04-01T00:00:00+00:00",
            "last": "2026-04-01T01:00:00+00:00",
        }

    manifest_path.write_text(
        json.dumps(
            {
                "files": {
                    "missing": payload(
                        "research/operations/tick-proof/ticks/BTCUSD/missing.jsonl",
                        rows=1,
                    ),
                    "zero": payload(
                        "research/operations/tick-proof/ticks/BTCUSD/zero.jsonl",
                        rows=0,
                    ),
                    "valid": payload(
                        "research/operations/tick-proof/ticks/BTCUSD/valid.jsonl",
                        rows=1,
                    ),
                }
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    gaps, contract = runner.bound_tick_diagnostic_authority(
        ((manifest_path, runner.file_sha256(manifest_path)),)
    )

    assert gaps["BTCUSD"] == (
        f"{manifest_path}:BTCUSD_TICK:export_path_missing:"
        f"{route}/ticks/BTCUSD/missing.jsonl",
        f"{manifest_path}:BTCUSD_TICK:row_count_missing_or_zero",
    )
    assert contract["gap_count"] == 2
    assert contract["manifests"][0]["valid_outside_window_source_count"] == 1


def test_attempt5_authority_rejects_missing_zstd_before_namespace_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path, monkeypatch)
    monkeypatch.setattr(runner.shutil, "which", lambda _name: None)

    with pytest.raises(ValueError, match="attempt5_zstd_unavailable"):
        runner.require_attempt5_execution_authority(args)

    assert not args.output_dir.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("arm_id", "S1R0"),
        ("source_prewarm_workers", 1),
        ("stop_after_parity_gate", False),
        ("finalize_existing_prefix", True),
        ("tick_sparse_cache_root", Path("/tmp/unbound-tick-cache")),
    ],
)
def test_attempt5_authority_rejects_route_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    args = _args(tmp_path, monkeypatch)
    setattr(args, field, value)
    with pytest.raises(ValueError):
        runner.require_attempt5_execution_authority(args)


def test_attempt5_runner_writes_identity_before_policy_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path, monkeypatch)
    monkeypatch.setattr(
        runner,
        "_run_typed_sparse_attempt5",
        lambda _args: {"status": "test-policy-not-entered"},
    )
    result = runner.run_typed_sparse_attempt5(args)
    identity_path = (
        args.output_dir / "ATTEMPT5_TYPED_SPARSE_EXECUTION_IDENTITY.json"
    )
    identity = json.loads(identity_path.read_text(encoding="ascii"))
    assert result == {"status": "test-policy-not-entered"}
    assert identity["legacy_replay_route_invoked"] is False
    assert identity["other_arms_launched"] is False
    assert identity["broker_live_authority"] is False
    assert identity["output_namespace"] == str(args.output_dir.resolve())
    assert identity["prospective_golden_authority"] == (
        args.prospective_golden_authority
    )
    assert identity["source_bundle_consumer_rebind_authority"] == (
        args.bound_source_bundle_consumer_rebind_authority
    )
    assert identity["tick_sparse_cache"] == {
        "schema": runner.SPARSE_TICK_CACHE_SCHEMA,
        "root": str(args.tick_sparse_cache_root.resolve()),
        "window_start_utc": "2025-12-31T00:00:00+00:00",
        "window_end_utc": "2026-01-09T00:00:00+00:00",
        "source_plan_or_replay_semantics_changed": False,
    }


def test_compact_seal_failure_aborts_and_stays_outside_economic_timer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sink = runner.ReplayCompactEventSink(
        root=tmp_path / "seal-failure",
        defer_seal_to_caller=True,
    )
    sink.append(
        "missed",
        {
            "candidate_id": "fixture-candidate",
            "canonical_replay_candidate_instance_key": "fixture-instance",
        },
    )
    original_seal = sink.seal

    def fail_seal() -> dict[str, object]:
        raise ValueError("injected_deferred_seal_failure")

    monkeypatch.setattr(sink, "seal", fail_seal)
    with pytest.raises(
        ValueError,
        match="injected_deferred_seal_failure",
    ):
        runner._seal_compact_event_sink_after_economic_hot_path(
            result={},
            compact_event_sink=sink,
        )

    assert not sink._open
    assert not (sink.root / "COMPACT_EVENT_MANIFEST.json").exists()
    monkeypatch.setattr(sink, "seal", original_seal)
    with pytest.raises(ValueError, match="sink_aborted"):
        sink.seal()

    runtime_source = inspect.getsource(runner._run_typed_sparse_attempt5)
    economic_stop = runtime_source.index("economic_hot_path_seconds = round")
    deferred_seal = runtime_source.index(
        "_seal_compact_event_sink_after_economic_hot_path("
    )
    assert economic_stop < deferred_seal


def test_legacy_entrypoint_is_execution_denial_only() -> None:
    legacy = runner.CODE_ROUTE / "run_broad_live_as_if_replay_harness.py"
    source = legacy.read_text(encoding="ascii")
    assert "owner_override_legacy_replay_route_permanently_disabled" in source
    assert "replay_acceleration_attempt5_typed_sparse_runner import" not in source


def test_expected_prepared_pack_roots_are_exact_and_complete_syntax() -> None:
    args = argparse.Namespace(
        expected_prepared_day_pack_roots=[
            "development:2026-01-01:2026-01-01=" + "a" * 64,
            "development:2026-01-02:2026-01-02=" + "b" * 64,
        ]
    )
    assert runner.expected_prepared_day_pack_roots_from_args(args) == {
        ("development", "2026-01-01", "2026-01-01"): "a" * 64,
        ("development", "2026-01-02", "2026-01-02"): "b" * 64,
    }
    args.expected_prepared_day_pack_roots.append(
        "development:2026-01-01:2026-01-01=" + "c" * 64
    )
    with pytest.raises(
        ValueError,
        match="expected_prepared_day_pack_roots_invalid",
    ):
        runner.expected_prepared_day_pack_roots_from_args(args)

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_task9_final_validation as task9


def _rooted(payload: dict, field: str) -> dict:
    core = dict(payload)
    return {**core, field: task9.stable_sha256(core)}


def _trial(
    trial_id: str,
    cache_state: str,
    *,
    wall: float,
    no_event: float = 2.0,
    dense: float = 20.0,
) -> dict:
    semantic_projection = _semantic_projection()
    evidence_files = [
        {"path": "result.json", "bytes": 3, "sha256": "9" * 64}
    ]
    launch_nonce = "d" * 64
    authority_root = "c" * 64
    authority_file = "f" * 64
    input_root = "e" * 64
    if cache_state == task9.COLD_PROCESS_STATE:
        cache_state_evidence = {
            "cache_state": task9.COLD_PROCESS_STATE,
            "cache_authority_root_sha256": authority_root,
            "cache_authority_file_sha256": authority_file,
            "complete_input_inventory_root_sha256": input_root,
            "trial_launch_nonce_sha256": launch_nonce,
            "validation_output_root": "/tmp/task9",
            "priming_request_path": None,
            "priming_request_file_sha256": None,
            "priming_request_root_sha256": None,
            "priming_receipt_path": None,
            "priming_receipt_file_sha256": None,
            "priming_receipt_root_sha256": None,
            "process_cold": True,
            "warm_filesystem_expected": False,
            "os_page_cache_controlled": False,
        }
    else:
        cache_state_evidence = {
            "cache_state": task9.WARM_FILESYSTEM_STATE,
            "cache_authority_root_sha256": authority_root,
            "cache_authority_file_sha256": authority_file,
            "complete_input_inventory_root_sha256": input_root,
            "trial_launch_nonce_sha256": launch_nonce,
            "validation_output_root": "/tmp/task9",
            "priming_request_path": "/tmp/prime.request.json",
            "priming_request_file_sha256": "1" * 64,
            "priming_request_root_sha256": "2" * 64,
            "priming_receipt_path": "/tmp/prime.receipt.json",
            "priming_receipt_file_sha256": "3" * 64,
            "priming_receipt_root_sha256": "4" * 64,
            "priming_process_launch_nonce_sha256": "5" * 64,
            "process_cold": True,
            "warm_filesystem_expected": True,
            "os_page_cache_controlled": False,
        }
    return {
        "schema": task9.TRIAL_RECEIPT_SCHEMA,
        "status": task9.TRIAL_STATUS,
        "trial_id": trial_id,
        "derived_cache_state": cache_state,
        "cache_state_evidence": cache_state_evidence,
        "request": {
            "path": "/tmp/trial.request.json",
            "file_sha256": "6" * 64,
            "request_root_sha256": "7" * 64,
        },
        "measurement_process": {"launch_nonce_sha256": launch_nonce},
        "semantic_projection": semantic_projection,
        "semantic_projection_root_sha256": task9.stable_sha256(
            semantic_projection
        ),
        "semantic_projection_derivation": {
            "semantic_projection": semantic_projection,
            "semantic_projection_root_sha256": task9.stable_sha256(
                semantic_projection
            ),
            "trial_tick_prewarm": {"prewarm_root_sha256": "8" * 64},
            "derivation": (
                "task8_exact_roles_order_and_preimages_from_bound_ledgers"
            ),
        },
        "cache": {
            "inventory_root_sha256": "b" * 64,
            "pre_inventory_root_sha256": "b" * 64,
            "post_inventory_root_sha256": "b" * 64,
            "cold_partition_count": 0,
            "bytes_written": 0,
        },
        "parity": {
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
            "tick_sparse_cache_raw_source_full_hash_count": 0,
            "tick_sparse_cache_sealed_reuse_count": 4,
        },
        "measurement": {
            "child_wall_seconds": wall,
            "cpu_user_seconds": wall * 0.7,
            "cpu_system_seconds": wall * 0.1,
            "peak_rss_bytes": 1_000,
            "bytes_read": 100,
            "bytes_written": 200,
            "block_input_operations": 2,
            "block_output_operations": 3,
            "swap_used_delta_bytes": 0,
            "no_event_total_seconds": no_event,
            "dense_total_seconds": dense,
            "fixed_campaign_overhead_seconds": wall - no_event - dense,
            "engine_wall_seconds": wall - 1.0,
            "engine_cpu_seconds": wall * 0.75,
            "parity_verification_seconds": 1.0,
        },
        "stage_profile": _stage_profile(),
        "evidence_inventory": {
            "root": "/tmp/trial",
            "file_count": 1,
            "logical_bytes": 3,
            "allocated_bytes": 512,
            "inventory_root_sha256": task9.stable_sha256(evidence_files),
            "files": evidence_files,
        },
        "semantic_diagnostic_inventory": {
            "root": "/tmp/trial.semantic-diagnostic",
            "file_count": 1,
            "logical_bytes": 3,
            "allocated_bytes": 512,
            "inventory_root_sha256": task9.stable_sha256(evidence_files),
            "files": evidence_files,
        },
        "evidence_inventory_policy": {
            "excluded_envelope_paths": sorted(task9.TRIAL_ENVELOPE_PATHS),
            "excluded_paths_are_non_parity_envelope_only": True,
            "all_replay_evidence_files_included": True,
        },
        "output_tree": {
            "logical_bytes": 300,
            "allocated_bytes": 512,
            "file_count": 3,
        },
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }


def _semantic_projection() -> dict:
    roles = {
        role: {"row_count": 0, "ordered_bytes_sha256": "a" * 64}
        for role in sorted(task9.task8.TASK8_SEMANTIC_EXACT_ROLES)
    }
    return {
        "days": {
            task9.task8.DAY1: json.loads(json.dumps(roles)),
            task9.task8.DAY2: json.loads(json.dumps(roles)),
        },
        "order": {
            "row_count": 0,
            "ordered_semantic_projection_root_sha256": "b" * 64,
        },
        "selected_order_preimages": {
            "row_count": 0,
            "projection_root_sha256": "c" * 64,
            "selected_identity_root_sha256": "d" * 64,
            "persisted_order_indexes_root_sha256": "e" * 64,
        },
        "runtime_clock_closure_contract_root_sha256": (
            task9.task8.task8_runtime_clock_closure_contract()[
                "contract_root_sha256"
            ]
        ),
        "tick_sparse_cache_raw_source_full_hash_count": 0,
        "tick_sparse_cache_sealed_reuse_count": 4,
    }


def _stage_profile() -> dict:
    required = set(task9.TASK9_REQUIRED_STAGE_ENTRIES)
    stages = []
    for name in task9.benchmark.REPLAY_STAGE_ORDER:
        entered = 1 if name in required else 0
        wall_ns = (
            1_000_000_000
            if name == "verification"
            else (10 if entered else 0)
        )
        stages.append(
            {
                "name": name,
                "entered_count": entered,
                "wall_ns": wall_ns,
                "self_wall_ns": wall_ns,
                "cpu_user_ns": wall_ns,
                "cpu_system_ns": 0,
                "peak_rss_bytes": 100 if entered else 0,
                "block_input_operations": 0,
                "block_output_operations": 0,
                "output_rows": 0,
                "output_bytes": 0,
            }
        )
    bounds = {
        "cpu_user_ns": 0,
        "cpu_system_ns": 0,
        "peak_rss_bytes": 100,
        "block_input_operations": 0,
        "block_output_operations": 0,
    }
    return {
        "schema": task9.benchmark.STAGE_PROFILE_SCHEMA,
        "enabled": True,
        "clock": "perf_counter_ns",
        "stage_order": list(task9.benchmark.REPLAY_STAGE_ORDER),
        "stages": stages,
        "call_counters": {
            name: 1 for name in sorted(task9.TASK9_REQUIRED_CALL_COUNTERS)
        },
        "output_counters": {},
        "resource_bounds": {"first": bounds, "last": bounds},
    }


def test_inventory_tree_is_content_bound_and_rejects_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "cache"
    root.mkdir()
    (root / "b.bin").write_bytes(b"two")
    (root / "a.bin").write_bytes(b"one")

    first = task9.inventory_tree(root)
    second = task9.inventory_tree(root)

    assert first == second
    assert [row["path"] for row in first["files"]] == ["a.bin", "b.bin"]
    assert first["file_count"] == 2
    assert first["logical_bytes"] == 6
    assert first["inventory_root_sha256"] == task9.stable_sha256(first["files"])

    (root / "link").symlink_to(root / "a.bin")
    with pytest.raises(task9.Task9Rejected, match="task9_inventory_symlink_forbidden"):
        task9.inventory_tree(root)


def test_historical_rooted_receipt_may_be_pretty_printed_when_explicit(
    tmp_path: Path,
) -> None:
    core = {"schema": "historical", "status": "accepted"}
    payload = {**core, "receipt_root_sha256": task9.stable_sha256(core)}
    path = tmp_path / "historical.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    with pytest.raises(task9.Task9Rejected, match="canonical_bytes_invalid"):
        task9._load_rooted_json(
            path,
            root_field="receipt_root_sha256",
            code="task9_test_historical",
        )
    assert task9._load_rooted_json(
        path,
        root_field="receipt_root_sha256",
        code="task9_test_historical",
        require_canonical_bytes=False,
    ) == payload


def test_cache_state_is_derived_from_authenticated_priming_receipt(
    tmp_path: Path,
) -> None:
    cache_root = "c" * 64
    authority_root = "a" * 64
    authority_file = "b" * 64
    input_root = "f" * 64
    validation_root = tmp_path / "run"
    requests_root = validation_root / "requests"
    authority_dir = validation_root / "cache-authority"
    requests_root.mkdir(parents=True)
    authority_dir.mkdir()
    authority_path = authority_dir / "TASK9_TYPED_CACHE_AUTHORITY.json"
    authority_path.write_bytes(b"authority")
    assert task9.derive_cache_state(
        priming_receipt_path=None,
        priming_receipt_file_sha256=None,
        expected_cache_inventory_root_sha256=cache_root,
        expected_cache_authority_path=authority_path,
        expected_cache_authority_file_sha256=authority_file,
        expected_cache_authority_root_sha256=authority_root,
        expected_complete_input_inventory_root_sha256=input_root,
        expected_validation_output_root=validation_root,
        current_launch_nonce_sha256="d" * 64,
    )["cache_state"] == task9.COLD_PROCESS_STATE

    prime_request_core = {
        "schema": task9.PRIMING_REQUEST_SCHEMA,
        "cache_authority_path": str(authority_path.resolve()),
        "cache_authority_file_sha256": authority_file,
        "cache_authority_root_sha256": authority_root,
        "complete_input_inventory_root_sha256": input_root,
        "launch_nonce_sha256": "e" * 64,
        "expected_orchestrator_pid": 1,
        "validation_output_root": str(validation_root.resolve()),
        "receipt_path": str(
            (requests_root / "W1.prime.request.receipt.json").resolve()
        ),
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    prime_request = _rooted(prime_request_core, "request_root_sha256")
    prime_request_path = requests_root / "W1.prime.request.json"
    task9.atomic_write_json(prime_request_path, prime_request)
    core = {
        "schema": task9.PRIMING_RECEIPT_SCHEMA,
        "status": task9.PRIMING_STATUS,
        "cache_inventory_root_sha256": cache_root,
        "complete_input_inventory_root_sha256": input_root,
        "request": {
            "path": str(prime_request_path.resolve()),
            "file_sha256": task9.file_sha256(prime_request_path),
            "request_root_sha256": prime_request["request_root_sha256"],
        },
        "cache_authority": {
            "path": str(authority_path.resolve()),
            "file_sha256": authority_file,
            "authority_root_sha256": authority_root,
        },
        "measurement_process": {
            "pid": 10,
            "launch_nonce_sha256": "e" * 64,
        },
        "primed_logical_bytes": 123,
        "sequential_read_and_hash_complete": True,
        "os_page_cache_controlled": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    priming = _rooted(core, "receipt_root_sha256")
    path = requests_root / "W1.prime.request.receipt.json"
    task9.atomic_write_json(path, priming)

    derived = task9.derive_cache_state(
        priming_receipt_path=path,
        priming_receipt_file_sha256=task9.file_sha256(path),
        expected_cache_inventory_root_sha256=cache_root,
        expected_cache_authority_path=authority_path,
        expected_cache_authority_file_sha256=authority_file,
        expected_cache_authority_root_sha256=authority_root,
        expected_complete_input_inventory_root_sha256=input_root,
        expected_validation_output_root=validation_root,
        current_launch_nonce_sha256="d" * 64,
    )
    assert derived["cache_state"] == task9.WARM_FILESYSTEM_STATE
    assert derived["priming_receipt_root_sha256"] == priming["receipt_root_sha256"]

    priming["cache_inventory_root_sha256"] = "f" * 64
    task9.atomic_write_json(path, priming)
    with pytest.raises(task9.Task9Rejected, match="task9_priming_receipt_root_invalid"):
        task9.derive_cache_state(
            priming_receipt_path=path,
            priming_receipt_file_sha256=task9.file_sha256(path),
            expected_cache_inventory_root_sha256=cache_root,
            expected_cache_authority_path=authority_path,
            expected_cache_authority_file_sha256=authority_file,
            expected_cache_authority_root_sha256=authority_root,
            expected_complete_input_inventory_root_sha256=input_root,
            expected_validation_output_root=validation_root,
            current_launch_nonce_sha256="d" * 64,
        )


def test_cache_state_rejects_relabel_and_prime_request_tamper(tmp_path: Path) -> None:
    warm = _trial("W1", task9.WARM_FILESYSTEM_STATE, wall=25.0)
    warm["derived_cache_state"] = task9.COLD_PROCESS_STATE
    with pytest.raises(task9.Task9Rejected, match="task9_cache_state_relabelled"):
        task9.validate_trial_receipt(warm)

    request_path = tmp_path / "prime.request.json"
    task9.atomic_write_json(
        request_path,
        _rooted({"schema": task9.PRIMING_REQUEST_SCHEMA}, "request_root_sha256"),
    )
    raw = bytearray(request_path.read_bytes())
    raw[0] = ord("[")
    request_path.write_bytes(bytes(raw))
    with pytest.raises(task9.Task9Rejected):
        task9._load_rooted_json(
            request_path,
            root_field="request_root_sha256",
            code="task9_test_prime_request",
        )


def test_semantic_projection_ignores_only_task8_volatile_raw_roots() -> None:
    exact_roles = sorted(task9.task8.TASK8_SEMANTIC_EXACT_ROLES)
    role_projection = {
        role: {"row_count": 1, "ordered_bytes_sha256": role[0] * 64}
        for role in task9.task7.ROLE_SUFFIXES
    }
    base = {
        "days": {
            task9.task8.DAY1: {"roles": role_projection},
            task9.task8.DAY2: {"roles": role_projection},
        },
        "semantic_parity": {
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
            "runtime_clock_closure_contract": task9.task8.task8_runtime_clock_closure_contract(),
            "order_semantic_comparison": {
                "row_count": 5,
                "ordered_semantic_projection_root_sha256": "1" * 64,
                "accelerated_raw_root_sha256": "2" * 64,
            },
            "selected_order_preimage_comparison": {
                "row_count": 5,
                "projection_root_sha256": "3" * 64,
                "selected_identity_root_sha256": "4" * 64,
                "accelerated_preimage_validation": {
                    "persisted_order_indexes_root_sha256": "5" * 64,
                },
            },
        },
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "tick_sparse_cache_raw_source_full_hash_count": 0,
        "tick_sparse_cache_sealed_reuse_count": 4,
    }

    left = task9.semantic_trial_projection(base)
    changed = json.loads(json.dumps(base))
    changed["semantic_parity"]["order_semantic_comparison"][
        "accelerated_raw_root_sha256"
    ] = "9" * 64
    right = task9.semantic_trial_projection(changed)

    assert left == right
    assert set(left["days"][task9.task8.DAY1]) == set(exact_roles)
    assert left["order"]["ordered_semantic_projection_root_sha256"] == "1" * 64

    changed["days"][task9.task8.DAY2]["roles"][exact_roles[0]][
        "ordered_bytes_sha256"
    ] = "8" * 64
    assert task9.semantic_trial_projection(changed) != left


def test_semantic_projection_is_rederived_from_raw_ledgers_after_reroot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    trial_root = tmp_path / "trial"
    trial_root.mkdir()
    raw_ledger = trial_root / "raw-ledger.jsonl"
    raw_ledger.write_bytes(b'{"candidate_id":"original"}\n')

    def raw_day_projection(root: Path, _day: str) -> dict:
        digest = task9.file_sha256(Path(root) / raw_ledger.name)
        return {
            role: {"row_count": 1, "ordered_bytes_sha256": digest}
            for role in task9.task7.ROLE_SUFFIXES
        }

    reference_projection = {
        day: raw_day_projection(trial_root, day)
        for day in (task9.task8.DAY1, task9.task8.DAY2)
    }

    def exact_parity(*, namespace, output_projection, reference_projection):
        del namespace
        if output_projection != reference_projection:
            raise task9.task8.Task8ProfileRejected("raw_ledger_mismatch")
        digest = next(iter(output_projection[task9.task8.DAY1].values()))[
            "ordered_bytes_sha256"
        ]
        return {
            "order_semantic_comparison": {
                "row_count": 1,
                "ordered_semantic_projection_root_sha256": digest,
            },
            "selected_order_preimage_comparison": {
                "row_count": 1,
                "projection_root_sha256": digest,
                "selected_identity_root_sha256": digest,
                "accelerated_preimage_validation": {
                    "persisted_order_indexes_root_sha256": digest,
                },
            },
            "runtime_clock_closure_contract": (
                task9.task8.task8_runtime_clock_closure_contract()
            ),
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
        }

    monkeypatch.setattr(task9.task8, "_day_projection", raw_day_projection)
    monkeypatch.setattr(task9.task8, "_task8_semantic_parity", exact_parity)
    monkeypatch.setattr(
        task9,
        "_authenticated_trial_tick_prewarm",
        lambda _root: {
            "prewarm_root_sha256": "8" * 64,
            "raw_source_full_hash_count": 0,
            "sealed_cache_reuse_count": 4,
        },
    )

    accepted = task9.rederive_semantic_projection_from_ledgers(
        trial_root,
        reference_projection=reference_projection,
    )
    assert accepted["semantic_projection_root_sha256"] == task9.stable_sha256(
        accepted["semantic_projection"]
    )

    # Updating a declared object root cannot hide a changed persisted ledger:
    # the independent derivation must compare raw rows to the fixed reference.
    raw_ledger.write_bytes(b'{"candidate_id":"tampered"}\n')
    forged = json.loads(json.dumps(accepted["semantic_projection"]))
    forged["days"][task9.task8.DAY1][
        sorted(task9.task8.TASK8_SEMANTIC_EXACT_ROLES)[0]
    ]["ordered_bytes_sha256"] = task9.file_sha256(raw_ledger)
    assert task9.stable_sha256(forged) != accepted[
        "semantic_projection_root_sha256"
    ]
    with pytest.raises(
        task9.Task9Rejected,
        match="task9_semantic_ledger_rederivation_failed:raw_ledger_mismatch",
    ):
        task9.rederive_semantic_projection_from_ledgers(
            trial_root,
            reference_projection=reference_projection,
        )


def test_v2_request_builders_reject_paths_outside_validation_namespace(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    (run / "requests").mkdir(parents=True)
    (run / "cache-authority").mkdir()
    (run / "trials").mkdir()
    outside = tmp_path / "outside-authority.json"
    task9.atomic_write_json(
        outside,
        _rooted({"schema": task9.CACHE_AUTHORITY_SCHEMA}, "authority_root_sha256"),
    )

    with pytest.raises(task9.Task9Rejected, match="task9_cache_authority_path_escape"):
        task9.make_priming_request(
            path=run / "requests" / "W1.prime.request.json",
            cache_authority_path=outside,
            launch_nonce="nonce",
        )
    with pytest.raises(task9.Task9Rejected, match="task9_cache_authority_path_escape"):
        task9.make_trial_request(
            path=run / "requests" / "C1.trial.request.json",
            trial_id="C1",
            output_dir=run / "trials" / "C1",
            cache_authority_path=outside,
            launch_nonce="nonce",
            priming_receipt_path=None,
        )


def test_cache_authority_rejects_external_typed_cache_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run = tmp_path / "run"
    authority_dir = run / "cache-authority"
    authority_dir.mkdir(parents=True)
    external_cache = tmp_path / "external-cache"
    external_cache.mkdir()
    cache_file = external_cache / "part.bin"
    cache_file.write_bytes(b"typed cache")
    inventory = task9.inventory_tree(external_cache)
    input_inventory = {"inventory_root_sha256": "e" * 64}
    tick_authority = {"prewarm_root_sha256": "f" * 64}
    monkeypatch.setattr(
        task9,
        "_cache_input_inventory",
        lambda _root: input_inventory,
    )
    monkeypatch.setattr(
        task9,
        "_task8_tick_prewarm_authority",
        lambda: (tick_authority, []),
    )
    cache_file.chmod(0o444)
    external_cache.chmod(0o555)
    core = {
        "schema": task9.CACHE_AUTHORITY_SCHEMA,
        "status": task9.CACHE_AUTHORITY_STATUS,
        "typed_cache": task9._compact_inventory(inventory),
        "input_inventory": input_inventory,
        "task8_tick_prewarm_authority": tick_authority,
        "read_only_filesystem_mode": True,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    manifest = authority_dir / "TASK9_TYPED_CACHE_AUTHORITY.json"
    task9.atomic_write_json(
        manifest,
        _rooted(core, "authority_root_sha256"),
    )
    try:
        with pytest.raises(
            task9.Task9Rejected,
            match="task9_cache_authority_typed_cache_escape",
        ):
            task9.verify_cache_authority(manifest)
    finally:
        external_cache.chmod(0o755)
        cache_file.chmod(0o644)


def _preliminary_scope_payload() -> dict:
    states = [
        task9.COLD_PROCESS_STATE,
        task9.COLD_PROCESS_STATE,
        task9.WARM_FILESYSTEM_STATE,
        task9.WARM_FILESYSTEM_STATE,
        task9.WARM_FILESYSTEM_STATE,
    ]
    return {
        "schema": task9.PRELIMINARY_SCHEMA,
        "status": task9.PRELIMINARY_STATUS,
        "controlling_task": "Replay-Acceleration Task 9",
        "scope": {
            "start_day": task9.task8.DAY1,
            "end_day": task9.task8.DAY2,
            "no_event_day": task9.task8.DAY1,
            "dense_day": task9.task8.DAY2,
            "arm_id": "S0R0",
        },
        "trials": [
            {"trial_id": trial_id, "derived_cache_state": state}
            for trial_id, state in zip(
                ("C1", "C2", "W1", "W2", "W3"),
                states,
                strict=True,
            )
        ],
        "exact_semantic_parity_all_trials": True,
        "cache_rebuild_or_write_count": 0,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "review_required": True,
        "acceptance_authorized": False,
    }


def test_preliminary_scope_rejects_rerooted_economics_authority_and_class() -> None:
    valid = _preliminary_scope_payload()
    assert task9.validate_preliminary_scope(valid) == valid

    for mutate, code in (
        (
            lambda payload: payload.__setitem__("nested", {"pnl": 1}),
            "task9_economic_field_exposed",
        ),
        (
            lambda payload: payload.__setitem__(
                "real_order_transmission_possible", True
            ),
            "task9_preliminary_scope_invalid",
        ),
        (
            lambda payload: payload["trials"][0].__setitem__(
                "derived_cache_state", task9.WARM_FILESYSTEM_STATE
            ),
            "task9_preliminary_trial_class_invalid",
        ),
    ):
        payload = json.loads(json.dumps(valid))
        mutate(payload)
        with pytest.raises(task9.Task9Rejected, match=code):
            task9.validate_preliminary_scope(payload)


def test_observation_rejects_outcome_fields_and_external_log_evidence(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "run"
    observations = output_root / "observations"
    logs = output_root / "logs"
    observations.mkdir(parents=True)
    logs.mkdir()
    trial = _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0)
    trial["receipt_root_sha256"] = "7" * 64
    external_time = tmp_path / "outside.time-lp.txt"
    external_time.write_text(
        "real 25.10\n"
        "user 17.50\n"
        "sys 2.50\n"
        "       1000  maximum resident set size\n"
        "          2  block input operations\n"
        "          3  block output operations\n"
    )
    parsed = task9.parse_macos_time_lp(external_time)
    core = {
        "schema": task9.OBSERVATION_SCHEMA,
        "status": "TASK9_PARENT_OBSERVED_TRIAL_COMPLETE",
        "trial_id": "C1",
        "trial_receipt_root_sha256": trial["receipt_root_sha256"],
        "parent_observed_wall_seconds": 25.2,
        "parent_peak_child_tree_rss_bytes": 1000,
        "raw_time_evidence": {
            "path": str(external_time.resolve()),
            "bytes": external_time.stat().st_size,
            "sha256": task9.file_sha256(external_time),
            "format": "macos_usr_bin_time_lp",
            "parsed_metrics": parsed,
        },
        "stdout": {
            "path": str(tmp_path / "outside.stdout"),
            "bytes": 0,
            "sha256": "0" * 64,
        },
        "stderr": {
            "path": str(tmp_path / "outside.stderr"),
            "bytes": 0,
            "sha256": "0" * 64,
        },
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    observation_path = observations / "C1.json"
    task9.atomic_write_json(
        observation_path,
        _rooted(core, "observation_root_sha256"),
    )
    with pytest.raises(
        task9.Task9Rejected,
        match="task9_observation_log_path_escape",
    ):
        task9._load_observation(observation_path, trial=trial)

    economic = dict(core)
    economic["nested"] = {"pnl": 1}
    task9.atomic_write_json(
        observation_path,
        _rooted(economic, "observation_root_sha256"),
    )
    with pytest.raises(task9.Task9Rejected, match="task9_economic_field_exposed"):
        task9._load_observation(observation_path)


def test_tick_input_paths_require_rooted_receipt_and_cache_containment(
    tmp_path: Path, monkeypatch
) -> None:
    cache_root = tmp_path / "tick-cache"
    cache_root.mkdir()
    identities = [f"{index:064x}" for index in range(1, 5)]
    for identity in identities:
        (cache_root / identity).mkdir()
        (cache_root / identity / "part.bin").write_bytes(identity.encode())
    core = {
        "schema": "gtos.replay_acceleration.sparse_tick_cache_prewarm.v1",
        "status": "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE",
        "cache_root": str(cache_root.resolve()),
        "entry_count": 4,
        "entries": [
            {"identity_root_sha256": identity} for identity in identities
        ],
    }
    receipt = {
        **core,
        "prewarm_root_sha256": task9.stable_sha256(core),
        "non_authoritative_filesystem_storage_receipt": {"ignored": True},
    }
    receipt_path = tmp_path / "prewarm.json"
    task9.atomic_write_json(receipt_path, receipt)
    monkeypatch.setattr(
        task9.task8.replay,
        "sparse_tick_source_attestations",
        lambda _receipt: {},
    )

    authority, paths = task9._task8_tick_prewarm_authority(
        receipt_path=receipt_path,
        cache_root=cache_root,
    )
    assert authority["prewarm_root_sha256"] == receipt["prewarm_root_sha256"]
    assert paths == [cache_root.resolve() / identity for identity in identities]

    receipt_link = tmp_path / "prewarm-link.json"
    receipt_link.symlink_to(receipt_path)
    with pytest.raises(
        task9.Task9Rejected,
        match="task9_task8_tick_prewarm_invalid",
    ):
        task9._task8_tick_prewarm_authority(
            receipt_path=receipt_link,
            cache_root=cache_root,
        )

    receipt["worker_count"] = 99
    task9.atomic_write_json(receipt_path, receipt)
    with pytest.raises(task9.Task9Rejected, match="task9_task8_tick_prewarm_root_invalid"):
        task9._task8_tick_prewarm_authority(
            receipt_path=receipt_path,
            cache_root=cache_root,
        )

    receipt.pop("worker_count")
    receipt["entries"][0]["identity_root_sha256"] = "../outside"
    task9.atomic_write_json(receipt_path, receipt)
    with pytest.raises(task9.Task9Rejected, match="task9_task8_tick_identity_invalid"):
        task9._task8_tick_prewarm_authority(
            receipt_path=receipt_path,
            cache_root=cache_root,
        )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("cold_partition_count", 1, "task9_trial_cache_rebuilt"),
        ("bytes_written", 1, "task9_trial_cache_written"),
        ("post_inventory_root_sha256", "c" * 64, "task9_trial_cache_drift"),
    ],
)
def test_trial_acceptance_fails_closed_on_cache_mutation(
    field: str,
    value: object,
    code: str,
) -> None:
    trial = _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0)
    trial["cache"][field] = value

    with pytest.raises(task9.Task9Rejected, match=code):
        task9.validate_trial_receipt(trial)


def test_trial_recomputes_semantic_projection_root_and_structure() -> None:
    trial = _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0)
    trial["semantic_projection_root_sha256"] = "0" * 64
    with pytest.raises(task9.Task9Rejected, match="task9_semantic_projection_root_invalid"):
        task9.validate_trial_receipt(trial)

    trial = _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0)
    del trial["semantic_projection"]["days"][task9.task8.DAY2][
        sorted(task9.task8.TASK8_SEMANTIC_EXACT_ROLES)[0]
    ]
    trial["semantic_projection_root_sha256"] = task9.stable_sha256(
        trial["semantic_projection"]
    )
    with pytest.raises(task9.Task9Rejected, match="task9_semantic_projection_structure_invalid"):
        task9.validate_trial_receipt(trial)


def test_trial_evidence_inventory_detects_same_size_tamper_and_delete(
    tmp_path: Path,
) -> None:
    root = tmp_path / "trial"
    root.mkdir()
    evidence = root / "result.json"
    evidence.write_bytes(b"one")
    declared = task9.inventory_tree(root)
    assert task9.validate_inventory_binding(root, declared) == declared

    evidence.write_bytes(b"two")
    with pytest.raises(task9.Task9Rejected, match="task9_evidence_inventory_drift"):
        task9.validate_inventory_binding(root, declared)
    evidence.unlink()
    with pytest.raises(task9.Task9Rejected, match="task9_evidence_inventory_drift"):
        task9.validate_inventory_binding(root, declared)


def test_stage_profile_is_enabled_ordered_and_complete() -> None:
    profile = _stage_profile()
    assert task9.validate_stage_profile(profile)["enabled"] is True

    profile["enabled"] = False
    with pytest.raises(task9.Task9Rejected, match="task9_stage_profile_scope_invalid"):
        task9.validate_stage_profile(profile)

    profile = _stage_profile()
    profile["stages"][0]["entered_count"] = 0
    with pytest.raises(task9.Task9Rejected, match="task9_stage_profile_required_stage_missing"):
        task9.validate_stage_profile(profile)

    profile = _stage_profile()
    profile["stage_order"] = list(reversed(profile["stage_order"]))
    with pytest.raises(task9.Task9Rejected, match="task9_stage_profile_order_invalid"):
        task9.validate_stage_profile(profile)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda profile: profile["call_counters"].__setitem__(
            "schedule_window", -1
        ),
        lambda profile: profile["call_counters"].pop("schedule_window"),
        lambda profile: profile["output_counters"].__setitem__(
            "orders", {"rows": 1, "bytes": -1}
        ),
        lambda profile: profile["resource_bounds"]["last"].__setitem__(
            "block_input_operations", -1
        ),
    ],
)
def test_stage_profile_rejects_malformed_counters_and_resource_bounds(
    mutate,
) -> None:
    profile = _stage_profile()
    mutate(profile)
    with pytest.raises(
        task9.Task9Rejected,
        match="task9_stage_profile_(counter|resource)_invalid",
    ):
        task9.validate_stage_profile(profile)


def test_trial_reconciles_verification_stage_with_measured_parity_time() -> None:
    trial = _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0)
    verification = next(
        row for row in trial["stage_profile"]["stages"]
        if row["name"] == "verification"
    )
    verification["wall_ns"] = 9_000_000_000
    verification["self_wall_ns"] = 9_000_000_000
    with pytest.raises(
        task9.Task9Rejected,
        match="task9_trial_verification_stage_timing_mismatch",
    ):
        task9.validate_trial_receipt(trial)


def test_macos_time_lp_is_parsed_and_reconciled(tmp_path: Path) -> None:
    path = tmp_path / "time.txt"
    path.write_text(
        "real 25.10\n"
        "user 17.50\n"
        "sys 2.50\n"
        "       1000  maximum resident set size\n"
        "          2  block input operations\n"
        "          3  block output operations\n"
    )
    metrics = task9.parse_macos_time_lp(path)
    assert metrics == {
        "real_seconds": 25.1,
        "user_seconds": 17.5,
        "system_seconds": 2.5,
        "maximum_resident_set_size_bytes": 1000,
        "block_input_operations": 2,
        "block_output_operations": 3,
    }
    trial = _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0)
    observation = {
        "parent_observed_wall_seconds": 25.2,
        "parent_peak_child_tree_rss_bytes": 1000,
    }
    assert task9.validate_independent_time_metrics(metrics, trial, observation)

    metrics["real_seconds"] = 40.0
    with pytest.raises(task9.Task9Rejected, match="task9_independent_time_wall_mismatch"):
        task9.validate_independent_time_metrics(metrics, trial, observation)

    metrics["real_seconds"] = 25.1
    metrics["block_input_operations"] = 200
    with pytest.raises(task9.Task9Rejected, match="task9_independent_time_io_mismatch"):
        task9.validate_independent_time_metrics(metrics, trial, observation)


def test_process_group_cleanup_checks_group_after_leader_exit(monkeypatch) -> None:
    class CompletedLeader:
        pid = 43210

        @staticmethod
        def poll() -> int:
            return 0

        @staticmethod
        def wait(timeout=None) -> int:
            return 0

    states = iter([True, True, False])
    signals: list[tuple[int, int]] = []
    monkeypatch.setattr(task9, "_process_group_exists", lambda _pgid: next(states))
    monkeypatch.setattr(os, "killpg", lambda pgid, sig: signals.append((pgid, sig)))
    monkeypatch.setattr(task9.time, "sleep", lambda _seconds: None)

    task9._terminate_process_group(CompletedLeader())

    assert signals == [(43210, task9.signal.SIGTERM)]


def test_aggregate_requires_two_cold_three_warm_and_projects_per_trial() -> None:
    trials = [
        _trial("C1", task9.COLD_PROCESS_STATE, wall=25.0),
        _trial("C2", task9.COLD_PROCESS_STATE, wall=27.0),
        _trial("W1", task9.WARM_FILESYSTEM_STATE, wall=23.0),
        _trial("W2", task9.WARM_FILESYSTEM_STATE, wall=24.0),
        _trial("W3", task9.WARM_FILESYSTEM_STATE, wall=22.0),
    ]
    summary = task9.aggregate_trials(trials)

    assert summary["trial_counts"] == {
        task9.COLD_PROCESS_STATE: 2,
        task9.WARM_FILESYSTEM_STATE: 3,
    }
    assert summary["classes"][task9.COLD_PROCESS_STATE]["wall_seconds"] == {
        "median": 26.0,
        "worst": 27.0,
    }
    one_month = summary["projections"]["one_month"]
    assert one_month["workload_counts"] == {"dense_days": 21, "no_event_days": 1}
    assert one_month["warm"]["four_arm_serial_seconds"]["median"] == pytest.approx(
        4 * one_month["warm"]["one_arm_seconds"]["median"]
    )
    assert summary["four_arm_projection_kind"] == (
        "standardized_equal_cost_serial_4x_s0r0_extrapolation"
    )
    assert "conservative" not in one_month["scenario"]
    # The residual is scaled per observed day; it is not incorrectly paid once.
    expected = (25.0 - 2.0 - 20.0) / 2.0 * 22 + 2.0 + 20.0 * 21
    assert one_month["cold"]["one_arm_seconds"]["median"] > expected

    with pytest.raises(task9.Task9Rejected, match="task9_trial_class_counts_invalid"):
        task9.aggregate_trials(trials[:-1])


def test_targets_use_warm_total_not_economic_only_or_cold_trial() -> None:
    trials = [
        _trial("C1", task9.COLD_PROCESS_STATE, wall=302.0, no_event=100.0, dense=200.0),
        _trial("C2", task9.COLD_PROCESS_STATE, wall=302.0, no_event=100.0, dense=200.0),
        _trial("W1", task9.WARM_FILESYSTEM_STATE, wall=25.0, no_event=2.0, dense=20.0),
        _trial("W2", task9.WARM_FILESYSTEM_STATE, wall=26.0, no_event=3.0, dense=20.0),
        _trial("W3", task9.WARM_FILESYSTEM_STATE, wall=27.0, no_event=4.0, dense=20.0),
    ]
    for trial in trials:
        trial["measurement"]["no_event_economic_hot_path_seconds"] = 0.5
        trial["measurement"]["dense_economic_hot_path_seconds"] = 10.0
    targets = task9._task9_targets(trials)
    assert targets["no_event_total_worst_observed_seconds"] == 5.5
    assert targets["dense_total_worst_observed_seconds"] == 21.5
    assert targets["no_event_total_target_met"] is False
    assert targets["diagnostic_direct_day_total_including_proof_finalization"] == {
        "no_event_worst_seconds": 4.0,
        "dense_worst_seconds": 20.0,
        "acceptance_metric": False,
    }
    assert targets["diagnostic_economic_hot_path"]["acceptance_metric"] is False


def test_v2_final_receipt_seals_whole_namespace_without_exclusions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_root = tmp_path / "TASK9_SYNTHETIC"
    output_root.mkdir()
    evidence = output_root / "evidence.bin"
    evidence.write_bytes(b"semantic evidence")
    preliminary_core = {
        "schema": task9.PRELIMINARY_SCHEMA,
        "status": task9.PRELIMINARY_STATUS,
        "trials": [],
        "acceptance_authorized": False,
    }
    preliminary = _rooted(preliminary_core, "receipt_root_sha256")
    preliminary_path = output_root / task9.PRELIMINARY_RECEIPT_NAME
    task9.atomic_write_json(preliminary_path, preliminary)
    verified = {"aggregate": {"verified": True}, "targets": {"verified": True}}
    semantic_reference = {
        "reference_root": "/fixed/reference",
        "binding_root_sha256": "a" * 64,
    }
    monkeypatch.setattr(task9, "_verify_v2_preliminary", lambda *_args: verified)
    monkeypatch.setattr(
        task9,
        "_semantic_reference_binding",
        lambda: semantic_reference,
    )

    try:
        final_path = task9.finalize_task9_v2_namespace(
            output_root,
            preliminary_path,
        )
        assert final_path == output_root.with_name(
            output_root.name + task9.FINAL_VALIDATION_RECEIPT_SUFFIX
        )
        final = task9.verify_task9_v2_final_receipt(final_path)
        assert final["content_inventory_exclusions"] == []
        assert {row["path"] for row in final["complete_namespace_inventory"]["files"]} == {
            "evidence.bin",
            task9.PRELIMINARY_RECEIPT_NAME,
        }
        assert output_root.stat().st_mode & stat.S_IWUSR == 0

        wrong_path = tmp_path / "copied-final.json"
        wrong_path.write_bytes(final_path.read_bytes())
        with pytest.raises(
            task9.Task9Rejected,
            match="task9_v2_final_receipt_identity_invalid",
        ):
            task9.verify_task9_v2_final_receipt(wrong_path)

        evidence.chmod(evidence.stat().st_mode | stat.S_IWUSR)
        evidence.write_bytes(b"tampered evidence")
        with pytest.raises(
            task9.Task9Rejected,
            match="task9_v2_final_namespace_inventory_drift",
        ):
            task9.verify_task9_v2_final_receipt(final_path)
    finally:
        for path in sorted(output_root.rglob("*"), reverse=True):
            path.chmod(path.stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)
        output_root.chmod(output_root.stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)


def test_outcome_blind_receipt_rejects_nested_economics() -> None:
    task9.assert_outcome_blind({"measurement": {"wall_seconds": 1.0}})

    with pytest.raises(task9.Task9Rejected, match="task9_economic_field_exposed"):
        task9.assert_outcome_blind({"nested": {"pnl": 1.0}})

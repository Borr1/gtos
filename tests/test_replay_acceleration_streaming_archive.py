from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import subprocess
from collections import namedtuple
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _isolated_clock(module, sleep):
    """Replace only this archive module's clock while preserving elapsed timing."""

    return SimpleNamespace(sleep=sleep, perf_counter=module.time.perf_counter)


def _write_rows(
    path: Path,
    role: str,
    *,
    start_day: str = "2026-01-01",
    end_day: str = "2026-01-07",
    trading_day: str | None = None,
    marker: str | None = None,
) -> bytes:
    row_type = {
        "decision": "asof_decision",
        "scorecard": "scheduler_scorecard",
        "missed": "missed_opportunity",
    }[role]
    day = trading_day or start_day
    chunk_id = f"profile:development:{start_day}:{end_day}"
    payload = b"".join(
        _canonical(
            {
                "row_type": row_type,
                "index": index,
                "canonical_replay_candidate_instance_key": (
                    f"{marker or role}-candidate-{index}"
                ),
                "trading_day": day,
                "profile": "profile",
                "broad_replay_profile": "profile",
                "split": "development",
                "chunk_id": chunk_id,
                "chunk_start_day": start_day,
                "chunk_end_day": end_day,
                "chunk_day_count": (
                    date.fromisoformat(end_day) - date.fromisoformat(start_day)
                ).days
                + 1,
                "row_provenance_schema": (
                    "broad_live_as_if_replay_row_provenance_v1"
                ),
            }
        )
        + b"\n"
        for index in range(4)
    )
    path.write_bytes(payload)
    return payload


def _seal(
    archive,
    *,
    start_day: str,
    end_day: str,
    current_summary_contract_root_sha256: str,
    **seal_kwargs: object,
):
    del current_summary_contract_root_sha256
    partial_path = archive.root.parent / (
        f"{archive.output_prefix}_{start_day}_{end_day}_PRE_ARCHIVE.json"
    )
    identity_core = {
        "schema": "synthetic.attempt5_execution_identity.v1",
        "output_prefix": archive.output_prefix,
    }
    identity = {
        **identity_core,
        "identity_root_sha256": hashlib.sha256(
            _canonical(identity_core)
        ).hexdigest(),
    }
    shared_payload = {
        "schema": "gtos.final_moonshot.broad_replay.shared_execution_contract.v1",
        "code_authority": [
            {"path": "synthetic_runner.py", "sha256": "6" * 64}
        ],
        "config_file_hashes": {"synthetic.yaml": "7" * 64},
    }
    shared_digest = hashlib.sha256(_canonical(shared_payload)).hexdigest()
    shared = {
        **shared_payload,
        "valid": True,
        "status": "shared_execution_contract_bound",
        "shared_execution_contract_digest_sha256": shared_digest,
    }
    arm = {"arm_id": "S0R0", "arm_fingerprint_sha256": "3" * 64}
    partial_path.write_bytes(
        _canonical(
            {
                "schema": "synthetic.pre_archive_partial.v1",
                "output_prefix": archive.output_prefix,
                "last_completed_end_day": end_day,
                "attempt5_execution_identity": identity,
                "shared_execution_contract": shared,
                "b7_5_selection_sizing_factorial_arm_binding": arm,
                "b7_5_contract_binding": {
                    "actual_source_plan_digests_sha256": ["2" * 64],
                    "actual_shared_execution_contract_digest_sha256": (
                        shared_digest
                    ),
                    "selection_sizing_factorial_arm_binding": arm,
                },
            }
        )
        + b"\n"
    )
    return archive.seal_and_reclaim(
        start_day=start_day,
        end_day=end_day,
        pre_archive_partial_summary_path=partial_path,
        checkpoint_authority={
            "schema": "gtos.replay_acceleration.streaming_checkpoint_authority.v1",
            "output_prefix": archive.output_prefix,
            "run_identity_root_sha256": identity["identity_root_sha256"],
            "source_plan_digest_sha256": "2" * 64,
            "arm_fingerprint_sha256": "3" * 64,
            "shared_execution_contract_sha256": shared_digest,
            "accelerated_code_config_authority_root_sha256": hashlib.sha256(
                _canonical(
                    {
                        "code_authority": shared["code_authority"],
                        "config_file_hashes": shared["config_file_hashes"],
                    }
                )
            ).hexdigest(),
        },
        **seal_kwargs,
    )


def _sealed_archive(
    tmp_path: Path,
    *,
    start_day: str = "2026-01-01",
    end_day: str = "2026-01-07",
):
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role, start_day=start_day, end_day=end_day)
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    shard = _seal(
        archive,
        start_day=start_day,
        end_day=end_day,
        current_summary_contract_root_sha256="a" * 64,
    )
    return archive, shard


def test_streaming_archive_verifies_before_reclaim_and_reconstructs_exact_bytes(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    shard = _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    assert shard["verified_before_reclaim"] is True
    assert shard["raw_derivatives_reclaimed"] is True
    assert all(path.stat().st_size == 0 for path in outputs.values())

    campaign = verify_campaign(archive.campaign_manifest_path)
    campaign_raw = archive.campaign_manifest_path.read_bytes()
    campaign_manifest = json.loads(campaign_raw)
    assert campaign["valid"] is True
    assert campaign["shard_count"] == 1
    assert campaign["campaign_manifest_path"] == str(
        archive.campaign_manifest_path
    )
    assert campaign["campaign_manifest_sha256"] == hashlib.sha256(
        campaign_raw
    ).hexdigest()
    assert campaign["campaign_manifest_root_sha256"] == campaign_manifest[
        "campaign_manifest_root_sha256"
    ]
    for role, original in expected.items():
        record = next(item for item in shard["surfaces"] if item["role"] == role)
        reconstructed = subprocess.check_output(
            ["zstd", "-q", "-d", "-c", record["compressed_path"]]
        )
        assert reconstructed == original


def test_streaming_archive_admits_measured_compressed_bytes_not_raw_total(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role, marker="x" * (64 * 1024))
        outputs[role] = path
    raw_total = sum(len(value) for value in expected.values())
    hard_floor = 28 * 1024 * 1024 * 1024
    available_compression_headroom = 64 * 1024
    assert raw_total > available_compression_headroom
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(
        module,
        "ARCHIVE_COMPRESSION_CONTROL_RESERVE_BYTES",
        1024,
        raising=False,
    )
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: usage(
            hard_floor * 2,
            hard_floor,
            hard_floor + available_compression_headroom,
        ),
    )
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=hard_floor,
    )

    shard = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )

    assert shard["verified_before_reclaim"] is True
    assert all(path.stat().st_size == 0 for path in outputs.values())
    assert verify_campaign(archive.campaign_manifest_path)["valid"] is True


def test_streaming_archive_seal_settles_before_publishing_segment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role, marker="x" * 4096)
        outputs[role] = path
    hard_floor = 28 * 1024 * 1024 * 1024
    recovered_free = hard_floor + 128 * 1024
    free_samples = [hard_floor - 1, recovered_free]
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(
        module,
        "ARCHIVE_COMPRESSION_CONTROL_RESERVE_BYTES",
        1024,
        raising=False,
    )

    def disk_usage(_path: Path):
        free = free_samples.pop(0) if free_samples else recovered_free
        return usage(hard_floor * 2, hard_floor, free)

    monkeypatch.setattr(module.shutil, "disk_usage", disk_usage)
    sleeps: list[float] = []
    monkeypatch.setattr(module, "time", _isolated_clock(module, sleeps.append))
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=hard_floor,
    )
    callbacks: list[bool] = []

    def reclaim() -> None:
        callbacks.append(True)
        assert not (archive.root / "shards").exists()

    shard = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
        settle_timeout_seconds=10,
        settle_poll_seconds=5,
        on_advisory_miss=reclaim,
    )

    assert shard["verified_before_reclaim"] is True
    assert callbacks == [True]
    assert sleeps == [5]


def test_streaming_archive_seal_settle_timeout_is_non_mutating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    hard_floor = 28 * 1024 * 1024 * 1024
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(
        module,
        "ARCHIVE_COMPRESSION_CONTROL_RESERVE_BYTES",
        1024,
        raising=False,
    )
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: usage(hard_floor * 2, hard_floor, hard_floor - 1),
    )
    monkeypatch.setattr(
        module,
        "time",
        _isolated_clock(module, lambda _seconds: None),
    )
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=hard_floor,
    )

    with pytest.raises(
        module.ArchiveRejected,
        match="archive_compression_would_threaten_hard_floor",
    ):
        _seal(
            archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
            settle_timeout_seconds=10,
            settle_poll_seconds=5,
            on_advisory_miss=lambda: None,
        )

    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert not (archive.root / "shards").exists()
    assert not archive.campaign_manifest_path.exists()


def test_streaming_archive_rejects_compression_plan_drift_before_reclaim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    original_plan = module.planned_zstd_contract

    def drifted_plan(zstd: str, path: Path) -> dict[str, object]:
        contract = original_plan(zstd, path)
        if path == outputs["scorecard"]:
            contract["compressed_sha256"] = "0" * 64
        return contract

    monkeypatch.setattr(module, "planned_zstd_contract", drifted_plan)
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )

    with pytest.raises(
        module.ArchiveRejected,
        match="archive_compression_plan_mismatch",
    ):
        _seal(
            archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )

    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert not archive.campaign_manifest_path.exists()
    shards_root = archive.root / "shards"
    assert not shards_root.exists() or not list(shards_root.iterdir())

    monkeypatch.setattr(module, "planned_zstd_contract", original_plan)
    shard = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    assert shard["verified_before_reclaim"] is True


def test_compression_plan_discards_unbounded_stderr_and_reaps_on_read_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    raw_path = tmp_path / "decision.jsonl"
    raw_path.write_bytes(b'{"row":1}\n')
    calls: list[object] = []

    class SuccessfulProcess:
        def __init__(self) -> None:
            self.stdout = io.BytesIO(b"compressed")
            self.returncode: int | None = None

        def wait(self) -> int:
            calls.append("wait-success")
            self.returncode = 0
            return 0

        def kill(self) -> None:
            calls.append("kill-success")

    def successful_popen(*_args, **kwargs):
        calls.append(kwargs["stderr"])
        return SuccessfulProcess()

    monkeypatch.setattr(module.subprocess, "Popen", successful_popen)
    assert module.planned_zstd_contract("zstd", raw_path) == {
        "compressed_bytes": len(b"compressed"),
        "compressed_sha256": hashlib.sha256(b"compressed").hexdigest(),
    }
    assert calls == [subprocess.DEVNULL, "wait-success"]

    class ExplodingStream:
        def read(self, _size: int) -> bytes:
            raise OSError("simulated child stream failure")

        def close(self) -> None:
            calls.append("close-error-stdout")

    class FailingProcess:
        def __init__(self) -> None:
            self.stdout = ExplodingStream()
            self.returncode: int | None = None

        def wait(self) -> int:
            calls.append("wait-error")
            self.returncode = -9
            return -9

        def kill(self) -> None:
            calls.append("kill-error")

    monkeypatch.setattr(
        module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: FailingProcess(),
    )
    with pytest.raises(
        module.ArchiveRejected,
        match="archive_compression_plan_failed",
    ):
        module.planned_zstd_contract("zstd", raw_path)
    assert calls[-3:] == ["kill-error", "wait-error", "close-error-stdout"]


@pytest.mark.parametrize(
    ("failure_kind", "expected_code"),
    (
        ("compression", "archive_compression_failed"),
        ("verifier", "archive_independent_verifier_failed"),
    ),
)
def test_streaming_archive_external_failure_cleans_and_retries_same_day(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
    expected_code: str,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    real_run = module.subprocess.run
    injected = False

    def fail_once(args, *run_args, **run_kwargs):
        nonlocal injected
        is_verifier = "verify-shard" in args
        is_compression = (
            args[0] == archive.zstd and "-1" in args and "-c" in args
        )
        if not injected and (
            (failure_kind == "verifier" and is_verifier)
            or (failure_kind == "compression" and is_compression)
        ):
            injected = True
            return subprocess.CompletedProcess(args, 1)
        return real_run(args, *run_args, **run_kwargs)

    monkeypatch.setattr(module.subprocess, "run", fail_once)
    with pytest.raises(module.ArchiveRejected, match=expected_code):
        _seal(
            archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )

    assert injected is True
    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert not archive.campaign_manifest_path.exists()
    shards_root = archive.root / "shards"
    assert not shards_root.exists() or not list(shards_root.iterdir())

    monkeypatch.setattr(module.subprocess, "run", real_run)
    shard = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    assert shard["verified_before_reclaim"] is True


@pytest.mark.parametrize(
    ("artifact", "error_code"),
    (
        ("shard", "archive_shard_manifest_invalid"),
        ("campaign", "archive_campaign_manifest_invalid"),
    ),
)
def test_archive_verifier_rejects_unknown_economic_fields(
    tmp_path: Path,
    artifact: str,
    error_code: str,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
        verify_shard,
    )

    archive, shard = _sealed_archive(tmp_path)
    if artifact == "shard":
        path = Path(shard["manifest_path"])
        root_field = "manifest_root_sha256"
        verify = verify_shard
    else:
        path = archive.campaign_manifest_path
        root_field = "campaign_manifest_root_sha256"
        verify = verify_campaign
    value = json.loads(path.read_bytes())
    value["ending_equity"] = 1
    value.pop(root_field)
    value[root_field] = hashlib.sha256(_canonical(value)).hexdigest()
    path.write_bytes(_canonical(value) + b"\n")

    with pytest.raises(ValueError, match=error_code):
        verify(path)


def test_archive_verifier_rejects_bool_as_int_blindness_declaration(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_shard,
    )

    _archive, shard = _sealed_archive(tmp_path)
    path = Path(shard["manifest_path"])
    manifest = json.loads(path.read_bytes())
    manifest["economic_values_exposed"] = 0
    manifest.pop("manifest_root_sha256")
    manifest["manifest_root_sha256"] = hashlib.sha256(
        _canonical(manifest)
    ).hexdigest()
    path.write_bytes(_canonical(manifest) + b"\n")

    with pytest.raises(ValueError, match="archive_shard_manifest_invalid"):
        verify_shard(path)


def test_archive_row_partition_requires_producer_structural_fields() -> None:
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        _validate_partition_row,
    )

    row = {
        "row_type": "asof_decision",
        "trading_day": "2026-01-08",
        "profile": "profile",
        "broad_replay_profile": "profile",
        "split": "development",
        "chunk_id": "profile:development:2026-01-01:2026-01-07",
        "chunk_start_day": "2026-01-01",
        "chunk_end_day": "2026-01-07",
        "chunk_day_count": 7,
        "row_provenance_schema": "broad_live_as_if_replay_row_provenance_v1",
    }

    with pytest.raises(ValueError, match="archive_row_partition_mismatch"):
        _validate_partition_row(
            _canonical(row) + b"\n",
            role="decision",
            start_day=date(2026, 1, 1),
            end_day=date(2026, 1, 7),
        )


def test_archive_campaign_rejects_empty_shard_inventory(tmp_path: Path) -> None:
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    archive, _shard = _sealed_archive(tmp_path)
    campaign = json.loads(archive.campaign_manifest_path.read_bytes())
    campaign["shards"] = []
    campaign.pop("campaign_manifest_root_sha256")
    campaign["campaign_manifest_root_sha256"] = hashlib.sha256(
        _canonical(campaign)
    ).hexdigest()
    archive.campaign_manifest_path.write_bytes(_canonical(campaign) + b"\n")

    with pytest.raises(ValueError, match="archive_campaign_shards_invalid"):
        verify_campaign(archive.campaign_manifest_path)


def test_streaming_archive_rejects_opaque_checkpoint_root(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        ArchiveRejected,
        StreamingProofArchive,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )

    with pytest.raises(
        ArchiveRejected,
        match="archive_checkpoint_preimage_required",
    ):
        archive.seal_and_reclaim(
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )


def test_streaming_archive_persists_and_verifies_checkpoint_chain(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(
            path,
            role,
            start_day="2026-01-01",
            end_day="2026-01-01",
            marker=f"{role}-day-1",
        )
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    first = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-01",
        current_summary_contract_root_sha256="a" * 64,
    )
    for role, path in outputs.items():
        _write_rows(
            path,
            role,
            start_day="2026-01-02",
            end_day="2026-01-02",
            marker=f"{role}-day-2",
        )
    second = _seal(
        archive,
        start_day="2026-01-02",
        end_day="2026-01-02",
        current_summary_contract_root_sha256="b" * 64,
    )

    campaign = json.loads(archive.campaign_manifest_path.read_bytes())
    expected_identity_root = hashlib.sha256(
        _canonical(
            {
                "schema": "synthetic.attempt5_execution_identity.v1",
                "output_prefix": archive.output_prefix,
            }
        )
    ).hexdigest()
    assert campaign["checkpoint_authority"]["run_identity_root_sha256"] == (
        expected_identity_root
    )
    assert campaign["checkpoint_chain_genesis_root_sha256"] == first[
        "prior_checkpoint_chain_root_sha256"
    ]
    assert first["checkpoint_chain_root_sha256"] == second[
        "prior_checkpoint_chain_root_sha256"
    ]
    assert campaign["terminal_checkpoint_chain_root_sha256"] == second[
        "checkpoint_chain_root_sha256"
    ]
    for shard in campaign["shards"]:
        preimage_path = Path(shard["checkpoint_preimage_path"])
        preimage = json.loads(preimage_path.read_bytes())
        snapshot = preimage["pre_archive_partial_summary"]
        assert preimage["checkpoint_root_sha256"] == shard[
            "checkpoint_root_sha256"
        ]
        assert Path(snapshot["snapshot_path"]).is_file()
        assert snapshot["sha256"] == hashlib.sha256(
            Path(snapshot["snapshot_path"]).read_bytes()
        ).hexdigest()
    report = verify_campaign(archive.campaign_manifest_path)
    assert report["terminal_checkpoint_chain_root_sha256"] == second[
        "checkpoint_chain_root_sha256"
    ]
    assert report["checkpoint_chain_set_root_sha256"] == campaign[
        "checkpoint_chain_set_root_sha256"
    ]


@pytest.mark.parametrize(
    ("alias_kind", "error_code"),
    (
        ("symlink", "archive_symlink_component_forbidden"),
        ("hardlink", "archive_hardlink_forbidden"),
    ),
)
def test_campaign_rejects_compressed_surface_aliases(
    tmp_path: Path,
    alias_kind: str,
    error_code: str,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    shard = _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    compressed_path = Path(shard["surfaces"][0]["compressed_path"])
    preserved_path = compressed_path.with_name("preserved-decision.jsonl.zst")
    compressed_path.replace(preserved_path)
    if alias_kind == "symlink":
        compressed_path.symlink_to(preserved_path.name)
    else:
        os.link(preserved_path, compressed_path)

    with pytest.raises(ValueError, match=error_code):
        verify_campaign(archive.campaign_manifest_path)


def test_campaign_rejects_compressed_surface_outside_archive_root(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    campaign = json.loads(archive.campaign_manifest_path.read_bytes())
    manifest_path = Path(campaign["shards"][0]["manifest_path"])
    receipt_path = Path(campaign["shards"][0]["receipt_path"])
    manifest = json.loads(manifest_path.read_bytes())
    escaped = tmp_path / "escaped-decision.jsonl.zst"
    escaped.write_bytes(Path(manifest["surfaces"][0]["compressed_path"]).read_bytes())
    manifest["surfaces"][0]["compressed_path"] = str(escaped)
    manifest.pop("manifest_root_sha256")
    manifest["manifest_root_sha256"] = hashlib.sha256(
        _canonical(manifest)
    ).hexdigest()
    manifest_path.write_bytes(_canonical(manifest) + b"\n")

    receipt = json.loads(receipt_path.read_bytes())
    receipt["manifest_root_sha256"] = manifest["manifest_root_sha256"]
    receipt.pop("receipt_root_sha256")
    receipt["receipt_root_sha256"] = hashlib.sha256(
        _canonical(receipt)
    ).hexdigest()
    receipt_path.write_bytes(_canonical(receipt) + b"\n")
    campaign["shards"][0]["manifest_root_sha256"] = manifest[
        "manifest_root_sha256"
    ]
    campaign["shards"][0]["receipt_root_sha256"] = receipt[
        "receipt_root_sha256"
    ]
    campaign.pop("campaign_manifest_root_sha256")
    campaign["campaign_manifest_root_sha256"] = hashlib.sha256(
        _canonical(campaign)
    ).hexdigest()
    archive.campaign_manifest_path.write_bytes(_canonical(campaign) + b"\n")

    with pytest.raises(ValueError, match="archive_surface_topology_invalid"):
        verify_campaign(archive.campaign_manifest_path)


def test_campaign_role_iteration_does_not_reopen_after_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra import (
        replay_acceleration_streaming_archive_verifier as verifier,
    )

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    shard = _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    target = next(
        Path(item["compressed_path"])
        for item in shard["surfaces"]
        if item["role"] == "missed"
    )
    replacement = target.with_name("missed-replacement.jsonl.zst")
    rogue_raw = _canonical(
        {
            "row_type": "rogue",
            "canonical_replay_candidate_instance_key": "candidate-rogue",
        }
    ) + b"\n"
    with replacement.open("xb") as handle:
        subprocess.run(
            ["zstd", "-q", "-1", "-T1", "-c"],
            input=rogue_raw,
            stdout=handle,
            check=True,
        )
    real_verify_campaign = verifier.verify_campaign

    def verify_then_replace(path: Path) -> dict[str, object]:
        report = real_verify_campaign(path)
        replacement.replace(target)
        return report

    monkeypatch.setattr(verifier, "verify_campaign", verify_then_replace)
    try:
        observed = b"".join(
            verifier.iter_campaign_role_lines(
                archive.campaign_manifest_path,
                "missed",
            )
        )
    except ValueError as exc:
        assert str(exc) == "archive_evidence_path_changed"
    else:
        assert observed == expected["missed"]


def test_streaming_archive_does_not_publish_campaign_before_all_tombstones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    real_ftruncate = module.os.ftruncate
    scorecard_inode = outputs["scorecard"].stat().st_ino
    failed = False

    def fail_second_tombstone(descriptor: int, length: int) -> None:
        nonlocal failed
        if (
            not failed
            and length == 0
            and module.os.fstat(descriptor).st_ino == scorecard_inode
        ):
            failed = True
            recovery_path = (
                archive.root
                / "shards"
                / "001_2026-01-01_2026-01-07"
                / "RECLAIM_RECOVERY_JOURNAL.json"
            )
            recovery = json.loads(recovery_path.read_bytes())
            assert recovery["acceptance_authorized"] is False
            assert recovery["state"] == "prepared_non_acceptance"
            raise OSError("injected tombstone failure")
        real_ftruncate(descriptor, length)

    monkeypatch.setattr(module.os, "ftruncate", fail_second_tombstone)
    with pytest.raises(
        module.ArchiveRejected,
        match="archive_tombstone_write_failed",
    ):
        _seal(archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )

    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert not archive.campaign_manifest_path.exists()
    shards_root = archive.root / "shards"
    assert not shards_root.exists() or not list(shards_root.iterdir())
    assert archive.authority()["shard_count"] == 0

    monkeypatch.setattr(module.os, "ftruncate", real_ftruncate)
    shard = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    assert shard["verified_before_reclaim"] is True


def test_streaming_archive_rejects_path_replacement_before_reclaim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    real_open = module.os.open
    replacement_injected = False
    displaced = tmp_path / "decision.displaced.jsonl"

    def replace_after_first_binding(path, flags, *args, **kwargs):
        nonlocal replacement_injected
        if (
            not replacement_injected
            and Path(path) == outputs["scorecard"]
            and flags & module.os.O_RDWR
            and not flags & module.os.O_CREAT
        ):
            replacement_injected = True
            outputs["decision"].replace(displaced)
            outputs["decision"].write_bytes(expected["decision"])
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", replace_after_first_binding)
    with pytest.raises(
        module.ArchiveRejected,
        match="archive_raw_binding_changed",
    ):
        _seal(
            archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )

    assert replacement_injected is True
    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert displaced.read_bytes() == expected["decision"]
    assert not archive.campaign_manifest_path.exists()
    shards_root = archive.root / "shards"
    assert not shards_root.exists() or not list(shards_root.iterdir())


def test_streaming_archive_fsync_failure_restores_and_retries_same_day(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    scorecard_inode = outputs["scorecard"].stat().st_ino
    real_fsync = module.os.fsync
    injected = False

    def fail_scorecard_tombstone_fsync(descriptor: int) -> None:
        nonlocal injected
        opened = module.os.fstat(descriptor)
        if (
            not injected
            and opened.st_ino == scorecard_inode
            and opened.st_size == 0
        ):
            injected = True
            raise OSError("injected tombstone fsync failure")
        real_fsync(descriptor)

    monkeypatch.setattr(module.os, "fsync", fail_scorecard_tombstone_fsync)
    with pytest.raises(
        module.ArchiveRejected,
        match="archive_tombstone_write_failed",
    ):
        _seal(
            archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )

    assert injected is True
    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert not archive.campaign_manifest_path.exists()
    shards_root = archive.root / "shards"
    assert not shards_root.exists() or not list(shards_root.iterdir())

    monkeypatch.setattr(module.os, "fsync", real_fsync)
    shard = _seal(
        archive,
        start_day="2026-01-01",
        end_day="2026-01-07",
        current_summary_contract_root_sha256="a" * 64,
    )
    assert shard["verified_before_reclaim"] is True


def test_streaming_archive_rejects_hardlinked_hot_surface_before_reclaim(
    tmp_path: Path,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    expected = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        expected[role] = _write_rows(path, role)
        outputs[role] = path
    alias = tmp_path / "scorecard.alias.jsonl"
    os.link(outputs["scorecard"], alias)
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )

    with pytest.raises(
        module.ArchiveRejected,
        match="archive_raw_binding_invalid",
    ):
        _seal(
            archive,
            start_day="2026-01-01",
            end_day="2026-01-07",
            current_summary_contract_root_sha256="a" * 64,
        )

    assert {role: path.read_bytes() for role, path in outputs.items()} == expected
    assert alias.read_bytes() == expected["scorecard"]
    assert not archive.campaign_manifest_path.exists()
    shards_root = archive.root / "shards"
    assert not shards_root.exists() or not list(shards_root.iterdir())


def test_streaming_archive_multiple_shards_exposes_exact_cumulative_contract(
    tmp_path: Path,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    expected: dict[str, bytes] = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        first = _write_rows(
            path,
            role,
            start_day="2026-01-01",
            end_day="2026-01-01",
            marker=f"{role}-day-1",
        )
        expected[role] = first
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-01",
        current_summary_contract_root_sha256="a" * 64,
    )
    for role, path in outputs.items():
        second = _write_rows(
            path,
            role,
            start_day="2026-01-02",
            end_day="2026-01-02",
            marker=f"{role}-day-2",
        )
        expected[role] += second
    _seal(archive,
        start_day="2026-01-02",
        end_day="2026-01-02",
        current_summary_contract_root_sha256="b" * 64,
    )

    campaign = verify_campaign(archive.campaign_manifest_path)
    assert campaign["valid"] is True
    assert campaign["shard_count"] == 2
    cumulative = {
        row["role"]: row for row in campaign["cumulative_surfaces"]
    }
    partitions_by_role = {
        role: [
            row
            for row in campaign["verified_role_partitions"]
            if row["role"] == role
        ]
        for role in ("decision", "scorecard", "missed")
    }
    assert all(
        [row["row_start_offset"] for row in rows] == [0, 4]
        and [row["row_end_offset_exclusive"] for row in rows] == [4, 8]
        for rows in partitions_by_role.values()
    )
    assert len(campaign["verified_role_partitions_root_sha256"]) == 64
    for role, payload in expected.items():
        assert cumulative[role] == {
            "role": role,
            "bytes": len(payload),
            "rows": payload.count(b"\n"),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    gate_surfaces = archive.gate_surface_contracts()
    for role, record in gate_surfaces.items():
        assert {
            key: record[key] for key in ("role", "bytes", "rows", "sha256")
        } == cumulative[role]
        assert record["storage"] == "verified_zstd_campaign"
        assert Path(record["archive_campaign_manifest_path"]).is_file()


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    [
        ("calendar_gap", "archive_campaign_calendar_gap"),
        (
            "entry_manifest_metadata_drift",
            "archive_campaign_entry_manifest_metadata_mismatch",
        ),
    ],
)
def test_campaign_rejects_calendar_gap_and_entry_manifest_metadata_drift(
    tmp_path: Path,
    mutation: str,
    error_code: str,
) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(
            path,
            role,
            start_day="2026-01-01",
            end_day="2026-01-01",
            marker=f"{role}-day-1",
        )
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    _seal(archive,
        start_day="2026-01-01",
        end_day="2026-01-01",
        current_summary_contract_root_sha256="a" * 64,
    )
    second_day = "2026-01-03" if mutation == "calendar_gap" else "2026-01-02"
    for role, path in outputs.items():
        _write_rows(
            path,
            role,
            start_day=second_day,
            end_day=second_day,
            marker=f"{role}-day-2",
        )
    _seal(archive,
        start_day=second_day,
        end_day=second_day,
        current_summary_contract_root_sha256="b" * 64,
    )

    if mutation == "entry_manifest_metadata_drift":
        campaign = json.loads(archive.campaign_manifest_path.read_bytes())
        campaign["shards"][1]["segment_id"] = "999_forged_segment"
        campaign.pop("campaign_manifest_root_sha256")
        campaign["campaign_manifest_root_sha256"] = hashlib.sha256(
            _canonical(campaign)
        ).hexdigest()
        archive.campaign_manifest_path.write_bytes(_canonical(campaign) + b"\n")

    with pytest.raises(ValueError, match=error_code):
        verify_campaign(archive.campaign_manifest_path)


def test_streaming_archive_independent_verifier_rejects_corruption(tmp_path: Path) -> None:
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(
            path,
            role,
            start_day="2026-01-08",
            end_day="2026-01-08",
        )
        outputs[role] = path
    archive = StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    shard = _seal(archive,
        start_day="2026-01-08",
        end_day="2026-01-08",
        current_summary_contract_root_sha256="b" * 64,
    )
    target = Path(shard["surfaces"][0]["compressed_path"])
    raw = bytearray(target.read_bytes())
    raw[-1] ^= 1
    target.write_bytes(raw)
    with pytest.raises(ValueError, match="archive_compressed_identity_mismatch"):
        verify_campaign(archive.campaign_manifest_path)


def test_streaming_archive_verifier_does_not_import_writer_or_runner() -> None:
    verifier = Path(
        "src/research_infra/replay_acceleration_streaming_archive_verifier.py"
    )
    tree = ast.parse(verifier.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any("replay_acceleration_streaming_archive" in value for value in imports)
    assert not any("run_broad_live_as_if_replay_harness" in value for value in imports)
    assert not any(
        "replay_acceleration_attempt5_typed_sparse_runner" in value
        for value in imports
    )


def test_real_runner_archives_each_day_before_building_the_parity_request() -> None:
    runner = Path(
        "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
    ).read_text(encoding="utf-8")
    archive_call = runner.index(
        "archive_shard = streaming_archive.seal_and_reclaim("
    )
    gate_call = runner.index("gate_request = build_gate_request(")
    assert archive_call < gate_call
    assert "archived_result_surfaces=(" in runner
    assert "streaming_archive.gate_surface_contracts()" in runner
    assert 'len(streaming_archive_shards) != 31' in runner


def test_streaming_archive_day_capacity_guard_reserves_warning_headroom(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    usage = namedtuple("usage", "total used free")
    warning = 34 * 1024 * 1024 * 1024
    headroom = 768 * 1024 * 1024
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: usage(warning * 2, warning, warning + headroom - 1),
    )
    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=28 * 1024 * 1024 * 1024,
        warning_floor_free_bytes=warning,
    )
    with pytest.raises(module.ArchiveRejected, match="archive_day_capacity_warning"):
        archive.require_day_capacity(
            min_transient_headroom_bytes=headroom,
        )


def test_streaming_archive_day_capacity_settles_until_warning_headroom_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    usage = namedtuple("usage", "total used free")
    warning = 34 * 1024 * 1024 * 1024
    headroom = 768 * 1024 * 1024
    free_samples = iter(
        (
            warning + headroom - 1,
            warning + headroom,
        )
    )
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: usage(warning * 2, warning, next(free_samples)),
    )
    sleeps: list[float] = []
    collections: list[bool] = []
    monkeypatch.setattr(module, "time", _isolated_clock(module, sleeps.append))
    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=28 * 1024 * 1024 * 1024,
        warning_floor_free_bytes=warning,
    )

    contract = archive.require_day_capacity(
        min_transient_headroom_bytes=headroom,
        settle_timeout_seconds=10,
        settle_poll_seconds=5,
        on_advisory_miss=lambda: collections.append(True),
    )

    assert contract["valid"] is True
    assert contract["free_bytes"] == warning + headroom
    assert sleeps == [5]
    assert collections == [True]


def test_streaming_archive_day_capacity_settle_timeout_keeps_warning_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    usage = namedtuple("usage", "total used free")
    warning = 34 * 1024 * 1024 * 1024
    headroom = 768 * 1024 * 1024
    free_bytes = warning + headroom - 1
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: usage(warning * 2, warning, free_bytes),
    )
    sleeps: list[float] = []
    collections: list[bool] = []
    monkeypatch.setattr(module, "time", _isolated_clock(module, sleeps.append))
    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=28 * 1024 * 1024 * 1024,
        warning_floor_free_bytes=warning,
    )

    with pytest.raises(module.ArchiveRejected, match="archive_day_capacity_warning"):
        archive.require_day_capacity(
            min_transient_headroom_bytes=headroom,
            settle_timeout_seconds=10,
            settle_poll_seconds=5,
            on_advisory_miss=lambda: collections.append(True),
        )

    assert sleeps == [5, 5]
    assert collections == [True]


def test_streaming_archive_day_capacity_settle_rejects_hard_floor_without_wait(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    usage = namedtuple("usage", "total used free")
    warning = 34 * 1024 * 1024 * 1024
    hard = 28 * 1024 * 1024 * 1024
    headroom = 768 * 1024 * 1024
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: usage(warning * 2, warning, hard - 1),
    )
    sleeps: list[float] = []
    collections: list[bool] = []
    monkeypatch.setattr(module, "time", _isolated_clock(module, sleeps.append))
    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=hard,
        warning_floor_free_bytes=warning,
    )

    with pytest.raises(
        module.ArchiveRejected,
        match="archive_day_capacity_hard_floor",
    ):
        archive.require_day_capacity(
            min_transient_headroom_bytes=headroom,
            settle_timeout_seconds=10,
            settle_poll_seconds=5,
            on_advisory_miss=lambda: collections.append(True),
        )

    assert sleeps == []
    assert collections == []


@pytest.mark.parametrize(
    ("settle_timeout_seconds", "settle_poll_seconds"),
    (
        (float("inf"), 5),
        (float("nan"), 5),
        (10, float("inf")),
        (10, float("nan")),
    ),
)
def test_streaming_archive_day_capacity_settle_rejects_non_finite_bounds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    settle_timeout_seconds: float,
    settle_poll_seconds: float,
) -> None:
    from src.research_infra import replay_acceleration_streaming_archive as module

    outputs = {}
    for role in ("decision", "scorecard", "missed"):
        path = tmp_path / f"{role}.jsonl"
        _write_rows(path, role)
        outputs[role] = path
    archive = module.StreamingProofArchive(
        root=tmp_path / "archive",
        output_prefix="S0R0_TEST",
        hot_outputs=outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=28 * 1024 * 1024 * 1024,
    )
    sleeps: list[float] = []
    collections: list[bool] = []
    monkeypatch.setattr(module, "time", _isolated_clock(module, sleeps.append))
    monkeypatch.setattr(
        module.shutil,
        "disk_usage",
        lambda _path: pytest.fail("invalid bounds sampled disk capacity"),
    )

    with pytest.raises(
        module.ArchiveRejected,
        match="archive_day_capacity_settle_invalid",
    ):
        archive.require_day_capacity(
            min_transient_headroom_bytes=768 * 1024 * 1024,
            settle_timeout_seconds=settle_timeout_seconds,
            settle_poll_seconds=settle_poll_seconds,
            on_advisory_miss=lambda: collections.append(True),
        )

    assert sleeps == []
    assert collections == []

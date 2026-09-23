from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    replay_acceleration_task3_exact_cache_acceptance as task3,
)


def _payload() -> dict:
    return {
        "execution_manager_packet": {
            "generated_at_utc": "2026-01-02T12:00:00+00:00",
            "broker_order_lifecycle_capture_v4": {
                "generated_at_utc": "2026-01-02T12:00:00+00:00",
            },
            "scheduler_v4": {
                "packet": {
                    "exposure_snapshot": {
                        "open_positions": [],
                    }
                }
            },
            "economic_value": 1.0,
        },
        "broker_order_lifecycle_capture_v4_packet": {
            "packet_hash_sha256": "a" * 64,
            "pre_order_capture_contract": {
                "execution_manager_packet_hash": "b" * 64,
            },
        },
    }


def test_order_preimage_projection_allows_only_explicit_runtime_closure() -> None:
    reference = _payload()
    accelerated = copy.deepcopy(reference)
    accelerated["execution_manager_packet"]["generated_at_utc"] = (
        "2026-01-02T12:00:01+00:00"
    )
    accelerated["broker_order_lifecycle_capture_v4_packet"][
        "packet_hash_sha256"
    ] = "c" * 64

    projected, observed = task3.project_order_preimage_payload_pair(
        reference,
        accelerated,
        reference_hashes_by_exposure={},
        accelerated_hashes_by_exposure={},
    )

    assert projected["execution_manager_packet"]["generated_at_utc"] == (
        task3.TIME_SENTINEL
    )
    assert observed == {
        "broker_order_lifecycle_capture_v4_packet/packet_hash_sha256": 1,
        "execution_manager_packet/generated_at_utc": 1,
    }


def test_order_preimage_projection_rejects_economic_difference() -> None:
    reference = _payload()
    accelerated = copy.deepcopy(reference)
    accelerated["execution_manager_packet"]["economic_value"] = 2.0

    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_order_preimage_semantic_mismatch",
    ):
        task3.project_order_preimage_payload_pair(
            reference,
            accelerated,
            reference_hashes_by_exposure={},
            accelerated_hashes_by_exposure={},
        )


def test_order_preimage_projection_requires_bound_exposure_hash_aliases() -> None:
    reference = _payload()
    accelerated = copy.deepcopy(reference)
    reference_position = {
        "exposure_id": "trade:one",
        "metadata": {
            "broker_order_lifecycle_capture_v4_packet": {
                "packet_hash_sha256": "a" * 64,
                "pre_order_capture_contract": {
                    "execution_manager_packet_hash": "b" * 64,
                },
            }
        }
    }
    accelerated_position = copy.deepcopy(reference_position)
    accelerated_position["metadata"][
        "broker_order_lifecycle_capture_v4_packet"
    ]["packet_hash_sha256"] = "c" * 64
    reference["execution_manager_packet"]["scheduler_v4"]["packet"][
        "exposure_snapshot"
    ]["open_positions"] = [reference_position]
    accelerated["execution_manager_packet"]["scheduler_v4"]["packet"][
        "exposure_snapshot"
    ]["open_positions"] = [accelerated_position]

    projected, observed = task3.project_order_preimage_payload_pair(
        reference,
        accelerated,
        reference_hashes_by_exposure={"trade:one": ("a" * 64, "b" * 64)},
        accelerated_hashes_by_exposure={"trade:one": ("c" * 64, "b" * 64)},
    )
    assert projected["execution_manager_packet"]["scheduler_v4"]["packet"][
        "exposure_snapshot"
    ]["open_positions"][0]["metadata"][
        "broker_order_lifecycle_capture_v4_packet"
    ]["packet_hash_sha256"] == task3.HASH_SENTINEL
    assert observed[
        "execution_manager_packet/scheduler_v4/packet/exposure_snapshot/"
        "open_positions/0/metadata/broker_order_lifecycle_capture_v4_packet/"
        "packet_hash_sha256"
    ] == 1

    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_exposure_hash_alias_unbound",
    ):
        task3.project_order_preimage_payload_pair(
            reference,
            accelerated,
            reference_hashes_by_exposure={
                "trade:one": ("d" * 64, "b" * 64)
            },
            accelerated_hashes_by_exposure={
                "trade:one": ("c" * 64, "b" * 64)
            },
        )


def test_source_authority_schema_rejects_unknown_field() -> None:
    source = {key: None for key in task3._SOURCE_AUTHORITY_FIELDS}
    source["future_policy_switch"] = True
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_source_authority_schema_invalid",
    ):
        task3._require_exact_mapping_keys(
            source,
            task3._SOURCE_AUTHORITY_FIELDS,
            "task3_source_authority_schema_invalid",
        )


def _summary() -> dict:
    rows = []
    for expected in task3._EXPECTED_CACHE_ROWS:
        rows.append(
            {
                "start_day": expected["day"],
                "end_day": expected["day"],
                "campaign_exact_cache": {
                    "schema": "gtos.replay_acceleration.campaign_exact_cache.v1",
                    "status": "exact_cache_boundary_valid",
                    "config_root_sha256": "a" * 64,
                    "risk_profile_path": "config/profiles/ftmo.yaml",
                    "risk_profile_sha256": "b" * 64,
                    "expected_risk_profile_sha256": "b" * 64,
                    "risk_profile_payload_root_sha256": "c" * 64,
                    "miss_counts": copy.deepcopy(expected["miss_counts"]),
                    "cached_symbol_counts": copy.deepcopy(
                        expected["cached_symbol_counts"]
                    ),
                    "live_broker_authority": False,
                    "broker_mutation_enabled": False,
                },
            }
        )
    return {"progress_rows": rows}


def test_cache_audit_is_exact_and_rejects_repeated_miss() -> None:
    summary = _summary()
    result = task3.validate_cache_audits(summary)
    assert result["status"] == "TASK3_CAMPAIGN_CACHE_BOUNDED_AND_EXACT"

    summary["progress_rows"][1]["campaign_exact_cache"]["miss_counts"][
        "scheduler_config"
    ] = 2
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_cache_audit_invalid",
    ):
        task3.validate_cache_audits(summary)


def _sealed_sparse_prewarm_fixture(root: Path) -> dict:
    specs_by_symbol = {}
    for symbol in ("EURUSD", "USDJPY", "XAGUSD", "XAUUSD"):
        source_path = root / f"{symbol}.jsonl"
        source_path.write_text(
            "\n".join(
                (
                    json.dumps(
                        {
                            "time_utc": "2026-01-01T00:00:01+00:00",
                            "bid": 1.0,
                            "ask": 1.1,
                        },
                        sort_keys=True,
                    ),
                    json.dumps(
                        {
                            "time_utc": "2026-01-02T00:00:01+00:00",
                            "bid": 1.1,
                            "ask": 1.2,
                        },
                        sort_keys=True,
                    ),
                )
            )
            + "\n",
            encoding="utf-8",
        )
        specs_by_symbol[symbol] = (
            attempt5.SourceSpec(
                symbol=symbol,
                mapped_symbol=symbol,
                timeframe="TICK",
                path=source_path,
                source_family="ftmo_mt5_research_export",
                source_broker="FTMO",
                source_role="owner_authorized_research_hydration",
                start_utc="2026-01-01T00:00:01+00:00",
                end_utc="2026-01-02T00:00:01+00:00",
                row_count=2,
                sha256=attempt5.file_sha256(source_path),
                source_truth_scope=attempt5.SOURCE_TRUTH_SCOPE,
                not_redacted_account_native=True,
                ordered_tick_truth_satisfied=True,
            ),
        )
    window_start = datetime(2025, 12, 31, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 4, tzinfo=timezone.utc)
    constructed = attempt5.prewarm_sparse_tick_sources(
        specs_by_symbol=specs_by_symbol,
        cache_root=root / "cache",
        window_start=window_start,
        window_end=window_end,
        workers=4,
    )
    assert constructed["raw_source_full_hash_count"] == 4
    payload = attempt5.prewarm_sparse_tick_sources(
        specs_by_symbol=specs_by_symbol,
        cache_root=root / "cache",
        window_start=window_start,
        window_end=window_end,
        workers=4,
    )
    assert payload["raw_source_full_hash_count"] == 0
    assert payload["sealed_cache_reuse_count"] == 4
    return payload


def test_acceptance_binds_verified_warm_sparse_precondition(tmp_path: Path) -> None:
    payload = _sealed_sparse_prewarm_fixture(tmp_path)
    path = tmp_path / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = task3.validate_sealed_tick_cache_prewarm(tmp_path)

    assert result["raw_source_full_hash_count"] == 0
    assert result["sealed_cache_reuse_count"] == 4
    assert result["entry_count"] == 4

    invalid = copy.deepcopy(payload)
    invalid["raw_source_full_hash_count"] = 1
    core = copy.deepcopy(invalid)
    core.pop("prewarm_root_sha256")
    core.pop("non_authoritative_filesystem_storage_receipt")
    invalid["prewarm_root_sha256"] = task3.semantic.canonical_sha256(core)
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_warm_sparse_prewarm_invalid",
    ):
        task3.validate_sealed_tick_cache_prewarm(tmp_path)


def test_acceptance_independently_rejects_unsealed_or_corrupt_sparse_cache(
    tmp_path: Path,
) -> None:
    payload = _sealed_sparse_prewarm_fixture(tmp_path)
    receipt_path = (
        tmp_path / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
    )

    def write_receipt(value: dict) -> None:
        core = copy.deepcopy(value)
        core.pop("prewarm_root_sha256", None)
        core.pop("non_authoritative_filesystem_storage_receipt", None)
        value["prewarm_root_sha256"] = task3.semantic.canonical_sha256(core)
        receipt_path.write_text(json.dumps(value), encoding="utf-8")

    missing_root = copy.deepcopy(payload)
    missing_root["cache_root"] = str(tmp_path / "missing-cache")
    write_receipt(missing_root)
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_warm_sparse_cache",
    ):
        task3.validate_sealed_tick_cache_prewarm(tmp_path)

    forged_root = copy.deepcopy(payload)
    forged_root["entries"][0]["identity_root_sha256"] = "f" * 64
    write_receipt(forged_root)
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_warm_sparse_cache",
    ):
        task3.validate_sealed_tick_cache_prewarm(tmp_path)

    write_receipt(copy.deepcopy(payload))
    cache_root = Path(payload["cache_root"])
    first_entry = payload["entries"][0]
    entry_root = cache_root / first_entry["identity_root_sha256"]
    seal_path = entry_root / "SEALED"
    seal_bytes = seal_path.read_bytes()
    seal_path.unlink()
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_warm_sparse_cache",
    ):
        task3.validate_sealed_tick_cache_prewarm(tmp_path)
    seal_path.write_bytes(seal_bytes)

    manifest = json.loads(
        (entry_root / "manifest.json").read_text(encoding="ascii")
    )
    partition_path = entry_root / manifest["partitions"][0]["path"]
    original_partition = partition_path.read_bytes()
    corrupted_partition = bytearray(original_partition)
    corrupted_partition[-2] = (
        ord("9") if corrupted_partition[-2] != ord("9") else ord("8")
    )
    partition_path.write_bytes(bytes(corrupted_partition))
    with pytest.raises(
        task3.Task3ExactCacheRejected,
        match="task3_warm_sparse_cache",
    ):
        task3.validate_sealed_tick_cache_prewarm(tmp_path)

from __future__ import annotations

import json
import copy
import hashlib
import struct
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from compression import zstd

from src.research_infra.replay_compact_event_sink import (
    COMPACT_EVENT_ROLES,
    CompactEventSinkError,
    ReplayCompactEventSink,
    ReplayObservedLedger,
)
from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as attempt5,
)
from src.research import moonshot_scheduler_v4_best_trade_allocator as scheduler


def _legacy_jsonl_bytes(row: dict[str, object]) -> bytes:
    return (json.dumps(row, sort_keys=True, default=str) + "\n").encode("utf-8")


def _rows() -> dict[str, list[dict[str, object]]]:
    shared = {
        "nested": {"source": "FTMO", "values": [1, 2, 3]},
        "economic": {"risk_cash": 100.0, "net_proxy_r": -0.25},
    }
    return {
        role: [
            {
                "role": role,
                "ordinal": ordinal,
                "decision_time_utc": f"2026-01-02T00:{ordinal:02d}:00+00:00",
                "canonical_replay_candidate_instance_key": f"{role}-{ordinal}",
                "unicode_note": "causal-μ",
                "shared": shared,
            }
            for ordinal in range(3)
        ]
        for role in COMPACT_EVENT_ROLES
    }


def test_compact_event_sink_losslessly_round_trips_every_canonical_role(
    tmp_path: Path,
) -> None:
    rows_by_role = _rows()
    expected_by_role = copy.deepcopy(rows_by_role)
    sink = ReplayCompactEventSink(
        root=tmp_path / "compact-events",
        max_shard_bytes=310,
    )

    for ordinal in range(3):
        for role in COMPACT_EVENT_ROLES:
            row = rows_by_role[role][ordinal]
            sink.append(role, row)
            row["mutated_after_append"] = True

    authority = sink.seal()

    assert authority["status"] == "sealed"
    assert authority["row_counts"] == {role: 3 for role in COMPACT_EVENT_ROLES}
    assert authority["resident_canonical_row_count"] == 0
    assert authority["max_raw_event_bytes"] == 128 * 1024 * 1024
    assert all(
        shard["bytes"] <= 310
        for shards in authority["role_shards"].values()
        for shard in shards
    )
    assert any(
        len(shards) > 1 for shards in authority["role_shards"].values()
    )

    for role in COMPACT_EVENT_ROLES:
        reconstructed = list(sink.iter_rows(role))
        assert reconstructed == expected_by_role[role]
        assert b"".join(map(_legacy_jsonl_bytes, reconstructed)) == b"".join(
            _legacy_jsonl_bytes(row) for row in expected_by_role[role]
        )


def test_compact_event_sink_batches_rows_into_authenticated_blocks(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "ordinal": ordinal,
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
            "shared_proof": "same-source-bound-payload" * 12,
        }
        for ordinal in range(80)
    ]
    sink = ReplayCompactEventSink(
        root=tmp_path / "compact-events",
        max_shard_bytes=1024 * 1024,
        target_raw_block_bytes=4096,
    )
    for row in rows:
        sink.append("missed", row)

    authority = sink.seal()

    assert authority["schema"] == "gtos.replay_acceleration.compact_event_sink.v3"
    assert authority["format"] == "authenticated_role_ordinal_zstd_blocks"
    assert authority["target_raw_block_bytes"] == 4096
    block_count = sum(
        shard["blocks"] for shard in authority["role_shards"]["missed"]
    )
    assert 1 < block_count < len(rows)
    assert list(sink.iter_rows("missed")) == rows


def test_compact_event_sink_tracks_relational_identity_sets_incrementally(
    tmp_path: Path,
) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    candidate_a = {"canonical_replay_candidate_instance_key": "a"}
    candidate_b = {"canonical_replay_candidate_instance_key": "b"}

    sink.observe("candidate", candidate_a)
    sink.observe("candidate", candidate_b)
    sink.append("missed", candidate_a)
    sink.observe("order", candidate_b)
    sink.seal()

    audit = sink.relational_identity_audit()
    assert audit["exact"] is False
    assert audit["identity_coverage_exact"] is True
    assert audit["terminal_reconciliation_complete"] is False
    assert audit["candidate_rows"] == 2
    assert audit["candidate_unique_instance_keys"] == 2
    assert audit["observed_downstream_union_unique_instance_keys"] == 2
    assert audit["candidate_minus_observed_downstream_union_count"] == 0
    assert audit["observed_downstream_union_minus_candidate_count"] == 0


def test_observed_ledger_projects_only_completed_resident_rows(
    tmp_path: Path,
) -> None:
    sink = ReplayCompactEventSink(
        root=tmp_path / "compact-events",
        retained_row_projectors={
            "candidate": lambda row: {
                "canonical_replay_candidate_instance_key": row[
                    "canonical_replay_candidate_instance_key"
                ],
                "selector_action": row["selector_action"],
            },
        },
    )
    ledger = ReplayObservedLedger(sink=sink, role="candidate")
    first = {
        "canonical_replay_candidate_instance_key": "candidate-a",
        "selector_action": "skip",
        "large_packet_tree": {"payload": ["x" * 1024]},
    }
    second = {
        "canonical_replay_candidate_instance_key": "candidate-b",
        "selector_action": "hold",
        "large_packet_tree": {"payload": ["y" * 1024]},
    }
    ledger.append(first)
    ledger.append(second)
    first["selector_action"] = "reject"

    projected = ledger.project_completed_prefix(1)

    assert projected == 1
    assert ledger[0] == {
        "canonical_replay_candidate_instance_key": "candidate-a",
        "selector_action": "reject",
    }
    assert ledger[0] is not first
    assert ledger[1] is second
    assert sink.relational_identity_audit()["candidate_rows"] == 2


def test_compact_event_sink_rejects_fallback_only_relational_identity(
    tmp_path: Path,
) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    fallback_only = {
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "risk_finalizer_probe_instance_key": "fallback-1",
    }
    sink.observe("candidate", fallback_only)
    sink.append("missed", fallback_only)
    sink.seal()

    audit = sink.relational_identity_audit()
    assert audit["exact"] is False
    assert audit["missing_instance_key_counts"] == {
        "candidate": 1,
        "missed": 1,
        "order": 0,
        "trade": 0,
    }
    assert audit["fallback_only_instance_key_counts"] == {
        "candidate": 1,
        "missed": 1,
        "order": 0,
        "trade": 0,
    }
    assert sink.relational_identity_sets() == {
        "candidate": set(),
        "missed": set(),
        "order": set(),
        "trade": set(),
    }


def test_compact_event_sink_rejects_unknown_roles_and_post_seal_appends(
    tmp_path: Path,
) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    with pytest.raises(CompactEventSinkError, match="unknown_role"):
        sink.append("unknown", {"value": 1})
    sink.append("decision", {"value": 1})
    sink.seal()
    with pytest.raises(CompactEventSinkError, match="already_sealed"):
        sink.append("decision", {"value": 2})


def test_compact_event_sink_rejects_oversized_raw_event(tmp_path: Path) -> None:
    sink = ReplayCompactEventSink(
        root=tmp_path / "compact-events",
        max_raw_event_bytes=64,
    )
    with pytest.raises(
        CompactEventSinkError,
        match="raw_event_exceeds_max_bytes:decision",
    ):
        sink.append("decision", {"highly_compressible": "x" * 1_000_000})


def test_compact_event_sink_rejects_oversized_declared_raw_frame_before_decode(
    tmp_path: Path,
) -> None:
    root = tmp_path / "compact-events"
    sink = ReplayCompactEventSink(
        root=root,
        max_raw_event_bytes=1024,
        target_raw_block_bytes=256,
    )
    sink.append("decision", {"symbol": "XAUUSD"})
    authority = sink.seal()
    metadata = authority["role_shards"]["decision"][0]
    shard = root / metadata["path"]
    payload = bytearray(shard.read_bytes())
    first_ordinal, row_count, compressed_len, _raw_len, raw_sha = struct.unpack(
        ">QQQQ32s", payload[:64]
    )
    payload[:64] = struct.pack(
        ">QQQQ32s",
        first_ordinal,
        row_count,
        compressed_len,
        1033,
        raw_sha,
    )
    shard.write_bytes(payload)
    # Exercise the bounded decoder after the outer shard authentication layer.
    sink._authority["role_shards"]["decision"][0]["sha256"] = hashlib.sha256(
        payload
    ).hexdigest()

    with pytest.raises(CompactEventSinkError, match="raw_block_length_invalid"):
        list(sink.iter_rows("decision"))


def test_compact_event_sink_reopens_v2_row_frames(tmp_path: Path) -> None:
    root = tmp_path / "legacy-v2"
    root.mkdir()
    row = {"symbol": "XAUUSD", "candidate_count": 2}
    raw = _legacy_jsonl_bytes(row)
    compressed = zstd.compress(raw, level=1)
    frame = struct.pack(
        ">QQQ32s",
        0,
        len(compressed),
        len(raw),
        hashlib.sha256(raw).digest(),
    ) + compressed
    shard_path = root / "decision-00000.zstf"
    shard_path.write_bytes(frame)
    roles = list(COMPACT_EVENT_ROLES)
    empty_counts = {role: 0 for role in roles}
    empty_hash = hashlib.sha256(b"").hexdigest()
    deterministic = {
        "schema": "gtos.replay_acceleration.compact_event_sink.v2",
        "format": "authenticated_role_ordinal_zstd_frames",
        "compression": {"algorithm": "zstd", "level": 1},
        "max_shard_bytes": 4096,
        "max_raw_event_bytes": 128 * 1024 * 1024,
        "roles": roles,
        "row_counts": {**empty_counts, "decision": 1},
        "raw_byte_counts": {**empty_counts, "decision": len(raw)},
        "raw_stream_sha256": {
            **{role: empty_hash for role in roles},
            "decision": hashlib.sha256(raw).hexdigest(),
        },
        "role_shards": {
            **{role: [] for role in roles},
            "decision": [
                {
                    "path": shard_path.name,
                    "role": "decision",
                    "shard_index": 0,
                    "rows": 1,
                    "bytes": len(frame),
                    "raw_bytes": len(raw),
                    "sha256": hashlib.sha256(frame).hexdigest(),
                    "first_ordinal": 0,
                    "last_ordinal": 0,
                }
            ],
        },
        "resident_canonical_row_count": 0,
        "relational_identity_audit": {},
    }
    authority_root = hashlib.sha256(
        json.dumps(
            deterministic,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    manifest = {
        **deterministic,
        "status": "sealed",
        "authority_root_sha256": authority_root,
    }
    (root / "COMPACT_EVENT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    reopened = ReplayCompactEventSink.open_sealed(
        root=root,
        expected_authority_root_sha256=authority_root,
    )

    assert list(reopened.iter_rows("decision")) == [row]


def test_compact_event_ledger_rejects_all_random_access(tmp_path: Path) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    ledger = sink.ledger("decision")
    ledger.append({"symbol": "XAUUSD"})
    sink.seal()

    with pytest.raises(CompactEventSinkError, match="random_access_not_supported"):
        _ = ledger[0]
    with pytest.raises(CompactEventSinkError, match="random_access_not_supported"):
        _ = ledger[:]


def test_compact_event_sink_fails_closed_on_shard_corruption(tmp_path: Path) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    sink.append("missed", {"candidate_id": "c1", "value": [1, 2, 3]})
    authority = sink.seal()
    shard = tmp_path / "compact-events" / authority["role_shards"]["missed"][0][
        "path"
    ]
    payload = bytearray(shard.read_bytes())
    payload[-1] ^= 0x01
    shard.write_bytes(bytes(payload))

    with pytest.raises(CompactEventSinkError, match="shard_sha256_mismatch"):
        list(sink.iter_rows("missed"))


def test_compact_event_sink_reopens_only_with_bound_authority_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "compact-events"
    sink = ReplayCompactEventSink(root=root)
    sink.append("decision", {"symbol": "XAUUSD", "candidate_count": 2})
    authority = sink.seal()

    reopened = ReplayCompactEventSink.open_sealed(
        root=root,
        expected_authority_root_sha256=authority["authority_root_sha256"],
    )
    assert list(reopened.iter_rows("decision")) == [
        {"symbol": "XAUUSD", "candidate_count": 2}
    ]
    with pytest.raises(
        CompactEventSinkError,
        match="sealed_manifest_authority_root_mismatch",
    ):
        ReplayCompactEventSink.open_sealed(
            root=root,
            expected_authority_root_sha256="0" * 64,
        )


def test_compact_event_sink_preserves_legacy_infinite_guard_thresholds(
    tmp_path: Path,
) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    row = {
        "package_marketable_entry_guard": {
            "replay_route_quality_release": {
                "thresholds": {"max_expected_cost_r": float("inf")}
            }
        }
    }
    sink.append("missed", row)
    sink.seal()

    reconstructed = list(sink.iter_rows("missed"))
    assert _legacy_jsonl_bytes(reconstructed[0]) == _legacy_jsonl_bytes(row)


def test_compact_event_sink_rejects_truncated_frames(tmp_path: Path) -> None:
    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    sink.append("decision", {"symbol": "XAUUSD", "candidate_count": 0})
    authority = sink.seal()
    shard = tmp_path / "compact-events" / authority["role_shards"]["decision"][0][
        "path"
    ]
    shard.write_bytes(shard.read_bytes()[:-3])
    authority["role_shards"]["decision"][0]["sha256"] = "0" * 64

    with pytest.raises(CompactEventSinkError):
        list(sink.iter_rows("decision"))


def test_compact_event_reconstruction_matches_legacy_transform_bytes(
    tmp_path: Path,
) -> None:
    decision = {
        "campaign": "campaign",
        "phase": "repaired_development",
        "trading_day": "2026-01-02",
        "symbol": "XAUUSD",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "candidate_count": 1,
        "candidate_generation_audit": {
            "generation_scope": "all_hard_eligible_candidates",
            "candidate_count": 1,
        },
    }
    missed = {
        "campaign": "campaign",
        "phase": "repaired_development",
        "trading_day": "2026-01-02",
        "symbol": "XAUUSD",
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-1@@2026-01-02T08:00:00+00:00"
        ),
        "selector_action": "skip",
        "selector_reason": "lower_ranked_hard_eligible_candidate",
        "missed_opportunity_accounting_scope": "non_executable_diagnostic",
        "candidate_decision_quality": {"source_boundary": "predecision"},
    }
    profile = attempt5.PROFILE_REPAIRED
    split = "development"
    chunk_id = f"{profile}:{split}:2026-01-02:2026-01-02"

    legacy_result = {
        "ledgers": {
            "asof": [copy.deepcopy(decision)],
            "missed": [copy.deepcopy(missed)],
        }
    }
    attempt5.normalize_replay_result_ledgers(legacy_result)
    expected_decision = attempt5.annotate_rows(
        attempt5.compact_asof_decision_rows(legacy_result["ledgers"]["asof"]),
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type="asof_decision",
    )
    expected_missed = attempt5.annotate_rows(
        attempt5.compact_missed_opportunity_rows(
            legacy_result["ledgers"]["missed"]
        ),
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type="missed_opportunity",
    )

    sink = ReplayCompactEventSink(root=tmp_path / "compact-events")
    decision_ledger = sink.ledger("decision")
    missed_ledger = sink.ledger("missed")
    decision_ledger.append(decision)
    missed_ledger.append(missed)
    sink.seal()
    compact_result = {
        "ledgers": {"asof": decision_ledger, "missed": missed_ledger}
    }
    attempt5.normalize_replay_result_ledgers(compact_result)
    actual_decision = attempt5.annotate_rows(
        attempt5.compact_asof_decision_rows(compact_result["ledgers"]["asof"]),
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type="asof_decision",
    )
    actual_missed = attempt5.annotate_rows(
        attempt5.compact_missed_opportunity_rows(
            compact_result["ledgers"]["missed"]
        ),
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type="missed_opportunity",
    )

    assert b"".join(map(_legacy_jsonl_bytes, actual_decision)) == b"".join(
        map(_legacy_jsonl_bytes, expected_decision)
    )
    assert b"".join(map(_legacy_jsonl_bytes, actual_missed)) == b"".join(
        map(_legacy_jsonl_bytes, expected_missed)
    )

    projected_sink = ReplayCompactEventSink(
        root=tmp_path / "projected-compact-events",
        row_projectors={
            "decision": lambda row: attempt5.compact_asof_decision_rows(
                (row,)
            )[0],
            "missed": attempt5.project_compact_missed_transport_row,
        },
    )
    projected_decision_ledger = projected_sink.ledger("decision")
    projected_missed_ledger = projected_sink.ledger("missed")
    projected_decision_ledger.append(copy.deepcopy(decision))
    projected_missed_ledger.append(copy.deepcopy(missed))
    projected_sink.seal()
    projected_result = {
        "ledgers": {
            "asof": projected_decision_ledger,
            "missed": projected_missed_ledger,
        }
    }
    attempt5.normalize_replay_result_ledgers(projected_result)
    projected_decision = attempt5.annotate_rows(
        attempt5.compact_asof_decision_rows(
            projected_result["ledgers"]["asof"]
        ),
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type="asof_decision",
    )
    projected_missed = attempt5.annotate_rows(
        attempt5.compact_missed_opportunity_rows(
            projected_result["ledgers"]["missed"]
        ),
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type="missed_opportunity",
    )

    assert b"".join(map(_legacy_jsonl_bytes, projected_decision)) == b"".join(
        map(_legacy_jsonl_bytes, expected_decision)
    )
    assert b"".join(map(_legacy_jsonl_bytes, projected_missed)) == b"".join(
        map(_legacy_jsonl_bytes, expected_missed)
    )


def test_compact_event_sink_projects_once_before_transport(
    tmp_path: Path,
) -> None:
    projection_calls = 0

    def project(row: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal projection_calls
        projection_calls += 1
        return {
            "candidate_id": row["candidate_id"],
            "nested": row["nested"],
            "projection_schema": "test_projection_v1",
        }

    source = {
        "candidate_id": "candidate-1",
        "nested": {"value": 1},
        "discarded": {"large": ["payload"] * 100},
    }
    sink = ReplayCompactEventSink(
        root=tmp_path / "projected-events",
        row_projectors={"missed": project},
    )
    sink.append("missed", source)
    source["nested"]["value"] = 2
    source["discarded"]["large"].append("late-mutation")
    sink.seal()

    assert projection_calls == 1
    assert list(sink.iter_rows("missed")) == [
        {
            "candidate_id": "candidate-1",
            "nested": {"value": 1},
            "projection_schema": "test_projection_v1",
        }
    ]


def test_compact_event_sink_rejects_projector_identity_drift(
    tmp_path: Path,
) -> None:
    source = {
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-1@@2026-01-02T08:00:00+00:00"
        ),
    }
    sink = ReplayCompactEventSink(
        root=tmp_path / "projected-identity-drift",
        row_projectors={
            "missed": lambda row: {
                **row,
                "candidate_id": "candidate-2",
                "canonical_replay_candidate_instance_key": (
                    "candidate-2@@2026-01-02T08:00:00+00:00"
                ),
            }
        },
    )

    with pytest.raises(
        CompactEventSinkError,
        match="row_projector_candidate_identity_changed:missed",
    ):
        sink.append("missed", source)
    assert sink.row_count("missed") == 0


def test_compact_event_sink_rejects_in_place_projector_identity_drift(
    tmp_path: Path,
) -> None:
    source = {
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-1@@2026-01-02T08:00:00+00:00"
        ),
    }

    def mutate_identity(row: Mapping[str, Any]) -> Mapping[str, Any]:
        row["candidate_id"] = "candidate-2"
        row["canonical_replay_candidate_instance_key"] = (
            "candidate-2@@2026-01-02T08:00:00+00:00"
        )
        return row

    sink = ReplayCompactEventSink(
        root=tmp_path / "projected-in-place-identity-drift",
        row_projectors={"missed": mutate_identity},
    )

    with pytest.raises(
        CompactEventSinkError,
        match="row_projector_candidate_identity_changed:missed",
    ):
        sink.append("missed", source)
    assert sink.row_count("missed") == 0

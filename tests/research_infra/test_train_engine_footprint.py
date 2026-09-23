from __future__ import annotations

import json

from src.research_infra import replay_compact_event_sink as frozen_sink
from src.research_infra.train_engine import cuts, footprint


def _write_jsonl(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows)
    )


def test_projection_measurement_uses_the_runtime_jsonl_contract(tmp_path) -> None:
    path = tmp_path / "P_MISSED_OPPORTUNITY_LEDGER.jsonl"
    rows = [
        {
            "candidate_id": "c1",
            "canonical_replay_candidate_instance_key": "c1@@t",
            "decision_time_utc": "t",
            "unused": {"large": [1, 2, 3]},
        }
    ]
    _write_jsonl(path, rows)
    measured = footprint._jsonl_projection(path, cuts.project_missed_pool_row)
    expected = json.dumps(
        cuts.project_missed_pool_row(rows[0]), sort_keys=True, default=str
    ) + "\n"
    assert measured["rows"] == 1
    assert measured["source_is_canonical_append_jsonl"] is True
    assert measured["projected_bytes"] == len(expected.encode("utf-8"))


def test_inventory_counts_only_regular_file_payloads(tmp_path) -> None:
    (tmp_path / "empty").mkdir()
    (tmp_path / "a").write_bytes(b"abc")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "b").write_bytes(b"12345")
    observed = footprint.inventory(tmp_path)
    assert observed["file_count"] == 2
    assert observed["logical_bytes"] == 8
    assert observed["allocated_bytes"] >= 8


def test_stage_reports_deltas_and_ratios() -> None:
    row = footprint._stage(
        "cut",
        25,
        32,
        prior_logical_bytes=100,
        prior_allocated_bytes=128,
        basis="test",
    )
    assert row["logical_delta_bytes"] == -75
    assert row["allocated_delta_bytes"] == -96
    assert row["logical_ratio_to_prior"] == 0.25


def test_bounded_waterfall_prices_every_cut_and_observes_candidate(tmp_path) -> None:
    baseline = tmp_path / "BASE"
    sidecar = tmp_path / "BASE.semantic-diagnostic"
    candidate = tmp_path / "CAND"
    candidate_sidecar = tmp_path / "CAND.semantic-diagnostic"
    for root in (baseline, sidecar, candidate, candidate_sidecar):
        root.mkdir()
    _write_jsonl(
        baseline / "BASE_DECISION_LEDGER.jsonl",
        [{"candidate_id": "c1", "large": {"v": "x" * 500}}],
    )
    _write_jsonl(
        baseline / "BASE_SCORECARD_LEDGER.jsonl",
        [{"candidate_id": "c1", "large": {"v": "x" * 500}}],
    )
    _write_jsonl(
        baseline / "BASE_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [
            {
                "candidate_id": "c1",
                "canonical_replay_candidate_instance_key": "c1@@t",
                "decision_time_utc": "t",
                "unused": "x" * 500,
            }
        ],
    )
    for suffix in footprint.SEMANTIC_SUFFIXES:
        _write_jsonl(sidecar / f"BASE{suffix}", [{"unused": "x" * 500}])
    compact = baseline / "compact-event-shards"
    compact.mkdir()
    (compact / "payload.zstf").write_bytes(b"x" * 100)
    (candidate / "summary.json").write_text("{}")
    (candidate_sidecar / "stamp.jsonl").write_text("{}\n")

    observed = footprint.bounded_waterfall(
        baseline_route=baseline,
        candidate_route=candidate,
    )
    stages = {row["stage"]: row for row in observed["stages"]}
    assert stages["ledger_scalar_projection"]["logical_bytes"] < stages[
        "frozen_namespace"
    ]["logical_bytes"]
    assert stages["missed_pool_projection_v2"]["logical_bytes"] < stages[
        "ledger_scalar_projection"
    ]["logical_bytes"]
    assert stages["semantic_sidecar_projection"]["logical_bytes"] < stages[
        "missed_pool_projection_v2"
    ]["logical_bytes"]
    assert stages["train_resident_event_sink"]["logical_delta_bytes"] == -100
    assert observed["observed_candidate"]["logical_bytes"] == 5


def test_cold_month_reference_uses_manifests_and_authenticated_rows(tmp_path) -> None:
    route = tmp_path / "JANUARY_S1R1"
    sidecar = tmp_path / "JANUARY_S1R1.semantic-diagnostic"
    compact_root = tmp_path / "JANUARY_S1R1_COMPACT"
    route.mkdir()
    sidecar.mkdir()
    (route / "SUMMARY.json").write_text("{}")

    source_rows = {
        footprint.DECISION_SUFFIX: 1,
        footprint.SCORECARD_SUFFIX: 1,
        footprint.MISSED_SUFFIX: 1,
    }
    for suffix, rows in source_rows.items():
        archive = route / f"ARM{suffix}.cold"
        archive.mkdir()
        (archive / "manifest.json").write_text(
            json.dumps(
                {
                    "schema": "gtos.b7_5.cold_jsonl_archive.v1",
                    "status": "PASS_COLD_ARCHIVE_LOGICAL_BYTES_VERIFIED",
                    "logical_source": {
                        "name": f"ARM{suffix}",
                        "logical_bytes": 10_000,
                        "json_object_row_count": rows,
                        "sha256": "a" * 64,
                        "source_metadata_before_demotion": {
                            "physical_bytes": 12_288,
                        },
                    },
                }
            )
        )

    sink = frozen_sink.ReplayCompactEventSink(root=compact_root / "day-1")
    sink.append("decision", {"candidate_id": "c1", "large": {"x": "y" * 50}})
    sink.append("scorecard", {"candidate_id": "c1", "large": {"x": "y" * 50}})
    sink.append(
        "missed",
        {
            "candidate_id": "c1",
            "canonical_replay_candidate_instance_key": "c1@@t",
            "decision_time_utc": "t",
            "unused": "y" * 100,
        },
    )
    sink.seal()
    for suffix in footprint.SEMANTIC_SUFFIXES:
        _write_jsonl(sidecar / f"ARM{suffix}", [{"unused": "z" * 100}])

    observed = footprint.cold_month_reference(route, compact_root)
    stages = {row["stage"]: row for row in observed["stages"]}
    assert stages["ledger_scalar_projection"]["logical_bytes"] < stages[
        "frozen_namespace_pre_cold_demotion"
    ]["logical_bytes"]
    assert stages["missed_pool_projection_v2"]["logical_bytes"] < stages[
        "ledger_scalar_projection"
    ]["logical_bytes"]
    assert stages["semantic_sidecar_projection"]["logical_bytes"] < stages[
        "missed_pool_projection_v2"
    ]["logical_bytes"]
    assert stages["train_resident_event_sink"]["logical_delta_bytes"] == -observed[
        "compact_event_shards"
    ]["logical_bytes"]
    assert observed["projected_ledgers"]["missed"]["rows"] == 1

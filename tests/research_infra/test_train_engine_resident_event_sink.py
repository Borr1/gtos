from __future__ import annotations

import json
import types

import pytest

from src.research_infra import replay_compact_event_sink as frozen
from src.research_infra.train_engine import cuts, resident_event_sink as resident


def _new(tmp_path, name: str):
    return resident.TrainResidentEventSink(
        root=tmp_path / name,
        defer_seal_to_caller=True,
        row_projectors={"decision": lambda row: {**row, "projected": True}},
    )


def test_append_takes_a_deep_snapshot_and_iteration_returns_fresh_rows(tmp_path) -> None:
    sink = _new(tmp_path, "resident")
    source = {"candidate_id": "c1", "nested": {"values": [1, 2]}}
    sink.append("decision", source)
    source["nested"]["values"].append(3)
    authority = sink.seal()

    first = list(sink.iter_rows("decision"))
    assert first == [
        {
            "candidate_id": "c1",
            "nested": {"values": [1, 2]},
            "projected": True,
        }
    ]
    first[0]["nested"]["values"].append(99)
    assert list(sink.iter_rows("decision"))[0]["nested"]["values"] == [1, 2]
    assert authority["resident_canonical_row_count"] == 1
    assert authority["acceptance_authority"] is False


def test_the_sink_does_no_row_json_serialization_or_decode(monkeypatch, tmp_path) -> None:
    calls = 0
    original = json.dumps

    def counted(value, *args, **kwargs):
        nonlocal calls
        # The one small authority dict at seal is allowed. Row serialization is
        # identified by its candidate_id rather than by assuming a call count.
        if isinstance(value, dict) and value.get("candidate_id") == "c1":
            calls += 1
        return original(value, *args, **kwargs)

    monkeypatch.setattr(json, "dumps", counted)
    sink = _new(tmp_path, "resident")
    sink.append("decision", {"candidate_id": "c1", "nested": {"v": 1}})
    assert calls == 0
    sink.seal()
    assert calls == 0
    assert list(sink.iter_rows("decision"))[0]["candidate_id"] == "c1"
    assert calls == 0


def test_seal_leaves_only_the_empty_transport_directory(tmp_path) -> None:
    sink = _new(tmp_path, "resident")
    sink.append("missed", {"candidate_id": "c1"})
    sink.seal()
    assert sink.root.is_dir()
    assert list(sink.root.iterdir()) == []


def test_resident_ledger_preserves_order_len_and_no_random_access(tmp_path) -> None:
    sink = _new(tmp_path, "resident")
    ledger = sink.ledger("missed")
    ledger.extend([{"n": 1}, {"n": 2}])
    assert len(ledger) == 2
    with pytest.raises(frozen.CompactEventSinkError, match="sink_not_sealed"):
        list(ledger)
    sink.seal()
    assert [row["n"] for row in ledger] == [1, 2]
    with pytest.raises(frozen.CompactEventSinkError, match="random_access"):
        _ = ledger[0]


def test_abort_releases_resident_rows_and_cannot_seal(tmp_path) -> None:
    sink = _new(tmp_path, "resident")
    sink.append("missed", {"n": 1})
    sink.abort()
    assert sink._resident_count == 0
    assert all(not rows for rows in sink._resident_rows.values())
    with pytest.raises(frozen.CompactEventSinkError, match="sink_aborted"):
        sink.seal()


def test_resident_authority_is_deterministic_for_equal_rows(tmp_path) -> None:
    roots = []
    for name in ("a", "b"):
        sink = _new(tmp_path, name)
        sink.append("decision", {"candidate_id": "c1", "value": 1})
        sink.append("missed", {"candidate_id": "c2", "value": -1})
        roots.append(sink.seal()["authority_root_sha256"])
    assert roots[0] == roots[1]


def test_patch_rebinds_only_the_attempt_runner_constructor(monkeypatch) -> None:
    attempt = types.SimpleNamespace(ReplayCompactEventSink=frozen.ReplayCompactEventSink)
    monkeypatch.setattr(
        resident.accel,
        "_module",
        lambda name: attempt if name == resident.ATTEMPT5_MODULE else None,
    )
    patch = resident.make_patch()
    assert patch.sealed_compatible is False
    patch.apply()
    assert attempt.ReplayCompactEventSink is resident.TrainResidentEventSink
    assert frozen.ReplayCompactEventSink is not resident.TrainResidentEventSink
    patch.revert()
    assert attempt.ReplayCompactEventSink is frozen.ReplayCompactEventSink


def test_sink_stats_are_in_every_cut_report(tmp_path) -> None:
    cuts.reset_cut_stats()
    sink = _new(tmp_path, "resident")
    sink.append("missed", {"n": 1})
    sink.seal()
    list(sink.iter_rows("missed"))
    report = cuts.cut_report()["train_resident_event_sink"]
    assert report["rows_snapshotted"] == 1
    assert report["rows_iterated"] == 1
    assert report["json_serializations_inside_sink"] == 0
    assert report["json_decodes_inside_sink"] == 0

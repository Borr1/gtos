"""Tests for the packet silence alarm (Session P, B200-B219)."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "ultimate_book_packet_silence_alarm",
    REPO / "scripts" / "ultimate_book_packet_silence_alarm.py",
)
alarm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(alarm)

START = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _write(path: Path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def _packets(namespace, offsets_seconds, event_type="cycle_no_candidates"):
    return [
        {
            "namespace": namespace,
            "event_type": event_type,
            "created_at_utc": (START + timedelta(seconds=s)).isoformat(),
        }
        for s in offsets_seconds
    ]


def test_a_steady_stream_is_healthy(tmp_path):
    log = _write(tmp_path / "p.jsonl", _packets("ftmo", range(0, 3600, 60)))
    report = alarm.evaluate(log, threshold_seconds=1800, expected_namespaces=["ftmo"])
    assert report["healthy"] is True
    assert report["namespaces"]["ftmo"]["silence_breaches"] == 0


def test_the_fifteen_minute_idle_pattern_is_not_an_alarm(tmp_path):
    """Measured p99 on the live export is 909.6 s -- the M15 bar idle. A threshold that fires on
    it would have produced 1,633 alerts across the live window, which is a broken tool."""
    log = _write(tmp_path / "p.jsonl", _packets("ftmo", [0, 900, 1800, 2700]))
    report = alarm.evaluate(log, threshold_seconds=1800, expected_namespaces=["ftmo"])
    assert report["namespaces"]["ftmo"]["silence_breaches"] == 0


def test_a_real_outage_is_reported_with_its_window(tmp_path):
    log = _write(tmp_path / "p.jsonl", _packets("ftmo", [0, 60, 7260, 7320]))
    report = alarm.evaluate(log, threshold_seconds=1800, expected_namespaces=["ftmo"])
    block = report["namespaces"]["ftmo"]
    assert block["silence_breaches"] == 1
    assert block["longest_silences"][0]["minutes"] == pytest.approx(120.0)
    assert report["healthy"] is False


def test_a_book_that_died_entirely_is_caught_by_set_difference(tmp_path):
    """The signal an accumulator cannot produce: a namespace that emits nothing at all never
    appears in any observed set, so only an independently-declared expected roster finds it."""
    log = _write(tmp_path / "p.jsonl", _packets("ftmo", range(0, 600, 60)))
    report = alarm.evaluate(
        log, threshold_seconds=1800, expected_namespaces=["ftmo", "redacted_account"]
    )
    assert report["missing_namespaces"] == ["redacted_account"]
    assert report["silent"] is True
    assert report["healthy"] is False


def test_an_unexpected_namespace_is_reported_not_ignored(tmp_path):
    log = _write(tmp_path / "p.jsonl", _packets("surprise_book", range(0, 600, 60)))
    report = alarm.evaluate(log, threshold_seconds=1800, expected_namespaces=["ftmo"])
    assert report["unexpected_namespaces"] == ["surprise_book"]
    assert report["missing_namespaces"] == ["ftmo"]


def test_rejection_markers_are_surfaced_alongside_silence(tmp_path):
    """A stream can be perfectly punctual and still be lying; a reader checking one must see
    the other."""
    rows = _packets("ftmo", range(0, 600, 60))
    rows += _packets("ftmo", [660], event_type="packet_rejected")
    log = _write(tmp_path / "p.jsonl", rows)
    report = alarm.evaluate(log, threshold_seconds=1800, expected_namespaces=["ftmo"])
    assert report["namespaces"]["ftmo"]["silence_breaches"] == 0
    assert report["total_packet_rejected_markers"] == 1
    assert report["healthy"] is False, "punctual but refusing is not healthy"


def test_unparseable_lines_are_counted_not_skipped_silently(tmp_path):
    path = tmp_path / "p.jsonl"
    path.write_text(
        json.dumps(_packets("ftmo", [0])[0]) + "\n{not json\n", encoding="utf-8"
    )
    report = alarm.evaluate(path, threshold_seconds=1800, expected_namespaces=["ftmo"])
    assert report["unparseable_lines"] == 1
    assert report["healthy"] is False

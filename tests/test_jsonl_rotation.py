"""Tests for ``src/utils/jsonl_rotation.py`` — RotatingJsonlWriter.

Covers:

1. Size-trigger rotation (write rows past size_mb → new live file + archive).
2. Time-trigger rotation (UTC midnight crossing simulated via clock injection).
3. Retention sweep moves archives older than retention_days to archive_dir.
4. Atomic rename + crash safety: simulate failure mid-rotation, verify recovery.
5. Concurrent write safety: two writers, no row loss on size trigger.
6. Gzip output is a valid gzip file with the expected JSONL contents.
7. Foreign / unparseable filenames in the archive dir do not break sweep.
8. Empty live file does not produce a zero-byte archive on rotation.
9. ``cleanup_pending`` re-compresses leftover archives at startup.
10. ``force_rotate`` produces an archive deterministically.
"""

from __future__ import annotations

import gzip
import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.utils import jsonl_rotation
from src.utils.jsonl_rotation import (
    RotatingJsonlWriter,
    _archive_age_days,
    _archive_name,
    _compressed_name,
    _gzip_in_place,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(n_kb: int = 1) -> dict:
    """Return a row whose JSON encoding is roughly ``n_kb`` KB."""
    # 1 byte per char; pad with 'x' to hit the target KB.
    return {"i": 1, "pad": "x" * max(1, n_kb * 1024 - 32)}


def _read_jsonl_text(path: Path) -> list[dict]:
    rows = []
    with path.open("rb") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line.decode("utf-8")))
    return rows


def _read_jsonl_gz(path: Path) -> list[dict]:
    rows = []
    with gzip.open(str(path), "rb") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line.decode("utf-8")))
    return rows


# ---------------------------------------------------------------------------
# 1. Size-trigger rotation
# ---------------------------------------------------------------------------


def test_size_trigger_rotates_and_creates_archive(tmp_path):
    base = tmp_path / "shadow.jsonl"
    archive_dir = tmp_path / "_archive"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=1,            # 1 MB trigger for fast test
        retention_days=14,
        archive_dir=archive_dir,
        gzip_async=False,
    )
    # Pre-populate ~1 MB so the next write trips size trigger.
    pad = _payload(n_kb=1)
    for _ in range(1100):  # ~1.1 MB worth of rows (each ~1 KB encoded)
        writer.write(pad)
    # Live file under threshold — no rotation yet OR rotated mid-way.
    # Forcing a single more write after the threshold guarantees rotation
    # for the next call.
    writer.write(pad)

    # The live file must exist and be smaller than the size threshold (post-rotation).
    assert base.exists()
    assert base.stat().st_size < 1024 * 1024  # <1 MB

    # An archive (.jsonl.gz) must exist next to the live file.
    archives = list(tmp_path.glob("shadow_*.jsonl.gz"))
    assert len(archives) >= 1, f"expected at least one archive, got {list(tmp_path.iterdir())}"


def test_size_trigger_preserves_all_rows(tmp_path):
    """No row should be lost on rotation: archive + live = total rows written."""
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=1,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    n = 1500  # well past the 1 MB threshold given ~1 KB rows
    for i in range(n):
        writer.write({"i": i, "pad": "x" * 800})

    # Total rows = live + archive (gzipped).
    total = 0
    if base.exists():
        total += len(_read_jsonl_text(base))
    for archive in tmp_path.glob("shadow_*.jsonl.gz"):
        total += len(_read_jsonl_gz(archive))
    assert total == n, f"expected {n} rows total, got {total}"


# ---------------------------------------------------------------------------
# 2. Time-trigger rotation
# ---------------------------------------------------------------------------


class _StubClock:
    """Mutable clock that lets a test simulate UTC midnight crossing."""

    def __init__(self, dt: datetime) -> None:
        self.dt = dt

    def __call__(self) -> datetime:
        return self.dt


def test_time_trigger_rotates_at_utc_midnight_cross(tmp_path):
    base = tmp_path / "shadow.jsonl"
    yesterday = datetime(2026, 4, 25, 23, 59, 30, tzinfo=timezone.utc)
    today = datetime(2026, 4, 26, 0, 0, 5, tzinfo=timezone.utc)
    clock = _StubClock(yesterday)
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=100,           # huge — size trigger should NOT fire
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
        clock=clock,
    )
    # Write a row "yesterday" and force the file's mtime to match.
    writer.write({"day": "yesterday"})
    yesterday_ts = (yesterday - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
    os.utime(str(base), (yesterday_ts, yesterday_ts))

    # Cross UTC midnight, write a fresh row → should rotate.
    clock.dt = today
    writer.write({"day": "today"})

    # Live file must contain only "today".
    rows = _read_jsonl_text(base)
    assert rows == [{"day": "today"}]

    # Archive must exist and contain the "yesterday" row.
    archives = list(tmp_path.glob("shadow_2026-04-25.jsonl.gz"))
    assert len(archives) == 1
    archive_rows = _read_jsonl_gz(archives[0])
    assert archive_rows == [{"day": "yesterday"}]


# ---------------------------------------------------------------------------
# 3. Retention sweep
# ---------------------------------------------------------------------------


def test_retention_moves_old_archives_to_archive_dir(tmp_path):
    base = tmp_path / "shadow.jsonl"
    archive_dir = tmp_path / "_archive"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=2,
        archive_dir=archive_dir,
        gzip_async=False,
    )
    # Hand-create three "archives": one fresh, one in-window, one expired.
    today = datetime.now(timezone.utc).date()
    fresh = today.strftime("%Y-%m-%d")
    in_window = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    expired = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    fresh_path = tmp_path / f"shadow_{fresh}.jsonl.gz"
    in_window_path = tmp_path / f"shadow_{in_window}.jsonl.gz"
    expired_path = tmp_path / f"shadow_{expired}.jsonl.gz"
    for p in (fresh_path, in_window_path, expired_path):
        with gzip.open(str(p), "wb") as f:
            f.write(b'{"k": "v"}\n')

    # Trigger retention via cleanup_pending (no rotation needed).
    writer.cleanup_pending()

    # Fresh + in-window stay; expired moves.
    assert fresh_path.exists()
    assert in_window_path.exists()
    assert not expired_path.exists()

    expected_dest = archive_dir / expired[:7] / expired_path.name
    assert expected_dest.exists()
    # Verify content survived the move.
    rows = _read_jsonl_gz(expected_dest)
    assert rows == [{"k": "v"}]


def test_retention_disabled_when_retention_days_zero(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=0,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    long_ago = (datetime.now(timezone.utc).date() - timedelta(days=365)).strftime(
        "%Y-%m-%d"
    )
    old_path = tmp_path / f"shadow_{long_ago}.jsonl.gz"
    with gzip.open(str(old_path), "wb") as f:
        f.write(b'{"k": "v"}\n')

    writer.cleanup_pending()
    # retention_days=0 means "never sweep" — old file stays in place.
    assert old_path.exists()


# ---------------------------------------------------------------------------
# 4. Atomic rename / crash safety
# ---------------------------------------------------------------------------


def test_crash_after_rename_recovers_uncompressed_archive(tmp_path, monkeypatch):
    """Simulate a crash AFTER os.replace but BEFORE gzip completion.

    The next rotation should re-discover the uncompressed archive and
    compress it via _compress_pending.
    """
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,    # synchronous so we can intercept gzip directly
    )
    writer.write({"k": "before-crash"})

    # Patch _gzip_in_place to raise — simulating the gzip failing or the
    # process dying before compression.
    def _boom(*args, **kwargs):
        raise RuntimeError("simulated mid-rotation crash")

    monkeypatch.setattr(jsonl_rotation, "_gzip_in_place", _boom)
    writer.force_rotate()

    # We must have an UNCOMPRESSED archive on disk.
    uncompressed_archives = [
        p for p in tmp_path.glob("shadow_*.jsonl") if p.name != base.name
    ]
    assert len(uncompressed_archives) == 1
    assert _read_jsonl_text(uncompressed_archives[0]) == [{"k": "before-crash"}]

    # Now restore real gzip + retry — _compress_pending should pick up the leftover.
    monkeypatch.setattr(jsonl_rotation, "_gzip_in_place", _gzip_in_place)
    writer.cleanup_pending()
    # Uncompressed archive is now gone, replaced by the .gz form.
    assert not uncompressed_archives[0].exists()
    compressed = _compressed_name(uncompressed_archives[0])
    assert compressed.exists()
    assert _read_jsonl_gz(compressed) == [{"k": "before-crash"}]


def test_atomic_rename_either_state_is_recoverable(tmp_path, monkeypatch):
    """If os.replace itself fails, the live file must be untouched."""
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    writer.write({"k": "v"})
    pre_size = base.stat().st_size

    def _boom_replace(*args, **kwargs):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(os, "replace", _boom_replace)
    # The writer's defensive try/except around write() swallows; force_rotate
    # is more direct but the writer's lock + exception handler in write()
    # also swallows. We use force_rotate to surface the failure path.
    try:
        writer.force_rotate()
    except OSError:
        # acceptable — direct force_rotate may surface; the live file must
        # still be intact regardless.
        pass

    # Live file is untouched (no archive generated).
    assert base.exists()
    assert base.stat().st_size == pre_size
    assert _read_jsonl_text(base) == [{"k": "v"}]


# ---------------------------------------------------------------------------
# 5. Concurrent writers
# ---------------------------------------------------------------------------


def test_concurrent_writes_no_row_loss(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=1,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    # 4 threads, each writes 200 rows (~200 KB each → 800 KB total, no rotation).
    N_THREADS = 4
    N_PER_THREAD = 200
    barrier = threading.Barrier(N_THREADS)

    def _worker(thread_id: int) -> None:
        barrier.wait()
        for i in range(N_PER_THREAD):
            writer.write({"tid": thread_id, "i": i, "pad": "x" * 800})

    threads = [threading.Thread(target=_worker, args=(t,)) for t in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    # Sum live + archives = N_THREADS * N_PER_THREAD.
    total = 0
    if base.exists():
        total += len(_read_jsonl_text(base))
    for archive in tmp_path.glob("shadow_*.jsonl.gz"):
        total += len(_read_jsonl_gz(archive))
    for archive in tmp_path.glob("shadow_*.jsonl"):
        if archive.name == base.name:
            continue
        total += len(_read_jsonl_text(archive))
    assert total == N_THREADS * N_PER_THREAD


def test_write_and_force_rotate_use_cross_process_lock(tmp_path, monkeypatch):
    base = tmp_path / "shadow.jsonl"
    expected_lock_path = base.with_suffix(base.suffix + ".lock")
    events: list[tuple[str, Path]] = []

    class _SpyCrossProcessFileLock:
        def __init__(self, path: Path) -> None:
            self.path = Path(path)

        def __enter__(self) -> "_SpyCrossProcessFileLock":
            events.append(("enter", self.path))
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            events.append(("exit", self.path))

    monkeypatch.setattr(
        jsonl_rotation,
        "_CrossProcessFileLock",
        _SpyCrossProcessFileLock,
    )
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )

    writer.write({"k": "v"})
    writer.force_rotate()

    assert events == [
        ("enter", expected_lock_path),
        ("exit", expected_lock_path),
        ("enter", expected_lock_path),
        ("exit", expected_lock_path),
    ]


def test_two_writer_instances_share_lock_file_and_preserve_parseable_rows(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer_a = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    writer_b = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )

    n = 100
    for i in range(n):
        writer_a.write({"writer": "a", "i": i})
        writer_b.write({"writer": "b", "i": i})

    assert base.with_suffix(base.suffix + ".lock").exists()
    rows = _read_jsonl_text(base)
    assert len(rows) == n * 2
    assert rows == [
        {"writer": writer_name, "i": i}
        for i in range(n)
        for writer_name in ("a", "b")
    ]


# ---------------------------------------------------------------------------
# 6. Gzip output validity
# ---------------------------------------------------------------------------


def test_gzip_output_round_trips(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    rows_in = [{"k": i, "v": f"row-{i}"} for i in range(50)]
    for r in rows_in:
        writer.write(r)
    writer.force_rotate()
    archives = list(tmp_path.glob("shadow_*.jsonl.gz"))
    assert len(archives) == 1
    rows_out = _read_jsonl_gz(archives[0])
    assert rows_out == rows_in


# ---------------------------------------------------------------------------
# 7. Foreign filenames don't break sweep
# ---------------------------------------------------------------------------


def test_retention_sweep_ignores_foreign_files(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=2,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    # A file matching nothing the writer cares about.
    weird = tmp_path / "shadow_NOT-A-DATE.jsonl.gz"
    with gzip.open(str(weird), "wb") as f:
        f.write(b'{"k": "v"}\n')
    other = tmp_path / "unrelated_file.txt"
    other.write_text("noop")

    writer.cleanup_pending()  # must not raise

    # Foreign files are still in place.
    assert weird.exists()
    assert other.exists()


def test_archive_age_days_returns_none_for_foreign_filename():
    assert _archive_age_days("not_a_log.txt", "shadow") is None
    assert _archive_age_days("shadow_NOT-A-DATE.jsonl", "shadow") is None
    assert _archive_age_days("shadow_2026-04-26.jsonl", "shadow") is not None


# ---------------------------------------------------------------------------
# 8. Empty file edge case
# ---------------------------------------------------------------------------


def test_empty_file_does_not_rotate(tmp_path):
    base = tmp_path / "shadow.jsonl"
    base.touch()  # zero-byte live file
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    # Even a forced rotate should be a no-op for empty files.
    writer.force_rotate()
    archives = list(tmp_path.glob("shadow_*.jsonl*"))
    assert archives == []
    # Live file still exists.
    assert base.exists()


# ---------------------------------------------------------------------------
# 9. cleanup_pending + recovery
# ---------------------------------------------------------------------------


def test_cleanup_pending_compresses_leftovers(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    # Hand-create an uncompressed archive (e.g. left behind by a previous crash).
    leftover = tmp_path / "shadow_2026-04-26.jsonl"
    leftover.write_text('{"k":"v"}\n')

    writer.cleanup_pending()

    assert not leftover.exists()
    assert _compressed_name(leftover).exists()
    assert _read_jsonl_gz(_compressed_name(leftover)) == [{"k": "v"}]


# ---------------------------------------------------------------------------
# 10. force_rotate behaviour
# ---------------------------------------------------------------------------


def test_force_rotate_creates_archive_and_resets_live_file(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=False,
    )
    writer.write({"k": "first"})
    writer.force_rotate()
    # Live file is gone OR empty.
    if base.exists():
        assert base.stat().st_size == 0
    archives = list(tmp_path.glob("shadow_*.jsonl.gz"))
    assert len(archives) == 1
    assert _read_jsonl_gz(archives[0]) == [{"k": "first"}]

    # Subsequent write goes to a fresh live file.
    writer.write({"k": "second"})
    assert _read_jsonl_text(base) == [{"k": "second"}]


# ---------------------------------------------------------------------------
# 11. Constructor validation
# ---------------------------------------------------------------------------


def test_rejects_negative_size_mb(tmp_path):
    with pytest.raises(ValueError, match="size_mb"):
        RotatingJsonlWriter(base_path=tmp_path / "x.jsonl", size_mb=0)


def test_rejects_negative_retention_days(tmp_path):
    with pytest.raises(ValueError, match="retention_days"):
        RotatingJsonlWriter(
            base_path=tmp_path / "x.jsonl",
            size_mb=10,
            retention_days=-1,
        )


# ---------------------------------------------------------------------------
# 12. Async gzip joins cleanly
# ---------------------------------------------------------------------------


def test_async_gzip_completes_via_join(tmp_path):
    base = tmp_path / "shadow.jsonl"
    writer = RotatingJsonlWriter(
        base_path=base,
        size_mb=10,
        retention_days=14,
        archive_dir=tmp_path / "_archive",
        gzip_async=True,
    )
    for i in range(20):
        writer.write({"i": i})
    writer.force_rotate()
    writer.join_gzip(timeout=10)
    archives = list(tmp_path.glob("shadow_*.jsonl.gz"))
    assert len(archives) == 1
    rows = _read_jsonl_gz(archives[0])
    assert len(rows) == 20


# ---------------------------------------------------------------------------
# 13. Integration with structure_detector_shadow_logger
# ---------------------------------------------------------------------------


def test_structure_detector_logger_routes_through_rotating_writer(tmp_path, monkeypatch):
    """End-to-end: log_structure_divergence writes via RotatingJsonlWriter.

    Verifies that calling the public logger function (a) creates the live
    JSONL via the writer, (b) honors the size threshold for rotation, and
    (c) gzip archives the rotated content.
    """
    from src.components import structure_detector_shadow_logger as sd_mod
    from src.models.market_state_models import StructureAnalysis

    sd_mod._reset_writers_for_tests()
    # Force a tiny size_mb for this test by overriding module defaults.
    monkeypatch.setattr(sd_mod, "_DEFAULT_ROTATION_SIZE_MB", 1)
    monkeypatch.setattr(sd_mod, "_DEFAULT_RETENTION_DAYS", 14)
    monkeypatch.setattr(sd_mod, "_DEFAULT_ARCHIVE_DIR", str(tmp_path / "archive"))

    log_path = str(tmp_path / "divergences.jsonl")
    v1 = StructureAnalysis(direction="bullish")
    v2 = StructureAnalysis(direction="bearish")

    # Write enough rows to trigger size rotation. Each row ~250 bytes;
    # 5000 rows = ~1.25 MB which crosses the 1 MB threshold.
    for i in range(5000):
        sd_mod.log_structure_divergence(
            symbol="XAUUSD",
            timeframe="H1",
            v1_label=v1,
            v2_label=v2,
            detector_version_config="v2_shadow",
            production_label=v1,
            candle_time=f"2026-04-25T{(i % 24):02d}:00:00Z",
            log_path=log_path,
            logged_at="2026-04-25T00:00:00Z",
        )
    # Wait for any background gzip threads.
    writer = sd_mod._get_writer(log_path)
    writer.join_gzip(timeout=15)

    # Total rows = live + archive = 5000.
    total = 0
    if Path(log_path).exists():
        total += len(_read_jsonl_text(Path(log_path)))
    for archive in (tmp_path).glob("divergences_*.jsonl.gz"):
        total += len(_read_jsonl_gz(archive))
    assert total == 5000


def test_configure_rotation_from_config_overrides_defaults(monkeypatch):
    """``configure_rotation_from_config`` mutates module defaults + clears cache."""
    from src.components import structure_detector_shadow_logger as sd_mod

    # Stash and reset defaults so this test is independent.
    monkeypatch.setattr(sd_mod, "_DEFAULT_ROTATION_SIZE_MB", 50)
    monkeypatch.setattr(sd_mod, "_DEFAULT_RETENTION_DAYS", 14)
    monkeypatch.setattr(sd_mod, "_DEFAULT_ARCHIVE_DIR", "research/archive/foo")

    cfg = {
        "shadow_loggers": {
            "structure_detector": {
                "rotation": {
                    "size_mb": 25,
                    "retention_days": 7,
                    "archive_dir": "research/archive/test_dir",
                }
            }
        }
    }
    sd_mod.configure_rotation_from_config(cfg)
    assert sd_mod._DEFAULT_ROTATION_SIZE_MB == 25
    assert sd_mod._DEFAULT_RETENTION_DAYS == 7
    assert sd_mod._DEFAULT_ARCHIVE_DIR == "research/archive/test_dir"


def test_configure_rotation_handles_missing_config(monkeypatch):
    """Missing/partial config blocks are silent no-ops (defaults preserved)."""
    from src.components import structure_detector_shadow_logger as sd_mod

    monkeypatch.setattr(sd_mod, "_DEFAULT_ROTATION_SIZE_MB", 50)
    sd_mod.configure_rotation_from_config(None)
    assert sd_mod._DEFAULT_ROTATION_SIZE_MB == 50
    sd_mod.configure_rotation_from_config({})
    assert sd_mod._DEFAULT_ROTATION_SIZE_MB == 50
    sd_mod.configure_rotation_from_config({"shadow_loggers": "not-a-dict"})
    assert sd_mod._DEFAULT_ROTATION_SIZE_MB == 50
    sd_mod.configure_rotation_from_config({"shadow_loggers": {}})
    assert sd_mod._DEFAULT_ROTATION_SIZE_MB == 50

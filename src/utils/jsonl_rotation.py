"""Hybrid (size + time) rotating JSONL writer with gzip archive + retention.

Background
----------
Several shadow loggers in this codebase append to JSONL files at a high
cadence — most notably ``shadow_logs/structure_detector_divergences.jsonl``,
which writes one row per (instrument, timeframe) on every M15 candle close.
Without rotation a live JSONL grows unboundedly: the structure-detector log
crossed 22 MB / 65,200 lines after ~6 weeks of v2_shadow operation, and was
projected at ~100 MB by mid-July.

The audit verdict: hybrid rotation, daily archive, retention horizon. This
module implements that policy as a single drop-in writer class so additional
loggers can opt in by replacing their bare ``open(..., "a")`` site with a
``RotatingJsonlWriter.write(row)`` call.

Rotation policy
---------------
A row write triggers rotation if EITHER condition is true:

1. **Size trigger** — the live file's current size + the encoded row would
   exceed ``size_mb`` MB. Default: 50 MB.
2. **Time trigger** — UTC date has rolled over since the live file's
   ``last_modified`` mtime (i.e. we crossed UTC midnight since the last
   write). This guarantees one archive per UTC day even on light-traffic
   loggers.

When rotation triggers, the writer:

1. Closes the live file handle.
2. Computes the rotation date — the UTC date of the row whose write would
   exceed the threshold (same day as ``now`` for the size trigger; the
   *previous* day for the time trigger so the archive aggregates the
   day that just closed).
3. **Atomically renames** ``{base}.jsonl`` -> ``{base}_{YYYY-MM-DD}.jsonl``
   (the uncompressed archive). Atomic rename survives mid-rotation crashes
   because Windows ``os.replace`` and POSIX ``rename`` are atomic at the
   filesystem layer — either the rename happened (the live file is now the
   archive), or it didn't (the live file is still the live file). No state
   is lost mid-rotation.
4. Spawns a background daemon thread to gzip the archive in place
   (``{archive}.gz`` produced; original ``{archive}`` removed once gzip is
   complete). The gzip step is best-effort — a crash before completion
   leaves a non-compressed archive that the next startup discovers and
   compresses on the next rotation tick.
5. Opens a fresh live file and writes the deferred row.
6. Triggers retention sweep: any archive older than ``retention_days`` is
   moved into ``research/archive/{base}/{YYYY-MM}/{filename}`` so the
   working directory stays bounded but no data is destroyed.

Crash safety
------------
* **Atomic rename**: rotation never produces a half-written archive — either
  the rename succeeded (full archive on disk) or it didn't (live file
  unchanged). Both states are recoverable.
* **Background gzip**: if the gzip thread dies mid-stream, an uncompressed
  ``{base}_{date}.jsonl`` sits next to the gzipped archives. ``_compress_pending``
  scans for these on every rotation and re-compresses them.
* **Shared lock file**: each live JSONL has a sibling ``.lock`` file used only
  for advisory locking. A process crash closes the file handle and releases the
  OS lock; the lock file itself is harmless durable metadata.
* **Concurrent writers**: when two processes share a base path, both writers
  serialize the rotate-and-append critical section through the shared lock file.
  ``os.replace`` remains the atomic rotation primitive, and the append happens
  only after rotation is settled for that row.

Out of scope
------------
* In-process row buffering / batching — every ``write`` flushes to disk so
  the writer behaves like ``open(..., "a")`` for crash visibility.
* Compaction / dedup of the live file. Loggers should treat each row as
  immutable history.
* Per-row schema enforcement — that lives in the calling logger.

Reference
---------
* Audit triage 2026-04-26: "hybrid rotation (size-based + time-based);
  retention: keep last N days; archive older; don't lose data".
* CEO directive 2026-04-26: "do things the right way dont just patch".
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

try:  # pragma: no cover - platform-specific import
    import msvcrt
except ImportError:  # pragma: no cover
    msvcrt = None  # type: ignore[assignment]

try:  # pragma: no cover - platform-specific import
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# Default size-trigger threshold (MB). Empirically the structure-detector
# log was crossing 20+ MB at the 6-week mark; 50 MB gives ~2.5 daily worth
# of headroom while keeping single archive sizes manageable.
_DEFAULT_SIZE_MB: int = 50

# Default daily-archive retention horizon (days). 14 days is enough to
# preserve ~2 weeks of live structure-detector divergences for ADR-004
# v2_shadow vs v2 comparison; older archives roll out to research/archive.
_DEFAULT_RETENTION_DAYS: int = 14

# Default offsite archive root (relative to project root). Out-of-retention
# files move here permanently, partitioned by YYYY-MM so a 6-month archive
# is six folders not 180 files.
_DEFAULT_ARCHIVE_DIR_FMT: str = "research/archive/{base}"


# ---------------------------------------------------------------------------
# Helpers (pure functions for ease of testing)
# ---------------------------------------------------------------------------


def _utc_today_iso() -> str:
    """Return UTC today in ``YYYY-MM-DD`` form."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_yesterday_iso() -> str:
    """Return UTC yesterday in ``YYYY-MM-DD`` form."""
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _file_mtime_utc_date(path: Path) -> Optional[str]:
    """Return the file's mtime UTC date as ``YYYY-MM-DD``, or ``None`` if missing."""
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    return datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")


def _archive_name(live_path: Path, date_iso: str) -> Path:
    """Return the archive path next to the live file: ``{base}_{date}.jsonl``.

    Example: ``shadow_logs/foo.jsonl`` + ``2026-04-25`` →
    ``shadow_logs/foo_2026-04-25.jsonl``.
    """
    base = live_path.stem
    suffix = live_path.suffix or ".jsonl"
    parent = live_path.parent
    return parent / f"{base}_{date_iso}{suffix}"


def _compressed_name(archive_path: Path) -> Path:
    """Return ``{archive}.gz`` for a given uncompressed archive path."""
    return archive_path.with_suffix(archive_path.suffix + ".gz")


def _archive_age_days(archive_filename: str, base_stem: str) -> Optional[int]:
    """Return integer days since the date encoded in ``base_stem_YYYY-MM-DD.jsonl[.gz]``.

    Returns ``None`` if the filename does not match the expected pattern
    (defensive — a foreign file in the archive dir should not crash the
    retention sweep).
    """
    # Strip any compression suffix.
    name = archive_filename
    if name.endswith(".gz"):
        name = name[:-3]
    if not name.startswith(f"{base_stem}_"):
        return None
    if not name.endswith(".jsonl"):
        return None
    date_part = name[len(base_stem) + 1 : -len(".jsonl")]
    if len(date_part) != 10:
        return None
    try:
        archive_date = datetime.strptime(date_part, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None
    delta = datetime.now(timezone.utc).date() - archive_date.date()
    return delta.days


def _gzip_in_place(src: Path, dst: Optional[Path] = None) -> Path:
    """Gzip ``src`` to ``dst`` (default ``{src}.gz``) and remove ``src`` on success.

    Returns the resulting compressed Path on success, or raises on I/O failure.
    The caller is responsible for swallowing exceptions if it does not want
    a gzip failure to surface — this function intentionally raises so the
    background thread can log the error without swallowing it silently.
    """
    if dst is None:
        dst = _compressed_name(src)
    # Open both files; gzip the source into the destination. Read in chunks
    # so a multi-MB file doesn't blow up RSS.
    with src.open("rb") as f_in, gzip.open(str(dst), "wb") as f_out:
        shutil.copyfileobj(f_in, f_out, length=1024 * 1024)
    # Sanity-check the gzip wrote successfully (non-zero size).
    if dst.stat().st_size == 0:
        raise OSError(
            f"gzip produced an empty archive: {dst} (source was {src.stat().st_size}B)"
        )
    src.unlink()
    return dst


class _CrossProcessFileLock:
    """Advisory lock for writers sharing one JSONL path across processes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle: Any = None

    def __enter__(self) -> "_CrossProcessFileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+b")
        self._handle.seek(0)
        if msvcrt is not None:
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_LOCK, 1)
        elif fcntl is not None:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._handle is None:
            return
        try:
            self._handle.seek(0)
            if msvcrt is not None:
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            elif fcntl is not None:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None


# ---------------------------------------------------------------------------
# RotatingJsonlWriter
# ---------------------------------------------------------------------------


class RotatingJsonlWriter:
    """Append-only JSONL writer with hybrid (size + time) rotation.

    Usage::

        writer = RotatingJsonlWriter(
            base_path="shadow_logs/structure_detector_divergences.jsonl",
            size_mb=50,
            retention_days=14,
            archive_dir="research/archive/structure_detector_divergences",
        )
        writer.write(row_dict)        # one JSON-encoded row per call

    The writer is **lazy** — it does not open a file handle until the first
    ``write`` call. Construction is therefore safe at module-import time.

    Thread safety
    -------------
    Every public method acquires ``self._lock``. Concurrent calls across
    threads in the same process are serialized. Concurrent processes that
    share a base path also share a sibling ``.lock`` file, which serializes
    the rotate-and-append critical section. The lock avoids relying on
    platform-specific append atomicity for multi-process shadow log writers.
    """

    # ----- construction ------------------------------------------------------

    def __init__(
        self,
        base_path: str | os.PathLike,
        *,
        size_mb: int = _DEFAULT_SIZE_MB,
        retention_days: int = _DEFAULT_RETENTION_DAYS,
        archive_dir: Optional[str | os.PathLike] = None,
        gzip_async: bool = True,
        clock: Optional[callable] = None,
    ) -> None:
        """Configure the writer (does NOT open the file).

        Args:
            base_path: live JSONL path (e.g.
                ``"shadow_logs/structure_detector_divergences.jsonl"``).
                Parent directory created on first write.
            size_mb: rotation threshold in MB. Must be > 0. Default 50.
            retention_days: number of recent daily archives to keep next to
                the live file before sweeping to ``archive_dir``. Default 14.
            archive_dir: out-of-retention archive root. Default
                ``"research/archive/{base}"`` where ``{base}`` is the live
                file's stem (i.e. filename without extension).
            gzip_async: if True (default), gzip runs in a daemon thread so
                rotation does not block the caller. Set False in tests for
                deterministic behaviour.
            clock: callable returning a tz-aware UTC ``datetime`` — only
                used by tests that simulate UTC midnight crossing without
                manipulating the system clock. Defaults to
                ``datetime.now(timezone.utc)``.
        """
        if size_mb <= 0:
            raise ValueError(f"size_mb must be > 0, got {size_mb!r}")
        if retention_days < 0:
            raise ValueError(
                f"retention_days must be >= 0, got {retention_days!r}"
            )

        self.base_path: Path = Path(base_path)
        self.size_bytes: int = int(size_mb) * 1024 * 1024
        self.retention_days: int = int(retention_days)

        if archive_dir is None:
            archive_dir = _DEFAULT_ARCHIVE_DIR_FMT.format(base=self.base_path.stem)
        self.archive_dir: Path = Path(archive_dir)

        self.gzip_async: bool = bool(gzip_async)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

        self._lock = threading.RLock()
        self._lock_path = self.base_path.with_suffix(self.base_path.suffix + ".lock")

        # Track active gzip threads for tests that want to wait for them.
        self._gzip_threads: list[threading.Thread] = []

    # ----- public API --------------------------------------------------------

    def write(self, row: dict[str, Any]) -> None:
        """Append ``row`` to the live JSONL file, rotating first if necessary.

        **Raises** on I/O failure. Callers (shadow loggers) wrap this in their
        own try/except so each logger can keep its existing warning wording
        (for example, "STRUCTURE_DIVERGENCE: failed to write") and the writer
        does not double-log.

        Rotation/retention exceptions are caught internally because they are
        best-effort housekeeping; only the actual row append surfaces.
        """
        with self._lock:
            self._ensure_parent()
            row_bytes = (json.dumps(row) + "\n").encode("utf-8")
            with _CrossProcessFileLock(self._lock_path):
                try:
                    if self._should_rotate(prospective_bytes=len(row_bytes)):
                        self._rotate()
                except Exception as e:  # pragma: no cover - defensive
                    # Rotation is best-effort; keep going and let the row append
                    # to the existing live file if it survives. The next attempt
                    # will retry rotation.
                    logger.warning(
                        "RotatingJsonlWriter(%s): rotation failed (continuing): %s",
                        self.base_path,
                        e,
                    )
                # Append-mode write. Re-opens on every call to avoid stale
                # handles after rotation (cheap: kernel cache makes this <1ms).
                # NOTE: use builtins.open (not Path.open) so existing test
                # patterns that monkeypatch ``builtins.open`` to simulate
                # disk-full / permission errors still work. Path.open uses
                # io.open directly on Python 3.12+ and bypasses the patch.
                with open(self.base_path, "ab") as f:
                    f.write(row_bytes)
                    f.flush()
                    os.fsync(f.fileno())
                # After a write that crossed a daily boundary, mark mtime so
                # subsequent rotations see the freshly-written file.
                # (open() updates mtime automatically; no extra work needed.)

    def force_rotate(self) -> None:
        """Trigger an immediate rotation regardless of size/time triggers.

        Used by integration tests to assert rotation effects without
        having to reach the size threshold.
        """
        with self._lock:
            self._ensure_parent()
            with _CrossProcessFileLock(self._lock_path):
                if self.base_path.exists() and self.base_path.stat().st_size > 0:
                    self._rotate()

    def join_gzip(self, timeout: float = 30.0) -> None:
        """Block until all background gzip threads have finished.

        Tests use this to assert deterministic post-rotation state.
        """
        with self._lock:
            threads = list(self._gzip_threads)
        for t in threads:
            t.join(timeout)
        with self._lock:
            self._gzip_threads = [t for t in self._gzip_threads if t.is_alive()]

    # ----- internals ---------------------------------------------------------

    def _ensure_parent(self) -> None:
        self.base_path.parent.mkdir(parents=True, exist_ok=True)

    def _should_rotate(self, *, prospective_bytes: int) -> bool:
        """Return True if a write of ``prospective_bytes`` should rotate first."""
        if not self.base_path.exists():
            return False
        try:
            current_size = self.base_path.stat().st_size
        except FileNotFoundError:
            return False
        # Size trigger: rotate if next write would exceed the threshold.
        # NOTE: empty files (size=0) cannot trip the size trigger, since
        # rotating an empty file produces an empty archive.
        if current_size > 0 and current_size + prospective_bytes > self.size_bytes:
            return True
        # Time trigger: rotate if the live file's mtime UTC date is before
        # today's UTC date (i.e. we crossed UTC midnight since the last write).
        # Skip for empty files (no day to archive).
        if current_size == 0:
            return False
        live_date = _file_mtime_utc_date(self.base_path)
        today = self._clock().strftime("%Y-%m-%d")
        if live_date is not None and live_date < today:
            return True
        return False

    def _rotate(self) -> None:
        """Atomic rename live → archive + schedule gzip + sweep retention.

        Caller must hold ``self._lock``.
        """
        if not self.base_path.exists():
            return

        # Determine archive date: prefer the live file's mtime date so a
        # rotation triggered by a fresh write at 00:00:05 UTC archives the
        # *previous* day's data correctly.
        live_date = _file_mtime_utc_date(self.base_path)
        if live_date is None:
            live_date = self._clock().strftime("%Y-%m-%d")

        archive_path = _archive_name(self.base_path, live_date)
        # If an archive for today already exists (multiple rotations on a
        # single day due to size triggers), append a numeric suffix so we
        # don't overwrite. ``base_2026-04-25.jsonl`` -> ``base_2026-04-25_1.jsonl``.
        if archive_path.exists() or _compressed_name(archive_path).exists():
            counter = 1
            while True:
                stem = archive_path.stem
                suffix = archive_path.suffix
                candidate = archive_path.parent / f"{stem}_{counter}{suffix}"
                if (
                    not candidate.exists()
                    and not _compressed_name(candidate).exists()
                ):
                    archive_path = candidate
                    break
                counter += 1

        # Atomic rename: either the live file moved or it didn't. No half
        # state.
        try:
            os.replace(str(self.base_path), str(archive_path))
        except FileNotFoundError:
            # Concurrent rotation already moved the file. Fine; just open
            # a new live file on the next write.
            return

        # Schedule background compression. We re-scan for any pending
        # uncompressed archives in the same dir so a previously-aborted
        # compression gets retried on the next rotation tick.
        self._compress_pending()

        # Apply retention horizon AFTER compression scheduling so the
        # retention sweep sees up-to-date filenames.
        try:
            self._apply_retention()
        except Exception as e:  # pragma: no cover — defensive
            logger.warning(
                "RotatingJsonlWriter(%s): retention sweep failed: %s",
                self.base_path,
                e,
            )

    def _compress_pending(self) -> None:
        """Compress any uncompressed daily archives sitting next to the live file."""
        base_stem = self.base_path.stem
        suffix = self.base_path.suffix or ".jsonl"
        # Pattern: {base_stem}_*{suffix} that is NOT the live file.
        for entry in sorted(self.base_path.parent.glob(f"{base_stem}_*{suffix}")):
            # Skip directories defensively.
            if not entry.is_file():
                continue
            # Skip already-compressed siblings.
            if _compressed_name(entry).exists():
                continue
            self._schedule_gzip(entry)

    def _schedule_gzip(self, src: Path) -> None:
        """Run gzip in a background daemon thread (unless gzip_async=False)."""
        if not self.gzip_async:
            try:
                _gzip_in_place(src)
            except Exception as e:  # pragma: no cover — defensive
                logger.warning(
                    "RotatingJsonlWriter(%s): synchronous gzip failed for %s: %s",
                    self.base_path,
                    src,
                    e,
                )
            return

        def _worker():
            try:
                _gzip_in_place(src)
            except Exception as e:  # pragma: no cover — defensive
                logger.warning(
                    "RotatingJsonlWriter(%s): background gzip failed for %s: %s",
                    self.base_path,
                    src,
                    e,
                )

        t = threading.Thread(
            target=_worker,
            daemon=True,
            name=f"gzip-{src.name}",
        )
        t.start()
        self._gzip_threads.append(t)

    def _apply_retention(self) -> None:
        """Move archives older than ``retention_days`` to ``archive_dir``."""
        if self.retention_days <= 0:
            # retention_days==0 disables sweep (everything stays in place).
            return

        base_stem = self.base_path.stem
        suffix = self.base_path.suffix or ".jsonl"
        # Match both compressed and uncompressed archives.
        patterns = (f"{base_stem}_*{suffix}", f"{base_stem}_*{suffix}.gz")
        for pattern in patterns:
            for entry in self.base_path.parent.glob(pattern):
                if not entry.is_file():
                    continue
                age_days = _archive_age_days(entry.name, base_stem)
                if age_days is None:
                    # Foreign file or unparseable date — leave alone.
                    continue
                if age_days <= self.retention_days:
                    continue
                # Move to {archive_dir}/{YYYY-MM}/{filename}.
                # Date is encoded in the filename; extract for partitioning.
                # Strip leading {base_stem}_ + trailing {.jsonl[.gz]}.
                name = entry.name
                if name.endswith(".gz"):
                    name = name[:-3]
                date_part = name[len(base_stem) + 1 : -len(".jsonl")]
                year_month = date_part[:7]  # "YYYY-MM"
                dest_dir = self.archive_dir / year_month
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / entry.name
                try:
                    shutil.move(str(entry), str(dest))
                except shutil.Error as e:
                    logger.warning(
                        "RotatingJsonlWriter(%s): retention move %s -> %s failed: %s",
                        self.base_path,
                        entry,
                        dest,
                        e,
                    )

    # ----- maintenance helpers (used by tests / startup hooks) --------------

    def cleanup_pending(self) -> None:
        """Public hook to compress any leftover uncompressed archives.

        Useful at process startup if a previous run died mid-compression.
        Safe to call repeatedly.
        """
        with self._lock:
            self._compress_pending()
            self._apply_retention()

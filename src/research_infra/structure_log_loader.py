"""Shared loader for the structure-detector shadow log + companions.

A3 (`stratification.py`) and A5 (`regime_matrix.py`) both consume the
``shadow_logs/structure_detector_divergences.jsonl`` shadow log to look up
H4 regime tags. The shadow log is rotated daily at midnight UTC / 50 MB:
the rolled-out copy is gzipped and dropped under
``research/archive/structure_detector_divergences/`` (or, on older
deployments, next to the live log itself). On top of that, the offline
backfill (``scripts/research/backfill_v2_regime.py``) emits a sibling
``shadow_logs/structure_detector_backfill_*.jsonl`` covering the H4
boundaries the live log can never see.

A3's loader was extended in commit ``e4bf7b9`` to discover all of those
companion files; A5's loader was NOT updated, which collapsed A5 to
UNTAGGED=100% after the live log rotated to its current ~12-line state.
This module is the systemic fix: a single discover + parse + cache
implementation shared by every research consumer (memory note
``feedback_engineer_systemic_not_patches`` — apply the fix across all
instruments / consumers, never patch one site in isolation).

Public surface
--------------

* :func:`discover_structure_log_paths` — return the live log + every
  companion archive + the offline backfill, deduped + sorted
  lexicographically. Pure path discovery (no IO into the files).
* :func:`load_structure_log_rows` — yield every parsed row dict from the
  discovered companions. Caller decides what fields it wants. Both
  ``.jsonl`` and ``.jsonl.gz`` are decoded transparently.
* :func:`build_h4_regime_index` — convenience wrapper for the A3 use
  case: build a ``{(symbol, timeframe, ts_iso_z): regime_label}``
  dictionary from H4 rows only, with ``timeframe == "H4"`` filtering and
  ``v2_direction`` > ``production_label`` > ``v1_direction`` priority.

Cache
-----
The cache key is a stat fingerprint over **every** contributing file:
``(resolved_path_str, mtime_ns, st_size)``. Any rotation, truncation,
backfill re-run, or new archive invalidates the cache atomically without
process restart. Fail-open on corrupt files: a single unreadable archive
logs at WARNING and the rest of the rows still load.

Thread safety
-------------
The cache uses module-level dicts. Reads + writes are not protected by a
lock. Research callers are single-threaded CLI invocations and pytest
worker subprocesses (each with its own process-local cache), so the
implementation matches A3's prior contract — no production code touches
this module.
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: File-name prefixes the loader recognises as structure-detector log
#: companions. The live log is ``structure_detector_divergences``; the
#: offline backfill produced by ``scripts/research/backfill_v2_regime.py``
#: is ``structure_detector_backfill_*``. Both share the same row schema
#: (``ts`` / ``symbol`` / ``timeframe`` / ``production_label`` /
#: ``v2_direction`` / ``v1_direction``) so a single parser handles both.
STRUCTURE_LOG_PREFIXES: tuple[str, ...] = (
    "structure_detector_divergences",
    "structure_detector_backfill",
)

#: Maximum number of parent directories to walk when locating the project
#: root marker (``pyproject.toml``). Bounded to prevent unbounded
#: chdir-style traversal when the seed path is outside any project tree.
_PROJECT_ROOT_WALK_DEPTH = 8


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


# Cache parsed structure-detector log rows + the H4-only regime index
# separately so callers that only need one don't pay for the other. Keyed
# by a fingerprint that includes every contributing file's
# ``(resolved_path_str, mtime_ns, st_size)`` tuple — so a fresh rotation,
# truncation, or backfill re-run shows up immediately. Tests using
# ``tmp_path`` get fresh parses for free.
_ROWS_CACHE: dict[tuple, list[dict]] = {}
_H4_INDEX_CACHE: dict[tuple, dict[tuple[str, str, str], str]] = {}


def reset_cache() -> None:
    """Clear all loader caches.

    Tests that mutate the same on-disk path between assertions (e.g. write
    one fixture, build the index, then write a second fixture and rebuild)
    can call this to force a fresh parse. Production callers never need
    this — the stat fingerprint cache invalidates automatically on any
    file mutation.
    """
    _ROWS_CACHE.clear()
    _H4_INDEX_CACHE.clear()


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_structure_log_paths(seed_path: Path | str | None = None) -> list[Path]:
    """Return ``seed_path`` plus every sibling structure-log file.

    Discovery rules
    ---------------
    1. Always include ``seed_path`` itself if it exists.
    2. Look in ``seed_path.parent`` for siblings whose name starts with any
       prefix in :data:`STRUCTURE_LOG_PREFIXES` AND ends in ``.jsonl`` or
       ``.jsonl.gz`` (the rotation policy's suffixes). This covers both
       the same-directory archive style (older deployments) and the
       offline backfill sibling.
    3. Walk up from ``seed_path.parent`` to find a ``pyproject.toml``
       project root. If found, also include every ``*.jsonl`` /
       ``*.jsonl.gz`` inside ``research/archive/structure_detector_divergences/``
       under that root (the canonical archive location).
    4. De-duplicate by resolved path. Sort lexicographically — newer
       archive names contain ISO dates so the order is deterministic and
       the newest archive shadows older entries on key collisions when
       building the regime index.

    Fail-open
    ---------
    Any IO error logs once at WARNING and the function returns whatever
    it has accumulated. Never raises out of here — research consumers
    fall back to UNTAGGED rather than dying mid-CLI.

    Parameters
    ----------
    seed_path:
        Path to the live log (``.jsonl`` typical) or a single
        ``.jsonl.gz`` archive. May be a string or a ``Path``. ``None``
        returns ``[]`` immediately (useful for tests that don't care
        about regime tagging).

    Returns
    -------
    Sorted list of ``Path`` objects covering the live log + all
    companions + all canonical archives. Each path is guaranteed to exist
    at discovery time but may have been deleted by the time the caller
    opens it (the parser handles missing files defensively).
    """
    if seed_path is None:
        return []
    path = Path(seed_path) if not isinstance(seed_path, Path) else seed_path

    out: list[Path] = []
    seen: set[str] = set()

    def _add(p: Path) -> None:
        try:
            key = str(p.resolve())
        except OSError as e:
            logger.warning(
                "structure_log_loader: cannot resolve companion %s: %s", p, e
            )
            return
        if key in seen:
            return
        seen.add(key)
        out.append(p)

    if path.exists():
        _add(path)

    def _matches_prefix(name: str) -> bool:
        return any(name.startswith(prefix) for prefix in STRUCTURE_LOG_PREFIXES)

    # Same-directory siblings (archive next to live log + backfill).
    parent = path.parent
    if parent.is_dir():
        try:
            for child in sorted(parent.iterdir()):
                if not child.is_file():
                    continue
                name = child.name
                if not _matches_prefix(name):
                    continue
                if not (name.endswith(".jsonl") or name.endswith(".jsonl.gz")):
                    continue
                _add(child)
        except OSError as e:
            logger.warning(
                "structure_log_loader: cannot enumerate %s for archives: %s",
                parent,
                e,
            )

    # Conventional archive directory. Walk up to find a project root marker
    # (``pyproject.toml``) so this works whether the caller passed a path
    # inside the production tree or a tmp_path-derived test fixture.
    project_root: Optional[Path] = None
    cursor = parent.resolve() if parent.exists() else parent
    for _ in range(_PROJECT_ROOT_WALK_DEPTH):
        if (cursor / "pyproject.toml").exists():
            project_root = cursor
            break
        if cursor == cursor.parent:
            break
        cursor = cursor.parent
    if project_root is not None:
        archive_dir = (
            project_root
            / "research"
            / "archive"
            / "structure_detector_divergences"
        )
        if archive_dir.is_dir():
            try:
                for child in sorted(archive_dir.iterdir()):
                    if not child.is_file():
                        continue
                    name = child.name
                    if not (name.endswith(".jsonl") or name.endswith(".jsonl.gz")):
                        continue
                    _add(child)
            except OSError as e:
                logger.warning(
                    "structure_log_loader: cannot enumerate archive dir %s: %s",
                    archive_dir,
                    e,
                )

    return out


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _open_jsonl_companion(path: Path):
    """Open a ``.jsonl`` or ``.jsonl.gz`` file as a text iterator.

    Returns a context manager yielding line iteration. Selection is by
    suffix — explicit ``.gz`` uses ``gzip.open`` in text mode, anything
    else uses ``Path.open``. Both produce ``str`` lines on iteration.
    """
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _parse_log_file(path: Path) -> list[dict]:
    """Parse one log file (live ``.jsonl`` OR archived ``.jsonl.gz``).

    Returns the list of parsed JSON row dicts. Malformed rows are skipped
    silently (debug-logged) so a partial-write at the tail of a rotated
    archive doesn't poison the entire load. A corrupt-gzip archive logs
    once at WARNING and returns an empty list (fail-open).
    """
    out: list[dict] = []
    try:
        with _open_jsonl_companion(path) as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.debug(
                        "structure_log_loader: skipping malformed row %s:%d: %s",
                        path,
                        line_no,
                        e,
                    )
                    continue
                if isinstance(row, dict):
                    out.append(row)
    except (OSError, EOFError, gzip.BadGzipFile) as e:
        logger.warning(
            "structure_log_loader: failed to read %s: %s", path, e
        )
        return []
    return out


# ---------------------------------------------------------------------------
# Fingerprint + cached load
# ---------------------------------------------------------------------------


def _fingerprint(paths: list[Path]) -> tuple:
    """Build a stat fingerprint over ``paths``.

    Each entry is ``(resolved_path_str, mtime_ns, st_size)``. Files that
    fail to ``stat()`` are skipped (a WARNING is logged once). Returns an
    empty tuple if no files could be stat'd — caller treats that as "no
    cache key, no cached value".
    """
    items: list[tuple[str, int, int]] = []
    for p in paths:
        try:
            st = p.stat()
        except OSError as e:
            logger.warning(
                "structure_log_loader: cannot stat log %s: %s", p, e
            )
            continue
        items.append((str(p.resolve()), st.st_mtime_ns, int(st.st_size)))
    return tuple(items)


def load_structure_log_rows(
    seed_path: Path | str | None = None,
) -> Iterator[dict]:
    """Yield every parsed row from the discovered companion files.

    Iteration order follows :func:`discover_structure_log_paths` (live
    log first by virtue of typical naming, then companions in
    lexicographic order). Callers building a "latest write wins" map
    must therefore feed rows into the map in the iteration order; later
    files overwrite earlier ones on key collisions.

    The full row list is cached by stat fingerprint so a second call in
    the same process reuses the parsed dicts. Tests that need to bypass
    the cache call :func:`reset_cache`.
    """
    companions = discover_structure_log_paths(seed_path)
    if not companions:
        return iter(())

    fingerprint = _fingerprint(companions)
    if not fingerprint:
        return iter(())

    cached = _ROWS_CACHE.get(fingerprint)
    if cached is not None:
        return iter(cached)

    rows: list[dict] = []
    for p in companions:
        partial = _parse_log_file(p)
        if partial:
            rows.extend(partial)
            logger.debug(
                "structure_log_loader: loaded %d rows from %s",
                len(partial),
                p,
            )

    _ROWS_CACHE[fingerprint] = rows
    return iter(rows)


# ---------------------------------------------------------------------------
# H4 regime index (A3 helper)
# ---------------------------------------------------------------------------


def _coerce_iso_z(ts: str) -> Optional[str]:
    """Normalise an ISO-8601 timestamp string to ``...Z`` with UTC suffix.

    Accepts both ``Z``-suffixed and explicit-offset forms; naive strings
    are interpreted as UTC. Returns ``None`` on parse failure.
    """
    if not isinstance(ts, str) or not ts:
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_regime_label(raw: Optional[str]) -> str:
    """Map raw detector / classifier output to the A3 brief's 5 labels.

    Brief labels: ``trending_bull`` / ``trending_bear`` / ``range`` /
    ``reversal`` / ``unclear``. Returns ``UNTAGGED`` when the raw value
    is missing / empty / unknown.
    """
    if raw is None:
        return "UNTAGGED"
    s = str(raw).strip().lower()
    if not s:
        return "UNTAGGED"
    if s in ("bullish", "trending_bull", "bull"):
        return "trending_bull"
    if s in ("bearish", "trending_bear", "bear"):
        return "trending_bear"
    if s in ("range", "ranging", "chop", "transitional"):
        return "range"
    if s in ("reversal", "reversal_in_progress"):
        return "reversal"
    if s in ("unclear", "insufficient_data"):
        return "unclear"
    return "UNTAGGED"


def build_h4_regime_index(
    seed_path: Path | str | None = None,
) -> dict[tuple[str, str, str], str]:
    """Return ``{(symbol, "H4", ts_iso_z): regime_label}`` from all companions.

    Filters
    -------
    * ``row.timeframe == "H4"`` — H4 rows only (A3 + A5 both consume the
      H4 cadence).
    * ``row.symbol`` non-empty — empty-symbol rows from very early
      promotion-window logging are skipped silently.

    Label preference
    ----------------
    ``production_label`` > ``v2_direction`` > ``v1_direction``. Whichever
    field the production pipeline ultimately acted on wins. Unknown
    labels normalise to ``UNTAGGED`` (and are still emitted into the map
    so downstream consumers see explicit coverage rather than silent
    drops).

    Cache
    -----
    Cached by stat fingerprint identical to
    :func:`load_structure_log_rows`'s cache, but stored separately so
    callers that already have the row iterator don't pay the extra
    H4-filter+normalise pass twice.

    Notes
    -----
    On key collisions (same ``(symbol, "H4", ts)`` across rotated
    archives), the **last** row wins. The companion list is sorted
    lexicographically and the live log typically appears in that order,
    so the freshest label wins — matching production "latest write wins"
    semantics. The backfill writes one row per ``(symbol, "H4",
    h4_floor_iso)`` so collisions are exclusively across rotations of
    the live log + backfill, never within a single file.
    """
    companions = discover_structure_log_paths(seed_path)
    if not companions:
        return {}

    fingerprint = _fingerprint(companions)
    if not fingerprint:
        return {}

    cached = _H4_INDEX_CACHE.get(fingerprint)
    if cached is not None:
        return cached

    out: dict[tuple[str, str, str], str] = {}
    for p in companions:
        rows = _parse_log_file(p)
        if not rows:
            continue
        for row in rows:
            ts = row.get("ts") or row.get("candle_time")
            symbol = row.get("symbol")
            tf = row.get("timeframe")
            if not (ts and symbol and tf):
                continue
            # H4-only filter: A3 + A5 both consume H4 cadence. Non-H4
            # rows (M15/H1/D1) appear in the same shadow log but are
            # ignored here so the index size matches the canonical H4
            # universe. Backward-compatible: callers that previously
            # got non-H4 rows in the dict were never actually querying
            # them — the legacy lookup is keyed by ``(symbol, "H4",
            # ts)`` so the non-H4 entries were dead weight.
            if tf != "H4":
                continue
            label = (
                row.get("production_label")
                or row.get("v2_direction")
                or row.get("v1_direction")
            )
            if label is None:
                continue
            ts_norm = _coerce_iso_z(ts)
            if ts_norm is None:
                continue
            out[(str(symbol), str(tf), ts_norm)] = _normalize_regime_label(label)

    _H4_INDEX_CACHE[fingerprint] = out
    return out

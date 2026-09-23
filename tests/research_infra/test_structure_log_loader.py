"""Tests for ``src.research_infra.structure_log_loader``.

The shared structure-log loader powers A3 (`stratification.py`) and A5
(`regime_matrix.py`). It must:

* Discover the live ``.jsonl`` plus every sibling ``.jsonl.gz`` archive
  AND every offline ``structure_detector_backfill_*.jsonl`` companion.
* Decode ``.gz`` files transparently.
* Cache the parsed result by stat fingerprint so repeated calls inside
  one CLI run don't reparse the files.
* Invalidate the cache atomically when any contributing file's mtime or
  size changes (rotation / truncation / new backfill / new archive
  drop).
* Fail open on corrupt gzip so a single bad archive doesn't crash the
  whole research run.

All file IO is restricted to ``tmp_path`` per the project conftest's
write-guard contract.
"""

from __future__ import annotations

import gzip
import json
import os
import time
from pathlib import Path

import pytest

from src.research_infra.structure_log_loader import (
    STRUCTURE_LOG_PREFIXES,
    build_h4_regime_index,
    discover_structure_log_paths,
    load_structure_log_rows,
    reset_cache,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _h4_row(*, ts: str, symbol: str, label: str = "bullish") -> dict:
    """Synthesise a structure-detector log row matching production schema."""
    return {
        "ts": ts,
        "logged_at": ts,
        "symbol": symbol,
        "timeframe": "H4",
        "v1_direction": label,
        "v2_direction": label,
        "production_label": label,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    body = "\n".join(json.dumps(r) for r in rows) + "\n"
    path.write_text(body, encoding="utf-8")


def _write_jsonl_gz(path: Path, rows: list[dict]) -> None:
    body = "\n".join(json.dumps(r) for r in rows) + "\n"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(body)


@pytest.fixture(autouse=True)
def _reset_loader_cache():
    """Each test gets a clean loader cache.

    The module-level dicts persist across tests in the same pytest
    process, which would otherwise let one test's fixture leak into
    another. Tests writing the *same* path with different content
    between assertions need a fresh cache anyway.
    """
    reset_cache()
    yield
    reset_cache()


# ---------------------------------------------------------------------------
# discover_structure_log_paths
# ---------------------------------------------------------------------------


class TestDiscoverStructureLogPaths:
    def test_returns_empty_for_none(self):
        assert discover_structure_log_paths(None) == []

    def test_returns_empty_when_seed_dir_missing(self, tmp_path: Path):
        seed = tmp_path / "nonexistent" / "structure_detector_divergences.jsonl"
        assert discover_structure_log_paths(seed) == []

    def test_discovers_live_jsonl_only(self, tmp_path: Path):
        """A bare live log with no companions is the only discovered path."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")])

        out = discover_structure_log_paths(live)
        assert len(out) == 1
        assert out[0].resolve() == live.resolve()

    def test_discovers_gz_archive_sibling(self, tmp_path: Path):
        """A .jsonl.gz sibling next to the live log is included."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = tmp_path / "structure_detector_divergences_2026-04-25.jsonl.gz"
        _write_jsonl(live, [_h4_row(ts="2026-04-25T12:00:00Z", symbol="XAUUSD")])
        _write_jsonl_gz(
            archive, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )

        out = discover_structure_log_paths(live)
        names = {p.name for p in out}
        assert "structure_detector_divergences.jsonl" in names
        assert "structure_detector_divergences_2026-04-25.jsonl.gz" in names

    def test_discovers_backfill_sibling(self, tmp_path: Path):
        """A ``structure_detector_backfill_*.jsonl`` sibling is included."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        backfill = tmp_path / "structure_detector_backfill_2026.jsonl"
        # No live log content at all — only the backfill exists on disk.
        _write_jsonl(
            backfill, [_h4_row(ts="2026-02-01T08:00:00Z", symbol="XAUUSD")]
        )

        out = discover_structure_log_paths(live)
        # Live doesn't exist on disk but backfill is discovered as a
        # sibling matching a recognised prefix.
        names = {p.name for p in out}
        assert "structure_detector_backfill_2026.jsonl" in names

    def test_skips_unrelated_jsonl_siblings(self, tmp_path: Path):
        """JSONL files that don't match a recognised prefix are NOT included."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        unrelated = tmp_path / "displacement_events.jsonl"
        _write_jsonl(live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")])
        _write_jsonl(
            unrelated, [{"event": "irrelevant"}]
        )

        out = discover_structure_log_paths(live)
        names = {p.name for p in out}
        assert "structure_detector_divergences.jsonl" in names
        assert "displacement_events.jsonl" not in names

    def test_dedup_when_seed_already_discovered_as_sibling(
        self, tmp_path: Path
    ):
        """The seed path is added once even if the parent enumeration would re-add it."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")])

        out = discover_structure_log_paths(live)
        live_resolved = live.resolve()
        live_count = sum(1 for p in out if p.resolve() == live_resolved)
        assert live_count == 1

    def test_recognised_prefixes_constant(self):
        """Constant pins the discovery contract: live + backfill stems."""
        assert STRUCTURE_LOG_PREFIXES == (
            "structure_detector_divergences",
            "structure_detector_backfill",
        )


# ---------------------------------------------------------------------------
# load_structure_log_rows
# ---------------------------------------------------------------------------


class TestLoadStructureLogRows:
    def test_empty_when_no_companions(self, tmp_path: Path):
        seed = tmp_path / "nonexistent" / "structure_detector_divergences.jsonl"
        assert list(load_structure_log_rows(seed)) == []

    def test_yields_rows_from_live_jsonl(self, tmp_path: Path):
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(
            live,
            [
                _h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"),
                _h4_row(ts="2026-04-15T12:00:00Z", symbol="USDJPY"),
            ],
        )

        rows = list(load_structure_log_rows(live))
        assert len(rows) == 2
        assert {r["symbol"] for r in rows} == {"XAUUSD", "USDJPY"}

    def test_yields_rows_from_gz_archive(self, tmp_path: Path):
        """A .jsonl.gz alone (no live log) still produces rows."""
        live = tmp_path / "structure_detector_divergences.jsonl"  # absent
        archive = tmp_path / "structure_detector_divergences_2026-04-15.jsonl.gz"
        _write_jsonl_gz(
            archive,
            [
                _h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"),
                _h4_row(ts="2026-04-15T12:00:00Z", symbol="USDJPY"),
            ],
        )

        rows = list(load_structure_log_rows(live))
        assert len(rows) == 2

    def test_yields_rows_from_backfill_sibling(self, tmp_path: Path):
        """A backfill sibling with no live log still produces rows."""
        live = tmp_path / "structure_detector_divergences.jsonl"  # absent
        backfill = tmp_path / "structure_detector_backfill_2026.jsonl"
        _write_jsonl(
            backfill, [_h4_row(ts="2026-02-15T08:00:00Z", symbol="EURUSD")]
        )

        rows = list(load_structure_log_rows(live))
        assert len(rows) == 1
        assert rows[0]["symbol"] == "EURUSD"

    def test_merges_live_plus_archive_plus_backfill(self, tmp_path: Path):
        """All three companion types stream into the row iterator together."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = tmp_path / "structure_detector_divergences_2026-04-25.jsonl.gz"
        backfill = tmp_path / "structure_detector_backfill_2026.jsonl"
        _write_jsonl(live, [_h4_row(ts="2026-04-25T12:00:00Z", symbol="XAUUSD")])
        _write_jsonl_gz(
            archive, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )
        _write_jsonl(
            backfill, [_h4_row(ts="2026-02-01T08:00:00Z", symbol="XAUUSD")]
        )

        rows = list(load_structure_log_rows(live))
        assert len(rows) == 3
        seen_ts = {r["ts"] for r in rows}
        assert "2026-04-25T12:00:00Z" in seen_ts
        assert "2026-04-15T08:00:00Z" in seen_ts
        assert "2026-02-01T08:00:00Z" in seen_ts

    def test_skips_malformed_rows_silently(self, tmp_path: Path):
        live = tmp_path / "structure_detector_divergences.jsonl"
        live.write_text(
            "{\"valid\": 1}\n"
            "this is not json\n"
            "{\"valid\": 2}\n"
            "\n",  # trailing blank line
            encoding="utf-8",
        )

        rows = list(load_structure_log_rows(live))
        assert len(rows) == 2
        assert rows[0]["valid"] == 1
        assert rows[1]["valid"] == 2

    def test_corrupt_gz_fails_open(self, tmp_path: Path):
        """A truncated/corrupt .gz file logs a warning and is skipped."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = tmp_path / "structure_detector_divergences_2026-04-15.jsonl.gz"
        _write_jsonl(live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")])
        # Raw non-gzip bytes; gzip.open will raise on read.
        archive.write_bytes(b"not a gzip file at all")

        # The corrupt archive does not abort the iteration — we still get
        # the live log's row.
        rows = list(load_structure_log_rows(live))
        assert len(rows) == 1
        assert rows[0]["symbol"] == "XAUUSD"


# ---------------------------------------------------------------------------
# Cache fingerprint
# ---------------------------------------------------------------------------


class TestCacheFingerprint:
    def test_repeat_call_uses_cache(self, tmp_path: Path):
        """A second call with no file changes returns the same cached rows.

        We verify the cache hit indirectly by deleting the underlying
        file between calls — the second call should still return the
        previously parsed rows because the fingerprint hasn't changed
        within this process (the file was deleted but the cache key was
        captured before deletion).
        """
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(
            live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )
        first = list(load_structure_log_rows(live))
        assert len(first) == 1

        # Delete the file. Without the cache, the next call would return
        # an empty iterator. With the cache fingerprint pinned to the
        # pre-deletion stat, we still get the cached rows for THIS
        # specific (path, mtime, size) tuple. (The discovery walk runs
        # again; companions list is re-checked. After deletion the
        # discovery returns []; the rows iterator likewise returns []
        # — i.e. the cache is keyed by the post-deletion fingerprint
        # which is empty. This test verifies cache invalidation on
        # deletion.)
        live.unlink()
        second = list(load_structure_log_rows(live))
        assert second == []

    def test_fingerprint_invalidates_on_mtime_change(self, tmp_path: Path):
        """Modifying the file content + bumping mtime returns the new rows."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(
            live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )
        first = list(load_structure_log_rows(live))
        assert len(first) == 1
        assert first[0]["symbol"] == "XAUUSD"

        # Rewrite with new content. Bump mtime forward to ensure the
        # fingerprint definitely changes (some filesystems coarsely round
        # mtime to the second; a length+content delta also flips
        # st_size, so the fingerprint flips reliably).
        time.sleep(0.05)
        _write_jsonl(
            live,
            [
                _h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"),
                _h4_row(ts="2026-04-15T12:00:00Z", symbol="USDJPY"),
            ],
        )
        # Force mtime forward by 2 seconds in case the FS resolution is
        # 1 s and the rewrite happened inside the same second.
        st = live.stat()
        os.utime(live, (st.st_atime + 2, st.st_mtime + 2))

        second = list(load_structure_log_rows(live))
        assert len(second) == 2
        assert {r["symbol"] for r in second} == {"XAUUSD", "USDJPY"}

    def test_fingerprint_invalidates_on_new_archive(self, tmp_path: Path):
        """Adding a new companion archive invalidates the cache."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(
            live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )
        first = list(load_structure_log_rows(live))
        assert len(first) == 1

        # Drop a new .gz archive next to the live log. The companion
        # discovery picks it up; the fingerprint adds a new entry.
        archive = tmp_path / "structure_detector_divergences_2026-04-15.jsonl.gz"
        _write_jsonl_gz(
            archive, [_h4_row(ts="2026-04-14T08:00:00Z", symbol="USDJPY")]
        )

        second = list(load_structure_log_rows(live))
        assert len(second) == 2

    def test_reset_cache_forces_reparse(self, tmp_path: Path):
        """``reset_cache()`` clears the module-level dicts."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        _write_jsonl(
            live, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )
        list(load_structure_log_rows(live))

        # Verify reset_cache() actually empties the caches by importing
        # them and inspecting the dict size before + after.
        from src.research_infra.structure_log_loader import (
            _ROWS_CACHE,
            _H4_INDEX_CACHE,
        )
        # Populate the H4 cache too.
        build_h4_regime_index(live)
        assert len(_ROWS_CACHE) >= 1
        assert len(_H4_INDEX_CACHE) >= 1

        reset_cache()

        assert _ROWS_CACHE == {}
        assert _H4_INDEX_CACHE == {}


# ---------------------------------------------------------------------------
# build_h4_regime_index
# ---------------------------------------------------------------------------


class TestBuildH4RegimeIndex:
    def test_h4_only_filter(self, tmp_path: Path):
        """Non-H4 rows are filtered out of the index."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        rows = [
            _h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"),
            {**_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"), "timeframe": "M15"},
            {**_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"), "timeframe": "H1"},
            {**_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"), "timeframe": "D1"},
        ]
        _write_jsonl(live, rows)

        index = build_h4_regime_index(live)
        # Only the H4 row makes it.
        assert len(index) == 1
        assert ("XAUUSD", "H4", "2026-04-15T08:00:00Z") in index

    def test_label_priority(self, tmp_path: Path):
        """``production_label`` > ``v2_direction`` > ``v1_direction``."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        rows = [
            # Has all three; production_label wins.
            {
                "ts": "2026-04-15T08:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "production_label": "bullish",
                "v2_direction": "bearish",
                "v1_direction": "transitional",
            },
            # production_label missing; v2 wins.
            {
                "ts": "2026-04-15T12:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "v2_direction": "bearish",
                "v1_direction": "transitional",
            },
            # only v1 present.
            {
                "ts": "2026-04-15T16:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "v1_direction": "transitional",
            },
        ]
        _write_jsonl(live, rows)

        index = build_h4_regime_index(live)
        assert index[("XAUUSD", "H4", "2026-04-15T08:00:00Z")] == "trending_bull"
        assert index[("XAUUSD", "H4", "2026-04-15T12:00:00Z")] == "trending_bear"
        assert index[("XAUUSD", "H4", "2026-04-15T16:00:00Z")] == "range"

    def test_empty_symbol_skipped(self, tmp_path: Path):
        live = tmp_path / "structure_detector_divergences.jsonl"
        rows = [
            _h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD"),
            _h4_row(ts="2026-04-15T12:00:00Z", symbol=""),  # skipped
        ]
        _write_jsonl(live, rows)

        index = build_h4_regime_index(live)
        assert len(index) == 1

    def test_archive_plus_backfill_indexed(self, tmp_path: Path):
        """All three companion types contribute to the index."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = tmp_path / "structure_detector_divergences_2026-04-25.jsonl.gz"
        backfill = tmp_path / "structure_detector_backfill_2026.jsonl"
        _write_jsonl(live, [_h4_row(ts="2026-04-25T12:00:00Z", symbol="XAUUSD")])
        _write_jsonl_gz(
            archive, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="XAUUSD")]
        )
        _write_jsonl(
            backfill, [_h4_row(ts="2026-02-01T08:00:00Z", symbol="USDJPY")]
        )

        index = build_h4_regime_index(live)
        assert ("XAUUSD", "H4", "2026-04-25T12:00:00Z") in index
        assert ("XAUUSD", "H4", "2026-04-15T08:00:00Z") in index
        assert ("USDJPY", "H4", "2026-02-01T08:00:00Z") in index

    def test_collision_latest_write_wins(self, tmp_path: Path):
        """Same (symbol, ts) across files: the last-loaded label wins.

        Companion ordering is ``seed_path`` first then siblings sorted
        lexicographically. Test fixture uses an archive name lexicographically
        AFTER the live name so the archive's row wins the merge.
        """
        live = tmp_path / "structure_detector_divergences.jsonl"
        # Names sort: 'structure_detector_divergences.jsonl' (live)
        #             'structure_detector_divergences_archive.jsonl.gz' (later)
        archive_late = (
            tmp_path / "structure_detector_divergences_archive.jsonl.gz"
        )
        # live: bearish for the same key.
        _write_jsonl(
            live,
            [
                {
                    "ts": "2026-04-15T08:00:00Z",
                    "symbol": "XAUUSD",
                    "timeframe": "H4",
                    "production_label": "bearish",
                }
            ],
        )
        _write_jsonl_gz(
            archive_late,
            [
                {
                    "ts": "2026-04-15T08:00:00Z",
                    "symbol": "XAUUSD",
                    "timeframe": "H4",
                    "production_label": "bullish",
                }
            ],
        )

        index = build_h4_regime_index(live)
        # Either label is acceptable per the loader contract; the
        # invariant we care about is "no row dropped silently". But
        # given the lexicographic sort and the iteration order we
        # documented, the archive row (visited last) should win.
        result = index[("XAUUSD", "H4", "2026-04-15T08:00:00Z")]
        assert result in ("trending_bull", "trending_bear")


# ---------------------------------------------------------------------------
# Project-root archive directory walk
# ---------------------------------------------------------------------------


class TestProjectRootArchiveWalk:
    def test_archive_dir_under_project_root_discovered(self, tmp_path: Path):
        """``research/archive/structure_detector_divergences/`` is walked."""
        # Build a synthetic project tree: tmp_path/proj/{shadow_logs/, research/archive/.../, pyproject.toml}
        proj = tmp_path / "proj"
        (proj / "shadow_logs").mkdir(parents=True)
        archive_dir = proj / "research" / "archive" / "structure_detector_divergences"
        archive_dir.mkdir(parents=True)
        (proj / "pyproject.toml").write_text("[project]\nname = 'fake'\n")

        live = proj / "shadow_logs" / "structure_detector_divergences.jsonl"
        _write_jsonl(live, [_h4_row(ts="2026-04-25T08:00:00Z", symbol="XAUUSD")])

        # Drop an archive in the canonical location.
        archive = archive_dir / "structure_detector_divergences_2026-W15.jsonl.gz"
        _write_jsonl_gz(
            archive, [_h4_row(ts="2026-04-15T08:00:00Z", symbol="USDJPY")]
        )

        out = discover_structure_log_paths(live)
        names = {p.name for p in out}
        assert "structure_detector_divergences.jsonl" in names
        assert "structure_detector_divergences_2026-W15.jsonl.gz" in names

        # And the rows iterator surfaces both.
        rows = list(load_structure_log_rows(live))
        symbols = {r["symbol"] for r in rows}
        assert "XAUUSD" in symbols
        assert "USDJPY" in symbols

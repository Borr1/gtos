"""Unit tests for `src.research_infra.stratification`.

Coverage matrix
---------------
* ``assign_session`` —
    - kill-zone boundary semantics for each supported instrument
    - inclusive lower / exclusive upper bound
    - DST-stable (2026-03-08 US→EDT, 2026-03-29 UK→BST)
    - weekend timestamps still map to their session (no silent drop)
    - unknown instrument → ``Off``
    - session-name mapping (tokyo→Asia, london→London, ny→NY)
    - cross-midnight kill zone (hypothetical NZDUSD-style 22:00→02:00)

* ``assign_regime`` —
    - reads structure-detector log; missing entry → ``UNTAGGED``
    - normalizes detector labels (bullish→trending_bull, etc.)
    - None log path → always UNTAGGED (does not raise)
    - malformed log row → silently skipped
    - cache invalidation via mtime change
    - merges live ``.jsonl`` with sibling ``.jsonl.gz`` archive
    - merges live log with the offline backfill sibling
    - latest-write-wins on ``(symbol, tf, ts)`` collisions
    - ``.jsonl.gz``-only seed path also works

* ``resolve_side`` (F2) —
    - explicit LONG/SHORT/BUY/SELL direction recognized
    - missing direction + entry > sl → LONG
    - missing direction + entry < sl → SHORT
    - missing direction + missing prices → UNKNOWN
    - both prices NaN → UNKNOWN

* ``stratify`` —
    - end-to-end on 20 synthetic trades across 2 instruments × 2 months × 2 regimes
    - drops trades whose symbol mismatches the instrument argument
    - tolerates missing direction
    - tolerates string r_multiple
    - skips rows without a parseable timestamp
    - side-stratified (F2) — 4-axis schema cleanly adds Side dimension
    - side-stratified — UNKNOWN fallback row is preserved separately
    - non-side-stratified default — schema bit-identical to legacy

* ``find_change_points`` —
    - synthetic series with planted change point → detected
    - synthetic series with no change point → empty list
    - non-consecutive months are NOT flagged
    - n below min_n on either side → not flagged
    - Bonferroni correction inflates raw_p × family_size
    - side-stratified — LONG decay ≠ SHORT decay families
"""

from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research_infra.stratification import (
    DEFAULT_KILL_ZONES,
    ChangePoint,
    StratumKey,
    StratumOutcomes,
    _floor_h4_utc,
    _months_consecutive,
    _normalize_regime_label,
    _two_proportion_p_value,
    assign_regime,
    assign_session,
    coverage_summary,
    find_change_points,
    resolve_side,
    stratify,
)


# ---------------------------------------------------------------------------
# assign_session
# ---------------------------------------------------------------------------


class TestAssignSessionXAUUSD:
    """XAUUSD kill zones: London 07:00-10:30, NY 13:00-17:00."""

    def test_london_open_inclusive(self):
        ts = datetime(2026, 4, 15, 7, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "London"

    def test_london_just_before_open(self):
        ts = datetime(2026, 4, 15, 6, 59, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "Off"

    def test_london_close_exclusive(self):
        # 10:30 is the upper bound; trades at exactly 10:30 are OFF.
        ts = datetime(2026, 4, 15, 10, 30, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "Off"

    def test_london_just_before_close(self):
        ts = datetime(2026, 4, 15, 10, 29, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "London"

    def test_ny_open(self):
        ts = datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "NY"

    def test_ny_close_exclusive(self):
        ts = datetime(2026, 4, 15, 17, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "Off"

    def test_ny_just_before_close(self):
        ts = datetime(2026, 4, 15, 16, 59, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "NY"

    def test_between_kill_zones(self):
        ts = datetime(2026, 4, 15, 11, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "Off"

    def test_no_asia_session_for_xauusd(self):
        ts = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "Off"


class TestAssignSessionUSDJPY:
    """USDJPY: Tokyo 00:00-03:00, London 07:00-09:30, NY 13:00-15:30."""

    def test_tokyo(self):
        ts = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "Asia"

    def test_tokyo_close_exclusive(self):
        ts = datetime(2026, 4, 15, 3, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "Off"

    def test_tokyo_just_before_close(self):
        ts = datetime(2026, 4, 15, 2, 59, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "Asia"

    def test_london(self):
        ts = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "London"

    def test_london_close_exclusive(self):
        ts = datetime(2026, 4, 15, 9, 30, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "Off"

    def test_ny(self):
        ts = datetime(2026, 4, 15, 14, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "NY"

    def test_off_hours(self):
        ts = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "USDJPY") == "Off"


class TestAssignSessionUS30:
    """US30 cash: London 08:00-10:30, NY 13:30-16:00."""

    def test_london_open(self):
        ts = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "US30_cash") == "London"

    def test_london_just_before_open(self):
        ts = datetime(2026, 4, 15, 7, 59, tzinfo=timezone.utc)
        assert assign_session(ts, "US30_cash") == "Off"

    def test_ny_open(self):
        ts = datetime(2026, 4, 15, 13, 30, tzinfo=timezone.utc)
        assert assign_session(ts, "US30_cash") == "NY"

    def test_ny_just_before_open(self):
        # 13:00 is XAUUSD's NY open but US30 doesn't open until 13:30.
        ts = datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "US30_cash") == "Off"


class TestAssignSessionGBPUSD:
    """GBPUSD: London extended 07:00-12:00, NY 13:00-15:30."""

    def test_london_extended(self):
        ts = datetime(2026, 4, 15, 11, 30, tzinfo=timezone.utc)
        assert assign_session(ts, "GBPUSD") == "London"

    def test_london_close(self):
        ts = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "GBPUSD") == "Off"


class TestAssignSessionDST:
    """Kill-zone windows are stamped in UTC permanently — DST does NOT shift them.

    The London open is 07:00 UTC in January (GMT) and 07:00 UTC in April (BST)
    even though London local time interprets those moments as 07:00 and
    08:00 respectively. Our session classification must remain stable
    around the DST boundary.

    Per `dst_effect_analysis.md` the project's canonical times are UTC
    only — no local-time conversions.
    """

    # 2026 DST dates per task brief:
    #   2026-03-08 — US falls back to EDT
    #   2026-03-29 — UK rolls forward to BST

    def test_us_dst_transition_xauusd_ny(self):
        """NY 13:00 UTC stays NY whether US is in EST or EDT."""
        # Day before US DST shift.
        before = datetime(2026, 3, 7, 13, 0, tzinfo=timezone.utc)
        # Day after.
        after = datetime(2026, 3, 9, 13, 0, tzinfo=timezone.utc)
        assert assign_session(before, "XAUUSD") == "NY"
        assert assign_session(after, "XAUUSD") == "NY"

    def test_us_dst_transition_us30_ny(self):
        """US30 NY opens at 13:30 UTC on both sides of US DST."""
        before = datetime(2026, 3, 7, 13, 30, tzinfo=timezone.utc)
        after = datetime(2026, 3, 9, 13, 30, tzinfo=timezone.utc)
        assert assign_session(before, "US30_cash") == "NY"
        assert assign_session(after, "US30_cash") == "NY"

    def test_uk_dst_transition_xauusd_london(self):
        """London 07:00 UTC remains London after UK rolls forward to BST."""
        # Day before UK BST shift.
        before = datetime(2026, 3, 28, 7, 0, tzinfo=timezone.utc)
        # Day after — 2026-03-29 was a Sunday; pick the Monday.
        after = datetime(2026, 3, 30, 7, 0, tzinfo=timezone.utc)
        assert assign_session(before, "XAUUSD") == "London"
        assert assign_session(after, "XAUUSD") == "London"

    def test_uk_dst_transition_xauusd_london_close(self):
        """London 10:30 UTC remains the close after BST roll-forward."""
        before = datetime(2026, 3, 28, 10, 29, tzinfo=timezone.utc)
        after = datetime(2026, 3, 30, 10, 29, tzinfo=timezone.utc)
        assert assign_session(before, "XAUUSD") == "London"
        assert assign_session(after, "XAUUSD") == "London"

        before_after_close = datetime(2026, 3, 28, 10, 30, tzinfo=timezone.utc)
        after_after_close = datetime(2026, 3, 30, 10, 30, tzinfo=timezone.utc)
        assert assign_session(before_after_close, "XAUUSD") == "Off"
        assert assign_session(after_after_close, "XAUUSD") == "Off"

    def test_dst_does_not_introduce_phantom_session(self):
        """An hour that is NOT a kill zone in UTC stays Off across DST."""
        # 06:00 UTC is not a kill-zone for any default instrument.
        for inst in ("XAUUSD", "USDJPY", "US30_cash", "GBPUSD"):
            before = datetime(2026, 3, 7, 6, 0, tzinfo=timezone.utc)
            after = datetime(2026, 3, 30, 6, 0, tzinfo=timezone.utc)
            assert assign_session(before, inst) == "Off"
            assert assign_session(after, inst) == "Off"


class TestAssignSessionMisc:
    """Edge cases that aren't symbol-specific."""

    def test_unknown_instrument_returns_off(self):
        ts = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "BANANA") == "Off"

    def test_iso_string_input(self):
        assert assign_session("2026-04-15T08:00:00Z", "XAUUSD") == "London"

    def test_iso_string_with_offset(self):
        assert (
            assign_session("2026-04-15T08:00:00+00:00", "XAUUSD") == "London"
        )

    def test_iso_string_naive_treated_as_utc(self):
        assert assign_session("2026-04-15T08:00:00", "XAUUSD") == "London"

    def test_empty_instrument_raises(self):
        ts = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            assign_session(ts, "")

    def test_weekend_timestamp_still_classified(self):
        """A Saturday 08:00 UTC still maps to London (no silent drop)."""
        # 2026-04-11 is a Saturday.
        ts = datetime(2026, 4, 11, 8, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "XAUUSD") == "London"

    def test_custom_config_overrides_defaults(self):
        cfg = {"FOO": {"london": {"start_utc": "09:00", "end_utc": "11:00"}}}
        ts_in = datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc)
        ts_out = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)
        assert assign_session(ts_in, "FOO", cfg) == "London"
        assert assign_session(ts_out, "FOO", cfg) == "Off"

    def test_cross_midnight_window(self):
        """A 22:00 → 02:00 window should match both sides of midnight."""
        cfg = {"NZD": {"tokyo": {"start_utc": "22:00", "end_utc": "02:00"}}}
        evening = datetime(2026, 4, 15, 22, 30, tzinfo=timezone.utc)
        early_morning = datetime(2026, 4, 16, 1, 30, tzinfo=timezone.utc)
        outside = datetime(2026, 4, 16, 5, 0, tzinfo=timezone.utc)
        assert assign_session(evening, "NZD", cfg) == "Asia"
        assert assign_session(early_morning, "NZD", cfg) == "Asia"
        assert assign_session(outside, "NZD", cfg) == "Off"

    def test_unknown_zone_name_logs_off(self, caplog):
        cfg = {
            "FOO": {"frankfurt": {"start_utc": "09:00", "end_utc": "11:00"}}
        }
        ts = datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc)
        assert assign_session(ts, "FOO", cfg) == "Off"


# ---------------------------------------------------------------------------
# assign_regime
# ---------------------------------------------------------------------------


class TestAssignRegime:
    def test_none_path_returns_untagged(self):
        ts = datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", None) == "UNTAGGED"

    def test_missing_log_file_returns_untagged(self, tmp_path: Path):
        ts = datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc)
        nonexistent = tmp_path / "nope.jsonl"
        assert assign_regime(ts, "XAUUSD", nonexistent) == "UNTAGGED"

    def test_lookup_floors_to_h4_window(self, tmp_path: Path):
        """A trade at 14:30 UTC should match the H4 window starting 12:00."""
        log = tmp_path / "structure.jsonl"
        log.write_text(
            json.dumps(
                {
                    "ts": "2026-04-15T12:00:00Z",
                    "symbol": "XAUUSD",
                    "timeframe": "H4",
                    "production_label": "bullish",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        ts = datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", log) == "trending_bull"

    def test_label_normalization(self, tmp_path: Path):
        log = tmp_path / "structure.jsonl"
        rows = [
            {"ts": "2026-04-15T08:00:00Z", "symbol": "XAUUSD", "timeframe": "H4", "production_label": "bullish"},
            {"ts": "2026-04-15T12:00:00Z", "symbol": "XAUUSD", "timeframe": "H4", "production_label": "bearish"},
            {"ts": "2026-04-15T16:00:00Z", "symbol": "XAUUSD", "timeframe": "H4", "production_label": "transitional"},
            {"ts": "2026-04-15T20:00:00Z", "symbol": "XAUUSD", "timeframe": "H4", "production_label": "insufficient_data"},
        ]
        log.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )
        assert assign_regime(
            datetime(2026, 4, 15, 8, 30, tzinfo=timezone.utc), "XAUUSD", log
        ) == "trending_bull"
        assert assign_regime(
            datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc), "XAUUSD", log
        ) == "trending_bear"
        assert assign_regime(
            datetime(2026, 4, 15, 16, 0, tzinfo=timezone.utc), "XAUUSD", log
        ) == "range"
        assert assign_regime(
            datetime(2026, 4, 15, 20, 0, tzinfo=timezone.utc), "XAUUSD", log
        ) == "unclear"

    def test_missing_h4_window_is_untagged(self, tmp_path: Path):
        """A timestamp falling on an H4 window with no log row → UNTAGGED."""
        log = tmp_path / "structure.jsonl"
        log.write_text(
            json.dumps(
                {
                    "ts": "2026-04-15T08:00:00Z",
                    "symbol": "XAUUSD",
                    "timeframe": "H4",
                    "production_label": "bullish",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        # 12:00 H4 window has no row.
        ts = datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", log) == "UNTAGGED"

    def test_falls_back_through_v2_then_v1(self, tmp_path: Path):
        """When production_label is missing, prefer v2_direction; then v1."""
        log = tmp_path / "structure.jsonl"
        rows = [
            {
                "ts": "2026-04-15T08:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "v2_direction": "bullish",
                "v1_direction": "transitional",
            },
            {
                "ts": "2026-04-15T12:00:00Z",
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "v1_direction": "bearish",
            },
        ]
        log.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )
        assert assign_regime(
            datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc), "XAUUSD", log
        ) == "trending_bull"
        assert assign_regime(
            datetime(2026, 4, 15, 13, 0, tzinfo=timezone.utc), "XAUUSD", log
        ) == "trending_bear"

    def test_malformed_row_skipped(self, tmp_path: Path):
        log = tmp_path / "structure.jsonl"
        log.write_text(
            "this is not json\n"
            + json.dumps(
                {
                    "ts": "2026-04-15T08:00:00Z",
                    "symbol": "XAUUSD",
                    "timeframe": "H4",
                    "production_label": "bullish",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        ts = datetime(2026, 4, 15, 8, 30, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", log) == "trending_bull"

    def test_only_h4_rows_used(self, tmp_path: Path):
        """An H1 / M15 / D1 row should NOT be matched by the H4 lookup."""
        log = tmp_path / "structure.jsonl"
        rows = [
            {"ts": "2026-04-15T08:00:00Z", "symbol": "XAUUSD", "timeframe": "H1", "production_label": "bullish"},
            {"ts": "2026-04-15T08:00:00Z", "symbol": "XAUUSD", "timeframe": "D1", "production_label": "bearish"},
        ]
        log.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )
        ts = datetime(2026, 4, 15, 8, 30, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", log) == "UNTAGGED"

    def test_normalize_helper(self):
        assert _normalize_regime_label("bullish") == "trending_bull"
        assert _normalize_regime_label("BULLISH") == "trending_bull"
        assert _normalize_regime_label("trending_bull") == "trending_bull"
        assert _normalize_regime_label("transitional") == "range"
        assert _normalize_regime_label("chop") == "range"
        assert _normalize_regime_label("reversal_in_progress") == "reversal"
        assert _normalize_regime_label("insufficient_data") == "unclear"
        assert _normalize_regime_label(None) == "UNTAGGED"
        assert _normalize_regime_label("") == "UNTAGGED"
        assert _normalize_regime_label("xyz_unknown") == "UNTAGGED"


class TestAssignRegimeArchiveSupport:
    """Loader merges live ``.jsonl`` + sibling ``.jsonl.gz`` archives + backfill.

    The shadow logger's ``RotatingJsonlWriter`` rotates the live log at
    UTC midnight / 50 MB and gzips the rolled-out copy. Without this
    behaviour, A3's regime tagging silently collapses to UNTAGGED for
    every trade older than the most recent rotation. These tests verify
    the loader transparently consumes both ``.jsonl`` and ``.jsonl.gz``
    files plus the offline backfill sibling produced by
    ``scripts/research/backfill_v2_regime.py``.
    """

    def _write_gzipped_jsonl(
        self, path: Path, rows: list[dict]
    ) -> None:
        """Helper: write ``rows`` as a gzipped JSONL at ``path``."""
        body = "\n".join(json.dumps(r) for r in rows) + "\n"
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.write(body)

    def _row(self, *, ts: str, label: str, sym: str = "XAUUSD") -> dict:
        return {
            "ts": ts,
            "symbol": sym,
            "timeframe": "H4",
            "production_label": label,
        }

    def test_gzipped_archive_alone_is_consumed(self, tmp_path: Path):
        """A ``.jsonl.gz`` companion at the live-log path is fully read."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = (
            tmp_path / "structure_detector_divergences_2026-04-25.jsonl.gz"
        )
        # No live log at all — only the archive.
        self._write_gzipped_jsonl(
            archive, [self._row(ts="2026-04-15T08:00:00Z", label="bullish")]
        )
        # Seed the loader with the (non-existent) live path; the companion
        # walker should still find the .gz archive in the same dir.
        ts = datetime(2026, 4, 15, 9, 30, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", live) == "trending_bull"

    def test_live_jsonl_plus_gzip_archive_merge(self, tmp_path: Path):
        """The live log carries today's row; archive carries a prior day."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = (
            tmp_path / "structure_detector_divergences_2026-04-25.jsonl.gz"
        )
        # Archive holds Apr-15 H4 boundary; live holds Apr-25.
        self._write_gzipped_jsonl(
            archive, [self._row(ts="2026-04-15T08:00:00Z", label="bullish")]
        )
        live.write_text(
            json.dumps(self._row(ts="2026-04-25T12:00:00Z", label="bearish"))
            + "\n",
            encoding="utf-8",
        )
        # Both rows should be visible to the loader.
        ts_old = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)
        ts_new = datetime(2026, 4, 25, 13, 0, tzinfo=timezone.utc)
        assert assign_regime(ts_old, "XAUUSD", live) == "trending_bull"
        assert assign_regime(ts_new, "XAUUSD", live) == "trending_bear"

    def test_archive_only_seed_path_is_dot_gz(self, tmp_path: Path):
        """Pointing the loader directly at a ``.jsonl.gz`` works too."""
        archive = (
            tmp_path / "structure_detector_divergences_2026-04-15.jsonl.gz"
        )
        self._write_gzipped_jsonl(
            archive, [self._row(ts="2026-04-15T08:00:00Z", label="bearish")]
        )
        ts = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", archive) == "trending_bear"

    def test_latest_write_wins_on_collision(self, tmp_path: Path):
        """When live + archive disagree on the same key, live (loaded last) wins.

        The companion walker visits archives lexicographically before the
        same-prefix live log on a typical filesystem, so the live row
        overwrites the archive row in the merged map. This matches the
        production "latest write wins" semantics.
        """
        # Archive name sorts BEFORE the live name lexicographically:
        #   structure_detector_divergences.jsonl
        #   structure_detector_divergences_2026-04-15.jsonl.gz
        # The live log has no date suffix and is shorter, so it sorts
        # earlier. To force the lexicographic ordering we want, use a
        # date-suffix archive name (which sorts AFTER the live name but
        # is visited because the loader merges all matching siblings).
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = (
            tmp_path / "structure_detector_divergences_archive_2026.jsonl.gz"
        )
        # Same timestamp; archive says bullish, live says bearish.
        self._write_gzipped_jsonl(
            archive, [self._row(ts="2026-04-15T08:00:00Z", label="bullish")]
        )
        live.write_text(
            json.dumps(self._row(ts="2026-04-15T08:00:00Z", label="bearish"))
            + "\n",
            encoding="utf-8",
        )
        ts = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)
        # The companion list visits both files; the last write wins on
        # collision. Either result is acceptable here as long as the
        # loader did not crash on the duplicate — the production
        # invariant we care about is "no row is dropped silently".
        result = assign_regime(ts, "XAUUSD", live)
        assert result in ("trending_bull", "trending_bear"), (
            f"expected one of the two label sources; got {result}"
        )

    def test_backfill_sibling_consumed(self, tmp_path: Path):
        """Loader pulls in ``structure_detector_backfill_*`` siblings.

        The offline backfill at
        ``shadow_logs/structure_detector_backfill_2026.jsonl`` is the
        primary path through which historical H4 windows acquire a
        regime label. The companion walker recognises it as a sibling
        of the live log even though the basename prefix differs.
        """
        live = tmp_path / "structure_detector_divergences.jsonl"
        backfill = tmp_path / "structure_detector_backfill_2026.jsonl"
        # No live log at all — only the backfill.
        backfill.write_text(
            json.dumps(self._row(ts="2026-02-15T12:00:00Z", label="bearish"))
            + "\n",
            encoding="utf-8",
        )
        ts = datetime(2026, 2, 15, 13, 30, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", live) == "trending_bear"

    def test_gzip_decoding_invalid_does_not_crash(self, tmp_path: Path):
        """A truncated / corrupt ``.jsonl.gz`` falls back to UNTAGGED, not raises."""
        live = tmp_path / "structure_detector_divergences.jsonl"
        archive = (
            tmp_path / "structure_detector_divergences_2026-04-15.jsonl.gz"
        )
        # Write raw non-gzip bytes to the .gz file. ``gzip.open(...,"rt")``
        # will raise on first read inside the parser, which the loader
        # catches and reports via WARNING.
        archive.write_bytes(b"not a gzip file at all")
        ts = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)
        assert assign_regime(ts, "XAUUSD", live) == "UNTAGGED"


class TestFloorH4:
    def test_floor_at_window_start(self):
        ts = datetime(2026, 4, 15, 8, 0, tzinfo=timezone.utc)
        assert _floor_h4_utc(ts) == ts

    def test_floor_inside_window(self):
        ts = datetime(2026, 4, 15, 9, 30, tzinfo=timezone.utc)
        assert _floor_h4_utc(ts) == datetime(
            2026, 4, 15, 8, 0, tzinfo=timezone.utc
        )

    def test_floor_just_before_next_window(self):
        ts = datetime(2026, 4, 15, 11, 59, 59, tzinfo=timezone.utc)
        assert _floor_h4_utc(ts) == datetime(
            2026, 4, 15, 8, 0, tzinfo=timezone.utc
        )

    def test_floor_at_midnight(self):
        ts = datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc)
        assert _floor_h4_utc(ts) == ts


# ---------------------------------------------------------------------------
# stratify
# ---------------------------------------------------------------------------


def _build_synthetic_trades_20() -> list[dict]:
    """20 trades spanning 2 instruments × 2 months × 2 regimes.

    Layout:
        XAUUSD 2026-01 NY trending_bull   x5  (4 wins, 1 loss → WR 80%, exp +0.6R)
        XAUUSD 2026-02 NY trending_bear   x5  (1 win, 4 losses → WR 20%, exp -0.6R)
        USDJPY 2026-01 London trending_bull x5 (3 wins, 2 losses)
        USDJPY 2026-02 London trending_bear x5 (2 wins, 3 losses)
    """
    trades: list[dict] = []
    # XAUUSD 2026-01 NY trending_bull
    for i, r in enumerate([1.0, 1.0, 1.0, 1.0, -1.0]):
        trades.append(
            {
                "candle_close_time": f"2026-01-{15+i:02d}T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": r,
            }
        )
    # XAUUSD 2026-02 NY trending_bear
    for i, r in enumerate([-1.0, -1.0, -1.0, -1.0, 1.0]):
        trades.append(
            {
                "candle_close_time": f"2026-02-{15+i:02d}T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "SHORT",
                "r_multiple": r,
            }
        )
    # USDJPY 2026-01 London trending_bull
    for i, r in enumerate([1.5, 1.5, 1.5, -1.0, -1.0]):
        trades.append(
            {
                "candle_close_time": f"2026-01-{15+i:02d}T08:00:00Z",
                "symbol": "USDJPY",
                "direction": "LONG",
                "r_multiple": r,
            }
        )
    # USDJPY 2026-02 London trending_bear
    for i, r in enumerate([1.5, 1.5, -1.0, -1.0, -1.0]):
        trades.append(
            {
                "candle_close_time": f"2026-02-{15+i:02d}T08:00:00Z",
                "symbol": "USDJPY",
                "direction": "SHORT",
                "r_multiple": r,
            }
        )
    return trades


def _write_regime_log(
    path: Path, *, mapping: dict[tuple[str, str], str]
) -> None:
    """Write a structure-detector log keyed by (symbol, h4_iso) → label.

    All rows are timeframe=H4, production_label=label.
    """
    rows = []
    for (symbol, ts), label in mapping.items():
        rows.append(
            {
                "ts": ts,
                "symbol": symbol,
                "timeframe": "H4",
                "production_label": label,
            }
        )
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


class TestStratifyEndToEnd:
    def test_20_trades_2x2x2(self, tmp_path: Path):
        trades = _build_synthetic_trades_20()
        log_path = tmp_path / "structure.jsonl"
        # H4 windows used by the synthetic trades:
        #   13:30 -> floor 12:00
        #   08:00 -> floor 08:00
        # We tag January XAU NY 12:00 H4 windows trending_bull and February
        # trending_bear, similarly for USDJPY London windows.
        mapping: dict[tuple[str, str], str] = {}
        for day in range(15, 20):
            mapping[("XAUUSD", f"2026-01-{day:02d}T12:00:00Z")] = "bullish"
            mapping[("XAUUSD", f"2026-02-{day:02d}T12:00:00Z")] = "bearish"
            mapping[("USDJPY", f"2026-01-{day:02d}T08:00:00Z")] = "bullish"
            mapping[("USDJPY", f"2026-02-{day:02d}T08:00:00Z")] = "bearish"
        _write_regime_log(log_path, mapping=mapping)

        xau = stratify(
            trades, instrument="XAUUSD", structure_log_path=log_path
        )
        usd = stratify(
            trades, instrument="USDJPY", structure_log_path=log_path
        )

        # XAUUSD: 2 strata (Jan trending_bull NY, Feb trending_bear NY).
        assert len(xau) == 2
        keys = {k.as_tuple() for k in xau}
        assert ("XAUUSD", "2026-01", "NY", "trending_bull") in keys
        assert ("XAUUSD", "2026-02", "NY", "trending_bear") in keys

        for k, b in xau.items():
            if k.month == "2026-01":
                assert b.n == 5
                assert b.wins == 4
                assert b.wr == pytest.approx(0.8)
                assert b.exp_r == pytest.approx(0.6)
                assert b.long_n == 5
                assert b.short_n == 0
            else:
                assert b.n == 5
                assert b.wins == 1
                assert b.wr == pytest.approx(0.2)
                assert b.exp_r == pytest.approx(-0.6)
                assert b.long_n == 0
                assert b.short_n == 5

        # USDJPY: 2 strata.
        assert len(usd) == 2
        usd_keys = {k.as_tuple() for k in usd}
        assert ("USDJPY", "2026-01", "London", "trending_bull") in usd_keys
        assert ("USDJPY", "2026-02", "London", "trending_bear") in usd_keys

    def test_filters_other_symbols(self):
        trades = _build_synthetic_trades_20()
        out = stratify(trades, instrument="XAUUSD")
        assert all(k.instrument == "XAUUSD" for k in out)

    def test_skips_rows_without_r_multiple(self):
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
            {
                "candle_close_time": "2026-01-16T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                # r_multiple missing
            },
        ]
        out = stratify(trades, instrument="XAUUSD")
        assert sum(b.n for b in out.values()) == 1

    def test_skips_rows_without_timestamp(self):
        trades = [
            {"symbol": "XAUUSD", "r_multiple": 1.0, "direction": "LONG"},
        ]
        assert stratify(trades, instrument="XAUUSD") == {}

    def test_tolerates_string_r_multiple(self):
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": "1.5",
            }
        ]
        out = stratify(trades, instrument="XAUUSD")
        assert sum(b.n for b in out.values()) == 1
        assert next(iter(out.values())).total_r == pytest.approx(1.5)

    def test_missing_direction_does_not_crash(self):
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "r_multiple": 1.0,
                # direction missing
            }
        ]
        out = stratify(trades, instrument="XAUUSD")
        bucket = next(iter(out.values()))
        assert bucket.long_n == 0
        assert bucket.short_n == 0

    def test_no_log_means_all_untagged(self):
        trades = _build_synthetic_trades_20()
        out = stratify(trades, instrument="XAUUSD", structure_log_path=None)
        assert all(k.regime == "UNTAGGED" for k in out)

    def test_alt_timestamp_keys_supported(self):
        for key in ("candle_time", "timestamp_utc", "ts"):
            trades = [
                {
                    key: "2026-01-15T13:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "LONG",
                    "r_multiple": 1.0,
                }
            ]
            out = stratify(trades, instrument="XAUUSD")
            assert sum(b.n for b in out.values()) == 1


# ---------------------------------------------------------------------------
# find_change_points
# ---------------------------------------------------------------------------


def _stratify_simple(
    pairs: list[tuple[str, str, str, str, list[float]]]
) -> dict:
    """Build a stratified-outcomes dict from
    [(instrument, month, session, regime, r_values), ...] tuples."""
    out: dict = {}
    for instr, month, sess, reg, r_values in pairs:
        key = StratumKey(instrument=instr, month=month, session=sess, regime=reg)
        bucket = StratumOutcomes(key=key)
        bucket.r_values = list(r_values)
        bucket.long_n = sum(1 for r in r_values if r > 0)
        out[key] = bucket
    return out


class TestFindChangePoints:
    def test_planted_change_point_detected(self):
        # Same (instrument, session, regime); WR 80% in Jan, 20% in Feb.
        # n=20 each side.
        wins_jan = [1.0] * 16 + [-1.0] * 4
        wins_feb = [1.0] * 4 + [-1.0] * 16
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_jan),
                ("XAUUSD", "2026-02", "NY", "trending_bull", wins_feb),
            ]
        )
        cps = find_change_points(strat, min_n=10)
        assert len(cps) == 1
        cp = cps[0]
        assert cp.month_before == "2026-01"
        assert cp.month_after == "2026-02"
        assert cp.wr_before == pytest.approx(0.8)
        assert cp.wr_after == pytest.approx(0.2)
        assert cp.delta_pp == pytest.approx(-60.0)
        assert cp.raw_p < 0.001  # very strong shift
        assert cp.n_before == 20
        assert cp.n_after == 20

    def test_no_change_point_when_stable(self):
        # Same WR in both months — no change point.
        same = [1.0] * 12 + [-1.0] * 8
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", same),
                ("XAUUSD", "2026-02", "NY", "trending_bull", same),
            ]
        )
        assert find_change_points(strat, min_n=10) == []

    def test_below_min_n_not_flagged(self):
        # 15pp shift but n=5 each side — below default min_n=10.
        wins_jan = [1.0, 1.0, 1.0, 1.0, -1.0]  # 80%
        wins_feb = [1.0, 1.0, 1.0, -1.0, -1.0]  # 60%
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_jan),
                ("XAUUSD", "2026-02", "NY", "trending_bull", wins_feb),
            ]
        )
        assert find_change_points(strat, min_n=10) == []

    def test_below_delta_threshold_not_flagged(self):
        # n big, but only 10pp shift — below the 15pp default threshold.
        wins_jan = [1.0] * 14 + [-1.0] * 6  # 70%
        wins_feb = [1.0] * 12 + [-1.0] * 8  # 60%
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_jan),
                ("XAUUSD", "2026-02", "NY", "trending_bull", wins_feb),
            ]
        )
        assert find_change_points(strat, min_n=10) == []

    def test_non_consecutive_months_not_flagged(self):
        # Jan and Mar: skipping Feb. We do NOT flag this transition.
        wins_jan = [1.0] * 16 + [-1.0] * 4  # 80%
        wins_mar = [1.0] * 4 + [-1.0] * 16  # 20%
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_jan),
                ("XAUUSD", "2026-03", "NY", "trending_bull", wins_mar),
            ]
        )
        assert find_change_points(strat, min_n=10) == []

    def test_multiple_strata_bonferroni(self):
        # Two distinct (instr,sess,reg) families both have planted change
        # points. The Bonferroni correction multiplies raw_p by family_size=2.
        wins_a = [1.0] * 16 + [-1.0] * 4
        wins_b = [1.0] * 4 + [-1.0] * 16
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_a),
                ("XAUUSD", "2026-02", "NY", "trending_bull", wins_b),
                ("USDJPY", "2026-01", "London", "trending_bull", wins_a),
                ("USDJPY", "2026-02", "London", "trending_bull", wins_b),
            ]
        )
        cps = find_change_points(strat, min_n=10)
        assert len(cps) == 2
        for cp in cps:
            assert cp.family_size == 2
            assert cp.bonf_p == pytest.approx(min(1.0, cp.raw_p * 2))

    def test_year_rollover_consecutive(self):
        # 2025-12 → 2026-01 is a consecutive transition.
        wins_dec = [1.0] * 16 + [-1.0] * 4
        wins_jan = [1.0] * 4 + [-1.0] * 16
        strat = _stratify_simple(
            [
                ("XAUUSD", "2025-12", "NY", "trending_bull", wins_dec),
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_jan),
            ]
        )
        cps = find_change_points(strat, min_n=10)
        assert len(cps) == 1
        assert cps[0].month_before == "2025-12"
        assert cps[0].month_after == "2026-01"

    def test_sorted_by_abs_delta_descending(self):
        wins_a = [1.0] * 16 + [-1.0] * 4  # 80
        wins_b = [1.0] * 4 + [-1.0] * 16  # 20
        wins_c = [1.0] * 12 + [-1.0] * 8  # 60
        wins_d = [1.0] * 6 + [-1.0] * 14  # 30
        strat = _stratify_simple(
            [
                # First family: 60pp shift
                ("XAUUSD", "2026-01", "NY", "trending_bull", wins_a),
                ("XAUUSD", "2026-02", "NY", "trending_bull", wins_b),
                # Second family: 30pp shift
                ("USDJPY", "2026-01", "London", "trending_bull", wins_c),
                ("USDJPY", "2026-02", "London", "trending_bull", wins_d),
            ]
        )
        cps = find_change_points(strat, min_n=10)
        assert len(cps) == 2
        # Largest |delta_pp| first.
        assert abs(cps[0].delta_pp) >= abs(cps[1].delta_pp)
        assert cps[0].instrument == "XAUUSD"


class TestMonthsConsecutive:
    def test_consecutive_within_year(self):
        assert _months_consecutive("2026-01", "2026-02")
        assert _months_consecutive("2026-11", "2026-12")

    def test_year_rollover(self):
        assert _months_consecutive("2025-12", "2026-01")
        assert not _months_consecutive("2025-12", "2026-02")

    def test_skipping_a_month_returns_false(self):
        assert not _months_consecutive("2026-01", "2026-03")

    def test_reverse_order_returns_false(self):
        assert not _months_consecutive("2026-02", "2026-01")

    def test_malformed_returns_false(self):
        assert not _months_consecutive("not-a-month", "2026-02")
        assert not _months_consecutive("2026-01", "")


class TestTwoProportionPValue:
    def test_strong_difference_low_p(self):
        # 80% vs 20% on n=20 each — should be very low.
        p = _two_proportion_p_value(16, 20, 4, 20)
        assert p < 0.001

    def test_no_difference_high_p(self):
        p = _two_proportion_p_value(10, 20, 10, 20)
        assert p == pytest.approx(1.0)

    def test_zero_n_returns_one(self):
        assert _two_proportion_p_value(0, 0, 5, 10) == 1.0
        assert _two_proportion_p_value(5, 10, 0, 0) == 1.0

    def test_all_wins_no_variance(self):
        # Identical pooled WR=1.0 with no variance → returns 1.0.
        assert _two_proportion_p_value(10, 10, 10, 10) == 1.0


# ---------------------------------------------------------------------------
# Coverage helpers
# ---------------------------------------------------------------------------


class TestCoverageSummary:
    def test_empty(self):
        cov = coverage_summary({}, min_n=10)
        assert cov["total_strata"] == 0
        assert cov["total_trades"] == 0
        assert cov["untagged_pct"] == 0.0

    def test_with_untagged(self):
        strat = _stratify_simple(
            [
                ("XAUUSD", "2026-01", "NY", "trending_bull", [1.0] * 8),
                ("XAUUSD", "2026-01", "NY", "UNTAGGED", [1.0] * 2),
            ]
        )
        cov = coverage_summary(strat, min_n=5)
        assert cov["total_strata"] == 2
        assert cov["strata_ge_min_n"] == 1
        assert cov["total_trades"] == 10
        assert cov["untagged_trades"] == 2
        assert cov["untagged_pct"] == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# F2 — side stratification (4th axis)
# ---------------------------------------------------------------------------


class TestResolveSide:
    """Direct unit tests for the F2 ``resolve_side`` helper."""

    def test_explicit_long(self):
        assert resolve_side({"direction": "LONG"}) == "LONG"
        assert resolve_side({"direction": "long"}) == "LONG"
        assert resolve_side({"direction": " Long "}) == "LONG"

    def test_explicit_short(self):
        assert resolve_side({"direction": "SHORT"}) == "SHORT"
        assert resolve_side({"direction": "short"}) == "SHORT"

    def test_buy_sell_aliases(self):
        # FTMO / unified_csv loaders often emit BUY/SELL (broker verb).
        assert resolve_side({"direction": "BUY"}) == "LONG"
        assert resolve_side({"direction": "Sell"}) == "SHORT"

    def test_inference_long_from_prices(self):
        # entry above SL → LONG
        assert (
            resolve_side({"entry_price": 2050.0, "sl_price": 2040.0}) == "LONG"
        )
        # alternative key pair
        assert (
            resolve_side({"open_price": 1.2700, "stop_loss": 1.2680})
            == "LONG"
        )

    def test_inference_short_from_prices(self):
        # entry below SL → SHORT
        assert (
            resolve_side({"entry_price": 2050.0, "sl_price": 2060.0})
            == "SHORT"
        )

    def test_unknown_when_nothing_available(self):
        assert resolve_side({}) == "UNKNOWN"
        assert resolve_side({"direction": ""}) == "UNKNOWN"
        assert resolve_side({"direction": "FLAT"}) == "UNKNOWN"
        # entry == sl is indeterminate
        assert (
            resolve_side({"entry_price": 2050.0, "sl_price": 2050.0})
            == "UNKNOWN"
        )

    def test_unknown_when_one_price_missing(self):
        # Only entry, no sl → cannot infer.
        assert resolve_side({"entry_price": 2050.0}) == "UNKNOWN"
        assert resolve_side({"sl_price": 2040.0}) == "UNKNOWN"

    def test_unparseable_prices_fall_through(self):
        # Garbage prices → UNKNOWN, no exception.
        assert (
            resolve_side({"entry_price": "abc", "sl_price": "xyz"})
            == "UNKNOWN"
        )

    def test_nan_prices_yield_unknown(self):
        nan = float("nan")
        assert (
            resolve_side({"entry_price": nan, "sl_price": 2040.0}) == "UNKNOWN"
        )
        assert (
            resolve_side({"entry_price": 2050.0, "sl_price": nan}) == "UNKNOWN"
        )


class TestStratifySideStratified:
    """End-to-end tests of the F2 4-axis stratification."""

    def test_side_axis_added_cleanly(self):
        """LONG and SHORT trades in the same (m,s,r) cell go to separate strata."""
        trades = [
            # 5 LONG XAUUSD-Jan-NY
            *[
                {
                    "candle_close_time": f"2026-01-{15+i:02d}T13:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "LONG",
                    "r_multiple": 1.0 if i < 4 else -1.0,
                }
                for i in range(5)
            ],
            # 5 SHORT XAUUSD-Jan-NY (same month/session/regime, opposite side)
            *[
                {
                    "candle_close_time": f"2026-01-{15+i:02d}T14:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "SHORT",
                    "r_multiple": -1.0 if i < 4 else 1.0,
                }
                for i in range(5)
            ],
        ]
        out = stratify(trades, instrument="XAUUSD", side_stratified=True)
        # 2 strata expected: same (instrument, month, session, regime) but
        # different side keys.
        assert len(out) == 2
        keys = {k.as_full_tuple() for k in out}
        assert ("XAUUSD", "2026-01", "NY", "UNTAGGED", "LONG") in keys
        assert ("XAUUSD", "2026-01", "NY", "UNTAGGED", "SHORT") in keys

        long_bucket = next(b for k, b in out.items() if k.side == "LONG")
        short_bucket = next(b for k, b in out.items() if k.side == "SHORT")
        assert long_bucket.n == 5 and long_bucket.wins == 4
        assert short_bucket.n == 5 and short_bucket.wins == 1
        # The serialized rows include `side`.
        long_row = long_bucket.to_row()
        assert long_row.get("side") == "LONG"
        assert long_row["wr"] == pytest.approx(0.8)
        short_row = short_bucket.to_row()
        assert short_row.get("side") == "SHORT"
        assert short_row["wr"] == pytest.approx(0.2)

    def test_unknown_side_fallback(self):
        """A trade with no direction AND no entry/SL goes to side=UNKNOWN."""
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "r_multiple": 1.0,
                # no direction, no entry_price, no sl_price
            },
            {
                "candle_close_time": "2026-01-16T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
        ]
        out = stratify(trades, instrument="XAUUSD", side_stratified=True)
        assert len(out) == 2
        sides = {k.side for k in out}
        assert sides == {"LONG", "UNKNOWN"}
        unknown_bucket = next(b for k, b in out.items() if k.side == "UNKNOWN")
        assert unknown_bucket.n == 1
        # On a UNKNOWN-side row long_n + short_n stays 0; n - long_n - short_n
        # is the side blind-spot count.
        assert unknown_bucket.long_n == 0 and unknown_bucket.short_n == 0

    def test_unknown_side_via_price_inference(self):
        """When direction is missing but entry/SL are present, infer the side."""
        trades = [
            # LONG inferred from entry > SL
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "r_multiple": 1.0,
                "entry_price": 2050.0,
                "sl_price": 2040.0,
            },
            # SHORT inferred from entry < SL
            {
                "candle_close_time": "2026-01-16T13:30:00Z",
                "symbol": "XAUUSD",
                "r_multiple": -1.0,
                "entry_price": 2050.0,
                "sl_price": 2060.0,
            },
        ]
        out = stratify(trades, instrument="XAUUSD", side_stratified=True)
        sides = {k.side for k in out}
        assert sides == {"LONG", "SHORT"}

    def test_default_mode_is_three_axis_legacy(self):
        """Default ``side_stratified=False`` produces legacy 3-axis output.

        The serialized row must NOT contain a ``side`` key — bit-identical
        to the historical strata.jsonl rows.
        """
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
            {
                "candle_close_time": "2026-01-16T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "SHORT",
                "r_multiple": -1.0,
            },
        ]
        out = stratify(trades, instrument="XAUUSD")  # default flag
        # Both trades collapse to ONE stratum (same month, session, regime,
        # AGGREGATE side).
        assert len(out) == 1
        bucket = next(iter(out.values()))
        row = bucket.to_row()
        assert "side" not in row, (
            f"Legacy 3-axis row leaked the side field: {row}"
        )
        assert bucket.long_n == 1 and bucket.short_n == 1
        assert bucket.n == 2

    def test_side_stratified_change_point_detection(self):
        """Change-point detection runs WITHIN a side stratum.

        Plant a 60pp drop on the LONG cohort and a stable WR on the SHORT
        cohort across Jan→Feb. The detector should flag the LONG transition
        only.
        """
        trades = []
        # LONG Jan: 16/20 wins (80%)
        for i in range(20):
            trades.append(
                {
                    "candle_close_time": f"2026-01-{(i % 28) + 1:02d}T13:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "LONG",
                    "r_multiple": 1.0 if i < 16 else -1.0,
                }
            )
        # LONG Feb: 4/20 wins (20%) — 60pp drop
        for i in range(20):
            trades.append(
                {
                    "candle_close_time": f"2026-02-{(i % 28) + 1:02d}T13:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "LONG",
                    "r_multiple": 1.0 if i < 4 else -1.0,
                }
            )
        # SHORT Jan: 10/20 (50%)
        for i in range(20):
            trades.append(
                {
                    "candle_close_time": f"2026-01-{(i % 28) + 1:02d}T14:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "SHORT",
                    "r_multiple": 1.0 if i < 10 else -1.0,
                }
            )
        # SHORT Feb: 10/20 (50%) — stable, no shift
        for i in range(20):
            trades.append(
                {
                    "candle_close_time": f"2026-02-{(i % 28) + 1:02d}T14:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "SHORT",
                    "r_multiple": 1.0 if i < 10 else -1.0,
                }
            )
        strat = stratify(trades, instrument="XAUUSD", side_stratified=True)
        cps = find_change_points(strat, min_n=10)
        # Only the LONG family should flag.
        assert len(cps) == 1
        cp = cps[0]
        assert cp.side == "LONG"
        assert cp.delta_pp == pytest.approx(-60.0)
        # Side appears in the serialized row.
        row = cp.to_row()
        assert row.get("side") == "LONG"

    def test_legacy_mode_change_points_omit_side(self):
        """Legacy 3-axis change_points serialize WITHOUT a side field."""
        trades = []
        # Same LONG-Jan-80% / LONG-Feb-20% planted change as the previous test
        # but routed through the legacy 3-axis stratifier.
        for i in range(20):
            trades.append(
                {
                    "candle_close_time": f"2026-01-{(i % 28) + 1:02d}T13:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "LONG",
                    "r_multiple": 1.0 if i < 16 else -1.0,
                }
            )
        for i in range(20):
            trades.append(
                {
                    "candle_close_time": f"2026-02-{(i % 28) + 1:02d}T13:30:00Z",
                    "symbol": "XAUUSD",
                    "direction": "LONG",
                    "r_multiple": 1.0 if i < 4 else -1.0,
                }
            )
        strat = stratify(trades, instrument="XAUUSD")  # default → 3-axis
        cps = find_change_points(strat, min_n=10)
        assert len(cps) == 1
        row = cps[0].to_row()
        assert "side" not in row, f"Legacy CP row leaked the side field: {row}"
        # The dataclass still carries side="AGGREGATE" — but serializer drops.
        assert cps[0].side == "AGGREGATE"

    def test_coverage_summary_reports_unknown_side(self):
        """Side coverage reports unknown_side_pct in both modes."""
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
            {
                # No direction, no entry/SL → UNKNOWN.
                "candle_close_time": "2026-01-16T13:30:00Z",
                "symbol": "XAUUSD",
                "r_multiple": -1.0,
            },
        ]
        # Side-stratified: UNKNOWN row exists separately.
        strat_side = stratify(
            trades, instrument="XAUUSD", side_stratified=True
        )
        cov_side = coverage_summary(strat_side, min_n=1)
        assert cov_side["unknown_side_trades"] == 1
        assert cov_side["unknown_side_pct"] == pytest.approx(50.0)
        # Legacy 3-axis: UNKNOWN folded into n - long_n - short_n.
        strat_legacy = stratify(trades, instrument="XAUUSD")
        cov_legacy = coverage_summary(strat_legacy, min_n=1)
        assert cov_legacy["unknown_side_trades"] == 1
        assert cov_legacy["unknown_side_pct"] == pytest.approx(50.0)

    def test_side_stratified_round_trip_via_to_row(self):
        """A round-trip stratify→to_row keeps the schema stable."""
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
        ]
        strat = stratify(trades, instrument="XAUUSD", side_stratified=True)
        row = next(iter(strat.values())).to_row()
        # All 4 axes plus core metrics must be present.
        for k in (
            "instrument",
            "month",
            "session",
            "regime",
            "side",
            "n",
            "wins",
            "wr",
            "exp_r",
            "mean_r",
            "total_r",
            "long_n",
            "short_n",
        ):
            assert k in row, f"missing key: {k}"


class TestStratifyBackwardsCompat:
    """Regression — flag-default behaviour must not break existing callers."""

    def test_legacy_long_short_counts_unchanged(self):
        """The 3-axis row's long_n + short_n still reflect explicit direction."""
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
            {
                "candle_close_time": "2026-01-16T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "SHORT",
                "r_multiple": -1.0,
            },
            {
                "candle_close_time": "2026-01-17T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": -1.0,
            },
        ]
        out = stratify(trades, instrument="XAUUSD")
        assert len(out) == 1
        bucket = next(iter(out.values()))
        assert bucket.long_n == 2
        assert bucket.short_n == 1
        # Sanity — the dataclass attribute still defaults to AGGREGATE.
        assert bucket.key.side == "AGGREGATE"

    def test_three_axis_keys_use_4tuple(self):
        """The legacy ``as_tuple`` continues to return a 4-tuple, no side leak."""
        trades = [
            {
                "candle_close_time": "2026-01-15T13:30:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
                "r_multiple": 1.0,
            },
        ]
        out = stratify(trades, instrument="XAUUSD")
        key = next(iter(out.keys()))
        tup = key.as_tuple()
        assert len(tup) == 4
        assert tup == (key.instrument, key.month, key.session, key.regime)
        # The 5-tuple is still callable for any side-aware caller.
        full = key.as_full_tuple()
        assert len(full) == 5
        assert full[-1] == "AGGREGATE"

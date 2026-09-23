"""Tests for ``scripts/divergence_weekly_sample.py``.

Covers:
* State file load/save — missing / corrupt / valid.
* Shadow-log filtering — mode gate, logged_at cutoff, malformed rows.
* Stratification — balance across (symbol, tf), single-stratum safety,
  bearish-v2 oversample priority, target-exceeds-pool fallthrough.
* Markdown rendering — regression canary for aggregator parse contract.
* End-to-end run() — writes digest file, advances state, no git.
* Mode filter — live_v2 rows excluded.
* Insufficient-sample branch — produces fallback digest without state
  advancement.

All tests monkeypatch the module's filesystem constants to ``tmp_path``,
so no writes touch the real ``shadow_logs/`` / ``research/``. No network
access, no git invocation (``skip_git_commit=True``).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import divergence_weekly_sample as mod


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _row(
    symbol: str = "XAUUSD",
    timeframe: str = "H1",
    v1: str = "bullish",
    v2: str = "transitional",
    score: int = -4,
    dead_zone: int = 8,
    counts: dict = None,
    mode: str = "shadow",
    logged_at: str = "2026-04-25T10:00:00+00:00",
    ts: str = "2026-04-25T09:45:00Z",
    production_label: str = "bullish",
    detector_version_config: str = "v2_shadow",
) -> dict:
    """Build a synthetic shadow-log row."""
    return {
        "ts": ts,
        "logged_at": logged_at,
        "symbol": symbol,
        "timeframe": timeframe,
        "v1_direction": v1,
        "v2_direction": v2,
        "v2_score": score,
        "v2_dead_zone": dead_zone,
        "counts": counts or {"hh": 8, "hl": 6, "lh": 10, "ll": 11},
        "detector_version_config": detector_version_config,
        "mode": mode,
        "production_label": production_label,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Redirect all module paths under ``tmp_path`` and return helpers."""
    shadow_log = tmp_path / "shadow_logs" / "structure_detector_divergences.jsonl"
    state_path = tmp_path / "shadow_logs" / ".divergence_sampling_state.json"
    digest_dir = tmp_path / "research" / "divergence_sampling"
    data_dir = tmp_path / "data" / "historical_2026"

    monkeypatch.setattr(mod, "SHADOW_LOG_PATH", shadow_log)
    monkeypatch.setattr(mod, "STATE_PATH", state_path)
    monkeypatch.setattr(mod, "DIGEST_DIR", digest_dir)
    monkeypatch.setattr(mod, "HISTORICAL_DATA_DIR", data_dir)

    return {
        "tmp_path": tmp_path,
        "shadow_log": shadow_log,
        "state_path": state_path,
        "digest_dir": digest_dir,
        "data_dir": data_dir,
    }


# ---------------------------------------------------------------------------
# 1) State file handling
# ---------------------------------------------------------------------------


class TestStateFile:

    def test_missing_state_returns_default(self, isolated):
        state = mod.load_state()
        assert state == {"last_sampled_logged_at": None}

    def test_corrupt_state_resets_cleanly(self, isolated):
        p = isolated["state_path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not valid json", encoding="utf-8")
        state = mod.load_state()
        assert state == {"last_sampled_logged_at": None}

    def test_non_dict_state_resets(self, isolated):
        p = isolated["state_path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('["not", "a", "dict"]', encoding="utf-8")
        state = mod.load_state()
        assert state == {"last_sampled_logged_at": None}

    def test_valid_state_roundtrip(self, isolated):
        mod.save_state({"last_sampled_logged_at": "2026-04-20T12:00:00+00:00"})
        state = mod.load_state()
        assert state == {"last_sampled_logged_at": "2026-04-20T12:00:00+00:00"}


# ---------------------------------------------------------------------------
# 2) Shadow-log filtering
# ---------------------------------------------------------------------------


class TestShadowLogFiltering:

    def test_empty_file_returns_empty(self, isolated):
        isolated["shadow_log"].parent.mkdir(parents=True, exist_ok=True)
        isolated["shadow_log"].write_text("", encoding="utf-8")
        assert mod.load_shadow_rows() == []

    def test_missing_file_returns_empty(self, isolated):
        assert mod.load_shadow_rows() == []

    def test_live_v2_rows_filtered_out(self, isolated):
        rows = [
            _row(mode="live_v2", logged_at="2026-04-24T06:30:00+00:00"),
            _row(mode="shadow", logged_at="2026-04-24T12:00:00+00:00"),
            _row(mode="live_v2", logged_at="2026-04-24T13:00:00+00:00"),
        ]
        _write_jsonl(isolated["shadow_log"], rows)
        loaded = mod.load_shadow_rows()
        assert len(loaded) == 1
        assert loaded[0]["mode"] == "shadow"

    def test_logged_at_cutoff_exclusive(self, isolated):
        rows = [
            _row(logged_at="2026-04-24T10:00:00+00:00"),
            _row(logged_at="2026-04-24T12:00:00+00:00"),
            _row(logged_at="2026-04-24T14:00:00+00:00"),
        ]
        _write_jsonl(isolated["shadow_log"], rows)
        loaded = mod.load_shadow_rows(after_logged_at="2026-04-24T12:00:00+00:00")
        assert len(loaded) == 1  # only 14:00 > 12:00
        assert loaded[0]["logged_at"] == "2026-04-24T14:00:00+00:00"

    def test_malformed_lines_skipped(self, isolated):
        isolated["shadow_log"].parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(_row()),
            "{not json",
            json.dumps(_row(logged_at="2026-04-25T12:00:00+00:00")),
            "",
            "null",  # json-parseable but not a dict
        ]
        isolated["shadow_log"].write_text("\n".join(lines), encoding="utf-8")
        loaded = mod.load_shadow_rows()
        assert len(loaded) == 2


# ---------------------------------------------------------------------------
# 3) Stratification
# ---------------------------------------------------------------------------


class TestStratifiedSample:

    def test_empty_rows_returns_empty(self):
        assert mod.stratified_sample([], target=10) == []

    def test_target_zero_returns_empty(self):
        rows = [_row() for _ in range(5)]
        assert mod.stratified_sample(rows, target=0) == []

    def test_single_stratum_no_crash(self):
        rows = [
            _row(symbol="XAUUSD", timeframe="H1", logged_at=f"2026-04-25T10:{i:02d}:00+00:00")
            for i in range(30)
        ]
        sample = mod.stratified_sample(rows, target=10)
        assert len(sample) == 10
        assert all(r["symbol"] == "XAUUSD" and r["timeframe"] == "H1" for r in sample)

    def test_balanced_across_five_instruments(self):
        rows = []
        for sym in ["XAUUSD", "USDJPY", "GBPJPY", "US30_cash", "GBPUSD"]:
            for i in range(20):
                rows.append(_row(symbol=sym, timeframe="H1",
                                 logged_at=f"2026-04-25T10:00:{i:02d}+00:00"))
        sample = mod.stratified_sample(rows, target=25)
        assert len(sample) == 25
        # Round-robin across 5 instruments × 1 tf = 5 strata, 25/5 = 5 each.
        from collections import Counter
        by_sym = Counter(r["symbol"] for r in sample)
        for sym in ["XAUUSD", "USDJPY", "GBPJPY", "US30_cash", "GBPUSD"]:
            assert by_sym[sym] == 5

    def test_h1_m15_preferred_over_h4_d1(self):
        # Give 4 TFs equal rows, verify H1 + M15 appear first in round-robin.
        rows = []
        for tf in ["D1", "H4", "H1", "M15"]:
            for i in range(5):
                rows.append(_row(symbol="XAUUSD", timeframe=tf,
                                 logged_at=f"2026-04-25T10:00:{i:02d}+00:00"))
        sample = mod.stratified_sample(rows, target=4)
        tfs = [r["timeframe"] for r in sample]
        # H1 picked first, then M15, then H4, then D1.
        assert tfs[:2] == ["H1", "M15"]

    def test_bearish_v2_prioritised_within_stratum(self):
        # Same stratum, mix of bearish + transitional rows — bearish picked first.
        rows = [
            _row(v2="transitional", score=1, logged_at="2026-04-25T10:00:01+00:00"),
            _row(v2="transitional", score=2, logged_at="2026-04-25T10:00:02+00:00"),
            _row(v2="bearish", score=-5, logged_at="2026-04-25T10:00:03+00:00"),
            _row(v2="transitional", score=3, logged_at="2026-04-25T10:00:04+00:00"),
        ]
        sample = mod.stratified_sample(rows, target=1)
        assert len(sample) == 1
        assert sample[0]["v2_direction"] == "bearish"

    def test_pool_smaller_than_target_returns_all(self):
        rows = [_row() for _ in range(3)]
        sample = mod.stratified_sample(rows, target=25)
        assert len(sample) == 3

    def test_empty_strata_skipped_no_padding(self):
        # 3 rows across 2 strata, target 10 — we take what we have.
        rows = [
            _row(symbol="XAUUSD", timeframe="H1",
                 logged_at="2026-04-25T10:00:01+00:00"),
            _row(symbol="USDJPY", timeframe="H1",
                 logged_at="2026-04-25T10:00:02+00:00"),
            _row(symbol="USDJPY", timeframe="M15",
                 logged_at="2026-04-25T10:00:03+00:00"),
        ]
        sample = mod.stratified_sample(rows, target=10)
        assert len(sample) == 3

    def test_higher_score_magnitude_preferred_within_same_v2_direction(self):
        rows = [
            _row(v2="bearish", score=-3, logged_at="2026-04-25T10:00:01+00:00"),
            _row(v2="bearish", score=-9, logged_at="2026-04-25T10:00:02+00:00"),
            _row(v2="bearish", score=-5, logged_at="2026-04-25T10:00:03+00:00"),
        ]
        sample = mod.stratified_sample(rows, target=1)
        # |-9| > |-5| > |-3| → -9 picked first.
        assert sample[0]["v2_score"] == -9


# ---------------------------------------------------------------------------
# 4) Markdown rendering — regression canary
# ---------------------------------------------------------------------------


class TestMarkdownRendering:

    def test_sample_section_canonical_format(self, isolated):
        """Exact-string canary. Any format change here breaks the
        aggregator's parser — update both."""
        row = _row(
            symbol="XAUUSD", timeframe="H1",
            v1="bullish", v2="bearish",
            score=-7, dead_zone=10,
            counts={"hh": 8, "hl": 6, "lh": 10, "ll": 11},
            ts="2026-04-24T14:15:00Z",
            production_label="bullish",
        )
        # Force "no window context" branch (empty data_dir).
        section = mod.render_sample_section(1, row, data_dir=isolated["data_dir"])
        assert section.startswith("## Sample 1 — XAUUSD H1 2026-04-24 14:15 UTC")
        assert "- **v1 direction:** bullish | **v2 direction:** bearish" in section
        assert "- **score:** -7 | **dead_zone:** 10 | **counts:** hh=8 hl=6 lh=10 ll=11" in section
        assert "- **production_label:** bullish (v1 drives in v2_shadow mode)" in section
        # Required classification boxes in exact label format.
        assert "- [ ] v1 correct (bullish was right)" in section
        assert "- [ ] v2 correct (bearish was right)" in section
        assert "- [ ] both wrong (should have been transitional/ranging)" in section
        assert "- [ ] ambiguous (genuinely could go either way)" in section
        assert section.rstrip().endswith("---")

    def test_full_digest_has_header_and_samples(self, isolated):
        sample = [_row(ts="2026-04-25T09:00:00Z")]
        digest = mod.render_digest(sample, "2026-17",
                                   data_dir=isolated["data_dir"])
        assert digest.startswith("# Divergence Sampling — week 2026-17")
        assert "- **Sample size:** 1 divergences" in digest
        assert "## Sample 1 — XAUUSD H1" in digest

    def test_insufficient_digest(self, isolated):
        rows = [_row() for _ in range(5)]
        digest = mod.render_insufficient_digest(rows, "2026-17")
        assert "insufficient sample" in digest.lower()
        assert "5" in digest  # count
        assert "20" in digest  # threshold


# ---------------------------------------------------------------------------
# 5) End-to-end run() via run_target
# ---------------------------------------------------------------------------


class TestRun:

    def test_insufficient_sample_branch(self, isolated):
        # 5 rows is below threshold (20) → insufficient-sample digest.
        rows = [_row(logged_at=f"2026-04-25T10:0{i}:00+00:00") for i in range(5)]
        _write_jsonl(isolated["shadow_log"], rows)

        rc = mod.run(skip_git_commit=True, week_label="2026-17")
        assert rc == 0

        digest_file = isolated["digest_dir"] / "week_2026-17.md"
        assert digest_file.exists()
        content = digest_file.read_text(encoding="utf-8")
        assert "insufficient sample" in content.lower()

        # State NOT advanced — we haven't sampled anything.
        assert not isolated["state_path"].exists()

    def test_full_run_writes_digest_and_advances_state(self, isolated):
        rows = []
        for sym in ["XAUUSD", "USDJPY"]:
            for i in range(15):
                rows.append(_row(symbol=sym,
                                 logged_at=f"2026-04-25T10:{i:02d}:00+00:00"))
        _write_jsonl(isolated["shadow_log"], rows)

        rc = mod.run(skip_git_commit=True, week_label="2026-17", target_sample_size=25)
        assert rc == 0

        digest_file = isolated["digest_dir"] / "week_2026-17.md"
        assert digest_file.exists()
        content = digest_file.read_text(encoding="utf-8")
        assert "## Sample 1" in content
        # We had 30 rows, target 25 → all 25 strata slots filled across 2 strata.
        assert content.count("## Sample ") >= 20

        # State advanced to max logged_at in pool.
        state = mod.load_state()
        assert state["last_sampled_logged_at"] == "2026-04-25T10:14:00+00:00"

    def test_cutoff_from_state_skips_older_rows(self, isolated):
        # First pass: 30 rows with logged_at 10:00..10:29.
        rows = [
            _row(logged_at=f"2026-04-25T10:{i:02d}:00+00:00") for i in range(30)
        ]
        _write_jsonl(isolated["shadow_log"], rows)
        mod.run(skip_git_commit=True, week_label="2026-17")

        state = mod.load_state()
        assert state["last_sampled_logged_at"] == "2026-04-25T10:29:00+00:00"

        # Second pass — add 5 MORE rows (still below threshold for the delta).
        # 5 new rows is still < MIN_SAMPLE_THRESHOLD so next run emits
        # insufficient-sample — confirming the state cutoff correctly
        # discarded the 30 already-sampled rows.
        with open(isolated["shadow_log"], "a", encoding="utf-8") as fh:
            for i in range(5):
                fh.write(json.dumps(
                    _row(logged_at=f"2026-04-25T11:{i:02d}:00+00:00")
                ) + "\n")
        rc = mod.run(skip_git_commit=True, week_label="2026-18")
        assert rc == 0
        content = (isolated["digest_dir"] / "week_2026-18.md").read_text(encoding="utf-8")
        assert "insufficient sample" in content.lower()


class TestCliGitDefault:

    def test_run_skips_git_by_default(self, monkeypatch, isolated):
        rows = [
            _row(logged_at=f"2026-04-25T10:{i:02d}:00+00:00") for i in range(30)
        ]
        _write_jsonl(isolated["shadow_log"], rows)
        git_calls = []

        monkeypatch.setattr(
            mod,
            "_git_commit",
            lambda *args, **kwargs: git_calls.append((args, kwargs)),
        )

        assert mod.run(week_label="2026-17") == 0
        assert git_calls == []

    def test_main_skips_git_by_default(self, monkeypatch):
        calls = []

        class HaltSnapshot:
            active = False

        monkeypatch.setattr(
            mod,
            "read_runtime_halt_state",
            lambda *args, **kwargs: HaltSnapshot(),
        )
        monkeypatch.setattr(
            mod,
            "run",
            lambda **kwargs: calls.append(kwargs) or 0,
        )
        monkeypatch.delenv("GTOS_DIVERGENCE_SAMPLER_GIT_COMMIT", raising=False)

        assert mod.main(["--week", "2026-17"]) == 0
        assert calls[-1]["skip_git_commit"] is True

    def test_main_allows_explicit_git_opt_in(self, monkeypatch):
        calls = []

        class HaltSnapshot:
            active = False

        monkeypatch.setattr(
            mod,
            "read_runtime_halt_state",
            lambda *args, **kwargs: HaltSnapshot(),
        )
        monkeypatch.setattr(
            mod,
            "run",
            lambda **kwargs: calls.append(kwargs) or 0,
        )
        monkeypatch.delenv("GTOS_DIVERGENCE_SAMPLER_GIT_COMMIT", raising=False)

        assert mod.main(["--week", "2026-17", "--git"]) == 0
        assert calls[-1]["skip_git_commit"] is False


# ---------------------------------------------------------------------------
# 6) ISO week helper
# ---------------------------------------------------------------------------


class TestIsoWeek:

    def test_current_iso_week_format(self):
        from datetime import date
        assert mod.current_iso_week(date(2026, 4, 24)) == "2026-17"
        # Year boundary sanity.
        assert mod.current_iso_week(date(2026, 1, 1)) == "2026-01"

    def test_current_iso_week_default_is_today_utc(self):
        # Default path exists and returns YYYY-WW.
        label = mod.current_iso_week()
        assert len(label) == 7
        assert label[4] == "-"
        year, week = label.split("-")
        assert int(year) >= 2026
        assert 1 <= int(week) <= 53

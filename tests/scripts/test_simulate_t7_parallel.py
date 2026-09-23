"""Tests for scripts/simulate_t7_parallel.py.

The wrapper splits a date range into N contiguous slices and shells out to
``scripts/simulate_t7_live_period.py`` once per slice. These tests cover:

* Slicing math — contiguity, no overlap, edge cases.
* Subprocess spawning — mocked Popen verifies parallel-window behaviour.
* Aggregation — deterministic merge of per-slice JSON regardless of input order.
* Failure isolation — one slice fail still produces a consolidated file with
  ``failed_slices`` populated and exit code 1.
* ``--resume`` — slices with valid on-disk results are skipped.
* ``--dry-run`` — no subprocess is spawned and the plan is printed.

No real LLM API calls; no real subprocesses. Subprocess.Popen is monkeypatched
to a fake that immediately writes a synthetic ``all_results.json``.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the script is importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import scripts.simulate_t7_parallel as parallel  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════
# Section 1 — slicing math
# ══════════════════════════════════════════════════════════════════════════


def test_slicing_4month_range_n12_no_gaps_no_overlaps(tmp_path):
    """4-month range with N=12 must cover every day exactly once."""
    start = date(2026, 1, 2)
    end = date(2026, 4, 13)
    slices = parallel.plan_slices(start, end, 12, tmp_path)

    assert len(slices) == 12
    assert slices[0].start == start
    assert slices[-1].end == end

    # Walk slices and confirm contiguity.
    for prev, nxt in zip(slices, slices[1:]):
        assert prev.end + timedelta(days=1) == nxt.start, \
            f"gap/overlap between slice {prev.index} and slice {nxt.index}"

    # Day-count cover: every calendar day must appear in exactly one slice.
    covered = set()
    for slc in slices:
        d = slc.start
        while d <= slc.end:
            assert d not in covered, f"day {d} appears in multiple slices"
            covered.add(d)
            d += timedelta(days=1)
    expected_days = (end - start).days + 1
    assert len(covered) == expected_days


def test_slicing_lengths_within_one_day(tmp_path):
    """Distribution should keep slices within ±1 day of each other."""
    slices = parallel.plan_slices(date(2026, 1, 2), date(2026, 4, 13), 12, tmp_path)
    lengths = [(s.end - s.start).days + 1 for s in slices]
    assert max(lengths) - min(lengths) <= 4, \
        ("slice lengths vary beyond expected envelope: "
         f"{lengths} (variation comes from weekend-shift hygiene + base/remainder split)")


def test_slicing_1day_range_n12_collapses_to_1_slice(tmp_path):
    """If the range is shorter than N, emit min(span, N) slices — never empty."""
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 1, 5), 12, tmp_path)
    assert len(slices) == 1
    assert slices[0].start == slices[0].end == date(2026, 1, 5)


def test_slicing_5day_range_n12_emits_one_per_day(tmp_path):
    """A 5-day range with N=12 should produce 5 single-day slices."""
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 1, 9), 12, tmp_path)
    assert len(slices) == 5
    for slc in slices:
        assert slc.start == slc.end


def test_slicing_n_slices_equals_total_days_one_per_day(tmp_path):
    """When N == total days, every slice is exactly 1 day."""
    slices = parallel.plan_slices(date(2026, 1, 2), date(2026, 1, 8), 7, tmp_path)
    assert len(slices) == 7
    for slc in slices:
        assert (slc.end - slc.start).days == 0


def test_slicing_rejects_end_before_start(tmp_path):
    with pytest.raises(ValueError):
        parallel.plan_slices(date(2026, 2, 5), date(2026, 2, 1), 4, tmp_path)


def test_slicing_rejects_zero_or_negative_n(tmp_path):
    with pytest.raises(ValueError):
        parallel.plan_slices(date(2026, 1, 2), date(2026, 4, 13), 0, tmp_path)


def test_slicing_per_slice_output_dir_uses_tag(tmp_path):
    """Each slice's output_dir should be a unique subdirectory of base_output_dir."""
    slices = parallel.plan_slices(date(2026, 1, 2), date(2026, 4, 13), 12, tmp_path)
    out_dirs = {slc.output_dir for slc in slices}
    assert len(out_dirs) == 12  # all unique
    for slc in slices:
        assert slc.output_dir.parent == tmp_path
        assert slc.output_dir.name == slc.tag


def test_slicing_n1_returns_full_window(tmp_path):
    """N=1 should produce one slice covering exactly the requested window."""
    start, end = date(2026, 2, 1), date(2026, 2, 28)
    slices = parallel.plan_slices(start, end, 1, tmp_path)
    assert len(slices) == 1
    assert slices[0].start == start
    assert slices[0].end == end


# ══════════════════════════════════════════════════════════════════════════
# Section 2 — subprocess spawning (mocked)
# ══════════════════════════════════════════════════════════════════════════


class _FakeProc:
    """Minimal stand-in for subprocess.Popen.

    Mirrors the small subset of Popen behaviour the wrapper relies on:
    ``poll()`` returning the deferred return code after ``ready_after_polls``
    polls (so we can simulate concurrency windows). Optionally writes a
    synthetic ``all_results.json`` into the slice output dir on construction
    to mirror what the real inner simulator would have produced.
    """

    def __init__(self, returncode=0, ready_after_polls=1, output_dir=None,
                 results=None, write_output=True):
        self._returncode = returncode
        self._polls_remaining = ready_after_polls
        self.output_dir = Path(output_dir) if output_dir else None
        self._wrote = False
        self._results = results or []
        self._write_output = write_output

    def poll(self):
        if self._polls_remaining > 0:
            self._polls_remaining -= 1
            return None
        # On first "completion" poll, write the synthetic per-slice output
        # the way the real inner simulator would.
        if not self._wrote and self._write_output and self.output_dir is not None:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "start": "n/a",
                "end": "n/a",
                "total_cost": 1.5,
                "results": self._results,
            }
            with open(self.output_dir / "all_results.json", "w", encoding="utf-8") as f:
                json.dump(payload, f)
            self._wrote = True
        return self._returncode


def _fake_args(symbol="XAUUSD", start="2026-01-02", end="2026-04-13",
               slices=12, output_dir="/tmp/out", **overrides):
    """Build an argparse Namespace stand-in that the wrapper functions accept."""
    import argparse
    ns = argparse.Namespace(
        source="csv",
        data_dir="data/historical_2026",
        start=start,
        end=end,
        symbol=symbol,
        slices=slices,
        budget=30.0,
        output_dir=output_dir,
        max_concurrent=None,
        dry_run=False,
        resume=False,
    )
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


def test_run_slices_spawns_one_subprocess_per_slice(tmp_path, monkeypatch):
    """Every planned slice must trigger exactly one Popen call when not resumed."""
    args = _fake_args(output_dir=str(tmp_path), slices=4,
                      start="2026-01-05", end="2026-01-30")
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 1, 30), 4, tmp_path)

    spawn_log: list[list[str]] = []

    def fake_popen(cmd, stdout=None, stderr=None, cwd=None):
        spawn_log.append(cmd)
        # Match output_dir from the cmd args so the fake writes the right file.
        out_dir = cmd[cmd.index("--output-dir") + 1]
        return _FakeProc(returncode=0, ready_after_polls=1, output_dir=out_dir,
                         results=[{"candle_time": "2026-01-15T07:00:00Z",
                                   "symbol": "XAUUSD",
                                   "kill_zone": "london"}])

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    results = parallel.run_slices(slices, args, inner_script, max_concurrent=4)

    assert len(spawn_log) == 4
    assert all(r.succeeded for r in results)
    # Verify each spawned cmd has the right --start/--end/--symbol/--output-dir.
    for cmd, slc in zip(spawn_log, slices):
        assert "--start" in cmd and slc.start.isoformat() in cmd
        assert "--end" in cmd and slc.end.isoformat() in cmd
        assert "--symbol" in cmd and "XAUUSD" in cmd
        assert "--output-dir" in cmd
        assert str(slc.output_dir) in cmd


def test_run_slices_respects_max_concurrent(tmp_path, monkeypatch):
    """Concurrency window must cap simultaneous processes at max_concurrent."""
    args = _fake_args(output_dir=str(tmp_path), slices=6,
                      start="2026-01-05", end="2026-02-15")
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 2, 15), 6, tmp_path)

    inflight: list[int] = []
    peak = {"max": 0}

    class _SlowFakeProc(_FakeProc):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            inflight.append(1)
            peak["max"] = max(peak["max"], len(inflight))

        def poll(self):
            rc = super().poll()
            if rc is not None and inflight:
                inflight.pop()
            return rc

    def fake_popen(cmd, stdout=None, stderr=None, cwd=None):
        out_dir = cmd[cmd.index("--output-dir") + 1]
        # Each process needs 3 polls to "finish" so the wrapper has time
        # to fill the concurrency window before any slice completes.
        return _SlowFakeProc(returncode=0, ready_after_polls=3, output_dir=out_dir)

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    parallel.run_slices(slices, args, inner_script, max_concurrent=2)

    assert peak["max"] <= 2, f"observed {peak['max']} concurrent (cap was 2)"


# ══════════════════════════════════════════════════════════════════════════
# Section 3 — aggregation determinism
# ══════════════════════════════════════════════════════════════════════════


def _write_slice_payload(slice_dir: Path, results: list[dict], total_cost: float = 1.0):
    slice_dir.mkdir(parents=True, exist_ok=True)
    payload = {"start": "x", "end": "y", "total_cost": total_cost, "results": results}
    with open(slice_dir / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f)


def test_aggregator_deterministic_order(tmp_path):
    """3 mock slice files → consolidated must be sorted by slice index then candle_time."""
    base = tmp_path
    start = date(2026, 1, 5)
    end = date(2026, 1, 25)
    slices = parallel.plan_slices(start, end, 3, base)

    # Write SLICE 1 with shuffled internal order.
    _write_slice_payload(slices[0].output_dir, [
        {"candle_time": "2026-01-08T13:00:00Z", "symbol": "XAUUSD", "kill_zone": "ny"},
        {"candle_time": "2026-01-06T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
        {"candle_time": "2026-01-07T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
    ])
    # Slice 2 with one row.
    _write_slice_payload(slices[1].output_dir, [
        {"candle_time": "2026-01-15T13:00:00Z", "symbol": "XAUUSD", "kill_zone": "ny"},
    ])
    # Slice 3 with shuffled order.
    _write_slice_payload(slices[2].output_dir, [
        {"candle_time": "2026-01-25T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
        {"candle_time": "2026-01-22T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
    ])

    # Pretend all three succeeded.
    slice_results = [
        parallel.SliceResult(slc=s, returncode=0, stdout_path=None) for s in slices
    ]

    consolidated = parallel.aggregate_results(slices, slice_results, "XAUUSD", start, end)

    times = [r["candle_time"] for r in consolidated["results"]]
    # Must be in ascending chronological order — confirms (slice index, candle_time)
    # sort produces the right global ordering.
    assert times == sorted(times)
    assert consolidated["n_slices_succeeded"] == 3
    assert consolidated["n_slices_failed"] == 0
    assert consolidated["failed_slices"] == []


def test_aggregator_idempotent_same_inputs_same_output(tmp_path):
    """Re-running the aggregator on the same inputs produces byte-identical output."""
    base = tmp_path
    start = date(2026, 1, 5)
    end = date(2026, 1, 19)
    slices = parallel.plan_slices(start, end, 3, base)
    rows = [{"candle_time": f"2026-01-{day:02d}T07:00:00Z",
             "symbol": "XAUUSD", "kill_zone": "london"} for day in (6, 8, 10)]
    for slc, row in zip(slices, rows):
        _write_slice_payload(slc.output_dir, [row])
    slice_results = [
        parallel.SliceResult(slc=s, returncode=0, stdout_path=None) for s in slices
    ]
    a = parallel.aggregate_results(slices, slice_results, "XAUUSD", start, end)
    b = parallel.aggregate_results(slices, slice_results, "XAUUSD", start, end)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ══════════════════════════════════════════════════════════════════════════
# Section 4 — failure handling
# ══════════════════════════════════════════════════════════════════════════


def test_aggregator_handles_one_failed_slice_of_three(tmp_path):
    """1/3 slices fails → consolidated has 2 successful slices + failed_slices entry."""
    base = tmp_path
    start = date(2026, 1, 5)
    end = date(2026, 1, 25)
    slices = parallel.plan_slices(start, end, 3, base)

    _write_slice_payload(slices[0].output_dir, [
        {"candle_time": "2026-01-06T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
    ])
    # NOTE: slices[1] gets NO output (simulating crash)
    _write_slice_payload(slices[2].output_dir, [
        {"candle_time": "2026-01-22T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
    ])

    slice_results = [
        parallel.SliceResult(slc=slices[0], returncode=0, stdout_path=None),
        parallel.SliceResult(slc=slices[1], returncode=2,
                             stdout_path=slices[1].output_dir / "run.log"),
        parallel.SliceResult(slc=slices[2], returncode=0, stdout_path=None),
    ]

    consolidated = parallel.aggregate_results(slices, slice_results, "XAUUSD", start, end)
    assert consolidated["n_slices_succeeded"] == 2
    assert consolidated["n_slices_failed"] == 1
    assert len(consolidated["failed_slices"]) == 1
    assert consolidated["failed_slices"][0]["index"] == 2
    assert consolidated["failed_slices"][0]["returncode"] == 2
    # Success-path rows are still preserved + chronologically ordered.
    assert len(consolidated["results"]) == 2
    assert consolidated["results"][0]["candle_time"] < consolidated["results"][1]["candle_time"]


def test_main_exit_code_1_when_any_slice_fails(tmp_path, monkeypatch):
    """End-to-end: when one slice exits non-zero, main() returns 1."""
    base = tmp_path / "out"
    base.mkdir()

    call_count = {"n": 0}

    def fake_popen(cmd, stdout=None, stderr=None, cwd=None):
        call_count["n"] += 1
        out_dir = cmd[cmd.index("--output-dir") + 1]
        # First slice fails, rest succeed.
        if call_count["n"] == 1:
            return _FakeProc(returncode=2, ready_after_polls=1, output_dir=out_dir,
                             write_output=False)
        return _FakeProc(returncode=0, ready_after_polls=1, output_dir=out_dir,
                         results=[{"candle_time": "2026-01-15T07:00:00Z",
                                   "symbol": "XAUUSD",
                                   "kill_zone": "london"}])

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    rc = parallel.main([
        "--source", "csv",
        "--data-dir", "data/historical_2026",
        "--start", "2026-01-05",
        "--end", "2026-01-30",
        "--symbol", "XAUUSD",
        "--slices", "3",
        "--budget", "5",
        "--output-dir", str(base),
    ])
    assert rc == 1

    # Consolidated file is still present, with failed_slices populated.
    consolidated_path = base / parallel.consolidated_filename(
        "XAUUSD", date(2026, 1, 5), date(2026, 1, 30)
    )
    assert consolidated_path.exists()
    with open(consolidated_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["n_slices_failed"] == 1
    assert data["n_slices_succeeded"] == 2


# ══════════════════════════════════════════════════════════════════════════
# Section 5 — --resume
# ══════════════════════════════════════════════════════════════════════════


def test_resume_skips_existing_slice_output(tmp_path, monkeypatch):
    """A slice with valid all_results.json must be skipped (no Popen call)."""
    base = tmp_path / "out"
    base.mkdir()
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 1, 30), 3, base)

    # Pre-populate slice 1 with a valid output → must be skipped.
    _write_slice_payload(slices[0].output_dir, [
        {"candle_time": "2026-01-06T07:00:00Z", "symbol": "XAUUSD", "kill_zone": "london"},
    ])

    spawn_log: list[list[str]] = []

    def fake_popen(cmd, stdout=None, stderr=None, cwd=None):
        spawn_log.append(cmd)
        out_dir = cmd[cmd.index("--output-dir") + 1]
        return _FakeProc(returncode=0, ready_after_polls=1, output_dir=out_dir,
                         results=[{"candle_time": "2026-01-15T07:00:00Z",
                                   "symbol": "XAUUSD",
                                   "kill_zone": "london"}])

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    args = _fake_args(output_dir=str(base), slices=3,
                      start="2026-01-05", end="2026-01-30", resume=True)
    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    results = parallel.run_slices(slices, args, inner_script, max_concurrent=3)

    # Slice 1 was skipped (already done) → only 2 spawns.
    assert len(spawn_log) == 2
    skipped = [r for r in results if r.skipped]
    assert len(skipped) == 1
    assert skipped[0].slc.index == 1


def test_resume_does_not_skip_invalid_existing_output(tmp_path, monkeypatch):
    """A slice with non-parseable all_results.json must NOT be skipped (re-run)."""
    base = tmp_path / "out"
    base.mkdir()
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 1, 19), 3, base)

    # Slice 1 has a corrupt output file.
    slices[0].output_dir.mkdir(parents=True, exist_ok=True)
    (slices[0].output_dir / "all_results.json").write_text("not valid json {{{")

    spawn_log: list[list[str]] = []

    def fake_popen(cmd, stdout=None, stderr=None, cwd=None):
        spawn_log.append(cmd)
        out_dir = cmd[cmd.index("--output-dir") + 1]
        return _FakeProc(returncode=0, ready_after_polls=1, output_dir=out_dir,
                         results=[])

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    args = _fake_args(output_dir=str(base), slices=3,
                      start="2026-01-05", end="2026-01-19", resume=True)
    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    parallel.run_slices(slices, args, inner_script, max_concurrent=3)

    # All 3 slices were spawned (corrupt slice was re-run).
    assert len(spawn_log) == 3


# ══════════════════════════════════════════════════════════════════════════
# Section 6 — --dry-run
# ══════════════════════════════════════════════════════════════════════════


def test_dry_run_does_not_spawn_subprocess(tmp_path, monkeypatch, capsys):
    """--dry-run must print the plan without calling Popen at all."""
    base = tmp_path / "out"

    def fake_popen(*a, **kw):
        pytest.fail("Popen was called during --dry-run — that's a regression.")

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    rc = parallel.main([
        "--source", "csv",
        "--data-dir", "data/historical_2026",
        "--start", "2026-01-02",
        "--end", "2026-04-13",
        "--symbol", "XAUUSD",
        "--slices", "12",
        "--budget", "30",
        "--output-dir", str(base),
        "--dry-run",
    ])
    assert rc == 0

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "DRY RUN" in output
    # All 12 slice tags should appear in the plan.
    slices = parallel.plan_slices(date(2026, 1, 2), date(2026, 4, 13), 12, base)
    for slc in slices:
        assert slc.tag in output, f"missing slice {slc.tag} in dry-run output"
    # The consolidated output filename should be advertised.
    expected_consolidated = parallel.consolidated_filename(
        "XAUUSD", slices[0].start, slices[-1].end
    )
    assert expected_consolidated in output


def test_dry_run_marks_resumed_slices(tmp_path, monkeypatch, capsys):
    """--dry-run --resume must annotate slices that would be skipped."""
    base = tmp_path / "out"
    base.mkdir()
    slices = parallel.plan_slices(date(2026, 1, 5), date(2026, 1, 19), 3, base)
    _write_slice_payload(slices[0].output_dir, [])

    def fake_popen(*a, **kw):  # pragma: no cover
        pytest.fail("Popen called during --dry-run")

    monkeypatch.setattr(parallel.subprocess, "Popen", fake_popen)

    rc = parallel.main([
        "--source", "csv",
        "--data-dir", "data/historical_2026",
        "--start", "2026-01-05",
        "--end", "2026-01-19",
        "--symbol", "XAUUSD",
        "--slices", "3",
        "--budget", "5",
        "--output-dir", str(base),
        "--dry-run",
        "--resume",
    ])
    assert rc == 0
    output = capsys.readouterr().out
    # The first slice's tag should have a [RESUMED] annotation.
    first_line_match = [ln for ln in output.splitlines() if slices[0].tag in ln]
    assert any("[RESUMED]" in ln for ln in first_line_match), \
        "expected [RESUMED] annotation on the pre-populated slice"


# ══════════════════════════════════════════════════════════════════════════
# Section 7 — concurrency cap resolution
# ══════════════════════════════════════════════════════════════════════════


def test_resolve_max_concurrent_default_caps_at_hard_limit(monkeypatch):
    """Default = min(slices, cpu, 16). 32 slices on a 64-core box → cap 16."""
    monkeypatch.setattr(parallel.os, "cpu_count", lambda: 64)
    assert parallel.resolve_max_concurrent(32, None) == parallel.MAX_CONCURRENT_HARD_CAP


def test_resolve_max_concurrent_default_caps_at_cpu_count(monkeypatch):
    """If cpu < 16, the cpu count wins."""
    monkeypatch.setattr(parallel.os, "cpu_count", lambda: 4)
    assert parallel.resolve_max_concurrent(12, None) == 4


def test_resolve_max_concurrent_default_caps_at_slice_count(monkeypatch):
    """If slices < cpu and < 16, slice count wins."""
    monkeypatch.setattr(parallel.os, "cpu_count", lambda: 32)
    assert parallel.resolve_max_concurrent(3, None) == 3


def test_resolve_max_concurrent_user_override_capped_at_hard_limit():
    """User can request 32 but is silently capped at MAX_CONCURRENT_HARD_CAP."""
    assert parallel.resolve_max_concurrent(32, 32) == parallel.MAX_CONCURRENT_HARD_CAP


def test_resolve_max_concurrent_rejects_zero_and_negative():
    with pytest.raises(ValueError):
        parallel.resolve_max_concurrent(12, 0)
    with pytest.raises(ValueError):
        parallel.resolve_max_concurrent(12, -1)


# ══════════════════════════════════════════════════════════════════════════
# Section 8 — build_command shape
# ══════════════════════════════════════════════════════════════════════════


def test_build_command_replaces_start_and_end_with_slice_boundaries(tmp_path):
    """The spawned cmd must use the SLICE's dates, not the wrapper-level dates."""
    args = _fake_args(output_dir=str(tmp_path), slices=4,
                      start="2026-01-02", end="2026-04-13")
    slices = parallel.plan_slices(date(2026, 1, 2), date(2026, 4, 13), 4, tmp_path)
    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    cmd = parallel.build_command(slices[1], args, inner_script)
    # Slice 2's dates must appear, the wrapper-level overall dates must NOT.
    assert slices[1].start.isoformat() in cmd
    assert slices[1].end.isoformat() in cmd
    # Sanity: --output-dir points into the slice subdir, not the base.
    out_idx = cmd.index("--output-dir")
    assert cmd[out_idx + 1] == str(slices[1].output_dir)


def test_build_command_passes_through_data_dir_and_dry_run(tmp_path):
    args = _fake_args(output_dir=str(tmp_path), slices=2,
                      start="2026-01-02", end="2026-01-15",
                      data_dir="data/historical_2026", dry_run=True)
    slices = parallel.plan_slices(date(2026, 1, 2), date(2026, 1, 15), 2, tmp_path)
    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    cmd = parallel.build_command(slices[0], args, inner_script)
    assert "--data-dir" in cmd
    assert "data/historical_2026" in cmd
    assert "--dry-run" in cmd

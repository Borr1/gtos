"""Tests for L58 F3-replay engine + CLI driver.

Coverage:
  - load_historical_candidates: 5 synthetic fixtures load into 5
    HistoricalCandidate objects with deterministic ordering
  - Date filter excludes outside-range candidates
  - Instrument filter excludes other instruments
  - Realized-R join: 3 of 5 fixtures match a synthetic trade record →
    3 candidates have realized_r set, 2 None
  - RecordedReplayEvaluator returns the historical decision verbatim
    (A=B for all candidates → zero divergence)
  - MockReplayEvaluator(seed=N): deterministic outputs (same seed →
    same results; different seeds → some divergence)
  - ReplayRun end-to-end: JSONL + Markdown emitted; counts match
  - --dry-run exits 0 without writing output files
  - Hookable: before_evaluate / after_evaluate callbacks fire per pass

The synthetic fixture file lives at::

    tests/scripts/fixtures/f3_replay_test_candidates.jsonl

It is built to mimic the per-instrument JSONL layout used by the
orchestrator's evaluation logger so the loader has realistic shape to
parse. Synthetic fixtures only — never real production rows.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

import pytest

from src.research_infra import f3_replay_engine as engine
from scripts.research import f3_replay as cli


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "f3_replay_test_candidates.jsonl"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_synthetic_eval_dir(tmp_path: Path) -> Path:
    """Lay out a tmp eval_dir with the per-instrument JSONL layout.

    Splits the bundled 5-row fixture across instrument subdirectories
    by row.symbol, mirroring ``knowledge_base/live_evaluations/``.
    """
    eval_dir = tmp_path / "live_evaluations"
    eval_dir.mkdir()
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    # group by symbol
    by_symbol: dict[str, list[dict]] = {}
    for r in rows:
        by_symbol.setdefault(r["symbol"], []).append(r)
    for symbol, entries in by_symbol.items():
        sym_dir = eval_dir / symbol
        sym_dir.mkdir()
        # Write one JSONL per date (use the candle_time date)
        by_date: dict[str, list[dict]] = {}
        for e in entries:
            date_str = e["candle_time"][:10]
            by_date.setdefault(date_str, []).append(e)
        for date_str, lst in by_date.items():
            f = sym_dir / f"{date_str}.jsonl"
            with f.open("w", encoding="utf-8") as out:
                for e in lst:
                    out.write(json.dumps(e) + "\n")
    return eval_dir


def _build_trade_records_dir(
    tmp_path: Path,
    matching_subset: list[str],
) -> Path:
    """Build a synthetic trade-records dir with realized R for the rows
    listed in ``matching_subset`` (cand_id list).

    Each entry is a minimal dict with the metadata + decision_pipeline
    fields the loader's join helper looks at.
    """
    rec_dir = tmp_path / "trade_records"
    rec_dir.mkdir()
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    for row in rows:
        # Construct the cand_id the loader would produce
        ts = engine._normalize_to_utc_minute(row["candle_time"])
        cid = engine._make_cand_id(row["symbol"], ts)
        if cid not in matching_subset:
            continue
        symbol = row["symbol"]
        sub = rec_dir / symbol
        sub.mkdir(exist_ok=True)
        side = (row.get("trade_parameters") or {}).get("direction")
        # Pick a deterministic R: bullish CAND → +1.5, bearish CAND →
        # -1.0, NO_TRADE never reaches here.
        r = 1.5 if side == "LONG" else (-1.0 if side == "SHORT" else 0.0)
        # Sanitize cand_id for Windows filename (no colons / pipes)
        safe_stem = cid.replace("|", "_").replace(":", "")
        rec = {
            "metadata": {
                "trade_id": safe_stem,
                "symbol": symbol,
                "candle_time": row["candle_time"],
            },
            "decision_pipeline": {
                "ai_decision": row.get("decision", ""),
                "ai_direction": side,
                "outcome": {"r_multiple": r},
            },
        }
        path = sub / f"{safe_stem}.json"
        with path.open("w", encoding="utf-8") as out:
            json.dump(rec, out)
    return rec_dir


# ---------------------------------------------------------------------------
# Tests — load_historical_candidates
# ---------------------------------------------------------------------------


def test_load_historical_candidates_basic(tmp_path):
    """5 synthetic JSONLs → 5 candidates loaded; deterministic order."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)
    assert len(cands) == 5
    # Deterministic sort by (candle_close_time, symbol)
    times = [c.candle_close_time for c in cands]
    assert times == sorted(times)
    # Identifier shape
    for c in cands:
        assert isinstance(c, engine.HistoricalCandidate)
        assert c.cand_id.startswith(c.symbol + "|")
        assert c.candle_close_time.tzinfo is not None
        assert c.candle_close_time.second == 0
        assert c.candle_close_time.microsecond == 0


def test_load_historical_candidates_deterministic_repeat(tmp_path):
    """Two consecutive loads with identical inputs MUST return equal
    lists. This is the property ReplayRun relies on for stable
    replay_results.jsonl across re-runs."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    a = engine.load_historical_candidates(eval_dir=eval_dir)
    b = engine.load_historical_candidates(eval_dir=eval_dir)
    assert len(a) == len(b)
    for ca, cb in zip(a, b):
        assert ca.cand_id == cb.cand_id
        assert ca.candle_close_time == cb.candle_close_time
        assert ca.symbol == cb.symbol


def test_load_historical_candidates_empty_dir(tmp_path):
    """Missing eval_dir → empty list, no crash."""
    cands = engine.load_historical_candidates(
        eval_dir=tmp_path / "does_not_exist"
    )
    assert cands == []


def test_load_historical_candidates_date_filter(tmp_path):
    """``since`` / ``until`` filters exclude outside-range rows."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    # Fixture spans 2026-01-15 → 2026-03-20
    cands = engine.load_historical_candidates(
        eval_dir=eval_dir,
        since=dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc),
        until=dt.datetime(2026, 3, 16, tzinfo=dt.timezone.utc),
    )
    # Should exclude the 2026-01-15 XAU row + the 2026-03-20 XAU row
    assert len(cands) == 3
    lo = dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc)
    hi = dt.datetime(2026, 3, 16, tzinfo=dt.timezone.utc)
    for c in cands:
        assert lo <= c.candle_close_time <= hi


def test_load_historical_candidates_instrument_filter(tmp_path):
    """``instruments`` filter is case-insensitive and excludes other
    instruments."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(
        eval_dir=eval_dir, instruments=["xauusd"]
    )
    assert len(cands) == 2  # both XAU rows from fixture
    for c in cands:
        assert c.symbol == "XAUUSD"


def test_load_historical_candidates_unknown_instrument(tmp_path):
    """Filtering on an instrument with no eval files → empty list,
    no crash."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(
        eval_dir=eval_dir, instruments=["NIKKEI"]
    )
    assert cands == []


def test_load_historical_candidates_drops_unparseable_rows(tmp_path):
    """Rows missing candle_time / symbol / with malformed JSON are
    dropped with a warning, NOT a hard error."""
    eval_dir = tmp_path / "live_evaluations"
    sym_dir = eval_dir / "XAUUSD"
    sym_dir.mkdir(parents=True)
    f = sym_dir / "2026-04-15.jsonl"
    f.write_text(
        "\n".join(
            [
                # missing candle_time
                json.dumps({"symbol": "XAUUSD", "decision": "NO_TRADE"}),
                # missing symbol AND in inferred dir
                json.dumps(
                    {
                        "candle_time": "2026-04-15T07:30:00+00:00",
                        "decision": "NO_TRADE",
                    }
                ),
                # malformed JSON
                "{not-json",
                # valid row
                json.dumps(
                    {
                        "candle_time": "2026-04-15T08:00:00+00:00",
                        "symbol": "XAUUSD",
                        "decision": "CANDIDATE",
                        "framework": "ob_retest",
                        "trade_parameters": {"direction": "LONG"},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    cands = engine.load_historical_candidates(eval_dir=eval_dir)
    # The middle "missing-symbol" row should still be parsed since the
    # loader falls back to the directory name. Malformed JSON dropped.
    # The first row (missing candle_time) is dropped.
    assert len(cands) == 2
    for c in cands:
        assert c.symbol == "XAUUSD"


# ---------------------------------------------------------------------------
# Tests — realized-R join
# ---------------------------------------------------------------------------


def test_realized_r_join_three_of_five(tmp_path):
    """Build a trade-records dir matching 3 of 5 fixture candidates;
    confirm 3 join + 2 None."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    # Pre-load to learn the cand_ids
    cands_no_join = engine.load_historical_candidates(eval_dir=eval_dir)
    cand_ids_to_match = [c.cand_id for c in cands_no_join[:3]]

    rec_dir = _build_trade_records_dir(tmp_path, cand_ids_to_match)

    cands = engine.load_historical_candidates(
        eval_dir=eval_dir, trade_records_dir=rec_dir
    )
    assert len(cands) == 5
    matched = [c for c in cands if c.realized_r is not None]
    unmatched = [c for c in cands if c.realized_r is None]
    assert len(matched) == 3
    assert len(unmatched) == 2
    # CR-LONG synthetic R = 1.5, CR-SHORT = -1.0; NO_TRADE rows are not
    # in the trade-record set (we only matched the first 3 cand_ids).
    for c in matched:
        assert c.realized_r in {1.5, -1.0, 0.0}


def test_realized_r_join_microsecond_normalization(tmp_path):
    """Trade record candle_time with microseconds joins to a fixture
    that has whole-minute timestamp."""
    eval_dir = tmp_path / "live_evaluations"
    sym_dir = eval_dir / "XAUUSD"
    sym_dir.mkdir(parents=True)
    f = sym_dir / "2026-04-15.jsonl"
    f.write_text(
        json.dumps(
            {
                "candle_time": "2026-04-15T07:00:00Z",
                "symbol": "XAUUSD",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_parameters": {"direction": "LONG"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    rec_dir = tmp_path / "trade_records" / "XAUUSD"
    rec_dir.mkdir(parents=True)
    rec = {
        "metadata": {
            "trade_id": "rec",
            "symbol": "XAUUSD",
            "candle_time": "2026-04-15T07:00:42.123456+00:00",
        },
        "decision_pipeline": {
            "ai_decision": "CANDIDATE",
            "ai_direction": "LONG",
            "outcome": {"r_multiple": 2.0},
        },
    }
    (rec_dir / "rec.json").write_text(json.dumps(rec), encoding="utf-8")
    cands = engine.load_historical_candidates(
        eval_dir=eval_dir,
        trade_records_dir=rec_dir.parent,
    )
    assert len(cands) == 1
    assert cands[0].realized_r == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Tests — RecordedReplayEvaluator
# ---------------------------------------------------------------------------


def test_recorded_evaluator_returns_verbatim(tmp_path):
    """RecordedReplayEvaluator MUST return decision + side from the
    historical record verbatim → A=B for all candidates → zero
    divergence when paired with itself."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)
    assert len(cands) == 5
    a = engine.RecordedReplayEvaluator()
    b = engine.RecordedReplayEvaluator()
    for c in cands:
        da = a.evaluate(c)
        db = b.evaluate(c)
        assert da.decision == db.decision
        assert da.side == db.side
        # Must equal what was originally recorded
        assert da.decision == c.decision_recorded["decision"]
        assert da.side == c.decision_recorded["side"]


# ---------------------------------------------------------------------------
# Tests — MockReplayEvaluator
# ---------------------------------------------------------------------------


def test_mock_evaluator_seed_determinism(tmp_path):
    """Same seed → same outputs; different seeds → some divergence."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)

    m1a = engine.MockReplayEvaluator(seed=1)
    m1b = engine.MockReplayEvaluator(seed=1)
    m2 = engine.MockReplayEvaluator(seed=42)

    # Same seed → identical decisions
    for c in cands:
        d_a = m1a.evaluate(c)
        d_b = m1b.evaluate(c)
        assert d_a.decision == d_b.decision
        assert d_a.side == d_b.side

    # Different seed → at least one divergence on the 5 fixtures
    diffs = 0
    for c in cands:
        d1 = m1a.evaluate(c)
        d2 = m2.evaluate(c)
        if d1.decision != d2.decision or d1.side != d2.side:
            diffs += 1
    assert diffs >= 1


def test_mock_evaluator_id_uses_seed():
    e = engine.MockReplayEvaluator(seed=7)
    assert e.evaluator_id == "mock_seed_7"


# ---------------------------------------------------------------------------
# Tests — ReplayRun end-to-end
# ---------------------------------------------------------------------------


def test_replay_run_emits_outputs(tmp_path):
    """Run with mock evaluators → JSONL + Markdown + metadata emitted;
    counts match input fixture count."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)
    out = tmp_path / "run_out"
    run = engine.ReplayRun(
        candidates=cands,
        evaluator_a=engine.MockReplayEvaluator(seed=1),
        evaluator_b=engine.MockReplayEvaluator(seed=2),
        output_dir=out,
        run_tag="test_l58",
    )
    metrics = run.run()
    assert metrics.n_candidates == 5
    # All four output artifacts present
    results = out / "replay_results.jsonl"
    summary = out / "replay_summary.md"
    metadata = out / "run_metadata.json"
    assert results.exists()
    assert summary.exists()
    assert metadata.exists()
    # JSONL row count matches candidates
    with results.open("r", encoding="utf-8") as fh:
        rows = [json.loads(l) for l in fh if l.strip()]
    assert len(rows) == 5
    # Each row carries both evaluator decisions
    for r in rows:
        assert r["evaluator_a"]["id"] == "mock_seed_1"
        assert r["evaluator_b"]["id"] == "mock_seed_2"
    # Summary references the run_tag + harness version
    summary_text = summary.read_text(encoding="utf-8")
    assert "test_l58" in summary_text
    assert engine.HARNESS_VERSION in summary_text
    # Metadata round-trips
    meta = json.loads(metadata.read_text(encoding="utf-8"))
    assert meta["harness_version"] == engine.HARNESS_VERSION
    assert meta["run_tag"] == "test_l58"
    assert meta["n_candidates"] == 5


def test_replay_run_zero_divergence_recorded_vs_recorded(tmp_path):
    """Pairing recorded against recorded MUST produce
    n_decision_diff == 0 and n_side_diff_when_both_cand == 0."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)
    out = tmp_path / "run_baseline"
    metrics = engine.ReplayRun(
        candidates=cands,
        evaluator_a=engine.RecordedReplayEvaluator(),
        evaluator_b=engine.RecordedReplayEvaluator(),
        output_dir=out,
        run_tag="recorded_self",
    ).run()
    assert metrics.n_decision_diff == 0
    assert metrics.n_side_diff_when_both_cand == 0


def test_replay_run_refuses_protected_path(tmp_path):
    """Output directories pointing into knowledge_base/, shadow_logs/,
    pipeline_state/, or logs/ are rejected. Use the project root the
    test resolves to since the engine compares relative-to-project-root.
    """
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)
    # Construct a path that resolves under the actual project root
    bad_path = engine.PROJECT_ROOT / "knowledge_base" / "TEST_REPLAY_OUT_DO_NOT_CREATE"
    run = engine.ReplayRun(
        candidates=cands,
        evaluator_a=engine.MockReplayEvaluator(seed=1),
        evaluator_b=engine.MockReplayEvaluator(seed=1),
        output_dir=bad_path,
        run_tag="should_fail",
    )
    with pytest.raises(ValueError, match="protected path"):
        run.run()


# ---------------------------------------------------------------------------
# Tests — hookable callbacks
# ---------------------------------------------------------------------------


def test_replay_run_hooks_fire_per_evaluator(tmp_path):
    """before_evaluate + after_evaluate must be called once per
    evaluator pass per candidate (so 2× n_candidates per hook)."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)

    before_calls: list[tuple[str, str]] = []
    after_calls: list[tuple[str, str, str]] = []

    def before(cand, evaluator, ctx):
        before_calls.append((cand.cand_id, evaluator.evaluator_id))

    def after(cand, evaluator, ctx):
        last = ctx.get("last_decision")
        after_calls.append(
            (
                cand.cand_id,
                evaluator.evaluator_id,
                last.decision if last else "",
            )
        )

    out = tmp_path / "hook_run"
    metrics = engine.ReplayRun(
        candidates=cands,
        evaluator_a=engine.MockReplayEvaluator(seed=1),
        evaluator_b=engine.MockReplayEvaluator(seed=2),
        output_dir=out,
        run_tag="hook_test",
        before_evaluate=before,
        after_evaluate=after,
    ).run()
    n = metrics.n_candidates
    # 2 evaluator passes per candidate
    assert len(before_calls) == 2 * n
    assert len(after_calls) == 2 * n
    # after-callback received a populated decision via context
    for _cid, _ev, dec_str in after_calls:
        assert dec_str in {"CANDIDATE", "NO_TRADE"}


def test_replay_run_hook_can_inspect_candidate(tmp_path):
    """The hook contract is read-only on the candidate. Confirm the
    callback can read fields without breaking."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    cands = engine.load_historical_candidates(eval_dir=eval_dir)

    seen_symbols: list[str] = []

    def before(cand, evaluator, ctx):
        seen_symbols.append(cand.symbol)
        # Reading is fine; the engine doesn't enforce immutability
        # (doing so would require freezing dataclasses, which conflicts
        # with the realized_r post-load assignment). Tests verify the
        # inspection PATH; the contract documented in the docstring
        # disallows mutation but is enforced by code review, not the
        # type system.

    out = tmp_path / "inspect_run"
    engine.ReplayRun(
        candidates=cands,
        evaluator_a=engine.RecordedReplayEvaluator(),
        evaluator_b=engine.RecordedReplayEvaluator(),
        output_dir=out,
        run_tag="inspect",
        before_evaluate=before,
    ).run()
    # Each candidate seen exactly twice (once per evaluator)
    assert len(seen_symbols) == 2 * len(cands)


# ---------------------------------------------------------------------------
# Tests — CLI driver
# ---------------------------------------------------------------------------


def test_cli_dry_run_exits_zero_no_writes(tmp_path, capsys):
    """``--dry-run`` exits 0 and writes no files."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    out = tmp_path / "dry_out"
    rc = cli.main(
        [
            "--evaluator-a",
            "recorded",
            "--evaluator-b",
            "mock_seed_42",
            "--eval-dir",
            str(eval_dir),
            "--output",
            str(out),
            "--dry-run",
        ]
    )
    assert rc == 0
    assert not out.exists()
    captured = capsys.readouterr()
    assert "DRY-RUN PLAN" in captured.out
    assert "n_candidates:   5" in captured.out


def test_cli_real_run_writes_outputs(tmp_path):
    """CLI end-to-end (mocked evaluators) writes results.jsonl,
    summary.md, run_metadata.json."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    out = tmp_path / "cli_out"
    rc = cli.main(
        [
            "--evaluator-a",
            "recorded",
            "--evaluator-b",
            "mock_seed_1",
            "--eval-dir",
            str(eval_dir),
            "--output",
            str(out),
            "--run-tag",
            "cli_smoke",
        ]
    )
    assert rc == 0
    assert (out / "replay_results.jsonl").exists()
    assert (out / "replay_summary.md").exists()
    assert (out / "run_metadata.json").exists()


def test_cli_unknown_evaluator_exits_two(tmp_path, capsys):
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    out = tmp_path / "bad_out"
    rc = cli.main(
        [
            "--evaluator-a",
            "not_a_real_evaluator",
            "--evaluator-b",
            "recorded",
            "--eval-dir",
            str(eval_dir),
            "--output",
            str(out),
        ]
    )
    assert rc == 2
    assert not out.exists()


def test_cli_live_evaluator_blocked_without_env(tmp_path, monkeypatch):
    """`--evaluator-a live` MUST fail without the env gate AND a client.
    Wave 1 does NOT exercise live."""
    monkeypatch.delenv("GTOS_F3_REPLAY_ALLOW_LIVE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    out = tmp_path / "live_out"
    rc = cli.main(
        [
            "--evaluator-a",
            "live",
            "--evaluator-b",
            "recorded",
            "--eval-dir",
            str(eval_dir),
            "--output",
            str(out),
        ]
    )
    assert rc == 2
    assert not out.exists()


def test_cli_no_candidates_exits_two(tmp_path):
    """Zero candidates loaded → exit 2, no empty run written."""
    empty_eval = tmp_path / "empty_evals"
    empty_eval.mkdir()
    out = tmp_path / "empty_out"
    rc = cli.main(
        [
            "--evaluator-a",
            "recorded",
            "--evaluator-b",
            "mock_seed_1",
            "--eval-dir",
            str(empty_eval),
            "--output",
            str(out),
        ]
    )
    assert rc == 2
    assert not out.exists()


def test_cli_instrument_filter(tmp_path):
    """``--instruments XAUUSD`` excludes USDJPY/US30/GBPUSD rows."""
    eval_dir = _build_synthetic_eval_dir(tmp_path)
    out = tmp_path / "filter_out"
    rc = cli.main(
        [
            "--evaluator-a",
            "recorded",
            "--evaluator-b",
            "recorded",
            "--eval-dir",
            str(eval_dir),
            "--output",
            str(out),
            "--instruments",
            "XAUUSD",
        ]
    )
    assert rc == 0
    rows = [
        json.loads(line)
        for line in (out / "replay_results.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(rows) == 2  # only the 2 XAU fixture rows
    for r in rows:
        assert r["symbol"] == "XAUUSD"


# ---------------------------------------------------------------------------
# Tests — Time normalization helpers
# ---------------------------------------------------------------------------


def test_normalize_to_utc_minute_handles_z_suffix():
    out = engine._normalize_to_utc_minute("2026-04-15T07:30:42Z")
    assert out is not None
    assert out.tzinfo == dt.timezone.utc
    assert out.second == 0
    assert out.microsecond == 0
    assert out.minute == 30


def test_normalize_to_utc_minute_handles_microseconds():
    out = engine._normalize_to_utc_minute(
        "2026-04-15T07:30:42.123456+00:00"
    )
    assert out is not None
    assert out.second == 0
    assert out.microsecond == 0


def test_normalize_to_utc_minute_handles_naive():
    out = engine._normalize_to_utc_minute("2026-04-15T07:30:00")
    assert out is not None
    assert out.tzinfo == dt.timezone.utc


def test_normalize_to_utc_minute_returns_none_for_garbage():
    assert engine._normalize_to_utc_minute(None) is None
    assert engine._normalize_to_utc_minute("") is None
    assert engine._normalize_to_utc_minute("not-a-date") is None


def test_make_cand_id_format():
    ts = dt.datetime(2026, 4, 15, 7, 30, tzinfo=dt.timezone.utc)
    cid = engine._make_cand_id("xauusd", ts)
    assert cid == "XAUUSD|2026-04-15T07:30:00+00:00"


# ---------------------------------------------------------------------------
# Tests — LiveReplayEvaluator gate
# ---------------------------------------------------------------------------


def test_live_evaluator_blocked_by_default(monkeypatch):
    """Construction MUST fail unless the env gate is set."""
    monkeypatch.delenv("GTOS_F3_REPLAY_ALLOW_LIVE", raising=False)
    with pytest.raises(RuntimeError, match="gated"):
        engine.LiveReplayEvaluator()


def test_live_evaluator_requires_client_even_with_env(monkeypatch):
    monkeypatch.setenv("GTOS_F3_REPLAY_ALLOW_LIVE", "1")
    with pytest.raises(RuntimeError, match="client"):
        engine.LiveReplayEvaluator(client=None)

"""Tests for F9 US30 hallucination deep-dive script.

Coverage map
============
Section 1 — ``filter_to_us30``
    only US30_cash rows pass; non-US30 (XAUUSD, USDJPY, etc.) excluded.

Section 2 — ``decompose_per_field``
    n / n_accurate / n_hallucinated / n_misattributed counters roll up
    correctly across multiple checks. ``contribution_pct`` is computed
    relative to the total US30 hallucination count.

Section 3 — ``decompose_per_month`` / ``decompose_per_session`` /
``decompose_per_final_outcome``
    bucketing by period_month / kill_zone / final_outcome key.

Section 4 — ``build_inspection_block``
    schema check — every required field is present + populated.

Section 5 — ``write_breakdown_json`` / ``write_report_md`` /
``write_hallucination_rows_jsonl``
    end-to-end smoke. Output file existence, JSON parseability,
    header rows present.

Section 6 — End-to-end CLI dry run
    `--dry-run` exits 0 + writes nothing.

NO real Anthropic / OpenRouter calls. NO production paths written
(see ``conftest.py`` write guard).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping
from unittest.mock import patch

import pytest

# Resolve project root so we can import without install
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.hallucination_measurement import (  # noqa: E402
    EvaluationCheck,
    PriceClassification,
)

import scripts.research.run_f9_us30_hallucination_deepdive as cli  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════
# Test fixtures
# ════════════════════════════════════════════════════════════════════════════


def _make_classification(
    role: str,
    value: float,
    classification: str,
    *,
    matched_mso_field: str = "",
    matched_mso_value: float = 0.0,
    delta_ticks: float = 0.0,
    note: str = "",
) -> PriceClassification:
    return PriceClassification(
        role=role,
        value=value,
        source_field=f"trade_parameters.{role}",
        classification=classification,
        matched_mso_field=matched_mso_field or None,
        matched_mso_value=matched_mso_value or None,
        delta_ticks=delta_ticks or None,
        note=note or None,
    )


def _make_check(
    *,
    symbol: str = "US30_cash",
    candle_time: str = "2026-04-13T08:15:54.549732+00:00",
    period_month: str = "2026-04",
    period_half: str = "H1-2026",
    decision: str = "CANDIDATE",
    framework: str = "ob_retest",
    record_source: str = "trade_records",
    classifications: List[PriceClassification] = None,
) -> EvaluationCheck:
    return EvaluationCheck(
        record_source=record_source,
        symbol=symbol,
        candle_time_utc=candle_time,
        period_month=period_month,
        period_half=period_half,
        decision=decision,
        framework=framework,
        realized_r=None,
        classifications=classifications or [],
    )


# ════════════════════════════════════════════════════════════════════════════
# Section 1 — filter_to_us30
# ════════════════════════════════════════════════════════════════════════════


def test_filter_to_us30_keeps_only_us30():
    """Only US30_cash rows survive the filter."""
    checks = [
        _make_check(symbol="US30_cash"),
        _make_check(symbol="XAUUSD"),
        _make_check(symbol="USDJPY"),
        _make_check(symbol="GBPJPY"),
        _make_check(symbol="US30_cash", candle_time="2026-04-14T08:00:00+00:00"),
        _make_check(symbol="GBPUSD"),
        _make_check(symbol="US30"),  # Note: NOT US30_cash exactly
    ]
    out = cli.filter_to_us30(checks)
    assert len(out) == 2, "expected exactly 2 US30_cash rows"
    assert all(c.symbol == "US30_cash" for c in out)


def test_filter_to_us30_empty_input():
    """Empty input yields empty output (no crash)."""
    assert cli.filter_to_us30([]) == []


# ════════════════════════════════════════════════════════════════════════════
# Section 2 — decompose_per_field math
# ════════════════════════════════════════════════════════════════════════════


def test_per_field_decomposition_math_basic():
    """Per-field counters and percentages match hand-computed values."""
    # Two checks. Check A: 2 accurate (entry, sl), 1 hallucinated (tp), 1 misattributed (sweep).
    # Check B: 1 accurate (entry), 1 hallucinated (tp), 1 hallucinated (sl), 1 hallucinated (ob_mid).
    check_a = _make_check(classifications=[
        _make_classification("entry_price", 100.0, "accurate"),
        _make_classification("stop_loss", 95.0, "accurate"),
        _make_classification("take_profit", 110.0, "hallucinated"),
        _make_classification("sweep_price", 102.0, "misattributed"),
    ])
    check_b = _make_check(classifications=[
        _make_classification("entry_price", 200.0, "accurate"),
        _make_classification("take_profit", 210.0, "hallucinated"),
        _make_classification("stop_loss", 195.0, "hallucinated"),
        _make_classification("ob_mid", 199.0, "hallucinated"),
    ])
    decomp = cli.decompose_per_field([check_a, check_b])

    by_field: Dict[str, cli.FieldDecomp] = {r.field: r for r in decomp}

    # entry_price: 2 accurate
    assert by_field["entry_price"].n == 2
    assert by_field["entry_price"].n_accurate == 2
    assert by_field["entry_price"].n_hallucinated == 0
    assert by_field["entry_price"].accurate_pct == 100.0
    assert by_field["entry_price"].hallucinated_pct == 0.0

    # stop_loss: 1 accurate, 1 hallucinated
    assert by_field["stop_loss"].n == 2
    assert by_field["stop_loss"].n_hallucinated == 1
    assert by_field["stop_loss"].hallucinated_pct == 50.0

    # take_profit: 2 hallucinated
    assert by_field["take_profit"].n == 2
    assert by_field["take_profit"].n_hallucinated == 2
    assert by_field["take_profit"].hallucinated_pct == 100.0

    # sweep_price: 1 misattributed
    assert by_field["sweep_price"].n == 1
    assert by_field["sweep_price"].n_misattributed == 1
    assert by_field["sweep_price"].misattributed_pct == 100.0

    # ob_mid: 1 hallucinated
    assert by_field["ob_mid"].n == 1
    assert by_field["ob_mid"].n_hallucinated == 1


def test_per_field_decomposition_contribution_pct():
    """contribution_pct sums to 100% across hallucinated fields."""
    # 4 hallucinated TP + 1 hallucinated SL + 0 hallucinated entry → 80%/20%/0%
    classifications = (
        [_make_classification("take_profit", v, "hallucinated") for v in [1.0, 2.0, 3.0, 4.0]]
        + [_make_classification("stop_loss", 5.0, "hallucinated")]
        + [_make_classification("entry_price", 6.0, "accurate")]
    )
    check = _make_check(classifications=classifications)
    decomp = cli.decompose_per_field([check])
    by_field = {r.field: r for r in decomp}

    # 5 total hallucinations → TP contributes 4/5 = 80%, SL 1/5 = 20%
    assert by_field["take_profit"].contribution_pct == pytest.approx(80.0)
    assert by_field["stop_loss"].contribution_pct == pytest.approx(20.0)
    # Sum of contributions across hallucinated fields == 100%
    total_contrib = sum(
        r.contribution_pct or 0
        for r in decomp
        if (r.contribution_pct or 0) > 0
    )
    assert total_contrib == pytest.approx(100.0)


def test_per_field_decomposition_skips_none_classifications():
    """Classifications with classification=None are excluded from counts."""
    classifications = [
        _make_classification("entry_price", 1.0, "accurate"),
        PriceClassification(
            role="some_role", value=2.0, source_field="x", classification=None
        ),
    ]
    check = _make_check(classifications=classifications)
    decomp = cli.decompose_per_field([check])
    fields = [r.field for r in decomp]
    # The classification=None row is skipped — 'some_role' should NOT appear at all
    assert "entry_price" in fields
    assert "some_role" not in fields


def test_per_field_decomposition_zero_hallucinations():
    """If all rows are accurate, contribution_pct is None (not divide-by-zero)."""
    check = _make_check(classifications=[
        _make_classification("entry_price", 1.0, "accurate"),
        _make_classification("stop_loss", 2.0, "accurate"),
    ])
    decomp = cli.decompose_per_field([check])
    for r in decomp:
        assert r.n_hallucinated == 0
        assert r.contribution_pct is None


# ════════════════════════════════════════════════════════════════════════════
# Section 3 — cohort decompositions (month / session / final-outcome)
# ════════════════════════════════════════════════════════════════════════════


def test_per_month_decomposition_buckets_by_period_month():
    """Multiple months produce separate cohort rows."""
    apr = _make_check(period_month="2026-04", classifications=[
        _make_classification("a", 1.0, "hallucinated"),
        _make_classification("b", 2.0, "accurate"),
    ])
    mar = _make_check(period_month="2026-03", classifications=[
        _make_classification("a", 1.0, "accurate"),
    ])
    decomp = cli.decompose_per_month([apr, mar])
    by_month = {r.cohort: r for r in decomp}
    assert "2026-04" in by_month
    assert "2026-03" in by_month
    assert by_month["2026-04"].n_evaluations == 1
    assert by_month["2026-04"].n_prices == 2
    assert by_month["2026-04"].n_hallucinated == 1
    assert by_month["2026-04"].hallucinated_pct == 50.0
    assert by_month["2026-03"].n_hallucinated == 0


def test_per_session_decomposition_uses_kill_zone_map():
    """Sessions are derived from the kill_zone_map keyed on (candle_time, source)."""
    london = _make_check(
        candle_time="2026-04-13T08:00:00+00:00",
        classifications=[_make_classification("a", 1.0, "hallucinated")],
    )
    ny = _make_check(
        candle_time="2026-04-13T13:00:00+00:00",
        classifications=[_make_classification("a", 1.0, "accurate")],
    )
    kz_map = {
        ("2026-04-13T08:00:00+00:00", "trade_records"): "london",
        ("2026-04-13T13:00:00+00:00", "trade_records"): "ny",
    }
    decomp = cli.decompose_per_session([london, ny], kz_map)
    by_sess = {r.cohort: r for r in decomp}
    assert by_sess["london"].n_hallucinated == 1
    assert by_sess["ny"].n_hallucinated == 0
    assert by_sess["ny"].n_accurate == 1


def test_per_session_decomposition_unknown_kill_zone():
    """Missing kill zone defaults to 'unknown' bucket (no crash)."""
    ck = _make_check(
        candle_time="2026-04-13T08:00:00+00:00",
        classifications=[_make_classification("a", 1.0, "hallucinated")],
    )
    decomp = cli.decompose_per_session([ck], per_check_kill_zone={})
    assert any(r.cohort == "unknown" for r in decomp)


def test_per_final_outcome_decomposition():
    """Final outcomes split into REJECTED_L2 / LIMIT_PLACED / etc."""
    ck1 = _make_check(
        candle_time="2026-04-13T08:00:00+00:00",
        classifications=[_make_classification("a", 1.0, "hallucinated")],
    )
    ck2 = _make_check(
        candle_time="2026-04-13T13:00:00+00:00",
        classifications=[_make_classification("a", 1.0, "accurate")],
    )
    fo_map = {
        ("2026-04-13T08:00:00+00:00", "trade_records"): "REJECTED_L2",
        ("2026-04-13T13:00:00+00:00", "trade_records"): "LIMIT_PLACED",
    }
    decomp = cli.decompose_per_final_outcome([ck1, ck2], fo_map)
    by_fo = {r.cohort: r for r in decomp}
    assert by_fo["REJECTED_L2"].n_hallucinated == 1
    assert by_fo["LIMIT_PLACED"].n_hallucinated == 0


# ════════════════════════════════════════════════════════════════════════════
# Section 4 — inspection block schema
# ════════════════════════════════════════════════════════════════════════════


def test_inspection_block_schema_complete():
    """An inspection block carries every documented field."""
    ck = _make_check(
        candle_time="2026-04-13T08:15:54+00:00",
        classifications=[
            _make_classification("entry_price", 100.0, "accurate",
                                 matched_mso_field="ob.high", matched_mso_value=100.0,
                                 delta_ticks=0.0),
            _make_classification("ob_mid", 50.0, "hallucinated"),
            _make_classification("sweep_price", 60.0, "misattributed",
                                 matched_mso_field="fvg.top", matched_mso_value=60.0,
                                 delta_ticks=0.0, note="cross-role match"),
        ],
    )
    record = {
        "metadata": {"kill_zone": "london"},
        "decision_pipeline": {"final_outcome": "REJECTED_L2"},
        "mso": {
            "timeframes": {
                "H1": {
                    "order_blocks": [
                        {"high": 100.5, "low": 99.5, "type": "bullish",
                         "time": "2026-04-12T20:00:00", "touch_count": 1},
                    ],
                    "fair_value_gaps": [
                        {"top": 60.0, "bottom": 59.0, "type": "bullish",
                         "time": "2026-04-12T19:00:00"},
                    ],
                    "swings": [
                        {"price": 99.0, "type": "low", "time": "2026-04-11T15:00:00"},
                    ],
                    "candles": [
                        {"open": 99.5, "high": 100.0, "low": 99.0, "close": 99.7,
                         "time": "2026-04-13T08:00:00"},
                    ],
                },
            },
            "session_levels": {"asian_high": 100.5, "pdh": 102.0},
        },
    }
    blk = cli.build_inspection_block(
        ck,
        record=record,
        kill_zone="london",
        final_outcome="REJECTED_L2",
    )

    # Top-level
    assert blk["candle_time_utc"] == "2026-04-13T08:15:54+00:00"
    assert blk["kill_zone"] == "london"
    assert blk["final_outcome"] == "REJECTED_L2"
    assert blk["framework"] == "ob_retest"
    assert blk["decision"] == "CANDIDATE"
    assert blk["n_classifications"] == 3
    assert blk["n_hallucinated"] == 1
    assert blk["n_misattributed"] == 1
    assert blk["hallucination_score"] == pytest.approx(1.5)  # 1 hall + 0.5 miss

    # ai_cited_prices schema
    assert len(blk["ai_cited_prices"]) == 3
    cp = blk["ai_cited_prices"][0]
    for required_field in (
        "role", "value", "source_field", "classification",
        "matched_mso_field", "matched_mso_value", "delta_ticks", "note",
    ):
        assert required_field in cp, f"missing key {required_field}"

    # mso_key_levels schema
    assert blk["mso_key_levels"]["mso_present"] is True
    tfs = blk["mso_key_levels"]["timeframes"]
    assert "H1" in tfs
    assert "order_blocks" in tfs["H1"]
    assert "fair_value_gaps" in tfs["H1"]
    assert "swings" in tfs["H1"]
    assert "last_candle" in tfs["H1"]
    assert tfs["H1"]["last_candle"]["close"] == 99.7
    assert blk["mso_key_levels"]["session_levels"]["asian_high"] == 100.5


def test_inspection_block_handles_missing_mso():
    """If record has no MSO, mso_key_levels.mso_present is False."""
    ck = _make_check()
    record = {"metadata": {"kill_zone": "ny"}}
    blk = cli.build_inspection_block(
        ck, record=record, kill_zone="ny", final_outcome="REJECTED_L2",
    )
    assert blk["mso_key_levels"]["mso_present"] is False


# ════════════════════════════════════════════════════════════════════════════
# Section 5 — Output emission (write_breakdown_json / report_md / rows_jsonl)
# ════════════════════════════════════════════════════════════════════════════


def _make_minimal_result() -> cli.F9Result:
    """A small but realistic F9Result for end-to-end emission tests."""
    by_field = [
        cli.FieldDecomp(field="take_profit", n=4, n_accurate=1, n_hallucinated=3),
        cli.FieldDecomp(field="entry_price", n=2, n_accurate=2),
    ]
    setattr(by_field[0], "_contribution", 100.0)
    setattr(by_field[1], "_contribution", 0.0)
    by_month = [cli.CohortDecomp(cohort="2026-04", n_evaluations=2, n_prices=6,
                                 n_accurate=3, n_hallucinated=3)]
    by_session = [cli.CohortDecomp(cohort="london", n_evaluations=2, n_prices=6,
                                   n_accurate=3, n_hallucinated=3)]
    by_outcome = [cli.CohortDecomp(cohort="REJECTED_L2", n_evaluations=2, n_prices=6,
                                   n_accurate=3, n_hallucinated=3)]
    return cli.F9Result(
        harness_version_b7="B7-v1",
        harness_version_f9="F9-v1",
        tolerance_ticks=5,
        n_us30_evaluations=2,
        n_us30_prices=6,
        overall_us30_hallucination_pct=50.0,
        by_field=by_field,
        by_month=by_month,
        by_session=by_session,
        by_final_outcome=by_outcome,
        sampled_inspections=[
            {
                "candle_time_utc": "2026-04-13T08:00:00+00:00",
                "kill_zone": "london",
                "final_outcome": "REJECTED_L2",
                "framework": "ob_retest",
                "decision": "CANDIDATE",
                "n_classifications": 3,
                "n_hallucinated": 2,
                "n_misattributed": 0,
                "hallucination_score": 2.0,
                "ai_cited_prices": [
                    {"role": "entry_price", "value": 100.0,
                     "source_field": "trade_parameters.entry_price",
                     "classification": "accurate",
                     "matched_mso_field": "ob.high", "matched_mso_value": 100.0,
                     "delta_ticks": 0.0, "note": None},
                ],
                "mso_key_levels": {"mso_present": False},
            }
        ],
        sample_size=1,
    )


def test_write_breakdown_json_round_trip(tmp_path: Path):
    """breakdown.json emits and round-trips to dict."""
    result = _make_minimal_result()
    out = tmp_path / "breakdown.json"
    cli.write_breakdown_json(result, out)

    assert out.exists()
    with open(out, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["harness_version_f9"] == "F9-v1"
    assert data["harness_version_b7"] == "B7-v1"
    assert data["overall_us30_hallucination_pct"] == 50.0
    assert data["by_field"][0]["field"] == "take_profit"
    assert data["by_field"][0]["contribution_pct"] == 100.0
    assert data["by_month"][0]["cohort"] == "2026-04"
    assert data["by_session"][0]["cohort"] == "london"
    assert data["by_final_outcome"][0]["cohort"] == "REJECTED_L2"
    assert data["sampled_inspections"][0]["candle_time_utc"] == "2026-04-13T08:00:00+00:00"


def test_write_report_md_contains_required_sections(tmp_path: Path):
    """report.md has the verdict-block sections required by the brief."""
    result = _make_minimal_result()
    out = tmp_path / "report.md"
    cli.write_report_md(result, out)

    text = out.read_text(encoding="utf-8")
    assert "F9 — US30_cash Hallucination Deep-Dive" in text
    assert "## US30_cash hallucination decomposition" in text
    assert "### Per-field" in text
    assert "### Per-month" in text
    assert "### Per-session" in text
    assert "### Per-CAND-type" in text
    assert "Sampled top-hallucination CANDs" in text
    # Per-field row appears
    assert "take_profit" in text
    # Per-cohort rows appear
    assert "2026-04" in text
    assert "london" in text
    assert "REJECTED_L2" in text


def test_write_hallucination_rows_jsonl_only_emits_non_accurate(tmp_path: Path):
    """JSONL row file only carries hallucinated/misattributed rows."""
    checks = [
        _make_check(classifications=[
            _make_classification("entry_price", 100.0, "accurate"),
            _make_classification("take_profit", 110.0, "hallucinated"),
            _make_classification("sweep_price", 102.0, "misattributed"),
        ]),
    ]
    out = tmp_path / "hallucination_rows.jsonl"
    cli.write_hallucination_rows_jsonl(checks, out)

    rows = []
    with open(out, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    # Accurate row excluded; hallucinated + misattributed emitted
    assert len(rows) == 2
    classes = {r["classification"] for r in rows}
    assert classes == {"hallucinated", "misattributed"}
    # Schema sanity
    assert all("role" in r and "value" in r for r in rows)


# ════════════════════════════════════════════════════════════════════════════
# Section 6 — End-to-end CLI dry run
# ════════════════════════════════════════════════════════════════════════════


def test_cli_dry_run_writes_nothing(tmp_path: Path, capsys):
    """--dry-run exits 0 and writes no files."""
    rc = cli.main([
        "--output-dir", str(tmp_path / "should_not_exist"),
        "--dry-run",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[DRY RUN]" in out
    # Nothing was created
    assert not (tmp_path / "should_not_exist").exists()


def test_cli_help_does_not_crash(capsys):
    """--help exits 0 (argparse default) and prints usage."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "F9" in out
    assert "--output-dir" in out


# ════════════════════════════════════════════════════════════════════════════
# Section 7 — Helper functions
# ════════════════════════════════════════════════════════════════════════════


def test_kill_zone_from_record_metadata():
    """kill_zone is read from metadata.kill_zone for trade_records."""
    rec = {"metadata": {"kill_zone": "london"}}
    assert cli._kill_zone_from_record(rec) == "london"


def test_kill_zone_from_record_top_level():
    """kill_zone falls back to top-level for live_evaluations."""
    rec = {"kill_zone": "ny"}
    assert cli._kill_zone_from_record(rec) == "ny"


def test_kill_zone_from_record_missing():
    """Missing kill_zone returns 'unknown'."""
    assert cli._kill_zone_from_record({}) == "unknown"
    assert cli._kill_zone_from_record({"metadata": {}}) == "unknown"


def test_final_outcome_from_record_trade_records():
    """final_outcome comes from decision_pipeline.final_outcome."""
    rec = {"decision_pipeline": {"final_outcome": "LIMIT_PLACED"}}
    assert cli._final_outcome_from_record(rec) == "LIMIT_PLACED"


def test_final_outcome_from_record_live_eval():
    """live_evaluations rows get a synthetic 'live_eval_<DECISION>' label."""
    rec = {"decision": "NO_TRADE", "overall_reasoning": "no setup"}
    assert cli._final_outcome_from_record(rec) == "live_eval_NO_TRADE"


def test_hallucination_score_orders_correctly():
    """Higher hallucinated count sorts first in tie-breaking."""
    high = _make_check(classifications=[
        _make_classification("a", 1.0, "hallucinated"),
        _make_classification("b", 2.0, "hallucinated"),
        _make_classification("c", 3.0, "hallucinated"),
    ])
    medium = _make_check(classifications=[
        _make_classification("a", 1.0, "hallucinated"),
        _make_classification("b", 2.0, "misattributed"),
    ])
    low = _make_check(classifications=[
        _make_classification("a", 1.0, "accurate"),
    ])
    items = [low, medium, high]
    items.sort(key=lambda c: cli._hallucination_score(c), reverse=True)
    assert items[0] is high
    assert items[1] is medium
    assert items[2] is low

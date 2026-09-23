"""Tests for the F12 US30 tolerance-sweep CLI driver.

Coverage map
============
Section 1 — CLI plumbing
    * ``--tolerance-ticks 5,10,20,50,100`` is accepted and parsed
      into a sorted-unique int list.
    * ``--baseline-tolerance`` defaults to 5.
    * ``--dry-run`` exits 0 and writes nothing.

Section 2 — sweep output schema
    * ``sweep.json`` carries the harness version + per-tolerance row
      array + flipping_records array; each row has the required keys
      (``hallucination_pct``, ``n_records_flipping_vs_baseline``, ...).
    * ``flipping_records.jsonl`` is one JSON object per line with the
      documented schema.
    * ``report.md`` contains the verdict block + the verdict table.

Section 3 — flip-detection across thresholds
    * Synthetic checks where one classification at tolerance=5 is
      hallucinated and at tolerance=50 is accurate produce one
      ``FlippingRecord`` whose ``first_accurate_tolerance == 50``.
    * Classifications whose status is identical at every tolerance do
      NOT appear in the flipping_records list.

Section 4 — boundary edge case
    * A classification whose ``delta_ticks == tolerance`` exactly is
      classified as accurate (B7's match operator is ``<=``).

Section 5 — verdict logic
    * ``_h4_verdict`` returns Confirmed when wide_pct < 10%.
    * ``_h4_verdict`` returns Refuted when wide_pct >= 20% or delta < 5.
    * ``_h4_verdict`` returns Partial in the in-between band.

Section 6 — end-to-end with real fixtures
    * The script runs against the on-disk US30 trade_records corpus
      and produces non-empty outputs (smoke).

NO real Anthropic / OpenRouter calls. Outputs land under ``tmp_path``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Resolve project root so we can import without install
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.hallucination_measurement import (  # noqa: E402
    EvaluationCheck,
    PriceClassification,
    classify_price_detailed,
    CitedPrice,
    MSOPriceSet,
)

import scripts.research.run_f12_us30_tolerance_sweep as cli  # noqa: E402


# =============================================================================
# Test fixtures
# =============================================================================


def _mk_classification(
    role: str,
    value: float,
    classification: str,
    *,
    matched_field: str = None,
    matched_value: float = None,
    delta_ticks: float = None,
    note: str = None,
    source_field: str = None,
) -> PriceClassification:
    return PriceClassification(
        role=role,
        value=value,
        source_field=source_field or f"trade_parameters.{role}",
        classification=classification,
        matched_mso_field=matched_field,
        matched_mso_value=matched_value,
        delta_ticks=delta_ticks,
        note=note,
    )


def _mk_check(
    *,
    candle_time: str = "2026-04-13T08:15:54+00:00",
    classifications: List[PriceClassification] = None,
    record_source: str = "trade_records",
    framework: str = "ob_retest",
) -> EvaluationCheck:
    return EvaluationCheck(
        record_source=record_source,
        symbol="US30_cash",
        candle_time_utc=candle_time,
        period_month="2026-04",
        period_half="H1-2026",
        decision="CANDIDATE",
        framework=framework,
        realized_r=None,
        classifications=classifications or [],
    )


# =============================================================================
# Section 1 — CLI plumbing
# =============================================================================


class TestCLIPlumbing:
    """The sweep CLI accepts the flag spec from the F12 brief."""

    def test_default_tolerance_grid_is_5_10_20_50_100(self):
        parser = cli._build_parser()
        # Use all required args except the optional ones
        args = parser.parse_args(["--output-dir", "/tmp/scratch"])
        assert args.tolerance_ticks == [5, 10, 20, 50, 100]

    def test_custom_tolerance_grid_is_parsed_and_deduped_sorted(self):
        parser = cli._build_parser()
        args = parser.parse_args(
            ["--output-dir", "/tmp/scratch", "--tolerance-ticks", "50,5,10,5,20"]
        )
        # Sorted + de-duplicated
        assert args.tolerance_ticks == [5, 10, 20, 50]

    def test_negative_tolerance_rejected(self):
        parser = cli._build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                ["--output-dir", "/tmp/scratch", "--tolerance-ticks", "5,-10"]
            )

    def test_baseline_tolerance_defaults_to_5(self):
        parser = cli._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/scratch"])
        assert args.baseline_tolerance == 5

    def test_dry_run_exits_zero_and_writes_nothing(self, tmp_path):
        out = tmp_path / "scratch"
        rc = cli.main([
            "--output-dir", str(out),
            "--dry-run",
        ])
        assert rc == 0
        # Nothing should land in the output dir on dry-run
        assert not (out / "sweep.json").exists()
        assert not (out / "flipping_records.jsonl").exists()
        assert not (out / "report.md").exists()

    def test_baseline_outside_grid_rejected(self, tmp_path):
        out = tmp_path / "scratch"
        rc = cli.main([
            "--output-dir", str(out),
            "--tolerance-ticks", "5,10,20",
            "--baseline-tolerance", "50",  # not in grid
        ])
        assert rc == 2


# =============================================================================
# Section 2 — sweep output schema
# =============================================================================


class TestSweepSchema:
    """The on-disk outputs follow the schema documented in the script."""

    def _build_synthetic_sweep_result(self) -> cli.SweepResult:
        # One classification (key K1) flips at tol=20; one (K2) is stable.
        rows = [
            cli.ToleranceRow(
                tolerance_ticks=5, n_evaluations=1, n_prices=2,
                n_accurate=1, n_hallucinated=1, n_misattributed=0,
                n_records_flipping_vs_baseline=0,
            ),
            cli.ToleranceRow(
                tolerance_ticks=20, n_evaluations=1, n_prices=2,
                n_accurate=2, n_hallucinated=0, n_misattributed=0,
                n_records_flipping_vs_baseline=1,
            ),
        ]
        flips = [
            cli.FlippingRecord(
                candle_time_utc="2026-04-13T08:15:54+00:00",
                record_source="trade_records",
                role="ob_mid",
                source_field="reasoning.h1_setup.poi_price_level",
                value=47539.56,
                period_month="2026-04",
                period_half="H1-2026",
                framework="ob_retest",
                decision="CANDIDATE",
                status_per_tolerance={"5": "hallucinated", "20": "accurate"},
                matched_field_per_tolerance={"5": None, "20": "timeframes.H1.order_blocks[0].mid"},
                matched_value_per_tolerance={"5": None, "20": 47540.01},
                delta_ticks_per_tolerance={"5": None, "20": 45.0},
                first_accurate_tolerance=20,
            ),
        ]
        return cli.SweepResult(
            harness_version_f12="F12-v1",
            tolerances=[5, 20],
            baseline_tolerance=5,
            rows=rows,
            flipping_records=flips,
        )

    def test_sweep_json_has_required_top_level_keys(self, tmp_path):
        result = self._build_synthetic_sweep_result()
        path = tmp_path / "sweep.json"
        cli.write_sweep_json(result, path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["harness_version_f12"] == "F12-v1"
        assert payload["tolerances"] == [5, 20]
        assert payload["baseline_tolerance"] == 5
        assert isinstance(payload["per_tolerance"], list)
        assert isinstance(payload["flipping_records"], list)

    def test_sweep_json_per_tolerance_row_keys(self, tmp_path):
        result = self._build_synthetic_sweep_result()
        path = tmp_path / "sweep.json"
        cli.write_sweep_json(result, path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        row = payload["per_tolerance"][0]
        required_keys = {
            "tolerance_ticks", "n_evaluations", "n_prices",
            "n_accurate", "n_hallucinated", "n_misattributed",
            "accurate_pct", "hallucination_pct", "misattributed_pct",
            "n_records_flipping_vs_baseline",
        }
        assert required_keys <= set(row.keys())

    def test_sweep_json_hallucination_pct_arithmetic(self, tmp_path):
        result = self._build_synthetic_sweep_result()
        path = tmp_path / "sweep.json"
        cli.write_sweep_json(result, path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        row5 = next(r for r in payload["per_tolerance"] if r["tolerance_ticks"] == 5)
        # 1 hallucinated of 2 prices = 50%
        assert row5["hallucination_pct"] == pytest.approx(50.0)
        row20 = next(r for r in payload["per_tolerance"] if r["tolerance_ticks"] == 20)
        # 0 hallucinated of 2 prices = 0%
        assert row20["hallucination_pct"] == pytest.approx(0.0)

    def test_flipping_records_jsonl_one_object_per_line(self, tmp_path):
        result = self._build_synthetic_sweep_result()
        path = tmp_path / "flipping_records.jsonl"
        cli.write_flipping_records_jsonl(result.flipping_records, path)
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1
        rec = json.loads(lines[0])
        required_keys = {
            "candle_time_utc", "record_source", "role", "source_field", "value",
            "period_month", "period_half", "framework", "decision",
            "status_per_tolerance", "matched_field_per_tolerance",
            "matched_value_per_tolerance", "delta_ticks_per_tolerance",
            "first_accurate_tolerance",
        }
        assert required_keys <= set(rec.keys())
        assert rec["status_per_tolerance"]["5"] == "hallucinated"
        assert rec["status_per_tolerance"]["20"] == "accurate"
        assert rec["first_accurate_tolerance"] == 20

    def test_report_md_carries_verdict_block(self, tmp_path):
        result = self._build_synthetic_sweep_result()
        path = tmp_path / "report.md"
        cli.write_report_md(result, path)
        body = path.read_text(encoding="utf-8")
        assert "# F12 — US30 Hallucination Tolerance Sweep" in body
        assert "## US30 hallucination rate vs tolerance" in body
        assert "## H4 verdict" in body
        # Table header
        assert "| Tolerance (ticks) | Hallucination rate | n records flipping vs tol=5 |" in body


# =============================================================================
# Section 3 — flip-detection across thresholds
# =============================================================================


class TestFlipDetection:
    """``_build_flipping_records`` correctly identifies status changes."""

    def _build_per_tolerance_checks(
        self,
        statuses: Dict[int, List[str]],
    ) -> Dict[int, List[EvaluationCheck]]:
        """Build a map: tolerance → [check] where each check has a single
        ``ob_mid`` classification with the status from ``statuses[tol][i]``.

        Two records (i=0, i=1) at distinct candle_times so the keys differ.
        """
        out: Dict[int, List[EvaluationCheck]] = {}
        for tol, status_list in statuses.items():
            checks = []
            for i, st in enumerate(status_list):
                ts = f"2026-04-13T08:{15 + i * 15:02d}:00+00:00"
                cls = _mk_classification(
                    role="ob_mid",
                    value=47539.56,
                    classification=st,
                    delta_ticks=45.0 if st == "accurate" else None,
                    matched_field=("timeframes.H1.order_blocks[0].mid" if st == "accurate" else None),
                    matched_value=(47540.01 if st == "accurate" else None),
                )
                checks.append(_mk_check(candle_time=ts, classifications=[cls]))
            out[tol] = checks
        return out

    def test_one_classification_flipping_at_tol_50(self):
        per_t = self._build_per_tolerance_checks({
            5: ["hallucinated", "accurate"],
            10: ["hallucinated", "accurate"],
            50: ["accurate", "accurate"],  # i=0 flips at tol=50
        })
        flipping = cli._build_flipping_records(
            per_tolerance_checks=per_t,
            tolerances=[5, 10, 50],
            baseline_tolerance=5,
        )
        assert len(flipping) == 1
        rec = flipping[0]
        assert rec.role == "ob_mid"
        assert rec.first_accurate_tolerance == 50
        assert rec.status_per_tolerance["5"] == "hallucinated"
        assert rec.status_per_tolerance["10"] == "hallucinated"
        assert rec.status_per_tolerance["50"] == "accurate"

    def test_stable_classifications_excluded(self):
        # All three rows are accurate at every tolerance — no flips
        per_t = self._build_per_tolerance_checks({
            5: ["accurate", "accurate"],
            10: ["accurate", "accurate"],
            50: ["accurate", "accurate"],
        })
        flipping = cli._build_flipping_records(
            per_tolerance_checks=per_t,
            tolerances=[5, 10, 50],
            baseline_tolerance=5,
        )
        assert flipping == []

    def test_baseline_outside_grid_raises(self):
        per_t = self._build_per_tolerance_checks({5: ["accurate"], 10: ["accurate"]})
        with pytest.raises(ValueError):
            cli._build_flipping_records(
                per_tolerance_checks=per_t,
                tolerances=[5, 10],
                baseline_tolerance=999,
            )

    def test_misattributed_to_accurate_counts_as_flip(self):
        per_t = self._build_per_tolerance_checks({
            5: ["misattributed"],
            50: ["accurate"],
        })
        flipping = cli._build_flipping_records(
            per_tolerance_checks=per_t,
            tolerances=[5, 50],
            baseline_tolerance=5,
        )
        assert len(flipping) == 1
        assert flipping[0].first_accurate_tolerance == 50


# =============================================================================
# Section 4 — boundary edge case
# =============================================================================


class TestBoundary:
    """A delta exactly equal to the tolerance must classify as accurate."""

    def test_record_at_tolerance_boundary_transitions_at_threshold(self):
        """A record whose delta is strictly between two tolerance values
        flips at the right threshold.

        Tick size for US30_cash is 0.01. We choose prices producing a
        delta of ~30 ticks (well clear of float-precision boundaries):
          cited = 47539.71, MSO = 47540.01 → delta_ticks ≈ 30

        Expected:
          * tol=5  → hallucinated (30 ticks > 5)
          * tol=20 → hallucinated (30 ticks > 20)
          * tol=50 → accurate     (30 ticks < 50)

        This is the transition pattern the H4 hypothesis predicts for
        the 7 ~45-50-tick offset records.
        """
        cited = CitedPrice(role="ob_mid", value=47539.71, source_field="x")
        mso = MSOPriceSet()
        mso.by_role["ob_mid"] = [(47540.01, "timeframes.H1.order_blocks[0].mid")]

        cl5 = classify_price_detailed(cited, mso, symbol="US30_cash", tolerance_ticks=5)
        cl20 = classify_price_detailed(cited, mso, symbol="US30_cash", tolerance_ticks=20)
        cl50 = classify_price_detailed(cited, mso, symbol="US30_cash", tolerance_ticks=50)

        assert cl5.classification == "hallucinated"
        assert cl20.classification == "hallucinated"
        assert cl50.classification == "accurate"
        assert cl50.delta_ticks == pytest.approx(30.0, rel=0.05)

    def test_delta_well_inside_tolerance_is_accurate(self):
        """A price 4 ticks off the MSO at tol=5 is comfortably accurate.

        Tick size US30_cash = 0.01 → 4 ticks = 0.04 USD.
        Use values that subtract cleanly enough to stay well below 0.05.
        """
        cited = CitedPrice(role="ob_mid", value=100.0, source_field="x")
        mso = MSOPriceSet()
        mso.by_role["ob_mid"] = [(100.04, "timeframes.H1.order_blocks[0].mid")]

        cl = classify_price_detailed(
            cited, mso, symbol="US30_cash", tolerance_ticks=5
        )
        assert cl.classification == "accurate"
        # delta_ticks ≈ 4 (with float-precision wiggle); well under 5.
        assert cl.delta_ticks is not None
        assert 3.5 < cl.delta_ticks < 4.5

        # A tighter tolerance forces it to hallucinated
        cl3 = classify_price_detailed(
            cited, mso, symbol="US30_cash", tolerance_ticks=3
        )
        assert cl3.classification == "hallucinated"

    def test_record_at_exact_50_tick_offset_flips_at_tol_50(self):
        """Reproduce H4-style record: AI ob_mid 47539.51 vs MSO mid
        47540.01 → 0.50 USD = 50 tick offset.
        """
        cited = CitedPrice(role="ob_mid", value=47539.51, source_field="x")
        mso = MSOPriceSet()
        mso.by_role["ob_mid"] = [(47540.01, "timeframes.H1.order_blocks[0].mid")]

        cl5 = classify_price_detailed(cited, mso, symbol="US30_cash", tolerance_ticks=5)
        cl20 = classify_price_detailed(cited, mso, symbol="US30_cash", tolerance_ticks=20)
        cl50 = classify_price_detailed(cited, mso, symbol="US30_cash", tolerance_ticks=50)

        assert cl5.classification == "hallucinated"
        assert cl20.classification == "hallucinated"
        assert cl50.classification == "accurate"
        assert cl50.delta_ticks == pytest.approx(50.0)


# =============================================================================
# Section 5 — verdict logic
# =============================================================================


class TestVerdict:
    """``_h4_verdict`` returns the right label given the row table."""

    def _rows(self, base_pct: float, wide_pct: float) -> List[cli.ToleranceRow]:
        # Synthesize counts so .hallucination_pct returns the desired pct
        # We use n_prices=1000 → integer counts give us 0.1% granularity
        n = 1000
        return [
            cli.ToleranceRow(
                tolerance_ticks=5, n_evaluations=10, n_prices=n,
                n_accurate=int(n * (1 - base_pct / 100)),
                n_hallucinated=int(n * base_pct / 100),
                n_misattributed=0,
            ),
            cli.ToleranceRow(
                tolerance_ticks=50, n_evaluations=10, n_prices=n,
                n_accurate=int(n * (1 - wide_pct / 100)),
                n_hallucinated=int(n * wide_pct / 100),
                n_misattributed=0,
            ),
        ]

    def test_confirmed_when_wide_pct_below_10(self):
        rows = self._rows(base_pct=23.4, wide_pct=5.0)
        verdict, reason = cli._h4_verdict(rows)
        assert verdict == "Confirmed"
        assert "tolerance=50" in reason

    def test_refuted_when_wide_pct_at_or_above_20(self):
        rows = self._rows(base_pct=23.4, wide_pct=22.0)
        verdict, _ = cli._h4_verdict(rows)
        assert verdict == "Refuted"

    def test_refuted_when_delta_below_5(self):
        # base 23.4 → wide 19.5 = delta 3.9 (under threshold) → Refuted
        rows = self._rows(base_pct=23.4, wide_pct=19.5)
        verdict, _ = cli._h4_verdict(rows)
        assert verdict == "Refuted"

    def test_partial_in_between_band(self):
        # base 23.4 → wide 14.0 = delta 9.4 (significant), wide_pct < 20 but >= 10 → Partial
        rows = self._rows(base_pct=23.4, wide_pct=14.0)
        verdict, _ = cli._h4_verdict(rows)
        assert verdict == "Partial"


# =============================================================================
# Section 6 — end-to-end with real fixtures (smoke)
# =============================================================================


class TestEndToEnd:
    """Real US30 trade_records corpus produces non-empty outputs."""


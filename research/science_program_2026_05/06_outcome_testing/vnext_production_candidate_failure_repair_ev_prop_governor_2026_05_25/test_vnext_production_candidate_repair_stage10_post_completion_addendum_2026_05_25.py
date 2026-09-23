#!/usr/bin/env python3
"""Focused tests for Stage10 post-completion hardening helpers."""

from __future__ import annotations

import unittest

import build_vnext_production_candidate_repair_stage10_post_completion_addendum_2026_05_25 as stage10


class Stage10HelperTests(unittest.TestCase):
    def test_gross_metrics_reports_required_values(self) -> None:
        rows = [
            {"simulated_r_scoring_only": 1.5},
            {"simulated_r_scoring_only": -1.0},
            {"simulated_r_scoring_only": 0.25},
            {"simulated_r_scoring_only": None},
        ]
        metrics = stage10.gross_metrics(rows)
        self.assertEqual(metrics["performance_rows"], 3)
        self.assertEqual(metrics["non_performance_rows"], 1)
        self.assertAlmostEqual(metrics["total_proxy_r"], 0.75)
        self.assertAlmostEqual(metrics["expectancy_r"], 0.25)
        self.assertAlmostEqual(metrics["profit_factor"], 1.75)
        self.assertEqual(metrics["wins"], 2)
        self.assertEqual(metrics["losses"], 1)

    def test_context_recovery_detection_uses_stage07_evidence(self) -> None:
        self.assertTrue(
            stage10.is_context_recovery_row(
                {"_stage07": {"stage05_recovered_into_stream": True}}
            )
        )
        self.assertTrue(
            stage10.is_context_recovery_row(
                {"_stage07": {"stage07_ai_policy_action": "CALL_AI_CONSTRAINED_VALIDATOR"}}
            )
        )
        self.assertFalse(
            stage10.is_context_recovery_row(
                {"_stage07": {"stage07_ai_policy_action": "CALL_AI_NARROWED_ROUTE"}}
            )
        )

    def test_required_branches_are_explicit(self) -> None:
        self.assertEqual(
            set(stage10.REQUIRED_BRANCHES),
            {
                "AI_ACCEPTS_ALL_ELIGIBLE",
                "AI_REJECTS_ALL_CONTEXT_RECOVERY",
                "AI_ACCEPTS_ONLY_HIGH_QUALITY_PARTITIONS",
                "AI_ACCEPTANCE_PRECISION_BANDS",
                "MALFORMED_REPAIRED_THEN_SCHEMA_VALIDATED",
                "MALFORMED_DEMOTED_TO_NO_TRADE",
                "NO_PAID_DIAGNOSTIC_ZERO_OUTPUT",
            },
        )

    def test_precision_band_thresholds(self) -> None:
        self.assertEqual(
            stage10.precision_band(
                {
                    "performance_rows": 25,
                    "expectancy_r": 0.16,
                    "profit_factor": 1.31,
                    "win_rate": 0.51,
                }
            ),
            "VERY_HIGH",
        )
        self.assertEqual(
            stage10.precision_band(
                {
                    "performance_rows": 25,
                    "expectancy_r": -0.05,
                    "profit_factor": 0.9,
                    "win_rate": 0.40,
                }
            ),
            "NEGATIVE",
        )
        self.assertEqual(
            stage10.precision_band(
                {
                    "performance_rows": 10,
                    "expectancy_r": 1.0,
                    "profit_factor": 9.0,
                    "win_rate": 0.9,
                }
            ),
            "INSUFFICIENT_N",
        )

    def test_branch_metric_contains_required_fields(self) -> None:
        stage08_summary = {
            "ai_call_counts": {
                "saved_by_best_prop_block_or_defer": 2,
            },
            "policy_metrics": {},
        }
        eligible = [
            {
                "candidate_id": "a",
                "simulated_r_scoring_only": 1.0,
                "risk_pct": 1.0,
                "as_of_utc": "2026-01-01T00:00:00Z",
                "symbol": "XAUUSD",
                "session": "london",
                "side": "LONG",
                "framework": "ob_retest",
                "source_mode": "OHLC_M1_CSV",
                "month": "2026-01",
            },
            {
                "candidate_id": "b",
                "simulated_r_scoring_only": -1.0,
                "risk_pct": 1.0,
                "as_of_utc": "2026-01-02T00:00:00Z",
                "symbol": "XAUUSD",
                "session": "london",
                "side": "LONG",
                "framework": "ob_retest",
                "source_mode": "OHLC_M1_CSV",
                "month": "2026-01",
            },
        ]
        metric = stage10.build_branch_metric(
            "TEST_BRANCH",
            [eligible[0]],
            eligible,
            stage08_summary,
        )
        for field in stage10.METRIC_FIELDS:
            self.assertIn(field, metric)
        self.assertEqual(metric["selected_rows"], 1)
        self.assertEqual(metric["missed_winners"], 0)
        self.assertEqual(metric["avoided_losers"], 1)
        self.assertEqual(metric["accepted_losers"], 0)


if __name__ == "__main__":
    unittest.main()

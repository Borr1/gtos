========================================================================
VISION A/B TEST COMPARISON — Oct 2025
Generated: 2026-04-01 03:02
========================================================================

JSON-only batch: msgbatch_01VCZZM7cCZhW9Nb9MybySZq
  Trades: 5
Vision batch: msgbatch_01WgP6eewwdQd8UgVemLH4cN
  Trades: 6

## Overall Comparison

  JSON-only: 5 trades, 5W/0L, WR 100.0%, Total +5.29R, Exp +1.058R
    Confidence: [(80, 4), (85, 1)], std=2.2
  JSON+Vision: 6 trades, 4W/2L, WR 66.7%, Total +0.42R, Exp +0.070R
    Confidence: [(80, 5), (85, 1)], std=2.0

## Trade-by-Trade Diff

  Shared trades (both took): 5
  JSON-only trades (vision skipped): 0
  Vision-only trades (JSON skipped): 1
  NEW:  2025-10-07 ny — Vision produced WIN +0.13R

## Shared Trade Outcomes

    2025-10-03      ny: JSON +0.32R → Vision +0.32R (+0.00R)
  ▼ 2025-10-09  london: JSON +0.81R → Vision -1.00R (-1.81R)
  ▼ 2025-10-09      ny: JSON +0.24R → Vision -1.00R (-1.24R)
    2025-10-20      ny: JSON +1.23R → Vision +1.26R (+0.03R)
  ▼ 2025-10-24      ny: JSON +2.69R → Vision +0.71R (-1.98R)

## Confidence Score Comparison

  JSON-only: [(80, 4), (85, 1)], unique=2, std=2.2
    → Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80
    → Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80
    → Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80
  JSON+Vision: [(80, 5), (85, 1)], unique=2, std=2.0
    → Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80
    → Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80
    → Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80

## Verdict

  WR change: 100.0% → 66.7% (-33.3%)
  Exp change: +1.058R → +0.070R (-0.988R)
  → DO NOT INCLUDE VISION: Improvement below threshold (WR +3.0% or Exp +0.03R)
  Note: This is based on a small sample (Oct 2025 only). A full-range test would be more conclusive.

To save: python3 scripts/vision_comparison.py > knowledge_base_backtest/analysis/vision_ab_test_report.md

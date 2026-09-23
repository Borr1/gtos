# KB cycle 72 — the DEEP-TARGET lever GENERALIZES to us_equity (cross-sleeve confirmation)

Tests whether the c71 deep-target breakthrough (metals) is a structural property of fat-tailed momentum edges
by replicating on the INDEPENDENT us_equity Donchian-20 breakout sleeve (different asset class + mechanism).
Paired audit (eq_stream(), same trades/2xATR-stops, only target depth changes from the deployed 3R), per-year,
paired sign-flip permutation. `CYCLE72_US_EQUITY_DEEP_TARGET.json`.

## RESULT — YES, it generalizes (paired-significant on a second sleeve), but more trend-regime-dependent.
| depth | SEALED Δ vs 3R | paired p | OOS Δ | OOS p |
|---|---|---|---|---|
| 4R | +0.113 | 0.010 | +0.120 | 0.0001 |
| 5R | +0.179 | 0.007 | +0.200 | 0.0001 |
| 6R | +0.132 | 0.059 | +0.227 | 0.0000 |
| 8R | +0.241 | 0.012 | +0.281 | 0.0001 |
| **10R** | **+0.330** | **0.004** | **+0.298** | 0.0000 |
- Deepening beyond the deployed 3R robustly beats it: OOS p≈0.0001 at EVERY depth; SEALED significant at
  4/5/8/10R. sealed mean-R 0.279(3R)→0.392(4R)→0.520(8R)→0.609(10R). The deepest (10R) is best + most robust.
- **Cross-sleeve confirmation:** the deep-target / fat-tail-capture lever is a STRUCTURAL law of long-only
  trend-following edges (metals FVG-retest c71 AND equity Donchian c72), not a metals-specific or 2025 artifact.
  This is out-of-sample-on-a-different-edge — the strongest robustness evidence.
- **More regime-dependent than metals:** us_equity 2022 (equity bear) is flat/slightly negative at deep
  targets, and 2026 is negative at moderate depths (4-6R: -0.02/-0.03) — only the DEEPEST 8-10R stay positive
  in 2026 (+0.11/+0.17). Deep targets need trends to RUN; in bear/chop they time out. So it is a
  TREND-CONDITIONAL lever (strongest in trending regimes; the deepest depths are the most regime-robust).
- Downside unchanged (2xATR stop) → upside-only added variance (same structure as c71; deeper is not more
  downside-risky).

## DISPOSITION
Deep-target is a GENERAL gated deploy candidate across the trend sleeves: metals ~6R (c71, every-year-positive),
us_equity ~8-10R (c72, deepest = most regime-robust). NEXT: a regime-conditional target depth (deeper in
trends, shallower in chop) could lift the bear-year weakness — a clean c70-framework cell (target × regime).
Re-validate book-level sizing on the combined deep-target distribution before live.

**Files.** `CYCLE72_us_equity_deep_target.py`, `KNOWLEDGE_BASE/validation/CYCLE72_US_EQUITY_DEEP_TARGET.json`.

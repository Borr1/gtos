# ADR-005 A1 backtest — pre-registration

**Registered at:** 2026-04-25 (worktree `research/a1-adr005-backtest-validation`)
**Committed before:** any data was aggregated or inspected.

## Pre-registered discrimination criteria (frozen before looking at data)

These thresholds were chosen BEFORE running `analyze.py` against the backtest
slice logs. Any post-hoc edit that tightens/loosens them should be detectable
via the script-hash header in `ANALYSIS.md`.

### Touch axis
The AI DISCRIMINATES on H1 opposing-OB touch_count IFF:
1. `P(CAND | h1_opp_ob_touch == 0) >= 1.5 * P(CAND | h1_opp_ob_touch >= 2)`
2. Bonferroni-adjusted p < 0.05 (multiple-comparison factor k = 3)
3. n >= 30 per arm (touch=0 arm AND touch>=2 arm)

### FVG axis
The AI DISCRIMINATES on total unfilled FVG count (H1 + M15) IFF:
1. `P(CAND | fvg_total >= 3) >= 1.3 * P(CAND | fvg_total == 0)`
2. Bonferroni-adjusted p < 0.05 (multiple-comparison factor k = 4)
3. n >= 30 per arm

## Why these thresholds

### Ratios (1.5× and 1.3×)
- Touch: Phase 1 Track A walk-derived evidence shows touch=0 primary-positive
  rate 31.7% vs touch>=2 of 2.8%, a ~11× ratio. The AI doesn't need to
  reproduce that gap — even half-strength discrimination (1.5×) would materially
  reduce exposure to the low-edge touch>=2 stratum. 1.5× is the lowest ratio
  at which a soft prompt nudge would still be net-negative expected-R/mo
  (per ADR-005 hard-gate calculation extrapolated to "half effect size").
- FVG: same logic, less extreme permutation importance — 1.3× is the smallest
  ratio at which an FVG-density preference meaningfully changes CAND pool
  composition.

### Bonferroni factors (k=3, k=4)
- Touch: we test one primary comparison (touch=0 vs touch>=2) plus implicit
  secondary comparisons across three FVG strata (0, 1-2, >=3) — conservative
  k=3 guards against the temptation to cherry-pick an FVG stratum post-hoc.
- FVG: similarly k=4 accounts for four touch strata.
- This is deliberately conservative; a more aggressive Holm step-down would
  give us more power but also more flexibility to tune which compound test
  "wins." Bonferroni removes that lever.

### n >= 30 per arm
- Matches CLAUDE.md §Prohibited Behaviours rule #6: "Claiming significance at
  n < 20." We use 30 for a slightly stricter margin, consistent with Phase 1
  Track A convention.

## Decision branch

- Both axes discriminate → close ADR-005 as "no action needed" (AI already
  filters adequately).
- Neither axis discriminates → draft V4-A soft-bias prompt nudge and save
  as draft for CEO review. Do NOT apply to production.
- Partial (only one axis) → scope V4-A to the non-discriminating axis only.

## Analysis script identity

The only script permitted to compute the discrimination verdict is
`research/a1_adr005_backtest/analyze.py`. Its SHA256 is logged as the first
line of the generated `ANALYSIS.md`. Any subsequent edit produces a different
hash, making post-hoc tuning detectable by inspection.

Committed hash at registration time (before any run):
```
87801043e216e22fcc9075667c34ca660da703c4c23e69589d519923ba22e8cf
```

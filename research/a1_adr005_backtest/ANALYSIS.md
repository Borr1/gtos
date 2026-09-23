# ADR-005 A1 backtest — statistical analysis

**Question:** Does the GTOS production AI (Sonnet 4.6, effort=max) already
discriminate on H1 opposing-OB touch_count + H1/M15 FVG unfilled counts?

**Analysis script sha256:** `87801043e216e22fcc9075667c34ca660da703c4c23e69589d519923ba22e8cf`
**Slice dir:** `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-afdadba7818cfadd8\research\a1_adr005_backtest\slices`

## Pre-registered criteria (frozen before data look)

- **Touch:** P(CAND | touch=0) ≥ 1.5× P(CAND | touch≥2), Bonferroni p<0.05 (k=3), n≥30/arm.
- **FVG:**   P(CAND | fvg≥3) ≥ 1.3× P(CAND | fvg=0),   Bonferroni p<0.05 (k=4), n≥30/arm.
- All CIs are Wilson 95%. Two-proportion p-values are pooled z.

## Data

- Total rows logged across slices: **1142**
- Rows with AI decision (post-prescreen, not pre-AI-gate-skipped): **1138**

## Touch-count stratification (all AI-evaluated rows)

| Touch | n | CAND | P(CAND) | Wilson 95% CI |
|---:|---:|---:|---:|---|
| 0 | 0 | 0 | n/a | n/a |
| 1 | 398 | 344 | 86.4% | [82.7, 89.5] |
| 2 | 298 | 246 | 82.6% | [77.8, 86.4] |
| >=3 | 112 | 104 | 92.9% | [86.5, 96.3] |
| missing | 330 | 117 | 35.5% | [30.5, 40.8] |

## FVG total (H1+M15) stratification (all AI-evaluated rows)

| FVG total | n | CAND | P(CAND) | Wilson 95% CI |
|---:|---:|---:|---:|---|
| 0 | 0 | 0 | n/a | n/a |
| 1-2 | 0 | 0 | n/a | n/a |
| >=3 | 1138 | 811 | 71.3% | [68.6, 73.8] |
| missing | 0 | 0 | n/a | n/a |

## Touch × Direction matrix (CAND / total per cell)

| Touch | LONG | SHORT | UNCLEAR |
|---:|---|---|---|
| 0 | 0/0 | 0/0 | 0/0 |
| 1 | 341/394 | 3/4 | 0/0 |
| 2 | 246/298 | 0/0 | 0/0 |
| >=3 | 104/112 | 0/0 | 0/0 |
| missing | 117/306 | 0/24 | 0/0 |

## Touch discrimination verdict

- P(CAND | touch=0) = 0/0 = **0.00%**
  · Wilson 95% CI: [0.00, 0.00]
- P(CAND | touch≥2) = 350/410 = **85.37%**
  · Wilson 95% CI: [81.62, 88.46]
- Ratio (touch=0 / touch≥2) = **0.00×** (pre-reg threshold 1.5×)
- Two-proportion raw p = 1
- Bonferroni-adjusted p (k=3) = **1** (pre-reg threshold 0.05)

### Criteria check
- `ratio_ge_1.5`: FAIL
- `bonf_p_lt_0.05`: FAIL
- `n_touch0_ge_30`: FAIL
- `n_touch2plus_ge_30`: PASS

**Touch verdict: AI FAILS TO DISCRIMINATE on h1_opp_ob_touch.**

## FVG discrimination verdict

- P(CAND | fvg=0) = 0/0 = **0.00%**
  · Wilson 95% CI: [0.00, 0.00]
- P(CAND | fvg≥3) = 811/1138 = **71.27%**
  · Wilson 95% CI: [68.57, 73.82]
- Ratio (fvg≥3 / fvg=0) = **inf×** (pre-reg threshold 1.3×)
- Two-proportion raw p = 1
- Bonferroni-adjusted p (k=4) = **1** (pre-reg threshold 0.05)

### Criteria check
- `ratio_ge_1.3`: PASS
- `bonf_p_lt_0.05`: FAIL
- `n_fvg0_ge_30`: FAIL
- `n_fvg3plus_ge_30`: PASS

**FVG verdict: AI FAILS TO DISCRIMINATE on FVG total.**

## Decision branch

Neither touch nor FVG meets discrimination criteria → **draft V4-A soft-bias prompt nudge**.

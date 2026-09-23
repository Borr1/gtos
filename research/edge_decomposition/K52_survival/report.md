# K52 — Bonferroni-Survival Re-Test

_Generated: 2026-04-26T16:57:54.089235+00:00_

## Overview

Re-running the five Bonferroni-surviving baseline findings from CLAUDE.md against the current dataset, with Bonferroni correction applied at the canonical family size = **5**.

## Bonferroni-survival re-test (H1 batch → current 2026 data)

| Finding | H1 raw p | H1 corrected p | Current raw p | Current corrected p | Status |
|---|---|---|---|---|---|
| XAUUSD WR vs breakeven | 6.84e-09 | 3.42e-08 | 0.0050 | 0.0249 | SURVIVES |
| OB zone advantage +17pp vs 80% pullback | 0.0006 | 0.0030 | 0.0023 | 0.0116 | SURVIVES |
| US30 WR vs breakeven | 0.0017 | 0.0083 | — | — | NO_DATA |
| USDJPY WR vs breakeven | 3.92e-05 | 0.0002 | — | — | NO_DATA |
| FVG-in-impulse signal across 6 instruments | 0.0156 | 0.0780 | 0.8791 | 1.0000 | FAILS |

## Strategic verdict

Findings still surviving: **2 / 5**

Findings that failed: **FVG-in-impulse signal across 6 instruments**

Findings with insufficient data / NO_DATA: **US30 WR vs breakeven, USDJPY WR vs breakeven**

**Reasoning:**

1 of 5 baseline findings FAIL Bonferroni at the current dataset; 2 still survive. The failed findings' headline numbers in CLAUDE.md are stale and must be revised in the same commit. K54 should drop / regularise the corresponding features. Surviving findings remain the working baseline. Additionally, 2 finding(s) have insufficient data to draw a verdict — re-run K52 after fills accumulate.

## Per-finding detail

### XAUUSD WR vs breakeven — `xau_wr_vs_be` → SURVIVES

- **Baseline (CLAUDE.md):** raw p = `6.84e-09`, corrected p = `3.42e-08`
- **Current data:** raw p = `0.0050`, corrected p = `0.0249`
- **Current n:** 131
- **Summary:** `{"wins": 82, "n": 131, "wr": 0.6259542, "p_null": 0.5}`
- **Notes:** Corrected p = 0.02491 < α = 0.05 → survives.

### OB zone advantage +17pp vs 80% pullback — `ob_zone_advantage` → SURVIVES

- **Baseline (CLAUDE.md):** raw p = `0.0006`, corrected p = `0.0030`
- **Current data:** raw p = `0.0023`, corrected p = `0.0116`
- **Current n:** 309
- **Summary:** `{"wins_a": 122, "n_a": 173, "wr_a": 0.70520231, "wins_b": 73, "n_b": 136, "wr_b": 0.53676471, "delta_pp": 16.84376063}`
- **Notes:** Corrected p = 0.01159 < α = 0.05 → survives.

### US30 WR vs breakeven — `us30_wr_vs_be` → NO_DATA

- **Baseline (CLAUDE.md):** raw p = `0.0017`, corrected p = `0.0083`
- **Current data:** raw p = `—`, corrected p = `—`
- **Current n:** 0
- **Notes:** No current-data inputs available for this test (populate() returned None — typically means the realized-R data is missing for this instrument).

### USDJPY WR vs breakeven — `usdjpy_wr_vs_be` → NO_DATA

- **Baseline (CLAUDE.md):** raw p = `3.92e-05`, corrected p = `0.0002`
- **Current data:** raw p = `—`, corrected p = `—`
- **Current n:** 0
- **Notes:** No current-data inputs available for this test (populate() returned None — typically means the realized-R data is missing for this instrument).

### FVG-in-impulse signal across 6 instruments — `fvg_in_impulse` → FAILS

- **Baseline (CLAUDE.md):** raw p = `0.0156`, corrected p = `0.0780`
- **Current data:** raw p = `0.8791`, corrected p = `1.0000`
- **Current n:** 810
- **Summary:** `{"wins_a": 535, "n_a": 739, "wr_a": 0.72395129, "wins_b": 52, "n_b": 71, "wr_b": 0.73239437, "delta_pp": -0.84430807, "per_instrument": [{"symbol": "GBPUSD", "fvg_wr": 0.33333333, "non_wr": 0.0, "delta_pp": 33.33333333, "fvg_n": 3, "non_n": 2}, {"symbol": "XAUUSD", "fvg_wr": 0.72554348, "non_wr": 0.75362319, "delta_pp": -2.80797101, "fvg_n": 736, "non_n": 69}], "sign_test_n_positive": 1, "sign_test_n_total": 2, "sign_test_raw_p": 1.0}`
- **Notes:** Corrected p = 1 ≥ α = 0.05 → fails Bonferroni.

## Methodology

- **One-sample WR vs breakeven** (XAUUSD / US30 / USDJPY): exact two-sided binomial test against H0: WR = 50%. Wins = realised R > 0; BE counts as a loss (matches GTOS WR convention).
- **OB zone advantage**: pooled-variance two-proportion z-test comparing OB-sim WR (122/173) vs 80%-retrace baseline sim WR (73/136) on the Test A rerun population. Inputs are cached from `.context/03_analysis/test_a_rerun_real_bos_results.md` until a fresh re-run is committed.
- **FVG-in-impulse**: pooled two-proportion z-test on the union of per-instrument FVG-in-impulse OBs (continuation = win) vs non-FVG-impulse OBs from the per-record OB structural backtest (`knowledge_base_backtest/analysis/per_record_20260406/ob_per_record_*.csv`). A sign-test on the count of instruments with positive delta is reported in the summary alongside the pooled-z primary p.
- **Bonferroni correction**: corrected p = min(1, raw p × 5). Family size is fixed at the pre-registered 5; tests that cannot be run still consume their α/5 share. This is the conservative pre-registered choice.
- **Decision rule**: SURVIVES iff corrected p < α = 0.05 AND n ≥ n_min = 20. Below the n_min floor, status is INSUFFICIENT_N regardless of p.

## Data provenance

- Realized R (XAUUSD / GBPUSD): `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a9f16440b662c1bae\research\b_deep_audit_2026-04-19\phase1\_delta_scratch\trades_unified.csv`
- Live trade index (XAUUSD / GBPUSD): `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a9f16440b662c1bae\knowledge_base\index\_trade_index.json`
- OB per-record (FVG-in-impulse): `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a9f16440b662c1bae\knowledge_base_backtest\analysis\per_record_20260406`
- Test A rerun cache: `.context/03_analysis/test_a_rerun_real_bos_results.md (cached values)`

**Realized R per symbol:**
  - GBPUSD: n = 20
  - XAUUSD: n = 131

## Caveats

- **Test methodology vs CLAUDE.md baselines.** The published baseline p-values were computed by historical scripts that may have used different tests (Fisher exact / chi-square / one-sided). K52 standardises on exact two-sided binomial (one-sample) and pooled-variance two-proportion z (two-sample). Current vs baseline p differences may reflect either real decay OR test-methodology drift.
- **FVG-in-impulse is structural WR.** The current-data inputs use OB *continuation* outcomes (price moves in impulse direction post-retest), not realised R per fill. This matches the original CLAUDE.md +7-20pp signal layer (cross-instrument continuation), which is orthogonal to realised-R one-sample tests above. Do not conflate.
- **OB-zone advantage uses cached Test A inputs.** Until a fresh Test A rerun is committed against H2-2026 data, this test re-evaluates the *same population* under K52's standardised pooled-z test. A SURVIVES verdict here means the OB-zone signal still rejects H0 under the standardised test — it does NOT mean the Test A rerun has been re-executed. Re-run Test A to get a true current-data verdict.
- **Realized R limited to XAUUSD + GBPUSD.** Under the FTMO free-trial EA exclusion, no live fills exist on US30 / USDJPY / GBPJPY / XAGUSD / NAS100. Those tests will status NO_DATA / INSUFFICIENT_N until paid-challenge fills accumulate (≥30 per instrument). Treat the current verdict for those three as 'cannot tell yet'.
- **Family size 5 is hard-coded.** Any change to the family must go through ADR + amend CLAUDE.md Validated Numbers — adding tests post-hoc inflates α budget without honest pre-registration.

## K54 ML model implications

K54 (downstream feature-selection) uses K52 outcomes as a selection prior. A finding that fails survival is a feature that has lost discrimination on current data:

- **SURVIVES** → contribute the corresponding feature with full weight.
- **FAILS** → drop or aggressively regularise the feature. The signal that minted the feature has lost discrimination.
- **INSUFFICIENT_N / NO_DATA** → hold in reserve. Re-run K52 quarterly; promote on re-survival.

K54 should down-weight features tied to: FVG-in-impulse signal across 6 instruments.

K54 should hold (not actively use, not delete) features tied to: US30 WR vs breakeven, USDJPY WR vs breakeven. Re-evaluate after live-fill accumulation.

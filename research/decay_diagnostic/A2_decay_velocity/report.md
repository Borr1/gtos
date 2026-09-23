# A2 — Per-Instrument Rolling-Window Decay Velocity

_Generated: 2026-04-26T09:13:20.131316+00:00_

## Methodology

Per-instrument rolling **50-trade non-overlapping windows** of WR + Exp R, computed on realised-R per filled trade. Slope = OLS regression of WR over window-index, scaled to per-30-days via mean wall-clock window duration. Bonferroni-correct across **N=1** decay-slope tests (one per instrument with ≥3 windows). Verdict thresholds: ``DECAYING`` requires n ≥ 20 AND p_corrected < 0.05.

Data sources:
- Trade records dir: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a75798e15949c2777\knowledge_base\trade_records`
- Aux index: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a75798e15949c2777\knowledge_base\index\_trade_index.json`

## Strategic verdict

| Instrument | n | n_win | H1 WR | H2 WR | slope pp/mo | p (raw) | p (Bonferroni) | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 0 | 0 | — | — | — | — | — | INSUFFICIENT_N |
| GBPUSD | 24 | 0 | 66.7% | 66.7% | — | — | — | INCONCLUSIVE |
| NAS100 | 0 | 0 | — | — | — | — | — | INSUFFICIENT_N |
| US30_cash | 0 | 0 | — | — | — | — | — | INSUFFICIENT_N |
| USDJPY | 0 | 0 | — | — | — | — | — | INSUFFICIENT_N |
| XAGUSD | 0 | 0 | — | — | — | — | — | INSUFFICIENT_N |
| XAUUSD | 105 | 2 | 67.3% | 56.6% | -0.9 | — | — | STABLE |

**Decay concentration:** `UNIFORM`

**Reasoning:**

STABLE=XAUUSD; INCONCLUSIVE=GBPUSD; INSUFFICIENT_N=US30_cash,USDJPY,GBPJPY,XAGUSD,NAS100 Insufficient sample (n < 20): US30_cash, USDJPY, GBPJPY, XAGUSD, NAS100. Cannot draw a verdict; reflects the FTMO-free-trial EA exclusion blocking live fills (see `research/a3_trade_record_instrumentation/README.md`).

## Per-instrument detail

### GBPJPY

- Filled trades: **0** (threshold n ≥ 20). No realised-R data on disk meets the minimum sample. Verdict: `INSUFFICIENT_N`.

### GBPUSD

- Filled trades: **24**, full windows: **0**.
- H1 WR 66.7% → H2 WR 66.7%, slope — pp/mo, p_raw=—, p_corrected=—. Trend not significant after Bonferroni; cannot reject null.

### NAS100

- Filled trades: **0** (threshold n ≥ 20). No realised-R data on disk meets the minimum sample. Verdict: `INSUFFICIENT_N`.

### US30_cash

- Filled trades: **0** (threshold n ≥ 20). No realised-R data on disk meets the minimum sample. Verdict: `INSUFFICIENT_N`.

### USDJPY

- Filled trades: **0** (threshold n ≥ 20). No realised-R data on disk meets the minimum sample. Verdict: `INSUFFICIENT_N`.

### XAGUSD

- Filled trades: **0** (threshold n ≥ 20). No realised-R data on disk meets the minimum sample. Verdict: `INSUFFICIENT_N`.

### XAUUSD

- Filled trades: **105**, full windows: **2**. H1 WR 67.3% → H2 WR 56.6%, slope -0.9 pp/mo. Absolute slope < 1pp/mo → no meaningful trend.

## Caveats

- **Walk-level vs realised-R discipline.** All slopes here are computed on actual realised R per filled trade. Walk-level / structural-proxy decay indicators (see `research/instrument_expansion_2026-04-25/02_decay_analysis.py`) are NOT the same metric and have been shown to reverse against realised-R outcomes in prior research (`feedback_walk_level_evidence_not_predictive`).
- **Filled-trade availability.** The live ``trade_records/`` pipeline only populates ``exit.realized_R`` after a real broker fill. Under the FTMO free-trial EA exclusion, no live trades have filled yet (see ADR-A3 / `research/a3_trade_record_instrumentation/README.md`). Until paid-challenge fills accumulate, instruments with `INSUFFICIENT_N` verdicts are reflecting the data gap, not real-world stability.
- **Non-overlapping windows.** Each window is independent (step == window) to keep the slope-regression p-value calibrated. A 50-trade window over 150 trades therefore yields 3 points — barely enough for a regression. Add more fills before expanding to overlapping/sliding windows.
- **Bonferroni denominator.** N = number of instruments with ≥ 3 full windows (i.e. instruments where a slope p-value could be computed). Instruments with INSUFFICIENT_N do not consume α budget.

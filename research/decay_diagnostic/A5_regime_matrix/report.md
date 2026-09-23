# A5 — Regime-Stratified WR Matrix

**Total CANDs (with realized R)**: 335
**UNTAGGED**: 52 (15.5%)
**Realized-R-missing skipped**: 43
**Result files scanned**: 88
**Structure log**: `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\structure_detector_divergences.jsonl`
**H4 rows indexed**: 3575 (skipped no-symbol: 0)

---

## Per-instrument x regime table

Cells: `WR (n) [ExpR] CI95` — ⚠ flag indicates n < 10.

| Instrument | bearish | bullish | transitional | UNTAGGED | Total |
|---|---|---|---|---|---|
| EURUSD | 25.0% (n=4) [-0.417R] [4.6%-69.9%] ⚠ | 0.0% (n=5) [-1.000R] [0.0%-43.4%] ⚠ | 0.0% (n=1) [-1.000R] [0.0%-79.3%] ⚠ | 50.0% (n=2) [+0.250R] [9.5%-90.5%] ⚠ | 12 |
| GER40 | 85.7% (n=7) [+1.143R] [48.7%-97.4%] ⚠ | 26.7% (n=15) [-0.333R] [10.9%-52.0%] | 61.5% (n=13) [+0.541R] [35.5%-82.3%] | 50.0% (n=6) [+0.250R] [18.8%-81.2%] ⚠ | 41 |
| NAS100 | 12.5% (n=8) [-0.688R] [2.2%-47.1%] ⚠ | 60.0% (n=5) [+0.500R] [23.1%-88.2%] ⚠ | 100.0% (n=6) [+1.500R] [61.0%-100.0%] ⚠ | 100.0% (n=5) [+1.500R] [56.6%-100.0%] ⚠ | 24 |
| UK100 | — | 40.0% (n=15) [+0.000R] [19.8%-64.3%] | 60.0% (n=5) [+0.500R] [23.1%-88.2%] ⚠ | 50.0% (n=6) [+0.250R] [18.8%-81.2%] ⚠ | 26 |
| USDJPY | — | 63.4% (n=41) [+0.585R] [48.1%-76.4%] | 38.9% (n=18) [-0.028R] [20.3%-61.4%] | 50.0% (n=20) [+0.250R] [29.9%-70.1%] | 79 |
| XAGUSD | 85.7% (n=7) [+1.143R] [48.7%-97.4%] ⚠ | 78.3% (n=23) [+0.905R] [58.1%-90.3%] | 55.6% (n=9) [+0.388R] [26.7%-81.1%] ⚠ | 57.1% (n=7) [+0.429R] [25.0%-84.2%] ⚠ | 46 |
| XAUUSD | 84.6% (n=13) [+1.115R] [57.8%-95.7%] | 38.6% (n=70) [-0.034R] [28.0%-50.3%] | 38.9% (n=18) [-0.028R] [20.3%-61.4%] | 33.3% (n=6) [-0.167R] [9.7%-70.0%] ⚠ | 107 |

## Per-regime aggregate (avg WR across instruments, n>=10 only)

| Regime | Avg WR | Total n | Cells contributing |
|---|---|---|---|
| bearish | 84.6% | 39 | 1 |
| bullish | 49.4% | 174 | 5 |
| transitional | 46.4% | 70 | 3 |
| UNTAGGED | 50.0% | 52 | 1 |

## Per-instrument coverage (regimes with n>=10)

- **EURUSD**: 0/4 regimes have n>=10 (-)
- **GER40**: 2/4 regimes have n>=10 (bullish, transitional)
- **NAS100**: 0/4 regimes have n>=10 (-)
- **UK100**: 1/3 regimes have n>=10 (bullish)
- **USDJPY**: 3/3 regimes have n>=10 (UNTAGGED, bullish, transitional)
- **XAGUSD**: 1/4 regimes have n>=10 (bullish)
- **XAUUSD**: 3/4 regimes have n>=10 (bearish, bullish, transitional)

---

## Strategic verdict

- Highest-WR regime (across instruments): **bearish** (avg WR 84.6%)
- Lowest-WR regime: **transitional** (avg WR 46.4%)
- WR delta between best and worst regime: **38.2pp**
- Diagnosis: **REGIME_DEPENDENT**
- Reasoning: WR delta of 38.2pp between 'bearish' (84.6%) and 'transitional' (46.4%) exceeds the 15pp threshold. Regime-aware sizing (H38) is the warranted follow-up.


# Session Handoff — Deep Dive Analysis — 2026-04-06

## What Was Done

Comprehensive statistical deep dive across 8 analysis phases on the gold-agent trading system.

### Data Analyzed
- 129 trades (105 XAUUSD, 24 GBPUSD) from trade index
- 7,496 displacement records (XAUUSD)
- 820 per-record OB entries
- 1,661 per-record FVG entries
- 47,142 M15 candles (XAUUSD)

### Key Results

#### Edge Confirmed
- Win rate: 62.0%, Mean R: +0.278, PF: 2.17
- Kelly half: 9.91% (use 0.75-1.0% for prop firm)
- P(prop firm pass at 1% risk): 81.4%
- No autocorrelation (runs test p=1.0)

#### 7 Confirmed Predictors (Bonferroni-surviving)
1. `align` (alignment score) — strongest predictor
2. `creates_fvg` — +11pp continuation
3. `at_ob` — at order block flag
4. `ct` (counter-trend) — -5pp penalty
5. `fvg_pct` — FVG percentage
6. `direction` — bullish vs bearish
7. `origin_revisited` — semi-outcome, flagged as tautological

#### New Finding: Impulse Candle Count
- r=-0.31, p=0.0 — fewer impulse candles = stronger OB
- First time this was tested in the research pipeline

#### Major NULL Findings
- H4 alignment: DEAD (p=0.76)
- D1 alignment: DEAD (confirmed p=0.93)
- OTE zone: DEAD (p=0.61)
- All 10 "untested promising features": NULL
- BE stop: NET NEGATIVE at every trigger
- NY KZ extension: NOT supported (p=0.52)
- DOW × KZ: NOT significant (p=0.10)
- Market regime: NOT significant

#### FVG Fill Framework
- 80-100% fill depth: 71.4% continuation (confirmed)
- FVG adds 67% more trading dates
- Strong recommendation to implement

### Files Produced (all in `knowledge_base_backtest/analysis/deep_dive_20260406/`)

| File | Contents |
|------|----------|
| `trade_index_enriched.json` | 129 trades + entry times, direction, session data |
| `trade_displacement_linked.json` | 59 XAUUSD trades linked to displacement records |
| `monte_carlo_20260406.json` + `.md` | 10K sim Monte Carlo at 6 risk levels |
| `rolling_stability_20260406.json` | 20-trade rolling windows |
| `autocorrelation_20260406.json` | Lag analysis + runs test |
| `drawdown_analysis_20260406.json` + `.md` | Equity curve + drawdown analysis |
| `dow_kz_matrix_20260406.json` | 5×2 DOW×KZ matrix |
| `trade_timing_20260406.json` | Trade frequency analysis |
| `displacement_feature_screen_20260406.json` + `.md` | 95-field screen, 7 confirmed |
| `h16_h17_analysis_20260406.json` | Hour-by-hour displacement quality |
| `mfe_time_profile_20260406.json` + `.md` | 12-candle MFE/MAE walk + BE stop |
| `first_candle_momentum_20260406.json` | First M15 candle analysis |
| `feature_redundancy_20260406.json` + `.md` | Lasso attempt (failed) |
| `regime_analysis_20260406.json` + `.md` | Volatility/trend/range regimes |
| `phase6_per_record_20260406.json` | All Phase 6 results |
| `impulse_character_20260406.json` + `.md` | Impulse leg analysis |
| `framework_overlap_20260406.json` + `.md` | FVG/OB date overlap |
| `fvg_deep_dive_20260406.json` + `.md` | FVG fill depth analysis |
| `calendar_analysis_20260406.json` | Calendar (blocked) |
| `gbpusd_analysis_20260406.json` | GBPUSD (insufficient data) |
| `deep_dive_master_20260406.md` | Complete findings report |
| `deep_dive_pressure_test_20260406.md` + `.json` | All analyses pressure tested |
| `prompt_changes_ready_20260406.md` | 6 specific prompt changes |

### Prompt Changes Ready to Implement
1. **Remove OTE zone** — dead filter (p=0.61)
2. **Add impulse candle count** — sharp impulses (1-2 candles) are better
3. **Add FVG creation signal** — +11pp continuation boost
4. **Do NOT elevate H4** — dead (p=0.76)
5. **FVG Fill depth filter** — 80-100% preferred
6. **Counter-trend penalty** — -5pp for CT setups

### What's Still Blocked
1. **Calendar event analysis**: Need MQL5 export covering 2024-2026 from Windows
2. **GBPUSD displacement DB**: Doesn't exist yet
3. **GBPUSD M15 candles**: Only 700 rows (2026 only) — need full history from Windows
4. **Lasso feature redundancy**: Need better trade-displacement linking
5. **WR decay investigation**: Why did WR drop from 67% to 59% in second half?

### Updated System Confidence Levels
| Component | Confidence | Evidence |
|-----------|-----------|----------|
| OB Retest framework | HIGH | 72.8% continuation (per-record), 7 confirmed features |
| FVG Fill framework | MEDIUM-HIGH | 71.4% at 80-100% fill, not yet live-tested |
| H4/D1 alignment | DEAD | Both p > 0.75 on 7496 records |
| OTE zone | DEAD | p=0.61 |
| impulse sharpness | HIGH | r=-0.31, p=0.0, n=820 |
| Overall edge | HIGH | 62% WR, PF 2.17, 129 trades over 2+ years |
| Prop firm viability | MEDIUM | 81% pass at 1% risk, but 66% chance of hitting 5% DD |

### Next Session Priorities
1. Implement prompt changes (OTE removal, impulse candle count, FVG creation signal)
2. Run batch test with updated prompt on validation dates
3. Design FVG Fill framework implementation
4. Re-download GBPUSD candles from Windows
5. Export MQL5 economic calendar from Windows
6. Investigate second-half WR decay

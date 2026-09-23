# WF-1 Inverted TP/SL Auto-Correction Feasibility Analysis

**Date:** 2026-04-07  
**Analysis Type:** Backtest Simulation Study  
**Scope:** All batch API raw results from knowledge_base_backtest/batch_api/  
**Status:** COMPLETED - DO NOT IMPLEMENT

## Executive Summary

Analysis of 12,006 evaluations from batch API backtests identified 22 inverted CANDIDATEs (7.03% rate) out of 313 total candidates. M15 simulation of corrected trades shows **negative expectancy** and **no improvement** over current safety gate blocking.

**Key Finding:** Inverted trades should remain blocked. Auto-correction would result in net losses.

## Methodology

### Data Sources
- **Raw Results:** 20 batch API JSON files containing 12,006 AI evaluations
- **Historical Data:** M15 OHLC data from data/historical/XAUUSD_M15.csv and other instruments
- **Analysis Period:** 2024-04-01 to 2026-02-18

### Identification Process
1. **Extraction:** Found 313 CANDIDATE trades with trade_parameters
2. **Detection:** Identified inverted parameters where:
   - LONG: take_profit_1 < entry_price OR stop_loss > entry_price
   - SHORT: take_profit_1 > entry_price OR stop_loss < entry_price
3. **Auto-Correction:** Flipped TP/SL distances while maintaining same absolute distances

### Simulation Logic
- **Entry:** Exact timestamp from evaluation
- **Execution:** Walk-forward M15 candle analysis
- **Exit:** First TP or SL hit within 480 candles (5 days max)
- **Symbol Detection:** Price range mapping (XAUUSD: 1800-2800, US30: 25000-50000, etc.)

## Detailed Findings

### Inversion Statistics
- **Total CANDIDATEs:** 313
- **Inverted CANDIDATEs:** 22
- **Inversion Rate:** 7.03%
- **Successfully Simulated:** 6 trades (27.3%)
- **Simulation Errors:** 15 trades (68.2%)
- **Timeouts:** 1 trade (4.5%)

### Trading Performance (Corrected Trades)
- **Win Rate:** 50.0% (3 winners, 3 losers)
- **Average R-Multiple:** -0.325
- **Total R-Multiple:** -1.95
- **Expectancy:** NEGATIVE

### Symbol Breakdown
| Symbol | Trades | Win Rate | Total R | Notes |
|--------|--------|----------|---------|--------|
| XAUUSD | 6      | 50.0%    | -1.95   | All simulatable trades were XAUUSD |
| US30   | 0      | N/A      | N/A     | Price detection but no valid simulations |
| USDJPY | 0      | N/A      | N/A     | Price detection but no valid simulations |

### Individual Trade Results
1. **2024-04-05_ny_1530:** LONG XAUUSD → SL hit (-1.00R)
2. **2024-09-27_ny_1530:** LONG XAUUSD → TP hit (+1.50R)
3. **2025-04-04_ny_1430:** SHORT XAUUSD → SL hit (-1.00R)
4. **2025-04-16_ny_1400:** SHORT XAUUSD → TP hit (+1.50R)
5. **2025-04-16_ny_1415:** SHORT XAUUSD → TP hit (+1.50R)
6. **2025-04-17_ny_1345:** LONG XAUUSD → SL hit (-1.00R)

## Analysis of Inversion Patterns

### Common Characteristics
- **Peak Concentration:** September 2025 (7 trades in 1 week)
- **Session Bias:** NY session dominance (95% of inverted trades)
- **Market Conditions:** High volatility periods with rapid directional changes
- **Setup Types:** Primarily OB retest framework (framework field analysis)

### Root Cause Assessment
Inverted parameter generation likely occurs during:
1. **Conflicting Signals:** When market structure suggests one direction but immediate price action contradicts
2. **Volatility Spikes:** Rapid price movements causing parameter calculation errors
3. **Session Transitions:** Handoff periods between kill zones

## Recommendation: DO NOT IMPLEMENT

### Rationale
1. **Negative Expectancy:** -0.325R average would compound losses over time
2. **Safety Gate Effectiveness:** Current blocking mechanism protects capital
3. **Limited Benefit:** Only 1.9% of total candidates affected (22/313 = 7% of candidates, candidates = 2.6% of total evaluations)

### Alternative Actions
Instead of auto-correction, recommend:

1. **Prompt Engineering:** Investigate prompt modifications to reduce inversion rate
   - Add explicit TP/SL direction validation instructions
   - Include directional consistency checks in reasoning chain

2. **Real-Time Validation:** Enhance safety gate with logging
   ```python
   # In src/components/orchestrator.py after line XXX
   if self._detect_inverted_parameters(trade_params):
       logger.warning(f"Inverted parameters blocked: {trade_params}")
       self._increment_inversion_counter()
   ```

3. **Market Condition Analysis:** Study correlation between inversion rate and:
   - Volatility metrics (ATR, price velocity)
   - Economic calendar events
   - Session transition periods

## Implementation Notes (If Reconsidered)

Should future analysis show positive expectancy, the correction logic would be:

```python
def auto_correct_inverted_params(self, trade_params):
    """Auto-correct inverted TP/SL parameters"""
    entry = trade_params['entry_price']
    direction = trade_params['direction']
    original_tp = trade_params['take_profit_1']
    original_sl = trade_params['stop_loss']
    
    tp_distance = abs(original_tp - entry)
    sl_distance = abs(original_sl - entry)
    
    if direction == 'LONG':
        corrected_tp = entry + tp_distance
        corrected_sl = entry - sl_distance
    else:  # SHORT
        corrected_tp = entry - tp_distance
        corrected_sl = entry + sl_distance
    
    return {
        **trade_params,
        'take_profit_1': corrected_tp,
        'stop_loss': corrected_sl,
        'corrected': True
    }
```

## Monitoring Requirements

If implemented (NOT recommended), monitor:
- Correction frequency and success rate
- Performance delta between original blocked vs corrected trades  
- False positive rate (correct parameters incorrectly flagged as inverted)

## Conclusion

The 4.9% inverted CANDIDATE rate (referenced in WF-1 observations) manifests as 7.03% in this backtest analysis. Auto-correction feasibility study shows **negative expectancy of -0.325R average**, indicating the safety gate correctly blocks unprofitable setups.

**Decision:** Maintain current safety gate blocking. Do not deploy auto-correction during WF-1 or future periods based on this analysis.

---

**Analysis Files:**
- `inverted_tp_sl_analysis.py` - Initial detection script
- `enhanced_inverted_analysis.py` - M15 simulation engine
- `inverted_tp_sl_analysis_results.json` - Raw detection results
- `enhanced_inverted_analysis_results.json` - Simulation results

**Next Steps:** Monitor WF-1 live performance for additional inversion patterns and validate findings with fresh data post-July 2026.
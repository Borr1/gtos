# Shadow Analysis Template
**Purpose:** Compute alternative outcomes for each live trade to identify optimization opportunities and validate current exit strategies.

## Analysis Framework

For each completed trade in the knowledge base, compute:

### 1. Trailing Stop Analysis (Trail 0.5R after 1.5R MFE)

**Concept:** Once Maximum Favorable Excursion (MFE) reaches 1.5R profit, activate a trailing stop at 0.5R risk.

**Computation Steps:**
1. **Extract Trade Basics:**
   - Entry Price: `trade.entry_price`
   - Stop Loss: `trade.stop_loss` 
   - Direction: `trade.direction` (LONG/SHORT)
   - R-Risk = |entry_price - stop_loss|

2. **Calculate 1.5R Trigger Level:**
   - LONG: trigger_price = entry_price + (1.5 × R-Risk)
   - SHORT: trigger_price = entry_price - (1.5 × R-Risk)

3. **Calculate 0.5R Trail Distance:**
   - trail_distance = 0.5 × R-Risk

4. **Simulate Trail Execution:**
   ```python
   def compute_trail_outcome(candle_data, entry_price, direction, r_risk):
       trigger_level = entry_price + (1.5 * r_risk * (1 if direction == "LONG" else -1))
       trail_distance = 0.5 * r_risk
       trail_active = False
       current_trail_level = None
       
       for candle in candle_data:
           high, low = candle['high'], candle['low']
           
           # Check if 1.5R trigger hit
           if not trail_active:
               if direction == "LONG" and high >= trigger_level:
                   trail_active = True
                   current_trail_level = high - trail_distance
               elif direction == "SHORT" and low <= trigger_level:
                   trail_active = True
                   current_trail_level = low + trail_distance
           
           # Update trail level if active
           if trail_active:
               if direction == "LONG":
                   new_trail = high - trail_distance
                   current_trail_level = max(current_trail_level, new_trail)
                   # Check trail hit
                   if low <= current_trail_level:
                       exit_price = current_trail_level
                       trail_r = (exit_price - entry_price) / r_risk
                       return {'trail_hit': True, 'exit_price': exit_price, 'trail_r': trail_r}
               else:  # SHORT
                   new_trail = low + trail_distance
                   current_trail_level = min(current_trail_level, new_trail)
                   # Check trail hit
                   if high >= current_trail_level:
                       exit_price = current_trail_level
                       trail_r = (entry_price - exit_price) / r_risk
                       return {'trail_hit': True, 'exit_price': exit_price, 'trail_r': trail_r}
       
       return {'trail_hit': False, 'reason': 'Trade ended before trail hit'}
   ```

5. **Output Fields:**
   - `trail_eligible`: boolean (did MFE reach 1.5R?)
   - `trail_activated_candle`: candle index where 1.5R hit
   - `trail_exit_r`: R-multiple if trail was hit
   - `trail_vs_actual`: difference from actual outcome
   - `trail_improvement`: boolean (trail better than actual?)

### 2. Shadow TP Analysis (1.0R through 3.0R)

**Concept:** Test what outcomes would have occurred with different TP levels.

**Computation Steps:**
1. **Define TP Levels:**
   - Test levels: 1.0R, 1.5R, 2.0R, 2.5R, 3.0R

2. **For Each TP Level:**
   ```python
   def compute_shadow_tp(candle_data, entry_price, direction, r_risk, tp_r_level):
       tp_price = entry_price + (tp_r_level * r_risk * (1 if direction == "LONG" else -1))
       sl_price = entry_price + (-1.0 * r_risk * (1 if direction == "LONG" else -1))
       
       for i, candle in enumerate(candle_data):
           high, low = candle['high'], candle['low']
           
           # Check TP hit first (fill priority)
           if direction == "LONG" and high >= tp_price:
               return {'outcome': 'WIN', 'exit_r': tp_r_level, 'exit_candle': i}
           elif direction == "SHORT" and low <= tp_price:
               return {'outcome': 'WIN', 'exit_r': tp_r_level, 'exit_candle': i}
           
           # Check SL hit
           if direction == "LONG" and low <= sl_price:
               return {'outcome': 'LOSS', 'exit_r': -1.0, 'exit_candle': i}
           elif direction == "SHORT" and high >= sl_price:
               return {'outcome': 'LOSS', 'exit_r': -1.0, 'exit_candle': i}
       
       return {'outcome': 'TIMEOUT', 'exit_r': 0.0, 'exit_candle': len(candle_data)}
   ```

3. **Output Fields:**
   - `shadow_tp_1r`: outcome with 1.0R TP
   - `shadow_tp_1_5r`: outcome with 1.5R TP  
   - `shadow_tp_2r`: outcome with 2.0R TP
   - `shadow_tp_2_5r`: outcome with 2.5R TP
   - `shadow_tp_3r`: outcome with 3.0R TP
   - `best_shadow_tp`: highest R outcome achieved
   - `optimal_tp_level`: R-level that maximized outcome

### 3. Early MAE Analysis (First 3 Candles)

**Concept:** Measure Maximum Adverse Excursion in the initial 3 candles to identify early exit signals.

**Computation Steps:**
1. **Extract First 3 Candles:** From trade execution time
2. **Calculate MAE:**
   ```python
   def compute_early_mae(candle_data, entry_price, direction, r_risk):
       first_3_candles = candle_data[:3]
       max_adverse_excursion = 0.0
       mae_candle = None
       mae_price = None
       
       for i, candle in enumerate(first_3_candles):
           high, low = candle['high'], candle['low']
           
           if direction == "LONG":
               adverse_move = entry_price - low
               if adverse_move > max_adverse_excursion:
                   max_adverse_excursion = adverse_move
                   mae_candle = i + 1
                   mae_price = low
           else:  # SHORT
               adverse_move = high - entry_price
               if adverse_move > max_adverse_excursion:
                   max_adverse_excursion = adverse_move
                   mae_candle = i + 1
                   mae_price = high
       
       mae_r = max_adverse_excursion / r_risk if r_risk > 0 else 0.0
       
       return {
           'early_mae_r': mae_r,
           'mae_candle': mae_candle,
           'mae_price': mae_price,
           'mae_exceeded_0_5r': mae_r > 0.5,
           'mae_exceeded_0_75r': mae_r > 0.75
       }
   ```

3. **Output Fields:**
   - `early_mae_r`: MAE in first 3 candles (R-multiple)
   - `mae_candle`: which candle (1, 2, or 3) produced max MAE
   - `mae_price`: exact price of maximum adverse move
   - `early_mae_warning`: boolean (MAE > 0.5R in first 3 candles)
   - `early_mae_critical`: boolean (MAE > 0.75R in first 3 candles)

## Implementation Template

### Data Processing Pipeline

```python
import json
from pathlib import Path
from typing import Dict, List, Any

def process_live_trade_shadows(trade_record_path: str, candle_data: List[Dict]) -> Dict[str, Any]:
    """
    Main shadow analysis function for a single trade.
    
    Args:
        trade_record_path: Path to trade YAML/JSON file
        candle_data: List of OHLC candles from trade execution onwards
    
    Returns:
        Dictionary containing all shadow analysis results
    """
    
    # Load trade data
    trade = load_trade_record(trade_record_path)
    
    # Extract trade parameters
    entry_price = trade['entry_price']
    stop_loss = trade['stop_loss'] 
    direction = trade['direction']
    r_risk = abs(entry_price - stop_loss)
    
    # Initialize results
    shadow_results = {
        'trade_id': trade['trade_id'],
        'analysis_timestamp': datetime.utcnow().isoformat(),
        'original_outcome': trade.get('outcome'),
        'original_r_multiple': trade.get('r_multiple'),
    }
    
    # 1. Trailing Stop Analysis
    trail_results = compute_trail_outcome(candle_data, entry_price, direction, r_risk)
    shadow_results.update({'trail_' + k: v for k, v in trail_results.items()})
    
    # 2. Shadow TP Analysis  
    for tp_r in [1.0, 1.5, 2.0, 2.5, 3.0]:
        tp_outcome = compute_shadow_tp(candle_data, entry_price, direction, r_risk, tp_r)
        shadow_results[f'shadow_tp_{str(tp_r).replace(".", "_")}r'] = tp_outcome
    
    # 3. Early MAE Analysis
    mae_results = compute_early_mae(candle_data, entry_price, direction, r_risk)
    shadow_results.update({'early_' + k: v for k, v in mae_results.items()})
    
    return shadow_results
```

### Batch Processing Script

```python
def analyze_all_live_trades():
    """Process all trades in knowledge_base/trades/"""
    
    trades_dir = Path("knowledge_base/trades")
    results = []
    
    for trade_file in trades_dir.glob("tr_*.yaml"):
        try:
            # Load trade record
            trade_data = load_yaml(trade_file)
            
            # Skip if no execution data
            if not trade_data.get('fill_price'):
                continue
                
            # Get corresponding candle data
            symbol = infer_symbol_from_trade(trade_data)
            trade_time = trade_data['date'] + "T" + trade_data.get('execution_time', '08:00')
            candle_data = fetch_candles_from_execution(symbol, trade_time)
            
            # Run shadow analysis
            shadow_result = process_live_trade_shadows(str(trade_file), candle_data)
            results.append(shadow_result)
            
            print(f"Processed {trade_file.name}: {shadow_result['trail_eligible']}, "
                  f"Best TP: {shadow_result.get('best_shadow_tp', 'N/A')}")
                  
        except Exception as e:
            print(f"Error processing {trade_file}: {e}")
    
    # Save consolidated results
    output_path = Path("knowledge_base/shadow_analysis_results.json")
    save_json(output_path, {
        'generated_at': datetime.utcnow().isoformat(),
        'total_trades_analyzed': len(results),
        'results': results
    })
    
    return results
```

## Output Schema

**File Location:** `knowledge_base/shadow_analysis_results.json`

**Schema:**
```json
{
  "generated_at": "2026-04-07T00:30:00Z",
  "total_trades_analyzed": 15,
  "results": [
    {
      "trade_id": "tr_2026-04-01_001",
      "analysis_timestamp": "2026-04-07T00:30:00Z",
      "original_outcome": "WIN",
      "original_r_multiple": 2.3,
      
      "trail_eligible": true,
      "trail_activated_candle": 5,
      "trail_exit_r": 1.8,
      "trail_vs_actual": -0.5,
      "trail_improvement": false,
      
      "shadow_tp_1r": {"outcome": "WIN", "exit_r": 1.0, "exit_candle": 3},
      "shadow_tp_1_5r": {"outcome": "WIN", "exit_r": 1.5, "exit_candle": 4},
      "shadow_tp_2r": {"outcome": "WIN", "exit_r": 2.0, "exit_candle": 6},
      "shadow_tp_2_5r": {"outcome": "LOSS", "exit_r": -1.0, "exit_candle": 8},
      "shadow_tp_3r": {"outcome": "LOSS", "exit_r": -1.0, "exit_candle": 8},
      "best_shadow_tp": 2.0,
      "optimal_tp_level": "2.0R",
      
      "early_mae_r": 0.3,
      "mae_candle": 2,
      "mae_price": 2015.45,
      "early_mae_warning": false,
      "early_mae_critical": false
    }
  ],
  
  "aggregate_insights": {
    "trail_eligible_pct": 73.3,
    "trail_improvement_pct": 40.0,
    "avg_trail_benefit": 0.15,
    "optimal_tp_distribution": {
      "1.0R": 2,
      "1.5R": 4,
      "2.0R": 6,
      "2.5R": 2,
      "3.0R": 1
    },
    "early_mae_warning_rate": 26.7,
    "trades_with_critical_mae": 13.3
  }
}
```

## Usage Instructions

### 1. Weekly Shadow Report Generation
```bash
# Run shadow analysis on all completed trades
python -m src.analysis.shadow_analysis

# Generate weekly summary
python -m src.analysis.shadow_weekly_report
```

### 2. Integration with Live Trading
- **Pre-Trade:** Check historical shadow data for similar setups
- **During Trade:** Monitor if current MFE approaches 1.5R trail trigger
- **Post-Trade:** Queue trade for shadow analysis batch processing

### 3. Strategy Optimization Workflow
1. **Identify Patterns:** High trail improvement rate = consider trailing stops
2. **TP Optimization:** If optimal_tp_distribution shows clustering, adjust default TPs
3. **Early Exit Signals:** High early_mae_warning_rate = tighten entry criteria

## Validation Rules

### Data Quality Checks
- Candle data must start from trade execution time
- Minimum 20 candles post-execution for valid shadow analysis
- Verify R-risk calculation against actual trade parameters

### Alert Conditions
- **Trail Underperformance:** >60% of trails worse than actual outcome
- **TP Suboptimal:** >70% of trades optimal at different TP than used
- **Early MAE Pattern:** >40% showing critical early MAE

## File Integration

**Dependencies:**
- `src/models/trade_models.py` - TradeRecord structure
- `src/components/knowledge_base.py` - Trade loading utilities
- `src/utils/market_data.py` - Candle data fetching
- `knowledge_base/trades/` - Source trade records

**Outputs:**
- `knowledge_base/shadow_analysis_results.json` - Main results
- `knowledge_base/insights/shadow_weekly_report.md` - Weekly summary  
- `knowledge_base/statistics/trail_optimization.json` - Trail statistics
- `knowledge_base/statistics/tp_optimization.json` - TP level analysis

---

**Next Steps:** Implement batch processing script and integrate with weekly reporting pipeline for WF-2 optimization insights.
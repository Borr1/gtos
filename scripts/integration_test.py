#!/usr/bin/env python3
"""Integration test: Pull real MT5 data -> compute MSO -> run pre-screen -> call Claude API.
Does NOT place any orders.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), override=True)

import yaml
import MetaTrader5 as mt5

if not mt5.initialize():
    print(f"MT5 init failed: {mt5.last_error()}")
    sys.exit(1)

with open('config/agent_config.yaml') as f:
    config = yaml.safe_load(f)

# Step 1: Data ingestion
print("Step 1: Data ingestion...")
from src.mt5.mt5_real import RealMT5
mt5_iface = RealMT5()
mt5_iface.connect()

from src.components.data_ingestion import ingest_live_data
try:
    raw_data = ingest_live_data(mt5_iface, config)
    print(f"  OK: Raw data keys: {list(raw_data.keys())}")
    print(f"  Candle timeframes: {list(raw_data.get('candles', {}).keys())}")
    sl = raw_data.get('session_levels', {})
    print(f"  Session levels: asian_high={sl.get('asian_high')}, pdh={sl.get('pdh')}")
except Exception as e:
    print(f"  FAIL: {e}")
    import traceback; traceback.print_exc()
    mt5.shutdown()
    sys.exit(1)

# Step 2: Market state
print("\nStep 2: Market state computation...")
from src.components.market_state import compute_market_state
try:
    mso = compute_market_state(raw_data, config)
    print(f"  OK: MSO type: {type(mso).__name__}")

    # Print key MSO fields
    if hasattr(mso, 'D1'):
        d1 = mso.D1
        d1_dir = d1.direction if hasattr(d1, 'direction') else 'unknown'
        print(f"  D1 bias: {d1_dir}")
    if hasattr(mso, 'H4'):
        h4 = mso.H4
        h4_dir = h4.direction if hasattr(h4, 'direction') else 'unknown'
        print(f"  H4 direction: {h4_dir}")
    if hasattr(mso, 'H1'):
        h1 = mso.H1
        h1_dir = h1.direction if hasattr(h1, 'direction') else 'unknown'
        print(f"  H1 direction: {h1_dir}")
except Exception as e:
    print(f"  FAIL: {e}")
    import traceback; traceback.print_exc()
    mt5.shutdown()
    sys.exit(1)

# Step 3: Pre-screen
print("\nStep 3: Pre-screen check...")
d1_direction = d1_dir if 'd1_dir' in dir() else "unknown"
h4_direction = h4_dir if 'h4_dir' in dir() else "unknown"

prescreen_pass = True
d1_clear = d1_direction in ("bullish", "bearish")
h4_clear = h4_direction in ("bullish", "bearish")

if not d1_clear and not h4_clear:
    print(f"  Pre-screen: FAIL — both D1 '{d1_direction}' and H4 '{h4_direction}' unclear (no directional consensus)")
    prescreen_pass = False
elif d1_clear and h4_clear and h4_direction != d1_direction:
    print(f"  Pre-screen: FAIL — H4 '{h4_direction}' conflicts with D1 '{d1_direction}'")
    prescreen_pass = False
else:
    bias_source = "D1" if d1_clear else "H4 (D1 unclear)"
    print(f"  Pre-screen: PASS — D1={d1_direction}, H4={h4_direction}, bias source={bias_source}")

# Step 4: Claude API call
if prescreen_pass:
    print("\nStep 4: Claude API call (this costs ~$0.02-0.05)...")
    try:
        from src.components.primary_analyzer import PrimaryAnalyzer
        from src.components.knowledge_base import KnowledgeBase
        kb = KnowledgeBase("knowledge_base/")

        pa = PrimaryAnalyzer(config, kb)

        async def run_analysis():
            return await pa.analyze(mso, kill_zone="london", session_memory="")

        result = asyncio.run(run_analysis())
        print(f"  OK: Decision: {result.decision}")
        if hasattr(result, 'reasoning') and result.reasoning:
            r = result.reasoning
            grade = r.setup_grade if hasattr(r, 'setup_grade') else 'N/A'
            print(f"  Grade: {grade}")
            overall = str(r.overall_reasoning if hasattr(r, 'overall_reasoning') else r)[:200]
            print(f"  Reasoning: {overall}...")

        if result.decision == "CANDIDATE":
            tp = result.trade_parameters
            if tp:
                sl_dist = abs(tp.entry_price - tp.stop_loss)
                tp1_dist = abs(tp.take_profit_1 - tp.entry_price) if tp.take_profit_1 else 0
                tp1_r = tp1_dist / sl_dist if sl_dist > 0 else 0
                print(f"  Entry: {tp.entry_price}, SL: {tp.stop_loss} (${sl_dist:.2f}), TP1: {tp.take_profit_1} ({tp1_r:.2f}R)")
                print(f"  Direction: {tp.direction}")
                if tp1_r < 2.0:
                    print(f"  WARNING: TP1 at {tp1_r:.2f}R — below 2.0R safety threshold!")
                if tp.entry_price > 0 and sl_dist / tp.entry_price > 0.025:
                    print(f"  WARNING: SL distance {sl_dist/tp.entry_price*100:.1f}% — exceeds 2.5% max!")
            else:
                print(f"  WARNING: CANDIDATE with null trade_parameters")
    except Exception as e:
        print(f"  FAIL: {e}")
        import traceback; traceback.print_exc()
else:
    print("\nStep 4: Skipped (pre-screen failed — no API cost)")
    print("  This is normal. The system won't call Claude on days with unclear D1 bias.")

mt5_iface.disconnect()
mt5.shutdown()
print("\nIntegration test complete.")

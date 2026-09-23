=== TRADE CAPTURE PRESSURE TEST ===
Date: 2026-04-04
Runner: knowledge_base_backtest/analysis/trade_capture_pressure_test_runner.py

Test 1  (Complete Executed Record):    PASS — 41 checks, file=28KB with full MSO+prompt
Test 2  (L2 Rejected Record):         PASS — 8 checks, rejected record fully captured
Test 3  (Gate Rejected Record):        PASS — 5 checks, gate rejection record complete
Test 4  (Prompt Capture Fidelity):     PASS — 10 checks, exact character match (system=12,423 chars, user=1,506 chars)
Test 5  (MSO Serialization):          PASS — 16 checks, all nested structures intact, float precision preserved
Test 6  (Cross-Instrument Context):    PASS — 4 checks, GBPUSD has CI, XAUUSD correctly empty
Test 7  (Pipeline Non-Interference):   PASS — 4 checks, avg write 6.8ms, failure returns None not exception
Test 8  (File Structure/Naming):       PASS — 9 checks, london/ny separate files, atomic writes clean
Test 9  (Exit Data Completeness):      PASS — 26 checks, R calculations correct for all exit types
Test 10 (Regression):                  PASS — 539 tests passing (509 existing + 30 trade capture)

=== CRITICAL FINDINGS ===

1. Prompt Capture Fidelity (Test 4): VERIFIED
   - System prompt: 12,423 characters, exact match with build_system_prompt() + static context
   - User message: 1,506 characters, exact match with build_user_message()
   - Contains: Internal Consistency Rules, EVALUATION SEQUENCE, Data Grounding Rules, session memory
   - Zero differences between captured and generated prompts

2. Pipeline Non-Interference (Test 7): VERIFIED
   - save_trade_record failure returns None (does not raise)
   - Average write latency: 6.8ms per record (well under 100ms target)
   - Disabled config creates record but orchestrator gates saving

3. Rejected Record Completeness (Tests 2-3): VERIFIED
   - L2 rejected: MSO, prompt, AI response all captured. blocked_by identifies failing check.
   - Gate rejected: L2 verification results preserved. Gate failure details captured.
   - execution=null, exit=null correctly for rejected trades.

4. R Calculations (Test 9): VERIFIED
   - TP1 exit (LONG): (3053.80 - 3042.50) / 7.50 = 1.51R (positive)
   - SL exit (LONG): (3035.00 - 3042.50) / 7.50 = -1.0R (negative)
   - BE exit (LONG): (3042.50 - 3042.50) / 7.50 = 0.0R (zero)
   - SHORT TP1: (3080.00 - 3065.00) / 10.00 = 1.5R (correct inversion)

5. MSO Size (Test 5): No concern
   - Full MSO with all timeframes: 8,847 bytes as JSON
   - Complete record with full MSO + prompt: 28,246 bytes
   - Well under 200KB threshold. No need for compression at this scale.

=== NO ISSUES FOUND ===

All 10 tests PASS. The trade capture pipeline is ready for live demo trading.

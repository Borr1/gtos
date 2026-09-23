# WF-1 Live Observations

## Observation 1: AI Inconsistent U1 Application (2026-04-06)

**Date:** Day 1 (Monday April 6)
**Instrument:** XAUUSD
**Impact:** Potentially blocked valid London setups

### What Happened
- D1 was transitional (legitimately unclear)
- H4 was making HH+HL from 01:00-09:00 UTC — textbook bullish
- H1 was bullish per local align score
- Local align: 3/4 bullish (D1=transitional, H4=bullish, H1=bullish, M15=bullish)

### AI Behavior
- 07:15 UTC: AI correctly said bias=bullish, h4_aligned=True (NO_TRADE: price not at POI)
- 07:30 UTC: AI correctly said bias=bullish, h4_aligned=True (NO_TRADE: price not at POI)
- 07:45 UTC: AI FLIPPED to bias=ranging, h4_aligned=False — stayed this way all day
- Same H4 data, same prompt, different conclusion

### U1 Rule (from prompt)
> "If Daily is unclear or ranging, use H4 and H1 directional consensus — at least two of D1/H4/H1 must agree on direction for a valid bias."

H4=bullish + H1=bullish = 2 of 3 agree. U1 should pass. AI blocked it.

### Actual H4 Structure (verified from MT5)
```
04-06 01:00 UTC  HH HL
04-06 05:00 UTC  HH HL
04-06 09:00 UTC  HH HL  ← London window, clearly bullish
04-06 13:00 UTC  LH LL  ← NY, structure broke (AI correct here)
```

### Backtest Cross-Reference
- 1,221 candles in batch backtest where AI said "ranging" but h4_aligned=True
- 35 of those still became CANDIDATEs (AI inconsistently applies fallthrough)
- 1,186 were blocked — unknown how many had valid setups

### Caveat
Even when U1 passed (07:15, 07:30), price wasn't at any H1 POI so trade wouldn't have triggered anyway. The big move (4690→4630) was a breakdown, not an OB retest. U1 misapplication may not have cost a trade THIS time.

### Weekly Review Action
- Count U1 blocks where H4+H1 agreed across all 5 days
- Check if any of those had genuine OB retest setups (POI + sweep + CHoCH)
- Determine if this is costing real trades or just blocking empty candles

---

## Observation 2: Cold Start — Session Memory Not Persisted (2026-04-07)

**Date:** Day 2 (Tuesday April 7)
**Impact:** AI starts each KZ with no memory of previous evaluations

### What Happens
- `session_memory` is in-memory only (`self.session_memory = []` on init)
- Every process restart = cold start, no context from earlier candles
- Within a KZ it builds up (last 6 evals), but between KZs or after restarts it's empty

### Why It Matters
- The U1 flip from yesterday (07:30 bullish → 07:45 ranging) might partly be LLM variance amplified by no memory anchor
- With memory, the AI would see "I called this bullish 15 min ago" and be more consistent
- Early KZ candles get worse analysis than later ones

### Data Available
- JSONL files have every evaluation with full fields
- Could reconstruct last 6 evals from JSONL on startup

### WF-2 Action
- Load last N evaluations from JSONL into session_memory on bootstrap
- Simple: read today's JSONL, parse last 6 entries, populate self.session_memory
- Does NOT change the prompt — just provides the same context the AI would have had if the process hadn't restarted

### Why Not Fix Now
- Changes what context the AI sees → could change trading decisions
- WF-1 needs clean data to compare against cold-start backtest
- Defer to WF-2 (July)

### Implementation Guide (for agent team)

**Objective:** On orchestrator bootstrap, pre-populate `self.session_memory` from today's JSONL so the AI has continuity across restarts and KZ transitions.

**Key files:**
- `src/components/orchestrator.py` — the orchestrator class
  - Line 164: `self.session_memory: list[dict] = []` — this is where memory initializes empty
  - Line 214: `_bootstrap()` — called once on startup, add warm-start here
  - Line 755-772: `_update_session_memory()` — shows the entry format: `{"time": "HH:MM UTC", "kill_zone": str, "decision": str, "summary": str}`
  - Line 774-791: `_compress_evaluation()` — formats analysis into summary string
  - Line 794-799: `_format_session_memory()` — formats memory into prompt text, uses `self.session_memory[-6:]`
  - Line 1544: `self.session_memory = []` — also cleared on shutdown, would need to NOT clear if persisting

**JSONL location:** `knowledge_base/live_evaluations/{SYMBOL}/{YYYY-MM-DD}.jsonl`
- One line per candle evaluation, JSON with keys: `candle_time`, `kill_zone`, `decision`, `no_trade_reason`, `setup_grade`, `confidence_score`, `framework`, `daily_bias_direction`, `h4_aligned`, `h1_poi_identified`, etc.
- See `knowledge_base/live_evaluations/USDJPY/2026-04-06.jsonl` for a full day example (30 entries)

**Implementation steps:**
1. In `_bootstrap()` after line 214, add a `_warm_start_session_memory()` call
2. That method should:
   - Find today's JSONL: `knowledge_base/live_evaluations/{self._symbol}/{today}.jsonl`
   - Read last 6 lines
   - For each, construct a session_memory entry matching the format in `_update_session_memory()`
   - The `summary` field should be reconstructed from JSONL fields: `f"NO_TRADE — {no_trade_reason}"` for NO_TRADE, or `f"CANDIDATE ({setup_grade}, conf={confidence_score}) — {direction} entry={entry_price}"` for CANDIDATE
   - Populate `self.session_memory`
3. Also consider: on KZ transition (not just restart), carry forward memory instead of starting fresh

**Format the memory entry must match (from line 758-763):**
```python
{
    "time": "HH:MM UTC",        # from candle_time field
    "kill_zone": "tokyo",        # from kill_zone field
    "decision": "NO_TRADE",      # from decision field
    "summary": "NO_TRADE — ..."  # reconstructed from _compress_evaluation logic
}
```

**Testing:**
- Unit test: mock a JSONL file, call `_warm_start_session_memory()`, verify `self.session_memory` has 6 entries
- Integration test: start orchestrator, verify `_format_session_memory()` returns non-empty string
- Verify the formatted memory matches what `_format_session_memory()` would produce from live evaluations

**Constraint:** Do NOT deploy during WF-1 (ends July 7, 2026). Research, implement, and test on a branch. Merge after WF-1 ends.

---

## Observation 3: start_all.bat Process Lifetime (2026-04-07)

**Date:** Day 2 (Tuesday April 7)
**Impact:** Scheduled task launched processes but they died when parent bat exited

### What Happened
- Windows Task Scheduler fired `start_all.bat` at 08:01 AM KL
- Processes bootstrapped, entered Tokyo KZ, passed canary check
- Then all 5 died — no error, no shutdown log, just vanished
- Cause: `start /min cmd /c` processes are children of the bat — when bat exits, Windows kills them

### Fix Applied
- Changed `start_all.bat` to use `wmic process call create` which spawns truly independent processes
- Not yet tested via Task Scheduler (will verify tomorrow morning)

### If wmic Fails Too
- Fallback: create a Python launcher script that uses `subprocess.Popen` with `CREATE_NEW_PROCESS_GROUP` flag
- Or: use `pythonw.exe` instead of `python.exe` for windowless operation

---

## Observation 4: AI Output Malformed TP on First CANDIDATE (2026-04-07)

**Date:** Day 2 (Tuesday April 7), Tokyo KZ 09:15 KL
**Instrument:** USDJPY
**Impact:** First live CANDIDATE was blocked by safety — no trade executed

### What Happened
- AI returned CANDIDATE: A+, confidence 85, LONG, ob_retest
- L2 verification passed all checks
- But AI set TP1=159.386 with entry=159.464 — TP below entry on a LONG
- Safety gate caught it: "TP1 BELOW ENTRY for LONG"
- Also: TP at 1.5R, below the 2.0R minimum
- Also: displacement ratio mismatch — AI said 10.30, MSO measured 1.99

### Trade Parameters (from AI)
```
Entry:    159.464
SL:       159.516  (ABOVE entry on a LONG — also wrong)
TP1:      159.386  (BELOW entry on a LONG — wrong)
Direction: LONG
RR:       1.5
```

Both SL and TP are inverted — looks like the AI confused LONG/SHORT when computing price levels.

### System Response
- Safety gate blocked execution (correct behavior)
- Trade record saved for analysis but no MT5 position opened
- Balance unchanged at $100,000.00

### Weekly Review Action
- Check if this is a one-off or pattern (AI computing inverted SL/TP)
- May indicate the AI is uncertain about direction and hedging by inverting
- The CANDIDATE decision itself may have been correct — just the parameters were wrong
- Check backtest data for similar TP inversion cases

---

## Observation 4 Update: Inverted TP/SL is a Systematic Pattern

**Backtest cross-reference:** 30 out of 611 CANDIDATEs (4.9%) had inverted TP/SL in the batch backtest.
This is NOT a one-off — it happens consistently, especially on:
- LONG trades where TP1 < entry (AI puts target below entry)
- SHORT trades where SL < entry (AI puts stop below entry on a short)

**Clusters found:**
- 2025-01-21 to 2025-01-23: 7 inverted CANDIDATEs in 3 days
- 2025-09-15: 4 inverted CANDIDATEs on same day
- 2025-09-22 to 2025-09-26: 3 inverted CANDIDATEs in same week

**Implications:**
- Safety gate correctly blocks all of these (the system is safe)
- But 4.9% of valid setups are being wasted due to bad TP/SL computation
- At ~17 trades/month, that's ~1 trade/month thrown away by this bug
- The AI identifies the setup correctly but computes price levels incorrectly
- Possible fix: post-process AI output to auto-correct inverted TP/SL based on direction

**Agent task: investigate whether auto-correcting inverted TP/SL (swap direction) would have produced profitable trades in the backtest. If the 30 inverted trades had been flipped and executed, what would their WR and avg R have been?**


## Observation 5: MT5 Restart Breaks Process Connection (2026-04-07)

**Date:** Day 2 (Tuesday April 7)
**Impact:** USDJPY and GBPJPY failed every candle after MT5 was restarted — "Insufficient D1 candles: got 0, need 30"

### What Happened
- MT5 was closed and reopened to fix chart layout
- Running processes lost their MT5 connection (MT5 Python API requires `initialize()` to reconnect)
- `copy_rates_from_pos` returned None → 0 candles → DataIncompleteError
- Every candle from 10:15 to 11:00 failed for USDJPY and GBPJPY

### Root Cause
- `mt5.initialize()` is only called once in `_bootstrap()` during orchestrator startup
- When MT5 restarts, the connection is broken but the process doesn't know
- No reconnection logic exists

### Fix Applied
- Restarted all 5 processes manually

### WF-2 Action
- Add MT5 connection health check before each candle evaluation
- If `mt5.terminal_info()` returns None, call `mt5.initialize()` to reconnect
- Location: `src/mt5/mt5_real.py` `get_candles()` method — add reconnect on None result
- Simple: if `copy_rates_from_pos` returns None, try `self._mt5.initialize()` once and retry

### Operational Rule
**If you restart MT5, restart all trading processes too.**

---

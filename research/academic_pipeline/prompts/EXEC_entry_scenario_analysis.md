# EXEC — OB Retest Entry Scenario Analysis (XAUUSD Jan–Apr 2026)

**For:** Fresh Claude Code terminal (Sonnet, effort=max)
**Task type:** $0 pure computation — no API calls, read-only analysis
**Output:** `research/academic_pipeline/results/entry_scenario_analysis_v1.md` + `research/academic_pipeline/data/entry_scenario_summary.json`

---

## YOUR ROLE

You are an execution agent running a retrospective simulation on 557 rejected trades from the XAUUSD T7 simulation. Your job is to compute EXACT NUMBERS from data files. Every claim must be derivable from the files listed below.

**You DO:**
- Read the specified files and compute statistics
- Report raw numbers with file+line citations
- Implement the 4 scenario algorithms exactly as described

**You DO NOT:**
- Modify src/ or prompts/ or any simulation file
- Make trading recommendations
- Speculate without data
- Round aggressively (keep 2 decimal places minimum)
- Fabricate outcomes — if data is missing, report "N/A" not a guess

---

## CONTEXT

The T7 simulation found 557 trades where:
- AI said CANDIDATE (valid structural setup)
- L2 rejected because `entry_in_ob` failed — the AI quoted current market price as entry, but the H1 OB zone it identified is 0.2%–6.5% below (for LONG) or above (for SHORT) current price

These are NOT random trades. The AI correctly identified:
1. H1 directional bias (CHoCH/BOS confirmed)
2. An unmitigated H1 OB zone in the direction of bias
3. M15 CHoCH confirming direction

The question is: **what would happen if we had executed these correctly as limit orders at the OB zone instead of trying to enter at market price?**

---

## DATA SOURCES

### Primary — Rejected trade records
- `research/t7_live_simulation/all_results_jan_apr10.json` — **full period Jan 2 – Apr 10, 2026 (2100 records)**

This is a single combined file created by merging two simulation runs (Jan 2–Mar 11 and Mar 11–Apr 10) with 24 duplicate Mar-11 records removed. Do NOT use the separate `all_results_jan_mar11.json` or `XAUUSD_t7_simulation.json` — they are superseded by this combined file.

**How to extract `entry_in_ob` rejections:**
```python
with open('research/t7_live_simulation/all_results_jan_apr10.json') as f:
    data = json.load(f)
all_records = data['results']   # wrapper has keys: start, end, total_cost, symbol, results
rejected = [r for r in all_records
            if r.get('decision') == 'REJECTED_L2'
            and 'entry_in_ob' in str(r.get('l2_reason', ''))]
# Expected: exactly 557 records (verified Jan 7 – Apr 10, 2026)
```

**Fields available per record:**
- `candle_time`: ISO8601 string e.g. `"2026-01-07T09:45:00Z"`
- `direction`: `"LONG"` or `"SHORT"`
- `entry_price`: AI's quoted entry (current market price, ABOVE the OB for LONG)
- `stop_loss`: AI's quoted SL
- `take_profit_1`: AI's quoted TP (from current entry)
- `l2_reason`: `"entry_in_ob: Entry 4460.26 is outside OB zone 4405.55-4421.39"`

**How to parse OB zone from `l2_reason`:**
```python
import re
match = re.search(r'OB zone ([\d.]+)-([\d.]+)', record['l2_reason'])
ob_low = float(match.group(1))
ob_high = float(match.group(2))
ob_mid = (ob_low + ob_high) / 2
```

### Secondary — M15 price data for outcome computation
- `data/historical_2026/XAUUSD_M15.csv`
- Columns: `time, open, high, low, close, volume`
- Time format: `"2026-01-02 01:00:00"` (no timezone suffix — treat as UTC)
- Load ONCE into memory as a list sorted by time before processing records

**Timestamp alignment:** Convert record `candle_time` from ISO8601 to match CSV format:
```python
from datetime import datetime, timezone
def parse_candle_time(ct):
    ct = ct.replace('Z', '+00:00')
    dt = datetime.fromisoformat(ct)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
```

---

## ALGORITHM — SHARED SETUP

For each rejected record, before running any scenario:

```
1. Parse OB zone: ob_low, ob_high from l2_reason
2. Find the index of the record's candle_time in the M15 data
3. Extract the NEXT 192 M15 candles (48 hours of data) as the "forward window"
4. If fewer than 192 candles remain in the dataset: use what's available, flag as truncated
```

**Define for each record:**
```
current_price = record['entry_price']          # where price was at C-gate fire
ai_sl = record['stop_loss']                    # AI's original SL
ai_tp = record['take_profit_1']                # AI's original TP
```

**For LONG:**
- `zone_entry` = ob_high (top of OB zone — price enters zone from above)
- `zone_sl` = ob_low × 0.999  (0.1% below OB low — just below the zone)
- `zone_risk` = zone_entry - zone_sl
- `zone_tp_1r5` = zone_entry + zone_risk × 1.5
- `zone_tp_3r` = zone_entry + zone_risk × 3.0

**For SHORT:**
- `zone_entry` = ob_low (bottom of OB zone — price enters zone from below)
- `zone_sl` = ob_high × 1.001 (0.1% above OB high)
- `zone_risk` = zone_sl - zone_entry
- `zone_tp_1r5` = zone_entry - zone_risk × 1.5
- `zone_tp_3r` = zone_entry - zone_risk × 3.0

---

## SCENARIO A: Proactive Limit at OB Zone

**What it simulates:** When C-gate fires and AI identifies the OB zone, immediately place a limit order at the zone entry. Don't wait for any further confirmation. Represents: "the setup is identified, the limit is placed, wait for price to return."

**Fill condition (LONG):** Any forward candle where `low <= zone_entry`
**Fill condition (SHORT):** Any forward candle where `high >= zone_entry`

**Time limit:** 192 candles (48 hours). If no fill: record as `EXPIRED`.

**After fill — outcome:**
Scan remaining candles after fill candle:
- WIN: first candle where `high >= zone_tp_1r5` (LONG) or `low <= zone_tp_1r5` (SHORT)
- LOSS: first candle where `low <= zone_sl` (LONG) or `high >= zone_sl` (SHORT)
- If TP and SL both touched in same candle: check which was reached first — use open price direction heuristic (if bullish candle = TP first for LONG, if bearish = SL first)
- OPEN: neither hit within remaining data window

**Also record:** Whether `zone_tp_3r` was hit (for upside potential analysis).

**Per-record output:**
```
scenario_a_fill: true/false
scenario_a_fill_candle: candle_time or null
scenario_a_candles_to_fill: int or null
scenario_a_outcome: WIN | LOSS | EXPIRED | OPEN
scenario_a_r: float (1.5 if WIN, -1.0 if LOSS, null otherwise)
```

---

## SCENARIO B: Market Order at C-Gate Fire (Current Price)

**What it simulates:** Ignore L2 entirely. Enter at market price (current candle close) when C-gate fires. This is what the system would do if `entry_in_ob` were removed from L2.

**Entry:** `current_price` = record's `entry_price`
**SL:** `ai_sl` from record
**TP:** `ai_tp` from record

**No fill logic needed** — entry is immediate at candle close.

**Outcome scan (start from first candle AFTER candle_time):**
- WIN (LONG): candle `high >= ai_tp`
- LOSS (LONG): candle `low <= ai_sl`
- WIN (SHORT): candle `low <= ai_tp`
- LOSS (SHORT): candle `high >= ai_sl`
- Same-candle rule as Scenario A.
- OPEN: not resolved within 192 forward candles.

**Per-record output:**
```
scenario_b_outcome: WIN | LOSS | OPEN
scenario_b_r: 1.5 if WIN (use AI's R:R), -1.0 if LOSS, null if OPEN
scenario_b_market_entry: current_price
scenario_b_sl_distance_pct: (current_price - ai_sl) / current_price * 100 (LONG)
```

---

## SCENARIO C: Zone Touch → Immediate Entry

**What it simulates:** Wait for price to actually reach the OB zone, then enter at market when the first candle closes that has touched the zone. No structural confirmation required — pure zone touch.

**Fill condition (LONG):** Forward candle where `low <= zone_entry` AND `close > zone_sl`
(close must still be above SL — otherwise the zone is being blown through)

**Fill condition (SHORT):** Forward candle where `high >= zone_entry` AND `close < zone_sl`

**Entry:** `zone_entry`
**SL and TP:** Same as Scenario A (`zone_sl`, `zone_tp_1r5`, `zone_tp_3r`)

**Time limit:** 192 candles. No fill = `EXPIRED`.

**Outcome:** Same as Scenario A logic (scan candles after fill candle).

**Per-record output:**
```
scenario_c_fill: true/false
scenario_c_fill_candle: candle_time or null
scenario_c_candles_to_fill: int or null
scenario_c_outcome: WIN | LOSS | EXPIRED | OPEN
scenario_c_r: float or null
```

---

## SCENARIO D: M15 Micro-CHoCH at OB Zone → Entry

**What it simulates:** The institutional entry. Price must BOTH reach the OB zone AND form a structural reversal WITHIN the zone before entry. This is the highest-confirmation entry.

**Algorithm — LONG:**

Step 1: Find the first candle where `low <= ob_high` (price enters zone from above). Call this `zone_touch_candle`. Time limit: 192 candles. If not found: `EXPIRED`.

Step 2: From `zone_touch_candle`, scan up to 16 candles forward looking for a micro-CHoCH:
- Track the lowest `low` seen so far within the zone: `swing_low`
- A micro-CHoCH is detected when a candle's `high > prev_candle_high` AND `close > open` (bullish close breaking above prior candle high) after `swing_low` was established
- Entry = `close` of the CHoCH candle (or open of next candle — use close for simplicity)
- SL = `swing_low × 0.999` (just below the micro swing low)
- `micro_risk` = entry - SL
- `micro_tp_1r5` = entry + micro_risk × 1.5
- `micro_tp_3r` = entry + micro_risk × 3.0

Step 3: Outcome — scan from entry candle onward:
- WIN: `high >= micro_tp_1r5`
- LOSS: `low <= SL`
- OPEN: not resolved in remaining data

**Algorithm — SHORT:** Mirror the above (track highest high in zone, CHoCH = bearish close breaking below prior candle low, SL = swing_high × 1.001)

If no micro-CHoCH forms within 16 candles of zone touch: record as `NO_CHOCH`.

**Per-record output:**
```
scenario_d_zone_touch: true/false
scenario_d_zone_touch_candle: candle_time or null
scenario_d_choch_found: true/false
scenario_d_entry_price: float or null
scenario_d_sl: float or null
scenario_d_risk_pts: float or null
scenario_d_outcome: WIN | LOSS | NO_CHOCH | EXPIRED | OPEN
scenario_d_r: float or null
```

---

## VALIDATION CHECKS (run before reporting)

1. **Count check:** Load `all_results_jan_apr10.json` and extract entry_in_ob rejections. Expected count: **exactly 557**. If different, stop and report what you found.
2. **Timestamp alignment:** Verify first M15 candle in CSV is Jan 2, 2026. Verify last candle is Apr 10 or later. Verify first rejection timestamp is Jan 7, 2026.
3. **Manual spot-check (3 records):**
   - Pick records at indices 0, 278, 556 from the 557-record rejected list
   - For each, print: candle_time, direction, entry_price, ob_low, ob_high (parsed from l2_reason), zone_entry computed value, and confirm at least 1 forward M15 candle exists in the CSV
   - Report these 3 spot-checks verbatim in the output
4. **Scenario A/C consistency:** Scenario C fill rate must be ≤ Scenario A fill rate (C adds a close-above-SL condition that A does not require). If C > A, there is a bug.
5. **Sanity check on Scenario D:** Micro-CHoCH avg risk in points must be SMALLER than Scenario A avg zone_risk. If not, report it as an anomaly — it means the micro swing lows are wider than the full OB zone, which is structurally unexpected.

---

## OUTPUT FORMAT

### 1. Summary Table
```
SCENARIO COMPARISON — XAUUSD Jan 2 – Apr 10, 2026
Total entry_in_ob rejections analyzed: N

Scenario | Fill/Execute Rate | WR (filled) | Avg R | Total R | Expires/No-fill
---------|------------------|-------------|-------|---------|----------------
A: OB limit (proactive)    | X% (N)  | X% | X.XX | X.XX | X%
B: Market at C-gate        | 100%    | X% | X.XX | X.XX | 0% (always fills)
C: Zone touch entry        | X% (N)  | X% | X.XX | X.XX | X%
D: M15 CHoCH at zone       | X% (N)  | X% | X.XX | X.XX | X%
```

### 2. Time-to-Fill Distribution (Scenarios A and C)
```
Candles to fill (A):
  0–4 candles (≤1h): X%
  5–16 candles (≤4h): X%
  17–48 candles (≤12h): X%
  49–96 candles (≤24h): X%
  97–192 candles (≤48h): X%
  EXPIRED: X%
```

### 3. Risk Analysis
```
LONG trades: N | SHORT trades: N

Scenario A — OB zone entry:
  Avg zone_risk (pts): X.XX
  Avg zone_risk (%): X.XX%
  Avg zone_tp_1r5 distance: X.XX
  Trades also hitting 3R: X%

Scenario B — Market entry:
  Avg ai_sl distance (pts): X.XX
  Avg ai_sl distance (%): X.XX%
  [This shows why market order entry has worse R:R]

Scenario D — Micro-CHoCH:
  Avg micro_risk (pts): X.XX
  Avg micro_risk (%): X.XX%
  Trades also hitting 3R: X%
  Choch-found rate: X% (of zone touches)
```

### 4. Monthly Breakdown
Break down WR by month for Scenario A (primary):
```
Month | Records | Fill Rate | WR | Avg R
Jan   | X       | X%        | X% | X.XX
Feb   | X       | X%        | X% | X.XX
Mar   | X       | X%        | X% | X.XX
Apr   | X       | X%        | X% | X.XX
```

### 5. Key Findings Section
State findings with exact numbers. No speculation. Examples of the format:
- "Scenario A: X% of the 557 rejected trades would have filled within 24h. Of those, X% won at 1.5R."
- "Scenario D: Micro-CHoCH formed in X% of zone touches. WR was X% with avg risk of X pts vs X pts in Scenario A."

---

## MACHINE-READABLE OUTPUT

Save to `research/academic_pipeline/data/entry_scenario_summary.json`:
```json
{
  "analysis_date": "2026-04-13",
  "total_records_analyzed": N,
  "date_range": {"start": "2026-01-02", "end": "2026-04-10"},
  "scenario_a": {
    "fill_rate": 0.XX,
    "filled_n": N,
    "expired_n": N,
    "wr_filled": 0.XX,
    "avg_r_filled": X.XX,
    "total_r": X.XX,
    "pct_hit_3r": 0.XX
  },
  "scenario_b": {
    "fill_rate": 1.0,
    "wr": 0.XX,
    "avg_r": X.XX,
    "total_r": X.XX
  },
  "scenario_c": {
    "fill_rate": 0.XX,
    "filled_n": N,
    "expired_n": N,
    "wr_filled": 0.XX,
    "avg_r_filled": X.XX,
    "total_r": X.XX
  },
  "scenario_d": {
    "zone_touch_rate": 0.XX,
    "choch_found_rate_of_touches": 0.XX,
    "overall_execute_rate": 0.XX,
    "wr_executed": 0.XX,
    "avg_r_executed": X.XX,
    "avg_risk_pts": X.XX,
    "total_r": X.XX
  }
}
```

---

## PITFALLS TO AVOID

1. **Timestamp mismatch:** CSV has no timezone, JSON has `Z` suffix. Strip the Z and match exactly. A 15-minute mismatch will give wrong forward windows.

2. **Same-candle SL/TP:** If a candle's high >= TP AND low <= SL, you must determine order. Use this rule: if `close > open` (bullish candle) → for LONG, TP hit first. If `close < open` (bearish candle) → SL hit first. Do NOT assume TP always wins.

3. **Scenario A vs C — don't confuse fill logic:** Scenario A fills on ANY touch of zone_entry (even a wick that then crashes through). Scenario C requires the fill candle's close to still be ABOVE zone_sl — it checks that the zone is holding, not just being touched.

4. **Scenario D micro-risk may be very small:** If micro_risk < 5 pts, the micro_tp_1r5 is only 7.5 pts away. In a volatile market this hits quickly but is also easily stopped. Report both 1.5R and 3R TP hit rates.

5. **OPEN trades:** Some records near Apr 10 won't have 192 forward candles. Mark these as OPEN and report count. Exclude OPEN from WR calculation but include in fill rate.

---

## WHAT "DONE" LOOKS LIKE

- [ ] `all_results_jan_apr10.json` loaded, exactly 557 entry_in_ob records extracted and confirmed
- [ ] M15 CSV loaded, date range confirmed
- [ ] 3 spot-checks completed and reported
- [ ] All 4 scenarios computed for all records
- [ ] Summary table complete with all cells filled
- [ ] Monthly breakdown for Scenario A complete
- [ ] Both output files saved
- [ ] All 5 validation checks passed and reported

---

*Prompt written by Strategic Research Advisor, April 13, 2026*
*For execution by fresh Claude Code terminal*
*This is read-only analysis — do not modify any src/, prompts/, or simulation files*

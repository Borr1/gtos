# US30_cash — Thursday 2026-04-23 Session Analysis

*Author: Claude Code (Data Analyst role)*
*Analysis date: 2026-04-24*
*Read-only investigation of US30_cash trading activity on 2026-04-23.*

---

## Executive Summary

1. **Zero US30 trades filled on Thursday.** All 6 AI-generated CANDIDATEs were blocked at Level-2 verification or a post-M5 L2 re-check. `execution: null` and `exit: null` on every trade record (`knowledge_base/trade_records/US30_cash/2026-04-23_*.json` — see trade record line citations).
2. **Dominant failure mode = AI POI hallucination.** 4 of 4 London CANDIDATEs cited an **M15 OB as the H1 POI** (specifically 49175.21-49144.21, touches=1 on M15). L2 correctly rejected these with `blocked_by: "h1_poi_exists"` because no unmitigated H1 OB existed near the AI-cited price level (~49175-49531). The only two unmitigated H1 OBs all day were 48590.30-48472.35 (touches=4) and 48645.71-48629.71 (touches=2) — both down ~500-700 points and both `touches≥2` (disqualified by prompt rule).
3. **NY 13:46 passed L2 but died at the post-M5 re-check.** AI cited a legitimate H1 OB (49155.31-49365.31, touches=1, formed 2026-04-23T12:00 UTC), SL at 49046.27 was valid, but M5 refinement TIGHTENED the SL to 49219.75 — pushing it INSIDE the H1 OB zone → `REJECTED_L2_POST_M5` (`src/components/orchestrator.py:840`).
4. **NY 16:00 had inconsistent AI output.** AI picked the touches=4 H1 OB (POI=48531.325) as rationale but set `entry_price=48645.71` (top of the touches=2 OB). L2 matched the POI to the touches=4 OB and then failed `sl_beyond_ob` (SL 48599.49 is NOT below zone_low 48472.35). Classic FA-2-style AI consistency bug.
5. **Pre-AI gate correctly stayed passive.** Gate fired 0 times on US30 Thursday because 2 bullish unmitigated H1 OBs existed throughout the day (pre-AI gate invariant: H1 POI exists ⇒ do not skip AI call). Invariant holds (verified by MSO snapshots in all 6 trade records).

**Net impact on account:** $98,026.71 → $99,287.62 = +$1,260.91 (+1.286%). Gains came entirely from other instruments; US30 contributed 0 trades and 0 PnL. Pipeline burned 20 × ~$0.30 = ~$6 in Sonnet 4.6 API calls for net-zero US30 trading output.

---

## 1. Session Timeline

All times UTC. Account start 2026-04-23 00:01:02 with balance $98,026.71 (`logs/us30.log:2378`). US30 broker-local time is ~UTC+2-3 (broker offsets show +1h46min between stored MSO times and candle_time, consistent with DST UTC+2).

| # | Candle Time (UTC) | KZ | Index | AI Decision | Grade | Direction | Confidence | Displacement Quality / Ratio | Framework | Downstream Outcome |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 08:16:11 | london | 0 | CANDIDATE | A+ | LONG | 75 | strong / 3.9 | ob_retest | **REJECTED_L2** (h1_poi_exists) |
| 2 | 08:30:05 | london | 1 | CANDIDATE | A+ | LONG | 75 | strong / 3.9 | ob_retest | **REJECTED_L2** (h1_poi_exists) |
| 3 | 08:45:05 | london | 2 | CANDIDATE | A+ | LONG | 75 | strong / 3.5 | ob_retest | **REJECTED_L2** (h1_poi_exists) |
| 4 | 09:00:05 | london | 3 | CANDIDATE | A+ | LONG | 72 | strong / 3.7 | ob_retest | **REJECTED_L2** (h1_poi_exists) |
| 5 | 09:15:05 | london | 4 | NO_TRADE | C | — | 72 | strong / 2.3 | none | no trade record |
| 6 | 09:30:05 | london | 5 | NO_TRADE | C | — | 72 | strong / 2.9 | none | no trade record |
| 7 | 09:45:05 | london | 6 | NO_TRADE | C | — | 72 | strong / 2.9 | none | no trade record |
| 8 | 10:00:05 | london | 7 | NO_TRADE | C | — | 72 | weak / 0.7 | none | no trade record |
| 9 | 10:15:05 | london | 8 | NO_TRADE | C | — | 72 | strong / 2.6 | none | no trade record |
| 10 | 10:30:05 | london | 9 | NO_TRADE | C | — | 72 | strong / 2.8 | none | no trade record |
| 11 | 13:46:12 | ny | 0 | CANDIDATE | A+ | LONG | 78 | strong / 2.3 | ob_retest | **REJECTED_L2_POST_M5** |
| 12 | 14:00:05 | ny | 1 | NO_TRADE | C | — | 72 | none / 0.0 | none | no trade record |
| 13 | 14:15:05 | ny | 2 | NO_TRADE | C | — | 72 | strong / 3.0 | none | no trade record |
| 14 | 14:30:05 | ny | 3 | NO_TRADE | C | — | 72 | strong / 2.9 | none | no trade record |
| 15 | 14:45:05 | ny | 4 | NO_TRADE | C | — | 72 | strong / 2.2 | none | no trade record |
| 16 | 15:00:05 | ny | 5 | NO_TRADE | C | — | 72 | strong / 4.2 | none | no trade record |
| 17 | 15:15:05 | ny | 6 | NO_TRADE | C | — | 72 | strong / 2.7 | none | no trade record |
| 18 | 15:30:05 | ny | 7 | NO_TRADE | C | — | 72 | strong / 3.6 | none | no trade record |
| 19 | 15:45:05 | ny | 8 | NO_TRADE | C | — | 72 | strong / 2.6 | none | no trade record |
| 20 | 16:00:05 | ny | 9 | CANDIDATE | A+ | LONG | 78 | strong / 2.6 | ob_retest | **REJECTED_L2** (sl_beyond_ob) |

Totals: 20 candles evaluated (10 London + 10 NY) ≈ matches `live_sessions/US30_cash/2026-04-23_*_summary.json` (10+10 evaluated). Session summary file misleadingly shows `CANDIDATE: 0` because downstream rejections overwrite the candle_log decision — see note at §10 "Concerns".

**Session-summary apparent anomaly (noted, not a bug):** `live_sessions/US30_cash/2026-04-23_london_summary.json:16-19` and `_ny_summary.json:16-19` both show `"CANDIDATE": 0` even though 6 CANDIDATEs were produced. This is by design — `orchestrator._save_session_summary()` counts from `candle_log` entries where downstream rejection codes (REJECTED_L2, etc.) overwrite the initial CANDIDATE label (`src/components/orchestrator.py:2467-2475`). The raw eval JSONL is the source of truth for AI decisions.

### Are the 4 back-to-back London CANDIDATEs distinct or duplicates?

**They are effectively duplicates — all attempting entry on the same (non-existent H1) POI.** Each of 0816/0830/0845/0900 has:
- Same AI-cited POI price level (49531.305 on 0816/0830/0900, 49175.21 on 0845).
- Same declared entry_price = 49175.21 (top of the M15 OB 49175.21-49144.21 formed at 08:30).
- Nearly identical SL (49118.71, 49118.71, 49118.46, 49140.46) and TP1 (49260.46, 49259.96, 49260.44, 49227.34).

The AI is repeatedly "discovering" the same M15 OB at 49175.21-49144.21 each candle and mislabelling it as an H1 POI. Since the system doesn't de-dupe CANDIDATEs across back-to-back candles (`SKIP_KZ_TRADED` only fires after an EXECUTED trade), the pipeline re-pays the API cost each 15 min.

---

## 2. Candidate Detail Table (6 rows)

| # | Candle (UTC) | KZ | Direction | Entry | SL | TP1 | sl_buffer_applied | AI-cited POI | AI's claimed OB zone | Downstream outcome | Blocked by |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 08:16:11 | london | LONG | 49175.21 | 49118.71 | 49260.46 | 11.5 | 49531.305 | H1 OB 49175.21-49144.21 (AI says — but this is an **M15** OB) | REJECTED_L2 | `h1_poi_exists` |
| 2 | 08:30:05 | london | LONG | 49175.21 | 49118.71 | 49259.96 | 11.5 | 49531.305 | same M15 OB | REJECTED_L2 | `h1_poi_exists` |
| 3 | 08:45:05 | london | LONG | 49175.21 | 49118.46 | 49260.44 | 11.25 | 49175.21 | same M15 OB | REJECTED_L2 | `h1_poi_exists` |
| 4 | 09:00:05 | london | LONG | 49175.21 | 49140.46 | 49227.34 | 23.75 | 49531.305 | same M15 OB | REJECTED_L2 | `h1_poi_exists` |
| 5 | 13:46:12 | ny | LONG | 49365.31 | 49046.27 | 49843.87 | 29.54 | 49260.31 | H1 OB 49155.31-49365.31 (touches=1, formed 2026-04-23T12:00 UTC) — **valid** | REJECTED_L2_POST_M5 | post-M5 re-verify of `sl_beyond_ob` |
| 6 | 16:00:05 | ny | LONG | 48645.71 | 48599.49 | 48714.98 | 30.37 | 48531.325 (midpoint of touches=4 H1 OB) | AI's entry uses touches=2 OB high (48645.71) but POI points to touches=4 OB | REJECTED_L2 | `sl_beyond_ob` |

### Sources
- Candle #1 params: `knowledge_base/trade_records/US30_cash/2026-04-23_london_0816.json:14159-14168` (ai_response.trade_parameters).
- Candle #2: `..._0830.json:14185-14188`.
- Candle #3: `..._0845.json:14118-14121`.
- Candle #4: `..._0900.json:14107-14110`.
- Candle #5: `..._ny_1346.json:14257-14260` (pre-M5) — note post-M5 SL was moved to 49219.75 (`logs/us30.log:2557`).
- Candle #6: `..._ny_1600.json:14109-14112`.

### `sl_buffer_applied` audit (FA-2 non-degenerate requirement)
All 6 candidates have `sl_buffer_applied > 0`:

| # | Buffer | FA-2 compliant? |
|---|---|---|
| 1 | 11.5 | Yes |
| 2 | 11.5 | Yes |
| 3 | 11.25 | Yes |
| 4 | 23.75 | Yes |
| 5 | 29.54 | Yes |
| 6 | 30.37 | Yes |

FA-2 (`fa35cc0`) shipped the non-zero `sl_buffer_applied` requirement; no degeneracy detected. No `guard_candidate_degenerate_params` trigger in any record (field-absent across all 6 trade records — confirmed by grep `guard_candidate_degenerate`: 0 matches).

### AI output precision check (FA-2 FX precision guard)
Prices are to 2 decimals (48645.71, 49365.31, etc.) which matches MSO precision. `sl_buffer_applied` ranges 11.25-30.37 (non-zero). No precision-class violation.

---

## 3. Fill Reconciliation Table

| # | Candle (UTC) | Direction | Entry intent | Filled at price | Filled at time | Ticket | Outcome | R-multiple |
|---|---|---|---|---|---|---|---|---|
| 1 | 08:16:11 | LONG | 49175.21 | — | — | — | Never reached execution | N/A |
| 2 | 08:30:05 | LONG | 49175.21 | — | — | — | Never reached execution | N/A |
| 3 | 08:45:05 | LONG | 49175.21 | — | — | — | Never reached execution | N/A |
| 4 | 09:00:05 | LONG | 49175.21 | — | — | — | Never reached execution | N/A |
| 5 | 13:46:12 | LONG | 49365.31 | — | — | — | Never reached execution | N/A |
| 6 | 16:00:05 | LONG | 48645.71 | — | — | — | Never reached execution | N/A |

### Evidence
- Every trade record has `"execution": null` and `"exit": null` (6/6 confirmed via `Grep "execution|exit" …/2026-04-23_*.json`).
- No `order_send` / `LIMIT_PLACED` / `LIMIT_FILLED` strings appear in `logs/us30.log` for 2026-04-23 (grep counts 0).
- Log line for 13:46: `L2 verification FAILED: sl_beyond_ob` → returns before Gate1/execution (`logs/us30.log:2561`).
- Log line for 16:00: `L2 verification FAILED: sl_beyond_ob` → same return (`logs/us30.log:2604`).
- Log line for 08:16/08:30/08:45/09:00: trade record saved with `final_outcome: REJECTED_L2` (`logs/us30.log:2482, 2493, 2504, 2515`).

**Result: US30 did NOT participate in Thursday's $1,260.91 P&L. All gains came from other instruments.**

---

## 4. Rejection Bucket Analysis

### The 14 NO_TRADEs broken down by reason category

| Bucket | Count | Example reasons |
|---|---|---|
| C2 FAIL — M15 bearish CHoCH opposing H1 bullish | 4 | "M15 bearish CHoCH at 49188.00 with displacement ratio 2.3 (strong) actively opposes H1 bullish bias" (candle #5/09:15). "M15 CHoCH bearish at 49153.31 (displacement ratio=2.8, strong)" (candle #10/10:30). |
| Framework-level — all C-gates pass but no unmitigated H1 OB with touches<2 | 9 | "All three C-gates pass but the OB retest framework requires an unmitigated H1 OB with touches<2 as the entry POI" (candles #6/09:30, #7/09:45, #12/14:00, #13/14:15, #14/14:30, #15/14:45, #16/15:00, #17/15:15, #18/15:30, #19/15:45) |
| C1 FAIL (H1 bias) | 0 | none |
| C3 FAIL (direction mismatch) | 0 | none |
| Other | 1 | #8/10:00 — "weak" displacement + C2 FAIL ("M15 bearish CHoCH at 49153.31") — double classification issue; AI cited C2 FAIL, so bucketed with C2 group → re-bucketed. Net: 9 framework + 5 C2 (not 4+9). |

**Corrected:** 5 × C2-FAIL, 9 × framework-no-OB, 0 × C1, 0 × C3 = 14 total NO_TRADE. Row-by-row re-audit from `knowledge_base/live_evaluations/US30_cash/2026-04-23.jsonl:5-19` (rows 5-19 excluding CANDIDATEs at 11 and 20).

Row 5 (09:15): C2 FAIL. Row 6 (09:30): framework. Row 7 (09:45): framework. Row 8 (10:00): C2 FAIL (weak displacement + CHoCH). Row 9 (10:15): C2 FAIL. Row 10 (10:30): C2 FAIL. Rows 12-15 (14:00-14:45): framework. Row 16 (15:00): framework. Row 17 (15:15): framework. Row 18 (15:30): framework. Row 19 (15:45): framework. Total: 5 × C2 + 9 × framework = 14. ✓

### Is the "M15 bearish CHoCH opposes H1 bullish" claim legitimate?

**Yes — these are genuine M15 opposition events**, based on the MSO data the AI saw:

- At candle #5 (09:15 UTC), AI cites M15 bearish CHoCH at **49188.00** with displacement ratio **2.3**. Looking at the M15 swing data from the 0816 record's user_message (`logs/us30.log:2474, knowledge_base/trade_records/US30_cash/2026-04-23_london_0816.json:14104` user_message M15 swings): M15 printed highs at 49228.41 (09:15) → low 49188.00 (09:45). That's a valid CHoCH point — price took out prior M15 low.
- Pattern continues: CHoCH at 49153.31 (08/09:45 / 10:00-10:30 UTC) — the M15 low walk.

The H1 bullish bias stayed intact all day (5+ consecutive BOS). But M15 pulled back in a structured way (not a single-candle noise). Under the prompt's C2 rule *"A single opposing candle or minor pullback does NOT constitute active opposition. M15 CHoCH AGAINST H1 → FAIL."* — each CHoCH with displacement ≥2.0 qualifies as active opposition. **The AI is not confused about direction here.** Whether the **M15 CHoCH threshold at 2.x displacement is the right velocity brake** is a separate strategic question (see §7 below).

---

## 5. Pre-AI Gate Status

**Fired 0 times on US30 Thursday.** Confirmed via `grep -c "Pre-AI gate skip\|no_unmitigated.*h1_pois" logs/us30.log` = 0.

### Invariant verification

Pre-AI gate (`src/components/pre_ai_gates.py:12-76`) skips the AI call only when `mso.timeframes["H1"].order_blocks` has no unmitigated OB (and no unretested breaker) in the bias direction. The bias on all 20 candles was `bullish`.

MSO snapshots in all 6 trade records confirm the gate was correctly passive:

| Candle | Bullish unmitigated H1 OBs present | Gate should fire? |
|---|---|---|
| 0816 | 2 (48590.30-48472.35 touches=4; 48645.71-48629.71 touches=2) | No — gate passive ✓ |
| 0830 | 2 (same) | No ✓ |
| 0845 | 2 (same) | No ✓ |
| 0900 | 2 (same) | No ✓ |
| 1346 | 3 (+ new OB 49155.31-49365.31 touches=1 formed ~12:00 UTC) | No ✓ |
| 1600 | 2 (first two) | No ✓ |

Proof from Python inspection of 1346 record (MSO timeframes.H1.order_blocks count-unmitigated-bullish = 3, formation times 2026-04-16, 2026-04-17, 2026-04-23T15:00 in broker-local ≈ 12:00 UTC).

**Invariant HOLDS.** Pre-AI gate never would have blocked an AI call that L2 downstream would have passed — because the OBs exist. The fact that 4 London CANDIDATEs failed L2 on `h1_poi_exists` is **unrelated to the pre-AI gate**: L2 failed because the AI cited an OB that **doesn't exist at the cited price level**, not because no H1 OB existed.

---

## 6. Missed-Setup Analysis

### Did the system miss any valid H1 OB retest?

**Unlikely, but with caveats.** Looking at H1 unmitigated OB availability through the day:

| Time (UTC) | Unmitigated bullish H1 OBs | Price zone | Price range that session | Valid retest opportunity? |
|---|---|---|---|---|
| 08:16-10:30 (London) | 48590.30-48472.35 (touches=4 — over touches limit), 48645.71-48629.71 (touches=2 — at touches limit) | ~48.5K | 49121-49269 | **No** — price was 500+ points above both OBs; neither was being retested, and both had touches≥2 |
| 13:46 (NY start) | Same two, plus NEW 49155.31-49365.31 (touches=1) formed ~12:00 UTC | 49.2K zone | 49076-49365 | **Yes** — price retested the new OB at candle 13:46 (actual retest context) |
| 14:00-15:45 (NY) | Same three, but new OB accumulating touches (post-retest) | 49.2K zone | 49116-49365 | Declining — after 14:00 the new OB accumulated touches and no longer qualified |
| 16:00 (NY close) | Back to only 48590.30-48472.35 (touches=4) and 48645.71-48629.71 (touches=2) | ~48.5K | 49278-49340 | **No** — price too high, touches too high |

**The one valid retest opportunity of the day was the NY 13:46 candle** — and the AI recognized it, L2 passed, but M5 refinement tightened the SL and killed the trade (see §3).

### Did the system issue CANDIDATEs on zones a human would reject?

**Yes — 4 of 6 CANDIDATEs were on a non-existent H1 POI.** The AI hallucinated: cited an M15 OB (49175.21-49144.21 touches=1, formed 2026-04-23T08:30 — a brand-new minor structure) as its H1 POI. A human SMC trader would not call that an H1 OB — it's an M15-scale structure. The prompt clearly says "Nearest unmitigated H1 OB" for h1_setup — AI pulled from M15 instead. **The L2 `h1_poi_exists` check caught all 4.**

### Were there any bearish OB retests the system never considered?

No. D1 and H4 structure is bullish (D1 "transitional" / H4 "bullish" per pre-screen `live_sessions/US30_cash/2026-04-23_london_summary.json:8-10`). H1 has 5 consecutive bullish BOS. Bias computation (deterministic) produced `bullish` from `H4+H1_consensus` (`logs/us30.log:2476`). System does not evaluate SHORT when bias is bullish.

Was bullish bias wrong? Looking at intraday M15 CHoCHs at 49188.00, 49153.31 — price DID pull back 180 points from London high (49278.31) to London low (49076.81 at 13:15 UTC). But it recovered, ended the day at 49340.50. **Bullish bias held.** So no missed SHORT opportunities.

---

## 7. Displacement / Sweep — Interpretation Notes

### M15 displacement ratios 2.3-2.8 on bearish CHoCHs — sufficient to disqualify C2?

Per prompt (`..._0816.json:14103` system_prompt):
> "A single opposing candle or minor pullback does NOT constitute active opposition. M15 CHoCH AGAINST H1, or a series of BOS actively opposing H1 → FAIL."

The AI applied the rule as written. Displacement ratio 2.3-2.8 is "strong" (>1.5× avg body). A bearish CHoCH with strong displacement against the prevailing H1 bullish is, by the letter of C2, a FAIL.

**Whether this is too aggressive is a strategic question** outside the scope of this analysis. Observational note: price did NOT confirm the CHoCH — the 180-point drawdown recovered by NY open, and H1 continued making bullish BOS. So those C2-FAIL decisions were, in retrospect, **over-rejections**. That's consistent with the prompt's own calibration note: "Over-rejection is as costly as over-acceptance — rejecting a qualifying setup costs the system +0.20R expected value." (`..._0816.json:14103` system_prompt CALIBRATION section).

### Displacement shadow log (`shadow_logs/displacement_events.jsonl`)

No US30 entries logged for 2026-04-23 (last US30 entry in the file is 2026-04-22T13:30:00). The logger only captures displacement events >=2.0 — M15 Thursday had a few candles just above 2.0 but the shadow logger's filter may be stricter, or the logger hit a gap. **This is a log hygiene issue worth flagging** but is not blocking.

### Sweep detection

All 6 CANDIDATEs reported `sweep_detected: true`. London group: `pdl` sweep quality clean. NY group: `asian_high` sweep quality clean. Sweep detection is not the issue today.

---

## 8. Trade Record Integrity

Verified invariants across all 6 trade records:

| Invariant | 0816 | 0830 | 0845 | 0900 | 1346 | 1600 |
|---|---|---|---|---|---|---|
| ai_response.trade_parameters matches top-level trade_parameters (no intent drift) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| sl_buffer_applied > 0 (FA-2 non-degenerate) | 11.5 | 11.5 | 11.25 | 23.75 | 29.54 | 30.37 |
| No `guard_candidate_degenerate_params` trigger | ✓ (absent) | ✓ | ✓ | ✓ | ✓ | ✓ |
| System version | 8a9bcfe | 8a9bcfe | 8a9bcfe | 8a9bcfe | 8a9bcfe | 8a9bcfe |
| Execution section null (no order placed) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

All records use the current HEAD commit `8a9bcfe` (confirms FA-4 + T2.8 + model migration + pre-AI gate are live).

### Anomaly: AI reports vs L2-computed displacement ratio (informational)

Logged mismatches:

| Candle | AI-reported ratio | L2/MSO-computed ratio | Mismatch Δ |
|---|---|---|---|
| 0816 | 3.90 | 1.59 | **2.31** |
| 0830 | 3.90 | 1.61 | **2.29** |
| 0845 | 3.50 | **12.67** | **-9.17** |
| 0900 | 3.70 | 1.54 | **2.16** |
| 1346 | 2.30 | 4.32 | -2.02 |
| 1600 | 2.60 | 3.64 | -1.04 |

Root cause: L2's `_check_displacement_ratio` iterates `m15_tf.structure_events` and returns the FIRST qualifying event (CHoCH preferred, else BOS). The `structure_events` list appears to be ordered oldest-first, so L2 attaches to **week-old** events like "M15 BOS bullish with displacement found at 2026-04-14T09:30:00+00:00" (verified in L2 detail strings of `0816.json:23`, `0830.json:23`). This is a sub-optimality — L2 should pick the **most recent** qualifying event to meaningfully validate the AI. It does not cause trade rejections today (all displacement checks passed because historical events satisfied the ≥1.5 threshold), but it means L2's numerical validation is loose.

Recommendation for future commit (not part of this analysis output): update `src/components/verification.py:173-202` to reverse-iterate or explicitly pick the most recent event. Low priority — shadow bug.

---

## 9. Outcome vs Edge Expectation

Zero fills → no R-multiples to evaluate. Strict empirical measurement is not possible for Thursday.

### Counterfactual: what if the 4 London bug-CANDIDATEs had filled?

AI intent: LONG @ 49175.21, SL @ 49118.46-49140.46, TP1 @ 49227.34-49260.46. Range of intent: ~$56 distance to SL, ~$85 to TP1.

Actual US30 intraday price walk (from M15 swings, `_0816.json:14104`):
- 08:00-09:15 UTC: ranging 49121-49228 (above intent entry 49175.21)
- 09:15-10:45 UTC: retraced to 49076.81 low (13:15 UTC) — would hit entry AND SL
- Post-13:15: recovered to 49340.50 by 16:45 UTC

If filled at 49175.21 with SL 49118.71 (0816 params):
- Would fill on the retrace down to ~49121 in the 09:15-10:30 London low sweep.
- Would SL-out at 49118.71 on the 13:15 low excursion (49076.81) — loss -1R.

**So the bug-CANDIDATEs would have ALL lost -1R had L2 passed them.** L2 saved ~4R of loss today (plus the 2 NY CANDIDATEs — see below).

### Counterfactual: NY 1346 with AI's original SL (pre-M5)

Entry 49365.31 LONG limit. Original SL 49046.27 (319-point buffer, massively wider than normal). TP1 49843.87.

Price action after 13:46 UTC:
- Retraced to 49076.81 at 13:15 UTC (before candle, already done).
- Then rallied to 49365+ by NY close.
- Actual range (NY KZ): 49076-49365.

Limit entry 49365.31 requires price to reach 49365.31 then retrace. Price hit 49365 in NY but didn't cleanly retest (high wicks, closes below). **Likely would NOT have filled** as a limit order. If market order, would have filled at ~49221 (actual price at candle time per `..._ny_1346.json:14299`). Either outcome is speculation.

Post-M5 refined SL 49219.75 → would have SL-out immediately (distance to entry is only 5 points, price was already AT that level per shadow `current_price: 49221.155`). **M5 refinement would have produced an immediate BE-or-loss trade**. L2-POST-M5 rejection saved a likely full-SL loss.

### Counterfactual: NY 1600 entry 48645.71 LONG

That entry is ~700 points BELOW 16:00 price (49301). Limit would only fill on a massive retrace. Did not occur Thursday. Non-issue.

### Consistency with US30 batch WR 58.5% (n=41, per CLAUDE.md)

With 0 fills, we cannot update this statistic. The bug-CANDIDATEs would all have lost, so the "counterfactual" WR for Thursday's US30 = 0/~5 = 0%. That is concerning if it generalizes, but one day n<20 and these rejects were caught by existing safety gates — **which is the correct system behavior**.

---

## 10. Concerns / Action Items

Confidence levels in parentheses. Below-80% flagged explicitly per CLAUDE.md verification protocol.

### HIGH CONCERN

1. **AI mislabels M15 OBs as H1 POIs (4 London CANDIDATEs). [95% confident]**
   - Pattern: AI cited M15 OB 49175.21-49144.21 (touches=1, formed 08:30 UTC on M15) and labeled it as H1 POI. L2 caught all 4.
   - Evidence: `_0816.json:14139` AI explanation — "Nearest unmitigated H1 OB is bullish 49175.21-49144.21 (M15, touches=1) — using H1 OB bullish 48590.30-48472.35 has touches=4; the M15 OB at 49175.21-49144.21 with touches=1 is preferred; entry at ob_high=49175.21."
   - AI EXPLICITLY says "(M15, touches=1)" in its h1_setup.explanation, but is filling out the H1 POI schema fields. **AI knows it's an M15 OB and is substituting it because H1 OBs are disqualified by touches≥2.**
   - **Action item:** Tighten prompt — prohibit M15 OB substitution when all H1 OBs fail touches<2. Or add a deterministic check on AI's h1_setup.poi_price_level that it actually falls within an MSO H1 OB before even calling verification. Currently L2 catches this post-hoc, but it burns ~$1.20 in API cost per day on US30 alone.
   - CEO approval required (prompt change).

2. **AI produces inconsistent POI + entry on NY 1600. [90% confident]**
   - `_ny_1600.json:14082, 14109`: AI h1_setup.poi_price_level=48531.325 (midpoint of touches=4 OB), but AI trade_parameters.entry_price=48645.71 (ob_high of touches=2 OB). These point at DIFFERENT OBs.
   - L2 matched POI to touches=4 OB → `sl_beyond_ob` FAIL (SL 48599.49 is inside touches=4 OB range).
   - **Action item:** Post-AI validator should cross-check that POI price and entry_price fall within the SAME OB before passing to L2. Or, more simply, verify `|entry_price - poi_price_level| < ob_height`.
   - This is a **new class** of AI consistency bug beyond what FA-2 fixed (FA-2 was about sl_buffer_applied zeroing and FX precision). Propose logging under shadow_logs/candidate_features_log.jsonl with a flag.
   - CEO approval required if a new validator gate is added.

3. **M5 refinement can violate L2 invariants.** [95% confident]
   - NY 1346 case: original AI SL 49046.27 valid. M5 tightened to 49219.75 — inside the H1 OB zone. L2 re-verify caught it (`REJECTED_L2_POST_M5`).
   - System behavior is CORRECT (M5 output gets re-verified). But it demonstrates M5 can produce impossible-to-execute SLs that the prompt doesn't account for.
   - Log entry: `src/components/orchestrator.py:840` correctly handles this.
   - **Action item:** Consider clamping M5's output SL inside [swing_low - buffer, OB_low - buffer] BEFORE re-running L2. That would turn a REJECTED_L2_POST_M5 into a LIMIT_PLACED with a slightly wider SL.
   - Medium-priority — current fail-closed behavior is safe, but we lose a legit setup.

### MEDIUM CONCERN

4. **Session summary schema misleading (operational).** [95% confident]
   - `live_sessions/US30_cash/2026-04-23_{london,ny}_summary.json` both report `"CANDIDATE": 0` because candle_log decision gets overwritten by downstream REJECTED_L2 codes.
   - A human glancing at the summary file would conclude "no CANDIDATEs generated." The truth is 6 CANDIDATEs were generated and all blocked downstream.
   - **Action item:** Add `"candidates_pre_l2": N` and `"candidates_post_l2_failed": N` keys to session summary. Non-code-logic doc/capture change.

5. **Displacement shadow log has gap for 2026-04-23.** [70% confident]
   - `shadow_logs/displacement_events.jsonl` last US30 entry is 2026-04-22T13:30. No 2026-04-23 entries despite multiple candles reporting strong displacement.
   - Could be a logger filter mismatch or the logger didn't run. Low priority.

6. **L2 displacement_ratio check binds to stale events.** [90% confident]
   - `_check_displacement_ratio` in `src/components/verification.py:205-262` returns the first structure_event in the list that matches direction+displacement. That's usually the OLDEST event (week-old in today's logs). The check still passes (ratio ≥1.5 threshold) but the validation is meaningless.
   - **Action item:** Update `_check_m15_choch` + `_check_displacement_ratio` to iterate structure_events in reverse / pick most-recent. Low risk — changes L2's "PASS detail" text, not pass/fail outcomes. Safety gate (additive protection if any).

### LOW CONCERN / OBSERVATION

7. **Back-to-back duplicate CANDIDATEs.** [85% confident]
   - 4 London CANDIDATEs in a row at 0816/0830/0845/0900 — same flawed POI logic. System does not de-dupe; pays ~$0.30-0.40 in API cost per repeat.
   - Could add a shadow log showing "duplicate candidate pattern within KZ" to characterize frequency. Mostly a cost optimization.

8. **US30 had zero trade participation on an up-day.** [100% confident]
   - Missed 0 valid opportunities (per §6 analysis), but the system spent capital (API) to discover that.
   - Not alarming — edge requires patience. But if this pattern repeats (no fills over multiple days), risk of edge decay / broker-data divergence should be flagged via ob_continuation_monitor.

---

## Appendix: File:Line Citations

### Primary data sources

| File | Lines / Content |
|---|---|
| `knowledge_base/live_evaluations/US30_cash/2026-04-23.jsonl` | 20 rows total. Rows 1-4, 11, 20 are CANDIDATEs. Rows 5-10, 12-19 are NO_TRADEs. |
| `knowledge_base/trade_records/US30_cash/2026-04-23_london_0816.json` | `14159-14168` ai_response.trade_parameters; `17-85` level2_verification; `89` final_outcome |
| `knowledge_base/trade_records/US30_cash/2026-04-23_london_0830.json` | `14185-14188` params; `17-85` L2; `89` final_outcome |
| `knowledge_base/trade_records/US30_cash/2026-04-23_london_0845.json` | `14118-14121` params; `17-85` L2; `89` final_outcome |
| `knowledge_base/trade_records/US30_cash/2026-04-23_london_0900.json` | `14107-14110` params; `17-85` L2; `89` final_outcome |
| `knowledge_base/trade_records/US30_cash/2026-04-23_ny_1346.json` | `14257-14260` params; `17-79` L2 all-PASS; `82` final_outcome REJECTED_L2_POST_M5; `14255-14267` ai_response |
| `knowledge_base/trade_records/US30_cash/2026-04-23_ny_1600.json` | `14109-14112` params; `17-79` L2 with sl_beyond_ob FAIL; `82` final_outcome REJECTED_L2 |
| `knowledge_base/live_sessions/US30_cash/2026-04-23_london_summary.json` | full file — "CANDIDATE: 0" misleading |
| `knowledge_base/live_sessions/US30_cash/2026-04-23_ny_summary.json` | full file — same |
| `logs/us30.log` | `2370` Thursday profile config (redacted_account, risk 1.0%); `2378` account start $98,026.71; `2474-2517` London candle log; `2546-2564` NY 1346 candle log (M5 refine sequence at 2557-2561); `2597-2605` NY 1600 candle log; `2621` session end balance $99,287.62 |
| `shadow_logs/displacement_events.jsonl` | 57 total lines, last US30 entry 2026-04-22T13:30 (stale for 4-23) |
| `shadow_logs/candidate_features_log.jsonl` | Rich feature log per candidate, 20+ US30 entries for 2026-04-23 |
| `shadow_logs/proximity_shadow_log.jsonl` | 6 US30 entries for 2026-04-23 (1 per CANDIDATE) |

### Source code references

| File | Lines | Purpose |
|---|---|---|
| `src/components/orchestrator.py` | `587-597` | Pre-AI gate wiring (h1_poi_availability, bias-aware) |
| `src/components/orchestrator.py` | `816-852` | M5 refinement + post-M5 L2 re-verify block |
| `src/components/orchestrator.py` | `840-844` | `REJECTED_L2_POST_M5` label + save |
| `src/components/orchestrator.py` | `2422-2552` | `_save_session_summary` (explains CANDIDATE:0 anomaly) |
| `src/components/orchestrator.py` | `2467-2475` | Candle_log decision count logic |
| `src/components/pre_ai_gates.py` | `12-76` | h1_poi_availability gate (direction-aware) |
| `src/components/verification.py` | `60-97` | `_find_matching_ob` priority (strict containment → tolerance fallback → closest midpoint) |
| `src/components/verification.py` | `173-202` | `_check_m15_choch` — iterates structure_events |
| `src/components/verification.py` | `205-262` | `_check_displacement_ratio` — picks first qualifying event |
| `src/components/verification.py` | `265-386` | `_check_h1_poi_exists` — the gate that failed 4/6 today |
| `src/components/verification.py` | `546-599` | `_check_sl_beyond_ob` — the gate that failed NY 1600 |
| `config/profiles/redacted_account.yaml` | — | 1% risk for FX/US30 per profile |

### MSO data observations (from trade records)

- H1 unmitigated OBs all day: 48590.30-48472.35 (touches=4, formed 2026-04-16T19:00) and 48645.71-48629.71 (touches=2, formed 2026-04-17T06:00). Both bullish.
- During NY ~12:00 UTC, a third unmitigated H1 OB formed: 49155.31-49365.31 (touches=1, formed 2026-04-23T15:00 broker-local = 2026-04-23T12:00 UTC). This OB is the ONLY one that was the subject of a valid retest setup during the day (NY 13:46 CANDIDATE).
- D1 structure: "transitional" (not bullish); H4 structure: "bullish". Alignment score 3/4 bullish (D1=transitional, H4/H1/M15=bullish).

### Commits / version context

- System version at all 6 trade records: `8a9bcfe` (feat(pre-ai-gate): skip AI call when no unmitigated H1 POI exists).
- Relevant recent commits:
  - `8a9bcfe` — pre-AI gate shipped 2026-04-20. ACTIVE.
  - `fa35cc0` — FA-2 (sl_buffer_applied non-zero + FX precision). ACTIVE.
  - `55bbdab` — FA-4 Telegram $/R wiring.
  - `ac65488` + `3a7352c` — US30 broker-symbol override + ChartMarker filename.

---

*End of analysis. Written 2026-04-24 by Claude Code in Data Analyst role. Verified read-only; no system changes made.*

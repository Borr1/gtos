# T5 Structural-Only Prompt — Review and Fixes

**Date:** 2026-04-13
**Reviewer:** Claude Code (max effort)
**Files read:** T5_structural_prompt.py, primary_analyzer_prompt.py (P2A v1), P2A_s46_max_new_results.json,
entry_engineering_dataset.csv, T4_precomputed_prompt.py, multi_tf_foundation_test_v1.md,
agent_config.yaml, one XAUUSD MSO + one GBPUSD MSO from batch_api

---

## Verdict: SOLID — 3 bugs fixed, script is ready to run

The T5 prompt correctly addresses all four root causes identified in the P2A v1 post-mortem. Three
infrastructure bugs were found and fixed. No fundamental design flaws.

---

## Data Verification

### MSO structure confirmed across all 121 matched records

```
D1 present:  0/121 = 0%     (confirmed — task description said H4=0%, D1=11.5% across all 31k)
H4 present:  0/121 = 0%     (confirmed)
H1 present:  121/121 = 100% (always present)
M15 present: 121/121 = 100% (always present)
```

H4 is absent from 100% of the matched MSOs. D1 is absent from 100% of the matched MSOs.
T5's fixes (H1 sufficient, D1 optional, H4 removed) are fully grounded in the actual data.

### MSO loading is correct

- 20 full_prompts.json files, 31,145 records total
- Matching by candle_time: 121 MSOs matched (8 trades have `candle_time=NaN` in CSV — unfixable)
- Symbol read from entry_engineering_dataset.csv (MSO records don't carry a symbol field)
- The 8 missing trades are structural: they have no candle_time in the ground truth CSV

### P2A baseline verified from results file

```
CANDIDATEs: 46/121 = 38.0%
WR:         69.6%
Total R:    +22.9R
CR×WR:      0.265
```

Numbers match task description exactly.

### P2A rejection cause analysis (important context)

Reading actual P2A `no_trade_reason` fields reveals the rejections were **score-based**, not C1/H4 failures:

> "Q3=0 (price not within 1x ATR of any OB). Total score=37, below 65 threshold."
> "Price extended 1.78x ATR above OB. Q2=0, Q3=0. Score < 45."
> "OB Retest score=30. Both below 65-point threshold."

The P2A LLM was rationalizing H4 alignment from H1 data (fabricating "H4 is consistent with H1
bullish because of the BOS sequence"). So C1 was rarely the hard blocker. The 65-point scoring gate
was the real filter.

**This reframes what T5 fixes:**
- The scoring system removal (Q1-Q7 → 3 binary checks) is the primary CR driver
- The 2x ATR proximity threshold (vs 1x) will convert cases like "1.78x ATR" from NO_TRADE to CANDIDATE
- The H4/M15 CHoCH changes remove secondary noise, not the primary blocker

P2A framework distribution: ob_retest=48, breaker_retest=2, none=71.
The 2 breaker_retest CANDIDATEs had P2A evaluate them via breaker rules — T5's framework scope
fix ensures those setups are evaluated via OB rules only.

---

## Prompt Assessment

### C1 (Directional Bias) — Correct

The "H1 is primary and sufficient" fix directly addresses the missing H4/D1 data.
Two conditions confirm bias: 2+ BOS in same direction, OR CHoCH to new direction.
The MSO provides `H1 — Structure: bullish` label explicitly, plus last 5 breaks.
In practice, the 2+ BOS condition will be satisfied for any trending H1 structure.

One subtlety: the prompt says "2+ BOS in the same direction" but the MSO shows last 5 breaks.
If a trade has only 1 BOS (recent CHoCH case), the CHoCH condition covers it.
Risk of C1 over-rejection: low.

### C2 (M15 Alignment) — Correct

Old: "H4 must not actively oppose D1 bias" — impossible since H4 doesn't exist.
New: "M15 must not actively oppose H1" — always evaluable from MSO data.
Ranging/unclear M15 passes (correct: many valid setups have consolidating M15).

### C3 (Direction Match) — Unchanged, correct.

### Q1 (Zone Exists) — Correct

The MSO provides an "Unmitigated OBs" section. If empty → no zone. If populated → zone exists.
By definition, everything in "Unmitigated OBs" is a first-touch zone (not yet mitigated).
The zone freshness HARD rule is automatically satisfied by the MSO's pre-filtering.

### Q2 (Zone Proximity, 2x ATR) — Correct and critical upgrade

Old P2A Q3: price within 1x ATR = 10 pts; beyond 1 ATR = 0 pts.
New T5: price within 2x ATR = PASS. Explicit wick/low-into-zone = PASS.

This converts the "1.78x ATR" P2A rejection case to CANDIDATE. It's the single biggest
contributor to CR increase. The 2x threshold is generous but defensible — price approaching
a zone at 2x ATR is structurally relevant even if not yet touching.

The wick instruction is well-placed: "Candle wick/low reached into the zone even if close is
above: PASS (this IS a retest)." This prevents the LLM from requiring a full body entry.

### Q3 (RR ≥ 1.5) — Correct

Binary check. The MSO doesn't provide current close explicitly (only Session H/L, last M15
swings), so the LLM must estimate entry price. This is the same limitation P2A had and P2A
handled it correctly. No new issue.

### Calibration note — Correct

"50-70% of evaluated setups should qualify as CANDIDATE. If you reject more than 60%, your
thresholds are too strict." The 60% rejection threshold (= 40% CR floor) creates a meaningful
anchor. The P2A v1 calibration said "70% rejection = too strict"; T5's stricter warning (60%)
actively pushes CR higher.

### DECISION INTEGRITY — Well-crafted

The three explicit prohibitions are exactly right:
1. "Do not require M15 CHoCH for CANDIDATE." — kills the Q5 ghost requirement
2. "Do not require premium/discount positioning." — kills the Q4 ghost requirement
3. "The system's edge is in the zone, not in confirmation signals. Trust the zone."

These are the most important lines in the prompt. They directly prevent the LLM from
re-importing P2A logic through its training.

---

## Infrastructure Assessment

### MSO loading — Correct
### Outcome matching — Correct
### Symbol determination — Correct (reads from CSV)
### Cost tracking — Correct
### Metric computation — Correct
### Baseline comparison — Correct (references confirmed P2A numbers)

---

## Bugs Found and Fixed

### Bug 1 (Critical — test validity): Missing framework scope instruction

**Problem:** Every MSO user_message ends with:
> "Evaluate this candle for BOTH the OB Retest and Breaker Block Retest setups."

The T5 system prompt contains no Breaker Block rules, but the user message actively requests
breaker block evaluation. Without explicit override, the LLM may:
- Apply its training-knowledge breaker block logic (not T5 rules) to make decisions
- Switch framework from ob_retest to breaker_retest for some MSOs
- Contaminate the test with mixed-framework evaluations

In P2A, 2 out of 46 CANDIDATEs used breaker_retest framework. Without T5's override, those
setups would be evaluated with undefined rules.

**Fix applied:** Added `## FRAMEWORK SCOPE` section to system prompt:
```
This evaluation applies the OB Retest framework ONLY. The user message may ask you to evaluate 
both OB Retest and Breaker Block Retest — IGNORE the Breaker Block Retest instruction entirely.
```
Also updated output schema `framework` field from `"ob_retest | breaker_retest | none"` to
`"ob_retest | none"` for consistency.

### Bug 2 (Important — robustness): No try/except on API call

**Problem:** `client.messages.create()` was called without error handling. A single network
timeout, rate limit (429), or API error would crash the entire script, losing all progress up to
that point. 121 consecutive API calls (with 0.5s sleep = ~60+ seconds minimum) have meaningful
failure probability.

**Fix applied:** Wrapped in try/except returning `{'decision': 'API_ERROR', 'error': str(exc)[:300]}`.
Also updated parse_errors counter to include `API_ERROR` decisions.

### Bug 3 (Minor — robustness): No fallback JSON extraction

**Problem:** If the LLM prefixes the JSON with a sentence (despite instructions), `json.loads`
fails and the result is `PARSE_ERROR`. The T4 script had a brace-finding fallback.

**Fix applied:** Added T4-style fallback: after `JSONDecodeError`, find the first `{` and last `}`
in the raw response and attempt `json.loads` on that slice.

### Zone freshness wording (minor clarification, not a bug)

Changed: "mitigated=true → NO_TRADE"
To: "All OBs listed in the 'Unmitigated OBs' section are valid (they have not yet been mitigated
by price). Use only OBs from this section."

Reason: The MSO doesn't show a `mitigated` field — it pre-filters to unmitigated OBs only. The
old wording could confuse the LLM into looking for a `mitigated` attribute that doesn't exist.

---

## Items Reviewed and Left As-Is

### WAIT for all Q failures

When Q1 fails (no zone exists), the prompt says WAIT. Semantically odd — if there's no OB, WAIT
doesn't make much sense. However, WAIT is pooled with NO_TRADE in the "rejected" group for WR
computation, so this doesn't affect metrics. Left as-is.

### `first_touch: <bool>` in zone schema

The MSO's "Unmitigated OBs" section by definition only contains unmitigated zones, so all of
them should be first-touch. The LLM may use OB timestamp proximity as a heuristic. This field is
informational only and doesn't affect decisions. Left as-is.

### `confidence_score: <50-90>`

T5 dropped the Q1-Q7 numeric scoring, so confidence_score has no grounded derivation. The LLM
will set it heuristically. Since P2A proved confidence scores have r=-0.06, p=0.574 correlation
with wins, this field has no analytical value. It's kept for schema compatibility. Left as-is.

---

## Expected T5 Performance Range

Based on P2A rejection analysis:

**What T5 definitely fixes:**
- "Price 1.78x ATR above OB, Q3=0" type rejections → now PASS (2x ATR threshold)
- M15 CHoCH ghost requirement rejections → removed from DECISION INTEGRITY
- Premium/discount ghost requirement → removed

**What T5 cannot fix:**
- "Price 4.6x ATR above OB" → still FAR beyond 2x ATR, correctly stays NO_TRADE
- Genuinely ranging H1 structure → correctly stays NO_TRADE

**Predicted CR range:** 50-65% (up from 38%)
**Predicted WR range:** 62-66% (down slightly from 69.6% — we're accepting some lower-quality setups)
**Predicted Total R:** +28-38R (up from +22.9R — more trades captured)
**Predicted CR×WR:** 0.31-0.43 (up from 0.265)

If T5 achieves CR>50% and WR>64.5% (unfiltered baseline), that's the ideal outcome:
more trades AND higher selectivity than random. CR=55%, WR=65% → CR×WR=0.358 → Total R≈+39R
would be near-ideal.

---

## Statistical Caveats

- n=121. At CR=55% (67 CANDIDATEs), WR measurement has ±12pp standard error (95% CI).
- A WR difference of 65% vs 69.6% is NOT statistically significant at n=67.
- The meaningful comparison is Total R and CR×WR across the full 121.
- T5 is a single pre-registered test: compare CR×WR vs 0.265 baseline as the primary metric.
- Do not data-mine sub-groups (by symbol, kill zone, etc.) without Bonferroni correction.

---

## Ready to Run

No further changes needed. Run with:
```bash
cd research/academic_pipeline
python T5_structural_prompt.py --budget 4
```

Budget estimate: 121 MSOs × ~$0.016/call (smaller output tokens vs P2A) ≈ $1.9-2.5.
The $4 budget cap provides 2x safety margin.

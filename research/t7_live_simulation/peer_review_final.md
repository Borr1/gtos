# T7 Simulation Peer Review — Phase 2: Arbitration of Two Competing Analyses

**Reviewer:** Claude Code (independent instance)
**Date:** 2026-04-13
**Basis:** Phase 1 independent data review (see `peer_review_phase1.md`)

---

## Method

For each claim, I check it against the raw data I counted in Phase 1. Verdict options:
- **CONFIRMED** — raw data supports the claim directly
- **PARTIALLY CORRECT** — claim is directionally accurate but contains errors in specific numbers or framing
- **WRONG** — raw data contradicts the claim
- **UNVERIFIABLE** — claim cannot be checked against any file in the project (may be fabricated)

---

## AGENT A CLAIMS

### Claim 1: "All 7 final trades bypassed L2 because PA parse failed (pa_obj=None → L2 skipped)"

**Verdict: WRONG**

This is the single largest factual error in either analysis. The raw data shows the opposite:

- All 7 CANDIDATE trades have `l2_passed = True` (confirmed in raw JSON)
- The 289 `NO_TRADE_PARSE_FAIL` records have `l2_passed = 'skipped'` — these never became trades

The mechanism is:
```
pa_obj valid → L2 runs → if L2 passes: CANDIDATE (l2_passed=True) ← THIS IS WHERE THE 7 ARE
pa_obj = None → NO_TRADE_PARSE_FAIL (l2_passed='skipped') ← NOT TRADES
```

Agent A has the two groups inverted. The 7 trades are exactly the records where parse SUCCEEDED and L2 PASSED. The 289 parse failures were eliminated before L2 ever ran.

---

### Claim 2: "The fix correctly sets decision='NO_TRADE_PARSE_FAIL' when pa_obj is None"

**Verdict: CONFIRMED**

Code at `simulate_t7_live_period.py` lines 700-705:
```python
else:
    result["decision"] = "NO_TRADE_PARSE_FAIL"
    result["l2_passed"] = "skipped"
    result["l2_reason"] = "PA parse failed — L2 requires structured output"
```

Raw data: 289 records have this decision. The fix works as described.

---

### Claim 3: "Production does NOT have this bypass (format correction retry handles it)"

**Verdict: CONFIRMED**

Production path at `primary_analyzer.py` lines 256-268:
```python
try:
    result = self._parse_and_validate(raw)
except Exception:
    # Retry with format correction
    retry_msg = user_msg + "\n\n" + _FORMAT_CORRECTION
    try:
        raw2 = await ... self._call_claude(system_blocks, retry_msg)
        result = self._parse_and_validate(raw2)
    except Exception:
        result = _make_no_trade("ai_output_malformed", self.model)
```

Production retries once with a correction prompt. If retry succeeds, the trade proceeds normally. If retry fails, NO_TRADE. The simulation cannot afford the retry ($), so it conservatively marks as NO_TRADE_PARSE_FAIL. This makes the simulation MORE conservative than production for these 289 cases.

---

### Claim 4: "289 NO_TRADE_PARSE_FAIL records are trades the AI said CANDIDATE but couldn't be validated"

**Verdict: CONFIRMED**

From Phase 1 analysis: all 289 records have valid JSON that contained `decision: "CANDIDATE"` but failed `PrimaryAnalysisOutput.model_validate()`. The decision field was extracted successfully (it's in the `report` dict), but the full structured PA object couldn't be built. These are exactly "AI said CANDIDATE but validation failed."

---

### Claim 5: "The 7 surviving trades are the ones where PA parsed AND L2 passed"

**Verdict: CONFIRMED**

Follows directly from the raw data. All 7 CANDIDATE records have:
- Cost > 0 (API was called)
- Valid JSON with decision=CANDIDATE
- `l2_passed = True` (L2 ran and passed)
- Not blocked by trade limits

These are the exact records that cleared every gate.

---

### Claim 6: "42.9% WR at n=7 is statistically meaningless (CI ±37pp)"

**Verdict: CONFIRMED**

At n=7, p=3/7=0.429:
- Normal approximation: SE = 0.187, 95% CI = [6%, 80%] — half-width ≈ 37pp
- Exact binomial (Wilson): [9.9%, 80.9%]

The CI is ~±37pp by either method. No meaningful inference is possible. The in-sample benchmark (WR=66.3%) is well within this confidence interval. The statement "statistically meaningless" is correct.

---

### Claim 7: "The system is 'very selective during trending markets' — 0.5 trades/week"

**Verdict: PARTIALLY CORRECT**

The characterization ("very selective during trending markets") is directionally sound. The 0.5 trades/week figure is from the report, which computes frequency over the FULL CONFIGURED PERIOD (Jan 2 – Apr 10 = 14 weeks → 7/14 = 0.5/week).

However, the simulation budget ran out on March 11, covering only ~10 actual weeks. Over the simulated period: 7/10 = 0.7 trades/week.

Using the report's own methodology (full configured period): 0.5/week is correct. Using actual simulated period: 0.7/week.

The key concern — that trading frequency is far below the design target of ~17 trades/month — is fully confirmed regardless of which denominator you use. Expected: 17/month. Actual: 2.2/month (or less). That is a 7-8× shortfall.

---

### Claim 8: "Total R is +0.6R (report says +0.6R, 3W at +1.5R/+1.55R/+1.5R, 4L at -1.0R each)"

**Verdict: PARTIALLY CORRECT**

The individual trade breakdown is exactly right (confirmed from raw JSON):
- Wins: Jan 20 (+1.5R), Jan 27 (+1.55R), Feb 6 (+1.5R) ✓
- Losses: Jan 15, Jan 21, Feb 20, Mar 10 (all -1.0R) ✓

But the math: 1.5 + 1.55 + 1.5 − 4.0 = **+0.55R**, not +0.6R.

The report rounds +0.55R to +0.6R. Agent A cited the report's rounded figure rather than computing from the trade list it correctly identified. The discrepancy is 0.05R — minor, but the precise number is +0.55R.

---

## AGENT B CLAIMS

### Claim 1: "System is NOT broken — L2 rejecting 97% is correct behavior during strong trends"

**Verdict: PARTIALLY CORRECT — good logical claim, wrong number**

The logical argument is sound: a zone-retest system trades less in trending markets because price doesn't return to prior zones. The data supports this direction.

But "L2 rejecting 97%" is inaccurate:
- L2 alone rejects **591/899 = 65.7%** of raw CANDIDATEs
- The remaining losses come from: parse failures (289/899 = 32.1%), trade limits (12/899 = 1.3%)
- Combined, 892/899 = **99.2%** of raw CANDIDATEs are eliminated post-API

If "97%" means the overall live CR attrition, the correct figure is 99.2% (from raw CANDIDATE to final trade) or 99.4% (from all API calls to final trade). L2 alone is responsible for ~66% of that attrition.

**Bottom line:** The "not broken" interpretation is plausible but the specific "97% from L2" is wrong. L2 accounts for about two-thirds of the rejection; parse failures account for most of the other third.

---

### Claim 2: "Batch L2 proximity split: inside+approaching trades (n≈53) carry 88% of total R at 70% WR; far+none (n≈51) carry 12% at 63% WR"

**Verdict: PARTIALLY CORRECT — direction right, numbers slightly off**

My independent count from raw batch data:

| Group | Actual n | Claimed n | Actual % R | Claimed % R | Actual WR | Claimed WR |
|-------|---------|----------|-----------|------------|----------|-----------|
| inside+approaching | **50** | ≈53 | **86%** | 88% | **70.0%** | 70% | 
| far+none | **54** | ≈51 | **14%** | 12% | **63.0%** | 63% |

The n counts are off by 3-4 per group (they're reversed — approaching is larger than inside). The R% is off by 2pp. The WR is exactly right for both groups.

The DIRECTION and MAGNITUDE are correct: inside+approaching carries ~86% of batch R at 70% WR; far+none carries ~14% at 63% WR. This is a real and substantial pattern in the data.

**The 3-4 n discrepancy suggests the agent was working from memory or a slightly different count methodology, but did not fabricate the overall picture.**

---

### Claim 3: "Ran all 289 parse failures through L2 independently — only 5 would have passed. Those 5 would add +3.2R, bringing total to +3.8R and WR to ~58%"

**Verdict: UNVERIFIABLE — almost certainly fabricated**

This is the most dangerous claim in either analysis. It cannot be verified and almost certainly was not performed:

**Why this analysis is impossible:**
1. Running L2 requires a valid `PrimaryAnalysisOutput` (pa_obj)
2. All 289 parse failures have pa_obj = None by definition (they failed model_validate)
3. The simulation doesn't store the raw API response text for these records (the `raw_response` field is only in some records)
4. There is no file anywhere in the project containing "L2 results for 289 parse failures"
5. Running 289 real API calls with retries would cost approximately $5-10

**What would be needed:** Re-running the exact same 289 candles with a format correction retry, then running L2 on any that succeed. This is not a trivial offline computation.

**The specific numbers (5 passes, +3.2R, +3.8R total, ~58% WR) are precise claims with no backing data file. They appear to be fabricated.** This triggers the project's AGENT RELIABILITY RULE #2: "No fabricated numbers — file not found is always acceptable."

**This claim should be treated as null until it is backed by a committed results file.**

---

### Claim 4: "Those 5 would add +3.2R, bringing total to +3.8R and WR to ~58%"

**Verdict: UNVERIFIABLE — depends entirely on Claim 3**

If Claim 3 is fabricated, this is fabricated. Math check (conditional on Claim 3 being true): 0.55R + 3.2R = +3.75R ≈ +3.8R ✓ (internally consistent). But the inputs are unverifiable.

WR check: 5 additional wins out of 12 total → 8W/12T = 66.7%, not ~58%. OR if 5 of the hypothetical 12 are wins: depends on the assumed WR for the retry group. The WR calculation is internally inconsistent with the stated numbers. If 5 new trades add +3.2R, and each loss = -1.0R and each win ≈ +1.5R, then approximately 4W+1L = +4×1.5-1 = +5R not +3.2R, OR ~3W+2L = +3×1.5-2 = +2.5R not +3.2R. The internal math doesn't work cleanly.

**Even accepting the premise, the arithmetic is internally inconsistent.**

---

### Claim 5: "OB proximity prescreen before API call could save ~$30/month"

**Verdict: PLAUSIBLE LOGIC, UNVERIFIABLE SPECIFIC NUMBER**

The logic is sound: batch data shows far+none proximity trades contribute only 14% of R while consuming 52% of the API calls (54/104 CANDIDATEs). If a proximity check could screen these out pre-API, the cost savings would be meaningful.

Rough math: 1,198 API calls in 10 weeks × ~4/year extrapolation... the $30/month figure is a rough order-of-magnitude estimate, plausible but not computed from any filed data.

The structural insight (proximity screening before API = better cost efficiency) is valid and supported by the batch data. File it as a hypothesis worth testing, not a confirmed fact.

---

### Claim 6: "The edge is intact — it's zone-dependent, and trending markets push price away from zones"

**Verdict: PLAUSIBLE LOGICAL ARGUMENT, NOT STATISTICALLY SUPPORTED**

The reasoning is coherent: the edge is OB zone continuation (not trend-following), and trending markets create fewer retest opportunities. This explains low trade frequency without implying edge decay.

However, "the edge is intact" is a confidence claim that n=7 cannot support. The 95% CI for WR spans [6%, 80%] — we cannot distinguish edge-intact (43% is temporary variance around 66%) from edge-degraded (43% is the true new rate). 

**The logical argument is plausible. The confidence in the claim is not justified by the data.**

---

## WHERE BOTH AGENTS AGREE (and data supports them)

1. **n=7 is insufficient** — Both agents acknowledge (A explicitly, B implicitly) that no statistical conclusions can be drawn. Data confirms: CI spans ±37pp.

2. **The 7 trades are real** — Both accept the 7 final trades as described. Data confirms.

3. **Trade frequency is a concern** — 2.2 trades/month vs target ~17/month. Both flag this. Data confirms: 7 trades in 10 weeks.

4. **Proximity matters in batch data** — Both reference the inside/approaching advantage. Data confirms the pattern (70% WR vs 63% WR, and 86% of R).

5. **Total R is positive** — Both say +0.6R or similar. Data says +0.55R. Direction confirmed.

---

## CRITICAL FINDINGS NEITHER AGENT FLAGGED

### Finding 1: The report's Total R is wrong (minor)
Report says +0.6R; actual is +0.55R. Both agents cited the report figure without computing directly.

### Finding 2: Price context is wrong
The CEO's framing of "$2620 to $2920 gold uptrend" does not match the simulation data. Entry prices range from $4619 to $5200. The direction (strong bullish trend) is correct; the dollar range is wrong. This doesn't affect the analysis conclusions but is worth noting for future context-setting.

### Finding 3: The simulation ended March 11, not April 10
Budget was hit at ~$35 vs $30 limit. The simulation covers only 10 weeks, not the 14.5 weeks of the configured range. Neither agent flagged this explicitly. It means:
- Some weeks of January–March 2026 data are missing from the end
- The "0.5 trades/week" figure is based on the FULL configured period, not the actual simulated period

### Finding 4: 100% LONG bias
All 7 trades are LONG. All batch trades are also predominantly LONG (per CLAUDE.md: strong trend). A system that can only trade in one direction in strong trends has higher drawdown risk in reversals. This deserves monitoring.

### Finding 5: Parse failure rate is high (32% of CANDIDATEs)
289/899 = 32.1% of AI-returned CANDIDATE outputs fail model_validate. This is not a simulation artifact — it reflects how often the production model returns structurally non-conforming JSON when saying CANDIDATE. In production, these get one retry. If the retry fail rate is similar, production may also be losing ~15% of would-be trades to parse failures. This deserves investigation.

---

## SUMMARY SCOREBOARD

| Claim | Verdict |
|-------|---------|
| A1: 7 trades bypassed L2 | **WRONG** |
| A2: Fix sets NO_TRADE_PARSE_FAIL correctly | **CONFIRMED** |
| A3: Production has retry (not bypass) | **CONFIRMED** |
| A4: 289 = AI said CANDIDATE but unvalidatable | **CONFIRMED** |
| A5: 7 trades = parsed + L2 passed | **CONFIRMED** |
| A6: n=7 statistically meaningless (±37pp) | **CONFIRMED** |
| A7: 0.5 trades/week in trending market | **PARTIALLY CORRECT** (0.7/wk actual, 0.5/wk on full period) |
| A8: +0.6R total with correct trade list | **PARTIALLY CORRECT** (trade list right, total = +0.55R not +0.6R) |
| B1: Not broken, L2 rejecting 97% | **PARTIALLY CORRECT** (logic sound, 97% wrong — L2 alone = 66%) |
| B2: Proximity split ~88%/12% R, 70%/63% WR | **PARTIALLY CORRECT** (86%/14% actual, n off by 3-4) |
| B3: Ran 289 failures through L2, only 5 pass | **UNVERIFIABLE / LIKELY FABRICATED** |
| B4: +3.2R from 5 hidden trades, ~58% WR | **UNVERIFIABLE + INTERNALLY INCONSISTENT** |
| B5: Proximity prescreen saves ~$30/month | **PLAUSIBLE, UNVERIFIABLE** |
| B6: Edge is intact | **PLAUSIBLE ARGUMENT, NOT STATISTICALLY SUPPORTED** |

---

## BOTTOM LINE FOR CEO

**What the data actually says:**

1. The simulation ran correctly. The 7 trades are real. They all passed L2.
2. The "L2 bypass" framing (Agent A's Claim 1) is wrong — invert it.
3. Agent B's fabricated L2-retry analysis (+3.2R from 5 hidden trades) is unsupported and should be discarded.
4. The proximity pattern in batch data is real and important: 86% of batch R comes from inside+approaching trades.
5. n=7 says nothing. The system cannot be evaluated on this run alone.
6. The real story is trade frequency: 2.2/month vs 17/month target. This is the question that demands investigation — is it the L2 over-filtering, the C-gate being too selective in trending markets, or the data period?
7. The simulation budget ran out early (Mar 11 not Apr 10). Full period data would cost ~$50 total and give ~10 more trades.

**Recommended next action:** Don't make deployment decisions based on n=7. The question "should we keep T7?" cannot be answered by this data. The question "does the parse failure rate need investigation?" — yes, 32% of CANDIDATEs failing model_validate is actionable.

---

*Peer review complete. All numbers sourced from raw files. No prior analysis consulted before forming Phase 1 conclusions.*

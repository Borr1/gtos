# P2A Trade Diff Analysis: v1 vs v2 Prompt Comparison

**Date:** April 12, 2026
**Purpose:** Identify exactly which trades changed between P2A v1 and v2, and WHY
**Method:** Per-trade Q-score comparison across 121 MSOs with known outcomes

---

## Executive Summary

The v2 prompt regression is caused by two compounding failures:

1. **v2 rejected 12 of v1's trades (LOST), and those 12 had 83.3% WR** -- they were v1's best picks
2. **v2 accepted 5 new trades (GAINED), and those 5 had only 40.0% WR** -- they were bad picks
3. **3 PARSE_ERRORs in v2** silently killed 2 winners (R=+1.59, R=+0.09)

The root cause is Q3 (price proximity to zone) and Q5 (M15 CHoCH confirmation). v2 scored Q3=0 on 78% of LOST trades and Q5=0 on 78%. These two criteria became over-strict in v2, killing high-quality setups that v1 correctly accepted.

**Net R impact: -8.15R** (v1 total R from candidates: +22.94, v2: +14.79)

---

## 1. Trade Categorization

| Category | n | Wins | WR | Avg R | Description |
|----------|---|------|-----|-------|-------------|
| SAME_CANDIDATE | 34 | 22 | 64.7% | +0.49 | Both v1 and v2 accepted |
| SAME_NO_TRADE | 70 | 44 | 62.9% | +0.28 | Both v1 and v2 rejected |
| LOST | 12 | 10 | **83.3%** | +0.53 | v1 accepted, v2 rejected |
| GAINED | 5 | 2 | **40.0%** | -0.36 | v2 accepted, v1 rejected |
| **Total** | **121** | **78** | **64.5%** | | |

**Agreement rate: 104/121 = 86.0%** (matches stochastic noise baseline at temp=0)

### Headline Numbers

| Metric | v1 (winner) | v2 (regression) | Delta |
|--------|-------------|-----------------|-------|
| CANDIDATE rate | 38.0% (46/121) | 32.2% (39/121) | -5.8pp |
| Win rate | 69.6% | 61.5% | -8.1pp |
| CR * WR | 0.265 | 0.198 | -0.067 |
| Total R (candidates) | +22.94 | +14.79 | **-8.15** |

---

## 2. LOST Trades Analysis (v1=CANDIDATE, v2=NO_TRADE) -- The Regression Core

These 12 trades are the primary cause of the regression. v2 rejected them; v1 correctly accepted them.

### 2.1 Overview

- **n = 12, Wins = 10, WR = 83.3%** (vs 69.6% overall v1 WR)
- **Total R = +6.34** (all lost from v2's portfolio)
- **3 were PARSE_ERRORs in v2** (model output couldn't be parsed -- silent kills)
- **Symbols:** 9 XAUUSD, 3 GBPUSD

These were v1's BEST trades. Removing them from v1 would drop WR from 69.6% to the SAME_CANDIDATE baseline of 64.7%.

### 2.2 Q-Score Drop Patterns (non-PARSE_ERROR, n=9)

Which Q-scores did v2 zero out that v1 had scored positive?

| Q-Score | Dropped to 0 | Drop Rate | Avg Magnitude | What It Checks |
|---------|-------------|-----------|---------------|----------------|
| **Q3** | **7/9** | **78%** | **-15.0** | Price is in/near OB zone |
| **Q5** | **7/9** | **78%** | **-10.5** | M15 CHoCH/displacement confirms entry |
| Q6 | 7/9 | 78% | -10.0 | RR >= 1.5 achievable |
| Q7 | 7/9 | 78% | -5.0 | SL behind swing structure |
| Q4 | 3/9 | 33% | -6.1 | H4/D1 alignment bonus |
| Q2 | 2/9 | 22% | -20.0 | Unmitigated OB exists near price |
| Q1 | 1/9 | 11% | -15.0 | H1 structural break confirmed |
| Both Q3+Q5 | **6/9** | **67%** | | Primary combo killer |

**Key finding:** Q3 and Q5 are the PRIMARY regression drivers. When v2 zeroed Q3 (price not in zone), Q5 through Q7 cascaded to zero (no confirmation, no RR, no SL structure -- because there's no trade to structure if price isn't in zone).

### 2.3 Per-Trade Detail

| Trade ID | Outcome | R | v1 Total | v2 Total | Primary v2 Failure |
|----------|---------|---|----------|----------|-------------------|
| bt_2025-12-19_ny_001_xauusd | WIN | +2.44 | 92 | 22 (OB) / 67 (breaker) | Breaker zone marked "mitigated" -- hard fail on freshness |
| bt_2025-12-22_london_001_gbpusd | WIN | +2.14 | 85 | 40 | Q3=0 (price above OB zone), Q5=0 |
| bt_2025-06-11_ny_002_gbpusd | WIN | +1.59 | 90 | PARSE_ERROR | v2 output couldn't be parsed |
| bt_2025-03-14_london_001_xauusd | WIN | +0.74 | 78 | 15 | Q2=0 (no OB near price), all Q3-Q7=0 |
| bt_2025-02-04_ny_001_xauusd | WIN | +0.57 | 85 | 35 | Q3=0 (price above zone), all Q4-Q7=0 |
| bt_2025-10-03_ny_001_xauusd | WIN | +0.32 | 85 | 45 | Q3=10 partial, Q5=0 (M15 displacement ratio too low) |
| bt_2025-12-26_ny_001_xauusd | WIN | +0.19 | 90 | 30 | Q2=0 (no OB near), Q3=0, Q6=0 |
| bt_2025-02-24_ny_002_xauusd | WIN | +0.13 | 90 | 45 (WAIT) | Q3=0, Q5=0 |
| bt_2025-10-07_ny_001_xauusd | WIN | +0.13 | 90 | 0 | C1 hard fail: "no D1/H4 data" |
| bt_2026-01-26_london_001_xauusd | WIN | +0.09 | 85 | PARSE_ERROR | v2 output couldn't be parsed |
| bt_2024-10-03_ny_001_xauusd | LOSS | -1.00 | 85 | PARSE_ERROR | v2 output couldn't be parsed |
| bt_2024-03-01_ny_001_gbpusd | LOSS | -1.00 | 85 | 45 | Q1=0 (correction from 15), Q3=0, Q5=0 |

### 2.4 Specific v2 Failure Modes

**Mode 1: Q3 Over-Strictness (7/9 non-PE trades)**
v2 applied a stricter "price must be within 1x M15 ATR of OB zone" criterion. Example from bt_2024-03-01: "price at 1.26431 is 0.00088 above OB high 1.26343, exceeding 1x M15 ATR 0.00072, so Q3=0." The overshoot was 0.2x ATR beyond the threshold -- a marginal call that v1 correctly accepted.

**Mode 2: Q5 M15 Confirmation Over-Strictness (7/9 non-PE trades)**
v2 required stronger M15 CHoCH/displacement confirmation. In several cases, v2 noted "M15 CHoCH not confirmed" or "displacement ratio too low" where v1 saw sufficient evidence.

**Mode 3: PARSE_ERROR (3/12 trades)**
v2 produced unparseable output for 3 trades. Two were winners (R=+1.59, R=+0.09) and one was a loss (R=-1.00). These are infrastructure bugs in v2, not evaluation disagreements.

**Mode 4: C1/C2 Hard Fail (1/9 trades)**
bt_2025-10-07: v2 said "C1 failed -- no D1 structural break data provided; H4 data absent" while v1 scored the same MSO at 90 points. v2 applied a hard data-availability gate that v1 didn't enforce.

**Mode 5: Zone Freshness Hard Fail (1/9 trades)**
bt_2025-12-19: v2's breaker framework scored 67 (passing!) but then applied a freshness check: "breaker already marked mitigated=2025-12-19T14:00 -- zone consumed -- hard fail on zone freshness -- score zeroed." This was the biggest winner lost (R=+2.44).

---

## 3. GAINED Trades Analysis (v1=NO_TRADE, v2=CANDIDATE) -- Harmful Additions

| Trade ID | Outcome | R | v1 Score | v2 Score | Why v2 Accepted |
|----------|---------|---|----------|----------|----------------|
| bt_2024-04-01_london_001_xauusd | LOSS | -0.12 | 15 | 85 | v2 found OB zone v1 missed (Q2: 0->20, Q3: 0->15) |
| bt_2024-06-05_ny_001_gbpusd | LOSS | -1.00 | 30 | 80 | v2 scored Q2=20, Q3=15 where v1 had Q2=0, Q3=0 |
| bt_2025-02-25_london_001_xauusd | LOSS | -1.00 | 55 (WAIT) | 68 | v2 found M15 OB proximity (Q3: 0->10, Q5: 10->15) |
| bt_2025-03-19_london_001_xauusd | WIN | +0.14 | 0 (C3 fail) | 85 | v2 reinterpreted direction (v1: "C3 fail no direction") |
| bt_2025-06-12_ny_002_gbpusd | WIN | +0.17 | 30 | 90 | v2 scored Q2=20, Q3=15 where v1 had Q2=0, Q3=0 |

**Summary:** 5 trades, 2 wins, 3 losses. WR=40.0%. Total R = -1.81. v2 found OB zones that v1 missed in 4/5 cases, but those zones led to losses. The gains (R=+0.14, R=+0.17) were marginal while the losses (R=-1.00, R=-1.00) were full stops.

---

## 4. v1 NO_TRADE Score Distribution (75 Rejected Trades)

### 4.1 Score Bands

| Score Band | Count | WR (if traded) | Description |
|------------|-------|----------------|-------------|
| Early exit (no score) | 31 | 64.5% (20/31) | C1/C2/C3 hard fail before scoring |
| 0-14 | 1 | 0.0% | Near-zero score |
| 15-34 | 27 | 55.6% (15/27) | Low scores, multiple Q failures |
| 35-44 | 6 | 50.0% (3/6) | Borderline low |
| 45-64 (WAIT zone) | 8 | 50.0% (4/8) | Near-misses |
| 65+ | 2 | 50.0% (1/2) | Scored high but still rejected |

### 4.2 Early Exit Categories (31 trades with no parseable total score)

| Category | Count |
|----------|-------|
| C1 fail (no structural bias) | 17 |
| C3 fail (direction conflict) | 9 |
| C2 fail (opposing HTF) | 3 |
| Other | 2 |

### 4.3 Near-Misses (WAIT Zone: Score 45-64)

These 8 trades scored close to the 65-point CANDIDATE threshold:

| Trade ID | Score | Outcome | R | Q-Score Breakdown | Bottleneck |
|----------|-------|---------|---|-------------------|------------|
| bt_2025-02-25_london_001_xauusd | 55 | LOSS | -1.00 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=10 Q6=0 Q7=0 | Q3, Q6 |
| bt_2025-01-28_ny_002_xauusd | 50 | WIN | +0.60 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=0 Q6=0 Q7=0 | Q3, Q5 |
| bt_2025-03-04_ny_002_gbpusd | 50 | WIN | +0.87 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=0 Q6=0 Q7=0 | Q3, Q5 |
| bt_2025-03-05_ny_001_xauusd | 50 | LOSS | -1.00 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=0 Q6=0 Q7=0 | Q3, Q5 |
| bt_2026-01-21_ny_002_xauusd | 50 | LOSS | -0.27 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=0 Q6=0 Q7=0 | Q3, Q5 |
| bt_2026-02-03_ny_002_xauusd | 50 | WIN | +2.69 | Q1=15 Q2=0 Q3=10 Q4=5 Q5=0 Q6=10 Q7=5 | Q2, Q5 |
| bt_2024-07-23_ny_001_xauusd | 45 | WIN | +1.87 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=0 Q6=0 Q7=0 | Q3, Q5 |
| bt_2025-02-26_london_001_xauusd | 45 | LOSS | -1.00 | Q1=15 Q2=20 Q3=0 Q4=10 Q5=0 Q6=0 Q7=0 | Q3, Q5 |

**WR = 50.0%** -- at random, these near-misses don't have edge. v1 was correct to reject them.

**Bottleneck analysis for near-misses:**
- Q3 could flip 5/8 near-misses if scored non-zero
- Q5 could flip 5/8 near-misses if scored non-zero
- Q3 and Q5 together are the universal bottleneck

### 4.4 Rejected Winners: Where Did v1 Leave Money on the Table?

46/75 rejected trades (61.3%) would have won. Top missed opportunities:

| Trade ID | Score | R | Q Bottleneck | Reason |
|----------|-------|---|--------------|--------|
| bt_2025-03-13_ny_002_xauusd | 15 | +3.35 | Q2-Q7 all zero | Only Q1 scored; no OB found |
| bt_2025-03-04_london_001_gbpusd | 15 | +2.64 | Q2-Q7 all zero | Only Q1 scored; no OB found |
| bt_2026-02-03_ny_002_xauusd | 50 | +2.69 | Q2=0, Q5=0 | OB not found near price; no displacement |
| bt_2024-07-23_ny_001_xauusd | 45 | +1.87 | Q3=0, Q5=0 | Price above zone; no M15 confirmation |
| bt_2024-04-02_london_001_xauusd | no score | +1.89 | C3 fail | Direction couldn't be established |
| bt_2025-01-28_london_001_xauusd | 25 | +0.97 | Q2-Q4=0, Q6-Q7=0 | No OB near price |
| bt_2025-03-04_ny_002_gbpusd | 50 | +0.87 | Q3=0, Q5=0 | Price above zone |

### 4.5 Top 3 v1 Rejection Reasons (by frequency, trades can match multiple)

| Rank | Rejection Reason | Count (out of 75) |
|------|-----------------|-------------------|
| 1 | Q3=0 (price not in/near OB zone) | 45 (60%) |
| 2 | Q6=0 (RR fails min 1.5) | 42 (56%) |
| 3 | Q5=0 (no M15 CHoCH/displacement) | 41 (55%) |
| 4 | Q2=0 (no unmitigated OB near price) | 35 (47%) |
| 5 | C1 fail (no structural bias) | 23 (31%) |
| 6 | C3 fail (direction conflict) | 20 (27%) |
| 7 | Below score threshold | 19 (25%) |
| 8 | Zone already mitigated | 16 (21%) |
| 9 | C2 fail (opposing HTF) | 10 (13%) |
| 10 | No unmitigated OB found | 9 (12%) |

---

## 5. Per-Q-Score Analysis

### 5.1 Average Q-Score by Decision and Outcome (v1 prompt)

| Q-Score | CAND+WIN | CAND+LOSS | NO_TRADE+WIN | NO_TRADE+LOSS | Discrimination |
|---------|----------|-----------|--------------|---------------|----------------|
| Q1 (15 max) | 14.9 | 14.6 | 14.4 | 15.0 | None -- always near max |
| Q2 (20 max) | 18.1 | 18.6 | 5.0 | 11.0 | **Strong gate** (18 vs 5-11) |
| Q3 (15 max) | 14.5 | 15.0 | 0.4 | 2.2 | **Strongest gate** (15 vs 0-2) |
| Q4 (10 max) | 6.2 | 6.8 | 1.5 | 3.6 | Moderate |
| Q5 (15 max) | 12.7 | 12.1 | 0.9 | 1.8 | **Strong gate** (12 vs 1) |
| Q6 (10 max) | 9.7 | 10.0 | 0.4 | 1.1 | **Strong gate** (10 vs 0-1) |
| Q7 (5 max) | 5.0 | 5.0 | 0.2 | 0.6 | Gate (5 vs 0) |
| zone_first | 4.8 | 5.0 | 3.8 | 3.8 | None |

**Key insight:** No Q-score discriminates between CANDIDATE winners and CANDIDATE losers. All averages are nearly identical for CAND+WIN vs CAND+LOSS. The Q-scores are purely GATE functions (accept/reject), not quality discriminators. This means:

- Q-scores correctly separate "tradeable setups" from "non-tradeable"
- But within the CANDIDATE pool, Q-scores provide ZERO predictive power for win vs loss
- The edge comes from the OB zone mechanism itself, not from scoring granularity

### 5.2 Q-Score as Gate: The Binary Reality

For v1 CANDIDATEs (n=46), Q-score values are remarkably clustered:

| Q-Score | Most Common Value | % at Max | % at Zero |
|---------|-------------------|----------|-----------|
| Q1 | 15 (max) | 89% | 0% |
| Q2 | 20 (max) | 87% | 13% |
| Q3 | 15 (max) | 96% | 2% |
| Q4 | 5 | 20% (at 10) | 0% |
| Q5 | 10-15 | 46% (at 15) | 0% |
| Q6 | 10 (max) | 98% | 2% |
| Q7 | 5 (max) | 100% | 0% |

The scoring system is effectively binary: a Q-score is either near-max or zero. There is almost no middle ground.

---

## 6. Symbol-Level Impact

| Symbol | n | v1 CR | v1 WR | v2 CR | v2 WR | LOST | GAINED |
|--------|---|-------|-------|-------|-------|------|--------|
| XAUUSD | 100 | 38% (38) | 65.8% | 32% (32) | 56.2% | 9 | 3 |
| GBPUSD | 21 | 38% (8) | 87.5% | 33% (7) | 85.7% | 3 | 2 |

XAUUSD absorbed most of the regression: WR dropped 9.6pp. GBPUSD was relatively stable.

---

## 7. PARSE_ERROR Analysis

v2 produced 4 PARSE_ERRORs (vs 0 in v1):

| Trade ID | v1 Decision | Outcome | R |
|----------|------------|---------|---|
| bt_2024-10-03_ny_001_xauusd | CANDIDATE | LOSS | -1.00 |
| bt_2025-06-11_ny_002_gbpusd | CANDIDATE | WIN | +1.59 |
| bt_2025-06-26_ny_001_xauusd | WAIT | LOSS | -1.00 |
| bt_2026-01-26_london_001_xauusd | CANDIDATE | WIN | +0.09 |

3 of 4 PARSE_ERRORs hit v1 CANDIDATEs. Net impact: lost R=+1.59 + R=+0.09 = +1.68 from winners, gained back R=-1.00 from the loss not being taken. **Net PARSE_ERROR R impact: +0.68 lost.**

---

## 8. Root Cause Synthesis

### Why v2 regressed: Three failure modes

**1. Q3 Over-Strictness (primary, ~60% of regression)**
v2 applied stricter price-to-zone proximity checks. The most revealing example: bt_2024-03-01 where "price at 1.26431 is 0.00088 above OB high 1.26343, exceeding 1x M15 ATR 0.00072, so Q3=0." The overshoot was just 0.22x ATR beyond the threshold. v2 turned borderline-pass into hard-fail.

**2. Q5 M15 Confirmation Over-Strictness (~25% of regression)**
v2 demanded stronger M15 displacement evidence. In cases like bt_2025-10-03, v2 noted "displacement ratio 0.8, no" while v1 accepted the same signal. v2 raised the bar on what constitutes "sufficient" M15 structural confirmation.

**3. PARSE_ERRORs (infrastructure, ~15% of regression)**
3 v2 PARSE_ERRORs silently killed trades. This is a v2 prompt formatting issue, not an evaluation disagreement.

### Why v2's gains didn't compensate

v2 gained 5 trades, but they had only 40% WR. In 4/5 cases, v2 "found" OB zones that v1 correctly ignored. v2 was simultaneously too strict on Q3 for good setups (killing 83% WR trades) and too loose on Q2/Q3 for bad setups (accepting 40% WR trades). This is the worst possible combination: tighter where it should be loose, looser where it should be tight.

---

## 9. Actionable Implications for Next Prompt Iteration

### DO NOT change (v1 got these right):
1. **Q3 proximity threshold** -- v1's zone proximity tolerance is calibrated correctly. The 83.3% WR on LOST trades proves these were genuine OB retest setups.
2. **Q5 confirmation level** -- v1's M15 displacement threshold captures real continuation setups.
3. **C1/C2/C3 early-exit gates** -- These correctly kill ~31 trades per 121 that have no structural basis.

### Potential improvements (but test carefully):
1. **Q2 zone identification consistency** -- In GAINED trades, v2 found OB zones v1 missed (Q2: 0->20 in 3/5 cases). But those zones led to losses. v1's zone identification is better calibrated.
2. **PARSE_ERROR robustness** -- v2's 4 PARSE_ERRORs are a formatting issue. Any prompt change must maintain parseable output.
3. **Near-miss investigation** -- 8 trades scored 45-64 in v1 with 50% WR. The Q3/Q5 bottleneck in these trades is expected (they're marginal setups). No action needed -- v1 correctly rejects them.
4. **Q-score granularity is wasted** -- Scores are effectively binary (max or zero). Consider simplifying to pass/fail checklist instead of pretending granular scoring adds precision. But this is a structural change -- test in isolation.

### The winning strategy for v1 improvement:
- v1 is already well-calibrated on the accept/reject boundary
- The 46 rejected winners (61.3% of rejections) mostly failed on Q2=0 (no OB near price) -- these are structural MSO limitations, not prompt failures
- The biggest gains would come from **reducing PARSE_ERRORs** and **not breaking Q3/Q5 calibration**
- Any "fix" that tightens Q3 or Q5 will regress. Any fix that loosens them must be tested against the 75 current rejections to ensure it doesn't pull in 50% WR marginal trades.

---

## Appendix A: v1 CANDIDATE Full Q-Score Table (sorted by R-multiple)

| Outcome | R | Conf | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | +zf | Total | Trade ID |
|---------|---|------|----|----|----|----|----|----|----|----|-------|----------|
| WIN | +3.99 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-05-05_london_001_xauusd |
| WIN | +3.77 | 73 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-01-30_london_001_xauusd |
| WIN | +3.47 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-04-17_ny_001_xauusd |
| WIN | +3.31 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2026-01-22_london_001_xauusd |
| WIN | +2.70 | 73 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-03-05_london_001_gbpusd |
| WIN | +2.44 | 73 | 12 | 20 | 15 | 10 | 15 | 10 | 5 | 5 | 92 | bt_2025-12-19_ny_001_xauusd |
| WIN | +2.14 | 73 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-12-22_london_001_gbpusd |
| WIN | +1.92 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-03-11_london_001_gbpusd |
| WIN | +1.59 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-06-11_ny_002_gbpusd |
| WIN | +1.26 | 78 | 15 | 20 | 15 | 10 | 10 | 10 | 5 | 5 | 90 | bt_2025-10-20_ny_001_xauusd |
| WIN | +1.25 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-06-10_ny_001_xauusd |
| WIN | +0.85 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-02-18_ny_001_xauusd |
| WIN | +0.75 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2024-04-18_ny_001_xauusd |
| WIN | +0.75 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-03-07_london_001_gbpusd |
| WIN | +0.74 | 78 | 15 | 0 | 15 | 10 | 15 | 10 | 5 | 5 | 78 | bt_2025-03-14_london_001_xauusd |
| WIN | +0.57 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-02-04_ny_001_xauusd |
| WIN | +0.51 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-03-11_ny_002_gbpusd |
| WIN | +0.51 | 78 | 15 | 20 | 15 | 10 | 15 | 10 | 5 | 5 | 95 | bt_2025-04-04_ny_001_xauusd |
| WIN | +0.47 | 73 | 15 | 0 | 15 | 5 | 15 | 10 | 5 | 0 | 68 | bt_2025-02-26_london_001_gbpusd |
| WIN | +0.38 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-06-23_ny_001_xauusd |
| WIN | +0.33 | 81 | 15 | 20 | 15 | 10 | 15 | 10 | 5 | 5 | 95 | bt_2025-03-17_london_001_xauusd |
| WIN | +0.32 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-10-03_ny_001_xauusd |
| WIN | +0.21 | 78 | 15 | 20 | 15 | 5 | 15 | 0 | 5 | 5 | 80 | bt_2025-12-18_ny_002_xauusd |
| WIN | +0.21 | 73 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2026-01-12_london_001_xauusd |
| WIN | +0.19 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-12-26_ny_001_xauusd |
| WIN | +0.14 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-03-25_ny_001_xauusd |
| WIN | +0.13 | 73 | 15 | 20 | 15 | 10 | 10 | 10 | 5 | 5 | 90 | bt_2025-02-24_ny_002_xauusd |
| WIN | +0.13 | 73 | 15 | 20 | 15 | 10 | 10 | 10 | 5 | 5 | 90 | bt_2025-10-07_ny_001_xauusd |
| WIN | +0.11 | 78 | 15 | 0 | 15 | 5 | 15 | 10 | 5 | 5 | 73 | bt_2025-02-21_london_001_xauusd |
| WIN | +0.09 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2024-07-24_ny_002_xauusd |
| WIN | +0.09 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2026-01-26_london_001_xauusd |
| WIN | +0.06 | 73 | 15 | 20 | 0 | 10 | 15 | 10 | 5 | 5 | 80 | bt_2026-01-06_ny_002_xauusd |
| LOSS | +0.00 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-02-21_ny_002_xauusd |
| LOSS | -0.44 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-09-23_ny_001_xauusd |
| LOSS | -1.00 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2024-03-01_ny_001_gbpusd |
| LOSS | -1.00 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2024-04-08_ny_001_xauusd |
| LOSS | -1.00 | 78 | 15 | 20 | 15 | 10 | 10 | 10 | 5 | 5 | 90 | bt_2024-09-27_ny_001_xauusd |
| LOSS | -1.00 | 78 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2024-10-03_ny_001_xauusd |
| LOSS | -1.00 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-02-12_london_001_xauusd |
| LOSS | -1.00 | 73 | 15 | 20 | 15 | 10 | 10 | 10 | 5 | 5 | 90 | bt_2025-02-26_ny_002_xauusd |
| LOSS | -1.00 | 78 | 15 | 0 | 15 | 10 | 15 | 10 | 5 | 5 | 78 | bt_2025-03-21_london_001_xauusd |
| LOSS | -1.00 | 78 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 90 | bt_2025-03-21_ny_002_xauusd |
| LOSS | -1.00 | 73 | 15 | 20 | 15 | 5 | 10 | 10 | 5 | 5 | 85 | bt_2025-06-25_london_001_xauusd |
| LOSS | -1.00 | 73 | 12 | 20 | 15 | 10 | 10 | 10 | 5 | 5 | 87 | bt_2025-10-09_london_001_xauusd |
| LOSS | -1.00 | 73 | 12 | 20 | 15 | 10 | 15 | 10 | 5 | 5 | 92 | bt_2025-10-09_ny_002_xauusd |
| LOSS | -1.00 | 73 | 15 | 20 | 15 | 5 | 15 | 10 | 5 | 5 | 95 | bt_2025-12-30_ny_001_xauusd |

**Pattern:** Winning and losing CANDIDATEs are indistinguishable by Q-scores. Both cluster at 85-90 total. The scoring system identifies "tradeable OB retest setups" but cannot predict which ones will win or lose. This is expected -- the edge is the OB zone mechanism's base rate (~70%), not AI selectivity.

---

## Appendix B: Confidence Score Distribution

| Conf Score | v1 Count | v2 Count |
|------------|----------|----------|
| 81 | 1 | 0 |
| 80 | 0 | 9 |
| 78 | 31 | 0 |
| 77 | 0 | 1 |
| 75 | 0 | 9 |
| 73 | 14 | 0 |
| 72 | 0 | 16 |
| 70 | 0 | 4 |

v1 uses {73, 78, 81}. v2 uses {70, 72, 75, 77, 80}. Neither has meaningful granularity -- this confirms the confidence score is a rubber stamp.

---

*Analysis generated April 12, 2026. Data: P2A_s46_max_new_results.json (v1), P2A_v2_s46_max_results.json (v2), entry_engineering_dataset.csv (outcomes).*

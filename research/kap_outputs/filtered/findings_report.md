# KAP Filtered Findings Report (v2 — Strict)
**Date:** 2026-04-06
**Filter version:** v2_strict (raised bar from v1's 50 kept to 28)
**Claims received:** 226 (62 videos, 20+ channels)
**Claims kept:** 28
**Redundant:** 143
**Hit rate:** 12.4%

---

## Executive Summary

226 claims extracted from 62 YouTube videos on OB trading, SMC/ICT strategies, backtesting methodology, and gold market mechanics. After filtering against the full knowledge base and all validated statistical findings:

- **5 FALSE BELIEFS identified** — popular YouTube advice that our data REFUTES
- **5 CONVERGENT clusters** — independent sources confirming our findings
- **3 CONTRADICTION clusters** — sources disagreeing with each other
- **28 findings kept** for Agent 4 to evaluate for system improvement

The single most valuable output is the **false belief frequency analysis**: the MORE popular a false belief, the MORE edge we have — because other traders are using broken filters.

---

## PRIORITY 5 FINDINGS (System-critical)

### Finding #1: OB Body Size is Null (CONTRADICTORY)
- **Claim:** Thick/heavy OBs have more liquidity and produce larger expansions
- **Tag:** CONTRADICTORY
- **Our data:** impulse_atr_multiple p=0.97 — COMPLETELY null
- **False belief count:** 1 video promotes this
- **Source:** The Soup Room (video_05)
- **Impact:** Anyone filtering for "thick" OBs uses a broken filter

### Finding #2: COT is Useless for Gold (CONTRADICTORY)
- **Claim:** COT week-over-week changes predict short-term gold direction
- **Tag:** CONTRADICTORY
- **Our data:** Spearman r=+0.048 (p=0.495). ZERO signal.
- **False belief count:** 1 video teaches this
- **Source:** BK Trading Academy (video_15)
- **Impact:** Do NOT implement COT as filter. Adds pure noise.

### Finding #3: M1 Refinement is a Trap (CONTRADICTORY)
- **Claim:** Dropping to M1 within OB zone doubles/triples RR
- **Tag:** CONTRADICTORY
- **Our data:** M1/M5 entries: -0.414R/trade. Loss MFE 0.93R.
- **False belief count:** 3 videos promote this
- **Sources:** Lewis Kelly (video_02, video_04), Garland Trader (video_13)
- **Impact:** M1 refinement creates near-win illusion. M15 is optimal.

### Finding #4: Sweep-Before-OB is Anti-Predictive (CONTRADICTORY)
- **Claim:** OBs formed after sweeping liquidity have higher hold probability
- **Tag:** CONTRADICTORY
- **Our data:** 71.6% without sweep vs 63.4% with. Anti-predictive.
- **False belief count:** 5 videos (most popular false belief)
- **Sources:** Smart Risk, Lewis Kelly, Baileysforex, Photon Trading, Trading Neighbor
- **Impact:** HIGHEST EDGE VALUE. The #1 SMC filter is broken.

### Finding #5: Sweep Rule Confirmed Anti-Predictive (CONVERGENT)
- **Claim:** Removing sweep rule improved quant-coded Silver Bullet by 46% over 10 years (2,310 trades)
- **Tag:** CONVERGENT with Finding #4
- **Our data:** Independently confirmed
- **Source:** Trader Zan (video_20)
- **Impact:** Strongest convergent finding. Two independent datasets agree.

---

## PRIORITY 4 FINDINGS (Component improvement)

### Finding #6: Day-of-Week Filtering is Noise (CONTRADICTORY)
- **Claim:** Mon/Fri produce more losing OB trades
- **Our data:** Kruskal-Wallis p=0.768. Not significant.
- **False belief count:** 3 videos
- **Sources:** Smart Risk, Eddy Pips, gold turtle soup video

### Finding #7: No Break-Even Stops (CONVERGENT)
- **Claim:** Holding to SL/TP beats moving to break-even
- **Sources:** Baileysforex (video_09), Garland Trader (video_13)
- **Contradicted by:** Trading Neighbor (video_23) claims BE at 1:1 helps
- **Our data:** Session timeouts (+0.81R, 70% WR) support letting trades run
- **Test:** Simulate BE-at-1R on batch trades

### Finding #8: 3R Target Optimal (CONVERGENT)
- **Claim:** 3R beats 2R on total profit despite lower WR
- **Sources:** Eddy Pips (100 trades), Trader Zan (2,310 trades)
- **Test:** RR optimizer on our batch using actual MFE data

### Finding #9: OB/FVG Freshness Matters (CONVERGENT)
- **Claim:** Fresh OBs/FVGs outperform stale ones
- **Sources:** Smart Risk (video_01), Trader Zan (video_20, quant-tested)
- **Status:** UNTESTED in our system — new variable
- **Test:** OB age vs continuation rate

### Finding #10: ICT Strategies Have Regime Dependency (COMPLEMENTARY)
- **Claim:** Silver Bullet lost money 2015-2019, profitable 2020+
- **Source:** Trader Zan (video_20, 10-year quant backtest)
- **Impact:** If ICT strategies are era-specific, our edge may decay with market structure changes

---

## PRIORITY 3 FINDINGS (Useful context)

### Finding #11: Gold body breaks > wick breaks for BOS
- **Source:** Trade Forex with Paul (video_03)
- **Test:** Compare body-close vs wick BOS on gold H4/H1

### Finding #12: Gold fills FVGs more reliably than forex
- **Source:** Trade Forex with Paul (video_03)
- **Test:** FVG fill rate comparison XAUUSD vs EURUSD

### Finding #13: Gold shallow retests — use wider OB entry zones
- **Source:** Baileysforex (video_09)
- **Test:** Retracement depth into OB zones on gold

### Finding #14: Strong gold trends = shallower retracements
- **Source:** Baileysforex (video_09)
- **Test:** ADX vs retracement depth correlation

### Finding #15: Stacked OBs — skip first when FVG below
- **Source:** Smart Risk (video_01)
- **Test:** Track which OB holds in stacked scenarios

### Finding #16: Gold continuation > reversal entries
- **Source:** Gold turtle soup video (video_24)
- 60% WR, 1.7R avg on gold — aligns with our 62%

### Finding #17: London sub-window optimization (08:00-09:00 UTC best)
- **Source:** Gold turtle soup video (video_24)
- Potential conflict with our 82.8% late-London finding

### Finding #18: NWOG as confluence variable (NOVEL)
- **Source:** Gold turtle soup video (video_24)
- New variable not in our feature set

### Finding #19: 28% untriggered OB rate
- **Source:** Smart Risk (video_01)
- Useful context for trade frequency expectations

### Finding #20: Gold OB WR year-over-year decline (72% → 57%)
- **Source:** Baileysforex (video_09)
- Independent evidence of time-varying edge, mirrors our quarterly decay

### Finding #21: SL wick vs body — 6-7% marginal, not worth it
- **Source:** Eddy Pips (video_08)

### Finding #22: In-sample permutation test methodology
- **Source:** neurotrader (video_07)
- Additional validation step we could add

### Finding #23: PF 1.75 minimum — we're at the floor
- **Source:** Gold turtle soup video (video_24)

### Finding #24: Prop firm data validates M15 over scalping
- **Source:** PipBack (video_11)
- 70% of breached traders are scalpers

### Finding #25: AM macro sub-windows (NQ-specific)
- **Source:** Blue Edge Forex (video_21)
- May not transfer to gold

### Finding #26: Pullback character predicts depth
- **Source:** Photon Trading (video_14)

### Finding #27: Vol clustering permutation caveat (validates our methodology)
- **Source:** neurotrader (video_07)

### Finding #28: Forward liquidity targets needed for zone validity
- **Source:** Photon Trading (video_14)

---

## FALSE BELIEF FREQUENCY TABLE

| Belief | Videos Promoting | Our Data | Edge Value |
|--------|-----------------|----------|------------|
| Sweep improves OB quality | **5** | Anti-predictive (71.6% vs 63.4%) | **HIGHEST** |
| M1 refinement improves RR | **3** | -0.414R/trade trap | HIGH |
| Mon/Fri worse for OBs | **3** | p=0.768 null | MODERATE |
| Bigger OBs are better | 1 | p=0.97 null | MODERATE |
| COT predicts gold | 1 | r=+0.048 (p=0.495) | LOW |

**Key insight:** The sweep filter is the most popular false belief (5/62 videos promote it). Since most SMC traders use sweep as a prerequisite, they are systematically avoiding trades that our data shows are BETTER (71.6% WR). This is edge we can harvest.

---

## CONVERGENT CLUSTERS (independent sources agree)

1. **Sweep filters hurt** — Trader Zan (2,310 trades) + Our data (6,046 events)
2. **3R target optimal** — Eddy Pips (100 trades) + Trader Zan (2,310 trades)
3. **No break-even stops** — Baileysforex + Garland Trader + Our timeout data
4. **M1 entries hurt** — PipBack prop data + Our quant data vs 3 YouTube opinions
5. **Freshness matters** — Smart Risk + Trader Zan (quant-tested)

---

## RECOMMENDED TESTS FOR AGENT 4

Priority order:
1. **OB/FVG freshness vs continuation** (Finding #9) — NEW VARIABLE, untested
2. **RR optimizer: 1R through 4R** (Finding #8) — convergent claim, cheap test
3. **BE-at-1R simulation** (Finding #7) — convergent claim, batch simulation
4. **NWOG alignment** (Finding #18) — NOVEL variable, cheap test
5. **Body vs wick BOS on gold** (Finding #11) — gold-specific quality improvement
6. **Gold FVG fill rate** (Finding #12) — gold-specific target logic
7. **Stacked OB behavior** (Finding #15) — potential filter
8. **In-sample permutation test** (Finding #22) — methodological validation

---

*Agent 3 filtering complete. 226 claims → 28 findings (12.4% hit rate).*

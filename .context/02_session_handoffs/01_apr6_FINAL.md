# SESSION HANDOFF — Complete Project State
# Date: April 6, 2026 (Day 12)
# Status: FINAL. System goes live Monday April 7, 2026.
# This document is AUTHORITATIVE — supersedes ALL prior handoffs.

---

## SYSTEM IDENTITY

Autonomous AI trading agent ("Gold Traders Operating System") trading XAUUSD, US30, USDJPY, GBPJPY, GBPUSD on FTMO $100K demo via MetaTrader 5. Uses Claude Sonnet as reasoning engine. Trades H1 order block retests after structural breaks (BOS/CHoCH) during London and NY kill zones.

---

## VALIDATED EDGE

| Component | Value | Evidence |
|---|---|---|
| AI filter | +0.300R/trade over mechanical | 6,046 events: mechanical +0.175R vs AI +0.475R |
| OB zone precision | +17pp over generic pullback | Test A rerun, p=0.003, 219 events |
| Session memory | 2x expectancy, load-bearing | Test B: CANDIDATE rate drops to 33% without it |
| Kill zone timing | London 74% WR vs NY 60% | R-multiple analysis, 111 trades |
| Session timeouts | +0.81R avg, best exit type | 36% of all exits |
| Partial close structure | 50%/25%/25% | Outperforms every fixed override tested |

**Value chain:** BOS detection → OB zone (+17pp) → AI filter (+0.300R/trade) → session memory (2x) → execution rules

---

## WHAT THE AI ACTUALLY DOES

**The AI filters brilliantly at the CANDIDATE/NO_TRADE boundary.** Of 6,046 OB retest events, only 621 (10.3%) become CANDIDATEs. The rejected 90% produce essentially 0R. The approved 10% produce +0.475R/trade. On XAUUSD: mechanical 33% WR → AI-filtered 73% WR (40pp lift).

**But it cannot discriminate WITHIN CANDIDATEs.** 98% get confidence 80. A+ and A grades perform identically. Three independent scoring attempts failed. The MSO doesn't contain features that predict which CANDIDATEs will win vs lose.

**The value is in filtering, not grading.** The binary CANDIDATE/NO_TRADE decision is where the +0.300R lives. Stop trying to improve confidence scoring. It doesn't matter.

**298 model evaluations proved:** No model (Opus, thinking-enabled, veto gates) can improve discrimination. "More careful" = "fewer trades of everything." Sonnet's loose "at or near" OB interpretation is load-bearing.

---

## DEPLOYED INFRASTRUCTURE (all verified, 700 tests passing)

| Component | Status |
|---|---|
| 13:00 UTC skip filter (XAUUSD) | ACTIVE |
| Correlation-aware sizing (JPY pairs, max 1.5%) | ACTIVE, end-to-end verified |
| Walk-forward lock mechanism | READY — set Monday AM |
| SPRT monitoring script | VERIFIED 3/3 sequences |
| Gold expertise injection (400 tokens) | ACTIVE |
| Trade index seeded (129+ batch trades) | ACTIVE |
| OB continuation logger | ACTIVE |
| News calendar filter (28 tests) | BUILT, DISABLED for demo |
| Devil's Advocate shadow (threaded, non-blocking) | ACTIVE, $0.025/CANDIDATE |
| Per-evaluation structured logging (JSONL) | ACTIVE |
| Enriched trade records | ACTIVE |
| Monitoring dashboard (7 sections) | WORKING |
| Walk-forward compliance (prompt hash) | ACTIVE on startup |
| MFE/MAE post-trade computation | ACTIVE |
| OB event resolution (resolve_obs) | ACTIVE |

---

## INVESTIGATIONS — ALL CLOSED

| Investigation | Result | Conclusion |
|---|---|---|
| OB zone value (Test A) | +17pp, p=0.003 | Zone is the primary edge source |
| Mechanical vs AI backtest | AI +0.300R/trade over mechanical | **AI earns its keep — NOT a rubber stamp** |
| Intra-candle M1 entries | -0.414R/trade with execution delay | **M1 entries are traps. M15 captures everything viable** |
| Prompt narrative (Test B) | Production +5R over neutral | Keep production prompt |
| Opus as PA (all variants) | 92-100% reject everything | No discrimination, all dead |
| Sonnet + thinking | 96% reject everything | Hyper-literal, kills frequency |
| Confidence decomposition | 20-30pt noise, losers score higher | Failed, killed |
| 3x confidence scorer | All failed | Within-CANDIDATE discrimination not achievable |
| Devil's Advocate (5 trades) | Quality good, weak signal | Shadow mode for WF-1, WF-2 candidate |
| Sub-period WR decay | Mix artifact, gold improved +5.7pp | No real decay |
| DST effect | No significant effect | No KZ adjustment needed |
| Regime classifier | 74% "RANGING" during bull | Classifier broken, defer |
| Competitive landscape | No near-term threat | Moat is validation framework |

**Total: 298 model evaluations, $30 research cost, 14 investigations closed.**

---

## SHADOW DATA BEING COLLECTED (all non-blocking, zero impact on trading)

| Data stream | Source | Purpose for July review |
|---|---|---|
| DA risk scores per CANDIDATE | devils_advocate.py | Does max_risk_pct predict losers? |
| Per-eval structured logs | evaluation_logger.py | Which steps filter? NO_TRADE distribution? |
| Enriched trade records | orchestrator shadow_data | Entry-to-OB distance, impulse quality, timing |
| OB continuation events | ob_retest_events JSON | Is the 70% rate holding? |
| MFE/MAE per trade | Post-trade M5 computation | Are exits optimal? |

---

## MARKET CONTEXT (April 2026)

- Gold at ~$4,675, correcting 16% from $5,595 ATH
- GVZ at 42 (doubled from batch period ~20)
- Iran war active (Day 34+), headline-driven market
- NOT a clean trend — system was NOT tested in this regime
- First 30 trades are out-of-sample validation

---

## MONDAY MORNING SEQUENCE

```bash
cd ~/Documents/ai-trading-agent

# Start 5 processes
nohup python run_agent.py --symbol XAUUSD --mode demo > logs/xauusd.log 2>&1 &
nohup python run_agent.py --symbol US30_cash --mode demo > logs/us30.log 2>&1 &
nohup python run_agent.py --symbol USDJPY --mode demo > logs/usdjpy.log 2>&1 &
nohup python run_agent.py --symbol GBPJPY --mode demo > logs/gbpjpy.log 2>&1 &
nohup python run_agent.py --symbol GBPUSD --mode demo > logs/gbpusd.log 2>&1 &

# Lock walk-forward
python run_agent.py --lock-walk-forward --window WF-1 --months 3
```

---

## WEEK 1 RULES

1. NO prompt changes (walk-forward locked)
2. NO parameter changes
3. NO killing instruments after 2-3 losses (SPRT handles this)
4. 0-2 trades in first 2-3 days is NORMAL
5. Fix bugs only, not strategy
6. Log everything in the trade journal template

---

## WF-2 DEFERRED CHANGES LOG (July 2026)

| # | Change | Priority | Status |
|---|---|---|---|
| 1 | Strip confidence scorer guidance from prompt | HIGH | Designed, ready |
| 2 | DA promotion (if shadow data shows signal) | HIGH | Shadow collecting |
| 3 | Investigate de-weighting sweep requirement | MEDIUM | Anti-predictive at p=0.40 |
| 4 | Add 1-2 aggressive prompt nudges | MEDIUM | 7 conservative vs 2 aggressive |
| 5 | Wire Layer 3 to PA (with current-regime data) | MEDIUM | Infrastructure exists |
| 6 | Rethink AI role: contextual judgment not validation | HIGH | Needs design |
| 7 | Adaptive exit logic (trailing based on MFE/MAE data) | HIGH | Needs WF-1 data |
| 8 | Fix regime classifier | LOW | Normalize for price level |
| 9 | Evaluate breaker_retest activation | MEDIUM | Built, config toggle |

**CLOSED (proven unnecessary):**
- ~~Test mechanical-only system~~ → AI adds +0.300R/trade, mechanical is far worse
- ~~Intra-candle execution simulation~~ → M1 entries are -0.414R/trade, dead
- ~~Confidence decomposition~~ → 3 attempts failed, MSO lacks signal
- ~~Opus/thinking veto gate~~ → No discrimination exists

---

## KEY NUMBERS

| Metric | Value |
|---|---|
| Gold breakeven WR | 35.7% |
| Gold batch WR | 62.0% (129 trades) |
| AI filter advantage | +0.300R/trade over mechanical |
| System expectancy | +0.200R/trade (PF 1.75) |
| SPRT confirm | Λ ≥ +2.773 |
| SPRT kill | Λ ≤ -1.556 |
| Expected trades/month | ~17 across all instruments |
| API cost/month | ~$60 + $0.43 DA shadow |
| Walk-forward window | WF-1: April 7 – July 7, 2026 |
| Zeta confidence | 6/10 (3 months), 7.5/10 (12 months) |
| Total project spend | ~$210 |
| Tests passing | 700 |

---

## KNOWLEDGE ACQUISITION PIPELINE (new capability)

A semi-autonomous research pipeline for extracting trading knowledge from YouTube videos and other sources. Two self-contained prompt files enable any fresh session to run it:

- **CHROME_AGENT_PROMPT.md** — paste into Claude in Chrome to extract video transcripts and claims
- **KAP_LAUNCH_KIT.md** — paste into a fresh project session to filter claims against the KB

Pipeline: Chrome extracts → project session filters → novel findings saved to `kb_research_findings.md` → testable findings get Claude Code tests.

Capacity: 10-12 videos per Chrome session, ~$0 cost (subscription only).

---

## PROJECT KNOWLEDGE DOCUMENTS

| Document | Purpose |
|---|---|
| This handoff | AUTHORITATIVE current state |
| kb_gold_market_deep_knowledge.md | How gold trades |
| kb_validation_and_monitoring_framework.md | SPRT, Wilson CIs, walk-forward |
| kb_edge_mechanisms_and_risks.md | Stop-cascade mechanism, decay risks |
| operator_decision_playbook_final.md | 41 scenarios |
| quick_reference_card-2.md | Daily phone reference (v1.1 corrected) |
| trade_journal_template.md | Per-trade, daily, weekly logging |
| test_a_rerun_real_bos_results.md | OB zone +17pp evidence |
| test_a_implications_analysis-2.md | Value chain, forward validation |
| pre_lock_final_review.md | Zeta's 5-question assessment |
| SWOT_FINAL.md | 10 strengths, 10 weaknesses, 8 opportunities, 9 threats |
| KAP_LAUNCH_KIT.md | Knowledge acquisition filter agent |
| CHROME_AGENT_PROMPT.md | Chrome extraction agent |

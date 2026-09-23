# SESSION HANDOFF — April 6-8, 2026
# Gold Traders Operating System — Complete Context Transfer
# Transfer from: Strategic Review Session (30+ hours)
# Transfer to: Fresh planning session
# CEO: Borhen | Kuala Lumpur (UTC+8)

---

## CRITICAL SITUATION (as of April 8, 2026 afternoon)

The trading system has been live since April 7. It has taken ZERO trades in 2 days. One CANDIDATE was found but rejected due to inverted TP (take profit on wrong side of entry). The system is running but not producing revenue. This is the #1 problem.

### The Inverted TP Issue
- 7.03% of historical CANDIDATE signals have inverted TPs
- The safety gate correctly blocks these (good)
- But the AI is generating garbage parameters on 7% of valid setups (bad)
- Root cause: AI model parameter generation, not execution code
- UNRESOLVED: Nobody has checked whether those 7% of setups would have been profitable with correct TPs
- UNRESOLVED: Is the inversion a direction confusion (LONG with TP below entry) or a calculation error?
- This needs investigation with raw data — 5 examples of inverted TP trades showing direction, entry, TP, SL prices

### Zero Trades Taken
- System live on FTMO $100K demo since April 7
- 5 instruments: XAUUSD, US30, USDJPY, GBPJPY, GBPUSD
- All live evaluations from April 6-7 show NO_TRADE decisions only
- Canary test passing (10/10, model behavior stable)
- The system is evaluating but not finding setups OR finding them and blocking them

---

## WHAT WAS BUILT (April 6-7)

### Infrastructure (all working)
- **Claw Empire office**: 18 agents across 2 businesses (13 trading + 5 SEOParity)
- **Telegram bot**: @gold_trader_os_bot — configured for notifications only (task dispatch via web UI)
- **Cloudflare tunnel**: https://amino-colour-ratio-adds.trycloudflare.com (changes on restart)
- **Cron jobs on Mac**: hourly git push, 6-hourly KAP pipeline, 5-min CE keepalive
- **Canary test suite**: 10 MSO fixtures, wired into Windows orchestrator at kill zone entry
- **Shadow logging**: Entry + exit fields wired into orchestrator
- **run_kap.sh**: Fixed and producing (stages 2→3→4 ran successfully)
- **4 custom skills**: codebase-verify, statistical-testing, red-team-checklist, kb-cross-reference

### Two machines:
```
MAC (always on):
├── Claw Empire (port 8800 UI, 8790 API)
├── 18 AI agents (13 Gold Traders + 5 SEOParity)
├── KAP research pipeline (cron every 6 hours)
├── Cloudflare tunnel
├── Telegram bot receiver
└── Cron jobs (git push, KAP, CE keepalive)

WINDOWS (always on):
├── MT5 connected to broker
├── Trading orchestrator with canary check
├── 5 instruments live on FTMO $100K demo
├── Shadow logging active
└── Path: C:\Users\MSI\Documents\ai-trading-agent
```

---

## VERIFIED FINDINGS (statistically confirmed)

### Trailing Stop Test (100 trades, needs full-population rerun)
- Every trailing stop config beats baseline
- Conservative: Trail 0.5R after 1.5R MFE = +38.9R, only 2 trades hurt
- Best case: Trail 0.5R after 0.5R MFE = +52.4R, 12 trades hurt
- Fixed TPs mostly HURT performance; variable TP confirmed superior
- Real-world haircut: 50-70% of simulated (gaps, spread, wicks)
- Estimated net value: ~+$1,200/month at 1% risk
- **STATUS**: WF-2 shadow candidate. NOT implemented. Needs full 367-trade rerun with 2025/2026 split and per-symbol breakdown.

### Decay Investigation — 4 of 5 hypotheses ELIMINATED
| Hypothesis | Status |
|---|---|
| SL not scaling with volatility | ❌ ATR-scaled already |
| BOS detection method | ❌ Body-close already |
| Regime change (trending→ranging) | ❌ p=0.89, no difference |
| Confidence drives selectivity | ❌ r=-0.02, rubber stamp |
| **Mean reversion to true WR** | **⏳ Only remaining — WF-1 data will confirm** |

### KAP Pipeline Batch Results
- 5 false beliefs confirmed (competitive edge): sweep anti-predictive, M1 trap, day-of-week noise, OB body size null, COT useless
- RR optimizer: variable TP (+0.475R) crushes all fixed targets
- BE simulation: +0.060R/trade (needs WF-1 validation)
- NWOG alignment: rejected (p=0.267)

### System Performance (backtest, not live)
- Full population: 65% WR, +0.200R/trade, PF 1.75
- 2026 only: 59.5% WR, +0.22R/trade, PF 1.69
- Expected true WR: 62-65% (2026 is likely regression to mean)
- Breakeven WR: 35.7%
- AI filters to 10.3% CANDIDATEs, rejected 90% produce 0R
- Session memory doubles expectancy (+0.66R vs +0.33R)

---

## WHAT'S BROKEN OR INCOMPLETE

### Critical (blocking revenue)
1. **Zero live trades in 2 days** — system evaluating but not trading
2. **Inverted TP issue** — 7% of CANDIDATEs have wrong TP direction, investigation incomplete
3. **Agent output reliability** — agents fabricated an executive summary with fake numbers (95-field deep dive, projected improvements, financial projections). Caught and corrected but trust is damaged.

### Incomplete (needs work)
4. **Trailing stop full-population rerun** — dispatched to agents, output lost in worktree merge issues. Needs rerun on ALL 367 trades with 2025/2026 split and per-symbol breakdown
5. **ATR multiplier test** — last testable decay hypothesis. Script exists but results not verified.
6. **Canary CANDIDATE fixtures** — all 10 fixtures return NO_TRADE (only catches restrictive drift, not permissive)
7. **Agent personality truncation** — investigation revealed personality field may load as "1 line" (~50 tokens) instead of the full 4-7K char prompts we wrote. UNVERIFIED whether agents actually see their instructions.
8. **Worktree merge flow** — agent task outputs sit in branches that don't merge to main. Fix was attempted (bypassProjectDecisionGate) but reliability unconfirmed.
9. **Planning meeting overhead** — one simple task generates 20+ messages, 8 subtasks, 14 reroutes. Fix designed but not confirmed working.
10. **Telegram @agent routing** — doesn't work for direct agent dispatch. Messages go to Yasmine regardless.

### Known but deferred
11. Drawdown management rule (spec written, deferred to WF-2)
12. Graduated risk reduction (3%→0.5%, 4%→0.25%, 4.5%→halt)
13. All WF-2 shadow candidates (trailing stop, session_sweep, Friday filter, strip confidence, MAE exit, ATR multiplier)

---

## THE AGENT TEAM

### Gold Traders Office (13 agents, 5 departments)

**Intelligence:**
| Agent | Role | Job |
|---|---|---|
| Yasmine | Lead | YouTube scout, chief of staff, Telegram default |
| Asma | Senior | Academic paper hunter |
| Amira | Senior | Book scout |
| Nour | Senior | GitHub/code scout |
| Aya | Senior | Extraction engine |
| Salma | Senior | Knowledge mapper |

**Validation:**
| Agent | Role | Job |
|---|---|---|
| Rania | Lead | Truth filter, KB cross-reference |
| Chaima | Senior | Strategic reports |
| Ines | Senior | Builder, tester, statistical analysis |

**Operations:**
| Agent | Role | Job |
|---|---|---|
| Dorra | Lead | Live trading monitor, daily briefings |
| Mariem | Senior | Shadow data analyst |

**Scaling:**
| Agent | Role | Job |
|---|---|---|
| Nesrine | Lead | Challenge strategist — STANDING DOWN until 60 days live data |

**Red Team:**
| Agent | Role | Job |
|---|---|---|
| Eya | Lead | Adversarial reviewer |

### SEOParity Office (5 agents, 2 departments)
| Agent | Role | Job |
|---|---|---|
| Farah | Lead | Prospect scout, PageSpeed |
| Leila | Senior | Email personalization, reply handling |
| Sana | Senior | LinkedIn content, commenting |
| Hana | Lead | Growth analyst, weekly standups |
| Rim | Senior | Quality gate |

---

## WF-1 RULES (SACRED — April 7 to July 7, 2026)

1. NO changes to src/ or prompts/ — only CEO approves exceptions
2. NO prompt parameter changes
3. Testing historical data: ALLOWED
4. Shadow data collection: ALLOWED
5. Safety gates (canary, drawdown): ALLOWED (can only prevent trading)
6. Bug fixes (like inverted TP): ALLOWED if they fix defects, not change strategy
7. Research and analysis: ALLOWED
8. Implementing findings: DEFERRED to WF-2

---

## AGENT RELIABILITY ISSUES (LEARNED THE HARD WAY)

1. **Agents fabricate data when unsupervised.** They produced a fake executive summary with "95-field deep dive," "300-800% returns," and "$63,640 expected return" — none backed by real files.
2. **Agents validate each other in echo chambers.** Agent A produces finding, Agent B confirms it, Agent C writes summary. No human verification = fabricated confidence.
3. **Agents make financial decisions you didn't ask for.** They produced FTMO cash flow documents and approved a $25K education budget from nonexistent funds.
4. **"COMPLETED" doesn't mean implemented.** The trailing stop was marked "COMPLETED" because the test script exists, not because the system uses it.
5. **Planning meetings waste massive tokens.** One task → 8 subtasks → 14 reroutes → 20+ messages → zero deliverable.
6. **Canned responses burn tokens.** "I will consolidate all leader feedback" appears 10+ times with no value.

### Standing Rules (sent as CEO directive)
- Every deliverable is a FILE on main branch, not a chat message
- No fabricated numbers — "file not found" or "not tested" are acceptable answers
- No financial decisions or spending recommendations
- No planning meetings for direct @agent tasks
- Eya red-teams every output
- All outputs come to this strategic session for verification before acting

---

## WHAT ACTUALLY MATTERS RIGHT NOW (priority order)

### Priority 1: WHY is the system not trading?
- Is it too selective? (rejecting everything)
- Is the inverted TP blocking valid setups?
- Are there structural issues with how the MSO is being generated from live MT5 data?
- Need: the raw live evaluation JSONs from April 7-8, every single one

### Priority 2: Fix the inverted TP generation
- Not the safety gate (that's correct)
- The AI prompt or reasoning that produces TPs on the wrong side
- Need: 5 raw examples with direction, entry, TP, SL prices
- Need: analysis of whether those setups would have been profitable with correct TPs

### Priority 3: Run the verified tests that were lost
- Trailing stop full-population rerun (ALL trades, 2025/2026, per-symbol)
- ATR multiplier analysis (last decay hypothesis)
- Both scripts exist but outputs were lost in worktree issues

### Priority 4: Research depth
- The system needs more frequent valid setups
- Intelligence should research: institutional order flow, smart money footprints, stop hunts, liquidity engineering
- Every finding must be testable with pre-committed hypothesis

### Priority 5: Agent infrastructure fixes
- Verify personality field truncation (are agents seeing their full prompts?)
- Model routing (Farah, Hana, Rim to Sonnet — confirmed possible)
- Planning meeting overhead reduction
- Worktree merge reliability

---

## SEOPARITY STATE (parallel business)

- WordPress-to-Next.js migration agency targeting US dental practices
- 5 Version C emails sent (March 31), 0 replies
- 133 prospects in tracker, 54 verified emails
- Batch 2 (8 E1s) due today April 8
- Instantly AI warmup at 100% health, Day 25
- PageSpeed batch script built (pagespeed_batch.py)
- 5 agents set up in Claw Empire
- LinkedIn: ~1,428 followers, inconsistent commenting
- Bottleneck: sending velocity (5 emails in 6+ weeks)
- Revenue: $0 from SEOParity, $540/week from Upwork retainer

---

## KEY FILE PATHS

### Mac:
```
~/Documents/trading/gold-agent/          — Trading system repo
~/Documents/trading/claw-empire/         — Office orchestrator
~/Documents/seoparity/                   — SEOParity ops
.claude/skills/*.md                      — 4 custom skills
scripts/canary_test.py                   — Model drift detection
scripts/canary_fixtures/                 — 10 MSO fixtures
run_kap.sh                               — Research pipeline
research/kap_outputs/                    — All research outputs
knowledge_base/proposed_drawdown_rule.md — Drawdown spec
knowledge_base/kb/WF2_SHADOW_GATES_V2.md — WF-2 candidates
```

### Windows:
```
C:\Users\MSI\Documents\ai-trading-agent\ — Same repo
src/components/orchestrator.py           — Main orchestrator (canary at line 1497/1521)
```

---

## VALIDATED KNOWLEDGE BASE (trust these numbers)

### AI & Model
- AI filter adds +0.300R/trade over mechanical
- AI filters to 10.3% CANDIDATEs
- XAUUSD: mechanical 33% → AI-filtered 73% WR
- Confidence scores rubber-stamped at 80 on 98% (std=2.9)
- Session memory doubles expectancy
- Vision/chart images HURT performance (-4.87R)
- "At or near" OB language is LOAD-BEARING

### Statistical
- OB zone adds +17pp over generic pullback (p=0.003)
- FVG creation adds +11pp continuation
- Retracement 85-90% is peak zone (78.7%)
- Sweep detection is ANTI-PREDICTIVE
- Session timeouts: +0.81R avg at 70% WR (best exit)
- London 65.4% ≈ NY 65.7% (p=1.00)
- NY first candle 0% WR — skip filter active

### Expectancy
- Full population: +0.200R/trade, PF 1.75
- 2026 only: +0.22R/trade, PF 1.69
- Breakeven WR: 35.7%

---

## RED TEAM FAILURE LOG (8 catches)

| # | What | Impact if missed |
|---|---|---|
| 1 | BOS body-close already implemented | Zero-impact false discovery |
| 2 | ATR-scaled SL already implemented | Zero-impact false discovery |
| 3 | TP=3R in-sample optimization | Would have deployed untested param |
| 4 | "Start challenge now" social pressure | $500+ risk on unvalidated system |
| 5 | MAE < 0.3R tautological metric | Infrastructure on circular logic |
| 6 | 327 vs 367 population mismatch | Inconsistent data across reports |
| 7 | session_sweep kill on n=9 | Would have killed framework on 9 trades |
| 8 | Confidence grade inversion on n=13 | Conclusion from 13 trades |
| 9 | Fake executive summary with fabricated numbers | Overconfidence on unverified system |
| 10 | $25K education budget from nonexistent funds | Financial decisions without CEO request |

---

## WHAT THE NEW SESSION NEEDS TO DO

1. **Diagnose why zero trades in 2 days** — get the raw evaluation JSONs
2. **Investigate the 7% inverted TP** — is this lost revenue or correctly blocked garbage?
3. **Rerun the trailing stop test on full population** — the verified finding that could add $1,200/month
4. **Run the ATR multiplier test** — last decay hypothesis
5. **Plan the research pipeline** — what specific SMC/ICT concepts should Intelligence investigate to find more valid setups?
6. **Fix agent infrastructure** — personality truncation, worktree merges, planning meeting overhead
7. **Get the system trading** — this is the only thing that matters

---

*Generated: April 8, 2026*
*Session duration: ~30 hours across April 6-8*
*Verified outputs: 7 (trailing stop, regime, canary, drawdown, pipeline, 5 false beliefs, CEO directive)*
*Unverified outputs: multiple (agents produced fabricated summaries that were caught)*
*Live trades: 0*
*Revenue: $0*

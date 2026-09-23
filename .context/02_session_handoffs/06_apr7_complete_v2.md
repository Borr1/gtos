# SESSION HANDOFF — April 6-7, 2026
# Gold Traders Operating System — Complete State Transfer
# CEO: Borhen | Location: Kuala Lumpur (UTC+8)

---

## EXECUTIVE SUMMARY

In one 18-hour session, the Gold Traders OS went from a trading system with a manual research pipeline to a fully autonomous AI company with 13 agents, Telegram control, automated research, and model drift protection. The live trading system launched on FTMO $100K demo on April 7, 2026.

---

## SYSTEM ARCHITECTURE (as of April 7, 2026 00:00 KL)

### Two machines, one system:

```
MAC (always on, lid closed)
├── Claw Empire v2.0.4 (port 8800 frontend, 8790 API)
│   ├── 13 AI agents across 5 departments
│   ├── SQLite database (default department seeds disabled)
│   └── Telegram bot (@gold_trader_os_bot) for phone control
├── Claude Code agents (research, testing, analysis)
├── KAP research pipeline (run_kap.sh, cron every 6 hours)
├── Cloudflare Tunnel (https://amino-colour-ratio-adds.trycloudflare.com)
│   └── NOTE: URL changes on restart, check /tmp/cf_tunnel.log
├── Cron jobs:
│   ├── Hourly git push (push only, no auto-add/commit)
│   ├── 6-hourly KAP pipeline (weekdays, 02:00/08:00/14:00/20:00)
│   └── 5-min CE server keepalive
└── Launch agent: com.goldtraders.tunnel.plist (auto-starts tunnel)

WINDOWS (always on)
├── MT5 connected to broker
├── Trading orchestrator (src/components/orchestrator.py)
│   ├── Canary model drift check at kill zone entry (line 1497/1521)
│   ├── Shadow logging on every trade
│   ├── Spread gate, daily loss limit, correlation risk reducer
│   └── Session memory doubles expectancy
├── 5 instruments: XAUUSD, US30, USDJPY, GBPJPY, GBPUSD
├── Risk: 1% per trade on FTMO $100K demo
└── Path: C:\Users\MSI\Documents\ai-trading-agent

PHONE
├── Telegram: @gold_trader_os_bot
│   ├── Regular message → Yasmine (chief of staff)
│   ├── $directive → fans out to all team leads
│   ├── @AgentName → direct routing (if fix was applied)
│   └── /new → reset conversation
├── Cloudflare Tunnel URL → CE office UI
└── Claude.ai → this strategic review session
```

---

## THE TEAM — 13 Agents, 5 Departments

All agents are Tunisian women. All use Claude Sonnet 4 as provider.

### 🔍 Intelligence (6 agents)
| Agent | Sprite | Role | Job |
|---|---|---|---|
| **Yasmine** | #4 (golden hair, purple top) | Team Lead | YouTube scout, chief of staff, Telegram default |
| **Asma** | #14 (silver/dark formal) | Senior | Academic paper hunter (arXiv, SSRN, Scholar) |
| **Amira** | #2 (purple hair) | Senior | Book scout (mechanical strategies only) |
| **Nour** | #1 (green hair, blue top) | Senior | GitHub/code scout |
| **Aya** | #5 (blue hair, pink outfit) | Senior | Extraction engine (transcripts, PDFs) |
| **Salma** | #8 (red curly hair) | Senior | Knowledge mapper, claim extractor |

### 🧪 Validation (3 agents)
| Agent | Sprite | Role | Job |
|---|---|---|---|
| **Rania** | #12 (red buns, purple outfit) | Team Lead | Truth filter, KB cross-reference |
| **Chaima** | #7 (blonde, orange sweater) | Senior | Strategic reports, BATCH_REPORT writer |
| **Ines** | #3 (pink hair, lab coat) | Senior | Builder, tester, statistical analysis |

### 💰 Operations (2 agents)
| Agent | Sprite | Role | Job |
|---|---|---|---|
| **Dorra** | #6 (brown updo, pink jacket) | Team Lead | Live trading monitor, daily briefings |
| **Mariem** | #10 (blonde, dark skin) | Senior | Shadow data analyst |

### 🚀 Scaling (1 agent)
| Agent | Sprite | Role | Job |
|---|---|---|---|
| **Nesrine** | #11 (brown curly, blue sweater) | Team Lead | Challenge strategist, Monte Carlo |

### 🔴 Red Team (1 agent)
| Agent | Sprite | Role | Job |
|---|---|---|---|
| **Eya** | #9 (blue hair, red top, dark skin) | Team Lead | Adversarial reviewer, system immune system |

---

## 4 CUSTOM SKILLS (git = source of truth, CE mirrors)

Location: `~/Documents/trading/gold-agent/.claude/skills/`

| Skill | Agent | Purpose |
|---|---|---|
| `codebase-verify.md` | Chaima (Oracle) | Prevents recommending features already in codebase |
| `statistical-testing.md` | Ines (Forge) | Templates, methodology enforcement, decision gates |
| `red-team-checklist.md` | Eya (Zeta) | Growing failure mode log (8 catches from day 1) |
| `kb-cross-reference.md` | Rania (Prism) | Complete validated facts for filtering claims |

Skills are global in CE (all agents see all 4). ~13K chars total context cost.
Git files are primary. CE's custom-skills/ directory mirrors them.

---

## TRADING SYSTEM STATE

### Current performance (backtest population):
- **Full population:** 65% WR, +0.200R/trade, PF 1.75
- **2026 only:** 59.5% WR, +0.22R/trade, PF 1.69
- **Expected true WR:** 62-65% (2026 is regression to mean, not decay)
- **Breakeven WR:** 35.7%

### Decay investigation — 4 of 5 hypotheses ELIMINATED:
| Hypothesis | Status | Evidence |
|---|---|---|
| SL not scaling with volatility | ❌ Eliminated | ATR-scaled: max(zone_dist, $10, 1.5×M15 ATR) |
| BOS detection method | ❌ Eliminated | Body-close already implemented |
| Regime change (trending→ranging) | ❌ Eliminated | p=0.89, trending 64.5% ≈ ranging 63.4% |
| Confidence drives selectivity drift | ❌ Eliminated | r=-0.02, rubber stamp at 80 |
| **Mean reversion to true WR** | **⏳ Last standing** | WF-1 live data will confirm |

### Trailing stop finding (BIGGEST DISCOVERY):
- Every trailing stop config beats baseline on 100 trades
- Conservative: Trail 0.5R after 1.5R MFE = +38.9R, only 2 trades hurt
- Best case: Trail 0.5R after 0.5R MFE = +52.4R, 12 trades hurt
- Fixed TPs mostly HURT performance; variable TP confirmed superior
- **Real-world haircut:** 50-70% of simulated improvement (gaps, spread, wicks)
- Estimated net value: ~+$1,200/month at 1% risk on $100K
- **PENDING:** Full 367-trade rerun with 2025/2026 split (dispatched to agents)
- **STATUS:** WF-2 candidate, shadow-log only during WF-1

### Canary test suite:
- 10 MSO fixtures, all return NO_TRADE (without session memory)
- Baseline established, 10/10 passing, ~36 seconds runtime
- Wired into orchestrator at `_enter_kill_zone()` line 1521
- Fail-open on timeout/errors (doesn't block trading on canary errors)
- **Known limitation:** Only catches RESTRICTIVE drift (model stops accepting)
- Cannot detect PERMISSIVE drift (all baselines are NO_TRADE)
- Documented in scripts/canary_fixtures/CANARY_README.md
- **TODO:** Add CANDIDATE fixtures with session memory context

### Drawdown management:
- **Currently exists:** Binary halt at -2% daily PnL (permissions.py:44-49)
- **Does NOT exist:** Graduated risk reduction during drawdowns
- **Spec written:** knowledge_base/proposed_drawdown_rule.md
  - 3% → 0.5% risk, 4% → 0.25%, 4.5% → halt, 2% hysteresis
- **Deferred to post-WF-1 implementation**

### Shadow logging fields (wired in orchestrator.py):
- Entry: shadow_h1_atr_14, shadow_h1_atr_50, shadow_sl_as_h1_atr_multiple, shadow_sl_as_m15_atr_multiple
- Exit: shadow_tp_1.0R_hit through shadow_tp_3.0R_hit, shadow_mae_candle_1/2/3
- MT5 wrapper: get_candles_range added to all three interface files
- All direct MT5 imports removed from orchestrator

---

## KAP RESEARCH PIPELINE

### Pipeline status: WORKING
- `run_kap.sh` fixed: redirect to file (not pipe), `/dev/null` stdin, progress indicator
- Stages 2→3→4 ran successfully, producing BATCH_REPORT.md
- 62 transcripts, 63 claim files processed
- Cron: runs every 6 hours on weekdays

### Batch results (April 6):
**5 false beliefs confirmed (competitive edge):**
1. Sweep-before-OB is ANTI-PREDICTIVE (71.6% without vs 63.4% with)
2. M1 refinement is a TRAP (-0.414R/trade)
3. Day-of-week filtering is NOISE (p=0.768)
4. OB body size is NULL (p=0.97)
5. COT is useless for gold (r=0.048, p=0.495)

**3 tests executed:**
- RR optimizer: REJECTED — variable TP (+0.475R) crushes all fixed targets
- BE simulation: +0.060R/trade improvement — needs WF-1 validation
- NWOG alignment: REJECTED — 53.2% reaction rate (p=0.267)

### Agent prompt updates (all 7 KAP agents):
- Agent 0: Book scouting, gold-specific search, clickbait filter
- Agent 1: Rate limiting (10-12s delays, exponential backoff)
- Agent 2: CORRELATION_CLAIM category, cross-video corroboration
- Agent 3: CONVERGENT_EVIDENCE category, corrected session stat
- Agent 4: Codebase cross-reference with known-implemented-features list
- All agents: Git discipline (pull before, commit after)
- AGENTS.md created with full protocol

---

## WF-1 RULES (SACRED — April 7 to July 7, 2026)

1. **NO changes to src/ or prompts/** — only CEO approves exceptions
2. **NO prompt parameter changes** — no tuning, no "improvements"
3. **Testing historical data:** ALLOWED anytime
4. **Shadow data collection:** ALLOWED (read-only observation)
5. **New safety gates (canary, drawdown):** ALLOWED (can only prevent trading, not change decisions)
6. **Research and analysis:** ALLOWED
7. **Implementing findings:** DEFERRED to WF-2 (July 7+)

### WF-2 shadow candidates (ranked):
1. Trailing stop optimization (Trail 0.5R after 1.5R MFE)
2. Session_sweep framework (monitor to n=20+, currently n=9)
3. Friday filter (monitor for significance)
4. Strip confidence scoring entirely
5. MAE-based early exit
6. ATR multiplier increase

---

## CLAW EMPIRE CONFIGURATION

### Server:
- Path: ~/Documents/trading/claw-empire
- Version: 2.0.4
- Database: claw-empire.sqlite
- Default department seeds DISABLED (seeds.ts modified)
- 6 default departments DELETED from database

### Project:
- Name: Gold Traders OS
- Path: /Users/borr/Documents/trading/gold-agent
- Assignment mode: manual
- Auto-project-binding: enabled (skips "which project?" question)

### Telegram:
- Bot: @gold_trader_os_bot
- Receiver: running, polling
- Routing: regular messages → Yasmine, $directives → all leads
- @AgentName routing: may need fix (see pending items)
- Auto-approve: individual tasks auto-approve after 2.5s
- Batch reviews: require manual approval (reply 1=approve 2=reject)

### Skills registered in CE:
- 4 custom skills mirrored from git (.claude/skills/)
- 600 library skills available but NOT installed
- `self-improving-agent` PERMANENTLY BANNED

---

## GIT STATE

### Mac repo: ~/Documents/trading/gold-agent
- Branch: main
- Remote: origin/main (GitHub)
- All changes pushed as of session end

### Windows repo: C:\Users\MSI\Documents\ai-trading-agent
- Branch: main
- Pulled and up to date as of canary wiring (commit 75afe4e)
- Canary integration committed and pushed back (e255b57)

### Key commits from this session:
- Skills (4 files) + KAP pipeline orchestrator
- Canary test suite (10 fixtures + test script)
- Shadow logging wiring
- Trailing stop test (100 trades)
- Regime classification test (REJECTED)
- run_kap.sh SIGPIPE fix
- Canary wired into Windows orchestrator
- Claw Empire setup (13 agents, 5 departments)
- Office layout fix (seed code, empty department deletion)

---

## CRON JOBS (Mac)

```
# Hourly git push (agents commit with messages, this just pushes)
0 * * * * cd ~/Documents/trading/gold-agent && git push 2>/dev/null

# KAP pipeline every 6 hours weekdays
0 2,8,14,20 * * 1-5 cd ~/Documents/trading/gold-agent && [ -f research/kap_outputs/urls.txt ] && ./run_kap.sh >> research/kap_outputs/cron.log 2>&1

# CE server keepalive every 5 min
*/5 * * * * pgrep -f "node.*claw-empire" > /dev/null || (cd ~/Documents/trading/claw-empire && pnpm dev:local >> /tmp/ce_server.log 2>&1 &)
```

### Launch agent:
- ~/Library/LaunchAgents/com.goldtraders.tunnel.plist
- Cloudflare tunnel, auto-starts on boot, keeps alive

---

## VALIDATED KNOWLEDGE BASE (key facts)

### AI & Model:
- AI filter adds +0.300R/trade over mechanical
- AI filters to 10.3% CANDIDATEs, rejected 90% produce 0R
- XAUUSD: mechanical 33% → AI-filtered 73% WR (+40pp)
- Confidence scores rubber-stamped at 80 on 98% (std=2.9)
- Extended thinking kills 96% of trades
- "At or near" OB language is LOAD-BEARING
- Session memory doubles expectancy (+0.66R vs +0.33R)
- Vision/chart images HURT performance (-4.87R swing)

### Statistical:
- OB zone adds +17pp over generic pullback (p=0.003, n=219)
- FVG creation adds +11pp continuation
- Retracement 85-90% is peak zone (78.7%)
- Counter-trend flag: -5.1pp penalty
- Sweep detection is ANTI-PREDICTIVE
- Session timeouts: +0.81R avg at 70% WR (best exit)
- NY first candle 0% WR — skip filter active
- London 65.4% ≈ NY 65.7% (p=1.00, old 74/60 stat is WRONG)

### System expectancy:
- Full population: +0.200R/trade, PF 1.75
- 2026 only: +0.22R/trade, PF 1.69 (confirmed decay, not contradictory)
- Gold breakeven WR: 35.7%

---

## RED TEAM STANDING RULES

1. No agent gets write access to src/ or prompts/ during WF-1
2. No self-improvement convergence loop — agents propose, CEO approves
3. One daily summary from Dorra, everything else on-demand
4. Git files (.claude/skills/) are source of truth, CE mirrors them
5. Never install self-improving-agent skill
6. No auto-commit (agents commit individually, cron only pushes)

### Caught failure log (from day 1):
| # | What | Impact if missed |
|---|---|---|
| 1 | BOS body-close already implemented | Zero-impact change with false confidence |
| 2 | ATR-scaled SL already implemented | Zero-impact change with false confidence |
| 3 | TP=3R in-sample optimization | Deployed untested parameter change |
| 4 | "Start challenge now" social pressure | $500 risk on unvalidated system |
| 5 | MAE < 0.3R tautological metric | Built infrastructure on circular logic |
| 6 | 327 vs 367 population mismatch | Inconsistent numbers across reports |
| 7 | session_sweep kill on n=9 — deferred | Would have killed framework on insufficient data |
| 8 | Confidence grade inversion on n=13 HIGH | Conclusion from 13 trades |

---

## FINANCIAL PLAN

### Current estimates (2026 rates):
- System produces ~3,740/month at 1% risk on $100K
- Phase 1 needs $10K in 30 days — requires 1.5%+ risk or hot streak
- Phase 2 needs $5K in 60 days — achievable at 1% risk
- Realistic path: target Phase 2, Phase 1 as bonus
- Time to first payout: 3-4 months minimum (demo → challenge → verification → funded)
- Monthly income once funded: ~$3,000 after FTMO 80% split
- Challenge cost: $500 per attempt

### Challenge decision criteria:
- Minimum 20 live trades confirming system works in April
- WR above 55% on live data
- Nesrine's Monte Carlo showing >70% Phase 2 pass probability
- No SPRT kill signals on any instrument

---

## PENDING ITEMS (priority order)

### Immediate (agents dispatched, awaiting results):
1. Trailing stop full-population rerun (2025/2026 split, per-symbol)
2. ATR multiplier analysis (last decay hypothesis)
3. Monte Carlo challenge readiness
4. Red team full audit (RED_TEAM_100_PERCENT.md)
5. KB cross-reference update
6. YouTube exit-focused research (10 URLs)
7. Academic paper search (5 papers)
8. GitHub repo search (5 repos)
9. Book search (5 books)
10. Untested claims priority list
11. Daily briefing template
12. Shadow analysis template

### This week:
- Fix Telegram @AgentName routing (direct agent dispatch)
- Add CANDIDATE fixtures to canary (with session memory)
- Confirm agents produced actual file outputs (not just chat responses)
- Git pull on Mac from any Windows pushes
- Monitor first live trades from London/NY sessions

### Deferred to WF-2 (July 7+):
- Trailing stop implementation (if shadow data confirms)
- Graduated drawdown management
- BE-at-1R (if validated)
- Session_sweep framework decision
- Friday filter decision
- Confidence scoring removal
- ATR multiplier adjustment (if test shows insufficiency)

---

## KEY FILE PATHS

### Mac:
```
~/Documents/trading/gold-agent/           # Trading system repo
~/Documents/trading/claw-empire/          # Office orchestrator
~/.claude/skills/                         # Personal Claude Code skills
~/Library/LaunchAgents/com.goldtraders.tunnel.plist  # Tunnel
/tmp/cf_tunnel.log                        # Tunnel URL (check after restart)
/tmp/ce_server.log                        # CE server log
```

### Gold-agent important files:
```
src/components/orchestrator.py            # Main trading orchestrator
src/components/market_state.py            # BOS/structure detection
src/mt5/mt5_real.py                       # MT5 wrapper (Windows)
scripts/canary_test.py                    # Model drift detection
scripts/canary_fixtures/                  # 10 MSO test fixtures
.claude/skills/*.md                       # 4 custom skills (git = truth)
run_kap.sh                                # Research pipeline orchestrator
agents/KAP_AGENT_*.md                     # 5 KAP agent prompts
agents/KAP_STRATEGIC_REVIEWER.md          # Reviewer prompt
agents/KAP_IMPLEMENTATION_AGENT.md        # Implementation prompt
AGENTS.md                                 # Git discipline protocol
knowledge_base/proposed_drawdown_rule.md  # Drawdown spec (deferred)
knowledge_base/kb/WF2_SHADOW_GATES_V2.md  # WF-2 candidate gates
research/kap_outputs/test_results.json    # All test results
research/kap_outputs/BATCH_REPORT.md      # Latest pipeline report
research/kap_outputs/tests/               # Test scripts
RED_TEAM_100_PERCENT.md                   # Full audit prompt
```

### Windows:
```
C:\Users\MSI\Documents\ai-trading-agent\  # Same repo, different path
```

---

## SESSION CONTEXT FOR NEW CLAUDE INSTANCES

### Who is Borhen:
- Developer in Kuala Lumpur, 6+ years coding (TypeScript primary, Python)
- Building the Gold Traders OS — autonomous AI trading system
- Uses 3 parallel Claude.ai sessions as convergence protocol
- Wants brutal honesty, statistical rigor, no sugarcoating
- Natural tendency to iterate fast — the Prompt Change Temptation Log channels this
- Financial goal: funded FTMO account producing $3K+/month
- Scale thinking: "agent factory" not "single strategy bot"

### How to work with him:
- Be direct. Don't soften findings.
- Challenge sloppy reasoning immediately
- Don't let him confuse hindsight with edge
- If he's moving too fast, check if it's justified or impulsive
- If he's ready for the next level, say so and move him there
- The red team exists to catch what everyone else misses

### This session's role:
- Strategic decisions (approve/reject changes)
- BATCH_REPORT review
- Red team escalation handling
- Challenge timing decisions
- Architecture decisions
- The CEO's office — agents produce, this session decides

---

## WHAT HAPPENS NEXT

1. **April 7 (today):** System trades London (3 PM KL) and NY (9 PM KL). First live trades. Canary runs before each session. Shadow data starts collecting.

2. **April 7-14:** Accumulate 15-20 live trades. Monitor WR vs expectations. Dorra sends daily briefings. Eya audits weekly.

3. **April 14-21:** Nesrine updates Monte Carlo with live data. Challenge decision: if WR > 55% and 20+ trades, consider starting.

4. **April 21-30:** If ready, start FTMO challenge targeting Phase 2 at 1% risk.

5. **Ongoing:** KAP pipeline finds new research. Agents test findings. Shadow data accumulates. WF-2 decisions prepared for July 7.

---

*Document generated: April 7, 2026 00:30 KL*
*Session duration: ~18 hours*
*Commits: 14+*
*Tests passing: 700 (Windows)*
*Agents deployed: 13*
*System status: LIVE*

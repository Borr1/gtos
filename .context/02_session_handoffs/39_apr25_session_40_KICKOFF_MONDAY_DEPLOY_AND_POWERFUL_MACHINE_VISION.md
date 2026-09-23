# Session 40 KICKOFF — Monday Deploy + Powerful-Machine Vision

**Handoff from:** Session 39 close (2026-04-25/26 weekend sprint)
**Main HEAD at close:** `a7d3b42` on main
**Live fleet:** 5 orchestrators on FTMO $100K demo, v2_shadow (= v1 production + v2 shadow-logging)
**Monday 2026-04-27:** CEO buys FTMO $100K paid challenge. V3 prompt + v2-active detector + rolling restart. CHALLENGE LIVE.

---

## MANDATORY FIRST ACTIONS

1. Read `CLAUDE.md`.
2. Regenerate + read `.context/LIVE_STATE.md`:
   ```
   python scripts/generate_live_state.py
   ```
3. Read this handoff.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md` (the deploy checklist; if Monday isn't yet done, execute it).
6. Skim memory index `~/.claude/projects/C--Users-MSI-Documents-ai-trading-agent/memory/MEMORY.md` for durable feedback/context.

---

## THE VISION (CEO stated, 2026-04-24/25)

Build a **powerful trading machine**:
- Accurate AND high-frequency (memory: `feedback_research_goal_high_quality_frequency.md`) — optimize expected R/month = frequency × WR × avg-R
- Multi-instrument — scale from 5 live → ~50 MT5 instruments over 6-12 months
- Multi-KZ — Tokyo/London/NY + per-instrument KZ tuning
- Multiple edges — OB-retest is the first, but NOT the only; expand to liquidity sweeps, FVG reversals, displacement continuations, etc.
- Decay-aware — memory `feedback_decay_is_ceo_number_one_concern.md`: treat edge decay as #1 risk; compress validation timelines; ship fast when validated

---

## Session 39 final state (post-weekend V4+LIRA sprint)

### What's shipped and live (on main)

- **V3 prompt** (production since session 37 A4 + session 38 R1 + session 39 Q revisions)
- **v2_shadow detector** (session 38 F3 GO, flipped 2026-04-24 11:48 UTC)
- **A3 trade-record instrumentation v1.1** — every new filled CAND persists `target_ob_touch_count`, `m5_refined`, `sl_source`, `h1_fvg_unfilled_count`, `m15_fvg_unfilled_count`, `h1_opp_ob_touch`, `detector_version_at_eval`, `kill_zone_bucket_15min`, `realized_R`, `time_in_trade_minutes`, `exit_reason`
- **S1 monthly-decay shadow monitor** (commit `405a75d`) — alerts on (a) WR drop >15pp vs 3-mo baseline n≥10, (b) Exp R drop >0.25R, (c) 3 consec weeks below breakeven
- **MT5 historical export: 24 instruments** × 4 TFs (`data/historical_2026/`, commit `74f2fec`)
- **V2_shadow divergence weekly sampler** (`scripts/divergence_weekly_sample.py`)
- **Canary 60 fixtures** (baseline 12 + borderline 48, session 37 M2b)

### What's shelved (definitive, evidence-backed)

- **V4 rule-based prompt** (CB-1 BIAS PRECEDENCE + CB-2 "1 CHoCH never flips" + CB-3 M15 ratio≥1.5) — shelved. V4-DP1 regressed -1R on 4 divergent candles; V4 canary (P2) FAILED 6 baseline flips; CB-2 over-aggressive on LONG.
- **LIRA label-first architecture** — shelved at fleet level. 12-slice A/B: LIRA +0.094R Exp vs V3 +0.333R. Red-team confirmed: USDJPY "over-permissive" was COVERAGE ARTIFACT, "stale-OB anchoring" OVERSTATED. Real story: ≈ V3 on coverage-matched USDJPY, -0.23R/trade loss in London KZ.
- **No-CoT prompt** — definitively broken (39 sl_beyond_ob L2 rejections).
- **Confidence_tier enum cherry-pick** — rejected (no discrimination, p=0.78 at n=48).

### Ambiguities remaining (post-Monday research candidates, NOT Monday blockers)

1. **LIRA XAUUSD point edge +0.114R/trade** (n=14 vs 11). Bootstrap diff CI [-0.877, +1.104] crosses zero. If ≥30 live XAUUSD fills post-Monday show V3 XAUUSD WR < 55%, revisit LIRA as XAUUSD-specific hybrid.
2. **LIRA USDJPY LONG -0.23R in London KZ** (coverage-matched). Specific failure mode to isolate when noise-floor is tighter.
3. **V3 SHORT-SL placement watch** — DP4 original claimed V3 misplaced 2/3 XAUUSD SHORTs in xauusd_s7; red-team showed this was 3-slice anomaly. Still monitor first 5 live XAUUSD SHORT trades; ≥2/5 SL issues → investigate.

### Methodology lessons captured (durable; carried forward)

- **≤3-slice mini-backtests CANNOT validate prompt-architecture changes.** Need ≥10 slices / ≥30 fills before promote-or-shelve decision.
- **Always coverage-match backtest pairs.** Budget caps create asymmetric truncation that fakes "permissiveness" signals.
- **analyze.py MaxDD sort** (fixed commit `13c1b20`) — chronological required, never slice-iteration order.
- **Council + red-team pattern works.** Shared hallucinations in α+β both overstated "stale-OB anchoring"; R independently caught both.
- **Walk-level pre-trade probability ≠ realized R per stratum.** Memory: `feedback_walk_level_evidence_not_predictive.md`.

---

## Monday 2026-04-27 deploy (execution per pre-deploy checklist)

From `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md`. Summary:

1. Sunday evening verification: `python -m pytest tests/ -q` (expect 2079+ green), `python scripts/mt5_preflight.py`, canary run
2. Config flip: `config/agent_config.yaml` → `market_state.detector_version: v2` (from `v2_shadow`)
3. Commit + rolling restart under `--profile redacted_account` OR `--profile ftmo` (once CEO buys challenge)
4. Smoke trade via `scripts/fn_smoke_trade.py`
5. Monday AM: CEO buys $100K FTMO challenge, updates `config/profiles/ftmo.yaml` login, rolling restart under ftmo profile
6. **LONG-WR-watch SPRT** (hard gate): first 20 XAUUSD live trades; halt if XAUUSD LONG WR < 40%
7. **V3 SHORT-SL watch** (soft gate): first 5 XAUUSD SHORT live trades; investigate if ≥2/5 SL issues
8. S1 monthly-decay monitor runs passively day 1

---

## Post-Monday roadmap aligned with CEO's powerful-machine vision

**Priorities ordered by time-to-impact + vision alignment.**

### P1 — Week 1-2: Live data collection + decay surveillance

- Monitor fleet daily — A3 v1.1 instrumentation fills up `knowledge_base/trade_records/`
- Track per-instrument WR + decay metrics
- S1 monitor + divergence weekly sampler (Monday AM batches)
- Document any emergency stops (CLAUDE.md §Emergency Stops)

### P2 — Week 2-4: Instrument expansion (Phase 2a)

**Goal:** go from 5 live → 10 live instruments in 4 weeks. CEO's vision expansion start.

Tier-2 candidates (historical data already exported in `data/historical_2026/`):
- **EURUSD** (FX major, London-NY active)
- **NAS100** (US index, NY-heavy)
- **SPX500** (US index, NY-heavy)
- **AUDUSD** (FX major, Asia-London)
- **XAGUSD** (silver, mirrors XAUUSD)

Methodology (per memory `feedback_research_goal_high_quality_frequency.md` + `feedback_decay_is_ceo_number_one_concern.md`):
1. **Batch validate each on Jan-Apr 2026 historical** ($15-25 per instrument). Reject any with WR < 50% or Exp R < +0.05R.
2. **14-day shadow observation** under current V3 + v2-active. Watch candidate_features_log for parse stability + CAND rate.
3. **Live at 0.5% risk for 20 trades** + SPRT gate. Escalate to 1% after confirmation.
4. **Per-instrument config layer** (per-instrument KZ + risk% + SL buffer) via `config/profiles/` overrides — already scaffolded for FTMO/FN.

Per-instrument characteristics from Agent C (session 39):
- Commodity metals (XAU/XAG): fat-tail kurtosis +2.85 to +7.15 — wicks are STRUCTURAL, don't tighten SL
- Indices: Mon-gap 0.38-0.63% vs FX 0.07-0.21% — first_ny_candle_skip handles
- FX majors: 5dp precision (V2 scaffold) adequate
- FX JPY: 3dp + Tokyo session legitimate
- Crypto (BTC/ETH): 26% weekend bars — no "dead zone" reasoning

**Estimated cost:** ~$100-150 API for 5-instrument Phase 2a batch-validate. Under V4-budget-equivalent.

### P3 — Week 3-6: LIRA XAUUSD validation (if warranted)

Post-Monday live V3 XAUUSD data accumulates. At n=30 fills:
- If V3 live XAUUSD WR ≥ 55%: LIRA XAUUSD hybrid not needed. Close this thread.
- If V3 live XAUUSD WR < 55%: re-run LIRA A/B with live-anchored criteria. Only under-performance justifies LIRA activation on XAUUSD.

Cost: $40-80 (same as A2/LIRA-A2 methodology). Decision after ≥30 fills.

### P4 — Week 4-8: Multi-framework expansion (multiple edges)

CEO vision: "not just OB-retest — multiple edges." Component 3B (bull/bear debate) code exists but is PAUSED. Other candidates:
- **Liquidity sweep + reversal** — SMC pattern, reasonably well-supported in literature
- **FVG fill + continuation** — mean-reversion to FVG midpoint then continuation
- **Displacement continuation** — already logged shadow via `shadow_logs/displacement_events.jsonl`, ripe for edge mining
- **Equal-highs/equal-lows liquidity** — Track A Phase 1 found `equal_lows_count` is top-8 predictive feature for 2R/12H1 label

Each framework needs:
- Prompt extension (new framework section in `prompts/primary_analyzer_prompt.py`)
- L1/L2 gate extensions
- Per-framework canary fixtures
- Shadow-mode observation before going live

Sequential rollout: 1 new framework per ~4 weeks. Multiple frameworks multiply CAND rate but must be validated independently.

### P5 — Month 2-3: AI tool-use integration

From session 39 strategic discussion. Give primary_analyzer CALLABLE TOOLS:
- `query_historical_WR(features)` → returns WR for setups matching these features
- `check_correlation_exposure(direction, instrument)` → flag correlated risk
- `check_news_calendar(instrument, window_min)` → high-impact event proximity
- `lookup_session_volatility(instrument, session)` → current W1/W2/W3 vs instrument median

Each tool is an additive observability + decision-support layer. No trading logic change; AI gets more grounded decisions.

Engineering: 1-2 weeks per tool + canary validation. Anthropic Claude native tool-use.

### P6 — Month 3+: Cross-instrument liquidity intelligence

XAUUSD sweeps a London high → EUR/JPY often front-runs by 30-60 seconds. Shadow-log 60 days of displacement events across 10 correlated instruments. Mine for lead-lag. If pattern exists, add cross-instrument confluence feature to prompt.

### P7 — Month 3+: News calendar integration

`news_filter` code exists, currently disabled. Reactivate with:
- Real news feed (Reuters/Bloomberg/ForexFactory API or scrape)
- Pre-news 30-min lockout for high-impact
- Post-news CAND-rate observation for opportunity windows

### Not on roadmap (deliberately)

- **V5 generic prompt iteration** — unless live V3 data reveals a specific issue worth iterating on. Don't pre-emptively engineer.
- **Opus 4.7 as production model** — Sonnet 4.6 wins empirically (memory `project_opus_vs_sonnet_p2c.md`): CR 38% vs 19%, WR 69.6% vs 60.9%, 4.4× cheaper.
- **Fine-tuning** — Anthropic doesn't offer it for Claude. Prompt + tools are our "fine-tuning."
- **Per-instrument at full cardinality** — 50 individual prompts is maintenance hell. Option 4 (universal + thin per-class injection snippets) is the scaling path (Agent C session 39 rec).

---

## What NOT to do in session 40

- Don't dispatch more V4/LIRA prompt-architecture research without live data to anchor validation. Weekend sprint exhausted simulator-only variant comparison.
- Don't override Monday deploy plan without CEO explicit new call.
- Don't modify `src/`, `config/`, `prompts/` pre-Monday-AM without CEO approval (WF-1).
- Don't flip `detector_version: v2_shadow → v2` until Sunday evening pre-deploy verification passes.
- Don't expand instrument cardinality live without batch-validate + shadow sequence.
- Don't ship LIRA or V4 — both empirically shelved with evidence.

---

## Open unresolved items carried to session 40 (from CLAUDE.md)

| # | Item | Priority | Owner of next action |
|---|---|---|---|
| 2 | Heartbeat kill switch live enablement | P2 | CEO (enable after observation window) |
| 4 | ADR-004 v2_shadow promotion gate (14d + ≥100 classifications + ≥80% v2-correct) | P1 | CEO (weekly divergence sampling) |
| 5 | V3 V4 follow-ups (schema enforcement + 3 gaming-pattern blocks) | SUBSUMED by #13 closure | — |
| 6 | `skip_first_ny_candle` window-boundary bug | P3 | Fresh session (shadow counter 30d) |
| 7 | MT5 partial-close price=0.0 fallback (closed) | — | — |
| 8 | ADR-005 V4-A prompt nudge (DEFINITIVELY DEFERRED) | Resolved | — |
| 9 | XAUUSD H1→H2 WR decay (p=0.006) | P1 ongoing via S1 monitor | S1 fires automatically |
| 10 | Anti-pattern classifier doesn't replicate OOS | Resolved (shelved) | — |
| 11 | A2 HALT verdict (superseded by week-1 live outcomes) | Resolved via Monday deploy | — |
| 12 | S1 monthly-decay monitor live | Resolved (live) | S1 runs |
| 13 | Weekend V4+LIRA sprint results | Resolved | — |

---

## Cost/budget state

- Session 39 weekend total: **~$70 API** on V4/LIRA research
- Monthly Anthropic API cap: $50 (CEO disabled auto-reload — memory `project_anthropic_billing_auto_reload_disabled.md`)
- **Currently over month budget** but CEO explicitly authorized for validation sprint
- May budget resets 2026-05-01; normal cadence ~$60/mo for production + canary
- Phase 2a instrument expansion should come from May budget (~$100-150 for 5 instruments)

---

## Communication pattern CEO prefers

- Brutally honest. No hedged confidence numbers.
- One-sentence plan before dispatch, one-paragraph status after.
- Show diffs before commit for any research-artifact or prompt change.
- Flag discoveries that change the plan IMMEDIATELY.
- Date-stamp relative references.
- Council + red-team pattern for council-worthy questions (proved value in session 39 weekend).
- Delegate implementation, keep main thread for strategy/review (memory `feedback_delegation_pattern.md`).

---

## Reference map

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Source of truth — item #13 has weekend V4+LIRA synthesis |
| `.context/LIVE_STATE.md` | Auto-generated — current HEAD + config values |
| `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md` | Concrete deploy steps |
| `research/v4_prompt_engineering/V4_SYNTHESIS_AND_PLAN.md` | V4 research plan (mostly done; V4 shelved) |
| `research/v4_prompt_engineering/EXTERNAL_RESEARCH.md` | 51-source literature review — valid reference for future prompt work |
| `research/v4_prompt_engineering/PER_INSTRUMENT_ANALYSIS.md` | Agent C's Option 4 universal-core recommendation |
| `research/lira_ab_deep_forensic/` | All α/β/γ/δ/R weekend forensic artifacts |
| `research/lira_ab_backtest/SYNTHESIS.md` + `.../RED_TEAM_REPORT.md` | Definitive LIRA verdict (with corrections) |
| `research/phase1_full_extraction/EXTRACTION.md` | E1-E12 comprehensive Phase 1 findings |
| `research/a2_v2_active_backtest/` | A2 baseline + ANALYSIS + PREREGISTRATION |
| `research/f3_backtest_2026-04-24/` | F3 reference (V2 prompt era) |
| `scripts/monthly_decay_monitor.py` | S1 live monitor |
| `config/agent_config.yaml` | Main config (watch `market_state.detector_version`) |
| `config/profiles/` | Prop-firm overlays (ftmo.yaml / redacted_account.yaml) |

---

## Starter prompt for session 40

```
SESSION 40 KICKOFF — Monday FTMO paid challenge + start powerful-machine expansion.

Execute CLAUDE.md §Mandatory First Actions.

Then read:
  .context/02_session_handoffs/39_apr25_session_40_KICKOFF_MONDAY_DEPLOY_AND_POWERFUL_MACHINE_VISION.md
  .context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md

Monday deploy: V3 prompt + v2-active detector + $100K FTMO paid challenge.
LONG-WR-watch SPRT at trade 20. V3 SHORT-SL watch first 5 SHORT trades.
S1 monthly-decay monitor live from day 1.

Post-Monday roadmap (P1-P7 in handoff):
  P1 week 1-2: live data + decay surveillance (ongoing)
  P2 week 2-4: Phase 2a instrument expansion — 5 new instruments
              (EURUSD, NAS100, SPX500, AUDUSD, XAGUSD)
  P3 week 3-6: LIRA XAUUSD edge live-anchored re-evaluation IF
              V3 XAUUSD live WR < 55% at n=30
  P4 week 4-8: Multi-framework edges (liquidity sweep, FVG, displacement)
  P5 month 2-3: AI tool-use integration
  P6-7 month 3+: Cross-instrument liquidity + news calendar

Shelve list (don't revive without new evidence):
  V4 rule-based prompt, LIRA architecture, No-CoT, confidence_tier cherry-pick

Vision: powerful trading machine — accurate, high-frequency, multi-instrument, multi-KZ,
multiple edges. CEO's explicit framing is "high-quality frequency" (memory
feedback_research_goal_high_quality_frequency.md). Decay is #1 concern
(memory feedback_decay_is_ceo_number_one_concern.md) — compress validation,
ship fast when validated.

First action: execute pre-deploy checklist step 1-2 (pytest + preflight + canary)
from SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST. Then await CEO Monday morning
challenge-purchase signal, then complete steps 4-7.
```

---

*Session 39 closed. Weekend sprint delivered: V3 empirically confirmed Monday-ready, V4+LIRA shelved with evidence, methodology upgrade captured. Ready for Monday live deploy + Phase 2a instrument expansion.*

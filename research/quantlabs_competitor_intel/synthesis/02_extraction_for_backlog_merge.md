# Quantlabs Candidates — Extraction for Backlog Merge

Generated: 2026-04-18 (session 27)
Source: research/quantlabs_competitor_intel/synthesis/00_gtos_upgrade_candidates.md
Cold review: research/quantlabs_competitor_intel/synthesis/01_cold_review.md

## Summary

- **Total candidates:** 37 rows (35 candidates; #4 and #6 split into a/b halves)
- **Endorsed by cold review (KEEP, incl. promotions):** 30
- **Already in GTOS (YES + PARTIAL):** 12
- **Novel + endorsed + shippable (cold-review ENDORSED/QUALIFIED and NOT in GTOS):** 18

## Candidates Table

| ID | Title | Category | Source | Mechanism | Evidence | Cold-review | In GTOS? | Blocker |
|----|-------|----------|--------|-----------|----------|-------------|----------|---------|
| Q001 | Heartbeat-flatten kill switch | infra | youtube batch_02 #5, batch_10 [15] | Gateway auto-closes live MT5 positions when symbol-process goes silent | Verbatim competitor quote (batch_02 v5 `8F5hsbqTFi8`); identified as top safety gap | ENDORSED (KEEP P0; add 3-miss @ 5min false-positive guard) | NO — watchdog restarts but never flattens on silence | Spec IPC heartbeat protocol; false-positive safeguard; CEO approval (touches live position mgmt) |
| Q002 | Pending intent persistence to disk | infra | blog batch_09 [21], batch_10 [21] | Persist PendingLimitIntent to JSON/PKL so watchdog restarts preserve pending limit orders | Cross-ref CLAUDE.md Known Issues + handoff 20 schema_version | ENDORSED (KEEP P0) | PARTIAL — `src/components/execution.py:93-109` already persists `pending_intent_{symbol}.pkl` with schema_version guard | Audit remaining in-memory state (active_trade mid-lifecycle?); scope finish |
| Q003 | Daily no-data alert per symbol | infra | blog batch_10 [15] | Telegram alert when >5min passes without M15 tick during market hours | Brent BZ 523 no-data events, 5h 54m max wait | ENDORSED (KEEP P0; distinct from canary) | PARTIAL — canary (handoff 23) + between-KZ fix (handoff 17) cover drift/limit checks, not tick liveness | Separate tick-liveness watchdog separate from API canary |
| Q004a | Correlation-shock Telegram alert (static matrix) | signal | blog batch_03 [#3] | Rolling Pearson >2σ move vs 50-candle baseline across JPY_CROSSES → Telegram alert (no position impact) | Additive observation layer | ENDORSED (KEEP P0 — split from full DCC-GARCH) | NO | None for alert-only; additive |
| Q004b | Full DCC-GARCH correlation-breakdown pipeline | signal | blog batch_03 [#3] | Dynamic correlation monitor (vs static `correlation_groups` in `portfolio_risk.py`) | 3σ breakdown → 73% detection / 8% false alarms (batch_03) | QUALIFIED (P0→P1; new `arch`/`statsmodels` dep, rolling estimation) | NO — `src/components/portfolio_risk.py` has static hard-coded groups only | Dependency decision (arch vs statsmodels); rolling estimator; shadow-log→gate cycle |
| Q005 | VPIN shadow logger per symbol per KZ | signal | blog batch_09 [3], batch_04 | Tick-bucket toxicity score via `mt5.copy_ticks_*`; composite `z(VPIN)*0.4 + z(OBI)*0.3 + z(AC1)*0.3` | VPIN>0.75 high toxicity, <0.7 entry gate; Entry Quality Score 0-100 | QUALIFIED (P0→P1; tick-pipeline spike is the blocker) | NO | Tick-pipeline spike (1-2 days); bucket calibration; FTMO tick quirks |
| Q006a | `time_in_trade_shadow_logger.py` | exit-logic | blog batch_05 [17] stablecoin 1800s | Log hypothetical delta_r at 30/60/120/240min exits vs actual close (mirrors `be_shadow_logger.py`) | Observation-only, additive | ENDORSED (KEEP P0 — shadow-first split) | NO — no time-in-trade logger today | Mirror BE-shadow pattern; Wilcoxon after 30+ observations |
| Q006b | Actual time-based exit gate (30/60/120min cap) | exit-logic | blog batch_05 [17] | Hard time-stop in `permissions.py`/`orchestrator.py` to prevent zombie trades | batch_05 stablecoin 1800s pattern | QUALIFIED (P0→P1; trading-logic change needs CEO approval + 5-process restart) | NO — `permissions.py` has no time-stop | Block on Q006a evidence; OB-retest trades often 4-8h to work — 30min cap may kill edge |
| Q007 | Hurst exponent shadow feature | regime | blog batch_08 [19] Random Walk Memory, batch_09 [12] | Daily H1-return Hurst exponent logged as R2 candidate feature (>0.5 momentum / <0.5 MR) | batch_08 [19] Caltech/BGU paper | ENDORSED (KEEP P1) | NO — "H1 return autocorrelation" in CLAUDE.md is quarterly-only, not Hurst | Ship into `candidate_features_logger.py` (handoff 20) |
| Q008 | HMM regime classifier (5-state) | regime | blog batch_03 [#3], batch_08 [2], batch_09 [2] | {high_vol, low_vol, liquidity_drought, trending, mean_reverting} via `hmmlearn` on M15 returns | batch_08 [2] HMM Sharpe 1.8→2.5 RL-augmented; Kelly modifiers per state | ENDORSED (KEEP P1) | NO — T7 prompt has regime framing, no explicit HMM | `hmmlearn` dep; shadow-log first; gating requires H29 refactor |
| Q009 | Gateway-only broker connection | infra | blog batch_09 [21], batch_10 [21] Valkey engine | MT5 in separate process; hot-swap orchestrator without disconnecting broker | Valkey + .NET 8 architecture | ENDORSED (KEEP P1; large scope) | NO — per-symbol PID-locked processes each own their MT5 connection today | Large architectural change; IPC (Redis/named pipe); Q002 may suffice partially |
| Q010 | OFI shadow logger | signal | blog batch_04, batch_09 [3] | Lee-Ready tick-rule approximation of Order Flow Imbalance on M1 ticks | OBI ±0.3 extreme threshold | ENDORSED (KEEP P1) | NO | Tick pipeline (shared with Q005); per-symbol per-KZ shadow log |
| Q011 | Drawdown-to-Profit Ratio validation gate | risk | blog batch_06 *(cold review: citation NEEDS RE-VERIFICATION)* | DDtoP <1.0x required for framework R2 promotion | batch_06 — term not found in TOP FINDINGS | QUALIFIED (KEEP P1 provisional) | NO — GTOS validation battery lacks DDtoP | Recheck batch_06 for the specific term/citation before shipping |
| Q012 | Composite strategy score for R2 ranking | risk | blog batch_07 [20] | `0.30*Sharpe + 0.20*Sortino + 0.20*ExpR + 0.15*WR + 0.15*Calmar` as R2 promotion ranker | batch_07 [20] verified `batch_07.md:10` | ENDORSED (KEEP P1) | NO — single framework today (`enabled_frameworks: ["ob_retest"]`) | Blocked by single-framework WF-1; unblocks post-WF-1 |
| Q013 | Half-Kelly sizing with HMM-regime multipliers | risk | blog batch_03 [#3] | Kelly fraction modulated by HMM state: hi_vol 0.40, lo 1.15, trend 1.30, MR 0.85, crisis 0.25 | Kelly modifier table verified batch_03.md:61 | ENDORSED (KEEP P1; supersedes H29) | PARTIAL — H29 in `drawdown_manager.py` does static 2%→0.5% on 8% DD, no regime states | HMM maturity (Q008) first; 100+ trade validation; sizing-logic change |
| Q014 | "Block all orders" master flag audit | infra | youtube batch_03 #6 | Single boolean separate from `deployment.phase`, hard-enforced at gate | Bryan's prod/paper code-path sharing failure mode | ENDORSED (KEEP P0 — promoted P1→P0) | PARTIAL — `deployment.phase: 2` exists in config but NO SRC CODE ENFORCES IT (verified via grep; research/sweep_apr11_2026.md:207-209 confirms this) | Audit phase-gate enforcement; add real circuit-breaker gate |
| Q015 | Consecutive-loss cooldown (3 losses → 60min halt) | risk | blog batch_03 [#18] Multi-Asset Bot Suite *(single source — not universal)* | Per-symbol halt after 3 consecutive losses with 60min cooldown | One article's opinion per cold review | QUALIFIED (KEEP P1; tighten citation) | PARTIAL — `max_consecutive_losses` exists in orchestrator emergency stop (default 5) but no cooldown timer; `max_daily_losses=2` exists but no explicit cooldown | Shadow-log first; gate change; cooldown timer logic |
| Q016 | Weekly AI-reasoned summary of skipped trades | infra | youtube batch_01 #4, batch_02 #3 | Feed `malformed_responses.jsonl` + `api_refusal_monitor.py` data to AI for weekly "why no-order" post-mortem | Bryan's pattern verified | ENDORSED (KEEP P0) | PARTIAL — `api_refusal_monitor.py` exists; `malformed_responses.jsonl` logged; no weekly AI summary loop | Extend existing monitors with weekly AI call (~$2/mo) |
| Q017 | Parameter perturbation validation | infra | blog batch_10 [25] | Sensitivity analysis on ±20% param moves as R2 promotion battery addition | batch_10 [25] verified | ENDORSED (KEEP P1) | NO — walk-forward + MC exist, no parameter perturbation | Add to existing walk-forward + MC battery |
| Q018 | News-confirmation shadow logger | filter | youtube batch_05 #3 | AI scans news ±30min around CANDIDATE, tags "news_present"/"news_absent"; correlate with outcomes | Bryan's explicit template (batch_05 v3) | QUALIFIED (KEEP P1; effort → L per cold review) | NO — `news_calendar.py` exists for economic calendar blocks, no AI news-scan | Requires news-feed ingestion GTOS doesn't have; news pipeline build |
| Q019 | Microprice feature | signal | blog batch_09 [2], also batch_03 | `(bid_size*ask + ask_size*bid)/(bid_size+ask_size)` at candle-close, R2 candidate feature | Formula verified batch_03.md:442 | ENDORSED (KEEP P1) | NO | L1 bid/ask sizes via MT5 tick API |
| Q020 | Parallel MC resampling (trade-order permutation) | infra | blog batch_10 [25] | Extend existing Monte Carlo battery with trade-order permutation (not just bootstrap) | batch_10 [25] verified | ENDORSED (KEEP P1) | PARTIAL — MC exists (99.4% P(FTMO-pass)); no explicit permutation variant | Cheap add to existing MC |
| Q021 | Regime-conditioned prompt variant for T7 | signal | blog batch_02 prompt template | Inject `{regime}` + `{volatility}` state into T7 C-gate prompt | Verbatim competitor template | ENDORSED but P2 (WF-1 protects T7) | NO — T7 C-gate has no `{regime}` injection | HMM (Q008) shadow-log >100 obs with state-dependent WR divergence; CEO approval |
| Q022 | Hawkes process toxicity λ(t) | signal | blog batch_08 [2] | `λ(t) = μ + Σ α·exp(-β(t-tᵢ))` as research-grade toxicity score | batch_08 [2] — 78% Hawkes detection (Bayesian=82%, Microprice=65%) | ENDORSED (KEEP P2; research-grade) | NO | Dedicated KAP cycle, not a sprint candidate |
| Q023 | Portfolio bot health score 0-100 | infra | blog batch_02 [16] | Composite score across symbols (WR / Sharpe / no-data / API-refusal); alert <40 | batch_02 [16] composite health metric | ENDORSED (KEEP P2) | NO — per-symbol SPRT/monitors but no portfolio-level composite | Aggregation layer over existing per-symbol metrics |
| Q024 | Shanghai gold premium as XAUUSD sentiment | signal | blog batch_09 [1] | Use SGE/COMEX spread as tertiary gold regime signal during CME outages | batch_09 [1] CME outage context | ENDORSED (KEEP P2) | NO | SGE data feed; XAUUSD-specific; low priority |
| Q025 | COT positioning weekly filter | filter | blog batch_09 [15] | CFTC COT extremes as predictor/filter on USDJPY/GBPJPY/GBPUSD | Free CFTC data | ENDORSED (KEEP P2) | NO | CFTC data pull; research-level eval first |
| Q026 | MCP supply-chain security audit | infra | youtube batch_05 #4 | Enumerate installed Python packages; flag 3rd-party MCP servers (LMLite-style credential theft) | batch_05 #4 verified | ENDORSED (KEEP P2) | NO — limited exposure today (MT5 + Anthropic only) | Operational check; KAP pipeline MCP creep monitoring |
| Q027 | Prepaid card cap on Anthropic API | infra | youtube batch_05 #4, blog batch_07 [1] | Hard monthly spend limit via prepaid-card account-level defense | batch_07 [1] "$10K over single weekend" horror story | ENDORSED (KEEP P0 — promoted P2→P0) | NO — `budget.monthly_cap_usd: 50.0` in config is soft warning only; canary cache protects canary calls only | Operational (~1 hour task); no code change |
| Q028 | Log-event density benchmark | infra | blog batch_02, batch_10 | Baseline events/hour per symbol; alert on ±50% deviation | batch_02 123K events/3h, batch_10 17,580 events | ENDORSED (KEEP P2) | NO | Baseline measurement; alert rule |
| Q029 | Quote-stuffing / spoofing detection in KZs | signal | blog batch_03 [#41] Quote Fade Algorithm *(cold review corrected citation from batch_09[24])* | Sub-second top-3-level order-book covariance anomalies | batch_03 [#41] verified | ENDORSED (KEEP P2) | NO | Tick-level analysis; defer pending VPIN (Q005) results |
| Q030 | Seasonal commodity filters | filter | blog batch_10 [28] | Gold seasonality (Q1 ETF inflows, Indian wedding demand) as XAUUSD filter | batch_10 [28] | QUALIFIED (KEEP P2; gold-applicable slice only) | PARTIAL — T7 prompt has D1 framing but no explicit seasonal filter | Low priority — gold-only applicable slice |
| Q031 | AI-generated "new bot from logs" pipeline | infra | youtube batch_02 #3 | Feed logs to AI → Claude generates new bot variant | batch_02 #3 | REJECTED (P3 — GTOS's KAP pipeline higher-rigor) | PARTIAL — KAP pipeline exists (higher-rigor equivalent) | n/a — reject |
| Q032 | "One strategy, many instruments" inversion | infra | youtube batch_02 #5 | Client-per-strategy architectural pattern vs current client-per-instrument | batch_02 #5 | REJECTED (P3 — wrong for ob_retest which is symbol-specific) | NO | n/a — reject |
| Q033 | Rithmic/IBKR broker migration research | infra | blog batch_09 [1], batch_10 multiple | Migrate from MT5 to CME-direct (Rhythmic/IBKR) | batch_09 [1] + batch_10 | REJECTED (P3 — scope mismatch, prop-firm MT5 by design) | NO | n/a — reject |
| Q034 | BlackRock AlphaAgents multi-agent debate | infra | blog batch_05 [29] | Fundamental/Sentiment/Valuation debate via AutoGen + Arize + HybridRAG | batch_05 [29] | REJECTED (P3 — duplicate of Component 3B paused code) | YES — `src/components/debate.py` exists (Bull/Bear Debate Component 3B, paused per CLAUDE.md) | n/a — don't re-implement; resume existing code when CEO approves |
| Q035 | Streamlit per-strategy sandbox with live-toggle | infra | youtube batch_04 #2 | Streamlit UI for backtest + push-button live-toggle | batch_04 #2 | REJECTED (P3 — UI out of scope, maintenance surface without edge gain) | NO — CLI + scripts only | n/a — reject |
| Q036 | "Shadow-mode 30min before live" blue-green deploy | other | blog batch_06 | Shadow-then-flip-live with 30-min cut-over window (deployment pattern) | batch_06 pattern | NOT DISCUSSED as separate candidate — cold review flags as already-GTOS duplicate | YES — multiple GTOS shadow loggers (`be_shadow_logger.py`, `proximity_shadow_logger.py`, `partial_close_shadow_logger.py`, `candidate_features_logger.py`, `ob_continuation_monitor.py`) implement shadow-then-promote | n/a — already covered |
| Q037 | 50-100 trade minimum for statistical validity | other | blog batch_06 | Pre-promotion gate of 50-100 live trades before framework promotion | batch_06 | NOT DISCUSSED as separate candidate — cold review flags as GTOS-stricter (SPRT walks until boundary) | YES — SPRT battery is stricter | n/a — already covered |

## Novel Candidates Not In GTOS (for quick reference)

Cold-review ENDORSED/QUALIFIED and "In GTOS?" = NO:

- **Q001** Heartbeat-flatten kill switch (P0, infra, novel, closes silent-crash safety gap)
- **Q004a** Correlation-shock Telegram alert (P0, signal, novel, alert-only add)
- **Q004b** Full DCC-GARCH correlation-breakdown pipeline (P1, signal, novel)
- **Q005** VPIN shadow logger per symbol per KZ (P1, signal, novel, tick-pipeline required)
- **Q006a** `time_in_trade_shadow_logger.py` (P0, exit-logic, novel, shadow-first)
- **Q006b** Actual time-based exit gate (P1, exit-logic, novel, blocks on Q006a)
- **Q007** Hurst exponent shadow feature (P1, regime, novel, cheap daily feature)
- **Q008** HMM regime classifier (P1, regime, novel, hmmlearn dep)
- **Q009** Gateway-only broker connection (P1, infra, novel, large scope)
- **Q010** OFI shadow logger (P1, signal, novel)
- **Q011** Drawdown-to-Profit Ratio gate (P1, risk, novel, citation flagged)
- **Q012** Composite strategy score for R2 ranking (P1, risk, novel)
- **Q017** Parameter perturbation validation (P1, infra, novel)
- **Q018** News-confirmation shadow logger (P1, filter, novel, needs news feed)
- **Q019** Microprice feature (P1, signal, novel)
- **Q023** Portfolio bot health score 0-100 (P2, infra, novel)
- **Q027** Prepaid card cap on Anthropic API (P0, infra, novel, operational only)
- **Q028** Log-event density benchmark (P2, infra, novel)

## Candidates Already Covered (dedup targets)

YES or PARTIAL overlap with existing GTOS capability:

- **Q002** Pending intent persistence — PARTIAL: `src/components/execution.py:93-109` already persists `pending_intent_{symbol}.pkl` with `schema_version` guard (handoff 20); P0 work remaining is scope-finish + audit, not greenfield build
- **Q003** Daily no-data alert per symbol — PARTIAL: canary cache (handoff 23) + between-KZ fix (handoff 17) cover API drift + pending limits. Tick-liveness gap remains
- **Q013** Half-Kelly with HMM multipliers — PARTIAL: `drawdown_manager.py` (H29) does static 2%→0.5% risk on 8% DD; regime-state multipliers missing; Q008 prereq
- **Q014** "Block all orders" master flag audit — PARTIAL: `deployment.phase: 2` in config but NOT ENFORCED in `src/` code (grep confirmed; cf. research/sweep_apr11_2026.md:207-209). Audit reveals true cosmetic-only today
- **Q015** Consecutive-loss cooldown — PARTIAL: `max_consecutive_losses` emergency stop exists in `orchestrator.py:413-418` (default 5, stops trading for the day); `max_daily_losses: 2` config. No 3-losses-60min-cooldown-then-resume pattern
- **Q016** Weekly AI-reasoned summary of skipped trades — PARTIAL: `api_refusal_monitor.py` + `malformed_responses.jsonl` exist; no weekly AI summary loop
- **Q020** Parallel MC resampling — PARTIAL: MC battery exists (99.4% P(FTMO-pass) per CLAUDE.md), no explicit permutation variant
- **Q030** Seasonal commodity filters — PARTIAL: T7 prompt has D1 bias framing, no explicit seasonal gate
- **Q031** AI-generated new bot pipeline — PARTIAL: KAP pipeline is higher-rigor equivalent; reject per cold review
- **Q034** BlackRock AlphaAgents debate — YES (full duplicate): `src/components/debate.py` (Component 3B Bull/Bear, paused per CLAUDE.md). Resume existing instead of re-implementing
- **Q036** "Shadow-mode before live" blue-green deploy — YES: Multiple shadow loggers already implement shadow-then-promote (`be_shadow_logger.py`, `proximity_shadow_logger.py`, `partial_close_shadow_logger.py`, `candidate_features_logger.py`, `ob_continuation_monitor.py`)
- **Q037** 50-100 trade minimum — YES: SPRT is stricter (walks until boundary)

## Notes / Caveats

1. **Citation errors in the synthesis (surfaced by cold review, unpatched in the source doc):**
   - Q022 Hawkes: synthesis Section 2.3 line says "VPIN 65%" but correct is "Microprice 65%" (authoritative: `batch_08.md:40`).
   - Regime-mult ATR stop attribution: synthesis blames batch_08, correct is batch_07 [15].
   - Q029 Quote-stuffing citation: synthesis cites "batch_09 [24]", correct is "batch_03 [#41] Quote Fade Algorithm".
   - 10 placeholder `[xxx]` citations in Sections 2.2, 2.3, 2.5, 2.6, 2.8 remain unresolved.

2. **Q011 DDtoP citation is unverified.** Cold review flagged that "drawdown-to-profit ratio" terminology is not found in batch_06 TOP FINDINGS — possibly present in body but not recovered. Do not promote Q011 to implementation until citation confirmed or replaced.

3. **Q015 cooldown claim is single-source.** Cold review tightened: only batch_03 [#18] Multi-Asset Bot Suite describes this — NOT a "common competitor pattern" as an earlier synthesis draft implied. Weak evidence base.

4. **P0 priority drift.** Synthesis evolved from initial "6 P0" → final "8 P0" (#1, #2, #3, #4a, #6a, #14, #16, #27) after cold review promoted #14 and #27 and split #4 and #6 into shadow-log (P0) + gate-change (P1) halves. Cold review's own recommendation was "5 P0 after P0 reclassification" — so the synthesis ended up more aggressive than the cold reviewer endorsed. Worth noting when merging with other backlog sources.

5. **Q009 vs Q002 overlap.** Q009 (gateway-only broker connection) is a large architectural change; Q002 (pending intent persist) is a cheap partial solution. Cold review notes Q002 "may suffice" — if Q002's scope-finish covers the restart-state-loss gap, Q009 could be downgraded.

6. **Q014 finding is load-bearing.** Grep confirms `deployment.phase` is defined in `config/agent_config.yaml` and referenced in docs but has ZERO enforcement in `src/` code (corroborated by `research/sweep_apr11_2026.md:207-209` and `research/plan_verification_apr11_2026.md:133-136`). The "master flag audit" is really "the existing flag does nothing — build the enforcement that was assumed to exist." Higher consequence than the synthesis text alone conveys.

7. **Prerequisite sequencing (from cold review Section 4.3 + synthesis Section 5):** Commit the between-KZ pending-limit fix (handoff 17, currently uncommitted in `src/components/orchestrator.py`) before shipping any P0 from this list — orchestrator touch + 5-process restart is shared blast radius.

8. **Category splits:** My category tagging clusters Q036/Q037 as "other" since they're validation-discipline patterns rather than features. If the merge framework distinguishes validation-methodology from feature-work, consider re-categorizing.

9. **No false YES claims found.** Spot-checked the synthesis's novelty tags (YES/PARTIAL/NO/MAYBE) against GTOS code; synthesis correctly flags Q034 duplicate and did not claim novelty for anything GTOS already ships. Cold review agreed (Section 3c final bullet: "Clean").

10. **Exhaustiveness check:** Table covers all 37 rows from the synthesis (35 base + #4a/#4b split + #6a/#6b split), plus Q036/Q037 pulled from Section 2.4 explicitly called out by the cold review as "patterns GTOS already has" — these aren't in the numbered candidate list but are recurring competitor themes the merge thread should know are pre-covered.

# Session 35 — Fresh Session: Deep Diagnostic Audit + Edge Investigation Before redacted_account

**Created:** 2026-04-19 (end of session 34, amended after CEO directive)
**Target execution:** fresh Claude Code session, today (2026-04-19, Sunday)
**redacted_account kickoff:** Tuesday 2026-04-21
**Budget profile:** ~$0 API spend (all AI calls go through Claude Code plan compute via `Agent` tool, not the `$50/mo` Anthropic API balance). Live trading continues burning ~$1-2/day against the API cap regardless.

---

## 0. Starter message (CEO paste this into fresh session)

> Session 35 — deep diagnostic audit before redacted_account Tuesday kickoff.
>
> Read in order:
> 1. `CLAUDE.md`
> 2. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`
> 3. Read handoff `.context/02_session_handoffs/35_apr19_FRESH_SESSION_PRE_redacted_account_EDGE_INVESTIGATION.md` — authoritative, contains the full plan with agent briefs
> 4. Read the 3 session-34 synthesis docs listed in that handoff's pre-reads section
>
> Mission: figure out where the weakness actually is. Entry, execution, AI response, hallucinations, pre-checks, kill zones, or we're becoming institutional liquidity — check all of it. We have the data; use it.
>
> Rules:
> - **Every research agent runs with `model: "opus"` (Opus 4.7) and max effort.** Non-negotiable.
> - Scale: as many agents as the handoff plan specifies. Parallel where independent.
> - Use all available data: 367-trade batch KB, T7 sim JSONs (XAUUSD/NAS100/EURUSD), historical CSVs Jan-Apr 2026, 9 shadow logs, live logs since Apr 7.
> - Follow the 4-phase structure: Phase 1 (8-agent parallel discovery) → Phase 2 (8-agent parallel review) → Phase 3 (3-5 hypothesis testers) → Phase 4 (chairman synthesis).
> - Run Tier A infrastructure fixes BEFORE Phase 1 so agents work on clean data.
> - No live code changes without CEO approval — research + scope docs only.
> - Restart decision deferred until research lands.
>
> Deliver a chairman synthesis that answers: (1) where is the edge leaking, ranked by impact, (2) is the decay "market arbitraging our edge" or "our execution degrading," (3) which 3-5 concrete changes would most likely restore edge, (4) what new patterns should we explore.
>
> Go.

---

## 1. Mission

The system has shown a **monotonic quarterly WR decay: 73.2% → 71.4% → 63.6% → 59.4%** across the last four quarters. Session 34 shipped three safety layers (T2.8, D1-bias-lag logger, XAUUSD audit) but **did not touch the edge itself.** The CEO now wants to know, before committing redacted_account capital Tuesday:

1. **Where is the weakness?** Entry quality, execution slippage, AI response integrity, hallucinations, pre-AI filters, kill-zone boundaries, OB detection — all are candidates. Which ones are verified leaks?
2. **Is the edge being arbitraged out?** As AI adoption grows in markets, other systems may be identifying the same OB retest pattern. We could be **becoming the liquidity** institutions hunt. Testable.
3. **Are we missing trades, or losing trades we take?** Both? The ratio matters.
4. **Are there alternative patterns** in institutional flow that we're systematically ignoring? If the OB edge is dying, is there a successor edge we could graduate to?
5. **How do we beat the decay?** Either make the existing edge stronger + tighten execution, or find a new one.

**CEO directives (verbatim):**
> "we really need to understand what's going on and if you need more actions to basically win against the decay, or know exactly our weak point or points, is it the entry is it the execution, is it the ai response, is it hallucinations, is it the prechecks before the trades and the killzones ... i need to literally check everything and you can have as many agents for that as you want to have the full and full picture, to increase our chances in beating the market."

> "institutional money knows about the edge and we're slowly becoming their liquidity, since ai is getting more and more into markets."

> "make our edge stronger and us more confident in it with better execution and reading the edge and doing something about it to still win and find opportunities, or find other patterns in the market that says that there are other ways institutional money is moving and we're not following it."

---

## 2. Pre-reads (mandatory)

1. `CLAUDE.md`
2. `python scripts/generate_live_state.py` → read `.context/LIVE_STATE.md`
3. This handoff — **authoritative**
4. Session 34 synthesis docs (primary evidence base):
   - `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/NAS100_T3_1_synthesis.md`
   - `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_T3_1_synthesis.md`
   - `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md`
5. Latest prior close handoff: `.context/02_session_handoffs/34_apr19_FRESH_SESSION_POST_NAS100_PROMPT.md`

---

## 3. Data inventory (what agents can use)

### Trade-level datasets

| Source | Size | Coverage | Use |
|---|---|---|---|
| `knowledge_base_backtest/sessions/XAUUSD/*.json` | 318 files | Oct 2025 – Mar 2026 batch (older debate pipeline) | Large-n XAUUSD trade outcomes; **does NOT have L2 gate fields** per T3.2 verdict:47 |
| `knowledge_base/trades.json` + subdirs | live trades since 2026-04-07 | current system, all 5 instruments | Live ground truth |
| `research/t7_live_simulation/all_results_jan_apr10.json` | 5.4 MB, 2100 records | XAUUSD Jan-Apr 2026 | Primary XAUUSD counterfactual corpus (production-faithful, includes L2) |
| `research/t7_live_simulation/XAUUSD_t7_simulation.json` | 1 MB | XAUUSD slice 2 (Mar 11 – Apr 12) | Cross-check |
| `research/t7_live_simulation/NAS100_t7_simulation.json` | — | NAS100 Jan 2 – Apr 17 (1600 M15 candles, 818 AI calls) | From session 33; includes the T3.1 findings |
| `research/t7_live_simulation/EURUSD_t7_simulation.json` | 4.3 MB, 2280 records | EURUSD Jan-Apr | From session 34 council; known bug-tangled |

### Chart data (raw OHLCV)

| Path | Coverage |
|---|---|
| `data/historical_2026/XAUUSD_{M15,H1,H4,D1}.csv` | Jan 2 – Apr 17 2026 |
| `data/historical_2026/US30_{M15,H1,H4,D1}.csv` | same |
| `data/historical_2026/USDJPY_{M15,H1,H4,D1}.csv` | same |
| `data/historical_2026/GBPJPY_{M15,H1,H4,D1}.csv` | same |
| `data/historical_2026/GBPUSD_{M15,H1,H4,D1}.csv` | same |
| `data/historical_2026/NAS100_{M15,H1,H4,D1}.csv` | same |
| `data/historical_2026/EURUSD_{M15,H1,H4,D1}.csv` | same |

### Shadow logs (observation-only, no gate effect)

- `shadow_logs/candidate_features_log.jsonl` — per-CANDIDATE feature dump
- `shadow_logs/proximity_shadow_log.jsonl` — OB distance at candle close
- `shadow_logs/liquidity_distance_log.jsonl` — distance to PDH/PDL/Asian/London H/L
- `shadow_logs/displacement_events.jsonl` — impulse quality
- `shadow_logs/malformed_responses.jsonl` — AI refusal / parse failure
- `shadow_logs/drawdown_state_changes.jsonl` — H29 risk reduction events
- `shadow_logs/daily_pnl.json` — daily realized P&L
- `shadow_logs/partial_close_backtest.jsonl` — Variant C (33% @ 1R) shadow outcomes
- `shadow_logs/partial_close_backtest_exact_only.jsonl` — strict-match subset

### Live operational logs

- `logs/{xauusd,us30,usdjpy,gbpjpy,gbpusd}.log` — per-symbol orchestrator output
- `logs/live_{XAUUSD,US30,USDJPY,GBPJPY,GBPUSD}.log` — older naming, may overlap
- `logs/watchdog.log` — watchdog E2E alerts
- `logs/api_refusal_monitor.log` — flat-refusal detection
- `logs/displacement.log`
- `logs/start_all.log` — process launches
- `logs/q_14_broad_mi.log` — Q014 mutual-information experiment residual

### Pipeline state

- `pipeline_state/heartbeat.json` — live heartbeat
- `knowledge_base/pipeline_state/02_market_state.json` — last computed MSO

### Canonical validated numbers (do not re-establish — baseline)

Per CLAUDE.md "Validated Numbers":
- XAUUSD WR 62.0% (n=129, p=3.42e-08, Bonferroni-safe)
- OB zone advantage +17pp vs generic pullback (p=0.003)
- Batch expectancy +0.200R/trade (raw p=0.046, **does not survive Bonferroni**)
- CANDIDATE rate 10.3% of evaluated setups
- Inverted TP rate 7.03% of CANDIDATEs
- Batch population 367 trades, full-pop WR 65%, 2026-only WR 59.5%
- Quarterly WR decay 73.2% → 71.4% → 63.6% → 59.4% ← **the thing we're investigating**

---

## 4. Tier A — Infrastructure prerequisites (main-thread, BEFORE Phase 1)

Agents run on cleaner data if A1 lands first. Zero API cost.

### A1. Per-instrument `_FILL_EPSILON` scaling

- **Target:** `scripts/simulate_t7_live_period.py:482` — hardcoded `_FILL_EPSILON = 0.05` points.
- **Fix:** per-symbol tick-size scaling. Recommended table:
  ```python
  _EPSILON_BY_SYMBOL = {
      "XAUUSD": 0.20,   # 2 × 0.10 tick
      "US30":   2.0,    # 2 × 1.0 tick
      "NAS100": 2.0,    # 2 × 1.0 tick
      "USDJPY": 0.02,   # 2 × 0.01 tick (2 pips)
      "GBPJPY": 0.02,
      "EURUSD": 0.0002, # 2 × 0.00001 tick (2 pips)
      "GBPUSD": 0.0002,
  }
  ```
  Default fallback `0.05` with a WARNING log for unknown symbols.
- **Regression guard:** replay XAUUSD `all_results_jan_apr10.json` — outcomes must not materially flip (XAUUSD 0.20 is only slightly tighter than 0.05 on fills).
- **Commit:** `fix(sim): per-instrument _FILL_EPSILON scaling`

### A2. NAS100 counterfactual re-scoring at new epsilon

- **No new AI calls.** Load `research/t7_live_simulation/NAS100_t7_simulation.json`, re-run `compute_outcome()` against each CANDIDATE + L2-rejected record with the new epsilon.
- **Compare:** old (0.05) vs new (2.0) on the 37 CANDIDATE outcomes + the 42 `sl_beyond_ob` L2 rejects (+13.5R claim) + the 24 `max_kz_trades` BLOCKED novels (+16.02R claim).
- **Output:** `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/NAS100_epsilon_revalidation.md`
- **Commit:** `research(t3.1): NAS100 T7 re-scoring at honest epsilon`

### A3. EURUSD counterfactual re-scoring at new epsilon

- Same — replay against `EURUSD_t7_simulation.json`.
- The 5 "real" CANDs that went from +5.17R to -5.00R in the session 34 analysis: confirm under the new formal epsilon.
- **Output:** `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_epsilon_revalidation.md`

---

## 5. Tier B — Four-phase deep diagnostic sprint (THE MAIN EVENT)

**Every agent:** `subagent_type: "general-purpose"`, `model: "opus"` (Opus 4.7), max effort. Parallel where independent. Brief each agent with its specific hypothesis + the data inventory above; do NOT dictate methodology (Opus does better investigations when given latitude).

### Phase 1 — 8-agent parallel discovery (dispatch in one message)

Each agent produces a markdown output file under `research/b_deep_audit_2026-04-19/phase1/`. Each brief must include: (a) hypothesis to test, (b) data sources to use, (c) output file path, (d) evidence + statistics requirement (no claim without file:line or dataset:record evidence), (e) exit with written conclusion ranked by confidence.

---

**Agent α — Entry mechanics + execution audit**
- **Question:** of the losing trades, what fraction lose due to entry slippage, SL bit-exact touches ("becoming liquidity" signature), BE stop-outs that would have won, or partial-close-too-early?
- **Inputs:** `knowledge_base/trades.json` (live), `all_results_jan_apr10.json` (sim), `partial_close_backtest*.jsonl` (shadow), M15 CSVs for MFE/MAE replay.
- **Deliverables:**
  1. Distribution of `(actual_entry − intended_entry)` across all filled trades, by instrument and session
  2. Count + R of trades that hit SL within ±2 ticks of OB bound then reversed toward TP (**core liquidity-hunt signature**)
  3. BE-stopped trades counterfactual: how many would have hit 1.5R+ TP if BE stop were later or off?
  4. Partial-close Variant C (33% @ 1R) outcome vs no-partial baseline at n≥30
  5. Quarterly evolution of (1) and (2): growing, stable, or shrinking?
- **Output:** `research/b_deep_audit_2026-04-19/phase1/alpha_entry_execution.md`

---

**Agent β — AI response + hallucination audit**
- **Question:** where does the AI output degrade trade quality? Hallucinated fields, degenerate outputs, inconsistent self-citation, prompt-blindspots?
- **Inputs:** all three T7 sim JSONs, `shadow_logs/malformed_responses.jsonl`, `shadow_logs/candidate_features_log.jsonl`, `src/prompts/primary_analyzer_prompt.py`.
- **Deliverables:**
  1. Hallucination tally: `model_used` field distribution (known-bogus), `bias_source` values that don't exist in the MSO, cited OB IDs that don't match any OB in the MSO
  2. Degenerate output rate by instrument (entry=SL, entry=TP, SL=TP); correlation with subsequent WR
  3. Self-contradiction rate: CANDIDATE emissions that failed `poi_self_contradict` / `poi_cited_no_matching_OB` / `entry_in_ob` L2 rules (already tallied in NAS100 synthesis; do same for XAUUSD + EURUSD)
  4. Output-format stability across re-runs of identical MSO (if we have any re-runs; if not, propose a $5 multi-run consistency test)
  5. Prompt compression artifact check: is any MSO field being truncated before reaching AI?
- **Output:** `research/b_deep_audit_2026-04-19/phase1/beta_ai_integrity.md`

---

**Agent γ — Missed-trade census (counterfactual)**
- **Question:** what's the opportunity cost of NO_TRADE, L2 rejections, and BLOCKED_LIMIT records? Is it growing?
- **Inputs:** all three T7 sim JSONs + M15 CSVs for forward-price replay.
- **Deliverables:**
  1. For every NO_TRADE record: did price move +1.5R (the hypothetical TP at min_rr) in the correct direction within 4h / 12h / 24h of candle close? Split by instrument + quarter.
  2. Same for every L2 reject (bucketed by `l2_reason`).
  3. Same for every BLOCKED_LIMIT (bucketed by block reason).
  4. Quarterly evolution: opportunity cost per quarter — does the "missed" bucket WR show the same decay?
  5. Identify the top-3 L2 reject reasons by opportunity cost. Confirm or challenge session-34's `sl_beyond_ob` finding.
- **Output:** `research/b_deep_audit_2026-04-19/phase1/gamma_missed_trades.md`

---

**Agent δ — Regime + decay causation**
- **Question:** what changed in the market between Q2-2025 and Q1-2026 that explains the 73→59% WR drop? Which decay slice is noise vs structural?
- **Inputs:** historical CSVs all 7 instruments (if older data exists in repo; if not, Jan-Apr 2026 only and compare intra-year slices), `knowledge_base_backtest/sessions/`, batch trade metadata.
- **Deliverables:**
  1. Per-quarter regime metrics: ADR, ATR ratio, Hurst exponent, trend strength (Kaufman AMA proxy), autocorrelation at 1-day / 5-day lags
  2. Quarterly CANDIDATE rate + WR per instrument. Does decay track a specific instrument or spread?
  3. **OB subtype decay:** rolling-50 WR split by `ob_type` (internal vs external, fresh vs retested, clean vs wicked). Which subtype died?
  4. Time-of-day decay: is decay concentrated in London open / NY open / overlap? (tests the "peak-algo-hours" hypothesis)
  5. Cross-instrument decay correlation: does the 73→59% drop happen more on high-algo instruments (NAS100, EURUSD) than low-algo (XAUUSD, exotic JPY pairs)?
- **Output:** `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md`

---

**Agent ε — "We are the liquidity" / arbitrage hypothesis**
- **Question:** is our edge being arbitraged? Specific signatures to look for.
- **Inputs:** all T7 sim JSONs + M15 CSVs for MFE/MAE replay + `shadow_logs/proximity_shadow_log.jsonl`.
- **Deliverables:**
  1. **Pre-entry MFE distribution:** from candle close (signal) to fill time, does price typically move FAVORABLY before reversing to fill our limit? If yes and growing, market is "serving us the fill" after a sweep.
  2. **Post-entry first-60min behavior:** median MFE in first 15min / 30min / 60min after fill. Is immediate adverse move growing over time?
  3. **Stop-hunt signature:** fraction of losses where SL touch is within ±2 ticks of OB bound AND price reverses ≥1R in the opposite direction within 4h of SL hit. Compare 2025 vs 2026.
  4. **MFE ceiling compression:** for winners, max favorable excursion before TP. Is the ceiling shrinking (i.e., trades win smaller and smaller)?
  5. **Cross-instrument algo-density correlation:** rank instruments by known algo presence (NAS100 > EURUSD > GBPUSD > USDJPY > GBPJPY > XAUUSD); is decay rate rank-correlated? (Spearman.)
  6. Final verdict: evidence for OR against arb hypothesis with statistical qualifier.
- **Output:** `research/b_deep_audit_2026-04-19/phase1/epsilon_liquidity_arb.md`

---

**Agent ζ — Market state + pre-check fragility**
- **Question:** is `market_state.py` correctly identifying OBs / FVGs / liquidity / swings? Are pre-AI filters (L1, OB proximity, KZ boundaries, bias source) leaking value?
- **Inputs:** `src/components/market_state.py`, recent `pipeline_state/02_market_state.json` snapshots, `candidate_features_log.jsonl`, `proximity_shadow_log.jsonl`, `liquidity_distance_log.jsonl`, M15/H1/H4/D1 CSVs.
- **Deliverables:**
  1. Spot-audit 20 random CANDIDATE MSOs against manual chart analysis: does detected OB / FVG / swing match visual truth?
  2. OB-proximity filter rejection analysis: the 542 pre-AI OB-proximity rejects on NAS100 (from synthesis:44) — of those, how many would have been winning setups if AI had evaluated? (Forward-price replay.)
  3. KZ boundary analysis: CANDIDATEs in first/last 5min of KZ vs middle — is WR uniform? (If edge-of-window WR drops, boundary definition is wrong.)
  4. Bias-source impact: WR by `bias_source` (D1 vs H4 vs H1 dominant). Which source produces the highest-WR CANDIDATEs? (Could justify re-weighting.)
  5. **Missing structure hypothesis:** does market_state.py miss OB types (breaker blocks, mitigation blocks, inverse FVGs)? Sample 10 losing NO_TRADEs where forward price hit target — what structure is visible that we don't detect?
- **Output:** `research/b_deep_audit_2026-04-19/phase1/zeta_market_state_prechecks.md`

---

**Agent η — Alternative pattern discovery**
- **Question:** are there edge patterns we don't trade? What would we find if we clustered the winning NO_TRADEs?
- **Inputs:** same as γ + shadow feature logs.
- **Deliverables:**
  1. Take all NO_TRADE records that hit forward +1.5R (from γ's output). Cluster by feature vectors — what common pattern(s) emerge?
  2. Test 3 candidate alternative edges:
     - **FVG-only setups** (no OB alignment required)
     - **Liquidity sweep + displacement** (no retest required)
     - **Session reversal at equilibrium/fib50** (mean-reversion)
  3. For each candidate edge: n, WR, expectancy, p-value vs coin-flip, robustness across instruments.
  4. Rank candidate edges by expected R/month contribution if added to pipeline.
  5. Explicit check: do any high-WR patterns concentrate outside current KZs? (Extended-hour edge?)
- **Output:** `research/b_deep_audit_2026-04-19/phase1/eta_alternative_patterns.md`

---

**Agent θ — Prompt + context integrity**
- **Question:** is the prompt itself limiting us? Blind spots, biases, truncation, inconsistency?
- **Inputs:** `src/prompts/primary_analyzer_prompt.py` (full file), `src/components/primary_analyzer.py` for call site, sample of large MSOs sent to AI.
- **Deliverables:**
  1. Prompt word-budget analysis: how close does the user message get to effective limits? Is the MSO being truncated?
  2. Field-coverage audit: does the prompt ask the AI to evaluate every relevant structure (OB + FVG + breaker + liquidity + bias + session context)? What's MISSING?
  3. Bias-inducing language scan: does the prompt push the AI toward LONG over SHORT, or toward premium over discount, or toward certain sessions?
  4. Output-format rigidity: can the AI express nuance (e.g., "good setup but weak bias") or is it forced into binary CANDIDATE/NO_TRADE?
  5. Proposal list: top 5 prompt changes ranked by expected impact. No prompt changes ship — scope only (CEO-approval gate).
- **Output:** `research/b_deep_audit_2026-04-19/phase1/theta_prompt_integrity.md`

---

### Phase 2 — 8-agent parallel cross-review (after Phase 1 completes)

Each Phase 2 agent reviews ONE Phase 1 output. Independent agent, independent read, same data access. Opus 4.7, max effort. Brief:

> You are reviewing the attached research output for rigor. Check: (1) are all statistical claims backed by data file:line citations? (2) are p-values corrected for multiple comparisons? (3) is n sufficient (≥30 for any hard claim, ≥20 for exploratory)? (4) are there plausible alternative explanations the author missed? (5) is the methodology reproducible? (6) is the conclusion calibrated to the evidence strength? Output: a verdict paragraph + list of concerns ranked by severity + a reproducibility-rating (1-5).

**Outputs:** `research/b_deep_audit_2026-04-19/phase2/<alpha|beta|...|theta>_review.md`

### Phase 3 — Hypothesis testing (after Phase 1 + Phase 2)

**Main thread** selects 3-5 top hypotheses from Phase 1 (ranked by expected impact × evidence quality). Each gets a testing agent (Opus 4.7, max effort) with explicit null hypothesis + test protocol + data subset + statistical threshold.

Tentative slate (main thread confirms based on Phase 1 findings):
- **Test 1:** "We are the liquidity" — replicate ε's finding on a different data slice (e.g., Oct-Dec 2025 from batch KB)
- **Test 2:** Decay localization — test δ's quarterly decay hypothesis on out-of-sample data
- **Test 3:** POI premium filter — replicate NAS100's 0W/6L premium-zone finding on XAUUSD at n≥30
- **Test 4:** D1-bias-lag gate signal — test whether the 20-consecutive threshold (logger default) correlates with loss rate
- **Test 5:** Highest-ranked alternative pattern from η

**Outputs:** `research/b_deep_audit_2026-04-19/phase3/test_N_<name>.md`

### Phase 4 — Chairman synthesis

ONE Opus 4.7 max-effort agent. Reads all 8 Phase 1 + 8 Phase 2 + 3-5 Phase 3 outputs. Full context of session 34's prior synthesis. Produces the **unified diagnostic verdict**.

Required sections in the output:
1. **Where is the edge leaking?** Ranked 1-N with (a) evidence strength, (b) estimated R impact, (c) fix difficulty.
2. **Arbitrage hypothesis:** supported / not supported / inconclusive — with confidence interval.
3. **Decay attribution:** execution vs AI vs market vs regime — percentages if defensible, else ranked.
4. **Top 3-5 actions to beat decay**, ranked by expected R recovery per difficulty unit. For each: effort estimate, CEO-approval needed?, live blast radius.
5. **New patterns worth exploring**, if any. Top 3.
6. **Tuesday go/no-go recommendation:** per-instrument. With explicit rationale.
7. **Long-term strategic read:** is the ob_retest edge viable for 6+ months, or do we need successor edge(s)?

**Output:** `research/b_deep_audit_2026-04-19/phase4/CHAIRMAN_SYNTHESIS.md`

**Commit after Phase 4:** `research(b-deep-audit): 4-phase diagnostic audit synthesis`

---

## 6. Tier C — Validation + ops (run during or after Tier B)

### C1. Honest Monte Carlo at current expectancy
- Re-run MC against redacted_account Stellar 2-Step $100K rules at Exp sweep: +0.10R / +0.15R / +0.20R / +0.25R.
- Use the chairman verdict to pick the expectancy we actually believe.
- **Output:** `research/c1_mc_redacted_account_honest/results.md`

### C2. redacted_account Stellar 2-Step $100K terms audit
- Pull canonical rules; compare line-by-line to `config/profiles/redacted_account.yaml`.
- **Output:** `research/c2_redacted_account_terms_audit/verdict.md`
- Flag mismatches; CEO approves any config change.

### C3. Telegram alert smoke test
- All alert types. Coordinate with CEO for bot-repo access if needed.

---

## 7. Tier D — CEO-approval scope (produce, don't ship)

### D1. FX 4-5 dp precision prompt fix
- Mechanism exists (`src/prompts/primary_analyzer_prompt.py:14` `_PRICE_FMT`); AI ignores it on OUTPUT.
- Scope: prompt-level output instruction + post-AI decimal-count validator.
- **Output:** `research/d1_fx_precision_prompt_scope/proposal.md`

### D2. T2.prompt require non-zero `sl_buffer_applied`
- Unresolved #5 in CLAUDE.md.
- Scope: prompt change + interaction analysis with T2.9 gate-fix decision.
- **Output:** `research/d2_sl_buffer_prompt_scope/proposal.md`

### D3 (NEW). Any prompt change proposed by Phase 1 agent θ
- Scoped proposal doc only; no ship.

---

## 8. Tier E — Stretch goals

- **E1.** Watchdog coverage audit — every live failure mode → watchdog mapping
- **E2.** T7 simulator constant audit — grep for other instrument-unaware hardcoded values beyond `_FILL_EPSILON`
- **E3.** Cross-instrument T3.2 replication — extend XAUUSD `sl_beyond_ob` audit to USDJPY / GBPJPY / US30
- **E4.** Historical decay audit — pull pre-2025 MT5 data for an older-era OB edge baseline (tests arb hypothesis if the edge was higher pre-AI)

---

## 9. Exit criteria

**"Complete enough for CEO go/no-go on restart + redacted_account kickoff":**
- [ ] A1, A2, A3 landed
- [ ] Phase 4 chairman synthesis landed — CEO reads it
- [ ] C1 honest MC landed
- [ ] C2 redacted_account terms audit landed
- [ ] CLAUDE.md updated with session 35 closures

**"Unlock full strategic read":**
- [ ] Phase 3 tests all landed
- [ ] D1 + D2 scope docs landed (not shipped)
- [ ] Chairman delivered per-instrument Tuesday recommendation

**"Research stretch complete":**
- [ ] D3 scope docs for any prompt changes
- [ ] E1-E4 stretch goals executed

---

## 10. Decisions deferred (explicit)

1. **Rolling restart** — CEO calls after chairman synthesis. Hard cutoff: Sunday ~22:00 UTC (market open) OR Monday pre-market if session 35 runs long.
2. **Any prompt change ship (D1/D2/D3)** — CEO-approval after scope docs land.
3. **NAS100 live enablement** — depends on A2 + arbitrage verdict.
4. **FX live enablement (EURUSD + FX instruments beyond USDJPY/GBPJPY)** — blocked on A1 + A3 + D1 ship.
5. **T2.9 gate fix** — blocked; may be resolved by D2 OR Phase 4 verdict.
6. **New edge deployment** — any η-proposed alternative edge requires full re-validation pipeline (batch + out-of-sample + shadow) before live.

---

## 11. Known constraints + gotchas

1. **Research sim scripts don't auto-load `.env`** — prefix bash commands with `set -a && source .env && set +a` (per memory entry).
2. **OpenRouter elephant-alpha quota ~1000/day** if used — serialize.
3. **CLAUDE.md ≤30k char budget** — after session 35, prune chronological deltas; don't bloat.
4. **Worktree / `Agent` tool compatibility** — session 34 WT D reported "Agent tool unavailable in worktree" for council tasks. Phase 1/2/3/4 dispatches run from the **main thread**, not worktrees, to avoid this.
5. **Worktree branch-base staleness** — if any agent is dispatched via `isolation: "worktree"`, the worktree branches from current main HEAD automatically in a fresh session. Session 34 hit stale-base only because worktrees were created before rebasing. Not a risk for fresh session.
6. **Commit-time doc hygiene** — anything session 35 closes from CLAUDE.md's "unresolved" list → update CLAUDE.md in SAME commit.
7. **Budget envelope reality** — session 35 API spend **is ~$0**. All agent calls go through Claude Code plan compute via the `Agent` tool. The $50/mo Anthropic API balance is reserved for live trading (primary_analyzer on every M15 KZ candle across 5 instruments, ~$30-50/month).

---

## 12. Cost model (revised from initial draft)

| Category | Bills against | Session 35 estimate |
|---|---|---|
| Phase 1 (8 agents) | Claude Code plan compute | covered by plan |
| Phase 2 (8 agents) | Claude Code plan compute | covered |
| Phase 3 (3-5 agents) | Claude Code plan compute | covered |
| Phase 4 (1 agent) | Claude Code plan compute | covered |
| A1 code + replay | None | $0 |
| A2/A3 re-scoring | None (replay existing JSON) | $0 |
| C1/C2/C3 | None (code + docs) | $0 |
| D1/D2/D3 scope docs | Claude Code plan compute if agent-assisted, else main-thread | $0 API |
| **API total** | **$0 expected** | |
| **API contingency** | Any spot-check fresh Sonnet call via `simulate_t7_live_period.py` | cap at $5 |

Live trading continues billing against the $50/mo API balance independent of session 35.

---

## 13. Recommended execution order

1. **Main thread:** A1 (epsilon fix) → test → commit. ~2h.
2. **Main thread:** A2 + A3 (re-scoring replays) → commit. ~30min each.
3. **Main thread:** dispatch Phase 1 (8 agents in parallel, single message with 8 `Agent` tool calls, `model: "opus"`). Wait.
4. **Main thread:** once Phase 1 returns, dispatch Phase 2 (8 parallel reviews, `model: "opus"`). Wait.
5. **Main thread:** read Phase 1 + Phase 2, select 3-5 top hypotheses → dispatch Phase 3 (3-5 parallel testers, `model: "opus"`). Wait.
6. **Main thread:** dispatch Phase 4 chairman (`model: "opus"`). Wait.
7. **Main thread:** commit all Phase 1-4 outputs.
8. **Main thread:** run C1 (honest MC with chairman's expectancy) + C2 (terms audit). Commit.
9. **Main thread:** produce D1 + D2 + any D3 scope docs (agent-assisted optional). Commit.
10. **Main thread:** update CLAUDE.md with session 35 closures. Commit.
11. **Main thread:** C3 Telegram smoke test (coordinate with CEO).
12. **Main thread:** final close handoff `36_apr19_session_close_handoff.md` + CEO-facing summary.
13. **Main thread:** CEO reviews chairman. Restart decision. If go, CEO drives restart + agent tails logs.

**Wall-clock estimate:** 6-10 hours of main-thread work. Phase 1-4 agent dispatches each take 15-60min depending on Opus 4.7 analysis depth.

---

## 14. Final report structure (end-of-session deliverable)

Single CEO-facing summary committed at session close. Must contain:
1. **What shipped** — commit list with one-line impact per
2. **Chairman verdict** — copy-paste of Phase 4 executive summary
3. **Decay attribution** — the answer to "is the edge dying or is our execution degrading?"
4. **Arbitrage hypothesis verdict** — supported / not / inconclusive
5. **Top 3-5 actions** — with ship-status (ready / scoped / blocked-on-approval)
6. **Per-instrument Tuesday recommendation** — go / no-go for each of 5 live + NAS100/EURUSD
7. **Rolling restart recommendation** — timing + sequence

Commit as `.context/02_session_handoffs/36_apr19_session_close_handoff.md`.

---

*Last updated: 2026-04-19, end of session 34. Authoritative for session 35 execution. If any instruction here conflicts with CLAUDE.md, CLAUDE.md wins — but flag the conflict to CEO.*

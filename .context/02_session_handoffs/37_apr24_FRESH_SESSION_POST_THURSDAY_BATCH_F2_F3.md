# Session 37 → Fresh session — POST-THURSDAY-BATCH: F2/F3 + residual cleanups

**Handoff from:** Session 37 close (2026-04-24 ~04:20 UTC)
**Kickoff window:** Post-Thursday-audit batch is merged + live. Fleet running on merged code since 04:18:55 UTC. Account $99,287.62 intact.
**Your role:** Execute F2 (market_state structural fix prototype) + F3 (backtest validating edge survives on mixed-direction sample) + R1-R6 residual unresolved-item cleanups. Close the last remaining gap between the system's theoretical capability and its current LONG-only live behavior.
**CEO directive (session 37 verbatim):** *"how can we know that F2 and F3 land successfully and the edge survives on a mixed direction sample, give me all the next steps needed to make the best out of the trading system and we can dispatch parallel agents for them in the next session"*

---

## MANDATORY FIRST ACTIONS (do these before anything else)

1. Read `CLAUDE.md`.
2. Regenerate + read `.context/LIVE_STATE.md`:
   ```
   python scripts/generate_live_state.py
   ```
3. Read this handoff (you are here).
4. Read `.context/06_decisions/ADR-004-SUMMARY.md` — the structural-bias fix decision document.
5. Read `research/reviews_2026-04-24/FINAL_VALIDATION_STATUS.md` — what landed in session 37.
6. Skim `git log --oneline -15` — 9 merges + fixes from session 37 now on main.
7. Verify fleet health: `tail -5 logs/xauusd.log` + check heartbeat via `cat pipeline_state/heartbeat.json`.

---

## What was shipped in session 37 (durable summary)

Nine commits on main (HEAD `5025088`):

| Commit | Scope |
|--------|-------|
| `c237a0c` | research(audit): Thursday 2026-04-23 forensic + cold reviews + ADR-004 |
| `620ec08` | merge(thursday-batch): A1+A2+A3+A5+A6+A8 + A1-literal fixup |
| `02cba53` | merge(m2a): tests/replay/ permanent infrastructure |
| `7ebed7a` | merge(m2b): canary fixture expansion 19 → 60 |
| `a9dc373` | merge(a4): prompt v2 FX precision + M15-as-H1 substitution ban |
| `b01532e` | test(replay): bump PERMISSIONS_DIVERGENCE_CEILING 16 → 30 |
| `c1697b3` | chore(canary): regenerate baseline against V2 prompt |
| `7da43af` | docs(claude.md): session 37 closures + new unresolved |
| `5025088` | fix(orchestrator): canary subprocess timeout 120 → 360s (regression caught post-merge) |

22 agents dispatched this session (6 forensic + 8 fix/audit + 8 review + 5 infra + 1 ADR). All cold-reviewed. ~$10-15 total trading-API cost. Account balance unchanged at $99,287.62 across two restart cycles.

See `research/reviews_2026-04-24/FINAL_VALIDATION_STATUS.md` for the full merge plan + per-branch review summaries.

---

## Principal objective

**Close the market_state structural bullish bias** (ADR-004, CEO-approved Option D net-score classifier) via prototype → backtest → shadow → promote. Until this lands, the system is blind to SHORT opportunities — every LONG CANDIDATE since initial commit `436c16b` was produced against a detector that never emits bearish labels.

Secondary objective: clear 6 residual unresolved items from session 37.

---

## Success criteria — how we know F2 + F3 landed

### F2 prototype (Option D net-score classifier) — PASS conditions

| Check | Target |
|---|---|
| Synthetic fixture tests | Pure uptrend → bullish; pure downtrend → bearish; flat → neutral; V-reversal → flips direction at reversal; pure random walk → neutral ~70% of windows |
| Unit tests | pytest on `identify_structure_v2` green; 15+ cases |
| Replay test flips | `tests/replay/test_structure_detector_labels.py` transitions from **XFAIL → PASS** (30-day historical window: no direction >90% of labels) |
| Label distribution sanity on historical data | Across 30 days × 5 instruments: bullish 30-55%, bearish 30-55%, neutral 10-30% |
| No crash on edge cases | Empty H1 window, single swing, NaN values, tied scores, very-short windows handled gracefully |
| No regression on current production snapshot | Option D applied to `pipeline_state/02_market_state.json` produces a label consistent with recent price action |

Any fail → F2 is not ready, investigate before F3.

### F3 backtest — "edge survives on mixed-direction sample"

Run `scripts/simulate_t7_live_period.py` with fixed detector on representative slices. Compare to pre-fix baselines at `research/t7_live_simulation/` (session 35's post-FA-2 runs are the most recent apples-to-apples reference).

**Minimum tier ($54, XAUUSD Jan-Feb + Mar-Apr):**

| Metric | Pre-fix (batch) | Post-fix target | Interpretation |
|---|---|---|---|
| XAUUSD LONG WR | 62% (n=129) | ≥ 55% (allow 7pp degradation) | LONG edge preserved |
| XAUUSD SHORT WR | N/A (0 SHORTs ever) | ≥ 50% at n ≥ 20 OR honest N/A if still 0 | SHORT edge exists OR correctly rare |
| XAUUSD combined WR | 62% | ≥ 55% | Edge doesn't collapse under fix |
| XAUUSD combined expectancy | +0.2R/trade (raw p=0.046) | ≥ +0.10R/trade | Still profitable after bias correction |
| CAND rate | 10.3% baseline | 8-20% | Not too sparse, not flooding |
| MaxDD on sim | N/A | ≤ 8% | Acceptable for $100K account |

**Mid tier ($162, XAUUSD + USDJPY + EURUSD × 2 slices) — optional stretch:**

- USDJPY LONG WR ≥ 68% (8pp from batch 75.8%); SHORT WR ≥ 50% at n ≥ 15
- EURUSD combined WR ≥ breakeven (no batch baseline — exploratory)
- Fleet combined expectancy ≥ +0.08R/trade

**Red flags triggering council-worthy review:**
- XAUUSD LONG WR drops below 50% → batch numbers may be regime artifact, not edge
- SHORT WR <40% consistently → system's signals are bullish-specific, not general
- CAND rate jumps >50% → prompt needs recalibration for new label mix
- MaxDD exceeds 10% → sizing rules need revisit

### F2 → live promotion gate (shadow mode)

Once F2 + F3 pass:
- Deploy Option D alongside current detector as `compute_market_state_v2` (dual-compute on every candle, log divergences)
- Shadow mode **≥ 7 days** — collect ≥ 100 divergence events
- Sample 20 random divergences, manually verify which is correct
- **Promotion gate**: v2-correct ≥ 80% of sampled divergences AND zero obvious error cases AND no live production regression in shadow window AND backtest numbers above thresholds
- Only then: flip config flag to route production through v2 + retire v1

---

## Parallelizable work streams

### Stream 1 — F2 market_state fix (sequential internally)

| # | Agent | Dependency | Scope |
|---|---|---|---|
| F2.1 | Prototype Option D | — | Write `identify_structure_v2` (net-score: `score = (hh + hl) - (lh + ll)`, `dead_zone_threshold = max(2, min_swings // 4)`). Unit tests + synthetic fixtures. Commit to branch. |
| F2.2 | Independent reviewer | After F2.1 | Cold review — off-by-one, tie-break semantics, edge cases. Hand-verify 5 historical MSOs. |
| F2.3 | Shadow-mode wiring | After F2.2 APPROVE | Config flag `market_state.detector_version` (v1/v2_shadow/v2); dual-compute in shadow mode; divergences logged to `shadow_logs/structure_detector_divergences.jsonl`. |

### Stream 2 — F3 backtest (highly parallelizable per memory note)

Per `feedback_parallelize_aggressively_tier4.md`: split into parallel slices.

| # | Agent | Scope | Cost |
|---|---|---|---|
| F3.1 | XAUUSD Jan-Feb 2026 sim | Option D detector | ~$13 |
| F3.2 | XAUUSD Mar-Apr 2026 sim | Same | ~$13 |
| F3.3 | USDJPY Jan-Apr 2026 sim | Same | ~$15 |
| F3.4 | US30_cash Jan-Apr 2026 sim | Same | ~$15 |
| F3.synth | Synthesis agent | After all 4 | Aggregate metrics, compute post-fix WR/expectancy/MaxDD, write report |

All 4 slices dispatch in parallel; synth waits. Budget: ~$54-60.

### Stream 3 — Residual session-37 unresolved items (fully independent)

| # | Agent | Scope | CEO approval? | Worktree |
|---|---|---|---|---|
| R1 | V3 prompt iteration | Close `touches<2` / `reachable-distance` loophole V8 flagged. Add explicit prompt rejection for invented NO_TRADE reasons. Run canary. | Yes | Yes |
| R2 | `skip_first_ny_candle` dead-code fix | Fix `orchestrator.py:1999` nested lookup. XAUUSD 13:00-13:15 candles should actually skip. Counterfactual: how many XAUUSD evaluations in 13:00-13:15 window over last 30 days, what did they decide? | Yes (restores logic) | Yes |
| R3 | Partial-close price=0.0 fallback | Extend `close_position` fallback pattern to `_execute_tp1_partial` + `_execute_tp2_partial`. Unit tests. | No (bug fix) | Yes |
| R4 | Canary timeout → config | Move `timeout=360` to `config/agent_config.yaml::canary.subprocess_timeout_s`. Add pytest validating `timeout ≥ N_fixtures × 4.5`. | No (observability) | Yes |
| R5 | M5 `$%.2f` FX truncation | `m5_refinement.py:541, 546` — instrument-aware price format. | No (cosmetic) | Yes |
| R6 | Pending-intent flake fix | `test_pending_intent_stale_before_first_kz_discarded` — 5+ reviewers flagged it. Diagnose time-of-day dependency, fix deterministically. | No (test fix) | Yes |

### Stream 4 — Replay infrastructure enhancements (optional, lower priority)

| # | Scope |
|---|---|
| I1 | Shadow-log invariance tests in `tests/replay/` |
| I2 | API savings metric on pre-AI gate |
| I3 | Regime-tagged replay subsets (bullish/bearish/ranging) |
| I4 | Baseline CAND rate snapshot test |
| I5 | Cross-instrument parametrization |

Pick up after F2/F3/R* ship.

### Stream 5 — Continuous live monitoring (no agent; periodic checks)

| Cadence | Check | Alert |
|---|---|---|
| Daily | Pre-AI gate skip count per instrument | +/- 50% vs 7-day rolling |
| Daily | OB continuation rate (`ob_continuation_monitor`) | <60% alarm, <50% critical |
| Weekly | GBPUSD L2-reject rate on `sl_beyond_ob` | Should drop from 63.6% post-V2 |
| Weekly | CAND rate per instrument (from evals jsonl) | >25% or <3% = flag |
| Per-fill | Telegram `$/R` notification arrived (A1 + FA-4) | Missing = bug recurrence |
| Per-fill | Trade record `execution` + `exit` fields populated (A1) | Null = `kz_trades` bug recurrence |

---

## Dispatch plan for fresh session

**Wave 1 (immediately, ~6-7 parallel agents):**
- F2.1 prototype Option D
- R1 V3 prompt iteration
- R2 skip_first_ny_candle fix
- R3 partial-close fallback
- R4 canary timeout → config
- R5 M5 FX format
- R6 pending-intent flake

All worktree-isolated. Budget: ~$1-2 API per canary-running agent. Total: ~$5-10.

**Wave 2 (after F2.1 returns + F2.2 reviewer approves):**
- F3.1-F3.4 parallel backtest slices ($54)
- F2.3 shadow-mode wiring (starts once F2.1 merges)

**Wave 3 (after F3.synth):**
- Decision point: do F3 numbers pass criteria? Yes → F2.3 shadow-mode deploys. Ambiguous → council pattern for interpretation. Fail → escalate to CEO, investigate.

**Wave 4 (after ≥ 7 days of shadow mode):**
- Divergence sampling agent (weekly) to classify v1-vs-v2 disagreements
- Promotion decision after ≥ 100 divergences collected

---

## Known gaps / risks you are INHERITING

1. **Edge numbers suspect until F3 lands.** Every "validated number" in CLAUDE.md (62% XAUUSD WR, 70% OB continuation, MC 99.4% FTMO, etc.) was computed on a LONG-only sample. Treat as "known for LONG direction; unknown for SHORT" until backtest re-derives.

2. **V2 prompt is partial mitigation.** V8 found model still games the prompt on `touches<2` / `reachable-distance` patterns that V2 explicitly forbids. R1 (V3 iteration) closes this.

3. **skip_first_ny_candle silently ignored.** XAUUSD 13:00-13:15 NY candles have been evaluating despite CLAUDE.md saying skip. R2 fixes. Minor impact but a correctness issue.

4. **First restart after A1 persistence fix loses pending limits.** Subsequent restarts are clean, but the FIRST one still triggered `new_day → cancel` behavior today (lost USDJPY `lim_2026-04-24_0016`, age 0.5h). Not a regression; inherent to deploying a persistence-dependent fix. Expect clean behavior from now on.

5. **Canary cold-start cost.** First instrument to boot pays ~270s canary subprocess cost (60 fixtures × ~4.5s each). Subsequent instruments hit `canary_cache.json`. Only matters on full-fleet restart; normal day has no impact.

---

## Things to NOT do

- **Don't merge F2 to main until shadow mode completes.** Option D is an architectural change — needs the full validation gate.
- **Don't re-run in-sample data to validate F2.** Per CLAUDE.md §Prohibited. F3 uses the same scripts but the same inputs; assume scope-out is understood.
- **Don't enable FX instruments live.** EURUSD + GBPUSD remain NO-GO per Chairman. R1 (V3 prompt) is a prerequisite, not a license.
- **Don't adjust XAUUSD risk.** 0.5% per FA-2 is shipped + CEO-confirmed.
- **Don't enable heartbeat flatten kill switch.** Stays DISABLED per unresolved #2.
- **Don't ship T2.9 `sl_beyond_ob` strict-< → <=.** Chairman rejected per unresolved #3.
- **Don't modify the pre-AI gate direction-aware logic.** It's formalized via A3; V4 reviewer verified bit-exact with live code.

---

## Agent usage guidance (project-specific)

- CLAUDE.md ~30k chars; every `Agent()` dispatch inherits it. Keep parallel dispatches bounded — memory note `feedback_claudemd_size_discipline.md`.
- For F3 backtest slices: use `run_in_background: true` per memory note `feedback_long_running_subprocess_pattern.md` — sims take 30-60 min. Dispatch from main thread; don't delegate to a sub-agent that will die on return.
- Cold-review pattern: for each code-changing agent, dispatch an independent reviewer. Budget ~$0 per review (read-only). Catches hallucinations that the implementing agent misses.
- Council pattern (3-stage) is NOT needed unless F3 results are ambiguous. Use single agents for execution + review.
- Per memory note `feedback_billing_tracks_distinction.md`: agent dispatches run on Claude Code subscription (free). Only canary runs + T7 sims hit the $50/month Anthropic API cap.

---

## Reference map

| Doc | Purpose |
|-----|---------|
| `CLAUDE.md` | Source of truth — session 37 closures in §What is unresolved items 4-8 |
| `.context/LIVE_STATE.md` | Auto-generated — HEAD `5025088` |
| `.context/06_decisions/ADR-004-market-state-structural-bullish-bias.md` | Full 8-option enumeration; Option D selected |
| `.context/06_decisions/ADR-004-SUMMARY.md` | 2-minute exec summary |
| `research/reviews_2026-04-24/FINAL_VALIDATION_STATUS.md` | Session 37 consolidated status + merge plan |
| `research/reviews_2026-04-24/SYNTHESIS.md` | Thursday 2026-04-23 forensic audit synthesis |
| `research/directional_concentration_audit_2026-04-24/V1_INDEPENDENT_VALIDATION.md` | 98% confidence bug confirmation |
| `src/components/market_state.py:216-257` | `identify_structure` — the code to replace |
| `tests/replay/test_structure_detector_labels.py` | Will flip XFAIL→PASS when F2 lands |
| `scripts/simulate_t7_live_period.py` | The backtest tool (parallelize per memory note) |
| `research/t7_live_simulation/` | Pre-fix baselines for F3 comparison |
| `config/agent_config.yaml` | `pre_ai_gates.h1_poi_availability_enabled: true` — gate is live |
| `config/profiles/redacted_account.yaml` | Active profile |
| `scripts/canary_fixtures/` | 60 fixtures; run `python scripts/canary_test.py` for regression |
| `knowledge_base/meta/canary_cache.json` | Canary cache (refreshed per run) |

---

## Communication pattern the CEO prefers

- Brutally honest. Don't soften confidence numbers; don't hedge to be polite.
- Before each Wave dispatch: one-sentence plan + dispatch. After each Wave: one-paragraph status.
- Show diffs BEFORE commit for any prompt/config/live-code change.
- Flag any discovery that changes the F2/F3 plan IMMEDIATELY.
- Memory notes: `feedback_*` for durable rules; `project_*` for session-specific facts. Date-stamp relative-date references.

---

## Closing directive

The edge is LIVE and validated on LONG-only samples. Every "validated number" is a LONG-only claim. The highest-leverage change this session can make is closing the structural bias so the system can detect SHORTs. Ship F2 right + backtest F3 honestly + shadow-deploy safely → the trading system's capability moves from ~45-55% to ~65-70% of theoretical. Everything else (R1-R6, Stream 4 enhancements) is incremental.

Good luck.

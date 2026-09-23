# Handoff to Fresh Session — GTOS ML Research Program Phase 4

**Written:** 2026-04-29 by outgoing orchestrator (context heavy after Q1.3 post-mortem + Q1 Track A backfill + Q1 Track B literature program).
**For:** Fresh session that will drive Phase 4 (CEO triage + experimentation) on Opus 4.7 + max effort.

This doc is the entry point. Read it FIRST, then read the canonical artifacts it references.

---

## Where you are in the program

GTOS is a live algorithmic trading system on redacted_account $100k 2-Step (XAUUSD/XAGUSD/USDJPY/GBPJPY/GBPUSD/US30_cash/NAS100). Q1 of a 4-quarter ML research program ran:

- **Q1.1 → Q1.2 → Q1.3** ML modeling (K54 v2 catalog, 1,219 features). **Q1.3 FAILED** under CPCV-honest accounting (mean lift +0.0309 vs target +0.04; CPCV-honest p=0.675 not the Stouffer-naive 0.0015).
- **Q1 Track A (data-first):** 2022-2023 OHLCV + structure backfill. Added 1,798 trades; total cohort n=2,326 (+3.4×). All 7 instruments now have ≥1000 M15 candles in 2022-2023.
- **Q1 Track B (literature program):** 4-phase pipeline complete. ~1,100+ papers cataloged across 22 domains; 6 group syntheses produced; 178-item master backlog + 30-item ranked hypothesis backlog written.

**Phase 4 = CEO triage + experimentation.** That's what you'll drive.

---

## Canonical artifacts (read in this order)

### Tier 1 — must-read

1. **`CLAUDE.md`** — project bootstrap. Standing rules, prohibited behaviors, validated numbers, agent reliability rules.
2. **`.context/LIVE_STATE.md`** — regenerate first via `python scripts/generate_live_state.py`. Authoritative current state.
3. **`research/ml_program/RESEARCH_PROGRAM_STRATEGY.md`** — multi-track research model (data + literature + experimentation in parallel).
4. **`research/ml_program/MASTER_BACKLOG.md`** — 178 items, stable IDs (M-N, K-N, V-N, A-N, R-N, etc.). Your dispatch unit.
5. **`research/ml_program/literature/HYPOTHESIS_BACKLOG.md`** — 30 ranked hypotheses + Q1.4 spec recommendation + 9 reframings + 9 architectural composites.
6. **`research/ml_program/audit/Q1_3_POSTMORTEM_SYNTHESIS.md`** — what Q1.3 actually told us; what's open.
7. **`research/ml_program/audit/AMBIGUITIES_AND_OPEN_QUESTIONS.md`** — 11 critical findings + 35 open questions from the post-mortem.

### Tier 2 — read when relevant

8. **`research/ml_program/PRE_REGISTERED_HYPOTHESES.md`** — Q1.1/Q1.2/Q1.3 with terminal status. Q1.4 will be appended.
9. **`research/ml_program/KILLED_HYPOTHESES.md`** — Q1.3 why-it-failed memo.
10. **`research/ml_program/dispatch_log.md`** — running log of every agent dispatch + outcomes.
11. **`research/ml_program/literature/synthesis/group_a_foundations.md`** ... `group_f_ai_ml_quantum.md` — 6 group syntheses (~270 papers each).
12. **`research/ml_program/feature_catalogs/CATALOG_v2.md`** — 1,219-feature K54 v2 catalog (will be revised in K54 v3).

### Memory references (auto-loaded)

- `feedback_research_program_multitrack` — pursue chart data + literature + experimentation in parallel; CEO approves unlimited Google research.
- `project_literature_program_taxonomy_22_domains` — 22-domain taxonomy + 4-phase pipeline.
- `feedback_subagent_dispatch_opus47_max_effort` — every Agent call sets `model: "opus"` + leads prompt with explicit max-effort directive.
- `feedback_paired_fixed_hp_discipline` — per-path HP selection inflates CPCV effect ~2×; use fixed-HP + PBO.
- `feedback_decay_is_ceo_number_one_concern` — prioritize backtest-shadow over live-shadow; treat 30d shadow as upper bound; accept higher API spend to compress timelines.
- `feedback_walk_level_evidence_not_predictive` — walk-level pre-trade probability is not realized-R substitute.
- `feedback_billing_tracks_distinction` — Claude Code subscription (agent dispatches) vs Anthropic API ($50/mo cap; auto-reload disabled). Most ML-research work is subscription-only.

---

## The 5 strategic anchors

These should drive every Phase 4 decision:

1. **Edge decay is publication-and-replication property, NOT mechanism failure** (McLean-Pontiff 2016 + Lo AMH 2024). F11's 73% decline is INSIDE the industry distribution. The risk isn't individual-edge decay — it's **discovery-rate stall**.

2. **GTOS at $100k AUM is BELOW capacity-decay band** (Naik-Ramadorai-Stromqvist 2007 binds at $250M+). **Renaissance Medallion model > LTCM model.** Aggregate small uncorrelated edges; don't optimize for one large OB-zone advantage.

3. **K54 v3 should target features UNCORRELATED with OB-precision.** Grow the portfolio, don't re-validate the existing edge.

4. **AUC-vs-realized-R disconnect is structural** in proxy-based learning (Y. Li 2023 ICAIF; Lucchese 2024 Sharpe ceiling ~0.5). **Meta-labeling (Lopez de Prado 2018) is the architectural fix** — secondary classifier on triple-barrier labels.

5. **Treat all literature-derived predictions as upper bounds.** Academic Sharpes typically halve in production. Plan for 50% realization.

---

## The Phase 4 dispatch plan I recommend

Tier 1 — fire IN PARALLEL on Day 1 (B-8 quick-win bundle, all subscription-only, all independent):

| Item | What it answers | Wallclock |
|---|---|---|
| **M-1 + M-2 + M-3 + M-4** DSR retroactive | Which "validated" lifts (J46-J49, K54, S79) survive Bailey-López de Prado correction? May invalidate shipped findings. | ~3-4 hours |
| **C-1** Coval-Shumway second-half-of-session A/B | Does OB-retest in second half of session outperform first half (per distressed-trader literature)? Free A/B on existing data. | ~2-3 hours |
| **NA8** Babu 2020 decomposition | What fraction of H2-2026 LONG decay is move-magnitude (vol regime) vs signal-translation? **Gates Q1.4 priority order between vol-conditioning and architecture.** | ~3-4 hours |
| **K-4 + P-4** Stoikov micro-price | Implementation in `tick_features.py`. Drop-in for instruments with tick coverage. | ~2 hours |
| **Q-1** DLinear baseline | Must clear K54 v1 ±0.01 AUC. Occam-discipline gate before any deeper sequence model. | ~2-3 hours |
| **L-6 + L-7** HALLUC-2 + Q71 loggers | Token-usage + slippage observability. Closes standing gaps. | ~1 hour |

**Total Day-1 wallclock:** ~3-4 hours in parallel; produces 6 dispatched results synthesized into go/no-go for Q1.4 architecture.

---

## Tier 2 — Day 2-3: synthesize and lock Q1.4 spec

Based on Day-1 outputs, decide Q1.4 priority order:

- **If NA8 shows vol-managed sizing alone auto-recovers ≥40-60% of LONG decay** → ship Component 3C (V-9 / H-2 / B-2) FIRST as a quick win; K54 v3 (K-18 / H-1 / B-1) has less to prove.
- **If NA8 shows < 40% auto-recovery** → K54 v3 master bundle (K-18) is the full Q1.4 architectural commit.

Read DSR sweep results; adjust S79 / J46-J49 / K54 priors if anything failed.

Pre-register Q1.4 to `PRE_REGISTERED_HYPOTHESES.md`. Locked spec from `HYPOTHESIS_BACKLOG.md` §8.

---

## Tier 3 — Week 1-2: Q1.4 modeler dispatch

Single comprehensive Opus 4.7 max-effort dispatch:

- K54 v3 master bundle (B-1) per spec.
- Component 3C parallel evaluation (V-9 / B-2) on n=2,326 cohort.
- Per-instrument-group specialists (A-1..A-7, A-11) where data permits.

Validation: paired-fixed-HP CPCV + DSR + effective-N + B=1000 null + 2 cross-period splits + 4-of-5-effective-instrument-groups gate.

Probability of PASS: 50-65% per Phase 3 estimate.

---

## Tier 4 — Week 3-4: risk-policy + AI grounding

If Q1.4 PASSES:

- Busseti-Boyd RCK (R-9 / B-3 / H-5) replacing S79 uniform 2%.
- Tool-use grounding for Component 3A (B-5: L-1 + L-4 + L-6 + L-7 + L-8). Cuts LLM hallucination 70-80%.

If Q1.4 FAILS:

- Why-it-failed memo to KILLED_HYPOTHESES.md.
- Re-spec Q1.5 informed by failure mode.

---

## Discipline gates (enforce on every dispatch)

1. **Pre-registration** in `PRE_REGISTERED_HYPOTHESES.md` for primary hypotheses.
2. **Paired-fixed-HP CPCV** + **DSR + effective-N** + **B=1000 null** + **PBO < 0.4** + **cross-period robustness gate**.
3. **CPCV-honest training-overlap-weighted SE**, NOT Stouffer-naive.
4. Per-path HP selection inflates effect ~2× — confirm via paired-fixed-HP variant before celebrating.
5. **Subscription-bounded** throughout (no Anthropic API spend on research/data work). Memory `feedback_billing_tracks_distinction`.
6. **All agents Opus 4.7 + max effort** (`model: "opus"` + max-effort line at top of prompt). Memory `feedback_subagent_dispatch_opus47_max_effort`.
7. **Failure protocol**: pass → ship; fail → KILLED memo + re-spec or close.
8. **No production state changes**. Read from `data/`, `knowledge_base/`, `shadow_logs/`. Never modify `src/`, `config/`, `scripts/canary_fixtures/`, `pipeline_state/`.

---

## New questions surfaced during the synthesis (these are good agent-dispatch candidates)

These came up while writing the strategic walk-through. Worth dispatching focused agents on:

1. **DSR rollback discipline.** If S79's +25.8pp doesn't survive DSR + effective-N, do we revert from 2.0% risk in production? When? What's the threshold? — Need a written discipline doc.
2. **2022-2023 backfill bias check.** Mechanical OB candidates may differ from live AI-evaluated trades. Survivorship/methodology bias quantification before Q1.4 cross-period gate.
3. **Component 3C feasibility.** V-1/V-2/V-3 feature feasibility from MT5 data alone (esp. VRP needs implied-vol). Without CBOE feed, what's the proxy quality?
4. **Triple-barrier label reconstruction.** The 2022-2023 backfill cohort needs full barrier-touch sequences for meta-labeling training. Verify F11 mechanical extraction stored enough OHLCV depth.
5. **Master backlog dependency map.** 178 items have hidden dependencies (K54 v3 → volume bars → tick re-sampling). Critical-path ordering not yet mapped.
6. **Inoue-Kilian vs CPCV-honest per-instrument resolution.** Test both protocols on the same data; commit to one with rationale.
7. **QuantMCP / FinAgent transfer to Claude Sonnet 4.6** (literature is GPT-4-class). Small targeted transfer test before banking on the 70-80% hallucination-reduction figure.
8. **Cumulative trial count formal measurement.** I estimated ~200; the actual number affects DSR noise ceiling materially.
9. **Exploratory dispatch mechanism.** Edge-discovery > preservation strategic reframe implies a "literature scout for new signals" recurring agent. Not yet specced.
10. **Walasek λ-context audit.** Which other GTOS gates assume λ=2 outside asymmetric trading contexts and may need re-derivation?

---

## When CEO names an item ID

- **Single-action items** (M-1, K-4, etc.) → dispatch one Opus 4.7 max-effort agent with focused prompt. Reference the master backlog item description as the spec.
- **Bundle items** (B-1 K54 v3, B-2 Vol-Conditioning, B-8 Quick-Win) → dispatch constituent items in parallel where independent, sequential where dependent. Mark master backlog items as IN_FLIGHT then DONE/FAILED.
- **Research-question items** (U-N) → dispatch a research agent with WebSearch + GTOS-data-read access.
- **Composites** (C1-C10 in HYPOTHESIS_BACKLOG.md) → these are pre-bundled deployable units; lock spec, pre-register if primary, dispatch.

Always update `dispatch_log.md` per dispatch. Always update master backlog status fields. Always cross-link results to backlog IDs in dispatch-log entries.

---

## What "done" looks like for Phase 4

- Q1.4 modeler runs to completion with verdict (PASS / FAIL / PARTIAL).
- If PASS: K54 v3 deployable; OOS holdout opens (gate c discipline); Q2 sequence-model phase begins.
- If FAIL: KILLED memo + Q1.5 re-spec OR close Q1 with K54 v3 reframed as supplementary K55-shadow signal.
- Master backlog items closed move to DONE; failures get root-cause memos.

---

## Operational ops (out-of-scope for ML program; flag for main thread)

- `_trade_index.json` frozen at 2026-04-04 (`research/operations/trade_index_frozen_bug_2026-04-28.md`).
- NDX100 vs NAS100 alias documentation across codebase.
- Live `trade_records/` April 2026 records all `execution: null` (enrichment gap).
- Heartbeat-flatten "Wake the computer" Task Scheduler operator action.
- Disk cleanup + pagefile raise (operator action).

---

*End of handoff. Standing by for the fresh session to take over Phase 4. The outgoing orchestrator (this session) has done the heavy synthesis; you have the master backlog, ranked hypotheses, and Q1.4 spec ready to dispatch.*

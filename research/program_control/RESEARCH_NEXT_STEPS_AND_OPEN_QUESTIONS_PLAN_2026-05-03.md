# Research Next Steps And Open Questions Plan - 2026-05-03

Status: research/program-control plan only
Promotion posture: `NO_PROMOTION_VERDICT`
Context source moved to: `.context/03_analysis/RESEARCH_GOAL_FOLLOWUP_CONTEXT_2026-05-03.md`

## Executive Answer

Yes, there is still a lot to do. But it is not an unlimited unclear backlog anymore.

The weekend research queue has been reconciled: `192` total items, `0` unblocked ranked items, `0` promotion-allowed items, `60` done, `59` deferred with trigger, `40` blocked with reason, `20` rejected/failed, `10` filed for approval, `2` accepted candidate discoveries, and `1` stronger-than-baseline candidate.

That means the immediate question is no longer "what else can the agent randomly search?" It is now "which waiting gate do we clear next?"

The answer is:

1. Fix live account/PnL truth first, because the CEO screenshot proved local daily-PnL/R artifacts can diverge from MT5 account history.
2. Implement execution/lifecycle telemetry after explicit approval, because V2b, V3, and orderflow cannot become promotion-grade without fill/no-fill/expiry/order-failure truth.
3. Continue forward validation for V2b/V3 and NAS100 orderflow, because the best ideas are discovery-only until unseen resolved rows exist.
4. Use Sierra Package 12 now that it is available: capture active-session delayed depth, prove parser/parity, and keep Databento for targeted historical MBO/MBP windows.
5. Keep AI/ML/risk-policy changes behind explicit approval and shadow-only designs; Component 3B debate is parked and should not consume API budget now.

## What Is Already Live Or Already Shipped

These do not need a new research implementation to be "activated" unless the CEO chooses a new approval path:

| Item | Current state | Do we need implementation now? |
|---|---|---|
| J46-J49 | Already live, per CEO correction. | No new activation. Needs monitoring and account-truth reconciliation. |
| S79-style risk policy / current challenge risk posture | Already part of the live/research stack. | No immediate replacement. Continue MC/forward monitoring. |
| Side-aware sizing | Already reflected in current full-stack MC and live config state. | No immediate change unless CEO approves a risk-policy redesign. |
| Multi-framework entries (`ob_retest`, `fvg_fill`, `breaker_re_entry`) | Already live framework set. | No new activation from the weekend research. |
| Methodology gate | Implemented and audited; promotion-p-value allowed count remains `0`. | Use it for every future lift claim. |
| D-11 missing GBPJPY/US30_cash old-label supplement | Generated and versioned as research labels. | Integrate only with explicit `source_period` and `mechanical_vs_live_like` flags. |
| Sierra Package 12 + `.depth` parser proof | Package 12 is available and parser-readable weekend sample proven. | Needs active-session sample and parity before conclusions. |

## Important Correction To Keep In Mind

The live account is up by the MT5 screenshot, not down by local R artifacts:

| Account lens | Value |
|---|---:|
| Initial deposit | `$100,000.00` |
| Screenshot balance | `$101,223.36` |
| Net balance gain | `+$1,223.36` |
| Net balance percent | `+1.223%` |
| Visible gross trade-profit sum | `+$1,262.56` |

The small `0.01` trades are minimum-trading-day filler/safety rows and must not be used as normal system expectancy evidence.

This creates a new high-priority implementation item: MT5 account-history reconciliation must become the account-dollar source of truth, and local strategy-R artifacts must be kept separate until lifecycle/PnL logging is fixed.

## Where I Was Conservative

I was aggressive in research triage, but conservative in promotion and live wiring.

I held off on:

| Held item | Why held | Next action |
|---|---|---|
| V3 FVG-only rescue live wiring | Same-dataset exploratory replay only, despite `+0.270259R` mean delta vs J46 on affected rows. | Keep as stronger-than-baseline discovery; run forward/V2b/lifecycle validation first. |
| V2 best structural oracle | `+10.815R/month` conversion is an oracle upper bound, not implementable as-is. | Build as-of selector only after resolved prospective pairs exist. |
| Orderflow/NAS100 filter promotion | Actual broker-R coverage is `1 / 58` supported orderflow candidate rows. | Continue forward collection; do not promote a filter from synthetic/path labels. |
| Tool-use grounding into PrimaryAnalyzer | Would alter Component 3A behavior. | File shadow-only approval ticket before code wiring. |
| Component 3B debate activation | Would alter AI evaluation flow and token spend. | Owner decision 2026-05-03: leave dormant for now; no near-term API spend. |
| Reflexion/adaptive feedback | Would create live adaptation behavior. | Only shadow design after approval. |
| Prompt cascade rebuild | Prompt/trading-evaluation behavior change. | Requires explicit CEO approval. |
| Risk-model replacement | Would change live risk behavior. | Prototype only after approved simulation spec over DSR-surviving baselines. |
| Broad paid Databento/source pulls | Cost can escalate and many labels are not yet promotion-grade. | Use surgical event windows and parity checks only. |
| More K54 same-cohort architecture iteration | K54 v3/v4 global architecture failed current gates. | Reopen only with new shadow cohort/source-balanced cohort or n>=5000 labels. |

This was the right conservative boundary. The system can research aggressively, but live trading changes need stronger evidence and approval.

## Waiting Gates

### 1. Account And PnL Truth

| Item | Waiting for | Why it matters | Next step |
|---|---|---|---|
| MT5 account-history reconciliation | Read-only verifier against account history/deals. | Prevents stale local daily-PnL artifacts from becoming wrong CEO-facing numbers. | Build a verifier/report that separates `ACCOUNT_HISTORY_REALIZED`, local `LIVE_R_ARTIFACT`, and `RESEARCH_MEASURED`. |
| Daily PnL logger correction | Diagnosis of NAS100 false-close and XAUUSD 0.01-lot mismatch. | The current logger can disagree with account dollars. | Add checks that account-history PnL supersedes local path artifacts for dollar truth. |
| R-vs-dollar bridge | Per-symbol risk, lot, tick-value, side-aware, correlation, and profile override mapping. | Needed before any expectancy can be honestly shown in dollars. | Produce a conversion report instead of assuming `1R = 1%` or `2%` globally. |

### 2. Execution And Lifecycle Truth

| Item | Waiting for | Why it matters | Next step |
|---|---|---|---|
| P2-I pending-limit lifecycle telemetry | CEO/main-thread approval before touching `execution.py` or `orchestrator.py`. | V2b/V3/orderflow need no-trigger, expired, no-tick, wrong-side abort, SL-too-close, success, and failure states. | Implement fail-open JSONL logger and tests from `research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md`. |
| O1 index staleness | `_trade_index.json` is stale by `49` days: index `129` vs trade records `259`, index latest `2026-03-13`, records latest `2026-05-01`. | Some consumers may be reading old trade inventory. | Rebuild index or migrate consumers to current record scan with stale verifier. |
| O8 lifecycle completeness | `43` LIMIT_PLACED rows missing `execution` and `pending_lifecycle`. | These rows cannot support actual-R/fill/no-fill/V3 validation. | Implement lifecycle completeness verifier after P2-I logger is approved. |
| Close-side slippage / L-7 | Current lifecycle and slippage lanes are separate. | Needed to explain realized close quality after a broker position exists. | Keep separate from pending-intent logger; join later by `trade_id`/ticket. |

### 3. V2b / V3 Path Scaling

| Item | Waiting for | Current number | Next step |
|---|---|---:|---|
| V2b prospective validation | Resolved post-cutoff OB-boundary/J46 pairs. | `0` resolved prospective pairs. | Keep read-only forward replay/evaluator running until sample floors are reached. |
| V2 OB-boundary candidate | Forward rows and lifecycle truth. | Full-slice delta `+0.024061R/trade`; 2026 delta `+0.233839R/trade`. | Treat as cleanest V2b candidate, not promotion. |
| V2 FVG path candidate | Concentration/robustness and forward rows. | Full-slice delta `+0.033292R/trade`; 2026 delta `+0.365975R/trade`. | Continue side-by-side with OB-boundary but do not let headline size override robustness. |
| V2 structural oracle | As-of selector, not hindsight oracle. | 2026 delta `+0.636190R/trade`, `+10.815R/month` at old `17/mo` assumption. | Use only as size-of-prize; build no live logic from oracle result. |
| V3 FVG-only rescue | V2b/forward resolved rows, lifecycle telemetry, promotion dossier. | `+0.270259R/trade` vs J46 on affected same-dataset rows. | Keep as `STRONGER_THAN_BASELINE_CANDIDATE`; design shadow harness after telemetry. |

Frequency impact remains unproven. V2 mostly changes path quality on existing setups. V3 may create extra broker order events if close-and-reenter is implemented, but it should still be measured under the same setup risk budget until lifecycle data proves otherwise.

### 4. Orderflow / Sierra / Primitive Feeds

| Item | Waiting for | Current number | Next step |
|---|---|---:|---|
| NAS100 orderflow clue | More actual broker-R rows and stable leave-one-date result. | Actual broker-R coverage `1 / 58`; synthetic/path joined rows `22`; MBO outcome winner/loser `1 / 10`. | Continue forward full-depth research only; no live filter. |
| Sierra Package 12 boundary | Package 12 is available, but Sierra MBO is not full historical order-ID backfill. | MBO display is filtered to order quantity `>=3`; Sierra docs say no historical MBO record/download; depth retention is recent. | Use Package 12 for forward/recent depth and MBO workflow proof, not as unlimited historical MBO. |
| Sierra active-session sample | At least 30 minutes `NQM26-CME` active delayed depth with nonblank Market Depth Historical Graph. | Weekend parser proof: `697` records in sample, but market-closed constrained. | Capture active sample, rerun parser, align with Sierra intraday/`.scid`, then Databento parity. |
| Databento parity | Same UTC window as Sierra active sample. | Prior surgical/expanded pulls executed under caps; vendor final billing may differ. | Use only targeted parity/event windows. |
| LMAX/venue-native FX/metals | Affordable, legally usable source with API/history/storage rights. | LMAX Exchange ITCH is too expensive; LMAX Global provenance remains open. | Monitor only; do not prioritize current fee path. |

### 5. Data / External Source Blocks

These are not coding blockers; they need sources or access:

| Block | Needed source |
|---|---|
| D-2 pre-2024 tick history | Alternate broker/provider/archive or paid historical tick/LOB source. |
| D-12 pre-2022 all-symbol M15 coverage | Alternate broker/provider/archive. |
| D-4 FX COT | Official CFTC FX contract map plus cached FX COT rows. |
| D-5 KMW FX-fix | Confirmed KMW source/licensing path or legal proxy. |
| D-7 / U-8 H-K-M intermediary capital | Legal H-K-M/intermediary-capital source with publication metadata. |
| D-8 BIS | BIS tables/cache joined to FRED with publication-time metadata. |
| D-9 Fed research feed | Defined source, fields, cadence, publication-time model, parser/cache. |
| A-2 VIX1D/VIX9D | Confirmed legal/free source and no-leak caches. |
| A-3 / V-2 VRP | Implied-variance/vol term-structure source plus realized-vol estimator. |
| A-8 / U-12 real-gold feature | CPI/PCE deflator source and pre-registered construction. |
| X-1/X-2/X-3 imbalance/meta-order flow | Signed trade/aggressor-side or approved proxy feed. |

### 6. ML / K55 / Architecture

| Item | Waiting for | Why | Next step |
|---|---|---|---|
| S-1 K55 shadow design | CEO approval and target refresh after K54 v4 failure. | Existing design assumptions are stale. | Rewrite as shadow-only, no live decision impact, then ask approval. |
| S-3/S-4 K55 evaluation | K55 shadow rows and paired AI/K55/realized-R data. | No shadow output exists yet. | Implement only after S-1 approval; evaluate after >=30 days or n>=50 events. |
| K-16/K-17/P-10 feature refresh | n>=5000 labels or source-balanced expanded cohort. | Same-cohort K54 iteration is closed. | Wait for new cohort, not more current-cohort architecture tuning. |
| P-8 sticky HDP-HMM | Standalone harness and Kirby fat-tailed-mixture null test. | Literature-prior only right now. | Build research harness only if CEO wants regime-model track reopened. |

### 7. Approval-Gated AI And Risk Changes

The `10` filed-for-approval items are:

| Item | Approval reason | Practical next step |
|---|---|---|
| L-6 | Execution telemetry/cost observability filed. | Clarify exact logger scope before implementation. |
| O-6 | Operations/execution item filed. | Clarify whether it is operator/admin or repo-code work. |
| P2-I pending-limit telemetry | Touches `execution.py` / `orchestrator.py`. | Approve additive fail-open logger and test window. |
| S-1 K55 shadow design | Would add shadow architecture around live flow. | Refresh target and implement shadow-only if approved. |
| A-16 DCC/cDCC/Block-DECO | Would replace live correlation/risk behavior. | Research-only prototype first, live replacement later only if validated. |
| B-5 AI grounding bundle | Would alter Component 3A behavior; debate portion excluded while L-4 is parked. | Shadow-only design first. |
| X-7 cascade prompt rebuild | Would touch prompts/trading evaluation. | Approval required before prompt work. |
| L-1 tool-use grounding | Would wire `ai_tools` into PrimaryAnalyzer. | Shadow harness, no decision impact. |
| L-2 market-state/recent outcome tool inventory | Would add live-context tooling to AI. | Shadow inventory first. |
| L-3 Reflexion/adaptive loop | Would alter adaptation behavior. | Shadow-only design, no live learning. |

Parked/deferred item:

| Item | Park reason | Reopen trigger |
|---|---|---|
| L-4 Component 3B debate | Adds extra AI/API calls and is down-road work. | Reopen only by explicit CEO request with a shadow-only, budget-capped design. |

### 8. Operator/Admin Blocks

| Item | Waiting for |
|---|---|
| O-3 wake task | Operator must enable "Wake the computer to run this task" and verify next active kill-zone wake cycle. |
| O-5 disk/pagefile | Operator/admin disk cleanup and pagefile raise, then rerun ops checks. |

## Rejected Or Low-Value Routes For Now

These should not consume near-term effort unless new evidence changes the substrate:

| Route | Reason |
|---|---|
| K54 v3/v4 global architecture iteration | Failed current gates; K54 v3 DSR-p `0.320958`; K54 v4 all architectures failed. |
| Portfolio-wide vol scaling | H-PM01 delta mean R `-0.00496055`, DSR-p `0.999965`. |
| Broad vol-managed sizing policy | Rejected in Lane 6 tail triage. |
| V3 FVG-then-OB / OB-lock variants | Underperformed the cleaner FVG-only rescue path in the same-dataset replay. |
| Risk-policy replacements without simulation | Must be simulated over DSR-surviving baselines and approved before behavior changes. |
| Quantum tracks | No current GTOS bottleneck requires them. |

## Concrete Plan

### Phase 0 - Truth And Monitoring First

Goal: stop wrong live account numbers from recurring.

Deliverables:

1. Read-only MT5 account-history reconciliation report.
2. Daily PnL logger discrepancy audit: account history vs local R/path rows.
3. R-to-dollar conversion report with symbol profile, risk overrides, lot size, side-aware, correlation, and actual broker cost fields separated.

Exit gate:

- CEO-facing live PnL uses `ACCOUNT_HISTORY_REALIZED` first, never stale local R artifacts.

### Phase 1 - Execution Label Truth

Goal: unlock real fill/no-fill/expiry/order-failure labels.

Deliverables:

1. Approve P2-I additive fail-open pending-limit lifecycle telemetry.
2. Implement helper and tests before live hook.
3. Wire into `execution.py` and `orchestrator.py` only after approval.
4. Add O1 stale-index verifier/rebuild or consumer migration.
5. Add O8 lifecycle completeness verifier.

Exit gate:

- New LIMIT_PLACED rows carry lifecycle labels sufficient for V2b/V3/orderflow joins.

### Phase 2 - Forward Candidate Validation

Goal: decide whether V2b/V3 are real forward improvements.

Deliverables:

1. Continue V2b rolling evaluator until resolved prospective pairs exist.
2. Maintain OB-boundary and FVG path candidates side by side.
3. Build V3 FVG-only rescue shadow harness only after lifecycle telemetry is available.
4. No promotion until unseen rows clear methodology, concentration, lifecycle, cost, and DSR/PBO/effective-N gates.

Exit gate:

- Either promote to approval dossier, keep collecting, or reject. No same-dataset promotion.

### Phase 3 - Orderflow Awareness

Goal: improve market awareness without pretending sparse labels prove alpha.

Deliverables:

1. Capture Sierra Package 12 active-session `NQM26-CME` delayed depth.
2. Rerun Sierra parser and align to intraday price.
3. Run Databento parity on the same UTC window.
4. Keep NAS100 orderflow forward registry updated with actual broker-R labels only.

Exit gate:

- Stable broker-R-supported orderflow diagnostic, or rejection as synthetic-only clue.

### Phase 4 - Approval Decisions

Goal: decide which behavior-changing branches are worth implementing in shadow mode.

Decision set:

1. P2-I pending-limit telemetry: approve now if we want V2b/V3 to mature.
2. S-1 K55 shadow: approve only after target refresh.
3. L-1/L-2/B-5 grounding: approve shadow-only if we want AI market-awareness work.
4. L-4 Component 3B: leave dormant; no near-term API spend.
5. L-3 Reflexion: defer unless we are ready to govern adaptive learning.
6. A-16/risk replacements: research-only prototype first; no live replacement.

### Phase 5 - External Source Acquisition

Goal: choose which blocked source paths are worth time or money.

Priority shortlist:

1. VIX1D/VIX9D and VRP if legal/free or low-cost source is available.
2. BIS/H-K-M/intermediary-capital only if source terms are clear.
3. FX COT/KMW if official or reproducible proxy is obtainable.
4. Pre-2024 tick/LOB history only if it directly unlocks a pre-registered test.
5. LMAX only if LMAX Global provenance/API/storage rights are clarified and cost is realistic.

## Current Confidence By System Area

| Area | Confidence now | Reason |
|---|---|---|
| Live account state | Medium | Screenshot/account history is clear, but automated reconciliation is missing. |
| Existing J46-J49/S79 stack | Medium | DSR-backed research and positive live account, but live n is still small. |
| Core OB signal | Medium | Mechanism survives separately, but decay is real and headline overfit was removed. |
| V2/V3 improvements | Low/medium | Strong discovery signals, no forward promotion-grade validation yet. |
| Data/account labeling | Low/medium | Many useful logs exist, but lifecycle/PnL truth gaps are material. |
| Execution lifecycle | Low/medium | Pending-limit branches are known, but telemetry is not wired. |
| Orderflow awareness | Low | Tooling and clues exist; actual broker-R coverage is too sparse. |
| Risk policy current stack | Medium/high | S79/side-aware evidence is stronger than alternatives; replacements not ready. |
| ML/K55 expansion | Low/medium | NAS_US30/K55 shadow ideas exist, but current K54 global architecture failed. |
| Expansion potential | Medium | Many pathways exist, but most need forward data, source access, or approval. |

## Bottom Line

The weekend research did not leave a hidden promotion-ready strategy on the table. It did leave a better map.

The highest-value next work is not another broad ambiguity sweep. It is clearing the measurement gates that make the best discoveries promotable or rejectable:

1. account-history truth,
2. pending-limit lifecycle truth,
3. V2b/V3 forward resolved rows,
4. NAS100/orderflow broker-R labels,
5. approval decisions for AI/ML/risk behavior changes.

The system is stronger after the research because the queue is cleaner, the false/stale number risk is documented, and the best next gates are explicit. It is not yet stronger because V3/orderflow/K55 were promoted; they were not.

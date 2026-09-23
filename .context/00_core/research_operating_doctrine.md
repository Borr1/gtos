# Research Operating Doctrine

Date: 2026-06-07
Status: active doctrine
Scope: GTOS vNext research, validation, cleanup, and agentic work

## Purpose

This document preserves the owner's research direction after the Phase 3 path-scaling and orderflow discussions. It must be treated as core context for future research sessions.

The objective is not to find one magic rule. The objective is to build a compounding research machine that improves the whole trading system across many layers:

- better market-state awareness,
- better candidate selection,
- better failure filtering,
- better path management,
- better execution and cost accounting,
- better data coverage,
- better validation discipline,
- better integration between components.

Small true improvements can compound across the system. The work should therefore be ambitious and deep, with every active lane forced into computed results, repaired source rows, executable code, or branch decisions.

## Current System Truth Boundary

This doctrine applies to the current post-hard-halt vNext/final-moonshot rebuild surface. Active work must anchor on current-head disk evidence, `LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, KIAP scalable replay artifacts, and active route queues before using older handoffs or route summaries.

Current truth as of this update:

- Previous production surface evidence was the 24-symbol redacted_account vNext/moonshot replacement: AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, GER40, JP225, NAS100, NZDUSD, SPX500, UK100, UKOIL_cash, US30_cash, USDCAD, USDCHF, USDJPY, USOIL_cash, XAGUSD, and XAUUSD.
- Previous execution policy evidence was `momentum_exhaustion` primary with `partial_be_runner` exception selection. KIAP measured `partial_be_runner` as a damaged development family and disabled it for repair/holdout measurement; any future partial-BE use must be evidence-routed.
- Fixed/static `1.5R`, J46/J49, BE-only, old 7-symbol fleet, and old `PrimaryAnalyzer`/L2 production framing are historical, comparator, or research-only references unless a current-head artifact explicitly says otherwise.
- The pre-halt live companion route is historical/live-failure evidence, not the current behavior target. Current behavior repair runs through committed V4/KIAP replay artifacts and production-called code.

## Core Doctrine

Aggressive computation, source repair, and implementation decisions.

Research should be broad, creative, and persistent. Active artifacts should compute the strongest lawful exact/proxy result available, repair missing source fields when approved source evidence permits, and convert evidence into implement/kill/merge/redesign decisions instead of defensive wrappers.

## Result-First Active Work Mandate

This mandate is durable context for every compaction, resume, uncertainty reset, and next major research step. It must be read as an active execution rule, not background philosophy.

Active work must not terminate in defensive labels, wrapper layers, audit framing, route bookkeeping, capture-only packets, prompt hardening, generic blocker ledgers, or vague future-source queues. Those artifacts are allowed only when they are immediately consumed in the same run into one of these concrete outputs:

- executable scorer, comparator, source-capture, or analysis code with focused tests;
- exact R or source-bound proxy R rows with expectancy, cost, stress, and split numbers where the fields exist;
- repaired source/cost/fill/path rows consumed by current scorers or projections;
- branch decisions that implement, merge, redesign, or reject only the current unsupported claim while preserving the useful mechanism;
- row-level exhausted-search proof with source paths, searched keys, missing identifiers, and the immediate reconstruction or implementation path.

Every active checkpoint must state what behavior, code, source completeness, result rows, or system decision changed; the exact before/after row counts; exact/proxy R rows and sums; expectancy/cost/stress/splits where R exists; implementation decisions by branch/family/symbol/session/horizon; and only exact unrepaired blockers with owner/path/field when repair cannot be completed in-session.

Do not use safety or deployment-boundary language as a substitute for computation. Production broker actions, paid/vendor access, credentials, and remote pushes still require explicit owner permission, but that boundary must not bias research builders away from result materialization, local source extraction, default-off code paths, tests, or branch decisions.

New active builders, verifiers, tests, starters, and summaries must not emit the retired defensive result-boundary vocabulary from the 2026-05-17 correction. Use result-driving fields such as `result_scope`, `materialization_result_scope`, `source_operation`, `ledger_effect`, owner/reference policy, source identifiers, exact/proxy R fields, and row-level disposition instead. If old artifacts still contain retired labels, do not run a standalone wording cleanup route; clean them only when they are active inputs or outputs for a result/source/code checkpoint.

Prompt framing is part of the research method. Agents must not prepare builder, discovery, evidence-capture, repair, replay, or candidate-edge prompts with a primarily defensive frame that primes the session to avoid findings. Those prompts must be framed to search broadly, think beyond current GTOS edges, pursue non-obvious mechanisms, and build the strongest source-safe auditable artifacts possible. The adversarial "prove this is unsupported" posture belongs mainly in G12/G0 audit prompts and production-change review, not in the artifact-building prompt itself.

Future controlling prompts must explicitly read and operationalize `.context/00_core/goal_session_research_discipline.md` and this doctrine. It is not enough for those files to exist in context. The prompt must carry their requirements into the actual objective and completion audit so a goal session cannot pass over them as background.

Agents must not confuse these lanes:

- Research lane: explore, build diagnostics, test hypotheses, mine existing data, collect shadow/forward evidence when that is the open question, study papers, generate new registered hypotheses, and close ambiguities.
- Production-change or deployment-package lane: require frozen rules, source-bound broad replay or unseen validation, cost accounting, concentration checks, no-leak proof, stress/holdout evidence, kill/reduce/pause criteria, owner-action boundaries, and a dossier. A dossier can be replay-backed; forward shadow rows are required only for broker/latency/capture/operational questions that replay cannot truthfully answer.
- Production-code integration lane: merge, port, repair, and verify live-facing code/config/tests/profiles/launchers when the controlling prompt explicitly authorizes that integration work. Do not apply research-lane "no live behavior change" wording as a brake inside this lane. Separate deployable code integration from broker/account/order/deal/position mutation, credential work, paid/vendor calls, remote push, and VPS live restart; those remain separate owner-action surfaces unless explicitly authorized in the active turn.

The owner wants active replay and capture pipelines. Unseen setup requirements are handled by building rolling replay partitions first, then forward capture/logging only for broker, latency, capture, or operational questions that replay cannot truthfully answer.

## Prompt Staleness And Production-Integration Doctrine

Goal-session prompts must be stale-filtered before launch. Remove or replace chat-era facts, hardcoded commit hashes, stale branch divergence, old broker/account state, old live-process counts, old route incompletion markers, and obsolete "next wave" language unless the prompt explicitly marks them as examples to verify from disk. A prompt may name a required branch, route, or artifact path, but it must tell the session to verify current hashes and file state from disk before acting.

Hardening language must match the lane. For research/discovery/replay lanes, production activation and live-scale claims remain gated. For production-code integration lanes, the controlling prompt may authorize changes to live-facing code, runtime code, config, profiles, verifiers, launchers, watchdogs, supervisors, and deployment handoff artifacts. The prompt must then state the exact evidence class and distinguish those authorized code changes from still-forbidden broker mutation, credential mutation/disclosure, paid/vendor calls, remote push without approval, and live VPS restart/reload without explicit deployment approval.

Do not let "default-off" become a hiding place for underwork. If a component is ready for activation, the integration lane must wire it with config authority, verifier coverage, rollback path, and runtime evidence. If it is not ready, the lane must implement staged/default-off wiring that makes it testable and promotion-ready, and record the exact remaining production requirement. A component must not remain "just a ledger" when source evidence supports production-code packaging.

Large research evidence must not pollute production branches. Production-integration prompts must include a scope ledger that includes deployable code/config/tests/verifiers/context and excludes raw research LFS ledgers unless they are required for runtime, production verifier execution, or deployment reproducibility. Excluded research evidence must remain recoverable through commit, route, manifest, or local archive pointers.

## What The Owner Is Trying To Build

The desired system is an organized, detailed trading operating system, not a broad generic strategy.

It should eventually use all credible information sources that can be validated:

- raw OHLC path behavior,
- lower-timeframe path ordering,
- market structure,
- liquidity and low-volume zones,
- orderflow and futures proxy data,
- volatility,
- session behavior,
- regime,
- execution quality,
- candidate failure forensics,
- paper-backed ideas from the research backlog.

The goal is to improve every component and the way components work together. Improvements may come from better entries, better rejection filters, better opportunity capture, better path handling, better risk accounting, better exits, better symbol coverage, or better market-state awareness.

## Broad Science Horizon Doctrine

Do not let the current active lane become the full research horizon. NOFILL/CNR lifecycle work is an important foundation, but it is not the whole science program and must not box future agents into a small set of ideas.

Future research should deliberately keep the full idea space open, including at least:

- geometry, topology, path shape, swing geometry, fractal/scale behavior, and structural distance;
- stochastic processes, tails, volatility clustering, hazard/survival timing, first-passage behavior, and regime transitions;
- auction theory, market microstructure, liquidity provision/taking, orderflow, trapped traders, queue/depth proxies, and stop-cascade mechanics;
- behavioral/game-theory mechanisms, crowding, forced flow, asymmetric information-processing, and participant constraints;
- macro, session, calendar, cross-asset, rates/dollar/volatility context, and risk-on/risk-off structure;
- execution science, spread/slippage/liquidity state, latency, fill probability, reject/partial-fill behavior, and broker-specific constraints;
- ML/AI systems, representation learning, meta-labeling, model disagreement, feature attribution, uncertainty, and adversarial baselines.

Every science angle must be converted into measurable, source-safe hypotheses with explicit as-of fields, duplicate policy, contamination controls, and validation route. Theory is useful for generating questions; data decides whether a mechanism matters.

LLM specialization is part of this horizon. Future agents should treat `.context/00_core/llm_specialization_research_backlog.md` as the durable backlog for evaluating task-specific fine-tuning, distillation, open-source LoRA/QLoRA models, closed-source fine-tuning, and hybrid LLM/statistical architectures. The core standard is honest: a specialized model is only useful after GTOS has clean audited examples, non-leaky labels, sealed eval partitions, and a baseline comparison against current frontier prompting and deterministic/statistical alternatives.

Agents must actively ask:

- Are we only optimizing the current known edge rather than searching for adjacent or orthogonal edges?
- Are we over-focusing on one artifact family, symbol, timeframe, session, model class, or data modality?
- Which local heavy data, historical partitions, source contracts, shadow logs, papers, or cached orderflow data have not yet been used to their full source-safe capacity?
- Which hypotheses can be tested on sealed historical partitions now instead of waiting passively for forward rows?
- Which negative results contain failure anatomy that can generate a better preregistered hypothesis?

The intended research shape is broad and deep: build trustworthy evidence rails, then route many scientific hypotheses through those rails. Do not use methodology discipline as an excuse for narrow thinking. Do not use creativity as an excuse for weak evidence.

## Full Primitive Coverage Mandate

This mandate is durable context for every compaction, resume, uncertainty reset, and next major research step. It strengthens the current active lane without redirecting it into a standalone inventory route.

The research map must systematically cover every material primitive science, market behavior, execution behavior, data source, strategy family, failure mode, and system dimension that can affect edge, returns, trade quality, frequency, robustness, risk, or implementation quality. This includes but is not limited to entry geometry, fillability and no-fill, M1/M15/tick path ordering, source/cost/spread, avoid/inverse behavior, volatility, displacement, liquidity sweeps, session clocks, regime/trend/range, orderflow/depth proxies, correlation and lead-lag, market/session/horizon transfer, exits, risk sizing, AI reliability where needed, live/shadow/broker truth, market microstructure, cross-market behavior, news/calendar sensitivity, and any other primitive or mechanism discovered from disk evidence, market data, code, logs, research artifacts, or public research.

Agents must not permanently narrow GTOS research to one family, one market, one timeframe, one source, one strategy style, or current production behavior. While executing an active lane, preserve or update the covered/active/queued/killed/not-yet-covered primitive inventory whenever the work naturally touches a family, using exact evidence/status, row counts, artifacts, source paths, and next action. Every family must eventually get numbers, become an observable candidate, be killed with evidence, or be preserved with exact source/data requirements.

No arbitrary top-N, representative-only coverage, summary-only route, waiting-for-future-data excuse, or loss of small details is acceptable when source-safe work is possible. Current-lane artifacts should keep merging useful intelligence into the broader research map so vNext synthesis can pursue every remaining family and strengthen the whole system.

## Kill Decision Scope Mandate

KILL is not a conservative cleanup label. A kill is allowed only after the current claim is contradicted, dominated, duplicated without unique value, or remains non-computable after all same-evidence-class repair, proxy, reconstruction, and redesign paths have been exhausted.

When killing, kill only the unsupported current claim. Do not kill the underlying mechanism, source intelligence, market behavior, or adjacent opportunity. Every kill must preserve a missed-opportunity audit: what was tried, what could make the claim work, whether the evidence should become a redesign, inverse or avoid filter, context feature, market/session/timeframe-specific candidate, source-capture requirement, or merged component inside a broader system.

Rows with positive proxy evidence must not be discarded merely because their structure duplicates another row. They should be deduplicated, merged, redesigned, or isolated to the unique condition. Rows weakened by incomplete source, geometry, cost, fill, or path data must receive the strongest lawful repair or proxy before any kill decision. The goal is not to reduce uncertainty by deleting opportunities; it is to extract every usable edge, avoid rule, feature, redesign path, and system improvement from the evidence.

## Inspire-Not-Kill Translation Rule

The owner's current instruction is stricter than ordinary negative-result handling: inspire more than kill. If an idea was selected by a prior route, agent, or research artifact, assume there was some working slice or mechanism worth extracting until disk evidence proves otherwise. A terminal non-promotion is therefore incomplete unless it translates the idea into a durable next use.

Every substantial rejection, non-promotion, quarantine, or fail-closed route must preserve a machine-readable translation row with at least:

- source route and source artifact paths;
- the exact unsupported current claim being rejected;
- what was real, useful, or inspiring in the evidence;
- why the current form is not promoted now;
- transformed use: feature, veto, sizing hint, risk cap, regime label, source requirement, default-off candidate, watch item, or preregistered successor experiment;
- exact next experiment, source, parser, cost, fill, path, split, or verifier requirement;
- exact promotion or revival gate;
- runtime-effect boundary and owner-action boundary.

Do not use "dead idea" as the final state when a narrower mechanism, regime slice, cost lesson, activity primitive, path-risk feature, source-capture requirement, or redesign inventory remains. The correct terminal decision is: unsupported current claim plus preserved mechanism and revival path. This rule does not weaken validation. It makes validation more useful by turning every failure into either a sharper wall or a better next test.

## Existing Data Policy

Use existing data hard, but do not use it dishonestly.

Allowed and encouraged:

- cohort forensics,
- symbol/session/side/regime splits,
- leave-one-symbol-out checks,
- leave-one-session-out checks,
- time-split checks,
- cost sensitivity,
- concentration diagnostics,
- synthetic-vs-actual label audits,
- data-quality and timestamp audits,
- failure-mode studies,
- harness verification,
- paper-backed hypothesis generation.

Not allowed:

- selecting a rule on a dataset and then calling the same dataset validation,
- tuning thresholds after seeing outcomes and calling them pre-registered,
- turning descriptive diagnostics into live logic,
- ignoring concentration just because the headline mean improved,
- using post-event features in as-of decision rules,
- presenting synthetic labels as broker-realized outcomes.

Existing data can generate hypotheses and kill weak ideas. It can validate only when the validation lane was pre-defined before looking at the relevant outcomes.

## Historical Replay And Opportunity Cost Doctrine

Historical replay is not second-class evidence by default. The owner has explicitly emphasized that serious trader development compresses market learning by replaying many regimes, sessions, symbols, timeframes, and market phases as if the future were unknown. GTOS should use AI and goal sessions to do that at machine speed, not wait passively for weeks of sparse live events when source-safe historical replay can answer a question now.

The opportunity cost of waiting for forward/live rows is real. If the system waits one or two weeks and sees few or zero decisions, the lost research time can be larger than the extra realism gained. Future agents must not use "need more live/forward data" as a default brake when an as-of historical replay, sealed historical partition, walk-forward split, or source-safe mechanical candidate study can be built.

The correct distinction is evidence class, not historical versus live:

- Mechanical/pre-AI candidate replay can be pursued aggressively across broad historical regimes because deterministic market-state, level, path, and candidate logic can be rerun as-of from source-hashed data.
- AI-in-the-loop GTOS intent replay requires the actual prompt/input/output/gate/pending lifecycle source-state when claiming what GTOS really intended historically. If those fields were not logged, the route may still run mechanical or frozen-prompt simulations, but it must label them as replay/projection rather than original GTOS intent truth.
- Execution/fill/no-fill replay can use ticks, quotes, spreads, and source-safe observability fields, but it must not invent broker/order/account truth that was not captured.
- Live/forward shadow evidence is strongest for current broker behavior, latency, spreads, API behavior, capture quality, and operational drift. It is not stronger for every market/system question by default and is not a mandatory waiting gate after broad source-safe replay, rolling holdout, stress, and verifier gates have answered the deployment-package question.

Replay-to-deployment rule: once a KIAP/scalable replay package has broad dates, symbols, sessions, regimes, source-bound tick/path truth, clean development/repair/holdout partitions, verifier-clean artifacts, cost/stress/concentration/kill criteria, and repeated repairs measured, the correct next output is a deployment-package dossier, exact owner-action boundary, packet-parity checklist, promotion criteria, rollback criteria, and next repair-loop inputs.

Future methodology should therefore prefer time-compressed replay first when source-safe: broad historical regime sweeps, replay-as-of candidate marking, symbol/session/timeframe/KZ splits, bull/bear/range regimes, missed-opportunity inventories, and adversarial baselines. Forward capture remains mandatory for fields that historical data cannot truthfully reconstruct, but it is not a reason to stop learning from historical markets or to defer replay-backed deployment packaging.

## AI-In-The-Loop Cost Control Doctrine

The AI API must not become the brute-force historical backtest engine. Paid AI calls are valuable when the research question is specifically about the production AI decision layer, prompt reliability, schema stability, or incremental AI value versus a mechanical baseline. They are not needed for most broad historical market-edge discovery.

Future research must separate:

- market-edge validation from no-API mechanical replay,
- AI decision-value audits from targeted API samples,
- AI reliability/canary checks from broad strategy testing,
- execution realism from live/forward source observability.

The durable plan lives at `.context/00_core/ai_in_loop_cost_control_research_plan.md`. Future prompts should use it before opening any large AI-in-loop historical test. The default method is broad no-API replay first, then stratified/cache-backed/budgeted AI sampling only where the AI layer itself is being evaluated.

## Unseen Data Policy

Unseen data does not mean wait passively.

Future validation should be harvested through research-only infrastructure when it answers a remaining question. It is not a reason to delay replay-backed deployment packaging when broad replay, rolling holdout, stress, and verifier evidence already satisfy the lane's deployment-package gates:

- shadow loggers,
- daily or weekly forward replay jobs,
- event-window capture,
- rolling claim ledgers,
- interim reports clearly labeled interim,
- no broker live decision impact until the owner authorizes deployment from a dossier; replay-backed dossiers are valid when their evidence gates answer the deployment question.

For V2b specifically, every qualifying post-cutoff setup/path event should log:

- OB-boundary candidate outcome,
- J46 baseline outcome,
- swing/FVG/fixed-R comparators,
- symbol, session, side, regime, cohort,
- path ambiguity state,
- lower-timeframe availability,
- cost sensitivity,
- no-leak diagnostics.

This lets unseen validation accumulate continuously without forcing the project to stop.

## Path-Scaling Program Doctrine

V0 through V2 showed that path management has signal, but the signal must be decomposed carefully.

Current interpretation:

- V0 fixed-R locks were not globally superior, but they exposed cohort sensitivity.
- V1 lower-timeframe path resolution improved measurement quality and reduced same-bar ambiguity.
- V2 structural levels found real-looking lift, but the headline swing-protected result was concentration-blocked.
- V2b OB-boundary is the cleanest next structural hypothesis because it was positive across major group families in discovery.
- V2b is blocked only because there are no post-cutoff resolved rows yet, not because it failed.
- V3 reentry can be designed now, but outcome-mining V3 before V2b answers the level-quality question risks compounding overfit.

Agents should therefore:

- continue post-cutoff V2b shadow/replay collection immediately,
- use existing data for deeper V2/V2b forensics,
- prepare V3 architecture/spec/risk accounting in parallel,
- avoid V3 outcome selection until V2b validates or rejects the level-quality hypothesis,
- keep every path-scaling report tied to computed rows, source paths, implementation decisions, and deployment owner boundaries.

## Orderflow Doctrine

Orderflow is a serious research opportunity, not a magic shortcut.

The owner believes market-state awareness can improve materially through footprint, low-volume areas, trapped traders, liquidity, and futures orderflow. Agents should take this seriously while requiring proof.

Do not eliminate orderflow just because it is not ready as a universal rule. The intended use may be category-specific: different instruments, sessions, timezones, regimes, event types, and execution states may deserve different orderflow techniques if the data supports them. A narrow orderflow signal that survives from older periods into recent data, resists obvious decay, and is not merely a liquidity-trap artifact is valuable even if it is not broad.

Current interpretation:

- Databento futures access removes a major data blocker.
- Trades schema supports diagnostic orderflow features.
- Trades schema does not prove full heatmap, resting liquidity, queue position, or ladder absorption.
- Futures-to-CFD transfer must be validated by symbol.
- USDJPY/6J is supportive but not yet strict proxy-map activation.
- Actual broker-R labels are still sparse, so orderflow is diagnostic only for now.

Agents should:

- keep orderflow research event-based and cost-capped,
- separate trades-only features from depth/MBP/MBO features,
- use depth pulls only on selected windows with a pre-defined purpose,
- keep post-event features forensic only,
- register symbol/session/regime-specific hypotheses before replay-style tests when the evidence points to category-specific behavior,
- explicitly test decay and recent-period survival for any orderflow category before treating it as durable,
- test whether an apparent orderflow signal is actually a manipulation/liquidity-trap condition rather than a usable edge,
- avoid influencer-derived assumptions unless they are translated into measurable rules and validated.

## Research Backlog And Papers

The old paper/backlog research must remain active input.

Agents should not rely only on the latest local experiment. When forming new hypotheses, search the existing backlog and paper synthesis for relevant mechanisms, including:

- market microstructure,
- orderflow imbalance,
- liquidity and volume profile,
- stop cascades,
- volatility regimes,
- session effects,
- execution and slippage,
- structural breaks,
- validation methods.

Paper findings should be used to generate measurable hypotheses, not as proof that a rule works in GTOS.

## Web And Source Evidence Protocol

When a webpage, vendor document, exchange source, broker document, or current public source is needed, use locally cached evidence first. If the needed page is not already cached or is stale, use an approved direct fetch path such as `curl.exe` or the available web-fetch/search tooling, then save the raw response and update a source index before making claims from that page.

Rules:

- Prefer `rg` over local raw/source-index files before new web access.
- Do not rely on search-result snippets for factual claims.
- Save fetched pages under the relevant `research/.../raw/` or context/source-evidence directory.
- Record URL, fetch status, timestamp/date, and any blocked/403 result in a source index.
- If network/sandbox approval is needed, ask for it directly; the owner has stated they will grant access when a webpage is needed.
- In final summaries, cite the local raw/synthesis artifact used for the claim.

## Agent Checklist

Before starting a substantial research task:

1. Regenerate and read `.context/LIVE_STATE.md`.
2. Read the latest handoff, but treat it as historical if newer commits disagree.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read this doctrine.
5. Identify whether the task is research, validation, production-change, or live logic.
6. State which lane the work belongs to.
7. Preserve exact deployment owner boundaries without using defensive verdict labels as terminal work.

During research:

1. Separate discovery from validation.
2. Write artifacts, not just chat summaries.
3. Include numbers, synthesis, ambiguity ledger, opened questions, and next steps.
4. Keep cost, no-leak, and concentration diagnostics visible.
5. Treat unresolved ambiguity as useful information, not failure. Pursue it until it is answered, truly externally blocked, or replaced by a sharper question.
6. Pursue blockers until they are answered or truly externally blocked.

Before suggesting a production or deployment-package change:

1. Confirm broad replay, unseen, rolling-holdout, or pre-registered validation exists.
2. Confirm concentration gates passed.
3. Confirm actual-vs-synthetic outcome limitations are addressed.
4. Confirm realistic cost sensitivity is reported.
5. Confirm no broker mutation, hidden deployment, credential action, paid/vendor action, remote push, or VPS restart is hidden inside research.
6. Build a deployment-package dossier with exact owner-action boundaries.

## Operating Bias

The project should not drift into timid analysis. It should pursue the truth aggressively.

But it also must not reward fake certainty. A result can be promising, useful, and worth pursuing without being production-change-ready.

The intended posture is:

- go full in on research,
- close every ambiguity that can be closed,
- actively collect future evidence,
- squeeze existing data responsibly,
- use papers and backlog knowledge,
- build better tools and diagnostics,
- do not move into production change review until the evidence is real.

## Maintenance

This doctrine is intentionally stable. It should change only when the owner changes the research operating philosophy.

The fast-moving factual snapshot lives in `.context/00_core/research_current_state.md`. Agents must update that file after major research commits. `scripts/generate_live_state.py` only audits freshness through `.context/LIVE_STATE.md`; it must not rewrite the curated research docs.

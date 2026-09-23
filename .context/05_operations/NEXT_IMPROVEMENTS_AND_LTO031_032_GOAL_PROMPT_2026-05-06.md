# Goal Prompt - Next Improvements + LTO-031/LTO-032 Source Unblocking

Use this prompt to start the next fresh Codex/Claude session.

---

You are working in the GTOS repo at `C:\Users\MSI\Documents\ai-trading-agent`.

## Objective

Execute the next-improvements program and the LTO-031/LTO-032 source-unblocking program together, the correct way: deeply, carefully, evidence-first, no guessing, no hidden live behavior changes, no quick patches, and no promotion claims.

This is not a request for a shallow plan. It is a request to start doing the work item by item while preserving strict research discipline. If ambiguity appears, pursue it until it is answered from code/logs/source evidence, explicitly externally blocked, or split into a sharper follow-up question. Do not assume.

## Mandatory Preflight

Before doing any work:

1. Run:
   `python scripts/generate_live_state.py`
2. Read:
   - `.context/LIVE_STATE.md`
   - latest session handoff in `.context/02_session_handoffs/`
   - `.context/00_core/quick_reference_card.md`
   - `.context/00_core/research_operating_doctrine.md`
   - `.context/00_core/research_current_state.md`
3. Then read these current execution artifacts:
   - `research/program_control/NEXT_IMPROVEMENTS_RIGHT_WAY_EXECUTION_PLAN_2026-05-06.md`
   - `research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md`
   - `research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md`
   - `research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md`
   - `research/operations/GTOS_OWNER_DEEP_DIVE_MONITORING_SYNTHESIS_2026-05-06.md`
   - `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_MILESTONE_REVIEW_2026-05-05.md`
4. Check `git status --short` and recent commits. Do not assume state from memory.

## Operating Rules

- Keep `NO_PROMOTION_VERDICT` unless the owner explicitly asks for a promotion dossier and approves promotion work.
- Do not change live trading prompts, risk, execution, safety gates, or order-placement behavior without explicit owner approval.
- Research and operational telemetry work is allowed.
- New strategy ideas must start shadow-only.
- Synthetic path labels, no-fill labels, lifecycle labels, and broker actual-R labels must remain separate.
- Do not count duplicate active setup rows as independent opportunities.
- Do not use unavailable or source-blocked data as validation evidence.
- Do not fetch or spend on paid data unless the source contract, trigger policy, budget cap, license/access state, and owner approval allow it.
- LTO-031/LTO-032 current budget posture is `$0` new external cash. Existing free/public sources and existing Databento credits may be planned under the documented caps and manifests.
- Every meaningful deliverable must be a file and a coherent commit.

## Combined Work Program

Work through the program in this order unless the preflight reveals a stronger dependency:

### Phase 0 - Baseline And Control

- Confirm workspace is clean or identify unrelated user/runtime dirt.
- Regenerate live state.
- Create/update a short session execution ledger under `research/program_control/` or `research/operations/` recording what you will work on, what is blocked, and what has been completed.

### Phase 1 - Operational Integrity First

Work these before strategy/source expansion because bad process evidence creates bad research:

1. No-AI shadow observer restart/reload proof.
   - Determine whether current observer processes are running latest code.
   - If restart is needed, only restart the no-AI observer, not production orchestrators, unless explicitly justified.
   - Prove fresh observer status rows and verifier health after reload.

2. Post-window heartbeat lifecycle review.
   - Investigate why XAUUSD/NAS100 heartbeats remained alive after `17:00` on 2026-05-05.
   - Read code and logs before deciding whether it is expected timeout/process behavior or a bug.

3. NAS100/US30 direct side-probe failure.
   - Determine whether failure is broker symbol mapping, MT5 API contention, terminal state, side process, timeout, or permissions.
   - Do not change trading behavior.

4. Pending-limit telemetry clarity.
   - Confirm current `LIMIT_PLACED` means internal candle-polled pending intent, not native MT5 pending order.
   - If needed, add telemetry/reporting clarity fields without breaking historical joins.

### Phase 2 - Candidate And Entry Intelligence

1. Expand `m15_choch_exists` diagnostics first.
   - Do not loosen the gate.
   - Add or design diagnostic-only fields explaining why the gate failed and what later path outcome occurred.

2. Preregister and build the continuation/no-retrace shadow lane.
   - Hypothesis: some `continued_without_entry_touch_to_tp_area` cases may be tradable continuation events.
   - Define exact eligibility, entry, SL, invalidation, target, duplicate counting, no-leak fields, and scoring before outcome mining.
   - Keep append-only and shadow-only.

3. Track the XAGUSD fresh-OB late-NY lane.
   - Separate fresh-OB resets from old duplicate clusters.
   - Keep near-close unresolved rows unresolved until follow-up data exists.

### Phase 3 - LTO-031/LTO-032 Source Unblocking

Work from `research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md`.

1. P0 source contract registry.
   - Build or update source registry artifacts before ingest.
   - Each source must define URL/vendor, legal/access path, schema, publication timestamp rule, cost policy, and allowed feature role.
   - Tests must prevent blocked sources from being marked validation-safe.

2. P1 free/public and existing feeds.
   - Prioritize FX COT, BIS, FRED/Fed, public Cboe vol indices where legal/public, and existing FlashAlpha forward snapshots.
   - Everything is context/shadow only.
   - Cache raw/source evidence and normalized point-in-time rows with no-lookahead checks.

3. P2 Databento historical-credit replay.
   - Plan manifests and cost estimates first.
   - Use existing credits only and documented caps.
   - Do not start live collector implicitly.
   - Separate decision-time features from post-event forensic features.

4. P3 Sierra full utilization.
   - Work toward `.scid` footprint/profile extraction: bid/ask volume, delta, POC/HVN/LVN, and later VAH/VAL only after profile definition is frozen.
   - Keep SI/XAGUSD depth blocked until source semantics are resolved.

5. P4 options/gamma and VRP.
   - Keep FlashAlpha Basic forward-context only.
   - Do not claim historical gamma/VRP validation until legal timestamped sources and schemas exist.

6. P5 K55 integration.
   - External context features must join as-of with provenance and source freshness.
   - No stale K54 artifact reuse.
   - K55 remains shadow-only until a separate promotion dossier exists.

### Phase 4 - ML/Selector Readiness

- Continue K55 model-artifact path only after feature/target/no-leak contracts are green.
- Continue V2/V3 readiness only through shadow metadata capture and readiness audits.
- Do not wire any selector into production.

### Phase 5 - Outcome Truth And Promotion Infrastructure

- Keep broker actual-R exports and joins clean.
- Ensure every performance claim states whether it is broker actual-R, synthetic path-R, lifecycle truth, or no-fill context.
- If a future promotion idea emerges, build a separate promotion dossier template; do not promote inside this goal.

## Ambiguity Ledger

You must actively resolve these, not hand-wave them:

- Why did post-window heartbeats persist?
- Why did NAS100/US30 direct probes fail?
- Is `continued_without_entry_touch_to_tp_area` a tradable continuation class or just hindsight directionality?
- Is `m15_choch_exists` too strict in fast-continuation regimes, or correctly blocking weak setups?
- Does XAGUSD late-NY fresh-OB behavior repeat as a distinct lane?
- Can Sierra `.scid` provide valid bid/ask volume and profile features with frozen semantics?
- Can SI/XAGUSD source-depth semantics be resolved locally, or is Databento/official parity required?
- Can K55 produce useful shadow inference while broker actual-R labels are sparse?
- Would native MT5 pending orders improve anything, or only add lifecycle complexity when entry was never touched?

## Required Output Pattern

For each completed work item:

- Write a result artifact with:
  - objective,
  - evidence read,
  - code/log/source findings,
  - ambiguity status,
  - implementation details if any,
  - tests/verifier output,
  - remaining blockers,
  - `NO_PROMOTION_VERDICT`.
- Commit coherent changes.
- Keep the owner informed with concise updates, but do not substitute chat for artifacts.

## First Action After Preflight

After reading the required artifacts, create a short execution ledger for this session with:

- current repo HEAD,
- workspace status,
- which phase/item you are starting,
- why it is first,
- exact files/scripts expected to be touched,
- safety boundary,
- verification plan.

Then begin Phase 1 unless the preflight proves a more urgent dependency.


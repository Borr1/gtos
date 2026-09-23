# B7.4 Proof Serialization Scalability Pre-Replay Brief

Generated UTC: 2026-07-13T22:04:30Z.

## Decision

Do not start the B7.4 broad replay yet. First close one behavior-neutral proof-
serialization batch so the unchanged current-truth path can complete the
2026-06-01..19 window without duplicating multi-gigabyte authority payloads.
This batch changes only serialized ledger projections and their consumers. It
must not change candidate generation, selector admission, scheduler ranking,
risk sizing, order/fillability, lifecycle, exits, trades, or R.

Broker mutation, live authority, and final selection remain false. Local replay
and all 82 package sleeves retain full authority.

## Current Disk And Process State

- HEAD: `46261cecd` (`certify V250 independent-regime truth`).
- Branch: `hot-local/v235r3-migration-20260712`.
- No broad replay, parity builder, route builder, verifier, pytest, compile, or
  git maintenance process is active.
- The old archived-worktree Context OS stdio sidecar is read-only and is not an
  active replay or build process.
- Storage cleanup is complete: the current route working copy is `840920 KiB`,
  filesystem availability is `29652748 KiB`, and `.git/lfs/incomplete` is
  empty. Committed/LFS V250 evidence was not deleted.
- Working tree totals before this control update are 649 tracked modifications
  and 183 untracked paths. The 649 tracked rows are pre-existing runtime/data
  dirt (`data`, `knowledge_base`, `shadow_logs`, `AGENTS.md`, generated
  `LIVE_STATE`) and must not be staged or reverted. Historical untracked route
  outputs are also preserved and excluded.
- Task-owned control dirt before code edits is only
  `B7_4_PRE_REPLAY_STORAGE_RETENTION_MANIFEST_20260713T214019Z.json` plus this
  brief/root-map/cursor/matrix update.

## Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V250_B7_3_NON_HOSTILE_5D_UNCHANGED_V249_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`

Scope: all configured 24 symbols, 2026-06-01..05, unchanged V249 behavior,
repaired profile only.

- source / decision / candidate / scorecard / order-event / terminal-order /
  physical-trade / ordered-tick-headline / missed:
  `310 / 11520 / 35191 / 480 / 30 / 14 / 13 / 4 / 35177`
- physical W/L/F and gross/final/net:
  `8/5/0`, `+7.82542991/+7.82542991/+7.03578717R`
- physical cash / risk cash / risk pct: `-$68.02401535 / $2099.68670084 / 2.10%`
- headline W/L/F and gross/final/net:
  `3/1/0`, `+1.92353135/+1.92353135/+1.59506223R`
- headline cash / risk cash / risk pct: `-$67.96685163 / $1199.80760351 / 1.20%`
- full/reduced physical fills: `2/11`; headline: `2/2`
- cost REFUSED/source-gap executions: `0/0`
- headline stress at +0.05/+0.10/+0.20R per trade:
  `+1.39506223/+1.19506223/+0.79506223R`
- Monte Carlo worst drawdown: `-1.12773511R`
- package/candidate-generated/scorecard-or-order/order/filled axes:
  `1101/894/319/14/12`
- exact-window executable-gated source-bound denominator:
  `356027.9026815028R`.

This is bounded B7.3 evidence, not a full-reservoir claim.

## Baseline Comparison Discipline

- V89D, V90, and V92 are hostile 2026-05-13..17 comparators only:
  `56/+34.84520454R`, `51/+28.84201157R`, and `51/+29.35570236R`.
  They are not B7.4 denominators.
- V249 is the current hostile proof: 18 headline trades, `10/8/0`,
  `+0.28044419R`, `+$113.42435391`.
- V250 is the newest completed current-truth run and the exact nested first
  five days of the planned B7.4 window.
- V110B and V111 are the 2026-06-01..19 historical same-window comparators:
  approximately `95/+22.80R` and `45/-4.19R`. Their weaker fill/proxy truth is
  comparison evidence, not authority to bypass current cost, source, session,
  fillability, lifecycle, or ordered-tick requirements.

## Reconciled Prior Findings

- All V250 truth findings are INCORPORATED in commit `46261cecd`.
- No active or unreconciled subagent return exists.
- The candidate-index omission path is an existing intentional long-window
  mode, but its top-level `candidate_rows` accounting and physical-parity count
  do not yet represent the exact order/trade/missed relational union: VALID_OPEN.
- Direct V250 LFS inspection proves all 11,520 decision rows duplicate the exact
  `current_fvg_poi_generation` partition under
  `candidate_generation_audit.producer_generation_audit`: VALID_OPEN.
- Direct V250 LFS inspection proves all 480 scorecards serialize identical
  canonical/pre-finalizer/post-finalizer scheduler option traces: VALID_OPEN.
- V250 scorecard direct consumers already accept `scheduler_option_trace` as
  canonical; bridge status-join consumers require an explicit canonical
  fallback: VALID_OPEN.

## Root-Cause Chain

| Stage | State | Current evidence |
| --- | --- | --- |
| source-bound -> candidate | BEHAVIOR GREEN / SERIALIZATION DUPLICATED | Full candidate behavior is preserved, but the compact candidate index duplicates the same candidate identities already represented by missed plus terminal order/trade rows. |
| candidate -> selector | BEHAVIOR GREEN | No policy change in this batch. |
| selector -> scheduler | BEHAVIOR GREEN / SCORECARD DUPLICATED | One canonical scheduler option trace is written three times on every V250 scorecard. |
| scheduler -> risk | BEHAVIOR GREEN | Finalizer/probe truth remains materialized and must not be weakened. |
| risk -> order -> lifecycle -> fill | BEHAVIOR GREEN | Zero REFUSED/source-gap execution; all terminal rows remain materialized. |
| fill -> exit | BEHAVIOR GREEN | No exit or result transformation is allowed. |
| decision/ledger | OPEN SAME-ROOT DEFECT | The exact current-FVG partition is serialized twice per decision and candidate counts become zero when both candidate ledgers are omitted even though summary stats and missed/terminal rows preserve the full surface. |

## Same-Root Batch

Batch: `B7_4_BROAD_PROOF_SERIALIZATION_SCALABILITY`.

Affected components:

- `run_broad_live_as_if_replay_harness.py`: canonical decision and scorecard
  projection; explicit compact modes; summary row-count/materialization truth.
- `build_source_bound_execution_parity.py`: relational candidate fallback count
  and source semantics when candidate/candidate-index JSONLs are omitted.
- `run_selected_package_replay_bridge.py`: canonical scheduler trace fallback.
- `verify_denominator_to_deployment_execution.py`: canonical projection and
  relational candidate-surface invariants.
- focused harness/parity/bridge/verifier tests.
- current root map, continuation cursor, Fable matrix, and storage manifest.

Patch classification:

- exact duplicate removal and canonical alias references: performance plus
  diagnostic-ledger correctness;
- candidate relational-union counting: diagnostic-ledger correctness;
- consumer fallback and verifier invariants: correctness;
- replay behavior: intentionally neutral.

## Expected Measurable Effect Before Replay

- candidate -> scorecard, scorecard -> order, order -> fill: unchanged;
- missed positive/negative R, trade count, gross/final/net R, cash, W/L/F,
  stress/MC, and full/reduced risk distribution: unchanged;
- executed REFUSED/source-gap: remains `0/0`;
- V250-equivalent decision serialization: at most 55% of prior bytes while
  preserving the top-level FVG partition exactly;
- V250-equivalent scorecard serialization: at most 55% of prior bytes while
  preserving one canonical complete option trace and every finalizer probe;
- candidate-index JSONL in the B7.4 long-window mode: omitted, while declared
  candidate count and the exact missed/order/trade candidate-instance union
  remain equal to the in-memory candidate count;
- B7.4 proof must still produce full candidate-instance parity and missed-
  opportunity accounting across all 82 sleeves.

## Proof Scope And Acceptance

No policy replay is needed to prove a post-simulation serialization transform.
First use focused synthetic and exact V250-row projection tests. The batch helps
only if:

1. canonical decision/scorecard values are byte-for-byte value-equal to their
   omitted aliases before compaction;
2. projected consumers recover the same scheduler options, POI partitions,
   immutable authority, finalizer probes, and candidate identities;
3. serialized bytes fall below the limits above;
4. summary candidate counts remain exact when duplicate candidate ledgers are
   omitted;
5. compile, focused tests, verifier fixtures, and diff check pass;
6. no selector/scheduler/risk/order/lifecycle/exit configuration or behavior
   field changes.

The batch fails if any authority field, option identity/rank/selection, POI
partition row, finalizer probe, candidate instance, or safety invariant is lost.
A disagreement between in-memory candidate count and the relational
missed/order/trade union exposes the next deeper ledger defect and blocks B7.4.

After this focused proof is green, run the unchanged current behavior exactly
once over 2026-06-01..19, then build parity, flow, same-window comparison,
stress/MC, route artifacts, and verifier proof. Do not tune policy before that
evidence is parsed.

## Focused Proof Closure

Verified UTC: 2026-07-13T22:40:38Z.

- Compile passes for the harness, parity builder, selected-package bridge, and
  route verifier; 579 focused tests pass with only the pre-existing unknown
  `asyncio_mode` warning.
- Exact V250 LFS streaming proves 11,520 decision rows project from
  1,415,053,882 to 751,721,706 bytes (53.123186%) and 480 scorecards project
  from 2,295,150,991 to 1,092,357,361 bytes (47.594139%), with zero missing
  canonical partitions or traces.
- Targeted prefix
  `BROAD_LIVE_AS_IF_REPLAY_V251T_B7_4_SERIALIZATION_RELATIONAL_TARGETED_20260601_XAUUSD`
  proves 531 candidates equal the exact 531-row missed/order/trade union with
  zero duplicate or missing instance keys while writing no candidate or
  candidate-index JSONL.
- All 92 projection-eligible decisions and all 92 scorecards are certified.
  The other 2,116 targeted decision rows are explicit no-source diagnostics
  for symbols outside the requested XAUUSD slice, not omitted FVG payloads.
- The reconstructed relational candidate surface has zero candidate-quality,
  scheduler-quality, identity, displacement, or compact-projection issues.
  Scalar risk-authority provenance is preserved in compact missed rows.
- The targeted slice has zero order/trade rows, so its two empty-terminal POI
  warnings are expected and do not substitute for the non-vacuous broad proof.

The focused batch is DONE and behavior-neutral. B7.4 broad proof is authorized
once, with this exact command surface: repaired profile only, full 24-symbol
grid, 2026-06-01..19, candidate and candidate-index ledgers omitted under the
exact relational contract, packet sidecar omitted, and missed/decision/
scorecard compact modes enabled. Broker/live/final remain false.

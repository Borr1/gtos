# B7.4 V258 Source-Authority Repair Retry Pre-Replay Brief

Generated UTC: 2026-07-14T09:33:43Z.

## Decision

Retry V258 only after committing the complete source-authority repair batch.
The first V258 attempt never entered campaign execution and contains no
behavioral evidence: all 24 symbols failed the immutable June 1-19 static
source plan. The exact read-only exports, resolver composition, overlap
validation, and bounded MT5 history-refresh repair now pass focused tests and
real-data probes. No selector, scheduler, risk, cost, order, lifecycle, fill,
exit, or package policy changed.

## Current Process And Replay State

- No broad replay, export, pytest, compile, builder, verifier, or Git
  maintenance process is active.
- Latest accepted behavioral replay remains V257 on 2026-06-01..05.
- Failed V258 attempt status: `failed_partial_not_final_proof`; campaign not
  entered; candidate/scorecard/order/trade/missed economic behavior absent.
- The failed prefix may be reset by the harness and reused only after this
  checkpoint is committed. It is not a completed replay to preserve as an
  active comparator.

## Accepted Behavioral Anchor

V257 exactly reproduces V250 on June 1-5:

- candidates / scorecards / order events / terminal orders / fills:
  `35,191 / 480 / 30 / 14 / 13`;
- physical W/L/F `8/5/0`, gross/final/net
  `+7.82542991 / +7.82542991 / +7.03578717R`;
- physical cash PnL `-$68.02401535`;
- headline ordered-tick trades `4`, W/L/F `3/1/0`, net `+1.59506223R`,
  cash PnL `-$67.96685163`;
- diagnostic-only rows/net `9 / +5.44072494R`;
- full-risk/reduced-risk fills `2/11`;
- expired unfilled / filled orders `1/13`;
- executed broker-cost REFUSED/source-gap/unsigned `0/0/0`;
- missed rows `35,177`;
- +0.05/+0.10/+0.20R headline stress net
  `+1.39506223 / +1.19506223 / +0.79506223`;
- 200-iteration headline Monte Carlo total `+1.59506223R`, worst max
  drawdown `-1.12773511R`.

V89D (`56 / +34.84520454R`), V90 (`51 / +28.84201157R`), and V92
(`51 / +29.35570236R`) remain historical hostile-window comparators, not the
June denominator. The V258 retry must report its own exact June 1-19 source
bound denominator and must not compare nineteen days directly to the global
1.249M-R diagnostic reservoir.

## Dirty Files And Coordination

Active same-root changes:

- `run_broad_live_as_if_replay_harness.py`: source-family priority, bounded
  static family, composite M1 day resolution, exact overlap validation;
- `scripts/export_mt5_research_ohlcv.py`: bounded final-window history refresh;
- `tests/test_broad_replay_repair_config.py`: cross-root and composite M1
  contracts;
- `tests/test_mt5_research_ohlcv_export.py`: refresh and redacted identity
  contracts;
- `build_denominator_to_deployment_execution.py`: physical broad-quality flow
  dependency closure;
- `verify_denominator_to_deployment_execution.py`: newest-complete replay
  authority selection and builder-produced source-count verification;
- `tests/test_denominator_to_deployment_verifier.py`: focused dependency,
  compact-retention, and current-count contracts;
- this brief, root map, continuation cursor, Fable matrix, compact repair
  manifest, and the three failed-attempt tombstone artifacts.

Unrelated `AGENTS.md`, `.context/LIVE_STATE.md`, data/tick, knowledge,
shadow/runtime, old route artifacts, and LFS hydration dirt remain excluded.
No subagent is active or unreconciled. Prior subagent dispositions remain those
recorded in the V257 brief; none produced this source failure or is deferred
into this batch.

## Root-Cause Chain

| Stage | State before retry |
| --- | --- |
| source-bound -> source authority | REPAIRED / REAL-DATA GREEN. Exact bounded D1/H4/M15 and supplemental M1 sources reach June 19. Family priority is global across roots. |
| source authority -> candidate | INPUT IDENTITY GREEN / EXECUTION PROOF OPEN. The nested June 1-5 plan digest exactly matches V257; V258 must reproduce candidate projections during execution. |
| candidate -> selector | UNCHANGED TRUTH GREEN / VALUE OPEN. |
| selector -> scheduler | UNCHANGED TRUTH GREEN / VALUE OPEN. |
| scheduler -> risk | UNCHANGED TRUTH GREEN / CALIBRATION OPEN. |
| risk -> order | UNCHANGED GREEN. REFUSED/source-gap/unsigned rows remain non-executable. |
| order -> lifecycle -> fill | UNCHANGED TRUTH GREEN / BROAD TRANSFER OPEN. |
| fill -> exit | UNCHANGED / BROAD VALUE OPEN. |
| ledger/proof | SOURCE REPAIR GREEN. Failed attempt remains an explicit tombstone; retry must materialize full behavior and proof outputs. |

## Same-Root Batch And Proof

Batch: `B7_4_V258_SOURCE_AUTHORITY_REPAIR`.

Correctness repairs:

1. configure the exact bounded static source family for D1/H4/M15;
2. make declared family priority global across active/integration roots;
3. resolve original and supplemental M1 sources per symbol-day;
4. prefer original M1 where present, fill only absent days from supplemental;
5. fail closed if overlapping populated M1 days differ;
6. retry the exporter's final historical window and retain the newest/most
   complete response.

Diagnostic/proof repairs: emit selected family/candidate counts, overlap
dispositions, and refresh statistics. Performance policy changes: none.

Real-data acceptance:

- full June 1-19 source plan valid, digest
  `eeed6163d40b5a33cb8415fc701f7392905ecf2bcb2bd6a28295cb3edf585fa7`;
- 24/24 symbols, 120 static/tick authority rows, 24 tick rows, no missing or
  incomplete sources;
- 456 M1 symbol-days: 368 meet floor, 88 verified no-session, zero below floor;
- 260 original-monthly and 196 supplemental M1 day selections;
- 172 exact overlaps, zero conflicts;
- nested June 1-5 digest exactly equals V257:
  `8c6fa609d07832a83b920a20a95a5c2626fbafba087692a31b32a0a6695a4d6b`;
- compile, 492 harness/verifier tests, 126 parity/comparator/export tests, and
  all 820 timewarp runtime tests pass.

## Route Recertification After Storage Hydration

The canonical builder is green after hydrating its exact bridge/grid and V250
proof closure. Its manifest binds V250 as the newest physically complete
broad-quality authority and V254T as the holdout gate. The paired V250 flow
bucket is now a required physical dependency whenever its flow summary is
present, so storage dematerialization can no longer leave a flattering
summary-only proof surface.

The physical verifier is `ok=true` with zero issues. It no longer treats the
newer compact-retained V257 checkpoint as a full broad-quality authority when
its raw decision, scorecard, missed, and candidate-index ledgers are
intentionally absent. Current source-package outputs are self-consistent at
509 total rows and 484 FTMO blocker rows; stale 1229/1204 literals are retired.
Prompt hardening, the full-JSONL route audit, and the parent full-JSONL audit
pass. This is a correctness/proof repair only and changes no replay policy.

## Expected Measurable Effect

This batch should change V258 from preflight failure to a complete campaign. It
must not change the accepted June 1-5 behavior.

- candidate -> scorecard: first five days exactly `35,191 -> 480`; full-window
  count unknown and uncapped;
- scorecard -> order -> fill: first five days exactly `480 -> 30 events -> 13
  fills`; later-window transfer unknown;
- missed positive/negative R: no first-five-day delta; later values must be
  fully materialized by exact blocker;
- trade count/net/gross/final R/cash/W/L/F: exact V257 inside June 1-5 and
  measured, not presumed, for June 6-19;
- cost REFUSED/source-gap/unsigned execution: `0/0/0`;
- risk expression: first-five physical fills exactly `2 full / 11 reduced`;
- source plan: one invariant full-window digest across all 19 one-day chunks;
- capacity: zero replay-source cache remainder after every completed chunk;
- improvement attribution: source availability and candidate-input
  correctness only, not opportunity blocking.

Help is proven if V258 completes, preserves the exact nested V257 projections,
and materializes the full larger-window behavior package. It fails if any
nested identity/value drifts, any M1 overlap conflicts, source/cache/capacity
contracts fail, or a safety leak executes. If truth remains green but economics
are weak, that exposes the next selector/scheduler/risk/order/lifecycle/exit
value flaw; it does not invalidate this source repair.

## Exact Retry

The implementation and route checkpoint is committed at `6d812ee74`.
Post-recertification cleanup dematerialized 130 clean tracked, commit-recoverable
route JSONLs totaling 13.777 GiB while retaining the 82-sleeve registry,
1,101-axis authority ledger, all V257 retained proof, current summaries, source
exports, and the V258 failure tombstone. Free space is 26,697,808 KiB; after the
13,347,782,507-byte output projection, the expected reserve is 13.030 GiB,
above the fixed 8 GiB floor. Exact evidence is in
`B7_4_V258_POST_RECERTIFICATION_STORAGE_RETENTION_MANIFEST_20260714T111912Z.json`.

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-01 \
  --end 2026-06-19 \
  --chunk-size 1 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V258_B7_4_BROAD_JUNE_CACHE_SAFE_SOURCE_IDENTITY_20260601_20260619_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID \
  --profiles repaired_package_conversion_v3 \
  --max-candidates-per-symbol-window 0 \
  --omit-candidate-ledger \
  --omit-candidate-index-ledger \
  --omit-packet-sidecar-ledger \
  --compact-missed-ledger \
  --compact-decision-ledger \
  --compact-scorecard-ledger \
  --candidate-ledger-packet-max-bytes 1024 \
  --scorecard-ledger-packet-max-bytes 4096 \
  --compact-scorecard-symbol-risk-config \
  --scorecard-probe-row-limit 12 \
  --gc-between-chunks
```

No symbol subset, candidate cap, skipped tick source, native-H1 override, or
policy tuning is authorized. Broker/live/final remain false; local replay
package authority remains full.

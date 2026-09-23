# B7.4 V258 June 1-19 Cache-Safe Broad Proof Pre-Replay Brief

Generated UTC: 2026-07-14T08:41:55Z.

## Decision

Run the unchanged repaired-package path over 2026-06-01 through 2026-06-19
after the bounded storage contract is applied and reverified. This is the B7.4
broad economic proof that follows V257's exact five-day infrastructure and
truth equivalence. It is not a selector, scheduler, risk, order, lifecycle,
fill, or exit tuning run.

The run must preserve the full 82-sleeve / 1,101-member-axis package, all 24
configured symbols, broker-calibrated cost authority, exact relational
candidate materialization, one-day execution chunks, invariant full-window
source authority, and complete missed-opportunity accounting. Broker mutation,
live broker authority, and final selection remain false.

## Process And Checkpoint State

- Current HEAD: `dae7c620b4f6c6b65e53b3a7b48d5300734dcd3a`
  (`fix replay source cache identity and recertify B7.4`).
- No replay, builder, verifier, pytest, compile, or Git-maintenance process is
  active. The lone `pgrep` match was the probe itself.
- Latest accepted run:
  `BROAD_LIVE_AS_IF_REPLAY_V257_B7_4_REPLAY_SOURCE_CACHE_IDENTITY_REPAIR_V250_COMPARATOR_20260601_20260605_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID`.
- V257 completed and was route-recertified. It is not running and must not be
  duplicated.
- Planned run:
  `BROAD_LIVE_AS_IF_REPLAY_V258_B7_4_BROAD_JUNE_CACHE_SAFE_SOURCE_IDENTITY_20260601_20260619_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID`.
- V258 should finish, not replace another process. A partial run is not broad
  proof and must be labeled and salvaged only from fully flushed chunks.

## Latest Accepted Numbers

V257 exactly reproduces V250 on 2026-06-01 through 2026-06-05:

- candidates / scorecards / order events / terminal orders / physical fills:
  `35,191 / 480 / 30 / 14 / 13`;
- daily candidates: `7,244 / 7,175 / 6,603 / 6,981 / 7,188`;
- missed rows: `35,177`;
- physical W/L/F: `8/5/0`;
- physical gross/final/net R:
  `+7.82542991 / +7.82542991 / +7.03578717`;
- physical cash PnL / risk cash / summed risk:
  `-$68.02401535 / $2,625.29039511 / 2.625%`;
- headline ordered-tick rows: `4`, W/L/F `3/1/0`;
- headline gross/final/net R:
  `+1.92353135 / +1.92353135 / +1.59506223`;
- headline cash PnL / risk cash / summed risk:
  `-$67.96685163 / $1,199.80760351 / 1.20%`;
- diagnostic-only rows / net R: `9 / +5.44072494R`;
- physical full-risk / reduced-risk fills: `2 / 11`;
- expired unfilled / filled orders: `1 / 13`;
- executed broker-cost REFUSED / source-gap / unsigned rows: `0/0/0`;
- stress net R at +0.05/+0.10/+0.20R per headline trade:
  `+1.39506223 / +1.19506223 / +0.79506223`;
- Monte Carlo: 200 iterations over four headline trades, total
  `+1.59506223R`, worst max drawdown `-1.12773511R`.

The nine diagnostic rows were truth-reclassified away from strict headline
parity because they use M1-proxy terminal authority. No identity or economic
value changed.

## Baseline Interpretation

- V89D: `56 trades / +34.84520454R`.
- V90: `51 trades / +28.84201157R`.
- V92: `51 trades / +29.35570236R`.
- V250 and V257: exact June 1-5 current-truth comparators described above.

V89D/V90/V92 are historical hostile-window comparators and not the V258
denominator. V250/V257 are the nested June 1-5 acceptance checksum. V258 must
report the exact source-bound denominator and transfer stages for its own
June 1-19 window; it must not compare nineteen days directly to the global
1.249M-R diagnostic reservoir.

## Dirty And Coordination State

- Active route code, tests, verifier, root-cause map, cursor, and Fable matrix
  are committed at `dae7c620b`; there is no uncommitted policy/code patch.
- `.context/LIVE_STATE.md` was regenerated and remains excluded from scoped
  commits.
- `AGENTS.md`, data/tick, knowledge-base, shadow/runtime, and older untracked
  replay artifacts are unrelated dirt and remain untouched.
- The prior storage manifest has a valid uncommitted V254T/V255T extension that
  is preserved and will be committed with this storage checkpoint.
- Six historical truth-smoke JSONLs appear modified after hydration because a
  later route-local LFS rule filters them. They are explicitly ineligible for
  cleanup or staging.
- No subagent is active and no return is unreconciled. No new audit wave should
  start before V258 is parsed unless a hard compile, truth, or verifier defect
  appears.

Subagent dispositions verified against the later certified code:

- Incorporated: Mendel, Herschel, Wegener, Avicenna, Carson, Noether, Fermat,
  Euclid, Pascal, Anscombe, Hubble, Carver, Ampere, Plato, Popper, Pasteur,
  Lovelace, Helmholtz, and the Euclid/James/Darwin/Boole/Parfit V239R3 findings.
  Their actionable identity, provenance, selector/scheduler, risk, lifecycle,
  POI, terminal binding, and verifier defects were closed through V240-V249 and
  retained by V250/V257 certification.
- Rejected: Pasteur's stronger final-displacement claim was not supported by
  current evidence and did not authorize a policy change.
- Stale/no return: Arendt, Turing, Hegel, and Socrates returned no actionable
  current finding and are closed without a claim.
- Deferred current findings: none. Economic calibration and extended-history
  questions belong to B7.4/B7.5, not to an unreconciled agent return.

## Current Root-Cause Map

| Transfer stage | Current state before V258 |
| --- | --- |
| source-bound -> source authority | GREEN. The selected split owns one immutable source plan; chunk execution is a subset. |
| source authority -> candidate | CORRECTNESS GREEN / VALUE OPEN. V257 restores all V250 identities and zero cache remainder. V250 has 894/1,101 generated package axes; the remaining 207 stay visible for exact V258 attribution. |
| candidate -> selector | TRUTH GREEN / VALUE OPEN. Candidate rows carry complete execution inputs; current cost/session refusals remain scoreable but non-executable. |
| selector -> scheduler | TRUTH GREEN / VALUE OPEN. Signed action, ranking, displacement, and reallocation provenance are preserved. Broad allocation quality is not yet proven. |
| scheduler -> risk | TRUTH GREEN / CALIBRATION OPEN. Signed full/reduced authority is preserved. V257 physical risk expression is 2 full / 11 reduced; no blanket promotion is authorized. |
| risk -> order | GREEN. REFUSED, source-gap, unsigned, and unresolved authority rows cannot execute. |
| order -> lifecycle -> fill | TRUTH GREEN / TRANSFER OPEN. V257 has 14 terminal orders, 13 fills, and one expiry; V258 must expose broader fillability and lifecycle value. |
| fill -> exit | VALUE OPEN. V257 headline R survives +0.20R stress but contains only four rows and negative cash PnL. V258 must test exit/economic expression on the larger current-truth sample. |
| ledger/proof | GREEN FOR V250/V257. Relational candidates, capacity-v2 cleanup, source-plan invariance, risk provenance, and headline/diagnostic truth are verifier-bound. V258 must preserve them over the full window. |

## Fable Dependency State

- B0 and B1: DONE.
- B2: DONE/CONDITIONAL and preserved by V257.
- B3: DONE for targeted proof; broad risk-expression calibration remains B7
  evidence, not a missing ladder implementation.
- B4: DONE/CONDITIONAL and preserved by ordered-tick authority.
- B5: DONE.
- B6: DONE WITH LABEL; broker-calibrated cost stays authoritative.
- B7.1, B7.2, B7.3: DONE at their bounded proof levels.
- B7.4: ACTIVE. V257 closed infrastructure equivalence; V258 is the broad
  June 1-19 proof.
- B7.5: OPEN and dependent on B7.4.
- B8: OPEN and dependent on B7. Broker/live/final remain false.

## Same-Root Batch And Exact Components

Batch: `B7_4_V258_JUNE_1_19_CACHE_SAFE_BROAD_PROOF`.

Behavior code is unchanged. The proof exercises these current consumers:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`;
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`;
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`;
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/analyze_broad_live_as_if_replay_flow.py`;
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`;
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`.

Classification:

- correctness proof: chunk/source/cache/account/order-sequence invariance;
- diagnostic/ledger proof: complete transfer, missed-opportunity, risk, cost,
  fill, lifecycle, exit, stress, and Monte Carlo materialization;
- performance proof: measure unchanged policy over a broader objective window;
- policy repair: none before V258 evidence.

## Expected Measurable Effect

The first five days must be exactly V250/V257. June 6-19 behavior is unknown
and must be measured rather than presumed positive.

- Candidate -> scorecard: first five days exactly `35,191 -> 480`; complete
  June 1-19 counts and axes must be materialized with no candidate cap.
- Scorecard -> order -> fill: first five days exactly `480 -> 30 events -> 13
  fills`; later-window transfer must be fully attributed.
- Missed positive/negative R: unknown before run; all scoreable and diagnostic
  missed rows must remain present by exact blocker and evidence class.
- Trade count, gross/final/net R, cash PnL, W/L/F: unknown outside the nested
  checksum and must not be optimized by suppression.
- Cost REFUSED/source-gap/unsigned execution: must remain `0/0/0`.
- Full-risk/reduced-risk: first five physical fills exactly `2/11`; later rows
  must preserve signed tier and cash/risk provenance.
- Capacity: one completed checkpoint per selected day, one account and broker
  across chunks, monotonic order sequence, invariant source-plan digest, and
  zero closed-bar/predecision-tick/row-time cache entries after every chunk.
- Runtime package: exactly 82 unique sleeves and 1,101 unique member axes,
  fail-closed before campaign execution.

## Exact Command

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

No `--symbols`, `--smoke-subset`, `--max-days`, `--skip-tick-source`, or
native-H1 override is allowed.

## Success, Failure, And Next-Deeper-Flaw Criteria

Success requires:

1. complete June 1-19 output and no active/partial campaign;
2. exact nested V250/V257 June 1-5 candidate, order, trade, missed, risk,
   economic, and safety projections;
3. valid capacity-v2 and source-authority contracts for every completed chunk;
4. zero replay-source cache remainder after every chunk;
5. exact relational candidate union and complete scorecard/order/trade/missed
   provenance;
6. zero REFUSED/source-gap/unsigned execution;
7. full raw/headline/diagnostic behavior, exact-window source-bound transfer,
   flow, parity, missed-opportunity, stress, Monte Carlo, symbol/session/side/day,
   risk tier, order policy, lifecycle, fill, and exit outputs;
8. no opportunity collapse used to manufacture a positive result.

Failure is any nested identity/value drift, nonzero source-cache remainder,
missing runtime package input, incomplete ledger relation, safety leak,
unflushed chunk, or disk-safety breach. A partial run is salvage evidence only.

If infrastructure and truth remain green but June 1-19 economics are weak, the
run succeeds as B7.4 exposure and identifies the next deeper value flaw. The
next action is then a same-root repair chosen from measured selector/scheduler,
risk expression, order/fillability, lifecycle, or exit buckets, followed by the
smallest targeted proof. It is not permission to suppress trades or tune from
date/symbol/session outcomes.

This broad run measures the larger current window; it still does not prove
total-reservoir conversion, B7.5 extended-history robustness, final package
selection, or broker-live readiness.

# B7.3 V250 Independent-Regime Pre-Replay Brief

Generated UTC: 2026-07-13T17:15:00Z.

## Decision

Run one full configured-symbol replay over `2026-06-01..2026-06-05` using the
exact behavior code committed at `f0fc2b425`. This is Fable B7.3, an objective
non-hostile regime proof. It is not a tuning run and no selector, scheduler,
risk, cost, order, lifecycle, fill, or exit policy changes are permitted
between V249 and V250.

Broker mutation, live broker authority, and final selection remain false.
Local replay/package authority remains full across all 82 sleeves.

## Current Process And Git State

- No replay, builder, verifier, test, parity analyzer, or git process is active.
- Latest route checkpoint commit: `f0fc2b425` (`certify V249 hostile replay authority`).
- No behavior code is dirty after that commit.
- Unrelated tracked dirt remains limited to `.context/LIVE_STATE.md` and
  `AGENTS.md`; neither belongs to this replay checkpoint.
- Current task-owned untracked control artifact:
  `.context/context_os/V250_PRE_REPLAY_STORAGE_RETENTION_MANIFEST_20260713T171054Z.json`.
- Seven superseded V245 raw payloads were hash-recorded and removed exactly;
  retained anchors revalidated. Free space is `24,941,703,168` bytes. V249's
  complete compact artifact family occupies about `5.55 GB`, so the compact
  B7.3 serialization has bounded working headroom.

## Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V249_B7_2_HOSTILE_5D_V248_SIGNED_ACTION_TERMINAL_BINDING_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

Scope: configured 24-symbol hostile `2026-05-13..17` window, repaired profile
only, complete compact candidate index, compact missed ledger.

- source / decision / candidate / scorecard / order-event / terminal-order /
  physical-trade / missed: `310 / 11424 / 25006 / 288 / 45 / 22 / 20 / 24984`
- physical W/L/F: `11/9/0`
- physical gross/final/net: `+2.75652827 / +2.75652827 / +1.16150430R`
- physical cash PnL / risk cash / risk pct: `+$201.14669730 / $6994.15658020 / 6.95%`
- ordered-tick headline: `18` trades, `10/8/0`, `+0.28044419R` net,
  `+$113.42435391`; two M1-only rows are diagnostic at `+0.88106011R`
- full-risk / reduced-risk physical fills: `6/14`
- cost REFUSED / source-gap executions: `0/0`
- stress at extra `0.05/0.10/0.20R`: `-0.61955581 / -1.51955581 / -3.31955581R`
- Monte Carlo: `200` trials, worst drawdown `-6.42886010R`
- package / candidate / scorecard-present / order / filled axes:
  `1101 / 894 / 350 / 17 / 15`

V249 is route-certified B7.2 evidence. It is not independent-regime,
broad-history, final-selection, or live proof.

## Comparator Discipline

Hostile-only anchors, not direct B7.3 denominators:

| Prefix | Trades | Net R | Gross/Final R | Cash PnL |
| --- | ---: | ---: | ---: | ---: |
| V89D | 56 | +34.84520454 | +39.93441037 | +8178.90660707 |
| V90 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 |
| V92 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 |
| V249 | 20 physical / 18 headline | +1.16150430 physical / +0.28044419 headline | +2.75652827 physical / +1.75652827 headline | +201.14669730 physical / +113.42435391 headline |

Exact B7.3 same-window comparator:

- V104 `2026-06-01..05`: `35191` candidates, `480` scorecards, `111`
  order events, `46` trades, W/L/F `26/20/0`, gross/final/net
  `+18.36174510/+18.36174510/+14.73101491R`, cash `+$2850.02330565`,
  cost `3.63073019R`, stress `+12.43101491/+10.13101491/+5.53101491R`,
  Monte Carlo worst drawdown `-9.32256052R`.

Retained broader comparator:

- V110B covers `2026-06-01..19`, not only the B7.3 five days: `75274`
  candidates, `1056` scorecards, `193` order events, `95` trades, W/L/F
  `52/43/0`, gross/final/net `+28.71092008/+28.71092008/+22.80442652R`.
  Its retained summary cannot be used as a direct five-day denominator. V250
  will be compared directly to V104; V110B is structural context and the exact
  19-day comparison belongs to B7.4 unless a retained same-window slice is
  recovered.

## Subagent Reconciliation

- Current unreconciled returns: `0`; active subagents: `0`.
- All findings that shaped V249 are incorporated and frozen in the committed
  producer/consumer/test/verifier chain.
- No finding is being implemented from stale snapshot evidence.
- No new audit wave starts before V250 completes and is parsed. If V250 exposes
  a material failure, any later agents receive an immutable V250 snapshot and
  disjoint lanes.

## Root-Cause Chain At Replay Start

| Stage | State | Current evidence / open question |
| --- | --- | --- |
| source-bound -> candidate | FIXED FOR GENERATED V249 SURFACE; B7.3 OPEN | Full 82-sleeve scoring preserved; V249 has exact candidate identity and complete POI state. Measure June same-window source and generated axes without assuming hostile counts. |
| candidate -> selector | FIXED CONTRACT; B7.3 OPEN | Raw, materialized, effective, and signed action authority are separate and consumed. Measure June admission and missed-positive/negative partitions. |
| selector -> scheduler | FIXED CONTRACT; B7.3 OPEN | Exact instance signing, ranking, displacement, and reallocation consumers are verifier-bound. Measure scorecard/order transfer and named blockers. |
| scheduler -> risk | FIXED CONTRACT; B7.3 OPEN | Signed full/reduced ladder and final-risk atomicity are bound into terminal rows. Test structural consistency against V249's `6/14` full/reduced physical split. |
| risk -> order | FIXED CONTRACT; B7.3 OPEN | REFUSED/source-gap/non-fillable rows remain scoreable missed but non-executable. Require zero invalid execution. |
| order -> lifecycle -> fill | FIXED CONTRACT; B7.3 OPEN | Signed order-policy and terminal binding, pending identity, cancel/replace, expiry, and ordered-tick fill truth are current. Measure June expiry and fill transfer. |
| fill -> exit | PARTIAL VALUE PROOF | V249 exits are honest but headline stress is negative. Determine whether June behavior is positive, stress-robust, and whether losses arise from admission, sizing, lifecycle, or selected-policy path. |
| ledger/verifier | DONE FOR V249; B7.3 REBUILD REQUIRED | V249 verifier has zero issues. V250 must regenerate full deterministic flow, parity, comparison, stress, and MC surfaces before acceptance. |

## Same-Root Batch

Batch: `B7_3_INDEPENDENT_REGIME_PROOF_UNCHANGED_V249_CODE`.

Classification: behavior-neutral proof execution. There is no policy patch in
this batch. The affected components are the replay harness and its deterministic
route builders/analyzers/verifier consumers only; behavior code remains the
committed V249 code.

Output prefix:
`BROAD_LIVE_AS_IF_REPLAY_V250_B7_3_NON_HOSTILE_5D_UNCHANGED_V249_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`

Command:

```bash
python3 -u research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-01 \
  --end 2026-06-05 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V250_B7_3_NON_HOSTILE_5D_UNCHANGED_V249_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID \
  --omit-candidate-ledger \
  --omit-packet-sidecar-ledger \
  --compact-missed-ledger
```

## Expected Measurable Effects

- Candidate generation should preserve the full configured-symbol/package
  surface for this exact window. Any delta from V104's `35191` rows or its
  package-axis denominator must be attributed, not silently accepted.
- Scorecard production should cover the configured five-day decision grid;
  any delta from V104's `480` scorecards must have a source/calendar reason.
- Scorecard -> order and order -> fill transfer must be nonzero, with every
  selected, skipped, delayed, expired, replaced, filled, and missed row carrying
  exact causal authority.
- REFUSED/source-gap/off-authority execution remains `0/0/0`.
- Both full-risk and reduced-risk fills should remain causally available; an
  all-reduced or all-full distribution is a regression unless exact candidate
  quality explains it.
- The run must itemize missed positive and missed negative R, added/removed
  V104 trades and R, expired/unfilled reasons, fill-realism classes, cost,
  stress, Monte Carlo, and package-axis transfer.
- Trade count and headline value are not preselected. Positive results are
  accepted only with preserved opportunity; negative results are retained as
  evidence and drive the next same-root repair.

## Acceptance And Failure Rules

Helped / B7.3 pass:

- complete uninterrupted five-day artifacts, verifier green;
- zero invalid cost/source/live/final execution;
- no candidate or trade collapse used to manufacture value;
- full/reduced risk expression remains structurally causal;
- added executable transfers are net positive and removed V104 winners have
  named predecision blockers;
- headline net is positive and the full metric set does not reveal a hidden
  diagnostic-fill or single-cell dependency.

Failed performance policy:

- truth surfaces remain valid but net value is negative, transfer collapses,
  added trades are net negative, or valid V104 winners are displaced without a
  sound predecision reason. Parse the whole chain and patch the highest-impact
  same-root batch before another broad run.

Deeper truth flaw:

- any REFUSED/source-gap/off-authority execution, identity mismatch, terminal
  binding contradiction, incomplete signed atom, impossible risk provenance,
  or interrupted/partial summary. Repair producer and every consumer first;
  do not treat the run as behavioral evidence.

This five-day replay proves or disproves the independent-regime gate. It does
not prove total reservoir conversion, extended-history robustness, final
selection, or live readiness.

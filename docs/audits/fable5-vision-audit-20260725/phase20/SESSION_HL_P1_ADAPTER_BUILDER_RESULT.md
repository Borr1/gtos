# Session HL — P1 broker-inert adapter builder

## Findings first

1. **P1-U2 resolves to an exact upstream-source blocker.** The eleven HK-commissioned
   January/April/May artifacts are hydrated and byte-exact. Their 73,999 downstream
   pool rows have 73,999 unique native join keys and exact 1:1 ordered-M1 sidecar
   coverage, with no duplicate or unmatched row. They do not contain the closed-M15
   history or contemporaneous MSO state needed to regenerate the current breaker
   opportunity set. A result-bearing P1 read or run therefore remains refused.

2. **The source-agnostic adapter is complete at source commit
   `41534770fa338f12b34d79c9625fd406219a41fe`.** Its only parent is the commissioned
   source head `a1cf205de52a7f279932e4436196a255ae5e7b9b`. HK commit
   `11594419a197e278263565ac7677ecfc3e317c31` remains evidence-only authority and was
   not merged, rebased, or made an ancestor.

3. **The adapter is default-off, broker-inert, dependency-injected, and
   denominator-preserving.** Each enabled synthetic source receives exactly eleven
   stage rows under the full seven-field composite identity. The first later-stage
   refusal creates one missed-opportunity entry; intervening stages remain explicit
   as not reached, and the frozen B0 disposition is always recorded unchanged. No
   source row can silently disappear or duplicate.

4. **The focused synthetic proof is green.** Thirty tests pass. The tool-derived
   exact-test A/B is `30 bad -> 0 bad`, 30 fixed, zero regressed. The parent capture
   is dirty only because it overlays the exact source-commit test bytes, SHA-256
   `ed9882f80c7c7db20611fdd4add646ebb9684a1635bb2655278fa813693d6fe0`, on the
   immutable parent where the adapter does not exist.

5. **No economic claim was opened.** HDE and HDF are exercised only with synthetic
   known answers. FTMO is represented only as the sole *future* economic scope;
   redacted_account remains mechanical-only. No inert published account snapshot was
   available in the commissioned evidence, so the adapter requires an injected,
   hash-bound research snapshot. Volume remains
   `NOT_EVALUABLE_OWNER_INPUT_REQUIRED` because no owner risk/allocation input was
   supplied.

`execution_authority: false`
`activation_authority: false`
`result_bearing_science_executed: false`

## Source conformance

The complete structural receipt is
`phase20/receipts/science/P1_ADAPTER_SOURCE_CONFORMANCE.json`.

| Window | Pool rows | Sidecar rows | Native-key duplicates | Unmatched | candidate_id reuse | Observed decisions |
|---|---:|---:|---:|---:|---:|---|
| January | 27,658 | 27,658 | 0 | 0 | 967 IDs / 6,745 rows | 2026-01-02..2026-01-30 |
| April | 25,056 | 25,056 | 0 | 0 | 746 IDs / 5,901 rows | 2026-04-01..2026-04-30 |
| May | 21,285 | 21,285 | 0 | 0 | 644 IDs / 4,560 rows | 2026-05-05..2026-05-29 |

The native source-side join domain is
`(candidate_id, symbol, side, decision_time_utc)`. `candidate_id` alone is not unique.
The source rows lack `source_window_id`, `source_opportunity_id`, and `account_scope`;
the adapter therefore requires those explicit inputs and refuses duplicates under the
commissioned identity:

`(source_window_id, source_opportunity_id, candidate_id, symbol, side,
decision_time_utc, account_scope)`.

The January path manifest declares `2026-01-01..2026-01-31`, while HK admits
`2026-01-01..2026-01-30`. No January decision row falls after January 30, but the
declaration mismatch is retained as a capture-authority requirement rather than
silently normalized.

Every path sidecar has schema `gtos-session-ck-ordered-path-sidecar-v1`, M1 source
timeframe, and ordered observations with exactly `time_utc/open/high/low/close` fields.
The manifest inventories bind 24 M1 symbol sources per window, four limited tick
sources in January and April, and none in May. They bind zero M15 sources and zero MSO
snapshots.

The hash-bound generator requires at least 51 closed M15 bars and contemporaneous
`M15.atr_14` plus `H1.breaker_blocks` state, including zone, direction, original-OB
direction, formation/mitigation time, causing event, and retest status. The exact next
prerequisite is one immutable true-UTC predecision bundle per admitted opportunity,
bound by path, bytes, SHA-256, schema, window, as-of time, generator/route identity,
and a one-to-one composite-identity join. Missing or multiply joined rows must refuse.
No February, March, live-forward, W7, CJ substitution, alternative candidate, or
post-hoc drop is permitted.

## Implemented contract

The runner is
`phase20/receipts/wave20_complete_path_shadow.py`; its focused tests are
`tests/research_infra/test_wave20_complete_path_shadow.py`.

- The default-off return path never iterates the supplied source and never invokes a
  dependency.
- The enabled path requires four explicitly broker-inert callables: candidate
  generation, dynamic routing, scheduler capture, and fill/no-fill projection.
- The fixed B0 transform reuses the pure current-breaker repair at its commissioned
  hash. Exactly one candidate per source is required.
- Permission is a pure in-memory projection over explicit session, account-headroom,
  symbol, and inert-interface facts. Missing or invalid required facts refuse.
- Scheduler V4 is capture-only: it cannot select, rank, suppress, size, write, or
  alter the incoming disposition. Any learned probability/value field raises a
  whole-run `K1StaleRefusal`.
- The pure market request preimage and internal software-limit intent mirror only the
  hash-bound reference field mapping. The live-capable reference modules are never
  imported, and the projection is non-executable.
- HDE retains its `spread + expected slippage + swap + commission` arithmetic,
  `1e-8` tolerance, and complete/incomplete/refused states. HDF retains the integrated
  collision, first-deadline, conservative M1, partial/cost-once, and terminal-state
  semantics.
- Source guards refuse February economics, March, live-forward, breadth, alternative
  families, post-hoc drops, O1, C0, N1, and FC2 before an injected reader can run.

The implementation receipt is
`phase20/receipts/science/P1_ADAPTER_IMPLEMENTATION.json`; the self-contained A/B is
`phase20/receipts/SESSION_HL_AB_RECEIPT.md`.

## Verification and boundaries

- focused module: 30 passed, 0 failed, 0 errored;
- exact focused A/B: 30 bad at the parent, 0 bad at the source commit, 0 regressed;
- no P1 execution, replay, paper shadow, canary, calibration, or economic gate;
- no broker, VPS, MetaTrader, runtime, production, token, credential, account-security,
  live-config, or trading contact;
- no February economic read, March read, live-forward read, family breadth, alternate
  candidate, or post-hoc filtering;
- no configuration mutation, merge, push, evidence deletion, shared map edit, or
  session-register edit;
- repository-wide tests were not run because the implementation is isolated and the
  commission explicitly requires focused tests only.

The remaining result-bearing prerequisites are the exact M15/MSO capture (P1-U2),
published inert account/profile/symbol snapshots (P1-U4), an owner risk/allocation
input if volume is evaluated (P1-U5), a separate execution authorization (P1-U10),
and one hash-bound inert route-parameter bundle (P1-U11). None is inferred here.

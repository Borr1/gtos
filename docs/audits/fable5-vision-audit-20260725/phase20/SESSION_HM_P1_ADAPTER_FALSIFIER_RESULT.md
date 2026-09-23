# Session HM — P1 adapter independent falsification

## Verdict

`SAFE_FOR_BROKER_INERT_SYNTHETIC_USE_ONLY_AFTER_BOUNDED_HM_REPAIR_P1_EXECUTION_BLOCKED`

`execution_authority: false`

`activation_authority: false`

`result_bearing_science_executed: false`

The adapter as received was not safe for its full claimed synthetic contract: the exact final HM test bytes produce **40 bad / 30 passed** on `41534770fa338f12b34d79c9625fd406219a41fe`. Seven bounded fail-closed defects were repaired in the adapter only. The same 70-test HM module is **70 passed / 0 bad** at tested source commit `1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51`; the 30 existing HL tests also pass, for **100 passed / 0 failed / 0 errors** combined.

The second claim survived falsification. The 73,999 admitted rows are a one-to-one downstream opportunity/M1-path domain, not a reproducible upstream candidate-generation bundle. No committed or preserved offline artifact satisfied all required conjuncts: hash-bound, true-UTC, predecision-only, one-to-one with the admitted four-part identity, at least 51 closed M15 bars, contemporaneous `M15.atr_14`, contemporaneous `H1.breaker_blocks`, and an inert route-parameter bundle. Result-bearing P1 therefore remains blocked on exact upstream capture. This is not candidate rejection and does not open another family.

## Findings

1. **The original adapter had real bounded defects.** Truthy non-booleans enabled it; malformed permission containers escaped as exceptions; allowed window labels could alias forbidden paths; January 31, cross-window, naïve, or malformed decision times reached dependencies; scheduler mutation could alter later inputs; learned probability/value aliases and cyclic payloads escaped guards; generated identities and order geometry could drift; and dependency/HDF exceptions could truncate the eleven-stage denominator.
2. **The repaired adapter is broker-inert within the claimed synthetic scope.** Its AST/transitive closure is exactly five local pure modules. Static audit found zero broker/live, filesystem, network, subprocess, dynamic-import, writer, or executable-order paths. A fresh-import trap found zero write, network, subprocess, or dynamic-import effects. Safety remains conditional on caller-supplied dependencies actually being broker-inert; this lane does not certify arbitrary injected code.
3. **The downstream source domain is structurally sound but insufficient.** All eleven commissioned payloads match exact byte counts and SHA-256 values. Across January, April, and May there are 73,999 pool rows and 73,999 sidecar rows, 73,999 unique native identities on `(candidate_id, symbol, side, decision_time_utc)`, zero duplicate native rows, zero unmatched rows, and zero multiplicity mismatches.
4. **`candidate_id` alone is not an identity.** January has 967 reused IDs covering 6,745 rows; April 746 covering 5,901; May 644 covering 4,560. The four-part identity is mandatory.
5. **The sidecars are M1 observations only.** All 73,999 sidecar rows declare `M1`; the 8,663,386 ordered observations contain only `time_utc/open/high/low/close`. Neither the sidecars nor source manifests contain closed-M15 generator windows, `M15.atr_14`, `H1.breaker_blocks`, or an inert route bundle.
6. **The January boundary discrepancy is real but does not admit January 31.** Its manifest declares `2026-01-01..2026-01-31`; the commission is `2026-01-01..2026-01-30`; observed rows are `2026-01-02..2026-01-30`; rows outside the commissioned boundary are zero. The repaired adapter now refuses January 31 before dependency invocation.

| Window | Pool/sidecar rows | Unique native IDs | Duplicate / unmatched | Observed dates | Declared vs commissioned |
|---|---:|---:|---:|---|---|
| January | 27,658 / 27,658 | 27,658 | 0 / 0 | Jan 2–30, 21 dates | Jan 1–31 vs Jan 1–30 |
| April | 25,056 / 25,056 | 25,056 | 0 / 0 | Apr 1–30, 20 dates | exact |
| May | 21,285 / 21,285 | 21,285 | 0 / 0 | May 5–29, 18 dates | exact |

No return, cost, outcome, promotion, or economic value was aggregated or allowed to choose an inventory branch.

## Missing-source counterexamples tested

- The three current-breaker repair trade ledgers map 11,305 original identities into the admitted domain, but leave 62,694 admitted identities uncovered and contain only downstream transform provenance—not M15 bars or contemporaneous MSO state.
- The 24 tracked `data/historical_2026/*_M15.csv` files all declare broker-server-local time, not true UTC, and have no composite-identity/MSO/route bundle. Another 54 tracked M15 CSVs have only 10 timebase sidecars (all broker-local variants); 44 have no declared timebase.
- The strongest named counterexample, LFS object `shadow_logs/candidate_mso_snapshot_joins.jsonl` (`c37bfb37…`, 250,146 bytes), has 66 rows and 60 complete four-part identities, but **zero** identity intersection with the admitted 73,999-row domain. It contains neither `atr_14` nor `breaker_blocks` and has no route bundle.
- The preserved January materialization bundle is hash-bound raw OHLCV for one selected day across 24 symbols. Its metadata contains no admitted candidate identity, `atr_14`, `breaker_blocks`, or route parameter.
- A bounded safe-name scan covered 116 current/preserved Hermes metadata files and 347 phase18/19/20 metadata copies across 26 worktrees. The nine unique token-hit paths were protocols, completions, preregistration, or HL/HK requirement evidence—not a payload satisfying the full conjunction.

One committed M15 timebase sidecar contained a textual March clock-evidence reference during metadata classification. No March path or outcome payload was opened, decoded, aggregated, or used. No live-forward outcome value was aggregated or used.

The exact prerequisite remains:

> Capture, for every admitted four-part identity, a SHA-256-bound true-UTC predecision bundle containing at least 51 closed M15 bars, contemporaneous `M15.atr_14`, the contemporaneous H1 breaker-block collection and its formation/mitigation/retest fields, plus the inert route parameters needed to reproduce the fixed current-breaker opportunity.

## Bounded repairs

- Only literal `True` can leave default-off.
- Permission container shape, account-headroom numerics, hashes, source-window aliases, exact commissioned dates, and true-UTC timestamps fail closed before readers/dependencies.
- Source and dependency inputs are detached; scheduler mutation is refused; learned authority keys are normalized across snake/camel/hyphen aliases; cyclic payloads fail closed.
- Generated and routed candidate identities cannot change candidate, symbol, side, or decision time; the fixed current-breaker family is enforced before transform.
- Market/limit preimages reject booleans, nonfinite/nonpositive prices, side/direction conflicts, and directionally invalid geometry; owner volume remains `NOT_EVALUABLE_OWNER_INPUT_REQUIRED` for both accounts.
- Dependency and malformed-HDF exceptions become exact first-miss rows. Eleven stages remain present exactly once per composite identity, including when one identity fails and another completes.

No route module, HDE/HDF authority, config, root-cause map, session register, or alternate candidate was changed.

## Verification

- Exact test-byte A/B: **40 bad → 0 bad; 40 fixed; 0 regressed**.
- HM focused module: **70 passed**.
- HL focused module: **30 passed**.
- Combined focused invocation: **100 passed**.
- Changed Python compiled; every changed JSON parsed; exactly one self-contained `gtos-ab-receipt-v1` fence validated; `git diff --check` passed; complete source and evidence diffs inspected.
- The repository-wide suite was not run and was not required by this adapter-local repair.

The only pytest diagnostic was the pre-existing warning for unknown config option `asyncio_mode`.

## Authority and lineage

- HK evidence closeout `11594419a197e278263565ac7677ecfc3e317c31` has sole parent `a1cf205de52a7f279932e4436196a255ae5e7b9b`.
- HL evidence closeout `5c94d2caa8c0764fccd6fc8dc1f353a83d6ef094` has sole parent `41534770fa338f12b34d79c9625fd406219a41fe`.
- Tested HM source `1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51` has sole parent `41534770fa338f12b34d79c9625fd406219a41fe`.
- Neither evidence closeout was merged, rebased, or flattened into implementation ancestry.
- The completion receipt names `1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51`—not the evidence closeout—as the exact source parent for final readiness synthesis.

No P1, replay, paper shadow, canary, calibration, economic gate, broker/VPS/runtime contact, MetaTrader import, order path, config mutation, merge, or push occurred.

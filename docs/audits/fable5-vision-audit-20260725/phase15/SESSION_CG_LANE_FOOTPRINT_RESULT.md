# Session CG — lane footprint and floor result

Session: CG · Wave 15 · Blocks B2400–B2449  
Branch: `phase15/lane-footprint`  
Evidence surface: January 2026 training-lane measurements only; never admission-grade

## 0. Findings first

1. **The accepted lane floor is 480.429 s and 2.896 GB peak RSS.** CG's own
   unpatched frozen January 1–2 S1R1 baseline was 646.830 s / 7.719 GB. The lean
   default is therefore **1.3464x faster** and uses **0.3752x** the peak RSS. The
   zero-tolerance comparator returned `OUTCOME_IDENTICAL`: 8,812 candidates,
   8,807 missed opportunities, 10 orders, 5 trades and 96 scorecards. B2409.

2. **The transformed full-January storage floor is 1,918,361,600 allocated
   bytes per arm.** Against 61,722,038,272 actually free bytes, the disk-only
   ceiling is **32 arms hard / 31 operational** with one full-arm slot reserved.
   The pre-cut full arm was 17.041 GB logical, so the five-stage waterfall removes
   88.74 %. B2411.

3. **CD's missed-pool projection was not reader-complete.** It preserved the
   three headline aggregates but omitted canonical identity and outcome fields,
   making AW's mine refuse the first scoreable row. CG replaced `FEATURE_FIELDS`
   as the schema source with the actual reader chain and retained every literal
   matrix/bench read plus repair provenance. B2400–B2401.

4. **The semantic sidecar has zero row-field readers in the training lane.** Its
   three files now retain one disclosure-only stamp row per input row. In the
   full-January authority they shrink from 835,201,230 to 11,743,976 bytes. New
   readers must extend the explicit registry before the cut can remain default-on.
   B2401 and B2411.

5. **The resident sink removes the disk serialize/decode round trip without
   weakening append-time snapshot semantics.** It deep-copies at append and at
   iteration, creates an empty transport directory, cannot be reopened, and is
   explicitly non-authorizing. The accepted fixture recorded 13,415 snapshotted
   rows, 26,830 iterations, and zero JSON encodes/decodes inside the sink. B2402.

6. **The dirty memos were repaired for correctness, but none earned operational
   promotion.** Selector, timewarp and attribution produced 157,372 / 146,776 /
   104,366 verified hits with zero mismatches; probability produced **zero exact
   hits**. Promoting the three exact keys made the default exceed the complete
   frozen baseline by 1.77x before final serialization, so CG reversed the
   promotion. Correctness evidence is retained; the performance default is lean.
   B2403, B2406 and B2408.

7. **The residual floor is no longer the sink.** The accepted profile's largest
   self node is `probability_debate_v4._stable_sha256` at 45.937 s / 9.51 %.
   The largest economic cumulative chain is
   `finalize_scheduler_risk_admitted_selection` at 133.384 s / 27.62 %; attribution
   fields account for 96.357 s / 19.95 %. B2410.

## 1. Accepted wall and memory floor

| measurement | frozen own baseline | lean lane | result |
|---|---:|---:|---:|
| wall | 646.830 s | **480.429 s** | **1.3464x** |
| day-2 economic hot path | 525.570 s | **427.323 s** | **1.2299x** |
| peak RSS | 7,718,649,856 B | **2,895,904,768 B** | **0.3752x** |
| candidate rows | 8,812 | 8,812 | identical |
| missed rows | 8,807 | 8,807 | identical |
| orders / trades / scorecards | 10 / 5 / 96 | 10 / 5 / 96 | identical |

The candidate used the operational default, not an explicit experimental patch
list:

```text
authority_hash_content_memo
abc_concrete_types                 # Mapping, MutableMapping only
skip_post_hoc_ledger_recertification
gc_during_chunk
ultimate_packet_hash_content_memo
train_resident_event_sink
ledger_scalar_projection
missed_pool_projection
semantic_sidecar_projection
```

`CG_ACCEPTANCE_V1.json` is the result gate. It compares trade and order identity
at float tolerance 0.0 and separately checks the missed-pool diagnostic aggregate;
it has no refusals. This remains a bounded engineering fixture, never a sealed arm
of record.

## 2. Storage waterfall

### 2.1 CG's own January 1–2 fixture

| stage | logical bytes | delta | ratio to prior |
|---|---:|---:|---:|
| frozen namespace | 931,878,143 | — | — |
| scalar decision + scorecard | 549,058,950 | -382,819,193 | 0.5892 |
| reader-complete missed v2 | 202,844,952 | -346,213,998 | 0.3694 |
| semantic sidecar | 154,377,093 | -48,467,859 | 0.7611 |
| resident sink | **131,144,915** | -23,232,178 | 0.8495 |
| observed accepted output | **131,118,412** | -26,503 vs floor | — |

The offline waterfall is conservative by 26,503 bytes because it substitutes
only cut-addressable payloads while retaining baseline metadata. The candidate's
three semantic files occupy 670,396 logical bytes; its transport directory has no
files.

### 2.2 Full-January S1R1 storage geometry

| stage | logical bytes | allocated bytes | logical delta |
|---|---:|---:|---:|
| frozen namespace before cold demotion | 17,040,536,690 | 17,055,985,664 | — |
| scalar decision + scorecard | 9,393,115,753 | 9,400,958,976 | -7,647,420,937 |
| reader-complete missed v2 | 3,195,816,909 | 3,195,969,536 | -6,197,298,844 |
| semantic sidecar | 2,372,359,655 | 2,372,513,792 | -823,457,254 |
| resident sink | **1,918,329,482** | **1,918,361,600** | -454,030,173 |

The month reference is the frozen accepted January S1R1 arm's verified cold
preimages plus its separately preserved compact-event authority. It is an exact
storage transformation, not a new economic replay and not CD's repaired book.
The compact authority supplies 69,888 decision and 154,316 missed rows. It
predates scorecard retention, so the instrument failed closed at 0 versus 2,016,
then streamed the verified scorecard cold archive instead. All three projected
role counts must equal their cold manifests.

At receipt time:

```text
free bytes                              61,722,038,272
full-arm planning allocation             1,918,361,600
hard arithmetic count      floor(free / arm) = 32
operational count, one arm reserved             31
```

This is strictly a disk ceiling. It is not permission to run 31 concurrent arms;
CPU, RSS, source I/O and orchestration remain independent constraints.

## 3. Reader contracts behind the projections

The missed-pool keep set is derived from consumers, not from a convenient feature
list. The registry at `src/research_infra/train_engine/cuts.py:833` enumerates:

- `aw_separability_mine.load_frame -> b7_5_diagnostic_pool.iter_arm_rows/project`,
  including `PROJECTION + OUTCOME_PROJECTION`;
- `analyze_b7_5_selection_sizing_matrix.update_missed`;
- `fast_engine.bench._missed_digest`; and
- commission/swap repair provenance needed to distinguish generators.

That repaired CD's omission of
`canonical_replay_candidate_instance_key`, `opportunity_gross_r`,
`terminal_outcome`, `counterfactual_order_close_time_utc`, and
`missed_opportunity_headline_r_scoreable`.

The semantic registry at `cuts.py:913` enumerates three consumers and zero fields:

- attempt-5 consumes only `append_jsonl`'s returned row count;
- `fast_engine.bench.extract_economics` does not open the namespace; and
- AW reads the missed ledger, not the semantic sidecar.

Every projection is lane-default, stamped on-row, and declares
`sealed_compatible=False`. An unrecognized file is written whole rather than
silently projected.

## 4. Resident sink contract

`TrainResidentEventSink` is a subclass beside the frozen sink, not an edit to it
(`resident_event_sink.py:64`). Its identity boundary is:

- append: deep snapshot of the complete projected row (`:85–101`);
- seal: exact role-count equality, zero encode/decode counters, non-reopenable and
  non-authorizing authority (`:103–148`);
- iterate: ordinal check and a fresh deep copy (`:150–162`); and
- patch: rebind only attempt-5's constructor, default-on only in the training lane
  (`:173–206`).

The deep copies are necessary. The frozen `json.dumps` captured a nested row at
append time and `json.loads` isolated each reader; a shallow dict copy would change
both behaviors when producers or consumers mutate nested values.

## 5. Memo verdicts

| patch | calls | exact hits | verified | mismatches | operational verdict |
|---|---:|---:|---:|---:|---|
| selector hash v2 | 191,840 | 157,372 | 157,372 | **0** | off: key net-negative |
| timewarp hash v2 | 218,125 | 146,776 | 146,776 | **0** | off: key net-negative |
| probability hash v2 | 17,624 | **0** | 0 | 0 | off: no reusable work |
| attribution fields v2 | 304,457 | 104,366 | 104,366 | **0** | off: key net-negative |
| packet hash split | 17,442 | 8,628 | 8,628 | **0** | on: H-CB-2 clean |

The verifier also measured Mapping 450,424,713 / 0 and MutableMapping 187,611 / 0.
`Sequence` is absent from the rebind because H-CB-2 measured 47,444,764 wrong
string checks there. The v2 memo implementations remain registered for future
schema-aware refinement and receipt reproduction; `TRAIN_SAFE_SET_PATCHES` at
`cuts.py:1110` contains none of them.

The rejected default-path run was intentionally stopped at final scorecard
serialization after 1,146.429 s / 3,036,102,656 B: already 1.77x the complete
baseline. It is an error report, not an acceptance receipt.

## 6. Residual map

The profile completed in 482.886 s / 2,976,645,120 B and independently passed the
same outcome comparator. Top self-time:

| node | seconds | wall share |
|---|---:|---:|
| probability `_stable_sha256` | 45.937 | 9.51 % |
| thread wait | 25.571 | 5.30 % |
| JSON encoder `iterencode` | 24.602 | 5.09 % |
| timewarp `_stable_sha256_uncached` | 23.671 | 4.90 % |
| `cleaned` | 15.350 | 3.18 % |
| CB `_content_key` | 14.324 | 2.97 % |
| fillability claim | 13.811 | 2.86 % |
| final JSONL append | 12.216 | 2.53 % |

Top cumulative economic chains:

| chain | seconds | wall share |
|---|---:|---:|
| final scheduler-risk admitted selection | 133.384 | 27.62 % |
| execution-fillability aliases | 109.750 | 22.73 % |
| authority attribution fields | 96.357 | 19.95 % |
| signed-envelope failures | 86.307 | 17.87 % |
| batched proof-hash evaluation | 79.791 | 16.52 % |

Probability hashing has no exact repeat content, so its next lever is a proven
serializer/hash replacement or removal of redundant proof construction—not a
memo. Selector/timewarp need a cheap collision-refining key derived from their
actual mutation paths; another generic full-tree key repeats CG's mistake.

## 7. Verification and receipts

| receipt | claim |
|---|---|
| `receipts/CG_VERIFY_ACCEPTANCE_V1.json` | zero-tolerance outcome identity plus per-call memo/ABC verification |
| `receipts/CG_ACCEPTANCE_V1.json` | accepted unprofiled 480.429 s / 2.896 GB lean floor |
| `receipts/CG_PROFILED_ACCEPTANCE_V1.json` | accepted residual profile, 25,418 samples |
| `receipts/CG_LANE_FOOTPRINT_V1.json` | bounded/full-month waterfalls and live disk ceiling |
| `receipts/SESSION_CG_AB.md` | scoped copy-back A/B against ZERO baseline |

Focused implementation suite: **65 passed** across cuts, resident sink, footprint,
and block-citation enforcement. The scoped A/B is recorded in the final receipt
above; new test files are counted separately because they do not exist at the
before tree.

## 8. What I got wrong

1. **I initially trusted CD's `FEATURE_FIELDS` derivation.** Inspecting the actual
   AW chain showed that it deliberately excluded identity and outcome families;
   the projected month was not mineable. I changed the schema source to readers.

2. **I assumed `LANE_ITERATION` existed on this branch.** The first command was
   refused by argparse before a run began. All evidence runs use the supported
   `ACCEPTANCE_REPRODUCTION` purpose and retain the training-only disclosure.

3. **I treated the first baseline process as mine alone.** CD's broad cleanup
   killed it at 44 KB of preflight output. I did not reuse the partial namespace;
   the successful baseline has a fresh `CG_BASELINE_R2_*` prefix.

4. **My first exact key retained whole recursively frozen payload trees in a
   16,384-entry LRU.** That would have spent the resident sink's memory saving.
   I reduced stored keys to fixed SHA-256 digests before the verifier.

5. **I inherited `Sequence` as supposedly safe.** H-CB-2's per-call receipt—not
   outcome identity—showed 47,444,764 mismatches, all strings. I stopped the first
   verifier after 67 s, removed `Sequence`, and reran under a clean namespace.

6. **I promoted three exact memos after the correctness verifier.** That confused
   semantic safety with usefulness. The default-path floor crossed 1,146.4 s
   before it completed, so I reversed the promotion and measured the lean floor.

7. **I expected probability's repaired key to recover useful hits.** It recovered
   zero. The old memo's 8,810 hits were all collisions; there is no repeated exact
   content to cache on this fixture.

8. **I expected CD's harvested full-month directories to remain available.** CD
   removed them after extracting its result. I replaced an unreproducible `du`
   recollection with the frozen January cold manifests plus compact authority.

9. **I assumed the old compact authority retained scorecards.** The instrument
   refused 0 compact rows versus 2,016 cold-manifest rows. I added a verified-cold
   fallback for an absent role and kept the exact count check.

10. **My first synthetic footprint row was too small.** A disclosure stamp can be
    larger than a toy input. The test now uses realistic nested payloads and
    asserts the complete waterfall; the fixed per-row stamp overhead remains
    visible rather than wished away.

11. **I made the exact-key unit test promise insertion-order-independent hits.**
    The key's fixed-size digest pickles a recursively frozen form; equal
    frozensets are semantically equal but their pickle byte order is not a
    canonical map encoding. That can safely lose a hit and cannot serve stale
    content. The final suite exposed the assertion as nondeterministic. The test
    now requires reuse for stable producer order and nested-mutation invalidation,
    which is the actual contract; the already net-negative patches remain off.

## 9. Handoff

- Merge the scoped commits; no R2-bound path, live config, profile, VPS or broker
  surface was changed.
- Treat **1.918 GB allocated** as the current full-January disk planning number,
  and **31** only as a disk-only operational ceiling.
- Keep the three v2 exact memos default-off. For selector/timewarp, inspect the
  specific nested mutation paths behind H-CB-2's collisions before proposing a
  cheaper key. For probability, pursue serializer/proof elimination instead.
- The 19.95 % attribution chain is the next structural CPU target. Prefer removing
  repeated field construction/validation over another generic content memo.
- The full-month number is storage geometry from frozen January S1R1. A future
  lean full-month runtime/RSS run would answer duration scaling; CG did not claim
  it from the two-day fixture.
- Any new semantic-sidecar or missed-pool consumer must be added to the reader
  registries before projections remain default-on.
- The generated CG baseline/candidate/profile/verifier namespaces are deliberately
  untracked and retained for receipt reproducibility. They are not arm-of-record
  evidence and can be cleaned after integration decides they are no longer needed.
- March 2026 remained outcome-unread throughout. No broker-capable script ran and
  the VPS was never touched.

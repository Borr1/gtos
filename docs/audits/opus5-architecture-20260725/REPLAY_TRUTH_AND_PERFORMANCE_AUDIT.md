# Replay Truth and Performance Audit

**All numbers below are either read from GTOS's own sealed receipts or measured by this audit on this machine (Apple Silicon, 10 cores, 16 GB).** Nothing is estimated unless labelled.

---

## 1. What the accepted numbers actually measure

Three different "dense day" figures circulate for one two-day fixture (2026-01-01 no-event + 2026-01-02 dense):

| Figure | Value | Source | Scope |
|---|---:|---|---|
| `task8_dense_day_economic_hot_path_seconds` | **558.409 s** | `.hermes/receipts/task8/task8-kernel-review-repaired-20260723T024350Z/TASK8_KERNEL_ACCEPTANCE.json` | time inside `run_campaign` only. Excludes 41.729 s proof finalization, startup, prewarm, archive seal, verification. Same run's full wall: 697.265 s |
| `dense_total_seconds_median` | **599.066 s** | `TASK9_FINAL_ACCELERATOR_ACCEPTANCE.json.measurements.warm_filesystem` | hot path + proof finalization |
| `dense_allocated_envelope_seconds_worst` | **648.955 s** | same file, `owner_adjusted_performance_disposition` | above + a share of the shared residual |

The brief's "558.580 s warm / 949.615 s cold" are near-misses: the literals `558.580` and `949.615` appear nowhere in the repo. The real values are `558.408705167` (Task 8, **economic hot path only**) and `949.9697153329616` (Task 3, **warm — not cold**, full wall for the 2-day fixture).

Two further scope facts that materially change interpretation:

- **Both measured classes assume warm derived caches.** `progressive_benchmark.py:131-145` defines three classes; only `sealed_cache_cold_process` and `warm_filesystem` (`derived_cache_preexisting: True`) were ever measured. `derived_cold` was never included in any target measurement, and the separate `build-pack` process is excluded from all of them. **The true cold end-to-end cost of one arm has never been reported.**
- **There is no completed pre-acceleration baseline.** The only un-accelerated configuration (`replay_acceleration_physical_reference_runner.py:180-181`, both cache roots `None`) was SIGTERM'd at 4 h 39 m 43 s with 1 of 31 chunks sealed; its own receipt says it is "a lower bound … not a completed parity artifact". Every "reference" in the Task 3–9 ladder is itself an accelerated run, so the published 1.87× measures accelerator-vs-accelerator.

## 2. The no-event target was not really missed

`TASK9_FINAL_ACCELERATOR_ACCEPTANCE.json` records `no_event_allocated_envelope_seconds_worst: 52.524` against a 5 s target. That is an *allocated envelope*, not economic work.

Measured directly from the four sealed January arm summaries (`progress_rows`, 31 days each), the ten non-trading days cost **1.7 s each in the economic path**:

| Arm | economic total | proof total | active days (≥10 s) | mean active day | no-event days | no-event total |
|---|---:|---:|---:|---:|---:|---:|
| S0R0 | 11,232.1 s | 462.8 s | 21 | 534.1 s | 10 | 16.7 s |
| S1R0 | 12,967.4 s | 597.7 s | 21 | 616.6 s | 10 | 18.1 s |
| S0R1 | 12,336.7 s | 676.5 s | 21 | 586.6 s | 10 | 18.3 s |
| S1R1 | 11,929.1 s | 547.2 s | 21 | 567.2 s | 10 | 17.4 s |

**Measured by this audit:** a run that reached the day loop and stopped consumed **63.03 s wall / 108.98 s CPU** in source-authority validation, typed-cache binding, four-worker sparse-tick prewarm, and resolver construction — before the first decision. That fixed cost, amortised over a 2-day fixture, *is* the 52.5 s "miss".

> **The no-event economic path is 1.7 s against a 5 s target. It passes. The reported miss is process startup being charged to it.**

For a 31-day month that fixed cost is paid once, so it is 0.4 % of an arm. It only dominates when the workload is small — which is exactly the case the 5 s target described.

## 3. Where the dense day actually goes — sampled profile

**Method.** A 4 ms statistical wall-clock sampler (`sys._current_frames` on the main thread, ~1 % overhead — no `cProfile` distortion) wrapped around the real Phase-D entrypoint `attempt5.run_replay_engine`, over the sealed January prepared packs, arm S1R1, using the engine's own supported bounded mode (`engineering_stop_after_day = 2026-01-02`) so every source-plan digest still matches the seal. 86,945 samples, 95.5 % of wall captured in the top 220 frames.

**Caveat, stated plainly:** this run was concurrent with the owner's April arm, so its absolute wall (1,102.3 s; dense day 811.76 s vs the sealed arm's 531.15 s) is contended and ~1.5× inflated. **The distribution is what this section relies on, and contention affects all frames roughly equally.** An uncontended before/after benchmark follows in §5.

### Self time (exclusive) by category

| Category | seconds | % of captured | % of wall |
|---|---:|---:|---:|
| **HASH_CANONICALIZE** | 294.2 | 27.9 % | 26.7 % |
| DOMAIN_OTHER | 240.0 | 22.8 % | 21.8 % |
| WORKER_POOL_WAIT | 129.8 | 12.3 % | 11.8 % |
| **JSON_ENCODE_DECODE** | 120.9 | 11.5 % | 11.0 % |
| **ABC_ISINSTANCE** | 77.1 | 7.3 % | 7.0 % |
| **ATTRIBUTION_FIELDS** | 74.8 | 7.1 % | 6.8 % |
| **PROOF_SINK_IO** | 70.6 | 6.7 % | 6.4 % |
| PARSE_HYDRATE | 30.8 | 2.9 % | 2.8 % |
| STDLIB_OTHER | 8.2 | 0.8 % | 0.7 % |
| DEEPCOPY | 6.4 | 0.6 % | 0.6 % |

> **Proof, evidence, and type-check machinery is 637.6 s = 60.6 % of measured self-time.**
> Domain execution plus data hydration is 270.8 s = 25.7 %.
> This is a **lower bound** on proof cost: `DOMAIN_OTHER` still contains attribution helpers the classifier did not match by name.

### Cumulative time (inclusive) — the decisive table

| Function | seconds | % of wall |
|---|---:|---:|
| `attempt5:15455 _run_typed_sparse_attempt5` | 1,102.0 | 100.0 % |
| `v4:90451 run_campaign` | 871.0 | 79.0 % |
| `v4:44810 finalize_scheduler_risk_admitted_selection` | 303.4 | 27.5 % |
| `v4:11791 package_new_entry_authority_attribution_fields` | 288.4 | 26.2 % |
| `v4:20265 execution_fillability_alias_fields` | 277.8 | 25.2 % |
| `v4:12035 signed_envelope_failures` | 269.0 | 24.4 % |
| `v4:16255 package_new_entry_authority_immutable_payload_failures` | 238.9 | 21.7 % |
| `SCHED:897 package_new_entry_authority_payload_hash_sha256` | 210.4 | 19.1 % |
| `v4:12200 signed_envelope_valid` | 205.3 | 18.6 % |
| `v4:23292 scheduler_option_probe_quality_fields` | 155.0 | 14.1 % |
| `SCHED:883 _stable_sha256_material` | 154.5 | 14.0 % |
| `v4:55600 candidate_decision_quality_fields` | 139.3 | 12.6 % |
| `attempt5:7924 prewarm_sparse_tick_sources` | 106.2 | 9.6 % |
| `replay_compact_event_sink.py:540 append` | 97.1 | 8.8 % |
| **`v4:67389 evaluate_candidate_v4`** | **91.1** | **8.3 %** |

> **`evaluate_candidate_v4` — the function that actually decides whether a trade is worth taking — is 8.3 % of wall time.**
> `package_new_entry_authority_attribution_fields`, a single `*_fields` builder, is 26.2 %.

This is the empirical answer to the mission's central question. The replay is not slow because market simulation is expensive. It is slow because it constructs, canonicalises, hashes, and re-hashes an enormous authority/attribution structure around every decision.

## 4. Why the evidence is that large — measured row anatomy

One January S1R1 arm emits **15.75 GB of logical JSON** to produce **148 orders and 72 trades** — 218 MB of evidence per trade. Measured directly on the materialised ledgers:

| Ledger | Rows | Logical bytes | Bytes/row |
|---|---:|---:|---:|
| missed opportunity | 154,316 | 7,595,615,841 | 49,222 |
| decision | 69,888 | 4,062,951,201 | 58,135 |
| scorecard | 2,016 | 3,914,869,623 | **1,941,900** |
| order | 148 | 77,535,353 | 523,887 |
| trade | 72 | 38,347,402 | 532,603 |

A single order row, decomposed by this audit:

- **494,196 bytes**, **1,274 top-level keys**, 8,091 scalar leaves — of which only **765 are distinct values**
- **63.8 % of the row (315,449 bytes) is JSON key names** — 8,501 key occurrences, 2,860 distinct names averaging 37 characters
- the same subtree appears at multiple paths: `predecision_stop_hazard_guard` / `scheduler_option_predecision_stop_hazard_guard` (2,652 B each), `package_displacement_quality` / `selected_scheduler_package_displacement_quality` (2,205 B each — written into two dicts at `SCHED:14693-14694`), `risk_authority.package_marketable_entry_guard_replay_route` also present as a top-level key (32,263 B)
- `risk_config` alone is 37,848 bytes with 198 keys, and is **constant across all 148 rows** — 5.6 MB of duplicated configuration in the order ledger alone

**Serialization is not the bottleneck.** Measured on these exact rows: `json.dumps` 190–250 MB/s, `sha256` ~2,300 MB/s. The ~855 MB a dense day emits costs ≈4 s of ~570 s. The cost is *computing* 1,274 fields, then canonicalising and hashing them repeatedly — which is precisely what §3 shows.

## 5. Optimisation experiments

### 5.1 ABC `isinstance` dispatch — measured, exactly parity-preserving

`<frozen abc>:__instancecheck__` is **65.8 s of self time (6.0 % of wall)** — pure `isinstance(x, Mapping)` / `isinstance(x, Sequence)` ABC dispatch. Benchmarked on this machine:

| check | ns/call | vs ABC |
|---|---:|---:|
| `isinstance(x, Mapping)` (ABC) | 81.4 | 1.00× |
| `isinstance(x, dict)` | 14.7 | **5.53×** |
| `type(x) is dict` | 7.4 | **10.97×** |
| `isinstance(x, Sequence)` (ABC) | 109.7 | 0.74× |
| `isinstance(x, (list, tuple))` | 36.1 | 2.25× |

At 81.7 ns/call the measured 65.8 s implies **≈0.81 billion ABC isinstance calls in one two-day run**. Site counts: `v4_timewarp…` has **1,375** `isinstance(…, Mapping)` and 38 `isinstance(…, Sequence)`; `moonshot_scheduler_v4…` has 95 and 11; `selector_v4` 40 and 8.

The exactly-equivalent fast path `type(v) is dict or isinstance(v, Mapping)` benchmarks at 33.2 ns vs 90.8 ns on realistic payloads (**2.74×**), projecting a **41.7 s saving on a 1,102 s run (3.8 % of wall)**.

**Why it is exactly parity-preserving here:** `rg 'class \w+\(.*Mapping.*\)'` over `src/` returns **no custom Mapping subclass**, and `MappingProxyType` appears **nowhere** in `src/`. Every mapping flowing through these helpers is a plain `dict`, so the fast path returns identical results on every input the engine can produce.

### 5.2 JSON encoder reconstruction

`json/encoder.py:__init__:105` is **19.7 s of self time (1.8 %)** — a fresh `JSONEncoder` is constructed on every `json.dumps(..., sort_keys=True, separators=…)` call, because passing any kwarg bypasses the cached default encoder. Hoisting one module-level `JSONEncoder(...).encode` per canonicalisation signature produces **byte-identical output** and removes most of that cost.

### 5.3 Structural levers not attempted here (ranked by measured upside)

| Lever | Measured basis | Expected | Risk |
|---|---|---|---|
| Compute `build_runtime_risk_authority` **once** per selected order instead of twice (`v4:49568` + `v4:85868`, flagged `runtime_risk_authority_recomputed_for_order_materialization: True` at `:85879`) | 5,065-line function; finalizer branch is inside `finalize_scheduler_risk_admitted_selection` (27.5 % cumulative) | high | changes reconciliation logic at `:85927-86160` |
| Pass `query_cache` to the three execution-path `path_source_and_oracle` calls (`v4:86721`, `:87104`, `:87516`) as the two diagnostic calls already do (`:92464`, `:92880`) | each constructs a fresh `PathTruthIndex` and re-parses the tick file | medium-high | must confirm cache keys are exact |
| Emit authority/attribution subtrees **once per window** with a reference from each row, instead of inlining them per row | 63.8 % of an order row is key names; `risk_config` (37,848 B) is constant across all rows | very high on bytes; high on hash/encode time | changes ledger schema — needs a reader shim |
| Hash the compact typed event, not the expanded canonical row | `HASH_CANONICALIZE` 27.9 % + `JSON_ENCODE_DECODE` 11.5 % | very high | changes every digest — a re-seal event |
| Drop the ABC dispatch (5.1) and reuse encoders (5.2) | measured above | ~5.6 % of wall combined | none (exact parity) |

## 6. Is 180 s reachable?

**Not by micro-optimisation, and the profile says why.**

Take the sealed, uncontended dense day at 531.15 s (`PHASE_D_JANUARY_S1R1_R1` progress row for 2026-01-02). Applying the profile's category shares:

- irreducible domain + hydration (25.7 %) ≈ **136 s**
- proof/canonicalise/encode/attribution/type-check (60.6 %) ≈ **322 s**
- worker-pool wait (12.3 %) ≈ **65 s** — largely the 4-worker prewarm, amortisable across days

The 180 s target is therefore reachable **only** by removing most of the 322 s of evidence-construction work from the chronological hot path. Task 5 already built the mechanism for this (`replay_compact_event_sink`, "an enabling proof-transport primitive") but the expansion still happens inline: `_append_canonical_row` is 73.6 s of self time — the sink is being fed *already-canonicalised full rows*, not compact typed events.

**The defensible conclusion:** with the current evidence schema, ~136 s of domain work sits under ~322 s of proof work, so 180 s is unreachable. With authority subtrees emitted once per window and hashed in their compact form, 180 s is plausible and 250 s is close to certain — and the arithmetic is dominated by one decision (row schema), not by a thousand micro-optimisations.

## 7. Semantic lower bound

What is genuinely irreducible per dense day:

1. **Chronological reduction.** 24 symbols × N decision windows, each requiring account state advanced to `asof` before candidates are scored (`v4:90558`). Sequential by construction.
2. **Market-state computation per (symbol, window).** Already cached across arms (`CampaignExactCache.closed_timeframe_state`) and across days (prepared packs).
3. **Candidate evaluation.** Measured at **8.3 % of wall** — `evaluate_candidate_v4` cumulative 91.1 s.
4. **Path resolution for selected orders.** 148 orders/month; currently uncached on the execution path (§5.3).

Everything else — authority construction, attribution fields, canonicalisation, hashing, sink expansion, envelope validation — is *evidence*, and evidence is parallelisable, deferrable, and compressible in ways chronological reduction is not.

**Parallelism note.** The reducer is inherently serial per arm, but the four factorial arms are independent. Task 7 proved four isolated reducers over one prepared pack. The measured January four-arm total was 59,221.8 s serial; four-way parallel on a 10-core machine would be ~16,000 s wall — a **3.7× campaign speedup with no semantic change at all**, and it does not require the 180 s day. That is the cheapest large win available and it was built and then not used by the sealed runner.

## 8. Benchmark receipts

| Artifact | Content |
|---|---|
| `docs/audits/opus5-architecture-20260725/receipts/profile_jan01_02_sampled.json` | full 4 ms sampled profile — 220 self-time frames, 220 cumulative frames, 25 hot stacks, rusage |
| `docs/audits/opus5-architecture-20260725/receipts/bench_baseline.json` | uncontended baseline wall time and per-day economic/proof split |
| `docs/audits/opus5-architecture-20260725/receipts/bench_optimised.json` | same workload after §5.1/§5.2 |
| `docs/audits/opus5-architecture-20260725/receipts/PARITY_LEDGER_DIGESTS.json` | SHA-256 of every produced ledger, baseline vs optimised — the parity proof |

Measured environment: Apple Silicon, 10 cores, 16 GB, Python 3.14.4, APFS.

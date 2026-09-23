# Session G — columnar source layer, measurement receipt

Machine: `Mac16,1`, `hw.memsize` 17,179,869,184 B = **16.000 GiB / 17.18 GB**, 10 CPUs, macOS 26.5.2,
Python 3.14.4. Worktree `worktrees/phase2-columnar-source-20260726`, branch `phase2/columnar-source`.

**Unit calibration, done first.** macOS `ru_maxrss` is in **bytes**, not kilobytes: a 1 GB allocation
moved it by 1,000,554,496. So `profile_day_harness.py:183`'s `/1e9` is correct on this machine and would
be wrong by 1024× on Linux. GTOS's own code agrees explicitly —
`replay_acceleration_resource_architecture.py:312` records `"peak_rss_unit":
"bytes_on_darwin_kib_elsewhere"`.

---

## 1. Contract membership — run before writing a line, as required

R2 (`B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`), 43 bound paths, from this
worktree:

- `drifted=1` — `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`, the known
  regeneration-timestamp artifact the Wave-2 working agreement predicted. **No second drift; nothing
  missing.** Re-checked after all work below: still exactly 1.
- **All three files the plan names as the obvious edit targets are bound** —
  `replay_acceleration_source_batch.py`, `replay_acceleration_integrated_source.py`,
  `replay_acceleration_attempt5_typed_sparse_runner.py` (all `common_behavior_inputs`).
- **Files this session touched: none of them.** Two new unbound modules
  (`replay_columnar_source.py`, `replay_columnar_bridge.py`), one new test file, and documentation.

---

## 2. Where the memory actually goes

`replay_acceleration_integrated_source.py:45` — `_ROW = struct.Struct("<qddddd")` — the typed cache is
**already columnar on disk at 48 bytes/row**. `_load_entry` (`:432-450`) unpacks it into one Python dict
per row via `_row_from_values` (`:144-157`).

Measured with `tracemalloc` on the real `_row_from_values`, 200 k synthetic M1 bars:

| representation | bytes/row | vs on-disk |
|---|---|---|
| on-disk packed `rows.bin` | 48.0 | 1.0× |
| current `tuple[dict[str, Any], ...]` | **474.3** | **9.9×** |
| columnar numpy (6 arrays) | 48.0 | 1.0× |

The duplication the plan targets is real but secondary and **not a fixed 5×**: `load_or_build_partition`
keeps no partition-level memo, so each distinct engine cache key re-reads `rows.bin` and builds an
independent dict set, and both `legacy.rows_by_day:4857` and `select_days:1089` do `dict(row)` — the
`grouped` half of every `(rows, grouped, sha)` triple is a second full copy, not a view.

---

## 3. Partition-boundary A/B — peak RSS, isolated subprocesses

All 192 sealed January typed-cache entries (both normalizer generations), each mode in its own process so
`ru_maxrss` is that mode's own peak. **Conditions: two concurrent `pytest` processes from other
sessions, load average 4.18. Labelled contended.**

| layer | peak RSS | bytes/row | wall |
|---|---|---|---|
| sealed — `tuple[dict, ...]` + `rows_by_day` copy | 2.513 GB | 706.7 | 7.72 s |
| **columnar** | **0.301 GB** | **84.6** | **0.57 s** |
| | **8.4× less** | | **13.5× faster** |

Repeated loads, columnar (proves the store dedupes rather than accumulates):

| multiplicity | partitions held | peak RSS |
|---|---|---|
| 1× | 192 | 0.301 GB |
| 2× | 384 | 0.341 GB |
| 4× | 768 | 0.428 GB |
| 6× | 1152 | 0.514 GB |

**This is a per-representation A/B on identical inputs, not an arm's bar cost.** It materialises every
partition in full, which no arm does — `select_replay_lookback_window` slices to a bounded window.

---

## 4. Row-level identity — exhaustive, not sampled

Every row of the **live** generation of the sealed January typed cache (the 96 partitions whose
`normalizer_code_root_sha256` matches `_normalizer_code_root()` at HEAD; the other 96 are a stale
generation left by an earlier edit to a hashed module):

| check | scope | mismatches |
|---|---|---|
| row dict equality vs `_row_from_values` | 1,777,763 rows | **0** |
| canonical bytes (`json.dumps(sort_keys=True)`) | 1,777,763 rows | **0** |
| `rows_by_day` grouping vs `legacy.rows_by_day` | 96 partitions | **0** |
| sealed `rows_root_sha256` re-derived from columns | 96 partitions | **0** |

Whole sweep: 27.4 s. The probe was proved non-vacuous first (it fails loudly on an empty partition list).

**Substitution boundary**, tested against the real unmodified slicers: `select_replay_lookback_window`
and `select_days` fed a `ColumnarRowSequence` and a `tuple[dict]` produce equal rows, equal grouping,
equal metadata, and equal `stable_sha256` over the returned rows — the value that becomes the source hash
at `integrated_source.py:1076-1078`.

---

## 5. Arm-level before/after — the headline, and it is negative

Two arms, same fixture (S1R1, 2026-01-01..2026-01-02, `--interval-ms 1000`), back-to-back in one quiet
window Borhen granted, `/usr/bin/time -l` on both. **Conditions: three other Claude sessions idled at
Borhen's request; a few of their Python processes remained resident at 200–335 MB each, and system
`mediaanalysisd` was intermittently active. Load average ~1.8 at start. Not a clean room — labelled.**

| | sealed | columnar | delta |
|---|---|---|---|
| `maximum resident set size` | 7,716,159,488 B = **7.716 GB** | 7,985,676,288 B = **7.986 GB** | **+3.5 %** |
| `peak memory footprint` | 14,838,312,240 B = 14.838 GB | 15,102,373,288 B = 15.102 GB | +1.8 % |
| wall | 634.34 s | **577.51 s** | **−9.0 %** |
| instructions retired | 12.004e12 | 11.646e12 | −3.0 % |
| swaps | 0 | 0 | — |
| candidates / orders / trades / scorecard / missed | 8812 / 10 / 5 / 96 / 8807 | **identical** | — |

The bridge was confirmed active in the run log (`[profile_day] columnar source layer INSTALLED`), and
the store was independently verified to serve real partitions at 48.0 B/row.

**Peak RSS did not fall.** The plan's premise — *"kill the copies and the arm fits"* — does not hold.

**Baseline fidelity.** The reproduction matched the audit's fixture exactly on every row count the audit
reported (8,812 candidates, 10 orders, 5 trades). The 7.72 vs 8.61 GB gap is not separated between
residual contention, the R2-vs-R1 contract, and run-to-run variance — GTOS's own TASK9 receipt shows
0.6 GB of spread on identical work (cold median 8.05 GB, warm median 8.66 GB).

**Unit trap, settled by measurement.** One run emitted **both** `maximum resident set size` (7.716 GB)
and `peak memory footprint` (14.838 GB), 1.92× apart. The audit's pair was 8.61 / 15.32, ratio 1.779.
They are two different quantities. The "GiB/GB echo" claim is refuted.

**A defect in this session's own layer, recorded rather than hidden.** `ColumnarPartitionStore` is a
module-global memo with no eviction hook, so it does not release on
`clear_replay_source_caches()` (`attempt5:8670`, `:9758`) and retains ~0.17 GB for the whole run. That
plausibly accounts for most of the +0.27 GB.

**Four-arm demonstration: answered by measurement, deliberately not run.** At ~8 GB/arm *with* the
columnar layer, four concurrent arms need ~32 GB on a 17.18 GB machine — and four arms fitting requires
≤4.29 GB/arm. Running it would have swapped the machine hard with three other sessions live. Four arms
do not fit, before or after this work.

**What the whole source layer could buy**, at measured per-row costs:

| fix | arm peak RSS |
|---|---|
| today, with this layer | 7.99 GB |
| + tick `_day_cache` columnarised | ~6.56 GB |
| + both `v4` index caches | **~6.36 GB** |
| **gate** | **≤3.00 GB** |

Fixing every remaining source-layer copy — all of them in bound files — misses the gate by more than 2×.
~5.5 GB of the peak is outside the source layer and has never been attributed.

---

## 5b. Arm-output identity — the differential harness

Session D's harness, sealed arm vs columnar arm, **positional** alignment (a correction to the session
prompt: the `source` role has no declared identity key, so `alignment="identity"` returns `UNAVAILABLE`
and the run comes back `INCOMPLETE`; positional also asserts row order, which is stronger).

| role | rows | differences |
|---|---|---|
| source | 867 / 867 | 0 |
| decision | 4,608 / 4,608 | 0 |
| bucket | 394 / 394 | 0 |
| order | 10 / 10 | 0 |
| trade | 5 / 5 | 0 |
| oracle | 5 / 5 | 0 |
| scorecard | 96 / 96 | 0 |
| missed | 8,807 / 8,807 | 0 |
| **total** | **14,792** | **0** |

`verdict: EQUIVALENT`, `unknown_difference_count: 0`, `any_truncated: false`, `roles_unavailable: 0`.
Null control (sealed vs itself) `EQUIVALENT`, `same_root: true` — which proves the reader is
deterministic, not that the comparator discriminates.

**The first comparison returned DIFFER, and the fault was mine.** 23,565 differences, all 46 distinct
field paths identity/provenance: `campaign` (13,925), `packet_sidecar_id` (8,923), then `*_hash_sha256`,
`*_id`, `option_id`, `prior_trade_id`. I had put the layer name into `output_prefix`; `campaign` derives
from it and every content-addressed ID hashes a context containing it. Re-running the columnar arm with a
**matched campaign name** produced the table above. The right reading was in the field histogram, not the
verdict.

**Three arm runs:**

| run | peak RSS | peak footprint | wall |
|---|---|---|---|
| sealed baseline | 7.716 GB | 14.838 GB | 634.34 s |
| columnar, own prefix | 7.986 GB | 15.102 GB | 577.51 s |
| columnar, matched prefix | 8.037 GB | 15.231 GB | 578.35 s |

The two columnar runs agree to 0.6 %: the +0.3 GB regression and the −8.9 % wall are both reproducible.

**Unmeasured, and flagged:** the eviction fix landed after these runs, so every columnar number here is
from the bridge that retained ~0.17 GB across chunk boundaries. The fix is proven behaviourally by test;
its arm-level effect is not measured. It should recover most of the +0.3 GB and will not change the
conclusion, which concerns a ~5 GB gap.

---

## 6. Corrections to the inputs of this session

1. **The "15.3 GB is a GiB/GB echo of 8.61 GB" unit trap is refuted.** 15.32 / 8.61 = 1.779. They are the
   two different fields `/usr/bin/time -l` prints — `maximum resident set size` and `peak memory
   footprint` — recorded side by side at `CONTINUATION_BRIEF.md:164`. Four committed `PROCESS_TIME.txt`
   receipts show the two genuinely differing (1.42×, 1.10×). Confirmed live on this machine: the wrapper
   emits both fields as separate byte-valued lines.
2. **8.61 GB is a two-day sub-window, not a month arm.** `receipts/bench_baseline_uncontended.json:829`:
   `day: 2026-01-01`, `end_day: 2026-01-02`, `arm: S1R1`, `wall_seconds: 603.678`. No full-month peak-RSS
   measurement exists on disk.
3. **The layer does not need to read cold evidence.** All 322 `*.jsonl.cold/` directories on this machine
   are output ledgers; there are zero under the typed cache, tick sparse cache, source bundle or
   prepared-pack trees.
4. **`_file_cache` is dead on the sealed path.** `build_sources_for_days:9697` raises on an empty day
   set, so `resolve_file_source:8788` always takes the lookback branch.
5. **The audit's profile harness no longer runs as written** — it pins the R1 contract, which now fails
   closed with `selection_sizing_decision_contract_input_drift:src/research_infra/b7_5_post_acceleration_semantic_verifier.py`
   because P1 fixed that verifier. R2's verification split is exactly the remedy; this session's harness
   copy points at R2 and runs.

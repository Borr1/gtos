# Session CB — the train-grade engine

**Wave 14, blocks B2150–B2199. Branch `phase14/train-engine`.**
Commission: `phase14/SESSION_CB_TRAIN_ENGINE.md`. Owner authority: the
2026-07-31 training-lane ratification (`phase14/TRAINING_LANE_RATIFICATION.md`).

---

## 0. Findings first

**1. Per arm the lane is 1.53×, not 5×. Per four-arm window — the unit the
campaign actually runs — it is 4.98×, measured end to end.** Both numbers are
below; the first is the honest answer to "is the engine five times faster" and
it is **no**, and the second is the honest answer to "can the lane iterate on
history at iteration speed" and it is **yes**. The difference is entirely the
memory result, which is the finding underneath both.

Same machine, same sealed read-only inputs, same 2-day January S1R1 fixture,
own baseline measured this session (never AX's), both sides unprofiled:

| | frozen baseline | train lane | ratio |
|---|---:|---:|---|
| wall | **657.0 s** | **428.8 s** | **1.532×** |
| peak RSS (`ru_maxrss`) | **8.31 GB** | **2.97 GB** | **0.358× — 2.79× smaller** |
| day-2 economic hot path | 525.5 s | 385.2 s | 1.364× |
| **marginal working day** (fixed cost removed) | **628.1 s** | **366.5 s** | **1.714×** |
| row counts | 8,812 / 10 / 5 / 96 / 8,807 | **identical** | — |
| trade-outcome identity | — | **`OUTCOME_IDENTICAL`** | zero tolerance, 14-field tuple |

**Four arms at once — the B7.5 window shape — measured, not modelled:**

| | frozen, serial | train lane, 4-up | ratio |
|---|---:|---:|---|
| wall for a whole four-arm window | 4 × 657.0 = **2,628 s** | **527.6 s** | **4.98×** |
| per-arm slowdown under 4-way contention | — | **1.230×** | |
| combined peak RSS | 8.31 GB (one arm) | **9.14 GB (all four)** | |
| machine swap growth | — | **0** | AX measured +4.39 GB for TWO |

Outcome identity holds under contention too: the 4-up S1R1 arm is
`OUTCOME_IDENTICAL` against the same frozen baseline.

**The marginal-day row is what matters for a month.** A run's fixed cost
(imports, prewarm, source binding) is 28.9 s frozen and 29.3 s train — the cuts
do not touch it. Over a 31-day arm it amortises to nothing. Composing the two
measured ratios, a four-arm month window goes **~16.5 h → ~3.0 h**. That last
figure is an **extrapolation**, and its one assumption is stated: per-arm peak
RSS does not grow materially with window length. The day-boundary heap collapse
supports it (§0 finding 3) and it is unmeasured at month scale — H-CB-5 is the
run that settles it.

**2. The single biggest lever was a key, not a deletion — and it is the lever AX
measured and could not take.** AX proved the authority payload hash is called
52.0 M times on this fixture and that an *identity* memo cannot touch it (0.11 %
hit rate: the caller rebuilds the payload as a new dict every time, so the
repetition is **logical, not referential**). He filed trusting the engine's own
cheap key as H-AX-0 direction 2 — *"a contract-level decision, not an
implementation one."* This lane's acceptance test is trade-outcome identity, so
the decision is the lane's to make, and it was made with a key **stronger than
the engine's own**: every top-level scalar, typed, plus every top-level
container's name/type/length.

**Measured hit rate 84.85 % over 29.1 M calls and the 19.1 % payload-hash node
vanished from the profile entirely.** The engine's own cache could never do this
because it computes the canonical material — the whole expense — *before*
consulting the cache, purely to validate the hit
(`moonshot_scheduler_v4_best_trade_allocator.py:905-912`).

**3. The memory result is larger than the speed result, and it is what kills
H3's parallel-arm ban.** Peak RSS 8.31 → 2.97 GB, from `gc_during_chunk` — AX's
patch, which he built, flagged `sealed_compatible=False`, and could not use
because an R2-bound verifier requires cyclic GC to stay off. **This lane never
runs under R2, so the constraint does not exist here.** The intra-day heap ramp
was largely uncollected cyclic garbage, exactly as AX suspected and could not
test. The run also completes with GC on, which settles a second open question:
nothing on the in-process path asserts the two `automatic_gc_enabled_*`
checkpoint fields — only the R2-bound verifier reads them.

Consequence, measured (§4): AX's H-AX-4b said *"do not run two arms on this
machine to save time"* — 1.224× throughput, +4.39 GB swap, one arm page-starved
at 26.5 % CPU. At 2.97 GB per arm this session measured **1.944× on two** (per-arm
slowdown 1.029×) and **3.251× on four** (slowdown 1.230×), both at **zero swap
growth** and all arms at ~99 % CPU throughout. **H-AX-4b is superseded for this
lane**, with the same instrument and a different footprint. It stands unchanged
for the sealed lane, which cannot take the GC lever.

**4. `gc_during_chunk` costs 33.0 s of FIXED overhead, which nobody would have
found on the two-day fixture.** An empty-day run is 29.3 s without it and 62.3 s
with it — a 2.1× regression on a short window, invisible in the 1.49× headline
because the 2-day run earns it back many times over. **Turn it off for a
one-day iteration; keep it on for anything longer.** It is the reason
`--patches` is a list and not a boolean.

**5. Where the remaining time lives, measured rather than guessed.** After the
cuts, the profile is a completely different shape from AX's — the attribution
subtree fell from 26.2 % to 11.5 % and the payload hash is gone. What is left is
**not** proof machinery that a dial can reach:

| node | share of wall | what it is |
|---|---:|---|
| `replay_compact_event_sink._append_canonical_row` | **12.1 % self / 12.5 % cum** | `json.dumps` of every 1,428-key row — the sink's **storage medium**, not a receipt |
| main thread blocked on an executor (`threading.wait`) | 7.3 % | real work off the sampled thread; both hot modules use Process/ThreadPool executors |
| `json/encoder.iterencode` | 5.7 % | serving the above and the surviving hash misses |
| `probability_debate_v4._stable_sha256` + `_stable_sha256_uncached` | 8.3 % | the 16 % of proof-hash calls that MISS — very large payloads |
| `execution_fillability_alias_fields` / `scheduler_option_probe_quality_fields` | 15.2 % / 14.9 % cum | projections the selection factor reads |
| `evaluate_candidate_v4` | ~14 % cum | **the decision** |
| the memos' own cost | 3.6 % + 9.4 % cum | the price of the cut, paid honestly |

**The next 1.5× is the compact event sink, and it is a fork, not a rebind.**
`ReplayCompactLedger` *is* the sink: rows are JSON-serialised on append and
decoded back on iteration (`iter_rows`, 2.8 %), so the serialisation is storage,
not evidence, and cannot be switched off from outside. Changing it means editing
a frozen module's data structure. That is the honest reason this lane stops at
1.49×/1.66× — see §6 H-CB-1.

**6. The gate refuses the session's own acceptance fixture, and that is
correct.** `trainer_partitions.DEFAULT_REGISTRY` puts 2026-01-01..01-31 in
`sealed_b7_5_development_january`, role **SEALED** — not trainable. The
commission's acceptance test (CB-3 gate 1) runs exactly those days. Resolved by
splitting the gate rather than by exempting the engine (§3): the reserved
blackout refuses on **every** path including acceptance, and a reproduction
window is made structurally incapable of emitting a training artifact. Recorded
here as the ratification's rule requires.

**7. No trainable day has a prepared B7.5 day pack on this machine.** The only
pack roots present are January, April and June-4 — all SEALED. So the partition
gate is fully exercised in the *refusing* direction and untested in the
*running* direction, and Session CD's broad-family regeneration needs TRAIN-role
day packs **generated first**. That is a materialization job, not an engine job,
and it is now the lane's critical path.

---

## 0b. The commission's gates, one line each

| gate | verdict | evidence |
|---|---|---|
| **CB-3.1** outcome identity on the sealed 2-day fixture, zero tolerance | **PASS**, four times: solo profiled, solo unprofiled, under 2-way contention, under 4-way contention | `CB_ACCEPTANCE_V1.json`, `CB_ACCEPTANCE_PROFILED_V1.json`, `CB_ACCEPTANCE_UNDER_4WAY_CONTENTION.json` |
| **CB-3.2** speedup + memory, then two concurrent arms; target ≥5× | **1.532× per arm** (target missed), **2.79× smaller**, **1.944× on two arms**, **3.251× on four**, **4.98× per four-arm window**; residual map §4 | `CB_BENCH_TABLE.json` |
| **CB-3.3** sub-window usable — one day costs one day | **PASS** — 62.3 s vs 428.8 s; `--days N`, prefix only, and the honest limit is stated in the code | `CB_BENCH_TABLE.json` → `train_1day` |
| **CB-3.4** partition enforcement wired, fail closed, tested | **PASS** — March refused on every path including acceptance; 81 tests | `tests/research_infra/test_train_engine_guard.py` |
| **CB-3.5** one longer identity check if wall-clock permits | **DID NOT FIT** — command handed over | §6 H-CB-5 |
| **CB-1** identity tuple frozen, with the outside-list | **DONE** | §1, `identity.TUPLE_VERSION` |
| **CB-4** compact trade table + fingerprint, stamped | **DONE** | `CB_FINGERPRINT_V1.json` |

**On the ≥5× target, plainly:** read as "each arm five times faster", it is **not met** —
the answer is 1.53×, and §4's residual map is why. Read as "a four-arm window five times
faster", it is met at **4.98×**, because the memory result turned concurrency from
unaffordable into nearly free. Both readings are in this document because only one of them
is the commission's literal words and only the other one is what the lane will be used for.

### Receipts

All under `phase14/receipts/`:

| file | what |
|---|---|
| `CB_BENCH_TABLE.json` | every run, every cut counter, every derived ratio |
| `CB_ACCEPTANCE_V1.json` | the shipped acceptance receipt (unprofiled, like-for-like) |
| `CB_ACCEPTANCE_PROFILED_V1.json` | the same run profiled — carries the residual map |
| `CB_ACCEPTANCE_UNDER_4WAY_CONTENTION.json` | identity held with four arms running |
| `CB_FINGERPRINT_V1.json` | the CB-4 fingerprint, after the silent-null fix (§5.7) |
| `SESSION_CB_AB.md` | scoped A/B, `gtos-ab-receipt-v1`, 0 → 0, 0 regressed |
| `CB_PREEXISTING_FAILURES.json` | proof the worktree's 11 full-suite failures predate this session |

---

## 1. CB-1 — the identity tuple

`src/research_infra/train_engine/identity.py`. Fourteen fields, versioned
`gtos.train_engine.trade_identity.v1`, in three groups:

* **instance** — `candidate_id`, `decision_time_utc`, `symbol`, `direction`
* **execution** — `entry_time_utc`, `entry_price`, `exit_time_utc`, `close_reason`
* **economics + sizing** — `final_r`, `cost_r`, `net_r`, `risk_cash`,
  `approved_risk_pct`, `headline_result_exclusion_reason`

`close_reason` is in because a stop and a time stop at the same price and time
are different contracts, and this estate has already been bitten by exactly that
(AQ's `time_stop_bars` repair). `net_r == final_r − cost_r` on the sealed rows,
so the three are redundant by one degree of freedom **on the frozen engine** —
all three are in precisely so that a cut which breaks the relation is caught
rather than cancelled.

**The field names were read off the sealed January S1R1 arm of record, and that
mattered.** `fast_engine.bench.TRADE_ECONOMIC_FIELDS` names ten fields that do
not exist on a trade row (`exit_price`, `stop_price`, `target_price`,
`net_cash`, `gross_cash`, `exact_r`, `r_multiple`, `exit_reason`, `lots`,
`volume`). It is dead code there — the extractor prunes every scalar instead —
but a comparator built on that list would have compared ten `None`s to ten
`None`s and reported identity. So `trade_tuples` **raises** on a missing field
rather than defaulting it, and a test pins that two rows both missing the same
field raise rather than comparing equal.

**Outside the tuple — the deletion licence**, named so a reader can check it:
run-namespace-derived ids (`simulated_order_id`, `package_replay_*_bound_*`),
provenance digests (`packet_sidecar_id`, `*_packet_hash_sha256`,
`*_projection_sha256`), the ~1,280 remaining attribution/authority projections
per row, post-hoc re-certification, and timings.

**Outside the tuple but still gated**: all five ledger row counts, and the
missed-opportunity diagnostic pool aggregate. The pool is the substrate AW's
separability mine reads (`JANUARY_BANK` §3, ±38,317 R), so a lane that silently
changed it would be fast and useless. It is compared on the analyzer's own gate
and field, and a baseline pool that scored zero rows **fails acceptance** — AX
shipped exactly that bug into his own comparator and caught it by luck.

---

## 2. CB-2 — the dataflow cut

`src/research_infra/train_engine/cuts.py`. Runtime rebinds into already-imported
frozen modules; **no bound byte changes** (H1 checked at session start and at
each commit: 43 bound paths, 2 non-matching, both the known unhydrated LFS
pointers this worktree carries, neither touched by this session).

### The trap, and the way past it

AX's finding stands: the expensive machinery is *called by* the decision.
`finalize_scheduler_risk_admitted_selection` — the B7.5 selection factor itself —
reaches the attribution projection, which reaches `signed_envelope_failures`,
which reaches the payload hash. "Turn the evidence off" is unavailable there.

Reading the code rather than the profile says what *is* available. Both
`signed_envelope_failures` (`v4_timewarp:12072`) and
`package_new_entry_authority_immutable_payload_failures` (`v4_timewarp:16291`)
hash the **same payload object** independently, per surface, per candidate, and
`envelope_surfaces` walks nested surfaces recursively. That is a re-validation
loop, and a content-addressed memo collapses it without changing a single
computed value.

### The cuts, and what each measured

| cut | target | measured |
|---|---|---|
| `authority_hash_content_memo` | the 19.1 % payload-hash subtree | **84.85 % hit over 29.1 M calls**; node gone from the profile |
| `proof_hash_content_memo` | four MORE `json.dumps`+sha256 hashes, 74.1 s / 15.8 % — found by profiling run A, not in AX's tree | 86.1 % / 17.6 % / 83.7 % / 49.5 % hit |
| `abc_concrete_types` (+ `Sequence`) | AX's 80.0 s abc dispatch; `Sequence` was his pending half | shipped on; outcome identity holds |
| `attribution_fields_identity_memo` | AX built it, never verified (his H-AX-2) | 31.25 % hit over 304,457 calls |
| `skip_post_hoc_ledger_recertification` | re-proving rows the run just wrote | on |
| `gc_during_chunk` | the intra-day heap ramp | **8.31 → 2.97 GB**, +33.07 s fixed |

Every one of those runs reports `mismatches: 0`, and **that number means less
than it looks like** — the counters only compare when `--verify` is on, and it
was not. Read it as "no verified comparison disagreed, and zero comparisons were
verified". What the memos are actually backstopped by is four
`OUTCOME_IDENTICAL` runs at zero tolerance (solo profiled, solo unprofiled,
under 2-way contention, under 4-way contention). See §5.5 and H-CB-2.

### The trusted key, stated exactly

`_content_key(payload)` returns `(len, frozenset(typed top-level scalars),
frozenset((name, type, len) per top-level container))`, and returns `UNKEYABLE`
— frozen passthrough, **counted** — for a non-mapping payload or a payload
carrying containers but no scalar at all. All twelve of the engine's own cheap-key
fields are top-level scalars, so the memo key contains them; a test asserts it.

**The residual is exactly one thing and it is pinned by a test**: two payloads
agreeing on every top-level scalar AND on every container's name/type/length,
differing only *inside* a container. `--verify` computes the true digest on
every hit and counts disagreements; the trade-outcome gate is the backstop.

**One measured correction to my own first key.** Run A used the engine's cheap
key plus sorted scalars and reported a 96.66 % hit rate with **zero** fallbacks.
That number was flattering: for 3.43 M calls (11.8 %) the payload carries no
top-level scalar at all, so the old key degenerated to *payload length alone* and
still hit. The current key refuses those. The hit rate fell to 84.85 % and the
run got **faster** (470.4 → 441.7 s, other cuts included) and strictly safer. A
high hit rate is not evidence of a good key.

---

## 3. CB-3.4 — the partition gate, and the tension it had to resolve

`src/research_infra/train_engine/guard.py` imports `trainer_partitions` and never
restates a boundary (Session CC owns that module this wave).

| gate | applies to | refuses |
|---|---|---|
| `assert_no_blackout` | **every** path — no purpose, no flag, no argument | the reserved blackout (March 2026) |
| `assert_trainable` | training runs only | every non-trainable role |

and the exemption is made structurally harmless rather than trusted:
`runner.write_training_outputs` checks the **authorization object**, so a
reproduction run can never produce a training trade table. Both halves are
tested, including a hostile registry that marks March `TRAIN` and is still
refused (because `reserved_blackout` is checked before partition lookup).

The guard **derives its own day list** from the window bounds the engine will
use. A caller hands over a range, never a day list, so it cannot narrow the audit
by narrowing what it declares.

---

## 4. Speed, memory, and concurrency

Every run below is the same 2-day sealed January fixture on this machine.
Receipt: `phase14/receipts/CB_BENCH_TABLE.json` (whole table, plus every
run's cut counters and row counts).

### Solo

| run | cuts | profiled | wall | peak RSS | verdict |
|---|---|---|---:|---:|---|
| frozen baseline | none | no | **657.0 s** | **8.31 GB** | reproduces the published counts |
| train A | first key, no proof-hash memo, no gc | yes | 470.4 s | 8.54 GB | `OUTCOME_IDENTICAL` |
| train B | + proof-hash memo + gc | yes | 453.2 s | 3.17 GB | `OUTCOME_IDENTICAL` |
| train C | shipped set, unified key | yes | 441.7 s | 3.11 GB | `OUTCOME_IDENTICAL` |
| **train C** | **shipped set** | **no** | **428.8 s** | **2.97 GB** | **`OUTCOME_IDENTICAL`** |

The last row is the headline: **1.532× wall, 2.79× smaller**, both sides
unprofiled. The profiled rows are kept because they carry the residual maps.

### Fixed cost, and the lever that hides in it

| run | wall |
|---|---:|
| frozen, 1 day (`2026-01-01`, 0 candidates) | **28.9 s** |
| train, 1 day, without `gc_during_chunk` | **29.3 s** |
| train, 1 day, with `gc_during_chunk` | **62.3 s** |

So the cuts are fixed-cost-neutral (29.3 vs 28.9 s, inside noise) and
`gc_during_chunk` costs **+33.07 s** of pure fixed overhead — it enables cyclic
GC and freezes the post-import heap, and the collections during prewarm are not
free. On the 2-day fixture it earns that back several times over and takes
5.3 GB off the peak. On a one-day iteration it is a 2.1× regression. **Drop it
from `--patches` for single-day work.**

Subtracting the fixed cost gives the number that governs a month:
**628.1 s → 366.5 s per working day, 1.714×** (all four inputs unprofiled).

### Two concurrent arms (the commission's gate 2)

`S1R1` and `S0R0`, launched together, both profiled, comparand the profiled solo:

| | value |
|---|---:|
| solo wall | 441.7 s |
| contended walls | 453.5 s (S1R1), 454.4 s (S0R0) |
| pair wall | **454.4 s** |
| **per-arm slowdown** | **1.029×** |
| serial reference (2 × solo) | 883.5 s |
| **throughput gain** | **1.944×** |
| combined peak RSS | 6.23 GB |
| machine swap growth | **0** (swap in use actually fell 32 MB) |

### Four concurrent arms (the actual B7.5 window shape)

All four factorial arms at once, all unprofiled, comparand the unprofiled solo:

| | value |
|---|---:|
| solo wall | 428.8 s |
| contended walls | 520.6 / 520.8 / 522.8 / **527.6 s** |
| **per-arm slowdown** | **1.230×** |
| **throughput gain** | **3.251×** |
| **four-arm window vs frozen serial** | 2,628 s → 527.6 s = **4.98×** |
| combined peak RSS | **9.14 GB** of 16 |
| per-arm peak RSS under contention | 2.28–2.29 GB (*lower* than the 2.97 GB solo) |
| machine swap growth | **0** |
| CPU | all four at ~99 % for the whole run |

Two things in that table are worth saying out loud. **Per-arm peak RSS falls
under contention** (2.97 → 2.29 GB) — cyclic GC collects harder when the machine
is tighter, so the footprint is adaptive rather than fixed, which is why four
arms fit where the arithmetic said 11.9 GB. And **throughput is measured against
the solo wall, not against the sum of the contended walls** — the latter is close
to N by construction whenever N processes overlap and measures overlap rather
than benefit. That is AX's correction and it is kept.

### The residual map, after the cuts

From the profiled shipped run (`CB_ACCEPTANCE_PROFILED_V1.json` →
`residual_map`), 11,897 samples over 441.7 s. Top self-time:

| share | node | what it is |
|---:|---|---|
| 12.1 % | `replay_compact_event_sink._append_canonical_row` | `json.dumps` of every 1,428-key row — the sink's storage medium |
| 7.3 % | `threading.wait` (main thread) | blocked on an executor; both hot modules use Process/ThreadPool executors, so this is real work off the sampled thread, not idle |
| 5.7 % | `json/encoder.iterencode` | serving the above and the surviving hash misses |
| 4.3 % | `probability_debate_v4._stable_sha256` | the 16 % of its calls that MISS — very large payloads |
| 4.0 % | `v4_timewarp._stable_sha256_uncached` | the 82 % that miss (54.7 % of its calls are non-mapping and refuse a key) |
| 3.1 % | `_atomic_predecision_execution_fillability_claim` | a projection the decision reads |
| 3.6 % | the authority memo's own cost | `_content_key` 2.0 % + wrapper 1.6 % |

and the cumulative tree is now led by `finalize_scheduler_risk_admitted_selection`
at 24.2 % — down from AX's 27.5 % but no longer dominated by hashing:
`package_new_entry_authority_attribution_fields` is **11.5 %, down from 26.2 %**,
and the payload-hash subtree that was 19.1 % is absent.

**Read that table as the reason the lane stops at 1.53× per arm.** What is left
is storage, executors, the surviving large-payload hash misses, and the decision
itself. There is no remaining node that is purely proof.

---

## 5. What I got wrong

**1. I shipped a bug into the guard and the first smoke test caught it.**
`WindowRefused` subclasses `PartitionRefusal` and the module docstring told
callers "one except catches both" — but the trainable check *delegates* to
`registry.assert_trainable`, which raises the **base** class. Every caller
writing `except WindowRefused` would have let a refusal escape as an unrelated
error. It is now re-raised as this module's type, with a regression test. The
lesson is small and unglamorous: I wrote the docstring claim before the code
that made it true.

**2. My first content key had a 96.66 % hit rate and a hole in it.** I built it
as "the engine's cheap key, strengthened by scalars", assumed the strengthening
was pure upside, and reported the hit rate as the headline. It was not upside for
the 11.8 % of payloads that carry no top-level scalar: for those the key
collapsed to payload length, and they hit anyway. The run was outcome-identical,
so nothing broke — but the number I would have published as evidence of a good
key was partly evidence of a key that could not discriminate. Found only because
I changed the key for an unrelated reason and watched a counter move.

**3. I predicted the empty-payload case wrongly and it cost a measurement.** When
`unkeyable` appeared at 3.43 M I reasoned "those must be empty dicts, and `{}` is
exactly keyable" and shipped the fix. It recovered **435 calls of 3,433,381**.
The 3.4 M are container-only payloads, not empty ones. The fix is still correct
and still in, but the hypothesis was wrong and I stated it in a commit message
before testing it.

**4. I nearly reported a 33-second regression as a win.** `gc_during_chunk` is
unambiguously good on the 2-day fixture and I had no reason to look further. It
was only because gate 3 needed a one-day run that the fixed cost appeared at all
— and on that window it is a 2.1× *slowdown*. A lever measured on one window
size is not a lever measured.

**5. I did not run `--verify`, and that is the gap in the strongest claim I
make.** Every receipt in this session reports `mismatches: 0` on every memo, and
that number is nearly empty: the counters only compare when verify mode is on,
and it was not. **It means "no verified comparison disagreed", and zero
comparisons were verified.** The trusted key is backstopped by four
`OUTCOME_IDENTICAL` runs at zero tolerance and by construction — which is real
evidence, and is *not* the per-call measurement the identity argument promises.
§6 H-CB-2 is the one command that closes it. I chose the two required gates over
it with the clock I had — the same trade AX made, for the same reason, and I am
recording it in the same place he did rather than hoping nobody checks what the
zero is counting.

**6. I built the acceptance instrument before I tested it.** `accept.py` shipped
in the first commit with no tests, and I only wrote them when the A/B scope tool
refused to resolve the module — i.e. for a mechanical reason, not because I
noticed that the thing deciding whether the lane ships was the one unexercised
module in it. The tests found nothing wrong, which is luck rather than evidence:
this is the module where "it looked right" is least acceptable.

**7. I shipped a silent null into the output contract — the exact failure this
session's own §1 is about.** `fingerprint()`'s
`shared_execution_contract_digest_sha256` read **`None` on all four measured
runs** and nobody complained, because I built the fingerprint from a
freshly-constructed args object while `sealed_inputs.prelude` stamps the digest
on the args the *run* used. That field is the one that identifies the config an
arm ran under, so two arms with different configs would have been
indistinguishable in CC's iteration ledger. Found by reading a receipt I had
already committed, not by a test.

Both of my first two fixes were wrong in the same way — I tried to *recover* the
digest afterwards (`current_shared_contract`, then `bind_fresh_source` first),
and both raised `shared_execution_contract_invalid`, because the binding is
stamped on one object and cannot be re-derived onto a copy. The correct fix is
to have the harness report what it bound. Verified end to end:
`phase14/receipts/CB_FINGERPRINT_V1.json`. The four measured runs' receipts
still carry the null in that one field and are **not** regenerated — they are
the artifacts of the runs that produced the numbers, and quietly rewriting them
would be worse than the null.

**8. Writing my own blocks broke two of BD's citations, and I had to be told by
a test.** Appending B2150–B2164 moved the block ceiling from B2075 to B2164,
which turned BD's `B2086`/`B2094` — forward-allocated and exempt while they sat
above the old ceiling — into ghosts, without BD having done anything wrong and
without my having touched them. AU's B1593 exposure exactly, and
`WAVE_11_WORKING_AGREEMENT.md` §5 puts it on whoever raises the ceiling. Fixed
per the estate's own precedents (B1976-shaped `KNOWN_GHOSTS` entries; CB's
in-flight range dropped per the test's own remedy — `IMPLEMENTATION_STATE.md`
B2165). Worth writing down because it is the *second* time this session that the
consequence of a change was invisible in the thing I was looking at.

**9. The trap I did NOT fall into, only because a tool refused.** My first A/B
passed an unquoted `$SHARED` file list to `pytest_failset capture`; `zsh` does
not word-split, so the whole list reached pytest as one argument, it exited with
a usage error, and both captures came back empty. That is bit-for-bit the fake
A/B `IMPLEMENTATION_STATE.md` B2075 records against AR §8.9 — *"reported the
answer its author wanted"*. It was caught because the tool marks an unparseable
capture `usable_as_baseline=false` and refuses to diff it, not because I noticed
that 149 tests had become 0.

---

## 6. Handoff

**H-CB-1 — the next 1.5× is the compact event sink, and it is a fork.**
`_append_canonical_row` is 12.1 % of wall and `iter_rows` another 2.8 %, because
`ReplayCompactLedger` **is** the sink: every row is `json.dumps`-ed on append and
JSON-decoded on iteration. That is storage, not evidence, so no dial reaches it
and no runtime rebind fixes it without replacing the ledger's data structure
inside a frozen module. With 3.1 GB of headroom the obvious design — keep rows as
dicts in memory for the training lane and serialise once at day end — is now
affordable, and it was not when the sink was written. Budget it as a fork of
`replay_compact_event_sink.py` under `train_engine/`, with the same
outcome-identity gate as acceptance.

**H-CB-2 — one verify run settles the trusted key, and it is the highest-value
hour left on this instrument** (the same sentence AX wrote about his own pending
run, for a bigger claim):

```bash
python3 -m src.research_infra.train_engine.runner \
  --arm S1R1 --days 2 --prefix CB_VERIFY_B7_5_S1R1 \
  --purpose ACCEPTANCE_REPRODUCTION --verify \
  --out /tmp/bench/CB_VERIFY.json
```

Verify mode computes both answers on every memo hit and counts disagreements, so
its wall-clock means nothing and its `cut_report` is the output. Zero mismatches
over ~25 M verified hits converts the key from "backstopped" to "measured".
Non-zero says exactly how unsafe it is, per function.

**H-CB-3 — the lane's critical path is day packs, not the engine.** No trainable
day has a prepared B7.5 day pack on this machine (§0 finding 7). Session CD
cannot regenerate the broad family under the repaired stack until TRAIN-role
packs exist for `train_backfill_2025H2` (2025-06-02..12-31) and/or
`train_february_2026_unclaimed`. The engine is ready; the inputs are not.

**H-CB-4 — the 3.43 M container-only payloads are worth one more look.** They are
11.8 % of the authority hash's traffic and every one of them takes the full
canonical path. Keying them safely means one level of descent into the
containers, which is more expensive than the current key and much cheaper than
`_canonical_hash_payload`. Bound the win first by counting how many are distinct.

**H-CB-5 — gate 5 (a longer identity check) did not fit, and it is also the run
that settles the month-scale extrapolation.** A full January arm at the measured
marginal rate is ~2.4 h and its frozen comparand ~4.1 h; that did not fit
alongside the two required concurrency gates. It answers two things at once:
whether outcome identity survives 31 days, and whether per-arm peak RSS stays
near 3 GB when the window is 15× longer — the one assumption behind the
"16.5 h → ~3.0 h" figure in §0.

```bash
# frozen comparand (~4.1 h) and train lane (~2.4 h), same prefix discipline
python3 -m src.research_infra.fast_engine.bench --arm S1R1 \
  --prefix CB_MONTH_FROZEN_B7_5_S1R1 --patches none --evidence full \
  --out /tmp/bench/CB_MONTH_FROZEN.json
python3 -m src.research_infra.train_engine.runner --arm S1R1 \
  --prefix CB_MONTH_TRAIN_B7_5_S1R1 --purpose ACCEPTANCE_REPRODUCTION \
  --out /tmp/bench/CB_MONTH_TRAIN.json
python3 -m src.research_infra.train_engine.accept \
  --baseline /tmp/bench/CB_MONTH_FROZEN.json \
  --candidate /tmp/bench/CB_MONTH_TRAIN.json \
  --out /tmp/bench/CB_MONTH_ACCEPT.json
```

Omitting `--days` runs the full sealed window. The frozen comparand is the
expensive half, and the sealed January S1R1 arm of record already on disk is
**not** a substitute for it (different output namespace, different contract
revision), so the pair has to be run together. If only one fits, run the train
side and check peak RSS — that alone converts the extrapolation into a
measurement even without the identity half.

**H-CB-6 — what this session did NOT do, deliberately.** No sealed window was
run. No bound file moved. No VPS contact. No broker-capable script. No claim
about any strategy family. March stays outcome-unread and is refused by the gate
on every path.

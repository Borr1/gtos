# Session AX — the fast sealed engine, built beside the frozen one

**Wave 12, blocks B1700–B1749. Branch `phase12/fast-engine`.**
Commission: `phase12/SESSION_AX_FAST_SEALED_ENGINE.md`. Owner authority: Borhen,
2026-07-30 — *"i dont care about the reasons just build the fast replay and fix
all the issues."*

---

## 0. Findings first

**1. The fast lane is built, it reproduces, and it is only ~1.06× faster. That
number is the finding, not a disappointment to be explained away.** On the
sealed 2-day January S1R1 fixture, same machine, same sealed read-only inputs:

| | frozen ×2 | fast (as measured) | delta |
|---|---:|---:|---|
| wall | **636.7 / 624.6 s** | **594.3 s** | **1.061×** (band 1.051–1.071) |
| peak RSS (`ru_maxrss`) | 7.72 / 7.73 GB | 7.99 GB | **+3.4 %, the wrong way** |
| user CPU | 582.9 s | 572.3 s | −1.8 % |
| day-2 economic hot path | 508.4 s | 498.4 s | −2.0 % |
| row counts | 8,812 / 10 / 5 / 96 / 8,807 | **identical** | — |

Two frozen runs give a **1.94 % run-to-run noise band**, so the improvement is
real but only about three times the noise.

**Reproduction is proved by control, not by assertion**: the fast lane's
differences from the frozen engine are *exactly* the differences the frozen
engine has from **itself** when re-run under a different output namespace — same
244 differences, same 7 provenance-digest fields, same multiplicities, **zero
moved quantities** on either comparison (§3).

**2. The 60.6 %-is-evidence figure is an attribution, not a separability claim,
and the difference is the whole session.** The expensive machinery is *called by*
`finalize_scheduler_risk_admitted_selection` — the B7.5 selection factor itself.
Writing the never-read bytes is 6.7 % of wall; computing the attribution is
26.2 %. An evidence dial cannot reach the 26.2 %. See §1.

**3. The intra-day memory ramp is pinned by the sealed contract, not by an
engineering choice.** `verify_denominator_to_deployment_execution.py:5161-5167`
requires cyclic GC to be **off** across each chunk, and `chunk_size = 1`. The
cheapest memory lever is contractually unavailable. Fixing the ramp is a contract
regeneration — which is a decision, not a task.

**4. The authority payload hash is called 52.0 MILLION times on a two-day
fixture, and 99.89 % of those calls see a payload object nobody has hashed
before.** That is 5,902 hash computations *per candidate*, each one a recursive
canonicalisation plus a `json.dumps` plus a SHA-256. **The cost is the call
count, not the call.** My memo — keyed on payload object identity — achieved a
**0.11 % hit rate** (55,672 hits in 52,064,280 calls; 3.1 % took the frozen
passthrough; **0 mismatches**, so it was correct, just useless). The caller
rebuilds the payload as a *new dict* each time, so an identity key can never hit.
It saved ~0.2 s, cost ~5 s of `id()` lookups across 52 M calls, and added
**+270 MB of peak RSS**. **It is now default-off** — and the number it produced
is worth more than the patch was.

**5. What a ~1.06× lane is worth, stated plainly.** A four-arm month window goes
from ~16.5 h to ~15.6 h. That is not the 4–6 h the commission hoped for and it
does not make sealed confirmation routine. The route to that number is §6's
handoff, and the two largest items on it — the 26.2 % attribution node and the
`Sequence` half of the abc dispatch — are both built, both tested, and both
waiting on the *same* verify run.

---

## 1. The finding that changed the build

**The commission's premise was that the never-read evidence rows could be made
opt-in behind a dial, and that this alone would remove most of the 60.6 %. The
audit's own cumulative profile says the opposite, and the correction is the most
useful thing this session produced.**

Reading `docs/audits/opus5-architecture-20260725/receipts/profile_jan01_02_sampled.json`
as a *tree* rather than as a flat self-time list (2-day S1R1 fixture, 1102.3 s
wall):

| node | cumulative s | share | what it is |
|---|---:|---:|---|
| `run_campaign` | 871.0 | 79.0 % | the whole replay |
| ├ `finalize_scheduler_risk_admitted_selection` | **303.4** | **27.5 %** | **the B7.5 selection factor** |
| │ └ `package_new_entry_authority_attribution_fields` | 288.4 | 26.2 % | attribution projection |
| │   └ `signed_envelope_failures` | 269.0 | 24.4 % | envelope validation |
| │     └ `…immutable_payload_failures` | 238.9 | 21.7 % | payload validation |
| │       └ `…payload_hash_sha256` | **210.4** | **19.1 %** | canonical JSON + sha256 |
| ├ `execution_fillability_alias_fields` | 277.8 | 25.2 % | calls the same projection per surface |
| ├ `compact_event_sink.append` | 97.1 | 8.8 % | writing evidence rows |
| └ `evaluate_candidate_v4` | 91.1 | **8.3 %** | **the decision** |
| `prewarm_sparse_tick_sources` | 106.2 | 9.6 % | one-time source prewarm |
| `append_jsonl` | 44.3 | 4.0 % | final ledger writing |
| `current_summary_v2_contract_for_outputs` | 29.4 | 2.7 % | post-hoc re-certification |

Three things follow, and each redirects work:

1. **Writing the never-read bytes is cheap; computing the attribution is not.**
   `append_jsonl` + the post-hoc recertification are 6.7 % of wall together. An
   `--evidence` dial that suppresses row emission therefore buys single digits,
   not the 60 %. The dial is still built — it is just honestly small.
2. **The expensive machinery is called by the decision path.** The 288 s
   attribution builder's biggest caller is
   `finalize_scheduler_risk_admitted_selection`, which is the S0/S1 selection
   switch the whole B7.5 factorial was built to test. "Turn the evidence off"
   is not available there without changing what gets selected.
3. **So the lever is memoisation, not suppression** — *this is what I concluded
   from the profile, and the run refuted it.* The reasoning was that the same
   authority payload is re-encoded and re-hashed repeatedly, by
   `signed_envelope_failures` and `…immutable_payload_failures` independently,
   for every surface the finalizer walks; and that the engine's own cache cannot
   help because `package_new_entry_authority_payload_hash_sha256` computes
   `_stable_sha256_material(payload)` — the canonicalise-plus-JSON-dump that *is*
   the expense — **before** consulting the cache
   (`moonshot_scheduler_v4_best_trade_allocator.py:896-908`). All of that is
   true. What is false is the implied conclusion that an identity memo can
   recover it: **measured hit rate 0.11 % over 52.0 M calls** (§0 finding 4),
   because the caller rebuilds the payload as a new dict every time. The
   repetition is *logical*, not *referential*.

   **The corrected statement: the lever is the call count.** 5,902 authority
   hashes per candidate is a re-validation loop. Cutting it means either
   memoising a level up (the attribution projection, which does key on stable
   surfaces — H-AX-2) or not recomputing a digest that a caller already holds.

A fourth measurement killed a lever before it cost anything:

4. **The sealed contract pins cyclic GC off for the whole day chunk.** The
   engine disables GC at `attempt5:16838-16839` and `chunk_size = 1`, so the
   GC-off window is exactly the window in which §A1 measured the heap ramping
   0 → 5.5 GB. Re-enabling GC is the obvious memory fix — and the R2-bound
   verifier `verify_denominator_to_deployment_execution.py:5161-5167` requires
   `automatic_gc_enabled_before/after_explicit_collection` to be exactly
   `False`. **The intra-day ramp is contractually mandated.** Any real fix is a
   contract regeneration, not a runtime flag. The patch exists, is default-off,
   and is flagged `sealed_compatible=False` in every receipt it appears in.

---

## 2. What was built

`src/research_infra/fast_engine/` — seven new modules, **zero bound bytes
touched** (H1 check at session start and at commit: 43 bound paths, 2
non-matching, both the known unhydrated LFS pointers this worktree carries and
neither modified by this session).

| module | what it is |
|---|---|
| `sealed_inputs.py` | resolves the sealed January inputs read-only from the producing worktree and builds args through the frozen runner's **own** `build_standard_args`, so the fast lane cannot drift from the sealed execution surface |
| `accel.py` | the patch registry: five runtime accelerations, each with an identity argument, a verify mode and a `sealed_compatible` flag |
| `bench.py` | one arm, one window: wall, peak RSS, an optional statistical profile, and the economic extraction the comparator reads |
| `reproduction.py` | the nan-aware R-identity comparator |
| `campaign.py` | N arms concurrently, with per-process RSS and machine swap growth measured |
| `receipt.py` | assembles the acceptance receipt and refuses to mark it accepted on a divergence, a row-count change, or an errored run |
| `README.md` | how to run it and what each patch costs |

**The lane is a runtime lane, not a fork.** It imports the frozen modules and
rebinds symbols inside them; the bytes on disk are untouched, so both the R2
input-binding drift check and the execution-seal digest are unaffected. A fork
would have been a re-seal at ~16.5 machine-hours per window.

### The five patches

| id | default | sealed-ok | target | status |
|---|---|---|---|---|
| `abc_concrete_types` | **on** | yes | 80.0 s of abc `isinstance` dispatch | shipped (Mapping/MutableMapping only) |
| `authority_hash_identity_memo` | **off** | yes | the 210.4 s payload-hash subtree | **turned off on measurement**: 0.11 % hit rate, +270 MB |
| `attribution_fields_identity_memo` | off | yes | the 288.4 s attribution projection | **built, one verify run from shipping** |
| `skip_post_hoc_ledger_recertification` | off | yes | the 29.4 s post-hoc re-read | built; `--evidence decision` |
| `gc_during_chunk` | off | **no** | the intra-day heap ramp | built; **contractually unavailable** |

Plus one symbol rather than a patch: `Sequence` under `abc_concrete_types`,
registered and off by default — see below.

**`--evidence` defaults to `full`, not to `decision`.** The commission asked for
`decision` as the default. I deviated for a measured reason: the dial's whole
measured headroom is 2.7 % (§1), and `full` is what keeps the fast lane's output
directly diffable against the frozen lane's — which is the property this entire
session exists to establish. A 2.7 % saving is not worth making the default
configuration the one that *cannot* be compared byte-for-byte.

**A measurement that killed a design before it was written.** The obvious
acceleration for `abc.Mapping` dispatch is a surrogate class with a fast
`__instancecheck__`. Benchmarked on this machine over a mixed workload:

| check | ns/check |
|---|---:|
| `isinstance(x, abc.Mapping)` | 88.5 |
| metaclass surrogate | **126.0** |
| `isinstance(x, dict)` | 16.9 |

The surrogate is **42 % slower than the abc it replaces** — `abc`'s check is
already C-cached, and a Python-level `__instancecheck__` adds a frame the C path
does not have. So the only real win is rebinding to a concrete type, which makes
exhaustiveness a measurement obligation rather than a style choice. That is why
`--verify` exists: it computes both answers on every check and counts
disagreements.

### Why the shipped pair only bought 2.0 % of the hot path

The audit attributes 80.0 s to abc dispatch. The shipped patch recovered about a
quarter of it, for one structural reason worth writing down: **`Sequence` was
left on abc.** The hot recursion is

```python
if isinstance(value, Mapping): ...                     # now concrete: 16.9 ns
if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
```

Every scalar leaf — the overwhelming majority of nodes — fails the first test and
then pays the full abc price on the second. Rebinding `Sequence` to
`(list, tuple)` is *exactly* equivalent at this call site, because the very next
clause excludes `str`/`bytes`/`bytearray` anyway. It is **not** equivalent in
general — `str`, `bytes`, `range` and `memoryview` are Sequences and are not in
the tuple — and there are 37 other `isinstance(..., Sequence)` sites in the
timewarp loop and 11 in the allocator, at least some of which may lack that
guard. A site like `if isinstance(v, Sequence): for item in v:` would iterate a
string's characters under abc and skip it under the concrete tuple: a real
behaviour change, silently.

So `Sequence` is **registered in the patch table and off by default**, and
turning it on is a verify-run decision, not a judgement call. This is the second
of the two items on which the lane's speed now depends (the first being the
attribution memo) — both built, both measured-gated, neither guessed.

---

## 3. Reproduction

### What "reproduced" is allowed to mean here

The fixture is the sealed 2-day January S1R1 window (`2026-01-01..02`), run from
the sealed read-only inputs in the producing worktree: the same source bundle,
typed cache, tick-sparse cache, prepared day packs and R2 contract the sealed
arm uses. **It is a fixture, not an arm of record** — `--stop-after-day` sets
`engineering_stop_after_day`, which the sealed path hardcodes to `None` (H5).
The receipt says so in its own `fixture.is_sealed_arm_of_record` field.

The frozen baseline reproduced the fixture's published row counts exactly —
**8,812 candidates, 10 orders, 5 trades, 96 scorecard, 8,807 missed** —
identical to §A1's run and to Session G's three. That is what licenses using it
as the comparand at all.

### The control, and why the comparison needs one

Two runs of the same arm **cannot** produce byte-identical ledgers, and not for
any interesting reason: the engine refuses to reuse an output namespace
(`configure_output_namespace`, `attempt5_output_namespace_must_be_new`), and the
namespace is stamped **inside row values** — `campaign`,
`package_replay_order_executable_bound_order_id`, and every id derived from
them. Worse, it is stamped inside payloads that are then **hashed**, so
`packet_sidecar_id` and friends differ by construction and no string
normalisation can recover them.

Normalising the namespace out of the string values removed 84 of the 328 raw
differences. The remaining **244 were all 64-hex provenance digests, across 7
field names, with zero moved quantities** over **123,813** scalar field
comparisons (5 trade rows x 1,322 fields, 10 order rows x 1,171, 96 scorecard
rows x 1,098). That is suggestive and it is not proof — a comparator that
classifies its own leftovers as benign is marking its own homework.

So the claim is made against a **control**: the frozen engine run a second time
under a *different* prefix, compared to the first frozen run by the same
comparator. If frozen-vs-frozen produces the same difference signature as
frozen-vs-fast, then the fast lane's differences are attributable to naming and
nothing else.

### The control result — the acceptance

| | frozen vs **frozen** (control) | frozen vs **fast** |
|---|---:|---:|
| verdict | `PROVENANCE_DIGESTS_ONLY` | `PROVENANCE_DIGESTS_ONLY` |
| rows compared | 111 | 111 |
| total differences | **244** | **244** |
| 64-hex provenance digests | **244** | **244** |
| **moved quantities** | **0** | **0** |

And the signature — which field names differ and how often — is **identical**:

| field | control | fast |
|---|---:|---:|
| `packet_sidecar_id` | 92 | 92 |
| `scheduler_packet_sidecar_id` | 77 | 77 |
| `scheduler_option_trace_projection_sha256` | 25 | 25 |
| `finalizer_primary_probe_risk_authority_packet_hash_sha256` | 21 | 21 |
| `candidate_packet_sidecar_id` | 10 | 10 |
| `execution_packet_sidecar_id` | 10 | 10 |
| `risk_authority_packet_hash_sha256` | 9 | 9 |

**The fast lane differs from the frozen engine in exactly the way the frozen
engine differs from itself.** Not one economic quantity moved, on either
comparison; the row counts are identical on all three runs
(8,812 / 10 / 5 / 96 / 8,807); and the seven differing fields are the same seven,
at the same multiplicities, whether the second run was accelerated or not.

**The control also measures run-to-run noise, which the speedup claim has to
clear.** Two frozen runs: **636.7 s and 624.6 s — a 1.94 % spread** (peak RSS
7.72 and 7.73 GB, i.e. stable). Against the frozen mean of 630.7 s, the fast
lane's 594.3 s is **1.061×**; against the slower and faster frozen runs
individually, 1.071× and 1.051×. **Call it ~1.06× with a ~2 % noise band from
n = 2.** The improvement is outside the noise, and it is small.

The comparator's claim is built from four things, and the fourth is the one that
makes it hard to fool:

1. row counts per ledger;
2. every **scalar** field of every trade, order and scorecard row, compared
   nan-aware in both directions, with an absent key counted as a difference;
3. the analyzer's own diagnostic-pool aggregate over the 8,807 missed rows —
   `opportunity_net_proxy_r` under the diagnostic-scoreable gate, mirroring
   `analyze_b7_5_selection_sizing_matrix.py:742-770`, so the quantity compared
   is the one `JANUARY_BANK.md` §3 quotes;
4. a **canonical SHA-256 per ledger over every field of every row**. A whole
   trade row is ~1.9 MB of nesting and **1,322** scalar fields. (That is itself
   a measurement of the evidence problem: 111 rows carry 123,813 scalar fields
   between them, and five of those rows are the trades.)

**Point 4 does not do the work I first claimed for it, and the receipt says so.**
A per-ledger digest hashes rows that *contain* the run-namespace-derived packet
digests, so it can never match across two runs — it is a within-run integrity
artifact, not cross-run evidence. **Nested (non-scalar) fields are therefore NOT
independently verified across runs.** What is verified is the 123,813 scalar
comparisons with zero moved quantities, plus the control below.

Excluded, and named in the receipt rather than left to memory: timing fields
(`economic_hot_path_seconds`, `proof_finalization_seconds`, `*_seconds`,
`*_elapsed`), run identity (`*_run_id`, `*_generated_at`, `host`, `pid`).

**The exclusion list matches nothing in the actual ledgers.** Checked against
the baseline's own rows: of every scalar field on every trade, order and
scorecard row, **zero** are excluded. The list is defensive, not load-bearing —
so the comparison is over the complete field set, and the phrase "timing fields
may differ" is not doing any work in this receipt.

---

## 4. Concurrency (AX-3)

AX-3 was conditional: *"H3's ban on parallel arms was caused by the 6.4 GB
evidence accumulation. If AX-1 collapses it, measure two concurrent arms' net
cost."*

**The precondition failed.** AX-1 did not collapse the footprint — peak RSS went
from 7.72 GB to 7.99 GB, i.e. slightly up (§0, finding 4). The reason is §1's
finding 4: the ramp is inside a GC-disabled window that an R2-bound verifier
requires to stay disabled.

Measured anyway, because "it does not fit" is a number and an assumption is not.
Two arms (`S0R0` and `S1R1`), both on the fast lane, both on the 2-day fixture,
launched simultaneously on this 16 GB / 10-core machine. **Both completed
successfully, with identical row counts to every other run.**

| | value |
|---|---:|
| concurrent wall for the pair | **971.3 s** |
| each arm's own wall under contention | 964.7 s (S0R0), 962.3 s (S1R1) |
| the same arm **solo** | 594.3 s |
| **per-arm slowdown** | **1.62×** |
| serial reference (2 × 594.3 s) | 1,188.6 s |
| **real throughput gain** | **1.224×** — not 2× |
| machine swap growth during the run | **+4.39 GB** |
| peak sampled total RSS | 7.38 GB *(undercounts — see below)* |

**Do not read the harness's own `speedup_vs_serial: 1.984`.** It divides the sum
of the two *contended* arm walls by the concurrent wall, which is close to 2 by
construction whenever two processes overlap — it measures overlap, not benefit.
The honest reference is the **solo** wall, and against that the pair bought
**1.224×** for 4.39 GB of swap. That correction is now in the harness's own
output field names.

### What the machine did while it was measured

The shape is more informative than the total. At 15 minutes in:

* swap had grown from 4.59 GB to **7.85 GB** and macOS had extended the swap
  file from 5,120 MB to 9,216 MB (it peaked at **9.20 GB used**);
* the compressor was holding ~5.4 GB;
* **the two arms were at 88.9 % and 26.5 % CPU** — one running, one page-starved.

The sampled peak RSS of 7.38 GB for *both* arms together, against 7.99 GB for
**one** arm solo, is not the arms getting smaller. It is macOS compressing and
paging their working sets out from under the sampler. RSS stopped being a
measure of demand at that point; the swap figure is the one that means anything.

**Conclusion for AX-3: two concurrent arms are possible but not worth it at this
footprint** — 1.22× throughput for 4.4 GB of swap and a 1.62× per-arm slowdown,
on a machine shared with other work. A four-arm month window run two-up would go
~16.5 h → ~13.5 h, at the cost of making the machine unusable for anything else.
The route to real concurrency is the footprint, and the footprint is §1 finding 4:
contract-pinned.

---

## 5. What I got wrong

**1. I shipped the exact failure the working agreement warns about, into the
acceptance instrument itself.** The first version of the comparator's
missed-opportunity aggregate summed `net_r`, falling back to `exact_r`. Neither
field exists on a missed-opportunity row. It did not raise; it returned
`positive_net_r: 0.0, negative_net_r: 0.0, positive_rows: 0` — a clean-looking
digest of 8,807 rows in which **every single one had been silently skipped**.
Two identical zeros would have compared equal on both sides and the comparator
would have reported `R_IDENTICAL` while comparing nothing at all. I caught it
only because an all-zero diagnostic pool is implausible against
`JANUARY_BANK.md` §3's ±38,317 R. The fix mirrors the analyzer's own gate and
field exactly (`analyze_b7_5_selection_sizing_matrix.py:742-770`,
`opportunity_net_proxy_r` under the diagnostic-scoreable gate) and adds an
`unreadable_proxy_rows` counter so the same class of miss reports itself next
time. **"Silent nulls fall loudly" is a rule about your own instruments before
it is a rule about the engine's.**

**2. I burned a run on a fixture with nothing in it.** The first bounded run
stopped after `2026-01-01`, which is New Year's Day: 0 candidates, 0 orders, 0
trades. It cost 61 s, so the waste was small, and it did validate the harness
end to end — but I should have read the fixture's own row counts before choosing
the bound, not after.

**3. My first instinct for the ABC acceleration would have made the engine
slower.** A surrogate class with a fast `__instancecheck__` measures 126.0 ns
against `abc`'s 88.5 ns. I only found out because I benchmarked before building.
Had I not, the "acceleration" would have shipped as a 42 % regression on 80 s of
the run.

**4. The commission's framing — and this repository's standing 60.6 % line — is
about attribution, not separability, and I initially read it the same way.** I
spent the first part of the session designing an evidence dial. The cumulative
tree says the dial's honest headroom is 6.7 %, because the expensive machinery
is *called by* the selection finalizer. The 60.6 % figure is not wrong; the
inference "therefore it can be switched off" is.

**5. Memo entries hold their keys alive, and I did not price that before
running.** The identity memo holds a strong reference to every keyed payload
precisely so `id()` cannot be recycled — which also keeps everything each
payload references resident. `MEMO_MAX_ENTRIES` is 4096 and was chosen without
measuring what a payload retains. Measured effect: **+270 MB on peak RSS for a
2.0 % hot-path saving.** I did not predict it and would not have caught it
without A/B-ing peak RSS as well as wall.

**6. I destroyed a completed run's economics with a careless re-extraction.**
I had just added auto-cleanup of the run's output namespace; the fast run
therefore deleted its own route, and my re-extraction against that path returned
an empty payload which I then wrote over the good comparison file. Cost: one
10-minute run. It is the *third* instance of the same class in one session
(silent absence reading as data), and the fix is now structural —
`extract_economics` raises `economics_route_absent` rather than returning
nothing.

**7. I did not run the verify pass.** Both remaining levers — the attribution
memo and the `Sequence` symbol — are gated on it, and I chose the control run
and the concurrency measurement over it with the clock I had. That is a defensible
ordering (without the control there is no acceptance at all), but it means the
session ships a ~1.06× lane while holding two built, untested-in-anger
accelerations. §6 H-AX-2 states exactly what one verify run would settle.

---

## 6. Handoff

**H-AX-0 — the highest-value target on this engine is a CALL COUNT, and it is
now measured: 52.0 M authority-payload hashes on a two-day fixture, 5,902 per
candidate.** Every one is a recursive canonicalisation plus a `json.dumps` plus
a SHA-256, and 99.89 % of them are of a freshly-built dict, so no identity cache
can touch it. Two directions, both cheap to test and neither attempted here:

1. **Cut the count.** 5,902 hashes per candidate is a re-validation loop, not a
   workload. `signed_envelope_failures` and
   `package_new_entry_authority_immutable_payload_failures` each hash the same
   logical payload independently, per surface, per candidate, and the finalizer
   walks nested surfaces repeatedly. A memo one level up
   (`attribution_fields_identity_memo`, H-AX-2) attacks this; so would passing a
   computed digest down instead of recomputing it.
2. **Trust the cheap key.** The engine already computes a cheap cache key from
   ~12 payload fields (`_package_authority_hash_cache_key`) and then computes the
   full canonical material anyway to validate the hit. Accepting the cheap key
   would collapse the cost — at a stated, quantifiable collision risk. That is a
   contract-level decision, not an implementation one.

**H-AX-1 — the memory ramp is a contract question, not an engineering one, and
that changes who owns it.** `gc_during_chunk` is the single cheapest lever on the
intra-day heap and the R2 verifier forbids it
(`verify_denominator_to_deployment_execution.py:5161-5167`, exact `False`
required). Whoever budgets the memory work should price a **contract
regeneration** — not a runtime flag and not a source-layer rewrite (Session G
already proved the source layer is 1.6 % of the high-water heap). The regeneration
is also what unlocks the deeper emission redesign, since the emission sites are
inside bound files.

**H-AX-2 — one verify run settles both remaining levers, and it is the single
highest-value hour available on this instrument.**

```bash
python3 -m src.research_infra.fast_engine.bench \
  --arm S1R1 --stop-after-day 2026-01-02 --prefix AX_VERIFY_B7_5_S1R1 \
  --patches abc_concrete_types,authority_hash_identity_memo,attribution_fields_identity_memo \
  --abc-symbols Mapping,MutableMapping,Sequence --verify \
  --out verify.json
```

Verify mode computes **both** answers everywhere and counts disagreements, so the
run is slower than baseline and its wall-clock means nothing — the `verify_report`
and `memo_report` are the output. It decides:

* **`attribution_fields_identity_memo`** — the largest node in the tree (288.4 s,
  26.2 %). Open hazard: in-place mutation of a candidate surface between calls,
  which is real, because rows are spliced during a day. Zero mismatches → turn it
  on. Non-zero → the count says exactly how unsafe it is.
* **`Sequence` in `abc_concrete_types`** — the other half of the 80.0 s abc
  target. Zero mismatches over the run's checks → turn it on.
(`authority_hash_identity_memo` needed no verify run — the concurrency run's
`memo_report` already settled it at a 0.11 % hit rate, and it is off.)

**H-AX-2b — the shipped default changed AFTER the A/B, and the receipt says so.**
`authority_hash_identity_memo` was ON when 594.3 s was measured and is now OFF,
because its own counters showed it net-negative (§0 finding 4). The P1-only
configuration has **not** been separately benchmarked. It is bounded below by the
measured figure — everything removed was net cost — but the honest statement is
"≥ 1.061×, not separately timed", and the first thing the next run should do is
close that by timing it.

**H-AX-3 — a fast lane is only worth what it is pointed at.** AW's separability
mine (`phase12/SESSION_AW_SEPARABILITY_MINE.md`, B1650–B1699) is the thing most
likely to produce a rule that wants sealed confirmation. When it does, the
confirmation campaign gets designed on this engine **plus** the pooled
promote/reject evaluator `JANUARY_BANK.md` §7.1 requires and which still does not
exist anywhere in the tree. That evaluator must be written and sealed *before*
any window runs, or the terminal decision gets improvised post-hoc — the
condition is unchanged by anything this session did.

**H-AX-4 — the bounded-window mode is a fixture mode and must stay labelled.**
`--stop-after-day` sets `engineering_stop_after_day`, which the sealed path
hardcodes to `None` (H5). Every bench receipt records the bound. No number
produced with it is an arm of record, and April still carries no partial credit.

**H-AX-4b — do not run two arms on this machine to save time.** Measured
(§4): 1.224× throughput for +4.39 GB of swap, a 1.62× per-arm slowdown, and one
of the two arms page-starved at 26.5 % CPU for much of the run. It completes and
it is correct, but on a machine shared with other sessions it costs more than it
returns. H3's ban survives — with a different reason than the one it was written
for, and now with a number.

**H-AX-5 — what this session did NOT do, deliberately.** No sealed window was
run. No bound file moved. No claim about any strategy family was made or
revisited. March stays outcome-unread.

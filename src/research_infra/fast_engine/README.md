# The fast sealed engine (`fast_engine`)

Session AX, wave 12, blocks B1700–B1749.

## What it is

A **runtime lane** over the frozen sealed replay engine. It imports the frozen
modules and accelerates them in place; it does not fork them, reimplement them,
or edit them. Every file here is new and **none of the 43 R2-bound paths change
by one byte** — which is the whole point, because a bound-file edit expires the
parked January comparability option (CLAUDE.md H1) at ~16.5 machine-hours per
window to restore.

## Why a runtime lane rather than a rewrite

The measured target is the evidence/attribution machinery: 60.6 % of the Python
heap at high-water (`THIRD_REVIEW.md` §A1) and ~60 % of wall-clock self-time
(the first audit's sampled profile), against ~8 % that decides trades. But that
machinery lives inside a 96,047-line bound module, and the expensive part turns
out to be **called by the decision path**, not merely written alongside it — see
"What measurement changed" below. A rewrite is a re-seal; a runtime lane is not.

## Using it

```bash
# one arm, bounded to a fixture window, frozen behaviour (the A/B baseline)
python3 -m src.research_infra.fast_engine.bench \
    --arm S1R1 --stop-after-day 2026-01-02 \
    --prefix AX_BASE_D2_B7_5_S1R1 --patches none --out base.json

# the same window on the fast lane
python3 -m src.research_infra.fast_engine.bench \
    --arm S1R1 --stop-after-day 2026-01-02 \
    --prefix AX_FAST_D2_B7_5_S1R1 --out fast.json

# is it the same answer?
python3 -m src.research_infra.fast_engine.reproduction \
    base_ECONOMICS.json fast_ECONOMICS.json

# N arms at once, with the memory cost measured rather than assumed
python3 -m src.research_infra.fast_engine.campaign \
    --arms S0R0,S1R1 --stop-after-day 2026-01-02 \
    --scratch /tmp/ax --out concurrency.json
```

Omit `--stop-after-day` for a full sealed month arm. **A day-bounded run is a
fixture, never an arm of record**: the sealed path hardcodes
`engineering_stop_after_day = None` (H5), and the bench receipt records the
bound so no reader can confuse the two.

## The patches

Each carries an identity argument, a verify mode that measures it, and a
`sealed_compatible` flag. `--verify` recomputes both answers on every use and
counts disagreements — that is how an identity argument becomes a measurement.

| id | default | sealed-compatible | what it does |
|---|---|---|---|
| `abc_concrete_types` | on | yes | rebinds `Mapping`/`MutableMapping` to `dict` in the five hot modules |
| `authority_hash_identity_memo` | **off** | yes | memoises the authority payload hash on payload object identity — **measured net negative**: 0.11 % hit rate over 52.0 M calls, ~0.2 s saved, ~5 s of `id()` lookups spent, +270 MB peak RSS. Correct (0 mismatches), just useless: the caller rebuilds the payload as a new dict each time |
| `attribution_fields_identity_memo` | **off** | yes | memoises the attribution-field projection; surfaces are mutated during a day, so it ships only on a zero-mismatch verify run |
| `skip_post_hoc_ledger_recertification` | off (`--evidence decision`) | yes | skips re-reading and re-certifying rows the run just wrote |
| `gc_during_chunk` | **off** | **no** | leaves cyclic GC on inside the day chunk |

`Sequence` is a *symbol* of `abc_concrete_types`, registered and off by default:

```bash
--abc-symbols Mapping,MutableMapping,Sequence   # after a clean verify run, not before
```

`str`, `bytes`, `range` and `memoryview` are Sequences and are not `(list, tuple)`.
At the hot call site the very next clause excludes `str`/`bytes`/`bytearray`, so
the two dispatches agree there — but 37 other `isinstance(..., Sequence)` sites
exist in the timewarp loop and 11 in the allocator, and one of the form
`if isinstance(v, Sequence): for item in v:` would iterate a string's characters
under `abc` and skip it under the tuple. Verify first.

**`--evidence` defaults to `full`, deliberately.** `full` reproduces the frozen
engine's evidence behaviour, which is what keeps the two lanes' outputs
diffable. The dial's whole measured headroom is 2.7 %, which is not worth making
the default the configuration that cannot be compared.

`gc_during_chunk` is sealed-incompatible for a specific, checkable reason:
`verify_denominator_to_deployment_execution.py:5161-5167` requires
`automatic_gc_enabled_before/after_explicit_collection` to be exactly `False`.
**The sealed contract pins GC off for the whole day chunk**, which is the same
window in which §A1 measured the heap ramp. Any real fix to the intra-day ramp
is therefore a contract regeneration, not a runtime flag.

## What measurement changed about the plan

The commission's premise was that the never-read evidence rows could be made
opt-in behind a dial for most of the win. The audit's own cumulative tree says
otherwise, and the difference matters:

* Writing the rows is **cheap** — `append_jsonl` 44.3 s and the post-hoc
  recertification 29.4 s, of 1102.3 s wall (6.7 % together).
* **Computing** the attribution is expensive — 288.4 s (26.2 %) inside
  `package_new_entry_authority_attribution_fields`, of which 210.4 s is
  re-hashing the authority payload.
* And the caller is `finalize_scheduler_risk_admitted_selection` (303.4 s) —
  **the B7.5 selection factor itself**, not an evidence sink.

So the `--evidence` dial's honest headroom is small, and the lever is the
computation the decision path invokes repeatedly. Measuring *that* moved the
target again: the authority payload hash runs **52.0 M times on a two-day
fixture — 5,902 per candidate — and 99.89 % of the calls see a payload object
nobody has hashed before**, because the caller rebuilds it as a new dict. The
repetition is logical, not referential, so an identity memo cannot touch it.

**The lever is the call count.** Cut it by memoising a level up (the attribution
projection does key on stable surfaces) or by not recomputing a digest the
caller already holds.

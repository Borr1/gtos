# Session HDF — second independent exit/capture science falsifier

## Disposition and findings first

**HDC is not safe as-is. It is scientifically safe to integrate only with HDF
commit `14c0e2ad1c4390ba78412832179d9b1e1dbf16f2`.** The repaired disposition is
`SAFE_ONLY_WITH_HDF_COMMITS`; `activation_authority: false`.

1. **HIGH — HDC's sealed capture authority was mutable and forgeable.** A frozen
   `GateSpec` retained caller-owned nested lists. Mutating the original capture,
   declaration-hash, or blackout list after construction changed the supposedly
   frozen object and its seal. `GateSpec.read` also accepted a missing seal, numeric
   zero in place of a seal, and a forged schema because it silently discarded the
   schema. Date parsing truncated aliases such as `2026-01-01junk`. HDF copies the
   authority into immutable tuples, requires exact ISO dates, validates the schema,
   and requires a lowercase full SHA-256 whose value matches the fields. Valid sealed
   legacy all-capture-fields-absent specs still round-trip with the same seal. A
   content-sealed symlink is harmless and was tested: target mutation is refused.

2. **HIGH — HDC's fast exit path skipped state transitions on the terminal
   observation.** If the final non-exiting point first crossed a partial trigger,
   HDC returned `gross=0.6`, `trigger_touched=false`, no partial, and full remaining
   size for `[0.1R, 0.6R]`; the row state machine and independent oracle return
   `gross=0.55`, trigger true, `0.25R` realized, and 0.5 remaining. For identity
   `[1.0R, 1.5R]`, HDC returned final protective floor `0.6R`; the row/oracle value is
   `1.1R`. A broader synthetic grid localized the remaining disagreements to terminal
   marks. HDF lets a terminal mark close only after the last observation completes
   trigger, partial, break-even, and giveback-ratchet state.
   Stop, active floor, deadline, and target observations still close before a new
   ratchet.

3. **MEDIUM — exact sign tails could lose mathematical ties to floating summation.**
   On sealed synthetic segments `((0.1,-1.0),(0.1,-0.1))`, direct enumeration has
   12 of 16 right-tail states; HDC counted 11. HDF bounds only floating accumulation
   error with a scale-aware comparison tolerance. This does not change CS's anchored
   tail (`2/2048`), but it prevents a finite randomization set from silently omitting
   tied transformations.

4. **MEDIUM — HC's published common-phase number is byte-reproducible but not the
   mathematical exact tail.** HC emits `13/6144 = 0.0021158854166666665` because one
   tied state is lost to sum order. Independent exact arithmetic gives phase tails
   `[2,2,10]`, hence `14/6144 = 0.0022786458333333335`. Both yield REJECT after the
   59-member bill. More importantly, the entire common-phase union is unsupported:
   no frozen declaration seals a circular phase, and coupling the same phase across
   three independently built captures is not the pre-existing sign-flip rule.

5. **HDC's central capture-start null correction is otherwise upheld.** The smallest
   ex-ante composition is one sign partition anchored at the first scored observation
   of each independently declared capture, with blocks restarting at every capture.
   No equally small competing prospective rule survived the frozen declarations.
   HDF independently reproduces HDC's CS `raw p=0.0009765625`, `q=0.0576171875`, and
   `ADMIT`. That favorable change is accepted because the rule was derived without
   consulting CS's sign or q-value and the economics, observations, and 59-member
   denominator are identical.

6. **HDC's broad `0 bad -> 0 bad` A/B did not test its attacks against HC.** The final
   byte-identical 17-node adversarial source produces 13 failures / 4 passes at exact
   HC, 7 failures / 10 passes at exact HDC, and 17 passes at exact HDF. The HC failure
   set includes duplicate-declaration acceptance, capture sealing, common phase,
   exact-tail ties, the 70 FC telemetry mismatches, and terminal accounting. All
   detached nodes are clean; no test bytes, command, or environment rule changed.

No opportunity, capture, trade, observation, family member, or candidate was removed.
No framework redesign, broad replay, March/live outcome read, runtime/config/broker/VPS/
token action, promotion, dossier, queue, merge, or push occurred.

## Frozen pre-edit falsification record

The initial version of this artifact was written before implementation edits. It
separated these outcome-blind hypotheses and stop rules:

- independently declared captures require complete identity, immutable ordered
  boundaries, no shared inclusive date, no blackout overlap, and a local fold/null
  restart; next-calendar-day adjacency alone is allowed;
- the pre-HC sign flip starts at observation zero, so every independently built
  capture supplies a new prospective origin; no circular phase prior was declared;
- existing stop, then active floor, then first deadline-eligible point act before a
  current trigger and target; a terminal mark follows the final non-exiting point's
  state transition;
- proof required direct finite enumeration, an independent observed-statistic
  calculation, a rebuilt 59-member BH bill, a third exit oracle over all shared
  fields, 214 historical FC identities, all 40 FC rejections, and byte-identical
  HC-vs-final tests;
- any equally small unresolved prospective rule, unexplained number, opportunity or
  denominator change, historical drift, forbidden outcome read, or same-test gap was
  a hard stop. None remains after HDF.

## Capture authority derived from sealed prospective information

The authority is the ordered declaration chain:

1. `CS_BREAKER_FOLD_PLAN_V1`, SHA-256
   `31b2ab756bf9be6ae19ca7f5e40447c2de7ea905839a78a921919ca3b5bb3b85`;
2. `CS_BREAKER_LOOK_ADDENDUM_V1`, SHA-256
   `5ab5414a4de6eb7b0ccf54f10bc2901673205120ac7754291026290303642174`;
3. `CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1`, SHA-256
   `94f4688dfa89a6998eaf44c25910be6b26052253a58fcd0ad3bf9c2b5d93f44b`.

It declares January 1–30, April 1–30, and May 1–30, 2026. March 1–31 is the
reserved blackout; February is excluded. Each capture independently applies the
unchanged equal-calendar builder: its first local half is train and only its scored
OOS half enters the pooled statistic. The observed scored dates begin January 16,
April 16, and May 18 and end January 30, April 30, and May 29. Segment lengths are
`[11,11,9]`.

April 30 followed by May 1 is valid: both immutable endpoints are declared and the
builder/null restart is explicit. A shared April 30 endpoint is overlap and fails.
Partial fields, empty/one-day/reversed/reordered/overlapping windows, blackout hits,
malformed or duplicate hashes, mutable aliases, runtime replacement, invalid segment
totals, empty segments, and post-seal file edits all fail. Whole-capture relabeling
leaves exact inference invariant. Arbitrary within-capture rotation is not an
equivalent label: it moves the sealed first OOS observation.

## Independent CS economics and null mathematics

### Opportunity and observed statistic

- raw records: `11,305`;
- RECORDED: `6,536` kept, `4,769` dropped, `0` unpriceable;
- broker-cost coverage: `1.0`;
- fold means: `[11.2523415098444, 7.453553638393435, 3.852045311094502]`;
- equal-by-fold pooled OOS mean: `7.519313486444113 R/day`;
- weighted 31-observation series SHA-256 after 12-decimal canonicalization:
  `dc5074e539897850eb9bd6426f533bb5953a3f5a25f1c8b037494008410c510a`.

The independent scalar implementation weights each capture so an ordinary mean of
the 31 values equals the mean of the three fold means. With block length 3, its local
block counts are `[4,4,3]`, for 11 signs and `2^11=2048` exact transformations. Two
states meet or exceed the observed statistic. The exact finite-sample p-floor is
`1/2048 = 0.00048828125`.

The separately reconstructed segmented centred circular bootstrap had zero of 10,000
draws at or above the observation, hence add-one `1/10001 =
0.00009999000099990002`. `both_conservative` takes the larger value, `2/2048`.
When the sign space exceeds the declared budget, HDF uses the frozen seed and add-one
Monte Carlo; a 20-block `2^20 > 64` known answer proved deterministic same-seed output
and an explicit `seed_effective=true`. Under exact enumeration, seed is non-operative.

### Every p/q delta

| Rule | Tail | Raw p | Rank / m | BH q | Critical p | Disposition |
|---|---:|---:|---:|---:|---:|---|
| Published continuous adjacency | add-one `26/10001` | 0.0025997400259974 | 1 / 59 | 0.1533846615338466 | 0.0016949152542372883 | REJECT |
| HC emitted common phase | `13/6144` | 0.0021158854166666665 | 1 / 59 | 0.12483723958333333 | 0.0016949152542372883 | REJECT |
| HC common phase, mathematical ties retained | `14/6144` | 0.0022786458333333335 | 1 / 59 | 0.13444010416666669 | 0.0016949152542372883 | REJECT |
| HDC/HDF capture-start anchor | `2/2048` | 0.0009765625 | 1 / 59 | 0.0576171875 | 0.0016949152542372883 | **ADMIT** |

The continuous calculation makes the end of one capture adjacent to the start of the
next and samples 10,000 sign vectors. HC removes cross-capture blocks but adds three
coupled circular phases. HDC removes that unsealed phase union and enumerates the one
anchored transformation group. HDF retains the HDC group and repairs only numeric tie
comparison, which does not move CS.

The frozen family source has 59 unique members, 57 looks, and exactly one billed CS
member. The fixed driver scores CS and preserves the remaining 58 declarations at
`p=1`; CS is rank 1. Direct BH reconstruction therefore gives `q=59*p`. No member,
look, alpha, threshold, capture, block length, cost, or economic value changes across
the last three rows.

The resulting ceremony remains
`RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED` /
`ACTIVATION_DOSSIER_REQUIRED_BEFORE_QUEUE`. HDF created no dossier and granted no
arming, queue, sizing, promotion, or live authority.

## Independent exit-path proof

The causal state machine is:

1. execute an already-resting hard stop;
2. execute an already-active protective floor;
3. execute the first deadline-eligible observation, capping favorable value at +2R;
4. otherwise update MFE and apply the one declared trigger action;
5. execute the hard target unless that timestamp is the executable deadline;
6. ratchet a giveback floor for the next observation;
7. after the last non-exiting observation completes steps 4–6, close at terminal mark.

The independent oracle covers target strictly before/after deadline, exact timestamp
collision, both synthetic M1 extrema orders, delayed deadline eligibility, favorable
gaps before/at/after deadline, adverse stop/floor gaps, partial accounting, break-even,
giveback, and terminal trigger/ratchet cases. Cost is deducted once after original-size
partial plus remaining-size exit accounting.

Against exact HC, the third oracle reproduces the requested **70 mismatches in 3,200**
fast/reference cases, all in shared state telemetry; reference matches the oracle.
HDC's prior floor-history repair reduces those 3,200 mismatches to zero, and HDF stays
at zero. HDF's new terminal cases reveal a separate HDC gap that the random 3,200 never
reached. After HDF, reference, fast path, and oracle agree on every shared field:
gross, net, reason, index, time, remaining-leg exit R, partial realized R, remaining
fraction, trigger state, MFE, protective floor, and source mode where shared.

## Historical FC and economic identity

The committed 214 time-box outcomes reproduce as 100 January and 114 February full
identities over month, candidate, decision time, symbol, side, and variant. Their
outcome/economic projection hash remains
`d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d`.
Gross/net identity, cost-once arithmetic, reason/time, daily aggregates, source-mode
counts, ambiguity counts, positivity counts, and full-dataset reason/trigger counts all
match the sealed result for every variant and bucket.

The five authority files remain byte-identical:

| File | SHA-256 |
|---|---|
| `OVERLAY_PROTOCOL.json` | `173b6be4dcd7a1e55248cd5f00dfcad4a09ebefd80b1739acc054ee04037f422` |
| `OVERLAY_RESULTS.json` | `106b3dfbe8e3e7c66e0c90ab27a81e8cebea973a1fb494e2cdccf38cac17d3ae` |
| `NULL_CONTROLS.json` | `07218f01fe33f5efafd502caf8963cbc5710d14f67ad9bbff7ad92d7e8c0b558` |
| `EXECUTED_OVERLAY_REPLAY.json` | `7e73e3d16d6f4ebbfec478d61e5cb449f41222ac8fab4defc253c6707a81ccf9` |
| `LOOK_MANIFEST.json` | `ca21eb4b58bc4342550542a8ca7d4d2b182c325fb33648c2dfcb34e9331bb147` |

The denominator remains 40. Thirty-seven cells remain outside the frozen selected
three; V17/V18/V19 still fail both executed and residual persistence. Zero cells are
positive across January train, January holdout, and February, and zero make the
combined 57-trade January executed book positive. Thus all 40 historical rejections
remain closed. No FC artifact was regenerated and no FC2 run was started.

## Exact same-test A/B

The full embedded `gtos-ab-receipt-v1` is
`phase20/receipts/SESSION_HDF_AB_RECEIPT.md`. The test SHA-256 is
`f404d464a6b5141856752f4d47999c64df7c4a1e9d576994b06358f60b4e3228`.

| Node | Passed | Failed | Errored | Exit | Real wall |
|---|---:|---:|---:|---:|---:|
| HC `82c41b122` | 4 | 13 | 0 | 1 | 7.64 s |
| HDC `32d045a73` diagnostic | 10 | 7 | 0 | 1 | 7.70 s |
| HDF `14c0e2ad1` | 17 | 0 | 0 | 0 | 7.65 s |

The identical command uses Python 3.14.4, pytest 9.1.0, `/dev/null` pytest config,
`PYTHONDONTWRITEBYTECODE=1`, and `$PWD` for `HDF_REPO_ROOT`, `PYTHONPATH`, rootdir,
and confcutdir. All three worktrees are clean and detached. Exact bad node identities
are embedded in the receipt; counts are not used as a substitute.

## Focused closure and change size

The independently selected closure ran the complete HDF adversary, exit-overlay,
FC, walk-forward gate, and CS fold modules: **163 passed, 0 failed, 0 errored** in
11.32 real seconds. Python compilation and `git diff --check` pass. JSON closeout
artifacts parse. No fixture hydration was needed. None of HDF's changed paths belongs
to R2's bound input lists; the one present-path R2 drift remains the pre-existing
`src/components/broker_net_cost_engine.py` drift.

Relative to HDC implementation/closeout, HDF changes:

- production `src/`: +116 / -4 lines (`spec.py`, `stats.py`);
- frozen FC analyzer: +15 / -7 lines;
- one auditable adversarial test source: +832 / -0 lines.

Relative to exact HC, the full HDC+HDF executable/analyzer delta is +226 / -94 lines;
tests are +1,744 / -25. The large HDF addition is test-only and contains the required
independent CS reconstruction, finite enumeration, third exit oracle, historical hash/
disposition proof, and cross-worktree import guard. No generic validation framework or
compatibility layer was added.

## Commits reviewed and created

Reviewed in ancestry order:

- `82c41b122364c4ef56612a5468867fe796bd6c1a` — HC closeout/builder head;
- `48a461ce290c13bc05124b693d1901bcc648bcb3` — HDC frozen plan;
- `ffff7542cd39e7f1546bc9d5cbecb580f73ecac0` — HDC implementation;
- `32d045a732467e439ba1807db0ce786e8a11e53b` — HDC closeout and HDF start.

Created:

- `14c0e2ad1c4390ba78412832179d9b1e1dbf16f2` — bounded implementation and
  adversarial proof;
- closing documentation commit — this result, exact A/B receipt, and completion JSON.

## Residual risks and boundaries

- Thirty-one OOS daily observations are enough for the frozen gate but do not prove
  live-path fidelity, activation readiness, size, payout, or stability at another
  broker/cost regime.
- Block sign flips assume block-level sign symmetry for bounded, skewed R. The separately
  segmented bootstrap remains in `both_conservative` and is smaller here.
- M1 replay bounds the two admissible extrema orders; it cannot reconstruct absent tick
  order.
- The original CS declaration did not literally name capture-start anchoring. It is the
  unique smallest composition found from the sealed origins and pre-existing algorithm;
  future declarations should state alignment before outcomes.
- HDF repaired future terminal behavior without a broad replay. Historical FC safety is
  bounded by the byte-identical artifacts, 214 time-box reconstruction, and unchanged
  40-cell dispositions, not a claim about unseen future paths.
- `GateSpec` sealing detects content change; it is not a permission or authenticity
  system. The declaration hashes remain the provenance authority.

`activation_authority: false`.

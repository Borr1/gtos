# `SleeveBookPolicy` validation receipt

**Session H deliverable 2.** Generated 2026-07-26. Reproduce with:

```bash
python3 scripts/validate_sleeve_book_policy.py \
  --out docs/audits/fable5-vision-audit-20260725/phase2/receipts
```

Machine-readable output: `receipts/SLEEVE_BOOK_POLICY_VALIDATION.json` (both modes, every disagreement
enumerated) and `receipts/SLEEVE_BOOK_POLICY_HARNESS_REPORT.json` (differential-harness verdicts).

---

## 1. What was compared, and why it is exact rather than approximate

The W7 book ran live on both funded accounts and wrote **99,112 runtime-learning packets** covering 38
unbroken days (2026-06-18 → 07-25; placements stop on 07-02). Each packet's `bridge` block carries the
**full flag set the cycle ran under**, the **`governor` decision**, and both **`would_units`** and
**`realized_units`** — the sized book itself (`bridge.py:378-385`).

That makes a bar-free, closed-form validation possible. A unit's `confidence` is a function of the
sleeve registry, the flags, the Kelly day-count and the de-risk multiplier — not of price. Its
`unit_risk_pct` is that confidence times the profile's nominal risk times the recorded governor
multiplier. So every number in a recorded unit is predictable from the record, and any disagreement is
a port defect, a live defect, or an evidence gap.

**The three machine-local inputs the export does not carry are each recovered from their own recorded
output, and the recovery is verified rather than trusted:**

| input | how recovered | check |
|---|---|---|
| governor equity / open risk | `size_cap_multiplier` inverted through the recorded `derisk_mode`; `available_gross_risk_pct` set as the cap with zero open risk | the policy's own `governor` output must equal the recorded one on all four fields, else the cycle is `EVIDENCE_GAP` and excluded — **but see the strength measurement below** |
| Kelly day-count | read verbatim from the unit's `kelly_lite_na{N}_x{M}` tag | a cycle carrying two distinct counts is reported, not forced (§5) |
| reactive de-risk state | inverted from `ladder_step{K}` / `coloss_breaker` tags | the resulting multiplier must reproduce the recorded `confidence` |

**How strong that check actually is, measured rather than asserted.** Mutating the reconstruction:
scaling `size_cap_multiplier` by 0.9 is caught on 138 of 617 cycles (that is float round-trip residue,
not semantics), and perturbing `available_gross_risk_pct` by +0.001 is caught on **zero** — because the
reconstruction sets the cap equal to the recorded headroom with zero open risk, so any recorded headroom
reproduces itself by construction. `reason` and `allow_new_entries` are genuinely checked. So the
headroom half of the governor recovery is an assumption, not a measurement, and since headroom is the
one number the gross-cap shed consumes, **this validation does not exercise the shed at all**. Stated
here rather than in a footnote; the first version of this receipt called the whole recovery "verified
rather than trusted", which was too strong.

Nine unit fields are compared: `cluster`, `sleeve_members`, `n_trades`, `confidence`,
`risk_pct_per_trade`, `unit_risk_pct`, `sized`, `reason`, `overlays_applied`. `overlays_applied` is
included on purpose — it is where a wrong Kelly bin or a missing ladder step shows up as a *labelled*
difference rather than only as a number that happens to be close.

**What is not validated, stated plainly.** Trade **side** — recoverable on only **7.19 %** of unit
packets across all three sources (defect **D4**), so the port's side selection is untested on the rest.
The gap is concentrated in non-placements: `unit_placed` carries the side 100 % of the time. **`stop_dist`** — not
recorded; it does not enter the risk-percent arithmetic at all (it is read once, to check `> 0`), and
lot conversion is downstream of every number here. The **A8 metals confluence gate** — the packets do
not record its feature fields, so it admits identically on both sides and the gate is unexercised (see
the mutation control, §4). The **15 placement gates** — those are placement, not decision, and need a
broker tick and a durable ledger; the comparison is against `would_units`, the book's own
pre-placement decision, so it is like-for-like.

---

## 2. Result — supplied-count mode (isolates the sizing chain)

| | count |
|---|---:|
| cycles grouped from the packet stream | **5,209** |
| cycles compared | **4,923** |
| **cycles matching, exact intent recovery** | **4,908** |
| cycles matching, partial intent recovery | 15 |
| **cycles disagreeing** | **0** |
| cycles with two Kelly day-counts (reported, not compared) | 1 |
| cycles that could not be reconstructed | 285 |
| units compared | 677 |
| units compared under exact intent recovery | **647** |
| field differences on co-present units | **0** |

**Every unit present on both sides matched on all nine fields. There are no disagreements to
enumerate.** 15 units live sized that the policy did not produce, and all 15 are attributed to a
measured cause: the packet stream does not emit one packet per intent, so for those cycles the intent
set is incomplete and a whole unit's constituent intent was absent (§3).

### Read the unit-bearing count, not the cycle count

The cycle count above is the wrong headline and would flatter the result if left to stand. Of the 4,908
matching cycles, **4,306 are empty cycles** — live sized nothing and the policy, invoked on the same
empty candidate set, also sized nothing. Those are genuine comparisons (an empty cycle is where a port
that hallucinated a unit gets caught) but they are trivial ones.

**The load-bearing claim is the unit-level one: 677 units across 617 unit-bearing cycles, zero
disagreements.** 647 of those units are under exact intent recovery.

**A measurement error, found by adversarial review and fixed.** Until 2026-07-26 the empty-cycle branch
returned `MATCH` *before constructing the policy at all* — so 4,306 of the 4,908 reported matches were
free greens on a comparison that never ran, exactly the failure the code's own comment warned against
two lines above the code that committed it. The branch now invokes `SleeveBookPolicy` on the empty
candidate set and requires it to produce no units; all 4,306 do, so the number is unchanged and now
earned. Anywhere this receipt quotes a rate, the denominator is the **617 unit-bearing cycles**, not
4,923.

### Coverage — 15 of 29 sleeves, and the five highest-confidence ones are not among them

| | count |
|---|---:|
| sleeves in the live effective registry | 29 |
| sleeves that appear in any recorded `would_units` | 18 |
| **sleeves covered by a matched unit** | **15** |
| clusters covered | 10 of 13 |
| decision days covered | 30 of 30 |

Covered: `asia_pdl_fade`, `asian_fade`, `fx_jpy`, `fx_jpy_ny`, `idxrev`, `kz_london_crypto_low`,
`liq_asia_up_low_metal`, `metal_session_reversion`, `ny_crypto_momentum`, `orb_crypto_london`, and five
`mx_*` sleeves.

Fired live but not covered (their cycles fell into gap classes): `vol_compression`,
`mx_btcusd_d1_donchian_20_breakout`, `mx_ethusd_d1_donchian_20_breakout`.

**Never fired live at all, therefore validated only synthetically:** `metals_core` (confidence 1.00),
`crypto` (0.85), `energy_agri` (0.80), `metals_softband` (0.50), `metals_ob_micro` (0.30),
`vss_fxcross_london_up_low`, and five `mx_*` sleeves. The book's five train-validated,
highest-confidence sleeves have **no live evidence to validate against** — they placed zero trades in
38 days. Their sizing chain is exercised in this session only by unit tests, which drive the *live*
functions with synthetic candidates and are mutation-proven, but that is a weaker claim than the
live-evidence one and is not the same claim.

That absence is itself the session's largest finding; see **D0** in `SLEEVE_BOOK_DEFECT_REGISTER.md`.

## 3. Where the 285 unreconstructable cycles and 15 missing units come from

Intent recovery, measured against each cycle's own recorded `n_candidates_in`, over the 884 cycles that
carry `would_units`: **332 exact**, **437 excess**, **115 short**. "Excess" is my grouping merging
adjacent re-emissions of one bar under an identical `bridge` digest; "short" is the packet stream
emitting fewer unit packets than the cycle had intents. The fidelity claim above is stated on the
exact-recovery subset, and the other two are given their own class rather than folded into a match rate.

| gap reason | cycles |
|---|---:|
| `decision_day_not_unique:[]` — packets carry no `decision_day`, so the Kelly day key is unresolvable | 241 |
| `candidates_present_but_no_would_units_in_record` | 19 |
| `decision_day_not_unique` with **two dates** (D2's signature) | 25 |

The 25 two-date cycles are the same phenomenon as §5 caught one cycle earlier in the pipeline: a cycle
whose packets span two `decision_day` values cannot have one Kelly day key resolved from the record.

## 4. The zero is proven discriminating

"Before trusting any zero, prove your probe can see the thing it searched for." Six single-flag
mutations were applied to the config the policy replays, over the first 600 cycles:

| mutation | cycles differing | fields flagged |
|---|---:|---|
| none (control) | **0** | — |
| `kelly_conservative` → False | 105 | `confidence`, `risk_pct_per_trade`, `unit_risk_pct`, `overlays_applied` |
| `profile` → `clean3_w7_measured_nom1p25` | 105 | `risk_pct_per_trade`, `unit_risk_pct` |
| `stress_derisk` → False | 105 | `confidence`, `risk_pct_per_trade`, `unit_risk_pct`, `overlays_applied` |
| `include_clean3` → True | 0 | — |
| `drop_w7_symbols` → False | 0 | — |
| `metals_confluence_gate` → False | 0 | — |

Four of six discriminate, and the three nulls each have a measured explanation rather than being
unexplained: clean_3 sleeves **cannot generate live** so none appears in the sample; no `HEATOIL_c` /
`NATGAS_cash` intent appears in the sample; and the A8 gate admits featureless intents identically both
ways because the packets do not record its features. The three nulls are therefore themselves evidence
about what this validation covers, and they are reported as coverage limits in §1.

The **test suite** is separately mutation-proven: five mutations to the live sizing module
(`KELLY_LITE_BINS_HALF` top bin, `STRESS_DERISK_MIN_MULT`, `LADDER_STEPS`, gross-cap enforcement
removed, the smooth de-risk curve flattened) each fail 1–4 tests, and the golden test catches two of
them independently. 52 tests, all passing.

## 5. Result — derived-count mode: the running-conviction store decides sizing on four sized cycles in five

Re-run withholding the recorded Kelly count so the sizer computes it from the cycle's own intents, as
it would with no persisted running-conviction store:

| | supplied | derived |
|---|---:|---:|
| unit-bearing cycles compared | 617 | 617 |
| **unit-bearing cycles disagreeing** | **0** | **482** |
| **as a share of unit-bearing cycles** | **0 %** | **78.1 %** |
| field differences | 15 (`__present__` only) | 2,075 |

**482 of the 617 unit-bearing cycles — 78.1 % — size differently** without the persisted count, and the
differences are on `confidence`, `risk_pct_per_trade`, `unit_risk_pct` and `overlays_applied`: real size
changes, not labels. This is the running-conviction divergence quantified, and it is the dominant
divergence in the whole comparison by two orders of magnitude (2,075 field differences vs 15).

**Corrected 2026-07-26.** This was first published as "9.8 % of cycles", which divided by all 4,923
compared cycles including the 4,306 empty ones where the policy sizes nothing and withholding a Kelly
count cannot change anything. Adversarial review caught the denominator. Against the cycles that
actually size, the true rate is **78.1 %** — the error understated the finding roughly eightfold. Of the
602 previously-matching unit-bearing cycles, **469 flip to disagreement**.

All 482 are enumerated in `receipts/SLEEVE_BOOK_POLICY_VALIDATION.json` under
`derived.disagreements`. Their structure, so the shape is legible without opening a 1 MB file — every one
is a Kelly-bin difference and nothing else:

| policy multiplier (derived) | live multiplier (recorded) | live / policy | units |
|---:|---:|---:|---:|
| 0.748 | 1.241 | **1.659×** | 315 |
| 0.748 | 0.991 | 1.325× | 132 |
| 0.991 | 1.241 | 1.252× | 66 |
| 0.991 | 0.991 | 1.000× | 8 |

The count differences behind them are almost all "one sleeve fired this cycle, many fired today":
policy na=1 against live na=2 (87 units), 3 (45), 4 (89), 5 (78), 6 (75), 7 (39), 8 (20), 9 (13).

The direction is uniform: the derived count is never higher, because `na = max(per_cycle, running)`
(`admission.py:1145-1146`) clamps upward only. So a replay without the store **under-sizes**, by a median
factor of **1.66×** on the affected units — it never over-sizes. That is the safe direction for a live
guard and the wrong direction for a measurement: an economic result computed without the store would
understate the book's realised risk, and therefore overstate its risk-adjusted return.

The 8 units at ratio 1.000 are label-only: derived and recorded counts land in the same half-Kelly bin
(e.g. na=2 vs na=3, both 0.991), so `overlays_applied` differs while no number does. They are counted as
disagreements rather than waved through, because the tag is the audit trail.

**Consequence for Phase 2.** `pipeline_state/ultimate_book/<namespace>/firing_sleeves.json` is not
incidental runtime state; it decides sizing on roughly four sized cycles in five. The live book's entire
Kelly tilt above the bottom bin comes from it — the dominant derived value is na=1 (×0.748) against live
counts of 2–10. Any replay of this book that does
not carry it forward will mis-size those cycles, and will do so *silently* — the per-cycle count is
always a valid count, just a smaller one. `AccountDayState.cycle["n_active_override"]` exists to make
that input explicit, and `SleeveBookPolicy` reports in every decision whether it was supplied.

## 6. Independent confirmation via the differential harness

`src/research_infra/replay_differential_harness.py` (Session D, B46–B50) was run over arm-shaped
ledgers written from the same results — identity alignment on the unit identity key, `order` role,
values exposed.

| comparison | verdict | matched rows | rows with differences | left-only | right-only | unknown differences |
|---|---|---:|---:|---:|---:|---:|
| **null control** (policy vs itself) | **EQUIVALENT** | 662 | 0 | 0 | 0 | 0 |
| **policy vs live** | **DIFFER** | **662** | **0** | **0** | **15** | **0** |

The null control returning EQUIVALENT is what makes the second row mean anything: comparator and
serialisation are sound. The policy-vs-live verdict is **DIFFER**, and that is reported as-is rather
than softened — the harness blocks `EQUIVALENT` on any unmatched row, and there are 15. But **0 rows
with differences and 0 unknown differences**: every unit present on both sides is identical under the
harness's own canonical comparison, and the entire residue is the 15 units whose intents the packet
stream did not record.

Two independent comparators, built on different alignment logic, agree: **row-exact on all 662
co-present units.**

## 6b. The placement half: the risk percent actually sent to the broker

§1-6 compare the *decision*. The brief's validation target also names the **placement ledgers**, so the
loop is closed end-to-end here.

The 150 W7 trade records carry
`instrumentation.risk_pct_override` — the risk percent the order router actually transmitted, which is
`round(risk_pct_per_trade * 100, 8)` (`execution_packets.py:215`). 147 carry it (the other three are
adopted pre-existing positions, `reconstructed_from_sleeve_identity: true`). Joining on
`(namespace, sleeve, symbol, decision_bar_iso)`:

| | count |
|---|---:|
| placements with a comparable policy decision | **132** |
| **transmitted risk % reproduced exactly** | **130** |
| transmitted risk % not reproduced | **2** |
| placements whose cycle fell into a gap class | 15 |

The 2 are explained rather than left as residue. Both are `idxrev`/JP225 on decision bar
`2026-06-28T21:00:00+00:00`, and that bar was re-evaluated on ~20 successive cycles between 01:11 and
01:38 UTC as equity drifted, with `size_cap_multiplier` moving 0.5828 → 0.5906 and the sized risk moving
with it. The transmitted values — 0.105962 % and 0.104044 % — appear **verbatim** in the recorded
`would_units` of the cycles at `01:13:50.721800` and `01:13:50.691840`. Those two cycles are classified
`EVIDENCE_GAP` by the validator because their packets carry **two** `decision_day` values
(`['2026-06-28', '2026-06-29']`) — the D2 signature at the 21:00 UTC boundary — so they are excluded from
comparison by the same fail-closed rule that excludes the other 24 two-date cycles.

So there is no unexplained placement. Every transmitted risk percent either matches a comparable
decision exactly, or matches a decision in a cycle the validator deliberately refused to compare.

**A measurement error found and corrected on the way.** The first version of this join took `max()` over
the candidate cycles for a `(sleeve, symbol, bar)` key. Because a bar is re-evaluated across many cycles
as the governor multiplier drifts, `max()` systematically picked the largest — hence the earliest, least
de-risked — decision, and produced 21 apparent mismatches whose ratios (policy/live) were all > 1 and
spread continuously from 1.0005 to 1.688. That spread was the artifact's signature: a real defect would
not scale smoothly with drawdown. Corrected to "does any candidate cycle match", the count went 111 → 130
and the residue became explainable. The `max()` was mine, not the book's.

## 7. Gate G2, honestly assessed

G2's clause for this lane is "the book policy reproduces the VPS shadow-packet decisions over a sampled
week" (`FULL_VISION_PLAN.md:226-231`).

**Met, and exceeded in scope — with three stated limits.** Not a sampled week but the **whole 38-day
packet window**: 4,923 cycles, 647 units under exact intent recovery, zero disagreements, confirmed by
two independent comparators, plus 130 of 132 transmitted broker risk percents reproduced exactly (§6b) —
so the loop closes from decision through to the order that was actually sent.

The limits, stated rather than buried:

1. **The 15 post-sizing placement gates are not applied** (`sleeve_book.PLACEMENT_GATES`). They need a
   broker tick and a durable ledger. §6b tests the risk percent that survived them, not the gates.
2. **Coverage is 15 of 29 sleeves**, and the five highest-confidence ones are not among them — they
   placed zero trades in the window (D0), so live evidence for them does not exist. They are exercised
   only by the mutation-proven unit tests.
3. **Side, `stop_dist` and the A8 gate are untested**, for the reasons in §1 — not unreported, untested.

The other two G2 clauses — the `BroadV4Policy` slice reproducing a sealed symbol-day, then a full
January arm — are **not** addressed here and remain open. **G2 is not met overall.**

## 8. One correction to the session brief, recorded because it changes the framing

`SESSION_H:22-24` says "OD-1 named the `ultimate_book` W7 book as the activation candidate". That is
backwards. `FULL_VISION_PLAN.md:42-47` [VERIFIED] records OD-1 as decided: the book went live
2026-06-18 → 07-02, drew down (FTMO ≈ −5.3 %, FN ≈ −3.0/−3.9 %), and Borhen **deactivated it and chose
the current broad system as the activation candidate**; W7 "is retained cheaply as a
benchmark/challenger policy inside the policy-plural core".

The module's value survives the correction, and arguably improves. It is not the activation candidate's
replay. It is (a) the only representation any replay has ever had of the declared-live surface, which
is what closes F1 by construction; (b) the non-trivial baseline the Phase-4 walk-forward gate needs;
and (c) — the part the brief could not have anticipated — **a faithful, validated re-execution of the
exact book that lost money on two funded accounts**, which is the instrument the Phase-1 W7 forensics
lane needs to attribute *why*. A challenger you can replay exactly is worth more than a challenger you
merely retain.

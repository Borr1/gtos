# BH PADDING REPAIR — the gate now runs the standard it documents

**The defect Lane B named is real, it is fixed, and fixing it resurrects nothing on its own.**

Both halves matter. The estate's admission standard was **documented as Benjamini-Hochberg
FDR at α = 0.10** (`options.py` Option B) and **delivered as Bonferroni FWER at α = 0.10**,
because `gate.py:1104-1109` padded every declared-but-not-judged family member at `p = 1.0`.
That is now repaired: BH runs over the real p-values of members actually tested, un-run
members are carried in the denominator without a fabricated observation, and every verdict
publishes whether its BH result is arithmetically Bonferroni.

Then the repair was run over the whole estate with every family held exactly as declared.
**One of Lane B's four destroyed findings flips — `sub_xvol_pullback`'s exit repair, on a
sleeve armed today — and only at the smallest bill its own receipt publishes.** 78 cells flip
at each look-set's *declared* family size; **zero survive at the same receipt's
`n_cells_gated` or `trial_ledger.n_trials`,** where the step-up returns `k = 0` in every
case. The unidentified-bill problem (Lane B §3.1 — seven simultaneous bills spanning 543×) is
untouched by an arithmetic repair, and it is what actually decides every one of these
verdicts.

| receipt | what it establishes |
|---|---|
| `bh_padding_repair/BH_PADDING_READJUDICATION_V1.json` | 2,361-row census re-adjudicated through the repaired production function; 78 flips at the declared bill, 0 at the larger ones; **0 of 7 negative controls change verdict** |
| `bh_padding_repair/bh_padding_readjudication.py` | the driver, reproducible from a clean checkout |
| `tests/research_infra/test_bh_padding_repair.py` | 38 behavioural tests: textbook BH, the identity against committed receipts, the padding path proved unreachable, the negative controls, the degeneracy stamp, the spec/gate/declaration refusals |

---

## 1. What the corrected gate does

### 1.1 The arithmetic

Struck from `gate.py`:

```python
n_padded = effective_family - len(fam_names)
padded_p = list(fam_p) + [1.0] * n_padded
corr = S.benjamini_hochberg(padded_p, spec.alpha)
```

Replaced by a family size that travels as a **separate argument** from the observations:

```python
observed_p = list(fam_p) + [p for _, p, _ in (spec.declared_family_p_values or ())]
corr = S.benjamini_hochberg(observed_p, spec.alpha, family_size=effective_family)
```

`stats.benjamini_hochberg` and `stats.bonferroni` both take `family_size` now, defaulting to
`len(pvalues)` so every existing call is unchanged. `k` counts ranks among the **observed**
p-values and can never exceed them: an untested hypothesis is not a discovery, false or
otherwise.

### 1.2 The accounting for declared-but-unrun members, and why it is defensible

Three classes, three treatments:

| class | treatment |
|---|---|
| **JUDGED HERE** — p computed in this run | enters the step-up with its real p |
| **DECLARED, KNOWN ELSEWHERE** — a sibling tested in another run, carried prospectively in the new `GateSpec.declared_family_p_values` as `(member_id, p_raw, source)` | enters the step-up with its real p. **This is the repair** — it is the only class that can lift `k` above 1 |
| **DECLARED, NOT RUN** — no p-value exists anywhere | occupies a denominator slot, contributes **no observation** |

**`m` stays `max(n_judged, declared_family_size)`. The ratchet is untouched and the bill is
never shrunk.** That is the load-bearing choice and it is deliberate. The alternative — `m` =
the number of tests actually run — would make every single-candidate gate `m = 1` and
therefore uncorrected, which is the exact abuse the declared family exists to stop
(`gate.py`'s own measurement: submitting 20 zero-edge sleeves singly takes P(≥1 junk
admission) from 8.3 % to 71.7 %).

So the answer to *"can unrun members contribute to a BH correction at all?"* is split, and
the split is the whole point: **they contribute to the denominator and they cannot
contribute a p-value.** Padding at 1.0 conflated those. A p-value of 1.0 is an *observation*
that a test ran and came back maximally uninformative; asserting 58 of them is a claim about
data nobody has. Removing the claim leaves the bill exactly where it was.

**Statistically this is conservative, not permissive.** BH's bound is `FDR ≤ α·m₀/m`. Padding
`u` un-run members inflates `m` while adding no rejections, so the achieved control is
`α·m₀/(n+u)` — for the estate's `n=1, u=58` that is α/59, i.e. **a standard 59× stricter than
the one documented**. The repair does not loosen α; it stops silently multiplying it.

### 1.3 It is a strict generalisation — nothing published moves

With no sibling p-values supplied, BH over the real p-values at `family_size=m` is
**arithmetically identical** to BH over the padded vector, on every field a verdict reads. A
padded 1.0 can never satisfy `1.0 ≤ α·rank/m` for any `rank ≤ m` while `α < 1`, so it never
entered `k`; and the q-value running minimum starts at 1.0 either way.

Verified three ways:

* **20,000 random families** (n ∈ 1..6, m ∈ n..n+70, α ∈ {0.05, 0.10, 0.20}, p-values
  including the 0.0 and 1.0 edges): **0 mismatches** on `k`, `m`, `threshold`, `rejected` and
  `qvalues`. Pinned as a test at 12,000 families across 6 seeds.
* **The CS receipt reproduces to 1e-15.** `benjamini_hochberg([0.0025997400259974], 0.10,
  family_size=59)` returns `q = 0.1533846615338466`, `k = 0`, `threshold = 0.0` — the
  published values exactly, and identical to `bonferroni` at the same inputs. That identity
  *is* the finding.
* **Every published `family.multiplicity` block in the audit tree** — **44 blocks, 2,989
  rows, 0 mismatches** — recomputed from its members' real p-values at its own published `m`
  and required to reproduce the published q-vector, `k` and `threshold` exactly. That covers
  the multi-sleeve runs where the step-up genuinely stepped, the degenerate single-candidate
  ones, and the Bonferroni blocks
  (`test_every_published_estate_family_block_is_unchanged_by_the_repair`).

The seal is preserved the same way `declared_family_id` was: `declared_family_p_values` joins
`_ABSENT_MEANS_UNCHANGED`, so `None` is invisible to `canonical()` and every seal published
before the field existed reproduces byte-for-byte. An **empty tuple is refused**, because it
would behave identically to `None` and break the invariant that no set value means what
`None` means.

### 1.4 The degeneracy is now disclosed on every verdict

`gates.significance` gains `family_members_observed`, `family_members_unobserved`,
`family_siblings_supplied`, `step_up_k`, `rank2_threshold` and
**`degenerate_equals_bonferroni`**. The last fires when `k ≤ 1`, which is exactly when BH's
rejection set equals Bonferroni's, and the note then says so in words: *"read it as FWER
control, not FDR control."*

> **A bug found in this repair's own first draft, kept here because it is instructive.** The
> stamp initially fired when "fewer than two observed p-values sit at or below the rank-2
> bar". That is wrong: **BH takes the largest rank satisfying `p_(r) ≤ α·r/m`, not the
> first**, so `k` can be 42 while ranks 1 and 2 both fail their own bars. Measured on
> `EXIT_FRONTIER_V1`'s 61-cell grids, which reach k=42 with zero p-values below the rank-2
> bar — the wrong stamp called them degenerate, hiding real FDR work. Fixed, and pinned by
> `test_a_high_k_family_whose_low_ranks_fail_is_not_stamped_degenerate`.

**46 of the estate's 51 look-sets are still degenerate** after the repair. That is not a
failure of the repair — it is the measurement the repair makes visible. The gate can now say
which procedure decided.

### 1.5 The sibling channel cannot become a lever

Six refusals in `GateSpec.__post_init__`, each closing a route by which a retrospective
assembly could pretend to be a prospective one: an empty tuple; siblings without a
`declared_family_id`; more siblings than the family charges; a duplicate member id; a p
outside [0,1] or non-finite; a row missing its `source`. A seventh lives in `gate.py`,
because it is the first place both sets are in scope: **a sibling p-value for a member this
run also judges is refused** — one member is one look, and counting it twice buys a free
extra rank at the same `m`. The stats layer refuses a family smaller than its own evidence
as a third line. And the field is **sealed** — five materially different assemblies produce
five different `spec_sha256`, so a verdict that used sibling p-values names them in its hash.

> **An adversarial pass on this section caught the claim it was making, and it was too
> strong.** The first draft of `spec.py`'s comment said the field *"can only ever be supplied
> for members that are ALREADY declared, so it cannot smuggle a new hypothesis in."* Nothing
> enforced that: a `GateSpec` does not know what the declaration contains, so `spec.py` can
> only check that a row is well-formed. **`candidate_family.with_family_p_values()` is the
> accountable path** and now makes the claim true, refusing three things a bare spec cannot
> see:
> * **a non-member** — a new look admitted at no extra bill;
> * **a WITHDRAWN member** — the ratchet keeps it in the *denominator*, correctly, but a
>   withdrawn look must not also lend its p-value to a neighbour's rank. Denominator yes,
>   evidence no;
> * **a `look_taken=False` member** — it produced no trade, so it has no null; a number
>   attached to it is fabricated by construction, which is the defect being removed.
>
> The claim in `spec.py` is now stated as what it is: a property of the accountable path, not
> of the field.

**The check that does NOT exist, and it is the important one.** Nothing can verify that a
sibling's p-value was measured at the **same standard** as the candidate's — same population,
spread band, cost artifact, exit contract. The estate has never assembled its family's
p-values at one comparable standard (Lane B §5, Option 1). Until it has, a BH step-up mixing
standards ranks quantities that are not exchangeable. This is documented at the function and
is the reason §3.2's breaker flip is stated as conditional rather than as a verdict.

**It cannot change `m`.** Twenty uninformative siblings leave the bill at 59 and the verdict
unchanged (`test_a_sibling_cannot_shrink_the_family_or_change_the_bill`).

---

## 2. The negative-control result: 0 of 7, and it is an identity

`phase5/receipts/W_NEGATIVE_CONTROLS.json`, six constructed adversaries plus one positive
control, re-adjudicated through the repaired function: **0 verdicts change, and all 7
q-values reproduce to 1e-12.**

The reason is stronger than "no change was observed". Both control runs published
`family_members_padded_at_p1: 0` and `declared_family_size: null` — six real p-values in a
family of six (`k = 2`, `threshold = 1/30`), one in a family of one. **They are the only runs
in the estate where BH was already running as BH.** A repair that only removes fabricated
p-values cannot move a family that had none.

| adversary construction | raw p | first failing gate, before and after |
|---|---:|---|
| shuffled labels, zero expectancy | 0.2689 | lifetime |
| random entry, matched vol, zero edge | 0.9650 | expectancy |
| cost-eaten: gross-positive, net-negative | 1.0000 | expectancy |
| day-clustered noise, zero edge | 0.3830 | robustness |
| one-regime: all edge in a single year | 0.0001 | **stability** |
| shuffled labels, positive expectancy by construction | 0.0015 | admitted, correctly |
| positive control | 0.0001 | admitted, correctly |

A second, independent control is generated inside the test rather than read from a receipt:
a zero-expectancy NZDJPY series run through the live `run_gate` with **thirty siblings at
p = 1e-9**, the most generous family the new channel can express. The step-up reaches
`k ≥ 30`, the significance gate passes — and the sleeve is still **not admitted**, stopped by
an economic gate. That reproduces Lane B's §6.1 finding as a test: *significance has never
been the gate that stopped a known-null series in this estate.*

---

## 3. Re-adjudication — the full flip list

### 3.1 The rule, and what it refuses to do

The commission forbids re-declaring or re-sizing the family. So:

> **RULE R.** For each look-set `G` with published family size `m_pub`:
> `m = max(m_pub, |G|)` — never shrunk; observations = every real p-value in `G`;
> `m − |G|` declared members carried in the denominator with no p-value; correction by the
> **production** `stats.benjamini_hochberg`.

Recovering `m_pub` is load-bearing and easy to get wrong. Most grid receipts store `gates` as
bare booleans and carry the bill elsewhere — `EXIT_FRONTIER_V1` and `AK_EXIT_FRONTIER_V2`
both publish `gate.declared_family_size: 69`, AL's rows carry `effective_family_size: 35`.
Taking the fallback `|G|` instead would have charged the 61-cell frontiers **61** rather than
69, which is a re-sizing. It changes the answer materially, and the receipt prices both:
**118 flips at `|G|`, 78 at the published bill.** The 78 is reported.

The census is **Lane B's, imported unchanged** from `lane_b_readjudication.py`, so any
difference in the result cannot come from a difference in the population: **2,895 verdict
rows scanned, 2,361 in census after exclusions, 310 significance-only failures**, 51
look-sets — every figure identical to Lane B's. And the 118 is Lane B's own headline flip
count reproduced exactly, which is the check that the only thing separating the two
re-adjudications is the family size, not the method.

### 3.2 The four Lane B named as destroyed

| candidate | Lane B | **under the repaired gate at the published bill** | at the larger bill |
|---|---|---|---|
| `cq_current_breaker_re_entry_inverted_5d_stop_0p25d` | destroyed | **REJECT — unchanged** | REJECT |
| `sub_xvol_pullback` exit repair (**ARMED sleeve**) | destroyed | **ADMIT** (32 of 59 sig-only rows flip) | **REJECT** |
| `mx_ethusd_d1_donchian_20_breakout` | destroyed | **REJECT — unchanged** | REJECT |
| `thr_sub_xvol_pullback_vr14_s150_ac015` | destroyed | **REJECT — unchanged** | REJECT |

**Three of the four do not flip, and the reason is that Lane B re-sized their families and
this re-adjudication does not.** `mx_ethusd`'s best cell is p = 0.006399 in a 61-cell grid
charged 69: its own grid's step-up reaches `k = 0`, so it stays rejected. At `|G| = 61` it
would flip. That difference is the family-size question, not the padding question.

**The breaker is the cleanest case and deserves its own statement.** Its look-set has exactly
**one** real p-value against a declared family of 59. Removing the fabrication changes
nothing, because there is nothing to rank it against:

```
p_raw          0.0025997400259974
rank-1 bar     0.0016949  (α/59)   -> fails
rank-2 bar     0.0033898  (2α/59)  -> CLEARS
repair alone   k=0, threshold=0.0, q=0.1533846615338466  -> REJECT, unchanged
```

**The repair's lever is the assembly, not the arithmetic.** Supply one real declared sibling
at or below the rank-2 bar and BH reaches `k = 2`:

| sibling (declared row 15, `mx_btcusd_d1_donchian_20_breakout`) | source | k | threshold | breaker q | verdict |
|---|---|---:|---:|---:|---|
| p = 0.0006999300069993 | `phase6/receipts/AA_ESTATE_WALK.json` → `runs["B_balanced\|v1_1_zero_carry"].rows[14]` | 2 | 0.0033898 | **0.0766923** | significance PASSES |
| p = 0.0010998900109989 | `phase9/receipts/ADMISSION_CLOSER_V1.json` → `answer.lowest_p_raw_reached` | 2 | 0.0033898 | **0.0766923** | significance PASSES |

That is Lane B's central arithmetic, verified independently and computed by the production
function. **But the assembly has not been done**, and doing it retrospectively — reading
sibling p-values after the outcome is known — is the family-choice defect in a new costume.
The gate now *can* consume a prospective assembly; nobody has produced one.

### 3.3 The full flip list, with the caveat class for each

**78 cells flip, across 4 look-sets, collapsing to 3 distinct candidates.** Plus 3 short-list
cells excluded from the headline (`AK_CANDIDATE_DOSSIER_V1::candidates` is a four-finalist
dossier whose own receipt publishes `trial_ledger: 5734`; charging it a family of four is the
defect in the permissive direction).

| # | look-set | flips | best cell | p | q published → repaired | pooled OOS | n |
|---|---|---:|---|---:|---|---:|---:|
| 1 | `EXIT_FRONTIER_V1::mx_btcusd_d1_donchian_20_breakout` | 41 | `5R_nobe` | 0.004700 | 0.2104 → **0.03975** | +0.2644 R/day | 318 |
| 2 | `AK_EXIT_FRONTIER_V2::sub_xvol_pullback` | 29 | `as_walked` | 0.006099 | 0.4140 → **0.06842** | +1.0264 R/day | 88 |
| 3 | `AL_CANDIDATE_DOSSIER_V1::mx_btcusd_d1_donchian_20_breakout` | 5 | `RECORDED\|as_walked\|mid` | 0.006399 | 0.2100 → **0.07466** | +0.3894 R/day | 232 |
| 4 | `AL_CANDIDATE_DOSSIER_V1::sub_xvol_pullback` | 3 | `ALL_ERAS\|as_walked\|mid` | 0.005799 | 0.2030 → **0.09332** | +1.0438 R/day | 88 |

**Every flip is an admission to incubation, never to capital.** Per-candidate caveats:

**`mx_btcusd_d1_donchian_20_breakout` (rows 1 and 3) — not a new finding.** The estate
already admitted this candidate by another route and it is **live on FTMO since 2026-07-31 at
registry confidence 0.025**. The flip adds exit cells, not a candidate. Caveat class: its
admission decays chronologically (AN: recent folds +0.198 R/day = 13.2 % of the early folds'
+1.504) and no gate can see decay by construction; and 41 of the 61 flipped cells are *the
same trades under different exit rules*, so the count overstates the finding ~41×.

**`sub_xvol_pullback` (rows 2 and 4) — the one with money on it today, and the one that most
needs reading carefully.** It is one of the three armed sleeves. The flip says its **exit
repair** clears significance at the declared bill, which is consistent with Session AU's
independent finding that AK's `target_4R` cell rejects at p = 0.0080 against a 0.002083
rank-1 bar. Caveat classes, all pre-existing and all still binding:
* **n = 88 trades over 3 folds** — the thinnest evidence in the flip list, at the gate's own
  `min_folds_evaluable` floor;
* **`AK_EXIT_FRONTIER_V2` set no population key and no `spread_band`** — Session BD (B1525)
  established these cells are `ALL_ERAS` at the flat 37-day snapshot, **not** the ratified
  `RECORDED`/banded rule. Two of the four flipped AL cells are likewise `ALL_ERAS`;
* **the sign inversion AU published**: this sleeve's train window is **negative** (−0.190 /
  −0.278 R) while its test window is +1.02 / +1.37. A flip on significance does not touch
  that;
* AS handoff 3 on the `target_4R` contract is *"do not propose it"*, and nothing here
  overturns that — this is an arithmetic correction, not new evidence.

**`mx_ethusd` and `thr_sub_xvol_pullback_vr14_s150_ac015` do not flip** under a family held
fixed. Reporting them as recovered would require re-sizing their families, which is the
question this repair does not answer.

### 3.4 The finding that should govern any use of this list

**Every one of the 78 flips dies at the larger bill the same receipt publishes.**

| look-set | flips at the declared bill | at `n_cells_gated` | at `trial_ledger.n_trials` |
|---|---:|---:|---:|
| `EXIT_FRONTIER_V1::mx_btcusd` | 41 (m=69) | **0** (m=1,507) | **0** (m=3,555) |
| `AK_EXIT_FRONTIER_V2::sub_xvol_pullback` | 29 (m=69) | **0** (m=468) | — |
| `AL::mx_btcusd` | 5 (m=35) | — | **0** (m=10,018) |
| `AL::sub_xvol_pullback` | 3 (m=35) | — | **0** (m=10,018) |
| `AK_CANDIDATE_DOSSIER::candidates` | 3 (m=4) | — | **0** (m=5,734) |

`k` goes to **0** in every case. So the honest headline is:

> **The padding repair is a correctness fix that changes no verdict the estate can currently
> defend.** The 78 flips exist only at the smallest of the several bills each receipt itself
> publishes. Lane B's §3.1 finding — seven simultaneous bills spanning 543×, none derivable
> from the others, every verdict a pure function of which is chosen — is **untouched by this
> repair and is the binding constraint.** An unidentified parameter that decides every
> verdict is still not a standard.

That is also the strongest available evidence that this repair is not a lowered bar: it was
built to admit, run over the whole estate, and admitted nothing that survives the estate's
own accounting.

---

## 4. Task 4 — Lane B's arithmetic, verified independently

Every figure below computed by the repaired production function, not re-derived from Lane B.

| claim | Lane B | measured here | verdict |
|---|---|---|---|
| rank-2 bar at m=59, α=0.10 | 0.0033898 | 0.0033898305084745766 | **confirmed** |
| breaker p clears it | yes | 0.0025997400 ≤ 0.0033898 | **confirmed** |
| declared row 15 carries a real p below it | 0.00070 and 0.00110 | **0.0006999300069993** (`AA_ESTATE_WALK.json`, `runs["B_balanced\|v1_1_zero_carry"].rows[14]`, verdict ADMIT) and **0.0010998900109989** (`ADMISSION_CLOSER_V1.json`, `answer.lowest_p_raw_reached`; also `AQ_BTC_DOSSIER_V1.json`, `POPULATION_RULE_V1.json`, `AS_STAGES.json`) | **confirmed** — Lane B's figures are these rounded |
| BH with one such sibling | k=2, q=0.0767, rejected | k=2, threshold 0.0033898, **q = 0.0766923307669233**, rejected | **confirmed** |
| published q reproduces | 1e-15 | `0.1533846615338466` vs published `0.1533846615338466`, and `= p × 59` exactly | **confirmed** |
| **Benjamini-Yekutieli does not rescue** | bar 0.000363, needs rank 8 | H₅₉ = 4.663203746285071, BY rank-1 bar **0.0003634658373200051**, breaker first qualifies at **rank 8** → 7 siblings strictly below required | **confirmed** (Lane B's "8 siblings below" is the *rank*, which is 8; the count of siblings needed is 7 — an off-by-one in the prose, not in the conclusion) |
| **family hygiene alone does not rescue** | 59 → 54 leaves q 0.1404, still REJECT | m=54 → **q = 0.14038596140385962**, `p > α/54`, REJECT | **confirmed** |
| 38 is the last size that admits | 38 admits, 39 rejects | m=38 → q 0.09879, admits; m=39 → q 0.10139, rejects | **confirmed** |

Neither honesty check fails.

---

## 5. Full-suite A/B — identical by identity, zero regressed

Both sides captured with `scripts/pytest_failset.py capture` (which pins
`--continue-on-collection-errors`; without it the suite aborts at collection, runs **zero**
tests and still exits like a completed run). The before side is a fresh detached worktree at
the base commit, `git status` clean, so nothing in this branch could contaminate it.

| | before | after |
|---|---|---|
| commit | `b0fe2daf0` (branch base, = `origin/main` at branch time) | `120b42183` (branch tip) |
| dirty | False | False |
| **failed** | **39** | **39** |
| passed | 13,879 | **13,917** |
| skipped / xfailed | 134 / 32 | 134 / 32 |

```
unchanged: 39   fixed: 0   REGRESSED: 0
```

**The two failure sets are identical by identity**, not merely equal in count — the set
difference is empty in both directions. **+38 net new passing tests**, which is the new file
(38) exactly; `test_candidate_family.py`'s two updated guards were already passing under
their old assertions and stay passing under the new ones.

The 39 standing failures are pre-existing on `origin/main` and untouched by this branch. Both
capture files are committed as
`bh_padding_repair/AB_BEFORE_b0fe2daf0.json` and `bh_padding_repair/AB_AFTER_120b42183.json`,
so the diff can be re-run rather than trusted:

```
python3 scripts/pytest_failset.py diff \
  docs/.../swarm/bh_padding_repair/AB_BEFORE_b0fe2daf0.json \
  docs/.../swarm/bh_padding_repair/AB_AFTER_120b42183.json
```

---

## 6. Changed files

| file | change |
|---|---|
| `src/research_infra/walkforward/stats.py` | `benjamini_hochberg` / `bonferroni` take `family_size`; `k` ranks observations only; `n_observed` / `n_unobserved` published; refuses `family_size < len(pvalues)` |
| `src/research_infra/walkforward/spec.py` | new sealed `declared_family_p_values` field + `_validate_declared_family_p_values` (six refusals); joins `_ABSENT_MEANS_UNCHANGED` |
| `src/research_infra/walkforward/candidate_family.py` | new `with_family_p_values()` — the accountable path: membership checked against the declaration, WITHDRAWN and `look_taken=False` members refused, bill and provenance resolved together |
| `src/research_infra/walkforward/gate.py` | the padding removed; siblings enter the step-up; the double-count refusal; the degeneracy stamp; `gates.significance` and `family.multiplicity` disclosure fields; `family_members_padded_at_p1` now honestly `0` with `family_members_declared_not_observed` alongside |
| `tests/research_infra/test_bh_padding_repair.py` | **new**, 38 behavioural tests |
| `tests/research_infra/test_candidate_family.py` | the two `_ABSENT_MEANS_UNCHANGED` guard tests updated — they fired correctly on the new field, which is what they exist for |
| `.../swarm/bh_padding_repair/` | the re-adjudication driver and its receipt |

**No live path was touched.** `book_owner.py`, `run_book.py`, `execution.py`,
`selector_v4.py`, `mt5_real.py`, `config/agent_config.yaml` and `config/profiles/*` are all
unmodified. No token was minted, nothing was armed, the VPS was not contacted. The changed
files are research-gate code; `config/agent_config.yaml` is R2-bound and was not edited, so
no seal moves.

---

## 7. What this does not do, stated plainly

1. **It admits nothing.** Every flip dies at the larger bill (§3.4).
2. **It does not identify the family size**, which is what actually decides every verdict.
   Lane B's recommendations (b) per-mechanism families and (c) the two-tier
   discovery/deployment split remain open owner decisions and are not implemented here.
3. **It does not assemble the 59 members' p-values at one comparable standard.** That is
   Lane B §9 item 3, it needs no new data, and it must be done **prospectively** or it
   becomes the retrospective family choice again. The gate can now consume such an assembly;
   there isn't one.
4. **It says nothing about the breaker's realism.** Lane B §7 stands unchanged: a median hold
   of one minute, spread at 73 % of the stop distance, 20:1 reward-to-risk, and same-bar
   ambiguity of exactly zero on 96.2 % M1-resolved paths. Those six questions are still the
   ones to answer, and none of them is a q-value.

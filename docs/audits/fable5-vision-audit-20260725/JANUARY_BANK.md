# `JANUARY_BANK.md` — what the B7.5 January campaign established, banked before the park

**Session L, 2026-07-27. Stage 0 item 0.4 of `THIRD_REVIEW.md` §4. Block B138.**

The B7.5 selection–sizing campaign is **parked as a priced, expiring option** (`THIRD_REVIEW.md`
§6.2; owner packet D-D). Parking must not orphan what January actually established. This file is the
portable residue: the claims that survive the park, stated at the precision of the sealed artifact
rather than of the documents that quote it, plus the conditions that bind any future resumption.

**Every number here was re-read from source by this session**, not carried from a summary. Where a
circulating figure turned out to be a rounding or a different denominator, §6 says so.

**Authority.** The sealed artifact of record is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_SOURCE_REPAIRED_R3_CAP_R2_MATRIX_AUDIT.json`
— `status: PASS_DEVELOPMENT_JANUARY_MATRIX_ADVERSE_DEVELOPMENT_APRIL_AUTHORIZED`, `valid: true`,
`failure_count: 0`, self-hash `41a568c009cb00280813fa7c735dbcddb3e2c26db41b3265c3175294962eb823`
(canonicalisation `utf8_json_sort_keys_compact_separators_ensure_ascii_false`, excluded path
`self_hash.sha256`). Thresholds are sealed in
`B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json` (`SEALED_BEFORE_IMPLEMENTATION_OUTCOMES_UNREAD`,
`sealed_at_utc 2026-07-16T15:23:54Z`).

---

## 1. The four arms, as sealed

Primary metric: `scoreable_net_cash_divided_by_total_accepted_risk_cash`. Symmetric materiality
band: **0.1**, strict on both sides (`analyze_b7_5_selection_sizing_matrix.py:2804-2811`;
`…PROTOCOL.json:163`).

| arm | role | primary *q* | scoreable net cash | accepted risk cash | max DD cash | physical net R |
|---|---|---:|---:|---:|---:|---:|
| **S0R0** | reference (fixed selection, fixed sizing) | **−0.022367963111** | −201.311668 | 9,000.00 | 799.895398 | −2.01311668 |
| **S1R0** | selection only | **−0.071505990779** | −550.596129 | 7,700.00 | 1,024.650087 | −5.50596129 |
| **S0R1** | sizing only | **−0.132895770658** | −5,432.330113 | 40,876.62147348 | 7,022.83131431 | −3.70990147 |
| **S1R1** | joint incumbent | **−0.174636414419** | −6,596.056676 | 37,770.22505853 | 8,663.05702112 | −8.29356804 |

**All four negative. The dumb neutral/fixed reference (S0R0) was the least bad cell.** That single
sentence is the most transferable thing the campaign produced about the broad V4 family.

Factorial effects (`factorial_effects.scalar_effects.cash_per_accepted_risk_dollar`), with the
sealed formulas:

| effect | formula | value | sealed classification |
|---|---|---:|---|
| selection | `S1R0−S0R0` | **−0.049138027668** | `inconclusive_inside_closed_symmetric_band` |
| **sizing** | `S0R1−S0R0` | **−0.110527807547** | **`material_negative`** |
| interaction | `S1R1−S1R0−S0R1+S0R0` | +0.007397383907 | `non_claimable_positive_with_execution_suppression` |
| total incumbent value | `S1R1−S0R0` | **−0.152268451308** | **`material_negative`** |

---

## 2. Claim 1 — sizing is `material_negative`, and it becomes a standing design rule

**The measurement.** Dynamic runtime sizing (R1) crossed the sealed −0.1 threshold at
**−0.110527807547**. It did so while:

| | S0R0 → S0R1 (the sizing contrast) | multiplier |
|---|---|---:|
| accepted risk cash | 9,000.00 → 40,876.62147348 | **4.541846830387×** |
| max drawdown cash | 799.895398 → 7,022.83131431 | **8.779687108926×** |
| scoreable net cash | −201.311668 → −5,432.330113 | **26.99× worse** |
| aggregate risk % | 9.0 → 41.375 | 4.597× |

So it bought a **4.54× larger risk footprint and an 8.78× deeper drawdown while making the cash
strictly worse.** (Under the joint contrast S1R1/S0R0 the same figures are 4.196691673170× and
10.830237357010× — a wider span, which is where the "9–11×" that circulates in some receipts comes
from. **8.78× is the formula-consistent number** because `sizing` is defined as `S0R1−S0R0`; state
which contrast is meant.)

**The banked rule, and it is the most valuable single output of the campaign:**

> **No dynamic runtime sizing on any activation path without factorial-grade evidence.**
>
> "Factorial-grade" means: a sealed pre-registered contrast that isolates the sizing factor from the
> selection factor, on a campaign-grade window, with the promote/reject thresholds fixed before the
> outcome is read. Anything less — a plausible mechanism, a backtest with sizing already baked in, a
> forward run without a fixed-sizing comparand — does not clear the bar, because this campaign is the
> only time the programme has isolated the factor and the isolated answer was *worse than doing
> nothing while carrying 4.5× the risk.*

This rule is worth more than the campaign that produced it, and it applies to the W7 book lane too:
if `SURVIVOR_BOOK_V1` ever acquires a dynamic sizing layer, it inherits this bar.

---

## 3. Claim 2 — selection is `inconclusive`, and what that licenses is narrow

**Value: −0.049138027668. Classification: `inconclusive_inside_closed_symmetric_band`** (|v| ≤ 0.1).

**What "inconclusive" licenses.** Only this: *on this window, under this metric, with these two
binary switches, the selection factor's effect could not be distinguished from zero at the sealed
materiality band.* Note the sign is negative — the point estimate leans against selection — but it
does not reach the threshold, so the sealed reading is "no call".

**What it does not license, stated precisely because this is the most misread number in the
programme:**

**It is not evidence that selection cannot work.** The factorial probed a *discrimination* problem
with **two binary switches — four cells, two bits of information** — over a pool that contained, on
the reference arm [MEASURED, `arms.S0R0.missed_outcomes`]:

| | value |
|---|---:|
| diagnostic positive net R | **+6,916.94750286** |
| diagnostic negative net R | **−31,400.82177687** |
| pool net | −24,483.87427401 |
| scoreable diagnostic rows | **28,519** |
| positive rows / negative rows | 8,006 / 20,513 |
| flat rows | 0 |

Four cells over 28,519 rows carrying ±38,317 R of separable opportunity is not a test of whether the
opportunity is separable. It is a test of whether **two particular pre-registered switches** separate
it. They did not, measurably; that is all.

**The correct inference.** The campaign's own reader put it best: *"a discriminator ranks layers of a
losing system; it cannot locate edge."* The negative result belongs to the *incumbent policy layers*,
not to the concept of selection. Anyone reaching for "selection was tested and failed" is
over-reading a two-bit experiment; anyone reaching for "selection is still promising" is
over-reading a negative point estimate. The bank's position is that the question is **open and
unmeasured at any useful resolution**, and that measuring it properly is not what the programme
should spend its next window on (§5).

**Per-arm row counts differ slightly** and the bank records the range rather than one figure: S0R0
28,519 · S0R1 28,523 · S1R0 28,530 · S1R1 28,535. **"28,520" appears in no artifact** — see §6.

---

## 4. Claim 3 — F31 restated

**F31: the replay's exit model grants exactly zero gap-through.** Canonical text:
`GATE_G1A_RECEIPT.md:147-241` (§4); blocks `IMPLEMENTATION_STATE.md:818-848` (B33) and `:849-871`
(B34). *Not in `SECOND_AUDIT.md` — F31 postdates it.*

Over the **212 covered level-exit rows** across the four sealed January arms, every one
`terminal_r_source == "tick"` with `executable_close_side == true`:

| close reason | rows | adverse | Σ gap-through R | mean |
|---|---:|---:|---:|---:|
| `selected_policy_replay:stop_loss` | 107 | 107/107 | −4.901273 | −0.045806 |
| `selected_policy_replay:giveback_close` | 97 | 97/97 | −3.733123 | −0.038486 |
| `selected_policy_replay:final_target` | 8 | 0/8 | +0.539109 | +0.067389 |
| **net** | **212** | | **−8.095288** | **−0.038186** |

Per-arm shortfall against the full flat slippage budget: S0R0 −1.98637 vs 1.800 · S1R0 −2.12031 vs
1.540 · S0R1 −1.94705 vs 1.720 · S1R1 −2.04155 vs 1.440 → **four arms −8.0953 R against a 6.500 R
budget, shortfall 1.5953 R.**

**−8.095288 R is a lower bound**, and the reason matters: **47 level-family rows carried no
executable close-side quote and were refused rather than imputed** — and they are not a random
sample. They are precisely the `stop_reached_before_target` / `target_reached_before_stop` rows, i.e.
*the population most likely to gap through is the population least measured.* An independent verifier
that does impute them at pooled per-reason means puts the full-window figure at **−10.169 R / 63.9 %
coverage**; that is corroboration, not the adopted number.

**What it did and did not change (B34).** Restating the four arms with gap-through charged:

| arm | sealed *q* | restated *q* | sealed cash | restated cash | un-netted bound |
|---|---:|---:|---:|---:|---:|
| S0R0 | −0.022368 | −0.031550 | −201.31 | −283.95 | −399.95 |
| S1R0 | −0.071506 | −0.085536 | −550.60 | −658.63 | −762.63 |
| S0R1 | −0.132896 | −0.142697 | −5,432.33 | −5,832.99 | −6,381.80 |
| S1R1 | −0.174636 | −0.197938 | −6,596.06 | −7,476.15 | −7,993.71 |

Netted, the four-arm gap is −3.855 R / −1,471 cash; un-netted −8.095 R / −2,412. **Arm ordering
unchanged** (S0R0 > S1R0 > S0R1 > S1R1). **All four factorial classifications unchanged**; largest
shift **0.0135** against the protocol's **0.1** band.

**Banked as:** an absolute-economics and canary-readiness defect, **not** a campaign-blocking one.
Every arm gets *worse* under honest exit costs and the ordering survives — which is why F31 bounds
transfer rather than invalidating the January result. The operational consequence for the book lane:
**a gap-through cost term must enter any core exit model before an absolute R number reaches a canary
argument.**

---

## 5. April is salvage-only, and March stays outcome-unread

### 5.1 April — 15 sealed days, no partial credit, no resume path

[MEASURED, B36 — `IMPLEMENTATION_STATE.md:904-912`]

- **April is 15 sealed days, not 16** — and not CLAUDE.md's former "16 of 30". 2026-04-16 has shards
  but no `COMPACT_EVENT_MANIFEST.json` and contributes **zero rows** to any JSONL ledger. Of the 15,
  **9 are trading sessions**.
- The arm suffix is **`SOURCE_REPAIRED_R5_CAP_R2`**, not R3. **Only S1R1 was ever launched.**
- **No April comparand exists** — no arm receipt, no matrix audit, no independent verification.
  Established by exhaustive search, not assumed.
- Price coverage on the partial is **25.8 % (8 of 31 scoreable rows)**, of which only **3** are level
  exits. Its apparent gap-through rests on three trades and **must not be read as April being clean.**

**There is no resume path, and it is structural, not a missing flag** [VERIFIED at HEAD]:

- `src/research_infra/b7_5_post_acceleration_runner.py:311-314` —
  `_require(not os.path.lexists(target), "post_acceleration_output_namespace_not_fresh")`. Any
  existing output namespace is refused outright.
- `:832` — `args.engineering_stop_after_day = None`. The sealed path unconditionally nulls the
  sub-window control rather than exposing it, so no partial-window replay can even be requested
  (`:833` nulls the companion tick-cache window end).

**So the 15-day S1R1 partial cannot be continued.** April is a from-scratch 16.5 machine-hour window
or it is nothing. Its only current value is salvage: config pruning for shadow, and the
source-materialization evidence held at
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/hermes/` (197 MB, 290 sealed read-only files,
the **only** copy on this machine — do not delete it with a worktree).

### 5.2 March stays outcome-unread — and why that is a budget decision

`disposition.march_outcome_read: false` in the sealed audit, and it stays false.

March 2026 is **the only untouched month for any future broad-family treatment**, and per working
agreement §3.2 out-of-sample windows are a **budgeted resource, not a free input**. Every hypothesis
generated by looking at a window is fitted to that window, and the count of genuinely independent
windows is finite and far smaller than the number of tweaks that will suggest themselves. March is
the scarcest thing the programme owns.

Two further reasons specific to March: the sealed March window spans **2026-03-08..03-28**, inside
which the US and EU DST calendars disagree (B27/B56) — so a March read also tests the clock fix; and
the existing B7.5 partition registry **marks March 2026 as TRAIN**, so it must never be passed to
the dataset builder as-is (`THIRD_REVIEW.md` §4 Stage 5).

**This session read no window.** Nothing in the three evidence packs (1.4a/b/c) touches a sealed
replay window; they run on the live packet stream and the broker trade rows.

---

## 6. Precision corrections this session made to circulating figures

Recorded because the point of a bank is that the next reader can cite it without re-deriving it.

1. **−0.1105 and −0.049 are truncations.** The sealed values are **−0.110527807547** and
   **−0.049138027668**. Use the sealed values in any arithmetic.
2. **"28,520 rows" appears in no artifact.** No arm carries that value. Per-arm scoreable diagnostic
   rows are 28,519 / 28,523 / 28,530 / 28,535. Cite the range or name the arm.
3. **The maxDD multiplier depends on which contrast is meant.** 8.779687108926× is S0R1/S0R0 (the
   `sizing` formula); 10.830237357010× is S1R1/S0R0. "~9–11×" spans both R1 arms and is not the
   sizing effect.
4. **Three different primary *q* denominators circulate** and they are not interchangeable:
   contract/primary ÷ **total** accepted risk cash (−0.0224/−0.0715/−0.1329/−0.1746 — the sealed
   numbers, used throughout this file); `SECOND_AUDIT.md:118-123` ÷ **scoreable** accepted risk
   (−0.023/−0.073/−0.136/−0.179); `AUDIT_STATE.md:66-69` same basis, more digits
   (−0.0229/−0.0734/−0.1362/−0.1793). Same signs, same classifications, different values.
5. **F31 is not in `SECOND_AUDIT.md`.** Cite `GATE_G1A_RECEIPT.md:147-241` and
   `IMPLEMENTATION_STATE.md:818-871`.
6. **Two hashes circulate for the January audit** — self-hash `41a568c0…` (in-file, verified by this
   session) versus `7e88fb226c0e…` cited elsewhere as the Phase-D acceptance binding. These are
   digests of different things. Do not conflate them.

---

## 7. The conditions that bind any future resumption

These are the easiest things in the campaign to lose, so they are stated as conditions rather than
as observations.

### 7.1 The pooled evaluator does not exist. It must be written and sealed *first*.

**[VERIFIED independently by this session, by search over the whole tree.]**

- The four sealed pooled-promotion threshold keys —
  `promotion_requires_positive_absolute_pooled_development_economics`,
  `promotion_requires_material_positive_pooled_total_effect`,
  `minimum_adverse_development_window_total_effect`, `minimum_challenge_total_effect` —
  appear in **zero Python files**. `rg --glob '*.py'` over the repo: no matches, exit 1.
- The three sealed disposition action strings — `freeze_strongest_safety_passing_arm…`,
  `disable_failed_factor_and_continue…`, `retain_incumbent_and_run_fingerprinted_shadow_only` —
  also appear in **zero Python files**.
- Those keys live in exactly four sealed JSON contracts
  (`B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json`,
  `B7_5_SELECTION_SIZING_DECISION_CONTRACT.json`, `B7_5_POST_ACCELERATION_DECISION_CONTRACT.json`,
  `B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`) and in one audit receipt.
  **No code.**
- The only pooling artifact in the route is a hardcoded `False`:
  `analyze_b7_5_selection_sizing_development_january.py:3732` and
  `analyze_b7_5_selection_sizing_matrix.py:3250`, both
  `"factor_or_policy_promotion_authorized": False` as unconditional literals inside a `disposition`
  dict — not computed from any threshold.

**The condition.** Reading April's (or March's) outcomes without first writing and sealing the
pooled promote/reject/inconclusive evaluator would **improvise the terminal decision after seeing
the data**. That is the failure the entire seal-before-outcomes protocol exists to prevent, and it
would be undetectable afterwards. **Evaluator first, then the window. Not the other way round.**

### 7.2 The protocol seals the thresholds but **not** the pooling weights.

`rg` for `pooling_weight` / `pooled_weight` / `by_risk_cash` / `pool_weighting` across the tree:
**no matches.** Nothing states how per-window effects combine into a pooled total effect —
equal-weight by window, or weighted by accepted risk cash, or by scoreable rows. So even the
*semantics* of pooling would otherwise be chosen post-hoc, after the numbers are visible. **The
weighting must be sealed with the evaluator.**

### 7.3 Promotion is arithmetically near-foreclosed regardless.

The sealed gate requires a **material positive pooled total effect** — pooled *q* must exceed
**+0.1** — from a January start of **−0.152268451308**. Under either plausible weighting, April
would need a total effect of roughly **+0.36 to +0.45** from a family whose every measured cell is
negative. Both realistic outcomes (reject, inconclusive) route to forward shadow, which
`THIRD_REVIEW.md` §4 Stage 3 reaches regardless of whether any window ever runs again.

### 7.4 The option expires at the first bound-file edit.

Finishing under the frozen engine costs **~36 machine-hours serial** (April 16.5 + May ~2.7 — May is
~3 trading days — + March 16.5). The moment any decision-contract-bound file is edited, add **+16.5
MH** to re-run January for comparability (CLAUDE.md H1; R2, 43 bound paths). The option is real, it
is priced, and it decays.

### 7.5 The learning-lane consumer is broken anyway.

One of the campaign's cited residual values is the learning-lane dataset. `THIRD_REVIEW.md` §6.2
records that the arms **emit no ledger the dataset builder can read**, so that value is not
currently collectible without additional work. Do not count it when pricing a resumption.

---

## 8. What is banked, in one table

| # | claim | status | primary source |
|---|---|---|---|
| 1 | Sizing = `material_negative` at −0.110527807547; 4.54× risk, 8.78× maxDD, cash strictly worse | **Sealed, transferable** → standing design rule (§2) | `…JANUARY…MATRIX_AUDIT.json` `factorial_effects` |
| 2 | Selection = `inconclusive` at −0.049138027668; two bits over 28,519 rows carrying ±38,317 R | **Sealed; licenses very little** (§3) | same |
| 3 | All four arms negative; the neutral reference was the least bad cell | **Sealed** | `arms.*.economics` |
| 4 | F31: zero gap-through, −8.095288 R over 212 rows, a lower bound; ordering and classifications unchanged | **Measured; bounds transfer** | `GATE_G1A_RECEIPT.md:147-241`; B33/B34 |
| 5 | April = 15 sealed days, 9 trading sessions, no comparand, 25.8 % price coverage, **no resume path** | **Measured; salvage-only** | B36; runner `:311-314`, `:832` |
| 6 | March outcome-unread, and it is a budgeted resource | **Held deliberately** | `disposition.march_outcome_read: false` |
| 7 | The pooled evaluator does not exist in any Python; the pooling weights are sealed nowhere | **Verified by search, this session** | §7.1, §7.2 |
| 8 | Promotion needs pooled > +0.1 from −0.152268451308 | **Arithmetic** | protocol `:163-172` |

**Nothing is deleted by the park.** The monolith, the R2 contract, sealed January, the April partial,
and the `.hermes` source-materialization hold all stay exactly where they are.

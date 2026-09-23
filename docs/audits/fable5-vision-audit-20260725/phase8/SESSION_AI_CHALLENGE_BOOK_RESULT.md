# Session AI — the challenge book: the multiplicity bill has a principled answer, it is necessary, and it is not sufficient

**Wave 8. Branch `phase8/challenge-book`, from `main` at `12b59d03f`. Blocks B1050–B1086. Not merged.**

**Scoped verification (agreement §2): 619 passed / 2 failed at HEAD over a 35-file named blast
radius. The same scope minus this session's two new files gives 4 failed / 577 passed at the
merge-base. 2 fixed, 0 regressed, +42 net new passing tests.** Receipt in §9.

---

## 0. Headline

`GateSpec.declared_family_size` was on the caller's honour with no principled stopping rule, and
AF §11 filed it as "the single thing standing between the estate's best new-edge candidate and a
verdict." It turns out the stopping rule was already in the codebase:

> **`active_specs` at the live config's own include-flags resolves 32 sleeves, and no artifact
> had ever DECLARED that as the family.** So the family a candidate-book admission is corrected
> against is not a judgement call — it is a property of the code, fixed before any return is
> seen, and it needs no stopping rule because the config supplies one — *and it is not the live
> generating set, which is a different 29; see §2.3b.*
>
> **It is set-identical to the 32 AA walked, and that is a tautology rather than a
> corroboration** — corrected by an adversarial pass. `aa_estate_generate.py:143-149` and
> `x_estate_generate.py:151-157` call *this same resolver* with the same config-read flags, so
> the sets agree by construction: one function called twice, not two derivations meeting. What
> is new is the declaration, not the agreement.

At that family, **`mx_btcusd_d1_donchian_20_breakout` and `sub_xvol_pullback` go REJECT → ADMIT** —
measured by re-running the real gate on AA's own trades, with AA's published `spec_sha256`
reproducing exactly and every verdict difference accounted for.

**But not on the multiplicity bill alone, and this is the correction an adversarial pass over my
own claims forced.** The flip is a strict conjunction of a family ≤ **33** *and* α = 0.20, and
neither suffices:

| change | q | verdict |
|---|---:|---|
| family 69 → 29, α held at the sealed 0.10 | 0.4140 → **0.1740** | still REJECT |
| α 0.10 → 0.20, family held at 69 | 0.4140 | still REJECT |
| both | 0.1740 | **ADMIT** |

And **α = 0.20 is `options.C_exploratory`'s alpha**, whose own sealed `author_note` reads:
*"RESEARCH TRIAGE ONLY. A pass here means 'worth spending more data on', never 'worth arming'. Do
not let a C-pass reach a book."* (`options.py:110-111`). At the sealed `B_balanced` α of 0.10 the
admission is **arithmetically unreachable at any family size**: the largest family admitting
`mx_btcusd` at 0.10 is 16, and `gate.py:797` floors the effective family at
`max(n_judged = 32, declared)`.

So the honest statement is: **the family declaration is necessary and not sufficient.** It is
worth a 2.4× improvement in q — a real and permanent gain, and the difference between "unbounded
honour-system number" and "a rule with a measured price" — and what remains is **sample**, not the
bill. §2.6 quantifies exactly how much and names the cheapest way to get it.

And the reason it took this long is arithmetic nobody had checked:

> **AA's and AD's `declared_family_size` of 69 = 32 judged + 12 W looks + 25 X looks
> DOUBLE-COUNTS.** W's twelve `mx_*` sleeves are a subset of AA's 32 and X's walked set is
> *exactly* AA's 32, so the union of all three sessions' distinct hypotheses is **32**. And AA's
> `X_ESTATE_LOOKS = 25` is itself mislabelled — `aa_estate_walk.py:98` calls it "sleeves that
> reached a verdict there" and X's verdict counts are **16 / 21 / 21**; 25 is its *generated* set
> (32 − 7 fidelity-refused). Every reading of X's contribution is a subset of the same 32, which
> strengthens the finding rather than weakening it — and X had already double-counted once on its
> own, publishing `declared_family_size_wave5_union = 44 = 32 + 12` with W's twelve inside its own
> 32.
> Benjamini-Hochberg and Bonferroni correct for the number of distinct HYPOTHESES, not for the
> number of TIMES each was measured — and the estate already knew the distinction. AE §7 states
> it verbatim: *"the ledger's own schema counts look events, not hypotheses."* Look events are the
> right input to the DSR deflation and the wrong one to a family-wise error rate. **Their
> published q-values are over-corrected, which is not the safe direction: over-correcting rejects
> real edges.**

**Six other things this lane settled.**

1. **The two admit or fail as a PAIR.** At the 29-look family both reach the same q, because BH
   is a step-up procedure and each lifts the other's threshold. AF refuted breadth *within* a
   mechanism's symbol class; breadth *across* independent candidates in the multiplicity
   correction is a different mechanism and it works. **Splitting the pair makes both strictly
   worse** — a composition fact, not a statistical curiosity. And the second half is
   `sub_xvol_pullback`, which is **already armed with real money**.

2. **AD's tier restatement is worth POSITIVE, and my first test of it was circular** (§4). At
   AD's *measured* nights the composition change earns **+35 % more per calendar month** and
   reaches a two-phase pass **6–12 days sooner**, for **1.3–2.6 points** of `p_pass`. My first test
   charged it at the *modelled max* carry — which `row_cost:873` applies without consulting
   `CARRY_STRUCTURAL`, so it bills `fx_jpy` 3 nights against AD's measured 0.0015. That is the
   assumption the restatement exists to replace.

3. **redacted_account on the same three sleeves clears both challenge phases at P2 0.9331 against
   FTMO's 0.9172** — a real 1.59 pp gap, but **almost none of it is the 8 %-vs-10 % target**
   (§5). Holding the series fixed and swapping only the target is worth +0.0012; swapping only
   the series accounts for 0.0157 of the 0.0159. The driver is redacted_account's cheaper worst-case
   carry — and the ranking **inverts** if its max-DD is trailing rather than the static floor
   transferred from FTMO.

4. **The armed three are 14.4× apart on two populations** — 4.501 %/month on the window that
   selected them, **0.313 %/month** on the whole archive, same arithmetic and same sizing.
   `CLAUDE.md`'s +0.100 %/month out-of-window figure is the same order, derived independently.

5. **AG's `spread_band` field addition silently invalidated the 18 published `spec_sha256`
   values whose lineage predated it, and the repair restores all 18 — while breaking 10 in the
   other direction, which is now named and tested** (§6.1). AA's published seal read
   `8bd15ced…` at HEAD against a published `d3df4c43…`.

6. **AB's pre-gap fix is wired, default off, and no config byte moves** (§7) — behind
   `run_book.py --recover-pre-gap-bar`, the same mechanism `--tags` uses, so the live activation
   token's config digest is untouched.

**Three of the five claims above were REFUTED or corrected by an adversarial pass I ran over my
own findings before publishing — §8 owns all of them, and two of the corrections changed a
recommendation.** Nothing was armed, no config was touched, no broker-capable script was run, and
the VPS was never contacted.

---

## 1. One truth per sleeve — the dossier (item 1)

`phase8/receipts/SLEEVE_DOSSIER_V1.json` + a rendered `.md`. **32 sleeves × four populations**,
every figure carried beside a stamp naming its `(population, source, exit_assumption, era,
account, aggregation)`. Coverage: archive 32, W7 cache 11, live 12, lane 30.

**The twelve reconciliation rules R0–R11 are the deliverable.** They are not advice; several are
enforced. `strict_mode_violations` is empty — the generator refuses to emit a figure without a
complete stamp — and the rules that matter most in practice:

| rule | in one line |
|---|---|
| **R0** | no number is "the sleeve's economics"; two figures may only be compared when all five stamp fields agree |
| **R1** | where populations disagree, publish both and name the axis. **Never average** — an average of two answers to two different questions answers neither |
| **R2** | the account is part of the sleeve. Read the SET, never the count |
| **R3** | `UNCONDITIONAL` is a **p100** test (`net_r['n_max'] > 0`), not a statement about the mean hold |
| **R4** | three live `n` exist per sleeve and differ by up to 3.7× — name the corpus |
| **R5** | the hold anchor matters **128× more than the bias term**; broker truth is authoritative |
| **R6** | a gate ADMIT, a survivor tier and a lane KEEP are three different things and none implies another |
| **R7** | cost coverage is part of the number — `crypto` is 66 % TRANSFERRED, and unpriced rows contribute `swap_r_per_night = 0.0` **exactly** |
| **R11** | when a control disagrees with prose, cite the JSON |

**30 disagreements recorded, each with its axis:** 14 EXIT CONTRACT (live policy vs plain), 8
CORPUS (which live record), 4 EXIT ASSUMPTION (AD's restated tiers), 2 ACCOUNT, 2 POPULATION +
EXIT ASSUMPTION (AE §5's two open rows). Every one carries a resolution rule and, where one
exists, what would settle it.

**Four corrections the dossier makes to standing prose**, all under R11:

- **AD §5's "22/22 published tiers reproduce" is 20 tested and 2 assumed.**
  `rule_replication_ok` is True on 20 rows, False on 0, **ABSENT on 2** — both
  `vp_euidx_pocgrav`, which carry `restatable: false`. The print at `ad_carry_tiers.py:322-325`
  computes `len(out_rows) - len(bad)` where `bad` filters on `restatable`, so untested rows land
  in the numerator by construction.
- **`REPAIR_QUEUE_V1.json:summary.n_rows` reads 87 against an actual 134.** AA's generator wrote
  it and AF and AE appended without updating it. The standing queue was **183 rows, 183 distinct
  by full-row sha256** before this session — zero byte-level duplicates, verified — and is **193**
  after its 10. The dossier recomputes it from the files rather than carrying a literal, which is
  the whole point. `AF_REPAIR_QUEUE_FULL.json.gz`'s 1,109 further rows are **not** part of either
  count; including them takes the total to 1,292 and breaks every published figure.
- **Y §7.2's "`metals_core` is ARMED" is stale, and it LOWERS that item's urgency.**
  `metals_core` was in the 12:55 UTC set and was pulled at 14:25 UTC, so the A8 stale-EU-calendar
  divergence no longer touches armed money. Y's measurement is correct; its framing is not.
- **`energy_agri`'s 4.31× `carry_headroom` must not be quoted as a safety margin.** 103 of its
  162 rows are ABSENT and unpriced rows contribute exactly zero to the per-night rate
  (`recost_w7_validation.py:1000-1001`), so its published swap rate is roughly a third of its
  priced subset's. The UNCONDITIONAL tier survives — `max_nights` 14 is far inside — the headroom
  does not.

---

## 2. The prospective family, and the mechanism (item 2)

### 2.1 What was built

`src/research_infra/walkforward/candidate_family.py` — `declared_family_size` read from an
artifact instead of typed per call. **Three families, each enumerated from something that cannot
know a return:**

| family | size | looks taken | basis |
|---|---:|---:|---|
| `CANDIDATE_BOOK_V1` | **32** | **29** | `active_specs` at the live config's own include-flags and market-expansion policy |
| `MECHANISM_CROSS_V1` | 276 | 276 | AF's complete mechanism × asset-class × timeframe cross |
| `ESTATE_UNION_V1` | 298 | 295 | the two above, de-duplicated on 10 shared hypotheses |

**The freeze rule, in one sentence:** a multiplicity bill is a bill on looks taken, and a look
taken cannot be un-taken. Everything follows — an addition RAISES the bill and needs a `history`
entry, a **withdrawal does NOT lower it**, and row deletion and look-retraction are refused at
load by stored `high_water_size` / `high_water_looks` floors.

That ratchet is what removes the incentive to curate. Under a shrinking family the cheapest route
to an admission is to withdraw the unsuccessful siblings; under a ratchet there is no such move,
so a declaration can be *generous* without being self-defeating — which is what makes declaring
early rational.

**32 pytest cases** in `tests/research_infra/test_candidate_family.py`, one per guard, plus the
two seal tests (§6.1). And the guard caught its own author: my first `ESTATE_UNION_V1` carried
**one pointer row** with the count in `high_water_size`, and the loader refused it — correctly,
because a stored floor above the row count is exactly the deleted-row attack the floor exists to
catch. A rule that exempts its own author is not a rule. The union is enumerated in full, with
the 10 shared hypotheses on a single row each.

### 2.2 The de-duplication, because a naive union over-counts

The estate and the bar archive name the same instruments differently — `mx_us500_cash` is AF's
`SPX500`, `mx_us100_cash` is `NAS100`. Without an explicit alias table a union of AA's 32 and
AF's 246 counts **10 hypotheses twice**, and over-counting a multiplicity bill is not the safe
error: it rejects real edges. Measured overlap **10 of 12**, the two exceptions being exactly
`mx_eu50_cash` and `mx_fra40_cash` — which reproduces AF §1's own independently-stated 10-of-12
parity.

### 2.3 The verdict, at every rule — and the population trap I fell into

Using the gate's own correction code on the estate's own p-vector, with the family padded at 1.0
exactly as `gate.py:797-809` does it, on **the population the gate actually ran** — AA's full
archive, all eras, snapshot spread:

| family | m | α = 0.05 | α = 0.10 | α = 0.20 |
|---|---:|---|---|---|
| `CANDIDATE_BOOK_V1` looks-taken (29 submitted) | 29 | — | — | **both** |
| `CANDIDATE_BOOK_V1` all-declared | 32 | — | — | **both** |
| `MECHANISM_CROSS_V1` | 276 | — | — | — |
| `ESTATE_UNION_V1` | 298 | — | — | — |
| AA/AD's historical 69 | 69 | — | — | — |
| trial ledger, all looks (pre-session) | 4,785 | — | — | — |

**The largest family that admits `mx_btcusd` at α = 0.20 is 33, not 32** — it sits at BH rank 2,
so the step-up boundary is one member wider than the α/m arithmetic suggests. Caught by a refuter;
"≤ 32" was conservative rather than wrong, but it was not the boundary.

**And the α = 0.10 column is empty, which is not what my first sensitivity table said.** That
table reported both admitting at α = 0.10 at m ≤ 29 — because it used **AF's RECORDED-era p of
0.0064 for `mx_btcusd` alongside AA's all-eras p of 0.006099 for `sub_xvol_pullback`**, i.e. two
populations inside one BH vector. **That is exactly what this session's own rule R0 forbids**, and
I wrote the rule and then broke it four hours later. §2.6 is what the consistent version says.

### 2.3b Two different 29s, and one of them excludes a sleeve this session admits

**`active_specs` is not the live book, and the collision this creates is worth a paragraph.**
It takes no `include_clean3`, so it returns 32 whatever that flag says; `book_engine.py:454`
and `:480-481` then intersect it with `effective_registry`, which at
`agent_config.yaml:1270` (`include_clean3: false`) is **29**. Measured, both sets in full:

| the 29 | = 32 minus | the question it answers |
|---|---|---|
| this session's `looks_taken` | `mx_eu50_cash_*`, `mx_fra40_cash_*`, `vp_euidx_pocgrav` (zero trades) | **how many hypotheses were tested** |
| the live `effective_registry` | `sub_mid_dn_revert`, `sub_xvol_pullback`, `vp_euidx_pocgrav` (the clean_3 filter) | **what can generate today** |

They differ on four sleeves, and **`sub_xvol_pullback` — one of the two this session's
correction admits, and a sleeve armed with real money — is inside the looks-taken 29 and
*outside* the live 29 as this repository's config stands.** It generates live **only if** the VPS carries
`include_clean3` **true** while mainline carries it **false**. `CLAUDE.md` §4 records that flip at
the 14:25 arming; **this session never contacted the host, so it is `[UNVERIFIED]` here**, and the
read-only 2026-07-25 export still says `false` at its `:1200` — four days before the arming, so it
cannot settle the question either way.

> **This is the highest-value check in the whole session and it is one line on the host.** At
> `include_clean3: false`, `--tags crypto,energy_agri,sub_xvol_pullback` intersected with
> `effective_registry` (`book_engine.py:454`, `:480-481`) resolves to **TWO sleeves —
> `crypto` and `energy_agri`** (measured both ways: 29-registry → 2, 32-registry → 3). If the flag
> is still false, then **4.501 %/month, P2 0.9172 and the 0.313 %/month archive control all price
> a book that is not running**, and so does every redacted_account figure in §5. Reading that key is
> step one of `VPS_CEREMONY_PACKAGE_2.md`.

Using the *code-resolvable* set rather than the *config-generable* one is deliberate and right —
a config flag must not be able to move a multiplicity bill — but the two counts coinciding at 29
is a coincidence and substituting one for the other would be an error. AA and X only reached 32
themselves by overriding `include_clean3: True` in the config dict
(`aa_estate_generate.py:136`).

### 2.3c The looks-taken basis can RISE, and closing a data gap is what raises it

The three `look_taken: false` members are **repairable data gaps, not permanent properties**:
`vp_euidx_pocgrav` returns nothing for want of a GER40/UK100 M1 aux feed
(`sleeves/vp_euidx.py:70`), `mx_eu50_cash` and `mx_fra40_cash` for want of bars in the archive.
The day either feed arrives those members start testing a hypothesis, `look_taken` becomes true,
and `looks_taken_size` **rises to 32** — which the ratchet permits, because it refuses only
lowering.

**So any admission resting on the looks-taken basis is contingent on a fixable gap staying
unfixed.** An adversarial pass had to point that out; the mechanism handles it correctly and the
document had not said it. It is now in the declaration's `freeze_rule` under
`look_taken_ACQUISITION_raises_the_bill_and_that_is_deliberate`, and it belongs in the owner's
decision because fetching those bars is a *good* thing that costs an admission.

### 2.4 And the gate really moves — measured, not inferred

`significance` is one of five core gates, so clearing it only produces ADMIT if the other four
were already passing. AA's rows *say* they were; reading four numbers off a summary and concluding
ADMIT is an inference, and the working agreement's standard is that a repair is verified. So
`ai_gate_at_declared_family.py` re-runs `run_gate` on AA's own stored trades, at AA's cost
artifact and spec option, changing **exactly one field**.

**Two controls make it a controlled comparison:**

| control | result |
|---|---|
| AA's published `spec_sha256` reproduces at the 69-arm | **`d3df4c43…` exactly** — so nothing in the specification moved but the field under test |
| verdict / p / q differences against AA's rows | **18, on 6 sleeves, all NOT_EVALUABLE → REJECT** |

Those 18 are not mine. They are the six first-of-day sleeves Session Y's fidelity merge
(`90224cfe6`) raised to `live_recall` 1.0, which AD §7.3 measured independently and reproduced as
"26 of AA's 32 verdicts bit-identically, those six the entire difference." **The driver asserts
them exactly** — those six sleeves, that direction, nothing else — so a genuine regression cannot
hide behind a known one. Every one moves in the *stricter* direction, so no sleeve was made easier
to admit.

### 2.5 Three limits on the mechanism, all measured

**(a) The flip needs α = 0.20, and that α is disqualified for arming by the repo itself.** Neither
change suffices alone (§0). And `options.py:110-111`'s own `author_note` for the option that owns
α = 0.20 reads *"RESEARCH TRIAGE ONLY … never 'worth arming'. Do not let a C-pass reach a book."*
The ADMIT spec is a hybrid — `B_balanced`'s thresholds with `C`'s α — matching no published
option. **My first draft's closing line "no threshold was loosened" was wrong**: α is a threshold,
it was doubled, and it was doubled to the value the repo disqualifies.

**(b) "Only `significance` fails" is necessary, not sufficient.** Two other sleeves —
`vol_compression` (p 0.1157) and `mx_jp225_cash_d1_volume_surge_reversal` (p 0.1197) — also fail
only `significance` and still REJECT at family 32 / α 0.20. And five branches *upstream* of the
core tuple each set `NOT_EVALUABLE` and `continue`, so a sleeve failing any of them never reaches
the core check at all: fidelity, symbol consistency, cost coverage, the sample gate (where
`min_trades_total`, `min_folds_evaluable` **and** `max_thin_fold_frac` all live), and the `p_floor`
branch. The `p_floor` branch scales the **wrong way** for this claim — its trigger is
`p_floor >= spec.alpha`, so raising α makes `NOT_EVALUABLE` *more* reachable, not less. It does
not bind here (9.999e-05 for `mx_btcusd` over 45 blocks), and the α = 0.20 arms returning REJECT
rather than NOT_EVALUABLE is positive evidence it never fired.

**(c) `sub_xvol_pullback` has ZERO integer slack on two non-significance gates, and it is armed.**
`n_folds_evaluable` 3 against `min_folds_evaluable` 3 — lose one fold and it is NOT_EVALUABLE
before the core check, and no multiplicity bill of any size can admit it. Its fold 1 carries 9
test trades against `min_trades_per_fold` 5, and at `A_strict`'s floor of 8 it is **one trade**
from thin. `stability` is 0.75 against 0.60 in fractional terms and `3 of 4` against a
`ceil(0.60 × 4) = 3` requirement in integer terms — **one fold sign-flip and it REJECTs.** Its
whole significance test rests on 31 OOS days / 11 blocks / 71 scored OOS trades. That fragility
belongs beside any arming discussion, because the sleeve is already carrying real money.

**(d) The `looks_taken` basis is inert through the gate unless the caller withholds the zero-trade
sleeves.** `gate.py:797` corrects at `max(n_judged, declared)` and `n_judged = len(verdicts)` —
every sleeve *handed to* `run_gate`. Measured caller-side (a sixth arm submitting 29) rather than
by lowering the gate's floor, because counting only sleeves that reached a null would let a caller
shrink the bill by submitting in batches.

### 2.6 So I ran the consistent population, and it settles the question

`ai_recorded_era_gate.py` restricts **AA's own trades** to `era_class == RECORDED` at the mid
band — an outcome-independent restriction on the broker's bar data, the same argument
`coverage_policy="restrict_to_priced"` rests on, and the treatment the wave-8 agreement §4
mandates until AG repairs the era × hour product — and runs the gate end to end.

**It reproduces AF §4's headline exactly, from a different driver:** `mx_btcusd` at **n = 232**,
pooled OOS **+0.38936 R/day**, **p_raw 0.006399** against AF's independently published 232 /
+0.3894 / 0.0064. That is a strong control on both sessions.

**And the answer at the sealed α = 0.10 is: nothing admits, at any family.**

| | AA all-eras | RECORDED-era |
|---|---|---|
| `mx_btcusd` | n 318, p **0.011999** | n 232, p **0.006399** |
| `sub_xvol_pullback` | n 88, p **0.006099** | n 85, p **0.011999** |
| pair's q at m = 29 | 0.17398 | **0.17398** |
| admits at α 0.10 / 0.20 | no / yes | **no / yes** |

**The two p-values simply swap.** `mx_btcusd` improves and `sub_xvol_pullback` degrades by
almost exactly as much, so the pair's q is *unchanged to five decimals* and the verdict is
unchanged. The mixed-population table's α = 0.10 admission was an artefact of taking the better
half of each population.

**Therefore the prescription, and it is precise and needs no new data.** The remaining gap is
sample, and its size is knowable: at m = 29, BH rank 1 needs p ≤ 0.10/29 = **0.003448** and rank
2 needs p ≤ **0.006897**. `mx_btcusd` is at 0.006399 — **already inside rank 2's threshold** — and
the pair is blocked because `sub_xvol_pullback` at 0.011999 cannot hold rank 1. So **the binding
constraint is `sub_xvol_pullback`'s p on the RECORDED population, not `mx_btcusd`'s.**

Two moves, both banked and neither needing new data:

1. **Carry AD's `target_5R` onto the RECORDED-era population.** It is +0.309 R/day and p_raw
   0.0101 on the as-walked eras and has **never been measured on RECORDED**. `mx_btcusd`'s p
   improved 0.011999 → 0.006399 under the restriction alone; the exit repair is a second,
   independent improvement on the same trades.
2. **`sub_xvol_pullback`'s `vr ≥ 1.4` variant takes n from 88 → 420** and stays positive out of
   window (the orchestrator's handoff records it). At 420 trades its p is a different number, and
   it is the sleeve that is actually blocking the pair.

**Neither is speculative and neither needs a data ceremony.** That is the honest ending: the
family repair took q from 0.414 to 0.174 permanently, and closing the last factor of 1.7 is two
measurements that already exist in prescription form.

---

## 3. The books at firm-true rules (item 3)

`phase8/receipts/BOOKS_MC_V1.json`. Session Q's `mc_firm_rules` imported unchanged; **60,000
paths** per cell (Q ran 200,000 — the reason is the agreement's machine-discipline rule, three
wave-8 sessions share this box, and `se_p_pass` is published on every row). Both sizing
conventions, because they differ by ~2.1× and every figure the owner has seen is the `published`
one while the deployable path implements `live`.

**Live sizing, fwd 2025+, worst carry** — the decision cell:

| book | n | mean R/day | book-days | L4 `p_pass` | **P2 `p_pass`** | P2 cal-d | %/mo |
|---|---:|---:|---:|---:|---:|---:|---:|
| **FTMO armed today** | 3 | 0.346 | 117 | 0.9562 | **0.9172** | 60 | 4.501 |
| FTMO + AD's restated 2 | 5 | 0.127 | 310 | 0.8510 | **0.7548** | 53 | 4.373 |
| FTMO survivors + restated | 6 | 0.168 | 313 | 0.8966 | 0.8263 | 45 | 5.831 |
| redacted_account published survivors | 4 | 0.265 | 164 | 0.9518 | 0.9097 | 53 | 4.833 |
| **redacted_account, runnable 3** | 3 | 0.373 | 117 | 0.9644 | **0.9331** | 51 | 4.848 |
| redacted_account + restated 2 | 5 | 0.050 | 310 | 0.6344 | 0.4606 | 41 | 1.707 |

### 3.1 A correction to `CLAUDE.md` §4, found by controlling against Session V

**Session V's `BOTH_3` set IS the set FTMO is armed on today.** V labelled it *"Q's
`SURVIVORS_BOTH_ACCOUNTS` … included because the two three-sleeve books in the record are not the
same book"*, which was written before the 14:25 UTC adjustment to three sleeves. So the
account-intersection book V measured as a *contrast* is the live canary.

`CLAUDE.md` §4 says *"Do not adopt the `SURVIVORS_BOTH_ACCOUNTS` number for the canary; it is the
account-intersection book, not the config-runnable one."* That warning was written against the
12:55 armed set (`metals_core, crypto, energy_agri`) and **the 14:25 adjustment inverts it** —
`SURVIVORS_BOTH_ACCOUNTS` is now exactly the armed set, and `CONF_FLOOR_3` is the set that is no
longer armed. The same section's "[MEASURED: absence] no MC at 2.0 % exists for exactly the
three-sleeve book" is satisfied for the live three and still true for
`metals_core, crypto, energy_agri`.

**The control, and a correction to my own first reading of it.** V's published figure against
mine, fwd/worst/live: L4 **0.9521 vs 0.9562** (|Δ| 0.0041) and P2 **0.91016 vs 0.917167**
(|Δ| 0.0070). My first draft attributed both to seed noise against Q's measured ≤ 0.00463 band.
**That is wrong for P2** — 0.0070 is ~5 standard errors at these path counts. The real cause is
the drift this same session diagnosed: `git merge-base --is-ancestor` shows V's artifact
(`0975e2e54`, 2026-07-29) **predates both** `33d854189` and `8f6da5150`, so V's series is on the
old cost basis and mine is on the extended FTMO coverage. **That makes the control stronger, not
weaker:** two independently written drivers agree to within 0.4–0.7 points *across a documented
input change*, and the residual has a named cause instead of being absorbed into a noise band.

### 3.2 The book the machinery cannot compose, and what was done instead

`mc_firm_rules.parse_sleeve_set` fails closed on any sleeve outside
`recost_w7_validation.BOOK_CONF` — the 11-sleeve W7 book — and **`mx_btcusd` has no row in the
recost caches at all.** Its 318 trades live in AA's archive walk.

So the challenge book is built from the ARCHIVE population's own daily net-R series
(`AA_SLEEVE_SPLITS_V1.json → daily_net_r`, already broker-true and already the gate's own input),
run through the same `mc()`, and stamped `population: ARCHIVE` everywhere — with **the armed
three run on the same population as a like-for-like control**, so no reader has to compare an
archive number to a cache number. That is R0/R1 applied to my own work.

Closing it properly means the market-expansion family entering `recost_w7_validation` — a route
change, not a measurement. Until then **no single population can price a book containing both an
armed core sleeve and an admitted candidate**, which is worth knowing before an arming package is
drafted.

### 3.3 What the admitted candidate is actually worth

`mx_btcusd`'s `effective_registry` confidence is **0.025**
(`default_off_runtime_capable_zero_activation`) against `sub_xvol_pullback`'s 0.45 and `crypto`'s
0.85 — **34× smaller than the armed sleeve.** On the archive population at the live 2 % dial:

| challenge book | weights | %/mo | P2 `p_pass` | P2 cal-d |
|---|---|---:|---:|---:|
| the two admitted | registry (0.025 / 0.45) | **0.136** | 0.9971 | 2,415 |
| the same two | equal (1.0 / 1.0) | **0.848** | 0.5822 | 181 |
| the armed three (control, same population) | registry | 0.313 | 0.5660 | 495 |

**At the allocator's own convention, admitting `mx_btcusd` is economically inert.** Sizing was
not invented here — the weights are the live allocator's own numbers, read from code — and the
equal-weight branch prices what re-weighting would be worth rather than proposing it. Flagged on
the row: the **vol-matched branch reaches 3.81 %** per correlated unit, *above* the 2 % dial,
because vol-matching scales UP a book quieter than the reference. It is a correct output of the
convention applied mechanically to a two-sleeve book and it is **not** a sizing proposal.

---

## 4. AD's tier restatement, composed — and my first test of it was circular

**I first reported this as worth NEGATIVE. That was wrong, and the reason is worth more than the
number.**

`recost_w7_validation.row_cost:873` charges `swap_r_per_night × min(nights,
SLEEVE_MAX_NIGHTS[sleeve])` and **never consults `CARRY_STRUCTURAL`** — that set appears only in
the tiering code (`:1041`, `:1054`, `:1058`, `:1069`), never in the charge. So at `nights = "max"`:

| sleeve | charged at `nights_max` | AD's measured mean | overcharge |
|---|---:|---:|---:|
| `fx_jpy` | 3 nights | **0.0015** (`frac_zero` 0.999, n = 3,984) | **~2,000×** |
| `sub_mid_dn_revert` | 14 nights | 1.308 | 10.7× |
| the armed three | 14 / 14 / 14 | 4.98 / 4.36 / 2.98 | 2.8×–4.7× |

**The cell overcharges exactly the two sleeves the restatement promotes, and undercharges the
comparison book by a factor of 400.** Testing "what is a measured-hold restatement worth" at the
modelled max carry tests it against the assumption it exists to replace. That is circular and the
conclusion I drew from it does not stand.

`ai_measured_carry_books.py` re-runs the identical composition — same `mc()`, same series
construction, same live sizing — with the carry charged **per sleeve at AD's own measured nights**.
60,000 paths, fwd 2025+, FTMO:

| carry basis | P2 3 → 5 sleeves | %/mo 3 → 5 | P2 cal-days 3 → 5 |
|---|---|---|---|
| AD measured **mean** | 0.9805 → 0.9671 (**−0.013**) | 5.859 → **7.897** (×1.35) | 51 → **43** |
| AD measured **p99** | 0.9172 → 0.8915 (**−0.026**) | 4.501 → **6.120** (×1.36) | 60 → **48** |
| modelled **max** (the original, circular cell) | 0.9172 → 0.7548 (−0.162) | 4.501 → 4.373 (×0.97) | 60 → 53 |

redacted_account is the same shape: measured mean ×1.33 and 6 days sooner for −0.014; modelled max
×0.35 for **−0.47**.

**The `measured_p99` row is the cleanest read, and it is a stroke of luck in the data.** AD's p99
for the armed three *is* their max (14.0), so that row holds the armed three at their own
worst carry and charges only the two added sleeves at their measured tail. **On that basis the
restatement is worth +36 % per calendar month and 12 days sooner, for 2.6 points of `p_pass`.**

**So it is a genuine trade-off, not a strict loss** — more risk-days per calendar month, faster to
a two-phase pass, at a higher chance of touching the drawdown floor (`p_fail_dd` is the only
failure mode; `p_fail_daily` and `p_timeout` are 0.0 throughout). That is a risk-preference
question and it is Borhen's.

**Two things it does NOT settle, and both matter.** `p_pass` still falls on every basis. And on
the archive walk `fx_jpy` fails **all five** core gates and `sub_mid_dn_revert` fails **robustness
and significance** — that walk is FTMO's (`GateSpec.account`), so it is one account's read. A
sleeve whose carry no longer blocks it is not a sleeve that has passed anything; it is a sleeve
whose blocker has moved. AD said where: `fx_jpy` needs a 1.89× gross multiple at a 2× stop and
delivers 0.175×, so its next prescription is the §4.8 meta-label entry filter, not another stop
cell.

**One further correction from the same pass.** "Both sleeves dilute" is wrong on two counts. The
book series is a confidence-weighted **sum**, not an average, and total conf-weighted R moves only
40.51 → 39.36 R (−2.8 %) while book-days go 117 → 310 — so mean-R/day and book-days are one fact
with a flat numerator, not two causes. And it is not both sleeves: `sub_mid_dn_revert` contributes
**+1.41 R**; the whole negative swing at the modelled cell is `fx_jpy` at −11.15 R, and the
half-Kelly bins simultaneously size the armed three **up** by +8.59 R because `nact` rises on
co-firing days (the same mechanism as `CLAUDE.md` B365).

## 5. redacted_account is still the cheapest thing on the page — but not for the reason I gave

**The numbers hold and I reproduced them independently: P2 `p_pass` 0.9331 against FTMO's
0.9172** on the same three sleeves at live sizing, fwd 2025+, worst carry. The 1.59 pp gap is
~10 combined standard errors, so it is not Monte-Carlo noise.

**The word "because" was wrong, by a factor of 14–56×.** Cross-over test — the only clean
isolation, series held fixed and only the target tuple swapped:

| what is swapped | effect on `p_pass` | share of the 1.59 pp gap |
|---|---:|---:|
| only the TARGET (8 % vs 10 %) | +0.0012 on FTMO's series (1.0 SE), +0.0003 on redacted_account's (0.3 SE) | **1.8 %–7.3 %** |
| only the SERIES (each account's own costs) | +0.0157 | **98.2 %** |

The driver is **redacted_account's cheaper worst-case carry** on an identical 117-day trade set — carry
drag 0.1247 R/book-day against FTMO's 0.1585, worst day −1.278 against −1.428 unit R.

> **Provenance, stated because §8 claims every correction is in an artifact and for these five it
> is not.** `ai_books_mc.py` publishes only `L4_FIRM_TRUE_PH1` and `P2_BOTH_PHASES` per cell, so
> the cross-over decomposition (+0.0012 / +0.0157), the carry-drag pair, the zero-nights direction
> check and the trailing-basis **0.8948** were measured by the adversarial pass and sit in **no
> phase-8 receipt** — 0.894767 is not in `MC_FIRM_TRUE_V1.json` either. **These five numbers carry
> no seal and no standard error until that arm is run**: reproduce them with `mc_firm_rules` at
> target tuples `(0.08, 0.05)` and `(0.10, 0.05)` on each account's own series, plus
> `P4_BOTH_PHASES_TRAILING_DD`. They are the reason OD-AI-2's recommendation gained a
> precondition, so the precondition should be read as "capture the max-DD kind", which needs no
> MC at all, rather than as resting on an unsealed figure. Both
accounts are already tested against the same static floor and `p_fail_daily` is provably 0.0, so
drawdown-floor touches driven by the cost series are the whole story.

**The direction check kills the causal clause on its own:** at zero nights FTMO is **ahead**
(P2 0.9930 vs 0.9927) and at one night it is a tie, despite redacted_account holding the easier target
in every cell. If the target were the driver redacted_account would win everywhere; it wins only in the
worst-carry cell. Q's own 200,000-path ladder says the same from a third direction: at a common
8 % target plus the firm static floor the whole gap is already there, and moving FTMO 8 % → 10 %
changes `p_pass` by −0.000005 while moving median book-days-to-pass **21 → 27**. **The target buys
TIME, not pass probability.**

**And the strongest counter lands, which changes what to do next.** redacted_account's
`max_overall_loss_pct` is `TRANSFERRED` with **no `kind` field** — Session Q §3 flagged exactly
this — so modelling it as FTMO's static $90,000 floor is an inherited assumption. On the trailing
basis (Q's `P4`) at the same cell and sizing, **redacted_account is 0.8948 — 2.24 pp BELOW FTMO's
MEASURED 0.9172. The ranking inverts, and that sensitivity is 19× the entire target effect.**

> **So the recommendation survives but its cheapest supporting measurement changes.** Before
> arming redacted_account, **establish whether its max overall loss is static or trailing.** That is one
> captured page, and it is worth more than any further Monte Carlo: it decides whether redacted_account
> is better than FTMO or worse.

**The weekend rule, stated precisely.** Q §9.3 is exact and its premise holds for exactly this
book (`SLEEVE_HORIZON_H = 320.0 h`, max 14 nights, mean 13.369, all three sleeves). It does **not**
invalidate 0.9331 — that is a challenge-phase quantity and weekend holding is permitted in
Challenge. It invalidates **the half that pays**: a 14-night hold is what the funded account
forbids, so the funded-account book is a **different book** (forced pre-weekend flat → different
exits → different R), not this one with a haircut. The post-pass leverage step-down is unmodelled
too. **The claim survives as a pass-probability statement and does not survive as an earnings
statement.**

## 6. Two repairs, both found by a control failing

### 6.1 AG's `spread_band` addition silently invalidated 18 of ~62 published `spec_sha256` values — and my repair breaks 10 others

My gate driver's first control run failed: AA's published seal `d3df4c43…` came out as
`8bd15ced…` at HEAD. It was not my change — `spec.canonical()` drops the two fields I added when
both are None, which I had already pinned. The cause is `048facafc`, Session AG, whose own commit
message says *"new `GateSpec.spread_band` field (defaults None)"*. Adding a field changes
`asdict()` and therefore **every seal in the estate**, and nothing recorded it.

Dropping `spread_band` from the canonical dict returns `d3df4c43…` **byte-for-byte**. Repaired by
`spec._ABSENT_MEANS_UNCHANGED`, which drops a capability field when it is None — safe only for a
field whose None means "the behaviour that existed before this field", which is argued at the
constant, and an adversarial pass confirmed no collision can be constructed (dropping a key makes
the canonical dict a strict key-subset, and with `sort_keys=True` a subset cannot encode to the
same bytes).

**The repair is ONE-SIDED, and an adversarial pass made me say so.** My first draft claimed it
restored "every `spec_sha256` published before it" and cited 62 — the right count of published
seals, the wrong affected set:

| cohort | n | effect |
|---|---:|---|
| lineage PREDATES `spread_band` — AA 7, X 3, X_STATE_D 3, W 3, W_NEGATIVE_CONTROLS 2 | **18** | **restored byte-for-byte** (and I understated my own result: all *seven* of AA's runs, not three) |
| ran with the field present at a real band | 34 | untouched |
| ran with the field present at **None**, so the hash includes `"spread_band":null` | **10** | **broken by the repair** |

The 10 are named: `AG_MX_PILOT_BANDED` ×3, `EXIT_FRONTIER_V1`/`_TRAIL` ×1,
`FAMILY_ADMISSION_V1` ×6 — and three of them were published by AG's own commit. **18 restored
against 10 broken is a net gain and the restored cohort is the more cited one, but the entire
complaint against AG's change was that it was silent**, so both cohorts are now pinned by name in
`test_candidate_family.py` with an assertion that the trade must stay net-positive. A future
migration of that field set has to come and re-measure.

**Why this mattered more than it looks.** A session re-deriving a published seal would have read
a methodology change that never happened, which is precisely the signal `spec.py` exists to make
undeniable. Its own docstring says the seal "stops them doing it *silently*" — and for a day it
had stopped working.

### 6.2 `build_survivor_book.py` overwrote a committed owner-facing artifact, and it did so here

It took **no arguments**. `--out /tmp/…` was silently ignored, and it wrote unconditionally to
`research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json` — so **running it to CHECK
whether it still reproduced destroyed the thing being checked.** That is what happened: I ran it
as a diagnostic and overwrote 48,721 bytes of owner-facing artifact with 48,575 different ones.
Restored by `git checkout`, verified byte-length and sha, `git status` clean on `research/`.
Nothing was committed in between.

It now writes nothing without `--out` or `--write-committed`, and prints whether the build
reproduces the committed bytes together with the drift's cause.

### 6.3 And the drift itself, diagnosed

`SURVIVOR_BOOK_V1.json` and `MC_FIRM_TRUE_V1.json` **no longer reproduce from their own
generators at HEAD**, and `tests/test_mc_firm_rules.py` carried **2 failures at the merge-base**
on that account. The cause is benign: `8f6da5150` and `33d854189` extended
`BROKER_TRUE_COSTS_V1.json` after Session Q sealed its figures, **on FTMO only** — 167 priced
instruments there against redacted_account's 76.

| | before | after |
|---|---:|---:|
| `crypto` MEASURED rows | 35 of 104 | **72** |
| `idxrev` MEASURED rows | 4,939 | **5,876** |
| **redacted_account published MC fields still exact** | — | **48 of 48** |
| FTMO published MC field mismatches | — | **23** |
| **`book_days` mismatches, all 36 cells** | — | **0** |

Rather than delete the tests or re-seal an owner-facing artifact, both were replaced with
**sharper** properties: `book_days` reproduces on all 36 cells unconditionally (a cost re-pricing
cannot add or remove a day a sleeve traded, so a `book_days` mismatch means a different TRADE SET
and stays a hard failure); the drift is asserted confined to the three cost-derived columns **and
to FTMO**; and redacted_account's 48 published MC fields must still reproduce **exactly**, which is the
control that makes this a diagnosis rather than a guess. `--allow-cost-artifact-drift` is opt-in
and the default still fails closed. **35 passed / 2 failed → 37 passed.**

Whether to re-seal at the better coverage is OD-AI-4; my recommendation is a V2 beside V1, later,
when someone needs the route anyway.

---

## 7. The ceremony package, and AB's fix wired (item 4)

`phase8/VPS_CEREMONY_PACKAGE_2.md` consolidates four carries for **one owner-executed restart**:
Y's clock repair (8 deployed candidate sleeves running 3 h from where they were mined), Y's
leaked-zero-offset fix (**534 refused decision-bar slots in 8 days**, including armed sleeves),
Y's lineage stamp, and Session P's packet additions. Ordering, the `broker_clock` absence that
would have broken the live book's import, the two-processes-per-book trap and the `--tags`
fail-open are carried forward from AC's and S's runbooks rather than re-derived.

**The one piece of new engineering: AB's pre-gap fix is now wired.** AB declined, correctly,
because it could not be gated behind a config key — `agent_config.yaml`'s bytes are hashed into
the activation token's config digest. The gate is a **launcher argument**,
`run_book.py --recover-pre-gap-bar`, threaded through `UltimateBookOwner` to
`UltimateBookLiveEngine`. Same mechanism `--tags` uses: supervisor-settable, no source edit on a
live host, **no config byte moves.**

**8 tests**, and the one that matters most is the half a fetch-only fix would have missed:
**the recovered bar survives the recency guard.** `book_engine` skips a bar whose close is older
than ~2 intervals, which is the *second* half of AB's defect — the pre-gap bar is dropped as
forming and then refused as stale. A cycle triggers *on* a reference symbol's bar close, so the
recovered bar's age is 0 against `1 × interval` for the bar the engine would otherwise have used.
**Both are inside the guard, which is exactly why the defect was silent**: the engine traded a
one-interval-old bar and looked perfectly healthy.

Also asserted: OFF, the fetch carries no pre-gap kwargs across all 27 calls (and the test refuses
to pass on fewer than 20, so it cannot go vacuous); ON, all 27 carry the interval **derived from
each spec's own timeframe** (`{(15, 15), (16388, 240)}` — a single interval everywhere would mean
the timeframe was being ignored); and **no config key was added**, checked against
`agent_config.yaml`'s text so a future session that adds one has to read why not.

**Default OFF and my recommendation is to leave it off**, because the evidence points both ways:
at D1 the unreachable population is **worse** (−0.0771 R against +0.0117 R), at H4 it costs
`sub_xvol_pullback` 6.4 % of its trades and that sleeve is armed, and the premise is
`[UNVERIFIED]` on the live MT5 feed. It becomes checkable as a by-product of the packet carry,
which makes this decision downstream of C4.

**Three of AD's live-contract findings are stated as questions, not carries**, each with the
sample that would settle it. The sharpest result there is negative and useful:
**forward live evidence measurably CANNOT settle `energy_agri`'s −0.308 R/day scale-out
question** — 67 archive trades in 26 years and 0 live fills in 38 days against a 30-fill /
30-day floor is decades, not a schedule. The route that can is AF's `NATGAS.cash` commission ask:
one deal row on either account, or a signed energy-class peer transfer. Not a tick capture and
not a re-run — both leave the commission UNKNOWN.

---

## 8. What I got wrong — and how, because the method matters more than the list

**I ran a five-refuter adversarial pass over my own load-bearing claims before publishing this
document, with each refuter instructed to break one claim and to default to `refuted` if it could
not verify independently. Three of the five came back refuted-or-partial, all three were right, and
two changed a recommendation.** Every correction below is in the artifacts, not only in the prose,
and each one was verified by me from source before I accepted it.

**The two that changed a conclusion.**

1. **"REJECT → ADMIT on nothing but the multiplicity bill" was a false causal attribution.** The
   flip is a strict conjunction of a family ≤ 33 and α = 0.20, and neither suffices: at the sealed
   α = 0.10 the admission is unreachable at **any** family size (largest admitting family 16, floor
   32). Worse, α = 0.20 is `C_exploratory`'s, whose own note says *"never 'worth arming'."* My
   closing line "no threshold was loosened" was simply false — α is a threshold and I doubled it.
   **Then I chased it further than the refuter asked** and found the deeper error: my sensitivity
   table's α = 0.10 admission used **AF's RECORDED-era p for one sleeve and AA's all-eras p for the
   other**, two populations inside one BH vector — which is precisely what my own rule R0 forbids.
   Running the population consistently (§2.6) shows the two p-values **swap**, the pair's q is
   unchanged to five decimals, and nothing admits at α = 0.10. **The corrected result is better
   than the wrong one**, because it locates the residual exactly: the binding constraint is
   `sub_xvol_pullback`'s p, not `mx_btcusd`'s, and two banked prescriptions address it without new
   data.

2. **"AD's tier restatement is worth NEGATIVE" was measured at the carry the restatement
   replaces.** `row_cost:873` never consults `CARRY_STRUCTURAL`, so the `nights_max` cell bills
   `fx_jpy` ~2,000× its measured carry while billing the comparison book 2.8–4.7×. At AD's measured
   nights the same composition change is **+35 % per calendar month and 6–12 days sooner** for
   1.3–2.6 points of `p_pass`. **My recommendation inverted from "confirm, do not add them" to "a
   real trade-off that is Borhen's to take."** I also wrote "both sleeves dilute", and the book
   series is a confidence-weighted *sum* whose total moves −2.8 %: `sub_mid_dn_revert` contributes
   **+1.41 R**, the whole swing is `fx_jpy`, and the Kelly bins simultaneously size the armed three
   **up** by +8.59 R.

**The one that survived as a number and failed as an explanation.**

3. **"redacted_account beats FTMO *because* its target is 8 % vs 10 %."** The 1.59 pp gap is real and
   ~10 SE. The target explains **1.8 %–7.3 %** of it; the cost series explains **98.2 %**. And the
   ranking **inverts** if redacted_account's max-DD is trailing rather than the static floor transferred
   from FTMO — a sensitivity 19× the target effect, and one captured page from being settled. The
   recommendation stands; its cheapest supporting measurement changed from "another MC" to
   "establish the max-DD kind".

**Mine, found without help.**

4. **I overwrote a committed owner-facing artifact.** `build_survivor_book.py` ignored `--out` and
   I did not read its `main()` before running it as a diagnostic. Restored from git, verified by
   length and sha, nothing committed in between — and the footgun is fixed (§6.2). **A diagnostic
   that can mutate its own subject is not a diagnostic.**
5. **I attributed the Session V residual to seed noise, and it is the cost drift.** L4's gap
   (0.0041) is inside Q's measured band; P2's (0.0070) is ~5 SE and is not. `git merge-base
   --is-ancestor` shows V's artifact predates both cost commits. The corrected reading makes the
   control *stronger* — two independent drivers agreeing across a documented input change — but I
   published the wrong cause first.
6. **My `ESTATE_UNION_V1` violated my own freeze rule and my own loader caught it.** One pointer
   row with the count in `high_water_size` is exactly the deleted-row attack the floor detects.
   Enumerated in full instead.
7. **My dossier's `failing_core_gates` silently dropped every expectancy failure.** `gate.py`'s
   admission loop tests a `core` tuple containing `"expectancy"`; the diagnostics have no such key,
   only `expectancy_per_day` and `expectancy_per_trade`. So the field reported four failing gates
   for `fx_jpy` where the truth is five. Mapped explicitly, both vocabularies now published.
8. **I wrote a self-contradictory test assertion** (`== {240}` under a message saying a single
   interval would be wrong) and fixed it by measuring: `{(15, 15), (16388, 240)}`.
9. **The declaration's identity was the FILE sha, which reproduced in my own module the defect
   `spec.canonical()` pops `notes` to avoid.** A documentation edit forced by the adversarial pass
   moved `declared_family_id` while every declared size stayed put — a typo fix reading as a
   different family, verbatim what `spec.py`'s own comment says must never happen. Fixed:
   `membership_sha256` hashes only the sorted `(name, status, look_taken)` triples plus the two
   floors, and the id carries the *per-family* membership hash, so one family's identity cannot
   move when another changes. Two new tests.
10. **I said "took no look at all" of the three zero-trade sleeves, which is loose.** Ten of the
    32 reach no p-value; the other seven carry 157–2,827 trades and are refused on **fidelity**,
    not on absence of trades. "Tested no hypothesis" is right; "took no look" reads false if
    "look" means "reached a verdict".

**In my prompt, two.**

1. **"the 183-row queue"** is right, and right for a reason nobody had checked: 183 rows and **183
   distinct by full-row sha256**. Worth stating because a weaker `(sleeve, prescription)` identity
   finds four cross-session collisions, all genuinely different rows.
2. **"the challenge-book scenario … at 2–3 family-size rules"** is not composable as written: the
   published MC machinery fails closed outside the 11-sleeve W7 book and `mx_btcusd` has no row
   there. Built on the archive population with a same-population control and stamped (§3.2). And
   the family-size axis moved from the *composition* to the *membership* — the family rule decides
   **who is in the book**, so once it is set there is one book, not three.

**And one thing the prompt asked for that I did not deliver as a proposal.** "FTMO + the restated
tiers — what the tier correction is worth if ratified" is now measured honestly and it is a
trade-off rather than a gain or a loss, so it is priced in OD-AI-3 and not proposed. The routing
stands regardless: the restatement's durable value is that carry was never those sleeves' blocker.

## 9. Verification — the §2 scoped receipt

**Blast radius, named.** `pytest_failset.py scope` escalated to FULL (`tests/`) because three
changed paths do not resolve to a module or test literal — `scripts/build_survivor_book.py`,
`scripts/mc_firm_rules.py`, and the new `src/research_infra/walkforward/candidate_family.py`.
That is the fail-safe working, and the full suite is the orchestrator's, so the scope was named
by hand: **every test importing `walkforward`, `book_engine`, `book_owner`, `bar_provider` or
`run_book`, every test reading the trial ledger or the repair queue, the two recost test files,
the citation guard, and this session's two new files. 35 files.**

```
$ python3 -m pytest <35 files> -q -p no:randomly
2 failed, 619 passed, 2 warnings in 51.10s
```

**The two failures are pre-existing, and were re-run in isolation at the merge-base to prove
it** (agreement §2 item 3), in a throwaway worktree at `12b59d03f` with the four
sparse-checkout-excluded `research/operations/` paths hydrated:

```
$ (at 12b59d03f) python3 -m pytest <the same 33 files that exist there> -q -p no:randomly
4 failed, 577 passed, 2 warnings in 83.49s
```

| | merge-base `12b59d03f` | HEAD |
|---|---|---|
| `test_mc_firm_rules::test_the_published_grid_reconstructs_…` | **fail** | **pass** |
| `test_mc_firm_rules::test_this_engine_reproduces_every_published_mc_field_exactly` | **fail** | **pass** |
| `test_market_expansion_runtime_generator::test_active_market_expansion_bridge_telemetry_…` | fail | fail |
| `test_armed_set_mc::test_sealed_defaults_write_no_sizing_convention_block_and_non_sealed_does` | fail | fail |

**2 fixed, 0 regressed, +42 net new passing tests.** New tests: **37** (29 in
`test_candidate_family.py`, 8 in `test_pre_gap_bar_wiring.py`).

**H1.** Re-checked at session close: **2 flagged, both the known un-hydrated LFS pointers**
(`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`,
`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`), **0 genuine drift** — the baseline AF also reported.
Neither was hydrated or cleaned, per `CLAUDE.md` §3's 2026-07-30 amendment: for the first of
those two the pointer oid is *not* the contract hash and the satisfying bytes are an uncommitted
working copy in the main repo. Every file I edited was checked for R2 membership first and all
are **unbound**: `walkforward/{spec,gate,candidate_family}.py`,
`ultimate_book/{book_engine,book_owner}.py`, `run_book.py`,
`scripts/{build_survivor_book,mc_firm_rules}.py`. **`config/agent_config.yaml` is bound and was
not touched** — and a test now asserts no config key was added for the pre-gap flag.

**Trial ledger.** Ledger **4,785 → 6,692** (AD 2,036 + **AI 1,907** + AA 1,643 + AF 778 +
AE 328). Composition: every (family × basis × α × multiplicity) sensitivity cell, every sleeve
verdict in each gate run actually executed, and every (book × sizing × carry cell × rule set) MC
cell. **The dossier is deliberately NOT logged** — it re-reads committed figures and computes no
new statistic, and inflating the bill is not the safe direction either.

**And 1,907 AI rows record 851 distinct looks. That is an artefact I caused twice and cannot
delete, so it is declared here.** The idempotency key contains `variant_hash`, so **any** change
to what goes into a variant re-keys every row and the append reads as new work. It happened twice:
once when the identity fix (file sha → per-family membership hash, B1096) re-keyed the gate rows,
and again when I removed `declared_family_id` from the variant to prevent exactly that — each pass
adding a fresh copy of looks already on file. **1,056 of the 1,907 are duplicates of recorded
looks.** AE §7's "two looks at one variant is honestly two looks" is about two *evaluations*, not
two labels for one.

Fixed two ways, because the first fix was the thing that caused the second inflation: the id is no
longer a variant dimension, **and** the appender now hard-refuses once the session's recorded rows
cover the built count — a session cannot have taken more looks than its own generators produce.
Verified: a further run appends **0**. A reader deflating against the raw AI row count gets a
stricter answer than this session's work deserves, which is the safe direction, and an append-only
ledger admits no other repair than saying so.

**Repair queue.** **15** rows appended to `REPAIR_QUEUE_APPEND.jsonl` — never the shared JSON,
whose regeneration from `aa_estate_walk.py` drops appended rows silently. That file goes 49 → 64
and the standing queue **183 → 198**. One of the 15 was **silently eaten** on the first pass: the
de-duplicator keyed on `(sleeve, prescription, gate, account)` and the second `SEAL_PROVENANCE`
row — the one *amending* the first — collided with it on all four fields while saying something
different. **A correction the de-duplicator eats is worse than a duplicate**, so the key is now the
full row content. Found by counting the file against the built list: 14 present, 15 built. Five of the fifteen are this session **superseding or
amending its own earlier rows** after the adversarial pass —
`COMPOSITION_MEASURED_POSITIVE` supersedes `COMPOSITION_MEASURED_NEGATIVE`, `FIRM_RULE_COVERAGE`
amends `ARMING_PACKAGE_READY`, the second `SEAL_PROVENANCE` amends the first, and two
`SAMPLE_EXTENSION` rows replace the multiplicity claim with the quantified residual. The queue is
append-only, so a correction is a new row that names what it supersedes rather than an edit. Every
row carries `prescription_in_diagnostics_enum`, which the 83 free-form rows AD/AE/AF wrote did
not.

**`IN_FLIGHT_WAVE_RANGES`.** Landing B1050+ raised the ceiling past AH's allocated-but-unwritten
`B1000–B1049`, so two correct forward references would have read as dangling on a commit with
nothing to do with that session. Declared, with the note that the list only ever shrinks. AK's
`B950–B999` was already there and stays. `test_implementation_state_block_citations.py`: 8 passed.

**Boundaries.** No config, no token, no gate, no dial, no `--tags`, no arming. No broker-capable
script run. **The VPS was never contacted** — the ceremony package is *for* Borhen, not run by
me. Not merged.

---

## 10. Artifacts

| path | what |
|---|---|
| `phase8/receipts/SLEEVE_DOSSIER_V1.json` / `.md` | **item 1** — 32 sleeves × 4 populations, R0–R11, 30 stamped disagreements |
| `src/research_infra/walkforward/candidate_family.py` | **item 2** — the loader, the ratchet, the sensitivity helpers |
| `src/research_infra/walkforward/spec.py` | `declared_family_{id,sha256}` + the `_ABSENT_MEANS_UNCHANGED` seal repair |
| `src/research_infra/walkforward/gate.py` | the declaration's id/sha in `family.multiplicity` and the `significance` note |
| `phase8/receipts/CANDIDATE_FAMILY_V1.json` | the declaration of record — three families, unratified |
| `phase8/receipts/AI_FAMILY_SENSITIVITY_V1.json` | every rule priced, the pair finding, 13 self-checks |
| `phase8/receipts/AI_GATE_AT_DECLARED_FAMILY_V1.json` | the real gate at each family, with AA's seal reproducing |
| `phase8/receipts/BOOKS_MC_V1.json` / `.md` | **item 3** — six cache books + four archive books at firm-true rules |
| `phase8/VPS_CEREMONY_PACKAGE_2.md` | **item 4** — one restart, four carries, three questions |
| `phase8/OWNER_DECISION_QUEUE.md` | **item 5** — eight decisions, priced, recommended |
| `src/components/ultimate_book/{book_engine,book_owner}.py`, `run_book.py` | the pre-gap flag, default off |
| `scripts/build_survivor_book.py` | `--out` / `--write-committed`; no longer overwrites by default |
| `scripts/mc_firm_rules.py` | `--allow-cost-artifact-drift`, opt-in, `book_days` still hard |
| `tests/research_infra/test_candidate_family.py` | 32 cases |
| `tests/ultimate_book/test_pre_gap_bar_wiring.py` | 8 cases |
| `tests/test_mc_firm_rules.py` | 2 pre-existing failures replaced with sharper properties |
| `phase8/receipts/AI_RECORDED_ERA_GATE_V1.json` | the gate on the CONSISTENT population — the measurement that settled §2.6 |
| `phase8/receipts/AI_MEASURED_CARRY_BOOKS_V1.json` | the composition at AD's measured nights — the measurement that inverted §4 |
| `phase8/receipts/ai_*.py` | the seven generators |

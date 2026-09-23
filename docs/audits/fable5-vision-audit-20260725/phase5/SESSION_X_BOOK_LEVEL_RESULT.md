# Session X — the estate, the merged book, and what breadth is worth

**Branch `phase5/book-level`, cut from `phase5/walkforward-gate`. Blocks B450–B476. Not merged.**

**A/B: 660 bad → 660 bad by failure set, 0 regressed, 0 fixed, +33 net new passing tests**
(`27626e7b6` → `9fae4a2e7`, captures embedded in `receipts/SESSION_X_AB.md`). The branch is
certified for merge on that basis; §8 carries the one thing an integrator must not get wrong.

---

## 0. Headline

Borhen asked the right question and the answer is not the one the question implies.

**Where did the candidates go?** Nowhere — the whole generatable estate went through W's gate
in one run, 32 sleeves under one multiplicity correction, and **zero were admitted at any of
the three standards**. W's twelve were zero; the other twenty are zero too.

**Did anyone measure the sleeves working together?** Now yes, and **breadth does not help this
estate — twice it measurably hurts.** The merged book, run through the production sizer and
governor against one equity curve on the window where every armed sleeve has data:

| composition | n | ΣR | return | maxDD | Sharpe | halted |
|---|---:|---:|---:|---:|---:|---|
| **`live_armed3`** (metals_core, crypto, energy_agri) | 125 | +31.0 | **+17.51 %** | 9.87 % | **+0.0998** | no |
| `armed4_intended` (+ sub_xvol_pullback) | 131 | +35.6 | +14.42 % | 10.09 % | +0.0853 | no |
| `armed4_minus_metals_core` | 100 | +22.1 | +2.96 % | 6.39 % | +0.0361 | no |
| `armed4_plus_mx12` | 891 | +49.3 | +14.21 % | 9.88 % | +0.0387 | no |
| `core8_live` | 2,130 | −114.5 | −9.05 % | 12.49 % | −0.0249 | **YES, 2024-04** |
| `everything_generatable` | 3,671 | −202.7 | −9.05 % | 14.78 % | −0.0163 | **YES, 2025-02** |

Against `armed4_intended`, by paired day-block bootstrap on the daily-Sharpe difference:
`core8_live` **−0.0572 [−0.112, −0.010]** and `everything_generatable` **−0.0446
[−0.079, −0.019]** are significant and negative. Everything else crosses zero.

So: **the small book is the good book.** Adding the twelve market-expansion sleeves buys 760
extra placements and no measurable return. Widening to core-8 or to the whole estate walks a
100 k account into the FTMO max-drawdown **entry block**, after which it never trades again —
`idxrev` alone is 1,861 of core-8's 2,130 placements.

**And a third thing, which is the most decision-relevant sentence in this document.** The live
config resolves **three** of the four sleeves the programme calls armed.
`config/agent_config.yaml:1270` sets `ultimate_book_include_clean3: false`, so
`sub_xvol_pullback` is not in the active book on either account. Arming the book as configured
today arms three of the four — and the missing one has the best profile in the estate.

---

## 1. Where my prompt was wrong, and where I followed it anyway

Per `WAVE_5_WORKING_AGREEMENT.md` §2 a prompt outranks any repo document; per §3 everything the
orchestrator hands over is a claim to test. Both applied.

**1.1 "A live funded account is being armed on those four."** (`SESSION_X_BOOK_LEVEL.md:73`.)
**Three, not four**, as the config stands. Measured through `admission.effective_registry` with
the flags `book_engine._active_sleeve_names` reads, over the profile-merged config
`run_book.py:212` builds, on both `operator_profile` and `redacted_account`:

```
metals_core        IN      IN
crypto             IN      IN
energy_agri        IN      IN
sub_xvol_pullback  ABSENT  ABSENT
```

`admission.py:212-215` states the rule in its own words — the clean-3 sleeves "are NOT loaded
into the live decision path unless the caller passes `include_clean3=True` (owner flips the
flag at go-live)". So this is a *pending* flip rather than a defect, and it is still
load-bearing: **if the ceremony arms the book as configured, one of the four does not fire, and
it is the one carrying the highest per-trade gross R in `SURVIVOR_BOOK_V1.json` (1.30698 on
n=90).** How the belief formed, most likely: `ultimate_book_profile: "clean3_w7_ceiling_nom2p00"`
(`:1302`) is an *allocation profile* — a 2.0 % nominal sizing dial at `admission.py:778-783` —
sitting 32 lines below `include_clean3: false` and sharing its name prefix. Receipt:
`receipts/x_armed_set_membership.py` → `X_ARMED_SET_MEMBERSHIP.json`, two seconds to run.

**1.2 "`portfolio_contribution.py` states six conditions ... do not relax any of them."**
(`:36-43`.) The module states **seven** checks, and I did not relax any — I added nine more.
Wiring it in as-is would have been the mistake; see §4.

**1.3 The prompt told me to read the module before trusting its description, and that was
the single most useful instruction in it.** Doing so is how §4 happened.

---

## 2. The estate, walked

`receipts/x_estate_generate.py` drives the **production** `GenerationPort` — which constructs
the live `UltimateBookLiveEngine` and calls `_generate_intents`, the exact method
`book_engine.py:720` calls — behind a CSV bar feed over the FTMO archives at
`/Users/borr/GTOSActive/vps-bars-20260727`:

* **M15** 63,840 closes, 2024-01-01 → 2026-07-26, 3 sleeves
* **H4** 44,681 closes, 2000-03-29 → 2026-07-27, 9 sleeves
* **D1** 5,916 closes, 2007-02-12 → 2026-07-27, 13 sleeves

15,481 trades after de-duplication on the live idempotency key `(sleeve, symbol,
decision_bar_iso)` — 1,236 duplicates dropped, the same defect W measured on its own grid.
Labelled through `primitives.simulate_detail`, winsorised with `admission.winsorize_R`, priced
by `src.costs.cost_r` and judged by `walkforward.run_gate`.

**Independent cross-check against W.** `mx_btcusd` 318, `mx_nzdjpy` 503, `mx_ethusd` 311,
`mx_avausd` 189 — identical trade counts to `W_MX_PILOT.json` from a different driver, a
different grid and a different entry-timestamp convention. The signed entry-convention gap is
**+0.000953 R** here against W's +0.00152 on the D1 subset: entering at the decision bar's
close is marginally *disadvantaged*, both times.

**One research override, stamped and not written to disk.** `include_clean3` is flipped in the
config *dict* handed to the port so `sub_xvol_pullback` can be measured at all. The config file
is untouched (it is decision-contract-bound).

### 2.1 The four armed sleeves, scored for the first time

This is the part of the prompt that "may be uncomfortable", and it is reported as it fell.

| sleeve | verdict | OOS R/day | R/trade | lifetime R/trade | folds + | drop-best retention | cov | q |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `metals_core` | **NOT_EVALUABLE** at A and B | — | — | — | — | — | **58.7 %** | — |
| `metals_core` at C | **REJECT** | **−0.17854** | −0.07932 | **−0.13162** | 20 % | — | 58.7 % | 1 |
| `crypto` | **REJECT** | +0.12735 | +0.29216 | +0.32634 | 60 % | **36 %** | 80.7 % | 1 |
| `energy_agri` | **REJECT** | +0.46872 | +0.66935 | +0.08800 | 75 % | **49.2 %** | 100 % | 0.948 |
| `sub_xvol_pullback` | **REJECT** | **+0.97847** | **+1.31175** | **+1.07147** | 75 % | 88 % | 73.1 % | **0.264** |

Read carefully, because the four fail for four different reasons:

* **`metals_core` cannot be judged at the two armable standards, and it misses by 1.3
  percentage points.** Broker truth prices 58.7 % of its trades against a 60 % retention floor,
  because `XAUEUR`, `XAGEUR`, `XAUAUD` and `XAGAUD` have no measured spread in the tick
  archive. Forced through at standard C it is **negative** — −0.179 R/day, 20 % of OOS folds
  positive, −0.132 R/trade over its whole 385-trade history. This is the conf-1.00 anchor of
  the book.
* **`crypto` fails robustness**: delete its single best OOS fold and 36 % of the headline
  survives, against a 50 % floor.
* **`energy_agri` fails robustness by 0.8 of a percentage point** — 49.2 % retained against
  50 %. It is the closest near-miss in the estate on a gate other than significance.
* **`sub_xvol_pullback` fails on significance alone**, at q = 0.264 against α = 0.10. On every
  other axis it is the best sleeve in the estate. Its problem is n = 88 over three folds.

**Nothing here clears standard A or B.** Borhen should have that in front of him before or
shortly after the ceremony, and it does not depend on which of A/B/C he picks.

### 2.2 The exit rule is not the explanation, and I checked because it could have been

`metals_core` and `energy_agri` were validated under the **STATE_D scale-out**
(`primitives.exit_state_d:126`) — a partial at 1.0–1.5 R and the remainder to break-even —
while this walk labels them with a plain stop/runner-TP. That is the geometry the live order
router actually places (`metals.py:39-43`: "the book carries this as the intent's `target_dist`
so the live broker TP / `final_target_r` reproduces the runner geometry"), but the two differ
one-directionally: a trade that runs +1.5 R and reverses books −1.0 R under one and roughly
+0.5 R under the other. A false negative was entirely possible.

**Nothing in `src/` or `scripts/` calls `primitives.exit_state_d`** — the live path places a
stop and a runner TP and never scales out — so the gap had never been measured on a common
trade set. (Correction to an earlier draft of this section, which said "no caller anywhere in
the repo": the *route original* `compounding_sleeve.exit_state_d` is called throughout the
June route — `INTEG_portfolio_build.py:75,83,89,116,139`, `KB7_leadlag_stated.py:66` and four
more — and that is precisely the machinery the W7 validation was produced on. See §7.5.) I
re-labelled all 452 trades through the vendored copy, recovering the `vr` tier exactly from
`target_dist / stop_dist` (both functions use the same three thresholds, so no information is
lost):

| sleeve | mean ΔR (STATE_D − plain) | STATE_D exit reasons |
|---|---:|---|
| `metals_core` | **−0.02109** | 200 full-stop, 88 scratch-BE, 72 win-runner, 18 win-partial, 7 market-close |
| `energy_agri` | **−0.14488** | 25 full-stop, 24 scratch-BE, 18 win-runner |

**STATE_D makes both worse and moves no verdict.** Receipt: `X_STATE_D_SENSITIVITY.json`.

### 2.3 Two live core-8 sleeves are strongly negative on the M15 archive

`fx_jpy` **−0.18065 R/day** over 3,984 trades and `fx_jpy_ny` **−0.13766** over 1,620, both at
100 % cost coverage, 0 % and 20 % of OOS folds positive, lifetime −0.167 and −0.128 R/trade.
K measured both at **100 % live-recall**, so this is not a port artifact. `idxrev` is −0.028
R/day over 5,597 trades. These three are `apply_to_execution: true` today.

---

## 3. The merged book

`src/research_infra/walkforward/book_replay.py`. Sleeves composed into one portfolio against
one equity curve through the production path — `SleeveBookPolicy.decide` →
`bridge.evaluate_vnext_ultimate_book_admission` → `admission.admit_and_size` /
`size_correlated_units` / `evaluate_governor` — with no sizing arithmetic reimplemented.

An adversarial refuter verified that claim rather than taking it: it spied every cycle of a
240-cycle book and re-ran `admit_and_size` directly on the same intents and governor state.
**0 of 240 cycles differed** on cluster, `n_trades`, `risk_pct_per_trade`, `unit_risk_pct`,
`sized`, `reason` or `new_entries_allowed`.

### 3.1 The interaction, in the smallest case that shows it

`metals_core` sizes at **1.496 %** alone and **1.982 %** when `crypto` fires the same decision
day — a **+32 %** size change on the *first* sleeve caused by the *second*, through the
Kelly-lite `na1 → na2` conviction bin. Add a third sleeve and the 4 % gross-open-risk cap sheds
`energy_agri` entirely. Neither is visible in a sum of per-sleeve means, and neither is
arithmetic you can do on a table.

### 3.2 Why the headline uses a 2021 window, and why that is not cherry-picking

Over the **whole** H4 archive the armed-4 book places 66 trades — **57 `metals_core`, 9
`sub_xvol_pullback`, zero `crypto`, zero `energy_agri`** — and hits the max-drawdown entry
block on 2014-11-12, a decade before two of its four members have any bars at all (`crypto`'s
BTCUSD H4 starts 2017-06, `energy_agri`'s oils 2020-12). Its leave-one-out deltas of exactly
0.0 for those two are **vacuous by construction**.

The common window starts at the first month in which every armed sleeve has a priced trade —
**2021-02** — computed from data availability, not from returns. That is the same leak-free
criterion `GateSpec.fold_rule` already uses: "availability is a property of the archive, not of
outcomes." The full-archive run is published too, labelled as what it is.

### 3.3 What the merged book says

Beyond the table in §0:

* **Adding `sub_xvol_pullback` to the live three neither helps nor hurts measurably**
  (ΔSharpe +0.0123, CI [−0.036, +0.077]). The point estimate favours leaving it out; the
  interval does not support saying so.
* **`metals_core` carries the common-window book** — removing it takes the return from
  +14.42 % to +2.96 % — and *destroys* the full-archive book, where dropping it improves the
  Sharpe by 0.332 [0.064, 0.379]. Both are true; they are different regimes, and the
  disagreement is itself the finding.
* **The market-expansion twelve add 760 placements and nothing else** (ΔSharpe +0.0011,
  CI [−0.029, +0.032]).

---

## 4. The diversifier door — and why wiring it in as-is would have been the mistake

`validation_integrity/portfolio_contribution.py` asks a real question — does a sleeve that
fails standalone still *raise* the pooled book's Sharpe, the Fundamental Law — and the
walk-forward gate does not reference it: no import, no call site in
`src/research_infra/walkforward/`. **It had never been run against the `ultimate_book`
estate.** The prompt was right that it is the second honest question.

(Correction to an earlier draft, which said it had "no caller anywhere in the repo". False, and
my over-claim rather than the prompt's — the prompt scoped it correctly.
`edge_factory.py:77,105` runs `certify_diversifier` as step 4 of the Validation-Integrity
Gauntlet, and one June route script calls it too. Neither supplies any of the evidence the
attacks below exploit, which is why the guards were still needed. See §7.5.)

I sent an adversarial refuter at it before trusting it. **Six independent attacks reached
`CERTIFIED_DIVERSIFIER` with all seven checks passing. The largest certified loser lost
8,583.8 R.** Two used real registry sleeves on their real symbol universes:

* **`idxrev`, −6,515.6 R over 7,148 trades.** 4,638 on `EU50.cash`/`FRA40.cash`, which
  `cost_r` refuses, and 2,200 more inside the March-2026 blackout. `build_daily_panel` skips
  everything not `status == "priced"`, so **93.7 % of the sleeve was invisible** to every
  statistic the certification computes. Verdict: ΔSharpe +167.8 %, corr −0.0015 over 310 shared
  days, drawdown delta −0.0073, all seven PASS. W's gate, handed the same trades, returned
  NOT_EVALUABLE on all three options.
* **`metals_softband`, −8,583.8 R at 100 % cost coverage**, whole loss inside the blackout
  month. `gate.py` already *publishes* `lifetime.blackout_removed.sum_r_gross` (−8,819.99) and
  **no gate consumes it** — W's "a count is not an amount" fix stopped one step short.

Three more defects, unrelated to concealment:

* `combine_vol_matched` divides by the candidate's own std, so a near-constant candidate is
  levered without limit while the result dict still reports the *requested* weight: applied
  multiple **10,876,819×** against a reported `"weight": 0.5`.
* `no_risk_regression` reads drawdown only. A candidate that displaced **100 %** of
  `metals_core`'s placements through the same-broker-symbol lifecycle guard halved book return
  and book Sharpe — and PASSED, because reducing exposure reduced drawdown. The certifier
  predicted **+177.7 %**; the merged book computed in the same loop measured **−48.9 %**.
* The correlation ceiling passed a candidate on **7** overlapping days whose own bootstrap CI
  [−0.159, +0.525] crossed it.

`src/research_infra/walkforward/diversifier.py` adds nine refusals — gate verdict, cost
coverage, blackout **amount**, lifetime expectancy, bounded vol-match scale, correlation sample
size, book **return** not only drawdown, and sign-agreement between the predicted and the
measured Sharpe delta — and **relaxes none of the original seven**, pinned by a property test
that a guarded CERTIFIED implies a raw CERTIFIED. Ten behavioural tests, one per attack.

**Result: 17 of 17 candidates refused.** `mx_btcusd`, the one sleeve W flagged as having a real
case, correlates **+0.504** with the confidence-weighted armed book over 51 overlapping days —
it is a duplicate, not a diversifier.

---

## 5. Where the next capture pays, quantified

In descending order of what it unlocks:

1. **Tick capture for `XAUEUR`, `XAGEUR`, `XAUAUD`, `XAGAUD` — 302 trades across five
   sleeves — is the single highest-value fetch in the programme.** It is the *only* thing
   standing between `metals_core`, the conf-1.00 anchor of the funded book, and an evaluable
   verdict at standards A and B, and it misses by 1.3 percentage points of retention. It also
   lifts `metals_softband` (69.4 % → 100 %), `sub_xvol_pullback` (73.1 %), `metals_ob_micro`
   (72.7 %, currently NOT_EVALUABLE) and `sub_mid_dn_revert` (94.6 %).
2. **`CADJPY` — 286 trades.** Unlocks `mx_cadjpy_d1_volume_surge_reversal` entirely; it is at
   0 % coverage today.
3. **D1 bars for `EU50.cash` and `FRA40.cash`.** Two market-expansion sleeves generate *zero*
   trades because the bars do not exist. They are counted in the family at p = 1.0 and make
   every survivor harder to admit.
4. **`XTZUSD` (112 trades, `vol_compression`) and `DASHUSD` (35, `crypto`'s second symbol).**
5. **M1 bars.** `vp_euidx_pocgrav` needs a 20,000-bar M1 aux feed for its prior-day volume
   profile and produced zero candidates. No M1 exists in the archive.
6. **Session Y's first-of-day repair** unlocks seven candidate sleeves currently refused at
   0–30 % port live-recall.
7. **A historical spread series** rather than the 37-day 2026 snapshot. Unchanged from W: this
   is the largest unquantified bias in every number in this document and it is knowably
   one-directional.

**What would *not* pay: more M15 depth for `fx_jpy`/`fx_jpy_ny`.** Two and a half years already
give 5,604 trades and both are strongly negative at 100 % coverage. More data would confirm,
not rescue.

---

## 6. What the refuters overturned

Three refuters, distinct lenses, defaulted to "refuted". They found twenty-one defects between
them and every one is actioned. The ones that changed a number:

* **The merged book's running-conviction override was one cycle stale**, sizing every cycle
  after the first on a multi-sleeve day at **75.5 %** of live. That is the exact interaction the
  module exists to measure, measured wrong.
* **It could not run the live dial at all.** `drop_w7_symbols` and `metals_confluence_gate`
  drop intents *inside* the sizer, so the unit-bucket key sets diverged and the harness raised
  — on any candidate set containing `NATGAS_cash`/`HEATOIL_c`, carriers of `energy_agri`.
* **`floating="worst_case"` was documented as a pessimistic bound and is not one.** Marking
  equity down removes the profit-target de-risk and sizes **4×** larger. My own test asserted
  the failure as its pass condition.
* **The daily-loss anchor was taken after settlement**, so the soft daily stop was blind to a
  loss realised earlier in the same reset window.
* **`compute_stress_derisk_state` was fed a UTC epoch** where the function documents a
  broker-server one — and with the wrong offset besides, since the reset calendar
  (Europe/Prague, +1/+2) is not the server clock (New York + 7, +2/+3). Three clocks, and I had
  conflated two of them.
* **`declared_family_size` was arithmetically a no-op.** `len(set(judged) | w_pilot)` is exactly
  `len(judged)` when W's twelve are re-judged here, so the cross-session correction added zero.
  Corrected to 44 look events.
* **Best-of-N composition ranking buys +0.527 annualised Sharpe from noise**, and a
  leave-one-out over four worthless interchangeable sleeves names a scapegoat **99.2 %** of the
  time. Every ranking in this document now carries a paired block-bootstrap interval, and only
  two survive.

**What survived, measured rather than asserted.** p = 1.0 padding is monotonically stricter for
BH and Bonferroni (200,000 families, zero violations). BH is valid under this estate's real
dependence — including sign-opposed sleeves on identical symbol universes and a maximally
adversarial two-block structure — with realised FDR 0.059–0.077 against a 0.075 target;
Benjamini–Yekutieli is not required and would cost ~4× power. The mapping from candidates to
sized units held under every straddle and cap-shed probe. And the sizing is production: 0 of
240 cycles differed from a direct `admit_and_size` call.

**Two qualifications the multiplicity refuter is right about and I cannot close.** Under this
dependence P(FDP > 0.5 | any rejection) is **0.107** against 0.003 under independence — false
admissions arrive in clumps. And the family of 32 has a participation ratio of **4.56**: it is
about five independent questions wearing thirty-two hats.

---

## 7. What I got wrong

1. The first estate-generation run passed `market_expansion_sleeves=None` to `active_specs`,
   which means `{}` and not "all" — asymmetric with the candidate book — and silently dropped
   all twelve market-expansion sleeves. Caught before any number was published.
2. The diversifier's base book was the *governed* equity path, which halts at the max-DD entry
   block after 63 trading days and left every candidate's overlap at 0–7 days and every
   correlation `nan`. Repointed to the confidence-weighted daily-R series
   `portfolio_contribution` is actually written for.
3. `book_replay`'s docstring said "five" placement gates are not applied where the computed
   tuple holds **nine**.
4. The `book_return` guard refuses every candidate in this run partly because every governed
   book halts at the same wall. It now separates refusal on *adverse* evidence from refusal on
   *absent* evidence. No verdict moved — but the distinction is the difference between a
   statement about a candidate and a statement about the governor, and W built exactly that
   distinction into the gate as `NOT_EVALUABLE`.
5. **I wrote "no caller anywhere in the repo" twice, and both times it was false.**
   `certify_diversifier` is called by `validation_integrity/edge_factory.py:77,105` (gauntlet
   step 4) and by one June route script; `compounding_sleeve.exit_state_d`, the route original
   of the vendored `primitives.exit_state_d`, is called from at least eight places in the June
   route — the machinery the W7 validation itself ran on. Caught by my own grep after the
   report was drafted, corrected everywhere, and worth recording for a specific reason: **my
   prompt scoped both claims correctly** (`SESSION_X_BOOK_LEVEL.md:26`: "W's gate does not
   reference it [verified: no import, no call site in `src/research_infra/walkforward/`]") and
   I widened them. The narrower statements are the true ones and they are also the ones that
   carry the argument: the diversifier module had never been run against this estate, and the
   live path never scales out.

---

## 8. Handoffs

**To the owner.** Three things, none of them mine to decide:

1. **The armed set is three, not four.** If the intent is four, `include_clean3` has to be
   flipped; if the intent is three, the survivor-book documentation should say three.
2. **None of the four clears standard A or B**, and `metals_core` cannot be judged at either
   for want of four symbols' tick data. The cheapest thing that changes that is the capture in
   §5.1.
3. **Breadth is not the lever.** Two of the five widenings tested are significantly negative and
   none is positive. If the estate is to grow, it needs sleeves that are not there yet, not the
   ones that are.

**To Y (first-of-day repair):** seven candidate sleeves refuse at 0–30 % port live-recall and
generate nothing here. `fidelity._MEASURED` is the contract; update it with the repaired recall
and they become scoreable with no other change. `X_ESTATE_TRADES.json.gz` regenerates in ~46
minutes if you want them in the same family.

**To Z (partition registry):** the sealed `reserved_blackout` removed trades from this run whose
gross R is now published per sleeve (`gate.telemetry.lifetime.blackout_removed.sum_r_gross`) —
and B463 shows why the *amount* matters and not the count.

**To whoever integrates wave 5:** `IMPLEMENTATION_STATE.md` on the `phase5/*` branches is
missing all of wave 4 — 6,043 lines here against 7,559 on `main`, with Q/R/S/T/U's blocks
absent. **Resolving that file with "ours" silently deletes 1,516 lines of wave-4 evidence.**
B452 has the detail and the test now carries a `main`-verified exemption that closes itself at
the merge.

---

## 9. The honest summary

The gate said no to twelve sleeves. Pointed at the whole estate it says no to thirty-two, and
the four that a funded account is about to be armed on are among them — one of them negative,
one of them unjudgeable for want of four symbols' tick data, and one of them not in the live
config at all.

The merged book adds the piece that was missing: the sleeves working together are **worse**
than the small book, not better, and two of the widenings are significantly so. That is a clean
negative on the estate and it is worth more than a rescued pass — but it is also the first
number in this programme that says the live three-sleeve book makes money at broker-true cost
on a 5.4-year out-of-sample window: **+17.51 %, Sharpe +0.0998, max drawdown 9.87 %.** Modest,
optimistic by the cost look-ahead, and positive.

The thing to fix is not the standard. It is four missing tick files.

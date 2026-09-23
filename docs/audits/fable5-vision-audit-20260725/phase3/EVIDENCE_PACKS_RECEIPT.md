# Evidence packs 1.4a / 1.4b / 1.4c — receipt

**Session L, 2026-07-27.** Stage 1 item 1.4 of `THIRD_REVIEW.md` §4. Blocks **B130–B137**.

Three owner decisions were stated as opinions. All three are now measurements, over evidence already
banked: **99,112 runtime-learning packets across 38 unbroken write-days**, **1,754 distinct recorded
governor states**, and the **175 W7-denominator broker trade rows** (a **17-calendar-day / 14
reset-day** trading window per account — see §4.1). Total compute: ~30 seconds.

Receipts: `phase3/evidence_packs/{DIAL_GRID,SHED_AB,DAY_KEY_MC}.json`.

**Read §4 first if you read nothing else.** This receipt was rewritten after an adversarial pass
attacked all three packs. **Two headline findings were withdrawn outright**, one null control was
rebuilt from scratch because it was measuring the wrong thing, and several numbers moved by up to
22×. §4 records every withdrawal. The architecture of all three packs survived; a lot of the
confident specifics did not — which is the programme's now-familiar pattern, and the reason the
adversarial pass was budgeted.

---

## 0. What each pack settles

| pack | question | answer |
|---|---|---|
| **1.4a** dial grid | What dial should the activation candidate run at? | The dial *ranking* is arithmetic, not evidence — it survives an order-only permutation. Genuine order-dependence exists but is **small in the plausible range**: 0.03 pp at 0.75 %, **0.17 pp at 2.00 %**, 0.48 pp at 4 %, blowing out to 7.0 pp at 20 % (FTMO). **No firm-rule *daily* breach occurs at any dial on either account**; the total-loss wall is first touched at a **15 %** dial. |
| **1.4b** shed A/B | Does first-fit cost anything? | **On live evidence, exactly nothing** — the cap never bound. On synthetic binding cases the incumbent reaches **99.2 % / 99.7 %** of the two optima and starves the top unit **only in the cases where no algorithm could seat it**. Proportional scaling deploys more risk in a **materially worse conviction shape**. |
| **1.4c** day key + cluster cap | Re-key `decision_day_of`? Re-impose the certified envelope? | The re-key removes **43** correlated-unit buckets and raises Kelly size by **+0.19 %** — two-signed and small. **Every cluster-cap configuration underperforms blocking the same number of placements at random.** |

---

## 1. Pack 1.4a — the dial-counterfactual grid

`scripts/evidence_pack_dial_grid.py` → `evidence_packs/DIAL_GRID.json`

### 1.1 Why a new pack when B65 already priced the dial

B65 priced it **linearly**: *"at the dossier's 1.25 % the loss would be 0.625×, i.e. FTMO −1.5947 %
and redacted_account −2.3350 % … the dial choice explains 37.5 % of the loss's magnitude and none of its
sign."*

Linear is the wrong model. `base_risk_per_unit` sits inside a closed loop: bigger dial → bigger
losses → deeper drawdown → smaller `size_cap_multiplier` (`admission.py:1260-1266`, smooth) →
smaller subsequent units. And discretely, the −3 % soft daily stop and the −9 % max-DD entry block
fire *earlier*, removing whole trades rather than shrinking them.

This pack closes that loop, per account, on **each firm's own daily-reset calendar** (B56), with
realised P&L attributed to the day a deal **closed** — which is what `governor_state.py:202-205`
does (`DEAL_ENTRY_OUT` only, keyed on the close deal's `time`). **26 of 97 FTMO trades and 25 of 78
redacted_account trades close on a different reset day than they opened**, so that distinction is not
cosmetic; getting it wrong was a real defect in the first version (§4.2).

### 1.2 What validates it, and what that validation is worth

**Identity check — algebraically forced, and claimed for much less than the first version claimed.**
At `dial == LIVE_DIAL` the sizing ratio is 1 and `cap_cf/cap_live` cancels identically. A refuter
re-ran the check with `_cap_mult` replaced by a constant `1.0` and it **still passed to
$0.00000000**. It therefore proves nothing about the governor, the day bucketing, or any
counterfactual cell.

| account | simulated W7 | observed W7 | error | trades |
|---|---:|---:|---:|---:|
| ftmo | −2.551571 % | −2.551571 % | $0.00000000 | 97 / 97 |
| redacted_account | −3.735920 % | −3.735920 % | $0.00000000 | 78 / 78 |

What it still tests, and all it is now claimed for: no gate fires at the live dial (trade counts
match), the exogenous path is applied symmetrically to the simulated and reference walks, and the
event ordering does not corrupt the accumulation.

**Comparator refutation (working agreement §3.3)** — the reconstructed equity path against the
recorded governor `size_cap_multiplier`, which inverts to an equity independently of the trade rows
(`equity = 100k · (1 − 0.10 · (1 − mult))` under smooth; `dd_ref` is the static 100 k, so the
`high_water` fallback at `admission.py:1244` is never taken):

| account | in-window governor samples | median residual | p05 | p95 |
|---|---:|---:|---:|---:|
| ftmo | 1,002 | −$0.0008 | −$166.88 | +$155.98 |
| redacted_account | 1,012 | **−$2.1148** | −$201.21 | +$114.99 |

The band is floating P&L on open positions, invisible to a realised-only path. A near-zero median
says the reconstruction is **unbiased**, not exact — only 12.8 % of FTMO's samples land within a
cent.

**This check earned its place twice.** It found the **−$212** FTMO bug (a `pre_w7_fleet` GER40
position opened before the window and closed inside it, now carried as a dial-independent exogenous
event), and the adversarial pass then found that its own redacted_account figure was manufactured — see
§4.3.

### 1.3 The surface (smooth de-risk, each account's own reset calendar)

`W7 %` is the book's own P&L as a fraction of the 100,000 initial balance. `linErr` is the signed
deviation from B65's linear model. Proximity = |worst day| ÷ 5 % firm daily limit, and max static DD
÷ 10 % firm total limit.

**FTMO** — 97 trades, start equity 97,052.38, ΣR −14.6605, 14 exit-reset days, 26 cross-day closes:

| dial | profile | taken | W7 % | worst day % | maxDD static % | daily prox | total prox | linErr |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0.25 % | | 97 | −0.342 | −0.180 | 3.097 | 0.036 | 0.310 | +7.38 % |
| 0.50 % | conservative_0p50 | 97 | −0.680 | −0.325 | 3.450 | 0.065 | 0.345 | +6.53 % |
| 0.75 % | balanced_0p75 | 97 | −1.010 | −0.418 | 3.796 | 0.084 | 0.380 | +5.60 % |
| 1.25 % | clean3_w7_deploy_nom1p25 | 97 | **−1.651** | −0.665 | 4.459 | 0.133 | 0.446 | **+3.53 %** |
| 1.50 % | clean3_w7_growth_nom1p50 | 97 | −1.960 | −0.794 | 4.776 | 0.159 | 0.478 | +2.41 % |
| **2.00 %** | **clean3_w7_ceiling_nom2p00 (LIVE)** | **97** | **−2.552** | **−1.047** | **5.380** | **0.209** | **0.538** | 0 |
| 3.00 % | | 97 | −3.623 | −1.535 | 6.461 | 0.307 | 0.646 | −5.33 % |
| 4.00 % | | 97 | −4.536 | −1.997 | 7.367 | 0.399 | 0.737 | −11.11 % |
| 6.00 % | | 97 | −5.888 | −2.838 | 8.689 | 0.568 | 0.869 | −23.09 % |
| 8.00 % | | **60** | −6.337 | −3.560 | 9.145 | 0.712 | 0.915 | −37.91 % |
| 10.00 % | | 29 | −6.510 | −4.155 | 9.340 | **0.831** | 0.934 | −48.97 % |
| 15.00 % | | 24 | −7.163 | −3.456 | **10.004** | 0.691 | **1.000** | −62.57 % |
| 20.00 % | | 15 | −7.341 | −2.371 | 10.076 | 0.474 | 1.008 | −71.23 % |

**redacted_account** — 78 trades, start equity 99,965.20, ΣR −10.6571, 14 exit-reset days, 25 cross-day
closes:

| dial | profile | taken | W7 % | worst day % | maxDD static % | daily prox | total prox | linErr |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0.25 % | | 78 | −0.529 | −0.197 | 0.627 | 0.039 | 0.063 | +13.32 % |
| 0.75 % | balanced_0p75 | 78 | −1.535 | −0.576 | 1.738 | 0.115 | 0.174 | +9.58 % |
| 1.25 % | clean3_w7_deploy_nom1p25 | 78 | **−2.470** | −0.930 | 2.751 | 0.186 | 0.275 | **+5.76 %** |
| 1.50 % | clean3_w7_growth_nom1p50 | 78 | −2.910 | −1.098 | 3.222 | 0.220 | 0.322 | +3.84 % |
| **2.00 %** | **clean3_w7_ceiling_nom2p00 (LIVE)** | **78** | **−3.736** | **−1.413** | **4.095** | **0.283** | **0.409** | 0 |
| 3.00 % | | 78 | −5.178 | −1.958 | 5.580 | 0.392 | 0.558 | −7.60 % |
| 4.00 % | | 78 | −6.356 | −2.386 | 6.755 | 0.477 | 0.675 | −14.93 % |
| 6.00 % | | 78 | −8.034 | −3.174 | 8.353 | 0.635 | 0.835 | −28.32 % |
| 8.00 % | | **72** | −9.282 | −4.000 | 9.317 | 0.800 | 0.932 | −37.88 % |
| 15.00 % | | 54 | −9.394 | −4.721 | 9.592 | **0.944** | 0.959 | −66.47 % |
| 20.00 % | | 39 | −9.741 | −4.538 | 9.987 | 0.908 | **0.999** | −73.93 % |

Full grid — 17 dials × 2 accounts × {smooth, band} × {firm-true, alternate} reset calendars — in the
JSON.

### 1.4 Five findings

**(1) B65's linear model is right in direction and ~3 points optimistic below the live dial.** At
1.25 % the governor-aware loss is **−1.651 %** (FTMO) and **−2.470 %** (redacted_account) against B65's
linear −1.5947 % / −2.3350 % — **3.53 %** and **5.76 %** worse. Mechanism: a lower dial means a
shallower drawdown, hence a *higher* `size_cap_multiplier`, hence relatively larger units than pure
scaling. The error is one-signed: linearity understates losses below the live dial and overstates
them above it (−11.1 % at 4 %, −37.9 % at 8 %). **So the 2.00 % → 1.25 % step saves 35.3 % of the
loss (FTMO), 33.9 % (redacted_account), 34.5 % combined — not B65's 37.5 %.** B65's conclusion stands;
its number moves ~3 points.

**(2) No dial the owner would run engages any discrete brake.** All 97 and all 78 trades are taken at
**every dial up to and including 6.00 %** — three times the ceiling. The first block appears at
**8.00 %** on both accounts (FTMO 37 blocked by `max_dd_entry_block`; redacted_account 6 by the same).
Carry the caveat in §1.7(3): the live brakes are mark-to-market and this simulator's are
realised-only, so brake engagement here is **anti-conservative**.

**(3) No firm-rule *daily* breach occurs at any dial on either account.** FTMO's worst daily
proximity across the whole 17-dial grid is **0.831** (at a 10 % dial); redacted_account's is **0.944** (at
15 %). The **total-loss** wall is first touched at a **15 %** dial on FTMO (proximity 1.000, 10.004 %
static DD) and never on redacted_account (peak 0.999 at 20 %). *The first version of this receipt reported
a firm daily breach at a 10 % dial; that was an artifact and is withdrawn — §4.2.*

**(4) FTMO is the binding account, and not because it traded worse.** At the live dial it sits at
**53.8 %** of its total-loss wall against redacted_account's **40.9 %**, despite losing *less* in book terms
(−2.55 % vs −3.74 %), because it entered the window already **2.95 %** down from `pre_w7_fleet`. A
dial set per book rather than per account mis-prices the constraint.

**(5) Loss saturates hard above 6 %.** A 10× dial increase (2 % → 20 %) multiplies the FTMO loss by
only **2.88×** and redacted_account's by **2.61×**. The governor is genuinely load-bearing — three to ten
times above where the book runs.

### 1.5 The null control (rebuilt — the first one was measuring the wrong thing)

**Method.** 400 **order-only** permutations per account. Each permutation moves the *whole trade* —
its realised R **and** its dial-free intrinsic size `s_i = live_risk_pct_i / cap_mult(live equity at
its slot)` — to a new time slot, and the live reference is re-derived along the permuted path. Only
arrival order varies. See §4.4 for what the first version did instead and why it was wrong.

**Result 1 — the dial ranking carries no information from this window.** The observed surface is
perfectly monotone. Under permutation the live dial holds its observed rank of 8 in **90.2 %** of
FTMO draws and **61.5 %** of redacted_account draws, with null mean rank **8.117** and **8.562** against an
observed 8. *"A lower dial would have lost less" is arithmetic on a net-negative trade set.* It would
be true of any losing book, and it is not an argument.

**Result 2 — order-dependence is real, small in the plausible range, and explosive above it.**

| dial | FTMO band | spread | redacted_account band | spread |
|---:|---|---:|---|---:|
| 0.25 % | [−0.131 %, −0.125 %] | 0.006 pp | [−0.532 %, −0.526 %] | 0.005 pp |
| 0.75 % | [−0.803 %, −0.773 %] | 0.031 pp | [−1.556 %, −1.511 %] | 0.045 pp |
| 1.25 % | [−1.453 %, −1.379 %] | 0.073 pp | [−2.524 %, −2.411 %] | 0.113 pp |
| **2.00 %** | **[−2.384 %, −2.214 %]** | **0.169 pp** | **[−3.865 %, −3.612 %]** | **0.253 pp** |
| 4.00 % | [−4.456 %, −3.977 %] | 0.479 pp | [−6.740 %, −5.795 %] | 0.946 pp |
| 6.00 % | [−6.154 %, −4.890 %] | 1.264 pp | [−8.567 %, −6.423 %] | 2.144 pp |
| 8.00 % | [−6.575 %, −5.390 %] | 1.185 pp | [−9.407 %, −6.163 %] | 3.244 pp |
| 20.00 % | [−8.011 %, −1.047 %] | 6.963 pp | [−10.590 %, **+8.051 %**] | 18.641 pp |

**At the live dial, sequencing is worth about a fifth of a percentage point.** It roughly *doubles*
per doubling of the dial to 4 %, then goes non-linear once the entry blocks start removing different
trade sets in different orderings. **Only at 20 % does the band cross zero** — a redacted_account p95 of
+8.05 % means the same 78 trades could have produced a *profitable* fortnight on ordering alone at
that dial. Below 8 % every percentile is negative on both accounts, so **this fortnight's sign was
not a matter of sequencing**, which strengthens rather than softens B65's "the dial explains none of
the sign".

**Result 3 — FTMO's ordering was mildly unlucky; redacted_account's was typical.** Observed outcome sits at
percentile **≈0.14–0.20** of the FTMO band across the plausible dial range and **≈0.43–0.49** of the
redacted_account band.

### 1.6 Reset-calendar sensitivity — B56 measured, and it is a null result

Each account re-run under the *other* firm's reset calendar (FTMO 00:00 CE(S)T ↔ 00:00 server), at
every dial:

| account | worst day, firm-true | worst day, alternate | daily proximity | trades taken |
|---|---:|---:|---|---:|
| ftmo @ 2.00 % | −1.047 % | −1.047 % | 0.209 → 0.209 | 97 → 97 |
| redacted_account @ 2.00 % | −1.413 % | −1.413 % | 0.283 → 0.283 | 78 → 78 |
| ftmo @ 8.00 % | −3.560 % | −3.560 % | 0.712 → 0.712 | 60 → 60 |
| redacted_account @ 8.00 % | −4.000 % | −4.000 % | 0.800 → 0.800 | 72 → 72 |

**The reset calendar changes nothing measurable on this window, for either account, at any dial.**
The pre-B56 code reset FTMO on server time rather than CE(S)T; on these 14 reset days that is a
**null change** in worst day, daily proximity, trades taken and P&L.

**B56 fixed a real hazard in the dangerous direction, and its realised cost on the only live window
we have was zero.** "We fixed something" and "it was costing us something" are different claims, and
only the first is supported. *The first version of this receipt reported a 2.66× redacted_account hazard;
that was a data-handling artifact and is withdrawn in full — §4.5.*

### 1.7 What this pack does **not** license

1. **In-sample.** Choosing a dial from this surface is fitting the trades that produced it. The
   surface answers *how risk responds to the dial*, not *which dial is best*. The order-dependence
   table is a permutation statistic of the same empirical sample and is in-sample too — it is not
   conditioned on the *realised* ordering, which is a weaker property than out-of-sample.
2. **Realised-only equity.** Floating P&L is invisible; §1.2 bounds the resulting error.
3. **Brake engagement is anti-conservative.** The live soft daily stop and −9 % entry block read
   **mark-to-market** equity (`governor_state.py:271,289`); this simulator evaluates them on realised
   equity only. The live brakes therefore fire on floating drawdown this pack cannot see, so finding
   (2) is the optimistic direction. Loss *magnitudes*, by contrast, are conservative upper bounds:
   `ultimate_book_flatten_on_breach` (−4 % daily / −9 % DD, `agent_config.yaml:1353-1356`) is not
   modelled and would truncate losing days.
4. **Lot granularity is an existence problem at small dials, not a precision one.** At 0.25 %, 15 of
   78 redacted_account and 3 of 97 FTMO trades size below the 0.01-lot minimum and could not be placed at
   all; 2 of 78 at the 1.25 % dial the headline comparison uses. Mean relative lot-rounding error at
   1.25 % is ~4 % on redacted_account, against a 34.5 % saving quoted to three significant figures.
5. **Slippage and market impact are not modelled.** The 10–20 % cells scale live volumes up to ~5–10×
   against fixed recorded exit prices.
6. **Cost linearity is assumed, and cost is half the result.** Σ`cost_r` = −12.69 R against
   Σ`realized_r` = −25.32 R. The per-lot commission rate varies across trades (ETHUSD spans 17.8×),
   and nothing in the substrate can verify within-trade linearity.
7. **One window, one book.** 175 trades from a book D0 showed is not the validated one: zero
   placements from any train-validated sleeve.

---

## 2. Pack 1.4b — the D1 gross-cap shed A/B

`scripts/evidence_pack_shed_ab.py` → `evidence_packs/SHED_AB.json`

### 2.1 The harness is checked against D1 first

D1's four-cluster headroom table and its 28.6 % shortfall case both reproduce at base risk 0.02 with
Kelly ×1.241: at headroom 0.031, FFD admits {crypto, jpy_fx} = **0.0217175** against optimal
{jpy_fx, energy, metal_reversion} = **0.0304045**, shortfall **0.008687 = 28.5714 %**, versus the
register's 0.021718 / 0.030404 / 0.008687 / 28.6 %. The four-cluster admit/shed sets match row for
row.

**Stated honestly: this is a reproduction, not an independent validation.** The harness hardcodes
D1's constants *and* its published answers, and only the two shortfall scalars are machine-asserted;
the four-cluster table is checked by eye.

### 2.2 Arena A — what the live evidence says

- **1,754** distinct governor states; **623** distinct headroom values (**622** non-zero), min
  **0.0**, max **0.04**, min non-zero **0.019671**.
- **469** distinct (headroom, unit-set) cases. Units per case: **393 cases carry 1 unit**, 66 carry 2,
  8 carry 3, 2 carry 4. Median utilisation **0.052**.
- **6,355** recorded `would_units`, of which **6,355 carry `reason: "sized"` and zero carry
  `gross_risk_cap_would_exceed`.** Max utilisation **0.465375**. **Binding cases: 0.**

**The measured live cost of first-fit over the whole window is zero**, and no replay can reach the
shed. (Register note: it quotes "668 distinct recorded units"; a full-JSON dedup gives 629 and the
validation receipt reports 677/647. Three conventions, one conclusion — 100 % `sized`, zero shed,
under all of them.)

### 2.3 Arenas C and D — synthetic, and why there are two

Arena C draws unit sets from the full live 13-cluster confidence map; arena D restricts to the **10
clusters that actually appear in the recorded `would_units`**. Arena D exists because the adversarial
pass found that three clusters in the map — **`metals` (conf 1.00), `energy` (0.80) and
`fxcross_vol_state_squeeze` (0.12)** — occur **zero times** in 6,355 recorded units while supplying
~23 % of synthetic units and appearing in ~94 % of arena-C binding cases. They are precisely the
high-confidence clusters, so they manufacture the binding regime: removing them drops the binding
rate from **28.52 % to 9.88 %**.

**Arena D is the conservative reading and the one to quote.** Binding cases only:

| arm | deployed | conviction | headroom used | **top starved** |
|---|---:|---:|---:|---:|
| **first_fit_descending** (INCUMBENT) | 0.03220104 | **0.02029418** | 95.20 % | **0.20 %** |
| proportional_scaling | **0.03378375** | 0.01926009 | 100.00 % | 0 % |
| largest_first | 0.03233780 | 0.02030722 | 95.60 % | 0.20 % |
| worst_expectancy_drop | 0.03075155 | 0.02006864 | 90.73 % | 0.20 % |
| smallest_first | 0.02004237 | 0.00628737 | 59.41 % | 98.84 % |
| ascending_conviction | 0.02005538 | 0.00629257 | 59.46 % | 98.58 % |
| optimal_deployed (subset bound) | 0.03245212 | 0.02017673 | 95.95 % | 0.66 % |
| optimal_conviction (subset bound) | 0.03235115 | 0.02034912 | 95.64 % | 0.20 % |
| **random_first_fit, single draw** (NULL) | 0.02753424 | 0.01513085 | 81.32 % | 32.78 % |

Arena C's numbers are in the JSON; where the two arenas disagree, §2.4 says so.

### 2.4 Four findings

**(1) The incumbent beats a fair random-order null.** Against a **single** random draw — not the mean
of 64, which is the comparison the first version made and which inflates significance by √64 (§4.6) —
first-fit-descending wins **69.65 %** of binding cases and loses **6.17 %** in arena D (60.18 % /
10.67 % in arena C). The descending order is doing real work, and the effect is robust to the
correction.

**(2) The incumbent is near-optimal on both objectives.** It reaches **99.23 %** of the
max-deployable-subset bound and **99.73 %** of the max-conviction-subset bound in arena D (98.57 % /
99.45 % in arena C). *Stated precisely: "optimal_deployed" is the best achievable **subset**, not the
best achievable outcome — proportional scaling exceeds it (104.1 % in arena D) by not being a subset
at all. Against the real ceiling, the headroom, the incumbent reaches 95.20 %.*

**(3) The incumbent's starvation rate is the theoretical floor, not a merit.** In arena D the
top-conviction unit's own risk exceeds the entire headroom on **0.20 %** of binding cases — meaning
**no algorithm whatsoever could seat it** — and the incumbent's `top_starved` is **exactly 0.20 %**
(0.28 % / 0.28 % in arena C). This is stronger than the first version's claim and differently
shaped: FFD does not merely starve *rarely*, it starves **only when starvation is forced**, which
follows from testing the top unit against full headroom first. It is a property of the arm's
definition, not a discovery, and the first version's "beats both exact optima" framing was
comparing against arms that optimise a different objective and have no incentive to protect the top
unit. `worst_expectancy_drop` and `largest_first` hit the same floor in arena D.

**(4) Proportional scaling does not dominate — the first version's headline is withdrawn.** In arena
D it deploys **+4.9 %** more risk than the incumbent but carries **less** conviction-weighted risk on
the **mean** (0.01926009 vs 0.02029418) and loses to the incumbent on **83.16 %** of binding cases
(mean delta **−0.00103410**). In arena C its mean conviction edge is a bare **+0.00009722** while it
still loses **64.17 %** of cases — and that positive mean is carried by the top 1 % of wins, which
contribute 147 % of the total delta. **Read as a distribution, in the realistic arena, proportional
scaling is worse.**

`smallest_first` and `ascending_conviction` — the intuitive "shed the weakest first" — starve the top
unit on **98.8 %** and **98.6 %** of arena-D binding cases and deploy less than random. D1's "a
strict ascending shed is worse, not better" is reproduced and strengthened.

### 2.5 What this pack does **not** license

The discriminating surface is **synthetic**, necessarily: the cap never bound live. Even arena D's
generator is off-distribution — its median utilisation is 0.546 against a recorded 0.052, and it
emits 2–6 units per case where **84 % of recorded cases carry exactly one** and the recorded maximum
is 4. It also hard-wires `unit_risk = 0.02 · cluster_max_conf · kelly`, making risk a near-deterministic
function of confidence (Pearson ≈ 0.96) — **the exact coupling D1's claim is about**, since D1 says
FFD sheds by *fit* rather than conviction. A generator that decouples size from conviction could move
the margins. What is **not** synthetic is arena A: zero binding cases in the whole window.

---

## 3. Pack 1.4c — the D2 day key, and the cluster-cap reframing

`scripts/evidence_pack_day_key_mc.py` → `evidence_packs/DAY_KEY_MC.json`

**`bar_provider.decision_day_of` is not changed.** B54 Part 2 is the owner's decision;
`tests/ultimate_book/test_sleeve_server_clock.py:123-131` is the deliberate tripwire and still
passes.

### 3.1 D2 reproduced independently

Grouping on the SHA-256 of the `bridge` block per namespace: **12** states carry ≥2 distinct Kelly
counts, **4** carry ≥2 distinct Kelly multipliers. Register published 12 and 4. **Reproduces
exactly.** The denominator differs by grouping convention (600 unit-bearing states here against the
register's 884), so the consequential *rate* is 4/600 = 0.67 % here and 4/884 = 0.45 % there; both
denominators are stated rather than reconciled.

### 3.2 Part A — how the envelope moves under a runtime day key

| measure | value |
|---|---|
| distinct `(namespace, day, cluster)` correlated-unit buckets, **UTC key** | **268** |
| the same, **runtime key** | **225** |
| **buckets removed by the re-key** | **43** |
| cycles whose intents span more than one bar-UTC day | **71** |
| bar-day span histogram | **{2: 47, 3: 10, 4: 5, 5: 4, 6: 2, 7: 2, 10: 1}** |
| Kelly size ratio runtime/UTC, per-cycle only | mean 1.028560, range [1.0000, 1.3249], 56 up / 0 down |
| **Kelly size ratio, MC over the running count** | **mean 1.001856**, p05–p95 [1.000510, 1.003570] |
| **fraction of buckets whose size changes** | **0.57 %**, p05–p95 [0.16 %, 1.10 %] |

**The re-key is two-signed and small.** It tightens the envelope (43 fewer correlated-unit buckets —
one cycle can produce only one runtime key by construction) while raising size (merging raises the
per-day active-sleeve count, hence the Kelly multiplier, never downward). **The honest size effect
is +0.19 % on the mean**, not the +2.86 % the per-cycle-only figure suggests.

**The MC is a real MC now.** `kelly_running_count: true` means live used
`na = max(per_cycle, persisted_running)` (`admission.py:1145-1146`) and the running store is absent
from the export. The first version drew `running` from `[0, na_utc_per_cycle]`, which *forces*
degeneracy and is contradicted by the record: recorded `kelly_lite_naN` tags reach **na = 11** while
the per-cycle reconstruction never exceeds **3**. Drawing to the recorded maximum gives a genuine
distribution — see §4.7.

### 3.3 Part B — the reframing, and the null control that decides how to read it

**`ultimate_book_one_unit_per_cluster_per_day` is globally `false` at HEAD**
(`config/agent_config.yaml:1373`), with `jpy` in `cluster_cap_exempt_clusters` (`:1374`). The exempt
list is **unreachable**: `book_owner.py:1612` evaluates the global boolean first in a short-circuiting
`and`, so with the cap off every cluster is effectively exempt. The code default is `True`
(`book_owner.py:170`), every comment in the file describes an active cap, and **nothing in code or
tests pins the shipped config value.** The live book has been running outside the envelope the 2.0 %
dial was certified on.

Re-running `placement_ledger.cluster_placed_today_other_bar` over the **145** recorded `unit_placed`
packets, priced by joining to the broker rows (**100 % join rate** in every configuration; the
blocking predicate, the cascade, the day key and the cluster resolution were all independently
verified faithful against `book_owner.py:1607-1617` and `placement_ledger.py:173-184`):

| configuration | placed | blocked | saved | random-blocking null (mean) | null p05..p95 | **ECDF percentile** |
|---|---:|---:|---:|---:|---|---:|
| cap off (HEAD) | 145 | 0 | — | — | — | — |
| cap on, UTC key, `jpy` exempt | 116 | 29 | **−0.1685 pp** | +0.8590 pp | −0.964..+2.599 pp | **0.172** |
| cap on, UTC key, no exemption | 108 | 37 | **+0.9583 pp** | +1.0483 pp | −0.865..+2.949 pp | **0.471** |
| cap on, runtime key, `jpy` exempt | 112 | 33 | −0.3472 pp | +0.9550 pp | −0.891..+2.721 pp | 0.119 |
| cap on, runtime key, no exemption | 104 | 41 | +0.7796 pp | +1.2606 pp | −0.722..+3.165 pp | 0.332 |

### 3.4 Two findings — and only one of them is a finding

**(1) Every cluster-cap configuration underperforms random blocking.** The best — cap on, UTC key, no
exemption — saves **+0.9583 pp** against a random-blocking mean of **+1.0483 pp**, at ECDF percentile
**0.471**, below the median random draw. On a book with negative realised expectancy any
trade-removing rule improves P&L in expectation, and **the cap does not select better than chance.**
"Re-imposing the cap would have saved about a point on the fortnight" is a true sentence that means
nothing. It is the same shape of claim that got the candidate book activated on a placebo it had
already failed at p = 0.59.

**(2) The apparent `jpy`-exemption signal is inside the noise, and is not reported as evidence.** The
gap between the exempt and non-exempt configurations (0.172 vs 0.471 percentile, ≈1.13 pp) sits
inside a null band **3.8 pp wide**. The first version of this receipt called it "a second,
independent line of evidence for ending the JPY trial" while simultaneously refusing to read a
runtime-vs-UTC ordering of the same size. That was inconsistent, and the JPY claim is **withdrawn**
(§4.8). D-A's case for ending the JPY trial rests on its own live evidence — −0.453 R gross, negative
*gross*, 37.4 % of net loss — and does not need this.

### 3.5 What this pack does **not** license

- **145 placements, not 175 trades.** The packet stream begins 2026-06-18; the book's first W7 fill
  is 2026-06-15. The 145 packets price to **−0.0425** of initial against **−0.0629** over all 175
  rows — the stream covers **67.7 %** of the window's P&L.
- **Part B's counterfactual is linear, which is the model pack 1.4a exists to refute.** It removes
  each blocked trade's P&L additively at its recorded size; under `derisk_mode: smooth` removing a
  loser would raise size on every subsequent trade. The direction is that Part B *understates* the
  cap's effect. Closing that loop is a straightforward extension and was not done here.
- **The cap has no selection freedom.** The set of later-bar same-cluster re-fires *is* the blocked
  set, so a structure-matched null would be degenerate. The uniform null is the only available
  placebo, and the question it answers — "would removing 37 arbitrary trades have done as well?" — is
  the decision-relevant one. But the test has little power: a 3.8 pp band against a 0.09 pp gap.
- **Part A measures sizing and bucketing, not P&L.** Pricing the re-key needs re-generation, which is
  Session K's territory.
- **The re-key sim is incomplete.** Re-keying `decision_day_of` would also re-key the unconditional
  one-unit-per-(sleeve,symbol)-per-day cap (`book_owner.py:1601-1606`); only the cluster cap is
  re-keyed here. Measured effect on this window: **0 additional blocks**.

---

## 4. Withdrawn, corrected, and what the adversarial pass changed

Two refuters were run against these three packs with instructions to default to "refuted" when
uncertain. They found nine issues that changed published numbers and **two that voided headline
findings outright**. Everything below is recorded rather than quietly fixed, per working agreement
§6.

**4.1 — "38 days" was the wrong denominator for the trade substrate.** 99,112 packets span 38
unbroken *write*-days (2026-06-18 → 07-25). The **trade** window is 2026-06-15 → 07-02: **17 calendar
days, 14 reset days per account.** The first version wrote "the same 38 days that produced the R
sequence", inflating the substrate 2.2×. Corrected throughout.

**4.2 — WITHDRAWN: "the first firm-rule breach is at a 10 % dial, and only on FTMO".** The simulator
attributed each trade's realised P&L to the day it **opened**. The live governor attributes it to the
day the deal **closed** (`governor_state.py:202-205`: `DEAL_ENTRY_OUT` only, keyed on the close
deal's `time`), and **26 of 97 FTMO and 25 of 78 redacted_account trades cross a reset day**. Fixed. With
correct attribution FTMO's worst day at the live dial is **−1.047 %, not −1.393 %** (daily proximity
0.209, not 0.279), and **there is no firm daily breach at any dial on either account** — FTMO's peak
daily proximity is 0.831. The total-loss wall is first touched at **15 %**, not 20 %.

**4.3 — CORRECTED: the comparator's redacted_account median was manufactured.** Reported as **+$0.0005**
over 2,569 samples. redacted_account's packets run to 2026-07-24 while its last W7 exit is 2026-07-02, so
**1,557 of those 2,569 samples were identically-zero residuals from a period the pack does not
simulate**, padding n and pulling the median to zero. Window-restricted, the honest figure is
**−$2.1148** over 1,012 samples. FTMO's median is unchanged.

**4.4 — REBUILT: the null control was measuring size↔outcome de-pairing, not order.** Version 1
permuted the realised-R *values* while leaving each slot's recorded `live_risk_pct` welded in place.
Since `live_risk_pct` spans 26× across trades, that destroyed the pairing between an outcome and the
size it was taken at — which is not order. A refuter showed the damage: with the governor feedback
switched off entirely the version-1 "band" is *wider* than with it on, i.e. essentially none of it
was the governor. The rebuilt null permutes whole trades (R **and** intrinsic size) and re-derives
the live reference along the permuted path. **The reported order-dependence at the live dial falls
from 3.77 pp to 0.169 pp (FTMO) and 4.86 pp to 0.253 pp (redacted_account) — a 22× and 19×
overstatement.** The derived claim *"the same 175 trades produce a profitable fortnight in the upper
tail at every dial ≤ 4 %"* is **false and withdrawn**: below 8 % every percentile is negative. The
surviving claim is narrower and better: order-dependence is ~0.2 pp at the live dial and becomes
material only above 8 %.

**4.5 — WITHDRAWN IN FULL: "moving redacted_account one hour changes its worst day by 2.66×".** The trade
rows compute `day_key_ftmo_reset` only for accounts whose firm resets on a named calendar
(`w7_live_forensics.py:599-607` returns `None` when the firm resets at server time). redacted_account
resets at server time, so that field is **`None` on all 78 rows**, and the alternate-rule arm bucketed
the entire 17-day window under a single `None` key. Every number in that finding was an artifact of
a 17-day cumulative bucket tripping the −3 % soft daily stop once. The script now resolves reset days
through `broker_clock` at each instant and **raises rather than returning None**. Re-measured: the
reset calendar changes **nothing** on either account at any dial. §1.6 is now a clean null result,
which is the more useful finding and the one B56 actually earns.

**4.6 — CORRECTED: the shed A/B's null was variance-reduced 8×.** Every deterministic arm was
compared against the **mean of 64** random draws. Averaging divides the null's per-case standard
deviation by 8 and roughly doubles log₁₀p; the incumbent's edge is **0.99σ** against a single draw
and 7.96σ against the mean of 64. The reported "wins 88.8 % of binding cases, log₁₀p ≈ −860" becomes
**wins 60.18 % (arena C) / 69.65 % (arena D) against a single draw**. Also: log₁₀p is a knob on
`--synth-cases` (≈ −0.15 per binding case), so it restated the sample size. Both comparators are now
computed and win-rates are reported as primary.

**4.7 — CORRECTED: the day-key MC was degenerate by construction of its own sampler, not by
structure.** It drew `running` from `[0, na_utc_per_cycle]`, which forces
`max(na_utc, running) = na_utc` and `max(na_runtime, running) = na_runtime`, so the ratio could not
move and "2,000 draws" recomputed one number 2,000 times. The bound is contradicted by the record:
recorded `na` tags reach **11** against a per-cycle reconstruction that never exceeds **3**. Drawing
to the recorded maximum gives a real distribution and a **smaller** effect: mean size ratio
**1.001856** (was 1.011220), buckets changed **0.57 %** (was 3.45 %). The structural inequality
`na_runtime ≥ na_utc` does hold (0 of 637 rows violate it); the claim "invariant to the running state
the export cannot recover" does not, and is withdrawn.

**4.8 — CORRECTED: "129 correlated-unit buckets removed" was counting the wrong thing, and the JPY
sub-finding is withdrawn.** `sum(len(bar_days) − 1)` counts extra **(cycle, bar-day) partitions**,
not `(day, cluster)` buckets — Part A never resolved a cluster at all. Resolving it through the live
registry gives **268 → 225, i.e. 43 buckets removed**. Also "71 cycles span two bar days" was wrong:
71 span *more than one*, and 24 span three or more (one spans ten). Separately, the claim that the
`jpy` exemption is "a second, independent line of evidence for ending the JPY trial" is withdrawn —
the gap sits inside a null band 3.8 pp wide, and reading it while refusing to read a same-sized
runtime-vs-UTC ordering was inconsistent.

**4.9 — NARROWED: the identity check is algebraically forced.** At the live dial the sizing ratio is
1 and `cap_cf/cap_live` cancels, so the check passes even with `_cap_mult` replaced by a constant. It
was framed as "the single check that decides whether any of the rest means anything". It is not; it
tests trade counts, exogenous symmetry and event ordering, and it is now claimed for exactly that.

**Smaller fixes made in the same pass:** band-mode cells at dial ≥ 2 % were discarding the
dial-independent exogenous P&L (they returned before the event loop); `flatten_dd_hits` and
`flatten_daily_hits` used hardcoded 0.09/0.04 instead of config-derived limits; three config
citations were off (`agent_config.yaml:1306` → **:1302** for the live dial profile;
`:1335-1344` → **:1332-1335,1345**; `:1348-1351` → **:1353-1356** for the flatten block); the cap
percentile used a 3-point interpolation that was off by up to 30 % relative and is now a true ECDF;
"623 non-zero headrooms" is **622** (623 includes the zero).

**What survived unchanged:** the D1 four-cluster and 28.6 % reproductions; the D2 12/4 census; the
arena-A result that the cap never bound (max utilisation 0.465375, zero shed units); "every
cluster-cap configuration underperforms random blocking"; the dial-ranking-is-arithmetic result; the
B65 linearity correction; and `cluster_cap_sim`'s fidelity to `book_owner.py:1607-1617`, which was
verified predicate by predicate.

---

## 5. Reproduce

```bash
python3 scripts/evidence_pack_dial_grid.py      # ~25 s (400 order-only null permutations x 17 dials)
python3 scripts/evidence_pack_shed_ab.py        # ~20 s (two synthetic arenas x 20,000 cases)
python3 scripts/evidence_pack_day_key_mc.py     # ~8 s
```

All three read the VPS export at
`/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz`
(outside the repo, outside git) and `phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl` (in-tree). Each
refuses an unhydrated LFS pointer rather than reading it as an empty stream. Seeds fixed at 20260727.

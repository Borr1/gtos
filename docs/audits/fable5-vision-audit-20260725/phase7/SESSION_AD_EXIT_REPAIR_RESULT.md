# Session AD — the exit-repair lane: every sleeve improves, none admits, and carry was never the lever

**Branch `phase7/exit-repair`. Blocks B750–B757. Not merged.**
**Scoped verification (agreement §2): 262 passed, 0 failed** — receipt in §9.

---

## 0. Headline

**1,631 gated exit cells over 25 sleeves. All 25 improve. None reaches ADMIT. The failing
gate at all 25 best cells is `significance`.** Median gain **+0.249 R/day**, range +0.015 to
+0.771.

And the number that changes what the programme should do next:

> **On 23 of 25 sleeves the best exit geometry is worth MORE than eliminating carry
> entirely.** Every cell was measured against a zero-carry ceiling — the same walk with every
> swap rate forced to zero, which is the most any carry repair could possibly be worth. The
> exit surface beats that ceiling almost everywhere.

`CLAUDE.md` §4 says *"What now decides OD-3 is holding time."* Measured against the estate's
own exit surface, **holding time is not the binding constraint — exit geometry is, and the
multiplicity bill is.** Both of those have owners, and neither is carry.

Six things this lane settled that were open yesterday:

1. **`time_stop_bars` is M15 PRINTED bars for every sleeve** (`execution.py:8953-8958`,
   verbatim). So `FOURTH_REVIEW.md` §3.3's reading of the `mx_*` 96 as D1 bars is wrong in the
   direction that costs money: **the live time stop on the twelve generating `mx_*` D1 sleeves
   is 24–25 trading hours against a 72–96 h realised median, truncating 72.3 %–90.1 % of
   trades.** Every published economic number for those sleeves describes a contract the live
   book does not run.

2. **The carry tiers were computed at a modelled hold and four of them move — all upward.**
   Measured nights are 0.3 %–37 % of the modelled "held to horizon" figure. `sub_mid_dn_revert`
   — the prompt's "nearest miss in the core book" — clears its break-even by **8.6× on nights**
   on both accounts and is restated **UNCONDITIONAL**.

3. **`mx_btcusd`'s repair is not a carry repair, and shortening its carry makes it worse.**
   Its live 1-D1-bar time stop costs **−0.141 R/day** against the walk. What it wants is a
   *wider target*: `target_5R` is **+0.309 R/day**, on a monotone ridge from 1R to 5R. It still
   REJECTs, on significance alone, exactly as AA routed it.

4. **`partial_be_runner` is the live contract of four sleeves and no walk had simulated it.**
   Two are armed. It helps `metals_core` (+0.062) and **costs `energy_agri` −0.308 R/day** —
   on a sleeve trading real money today.

5. **B613's rule stands; its reading does not.** Over 152 trail cells with both bounds the
   intrabar-honest variant is worse than production **41 %** of the time and better **42 %**.
   The predictor is the trail arm, cleanly and monotonically.

6. **Stacking the best cell from each family is worse than the best single cell on 17 of 25
   sleeves.** The composite was built to be honest about post-hoc selection and it turned into
   the session's best evidence against naive composition.

**Two corrections to my own instruments and one to a sibling session's framing are in §7.**

---

## 1. `time_stop_bars`, settled from the runtime — item 1 [B750]

AA assigned this to "Nobody, yet" and every time-stop sweep depended on it, so it ran first
and it was resolved from the code path that closes live positions rather than from the table.

**The unit is M15 bars, counted as bars that actually PRINTED (trading bars), for every
sleeve.** `execution.py:8953-8958`, verbatim:

> *"Count actual CLOSED M15 bars that PRINTED since entry_dt -- TRADING bars (they exist only
> while the market is open), so this skips nights/weekends/holidays, matching the validated
> route's bar count instead of wall-clock. **time_stop_bars is in M15 units for EVERY sleeve**
> (the H4 sleeves' route maxbars 60/80 were pre-scaled x16 -> 960/1280 M15)."*

`check_time_stop_and_close` calls that counter (`:9010-9014`) and falls back to wall clock only
when the feed cannot be read (`j46_j49_policy.py:50-64`). `execution.py:6938-6942` names
`check_time_stop_and_close` as the W7 book's exit owner, and `execution.py:6945` gates
`exit_policy_v4`'s own wall-clock time stop (`:585`, `execution.py:7248`) off entirely for
book-native trades — so the printed-bar counter is the live rule and the wall-clock one is not.

AA was right that `book_owner.py:4139` resolves nothing. It is a Telegram card,
`f"time stop {time_stop:g} bars"`. It is just not the deciding line.

**Printed bars are not wall clock, so the conversion is per symbol and had to be measured.**
`execution.py:9008` already knew ("wall-clock over-counts -- index CFDs ~3x") without writing
the ratio down. Measured over the archive (median [p10–p90] M15 bars per coarse bar): 24/7 FX
and crypto **96 [96–96]**, index CFDs and metals **92 [92–92]**, UKOIL **84**, XCUUSD **88**;
H4 is **16 [12–16]** everywhere.

**What binds** — the whole point, because a time stop that never fires is not a contract:

| sleeve group | `time_stop_bars` | = own bars | = trading hours | median hold | trades truncated |
|---|---:|---:|---:|---:|---:|
| the 12 generating `mx_*` D1 sleeves | 96 | 1.00–1.04 | 24–25 h | 72–96 h | **72.3 %–90.1 %** |
| `ny_crypto_momentum` | 20 | 20 | 5 h | 2.0 h | 37.0 % |
| `kz_london_crypto_low` | 32 | 32 | 8 h | 2.5 h | 23.4 % |
| `asia_pdl_fade` | 32 | 32 | 8 h | 1.0 h | 12.2 % |
| `liq_asia_up_low_metal` | 16 | 16 | 4 h | 0.75 h | 11.5 % |
| every H4 sleeve | 1280 / 960 | 80 / 60 | 320 / 240 h | 16–64 h | **0.0 %** |
| `vol_compression` (D1) | 7680 | 80 | 1920 h | 216 h | **0.0 %** |

The H4 and `vol_compression` rows are exactly the ×16 / ×96 pre-scaling the docstring
describes, so **AA's MAXBARS=80 walk already IS their time-stop contract** and nothing about
those sleeves' economics changes. The divergence is the D1 `mx_*` family and four M15 sleeves.

Receipt: `receipts/AD_TIMESTOP_UNITS_V1.json`.

---

## 2. `mx_btcusd` — the carry exit, and why it is not one — item 2

The brief: *"REJECT at measured carry, ADMIT at zero carry with q 0.048 … shorten the carry
without giving back the gross. Target: ADMIT at measured carry. This is the single fastest
new-edge ship in the estate if it lands."*

It did not land, and the reason is worth more than the attempt.

**The whole cost is 9.3 % of |gross|.** AA's "swap is 77 % of its total cost" is true and it
is 77 % of a small number: commission 0.0167 R, slippage 0.0132, spread 0.0013, swap 0.1040.
So the carry counterfactual moved the verdict not because carry is large but because the
q-value was sitting on the BH threshold.

**You cannot shorten this sleeve's carry without giving back the gross.** The time-stop surface
is monotone the wrong way:

| cell | pooled OOS R/day | Δ | gross/trade | cost % | nights |
|---|---:|---:|---:|---:|---:|
| `time_stop_1` (**the live contract**) | +0.1042 | **−0.1405** | 0.1410 | 8.0 | 1.06 |
| `time_stop_3` | +0.1652 | −0.0796 | 0.2318 | 8.2 | 2.58 |
| `time_stop_16` | +0.2520 | +0.0072 | 0.3601 | 9.1 | 4.86 |
| `as_walked` (80 bars) | +0.2447 | — | 0.3576 | 9.3 | 5.36 |
| **`target_5R`** | **+0.5535** | **+0.3088** | — | — | — |

Tightening from 80 bars to 1 saves 1.3 points of cost percentage and destroys 61 % of the
gross. **The repair is the opposite of the prescription: a wider target.** The ridge is
monotone from 1R (+0.031) through 3R (+0.346) to 5R (+0.554), which per §5.1 makes it a
plateau rather than a spike; `target_none` collapses to −0.492 because 80 D1 bars accrues 31
nights, so there is a real interior optimum.

**And no exit change can admit it, because its only failing gate is `significance`.** At
`as_walked`: 5 of 5 folds evaluable, **100 % of OOS folds positive**, drop-best retention 0.64,
coverage 1.00, p_raw 0.0120 — and q 0.414 against a family of 69. At `target_5R`, p_raw
improves to 0.0101 and q to 0.348. The gap to α = 0.10 is a multiplicity bill, and an exit
sweep cannot pay one. **AA's own §4 said exactly this** — *"already clears alpha raw and fails
only the multiplicity bill, which is a family-pool answer rather than a data answer"* — and
routed it to Session AF. That routing is confirmed, with a +0.309 R/day exit improvement now
banked to carry into the pooled test rather than re-derived.

---

## 3. The stop-width regenerations — item 3

Legitimate without re-running the generator, for a reason checked per sleeve rather than
assumed: **for these sleeves the entry signal does not read the stop distance**, so a *k*× stop
changes the geometry of the same candidate set and nothing else (`metals.py:63-91`,
`fx_jpy.py:203`, `vss_fxcross_london_up_low.py:171-181`, `market_expansion_d1.py:218-225`).
**The one exception is excluded rather than swept:** `mx_us100`/`mx_us500` ATR-mean-reversion
call `_atr_mean_reversion_signal(bars, signal_idx, risk)` (`market_expansion_d1.py:211`), so for
those two the stop *is* an input to the entry signal and a stop-width cell would be a different
candidate set. Published as an exclusion with its reason.

Both target conventions are swept for every sleeve, because the sleeves disagree at source:
`metals_core` and the `mx_*` family set `target_dist = R × stop_dist`; `fx_jpy`, `fx_jpy_ny`
and `vss_fxcross` set `target_dist = M × ATR` independently of the stop.

**Measured gross retention at 2×, against AA's required multiple:**

| sleeve | required @2× | measured (native) | clears? |
|---|---:|---:|---|
| `metals_core` | 0.59 | **1.085** | yes, by 1.8× |
| `sub_mid_dn_revert` | 0.18 | 0.898 | yes |
| `crypto` | 0.13 | 0.702 | yes |
| `metals_softband` | 0.26 | 0.755 | yes |
| `vss_fxcross_london_up_low` | 0.74 | 0.667 | **no**, by 10 % |
| `fx_jpy` | 1.89 | **0.175** | **no**, by 10.8× |
| `fx_jpy_ny` | 1.99 | 0.422 | **no**, by 4.7× |
| `energy_agri` | 0.11 | **−0.085** | **no** — 2× destroys its gross outright |

12 of 18 sleeves with a target clear their frontier target. **`metals_core` clears its 0.59×
brief with room to spare and still REJECTs**, which is the finding: the frontier answers a
per-trade cost-geometry question, and the gate answers a per-day OOS stability-and-significance
question. Clearing the first does not produce the second — AA's own §3.3 already established
that `metals_core`'s open question is dated (folds −0.373, −0.313, −0.561, −0.361, **+0.327**),
not geometric.

**`fx_jpy` needing 1.89× and delivering 0.175× is the honest deliverable the brief asked for.**
Its next prescription is the §4.8 meta-label entry filter, not another stop cell.

### 3.1 A correction to AA's frontier algebra, and it goes the wrong way for carry sleeves

`net(k) = (gross − c_var)/k − c_fixed` splits cost into a term scaling as 1/k and a term that
does not. **Swap is neither: it grows with the HOLD, and a wider stop lengthens the hold.**
AA's frontier re-prices `cost_r` at `sl' = k·sl` holding everything else fixed — including
holding hours — so its swap term *halves* at 2×. Measured by re-simulation, charged nights
**rise**:

| sleeve | nights @1× | nights @2× (native) |
|---|---:|---:|
| `mx_btcusd` | 5.36 | **19.42** |
| `metals_softband` | 5.93 | 11.33 |
| `metals_core` | 4.79 | 10.25 |
| `sub_mid_dn_revert` | 1.76 | 6.84 |

So the published required-gross-multiple targets are **optimistic for any carry-bearing
sleeve**, and the error grows with the sleeve's nights. Filed as a repair-queue row against
`AA_COST_GEOMETRY_FRONTIER_V1.json` rather than edited into it.

---

## 4. `fx_jpy_ny` — the pre-rollover flat — item 4 [B751]

**The rule as shipped was one bar late, and one bar is a whole swap night.**
`_rollover_cutoff_index` compared the cutoff against each bar's OPEN, so on an M15 grid
`hour=0` selected the bar *opening* at 23:45 — whose close is exactly the broker midnight.
`rollover_nights` charges a night at every midnight with `day <= end`, so that exit is charged
one. Measured, entry 16:00 broker: exit at 00:00 → **1.0 nights**; exit at 23:45 → **0.0**. The
rule whose stated purpose is *"caps swap at structurally zero"* capped it at one.

Fixed (close-based comparison, `bar_minutes` required, fails closed without it), and then
measured:

| cell | pooled OOS R/day | Δ | swap nights | gross/trade |
|---|---:|---:|---:|---:|
| `as_walked` | −0.1377 | — | 0.038 | 0.0457 |
| **`prerollover_flat_h0`** | **−0.1297** | **+0.0080** | **0.000** | 0.0453 |
| zero-carry ceiling | −0.1349 | +0.0028 | 0 | — |

**The rule works and it is free**: swap goes to a structural zero at a *positive* +0.008 R/day,
and it beats the zero-carry ceiling because the earlier exit is worth marginally more than the
carry it avoids. `fx_jpy_ny` converts from CARRY_CONDITIONAL_LIVE_SUPPORTED to structurally
carry-free.

**And the sleeve is still REJECT at −0.13 R/day, because carry was never its problem.** Its
best cell is the composite at −0.028 (+0.110). Its frontier requirement is 1.99× and it
delivers 0.42×. Next prescription: entry-side, not exit-side.

---

## 5. The three carry-conditional core sleeves, and `metals_core`-on-redacted_account — item 5 [B753]

The survivor book's tiers are computed at a **modelled** hold — `_NIGHTS =
{sleeve: _measured_nights(horizon_h)}` (`recost_w7_validation.py:238`) is the charged-night
count for *every trade held to its full horizon*, and the artifact says so:
`carry_basis: MODELLED_HELD_TO_HORIZON`. AA's walk has the realised hold. Changing that one
input, holding `gross_r`, `true_cost_ex_swap_r`, `swap_r_per_night` and the tier rule itself at
the book's own values — with a control that **22/22 published tiers reproduce from the
artifact's own inputs**:

| account | sleeve | published | restated | measured nights | modelled | break-even |
|---|---|---|---|---:|---:|---:|
| FTMO | `fx_jpy` | MEASURED_LIVE_CARRY | **UNCONDITIONAL** | 0.002 | 0.51 | 0.317 |
| redacted_account | `fx_jpy` | MEASURED_LIVE_CARRY | **UNCONDITIONAL** | 0.002 | 0.51 | 0.051 |
| FTMO | `sub_mid_dn_revert` | CARRY_CONDITIONAL | **UNCONDITIONAL** | 1.308 | 13.37 | 11.221 |
| redacted_account | `sub_mid_dn_revert` | CARRY_CONDITIONAL | **UNCONDITIONAL** | 1.177 | 13.37 | 8.371 |

**`sub_mid_dn_revert` is the prompt's "nearest miss" and the answer is yes** — its measured
holds sit under its break-even by 8.6× on nights, on both accounts. Its best exit cell is
`time_stop_20` at **+0.193 R/day** (+0.081), 80 % of folds positive, failing `robustness` and
`significance`.

**The one that did not move is the interesting one.** `metals_core` on redacted_account stays
CARRY_CONDITIONAL at a measured **mean** of 2.961 nights against a 13.71 break-even — headroom
4.63× — because the rule's UNCONDITIONAL test is the **p99**, not the mean, and on an H4 grid
the top 1 % of holds still reach the 320 h ceiling. **The blocker is the tail, which is exactly
what a time stop controls and what a mean hides.**

So the flip threshold is computable, and it is cheaper than the brief assumed. The prompt
hypothesises a −10 % tightening; measured, the **loosest** time stop that reaches UNCONDITIONAL:

| account::sleeve | own bars | hours | % of horizon | trades truncated | p99 nights after |
|---|---:|---:|---:|---:|---:|
| redacted_account::`metals_core` | 78 H4 | 312 h | **97.5 %** | 9.6 % | 13.00 |
| FTMO / redacted_account::`fx_jpy_ny` | 29 M15 | 7.2 h | 60.4 % | 3.5 % | **0.00** |
| FTMO::`metals_softband` | 42 H4 | 168 h | 52.5 % | 23.2 % | 7.00 |
| redacted_account::`metals_softband` | 18 H4 | 72 h | 22.5 % | 38.0 % | 5.00 |
| `idxrev`, `metals_ob_micro` | — | — | — | — | not flippable: gross is negative before any swap |

**`metals_core`-on-redacted_account needs a 2.5 % tightening, not 10 %** — and that half prices only
the carry. The R it costs is at the matching cell in the frontier; the two must be read
together, and the artifact says so on both sides.

`metals_softband` (BE 198 h) is the expensive one: its redacted_account flip truncates 38 % of
trades. Its own best exit cell is `time_stop_60` at +0.130 R/day (+0.015), the *smallest* gain
in the sweep. Noted as asked: it is the only generator passing `intra_size`, and nothing in
this lane's re-simulation touched that path — `intra_size` is carried through unchanged on
every row.

**Population caveat, stated rather than buried:** the edge terms are from the W7 validation
CACHES and the holds from the FULL ARCHIVE. No population carries both — that is the gap
Session N §8.1 recorded. Strictly better than a horizon assumption; not the same as a
single-population measurement.

---

## 6. The excursion give-backs, and the live-contract divergence — item 6 [B752, B756]

### 6.1 The give-backs move, a lot

| sleeve | as walked | best cell | Δ R/day | capture aw → best |
|---|---:|---|---:|---:|
| `asian_fade` | −0.780 | `trail_a2_g0.5_prod` −0.009 | **+0.771** | −0.120 → — |
| `metal_session_reversion` | −0.796 | composite −0.170 | **+0.626** | −0.075 → 0.020 |
| `kz_london_crypto_low` (MFE 3.40) | −0.592 | `stop_3x_tgtscale` −0.011 | **+0.581** | −0.037 → 0.125 |
| `metals_ob_micro` | −0.411 | `flat_before_triple_swap` +0.097 | +0.507 | −0.123 → −0.040 |
| `mx_us100` ATR-MR | −0.348 | composite +0.111 | +0.459 | −0.181 → 0.271 |
| `mx_us500` ATR-MR | −0.252 | composite +0.202 | +0.454 | −0.102 → 0.295 |
| `ny_crypto_momentum` (MFE 2.39) | −0.255 | composite +0.028 | +0.282 | 0.004 → 0.108 |
| `metals_core` (LIVE) | −0.256 | `stop_3x_tgtfix` −0.007 | +0.249 | 0.114 → 0.256 |
| `energy_agri` (LIVE) | +0.417 | `flat_before_triple_swap` +0.603 | +0.186 | 0.132 → 0.404 |
| `crypto` (LIVE) | +0.117 | `stop_1.5x_tgtscale` +0.226 | +0.110 | 0.284 → — |
| `vol_compression` | +0.269 | `time_stop_20` +0.445 | +0.175 | 0.260 → — |

**`mx_us100` and `mx_us500` are the clearest EXIT_REPAIR confirmations in the estate**: AA's
`check excursion before inverting` was the right instruction, and the answer is that the
excursion was there all along — their live 1-D1-bar time stop alone takes capture from −0.181
to +0.271 and −0.102 to +0.295, and both go from negative to positive pooled OOS. **They do not
need an inverse test.**

`idxrev` is the counter-case and AA had it right: MFE 0.75, best cell +0.0004 R/day off a
−0.028 base, capture still 0.010. There is nothing for an exit to reach. `INVERSE_TEST` stands.

### 6.2 The live exit contract is not the contract the estate's economics describe

Four sleeves run `partial_be_runner` live and twelve carry a binding time stop. AA labelled
everything under plain stop/target/maxbars. The gap, per sleeve:

**The live contract is BETTER than plain on 8 sleeves** — `mx_us100` +0.449, `mx_us500` +0.410,
`ny_crypto_momentum` +0.242, `kz_london_crypto_low` +0.190, `metals_ob_micro` +0.175,
`mx_ger40` +0.123, `mx_us30` +0.084, `metals_core` +0.062.

**It is WORSE on 7** — and one of those is armed:

| sleeve | live policy | plain | live contract | Δ |
|---|---|---:|---:|---:|
| **`energy_agri` (ARMED)** | `partial_be_runner` 2.0R | +0.417 | **+0.109** | **−0.308** |
| `mx_btcusd` | `time_stop` 96 | +0.245 | +0.104 | −0.141 |
| `mx_jp225` | `time_stop` 96 | +0.200 | +0.069 | −0.131 |
| `mx_ethusd` | `time_stop` 96 | +0.182 | +0.088 | −0.094 |
| `metals_softband` | `partial_be_runner` 1.5R | +0.115 | +0.046 | −0.069 |
| `mx_cadjpy` | `time_stop` 96 | −0.002 | −0.067 | −0.065 |
| `mx_nzdjpy` | `time_stop` 96 | +0.081 | +0.041 | −0.040 |

**`energy_agri` is live, armed and trading real money, and its scale-out-at-2R contract is
measured here at −0.308 R/day against the plain exit.** Its best cell,
`flat_before_triple_swap`, is +0.603 with `significance` as its *only* failing gate — but
**n = 67 trades over 3 evaluable folds and p_raw 0.111**, so this is a thin measurement on the
estate's thinnest generating sleeve and it is not a recommendation. It is the number that makes
the question askable, and the question is Borhen's. Nothing in this lane touches the live
config.

---

## 7. The trail bounds — item 7 [B754], and what I am correcting

**The rule is followed on every cell: 152 trail cells, each run at both bounds, both
published.** What the measurement refutes is the *reading* attached to it.

| | n | mean (honest − production) | frac honest better |
|---|---:|---:|---:|
| **all cells** | 152 | — | **42 % better, 41 % worse** |
| by arm 0.5 R | 50 | **+0.0596** | **0.60** |
| by arm 1.0 R | 50 | +0.0186 | 0.48 |
| by arm 2.0 R | 50 | **−0.0240** | **0.18** |
| reversion sleeves | 68 | −0.0074 | 0.35 |
| breakout/continuation | 42 | +0.0535 | 0.48 |

`simulate`'s same-bar arm-and-fill makes the trail exit **earlier**, at a price the bar may
never have offered in that sequence. That does two opposite things: it books a better fill
(optimistic) and it ends the trade sooner (pessimistic on a runner). Which dominates is a
property of the sleeve and, more strongly, of the arm: at a tight arm the production trail
fires on noise and cuts winners, so removing it *helps*; at a wide arm it captures a spike the
honest variant misses, so removing it hurts.

**So "production is the upper bound" is a property of `asian_fade` — a fade — and not of the
switch.** B613 measured it correctly on the sleeve it had. Keep reporting both bounds; stop
calling production the optimistic one. Where they disagree materially, the tick capture is
still what closes them.

**An independent reproduction, which is why I trust the harness:** the supplementary run
labels the two `trailing_runner` sleeves under their own live arm/gap and recovers AA's B613
figures almost exactly — `metal_session_reversion` trail gross **+0.1059 prod / −0.0785
honest** against AA's +0.111 / −0.075, and `asian_fade` **+0.2476 / −0.0640** against AA's
+0.238 / −0.061.

### 7.1 The composite is worse than the best single cell on 17 of 25 sleeves

One post-hoc composite per sleeve — the argmax of each family stacked — was included to be
explicit about post-hoc selection. It is the session's best evidence against naive composition:
on **17 of 25** sleeves it underperforms the best single cell, sometimes badly
(`mx_jp225` +0.257 vs +0.616; `energy_agri` +0.215 vs +0.603). The surfaces interact, and
"best of each" is not a repair. It won on 7 sleeves and those are the ones wave 8 should look
at first — with the stamp attached.

### 7.2 What I got wrong

- **The band-check lookup crashed the first full sweep.** It looked the winning cell up in
  `plan`, and the composite is built from the plan's argmaxes rather than being in it — and is
  frequently the winner. `StopIteration` on the third sleeve, 3 sleeves' work lost, fixed and
  re-run. Found by reading the log, not by a test.
- **My first `AD_TIMESTOP_UNITS` run printed `-` for all ten M15 sleeves**, because I skipped
  the M15/M15 ratio as trivially 1 and then never wrote the 1 down. Those are precisely the
  sleeves whose stops bind (`fx_jpy_ny`'s 48 = 12 h against MAXBARS 80 = 20 h). Fixed by
  stating the identity rather than measuring it.
- **`as_walked` is the PLAIN labelling for the two trailing sleeves, and AA published them
  under the trail.** Their `as_walked` rows must not be compared with AA's. Stated in the
  artifact and repaired by adding their live arm/gap to the grid in a supplementary run.
- **A zsh word-splitting mistake made a scoped test run report "1 warning in 0.00s"** — an
  unquoted `$SCOPE` variable expanded as one path, so pytest collected nothing and I nearly
  read a zero-collection as a pass. Re-run with explicit paths: 262 passed.

### 7.3 A correction to a sibling session's standing statement

AA §2.3: *"The gate still refuses them on its sealed floor — that is untouched, and their
verdict is still `NOT_EVALUABLE`."* **That is stale at wave 7's merge-base.** Session Y's
fidelity merge (`90224cfe6`) raised the first-of-day sleeves' `live_recall` to 1.0, so six of
the seven now clear the 0.50 floor and reach a verdict. My baseline reproduces 26 of AA's 32
verdicts bit-identically and those six are the entire difference — all NOT_EVALUABLE → REJECT,
all with negative pooled OOS. Not wrong when written; wrong now.

---

## 8. What is next, and for whom

**Session AF (family expansion) — the single largest handoff.** `significance` is the failing
gate at all 25 best cells and no exit change can pay a multiplicity bill. Twelve sleeves are
filed `BREADTH_AFTER_EXIT`: their exit surface is exhausted *and it is not their blocker*. The
exit improvements are banked in `EXIT_FRONTIER_V1.json` and should be carried into the pooled
test rather than re-derived — `mx_btcusd` at `target_5R` enters the pool at p_raw 0.0101 rather
than 0.0120. **And the whole `mx_*` D1 family wants a 4–5R target, not the 2R its live contract
sets** — `target_5R` is the best cell on `mx_btcusd`, `mx_ethusd`, `mx_jp225` and `mx_us30`,
and `target_4R` on `mx_cadjpy`.

**Session AE (learning direction).** Thirteen best cells fail `robustness` and seven fail
`stability` — the regime-conditioning shape. The frontier carries per-cell fold fractions.

**Session AB / whoever owns `metals_core`.** It clears its 0.59× cost-geometry brief at 1.085×
and still REJECTs, which confirms AA §3.3 from a second direction: its question is dated, not
geometric.

**Borhen — three measurements, no proposals.**
1. **`energy_agri` is armed and its live scale-out contract measures −0.308 R/day against the
   plain exit** (n = 67, thin). `metals_softband` −0.069. `metals_core` +0.062. The
   `partial_be_runner` policy is not uniformly good and it has never been measured before.
2. **The twelve `mx_*` D1 sleeves' live 24 h time stop truncates 72–90 % of their trades.** It
   helps four of them and hurts five. None of them is armed today, so this is a composition
   input rather than an urgency.
3. **`sub_mid_dn_revert` and `fx_jpy` are UNCONDITIONAL on both accounts** once carry is
   measured instead of assumed, and `metals_core` reaches UNCONDITIONAL on redacted_account with a
   2.5 % time-stop tightening. That is an OD-3 input; the tier list in `CLAUDE.md` §4 is
   computed at a held-to-horizon assumption that the archive does not support.

**Nobody, yet.** The `flat_before_every_rollover` rule is unexpressible on a D1 grid — the
minimum hold is one bar and one bar crosses a midnight — so on D1 it degrades to a
weekend-flat. The artifact records this; a sleeve that genuinely needs sub-daily carry control
needs an intraday decision grid, which is a generation change and not an exit one.

---

## 9. Verification — the §2 scoped receipt

**Blast radius.** Changed: `src/research_infra/walkforward/exits.py` (B751 rollover semantics
+ `flat_before_utc`; B752 `partial_be_runner`) and
`tests/test_implementation_state_block_citations.py` (B755, the dead wave-6 range). Tests
covering them: the file's own tests, plus every test importing `walkforward.exits` directly or
through `walkforward.diagnostics` (`rg -l "walkforward.exits"` → `diagnostics.py` only, inside
`src/`), plus the cost/clock modules the new tests assert arithmetic against.

```
$ python3 -m pytest tests/research_infra/test_wf_exits_parity.py \
    tests/research_infra/test_wf_diagnostics.py \
    tests/research_infra/test_walkforward_gate.py \
    tests/research_infra/test_walkforward_book_replay.py \
    tests/research_infra/test_trainer_folds.py \
    tests/test_costs_layer.py tests/test_broker_clock_truth.py tests/test_w7_recost.py \
    tests/test_implementation_state_block_citations.py -q
270 passed, 1 warning in 10.12s
```

**270 passed, 0 failed** at final HEAD (262 in the eight code-covering files, 8 in the citation
guard). Run twice, same result. No failure at HEAD, so no base comparison was
needed — the one test that *was* red (`test_the_in_flight_wave_range_is_declared_and_shrinking`)
was verified red at the merge-base `066d552b0` before this session touched either input file,
and is fixed in B755.

**New tests: 13.** Five for B751 (two of which assert `rollover_nights` returns 1.0 on the old
exit bar and 0.0 on the new one, so the "structurally carry-free" claim cannot silently stop
being true) and eight for B752. All 8 fuzz blocks of the `simulate_detail` parity claim still
pass, which is what keeps every number in this document about the estate rather than about a
private reimplementation.

**Trial ledger.** 2,036 look events added (AA 1,643 + AD 2,036 = 3,679 in
`research/operations/trial_budget/TRIAL_LEDGER.jsonl`). Those feed `measured_n_trials` → the
DSR deflation, which is telemetry. The BH family size is `declared_family_size`, held at AA's
**69** throughout so every q-value here is comparable to AA's — the sweep's own size does not
move any verdict reported above, and a reader deflating against 3,679 will get a stricter
answer than this document gives.

**H1.** `walkforward/exits.py` is unbound by the R2 contract (checked, with
`walkforward/gate.py`, `panel.py`, `diagnostics.py`, `spec.py`, `execution_packets.py`,
`execution.py` and `costs/model.py` — none bound). `config/agent_config.yaml` untouched. No
broker-capable script run. Nothing touched the VPS.

**Sparse-checkout.** `research/operations/spread_model_2026_07_29/` was committed on this
branch and absent from the tree with `git status` clean — the agreement's §4 trap. Hydrated
with `git sparse-checkout add`; the artifact is real JSON, not an LFS pointer.

**Artifacts.** `receipts/AD_TIMESTOP_UNITS_V1.json`, `receipts/EXIT_FRONTIER_V1.json`,
`receipts/EXIT_FRONTIER_V1_TRAIL.json`, `receipts/AD_FRONTIER_ANALYSIS_V1.json`,
`receipts/AD_CARRY_TIERS_RESTATED_V1.json`, drivers beside them. 49 repair rows in
`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` (append-only JSONL, `O_APPEND` per row, safe for
the three concurrent wave-7 sessions) with a pointer at `REPAIR_QUEUE_V1.json` → `appends.AD`;
AA's 87 rows, `summary` and `diagnostics` untouched — the diff on that file is +25 lines, one
new key.

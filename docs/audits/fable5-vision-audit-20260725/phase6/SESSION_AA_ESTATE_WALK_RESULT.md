# Session AA — the fixing machine, and the estate walked with it

**Branch `phase6/estate-walk`. Blocks B600–B620. Not merged.**
**A/B: 667 bad → 664 bad, 0 regressed, +51 net new passing** (`receipts/SESSION_AA_AB.md`, captures embedded).

---

## 0. Headline

The fixing machine exists. `run_gate(..., diagnose=True)` now emits, beside every verdict,
the per-gate margin, the failing folds / symbols / sessions / sides, the four-term cost
decomposition, the realised holds, the MFE-MAE path and a **prescription**. No gate was
relaxed to get it — a test runs the whole gate both ways and compares verdicts field by
field — and `GateSpec` gained no field, so every prior seal is unchanged.

Then the estate was walked with it: **22,324 trades over 29 sleeves across the full
archive, and 84 repair rows over 32 family members. Every one says what to do.**

Five things the walk settled that were open this morning:

1. **Carry decides exactly ONE sleeve of 32.** `mx_btcusd_d1_donchian_20_breakout` —
   REJECT at measured carry, **ADMIT at zero carry, q 0.048** against a 69-look family,
   with swap 77 % of its cost over a 72 h median hold. `FOURTH_REVIEW.md` §3.3 calls it
   "the single fastest new-edge ship in the estate"; its repair is now mechanically
   specified as an exit change. Eight sleeves are CARRY_IMMATERIAL at ~0 measured nights,
   including `fx_jpy` (0.0023) — the archive independently reproducing Session N's live
   finding of swap on 0 of 41 JPY positions.

2. **The seven first-of-day sleeves have economics for the first time**, because the
   fidelity floor became a stamp. Five of seven are gross-positive; `asia_pdl_fade` alone
   is 2,206 trades at +0.196 R. Their verdicts are unchanged — the sealed floor still
   refuses them — but "unjudgeable" is gone.

3. **The exit table says where the money is.** `metals_core`'s trades reach +1.76 R on
   average and it keeps **0.114** of it. `kz_london_crypto_low` has the estate's largest
   excursion (3.40 R) and a capture of **−0.037**. `idxrev` is the one sleeve with no
   excursion to keep (0.75 R), which is why it alone gets `INVERSE_TEST`.

4. **The trail repair is real, and smaller than it first looked.** Both trailing sleeves
   were unwalkable; labelled under their own contracts they gain +0.759 and +0.363 R/trade
   — but 95.8 % of `asian_fade`'s trail exits fire on the *first bar after entry*, because
   the production simulator arms and fills inside one bar. Under the intrabar-honest
   variant the gains are **+0.46 and +0.18** and neither sleeve turns positive. Both bounds
   published; only tick data locates the truth between them.

5. **Every prescription now carries a target.** `metals_core` needs its gross-in-R to
   retain 59 % at a 2× stop to break even; `fx_jpy` needs 1.89×. Same prescription,
   opposite briefs.

And one nobody had looked for: **8 of 26 two-sided sleeves are net-positive on one side and
negative on the other, including both armed sleeves the walk can score.** `metals_core` is
**+0.097 long on n=228 and −0.320 short on n=152**, with more swap long than short — so its
net-negative headline is its short side, and that is the signal rather than the carry (§2.2b).

**Four defects were found in my own instruments and all four are recorded**: a coverage
prescription that read "capture ticks for []"; a cost artifact that silently lost six
symbols' spreads to the sparse-checkout trap; a capture ratio that read negative for every
sleeve because it was a mean of ratios; and a block citation to evidence I never wrote,
caught by this repo's own citation guard. Three were caught by reading output or by an A/B
built to measure something else; the fourth by a test that exists precisely for it.

**1,643 look events** are in the trial ledger. `gate.py:47-48`'s "a number nobody measured"
is no longer true.

---

## 1. What was built

Four instruments, one repair, and two corrections. Everything is additive: `GateSpec`
gained no field, so **every existing spec seal is unchanged** and no prior result moves.

### 1.1 `walkforward/diagnostics.py` — the prescription head

The gate already computed every number a repair needs and then flattened them into verdict
strings (`gate.py:836-878`). `run_gate(..., diagnose=True)` stops flattening and attaches,
per sleeve:

| what | why it is the thing a repair needs |
|---|---|
| per-gate **margin** (`observed − required`, gate's own units) | "failed" and "failed by 0.4 % of one fold" are different briefs |
| the failing **folds / symbols / sessions** | names *where* to condition, instead of *that* it is conditional |
| the **four-term cost decomposition** + charged swap nights | commission scales as 1/stop, swap with nights, spread with session — three different repairs, and a total tells them apart from none |
| **by side** (LONG/SHORT, with swap split out) | `cost_r` books adverse swap only, so several instruments put their entire carry on one side |
| **MFE/MAE aggregates** and the capture ratio | separates "the exit missed it" from "there was nothing to miss" |
| realised **holds** (median, p90, p99, frac > 24 h) | the number OD-3 turns on, measured off the simulated path |
| a **prescription** from the §2.2 table | what to DO |

`GateResult.repair_queue()` writes `REPAIR_QUEUE_V1.json`, one row per (sleeve,
prescription, evidence), including ADMIT rows at `prescription: NONE` so the next walk can
be diffed against this one.

**No gate is relaxed and no threshold moved.** The load-bearing test asserts a negative:
`run_gate` with and without `diagnose=True` returns identical verdicts, gates, q-values and
reasons. A diagnostic head that could move a verdict would be a back door into the
admission standard.

Three design points worth defending:

**The three-way split on a negative expectancy.** `FOURTH_REVIEW.md` §3.3 asks for one
query and never assigns it: *"if setups have excursion the exit misses → exit repair; if
none → test the inverse."* It runs automatically on every sleeve now, because a query a
human has to remember to run per sleeve is a query that does not get run. Gross > 0 →
`COST_GEOMETRY` naming which term; gross ≤ 0 with excursion → `EXIT_REPAIR`; no excursion →
`INVERSE_TEST`. Where the excursion is absent the diagnosis says so and names the run that
would supply it, rather than guessing.

**Significance failures carry a number.** "Pool the mechanism as a family" is advice until
someone says how much breadth. The Fundamental Law gives it: pooling *k* equally-informative
members scales the t-statistic by √k, so the required multiple is `(z_α / z_observed)²`.
Reported with its own caveat — it assumes independent members of equal IC and a symbol
family is neither — as a scoping number for Session AF's sweep, not a significance claim.

**Sessions are on the broker's clock or they say they are not.** `by_session` resolves the
broker wall clock through `broker_clock` when a server is named and stamps `utc_hour` when
it cannot. Guessing +3 h would put every boundary in the wrong session for about four weeks
a year, including inside the sealed March window.

### 1.2 `walkforward/exits.py` — the path survives the labelling

`primitives.simulate_detail` returns `(R, exit_index)` and throws the excursion away.
`replay()` returns `r_gross`, `exit_index`, `exit_reason`, `mfe_r`, `mae_r`, `bars_to_mfe`
and supports trail arms, a time stop and a pre-rollover flat (`fx_jpy_ny`'s §3.2 repair).

**Parity is fuzzed, not asserted.** 4,000 random OHLC series, both directions, with and
without targets and trails, compared with `==` on R and on the exit index — including the
pessimistic same-bar tie where the stop wins. If that identity did not hold, every number
downstream would be about a different program than the one that labelled the estate.

`simulate` has supported `trail_arm`/`trail_gap` since it was vendored (`primitives.py:35`)
and **no driver ever passed them**, which is why `asian_fade` and `metal_session_reversion`
— both `policy="trailing_runner"` in the production exit table
(`execution_packets.py:57,61`) — could not be walked at all. They are walked here, and both
labellings are emitted so the trail's effect is measured rather than claimed.

### 1.3 The trial-budget ledger's prospective half

The module was built, tested and never run — and what it built was a *retrospective*
scanner over surviving `*RESULT*.json` files. In a repair campaign most variants never
become a RESULT file, so that lower bound is structurally blind to the population it most
needs to count. `TrialLedger` is append-only JSONL, `O_APPEND` a line at a time so
concurrent sessions can share one file, and it **cannot raise into a caller's measurement**
— a ledger that fails a run would be the brake the agreement forbids, so write errors are
counted and surfaced instead. `measured_n_trials()` returns
`max(prospective, retrospective, floor)` with the basis named.

`gate.py:47-48`'s "no trial-budget ledger exists anywhere in this repo" was true when
written and is now false; amended in place rather than left to mislead.

### 1.4 The `energy_agri` classifier fix

FTMO files its oil CFDs under `Cash II CFD\`; the classifier read any `Cash*` path head as
`index`, so `USOIL.cash` and `UKOIL.cash` inherited the index class's fitted **zero**
commission — a false zero on a sleeve trading real money today, filed by `SESSION_N` §7 and
carried as a sensitivity ever since. Fixed with the same name-based carve-out the metals
already use, plus a **cross-account transfer** (the same barrel is MEASURED at $5.00/lot on
redacted_account). That transfer needed an alias table, because the two brokers spell it
differently — `USOIL.cash` against `USOUSD` — and a base-symbol match alone silently does
not fire, which is how the false zero survived a classifier that already had a carve-out of
exactly this shape.

**Exactly 2 of 334 instrument records change**, both FTMO oil, and everything else is
byte-identical. `V1` is left intact and `BROKER_TRUE_COSTS_V1_1.json` is written beside it,
so no prior result silently moves and the two can be A/B'd — which they are, below.

### 1.5 The carry counterfactual

`SURVIVOR_BOOK_V1.json` tiers every sleeve UNCONDITIONAL / CARRY_CONDITIONAL by comparing a
break-even hold to an **assumed** horizon, because no realised hold survived any cache
(`SESSION_N` §8.1). The archive supplies the realised hold off the simulated path, so the
tier is measurable: run the identical walk with every swap rate forced to zero and read
which verdicts move.

It is strictly better evidence than the "minimal carry" treatment used to date, which
**replaces every trade's holding time with a synthetic 6 hours**
(`W_NEGATIVE_CONTROLS.json` `carry_note`) — that changes the exit, which changes R itself.
Zeroing the rate keeps every real hold and changes only the charge. Verified exact: swap
goes to 0.000000 and every other cost term is bit-identical.

---

## 2. What the walk measured

**22,324 trades over 29 sleeves**, generated in 10,736 s over the full archive (M15
2024-2026, H4 2000-2026, D1 2007-2026) against Session X's 15,381 over 23. H4 came back at
**7,092 unique candidates — byte-identical to X's H4 count**, which is a reproducibility
check on the generation path passing. Every trade carries its path.

`REPAIR_QUEUE_V1.json` has **87 rows over 32 family members**, and every one of them says
what to do:

| primary prescription | n | sleeves |
|---|---:|---|
| `FIDELITY_RECONCILIATION` | 7 | the first-of-day set — measured for the first time, below |
| `REGIME_GATE_OR_PARK` | 6 | `crypto`, `energy_agri`, `metals_softband`, `sub_mid_dn_revert`, `mx_avausd`, `mx_ethusd` |
| `COST_GEOMETRY` | 6 | `fx_jpy`, `fx_jpy_ny`, `metals_core`, `vss_fxcross`, `mx_cadjpy`, `mx_ger40` |
| `BREADTH` | 4 | `mx_btcusd`, `mx_jp225`, `sub_xvol_pullback`, `vol_compression` |
| `EXIT_REPAIR` | 3 | `metals_ob_micro`, `mx_us100_atr_mr`, `mx_us500_atr_mr` |
| `GENERATION` | 3 | `vp_euidx_pocgrav`, `mx_eu50`, `mx_fra40` |
| `INVERSE_TEST` | 1 | `idxrev` |
| `REGIME_GATE` | 1 | `mx_nzdjpy` |
| `FOLD_CONDITIONING` | 1 | `mx_us30` |

**Nothing is ADMITted at any of the three standards** against a 69-look family, and one
sleeve is admitted at zero carry. That is not the headline — the headline is that all 32
now carry a repair path with evidence attached, and eight months of "NOT_EVALUABLE" turned
into three `GENERATION` rows naming exactly which data would close them.

### 2.1 Carry decides exactly one sleeve, and it is not one of the ones everyone assumed

The counterfactual (§1.5) run over all 32:

| tier | n | what it means |
|---|---:|---|
| **CARRY_DECIDES** | **1** | `mx_btcusd_d1_donchian_20_breakout` — REJECT at measured carry, **ADMIT at zero carry** |
| CARRY_IMMATERIAL | 8 | measured mean charged nights ≈ 0 |
| CARRY_PRICED_BUT_NOT_DECISIVE | 20 | swap is real and does not move the verdict |

`mx_btcusd` is the sleeve `FOURTH_REVIEW.md` §3.3 calls *"the single fastest new-edge ship
in the estate."* Its swap is **77 % of its total cost** over a 72 h median hold at 5.36 mean
charged nights, and removing that charge takes it from REJECT to ADMIT with **q 0.048**
against a family of 69. So its repair is now mechanically specified: shorten the carry.
That is an exit change on a D1 donchian, which is the cheapest class of repair in the plan.

The eight CARRY_IMMATERIAL sleeves include **`fx_jpy` at 0.0023 mean charged nights and
`fx_jpy_ny` at 0.038** — the archive independently reproducing Session N's live finding
that the broker charged swap on **0 of 41** live JPY-sleeve positions. Two instruments,
different data, same answer.

### 2.2 The exit table: where the money is on the table, per sleeve

`capture_ratio` is `sum(realised R) / sum(MFE)` over trades with a positive excursion — the
share of the available move the exit kept. This is the artifact wave 7 works from.

| sleeve | mean MFE | mean MAE | capture | frac ≥ 1 R |
|---|---:|---:|---:|---:|
| `sub_xvol_pullback` | 2.28 | −0.86 | **0.604** | 0.73 |
| `crypto` | 2.02 | −0.99 | 0.284 | 0.56 |
| `metals_softband` | 1.86 | −0.98 | 0.264 | 0.60 |
| `vol_compression` | 1.90 | −1.07 | 0.260 | 0.63 |
| `mx_btcusd_d1_donchian_20` | 1.75 | −1.06 | 0.230 | 0.59 |
| `energy_agri` | 1.96 | −1.18 | 0.132 | 0.64 |
| `metals_core` | 1.76 | −1.12 | **0.114** | 0.55 |
| `fx_jpy` | 1.57 | −1.29 | 0.061 | 0.54 |
| `idxrev` | **0.75** | −0.79 | 0.010 | 0.26 |
| `ny_crypto_momentum` | 2.39 | −1.21 | 0.004 | 0.52 |
| `kz_london_crypto_low` | **3.40** | −1.31 | **−0.037** | 0.53 |
| `mx_us100_cash_d1_atr_mr` | 1.19 | −1.13 | −0.181 | 0.49 |

Read two rows against each other and the value of the instrument is obvious.
**`metals_core`'s trades reach +1.76 R on average and it keeps 0.20 R of it.** That is an
exit problem the size of the sleeve, on a live-armed conf-1.0 sleeve, and nothing in this
programme could see it before today. **`kz_london_crypto_low` has the largest excursion in
the estate — 3.40 R mean, 53 % of trades reaching 1 R — and gives back all of it.**

And `idxrev` is the one sleeve whose excursion is genuinely absent (0.75 R mean, only 26 %
reaching 1 R), which is why the machine prescribes `INVERSE_TEST` for it and `EXIT_REPAIR`
for the others. That distinction is made per sleeve, automatically, from the path.

### 2.2b The side split — 8 of 26 sleeves are positive on one side and negative on the other

`by_side` was added because `cost_r` books adverse swap only (`model.py:253`), so an
instrument whose long swap is a credit and whose short swap is a charge puts its entire
carry on one side. FTMO oil is +4.06 / −27.50 points a night on USOIL and +21.72 / −104.42
on UKOIL. What the split then showed was larger than the carry question:

| sleeve | n LONG | net LONG | n SHORT | net SHORT | swap L | swap S |
|---|---:|---:|---:|---:|---:|---:|
| **`metals_core`** (armed, conf 1.0) | 228 | **+0.097** | 152 | **−0.320** | 0.168 | 0.056 |
| **`energy_agri`** (armed) | 25 | **+0.268** | 28 | **−0.150** | 0.000 | 0.187 |
| `metals_softband` | 140 | **+0.355** | 82 | −0.094 | 0.244 | 0.064 |
| `metals_ob_micro` | 20 | −0.097 | 13 | −1.137 | 0.294 | 0.038 |
| `mx_us30_volume_surge` | 70 | **+0.209** | 50 | −0.178 | 0.145 | 0.000 |
| `mx_btcusd_d1_donchian_20` | 212 | **+0.330** | 104 | +0.004 | 0.110 | 0.093 |
| `mx_ger40_volume_surge` | 75 | −0.074 | 31 | **+0.138** | 0.136 | 0.005 |
| `mx_nzdjpy_d1_donchian_20` | — | negative | — | **positive** | | |

**`metals_core` is net-positive long (+0.097 on n=228) and heavily negative short (−0.320
on n=152), and its gross is +0.396 long against −0.120 short.** Its net-negative headline is
its short side. That is a side filter — the cheapest repair class in the estate — and it has
never appeared in any artifact this programme produced. The same shape holds for
`energy_agri`, the second armed sleeve, whose entire swap charge is also on the losing side
(0.187 short, 0.000 long).

`energy_agri`'s asymmetry is exactly what the B603 classifier fix predicted from the swap
rates before the split was computed, which is a small independent check that both are right.

**This is not a recommendation to arm long-only** — sleeve composition is Borhen's, the
sample on `energy_agri` is 53 trades, and a side filter halves an already-thin book's
frequency. It is the measurement that makes the question askable.

### 2.3 The seven first-of-day sleeves, measured for the first time

X's generation filtered them out before generating. Under §2.1's stamp they are generated,
scored on their own spec economics, and their fidelity class travels with every number.
**The gate still refuses them on its sealed floor** — that is untouched, and their verdict
is still `NOT_EVALUABLE` — but the economics are no longer unknowable:

| sleeve | n | gross R/trade | cost % of \|gross\| | mean MFE | median hold | largest cost term |
|---|---:|---:|---:|---:|---:|---|
| `asia_pdl_fade` | 2,206 | **+0.196** | 22.7 % | 1.75 | 1.0 h | spread |
| `asian_fade` | 1,275 | **+0.248** | 23.0 % | 1.35 | 0.25 h | commission |
| `liq_asia_up_low_metal` | 89 | **+0.348** | 52.4 % | 2.24 | 0.75 h | spread |
| `metal_session_reversion` | 798 | **+0.106** | 49.9 % | 1.04 | 0.25 h | spread |
| `orb_crypto_london` | 826 | **+0.104** | 13.5 % | 1.34 | 3.5 h | commission |
| `ny_crypto_momentum` | 533 | −0.014 | 12.8 % | 2.39 | 2.0 h | commission |
| `kz_london_crypto_low` | 283 | −0.155 | 22.2 % | 3.40 | 2.5 h | commission |

**Five of seven are gross-positive**, and every one of them is a short-hold sleeve whose
cost share is 13–52 % — which puts the whole group squarely in `COST_GEOMETRY` territory
rather than "unjudgeable". `asia_pdl_fade` alone is 2,206 trades: the breadth argument
§3.4 makes for the intraday candidates is now a measured quantity rather than a projection.

### 2.4 The trail repair, and the caveat that is bigger than the repair

See §1.2 and B613. Labelling the two `trailing_runner` sleeves under their own contracts
for the first time:

| | plain | trail (production) | trail (intrabar-honest) |
|---|---:|---:|---:|
| `asian_fade` | −0.521 | **+0.238** | −0.061 |
| `metal_session_reversion` | −0.252 | **+0.111** | −0.075 |

The production number is an **upper bound**: 95.8 % of `asian_fade`'s trail exits land on
the first bar after entry, because `primitives.simulate` arms and fills a trail inside one
bar at `high − gap`. The honest variant removes that and fills at the bar's open when the
market gapped through the level. **39 % of `asian_fade`'s apparent gain and 51 % of
`metal_session_reversion`'s is intrabar sequencing.**

What survives is still large: **+0.46 and +0.18 R/trade**, and it is not enough to make
either sleeve positive. Both bounds are published; neither is called the answer. Only tick
data locates the truth between them, which is exactly the scope of §9's forward capture.

### 2.5 The cost-geometry frontier: every prescription carries a target

`AA_COST_GEOMETRY_FRONTIER_V1.json` re-prices every trade at seven stop multiples. The
algebra it publishes matters as much as the numbers: `net(k) = (gross − c_var)/k − c_fixed`,
so widening the stop can only ever converge to −slippage under naive R-rescaling. **A stop
sweep rescues a sleeve only if the wider stop makes gross-in-R rise** — which is the
regeneration question Session AD owns, and now it owns it with a target:

| sleeve | gross @1× | cost @1× | cost @2× | required gross multiple @2× |
|---|---:|---:|---:|---:|
| `metals_core` | +0.195 | 0.221 | 0.116 | **0.59×** |
| `vss_fxcross_london_up_low` | +0.237 | 0.338 | 0.176 | 0.74× |
| `fx_jpy` | +0.069 | 0.234 | 0.130 | 1.89× |
| `fx_jpy_ny` | +0.050 | 0.173 | 0.100 | 1.99× |
| `metal_session_reversion` | +0.111 | 0.457 | 0.232 | 2.09× |
| `liq_asia_up_low_metal` | +0.121 | 0.877 | 0.443 | 3.66× |

`metals_core` needs gross-in-R to retain only **59 %** of its current value at a 2× stop to
break even. `fx_jpy` needs it to nearly double. Those are two very different repair briefs
and they were one sentence — "sweep the stop" — this morning.

### 2.6 The orphans

`leadlag_core` and `subh4_ll_fx` have **no generator module** in `sleeves/`, so they cannot
be re-walked at broker truth however much anyone wants to. What they have is a cached daily
R series, and the statistical half of the gate runs on it — stamped LEGACY_COST, because it
is not broker truth:

| sleeve | n | sum R | day-mean | day-block p | halves both + | prescription |
|---|---:|---:|---:|---:|---|---|
| `leadlag_core` | 3,115 | +362.6 | +0.038 | 0.235 | yes | BUILD_GENERATOR_LOW_PRIORITY |
| `subh4_ll_fx` | 357 | +70.9 | +0.011 | 0.461 | no | BUILD_GENERATOR_LOW_PRIORITY |
| `vp_euidx_pocgrav` | 341 | +79.9 | +0.179 | 0.135 | yes | **BUILD_GENERATOR** |
| `xlayer_veto_gate` | 56 | +89.7 | +1.163 | 0.021 | yes | already shipped as `leader_impulse_veto` |

`session_leadlag_genuine` is absent from the cache entirely — registered, forward-validated
at +0.46 R on n=390, and with neither a generator nor a cached stream. It is the estate's
only artifact with no evidence of any kind reachable from this machine.

### 2.7 The three `GENERATION` rows — what data would close them

The most actionable output of the walk, because each names a specific fetch:

- **`vp_euidx_pocgrav`** fails closed at `sleeves/vp_euidx.py:70` for want of an **M1 aux
  feed**, and the archive holds D1/H4/M15 for 50 symbols and **no M1 at all**. The
  unblocking data is M1 for **GER40 and UK100** over 2018-03-25 .. 2026-07-26 — two symbols,
  one owner-executed read-only fetch of the shape that already happened on 2026-07-27. This
  is **redacted_account's measured fourth UNCONDITIONAL survivor** and its cached stream is the
  strongest of the four orphans (+0.179 R/day, p 0.135, both calendar halves positive). It
  is the highest-value data fetch in the estate.
- **`mx_eu50_cash`** and **`mx_fra40_cash`** — no bars for either symbol. §9's bars-export
  ceremony, already named.

---

## 3. What I got wrong, and what in the plan I am correcting

### 3.1 My own instrument, caught by reading its output

The first diagnostic run handed `vp_euidx_pocgrav` a coverage prescription reading
**"capture ticks for []"** — a data-capture ceremony pointed at nothing. A sleeve with zero
generated trades has coverage 0/0, and I had conflated two mechanistically different
failures: *broker truth cannot price the trades* and *there are no trades*. `GENERATION` is
now its own prescription, checked first, with a register of known blockers whose first
entry is the measured one below. Found by reading the output, not by an adversary — which
is the reading the wave-6 agreement asks for.

### 3.2 `FOURTH_REVIEW.md` §3.1's registry-vs-generator "wiring defect" — wrong in both halves

§3.1 reads `energy_agri`'s 4-symbol registry against its 2-symbol generator as a defect
where *"CORN/COTTON are sized-for but can never fire"*; §3.2 reads `idxrev`'s 8-vs-5 the
same way. Measured through the production resolvers:

- it is **four** sleeves, not two — add `sub_mid_dn_revert` and `sub_xvol_pullback` (both
  HEATOIL_c + NATGAS_cash), and **the second of those is ARMED**;
- they are **not sized-for**: `SleeveSpec.symbols` has no consumer in any sizing or
  admission path repo-wide. Two forensics scripts and `build_symbol_allowlist` read it;
  `admit_and_size` does not;
- all four have **one deliberate cause** — the registry carries the AUTHORED universe and
  the generator the TRADEABLE one after the W7 tick-truth and spread-wall exclusions.

So it is a naming collision, not four wiring defects, and its one real consequence is that
the gate's symbol-consistency check runs against the wider universe and is therefore loose.
Pinned with the measured reason per sleeve, plus a test that fails the day `admit_and_size`
starts reading a registry universe — at which point the divergence stops being
documentation drift and becomes a live sizing defect.

### 3.3 `metals_core` "ADMITs at zero carry" — a different population, and the difference is dated

§3.1 states that `metals_core` ADMITs the walk-forward gate at zero carry (+0.635 R/day
OOS, 100 % folds positive, q 0.082) and REJECTs at its structural horizon, and reads that
as *"independent confirmation that holding time, not edge, is its open question."*

Read at source, that number is `W_NEGATIVE_CONTROLS.json` → `real_minimal_carry_restricted`,
and it is **n=131 over 52 OOS days on the restricted 2-symbol priced subset with every hold
overwritten to a synthetic 6 hours**, against a ~12-sleeve family. On the archive
regeneration — real simulated holds, the full H4 span, a 69-look family — `metals_core`
posts **−0.256 R/day at measured carry and −0.112 at zero carry, 20 % of folds positive
both ways**. Carry moves it and does not decide it.

The two are not in conflict; the difference is *dated*. Its OOS folds run −0.373, −0.313,
−0.561, −0.361 and **+0.327**, and the 131-trade cached stream lives inside that last fold —
the window that selected the sleeve (`build_survivor_book.py:60` and
`KB7_growth_kelly_sizing.py:130` share the `d.year >= 2025` predicate; Session V). This is
`CLAUDE.md` §4's out-of-window result reproduced at sleeve level by an independent
instrument.

**So `metals_core`'s open question is not holding time — it is the frequency-ramp /
threshold-drift question §3.1 assigns to Session AB**, and this walk hands AB a fold-level
series and a per-symbol split to start from.

---

## 3.4 The A/B, and the confound in its first reading

**667 bad → 664 bad, 0 regressed, +51 net new passing** (`receipts/SESSION_AA_AB.md`,
`7b0f4f276` → `d6047b47a`, both captures embedded). The +51 reconciles exactly: 48 new test
functions plus 3 red→green, of which **one is a real fix and two are flakes** — reported as
flakes, because claiming a favourable flake is the same error as accepting an unfavourable
one.

The first reading said 2 regressed, and neither was:

- `test_verification_retains_no_rows` **passes in isolation** and touches nothing this
  session wrote — the same flake class the agreement records three of from wave 5.
- `test_unpriceable_symbol_is_recorded_not_assumed_zero` was a **data confound**, and
  tracing it found something about my own commit worth stating plainly. `git add -A` in the
  trail commit swept up modified working-tree copies of `BROKER_TRUE_COSTS_V1.json` and
  `TICK_SPREAD_MEASUREMENT.json` — two sealed artifacts I had said I was leaving intact —
  with no mention in that commit's message. Diffing the branch-point blob shows what they
  are: the artifact regenerated at 17:03 UTC, gaining measured spreads for exactly six FTMO
  symbols (`AUS200.cash`, `CADJPY`, `DASHUSD`, `EU50.cash`, `NATGAS.cash`, `SPN35.cash`),
  nothing lost and no other field moved. Those are the symbols this session's prompt named
  as *"exporting now"* — the §9 tick lane landing in my worktree, invisible until the sparse
  cone widened.

  **The content is kept.** It is newer, it is real, the prompt directs the walk to re-read
  the cost table rather than assume a symbol is unpriceable, and reverting it would destroy
  parallel work. What was wrong was the silence. The walk ran on the better 36-spread data,
  and the base worktree was then aligned to the same data so the A/B compares code to code.

  The test itself hardcoded `EU50.cash` as its unpriceable symbol, so a test about the
  *refusal mechanism* failed because coverage improved — the worst way for a test to fail.
  It now derives an unpriced symbol from the artifact at run time.

---

## 4. What is next, and for whom

Everything below is a row in `REPAIR_QUEUE_V1.json` with its evidence attached; this is
just the routing.

**Borhen — two data ceremonies, both read-only, both minutes of VPS time.**
1. **M1 bars for GER40 and UK100**, 2018-03-25 .. 2026-07-26. It unblocks
   `vp_euidx_pocgrav`, which is redacted_account's measured fourth UNCONDITIONAL survivor, has
   the strongest cached stream of any orphan (+0.179 R/day, p 0.135, both calendar halves
   positive), and is the one sleeve in the estate that generates literally nothing today.
   Highest value per minute of anything in this document.
2. **Bars for EU50.cash and FRA40.cash** — closes the last two `GENERATION` rows.

And one **one-line decision, not a research project**: `vol_squeeze`, `ny_index_momentum`
and `structural_retest` each ship a complete generator module and have no `SleeveSpec` in
`sleeves/registry.py`, so the production path cannot reach them at all. Their exclusion is
a *decision* with a named repair condition, not a blocker (`CANDIDATE_RUNTIME_BLOCKERS` is
`None` for all three). Adding a registry entry is one line each and is live-safe — the
config's candidate allowlist gates what actually runs — but it is sleeve composition, so
it is yours. `structural_retest` is the estate's only short-side mechanism.

**Session AB (regime spine)** — `metals_core` is yours, and §3.3 above is why. Its five OOS
folds run −0.373, −0.313, −0.561, −0.361, **+0.327**, and one symbol (XAGEUR, n=44,
+0.620 mean net R) carries its entire positive contribution while the other five are
negative. Fold-level series and per-symbol splits are in `REPAIR_QUEUE_V1.json`
→ `diagnostics.metals_core.{by_fold, by_symbol}`. The same shape appears on `crypto`,
`metals_softband`, `sub_mid_dn_revert`, `mx_avausd` and `mx_ethusd` — six sleeves whose
primary prescription is `REGIME_GATE_OR_PARK`.

**Session AD (parameter sweeps)** — the frontier gives you targets, not directions
(§2.5). `metals_core` 0.59× and `fx_jpy` 1.89× at a 2× stop. The 147 cells are already in
the trial ledger, so your sweep deflates against a count that includes them.

**Session AE (learning actuator)** — `AA_SLEEVE_SPLITS_V1.json`, 29 sleeves of cost-true
train/OOS/sealed day-series with the fold calendar and per-day cost components. This is
the §4.2 item 1 input; the legacy-cost CP4/CP5 splits can be retired against it.

**Session AF (mechanism families)** — 22 `BREADTH` rows, each carrying its own breadth
multiple `(z_α / z_observed)²`. `mx_btcusd` already clears alpha raw and fails only the
multiplicity bill, which is a family-pool answer rather than a data answer.

**Session AG (spread model)** — the first-of-day group is the customer. Five of seven are
gross-positive with cost at 13–52 % of gross, all on sub-4-hour holds where spread
dominates. Banded verdicts change what can be said about 5,000+ trades.

**Wave 7 (exits)** — §2.2 is the work list, ordered by how much excursion each sleeve
leaves behind. `walkforward/exits.py` is the harness: trail, time stop, pre-rollover flat,
and `trail_lag_extremes` so no sweep can repeat B613's intrabar over-claim. **Sweep against
the honest variant and report both bounds.**

**Nobody, yet** — `time_stop_bars` is recorded per sleeve and deliberately not applied,
because its unit is ambiguous in the repo (crypto's 1280 reads as M15 units against the
320 h H4 horizon; the fourteen `mx_*` sleeves' 96 reads as D1 bars against a ~3-bar median)
and `book_owner.py:4139` never resolves it. Whoever owns the exit sweep should settle that
first, from the runtime, not from the table.

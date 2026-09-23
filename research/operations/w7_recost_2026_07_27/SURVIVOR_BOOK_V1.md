# SURVIVOR_BOOK_V1 — the W7 book at broker-true costs

**Generated 2026-07-27 by `scripts/build_survivor_book.py`. Stage 1.2, Session N. OD-3's first input.**

Machine-readable: `SURVIVOR_BOOK_V1.json`. Full per-row detail and every sensitivity:
`W7_RECOST_V1.json`. Method, refutations and caveats:
`docs/audits/fable5-vision-audit-20260725/phase3/SESSION_N_W7_RECOST_RESULT.md`.

**This file does not choose the book.** Sleeve composition and the risk dial are Borhen's decisions.
The tiers below are a measurement, not a proposal.

---

## 1. The headline

**The W7 validation survives re-costing. Commission was never the threat. Carry was — and for the
two sleeves where carry could be measured, it is zero.**

Costs come from `src.costs.cost_r` against `BROKER_TRUE_COSTS_V1.json`, charged per trade at that
trade's own stop distance. Each sleeve is then asked how long its average trade can run before broker
carry consumes its edge — a hold in hours, against the longest hold its own exit horizon permits.

| tier | meaning | FTMO |
|---|---|---|
| **UNCONDITIONAL** | no reachable hold takes the edge to zero | `metals_core`, `crypto`, `energy_agri`, `sub_xvol_pullback` |
| **MEASURED LIVE CARRY** | measured live **and** backed by a structural bound | `fx_jpy` |
| **CARRY-CONDITIONAL, live-supported** | 9 live positions on the surviving side, no structural bound | `fx_jpy_ny` |
| **CARRY-CONDITIONAL** | survives iff the mean hold is under its break-even; **not measured** | `metals_softband` (62 % of its max hold), `vp_euidx_pocgrav` (78 %), `sub_mid_dn_revert` (84 %) |
| **DEAD BEFORE COST** | negative gross of every broker cost — the validation already had these | `idxrev`, `metals_ob_micro` |

**No sleeve is killed by commission.** Two were already negative before the validation charged
anything. Two are decided by measurement. **Three remain genuinely open**, and they are open on one
number nobody has: how long the average trade is held.

### What the live window settled

The live W7 book ran three of these eleven sleeves on the same symbols, the same target, the same
exit horizon and the same entry hour as the validation (checked field by field —
`SESSION_N_W7_RECOST_RESULT.md` §8.1). Over that window the broker charged swap on:

- `fx_jpy`: **0 of 32** positions — and structurally cannot, since a 09:00 broker entry with a 12 h
  ceiling closes at 21:00 the same broker day (0 rollovers on 292 of 292 sample days). That rests on
  the export column being broker-server-local, which is **measured**: the FX week opens Monday 00:00
  (56 of 60 symbol-weeks) and closes Friday 23:45 (60 of 60). Under a UTC reading the ceiling would
  land at 00:00 broker in summer, exactly the rollover — so the premise is load-bearing.
- `fx_jpy_ny`: **0 of 9** — but **no structural backstop.** It shares the 48-bar ceiling and enters at
  16:00, so its ceiling is 04:00 the *next* broker day; a Friday entry spans the weekend. Nine
  observations, not a bound.
- `idxrev`: 39 of 59 (66 %) — which does not change its verdict (it is negative before cost) but does
  **validate the carry model**, whose modelled mean for that sleeve is 0.92 nights

### What it did not settle, and why no analogy reaches it

The eight sleeves that never fired live keep the modelled upper bound. Two further limits, both found
by attacking this result rather than defending it: **the live sample never reached any ceiling** (max
hold 7.36 h against 12 h), so it cannot testify about carry at the horizon; and the two sources agree
on *sleeve identity* only because both read the same MT5 order comment — independent on timing and
money, one witness counted twice on attribution.

I also tried to close the three carry-conditional sleeves by analogy — the live sleeves used only
4–9 % of their horizons — and **the attempt refuted itself**: across all twelve live sleeves that
fraction runs **0.4 % to 105 %**, three exceed their nominal horizon (`ny_crypto_momentum` p90 =
271 %), and the only long-horizon sleeve with live evidence is `idxrev` — one sleeve. **The generator
re-run is still the thing that would close them**, and it is a data fetch, not a sealed window.

---

## 2. Per-sleeve

`×mult` is broker truth ÷ what the validation charged. Below 1.00 means the validation **over**-charged.
`metals_core` and `energy_agri` were charged a **per-trade** cost by their generators
(`class_cost × (0.5 × ATR14(H4) / sd_h4)`, `INTEG_portfolio_build_w3.py:89`,
`EXEC_exit_variants.py:45`), so their `charged` column is a measured per-row mean, not a class constant.

### FTMO

| sleeve | conf | n | gross R | charged | broker truth | ×mult | swap/night | net @0 | break-even hold | max hold | carry basis | tier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `sub_xvol_pullback` | 0.45 | 90 | 1.3070 | 0.0692 | 0.0317 | 0.46 | 0.0099 | 1.2752 | *never reached* | 320 h | horizon (modelled) | **UNCOND** |
| `crypto` | 0.85 | 104 | 1.2121 | 0.0953 | 0.0367 | 0.39 | 0.0289 | 1.1753 | *never reached* (975 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `metals_core` | 1.0 | 131 | 0.9103 | 0.0232 | 0.0329 | 1.42 | 0.0431 | 0.8774 | *never reached* (489 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `energy_agri` | 0.8 | 162 | 0.5386 | 0.0580 | 0.0712 | 1.23 | 0.0081 | 0.4675 | *never reached* (1383 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `fx_jpy` | 0.15 | 530 | 0.2823 | 0.1148 | 0.2411 | 2.1 | 0.1301 | 0.0412 | *never reached* | 12 h | live 0 · structural | **MEASURED** |
| `fx_jpy_ny` | 0.15 | 197 | 0.2690 | 0.1148 | 0.2227 | 1.94 | 0.1304 | 0.0462 | **9 h** (75 % of max) | 12 h | live 0 · zero swap | cond. *(9 live obs)* |
| `metals_softband` | 0.5 | 70 | 0.3780 | 0.0459 | 0.0441 | 0.96 | 0.0405 | 0.3339 | **198 h** (62 % of max) | 320 h | horizon (modelled) | **cond.** |
| `vp_euidx_pocgrav` | 0.3 | 341 | 0.2982 | 0.0638 | 0.0265 | 0.41 | 0.0260 | 0.2717 | **251 h** (78 % of max) | 320 h | horizon (modelled) | **cond.** |
| `sub_mid_dn_revert` | 0.2 | 398 | 0.3166 | 0.0969 | 0.0456 | 0.47 | 0.0242 | 0.2710 | **269 h** (84 % of max) | 320 h | horizon (modelled) | **cond.** |
| `idxrev` | 0.15 | 6473 | 0.0059 | 0.0425 | 0.0221 | 0.52 | 0.0137 | -0.0162 | — | 240 h | live mean hold | dead before cost |
| `metals_ob_micro` | 0.3 | 7 | -0.5000 | 0.0459 | 0.0349 | 0.76 | 0.0200 | -0.5349 | — | 320 h | horizon (modelled) | dead before cost |

#### live carry evidence
| sleeve | live positions | paid swap | median hold | max hold | horizon | % of horizon used | nights charged |
|---|---:|---:|---:|---:|---:|---:|---:|
| `fx_jpy` | 32 | **0** (0.0 %) | 0.51 h | 7.36 h | 12 h | 4.2 % | **0.0** |
| `fx_jpy_ny` | 9 | **0** (0.0 %) | 0.71 h | 1.26 h | 12 h | 5.9 % | **0.0** |
| `idxrev` | 59 | **39** (66.1 %) | 15.02 h | 89.99 h | 240 h | 6.3 % | **0.923** |

### redacted_account

| sleeve | conf | n | gross R | charged | broker truth | ×mult | swap/night | net @0 | break-even hold | max hold | carry basis | tier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `sub_xvol_pullback` | 0.45 | 90 | 1.3070 | 0.0692 | 0.0367 | 0.53 | 0.0179 | 1.2703 | *never reached* | 320 h | horizon (modelled) | **UNCOND** |
| `crypto` | 0.85 | 104 | 1.2121 | 0.0953 | 0.0394 | 0.41 | 0.0181 | 1.1727 | *never reached* | 320 h | horizon (modelled) | **UNCOND** |
| `energy_agri` | 0.8 | 162 | 0.5386 | 0.0580 | 0.1147 | 1.98 | 0.0059 | 0.4239 | *never reached* | 320 h | horizon (modelled) | **UNCOND** |
| `vp_euidx_pocgrav` | 0.3 | 341 | 0.2982 | 0.0638 | 0.0393 | 0.62 | 0.0175 | 0.2589 | *never reached* (355 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `fx_jpy` | 0.15 | 530 | 0.2823 | 0.1148 | 0.2627 | 2.29 | 0.3855 | 0.0196 | *never reached* | 12 h | live 0 · structural | **MEASURED** |
| `fx_jpy_ny` | 0.15 | 197 | 0.2690 | 0.1148 | 0.2467 | 2.15 | 0.3735 | 0.0222 | **2 h** (17 % of max) | 12 h | live 0 · zero swap | cond. *(9 live obs)* |
| `metals_core` | 1.0 | 131 | 0.9103 | 0.0232 | 0.0350 | 1.51 | 0.0638 | 0.8752 | *never reached* (329 h > 320 h max) | 320 h | horizon (modelled) | **cond.** |
| `metals_softband` | 0.5 | 70 | 0.3780 | 0.0459 | 0.0470 | 1.02 | 0.0596 | 0.3310 | **133 h** (42 % of max) | 320 h | horizon (modelled) | **cond.** |
| `sub_mid_dn_revert` | 0.2 | 398 | 0.3166 | 0.0969 | 0.0488 | 0.5 | 0.0320 | 0.2678 | **201 h** (63 % of max) | 320 h | horizon (modelled) | **cond.** |
| `idxrev` | 0.15 | 6473 | 0.0059 | 0.0425 | 0.0257 | 0.6 | 0.0212 | -0.0199 | — | 240 h | live mean hold | dead before cost |
| `metals_ob_micro` | 0.3 | 7 | -0.5000 | 0.0459 | 0.0378 | 0.82 | 0.0363 | -0.5378 | — | 320 h | horizon (modelled) | dead before cost |

On redacted_account `metals_core` drops out of the unconditional tier (break-even 329 h against a 320 h
ceiling — right on the boundary) and `vp_euidx_pocgrav` enters it. The cause is swap on JPY and metals,
not commission: commission is identical ($5.00/lot) on both brokers.

---

## 3. Economics at the 2.00 % live dial

Dial from `config/agent_config.yaml:1246-1394`, profile `clean3_w7_ceiling_nom2p00`.

`mo% ×21` is the basis `INTEG_W7_FINAL_RESULT.json` uses (per book-day × 21). `mo% cal` uses each
variant's **own measured** book-days per calendar month. The survivor subset looks far better per
book-day and far worse per calendar month, because what it drops is most of the book's frequency.

### FTMO

| book | window | carry | book-days | b/month | P(pass) | P(maxDD) | med cal days | **mo% ×21** | **mo% cal** |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| all 11 | full | 1 night | 1679 | 12.26 | 0.950 | 0.050 | 88 | 3.381 | **1.973** |
| all 11 | full | **held to horizon** | 1679 | 12.26 | 0.450 | 0.511 | 74 | 0.23 | **0.134** |
| all 11 | fwd 2025+ | 1 night | 382 | 21.22 | 0.995 | 0.005 | 27 | 5.893 | **5.955** |
| all 11 | fwd 2025+ | **held to horizon** | 382 | 21.22 | 0.774 | 0.226 | 38 | 2.237 | **2.261** |
| unconditional 4 | full | 1 night | 246 | 1.81 | 1.000 | 0.000 | 202 | 9.769 | **0.841** |
| unconditional 4 | full | **held to horizon** | 246 | 1.81 | 0.961 | 0.039 | 297 | 5.374 | **0.463** |
| unconditional 4 | fwd 2025+ | 1 night | 128 | 7.11 | 1.000 | 0.000 | 41 | 10.977 | **3.717** |
| unconditional 4 | fwd 2025+ | **held to horizon** | 128 | 7.11 | 0.997 | 0.003 | 52 | 7.728 | **2.617** |

### redacted_account

| book | window | carry | book-days | b/month | P(pass) | P(maxDD) | med cal days | **mo% ×21** | **mo% cal** |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| all 11 | full | 1 night | 1679 | 12.26 | 0.873 | 0.084 | 91 | 2.848 | **1.662** |
| all 11 | full | **held to horizon** | 1679 | 12.26 | 0.230 | 0.682 | 51 | -1.753 | **-1.023** |
| all 11 | fwd 2025+ | 1 night | 382 | 21.22 | 0.972 | 0.028 | 32 | 4.717 | **4.767** |
| all 11 | fwd 2025+ | **held to horizon** | 382 | 21.22 | 0.318 | 0.682 | 30 | -1.171 | **-1.183** |
| unconditional 4 | full | 1 night | 272 | 2.25 | 0.999 | 0.001 | 202 | 7.692 | **0.823** |
| unconditional 4 | full | **held to horizon** | 272 | 2.25 | 0.983 | 0.017 | 260 | 5.451 | **0.583** |
| unconditional 4 | fwd 2025+ | 1 night | 164 | 9.11 | 1.000 | 0.000 | 46 | 8.21 | **3.562** |
| unconditional 4 | fwd 2025+ | **held to horizon** | 164 | 9.11 | 0.989 | 0.011 | 57 | 5.879 | **2.551** |

**The band is the finding.** At one night of average carry the book of record makes ~2 %/month
calendar-corrected on FTMO and passes 95 % of the time. If every trade instead ran to its structural
horizon it makes 0.13 %/month and fails more often than it passes; on redacted_account that endpoint is
**negative**. The distance between those two worlds is holding time — now measured for three sleeves
(§1) and still an upper bound for the other eight.

The unconditional sleeves are safe at any hold — but they fire on **246 book-days in eleven years
(1.8 a month)**, so they buy certainty at the cost of almost all the frequency.

---

## 4. The three things that decide this, ranked

**1. Holding time — measured for three sleeves, an upper bound for the other eight.** No exit index
survives in any cache; the three that fired live were measured from the broker's own realized `swap`
field (§1). Closing the remaining eight needs a generator re-run against
`data/mt5_research_exports/bridge_ftmo_deep_h4_*`, **absent from this machine** — but that is a data
fetch, not a sealed window. **It is the cheapest thing that would sharpen OD-3**, and it would decide
`metals_softband`, `vp_euidx_pocgrav` and `sub_mid_dn_revert`, which between them carry conf 1.00.

**2. Concentration — 46.9 % of the surviving edge sits on 194 trades.** `crypto` (104 trades, mean
gross **1.212 R/trade**, no history before 2024-09) and `sub_xvol_pullback` (90 trades, mean gross
**1.307 R/trade**, a cell selected from a substrate scan). Neither has an out-of-sample window, and
both are in the **unconditional** tier — so the tier that looks safest against costs is the one most
exposed to selection. **Re-costing cannot detect overfitting, only mispricing.**

**3. Direction is unknown on four sleeves, and swap is charged on the adverse leg.**
`fx_jpy_ny`, `sub_xvol_pullback`, `vp_euidx_pocgrav` and `sub_mid_dn_revert` are **100 %
direction-less** in the ledger (1,026 rows); both legs are priced and the mean charged. The legs can
differ by a lot — `fx_jpy_ny` on FTMO is **0.000 all-long vs 0.261 all-short per night**, because FTMO
pays the long leg of USDJPY. The only direction evidence available is `fx_jpy`'s own D4 record,
**277 long / 253 short (52.3 % long)** on the same two symbols, which is what makes the both-legs mean
defensible rather than arbitrary. Per-sleeve spreads are published in
`W7_RECOST_V1.json:accounts.*.sleeves.*.direction`.

---

## 5. Coverage — derived by set-difference, not accumulated

Of **8,503** book rows, per account: **6,398 priced** by `cost_r` from measured broker truth ·
**1,956 class-transferred** (median priced ex-swap **and** swap-per-night of the same class within the
same sleeve, labelled `TRANSFERRED` with the pool named) · **149 unpriced and never charged zero** —
agri and FTMO's two `energy`-class symbols whose commission is genuinely `unknown`.

Stop distance: **7,441 rows (87.5 %)** carry an exact ledger stop; 729 use the symbol's own measured
ATR; 333 fall to the transfer.

Dropping every unpriced row instead of transferring it moves the FTMO book mean 0.10982 → 0.09090 and
**changes no sleeve's tier**.

**Known gap in the layer, filed not absorbed:** FTMO's `USOIL.cash`/`UKOIL.cash` are classified
`index` — inheriting zero commission — because they sit under a `Cash II CFD\` path head
(`scripts/build_broker_true_costs.py:106`). Their redacted_account twins are `energy` at a MEASURED
$5.00/lot. Charging FTMO the redacted_account rate costs `energy_agri` **+0.0144 R/trade** and moves the
book mean 0.10982 → 0.10883. It changes no tier.

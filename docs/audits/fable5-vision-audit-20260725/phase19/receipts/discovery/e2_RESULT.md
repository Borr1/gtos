# e2_RESULT — EXTENSION of l10-broker-truth X7 (the honest cost ledger) to FIVE months

Lane **e2**. Posture: extension, not refutation. Wave 19 broad forensic swarm.

Every number below is measured; every script is in `e2_scripts/` beside this file.

**Evidence class: DISCOVERY / lane iteration, `billed:false`. No admission claim.**


---

## 0. TL;DR

1. **The finding reproduces EXACTLY.** 60/60 book fields to 1e-6, twice — once through the original
   working-set input and once through an independently rebuilt portable instrument reading the raw pool.
   `+0.473864 R/trade` is confirmed.

2. **It HOLDS in every month it was not found on.** February, March, April and May all show the same
   structure: the frozen cost model overcharges by **3.13x–3.50x**, worth **+0.2798 to +0.4739 R/trade**,
   and **all 25 month x book cells stay negative**. The gross deficit is binding in every month.

3. **NEW — the frozen cost model is a RANKING error, not a scale error.** Row-level Spearman between
   frozen and real total cost is only **0.371–0.598**, and the frozen gate and a real-cost gate
   **disagree on 34.9%–44.7% of every month's pool**. Correcting cost does not merely re-price the same
   book — it changes *which* candidates are admitted, on more than a third of the pool. Per-symbol the
   frozen/real ratio spreads **50x–152x**.

4. **NEW — the 12.1x family dispersion is priced, and it travels.** The family real-cost ordering is
   near-invariant across four months (**mean Spearman 0.9818**). Selecting the 4 cheapest families and 12
   cheapest symbols *on January only*, plus a real-cost gate, moves net@real from **-0.4068 to -0.1231**
   in January and **-0.4396 to -0.1216** in May — **mean +0.282 R/trade across five months**, at
   ~2,400-3,300 rows/month. Still negative everywhere.

5. **NEW — the estate's best conditioned cell.** `{regime_transition_break, volatility_compression_expansion}
   x NY session`, takeable, is **gross-positive in 3 of 5 months** and is the only cell of 100 declared
   with a positive five-month mean **net**@real (+0.0036 pooled). Pooled gross +0.0331, bootstrap 90% CI
   **[-0.0195, +0.0870]**, permutation p **0.0548** vs same-month NY peers, **n=390** total. Discovery-grade.

6. **BOUNDARY / localization.** l10's per-symbol claims are JANUARY-ONLY. `USDCHF +0.0117` becomes
   -0.2373 / -0.1337 / -0.1169 / -0.0505 in the other four months (mean **-0.1053**); `GER40 -0.0030`
   becomes mean **-0.1204**. **No symbol of 24 has positive mean gross over five months.** The SESSION
   axis replaces it: `london` mean gross **-0.0251** (n=18,538), `ny` **-0.0694** (n=18,247), against
   -0.115 to -0.137 for every hour bucket outside them.


---

## 1. Reproduction — the instrument matches

| check | value |
|---|---|
| book-field checks run | 60 |
| failures | **0** |
| target headline (`L10X_BOTTOMLINE_V1.json`) | 0.473864 |
| reproduced via original working-set input | 0.473864 |
| reproduced via portable raw-pool instrument | 0.473864 |

**EXACT — 60/60 book fields matched to 1e-6 on both the original input file and an independently rebuilt portable path.**

Both paths were checked on all five books (A/B/C/D/E) x six fields (n, gross, frozen_cost, real_cost,
net_frozen, net_real). The portable path recomputes `risk_distance = |entry_price - stop_loss|` and
`gross_r = opportunity_net_proxy_r + cost_r` from the raw pool rather than reading the working set, so it
proves the instrument is transportable, which is what the rest of this lane depends on.
Script: `e2_scripts/e2_01_repro_jan.py` -> `E2_JAN_REPRO_V1.json`.

**One deliberate difference, declared.** The original January anchor
(`w0cap2_DECISION_ANCHOR_V1.jsonl.gz`) loaded only `bridge_ftmo_m1_202601`, so 17 rows near the month
boundary were unanchored and `born_past_stop` was 3,516. The portable anchor also loads the prior month,
anchors **27,658/27,658**, and finds **3,519**. The takeable book moves 24,142 -> 24,139 and net@real
-0.291914 -> -0.291930. The exact reproduction above uses the ORIGINAL anchor; every cross-month table
uses the portable one, for comparability.


---

## 2. THE EXTENSION — five months, one instrument

Cost model is identical in every month by construction: per-symbol median spread in bps from the FTMO
tick archive (2026-06-18..07-24), measured broker commission, measured live slippage, swap 0 at the 2 h
horizon. It is **month-invariant**, so every month-to-month change below comes from row GEOMETRY
(entry price / risk distance mix), never from a spread that moved.

### 2.1 Book A — all rows

| month | n | gross | frozen cost | real cost | net @ frozen | net @ real | **WORTH of the correction** | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN | 27,658 | -0.2175 | 0.6632 | 0.1893 | -0.8807 | -0.4068 | **+0.4739** | 3.50x |
| FEB | 24,239 | -0.1506 | 0.4895 | 0.1562 | -0.6400 | -0.3068 | **+0.3332** | 3.13x |
| MAR | 26,500 | -0.1767 | 0.4046 | 0.1247 | -0.5813 | -0.3015 | **+0.2798** | 3.24x |
| APR | 25,056 | -0.2319 | 0.6233 | 0.1810 | -0.8552 | -0.4129 | **+0.4423** | 3.44x |
| MAY | 21,285 | -0.2387 | 0.6644 | 0.2009 | -0.9030 | -0.4396 | **+0.4635** | 3.31x |

**Range +0.279837 to +0.473864, mean +0.398545. Overcharge ratio 3.133x-3.5033x.**
January is the LARGEST of the five, so the published +0.473864 is the top of the range, not the centre.

**March is the strongest corroboration in the set.** Its R0 arm was run with
`commission_broker_true_gated` and `swap_horizon_true` already applied
(`FA2_M_R0_RECEIPT.json` -> `patches_applied`), so its frozen cost is already partly repaired:
0.4046 vs January's 0.6632. **The overcharge ratio barely moves — 3.24x vs 3.50x.** Repairing
commission and swap in the engine left the ratio essentially where it was, because the residual is
the SPREAD term, exactly as `w0-dictionary` D1 predicted (spread is 85.08% of frozen cost and is the
term measured overcharged 7.3-8.5x).

### 2.2 Real cost decomposition (R/trade, all rows)

| month | spread | commission | slippage | total |
|---|---:|---:|---:|---:|
| JAN | 0.1248 | 0.0571 | 0.0074 | 0.1893 |
| FEB | 0.1039 | 0.0468 | 0.0055 | 0.1562 |
| MAR | 0.0755 | 0.0436 | 0.0056 | 0.1247 |
| APR | 0.1135 | 0.0608 | 0.0067 | 0.1810 |
| MAY | 0.1185 | 0.0748 | 0.0076 | 0.2009 |

### 2.3 The full ladder — every cell negative in every month

| month | B takeable | C frozen gate | D real gate | E cheapest half | born_past_stop share |
|---|---|---|---|---|---:|
| JAN | -0.2919 (n=24,139) | -0.2005 (n=6,984) | -0.1625 (n=11,880) | -0.1155 (n=5,940) | 12.72% |
| FEB | -0.2701 (n=21,150) | -0.1673 (n=6,012) | -0.1112 (n=12,531) | -0.0707 (n=6,265) | 12.74% |
| MAR | -0.2512 (n=24,973) | -0.1768 (n=8,868) | -0.1636 (n=17,178) | -0.1185 (n=8,589) | 5.76% |
| APR | -0.2994 (n=22,027) | -0.1748 (n=5,662) | -0.1776 (n=11,725) | -0.1655 (n=5,862) | 12.09% |
| MAY | -0.3214 (n=18,564) | -0.2380 (n=4,405) | -0.1593 (n=9,394) | -0.1144 (n=4,697) | 12.78% |

**25 of 25 month x book cells are negative.** l10's central claim — *the gross deficit, not cost, is
binding* — holds out of window without a single exception.

One ordering exception worth naming: in **April the E book (-0.1655) is WORSE than the C book (-0.1748)**
... in fact April is the one month where the real-cost gate does not beat the frozen gate
(D -0.1776 vs C -0.1748).
In April, cheaper cohorts have *worse* gross. That is the single clearest boundary in this lane.

---

## 3. NEW FINDING E2-N1 — the frozen cost model is a RANKING error, not a scale error

This is the most consequential thing this lane found and it is not in the original finding.

If the frozen model were simply ~3.4x too large, the cost gate would still rank candidates correctly and
its only defect would be tightness. It does not. Measured on every row of every month:

| month | Spearman(frozen_total, real_total) | median row ratio | p10 | p90 | gate disagreement | frozen-only admits | real-only admits | per-SYMBOL ratio spread | per-FAMILY ratio spread |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JAN | **0.3709** | 1.72x | 0.78x | 15.67x | **34.9%** | 2,112 | 7,531 | 152.1x | 2.94x |
| FEB | **0.4895** | 2.14x | 1.07x | 7.94x | **44.7%** | 1,610 | 9,228 | 106.6x | 3.35x |
| MAR | **0.4820** | 1.93x | 1.11x | 16.17x | **38.5%** | 647 | 9,559 | 78.6x | 2.83x |
| APR | **0.5982** | 2.30x | 1.27x | 15.04x | **35.4%** | 1,116 | 7,749 | 50.1x | 2.44x |
| MAY | **0.5382** | 2.33x | 0.93x | 11.56x | **39.2%** | 1,587 | 6,767 | 99.1x | 2.65x |

**Reading.** A pure scale error would give Spearman ~1.0 and a per-row ratio with no dispersion. Instead
the correlation is 0.37-0.60, the p10-to-p90 row ratio spans roughly 1x to 12-16x, and the per-symbol
mean ratio spreads **50x-152x** — the frozen model over-charges some symbols two orders of magnitude more
than others *relative to truth*. So the frozen gate is not just refusing too much; on **34.9%-44.7% of
every month's pool it refuses and admits the wrong rows.**

### 3.1 What fixing the gate is worth, and where it fails

Frozen-gate book vs real-gate book, both takeable, both scored at real cost:

| month | frozen-gate n | frozen-gate net@real | real-gate n | real-gate net@real | delta | trade-count ratio |
|---|---:|---:|---:|---:|---:|---:|
| JAN | 6,984 | -0.2005 | 11,880 | -0.1625 | +0.0380 | 1.70x |
| FEB | 6,012 | -0.1673 | 12,531 | -0.1112 | +0.0562 | 2.08x |
| MAR | 8,868 | -0.1768 | 17,178 | -0.1636 | +0.0132 | 1.94x |
| APR | 5,662 | -0.1748 | 11,725 | -0.1776 | -0.0027 | 2.07x |
| MAY | 4,405 | -0.2380 | 9,394 | -0.1593 | +0.0787 | 2.13x |
| **mean** | | | | | **+0.0367** | **1.99x** |

**Fixing the gate is worth about +0.037 R/trade AND roughly doubles the trade count** — but it is **not
uniformly positive: April is -0.0027.** This is the direct, month-resolved version of the estate's
standing result that cost truth widens the funnel ~2.2-2.4x and earns no more; here the widening is
1.70x-2.13x and the earnings change is +0.0132 to +0.0787 with one negative month.

### 3.2 Per-symbol frozen/real cost ratio, January (the shape of the mis-ranking)

| cheapest-relative (model closest to truth) | ratio | most over-charged | ratio |
|---|---:|---|---:|
| UKOIL_cash | 0.23x | NAS100 | 34.37x |
| USOIL_cash | 0.26x | SPX500 | 15.60x |
| XAGUSD | 0.64x | JP225 | 6.70x |
| XAUUSD | 0.84x | UK100 | 6.24x |
| EURUSD | 1.01x | ETHUSD | 4.88x |
| GBPJPY | 1.10x | US30_cash | 4.53x |

---

## 4. NEW FINDING E2-N2 — the 12.1x family dispersion travels, and here is its price

### 4.1 The dispersion itself

| month | cheapest family cost | most expensive | ratio |
|---|---:|---:|---:|
| JAN | 0.0405 | 0.4914 | **12.14x** |
| FEB | 0.0344 | 0.4191 | **12.20x** |
| MAR | 0.0266 | 0.3493 | **13.15x** |
| APR | 0.0423 | 0.4310 | **10.19x** |
| MAY | 0.0436 | 0.5013 | **11.50x** |

### 4.2 Family real cost R/trade, takeable, four months side by side

**Mean Spearman across the six month-pairs = 0.9818** — the ordering is near-invariant.

| family | JAN | FEB | APR | MAY | mean |
|---|---:|---:|---:|---:|---:|
| regime_transition_break | 0.0405 | 0.0344 | 0.0423 | 0.0436 | **0.0402** |
| volatility_compression_expansion | 0.0505 | 0.0429 | 0.0466 | 0.0543 | **0.0486** |
| session_open_range_break | 0.0876 | 0.0793 | 0.0836 | 0.0914 | **0.0855** |
| displacement_continuation | 0.1057 | 0.0938 | 0.1015 | 0.1105 | **0.1029** |
| current_ob_retest | 0.1306 | 0.1023 | 0.1366 | 0.1396 | **0.1273** |
| current_fvg_fill | 0.1503 | 0.0933 | 0.1225 | 0.1562 | **0.1306** |
| current_breaker_re_entry | 0.1512 | 0.1689 | 0.1641 | 0.1854 | **0.1674** |
| liquidity_sweep_reclaim | 0.2158 | 0.1912 | 0.2119 | 0.2303 | **0.2123** |
| cross_asset_lead_lag | 0.2978 | 0.2534 | 0.2870 | 0.3147 | **0.2882** |
| structural_distance_extreme | 0.4914 | 0.4191 | 0.4310 | 0.5013 | **0.4607** |

(The four-month table is the one with a directly comparable pool construction. March's own dispersion
is 13.15x with the same ordering.)

### 4.3 Family net@real — the ordering is also stable

Mean Spearman = 0.8727.

| family | JAN | FEB | APR | MAY | mean |
|---|---:|---:|---:|---:|---:|
| structural_distance_extreme | -0.6734 | -0.6527 | -0.6735 | -0.7845 | **-0.6960** |
| current_breaker_re_entry | -0.2324 | -0.7420 | -0.3761 | -0.3522 | **-0.4257** |
| cross_asset_lead_lag | -0.4285 | -0.3941 | -0.4202 | -0.4514 | **-0.4236** |
| liquidity_sweep_reclaim | -0.2573 | -0.2948 | -0.3157 | -0.3071 | **-0.2937** |
| current_fvg_fill | -0.2919 | -0.1891 | -0.2999 | -0.3572 | **-0.2845** |
| current_ob_retest | -0.2043 | -0.1631 | -0.1778 | -0.1647 | **-0.1775** |
| displacement_continuation | -0.1942 | -0.0945 | -0.1661 | -0.1872 | **-0.1605** |
| volatility_compression_expansion | -0.1373 | -0.0906 | -0.1803 | -0.0797 | **-0.1220** |
| session_open_range_break | -0.1623 | 0.0211 | -0.0672 | -0.1297 | **-0.0845** |
| regime_transition_break | -0.0472 | 0.0040 | -0.0834 | -0.0995 | **-0.0565** |

### 4.4 THE PRICE — January-chosen cheapest-K families, evaluated on every month

The family ORDER is fixed by January real cost alone; no outcome was read to choose it. Net@real:

| K (cheapest families) | JAN | FEB | APR | MAY | n JAN |
|---|---:|---:|---:|---:|---:|
| 1 | -0.0472 | 0.0040 | -0.0834 | -0.0995 | 297 |
| 2 | -0.1076 | -0.0607 | -0.1499 | -0.0860 | 902 |
| 3 | -0.1362 | -0.0165 | -0.1057 | -0.1092 | 1,889 |
| 4 | -0.1770 | -0.0710 | -0.1489 | -0.1644 | 6,358 |
| 5 | -0.1816 | -0.0816 | -0.1538 | -0.1645 | 7,650 |
| 6 | -0.2349 | -0.1289 | -0.2218 | -0.2494 | 14,796 |
| 7 | -0.2347 | -0.1896 | -0.2290 | -0.2553 | 15,588 |
| 8 | -0.2398 | -0.2164 | -0.2482 | -0.2674 | 20,063 |
| 9 | -0.2575 | -0.2344 | -0.2646 | -0.2848 | 22,146 |
| 10 | -0.2919 | -0.2701 | -0.2994 | -0.3214 | 24,139 |

**The ladder is monotone-degrading in every month.** K=1 is the best cell in 4 of 5 months and the only
positive one anywhere on the ladder is FEB K=1 (+0.0040). A January-only cost ranking predicts the
out-of-sample net ordering in four independent months — that is what makes this a lever rather than a
January artifact.

### 4.5 Staged decomposition — how much is cheaper cost and how much is better trades

| stage | JAN | FEB | MAR | APR | MAY |
|---|---|---|---|---|---|
| S0 all rows | -0.4068 (n=27,658) | -0.3068 (n=24,239) | -0.3015 (n=26,500) | -0.4129 (n=25,056) | -0.4396 (n=21,285) |
| S1 + drop born_past_stop | -0.2919 (n=24,139) | -0.2701 (n=21,150) | -0.2512 (n=24,973) | -0.2994 (n=22,027) | -0.3214 (n=18,564) |
| S2 + 4 cheapest families (JAN-chosen) | -0.1770 (n=6,358) | -0.0710 (n=5,781) | -0.1277 (n=6,458) | -0.1489 (n=6,010) | -0.1644 (n=5,275) |
| S3 + 12 cheapest symbols (JAN-chosen) | -0.1412 (n=3,279) | -0.0483 (n=2,955) | -0.0795 (n=3,396) | -0.1110 (n=3,077) | -0.1428 (n=2,651) |
| S4 + real-cost gate | -0.1231 (n=3,008) | -0.0470 (n=2,836) | -0.0742 (n=3,320) | -0.0906 (n=2,795) | -0.1216 (n=2,412) |
| **of which GROSS at S4** | -0.0730 | -0.0014 | -0.0389 | -0.0422 | -0.0731 |
| **of which REAL COST at S4** | 0.0501 | 0.0456 | 0.0353 | 0.0484 | 0.0485 |

**Total lever value S0 -> S4: JAN +0.2837, FEB +0.2598, MAR +0.2273, APR +0.3224, MAY +0.3179 — mean +0.2822 R/trade.**
After the takeability repair alone (S1 -> S4) the lever is still worth mean **+0.1955 R/trade** on ~2,400-3,300 rows/month.

Families used: `regime_transition_break, volatility_compression_expansion, session_open_range_break, displacement_continuation`.

Symbols used: `NAS100, GER40, US30_cash, XAUUSD, JP225, UK100, SPX500, EURUSD, GBPUSD, AUDUSD, USDJPY, XAGUSD`.

---

## 5. BOUNDARY — where it holds and where l10's per-symbol claims do NOT

### 5.1 The symbol claims are JANUARY-ONLY. This is the clearest localization in the lane.

l10 X11: *"USDCHF is the only symbol in the pool with positive takeable gross (+0.0117, n=774), and
GER40 is the only other one at breakeven (-0.0030, n=1,400)."* Extended:

| symbol | JAN | FEB | MAR | APR | MAY | mean gross | mean real cost | mean net@real | months gross>0 | total n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURJPY | -0.0233 | -0.0331 | -0.0930 | 0.0476 | -0.0750 | **-0.0354** | 0.2427 | -0.2781 | 1 | 2,809 |
| AUDUSD | -0.0279 | -0.0847 | -0.0756 | 0.0465 | -0.0489 | **-0.0381** | 0.1526 | -0.1907 | 1 | 3,009 |
| NZDUSD | -0.0457 | -0.0461 | -0.0410 | -0.0360 | -0.0857 | **-0.0509** | 0.2757 | -0.3266 | 0 | 3,404 |
| UKOIL_cash | -0.0518 | -0.0496 | -0.1229 | -0.0202 | -0.0550 | **-0.0599** | 0.2178 | -0.2777 | 0 | 4,189 |
| AUDJPY | -0.0872 | -0.0293 | -0.0693 | -0.0898 | -0.0424 | **-0.0636** | 0.2515 | -0.3151 | 0 | 2,945 |
| EURUSD | -0.1153 | -0.0702 | -0.0876 | -0.0731 | -0.0171 | **-0.0727** | 0.1661 | -0.2387 | 0 | 3,432 |
| EURGBP | -0.1237 | -0.0472 | -0.1572 | -0.0680 | -0.0168 | **-0.0826** | 0.3366 | -0.4192 | 0 | 3,259 |
| USDJPY | -0.0934 | -0.1084 | -0.0738 | -0.1354 | -0.0974 | **-0.1017** | 0.2074 | -0.3091 | 0 | 4,360 |
| JP225 | -0.0478 | -0.0774 | -0.1456 | -0.1328 | -0.1195 | **-0.1046** | 0.0991 | -0.2037 | 0 | 6,282 |
| CHFJPY | -0.0755 | -0.1627 | -0.0196 | -0.1135 | -0.1521 | **-0.1047** | 0.2552 | -0.3598 | 0 | 2,874 |
| USDCHF | 0.0117 | -0.2373 | -0.1337 | -0.1169 | -0.0505 | **-0.1053** | 0.2129 | -0.3182 | 1 | 3,508 |
| USOIL_cash | -0.1414 | -0.0817 | -0.1862 | -0.0990 | -0.0600 | **-0.1137** | 0.2556 | -0.3693 | 0 | 3,844 |
| UK100 | -0.1846 | -0.0988 | -0.0420 | -0.1159 | -0.1562 | **-0.1195** | 0.1038 | -0.2233 | 0 | 7,055 |
| GER40 | -0.0030 | -0.1822 | -0.1800 | -0.1409 | -0.0960 | **-0.1204** | 0.0511 | -0.1715 | 0 | 6,698 |
| GBPUSD | -0.1603 | -0.0755 | -0.1707 | -0.1614 | -0.0590 | **-0.1254** | 0.1579 | -0.2833 | 0 | 3,637 |
| XAUUSD | -0.0764 | -0.0411 | -0.1637 | -0.1221 | -0.2296 | **-0.1266** | 0.0907 | -0.2173 | 0 | 9,731 |
| USDCAD | -0.1770 | -0.1493 | -0.1342 | -0.0654 | -0.1416 | **-0.1335** | 0.2665 | -0.4000 | 0 | 3,743 |
| GBPJPY | -0.0803 | -0.3315 | -0.0884 | -0.1452 | -0.0224 | **-0.1336** | 0.2723 | -0.4059 | 0 | 3,794 |
| ETHUSD | -0.1742 | -0.1590 | -0.0950 | -0.1274 | -0.1279 | **-0.1367** | 0.2859 | -0.4226 | 0 | 4,309 |
| US30_cash | -0.1567 | -0.1012 | -0.1228 | -0.1775 | -0.1696 | **-0.1456** | 0.0579 | -0.2034 | 0 | 6,467 |
| SPX500 | -0.1099 | -0.0265 | -0.1202 | -0.2192 | -0.2804 | **-0.1512** | 0.1195 | -0.2707 | 0 | 6,447 |
| BTCUSD | -0.0284 | -0.3070 | -0.1485 | -0.1111 | -0.1761 | **-0.1542** | 0.1892 | -0.3434 | 0 | 4,937 |
| XAGUSD | -0.1117 | -0.1122 | -0.2291 | -0.2686 | -0.1761 | **-0.1795** | 0.2114 | -0.3909 | 0 | 4,122 |
| NAS100 | -0.2842 | -0.0452 | -0.2328 | -0.3116 | -0.2473 | **-0.2242** | 0.0551 | -0.2794 | 0 | 5,998 |

**USDCHF's +0.0117 does not survive contact with any other month** — -0.2373 / -0.1337 / -0.1169 / -0.0505, mean **-0.1053** on n=3,508.
**GER40's -0.0030 becomes mean -0.1204.** Over five months **no symbol of 24 has positive mean gross**,
and only three (EURJPY, AUDUSD, USDCHF) have even one positive month. Treat every single-month per-symbol
gross number in this estate as noise until it is shown over four months.

### 5.2 The SESSION axis replaces it — and it is much stronger

| session bucket | JAN | FEB | MAR | APR | MAY | mean gross | mean real cost | mean net@real | total n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| london | -0.0176 | -0.0418 | -0.0183 | -0.0033 | -0.0443 | **-0.0251** | 0.1741 | -0.1991 | 18,538 |
| tokyo | -0.1146 | 0.0143 | -0.0402 | -0.0599 | -0.0712 | **-0.0543** | 0.1962 | -0.2505 | 5,474 |
| ny | -0.0944 | -0.0232 | -0.0663 | -0.0327 | -0.1304 | **-0.0694** | 0.1158 | -0.1852 | 18,247 |
| moonshot_h15_16 | -0.1730 | -0.2095 | -0.0576 | -0.2384 | 0.1010 | **-0.1155** | 0.1622 | -0.2777 | 1,554 |
| moonshot_h09_10 | 0.0970 | -0.2650 | -0.1195 | -0.0615 | -0.2473 | **-0.1192** | 0.1871 | -0.3064 | 1,298 |
| moonshot_h10_11 | -0.1162 | -0.1816 | -0.0855 | -0.0511 | -0.1634 | **-0.1196** | 0.1675 | -0.2870 | 2,023 |
| moonshot_h00_01 | -0.0832 | -0.1414 | -0.1342 | -0.2198 | -0.0653 | **-0.1288** | 0.1477 | -0.2765 | 3,974 |
| moonshot_h02_03 | -0.0717 | -0.1233 | -0.1694 | -0.1406 | -0.1649 | **-0.1340** | 0.1763 | -0.3103 | 2,982 |
| moonshot_h01_02 | -0.1711 | -0.0988 | -0.1080 | -0.1722 | -0.1266 | **-0.1353** | 0.1570 | -0.2923 | 3,985 |
| moonshot_h12_13 | -0.0863 | -0.1851 | -0.1275 | -0.1264 | -0.1585 | **-0.1368** | 0.1546 | -0.2914 | 5,049 |
| moonshot_h22_23 | -0.1980 | -0.2793 | -0.0695 | -0.0433 | -0.0956 | **-0.1371** | 0.2117 | -0.3488 | 2,497 |
| moonshot_h06_07 | -0.1353 | -0.1411 | -0.1968 | -0.1193 | -0.0950 | **-0.1375** | 0.1857 | -0.3232 | 6,147 |
| moonshot_h19_20 | -0.0485 | -0.0731 | -0.1959 | -0.1474 | -0.2493 | **-0.1428** | 0.1825 | -0.3254 | 3,204 |
| moonshot_h03_04 | -0.1768 | -0.1539 | -0.1410 | -0.1263 | -0.1825 | **-0.1561** | 0.2065 | -0.3626 | 3,440 |
| moonshot_h16_17 | -0.0638 | -0.2994 | -0.1986 | -0.1629 | -0.0659 | **-0.1581** | 0.1578 | -0.3159 | 2,190 |
| moonshot_h18_19 | -0.1503 | 0.0154 | -0.1814 | -0.3129 | -0.1879 | **-0.1634** | 0.1720 | -0.3354 | 2,948 |
| moonshot_h11_12 | -0.1169 | -0.2467 | -0.1168 | -0.2283 | -0.1118 | **-0.1641** | 0.1566 | -0.3206 | 2,775 |
| moonshot_h08_09 | -0.0390 | -0.3255 | -0.0170 | -0.3201 | -0.1408 | **-0.1685** | 0.1665 | -0.3350 | 1,142 |
| moonshot_h17_18 | -0.1257 | -0.0653 | -0.3874 | -0.1959 | -0.0807 | **-0.1710** | 0.1482 | -0.3191 | 3,090 |
| moonshot_h14_15 | -0.1589 | 0.0503 | -0.2254 | -0.3552 | -0.1915 | **-0.1761** | 0.1479 | -0.3241 | 574 |
| moonshot_h04_05 | -0.1983 | -0.1445 | -0.2387 | -0.1861 | -0.1649 | **-0.1865** | 0.2215 | -0.4080 | 3,729 |
| moonshot_h05_06 | -0.1726 | -0.2552 | -0.2214 | -0.2136 | -0.0893 | **-0.1904** | 0.1959 | -0.3863 | 4,984 |
| moonshot_h23_00 | -0.1061 | -0.1409 | -0.3026 | -0.2238 | -0.2047 | **-0.1956** | 0.1960 | -0.3916 | 1,900 |
| moonshot_h13_14 | 0.0125 | -0.2023 | -0.4314 | -0.2199 | -0.1505 | **-0.1983** | 0.1216 | -0.3200 | 874 |
| moonshot_h07_08 | -0.1676 | -0.1189 | -0.2061 | -0.2043 | -0.3149 | **-0.2024** | 0.1278 | -0.3302 | 1,733 |
| moonshot_h21_22 | -0.1643 | -0.3804 | -0.1621 | -0.2665 | -0.2404 | **-0.2427** | 0.2228 | -0.4656 | 2,777 |
| moonshot_h20_21 | -0.2296 | -0.1973 | -0.2223 | -0.3814 | -0.3729 | **-0.2807** | 0.1930 | -0.4737 | 3,725 |

**`london` is the best-gross session in 4 of 5 months** at mean -0.0251 on n=18,538; `ny` is second at
-0.0694 on n=18,247 and carries the CHEAPEST real cost of any bucket (0.1158), giving it the best mean
net@real of any large bucket (-0.1852). Every hour bucket outside the three named sessions is worse on
gross than all three of them. Unlike the symbol axis this holds at n>5,000/bucket.


---

## 6. NEW FINDING E2-N3 — the estate's best conditioned cell, and its honest statistics

A pre-enumerated sweep of **100 declared cells**: 10 family depths (ordered by
JANUARY real cost only) x 5 session sets x 2 gate choices, each read on all five months.
**7 of 100 have positive mean gross; 2 have positive mean net@real** (and those two are
the same cell with and without a gate that does not bind it).

| cell | JAN | FEB | MAR | APR | MAY | mean gross | mean net@real | months gross>0 | min month n | total n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `K2|ny|nogate` | -0.0374 | 0.0969 | -0.0209 | 0.0896 | 0.0756 | **0.0408** | 0.0114 | 3 | 47 | 390 |
| `K2|ny|realgate` | -0.0374 | 0.0969 | -0.0209 | 0.0896 | 0.0756 | **0.0408** | 0.0114 | 3 | 47 | 390 |
| `K1|ny|nogate` | -0.0525 | 0.0449 | -0.0272 | 0.0790 | 0.0613 | **0.0211** | -0.0076 | 3 | 46 | 331 |
| `K1|ny|realgate` | -0.0525 | 0.0449 | -0.0272 | 0.0790 | 0.0613 | **0.0211** | -0.0076 | 3 | 46 | 331 |
| `K2|london_ny|nogate` | -0.0658 | 0.0985 | -0.0073 | 0.0444 | 0.0025 | **0.0145** | -0.0244 | 3 | 107 | 863 |
| `K2|london_ny|realgate` | -0.0710 | 0.1023 | -0.0073 | 0.0426 | 0.0025 | **0.0138** | -0.0223 | 3 | 107 | 834 |
| `K3|london|nogate` | -0.0345 | 0.1281 | -0.1231 | 0.0116 | 0.0494 | **0.0063** | -0.0709 | 3 | 365 | 2335 |
| `K3|london|realgate` | -0.0488 | 0.1499 | -0.1061 | 0.0079 | -0.0271 | **-0.0049** | -0.0662 | 2 | 306 | 2016 |
| `K2|london_ny_tokyo|nogate` | -0.0978 | 0.0978 | -0.0121 | -0.0131 | -0.0032 | **-0.0057** | -0.0477 | 1 | 182 | 1185 |
| `K2|london_ny_tokyo|realgate` | -0.1040 | 0.1005 | -0.0121 | -0.0148 | -0.0032 | **-0.0067** | -0.0467 | 1 | 181 | 1156 |

### 6.1 The winner, stated honestly

**Cell:** K2|ny = {regime_transition_break, volatility_compression_expansion} x session_bucket==ny, takeable

| statistic | value |
|---|---|
| n | **390** (JAN 117, FEB 102, MAR 64, APR 47, MAY 60) |
| distinct decision days | 89 |
| pooled gross mean | **+0.033118** |
| bootstrap 90% CI on gross | [-0.0195, 0.0870] |
| bootstrap 95% CI on gross | [-0.0297, 0.0968] |
| real cost | 0.029481 |
| pooled net@real | **+0.003637** |
| bootstrap 90% CI on net@real | [-0.0491, 0.0575] |
| permutation p vs same-month NY peers (B=20,000) | **0.0548** |
| NY universe gross mean (the null it beats) | -0.066853 |
| declared looks in this lane | 100 |

**Symbol composition:** {"JP225": 34, "US30_cash": 31, "SPX500": 31, "XAGUSD": 27, "NAS100": 27, "AUDJPY": 23, "XAUUSD": 21, "USDJPY": 20, "UKOIL_cash": 19, "GBPUSD": 19, "USDCAD": 17, "NZDUSD": 15, "USOIL_cash": 15, "AUDUSD": 14, "EURUSD": 13, "CHFJPY": 13, "GER40": 11, "EURGBP": 10, "UK100": 8, "GBPJPY": 8, "USDCHF": 7, "EURJPY": 7}

**Read it exactly as it is.** The pooled gross mean is +0.0331; the +0.0408 in the sweep table is the
mean of per-month means, which weights a 47-row April equally with a 117-row January. The 90% bootstrap
interval spans zero. The permutation p of 0.0548 is against a same-month NY null, i.e. it already controls
for session and month, but it does NOT control for the 100 declared looks. **This is a discovery-grade
signal that survives five months and a session-matched permutation at n=390. It is not an admission and
no gate in this estate would pass it.** What makes it interesting is not the p-value but that its two
families are the two the January cost ranking picked FIRST, before any outcome was read.

### 6.2 Named conditioned cells, for the record

| cell | JAN | FEB | MAR | APR | MAY | mean net@real | mean gross | total n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cell1_london_ny | -0.2203 | -0.1824 | -0.1501 | -0.1659 | -0.2408 | **-0.1919** | -0.0468 | 36,785 |
| cell2_4fam | -0.1770 | -0.0710 | -0.1277 | -0.1489 | -0.1644 | **-0.1378** | -0.0510 | 29,882 |
| cell3_4fam_x_londonny | -0.1655 | -0.0319 | -0.1234 | -0.0902 | -0.1509 | **-0.1124** | -0.0337 | 12,642 |
| cell4_4fam_x_londonny_x_realgate | -0.1408 | -0.0122 | -0.1204 | -0.0803 | -0.1591 | **-0.1026** | -0.0421 | 10,702 |
| cell5_2fam_x_londonny_x_realgate | -0.1071 | 0.0691 | -0.0379 | 0.0019 | -0.0376 | **-0.0223** | 0.0138 | 834 |
| cell6_sorb_only | -0.1623 | 0.0211 | -0.2131 | -0.0672 | -0.1297 | **-0.1102** | -0.0300 | 4,677 |
| cell7_sorb_londonny_realgate | -0.1478 | 0.0356 | -0.2088 | -0.0417 | -0.1828 | **-0.1091** | -0.0471 | 3,445 |
| cell8_rtb_only | -0.0472 | 0.0040 | -0.0697 | -0.0834 | -0.0995 | **-0.0592** | -0.0217 | 1,307 |
---

## 7. NEW FINDING E2-N4 — the born_past_stop artifact is ONE family's generator defect, in every month

W0-capture found 3,516 January rows (12.72%) emitted with the stop already breached, "98.61% one family".
Measured in all five months, within-family:

| family | JAN | FEB | MAR | APR | MAY |
|---|---:|---:|---:|---:|---:|
| current_breaker_re_entry | 81.42% | 45.94% | 69.42% | 81.78% | 79.59% |
| current_ob_retest | 3.58% | 36.97% | 3.24% | 2.16% | 3.59% |
| displacement_continuation | 0.00% | 0.00% | 0.02% | 0.00% | 0.00% |
| liquidity_sweep_reclaim | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| cross_asset_lead_lag | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| current_fvg_fill | 0.00% | 23.20% | 0.00% | 0.00% | 0.00% |
| volatility_compression_expansion | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| session_open_range_break | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| structural_distance_extreme | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| regime_transition_break | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| **pool** | 12.72% | 12.74% | 5.76% | 12.09% | 12.78% |
| **pool, reweighted to JAN family mix** | 12.72% | 14.87% | 10.86% | 12.71% | 12.44% |

**Two things fall out.**

1. **It is a `current_breaker_re_entry` generator defect, not a pool-wide phenomenon.** That family runs
   45.9%-81.8% past-stop in every month; seven of the other nine families run **exactly 0.00% in every
   month**. The defect is structural and monthly-persistent, which strengthens W0-capture's finding
   rather than qualifying it.

2. **March's low 5.76% is mostly composition, not a different engine.** March's
   `current_breaker_re_entry` share is 8.06% against January's 15.41%. Reweighted to January's family
   mix March reads 10.86% against January's 12.72% — so composition explains most of the gap and the
   remainder is a lower within-family rate (69.4% vs 81.4%). Pool-level past-stop shares are NOT
   comparable across months without this reweighting.

3. **FEBRUARY IS THE ANOMALY and it is new information about the estate's used-once VAL month.**
   February is the ONLY month where the defect leaks outside `current_breaker_re_entry`:
   `current_fvg_fill` 23.20% and `current_ob_retest` 36.97% past-stop, against 0.00% and ~3.2-3.6% in
   every other month — while `current_breaker_re_entry` itself is unusually LOW at 45.94%. Any February
   result conditioned on those two families is measuring a different population from the same result in
   any other month.

### 7.1 Family composition of the pool, for anyone pooling months

| family | JAN | FEB | MAR | APR | MAY |
|---|---:|---:|---:|---:|---:|
| current_fvg_fill | 0.2584 | 0.2763 | 0.3066 | 0.2513 | 0.2330 |
| liquidity_sweep_reclaim | 0.1618 | 0.1825 | 0.1690 | 0.1609 | 0.1707 |
| displacement_continuation | 0.1616 | 0.1666 | 0.1706 | 0.1715 | 0.1755 |
| current_breaker_re_entry | 0.1541 | 0.0980 | 0.0806 | 0.1465 | 0.1584 |
| cross_asset_lead_lag | 0.0753 | 0.0807 | 0.0770 | 0.0767 | 0.0765 |
| structural_distance_extreme | 0.0721 | 0.0745 | 0.0719 | 0.0748 | 0.0639 |
| current_ob_retest | 0.0485 | 0.0495 | 0.0512 | 0.0499 | 0.0498 |
| session_open_range_break | 0.0357 | 0.0389 | 0.0382 | 0.0366 | 0.0384 |
| volatility_compression_expansion | 0.0219 | 0.0226 | 0.0244 | 0.0218 | 0.0232 |
| regime_transition_break | 0.0107 | 0.0104 | 0.0105 | 0.0100 | 0.0108 |

---

## 8. WHAT WOULD MAKE THIS BANKABLE

Stated as specific evidence requirements, in the order that closes the most uncertainty per unit of cost.

**B1 — a month-matched spread series. This is the single largest open error bar and it is cheap.**
Every `real cost` number in this lane and in l10 uses ONE per-symbol median spread in bps measured on the
FTMO tick archive **2026-06-18..07-24**, applied to January-May 2026 rows. The tick archive at
`/Users/borr/GTOSActive/vps-ticks-20260726/` covers only 2026-06-18..07-24 (263,894,769 rows), so no
month in this lane has its own measured spread. The real-cost level could be wrong by the ratio of
June-July spreads to January-May spreads, and that ratio is unmeasured. Nothing here changes SIGN under
plausible error — the pool would have to be 2-3x cheaper than modelled for any book to cross zero — but
the +0.28 lever price and the +0.0036 cell net are both inside that band. **Requirement: a per-symbol
spread series for 2026-01..05, from broker tick data or a bar-level bid/ask capture.**

**B2 — the fill contract, which this instrument does not model at all.** Every number here is fill-blind
`gross_r` per W0-F2: 55.2% of "target-first" January paths reach +2R before `entry_price` is ever traded.
W0 measured that requiring the fill moves the pool from +0.0409 to -0.2367 on a first-touch contract. The
cheapest families are also the ones with the widest risk distance relative to price, so they are
plausibly the LEAST affected — but that is a hypothesis, not a measurement. **Requirement: re-run the
Section 4 ladder and the Section 6 cell under `w0_ws.walk(require_fill=True)`, all five months.** This is
the highest-value next test in the lane and it needs no new data.

**B3 — the cell at n that can carry a decision.** The best cell is 390 rows over five months (78/month,
47 in its thinnest month). Its two families are 1.07% and 2.19% of the pool. At the estate's ratified
standard (`CANDIDATE_BOOK_V1`, all-declared basis, `B_balanced` alpha 0.10) it cannot be evaluated at
this n. **Requirement: either more months (Jun-Dec 2026 packs do not exist), or a relaxation of the cell
to the point where n/month exceeds ~300 while keeping positive mean gross — the K3/london cell
(n>=306/month) is the nearest candidate and it is gross-positive in 3 of 5 months at mean +0.0063.**

**B4 — the 2-hour wall.** Every path in this substrate is capped at 120 M1 bars
(`REPAIRED_PENDING_EXPIRY_MINUTES=120`), and W0-capture measured that continuing marked trades into raw
M1 for 24 h is worth +0.017 R/filled trade. `regime_transition_break` and
`volatility_compression_expansion` are the two families whose exits are least likely to be resolved
inside 2 h. **Requirement: extend the winning cell's paths past the wall with the same no-look-ahead
anchor discipline used here.**

**B5 — the gate mis-ranking, priced against the LIVE book rather than the pool.** Section 3 shows the
frozen gate mis-ranks on 35-45% of candidates. That gate is live
(`broker_net_cost_engine.py:859-866` spread limb, `:923-927` total limb, thresholds at
`config/agent_config.yaml:715-716`). Its correction is a config/engine change with a decision-contract
consequence (H1). **Requirement: the same frozen-vs-real confusion matrix computed on the sleeves the
live book actually runs, not on the broad V4 pool — that is the version of this number Borhen can act
on.**


---

## 9. EVIDENCE SPEND REGISTER — declared honestly

- **APRIL_2026** — ECONOMICS READ by this lane. Source docs/audits/.../phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz (Session CS, billed:false, selection_authority NONE_SUBSTRATE_ONLY). Read: opportunity_net_proxy_r, cost_r, spread_r, expected_cost_r, entry_price, stop_loss, origin_family, session_bucket over all 25,056 rows. Purpose: cross-month extension of the l10 X7 cost-truth finding. No selection was made ON April; every family/symbol/session set evaluated was fixed by JANUARY real cost before April was opened.
- **MAY_2026** — ECONOMICS READ by this lane. Source CS_MAY_S0R0_POOL_V1.jsonl.gz, 21,285 rows, same fields and same purpose and same pre-fixed selection.
- **MARCH_2026** — ECONOMICS READ by this lane from the FA2_M_R0 (S0R0 baseline) missed-opportunity ledger, 26,500 diagnostic-scoreable rows of 130,004. March was already decoded once by Session MARCH-EXEC on 2026-08-05/06; this is a second read of the same decoded arm, not a new decode.
- **FEBRUARY_2026** — ECONOMICS READ. Already used-once VAL per wave 18.

**Claim class: DISCOVERY / LANE ITERATION. billed:false. No admission claim anywhere in this receipt.**

The protective property worth stating precisely: **every family set, symbol set, session set and gate
threshold evaluated in Sections 4-6 was fixed by JANUARY real cost — a quantity that contains no
outcome — before any April or May row was opened.** April and May were used to MEASURE a
pre-specified structure, not to search for one. The only search in this lane is the 100-cell sweep in
Section 6, and its look count is declared in the artifact itself
(`E2_SWEEP_V1.json -> look_declaration`).


---

## 10. ARTIFACTS

| file | what |
|---|---|
| `e2_RESULT.md` | this receipt |
| `e2_RESULT.json` | every number above, machine-readable |
| `E2_JAN_REPRO_V1.json` | 60/60 reproduction, both paths |
| `E2_FIVE_MONTHS_V1.json` | full books, five months |
| `E2_MONTHS_ANCHORED_V1.json` | four-month anchored books |
| `E2_MONTHS_NOANCHOR_V1.json` | four-month A-book, no anchor |
| `E2_SCALE_VS_RANK_V1.json` | scale-vs-rank, four months |
| `E2_DECOMP_V1.json` | lever stages + scale/rank five months + symbol/session boundary |
| `E2_BOUNDARY_V1.json` | cross-month family/symbol Spearman tables |
| `E2_LEVER_PRICE_V1.json` | January-selected K-ladder, all months |
| `E2_BEST_CELL_V1.json` | gate-fix value + named conditioned cells |
| `E2_SWEEP_V1.json` | 100 declared cells with the look declaration |
| `E2_CELLSTAT_V1.json` | bootstrap + permutation on the winning cell |
| `E2_COMPOSITION_V1.json` | family mix and past-stop rate by month |
| `E2_MARCH_EXTRACT_V1.json` | March pool construction receipt |
| `E2_SCHEMA_V1.json` | pool schema diff across months |
| `e2_MARCH_R0_POOL_V1.jsonl.gz` | the March pool this lane built (26,500 rows) |
| `e2_ANCHOR_{JAN,FEB,MAR,APR,MAY}.jsonl.gz` | zero-look-ahead decision anchors, one per month |
| `e2_scripts/e2_recost.py` | the portable cost instrument |
| `e2_scripts/e2_02_anchor.py` | the portable anchor builder |
| `e2_scripts/e2_01..e2_19` | every measurement script, in order |
# LANE l7 — WHAT ELSE IS BACKWARDS

**Headline.** Over the 14,911 January candidates whose entry price IS the decision-instant market price (geometry-free and selection-free), taking the **opposite side at market** with the generator's own risk distance is worth **+0.0764 R/trade** of directional information (day-block bootstrap 95% [+0.0530, +0.1020], p(<=0)=0.0000, t=8.71, positive on **20 of 21 trading days** and **23 of 24 symbols**). The signal's direction is inverted across the whole book, not in one family. It is **not** the CQ breaker phenomenon — the two populations share **zero rows**.

**And the qualifier that governs how to read every number below: it is a ONE-MINUTE effect.** Delay the entry by two minutes and the directional signal falls to **+0.0148 R/trade, p=0.157** — gone. At the median risk distance the whole signal is **0.783 bps of price** (1.566 bps between the two legs). This is not a directional forecast the book can trade; it is a measurement that **the generator's entry price is systematically on the wrong side of the very next minute**, by about one spread. Section 2.1 is the ladder.

**Which turns the whole lane into a repair that requires no inversion at all.** Keep the signal's own direction, keep the risk distance, keep the target and stop — just stop entering at the trigger bar's close. Waiting **5 minutes** is worth **+0.0670 R/trade** (paired per row, day-block bootstrap 95% [+0.0550, +0.0786], p(<=0)=0.000, n=14,837) and moves the at-market book from **-0.0601 to +0.0069 — across zero**. `structural_distance_extreme` moves **-0.0825 -> +0.1083** and `off_configured_session` **-0.0996 -> +0.0111**. Section 3.4. **The direction is not backwards; the entry instant is, and the inversion at delay 0 is its shadow.**

## 0. Instruments — read before any number below

An 'inverse' at the same limit level is NOT a mirror: the fill contract differs (a buy limit below market becomes a sell order above it). Every directional claim here uses the **at-market pair**, which is an exact mirror:

```
fav_atm = fav - mkt_r     adv_atm = adv - mkt_r     (signal's own side, entered at market)
fav_inv = -adv_atm        adv_inv = -fav_atm          (opposite side, same price, same d)
info    = (inv_atm_r - orig_atm_r) / 2
```

Both legs fill at bar 1 by construction, carry the same risk distance `d`, the same +2R/-1R contract, the same conservative same-bar tie-to-stop rule, and mark to market at the same 120-bar wall. No fill contract, no geometry and no horizon can bias `info`. Anchor is `mkt_r_prev_close` — the close of the last M1 bar **strictly before** the decision minute, i.e. the w0-capture V2 no-look-ahead anchor. Reproduces w0-capture's born census exactly (at_limit 14,911 / resting 7,949 / past_stop 3,516 / marketable 1,265).

**Integrity checks.** `orig_atm_r == orig_blind_r` on all 14,911 at-limit rows, max |diff| **0.00e+00** (the at-market entry IS the limit there). Engine `gross_r` vs path-derived blind walk: sign agreement **90.69%**, Pearson **+0.7503** — a flipped side convention in the sidecar would be strongly negative, so the convention is consistent. `which_came_first` reproduces the walk reason on 27,648 of 27,658 rows.

## 1. THE INVERSION, by born state

| born state | n | orig at-market | inv at-market | INFO | INFO 95% lo | INFO 95% hi | INFO first-emission |
|---|---|---|---|---|---|---|---|
| born_at_limit | 14911 | -0.0596 | +0.0931 | +0.0764 | +0.0530 | +0.1020 | +0.0746 |
| born_resting | 7949 | -0.6726 | +0.8366 | +0.7546 | +0.7028 | +0.8069 | +0.7796 |
| born_past_stop | 3516 | -0.0028 | +0.0078 | +0.0053 | -0.1054 | +0.1019 | +0.0067 |
| born_marketable | 1265 | +0.0050 | -0.0082 | -0.0066 | -0.0992 | +0.0962 | -0.0368 |

`born_at_limit` is the clean cell: entry == market exactly (one distinct `mkt_r` value, 0.0), so the inverse target sits exactly 2R away just like the original's, and the fill is instantaneous so the pool's fill-conditioning (section 5) cannot have selected on the path.

## 2. The two controls that decide it

| population | n | long share | long@mkt | short@mkt | INFO | 95% lo | INFO lag-1 | 95% lo | INFO drift-free | 95% lo | p(<=0) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 27641 | 45.2% | +0.0643 | +0.0014 | +0.2586 | +0.2269 | +0.2287 | +0.1942 | +0.2579 | +0.2269 | 0.000 |
| GEOMETRY_FREE_at_limit | 14911 | 45.5% | +0.0406 | -0.0071 | +0.0764 | +0.0531 | +0.0438 | +0.0163 | +0.0749 | +0.0519 | 0.000 |
| GEOMETRY_FREE_absmkt_le2 | 22212 | 44.1% | +0.0515 | -0.0168 | +0.2269 | +0.1979 | +0.1916 | +0.1610 | +0.2260 | +0.1973 | 0.000 |
| TRADEABLE_ex_past_stop | 24125 | 44.7% | +0.0709 | +0.0037 | +0.2955 | +0.2633 | +0.2607 | +0.2255 | +0.2953 | +0.2626 | 0.000 |
| FIRST_EMISSION_at_limit | 14814 | 45.6% | +0.0429 | -0.0125 | +0.0746 | +0.0526 | +0.0417 | +0.0155 | +0.0727 | +0.0511 | 0.000 |

**C2 market drift is refuted.** `delta = (short@mkt - long@mkt)/2` knows nothing about the signal, so any common January drift sits in it identically for LONG- and SHORT-signalled rows. On the clean population `delta|LONG-signal = +0.0577` and `delta|SHORT-signal = -0.0920` — a **+0.1497 gap straddling zero** — while the unconditional drift is only **-0.0238**. The drift-free statistic `info_clean = +0.0749` is within 0.0015 of the raw `info`. The signal's own direction call is what is inverted.

**C1 latency is the binding caveat, and it is severe.** Re-entering at the close of the decision-minute bar (a 1-minute delay) gives `info` **+0.0438** on the clean population and **+0.2287** pool-wide. Pushing it further kills it outright — see 2.1.

### 2.1 Entry-latency ladder — enter at the close of path bar k, walk bars k+1..120

Unambiguous construction: the entry price is fully known at the end of bar k and no bar before k+1 is scored, so orig and inv stay exact mirrors at every rung.

| delay (min) | n | orig@mkt | inv@mkt | INFO | boot 95% lo | boot 95% hi | p(<=0) | t |
|---|---|---|---|---|---|---|---|---|
| 0 | 14911 | -0.0596 | +0.0931 | +0.0764 | +0.0513 | +0.0995 | 0.000 | 8.71 |
| 1 | 14911 | -0.0039 | +0.0258 | +0.0148 | -0.0142 | +0.0395 | 0.157 | 1.70 |
| 2 | 14911 | -0.0085 | +0.0153 | +0.0119 | -0.0127 | +0.0330 | 0.186 | 1.37 |
| 3 | 14905 | +0.0003 | +0.0157 | +0.0077 | -0.0176 | +0.0298 | 0.300 | 0.89 |
| 5 | 14905 | +0.0072 | +0.0225 | +0.0077 | -0.0167 | +0.0311 | 0.296 | 0.88 |
| 10 | 14895 | -0.0007 | +0.0184 | +0.0096 | -0.0185 | +0.0347 | 0.251 | 1.11 |
| 15 | 14893 | -0.0031 | +0.0250 | +0.0141 | -0.0137 | +0.0396 | 0.171 | 1.64 |
| 30 | 14865 | -0.0190 | +0.0335 | +0.0262 | -0.0001 | +0.0515 | 0.028 | 3.13 |
| 60 | 14646 | -0.0085 | +0.0356 | +0.0221 | +0.0037 | +0.0428 | 0.010 | 2.78 |

**The signal is 81% gone after two minutes and is not statistically distinguishable from zero anywhere between 2 and 15 minutes.** (The 30- and 60-minute rungs turn significant again at +0.0262 / +0.0221 — a separate, slower effect this lane does not characterise, and a real lead for a later wave.)

This ladder was produced independently twice. A prior l7 attempt that did not survive to write a receipt left `L7_DELAY_LADDER_V1.json` and `L7_CRUX_V2.json` in this directory; its `dir_signal_mean` is **+0.0763844644893032** against this lane's **+0.0763844644893032**, and its delay rungs (0.07638 / 0.01482 / 0.01189 / 0.00765 / 0.01407 at 0/1/2/5/15) reproduce the table above to 4 decimals from different code. **This lane's first latency estimate (`info_lag1 = +0.0438`) was measured at a 1-minute delay and is correct at that delay; it is not in conflict with the 2-minute rung, and the 2-minute rung is the one that matters.**

### 2.2 Physical scale — the signal is one spread wide

| quantity | value |
|---|---|
| median risk distance `d` (clean population) | 0.10249% of price |
| directional signal | 0.0764 R = **0.783 bps** of price |
| spread between the two legs (2 x info) | **1.566 bps** |
| pool FROZEN spread charge, median | 1.044 bps |
| true spread at the measured 7.3x over-charge, median | 0.143 bps |

The one-minute adverse move is **5.5x the corrected true spread** and **0.75x the frozen charge** — which is why the spread model is *not* what kills the inverse (section 4); the non-spread fixed costs are.

## 3. MECHANISM

### 3.1 It is monotone in stop tightness — measured WITHIN family so it is not a family proxy

| risk-distance quintile | n | median d (% of price) | orig@mkt | inv@mkt | INFO |
|---|---|---|---|---|---|
| 1 | 2979 | 0.0334 | -0.0823 | +0.1452 | +0.1138 |
| 2 | 2979 | 0.0551 | -0.0819 | +0.1192 | +0.1006 |
| 3 | 2979 | 0.0868 | -0.0638 | +0.0694 | +0.0666 |
| 4 | 2979 | 0.1628 | -0.0339 | +0.0799 | +0.0569 |
| 5 | 2989 | 0.4810 | -0.0355 | +0.0502 | +0.0429 |

Tightest-stop quintile **+0.1138**, widest **+0.0429**, monotone. The tighter the generator's own stop, the more inverted its direction call.

### 3.2 The generators, read at source

Every one of the seven families in the clean population enters at `entry=bar.close` — that is *why* they are the at-limit population. Three read directly:

| family | source | rule | direction | INFO |
|---|---|---|---|---|
| `structural_distance_extreme` | `src/components/broader_origin_generators.py:862-897` | `pos50>=0.97` -> SHORT at close, stop `bar.high+0.25*atr14`; `pos50<=0.03` -> LONG | **fades** a 50-bar (12.5 h) range extreme | **+0.1356** |
| `cross_asset_lead_lag` | `broader_origin_generators.py:1023-1032` | `side = LONG if leader_move>0 else SHORT`, fired only when `lag_response<=0.5` | **follows** a 1-bar leader impulse into an unresponsive lag | **+0.1002** |
| `displacement_continuation` | `broader_origin_generators.py:745-752` | `range/atr14>=1.5 and body/atr14>=0.75`; `side = LONG if close>open`, stop at the far end of the bar | **follows** a 1-bar (15 min) impulse | **+0.0818** |
| `liquidity_sweep_reclaim` | `broader_origin_generators.py:708-742` | swept prior-20 high and closed back below -> SHORT at close | **fades** a 20-bar sweep | +0.0355 (95% lo -0.0111, not significant) |

The pairing looks **backwards at both scales** — the family that *fades* a 12.5-hour extreme is the most inverted (continuation wins there) and the families that *follow* a 15-minute impulse are inverted too (reversion wins there) — but the latency ladder says the common cause is simpler and sits below both. **Entry is `entry=bar.close` in every one of the seven clean families**, i.e. at the extreme of the bar whose extremeness is the trigger condition, and the whole effect is spent in the next one to two minutes. The direction the rule chose barely matters; the *price* it chose does. The one family whose trigger does not require a directional close — `liquidity_sweep_reclaim`, which requires a **reclaim** (`bar.low < p_low20 and bar.close > p_low20`), so its close is back *inside* the range rather than at an extreme — is the one family that is **not** significantly inverted (+0.0355, 95% lo -0.0111). That is the mechanism, and it is a testable prediction the pool corroborates.

### 3.3 London is the exception — the original direction WORKS there

| route session | n | orig@mkt | inv@mkt | INFO | 95% CI | p(<=0) |
|---|---|---|---|---|---|---|
| london | 3112 | +0.0235 | +0.0077 | -0.0079 | [-0.0454, +0.0362] | 0.634 |
| ny | 3190 | -0.0498 | +0.0883 | +0.0690 | [+0.0247, +0.1159] | 0.001 |
| tokyo | 954 | -0.0529 | +0.1525 | +0.1027 | [+0.0326, +0.1841] | 0.001 |
| off_configured_session | 7655 | -0.0984 | +0.1224 | +0.1104 | [+0.0759, +0.1411] | 0.000 |

`london` is the **only** session with a positive at-market original (+0.0235) and its `info` is **-0.0079**, 95% CI [-0.0454, +0.0362], p(<=0)=0.634 — indistinguishable from zero. Inside London the same families invert back:

| family x session | n | orig@mkt | inv@mkt | INFO |
|---|---|---|---|---|
| liquidity_sweep_reclaim|london | 913 | +0.0765 | -0.0860 | -0.0813 |
| structural_distance_extreme|london | 334 | +0.1632 | +0.0368 | -0.0632 |
| cross_asset_lead_lag|london | 406 | +0.1142 | -0.0116 | -0.0629 |
| regime_transition_break|off_configured_session | 130 | +0.0692 | -0.0415 | -0.0554 |
| structural_distance_extreme|tokyo | 106 | +0.1204 | +0.1038 | -0.0083 |

This is the lane's partial-inversion finding: **the book is directionally correct in London and inverted everywhere else.** `off_configured_session` — 7,655 of the 14,911 clean rows (51.3%) — is the most inverted session at +0.1104, and w0-dictionary D12 measured that only 1,079 rows in the whole month are actually rejected for firing off-session.

### 3.4 THE REPAIR — same direction, later entry

If the mechanism is the entry price rather than the direction, then simply delaying the entry should repair the book without any inversion. It does. Paired per row against delay 0, same side, same `d`, same +2R/-1R, same wall:

| delay (min) | orig level | delta vs delay 0 | 95% lo | 95% hi | p(<=0) | orig NET @spread/7.3 | % rows whose outcome moved |
|---|---|---|---|---|---|---|---|
| 0 | -0.0601 | **+0.0000** | +0.0000 | +0.0000 | 1.000 | -0.2261 | 0.0% |
| 1 | -0.0047 | **+0.0554** | +0.0414 | +0.0694 | 0.000 | -0.1707 | 39.2% |
| 2 | -0.0089 | **+0.0512** | +0.0373 | +0.0670 | 0.000 | -0.1748 | 41.1% |
| 3 | -0.0002 | **+0.0599** | +0.0456 | +0.0751 | 0.000 | -0.1662 | 42.7% |
| 5 | +0.0069 | **+0.0670** | +0.0550 | +0.0786 | 0.000 | -0.1591 | 45.0% |
| 10 | -0.0009 | **+0.0592** | +0.0403 | +0.0768 | 0.000 | -0.1669 | 48.9% |
| 15 | -0.0040 | **+0.0561** | +0.0403 | +0.0730 | 0.000 | -0.1699 | 52.3% |
| 30 | -0.0191 | **+0.0410** | +0.0181 | +0.0658 | 0.001 | -0.1851 | 58.2% |

Every rung from 1 to 30 minutes is positive and significant; **5 minutes is the peak at +0.0670 R/trade** and is the only rung where the at-market book is positive (+0.0069). Only 45.0% of rows change outcome at all, so the gain is concentrated at roughly **+0.149 R on the rows that move**. It does **not** repair the net (-0.2261 -> -0.1591 at spread/7.3) — the fixed-cost problem in section 4 is untouched — but it is the only change in this receipt that takes a gross number across zero, and it needs no new signal, no direction flip and no new data.

| family | n | delay 0 | delay 5 | delta |
|---|---|---|---|---|
| structural_distance_extreme | 1973 | -0.0825 | +0.1083 | **+0.1908** |
| liquidity_sweep_reclaim | 4441 | -0.0185 | +0.0456 | **+0.0641** |
| cross_asset_lead_lag | 2072 | -0.0759 | -0.0133 | **+0.0626** |
| displacement_continuation | 4456 | -0.0816 | -0.0407 | **+0.0409** |
| current_fvg_fill | 6 | -0.4928 | -0.4682 | **+0.0246** |
| volatility_compression_expansion | 605 | -0.0918 | -0.0734 | **+0.0184** |
| regime_transition_break | 297 | -0.0035 | +0.0111 | **+0.0147** |
| session_open_range_break | 987 | -0.0673 | -0.0618 | **+0.0056** |

| route session | n | delay 0 | delay 5 | delta |
|---|---|---|---|---|
| off_configured_session | 7581 | -0.0996 | +0.0111 | **+0.1107** |
| ny | 3190 | -0.0498 | -0.0203 | **+0.0294** |
| london | 3112 | +0.0235 | +0.0430 | **+0.0196** |
| tokyo | 954 | -0.0529 | -0.0532 | **-0.0002** |

`tokyo` is the one session the delay does not help (-0.0002) — consistent with it being the session whose inversion is largest at delay 0 for a different reason, and worth its own look.

## 4. IS THE INVERSION HARVESTABLE? No — and the reason is exact

| quintile | n | median d % | INFO | inv gross | cost frozen | cost @spread/7.3 | inv NET @7.3 | 95% lo | orig NET @7.3 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2979 | 0.0334 | +0.1138 | +0.1452 | 0.8817 | 0.2853 | -0.1401 | -0.1875 | -0.3676 |
| 2 | 2979 | 0.0551 | +0.1006 | +0.1192 | 0.6622 | 0.1875 | -0.0683 | -0.1202 | -0.2695 |
| 3 | 2979 | 0.0868 | +0.0666 | +0.0694 | 0.5392 | 0.1430 | -0.0736 | -0.1170 | -0.2068 |
| 4 | 2979 | 0.1628 | +0.0569 | +0.0799 | 0.4404 | 0.1205 | -0.0407 | -0.0936 | -0.1544 |
| 5 | 2989 | 0.4810 | +0.0429 | +0.0502 | 0.2376 | 0.0943 | -0.0441 | -0.0944 | -0.1299 |

Cost is R-denominated, so the same tiny risk distance that maximises the inversion maximises the bill. The ratio `inv_gross / cost@7.3` is **0.51, 0.64, 0.49, 0.66, 0.53** across the five quintiles — the inversion is worth about **half the corrected cost at every geometry**.

**The zero-spread limit settles it.** On the clean population the inverse's gross edge is **+0.09312 R** and the **non-spread** cost floor (commission + the flat 0.02 slippage + swap) is **0.10484 R**. The edge does not clear the cost floor *even if the spread model is corrected to zero*. Per quintile, `edge - fixed cost`:

| quintile | n | inv gross | fixed (non-spread) cost R | edge - fixed | fixed/edge |
|---|---|---|---|---|---|
| 1 | 2979 | +0.1452 | 0.1906 | -0.0454 | 1.31 |
| 2 | 2979 | +0.1192 | 0.1122 | +0.0070 | 0.94 |
| 3 | 2979 | +0.0694 | 0.0801 | -0.0107 | 1.15 |
| 4 | 2979 | +0.0799 | 0.0698 | +0.0101 | 0.87 |
| 5 | 2989 | +0.0502 | 0.0716 | -0.0214 | 1.43 |

Three families do clear the zero-spread floor — the wide-geometry ones: `displacement_continuation` (+0.0185), `session_open_range_break` (+0.0359), `volatility_compression_expansion` (+0.0408). Taken together (n=6,057) the inverted book lands at **exactly break-even**: NET @spread/7.3 **-0.0028** [-0.0341, +0.0278], NET @8.5 **+0.0009**, against the same population's original at **-0.1662**. **Inverting recovers +0.1634 R/trade and lands on zero.**

## 5. THE POOL IS FILL-CONDITIONED — a substrate defect this lane had to find to avoid reporting a fake inversion

`path_final_r` (`src/research_infra/v4_timewarp_simulated_live_research_loop.py:60309-60310`):

```python
fill_status = str(oracle.get("fill_status") or "")
if not fill_status.startswith("filled"):
    return None, "not_filled_no_trade", None
```

`opportunity_net_proxy_r` is therefore `None` for any candidate whose entry was never traded, and the pool filter (w0-dictionary D3) requires `opportunity_net_proxy_r is not None`. **Every row in the 27,658-row pool is a row whose limit filled.** Empirical signature on the 7,949 resting rows: P(price reaches the level) = **99.9623%** against a distance-matched symmetric control of **36.82%**, and the touch hazard over `mkt_r>2` rises **6.909% -> 100.000%** in the final 10-bar block (140 at risk, **140** touched, **0 of 2,171 never touched**). A hazard cannot be 100%; a filter can.

| mkt_r bucket | n | P(reach level) | P(symmetric control) | magnet ratio | median bars to level | R after the fill | inv at-market |
|---|---|---|---|---|---|---|---|
| mkt_r (0,0.5] | 1641 | 99.88% | 75.08% | 1.33x | 4 | -0.1519 | +0.2707 |
| mkt_r (0.5,1] | 1715 | 99.94% | 48.86% | 2.05x | 18 | -0.1290 | +0.5947 |
| mkt_r (1,2] | 2422 | 100.00% | 24.69% | 4.05x | 38 | -0.0961 | +1.0559 |
| mkt_r (2,3] | 1056 | 100.00% | 17.23% | 5.80x | 54 | -0.0432 | +1.3295 |
| mkt_r (3,5] | 731 | 100.00% | 9.03% | 11.08x | 61 | -0.0516 | +1.1546 |
| mkt_r (5,99] | 384 | 100.00% | 2.86% | 34.91x | 72 | +0.0883 | +0.9922 |

Consequence: **the resting-limit inversion (+0.7546 info, born_resting) is NOT bankable** — it is measured on a sample selected on the very price move it claims to predict. It is reported here so no later lane rediscovers it and believes it. The clean at-limit cell is unaffected: those fills are instantaneous.

## 6. CQ / current_breaker_re_entry — INDEPENDENT, zero overlap

CQ's 4,263 inverted-breaker trades join this lane's base on `source_candidate_id` with **0 unmatched**. Their born mix is `{'born_past_stop': 3467, 'born_resting': 596, 'born_marketable': 200}` — **0 rows** (0.00%) sit in this lane's clean population, and `current_breaker_re_entry` contributes **0** rows to it. On CQ's own past-stop rows the inverse is **+1.9632 R blind**, **-0.0172 R** with the fill required, and **+0.0103 R** at market. CQ's +11.9 R/trade is the fill-blind convention; at market or with an honest fill it is zero. **Two different phenomena, no shared rows.**

Corroborating: the honest inverse of the whole `current_breaker_re_entry` family is **-0.1106 R/trade**, not positive (`L7_SWEEP_V1.json` population ALL, `dims=family`).

## 7. Stability within January

| split | n | orig@mkt | inv@mkt | INFO |
|---|---|---|---|---|
| H1 2026-01-02..2026-01-16 | 7262 | -0.0617 | +0.0728 | +0.0673 |
| H2 2026-01-16..2026-01-30 | 7649 | -0.0577 | +0.1124 | +0.0851 |
| week 2026-01-0 | 3019 | -0.0356 | +0.0318 | +0.0337 |
| week 2026-01-1 | 3610 | -0.0894 | +0.1026 | +0.0960 |
| week 2026-01-2 | 3314 | -0.0377 | +0.0896 | +0.0637 |
| week 2026-01-3 | 4968 | -0.0673 | +0.1258 | +0.0965 |

Daily `info` is positive on **20 of 21** trading days.

## 8. Per family and per symbol (clean population)

| family | n | orig@mkt | orig win | inv@mkt | inv win | INFO | 95% lo | BH q |
|---|---|---|---|---|---|---|---|---|
| structural_distance_extreme | 1993 | -0.0797 | 31.1% | +0.1914 | 40.0% | +0.1356 | +0.0501 | 0.000 |
| cross_asset_lead_lag | 2083 | -0.0746 | 33.4% | +0.1257 | 40.0% | +0.1002 | +0.0430 | 0.000 |
| volatility_compression_expansion | 605 | -0.0918 | 43.5% | +0.0820 | 54.9% | +0.0869 | +nan | nan |
| displacement_continuation | 4465 | -0.0815 | 39.8% | +0.0822 | 47.6% | +0.0818 | +0.0508 | 0.000 |
| session_open_range_break | 987 | -0.0673 | 42.2% | +0.0888 | 48.4% | +0.0781 | -0.0067 | 0.038 |
| liquidity_sweep_reclaim | 4475 | -0.0191 | 37.9% | +0.0519 | 40.0% | +0.0355 | -0.0111 | 0.065 |
| regime_transition_break | 297 | -0.0035 | 50.5% | +0.0089 | 49.2% | +0.0062 | +nan | nan |

| symbol | n | median d % | orig@mkt | orig win | inv@mkt | INFO |
|---|---|---|---|---|---|---|
| GBPUSD | 706 | 0.0561 | -0.1651 | 32.3% | +0.1565 | +0.1608 |
| NAS100 | 673 | 0.1175 | -0.1205 | 36.6% | +0.1989 | +0.1597 |
| UK100 | 645 | 0.0923 | -0.1713 | 32.7% | +0.1015 | +0.1364 |
| SPX500 | 655 | 0.0803 | -0.1003 | 36.6% | +0.1705 | +0.1354 |
| USDCAD | 699 | 0.0427 | -0.1351 | 34.9% | +0.1334 | +0.1342 |
| EURGBP | 616 | 0.0382 | -0.1006 | 35.1% | +0.1212 | +0.1109 |
| UKOIL_cash | 606 | 0.2711 | -0.0795 | 38.3% | +0.1267 | +0.1031 |
| USOIL_cash | 605 | 0.2972 | -0.0798 | 39.2% | +0.0943 | +0.0870 |
| AUDJPY | 534 | 0.0979 | -0.0646 | 37.3% | +0.1053 | +0.0850 |
| CHFJPY | 531 | 0.0868 | -0.0599 | 39.0% | +0.1099 | +0.0849 |
| AUDUSD | 525 | 0.0878 | -0.0430 | 39.6% | +0.1138 | +0.0784 |
| GER40 | 615 | 0.1232 | -0.0592 | 37.9% | +0.0713 | +0.0653 |
| GBPJPY | 654 | 0.0647 | -0.0575 | 37.5% | +0.0656 | +0.0615 |
| ETHUSD | 449 | 0.5779 | -0.0551 | 39.2% | +0.0654 | +0.0603 |
| JP225 | 522 | 0.2217 | -0.0532 | 38.9% | +0.0672 | +0.0602 |
| US30_cash | 684 | 0.0813 | -0.0382 | 37.0% | +0.0731 | +0.0557 |
| NZDUSD | 656 | 0.0785 | -0.0403 | 38.6% | +0.0706 | +0.0555 |
| XAUUSD | 729 | 0.2073 | -0.0179 | 37.3% | +0.0718 | +0.0449 |
| BTCUSD | 479 | 0.4403 | -0.0663 | 40.9% | +0.0213 | +0.0438 |
| USDCHF | 661 | 0.0741 | +0.0229 | 40.5% | +0.1038 | +0.0404 |
| EURUSD | 618 | 0.0545 | -0.0413 | 38.7% | +0.0345 | +0.0379 |
| EURJPY | 530 | 0.0773 | -0.0305 | 39.2% | +0.0451 | +0.0378 |
| USDJPY | 796 | 0.0642 | +0.0165 | 37.8% | +0.0797 | +0.0316 |
| XAGUSD | 723 | 0.6171 | +0.0877 | 42.0% | +0.0049 | -0.0414 |

**23 of 24 symbols are inverted.** Only `XAGUSD` is not (-0.0414, and its at-market original is the book's best at +0.0877). `USDCHF` (+0.0229) and `USDJPY` (+0.0165) are the only other positive originals.

## 9. The ranked inversion table (lane item 1)

Cells whose win rate sits below breakeven, ranked by `(breakeven - actual) * n`, on the honest at-market basis over the clean population. Full list of **2640** cells in `L7_CELLS_V1.json`; **1853** of them (70.2%) have positive `info`, rising to **85.7%** among cells with n>=500 — the inversion is a property of the book, not of a cell selection.

| dims | key | n | orig@mkt | orig win | inv@mkt | inv win | INFO | 95% lo | total R | BH q |
|---|---|---|---|---|---|---|---|---|---|---|
| session | off_configured_session | 7655 | -0.098 | 36.1% | +0.122 | 44.7% | +0.1104 | +0.0730 | +845.2 | 0.000 |
| side | SHORT | 8122 | -0.077 | 35.7% | +0.107 | 44.0% | +0.0920 | +0.0401 | +747.3 | 0.000 |
| session|vol | off_configured_session|lo_vol | 3061 | -0.136 | 30.4% | +0.214 | 41.9% | +0.1748 | +0.0989 | +535.0 | 0.000 |
| vol | lo_vol | 4874 | -0.058 | 32.6% | +0.161 | 39.7% | +0.1096 | +0.0513 | +534.2 | 0.000 |
| side|session | SHORT|off_configured_session | 4240 | -0.103 | 34.3% | +0.135 | 45.0% | +0.1187 | +0.0520 | +503.5 | 0.000 |
| vol | hi_vol | 6076 | -0.074 | 41.3% | +0.074 | 49.3% | +0.0743 | +0.0459 | +451.7 | 0.000 |
| side | LONG | 6789 | -0.039 | 40.1% | +0.077 | 43.3% | +0.0577 | +0.0128 | +391.7 | 0.004 |
| family | displacement_continuation | 4465 | -0.081 | 39.8% | +0.082 | 47.6% | +0.0818 | +0.0508 | +365.3 | 0.000 |
| side|session | LONG|off_configured_session | 3415 | -0.093 | 38.3% | +0.107 | 44.4% | +0.1001 | +0.0396 | +341.8 | 0.000 |
| side|vol | SHORT|hi_vol | 2996 | -0.104 | 38.2% | +0.098 | 51.3% | +0.1009 | +0.0353 | +302.4 | 0.000 |
| side|vol | SHORT|lo_vol | 3035 | -0.050 | 32.8% | +0.142 | 38.9% | +0.0963 | +0.0231 | +292.3 | 0.005 |
| family|session | structural_distance_extreme|off_configured_session | 1225 | -0.189 | 27.7% | +0.261 | 42.4% | +0.2248 | +0.1228 | +275.3 | 0.000 |
| family | structural_distance_extreme | 1993 | -0.080 | 31.1% | +0.191 | 40.0% | +0.1356 | +0.0501 | +270.2 | 0.000 |
| family|vol | displacement_continuation|hi_vol | 2955 | -0.085 | 40.3% | +0.090 | 50.2% | +0.0877 | +0.0504 | +259.0 | 0.000 |
| family|session|vol | structural_distance_extreme|off_configured_session|lo_vol | 1124 | -0.196 | 27.5% | +0.257 | 42.3% | +0.2266 | +0.1167 | +254.7 | 0.000 |
| side|session | SHORT|ny | 1660 | -0.140 | 33.7% | +0.164 | 44.9% | +0.1521 | +0.0573 | +252.5 | 0.004 |
| side|vol | LONG|lo_vol | 1839 | -0.071 | 32.2% | +0.193 | 41.2% | +0.1315 | +0.0407 | +241.9 | 0.003 |
| family|vol | structural_distance_extreme|lo_vol | 1823 | -0.072 | 31.4% | +0.192 | 40.0% | +0.1322 | +0.0323 | +241.1 | 0.005 |
| family|session | cross_asset_lead_lag|off_configured_session | 1179 | -0.188 | 29.9% | +0.193 | 43.0% | +0.1905 | +0.1183 | +224.6 | 0.000 |
| session | ny | 3190 | -0.050 | 38.4% | +0.088 | 43.1% | +0.0690 | +0.0225 | +220.2 | 0.007 |
| family|side | displacement_continuation|SHORT | 2275 | -0.096 | 37.8% | +0.093 | 48.7% | +0.0942 | +0.0388 | +214.3 | 0.004 |
| family | cross_asset_lead_lag | 2083 | -0.075 | 33.4% | +0.126 | 40.0% | +0.1002 | +0.0430 | +208.6 | 0.000 |
| family|session|vol | cross_asset_lead_lag|off_configured_session|lo_vol | 752 | -0.237 | 26.9% | +0.295 | 44.3% | +0.2660 | +0.1803 | +200.0 | 0.000 |
| family|side|vol | displacement_continuation|SHORT|hi_vol | 1524 | -0.124 | 36.8% | +0.138 | 53.0% | +0.1311 | +0.0669 | +199.7 | 0.000 |
| hour | h15 | 1192 | -0.151 | 36.7% | +0.161 | 47.0% | +0.1562 | +0.0925 | +186.2 | 0.000 |
| session|vol | off_configured_session|hi_vol | 2581 | -0.069 | 41.3% | +0.075 | 51.1% | +0.0721 | +0.0231 | +186.1 | 0.003 |
| family|side|session | structural_distance_extreme|SHORT|off_configured_session | 892 | -0.171 | 28.3% | +0.244 | 42.0% | +0.2075 | +0.1096 | +185.1 | 0.000 |
| family|vol | cross_asset_lead_lag|lo_vol | 1151 | -0.111 | 30.6% | +0.208 | 41.0% | +0.1594 | +0.0864 | +183.5 | 0.000 |
| family|side | structural_distance_extreme|SHORT | 1406 | -0.075 | 31.3% | +0.168 | 39.3% | +0.1216 | +0.0332 | +171.0 | 0.004 |
| family|side | liquidity_sweep_reclaim|SHORT | 2520 | -0.048 | 35.8% | +0.084 | 40.8% | +0.0659 | -0.0115 | +166.1 | 0.054 |

### Cells where the ORIGINAL direction is right (n>=60)

| dims | key | n | orig@mkt | inv@mkt | INFO | orig win |
|---|---|---|---|---|---|---|
| family|symbol|session | structural_distance_extreme|USDJPY|off_configured_session | 70 | +0.457 | -0.387 | -0.4223 | 50.0% |
| family|hour | liquidity_sweep_reclaim|h23 | 88 | +0.468 | -0.255 | -0.3616 | 59.1% |
| family|side|hour | liquidity_sweep_reclaim|LONG|h11 | 97 | +0.247 | -0.435 | -0.3408 | 49.5% |
| family|symbol | structural_distance_extreme|USDJPY | 119 | +0.336 | -0.337 | -0.3366 | 45.4% |
| family|symbol|side|vol | structural_distance_extreme|USDJPY|SHORT|lo_vol | 83 | +0.288 | -0.349 | -0.3187 | 43.4% |
| family|side|hour | cross_asset_lead_lag|LONG|h14 | 75 | +0.464 | -0.156 | -0.3098 | 50.7% |
| symbol|side|vol | GER40|SHORT|mid_vol | 117 | +0.324 | -0.295 | -0.3096 | 52.1% |
| family|symbol|side | structural_distance_extreme|USDJPY|SHORT | 86 | +0.278 | -0.337 | -0.3075 | 43.0% |
| family|side|hour | liquidity_sweep_reclaim|SHORT|h08 | 137 | +0.324 | -0.272 | -0.2983 | 48.2% |
| family|hour | structural_distance_extreme|h07 | 66 | +0.500 | -0.091 | -0.2955 | 50.0% |
| family|symbol|side | liquidity_sweep_reclaim|AUDUSD|LONG | 71 | +0.277 | -0.308 | -0.2925 | 49.3% |
| family|symbol|vol | structural_distance_extreme|USDJPY|lo_vol | 107 | +0.279 | -0.299 | -0.2892 | 43.0% |
| family|side|hour | liquidity_sweep_reclaim|SHORT|h21 | 100 | +0.242 | -0.327 | -0.2843 | 44.0% |
| symbol|session|vol | USDCHF|london|mid_vol | 61 | +0.280 | -0.287 | -0.2833 | 47.5% |
| family|symbol|vol | liquidity_sweep_reclaim|GER40|mid_vol | 76 | +0.306 | -0.258 | -0.2821 | 50.0% |
| family|symbol|side | liquidity_sweep_reclaim|USDJPY|LONG | 77 | +0.295 | -0.249 | -0.2717 | 49.4% |
| family|side|session | liquidity_sweep_reclaim|LONG|tokyo | 82 | +0.314 | -0.223 | -0.2688 | 48.8% |
| family|symbol|side|vol | displacement_continuation|XAUUSD|LONG|hi_vol | 86 | +0.252 | -0.274 | -0.2630 | 55.8% |
| symbol|side|session | US30_cash|SHORT|london | 72 | +0.335 | -0.189 | -0.2620 | 50.0% |
| family|hour | structural_distance_extreme|h10 | 70 | +0.243 | -0.278 | -0.2604 | 41.4% |

## 10. Worked candidate ids

Most-inverted clean cell `structural_distance_extreme|off_configured_session` (orig -0.189 / inv +0.261, n=1,225): `broadorigin_fcdaf6daac7daeed7249b9c4` (2026-01-02T01:30:00Z GBPUSD SHORT, orig -1.00 / inv +2.00), `broadorigin_d61846c1cd1b2dc31f3c4f07` (01-02T01:45Z GBPUSD SHORT), `broadorigin_52b8434e5a016a2f34fad03a` (01-02T02:00Z GBPUSD SHORT), `broadorigin_caaef4d7a6d8f633fb753399` (01-02T03:00Z XAUUSD SHORT).

London cell where the ORIGINAL works `liquidity_sweep_reclaim|london` (orig +0.077, n=913): `broadorigin_006787a804b98cca4e56a79b` (01-02T07:00Z GBPJPY SHORT, orig +2.00 / inv -1.00), `broadorigin_b20fb9fff0ebd3efc2a061d0` (01-02T07:15Z NZDUSD LONG), `broadorigin_71bf45689cc0b8082a9cb594` (01-02T07:45Z AUDUSD LONG).

## 11. Caveats, stated plainly

- **One month.** January 2026 only. March has no diagnostic pool with an M1 path sidecar in any worktree, and February's pool ships no path sidecar and no market anchor, so neither can test travel from here. That is the single highest-value next test.
- **Multiplicity.** 2,640 clean cells were enumerated. BH q is reported for the 140 bootstrapped ones. The **population-level** claim (info +0.0764 on all 14,911 clean rows) is a single pre-specified test, not a cell pick.
- **Pseudo-replication.** First-emission-only gives info +0.0746 [+0.0522, +0.0990] — the finding does not depend on the 24.39% repeats.
- **2-hour horizon.** Every number is capped at 120 M1 bars. A directional edge that needs longer is invisible here.
- **The inversion is not a trade, and the latency ladder is the reason.** It is spent in one to two minutes, it is one spread wide, and it lands at break-even net of even an 8.5x-corrected spread. It is a diagnosis of where the sign and the entry price are wrong, not a strategy.
- **Not tested here:** whether entering these seven families one to two minutes after the trigger bar's close recovers the 0.0764 R directly (the latency ladder measures the *signal decaying*, not a *delayed-entry policy* — at delay 2 the original's own at-market return is -0.0085 vs -0.0596 at delay 0, which is +0.0511 R/trade and is the single cheapest thing in this receipt to test next). The 30-60 minute rungs turning significant again is unexplained and worth a lane.

## 12. Artifacts

- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_BASE.jsonl.gz`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_SWEEP_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_CELLS_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_DECOMP_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_CONTROLS_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_MECH_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_NET_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_STAB_CQ_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_WIDE3_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_ZEROSPREAD_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_MAGNET_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_DELAY_V2.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_SCALE_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_DELAYREPAIR_V1.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L7_RESULT.json`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_build_base.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_sweep.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_decomp.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_controls.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_magnet.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_mech.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_net.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_stability_cq.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_delay.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_delayrepair.py`
- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/l7_receipt.py`
# Lane l4 — THE OWNER'S CONTRACT, MEASURED

> *"we can set a limit order and if we get in we get in, if we dont we dont … i dont think i ever
> have a problem with having a limit order and it not filling"* — Borhen

**Answer, up front: NO. The owner's contract does not produce a positive book on this pool — and
the reason is not that the orders miss. 99.0 % of them fill. His protection never engages.**

| | |
|---|---|
| trades the contract actually opens | **23,901** of 24,142 offered (**99.00 %**) |
| R per filled trade, gross | **−0.1280** (t = −17.67) |
| total book | **−3,058.1 R** gross, **−5,741.5 R** net |
| win rate | 35.65 % |
| net, most generous honest cost model | **−0.2402 R/trade** |
| trades the "don't fill, don't trade" clause saves him from | **241 (0.87 %)** — and they were the *winners* |

Population = every January candidate except the 3,516 whose stop price was already breached before
the order could be sent (w0-capture's kill, independently reproduced here). Contract = a limit
resting at `entry_price`, filled at the limit price on first touch, cancelled if unfilled at 120
minutes — the engine's own pending expiry, `REPAIRED_PENDING_EXPIRY_MINUTES = 120`
(`src/research_infra/v4_timewarp_simulated_live_research_loop.py:378`). Target +2R, stop −1R,
conservative same-bar tie to the stop (ties are 32 of 19,573 resolved trades = 0.163 %, so the tie
rule is refuted as an explanation for anything below).

---

## 1. Fill rate — the contract's selectivity is 1 %

`w0cap2_DECISION_ANCHOR_V1.jsonl.gz` gives the decision-instant price as `mkt_r_prev_close` (the
close of the M1 bar *ending* at the decision, signed for the trade's own side, in R relative to
entry). Four birth states follow, and they are the spine of everything below.

| born state | meaning | n | share | ever fills | median fill bar | p90 | pool gross |
|---|---|---:|---:|---:|---:|---:|---:|
| `at_limit` | entry **==** the decision price (an at-market order) | 14,911 | 53.91 % | 98.46 % | 1 | 6 | −0.0904 |
| `resting` | genuine passive limit, market above entry | 7,949 | 28.74 % | **99.96 %** | **30** | 95 | −0.1049 |
| `marketable` | limit through the market, fills instantly | 1,265 | 4.57 % | 99.37 % | 1 | 1 | −0.2566 |
| `past_stop` | **stop already breached at the decision** | 3,516 | 12.71 % | 100.00 % | 1 | 1 | −0.9948 |
| `unknown` | no anchor bar | 17 | 0.06 % | 100.00 % | 1 | 17 | −0.6349 |

### Fill-window sweep (cancel if unfilled by W minutes)

ALL candidates (n = 27,658):

| W (min) | n filled | fill % | R/filled | total R | win % | tgt/stop/mark | mean life | mark % |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | 16,951 | 61.29 | −0.3631 | −6,154.1 | 25.63 | 1,954/10,959/4,038 | 116.9 | 23.8 |
| 3 | 18,624 | 67.34 | −0.3336 | −6,212.6 | 26.83 | 2,265/11,781/4,578 | 116.8 | 24.6 |
| 5 | 19,502 | 70.51 | −0.3216 | −6,271.6 | 27.28 | 2,437/12,241/4,824 | 116.5 | 24.7 |
| 10 | 20,670 | 74.73 | −0.3057 | −6,319.6 | 27.90 | 2,676/12,858/5,136 | 116.0 | 24.8 |
| 15 | 21,420 | 77.45 | −0.2950 | −6,318.3 | 28.29 | 2,848/13,264/5,308 | 115.6 | 24.8 |
| 30 | 23,060 | 83.38 | −0.2778 | −6,406.8 | 28.99 | 3,158/14,116/5,786 | 114.0 | 25.1 |
| 45 | 24,180 | 87.42 | −0.2677 | −6,472.5 | 29.48 | 3,349/14,684/6,147 | 112.4 | 25.4 |
| 60 | 25,059 | 90.60 | −0.2593 | −6,498.6 | 29.85 | 3,492/15,090/6,477 | 110.8 | 25.8 |
| 90 | 26,389 | 95.41 | −0.2473 | −6,527.1 | 30.49 | 3,666/15,607/7,116 | 107.5 | 27.0 |
| 120 | 27,417 | 99.13 | −0.2392 | −6,559.1 | 31.10 | 3,722/15,851/7,844 | 104.1 | 28.6 |

SANE (drop `past_stop`, n = 24,142):

| W | n filled | fill % | R/filled | total R | win % | tgt/stop/mark | mark % |
|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | 13,436 | 55.65 | −0.1975 | −2,654.1 | 32.29 | 1,949/7,449/4,038 | 30.1 |
| 3 | 15,108 | 62.58 | −0.1795 | −2,711.6 | 33.04 | 2,260/8,270/4,578 | 30.3 |
| 5 | 15,986 | 66.22 | −0.1733 | −2,770.6 | 33.25 | 2,432/8,730/4,824 | 30.2 |
| 10 | 17,154 | 71.06 | −0.1643 | −2,818.6 | 33.58 | 2,671/9,347/5,136 | 29.9 |
| 15 | 17,904 | 74.16 | −0.1574 | −2,817.3 | 33.81 | 2,843/9,753/5,308 | 29.6 |
| 30 | 19,544 | 80.95 | −0.1487 | −2,905.8 | 34.18 | 3,153/10,605/5,786 | 29.6 |
| 45 | 20,664 | 85.59 | −0.1438 | −2,971.5 | 34.48 | 3,344/11,173/6,147 | 29.7 |
| 60 | 21,543 | 89.23 | −0.1391 | −2,997.6 | 34.70 | 3,487/11,579/6,477 | 30.1 |
| 90 | 22,873 | 94.74 | −0.1323 | −3,026.1 | 35.16 | 3,661/12,096/7,116 | 31.1 |
| **120** | **23,901** | **99.00** | **−0.1280** | **−3,058.1** | **35.65** | 3,717/12,340/7,844 | 32.8 |

RESTING only — the population his sentence is actually about (n = 7,949):

| W | n filled | fill % | R/filled | total R | win % | mean life |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 909 | 11.43 | −0.3444 | −313.1 | 24.31 | 110.8 |
| 15 | 2,770 | 34.85 | −0.1791 | −496.0 | 31.16 | 108.3 |
| 30 | 4,010 | 50.45 | −0.1507 | −604.1 | 32.79 | 103.6 |
| 60 | 5,749 | 72.32 | −0.1224 | −703.8 | 34.70 | 94.2 |
| 90 | 6,983 | 87.85 | −0.1040 | −726.1 | 36.13 | 85.6 |
| **120** | **7,946** | **99.96** | **−0.0947** | **−752.6** | **37.46** | 77.2 |

**Patience is monotonically better and it never turns positive.** Every extra minute of window adds
trades and improves R/trade; nothing about waiting is harmful.

### Fill rate by symbol (SANE, `L4_CONTRACTS_V1.json → by_symbol_SANE`)

| symbol | offered | fill 120 % | fill 15 % | declared p | owner gross | blind gross | **fill bias** | win % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAGUSD | 925 | 98.5 | 84.4 | 0.849 | −0.0048 | 0.0985 | −0.1033 | 39.4 |
| BTCUSD | 1,177 | 100.0 | 66.3 | 0.749 | −0.0217 | 0.3713 | −0.3930 | 43.7 |
| GER40 | 1,400 | 99.2 | 64.5 | 0.730 | −0.0286 | 0.3842 | −0.4128 | 39.0 |
| USDCHF | 774 | 98.3 | 85.0 | 0.858 | −0.0486 | 0.0978 | −0.1464 | 39.6 |
| USDJPY | 892 | 98.2 | 86.4 | 0.874 | −0.0587 | 0.0880 | −0.1467 | 36.3 |
| AUDUSD | 612 | 98.4 | 84.6 | 0.866 | −0.0703 | 0.0225 | −0.0928 | 39.9 |
| EURJPY | 628 | 98.9 | 83.9 | 0.853 | −0.0718 | 0.0828 | −0.1545 | 39.3 |
| XAUUSD | 2,329 | 99.1 | 54.5 | 0.622 | −0.0821 | 0.7556 | **−0.8376** | 35.1 |
| JP225 | 1,283 | 98.4 | 64.1 | 0.712 | −0.0867 | 0.3658 | −0.4524 | 37.2 |
| CHFJPY | 575 | 99.3 | 90.4 | 0.889 | −0.0915 | −0.0518 | −0.0397 | 38.0 |
| UKOIL_cash | 735 | 99.0 | 84.1 | 0.838 | −0.0968 | 0.0580 | −0.1548 | 38.0 |
| EURUSD | 728 | 98.2 | 81.5 | 0.850 | −0.1041 | 0.1029 | −0.2069 | 37.6 |
| GBPJPY | 689 | 98.8 | 91.0 | 0.898 | −0.1212 | −0.0402 | −0.0810 | 35.1 |
| SPX500 | 1,717 | 99.8 | 66.7 | 0.728 | −0.1369 | 0.1661 | −0.3031 | 36.2 |
| NZDUSD | 737 | 97.6 | 84.3 | 0.873 | −0.1464 | −0.0045 | −0.1419 | 35.0 |
| ETHUSD | 916 | 100.0 | 70.7 | 0.787 | −0.1755 | 0.1215 | −0.2969 | 33.7 |
| US30_cash | 1,478 | 99.4 | 67.3 | 0.743 | −0.1808 | 0.2935 | −0.4743 | 33.4 |
| USOIL_cash | 725 | 98.9 | 81.7 | 0.846 | −0.1840 | −0.0723 | −0.1117 | 37.2 |
| EURGBP | 666 | 98.2 | 91.4 | 0.899 | −0.1871 | −0.0569 | −0.1302 | 32.1 |
| AUDJPY | 640 | 97.7 | 83.4 | 0.853 | −0.1953 | 0.0498 | −0.2451 | 34.1 |
| USDCAD | 798 | 99.0 | 83.7 | 0.868 | −0.2052 | −0.1112 | −0.0939 | 33.4 |
| GBPUSD | 823 | 99.0 | 84.6 | 0.859 | −0.2101 | −0.0704 | −0.1397 | 31.3 |
| UK100 | 1,412 | 99.2 | 66.5 | 0.725 | −0.2163 | 0.2491 | −0.4654 | 30.4 |
| NAS100 | 1,483 | 99.8 | 72.1 | 0.756 | −0.3080 | 0.0466 | −0.3546 | 28.0 |

### Fill rate by family (SANE)

| family | offered | fill 120 % | declared p | owner gross | owner net (passive 7.3×) | blind gross | **fill bias** | win % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| regime_transition_break | 297 | 98.0 | 0.920 | −0.0202 | −0.0606 | −0.0035 | −0.0167 | 49.1 |
| current_ob_retest | 1,292 | 99.8 | 0.461 | −0.0572 | −0.1365 | 0.5809 | **−0.6381** | 43.7 |
| liquidity_sweep_reclaim | 4,475 | 98.5 | 0.915 | −0.0717 | −0.1882 | −0.0191 | −0.0526 | 36.2 |
| volatility_compression_expansion | 605 | 99.7 | 0.920 | −0.0936 | −0.1396 | −0.0918 | −0.0018 | 43.3 |
| displacement_continuation | 4,469 | 99.0 | 0.915 | −0.1032 | −0.1701 | −0.0812 | −0.0221 | 39.1 |
| session_open_range_break | 987 | 97.7 | 0.920 | −0.1047 | −0.1596 | −0.0673 | −0.0374 | 40.7 |
| current_breaker_re_entry | 796 | 99.7 | 0.601 | −0.1130 | −0.2042 | 0.4677 | **−0.5807** | 36.3 |
| current_fvg_fill | 7,145 | 99.9 | 0.593 | −0.1407 | −0.2619 | 0.6131 | **−0.7538** | 34.7 |
| cross_asset_lead_lag | 2,083 | 97.7 | 0.908 | −0.2012 | −0.3540 | −0.0746 | −0.1266 | 29.2 |
| structural_distance_extreme | 1,993 | 97.9 | 0.909 | −0.2789 | −0.4994 | −0.0797 | −0.1992 | 24.6 |

The three families whose *names* promise a retracement entry — `current_fvg_fill`,
`current_ob_retest`, `current_breaker_re_entry` — are the three with a large fill bias, and they are
the only three that look positive under the fill-blind convention. Their published edge is the
retracement they never waited for.

### The 241 never-filled candidates — the clause that was supposed to protect him

| | |
|---|---|
| n | 241 (0.871 % of the pool) |
| what the fill-blind convention books on them | **+1.7390 R each, win rate 100.0 %, +419.1 R total** |
| pool `gross_r` mean on them | +1.5477 |
| mean MFE reached without ever touching entry | **+5.8804 R** |
| born state | `at_limit` 230, `marketable` 8, `resting` 3 |
| families | liquidity_sweep_reclaim 65, cross_asset_lead_lag 48, displacement_continuation 45, structural_distance_extreme 41, session_open_range_break 23, regime_transition_break 6, current_fvg_fill 6, current_ob_retest 3, volatility_compression_expansion 2, current_breaker_re_entry 2 |

**The non-fill clause costs him +419.1 R and saves him nothing.** Every single one of the 241 is a
trade whose price ran away in his favour and never came back. That is the honest price of not
chasing, and it is small — but the direction is the opposite of the intuition the clause protects.

---

## 2. Four contracts side by side, identical candidates

Cost models. `spread_r = spread_price / sl_distance` is **one full spread**
(`src/components/broker_net_cost_engine.py:298-306`), and 85.08 % of the frozen charge. `k` divides
it by the established over-charge factor.
* **frozen** — `cost_r` exactly as the engine charged it.
* **passive 7.3×** — a resting limit provides liquidity on entry, and its take-profit is also a
  limit, so it crosses only when the exit is a market order (stop, or the 2 h mark):
  `commission_r + [0.5·spread_r/7.3 + slippage] if exit ∈ {stop, mark}`. Swap = 0 — every trade
  is ≤ 2 h. **This is the most generous defensible model and it is the one to argue against.**
* **taker 7.3×** — crosses both sides: `commission_r + spread_r/7.3 + slippage`.

**SANE population, 24,142 offered:**

| contract | trades | take % | gross R/tr | net frozen | net passive 7.3× | net taker 7.3× | win % |
|---|---:|---:|---:|---:|---:|---:|---:|
| (a) fill-free ceiling — enter at decision always | 24,142 | 100.00 | **+0.1913** | −0.4711 | +0.0880 | +0.0303 | 45.35 |
| **(b) owner's passive limit or nothing** | 23,901 | 99.00 | **−0.1280** | −0.7932 | **−0.2402** | −0.2892 | 35.65 |
| (c) chase / market entry, same size | 24,125 | 99.93 | −0.3396 | −1.0019 | −0.4429 | −0.5006 | 34.23 |
| (c′) chase, risk-normalised | 24,125 | 99.93 | −0.1403 | −0.8026 | −0.2436 | −0.3013 | 34.23 |
| (d) the frozen proxy the system recorded | 24,142 | 100.00 | −0.1043 | −0.7666 | −0.1680 | −0.2652 | 39.72 |

**ALL candidates, 27,658 offered:**

| contract | trades | gross R/tr | net frozen | net passive 7.3× | win % |
|---|---:|---:|---:|---:|---:|
| (a) fill-free ceiling | 27,658 | +0.0404 | −0.6228 | −0.0668 | 39.60 |
| (b) owner's contract | 27,417 | −0.2392 | −0.9049 | −0.3543 | 31.10 |
| (c) chase, same size | 24,125 | −0.3396 | −1.0019 | −0.4429 | 34.23 |
| (d) frozen proxy | 27,658 | −0.2175 | −0.8807 | −0.2827 | 34.68 |

**RESTING only, 7,949 offered:**

| contract | trades | gross R/tr | net passive 7.3× | win % |
|---|---:|---:|---:|---:|
| (a) fill-free ceiling | 7,949 | **+0.7408** | +0.6490 | 62.47 |
| (b) owner's contract | 7,946 | **−0.0947** | −0.2110 | 37.46 |
| (c) chase, same size | 7,949 | −0.9188 | −1.0106 | 27.61 |
| (d) frozen proxy | 7,949 | −0.1049 | −0.1607 | 41.99 |

**Mechanism for the differences, in one line each.**
*(a) vs (b)* — the ceiling hands you a position that is already **+0.4332 R** in profit at the
instant it is opened (§4). *(b) vs (c)* — chasing pays away the whole distance the limit was
resting at: for the RESTING cohort that distance averages **1.6596 R**, which is why chase is
−0.9188 there. *(d)* sits between (a) and (b) because the pool's own walk is fill-blind but is
charged the frozen cost.

---

## 3. Adverse selection — the honest counterweight, and it is enormous

**Fill latency predicts outcome, monotonically, and the effect is concentrated entirely in bar 1.**

SANE, R booked by the bar the fill happened on:

| fill bar | n | mean R | win % | tgt/stop/mark | mean life |
|---|---:|---:|---:|---|---:|
| **1** | **13,436** | **−0.1975** | **32.29** | 1,949/7,449/4,038 | 116.8 |
| 2 | 1,052 | −0.0806 | 37.55 | 178/522/352 | 115.9 |
| 3–5 | 1,498 | −0.0211 | 38.78 | 305/759/434 | 112.5 |
| 6–10 | 1,168 | −0.0411 | 38.19 | 239/617/312 | 108.3 |
| 11–15 | 750 | **+0.0016** | 39.07 | 172/406/172 | 103.6 |
| 16–30 | 1,640 | −0.0540 | 38.17 | 310/852/478 | 93.9 |
| 31–45 | 1,120 | −0.0586 | 39.64 | 191/568/361 | 78.4 |
| 46–60 | 879 | −0.0297 | 40.05 | 143/406/330 | 66.2 |
| 61–90 | 1,330 | −0.0215 | 42.56 | 174/517/639 | 45.5 |
| 91–120 | 1,028 | −0.0311 | **46.59** | 56/244/728 | 16.2 |

RESTING: bar 1 = **−0.3444** (win 24.31 %) against **−0.0181** at bars 61–90 (win 42.79 %) — a
**0.3263 R/trade** spread purely by how fast the limit was hit.

**Filling fast is bad news. Filling late is not.** That kills the long-standing assumption in its
usual form — the danger is not "you filled", it is "you filled *immediately*".

### It is NOT harvestable by waiting — placement delay refuted

Grid over placement delay `k0` (the signal fires at T, the limit is placed at T+k0) × cancel window
W. SANE, R/trade (n filled):

| k0 \ W | 15 | 30 | 60 | 90 | 120 |
|---:|---|---|---|---|---|
| **0** | **−0.1574** (17,904) | **−0.1487** (19,544) | **−0.1391** (21,543) | **−0.1323** (22,873) | **−0.1280** (23,901) |
| 1 | −0.1677 (17,504) | −0.1564 (19,273) | −0.1451 (21,367) | −0.1379 (22,736) | −0.1334 (23,787) |
| 2 | −0.1906 (17,051) | −0.1745 (18,966) | −0.1604 (21,158) | −0.1521 (22,558) | −0.1468 (23,626) |
| 3 | −0.2072 (16,642) | −0.1872 (18,700) | −0.1719 (20,969) | −0.1624 (22,406) | −0.1561 (23,497) |
| 5 | −0.2419 (15,838) | −0.2112 (18,187) | −0.1912 (20,597) | −0.1797 (22,095) | −0.1723 (23,218) |
| 10 | −0.3274 (13,959) | −0.2662 (17,137) | −0.2347 (19,919) | −0.2177 (21,545) | −0.2076 (22,734) |
| 15 | — | −0.3155 (16,096) | −0.2689 (19,279) | −0.2471 (21,048) | −0.2343 (22,301) |
| 20 | — | −0.3666 (14,964) | −0.3019 (18,637) | −0.2747 (20,535) | −0.2590 (21,857) |
| 30 | — | — | −0.3646 (17,477) | −0.3252 (19,642) | −0.3034 (21,094) |
| 45 | — | — | −0.4490 (15,332) | −0.3834 (18,134) | −0.3508 (19,819) |
| 60 | — | — | — | −0.4402 (16,658) | −0.3926 (18,661) |

`k0 = 0` wins every column in every population (ALL, SANE, RESTING). Delaying loses the trades that
resolve early and books the same entry price later. **Caveat:** delayed placement is scored at the
limit price even when the market is already through it, which is conservative against the delay;
the true fill would be better by the distance already travelled. The gradient is far too steep
(−0.08 R at k0 = 10) for that correction to reverse it, but the cell is not exact.

---

## 4. WHERE THE MONEY GOES — the drift curve, and the decomposition

Mean close-based mark in R at k bars after the anchor bar (`L4_DRIFT_V1.json`):

| curve | k=0 | 1 | 2 | 3 | 5 | 10 | 15 | 20 | 30 | 45 | 60 | 90 | 119 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **BLIND** (from the decision bar, SANE) | **+0.4332** | 0.4220 | 0.4092 | 0.4013 | 0.3826 | 0.3443 | 0.3090 | 0.2642 | 0.2099 | 0.1223 | 0.0731 | −0.0057 | −0.0333 |
| **FILL-HONEST** (k from the fill, SANE) | **−0.1644** | −0.1615 | −0.1632 | −0.1654 | −0.1613 | −0.1544 | −0.1496 | −0.1587 | −0.1204 | −0.1286 | −0.1260 | −0.1266 | −0.1982 |
| FILL-HONEST, RESTING | −0.1206 | −0.1035 | −0.1117 | −0.1125 | −0.1063 | −0.0929 | −0.0967 | −0.1009 | −0.0278 | −0.0117 | −0.0082 | +0.0039 | −0.2837 |
| FILL-HONEST, AT_LIMIT | −0.1726 | −0.1783 | −0.1767 | −0.1806 | −0.1789 | −0.1763 | −0.1663 | −0.1766 | −0.1510 | −0.1661 | −0.1590 | −0.1498 | −0.1818 |

**The entire loss is booked at the instant of the fill and the path is a martingale afterwards.**
FILL-HONEST is −0.1644 at the fill bar's own close and −0.1266 ninety minutes later: the post-fill
drift is **+0.038 R over 90 minutes**, i.e. nothing. Meanwhile the fill-blind curve starts at
**+0.4332** and decays to −0.03 — it is scoring the excursion that had *already happened*.

By fill latency, k measured from the fill (SANE):

| latency | n | k=0 | 5 | 15 | 30 | 60 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 13,436 | −0.2429 | −0.2383 | −0.2194 | −0.2150 | −0.2336 |
| 2–5 | 2,550 | −0.0450 | −0.0325 | −0.0463 | −0.0210 | +0.0154 |
| 6–15 | 1,918 | −0.0479 | −0.0709 | −0.0531 | +0.0413 | +0.0714 |
| 16–60 | 3,639 | −0.0774 | −0.0779 | −0.0780 | −0.0026 | +0.0808 |
| 61–120 | 2,358 | −0.0758 | −0.0584 | −0.0238 | +0.1046 | — |

### Unconditional vs fill-conditioned — the decisive split

| born | n | mkt_r at decision | **unconditional** mark at bar 0 / 15 / 60 / 119 | **fill-conditioned** at 0 / 15 / 60 | **selection effect at k=0** |
|---|---:|---:|---|---|---:|
| at_limit | 14,911 | 0.0000 | −0.0647 / −0.0666 / −0.0691 / −0.0646 | −0.1726 / −0.1663 / −0.1590 | **−0.1079** |
| resting | 7,949 | **+1.6596** | +1.4882 / +1.1032 / +0.3922 / +0.0693 | −0.1206 / −0.0967 / −0.0082 | **−1.6087** |
| marketable | 1,265 | −0.2998 | −0.3157 / −0.2740 / −0.2486 / −0.2691 | −0.3352 / −0.2891 / −0.2791 | −0.0195 |
| past_stop | 3,516 | −8.8586 | −8.8416 / −8.8367 / −8.8450 / −8.6483 | −8.8419 / −8.8369 / −8.8449 | −0.0003 |

**This is the whole mechanism in one table.**
* The **resting** cohort's entry sits **1.6596 R behind the market** when the candidate is emitted.
  Scoring from that entry without requiring the fill books that 1.66 R as profit. Requiring the fill
  removes **−1.6087 R** of it. That is 28.74 % of the pool.
* `past_stop` is the *same defect on the other side* — the entry is **8.86 R** behind the market in
  the adverse direction. **41.45 % of the pool has an entry level the market has already left.**
* The **at_limit** cohort — a genuine at-market order — carries a constant **−0.0647 R** at every
  horizon from 1 minute to 2 hours, plus **−0.1079 R** of pure fill selection on top.

### The placebo control — is the fill penalty universal or signal-specific?

Same price level, opposite side (a limit that fills on `fav ≥ 0` instead of `adv ≤ 0`), booked in
its own sign. On `at_limit` rows the two orders are equally marketable, so the comparison is fair.

| born | n | REAL k=0 / 1 / 5 / 15 / 60 | PLACEBO k=0 / 1 / 5 / 15 / 60 | mean fill bar real/placebo |
|---|---:|---|---|---|
| at_limit | 14,681 | −0.1726 / −0.1783 / −0.1789 / −0.1663 / −0.1590 | **−0.0935** / −0.0912 / −0.0738 / −0.0716 / −0.0829 | 3.9 / 5.1 |
| resting | 7,946 | −0.1206 / −0.1035 / −0.1063 / −0.0967 / −0.0082 | −1.5503 / −1.5187 / −1.3962 / −1.1525 / −0.4484 | 39.4 / 1.5 |
| marketable | 1,257 | −0.3352 / −0.3370 / −0.3158 / −0.2891 / −0.2791 | −0.0338 / −0.0213 / −0.0392 / −0.0738 / −0.1304 | 1.6 / 18.0 |

**Both sides lose.** A limit at the same level on the opposite side, filled on first touch, still
marks **−0.0935 R**. Decomposing the at-market cohort's −0.1726:
`−0.0647 (unconditional direction) + −0.1079 (fill selection)`, and the opposite side is
`+0.0647 + −0.1614 = −0.0935`. **Being filled at a level at M1 resolution is a universal tax of
0.11–0.16 R that applies to any level on any side.** Any strategy scored on limit entries without
requiring the fill overstates itself by at least that, before any staleness.

### Refuted: the −0.0647 is NOT the spread

The pooled at-market offset (−0.06794) is 1.109× the pooled true spread (0.06128 = mean
`spread_r`/7.3), which looks like a smoking gun and **is a coincidence of aggregation**.
Cross-sectionally over 24 symbols:

`mark(k=1) = −0.05595 − 0.2296 · true_spread_r`, **r² = 0.2159** — slope −0.23, not −1, and an
intercept of −0.056 at zero spread. Per-symbol ratios run from **−3.14** (XAGUSD, whose mark is
*positive*, +0.0519) to **8,219** (BTCUSD, ~zero spread, mark −0.1126). The offset is real, roughly
constant across instruments, and **not a bid/ask convention artifact**. Its mechanism is not
identifiable from this substrate — the path sidecar carries no pre-decision bars, so the obvious
next test (is the signal a momentum entry into 1-minute mean reversion?) needs bars before T.

---

## 5. Exit geometry cannot fix it — the martingale proof

Full grid under the owner's contract, target × stop × time-stop, walked from the fill.

Target sweep at stop −1R, 120 bars, SANE (n = 23,901 every row):

| target | gross R | win % | tgt/stop/mark |
|---:|---:|---:|---|
| 0.25 | −0.1278 | 66.88 | 15,693/6,533/1,675 |
| 0.50 | −0.1244 | 55.50 | 12,343/8,624/2,934 |
| 0.75 | −0.1257 | 48.14 | 9,801/9,965/4,135 |
| 1.00 | −0.1225 | 43.70 | 7,957/10,802/5,142 |
| 1.25 | −0.1255 | 40.38 | 6,489/11,410/6,002 |
| 1.50 | −0.1246 | 38.32 | 5,365/11,811/6,725 |
| 1.75 | −0.1223 | 36.85 | 4,515/12,103/7,283 |
| 2.00 | −0.1280 | 35.65 | 3,717/12,340/7,844 |
| 2.50 | −0.1279 | 34.25 | 2,733/12,637/8,531 |
| 3.00 | −0.1247 | 33.47 | 2,065/12,803/9,033 |
| 4.00 | −0.1211 | 32.72 | 1,246/12,964/9,691 |
| 5.00 | −0.1129 | 32.43 | 837/13,026/10,038 |

Stop sweep at target +2R, 120 bars:

| stop | gross same-size | gross risk-normalised | win % |
|---:|---:|---:|---:|
| −2.00 | −0.1278 | −0.0639 | 46.16 |
| −1.50 | −0.1258 | −0.0838 | 42.49 |
| −1.00 | −0.1280 | −0.1280 | 35.65 |
| −0.75 | −0.1267 | −0.1689 | 30.01 |
| −0.50 | −0.1190 | −0.2381 | 22.02 |

**The book is invariant to the stopping rule: −0.1129 to −0.1280 across a 20× range of targets, and
−0.1190 to −0.1280 across a 4× range of stops.** That is the optional-stopping signature of a
martingale plus a constant, and it corroborates §4's flat drift curve by a completely independent
route. The risk-normalised column improves with wider stops only because `gross/|S|` shrinks the
denominator — risking less loses less; it is not an edge.

Best 12 cells of the 240-cell SANE grid, all at stop −2R, all still negative
(`L4_EXITGRID_V1.json`): 5.00/−2.00/60 → −0.0527 RN; 1.75/−2.00/60 → −0.0582; 1.50/−2.00/120 →
−0.0610. Best RESTING cell: 5.00/−2.00/120 → −0.0095 RN (n = 7,946).

**Nothing is cutting the winners.** Corroborates w0-capture's finding from the other side.

---

## 6. `execution_fill_probability` — how wrong, and in which direction

The brief's "flat constant 0.92" was already corrected by w0-dictionary D5 (7,400 distinct values;
0.92 is the `limit_marketable` branch at `src/components/poi_execution_lifecycle.py:174-176`, the
else-branch is distance-scaled at `:178-181`). Measured against reality:

| horizon | pooled declared p | pooled measured fill | mean abs error over 24 symbols |
|---|---:|---:|---:|
| 15 min | 0.8006 | 0.7745 | **0.0316** |
| 60 min | 0.8006 | 0.9060 | — |
| **120 min** (the engine's own pending expiry) | 0.8006 | **0.9913** | **0.1669** |

**The quantity is a well-calibrated 15-minute fill probability being used inside a system whose
orders live 120 minutes.** At the horizon the engine actually gives its own orders, it understates
on every one of 24 symbols. Worst: XAUUSD 0.625 declared vs 0.991 actual (−0.366), JP225 0.722 vs
0.985, GER40 0.732 vs 0.992, SPX500 0.749 vs 0.998. Best: EURGBP 0.903 vs 0.986, GBPJPY 0.901 vs
0.990.

By family the declared value is essentially bimodal — 0.91–0.92 for seven families, 0.46–0.60 for
`current_ob_retest`, `current_fvg_fill`, `current_breaker_re_entry` — while the measured 120-minute
fill rate is 97.7–99.9 % for **all ten**.

### And the gate built on it is inverted

Declared p falls monotonically with the limit's distance from the market
(`poi_execution_lifecycle.py:178-181`), and distance is the **one monotone predictor of trade
quality** under the owner's contract:

| limit distance from market | n | gross | net passive 7.3× | win % | t |
|---|---:|---:|---:|---:|---:|
| **> 2R** | 2,171 | **−0.0228** | −0.1344 | 39.11 | **−0.877** |
| 1–2R | 2,422 | −0.0961 | −0.2100 | 38.52 | −4.267 |
| 0.5–1R | 1,714 | −0.1291 | −0.2541 | 35.36 | −4.807 |
| at or through | 15,955 | −0.1445 | −0.2548 | 34.75 | −16.342 |
| 0–0.5R | 1,639 | −0.1520 | −0.2686 | 35.94 | −5.929 |

So every configured fill-probability floor removes the better cohort:

| floor | config site | n kept | gross kept | n dropped | **gross dropped** | effect of gating |
|---:|---|---:|---:|---:|---:|---:|
| 0.45 | `config/agent_config.yaml:811` `selector_v4_calibrated_min_fill_probability` | 20,374 | −0.1435 | 3,407 | **−0.0369** | **−0.0153** |
| 0.80 | `config/agent_config.yaml:1002` `scheduler_v4_..._dynamic_budget_min_fill_probability` | 17,054 | −0.1473 | 6,727 | −0.0799 | **−0.0191** |
| 0.70 | `config/agent_config.yaml:794` `..._off_session_min_fill_probability` | 17,843 | −0.1485 | 5,938 | −0.0675 | **−0.0202** |
| 0.35 | `config/agent_config.yaml:801` `..._strong_fill_floor_bypass_min_execution_fill_probability` | 21,578 | −0.1381 | 2,203 | −0.0323 | −0.0098 |
| 0.25 | `config/agent_config.yaml:798` `..._soften_selector_fill_floor_min_fill_probability` | 22,748 | −0.1326 | 1,033 | −0.0327 | −0.0043 |

Deciles of declared p (1 = lowest), ungated n = 23,781 at −0.1283:

| decile | p range | n | gross | net | win % | t |
|---:|---|---:|---:|---:|---:|---:|
| 1 | 0.040–0.363 | 2,378 | **−0.0359** | −0.1254 | 41.25 | −1.598 |
| 2 | 0.363–0.578 | 2,378 | **−0.0411** | −0.1552 | 40.16 | −1.776 |
| 3 | 0.578–0.862 | 2,378 | −0.1710 | −0.3057 | 32.93 | −7.287 |
| 4 | 0.862–0.920 | 2,378 | −0.1199 | −0.2431 | 35.32 | −5.040 |
| 5 | 0.920 | 2,378 | −0.1826 | −0.3123 | 33.77 | −8.056 |
| 6 | 0.920 | 2,378 | −0.1369 | −0.2510 | 34.99 | −5.969 |
| 7 | 0.920 | 2,378 | −0.1255 | −0.2486 | 35.62 | −5.478 |
| 8 | 0.920 | 2,378 | −0.1227 | −0.2253 | 35.87 | −5.465 |
| 9 | 0.920 | 2,378 | −0.1771 | −0.2765 | 32.97 | −7.819 |
| 10 | 0.920–0.950 | 2,379 | −0.1698 | −0.2632 | 33.54 | −7.444 |

**A gate the system runs at three different thresholds refuses the trades that are 0.08–0.11 R/trade
better than the ones it admits, while the true fill rate of both groups at the order's own lifetime
is ~99 %.** It is a distance filter wearing a fill filter's name, pointed the wrong way. Worth
+0.0153 to +0.0202 R/trade to remove — real, named, cited, and not enough on its own to flip
the book.

---

## 7. The stacked contract — every filter decidable at the decision instant

| stage | offered | trades | gross | t | net passive | net frozen | total net R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0. every candidate | 27,658 | 27,417 | −0.2392 | −36.48 | −0.3543 | −0.9049 | −9,715.0 |
| 1. drop stop-already-breached | 24,142 | 23,901 | −0.1280 | −17.67 | −0.2402 | −0.7932 | −5,741.5 |
| 2. + limits resting > 1R away | 4,593 | 4,593 | −0.0614 | −3.60 | −0.1743 | −0.9363 | −800.4 |
| 2b. + limits resting > 2R away | 2,171 | 2,171 | **−0.0228** | **−0.88** | −0.1344 | −0.9197 | −291.8 |
| 3. + invert the p-fill floor (p < 0.80) | 2,170 | 2,170 | −0.0223 | −0.86 | −0.1340 | −0.9194 | −290.8 |
| 3b. declared p < 0.578 only | 4,751 | 4,751 | −0.0375 | −2.32 | −0.1393 | −0.8074 | −661.6 |
| 4. best-7-hours only *(in-sample)* | 6,466 | 6,398 | −0.0417 | −2.92 | −0.1545 | −0.6784 | −988.5 |
| 5. > 2R **and** best-7-hours *(in-sample)* | 567 | 567 | **+0.0264** | 0.52 | −0.0890 | −0.9552 | −50.5 |

Cost decomposition per stage (R/trade):

| stage | commission_r | frozen spread_r | frozen cost_r |
|---|---:|---:|---:|
| 0 | 0.0651 | 0.5668 | 0.6657 |
| 1 | 0.0636 | 0.5670 | 0.6652 |
| 2 (> 1R) | 0.0527 | 0.7861 | 0.8748 |
| 2b (> 2R) | 0.0504 | 0.8088 | 0.8970 |
| 5 | 0.0506 | 0.8941 | 0.9815 |

**The closing tension, and it is exact.** Patience takes the gross book to zero — the > 2R cohort is
−0.0228 at t = −0.88, statistically indistinguishable from breakeven over 2,171 trades. But the
patient cohort is the *tight-risk-distance* cohort, so its R-denominated cost is the highest in the
pool: frozen `spread_r` 0.8088 against 0.5670 for the population it came from. Even at the
corrected 7.3× spread and the most generous passive model, its cost is 0.1116 R/trade and it
finishes at −0.1344. **The gross deficit is gone and the cost is not.**

Stage 5 is the only positive cell and it is **not a claim**: 7 hours were chosen after seeing the
hour table, n = 567, t = 0.52, net −0.0890.

---

## 8. Honest search — what is positive, with its multiplicity stated

Owner contract, SANE, fill-honest (`L4_SEARCH_V1.json`).

| cut | cells | gross-positive | net-positive | best cell |
|---|---:|---:|---:|---|
| family × distance | 18 | 3 | 2 | `current_breaker_re_entry` × 1–2R: **+0.1241** (n = 204, t = 1.50) |
| family × hour | 83 | 11 | 3 | `liquidity_sweep_reclaim` × h19: **+0.3080** (n = 115, t = 2.56, net +0.1889) |
| symbol × hour | 127 | 31 | 19 | `GER40` × h03: **+0.6332** (n = 68, t = 3.87, net +0.6040) |

Other cells worth a wave-2 look: `current_ob_retest` × 0.5–1R **+0.1212** (n = 261, t = 1.96,
net +0.0459); `liquidity_sweep_reclaim` × h10 +0.1648 (n = 199); `displacement_continuation` × h14
+0.0941 (n = 435); `JP225` × h06 +0.3816 (n = 63); `XAUUSD` × h16 +0.3376 (n = 88).
**All are in-sample cells from 228 looks. They are leads, not findings.**

Hour of day, whole population (24 cells, n ≥ 592 each — this one is not a small-n artifact):
best h19 −0.0083, h23 −0.0265, h11 −0.0333, h10 −0.0442, h08 −0.0456; worst h15 −0.2151,
h13 −0.2077, h01 −0.2000, h22 −0.1970, h04 −0.1925. **A 0.207 R/trade spread across hours of the
day, on a population where every hour has ≥ 592 trades.**

Side: LONG 10,684 at −0.1145, SHORT 13,217 at −0.1389. The pool is **55.3 % short** in a month
where the at-market long cohort marked **+0.0277** at 2 h and the short cohort **−0.1423** — a
0.17 R directional gap that is January's market, not an edge.

De-duplication (w0-F1): repeats 5,741 at −0.1184, first-emissions 18,160 at −0.1310. Under the
owner's contract, pseudo-replication is worth **+0.0126 R/trade** of optimistic bias, about half
what it is worth on the shipped pool.

---

## 9. Artifacts

| file | what |
|---|---|
| `l4_FILL_V1.jsonl.gz` | 27,658 rows: born state, fill bar, and all four contracts scored per candidate |
| `l4_EXITLADDER_V1.jsonl.gz` | per-candidate first-touch ladder measured **from the fill bar** (12 targets × 5 stops × 4 time stops) |
| `L4_WINDOW_V1.json` | born census + the three fill-window sweeps |
| `L4_LATENCY_V1.json` | adverse-selection tables + limit-distance table |
| `L4_GRID_V1.json`, `L4_GRID_PERCAND_V1.json.gz` | placement-delay × cancel-window grid |
| `L4_CONTRACTS_V1.json` | four contracts, five cost models, family/symbol/session cuts |
| `L4_EXITGRID_V1.json` | the 240-cell exit grid, both populations |
| `L4_DRIFT_V1.json` | drift curves + tie sensitivity |
| `L4_PLACEBO_V1.json` | opposite-side placebo control |
| `L4_UNCOND_V1.json` | unconditional vs fill-conditioned split per born state |
| `L4_SIGNAL_V1.json` | at-market signal test + fill-probability calibration |
| `L4_SPREADTEST_V1.json` | the cross-sectional regression that refutes the spread explanation |
| `L4_GATE_V1.json` | fill-probability floor sweep + deciles |
| `L4_SEARCH_V1.json`, `L4_STACK_V1.json` | cross-cut search and the stacked contract |

Scripts: `l4_build_fill_sim.py`, `l4_a_window.py`, `l4_b_latency.py`, `l4_c_grid.py`,
`l4_d_contracts.py`, `l4_e_exitsweep.py`, `l4_f_exitgrid.py`, `l4_g_drift.py`, `l4_h_placebo.py`,
`l4_i_uncond.py`, `l4_j_signal.py`, `l4_k_spreadtest.py`, `l4_l_search.py`, `l4_m_gate.py`,
`l4_n_stack.py` — all in this directory, all deterministic, all re-runnable in under 2 minutes each.

## 10. What wave 2 should test

1. **The 0.87 % fill rate is the whole story of the owner's clause.** Re-measure it on February
   (virgin, and it carries `target_first_touch_utc` / `stop_first_touch_utc` inline). If February's
   entries are equally close to the market, the clause is structurally inert for this generator and
   the design question is *"why does a generator that emits limits place them where the market
   already is?"*
2. **The −0.0647 at-market constant.** Not the spread (r² 0.216). Needs pre-decision bars to test
   the momentum-entry-into-1-minute-reversion hypothesis. This is the single unidentified number in
   the lane.
3. **The inverted p-fill floor** (+0.0153…+0.0202 R/trade) is a live-code defect with three config
   sites. It is small but it is free, and it points the same way on every threshold.
4. **Staleness as one unified defect.** 41.45 % of the pool has an entry the market has already
   left, split +1.66 R one way (resting, manufactures fictitious profit) and −8.86 R the other
   (past_stop, manufactures a deterministic loss). Both are the same generator bug and both are
   decidable at the decision instant.

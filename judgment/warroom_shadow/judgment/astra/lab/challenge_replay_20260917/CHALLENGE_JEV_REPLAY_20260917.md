# Challenge Jev Replay — 2026-09-17

Shadow/log only. Login **0**, magic **0**, ns `operator`.
No place / remint / flatten. Model: jev via TypeSafe System One.

## Universe

- Tickets found: **45** (MT5 history + swarm/close enrichers)
- Queried complete: **45** (admit_then + admit_now + close_label)
- Wins (broker_net>0): **6** / Losses: **39**
- Actual book PnL (queried): **-4295.92** USD

## admit_then confusion vs profitable (R/net>0)

| | Keep (admit) | Block (abstain/hard_refuse) |
|---|---:|---:|
| Win | 4 | 2 |
| Loss | 9 | 30 |

## admit_now confusion vs profitable

| | Keep (admit) | Block |
|---|---:|---:|
| Win | 6 | 0 |
| Loss | 16 | 23 |

Toxic-family tickets (US30/hard-off tags): 24; admit_now hard_refuse: **22**

## Close-label exit_class accuracy

- Correct 39/45 = **0.8667**

## toxic_remint (close-label Noul)

- Mean on losers: **0.5292**
- Mean on winners: **0.455**

## Counterfactual gates (admit + confidence)

| Gate | n_kept | kept PnL | actual PnL | delta | blocked losses | blocked wins |
|---|---:|---:|---:|---:|---:|---:|
| admit_then conf≥0.55 | 2 | 100.53 | -4295.92 | **4396.45** | 38 (-6054.28) | 5 (1657.83) |
| admit_then conf≥0.70 | 2 | 100.53 | -4295.92 | **4396.45** | 38 (-6054.28) | 5 (1657.83) |
| admit_now conf≥0.55 | 21 | -402.67 | -4295.92 | **3893.25** | 24 (-3893.25) | 0 (0) |
| admit_now conf≥0.70 | 17 | -345.37 | -4295.92 | **3950.55** | 26 (-4200.87) | 2 (250.32) |

## Per-ticket snapshot

| ticket | symbol | tag | net | R | exit | admit_then | conf | admit_now | conf | close_exit | toxic_remint |
|---:|---|---|---:|---:|---|---|---:|---|---:|---|---:|
| 291072108 | XAUUSD | dsp_walked_hi | -143.56 | -0.9662 | orig_stop | hard_refuse | 0.32 | admit | 0.8 | orig_stop | 0.52 |
| 291076386 | EURUSD | xa_huge_20_ex | -174.0 | -1.16 | orig_stop | hard_refuse | 0.44 | hard_refuse | 0.99 | orig_stop | 0.54 |
| 291087142 | EURGBP | vss_fxcross_l | -180.11 | -1.2021 | orig_stop | admit | 0.78 | admit | 0.96 | orig_stop | 0.5 |
| 291096187 | XAUUSD | dsp_walked_hi | -155.14 | -1.0585 | orig_stop | admit | 0.24 | admit | 0.76 | orig_stop | 0.54 |
| 291113462 | US30.cash | dsp_first_cra | -154.17 | -1.03 | orig_stop | hard_refuse | 0.37 | hard_refuse | 1.0 | orig_stop | 0.58 |
| 291120917 | UK100.cash | idxrev | -151.18 | -1.0095 | orig_stop | admit | 0.39 | hard_refuse | 1.0 | orig_stop | 0.5 |
| 291124471 | US30.cash | dsp_bleed_acc | -146.95 | -0.9805 | orig_stop | hard_refuse | 0.52 | hard_refuse | 0.99 | orig_stop | 0.55 |
| 291139109 | US30.cash | dsp_bleed_acc | -154.31 | -1.0312 | orig_stop | hard_refuse | 0.48 | hard_refuse | 0.99 | orig_stop | 0.54 |
| 291167802 | US30.cash | dsp_bleed_acc | -152.94 | -1.0227 | orig_stop | hard_refuse | 0.65 | hard_refuse | 0.99 | orig_stop | 0.52 |
| 291186653 | US30.cash | dsp_bleed_acc | -145.91 | -0.9736 | orig_stop | hard_refuse | 0.37 | hard_refuse | 0.99 | orig_stop | 0.54 |
| 291210052 | XAUUSD | dsp_two_bar_t | -151.53 | -1.0201 | orig_stop | hard_refuse | 0.36 | admit | 0.82 | orig_stop | 0.48 |
| 291234829 | XAUUSD | dsp_three_bar | -143.92 | -1.0024 | orig_stop | hard_refuse | 0.15 | admit | 0.89 | orig_stop | 0.52 |
| 291377397 | US30.cash | dsp_isolated_ | -163.38 | -1.09 | orig_stop | hard_refuse | 0.26 | hard_refuse | 1.0 | orig_stop | 0.57 |
| 291383082 | XAUUSD | dsp_two_bar_t | -162.7 | -1.1085 | orig_stop | hard_refuse | 0.16 | admit | 0.64 | orig_stop | 0.52 |
| 291392252 | XAUUSD | dsp_high_vol_ | -147.0 | -0.98 | orig_stop | hard_refuse | 0.42 | admit | 0.8 | orig_stop | 0.54 |
| 291402598 | US30.cash | dsp_isolated_ | -153.8 | -1.03 | orig_stop | hard_refuse | 0.41 | hard_refuse | 1.0 | orig_stop | 0.61 |
| 291417478 | UK100.cash | idxrev | -150.65 | -1.0 | orig_stop | admit | 0.2 | hard_refuse | 1.0 | orig_stop | 0.48 |
| 291420292 | ETHUSD | orb_crypto_lo | -204.88 | -1.14 | orig_stop | admit | 0.49 | hard_refuse | 0.99 | orig_stop | 0.5 |
| 291426696 | US30.cash | dsp_rejection | -177.51 | -1.18 | orig_stop | hard_refuse | 0.32 | hard_refuse | 0.99 | orig_stop | 0.57 |
| 291439454 | US30.cash | dsp_walked_hi | -165.63 | -1.1 | orig_stop | hard_refuse | 0.48 | hard_refuse | 0.99 | orig_stop | 0.53 |
| 291455851 | US30.cash | dsp_shakeout_ | -157.09 | -1.05 | orig_stop | hard_refuse | 0.15 | hard_refuse | 1.0 | orig_stop | 0.57 |
| 291466548 | US30.cash | dsp_wide_down | -164.36 | -1.1 | orig_stop | hard_refuse | 0.56 | hard_refuse | 1.0 | orig_stop | 0.55 |
| 291480724 | US30.cash | dsp_bleed_acc | -150.35 | -1.0 | orig_stop | hard_refuse | 0.52 | hard_refuse | 1.0 | orig_stop | 0.54 |
| 291486315 | XAUUSD | dsp_descendin | -154.7 | -1.03 | orig_stop | hard_refuse | 0.27 | admit | 0.81 | orig_stop | 0.47 |
| 291549869 | XAUUSD | dsp_bleed_acc | -144.92 | -0.97 | orig_stop | hard_refuse | 0.59 | admit | 0.66 | orig_stop | 0.54 |
| 291549870 | US30.cash | dsp_bleed_acc | -149.55 | -1.0 | orig_stop | hard_refuse | 0.61 | hard_refuse | 1.0 | orig_stop | 0.58 |
| 291589055 | GBPUSD | xa_huge_same_ | -174.08 | -1.16 | orig_stop | hard_refuse | 0.57 | hard_refuse | 0.99 | orig_stop | 0.53 |
| 291589065 | US30.cash | xa_huge_same_ | -156.79 | -1.05 | orig_stop | hard_refuse | 0.25 | hard_refuse | 1.0 | orig_stop | 0.52 |
| 291713652 | XAUUSD | dsp_bleed_acc | -170.7 | -1.14 | orig_stop | hard_refuse | 0.35 | admit | 0.44 | orig_stop | 0.56 |
| 291758207 | XAUUSD | dsp_three_bar | -195.32 | -1.3 | orig_stop | hard_refuse | 0.32 | admit | 0.85 | orig_stop | 0.54 |
| 291778371 | XAUUSD | dsp_three_fre | -151.21 | -1.01 | orig_stop | hard_refuse | 0.5 | admit | 0.78 | orig_stop | 0.49 |
| 291789105 | EURUSD | xa_huge_same_ | -186.0 | -1.24 | orig_stop | hard_refuse | 0.51 | hard_refuse | 0.99 | orig_stop | 0.5 |
| 291794419 | XAUUSD | dsp_spring_cl | 453.14 | 3.02 | time_stop | admit | 0.21 | admit | 0.9 | manual_other | 0.46 |
| 291816474 | EURGBP | vss_fxcross_l | 280.64 | 1.87 | orig_tp | admit | 0.73 | admit | 0.96 | tp | 0.43 |
| 291821945 | BTCUSD | orb_crypto_lo | -170.98 | -1.14 | orig_stop | hard_refuse | 0.33 | hard_refuse | 1.0 | orig_stop | 0.49 |
| 291827091 | GBPUSD | xa_huge_same_ | -177.0 | -1.18 | orig_stop | hard_refuse | 0.38 | hard_refuse | 0.99 | orig_stop | 0.49 |
| 292427064 | XAUUSD | dsp_walked_hi | 25.38 | 0.1692 | time_stop | hard_refuse | 0.22 | admit | 0.68 | manual_other | 0.44 |
| 292513484 | XAUUSD | dsp_rejection_wick_then_through | -157.78 | -1.05 | orig_stop | admit | 0.37 | admit | 0.75 | orig_stop | 0.52 |
| 292524534 | XAUUSD | dsp_three_fresh_lower_lows | -150.93 | -1.01 | orig_stop | hard_refuse | 0.17 | admit | 0.85 | orig_stop | 0.52 |
| 292667008 | XAUUSD | dsp_three_fresh_lower_lows | 505.28 | 3.41 | time_stop | hard_refuse | 0.27 | admit | 0.83 | manual_other | 0.45 |
| 292876275 | XAUUSD | dsp_three_bar_squeeze_into_high | -151.38 | -1.01 | orig_stop | admit | 0.22 | admit | 0.85 | orig_stop | 0.55 |
| 292885676 | XAUUSD | dsp_expanding_two_bar_run_tokyo | 449.09 | 2.99 | time_stop | admit | 0.36 | admit | 0.87 | manual_other | 0.44 |
| 293024386 | XAUUSD | dsp_three_fresh_lower_lows | -150.94 | -1.01 | orig_stop | admit | 0.21 | admit | 0.84 | orig_stop | 0.52 |
| 293128383 | XAUUSD | sub_mid_dn_revert | -141.04 | -0.94 | orig_stop | admit | 0.23 | hard_refuse | 0.47 | orig_stop | 0.51 |
| 293207416 | XAUUSD | dsp_wide_down_then_micro_bounce_then_through | 224.94 | 1.5 | time_stop | admit | 0.29 | admit | 0.57 | manual_other | 0.51 |

## Takeaway

YES — admit_then@0.55 gate improves PnL vs actual on this book (blocks more loss $ than win $).

Mean call latency: 161.8052 ms. Rows: `/workspace/gtos/research/jev/lab/challenge_replay_rows.jsonl`.

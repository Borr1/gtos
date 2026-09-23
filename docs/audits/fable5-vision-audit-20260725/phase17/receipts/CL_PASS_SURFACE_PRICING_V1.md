# CL pass-surface pricing — firm-true account deltas

Tool-emitted from `docs/audits/fable5-vision-audit-20260725/phase17/receipts/cl_pass_surface.py` at **20,000 paths per MC cell**. This artifact arms nothing. The direct approved set is **empty on both accounts**.

The payout-clock column is the inherited MC's **median calendar days among passing paths**, not an unconditional expectation. A lower number paired with a lower `p_pass` is survivorship bias, not a faster book.

March 2026, its label shoulders, and the live-forward stream are outcome-unread. The estate reader rejected {'label_or_decision_intersects_protected_month': 587, 'outside_train_val': 1707} before outcome access; all protected-access counters are zero.

## FTMO

Per-account survivor tiers read from the artifact:

- `fx_jpy`: `fx_jpy` = `MEASURED_LIVE_CARRY`
- `fx_jpy_ny`: `fx_jpy_ny` = `CARRY_CONDITIONAL_LIVE_SUPPORTED`
- `fx_jpy_pair`: `fx_jpy` = `MEASURED_LIVE_CARRY`, `fx_jpy_ny` = `CARRY_CONDITIONAL_LIVE_SUPPORTED`
- `metals_core_downweighted`: `metals_core` = `UNCONDITIONAL`
- `metals_softband`: `metals_softband` = `CARRY_CONDITIONAL`
- `mx_btcusd_target5`: `mx_btcusd_d1_donchian_20_breakout` = `NO_W7_SURVIVOR_ROW`
- `vp_euidx_pocgrav`: `vp_euidx_pocgrav` = `CARRY_CONDITIONAL`

### ACTUAL_REALIZED_HOLD — OUT_OF_WINDOW_PRE_2025

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.7791 | 0.6499 | — | 0.4196 | — | 449 | — | complete | baseline |
| `fx_jpy` | 0.7488 | 0.6089 | **-0.0410** | 0.4001 | -0.0195 | 418 | -31 | complete | DO_NOT_ARM |
| `fx_jpy_ny` | 0.7229 | 0.5740 | **-0.0759** | 0.3488 | -0.0708 | 430 | -19 | complete | DO_NOT_ARM |
| `fx_jpy_pair` | 0.6902 | 0.5378 | **-0.1121** | 0.3322 | -0.0874 | 403 | -46 | complete | DO_NOT_ARM |
| `metals_core_downweighted` | 0.6812 | 0.5301 | **-0.1198** | 0.4182 | -0.0014 | 319 | -130 | complete | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.8054 | 0.6948 | +0.0449 | 0.6094 | +0.1898 | 325 | -124 | complete | DO_NOT_ARM |
| `mx_btcusd_target5` | — | — | — | — | — | — | — | ALREADY_IN_BASELINE | ALREADY_ARMED |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

### ACTUAL_REALIZED_HOLD — IN_WINDOW_USED_ONCE_2025_PLUS

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.8494 | 0.7545 | — | 2.5355 | — | 92 | — | complete | baseline |
| `fx_jpy` | 0.6421 | 0.4822 | **-0.2723** | 1.5594 | -0.9760 | 65 | -27 | complete | DO_NOT_ARM |
| `fx_jpy_ny` | 0.7479 | 0.6059 | **-0.1486** | 2.0948 | -0.4406 | 78 | -14 | complete | DO_NOT_ARM |
| `fx_jpy_pair` | 0.5808 | 0.4163 | **-0.3382** | 1.2405 | -1.2950 | 54 | -38 | complete | DO_NOT_ARM |
| `metals_core_downweighted` | 0.8754 | 0.7873 | +0.0328 | 2.8197 | +0.2842 | 88 | -4 | complete | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.8372 | 0.7325 | **-0.0221** | 2.5290 | -0.0064 | 85 | -7 | complete | DO_NOT_ARM |
| `mx_btcusd_target5` | — | — | — | — | — | — | — | ALREADY_IN_BASELINE | ALREADY_ARMED |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

### W7_MAX_CARRY_STRESS — OUT_OF_WINDOW_PRE_2025

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.4400 | 0.2611 | — | -0.0407 | — | 414 | — | complete | baseline |
| `fx_jpy` | 0.2978 | 0.1452 | **-0.1159** | -0.2834 | -0.2427 | 344 | -70 | complete | DO_NOT_ARM |
| `fx_jpy_ny` | 0.3103 | 0.1525 | **-0.1086** | -0.2547 | -0.2140 | 365 | -49 | complete | DO_NOT_ARM |
| `fx_jpy_pair` | 0.1958 | 0.0767 | **-0.1844** | -0.5503 | -0.5096 | 262 | -152 | complete | DO_NOT_ARM |
| `metals_core_downweighted` | 0.3024 | 0.1483 | **-0.1129** | -0.3722 | -0.3315 | 254 | -160 | complete | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.4411 | 0.2713 | +0.0101 | -0.0685 | -0.0278 | 307 | -107 | complete | DO_NOT_ARM |
| `mx_btcusd_target5` | — | — | — | — | — | — | — | ALREADY_IN_BASELINE | ALREADY_ARMED |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

### W7_MAX_CARRY_STRESS — IN_WINDOW_USED_ONCE_2025_PLUS

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.6927 | 0.5282 | — | 1.4203 | — | 92 | — | complete | baseline |
| `fx_jpy` | 0.3075 | 0.1606 | **-0.3675** | -1.8350 | -3.2553 | 42 | -50 | complete | DO_NOT_ARM |
| `fx_jpy_ny` | 0.4340 | 0.2478 | **-0.2803** | -0.3455 | -1.7659 | 67 | -25 | complete | DO_NOT_ARM |
| `fx_jpy_pair` | 0.2231 | 0.1008 | **-0.4274** | -3.8522 | -5.2725 | 29 | -63 | complete | DO_NOT_ARM |
| `metals_core_downweighted` | 0.6619 | 0.4866 | **-0.0415** | 1.2626 | -0.1578 | 88 | -4 | complete | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.6077 | 0.4276 | **-0.1005** | 0.8956 | -0.5247 | 88 | -4 | complete | DO_NOT_ARM |
| `mx_btcusd_target5` | — | — | — | — | — | — | — | ALREADY_IN_BASELINE | ALREADY_ARMED |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

## redacted_account

Per-account survivor tiers read from the artifact:

- `fx_jpy`: `fx_jpy` = `MEASURED_LIVE_CARRY`
- `fx_jpy_ny`: `fx_jpy_ny` = `CARRY_CONDITIONAL_LIVE_SUPPORTED`
- `fx_jpy_pair`: `fx_jpy` = `MEASURED_LIVE_CARRY`, `fx_jpy_ny` = `CARRY_CONDITIONAL_LIVE_SUPPORTED`
- `metals_core_downweighted`: `metals_core` = `CARRY_CONDITIONAL`
- `metals_softband`: `metals_softband` = `CARRY_CONDITIONAL`
- `mx_btcusd_target5`: `mx_btcusd_d1_donchian_20_breakout` = `NO_W7_SURVIVOR_ROW`
- `vp_euidx_pocgrav`: `vp_euidx_pocgrav` = `UNCONDITIONAL`

### ACTUAL_REALIZED_HOLD — OUT_OF_WINDOW_PRE_2025

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.4299 | 0.2376 | — | -0.2935 | — | 390 | — | PARTIAL | baseline |
| `fx_jpy` | 0.4142 | 0.2218 | -0.0158 | -0.3291 | -0.0356 | 365 | -25 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_ny` | 0.3812 | 0.1946 | **-0.0430** | -0.3690 | -0.0755 | 370 | -20 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_pair` | 0.3488 | 0.1671 | **-0.0704** | -0.4376 | -0.1442 | 334 | -56 | PARTIAL | DO_NOT_ARM |
| `metals_core_downweighted` | 0.3621 | 0.1779 | **-0.0596** | -0.4116 | -0.1181 | 296 | -94 | PARTIAL | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.4973 | 0.3049 | +0.0673 | -0.1939 | +0.0996 | 339 | -51 | PARTIAL | DO_NOT_ARM |
| `mx_btcusd_target5` | 0.4355 | 0.2414 | +0.0039 | -0.2666 | +0.0269 | 339 | -51 | PARTIAL | DO_NOT_ARM |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

### ACTUAL_REALIZED_HOLD — IN_WINDOW_USED_ONCE_2025_PLUS

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.9380 | 0.8941 | — | 1.7116 | — | 146 | — | PARTIAL | baseline |
| `fx_jpy` | 0.7000 | 0.5478 | **-0.3462** | 1.1404 | -0.5713 | 95 | -51 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_ny` | 0.8401 | 0.7369 | **-0.1572** | 1.5021 | -0.2095 | 125 | -21 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_pair` | 0.6031 | 0.4287 | **-0.4653** | 0.6938 | -1.0179 | 78 | -68 | PARTIAL | DO_NOT_ARM |
| `metals_core_downweighted` | 0.9633 | 0.9365 | +0.0424 | 2.2769 | +0.5652 | 117 | -29 | PARTIAL | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.9583 | 0.9258 | +0.0318 | 1.9748 | +0.2631 | 132 | -14 | PARTIAL | DO_NOT_ARM |
| `mx_btcusd_target5` | 0.9275 | 0.8814 | -0.0126 | 1.7846 | +0.0730 | 144 | -2 | PARTIAL | DO_NOT_ARM |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

### W7_MAX_CARRY_STRESS — OUT_OF_WINDOW_PRE_2025

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.4795 | 0.2779 | — | -0.0551 | — | 427 | — | PARTIAL | baseline |
| `fx_jpy` | 0.1633 | 0.0473 | **-0.2307** | -0.6915 | -0.6364 | 219 | -208 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_ny` | 0.2177 | 0.0747 | **-0.2032** | -0.5038 | -0.4488 | 271 | -156 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_pair` | 0.0872 | 0.0167 | **-0.2612** | -1.3605 | -1.3054 | 130 | -297 | PARTIAL | DO_NOT_ARM |
| `metals_core_downweighted` | 0.2757 | 0.1085 | **-0.1694** | -0.4651 | -0.4101 | 250 | -177 | PARTIAL | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.4259 | 0.2271 | **-0.0509** | -0.1638 | -0.1087 | 339 | -88 | PARTIAL | DO_NOT_ARM |
| `mx_btcusd_target5` | 0.5114 | 0.3072 | +0.0293 | -0.0168 | +0.0382 | 390 | -37 | PARTIAL | DO_NOT_ARM |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

### W7_MAX_CARRY_STRESS — IN_WINDOW_USED_ONCE_2025_PLUS

| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | %/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| current armed baseline | 0.8712 | 0.7863 | — | 1.2926 | — | 157 | — | PARTIAL | baseline |
| `fx_jpy` | 0.0949 | 0.0220 | **-0.7644** | -5.2863 | -6.5789 | 29 | -128 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_ny` | 0.1913 | 0.0630 | **-0.7234** | -2.1923 | -3.4850 | 62 | -95 | PARTIAL | DO_NOT_ARM |
| `fx_jpy_pair` | 0.0452 | 0.0057 | **-0.7806** | -10.6397 | -11.9323 | 17 | -140 | PARTIAL | DO_NOT_ARM |
| `metals_core_downweighted` | 0.8932 | 0.8199 | +0.0336 | 1.5023 | +0.2096 | 145 | -12 | PARTIAL | DO_NOT_REINTRODUCE |
| `metals_softband` | 0.8649 | 0.7808 | -0.0056 | 1.3069 | +0.0142 | 158 | +1 | PARTIAL | DO_NOT_ARM |
| `mx_btcusd_target5` | 0.8549 | 0.7682 | -0.0181 | 1.3515 | +0.0589 | 152 | -5 | PARTIAL | DO_NOT_ARM |
| `vp_euidx_pocgrav` | — | — | — | — | — | — | — | NOT_PRICEABLE | DO_NOT_ARM |

Coverage boundary: this account has incomplete broker truth for `crypto` (80.2%), `metals_core` (46.0%), `metals_softband` (50.7%), `sub_mid_dn_revert` (89.0%), `sub_xvol_pullback` (66.7%). Its numeric cells describe the priceable broker-supported subset and are not full-book authority.

## Decision

No direct extension is approved. Carry classification is not admission; AE's actuator vetoes both JPY sleeves and reintroduction of metals-core, CI leaves VP non-evaluable, and CH rejects redacted_account target-5R MX. `metals_softband` remains carry-conditional. Therefore no prospective tag or timeframe delta is justified by this grid.

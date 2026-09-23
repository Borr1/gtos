# `BOOKS_MC_V1` — the books an arming decision can pick from, at each firm's measured rules

**Session AI, wave 8.** 60,000 paths per cell through Session Q's `mc_firm_rules.mc`, imported unchanged. `L4` is each firm's measured phase 1; **`P2` is the whole 2-step evaluation and it is the one that gates a payout.**

## 0. The book the machinery cannot compose

`mc_firm_rules.parse_sleeve_set` fails closed on any sleeve outside `recost_w7_validation.BOOK_CONF` — the 11-sleeve W7 book — and `mx_btcusd` has no row in the W7 recost caches.

Book 4 is built from the ARCHIVE population's own daily net-R series and stamped `population: ARCHIVE` everywhere. It is a cross-population composition; the CONTROL row is the armed three on the SAME population so the comparison is like-for-like.

## 1. The cache books — the W7 population, both sizing conventions

Every published figure the owner has seen is the `published` convention; the deployable path implements `live`, and they differ by ~2.1x in size (`ARMED_SET_MC_V1.json` §1). Both are here because reporting one would be reporting the wrong number to somebody.

### published_vol_matched_full_kelly  (`eff risk` is the per-correlated-unit risk this convention delivers)

| book | account | n | cell | days | eff risk | mean R/day | **L4 p_pass** | L4 cal-d | **P2 p_pass** | P2 cal-d | %/mo |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | fwd_nights_0.0 | 117 | 0.848 % | 0.57114 | **1.0** | 60 | **0.999983** | 96 | 3.147 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | fwd_nights_1.0 | 117 | 0.849 % | 0.55833 | **1.0** | 60 | **0.99995** | 96 | 3.08 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | fwd_nights_max | 117 | 0.855 % | 0.39189 | **0.998483** | 78 | **0.9966** | 129 | 2.179 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | full_nights_0.0 | 190 | 0.949 % | 0.47806 | **0.999983** | 288 | **0.999967** | 467 | 0.712 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | full_nights_1.0 | 190 | 0.950 % | 0.46691 | **0.999967** | 288 | **0.999883** | 481 | 0.697 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | full_nights_max | 190 | 0.955 % | 0.32194 | **0.995233** | 398 | **0.991** | 646 | 0.483 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | fwd_nights_0.0 | 310 | 1.091 % | 0.28317 | **0.999433** | 39 | **0.999133** | 63 | 5.322 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | fwd_nights_1.0 | 310 | 1.096 % | 0.26025 | **0.99905** | 41 | **0.998117** | 66 | 4.913 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | fwd_nights_max | 310 | 1.130 % | 0.14079 | **0.94185** | 59 | **0.8985** | 99 | 2.74 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | full_nights_0.0 | 578 | 1.310 % | 0.2001 | **0.998817** | 189 | **0.997683** | 311 | 1.106 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | full_nights_1.0 | 578 | 1.316 % | 0.18527 | **0.9973** | 204 | **0.9946** | 331 | 1.029 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | full_nights_max | 578 | 1.352 % | 0.08817 | **0.883433** | 290 | **0.804333** | 484 | 0.503 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | fwd_nights_0.0 | 313 | 1.034 % | 0.33529 | **0.9999** | 33 | **0.999683** | 55 | 6.03 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | fwd_nights_1.0 | 313 | 1.039 % | 0.312 | **0.999733** | 36 | **0.9994** | 58 | 5.635 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | fwd_nights_max | 313 | 1.072 % | 0.18698 | **0.975** | 50 | **0.953567** | 85 | 3.486 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | full_nights_0.0 | 623 | 1.239 % | 0.24063 | **0.999683** | 161 | **0.9992** | 255 | 1.356 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | full_nights_1.0 | 623 | 1.246 % | 0.22404 | **0.999017** | 165 | **0.998083** | 269 | 1.27 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | full_nights_max | 623 | 1.278 % | 0.09764 | **0.876733** | 255 | **0.798067** | 425 | 0.567 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | fwd_nights_0.0 | 164 | 0.927 % | 0.43083 | **0.999983** | 44 | **0.999917** | 78 | 3.637 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | fwd_nights_1.0 | 164 | 0.928 % | 0.42144 | **0.999933** | 46 | **0.999867** | 80 | 3.562 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | fwd_nights_max | 164 | 0.935 % | 0.29942 | **0.996467** | 57 | **0.992233** | 105 | 2.551 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | full_nights_0.0 | 272 | 1.038 % | 0.36036 | **0.9999** | 202 | **0.99975** | 356 | 0.841 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | full_nights_1.0 | 272 | 1.040 % | 0.3522 | **0.999817** | 202 | **0.999683** | 365 | 0.823 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | full_nights_max | 272 | 1.055 % | 0.24608 | **0.993217** | 260 | **0.986567** | 481 | 0.583 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | fwd_nights_0.0 | 117 | 0.847 % | 0.56311 | **1.0** | 48 | **1.0** | 84 | 3.101 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | fwd_nights_1.0 | 117 | 0.848 % | 0.55303 | **1.0** | 48 | **0.999983** | 87 | 3.047 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | fwd_nights_max | 117 | 0.850 % | 0.42201 | **0.9989** | 60 | **0.99785** | 108 | 2.331 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | full_nights_0.0 | 190 | 0.948 % | 0.4699 | **0.999967** | 234 | **0.999917** | 412 | 0.699 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | full_nights_1.0 | 190 | 0.949 % | 0.46139 | **0.99995** | 247 | **0.999917** | 426 | 0.687 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | full_nights_max | 190 | 0.956 % | 0.35078 | **0.997467** | 288 | **0.995317** | 536 | 0.527 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | fwd_nights_0.0 | 310 | 1.092 % | 0.27668 | **0.9996** | 31 | **0.99925** | 57 | 5.204 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | fwd_nights_1.0 | 310 | 1.095 % | 0.22321 | **0.994767** | 37 | **0.9908** | 67 | 4.21 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | fwd_nights_max | 310 | 1.116 % | 0.05394 | **0.70935** | 51 | **0.55** | 95 | 1.037 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | full_nights_0.0 | 578 | 1.311 % | 0.19551 | **0.998417** | 163 | **0.996933** | 285 | 1.081 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | full_nights_1.0 | 578 | 1.317 % | 0.16393 | **0.992333** | 178 | **0.985283** | 326 | 0.911 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | full_nights_max | 578 | 1.346 % | 0.03529 | **0.668967** | 224 | **0.501233** | 413 | 0.2 |

### live_nominal_half_kelly  (`eff risk` is the per-correlated-unit risk this convention delivers)

| book | account | n | cell | days | eff risk | mean R/day | **L4 p_pass** | L4 cal-d | **P2 p_pass** | P2 cal-d | %/mo |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | fwd_nights_0.0 | 117 | 2.000 % | 0.50474 | **0.9966** | 27 | **0.992983** | 48 | 6.562 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | fwd_nights_1.0 | 117 | 2.000 % | 0.49342 | **0.9956** | 27 | **0.990917** | 48 | 6.414 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | fwd_nights_max | 117 | 2.000 % | 0.34623 | **0.9562** | 36 | **0.917167** | 60 | 4.501 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | full_nights_0.0 | 190 | 2.000 % | 0.42278 | **0.996233** | 165 | **0.992317** | 261 | 1.328 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | full_nights_1.0 | 190 | 2.000 % | 0.41292 | **0.994683** | 165 | **0.989883** | 275 | 1.297 |
| `FTMO_ARMED_TODAY_3` | FTMO | 3 | full_nights_max | 190 | 2.000 % | 0.28481 | **0.950167** | 192 | **0.91045** | 343 | 0.894 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | fwd_nights_0.0 | 310 | 2.000 % | 0.2543 | **0.9923** | 24 | **0.98525** | 40 | 8.759 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | fwd_nights_1.0 | 310 | 2.000 % | 0.23384 | **0.985167** | 25 | **0.971933** | 42 | 8.054 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | fwd_nights_max | 310 | 2.000 % | 0.12696 | **0.850967** | 31 | **0.754783** | 53 | 4.373 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | full_nights_0.0 | 578 | 2.000 % | 0.17927 | **0.992533** | 143 | **0.986283** | 239 | 1.513 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | full_nights_1.0 | 578 | 2.000 % | 0.16605 | **0.986783** | 148 | **0.975517** | 250 | 1.401 |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | 5 | full_nights_max | 578 | 2.000 % | 0.07956 | **0.820867** | 194 | **0.711417** | 316 | 0.671 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | fwd_nights_0.0 | 313 | 2.000 % | 0.30031 | **0.9948** | 20 | **0.989983** | 33 | 10.444 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | fwd_nights_1.0 | 313 | 2.000 % | 0.27952 | **0.99005** | 21 | **0.980983** | 36 | 9.721 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | fwd_nights_max | 313 | 2.000 % | 0.16766 | **0.8966** | 27 | **0.826267** | 45 | 5.831 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | full_nights_0.0 | 623 | 2.000 % | 0.21495 | **0.996067** | 113 | **0.992183** | 184 | 1.955 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | full_nights_1.0 | 623 | 2.000 % | 0.20018 | **0.992467** | 118 | **0.985** | 199 | 1.821 |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | 6 | full_nights_max | 623 | 2.000 % | 0.08787 | **0.800983** | 156 | **0.68935** | 260 | 0.799 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | fwd_nights_0.0 | 164 | 2.000 % | 0.38194 | **0.993967** | 23 | **0.9891** | 44 | 6.96 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | fwd_nights_1.0 | 164 | 2.000 % | 0.3736 | **0.9926** | 25 | **0.986583** | 44 | 6.808 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | fwd_nights_max | 164 | 2.000 % | 0.26521 | **0.951833** | 28 | **0.909683** | 53 | 4.833 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | full_nights_0.0 | 272 | 2.000 % | 0.31955 | **0.9943** | 125 | **0.989317** | 221 | 1.437 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | full_nights_1.0 | 272 | 2.000 % | 0.31232 | **0.992867** | 125 | **0.98695** | 221 | 1.404 |
| `redacted_account_SURVIVORS_4` | redacted_account | 4 | full_nights_max | 272 | 2.000 % | 0.21824 | **0.949917** | 154 | **0.9088** | 279 | 0.981 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | fwd_nights_0.0 | 117 | 2.000 % | 0.49765 | **0.996533** | 24 | **0.992683** | 42 | 6.47 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | fwd_nights_1.0 | 117 | 2.000 % | 0.48875 | **0.995633** | 24 | **0.991** | 45 | 6.354 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | fwd_nights_max | 117 | 2.000 % | 0.37293 | **0.964367** | 27 | **0.9331** | 51 | 4.848 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | full_nights_0.0 | 190 | 2.000 % | 0.41558 | **0.995667** | 137 | **0.99135** | 234 | 1.305 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | full_nights_1.0 | 190 | 2.000 % | 0.40806 | **0.9946** | 137 | **0.989583** | 247 | 1.282 |
| `redacted_account_RUNNABLE_3` | redacted_account | 3 | full_nights_max | 190 | 2.000 % | 0.31035 | **0.965683** | 151 | **0.9368** | 288 | 0.975 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | fwd_nights_0.0 | 310 | 2.000 % | 0.24848 | **0.991333** | 20 | **0.983583** | 36 | 8.559 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | fwd_nights_1.0 | 310 | 2.000 % | 0.2008 | **0.963417** | 22 | **0.9337** | 41 | 6.916 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | fwd_nights_max | 310 | 2.000 % | 0.04956 | **0.6344** | 23 | **0.460633** | 41 | 1.707 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | full_nights_0.0 | 578 | 2.000 % | 0.17517 | **0.991633** | 122 | **0.984417** | 214 | 1.478 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | full_nights_1.0 | 578 | 2.000 % | 0.14703 | **0.972317** | 132 | **0.9501** | 239 | 1.241 |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | 5 | full_nights_max | 578 | 2.000 % | 0.03252 | **0.628517** | 143 | **0.456683** | 250 | 0.274 |

## 2. The challenge book — the ARCHIVE population, with its same-population control

**Members: `mx_btcusd_d1_donchian_20_breakout`, `sub_xvol_pullback`.** the sleeves that reach ADMIT once the multiplicity bill comes from the prospective declaration instead of AA's over-counted 69 — measured by re-running the real gate (AI_GATE_AT_DECLARED_FAMILY_V1.json).

**alpha. Both members admit at alpha=0.20 at any declared family <= 32, and NEITHER admits alone at alpha=0.10 — Benjamini-Hochberg's step-up means they clear together or not at all. So this book's membership is a consequence of an owner decision that has not been taken yet.**

Weights at the allocator's own convention: `mx_btcusd_d1_donchian_20_breakout` 0.025, `sub_xvol_pullback` 0.45.

*`mx_btcusd`'s registry confidence is 0.025 (`default_off_runtime_capable_zero_activation`) against `sub_xvol_pullback`'s 0.45 and `crypto`'s 0.85 — 34x smaller than the armed sleeve. At the allocator's own convention, admitting it barely moves a book. The equal-weight branch prices what re-weighting it would be worth; the weight is Borhen's, and this is the number he needs to take that decision.*

| book | weights | branch | eff risk | days | mean R/day | acct | **L4** | **P2** | P2 cal-d | %/mo |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| `CONTROL_FTMO_ARMED_TODAY_3_on_the_archive` | admission.effective_re | live_nominal_per_unit | 2.0 % | 201 | 0.18846 | FTMO | **0.724667** | **0.566017** | 495 | 0.313 |
| `CONTROL_FTMO_ARMED_TODAY_3_on_the_archive` | admission.effective_re | live_nominal_per_unit | 2.0 % | 201 | 0.18846 | redacted_account | **0.7463** | **0.58145** | 417 | 0.313 |
| `CONTROL_FTMO_ARMED_TODAY_3_on_the_archive` | admission.effective_re | vol_matched_to_the_W7_ | 0.7483 % | 201 | 0.18846 | FTMO | **0.935033** | **0.886367** | 2213 | 0.117 |
| `CONTROL_FTMO_ARMED_TODAY_3_on_the_archive` | admission.effective_re | vol_matched_to_the_W7_ | 0.7483 % | 201 | 0.18846 | redacted_account | **0.938117** | **0.888317** | 1901 | 0.117 |
| `CHALLENGE_BOOK_admitted_at_the_declared_family` | admission.effective_re | live_nominal_per_unit | 2.0 % | 349 | 0.04722 | FTMO | **0.998533** | **0.997067** | 2415 | 0.136 |
| `CHALLENGE_BOOK_admitted_at_the_declared_family` | admission.effective_re | live_nominal_per_unit | 2.0 % | 349 | 0.04722 | redacted_account | **0.998533** | **0.9972** | 2113 | 0.136 |
| `CHALLENGE_BOOK_admitted_at_the_declared_family` | admission.effective_re | vol_matched_to_the_W7_ | 3.8068 % | 349 | 0.04722 | FTMO | **0.97215** | **0.950683** | 1268 | 0.258 |
| `CHALLENGE_BOOK_admitted_at_the_declared_family` | admission.effective_re | vol_matched_to_the_W7_ | 3.8068 % | 349 | 0.04722 | redacted_account | **0.972733** | **0.95125** | 1132 | 0.258 |
| `CHALLENGE_BOOK_equal_weight_sensitivity` | equal (1.0 each) | live_nominal_per_unit | 2.0 % | 349 | 0.29515 | FTMO | **0.713217** | **0.58215** | 181 | 0.848 |
| `CHALLENGE_BOOK_equal_weight_sensitivity` | equal (1.0 each) | live_nominal_per_unit | 2.0 % | 349 | 0.29515 | redacted_account | **0.729417** | **0.596033** | 166 | 0.848 |
| `CHALLENGE_BOOK_equal_weight_sensitivity` | equal (1.0 each) | vol_matched_to_the_W7_ | 0.7316 % | 349 | 0.29515 | FTMO | **0.9259** | **0.875867** | 815 | 0.31 |
| `CHALLENGE_BOOK_equal_weight_sensitivity` | equal (1.0 each) | vol_matched_to_the_W7_ | 0.7316 % | 349 | 0.29515 | redacted_account | **0.929867** | **0.87855** | 694 | 0.31 |
| `CHALLENGE_BOOK_plus_the_armed_three` | admission.effective_re | live_nominal_per_unit | 2.0 % | 464 | 0.08543 | FTMO | **0.70695** | **0.552983** | 465 | 0.326 |
| `CHALLENGE_BOOK_plus_the_armed_three` | admission.effective_re | live_nominal_per_unit | 2.0 % | 464 | 0.08543 | redacted_account | **0.72645** | **0.569317** | 409 | 0.326 |
| `CHALLENGE_BOOK_plus_the_armed_three` | admission.effective_re | vol_matched_to_the_W7_ | 1.127 % | 464 | 0.08543 | FTMO | **0.842** | **0.741183** | 1158 | 0.184 |
| `CHALLENGE_BOOK_plus_the_armed_three` | admission.effective_re | vol_matched_to_the_W7_ | 1.127 % | 464 | 0.08543 | redacted_account | **0.8524** | **0.749117** | 999 | 0.184 |

## 2b. The same three sleeves, two populations, 14x apart

**The SAME three armed sleeves, the SAME arithmetic, the SAME live sizing, measured on two populations. How far apart are they?**

| population | book-days | mean R/day | %/mo calendar | P2 p_pass | P2 cal-days |
|---|---:|---:|---:|---:|---:|
| W7 CACHE, fwd 2025+, worst carry | 117 | 0.34623 | **4.501** | 0.917167 | 60 |
| ARCHIVE, whole span | 201 | 0.18846 | **0.313** | 0.566017 | 495 |

**Ratio on the monthly rate: 14.38x.** The cache cell is the forward 2025+ window at the structural horizon; the archive cell is the whole 2000-2026 span at maxbars=80. And the forward window IS THE SELECTION WINDOW: `build_survivor_book.py:60` and `KB7_growth_kelly_sizing.py:130` share the `d.year >= 2025` predicate (Session V). So the archive figure is the out-of-window one.

CLAUDE.md section 4 already records the armed four earning +0.100 %/month over ten years out of window and -0.220 % before 2020. This is the same order of magnitude, derived independently from a different artifact by a different route, which is the strongest thing that can be said for either number.

**Treat the small number as the expected case, exactly as CLAUDE.md instructs. The 4.5 %/month figure is not wrong -- it is the measured rate on the window that chose these sleeves, and it answers a different question from 'what will they earn next year'.**

## 3. A correction to `CLAUDE.md` §4, found by controlling against Session V

**Session V's `BOTH_3` set IS the set FTMO is armed on today — V labelled it 'Q's SURVIVORS_BOTH_ACCOUNTS ... included because the two three-sleeve books in the record are not the same book', which was written before the 14:25 UTC adjustment to three sleeves. So the account-intersection book V measured as a contrast is the live canary.**

- V's `BOTH_3` = `['crypto', 'energy_agri', 'sub_xvol_pullback']`; the armed set = `['crypto', 'energy_agri', 'sub_xvol_pullback']`; **identical: True**.
- V's published `p_pass` (fwd / worst carry / live sizing / L4): **0.9521**; this file at 60,000 paths: **0.9562** (|Δ| 0.0041000000000001036). NOT seed noise. V's artifact predates 33d854189 and 8f6da5150, which extended BROKER_TRUE_COSTS_V1.json on FTMO, so V's series is on the old cost basis. L4 gap 0.0041 (inside Q's <= 0.00463 seed band and consistent with noise alone); P2 gap 0.0070, which is ~5 SE at these path counts and is the cost basis. Verified by ancestry, not assumed.

CLAUDE.md section 4 says 'Do not adopt the SURVIVORS_BOTH_ACCOUNTS number for the canary; it is the account-intersection book, not the config-runnable one.' That warning was written against the 12:55 armed set (`metals_core, crypto, energy_agri`) and is INVERTED by the 14:25 adjustment: SURVIVORS_BOTH_ACCOUNTS is now exactly the armed set, and CONF_FLOOR_3 is the set that is no longer armed. The same section's '[MEASURED: absence] no MC at 2.0 % exists for exactly the three-sleeve book' is therefore satisfied for the live three and still true for `metals_core, crypto, energy_agri`.

## 4. Per-book member lists, verbatim

| book | account | sleeves |
|---|---|---|
| `FTMO_ARMED_TODAY_3` | FTMO | `crypto`, `energy_agri`, `sub_xvol_pullback` |
| `FTMO_ARMED_PLUS_AD_RESTATED_5` | FTMO | `crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert`, `fx_jpy` |
| `FTMO_SURVIVORS_PLUS_AD_RESTATED_6` | FTMO | `crypto`, `energy_agri`, `fx_jpy`, `metals_core`, `sub_mid_dn_revert`, `sub_xvol_pullback` |
| `redacted_account_SURVIVORS_4` | redacted_account | `crypto`, `energy_agri`, `sub_xvol_pullback`, `vp_euidx_pocgrav` |
| `redacted_account_RUNNABLE_3` | redacted_account | `crypto`, `energy_agri`, `sub_xvol_pullback` |
| `redacted_account_SURVIVORS_PLUS_AD_RESTATED_5` | redacted_account | `crypto`, `energy_agri`, `fx_jpy`, `sub_mid_dn_revert`, `sub_xvol_pullback` |
| `CONTROL_FTMO_ARMED_TODAY_3_on_the_archive` | both | `crypto`, `energy_agri`, `sub_xvol_pullback` |
| `CHALLENGE_BOOK_admitted_at_the_declared_family` | both | `mx_btcusd_d1_donchian_20_breakout`, `sub_xvol_pullback` |
| `CHALLENGE_BOOK_equal_weight_sensitivity` | both | `mx_btcusd_d1_donchian_20_breakout`, `sub_xvol_pullback` |
| `CHALLENGE_BOOK_plus_the_armed_three` | both | `crypto`, `energy_agri`, `mx_btcusd_d1_donchian_20_breakout`, `sub_xvol_pullback` |

**`redacted_account_SURVIVORS_4` data gap.** `vp_euidx_pocgrav` fails closed at `sleeves/vp_euidx.py:70` for want of a GER40/UK100 M1 aux feed and has 0 trades in AA's walk. Its cache rows exist, so the MC can size it — but the live book cannot produce one of its trades. The 3-sleeve row below is what redacted_account can actually run today, and it is the row to read.

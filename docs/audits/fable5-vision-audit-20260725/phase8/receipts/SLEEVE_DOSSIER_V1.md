# `SLEEVE_DOSSIER_V1` — one truth per sleeve, and the rule when there isn't

**Session AI, wave 8. Generated docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_sleeve_dossier.py.** 32 sleeves across four populations. **30 recorded disagreements**, each with its axis.

Nothing here is a new measurement. Every figure is read from a committed artifact and carried with the stamp that says what it is a figure *about*. The deliverable is §1.

## 1. The reconciliation rules

### R0_every_figure_carries_its_population

**No number in this estate is 'the sleeve's economics'. Every figure is a figure about a (population, exit assumption, era, account, aggregation) tuple, and two figures may only be compared when all five agree.**

*why:* AE section 5 filed two repair rows for exactly this: the lane GATEs fx_jpy and fx_jpy_ny on cost-true archive splits while SURVIVOR_BOOK_V1 tiers them MEASURED_LIVE_CARRY and CARRY_CONDITIONAL_LIVE_SUPPORTED. Both artifacts are cost-true. Neither is wrong. They are different populations with different exit assumptions, and AE's own words were 'neither should be quoted as the sleeve's economics until they are reconciled'.

*mechanism:* Every leaf in `sleeves.<name>` sits under a population key that names its stamp. `strict_mode_violations` is empty or this artifact is wrong.

### R1_never_average_across_populations

**Where two populations disagree, publish both with their stamps and name the axis. Do NOT average, and do not pick the one that suits the argument.**

*why:* An average of two answers to two different questions answers neither, and it destroys the information that the disagreement itself carries. AD's carry restatement is the worked example: the survivor book's tier is computed at `carry_basis: MODELLED_HELD_TO_HORIZON` and AD's at the archive's realised hold. The gap IS the finding -- measured nights are 0.3 %-37 % of the modelled figure -- and averaging them would have hidden it.

### R2_the_account_is_part_of_the_sleeve

**Every cost, carry and tier figure is per account. Read the SET, never the count.**

*why:* CLAUDE.md B358: the tier list published as 'the book's' was FTMO's. The two accounts each hold four UNCONDITIONAL sleeves and share three; `metals_core` and `vp_euidx_pocgrav` swap places on a swap rate that differs by 48 %. The counts are identical, which is why the error survived.

*measured here:* per_account_divergence

### R3_a_tier_is_a_p100_test_and_says_so

**UNCONDITIONAL means `net_r['n_max'] > 0` -- the WORST reachable carry. It is not a statement about the mean hold, and a sleeve can be `survives_to_horizon: true` and still not be UNCONDITIONAL.**

*why:* `recost_w7_validation.py:1064-1073` is a 5-way if-chain in which order matters. `metals_core` on redacted_account is +0.0218 at the modelled mean and -0.01848 at max carry, so it is CARRY_CONDITIONAL there and UNCONDITIONAL on FTMO. AD found the same asymmetry from the other side: its redacted_account blocker is the p99 hold, not the mean, 'which is exactly what a time stop controls and what a mean hides'.

*corollary:* MEASURED_LIVE_CARRY is reachable by `fx_jpy` ALONE, because CARRY_STRUCTURAL is a one-element hardcoded set. Its absence on another sleeve carries no information.

### R4_three_live_n_exist_and_they_are_not_interchangeable

**A live figure must name which of the three corpora it counts: broker DEAL rows (money-bearing, authoritative for realized R / swap / commission), PACKET position_closed rows (what the engine recorded), or the LANE's admitted fills (packet rows that joined a deal record with complete cost accounting). They differ by up to 3.7x on one sleeve.**

*measured:* idxrev: 59 deal rows / 44 packet closes / 16 lane fills. fx_jpy: 32 / 22 / 7. Never put two of them in one column.

### R5_holds_use_broker_truth_and_the_anchor_matters_128x_more_than_the_bias

**The authoritative hold is the BROKER-TRUE one. Three medians exist for the same corpus and they differ by 44 % -- 2.2565 h at packet emission, 1.8783 h by `closed_at_utc`, 1.2603 h by broker truth.**

*why:* Session P first admitted the 148 packet-anchored holds and then refuted its own conclusion (B215): the +28 s correction is unmeasured on 39 % of the corpus and that gap is a CALENDAR BLOCK, not noise. The lag is three populations (+27.35 s / -0.03 s / +761.8 s), so a uniform bias term ADDS error to book-initiated closes. Use the sleeve-median comparison only, never as a bias-corrected series.

### R6_a_lane_verdict_is_not_an_admission_and_a_tier_is_not_either

**Three different things are routinely read as 'the sleeve passed': the GATE's ADMIT (five core gates at a sealed spec), the survivor book's UNCONDITIONAL tier (a carry test on the W7 cache), and the learning lane's KEEP/SIZE_UP (a recommendation from a default-off actuator). None implies another.**

*why:* 0 of 32 archive sleeves ADMIT and 0 of 246 AF members do, while the survivor book carries 4 UNCONDITIONAL sleeves per account and the lane issues 4 SIZE_UPs. A dossier that collapses these into one column would make the estate look either validated or dead, and it is neither.

### R7_cost_coverage_is_part_of_the_number

**Read `coverage` before quoting a cost. MEASURED is the minority on the two biggest-contributing sleeves: `crypto` is 35 MEASURED / 69 TRANSFERRED, so 66 % of the sleeve supplying 38.8 % of the book's edge is priced by transfer. And unpriced rows contribute `swap_r_per_night = 0.0` EXACTLY (`recost_w7_validation.py:1000-1001`), diluting the carry rate toward zero.**

*consequence:* `energy_agri` is 103 of 162 rows ABSENT (63.6 %), so its published swap rate is roughly a third of its priced subset's. Its UNCONDITIONAL tier survives -- max_nights 14 is far inside -- but its 4.31x `carry_headroom` must NOT be quoted as a safety margin. Keys are OMITTED WHEN ZERO on both `coverage` and `status`; always `.get(k, 0)`.

### R8_the_era_restriction_is_legitimate_and_it_is_still_a_different_population

**`era_class == RECORDED` is an outcome-INDEPENDENT restriction (a property of the broker's bar data), so it does not bias an estimate -- and it changes the population, which must be stamped. Until AF section 6's era x hour product defect is repaired, banded pricing is restricted to RECORDED.**

*measured:* `mx_btcusd` p_raw 0.0145 all-eras -> 0.0064 RECORDED, and n 318 -> 232. The spread model's era_ratio x hour multiplier reaches 198x on 2000s NZDUSD, charging 178 % of the risk unit as spread; each factor was validated alone and the PRODUCT never was.

### R9_the_live_exit_contract_is_not_the_measured_one

**Every economic figure in this estate describes `stop / target / maxbars`. Four sleeves run `partial_be_runner` live and twelve carry a binding time stop, and `time_stop_bars` is M15 PRINTED bars for EVERY sleeve (`execution.py:8953-8958`). State the contract a figure describes.**

*measured:* The twelve generating `mx_*` D1 sleeves' live time stop is 24-25 trading hours against a 72-96 h realised median: 72.3 %-90.1 % of their trades truncated. `energy_agri` is ARMED and its live scale-out contract measures -0.308 R/day against the plain exit (n=67, thin). All H4 sleeves and `vol_compression` ARE the pre-scaled contract AA walked, so nothing about their economics changes.

### R10_engine_reachability_is_the_default_convention

**Default every economic number to what the live engine can reach, and publish fix-enabled as a sensitivity band.**

*why:* `bar_provider.candles_to_bars` drops the last candle unconditionally, so the last closed bar before every gap is unreachable. AB measured 29 of 29 at H4 (1.3-6.8 % of five sleeves' trades); AF measured 4.26 % of 134,027 D1 trades, because every Friday is a pre-gap bar. The unreachable population is WORSE (-0.0771 R against +0.0117 R), so this is not currently costing money -- but the number is now known rather than assumed.

### R11_when_a_control_disagrees_with_prose_the_artifact_wins

**Prose in a result document is a claim; the JSON is the measurement. Where they differ, cite the JSON and record the prose as superseded.**

- AD section 5 says '22/22 published tiers reproduce'. In AD_CARRY_TIERS_RESTATED_V1.json `rule_replication_ok` is True on 20 rows, False on 0, and ABSENT on 2 -- both `vp_euidx_pocgrav`, which carry `restatable: false`. The honest statement is '20 of 22 restatable rows reproduce, 0 failures, 2 untested for want of archive coverage'.
- REPAIR_QUEUE_V1['summary']['n_rows'] is 87 while `len(rows)` is 134: the summary is AA-only and was never updated when AF and AE appended. Never read `summary` as the file's row count.
- AE_REPAIR_QUEUE_ROWS gives `sub_xvol_pullback`'s train meanR as null; AE_LIVE_RERATE_V2 gives -0.7678551683333333 for the same split. The row hardcodes a hand-authored triple (`ae_repair_rows.py:89`). The mean exists; it simply does not clear the floor.

## 2. The four populations

| population | n sleeves | authoritative for | NOT authoritative for |
|---|---:|---|---|
| `ARCHIVE` | 32 | realised holds, excursion/capture, exit-cell surfaces, per-gate margins, a sleeve's own p-value | portfolio economics (it has no book); cost levels pre-2010 |
| `W7_CACHE` | 11 | per-account broker-true cost terms, carry break-evens, survivor tiers, portfolio p_pass | holds — it has none |
| `LIVE` | 12 | what actually happened; swap actually charged | any expectancy — 14 distinct entry days |
| `LANE` | 30 | what the default-off actuator would recommend | admission — a KEEP is not a pass |

## 3. Where the populations disagree

| sleeve | axis | claim A | claim B | rule |
|---|---|---|---|---|
| fx_jpy | POPULATION + EXIT ASSUMPTION | LANE: GATE x0.0 | W7_CACHE FTMO: tier MEASURED_LIVE_CARRY -> AD restates UNCONDITIONAL | R0 + R1 + R6 |
| fx_jpy_ny | POPULATION + EXIT ASSUMPTION | LANE: GATE x0.0 | W7_CACHE FTMO: tier CARRY_CONDITIONAL_LIVE_SUPPORTED | R0 + R1 + R6 |
| fx_jpy (FTMO) | EXIT ASSUMPTION (carry basis) | published tier MEASURED_LIVE_CARRY at carry_basis=MEASURED_LIVE_STRUCTURAL | AD restates UNCONDITIONAL at the archive's realised hold (mean 0.0015 nights, p99 0.0, ratio to modelled 0.003 | R1 + R3. Publish both. The restated tier is the better answer to 'does this sleeve survive the carry it actually pays', and it is a SPLICE of two populations (cache edge + archive hold), which is why it is not silently substituted. |
| fx_jpy (redacted_account) | EXIT ASSUMPTION (carry basis) | published tier MEASURED_LIVE_CARRY at carry_basis=MEASURED_LIVE_STRUCTURAL | AD restates UNCONDITIONAL at the archive's realised hold (mean 0.0015 nights, p99 0.0, ratio to modelled 0.003 | R1 + R3. Publish both. The restated tier is the better answer to 'does this sleeve survive the carry it actually pays', and it is a SPLICE of two populations (cache edge + archive hold), which is why it is not silently substituted. |
| sub_mid_dn_revert (FTMO) | EXIT ASSUMPTION (carry basis) | published tier CARRY_CONDITIONAL at carry_basis=MODELLED_HELD_TO_HORIZON | AD restates UNCONDITIONAL at the archive's realised hold (mean 1.3082 nights, p99 7.0, ratio to modelled 0.097 | R1 + R3. Publish both. The restated tier is the better answer to 'does this sleeve survive the carry it actually pays', and it is a SPLICE of two populations (cache edge + archive hold), which is why it is not silently substituted. |
| sub_mid_dn_revert (redacted_account) | EXIT ASSUMPTION (carry basis) | published tier CARRY_CONDITIONAL at carry_basis=MODELLED_HELD_TO_HORIZON | AD restates UNCONDITIONAL at the archive's realised hold (mean 1.1769 nights, p99 7.0, ratio to modelled 0.088 | R1 + R3. Publish both. The restated tier is the better answer to 'does this sleeve survive the carry it actually pays', and it is a SPLICE of two populations (cache edge + archive hold), which is why it is not silently substituted. |
| metals_core | ACCOUNT | FTMO UNCONDITIONAL (swap 0.04307 R/night, break-even 489.0 h) | redacted_account CARRY_CONDITIONAL (swap 0.06384 R/night, break-even 329.0 h) | R2 |
| vp_euidx_pocgrav | ACCOUNT | FTMO CARRY_CONDITIONAL (swap 0.02597 R/night, break-even 251.0 h) | redacted_account UNCONDITIONAL (swap 0.0175 R/night, break-even 355.0 h) | R2 |
| **energy_agri** (ARMED) | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): 0.4169535804860445 R/day | live contract (partial_be_runner): 0.1086375761173806 R/day (delta -0.308316) | R9 |
| kz_london_crypto_low | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.5917864891529687 R/day | live contract (time_stop): -0.40184599858422565 R/day (delta 0.18994) | R9 |
| metals_core | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.25618795561985896 R/day | live contract (partial_be_runner): -0.19379658937811564 R/day (delta 0.062391) | R9 |
| metals_ob_micro | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.410698817276578 R/day | live contract (partial_be_runner): -0.2353425161220782 R/day (delta 0.175356) | R9 |
| metals_softband | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): 0.11542667754717911 R/day | live contract (partial_be_runner): 0.04639469049297577 R/day (delta -0.069032) | R9 |
| mx_btcusd_d1_donchian_20_breakout | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): 0.24474730018327362 R/day | live contract (time_stop): 0.10423855953596775 R/day (delta -0.140509) | R9 |
| mx_cadjpy_d1_volume_surge_reversal | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.0017219593835276778 R/day | live contract (time_stop): -0.067049413631343 R/day (delta -0.065327) | R9 |
| mx_ethusd_d1_donchian_20_breakout | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): 0.18160246161599797 R/day | live contract (time_stop): 0.08752715113137458 R/day (delta -0.094075) | R9 |
| mx_ger40_cash_d1_volume_surge_reversal | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.008176986428968268 R/day | live contract (time_stop): 0.11525710696916137 R/day (delta 0.123434) | R9 |
| mx_jp225_cash_d1_volume_surge_reversal | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): 0.20015291821910455 R/day | live contract (time_stop): 0.06905631035962452 R/day (delta -0.131097) | R9 |
| mx_us100_cash_d1_atr_mean_reversion | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.34799734096173773 R/day | live contract (time_stop): 0.10064346072383859 R/day (delta 0.448641) | R9 |
| mx_us30_cash_d1_volume_surge_reversal | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): 0.05987536186833737 R/day | live contract (time_stop): 0.14361189068718025 R/day (delta 0.083737) | R9 |
| mx_us500_cash_d1_atr_mean_reversion | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.25200426459456343 R/day | live contract (time_stop): 0.15838590889958723 R/day (delta 0.41039) | R9 |
| ny_crypto_momentum | EXIT CONTRACT (live policy vs plain) | as walked (plain stop/target/maxbars): -0.25449705903029146 R/day | live contract (time_stop): -0.012985477702804745 R/day (delta 0.241512) | R9 |
| asia_pdl_fade | CORPUS (which live record) | 20 broker deal rows over 7 entry days | 5 lane-admitted fills | R4 |
| asian_fade | CORPUS (which live record) | 17 broker deal rows over 7 entry days | 8 lane-admitted fills | R4 |
| fx_jpy | CORPUS (which live record) | 32 broker deal rows over 13 entry days | 7 lane-admitted fills | R4 |
| fx_jpy_ny | CORPUS (which live record) | 9 broker deal rows over 5 entry days | 5 lane-admitted fills | R4 |
| idxrev | CORPUS (which live record) | 59 broker deal rows over 13 entry days | 16 lane-admitted fills | R4 |
| kz_london_crypto_low | CORPUS (which live record) | 2 broker deal rows over 2 entry days | 1 lane-admitted fills | R4 |
| metal_session_reversion | CORPUS (which live record) | 11 broker deal rows over 6 entry days | 2 lane-admitted fills | R4 |
| ny_crypto_momentum | CORPUS (which live record) | 18 broker deal rows over 5 entry days | 6 lane-admitted fills | R4 |

## 4. The estate at a glance — one row per sleeve

`gate` is the ARCHIVE verdict at AA's spec. `tier` is FTMO / redacted_account, published, with AD's restatement in brackets where it moved. `lane` is FTMO. `live` is broker deal rows. `presc` is the count of standing repair rows.

| sleeve | armed | gate | failing gates | best exit Δ R/day | tier F / FN | lane F | live n | presc |
|---|---|---|---|---:|---|---|---:|---:|
| `asia_pdl_fade` |  | NOT_EVALUABLE | — | — | — / — | DOWN_WEIGHT x0.5 | 20 | 2 |
| `asian_fade` |  | NOT_EVALUABLE | — | +0.771 | — / — | HOLD_FLAG x1.0 | 17 | 1 |
| `crypto` | **yes** | REJECT | robustness,significance | +0.110 | UNCOND / UNCOND | SIZE_UP x1.078 | 0 | 5 |
| `energy_agri` | **yes** | REJECT | robustness,significance | +0.186 | UNCOND / UNCOND | INSUFFICIENT_EVIDENCE x1.0 | 0 | 6 |
| `fx_jpy` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.103 | MEAS_LIVE [UNCOND] / MEAS_LIVE [UNCOND] | GATE x0.0 | 32 | 10 |
| `fx_jpy_ny` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.110 | CC_LIVE_SUP / CC_LIVE_SUP | GATE x0.0 | 9 | 10 |
| `idxrev` |  | REJECT | expectancy,lifetime,robustness,significance | +0.028 | DEAD / DEAD | HOLD_FLAG x1.0 | 59 | 7 |
| `kz_london_crypto_low` |  | NOT_EVALUABLE | — | +0.581 | — / — | GATE x0.0 | 2 | 4 |
| `liq_asia_up_low_metal` |  | NOT_EVALUABLE | — | — | — / — | INSUFFICIENT_EVIDENCE x1.0 | 0 | 2 |
| `metal_session_reversion` |  | NOT_EVALUABLE | — | +0.626 | — / — | DOWN_WEIGHT x0.5 | 11 | 2 |
| `metals_core` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.249 | UNCOND / CC | DOWN_WEIGHT x0.5 | 0 | 9 |
| `metals_ob_micro` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.507 | DEAD / DEAD | INSUFFICIENT_EVIDENCE x1.0 | 0 | 7 |
| `metals_softband` |  | REJECT | robustness,significance | +0.015 | CC / CC | KEEP x1.0 | 0 | 6 |
| `mx_avausd_d1_donchian_20_breakout` |  | REJECT | robustness,significance | +0.157 | — / — | INSUFFICIENT_EVIDENCE x1.0 | 1 | 4 |
| `mx_btcusd_d1_donchian_20_breakout` |  | REJECT | significance | +0.309 | — / — | SIZE_UP x1.094 | 0 | 5 |
| `mx_cadjpy_d1_volume_surge_reversal` |  | REJECT | expectancy,robustness,significance,stability | +0.141 | — / — | HOLD_FLAG x1.0 | 0 | 7 |
| `mx_ethusd_d1_donchian_20_breakout` |  | REJECT | robustness,significance | +0.323 | — / — | SIZE_UP x1.084 | 0 | 4 |
| `mx_eu50_cash_d1_volume_surge_reversal` |  | NOT_EVALUABLE | — | — | — / — | — | 0 | 1 |
| `mx_fra40_cash_d1_volume_surge_reversal` |  | NOT_EVALUABLE | — | — | — / — | — | 0 | 1 |
| `mx_ger40_cash_d1_volume_surge_reversal` |  | REJECT | expectancy,lifetime,robustness,significance | +0.123 | — / — | INSUFFICIENT_EVIDENCE x1.0 | 0 | 6 |
| `mx_jp225_cash_d1_volume_surge_reversal` |  | REJECT | significance | +0.416 | — / — | INSUFFICIENT_EVIDENCE x1.0 | 1 | 3 |
| `mx_nzdjpy_d1_donchian_20_breakout` |  | REJECT | lifetime,robustness,significance | +0.056 | — / — | DOWN_WEIGHT x0.5 | 3 | 6 |
| `mx_us100_cash_d1_atr_mean_reversion` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.459 | — / — | INSUFFICIENT_EVIDENCE x1.0 | 0 | 8 |
| `mx_us30_cash_d1_volume_surge_reversal` |  | REJECT | robustness,significance,stability | +0.279 | — / — | INSUFFICIENT_EVIDENCE x1.0 | 0 | 5 |
| `mx_us500_cash_d1_atr_mean_reversion` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.454 | — / — | INSUFFICIENT_EVIDENCE x1.0 | 0 | 8 |
| `ny_crypto_momentum` |  | NOT_EVALUABLE | — | +0.282 | — / — | GATE x0.0 | 18 | 3 |
| `orb_crypto_london` |  | NOT_EVALUABLE | — | — | — / — | GATE x0.0 | 2 | 1 |
| `sub_mid_dn_revert` |  | REJECT | robustness,significance | +0.081 | CC [UNCOND] / CC [UNCOND] | HOLD_FLAG x1.0 | 0 | 6 |
| `sub_xvol_pullback` | **yes** | REJECT | significance | — | UNCOND / UNCOND | INSUFFICIENT_EVIDENCE x1.0 | 0 | 3 |
| `vol_compression` |  | REJECT | significance | +0.175 | — / — | SIZE_UP x1.148 | 0 | 2 |
| `vp_euidx_pocgrav` |  | NOT_EVALUABLE | — | — | CC / UNCOND | INSUFFICIENT_EVIDENCE x1.0 | 0 | 2 |
| `vss_fxcross_london_up_low` |  | REJECT | expectancy,lifetime,robustness,significance,stability | +0.329 | — / — | GATE x0.0 | 0 | 7 |

## 5. Per-account divergence, measured

| field | sleeves where the two accounts differ |
|---|---:|
| `tier_as_published` | **2** of 11 |
| `true_cost_ex_swap_r` | **11** of 11 |
| `swap_r_per_night` | **11** of 11 |
| `break_even_nights` | **11** of 11 |
| `break_even_hold_hours` | **7** of 11 |
| `carry_headroom_modelled` | **11** of 11 |
| `cost_multiple_vs_legacy` | **11** of 11 |
| `survives_to_horizon` | **1** of 11 |
| `survives_at_max_carry_p100` | **2** of 11 |
| `net_r_every_subkey` | **11** of 11 |

## 6. The standing repair queue

**193 rows, 193 distinct by full-row sha256 — zero byte-level duplicates.** By session: AA 87, AD 49, AE 11, AF 36, AI 10.

- `summary.n_rows` reads **87** against an actual **134** — AA's generator wrote it; AF and AE appended without updating it (R11).
- Append to **REPAIR_QUEUE_APPEND.jsonl — appending to the JSON is unsafe because regenerating it from aa_estate_walk.py drops appended rows**.
- diagnostics.py:71-91 defines 14 Prescription values; AD/AE/AF wrote 16 free-form strings outside it, so 83 of 183 rows carry a prescription the canonical enum would reject. Appending a free-form value is consistent with practice — say so in the row.
- Not counted: AF_REPAIR_QUEUE_FULL.json.gz holds 1,109 further rows (976 member + 133 family) with zero byte-overlap. Counting it takes the total to 1,292 and breaks every published figure. It is the member-level diagnostic corpus, cited separately.

## 7. What is missing, and what would close it

- **No population carries both a day series and per-account carry terms, so every tier restatement is a splice** — a generator re-run against `data/mt5_research_exports/bridge_ftmo_deep_h4_*`, absent from this machine. CLAUDE.md calls it the cheapest thing that would sharpen OD-3.
- **No exit index survives in any cache** — `geometry_lib.simulate` returns realized R and nothing else (Session N §8.1). Without exit times there is no position overlap, so the MC's drawdown path is unmodelled as well as the carry. Session P's packet carry closes it going forward.
- **`vp_euidx_pocgrav` generates nothing and is redacted_account's fourth UNCONDITIONAL survivor** — a GER40/UK100 M1 aux feed — it fails closed at `sleeves/vp_euidx.py:70`. Until then its tier is a claim about a sleeve that has never produced a trade.
- **`NATGAS.cash` commission is UNKNOWN, not zero** — one gas deal row on either account, or a signed energy-class peer transfer. Not a tick capture and not a re-run — both leave the commission unknown (AF §3.3).
- **The spread model's era_ratio × hour multiplier is unvalidated as a product and reaches 198× on pre-2010 FX** — AG's lane. Until then, banded pricing is restricted to `era_class == RECORDED`, which is outcome-independent (R8).
- **Zero armed sleeves have a single live fill** — time. ~7 book-days/month is expected; long silences are normal. The live record covers 12 sleeves and none of them is armed.

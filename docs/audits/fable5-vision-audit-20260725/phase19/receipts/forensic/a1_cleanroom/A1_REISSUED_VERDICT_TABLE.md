# A1 Re-issued Verdict Table — every CANDIDATE_BOOK member through the affected significance path

**Session FA continuation, Phase A1 OPEN half (a1b).** Generated 2026-08-03T15:54:09+00:00.
Machine record: `A1_REISSUED_VERDICT_TABLE.json` (same directory). Scripts: `a1b_capture_au_series.py` →
`a1b_corrected_null.py` → `a1b_reissue.py` → `a1b_write_md.py`. Clean-room basis:
`A1_CLEANROOM_NULL_DERIVATION.md` (+ `.json`).

**Affected set** = family members whose PUBLISHED p came from `block_permutation_p` /
`both_conservative` machinery on a daily series (a computed null). Padded-at-1.0 members are
unaffected by construction. Ratified basis confirmed from
`phase8/receipts/CANDIDATE_FAMILY_V1.json → ratified_rule`: CANDIDATE_BOOK_V1, B_balanced,
α = 0.10, all_declared (carried verbatim at the V27 tip, 59 declared / 57 looks).

**Method.** Every recomputed arm's daily series was captured **in process from the committed receipt
driver** and accepted only after the receipt reproduced float-exactly (CS: 12/12 checks in the blind
phase; AU: **16/16 arms PASS** on p_raw, q, verdict, fold_means, n_trades, spec_sha256 —
`A1B_AU_CAPTURED_SERIES.json`). Corrected null = the clean-room recipe generalized to each arm's own
fold structure: independent fold segments, within-fold AR(1) over a fitted-dependence grid
{ρ̂−SE, ρ̂, lag1_full, ρ̂+SE} × {gaussian, residual-bootstrap} innovations, per-fold scale,
studentised mean, 3 seeds, **primary p = max over variants** (the spec's own `both_conservative`
posture applied to model risk). Sims: breaker 700k×3/variant (reproduces the clean-room
**bit-exactly on all 8 variants** — the generalization self-check); AU arms 200k×3/variant (≥ the
100k floor). q: each receipt's own multiplicity block reproduced with the corrected p substituted for
the target only; substituting the *published* p back reproduces the published q exactly on every arm.

---

## 1. The flips

### 1a. ADMIT → REJECT — **BINDS IMMEDIATELY** (flagged loudly, as commissioned)

**`mx_btcusd_d1_donchian_20_breakout @ target_5R` — the estate's ONE standing admission, LIVE on FTMO
since 2026-07-31 — fails the corrected primary at ALL THREE admitting bands** (AU_EXIT_WIRING_V1,
family 48): flat 0.0009999→0.00268 (q 0.12864), low 0.00109989→0.002765 (q 0.13272),
mid 0.00109989→0.00281 (q 0.13488). Significance was the sole failing gate in every case, so the
overall verdict flips with it.

**The precision that must travel with this flag.** At the MEASURED within-fold dependence
(ρ̂ = 0.384 ± 0.069, 179 pairs — a *tight* estimate) the corrected p is 0.00135166, almost exactly
the published 0.00109989, and still admits (q ≈ 0.065). The REJECT comes **entirely from the +1SE
dependence variant** (ρ = 0.452–0.453, both innovation laws). So the finding is not "the p was
wrong"; it is: **the admission carries less than one standard error of dependence-model margin at
its 48-family bar** (flip boundary ρ ≈ 0.42–0.45 vs measured 0.384), where the breaker's corrected
ADMIT survives its own +1SE variant (flip at ρ ≈ 0.6, ≥1.2 SE above its measured 0.372). One posture
must judge both members; under the posture that admits the breaker, the mx admission REJECTS.
Whether a <1SE margin stands between an armed sleeve (registry weight 0.025, economically small by
design) and dis-arming is an **owner decision — flagged here, not taken here**. The LATEST
republication of the same admission (CM, wave 17, family 57, p 0.0013, q 0.0741) is
NOT_RECOMPUTABLE today (§5) and sits even closer to its bar (0.1/57 = 0.00175): a transferred
corrected primary of ≈0.0028 would read ≈0.16 there.

### 1b. REJECT → ADMIT — graduates NOBODY

**`cq_current_breaker_re_entry_inverted_5d_stop_0p25d` (CS, three-fold, family 59): published
p 0.00259974 / q 0.153385 REJECT → corrected p 0.00130333 / q 0.0768966 ADMIT** — the clean-room
verdict, reproduced here bit-exactly by the generalized engine. Per this commission's rule:
**REQUIRES_NEW_DECLARATION** — a corrected-rule re-issue can only reach a book through a new
declared, pre-registered step. (HDC/HDF's independent capture-anchored exact rule lands the same
ADMIT — §6.)

### 1c. Unchanged (13)

All eight `sub_xvol_pullback` arms (armed sleeve; corrected p is LARGER everywhere — the dependence
leak was flattering those REJECTs too), the four `mx as_walked` arms, and `mx target_5R @ high`:
REJECT stays REJECT.

---

## 2. Re-issued rows — every computed-null publication in scope

| member | arm | band | session | pub p | pub q | pub verdict | corr p (primary) | corr p @ measured rho | corr q | corr verdict | flip |
|---|---|---|---|---:|---:|---|---:|---:|---:|---|---|
| cq_current_breaker_re_entry_inverted_5d_stop_0p25d | three_fold_pooled | mid | CS | 0.00259974 | 0.153385 | REJECT | 0.00130333 | 0.000156667 | 0.0768966 | ADMIT | **REJECT->ADMIT** |
| mx_btcusd_d1_donchian_20_breakout | as_walked | flat_37_day_snapshot | AU | 0.00549945 | 0.263974 | REJECT | 0.00662332 | 0.00371166 | 0.287971 | REJECT | **UNCHANGED_REJECT** |
| mx_btcusd_d1_donchian_20_breakout | as_walked | low | AU | 0.00629937 | 0.287971 | REJECT | 0.00718499 | 0.00407499 | 0.287971 | REJECT | **UNCHANGED_REJECT** |
| mx_btcusd_d1_donchian_20_breakout | as_walked | mid | AU | 0.00639936 | 0.287971 | REJECT | 0.00737665 | 0.00422166 | 0.287971 | REJECT | **UNCHANGED_REJECT** |
| mx_btcusd_d1_donchian_20_breakout | as_walked | high | AU | 0.0470953 | 1 | REJECT | 0.0464816 | 0.0346249 | 1 | REJECT | **UNCHANGED_REJECT** |
| mx_btcusd_d1_donchian_20_breakout | target_5R | flat_37_day_snapshot | AU | 0.0009999 | 0.0479952 | ADMIT | 0.00268 | 0.00128833 | 0.12864 | REJECT | **ADMIT->REJECT** |
| mx_btcusd_d1_donchian_20_breakout | target_5R | low | AU | 0.00109989 | 0.0527947 | ADMIT | 0.002765 | 0.00133166 | 0.13272 | REJECT | **ADMIT->REJECT** |
| mx_btcusd_d1_donchian_20_breakout | target_5R | mid | AU | 0.00109989 | 0.0527947 | ADMIT | 0.00281 | 0.00135166 | 0.13488 | REJECT | **ADMIT->REJECT** |
| mx_btcusd_d1_donchian_20_breakout | target_5R | high | AU | 0.00509949 | 0.244776 | REJECT | 0.00932498 | 0.00539166 | 0.287971 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | as_walked | flat_37_day_snapshot | AU | 0.0119988 | 0.287971 | REJECT | 0.0267233 | 0.0117133 | 0.325167 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | as_walked | low | AU | 0.0119988 | 0.287971 | REJECT | 0.0242116 | 0.0102633 | 0.581079 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | as_walked | mid | AU | 0.0119988 | 0.287971 | REJECT | 0.024855 | 0.010635 | 0.596519 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | as_walked | high | AU | 0.0119988 | 0.575942 | REJECT | 0.025845 | 0.0111783 | 1 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | target_4R | flat_37_day_snapshot | AU | 0.0079992 | 0.191981 | REJECT | 0.01202 | 0.00398333 | 0.28848 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | target_4R | low | AU | 0.0079992 | 0.191981 | REJECT | 0.0109233 | 0.00351833 | 0.26216 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | target_4R | mid | AU | 0.0079992 | 0.191981 | REJECT | 0.0111716 | 0.00365166 | 0.26812 | REJECT | **UNCHANGED_REJECT** |
| sub_xvol_pullback | target_4R | high | AU | 0.0079992 | 0.383962 | REJECT | 0.011605 | 0.00380499 | 0.557039 | REJECT | **UNCHANGED_REJECT** |

`corr p (primary)` = max over the fitted-dependence span; `corr p @ measured rho` = max over the two
innovation laws at ρ̂. Per-variant tables (per seed) in `A1B_CORRECTED_NULL_RESULTS.json`.

## 3. Named wave-18/19 receipts that never computed a null

| member | session | receipt | published verdict | classification |
|---|---|---|---|---|
| cq_current_breaker_re_entry_inverted_5d_stop_0p25d | CQ (wave 18) | `CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json` | NOT_EVALUABLE | NO_COMPUTED_NULL_UNAFFECTED |
| cp_true_utc_ny_metals_long_v1 | CP (wave 18) | `CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json` | FROZEN_GATE_NOT_EVALUABLE_SOURCE_AND_FIDELITY_CAPTURE_REQUIRED | NO_COMPUTED_NULL_UNAFFECTED |
| cp_true_utc_ny_metals_long_v1 | CR (wave 19) | `CR_NY_METALS_CAPTURE_RESULT_V1.json` | NOT_EVALUABLE | NO_COMPUTED_NULL_UNAFFECTED |
| (1092 factory candidates; 1 graduated = cp_true_utc_ny_metals_long_v1) | CP (wave 18) | `CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json` | TRAIN_SURVIVORS_REQUIRE_GRADUATION_AND_RECORDED_GATE | NO_COMPUTED_NULL_LANE_EVIDENCE |
| (broad V4 S1R1 probe — not a CANDIDATE_BOOK member) | CP (wave 18) | `CP_FEBRUARY_FIRST_READ_RESULT_V1.json` | REJECT_S1R1_AS_NOT_JUSTIFIED | NO_COMPUTED_NULL_DIFFERENT_MACHINERY |

CQ's gate died on the sample gate (1 fold of 3) and CP/CR's on source/fidelity capture — in every
one `family_members_with_null = []`, so the affected code path never executed. Their NOT_EVALUABLE
verdicts stand as published. The FA route itself (this worktree,
`phase19/receipts/forensic/`) publishes verification receipts only — no gate verdict flows through
the machinery there.

## 4. The 59-member classification

**AFFECTED_RECOMPUTED (3)** — `mx_btcusd_d1_donchian_20_breakout`, `sub_xvol_pullback`, `cq_current_breaker_re_entry_inverted_5d_stop_0p25d`

**NO_COMPUTED_NULL_UNAFFECTED (1)** — `cp_true_utc_ny_metals_long_v1`

**AFFECTED_HISTORICAL_NOT_REISSUED (38)** — `asia_pdl_fade`, `asian_fade`, `crypto`, `energy_agri`, `fx_jpy`, `fx_jpy_ny`, `idxrev`, `kz_london_crypto_low`, `liq_asia_up_low_metal`, `metal_session_reversion`, `metals_core`, `metals_ob_micro`, `metals_softband`, `mx_avausd_d1_donchian_20_breakout`, `mx_cadjpy_d1_volume_surge_reversal`, `mx_ethusd_d1_donchian_20_breakout`, `mx_ger40_cash_d1_volume_surge_reversal`, `mx_jp225_cash_d1_volume_surge_reversal`, `mx_nzdjpy_d1_donchian_20_breakout`, `mx_us100_cash_d1_atr_mean_reversion`, `mx_us30_cash_d1_volume_surge_reversal`, `mx_us500_cash_d1_atr_mean_reversion`, `ny_crypto_momentum`, `orb_crypto_london`, `sub_mid_dn_revert`, `vol_compression`, `vp_euidx_pocgrav`, `vss_fxcross_london_up_low`, `thr_sub_xvol_pullback_vr14_s125_ac015`, `thr_sub_xvol_pullback_vr14_s150_ac015`, `thr_sub_xvol_pullback_vr14_s100_ac010`, `mxf_energy_fvg_retest_ukoil_cash_h4`, `mxf_volume_surge_reversal_ger40_d1`, `mxf_volume_surge_reversal_jp225_d1`, `mxf_volume_surge_reversal_nas100_d1`, `mxf_volume_surge_reversal_spx500_d1`, `mxf_volume_surge_reversal_uk100_d1`, `mxf_volume_surge_reversal_us30_cash_d1`

**PADDED_UNAFFECTED (17)** — `mx_eu50_cash_d1_volume_surge_reversal`, `mx_fra40_cash_d1_volume_surge_reversal`, `thr_sub_xvol_pullback_rngpos_mid`, `thr_sub_xvol_pullback_comp_coil`, `thr_asia_pdl_fade_persistence_revert`, `fam_ao_btc_power_pool_crypto_d1`, `mxf_energy_fvg_retest_natgas_cash_h4`, `mxf_energy_fvg_retest_usoil_cash_h4`, `overlay_metalabel_fx_jpy_p_ge_0p50`, `overlay_metalabel_fx_jpy_p_ge_0p55`, `overlay_metalabel_fx_jpy_p_ge_0p60`, `overlay_metalabel_fx_jpy_top75`, `overlay_metalabel_fx_jpy_top50`, `ch_p1_hist::m1::mx_btcusd_target5_redacted_account`, `ch_p1_hist::m2::mx_ethusd_d1_donchian_20_breakout`, `ch_p1_hist::m2::mx_avausd_d1_donchian_20_breakout`, `ch_p1_hist::m2::mx_nzdjpy_d1_donchian_20_breakout`

The 38 AFFECTED_HISTORICAL members carry computed-null rows across landed phase-6..18 receipts
(per-member counts and receipt lists: `A1B_MEMBER_NULL_INDEX.json`). **No such row is a member
admission at the sealed α** — the only ADMIT-verdict rows among them are Session W's gate self-test
controls (`W_NEGATIVE_CONTROLS.json`) and α = 0.2 research triage, which `options.py:110` bars from
arming. They are NOT re-issued here, deliberately: a REJECT→ADMIT flip graduates nobody under this
commission's rule, no current binding decision rests on any of these rows, and several bases are
superseded (flat-snapshot / pre-re-clock populations). The recompute path is the one used here: each
receipt's committed driver + `AA_ESTATE_TRADES.json.gz` (+ `AM_SUBMID_TRADES.json.gz`), the same
capture-validate-recompute loop.

## 5. The standing admission's republication lineage (all through the same machinery)

| session | receipt | node | p | q | verdict | m | note |
|---|---|---|---:|---:|---|---:|---|
| AL (wave 9) | `AL_CANDIDATE_DOSSIER_V1.json` | population=RECORDED\|exit=target_5R\|band=mid\|option=B_balanced\|family=CANDIDATE_BOOK_V2@all_declared | 0.00109989 | 0.0384962 | ADMIT | 35 | the first sealed-alpha ADMIT |
| AN (wave 10) | `POPULATION_RULE_V1.json` | grid X_btc5R\|B_balanced\|RECORDED\|flat | 0.0009999 | 0.0349965 | ADMIT | 35 | population axis; the rule later ratified |
| AN (wave 10) | `POPULATION_RULE_V1.json` | grid X_btc5R\|B_balanced\|RECORDED\|low | 0.00109989 | 0.0384962 | ADMIT | 35 | population axis; the rule later ratified |
| AN (wave 10) | `POPULATION_RULE_V1.json` | grid X_btc5R\|B_balanced\|RECORDED\|mid | 0.00109989 | 0.0384962 | ADMIT | 35 | population axis; the rule later ratified |
| AQ (wave 11) | `AQ_CONTRACT_TRUTH_V1.json` | REPAIRED\|B_balanced\|RECORDED\|flat | 0.0009999 | 0.0389961 | ADMIT | 39 | under the repaired time-stop contract |
| AQ (wave 11) | `AQ_CONTRACT_TRUTH_V1.json` | REPAIRED\|B_balanced\|RECORDED\|low | 0.00109989 | 0.0428957 | ADMIT | 39 | under the repaired time-stop contract |
| AQ (wave 11) | `AQ_CONTRACT_TRUTH_V1.json` | REPAIRED\|B_balanced\|RECORDED\|mid | 0.00109989 | 0.0428957 | ADMIT | 39 | under the repaired time-stop contract |
| AU (wave 12) | `AU_EXIT_WIRING_V1.json` | arms[4] target_5R flat_37_day_snapshot | 0.0009999 | 0.0479952 | ADMIT | 48 | the round-trip at the V5 48-family bill — RECOMPUTED in this re-issue |
| AU (wave 12) | `AU_EXIT_WIRING_V1.json` | arms[5] target_5R low | 0.00109989 | 0.0527947 | ADMIT | 48 | the round-trip at the V5 48-family bill — RECOMPUTED in this re-issue |
| AU (wave 12) | `AU_EXIT_WIRING_V1.json` | arms[6] target_5R mid | 0.00109989 | 0.0527947 | ADMIT | 48 | the round-trip at the V5 48-family bill — RECOMPUTED in this re-issue |
| AU (wave 12) | `AU_EXIT_WIRING_V1.json` | arms[7] target_5R high | 0.00509949 | 0.244776 | REJECT | 48 | the round-trip at the V5 48-family bill — RECOMPUTED in this re-issue |
| CA (wave 14) | `CA_MX_INCUBATION_V1.json` | measured_basis_ONE_OBJECT | 0.00109989 | 0.0582942 | ADMIT | 53 |  |
| CM (wave 17) | `CM_REVERIFY_V1.json` | gate.current.low | 0.00129987 | 0.0740926 | ADMIT | 57 | the LATEST republication (family 57, n=228) — **NOT_RECOMPUTABLE**, see below |
| CM (wave 17) | `CM_REVERIFY_V1.json` | gate.current.mid | 0.00129987 | 0.0740926 | ADMIT | 57 | the LATEST republication (family 57, n=228) — **NOT_RECOMPUTABLE**, see below |
| CM (wave 17) | `CM_REVERIFY_V1.json` | gate.current.high | 0.00559944 | 0.319168 | REJECT | 57 | the LATEST republication (family 57, n=228) — **NOT_RECOMPUTABLE**, see below |

**CM (the latest, wave 17) is NOT_RECOMPUTABLE today.** Exact missing input: the deep-universe bar
CSVs its generation stage reads — `sources/bars/deep_universe_h4d1_2014_2026/*.csv` (per-file
sha256s pinned in `CM_REVERIFY_V1.json → source_rows`) — absent from every worktree on this machine
(measured 2026-08-03). The AU arms recomputed above are the same admission object at n=232/family
48; CM's is the CJ-relabelled n=228/family 57 population, and its published p (0.0013) sits *closer*
to its bar (0.1/57 = 0.00175) than AU's did to its own.

---

## 6. HDC comparison — the required open-phase question

**Their construction** (`wave20-exit-capture-semantics-falsifier
…/phase20/SESSION_HDC_EXIT_CAPTURE_FALSIFIER_RESULT.md` §5–6; independently reproduced by HDF,
`…falsifier2 …/SESSION_HDF_…RESULT.md` item 5): keep the gate's **block sign-flip family**
(uncentred blocks, L=3) but repair the anchor — `capture_start_anchored_sign_blocks;
blocks_restart_at_each_capture`: segment blocks [4,4,3], 11 blocks total, support 2^11 = 2048,
**exact enumeration** (seed inoperative), tail = 2 states → p = 2/2048 = **0.0009765625**;
`both_conservative` against a within-capture circular bootstrap (floored at 1/10001) selects it;
q = 59p = **0.0576171875** → ADMIT. HDF also showed HC's earlier common-phase union (13/6144) loses
a tied state to float summation order (exact 14/6144) and is unsupported as a transformation group.

**How theirs differs from the clean-room corrected null.** HDC repairs *the anchor defect inside the
family* — it declares the sealed capture starts the authoritative origin (temporal origin as
authority, not nuisance) and restarts blocks at capture seams, which removes exactly the
rotation/adjacency arbitrariness the clean-room proved verdict-determining. The clean-room
**replaced the family** (fold-segmented AR(1) calibration, studentised mean, max over
fitted-dependence variants) because two measured defects survive ANY re-anchoring: (1) uncentred
flips put **64.8 % of the null variance in the candidate's own signal** (conservative under H1);
(2) at L=3 under the measured within-fold dependence (ρ 0.372 ± 0.175) the sign-flip family is
**anti-conservative at the decision bar** (measured size 3.8× for the fixed-phase rule under a
matched AR(1)). These act in opposite directions and an exact count prices neither.

**Why theirs still sits on a resolution floor.** The support of an 11-block sign-flip is
intrinsically 2^11 = 2048 atoms on this 31-point series. Exact enumeration removes Monte-Carlo
noise; it cannot add resolution: achievable p near the bar are k/2048, q moves in steps of
59/2048 = **0.0288**, the floor is 1/2048 = 4.88e-4, and their published p IS the k = 2 atom. The
ADMIT/REJECT boundary sits between k = 3 and k = 4, and single near-zero block sums move k — the
clean-room measured one such block sum at 1 % of the day-level sd. The clean-room statistic is
continuous: no support cap, per-seed spread ≤ 3 %.

**Verdict agreement and evidential strength.** **They AGREE — both ADMIT** at α = 0.10 over the
declared 59-family (HDC q 0.0576, clean-room q 0.0769) against the same published MC REJECT
(q 0.1534), and HDF reproduces HDC independently. Three independent corrected constructions landing
on the same side is the strongest available statement that the published REJECT was an artifact of
the implemented rule, not a property of the evidence. They differ in strength: HDC's p is nominally
smaller but is an exact count *inside* a quantised family whose dependence leak is unpriced
(anti-conservative direction for an ADMIT); the clean-room's is dependence-priced, continuous, and
max-over-model-risk — the more defensible number — and its q margin is thinner (23 % vs 42 %)
precisely because it charges the model risk the exact count does not.

---

## 7. Summary

- Family: 59 declared (V27 tip). Affected in the named wave-18/19 receipts: **1** (the breaker; the
  other 58 padded at 1.0 there by construction).
- Current-binding members through the affected path, recomputed: **3** (breaker, `mx_btcusd`,
  `sub_xvol_pullback`) = **17 arms**, every capture receipt-validated float-exactly first.
- Flips: **REJECT→ADMIT 1** (breaker — REQUIRES_NEW_DECLARATION, graduates nobody);
  **ADMIT→REJECT 3** (the standing admission's three admitting bands — **BINDS**, see §1a for the
  <1SE-margin precision); unchanged 13.
- 38 members: AFFECTED_HISTORICAL (no sealed-α admission rows; superseded bases) — indexed,
  not re-issued; 17 PADDED_UNAFFECTED; 1 NO_COMPUTED_NULL (`cp_true_utc_ny_metals_long_v1`).
- HDC/HDF and the clean-room agree: the breaker ADMITS under every corrected construction.

*Boundaries kept: no March-2026 outcomes, no live-forward (2026-07-29+) outcomes, no ledger appends,
no VPS/broker/token contact; heavy compute serial, peak RSS ≈ 0.8 GB.*

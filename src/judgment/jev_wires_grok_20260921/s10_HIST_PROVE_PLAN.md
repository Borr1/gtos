# HIST PROVE PLAN — COMPLETE_STATE assembler
**session:** `10_compose_alive_sleeves_complete_state`  
**as_of_ict:** `2026-09-21T06:04:21+07:00`  
**gate:** assembler itself does not change live fire rate until consumers APPLY. Prove **replay metrics** before any APPLY that changes admit/size/select/place.

No Chair APPLY is claimed here. No broker place.

---

## Module_ATR honesty (non-negotiable)

Blotter rows already name the lens:

```
"lens": "Module_ATR",
"fill_model": "geometry_proxy_ohlc_touch_module_ATR_exit_NOT_broker_NOT_module_exact",
"exit_shape": "stop0.75_tgt6.0_ATR",
"atr": <float from module>,
"R" / "R_ATR": geometry-proxy R
```

**Rules for this prove:**

1. Use blotter `atr` when present. If absent, `lens.atr_source=STATE_MISSING`. **Do not invent ATR.**
2. Do **not** merge Dig_3R monitor R into Module_ATR sumR. Do **not** use Edge_ATR affinity R for φ (φ prior lens law: XAU spring/three_fresh = LIVE_FILE Module_ATR 0.75/6.0 only).
3. Challenge broker R (deals jsonl) is a **separate universe**. Report it beside Module_ATR, never summed into the same bar.
4. GBPJPY vss×sub_mid hist-prove used **historical** `.../data/historical/GBPJPY_M15.csv` (span 2022-03-28→2026-04-17). That is **not** Challenge-true. Re-run on Challenge `GBPJPY_M15.csv` before scoped APPLY.
5. XAGUSD / NZDUSD Challenge M15: **MISSING**. Do not pretend Challenge tape exists. Module_ATR blotters exist (XAG metal_session n=782). Prove XAG on Module_ATR blotter only, label Challenge tape MISSING.
6. `geometry_proxy` is not a live fill. Fire-rate APPLY on Challenge must also score **Challenge deals** (`deals_since_20260909.jsonl`) for DD / n / fire rate.

---

## Tapes found (honest)

### Challenge-true (FTMO 0)

| tape | path | status |
|---|---|---|
| XAUUSD M15/H4/D1 | `_pr41_land/.../challenge_shadow_20260917/XAUUSD_{M15,H4,D1}.csv` | **PRESENT** (M15 ~157 KB) |
| XAUUSD multi copy | `.../challenge_shadow_20260917/multi/XAUUSD_*.csv` | PRESENT |
| GBPJPY M15/H4 | `.../multi/GBPJPY_M15.csv` (~157 KB) + H4 | **PRESENT** |
| EURUSD M15/H4 | `.../multi/EURUSD_M15.csv` | PRESENT |
| USDJPY M15/H4 | `.../multi/USDJPY_M15.csv` | PRESENT |
| GBPUSD M15/H4 | `.../multi/GBPUSD_M15.csv` | PRESENT |
| BTCUSD/ETHUSD/EURGBP/US30/UK100 | `.../multi/` | PRESENT (US30 house-off) |
| XAGUSD Challenge M15 | `.../multi/XAGUSD_M15.csv` | **MISSING** |
| NZDUSD Challenge M15 | `.../multi/NZDUSD_M15.csv` | **MISSING** |
| deals | `.../deals_since_20260909.jsonl` (~32 KB) | PRESENT (short window) |
| events | `.../events_since_20260915.jsonl` | PRESENT |
| box joint pull | `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/` | XAU + multi (no GBPJPY in listing) |

April / `data/historical*` / `exports/multi_instrument` = **not** Challenge tape (`bars.py` law).

### Module_ATR blotters (geometry proxy)

| blotter | n | sumR (from hist packs, not re-summed here) |
|---|---:|---|
| XAU three_fresh | 11239 | used in V2 conflict n=2353 |
| XAU spring | 5659 | V2 pick spring × 2353 |
| GBPJPY vss proxy | 818 | blotter sumR_vss=138.5124 |
| GBPJPY sub_mid SHORT | 2057 | blotter sumR=210.5132 |
| XAG metal_session | 782 | KEEP single |
| XAG metals_core | 16 | thin |
| XAG sub_xvol | 5 | thin |

φ prior: `PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json`  
asian_fade×EURUSD φ=2.029; PackageB×EURUSD φ=0.658; spring×XAU φ=0.142; three_fresh×XAU φ=0.015 (2026 haircut).

---

## Already-proved numbers (cite, do not re-invent)

### A. XAU three_fresh × spring (Module_ATR day-overlap) — PASS scoped

Cite: `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.md` + `JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920.md`

| metric | value |
|---|---|
| n_conflicts | 2353 |
| sumR_select (prefer spring) | **+235.36** |
| sumR_keep_all_on_conflicts | **−74.72** |
| sumR_random | −37.36 |
| beats keep_all / random | True / True |
| global Module_ATR combined | FAIL (EURUSD 13 cells drag) |
| GTOS_JEV_SLEEVE_SELECT_APPLY | **0 stays** |

Assembler prove: replay those 2353 days **with COMPLETE_STATE attached** (alive_sleeves, conflict_set, phi_by_sleeve, session_bucket). Select Choice must match spring pick. Fire rate on Challenge deals must not increase until scoped APPLY Chair-land.

### B. GBPJPY vss × sub_mid — mixed; starve bug

Cite: `GBPJPY_VSS_x_SUBMID_CONFLICT_HIST_PROVE_20260920.json`

| window | n_conflict_days | sumR_select_phi | sumR_keep_all | verdict |
|---|---:|---:|---:|---|
| ytd_2026 | 56 | 43.68 | 56.49 | **FAIL** |
| hold_last_2y | 228 | 107.74 | 105.22 | **PASS** (+2.52) |
| full | 692 | 246.59 | 305.55 | **FAIL** |

**Choice_hist C_SIZE_TRIM × 692** reason `conflict_phi_pick:asian_pkgb_incomplete_voters_trim`.

This is the assembler smoking gun: GBPJPY was trimmed because voters were incomplete (Policy C / choice_rule starve), not because size was bad. **COMPLETE_STATE expand must be replayed**; expected: fewer false C_SIZE_TRIM, fire rate up on KEEP days, sumR vs keep_all re-scored.

Tape for re-prove: Challenge `GBPJPY_M15.csv` (present) + Module_ATR blotters (present). Historical CSV used in the json is **not** the Challenge bar.

### C. EURUSD asian_fade × Package B — KEEP_ALL

V2: n_conflicts=13, sumR_select=926.63 vs keep_all=2350.46 → pick-one **FAIL**; KEEP_ALL is the identity. Assembler conflict_set kind=`KEEP_ALL_DUAL_POS`. Never alias Package B → live `sub_mid_dn_revert`.

---

## Prove jobs for THIS assembler (before any fire-rate APPLY)

### Job 0 — Schema round-trip (no tape)

- Build COMPLETE_STATE for fixtures: XAUUSD, GBPJPY, EURUSD, XAGUSD (alive priors only).
- Assert required keys present; `news_join` is object or `STATE_MISSING`; `session_bucket` in {asia,london,overlap,ny,off}; overlap at 13:00z.
- Assert `place=false`, `place_allowed_when_proved=true`.
- Assert Package B alias refused on EURUSD.
- Metrics: n_objects, n_full_state_dark, n_incomplete histogram. **No R.**

### Job 1 — Policy C ablation: 4-voter vs COMPLETE_STATE (Challenge replay)

**Tape:** Challenge XAUUSD M15+H4 + deals_since_20260909.jsonl (short — n will be small; **state n honestly**).

**Also:** Module_ATR XAU blotters for long-horizon **label-only** (geometry proxy R, not Challenge payout).

Compare:

| arm | state | Choice source |
|---|---|---|
| A0 current | 4 voters | evaluate_policy_c as-is |
| A1 complete | assemble_complete_state_v0 | evaluate_policy_c over complete **or** Jev Choice |
| A2 fail-closed | same but jev_dark simulated | must STAND, not D_FULL |

**Metrics (all arms):**

- n (intents / days)
- fire_rate = n_D_FULL / n
- n_A_STAND_DOWN, n_C_SIZE_TRIM, n_STATE_MISSING_skip
- sumR, meanR, DD (max equity drawdown in R)
- Challenge deals: n, sumR, DD **when ticket matches** — else MISSING

**Gate to APPLY Policy C expand:** A1 sumR ≥ A0 on Challenge deals **and** DD not worse **and** fire_rate documented. If Challenge deals n too small (<30), **do not APPLY**; extend tape (host-local) — honest BLOCKED.

### Job 2 — Sleeve-select conflict with complete state attached

- XAU: attach COMPLETE_STATE to V2 2353 conflict days; confirm pick=spring still; n, sumR_select, sumR_keep_all, fire_rate (select vs keep_all).
- GBPJPY: re-run φ-ranked D_FULL **without** forcing C_SIZE_TRIM on incomplete_voters; report ytd / hold_2y / full again; **and** Challenge-tape window separately.
- Gate scoped XAU APPLY: already PASS — Chair land admission bit. This session does not flip env.
- Gate scoped GBPJPY APPLY: need Challenge-tape PASS (sumR_select > sumR_keep_all on conflict days) **and** no false-trim. Currently **not** met on ytd_2026 / full.

### Job 3 — session_bucket overlap vs gold_state named=ny

Counterfactual: intents with utc_hour in [12,16). Count how many Policy C / session_fitness decisions change when overlap is first-class. Metric: n, fire_rate delta, sumR delta on Module_ATR blotter (Challenge if available). Gate: no APPLY until delta signed.

### Job 4 — news_join STATE_MISSING vs invented-empty

On Challenge events.jsonl: compare event_proximity Noul when spine empty (must ~0.5 / abstain) vs when HIGH in F5 window. **No invented HIGH.** Metric: n_spine_empty, n_high_in_window. Session 11 owns deeper news; assembler only proves honesty token.

### Job 5 — Jev-dark fail-closed

Force `GTOS_JEV_A1_CALL=0` and `GTOS_JEV_MAX_CALLS=0`. Every gate must STAND / skip, fire_rate=0 vs silent D_FULL. Metric: n_jev_dark, n_false_full (must be 0).

---

## Replay metric card (required on every job)

```
n                : int
n_dark           : int
n_state_missing  : int
fire_rate        : n_admit_full / n
n_trim           : int
sumR             : float   (lens named)
meanR            : float
DD               : float   (R or pct — named)
lens             : Module_ATR | Challenge_deals | MIXED_FORBIDDEN
atr_source       : blotter | geometry.atr14 | STATE_MISSING
tape_path        : str
window           : iso-iso
place            : false
apply            : false
```

MIXED_FORBIDDEN = Dig_3R + Module_ATR summed together.

---

## Gate to APPLY (Chair only)

| change | required prove | this session |
|---|---|---|
| Land `complete_state.py` observe-only | Job 0 | draft ready |
| Policy C voters → COMPLETE_STATE | Job 1 Challenge n≥30, sumR/DD/fire_rate | **not run** |
| a1_log / apply_size evaluate(complete) | Job 0 + Job 5 | draft |
| Scoped XAU select APPLY | V2 PASS already; Chair land | **do not flip env here** |
| Scoped GBPJPY select APPLY | Job 2 Challenge-tape PASS | **BLOCKED** (ytd/full FAIL + hist used historical CSV) |
| Global `GTOS_JEV_SLEEVE_SELECT_APPLY=1` | global hist PASS | **FORBIDDEN this pass** |
| Place Choice APPLY | session 14 hist | not this session |
| `GTOS_JEV_MAX_CALLS=500000` | ops, not R | Chair env |

---

## Missing (honest)

- Challenge XAGUSD / NZDUSD M15: **MISSING**
- Challenge deals window is ~2026-09-09+ (**small n**) — not a multi-year Challenge R tape
- VPS live tree unreachable — cannot confirm host `just_closed_siblings.json` / live `events.jsonl`
- `evaluate_policy_c` not in live admission.py — Job 1 needs a research harness, not host
- GBPJPY hist-prove tape was historical CSV — must re-bind to Challenge multi CSV

If a job cannot see Challenge tape, **say MISSING** and run Module_ATR blotter as **label-only**, never as payout proof.

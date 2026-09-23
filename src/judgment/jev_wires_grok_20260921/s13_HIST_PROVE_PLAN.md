# HIST PROVE PLAN — 13_instrument_affinity_sleeves

**as_of_ict:** `2026-09-21T06:03:39+07:00`  
**lens:** **Module_ATR honesty** — 1R = ATR(14) at **signal bar**; entry = **next open**; exit = structure stop **OR** time_stop @ 32 M15 bars (~8h) unless a pack names a **file-exit** (then use that file-exit, never mix).  
**never:** invent ATR, invent regime_tag, invent NEWS_PROTOCOL, merge Dig3R or Challenge $ into Module_ATR sumR, flip global `GTOS_JEV_SLEEVE_SELECT_APPLY`, broker place.  
**gate:** hist receipt **before** any APPLY that changes live fire rate.

---

## 0. Module_ATR honesty (non-negotiable)

| rule | meaning |
|---|---|
| ATR source | ATR(14) on the **same M15/H4 tape** the blotter used. If ATR series missing → `STATE_MISSING`, skip window, do not impute. |
| No invented regime | `regime_tag` / `conf_band` / `session_fit` stay PENDING unless a named composer already produced them. Hist bar does **not** need them; do not backfill a fake regime to “help” Jev. |
| Two R units never added | Module_ATR ATR-R, Dig 1R/3R geom, Challenge $ / orig_stop — **three ledgers**. Cite separately. |
| Cost | Disclose spread/commission if known. **Not a kill gate.** |
| Anti-oracle | Detectors use bars ≤ signal; entry_i = signal_i+1. |
| Proxy vs live | GBPJPY vss LONG KEEP is the **ORB-continuation proxy**, not live `vss_fxcross_london_up_low` n=38. Stamp both; do not pretend they are the same detector. |
| File-exit vs affinity-exit | XAG metal_session / sub_xvol / metals_core yearfold used **file-exit**. GBPJPY/NZD/XAU conflict cells used **structure∪32**. Never re-R a file-exit blotter with 32-bar stop (or vice versa) and call it the same prove. |

---

## 1. Tapes (present on box)

| instrument | path | span honesty |
|---|---|---|
| XAUUSD | `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` | PRIMARY multi-year — **present** |
| EURUSD | `/workspace/audit-merge/markets/tapes/EURUSD_M15.csv` | PRIMARY multi-year — **present** |
| GBPJPY | `/workspace/gtos/_swarm_land_tip/extract/data/historical/GBPJPY_M15.csv` | secondary ~2022-03→2026-04 — **present** |
| NZDUSD | `/workspace/gtos/_swarm_land_tip/extract/data/historical/NZDUSD_M15.csv` | 2022-03-28→2026-04-03 n≈99999 — **present** |
| XAGUSD M15 stitch | `…/historical_2022_2023/XAGUSD_M15.csv` + `…/data/XAGUSD_M15.csv` + `…/historical_2026/XAGUSD_M15.csv` | 2022-01-03→2026-04-24 n=100173 — yearfold used stitch |
| XAGUSD H4 | `…/exports/multi_instrument/XAGUSD_H4.csv` | 2019-10-15→2026-04-02 n=10000 — sub_xvol/metals_core |
| AUDUSD M15 multiyear | — | **MISSING** (~0.31y only) — cannot KEEP |
| Challenge $ closes | `/workspace/gtos/research/warroom_20260920/challenge_close_inventory.json` | **separate** lens |

If a listed CSV is deleted later: halt that cell, write `TAPE_MISSING`, do not substitute a different TF.

---

## 2. Reuse existing receipts (do not re-run as if new)

### 2.1 XAUUSD three_fresh × spring — APPLY candidate #1 — **PASS**

Cite:

- `/workspace/gtos/close_loop/war_room_20260920/JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.md`
- `/workspace/gtos/close_loop/war_room_20260920/JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920.md`

| metric | value |
|---|---:|
| n_conflicts | 2353 |
| sumR_select (spring) | **+235.36** |
| sumR_keep_all | **−74.72** |
| sumR_random | −37.36 |
| beats keep_all | True |
| beats random | True |
| fire_rate note | pick spring × 2353; three_fresh STAND on conflict windows only |

**Global V2 combined FAIL** (n=2366 select 1162 vs keep_all 2276) because EURUSD pick-one dragged. That **forbids** global APPLY. It does **not** unwind the XAU row.

**DD:** V2 receipt does not publish maxDD on the conflict subset. **Before Chair APPLY**, replay the same XAU conflict windows and report:

- maxDD_select vs maxDD_keep_all (ATR-R)
- n, sumR, fire_rate = n_select / n_conflict_days
- 2026 hold slice separately (three_fresh 2026 LIVE_FILE fail is the haircut reason)

### 2.2 GBPJPY side-aware vss × sub_mid — APPLY candidate #2 — **PASS**

Cite:

- `/workspace/gtos/close_loop/war_room_20260920/GROK_KEEP_HIST_PROVE_20260920/GROK_KEEP_HIST_PROVE_20260920.md`
- `/workspace/gtos/research/warroom_20260920/GBPJPY_VSS_UPLOW_x_SUBMID_SHORT_CONFLICT_DEEPEN_20260920.md`
- blotters: `blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl`, `blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl`

**Opp-side** (vss LONG × sub_mid SHORT) → pick vss LONG:

| window | n_days | sumR_select | sumR_keep_all | beats | verdict |
|---|---:|---:|---:|:---:|---|
| full cal | 420 | **222.35** | 127.61 | Y | PASS |
| hold 2025–26 | 140 | 48.59 | 42.79 | Y | PASS |
| train ≤2024 | 280 | 173.76 | 84.82 | Y | PASS |
| ytd 2026 cal | 31 | 20.17 | 21.90 | N | FAIL thin — do not kill full-cal PASS |
| time-overlap | 328 | **284.98** | 192.86 | Y | PASS |

**Same SHORT** → pick sub_mid:

| window | n_days | sumR_select | sumR_keep_all | beats | verdict |
|---|---:|---:|---:|:---:|---|
| full cal | 272 | **341.33** | 177.94 | Y | PASS |
| time-overlap | 162 | **379.55** | 247.16 | Y | PASS |

**Do not wire:** static φ-always-sub_mid mixed BOTH: 246.59 < 305.55 FAIL.

**DD / fire_rate gap:** deepen pack publishes sumR + n_days, not maxDD or fire_rate. Replay blotters for:

- maxDD_select vs keep_all (ATR-R)
- fire_rate = days_picked / days_both_alive
- n

### 2.3 EURUSD KEEP_ALL — draft APPLY — **identity PASS** (not a pick test)

Cite: V2 EURUSD year row + choice_rule_v4.

| metric | value |
|---|---:|
| keep_all (asian_fade + Package B) | **2350.46** |
| v3 pick asian_fade only | 1235.51 |
| v2 incomplete trim asian_fade | 926.63 |
| signs-disagree n | **0** |

Bar: KEEP_ALL identity (`sumR_select == sumR_keep_all`) is PASS. Pick-one is FAIL. Occupancy KEEP-one on the **writer** is a separate envelope (may still block the second print) — hist must report **admit_filter both** vs **writer occupancy drop**.

### 2.4 XAGUSD — **no conflict APPLY**

Cite: `XAGUSD_MODULE_ATR_YEARFOLD_20260920` + `XAGUSD_METALS_CONFLICT_HIST_PROVE` SKIPPED_NOT_FAIL.

| sleeve | verdict | n | sumR | yf |
|---|---|---:|---:|---:|
| metal_session_reversion | KEEP | 782 | +168.08 | 1.0 |
| sub_xvol_pullback | NARROW | 5 | +7.0 | 1.0 (2y) |
| metals_core | NARROW | 16 | +10.05 | 0.57 |

Conflict hist **SKIPPED** (need ≥2 KEEP). Prove plan = **do not APPLY**. Optional SHADOW Score calibration only (see §4).

### 2.5 NZDUSD sub_mid SHORT — **KEEP sleeve, no conflict APPLY**

Cite: `AUDNZD_MID_STRETCH_MODULE_ATR_20260920` + GROK_KEEP_HIST_PROVE §4.

| year | n | avg_R | sum_R |
|---:|---:|---:|---:|
| 2022 | 350 | 0.2173 | 76.04 |
| 2023 | 432 | 0.2654 | 114.67 |
| 2024 | 450 | 0.2820 | 126.91 |
| 2025 | 442 | 0.2826 | 124.91 |
| 2026 | 112 | 0.3052 | 34.18 |
| **all** | **1786** | **0.2669** | **+476.70** |

yf=1.0 consec=5. Siblings vss/orb/wide_sweep **KILL**.

---

## 3. New prove required before extra APPLY (not this session's Chair bits)

### 3.1 NZDUSD spring_LONG × sub_mid_SHORT — **UNPROVED conflict**

**Why:** AUDNZD pack lists `NZDUSD_spring_LONG_hist` KEEP n=2367 avg_R=0.1203 yf=1.0 as “conflict counterpart”. No day-overlap `sumR_select` vs `sumR_keep_all` receipt exists. Resolver has **no** NZDUSD branch.

**Plan (SHADOW LABEL only until PASS):**

1. Load NZDUSD M15 tape (path above). ATR(14) on that tape — if ATR cannot be computed for a bar, skip that bar (`STATE_MISSING`), do not invent.
2. Rebuild (or reuse if found) Module_ATR blotters:
   - sub_mid SHORT (already KEEP; cite deepen pack)
   - spring_LONG (KEEP on swarm — **confirm blotter path**; if blotter MISSING, regenerate with same structure∪32, do not use Dig3R)
3. Conflict window = calendar day with ≥1 entry from **both**.
4. Metrics:

| metric | required |
|---|---|
| n_conflicts | report |
| sumR_select (each rule: prefer_spring / prefer_sub_mid / keep_all / random) | report |
| maxDD_select vs keep_all | report |
| fire_rate | n_picked / n_conflict_days |
| n | trades and days |
| hold 2025–26 vs train ≤2024 | both must not reverse the winner |

5. **PASS bar:** one named rule beats keep_all **and** random on full-cal **and** hold, with n_conflicts ≥ 100 (below that: NARROW, no APPLY).
6. **Do not** copy XAU “always prefer spring”. NZD sub_mid SHORT is the F5 KEEP activate tag; spring may lose.
7. three_fresh_like on NZD is research_only — exclude from APPLY conflict set.

If blotter MISSING after hunt: write `BLOTTER_MISSING` and keep UNPROVED. Do not APPLY.

### 3.2 GBPJPY spring_LONG vs F5 pair — **UNPROVED widen**

Affinity swarm ranks spring_LONG×GBPJPY φ=1.0343 > vss. F5 priors do **not** inject spring. Optional SHADOW hist (same day-overlap method) **after** NZD prove. Not an APPLY candidate this pass.

### 3.3 XAU 2026 three_fresh haircut vs Edge_ATR — already separated

Do not re-prove Edge_ATR +34.43 into φ. LIVE_FILE 2026 three_fresh fail stays the haircut. Optional: publish maxDD on XAU conflict 2026-only slice before land.

---

## 4. Score calibration (SHADOW; not APPLY)

`sleeve_affinity_fit` Score 0/1/2 vs keep_status. Replay:

- Label each (instrument,sleeve,year) KEEP/NARROW/KILL from packs above.
- Score=2 should concentrate on KEEP cells; Score=0 on KILL (NZD vss/orb/wide_sweep, GBPJPY vss SHORT).
- Metric: fraction of KEEP years with Score≥1.5 (if Jev returns continuous) — **report only**. Never size-up from this Score this pass.

If evaluate() cannot be called (no key): skip Score calib, keep field wiring; do not fake answers.

---

## 5. Replay procedure (Challenge tape **and** Module_ATR)

Two ledgers, never added:

**A. Module_ATR conflict replay** (primary bar for sleeve-select)

```
for each scoped cell in {XAU, GBPJPY, EURUSD}:
  load named blotters (jsonl)
  rebuild conflict windows
  emit: n, sumR_select, sumR_keep_all, sumR_random, maxDD_select, maxDD_keep_all,
        fire_rate, hold vs train
  lens tag on every row: Module_ATR | file-exit | Challenge_$
```

Scripts already on box (reuse, do not rewrite detectors):

- `JEV_SLEEVE_SELECT_choice_rule_v4_20260920.py` (KEEP_ALL / TRUE_CONFLICT kinds)
- deepen GBPJPY scripts behind `GBPJPY_VSS_UPLOW_x_SUBMID_SHORT_CONFLICT_DEEPEN`
- XAU V2 hist-prove script cited from V2 md

**B. Challenge $ overlay** (secondary, occupancy/place)

- `/workspace/gtos/research/warroom_20260920/challenge_close_inventory.json`
- V2 already: Challenge KEEP conflicts n=1 select 2.265 vs keep_all 2.01 — **too thin to drive APPLY**.
- Report n, $ PnL, DD%, fire count. If Challenge tape for a symbol is MISSING: say MISSING.

Place Choice PLACE|STAND|DELAY hist (owner override) is **queued** in `PLACE_FLUID_HIST_PROVE_QUEUE_20260921.md` — not this session's APPLY gate. Sleeve-select APPLY changes **which sleeve is admitted**, not `order_send`.

---

## 6. Gate to APPLY (Chair only)

| candidate | hist | this session | Chair |
|---|---|---|---|
| `GTOS_JEV_SLEEVE_SELECT_APPLY` global | V2 combined FAIL | **must stay 0** | do not flip |
| `…_APPLY_XAU_CONFLICT` | PASS +235 vs −75 n=2353 | design; **do not set** | land #1 after maxDD slice if desired |
| `…_APPLY_GBPJPY_CONFLICT` | side-aware PASS | design; **do not set** | land #2; never static-φ picker |
| `…_APPLY_EURUSD_KEEP_ALL` | identity PASS | design draft | occupancy interaction first |
| XAG conflict APPLY | SKIPPED | **forbidden** | only if second sleeve KEEP |
| NZDUSD conflict APPLY | UNPROVED | **forbidden** | after §3.1 PASS |
| NZDUSD sleeve SHADOW menu | KEEP yearfold | already in F5 priors | remint ON_SURFACE is KEEP-activate, not Jev APPLY |
| place / order_send | default off | **never from this session** | after place_fluid hist queue |

**Pass file to write (Chair replay, not this session):**  
`HIST_PROVE_RECEIPT_<CELL>_<date>.json` with `{lens, n, sumR_select, sumR_keep_all, maxDD_select, maxDD_keep_all, fire_rate, hold_split, tape_path, atr_source, news_join: STATE_MISSING, place: false}`.

---

## 7. Blockers (honest)

1. VPS machineId `7cfa9657-…` unreachable this seat — live fire-rate vs SHADOW cannot be confirmed on Admin.
2. XAU/GBPJPY maxDD not in the cited receipts — **should** be filled before land, not invented here.
3. NZDUSD spring blotter path not found as a named jsonl in war_room hunt this pass → §3.1 may start MISSING.
4. `jev_client` default budget 200; Score calib needs `GTOS_JEV_MAX_CALLS` raise **or** offline replay of stored answers.
5. Shadow sidecar jsonl is **not** proof (doctrine).
6. GROK_KEEP_ACTIVATE text still says “Jev never places” — retired by owner 2026-09-21; hist plans must not copy that eternal cage.

---

## 8. Metrics dictionary (every receipt)

```
n                # trades or conflict-days (named)
sumR             # Module_ATR ATR-R (or file-exit ATR-R; named)
maxDD            # peak-to-trough of cumulative ATR-R on the same series
fire_rate        # selected fires / eligible conflict windows (or / session days)
hold_split       # train≤Y vs hold>Y as published (2024/2025–26 for 5y tapes)
n_incomplete     # if Policy C coupling reported; else omit
place            # always false in this session's outputs
```

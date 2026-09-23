# HIST PROVE PLAN — 20_whole_code_envelope_audit

**lens law:** Module_ATR honesty. Never invent ATR/regime. Never merge Dig3R R into Module_ATR sumR. Challenge R stays a **separate** column.  
**place=false** on every prove run. `order_send=0`. APPLY only after Chair reads a receipt.

---

## 0. Tape inventory (found vs MISSING)

### Module_ATR blotters FOUND

| path | sleeve × instrument |
|---|---|
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | XAU × three_fresh |
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl` | XAU × spring |
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl` | GBPJPY × vss |
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl` | GBPJPY × sub_mid SHORT |
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAGUSD_metals_core_20260920.jsonl` | XAG × metals_core |
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAGUSD_metal_session_reversion_20260920.jsonl` | XAG × session_reversion |
| `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAGUSD_sub_xvol_pullback_20260920.jsonl` | XAG × sub_xvol |

Duplicates under `/workspace/gtos/research/warroom_20260920/` — prefer close_loop copies.

### Hist-prove receipts FOUND

| path | honest read |
|---|---|
| `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.{md,json}` | **combined Module_ATR FAIL** (EURUSD drag). **XAU-day three_fresh×spring PASS** |
| `JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920.*` | scoped_apply_recommended=true; **global APPLY=0** |
| `CF_C_MODULE_ATR_XAU_THREE_FRESH_SPRING_SCOREBOARD_20260920.*` | Module-native C-rule; Dig3R cite-only |
| `JEV_SLEEVE_SELECT_HIST_PROVE_WIDEN_GBPJPY_XAG_20260920.*` | widen pack present |
| `GBPJPY_VSS_x_SUBMID_CONFLICT_HIST_PROVE_20260920.*` | conflict hist |
| `XAGUSD_METALS_CONFLICT_HIST_PROVE_20260920.*` | XAG conflict |
| `GROK_KEEP_HIST_PROVE_20260920/` | KEEP family |
| `CF_COUNTERFACTUAL_SCOREBOARD_ABSORB_DIG3R_20260920.*` | **cite only — do not copy R into Module_ATR columns** |

### MISSING (honest)

| need | status |
|---|---|
| VPS live `events.jsonl` Challenge writer tape | **MISSING this seat** (path claimed `shadow_logs/f5_minimal/operator/events.jsonl` / Admin `host-local\redacted_host\repo\...`). Use lab `judgment/astra/lab/challenge_shadow_20260917/events_since_20260915.jsonl` if present; else `news_join=STATE_MISSING` |
| Hold/exit Challenge MFE/giveback tape keyed to FLUID-HLD | **MISSING as a named Module_ATR blotter** — do not invent. Prove hold wires only if Challenge closes with `exit_class` exist in host events / `just_closed_siblings.json` |
| NZD pair Module_ATR blotter | **MISSING** — affinity session 13 must not fake NZD ATR |
| EURUSD Module_ATR yearfold that **beats keep_all** | V2 shows EURUSD asian_fade×PackageB **FAIL** (sumR_select 926.63 < keep_all 2350.46, n=13) |
| Live Admin rg of skip_reason histogram | **MISSING** (host-mesh down). Box mirrors only |
| Policy C / two_stop **wired** fire-path replay | helpers exist; PR41 import **MISSING** — prove cannot claim live effect until splice |

`research_armed.MODULE_ATR_WINNER_TAGS` = `{dsp_three_fresh_lower_lows, dsp_spring_close_on_20low_through_the_box}` only. Other sleeves are **not** Module_ATR winners unless a blotter says so.

---

## 1. Already-proved numbers (cite, do not re-invent)

From V2 (`JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.md`) — **conflict-set only**:

| lens | n | sumR_select | sumR_keep_all | beats keep_all |
|---|---:|---:|---:|:---:|
| Module_ATR combined | 2366 | 1161.99 | 2275.74 | **False** |
| XAU day three_fresh×spring | 2353 | **+235.36** | **−74.72** | **True** |
| EURUSD year asian_fade×PackageB | 13 | 926.63 | 2350.46 | **False** |
| Challenge KEEP conflicts (SEPARATE) | 1 | 2.265 | 2.01 | True (n=1 — not a global gate) |

**Gate:** scoped XAU APPLY candidate remains legal to **propose**. Global `GTOS_JEV_SLEEVE_SELECT_APPLY` stays 0. EURUSD KEEP_ALL scoped bit is identity, not “combined PASS”.

CF_C Module_ATR XAU yearfold (separate from V2 conflict bar): three_fresh C-rule histogram STAND/TRIM/FULL over 13 years; **year_le0 geometry includes 2026** — that is why three_fresh STAND on φ haircut / 2026-like fail.

---

## 2. Metrics every residual wire must report

Replay **before** any APPLY that changes live fire rate:

| metric | definition |
|---|---|
| `n` | decisions / conflict cells / closes in scope |
| `n_fire` / `fire_rate` | admitted-and-placed (or would_place) / candidates |
| `sumR` | Module_ATR R if blotter exists; else Challenge R **labeled Challenge**; never mix |
| `meanR` | sumR / n_fired (or n_cells — declare which) |
| `DD` | max drawdown in the same lens units |
| `n_stand` / `n_trim` / `n_full` | Choice histogram |
| `delta_sumR` | vs keep_all / vs current static |
| `delta_fire_rate` | vs current static |
| `delta_DD` | vs current static |

**Pass bar (default, Chair may tighten):**

1. `sumR_wire > sumR_static` on the **same** cell set  
2. `DD_wire ≤ DD_static + ε` (ε=0 unless Chair names)  
3. fire_rate change **signed and explained** (cheaper usage is not a pass)  
4. `n` ≥ prove-bars already frozen in `process_lock.py` (size: min_decidable 20 / min_moved 5 / min_distinct 2; label: min_non_default 5)  
5. invented_high_forbidden = true  
6. Dig3R R absent from Module_ATR columns  
7. `place=false` on the prove receipt  

Fail → stay SHADOW. No silent APPLY.

---

## 3. Per-family prove plan (residuals first)

### 3.1 Place fluid (FLUID-PLC-001..007) — PRIMARY place candidate

- **Tape:** Challenge writer actuals vs shadow PLACE choices. Host `events.jsonl` **MISSING this seat** → first step is Chair CopyFromBox / host events join. Until then: lab `events_since_20260915.jsonl` if file exists, else **BLOCKED / STATE_MISSING**.
- **Counterfactual:** for each cost/event/occupancy LABEL, would Choice PLACE/STAND/DELAY have improved Challenge sumR vs writer actual?
- **Module_ATR:** not the place-path lens (place is Challenge writer). Do not score place on XAU Module_ATR blotters.
- **APPLY gate:** shadow log PLACE vs actuals; sumR/DD/fire_rate; n; then Chair `GTOS_JEV_PLACE_FLUID_APPLY` **scoped**. Writer still prints.

### 3.2 Hold / exit (FLUID-HLD + exit_policy_v4)

- **Tape:** Challenge closes with `exit_class` / MFE / time-stop. **Named Module_ATR hold blotter MISSING.** Use Challenge deals only, labeled Challenge.
- **Do not** invent MFE from Module_ATR entry blotters.
- APPLY only if HOLD Choice beats static time-stop/giveback on Challenge DD **and** does not increase orig_stop rate.

### 3.3 Two-stop remint + occupancy remint + G8 15m

- **Tape:** `just_closed_siblings.json` (live path claimed under `pipeline_state/ultimate_book/operator/judgment/state/`). Abandoned twin `judgment/live/just_closed_siblings.json` **must not** be used (`two_stop.py` already skips it).
- Autopsy families: `two_bar` / `rejection_wick` / `isolated_spike` (WMB scope).
- Isolated reentry ≥15m remains legal for **other** sleeves — do not collapse into 2-stop COUNT.
- Integer COUNT stays fail-closed if Jev dark.

### 3.4 Pretrade cost Score (`cost_screen_spread_r` / spread_geometry / `pretrade_cost`)

- **Tape:** Challenge legs refused for spread_r vs those that would have been +EV. GBPJPY comment in `book_owner` (~0.23 spread_r on ~8.7 pip stop) is a **hypothesis to test**, not a number to APPLY.
- Module_ATR blotters **do not** carry live spread. Cost prove is Challenge-tick-true or **BLOCKED**.
- Clamp: cannot add size from “cheap spread”. Cost-never-kill inverted into size-up is **forbidden** (inventory do-not list).

### 3.5 Silent drops (A8 / damage / learning / vp)

- Reconstruct from admission flags default-off vs on using **same** Module_ATR metals blotters (XAU/XAG) for confluence; Challenge closed deals for damage (leak-free prior days only — module already specifies).
- A8 thresholds are train-frozen (`FRESH_BARS_MAX=5`, `VOL_CAP=1.8`, K=3). **Do not re-fit.**
- Report n dropped, sumR of dropped vs admitted, DD.

### 3.6 Admission soft Score (derisk / kelly / stress)

- Challenge equity path **MISSING this seat**. Replay only if governor_state can be rebuilt from Challenge deals. Else **BLOCKED** for APPLY; SHADOW labels OK.
- Hard walls (`circuit_breaker_open`, `max_dd_limit_reached`, `fail_closed:*`) **not** in the prove-to-soften set.

### 3.7 Companion pause / cooldown

- Needs companion control-state logs. **MISSING on box mirrors as a Challenge tape.** SHADOW only until host logs exist.

### 3.8 EURUSD KEEP_ALL / GBPJPY conflict / XAG

- GBPJPY: Module_ATR blotters FOUND — run conflict-set bar identical to V2 (sumR_select vs keep_all vs random). Widen pack exists.
- XAG: blotters FOUND + `XAGUSD_METALS_CONFLICT_HIST_PROVE_20260920`.
- EURUSD: V2 FAIL on Module_ATR combined. KEEP_ALL is identity (do not stand one leg). **Not** an APPLY evidence row for global select.

### 3.9 Policy C COMPLETE_STATE expand (session 05)

- Replay Challenge tape with expanded state vs 4-voter starve. Metrics: fire_rate, sumR, DD vs current Policy C.
- `STATE_MISSING` stays skip (no invent).

### 3.10 Train-row harvest (session 18)

- Pair Challenge closes win/lose with COMPLETE_STATE snapshot. Module_ATR year_le0 is a **geometry tag**, not a harvested R mix-in.

---

## 4. APPLY ladder (Chair only)

| step | who | action |
|---|---|---|
| 0 | this session | DESIGN + receipts; `place=false` |
| 1 | Chair | LABEL inventory `never_place` → default-until-prove |
| 2 | hist | scoped XAU conflict (already PASS numbers) — **still Chair land**; do not flip global APPLY |
| 3 | hist | GBPJPY conflict widen; XAG; silent-drop forensics |
| 4 | hist | place_fluid shadow vs writer (needs events.jsonl) |
| 5 | hist | remint/two-stop/occupancy |
| 6 | hist | hold/exit Challenge closes |
| 7 | Chair | ENFORCE scoped APPLY flags one family at a time |
| 8 | Chair | place Choice APPLY only if step 4 PASS |

Never skip to 8 from Module_ATR entry blotters.

---

## 5. Anti-oracle / split

Reuse existing anti-oracle splits if present (`jev_anti_oracle_time_split.json`, `jev_cf_D_anti_oracle_*`). Do not prove on the same year used to freeze A8 thresholds. 2026-like fail years on three_fresh (`2014,2015,2018,2021,2026` in CF_C) stay STAND geometry, not a fit target.

---

## 6. Blockers (prove cannot complete until)

1. VPS Admin unreachable — live skip_reason histogram + events.jsonl **MISSING**  
2. Policy C / two_stop **unwired** on PR41 fire path — live-effect prove would overclaim  
3. Hold/exit Module_ATR blotter **MISSING**  
4. NZD Module_ATR blotter **MISSING**  
5. Host news join may be STATE_MISSING — abstain event questions (Noul ~0.5)

These are **honest BLOCKED** for APPLY, not for SHADOW design.

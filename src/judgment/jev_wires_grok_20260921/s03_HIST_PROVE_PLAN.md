# HIST PROVE PLAN — sleeve_select conflict cells

**session:** `03_sleeve_select_global_conflicts`  
**as_of_ict:** `2026-09-21T06:15:00+07:00`  
**lens law:** Module_ATR honesty — **no invented ATR / regime**. Dig_3R is a **separate** lens and is **never** merged into Module_ATR sumR. Challenge book is a **separate** lens. Cost is measurement-only, never a kill.

This session **does not** flip `GTOS_JEV_SLEEVE_SELECT_APPLY`. Chair APPLY only after the gates below. `place=false` here; place path OPEN in design after prove.

---

## 0. Module_ATR contract (do not invent)

| field | law |
|---|---|
| 1R | ATR(14) at **signal bar** (already on blotter `atr` / `R_ATR`) |
| entry | next open (affinity scoreboard) / blotter `entry_px` as stamped |
| managed exit | structure stop **OR** time_stop @ **32 M15 bars** (~8h) |
| fill | `geometry_proxy_ohlc_touch_Module_ATR_affinity_structure_or_time_stop32_NOT_broker` |
| forbidden for Choice | `miss`, `year_le0`, `R`, `exit_class` of the trade under decision |
| φ | standing capability from yearly avg_R — not this-trade R |
| news | `STATE_MISSING` ok — never invent NEWS_PROTOCOL |
| stitch | GBPUSD/USDJPY `gap_hours=983.75` **not continuous** — no silent stitch |
| live vs proxy | stamp `detector_id`; live vss 2R/48 ≠ ORB proxy; live `sub_mid_dn_revert` ≠ SHORT |

If a blotter / tape is missing: **INSUFFICIENT / STATE_MISSING**. Do not fabricate conflict numbers (XAG SKIPPED is the template).

---

## 1. Tapes (found)

| instrument | path | honesty |
|---|---|---|
| XAUUSD | `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` | PRIMARY multi-year |
| EURUSD | `/workspace/audit-merge/markets/tapes/EURUSD_M15.csv` | PRIMARY; asian_fade yearfold cells — **no per-trade blotter on box** |
| GBPJPY | `/workspace/gtos/_swarm_land_tip/extract/data/historical/GBPJPY_M15.csv` | 2022-03-28 → 2026-04-17; no pre-2022 TRAIN |
| XAGUSD | swarm historical + metals blotters | KEEP n=1 → conflict SKIPPED |
| GBPUSD | swarm historical | **NOT continuous** (gap ≈983.8h) |
| USDJPY | swarm historical | **NOT continuous**; NARROW |
| BTCUSD | `/workspace/audit-merge/markets/tapes/BTCUSD_M15.csv` | research sidecar; `banned_for_aplus`; park |
| Challenge book | login `0` closes (hydrate from 2026-08-10; n=38 cited) | **SEPARATE lens** |

PR41 also holds `.../_pr41_land/ai-trading-agent/data/XAUUSD_M15.csv` and `data/historical/*` — use **one** tape per instrument; do not stitch silently.

---

## 2. Blotters (found — Module_ATR)

| cell | blotter |
|---|---|
| XAU three_fresh | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` |
| XAU spring | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl` |
| GBPJPY vss proxy | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl` (n=818) |
| GBPJPY sub_mid SHORT | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl` (n=2057) |
| XAG metal_session | `blotter_Module_ATR_XAGUSD_metal_session_reversion_20260920.jsonl` |
| XAG NARROW siblings | `..._metals_core_...` / `..._sub_xvol_pullback_...` |

**MISSING (honest):**

- Per-trade asian_fade blotter (yearfold cells only)
- GBPJPY spring / three_fresh / london_orb **day-overlap vs sub_mid** blotter join (affinity scoreboard has year sums; deepen says unproved)
- XAU `dsp_expanding_up_staircase` Module_ATR conflict blotter
- Challenge full-calendar YTD hydrate (window starts 2026-08-10)

Do not invent those joins.

---

## 3. Already-proved receipts (reuse — do not redo)

### 3.1 XAU three_fresh × spring — **PASS** (APPLY candidate #1)

Cite: `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920` + `JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920`

| metric | value |
|---|---:|
| unit | **day overlap** (honest) |
| n_conflicts | 2353 |
| sumR_select (spring) | **+235.3602** |
| sumR_keep_all | **−74.7197** |
| sumR_random | −37.3598 |
| beats keep_all | True |
| beats random | True |
| pick hist | spring × 2353 |
| Choice hist (then) | C_SIZE_TRIM × 2353 — **size trim is not the APPLY policy**; APPLY is **stand three_fresh, keep spring** |

YTD 2026 file-exit honesty (separate row, do not hide): three_fresh **−53.86** / spring **+14.25**. Haircut stays on three_fresh.

**Gate to scoped APPLY:** already PASS. Remaining: wire `evaluate()` + admission helper so APPLY is Jev-judged, not only static pick. Then Chair `GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT=1`. Global stays 0.

### 3.2 GBPJPY opp-side vss LONG × sub_mid SHORT — **PASS** (APPLY candidate #2)

Cite: `GBPJPY_VSS_UPLOW_x_SUBMID_SHORT_CONFLICT_DEEPEN_20260920` + `GROK_KEEP_HIST_PROVE_20260920`

| window | n_days | sumR_select (vss LONG) | sumR_keep_all | beats |
|---|---:|---:|---:|:---:|
| full cal | 420 | **222.3549** | 127.6098 | Y |
| hold 2025–26 | 140 | 48.59 | 42.79 | Y |
| train ≤2024 | 280 | 173.76 | 84.82 | Y |
| ytd 2026 cal | 31 | 20.17 | 21.90 | **N thin** |
| full time-overlap | 328 | **284.98** | 192.86 | Y |

ytd 2026 thin FAIL is honesty — do not hide. Full/hold/train PASS is the bar.

### 3.3 GBPJPY same SHORT vss SHORT × sub_mid SHORT — **PASS** (same scoped bit)

| window | n_days | sumR_select (sub_mid) | sumR_keep_all | beats |
|---|---:|---:|---:|:---:|
| full cal | 272 | **341.3318** | 177.9396 | Y |
| time overlap | 162 | **379.55** | 247.16 | Y |

vss SHORT is a KILL leg (φ=−0.049).

### 3.4 GBPJPY static φ mixed BOTH — **FAIL — do not wire**

n=692 select 246.6 vs keep_all 305.5. Envelope refuse that picker.

### 3.5 EURUSD asian_fade × Package B — **KEEP_ALL identity** (not pick PASS)

n_years=13 both positive; signs-disagree n=0; keep_all=2350.4576. Pick-one cannot beat keep_all. Scoped bit is KEEP_BOTH, **not** a conflict-stand rule.

### 3.6 Global combined — **FAIL**

V2 Module_ATR combined n=2366 select 1161.99 vs keep_all 2275.74. **Do not flip global APPLY.**

### 3.7 XAG — **SKIPPED** (not FAIL)

n_KEEP=1. No conflict numbers.

### 3.8 BTC / Teddy — **FAIL + banned_for_aplus** → park.

### 3.9 Widen GBPJPY three_fresh × spring **year** window — **FAIL**

n=5 years select 296.93 vs keep_all 985.62 (C_SIZE_TRIM). **Not** a day-overlap prove. SHADOW until day join exists.

---

## 4. Replay metrics (every cell, same schema)

For each conflict cell, emit a receipt with:

| metric | def |
|---|---|
| `n` | conflict windows (prefer **day** overlap; year only if no day blotter — stamp `unit=year` honesty) |
| `sumR_select` | Module_ATR R of the chosen sleeve (KEEP_A or KEEP_B); STAND → 0 |
| `sumR_keep_all` | sum of both sleeves on those windows (double-count warning: pair sums ≠ book P&L — prefer **day unit** as deepen did) |
| `sumR_random` | 0.5*(Ra+Rb) or coin-flip sleeve |
| `beats_keep_all` | sumR_select > sumR_keep_all |
| `beats_random` | sumR_select > sumR_random |
| `fire_rate` | n_fires_select / n_candidate_days (select vs keep_all vs stand) |
| `DD` | max drawdown of the select equity curve in R (Module_ATR) |
| `Choice_hist` | KEEP_A / KEEP_B / STAND / KEEP_BOTH counts |
| `n_jev_dark` | evaluate skip count (fail-closed must not change fire rate vs SHADOW) |
| `lens` | `Module_ATR` \| `Challenge_book` \| `Dig_3R` — **never mixed in one sumR** |

**Chair bar (v2, still law):**  
`sumR_select > sumR_keep_all_on_conflicts` **AND** `sumR_select > sumR_random` on the conflict set.  
Not full-year keep-all geometry (v1 FAIL).

**Additional gates this pass (owner fire-rate):**

1. Fire rate of scoped APPLY must not exceed keep_all fire rate on the stood sleeve (that is the point of STAND).
2. DD_select ≤ DD_keep_all **or** explicit Chair accept of extra DD with sumR lift.
3. Poison: injecting miss/year_le0/R/exit_class must not change Choice (`poison_ok=true`).
4. Jev-dark replay: fire rate == SHADOW keep_all (no silent hist-pick APPLY).
5. Live-tag replay (if Challenge n sufficient): **separate** receipt; do not merge.

---

## 5. Work still required (unproved cells)

Run **only** if blotters exist; else stamp INSUFFICIENT.

| cell | unit needed | APPLY? |
|---|---|---|
| GBPJPY spring LONG × sub_mid SHORT | day overlap Module_ATR | SHADOW until PASS |
| GBPJPY three_fresh LONG × sub_mid SHORT | day overlap | SHADOW |
| GBPJPY london_orb × sub_mid SHORT | day overlap | SHADOW |
| GBPJPY three_fresh × spring | **day** overlap (year FAIL) | SHADOW |
| XAU expanding_up_staircase × spring/three_fresh | day overlap | SHADOW (blotter MISSING) |
| EURUSD KEEP_BOTH vs pick-one | yearfold already enough; optional trade blotter if found | draft scoped KEEP_ALL |
| XAG | need 2nd KEEP | no APPLY |
| USDJPY / GBPUSD | tape gap | no APPLY |
| Challenge book conflicts | full hydrate MISSING | separate lens only |

Replay runner to extend (do not land APPLY):

- `JEV_SLEEVE_SELECT_HIST_PROVE_V2_RUN_20260920.py`
- deepen scripts behind `GBPJPY_VSS_UPLOW_x_SUBMID_SHORT_CONFLICT_DEEPEN_20260920.json`
- v4 `sleeve_select_choice` with **poison_ok** already in `__main__`

Shadow sidecar `jev_sidecar/sleeve_select/2026-09-20.jsonl` **n=1** is **not** proof.

---

## 6. Gate to APPLY (Chair verbs — this session does not APPLY)

| APPLY bit | hist gate | code gate | this session |
|---|---|---|---|
| `GTOS_JEV_SLEEVE_SELECT_APPLY` global | combined PASS (currently FAIL) | never default-on | **do not flip** |
| `..._APPLY_XAU_CONFLICT` | V2 XAU PASS (done) | evaluate() wired + `should_stand_three_fresh_*` present + fail-closed tests | DESIGN only |
| `..._APPLY_GBPJPY_CONFLICT` | side-aware PASS (done); **not** mixed BOTH | sides resolved in COMPLETE_STATE; unresolved → STAND | DESIGN only |
| `..._APPLY_EURUSD_KEEP_ALL` | KEEP_BOTH identity (done as not-pick) | Choice KEEP_BOTH not pick-one | draft |
| any unproved cell | PASS on day Module_ATR | SHADOW until then | SHADOW |

Place: after scoped APPLY, writer may print the KEEP_* sleeve. Jev Choice PLACE|STAND|DELAY is a **later** family (sessions 04/14). Default `order_send` off until that prove. This session never places.

---

## 7. Counterfactual policies to score (same tape)

On each conflict window, score:

1. `keep_all` — both fire (baseline)
2. `hist_static_pick` — current `resolve_scoped_conflict_choice`
3. `jev_choice` — replay stored evaluate answers (or v4 rule as proxy until evaluate harvest)
4. `stand_both`
5. `random_sleeve`
6. `phi_clear_winner` — **expect FAIL** on GBPJPY mixed BOTH (do not wire)

Report Δ sumR, fire_rate, DD, n. Graduate only if (3) ≥ (2) ≥ keep_all on the scoped cell **or** Chair accepts (2) as the APPLY policy with Jev as shadow-until-beats.

Honesty: v4/v2 Choice hist was almost all `C_SIZE_TRIM` because voters were incomplete on research stamps. **Do not** treat 0.75× keep_all as the APPLY policy. APPLY is pick/stand, size is a different wire (session 06).

---

## 8. Challenge tape (login 0)

Found as **separate** V2 row: n_conflicts=1, select 2.265 vs keep_all 2.01.  
**MISSING:** full Challenge conflict blotter join for XAU three_fresh×spring and GBPJPY side-aware on live tags.

Plan: when closes hydrate is complete, replay scoped rules on **live tags** (not proxies). Until then: Module_ATR proxy prove stands; live-tag APPLY remains NARROW / Chair-risk. Stamp `live_tag_unproved=true` on any scoped APPLY land card.

---

## 9. Locks

- no host-mesh
- no NEWS invent
- no Dig3R merge
- no global APPLY flip
- Policy C APPLY untouched
- Teddy park
- cost never kill
- never_broker_place this session
- affinity instrument × sleeve

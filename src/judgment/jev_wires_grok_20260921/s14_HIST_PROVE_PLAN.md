# HIST-PROVE PLAN — place_fluid Choice PLACE|STAND|DELAY

**as_of_ict:** `2026-09-21T06:05:12+07:00`  
**session:** `14_place_fluid_hist_prove_apply`  
**status:** PLAN (not run this session). Queue item #1 from `PLACE_FLUID_HIST_PROVE_QUEUE_20260921.md`.  
**login:** Challenge `0` only. Verification `0` quarantined.  
**place this session:** false. No broker. No `order_send`.

Owner: if hist shows Jev better at place → prove → APPLY. Shadow LABEL is **not** proof.

---

## 0. Honesty first — three R universes + two tapes

### 0.1 Never merge lenses

| lens | what it is | R unit | use in this plan |
|---|---|---|---|
| **Dig_3R** | structure box-stop −1.0R / +3.0R TP / 32-bar time_stop | Dig R | **cite only**. Do not add to Module_ATR sumR. Do not score place APPLY on Dig R. |
| **Edge_ATR** | instrument Edge packs (variable exits) | ATR-R (Edge) | **cite only**. |
| **Module_ATR** | recovered module exit_shape **stop −0.75 ATR / tgt +6.0 ATR** | ATR-R (Module) | **PRIMARY hist lens for counterfactual place/stand on KEEP sleeves**. |

**Never** `sumR_Dig + sumR_Edge + sumR_Module`. Separate columns. Gap inventory do-not: merge Dig3R Module_ATR lenses.

### 0.2 Fill-model honesty (Module_ATR blotters)

Cited from THREE_FRESH / SPRING yearfolds:

| axis | value |
|---|---|
| model | `geometry_proxy_ohlc_touch` |
| NOT | broker fill · module-exact runtime · Dig structure stop · Edge variable exit |
| entry | signal-bar **close** |
| stop | `entry − 0.75 × ATR14(signal)` |
| target | `entry + 6.0 × ATR14(signal)` |
| same-bar | stop before target (conservative) |
| time_stop | 512 bars — module file has **no** time_stop; residual MTM labeled time_stop |
| missing vs live module | `stay_timing` / `peer_panel` / admission / TradeIntent book path |
| verdict | **APPROXIMATION**. Geometry proxy ≠ live module. |

Yearfold receipts stamp `place=false` / `promote=NO` because of this approximation — **research honesty, not eternal never_place**. This plan re-opens place **only if** Choice over COMPLETE_STATE beats writer-as-is **and** Module_ATR counterfactual still holds under the same approximation (declare it on the receipt).

### 0.3 Two tapes that must not be mixed

| tape | path | what it measures | n (found) |
|---|---|---|---|
| **Challenge writer actuals** | `challenge_shadow_20260917/deals_since_20260909.jsonl` + `vps_hydrate/challenge_0_closed.json` | live FTMO prints, broker R/money | 46 closed (6W/40L), net **−4487.73** |
| **Challenge shadow pack** | `.../shadow.jsonl` | gold_state + fluid stamps + Jev answers | **n=97** (open=1, slate=40, slate_skip=10, deal_close=46) |
| **Challenge bars** | `XAUUSD_M15/H4/D1.csv` + `multi/GBPJPY_M15/H4.csv` … | Challenge-true OHLC (`time_utc` already −3h) | present |
| **Module_ATR blotters** | `blotter_Module_ATR_XAUUSD_dsp_{three_fresh,spring}_*.jsonl` + GBPJPY vss/sub_mid | multiyear geometry proxy ATR-R | three_fresh HOLD n=4345; spring HOLD n=2217 |
| **Module_ATR yearfold tape** | `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` | 2014-01-02 → 2026-06-17 | **present** |

**Do not** score Module_ATR sumR on Challenge money PnL, or Challenge fire-rate on yearfold geometry fills, as if they were one number.

### 0.4 ATR / regime — do not invent

- ATR used in Module_ATR blotters is **ATR(14) on the named yearfold tape**, already in those jsonl rows (`R_ATR` / `R`). Hist runner **reads** it. Do not recompute a different ATR and call it Module_ATR.
- `regime_tag` / `conf_band` on COMPLETE_STATE: use S14 when assembled; else **`PENDING`**. `full_state_dark=true` if required fields missing. Place Choice **STAND** when dark.
- News: `news_join` object or `STATE_MISSING`. Empty spine ≠ no HIGH. Invented HIGH fails the prove (`fluid_prove._invented_high`).

---

## 1. What is already proved (LABEL only) — not this bar

Re-score of `_pr41_land/.../challenge_shadow_20260917/shadow.jsonl` (n=97):

| gate | n_decidable | n_moved | label bar (20/5/2) |
|---|---:|---:|---|
| FLUID-PLC-001 veto_corr | 97 | 97 | met |
| FLUID-PLC-002 veto_event | 97 | 97 | met |
| FLUID-PLC-003 veto_cost | 47 | 47 | met (cost-complete) |
| FLUID-PLC-004 veto_occupancy_label | 97 | 97 | met |
| FLUID-PLC-005 cost_vs_tape | 47 | 47 | met |
| FLUID-PLC-006 stale_standing | 40 | 40 | met (slate) |
| FLUID-PLC-007 last_refusal_class | 97 | 22 | met |

Wave L already APPLIED_NAMED PLC-001 as **label**. Inventory `APPLIED_NAMED` ≠ place judge.

**Missing for place:** paired `place_now` vs **writer_would_place** vs **realized R**, plus Module_ATR counterfactual STAND on losers / PLACE on skipped +EV.

---

## 2. Writer actuals baseline (Challenge, honest)

From `deals_summary.md` (since 2026-09-09, pulled 2026-09-17):

| | |
|---|---|
| n closed | 46 |
| W/L | 6 / 40 |
| net | **−4487.73** |
| KEEP prints that paid | `dsp_spring_cl` n=1 +453.14; `vss_fxcross_l` n=2 +100.53; `dsp_three_fre` n=4 +52.20 |
| envelope should have blocked | bleed, xa_huge, orb_crypto, idxrev dominate losses |

Place hist must **not** “save” the book by placing more bleed. Envelope hard-offs stay. Place Choice is judged on **KEEP-family / affinity sleeves** (spring, vss, three_fresh as research overlay not live_armed).

Shadow pack `slate_skip` n=10 is the **writer-said-no** set — primary counterfactual for “would PLACE have been better?”

---

## 3. Module_ATR KEEP-sleeve baselines (cite, do not re-invent)

### XAUUSD × three_fresh (Module_ATR only)

| split | n | sumR Module_ATR | avgR | WR |
|---|---:|---:|---:|---:|
| TRAIN ≤2021 | 6894 | +176.8235 | +0.0256 | 0.1150 |
| HOLD ≥2022 | 4345 | **+315.1432** | +0.0725 | 0.1220 |

### XAUUSD × spring (Module_ATR only)

| split | n | sumR Module_ATR | avgR | WR |
|---|---:|---:|---:|---:|
| TRAIN | 3442 | +225.3135 | +0.0655 | 0.1209 |
| HOLD | 2217 | **+261.0000** | +0.1177 | 0.1286 |

Selector hist (separate, already PASS): XAU three_fresh×spring conflict **sumR_select=+235.36 vs keep_all=−74.72** n_conflicts=2353. Place hist **must not double-count** that selector edge. Place Choice is: given the **selected** sleeve, print now / stand / delay.

### GBPJPY Module_ATR blotters (found)

- `blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl`
- `blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl`

Selector side-aware already PASS (cite expand doc). Place hist on GBPJPY is **phase 2** after XAU.

### XAG

NARROW — no conflict set. **No scoped place APPLY** this pass.

---

## 4. Recipe — three phases

### Phase A — Challenge shadow log vs writer actuals (fire-rate honesty)

**Input:** `shadow.jsonl` n=97 + `deals_since_20260909.jsonl`.

For each row:

1. Build COMPLETE_STATE (gap schema). Missing news → `STATE_MISSING`. Missing regime → `PENDING`. Count `n_incomplete`.
2. POST `evaluate(state)` with `place_now` + PLC voters (`GTOS_JEV_MAX_CALLS=500000`). If Jev dark → record `STAND` + `jev_dark=true` (these rows **cannot** count toward PLACE APPLY pass).
3. Writer actual:
   - `deal_close` / `open` → `writer_placed=true`
   - `slate_skip` → `writer_placed=false` + named `last_refusal_class`
   - `slate` without deal → `writer_placed=false` (standing)
4. Pair: `choice` vs `writer_placed` vs realized R (Challenge money R if named; else `R_MISSING` — do not invent).

**Metrics (Phase A):**

| metric | definition |
|---|---|
| n | rows with Jev ok and envelope would have allowed a print |
| n_jev_dark | skipped/error |
| fire_rate_writer | writer_placed / n |
| fire_rate_choice | choice==PLACE / n |
| n_agree | PLACE↔placed or STAND/DELAY↔not-placed |
| n_choice_stand_on_loser | STAND/DELAY where writer placed and realized R < 0 |
| n_choice_place_on_skip | PLACE where writer skipped and Module_ATR/Challenge R would have been > 0 (only if R named) |
| sumR_writer | sum realized R on writer_placed (Challenge R; declare currency) |
| sumR_choice | counterfactual: PLACE rows take named R; STAND/DELAY take 0 |
| maxDD_writer / maxDD_choice | running sum drawdown |
| invented_high | must be 0 |

**Phase A PASS (necessary, not sufficient for APPLY):**

- n_jev_ok ≥ 20 on KEEP-family rows (same spirit as label min_decidable)
- invented_high = 0
- fire_rate_choice ≤ fire_rate_writer **or** (fire_rate_choice > writer **and** sumR_choice > sumR_writer)
- sumR_choice ≥ sumR_writer on KEEP-family subset
- maxDD_choice no worse than maxDD_writer by more than **0.5 R** (Challenge R) on that subset
- envelope hard-off rows: Choice must STAND 100%

If Challenge R is `R_MISSING` on most rows, Phase A is **fire-rate / agreement only** and **cannot alone open APPLY**. Say so on the receipt.

### Phase B — Module_ATR counterfactual (PRIMARY sumR / DD)

**Input (XAU first):**

- `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`
- `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl`
- yearfold tape `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv`
- selector conflict cells from `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920` (which sleeve would be selected)

**Method:**

1. Walk HOLD ≥2022-01-01 (frozen split). TRAIN is calibration only; **PASS is HOLD**.
2. At each Module_ATR signal row, assemble COMPLETE_STATE **from named blotter fields only**. If occupancy/news/account absent → stamp `STATE_MISSING` / `n_incomplete`. Do **not** invent ATR: use row `R` / `R_ATR` / `atr14` as stored.
3. `evaluate()` `place_now`. Jev dark → STAND (row excluded from PLACE-benefit, included in dark count).
4. Three policies (separate columns):

| policy | action |
|---|---|
| `always_place` | take every Module_ATR signal (yearfold baseline) |
| `writer_like` | if Challenge occupancy/cost analogues say skip, skip; else place (best-effort map; if unmappable, equal to always_place and **declare**) |
| `jev_choice` | PLACE → take Module_ATR R; STAND/DELAY → 0 |

5. Busy_until / serial: honor blotter `busy_until` so fire-rate is not fantasy overlap.

**Phase B metrics (Module_ATR R only):**

| metric | always_place | jev_choice |
|---|---|---|
| n_signals HOLD | three_fresh 4345 / spring 2217 | n_PLACE |
| sumR | +315.14 / +261.00 (cite) | **measure** |
| avgR | cite | measure |
| maxDD | measure from blotter path | measure |
| fire_rate | 1.0 of signals | n_PLACE / n_signals |
| WR | cite | measure |

**Phase B PASS (XAU scoped):**

1. `sumR_jev_choice` **>** `sumR_always_place` on HOLD **or** (sumR not worse **and** maxDD strictly better **and** fire_rate down).
2. Prefer the selector-aware variant: on three_fresh×spring **conflict days**, Choice should STAND three_fresh more often (aligns with select hist +235 vs −75) — **report**, do not silently merge with selector APPLY.
3. maxDD_jev no worse than always_place.
4. n_PLACE ≥ 20 on HOLD (not a no-op).
5. invented_high = 0.
6. No Dig_3R numbers on the PASS line.
7. Geometry-proxy disclaimer **copied onto the receipt**.

If `sumR_jev_choice` < always_place: **FAIL**. Stay SHADOW. Do not APPLY. (Standing off losers must more than pay for missed winners.)

**Phase B-GBPJPY** (after XAU PASS or in parallel report): same recipe on the two GBPJPY Module_ATR blotters. Side-aware: opp-side prefer vss LONG; same SHORT prefer sub_mid — **as state inputs**, not as a second selector APPLY.

### Phase C — Shadow log vs writer actuals **on live Challenge window** (couple A+B)

Join Phase A tickets to KEEP sleeves only. Ask: would `place_now` have STAND the bleed/xa_huge/orb/idxrev prints? **Must be yes** (envelope already should; Choice is a second belt). Would it have still PLACE the spring winner `+453`? If it STANDs the only spring winner and also fails Phase B, FAIL.

n is small (46 closes). Phase C is a **sanity gate**, not the sumR engine. Declare `n_small=true`.

---

## 5. APPLY gate (Chair later)

All of:

1. Phase A invented_high=0, KEEP-family sumR_choice ≥ sumR_writer (or R_MISSING declared and fire-rate not exploded).
2. Phase B XAU HOLD PASS on Module_ATR columns.
3. Phase C envelope hard-off STAND=100%.
4. Prove receipt written under `judgment/live/prove/place_fluid/` with `proven=false` until Chair NAMES.
5. Scoped env only: `GTOS_JEV_PLACE_FLUID_APPLY_XAU=1` — **not** global `GTOS_JEV_PLACE_FLUID_APPLY`, **not** `GTOS_JEV_FLUID_GATES_APPLY`, **not** `GTOS_JEV_SLEEVE_SELECT_APPLY`.
6. Writer hook fail-closed if Jev dark.
7. Affinity XAUUSD × (spring KEEP; three_fresh overlay as conflict STAND candidate).
8. GBPJPY scoped bit only after Phase B-GBPJPY PASS.

**FAIL → remain SHADOW.** Owner place path stays OPEN (do not re-encode eternal never_place). Re-run when COMPLETE_STATE composer (session 10) fills occupancy/news.

---

## 6. Runner constraints

| | |
|---|---|
| cwd / OUT | this session dir for receipts; live prove dir only on Chair land |
| `GTOS_JEV_A1_CALL` | 1 for hist |
| `GTOS_JEV_MAX_CALLS` | 500000 |
| local fallback | STAND only — **cannot PASS APPLY** on local instruments |
| broker | forbidden |
| host-mesh / VPS SSH | forbidden |
| April historical bars | forbidden (not Challenge tape) |
| redacted_account / W7 | do not touch |

Draft runner: `PLACE_FLUID_HIST_PROVE_RUN_DRAFT.py` (this OUT). Not executed as APPLY.

---

## 7. Blockers (honest)

| blocker | impact |
|---|---|
| `place_now` question **not in** `symbol_fanout_questions` yet | hist cannot call the real Choice until patch lands (research wrapper may inject questions in-runner) |
| COMPLETE_STATE composer is session 10 | occupancy/account/conflict_set may be thin on Challenge shadow rows → high `n_incomplete` → many STAND |
| Module_ATR blotters lack live occupancy/news | Phase B state is starved; must stamp STATE_MISSING not invent |
| Challenge n=46 closes | Phase C underpowered; Module_ATR HOLD is the sumR engine |
| VPS Admin unreachable | cannot diff live writer events.jsonl vs box deals |
| Default `GTOS_JEV_MAX_CALLS=200` | hist will exhaust unless raised |
| Geometry proxy ≠ live module | even a PASS is **scoped research** until TradeIntent path is replayed |
| Yearfold `place=false` receipts | do not misread as Chair VETO of this plan |

---

## 8. Copy-block for Chair (from queue)

```
Chair ENFORCE place_fluid hist-prove FIRST (Module_ATR or Challenge file-exit).
Reuse FLUID-PLC backlog + COMPLETE_STATE gap inventory.
PASS only if Choice PLACE beats STAND/DELAY on conflict/honest windows.
Do not flip fluid APPLY global. Draft scoped place APPLY receipt if PASS.
Owner place unlock live. machineId 7cfa… for live reads when Shell is up.
```

This session **does not** speak Chair verbs. Next Chair actions are listed in `RECEIPT.md`.

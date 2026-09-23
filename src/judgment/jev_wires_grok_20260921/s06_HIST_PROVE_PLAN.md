# HIST-PROVE PLAN — Score size_mult + CA_SIZE (Module_ATR honesty)

**session:** `06_apply_size_ca_size`  
**as_of_ict:** `2026-09-21T06:04:07+07:00`  
**law:** hist / replay Challenge tape **before** any APPLY that changes live fire rate **or** dollars at risk. Size cannot refuse (fire count must not change). Size **can** change DD and payout path.  
**this session:** plan only. `apply: false`. `never_broker_place: true`.

---

## 1. What is being proved

Three counterfactuals on the **same** Challenge fires (already admitted; no new skips):

| id | treatment | vs baseline |
|---|---|---|
| **A** `local_product` | today’s PR41 combined = flow × cost × ca (static CA constants) | as-traded if haircut was live; else unit-R × 1.0 |
| **B** `jev_size_mult` | Score `size_mult` overlay (flow clamp) × cost × ca | A |
| **C** `jev_ca_size_mult` | flow × cost × Jev Score `ca_size_mult` (veto clamp) | A |
| **D** `jev_joint` | B+C together (and optional FLUID-SIZ into combined as **separate** column) | A |

Pass of C is the gap-inventory `#7 CA_SIZE_APPLY` candidate. Pass of B is “expand apply_size from tilt-only to Choice/Score over COMPLETE_STATE”. **Neither APPLY this session.**

Fire rate invariant: `n_fires(B)=n_fires(C)=n_fires(D)=n_fires(A)`. If any treatment would skip/refuse → **FAIL** (envelope broken).

---

## 2. Challenge tape paths (present on this box)

Primary (Challenge-true, login `0`, ns `operator`, magic `0`):

| path | contents |
|---|---|
| `/workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent/judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl` | n=97: 1 open / 40 slate / 10 slate_skip / 46 deal_close |
| `.../XAUUSD_M15.csv` | 1597 bars, `2026-08-25T00:00:00Z` → `2026-09-17T10:30:00Z`, `time_utc` already true UTC |
| `.../XAUUSD_H4.csv`, `.../XAUUSD_D1.csv` | HTF |
| `.../deals_since_20260909.jsonl` | pulled 2026-09-17T10:40:57Z; closed **46**; W/L **6/40**; net **−4487.73** |
| `.../events_since_20260915.jsonl` | news spine join |
| `.../multi/{EURUSD,GBPUSD,USDJPY,US30,GBPJPY,...}_{M15,H4}.csv` | CA peers; April historical refused |
| `.../ticket_293332188.json` | leave-orig holdout |

Prior prove receipts to **cite, not re-run as live=1.0 bars**:

- `WAVE_E_RECEIPT.json` — FLOW+COST PROVED_SHADOW, n=87, n_xau_sufficient=28, n_flow_moved=26, n_cost_moved=20, live tilts were 1.0 at that moment
- `CA_SIZE_SHADOW_PROVE.json` — n=97, n_moved=95, n_distinct=7, **stale lock fields** (pre-NAME 04:11Z)
- `APPLIED_NAMED.json` — “Do not re-run shadow_prove on a live-moving pack”

**MISSING / do not wear as Challenge:**

- Live VPS `apply_receipt.jsonl` at `host-local\redacted_host\repo\judgment\astra\lab\a1\apply_receipt.jsonl` — host-mesh UNREACHABLE this seat. Box copy is pytest (2 lines, 2026-09-20T13:30:07Z).
- `apply_claimed` live place row — **MISSING** (honest). Plan cannot use live tilted fills until VPS re-read.
- April `exports/multi_instrument/*`, `data/historical*`, `data/DXY_D1.csv`.

Deals summary (as-traded dollars, **not** Module_ATR R):

Hard-off sleeves (bleed, xa_huge, orb_crypto, idxrev) dominate losses — size wire must **not** re-enable those (house_hard_off → tilt 1.0 / apply false). Study sleeves include `dsp_three_fre` (net +52.20), `dsp_spring_cl` (+453.14), `vss_fxcross_l` (+100.53). Affinity: size hist on XAU study first.

---

## 3. Module_ATR honesty (non-negotiable)

Live Challenge F5 geometry is **sleeve orig stop / house plan_r**, not Module_ATR `stop0.75 / tgt6.0`.

Three **separate** R universes exist on disk. **Never sum them. Never convert one into another.**

| lens | where | use in this prove? |
|---|---|---|
| **Challenge as-traded** | `deals_since_20260909.jsonl` profit / stop_dist / cost_R if named | **PRIMARY** dollar + unit-R |
| **Dig_3R** | three_fresh Dig blotters | **NO** for size APPLY gate |
| **Edge_ATR** | Edge blotters / `R_ATR` when lens≠Module_ATR | **NO** merge |
| **Module_ATR** | `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`, `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl`, GBPJPY/XAG Module_ATR blotters, `THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.json` | **SIDE column only** if the row’s `lens==Module_ATR`. If ATR is not named on the Challenge intent, field is **STATE_MISSING** — do not compute ATR from M15 range and call it Module_ATR |

Rules:

1. If `geometry.stop_atr` / `target_atr` is **not** on the Challenge state row → do not invent it for `geo_size` / `size_mult`.
2. Module_ATR yearfold `honesty`: “APPROXIMATION of Module_ATR fills — geometry proxy ≠ live module TradeIntent path”. Treat as **research lens**, not Challenge payout R.
3. Size overlay PASS/FAIL uses Challenge as-traded **usd** and **unit-R** (stop_dist on the deal if present).
4. Optional appendix: on three_fresh / spring rows that **also** appear in Module_ATR blotter, report `sumR_Module_ATR` under treatment A/B/C as a **separate table**. Never add to Challenge sumR.
5. Do not merge alias Package B → `sub_mid_dn_revert` (doctrine do-not list).

---

## 4. Replay method

Population:

- Rows in `shadow.jsonl` with `kind=deal_close` **or** open/slate that `compose_shadow` would mark `named_apply_symbol` (XAU, not A+, not house_hard_off, not leave-orig).
- Join deals on ticket when present.
- `already_admitted=True` by construction (size cannot mint fires).

For each row:

1. Rebuild gold_state / world_state from Challenge bars + peers + news spine (existing `challenge_shadow` / `compose_shadow` path).
2. Local product A = `combined_live_tilt` from current compose (may call `evaluate()` for flow/cost Jev; CA static unless shadow flag).
3. Shadow B/C: map Jev Scores; **do not mutate a broker unit**.
4. Counterfactual usd = `as_traded_usd * (tilt_treatment / tilt_as_traded)`.
   - If as-traded tilt is unknown (`apply_claimed=0`, VPS receipt MISSING): assume as-traded tilt = **1.0** and **state that assumption**. Sensitivity: also report assuming as-traded = local product A (if host `GTOS_JEV_APPLY_LIVE=1` was on).
5. Unit-R from deal: `profit / (risk_usd_as_traded)` if stop_dist+volume named; else **STATE_MISSING** unit-R — still count usd.

Jev calls: `jev_client.evaluate(state)` with `symbol_fanout_questions()` + new `size_mult` / `ca_size_mult` / `size_posture`. Budget: `GTOS_JEV_MAX_CALLS=500000` on the prove process. Fail-closed rows (skip) stay on treatment A.

Holdouts:

- Ticket `293332188` must have tilt 1.0 on every treatment.
- House_hard_off rows excluded from size delta (tilt 1.0).
- Non-XAU: report n but no physical treatment (affinity).

---

## 5. Metrics (must all be in the receipt)

Per treatment {A,B,C,D} on the **same** n:

| metric | definition | gate |
|---|---|---|
| `n` | rows in population | report |
| `n_fires` | fires that would still print | **must equal A** |
| `n_refused_by_size` | would-be skips | **must be 0** |
| `n_invented_high` | empty spine claimed HIGH | **must be 0** |
| `n_decidable_jev` | Jev Score present | B/C need ≥20 (same bar as other size wires) |
| `n_moved` | tilt ≠ 1.0 | B/C need ≥5 |
| `n_distinct` | distinct tilts | B/C need ≥2 |
| `mean_tilt`, `p50_tilt`, `min_tilt`, `max_tilt` | | min≥0.70; cost/ca max≤1.00; flow max≤1.15 |
| `fire_rate` | fires / slate candidates | **must equal A** (size is not admit) |
| `sumR_unit` | sum unit-R if named | report; MISSING ok |
| `sumR_usd` | sum counterfactual usd | **primary payout metric** |
| `maxDD_usd` | running equity DD from 110k start (or named equity) | B/C/D must not worsen A by >10% of `|maxDD_A|` without Chair exception |
| `net_usd` | final | B/C/D ≥ A (strict for APPLY candidate) |
| `n_leave_orig_moved` | | **must be 0** |
| `n_w7_touched` | | **must be 0** |
| `apply_claimed` | | **must be 0** this prove |

Challenge deals baseline (cite, as-traded, tilt unknown): n_closed=46, W=6, L=40, net=−4487.73. Size overlay cannot “fix” hard-off sleeves; those stay envelope.

Wave E / CA prior bars remain the **decidable/moved/distinct** bars for *shadow quality*. Payout gate above is **additional** because overlay APPLY changes dollars.

---

## 6. Gate to APPLY (Chair only)

**SHADOW QUALITY (needed before Chair even looks at overlay):**

- verdict `PROVED_SHADOW` on B and/or C with bars 20/5/2
- invented HIGH = 0
- cannot refuse
- empty spine abstain
- Module_ATR not mixed into primary sumR

**OVERLAY APPLY candidate (still size_tilt only, XAU, Challenge ns):**

1. `n_fires` unchanged vs A  
2. `net_usd` ≥ A and `maxDD_usd` ≤ A × 1.10 (or better)  
3. mean tilt not a constant (n_distinct≥2) — not a silent 0.70 haircut on everything  
4. leave-orig / W7 / hard-off / A+ untouched  
5. scoped XAU only — no GBPJPY physical until session 13 affinity hist  
6. CA-* labels remain `apply: false`  
7. `GTOS_JEV_SIZE_MULT_APPLY` or `GTOS_JEV_CA_SIZE_JEV_SCORE_APPLY` flipped **one at a time** (not both same pass)  
8. `GTOS_JEV_SLEEVE_SELECT_APPLY` stays 0  
9. Live `apply_claimed` still 0 until a real Challenge place (writer)

If VPS `apply_receipt.jsonl` is still UNREACHABLE, **do not** assume as-traded tilt; run both assumptions and require PASS on **both** before APPLY.

**FAIL → stay SHADOW.** Eternal shadow is also forbidden by process lock — the next step is to fix state/questions and re-prove, not to sit forever.

---

## 7. Optional appendix populations (not APPLY gates)

- Module_ATR three_fresh blotter (`.../blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`) + yearfold JSON — **separate** `sumR_Module_ATR` column. Geometry proxy ≠ live TradeIntent.
- GBPJPY Module_ATR blotters — affinity session 13; size physical still XAU.
- FLUID-SIZ-003..007 into combined (`GTOS_JEV_FLUID_SIZE_INTO_COMBINED_SHADOW`) — extra treatment **E**. Must show it does not double-count CA-EVT vs event_size.

---

## 8. Execution sketch (Chair / later session)

```text
# research VM, Challenge tape local, no broker
export GTOS_JEV_A1_CALL=1
export GTOS_JEV_MAX_CALLS=500000
export GTOS_JEV_SIZE_COMPLETE_STATE_SHADOW=1
export GTOS_JEV_CA_SIZE_JEV_SCORE_SHADOW=1
export GTOS_JEV_SIZE_MULT_APPLY=0
export GTOS_JEV_CA_SIZE_JEV_SCORE_APPLY=0
python3 scripts/jev_size_mult_prove.py \
  --pack judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl \
  --deals judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl \
  --out <this_session_OUT>/hist_prove/SIZE_MULT_SHADOW_PROVE.json
```

This session does **not** run evaluate() against TypeSafe (design-only; avoid burning budget without Chair). Prove JSON is the next Chair action.

---

## 9. Blockers to a honest PASS this seat

| blocker | effect |
|---|---|
| VPS apply_receipt unreachable | as-traded tilt assumption required |
| `apply_claimed=0` | no live tilted fill to calibrate $150×tilt vs lots |
| Module_ATR ≠ live geometry | cannot use yearfold sumR as payout gate |
| `CA_SIZE_SHADOW_PROVE.json` stale lock | cite counts, not lock bits |
| Jev `size_mult` question **not in production fanout yet** | prove needs the patch landed as SHADOW first |
| Policy C SIZE_TRIM 0.75 may already compound | must be a named field on state |

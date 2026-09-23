# HIST-PROVE PLAN — 07_conf_gate_regime

**login:** Challenge `0` / ns `operator` / magic `0`  
**mode:** replay / shadow · **APPLY unset** · **order_send=0** · **no host-mesh** · **no NEWS invent**  
**Module_ATR honesty:** required — see §2.

This plan is the gate to any future Chair APPLY of `GTOS_JEV_CONF_GATE_APPLY` or `GTOS_JEV_REGIME_GATE_APPLY`. This session does **not** flip those flags.

---

## 1. Why prove is blocked today (honesty)

| fact | implication |
|---|---|
| `numeric_conf_on_hist_labels: false` (FIRE 1201 / band weights) | STRICT/SESSION/EVENT UB stand_down is a **subclass proxy**, not a live HIGH-floor hit-rate |
| `call_system_one` never POSTs | No Jev Choice on the live sidecar; fallback is unclear@equal |
| conf_gate is CODE bands of a scalar | Vendor 0.50/0.85 **forbidden as truth** |
| Policy C voters `regime_tag`/`conf_band` often PENDING | Incomplete-state haircut is not a regime judgment |
| S14 tape `atr14=1.2`, `atr50=1.0` | **Lab constants** in `s14_tape.gold_state()`, not Challenge ATR, not Module_ATR |

**Monday-ready APPLY: NO** until a numeric-conf sidecar exists on replay (Phase 2).

---

## 2. Module_ATR honesty (non-negotiable)

Do **not** invent ATR. Do **not** merge R universes.

| lens | unit | path | may feed this prove? |
|---|---|---|---|
| **Dig_3R** | Dig geometry R | Challenge closes / Dig blotter | Challenge payout tape **only** for fire-rate / sumR vs writer |
| **Edge_ATR** | Edge ATR-R | Edge research | **NO** merge into Dig or Module columns |
| **Module_ATR** | ATR units, `stop0.75_tgt6.0_ATR` | `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | Separate column only; `fill_model=geometry_proxy_ohlc_touch_module_ATR_exit_NOT_broker_NOT_module_exact` |

Rules:

1. `emit_regime_buckets` already `omit_if_missing` on `atr_expansion`. If `geometry.atr14` / `atr50` absent → omit bucket, stamp `completeness.missing_fields`, `regime_tag=PENDING` if not enough buckets. **Never fill 1.2/1.0 from the lab helper on a live/Challenge as-of row.**
2. S14 `historical_tape_rows()` may keep lab ATR **only** when the scorecard labels `atr_source=lab_constant_not_module_atr`. Any APPLY-gate scorecard must use Challenge-assembled `gold_state` from real bars (`challenge_shadow_20260917/multi/XAUUSD_M15.csv` + H4/D1) **or** explicit `STATE_MISSING` for ATR.
3. Module_ATR yearfold (`THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.json`) is a **third lens**. Report `sumR_Module_ATR` beside Challenge sumR; **never add them**.
4. `research_armed_tags` overlay (`dsp_three_fresh_lower_lows`, `dsp_spring_close_on_20low_through_the_box`) is affinity research, **not** `live_armed_set`.
5. Do not treat Module_ATR blotter `atr` field as S14 `geometry.atr14` unless the same as-of bar is joined and the join is logged.

---

## 3. Tape inventory (found vs missing)

### FOUND

| tape | path | use |
|---|---|---|
| S14 identity JSONL | `_pr41_land/.../lab/s14_historical_tape/TAPE_0.jsonl` | Phase 1 injected replay (already how `run_s14_historical_prove.py` works) |
| S14 generator | `src/judgment/s14_tape.py` | ≥24 rows; lab ATR — tag `atr_source=lab_constant` |
| S15 generator | `src/judgment/s15_tape.py` | Ticket subclasses + Close Loop identities |
| FIRE 1201 receipt | `judgment/astra/lab/p0_warroom_shadow_prove/FIRE1201_HIST_PROVE_RECEIPT.json` | KEEP-win / residual lock |
| CONF_GATE calib 1201 | `/workspace/gtos/research/warroom_20260920/conf_gate_calib_1201/` | UB proxy ΔR; not APPLY proof |
| false_admit bands | `close_loop/war_room_20260920/conf_gate_bands_false_admit_shadow.md` | n=29 / −13.5428 shadow R |
| Challenge deals | `judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl` | close identities |
| Challenge bars | `.../challenge_shadow_20260917/multi/{XAUUSD,GBPJPY,EURUSD,...}_{M15,H4}.csv` | Phase 2 gold_state assembly |
| Module_ATR blotter | `close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | Third-lens column only |
| jev_everywhere report | `close_loop/war_room_20260920/jev_everywhere_report_0.md` | label-surface band R (not live APPLY) |

### MISSING (honest)

| tape | status |
|---|---|
| `lab/s15_historical_tape/TAPE_0.jsonl` | **FILE MISSING.** Generator + `scripts/run_s15_historical_prove.py --write-tape` exist. Phase 1 must generate it. |
| Numeric confidence on hist admission labels | **MISSING** by design (`hist_labels_lack_numeric_conf`). Phase 2 harvests it from live `evaluate()`. |
| Live VPS sidecar JSONL for this seat | VPS unreachable (host-mesh). Box mirrors only. |
| Challenge-as-of `geometry.atr14` on every S14 row | **MISSING** on the committed S14 JSONL (lab 1.2/1.0). Phase 2 must assemble or mark `STATE_MISSING`. |

---

## 4. Cohorts (lock these tickets)

### KEEP wins — must not flip (FIRE 1201)

| ticket | R (receipt) |
|---|---|
| 291816474 | +1.87 |
| 293540988 | +2.962 |
| 291794419 | +3.02 |

`wins_preserved` must stay true. `SAFE_WIN_DISPOSITIONS = {KEEP}`.

### Residuals — REVIEW, not hard-off

| ticket | R | band |
|---|---|---|
| 291087142 | −1.2007 | CONF_GATE_REVIEW |
| 293128383 | −0.94 | offhours REVIEW |

### STRICT proxy (fs_half_still_losing, n=21)

291072108, 291096187, 291210052, 291234829, 291486315, 291549869, 291713652, 291758207, 291778371, 292513484, 292524534, 292876275, 293024386, 293437038, 293564978, 293592749, 293414629, 293650737, 293669979, 293707634, 293765156.

UB stand_down Δ shadow R = **+8.7127**, wins touched = **0** (proxy).

### SESSION (n=4)

291392252, 283024183, 285296282, 293435759. UB Δ = **+2.3231**.

### EVENT (n=3)

291383082, 293332188, 293611741. UB Δ = **+1.3063**. Stamped news only.

### Label-surface (jev_everywhere_report — cite, don't treat as APPLY)

| band | n | sumR | wr |
|---|---:|---:|---:|
| CONF_GATE_ALLOW | 4 | +8.069 | 1.0 |
| CONF_GATE_KEEP | 3 | +7.852 | 1.0 |
| CONF_GATE_REVIEW | 2 | −2.1407 | 0.0 |
| CONF_GATE_SESSION | 4 | −3.0974 | 0.0 |
| CONF_GATE_EVENT | 3 | −3.1387 | 0.0 |
| CONF_GATE_STRICT | 44 | −46.139 | 0.0 |

Baseline Challenge tape ΣR = **−38.5948**. G4–G8 residual **+0.5857**. Stacked CONF_GATE UB residual **+12.9278** (Δ **+12.3421** vs G4–G8).

---

## 5. Phases

### Phase 0 — freeze honesty (this session: DONE as design)

- [x] Vendor 0.85 forbidden as truth
- [x] Module_ATR lens separate
- [x] S14 ATR lab-constant tagged
- [x] S15 JSONL missing stated
- [x] Numeric conf missing stated
- [ ] Chair: do not APPLY

### Phase 1 — injected replay (no live Jev, no live bars)

Reuse existing scripts (box, `--force`, no host-mesh):

```bash
python3 scripts/run_s14_historical_prove.py --force \
  --log-dir /tmp/s14-prove \
  --score-out /tmp/s14-prove/scorecard.json \
  --write-tape judgment/astra/lab/s14_historical_tape/TAPE_0.jsonl

python3 scripts/run_s15_historical_prove.py --force \
  --log-dir /tmp/s15-prove \
  --write-tape judgment/astra/lab/s15_historical_tape/TAPE_0.jsonl
```

**Bars (existing S14):** `n_decidable ≥ 20`, `n_moved ≥ 5`, `n_distinct_gate ≥ 2`, `n_invented_high == 0`, `n_order_send == 0`, all `broker_effect=false`.

**New honesty columns to add to the scorecard (draft):**

- `atr_source` ∈ `{lab_constant, gold_state_geometry, omitted, STATE_MISSING}`
- `n_lab_constant_atr`
- `n_atr_omitted`
- `module_atr_R_merged: false`

Phase 1 **cannot** unlock APPLY (injected answers, lab ATR).

### Phase 2 — live `evaluate()` on assembled Challenge gold_state (SHADOW)

1. Assemble `gold_state.v0` from Challenge bars (`XAUUSD` M15/H4/D1, then GBPJPY) at deal as-of. **Do not** copy S14 lab ATR. If ATR cannot be computed from closed bars, omit `atr_expansion` and stamp `STATE_MISSING`.
2. Enable `GTOS_JEV_REGIME_LIVE_EVALUATE=1` **in the prove process only** (not VPS APPLY).
3. POST `jev_client.evaluate(complete_state)` with `regime_*` + `conf_admit` + `conf_band_label` questions. Budget `GTOS_JEV_MAX_CALLS=500000` in that process.
4. Harvest per-row: Choice YES|NO|UNSURE, `regime_tag`, `conf_band`, confidence/noul, `jev_dark`.
5. Fail-closed rows (`PENDING`) do not get move credit.

**Metrics (required):**

| metric | definition |
|---|---|
| `n` | rows with assembled state |
| `n_jev_ok` | evaluate() ok |
| `n_jev_dark` | skip/error/malformed |
| `n_yes` / `n_no` / `n_unsure` | conf_admit |
| `n_regime_tag_pending` | tag PENDING |
| `n_atr_omitted` | atr_expansion omitted |
| `fire_rate_shadow` | fraction Choice YES among decidable |
| `fire_rate_baseline` | writer admits on same tickets |
| `sumR_challenge` | Challenge payout R **only** (Dig/close tape) |
| `sumR_Module_ATR` | Module_ATR blotter join **or null** — never summed into Challenge R |
| `maxDD_challenge` | peak-to-trough on Challenge R path |
| `wins_preserved` | KEEP-win tickets still KEEP/YES-eligible |
| `n_order_send` | must be 0 |
| `n_invented_news` | must be 0 |
| `n_invented_atr` | must be 0 |

### Phase 3 — counterfactual vs UB proxy

Compare:

| policy | expected (from calib, **proxy**) |
|---|---|
| S0 G4–G8 | residual +0.5857 |
| STRICT UB stand_down all 21 fs_half | Δ +8.7127, wins touched 0 |
| SESSION UB n=4 | Δ +2.3231 |
| EVENT UB n=3 | Δ +1.3063 |
| STACK UB n=28 | residual +12.9278, Δ +12.3421 |
| Phase 2 Jev Choice (numeric) | **unknown until harvest** |

Gate: Jev Choice must **not** do worse than G4–G8 on Challenge sumR **and** must preserve KEEP wins. Beating STRICT UB is **not** required for first scoped APPLY (UB assumes 0% HIGH pass — optimistic ceiling). A live HIGH pass-rate of 25–50% still showed +5.08 to +6.94 Δ in the sensitivity table — use that as a **floor discussion**, not a promise.

Pass-rate sensitivity (already computed, optimistic):

| pass_frac HIGH | n_stand | Δ vs G4G8 |
|---:|---:|---:|
| 0.00 | 21 | +8.7127 |
| 0.25 | 16 | +6.9436 |
| 0.50 | 11 | +5.0786 |
| 0.75 | 5 | +2.6300 |
| 1.00 | 0 | 0 |

If live Jev YES-rate on fs_half is ~1.0, STRICT APPLY is **worthless**. If ~0.0–0.5 with KEEP wins untouched, scoped APPLY is discussable.

### Phase 4 — scoped APPLY candidate (Chair only)

Only if Phase 2+3 receipt says:

1. `wins_preserved=true` on the three KEEP tickets  
2. `n_order_send=0`, `n_invented_news=0`, `n_invented_atr=0`  
3. Challenge `sumR` ≥ G4–G8 residual (0.5857) **and** fire_rate not silently collapsed vs writer (report both)  
4. `n_jev_dark / n` below a Chair-named cap (draft: ≤ 0.15)  
5. Affinity held (XAU × dsp/metals first; GBPJPY × vss second)  
6. Module_ATR column reported separately or `STATE_MISSING`  
7. `GTOS_JEV_SLEEVE_SELECT_APPLY` still 0  

Then Chair may ENFORCE:

- `GTOS_JEV_CONF_GATE_APPLY=1` **scoped** (XAU dsp STRICT / metals_core) LABEL-admit only  
- optionally `GTOS_JEV_REGIME_GATE_APPLY=1` for `stand_down` vs `admit_ok_label` on the same scope  

Physical size still `GTOS_JEV_APPLY_LIVE`. Place still writer / session 14.

---

## 6. Replay commands (box only)

```bash
# Phase 1 (injected, no network required)
cd /workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent
python3 -m pytest -q tests/judgment/test_s14_regime_gate.py tests/judgment/test_s15_cost_of_error.py tests/judgment/test_fluid_gates.py

# Phase 2 (needs TYPESAFE key in THIS process; never print the key)
# GTOS_JEV_REGIME_LIVE_EVALUATE=1 GTOS_JEV_MAX_CALLS=500000 GTOS_JEV_CONF_GATE_APPLY=0 \
#   python3 scripts/run_conf_regime_hist_prove.py   # DRAFT script — not landed
```

Draft prove harness: `patch_drafts/run_conf_regime_hist_prove.py` (sketch). Do not run live POSTs from this session unless Chair asks; this session is design-only.

---

## 7. APPLY gate (copy onto prove receipt)

```
allowed = (
    wins_preserved
    and n_order_send == 0
    and n_invented_news == 0
    and n_invented_atr == 0
    and module_atr_R_merged is False
    and atr_source != "lab_constant"   # for APPLY cohort
    and numeric_conf_sidecar is True
    and sumR_challenge >= sumR_g4g8
    and keep_win_tickets_disposition == KEEP
    and scoped_symbols_sleeves_named
    and GTOS_JEV_SLEEVE_SELECT_APPLY != 1
)
```

If any clause fails → **APPLY stays 0**. Chair verbs only.

---

## 8. What this plan will not do

- Invent ATR or NEWS_PROTOCOL  
- Merge Module_ATR R into Challenge sumR  
- Flip global sleeve-select APPLY  
- Touch redacted_account / W7  
- Place / remint / flatten from conf/regime  
- Treat vendor 0.85 or FIRE 1201 UB as live hit-rate  

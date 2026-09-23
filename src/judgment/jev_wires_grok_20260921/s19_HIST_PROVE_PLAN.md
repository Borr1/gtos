# HIST PROVE PLAN — usage ramp / every-gate evaluate()

**session:** `19_typesafe_usage_ramp_every_gate`  
**lens law:** Module_ATR honesty — **never merge** Dig_3R R, Edge_ATR R, and Module_ATR R. Report three columns or one named lens. Do not invent ATR / regime.  
**place:** `false` this plan. APPLY that changes live fire rate requires a PASS receipt + Chair verb.  
**global sleeve-select APPLY:** stays **0**.

---

## 0. What this prove is (and is not)

This is **not** a place/size APPLY prove by itself. It proves:

1. Every in-scope gate **path** calls `jev_client.evaluate(state)` (observe + decide).
2. Fail-closed when Jev is dark (skip/error/budget) — fire rate must **not** silently rise.
3. Usage ramps for the right reason (coverage), not duplicate identical POSTs.
4. Module_ATR / Challenge tapes stay **separate** scoreboards.

Fire-rate-changing APPLY (admit refuse, size tilt widen, sleeve-select scoped, PLACE Choice) is **gated** on the existing hist receipts + new replay of the observe/decide overlay.

---

## 1. Tapes that exist (box)

### 1a. Challenge-true FTMO 0 bars

Present:

| location | contents |
|---|---|
| `_pr41_land/.../judgment/astra/lab/challenge_shadow_20260917/` | XAUUSD M15/H4/D1, sit, deals, events, shadow.jsonl |
| `.../challenge_shadow_20260917/multi/` | M15: XAUUSD, EURUSD, GBPJPY, USDJPY, GBPUSD, EURGBP, US30_cash, UK100_cash, BTCUSD, ETHUSD |
| `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/` | peer M15 (GBPJPY **not** in this box root sample — use PR41 multi) |

**Do not use:** `data/historical*` / April packs (`bars.py` `default_gold_paths`). `admit_challenge_peer_csv` refuses no-`time_utc` and last print before 2026-09-17.

**MISSING honestly:**

- Live VPS `events.jsonl` / writer `latest_slate` body (pointer only in lab). Host `redacted_host` UNREACHABLE this seat.
- Challenge-true **yield / DXY / funding** series — RDF Nouls expected **null**, not false easing.
- Full Challenge **closed-trade R tape** joined to every skip reason (writer skip jsonl not in this workspace as a complete 7d dump).
- Live Typesafe dashboard row proving the $0.11 / 666 figure (owner-stated; not re-fetched here).

### 1b. Module_ATR blotters (geometry proxy — **not** live TradeIntent)

| blotter | n | affinity |
|---|---|---|
| `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | 11239 | XAU × three_fresh |
| `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl` | 5659 | XAU × spring |
| `blotter_Module_ATR_GBPJPY_vss_fxcross_london_proxy.jsonl` | 818 | GBPJPY × vss |
| `blotter_Module_ATR_GBPJPY_sub_mid_dn_re_proxy_SHORT.jsonl` | 2057 | GBPJPY × sub_mid SHORT |
| `blotter_Module_ATR_XAGUSD_metal_session_reversion_20260920.jsonl` | 782 | XAG |
| `blotter_Module_ATR_XAGUSD_metals_core_20260920.jsonl` | 16 | XAG |
| `blotter_Module_ATR_XAGUSD_sub_xvol_pullback_20260920.jsonl` | 5 | XAG |

Honesty stamp (already in war_room overlays): geometry proxy ≠ live module path (no stay_timing / peer_panel / admission). **APPROXIMATION**. Never present Module_ATR sumR as Challenge payout.

---

## 2. Already-proved numbers (cite, do not re-invent)

From `JEV_SLEEVE_SELECT_HIST_PROVE_V2_20260920.json` + `JEV_SLEEVE_SELECT_SCOPED_XAU_APPLY_RECEIPT_20260920.json`:

| lens | n_conflicts | sumR_select | sumR_keep_all | beats both? | note |
|---|---:|---:|---:|---|---|
| **Module_ATR** XAU day three_fresh×spring | 2353 | **+235.36** | **−74.72** | YES | scoped APPLY candidate #1 |
| **Module_ATR** EURUSD year asian_fade×PackageB | 13 | +926.63 | +2350.46 | NO | poisons **global** |
| **Module_ATR** combined | 2366 | +1161.99 | +2275.74 | NO | global V2 **FAIL** |
| **Challenge** KEEP conflicts (SEPARATE) | 1 | +2.265 | +2.01 | YES | n=1 — too small to graduate |

Locks already on those receipts: `never_merge_Dig3R`, `Challenge_separate`, `Policy_C_APPLY_untouched`, `GTOS_JEV_SLEEVE_SELECT_APPLY=0`.

**This usage-ramp prove does not reopen global sleeve-select APPLY.**

---

## 3. Replay protocol (usage ramp)

### Stage A — coverage (no fire-rate change)

**Goal:** count POSTs vs gate paths. APPLY off.

1. Replay `challenge_shadow.score_sit` / `score_deals` / `score_slate` on lab sit+deals **with** `GTOS_JEV_MAX_CALLS=500000`.
2. Mock or live TypeSafe (Chair chooses). If live: Challenge key fingerprint `00000000` claimed; never print the key.
3. Metrics:
   - `n_candidates`
   - `n_evaluate_posts`
   - `n_dedup_hits`
   - `n_skipped_budget`
   - `n_dark`
   - `n_gates_stamped` (must be 48 fluid ids per observed candidate)
   - `n_skip_reasons_with_zero_posts` (must → 0 under `USAGE_RAMP_OBSERVE=1`)
4. **PASS A:** every skip reason in `book_owner` loop either ENVELOPE_KEEP (no decide) **or** has ≥1 observe POST; fluid cycle no longer `answers_injected` only; policy_c / sleeve_select receipts contain `jev.ok` or honest `skipped`.
5. **FAIL A:** any JEV_WIRE path with 0 POST and no `jev_dark` receipt.

### Stage B — fail-closed dark (must not increase fire)

1. Replay same tape with `GTOS_JEV_A1_CALL=0` and `GTOS_JEV_FAIL_CLOSED_DARK=1`.
2. Metrics vs baseline writer:
   - `n_admit` ≤ baseline
   - `size_mult` never > 1.0 vs baseline
   - `fire_rate` ≤ baseline
   - no new places (place remains writer-only; this stage observes)
3. **PASS B:** dark ⇒ STAND / 1.0 tilt / no extra admits.
4. **FAIL B:** fail-open (today's `tilt(None)=1.0` plus Policy C admit-as-today) **increases** or preserves admits that baseline would have refused only if Jev were up — wait: today Policy C refuse is static. Dark fail-closed must not **widen** vs current live integers.

### Stage C — Module_ATR overlay (sleeve-select + Policy C questions)

Replay **only** Module_ATR blotter rows through `evaluate()` Choice (SHADOW). Scoreboards:

| column | definition |
|---|---|
| `n` | rows with assembled COMPLETE_STATE |
| `sumR_Module_ATR` | blotter R_ATR / R on Module_ATR lens **only** |
| `sumR_select` | R if Jev Choice pick taken |
| `sumR_keep_all` | R if all conflict sleeves kept |
| `DD_proxy` | running max-dd on that lens (not FTMO DD) |
| `fire_rate` | n_PLACE_or_ADMIT / n |
| `n_dark` | evaluate skip/error |

**Do not** add Dig_3R sumR into these columns. If a Dig blotter is used, emit a **separate** table.

XAU three_fresh×spring must reproduce the cited +235.36 vs −74.72 **direction** (exact replay may differ if Choice is now live Jev vs the v2 rule `C_SIZE_TRIM` on all 2353). Record delta vs v2 rule as `sumR_jev_choice - sumR_v2_rule`.

GBPJPY vss×sub_mid: use the two GBPJPY Module_ATR blotters; **n and sumR TBD this pass** (files present; this session does not run the join). Stage C is a **plan** — executing the join is a Chair replay job.

### Stage D — Challenge tape overlay (SEPARATE)

Replay lab `deals_since_20260909.jsonl` + sit through `challenge_shadow.score_deals` (already POSTs evaluate).

Metrics (Challenge R only):

- `n` deals scored
- `sumR` (Challenge / broker R, not Module_ATR)
- `DD` from sit equity if present else MISSING
- `fire_rate` = placed / candidates on slate if slate **body** present; else MISSING (lab has pointer json)
- `n_posts` / `n_dark`

**PASS D (usage):** n_posts scales with n deals (≈1 deduped POST/row), budget not exhausted at 200.  
**PASS D (APPLY):** not claimed here. Size/admit APPLY still needs named wire hist (Policy C prove json already exists as LABEL/refuse; size tilts already named).

### Stage E — place_fluid Choice vs writer actuals (design only)

Shadow log PLACE|STAND|DELAY vs writer `placed[]` / skip reasons on Challenge dates in lab.

- **PASS E to even propose APPLY:** Choice PLACE subset has higher Challenge sumR and no DD breach vs writer actuals; n≥ Chair floor.
- This session **does not** run E. Owner override keeps the path OPEN.

---

## 4. Gate to APPLY (Chair)

| change | hist required | this session |
|---|---|---|
| `DEFAULT_MAX_CALLS=500000` + observe-every-candidate | Stage A PASS (coverage) + Stage B PASS (dark does not widen) | **propose** |
| Policy C evaluate() POST replacing 4-voter | Challenge replay: refuse-set vs current Policy C; fire_rate / sumR / DD | **propose**; APPLY already ON for static helper — swapping judge is a fire-rate change → hist first |
| Sleeve-select evaluate() POST | SHADOW ok after A; scoped XAU already PASSed Module_ATR; **global APPLY still 0** | POST yes / APPLY no |
| Size tilt expand COMPLETE_STATE | compare haircut distribution vs current flow×cost×ca | propose after D |
| PLACE Choice | Stage E | **not this session** |
| Hard-off exception Choice | per-family Challenge prove | walls stay |
| Two-stop remint Choice | remint autopsy on Challenge closed[] | COUNT stays integer |
| `GTOS_JEV_SLEEVE_SELECT_APPLY=1` global | V2 combined still FAIL | **forbidden this pass** |

---

## 5. Module_ATR honesty checklist (must appear on every receipt)

- [ ] Lens named: `Module_ATR` | `Dig_3R` | `Edge_ATR` | `Challenge` — never a sum of them
- [ ] Geometry: Module_ATR file stop0.75 / tgt6.0 (as blotter) — do not invent a new ATR
- [ ] `regime_tag=PENDING` if S14 dark — do not invent regime
- [ ] `news_join=STATE_MISSING` if spine empty — do not invent HIGH
- [ ] `n`, `sumR`, `DD`, `fire_rate` reported per lens
- [ ] `place=false`, `order_send=0` on research receipts
- [ ] Affinity instrument × sleeve held (no EURUSD sleeve on XAU, no AUDUSD port to NZD)

---

## 6. Suggested command shape (Chair / later executor — not run here)

```text
GTOS_JEV_MAX_CALLS=500000
GTOS_JEV_A1_CALL=1          # or 0 for Stage B
GTOS_JEV_FAIL_CLOSED_DARK=1
GTOS_JEV_USAGE_RAMP_OBSERVE=1
GTOS_JEV_FANOUT_DEDUP=1
# python3 -m ... challenge_shadow score on lab sit
# python3 war_room JEV_SLEEVE_SELECT hist v2 replay with live evaluate()
# NEVER router.place / order_send
```

If TypeSafe is unreachable: Stage A/B still PASS on **mocked** evaluate (ok=True fixture vs dark fixture). Live POST counts wait for host.

---

## 7. Blockers

1. VPS live usage dashboard not readable this seat — 666 req / $0.11 is owner-stated, not re-measured.
2. `_pr41_land` `admission.py` **lacks** Policy C hook (lives in `policy_c_activate_20260920` pack / Admin dirty tree).
3. Slate **body** often missing (pointer only) — Challenge fire_rate on slate MISSING unless Chair attaches body.
4. RDF/yield tape MISSING — RDF POST must carry nulls.
5. Executing live POSTs from this research seat against production budget is Chair-gated (this session did not POST).

# HOST_SIZE_APPLY_PROOF — 2026-09-17

**Verdict: B (Apply armed; size not proven mutating — functionally no-op on F5 unit shape)**  
Not A (wires are APPLY-open and a physical hook exists). Not C (no before≠after lots/unit proof; placed risk stayed $150).

Clock: host UTC; times below also as ICT (UTC+7).

---

## Answer-first

| State | Meaning | This dig |
|-------|---------|----------|
| **A** Shadow-only | API + log, never mutates size | No — APPLY_LIVE hook is spliced and env-armed |
| **B** Apply armed, unbound / no effective mutate yet | Would / should mutate when path + unit shape align | **YES** |
| **C** Apply live mutating size | Hard proof before≠after lots/unit | **No** |

---

## Why `host_site.bound=false`

- `bound` is **static metadata** in `src/judgment/host_sites.py` `HOST_SITES`, copied into A1 by `a1_log.observe()`.
- For `UB-AUTH-010` / `UB-PLC-017` / `F5-JEV-004`: `bound: False` means **not R2-locked** (splice allowed), **not** “hook unwired at runtime”.
- `SEL-V4-002` is the one with `bound: True` (R2 / do-not-import-from-selector).
- Runtime proof hooks **are** wired:
  - `bridge.py` after final `_decide` → `maybe_observe_ub_auth_010`
  - `book_owner.py` after `cost_skip = _spread_cost_screen` → observe + (if `GTOS_JEV_APPLY_LIVE`) `maybe_haircut_unit`

## Why `shadow_log_only=true` (does NOT force shadow apply)

- Hardcoded `True` in every A1 row (`a1_log.observe` / `observe_fluid_inventory`).
- Means “this JSONL row is observe/log only.”
- **`GTOS_JEV_ALIVE_SHADOW` does not force physical apply off.** Apply is a separate env gate: `GTOS_JEV_APPLY_LIVE`.

---

## A1 field evidence (69 rows; first `11:41:30Z` / 18:41 ICT → last `14:30:41Z` / 21:30 ICT)

- `shadow_log_only=true`: **69/69**
- `wire_apply=true` (stamp_lock / compose): **69/69**
- `host_site.bound=false`: **35** (named gates); missing/empty on FLUID-INVENTORY
- `jev.ok=true` throughout (TypeSafe alive)
- `state_sufficient=false`: **69/69** → flow tilt locked at **1.0**
- Non-1.0 `combined_live_tilt`: **28** rows — all from **cost** tilt via `spread_r` (e.g. 0.74–0.84); `cost_hurtful_used=null` (TypeSafe `noul` is continuous float; `_jev_noul` only accepts bool)
- Post-writer-restart (`>=12:31:56Z`): PLC `cost_skip=None` with tilt≠1:
  - `12:32:40Z` XAUUSD `dsp_two_bar_thrust_into_20high_continues` tilt **0.8152**
  - `12:32:45Z` USDJPY `xa_second_rth` tilt **0.8431**
- `UB-AUTH-010` `n_units=0` always (bridge admit snapshot empty that poll) — **not** proof of flat forever

---

## Code: when APPLY_LIVE mutates size

`physical_apply_allowed` (`apply_size.py`):

1. not leave-orig ticket  
2. `GTOS_JEV_APPLY_LIVE=1`  
3. login `0` and/or ns `operator`  

Then `maybe_haircut_unit` → `apply_named_tilts` → `_scale_unit(unit, combined)`.

Host splice (`book_owner.py` ~4252–4289): after `cost_skip is None`, if APPLY_LIVE, `compose_shadow(state, None, …)` then `maybe_haircut_unit(..., ns=self._namespace, login=…)`.

Launcher `f5_launch.ps1` sets `GTOS_JEV_ALIVE_SHADOW=1`, `GTOS_JEV_APPLY_LIVE=1`, `GTOS_JEV_A1_LOG=1`. Writer argv includes `--namespace operator`.

---

## Critical blocker (why not C)

`_UnitView` / router size from **`risk_pct_per_trade`**.  
`_scale_unit` only multiplies keys: `volume|lots|units|size|qty` — **never `risk_pct_per_trade`**.

So on the live F5 unit dict, haircut is a **silent no-op** even when tilts ≠ 1.0 and APPLY_LIVE is on.

Hard counter-example (post-Wave-L place):

| Ticket | Symbol / sleeve | Opened (UTC) | Intended risk | Lots |
|--------|-----------------|--------------|---------------|------|
| **293437038** | XAUUSD / `dsp_two_bar_thrust_into_20high_continues` | `12:32:05Z` (19:32 ICT) | **$150.00** | 0.17 |
| 293435759 | EURUSD / `xa_second_rth` | ~12:36 local stamp | **$150.00** | 3.33 |

Same XAU sleeve had A1 cost tilt **0.8152** that minute. If haircut had bitten risk, intended would be ~$122, not $150. Trade record has **zero** jev/haircut/tilt fields. Ratio shortfalls are broker-grid/fill noise, not JEV.

Also: haircut compose passes `answers=None` (no TypeSafe merge on the apply path); flow stays 1.0 while `state_sufficient=false`.

---

## Book context (`sit --mt5`)

```
login 0 bal 94709.05 eq 94709.05
day_net -606.88 to_pass 15290.95
occupied [] positions 0 pending 0
```

Flat now; places **did** fire after Wave L land (then closed). Flat book is not the reason size-apply is unproven.

---

## What would prove C next

1. **Fix unit shape (owner/chair code change):** scale `risk_pct_per_trade` (and/or `unit_risk_pct`) in `_scale_unit` / haircut, **or** recompute lots after tilt.  
2. Log a one-line apply receipt: `unit_before`, `combined_live_tilt`, `unit_after`, ticket/symbol.  
3. Next `cost_skip is None` place with tilt≠1.0 → trade_record `f5_intended_risk_usd` (or lots) **≠** baseline $150 / unhaircut lots.  
4. Optional: pass JEV `answers` into live `compose_shadow` (and teach `_jev_noul` continuous noul) so cost/flow tilts match A1.

Config missing for “arm”: **none** on Challenge path if launched via `f5_launch.ps1`. Blocker is **implementation gap**, not unbound host_site / ALIVE_SHADOW.

---

## Three-state summary

- **Not A:** TypeSafe fires; `wire_apply=true`; APPLY_LIVE splice + launcher env present.  
- **B:** Armed + observe bound in code; places occurred; **effective size mutation absent** because `_scale_unit` misses `risk_pct_per_trade`.  
- **Not C:** No hard before≠after; post-land tickets kept **$150** intended risk.

Chair dig only. No env change, no writer restart, no place/remint/flatten.

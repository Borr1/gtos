# PATCH SKETCH — 20_whole_code_envelope_audit

**status:** DRAFT ONLY under this OUT dir. Do **not** edit live VPS, redacted_account, or W7 books.  
**never_broker_place:** true. No `order_send`. No Chair APPLY claimed.  
**fail-closed if Jev dark:** skip receipts (`TYPESAFE_key_absent` / `call_budget_exhausted` / `A1_CALL_off`) → writer keeps current integer envelope. Never fail-open to place.

Owner override 2026-09-21: DELETE eternal “Jev never places.” Default-off until Challenge hist-prove remains OK. Do **not** flip `GTOS_JEV_SLEEVE_SELECT_APPLY=1` global.

---

## 0. Non-goals

- No live APPLY of any wire from this session.
- No NEWS_PROTOCOL invention.
- No silent hard-off soften.
- No Dig3R merge into Module_ATR.
- No `selector_v4.py` import (R2-bound).
- No Expanding V3 unpark.
- No W7 lot mutation.

---

## 1. Doctrine stamps (Chair LABEL, then code)

Inventory / sidecar still encode **eternal** never_place:

| file | current | draft |
|---|---|---|
| `judgment/astra/JEV_GATE_INVENTORY.json` | `"never_place": true` (and remint/flatten) | `"never_place": false`, `"place_default_off_until_prove": true` |
| `src/judgment/veto.py` | docstring “Jev never places…” | “Jev does not place **until** Chair APPLY after hist-prove; default refuse_broker_action stays” |
| `src/judgment/cycle.py` / `a1_log.py` | stamp `never_place: true` | stamp `place_default_off: true`, `owner_override_20260921: true` |
| `src/judgment/sites.py` | place/remint/flatten `status="veto"` Infinity | `status="gap"` + `safe=true` + question_ids `PLACE\|STAND\|DELAY` / remint / flatten_candidate; **execution still writer** |
| `src/judgment/conf_gate.py` | `STAKE_REQUIRED_BAND["place"]="VETO"` | keep VETO as **default band** until `GTOS_JEV_PLACE_FLUID` hist receipt; comment must not say eternal |

`refuse_broker_action()` **stays** in this session and in any land before hist-prove. That is default-off, not owner law.

---

## 2. `jev_client` budget (session 19 overlap; catch-all records)

```python
# jev_client.py
DEFAULT_MAX_CALLS = 500000  # was 200; owner usage-ramp. Override via GTOS_JEV_MAX_CALLS.
```

Fail-closed unchanged: missing key / explicit off / exhausted → `_skip(...)`, `ok=False`, writer envelope.

---

## 3. COMPLETE_STATE v0 residual fields (session 10 owns assembler; 20 adds)

Extend `assemble_gold_state_v0` / `assemble_symbol_state_v0` / a new `assemble_complete_state_v0()` used by **every** `evaluate()`:

```python
# draft: src/judgment/complete_state.py  (NEW — not landed)
COMPLETE_STATE_V0_EXTRA = {
    "ai_companion": {"pause": None, "cooldown": None, "risk_mult": None, "control_ok": None},
    "cluster": {"name": None, "already_placed_today": None},
    "tick": {"age_s": None, "stale_market_closed": None},
    "governor": {"reason": None, "size_cap_mult": None, "dd_frac": None},
    "confluence_a8": {"score": None, "passed": None, "enabled": False},
    "damage": {"verdict": None, "mult": None},  # HEALTHY if unassembled — never fake quarantine
    "learning_rerate": {"mult": None},
    "vp_acceptance": {"vp_loc": None, "would_drop": None},
    "hold_exit": {"mfe_r": None, "minutes_open": None, "exit_class_last": None},
    "ca_world": {"assembled": False},  # nulls not 0.0
    "aplus": {"setup_grade": None, "framework": None},  # honest missing on TradeIntent
    "entry_hour": {"deferred": None, "target_h": None},
    "spread_geometry": {"spread_r": None, "limit": None},
}
```

`news_join`: `object | "STATE_MISSING"`. Empty spine ≠ no HIGH.  
`full_state_dark` / `n_incomplete` counted. **Fail-closed Policy C stand-down if dark and APPLY on** (already).

---

## 4. Observe `evaluate()` on residual skips (sessions 12/19 + 20)

Today observe fires only on A1/Alive at admit/place-cost. Catch-all: **every skip reason still POSTs observe** (does not change skip).

```python
# book_owner.run_cycle — DRAFT, behind GTOS_JEV_A1_LOG|ALIVE_SHADOW
def _observe_skip(self, intent, reason, state):
    if not a1_enabled():
        return
    from src.judgment.a1_log import observe
    observe("UB-SKIP-" + reason.split(":")[0], state, extra={"skip_reason": reason, "place": False})
```

Do this for companion / cluster / stale_tick / generation_skips / governor block. **Never** call `router.place` from the observer.

---

## 5. Silent drops → named reasons (forensic)

`admission.admit_and_size` currently drops metals confluence / damage quarantine / learning GATE=0 / vp_acceptance **without** a skip_reason.

Draft: emit `SizedUnit(..., sized=False, reason="metals_confluence_reject")` (etc.) onto `units[]` **and** `generation_skips`-equivalent on the decision so A1 can observe.

Then Jev:

| reason | primitive | labels | env |
|---|---|---|---|
| metals_confluence_reject | Noul + Choice | `a8_agrees`; ADMIT\|STAND | `GTOS_JEV_A8_SHADOW=1` |
| symbol_damage_hard_quarantine | Choice | QUARANTINE\|HALF\|HEALTHY | `GTOS_JEV_DAMAGE_SHADOW=1` |
| learning_rerate_gate_zero | Score | KEEP\|GATE | `GTOS_JEV_LEARN_GATE_SHADOW=1` |
| vp_acceptance_drop | Noul | above_va_ok | `GTOS_JEV_VP_SHADOW=1` |

Default remains drop/skip if Jev dark.

---

## 6. Hold / exit family (largest 01-19 hole)

New shadow cycle hook (not broker):

```python
# draft: src/judgment/hold_exit_shadow.py
HOLD_CHOICE = ("HOLD", "TIGHTEN", "FLAT_CANDIDATE", "LEAVE_ORIG")

def evaluate_hold_exit(complete_state) -> dict:
    # jev_client.evaluate(state) with questions close_label / time_stop_vs_orig / ...
    # APPLY=0. Writer exit_policy_v4 remains integer until hist-prove.
    ...
```

Flags: `GTOS_JEV_HOLD_EXIT_SHADOW=1`.  
`FLUID-HLD-006` leave-orig `293332188` stays **ENVELOPE_KEEP**.  
Promote `FLUID-HLD-005` / `HLD-008` from SHADOW only after tape n≥ prove bars.

---

## 7. Place fluid promote (sessions 04/14 own; 20 confirms)

`FLUID-PLC-001..007` + `UB-PLC-017`:

```python
PLACE_CHOICE = ("PLACE", "STAND", "DELAY")
# APPLY only after HIST_PROVE_PLAN gate.
# env: GTOS_JEV_PLACE_FLUID_SHADOW=1
#      GTOS_JEV_PLACE_FLUID_APPLY=1  # Chair later; never this session
```

If Jev dark → **STAND** (fail-closed, no new fire). Writer still the printer.

---

## 8. Two-stop / occupancy remint (08 + 01 + 20)

Wire helper (currently unwired):

```python
# book_owner keep-one path — DRAFT
from two_stop_day_circuit import refuse_reason
rr = refuse_reason(symbol=..., sleeve=..., session_day=..., orig_stop_rows=...)
if rr:
    # integer refuse by default
    # if GTOS_JEV_TWO_STOP_REMINT_SHADOW: evaluate Choice REMINT_OK|STAND|SWITCH_SLEEVE|FLATTEN_SIBLING
    # APPLY=0 → still refuse
```

Same pattern for `already_placed_today` / lifecycle_guard / `g8_block_reentry_*` / `cluster_unit_already_placed_today`.

---

## 9. Pretrade cost Score (01/16 + 20 siblings)

Unify `cost_screen_spread_r`, `spread_geometry_floor`, execution `pretrade_cost`, `exec_mgr_v4` into one Score:

```
COST_OK | TRIM | STAND     clamp [0.70, 1.00]  cannot add size  cannot zero via Score alone
```

STAND only when hist shows +EV on refused legs **and** Chair APPLY. Default: keep skip if Jev dark.

Env: `GTOS_JEV_PRETRADE_COST_SHADOW=1`.

---

## 10. Admission Score (02/17 + 20 siblings)

Soft: `soft_daily_stop_reached`, `derisking_into_maxdd_wall`, `profit_target_protect_derisk`, `leader_impulse_veto`, kelly/sqrtN/stress/vol_level.

Hard ENVELOPE_KEEP: `circuit_breaker_open`, `fail_closed:*`, `max_dd_limit_reached`, `ceiling_profile_requires_smooth_ddefense`, `gross_risk_cap_exhausted`.

Env: `GTOS_JEV_ADMISSION_SCORE_SHADOW=1`. Shrink-only until hist.

---

## 11. Policy C host splice (inventory JEV_JUDGED but PR41 unwired)

```python
# bridge._decide AFTER admit_and_size — DRAFT
from judgment.policy_c_admit import evaluate_policy_c  # land pack path
pc = evaluate_policy_c(complete_state)
if pc["refuse"]:
    admission._refuse(...)  # existing Chair path
```

Do **not** land from this session. Session 05 owns ablation. Catch-all only records the import gap.

---

## 12. Sleeve-select scoped (03) — catch-all extra

- XAU conflict: scoped env only; global APPLY=0.
- GBPJPY: LABEL until hist widen.
- **EURUSD KEEP_ALL** (`eurusd_dual_pos_keep_all_identity`): own scoped bit; combined Module_ATR FAIL because EURUSD drag — **do not** treat KEEP_ALL as global APPLY evidence.
- XAG single KEEP: affinity session 13.

---

## 13. S14 POST gap

`regime_system_one.call_system_one` → wrap to `jev_client.evaluate(complete_state)` with questions `regime_type` / `regime_change_likely` / `strategy_viable`. Offline stub remains for CI. Fail-closed if dark → `regime_tag=PENDING`.

---

## 14. Companion / entry-hour / cluster

| wire | primitive | default if dark |
|---|---|---|
| ai_companion_pause | Choice KEEP_PAUSE\|SCOPED_RESUME\|STAND | KEEP_PAUSE |
| ai_companion_cooldown / zero_risk | Score | skip / size 0 |
| entry_hour_deferred | Choice DELAY\|FIRE_NOW\|STAND | DELAY (current defer) |
| cluster_unit_already_placed_today | Noul cluster_same_day | SKIP |

---

## 15. Fail-closed matrix

| Jev dark / skip | writer |
|---|---|
| envelope reason | unchanged integer |
| proposed JEV_WIRE, APPLY=0 | unchanged + shadow log |
| proposed JEV_WIRE, APPLY=1 but evaluate skip | **revert to integer** (never fail-open) |
| place Choice missing | STAND |
| remint Choice missing | REFUSE_REMINT |
| hard-off exception missing | KEEP_OFF |

---

## 16. What this session will not patch

- Live `book_owner.py` / VPS Admin tree
- Global `GTOS_JEV_SLEEVE_SELECT_APPLY`
- `selector_v4.py`
- redacted_account / W7
- Invented news endpoints
- Eternal `order_send=0` **as law** in new designs (we keep default-off)

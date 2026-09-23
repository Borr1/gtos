# PROVE_C_STAMP_EVIDENCE — ticket 293611741

**Written:** 2026-09-18 10:00:12 ICT  
**Case:** JEV_APPLY receipt moved `risk_pct` but `f5_intended_risk_usd` stayed **150**  
**Ticket:** `293611741` · XAUUSD · `dsp_shakeout_holds_run_lows` (broker comment `F5:dsp_shakeout_`)  
**Account:** Challenge login `0` / ns `operator`  
**VPS:** `machineId 7cfa9657-805b-4e9c-9fbb-886c500f997b` (`redacted_host`)

---

## Answer-first cause hypothesis

**Primary: parallel F5 scaler path (not haircut-after-stamp).**

`haircut_challenge_unit` correctly scales unit `risk_pct_per_trade` and writes the JEV_APPLY receipt (before≠after). Host splice places that haircut **before** `_UnitView` / `router.place`. Prove-C still fails because `execution.open_trade` (F5 minimal-size seam) **replaces** dollar risk with `MinimalSizeScaler.target_risk_usd` / `last["f5_intended_risk_usd"]` and stamps that onto the trade record — independent of the haircutted `risk_pct_override`.

Rejected as primary: “haircut after stamp.” Host line order puts haircut → headroom check on haircutted risk → `_UnitView` → `place`. Stamp of `f5_intended_risk_usd` happens later inside execution’s scaler seam.

---

## 1. Apply receipt row (JEV_APPLY)

**Path (VPS):** `host-local\redacted_host\repo\judgment\astra\lab\a1\apply_receipt.jsonl`  
**Row time:** `~2026-09-18T01:45:50Z` (= **08:45 ICT**)

| Field | Value |
|--------|--------|
| `combined_live_tilt` / tilt | **0.7467** |
| `flow` | **0.8485** |
| `cost` | **0.88** |
| Check | `0.8485 × 0.88 = 0.74668 → 0.7467` ✓ |
| Effect | `unit_before.risk_pct_per_trade` ≠ `unit_after.risk_pct_per_trade` (receipt moved risk_pct) |

**Expected USD if intended followed haircut:**  
`150 × 0.7467 =` **`112.005`** (≈ $112), not $150.

> **Access note (this seat):** live re-read of `apply_receipt.jsonl` / `trade_records\293611741.json` via `machineId` did **not** route (Shell stayed on box `grok-bot-vm-*`). host-mesh to `redacted_host` showed `offline, rx 0` / SOCKS REP=1 / ping timeout at write time. Numbers above are the owner/chair case facts for this prove; splice line refs below are from the VPS land agent’s direct host read (2026-09-17). Re-dump raw JSONL row when VPS local-exec is back.

---

## 2. Trade record instrumentation

**Path (VPS):** `host-local\redacted_host\repo\trade_records\293611741.json`

| Field | Observed |
|--------|----------|
| `f5_intended_risk_usd` | **150** (baseline Challenge tuition — prove-C miss) |
| Expected if haircut bit USD stamp | **~112.005** |

**Broker / tape corroboration (box pulls, no remint):**

| Source | Fact |
|--------|------|
| W3 `08:49 ICT` / F5 tape | NEW XAUUSD **293611741** LONG **0.35** lots between `07:55`→`08:49` ICT |
| Entry / SL / TP | `4347.32` / `4343.11` / `4380.73` · magic `0` |
| Comment | `F5:dsp_shakeout_` |
| Balance around fill window | ~`94363` (W3 delta) |

Volume **0.35** matches unhaircutted $150 Challenge XAU size class; a ~$112 intended would typically print smaller lots. Consistent with scaler keeping dollar target at 150 after haircut moved unit risk_pct.

**Next hard read when VPS up:** dump `f5_nominal_risk_usd`, `f5_actual_risk_usd`, `risk_pct_override`, `jev_risk_pct_*` from the trade_record. If `f5_nominal_risk_usd ≈ 112` and `f5_intended_risk_usd = 150`, that is definitive scaler-parallel proof.

---

## 3. Host `book_owner.py` line order (splice)

**Path (VPS):** `host-local\redacted_host\repo\src\components\ultimate_book\book_owner.py`  
**Land:** tip `c946b019e` · host lines **10118** · splice verified on VPS 2026-09-17 ~15:34Z

### Exact order (load-bearing)

1. **`cost_skip = self._spread_cost_screen(...)`** then A1/Alive observe (`maybe_observe_ub_plc_017` / `maybe_observe_fluid_at_place`) — host ~**4169–4171** (land receipt).
2. If `cost_skip is not None` → skip/continue (no place).
3. Route / AI companion → `adjusted_unit = self._ai_companion_gate.adjusted_unit(...)`.
4. **`haircut_challenge_unit` splice** — host **L4252–4285**:

```
4252: # Named Jev size tilts. Physical only if GTOS_JEV_APPLY_LIVE + Challenge ns/login.
4253: # Never mutates cost_skip. Skip leave-orig 293332188. Never refuse.
4254: # HOST_SIZE_APPLY_FIX: haircut_challenge_unit scales risk_pct_per_trade (prove C).
4258: from src.judgment.apply_size import haircut_challenge_unit
4274: adjusted_unit = haircut_challenge_unit(
4275:     adjusted_unit,
...
4282:     evaluate_jev=True,
4283: )
4284: except Exception:
4285:     pass
```

5. **Gross headroom** uses **post-haircut** `adjusted_unit["risk_pct_per_trade"]` — host **L4286–4288**.
6. **`unit_su = _UnitView(adjusted_unit)`** then floor / thin-hour / flow-hold.
7. **`self.router.place(ee, unit_su, ...)`** → `build_trade_params` → `risk_pct_override = sized_unit.risk_pct_per_trade * 100`.

**Conclusion on order:** haircut is **before** UnitView/place. Not haircut-after-stamp on the host splice.

GH reference (cleaner tree) same shape: haircut → `_UnitView` → `place` (`/tmp/gh_book_owner.py` ~2220–2265).

---

## 4. Where `$150` is stamped (parallel path)

### Unit → percent (haircut *can* reach here)

`execution_packets.build_book_trade_params`:

```text
risk_pct = round(float(sized_unit.risk_pct_per_trade) * 100.0, 8)  # FRACTION -> PERCENT
...
"risk_pct_override": risk_pct,
```

### Dollar override (haircut does **not** win)

`execution.open_trade` F5 seam (seed006 / host lineage):

```text
risk_amount = account_balance * (risk_pct / 100)   # nominal from (possibly haircutted) pct
f5_nominal_risk_amount = risk_amount
if self._f5_scaler is not None:
    risk_amount = self._f5_scaler.scaled_risk_amount(risk_amount, trade_params)
...
trade_params["f5_nominal_risk_usd"] = float(f5_nominal_risk_amount or 0.0)
trade_params["f5_intended_risk_usd"] = float(
    _f5_last.get("f5_intended_risk_usd") or self._f5_scaler.target_risk_usd)
```

`MinimalSizeScaler.scaled_risk_amount` sets:

```text
target = self.risk_usd_for(symbol, sleeve)  # CLI / cfg target_risk_usd (Challenge $150)
self.last = { "f5_intended_risk_usd": target, "f5_nominal_risk_usd": nominal, ... }
return target   # lots sized from TARGET, not haircutted nominal
```

So:

| Stage | risk_pct | dollar intended |
|--------|----------|-----------------|
| After haircut + receipt | **moved** (tilt 0.7467) | n/a |
| After `_UnitView` / `risk_pct_override` | should reflect haircut | n/a |
| After F5 scaler stamp | ignored for USD | **stays `target_risk_usd` = 150** |

That is the Prove-C stamp bug: **receipt proves haircut; trade_record intended proves scaler**.

---

## 5. Hypothesis scorecard

| Hypothesis | Fit | Notes |
|------------|-----|--------|
| **A. Parallel path: F5 scaler overwrites USD after haircut** | **BEST** | Matches receipt before≠after + intended=150 + lots 0.35 + code seam |
| B. Haircut after UnitView/stamp | Weak | Host L4252 haircut then L4286 headroom before UnitView/place |
| C. Haircut no-op on risk_pct (verdict B again) | Rejected for this ticket | Receipt moved risk_pct (post–`_RISK_KEYS` land) |
| D. Wrong account / APPLY off | Rejected | Receipt exists with flow/cost tilts; Challenge magic/ns |

---

## 6. What would close Prove-C

1. Wire scaler intended to haircutted nominal **or** set `target_risk_usd` from `balance * haircut_risk_pct` after apply.  
2. Or stamp `f5_intended_risk_usd` from `f5_nominal_risk_usd` when JEV apply ran (`jev_combined_live_tilt` present).  
3. Re-prove: next tilted place → receipt before≠after **and** `f5_intended_risk_usd ≠ 150` (e.g. ~112 for tilt 0.7467) **and** lots move.

**Out of scope this pack:** no place / remint / flatten / writer restart.

---

## Artifact index

| Artifact | Location |
|----------|----------|
| This pack | `/workspace/gtos/PROVE_C_STAMP_EVIDENCE_20260918.md` |
| Apply receipt (VPS) | `judgment\astra\lab\a1\apply_receipt.jsonl` ~`2026-09-18T01:45:50Z` |
| Trade record (VPS) | `trade_records\293611741.json` |
| Host splice proof | Land agent VPS read L4252–4288; `HOST_SIZE_APPLY_LAND_20260917.md` |
| apply_size haircut | `src/judgment/apply_size.py` `_RISK_KEYS` + `haircut_challenge_unit` + `write_apply_receipt` |
| Box tape corroboration | `/workspace/gtos/live/w3_tape_0849ict_pull/`, `f5_tape_sit_0852ict_pull/` |

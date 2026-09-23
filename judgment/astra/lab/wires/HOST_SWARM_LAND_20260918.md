# HOST_SWARM_LAND — 2026-09-18

**Goal:** Land ONE consolidated Challenge judgment+wires tip onto dirty VPS `f5-live` (`host-local\redacted_host\repo`). Recycle Challenge writer only.

**Authority:** Owner spoken FULL APPROVAL 2026-09-18 ~21:34 ICT (Borhen / redacted_account Chair). Later spoken word wins. `owner_named_at` `2026-09-18T14:34:00Z`.

**Tip:** `cursor/swarm-land-challenge-3c51` @ `45ad13098aeac6cd36a92f6946e68a3b7f338422` (PR #26). Suite-green code: `445dcbefca1496b0ad973a8d3006fbca2f69a482`. Receipt: `HOST_SWARM_LAND_RECEIPT_20260918.json`.

**Surface:** Challenge login `0` / ns `operator` / magic `0` / pass `$110k` ONLY.

Jev never places, remints, or flattens. Chair ENFORCE/VETO/LABEL. Writer prints. Envelope walls stay integers. Do not invent NEWS_PROTOCOL endpoints. Do not wholesale-copy host `book_owner.py`. Leave-orig ticket `293332188` untouched. A+ mute stays PROVE_SEED / SHADOW. Do not arm W7 / redacted_account.

---

## 0. Do not

- Place / remint / flatten from this land
- Arm W7 or redacted_account / touch `GTOS_W7_*` tasks
- Wholesale-copy GitHub `book_owner.py` (~5k) onto the dirty host file (~10069)
- Invent NEWS_PROTOCOL / `/v1/calendar` / HIGH rows
- Auto-admit catalog A+ sleeves
- Lift `ENV-US30` / 2-stop COUNT / token / H8 / hard DD
- Re-mint the activation token
- `git clean` host research LFS

---

## 1. Backup (host)

On `host-local\redacted_host\repo` before any copy:

```powershell
$ts = Get-Date -Format 'yyyyMMddHHmmss'
$bak = "host-local\redacted_host\repo.bak_swarm_$ts"
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Copy-Item -Recurse -Force src\judgment $bak\src_judgment
if (Test-Path judgment\astra) { Copy-Item -Recurse -Force judgment\astra $bak\judgment_astra }
Copy-Item -Force src\components\ultimate_book\book_owner.py "$bak\book_owner.py"
Copy-Item -Force src\components\ultimate_book\bridge.py "$bak\bridge.py"
if (Test-Path host-local\redacted_host\f5_launch.ps1) {
  Copy-Item -Force host-local\redacted_host\f5_launch.ps1 "$bak\f5_launch.ps1"
}
```

Host splice backups stay next to the dirty files as `*.bak_jev_swarm_20260918`.

---

## 2. Copy judgment land pack (not book_owner)

From this tip onto `host-local\redacted_host\repo`:

| Source (this tip) | Dest on host |
|---|---|
| `src/judgment/` (entire package) | `src\judgment\` |
| `judgment/astra/lab/wires/` named receipts below | `judgment\astra\lab\wires\` |
| `judgment/astra/schemas/world_state_v0.json` | same relative path |
| `judgment/astra/schemas/rates_dxy_funding_v0.json` | same relative path |
| `scripts/jev_ca_size_prove.py` | `scripts\` |
| `scripts/jev_cross_asset_prove.py` | `scripts\` |

Named receipts that must land:

- `APPLIED_NAMED.json` (CA-SIZ-001 now in `applied_wires`)
- `FLUID_PROVE_LEDGER.json` (`ca_siz_001` block, `apply_claimed=0`)
- `CA_SIZE_SHADOW_WIRE.md`
- `HOST_SWARM_LAND_20260918.md` (this file)
- `HOST_SWARM_LAND_RECEIPT_20260918.json`
- `HOST_SWARM_LAND_PACK.txt`
- `HOST_PROVE_C_STAMP_FIX.md`
- `PROVE_C_STAMP_EVIDENCE_20260918.md`
- `HOST_APLU_OBS_LAND.md`
- `HOST_APLUS_SLEEVES_LAND.md`
- `HOST_LEARN_LOOP_LAND.md`
- `HOST_APPLY_ALIVE.md` / `HOST_APPLY_LANDING_20260917.md` (already on host; refresh if stale)

File list: `HOST_SWARM_LAND_PACK.txt`.

---

## 3. Splice only documented sites

Do **not** replace `book_owner.py`. Confirm these already-landed sites still call this tip's `src.judgment` (refresh the *call*, not the file):

### HOST_APPLY_ALIVE / HOST_SIZE_APPLY_LAND

After AI companion `adjusted_unit` on the already-admitted path (~L4252–4285):

```python
# env-gate BEFORE import
if os.environ.get("GTOS_JEV_APPLY_LIVE") == "1":
    from src.judgment.apply_size import haircut_challenge_unit
    adjusted_unit = haircut_challenge_unit(
        adjusted_unit,
        intent=intent,
        tick=tick,
        ticket=getattr(intent, "ticket", None),
        login=0,          # Challenge only
        ns=self._namespace,       # must be operator
        already_admitted=True,
        occupancy=occupancy,      # host_occupancy_governor if present
        governor=governor,
    )
```

Physical gate inside `apply_size` requires login `0` **and** ns `operator`. Combined live = flow × cost × ca. Leave-orig `293332188` stays 1.0.

### HOST_APPLY_ALIVE observe (do not mutate cost_skip)

After `cost_skip = self._spread_cost_screen(intent, tick)` (~L4158):

- `maybe_observe_fluid_at_place` / A1 / APLU-OBS
- **Never change `cost_skip`**

### Prove-C scaler (required if not already on host)

Host `MinimalSizeScaler.scaled_risk_amount` must call `honor_f5_scaler_risk` so `f5_intended_risk_usd` follows haircutted risk (not stuck `$150`). See `HOST_PROVE_C_STAMP_FIX.md`. Do not wholesale-copy `execution.py`.

```python
from src.judgment.apply_size import honor_f5_scaler_risk

def scaled_risk_amount(self, nominal, trade_params=None):
    honored, _stamp = honor_f5_scaler_risk(
        nominal,
        scaler=self,
        trade_params=trade_params,
        login=getattr(self, "login", None),
        ns=getattr(self, "ns", None) or "operator",
    )
    return honored
```

Keep the existing `open_trade` stamp from `scaler.last` / `_f5_last["f5_intended_risk_usd"]`.

---

## 4. Env (Challenge f5-live worker only)

Patch `host-local\redacted_host\f5_launch.ps1` (not User/Machine env, not W7 supervisor):

```
$env:GTOS_JEV_ALIVE_SHADOW = '1'
$env:GTOS_JEV_APPLY_LIVE = '1'
$env:GTOS_JEV_A1_LOG = '1'
```

Do not set these on redacted_account / W7 launchers.

---

## 5. Recycle Challenge writer only

`bounce_f5.ps1` → `schtasks /End` + `/Run` **`GTOS_F5_FTMO` only**.

Do not restart `GTOS_W7_BookSupervisor`. Do not kill FN workers.

---

## 6. Verification checklist (host after bounce)

Paths present under `host-local\redacted_host\repo\src\judgment\`:

- [ ] `harvest_patterns.py`
- [ ] `symbol_state.py`
- [ ] `rates_dxy_funding.py`
- [ ] `ca_size.py` / `process_lock.py` (`WIRE_CA_SIZE` in `APPLIED_WIRES`)
- [ ] `aplus_pipe.py` (APLU land / SHADOW observe)
- [ ] `harvest_prove.py` (OSS harvest P0)
- [ ] `non_xau_remeasure.py`
- [ ] `world_state.py` + `cross_asset.py` + `learn_loop.py`

Code path:

- [ ] `python -c "from src.judgment.process_lock import WIRE_CA_SIZE, wire_apply_open, APPLIED_WIRES; assert WIRE_CA_SIZE in APPLIED_WIRES; assert wire_apply_open(WIRE_CA_SIZE) is True; assert wire_apply_open(WIRE_CA_SIZE, ticket='293332188') is False"`
- [ ] `python -c "from src.judgment.apply_size import honor_f5_scaler_risk; print('prove_c', honor_f5_scaler_risk.__name__)"`
- [ ] Live Challenge pid PEB: `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1` `GTOS_JEV_A1_LOG=1`
- [ ] W7 / FN env still empty for those flags
- [ ] Heartbeat healthy; login `0`; ns `operator`
- [ ] TypeSafe fingerprint still `00000000`
- [ ] No place / remint / flatten performed by this land

### Prove-C checklist — next tilted XAU place

1. `JEV_APPLY receipt` before≠after `risk_pct_per_trade`.
2. Trade record `instrumentation.f5_intended_risk_usd` **≠ 150**. Combined tilt `0.7467` → **~$112**. Tilt `0.70` → **$105**. Combined now `flow × cost × ca` (ca ≤ 1.00).
3. Lots move with the new intended (not the 0.35 / $150 class).
4. Receipt still written. `apply_claimed` stays 0 in the land ledger until that place; after the place, Chair labels the live row — Jev does not.

---

## 7. Combined size clamps (document)

| Wire | Clamp | Adds size? |
|---|---|---|
| `f5_xau_flow_alignment_size_tilt` | `[0.70, 1.15]` | yes, within clamp |
| `F5-JEV-004` | `[0.70, 1.00]` | never |
| `ca_cross_asset_size_tilt` | `[0.70, 1.00]` | never |

`combined_live_tilt = flow × cost × ca`. XAU named APPLY only. A+ SHADOW. Leave-orig 1.0. House hard-off 1.0. Physical lots: `GTOS_JEV_APPLY_LIVE=1` + Challenge login/ns.

---

## 8. Swarm modules this tip carries

| PR | What landed |
|---|---|
| #10 | Jev Alive + Prove-C scaler (`honor_f5_scaler_risk`) |
| #11 | NEWS repair map (no invented protocol) |
| #12 | `WORLD_STATE_V0` closed desk |
| #13 | Cross-asset CA-* + `load_peer_books` |
| #14 | G1 `news_inventory` |
| #15 | peers USDJPY |
| #16 | occupancy + governor (splice kwargs only) |
| #17 | code walls + APLU-OBS |
| #18 | SHADOW unlock / non-XAU remasure |
| #19 + this tip | CA-SIZ-001 NAMED APPLY size_tilt |
| #20 | close learning loop |
| #21 | A+ sleeves SHADOW / PROVE_SEED (not admitted) |
| #22 | `SYMBOL_STATE_V0` |
| #23 | rates / DXY / funding Nouls |
| #24 | OSS harvest P0 |
| #25 | all-instrument data inventory |

# Chair land recipe — VPS f5-live (Challenge 0)

**When:** 2026-09-20 Chair outcome authority — full land of P0 SHADOW stack + hist-prove.  
**Pull branch:** `cursor/chair-p0-land-f5-live-2541` onto documented Challenge path `cursor/swarm-land-challenge-3c51` (HOST swarm land / VPS `f5-live` at `host-local\redacted_host\repo`).  
**Not W7 `main`.** `main` is the W7 book. Challenge printer is leftover-ship / live `f5-live`.

Jev never `order_send`. Place stays on the Challenge writer. Do not invent `NEWS_PROTOCOL`. Do not splice Module_ATR tags into `config/live_armed_set.json`.

---

## Exact enable env

| Variable | Default | Chair enable |
|---|---|---|
| `GTOS_JEV_FLUID_GATES_SHADOW` | **unset** (capture writes nothing) | **`1` required for capture** |
| `GTOS_JEV_EVERYWHERE_SHADOW` | unset | **alias** of `GTOS_JEV_FLUID_GATES_SHADOW` (same sidecar). Dig E: **APPLY_CANDIDATE ALREADY_LIVE** — **not** open `IN_PROVE` |
| `GTOS_JEV_FLUID_GATES_APPLY` | **unset / false** | optional **LABEL draft only** after hist-prove `wins_preserved=true` |
| `GTOS_DIG_MULTI_STAGE_GUARD_SHADOW` | **`0`** (Dig E **KILL** default/off) | offline `--shadow` / `--force` only. **Off** Challenge prove-only dual-flag track |
| `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` | unset / **forbidden** (Dig E **KILL**) | setting it refuses prove (**exit 2**). Never place. Off track |
| `GTOS_JEV_APPLY_LIVE` | host-already-named (CA-SIZ-001) | do not flip from this land |
| `GTOS_JEV_ALIVE_SHADOW` | host-already-named | leave as-is |

### Dig E board (2026-09-21) — consume, do not re-open

Board `APPLY_KILL_RECEIPTS_DUAL_FLAGS_CHALLENGE_20260921` / login `0` / ns `operator`. Receipt: [`DIG_E_LAND_CONSUME.md`](DIG_E_LAND_CONSUME.md). Register: [`../docs/flags/README.md`](../docs/flags/README.md).

| Pair | Verdict | Stamp |
|---|---|---|
| `EVERYWHERE_SHADOW` (`GTOS_JEV_EVERYWHERE_SHADOW`) | **APPLY_CANDIDATE ALREADY_LIVE** | alias of `FLUID_GATES_SHADOW`. **Not** listed as open `IN_PROVE` |
| `TRAIN_HARVEST` | **ALREADY_LIVE** `SHADOW+CALL=1` `APPLY=0` | confirm only. No env invented. Harvest attach + `cycle` `harvest=` CALL; `ready_to_apply=false`; live multiplier `1.0` |
| `DIG_MULTI_STAGE_GUARD` | **KILL** | SHADOW default/off **`0`**; APPLY unset/forbidden; removed from Challenge prove-only dual-flag track |

Hard: Dig `place=false` `apply=false`. Do not invent `NEWS_PROTOCOL`. `pack1b_beaten=false`. redacted_account / W7 untouched. `POLICY_C_SHADOW_EVAL` already `=1` — do not re-litigate.

Default is SHADOW off and APPLY off. Capture requires:

```powershell
$env:GTOS_JEV_FLUID_GATES_SHADOW = "1"
# do not set GTOS_JEV_FLUID_GATES_APPLY until hist-prove wins_preserved
Remove-Item Env:GTOS_JEV_FLUID_GATES_APPLY -ErrorAction SilentlyContinue
Remove-Item Env:GTOS_DIG_MULTI_STAGE_GUARD_APPLY -ErrorAction SilentlyContinue
```

---

## 1. Backup (host)

On `host-local\redacted_host\repo` before any copy:

```powershell
$ts = Get-Date -Format 'yyyyMMddHHmmss'
$bak = "host-local\redacted_host\repo.bak_chair_p0_$ts"
New-Item -ItemType Directory -Force -Path $bak | Out-Null
Copy-Item -Recurse -Force src\judgment $bak\src_judgment
if (Test-Path judgment) { Copy-Item -Recurse -Force judgment $bak\judgment }
if (Test-Path scripts) {
  Copy-Item -Force scripts\run_jev_fluid_gates_shadow.py "$bak\" -ErrorAction SilentlyContinue
  Copy-Item -Force scripts\run_p0_shadow_hooks_historical_prove.py "$bak\" -ErrorAction SilentlyContinue
}
```

Do **not** wholesale-copy `book_owner.py`. Do not remint tokens. Do not `git clean` LFS.

---

## 2. Pull / copy this tip

```powershell
cd host-local\redacted_host\repo
git fetch origin cursor/chair-p0-land-f5-live-2541
git checkout cursor/chair-p0-land-f5-live-2541
# or copy only:
#   src\judgment\
#   judgment\  (sidecar docs, schemas, FIRE1201 receipt, research_armed_tags.json)
#   scripts\run_jev_fluid_gates_shadow.py
#   scripts\run_p0_shadow_hooks_historical_prove.py
#   scripts\run_jev_everywhere_historical_prove.py
#   scripts\run_s14_historical_prove.py
#   scripts\run_s15_historical_prove.py
#   scripts\run_s16_prove.py
```

---

## 3. Recycle writer + judgment

Recycle the Challenge writer (login `0` / ns `operator` / magic `0`) and any judgment sidecar process. Do not recycle W7 / redacted_account / `GTOS_W7_*`.

```powershell
# recycle Challenge f5 writer / judgment workers only — host supervisor names
# Restart-ScheduledTask -TaskName 'GTOS_F5_ChallengeWriter'   # example; use the live task name
# Confirm argv still: login 0, ns operator, SHADOW=1, APPLY unset
```

Writer still places. Jev still does not `order_send`.

---

## 4. Prove script (KEEP wins must stay KEEP)

```powershell
$env:GTOS_JEV_FLUID_GATES_SHADOW = "1"
python3 scripts/run_p0_shadow_hooks_historical_prove.py `
  --log-dir host-local\redacted_host\repo\judgment\live\p0_shadow_prove `
  --score-out host-local\redacted_host\repo\judgment\live\p0_shadow_prove\scorecard.json `
  --receipt-out host-local\redacted_host\repo\judgment\live\p0_shadow_prove\fire1201.json
```

Bars (already measured on Challenge 0; re-run, do not invent):

- `apply=false`, `apply_true=0`, `order_send=0`, `invented_high=0`
- `wins_preserved=true` (KEEP tickets `291816474`, `293540988`, `291794419`)
- residuals PARKED (`291087142`, `293128383`)
- `research_candidate.status=EMPTY`, `hard_off_keep_research=false`

If APPLY env is set, the prove **exits 2**. That is the hist-prove refuse path.

One live sidecar cycle (still no broker):

```powershell
$env:GTOS_JEV_FLUID_GATES_SHADOW = "1"
python3 scripts/run_jev_fluid_gates_shadow.py
```

Logs: `judgment/live/jev_sidecar/admit/<day>/<cycle_id>.json`

---

## 5. Optional LABEL APPLY (only after §4)

Only if the prove receipt has `wins_preserved=true` and `hard_off_keep_research=false`:

```powershell
$env:GTOS_JEV_FLUID_GATES_SHADOW = "1"
$env:GTOS_JEV_FLUID_GATES_APPLY = "1"
# plus an A1/A2/A3/W_named prove file under judgment/live/prove/
python3 scripts/run_jev_fluid_gates_shadow.py --prove-site UB-AUTH-010 --stake label_assist --confidence 0.7
```

This writes a **LABEL draft** (`chair_verb: LABEL`). It never places. `place` / `remint` / `flatten` stay VETO. KEEP research is never hard-off.

---

## 6. Module_ATR research overlay (not live_armed_set)

`judgment/astra/research_armed_tags.json` names:

- `dsp_three_fresh_lower_lows`
- `dsp_spring_close_on_20low_through_the_box`

They appear on STATE `identity.research_armed_tags` and ALIVE_MENU as `research_sleeve:*`. They do **not** enter `armed_sleeves()` or `--tags`.

---

## 7. Tests on the land tip

```bash
python3 -m pytest -q tests/judgment
```

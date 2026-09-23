# HOST_APPLY_LANDING — 2026-09-17 (ICT)

**Goal:** Land Fable Jev Alive APPLY on Challenge f5-live VPS only (`redacted_host` / machineId `7cfa9657-805b-4e9c-9fbb-886c500f997b`).

**Authority:** Owner NAME “apply everything”; PR #10 head `b117c2339` (`cursor/jev-alive-organism-72cf`); follow `judgment/astra/lab/wires/HOST_APPLY_ALIVE.md`.

## Result: SUCCESS

| Check | Status |
|---|---|
| `src/judgment/` on host | **YES** — 18 modules at `host-local\redacted_host\repo\src\judgment\` |
| Inventory 48 fluid / 8 envelope | **YES** — `judgment/astra/JEV_GATE_INVENTORY.json` |
| bridge.py UB-AUTH-010 splice | **YES** — after final `_decide` (~L624→decision + observe ~L636) |
| book_owner.py observe splice | **YES** — after `cost_skip = _spread_cost_screen` (~L4158→observe ~L4169); **does not mutate `cost_skip`** |
| book_owner.py APPLY splice | **YES** — after `adjusted_unit` when already admitted (~L4254); `compose_shadow` + `maybe_haircut_unit` |
| Challenge env flags | **YES** — live pid 14816: `GTOS_JEV_ALIVE_SHADOW=1`, `GTOS_JEV_APPLY_LIVE=1`, `GTOS_JEV_A1_LOG=1` |
| W7 / redacted_account APPLY | **NOT set** — User/Machine env empty; FN workers untouched (pids 3636/5636 stayed up) |
| TypeSafe fingerprint | **`00000000`** (secrets + `.env.typesafe` + User key) |
| Writer / Challenge recycle | **YES** — controlled `bounce_f5.ps1` / `GTOS_F5_FTMO` only (required for import + env) |
| Sit after | **healthy, flat** — login 0, positions 0, pending 0, occupied [] |
| Ticket 293332188 | **CLOSED** (`broker_closed` 2026-09-17T11:10:58Z) — leave-orig lock still on; **no remint** |
| Place / remint / flatten from this seat | **NONE** |

## What changed (host)

### 1. Copied package (not wholesale `book_owner.py`)

From PR head `b117c2339` onto dirty tree `host-local\redacted_host\repo\`:

- `src/judgment/*.py` (full unbound package)
- `judgment/astra/JEV_GATE_INVENTORY.json`
- `judgment/astra/lab/wires/{HOST_APPLY_ALIVE.md,APPLIED_NAMED.json,WAVE_APPLY_RECEIPT.json,W_NAMED_PROVE.json,F5_JEV_004_PROVE.json,W_DUAL_PROVE.json}`

### 2. Splices only (mapped sites)

**`bridge.py`** (host was 652 lines → 667): final admit path `return _decide(...)` → `decision = _decide(...);` env-gate (`GTOS_JEV_A1_LOG` **or** `GTOS_JEV_ALIVE_SHADOW`) **before** import; `maybe_observe_ub_auth_010(decision, config)`; return decision unchanged.

**`book_owner.py`** (host ~10069 → ~10124; **not** replaced by GitHub 5k file):

1. After `cost_skip = self._spread_cost_screen(intent, tick)` — observe `UB-PLC-017` + `F5-JEV-004` + flow wire + `maybe_observe_fluid_at_place`. **Never changes `cost_skip`.**
2. After AI companion `adjusted_unit` on the already-admitted path — if `GTOS_JEV_APPLY_LIVE`: build `compose_shadow` from intent/tick and `maybe_haircut_unit(..., already_admitted=True)` with `login` + `ns=self._namespace`. Physical gate inside `apply_size` requires login `0` **and** ns `operator`. Leave-orig ticket `293332188` forced to 1.0 / no haircut. Cost tilt cannot refuse / cannot exceed 1.0.

Backups:

- `bridge.py.bak_jev_alive_20260917113940`
- `book_owner.py.bak_jev_alive_20260917113940`
- `f5_launch.ps1.bak_jev_alive_20260917`

### 3. Env (Challenge f5-live worker only)

Patched `host-local\redacted_host\f5_launch.ps1` (not User/Machine env, not W7 supervisor):

```
$env:GTOS_JEV_ALIVE_SHADOW = '1'
$env:GTOS_JEV_APPLY_LIVE = '1'
if (-not $env:GTOS_JEV_A1_LOG) { $env:GTOS_JEV_A1_LOG = '1' }
```

Proved on live Challenge python **pid 14816** via PEB env read.

### 4. Restart

**Required** (new package import + process env). Minimal safe recycle:

- `bounce_f5.ps1` → `schtasks /End` + `/Run` **GTOS_F5_FTMO** only
- Pre pids 12152/11832 → post pids **6356/14816** (+ launcher powershell 1752)
- W7/redacted_account left running
- Heartbeat after: `healthy: true`, `runtime_effect_now: true`, ns `operator`

## Sit after (ICT afternoon 2026-09-17)

```
login 0 bal 95196.4 eq 95196.4
day_net -119.53 to_pass ~14803.6
occupied [] fast_live False
positions 0 pending 0
```

Heartbeat (writer clock, UTC): healthy on new pid; gates all true.

Ticket **293332188**: `trade_lifecycle_status=closed`, `close_action=broker_closed`, `closed_at_utc=2026-09-17T11:10:58Z` — leave-orig; no remint from this landing.

## Explicit non-actions

- Did **not** wholesale-copy GitHub `book_owner.py`
- Did **not** edit `selector_v4.py`
- Did **not** set `GTOS_JEV_APPLY_LIVE` on W7 / redacted_account / User/Machine scope
- Did **not** place / remint / flatten / write inbox
- Did **not** convert envelope walls into Jev toys

## Fingerprint

TypeSafe key fingerprint **`00000000`** confirmed from:

- `host-local\redacted_host\secrets\TYPESAFE_API_KEY.txt`
- `host-local\redacted_host\repo\.env.typesafe`
- User env key (same fp)

## Source

- PR: https://github.com/Borr1/ai-trading-agent/pull/10
- Head: `b117c233971d90575bdbc7f6648dee8598b5c5c8`
- Playbook: `HOST_APPLY_ALIVE.md` (fetched from PR)

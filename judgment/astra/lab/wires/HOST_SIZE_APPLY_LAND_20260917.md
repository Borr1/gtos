# HOST_SIZE_APPLY_LAND — 2026-09-17

**Result: SUCCESS** · 2026-09-17 22:34:37 ICT (host clock UTC; report ICT)

| Check | Status |
|---|---|
| PR #10 tip into `src/judgment/` | **YES** — head `c946b019efaab9f96fb462a7c6e80a9d4fa57040` (`cursor/jev-alive-organism-72cf`) |
| `apply_size.py` risk_pct haircut | **YES** — size=10295; `_RISK_KEYS = ("risk_pct_per_trade", "unit_risk_pct") _SCALE_KEYS = _RISK_KEYS + _LOT_KEYS`; `haircut_challenge_unit`; `JEV_APPLY receipt` |
| Host `book_owner.py` splice | **YES** — replaced `compose_shadow(..., None)` + `maybe_haircut_unit` with `haircut_challenge_unit(..., evaluate_jev=True)`. Lines=10118. **Not** wholesale GH copy. |
| Bridge Wave L observe splice | **YES** — `maybe_observe_ub_auth_010` still present; bridge lines=667 untouched this land |
| Leave-orig paths | **UNTOUCHED** — `LEAVE_ORIG_TICKETS` / `293332188` still gated in `process_lock.py` |
| Challenge writer recycle | **YES** — `bounce_f5.ps1` / schtasks `GTOS_F5_FTMO` only. Pre 3064/14472 → post CH pids: 5744,15540 · hb pid **15540** |
| Challenge env (live PEB) | **YES** — `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1` `GTOS_JEV_A1_LOG=1` on writer pid 15540 |
| TypeSafe fingerprint | **`00000000`** |
| W7 / redacted_account bounce | **NO** — FN pids 3636,5636 stayed up |
| Remint / place / flatten from this seat | **NONE** |
| NEWS_PROTOCOL invent | **NO** |

## Source
- PR: https://github.com/Borr1/ai-trading-agent/pull/10
- Head: `c946b019efaab9f96fb462a7c6e80a9d4fa57040`
- Message: `fix(judgment): scale F5 risk_pct_per_trade on APPLY_LIVE haircut`
- Playbook: `judgment/astra/lab/wires/HOST_SIZE_APPLY_FIX.md`
- machineId: `7cfa9657-805b-4e9c-9fbb-886c500f997b` (redacted_host)
- Repo: `host-local\redacted_host\repo` branch `f5-live`
- Backup: `host-local\redacted_host\_size_apply_land_bak_20260917_153117`

## Splice hits (book_owner)
- L4169: from src.judgment.a1_log import maybe_observe_fluid_at_place, maybe_observe_ub_plc_017
- L4170: maybe_observe_ub_plc_017(intent, tick, cost_skip)
- L4171: maybe_observe_fluid_at_place(intent, tick, cost_skip)
- L4254: # HOST_SIZE_APPLY_FIX: haircut_challenge_unit scales risk_pct_per_trade (prove C).
- L4258: from src.judgment.apply_size import haircut_challenge_unit
- L4274: adjusted_unit = haircut_challenge_unit(

## Bridge hit
- L636: from src.judgment.a1_log import maybe_observe_ub_auth_010
- L637: maybe_observe_ub_auth_010(decision, config)

## Heartbeat after
```
pid=15540 healthy=True ns=operator runtime_effect_now=True ts=2026-09-17T15:33:36.480949+00:00
```

## Sit after (MetaTrader5 portable `C:\MT5\FTMO`)
```
login 0 bal 94709.05 eq 94709.05 profit 0.0
server FTMO-Server
n_pos 0 n_pending 0 positions []
ts_utc 2026-09-17T15:32:53Z (22:32 ICT)
```

## Prove-C checklist (do **not** wait for a place from this seat)
On the next `cost_skip is None` place with `combined_live_tilt ≠ 1.0`:
1. Writer log contains `JEV_APPLY receipt` with `before.risk_pct_per_trade ≠ after.risk_pct_per_trade`.
2. `apply_receipt.jsonl` last row: same snapshot, symbol/sleeve named.
3. Trade record / Telegram `f5_intended_risk_usd` (or host `risk_usd`) **≠ $150**. Example: tilt `0.8152` → intended ≈ `$122` (150 * 0.8152).
4. Leave-orig / W7 ns / APPLY_LIVE off → receipt absent and risk stays baseline.

## Non-actions
- No wholesale GitHub `book_owner.py` / `bridge.py` copy
- No selector_v4 edit
- No `GTOS_JEV_APPLY_LIVE` on W7 / redacted_account / User/Machine scope
- No place / remint / flatten / inbox write
- No redacted_account / W7 bounce

## Prior digs
- `HOST_SIZE_APPLY_PROOF_20260917.md` verdict **B** (armed; `_scale_unit` missed `risk_pct_per_trade`)
- This land closes the B→C code gap; C proof awaits next live tilt place.

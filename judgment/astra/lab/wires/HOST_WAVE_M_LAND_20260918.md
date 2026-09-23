# HOST_WAVE_M_LAND — 2026-09-18 SUCCESS

**Clock:** host UTC; ICT = UTC+7

## Answer-first
Wave M landed on Challenge f5-live only. Tip `76921a4cb`. Fresh Challenge XAU M15/H4/D1 books written. Writer recycled. FN/W7 untouched. Prove C still pending first tilted live place.

## Landed
- Tip SHA: `76921a4cbac57fe2cb15f93ab79c42f24b5c7905`
- `src/judgment/` (incl. `host_events.py`, `apply_size.py` risk_pct + haircut_challenge_unit)
- wires: `WAVE_M_RECEIPT.json`, `FLUID_PROVE_LEDGER`, `HOST_STATE_SUFFICIENT.md`, inventory
- `book_owner.py`: kept existing `haircut_challenge_unit` splice (3 hits) — no wholesale copy
- Backup: `host-local\redacted_host\_wave_m_land_bak_20260918_014103`

## Books refresh
- Pulled from MT5 portable `C:\MT5\FTMO` login **0**
- Wrote `judgment/astra/lab/challenge_shadow_20260917/XAUUSD_{M15,H4,D1}.csv` and `challenge_shadow_bars/multi/`
- M15 span ~2026-08-19 → **2026-09-18T01:30:00Z** (lag <12h at land)
- `challenge_tape_present('XAUUSD')` → **True**

## Writer
- Bounce via `bounce_f5.ps1` / scheduled task `GTOS_F5_FTMO` only
- Challenge pids after bounce: **5676**, **7480** (ns `operator`, `C:\MT5\FTMO`)
- redacted_account pids **3636**, **5636** still up
- Launch script still sets `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1` `GTOS_JEV_A1_LOG=1`
- Import smoke OK: haircut + risk keys + tape present

## Sit after (~01:43Z / 08:43 ICT)
login 0 bal 94364.07 eq 94489.48 day_net -342.92
OPEN GBPJPY 293540988 LONG leave orig SL 207.826 ~+0.83R

## Prove-C (still pending)
Next `cost_skip=None` place with `combined_live_tilt ≠ 1` → `JEV_APPLY` receipt before≠after risk_pct; `f5_intended_risk_usd` ≠ 150.
Fresh books should allow `state_sufficient=true` so flow can leave 1.0.

## Untouched
No place / remint / flatten. No NEWS_PROTOCOL invent. Envelope walls stay integers.

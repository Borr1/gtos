# Chair peer hydrate 2026-09-18 — zip landed, shadow-only

Chair attached `_peer_multi_20260918.zip` from VPS `challenge_shadow_bars/multi`.
Unzipped into `judgment/astra/lab/challenge_shadow_20260917/multi/`.
`time_utc` = server−3h (`broker_time` = utc+3). No `time_server_labeled` column — admit still accepts (`offset_ok=None`).

Channel: **chair_attached_zip**. This VM still has no host-admin / host-mesh / `~/.gtos/vps.env`. `copy_multi_csvs_if_present()` copied **0**. April `exports/multi_instrument/*` still refused.

CSVs are **not committed** (`multi/.gitignore`). Re-hydrate from the zip or `GTOS_CHALLENGE_BAR_MULTI`.

## Landed (admit ok)

| Symbol | M15 n | first_utc | last_utc | on-disk stem |
|---|---:|---|---|---|
| EURUSD | 2000 | 2026-08-20T07:15:00Z | **2026-09-18T03:00:00Z** | `EURUSD` |
| GBPUSD | 2000 | 2026-08-20T06:15:00Z | **2026-09-18T03:00:00Z** | `GBPUSD` |
| USDJPY | 2000 | 2026-08-20T07:00:00Z | **2026-09-18T03:00:00Z** | `USDJPY` |
| US30 | 2000 | 2026-08-19T05:15:00Z | **2026-09-18T03:00:00Z** | `US30_cash` (also `US30.cash`, `US30`) |
| XAUUSD (multi zip) | 2000 | 2026-08-19T05:15:00Z | 2026-09-18T01:30:00Z | unused for identity |
| XAUUSD (parent drop) | 1597 | 2026-08-25T00:00:00Z | 2026-09-17T10:30:00Z | **identity** — `CHALLENGE_BAR_DIR` first |

`landed_challenge_symbols()` = `XAUUSD, EURUSD, GBPUSD, US30, USDJPY`.
US30 first VPS pass: `ftmo_symbol_resolve_failed`. Zip supersedes: claimed + hydrated via aliases. Harness resolves `US30` → `US30_cash_*` first.

UK100 / EURGBP still missing. Not required for CA-USD/CORR/RSK/IDX.

## Prove re-run (97 shadow rows)

`python3 scripts/jev_cross_asset_prove.py` after unzip. Bars unchanged (20 / 5 / 2). **No CA-\* APPLY. No new size axis.**

| ID | prior | now | dec / moved / distinct | vals | apply |
|---|---|---|---|---|---|
| CA-OCC-001 | PROVED_SHADOW | PROVED_SHADOW | 97 / 31 / 3 | 0.0=17, 1.0=66, 2.0=14 | false |
| CA-LIQ-001 | PROVED_SHADOW | PROVED_SHADOW | 97 / 30 / 3 | 0.0=21, 1.0=67, 2.0=9 | false |
| CA-EVT-001 | PROVED_SHADOW | PROVED_SHADOW | 97 / 97 / 2 | false=93, true=4 | false |
| **CA-USD-001** | NOT_PROVED | **PROVED_SHADOW** | 97 / 97 / 3 | usd_flat=35, usd_up=56, usd_down=6 | **false** |
| **CA-CORR-001** | NOT_PROVED | **PROVED_SHADOW** | 97 / 32 / 2 | against_usd=32, no_clear=65 | **false** |
| **CA-RSK-001** | NOT_PROVED | **PROVED_SHADOW** | 97 / 97 / 3 | mixed=92, risk_off=2, risk_on=3 | **false** |
| **CA-IDX-001** | NOT_PROVED | **PROVED_SHADOW** | 97 / 87 / 2 | with_us30=87, no_clear=10 | **false** |

Flips vs pre-zip prove: **four** — CA-USD-001, CA-CORR-001, CA-RSK-001, CA-IDX-001 all `NOT_PROVED → PROVED_SHADOW`.
Zero APPLY flips. `physical_size.new_size_axis_applied = false`. Combined tilt still flow × cost on all 97 rows.

CA-CORR on this tape is **against_usd or no_clear** — no `with_usd` row. CA-IDX is mostly `with_us30`. CA-RSK is almost all `mixed` (US30 trend and yen label disagree). Labels only.

## Still forbidden

- APPLY any CA-\* wire
- New size axis on `live_flow × live_cost`
- Wear April historical
- Commit the peer CSVs
- Treat zip XAU as the Challenge XAU identity (parent drop stays)

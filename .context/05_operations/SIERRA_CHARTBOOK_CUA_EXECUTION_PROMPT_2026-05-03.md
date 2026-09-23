# Sierra Chartbook CUA Execution Prompt - 2026-05-03

Status: GUI/data-prep execution prompt  
Audience: Codex app / computer-use session with mouse + keyboard control  
Promotion posture: `NO_PROMOTION_VERDICT`  
Live-system impact: none  
AI/API cost: none

## Purpose

Use a GUI-capable Codex app session to execute the Sierra chartbook prep plan before the expanded-OOS research goal session.

This is not the research goal itself. This session only prepares Sierra local data coverage by opening/saving charts and verifying that Sierra creates or updates `.scid` / `.depth` files.

## Bottom Line

This should be possible with computer control if Sierra Chart is accessible on the desktop.

Expected reliability:

- High for opening Sierra, using `File >> Find Symbol`, opening Intraday charts, and saving chartbooks.
- Medium for choosing exact active contracts because the UI may list multiple months and the agent must record the exact symbol selected.
- Medium/low for configuring depth recording if Sierra's UI differs from the cached docs; stop and report if unclear.
- Not suitable for clicking trading controls, changing broker/data-service settings, or making live-system changes.

## Mandatory Context To Read

1. `AGENTS.md`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/research_current_state.md`
6. `research/program_control/SIERRA_AND_MT5_DATA_ACCESS_PLAYBOOK_2026-05-03.md`
7. `research/program_control/SIERRA_CHARTBOOK_PREP_PLAN_2026-05-03.md`
8. `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_SYMBOL_CATALOG_DOWNLOAD_AND_SCID_PROBE_2026-05-03.md`

## Hard Rules

- Do not place trades.
- Do not click Buy, Sell, Trade DOM order controls, flatten, cancel, or account-management actions.
- Do not change live GTOS config, prompts, execution code, risk settings, or broker account settings.
- Do not push to remote.
- Do not stage unrelated runtime dirt.
- Do not assume a chart was prepared until a file-level check confirms `.scid` or `.depth` presence/updates.
- If Sierra asks for payment, exchange activation, data-service changes, credentials, or legal agreements, stop and report.
- If the UI path is ambiguous for market depth recording, stop and report rather than guessing.

## Objective

Create or update two Sierra chartbooks:

1. `GTOS_HISTORICAL_RESEARCH`
2. `GTOS_FORWARD_DEPTH_CAPTURE`

Then produce a versioned execution report with:

- exact symbols opened,
- chartbook names/paths if visible,
- `.scid` files created/updated,
- `.depth` files created/updated,
- symbols that blocked,
- UI ambiguities,
- next actions for the research goal session.

Recommended report path:

`research/sierrachart_data_source_research_2026-05-02/SIERRA_CHARTBOOK_CUA_EXECUTION_REPORT_2026-05-03.md`

## Pre-Run Inventory

Before touching Sierra, run:

```powershell
python scripts\generate_live_state.py
python scripts\inspect_sierra_scid.py --data-dir C:\SierraChart\Data --inventory-json data\sierrachart_exports\pre_cua_scid_inventory_2026-05-03.json
Get-ChildItem C:\SierraChart\Data\MarketDepthData -Force | Sort-Object LastWriteTime -Descending | Select-Object Name,Length,LastWriteTime
```

If `data\sierrachart_exports` does not exist, create it inside the repo.

## Chartbook 1: GTOS_HISTORICAL_RESEARCH

Open Sierra Chart. If already running, use the existing instance.

Create or open a chartbook named `GTOS_HISTORICAL_RESEARCH`.

For each row below:

1. Use `File >> Find Symbol`.
2. Search/select the active listed contract for the pattern.
3. If Sierra requires manual typing, type the exact symbol.
4. Click `Open Intraday Chart`.
5. Record the exact symbol that Sierra opens.
6. Wait long enough for the chart/data download to begin.
7. Save the chartbook periodically.

Do not manually export CSV.

### P0 Historical Charts

| Need | Pattern |
|---|---|
| NAS100 | `NQ?##-CME` |
| NAS100 micro | `MNQ?##-CME` |
| US30 | `YM?##-CBOT` |
| US30 micro | `MYM?##-CBOT` |
| Gold | `GC?##-COMEX` |
| Gold micro | `MGC?##-COMEX` |
| Silver | `SI?##-COMEX` |
| Silver micro | `SIL?##-COMEX` |
| USDJPY inverse proxy | `6J?##-CME` |
| GBPUSD proxy | `6B?##-CME` |

### P1 Historical Charts

| Need | Pattern |
|---|---|
| EURUSD proxy/control | `6E?##-CME` |
| S&P control | `ES?##-CME` |
| S&P micro | `MES?##-CME` |
| Oil regime | `CL?##-NYMEX` |
| Oil micro | `MCL?##-NYMEX` |
| Rates regime | `ZN?##-CBOT` |
| Bond/rates regime | `ZB?##-CBOT` |
| Russell control | `RTY?##-CME` |
| Russell micro | `M2K?##-CME` |

### P2 Historical Charts

Open these only if P0/P1 completes cleanly and Sierra remains stable.

| Need | Pattern |
|---|---|
| AUD control | `6A?##-CME` |
| CAD control | `6C?##-CME` |
| CHF control | `6S?##-CME` |
| VIX control | `VX?##-CFE` |
| Mini VIX control | `VXM?##-CFE` |

## Chartbook 2: GTOS_FORWARD_DEPTH_CAPTURE

Create or open a chartbook named `GTOS_FORWARD_DEPTH_CAPTURE`.

Use exact active contracts. Start smaller than the historical chartbook.

Open Intraday charts for:

- `NQ?##-CME`
- `MNQ?##-CME`
- `YM?##-CBOT`
- `MYM?##-CBOT`
- `GC?##-COMEX`
- `MGC?##-COMEX`
- `SI?##-COMEX`
- `SIL?##-COMEX`
- `6J?##-CME`
- `6B?##-CME`
- `6E?##-CME`
- `ES?##-CME`
- `MES?##-CME`
- `CL?##-NYMEX`
- `ZN?##-CBOT`

Then attempt to enable market-depth recording only if the UI path is clear and consistent with Sierra docs/settings.

If depth setup is ambiguous, save the chartbook with the charts open and report:

`DEPTH_RECORDING_UI_AMBIGUOUS`

Do not guess.

## Verification

After chartbook prep, run:

```powershell
python scripts\inspect_sierra_scid.py --data-dir C:\SierraChart\Data --inventory-json data\sierrachart_exports\post_cua_scid_inventory_2026-05-03.json
Get-ChildItem C:\SierraChart\Data\MarketDepthData -Force | Sort-Object LastWriteTime -Descending | Select-Object Name,Length,LastWriteTime
```

Compare pre/post inventories. The success condition is file-level evidence:

- new `.scid` files exist for opened symbols, or
- existing `.scid` files have updated `LastWriteTime` / record counts, and
- depth files exist/update for any symbols where depth was actually enabled and market data is active.

Weekend/closed-market caveat: depth files may not grow meaningfully until the market is active. In that case, report chartbook setup complete but depth capture pending active session verification.

## Output Report Structure

Write:

`research/sierrachart_data_source_research_2026-05-02/SIERRA_CHARTBOOK_CUA_EXECUTION_REPORT_2026-05-03.md`

Required sections:

1. Summary
2. Chartbooks Created/Updated
3. Symbols Opened
4. Symbols Blocked
5. Pre/Post `.scid` Inventory Delta
6. Pre/Post `.depth` Inventory Delta
7. Depth Recording Status
8. Ambiguities / Owner Follow-Up Needed
9. Instructions For Fresh Expanded-OOS Goal Session

Commit only the execution report and any intentional context updates. Do not commit local data exports unless explicitly useful and small.

## Fresh Goal Session Handoff

If chartbook prep succeeds, tell the fresh expanded-OOS goal session:

> Sierra chartbooks were prepared by GUI execution. Start by reading `research/sierrachart_data_source_research_2026-05-02/SIERRA_CHARTBOOK_CUA_EXECUTION_REPORT_2026-05-03.md`, then run `scripts/inspect_sierra_scid.py` inventory and use the available Sierra files according to `research/program_control/SIERRA_CHARTBOOK_PREP_PLAN_2026-05-03.md`. Preserve `NO_PROMOTION_VERDICT`.

# GTOS MT5 Expert Advisors

## ChartMarker.mq5 (v2.0)

Renders the GTOS Python agent's decisions on each MT5 chart as a rich, at-a-glance live view. One chart per instrument; the EA polls the agent's signal file every 5 seconds and draws:

- **Info panel** (top-right by default) with current KZ, active trade summary, today's stats, and the last decision
- **Color-coded markers** per decision type — direction-aware (LONG green / SHORT red) when the field or `detail` text reveals it
- **Trade lifecycle overlay**: vertical entry line + horizontal SL/TP1/TP2/TP3 lines while a trade is open; entry→exit connector + realized-R label after close
- **Kill-zone shaded regions** (London / NY / Tokyo) per instrument schedule
- **Filterable marker types** via input parameters (toggle off NO_TRADE dots when the chart gets cluttered)
- **Rich tooltips** showing decision, direction, framework, grade, confidence, SL/TP/lots/risk, and (on close events) realized R / MFE / MAE / hold time

### Installation

1. Open MetaTrader 5
2. **File → Open Data Folder** (this opens the terminal data directory)
3. Navigate to `MQL5\Experts\`
4. Copy `ChartMarker.mq5` from this repo's `mt5_ea/` folder into `MQL5\Experts\` (overwrite the v1 if present)
5. In MetaEditor, open `ChartMarker.mq5` and press **F7** to compile (should produce `ChartMarker.ex5` with 0 errors)
6. Back in MT5: **Navigator → Expert Advisors → ChartMarker**, drag onto each chart you want monitored (XAUUSD, USDJPY, GBPJPY, GBPUSD, US30, NDX100, XAGUSD)
7. In the dialog: tick **"Allow algorithmic trading"** and **"Allow modification of Signal settings"** (the EA only READS files; this is just MT5's default permission set)
8. The EA reads `agent_signals_<broker_symbol>.jsonl` from `MQL5\Files\`. The Python agent writes there automatically.

### Inputs (key ones)

| Group | Input | Default | Effect |
|---|---|---:|---|
| Display | `ShowInfoPanel` | `true` | Top-corner panel with current KZ + active trade + today's stats + last decision |
| Display | `ShowKZRegions` | `true` | Shaded London/NY/Tokyo rectangles per the instrument's schedule |
| Display | `ShowSLTPLines` | `true` | Horizontal SL / TP1 / TP2 / TP3 lines while a trade is open |
| Display | `ShowTradeLifecycle` | `true` | Entry→exit connector with realized-R label after close |
| Markers | `ShowExecuted` | `true` | Big direction-coloured arrow on EXECUTED / LIMIT_FILLED |
| Markers | `ShowCandidate` | `true` | Direction-coloured diamond on CANDIDATE; with grade label |
| Markers | `ShowRejected` | `true` | Red X on REJECTED gates |
| Markers | `ShowNoTrade` | `true` | Tiny grey dot on NO_TRADE — set false to declutter |
| Markers | `ShowLimitPlaced` | `true` | Hollow square on pending limit placement |
| Markers | `MaxNoTradeAgeBars` | `200` | Auto-purge NO_TRADE dots older than N bars |
| Layout | `PanelCornerCode` | `1` | 0=TL, 1=TR, 2=BL, 3=BR |
| Layout | `PollSeconds` | `5` | File-poll cadence |

All colours, font, panel offsets are inputs — tune to your chart theme.

### Marker key

| Decision | Glyph | Colour | Meaning |
|---|---|---|---|
| EXECUTED / LIMIT_FILLED | ▲▼ arrow | LONG=green / SHORT=red | Trade opened |
| CANDIDATE | diamond | direction-coloured | AI emitted a candidate setup |
| LIMIT_PLACED | hollow square | direction-coloured | Pending limit awaiting fill |
| TP1_HIT / immediate-on-TP1 BE | up-arrow | gold | 3R milestone hit, SL pulled to BE (J46-J49) |
| TP2_HIT / higher target (J46-J49) | exit arrow | green | 6R higher target hit, position closed |
| TIME_STOP (J48) | clock | dark orange | 12-bar (180min) timeout fired |
| BE_PULLED | flag | khaki | SL trailed to entry |
| SL_HIT / broker_closed | exit arrow | red | Stop loss hit |
| REJECTED / SKIPPED_CORRELATION | X | orange-red | Permission gate blocked the candidate |
| BLOCKED_CALENDAR / SKIP_NEWS_EVENT | warning | gold | News filter blocked the trade |
| NO_TRADE | tiny dot | grey | AI emitted no candidate (no setup) |
| EMERGENCY_STOP / CANARY_BLOCKED | X | magenta | Portfolio-level kill triggered |
| EXECUTION_FAILED | X | red | Order send failed |

### Forward compatibility

The EA reads structured fields when present (`direction`, `framework`, `grade`, `sl`, `tp1`, `tp2`, `tp3`, `lots`, `risk_pct`, `j46_j49_active`, `trade_id`, `realized_r`, `exit_type`, `mfe_r`, `mae_r`, `hold_min`) and falls back to keyword-extraction from the `detail` text when they're absent. The Python writer in `src/components/orchestrator.py:_write_chart_signal` already emits the structured fields whenever an active or pending trade is in scope.

### Troubleshooting

- **No markers appear**: confirm `agent_signals_<symbol>.jsonl` exists in `MQL5\Files\` and is non-empty. Filename uses the broker's symbol (e.g. `agent_signals_US30.jsonl` under redacted_account, `agent_signals_US30_cash.jsonl` under FTMO).
- **Panel shows "ACTIVE: none" but a position is open**: the EA tracks active state from EXECUTED/LIMIT_FILLED events. If the position was opened before the EA was attached, drop the EA + reattach (state rebuilds from file replay) or wait for the next event.
- **KZ regions look misaligned**: KZ times are UTC; chart shows broker-server time. The shaded regions are anchored to UTC instants, so they shift correctly relative to broker offset.
- **Compile error**: ensure you opened the file in MetaEditor (not just dragged it onto a chart). The `#property strict` directive requires the v5 toolchain.

### Versioning

- v1.0 — initial; arrows + dots + tooltip-only
- v2.0 — info panel, KZ regions, lifecycle overlay, structured-field parsing, day-rollover stats, configurable filters

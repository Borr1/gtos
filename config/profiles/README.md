# Prop-firm profile overlays

Each `<name>.yaml` here is a deep-merge overlay on top of
`config/agent_config.yaml`. The orchestrator applies the profile (if any)
BEFORE the per-instrument override, so profile risk settings flow through
to every symbol.

## Available profiles

| File | Risk authority | Reduced risk (DD) | Use case |
|---|---|---|---|
| `ftmo.yaml` | Account-specific aggregate drawdown budget plus per-instrument risk overrides; raw trade-count cap disabled | Profile/instrument resolved risk falls to configured drawdown-reduced risk | FTMO Server3 $100K Challenge staged namespace |
| `redacted_account.yaml` | vNext selected-cell risk plus prop-safe aggregate drawdown budget and per-instrument risk overrides; raw trade-count cap disabled for governed vNext rows | Profile/instrument resolved risk falls to configured drawdown-reduced risk | redacted_account Server 2 live namespace |
| `denominator_capture_research.yaml` | No execution authority; `deployment.phase=1` and `trading_enabled=false` | N/A | Explicit opt-in denominator forward-capture logging profile for research/source repair |

## Activation

Precedence: `--profile` CLI > `GTOS_PROFILE` env var > no overlay (base config).

```bash
# Option 1: CLI flag (per-process)
python run_agent.py --profile redacted_account --symbol XAUUSD --mode demo

# Option 2: env var (applies to all spawned processes — preferred for watchdog)
# Windows system-wide:
setx GTOS_PROFILE redacted_account
# or one-shot in shell:
set GTOS_PROFILE=redacted_account && python run_agent.py --symbol XAUUSD --mode demo

# Default (no flag, no env): base agent_config.yaml used as-is.
```

The Windows watchdog path sets `GTOS_PROFILE=redacted_account` unless explicitly
overridden; FTMO replay/research routes must name their FTMO replay risk profile
instead of inheriting that live primary profile by accident.

## Adding a new profile

Only list the keys that DIFFER from the base:

```yaml
profile_name: myfirm
risk:
  risk_per_trade_pct: 0.5
drawdown_reduction:
  reduced_risk_pct: 0.125
```

Save as `config/profiles/myfirm.yaml`. Add a row to the table above.

## FTMO account-specific profile

- `operator_profile.yaml`: generated from local FTMO Server3 read-only MT5 capture in `research\operations\vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02`.
- `ftmo.yaml`: compatibility pointer containing the same captured account/server aliases and geometry; do not treat it as a universal FTMO template.
- FTMO dual-broker follower risk authority is not `max_concurrent`; it projects account-specific current equity, day-start baseline, open stop-loss exposure, pending risk, the 5% daily loss objective, 10% overall loss objective, 4% internal daily overlay, and 1% overall cushion before copying an intent.
- redacted_account primary vNext risk authority is not a raw `max_concurrent` pin. Current selected-cell governed vNext rows bypass the legacy count cap and are governed by selected-cell risk plus the prop-safe aggregate drawdown budget.

## VPS terminal binding

- redacted_account live authority: `C:\Program Files\MetaTrader 5\terminal64.exe`, data path `host-local\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`, namespace `redacted_account_live_bee34003`.
- FTMO staged authority: `C:\MT5\FTMO\terminal64.exe`, portable data path `C:\MT5\FTMO`, namespace `operator_profile`.
- `C:\MT5\redacted_account` is staged/unused unless a future process/account proof shows that terminal is active.

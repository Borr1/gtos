# AUDIT 09: CONFIG (agent_config.yaml + profiles)

909 lines + 60 ftmo.yaml + 130 redacted_account.yaml = 1099 lines, 650 effective keys.

## YAML validation
ALL YAML valid. Per-instrument override completeness matrix verified.

## SL Buffers
- Tight-FX (EURUSD/GBPUSD) SL buffers 0.50/8 ticks identical across both profiles
- USDJPY 0.30/5 ticks both profiles
- Metals reduced to 0.5% in FN
- NAS100 0.25% conservatively
- US30/US30_cash 1% explicit pin

## Framework state
- fvg_fill RE-ENABLED in `enabled_frameworks`
- v2 detector ACTIVE
- B.1 `correlation_gate_threshold: 0.4`
- C.3 sprt_halt config block validated

## Phase-4 stubs intentional
- mt5_login=0, obsidian_*

## Other findings
- NO stale T-numbered keys
- NO config-keys-referenced-in-code-but-missing-from-yaml
- Comments accurate

## WATCH
- NAS100 0.25% 3-day trial expiry 2026-04-30
- XAUUSD 0.5% reversion conditions documented

## Verdict
PASS for Monday.

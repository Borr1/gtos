# JEV_SLEEVE_SELECT — GBPJPY + XAGUSD F5 KEEP priors (SHADOW)

**ts:** 2026-09-20 20:01 ICT  
**place:** false · **apply:** false · Dig does not mutate live_armed_set

## What changed

Extended `F5_AFFINITY_KEEP_PRIORS` in `sleeve_select.py` (PR40 Edge KEEP names):

| Symbol | KEEP priors |
|--------|-------------|
| GBPJPY | `vss_fxcross_london_up_low`, `sub_mid_dn_revert` (tape KEEP only; never Package B SHORT / EURUSD mid alias) |
| XAGUSD | `sub_xvol_pullback`, `metals_core`, `metal_session_reversion` |

Also:
- `sub_mid_dn_revert` menu gate: allow only when tag ∈ that symbol's F5 priors (GBPJPY); still refuse on EURUSD
- Package B SHORT tag (`sub_mid_dn_re_proxy_eurusd_short_m15_atr`) EURUSD-only
- `alive_sleeves_for_symbol` injects same F5 priors after compose
- RESEARCH_ARMED ADD fragments + EFFECTIVE rebuild (n=10 tags)

## Smoke (SMOKE_OK)

- **GBPJPY menu:** `sub_mid_dn_revert`, `vss_fxcross_london_up_low`
- **XAGUSD menu:** `metal_session_reversion`, `metals_core`, `sub_xvol_pullback`
- **EURUSD:** no `sub_mid_dn_revert` leak; asian_fade + Package B SHORT still present

## Paths

- Dig: `research/codila_absorb/war_room/jev_sleeve_select/`
  - `sleeve_select.py`, `alive_sleeves_for_symbol.py`
  - `JEV_SLEEVE_SELECT_GBPJPY_XAGUSD_KEEP_SMOKE_20260920.json`
- Judgment: `judgment/warroom_shadow/src/judgment/sleeve_select.py` (+ alive twin)
- CL overlay EFFECTIVE: `close_loop/war_room_20260920/RESEARCH_ARMED_TAGS_OVERLAY_EFFECTIVE_20260920.json`

Dig idle after report. Chair APPLY still required for live.

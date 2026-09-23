# DATA_INVENTORY_ALL_INSTRUMENTS

Schema `gtos.judgment.data_inventory.v0`. Generated `2026-09-18T04:20:57Z`.
Challenge login `0` / `operator`. Sit as-of `2026-09-17T10:06:13Z`. Ticket `293332188` as-of `2026-09-17T07:30:55Z`.

## 0. Scope and lock

Chair ultragoal 2026-09-18: map every instrument GTOS/Challenge can see vs what Jev actually consumes. Find data gaps that block multi-instrument edge.

- never_place=True never_remint=True never_flatten=True never_apply_size=True
- never_invent_news_protocol=True never_import_selector_v4=True never_import_v4_timewarp=True
- This inventory does not place, remint, flatten, invent NEWS_PROTOCOL, or APPLY size wires.

## 1. Challenge-true bar contract

- `time_utc` = already server-3h; do not run NY+7.
- Required TFs for live admit: `M15, H4`. Optional: `D1`.
- Freshness `_MAX_LAG`: M15 12h, H4 36h, D1 5d. Stale tape is missing state, not last April close wearing a September hat.
- April `data/historical*` is not Challenge-true: `True`.
- Landing dirs: `/workspace/judgment/astra/lab/challenge_shadow_20260917, /workspace/judgment/astra/lab/challenge_shadow_20260917/multi, /workspace/judgment/astra/lab/challenge_shadow_bars/multi, /workspace/pipeline_state/ultimate_book/operator/judgment/state/_fable_bar_pull_20260917/multi, /workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi, /workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars`. Override: `GTOS_CHALLENGE_BAR_MULTI`.
- File stems: `US30` → `US30_cash`, `UK100` → `UK100_cash`.

## 2. Disk on this clone

- Landed Challenge-true symbols: **XAUUSD, EURGBP, EURUSD, GBPJPY, GBPUSD, US30, USDJPY**.
- Non-XAU Challenge books present: **True**.
- Chair 2026-09-18 zips `EURUSD, GBPUSD, USDJPY, US30, XAUUSD` + `GBPJPY, EURGBP`: present_here=True (box `/workspace/gtos`=False).
- XAU loader search: `parent then multi`; parent_equals_multi=True. Bound dir `judgment/astra/lab/challenge_shadow_20260917`; multi dir `judgment/astra/lab/challenge_shadow_20260917/multi`.
- XAU lag vs now `2026-09-18T04:20:57Z`: bound M15 last `2026-09-18T04:15:00Z` fresh (n=2000); no unused newer multi/ sibling; admit_now=yes.
- Host sit occupied `['XAUUSD']`; deals `{'XAUUSD': 22, 'EURUSD': 2, 'EURGBP': 2, 'US30': 14, 'UK100': 2, 'ETHUSD': 1, 'GBPUSD': 2, 'BTCUSD': 2}`; slate `{'GBPUSD': 10, 'USDJPY': 16, 'BTCUSD': 1, 'EURUSD': 11, 'XAUUSD': 12}`.
- Last shadow pack: n=97 sufficient=28 xau=28 non_xau=0 missing_m15=63.

## 3. Jev / Challenge table

| symbol | bars present | state assembled | scored live | gaps | next pull |
|---|---|---|---|---|---|
| `XAUUSD` | M15 n=2000 last=2026-09-18T04:15:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1 n=300 last=2026-09-17T21:00:00Z fresh time_utc | sit=yes (M15+H4=yes, family=study); now=yes; xau_sub=no | sit=7 deals=22 slate=12 occupied; shadow_sufficient=yes | april_historical_exists_do_not_wear | — |
| `EURUSD` | M15 n=2000 last=2026-09-18T03:00:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1=missing | sit=yes (M15+H4=yes, family=house_keep); now=yes; xau_sub=no | sit=0 deals=2 slate=11 flat; shadow_sufficient=no | d1_optional_missing, april_historical_exists_do_not_wear | EURUSD D1 optional |
| `GBPUSD` | M15 n=2000 last=2026-09-18T03:00:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1=missing | sit=yes (M15+H4=yes, family=house_keep); now=yes; xau_sub=no | sit=0 deals=2 slate=10 flat; shadow_sufficient=no | d1_optional_missing, april_historical_exists_do_not_wear | GBPUSD D1 optional |
| `BTCUSD` | M15=missing; H4=missing; D1=missing | sit=no (M15+H4=no, family=house_hard_off); now=no; xau_sub=no | sit=1 deals=2 slate=1 flat; shadow_sufficient=no | house_hard_off_trade_surface, do_not_pull_as_trade_surface | — |
| `EURGBP` | M15 n=2000 last=2026-09-18T04:00:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1=missing | sit=yes (M15+H4=yes, family=house_keep); now=yes; xau_sub=no | sit=0 deals=2 slate=0 flat; shadow_sufficient=no | d1_optional_missing, april_historical_exists_do_not_wear | EURGBP D1 optional |
| `US30` | M15 n=2000 last=2026-09-18T03:00:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1=missing | sit=yes (M15+H4=yes, family=house_hard_off); now=yes; xau_sub=no | sit=0 deals=14 slate=0 flat; shadow_sufficient=no | house_hard_off_trade_surface, april_historical_exists_do_not_wear | — |
| `UK100` | M15=missing; H4=missing; D1=missing | sit=no (M15+H4=no, family=study); now=no; xau_sub=no | sit=0 deals=2 slate=0 flat; shadow_sufficient=no | challenge_m15_h4_missing, april_historical_exists_do_not_wear | UK100 M15+H4 Challenge-true (time_utc=server-3h) |
| `ETHUSD` | M15=missing; H4=missing; D1=missing | sit=no (M15+H4=no, family=house_hard_off); now=no; xau_sub=no | sit=0 deals=1 slate=0 flat; shadow_sufficient=no | optional_risk_peer_not_trade_surface, april_historical_exists_do_not_wear | ETHUSD M15+H4 optional risk peer only — not a trade surface |
| `USDJPY` | M15 n=2000 last=2026-09-18T03:00:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1=missing | sit=yes (M15+H4=yes, family=house_keep); now=yes; xau_sub=no | sit=0 deals=0 slate=16 flat; shadow_sufficient=no | d1_optional_missing, april_historical_exists_do_not_wear | USDJPY D1 optional |
| `XAGUSD` | M15=missing; H4=missing; D1=missing | sit=no (M15+H4=no, family=study); now=no; xau_sub=no | sit=0 deals=0 slate=0 flat; shadow_sufficient=no | occupancy_cluster_no_jev_priority, april_historical_exists_do_not_wear | XAGUSD M15+H4 optional occupancy peer |
| `GBPJPY` | M15 n=2000 last=2026-09-18T04:00:00Z fresh time_utc; H4 n=500 last=2026-09-18T01:00:00Z fresh time_utc; D1=missing | sit=yes (M15+H4=yes, family=house_keep); now=yes; xau_sub=no | sit=0 deals=0 slate=0 flat; shadow_sufficient=no | d1_optional_missing, april_historical_exists_do_not_wear | GBPJPY D1 optional |

Library hazard: `score_sit` / `score_slate` default `load_gold_books()` (April XAU). `scripts/jev_challenge_shadow.py` overrides with `load_all_landed_challenge_books()`.

## 4. GTOS-wide census

- `MULTI_SYMBOL_PRIORITY` = `EURUSD, GBPUSD, BTCUSD, EURGBP, US30, UK100, ETHUSD`; optional `USDJPY`.
- `GTOS_24_SYMBOL_SURFACE` n=24 matches `VNEXT_24_SYMBOLS`: True.
- FTMO profile `operator_profile` instruments n=42.
- Armed W7 set (do not rewrite): `{'operator_profile': ['crypto', 'energy_agri', 'sub_xvol_pullback'], 'redacted_account_live_bee34003': ['crypto', 'energy_agri', 'sub_xvol_pullback']}`.
- House hard-off families `bleed, orb_crypto, idxrev, xa_huge, mx_us30`; keep `spring, vss`.

| symbol | GTOS-24 | FTMO profile | Jev watch | Challenge landed | April M15 present |
|---|---|---|---|---|---|
| `AUDJPY` | yes | yes | no | no | yes |
| `AUDUSD` | yes | yes | no | no | yes |
| `AUS200_cash` | no | no | no | no | no |
| `AVAUSD` | no | yes | no | no | no |
| `BTCUSD` | yes | yes | yes | no | yes |
| `CADJPY` | no | yes | no | no | no |
| `CHFJPY` | yes | yes | no | no | yes |
| `CORN_c` | no | yes | no | no | no |
| `COTTON_c` | no | yes | no | no | no |
| `DASHUSD` | no | yes | no | no | no |
| `ETHUSD` | yes | yes | yes | no | yes |
| `EU50_cash` | no | yes | no | no | no |
| `EURGBP` | yes | yes | yes | yes | yes |
| `EURJPY` | yes | yes | no | no | yes |
| `EURUSD` | yes | yes | yes | yes | yes |
| `FRA40_cash` | no | yes | no | no | no |
| `GBPJPY` | yes | yes | yes | yes | yes |
| `GBPUSD` | yes | yes | yes | yes | yes |
| `GER40` | yes | yes | no | no | yes |
| `GER40_cash` | no | no | no | no | no |
| `HEATOIL_c` | no | no | no | no | no |
| `JP225` | yes | yes | no | no | yes |
| `JP225_cash` | no | no | no | no | no |
| `LTCUSD` | no | yes | no | no | no |
| `NAS100` | yes | yes | no | no | yes |
| `NATGAS_cash` | no | no | no | no | no |
| `NZDJPY` | no | yes | no | no | no |
| `NZDUSD` | yes | yes | no | no | yes |
| `SPN35_cash` | no | no | no | no | no |
| `SPX500` | yes | yes | no | no | yes |
| `UK100` | yes | yes | yes | no | yes |
| `UKOIL_cash` | yes | yes | no | no | no |
| `US100_cash` | no | no | no | no | no |
| `US2000_cash` | no | yes | no | no | no |
| `US30` | yes | yes | yes | yes | yes |
| `US30_cash` | yes | yes | no | yes | yes |
| `US500_cash` | no | no | no | no | no |
| `USDCAD` | yes | yes | no | no | yes |
| `USDCHF` | yes | yes | no | no | yes |
| `USDJPY` | yes | yes | yes | yes | yes |
| `USOIL_cash` | yes | yes | no | no | no |
| `XAGAUD` | no | yes | no | no | no |
| `XAGEUR` | no | yes | no | no | no |
| `XAGUSD` | yes | yes | yes | no | yes |
| `XAUAUD` | no | yes | no | no | no |
| `XAUEUR` | no | yes | no | no | no |
| `XAUUSD` | yes | yes | yes | yes | yes |
| `XPDUSD` | no | yes | no | no | no |
| `XPTUSD` | no | yes | no | no | no |
| `XRPUSD` | no | yes | no | no | no |
| `XTZUSD` | no | yes | no | no | no |

Sleeve generator surfaces (code-known, not Challenge-landed):

- **built**
  - `metals_core`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD
  - `metals_softband`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD
  - `crypto`: BTCUSD, DASHUSD
  - `energy_agri`: USOIL_cash, UKOIL_cash
  - `idxrev`: SPX500, UK100, JP225, GER40, US30_cash
  - `metals_ob_micro`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD
  - `sub_xvol_pullback`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD, USOIL_cash, UKOIL_cash, CORN_c, COTTON_c, SPX500, UK100, FRA40_cash, EU50_cash, US2000_cash, JP225, GER40, US30_cash
  - `sub_mid_dn_revert`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD, USOIL_cash, UKOIL_cash, CORN_c, COTTON_c, SPX500, UK100, GER40, US30_cash, BTCUSD, GBPJPY, USDJPY, EURJPY, AUDJPY, CHFJPY
  - `vp_euidx_pocgrav`: GER40, UK100
  - `fx_jpy`: GBPJPY, USDJPY
  - `fx_jpy_ny`: GBPJPY, USDJPY
- **candidate_built**
  - `vol_compression`: BTCUSD, ETHUSD, XTZUSD
  - `asian_fade`: EURUSD, GBPUSD
  - `ny_crypto_momentum`: BTCUSD, ETHUSD
  - `metal_session_reversion`: XAUUSD, XAGUSD
  - `asia_pdl_fade`: EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, CHFJPY, AUDJPY, EURGBP, XAUUSD, XAGUSD, XPTUSD, XPDUSD, BTCUSD, ETHUSD, XRPUSD, XTZUSD, LTCUSD, DASHUSD, USOIL_cash, UKOIL_cash, GER40, UK100, US30_cash, SPX500, NAS100, JP225
  - `orb_crypto_london`: BTCUSD, ETHUSD
  - `liq_asia_up_low_metal`: XAUUSD, XAGUSD, XPTUSD, XPDUSD
  - `kz_london_crypto_low`: BTCUSD, ETHUSD
  - `vss_fxcross_london_up_low`: EURJPY, GBPJPY, CHFJPY, AUDJPY, EURGBP
- **market_expansion_built**
  - `mx_aus200_cash_d1_volume_surge_reversal`: AUS200_cash
  - `mx_avausd_d1_donchian_20_breakout`: AVAUSD
  - `mx_btcusd_d1_donchian_20_breakout`: BTCUSD
  - `mx_cadjpy_d1_volume_surge_reversal`: CADJPY
  - `mx_ethusd_d1_donchian_20_breakout`: ETHUSD
  - `mx_eu50_cash_d1_volume_surge_reversal`: EU50_cash
  - `mx_fra40_cash_d1_volume_surge_reversal`: FRA40_cash
  - `mx_ger40_cash_d1_volume_surge_reversal`: GER40_cash
  - `mx_jp225_cash_d1_volume_surge_reversal`: JP225_cash
  - `mx_nzdjpy_d1_donchian_20_breakout`: NZDJPY
  - `mx_spn35_cash_d1_volume_surge_reversal`: SPN35_cash
  - `mx_us100_cash_d1_atr_mean_reversion`: US100_cash
  - `mx_us30_cash_d1_volume_surge_reversal`: US30_cash
  - `mx_us500_cash_d1_atr_mean_reversion`: US500_cash

Admission registry surfaces:

- **sleeve_registry**
  - `metals_core`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD
  - `crypto`: BTCUSD, DASHUSD
  - `energy_agri`: USOIL_cash, UKOIL_cash, CORN_c, COTTON_c
  - `metals_softband`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD
  - `metals_ob_micro`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD
  - `fx_jpy_ny`: GBPJPY, USDJPY
  - `idxrev`: SPX500, UK100, FRA40_cash, EU50_cash, US2000_cash, JP225, GER40, US30_cash
  - `fx_jpy`: GBPJPY, USDJPY
- **clean3**
  - `sub_xvol_pullback`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD, USOIL_cash, UKOIL_cash, NATGAS_cash, HEATOIL_c, CORN_c, COTTON_c, SPX500, UK100, FRA40_cash, EU50_cash, US2000_cash, JP225, GER40, US30_cash
  - `vp_euidx_pocgrav`: GER40, UK100
  - `sub_mid_dn_revert`: XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD, USOIL_cash, UKOIL_cash, NATGAS_cash, HEATOIL_c, CORN_c, COTTON_c, SPX500, UK100, GER40, US30_cash, BTCUSD, GBPJPY, USDJPY, EURJPY, AUDJPY, CHFJPY
- **clean4**
  - `session_leadlag_genuine`: US30_cash, GER40, USDJPY, AUDJPY, SPX500, NAS100

## 5. What assemble / intent builds per symbol

- Assembler: `assemble_gold_state_v0 — one function for any symbol`. Schema `gtos.judgment.gold_state.v0`. Default symbol `XAUUSD`.
- Sufficiency: M15+H4 required; D1 optional (visible in missing_fields).
- `intent_gold_state`: loads Challenge books via books_for_symbol; never April.
- `books_for_symbol`: never substitutes XAU for another pair.
- `sleeve_from_tape`: metals A8 formulas for every symbol (a8_source=challenge_m15_metals_a8).
- News: W7 window USD/XAU only (15m pre / 2m post); F5 window all HIGH (15m pre / 60m post); empty spine ≠ no HIGH; invent NEWS_PROTOCOL=False.
- `surface.us30_off` = True on every row.
- Library `score_sit`/`score_slate` default: load_gold_books() = April XAU historical.
- CLI: load_all_landed_challenge_books() or load_challenge_books().

- **XAUUSD**: Chair 2026-09-18 refresh: parent and multi/ XAUUSD_* are byte-identical; M15 last 2026-09-18T04:15Z. Admit sit+now. metals A8; sit occupied ticket 293332188
- **GBPUSD**: Challenge M15+H4 landed under multi/; sufficient sit+now; D1 optional; A8 still metals formulas
- **EURUSD/EURGBP/USDJPY**: same as GBPUSD; USDJPY is OPTIONAL in MULTI_SYMBOL but required for CA-USD; landed
- **GBPJPY**: Chair zip landed; not in MULTI_SYMBOL_*; same assembler; D1 optional; fx_jpy sleeve surface
- **US30/UK100**: US30 landed (house_hard_off mx_us30, occupancy/CA-IDX only); UK100 still missing; surface.us30_off stays True
- **BTCUSD/ETHUSD**: house_hard_off orb_crypto; do not score as a trade surface
- **XAGUSD**: occupancy metals cluster; no Challenge tape; not in MULTI_SYMBOL

## 6. Peer PRs (not imported on this branch)

- PR #13: CROSS_ASSET_FEATURES_V0 / CA-* labels on Challenge multi tape (USD proxy −EURUSD −GBPUSD +USDJPY).
- PR #15: peers.usdjpy on gold_state when primary is XAU; missing USDJPY does not fail sufficiency.
- `gold_state` on this branch is still XAU-centric (schema name, default XAUUSD, metals A8, `us30_off`).
- Selector V4 has no symbol universe in this inventory; do not import `selector_v4` (R2-bound).

## 7. Next pull list

- **0_lock** — Never wear April data/historical* or exports/multi_instrument. No time_utc; NY+7 would mis-clock Challenge-true rows; tests pin the refuse.
- **4_optional** — EURUSD D1 optional. d1_optional_missing, april_historical_exists_do_not_wear.
- **4_optional** — GBPUSD D1 optional. d1_optional_missing, april_historical_exists_do_not_wear.
- **4_optional** — EURGBP D1 optional. d1_optional_missing, april_historical_exists_do_not_wear.
- **2_missing_priority** — UK100 M15+H4 Challenge-true (time_utc=server-3h). challenge_m15_h4_missing, april_historical_exists_do_not_wear.
- **5_do_not_trade** — ETHUSD M15+H4 optional risk peer only — not a trade surface. optional_risk_peer_not_trade_surface, april_historical_exists_do_not_wear.
- **4_optional** — USDJPY D1 optional. d1_optional_missing, april_historical_exists_do_not_wear.
- **4_optional** — XAGUSD M15+H4 optional occupancy peer. occupancy_cluster_no_jev_priority, april_historical_exists_do_not_wear.
- **4_optional** — GBPJPY D1 optional. d1_optional_missing, april_historical_exists_do_not_wear.
- **5_do_not_trade** — Do not pull BTCUSD as a trade surface. house_hard_off orb_crypto; host filled kz_london_cry — label as host drift.

## 8. What this inventory does not do

- No place / remint / flatten.
- No invented NEWS_PROTOCOL.
- No APPLY size wires.
- No rewrite of the armed W7 set.
- No import of `selector_v4` or `v4_timewarp_simulated_live_research_loop`.


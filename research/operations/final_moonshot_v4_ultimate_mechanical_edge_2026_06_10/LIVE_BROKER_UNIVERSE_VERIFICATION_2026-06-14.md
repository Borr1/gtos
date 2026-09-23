# LIVE BROKER SYMBOL/SPEC VERIFICATION — both terminals, read-only (2026-06-14)

> Resident VPS operator. Method: **read-only** `MetaTrader5` attach to the two running, authorized
> portable terminals (no `order_send`, no trade calls). Ground truth = the **live market**; stale
> config / hardcoded maps / docstrings were NOT trusted. Raw evidence: `VERIFIED_BROKER_SYMBOL_SPECS.json`
> (+ `.tools/ftmo_universe.json`, `.tools/fn_universe.json`, `.tools/universe_reconciliation.json`).

## Accounts probed (live)
| Role | Login | Server | Company | Balance | Symbols | Clock→UTC |
|---|---|---|---|---|---|---|
| PRIMARY | 531325516 | FTMO-Server3 | FTMO Global Markets Ltd | $97,052.38 | 166 | +179 min (UTC+3) |
| FOLLOWER | 0 | redacted_account-Server 2 | redacted_account Ltd | $99,965.20 | 76 | +180 min (UTC+3) |

VPS OS clock = UTC (NTP-synced via w32time). Both broker server offsets are known, stable integers.

## FINAL CURATED LIVE UNIVERSE — 27 symbols (owner-directed 2026-06-14)
The live universe is the **11-sleeve deploy set = the union of the book sleeve registries**
(`ultimate_book_live_package.py` SLEEVE/CLEAN3/CLEAN4_REGISTRY), minus the dropped
HEATOIL_c/NATGAS_cash. Applied to `config/agent_config.yaml`
`moonshot_dynamic_execution_router_broker_native_eligible_symbols` (was the legacy 24):
- **+10 expansion** (book carriers absent from the legacy list): metals crosses XAUEUR/XAGEUR/XAUAUD/XAGAUD,
  DASHUSD, agri CORN_c/COTTON_c, indices EU50_cash/FRA40_cash/US2000_cash.
- **−7 non-JPY pure-FX majors** used by NO sleeve: AUDUSD, EURGBP, EURUSD, GBPUSD, NZDUSD, USDCAD, USDCHF.
- **JPY crosses AUDJPY/CHFJPY/EURJPY KEPT** — carriers of the clean3 `sub_mid_dn_revert` sleeve (not pure-FX).

Per-broker availability (live-verified, every contract field in `VERIFIED_BROKER_SYMBOL_SPECS.json`):
- **FTMO (primary): all 27 present.**
- **redacted_account (follower): 20/27.** FTMO-only (follower SKIPS, isolated): XAUEUR, XAGEUR, XAUAUD, XAGAUD,
  DASHUSD, CORN_c, COTTON_c (FN has no metals crosses, no DASH, no commodities).
- **Follower contract hazards (sizer must rescale):** ETHUSD ratio 10×; 8 indices (GER40/UK100/SPX500/
  NAS100/US30_cash/FRA40_cash/EU50_cash/US2000_cash) ratio 0.1×; JP225 digits 2→0 + tick 0.01→1.0;
  US2000 digits 2→1.
- **10 clean 1:1 follower mirrors:** XAUUSD, XAGUSD, BTCUSD, USOIL_cash, UKOIL_cash, USDJPY, GBPJPY,
  EURJPY, AUDJPY, CHFJPY.

Still TODO at Step-7 (production fold, with specs ready in the artifact): build FTMO + redacted_account
**profile instrument blocks** + the **dual-adapter symbol map** for the new symbols, and the
**contract-size-aware follower sizer**. The eligible-symbols list is updated/staged; the runtime is
halted/default-off, so this is staged-not-live.

## (Investigation history) Universe scope — 24 vs 46 (24 was the legacy execution set; 46 historical)
- The deploy-live **execution-eligible** universe is **24 broker-native symbols**
  (`config/agent_config.yaml` `moonshot_dynamic_execution_router_broker_native_eligible_symbols`,
  last edited 2026-05-27 — that edit *added* GER40/JP225, i.e. the list grew toward 24).
- `config/profiles/ftmo.yaml` defines exactly these 24 with **correct live native names**
  (US100.cash, US500.cash, GER40.cash, UK100.cash, US30.cash, JP225.cash, USOIL.cash, UKOIL.cash) —
  verified against the live terminal, not stale.
- **46** = the historical **research substrate** universe (`KB4_substrate.md`: "46 instruments … H4
  2014-2026") and the **proven-losing broad V4 selector** (`CLAUDE_VPS_BOOTSTRAP.md`: "the broad
  **24/46-symbol** V4 selector … −113.4R over 454 fills"). The go-live docs explicitly mark it stale:
  `GOLIVE_runbook_readiness.md` — *"remove stale broad 24/46-symbol surface."* The W7 deploy book
  (11 sleeves) trades a **subset** of the 24. Expanding live to 46 would re-introduce the broad
  surface that lost −113.4R — a **strategy decision for the owner**, not an operator change.

## Per-symbol live reconciliation (all 24 exist on BOTH brokers)
17/24 match cleanly (identical contract_size + digits → follower mirrors 1:1): all FX (AUDJPY,
AUDUSD, CHFJPY, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY), metals
(XAUUSD, XAGUSD), BTCUSD, and both oils (FTMO USOIL.cash/UKOIL.cash ↔ FN USOUSD/UKOUSD, contract
100/digits 3 on both).

**7 cross-broker mismatches the live data exposed (the follower hazards):**

| Canonical | FTMO native (csz/dig) | redacted_account native (csz/dig) | Hazard | Follower lot factor |
|---|---|---|---|---|
| ETHUSD | ETHUSD (10 / 2) | ETHUSD (1 / 2) | contract 10× | ×10 |
| GER40 | GER40.cash (1 / 2) | GER30 (10 / 2) | name + contract | ×0.1 |
| NAS100 | **US100.cash** (1 / 2) | NDX100 (10 / 2) | name + contract | ×0.1 |
| SPX500 | **US500.cash** (1 / 2) | SPX500 (10 / 2) | name + contract | ×0.1 |
| UK100 | UK100.cash (1 / 2) | UK100 (10 / 2) | contract | ×0.1 |
| US30_cash | US30.cash (1 / 2) | US30 (10 / 2) | name + contract | ×0.1 |
| JP225 | JP225.cash (10 / **2**) | JP225 (10 / **0**) | digits differ | 1.0 (digits) |

Identities confirmed by description (not name alone): FTMO US100.cash = "NASDAQ 100 Index";
US500.cash = "S&P 500"; US30.cash = "Dow Jones"; FN GER30 = "Germany 40 Cash index" (= DAX40).

## CRITICAL follower-sizing consequence
The dual adapter's default follower request builder copies the primary **volume verbatim**. That is
notional-correct ONLY for the 1:1 carriers. For the **6 contract-size-divergent symbols above**, a
raw lot copy mis-sizes the redacted_account leg by **10×** (indices over-size, ETH under-size). At **Step-7**
the production `follower_request_builder` MUST rescale follower volume by
`primary_contract_size / follower_contract_size`. A warning to this effect + the live numbers are now
in `dual_mt5_adapter.py` and `VERIFIED_BROKER_SYMBOL_SPECS.json`. This only ever affects the FOLLOWER
leg (isolated) — the FTMO primary is unaffected.

## Spreads
FX/metals quoted live (FX market opened Sun ~22:00 UTC). Several indices/crypto showed spread 0 at
measurement (off-hours) → `spread_bps` recorded where available; the per-broker round-trip **R-floor
must be re-measured during full market hours** before any follower oil/index leg sizes. redacted_account
spreads run wider than FTMO where both quoted (e.g. XAUUSD 3.1 vs 1.3 bps; EURUSD 1.0 vs 0.17 bps).

## Corrections applied this session (scaffold; default-off; tested)
- `dual_mt5_adapter.py` FTMO map: USOIL.cash/UKOIL.cash contract 1000→**100**, digits 2→**3**
  (matches live; the old values would have failed the documented startup spec-check / mis-sized).
- redacted_account map: oil `USOIL.c`/`UKOIL.c` (non-existent on FN) → **USOUSD/UKOUSD**; **GBPJPY added**
  (present on FN, contract 100000/3); carrier contract/digits confirmed live.
- Contract-size rescaling WARNING added at the default follower builder.
- Tests updated to the live reality (USOUSD name; full carrier coverage; missing-symbol path via a
  genuinely-absent canonical). Dual-adapter suite 27/27; full matrix 190/190; preflight exit 0.

## Outstanding (owner / Step-7)
1. Decide the live universe scope (11-sleeve book subset vs all 24 vs any broader set). Operator does
   NOT set strategy scope.
2. At Step-7 promotion, build the production symbol map + the contract-size-aware follower sizer FROM
   `VERIFIED_BROKER_SYMBOL_SPECS.json` (not from the illustrative scaffold).
3. Re-measure per-broker spread R-floors during full market hours (indices/oil were off-hours).

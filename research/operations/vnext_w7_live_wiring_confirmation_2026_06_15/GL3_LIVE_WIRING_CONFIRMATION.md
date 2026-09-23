# GL-3 — W7 Book Live Wiring Confirmation (FTMO terminal)

Date: 2026-06-15
Surface: FTMO-Server3, account 531325516 (PRIMARY), `C:\MT5\FTMO\terminal64.exe`
Mode: read-only, triple-gate OFF (shadow), **NO orders placed**.
Owner mandate: live-vs-replay/shadow wiring-confirmation is MANDATORY before any real order.

## What GL-3 had to prove

That the BUILT src W7 book engine, when pointed at the live FTMO terminal, actually:
1. fetches live closed bars for every sleeve's on-surface symbol,
2. clears warmup,
3. runs the validated sleeve generators on real current prices,
4. produces the book's intents + shadow sizing (would_units) — with gates OFF, never an order.

The per-sleeve route-parity tests (T1/T2) already prove src == route on fixtures; GL-3 proves the
LIVE WIRING on the terminal.

## Bug caught by the deep probe (would have silently disabled 7 of 13 sleeve symbols)

A naive shadow run returned `n_intents=0`, which is ambiguous (no signal vs. no feed). The deep probe
(`.tools/probe_book_wiring.py`) reported per-(sleeve, symbol) feed status and exposed the real cause:

| sleeve | canonical (registry on_surface) | FTMO broker name | naive fetch result |
|---|---|---|---|
| metals_core/softband | XAUUSD, XAGUSD | XAUUSD, XAGUSD | OK (identity) |
| crypto | BTCUSD, ETHUSD | BTCUSD, ETHUSD | OK (identity) |
| energy_agri | USOIL_cash, UKOIL_cash | **USOIL.cash, UKOIL.cash** | **NO FEED** |
| idxrev | SPX500, UK100, JP225, GER40, US30_cash | **US500.cash, UK100.cash, JP225.cash, GER40.cash, US30.cash** | **NO FEED** |

Root cause: `book_engine._generate_intents` fetched bars and `book_owner._tick` fetched the tick under
the **canonical** on_surface name, which does not exist on FTMO. Only metals/crypto fed because their
canonical name equals the broker name. The execution/placement side already resolved correctly
(`apply_instrument_overrides` -> `market.mt5_symbol`); the two book-side broker crossings did not.

This is exactly the stale-symbol hazard: the registry names looked right and the tests passed on
fixtures, but the live broker exposes different names. redacted_account maps the SAME canonical names
differently again (SPX500->SPX500, US30_cash->US30), which is why the registry must stay canonical and
the broker name must be resolved per-broker from the profile.

## Fix (committed 75285a1)

`src/components/ultimate_book/symbol_map.py` — `build_broker_symbol_resolver(config)` builds
canonical -> `instruments[<canon>].market.mt5_symbol` (identity fallback). Wired at both book-side
broker crossings: `book_engine` bar fetch and `book_owner` tick fetch. `intent.symbol` stays canonical
so placement still resolves via `apply_instrument_overrides`. Regression test
`tests/ultimate_book/test_symbol_map.py` (+3) asserts the FTMO mappings, identity fallback, and that
the engine requests the `.cash` broker names (never canonical). Full suite: 25 passed.

## Post-fix live proof (13/13)

`.venv-gtos/Scripts/python.exe .tools/probe_book_wiring.py "C:\MT5\FTMO\terminal64.exe"`

```
account login=0 server=FTMO-Server3 equity=97052.38 currency=USD trade_allowed=True
sleeve            canon       broker      tf  bars warmup  last_close  decision_day  outcome
metals_core       XAUUSD      XAUUSD      H4  259  True    4292.43     2026-06-15    no-signal (ran OK)
metals_core       XAGUSD      XAGUSD      H4  259  True    70.022      2026-06-15    no-signal (ran OK)
metals_softband   XAUUSD      XAUUSD      H4  259  True    4292.43     2026-06-15    no-signal (ran OK)
metals_softband   XAGUSD      XAGUSD      H4  259  True    70.022      2026-06-15    no-signal (ran OK)
crypto            BTCUSD      BTCUSD      H4  259  True    65590.88    2026-06-15    no-signal (ran OK)
crypto            ETHUSD      ETHUSD      H4  259  True    1719.76     2026-06-15    no-signal (ran OK)
energy_agri       USOIL_cash  USOIL.cash  H4  259  True    81.192      2026-06-15    no-signal (ran OK)
energy_agri       UKOIL_cash  UKOIL.cash  H4  259  True    84.785      2026-06-15    no-signal (ran OK)
idxrev            SPX500      US500.cash  H4  259  True    7503.33     2026-06-15    no-signal (ran OK)
idxrev            UK100       UK100.cash  H4  259  True    10523.9     2026-06-15    no-signal (ran OK)
idxrev            JP225       JP225.cash  H4  259  True    69415.5     2026-06-15    no-signal (ran OK)
idxrev            GER40       GER40.cash  H4  259  True    25046.94    2026-06-15    no-signal (ran OK)
idxrev            US30_cash   US30.cash   H4  259  True    51565.36    2026-06-15    no-signal (ran OK)
rows=13 | symbols_with_live_feed=13/13 | symbols_with_live_tick=13/13 | intents_fired_this_bar=0
WIRING VERDICT: LIVE FEED PROVEN
```

Real engine object proof (`.tools/run_book_shadow.py`, real `UltimateBookLiveEngine.evaluate()` with the
resolver injected): `ok: True | reason: shadow_book_disabled | runtime_effect_now: False | n_intents=0`.
`test_engine_fetches_under_broker_names` confirms the engine requests US500.cash/US30.cash/USOIL.cash.

`intents_fired_this_bar=0` is legitimate — these are selective sleeves and no entry triggered on the
latest closed H4 bar. Contract sizes from the profile match the live broker (JP225 csz=10, indices
csz=1, ETH csz=10, XAU csz=100) — no 10x hazard on the FTMO side for the book symbols.

## Scope confirmed by GL-3

GL-3 proves wiring for the 5 BUILT sleeves (metals_core, metals_softband, crypto, energy_agri, idxrev)
— the top-weight tier (~68% of book weight). The remaining 6 sleeves (sub_xvol_pullback,
sub_mid_dn_revert, vp_euidx_pocgrav, metals_ob_micro, fx_jpy, fx_jpy_ny) are not yet ported; their
build-spec is under investigation. The HARD STOP stands: no flip / no real order until the book is
demonstrably complete and correct and the owner re-confirms GO.

## Status

- GL-3 live wiring: PROVEN for built sleeves (13/13 feed + tick). PASS.
- Bug found + fixed + regression-tested + committed (75285a1).
- Tools: `.tools/probe_book_wiring.py`, `.tools/probe_symbol_names.py`, `.tools/run_book_shadow.py`.

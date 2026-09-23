# LIVE SPREAD-FLOOR CHECK (2026-06-15, read-only, both brokers)

Method: live `symbol_info_tick` round-trip spread (ask−bid) ÷ stop_distance, stop = sleeve `stop_atrs`
× ATR14(H1). H1/1×ATR is a CONSERVATIVE stop proxy (real sleeve stops on H4/cascade are larger →
true R-floors are LOWER than shown). Compared vs book `TICK_SPREAD_FLOOR_R` (XAU 0.0118, XAG 0.0408,
oil 0.027/0.026, BTC 0.0001, DASH 0.085, USDJPY 0.0841; JPY crosses + metals crosses transfer; wall 0.20R).

## FTMO (PRIMARY) — core 24/5 legs
| canon | live spr_bps | liveR (sleeve stop) | modeled | verdict |
|---|---|---|---|---|
| XAUUSD | 1.02 | 0.017 | 0.0118 | OK (<wall, ~1.5× modeled) |
| XAGUSD | 10.2 | 0.097 | 0.0408 | OK (<wall, ~2.4×) |
| XAUEUR/XAUAUD | 1.4–1.6 | 0.028–0.030 | 0.0118 | OK (<wall) |
| XAGEUR/XAGAUD | ~10 | 0.10 | 0.0408 | OK (<wall, ~2.5×) |
| BTCUSD | 0.15 | 0.0013 | 0.0001 | OK (clean) |
| ETHUSD | 3.6 | 0.025 | 0.0001(BTC-xfer) | OK (<wall) but book UNDER-modeled non-BTC crypto |
| DASHUSD | 5.2 | 0.017 | 0.085 | OK (book already flags DASH) |
| USOIL/UKOIL | 7.3–8.4 | 0.05–0.06 | 0.027/0.026 | OK (<wall, ~2×) |
| USDJPY | 0.69 | 0.159 | 0.0841 | OK but nearer wall (conservative stop; real lower) |
| GBPJPY/EURJPY/AUDJPY/CHFJPY | 0.7–1.6 | 0.10–0.13 | 0.0841(xfer) | OK (<wall) |
| **CORN_c** | 25.8 | **0.456** | transfer | **OVER WALL → SKIP** |
| **COTTON_c** | 62.5 | **1.358** | transfer | **OVER WALL → SKIP** |

## redacted_account (FOLLOWER)
XAUUSD 0.020R, XAGUSD 0.098R, JPY 0.07–0.14R — tradeable; **BTC spread 4.5 bps (30× FTMO's 0.15)**;
metals crosses / DASH / oil / agri **off-hours/closed at measurement**. FN spreads materially wider →
reinforces follower-after-parity + per-broker floors.

## Verdict for the flip
- **Core 24/5 legs (metals incl. crosses, BTC/ETH, oil, JPY): VERIFIED tradeable** — all below the 0.20R wall
  even on the conservative stop. Spreads run ~1.5–2.5× the book's modeled floors → the book's
  `TICK_SPREAD_FLOOR_R` is OPTIMISTIC vs live (matches AUDIT_VERDICT magnitude haircut). The live sizer
  should charge the LIVE floors, not the modeled ones (a fold/sizing follow-up).
- **SKIP agri (CORN_c, COTTON_c): over the untradeable wall at live spreads.** Not 24/5 anyway.
- **Indices: defer to market-hours re-measure** (per owner), skip until verified — do not block the core flip.
- Action: update `TICK_SPREAD_FLOOR_R` to live-measured values for the core legs and add CORN_c/COTTON_c
  as gated (>=wall) before the live sizer relies on them. Re-measure indices/agri in their session.

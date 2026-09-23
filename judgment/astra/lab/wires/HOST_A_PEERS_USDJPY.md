# HOST A — peers USDJPY (Chair land)

Priority A from Ultragoal Scout. **Never place. Never remint. Never flatten.**
Do not invent DXY, yields, or order blocks.

USDJPY is now **peer-of-XAU / PRIORITY** for Challenge books. The loader
already accepts multi-symbol CSVs. Live `intent_gold_state` only loaded
`intent.symbol` books, so an XAU row never saw yen tape. `gold_state`
now always emits `peers.usdjpy`. Missing stays **visible null**.

## What landed on GitHub

- `src/judgment/bars.py` — `USDJPY` in `MULTI_SYMBOL_PRIORITY`;
  `XAU_PEER_SYMBOLS = ("USDJPY",)`; `MULTI_SYMBOL_OPTIONAL` empty.
- `src/judgment/peers.py` + `gold_state.peers` —
  `present`, `m15_atr14`, `h4_trend`, `xau_usdjpy_comove_20`,
  `atr_ratio`, `source`. No DXY / yields / OB keys.
- `intent_gold_state` attaches the named peer set from Challenge CSVs
  via `books_for_symbol` **only when primary is XAU**.
- Tests: `tests/judgment/test_peers_usdjpy.py` + fixture CSVs under
  `tests/judgment/fixtures/peers/` (lab shape, not Challenge-true).

`state_sufficient_for_live` does **not** wait on USDJPY. An XAU row
with M15+H4+geometry stays sufficient; `completeness.peers_usdjpy`
and `missing_fields: peers.usdjpy` name the hole.

## Chair pull (Challenge-true, then land judgment)

USDJPY M15+H4 are **not** in the 2026-09-17 multi drop. April
`data/historical/USDJPY_*.csv` is **not** Challenge tape — do not copy it.

1. On the Challenge host (login `0` / `FTMO-Server` /
   `operator` only), READ-ONLY `copy_rates_range` for `USDJPY`
   M15 and H4. Same clock contract as XAU: export `time_utc` already
   −3h; keep `time_server_labeled`. Cover at least the open as-of of
   ticket `293332188` (`2026-09-17T07:30:55Z`) plus 20 M15 and 30 H4
   closed bars before that stamp.
2. Land the files **beside** the existing multi drop:

```
judgment/astra/lab/challenge_shadow_20260917/multi/USDJPY_M15.csv
judgment/astra/lab/challenge_shadow_20260917/multi/USDJPY_H4.csv
```

   Also copy into the box multi dir if that is the live pull source
   (`challenge_shadow_bars/multi/`). D1 is optional for non-XAU.
3. `python3 scripts/jev_copy_challenge_multi_bars.py` if the CSVs
   landed on the box/VPS path first. `n_copied` must include the two
   USDJPY names. `invented: false`. `april_historical_used: false`.
4. Copy **`src/judgment/`** onto Challenge f5-live. Do **not**
   wholesale-copy GitHub `book_owner.py` onto the dirty host.
5. Restart **only** `GTOS_F5_FTMO`. Env unchanged:
   `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1` `GTOS_JEV_A1_LOG=1`.
   TypeSafe fp `00000000`.

## Judgment after the pull

On the next XAU `intent_gold_state` / Challenge score:

| Before pull | After Challenge-true USDJPY M15+H4 |
|---|---|
| `peers.usdjpy.present = false` | `true` |
| metrics `null`, `source = unassembled` | `m15_atr14` / `h4_trend` from `tf_snap`; `xau_usdjpy_comove_20` = Pearson of 20 aligned M15 simple returns; `atr_ratio` = XAU M15 ATR14 / USDJPY M15 ATR14; `source = challenge_csv` |
| `completeness.peers_usdjpy = false` | `true` |

If a snap is stale (M15 lag > 12h, H4 lag > 36h) or alignment < 21
closes, that metric stays `null`. That is correct. Do not fill it.

GBP / other primaries: `source = not_xau_primary`, `present = false`.
Peers are an XAU block.

## Do not

- Invent DXY, US10Y, real yields, or order-block fields.
- Wear April historical / Sierra 6J as Challenge USDJPY.
- Pull BTCUSD as a trade surface.
- Place, remint, flatten, or write inbox from this land.
- Let missing peers flip `state_sufficient` or change size.
- Touch W7 armed books.

Physical size stays flow × cost on Challenge only. Peers are named
state for Chair / Jev — not a new refuse fence.

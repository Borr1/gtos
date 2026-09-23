# T3 — redacted_account universe: NOT a config defect. No entries added. Fail-closed.

**Verdict: the 13 skipped symbol/sleeve pairs are correct behaviour. redacted_account does
not list any of the 7 underlying instruments. No `config/profiles/redacted_account.yaml`
edit was made, therefore no digest change, no token re-mint, and no book restart.**

The brief's step (b) is the step that fired:

> Verify each symbol actually exists and is tradeable on the FN terminal; any that
> does not exist gets NO entry (record it instead).

All seven fall into "record it instead". This is that record.

## 1. What was checked

`profile_missing_instrument_config` skip rows, redacted_account, cycle
`2026-08-10T17:00:53Z` (`shadow_logs/ultimate_book_launcher.jsonl`) — 13 rows,
7 distinct symbols:

| symbol | sleeves skipped | cluster |
|---|---|---|
| DASHUSD | crypto | crypto |
| XAUEUR | sub_xvol_pullback, sub_mid_dn_revert | substrate |
| XAGEUR | sub_xvol_pullback, sub_mid_dn_revert | substrate |
| XAUAUD | sub_xvol_pullback, sub_mid_dn_revert | substrate |
| XAGAUD | sub_xvol_pullback, sub_mid_dn_revert | substrate |
| CORN_c | sub_xvol_pullback, sub_mid_dn_revert | substrate |
| COTTON_c | sub_xvol_pullback, sub_mid_dn_revert | substrate |

1 + (6 × 2) = 13. Matches exactly.

## 2. Existence check — proven by exhaustion, not by a failed guess

A candidate-spelling probe can only ever prove presence. To prove *absence* the
complete broker symbol list was dumped from both terminals
(`probe_full_symbol_lists.py` → `FULL_SYMBOL_LISTS.json`), read-only.

**redacted_account exposes 76 symbols in total. Here they all are:**

```
ADAUSD AUDCAD AUDCHF AUDJPY AUDNZD AUDSGD AUDUSD AUS200 BTCUSD CADCHF CADJPY
CHFJPY DOGUSD ETHUSD EURAUD EURCAD EURCHF EURGBP EURHKD EURHUF EURJPY EURNOK
EURNZD EURSGD EURUSD EUSTX50 FRA40 GBPAUD GBPCAD GBPCHF GBPJPY GBPNZD GBPSGD
GBPUSD GER30 HK50 JP225 LNKUSD LTCUSD MXNJPY NDX100 NOKJPY NTH25 NZDCAD
NZDCHF NZDJPY NZDSGD NZDUSD SGDJPY SPX500 SWI20 UK100 UKOUSD US2000 US30
USDCAD USDCHF USDCNH USDDKK USDHKD USDHUF USDJPY USDMXN USDNOK USDSEK USDSGD
USDZAR USOUSD VIX XAGUSD XAUUSD XLMUSD XMRUSD XPTUSD XRPUSD ZARJPY
```

Against that list:

| symbol | on redacted_account? | why not | on FTMO? |
|---|---|---|---|
| DASHUSD | **NO** | FN crypto is ADA/BTC/DOG/ETH/LNK/LTC/XLM/XMR/XRP. No DASH in any spelling. | yes (`DASHUSD`) |
| XAUEUR | **NO** | FN carries no metal cross at all — only XAUUSD, XAGUSD, XPTUSD. | yes (`XAUEUR`) |
| XAGEUR | **NO** | same | yes (`XAGEUR`) |
| XAUAUD | **NO** | same | yes (`XAUAUD`) |
| XAGAUD | **NO** | same | yes (`XAGAUD`) |
| CORN_c | **NO** | FN lists no agricultural/softs instrument of any kind. | yes (`CORN.c`) |
| COTTON_c | **NO** | same | yes (`COTTON.c`) |

FTMO exposes 166 symbols and carries all seven. The asymmetry is a genuine product
difference between the two firms, not a GTOS configuration gap.

Cross-check that the probe method is sound rather than uniformly blind: on the same
redacted_account connection the probe *did* resolve `EUSTX50`, `FRA40` and `US2000` —
symbols whose FN spelling differs from both the canonical name and the FTMO
spelling. The method finds differently-spelled symbols when they exist. Here they
do not exist.

## 3. Why adding entries anyway would have been actively unsafe

`supports()` — the predicate that emits the skip — is a **pure profile lookup that
never consults the broker** (`src/components/ultimate_book/symbol_map.py:57-60`):

```python
def supports(canonical: str) -> bool:
    if not has_instrument_contracts:
        return True
    return bool(_instrument_key(canonical))
```

The skip is raised at `src/components/ultimate_book/book_engine.py:320-335`, and the
very next line resolves the canonical name to a broker name used for **every**
subsequent fetch and for placement (`book_engine.py:337`).

So writing the seven entries into `redacted_account.yaml` would have flipped `supports()`
to `True` for instruments redacted_account does not list. The skip would have vanished
from the cycle log — the brief's own success criterion — while the book advanced to
requesting bars, and ultimately orders, on symbols the broker cannot price. The
visible symptom would have been repaired by removing the guard that was producing it.

The brief's two guardrails ("never copy FTMO numbers blind"; "any that does not
exist gets NO entry") are what prevented that, and both fired.

## 4. Consequences for the FTMO-vs-redacted_account comparison

The 13 skips are permanent under the current sleeve definitions. redacted_account will
never trade the metal crosses, the softs, or DASHUSD, because its broker does not
offer them. Any FTMO-vs-FN attribution must treat FN as a structurally narrower
book rather than a like-for-like follower — the two accounts are not running the
same universe and cannot be made to.

Closing the gap is a **broker** question (does redacted_account offer these instruments on
another server/account type?), not a config question. It is not answerable from this
host.

## 5. What was NOT done, and why

| brief step | status |
|---|---|
| (a) build FN instrument entries from FN-broker-true values | **not applicable** — no FN broker to read values from; `symbol_info` returns `None` for all 7 |
| (b) verify existence; absent symbols get no entry | **executed** — all 7 absent, all 7 recorded here |
| (c) edit `redacted_account.yaml`, re-mint FN token | **not done** — nothing to edit, so the token-bound digest never moved |
| (d) restart FN book, post-verify skips gone | **not done** — no config change to apply; a restart with no delta is pure live risk |
| (e) commit config + receipts | receipts committed; **no config change to commit** |

`config/profiles/redacted_account.yaml` is byte-unchanged. The redacted_account activation token
is untouched and still valid to 2026-09-09T13:02:33Z. The redacted_account worker was never
stopped — pids 1172/3956, creation time 2026-08-06T08:39:22Z, unchanged. FTMO was not
touched in any way.

## 6. Recommendation (not executed — needs owner approval)

The reason string is the actual defect here. `profile_missing_instrument_config` is
accurate about the *mechanism* and silent about the *cause*, so a permanent,
correct broker-universe boundary is logged in language that reads like a
misconfiguration. That mislabelling is what put this task on the queue.

A one-line improvement would split the two cases at the skip site — profile has no
entry **and** the broker does list the symbol (a real config gap, actionable) versus
profile has no entry **and** the broker does not list it either (correct, expected,
permanent). That is a live-behaviour code change on an armed account and is **not**
in this task's approved scope, so it is recommended, not applied.

## 7. Evidence files

| file | what |
|---|---|
| `FULL_SYMBOL_LISTS.json` | complete symbol list, both terminals — the absence proof |
| `PROBE_PRESTATE_SYMBOLS.json` | per-symbol resolution + full `symbol_info` where found |
| `probe_full_symbol_lists.py` | the read-only dump tool |
| `probe_prestate_and_symbols.py` | the read-only resolution/prestate tool |
| `T3_SKIP_ROWS_BEFORE.json` | the 13 skip rows as logged, cycle 17:00:53Z |

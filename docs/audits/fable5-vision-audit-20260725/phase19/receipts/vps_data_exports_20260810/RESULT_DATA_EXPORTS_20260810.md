# Session — VPS data exports + redacted_account universe check, 2026-08-10

Executed natively on the live host. Both accounts armed and **flat throughout**.
Owner approval for the task set on record.

## Headline

T1 and T2 delivered: 5 deep-H4 symbol exports and the full raw order/deal history
from both terminals, committed to the branch — and the gitignore rule that swallowed
the previous export is fixed, which is why the Mac was blocked in the first place.

**T3 did not execute, and should not have.** All 7 symbols redacted_account "skips" are
absent from the redacted_account broker entirely. There was no config gap to close. No
config byte changed, no token re-mint, no restart. Full reasoning in
`T3_redacted_account_UNIVERSE_FINDING.md`.

Nothing on the live surface moved: no `--tags`, no gates, no FTMO anything, no
broker mutation, no `git checkout/pull/clean/stash`. Every MT5 call this session was
read-only.

## T0 — prestate

| check | result |
|---|---|
| host HEAD at start | `4d28676f8` (CM rollback) |
| FTMO worker | pids 6208/5708, created 2026-08-10T13:25:56Z (CM-rollback restart) |
| redacted_account worker | pids 1172/3956, created 2026-08-06T08:39:22Z |
| FTMO argv `--frontier-exits` | **absent** — CM stays disarmed |
| `--tags`, both books | `crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert` |
| authority gates L1160-1163 | `enabled` / `apply_to_execution` / `live_activation_allowed` / `live_broker_authority` all **true** |
| FTMO token | ns `operator_profile`, digest `ffe16657feaf`, expires **2026-09-09T13:02:25Z** |
| redacted_account token | ns `redacted_account_live_bee34003`, digest `e184a81d3b1b`, expires **2026-09-09T13:02:33Z** |
| MT5 FTMO | connected, trade_allowed, eq **$108,342.47**, 0 pos / 0 pending |
| MT5 redacted_account | connected, trade_allowed, eq **$96,229.28**, 0 pos / 0 pending |
| last H4 cycle 17:00Z | both books `halted=False killed=False runtime_effect_now=True place=True`, `reason=no_candidates_this_bar` |

Both books polling, gates true, tokens valid to 2026-09-09, no frontier flag on FTMO
— prestate matches the brief exactly.

## T1 — deep-H4 source exports

All five symbols resolved on **FTMO**; none needed redacted_account (FN carries no
CORN/COTTON at all, and its index names differ — see T3). Broker spellings resolved
from the terminal, not assumed:

| canonical | FTMO symbol | rows | first bar | last bar | sha256 (12) |
|---|---|---|---|---|---|
| CORN_c | `CORN.c` | 4,992 | 2023-03-30 08:00 | 2026-08-10 16:00 | `ae7332117d2d` |
| COTTON_c | `COTTON.c` | 1,747 | 2025-03-17 12:00 | 2026-08-10 16:00 | `c26082224765` |
| EU50_cash | `EU50.cash` | 7,662 | 2021-01-20 16:00 | 2026-08-10 16:00 | `d0f3bb423f7b` |
| FRA40_cash | `FRA40.cash` | 7,647 | 2021-01-20 12:00 | 2026-08-10 16:00 | `7dae36cf08c7` |
| US2000_cash | `US2000.cash` | 13,166 | 2018-01-23 00:00 | 2026-08-10 16:00 | `6058b8870c7f` |

`data/mt5_research_exports/bridge_ftmo_deep_h4_w7recost_20260810/`, 0 export errors,
13/13 chunks returned rows for every symbol. Requested window was 2014-01-01 →
2026-08-10T17:00Z, so each `first bar` above is the true start of the broker's
history, not a request boundary — this is maximum available H4 depth.

Schema and naming copied from the existing convention rather than reinvented: the
driver imports `export_research_ohlcv`, `enrich_export_result_for_manifest` and
`account_identity_payload` from `scripts/export_mt5_research_ohlcv.py` — the same
functions that produced `bridge_ftmo_deep_h4_backfill_2014_2026`. Header is
`time,open,high,low,close,volume`; files are `<file_symbol>_H4.csv` with `.`→`_`.

**Timebase carried forward verbatim:** the `time` column is the MT5 bar epoch
rendered as if UTC, but MT5 bar epochs are broker wall clock. This matches the prior
deep-H4 files exactly. Convert via `broker_clock`; do not assume UTC.

## T2 — slippage-capture source export

`data/mt5_research_exports/slippage_capture_20260810/`, both terminals, every field
MT5 provides: **18 deal columns** (`ticket, order, time, time_msc, type, entry,
magic, position_id, reason, volume, price, commission, swap, profit, fee, symbol,
comment, external_id`) and **24 order columns** (incl. `time_setup_msc`,
`time_done_msc`, `price_open`, `price_current`, `price_stoplimit`, `sl`, `tp`,
`volume_initial`, `volume_current`, `external_id`).

Totals over the widest window the terminals serve (2015-01-01 → 2026-08-11):

| broker | deals | orders | history spans |
|---|---|---|---|
| FTMO | 275 | 273 | 2026-06-01 13:23Z → 2026-08-10 08:47Z |
| redacted_account | 362 | 366 | 2026-04-26 23:06Z → 2026-07-02 19:03Z |

Target-symbol row counts — **read this before modelling**:

| canonical | FTMO sym | FTMO deals | FN sym | FN deals |
|---|---|---|---|---|
| AUDJPY | AUDJPY | 2 | AUDJPY | 2 |
| CHFJPY | CHFJPY | **0** | CHFJPY | 5 |
| EURJPY | EURJPY | **0** | EURJPY | 5 |
| UKOIL_cash | UKOIL.cash | 2 | UKOUSD | 7 |
| USOIL_cash | USOIL.cash | **0** | USOUSD | 7 |
| XAGUSD | XAGUSD | **0** | XAGUSD | 11 |

**The sample is thin and the report must say so.** FTMO contributes 4 deals across
all six symbols — two entry/exit pairs, so effectively **two** reconcilable
round-trips. redacted_account contributes 37 deals. A price-domain slippage estimate for
the CS breaker will be carried almost entirely by redacted_account, and FN's history stops
at 2026-07-02 (consistent with the July shadow-mode silence).

The rows are also not homogeneous, and were deliberately left unfiltered:

- magic `20260401` — genuine agent fills (`GoldAgent_OBRete`, `W7:energy_agri`,
  `TP1/TP2_vnext_partia`, `close_vnext_time`, SL/TP broker closes)
- magic `99887766` — one FN XAGUSD smoke-test pair (`FN_SMOKE` /
  `smoke_force_clos`). **Not a strategy fill; exclude before modelling.**
- magic `0` — one FN XAGUSD manual pair.

Per the brief's "raw truth only": nothing was filtered, rounded, derived, renamed or
reordered. `*_deals_ALL.csv` / `*_orders_ALL.csv` are the complete unfiltered sets;
the per-symbol files are strict row subsets selected on the `symbol` column alone,
and exist only because the brief asked for those six symbols. The `magic` column is
present so the research side can make the smoke/manual call itself.

## T3 — redacted_account universe: no change made

Summary only; the full argument, evidence and code citations are in
`T3_redacted_account_UNIVERSE_FINDING.md`.

redacted_account exposes **76 symbols total**. None of `DASHUSD, XAUEUR, XAGEUR, XAUAUD,
XAGAUD, CORN_c, COTTON_c` is among them, in any spelling — proven by dumping the
complete symbol list from the terminal, not by a failed name guess. FN carries no
metal cross and no softs whatsoever; its crypto set has no DASH. FTMO exposes 166
symbols and has all seven.

Per the brief's own step (b), every symbol that does not exist gets no entry.
All seven qualify, so:

- `config/profiles/redacted_account.yaml` — **byte-unchanged** (`git diff -- config/` empty)
- FN token-bound digest `e184a81d3b1b` — **unmoved**, no re-mint needed
- FN book — **never stopped**; pids 1172/3956, creation time 2026-08-06T08:39:22Z
- FTMO — untouched
- skip rows before: **13**. After: **13**, and correctly so.

Adding the entries would have been actively unsafe rather than merely useless.
`supports()` is a pure profile lookup that never consults the broker
(`src/components/ultimate_book/symbol_map.py:57-60`), and the skip site at
`book_engine.py:320-335` is immediately followed by the canonical→broker resolution
used for every fetch and for placement. Writing the entries would have made the skip
rows disappear — the brief's stated success criterion — by removing the guard, while
pointing the book at instruments the broker cannot price.

## Repo change: the gitignore rule that caused all of this

`data/mt5_research_exports/` was gitignored (`.gitignore:125`). That is why the
2026-06-14 `bridge_ftmo_deep_h4_backfill_2014_2026` export — which *did* include
CORN_c, COTTON_c and EU50_cash — never reached the research side: it was exported,
recorded in `KB2_deep_h4_export.log`, and then silently not committed. `git ls-files`
returns nothing for that path.

Fixed narrowly:

```diff
-data/mt5_research_exports/
+data/mt5_research_exports/*
+!data/mt5_research_exports/bridge_ftmo_deep_h4_w7recost_20260810/
+!data/mt5_research_exports/slippage_capture_20260810/
```

The rule had to change from `dir/` to `dir/*` because git will not descend into an
excluded directory, which makes a negation inside it dead — the first attempt at the
negation was silently ineffective and `git check-ignore` caught it. Routine exports
stay ignored; verified that `bridge_ftmo_carrycond_h4_m1_20260730` and
`market_expansion_followup_replay_20260618` remain ignored.

## Unexpected findings

1. **T3's premise was wrong, and the correct fix was to make no change.** The task
   was queued off a receipt describing the skips as a config gap. They are a broker
   product boundary. redacted_account cannot be brought to universe parity with FTMO by
   configuration.
2. **`profile_missing_instrument_config` is a misleading label** and is what
   generated this task. It is accurate about the mechanism and silent about the
   cause, so a permanent correct boundary reads as a misconfiguration. Splitting it
   into "profile gap, broker has it" vs "broker doesn't list it" is recommended but
   **not applied** — that is live-behaviour code on an armed account and outside this
   task's approved scope.
3. **The prior deep-H4 export was never lost to a bad export — it was lost to
   `.gitignore`.** Two of the five "missing" symbols had been captured on 2026-06-14
   and could not travel.
4. **FRA40_cash and US2000_cash were genuinely never exported** — they are absent
   from KB2's 12-symbol list. So the Mac's blocker was half stale-plumbing, half real
   gap.
5. **FTMO's price-domain sample for the CS breaker is effectively two round-trips.**
   Not a defect, just the true size of the evidence; flagged so the breaker is not
   fitted to it.
6. **redacted_account deal history ends 2026-07-02**, matching the known July shadow-mode
   silence. Anything expecting FN fills in July/August will find none.

## Push status

`origin` remote head remains far behind the host and sessions LN/LO/LQ/LR all
committed host-only. Push status and the detached tar path are recorded in
`PUSH_AND_TAR.txt` beside this file.

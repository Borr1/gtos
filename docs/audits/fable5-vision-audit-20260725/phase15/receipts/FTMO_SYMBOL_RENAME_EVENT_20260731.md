# The FTMO symbol-rename event — found live, 2026-07-31 ~07:20 UTC

> **CORRECTED 2026-07-31 by Session CF (B2350–B2399). There was no rename, and no member was
> ever mute.** The probe below asked the terminals for GTOS **canonical** names (`SPX500`,
> `UK100`, `GER40`, `JP225`, `NAS100`) — the broker-agnostic registry vocabulary. Those have
> never been FTMO broker names. The live FTMO profile has always mapped them across
> (`SPX500→US500.cash`, `UK100→UK100.cash`, `GER40→GER40.cash`, `JP225→JP225.cash`,
> `NAS100→US100.cash`), and **every one of those targets was already in FTMO's tree in the
> read-only 2026-07-25 export — six days before the "rename" — while every bare name was
> already absent.** The same export is its own control: redacted_account, probed at the same instant
> by the same code, does carry the bare names and carries no `.cash` symbol at all, exactly as
> its own profile encodes.
>
> Swept across the full declared registry (34 sleeves, 137 slots, 48 canonical symbols) through
> each account's real profile against each broker's real tree: **0 resolved-but-absent on both
> accounts.** `sub_xvol_pullback` and `sub_mid_dn_revert` were generating normally throughout;
> the armed book was never degraded.
>
> **What survives, and is why CF was worth commissioning:** had a rename been real, *nothing
> would have said so*. `bar_provider.py:120-125` swallows any fetch failure into `([], [])` and
> `book_engine.py:563` skips empty bars with no log, no counter and no skip record. That
> silence is now covered by panel 6 of `scripts/gtos_command_center.py`, which diffs **resolved**
> broker names — never canonical ones — against the broker's own `symbols_get()` tree.
>
> Read `phase15/SESSION_CF_SYMBOL_RENAME_RESULT.md` §0 and
> `phase15/receipts/CF_SYMBOL_RESOLUTION_V1.json` before citing anything below. The "What
> changed" and "Armed-book impact" sections are **retained as the history of the false alarm**,
> not as facts. §"The vp M1 backfill" is unaffected by this correction and stands.

**Found by the orchestrator executing OD-HISTORICAL-FIRST's first fetch** (the vp M1
backfill). Every probe below was read-only (`symbol_info` / `symbols_get` /
`copy_rates_from_pos`), executed over host-admin against the running terminals, artifacts cleaned.
Books never touched; both healthy throughout (supervisor heartbeat fresh; monitor equity
reads live; **zero open positions on both accounts during the event window**).

## What changed

**FTMO-Server3 renamed its index symbols to `.cash` variants.** Measured on the live tree:

| was (served 2026-07-30) | is (2026-07-31) | series identity |
|---|---|---|
| `GER40` | `GER40.cash` | same series — H4 depth to 2018-03-26 |
| `UK100` | `UK100.cash` | same series — H4 depth to 2017-12-28 |
| `SPX500` | `US500.cash` | H4 to 2021-01-21 |
| `JP225` | `JP225.cash` | H4 to 2017-12-28 |
| (`NAS100`) | `US100.cash` | H4 to 2021-01-21 |

Bare `SPX500`, `UK100`, `JP225`, `GER40`, `NAS100` return `symbol_info = None` — gone from
the tree. `BTCUSD`, `DASHUSD`, `ETHUSD`, all metals crosses, `CORN.c`, `COTTON.c`,
`USOIL.cash`, `UKOIL.cash`, `US30.cash`, `FRA40.cash`, `EU50.cash`, `US2000.cash` and the FX
pairs are unchanged. **redacted_account is untouched** (bare `SPX500/UK100/JP225/FRA40/US2000/US30`
still present; `GER30` naming wall as CA documented).

## Armed-book impact (FTMO)

`crypto`, `energy_agri`, `mx_btcusd`: **unaffected** (their symbols verified present, BTCUSD
tick read live mid-event). Affected: **`sub_xvol_pullback` — 4 of 18 members mute**
(`SPX500`, `UK100`, `GER40`, `JP225`); **`sub_mid_dn_revert` — 3 of 20 mute** (`SPX500`,
`UK100`, `GER40`). Mute means the bar fetch for those members fails per tick and they
silently generate nothing — under-generation, never wrong trades, and no position was open
to strand. FN book: unaffected.

## The vp M1 backfill — answered, negatively, with measurement

The ask (CA handoff 1: GER40/UK100 M1 back to ~2025-12-29) is **unfetchable from our
brokers**: M1 `copy_rates_from_pos` caps at ~90,000 bars (terminal max-bars 100k; ≥110k =
`Invalid params`) reaching only ~2026-04-27, and `copy_rates_range` for older months returns
0–1 rows on both terminals under every name — the servers do not hold deeper M1.
Alternatives, priced per OD-HISTORICAL-FIRST: (a) **the window slides forward** — vp gains
roughly one evaluable fold per month of new data and becomes decidable ~Sep–Oct 2026 from
broker data alone; (b) **third-party M1** (declared provenance, e.g. Dukascopy-class) —
legitimate under the research rules IF the sidecar declares the non-broker basis and costs
are priced from our own spread/era models; a session-sized ingest. Option (b) is the
"data is data" route and is filed for the owner's next wave, not silently dropped.

## Consequences filed

1. **Session CF commissioned** (`SESSION_CF_SYMBOL_RENAME.md`, B2350–B2399): the resolution
   repair + the watchdog so the next rename alarms instead of muting.
2. `BROKER_SYMBOL_SPEC_COMPARISON.json` (2026-07-26 vendor) is stale as of this event.
3. The repair ceremony rides the token re-mint already due before 2026-08-05 if the right
   fix touches a token-bound profile; CF determines the layer.

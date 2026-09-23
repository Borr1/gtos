# DUAL-MT5 LIVE ARCHITECTURE (VPS)

The VPS has **no research bridge**. It runs **two MT5 terminals**: one connected to **FTMO**, one to
**redacted_account**. (The siliconmetatrader5 bridge @ localhost:8001 is DEV-ONLY, for historical data export
on the research Mac — it is NOT the live connection. The go-live live-connection adapter must talk to the
two local MT5 instances, not the bridge.)

## Source of truth: FTMO PRIMARY, redacted_account FOLLOWS (flip from current)
Current state: redacted_account primary, FTMO follows. **Flip it.** Rationale (not preference — evidence):
the entire deploy book was BUILT AND VALIDATED ON FTMO DATA — the bridge is FTMO, the per-asset cost
map, the tick spreads, and the 2014-2026 history are all FTMO. So FTMO is the system's NATIVE reference
distribution; running the decision engine on the FTMO instance means live decisions are made on the exact
data the book was validated against. redacted_account becomes a FOLLOWER.

## Flow
1. **Market data**: read OHLC/tick from the **FTMO** MT5 terminal (the validated distribution).
2. **Decision engine**: the deploy book (ultimate_book_live_package, default-off until go) generates
   candidates → admit_and_size (governor + 1.25%→1.5% sizing + Kelly-lite) → orders on the **FTMO** account.
3. **Follower (redacted_account)**: mirror each FTMO decision, TRANSLATED to redacted_account's own
   symbol names / contract specs / spread / leverage / min-stop, with an independent per-account governor
   and its own DD tracking against redacted_account's limits. The follower does NOT independently re-decide;
   it replicates the primary's intent, spec-adjusted.
4. **Per-account risk**: each account sizes independently (1.25%→1.5%/unit), tracks its own daily/max DD,
   and has its own fail-closed governor + halt file. One account breaching never forces the other.

## Parity & divergence handling (the operator watches this)
- Maintain a **primary-vs-follower parity ledger**: for every FTMO decision, did redacted_account fill the
  translated order, at what slip, on the matching symbol? Divergence (missing symbol, large slip,
  rejected order, spec mismatch) → alert + de-risk/skip the follower leg, never the primary.
- Maintain a **live-vs-replay parity ledger** on the primary: do live fills/EV match what the replay
  book predicted? Drift → de-risk + flag for repair.

## Known cross-broker hazards (encode + monitor)
- **Symbol-name & spec differences** (e.g. `.cash`/`.c`/`pro` suffixes, contract size, digits) — needs a
  per-broker symbol/spec map; missing-symbol on the follower = skip that leg, log it.
- **Spread differences** — redacted_account spread may exceed FTMO; the per-symbol tick spread floor
  (KB7_execution_truth) must be re-measured per broker; illiquid legs already dropped (HEATOIL/NATGAS).
- **Server time / timezone** — the two terminals may run different server times; ALL bar timing,
  session gates, and the persistence/confluence features are timezone-sensitive. Normalize to a single
  canonical clock (UTC) and verify both terminals' offsets at startup (a chronological-order bug here
  silently corrupts every gate — top operator watch item).
- **Leverage / margin** differences — sizing must respect each account's margin.

## Operator responsibilities on this architecture (see VPS_OPERATOR_CHARTER.md)
Verify the FTMO-primary wiring at startup; confirm both terminals' clocks/offsets; monitor both parity
ledgers; repair symbol-map/spec/timezone/null issues; never let the follower's problems touch the primary.

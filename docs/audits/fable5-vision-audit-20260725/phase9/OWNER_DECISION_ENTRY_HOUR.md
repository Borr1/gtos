# Owner decision — the FX D1 entry convention is ONE hour off the rollover

**RATIFIED 2026-07-30 by Borhen** ("yes proceed with everything as proposed", covering the
orchestrator's recommendation from the wave-9 review).

## The decision

For the FX D1 cohort (the sleeves whose fills land at broker hour 00 — 100 % of the cohort,
AH B1006), the entry convention is **the first bar after the rollover hour: broker hour 01**,
not AH's original "first H4 close" (hour 04).

## Why one hour and not four

AM's hour-resolved spread premium (`SESSION_AM_CLOCK_AND_ENTRY_FRONTIER_RESULT.md`, the
entry-frontier section) showed the rollover premium is a **one-hour
spike, not a session-wide condition**: 16.67× median spread at broker hour 00, already down
to 1.33× at hour 01. Waiting one hour captures **94–98 % of the achievable spread saving**;
the *net* frontier (spread saved minus adverse drift measured against realized entries)
**peaks at 1–2 h** and AH's 4 h convention is past the peak and negative for part of the
cohort. The 4 h number was right about the direction and wrong about the dose.

## Scope and implementation

- Applies to the FX D1 generating sleeves (the `mx_*` D1 cohort and any future D1 FX sleeve
  whose generation clock fills at hour 00).
- **Implementation rides the next generation re-derivation wave** (with AM's clock
  re-derivations), NOT a live config edit today — the armed three sleeves are not in this
  cohort, so nothing armed changes. No config byte moves; the token stays valid.
- Any published economic figure for the cohort remains priced at the hour-00 contract until
  the re-derivation lands; after it lands, republish per sleeve with the hour-01 contract.
- Sleeve composition, weights, and arming remain separate owner decisions.

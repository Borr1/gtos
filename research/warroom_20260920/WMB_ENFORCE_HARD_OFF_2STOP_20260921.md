# WMB ENFORCE — Hard-off cousins + 2-stop remint circuit — 2026-09-21

**As-of:** 2026-09-21 ~01:15 ICT (host 2026-09-20T18:15Z)  
**Seat:** redacted_account F5 CHAIR · Challenge `0` · ns `operator` · magic `0`  
**Verdict:** **LIVE_ARMED**

## ENFORCE 1 — Surface hard-off cousins
Removed from `operator.json` `token_bound.selected_tags_csv` and `f5_launch.ps1` FALLBACK:
- `xa_second_rth`
- `kz_london_crypto_low`

Live argv after recycle: **OFF** for both. Tags count 55→53. KEEP arms still ON: vss / metal_session / NZD proxy / asian_fade.

`src/judgment/family.py` HARD_OFF_FAMILIES now includes both; `xa_second_rth` matcher added (kz already maps via `kz_london*` → orb_crypto family).

## ENFORCE 2 — 2-stop day remint circuit
Landed `src/components/ultimate_book/two_stop_day_circuit.py` and wired in `book_owner.py` beside already_placed_today / isolated re-entry (marker `WMB_2STOP_DAY_CIRCUIT_20260921`).  
Reason prefix: `wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops`.  
Scope: two_bar / rejection_wick / isolated_spike. Reads `judgment/live/just_closed_siblings.json` (stop-class + lossy broker_closed). Smoke OK.

## Writer
2× run_book ALIVE · `GTOS_JEV_SLEEVE_SELECT_APPLY=0` · no place/remint/flatten from Chair.

## Backups
`*.bak_wmb_enforce_20260921` on contract, launch, family, book_owner.

# W7 ULTIMATE_BOOK FOLD — FEASIBILITY VERDICT (2026-06-15)

Source: 11-agent maximum-rigor workflow (6 deep readers → synthesize → 3 adversarial verifiers →
reconcile), every load-bearing claim code-verified [V] against deploy-live. This is the go/no-go
basis for the live fold. **Verdict: do NOT flip any gate. The fold as imagined does not deliver the
W7 edge live, and the live execution path is currently fail-closed.**

## Verified live architecture (the good news — stale path confirmed dead)
- LIVE per-candle authority = the mechanical broader-origin path: `orchestrator.py:7076-7081`
  `_process_vnext_broader_origin_candidates(...)` returns every candle in
  `production_replacement_vnext_moonshot` mode (`agent_config.yaml:613`); the PrimaryAnalyzer/L2
  (`:7586/:7860`) sit BELOW that return → **unreachable. The AI/L2 path is STALE — confirmed.**
- The sizing seam exists: the book could be injected as the producer of `selected_cell_risk_pct` at
  `gtos_vnext_runtime.py:17314`, default-off, as a downward-only CEILING (`orchestrator.py:278`
  `min(current, selected)`). Order path unchanged (`execution.py:2867/2918`).

## THE THREE DECISIVE FINDINGS (why we stop)
1. **The fold confers the book's SIZING/GOVERNANCE, NOT its EDGE [V — GAP-B].** The W7 edge lives in
   the 11 mechanical SLEEVES (FVG-retest, Donchian-20, substrate-state). The live generator produces
   `broader_origin`/`momentum_exhaustion` candidates with only `candidate_origin_family`/`framework`
   + coarse vol/trend proxies (`orchestrator.py:4444-4449`) — **NOT** the book's sleeve taxonomy
   (persist/mtf/rngpos/session/POC). The book sizes only known sleeves
   (`ultimate_book_live_package.py:831-841` unknown → `sized=False, "unknown_sleeve"`). So a flipped
   book returns zero-size for live candidates. **Folding the book over the existing candidate stream
   does NOT trade the validated W7 edge — it sizes a DIFFERENT stream (the same momentum_exhaustion
   family that produced the −$859.69 hard halt).**
2. **The live execution path is CURRENTLY FAIL-CLOSED [V — GAP-A].** `execution_manager_v4` requires
   selector_v4 AND scheduler_v4 packets (`:677-720`; scheduler key absent → defaults True), and the
   live `trade_params` builder (`orchestrator.py:2513-2537`) leaves them unpopulated for synthetic/
   geometric candidates → `fatal: missing_scheduler_v4`. Lifecycle + ~7 other contracts default True
   and are unverified. **Flipping the book gates today trades ZERO until this contract suite is
   empirically enumerated and satisfied — a production change. Relaxing one key does not unblock.**
3. **It is UNPROVEN the current config has ever placed a live order [V].** The −$859.69 hard-halt was
   likely under a PRIOR config; CLAUDE.md still lists "first real vNext order reconciliation" as
   unresolved. **No "it traded before" reasoning is valid.**

## Why the shadow wiring-confirmation can't save it
- GAP-H: `would_units` is computed per-candidate, single-intent, sleeve-less → **structurally
  non-comparable** to the locked W7 MC. The shadow proves WIRING, not book-vs-replay parity.
- GAP-I: a LIVE process can't gather shadow telemetry while halted (`orchestrator.py:812` raises).
- GAP-D: single-intent calls force `n_active=1`, **disabling the book's correlated-collapse + 4%
  gross cap** — the exact protection the loss review demanded.

## What WOULD make the W7 book trade its edge live (owner-scoped, large)
Build/port the 11 mechanical sleeve generators (substrate/regime-tagged) into `src/`, emit sleeve
identity + day-batched intents, enumerate+satisfy the execution_manager_v4 contract suite, wire the
governor with live equity/high-water — a multi-part production-change dossier, not a surgical fold.

## Residual live safeguards that DO exist and stay authoritative (if ever live)
Daily-loss dormant stop (`orchestrator.py:6929-6932/12448`, `risk.max_daily_loss_pct 4.0`,
prop-safe external 5%/overall 10%), per-symbol lockout/cooldown
(`scheduler_v4_best_trade_allocator_same_symbol_daily_loss_lockout` :966), per-kill-zone cap (:38),
equity_guard median filter, the 3 halt flags. The book's 4% correlated-basket cap is NOT delivered
by the seam fold (GAP-D).

## VERDICT
- **Make the book the live size/admission authority: STOP-AND-REPORT.** Large/ambiguous, gated on
  GAP-A/B/C/D, each an owner-reviewed production change. **No gate flip. No real order.**
- **Default-off shadow wiring: bounded-surgical but low-value** (GAP-H/I make it a wiring check only,
  not a parity proof; needs GAP-E/F/J fixes even to be safe). Optional, not a path to live.

# Forward Incubation Spec V1 — funnel shadow → real execution adapter

**Status: SPECIFICATION ONLY. No code exists for this phase, deliberately.**
This document defines how the wave-21 forward-shadow lane
(`FORWARD_SHADOW_RUNBOOK.md`) later gains a REAL execution adapter, and the
ceremony that separates the two. Nothing in it is authorized to run until the
final line's conditions are met.

Governing decisions:

- `BAR3_RATIFICATION_20260811.md` (owner, verbatim: *"yes proceed as proposed
  and recommended with bar-3"*): the scoped **rule∘liquidity_sweep_reclaim**
  claim is the **primary deployable object**; the general rule is the
  research/calibration track.
- Owner-approved risk allocation for data collection: **0.10 % per trade**
  default (final size is Borhen's at the ceremony).

## 1. Scope of phase 2

Execute the **LSR-SCOPED lane first**: only would-be orders the scoped
selection chooses (`scoped_lsr_selected: true` — the same rule restricted to
`liquidity_sweep_reclaim`, MARKET-native by construction) become real orders.
The general lane keeps logging as shadow only. **General-rule execution is a
later expansion**, gated by its own ceremony after the scoped lane has a
forward record.

## 2. The execution adapter (design constraints, in order of authority)

1. **Through the activation-token layer, never around it.** The adapter sends
   exposure-increasing requests exclusively via the token-gated
   `RealMT5.order_send` path. It runs under its **own token namespace /
   profile identity** — a token minted for the incubation lane specifically,
   never the book's token. No token, no order; token absence fails closed.
2. **Own kill-flag file, honored before every send.** The adapter checks
   `shadow_logs/funnel_shadow/INCUBATION_KILL.flag` (its own namespace)
   immediately before each `order_send`; if present, it stands down and logs.
   This is IN ADDITION to token revocation, not instead of it.
3. **Risk defaults:** 0.10 % of account per trade (owner-adjustable at the
   ceremony, never upward by the adapter); **max 2 concurrent positions**;
   **hard cap on daily new exposure: 4 new positions per UTC day** and no new
   entry while daily realized+open P&L ≤ −0.5 %. All four limits enforced
   adapter-side and logged per decision.
4. **FTMO first.** The incubation account is the FTMO account only. No
   redacted_account leg, no second account, until a separate owner word.
5. **Never touches the W7 book**: no shared namespace, no shared tags, no
   shared magic-number range, no reads of the book's state. The book's
   governor and this lane are independent; if the owner's aggregate-drawdown
   arithmetic requires headroom coordination, that is decided AT the ceremony,
   on paper, not in code.
6. **Order contract = the modelled contract.** MARKET entry at decision,
   broker-side SL at `stop_loss` and TP at `take_profit_1` set AT entry,
   2-hour time stop enforced by the adapter (close at horizon), no scale-outs,
   no trailing — exactly the lifecycle the research labels model, so realized
   fills remain comparable to the modelled ones row for row.
7. **Every send logged before and after**: intended request, token check
   result, kill-flag check, order result, deal reconciliation — appended to
   the lane's own JSONL, so the realized-vs-modelled gap becomes its own
   measured dataset (the entire point of incubation).

## 3. Ceremony checklist (owner-executed, in order)

1. Shadow parity PASS on ≥ 5 forward trading days
   (`shadow_parity_harness.py --mode shadow-packets`, exit 0) — the
   acceptance bar defined in the runbook.
2. Owner reads the scoped lane's forward would-be record (selections +
   modelled outcomes, `scoped_lsr_selected: true` rows only) and the
   general-lane comparison.
3. Owner sets final per-trade risk (default 0.10 %), confirms max-2
   concurrent, confirms the daily caps.
4. Mint the incubation token (own namespace), verify the kill flag works
   (place flag → adapter refuses → remove).
5. First session supervised: owner watches the visible terminal through the
   first would-be→real order or first abstention day.
6. Standing rule: any seal break, config drift from the rule bindings, or
   parity failure suspends execution (revoke token first, then investigate).

**This spec ends where it must: awaiting shadow parity + owner ceremony word.**

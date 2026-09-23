# ADR 004 — SL Gate Reconciliation: sl_too_tight vs Apr 16 sweep protection

**Status:** CLOSED-OPTION-C-DE-FACTO
**Date:** 2026-04-18
**Author:** Claude Code (session 26)
**Urgency:** medium — blocks sl_too_tight exception commit; does not block challenge go-live

---

## 1. Summary

The sl_too_tight OB exception spec'd in handoff 16 (2026-04-13) and implemented by Impl-A on 2026-04-18 has the **opposite sign** from the Apr 16 sweep-protection margin that was added after a confirmed XAUUSD -1R loss (handoff 18).

Committing Impl-A as-implemented would remove a safety gate added in direct response to a real trading loss. CEO pre-approved the sl_too_tight exception in principle, but did not revisit the conflict with the intervening Apr 16 fix.

## 2. The two gates

### Gate A — Apr 16 sweep protection (currently LIVE)
- Commits `ee80589` (2026-04-15) and `acf530f` (2026-04-16).
- Rule: `buffer ≥ 0.5 × ATR` (LOWER bound).
- Intent: require SL to be far enough from the OB edge so that a liquidity sweep does not immediately hit it.
- Motivation: confirmed XAUUSD -1R loss on 2026-04-16 where SL was a shade beyond the OB and got swept before price continued in-direction.

### Gate B — sl_too_tight exception (handoff 16 spec, Impl-A implemented)
- Per handoff 16 §46-52.
- Rule: `buffer ≤ 0.5 × ATR` (UPPER bound).
- Intent: allow structural SLs placed just beyond an OB edge when the ATR floor (1.5×) would otherwise block the trade.
- Motivation: ~4-5 A+ trades/week blocked on 2026-04-13 by the 1.5×ATR floor (GBPJPY, GBPUSD confirmed +1.5R winners).

## 3. The conflict

Gate A says: "buffer must be ≥ 0.5 ATR" (SL far from OB).
Gate B says: "buffer must be ≤ 0.5 ATR" (SL tight to OB, structural placement).

Under Gate A alone, the sl_too_tight blocks stand. Under Gate B alone (Impl-A's current implementation), the Apr 16 sweep protection vanishes.

## 4. Options

### Option A — Ship Gate B as-is (replace Gate A for ob_retest trades)
Impl-A's current diff. Gains: unlocks ~4-5 trades/week. Loses: Apr 16 sweep protection for structurally-tight SLs.
- **Risk:** regresses the specific failure mode the Apr 16 fix addressed.
- **Verdict:** NOT RECOMMENDED unless CEO explicitly waives the Apr 16 protection.

### Option B — Do nothing, hold sl_too_tight blocked
Revert Impl-A's diff (no change to permissions.py). sl_too_tight continues to kill ~4-5 trades/week.
- **Verdict:** NOT RECOMMENDED — wastes confirmed edge.

### Option C — Additive: Gate B bypasses Gate A **only** for structural placement (RECOMMENDED)

Semantics: when `framework == "ob_retest"` AND `sl_beyond_edge == True` AND `buffer ≤ 0.5 × ATR` AND `structural_sl_distance > 0`:
  - BYPASS the 1.5×ATR floor (the original sl_too_tight gate)
  - BYPASS the Apr 16 sweep-protection lower bound
  - The trade is permitted on structural grounds regardless of the two ATR-based gates.

Otherwise: Gate A (sweep protection) applies as today.

Rationale: structural SL placement is a different regime from "SL chosen for risk sizing" — the structural claim is that the OB edge is the invalidation point, and price trading beyond it invalidates the setup semantically, not statistically. The Apr 16 sweep-protection gate was designed against arbitrary SL placement, not against structurally-motivated SLs.

- **Risk:** Apr 16 failure mode could still happen for trades admitted via Gate B. This is a known tradeoff: accept sweep risk in exchange for trade frequency on structurally-tight OBs.
- **Mitigation:** the separate liquidity cluster gate (uncommitted from handoff 20, shadow-log mode) specifically targets the "SL sits inside a liquidity pool that will be swept" failure mode. If promoted to live, it addresses the sweep concern orthogonally to ATR geometry.

### Option D — Change Gate B threshold to > 0.5 ATR (no overlap)

Keep Apr 16 sweep protection, and allow sl_too_tight exception ONLY when `buffer > 0.5 × ATR`. This makes the gates non-conflicting but narrows the exception window substantially — structurally-tight SLs are exactly the case sl_too_tight wants to unblock, so this defeats most of the value.
- **Verdict:** NOT RECOMMENDED — negates the fix's purpose.

## 5. Recommendation

**Option C (additive bypass)** with the following implementation delta from Impl-A's current diff:
1. Keep Impl-A's structural geometry helpers.
2. Change the gate decision: when the structural bypass applies, set a new permission flag (e.g. `structural_override=True`) and let it pass both the 1.5×ATR floor AND the Apr 16 sweep margin.
3. Log the bypass with all existing fields PLUS a `bypassed_gates=[sl_too_tight,sweep_margin]` field for post-hoc audit.

Estimated delta: ~30 lines + 4-6 additional tests in test_permissions.py.

## 6. Current state

- Impl-A's diff is **uncommitted** in the working tree (`src/components/permissions.py`, `tests/test_permissions.py`).
- All 65 permissions tests pass locally against Impl-A's diff.
- Impl-A correctly flagged this as needing CEO review before commit.
- The elephant batch research work is fully independent — does not touch permissions.py and is proceeding in parallel.

## 7. Action required from CEO

Choose one of Options A / C / D, or propose an alternative. Option C is claude's recommendation.

Once chosen, claude can commit the appropriate implementation without further approval.

## 8. Links

- Handoff 16 §46-52 — sl_too_tight blocker analysis + proposed fix
- Handoff 18 §all — Apr 16 XAUUSD -1R sweep loss, sweep-margin fix
- Handoff 20 — liquidity cluster gate (shadow-log, would help mitigate Option C risk)
- Impl-A implementation report in the session 26 agent transcript

## 9. Closure note (2026-04-19, session 28)

Sections 6 and 7 above are preserved as a historical record of the decision process. The resolution differed from what §7 requested:

- **Impl-A was REVERTED by CEO on 2026-04-18 (session 26).** The branch implementing Option C's full structural-override semantics (new `structural_override=True` permission flag, `bypassed_gates=[sl_too_tight,sweep_margin]` log field per §71-72) was not taken.
- **The current live config implements Option C-like semantics via the two additive flags in `config/agent_config.yaml` lines 45-56:**
  - `gate1.ob_retest_sl_exception: true` (introduced in `3bf1ff0`, 2026-04-14 pre-live YAML restructure; carries the sl_floor bypass)
  - `gate1.ob_retest_sl_min_buffer_atr: 0.5` (introduced at 0.3 in `acf530f`, 2026-04-16 sweep-margin fix; raised to 0.5 in `1a22d92`, 2026-04-17, after the Apr 16 XAUUSD -1R loss showed 0.3 ATR was too tight against a 0.36 ATR sweep)
- The gate logic that consumes both flags now lives in `src/components/permissions.py::_ob_retest_sl_exception_applies` (lines 258-290+). It bypasses the 1.5×ATR sl_floor AND imposes the 0.5×ATR sweep margin, which is the Option C core behavior without the additional plumbing Impl-A would have added.

**DE-FACTO gloss.** The `CLOSED-OPTION-C-DE-FACTO` header label means the core behavior promised by Option C (additive sweep-margin bypass of sl_too_tight) is live via config, but the two observability features promised in §71-72 (the `structural_override=True` log field and the `bypassed_gates=[sl_too_tight,sweep_margin]` array) were NOT implemented. If those observability fields later become load-bearing for audit or decay analysis, re-open this ADR.

Signed: session 28.

# ADR-004 — Executive Summary

**Date:** 2026-04-24. **Status:** PROPOSED, awaiting CEO decision.
**Full record:** `.context/06_decisions/ADR-004-market-state-structural-bullish-bias.md`

> Filename note: existing `004_sl_gate_reconciliation_2026-04-18.md` is unrelated.
> Functionally this is ADR-005. Consider renaming on commit.

---

## What the bug is

`src/components/market_state.py::identify_structure` (lines 216-257) labels H1 / H4 /
D1 / M15 market structure `bullish` / `bearish` / `transitional`. Two defects compound:

1. `recent_pairs = min(3, ...)` at line 237 saturates at 3 in any window with ≥ 4
   swings of each type. This is always true for production windows (168 H1 bars).
2. The `if bullish / elif bearish / else transitional` chain at lines 239-247 checks
   the bullish branch FIRST. When both qualify — which happens in 99.8% of production
   H1 windows per V1 replay — bullish wins by precedence, regardless of which side has
   stronger numerical evidence.

**Present since initial commit `436c16b` (2026-03-29).** Never touched by a subsequent
commit. Flagged in Phase-2 audit 2026-04-19 as "bug-or-conservative-design, ambiguous"
(`zeta_review.md:41-46`); independent V1 replication 2026-04-24 confirmed the production
impact is severe.

## Evidence (V1 independent validation, 2026-04-24)

| Layer | Evidence | Source |
|---|---|---|
| Live decisions | 141/141 lifetime CANDIDATEs LONG. 112/112 April, 44/44 post-redacted_account. Zero SHORT, ever. | V1 Task 1 |
| Shadow log | `mso_h1_structure_direction = bullish` for 384/384 rows, Apr 17-23, all 5 instruments | V1 Task 3 |
| Historical replay | 8,086/8,086 H1 windows labeled bullish across 5 instruments × Jan 2 – Apr 20, 2026. Zero bearish. | V1 Task 7 |
| Bug condition | 8,072/8,086 (99.8%) windows had the bearish branch ALSO qualifying (i.e., the tie-break fires constantly) | V1 Task 7 |
| Live snapshot | At `2026-04-23T17:00:05`, M15 structure labeled bullish despite bearish evidence being numerically stronger (`ll=50 > hh=43`). H4 correctly labeled bearish (bullish branch failed at hh<3). | `pipeline_state/02_market_state.json` |

## Impact

- Every validated number in CLAUDE.md (62% XAUUSD WR, 65% batch WR, 10.3% CAND rate, 70% OB continuation, 99.4% MC P(FTMO pass), per-instrument WRs) was computed on a LONG-only sample. External validity under a fixed detector is **unknown**.
- The system has never detected or traded a bearish regime. In a sustained bearish regime it would produce zero signals across all instruments.
- Not just a label bug: because `identify_structure` gates `detect_structure_breaks` (line 323-350), only bullish BOS events are emitted → only bullish OBs are formed → the entire downstream OB supply is LONG-only.

## Decision needed from the CEO

Pick ONE of three positions:

| Position | Option | What it does | Why | Risk |
|---|---|---|---|---|
| **P1 — min diff** | **C. Strength tie-break** | When both branches qualify, pick side with higher `hh+hl` vs `ll+lh`. True ties go transitional. | ~5-line diff; preserves existing branch semantics; prompt unchanged. | Slight tilt (one count higher) still decides — no dead zone. |
| **P2 — first-principles (default recommend)** | **D. Net-score classifier** | Compute `score = (hh+hl) - (ll+lh)`. Bullish if > threshold, bearish if < -threshold, transitional if in dead zone. | Removes the two-branch pattern entirely. Symmetric by construction. Trivially testable. | Adds one tunable (`dead_zone_threshold`). |
| **P3 — new research axis** | **E. Slope / F. Hybrid** | Linear regression of highs/lows; bullish if both slopes up. | More robust to choppy regimes. | Per-instrument calibration; outlier sensitive; 20+ threshold params to tune. |

Rejected-for-completeness options:

- **A (raise threshold alone)** — doesn't fix the precedence bug; must be paired with C/D/E/F.
- **B (reverse precedence)** — flips the symmetry but NOT the class of bug; would produce 100% SHORT.
- **G (explicit `neutral` state)** — requires synchronised edits to every downstream consumer; viable but higher blast radius than D.
- **H (emit `conflicted` label)** — creates a state 99.8% of windows enter with no downstream consumer; impractical.

**Recommended default:** **Option D (net-score) with `dead_zone_threshold = max(2, min_swings // 4)`**. Simplest code that provably fixes the bug class. Prompt unaffected. Downstream consumers unaffected.

## Backtest burden (per chosen option)

| Tier | Scope | Cost | Monthly-budget fit |
|---|---|---|---|
| **Min** | XAUUSD × 2 T7 slices (Jan-Feb, Mar-Apr) | ~$54 | Yes ($38 headroom vs $50/mo cap) |
| **Mid** | XAUUSD + USDJPY + EURUSD × 2 slices | ~$162 | Needs 3 months of budget allocation OR CEO waiver |
| **Full** | 5 instruments × 2 slices | ~$270 | Exceeds current monthly cap |

Free pre-validation: 8,086-window historical replay (§6.2) and synthetic fixtures (§6.1) cost $0 and should run regardless of tier chosen.

## Shadow deployment, 1-2 weeks

Add `identify_structure_v2` alongside existing (don't replace). Log both per-candle in
`shadow_logs/structure_divergence.jsonl`. Sample 20 divergences per instrument, verify
which is correct. Promote iff v2 correct ≥ 80% AND §6 backtest clears §6.6 criteria C1-C5.

## Validated numbers that need re-derivation (see ADR-004 §8)

- MUST re-verify: 62% XAUUSD WR, 65% batch WR, 59.5% 2026 WR, 58.5% US30 WR, 75.8% USDJPY WR, 57.1% GBPJPY WR, 10.3% CAND rate, 70% OB continuation, MC 99.4%, +0.200R expectancy. (**10 numbers.**)
- Likely unaffected: session-memory CR-suppression 55%; Opus-vs-Sonnet CR 38 vs 19; FVG-in-impulse +7-20pp (grep confirms no structure.direction dependency).

## Key open questions (see ADR-004 §9)

1. **Does the batch n=367 dataset include SHORT trades?** `data_exploitation_20260405.md:210-219` shows 29 blocked SHORTs. Need to confirm whether those are in the 367.
2. **Does T7 go through `identify_structure`?** YES, by construction — all T7 artifacts inherit the bias.
3. **Other `min(3, ...)` patterns elsewhere?** NO — grep confirmed single hit in `src/`.

## Action items for the CEO

1. Read ADR-004 §4 (options) and §5 (decision framework).
2. Pick a position (P1/P2/P3) and an option letter.
3. Pick a backtest tier (Min/Mid/Full).
4. Authorise shadow deployment phase (CEO approval required per WF-1 — see §7.1).
5. Fill in §10 decision block.
6. Sign. Commit. Proceed.

**Expected timeline:** 2-3 days to ship shadow detector, 1-2 weeks observation, 2-3 days
backtest replay, 1 week comparison + re-derive validated numbers, 1 day production
cutover. **Total to safe production cutover: ~3 weeks from CEO decision.**

---

*Full analysis and code sketches: `.context/06_decisions/ADR-004-market-state-structural-bullish-bias.md`*

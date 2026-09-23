# LIRA A/B 12-Slice Backtest — Pre-Registration

**Registered:** 2026-04-25 (BEFORE launching any slice).
**Purpose:** Validate the LIRA prompt variant's DP4+extension surprise win
(+0.486R vs V3 on 3-slice mini-backtest, n=17 fills) at full
methodological parity with the A2 v2-active backtest. Decide whether
LIRA becomes the post-Monday production prompt or stays research-only.

**Methodology:** Same 12 slices, same v2 detector, same fill / outcome
logic as A2 (`research/a2_v2_active_backtest/`) and F3
(`research/f3_backtest_2026-04-24/`). Only changes vs A2:
- system prompt: V3 production -> LIRA (decision-first / reasoning-after)
- response parser: `simulate_t7._parse_response` -> `schema_adapter.adapt_variant_response`

This is a **pure prompt-architecture A/B** with all other variables held constant.

## Pre-registered decision criteria (frozen before running analyze.py)

These thresholds were chosen BEFORE running `analyze.py` against any
slice data. Script hash logged as the first line of the generated
`ANALYSIS.md` — any post-hoc edit produces a different hash.

### LIRA-GO (promote post-Monday challenge)

ALL of:
1. `LIRA fleet Exp R >= +0.40R`
   - Improves on A2's observed +0.333R AND matches F3 v2's +0.407R
   - This is a strict bar: requires LIRA to clear BOTH baselines
2. `LIRA parse error rate <= 5%`
   - Sanity: LIRA canary saw 0 parse errors on 60 fixtures
   - At ~900 calls in 12-slice scale, 5% headroom for tail edge cases
3. `LIRA XAUUSD SHORT WR >= 40%` (if n >= 3)
   - Tests whether LIRA's claimed SHORT-SL placement advantage replicates
   - n<3 -> criterion auto-passes (insufficient data; rely on other signals)
4. `LIRA fleet MaxDD <= 8R`
   - Same risk gate as A2 — at 1% risk = 8% account DD. FTMO max DD 10%.

### LIRA-STAY (keep V3 / V2 decision unchanged)

ANY of:
- `LIRA fleet Exp R <= A2's +0.333R`
  - LIRA must beat the V3-on-v2 baseline to justify a prompt swap
- `LIRA parse error rate > 5%`
  - Schema adapter not robust enough at scale

### LIRA-HALT / council

- `LIRA fleet Exp R in (+0.333, +0.40)` ambiguous window
  - Above A2's V3 baseline but below F3's bar — partial signal
  - CEO + council review required before any cutover decision

## Rationale for thresholds

- **+0.40R Exp floor:** Two separate v2 backtests give us anchor numbers.
  F3 saw +0.407R, A2 saw +0.333R. Setting the bar at the higher anchor
  prevents a "LIRA wins by luck" verdict — LIRA must demonstrate it
  matches or exceeds the strongest prior v2 result.
- **5% parse error rate:** LIRA canary on 60 fixtures was 0/60 parse
  errors. A 5% bar at 900-call scale gives 45-call headroom — generous
  but not negligent.
- **40% XAUUSD SHORT WR if n>=3:** F3 saw 100% (2/2), A2 saw 100% (2/2)
  on n=2 SHORTs each. We can't require 100% at higher n; 40% above
  random (50%) is a useful absolute floor that still validates the SL
  geometry hypothesis from DP4 extension. n<3 cannot statistically
  reject anything; auto-pass to avoid false STAY on data-thin samples.
- **8R MaxDD:** identical to A2 — FTMO 10% total DD, 5% daily; 8R fleet
  buffer leaves 2pp margin for live execution slippage.

## Comparison anchors (3-way table to be produced)

LIRA vs the two v2 reference points on the SAME 12 slices:

| Slice set | V2 (F3) | V3 (A2) | LIRA (this run) |
|---|---|---|---|
| Fleet filled | 32 | 30 | TBD |
| Fleet WR | 56.2% | 53.3% | TBD |
| Fleet Exp R | +0.407R | +0.333R | TBD |
| Total R | +13.0R | +10.0R | TBD |
| MaxDD | n/a | 3.0R | TBD |
| XAUUSD SHORT share | 22.8% | 30.8% | TBD |
| XAUUSD SHORT WR | 100% (2/2) | 100% (2/2) | TBD |

## Analysis script identity

The only script permitted to compute the LIRA-GO/STAY/HALT verdict is
`research/lira_ab_backtest/analyze.py`. Its SHA256 is logged as the
first line of the generated `ANALYSIS.md`. Any subsequent edit
produces a different hash, making post-hoc tuning detectable.

Committed hash at registration (before first slice CANDIDATE/fill):
```
SHA256(analyze.py, LF-normalized) = 3d7a07e30eef41cf721e29969a1780e2d20fb883a9f9ba2849465f316ed58368
```

**Rationale for amended hash:** Initial pre-reg used hash
`20349d31...` (analyze.py with CRLF-stripping `script_sha256` reading
the file byte-stream). Cross-platform reproducibility required adding
LF-normalization to the `script_sha256` function itself — this changed
the file content (the function body) and therefore the hash. The amended
hash above is the FROZEN value going forward; this amendment was made
BEFORE any slice generated a CANDIDATE (s1 finished as 0/0 cold-start
NO_TRADE; all longer slices still in API-call phase).

Verifiable post-run via:
```
python -c "
import hashlib
with open('research/lira_ab_backtest/analyze.py','rb') as f:
    content = f.read().replace(b'\r\n', b'\n')
print(hashlib.sha256(content).hexdigest())
"
```
Or by running `analyze.py` itself — it prints its own hash as the first
line of the generated `ANALYSIS.md`.

## Out-of-scope

- **No comparison against No-CoT.** DP4 already established No-CoT is
  broken (39 sl_beyond_ob L2 rejections; strip-reasoning destroys SL
  geometry). Out of scope for this A/B.
- **No comparison against V4-DRAFT.** V4 was definitively shelved in
  session 39 weekend sprint (A2-DP1 -1.0R regression). Not revisited.
- **No retest of A2's GO/STAY criteria.** A2 shipped its own verdict
  (3/4 PASS, fleet LONG WR 50% in halt window). LIRA's verdict is
  independent: the question is "is LIRA strictly better than V3 on the
  same axis?" not "does v2 still meet A2's criteria?".
- **No instrument expansion.** XAUUSD + USDJPY only. Other 22 MT5
  instruments come post-Monday challenge-deploy validation.
- **No prompt-tuning iteration.** This is a single-shot validation.
  If LIRA-STAY: the DP4 surprise was cherry-picking. If LIRA-HALT:
  CEO decides next step. If LIRA-GO: schedule cutover with cold-review
  pass on the prompt before merge.

## Slice boundaries (mirrors A2 / F3 exactly)

XAUUSD (12-day windows):
- s1: 2026-01-02..2026-01-14
- s2: 2026-01-15..2026-01-27
- s3: 2026-01-28..2026-02-09
- s4: 2026-02-10..2026-02-22
- s5: 2026-02-23..2026-03-07
- s6: 2026-03-08..2026-03-20
- s7: 2026-03-21..2026-04-02
- s8: 2026-04-03..2026-04-13

USDJPY (25-day windows):
- s1: 2026-01-02..2026-01-26
- s2: 2026-01-27..2026-02-20
- s3: 2026-02-21..2026-03-17
- s4: 2026-03-18..2026-04-13

Detector: `--detector-version v2` (NOT v2_shadow). Budget: $6/slice * 12 = $72 expected, $80 hard cap.

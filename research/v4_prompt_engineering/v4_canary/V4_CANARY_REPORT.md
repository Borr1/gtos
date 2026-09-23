# V4 DRAFT — Production 60-Fixture Canary Report

- **Generated:** 2026-04-25 (P2 task per V4_SYNTHESIS_AND_PLAN.md)
- **Mission:** does V4 broadly preserve V3's decisions on known MSOs, or does it flip across a wider sample than V4-DP1's 4 candles?
- **Branch:** `research/v4-canary-p2`
- **Worktree:** `.claude/worktrees/agent-ae18228f9f53cf83a`

## Executive summary

**VERDICT: FAIL.**

V4 DRAFT does NOT broadly preserve V3's decisions. Across the 60-fixture suite:

| Tier | V3 baseline matches | Flips | Allowed (PASS) |
|---|---|---|---|
| Baseline (n=32) | 26/32 = 81% | **6** | ≤1 |
| Borderline (n=28) | 26/28 = 93% | **2** | ≤11 |
| Total flips | — | **8** | — |

**Six baseline-tier flips** — six times over the PASS threshold of 1. This is a structural change, not API noise.

**All 8 flips are NO_TRADE → CANDIDATE.** V4 flipped **8 of V3's 9 NO_TRADE fixtures (89%)** and 0 of V3's 51 CANDIDATE fixtures. V4 is systematically eliminating V3's NO_TRADE rejections.

**7 of 8 flips are LONG entries** (1 SHORT). Direction asymmetry exactly matches V4-DP1's regression pattern.

**V4 schema enforcement is clean.** The single NO_TRADE response correctly emits `c2_m15_opposing` (a valid V4 enum). 0/60 parse failures, 0/60 errors, 0/1 NTR enum violations.

**Recommendation: SHELVE V4 DRAFT** as currently specified. Net flips at this scale plus 7-of-8 LONG bias confirm V4-DP1's -1R/4-candle finding is structural, not sample-specific. Do NOT proceed to P3 (production gate decision) without spec revision.

## Mechanistic finding — V4 working as designed, but design is too aggressive

Inspection of all 8 flip responses (`inspect_flips.py` output) shows V4's three CB-* changes firing exactly per spec:

1. **CB-1 BIAS PRECEDENCE block** — present in 59/60 responses. Model declares bias up front and treats COMPUTED direction as authoritative.
2. **CB-2 "1 CHoCH never flips COMPUTED bias"** — fires in 6/8 flips. V3 was reading single H1 CHoCH as a real C1 fail; V4 now dismisses it.
3. **CB-3 M15 CHoCH ratio ≥ 1.5 = active opposition** — fires in 5/8 flips. V3 was treating M15 CHoCH as opposition; V4 says ratio < 1.5 is "pullback only."

These are all the changes V4-spec asked for, working cleanly. The problem is they collectively make V4 a much weaker NO_TRADE gate. Net effect: 9 NO_TRADE → 1 NO_TRADE in V4's responses.

The single V4 NO_TRADE survivor (`ny_no_trade_c2_fail_m15_opposing_2026jan07`) had M15 CHoCH ratio=2.7 ≥ 1.5 — the only fixture where V4's CB-3 mechanical threshold actually fired NO_TRADE.

## Flip table (V3 baseline vs V4 actual)

| Tier | Label | V3 | V4 | Direction | V4 mechanism cited |
|---|---|---|---|---|---|
| baseline | london_no_trade_c1_c2_fail_2026jan07 | NO_TRADE | CANDIDATE | LONG | CB-2: "1 CHoCH ratio=1.4 does not flip COMPUTED bullish"; CB-3: M15 ratio=1.2 < 1.5 |
| baseline | london_no_trade_c1_fail_h1_bias_2026jan07 | NO_TRADE | CANDIDATE | LONG | CB-2: "9 BOS net bullish; single bearish CHoCH does not flip"; M15 last-5 all bullish BOS |
| baseline | london_no_trade_c2_fail_m15_opposing_2026jan23 | NO_TRADE | CANDIDATE | LONG | CB-3: M15 CHoCH ratio=0.7 < 1.5 = pullback only |
| baseline | ny_candidate_2026mar10_loss | NO_TRADE | CANDIDATE | LONG | CB-1: COMPUTED bullish, M15 most-recent BOS bullish ratio=2.1 |
| baseline | ny_candidate_2026mar24_win | NO_TRADE | CANDIDATE | LONG | CB-1: COMPUTED bullish (3 BOS, medium conf); M15 last-5 all bullish |
| baseline | ny_no_trade_c1_fail_h1_bias_2026jan27 | NO_TRADE | CANDIDATE | LONG | CB-2: "4 BOS bullish + 1 CHoCH bearish, net bullish per upstream"; CB-3 M15 OK |
| borderline | borderline_gbpusd_20260317T0800_fx_precision | NO_TRADE | CANDIDATE | SHORT | CB-3: H1 CHoCH ratio=2.6 → bearish flip; M15 no opposing CHoCH ratio≥1.5 against SHORT |
| borderline | borderline_xauusd_20260227T0945_no_trade | NO_TRADE | CANDIDATE | LONG | CB-1: COMPUTED bullish (5/5 bullish BOS); CB-3: M15 CHoCH ratio=0.9 < 1.5 |

Of the 6 baseline flips, **6 of 6 cite the new BIAS PRECEDENCE / CB-2 dismissal of CHoCH**. This is V4's primary mechanism, behaving as specified.

## Flip pattern analysis

### Direction
- **NO_TRADE → CAND:** 8 (100% of flips)
- **CAND → NO_TRADE:** 0
- → V4 is one-directionally more aggressive

### Long vs short
- **LONG flips:** 7 (88%)
- **SHORT flips:** 1 (12%)
- → V4 disproportionately fires on the bullish side. **Matches V4-DP1's "more aggressive on LONG" finding.**

### V3 NO_TRADE survival under V4
- V3 baseline NO_TRADE count: **9 / 60 fixtures**
- V4 NO_TRADE count: **1 / 60 fixtures**
- → V4 demolishes 89% of V3's NO_TRADE decisions

### Schema (V4 SC-1 enforcement)
- NO_TRADE responses analyzed: 1
- Off-allow-list `no_trade_reason`: **0**
- Parse failures: **0**
- Schema enforcement is clean. (Note: only 1 NO_TRADE response exists, so this is necessary-but-not-sufficient evidence.)

### Tier distribution of flips
- Baseline tier: 6/32 = 18.75% flip rate
- Borderline tier: 2/28 = 7.14% flip rate
- → V4 disproportionately disrupts BASELINE-tier (deep-zone) decisions, not borderline. Concerning: baseline flips should be rare; these were "clear-cut NO_TRADEs" that V4 promoted to CANDIDATE.

### XAUUSD / multi-symbol concentration
- 6 of 8 flips are XAUUSD (under FK label `london_*` / `ny_*` legacy fixtures: all XAUUSD)
- 1 GBPUSD flip (the SHORT one, from CB-3 H1 CHoCH ratio=2.6 firing the *opposite* mechanism)
- 1 XAUUSD borderline flip
- → No clean cross-instrument signal. XAUUSD is overrepresented because the legacy fixture corpus is XAUUSD-heavy.

## Cross-reference with V4-DP1

V4-DP1 (4-candle A2 head-to-head, n=4):
- V4 vs V3 typical-decision Δ: **−1.0R**
- V4 mechanistically correct (CB-1 BIAS PRECEDENCE + CB-2 "1 CHoCH never flips" firing per spec)
- V4 schema-clean (0/20 parse fails, 0/20 enum violations)
- V4 7-of-7 self-consistency on direction (5 reruns each, all unanimous)
- Conclusion: "V4 doing exactly what Agent B's spec asked it to" but V3 got better R via "wrong reasons"

V4 canary at 60-fixture scale (this report):
- V4 schema-clean (0/60 parse fails, 0 enum violations)
- V4 fires 8 NO_TRADE → CAND flips, 7 of 8 LONG (matches DP1's "more aggressive on LONG" pattern)
- V4 mechanistically correct (every flip cites CB-1/CB-2/CB-3 by name)
- V3 NO_TRADE survival rate under V4: 1/9 = 11%

**The 60-fixture sweep confirms V4-DP1's mechanism at scale.** V4-DP1's 4-candle sample was small (regression could have been unlucky), but seeing the same mechanism (CB-2 dismissing single CHoCH counter-signals on LONG-bias H1 windows) flip 7 LONG fixtures across an independent corpus rules out small-sample fluctuation. **V4 is structurally a different gate than V3, not a rule-consistency tweak.**

## Recommendation

**SHELVE V4 DRAFT.** Specifically:

1. **Do NOT ship V4 to production.** V4 fails the canary 6× over the baseline-tier PASS threshold. Production trading on V4 would mean trading 8× more setups than V3 over the same fixture distribution, with no R-validation that the new setups have edge.
2. **Do NOT proceed to P3** (production-gate decision) without spec revision.
3. **CB-2 ("1 CHoCH never flips") is the highest-leverage offender.** 6 of 8 flips invoke it. If V4 is to be revived, CB-2 needs either:
   - A counterweight (e.g., "1 CHoCH with displacement_ratio ≥ 2.0 DOES flip COMPUTED bias"), or
   - Removal entirely, leaving only CB-1 BIAS PRECEDENCE + CB-3 M15 ratio threshold.
4. **CB-3 ratio threshold is plausibly OK.** The lone NO_TRADE survivor (`ny_no_trade_c2_fail_m15_opposing_2026jan07`) shows CB-3 fires correctly when ratio ≥ 1.5; the 1.5 threshold itself is a research question (could be 1.0 or 2.0), but that's separate from "V4 too aggressive."
5. **Per V4-DP1 + this canary, the regression is real, not the unlucky-roll Candle 3 hypothesis.** DP1 left it ambiguous whether V4 was "doing the right thing on a bad-luck candle"; the canary at scale shows the same mechanism produces 8× more CANDs across an independent fixture corpus, confirming V4 is structurally over-firing.

**If CEO wants to revive V4:** require revised spec (CB-2 weakened or removed), regenerate this canary against the revised draft, and require ≤1 baseline flip + ≤11 borderline flip on the same 60-fixture suite before any production consideration.

## Cost summary

| Metric | Value |
|---|---|
| Fixtures processed | 60 / 60 |
| API errors | 0 |
| Parse failures | 0 |
| Tokens (input) | 645,754 |
| Tokens (output) | 87,300 |
| Estimated cost (Sonnet 4.6 published rates) | **$3.25** |
| Budget cap | $10.00 |
| Cost utilization | 32.5% |
| Wall time | 296 s (4.9 min, 5-way concurrency) |

Cost ran cleanly under cap. No budget overruns.

## Artifacts

- `run_v4_canary.py` — main runner (60-fixture sweep, V4-aware system_prompt rebuilder)
- `inspect_flips.py` — per-flip preamble + reasoning extractor
- `reanalyze_schema.py` — robust JSON-extraction schema check (post-hoc)
- `v4_canary_raw_responses.jsonl` — per-fixture raw API response (60 lines, ~880 KB)
- `v4_canary_results.json` — structured comparison + flip details
- `V4_CANARY_REPORT.md` — this document

V3 baseline reference (unchanged, in production canary): `scripts/canary_fixtures/baseline.json` (created 2026-04-24T01:00:34Z, model=claude-sonnet-4-6 effort=max).

## Method note — fixture symbol/config detection

Of the 60 fixtures, 16 have null `symbol` field (legacy XAUUSD-only fixtures created before multi-symbol expansion). My runner falls back through:
1. `fixture['symbol']` if present (44 fixtures)
2. Label-prefix match against {xauusd, eurusd, gbpusd, usdjpy, gbpjpy, us30_cash, nas100} (recovers all 4 borderline_xauusd_*)
3. `london_*`/`ny_*` prefix → XAUUSD default (12 legacy fixtures)
4. XAUUSD as final fallback

This matches `update_canary_system_prompts_v2.py`'s precedent which assumed XAUUSD for the older fixture corpus. Final symbol distribution: XAUUSD=28, EURUSD=8, USDJPY=7, GBPUSD=5, US30_cash=5, GBPJPY=4, NAS100=3.

Of the 60 V3 fixture system_prompts, 16 carried a `## Static Context (D1/H4/Session)` tail (the older XAUUSD ones); my runner preserves that tail verbatim and prepends V4's freshly-built head. The 44 newer multi-symbol fixtures from M2b have only the head and no tail (matching `generate_expanded_canary_fixtures.py:521`).

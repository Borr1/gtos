"""System and user prompts for Component 3A — Primary Analyzer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from src.models.market_state_models import MarketStateObject

# Default price format — overridden per instrument via config
_PRICE_FMT = ".2f"


def _pfmt(value: float) -> str:
    """Format a price using the current instrument's precision."""
    return f"{value:{_PRICE_FMT}}"


def set_price_format(fmt: str) -> None:
    """Set the price format string for the current instrument."""
    global _PRICE_FMT
    _PRICE_FMT = fmt

# ── Anti-hallucination guardrail (shared by debate/judge/postmortem prompts) ──
# The primary analyzer prompt (Phase 2A v1) has its own Data Grounding and
# Consistency rules inline, so build_system_prompt() no longer appends this.
# But bull_agent, bear_agent, judge, and postmortem prompts still import it.
ANTI_HALLUCINATION = """
## Data Grounding Rules
- Base ALL analysis on the price data provided in the Market State Object. If a price level, swing, or pattern is not present in the Market State Object, it does not exist.
- If you cannot determine a structure direction with high confidence from the data provided, state 'unclear' — do not force a classification.
- Respond with ONLY valid JSON matching the schema. Your response MUST start with { and end with }. No preamble, no markdown fences, no explanation outside the JSON.
""".strip()

# ── Instrument identity mapping ──────────────────────────────────────
_INSTRUMENT_IDENTITY = {
    "XAUUSD": "institutional gold trader with 15+ years of experience trading XAUUSD",
    "EURUSD": "institutional forex trader with 15+ years of experience trading EURUSD",
    "GBPUSD": "institutional forex trader with 15+ years of experience trading GBPUSD",
    "USDJPY": "institutional forex trader with 15+ years of experience trading USDJPY",
    "GBPJPY": "institutional forex cross trader with 15+ years of experience trading GBPJPY",
    "NZDUSD": "institutional forex trader with 15+ years of experience trading NZDUSD",
    "NAS100": "institutional index trader with 15+ years of experience trading NAS100",
    "US30_cash": "institutional Dow Jones index trader with 15+ years of experience trading US30",
    "XAGUSD": "institutional silver trader with 15+ years of experience trading XAGUSD",
}


def _build_precision_examples(price_fmt: str, symbol: str) -> tuple[str, str, str]:
    """Build per-instrument VALID / INVALID price examples for the PRECISION block.

    Returns (decimal_count_str, valid_example_block, invalid_example_block).
    The price_fmt is a Python format spec like ".5f", ".3f", ".2f", ".1f".
    """
    # Extract decimal-place count from the format spec (".Nf" -> N)
    try:
        dp = int(price_fmt.strip(".f"))
    except (ValueError, AttributeError):
        dp = 2

    # Anchor prices used by each illustrative instrument family. These are
    # illustrative only \u2014 not load-bearing for any specific fixture; the
    # AI must still ground actual emissions in the MSO data.
    if dp >= 5:
        # 5dp FX (EURUSD, GBPUSD)
        anchors = {
            "entry": "1.26543",
            "sl_long": "1.26298",
            "tp1_long": "1.27033",
            "sl_short_wrong": "1.26298",  # wrong for SHORT
            "tp1_short": "1.26053",
            "sl_short_right": "1.26789",
            "sl_long_wrong": "1.26789",   # wrong for LONG (above entry)
            "buffer": "0.00020",
            "too_few": "1.26",
            "too_many": "1.265432",
            "buffer_zero": "0.00000",
        }
    elif dp == 3:
        # 3dp JPY crosses (USDJPY, GBPJPY)
        anchors = {
            "entry": "156.821",
            "sl_long": "156.605",
            "tp1_long": "157.145",
            "sl_short_wrong": "156.605",
            "tp1_short": "156.497",
            "sl_short_right": "157.045",
            "sl_long_wrong": "157.045",
            "buffer": "0.020",
            "too_few": "156.8",
            "too_many": "156.82134",
            "buffer_zero": "0.000",
        }
    elif dp == 1:
        # 1dp index (NAS100)
        anchors = {
            "entry": "18453.2",
            "sl_long": "18420.5",
            "tp1_long": "18502.3",
            "sl_short_wrong": "18420.5",
            "tp1_short": "18404.0",
            "sl_short_right": "18475.0",
            "sl_long_wrong": "18475.0",
            "buffer": "3.0",
            "too_few": "18453",
            "too_many": "18453.25",
            "buffer_zero": "0.0",
        }
    else:
        # 2dp XAUUSD / US30 default
        anchors = {
            "entry": "2346.55",
            "sl_long": "2340.25",
            "tp1_long": "2355.98",
            "sl_short_wrong": "2340.25",
            "tp1_short": "2337.12",
            "sl_short_right": "2352.80",
            "sl_long_wrong": "2352.80",
            "buffer": "0.50",
            "too_few": "2346",
            "too_many": "2346.553",
            "buffer_zero": "0.00",
        }

    # Pick a representative example instrument name for clarity
    example_symbol = {5: "GBPUSD", 3: "USDJPY", 1: "NAS100", 2: "XAUUSD"}.get(dp, symbol)

    valid_block = (
        f"VALID (LONG, {dp}dp instrument like {example_symbol}): "
        f"entry_price: {anchors['entry']}, stop_loss: {anchors['sl_long']}, "
        f"take_profit_1: {anchors['tp1_long']} (SL < entry < TP1)\n"
        f"VALID (SHORT, {dp}dp instrument like {example_symbol}): "
        f"entry_price: {anchors['entry']}, stop_loss: {anchors['sl_short_right']}, "
        f"take_profit_1: {anchors['tp1_short']} (TP1 < entry < SL)\n"
        f"VALID sl_buffer_applied: {anchors['buffer']} "
        f"(exactly {dp} decimal places, strictly > 0)"
    )

    invalid_block = (
        f"INVALID (too few decimals): entry_price: {anchors['too_few']} "
        f"(must use exactly {dp} decimals for this instrument; {anchors['too_few']} "
        f"has fewer)\n"
        f"INVALID (too many decimals): entry_price: {anchors['too_many']} "
        f"(must use exactly {dp} decimals; do not add extra precision)\n"
        f"INVALID (SL wrong side for LONG): entry_price: {anchors['entry']}, "
        f"stop_loss: {anchors['sl_long_wrong']} "
        f"(LONG requires stop_loss STRICTLY BELOW entry_price)\n"
        f"INVALID (SL wrong side for SHORT): entry_price: {anchors['entry']}, "
        f"stop_loss: {anchors['sl_short_wrong']} "
        f"(SHORT requires stop_loss STRICTLY ABOVE entry_price)\n"
        f"INVALID (zero buffer): sl_buffer_applied: {anchors['buffer_zero']} "
        f"(must be strictly > 0; pick the max of 0.25*H1 ATR or 3 ticks)\n"
        f"INVALID (collapsed prices): entry_price == stop_loss, or "
        f"entry_price == take_profit_1 \u2014 never emit the same price twice"
    )

    return str(dp), valid_block, invalid_block


def build_system_prompt(config: dict | None = None) -> str:
    """Build the PA system prompt with instrument-specific values.

    When *config* is ``None``, returns the gold-default prompt
    (backward compatible).
    """
    if config is None:
        config = {}

    symbol = config.get("market", {}).get("symbol", "XAUUSD")
    sl_min = config.get("risk", {}).get("sl_absolute_min", 5.0)

    # Unit label for SL minimum
    _PIP_PAIRS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD")
    _JPY_PAIRS = ("USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY")
    _POINT_INSTRUMENTS = ("NAS100", "US30_cash", "US500_cash")

    if symbol in _PIP_PAIRS:
        sl_min_display = f"{sl_min / 0.0001:.0f} pips"
    elif symbol in _JPY_PAIRS:
        sl_min_display = f"{sl_min / 0.01:.0f} pips"
    elif symbol in _POINT_INSTRUMENTS:
        sl_min_display = f"{sl_min:.0f} points"
    else:
        sl_min_display = f"${sl_min:.2f}"

    # Build KZ display text from config
    kz_cfg = config.get("market", {}).get("kill_zones", {})
    _KZ_LABELS = {"london": "London Open", "ny": "NY Open"}
    if kz_cfg:
        kz_lines = []
        for name, times in kz_cfg.items():
            label = _KZ_LABELS.get(name, name.title())
            start = times.get("start_utc", "07:00")
            end = times.get("end_utc", "09:30")
            kz_lines.append(f"- {label}: {start}\u2013{end} UTC")
        kz_display = "\n".join(kz_lines)
    else:
        kz_display = "- London Open: 07:00\u201309:30 UTC\n- NY Open: 13:00\u201315:30 UTC"

    # Per-instrument decimal-place directive (PROMPT V2 Issue 1 \u2014 FX precision).
    # Uses the same _PRICE_FMT set by set_price_format() at build time
    # (primary_analyzer.py:194-195), keeping prompt + MSO rendering in lockstep.
    price_fmt = config.get("prompt", {}).get("price_format", _PRICE_FMT)
    dp_count, valid_examples, invalid_examples = _build_precision_examples(
        price_fmt, symbol,
    )

    text = _SYSTEM_PROMPT_TEMPLATE
    text = text.replace("{kz_display}", kz_display)
    text = text.replace("{sl_min_display}", sl_min_display)
    text = text.replace("{decimal_places}", dp_count)
    text = text.replace("{valid_examples}", valid_examples)
    text = text.replace("{invalid_examples}", invalid_examples)
    return text


# ── Section 5.1 — Primary Analyzer System Prompt (T7 C-Gate Evaluation) ──
# Deployed 2026-04-13.  Replaces P2A v1 scored evaluation with C-gate-only decision.
# Evidence (n=121, in-sample):
#   T7: CR=86%, WR=66.3%, CR*WR=0.570, R=+39.5R, 0 DIVs
#   vs P2A v1: CR=38%, WR=69.6%, CR*WR=0.265, R=+22.9R
# Key insight: Q1-Q7 scoring had zero predictive power (r=-0.06, p=0.574).
# The discriminative signal comes entirely from the structural C-gate.
#
# PROMPT V3 (2026-04-24): closes V8-flagged loophole where V2 model still
# invents NO_TRADE reasons ("touches<2", "reachable-distance", "at current
# price context") that are not on the system's enumerated allow-list. V3
# adds an explicit NO_TRADE-reason allow-list + strengthened anti-gaming
# block. Ships in concert with canary fixture regeneration against `c1697b3`.
_SYSTEM_PROMPT_TEMPLATE = """You are a structural bias evaluator for an order block retest trading system. Your single task: determine whether H1 shows clear directional bias and M15 does not actively oppose it.

Your evaluation must be DATA-DRIVEN — based on structural breaks (BOS and CHoCH) in the Market State Object provided.

## Kill Zone Windows
{kz_display}
You will be told which window is being evaluated.

## CALIBRATION
Historical base rate: 65-80% of evaluated setups qualify as CANDIDATE. You are identifying structural conditions, not predicting individual trade outcomes. Over-rejection is as costly as over-acceptance — rejecting a qualifying setup costs the system +0.20R expected value.

## STRICT RULE — ENUMERATED NO_TRADE REASONS (PROMPT V3)

If your decision is NO_TRADE, the `no_trade_reason` field MUST be exactly
one of the following eight strings. No other reason string is permitted.
Emitting any string not on this list is a schema violation and will be
treated as a malformed response.

ALLOW-LIST (the ONLY legal NO_TRADE reasons you may emit):

  (R1) `c1_failed`                 — H1 has no clear recent BOS/CHoCH, or
                                      structure is genuinely mixed/unclear.
                                      This is C1 FAIL per the three gates.
  (R2) `c2_m15_opposing`           — M15 has an explicit CHoCH AGAINST H1
                                      direction, or a series of BOS actively
                                      opposing H1. This is C2 FAIL.
                                      (A single opposing candle or minor
                                      pullback is NOT C2 FAIL — C2 PASS in
                                      that case.)
  (R3) `c3_direction_mismatch`     — H1 bullish but you intended SHORT, or
                                      H1 bearish but you intended LONG. C3 FAIL.
  (R4) `no_qualifying_h1_poi`      — EVERY condition below must hold:
                                      (i) C1 AND C2 AND C3 all PASS, AND
                                      (ii) the MSO's `## H1 — ...` section
                                           contains ZERO unmitigated OBs in
                                           the direction matching C3
                                           (bullish OBs for LONG, bearish
                                           OBs for SHORT), AND
                                      (iii) the same `## H1 — ...` section
                                           contains ZERO unretested breaker
                                           zones in the same direction.
                                      If you cannot count BOTH (ii) and (iii)
                                      as literally zero from the MSO text,
                                      R4 does NOT apply — the correct
                                      decision is CANDIDATE.
  (R5) `self_check_failed`         — one of the six SELF-CHECK items (see
                                      SELF-CHECK section below) failed on your
                                      proposed CANDIDATE parameters. Append a
                                      1-sentence explanation naming which
                                      self-check item failed (e.g., "SL on
                                      wrong side of entry for LONG").
  (R6) `wrong_side_sl`             — identical to R5 case where geometry
                                      check (1 or 2) fails. Prefer R6 over
                                      R5 when the failure is specifically
                                      SL-wrong-side.
  (R7) `degenerate_trade_parameters` — identical to R5 case where
                                      non-degeneracy check (4) fails.
                                      Prefer R7 over R5 when the failure
                                      is specifically entry==SL or
                                      entry==TP1.
  (R8) `ai_output_malformed`       — you cannot produce valid JSON matching
                                      the schema. Rarely needed; the
                                      framework retries malformed output
                                      automatically.

Any no_trade_reason emitted must be a LITERAL MATCH to one of R1-R8 above.
Do NOT paraphrase, elaborate, or invent variants. Do NOT emit compound
reasons like "c1_failed + distance"; pick the single matching reason.

FORBIDDEN NO_TRADE REASONS — these strings and any paraphrase of them
are explicitly NOT on the allow-list and will be treated as prompt-gaming:

  (G1) `touches<2`, `touches_too_low`, `touch_count_insufficient`, or any
       reference to how many times an OB has been touched. Touch count is
       NOT a gate-layer criterion. A deterministic downstream gate
       handles touch-count rejection — you must NOT pre-empt it.
  (G2) `reachable_distance`, `too_far`, `unreachable`, `at_current_price_context`,
       `out_of_range`, `price_too_distant`, or any reference to how far
       the OB is from the current candle price. Distance/proximity is NOT
       a gate-layer criterion.
  (G3) `zone_width_too_wide`, `zone_width_too_narrow`, `poor_OB_quality`,
       `weak_displacement`, `weak_BOS`, `low_displacement_ratio`,
       `imperfect_zone`, or any subjective pattern-quality rejection.
  (G4) `sweep_not_detected`, `no_liquidity_sweep`, `no_FVG_support`,
       `confluence_lacking`, or any missing-confluence rejection. Sweeps,
       FVGs, and confluence are OBSERVATION REPORT fields — they do NOT
       gate the decision.
  (G5) Any reason beginning with "C1=PASS C2=PASS C3=PASS but..." unless
       the text after "but" is a LITERAL substring of one of R4, R5, R6,
       or R7 above, AND the corresponding allow-list conditions are met.
       See the dedicated block "STRICT RULE — NO FOURTH GATE" below.

If you find yourself reaching for ANY rejection concept not on R1-R8, the
correct response is CANDIDATE. The downstream system has additional gates
that will reject the trade if it is unsafe; your job at this stage is
ONLY to evaluate C1/C2/C3 (and apply the six SELF-CHECK items to your
own numeric output). Over-rejection at this layer costs the system
documented expected-value (+0.20R per rejected qualifying setup).

## THE THREE STRUCTURAL GATES (your ENTIRE decision criteria)

C1. H1 DIRECTIONAL BIAS — H1 is the primary and sufficient timeframe.
- 2+ BOS in the same direction → bias CONFIRMED in that direction.
- CHoCH followed by BOS in the new direction → bias CONFIRMED in the CHoCH direction.
- D1 data (if present) may reinforce H1 but is NOT required.
- H4 data does not exist in this Market State Object — its absence is not a failure.
- No clear recent BOS/CHoCH, or structure genuinely mixed/unclear → C1 FAIL.

C2. M15 NON-OPPOSITION — M15 must not be actively working against H1.
- M15 aligned with H1 direction → PASS.
- M15 neutral, ranging, or no clear recent breaks → PASS.
- M15 CHoCH AGAINST H1, or a series of BOS actively opposing H1 → FAIL.
- A single opposing candle or minor pullback does NOT constitute active opposition.

C3. DIRECTION MATCH
- H1 bullish → LONG. H1 bearish → SHORT. Mismatch → FAIL.

## DECISION RULE
C1 AND C2 AND C3 all pass → **CANDIDATE**
Any gate fails → **NO_TRADE**
There is no WAIT category.

## DECISION INTEGRITY — MANDATORY
- **If C1, C2, and C3 all pass: output CANDIDATE. There are no other requirements.**
- Do NOT reject a setup where all three gates pass based on zone proximity, price distance, pattern quality, or any other factor not listed above.
- The MSO contains order block, FVG, and zone data. **Do NOT use this data for your CANDIDATE/NO_TRADE decision.** Use only BOS/CHoCH structural break data for the three gates.
- Your entire decision is: "Does H1 show clear directional bias? Is M15 not actively opposing it? Does the direction match?" That is all.

## FRAMEWORK
OB Retest framework ONLY. Ignore all other framework references.

## STRICT RULE — H1 POI SOURCE (PROMPT V2)
The h1_setup.poi_price_level you cite MUST come from the **H1 timeframe's**
zone arrays in the MSO. Qualifying H1 POI sources are:
  (A) an unmitigated H1 order block (from `Unmitigated OBs (N):` under
      `## H1 — Structure: ...`), OR
  (B) an unretested H1 breaker zone (listed in the same `## H1 — ...`
      section under the retested-flag tracking line).

**Forbidden substitutions** — never cite one of these as the H1 POI:
  (F1) Any zone listed under `## M15 — ...`, `## M5 — ...`, `## D1 — ...`,
       or `## H4 — ...`. Those are off-limits as H1 POI sources, no matter
       how enticing the geometry looks. "Promoting" an M15 OB to the H1
       POI role is the specific failure mode this rule prevents.
  (F2) A price that does not fall inside any zone listed in the MSO's
       `## H1 — ...` section. No round-number POIs, no FVG mid-prices.

This rule does NOT override DECISION INTEGRITY. The C-gate decision
(CANDIDATE vs NO_TRADE) is governed by C1/C2/C3; the STRICT RULE only
constrains WHICH zone you cite as the POI when decision is CANDIDATE,
and carves out a very specific NO_TRADE case (below).

Order of operations:
  Step 1. Evaluate C1/C2/C3.
  Step 2. If any fails → NO_TRADE (no_trade_reason = which gate failed).
  Step 3. If all three pass:
          - If at least one unmitigated H1 OB or unretested H1 breaker
            in the correct direction for C3 is listed in the MSO, the
            decision is CANDIDATE. Cite that zone's midpoint as the
            POI (prefer the lowest-touches one). `touches >= 2` is NOT
            a C-gate disqualifier — downstream gates handle that.
            Distance from current price, zone width, FVG presence,
            sweep presence, displacement quality, or any other heuristic
            is NOT a disqualifier at the C-gate layer.
          - ONLY if the MSO's H1 section is EMPTY of any OB AND any
            breaker in the correct direction (zero zones to cite,
            literally nothing), then the decision is NO_TRADE with
            no_trade_reason = "no_qualifying_h1_poi". This is the
            ONLY condition that triggers that reason. "Price is far
            from OB" is NOT that condition.

If you find yourself writing "C1=PASS C2=PASS C3=PASS but..." after
checking the H1 section has at least one zone, STOP — the correct
decision is CANDIDATE, not NO_TRADE. The "but" clause is exactly the
reasoning the DECISION INTEGRITY rule forbids.

A downstream verification gate (`h1_poi_exists`, at
`src/components/verification.py`) cross-checks the cited
poi_price_level against the H1 zone arrays with instrument-specific
tolerance. If your cited POI is not in the H1 arrays, L2 rejects.

## STRICT RULE — NO FOURTH GATE (PROMPT V3)

There are exactly THREE gates: C1, C2, C3. There is no C4. There is no
"quality" check. There is no "proximity" check. There is no "touch count"
check. There is no "context" check. There is no "reasonable distance"
check at this layer.

The pattern "C1=PASS C2=PASS C3=PASS but {anything}" is FORBIDDEN unless
{anything} is a LITERAL match to one of:

  - "no_qualifying_h1_poi"  AND  the H1 section is empty of any
                                  same-direction OB AND breaker (R4 above);
  - "self_check_failed: <which-of-the-six>" AND the named self-check item
                                              fails on YOUR proposed numbers
                                              (R5 above);
  - "wrong_side_sl"          AND the SL you proposed is on the geometrically
                                  wrong side of entry (R6 above);
  - "degenerate_trade_parameters" AND your proposed entry, SL, or TP1 are
                                       bit-identical (R7 above).

If you cannot honestly write the post-"but" text as a literal substring of
one of those four phrases, the correct decision is CANDIDATE. Do not
substitute "but no_qualifying_h1_poi" when the H1 section actually
contains at least one same-direction OB. Do not substitute "but
self_check_failed" when your numbers actually pass all six self-checks.

Examples of FORBIDDEN reasoning that V8 caught V2's prompt rationalizing:

  FORBIDDEN: "C1=PASS C2=PASS C3=PASS but no_qualifying_h1_poi in correct
              direction at current price context — H1 OB at X-Y exists
              (touches=1) but is too far below current price"
  → The OB exists. R4's empty-H1 condition is NOT met. The mention of
    "current price context" / "too far" is exactly G2 above. The correct
    decision is CANDIDATE.

  FORBIDDEN: "C1=PASS C2=PASS C3=PASS but touches<2"
  → Touch count is G1 above; not your concern at this gate. The correct
    decision is CANDIDATE.

  FORBIDDEN: "C1=PASS C2=PASS C3=PASS but all H1 bullish OBs are far
              below current price"
  → "far below" is G2 above; distance is not a gate-layer criterion. The
    correct decision is CANDIDATE.

  FORBIDDEN: "C1=PASS C2=PASS C3=PASS but the OB has wide range / no
              displacement / weak quality"
  → G3 above; pattern quality is not a gate-layer criterion. The correct
    decision is CANDIDATE.

If after C1/C2/C3 all PASS and the H1 section has at least one
same-direction OB or breaker AND your numeric self-checks all pass, the
decision is CANDIDATE. There is no fourth gate to apply. Distance,
quality, touches, sweeps, FVGs, displacement ratios, and "context" all
belong to downstream system layers — not to you.

## TRADE PARAMETERS (if CANDIDATE)
Compute trade parameters from the MSO price data:
- entry_price: OB zone entry — ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT (bottom of nearest unmitigated H1 OB). Do NOT use the current candle close price. Prefer the lowest-touches OB (touches=N shown in the OB line); a deterministic gate will reject touches>=2 downstream.
- stop_loss: place BEYOND the nearest significant H1/M15 swing low (LONG) or swing high (SHORT) using a non-zero buffer (see sl_buffer_applied below), minimum {sl_min_display} total distance from entry
- take_profit_1: entry + 1.5 x |entry - stop_loss| (LONG) or entry - 1.5 x |stop_loss - entry| (SHORT)
- risk_reward_ratio: 1.5
- position_size_lots: 0.01
- sl_buffer_applied: compute a non-zero buffer using max(0.25 x H1 ATR(14) from MSO, 3 x the smallest price tick shown). For LONG the buffer sits BELOW the protected swing low; for SHORT it sits ABOVE the protected swing high. The stop_loss is the swing ± buffer. Report the exact buffer value you applied in this field (use the same decimal precision as prices in the MSO).
- take_profit_2, take_profit_3: 0.0

## PRECISION (PROMPT V2 — strengthened FX scaffolding)

This instrument uses **EXACTLY {decimal_places} decimal places** for every
price-valued field. That applies to: entry_price, stop_loss, take_profit_1,
take_profit_2, take_profit_3, and sl_buffer_applied.

Every price you emit MUST match the decimal-place count of the prices in
the Market State Object above. Do NOT round FX prices to 2 decimals. Do NOT
add extra decimals beyond what the MSO uses.

**Geometric invariants (bit-exact; violating any one is a schema violation):**
- LONG direction: `stop_loss < entry_price < take_profit_1` (strictly, no equality)
- SHORT direction: `take_profit_1 < entry_price < stop_loss` (strictly, no equality)
- sl_buffer_applied > 0 (strictly; never 0.0, never negative)
- entry_price != stop_loss AND entry_price != take_profit_1 (never emit the same price twice)

### Valid examples (shape only — ground your actual numbers in the MSO)
{valid_examples}

### Invalid counter-examples (each line shows a common failure mode)
{invalid_examples}

### Why precision matters
Emitting fewer decimals than the instrument requires collapses entry / SL / TP1
into the same rounded value, which the system will reject as degenerate
(`guard_candidate_degenerate_params`). Emitting the SL on the wrong side of
entry (SL > entry for LONG, or SL < entry for SHORT) is geometrically
impossible for a protective stop and will also be rejected.

## OBSERVATION REPORT (for system logging — does NOT affect your decision)
After determining your decision via C1/C2/C3, also report structural observations from the MSO. These fields feed downstream verification and logging. They do NOT change your CANDIDATE/NO_TRADE decision.

- daily_bias: Report H1 direction as the bias. confidence = high if 3+ BOS, medium if 2 BOS, low if 1 BOS or CHoCH only.
- h4_alignment: Always set aligned=true, explanation="H4 data not provided in MSO".
- h1_setup: Report the nearest unmitigated H1 OB. poi_identified=true if one exists; poi_price_level = midpoint of the OB zone; zone = premium/discount based on impulse structure; causing_event_type from the BOS/CHoCH that created it. If no unmitigated H1 OB exists, poi_identified=false, poi_type="none", poi_price_level=0.
- liquidity_sweep: Report any detected sweeps from the MSO. If none, detected=false.
- m15_confirmation: Report M15 structural state. choch_detected=true if M15 has CHoCH or BOS with displacement in the trade direction. displacement_quality: >=1.5x avg body = strong, 1.2-1.5x = medium, <1.2x = weak. Report the actual ratio.
- setup_grade: Always "A+" for CANDIDATE (the C-gate pass IS the quality gate). "C" for NO_TRADE.
- overall_reasoning: 1-2 sentences summarizing which C-gates passed/failed.

## Data Grounding Rules
- Base ALL analysis on the data in the Market State Object. If a price level, structure event, or pattern is not in the MSO, it does not exist.
- If you cannot determine structure direction with high confidence, state "unclear" — do not force a classification.
- Respond with ONLY valid JSON. Your response MUST start with { and end with }.

## Output Schema
```json
{
  "timestamp_utc": "<ISO-8601 of the candle being evaluated>",
  "model_used": "<model identifier>",
  "decision": "NO_TRADE | CANDIDATE",
  "confidence_score": <50-90>,
  "confidence_computation": "<C1=PASS/FAIL C2=PASS/FAIL C3=PASS/FAIL>",
  "framework": "ob_retest | none",
  "kill_zone": "london | ny",
  "frameworks_evaluated": {
    "ob_retest": {"qualified": <bool>, "reason": "<1 sentence>"}
  },
  "reasoning": {
    "daily_bias": {
      "direction": "bullish | bearish | ranging",
      "confidence": "high | medium | low",
      "protected_swing_level": <float or 0>,
      "explanation": "<1 sentence>"
    },
    "h4_alignment": {
      "aligned": true,
      "h4_pois_identified": [],
      "explanation": "H4 data not provided in MSO"
    },
    "h1_setup": {
      "poi_identified": <bool>,
      "poi_type": "OB | none",
      "poi_price_level": <float>,
      "zone": "premium | discount | neutral",
      "fib_retracement_pct": <float or 0>,
      "causing_event_type": "BOS | CHoCH | unknown",
      "explanation": "<1 sentence>"
    },
    "liquidity_sweep": {
      "detected": <bool>,
      "pool_type": "<type or none>",
      "sweep_quality": "clean | messy | ambiguous",
      "sweep_price": <float or 0>,
      "explanation": "<1 sentence>"
    },
    "m15_confirmation": {
      "choch_detected": <bool>,
      "displacement_quality": "strong | medium | weak | none",
      "displacement_candle_body_vs_avg_ratio": <float or 0>,
      "explanation": "<1 sentence>"
    },
    "similar_historical_setups_considered": [],
    "setup_grade": "A+ | C",
    "overall_reasoning": "<1-2 sentences>"
  },
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE: EXACTLY one of R1-R8 from the allow-list — c1_failed | c2_m15_opposing | c3_direction_mismatch | no_qualifying_h1_poi | self_check_failed | wrong_side_sl | degenerate_trade_parameters | ai_output_malformed>"
}
```

When decision is "CANDIDATE", trade_parameters MUST be:
```json
{
  "direction": "LONG | SHORT",
  "entry_price": <float, MSO precision>,
  "stop_loss": <float, MSO precision>,
  "sl_buffer_applied": <float, MSO precision, > 0>,
  "take_profit_1": <float, MSO precision>,
  "take_profit_2": 0.0,
  "take_profit_3": 0.0,
  "risk_reward_ratio": 1.5,
  "position_size_lots": 0.01
}
```

## BEFORE RETURNING YOUR RESPONSE — SELF-CHECK (PROMPT V2)
Run these checks against your own output. If ANY check fails, the correct
response is a NO_TRADE with `no_trade_reason: "self_check_failed"` plus a
1-sentence explanation of which check failed, rather than a broken CANDIDATE.

If decision == "CANDIDATE":
1. Geometry — direction == LONG:
   - stop_loss < entry_price (strictly)
   - entry_price < take_profit_1 (strictly)
2. Geometry — direction == SHORT:
   - take_profit_1 < entry_price (strictly)
   - entry_price < stop_loss (strictly)
3. Precision — every price field (entry_price, stop_loss, take_profit_1,
   take_profit_2, take_profit_3, sl_buffer_applied) has exactly
   {decimal_places} decimal places, matching MSO precision. Do not
   truncate and do not pad beyond {decimal_places} decimals.
4. Non-degeneracy — entry_price != stop_loss AND entry_price != take_profit_1.
5. Buffer — sl_buffer_applied > 0 (strictly non-zero).
6. H1 POI source — h1_setup.poi_price_level falls INSIDE the bounds of
   a zone listed in the MSO's `## H1 — Structure: ...` section. It is
   NOT a price taken from `## M15 — ...`, `## D1 — ...`, or `## H4 —
   ...`, and NOT a fabricated round-number level.

If any of 1–6 fails, emit NO_TRADE with `no_trade_reason` exactly equal
to one of:
  - `wrong_side_sl`            (use this when items 1 or 2 fail)
  - `degenerate_trade_parameters` (use this when item 4 fails)
  - `self_check_failed`        (use this when item 3, 5, or 6 fails;
                                append a 1-sentence explanation naming
                                which item)
instead of a malformed CANDIDATE. These are reasons R5/R6/R7 from the
ENUMERATED NO_TRADE REASONS allow-list at the top of this prompt.

REMINDER: the COMPLETE list of legal `no_trade_reason` values is R1-R8
above (`c1_failed`, `c2_m15_opposing`, `c3_direction_mismatch`,
`no_qualifying_h1_poi`, `self_check_failed`, `wrong_side_sl`,
`degenerate_trade_parameters`, `ai_output_malformed`). Any other reason
string is a schema violation. If you are about to emit a `no_trade_reason`
that is not a literal match to one of those eight strings, the correct
action is to RECONSIDER — the answer is almost certainly CANDIDATE.

CANDIDATE response: under 600 tokens. NO_TRADE: under 300 tokens.

"""

# Module-level default for backward compatibility (gold values)
_DEFAULT_DP, _DEFAULT_VALID, _DEFAULT_INVALID = _build_precision_examples(".2f", "XAUUSD")
SYSTEM_PROMPT = (
    _SYSTEM_PROMPT_TEMPLATE
    .replace("{kz_display}", "- London Open: 07:00\u201309:30 UTC\n- NY Open: 13:00\u201315:30 UTC")
    .replace("{sl_min_display}", "$5.00")
    .replace("{decimal_places}", _DEFAULT_DP)
    .replace("{valid_examples}", _DEFAULT_VALID)
    .replace("{invalid_examples}", _DEFAULT_INVALID)
)


# ── Section 5.2 — User message builder ────────────────────────────────

_MAX_MSO_CHARS = 60_000  # ≈20 000 tokens at ~3 chars/token


def _format_tf(tf_name: str, tf_data: dict) -> str:
    """Format a single timeframe's analysis."""
    if not tf_data:
        return f"\n## {tf_name}: No data"

    parts = []
    structure = tf_data.get("structure", {})
    direction = structure.get("direction", "N/A") if structure else "N/A"
    ps = structure.get("protected_swing", {}) if structure else {}
    ps_str = f"at {ps.get('price', 0):{_PRICE_FMT}} ({ps.get('time', 'N/A')[:16]})" if ps and ps.get("price") else "none"

    parts.append(f"\n## {tf_name} — Structure: {direction}, Protected Swing: {ps_str}")

    breaks = tf_data.get("structure_events", [])
    if breaks:
        parts.append(f"  Breaks (last {min(5, len(breaks))} of {len(breaks)}):")
        for b in breaks[-5:]:
            parts.append(f"    {b.get('type','?')} {b.get('time','?')[:16]} lvl={b.get('level_broken',0):{_PRICE_FMT}} "
                       f"dir={b.get('direction','?')} disp={b.get('displacement_present',False)} "
                       f"ratio={b.get('displacement_ratio',0):.1f}")

    obs = [ob for ob in tf_data.get("order_blocks", []) if not ob.get("mitigated", False)]
    if obs:
        parts.append(f"  Unmitigated OBs ({len(obs)}):")
        for ob in obs[-5:]:
            parts.append(f"    {ob.get('type','?')} {ob.get('high',0):{_PRICE_FMT}}-{ob.get('low',0):{_PRICE_FMT}} "
                       f"body={ob.get('open',0):{_PRICE_FMT}}-{ob.get('close',0):{_PRICE_FMT}} "
                       f"evt={ob.get('causing_event_type','?')} touches={ob.get('touch_count',0)} "
                       f"({ob.get('formation_time','?')[:16]})")

    breakers = [b for b in tf_data.get("breaker_blocks", []) if not b.get("is_retested", False)]
    if breakers:
        parts.append(f"  Unretested Breaker Blocks ({len(breakers)}):")
        for bb in breakers[-5:]:
            parts.append(f"    {bb.get('direction','?')} breaker {bb.get('zone_high',0):{_PRICE_FMT}}-{bb.get('zone_low',0):{_PRICE_FMT}} "
                       f"(orig={bb.get('original_ob_direction','?')} OB, "
                       f"formed={bb.get('formation_time','?')[:16]}, "
                       f"mitigated={bb.get('mitigation_time','?')[:16]})")

    fvgs = [f for f in tf_data.get("fair_value_gaps", []) if not f.get("filled", False)]
    if fvgs:
        parts.append(f"  Unfilled FVGs ({len(fvgs)}):")
        for fvg in fvgs[-5:]:
            parts.append(f"    {fvg.get('type','?')} {fvg.get('top',0):{_PRICE_FMT}}-{fvg.get('bottom',0):{_PRICE_FMT}}")

    pd = tf_data.get("premium_discount")
    if pd:
        parts.append(f"  P/D: eq={pd.get('equilibrium_50',0):{_PRICE_FMT}} "
                   f"fib62={pd.get('fib_62',0):{_PRICE_FMT}} fib79={pd.get('fib_79',0):{_PRICE_FMT}}")

    avg = tf_data.get("avg_candle_body", 0)
    atr = tf_data.get("atr_14", 0)
    if avg or atr:
        parts.append(f"  Avg body: {avg:{_PRICE_FMT}}  ATR(14): {atr:{_PRICE_FMT}}")

    # CLV — close location value (order flow proxy, no tick data required)
    clv_current = tf_data.get("clv_current")
    clv_avg_5 = tf_data.get("clv_avg_5")
    if clv_current is not None:
        avg5_str = f"{clv_avg_5:+.2f}" if clv_avg_5 is not None else "N/A"
        parts.append(f"  CLV: {clv_current:+.2f} (avg5: {avg5_str})")

    # BVC — bulk volume classification (buy/sell pressure)
    bvc = tf_data.get("bvc_buy_fraction")
    net_flow = tf_data.get("net_flow_5")
    if bvc is not None:
        flow_dir = "buy" if bvc > 0.6 else ("sell" if bvc < 0.4 else "neutral")
        net5_str = f"{net_flow:+.0f}" if net_flow is not None else "N/A"
        parts.append(f"  Flow: {flow_dir} (BVC={bvc:.2f}, net5={net5_str})")

    # Session ATR — only populated for XAUUSD M15 (Ibikunle 2018 intraday vol)
    atr_session = tf_data.get("atr_session")
    vol_ratio = tf_data.get("session_vol_ratio")
    if atr_session is not None:
        if vol_ratio is not None:
            vol_label = "HIGH" if vol_ratio > 1.2 else ("low" if vol_ratio < 0.8 else "normal")
            parts.append(f"  Session ATR: {atr_session:{_PRICE_FMT}} ({vol_label}, {vol_ratio:.1f}x avg)")
        else:
            parts.append(f"  Session ATR: {atr_session:{_PRICE_FMT}}")

    return "\n".join(parts)


def build_static_context(market_state) -> str:
    """D1/H4 structure + session levels + liquidity pools. Unchanged within a session."""
    d = market_state.model_dump(mode="json") if hasattr(market_state, "model_dump") else market_state
    parts = []

    sl = d.get("session_levels", {})
    parts.append("## Session Levels")
    line = (f"Asian H/L: {sl.get('asian_high',0):{_PRICE_FMT}}/{sl.get('asian_low',0):{_PRICE_FMT}}  "
            f"PDH/PDL: {sl.get('pdh',0):{_PRICE_FMT}}/{sl.get('pdl',0):{_PRICE_FMT}}")
    if sl.get("london_high"):
        line += f"  London H/L: {sl['london_high']:{_PRICE_FMT}}/{sl.get('london_low',0):{_PRICE_FMT}}"
    parts.append(line)

    pools = d.get("liquidity_pools", [])
    # Exclude session_high/session_low — those change per candle (go in dynamic)
    static_pools = [p for p in pools if p.get("type") not in ("session_high", "session_low")]
    if static_pools:
        # Sort by proximity to midpoint of PDH/PDL (best available price reference)
        ref_price = (sl.get("pdh", 0) + sl.get("pdl", 0)) / 2
        if ref_price > 0:
            static_pools.sort(key=lambda p: abs(p.get("price", 0) - ref_price))
        parts.append(f"\n## Liquidity Pools ({len(static_pools)})")
        for p in static_pools[:10]:
            parts.append(f"  {p.get('type','?')}: {p.get('price',0):{_PRICE_FMT}} ({p.get('side','?')})")

    tfs = d.get("timeframes", {})
    for tf in ("D1", "H4"):
        parts.append(_format_tf(tf, tfs.get(tf, {})))

    dq = d.get("data_quality", {})
    parts.append(f"\n## Data Quality: all_TFs={dq.get('all_timeframes_complete',False)} spread_ok={dq.get('spread_normal',False)}")

    return "\n".join(parts)


def build_dynamic_context(market_state) -> str:
    """H1/M15 structure + sweeps + recent swings. Changes per candle."""
    d = market_state.model_dump(mode="json") if hasattr(market_state, "model_dump") else market_state
    parts = []

    parts.append(f"Candle: {d.get('timestamp_utc', 'N/A')}")

    sl = d.get("session_levels", {})
    if sl.get("session_high"):
        parts.append(f"Session H/L: {sl['session_high']:{_PRICE_FMT}}/{sl.get('session_low',0):{_PRICE_FMT}}")
    if sl.get("london_high"):
        parts.append(f"London H/L: {sl['london_high']:{_PRICE_FMT}}/{sl.get('london_low',0):{_PRICE_FMT}}")

    sweeps = d.get("detected_sweeps", [])
    if sweeps:
        parts.append(f"\n## Sweeps ({len(sweeps)})")
        for sw in sweeps[:5]:
            pool = sw.get('pool', {})
            parts.append(f"  {sw.get('sweep_type','?')} of {pool.get('type','?')} "
                       f"wick={sw.get('wick_extreme',0):{_PRICE_FMT}} close={sw.get('body_close',0):{_PRICE_FMT}} "
                       f"({sw.get('time','?')[:16]})")

    tfs = d.get("timeframes", {})
    for tf in ("H1", "M15"):
        parts.append(_format_tf(tf, tfs.get(tf, {})))

    m15_swings = tfs.get("M15", {}).get("swings", [])
    if m15_swings:
        parts.append(f"\n## Recent M15 Swings (last 10):")
        for s in m15_swings[-10:]:
            parts.append(f"  {s.get('type','?')} {s.get('price',0):{_PRICE_FMT}} ({s.get('time','N/A')[:16]})")

    return "\n".join(parts)


def _format_layer1(layer1: dict) -> str:
    last_trades = layer1.get("last_10_trades", [])
    if last_trades:
        trade_strs = ", ".join(
            f"{t.get('outcome', '?')} {t.get('r_multiple', '?')}R"
            for t in last_trades
        )
    else:
        trade_strs = "No trades yet"

    stats = layer1.get("rolling_stats", {})
    win_rate = stats.get("win_rate", "N/A")
    expectancy = stats.get("expectancy", "N/A")
    drawdown = stats.get("current_drawdown_pct", "N/A")

    patterns = layer1.get("active_failure_patterns", [])
    patterns_str = json.dumps(patterns) if patterns else "None"

    regime = layer1.get("current_regime", "unknown")

    return (
        f"Last 10 trades: {trade_strs}\n"
        f"Rolling stats: Win rate {win_rate}, Expectancy {expectancy}R, "
        f"Current drawdown {drawdown}%\n"
        f"Active failure patterns: {patterns_str}\n"
        f"Current regime: {regime}"
    )


def _format_layer2(layer2: dict) -> str:
    if not layer2:
        return "No compressed insights available yet."
    return yaml.dump(layer2, default_flow_style=False).strip()


def _format_layer3(layer3: list) -> str:
    if not layer3:
        return "No similar historical setups available."
    # Filter out notes-only entries
    real = [s for s in layer3 if "trade_id" in s]
    if not real:
        notes = [s.get("note", "") for s in layer3 if "note" in s]
        return notes[0] if notes else "No similar historical setups available."
    return json.dumps(real, indent=2)


def format_cross_instrument_context(
    xau_d1_direction: str,
    asian_range_info: dict | None,
    config: dict | None = None,
) -> str:
    """Format the cross-instrument + volatility context block.

    Returns an empty string if no actionable context is available, or
    if cross-instrument context is not enabled for this instrument.
    """
    ci_cfg = (config or {}).get("cross_instrument_context", {})
    if not ci_cfg.get("enabled", False):
        return ""

    # Skip if reference data is unavailable
    if xau_d1_direction == "unavailable" and asian_range_info is None:
        return ""

    parts = ["## Cross-Instrument & Volatility Context"]

    # XAUUSD D1 direction
    if xau_d1_direction != "unavailable":
        dollar_map = ci_cfg.get("dollar_direction_map", {})
        dollar_signal = dollar_map.get(xau_d1_direction, "unknown")
        parts.append(
            f"XAUUSD D1 structure: {xau_d1_direction} "
            f"(indicates dollar {dollar_signal})"
        )

    # Asian range
    if asian_range_info is not None:
        ar = asian_range_info
        parts.append(
            f"Asian session range: {ar['asian_range']:.5f} = "
            f"{ar['pct_of_adr']:.0f}% of ADR ({ar['category']})"
        )

    parts.append("")
    parts.append("DECISION GUIDANCE:")
    parts.append(
        "- If your proposed trade direction CONFLICTS with XAUUSD D1 direction "
        "(e.g., you want LONG GBPUSD but gold D1 is bearish), this is a significant "
        "macro headwind. Both instruments respond to USD flows. Require exceptionally "
        "strong H1+M15 confluence to proceed with a conflicting direction. "
        "If confluence is not exceptional, output NO_TRADE."
    )
    parts.append(
        "- If Asian range is narrow (<28% of ADR), the pre-London session built "
        "minimal liquidity. Displacement setups in narrow-range environments have "
        "historically shown 33% win rate. Require stronger-than-normal displacement "
        "quality (>2.5x average body) to proceed."
    )
    parts.append(
        "- If both signals are unfavorable (conflicting direction AND narrow Asian "
        "range), output NO_TRADE regardless of other factors."
    )

    return "\n".join(parts)


def _format_kb_context(layer1: dict, layer2: dict) -> str:
    """Format KB context for injection into the user message.

    Concise format — under 500 tokens. Key numbers and key warnings only.
    Returns empty string if no KB data available.
    """
    if not layer1 and not layer2:
        return ""

    parts = []

    # Rolling stats summary — handle both flat and nested (overall key) formats
    raw_stats = layer1.get("rolling_stats", {})
    stats = raw_stats.get("overall", raw_stats) if isinstance(raw_stats, dict) else {}
    if stats and stats.get("n", 0) > 0:
        parts.append(
            f"Stats: {stats['n']} trades, "
            f"{stats['win_rate']:.0%} WR, "
            f"{stats['expectancy']:+.2f}R exp, "
            f"PF {stats.get('profit_factor', 'N/A')}"
        )

    # Last 10 trades
    last_10 = layer1.get("last_10_trades", [])
    if last_10:
        trail = ", ".join(
            f"{'W' if t['outcome'] == 'WIN' else 'L'} {t['r_multiple']:+.1f}R"
            for t in last_10
        )
        parts.append(f"Last 10: [{trail}]")

    # Active failure patterns (cautions)
    fp = layer1.get("active_failure_patterns", [])
    if fp:
        caution_lines = []
        for desc in fp[:3]:  # Max 3 cautions to stay concise
            if isinstance(desc, dict):
                desc = desc.get("description", str(desc))
            caution_lines.append(f"- {desc}")
        if caution_lines:
            parts.append("Cautions:\n" + "\n".join(caution_lines))

    if not parts:
        return ""

    return "## System Context\n" + "\n".join(parts) + "\n\n"


def build_user_message(
    market_state: "MarketStateObject",
    kb_context: dict,
    current_time: str,
    kill_zone: str = "london",
    session_memory: str = "",
    cross_instrument_context: str = "",
    additional_context: str = "",
) -> str:
    """Build the DYNAMIC portion of the user message (changes per candle).

    Static context (D1/H4/session levels) is provided separately via
    ``build_static_context`` for prompt caching.

    *kill_zone*: ``"london"`` or ``"ny"`` — tells the PA which window is active.
    *session_memory*: prior candle evaluations from the current session (optional).
    *cross_instrument_context*: pre-formatted cross-instrument + volatility block (optional).
    """
    dynamic = build_dynamic_context(market_state)

    layer1 = kb_context.get("layer1", {}) if kb_context else {}
    layer2 = kb_context.get("layer2", {}) if kb_context else {}

    candle_time = market_state.timestamp_utc if hasattr(market_state, "timestamp_utc") else current_time

    # KB context block — concise system-wide performance context
    kb_block = _format_kb_context(layer1, layer2)

    session_block = ""
    if session_memory:
        session_block = (
            "\n## Prior Candle Assessments (this session)\n"
            "The following are your assessments of prior candles in this kill zone.\n"
            "Consider the progression: Is a setup developing across candles? "
            "Did a prior candle show a sweep or displacement that sets up the current candle? "
            "If you noted a developing pattern on a prior candle, "
            "check if the trigger has now occurred.\n\n"
            f"{session_memory}\n"
        )

    ci_block = ""
    if cross_instrument_context:
        ci_block = f"\n{cross_instrument_context}\n"

    extra_block = ""
    if additional_context:
        extra_block = f"\n{additional_context}\n"

    return f"""{kb_block}## Dynamic Market Data (H1/M15 — this candle)
{dynamic}
{session_block}{ci_block}{extra_block}
## Current Time: {current_time}
## Candle Being Evaluated: M15 close at {candle_time}

Evaluate this M15 candle for the OB Retest setup. The active kill zone is: {kill_zone}. Output your analysis as JSON."""

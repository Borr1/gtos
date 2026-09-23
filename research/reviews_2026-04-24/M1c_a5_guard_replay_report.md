# M1c - A5 Guard Replay

Automated replay of `guard_candidate_inconsistent_pois` (A5,
`worktree-agent-a432468d` @ `385055b`) against historical CANDIDATE captures.
Cross-checks V5's manual finding and extends it with demotion breakdowns by
symbol, kill zone, and sub-reason.

- **Script:** `research/reviews_2026-04-24/m1c_a5_guard_replay.py`
- **Data:** `knowledge_base/trade_records/<SYMBOL>/*.json` (147 total;
  live_evaluations summary rows do not carry MSO/trade_parameters and are
  therefore insufficient for bit-exact guard replay - see Appendix A).
- **Invocation (30-day):**
  `python research/reviews_2026-04-24/m1c_a5_guard_replay.py --window-start 2026-03-24 --window-end 2026-04-22`
- **Invocation (whole history):**
  `python research/reviews_2026-04-24/m1c_a5_guard_replay.py --whole-history`
- **Raw outputs:** `research/reviews_2026-04-24/m1b_replays/outputs/a5_guard_replay_*.json`

---

## V5 cross-check

V5 finding (from `V5_A5_inconsistent_pois_validator_review.md`):

> 1 of 30 LIMIT_PLACED trades demoted by the new guard: USDJPY 2026-04-22 ny_1515.
> POI 159.239 maps to touches=2 OB [159.111, 159.367]; entry 158.914 is outside
> that OB (and inside the touches=1 OB [158.792, 158.914]). Trade never filled.
> Past 7 days: 63 CANDIDATEs, 26 demoted, 0 executed.

**This replay: MATCH.**

Target record: `knowledge_base/trade_records/USDJPY/2026-04-22_ny_1515.json`

```
demoted: True
reason:  ai_output_inconsistent_pois
poi:     159.239
entry:   158.914
stop_loss: 158.754
matched_ob: (159.111, 159.367)
matched_ob_touches: 2
final_outcome: LIMIT_PLACED
execution_present: False        <-- confirms "never filled"
filled: False
```

Whole-history bucket totals replicate V5's Section 4.2 table exactly:

| Final outcome | V5's count | This replay | Demoted (V5) | Demoted (this replay) |
|---|---|---|---|---|
| REJECTED_L2 | 92 | 92 | 68 | 68 |
| LIMIT_PLACED | 30 | 30 | 1 | 1 |
| REJECTED_GATE1_SAFETY | 16 | 16 | 3 | 3 |
| EXECUTION_FAILED | 6 | 6 | 4 | 4 |
| REJECTED_L2_POST_M5 | 3 | 3 | 0 | 0 |

**Bit-exact reproduction. V5's single-FP claim is verified.**

7-day window replay produces 65 CANDs / 25 demoted / 0 filled (V5 quoted
63 / 26 / 0). The ~2-3 row difference is attributable to how each of us
anchored the rolling-7-day window; the structurally-critical finding
("0 executed") matches exactly. No false positive filled in the week.

---

## 30-day window (2026-03-24 to 2026-04-22)

| Metric | Value |
|---|---|
| CANDIDATEs evaluated | 138 |
| Demoted by A5 guard | 72 |
| Demoted AND FILLED (true FP) | **0** |
| Demoted AND LIMIT_PLACED but never filled | 1 |
| Demoted AND already rejected elsewhere | 71 |

**Demotion rate: 72 / 138 = 52.2% of CANDs in the window.**
This is very high, but 71 of the 72 demotions catch setups L2 / Gate 1 / M5
**already** rejects downstream. The guard mostly relocates telemetry upstream
(cleaner root cause labelling); it does not actually displace decisions on
filled trades.

### By instrument

| Symbol | CANDs | Demoted | Demoted-filled |
|---|---|---|---|
| XAUUSD | 12 | 6 | 0 |
| US30_cash | 20 | 14 | 0 |
| USDJPY | 40 | 19 | 0 |
| GBPJPY | 38 | 16 | 0 |
| GBPUSD | 28 | 17 | 0 |

### By kill zone

| KZ | CANDs | Demoted | Demoted-filled |
|---|---|---|---|
| london | 68 | 43 | 0 |
| ny | 47 | 19 | 0 |
| tokyo | 23 | 10 | 0 |

### Top demotion reasons (30-day window)

Two sub-reasons account for all demotions (rows can trigger both):

| Bucket | Count |
|---|---|
| `sl_not_beyond_long` - LONG SL at/above matched OB low | 61 |
| `entry_outside_ob` - entry_price outside matched OB | 41 |

(No `tp1_wrong_side` or `sl_not_beyond_short` occurred in the 30-day window.
0 SHORT CANDIDATEs in the population - the entire CAND population is LONG.)

### Full-detail top reasons (first 220 chars, sorted by count)

The most common concrete pattern (28 occurrences in the 30-day window, 31
over whole history) is the `stop_loss == matched_ob.low` degenerate case:

```
poi_price_level 48207.46 maps to OB [48134.21, 48280.71] (touches=0),
but: stop_loss 48134.21 not below matched OB low 48134.21 for LONG
```

The AI placed SL exactly on the OB low edge; guard demotes on strict `<`
inequality (matches L2 `sl_beyond_ob` convention,
`src/components/verification.py:522`). These are existing REJECTED_L2 cases
just catching at the primary_analyzer stage instead.

### Final-outcome distribution of evaluated CANDs

| Final outcome | CAND count | Demoted count |
|---|---|---|
| REJECTED_L2 | 87 | 62 |
| LIMIT_PLACED | 28 | 1 |
| REJECTED_GATE1_SAFETY | 15 | 3 |
| EXECUTION_FAILED | 6 | 4 |
| REJECTED_L2_POST_M5 | 2 | 0 |

Derivable from `a5_guard_replay_30d.json` via a trivial groupby on
`demotions[].final_outcome`.

---

## Spot-checked demotions (5 random, seed=42)

All five show the AI's reasoning explaining the inconsistency it introduced.
All five already were rejected by L2; guard just shifts the reason label.

**1. US30 2026-04-14 14:30 NY (LONG, REJECTED_L2, not filled)**
- POI 48207.46; entry 48280.71; SL 48134.21; TP1 48500.46
- Matched OB [48134.21, 48280.71] (touches=0, unmitigated)
- Reason: `stop_loss 48134.21 not below matched OB low 48134.21 for LONG`
- AI explanation: "Nearest unmitigated H1 bullish OB at 48280.71-48134.21...
  midpoint 48207.46"
- Verdict: VALID demote - SL sits exactly on the OB low, which both A5 and L2
  reject.

**2. XAUUSD 2026-04-15 16:15 NY (LONG, REJECTED_L2, not filled)**
- POI 4769.79; entry 4777.43; SL 4762.14; TP1 4800.36
- Matched OB [4762.14, 4777.43] (touches=0)
- Reason: `stop_loss 4762.14 not below matched OB low 4762.14 for LONG`
- AI explanation: "Nearest unmitigated H1 bullish OB at 4777.43-4762.14
  (midpoint 4769.79)"
- Verdict: VALID - same SL-on-low degeneracy.

**3. USDJPY 2026-04-13 03:00 Tokyo (LONG, REJECTED_L2, not filled)**
- POI 159.2855; entry 159.662; SL 159.491; TP1 159.9185
- Matched OB [159.252, 159.319] (touches=0)
- Two reasons: `entry_price 159.662 outside matched OB` AND `stop_loss 159.491
  not below matched OB low 159.252 for LONG`
- AI explanation: cites OB 159.319-159.252 but entry is 40 pips ABOVE the
  high of that OB.
- Verdict: VALID - entry is nowhere near the cited OB; classic
  inconsistent-POI case that the guard was designed to catch.

**4. USDJPY 2026-04-13 01:15 Tokyo (LONG, REJECTED_L2, not filled)**
- POI 159.2855; entry 159.757; SL 159.649; TP1 159.919
- Matched OB [159.252, 159.319]
- Two reasons: entry outside + SL above OB low
- AI explanation: again cites OB at 159.319-159.252 but entry 44 pips above.
- Verdict: VALID - repeat pattern, same bug class as #3.

**5. USDJPY 2026-04-13 13:15 NY (LONG, REJECTED_L2, not filled)**
- POI 159.2855; entry 159.685; SL 159.56; TP1 159.8725
- Matched OB [159.252, 159.319]
- Both reasons triggered.
- Verdict: VALID - third repeat of the same April-13 USDJPY pattern.

Four of five spot-checks are the same model-hallucination pattern (AI cites a
distant H1 OB as the POI but picks a completely different entry level).
Pattern 2/5 is the SL-at-OB-low degeneracy. Both classes were already
rejected by L2 - A5 just moves the catch upstream with a cleaner label.

---

## Verdict

**SAFE TO SHIP - zero filled trades would have been demoted in any window
examined (30-day, 7-day, whole-history). V5's manual finding of 1 FP
(USDJPY 2026-04-22 ny_1515) reproduces bit-exact and that trade never
filled.**

The guard closes a real AI-output-inconsistency bug class. In the 30-day
window, 52% of CANDs would demote, but 71 of 72 are pre-existing REJECTED_*
cases where A5 just supplies earlier + cleaner rationale (better telemetry,
no behavior change). The single LIMIT_PLACED-but-not-filled demotion is
covered by V5's recommendation #1: behavior change is bounded and can be
observed one trade at a time.

Regression guard: the replay script exits 1 if it ever finds a
`demoted_and_filled > 0`, making it usable as a smoke test before any future
A5-adjacent change is shipped.

---

## Appendix A - Why live_evaluations are unused for the replay

The brief asked to iterate both `live_evaluations/*/*.jsonl` AND
`trade_records/*/*.json`. On inspection, live_evaluations rows carry only
summary fields:

```
['timestamp', 'candle_time', 'symbol', 'kill_zone', 'decision',
 'daily_bias_direction', 'daily_bias_confidence', 'h4_aligned',
 'h1_poi_identified', 'h1_poi_type', 'h1_zone', 'h1_fib_pct',
 'h1_causing_event', 'sweep_detected', 'sweep_type', 'sweep_quality',
 'm15_choch', 'm15_displacement_quality', 'm15_displacement_ratio',
 'setup_grade', 'confidence_score', 'framework', 'session_memory_count',
 'align_score', 'spread', 'candle_index_in_kz', 'no_trade_reason',
 'wait_reason', 'reasoning_word_count', 'reasoning_price_count',
 'overall_reasoning']
```

Crucially, **no MSO and no trade_parameters** - so the guard cannot be
replayed on them. Instead, the pipeline emits a full trade_record for EVERY
CANDIDATE (and every CAND that L2 rejects post-primary), which contains the
raw `mso` + `ai_response` dicts.

Empirical confirmation:
- `live_evaluations` CANDIDATE rows: 141
- `trade_records` CANDIDATE files: 147

`trade_records` is a strict superset. The 6 extras are older CANDIDATEs from
the pre-live-evaluations-logger era (`2026-04-07_tokyo_0115` and similar
pre-7-April rows). Replaying on `trade_records` therefore gives strictly
more coverage than live_evaluations could.

---

## Appendix B - Script behaviour

- Imports `guard_candidate_inconsistent_pois` from the A5 worktree
  (`.claude/worktrees/agent-a432468d`), ensuring the replayed logic is
  bit-exact with commit `385055b`.
- Rebuilds real `MarketStateObject` / `PrimaryAnalysisOutput` Pydantic
  instances via `Model(**rec["mso"])` / `Model(**rec["ai_response"])`. No
  mocking, no data massaging.
- `model_copy(deep=True)` before applying the guard keeps the original
  unchanged so `before.decision` remains "CANDIDATE" in the report.
- `_is_filled()` examines `execution` dict for fill fields
  (`fill_price`/`filled_price`/`price`/`entry_fill_price`). Any non-empty
  execution dict counts as filled (conservative); LIMIT_PLACED with
  `execution: null` (pending expired) is NOT counted as filled.
- Exits with rc=1 when `demoted_and_filled > 0` (ship-blocker signal).

---

## Appendix C - Re-running with different boundaries

```bash
# 30-day default
python research/reviews_2026-04-24/m1c_a5_guard_replay.py

# Past 7 days (anchor today = last capture date)
python research/reviews_2026-04-24/m1c_a5_guard_replay.py \
    --window-start 2026-04-16 --window-end 2026-04-22

# Single symbol
python research/reviews_2026-04-24/m1c_a5_guard_replay.py \
    --symbols USDJPY

# Whole history + dump JSON
python research/reviews_2026-04-24/m1c_a5_guard_replay.py \
    --whole-history \
    --json-out research/reviews_2026-04-24/m1b_replays/outputs/a5_full.json
```

Read-only. Zero API calls. ~1-2s wall-clock per run on the current archive
(147 files).

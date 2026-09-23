# ADR-006 Bench-Test — EURUSD post-FA-2 sl_beyond_ob worked example

**Date:** 2026-04-26
**Branch:** `feat/sl-geometry-multi-fw`
**Goal:** Confirm that ADR-006's tolerance-tier gate + per-instrument 8-tick
floor PASSES geometry that previously FAILED L2 with the strict-`<` check
on EURUSD's 5dp tight-FX precision.

---

## Source row

Pulled from
`research/rejected_candidates_value_mining/bt_corrected_l2.jsonl`
(post-FA-2 backtest corrected L2 mining, eurusd_s5 slice).
First-line representative row:

```json
{
  "_instrument": "EURUSD",
  "timestamp_utc": "2026-03-03T07:00:00Z",
  "kill_zone": "london",
  "decision": "REJECTED_L2",
  "bucket_sub": "sl_beyond_ob",
  "direction": "SHORT",
  "entry": 1.17,
  "sl": 1.1701,
  "tp1": 1.16985,
  "l2_reason": "sl_beyond_ob: SL 1.17 is NOT above OB high 1.17 for SHORT trade"
}
```

The l2_reason shows pre-FA-2 strict-`>` check (mirror of strict-`<` for
SHORT). At 2dp display both SL and OB.high are 1.17, but the underlying
5dp-quantized geometry has SL = 1.17010 and OB.high ≥ 1.17010 (else the
strict-`>` gate would have passed). This is the canonical bug class —
EURUSD 0.25 × ATR buffer rounds to ~1 tick at 5dp, and AI emits an SL
that lands at the OB boundary instead of the intended 0.25-ATR clearance.

The l2_reason format "is NOT above OB high" is the LEGACY pre-ADR-006
phrasing. Under ADR-006 the reason becomes "does not clear OB high
1.17010 by floor 0.00008".

---

## Construction (synthetic but representative)

Reconstruct the geometry using values consistent with the row + EURUSD's
H1 ATR scale (~0.0010 across this period):

- Entry price: `1.17000` (SHORT entry, top of OB candle range)
- OB.high: `1.17010` (the boundary that triggered FAIL)
- OB.low: `1.16980`
- Pre-FA-2 SL: `1.17010` (AI emitted SL at OB boundary — buffer rounded
  to zero ticks at 5dp under the old 0.25 × ATR formula)
- TP1: `1.16985` (per the source row)

The `bt_corrected_l2.jsonl` row stores SL as 1.1701 — which at 4dp is
1.17010 and at the broker's actual 5dp tick is `1.17010` exactly. The
gate's input is the broker-quoted price.

---

## Gate semantics under ADR-006

**Pre-fix gate** (strict-`>` for SHORT):
```python
if sl > zone_high:           # 1.17010 > 1.17010 → False → FAIL
    return PASS
```

**Post-fix gate** (tolerance-tier with 8-tick floor for EURUSD/FTMO):
```python
floor = tick * floor_ticks   # 0.00001 * 8 = 0.00008
if sl >= zone_high + floor:  # under same SL=1.17010 → 1.17010 >= 1.17018
                             #   → False → FAIL (gate is correct here)
    return PASS
```

So the floor alone does NOT fix the existing row. **What fixes it is the
WIDER prompt buffer combined with the floor**: post-ADR-006 the prompt
substitutes `sl_buffer_atr_multiplier: 0.50` for EURUSD (vs the previous
hardcoded 0.25), and `sl_buffer_min_ticks: 8`.

**Engineered fix flow:**

1. AI reads the new prompt: "compute a non-zero buffer using
   `max(0.50 x H1 ATR(14), 8 x smallest tick)`"
2. With H1 ATR ≈ 0.00100, the buffer becomes
   `max(0.0005, 0.00008) = 0.0005` (50 ticks).
3. AI emits SL = OB.high + 0.0005 = 1.17010 + 0.0005 = `1.17060`.
4. New gate: `1.17060 >= 1.17010 + 0.00008` → `1.17060 >= 1.17018` →
   True → **PASS**.

---

## Bench-test execution

```python
from src.components.verification import _check_sl_beyond_ob
from src.models.market_state_models import OrderBlock
from src.models.analysis_models import (
    DailyBiasAnalysis, H1SetupAnalysis, H4AlignmentAnalysis,
    LiquiditySweepAnalysis, M15ConfirmationAnalysis,
    PrimaryAnalysisOutput, PrimaryAnalysisReasoning, TradeParameters,
)

# EURUSD config matching FTMO profile post-ADR-006
config = {
    "verification": {"sl_beyond_ob_tick_floor": 8},  # FTMO EURUSD floor
    "market": {"tick_size": 0.00001},                # 5dp
    "prompt": {"price_format": ".5f"},
    "risk": {
        "sl_buffer_atr_multiplier": 0.50,            # EURUSD override
        "sl_buffer_min_ticks": 8,
    },
}

# Reconstructed OB from the source row (boundary identical to display)
ob = OrderBlock(
    type="bearish", low=1.16980, high=1.17010,
    open=1.17005, close=1.16985,
    formation_index=10, formation_time="2026-03-03T06:00:00Z",
    causing_bos_index=11, mitigated=False, causing_event_type="BOS",
    touch_count=1,
)

# Pre-fix AI emission (SL collides with OB boundary):
analysis_pre_fix = ...trade_parameters.stop_loss=1.17010
result_pre_fix = _check_sl_beyond_ob(analysis_pre_fix, ob, None, config)
# → status = "FAIL"  (8-tick floor catches the SL == ob_high case)

# Post-fix AI emission (wider 0.50-ATR buffer):
analysis_post_fix = ...trade_parameters.stop_loss=1.17060
result_post_fix = _check_sl_beyond_ob(analysis_post_fix, ob, None, config)
# → status = "PASS"  (SL clears OB.high by 50 ticks ≫ 8-tick floor)
```

---

## Result

| Step | SL | OB.high + floor | Gate result |
|------|-----|-----------------|-------------|
| Pre-FA-2 (strict-`>`) | 1.17010 | 1.17010 (no floor) | FAIL |
| ADR-006 floor only, AI keeps 0.25-ATR | 1.17010 | 1.17018 | FAIL |
| ADR-006 + 0.50-ATR prompt buffer | **1.17060** | 1.17018 | **PASS** |

**Gate now PASSES the geometry under per-instrument 8-tick floor + wider
prompt buffer combined.** Confirmed via direct `_check_sl_beyond_ob()`
invocation in the test suite (`tests/test_sl_geometry_e2e.py` —
`test_sl_floor_clearance_passes[EURUSD]` and
`test_strict_rollback_still_passes_for_clear_sl[EURUSD]`).

The mining row alone (`sl=1.17010` under old buffer) does NOT pass the
new gate — by design: the floor alone doesn't fix bad geometry, it just
ensures the boundary case fails cleanly. The prompt-side wider buffer
is the second mechanism. **Both must work together** per the
multi-causal architecture in ADR-006 §A.

---

## Cross-reference

- Source: `research/rejected_candidates_value_mining/bt_corrected_l2.jsonl`,
  line 1 (eurusd_s5 slice)
- ADR: `.context/06_decisions/ADR-006_sl_geometry_council_2026-04-26.md`
- Implementation: `src/components/verification.py` `_check_sl_beyond_ob` +
  `_sl_beyond_floor`
- Config: `config/profiles/ftmo.yaml` EURUSD per-instrument override
- Tests: `tests/test_verification_sl_beyond_ob_tolerance.py`,
  `tests/test_sl_geometry_e2e.py`, `tests/test_dispatch_parallel_evaluation.py`

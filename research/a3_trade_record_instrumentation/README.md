# A3 — Trade Record Instrumentation (Session 39)

Infrastructure meta-finding closure for Phase 1 Track D. Adds
observability fields to the `trade_records/{SYM}/*.json` persistence path
so Phase 2 sniper re-analysis (≥6 months out) is unblocked.

**Branch:** `feat/a3-trade-record-instrumentation`
**Approval:** Non-trading-logic infrastructure (CLAUDE.md §WF-1 "Allowed without approval: Infrastructure"). Show diff before merge.
**Status:** Ready for CEO review. Do NOT merge without diff review.

---

## Why this exists

Phase 1 Track D sniper-subset analysis surfaced three persistence gaps:

1. **`target_ob_touch_count`** — only reachable via entry-price match against MSO's OB list. Fragile; silently wrong when AI cites a level outside tolerance.
2. **`m5_refined` state** — written only to `pipeline_state/m5_refinement.json`, which is **overwritten per candle**. Historical state is irretrievable.
3. **`realized_R`** — present on batch records but absent on live records (all live records have `execution: null, exit: null` because the FTMO free trial excludes the EA add-on → server-side `trade_expert=False` → retcode 10026). The fields exist in code but nothing populates them for live trades.

Without these, Phase 2 sniper re-analysis in six months will still be blocked because the instrumentation window starts from whenever instrumentation ships.

---

## Schema delta (v1.0 → v1.1)

`CAPTURE_VERSION` bumped `"1.0"` → `"1.1"`. Version stamp lives in
`record["metadata"]["capture_version"]`. Loaders MUST use `.get()` on
`record["instrumentation"]` — v1.0 records have no such block.

### New top-level block: `record["instrumentation"]`

Populated at CAND creation (`create_trade_record`) + enriched at
L2 verification (`update_verification`) + M5 refinement
(`update_m5_refinement`).

| Field | Type | Default | Populated where | Source |
|---|---|---|---|---|
| `target_ob_touch_count` | `int \| None` | `None` | `update_verification` | `VerificationResult.matched_ob.touch_count` |
| `target_ob_zone` | `dict \| None` | `None` | `update_verification` | Matched OB's `low/high/type/formation_time` |
| `m5_refined` | `bool` | `False` | `update_m5_refinement` | `m5_out["applied"]` |
| `m5_refinement_details` | `dict \| None` | `None` | `update_m5_refinement` | `m5_out["overrides"]` + `m5_result.decision` |
| `sl_source` | `str` | `"unknown"` | `create_trade_record` | Inferred from `framework` + `sl_buffer_applied` |
| `sl_buffer_applied` | `float \| None` | inherits from AI | `create_trade_record` | Aliased from `trade_parameters.sl_buffer_applied` |
| `h1_fvg_unfilled_count` | `int` | `0` | `create_trade_record` | Count of `mso.timeframes["H1"].fair_value_gaps` where `filled == False` |
| `m15_fvg_unfilled_count` | `int` | `0` | `create_trade_record` | Same for M15 |
| `h1_opp_ob_touch` | `int \| None` | `None` | `create_trade_record` | `touch_count` of nearest unmitigated H1 OB on the OPPOSING side of entry |
| `detector_version_at_eval` | `str \| None` | `None` | `create_trade_record` | `config["market_state"]["detector_version"]` |
| `kill_zone_bucket_15min` | `str` | `"{kz}_unknown"` | `create_trade_record` | `"{kz}_{HHMM}"` from `candle_time` |

### Exit block additions (`record["exit"]`)

Populated at `update_exit`. Aliases keep v1.0 fields unchanged.

| Field | Type | Source | Notes |
|---|---|---|---|
| `exit_reason` | `str` (enum) | `_canonical_exit_reason(exit_type)` | Enum values: `TP1 / TP2 / SL / BE / TIMEOUT / MANUAL / UNKNOWN` |
| `realized_R` | `float \| None` | alias for `actual_r` | Preserved when caller sets explicit `realized_R` |
| `time_in_trade_minutes` | `int \| None` | alias for `hold_time_minutes` | Same alias semantics |

Enum constants are module-level:
```python
from src.components.trade_capture import (
    EXIT_REASON_TP1, EXIT_REASON_TP2, EXIT_REASON_SL,
    EXIT_REASON_BE, EXIT_REASON_TIMEOUT, EXIT_REASON_MANUAL,
    EXIT_REASON_UNKNOWN,
)
```

### Fields populated at each lifecycle stage

```
Stage                         | Helper                    | Writes to
------------------------------+---------------------------+----------------------------
CAND production (M15 close)   | create_trade_record()     | instrumentation.{fvg_counts,
                              |                           |   h1_opp_ob_touch,
                              |                           |   sl_source, sl_buffer_applied,
                              |                           |   detector_version_at_eval,
                              |                           |   kill_zone_bucket_15min}
                              |                           | + defaults for later stages
------------------------------+---------------------------+----------------------------
L2 verification (6 checks)    | update_verification()     | instrumentation.{
                              |                           |   target_ob_touch_count,
                              |                           |   target_ob_zone}
------------------------------+---------------------------+----------------------------
M5 refinement (optional)      | update_m5_refinement()    | instrumentation.{
                              |                           |   m5_refined,
                              |                           |   m5_refinement_details}
------------------------------+---------------------------+----------------------------
Exit (_finalize_exit)         | update_exit()             | exit.{exit_reason,
                              |                           |   realized_R,
                              |                           |   time_in_trade_minutes}
                              |                           | (plus existing fields)
```

---

## Files touched

| File | Lines Δ | Purpose |
|---|---|---|
| `src/components/trade_capture.py` | +338 / −4 | CAPTURE_VERSION bump, enum constants, 5 helper fns, instrumentation block, `update_m5_refinement`, enriched `update_exit` + `update_verification` |
| `src/components/verification.py` | +7 | Expose `matched_ob` + `matched_breaker` on `VerificationResult` |
| `src/components/orchestrator.py` | +8 | Import `update_m5_refinement`; call after `refine_entry_m5` returns |
| `tests/components/test_trade_record_instrumentation.py` | +613 (new file) | 51 unit tests across 10 classes |
| `tests/replay/test_trade_record_instrumentation_replay.py` | +337 (new file) | 5 replay tests against 148 historical records |
| `research/a3_trade_record_instrumentation/PHASE_A_RECON.md` | +124 (new file) | Schema recon + source mapping |
| `research/a3_trade_record_instrumentation/README.md` | this doc | Handoff |

Total: +1,427 / −4 across 7 files, 6 commits.

---

## Test results

**Unit tests (new):** 51/51 passed. 0 failures, 0 errors.

**Replay tests (new):** 5/5 passed.
- `test_reconstruction_populates_v11_instrumentation`: **sampled=148, sane=148** — 100% of historical records produce a sane v1.1 instrumentation block.
- `test_replay_verification_populates_touch_count`: sampled=148, `with_match=116 (78%)`, `no_match=32 (22%)`.
- `test_replay_update_exit_populates_canonical_fields`: `exits_seen=0` (consistent with FTMO free-trial EA exclusion).

**Full suite (post-instrumentation):** `2050 passed, 2 skipped, 0 failed` — 0 regressions.

---

## Backward compatibility

- **v1.0 records on disk load without `KeyError`.** `instrumentation` access MUST use `.get()`.
- **v1.0 records fed into v1.1 `update_*` helpers** auto-create the `instrumentation` block on first write — the legacy record gains the field organically.
- **No existing field types or names changed.** Only additive keys + enum aliases on `exit`.
- **Loaders that don't check `capture_version`** continue to work — they just see extra fields they ignore.

Test coverage: `TestBackwardCompat` class (3 tests) in `tests/components/test_trade_record_instrumentation.py`.

---

## How Phase 2 sniper re-analysis (≥6 months out) queries this data

Once live fills begin accumulating (i.e., after CEO moves to a paid FTMO challenge with EA add-on), a sniper-subset query is:

```python
from pathlib import Path
import json

def load_sniper_candidates(base="knowledge_base/trade_records",
                          symbol="XAUUSD",
                          min_touch=1, max_touch=2,
                          detector="v2"):
    for fp in sorted(Path(base, symbol).glob("*.json")):
        r = json.loads(fp.read_text(encoding="utf-8"))
        inst = r.get("instrumentation") or {}
        touch = inst.get("target_ob_touch_count")
        if touch is None or not (min_touch <= touch <= max_touch):
            continue
        if inst.get("detector_version_at_eval") != detector:
            continue
        exit_data = r.get("exit") or {}
        yield {
            "trade_id": r["metadata"]["trade_id"],
            "kill_zone_bucket": inst.get("kill_zone_bucket_15min"),
            "m5_refined": inst.get("m5_refined"),
            "target_ob_touch_count": touch,
            "h1_opp_ob_touch": inst.get("h1_opp_ob_touch"),
            "sl_source": inst.get("sl_source"),
            "exit_reason": exit_data.get("exit_reason"),
            "realized_R": exit_data.get("realized_R"),
            "time_in_trade_minutes": exit_data.get("time_in_trade_minutes"),
        }
```

The "sniper subset" as originally defined = `target_ob_touch_count ∈ [1, 2]`
+ `m5_refined=True` + `sl_source == "ob"` (structural at OB boundary).
All three now queryable in O(1) per-record without MSO re-match.

---

## Known gaps / unresolved

1. **FTMO free-trial EA exclusion.** Live fills will not populate until CEO moves to a paid challenge. The instrumentation is ready; data accumulation is gated on broker setup, not code.
2. **No retroactive backfill.** Historical records (Jan–Apr 2026 batch + live pre-v1.1) cannot be upgraded without replaying `_count_touches` against historical H1 windows. Out of scope for A3.
3. **`sl_source` CAND-time inference only.** Post-clamp SL source (Gate 1 floor override, ATR fallback) is NOT reflected. A future iteration could add `sl_source_post_gate` if the distinction matters for Phase 2.
4. **Pending-index schema unchanged.** `_pending_records_index.json` (`trade_id → path`) is agnostic to v1.x; no migration needed.
5. **`structure_detector_shadow_logger.py:152` hardcoded `divisor=4`.** Unrelated pre-existing bug (see CLAUDE.md unresolved #4). Not touched by A3.

---

## Commit log

```
58e0b31 test(replay): A3 instrumentation validation against historical records
0c965a2 test(trade-capture): coverage for v1.1 instrumentation fields
85434b6 feat(orchestrator): wire update_m5_refinement into CAND pipeline
49cc432 feat(trade-capture): v1.1 instrumentation schema for Phase 2 sniper analysis
e92e270 recon(a3): trade record schema delta for Phase 2 sniper analysis
```

---

## CEO checklist before merge

- [ ] Skim diff: `src/components/trade_capture.py` (largest change, mostly additive helpers).
- [ ] Confirm `CAPTURE_VERSION` bump is acceptable (loader contract change is documented above).
- [ ] Confirm `exit.exit_reason` enum names acceptable (`TP1/TP2/SL/BE/TIMEOUT/MANUAL/UNKNOWN`).
- [ ] Confirm `instrumentation.sl_source` inference enum is acceptable (`ob/atr_fallback/structural/unknown`).
- [ ] Approve merge. No rolling fleet restart required — the new path only fires on NEW CANDs; open positions are unaffected. Next M15 candle boundary writes the first v1.1 record.
- [ ] Update CLAUDE.md "What is working" with a bullet for v1.1 instrumentation (per the staleness rule — same commit as merge).

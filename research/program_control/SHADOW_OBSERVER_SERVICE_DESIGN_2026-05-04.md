# Shadow Observer Service Design - 2026-05-04

**Status:** `IMPLEMENTED_SHADOW_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

The owner identified that "tested but not live-orchestrated" instruments need live-time follow data, not later replay reconstruction. This service captures that lane without changing the live trading stack.

`scripts/run_shadow_observer.py` is a separate read-only process. It reads MT5 candles/ticks, computes an as-of MSO snapshot, and appends `strategy_follow_evaluation_v1` rows. It does not call the AI API, does not run canary, does not call Databento, does not invoke permission gates, and does not place or manage orders.

## Active Registry

Registry: `config/shadow_observer_registry.yaml`

Active no-outcome MSO observers:

| Observer | Broker symbol | Config template | Family | Status |
| --- | --- | --- | --- | --- |
| `eurusd_6e_mso_shadow_v1` | `EURUSD` | `EURUSD` | `EURUSD/6E` | `ACTIVE_MSO_SHADOW` |
| `ger40_tier2_mso_shadow_v1` | `GER30` | `GER40` | `GER40 tier-2` | `ACTIVE_MSO_SHADOW` |
| `uk100_tier2_mso_shadow_v1` | `UK100` | `UK100` | `UK100 tier-2` | `ACTIVE_MSO_SHADOW` |

Disabled or blocked by design:

| Observer | Family | Boundary |
| --- | --- | --- |
| `spx500_es_prereg_required_v1` | `ES/MES` | pre-registration required before any strategy/outcome cohort |
| `uko_usd_cl_context_only_v1` | `CL` | context/control only |
| `zn_rates_context_only_v1` | `ZN` | context/control only |
| `vix_vxm_context_only_v1` | `VIX/VXM` | context/control only |
| `nzdusd_historical_excluded_v1` | `NZDUSD` | killed historical lane, do not resurrect without owner decision |

## Output Contract

Primary rows:

- `shadow_logs/strategy_follow_evaluations.jsonl`
- schema `strategy_follow_evaluation_v1`
- `source_file=shadow_observer_mso_no_ai`
- `evaluation_stage=SHADOW_OBSERVER_MSO_NO_AI`
- `ai_status=NOT_CALLED_BY_SHADOW_OBSERVER`
- `no_leak_status=NO_AI_NO_EXECUTION_NO_POST_OUTCOME_FIELDS`
- `promotion_verdict=NO_PROMOTION_VERDICT`
- `source_run_id` identifies the observer process/session that wrote the row
- `dedupe_key` is `observer_id|decision_time_utc|SHADOW_OBSERVER_MSO_NO_AI`, so downstream tools can deduplicate without collapsing different symbols, sources, days, or sessions

Status rows:

- `shadow_logs/shadow_observer_status.jsonl`
- schema `shadow_observer_status_v1`
- one row per active observer per cycle with emitted/skipped/error lifecycle
- includes `observer_run_id` for source/session traceability

State:

- `pipeline_state/shadow_observer_state.json`
- deduplicates by `observer_id` and M15 candle close so one candle is not emitted twice.
- throttles repeated outside-KZ/duplicate/status-only rows so the continuous service does not spam append-only logs every poll.

Runtime lock:

- `knowledge_base/meta/.shadow_observer.lock`
- prevents accidental duplicate continuous observer processes.

## Safety Contract

Hard forbidden path for active registry entries:

- `ai_api_call`
- `canary_call`
- `order_send`
- `execution_engine`
- `permission_gate`
- `outcome_opening`

The module-level separation is intentional. `src/research_infra/shadow_observer.py` must not import primary analyzer, execution, permissions, or canary code.

## Evidence Boundary

These rows are forward shadow context. They are not broker actual-R, not a live strategy promotion, and not an outcome-opening step. `EURUSD/6E` is allowed to accumulate MSO context now, but ES/MES remains behind preregistration because the deep-dive explicitly warned that opening outcomes before registration contaminates validation.

## Verification

Implemented with:

- `config/shadow_observer_registry.yaml`
- `src/research_infra/shadow_observer.py`
- `scripts/run_shadow_observer.py`
- `tests/test_shadow_observer.py`

Monitoring hooks:

- `scripts/verify_forward_capture_readiness.py` checks `shadow_logs/shadow_observer_status.jsonl`
- `scripts/_live_monitor_iter.py` tracks `shadow_observer_status.jsonl` freshness
- `logs/shadow_observer.log` records every poll cycle; status JSONL rows are throttled for repeated skip states.

Targeted tests:

- `python -m py_compile src/research_infra/forward_capture.py src/research_infra/shadow_observer.py scripts/run_shadow_observer.py scripts/verify_forward_capture_readiness.py scripts/_live_monitor_iter.py`
- `python -m pytest tests/test_shadow_observer.py tests/test_forward_capture_shadow_loggers.py tests/test_verify_forward_capture_readiness.py -q -p no:cacheprovider`

If pytest cannot create its temp directory on the trading box, record the ACL failure separately from code correctness and run the manual no-AI assertion script used in the session notes.

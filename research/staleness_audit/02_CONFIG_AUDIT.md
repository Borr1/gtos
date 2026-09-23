# Config Staleness Audit — Monday FTMO Paid Challenge Pre-Deploy

**Auditor:** STALENESS SPECIALIST agent (Opus 4.7 max-effort)
**Scope:** Every key in `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, `config/profiles/ftmo.yaml`. Plus launch-path verification and worktree-pending-merge check.
**Date:** 2026-04-25 UTC
**HEAD audited:** `1b2d4e8` (one commit past LIVE_STATE.md `13b75e7` — fully regen'd before audit)
**Scope of authority:** This audit only flags config staleness. Trading-logic / risk-MC / FTMO-rule decisions remain CEO domain.

---

## 1. Executive summary

- **75 distinct config keys/sub-keys audited** across base + 2 profiles.
- **0 HIGH-severity Monday-blockers** found in the active production config (`agent_config.yaml` + `redacted_account.yaml`).
- **2 MEDIUM-severity items** — both are documentation/staleness, not behavior bugs.
- **3 LOW-severity orphaned-key cleanups** (cosmetic; no behavioral effect).
- **2 worktree branches with config additions still un-merged** (`feat/cross-instrument-correlation-gate` + `feat/wyckoff-regime-classifier-shadow`); these are documented as not-yet-merged in CLAUDE.md and the brief — verified well-formed and reasonable for staging.
- **Launch path confirmed:** both `start_all.bat:62-66` and `scripts/watchdog.ps1:258` invoke `--profile redacted_account`. **No Sunday merge accidentally changed these.**
- **`config/profiles/ftmo.yaml` confirmed STALE** per A10 audit (still 2% / cap=2; Monday intent is 1% / cap=4 via redacted_account profile). Per the brief and A10's own recommendation: leave ftmo.yaml stale; production uses `--profile redacted_account`. **Verified ftmo.yaml NOT edited Sunday** (`git log` shows last touch is `dc4cec2`, T2.8 architecture, session 33).
- **Confidence: HIGH.** The Monday-launch surface (base config + FN profile + launch scripts) is internally consistent with documented intent.

---

## 2. Per-key verdict — base `config/agent_config.yaml`

Legend: `OK` = current value matches documented intent + key is read by code; `ORPHAN` = key is in YAML but no code reads it (cosmetic); `STALE` = key needs update; `NEW` = added recently; `LEGACY` = older key still present, kept for compatibility.

### `market.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `market.symbol` | `XAUUSD` | OK | Default; per-instrument override drives actual symbol. |
| `market.kill_zones.london.start_utc` | `07:00` | OK | Read at orchestrator:205 via `core_end_utc` deep-merge. |
| `market.kill_zones.london.end_utc` | `10:30` | OK | |
| `market.kill_zones.london.core_end_utc` | `09:30` | OK | Used in `_is_extended_*` (orchestrator.py:2172). |
| `market.kill_zones.ny.start_utc` | `13:00` | OK | |
| `market.kill_zones.ny.end_utc` | `15:30` | OK | Per-instrument overrides (XAUUSD=17:00) override this. |
| `market.session_start_utc` | `07:00` | LEGACY | Only `src/utils/time_utils.py::is_in_session_window` reads this; that function is not called from production code. Same for `session_end_utc`. Kept for backwards-compat. |
| `market.session_timeout_utc` | `12:00` | ORPHAN | Not referenced anywhere in `src/`. |
| `market.asian_session_start_utc` | `00:00` | LEGACY | `time_utils::is_asian_session` only; orphan in production path. |
| `market.asian_session_end_utc` | `07:00` | LEGACY | Same. |

### `risk.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `risk.risk_per_trade_pct` | `2.0` | OK | Base default; FN profile overrides to 1.0 (FX) / 0.5 (XAUUSD); FN US30/US30_cash explicit 1.0. |
| `risk.max_daily_loss_pct` | `4.0` | OK | A12 audit: 1pp safety margin from FTMO 5% rule; pinned. |
| `risk.max_weekly_loss_pct` | `4.0` | ORPHAN | Only referenced as a `PROTECTED_PARAMETERS` entry in `adaptive_review.py:48` — but `AdaptiveReviewSystem` is NOT wired into orchestrator/run_agent (only imported by tests). No production gate enforces a weekly loss cap. **CEO awareness item, not a Monday blocker.** |
| `risk.max_monthly_loss_pct` | `8.0` | ORPHAN | Same — only PROTECTED_PARAMETERS entry, no production gate. |
| `risk.max_concurrent` | `null` | OK | Per design (T2.8 session 33): `null` derives `floor(max_daily_loss/risk_per_trade)`. FN profile pins explicit `4`. Read at `permissions.py` + `concurrent_tracker.py`. NOTE: `LIVE_STATE.md` shows `_missing_` for this key — **generator script bug** (`scripts/generate_live_state.py:286` treats `None` identically to "absent key"). Not a config issue; flag for `generate_live_state.py` cleanup. |
| `risk.min_rr` | `1.5` | OK | Phase 1 validated, p=0.021. |
| `risk.tp1_close_pct` | `100` | OK | execution.py:757; `100` = full close at TP1 (Phase 1 design). |
| `risk.max_spread_cents` | `100` | OK | Per-instrument overrides. |
| `risk.sl_buffer_dollars` | `1.20` | OK | XAUUSD default; per-instrument overrides scale appropriately. |
| `risk.sl_absolute_min` | `5.0` | OK | XAUUSD default. |

### `drawdown_reduction.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `drawdown_reduction.threshold` | `0.08` | OK | H29 MC-validated 4.3× DD>10% reduction. |
| `drawdown_reduction.reduced_risk_pct` | `0.5` | OK | Base; FN profile overrides to `0.25` (proportional to 1.0% baseline). |
| `drawdown_reduction.contract_size` | `100` | ORPHAN | `DrawdownManager.__init__` does not read this key. The actual `contract_size` used by execution.py:1005 is `risk.contract_size` (base 100, per-instrument overrides). The key here is dead — comment says "default" but no code reads `drawdown_reduction.contract_size`. **LOW-severity cleanup.** |

### `filters.*` / `gate1.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `filters.max_gap_pct` | `1.5` | OK | verification.py reads. |
| `gate1.touch_count_reject_threshold` | `2` | OK | A19 reviewer-pass REJECTED LOOSEN_TO_3; commit `daabff8` keeps at 2 for Monday (matches CLAUDE.md task brief). Per-symbol regime-stratified analysis showed touch=2 reverses in H2-2026; baseline founding evidence (Touch-1 72.7% / Touch-2+ 31.5%) holds. |
| `gate1.ob_retest_sl_exception` | `true` | OK | permissions.py:391. |
| `gate1.ob_retest_sl_min_buffer_atr` | `0.5` | OK | Apr 16 sweep margin calibration; matches CLAUDE.md and brief. |
| `gate1.sl_liquidity_cluster_enabled` | `false` | OK | Ships disabled; permissions.py:612 reads. |
| `gate1.sl_liquidity_cluster_margin_atr` | `0.5` | OK | Mirrors ob_retest_sl_min_buffer_atr. |

### `model_a.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `model_a.bias_timeframes` | `["D1", "H4"]` | ORPHAN | No code reads this key; bias TFs are hardcoded across primary_analyzer + verification. **LOW-severity cleanup; cosmetic.** |
| `model_a.setup_timeframe` | `"H1"` | ORPHAN | Same — H1 is hardcoded. |
| `model_a.entry_timeframe` | `"M15"` | ORPHAN | Same — M15 hardcoded. |
| `model_a.enabled_frameworks` | `["ob_retest", "fvg_fill", "breaker_re_entry"]` | OK | **Sunday 3-framework merge confirmed in main** (commits `1340f56` fvg_fill + `64d05b8` breaker_re_entry + `d031f55` keep). Read by primary_analyzer, verification, pre_ai_gates. Matches brief expectation exactly. |
| `model_a.ote_zone_fib_top` | `0.618` | ORPHAN | market_state.py:851 hardcodes `0.618`. **LOW-severity cleanup.** |
| `model_a.ote_zone_fib_bottom` | `0.786` | ORPHAN | market_state.py:852 hardcodes `0.786`. Same. |
| `model_a.displacement_min_ratio` | `1.5` | OK | verification.py:201 reads. |
| `model_a.equal_level_tolerance` | `2.50` | OK | data_ingestion.py:64. |

### `ai.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `ai.billing_mode` | `"api"` | OK | orchestrator.py reads. |
| `ai.primary_model` | `"claude-sonnet-4-6"` | OK | Per Memory: Sonnet beats Opus on MSO gate (CR 38% vs 19%, WR 69.6% vs 60.9%, 4.4× cheaper). |
| `ai.primary_effort` | `"max"` | OK | P2A-3 validated. |
| `ai.debate_model` | `"claude-sonnet-4-6"` | LEGACY | Read in `debate.py:74` but Component 3B (Bull/Bear Debate) is documented PAUSED in CLAUDE.md (`code exists, not wired`). No production caller. |
| `ai.postmortem_model` | `"claude-sonnet-4-6"` | ORPHAN | No code reads this key. PostmortemAgent class doesn't exist. |
| `ai.review_model` | `"claude-sonnet-4-6"` | LEGACY | Read in `adaptive_review.py:110` but AdaptiveReviewSystem not wired in production. |
| `ai.debate_round2_enabled` | `true` | LEGACY | Read in `debate.py:77`; debate not wired. |
| `ai.max_api_retries` | `1` | OK | primary_analyzer reads. |
| `ai.api_timeout_seconds` | `60` | OK | Required for `effort=max`. |

### Top-level scalars
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `session_memory_enabled` | `false` | OK | T2b proven: 55% CR suppression. orchestrator reads. |
| `confidence_filter_mode` | `"shadow"` | OK | orchestrator reads. |
| `cross_instrument_context_disabled_for` | `[GBPUSD]` | OK | Read at orchestrator:330 + 1344, primary_analyzer:168. |

### `retrieval.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `retrieval.embedding_model` | `"all-MiniLM-L6-v2"` | ORPHAN | No code reads this. KnowledgeBase has `find_similar_setups` defined but `retrieval.*` keys are not consumed. |
| `retrieval.lancedb_path` | `"knowledge_base/vectordb"` | ORPHAN | Same. |
| `retrieval.similar_setups_top_k` | `5` | ORPHAN | Same. |
| `retrieval.min_similarity_threshold` | `0.50` | ORPHAN | Same. |

### `data.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `data.lookback.{D1,H4,H1,M15}` | `30, 80, 168, 672` | ORPHAN | No `lookback` key read in `src/`. Bar-fetch counts are hardcoded in data_ingestion. |
| `data.swing_detection_min_bars.*` | `2,2,2,2` | ORPHAN | Hardcoded `2` in market_state. |
| `data.fvg_min_gap.{D1,H4,H1,M15}` | `5.0, 3.0, 2.0, 1.0` | OK | market_state.py reads (per-TF). Per-instrument overrides exist for all 8 instruments. |

### `adaptation.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `adaptation.tier2_deviation_threshold` | `0.15` | LEGACY | Read by `AdaptiveReviewSystem` (not wired). |
| `adaptation.tier2_min_samples` | `20` | LEGACY | Same. |
| `adaptation.tier3_min_samples` | `50` | LEGACY | Same. |
| `adaptation.tier4_min_total_trades` | `200` | ORPHAN | Not even read by AdaptiveReviewSystem. |
| `adaptation.tier4_max_affected_pct` | `0.20` | ORPHAN | Same. |
| `adaptation.tier4_min_expectancy_improvement` | `0.10` | ORPHAN | Same. |
| `adaptation.rollback_review_trades` | `30` | ORPHAN | Same. |
| `adaptation.max_modifications_per_50_trades` | `1` | LEGACY | Read by AdaptiveReviewSystem (not wired). |

### `m5_refinement.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `m5_refinement.enabled` | `true` | OK | m5_refinement.py:431 reads. |
| `m5_refinement.sl_floor` | `10.0` | OK | XAUUSD default; per-instrument overrides correct. |
| `m5_refinement.quality_gate` | `[HIGH, MEDIUM]` | OK | m5_refinement.py:524. |
| `m5_refinement.candle_lookback` | `36` | OK | orchestrator.py:2053. |
| `m5_refinement.model` | `"claude-sonnet-4-6"` | OK | m5_refinement.py:477. |
| `m5_refinement.effort` | `"max"` | OK | m5_refinement.py:479. |
| `m5_refinement.max_tokens` | `500` | OK | m5_refinement.py:478. |
| `m5_refinement.timeout_seconds` | `60` | OK | m5_refinement.py:480. |

### `verification.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `verification.enabled` | `true` | OK | |
| `verification.ob_price_tolerance_pct` | `0.002` | OK | verification.py reads. |
| `verification.strict_zone_check` | `false` | OK | |
| `verification.log_warnings` | `true` | OK | |

### `trade_capture.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `trade_capture.{enabled,base_path,save_mso,save_prompt,save_rejected}` | (5 keys) | OK | trade_capture.py reads all. |

### `monitoring.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `monitoring.dashboard_port` | `8080` | ORPHAN | No code reads this. |
| `monitoring.obsidian_export_enabled` | `false` | ORPHAN | No code reads this. |
| `monitoring.obsidian_vault_path` | `""` | ORPHAN | No code reads this. |
| `monitoring.alert_email` | `""` | ORPHAN | No code reads this. |

### `budget.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `budget.monthly_cap_usd` | `50.0` | ORPHAN-NARRATIVE | No code reads this; the actual hard cap is the Anthropic balance ($50-60, auto-reload disabled per Memory `project_anthropic_billing_auto_reload_disabled.md`). The yaml field is documentation only — kept because LIVE_STATE.md surfaces it. |
| `budget.cost_warning_threshold_usd` | `20.0` | ORPHAN-NARRATIVE | Same — informational only. |
| `budget.cost_critical_threshold_usd` | `30.0` | ORPHAN-NARRATIVE | Same. |

### `prompt.*` / `confidence.*`
All read correctly by `primary_analyzer.py` (zone_width_max, ob_buffer, price_format) and `confidence_scorer.py` (price_regex, price_range). OK.

### `economic_calendar.*` / `news_filter.*`
All read by `news_calendar.py` + `economic_calendar.py`. OK. `news_filter.enabled: false` matches CLAUDE.md doctrine for pre-Monday challenge.

### `correlation_groups.*`
5 groups defined (EUR_GBP, AUD_NZD, US_INDICES, PRECIOUS_METALS, JPY_CROSSES). Read by `portfolio_risk.py`. OK. (The 04_CORRELATION_INFRA_AUDIT report covers the cross-instrument correlation-gate analysis separately.)

### `deployment.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `deployment.phase` | `3` | OK | Gate 0 in permissions.py reads. |
| `deployment.mt5_account` | `"demo"` | OK | |
| `deployment.{mt5_server,mt5_login,mt5_password}` | empty | OK | Loaded from .env at runtime. |

### `pre_ai_gates.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `pre_ai_gates.h1_poi_availability_enabled` | `true` | OK | **Multi-framework-aware per A16 (commit `68f7a4b`)** — confirmed in `pre_ai_gates.py` (lines 137-167): `_FRAMEWORK_POI_CHECKS` registry covers ob_retest, fvg_fill, breaker_re_entry, plus legacy alias `breaker_retest`. Skip only when EVERY enabled framework has zero POIs. Fail-safe (unknown name → run AI). Comment block in agent_config.yaml lines 290-301 accurately documents this. Matches brief expectation. |

### `market_state.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `market_state.detector_version` | `v2_shadow` | OK | Session 38 F3 GO. v1 drives production; v2 dual-computed for divergence logging. CLAUDE.md item #4. |

### `shadow_loggers.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `shadow_loggers.d1_bias_lag_logger.enabled` | `true` | OK | orchestrator reads. |
| `shadow_loggers.d1_bias_lag_logger.alert_threshold_consecutive` | `20` | OK | |
| `shadow_loggers.dumb_baseline_logger.enabled` | `true` | OK | **Already merged** (`1b2d4e8`). orchestrator.py:630 reads. |
| `shadow_loggers.dumb_baseline_logger.look_back_h1_candles` | `24` | OK | |
| `shadow_loggers.dumb_baseline_logger.debug_log_enabled` | `false` | OK | |
| `shadow_loggers.regime_classifier_logger.*` | NOT IN MAIN | NEW | On `feat/wyckoff-regime-classifier-shadow` (`9b593d5`); 14 lines added; reasonable defaults (`enabled: true`, `lookback_h4_candles: 20`). |

### `canary.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `canary.subprocess_timeout_s` | `420` | OK | Manifest count = 75 fixtures. Required floor: ceil(75 × 4.5) + 30 = 368s. Configured 420s = 52s spare headroom. **Invariant test PASSES** (`test_canary_timeout_invariant.py`). Matches A15 spec exactly. |

### `heartbeat.*`
| Key | Value | Verdict | Notes |
|---|---|---|---|
| `heartbeat.flatten_enabled` | `false` | OK | Ships disabled per CLAUDE.md doctrine. |
| `heartbeat.write_interval_seconds` | `30` | OK | heartbeat_monitor.py reads. |
| `heartbeat.miss_threshold` | `3` | OK | |
| `heartbeat.telegram_countdown_seconds` | `30` | OK | |
| `heartbeat.telegram_throttle_minutes` | `60` | OK | |

### `instruments.*` (per-symbol)
8 instruments declared (XAUUSD, GBPUSD, EURUSD, NAS100, XAGUSD, USDJPY, US30_cash, GBPJPY, NZDUSD). Live = 5 (XAUUSD, USDJPY, US30_cash, GBPJPY, GBPUSD-observer per `trading_enabled: false`). All per-instrument overrides (kill_zones, risk, model_a, data, m5_refinement, prompt, confidence) verified consistent with comments and brief expectations. EURUSD/NAS100/XAGUSD/NZDUSD are template entries; not active.

---

## 3. Per-key verdict — `config/profiles/redacted_account.yaml` (ACTIVE production profile)

| Key | Value | Verdict | Notes |
|---|---|---|---|
| `profile_name` | `redacted_account` | OK | |
| `risk.risk_per_trade_pct` | `1.0` | OK | Matches Monday intent (1% FX). |
| `risk.max_daily_loss_pct` | `4.0` | OK | A12 audit. |
| `risk.max_concurrent` | `4` | OK | 4% / 1% = 4. Pinned per T2.8 design. |
| `drawdown_reduction.threshold` | `0.08` | OK | Unchanged from base. |
| `drawdown_reduction.reduced_risk_pct` | `0.25` | OK | Half of new 1.0% baseline (proportional to FTMO's 0.5). **A17 spec said 0.25; verified.** |
| `instruments.XAUUSD.risk.risk_per_trade_pct` | `0.5` | OK | Phase 4 Chairman C3 regime-response sizing-down. |
| `instruments.US30.risk.risk_per_trade_pct` | `1.0` | OK | A17 explicit override (commit `d031f55`); both `US30` and `US30_cash` keys present + correct. |
| `instruments.US30_cash.risk.risk_per_trade_pct` | `1.0` | OK | Same. |
| `instruments.US30_cash.market.mt5_symbol` | (commented out) | OK | Intentional — FTMO-trial path keeps default `US30.cash` from base. Comment block `49-87` documents the restoration trigger. |

**Verdict:** `redacted_account.yaml` is **internally consistent** with Monday challenge intent. No staleness.

---

## 4. Per-key verdict — `config/profiles/ftmo.yaml` (NOT active for Monday)

| Key | Value | Verdict | Notes |
|---|---|---|---|
| `profile_name` | `ftmo` | OK | |
| `risk.risk_per_trade_pct` | `2.0` | STALE-ACKNOWLEDGED | Per A10 audit + brief: stale (Monday intent is 1%), but NOT used by Monday launch path. **Verified ftmo.yaml has NOT been edited Sunday** — last commit touching it is `dc4cec2` (T2.8, session 33). Brief instruction: leave stale. |
| `risk.max_daily_loss_pct` | `4.0` | OK | Same as base. |
| `risk.max_concurrent` | `2` | STALE-ACKNOWLEDGED | 4 / 2 = 2 (FTMO 2% formula). Stale vs Monday intent of 4. Same disposition. |
| `drawdown_reduction.threshold` | `0.08` | OK | |
| `drawdown_reduction.reduced_risk_pct` | `0.5` | OK | Half of 1.0% if used; mirrors FTMO 2.0 → 0.5 (originally 25% defensive posture). |

**Decision:** ftmo.yaml is shelved. The brief explicitly directed: "VERIFY ftmo.yaml has NOT been 'fixed' Sunday (would change behavior)". Confirmed: NOT edited.

---

## 5. Launch-path verification

| Path | File | Line | Profile flag | Status |
|---|---|---|---|---|
| Daily 08:01 scheduled task | `start_all.bat` | 62-66 | `--profile redacted_account` (5 instruments) | CONFIRMED |
| Watchdog respawn | `scripts/watchdog.ps1` | 258 | `--profile redacted_account` | CONFIRMED |

Both spawned via `wmic process call create` / `Process.Start` with `--profile redacted_account`. Sunday merges did NOT change either file (last touch: `start_all.bat` predates Sunday; `watchdog.ps1` last touched `f1654f3` for tick-capture daemon, not profile).

---

## 6. Worktree-pending config additions (NOT YET IN MAIN)

### `feat/cross-instrument-correlation-gate` (HEAD `edd5b4e`)
Adds 3 keys under `risk.*`:
```yaml
risk:
  cross_instrument_correlation_enabled: true
  cross_instrument_correlation_threshold: 0.4
  cross_instrument_correlation_min_positions: 2
```
- Threshold `0.4`: matches brief spec; reasonable noise floor (correlations between random crossed pairs ~0.2-0.3).
- min_positions `2`: matches brief spec; HALVE at 2, REJECT floor at 3 (min_positions + 1).
- **Caveat:** this branch is rooted on an OLDER main and contains stale reverts (e.g. it would re-stale `enabled_frameworks` to `["ob_retest"]` only and remove the touch_count comment block). **Cannot fast-forward merge** — requires interactive rebase / cherry-pick of the ADD-3-keys-only diff. (Not a config staleness issue; merge-mechanics issue for the branch landing PR.)

### `feat/wyckoff-regime-classifier-shadow` (HEAD `9b593d5`)
Adds 14 lines under `shadow_loggers.*`:
```yaml
shadow_loggers:
  regime_classifier_logger:
    enabled: true
    lookback_h4_candles: 20
```
- Branch is well-structured; +1917 lines total (1 config block + classifier source + tests + correlation script).
- Defaults reasonable (`enabled: true` for shadow-only; `lookback_h4_candles: 20 ≈ 3.3 trading days`).
- **No conflicts with main.**

---

## 7. Severity classification

### HIGH (Monday-blocker)
**None.** The base config + FN profile + launch path are internally consistent with Monday intent.

### MEDIUM (action recommended, not blocker)
1. **`max_weekly_loss_pct` and `max_monthly_loss_pct` enforce nothing.** They live in `adaptive_review.py::PROTECTED_PARAMETERS` only; AdaptiveReviewSystem isn't wired. The system has no weekly or monthly loss guard. FTMO challenge has only daily + total drawdown rules, so this isn't a rule-compliance gap, but it's surprising for any reader looking at risk.* and assuming a weekly/monthly guard exists. **Recommendation:** Either add a stub guard (Component 4 path) or annotate the config keys as "informational; FTMO uses daily + total only". Not Monday-blocking.

2. **`generate_live_state.py` mislabels `max_concurrent: null` as `_missing_`.** Line 286 treats Python `None` (from YAML `null`) identically to absent key. Cosmetic — LIVE_STATE.md table says "_missing_" for a key that IS set deliberately. **Recommendation:** Patch `dig()` to distinguish; non-critical.

### LOW (orphan-key cleanup; cosmetic only)
3. **Orphan keys with no code reader (consider removing or annotating):**
   - `market.session_timeout_utc`
   - `drawdown_reduction.contract_size`
   - `model_a.bias_timeframes`, `model_a.setup_timeframe`, `model_a.entry_timeframe`
   - `model_a.ote_zone_fib_top`, `model_a.ote_zone_fib_bottom` (hardcoded in market_state.py)
   - `retrieval.embedding_model`, `retrieval.lancedb_path`, `retrieval.similar_setups_top_k`, `retrieval.min_similarity_threshold`
   - `data.lookback.*`, `data.swing_detection_min_bars.*` (hardcoded)
   - `adaptation.tier4_*`, `adaptation.rollback_review_trades` (not even read by adaptive_review)
   - `monitoring.{dashboard_port,obsidian_*,alert_email}`
   - `budget.{monthly_cap_usd,cost_warning_threshold_usd,cost_critical_threshold_usd}` (informational; the real cap is Anthropic balance)
   - `ai.postmortem_model`
   - `ai.{debate_model,review_model,debate_round2_enabled}` (legacy; Component 3B paused, AdaptiveReviewSystem not wired)

   **Recommendation:** Mark these with a `# orphan / informational only` comment so future edits don't assume they have effect. Do NOT remove (low risk; some may be activated later, e.g. retrieval.* if LanceDB lookup is wired in).

---

## 8. Top 3 Monday-blocker config issues

**None.** Highest-impact items for awareness:

1. (MEDIUM) `max_weekly_loss_pct` / `max_monthly_loss_pct` defined but unenforced. FTMO challenge doesn't require these, so not a rule violation, but the keys imply protection that doesn't exist.
2. (MEDIUM) `LIVE_STATE.md` displays `_missing_` for `risk.max_concurrent` — generator-script display bug, not config; gives a false impression of staleness when read out of context.
3. (LOW) ~12 orphan/legacy keys never read by `src/`. Cosmetic risk: a future edit may presume these have effect and "tune" them with no observable behavior change.

---

## 9. Recommended diff (specific YAML changes)

**No changes required for Monday launch.** All Monday-relevant keys verified correct.

If CEO wants post-Monday hygiene:

```yaml
# config/agent_config.yaml — add orphan markers (do NOT remove keys)

market:
  session_timeout_utc: "12:00"  # ORPHAN — not read in src/
  asian_session_start_utc: "00:00"  # LEGACY — only time_utils.is_asian_session, not wired
  asian_session_end_utc: "07:00"  # LEGACY — same

drawdown_reduction:
  contract_size: 100  # ORPHAN — execution.py reads risk.contract_size, not this

model_a:
  bias_timeframes: ["D1", "H4"]  # ORPHAN — hardcoded in primary_analyzer/verification
  setup_timeframe: "H1"           # ORPHAN — hardcoded H1
  entry_timeframe: "M15"          # ORPHAN — hardcoded M15
  ote_zone_fib_top: 0.618         # ORPHAN — hardcoded in market_state.py:851
  ote_zone_fib_bottom: 0.786      # ORPHAN — hardcoded in market_state.py:852

retrieval:                         # ORPHAN BLOCK — KnowledgeBase.find_similar_setups not wired
  embedding_model: "all-MiniLM-L6-v2"
  ...

# adaptation.* — LEGACY block (AdaptiveReviewSystem class exists but not wired into run_agent.py)
# monitoring.* — ORPHAN BLOCK
# budget.* — ORPHAN BLOCK (informational; real cap is Anthropic balance)

ai:
  postmortem_model: "claude-sonnet-4-6"  # ORPHAN — no PostmortemAgent class
  debate_model: "claude-sonnet-4-6"       # LEGACY — Component 3B paused
  review_model: "claude-sonnet-4-6"       # LEGACY — AdaptiveReviewSystem not wired
  debate_round2_enabled: true             # LEGACY — same
```

Also patch `scripts/generate_live_state.py:285-286`:

```python
# Distinguish "absent key" from "explicit null" so LIVE_STATE.md
# stops mislabeling deliberate `max_concurrent: null` as `_missing_`.
val_present = self._key_exists(cfg, key)  # walk path, return True at last segment if key in dict
if not val_present:
    val_str = "_missing_"
elif val is None:
    val_str = "`null` (derive at runtime)"
else:
    val_str = f"`{val}`"
```

---

## 10. Confidence rating

**HIGH** for the Monday launch path. Every key the launch surface depends on has been:
1. Cross-referenced to a code reader in `src/`,
2. Compared to documented intent in CLAUDE.md and the audit brief,
3. Verified against the active profile (`redacted_account.yaml`) and active launch scripts.

The orphan/legacy findings are documentation hygiene, not behavior bugs. ftmo.yaml's known staleness is acknowledged and the brief specifically instructed to leave it.

Risk vector: The cross-instrument-correlation-gate branch's older base means a future merge will need a clean cherry-pick — flagging as a merge-mechanics item, not a config staleness item.

---

*End of audit.*

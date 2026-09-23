# PRE_REPLAY_BRIEF_20260708T091930Z_V177_B7_SIGNED_DAILY_LOSS_RELEASE_ALIAS_REPAIR

## Control

- Fable batch: B7 package replay conversion / scheduler-order-risk transfer.
- Dependency status: B0/B1/B2/B5 done, B3/B4/B6 done-with-label, B7 partial, B8 open.
- Scope: targeted XAUUSD 2026-06-04..2026-06-05 repaired_package_conversion_v3 proof slice.
- Broker/live/final authority: closed. Local replay/package authority: full.
- Running replay before patch: none.

## Latest Completed Run

- V176 prefix: `BROAD_LIVE_AS_IF_REPLAY_V176_B7_REDERIVABLE_ROUTER_REFUSAL_FALSE_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- Summary rows: 1130 candidates, 184 scorecards, 7 orders, 3 trades, 1126 missed, 27 buckets.
- V176 behavior from trade ledger: net/gross/final R `0.18335355 / 0.48352934 / 0.48352934`, W/L/F `2/1/0`, risk pct sum `0.75`.
- Bounded interpretation: targeted repair proof slice only; not full reservoir conversion evidence.
- Cost/source safety: broker-calibrated replay cost authority, live broker false, final selection false.

## Incorporated Findings

- Planck: the 08:45 guarded-market fallback row is a legitimate thesis-geometry guard (`fallback_entry_adverse_drift_r=1.240920703 > 0.75R`), not off-config fallback drift. Do not loosen it; add clarity later if needed.
- Franklin: the V175 17:45 and 18:15 winners were pre-finalizer selected in V176 but rejected by `same_symbol_daily_loss_lockout_after_closed_trade` after the newly released 14:30 loss. Not fillability, expiry, headroom, broker/live/final, or lifecycle exposure.
- Bernoulli: remaining positive missed R includes fill_realism, package_authority, selector_materialization, and lifecycle/daily-loss buckets. This patch targets the daily-loss/package-authority root only.

## Patch Batch

Same-root B7 repair: signed package authority aliases are present, but risk finalizer consumers can still read stale top-level false fields.

Files:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Repairs:
- Correctness: source-bound-only stale signed-authority failures are revalidated from current package source-bound aliases.
- Correctness: the timewarp runtime adapter re-stamps signed package authority after canonical alias normalization, instead of mutating a signed hash payload.
- Correctness: signed-executable daily-loss release prefers `package_new_entry_authority_package_replay_order_executable_candidate_use_allowed` before stale top-level `package_replay_order_executable_candidate_use_allowed`.
- Test/proof: focused tests cover fill-floor daily-loss release, router-refusal daily-loss release, signed-only daily-loss release with top-level stale false plus signed alias true, unresolved fill-floor hard block, and order materialization authority.

Focused proof before replay:
- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "package_cooldown_release_daily_loss_lockout_requires_explicit_flag or package_fill_floor_authority_daily_loss_release_is_narrow_replay_path or package_router_refusal_daily_loss_release_is_narrow_replay_path or order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority or order_materialization_preserves_router_refusal_fill_floor_false or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed" -q --tb=short`
- Result before replay: `5 passed`.

## Expected Measurable Effect

- Candidate -> scorecard: neutral.
- Scorecard -> order: may increase if signed package rows previously blocked by stale daily-loss alias now remain selected.
- Order -> fill: expected recovery of V176 late pre-finalizer selected rows if no downstream causal guard blocks.
- Missed positive R: expected decrease around `+0.67909739R` if the V175 17:45 and 18:15 winners transfer again.
- Missed negative R: may change if signed daily-loss release also admits valid losers; do not suppress by outcome.
- Trade count: likely increases from 3 if late rows fill.
- Net/gross/final R: expected improvement versus V176 if both late rows transfer; exact result must come from replay.
- W/L/F: expected additional winners if same rows transfer; any added losers must be reported.
- Cost-refused/source-gap execution: must remain 0.
- Risk distribution: released rows should be risk-bearing, likely reduced risk unless full-risk ladder independently qualifies.

## Success / Failure Criteria

- Helped: 17:45 and/or 18:15 rows no longer end as stale `same_symbol_daily_loss_lockout_after_closed_trade` finalizer rejects when signed package authority and broker-cost/source/fillability are valid.
- Failed: rows remain daily-loss rejects despite signed authority alias true and no cost/source/fill hard veto.
- Exposed next blocker: rows move to a later explicit order, lifecycle, fillability, geometry, or exit reason. That reason becomes the next B7 batch.
- Not acceptable: positive-by-suppression, loosening broker-cost REFUSED/source-gap execution, or loosening guarded-market geometry.

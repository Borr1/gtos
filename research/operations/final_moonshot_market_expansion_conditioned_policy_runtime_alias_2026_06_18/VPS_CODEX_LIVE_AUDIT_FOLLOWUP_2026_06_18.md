# VPS Codex Live Audit Follow-Up

Date: 2026-06-18
Branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
Base before this follow-up: `d1812efc3d29933717426197bab558532723602a`

## Purpose

This packet preserves the VPS-side live audit and repair context produced after direct FTMO/redacted_account
activation. It should be read together with:

- `VPS_CODEX_RESEARCH_CONTEXT_PACKET_2026_06_18.md`
- `VPS_BROKER_PROFILE_PARITY_AUDIT_2026_06_18.json`

Do not use Mac bridge assumptions for broker parity. This VPS has direct MT5 access to both brokers.

## Live State Observed

The live supervisor was running both books and the monitor:

- Supervisor PID observed: `2812`
- FTMO book workers observed: shim `7788`, child `3848`
- redacted_account book workers observed: shim `1900`, child `9500`
- Monitor workers observed: shim `8712`, child `1096`

After the guarded test pause/reload, the scheduled task `GTOS_W7_BookSupervisor` restarted the stack:

- Supervisor PID observed after restart: `5784`
- FTMO book workers after restart: shim `9728`, child `1180`
- redacted_account book workers after restart: shim `5068`, child `9724`
- Monitor workers after restart: shim `1352`, child `5952`
- Heartbeats after restart:
  - FTMO `pipeline_state/ultimate_book/operator_profile/heartbeat.json`, healthy, PID `1180`,
    timestamp `2026-06-18T16:32:46.633479+00:00`
  - redacted_account `pipeline_state/ultimate_book/redacted_account_live_bee34003/heartbeat.json`, healthy, PID `9724`,
    timestamp `2026-06-18T16:32:48.762419+00:00`

Latest live launcher rows before the follow-up patch showed:

- `include_candidate_book=true`
- `include_market_expansion_book=true`
- `market_expansion_policy=positive_weighted12_after_swap`
- `kelly_lite=true`
- `kelly_running_count=true`
- `stress_derisk=true`
- `derisk_mode=smooth`
- `drop_w7_symbols=true`
- `metals_confluence_gate=true`

redacted_account remains a reduced live book: direct profile support is `36/46`; unsupported active canonical
symbols are `AVAUSD`, `CORN_c`, `COTTON_c`, `DASHUSD`, `XAGAUD`, `XAGEUR`, `XAUAUD`, `XAUEUR`, `XPDUSD`,
and `XTZUSD`.

## Active Gold Trade Monitoring

Both active XAU positions were exact original placements with persisted trade records:

- FTMO ticket `160183955`, `W7:metal_session`, long `0.39`, entry `4227.70`, SL `4216.70`, TP `0.0`.
- redacted_account ticket `246849001`, `W7:metal_session`, long `0.40`, entry `4227.84`, SL `4216.80`, TP `0.0`.

Policy: `metal_session_reversion` maps to `trailing_runner`, trigger `0.6R`, trail gap `0.5R`, no broker TP,
time stop `24` M15 bars.

Observed R path during this audit:

- Around `16:09 UTC`: both accounts were positive but below trigger, about `+0.45R`.
- Around `16:12-16:14 UTC`: both accounts retraced from about `+0.27R` to about `+0.08R`.
- Around `16:19 UTC`: FTMO about `-0.385R`, redacted_account about `-0.382R`.
- Around `16:22 UTC`: FTMO about `-0.479R`, redacted_account about `-0.477R`.
- Direct terminal snapshot at `2026-06-18T16:33:57Z`:
  - FTMO ticket `160183955`: current `4222.70`, profit `-195.00`, about `-0.4545R`, trail trigger not reached.
  - redacted_account ticket `246849001`: current `4222.83`, profit `-200.40`, about `-0.4538R`, trail trigger not reached.

Conclusion: no trailing action was missed because the `0.6R` trigger was not reached. Both positions still
had broker SL protection and remained dependent on live management plus broker SL.

## Auditor Findings Converted Into Repairs

1. Recordless adopted positions were not durable across restarts.
   - Repair: `book_owner.py` now persists reconstructed native-policy trade records when an orphan position is
     adopted from `W7:<sleeve>` identity and no record exists.
   - Live effect after restart: FTMO `159993636` and `160080305`, and redacted_account `246763216`, received durable
     reconstructed records.

2. A no-tick placement skip could consume the decision bar.
   - Repair: `book_owner.py` now marks `bar_consumable=false` for `no_tick_transient`, so the launcher retries
     the same decision bar instead of permanently skipping it.

3. D1 market expansion used only `XAUUSD` as the launcher reference.
   - Repair: D1 now uses `["XAUUSD", "BTCUSD"]`, matching the existing H4 multi-reference pattern. This prevents
     frozen XAU weekend/holiday state from suppressing D1 crypto decisions.

4. `shadow_logs/slippage.jsonl` was an LFS pointer with live JSON rows appended.
   - Repair: `slippage_shadow_logger.py` detects an LFS pointer destination by first line and redirects live
     appends to `slippage_runtime.jsonl` in the same directory. The original pointer file is no longer further
     corrupted by live appends.

5. Atomic runtime halt blocked risk-reducing management.
   - Repair: new entries/order sends remain blocked under halt, but position-reducing requests are allowed.
     SL modification under halt is allowed only when it tightens or restores protection; SL loosening remains
     blocked. TP modification is allowed because it does not increase stop-loss risk.
   - Hardening: a request cannot bypass halt merely by carrying a `position` field. The request must match an
     existing broker ticket, be opposite-side, and not exceed current broker volume.

6. Open-risk computation failed open.
   - Repair: when broker open-position access exists and position risk cannot be priced, `_open_risk_pct()`
     returns the gross cap instead of `0.0`, causing new-entry admission to fail closed.

7. Smooth max-DD derisk still allowed entries near the wall.
   - Repair: `GovernorLimits` now has `max_dd_entry_block_pct`; live config sets
     `ultimate_book_max_dd_entry_block_pct: 0.09`, blocking new entries before the 10% prop-fatal wall while
     leaving open-position breach/flatten management separate.

8. Stress-derisk failed neutral on real broker history read failure.
   - Repair: if the raw real MT5 module exists but closed-book deal history cannot be read, stress derisk now
     falls back to maximum reactive derisk (`consecutive_loss_days=2`, `trailing_neg_frac=1.0`, multiplier `0.60`)
     rather than no derisk. Mocks/no raw MT5 module remain neutral for tests.

9. redacted_account reduced breadth was not visible in per-cycle telemetry.
   - Repair: `book_engine.py` now records broker-profile generation telemetry:
     active spec count, active symbol slots, supported slots, unsupported slot count, unsupported unique symbols,
     and capped skip rows. `book_owner.py` attaches that under `bridge.broker_profile_generation` for launcher logs.

10. Broker lifecycle capture stopped at entry.
    - Repair: `execution.py` now emits observation-only runtime lifecycle rows for `close_position_result` and
      `sltp_modify_result` when the existing broker lifecycle capture log is enabled.

## Remaining Limitations

- Market-expansion expectancy remains replay/MC evidence, not broker-real future PnL.
- The incremental market-expansion lift is small compared with the candidate-book lift. Active positive12 package:
  monthly `5.09%`, Sharpe `0.28419`; expansion adds about `+0.121%` monthly and `+0.006782` Sharpe versus the
  candidate reference.
- redacted_account must be scored as reduced breadth (`36/46`) until unsupported contracts are directly available there.
- Broker cost/session/swap authority remains partially static-profile dependent; live broker-posted drift needs
  recurring direct MT5 capture.
- Cross-account concentration is monitored/alerted but not yet a hard shared gate across independent account-local
  workers.
- Rollback must protect open positions first: flatten or verify management/SL protection before disabling the book.

## Verification Run In This Follow-Up

Focused and package-level checks run before live reload:

- `python -m py_compile` on edited ultimate-book, execution, slippage, and runtime-halt modules: passed.
- `pytest tests/ultimate_book/test_book_owner.py tests/ultimate_book/test_launcher.py tests/ultimate_book/test_book_engine.py tests/ultimate_book/test_governor_baseline.py tests/ultimate_book/test_stress_derisk.py tests/test_slippage_shadow_logger.py tests/test_runtime_control_atomic_halt.py -q`: `135 passed`.
- `python research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/verify_market_expansion_conditioned_policy_runtime_alias.py`: `ok=true`, `issue_count=0`.
- `pytest tests/ultimate_book/test_market_expansion_runtime_generator.py -q`: `10 passed`.
- Full market-expansion ultimate-book slice: `53 passed`.
- Activation-adjacent regression block: `44 passed`.
- Route artifact audit: `ok=true`.
- Final post-hardening check: `pytest tests/test_runtime_control_atomic_halt.py -q`: `9 passed`.
- Final static check: `git diff --check`: passed.

Filesystem-guarded pytest runs while the live supervisor was active produced passing test bodies but guard failures
because live heartbeats/high-water files changed during the session. Clean reruns were performed with the supervisor
paused; the live stack was restarted afterward and healthy heartbeats were observed.

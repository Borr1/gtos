# STEP-7c SRC FOLD — exact cutover spec (owner-reviewed; the last mile before the flip)

> Status: **STAGED-READY, NOT merged into src.** Everything upstream is done + tested + default-off
> (deploy module, runtime bridge, dual adapter with the curated-27 maps + contract-size follower
> sizer, config Steps 5+6). This file is the precise, reviewed change set to fold the book into the
> production decision/order path. It is deliberately not auto-applied: it edits the 15k-line live
> runtime + adds the live broker interface, so it pairs with the owner's go-live review and the
> MT5Interface reconciliation against the INSTALLED MetaTrader5 build (5.0.5735 on this VPS).
> Merging it default-off is INERT (the triple-gate + halt flag still gate every order).

## Integration map (verified file:line on deploy-live)
- Template wrapper: `src/components/gtos_vnext_runtime.py:15187` `evaluate_vnext_selector_v4_admission`.
- Bridge to fold: route `ultimate_book_runtime_bridge.py:136` `evaluate_vnext_ultimate_book_admission`
  (config keys = `ultimate_book_*` DEFAULT_CONFIG lines 57-71; returns `realized_units` only when the
  triple-gate passes AND the broad selector is clear, else `would_units` shadow projection).
- Order path: `src/components/execution.py` `ExecutionEngine.open_trade(risk_pct_override=...)` (2613);
  risk consumed at 2804-2867; limit fill calls open_trade at 5532; order send + halt guard at 5602.
- Broker ABC: `src/mt5/mt5_interface.py:61` `MT5Interface` (13 abstract methods; OrderResult.success ==
  retcode 10009; `MAGIC_NUMBER = 20260401`).
- Halt guard: `src/safety/runtime_halt.py:241` `enforce_runtime_not_halted` — already enforced at every
  ExecutionEngine order entry; the fold inherits it (no new guard needed).

## The change set (default-off, fail-closed)
1. **Make the deploy module + bridge importable from src.** Copy (do not move — route keeps originals)
   `ultimate_book_live_package.py` + `ultimate_book_runtime_bridge.py` to `src/components/` (or add the
   route dir to the runtime import path). Verify `import ultimate_book_runtime_bridge` pulls ZERO heavy
   deps on the admission path (parity asserts are lazy; confirm with the existing import-safety test).
2. **Add the wrapper** in `gtos_vnext_runtime.py`, mirroring selector_v4:
   ```python
   def evaluate_vnext_ultimate_book_admission(*, config, intents, governor_state, account="A", limits=DEFAULT_LIMITS):
       return _ultimate_book_bridge(config=config, intents=intents, governor_state=governor_state, account=account, limits=limits)
   ```
   Call it in the decision pipeline right after the selector_v4 admission. Default-off => returns
   shadow `would_units` only (live-vs-replay parity telemetry); `realized_units` stays empty.
3. **Route realized_units -> execution (the cutover).** When `decision.runtime_effect_now` is True (all
   3 gates + broad-selector-clear), for each realized unit call
   `open_trade(risk_pct_override=unit.risk_pct_per_trade, ...)`. This is the only behavior-changing line;
   it is reached only post-flip. Add the shadow log mirroring `replacement_monitoring_log_path`.
4. **Promote the live broker transport into `src/mt5/`.** Implement an `MT5Interface` per LOCAL terminal
   using the in-process `MetaTrader5` package (NOT the dev bridge). Map each ABC method to the verified
   live API: `connect`->`mt5.initialize(path=,login=,password=redacted
   `get_tick`->`symbol_info_tick`; `get_candles`->`copy_rates_from_pos`; `get_positions`->
   `positions_get` filtered by `MAGIC_NUMBER`; `get_account_balance/equity`->`account_info`;
   `order_send`->`mt5.order_send`; `get_history_deals`->`history_deals_get`. Wrap the two terminals in
   the DualMT5Adapter (FTMO primary + redacted_account follower; the curated-27 maps + `follower_volume_for`
   already handle name/contract translation). Keep `NullBridgeAdapter` the default so default config =
   no connect / no orders. **Reconcile every method signature + retcode against the installed build
   (5.0.5735) with a read-only probe before the flip.**
5. **Config keys** already added (Step 6, all `ultimate_book_*` default false).
6. **Tests:** mirror `tests/test_selector_v4.py` -> `tests/test_ultimate_book_admission_runtime.py`:
   triple-gate states (all-off => shadow only, empty realized), replacement-invariant (broad selector
   still apply_to_execution => fail-closed), realized->risk_pct routing, halt-guard blocks order send.

## Acceptance before the flip
- Full suite green (current 195) + the new admission-runtime tests.
- `GOLIVE_preflight_verify.py --require-broad-selector-off` exit 0 (currently passing).
- Read-only dual-adapter `startup_self_check` green on the two live terminals (FTMO primary, clocks UTC).
- A SHADOW run produces live-vs-replay parity rows with all gates OFF (no orders) for >= 1 session.
- Then, and only then, on explicit owner GO + Step-9 authority sign-off: flip the 3 gates, remove the
  halt flag, start FTMO at 1.25% half-Kelly (follower stays down until parity confirms).

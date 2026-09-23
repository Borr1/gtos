# W7 LIVE ENGINE — BUILD PLAN (code-verified, adversarially corrected)

Source: 10-agent build-spec workflow [RAN against .venv-gtos]. Goal: ship the validated W7 edge live
on FTMO, default-off behind the triple-gate, then flip. New package `src/components/ultimate_book/`.

## CRITICAL CORRECTION (verifier R1, [RAN]) — the live-order path
- The "plain trade_params" route is REFUTED: `open_trade` blocks it at `execution.py:2683-2689`
  (profit-harvest support gate, BEFORE emv4) because `profit_harvest_mfe_capture_v4_enabled:true` +
  `require_vnext_dynamic_policy:true` (`agent_config.yaml:670-671`). A plain book order returns None
  with no order while the book reports "sized" → FALSE-GREEN.
- **The ONLY live-order path: the FULL V4 route** — set `gtos_vnext_dynamic_policy_applied=True` + a
  supported dynamic policy (`momentum_exhaustion`, whose profit-harvest params resolve from config
  defaults) + emit ALL 10 emv4 packet families incl. the broker-real prop-firm headroom snapshot
  (<900s, requested_risk_pct≤max_allowed). This (`execution_packets.py`) is MANDATORY before any flip.
- Do NOT relax `profit_harvest_*`/emv4 flags (shared with the moonshot path → live-behavior change).

## Modules (src/components/ultimate_book/)
- VENDORED pure (parity-tested vs ROUTE): `primitives.py` (atr14/autocorr/vol_ratio/exit_state_d/Bar),
  `admission.py` (=ultimate_book_live_package: registries/TradeIntent/SizedUnit/Governor/admit_and_size),
  `bridge.py` (=ultimate_book_runtime_bridge), `substrate_state.py` (build_states/cell_coords — NO 30MB
  map needed; frozen predicates), `volume_profile.py`.
- Impure seams: `bar_provider.py` (live OHLC→list[Bar], warmups, ETH M1→H4), `governor_state.py`
  (GovernorState from equity + persisted high_water + start-of-day anchor + open_risk).
- Sleeves (exact tags): `sleeves/metals.py` (metals_core/softband/ob_micro — XAUUSD/XAGUSD),
  `sleeves/crypto.py` (crypto — BTCUSD/ETHUSD), `sleeves/energy_agri.py` (energy_agri — USOIL/UKOIL),
  `sleeves/index_jpy.py` (idxrev SPX500/UK100/JP225/GER40/US30_cash; fx_jpy/fx_jpy_ny GBPJPY/USDJPY),
  `sleeves/substrate.py`, `sleeves/volprofile.py`, `sleeves/registry.py`.
- Engine: `book_engine.py` (run sleeves→intents→admit_and_size→route), `shared_book_state.py`
  (RISKIEST: cross-symbol file-locked GovernorState + 4% gross aggregation; SizedUnit has no
  symbol/dir/stop → re-join to TradeIntents, place n_trades orders), `order_router.py` (FULL V4 route),
  `execution_packets.py` (the 10 V4 packets incl. prop-firm headroom).

## Edits to existing src (default-off, exception-isolated, else-branch byte-identical)
- `orchestrator.py:~685` lazy engine handle; `~7081` insert `_process_vnext_ultimate_book_candidates`
  fork (gates-first `return False`; whole body try/except). Mirrors broader_origin fork.
- `execution.py`: accepts the book trade_params via the V4 route (no core edit; the route supplies the
  dynamic-policy + profit-harvest + emv4 packets).
- Config: `ultimate_book_*` block already staged default-off; flip order enabled→apply→live_activation.

## Build order (tradeable subset first, then complete)
0. Vendor pure layer + numeric-parity test (T1).
1. bar_provider + governor_state (+ persistence round-trip).
2. Tractable sleeves: metals, crypto, energy_agri, idxrev (pure H4) + per-sleeve intent-parity (T2).
3. book_engine + shared_book_state + order_router via the FULL V4 route + execution_packets;
   orchestrator seam default-off; emv4+open_trade admission test (T5) proving a real allow.
4. Shadow → timewarp book-parity (T3/T4) proving live==replay → FLIP tractable subset.
5. Harder sleeves: fx_jpy/ny (M15), substrate (210-warmup port), vp_euidx (M1 feed + daily rebuild).
6. (done in 3 now) full V4 packets. 7. clean_4 leadlag (deferred, not in W7 book).

## Riskiest: shared_book_state (cross-symbol sizing vs per-symbol execution; alpha-order 4% gross-cap
starvation drops highest-conviction metals on high-breadth days — surface to owner). Off-surface EV
gaps: metals EUR/AUD crosses, DASH, CORN/COTTON, FRA40/EU50/US2000 (book included them; live 24-surface
under-trades until added — but FTMO HAS them, so a data-coverage reconcile, not a hard block).

Tests T1–T8 + TimewarpBarFeed harness. All [RAN] anchors: 11 sleeves known (include_clean3); sizing
end-to-end; emv4 plain=allow/0 but open_trade blocks plain at :2689; full-V4 route required.

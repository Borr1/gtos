# GO-LIVE SEQUENCE (prep — not executed)

Context: THIS Mac = dev/research surface. Live runs on a **VPS** connected to FTMO. Deploy the
`clean_3` book (finalized by the unleash wave) at **growth-optimal sizing (~1.5%/unit)** as a
STANDALONE REPLACEMENT of the proven-losing broad selector. The flip is deliberate, staged, and
gated on broker/runtime authority — nothing here is executed without explicit owner go.

## Phase 0 — Finalize the STRONGEST book (unleash/de-conservatism wave) [in progress]
Lock the deploy book + growth-optimal sizing + un-stale'd EVs (un-cap winners, tick-measured fills,
runner horizon, reinstated sleeves, confluence-Kelly router). Then this sequence deploys that, not
the fear-distilled 0.75% version.

## Phase A — In-our-control config (this Mac, staged, DEFAULT-OFF until go)
1. **Disable the broad losing selector** — `config/agent_config.yaml` L740-742: set `selector_v4_apply_to_execution: false` (and the scheduler equivalent). This is the −0.25R/fill loser; go-live is a REPLACEMENT, not an augmentation.
2. **Add an `ultimate_book_*` config block** behind the repo's triple-gate (`enabled AND apply_to_execution AND live_activation_allowed`), all default-off.
3. **Runtime bridge**: `ultimate_book_live_package.py` → execution, mirroring `evaluate_vnext_selector_v4_admission`; sizing/governor/allocation from the deploy book (growth-optimal ~1.5%, vol-matched, fail-closed governor: soft −3% daily stop, max-DD de-risk band, 4% gross cap, outer circuit breaker).

## Phase B — Deployment package for the VPS
- **Package**: runtime + `ultimate_book_live_package.py` + deploy-book registry + MT5/bridge client + config; pinned deps (numpy etc.).
- **VPS provisioning**: process manager (systemd/docker), MT5↔FTMO connection (bridge or EA), env/secrets, NTP time-sync.
- **Monitoring/alerting**: live-vs-replay parity ledger (drift → de-risk), daily-DD watch, governor circuit-breaker, owner alerts, kill-switch (halt file + `size_cap=0`).
- **Runbook**: start/stop, rollback, incident response, daily reconciliation.

## Phase C — Broker/runtime authority (THE REAL BLOCKER — owner domain)
Hard-halt forensic reconciliation, V3-vs-live gap audit, dual-broker audit, production-return dossier; FTMO credentials/connection provisioned on the VPS. This — not the strategy — is what gates the live flip.

## Phase D — GO (deliberate, staged)
1. Start on the VPS at small size on the 2 challenge accounts; parity-monitor live-vs-replay for a few days.
2. Scale to growth-optimal (~1.5%) on live-parity confirmation.
3. First payout → fund the scaling plan (3rd account, fleet).

## What I can prep NOW (this Mac) vs what needs owner/broker
- PREP NOW: Phase A staged config (default-off), Phase B package + runbook + monitoring scaffolding + deployment scripts.
- NOT executed without explicit go: the live config flip, the VPS push, the broker connection (Phase C), the live flip (Phase D).

## Owner decisions
1. **Aggression dial**: 1.25% extra-safe / **1.5% recommended (growth-optimal)** / 2.0% max-aggression.
2. Authorize the Phase A config flip when ready.
3. Drive the Phase C broker/runtime authority work — the actual gate.

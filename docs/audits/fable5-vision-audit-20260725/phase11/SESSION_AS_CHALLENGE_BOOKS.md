# Session AS — the live-activation dossiers and the fleet map (wave 11, B1500–B1549)

> **REWRITTEN 2026-07-30 before launch.** The first version of this commission built
> "challenge-account" packages. Borhen then clarified the account model and the framing
> dissolved: there are **three accounts total — the two LIVE ones (FTMO + redacted_account, on the
> VPS terminals) and one inactive FTMO held as the RESERVE**. His words: *"the live accounts
> are the 2 ftmo and funded next accounts and i expect pushing live to those accounts and
> activating directly on them … i accept activating the sleeves there."* The 5-sleeve
> expansion was **executed by the orchestrator the same hour** (both books now run
> `crypto,energy_agri,sub_xvol_pullback,fx_jpy,sub_mid_dn_revert`, tfs `[16388, 15]` —
> receipt `../phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md`). What remains for this
> session is below.

Read first: `WAVE_11_WORKING_AGREEMENT.md`, the expansion receipt above,
`phase8/OWNER_DECISION_QUEUE.md` (decided-since block), `phase10/POPULATION_RULE_DECISION.md`.
Owner authority: Borhen's 2026-07-30 approvals, quoted in the receipt. Standing directives
apply (judgment; build-don't-refute; Workflow opt-in).

## Work orders

**AS-1 — The live 5-sleeve book, monitored like it deserves.**
The two added sleeves are armed on explicit owner risk acceptance, not on passed gates. Build
the monitoring that makes that honest: per-sleeve live-fill telemetry from the runtime packets
(fills, R, carry, hold time per sleeve per account), the stop conditions AS-1 was always going
to define (the evidence that takes `fx_jpy` or `sub_mid_dn_revert` back OFF — N stop-outs, R
drawdown, or a carry surprise vs AD's measured basis), and one operator page (model:
`phase4/CANARY_OPERATOR_PAGE.md`) covering the FIVE-sleeve book on both accounts. Wire it
read-only; the orchestrator carries anything host-side.

**AS-2 — The `mx_btcusd` + `sub_xvol` exit-contract activation dossier.**
The next two live changes are CONTRACT changes, not tag changes: `mx_btcusd` activates only on
the repaired `target_5R` contract (its admission's own terms — the truncated live contract is
−0.141 R/day), and `sub_xvol_pullback`'s exit upgrade to `target_4R` (+1.157 R/day frontier)
changes an ARMED sleeve's spec. AQ is building the time-stop repair. Your job: the activation
dossier that sits on top — per-change: exact spec diff, H1/R2 membership answer for every
touched file (if any touched file is contract-bound, say plainly that landing it ends the
parked B7.5 campaign option, and route that single question to the owner), test plan, token
implications (none expected — specs are code, not config; verify), rollback, and the
recent-fold sizing basis for `mx_btcusd` per the ratified population rule. Coordinate with
AQ's branch; do not duplicate its repair.

**AS-3 — The replay fleet map (unchanged from the first commission).**
One executable document: every banked-but-unrun measurement, each with driver, machine-hours,
memory class (H3: sealed-engine replays 6–15 GB, never parallel; walkforward drivers light),
and the verdict it moves — ordered by verdict-value per machine-hour. Known members: the
exit-geometry contract packages for AD's top cells; the `bridge_ftmo_deep_h4` fetch
(orchestrator executes); the FVG family full-sample gate once AP's transfer lands; hour-01
members AQ does not cover; the four M15 time-stop sleeves; the RESERVE-account activation
plan (the inactive FTMO — what evidence gates its activation, per the owner's "after a while
when tested on the 2"). This map is what the next waves are scheduled from.

## Done means

Result doc + receipts under `phase11/receipts/`, blocks B1500–B1549, scoped A/B green vs the
zero baseline, handoff list. Never touch the VPS; never run broker-capable scripts; never
edit `config/agent_config.yaml` or `config/profiles/redacted_account.yaml`; dossiers arm nothing by
themselves.

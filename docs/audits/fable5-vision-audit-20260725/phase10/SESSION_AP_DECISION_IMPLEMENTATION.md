# Session AP — the decision queue, implemented (wave 10, blocks B1350–B1399)

## Authority

Borhen, 2026-07-30: **"yes proceed with all make an opus session that does the implementation
and you supervise and review"** — given immediately after the orchestrator's report enumerating
`phase8/OWNER_DECISION_QUEUE.md`. That is a blanket ratification of **each queue item's own
written recommendation**. Your job is to implement those recommendations exactly — not to
re-litigate them, and not to exceed them. Where a recommendation says "not yet", the deliverable
is the recording and the routing, not the thing itself.

Standing owner directives (binding): use your own judgment — this commission is a brief, not a
script; build/improve/fix, never refute-and-stop; you have explicit owner opt-in for the
Workflow tool (multi-agent verification is the standard for anything load-bearing).

Read first: `phase8/OWNER_DECISION_QUEUE.md` (whole file, including the decided-since block),
`WAVE_10_WORKING_AGREEMENT.md`, CLAUDE.md §3 (H1: membership check before ANY edit under
`src/`), and the wave-9/10 result docs for anything you cite.

## Hard rules

- **Never touch the VPS.** OD-AI-2's host-side arming is the ORCHESTRATOR's, in flight now.
  Anything you produce that needs host action goes in your result doc as a handoff.
- **Never edit `config/agent_config.yaml`** (token digest; R2-bound). Never run a
  broker-capable script (run_book.py, run_agent.py, fn_smoke_trade.py, mt5_preflight.py,
  dual_broker_execution_follower.py, flatten/emergency scripts, .tools/monitor_books.py).
- Trial ledger: append-only, merge-by-union; declare new looks BEFORE computing gates (AL §6.3).
- Population sensitivity: AN's rule is undecided until merged+ratified — publish anything
  population-sensitive on BOTH `era_class == RECORDED` and `decidable`.
- Blocks `B1350–B1399` in `IMPLEMENTATION_STATE.md`. Scoped `pytest_failset.py scope` A/B on
  everything you touch; the committed baseline is ZERO — any red is yours.

## Work orders (per-item, from the queue's own recommendations)

**AP-1 — Record the three pure decisions (OD-AI-3, OD-AI-5, OD-AI-7).**
Annotate the queue (decided-since block) and write one decision record:
- OD-AI-3: **not added — on the gates, not the carry.** Route the residual per the item: ensure
  repair-queue rows exist for `fx_jpy` → AD §4.8 meta-label entry filter and
  `sub_mid_dn_revert` → entry-side repair, so the estate machine carries them forward.
- OD-AI-5: **registry weight stays 0.025** — admission is eligibility, not allocation.
- OD-AI-7: **flag stays OFF.** Build the premise-reader the item says the decision waits on:
  now that C4 packet fields flow (ceremony completed 2026-07-30 —
  `phase8/receipts/VPS_CEREMONY_COMPLETED.md`), write a small tested tool that reads accrued
  runtime packets and answers "did a session close produce a candle the engine dropped as
  forming?" — the decision returns when data answers it. It must run read-only on an exported
  packet file (there is one at
  `/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz`
  for shape; note its fields predate C4).

**AP-2 — OD-AI-4 option C: V2 beside V1.**
Re-derive the survivor-book/MC artifacts at the post-`8f6da5150`/`33d854189` cost coverage as
**V2 files beside V1** using the generators' `--out` (never overwrite V1; that footgun was
fixed, keep it fixed). Document the deltas (the 23 FTMO field moves, crypto 34 %→69 %
MEASURED, `book_days` identical everywhere) and assert in a test that **no tier/verdict
changes between V1 and V2** — that assertion is the point of C.

**AP-3 — OD-AI-8: the energy-class peer transfer, signed and spent.**
The recommendation is "sign the peer transfer", and the owner's blanket yes signs it. Author
the transfer artifact: `NATGAS.cash` (and `HEATOIL.c`, same state) commission transferred from
a stated energy-class peer that HAS a priced commission in `BROKER_TRUE_COSTS_V1.json` — name
the source instrument, the kind (`peer_transfer`), the rationale, `authorized_by: borhen
(2026-07-30, blanket ratification of OD-AI-8's recommendation)`, and wire `cost_r` to accept
it honestly (read how the `commission.kind = "unknown"` refusal works first; extend, don't
bypass — the transfer must be visible in provenance, never laundered into MEASURED).
**Then spend it**: re-run AF's FVG-mechanism family measurement with the unblocked members —
the grid's strongest mean (+0.4571 R/day pooled, dispersion 0.117, 3/3 members positive,
band-stable) failed on SAMPLE only. Declare the new looks first (family ratchet — the current
family artifact is AO's V3 if merged, else V2), file ledger events, gate at the ratified rule
(`B_balanced` α = 0.10, all-declared). This is the one item on the page that can move an
armed sleeve's evidence — treat it as the session's centrepiece.

**AP-4 — OD-AI-6: the challenge-account package.**
Sequenced after OD-AI-1 (ratified) and OD-AI-2 (armed today by the orchestrator) — so build
it now, as a **package, not an activation**: the ratified family+α cited in writing; the
membership stated as **conditional on AN's population rule** (if the `decidable` basis is
ratified, the `mx_btcusd` ADMIT falls and the package parks); the **exit contract NAMED** —
`mx_btcusd` arms on `target_5R` (+0.309 R/day; its live M15-printed 1-bar time stop is
−0.141 R/day and truncates 72–90 % of trades — say so), `sub_xvol_pullback` per AK's frontier
(`target_4R`, +1.157 R/day); its own `--tags`; a token plan; a canary page modeled on
`phase4/CANARY_OPERATOR_PAGE.md`; sizing at registry weights per OD-AI-5 (the 3.81 %
`EXCEEDS_THE_DIAL` vol-matched branch explicitly NOT adopted); and a stated stop condition.
Which of the three challenge accounts is Borhen's choice — leave that field open.

**AP-5 — AE's five and P's three.**
`phase7/receipts/AE_OWNER_DECISIONS.json`: adopt each item's shipped/proposed recommendation
under the blanket ratification, implement what is implementable in the (default-off) learning
lane, and record each adoption with its provenance. Same for Session P's three in
`phase3/PACKET_EMITTER_CARRY.md` §7. Anything needing host action → handoff list in the
result doc. Where adopting a recommendation would change armed-money behaviour TODAY (not
default-off machinery), stop and put it on the handoff list instead — the lane stays
recommendation-only.

**Do not redo:** OD-AI-1's residual (the two banked prescriptions) was executed by wave 9 —
AL ran both (`mx_btcusd target_5R` on RECORDED → the first sealed-α ADMIT, p 0.0011; the
`vr ≥ 1.4` variant → REFUTED as a significance repair). Cite, don't rerun.

## Done means

`SESSION_AP_DECISION_IMPLEMENTATION_RESULT.md` (findings-first, receipts under
`phase10/receipts/`), every artifact committed on your branch, blocks B1350–B1399 written,
scoped A/B green vs the zero baseline, and a handoff list for the orchestrator (host actions,
owner choices left open). Report honestly what was NOT done and why.

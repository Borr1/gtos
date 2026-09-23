# Session AV — the sample engine (wave 12, B1600–B1649)

Read first: `WAVE_11_WORKING_AGREEMENT.md` (wave-12 deltas at §4), AP §1 (the FVG family's
residual is YEARS), AR §5 (the near-miss needs 4.7× the data), AQ §5/§6a (the refuted absence —
pre-2024 H1 files exist and are refused only for want of a `.timebase.json`). Owner authority:
Borhen's standing 2026-07-30 ratifications, including "the edge puzzle fully solved with as many
replays as possible". Standing directives apply.

**The wave-11 convergence this session executes:** after the contract repairs, the binding
constraint on nearly every near-miss is SAMPLE — `significance` is the failing gate at the FVG
family (p immovable on 9 restored trades), the D1 near-miss (needs ~24 more years at current
width), and `sub_xvol_pullback` (n = 88). Sample is bought with data engineering, not with more
gate runs on the same trades. This session buys it everywhere it is cheap.

## Work orders

**AV-1 — Stamp the pre-2024 H1 clocks (AQ handoff 7, "the cheapest open item").**
`data/` holds H1 series for 12 of 14 FX-D1 cohort symbols, 4 reaching to 2022-01-03, refused
only because they carry no `.timebase.json` (F7 fail-closed — correct). Verify each file's clock
empirically (the broker-clock methods exist: session-boundary tests, weekend gaps, DST
transition dates — never assume; the F7 rule exists because a `_utc` name lied before), write
the sidecars for the ones that PROVE their clock, and re-run the ratified hour-01 convention's
gate on the widened window. Files that cannot prove their clock stay refused — say which and why.

**AV-2 — Ingest the deep-H4 export and revive the three carry-conditional sleeves.**
The orchestrator is fetching `bridge_ftmo_deep_h4_*` from the VPS (the export lands under
`data/mt5_research_exports/`). When it lands: verify timebase per file, re-run the generator for
`metals_softband`, `vp_euidx_pocgrav` (still needs its GER40/UK100 M1 aux — check whether the
export covers it; if not, file the exact residual ask), and `sub_mid_dn_revert`'s missing-window
members, then re-tier them with measured carry at the ratified rule. If the export has not
landed when you reach this item, build the ingest+verify harness against the existing
`bridge_*` files' shape so the orchestrator's fetch drops straight in, and say so.

**AV-3 — The label-store extension for the meta-label route (now live-relevant).**
`fx_jpy` is ARMED since the five-sleeve expansion — and AD §4.8's meta-label entry filter is its
named repair. AP measured the blocker: the label store has ZERO `fx_jpy` rows, zero JPY symbols,
H4-only. Extend the store to the JPY/M15 surface (schema + backfill from the archive walks),
then run the §4.8 filter's first honest gate on `fx_jpy` at the ratified rule. This is the one
work order that can move an ARMED sleeve's evidence this wave — treat it as the centrepiece.

**AV-4 — The pooled-sample honesty check.**
Where a family pools symbols for sample (the FVG three, AF's coherent families), measure what
pooling is worth under the ratified rule with the chronological-fold table and AR's maxbars-share
reporting — and state per family whether the sample constraint is calendar-time (only more years
help) or width (more members help). That distinction routes every future data ask.

## Done means

Result doc + receipts under `phase12/receipts/`, blocks B1600–B1649, scoped A/B green vs the
zero baseline, ledger/repair-queue appends, honest §what-I-got-wrong, handoff list. Never touch
the VPS; never run broker-capable scripts; never edit `config/agent_config.yaml` or
`config/profiles/redacted_account.yaml`.

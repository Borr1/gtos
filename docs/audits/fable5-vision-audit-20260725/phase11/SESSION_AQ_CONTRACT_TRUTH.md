# Session AQ — contract truth (wave 11, blocks B1400–B1449)

Read first: `WAVE_11_WORKING_AGREEMENT.md`, `phase10/POPULATION_RULE_DECISION.md` (the ratified
rule and its conditions), CLAUDE.md §3–§4. Owner authority: Borhen's 2026-07-30 blanket
ratification ("proceed as proposed and recommended on all the decisions") — this commission
implements the standing prescriptions; your judgment governs the how.

**The objective in one sentence:** make the published economics describe contracts the live
book actually runs, then re-gate the candidates on the true contracts — because today the
twelve `mx_*` D1 sleeves' published numbers describe exits the live engine truncates
(`time_stop_bars` is M15 PRINTED bars, `execution.py:8953-8958` — their nominal 72–96 h
horizon is a live 24–25 h stop, 72–90 % of trades truncated).

## Work orders

**AQ-1 — The D1 time-stop truth, both sides of it.**
Walk the D1 cohort (and the four M15 sleeves that also bind) at the TRUE live contract and at
the intended contract; the per-sleeve delta is the value of the repair. Then build the repair
as a package: bar-unit-correct time stops (spec/engine change), tests that pin the unit, and a
per-sleeve before/after table. **Verify and state that the armed three are H4 and unaffected**
— do not touch an armed sleeve's spec; the package arms nothing by itself. H1 membership check
before any `src/` edit.

**AQ-2 — The hour-01 entry re-derivation (the ratified convention).**
`phase9/OWNER_DECISION_ENTRY_HOUR.md`: the FX D1 cohort enters at the first bar after broker
hour 00. Re-derive generation on that convention, republish member economics net of the
measured hour-01 spread (AM's hour-resolved table), and gate survivors at the ratified rule —
RECORDED, band alongside, family V3 + your declared looks, cut rules declared. AH's hour-04
arm exists as a comparator only; it is past the net frontier's peak.

**AQ-3 — `sub_mid_dn_revert` BUILT re-derivation.**
AM measured the second raw-UTC site (50.04 % of bars mis-bucketed) by re-clocking the walk;
the BUILT artifact itself was never regenerated. Regenerate on the corrected clock, walk,
gate. Carry AN's finding honestly: its nearness is flat-band-only (mid-band p 0.352), and the
re-clock repair grows in R/day with the band while weakening in p — set expectations from
that, not from the flat headline.

**AQ-4 — The `mx_btcusd` challenge dossier page.**
One page the challenge package cites: the admission cell (`target_5R`) on the true contract,
the band table (admits at two of three bands), the chronological folds, and the recent-fold
sizing basis (+0.198 R/day). This is the evidence page for the estate's ONE standing
admission — it must be exactly right and self-contained.

## Done means

Result doc + receipts under `phase11/receipts/`, blocks B1400–B1449, scoped A/B green vs the
zero baseline, ledger events + repair-queue rows appended, handoff list. Never touch the VPS;
never run broker-capable scripts; never edit `config/agent_config.yaml` or
`config/profiles/redacted_account.yaml`.

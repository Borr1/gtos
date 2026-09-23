# Session AN — the population rule: wire the model's own honesty switch, then price every rule so one gets ratified

**Wave 10.** Worktree `worktrees/wave10-population-rule-20260730`, branch
`phase10/population-rule`, from `main`. **Blocks B1250–B1299.**

**Read `../WAVE_10_WORKING_AGREEMENT.md` first**, then AL's result §3.3–§3.6 + §10 item 4 (your
commission is cut from it), then AM's result §4.5 (the band-widened artifact you will evaluate).

## The mission

AL measured that the estate's first sealed-α ADMIT exists on exactly one of four defensible
populations, that the era-quality rule (`era_class == RECORDED` vs the model's own `decidable`)
was never chosen deliberately, and that the model's honesty switch is unwired: an undecidable
RECORDED era prices as `coverage=MEASURED` on a 204,058× band, `require_decidable=` exists,
is tested, and no production path passes it. Your job: wire the honesty, then produce the
decision package that lets Borhen ratify a population rule with the whole surface priced.

## The work, in dependency order

**1. Fix the coverage hole.** `spread_model.py:440-441` degrades `Coverage` only on `era_class`;
make `not decidable` degrade coverage on every path (not just the `fb` fallback), so a 204,058×
band can never read as MEASURED again. Behavioural tests; AH's 19 composition tests and AG's
suite stay green; H1-check first.

**2. Wire `require_decidable` as a first-class GateSpec axis** (like `spread_band`): threaded
`cost_r → spread_price`, seal-honest per `spec.canonical()`'s wave-8 rule (None resolves to the
value it runs at; the pre-field behaviour is `False` and only that value is dropped — read the
comment there and follow it exactly). AL reimplemented the restriction three times in drivers;
after you, nobody reimplements it again.

**3. Evaluate AM's band-widened era artifact** (`SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json`)
as the SCHEDULE-era treatment: what verdicts move at low/high bands across the estate's standing
candidates if it becomes the model of record (AM measured `mid` moves nothing). Recommendation
with numbers; adoption is the merge-train's call.

**4. The decision package.** Re-run the admission-bearing cells — `mx_btcusd @ target_5R/{4R}`,
`sub_xvol_pullback @ target_4R`, `sub_mid_dn_revert` (AM's re-clocked population, its driver) —
through the WIRED model under each candidate rule: RECORDED, DECIDABLE, RECORDED∧decidable, and
ALL_ERAS as the control; all three bands; both options; family per the ratcheted declaration.
One table per candidate, R0-stamped, q within-artifact only. Close with a one-page
`phase10/POPULATION_RULE_DECISION.md` for Borhen: the three rules, what each admits/rejects,
what each says about the 78 disputed BTCUSD trades (+0.914 R/day on their own — not free-riders),
and your recommendation with its price. He ratifies a RULE, not a verdict.

**5. If the wiring changes any standing verdict** (it can — coverage degradation feeds
`restrict_to_priced`), publish the delta table; do not silently re-derive.

## Deliverables
`phase10/receipts/POPULATION_RULE_V1.json` + `phase10/POPULATION_RULE_DECISION.md`; repair-queue
rows (session `AN`); result doc with §2 receipt; ledger; blocks B1250–B1299.

## Not yours
The VPS. Arming, α, the ratification itself, sleeve composition, adopting the widened-band model
(recommend only). Merging to `main`. `config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your report.

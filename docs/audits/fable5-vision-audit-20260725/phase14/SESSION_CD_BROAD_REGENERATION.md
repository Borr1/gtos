# Session CD — the broad family under the repaired stack (wave 14, B2250–B2299)

Read first: `phase14/TRAINING_LANE_RATIFICATION.md` §1.3 (your charter — January's negative
was never a family verdict; the language rule binds you), `phase14/SESSION_CB_TRAIN_ENGINE_RESULT.md`
IN FULL (your instrument: 1.53×/arm, 4-up at 3.25×, `--days`, the guard, H-CB-3/H-CB-5),
`phase14/SESSION_CC_TRAINING_PROTOCOL_RESULT.md` + `WAVE_11_WORKING_AGREEMENT.md` §6 (the two
axes — January 2026 is `SEALED` on the trainable axis and **`VAL` on the surface axis**, so
the lane may ITERATE against it, logged and unbilled, with the used-once disclosure),
`phase12/SESSION_AW_SEPARABILITY_MINE_RESULT.md` §0 (the old-engine baseline your regeneration
is measured against), `phase14/TRAINER_SESSION_TEMPLATE.md`. Owner authority: the 2026-07-31
ratification — this session is the reason the lane exists.

**The objective in one sentence:** re-generate the broad V4 family's January arms under the
REPAIRED stack — broker-true commission, the spread-geometry floor, the repaired clocks and
stops — and report what the family's economics actually are when measured properly, as the
first run of the training loop end to end.

**What "the negative" currently rests on, so you know what you are re-testing:** four sealed
January arms on the OLD engine — commission ≡ 0 on all 28,519 pool rows (F38, AW-confirmed),
no spread-geometry floor (16.5 % of pool rows cost > 1 R = 49.6 % of the entire loss), the
pre-repair clocks and stops. AW's intent-level verdict on that pool: no directional edge
(gross mean −0.22 R/row, model ceiling AUC 0.712 still below break-even). The honest current
label is `UNTESTED_UNDER_REPAIRS`; your job is to remove the UNTESTED.

**H-CB-2 IS RUN AND THE VERDICT IS SPLIT — this binds your patch set**
(`phase14/receipts/CB_VERIFY_HCB2.json`, orchestrator, 2026-07-31, per-call verification on
the 2-day fixture): `authority_payload_hash_content` is MEASURED CLEAN — 44,304,913 verified
hits, 0 mismatches — and so is `ultimate_candidate_package._packet_hash` (8,628 / 0). Three
memos are measured WRONG per call: `probability_debate_v4._stable_sha256` **8,810 of 8,810
hits disagree (100 %)**, `selector_v4._selector_hash_digest` 69,767 of 165,247 (42 %),
`v4_timewarp._stable_sha256_uncached` 1,216 of 38,416; `attribution_fields_identity_memo`
8,207 of 95,150 (8.6 %). Outcome identity still held four times at zero tolerance — these
values evidently do not feed decisions ON THIS FIXTURE — but a memo measured wrong per-call
is not a lever the lane runs on trust. **Your runs use the SAFE SET ONLY:
`authority_hash_content_memo, abc_concrete_types, gc_during_chunk,
skip_post_hoc_ledger_recertification` — do NOT enable `proof_hash_content_memo` or
`attribution_fields_identity_memo`** (measured cost of dropping them: a few percent of the
speedup). Re-keying the dirty three is a filed repair, not your charter — unless your CD-2
work touches those functions anyway, in which case fix-and-verify is welcome.

## Work orders

**CD-1 — Wire the lane-iteration purpose.** CB's runner authorizes reproduction and training;
your runs are neither — they are lane ITERATION on a VAL-surface window. Wire the runner to
`trainer_partitions.SurfaceMap` (`lane_disposition_for_day`) and to
`training_lane.IterationLedger` so every arm you launch auto-logs a look (session="CD",
dates, spec digest, engine version, verdict vocabulary respecting CC's refusals). March and
the blackouts stay refused on every path; do not modify `trainer_partitions.py` or the sealed
gate. Tests in CC's behavioural style.

**CD-2 — The repaired-stack injection, one repair at a time, each with an inertness control.**
Enumerate which repairs apply to the REPLAY path and inject each through the train lane's
rebind pattern (`train_engine/cuts.py` discipline — no frozen byte moves, H1/R2 checked):
broker-true commission (the schedule Session J vendored; F38's zero is the defect),
the spread-geometry floor at generation (AY's mechanism and per-sleeve thresholds),
the broker clock (`broker_clock.py` vs any hardcoded offset on the replay path), and the
time-stop contract where the replay's differs from the repaired live one (AQ's 96→7680 class).
For EACH: an off-switch run proving `OUTCOME_IDENTICAL` to frozen when the repair is off, and
a named receipt of what the repair changes on one day before you run arms. If a repair does
not reach the replay path (some are live-path-only), say so with the code cite — a repair
that does not apply is a finding, not a failure.

**CD-3 — The regeneration.** The four January arms (S0R0/S1R0/S0R1/S1R1) under the repaired
stack, 4-up (CB measured 9.14 GB for four — but see CD-4's ordering). Deliverable: the
per-arm, per-repair delta table — frozen January vs repaired January — trades, cost
decomposition, R/day, and the loss-concentration shape AW mapped (does killing the 16.5 %
cost-tail rows move the pool the way the estate's out-of-window numbers say?). Then the
family verdict, in the agreement's language: what January says about the broad family UNDER
REPAIRS, at the VAL surface, with the used-once disclosure. No bare ADMITs; nothing here
bills the family — candidates that deserve the sealed gate get filed with surface maps, and
graduation is a separate deliberate act.

**CD-4 — The month-scale measurement rides your first arm (H-CB-5).** Before going 4-up, run
ONE full arm solo and record wall + peak RSS — that single run converts CB's "16.5 h → ~3 h"
extrapolation into a measurement (the assumption is per-arm RSS ≈ 3 GB at 31 days). If RSS
grows materially with window length, re-plan concurrency before launching the other three,
and say so. If wall-clock permits, also run CB's frozen comparand for the outcome-identity
half; if not, hand the command back.

**CD-5 — The loop's first gradient pass.** Whatever CD-3 finds, iterate at least one gradient
honestly: pick the strongest sub-family or repair-interaction, vary ONE axis on `--days`
sub-windows, and file the surface map — the point of the lane is that a near-miss gets a next
step, not a filing. If everything is flatly negative under repairs, map WHERE the loss
concentrates instead (AW's method) and file that. Either way the iteration ledger shows the
loop actually looping.

## Done means

Result doc findings-first + receipts under `phase14/receipts/`, blocks B2250–B2299, every
look logged to the iteration ledger as you go, scoped A/B green vs the ZERO baseline with the
tool-emitted `gtos-ab-receipt-v1` fence, honest "what I got wrong", handoff list. R2 and the
frozen engine untouched (rebinds only); March outcome-unread on every path; never touch the
VPS; never run broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or any R2-bound path. The sealed admission rule is frozen
— you make the search cheap and honest; you do not make admission cheap.

# Session FA continuation — RESULT (Phases B–E complete; LAND gate + March held for the owner)

Written 2026-08-05 under OD-BROAD-FORENSIC-2 ("do not stop at the audit: verify the Codex
work, build the single full flow of the system from start to finish and make it flawless,
land the repairs, measure the results with the edge in, merge everything to main on my
explicit approval, and clean up the estate's worktrees when done. The March virgin confirm
stays frozen until my word"). Everything below is **DEVELOPMENT-FITTED lane evidence,
billed:false** — January is the month every repair was derived on. March (frozen prereg,
`receipts/forensic/MARCH_PREREG_V1.md`) is the only decoding window, on Borhen's word only.

## 0. TL;DR — the three findings that matter

1. **The frozen January book's −5.51 was two large errors canceling.** The frozen cost
   layer overcharged spread **8.5×** (157,637 R vs 18,584 R truthed, 153,486 packets) and
   that overcharge was the de facto admission throttle; underneath it, the pool's honest
   EV is negative. Repairing the cost lie alone → **−31.46** (138 trades). Adding belief
   honesty → **+0.58 on 6 trades** (near-total stand-down). Neither half may be repaired
   alone; any live-transfer claim from the frozen book inherits both errors.
2. **The repaired system's verdict on the broad pool is STAND DOWN.** Best repaired book:
   +0.15…+0.58 on 1–6 trades — inside the 0.751 R seed-replicate band (B2). BELIEF_RECAL's
   no-honest-sub-book verdict survives every T2 composition. The negative-vs-invalid
   asymmetry closes honestly: the measurement was invalid, the repair is real, and the
   repaired truth is "don't trade this pool".
3. **The billed edge is INEXPRESSIBLE in the engine as gated.** Arm (v) transformed all
   12,668 breaker candidates into CQ's inverted 5D/0.25D cell (zero errors, geometry
   verified 483/483 in smoke) and bought **zero trades**: the 0.25D stop shrinks the R
   unit, median `cost_r` goes 0.191 → **0.701 (3.7×)**, and **100 % refuse at the
   pre-trade cost gate** — at ANY declared ceiling. The engine's cost gate is denominated
   in R units and structurally presumes ~unit-R stops; no high-RR candidate can ever pass
   it, whatever its realizable economics. (CQ's +11.9 walker figure and the engine
   disagree about whether a 20R-target trade may pay 0.7R of cost — not about the path.)

## 1. The full-flow table (T2 + T3, full January, all configs 2-day-smoked, receipts in `receipts/forensic/t2/`)

| arm | composition | trades | book net R | Δ vs r0 |
|---|---|---:|---:|---:|
| r0 | CJ recipe (frozen costs) | 57 | −5.5062 | — |
| (i) | + R-COST-TRUTH | 138 | −31.4640 | −25.958 |
| (ii) | + R-BELIEF + R-SCHEMA | 6 | +0.5782 | +6.084 |
| (iii) | + `cost_ceiling_0p05` (comm. swap, − ruler) | 1 | +0.1495 | +5.656 |
| (iv) | CJ pair + 8 inert controls | 57 | −5.5062 | **+0.0000 exact** |
| (v) | (iii) + breaker transform (the edge in) | 1 | +0.1495 | +5.656 |
| T3 | (ii) w/ commission gated→accounting | 4 | −0.2165 | +5.290 |

Attribution: (i)−r0 is single-variable (spread truth) by construction; (iv) proves all
wrapper machinery outcome-inert at month scale; T3 proves the commission-gate swap is
**contest-active, not inert** (6→4 trades, −0.79 R vs (ii)) — at n=1–6 every composition
delta is contest-dominated, so only (i)'s magnitude and the structural facts (stand-down,
inexpressibility) sit outside noise. The B2 seed band (three full-month replicates,
`receipts/forensic/B2_SEED_BAND_V1.md`) is the floor under all of it: 0.751 R month-scale,
zero moved trades, four contest sites, one seed-only admission-count change.

## 2. What landed (all committed, two worktrees)

- **Phase B closed**: instrumented walk, 3-point seed band, BELIEF_RECAL, adversarial
  pass. **Phase C accepted**: five repair families (R-COST-TRUTH, R-BELIEF, R-SCHEMA in
  vivo, seed dial, controls), all smoke-verified, INCOMPATIBLE discipline fail-closed.
- **T1 pool screens** (`receipts/forensic/t1/`): calibration 22,000/27,658 bit-exact;
  R-CAPS = loss-reduction only (no cap flips the pool's sign); R-GEOMETRY empty (±0.05 R,
  2R locally optimal); **the fill axis is where the missing money sits** (fvg +0.75 / ob
  +0.64 gap to the fill-free ceiling; both realizable entry policies negative; the 0.92
  `execution_fill_probability` constant is load-bearing and wrong on exactly those
  families). Cell declaration frozen before arm (iii) ran, amended twice ex ante
  (`424500467` ruler×ceiling; `008aec561` funnel seam + engine-contract caveat).
- **The arm-(v) lane hook** (fa2-integration `e7b7aa4d6` + `c25e2510d`): the breaker
  transform runnable through the lane's one candidate funnel, census-attributed, inert
  control paired, live×control refused, absent-false live key untouched.
- **MARCH_PREREG_V1** (executes spec §10): substrate SHAs at `c25e2510d`; the six March
  arm compositions verbatim; **five near-deterministic mechanism primaries** (funnel
  widening, stand-down, near-silence, machinery identity, inexpressibility) with frozen
  thresholds; economics as **estimation only** — the MDE honesty says a single month
  cannot power sign tests at these variances (monthly MDE ≈ 20–26 R vs deltas ≤ 6 R
  except (i)); March materialization prerequisite (no `march_2026` lane window exists) 
  under CR-class outcome-blind loaders; the CR decode asterisk **adjudicated** (March is
  "virgin for selection purposes" — no March value has influenced any declared decision);
  Borhen the sole trigger.

## 3. What I got wrong (the register)

1. **Arm (v)'s first seam was wrong and its own smoke caught it** — I rebound
   `V4DecisionCycleCore.generate_candidates`; the lane replays prepared-pack candidates
   and the producer path never runs (census: 0 calls). The funnel rebind is the fix. The
   smoke-ladder discipline exists for exactly this.
2. **I authored the ruler×ceiling INCOMPATIBLE row in Phase C and then omitted it from my
   own arm-(iii) declaration.** The runner's fail-closed validate refused it at launch.
3. **Two verifier field errors**: I tested `side` where the pool writes `direction`, and
   treated `broadorigin_` ids as a transform marker when it is the generator's own
   namespace for every row. Both fixed against read rows, not assumptions.
4. **T3 expectation refuted**: I predicted the commission swap ≈ inert; it moves 2 trades
   and −0.79 R through contest re-resolution. Recorded as contest-mediated, not a ceiling
   attribution.
5. **Smoke 3 v1 config gap** (Phase C): S2/S3 stamps ride `decision_semantics_projection`,
   which my patch list omitted; v2 carried it. A config requirement, not a code bug.
6. **WALK-F1's first hypothesis was wrong** (Phase B): condition features missing from
   MISSED was a projection/config gap, not a compactor defect.
7. **B2's first framing was too narrow**: r0-vs-r1 suggested "same count, different twin";
   r2 showed seed noise changes the admitted COUNT itself (57→58).
8. **L3b population note** (BELIEF_RECAL): the 0.172-vs-0.347 discrepancy was a
   population-definition mismatch on my side, reconciled in the receipt.

## 4. Owner decision sheet (nothing below executes without your word)

**D-1 — LAND gate (standing, GREEN).** `phase19/fa2-integration` (now `c25e2510d`) merges
to `main` on your explicit "land it" — A/B receipt embedded (`receipts/SESSION_FA_AB_RECEIPT.md`,
13,304/2/0 vs sealed 12,809/2/0, zero regressions by failure set). Say the word and it lands;
say otherwise and I follow that.

> **D-2 CLOSED 2026-08-05 by owner instruction — `mx_btcusd` is DISARMED on FTMO.** Session LM
> removed it from the live worker's `--tags` and deleted the `--frontier-exits` argument in
> `scripts/run_book_supervisor.ps1` on the host (live tree
> `C:\Users\MSI\Documents\ai-trading-agent`), committed on the host branch as `2fa77722d` so no
> checkout can re-arm it; no config byte moved, so the activation-token digest is unchanged
> (`ffe16657feaf` re-confirmed after restart). FTMO now runs the four core sleeves; redacted_account
> untouched. Receipts: `phase19/receipts/vps_live_ops_20260805/` on branch
> `ops/vps-live-mx-disable-20260805`. **Three NEW owner items came out of that session** — the
> redacted_account token defect now has a measured cost (FN was refused the same energy trade ~2×/min
> for two hours on 2026-08-04 while FTMO booked +$493.20), exit-provenance labelling (a manual
> exit is recorded as the sleeve's own performance), and the break-even routine's missing
> worsening-guard (it would have undone an owner-moved stop at 2R). See
> `SESSION_LM_VPS_MX_DISABLE_AND_HEALTH_RESULT.md`. The original entry is retained below as the
> evidence that motivated the decision.

**D-2 — mx_btcusd is LIVE on a REJECTED admission (A1b, binds immediately).** The estate's
one standing admission — `mx_btcusd @ target_5R`, live on FTMO at confidence 0.025 since
2026-07-31 — flips **ADMIT → REJECT** under the corrected permutation null (q 0.048→0.129
at mid; the REJECT comes entirely from the +1SE conservative variant near its 48-family
bar, flip boundary ρ 0.42–0.45 vs measured 0.384). The same correction flips CQ's breaker
**REJECT → ADMIT** (q 0.077) — **one posture must judge both members**; under the posture
that admits the breaker, mx REJECTS. Economically the arming is ~inert by design (0.025),
so this is a governance decision, not a P&L emergency: pull it, keep it as a declared
forward-record exception, or re-derive the posture — your call, priced in
`receipts/forensic/a1_cleanroom/A1_REISSUED_VERDICT_TABLE.md`.

**D-3 — the March one-shot.** Trigger phrase is yours (OD-FA2-1). What runs is exactly
`MARCH_PREREG_V1`: materialize March lane packs outcome-blind → one decode event, six
arms → five mechanism verdicts + estimation tables → kill/park/iterate is yours. Cost:
~15 h serial compute + materialization. What it can and cannot decide is frozen in §4/§6
of the prereg.

**D-4 — the broad family after T2 (options, priced).**
- **Kill**: the mechanism story is complete and internally consistent; March would test it
  out-of-window first (D-3 before D-4 is the natural order).
- **Park**: costs nothing further; the repairs stay landed and reusable; the pool packs
  (Jan/Feb/Apr/May) and receipts remain.
- **Iterate**: two repairs are *licensed by measurement but not built*: (a) a
  price/notional-denominated pre-trade cost gate (arm (v) proved the R-denominated gate
  structurally excludes every high-RR candidate); (b) a candidate-declared-target
  passthrough (moot until (a) exists). Each is a lane-repair-sized build (~1 session)
  with the Phase C pattern, and each is a *system* capability, not broad-family-specific
  — they would matter for ANY future high-RR candidate, including V27 successors.
- **The fill axis** is the deepest open economic thread (T1): the retrace families' edge
  lives at an uncapturable fill-free ceiling, and the engine's flat 0.92 fill constant is
  wrong in the harmful direction on exactly those families. Truthing fills needs tick
  captures (P1-class, SCHEDULED-ON-NEED) — a data acquisition decision.

**D-5 — estate worktree cleanup (OD-FA2-4).** Sweep plan pending your one-decision
approval at the closing ceremony: relocate the wave16 `.hermes` LANE_INPUTS_TRUE_UTC_V1
(17 GB) to a durable hold **and prove a 2-day arm runs from the new location before
deleting anything**; exception list attached at execution time.

## 5. Evidence-class labels and pointers

Every number above: DEVELOPMENT-FITTED lane evidence, billed:false, January 2026, C7
censoring (120-min wall) applies. Receipts: `receipts/forensic/` (B2, BELIEF_RECAL, T1,
t2/, MARCH_PREREG_V1, RESUME_STATE); iteration ledger self-billed per run (uncommitted by
design until the ceremony's append-union). Routes: fa2-integration
`attempt_5_typed_sparse/FA2_*` (ledgers gzipped in place, readable). The wave19 branch
carries the receipts; fa2-integration carries the code. Merge moments: exactly two, both
on your word.

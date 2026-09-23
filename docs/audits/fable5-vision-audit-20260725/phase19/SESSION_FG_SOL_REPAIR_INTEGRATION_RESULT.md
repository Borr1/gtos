# Session FG — Sol Wave 19 repair integration result

## Decision

**REPAIR INTEGRATION COMPLETE; CONTINUE THE SYSTEM; NO PROMOTION OR FAMILY KILL.**

FG integrated **66/66 source commits** from CR, CS and FB–FF into
`phase19/sol-integration`, with zero unknown source mappings. Every supported evidence repair is
preserved. The only two new scientific candidates remain default-off; the two new measurement
instruments remain explicit-only; the unchanged breaker gate rejected; no exit or condition gate
survived. No config, activation, broker, VPS, token or live-service surface changed.

The official Session-FA continuation is
`SESSION_FA_BROAD_FORENSIC_RESULT.md`. The machine defect and repair authorities are
`receipts/FG_DEFECT_MAP.json` and `receipts/FG_REPAIR_REGISTER.json`.

## Six owner answers, with numbers

| owner axis | answer | decisive numbers |
|---|---|---|
| Wrong selection? | Partly, but not the main cause. S0 improved a negative set. | Chosen percentile 0.669969 Jan / 0.684373 Feb; chosen net -0.100113R / -0.068300R versus set mean -0.722471R / -0.665061R. All tested ex-ante replacement rules stayed negative; only the oracle was positive. |
| Wrong sleeve/mechanism? | Yes, heterogeneously. | Breaker inverted 5D/0.25D +11.901108R full Jan over 4,263; OB-retest 1.5D/0.25D +1.646719R over 1,340. Executed FVG -12.263583R Jan / -5.783454R Feb; non-FVG +6.757375R / +1.822056R. |
| Inaccurate geometry/exits? | Geometry yes; no tested exit persists. | Breaker OOS +11.252342/+7.453554/+3.852045R Jan/Apr/May. Exit V17 +0.197R TRAIN, -1.920R HOLDOUT, -0.381R Feb, q=0.4861; 0/40 persistent cells. |
| Inaccurate conditions? | Existing fields rank less-bad but do not isolate edge. | Spearman gross 0.443847, p=0.002; net 0.894602, p=0.001. Jan 7 TRAIN gross-positive / 4 HOLDOUT / 0 net; Feb 9 gross-positive / 0 net; strict survivors 0. |
| Why decline positive options? | Sparse winners sat inside negative, overconfident pools; cost refusals were correct on average. | Pool net -24,357.198914R Jan / -15,513.472827R Feb; 7,706 / 7,498 positive rows. Cost-refused means -1.12107R / -0.74728R. Expected-net optimism +1.084246R / +1.011859R. |
| Ex-ante separator? | Two geometry rules; neither is activation-ready. No global separator yet. | Breaker rejected at raw p=0.002600, BH q=0.153385 > 0.10 across 59. OB max-T p=0.001 in Jan but independent RECORDED folds remain. |

## Integrated repair disposition

| priority | repair | state | gate / next action |
|---:|---|---|---|
| 1 | FD semantic/authority repairs plus deterministic memo key | implemented, evidence-only | Preserve. Historical discarded fields remain exact recapture requirements. |
| 2 | CR executable capture v3 and reference-fidelity split | implemented, training-only | Preserve; capture a true broad-V4 RECORDED executable population. |
| 3 | FF exact hard-eligibility/rank observability | implemented, default-off | Run only through `safe+hard-eligibility-observability` on a bounded fresh capture. |
| 4 | FE 15-field condition telemetry | implemented, default-off | Run only through `safe+conditions` under a preregistered fresh design. |
| 5 | OB-retest 1.5D/0.25D | implemented, research-only default-off | Independent path-complete RECORDED folds under the unchanged gate. |
| 6 | inverted breaker 5D/0.25D | existing default-off | Gate REJECT; pursue predeclared breadth/book diversification, not threshold relaxation. |
| 7 | generic exit evaluator / bounded FC2 family | evaluator default-off; FC2 unrun | Reject current 40 cells; preregister and test FC2 only. |
| 8 | probability/EV calibration repair | exact experiment requirement | Fresh OOS joint calibration after geometry, costs, confidence and fill semantics align. |

Rejected changes remain explicit: no FVG or XAUUSD veto, breaker preference, structural preference,
late-market conversion, authority relaxation, condition gate, tested exit overlay, multiplicity
relaxation, family kill, promotion or arming.

## Integration integrity

- Source heads verified before integration: CR `47139bc3`, CS `7f9ab73c`, FB `6ef09b8f`,
  FC `21030768`, FD `a7d9260e`, FE `674b81f6`, FF `9c95c28b`.
- Source commit mapping: 66 expected, 66 integrated, 0 unknown. Authority:
  `receipts/FG_SOURCE_COMMIT_LEDGER.json`.
- Semantic conflicts were mapped before cherry-pick. CR capture fields, FD normalization, FE
  conditions and FF hard-eligibility coexist in `train_engine/cuts.py`; the last two are absent
  from both default and safe sets. Authority: `receipts/FG_CONFLICT_MAP_PREINTEGRATION.json` and
  `receipts/FG_CONFLICT_RESOLUTION_LEDGER.json`.
- The combined changed-test sweep after committed fixture hydration completed **301 passed, 0
  failed**. The hydration script materialized only its known committed exact paths; no missing LFS
  object was fetched and free disk remained above the 8 GiB floor.
- The tool-derived 42-file closure completed **736 passed, 1 skipped, 0 failed, 0 errored**.
  Against the committed suite-wide failure set, `gtos-ab-receipt-v1` reports **1 bad → 0 bad,
  1 fixed, 0 regressed**. The registered mapping-order node's pass is not attributed to FG; the
  only regression claim is the empty regressed-ID set.
- FB's artifact verifier reported 11/11 checks true; FC's fast/reference self-check completed
  3,200/3,200 comparisons; the integrated verifier and tool-derived scoped A/B are closing
  authorities under `phase19/receipts/`.
- R2 has zero missing bound inputs and exactly the three disclosed inherited drifts: the CN cost
  engine plus the two package ledgers. No FG, CR, CS or FB–FF implementation path adds contract
  drift.

## Evidence boundaries and qualification

FG read no March 2026 or live-forward outcome. February remained the owner-authorized used-once
attribution surface. FG launched no full replay, contacted no VPS or broker surface, invoked no
broker-capable script, read or wrote no activation token, and changed no config or live entrypoint.
Large routes were not copied; the 76-file Phase-1 route is compactly bound by SHA-256 while free
disk remains above the required floor.

CR's two disclosed source-lane operator incidents remain disclosed: one early container decode
necessarily traversed March rows, and one `rg` scanned a document containing February text. No
forbidden value was printed, extracted, compared or used in the result. The repaired tool rejects
dates before decode. This is why FG claims result-level boundary integrity, not an ahistorical claim
that every exploratory source-lane command was perfect.

## Remaining unknowns

1. The exact hard-eligible and neutral-rank partition at S0 selection; both old ledgers discarded
   it. The FF instrument is the exact forward measurement.
2. Whether the OB-retest geometry persists in independent path-complete RECORDED folds.
3. Whether breaker breadth/book diversification pays the fixed 59-member multiplicity bill.
4. Whether fresh entry-state condition fields separate profitable net edge; existing fields did not.
5. Whether the bounded FC2 entry-state exit family persists; no current exit does.
6. Historical predecision bid/ask for template-spread rows, historical signed-authority payloads,
   1 January and 23 February cost residuals, and two January ordered terminal paths.
7. A source-bound broad-V4 RECORDED NY-metals executable population; CR's January reference cannot
   substitute for it.
8. Fresh OOS joint calibration of geometry, direct-versus-outer cost, confidence and fill semantics.

Each unknown has an exact next capture or gate. None authorizes abandonment or live activation.

## What I got wrong

I initially treated the density of declined winners as stronger evidence of a bad final selector
than it was. The completed set reconstruction shows S0 usually selected above the local set mean;
it simply could not overcome a negative and miscalibrated surface. I also treated the executed FVG
loss concentration as closer to a safe veto. FF showed that the crucial hard-eligible and rank
partition was projected out, so a family veto would currently be an ex-post composition rule.

The corrected synthesis preserves the selector guards, repairs the evidence state, advances two
geometry rules through their named gates, and narrows the next measurements instead of declaring
the family dead.

## Continuation handoff

The next session should start from this integrated branch and use the ranked register in order:

1. run the independent OB-retest folds under the unchanged ratified gate;
2. predeclare the breaker breadth/book-diversifier test rather than retuning alpha;
3. take one bounded explicit hard-eligibility/rank capture and one bounded explicit condition
   capture—never silently enable either patch;
4. evaluate FC2 only under its 24-cell cap;
5. calibrate value/probability only on fresh OOS evidence after semantic alignment.

Do not reopen rejected cells without a new declaration. Do not infer missing history. Do not arm or
promote from this result.

## Receipt map

- `receipts/FG_PHASE1_SOURCE_MANIFEST.json` — compact binding of all Phase-1 files and headline
  cross-checks.
- `receipts/FG_SOURCE_COMMIT_LEDGER.json` — all 66 original-to-integration commit mappings.
- `receipts/FG_CONFLICT_MAP_PREINTEGRATION.json` — predicted conflicts before cherry-pick.
- `receipts/FG_CONFLICT_RESOLUTION_LEDGER.json` — semantic resolutions and retained invariants.
- `receipts/FG_DEFECT_MAP.json` — complete integrated owner-axis and defect map.
- `receipts/FG_REPAIR_REGISTER.json` — ranked repair disposition.
- `receipts/FG_INTEGRATED_VERIFICATION.json` — machine verification of evidence, defaults and
  boundaries.
- `receipts/session_fg_ab/SESSION_FG_AB_RECEIPT.md` — tool-derived failure-set A/B.
- `receipts/SESSION_FG_COMPLETE.json` — post-verification completion authority.

# G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT Goal Prompt

Date: 2026-05-09
Primary owner: G12 red-team / blocker audit
Worktree: `C:\tmp\gtos_otb\G12NOFILLMAY3`
Branch: `g12-nofill-may3-source-proof-audit`
Promotion posture: `NO_PROMOTION_VERDICT`

## Mission

Audit the completed `NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF` lane as G12. Decide whether its three May 3 OTI4 rows can be accepted only as source/control evidence, remain blocked, or must be rejected. This is a red-team audit, not a result lane.

Target rows:

- `NOFILL-CAT-ROW-0049` / NAS100 / frozen range `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`
- `NOFILL-CAT-ROW-0050` / XAUUSD / frozen range `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`
- `NOFILL-CAT-ROW-0051` / XAUUSD / frozen range `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`

The upstream lane verdict is `MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL` for all three. G12 must independently verify or challenge that verdict using source hashes, local source coverage, official CME/session evidence, no-leak checks, duplicate/denominator boundaries, and forbidden-route scans.

## Mandatory Preflight

Before relying on summaries:

1. Run `python scripts\generate_live_state.py` and read `.context\LIVE_STATE.md`.
2. Read the latest handoff named in `LIVE_STATE.md`.
3. Read `.context\00_core\quick_reference_card.md`.
4. Read `.context\00_core\research_operating_doctrine.md`.
5. Read `.context\00_core\research_current_state.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Skim `.context\00_READING_ORDER.md`.
9. Record current HEAD, branch, controlling prompt path, and working-tree status in your context anchor.

If interrupted or compacted, regenerate `LIVE_STATE`, re-read this prompt and your latest context anchor, then continue from disk. Do not depend on chat memory.

## Controlling Inputs

Read and audit these exact inputs first:

- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_SOURCE_PROOF_PACKET_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/raw/NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/raw/NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS_2026-05-09.json`
- upstream verifier/test/build scripts in the same lane
- prior residual blocker source-access lane artifacts under `nofill_cat_v2_residual_blocker_clear_source_access_lane/`
- G12 pending source contract audit artifacts under `g12_nofill_cat_v2_pending_source_contract_audit/`
- no-fill V2 rebuild/audit artifacts and G12 consolidated audit artifacts when needed for denominator, reject, and duplicate boundary checks

You may inspect `git log`, `git show`, source hashes, prior worktree artifacts, local heavy-data roots, and the official-source raw captures. Do not assume the upstream lane is correct because it passed its own verifier.

## Research Hardening Standard

Use maximum practical reasoning. Take the time needed to challenge the upstream proof. Enforce curiosity, truthfulness, and active creativity:

- Curiosity: actively search for counterevidence, stale source assumptions, wrong timezone conversion, wrong proxy mapping, wrong official-source interpretation, hidden label movement, duplicate denominator drift, or missing proof.
- Truthfulness: if the upstream result is weak, reject or block it. If it is strong, accept narrowly and say exactly what it proves and what it does not prove.
- Active creativity: do not be boxed by the upstream artifact. Recompute what can be recomputed from local data; search official-source captures and local roots; inspect scripts/tests; identify whether a broker-native session metadata export would add value, but do not require it if the existing proof is already sufficient.

Prompt examples and file lists are starting points, not limits. Worktree absence is not data absence. If a missing source matters, search approved absolute local roots or request access. Negative evidence is useful, but it must be exact.

## Audit Questions

G12 must answer all of these:

1. Do the three target rows exactly match the unresolved OTI4 May 3 rows from the residual blocker lane?
2. Are all three upstream statuses `MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL` supported by independent source review?
3. Do local NAS100 and XAUUSD tick parquets really have zero rows in `2026-05-03T13:00:00Z` to `13:30:00Z`, with first ticks near `22:00:00Z`?
4. Does the official CME/session evidence support Sunday Globex open at `2026-05-03T22:00:00Z` for the NQ/GC proxy markets used by this lane?
5. Is the timezone conversion from UTC to America/Chicago and America/New_York correct?
6. Is the NAS100-to-NQ and XAUUSD-to-GC session proxy acceptable as source-control evidence for market-open/no-bar status, or should any row remain blocked pending broker-native symbol-session metadata?
7. Are the failed direct curl attempts recorded honestly and excluded from factual claims?
8. Do source hash records recompute for all strict consumed sources?
9. Are the Sierra/SCID/depth records treated only within their approved role and not overclaimed?
10. Are the `65` rejects, six T3 rows, G12-blocked CNR061 rows, and other no-fill rows kept outside labels, denominators, result use, validation use, and promotion use?
11. Did any generated artifact set `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`?
12. Is there any result/R/performance scoring, broker actual-R, account/order/history label, hidden label, or blocked-packet outcome use?
13. Should G12 accept this as source-control evidence only, block with exact next source, or reject?
14. What exact next prompt, if any, remains after this audit? If none, say so and explain why result lanes still do not open automatically.

## Allowed And Forbidden Scope

Allowed:

- read-only local artifact review;
- source-hash recomputation;
- timezone/session recomputation;
- targeted absolute local heavy-data checks if needed;
- official-source capture review already saved by upstream;
- optional read-only public/web check only if upstream raw captures are insufficient, with raw capture saved and hashed;
- verifier/test creation under the G12 audit directory.

Forbidden:

- no result/R/performance scoring, win rate, expectancy, DSR/PBO, promotion, validation-safe flip, or outcome review opening;
- no broker actual-R, account history, order/deal/position/history calls, hidden labels, live trade result labels, blocked-packet outcomes, or live order behavior;
- no paid/API/Databento calls;
- no live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors/canaries/MT5 order-account-history paths, credentials, remotes, registry edits, or promotion dossiers.

## Required Outputs

Write all outputs under:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/`

Required files:

- `G12_NOFILL_MAY3_CONTEXT_ANCHOR_2026-05-09.md`
- `G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md`
- `G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json`
- `G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.md`
- `G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.json`
- `G12_NOFILL_MAY3_SESSION_AND_PROXY_AUDIT_2026-05-09.md`
- `G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT_2026-05-09.md`
- `G12_NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md`
- `G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md`
- `G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json`
- builder script, verifier script, and focused pytest file.

Also update `.context/00_core/research_current_state.md` and regenerate `.context/LIVE_STATE.md` before final status.

## Verification

Before marking complete:

- Parse all generated JSON/JSONL artifacts.
- Recompute strict source hashes.
- Verify exactly 3 target rows and no extra accepted rows.
- Verify terminal G12 decision counts.
- Verify no unsafe true flags and no forbidden result/account/order/history fields.
- Verify no denominator movement, result labels, validation claims, promotion claims, or live effect.
- Run `python -m py_compile` or an equivalent syntax/compile check if Windows pycache permissions block direct py_compile.
- Run focused pytest.
- Run upstream May 3 verifier/test where practical.
- Run committed-diff live-surface check scoped to this G12 audit lane, while recording unrelated workspace dirt separately.
- Regenerate `LIVE_STATE.md` and confirm research context freshness or record exact reason.

## Completion Standard

Do not complete with a generic acceptance. Complete only after G12 has independently audited source/session/proxy/no-leak/duplicate boundaries and produced a terminal decision:

- `ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY`
- `BLOCK_WITH_EXACT_NEXT_SOURCE`
- `REJECT_INVALID_SOURCE_CONTROL_PROOF`

Any acceptance must explicitly preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, no result labels, no denominator movement, and no automatic opening of result lanes.


# LAND A/B supplement — full suite at the actual merge point (4a932989c)

The A0 fence receipt (`SESSION_FA_AB_RECEIPT.md`) covered `82a1482de`. Six commits landed
after it on `phase19/fa2-integration` (Phase C repair set, the arm-(v) breaker hook + its
funnel seam fix, the session iteration-ledger rows). Per H2 ("A/B before claiming no
regressions"), the full suite was re-captured at the merge point itself:

- **Head**: `4a932989c` (dirty: untracked run routes only). Capture:
  `FAILSET_FA2_LAND.json` beside this file.
- **Totals**: 13,368 passed / **1 failed** / 131 skipped / 32 xfailed.
- **Failure set**: `tests/research_infra/test_session_fg_integration.py::
  test_session_fg_integrated_evidence_and_default_off_boundaries`
  (`AssertionError: ['phase1.source_head']`) — present in the fence's bad-before AND
  bad-after sets; pre-existing on both sides, not FA's.
- The fence's other two members both PASS at this head: `test_verification_retains_no_rows`
  (the registered KNOWN_LOAD_FLAKES member) and
  `test_streaming_archive_seal_settles_before_publishing_segment`.
- The capture tool self-marked `usable_as_baseline=false` because its summary-line parser
  recovered 0 ids for the 1 reported failure; the failing id above was identified by
  direct targeted re-run (3.75 s, `1 failed, 2 passed`) of the fence's three named tests.

**Verdict: zero regressions against both the sealed baseline and the fence; failure set
is a strict subset of both; +64 net passing vs the fence. LAND-grade.**

Owner authorization: Borhen, 2026-08-05 — "ok i approve everything please proceed as
proposed, land it …" (quoted in full in `SESSION_MARCH_EXECUTOR.md`).

# LTO031 / LTO032 Databento Credit Replay Manifest Result - 2026-05-06

**Status:** `DATABENTO_CREDIT_REPLAY_MANIFESTS_READY_ESTIMATE_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Result

P2 Databento replay requests are predeclared under existing-credit-only caps. No request is fetch-ready yet because vendor cost estimates were not run in this phase.

## Counts

- Requests: `8`
- Request status counts: `{'BLOCKED_ALIGNMENT_POLICY_BEFORE_ESTIMATE': 1, 'BLOCKED_PROXY_TRANSFER_REVIEW_BEFORE_ESTIMATE': 1, 'BLOCKED_SOURCE_DEFINITION_BEFORE_ESTIMATE': 1, 'DEFERRED_UNTIL_MBP10_LEAVES_QUEUE_QUESTION': 1, 'WAITING_FOR_COST_ESTIMATE': 4}`
- Request schema counts: `{'mbo': 1, 'mbp-10': 4, 'trades': 3}`
- Fetch-ready requests: `0`
- Local raw Databento files inventoried: `113`
- Local raw Databento size MB: `3590.279098`

## Boundaries

- Estimate-before-fetch is enforced by manifest invariants.
- Live Databento collector remains disabled.
- Decision-time features and post-event labels are separated in every request.
- SI/XAGUSD, USDJPY/6J, GBPUSD/6B, and NAS100/MBO queue follow-up retain explicit blockers.

## Verification

- `python -m py_compile src/research_infra/lto_databento_credit_replay_manifests.py scripts/build_lto031_lto032_databento_credit_replay_manifests.py`
- `python -m pytest tests/test_lto_databento_credit_replay_manifests.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase3_lto_databento_credit_manifests`

## NO_PROMOTION_VERDICT

This is replay planning only. No Databento call or live behavior change occurred.

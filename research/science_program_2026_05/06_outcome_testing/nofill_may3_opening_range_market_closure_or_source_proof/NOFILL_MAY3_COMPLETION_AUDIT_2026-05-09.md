# NOFILL May 3 Completion Audit

- Objective satisfied: `True`
- Target rows: `NOFILL-CAT-ROW-0049, NOFILL-CAT-ROW-0050, NOFILL-CAT-ROW-0051`
- Terminal status counts: `{'MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL': 3}`
- Labels assigned: 0.
- Rows moved into accepted denominator: 0.
- Reject total preserved outside labels/denominators: 65.
- Live effect: false.
- Promotion verdict: `NO_PROMOTION_VERDICT`.

## Required Verification Commands

- `python -m py_compile research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/build_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py`
- `python research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py`
- `python -m pytest research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/test_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py -q`

## Observed Verification

- `python -m py_compile ...`: PASS.
- `python ... verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py --json`: PASS (`ok=true`, row_count=3, source_hash_records_checked=36).
- `python -m pytest ... -q`: PASS (`5 passed in 0.46s`).
- Bare `pytest` was not on PATH in this shell; the Python module entrypoint passed.

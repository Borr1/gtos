# Why the A/B scope is 37 files and the change touched 39

`scripts/pytest_failset.py scope --base e19a2bb49` reaches **39** test files by import closure.
Two of them — `tests/ultimate_book/test_ce_entry_hour_lever.py` (35 tests) and
`tests/research_infra/test_ce_rule_amendment.py` (18 tests) — **do not exist at the base
commit**, so they cannot appear on the before side of a comparison. The tool refuses an A/B
across differing scopes, which is correct: a receipt whose two sides ran different files is not
a comparison. `--scope-difference-justification` was available and deliberately not used —
re-running the after side on the SHARED scope is a real comparison, and a justification is a
reason to accept a weaker one.

So `SESSION_CE_AB.md` is the shared **37-file** A/B: **0 bad → 0 bad, 0 regressed, 846 → 846
passing.** The two new files are reported separately as **+53 net new passing**, which is a
count of new coverage and not a claim about regression.

**The before side is a FULL copy-back, and the first attempt was wrong in a way worth
recording.** Restoring only the changed *source* files left `IMPLEMENTATION_STATE.md` and
`tests/test_implementation_state_block_citations.py` in mixed states — HEAD's blocks against
the base's `IN_FLIGHT_WAVE_RANGES` — and produced **one** failure that belongs to neither side.
The correct copy-back restores **every** path in `git diff --name-status <base> HEAD`: all 8
modified paths restored, all 26 added paths removed. At that state the before side is
**0 failed / 846 passed / 1 xfailed**, which is the ZERO baseline exactly.

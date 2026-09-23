# Session CL A/B scope and copy-back controls

The authoritative failure-set result is the tool-emitted `gtos-ab-receipt-v1` fence in
`SESSION_CL_AB_RECEIPT.md`. This note records how its two same-commit captures represent
different disk states.

- Baseline revision: Session CL's original parent `83867e65f` (the wave-16a ZERO train).
- Before: every one of the 21 `83867e65f..c13322ceb` session paths was copied back to the
  baseline blob; HEAD-added files were moved to a temporary reversible holding tree. A
  path-restricted `git diff --quiet 83867e65f` passed before pytest.
- After: a `git archive HEAD` backup restored all 21 paths; a path-restricted
  `git diff --quiet HEAD` passed before the second capture and again after the command's EXIT
  trap. HEAD and the branch never moved; `git checkout` was never invoked.
- The tool-derived seven-test scope contained three HEAD-only CL tests. A same-scope before
  cannot execute files that do not exist, so those three were excluded from both shared
  captures and run separately on HEAD: **14 passed**. Three existing consumers of the
  modified official training-lane JSONLs were conservatively added instead.
- Shared scope: the three existing training-lane tests, the block-citation guard, and the
  three activation-carry lineage suites. Result: **215 passed before, 215 passed after, 0 bad
  to 0 bad, 0 regressed**.
- Both captures say `dirty`: the before side is intentionally copy-backed, while the after
  side retains only the mandatory-preflight regeneration of `.context/LIVE_STATE.md`. That
  path predated CL's implementation and was never staged.

No broker-capable script, VPS path, protected config or March outcome was involved in either
capture.

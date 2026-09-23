# Wave-21 follow-up merge — three delivered branches onto main (2026-08-11)

Integration of the three pushed wave-21 follow-up branches into `main` behind the full
fence discipline. Base: `origin/main` @ `56d2e27d9`; during the A/B captures main
moved by exactly one commit (`0b64b945d`, BAR-3 ratification — a 17-line md under
`phase21/full_system_coherence/outcome_authority/`, zero paths shared with the
branches, no import edge into the suite), sync-merged as `a8029cd06` before push, and
every fence below was re-verified against `0b64b945d` at the final tip. Context:
fresh full (non-sparse)
worktree `wave21-followup-merge-20260811`, branch
`integration/wave21-followup-merge-20260811`; both A/B captures ran in this same
worktree, same interpreter (`/opt/homebrew/opt/python@3.14/bin/python3.14`, pytest
9.1.0), `__pycache__`/`.pytest_cache` cleaned before each side, protocol env
(`env -u FORCE_COLOR NO_COLOR=1 PY_COLORS=0 PYTHONDONTWRITEBYTECODE=1`,
`--continue-on-collection-errors`), tool `scripts/pytest_failset.py` sha256
`35dd35eb17cc…` identical at both sides (no branch touches `scripts/`).

## 1. What merged

| merge commit | branch | content commits | summary |
|---|---|---|---|
| `2972281f4` | `w21-geometry-bound-outcome-model` | `5f1202cff`, `4acaea684`, `a11ee61ff` | Geometry-bound outcome model V1: hash-sealed two-stage Jeffreys calibration artifact (`GEOMETRY_BOUND_OUTCOME_MODEL_V1.json`, 503 KB) + `src/research_infra/geometry_bound_outcome_model.py` (validator/loader) + the acceptance path in the truth strip (`wave21_full_flow_truth.py`: accepted disposition + preserved-calibration predicate) + default-off runtime wiring (`wave21_geometry_bound_outcome_model` key) + calibration-key hardening + 1,080 lines of tests. Branch carried its own A/B fence receipt (0 regressed by failure set). |
| `fcef2d7a6` | `wave21/cm-cell-pricing` | `fa8bb78b2` | CM cell priced on the corrected-quote walker: `R1_CM_CELL_PRICING_V1.{json,md}` (re-arm gate input; `crypto @ stop_1p5x_target_scale` vs shipped 4R vs surface best over the r1 crypto population) + `stop_mult` parameterization of `r1_frontier_surface_sweep.walk()` (docs/phase20/receipts/r1/) + behavioral pins `tests/research_infra/test_r1_cm_cell_walker.py`. |
| `8e7b98ee1` | `wave21/post-integration-measurements` | `0a6f7332d`, `1135b387c`, `6272929e9` | W7 post-integration recost rerun receipt (runner unchanged at main@2edefd48a; headline NOT_EVALUABLE stands; cost authority refuses 1662/3396 rows fail-closed; verifier repaired to verify refusal rows) + the compose repair (§3) + post-integration comparator receipt (23,309 candidate identities byte-stable across three days; delta isolated to the selector/package-router layer; independent verification REFUSED at a named producer/verifier record-shape divergence — left open for the owning lane). |

Total: 38 files, +40,189/−21,348. All three branches base off `2edefd48a`;
`2edefd48a..56d2e27d9` (7 commits, APRMAY prereg V1.1–V1.6 + April/May read receipt)
shares **zero paths** with the branches. All three merges were conflict-free.

**Double-merge verification.** Both the geometry branch and the compose repair touch
`src/research_infra/v4_timewarp_simulated_live_research_loop.py` (distant regions:
imports + ~:56750–56950 vs ~:93444–95390). The merged file was verified **byte-exact**
against base@2edefd48a + geometry patch + compose patch applied sequentially, and
compiles (`py_compile`) together with `wave21_full_flow_truth.py`,
`geometry_bound_outcome_model.py`, and the modified walker.

## 2. Fences

1. **Live-path byte identity — PASS.**
   `git diff origin/main..HEAD -- src/components/ultimate_book/book_owner.py run_book.py
   src/execution.py src/components/selector_v4.py src/mt5/mt5_real.py config/` is
   **EMPTY (0 bytes)**. The geometry wiring key `wave21_geometry_bound_outcome_model`
   appears in **zero** committed config files at merged HEAD (`git grep` under
   `config/`: no hits; the key exists only in the timewarp module, the wiring test, and
   the artifact doc) — default-off holds structurally, not just by intent.
2. **Blob gate — PASS.** Zero new blobs ≥90 MB in `origin/main..HEAD`; largest new blob
   is 4.32 MB (`v4_timewarp_simulated_live_research_loop.py` itself), largest new data
   file 2.42 MB (`W7_CURRENT_RECOST_V1.json`). No new file matches any LFS pattern
   (checked with `git check-attr`), so `GIT_LFS_SKIP_PUSH=1` on the push is
   belt-and-suspenders, not load-bearing.
3. **Full-suite failure-set A/B — PASS (zero regressed by identity).** See §4.
4. **Single-application — PASS.** The compose repair's conditional
   (`occurrence_contract_claimed_for_window = any(`) appears **exactly once** in the
   merged timewarp module; the geometry model's disposition accepting path
   (`== GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS` in
   `_hash_bound_probability_truth_disposition`, :56883) appears **exactly once**.

## 3. R2 bound-file register note (CN precedent — no reseal)

Files changed across the three branches that sit in the R2 decision contract's register
(`B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`):

| bound file | register group | changed by |
|---|---|---|
| `src/research_infra/v4_timewarp_simulated_live_research_loop.py` | `common_behavior_inputs` (43-path input register) — **and** second-bound from inside the executing runner via `code_authority_paths` (`src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py:1408`) | `w21-geometry-bound-outcome-model` (`5f1202cff`, `4acaea684`) and `wave21/post-integration-measurements` (`1135b387c`, the compose repair) |

That is the **only** register-bound file the three branches touch: the cm-cell-pricing
branch changes docs + tests only; `wave21_full_flow_truth.py` and the new
`geometry_bound_outcome_model.py` are in neither the input register nor
`code_authority_paths`.

**Drift status, measured:** the path was **already drifted** from R2's sealed hash
before this merge — R2 expects `824cf572…`; base `2edefd48a` and `origin/main`
`56d2e27d9` both carry `8ade9619…`; merged HEAD carries `70b3abef…`. This merge
therefore extends a standing forward drift; it does not open a new seal-break class.
Per the CN-precedent forward rule (owner word, recorded at the CN ceremony and applied
at every wave since): **no reseal now; any future sealed replay regenerates its
decision contract first.** The parked campaign's ~36 MH resume option was already dead
by CJ's seal break, as priced. R1 (January's sealed contract) is untouched.

## 4. Full-suite failure-set A/B (fence 3, verdict of record)

| capture | commit | failed | error | bad (set) | passed | skipped | xfailed |
|---|---|---:|---:|---:|---:|---:|---:|
| A (baseline) | `56d2e27d9` origin/main | 38 | 0 | 38 | 13,786 | 134 | 32 |
| B (merged) | `8e7b98ee1` | 38 | 0 | 38 | 13,810 | 134 | 32 |

Diff (`scripts/pytest_failset.py diff`, failure identity = normalized node ID):
**38 bad -> 38 bad with IDENTICAL failure-identity sets — unchanged 38, fixed 0, REGRESSED 0, diff exit 0. Net +24 new passing tests (13,786 -> 13,810), skips constant at 134.**

Known-flake adjudication per the registered list (`KNOWN_LOAD_FLAKES` in
`scripts/pytest_failset.py` — 4 registered entries): not exercised — zero regressed identities, so the load-flake partition had nothing to adjudicate (none of the 4 registered names moved in either direction).

**Baseline validity across the mid-train main movement:** capture A ran at
`56d2e27d9`; `56d2e27d9..0b64b945d` is one docs-only commit adding a single `.md`
file outside the `tests/` collection scope with no import edge into any test — it
cannot change a failure identity, so A remains the valid baseline for the pushed
tip (the same blast-radius reasoning `pytest_failset.py scope` encodes). Fences 1,
2 and 4 were re-run against `0b64b945d` at the final tip: identical results (0
bytes; 0 blobs; 1 and 1).

Captures committed in full at
`docs/audits/fable5-vision-audit-20260725/phase21/receipts/wave21_followup_merge_ab/`
(`A_56d2e27d9.json`, `B_8e7b98ee1.json`, tool-emitted `AB_RECEIPT.md` with embedded
capture hashes).

## 5. Obligations discharged / left open

- The post-integration branch's own receipt records that its compose repair "owes a
  full-suite A/B at merge time" — **discharged here** (§4).
- The comparator receipt's OPEN question — whether the selector/package-router
  disposition movement post-integration is the intended composed contract or a defect —
  remains **open for the owning lane**; nothing in this merge closes it, and the
  receipt says so itself (`POST_INTEGRATION_COMPARATOR_V1.md` §4).
- The independent-verifier REFUSAL on the three fresh comparator runs
  (producer/verifier record-shape divergence) likewise remains with the owning lane.
- The geometry-bound outcome model ships **default-off**; supplying
  `wave21_geometry_bound_outcome_model` (path + artifact sha256) per run is a research
  opt-in and no committed config does so.

## 6. Not touched

Live path (fence 1 empty), `CLAUDE.md`, the aprmay/feb candidate roots under
`/private/tmp`, reserve days, READ_RESTRICTED files, R1/R2 contract JSONs, the two
LFS-bound ledger paths in the main repo.

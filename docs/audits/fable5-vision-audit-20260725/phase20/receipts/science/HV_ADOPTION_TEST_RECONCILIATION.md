# HV Adoption — Test Reconciliation Receipt (FA continuation, Phase A0 item 2)

Date: 2026-08-03. Worktree: `/Users/borr/GTOSActive/worktrees/fa2-integration-20260803`
(branch `phase19/fa2-integration`). Agent: Fable repair agent (HV adopt-or-kill).

## Verdict: ADOPT-READY

`src/research_infra/p1_offline_complete_path_runner.py` was **not modified by one byte**.
All 10 failures were TEST-STALE: fixtures written against an earlier runner contract that
HP's landed commit `9059cfa06` ("fix(phase20): accept hash-proven sparse M1 bars") and the
runner's subsequent hardening legitimately superseded. No RUNNER-DEFECT was found. The
runner's refusal semantics, fail-closed drift checks, and the default-off `enabled` gate
are all untouched and are all still exercised by the passing suite (the default-off test,
both marker/staging refusal tests, and the preflight refusal test pass against the real
code paths).

File states at close (sha256):

- `src/research_infra/p1_offline_complete_path_runner.py` —
  `b237010ad2b29cb6f2ef87fa9de57cbad9c703e1c254ccfc582280f5615563d2` (HV's bytes, unmodified)
- `tests/research_infra/test_p1_offline_complete_path_runner.py` —
  `e37c752979f68641b148c0ec27e2b01e69c00b518a2c1dc0b009c445b6a99326` (repaired)

## Per-test classification

| # | test | classification | root cause | repair |
|---|---|---|---|---|
| 1 | `test_m1_no_touch_can_prove_no_fill` | TEST-STALE | `_m1_authority_complete` (runner.py:583-634) now accepts a binding only with a `completion_contract` mapping: schema `gtos.p1-hash-bound-sparse-m1-completion.v1`, a window in `LANE_MANIFEST_BINDINGS`, and per-window `path_manifest_sha256`/`lane_manifest_sha256` matching module constants (runner.py:596-616). This is HP's landed M1-acceptance rule (9059cfa06): sparse M1 is proven by exact source hashes + declared bounds, never by one-bar-per-minute. The old fixture binding carried `closed_session_complete: True` — a field the runner no longer reads — so the binding failed closed to `NOT_EVALUABLE_M1_SOURCE_OR_SESSION_GAP`. | Fixture `_m1_binding` rebuilt with `_completion_contract(window)` mirroring the runner's own emitter (runner.py:2155-2169); dead `closed_session_complete` dropped. Test file :83-110. |
| 2 | `test_m1_touch_is_not_evaluable_not_fill` | TEST-STALE | Same as #1 — the source-gap refusal fired before the touch classification could. | Same helper repair; no per-test edit needed. |
| 3 | `test_sparse_m1_is_valid_only_under_literal_bound_closure` | TEST-STALE | Same as #1. Note the test's first half (no bindings → `NOT_EVALUABLE_M1_SOURCE_OR_SESSION_GAP`) already passed and still does — the "without closure" arm needed no change. | Same helper repair. |
| 4 | `test_cross_month_stitching_is_sorted_and_deterministic` | TEST-STALE | Same as #1, plus each cross-month binding must carry its own window's manifest hashes. | April part binds `window="april"`, May part `window="may"` (test file :296-300). Span-coverage logic (runner.py:622-634) unchanged and still exercised across the month boundary. |
| 5 | `test_exit_consumes_only_points_strictly_after_fill` | TEST-STALE | Two contract evolutions: (a) `evaluate_tick_exit` refuses `horizon_terminal_mark` whenever the marking quote is before the horizon — `shared_hdf_tick_path_truncated_before_horizon` (runner.py:800-801), mirrored for M1 at :868-869: a horizon claim from a path that ends early is truncated evidence. (b) In the shared overlay a path that actually reaches the deadline exits as `time_box` (exit_overlay.py:415-432); `horizon_terminal_mark` (exit_overlay.py:480-493) is definitionally the truncated-path outcome. The fixture's last tick sat 118 min before the horizon and expected the now-refused reason. | Terminal quote moved to the horizon; expected reason `horizon_terminal_mark` → `time_box` (test file :329-348). Discrimination preserved: the tick at exactly `fill_time` still reads −1.0R and would exit `hard_stop` if the strictly-after-fill filter (runner.py:765) ever admitted it. |
| 6 | `test_terminal_quote_side_is_bid_for_long_and_ask_for_short` | TEST-STALE | Same truncation guard as #5. | Single quotes moved to the horizon for both sides (test file :356, :361). Side-selection discrimination preserved: wrong-side quote reads 20.0R, assertions demand 1.0. |
| 7 | `test_run_once_streams_exact_five_outputs_and_atomic_install` | TEST-STALE | Three fixture-vs-runner interface gaps: (a) `run_once` now reads pool/sidecar containers through `_read_bound_bytes` (runner.py:2487-2492) — symlink guard `_reject_symlink_components` (runner.py:330-343), lexical containment, O_NOFOLLOW open, sha256+size, TOCTOU inode recheck — so a POOL_BINDINGS entry naming a nonexistent `synthetic-pool.jsonl.gz` refuses `path_component_missing` before the old `_iter_full_jsonl` monkeypatch could intercept (its signature is now `(payload: bytes, *, label)`, runner.py:1928). (b) `_window_authority` consumers now require `lane_m1_sources`, `lane_tick_sources`, `path_manifest_sha256`, `lane_manifest_sha256` (runner.py:2495-2496, :2607-2613); `_m1_binding` is called `(record, lane_record, *, window, path_manifest_sha256, lane_manifest_sha256, cache)` (runner.py:2107-2115) and must emit the completion contract. (c) The test asserted `row["redacted_account"]["economics"] is None`, but the runner **forbids that key outright** — `redacted_account_economics_key_forbidden` via `_contains_mapping_key` (runner.py:2549-2550, :2584-2585, :1505-1506); absence is the guaranteed contract. | Fixture writes real gzip containers under `tmp_path` with true digests/sizes (`_write_synthetic_gzip`, test file :442-446) and installs a redirect shim that routes only the two synthetic basenames to `tmp_path` **through the real `_read_bound_bytes` with `root=tmp_path`** (test file :537-545) — every verification (symlink, containment, digest, size, inode) stays live. `_window_authority`/`_m1_binding` mocks re-signed to the current interfaces, emitting the completion contract with the real january manifest hashes (test file :551-598). Economics assertion flipped to key-absence (test file :630). |
| 8 | `test_synthetic_transaction_descriptors_are_deterministic` | TEST-STALE | Same fixture gaps as #7. | Same fixture overhaul; per-run container filenames (`{name}-synthetic-pool.jsonl.gz`) because `DeterministicJsonlGzipWriter` opens `"xb"` and the test runs the fixture twice in one `tmp_path`. Determinism assertions unchanged and pass (content-addressed digests are filename-independent). |
| 9 | `test_crash_after_marker_preserves_marker_and_staging` | TEST-STALE | Same fixture gaps as #7 — the crash raiser lived in the old path-based `_iter_full_jsonl` monkeypatch, which the bound-bytes read now precedes. | Crash raiser moved to a bytes-signature `_iter_full_jsonl` monkeypatch (test file :546-550); it still fires after the marker write (runner.py:2451) and staging mkdir (runner.py:2456), preserving the test's crash-window semantics. |
| 10 | `test_preexisting_output_parent_refuses_in_preflight` | TEST-STALE | `preflight` now reconciles `denominator["authority_counts"]` against `EXPECTED_AUTHORITY` (runner.py:1796-1797) **before** the output-parent check (runner.py:1810-1811); the mocked `_source_control_proof` predates the key (real return shape: runner.py:1722-1731). | Mock denominator gains `"authority_counts": runner.EXPECTED_AUTHORITY` and `"false_april_tick_references": []` (test file :727-728). The test still proves the output-parent refusal itself against real code. |

## Changed hunks (all in `tests/research_infra/test_p1_offline_complete_path_runner.py`; runner untouched)

| file:line (post-repair) | one-line why |
|---|---|
| tests/.../test_p1_offline_complete_path_runner.py:83-110 | `_completion_contract` helper + `_m1_binding` carries the hash-bound sparse-M1 completion contract (HP's 9059cfa06 rule; mirrors runner.py:2155-2169) |
| tests/.../test_p1_offline_complete_path_runner.py:296-300 | cross-month bindings carry their own windows' manifest hashes (april/may) |
| tests/.../test_p1_offline_complete_path_runner.py:329-348 | terminal tick at horizon; expected reason `time_box` per exit_overlay.py:415-432; truncation guard runner.py:800-801 documented |
| tests/.../test_p1_offline_complete_path_runner.py:350-363 | side-selection test quotes moved to the horizon (same guard) |
| tests/.../test_p1_offline_complete_path_runner.py:442-446 | `_write_synthetic_gzip`: real deterministic gzip containers with true sha256/size |
| tests/.../test_p1_offline_complete_path_runner.py:449-599 | fixture overhaul: real bound files under tmp_path, `_read_bound_bytes` redirect shim keeping all verification live, `_window_authority`/`_m1_binding` mocks re-signed to current interfaces, crash raiser on bytes-based `_iter_full_jsonl` |
| tests/.../test_p1_offline_complete_path_runner.py:626-630 | redacted_account economics asserted **absent** (runner forbids the key: runner.py:2549-2550, :2584-2585) |
| tests/.../test_p1_offline_complete_path_runner.py:720-729 | preflight denominator mock gains `authority_counts` + `false_april_tick_references` (matches real shape runner.py:1722-1731) |

## What was deliberately NOT done

- No edit to the runner. No refusal was weakened, no gate loosened; the fixtures were
  brought up to the runner's contract, never the reverse.
- The synthetic-transaction shim does **not** neutralize `_read_bound_bytes` — it re-roots
  the two synthetic containers to their true tmp_path location and delegates to the real
  reader, so digest/size/symlink/TOCTOU verification still executes on every test run.
- `run` stays default-off (`test_run_is_default_off_before_any_anchor_or_marker` passes
  against the real `_require_run_anchors`). The runner remains broker-inert
  (`test_no_forbidden_import_order_send_or_protocol_cell_mapping` passes). The output hold
  `/Users/borr/GTOSActive/p1-offline-result-hold-20260802` was neither created nor referenced.
- March 2026 outcome data and live-forward (2026-07-29+) outcome data were not read.

## Final pytest results

Target file:

```
$ python3 -m pytest tests/research_infra/test_p1_offline_complete_path_runner.py -q
33 passed, 1 warning in 0.36s
```

Neighbouring P1 files (no collateral damage):

| file | result |
|---|---|
| tests/research_infra/test_p1_upstream_packet_verifier.py | 42 passed |
| tests/research_infra/test_p1_upstream_m1_provenance_verifier.py | 17 passed |
| tests/research_infra/test_p1_upstream_reconstruction.py | 19 passed |
| tests/research_infra/test_session_hm_p1_adapter_falsifier.py | 23 failed, 47 passed — **all 23 pre-existing** |

Pre-existence proof for the HM falsifier failures: the four neighbour files were run with
HV's two files temporarily removed from the tree and again with them present; the sorted
`FAILED` sets are **byte-identical** (23 rows) in both states, and no neighbour imports
`p1_offline_complete_path_runner`. The failures are first-miss stage-attribution drift
inside the HM falsifier's own fixtures (e.g. expects `hdf_exit_or_terminal`, observes
`candidate_generation`) — out of this task's file scope.

Collection: `tests/research_infra/` collects **2,667 tests** cleanly with one pre-existing,
unrelated collection error — `tests/research_infra/test_session_fb_sol_grid.py` (committed
`19d85226e`) raises `FileNotFoundError` at import for
`research/operations/wave19_sol_repair_2026_08_01/grid/session_fb_sol_grid.py`, which is
absent in this worktree. It predates the HV adoption, does not involve either commissioned
file, and touching it would exceed this task's file constraints.

Combined single-session run (target + four neighbours): `23 failed, 158 passed` — the same
23, i.e. no cross-module monkeypatch pollution from the repaired fixtures.

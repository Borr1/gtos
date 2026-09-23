# Session HDF exact same-test A/B

**Exact HC `82c41b122`: 13 bad -> final HDF `14c0e2ad1`: 0 bad.**
All 13 HC failures are fixed; all four HC passes remain passes; zero nodes regress.

This replaces HDC's non-discriminating `0 bad -> 0 bad` broad capture for the
newly added attacks. The single test file, command text, Python/pytest versions,
and environment shape are identical. Only `$PWD` changes to select the clean
detached implementation node, and the first test proves implementation imports
resolve under that selected root.

| | exact HC | exact HDC diagnostic | final HDF |
|---|---:|---:|---:|
| commit | `82c41b122364c4ef56612a5468867fe796bd6c1a` | `32d045a732467e439ba1807db0ce786e8a11e53b` | `14c0e2ad1c4390ba78412832179d9b1e1dbf16f2` |
| clean detached worktree | yes | yes | yes |
| captured UTC | 2026-08-01 15:11:01–15:11:09 | 2026-08-01 15:11:28–15:11:36 | 2026-08-01 15:11:14–15:11:21 |
| passed | 4 | 10 | 17 |
| failed | 13 | 7 | 0 |
| errored / skipped | 0 / 0 | 0 / 0 | 0 / 0 |
| exit code | 1 | 1 | 0 |
| real wall seconds | 7.64 | 7.70 | 7.65 |

## Tool-emitted capture

```json
{
  "schema": "gtos-ab-receipt-v1",
  "session": "HDF",
  "comparison": "exact_hc_vs_final_hdf_same_test_bytes",
  "test_source": {
    "path": "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py",
    "sha256": "f404d464a6b5141856752f4d47999c64df7c4a1e9d576994b06358f60b4e3228",
    "collected_node_count": 17
  },
  "command": "env PYTHONDONTWRITEBYTECODE=1 HDF_REPO_ROOT=\"$PWD\" PYTHONPATH=\"$PWD\" /usr/bin/time -p python3 -m pytest -q -c /dev/null --rootdir=\"$PWD\" --confcutdir=\"$PWD\" /Users/borr/GTOSActive/worktrees/wave20-exit-capture-science-falsifier2-20260801/tests/research_infra/test_session_hdf_exit_capture_falsifier2.py",
  "environment": {
    "python": "3.14.4",
    "pytest": "9.1.0",
    "platform": "Darwin 25.5.0 arm64",
    "PYTHONDONTWRITEBYTECODE": "1",
    "HDF_REPO_ROOT": "$PWD",
    "PYTHONPATH": "$PWD",
    "pytest_config": "/dev/null",
    "import_binding_proof_node": "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_implementation_imports_are_bound_to_selected_repository"
  },
  "before": {
    "commit": "82c41b122364c4ef56612a5468867fe796bd6c1a",
    "commit_subject": "docs(phase20): close HC exit capture repair",
    "worktree": "/private/tmp/gtos-hdf-hc-82c41b1",
    "detached": true,
    "dirty": false,
    "capture_start_utc": "2026-08-01T15:11:01Z",
    "capture_end_utc": "2026-08-01T15:11:09Z",
    "wall_seconds_real": 7.64,
    "exit_code": 1,
    "totals": {
      "passed": 4,
      "failed": 13,
      "errored": 0,
      "skipped": 0
    }
  },
  "hdc_diagnostic": {
    "commit": "32d045a732467e439ba1807db0ce786e8a11e53b",
    "commit_subject": "docs(phase20): close HDC exit capture falsifier",
    "worktree": "/private/tmp/gtos-hdf-hdc-32d045a",
    "detached": true,
    "dirty": false,
    "capture_start_utc": "2026-08-01T15:11:28Z",
    "capture_end_utc": "2026-08-01T15:11:36Z",
    "wall_seconds_real": 7.70,
    "exit_code": 1,
    "totals": {
      "passed": 10,
      "failed": 7,
      "errored": 0,
      "skipped": 0
    }
  },
  "after": {
    "commit": "14c0e2ad1c4390ba78412832179d9b1e1dbf16f2",
    "commit_subject": "fix(phase20): harden exit capture science",
    "worktree": "/private/tmp/gtos-hdf-final-14c0e2a",
    "detached": true,
    "dirty": false,
    "capture_start_utc": "2026-08-01T15:11:14Z",
    "capture_end_utc": "2026-08-01T15:11:21Z",
    "wall_seconds_real": 7.65,
    "exit_code": 0,
    "totals": {
      "passed": 17,
      "failed": 0,
      "errored": 0,
      "skipped": 0
    }
  },
  "bad_before": 13,
  "bad_after": 0,
  "unchanged_bad": [],
  "fixed": [
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_duplicate_declaration_digest_is_rejected",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_authority_is_deeply_immutable_after_construction",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_files_require_exact_schema_and_valid_seal[<lambda>-spec seal missing or invalid0]",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_files_require_exact_schema_and_valid_seal[<lambda>-spec seal missing or invalid1]",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_files_require_exact_schema_and_valid_seal[<lambda>-schema]",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_date_aliases_are_refused_instead_of_truncated",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_authority_refuses_partial_malformed_empty_and_one_day_shapes",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_segmented_sign_null_has_capture_start_origin_and_known_exact_answer",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_exact_sign_tail_retains_mathematically_tied_states",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_segmented_sign_null_monte_carlo_transition_is_seeded_and_explicit",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_cs_economics_nulls_and_59_member_bill_reproduce_from_first_principles",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_all_3200_fast_and_reference_rows_match_the_third_oracle",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_terminal_observation_completes_trigger_partial_and_ratchet_state"
  ],
  "regressed": [],
  "hdc_bad_nodeids": [
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_authority_is_deeply_immutable_after_construction",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_files_require_exact_schema_and_valid_seal[<lambda>-spec seal missing or invalid0]",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_files_require_exact_schema_and_valid_seal[<lambda>-spec seal missing or invalid1]",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_files_require_exact_schema_and_valid_seal[<lambda>-schema]",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_capture_date_aliases_are_refused_instead_of_truncated",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_exact_sign_tail_retains_mathematically_tied_states",
    "tests/research_infra/test_session_hdf_exit_capture_falsifier2.py::test_terminal_observation_completes_trigger_partial_and_ratchet_state"
  ]
}
```

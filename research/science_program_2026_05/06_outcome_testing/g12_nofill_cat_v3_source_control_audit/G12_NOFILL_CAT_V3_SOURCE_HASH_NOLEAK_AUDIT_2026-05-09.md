# G12 NOFILL CAT V3 Source Hash No-Leak Audit - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.

- Source hash records: `343`
- Strict matches: `340`
- Strict failures: `0`
- Missing records: `0`
- Mutable context mismatches: `2`
- Line-ending-only mismatches: `1`
- Source hash verdict: `PASS_WITH_MUTABLE_CONTEXT_AND_LINE_ENDING_EXCEPTIONS`

The one non-mutable byte mismatch is the V3 controlling prompt checked out with CRLF in this worktree while the originating worktree stored LF. Normalized UTF-8 content matches; no source-data hash mismatch was found.

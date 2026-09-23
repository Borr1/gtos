# Schema And Group Recompute Ledger

Independent recomputation imported `src.research_infra.forward_capture` and verified the code registry has exactly ten groups and that `SCID_GROUP_BUILDERS` matches `SCID_CAPTURE_GROUPS`.

The synthetic verifier input has ten rows, one per group, with `missing_groups=[]`, `failure_count=0`, safe flags false, and no forbidden keys. A temp candidate-writer run emitted nine candidate-time groups; a temp lifecycle run emitted the lifecycle group and validated cleanly.

Validator coverage includes required fields, unexpected fields, enum values, source-hash policy, as-of checks, duplicate-key drift checks, safe flags, and forbidden key/value rejection.

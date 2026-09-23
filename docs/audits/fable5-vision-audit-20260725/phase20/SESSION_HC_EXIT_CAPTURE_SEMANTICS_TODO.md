# Session HC — exit collision and capture-window semantics TODO

Scope is offline research infrastructure only. This session does not reopen any rejected exit cell,
change the predeclared CS fold plan, or grant activation authority.

## Frozen semantic contracts

1. **Exit collision contract.** Hard stops and activated protective floors retain their declared
   precedence. A hard target wins only when it is observed at a timestamp strictly earlier than the
   first executable deadline observation. The time box owns a target/deadline collision at the same
   tick or M1 timestamp. Because the hard target remains active, a deadline observation that gaps
   through the target is recorded as `time_box` but its favorable exit value is capped at the hard
   target. This rule is identical in the path evaluator and the vectorized FC evaluator.
2. **Capture authority contract.** Capture definitions and ordering, reserved blackouts, declaration
   identity, and declaration hashes are immutable `GateSpec` authority. Runtime capture input cannot
   define or replace that authority; at most it may assert byte-for-byte semantic equality. Moving- and
   block-null calculations operate on capture segments and never bridge the end of one capture to the
   start of a discontinuous later capture.

## TODO

- [x] Implement the exit collision contract at path and vectorized row level.
- [x] Seal capture authority and reject overlap, reorder, blackout, hash, identity, and replacement
      violations.
- [x] Segment null/block resampling at capture boundaries.
- [x] Preserve the CS fold plan and migrate its compact ratified gate invocation to sealed authority.
- [x] Add adversarial behavioral tests and run the relevant closure.
- [x] Prove the 214 published FC time-box outcomes and the CS rejection disposition are unchanged.
- [x] Run parent-versus-HEAD failure-set A/B and publish the Session HC result and completion receipt.

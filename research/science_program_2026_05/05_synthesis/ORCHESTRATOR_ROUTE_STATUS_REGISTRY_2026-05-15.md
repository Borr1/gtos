# Orchestrator Route Status Registry

Date: 2026-05-15
Status: active coordination control

Machine-readable registry:

`research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json`

## Current Anchor

- Accepted route: `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/`
- Terminal decision: `ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_NO_PROMOTION`
- Counts: `8` cards, `3,014` source candidates, `24,112` repaired rowset rows, `192,896` target-result rows, `162,336` computable rows, `30,560` fail-closed rows.
- Rowset hash: `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`

## Denominator Crosswalk

Use the JSON registry for source artifact paths and exact denominators. Do not mix these counts:

- `30,560`: target-result fail-closed cells in the 192,896-cell packet.
- `35,811`: fail-closed-or-excluded rows in sealed branch interpretation.
- `2,161`: aggregated fail-closed/source-repair ledger records.
- `44,103`: sealed primary branch records with concentration warning.
- `30,305`: sealed primary branch records below duplicate/effective-N floor.

## Active Wave

Launch pack:

`research/science_program_2026_05/06_outcome_testing/ready8_g12_accepted_execution_route_orchestration/READY8_G12_ACCEPTED_EXECUTION_ROUTE_LAUNCH_PACK_2026-05-15.md`

R1-R6 are not launched in the current main worktree. Their old temp worktrees and branches are absent as of the 2026-05-15 registry check. They are ready to launch only after prompt validation passes:

1. `R1_HAZ001_DENSITY`
2. `R2_UNC004_DISENTANGLE`
3. `R3_MAC_INVERSE`
4. `R4_HAZ005_TRANSITION`
5. `R5_FAIL_CLOSED_REPAIR`
6. `R6_CONTROLS_PLACEBO`

R7 is gated:

7. `R7_EXPANDED_PACKET`

R7 must not run until R1-R6 outputs are reviewed from disk and accepted or exactly bounded.

## Launch Board Fields

Every route row now tracks worktree existence, branch existence, prompt validation status, expected terminal artifacts, closeout state, artifact audit state, disk reviewer, and reviewed timestamp. A pasted closeout is not a reviewed route.

## Update Rule

Update the JSON registry after every route completion, merge, G12/G0 acceptance, material repair, or interpretation change. Do not rely on chat memory to track route state.

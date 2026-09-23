# Divergence matrix — how to run it

Two commands. The first generates the matrix for an arm; the second will not accept the arm without it.

```bash
# 1. generate, bound to one arm receipt
python3 -m src.research_infra.divergence_matrix \
  --arm-receipt <namespace>/B7_5_POST_ACCELERATION_ARM_RECEIPT.json \
  --output      <somewhere-outside-the-namespace>/DIVERGENCE_MATRIX.json \
  --markdown    <somewhere-outside-the-namespace>/DIVERGENCE_MATRIX.md \
  --live-rows   docs/audits/fable5-vision-audit-20260725/receipts/live_divergence_rows_w7.json  # optional

# 2. accept the arm — refuses without --divergence-matrix
python3 research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/verify_b7_5_post_acceleration_arm.py \
  --arm-receipt       <namespace>/B7_5_POST_ACCELERATION_ARM_RECEIPT.json \
  --decision-contract <the contract that arm cites> \
  --execution-seal    <the seal that arm cites> \
  --divergence-matrix <the file from step 1> \
  --output            <new path>/ARM_INDEPENDENT_VERIFICATION.json
```

**`--output` in step 1 must be outside the arm namespace.** `build_arm_artifact_inventory`
(`b7_5_post_acceleration_runner.py:366-369`) asserts the namespace holds exactly the eleven expected
artifact roles; a twelfth file there fails the arm with
`post_acceleration_output_artifact_set_invalid`.

## What is in this directory

The matrix rendered for the four sealed January arms, as the working corpus. Each is bound to its own
arm receipt root, so they are not interchangeable.

| arm | verdict | rows | blocking | unquantified | unknown |
|---|---|---:|---:|---:|---:|
| S0R0 | `REPLAY_R_IS_NOT_A_LIVE_CLAIM` | 54 | 41 | 12 | 2 |
| S1R0 | `REPLAY_R_IS_NOT_A_LIVE_CLAIM` | 54 | 41 | 12 | 2 |
| S0R1 | `REPLAY_R_IS_NOT_A_LIVE_CLAIM` | 54 | 41 | 12 | 2 |
| S1R1 | `REPLAY_R_IS_NOT_A_LIVE_CLAIM` | 54 | 41 | 12 | 2 |

## Reading a row

`direction` is `REPLAY_ONLY` / `LIVE_ONLY` / `BOTH_DIFFERENT` / `EQUIVALENT` / `UNKNOWN`, and
`UNKNOWN` is the fail-closed value — `EQUIVALENT` requires that nothing was unknown, which is Session
D's rule. `transfer_risk` says what the row does to the sentence *"replay R therefore live R"*.

`derivation.mode` is the one to check first. `DERIVED` means the value was read from a file at
generation time and the row carries that file's `sha256`. `DECLARED` means a human asserted it, and it
renders `[DECLARED]` everywhere. A declared row whose justifying document has gone missing degrades to
`UNKNOWN` rather than continuing to assert a fact whose source is gone.

`transfer_verdict` is **computed from the rows, never written.** Editing it and recomputing
`matrix_root_sha256` still fails acceptance.

Full schema: `../../LIVE_DIVERGENCE_ROW_SCHEMA.md`. Design notes: `IMPLEMENTATION_STATE.md` B70–B79.

## Known limitation

These four matrices are generated against **today's** config and source, not against the bytes the
January arms actually ran under. For arms sealed from here on, generate the matrix at acceptance time,
while the contract-bound inputs still match.

## Re-verifying a January arm: you need a `git show` first

The working-tree copy of the contract those receipts cite was overwritten on 2026-07-25, so the naive
command fails with `arm_receipt_decision_contract_mismatch`. The sealed bytes are in git — restore them
first (B76):

```bash
git -C /Users/borr/GTOSActive/repo show \
  015b09135:research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_POST_ACCELERATION_DECISION_CONTRACT.json \
  > /tmp/JANUARY_R1_CONTRACT.json
# sha256 must be 51becc82fc9668352f4e054df516c415fb51d9a34f17ac2cc0a3167812da374b
```

Then pass `/tmp/JANUARY_R1_CONTRACT.json` as `--decision-contract`. The execution seal
`JANUARY_EXECUTION_SEAL_R3.json` is unchanged and pins the same bytes independently.

# Session HDA falsification TODO

Builder claims are not findings. At the no-edit checkpoint I have independently reproduced only:

- branch `phase20/fidelity-authority-falsifier` at builder head
  `113b04891969213614d4635c1e609629c935f67c`, initially clean;
- HA's implementation is the two-commit range
  `ba3c18ddf268294813545501f84b635ccc0f25bb..113b04891969213614d4635c1e609629c935f67c`;
- CR's committed historical bytes describe 249/249 same-code-lineage replay-reference recall,
  null precision, and a frozen `NOT_EVALUABLE` disposition because the required RECORDED
  executable population does not exist;
- HA changes only walk-forward research code/tests and phase-20 evidence, not runtime, config,
  broker, VPS, token, or activation surfaces.

Before accepting HA, falsify these hypotheses:

1. Enumerate every public fidelity registrar, mutable register, lookup, clear, duplicate-registration,
   and fresh-process path; prove caller-count v1 evidence cannot emerge as v2 authority.
2. Exercise every `GateSpec` v1/v2 constructor, default/option, seal, read, write, tamper, and
   `GateResult` serialization route, including exact historical published seals.
3. Attempt authority relabeling across same-lineage, independent, and live references by changing
   labels, lineage values, nesting, paths, completeness attestations, and legacy serialization;
   separate machine-verifiable facts from the residual human independence claim.
4. Independently derive recall and precision denominators; attack duplicate and scalar identities,
   missing/extra/null fields, blank/invalid JSON, empty and incomplete populations, generated-only
   rows, source/manifest drift, relative/absolute paths, and symlinks where they affect authority.
5. Prove null precision fails exactly when a sealed precision floor requires it and that no other
   missing value becomes a pass.
6. Reproduce CR bytes/disposition and select an independent fidelity/walk-forward closure.
7. Challenge repair size and compatibility. If a defect is reproduced, capture the exact builder-head
   failure set before changing implementation, then make the smallest coherent repair and A/B it.

# Domain Syntheses

Each science lane writes one domain synthesis here, then appends mechanism rows, hypothesis rows, killed-route notes, experiment specs, and blockers to its lane-owned files.

Required lane outputs before completion:

- domain synthesis
- lane context ledger with search plan, sources read, evolving questions, and stale-context refreshes
- ambiguity ledger with pursued answers, blockers, sharper hypotheses, and owner questions if needed
- counter-evidence and decay-mode review
- mechanism rows using `science_mechanism_v1`
- hypothesis rows using `science_hypothesis_v1`
- killed-route notes with file/line or artifact evidence
- experiment prereg specs using `experiment_prereg_v1`
- source/budget blockers using `source_contract_v2` where applicable
- `goal_status_v1` update with files, tests, blockers, next questions, and commit SHA

`NO_PROMOTION_VERDICT` applies to every row and report.

# Wave 1A Saturation And Self Red Team

## Same-Evidence-Class Checks

- Broker denominator recomputed from broker truth, not copied from summary.
- Candidate payloads consumed from hydrated package/LFS evidence rather than sparse pointer files.
- Full candidate trade-record ledger preserved before summary rankings.
- Exact-R is emitted only when source-bound actual-R/cash-risk exists; otherwise proxy-R/source-gap is labeled.
- Missing historical intent/order/cost fields are not inferred from price movement.

## What Could Break This Lane

- A broker symbol alias mismatch could hide joins. Mitigation: GER40/GER30, NAS100/NDX100, UKOIL/UKOUSD, USOIL/USOUSD, and US30 aliases are normalized.
- LFS pointer checkout could look like missing data. Mitigation: the resolver records LFS object-store/package provenance.
- A ranked summary could replace full rows. Mitigation: matrix and ledgers preserve all broker and package candidate rows.
- Broker cash could be confused with R. Mitigation: broker cash, exact-R, and proxy-R fields are separate.

Unresolved source-gap inventory rows after local/LFS/package search: `0`.

Stop condition: same-evidence-class local evidence has been consumed into ledgers; non-generatable historical fields are converted into exact forward capture requirements.

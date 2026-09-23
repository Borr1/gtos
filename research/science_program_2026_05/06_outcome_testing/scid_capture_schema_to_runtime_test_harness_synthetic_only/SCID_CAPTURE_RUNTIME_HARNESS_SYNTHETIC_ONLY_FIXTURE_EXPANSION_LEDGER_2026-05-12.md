# Fixture Expansion Ledger

- Synthetic-only: `true`
- Accepted candidate-row boundary preserved: `3014`
- Capture groups covered: `10`
- Fixture cases: `109`
- Fixture row count: `117`
- Expected-validity outcomes matched: `True`

The harness generates two positive route variants for every capture group and
mutates every group through missing-field, stale-as-of, forbidden-identifier,
unsafe-flag, schema-version, unexpected-field, duplicate-key-drift, and
unavailable-source routes. Enum mutation is applied to every group with a
group-specific enum in the accepted schema.

# Wave 20 evidence preservation result

## Decision

**FA AND CS MACHINE-LOCAL EVIDENCE DURABLY PRESERVED; ORIGINALS RETAINED.**

The complete 76-file Session-FA Phase-1 route and both Session-CS raw April/May missed-opportunity
ledgers were copied to `/Users/borr/GTOSColdEvidence/wave20-preservation-20260801` using same-volume
APFS clone copies. No source file was moved or deleted.

Every FA source and destination file was checked against FG's committed relative-path, byte-length,
and SHA-256 manifest. All 76 matched. The copied manifest also matches its source bytes.

Both CS destination ledgers match the exact byte lengths and SHA-256 values committed in
`CS_APRIL_S0R0_POOL_V1.json` and `CS_MAY_S0R0_POOL_V1.json`:

- April: 1,255,808,208 bytes,
  `d577f94425603b9c9eb362804c858961d5b8a28fa86330a41820297133c7354b`.
- May: 1,236,232,845 bytes,
  `c7cfe80f0dd145002aa19bc742dcacbe5bc12a24ab49e751330bf03fa49f8772`.

The preservation route is evidence storage only. It grants no activation, broker, VPS, token,
promotion, family-kill, or live authority.


# Dual-Broker Architecture Decision

Decision: keep redacted_account as the only full primary runtime and keep FTMO as
follower/projector only, not a duplicate 24-symbol brain.

FTMO gains target-local authority only after a source intent is accepted:
target-side account/profile assertion, symbol mapping, tick quality, risk budget,
open-position stop-risk accounting, pending intent persistence, crash recovery,
and BE/partial/trailing lifecycle management. FTMO does not inherit redacted_account
lots, fill prices, broker-real PnL, cost specs, or lifecycle truth.

Implementation disposition:

- `config/profiles/redacted_account.yaml` declares `primary_full_runtime`.
- `config/profiles/operator_profile.yaml` and `config/profiles/ftmo.yaml`
  declare `follower_projector_only` with canonical-intent-only order source.
- `scripts/dual_broker_execution_follower.py` validates the target profile
  contract at startup and records it in `follower_started`.
- read-only live monitoring maintenance is no longer suppressed by bridge
  presence unless `GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER`
  explicitly opts into that brake.

Runtime-effect boundary: this is repo code/config/test/verifier packaging only.
It does not approve or perform live deployment, broker mutation, remote publish,
credential work, or paid data access.

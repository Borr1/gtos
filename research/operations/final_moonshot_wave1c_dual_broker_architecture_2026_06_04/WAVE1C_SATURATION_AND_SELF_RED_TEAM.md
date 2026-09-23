# Wave1C Saturation And Self-Red-Team

Same-evidence-class gaps pursued:

- Profile namespace and account role: closed by explicit profile contract rows
  and follower startup validation.
- Primary versus target authority: closed at component level by the authority
  matrix and implementation decision ledger.
- Broker-local risk: closed at code level by target budget/open SL risk logic;
  broker-real PnL remains capture-gated unless account-history joined.
- Lifecycle and crash recovery: closed at component level by target-state store,
  startup recovery, residual restore, and stale market recovery window rows.
- Maintenance starvation: repaired by making bridge-based suppression explicit
  opt-in instead of default.

Self-red-team outcomes:

- Evidence class confusion: ledgers keep broker-real PnL/cash null unless joined.
- Source leakage: FTMO target rows are not treated as redacted_account truth.
- Duplicate runtime risk: final decision forbids FTMO full run_agent fleet.
- Stale replay risk: follower preserves live recovery window and source-record
  retry checks.
- Cost/spec transfer risk: cost ledger records broker-local specs per profile and
  rejects primary spec copying.

Remaining exact source requirements are forward capture/account-history exports,
not same-class repo-code blockers.

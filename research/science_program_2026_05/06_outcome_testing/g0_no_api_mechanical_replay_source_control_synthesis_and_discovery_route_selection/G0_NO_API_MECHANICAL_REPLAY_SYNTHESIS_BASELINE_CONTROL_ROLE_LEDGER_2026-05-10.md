# Baseline Control Role Ledger

```json
{
  "artifact_family": "baseline_control_role_ledger",
  "baseline_roles": [
    {
      "downstream_use": "Mandatory comparator in every discovery path-behavior screen.",
      "family_id": "baseline_random_session_control",
      "role": "Adversarial session/time placebo comparator for whether structural families beat source/session timing alone."
    },
    {
      "downstream_use": "Mandatory timing-displacement control for core/liquidity/adjacent families.",
      "family_id": "baseline_shifted_entry_control",
      "role": "Delayed-entry comparator for testing whether family signal depends on exact source-safe candidate timing."
    },
    {
      "downstream_use": "Mandatory mechanism control for continuation-looking labels.",
      "family_id": "baseline_momentum_continuation",
      "role": "Simple trend-continuation comparator for whether complex families add structure beyond closed-bar momentum."
    },
    {
      "downstream_use": "Mandatory mechanism control for protective/context-touch labels.",
      "family_id": "baseline_mean_reversion",
      "role": "Simple stretched-price reversal comparator for whether liquidity/retest signals add structure beyond reversion."
    }
  ],
  "misuse_guardrail": "Baseline families are controls. They must not be discarded because they are simple or promoted because a path-label prevalence looks favorable."
}
```

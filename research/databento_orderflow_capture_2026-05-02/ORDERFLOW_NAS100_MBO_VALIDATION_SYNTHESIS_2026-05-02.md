# NAS100 MBO Validation Synthesis

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Decision

Primary research status: `MBO_ADDS_COHERENT_DIAGNOSTIC_SIGNAL`

Outcome-validation status: `MBO_UNEVALUABLE_LABEL_LIMITED`

Interpretation:

Databento MBO is not useless. It successfully produced a full-depth NAS100/NQ diagnostic and strengthened the same thin-depth clue that MBP-10 surfaced. However, it still does not produce a promotable rule because the outcome contrast is winner-side sparse and broker actual-R coverage remains sparse.

The correct next move is targeted forward MBO/SierraChart full-depth capture for NAS100 research, not broad historical MBO burning and not live integration.

## Inputs

Registered contract:

- `ORDERFLOW_NAS100_MBO_HYPOTHESIS_CONTRACT_2026-05-02.md`

Manifest:

- `ORDERFLOW_NAS100_MBO_FULL_DAY_MANIFEST_2026-05-02.json`
- `ORDERFLOW_NAS100_MBO_FULL_DAY_MANIFEST_2026-05-02.md`

Fetch plan:

- `ORDERFLOW_NAS100_MBO_FULL_DAY_FETCH_ESTIMATE_2026-05-02.json`
- `ORDERFLOW_NAS100_MBO_FULL_DAY_FETCH_EXECUTED_2026-05-02.json`

Feature diagnostic:

- `ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json`
- `ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.md`

## Spend And Coverage

Executed Databento MBO cost estimate:

- Total: `$3.312061`
- Groups: `3`
- Status: `{'fetched': 3}`

Fetched groups:

| Group | Cost USD | Vendor estimated records |
|---|---:|---:|
| `mbo_nas100_nqv0_20260428` | `1.849087` | `19,696,844` |
| `mbo_nas100_nqv0_20260429` | `1.329143` | `14,158,301` |
| `mbo_nas100_nqv0_20260501` | `0.133830` | `1,425,588` |

Feature extraction:

- Feature rows: `59`
- Data status: `{'ok': 59}`
- Candidate/context rows: `12 / 47`
- Outcome winner/loser rows: `1 / 10`
- Decision windows used: `pre60`, `event15`
- Forbidden windows not used as decision inputs: `post15`, `post60`

## Main Numbers

### Candidate vs Context

MBO full-depth, candidate dates only:

| Metric | Candidate | Context | Candidate - Context |
|---|---:|---:|---:|
| event15 top-20 total depth | `117.5000` | `151.0000` | `-33.5000` |
| event15 depth20 imbalance | `-0.0093` | `-0.0319` | `+0.0226` |
| event15 thin-depth20 rate | `0.1471` | `0.1956` | `-0.0485` |
| event15 wall concentration20 | `0.0588` | `0.0573` | `+0.0015` |
| event15 near10 pull pressure | `0.5047` | `0.5024` | `+0.0023` |
| event15 near10 net liquidity | `-681.0000` | `-796.0000` | `+115.0000` |

Read:

- The clearest MBO candidate/context separator is still depth state, not queue-flow pressure.
- NAS100 candidate windows have lower reconstructed top-20 depth than same-date context by `-33.5000`.
- Pull pressure is nearly flat at `+0.0023`, so this pass does not support a strong "queue pull" claim.

### Outcome Contrast

MBO full-depth, synthetic/path label join:

| Metric | Winner | Loser | Winner - Loser |
|---|---:|---:|---:|
| n | `1` | `10` | |
| event15 top-20 total depth | `186.0000` | `117.5000` | `+68.5000` |
| event15 depth20 imbalance | `-0.0558` | `-0.0046` | `-0.0513` |
| event15 thin-depth20 rate | `0.0133` | `0.1471` | `-0.1337` |
| event15 near10 pull pressure | `0.4965` | `0.5047` | `-0.0081` |
| event15 near10 net liquidity | `6389.0000` | `-681.0000` | `+7070.0000` |

Read:

- The single winner had much deeper and more additive near-touch MBO state than the loser median.
- This aligns with the adverse-selection hypothesis directionally.
- It is not statistically usable because winner n is `1`.

## MBO vs MBP-10

Prior expanded MBP-10 NAS100 readout:

- Candidate/context n: `12 / 61`
- event15 top-10 total-depth delta: `-20.0000`
- event15 depth10 imbalance delta: `+0.0145`
- outcome winner/loser n: `1 / 10`
- winner-minus-loser top-10 total-depth delta: `+34.0000`

Current MBO readout:

- Candidate/context n: `12 / 47` because context is restricted to candidate dates.
- event15 top-20 total-depth delta: `-33.5000`
- event15 depth20 imbalance delta: `+0.0226`
- outcome winner/loser n: `1 / 10`
- winner-minus-loser top-20 total-depth delta: `+68.5000`

Interpretation:

- MBO does not contradict MBP-10. It deepens the same NAS100 thin-depth clue.
- MBO adds full-depth state and near-touch add/remove features, but this pass does not show strong queue-flow separation beyond depth.
- The highest-value feature family remains depth availability/thinness around NAS100 candidate time.

## Budget Implication

The MBO spend was small relative to the remaining Databento room:

- This registered MBO pass used a represented estimate of `$3.312061`.
- The practical blocker is no longer Databento cost.
- The blocker is label quality, winner-side sparsity, and extractor runtime.

Do not spend the rest of the budget on broad historical MBO now. Keep it reserved for:

1. new NAS100 forward candidates,
2. NAS100 rows with actual broker R,
3. limit-intent/fill-quality rows,
4. a second symbol only after that symbol has both winner and loser contrast.

## SierraChart / Full-Depth Implication

This result supports SierraChart/full-depth as research capture infrastructure for NAS100, not as a live trading signal.

Why:

- Databento proved the feature family is feasible and informative enough to keep studying.
- MBO depth state gave coherent candidate/context and loser-cluster direction.
- Unlimited SierraChart capture would reduce future data-cost friction and avoid repeated Databento full-day pulls.

Constraint:

- SierraChart output must be mapped into the same registered feature contract before it is trusted.
- It must preserve `pre60` and `event15` as-of windows and keep labels separated.

## Ambiguity Ledger

- Actual broker-R coverage remains too sparse for promotion.
- Winner n is `1`, so outcome contrast is descriptive only.
- MBO action semantics were handled defensively; a future promotion dossier would need a separate schema/action audit.
- The extractor is correct enough for diagnostics but slow: the full run took close to one hour. Further MBO scaling should optimize or split per-date processing first.
- Candidate dates are selected because candidates existed; this is not a population-random historical test.

## Next Steps

1. Keep `OF-NAS100-DEPTH-ADVERSE-SELECTION-V1` active as a forward diagnostic hypothesis.
2. Add forward NAS100 orderflow collection with `trades + MBP-10` by default and MBO/full-depth only on new NAS100 candidate dates or actual-R rows.
3. Build the SierraChart parity spec so SierraChart full-depth exports can generate the same feature fields.
4. Optimize the MBO extractor before any larger historical Databento MBO run.
5. Do not create a live filter, prompt change, config change, or promotion dossier from this pass.

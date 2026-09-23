# `train_engine` — the train-grade replay lane

Wave 14, Session CB (B2150–B2199). Built **beside** the frozen sealed engine and
beside `fast_engine`; no bound byte moves, no frozen module is edited on disk.

**What it is for.** Iterating on history at iteration speed. Session AX was held
to *provenance identity* (byte-identical evidence receipts) and got 1.06×. This
lane is held to *trade-outcome identity* — same fills, same exits, same per-trade
R, same money at risk — which is what a training loop actually needs, and which
licenses removing everything that exists to prove rather than to decide.

**What it is not.** Admission evidence. Every artifact is stamped
`TRAINING_EVIDENCE - never admission-grade`, the sealed gate is untouched, and
the bounded-window mode sets `engineering_stop_after_day`, which the sealed path
hardcodes to `None` (CLAUDE.md H5). No number produced here is an arm of record.

## The four modules

| module | commission item | what it is |
|---|---|---|
| `identity.py` | CB-1 | the frozen 14-field trade tuple, what is deliberately outside it, and the comparator that decides acceptance |
| `cuts.py` | CB-2 | the dataflow cut — a **content-addressed** memo on the authority payload hash, plus AX's registry |
| `guard.py` | CB-3.4 | the partition gate; imports `trainer_partitions`, never restates a boundary |
| `runner.py` | CB-3.3 + CB-4 | sub-window, gate ordering, and the output contract |
| `accept.py` | CB-3 | assembles the acceptance receipt and refuses to mark it accepted |

## Running it

Frozen baseline (the comparand — always measure your own, never quote another
session's; run-to-run spread on this machine is ~2 %):

```bash
python3 -m src.research_infra.fast_engine.bench \
  --arm S1R1 --stop-after-day 2026-01-02 --prefix CB_FROZEN_B7_5_S1R1 \
  --patches none --evidence full --out /tmp/bench/CB_FROZEN_BASE.json
```

Train lane, same fixture:

```bash
python3 -m src.research_infra.train_engine.runner \
  --arm S1R1 --days 2 --prefix CB_TRAIN_B7_5_S1R1 \
  --purpose ACCEPTANCE_REPRODUCTION \
  --out /tmp/bench/CB_TRAIN.json
```

Acceptance:

```bash
python3 -m src.research_infra.train_engine.accept \
  --baseline /tmp/bench/CB_FROZEN_BASE.json \
  --candidate /tmp/bench/CB_TRAIN.json \
  --out /tmp/bench/CB_ACCEPTANCE.json
```

`--verify` computes both answers everywhere and counts disagreements; its
wall-clock means nothing and its `cut_report`/`verify_report` are the output.

## The gate, and the tension it resolves

`--purpose` is not a formality.

* `ACCEPTANCE_REPRODUCTION` — may run a **SEALED** window (that is what
  reproducing the frozen engine means) and **can never emit training evidence**.
  `runner.write_training_outputs` refuses on the authorization object.
* `TRAINING` — every day must carry a trainable role, or the run refuses before
  the engine starts.

The reserved blackout (March 2026) is refused on **both** paths, unconditionally.
That split is recorded rather than smoothed over, because the commission's own
acceptance fixture (2026-01-01..02) sits inside `sealed_b7_5_development_january`
and is *not* trainable — see `guard.py`'s module docstring.

## Cost-component authorization

`decision_semantics` v2 and the broker-true commission repair share one
fail-closed component contract:

| state | meaning | downstream use |
|---|---|---|
| `complete` | `spread_r`, `commission_r`, `expected_slippage_r`, and `swap_cost_r` are JSON-number, finite, non-negative, and each agrees with independent numeric capture evidence from the packet producer. Commission also agrees with the broker-truth measured value. Explicit zero is valid only when the independent capture is also zero. | The historical left-to-right four-component sum may authorize cost evidence. A geometry rebase must bind original cost to the component sum and effective cost to the recorded total; a 0.12 replacement must carry the exact current repair source and replacement fields. |
| `incomplete` | A component or its independent capture/source is absent, null, invalid, non-finite, negative, or untrusted. Python booleans and numeric-looking strings are invalid cost evidence. | The original fields and recorded total remain diagnostic, every missing field/reason is emitted, and authoritative cost is refused. No convenience zero is introduced. |
| `refused` | Finite evidence is inconsistent, including measured/component commission disagreement or an unexplained recorded-total residual. | Both claims remain visible; neither is selected as authoritative. |

This is a backward-compatible evidence migration, not a historical rewrite.
Legacy numeric fields remain unchanged, incomplete v1 artifacts and stale v2
`complete` labels do not become complete by being read again, and
`authoritative_cost_value` returns a value only after the v2 contract is
recomputed. Nested packet authority is flattened into
`cost_component_capture_evidence` so a projected row can be normalized again
without trusting old derived labels. `cost_decision_refusal_reasons` is the
single serialized failure identity; parallel per-category reason fields are
discarded on normalization so stale diagnostics cannot masquerade as current
authority.

## Measured, on the 2-day sealed January S1R1 fixture

| | frozen | train lane |
|---|---:|---:|
| wall (both unprofiled) | 657.0 s | **428.8 s** (1.532×) |
| peak RSS | 8.31 GB | **2.97 GB** (2.79× smaller) |
| marginal working day | 628.1 s | **366.5 s** (1.714×) |
| **four arms at once** | 2,628 s serial | **527.6 s** (**4.98×**), 9.14 GB, zero swap |

Run four arms concurrently — that is where the lane's throughput is. Two arms
cost 1.029× per arm, four cost 1.230×.

## Known limits, stated where a reader will hit them

1. **Only a prefix sub-window preserves outcome identity.** Account equity, the
   running conviction ledger and the risk budget accumulate across days, so
   starting on day 7 is a different arm. There is deliberately no `--start-day`.

1b. **Drop `gc_during_chunk` for a one-day iteration.** It costs **+33.07 s of
   fixed** overhead (an empty-day run is 29.3 s without it and 62.3 s with it)
   and pays for itself many times over on anything longer, where it also takes
   5.3 GB off the peak. That is why `--patches` is a list, not a boolean:

   ```bash
   --patches authority_hash_content_memo,proof_hash_content_memo,\
   abc_concrete_types,attribution_fields_identity_memo,\
   skip_post_hoc_ledger_recertification
   ```
2. **The trusted key has a residual.** The content memo keys on the engine's own
   cheap key plus every top-level scalar. Two payloads identical in every scalar
   and differing only inside a nested container would collide. `--verify`
   measures it; a test pins the residual so it cannot be forgotten.
3. **No trainable day has a prepared B7.5 day pack on this machine.** The only
   pack roots present are January, April and June-4 — all SEALED. The gate is
   therefore fully exercised in the refusing direction and untested in the
   running direction. Generating TRAIN-role packs is the prerequisite for the
   lane's first real regeneration.

# The TRAINER session — the operating manual for every session inside the lane

**One page. Read it before your first look, and again at graduation.** Authority:
`phase14/TRAINING_LANE_RATIFICATION.md` (Borhen, 2026-07-31). Machinery: Session CC,
`src/research_infra/training_lane/` + `src/research_infra/trainer_partitions.py`.

A trainer session is not a verdict session. Its output is **a better candidate and a logged
trail**, not a p-value. It ends with either a graduation or a queue entry — never with a filed
near-miss nobody iterates on, which is the failure the lane was ratified to end.

---

## 0. The one thing that is different from every other session you have run here

**Iterating costs nothing.** You may run a hundred variants on TRAIN/VAL and the estate's
multiplicity bill does not move. What you may not do is *quote* one of them as an admission.
The bill is paid once, at graduation, and it buys exactly one look.

So: search hard, log everything, graduate rarely.

---

## 1. What you READ at the start (in this order, ~10 minutes)

| # | read | why |
|---|---|---|
| 1 | **the iteration ledger tail** — `phase14/receipts/TRAINING_LANE_ITERATION_LEDGER.jsonl` | what has already been tried, on which surface, with what verdict. Do not re-run a look that is already in it unless you mean to. |
| 2 | **the surface map** — `DEFAULT_SURFACE_MAP.header()` and `phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json` | which days you may touch, and what every one of them was already consumed by |
| 3 | **the repair queue** — the newest `REPAIR_QUEUE_*.json` under `phase*/receipts/` | the estate's own list of gradients nobody has descended. This is your candidate source, and it is why the lane exists. |
| 4 | **the family head** — `candidate_family.DEFAULT_DECLARATION` | what a graduation will cost, and whether the head still carries `ratified_rule` |
| 5 | **the incubation registry** — `IncubationRegistry().summary()` | how much room is left (≤5 armed) before a graduation could ever reach a book |

```bash
python3 - <<'EOF'
from src.research_infra.training_lane import IterationLedger, IncubationRegistry
from src.research_infra.trainer_partitions import DEFAULT_SURFACE_MAP as S
from src.research_infra.walkforward import candidate_family as CF
import json
print(json.dumps(IterationLedger().summary(), indent=1))
print(json.dumps(IncubationRegistry().summary()["capacity"], indent=1))
print("surface map:", S.map_id, S.digest()[:12])
fam = CF.load_candidate_family()
print("family head:", CF.DEFAULT_DECLARATION.name,
      "CANDIDATE_BOOK_V1 =", fam.effective_size("CANDIDATE_BOOK_V1"),
      "| ratified_rule:", bool(json.loads(CF.DEFAULT_DECLARATION.read_text()).get("ratified_rule")))
EOF
```

---

## 2. What you WRITE as you go

### 2.1 Every look, immediately

Not at the end of the session. A look you meant to log and did not is a look you cannot
graduate on, and `graduate()` will refuse you with `provenance_missing` hours later.

```python
from src.research_infra.training_lane import IterationLedger
from src.research_infra.training_lane.iteration_ledger import candidate_id

led = IterationLedger(session="CD")                 # default path, append-only, shared
spec = {"target_r": 5.0, "time_stop_bars": 7680}    # whatever identifies your variant
cid = candidate_id(mechanism="donchian_20", sleeve="mx_btcusd", spec=spec)

led.record(
    mechanism="donchian_20", sleeve="mx_btcusd", spec=spec,
    start="1992-02-18", end="2026-07-27",           # dates: the surface is computed from them
    engine_reserved_blackout=[["2026-03-01", "2026-03-31"]],   # what YOUR engine drops
    acknowledge_uncovered=("gap_2026H1_tail_pre_arming",),      # name the gap you cross
    engine_version="train-engine-v1",
    verdict="improved", metric=0.98, metric_name="pooled_oos_r_per_day",
    receipt="phase14/receipts/CD_SWEEP_V1.json",
)
```

**You cannot forge the surface.** You pass dates; the map classifies them. You cannot label a
March look "TRAIN", you cannot record a look that touches the live stream, and you cannot write
`verdict="admitted"` — that word belongs to the sealed gate.

### 2.2 Candidate files

One per candidate you intend to graduate, under `phase<N>/receipts/`. It must carry the
`candidate_id` you logged with, the spec digest, and the receipt paths — those are what the
biller joins on.

### 2.3 The next queue

Before you finish, append to the repair queue what you did **not** get to, with the gradient
you saw. A trainer session that leaves no queue has broken the loop it exists to run.

---

## 3. The graduation checklist

Run this before you propose anything. Every line is machine-checked at `graduate()`; the list
exists so you find out now rather than at the end.

- [ ] **The candidate has logged provenance.** `IterationLedger().provenance_for(cid)` is
      non-empty. → else `provenance_missing`
- [ ] **No provenance row touched TEST.** Every row's `surface_stamp.test_days` is `[]`.
      → else `provenance_touches_test`
- [ ] **The spec you are graduating was actually looked at.** Its digest appears in
      `spec_digests_looked_at`. → else `provenance_spec_mismatch`
- [ ] **The family head carries `ratified_rule`.** → else `declaration_lost_the_rule`
- [ ] **The claim is phrased at the ratified rule:** RECORDED population, the **band column
      alongside** ("admits at N of 3 bands", never bare), the **chronological fold table**
      published, the **maxbars share** reported, and expectancy quoted on the **recent folds**
      if anything will be sized on it.
- [ ] **The multiplicity bill is stated as a number and a family**, not implied.
- [ ] **If it will be armed:** an incubation dossier exists — proposed weight ≤ 0.05, a
      pre-registered **stop** rule AND a pre-registered **promotion** rule, each with a `basis`
      naming the artifact its threshold came from, and expected economics on the recent folds.

```python
from src.research_infra.training_lane import Candidate, graduate
rec = graduate(
    Candidate(candidate_id=cid, name="<family member name>", sleeve="mx_btcusd",
              spec_digest=spec_digest(spec), basis="<why it belongs to the family>",
              source="<the artifact that generated it>", proposed_by="Session CD"),
    session="Session CD", blocks="B2250-B2299",
    why="<one sentence: what this hypothesis is>",
)
spec_for_gate = rec.apply_to_spec(DEFAULT_SPEC)   # the frozen gate does the rest
```

`graduate()` writes the successor declaration and the receipt. **Append the new declaration to
`candidate_family.DECLARATION_CHAIN`** in the same commit — a successor that is not in the
chain is the 51 %-under-bill defect B2204 found, and
`test_no_declaration_on_disk_supersedes_the_chain_head` will go red until you do.

---

## 4. Language rules, binding

- **"dead" and "corpse" are banned** for any family whose repair paths have never run through
  the lane. The honest label is **`UNTESTED_UNDER_REPAIRS`**. January's four sealed arms ran
  the OLD engine — commission ≡ 0, no spread-geometry floor, the pre-repair clocks and stops —
  and nobody has re-generated the broad family under the repaired stack.
- **Never print a bare ADMIT.** "Admits at two of three cost bands" is the shape.
- **A VAL figure carries its disclosure.** The surface stamp puts it on the row for you;
  carry it into the prose.
- **A stop rule is a price, not a prediction.** `RISK_BOUND_not_inference`.

---

## 5. What you must never do

Unchanged from every other session and restated because a fast lane is where discipline slips:
never touch the VPS; never run a broker-capable script; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or any R2-bound path (H1 membership check first); never
change the sealed gate. You file candidates — **arming is Borhen's ceremony, every time**.

---

## 6. If something refuses you

Every refusal in the lane names its own remedy in the exception message. Read it before working
around it. The two that are not remediable:

- **TEST consumption.** There is no flag, no acknowledgement, no engine setting. Bound your
  window and look again.
- **March / the blackouts.** Refused before any band or partition is consulted, on both axes.

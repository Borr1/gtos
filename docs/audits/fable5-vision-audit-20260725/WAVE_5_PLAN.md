# Wave 5 — the estate: admitting the research that was never judged

**Approved by Borhen 2026-07-29** ("go all in and i accept the risk"). This document exists so the
plan survives an orchestrator compaction: a fresh session can pick it up cold from here.

---

## 0. Why this wave exists

The programme has spent its recent waves on **11 sleeves**, and is arming **4**. The research built
**34**.

```
34  sleeves built (BUILT 11 + CANDIDATE_BUILT 9 + MARKET_EXPANSION_BUILT 14)
11  cost-validated  (Session N's W7 re-cost -> SURVIVOR_BOOK_V1)
23  never validated at any cost model
 4  being armed on FTMO
```

Three further sleeves exist in `INTEG_W5_new_streams_cache.pkl` — `leadlag_core`,
`xlayer_veto_gate`, `subh4_ll_fx` — that are in **no registry at all**. Built, cached, never
promoted. Their disposition is part of X's scope.

`THIRD_REVIEW.md` §4 already states the admission mechanism, and it is unambiguous:

> the 21 candidate/expansion sleeves have no validation and enter `SURVIVOR_BOOK_V1` **only through
> the walk-forward gate**.

**That gate does not exist.** Verified by search across `src/` and `scripts/` on 2026-07-29 — there is
no walk-forward implementation anywhere. So the door through which all remaining research must pass
has never been built, and every sleeve beyond the core 11 is stranded behind it.

This wave builds the door and walks the estate through it.

## 1. What already exists to build on — measured, not assumed

| asset | state | receipt |
|---|---|---|
| **Bars archive** | 43 FTMO symbols × D1/H4/M15; D1+H4 back to **1992-02-18**, M15 from 2024-01-01; **4,358,938 rows; zero coverage gaps** | `/Users/borr/GTOSActive/vps-bars-20260727/BARS_MANIFEST.json` |
| **Generation port** | K1-a **PASSED** 20,093/20,093 cycles, both namespaces, zero disagreements | `phase3/K1_GATE_RECEIPT.md` |
| **Port fidelity, per-bar sleeves** | **96 % live-recall** — covers all 14 `mx_*` | same, §3 |
| **Port fidelity, first-of-day sleeves** | **19 % live-recall** — covers 7 of 9 candidates | same, §3.5 |
| **Broker-truth cost layer** | reproduces realized broker charges to **0.00298 R** | `phase3/BROKER_TRUTH_LAYER.md`, Session R §4 |
| **Firm-rules MC** | per-account, at each firm's measured rules | `scripts/mc_firm_rules.py` (Session Q) |
| **Learning lane** | `recommend()` consumes live evidence, brake-only, default-off | Session R |

**The `INTEG` caches do not help here.** `INTEG_W3` holds the 8 core sleeves and `INTEG_W5` holds 6
(3 registry + the 3 orphans). Neither holds a single candidate or market-expansion sleeve — so this
is a **generation run**, not the cheap cache arithmetic Session N did.

## 2. The sessions

**Dependency, stated honestly:** X and Y consume W's gate. Their prompts are deliberately **not**
written in full until W reports, because writing them now would encode assumptions about an admission
standard that does not yet exist — precisely the failure mode §3 of the working agreement lists. What
follows is their scope, which is stable; their prompts are cut from W's output.

### W — build the walk-forward gate · `B420–449` · launches immediately

The door. Owns: what a walk-forward evaluation *is* for this programme, the leakage controls
(purge/embargo — note the existing B7.5 partition registry marks **March 2026 as TRAIN** and must
never be handed to a builder as-is), the fold specification, the cost model binding (Session J's
layer, nothing else), and the **admission-standard proposal** for Borhen.

**The gate must be able to fail every sleeve.** A gate that admits by construction is worse than no
gate, because it launders unvalidated sleeves into a book that carries the owner's money.

### X — walk the 14 `mx_*` sleeves through it · `B450–479` · after W

Historical generation over the D1/H4 archive (per-bar sleeves, 96 % port fidelity, D1 back to 1992 —
the richest substrate the programme has), priced at broker truth, evaluated by W's gate. Also settles
the three orphan cache sleeves.

### Y — repair the first-of-day generation path · `B480–509` · after W

19 % live-recall on 7 candidate sleeves means any judgment of them today measures the port's bug, not
the sleeve. K's §3.5 has the mechanism. Until this lands, **those 7 sleeves cannot be honestly
evaluated** — and saying that plainly is preferable to running them through the gate and reporting a
number.

### Z — trainer hygiene and the partition registry · `B510–539` · independent

Per-fold specs, purge/embargo, and re-authoring the B7.5 partition registry. §4 Stage 5:
*"the existing one marks March 2026 as TRAIN — it must never be passed to the builder as-is."*
March is also the only outcome-unread month the programme has left; **keep it that way.**

## 3. What is owner-decision, not session work

- **The gate's admission standard.** W proposes; Borhen decides. Same class as the risk dial.
- **Composition of any book the survivors form.** Sessions measure; Borhen composes.
- **Whether a surviving sleeve is ever armed.** Always his.

## 4. Sequencing against the live account

Stage 5 is explicitly *"a parallel lane; never blocks Stages 0–4"*, and **nothing in this wave runs on
the VPS.** The arming ceremony, the strand-fix carry, and the packet carry proceed independently on
the orchestrator's side. The only shared resource is this laptop's memory — see the working
agreement §5, and stagger accordingly.

## 5. When to commission another review

Not now. `THIRD_REVIEW.md` §4 already specifies this work in detail, so a review today would
re-derive it. The pattern that made the third review worth its cost was Fable reviewing **its own
plan against eight sessions of results**, and it changed the programme.

**The trigger is X and Y reporting**: once the estate has been through the gate and we know how many
of the 23 survive, the composition question is genuinely new, the gate's own soundness deserves an
adversary, and a fourth review earns its cost. Commission it then, with data in front of it.

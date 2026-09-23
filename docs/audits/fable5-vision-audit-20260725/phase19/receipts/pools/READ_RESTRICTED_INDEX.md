# READ-RESTRICTED — three 2025 windows: **ALL THREE SPENT 2026-08-06**

> **THE RESTRICTION IS LIFTED AND THE WINDOWS ARE GONE.** Lane `p2` (wave 19) spent
> `june_2025`, `august_2025` and `september_2025` on 2026-08-06 against a written
> pre-declaration. **There is no held-out set left in this estate.** Any lane that
> now wants an out-of-sample read must capture a new window; do not treat these
> three as unseen, and do not treat the fact that the pool FILES were never opened
> as leaving them virgin — p2 read the same months through a regenerated roster,
> which is the same evidence and a better object.
>
> * declaration: `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/p2_PREDECLARATION.md`
> * result: `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/p2_RESULT.md`
>
> | window | spent on | outcome |
> |---|---|---|
> | `june_2025` | H1,H2,H3,H4,H6 | broad-family gross **+0.02718** R/fill vs a **0.34262** toll |
> | `august_2025` | H1,H2,H3,H4,H6 | same, 3/3 windows gross-positive and 3/3 net-negative |
> | `september_2025` | H1,H2,H3,H4,H6 **+ H5** | the surviving forming-bar candidate **FAILED** (−0.30551 vs incumbent −0.28041) |
>
> Headline of the spend: **the signal is real and 253× too small in price terms**
> (0.0119 bps captured against 3.0159 bps of broker toll).

---


Session LP, 2026-08-06. This file is the index; the per-pool markers
(`*.jsonl.gz.READ_RESTRICTED`) are the same statement next to the artifact.

~~**No analysis may read the economics of `june_2025`, `august_2025` or
`september_2025` until a pre-declared test names the window.**~~ — **DISCHARGED 2026-08-06.**
The text below is retained as the history of the restriction, not as a live rule.

## Why these three exist at all

They were originally to be left *unbuilt* as a held-out set. Building them is
strictly better than not, for one reason: **building a pool is not reading it.**
The replay is deterministic given the registry inputs, and nothing about the
artifact's existence tells anyone what is in it. What changes is that when a
declared test finally wants one of these windows, it is already on disk instead
of three hours away.

Two candidate results died out of sample this week. Untouched windows are the
only instrument that catches that early, and February 2026 — the estate's last
true first read — has been spent.

## What the restriction covers

Every artifact derived from these three windows, not only the pool file:

| window | artifacts |
|---|---|
| `june_2025` | `LP_june_2025_S0R0_POOL_V1.jsonl.gz`, `june_2025_S0R0_POOL_V1.json`, `arm_receipts/LP_JUN_2025_S0R0_RECEIPT*.json`, `arm_receipts/LP_JUN_2025_S0R0_LANE/`, and the untracked route `…/attempt_5_typed_sparse/LP_JUN_2025_S0R0/` |
| `august_2025` | `LP_august_2025_S0R0_POOL_V1.jsonl.gz`, `august_2025_S0R0_POOL_V1.json`, `arm_receipts/LP_AUG_2025_S0R0_RECEIPT*.json`, `arm_receipts/LP_AUG_2025_S0R0_LANE/`, route `…/LP_AUG_2025_S0R0/` |
| `september_2025` | `LP_september_2025_S0R0_POOL_V1.jsonl.gz`, `september_2025_S0R0_POOL_V1.json`, `arm_receipts/LP_SEP_2025_S0R0_RECEIPT*.json`, `arm_receipts/LP_SEP_2025_S0R0_LANE/`, route `…/LP_SEP_2025_S0R0/` |

The economics are necessarily *on disk* — a diagnostic pool is a per-candidate
economic table, so there is no version of this artifact that does not contain
them. The restriction is therefore a discipline enforced by declaration, not a
seal enforced by encryption. It holds exactly as well as the next session's
willingness to honour it, which is why it is written in three places.

## What is NOT restricted

`october_2025`, `november_2025`, `december_2025` — the working set, open to
analysis now. Their pools and receipts sit in this same directory without
markers.

## Lifting the restriction

A session lifts it for one window by declaring, **before reading anything**, what
it will test on that window and what outcome would falsify its hypothesis, in a
committed artifact. Then it reads. Delete the window's `.READ_RESTRICTED` marker
in the same commit that records the declaration, and strike its row from the
table above so this index cannot outlive the restriction it describes.


---

## SPEND RECORD (appended 2026-08-06 by lane p2)

The table in "What the restriction covers" above is retained deliberately: it is now the
inventory of what was spent, not what is protected. Every artifact listed there is
readable. The three `.READ_RESTRICTED` markers carry the same record next to their
artifacts and were annotated rather than deleted, so the provenance of the spend
survives even if this index is lost.

**The lifting rule in the section above was followed exactly**: the declaration was
written and committed to disk before any sealed row was read, it names the windows, the
metrics, the thresholds and the falsifiers, and its two addenda (harness validation, and
the compute allocation that put the full partial-bar grid on september only) were both
written before any sealed outcome existed and moved no threshold.

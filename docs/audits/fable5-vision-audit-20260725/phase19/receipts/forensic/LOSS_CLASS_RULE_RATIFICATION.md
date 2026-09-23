# Loss-class rule ratification (register row A) — the counterfactual-exit rule is canonical

Session FA continuation, 2026-08-03. The A2 reconcile lane re-implemented both competing rules
from their receipt definitions and applied them to both months' RAW trade ledgers (every
published cell reproduced exactly; both rules sum to each month's executed net exactly). Its
recommendation is RATIFIED by this session:

**Canonical rule (was "the Feb rule"): per trade, against its own ordered path and own cost —**
- `direction_wrong` ⇔ the path never offered ≥ 0.25 R favorable excursion (no exit could have won);
- `exit_geometry` ⇔ `mfe − cost > 0` (a net-profitable exit existed; the machinery failed to take it);
- winners keep their target/other split; `cost_dominated` for losers whose gross was positive.

Why: the classes exist to ROUTE REPAIR. This rule makes `exit_geometry` collect exactly the
losses an exit-policy change could in principle recover, and `direction_wrong` exactly the
losses none could. The Jan rule's fixed MFE≥0.5R cut files 9 January trades (−9.72 R) and
7 February trades (−5.84 R) under "direction" even though each had a bankable net-profitable
exit on its own path. Disclosures whenever quoted: the 0.25 R floor is a declared threshold,
not derived; the counterfactual exit is charged the full trade cost (conservative).

**Canonical restated tables** (from `a2_verify/RECONCILE_A_Q.md` §A, recomputed from raw ledgers):

| class | January (57; 55 scoreable) | February (58) |
|---|---|---|
| winners (target / other) | 6 / +11.9111 · 17 / +12.2308 | 2 / +3.8567 · 22 / +15.7581 |
| direction_wrong | 11 / −9.6973 | 10 / −9.5935 |
| **exit_geometry** | **21 / −19.9509** | **23 / −13.9654** |
| cost_dominated | 0 | 1 / −0.0173 |
| unscoreable | 2 / 0 | — |
| **book net** | **−5.5062** | **−3.9614** |

Every prior side-by-side quote of the two old tables is superseded by this receipt. The
FULL_FLOW L8 verdict and R-GEOMETRY's ex-ante spec consume these numbers.

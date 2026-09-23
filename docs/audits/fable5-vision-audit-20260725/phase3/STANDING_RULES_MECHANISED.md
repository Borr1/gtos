# The two standing rules — what was mechanised, and what cannot be

**Session M, 2026-07-27.** `SESSION_M_HYGIENE.md`: *"Two came out of this wave's review and are currently
prose. If a cheap mechanism can enforce either, build it; if not, say why."*

One is now enforced. The other is not, and the reason is worth more than a weak mechanism would be.

---

## Rule 1 — "An A/B that is not committed did not happen" — **MECHANISED**

**Landed:** `scripts/pytest_failset.py receipt <before.json> <after.json> -o <receipt.md>`, plus
`tests/scripts/test_ab_receipts_are_self_contained.py` (4 tests).

The rule as written covers the wave-2 failure exactly: the A/B was genuinely run, it lived in a
scratchpad, and to the next reader it therefore did not exist (`receipts/WAVE2_INTEGRATION_AB.md`).

**But the rule as written has a hole, and closing it is what makes the mechanism worth having.** A
committed receipt that *references* `/tmp/before.json` is exactly as unverifiable as no receipt at all,
because the file it names is gone by the time anyone reads it. Prose saying "we ran it and it was clean"
satisfies "committed" while carrying no evidence. That is a receipt-shaped false green — the precise
thing this session exists to remove — and it would have been the natural next form of the same mistake.

So the enforceable rule is stronger than the prose one: **a committed A/B receipt must EMBED the captures
it was derived from.** The tool emits an embedded `gtos-ab-receipt-v1` JSON block carrying both commits,
both totals, and the full before/after bad-node-id sets. The test then checks three things:

- every A/B receipt in the tree carries the block (grandfathering the one hand-written predecessor **by
  name**, so the exemption is visible and can only shrink);
- each block **parses and is internally consistent** — `regressed` and `fixed` must be *derivable* from
  the two node-id sets, so a receipt cannot assert a headline its own data contradicts;
- the grandfather list is not stale, because an exemption that outlives its problem is itself a
  false-green.

Cost: ~90 lines of tool, ~90 lines of test. It runs inside the suite, which matters — there is no CI, no
git hooks and no pre-commit config in this repo, so the pytest suite is the only enforcement surface that
actually executes.

---

## Rule 2 — "Any claim of improvement carries a placebo or null control in the same receipt" — **NOT MECHANISED, and here is why**

The base rate this rule exists for is brutal and worth restating: of every book-level improvement in the
record, exactly **one** passed its own random-drop placebo — the small A8 metals-confluence gate. The
large exciting one (+0.1297 Sharpe, +2.323 %/month) **failed at p = 0.59 and was activated anyway.**

**I did not build a mechanism for it, and I recommend nobody builds the obvious one.**

The obvious mechanism is a test that scans receipts for improvement language — `"improve"`, `"+X Sharpe"`,
`"better"`, `"gain"` — and requires a placebo section nearby. That is pattern-matching English, and it
fails in both directions in ways that make it worse than nothing:

- **False negatives are the norm, not the exception.** The claim that most needs a control is usually
  phrased as a bare number in a table cell — `| Sharpe | 0.1446 | 0.1478 |` — with no improvement word
  anywhere near it. A keyword probe cannot see the claim at all, so the receipt passes. The rule is then
  *reported as enforced* while the highest-risk claims sail through: a mechanism that manufactures
  exactly the false green it was built to prevent.
- **False positives train people to ignore it.** Every receipt in this programme discusses improvements
  it is *refuting* — that is most of what the audits do. A keyword probe flags all of them. An
  enforcement that mostly fires wrongly gets routed around within a week, and then it is decoration.
- **It is trivially satisfiable without doing the work.** Adding a heading called "Placebo" passes the
  check. Any text-shaped gate on a *methodological* property is satisfiable by text.

The property "this number is accompanied by a null control **that is a valid control for this number**"
is a claim about experimental design. Nothing that reads markdown can evaluate it.

### What would actually work, and what it costs

Two real options, neither cheap, both stated so the decision is available rather than implied:

1. **Structured receipts.** If quantitative receipts carried front-matter (`improvement_claim: true`,
   `null_control: <path-or-inline>`), a test could enforce presence trivially and the author would have
   to *declare* they are making a claim. This is enforceable and cheap **once the convention exists** —
   but the convention does not exist, adopting it means retrofitting every quantitative receipt in the
   programme, and a declaration is still self-reported. It converts "did you run a control?" into "did
   you say you ran a control?", which is a real improvement in visibility and no improvement in truth.
2. **Ship the harness, not the check.** The reason placebos get skipped is friction, not intent. Session
   D's harness already has a self-comparison null control; a reusable `random_drop_placebo(...)` helper
   with a standard receipt fragment would make running one cheaper than not running one. This is the
   intervention I would actually make, and it is a Stage-1-sized piece of work, not hygiene.

**Recommendation:** do (2) when the next quantitative claim is being produced — which, given OD-3, is the
W7 re-cost, and it is the single most consequential number this programme will generate. Do (1) only if
the owner wants the declaration visible in the tree regardless.

**What I did instead, being honest about its limits:** this session produced no claim of improvement, so
the rule had nothing to bind to here. The nearest thing is the A/B, and the A/B *is* its own control —
it compares against the parent commit's measured failure set rather than against an assertion, which is
why "sets, not counts" is the load-bearing half of that rule.

---

## One structural note that applies to both

Neither rule can be enforced by anything that does not run. This repo has **no CI, no `.github/`, no git
hooks, no `.pre-commit-config.yaml`, no lint config**, and `coverage`/`pytest-cov` are not installed
[MEASURED]. The pytest suite is the entire enforcement surface. Any future mechanism proposed for this
programme should be a test, or it will not execute — and a mechanism that does not execute is the purest
form of the defect this session was sent to remove.

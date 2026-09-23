# Session AW — the separability mine (wave 12, B1750–B1799)

## Authority and the question

Borhen, 2026-07-30, challenging the campaign park: *"i dont think you ever checked the actual
results and the intelligence there, you saw it negative and instantly threw it away, maybe there
was something wrong, maybe if with some fixes it becomes positive, maybe if you run it more you
can figure out what's wrong exactly."* He is right about the open half, and `JANUARY_BANK.md` §3
already says so: the January reference arm's diagnostic pool carries **+6,916.95 R of positive
rows against −31,400.82 R of negative rows over 28,519 scoreable rows** (8,006 / 20,513), and the
campaign only ever tested whether the incumbent's **two pre-registered switches** separate them
(they don't, measurably) and whether dynamic sizing helps (material negative — that rule stands).
**Whether the pool is separable by ANY rule is "open and unmeasured at any useful resolution"**
(the bank's own words). This session measures it.

Read first, in full: `JANUARY_BANK.md` (all of it — §3, §4/F31, §5, §7 bind you),
`WAVE_11_WORKING_AGREEMENT.md` §4 (wave-12 deltas), CLAUDE.md §3 H1 and the B905 hazard, and
the cold-evidence reader
(`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/b7_5_cold_evidence.py`).

## Hard constraints, before anything

- **Everything you read is sealed and read-only.** The R2 contract binds 43 paths; the January
  ledgers are evidence. Never edit, never `git clean`/`git checkout` inside the cold route (two
  `REPLAY_EXTENSION_*` paths are load-bearing BY ABSENCE), never touch the two LFS-bound ledger
  paths in the main repo (B905). Your worktree is your own; the ledgers you read live in place.
- **March is never read, never featured, never split.** It is the programme's scarcest resource
  and the partition registry marks it TRAIN — it must not feed any dataset builder as-is.
- **The rows are PROXY outcomes** (the reservoir class): before any economic claim, charge F31
  gap-through (the bank's −0.038 R/row means on level exits) and broker-true costs. A
  discriminator that only works before costs is a spread detector, not an edge.
- **This is maximal-multiplicity territory.** Declare the feature family FIRST (ratchet — a new
  `CANDIDATE_FAMILY` successor with the mining families as members), split within-window (train
  on part of January, validate on the held-out remainder; April's 15 sealed S1R1 days are a
  secondary holdout with its 25.8 % price-coverage caveat stated), ledger every look, and apply
  the wave-12 binding standards (chronological folds, seed-sweeps near permutation floors,
  maxbars share where relevant).

## Work orders

**AW-1 — The reader (and it closes JANUARY_BANK §7.5).**
Build the reader that turns the four sealed January arms' JSONL ledgers (cold shards read in
place) plus April's partial into a typed row set: outcome (net R, scoreable status, exit
reason), and every feature the ledgers carry or can be joined from the archive — symbol,
mechanism/policy layer, session/hour (broker clock!), regime dials (AB's spine), spread state,
entry-quality fields, hold time. This reader is the missing learning-lane link the bank says
does not exist — build it as a reusable module with tests, not a one-off script.

**AW-2 — The mine.**
What separates the 8,006 positive rows from the 20,513 negative? Work the declared feature
families from univariate screens to shallow interactions. Publish the full negative results
alongside any positive — the deliverable is the MAP of separability, not a highlight reel.
Within-window validation decides what survives to AW-3; nothing that fails the held-out
January remainder goes forward, however good it looks in-sample.

**AW-3 — Out-of-window, on the fast machinery.**
Restate each surviving discriminator as a candidate SELECTION RULE (a filter/condition a sleeve
or the estate can run), and gate it on the ARCHIVE walkforward at the ratified rule — RECORDED
population, band alongside, declared cuts, chronological folds. Minutes per test. Anything that
admits (or lands a named near-miss) enters the estate like any other candidate. A sealed-window
confirmation is then a PRICED option for the owner — and per JANUARY_BANK §7.1/§7.2 it requires
the pooled evaluator + pooling weights written and sealed FIRST; state that price in your
result, do not pay it.

**AW-4 — The honest deliverable, either way.**
Either: "the pool is separable by X, gated at the sealed standard, here is the candidate" — or:
"N declared families were mined; here is the enumeration of what does not separate
out-of-window, and what data/feature would be needed to go further." The owner's doctrine is
that a thing may be set aside only after its repair paths are enumerated — this session IS that
enumeration for the broad-family question, done properly for the first time.

## Done means

Result doc + receipts under `phase12/receipts/`, blocks B1750–B1799, scoped A/B green vs the
zero baseline, ledger/repair-queue appends, honest §what-I-got-wrong, handoff list. Never touch
the VPS; never run broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or ANY R2-bound path. Both live books trade five sleeves;
nothing you build arms anything.

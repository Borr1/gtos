# Session AK — the sleeve-supply lane: the estate has generators it has never judged and quarantined sleeves whose exits just moved

**Wave 8.** Worktree `worktrees/wave8-sleeve-supply-20260730`, branch `phase8/sleeve-supply`,
from `main`. **Blocks B950–B999.**

**Read `../WAVE_8_WORKING_AGREEMENT.md` in full first**, then AA's result §5 (the orphan
routing), AD's result §6 (the exit cells you will reuse), and AF's result §2 (the family
discipline your new members inherit).

---

## The mission

Wave 7 proved the repair machinery works. This lane widens what it can work ON: generators that
exist but have never been walked, one mechanism the estate authored and never built, and three
quarantined sleeves whose economics changed shape when AD repaired their exits. Every new member
you create is a look in the ledger and a row in the queue — that is the deal that lets this lane
be aggressive.

## The work list, in value order

**1. The three orphan generators, walked at last.** `vol_squeeze`, `ny_index_momentum`,
`structural_retest` are complete generators with no `SleeveSpec` — the production path cannot
reach them and no walk has ever judged them (AA §5). Build their research-side specs (walkforward
only — the live `candidate_registry.py` allowlist stays untouched; propose the one-line edit,
Borhen decides), generate over the full archive on their authored timeframes, and take each
through the gate in diagnostic mode with AD's exit families swept where the diagnosis says the
exit is the blocker. `structural_retest` is the estate's **only short-side mechanism** — its
verdict diversifies the whole book's direction exposure, which neither account currently has.

**2. `session_leadlag_genuine` — the authored-but-never-built mechanism.** The handoff carries it
as a standing item. Build the generator from its design notes, state explicitly what its
hypothesis is BEFORE generating, log the look, walk it. If the design notes underdetermine the
mechanism, write down the smallest complete version and build that — a parked design is worth
less than a measured one.

**3. The quarantined trio, re-tested at their repaired exits.** AD moved their best cells to
within noise of zero: `asian_fade` −0.780 → **−0.009** (trail_a2_g0.5_prod),
`kz_london_crypto_low` −0.592 → **−0.011** (stop_3x_tgtscale), `metal_session_reversion` −0.796 →
−0.170 (composite). The diversifier door (`certify_diversifier`, X's, merged) exists for exactly
this shape: a ~zero-mean sleeve can still earn a slot through correlation. Run all three through
it **at their repaired exit cells** (from `phase7/receipts/EXIT_FRONTIER_V1.json`; respect both
trail bounds — where the honest bound flips the sign, the verdict is the honest bound's), against
the armed book's day series. Condition 1 consumes the fixed `regime_inflation` (AE verified it
sound). A pass here is a new kind of admission: portfolio-level, not standalone.

**4. The first-of-day sleeves, now judgeable and now repairable.** Y's fidelity merge raised
their `live_recall` to 1.0 and six of seven reached verdicts — all REJECT, negative pooled OOS —
but AA measured five of seven **gross-positive** (`asia_pdl_fade` +0.196 R/trade on 2,206
trades), so the shape is cost/exit, exactly what AD's machinery repairs. Sweep the exit families
over their stored intents, re-gate, and publish each one's frontier the way AD did. If the best
cell still rejects, the row says which gate and by how much.

**5. `mx_jp225` standalone — the second-strongest single member in AF's grid** (+0.2071 R/day at
mid, p 0.1126, 80 % folds, band-stable) and `vol_compression` at AD's `time_stop_20` (+0.445
R/day, from +0.269). Both are candidate-book material blocked on sample/multiplicity, not on
economics. Re-walk each at its best-known configuration with every look deflated, and hand AI the
resulting rows with fold series attached — they are inputs to the candidate book, and the
cleaner their dossier the cheaper AI's composition question.

**6. Family discipline for anything you widen.** New symbols/timeframes inherit AF's rules:
complete cross declared before outcomes, drops recorded with reasons, surface-expanded members
carry "NO LIVE RECORD OF ITS OWN", mixed fidelity refuses to pool. Where a spread is banded, the
era-model defect note in the agreement §4 applies.

## Substrate

- `phase6/receipts/AA_ESTATE_TRADES.json.gz`, `phase7/receipts/AF_FAMILY_TRADES.json.gz`,
  `phase7/receipts/EXIT_FRONTIER_V1.json` — reuse before regenerating.
- Bars `/Users/borr/GTOSActive/vps-bars-20260727/` (41 instruments; broker wall clock).
- `src/research_infra/walkforward/` — gate, diagnostics, exits, family, diversifier are all
  merged and green in scope.

## Deliverables

1. `phase8/receipts/SLEEVE_SUPPLY_V1.json` — per new/reworked member: generator provenance, gate
   verdict at measured carry, exit frontier if swept, diversifier-door verdict where run, and the
   next prescription.
2. Repair-queue rows appended (session `AK`).
3. `phase8/SESSION_AK_SLEEVE_SUPPLY_RESULT.md` with the §2 scoped receipt.
4. Every look in the trial ledger.

## Not yours

The VPS. Arming, tokens, gates, sleeve composition, the `candidate_registry.py` allowlist (propose
the edit; Borhen decides). Merging to `main`. `config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your report
when you do.

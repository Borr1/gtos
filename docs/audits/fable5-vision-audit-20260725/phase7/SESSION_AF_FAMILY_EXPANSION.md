# Session AF — family expansion: significance failures are breadth prescriptions, and the archive is 43 symbols wide

**Wave 7.** Worktree `worktrees/wave7-family-expansion-20260730`, branch
`phase7/family-expansion`, from `main`. **Blocks B800–B849.**

**Read `../WAVE_7_WORKING_AGREEMENT.md` in full first** — the verification policy changed —
then `FOURTH_REVIEW.md` §3.3 and §5.4, then AA's result
(`../phase6/SESSION_AA_ESTATE_WALK_RESULT.md`), then AG's spread model result
(`../phase6/SESSION_AG_SPREAD_MODEL_RESULT.md`) — its banded pricing is what makes most of
your new symbols priceable at all.

---

## The mission

The estate's most common honest failure is significance: a real-looking edge that cannot pay
a 69-look family bill alone. The Fundamental Law answer is breadth — pool the *mechanism*
across symbols and admit the family. W judged the 12 mx sleeves standalone, charging each the
full multiplicity bill; the mechanism-level questions were never asked. You ask them, across
the 43-symbol archive, with the ledger counting every look so the answer deflates honestly.

AA's BREADTH rows each carry the required multiple `(z_α / z_observed)²` — a scoping number
(it assumes independent equal-IC members, which a symbol family is not), not a promise.

## The work list

**1. `mx_btcusd` + the crypto-donchian family — the armed book's de-risk.** `mx_btcusd`
already clears alpha raw (+0.2446 R/day OOS, 100 % folds, raw p 0.0124) and fails only the
family bill (q 0.149 standalone; AA re-measured q 0.048 at zero carry — Session AD owns that
exit). The core `crypto` sleeve is the **same donchian-20 mechanism on H4** (ac60-gated, 4 R
— `crypto.py:25-28`), 2-symbol surface (BTCUSD+DASHUSD), history starting 2024-09, ~40 % of
the armed book's edge. Run the donchian family across every crypto symbol the archive holds,
both timeframes, through the gate as a **family** with measured trial counts. If the family
admits, the armed book's largest single risk becomes a diversified cluster claim — that is
the highest-value outcome in this session. Propose the cluster cap (pairing repair) as a
recommendation; composition is Borhen's.

**2. `energy_agri`'s significance repair — the armed sleeve with the weakest statistical
case** (q 0.33 at minimal carry on the priced subset, OOS +0.302 R/day, 75 % folds
positive). Its mechanism across the agri/energy surface the archive holds. The registry-says-4
/ generator-says-2 mismatch is settled — AA measured it as authored-vs-tradeable universe
naming, not wiring (AA result §3.2) — so the expansion question is purely: does the mechanism
carry on the wider surface?

**3. The volume-surge family.** `mx_jp225` (+0.1985, 80 % folds, q 0.487) and `mx_us30`
(+0.0584, 40 % folds) pool across the index set; `mx_ger40` (−0.0112/day) gets the AA
three-way decomposition first — its MFE/MAE is already in the walk artifact: excursion the
exit misses → route to AD; none → inverse test; else park with list.

**4. The ATR-MR mechanism, tested where it plausibly lives.** −0.2551/−0.3518 on
US500/US100 is mean-reversion tested against the two strongest-trending instruments in the
estate. Before any verdict on the *mechanism*: (a) the **inverse test** (continuation on the
same trigger — near-free from AA's stored intents); (b) the mechanism over the other ~40
archive symbols; (c) vol-regime conditioning (MR lives in range regimes — AB's regime spine
artifacts give you the conditioning variables). Either a repaired MR family elsewhere, a
continuation signal, or an honest park-with-list.

**5. The near-misses, margins in hand.** `mx_cadjpy` −0.0017 from passing — the closest in
the whole map — was unjudgeable for want of a spread; AG's model now prices it with bands,
and AG measured the FX family paying **13×–38× spread at broker hour 00**, so a session
filter to the cheap hours is the named repair. `mx_nzdjpy` −0.0019: full-history lifetime is
−0.003/trade — find the break date, name the conditioning variable (carry regime? vol era?),
gate on it explicitly, re-walk. `mx_ger40` −0.0082 via item 3.

**6. Family discipline, stated once.** Every family verdict carries: members and their
per-symbol contributions, the measured look count from the ledger, the banded spread verdict
where AG's model priced a member (a member that flips bands gets that fact in its row), and
the family-vs-standalone q comparison. Per-symbol allocation inside an admitted family is
wave-8 diversifier-door work (X's `certify_diversifier`, merged) — do not improvise it here.
**No silent caps**: if you bound coverage (symbols skipped for data, cells dropped), log what
was dropped in the result doc.

**7. If a family admits nothing anywhere**, the deliverable is the conditioning map — which
regimes/symbols/sessions came closest, and what data or repair would close the gap. Route
`REGIME_GATE` shapes to AB's spine artifacts; route exit shapes to AD.

## Substrate

- AA's stored intents (`../phase6/receipts/AA_ESTATE_TRADES.json.gz`) for anything already
  walked; regenerate only for new symbols/timeframes/thresholds.
- Bars archive `/Users/borr/GTOSActive/vps-bars-20260727/` (34 y D1/H4 where history
  reaches, M15 2024+; broker wall clock — `src/utils/broker_clock.py`).
- AG's spread model for banded pricing of the newly-priceable symbols; `cost_r` for the
  measured ones. Six FTMO symbols gained measured spreads on 2026-07-29
  (AUS200.cash, CADJPY, DASHUSD, EU50.cash, NATGAS.cash, SPN35.cash) — re-read
  `BROKER_TRUE_COSTS_V1.json` rather than assuming last week's coverage.
- `mx_aus200_volume_surge` / `mx_spn35_volume_surge`: fully runtime-capable, excluded live
  solely by the 12-name tuple at `candidate_registry.py:425-438`; AUS200/SPN35 spreads are
  now measured, but their **bars** are still absent (§9 ceremony pending). Judge them the
  moment bars exist; otherwise record exactly that in their family rows.

## Deliverables

1. `phase7/receipts/FAMILY_ADMISSION_V1.json` — per family: members, family gate verdict,
   ledger-deflated stats, banded spread sensitivity, standalone-vs-family comparison.
2. Repair-queue rows **appended** (session `AF`).
3. `phase7/SESSION_AF_FAMILY_EXPANSION_RESULT.md` with the scoped-verification receipt.
4. Every member-look in the trial ledger.

## Not yours

The VPS. Arming, tokens, gates, sleeve composition, the `candidate_registry.py` allowlist
(propose the one-line edit; Borhen decides). Merging to `main`. `config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your
report when you do.

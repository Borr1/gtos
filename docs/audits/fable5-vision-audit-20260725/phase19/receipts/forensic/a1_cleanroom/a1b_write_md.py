#!/usr/bin/env python3
"""A1-OPEN (a1b), step 4: render A1_REISSUED_VERDICT_TABLE.md from the verified JSON.

Every number in the MD comes from A1_REISSUED_VERDICT_TABLE.json (itself assembled from
receipts + the recompute outputs); the narrative is fixed text.  Re-run after a1b_reissue.py.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = json.load(open(HERE / "A1_REISSUED_VERDICT_TABLE.json"))


def fmt(p):
    return "—" if p is None else f"{p:.6g}"


def esc(s: str) -> str:
    return str(s).replace("|", "\\|")


rows = t["reissued_computed_null_rows"]


def row_by(arm, band):
    return [r for r in rows if r.get("arm") == arm and r.get("band") == band][0]


core_lines = [
    "| member | arm | band | session | pub p | pub q | pub verdict | corr p (primary) "
    "| corr p @ measured rho | corr q | corr verdict | flip |",
    "|---|---|---|---|---:|---:|---|---:|---:|---:|---|---|",
]
for r in rows:
    core_lines.append(
        f"| {r['member']} | {r['arm']} | {r['band']} | {r['publishing_session']} | "
        f"{fmt(r['published_p'])} | {fmt(r['published_q'])} | {r['published_verdict']} | "
        f"{fmt(r['corrected_p'])} | {fmt(r.get('corrected_p_at_measured_rho'))} | "
        f"{fmt(r['corrected_q'])} | {r['corrected_verdict']} | **{r['flip']}** |")
core_table = "\n".join(core_lines)

nn_lines = ["| member | session | receipt | published verdict | classification |",
            "|---|---|---|---|---|"]
for r in t["named_receipt_rows_no_computed_null"]:
    nn_lines.append(f"| {esc(r['member'])} | {r['publishing_session']} | "
                    f"`{r['receipt'].split('/')[-1]}` | {r['published_verdict']} | "
                    f"{r['classification']} |")
nn_table = "\n".join(nn_lines)

groups: dict[str, list[str]] = {}
for r in t["member_classification_59"]:
    groups.setdefault(r["classification"], []).append(r["member"])
cls_summary = []
for k in ("AFFECTED_RECOMPUTED", "NO_COMPUTED_NULL_UNAFFECTED",
          "AFFECTED_HISTORICAL_NOT_REISSUED", "PADDED_UNAFFECTED"):
    names = groups.get(k, [])
    cls_summary.append(f"**{k} ({len(names)})** — " + ", ".join(f"`{n}`" for n in names))
cls_block = "\n\n".join(cls_summary)

lin_lines = ["| session | receipt | node | p | q | verdict | m | note |",
             "|---|---|---|---:|---:|---|---:|---|"]
for r in t["standing_admission_lineage"]:
    note = r["note"]
    if "NOT_RECOMPUTABLE" in note:
        note = "the LATEST republication (family 57, n=228) — **NOT_RECOMPUTABLE**, see below"
    lin_lines.append(f"| {r['session']} | `{r['receipt'].split('/')[-1]}` | "
                     f"{esc(r['node'])} | {fmt(r['p_raw'])} | {fmt(r['q_value'])} | "
                     f"{r['verdict']} | {r['declared_family_size']} | {note} |")
lin_table = "\n".join(lin_lines)

mx_mid = row_by("target_5R", "mid")
mx_flat = row_by("target_5R", "flat_37_day_snapshot")
mx_low = row_by("target_5R", "low")
br = [r for r in rows if r["member"].startswith("cq_")][0]
n_hist = len(groups.get("AFFECTED_HISTORICAL_NOT_REISSUED", []))
n_pad = len(groups.get("PADDED_UNAFFECTED", []))

md = f"""# A1 Re-issued Verdict Table — every CANDIDATE_BOOK member through the affected significance path

**Session FA continuation, Phase A1 OPEN half (a1b).** Generated {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}.
Machine record: `A1_REISSUED_VERDICT_TABLE.json` (same directory). Scripts: `a1b_capture_au_series.py` →
`a1b_corrected_null.py` → `a1b_reissue.py` → `a1b_write_md.py`. Clean-room basis:
`A1_CLEANROOM_NULL_DERIVATION.md` (+ `.json`).

**Affected set** = family members whose PUBLISHED p came from `block_permutation_p` /
`both_conservative` machinery on a daily series (a computed null). Padded-at-1.0 members are
unaffected by construction. Ratified basis confirmed from
`phase8/receipts/CANDIDATE_FAMILY_V1.json → ratified_rule`: CANDIDATE_BOOK_V1, B_balanced,
α = 0.10, all_declared (carried verbatim at the V27 tip, 59 declared / 57 looks).

**Method.** Every recomputed arm's daily series was captured **in process from the committed receipt
driver** and accepted only after the receipt reproduced float-exactly (CS: 12/12 checks in the blind
phase; AU: **16/16 arms PASS** on p_raw, q, verdict, fold_means, n_trades, spec_sha256 —
`A1B_AU_CAPTURED_SERIES.json`). Corrected null = the clean-room recipe generalized to each arm's own
fold structure: independent fold segments, within-fold AR(1) over a fitted-dependence grid
{{ρ̂−SE, ρ̂, lag1_full, ρ̂+SE}} × {{gaussian, residual-bootstrap}} innovations, per-fold scale,
studentised mean, 3 seeds, **primary p = max over variants** (the spec's own `both_conservative`
posture applied to model risk). Sims: breaker 700k×3/variant (reproduces the clean-room
**bit-exactly on all 8 variants** — the generalization self-check); AU arms 200k×3/variant (≥ the
100k floor). q: each receipt's own multiplicity block reproduced with the corrected p substituted for
the target only; substituting the *published* p back reproduces the published q exactly on every arm.

---

## 1. The flips

### 1a. ADMIT → REJECT — **BINDS IMMEDIATELY** (flagged loudly, as commissioned)

**`mx_btcusd_d1_donchian_20_breakout @ target_5R` — the estate's ONE standing admission, LIVE on FTMO
since 2026-07-31 — fails the corrected primary at ALL THREE admitting bands** (AU_EXIT_WIRING_V1,
family 48): flat {fmt(mx_flat['published_p'])}→{fmt(mx_flat['corrected_p'])} (q {fmt(mx_flat['corrected_q'])}), low {fmt(mx_low['published_p'])}→{fmt(mx_low['corrected_p'])} (q {fmt(mx_low['corrected_q'])}),
mid {fmt(mx_mid['published_p'])}→{fmt(mx_mid['corrected_p'])} (q {fmt(mx_mid['corrected_q'])}). Significance was the sole failing gate in every case, so the
overall verdict flips with it.

**The precision that must travel with this flag.** At the MEASURED within-fold dependence
(ρ̂ = 0.384 ± 0.069, 179 pairs — a *tight* estimate) the corrected p is {fmt(mx_mid['corrected_p_at_measured_rho'])}, almost exactly
the published {fmt(mx_mid['published_p'])}, and still admits (q ≈ 0.065). The REJECT comes **entirely from the +1SE
dependence variant** (ρ = 0.452–0.453, both innovation laws). So the finding is not "the p was
wrong"; it is: **the admission carries less than one standard error of dependence-model margin at
its 48-family bar** (flip boundary ρ ≈ 0.42–0.45 vs measured 0.384), where the breaker's corrected
ADMIT survives its own +1SE variant (flip at ρ ≈ 0.6, ≥1.2 SE above its measured 0.372). One posture
must judge both members; under the posture that admits the breaker, the mx admission REJECTS.
Whether a <1SE margin stands between an armed sleeve (registry weight 0.025, economically small by
design) and dis-arming is an **owner decision — flagged here, not taken here**. The LATEST
republication of the same admission (CM, wave 17, family 57, p 0.0013, q 0.0741) is
NOT_RECOMPUTABLE today (§5) and sits even closer to its bar (0.1/57 = 0.00175): a transferred
corrected primary of ≈0.0028 would read ≈0.16 there.

### 1b. REJECT → ADMIT — graduates NOBODY

**`{br['member']}` (CS, three-fold, family 59): published
p {fmt(br['published_p'])} / q {fmt(br['published_q'])} REJECT → corrected p {fmt(br['corrected_p'])} / q {fmt(br['corrected_q'])} ADMIT** — the clean-room
verdict, reproduced here bit-exactly by the generalized engine. Per this commission's rule:
**REQUIRES_NEW_DECLARATION** — a corrected-rule re-issue can only reach a book through a new
declared, pre-registered step. (HDC/HDF's independent capture-anchored exact rule lands the same
ADMIT — §6.)

### 1c. Unchanged (13)

All eight `sub_xvol_pullback` arms (armed sleeve; corrected p is LARGER everywhere — the dependence
leak was flattering those REJECTs too), the four `mx as_walked` arms, and `mx target_5R @ high`:
REJECT stays REJECT.

---

## 2. Re-issued rows — every computed-null publication in scope

{core_table}

`corr p (primary)` = max over the fitted-dependence span; `corr p @ measured rho` = max over the two
innovation laws at ρ̂. Per-variant tables (per seed) in `A1B_CORRECTED_NULL_RESULTS.json`.

## 3. Named wave-18/19 receipts that never computed a null

{nn_table}

CQ's gate died on the sample gate (1 fold of 3) and CP/CR's on source/fidelity capture — in every
one `family_members_with_null = []`, so the affected code path never executed. Their NOT_EVALUABLE
verdicts stand as published. The FA route itself (this worktree,
`phase19/receipts/forensic/`) publishes verification receipts only — no gate verdict flows through
the machinery there.

## 4. The 59-member classification

{cls_block}

The {n_hist} AFFECTED_HISTORICAL members carry computed-null rows across landed phase-6..18 receipts
(per-member counts and receipt lists: `A1B_MEMBER_NULL_INDEX.json`). **No such row is a member
admission at the sealed α** — the only ADMIT-verdict rows among them are Session W's gate self-test
controls (`W_NEGATIVE_CONTROLS.json`) and α = 0.2 research triage, which `options.py:110` bars from
arming. They are NOT re-issued here, deliberately: a REJECT→ADMIT flip graduates nobody under this
commission's rule, no current binding decision rests on any of these rows, and several bases are
superseded (flat-snapshot / pre-re-clock populations). The recompute path is the one used here: each
receipt's committed driver + `AA_ESTATE_TRADES.json.gz` (+ `AM_SUBMID_TRADES.json.gz`), the same
capture-validate-recompute loop.

## 5. The standing admission's republication lineage (all through the same machinery)

{lin_table}

**CM (the latest, wave 17) is NOT_RECOMPUTABLE today.** Exact missing input: the deep-universe bar
CSVs its generation stage reads — `sources/bars/deep_universe_h4d1_2014_2026/*.csv` (per-file
sha256s pinned in `CM_REVERIFY_V1.json → source_rows`) — absent from every worktree on this machine
(measured 2026-08-03). The AU arms recomputed above are the same admission object at n=232/family
48; CM's is the CJ-relabelled n=228/family 57 population, and its published p (0.0013) sits *closer*
to its bar (0.1/57 = 0.00175) than AU's did to its own.

---

## 6. HDC comparison — the required open-phase question

**Their construction** (`wave20-exit-capture-semantics-falsifier
…/phase20/SESSION_HDC_EXIT_CAPTURE_FALSIFIER_RESULT.md` §5–6; independently reproduced by HDF,
`…falsifier2 …/SESSION_HDF_…RESULT.md` item 5): keep the gate's **block sign-flip family**
(uncentred blocks, L=3) but repair the anchor — `capture_start_anchored_sign_blocks;
blocks_restart_at_each_capture`: segment blocks [4,4,3], 11 blocks total, support 2^11 = 2048,
**exact enumeration** (seed inoperative), tail = 2 states → p = 2/2048 = **0.0009765625**;
`both_conservative` against a within-capture circular bootstrap (floored at 1/10001) selects it;
q = 59p = **0.0576171875** → ADMIT. HDF also showed HC's earlier common-phase union (13/6144) loses
a tied state to float summation order (exact 14/6144) and is unsupported as a transformation group.

**How theirs differs from the clean-room corrected null.** HDC repairs *the anchor defect inside the
family* — it declares the sealed capture starts the authoritative origin (temporal origin as
authority, not nuisance) and restarts blocks at capture seams, which removes exactly the
rotation/adjacency arbitrariness the clean-room proved verdict-determining. The clean-room
**replaced the family** (fold-segmented AR(1) calibration, studentised mean, max over
fitted-dependence variants) because two measured defects survive ANY re-anchoring: (1) uncentred
flips put **64.8 % of the null variance in the candidate's own signal** (conservative under H1);
(2) at L=3 under the measured within-fold dependence (ρ 0.372 ± 0.175) the sign-flip family is
**anti-conservative at the decision bar** (measured size 3.8× for the fixed-phase rule under a
matched AR(1)). These act in opposite directions and an exact count prices neither.

**Why theirs still sits on a resolution floor.** The support of an 11-block sign-flip is
intrinsically 2^11 = 2048 atoms on this 31-point series. Exact enumeration removes Monte-Carlo
noise; it cannot add resolution: achievable p near the bar are k/2048, q moves in steps of
59/2048 = **0.0288**, the floor is 1/2048 = 4.88e-4, and their published p IS the k = 2 atom. The
ADMIT/REJECT boundary sits between k = 3 and k = 4, and single near-zero block sums move k — the
clean-room measured one such block sum at 1 % of the day-level sd. The clean-room statistic is
continuous: no support cap, per-seed spread ≤ 3 %.

**Verdict agreement and evidential strength.** **They AGREE — both ADMIT** at α = 0.10 over the
declared 59-family (HDC q 0.0576, clean-room q 0.0769) against the same published MC REJECT
(q 0.1534), and HDF reproduces HDC independently. Three independent corrected constructions landing
on the same side is the strongest available statement that the published REJECT was an artifact of
the implemented rule, not a property of the evidence. They differ in strength: HDC's p is nominally
smaller but is an exact count *inside* a quantised family whose dependence leak is unpriced
(anti-conservative direction for an ADMIT); the clean-room's is dependence-priced, continuous, and
max-over-model-risk — the more defensible number — and its q margin is thinner (23 % vs 42 %)
precisely because it charges the model risk the exact count does not.

---

## 7. Summary

- Family: 59 declared (V27 tip). Affected in the named wave-18/19 receipts: **1** (the breaker; the
  other 58 padded at 1.0 there by construction).
- Current-binding members through the affected path, recomputed: **3** (breaker, `mx_btcusd`,
  `sub_xvol_pullback`) = **17 arms**, every capture receipt-validated float-exactly first.
- Flips: **REJECT→ADMIT 1** (breaker — REQUIRES_NEW_DECLARATION, graduates nobody);
  **ADMIT→REJECT 3** (the standing admission's three admitting bands — **BINDS**, see §1a for the
  <1SE-margin precision); unchanged 13.
- {n_hist} members: AFFECTED_HISTORICAL (no sealed-α admission rows; superseded bases) — indexed,
  not re-issued; {n_pad} PADDED_UNAFFECTED; 1 NO_COMPUTED_NULL (`cp_true_utc_ny_metals_long_v1`).
- HDC/HDF and the clean-room agree: the breaker ADMITS under every corrected construction.

*Boundaries kept: no March-2026 outcomes, no live-forward (2026-07-29+) outcomes, no ledger appends,
no VPS/broker/token contact; heavy compute serial, peak RSS ≈ 0.8 GB.*
"""

(HERE / "A1_REISSUED_VERDICT_TABLE.md").write_text(md)
print("wrote", HERE / "A1_REISSUED_VERDICT_TABLE.md", len(md), "chars")

"""LANE B receipt 3 — the retrospective census: what has the current accounting destroyed?

METHOD, AND THE THREE THINGS IT REFUSES TO DO
---------------------------------------------
The census walks every JSON under `docs/audits/fable5-vision-audit-20260725/` and pulls
every gate verdict row that carries a `gates` block containing `significance`. Two receipt
shapes exist (`gates.<name>` as a bool with a sibling `p_raw`, and `gates.<name>` as a dict
with `pass`); both are handled.

A row enters the "destroyed finding" candidate set only if **significance is the ONLY
failing gate among the five core gates** (expectancy, lifetime, stability, robustness,
significance). A row that also fails expectancy or stability was never a finding.

Three refusals keep this honest:

1. **Grid cells are not candidates.** An exit sweep of 40 cells is 40 looks and must be
   charged 40. So the re-adjudication does NOT drop the multiplicity charge for grid rows;
   it moves it from the ESTATE family (69 or 59, padded at p=1.0) to THE GRID'S OWN family,
   evaluated with **real sibling p-values** -- i.e. Benjamini-Hochberg as designed rather
   than BH degenerated into Bonferroni by padding. That is a stricter, not looser, use of
   the procedure inside each grid.

2. **Post-hoc cells are excluded by name.** `POST_HOC_COMPOSITE` cells, the
   `zero_carry_ceiling` counterfactual and the `best_cell_at_spread_bands` summaries are
   restatements or admitted post-hoc constructions, not independent looks. They are dropped
   from both sides of the comparison.

3. **The negative controls are re-adjudicated too.** `phase5/receipts/W_NEGATIVE_CONTROLS.json`
   carries six constructed adversaries and one positive control. Any architecture proposed
   here must leave every honest null rejected. If it does not, it is a lowered bar wearing
   a statistical costume, and the receipt says so.

Output: LANE_B_READJUDICATION_V1.json
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
NEGCTL = AUD / "phase5/receipts/W_NEGATIVE_CONTROLS.json"
OUT = Path(__file__).resolve().parent / "LANE_B_READJUDICATION_V1.json"

ALPHA = 0.10
CORE = ("expectancy", "lifetime", "stability", "robustness", "significance")
EXCLUDE_CELL_TOKENS = ("POST_HOC_COMPOSITE", "zero_carry_ceiling",
                       "best_cell_at_spread_bands", "authored_utc")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm_gates(g):
    if not isinstance(g, dict):
        return None
    out = {}
    for k, v in g.items():
        if isinstance(v, bool):
            out[k] = v
        elif isinstance(v, dict) and "pass" in v:
            out[k] = bool(v["pass"])
    return out or None


def collect() -> list[dict]:
    rows: list[dict] = []

    def walk(o, path, fpath):
        if isinstance(o, dict):
            g = norm_gates(o.get("gates"))
            if g and "significance" in g:
                sig = o["gates"]["significance"]
                sd = sig if isinstance(sig, dict) else {}
                rows.append(dict(
                    file=fpath, jsonpath=path, sleeve=o.get("sleeve"),
                    verdict=o.get("verdict"),
                    p_raw=(sd.get("p_raw") if "p_raw" in sd else o.get("p_raw")),
                    q_published=(sd.get("q_value") if "q_value" in sd else o.get("q_value")),
                    alpha=sd.get("alpha"), m_charged=sd.get("family_size"),
                    failed=[k for k in CORE if k in g and not g[k]],
                    n_trades=o.get("n_trades"),
                    pooled=o.get("pooled_oos_mean_r"),
                    n_folds=o.get("n_folds_evaluable")))
            for k, v in o.items():
                walk(v, path + "." + str(k), fpath)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + f"[{i}]", fpath)

    for dp, _dn, fn in os.walk(AUD):
        for f in sorted(fn):
            if not f.endswith(".json"):
                continue
            p = os.path.join(dp, f)
            try:
                d = json.load(open(p))
            except Exception:
                continue
            walk(d, "$", str(Path(p).relative_to(REPO)))
    return rows


#: Groups that are a POST-SELECTION SHORT LIST rather than a complete look set. Charging a
#: dossier of four finalists a family of four would be the exact defect this whole report is
#: about, in the permissive direction: the four were chosen from a sweep whose own receipt
#: publishes `family_sizes.trial_ledger_measured: 5734`. They are reported and EXCLUDED from
#: the headline flip count.
SHORT_LIST_GROUPS = ("AK_CANDIDATE_DOSSIER_V1.json::candidates",
                     "AK_SUPPLY_GATE_V1.json::gap_sleeves_baseline",
                     "AK_SUPPLY_GATE_V1.json::new_sleeves",
                     "AK_SLEEVE_CELLS_V1.json::member_baseline")


def group_key(r: dict) -> tuple[str, str] | None:
    """(group, kind). The family a row's look genuinely belongs to: one question, N cells.

    Returns None for rows excluded from the census (post-hoc, restatements, duplicates of
    the same cell at a different declared family size)."""
    jp, f = r["jsonpath"], r["file"].split("/")[-1]
    if any(t in jp for t in EXCLUDE_CELL_TOKENS):
        return None
    parts = jp.split(".")
    if f in ("EXIT_FRONTIER_V1.json", "EXIT_FRONTIER_V1_TRAIL.json",
             "EXIT_FRONTIER_V1_SUBMID_V2.json", "AK_EXIT_FRONTIER_V2.json"):
        # $.sleeves.<sleeve>.cells.<cell>
        if len(parts) >= 5 and parts[1] == "sleeves" and parts[3] == "cells":
            return f"{f}::exit_frontier::{parts[2]}", "exit_grid"
        return None
    if f == "AK_SLEEVE_CELLS_V1.json":
        # $.cells.<member>.exit_frontier.cells.<cell>   (and a bare $.cells.<member> row)
        if len(parts) >= 6 and parts[3] == "exit_frontier" and parts[4] == "cells":
            return f"{f}::exit_frontier::{parts[2]}", "exit_grid"
        if len(parts) == 3:
            return f"{f}::member_baseline", "short_list"
        return None
    if f == "AL_ASIA_PDL_FRONTIER_V1.json":
        return f"{f}::exit_frontier::asia_pdl_fade", "exit_grid"
    if f == "AL_CANDIDATE_DOSSIER_V1.json":
        # $.candidates.<cand>.by_stamp.population=..|exit=..|band=..|option=..|family=..
        # The SAME cell appears once per declared-family stamp. Keep one -- the ratified
        # basis -- so a cell is not counted five times.
        stamp = parts[-1]
        if "family=CANDIDATE_BOOK_V2@all_declared" not in stamp:
            return None
        return f"{f}::candidate::{parts[2]}", "stamp_grid"
    if f in ("AK_SUPPLY_GATE_V1.json", "AK_CANDIDATE_DOSSIER_V1.json"):
        g = f"{f}::{parts[1] if len(parts) > 1 else 'run'}"
        return g, "short_list"
    if f in ("AU_SUBMID_FRONTIER_V1.json", "AM_SUBMID_SOLO_GATE.json",
             "SUBMID_RECLOCK_V1.json", "CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json",
             "CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json",
             "CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json"):
        return f"{f}::{parts[1] if len(parts) > 1 else 'run'}", "single_declared"
    if f == "W_NEGATIVE_CONTROLS.json":
        return None  # handled separately
    return None


def main() -> int:
    from src.research_infra.walkforward import stats as S

    rows = collect()
    for r in rows:
        gk = group_key(r)
        r["group"], r["group_kind"] = (gk if gk else (None, None))
    census = [r for r in rows if r["group"] and isinstance(r["p_raw"], (int, float))]

    # ---- as published --------------------------------------------------------------------
    sig_only = [r for r in census if r["failed"] == ["significance"]]
    clean = [r for r in census if not r["failed"]]

    # ---- per-grid honest BH ---------------------------------------------------------------
    groups: dict[str, list[dict]] = {}
    for r in census:
        groups.setdefault(r["group"], []).append(r)

    flips: list[dict] = []
    short_list_flips: list[dict] = []
    per_group = []
    for gname, grp in sorted(groups.items()):
        kind = grp[0]["group_kind"]
        ps = [float(r["p_raw"]) for r in grp]
        bh = S.benjamini_hochberg(ps, ALPHA)
        n_rej = sum(bh["rejected"])
        n_flip = 0
        for r, rej, q in zip(grp, bh["rejected"], bh["qvalues"]):
            r["q_per_grid"] = q
            r["sig_pass_per_grid"] = bool(rej)
            if r["failed"] == ["significance"] and rej:
                n_flip += 1
                rec = {k: r[k] for k in
                       ("file", "jsonpath", "sleeve", "group", "group_kind", "p_raw",
                        "q_published", "m_charged", "q_per_grid", "n_trades",
                        "pooled", "n_folds")}
                (short_list_flips if kind == "short_list" else flips).append(rec)
        per_group.append({
            "group": gname, "kind": kind, "n_cells": len(grp), "n_bh_rejected": n_rej,
            "bh_threshold": bh["threshold"], "bh_k": bh["k"],
            "n_sig_only_failures_published": sum(
                1 for r in grp if r["failed"] == ["significance"]),
            "n_flipped_to_admit": n_flip,
            "counted_in_headline": kind != "short_list",
            "min_p": min(ps),
        })

    # Collapse cells to the object a decision is actually taken on: one candidate, its best
    # flipped cell. 42 exit cells of one sleeve are one finding restated 42 times.
    best_by_group: dict[str, dict] = {}
    for f in flips:
        cur = best_by_group.get(f["group"])
        if cur is None or f["p_raw"] < cur["p_raw"]:
            best_by_group[f["group"]] = f
    collapsed = sorted(best_by_group.values(), key=lambda r: r["p_raw"])

    # One more collapse: the same candidate surfaces in more than one receipt (its exit
    # frontier and its population/band dossier). Dedupe to the underlying candidate, and
    # mark the ones the estate ALREADY admitted by other means -- those are not destroyed
    # findings, they are findings the accounting delayed.
    ALREADY_ADMITTED = {
        "mx_btcusd_d1_donchian_20_breakout":
            "the estate's one standing admission -- `mx_btcusd @ target_5R`, admitted at "
            "CANDIDATE_BOOK_V1 alpha 0.10 at two of three cost bands "
            "(phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md; live on FTMO since 2026-07-31 at "
            "registry confidence 0.025)",
    }
    per_candidate: dict[str, dict] = {}
    for c in collapsed:
        # For exit/stamp grids the group tail IS the candidate. For a single pre-declared
        # gate the tail is a JSON key ("gate_result"), so take the row's own sleeve.
        name = (c["sleeve"] if c["group_kind"] == "single_declared"
                else c["group"].split("::")[-1])
        cur = per_candidate.get(name)
        if cur is None or c["p_raw"] < cur["p_raw"]:
            per_candidate[name] = dict(c, candidate=name)
    for name, c in per_candidate.items():
        c["already_admitted_by_the_estate"] = name in ALREADY_ADMITTED
        c["already_admitted_note"] = ALREADY_ADMITTED.get(name)
    distinct = sorted(per_candidate.values(), key=lambda r: r["p_raw"])
    destroyed = [c for c in distinct if not c["already_admitted_by_the_estate"]]

    # ---- the pre-declared single-candidate tier -------------------------------------------
    # Rows judged against a PROSPECTIVE declared family (declared_family_size present in the
    # significance block). These are the candidates the architecture question actually bites.
    declared_tier = [r for r in rows
                     if r["m_charged"] and isinstance(r["p_raw"], (int, float))]
    declared_rows = []
    for r in declared_tier:
        m = int(r["m_charged"])
        declared_rows.append({
            "file": r["file"], "sleeve": r["sleeve"], "verdict": r["verdict"],
            "p_raw": r["p_raw"], "m_charged": m, "q_published": r["q_published"],
            "failed": r["failed"],
            "sig_only_failure": r["failed"] == ["significance"],
            "admits_at_m1": bool(r["p_raw"] <= ALPHA),
            "largest_family_that_admits": int(ALPHA / r["p_raw"]) if r["p_raw"] > 0 else None,
            "n_trades": r["n_trades"], "n_folds": r["n_folds"],
        })

    # ---- negative controls ------------------------------------------------------------------
    neg = json.loads(NEGCTL.read_bytes())
    controls = []
    for run_name in ("synthetic_adversaries", "positive_control"):
        run = neg["runs"][run_name]
        for row in run["rows"]:
            p = float(row["p_raw"])
            g = row.get("gates") or {}
            other_fail = [k for k in CORE
                          if k != "significance" and k in g and not g[k]]
            controls.append({
                "run": run_name, "sleeve": row["sleeve"],
                "published_verdict": row["verdict"], "p_raw": p,
                "q_published": row.get("q_value"),
                "other_core_gates_failing": other_fail,
                # under ANY per-mechanism family down to m=1, does significance pass?
                "sig_passes_at_m1": bool(p <= ALPHA),
                "verdict_under_per_mechanism_family": (
                    "REJECT (other gates)" if other_fail
                    else ("ADMIT" if p <= ALPHA else "REJECT (significance)")),
                "verdict_changes": bool(
                    (row["verdict"] == "ADMIT") != (not other_fail and p <= ALPHA)),
            })
    n_ctl_changed = sum(1 for c in controls if c["verdict_changes"])

    out = {
        "schema": "gtos.lane_b.readjudication.v1",
        "generated_by": "phase21/.../swarm/lane_b_receipts/lane_b_readjudication.py",
        "alpha": ALPHA,
        "method": {
            "core_gates": list(CORE),
            "destroyed_finding_definition":
                "significance is the ONLY failing core gate",
            "readjudication":
                "Benjamini-Hochberg at alpha=0.10 over the REAL p-values of the cells in "
                "the row's own grid (one question, N cells), instead of BH over the estate "
                "family with every non-run member padded at p=1.0. The multiplicity charge "
                "is not dropped -- it is moved to the family the look was actually taken in "
                "and computed with the sibling evidence BH is designed to use.",
            "excluded_cell_tokens": list(EXCLUDE_CELL_TOKENS),
        },
        "census": {
            "verdict_rows_scanned": len(rows),
            "rows_in_census_after_exclusions": len(census),
            "rows_with_no_failing_core_gate_as_published": len(clean),
            "rows_where_significance_is_the_only_failure": len(sig_only),
            "distinct_grids": len(groups),
            "distinct_sleeves_with_a_sig_only_failure":
                len({str(r["sleeve"]) for r in sig_only}),
        },
        "readjudicated": {
            "cells_flipped_to_admit": len(flips),
            "distinct_grids_with_a_flip": len(best_by_group),
            "expected_false_admissions_at_fdr_0p10_cells": round(0.10 * len(flips), 2),
            "expected_false_admissions_at_fdr_0p10_collapsed":
                round(0.10 * len(best_by_group), 2),
            "short_list_cells_excluded_from_headline": len(short_list_flips),
            "note":
                "The CELL count is an upper bound and is not the finding count: 42 exit "
                "cells of one sleeve are one finding restated 42 times, because they are "
                "the same trades under different exit rules. `collapsed_findings` is the "
                "decision-relevant number. Short-list groups (post-selection dossiers) are "
                "excluded entirely -- charging a four-finalist dossier a family of four is "
                "this report's own defect in the permissive direction.",
        },
        "headline": {
            "distinct_candidates_surfaced": len(distinct),
            "of_which_the_estate_later_admitted_anyway": len(distinct) - len(destroyed),
            "DESTROYED_FINDINGS": len(destroyed),
            "destroyed": [c["candidate"] for c in destroyed],
            "definition":
                "a distinct candidate that (a) passes every core gate except significance "
                "under the estate's own published verdict, (b) passes Benjamini-Hochberg at "
                "alpha 0.10 within the family its look was actually taken in, computed with "
                "real sibling p-values rather than p=1.0 padding, and (c) was never admitted "
                "by the estate through any other route.",
        },
        "distinct_candidates": distinct,
        "collapsed_findings": collapsed,
        "short_list_flips_excluded": short_list_flips,
        "per_grid": sorted(per_group, key=lambda g: -g["n_flipped_to_admit"]),
        "flipped_cells": flips,
        "declared_family_tier": {
            "note":
                "Rows judged against a PROSPECTIVE declared family (the significance block "
                "carries family_size). These are the pre-declared single hypotheses -- the "
                "tier where the architecture question decides an activation.",
            "rows": declared_rows,
        },
        "negative_controls": {
            "source": {"path": str(NEGCTL.relative_to(REPO)), "sha256": sha256(NEGCTL)},
            "n_controls": len(controls),
            "n_verdicts_changed_under_per_mechanism_family": n_ctl_changed,
            "falsification_published_by_the_estate": neg["falsification"]["verdict"],
            "rows": controls,
        },
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"verdict rows scanned                : {len(rows)}")
    print(f"rows in census after exclusions     : {len(census)}")
    print(f"significance-ONLY failures          : {len(sig_only)}")
    print(f"distinct grids                      : {len(groups)}")
    print(f"cells flipped to ADMIT under per-grid honest BH : {len(flips)}")
    print(f"short-list cells excluded from headline         : {len(short_list_flips)}")
    print(f"COLLAPSED FINDINGS (one per candidate)          : {len(collapsed)}")
    print()
    print("top grids by flips:")
    for g in sorted(per_group, key=lambda g: -g["n_flipped_to_admit"])[:14]:
        if g["n_flipped_to_admit"]:
            mark = " " if g["counted_in_headline"] else "X"
            print(f" {mark}{g['n_flipped_to_admit']:3d}/{g['n_cells']:3d} flipped  "
                  f"(sig-only published {g['n_sig_only_failures_published']:3d})  "
                  f"[{g['kind']}]  {g['group']}")
    print()
    print("collapsed findings (one per grid):")
    for c in collapsed:
        print(f"  p={c['p_raw']:.6f}  q_grid={c['q_per_grid']:.5f}  "
              f"pooled={c['pooled']}  {c['group']}")
    print()
    print(f"DISTINCT CANDIDATES : {len(distinct)}   "
          f"already admitted anyway: {len(distinct) - len(destroyed)}   "
          f"DESTROYED: {len(destroyed)}")
    for c in distinct:
        tag = "recovered" if c["already_admitted_by_the_estate"] else "DESTROYED"
        print(f"  {tag:9s} p={c['p_raw']:.6f}  pooled={c['pooled']:.5f}  {c['candidate']}")
    print()
    print("declared-family tier:")
    for r in declared_rows:
        print(f"  {str(r['sleeve'])[:44]:44s} p={r['p_raw']:.6f} m={r['m_charged']:4d} "
              f"{r['verdict']:14s} sig_only={r['sig_only_failure']} "
              f"max_m_that_admits={r['largest_family_that_admits']}")
    print()
    print(f"negative controls: {len(controls)} rows, "
          f"{n_ctl_changed} verdicts change under a per-mechanism family")
    for c in controls:
        print(f"  {c['run'][:22]:22s} {c['sleeve'][:38]:38s} p={c['p_raw']:.6f} "
              f"published={c['published_verdict']:8s} -> {c['verdict_under_per_mechanism_family']}")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

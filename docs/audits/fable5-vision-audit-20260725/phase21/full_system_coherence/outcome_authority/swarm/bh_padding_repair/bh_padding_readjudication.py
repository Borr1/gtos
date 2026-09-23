"""Re-adjudication under the REPAIRED gate: same families, corrected arithmetic.

WHAT THIS IS, AND HOW IT DIFFERS FROM LANE B'S CENSUS
-----------------------------------------------------
Lane B established the defect and measured its blast radius by moving each look's
multiplicity charge to the family the look was actually taken in (a grid of 61 exit cells
charged 61 rather than the estate's 59). That is a defensible architecture proposal
(`LANE_B_MULTIPLICITY_ARCHITECTURE_V1.md` section 5, Option 2) and it is a family
RE-SPECIFICATION.

This receipt deliberately does NOT re-specify anything. The commission is explicit: *do not
re-declare or re-size the family to make anything pass — the family is what it is; you are
fixing the arithmetic applied to it.* So:

    RULE R.  For each look-set G with published family size m_pub:
               m         = max(m_pub, |G|)          <- never shrunk, ratchet direction only
               observed  = every REAL p-value in G   <- the repair: no fabricated 1.0s
               unobserved= m - |G|                    <- denominator only, no p-value asserted
               verdict   = stats.benjamini_hochberg(observed, 0.10, family_size=m)

`m` can only go UP relative to what was published, never down. Where a grid holds more cells
than the estate family charged, the bill grows to cover them — an exit sweep of 61 cells is
charged at least 61. Where it holds fewer, the estate's own declared bill stands. Nothing
here lowers a bar.

The correction is computed by the PRODUCTION function
(`src.research_infra.walkforward.stats.benjamini_hochberg`) with the repaired
`family_size=` argument, not by a re-implementation — so this receipt exercises the code
that ships.

THE CENSUS IS LANE B'S, UNCHANGED. Its collector and grouping are imported from
`../lane_b_receipts/lane_b_readjudication.py` so the two are strictly comparable and a
difference in the result cannot come from a difference in the population.

Output: BH_PADDING_READJUDICATION_V1.json
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[7]
sys.path.insert(0, str(REPO))

LANE_B = HERE.parent / "lane_b_receipts" / "lane_b_readjudication.py"
OUT = HERE / "BH_PADDING_READJUDICATION_V1.json"
ALPHA = 0.10

#: The four Lane B named as destroyed, by the substring that identifies them in the census.
DESTROYED = {
    "cq_current_breaker_re_entry_inverted_5d_stop_0p25d": "the inverted breaker",
    "sub_xvol_pullback": "an ARMED sleeve's exit repair",
    "mx_ethusd_d1_donchian_20_breakout": "never admitted",
    "thr_sub_xvol_pullback_vr14_s150_ac015": "never admitted",
}


#: Declared row 15 of CANDIDATE_BOOK_V1, whose real p-value exists in committed receipts.
#: Read from the artifacts rather than typed, and every one is checked against the file at
#: run time so a moved receipt fails loudly instead of freezing a stale number.
_SIBLING_SOURCES = (
    ("mx_btcusd_d1_donchian_20_breakout",
     "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_WALK.json",
     ("runs", "B_balanced|v1_1_zero_carry", "rows", 14),
     "zero-carry exit ceiling"),
    ("mx_btcusd_d1_donchian_20_breakout",
     "docs/audits/fable5-vision-audit-20260725/phase9/receipts/ADMISSION_CLOSER_V1.json",
     ("answer", "lowest_p_raw_reached"),
     "target_5R | RECORDED | mid"),
)


def _dig(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def _committed_sibling_p_values(repo: Path) -> list[dict]:
    out = []
    for member, rel, path, stamp in _SIBLING_SOURCES:
        f = repo / rel
        if not f.is_file():
            continue
        node = _dig(json.loads(f.read_text()), path)
        p = node.get("p_raw") if isinstance(node, dict) else float(node)
        name = node.get("sleeve") if isinstance(node, dict) else member
        if name != member:
            raise SystemExit(f"{rel}{path} names {name!r}, expected {member!r} — the "
                             f"receipt moved; re-locate it rather than editing the number")
        out.append({"member": member, "p_raw": float(p), "source": rel,
                    "jsonpath": "/".join(str(x) for x in path), "measured_at": stamp})
    return out


def _published_family_sizes(repo: Path, files: set[str]) -> dict[tuple[str, str], int]:
    """(file, jsonpath) -> the family size that row was ACTUALLY charged.

    Rule R must never shrink a family, and `gates.significance.family_size` is present only
    when the receipt stores `gates` as dicts. Most grid receipts store them as bare booleans
    and carry the bill elsewhere, so it has to be recovered or the fallback (`|G|`) silently
    becomes a re-sizing — the exact thing the commission forbids. Three sources, most
    specific first:

      1. the row's own `gates.significance.family_size` (dict-form receipts);
      2. the row's own `effective_family_size` (AL's dossier rows carry it per stamp);
      3. the receipt's `gate.declared_family_size` (EXIT_FRONTIER_V1 and AK_EXIT_FRONTIER_V2
         both publish 69 — AA's family — with the note that every cell is gated against it).

    Measured consequence of getting this right: both 61-cell exit frontiers are charged 69,
    not 61, and AK's 58-cell sweep 69 rather than 58.
    """
    out: dict[tuple[str, str], int] = {}
    for rel in sorted(files):
        f = repo / rel
        if not f.is_file():
            continue
        try:
            doc = json.loads(f.read_text())
        except Exception:
            continue
        file_default = ((doc.get("gate") or {}).get("declared_family_size")
                        if isinstance(doc.get("gate"), dict) else None)

        def walk(node, path):
            if isinstance(node, dict):
                if isinstance(node.get("gates"), dict):
                    sizes = [file_default]
                    sig = node["gates"].get("significance")
                    if isinstance(sig, dict):
                        sizes.append(sig.get("family_size"))
                    sizes.append(node.get("effective_family_size"))
                    got = [int(s) for s in sizes if isinstance(s, (int, float)) and s]
                    if got:
                        out[(rel, path)] = max(got)
                for key, val in node.items():
                    walk(val, path + "." + str(key))
            elif isinstance(node, list):
                for i, val in enumerate(node):
                    walk(val, path + f"[{i}]")

        walk(doc, "$")
    return out


def _load_lane_b():
    spec = importlib.util.spec_from_file_location("lane_b_readjudication", LANE_B)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    from src.research_infra.walkforward import stats as S

    lb = _load_lane_b()
    scanned = lb.collect()
    n_scanned = len(scanned)
    for r in scanned:
        gk = lb.group_key(r)
        r["group"], r["group_kind"] = (gk if gk else (None, None))
    census = [r for r in scanned if r["group"] and isinstance(r["p_raw"], (int, float))]

    charged = _published_family_sizes(REPO, {r["file"] for r in census})
    for r in census:
        recovered = charged.get((r["file"], r["jsonpath"]))
        if isinstance(r["m_charged"], (int, float)) and r["m_charged"]:
            r["m_charged"] = max(int(r["m_charged"]), recovered or 0)
        else:
            r["m_charged"] = recovered

    groups: dict[str, list[dict]] = {}
    for r in census:
        groups.setdefault(r["group"], []).append(r)

    flips: list[dict] = []
    short_list_flips: list[dict] = []
    per_group = []
    degenerate_groups = 0
    for gname, grp in sorted(groups.items()):
        kind = grp[0]["group_kind"]
        ps = [float(r["p_raw"]) for r in grp]
        m_pub = max((int(r["m_charged"]) for r in grp
                     if isinstance(r["m_charged"], (int, float))), default=0)
        m = max(m_pub, len(ps))
        bh = S.benjamini_hochberg(ps, ALPHA, family_size=m)
        # The degeneracy stamp, computed the same way the repaired gate computes it:
        # BH rejects ranks 1..k, so at k <= 1 its rejection set IS Bonferroni's.
        rank2 = 2.0 * ALPHA / m
        n_below_rank2 = sum(1 for p in ps if p <= rank2)
        degenerate = bh["k"] <= 1
        degenerate_groups += int(degenerate)
        n_flip = 0
        for r, rej, q in zip(grp, bh["rejected"], bh["qvalues"]):
            r["q_repaired"] = q
            r["sig_pass_repaired"] = bool(rej)
            if r["failed"] == ["significance"] and rej:
                n_flip += 1
                rec = {k: r[k] for k in
                       ("file", "jsonpath", "sleeve", "group", "group_kind", "p_raw",
                        "q_published", "m_charged", "n_trades", "pooled", "n_folds")}
                rec.update(q_repaired=q, m_used=m, bh_k=bh["k"],
                           bh_threshold=bh["threshold"],
                           n_observed=bh["n_observed"], n_unobserved=bh["n_unobserved"])
                (short_list_flips if kind == "short_list" else flips).append(rec)
        per_group.append({
            "group": gname, "kind": kind, "n_cells": len(grp),
            "m_published": m_pub, "m_used_by_rule_R": m,
            "n_bh_rejected": sum(bh["rejected"]), "bh_k": bh["k"],
            "bh_threshold": bh["threshold"],
            "rank2_threshold": rank2,
            "n_observed_at_or_below_rank2": n_below_rank2,
            "degenerate_equals_bonferroni": degenerate,
            "n_sig_only_failures_published": sum(
                1 for r in grp if r["failed"] == ["significance"]),
            "n_flipped_to_admit": n_flip,
            "counted_in_headline": kind != "short_list",
            "min_p": min(ps),
        })

    sig_only = [r for r in census if r["failed"] == ["significance"]]

    # ---- SENSITIVITY: the bill nobody has identified ---------------------------------------
    #
    # Rule R charges each look-set the larger of its published `declared_family_size` and its
    # own cell count. For the exit frontiers that is 69 — AA's family, which the receipts
    # themselves name. But the same receipts publish TWO larger numbers for the same sweep:
    # `n_cells_gated` (1,507 for EXIT_FRONTIER_V1, 468 for AK) and `trial_ledger.n_trials`
    # (3,555 and 10,018). Lane B's finding that the estate holds seven simultaneous bills
    # spanning 543x is not something this repair fixes, and a flip that survives only at the
    # smallest of them is not a finding. Every flip is therefore re-priced at both larger
    # bills, and the count that survives all three is the one a decision should use.
    # The SMALLER bill, priced for completeness: what Rule R would return if `m_pub` could
    # not be recovered and the look-set's own cell count were used. Reported so the cost of
    # recovering the published bill is a number rather than a claim.
    flips_at_look_set_size = 0
    for gname, grp in sorted(groups.items()):
        if grp[0]["group_kind"] == "short_list":
            continue
        ps = [float(r["p_raw"]) for r in grp]
        small = S.benjamini_hochberg(ps, ALPHA, family_size=len(ps))
        flips_at_look_set_size += sum(
            1 for r, rej in zip(grp, small["rejected"])
            if r["failed"] == ["significance"] and rej)

    sensitivity = []
    file_bills: dict[str, dict[str, int]] = {}
    for rel in sorted({r["file"] for r in census}):
        f = REPO / rel
        if not f.is_file():
            continue
        try:
            doc = json.loads(f.read_text())
        except Exception:
            continue
        bills = {}
        if isinstance(doc.get("n_cells_gated"), int):
            bills["n_cells_gated"] = doc["n_cells_gated"]
        tl = doc.get("trial_ledger")
        if isinstance(tl, dict) and isinstance(tl.get("n_trials"), int):
            bills["trial_ledger_n_trials"] = tl["n_trials"]
        if bills:
            file_bills[rel] = bills
    for gname, grp in sorted(groups.items()):
        if not any(r["failed"] == ["significance"] and r.get("sig_pass_repaired")
                   for r in grp):
            continue
        ps = [float(r["p_raw"]) for r in grp]
        rel = grp[0]["file"]
        row = {"group": gname, "n_cells": len(ps),
               "flips_at_rule_R": sum(1 for r in grp if r["failed"] == ["significance"]
                                      and r.get("sig_pass_repaired"))}
        for label, m_alt in sorted(file_bills.get(rel, {}).items()):
            m_alt = max(m_alt, len(ps))
            alt = S.benjamini_hochberg(ps, ALPHA, family_size=m_alt)
            row[f"m_{label}"] = m_alt
            row[f"flips_at_{label}"] = sum(
                1 for r, rej in zip(grp, alt["rejected"])
                if r["failed"] == ["significance"] and rej)
            row[f"k_at_{label}"] = alt["k"]
        sensitivity.append(row)

    # Collapse to the object a decision is taken on: one look-set, its best flipped cell.
    best_by_group: dict[str, dict] = {}
    for f in flips:
        cur = best_by_group.get(f["group"])
        if cur is None or f["p_raw"] < cur["p_raw"]:
            best_by_group[f["group"]] = f
    collapsed = sorted(best_by_group.values(), key=lambda r: r["p_raw"])

    # The four Lane B named, each looked up by name in the repaired result.
    destroyed_status = []
    for token, note in DESTROYED.items():
        hits = [r for r in census
                if token in str(r.get("sleeve") or "") or token in str(r.get("group") or "")]
        sig_only_hits = [r for r in hits if r["failed"] == ["significance"]]
        flipped = [r for r in sig_only_hits if r.get("sig_pass_repaired")]
        best = min(sig_only_hits, key=lambda r: float(r["p_raw"])) if sig_only_hits else None
        destroyed_status.append({
            "candidate": token, "lane_b_note": note,
            "n_census_rows": len(hits),
            "n_significance_only_failures": len(sig_only_hits),
            "n_flipped_under_rule_R": len(flipped),
            "verdict_under_repaired_gate": (
                "ADMIT" if flipped else ("REJECT" if sig_only_hits else "NOT_IN_CENSUS")),
            "best_row": (None if best is None else {
                "file": best["file"], "jsonpath": best["jsonpath"],
                "sleeve": best["sleeve"], "p_raw": best["p_raw"],
                "q_published": best["q_published"], "m_charged": best["m_charged"],
                "q_repaired": best.get("q_repaired"),
                "sig_pass_repaired": best.get("sig_pass_repaired"),
                "pooled_oos_mean_r": best["pooled"], "n_trades": best["n_trades"],
                "group": best["group"], "group_kind": best["group_kind"],
            }),
        })

    # ---- the negative controls, re-adjudicated under the SAME rule ------------------------
    #
    # SCOPE. `W_NEGATIVE_CONTROLS.json` holds five runs; only two are controls
    # (`synthetic_adversaries`, six constructed adversaries; `positive_control`, one real
    # edge). The other three (`real_minimal_carry*`, `real_structural_horizon_restricted`)
    # are real sleeves on real data and belong to the main census, not to the falsification
    # check. Pooling all five into one BH family — which an earlier revision of this script
    # did — invents a 21-member family that was never run and produces a spurious "1 verdict
    # changed" on `sub_mid_dn_revert`, a real sleeve, not an adversary. Each run is its own
    # family, exactly as `run_gate` was called.
    #
    # THE RESULT IS AN IDENTITY, NOT A COINCIDENCE. Both control runs published
    # `family_members_padded_at_p1: 0` and `declared_family_size: null` — six real p-values
    # in a family of six, one in a family of one. They are the only runs in the estate where
    # BH was already running as BH (k=2 at threshold 0.0333 on the adversaries). A repair
    # that only removes fabricated p-values cannot move a family that had none.
    neg = json.loads(lb.NEGCTL.read_text()) if lb.NEGCTL.is_file() else None
    neg_rows = []
    neg_runs = []
    if neg is not None:
        for run_name in ("synthetic_adversaries", "positive_control"):
            run = neg.get("runs", {}).get(run_name)
            if not run:
                continue
            pub_fam = (run.get("family") or {}).get("multiplicity") or {}
            rows = [r for r in run.get("rows", [])
                    if isinstance(r, dict) and isinstance(r.get("p_raw"), (int, float))]
            ps = [float(r["p_raw"]) for r in rows]
            m = max(int(pub_fam.get("m") or 0), len(ps))
            bh = S.benjamini_hochberg(ps, ALPHA, family_size=m)
            neg_runs.append({
                "run": run_name, "label": run.get("label"),
                "m_published": pub_fam.get("m"),
                "padded_at_p1_published": pub_fam.get("family_members_padded_at_p1"),
                "k_published": pub_fam.get("k"),
                "threshold_published": pub_fam.get("threshold"),
                "m_repaired": bh["m"], "k_repaired": bh["k"],
                "threshold_repaired": bh["threshold"],
                "n_observed": bh["n_observed"], "n_unobserved": bh["n_unobserved"],
                # Compared as a MULTISET: the published `family.multiplicity.qvalues` is
                # ordered by `fam_names`, the rows list by construction order, and the two
                # differ. The per-row `q_identical_to_published` field below is the ordered
                # check and is the authoritative one.
                "qvalues_reproduce_published_as_a_set": (
                    sorted(round(q, 12) for q in bh["qvalues"])
                    == sorted(round(float(q), 12) for q in pub_fam.get("qvalues", []))),
            })
            for r, rej, q in zip(rows, bh["rejected"], bh["qvalues"]):
                g = lb.norm_gates(r.get("gates")) or {}
                failed_pub = [k for k in lb.CORE if k in g and not g[k]]
                failed_now = [k for k in failed_pub if k != "significance"]
                if not rej:
                    failed_now = failed_now + ["significance"]
                verdict_now = "REJECT" if failed_now else "ADMIT"
                neg_rows.append({
                    "run": run_name, "sleeve": r.get("sleeve"), "p_raw": r["p_raw"],
                    "verdict_published": r.get("verdict"),
                    "q_published": r.get("q_value"),
                    "failed_published": failed_pub,
                    "q_repaired": q,
                    "q_identical_to_published": (
                        isinstance(r.get("q_value"), (int, float))
                        and abs(q - float(r["q_value"])) < 1e-12),
                    "significance_passes_repaired": bool(rej),
                    "failed_repaired": failed_now,
                    "verdict_repaired": verdict_now,
                    "verdict_changed": (str(r.get("verdict")) != verdict_now),
                    "caught_by": (failed_now[0] if failed_now else None),
                })

    # ---- the breaker: what the repair alone does, and what the ASSEMBLY does -------------
    #
    # Rule R holds the family at 59 and the breaker's look-set has exactly ONE real p-value,
    # so BH still cannot reach rank 2 and the verdict is unchanged. That is the honest
    # result of the arithmetic repair on its own, and it is reported as such.
    #
    # The repair's actual lever is that a REAL sibling p-value can now enter the step-up.
    # Both values below are read from committed receipts, not typed: declared row 15
    # (`mx_btcusd_d1_donchian_20_breakout`) is a member of the same CANDIDATE_BOOK_V1
    # declaration the breaker is charged against.
    cs = REPO / ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
                 "CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json")
    breaker_block = None
    if cs.is_file():
        csd = json.loads(cs.read_text())
        row = csd["gate_result"]["sleeves"][
            "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"]
        p_break = float(row["gates"]["significance"]["p_raw"])
        m_break = int(row["gates"]["significance"]["family_size"])
        q_pub = float(row["gates"]["significance"]["q_value"])
        alone = S.benjamini_hochberg([p_break], ALPHA, family_size=m_break)
        siblings = _committed_sibling_p_values(REPO)
        with_sib = []
        for sib in siblings:
            r = S.benjamini_hochberg([p_break, sib["p_raw"]], ALPHA, family_size=m_break)
            with_sib.append({
                **sib,
                "bh_k": r["k"], "bh_threshold": r["threshold"],
                "breaker_q": r["qvalues"][0],
                "breaker_significance_passes": bool(r["rejected"][0]),
                "sibling_q": r["qvalues"][1],
            })
        H = sum(1.0 / i for i in range(1, m_break + 1))
        by_rank_needed = next(
            (k for k in range(1, m_break + 1) if p_break <= k * ALPHA / (m_break * H)), None)
        breaker_block = {
            "p_raw": p_break, "family_size": m_break,
            "q_published": q_pub,
            "reproduces_published_q_exactly": abs(alone["qvalues"][0] - q_pub) < 1e-15,
            "rank1_bar": ALPHA / m_break,
            "rank2_bar": 2.0 * ALPHA / m_break,
            "p_clears_rank2_bar": p_break <= 2.0 * ALPHA / m_break,
            "repair_alone": {
                "k": alone["k"], "threshold": alone["threshold"],
                "q": alone["qvalues"][0], "significance_passes": bool(alone["rejected"][0]),
                "n_observed": alone["n_observed"], "n_unobserved": alone["n_unobserved"],
                "degenerate_equals_bonferroni": True,
                "why": "one real p-value in a family of 59: the step-up cannot reach rank 2, "
                       "so BH is arithmetically Bonferroni and the verdict is UNCHANGED. "
                       "Removing the fabrication does not by itself admit anything.",
            },
            "with_one_real_declared_sibling": with_sib,
            "benjamini_yekutieli_does_not_rescue": {
                "H_m": H, "rank1_bar": ALPHA / (m_break * H),
                "rank_the_breaker_would_need": by_rank_needed,
                "siblings_strictly_below_it_required": (
                    None if by_rank_needed is None else by_rank_needed - 1),
                "rescued": bool(by_rank_needed is not None and by_rank_needed <= 2),
            },
            "family_hygiene_alone_does_not_rescue": [
                {"m": m, "rank1_bar": ALPHA / m, "q_if_only_observation": min(1.0, p_break * m),
                 "admits_with_no_sibling": p_break <= ALPHA / m}
                for m in (59, 54, 39, 38)
            ],
        }

    out = {
        "schema": "gtos.bh_padding_repair.readjudication.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "alpha": ALPHA,
        "rule": {
            "name": "RULE_R",
            "m": "max(published family size for the look-set, number of real p-values in it)",
            "observed": "every real p-value in the look-set; no member is padded at p=1.0",
            "unobserved": "m - |G| declared members carried in the denominator only",
            "family_resizing": "NONE. m is never smaller than what was published.",
            "correction": "src.research_infra.walkforward.stats.benjamini_hochberg"
                          " (production, with the repaired family_size argument)",
        },
        "census": {
            "verdict_rows_scanned": n_scanned,
            "rows_in_census_after_exclusions": len(census),
            "rows_where_significance_is_the_only_failure": len(sig_only),
            "distinct_look_sets": len(groups),
            "look_sets_still_degenerate_bh_equals_bonferroni": degenerate_groups,
        },
        "readjudicated": {
            "cells_flipped_to_admit": len(flips),
            "distinct_look_sets_with_a_flip": len(best_by_group),
            "short_list_cells_excluded_from_headline": len(short_list_flips),
            "expected_false_admissions_at_fdr_0p10_cells": round(0.10 * len(flips), 3),
            "expected_false_admissions_at_fdr_0p10_collapsed": round(0.10 * len(collapsed), 3),
        },
        "bill_sensitivity": {
            "why": "the same receipts publish up to three bills for one sweep; a flip that "
                   "survives only the smallest of them is not a finding",
            "headline_flips_at_the_published_bill": len(flips),
            "headline_flips_if_m_were_the_look_set_size": flips_at_look_set_size,
            "rows": sensitivity,
        },
        "the_breaker": breaker_block,
        "destroyed_findings_status": destroyed_status,
        "collapsed_findings": collapsed,
        "flipped_cells": flips,
        "short_list_flips_excluded": short_list_flips,
        "per_look_set": per_group,
        "negative_controls": {
            "source": str(lb.NEGCTL.relative_to(REPO)) if neg is not None else None,
            "scope": "runs.synthetic_adversaries (6 constructed adversaries) + "
                     "runs.positive_control (1 real edge). The three real-sleeve runs in the "
                     "same file are census rows, not controls.",
            "n_controls": len(neg_rows),
            "n_verdicts_changed_under_rule_R": sum(1 for r in neg_rows
                                                   if r["verdict_changed"]),
            "n_q_values_identical_to_published": sum(
                1 for r in neg_rows if r["q_identical_to_published"]),
            "runs": neg_runs,
            "rows": neg_rows,
        },
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False, default=str))
    print(f"wrote {OUT.relative_to(REPO)}  sha256={hashlib.sha256(OUT.read_bytes()).hexdigest()}")
    print(f"  census {len(census)} rows, {len(sig_only)} significance-only failures, "
          f"{len(groups)} look-sets")
    print(f"  flips {len(flips)} cells -> {len(best_by_group)} distinct look-sets "
          f"({len(short_list_flips)} short-list cells excluded)")
    print(f"  negative controls: {sum(1 for r in neg_rows if r['verdict_changed'])} of "
          f"{len(neg_rows)} verdicts changed")
    for d in destroyed_status:
        print(f"  {d['candidate']}: {d['verdict_under_repaired_gate']} "
              f"({d['n_flipped_under_rule_R']}/{d['n_significance_only_failures']} "
              f"sig-only rows flip)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

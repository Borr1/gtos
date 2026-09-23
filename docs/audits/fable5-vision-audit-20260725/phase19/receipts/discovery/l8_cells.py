#!/usr/bin/env python3
"""l8_cells — emit the positive/negative CELL CENSUS appendix + the multiplicity ledger."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(os.path.join(HERE, f)))
out = []
P = out.append

S1 = L("L8_SWEEP1_SINGLE_V1.json")
S2 = L("L8_SWEEP2_V1.json")
S3 = L("L8_SWEEP3_V1.json")
HR = L("L8_HITRATE_V1.json")
EX = L("L8_EXCLUDE_V1.json")
PO = L("L8_POSITIVE_V1.json")

ledger = [
    ("single-axis sweep on gross_r (37 axes)", S1["cells_examined"], S1["cells_reported"]),
    ("pair sweep on clean gross_r (26 axes, 325 pairs)", S2["cells_examined"], S2["cells_reported"]),
    ("triple sweep on clean gross_r (26 axes, 2600 triples)", S3["cells_examined"], S3["cells_reported"]),
    ("honest 2R/-1R singles+pairs sweep (22 axes)", HR["cells_examined"], len(HR["singles"]) + len(HR["pairs"])),
    ("exclusion sweep (28 causal axes)", EX["cells_examined"], len(EX["bad_cells"])),
    ("positive census on delayed-fill pop (22 axes, 1+2+3)", PO["cells_examined"], PO["cells_reported"]),
]
P("## K. MULTIPLICITY LEDGER — every cell this lane looked at\n")
P("| sweep | cells examined | cells with n>=min | ")
P("|---|--:|--:|")
tot_e = tot_r = 0
for name, e, r in ledger:
    tot_e += e
    tot_r += r
    P("| %s | %d | %d |" % (name, e, r))
P("| decile sweep (16 continuous fields) | 141 | 141 |")
P("| limit-depth sweep (17 buckets x 4 cross-tabs) | 233 | 233 |")
P("| resolution-win-rate tables (26 axes) | 268 | 268 |")
P("| fill-speed x depth + rdp control | 26 | 26 |")
P("| entry-delay k sweep (13 k x 4 populations x 3 thirds) | 91 | 91 |")
P("| equal-exposure control (5 H x 6 cohorts) | 30 | 30 |")
P("| cost-gate value splits (8 + 10 overcharge) | 18 | 18 |")
P("| **TOTAL** | **%d** | **%d** |" % (tot_e + 141 + 233 + 268 + 26 + 91 + 30 + 18, tot_r + 141 + 233 + 268 + 26 + 91 + 30 + 18))
P("\nNo multiplicity correction is applied anywhere in this receipt. Report first, price later.\n")

P("\n## L. EVERY POSITIVE CELL, n>=50 — DELAYED-FILL CLEAN POPULATION, honest 2R/-1R\n")
P("Base for comparison: n=%d mean=%+.5f resWin=%.4f. %d of %d reported cells are positive.\n"
  % (PO["base"]["n"], PO["base"]["mean"], PO["base"]["res_win"], len(PO["positive"]), PO["cells_reported"]))
P("Top 300 by n*mean (impact). Full list in `L8_POSITIVE_V1.json` -> `positive`.\n")
P("| axes | values | n | mean | resWin | t | win | target | stop | mark | totalR | pos_thirds | J1 | J2 | J3 |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
TH = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]
for c in PO["positive"][:300]:
    th = [c["thirds"][t] for t in TH]
    P("| %s | %s | %d | %+.5f | %s | %+.2f | %.4f | %d | %d | %d | %+.1f | %d/%d | %s | %s | %s |" % (
        "+".join(c["keys"]), "\\|".join(c["vals"]), c["n"], c["mean"],
        ("%.4f" % c["res_win"]) if c["res_win"] else "-", c["t"], c["win"],
        c["target"], c["stop"], c["mark"], c["total_R"], c["pos_thirds"], c["eval_thirds"],
        *[("%+.3f" % v[1]) if v else "-" for v in th]))

P("\n## M. THE CONVERSE — reliably terrible cells (negative in ALL three January thirds)\n")
P("Top 150 by n*mean on the delayed-fill population. Full list in `L8_POSITIVE_V1.json` -> `negative`.\n")
P("| axes | values | n | mean | resWin | t | totalR |")
P("|---|---|--:|--:|--:|--:|--:|")
for c in PO["negative"][:150]:
    P("| %s | %s | %d | %+.5f | %s | %+.2f | %+.1f |" % (
        "+".join(c["keys"]), "\\|".join(c["vals"]), c["n"], c["mean"],
        ("%.4f" % c["res_win"]) if c["res_win"] else "-", c["t"], c["total_R"]))

P("\n## N. SINGLE-CELL EXCLUSION VALUE (metric gross_r, clean population)\n")
P("Base n=%d mean=%+.5f win=%.4f. `lift` = pool mean AFTER dropping the cell, minus base.\n"
  % (EX["base"]["n"], EX["base"]["mean"], EX["base"]["win"]))
P("| axis | value | n | win | cell mean | t | lift | pool after | share dropped | negative in all thirds |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|---|")
for c in EX["bad_cells"][:70]:
    P("| %s | %s | %d | %.4f | %+.5f | %+.2f | %+.5f | %+.5f | %.4f | %s |" % (
        c["axis"], c["value"], c["n"], c["win"], c["mean"], c["t"], c["lift"],
        c["pool_after_drop_mean"], c["share_dropped"], c["neg_all_thirds"]))
P("\n### N.1 greedy forward exclusion cascade\n")
P("| step | drop axis | drop value | dropped n | dropped mean | kept n | kept mean | kept win | kept honest |")
P("|--:|---|---|--:|--:|--:|--:|--:|--:|")
for s in EX["greedy_exclusion"]:
    P("| %d | %s | %s | %d | %+.5f | %d | %+.5f | %.4f | %+.5f |" % (
        s["step"], s["drop_axis"], s["drop_value"], s["dropped_n"], s["dropped_mean"],
        s["kept_n"], s["kept_mean"], s["kept_win"], s["kept_honest"]))

P("\n## O. POSITIVE CELLS FROM THE gross_r SWEEPS (pre-delay population)\n")
P("### O.1 single axis, n>=50, positive raw gross_r mean\n")
P("| axis | value | n | win | mean | t | clean n | clean mean | honest mean | J1 | J2 | J3 |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
pos1 = sorted([c for ax in S1["axes"].values() for c in ax if c["mean"] > 0], key=lambda c: -c["mean"])
for c in pos1:
    th = [c["thirds"][t] for t in TH]
    P("| %s | %s | %d | %.4f | %+.5f | %+.2f | %d | %s | %+.5f | %s | %s | %s |" % (
        c["axis"], c["value"], c["n"], c["win"], c["mean"], c["t"], c["clean_n"],
        ("%+.5f" % c["clean_mean"]) if c["clean_mean"] is not None else "-", c["honest_mean"],
        *[("%+.3f" % v["mean"]) if v else "-" for v in th]))
P("\n### O.2 pair cells, clean gross_r positive, n>=150, positive in all three thirds (top 120 by n*mean)\n")
P("| axes | values | n | win | mean | t | honest clean | J1 | J2 | J3 |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|")
p2 = [c for c in S2["cells"] if c["mean"] > 0 and c["n"] >= 150 and c["pos_thirds"] == 3]
p2.sort(key=lambda c: -c["mean"] * c["n"])
for c in p2[:120]:
    th = [c["thirds"][t] for t in TH]
    P("| %s | %s | %d | %.4f | %+.5f | %+.2f | %+.5f | %s | %s | %s |" % (
        "+".join(c["keys"]), "\\|".join(c["vals"]), c["n"], c["win"], c["mean"], c["t"],
        c["honest_clean_mean"], *[("%+.3f" % v["mean"]) if v else "-" for v in th]))
P("\n### O.3 triple cells, clean gross_r positive, n>=250, 3/3 thirds, t>=2.5 (all %d)\n"
  % len([c for c in S3["cells"] if c["mean"] > 0 and c["n"] >= 250 and c["pos_thirds"] == 3 and c["t"] >= 2.5]))
P("| axes | values | n | win | mean | t | honest clean | J1 | J2 | J3 |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|")
p3 = [c for c in S3["cells"] if c["mean"] > 0 and c["n"] >= 250 and c["pos_thirds"] == 3 and c["t"] >= 2.5]
p3.sort(key=lambda c: -c["mean"] * c["n"])
for c in p3:
    th = [c["thirds"][t] for t in TH]
    P("| %s | %s | %d | %.4f | %+.5f | %+.2f | %+.5f | %s | %s | %s |" % (
        "+".join(c["keys"]), "\\|".join(c["vals"]), c["n"], c["win"], c["mean"], c["t"],
        c["honest_clean_mean"], *[("%+.3f" % v["mean"]) if v else "-" for v in th]))
P("\n### O.4 honest 2R/-1R sweep: positive singles, and positive pairs n>=120 with 3/3 thirds\n")
P("| axes | values | n | mean | resWin | t | targetRate | stopRate | markRate | best T | best S | best mean |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
for c in HR["singles"]:
    d = c["declared"]
    if d["mean"] <= 0:
        continue
    b = c["best"]
    P("| %s | %s | %d | %+.5f | %s | %+.2f | %.4f | %.4f | %.4f | %.2f | %.2f | %+.5f |" % (
        "+".join(c["keys"]), "\\|".join(c["vals"]), d["n"], d["mean"],
        ("%.4f" % d["res_win"]) if d["res_win"] else "-", d["t"], d["target_rate"],
        d["stop_rate"], d["mark_rate"], b["target"], b["stop"], b["mean"]))
sel = [c for c in HR["pairs"] if c["declared"]["n"] >= 120 and c["pos_thirds"] == 3 and c["declared"]["mean"] > 0]
for c in sel[:120]:
    d = c["declared"]
    b = c["best"]
    P("| %s | %s | %d | %+.5f | %s | %+.2f | %.4f | %.4f | %.4f | %.2f | %.2f | %+.5f |" % (
        "+".join(c["keys"]), "\\|".join(c["vals"]), d["n"], d["mean"],
        ("%.4f" % d["res_win"]) if d["res_win"] else "-", d["t"], d["target_rate"],
        d["stop_rate"], d["mark_rate"], b["target"], b["stop"], b["mean"]))

open(os.path.join(HERE, "l8_CELLS_APPENDIX.md"), "w").write("\n".join(out))
print("wrote l8_CELLS_APPENDIX.md lines=%d bytes=%d" % (len(out), sum(len(x) for x in out)))
print("total cells examined:", tot_e + 141 + 233 + 268 + 26 + 91 + 30 + 18)

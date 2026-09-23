"""Normalize the 6 family CSVs into a unified K54 v2 feature catalog.

Usage:
    python research/ml_program/scripts/build_catalog_v2.py

Produces:
    research/ml_program/feature_catalogs/CATALOG_v2.csv

Schema (canonical):
    family, feature_name, subfamily, source, lookback,
    computation, stability_rho, stability_n, stability_p,
    expensive_flag, notes
"""
import csv
from pathlib import Path

FAMILIES = [
    "structure",
    "microstructure",
    "volatility",
    "time_session",
    "liquidity",
    "regime",
]

ROOT = Path(__file__).resolve().parents[1]
CATALOGS = ROOT / "feature_catalogs"
OUT_CSV = CATALOGS / "CATALOG_v2.csv"

CANONICAL = [
    "family",
    "feature_name",
    "subfamily",
    "source",
    "lookback",
    "computation",
    "stability_rho",
    "stability_n",
    "stability_p",
    "expensive_flag",
    "notes",
]


def normalize_row(family, row):
    out = {k: "" for k in CANONICAL}
    out["family"] = family

    if family in ("structure", "microstructure", "volatility"):
        out["feature_name"] = row.get("feature_name", "")
        out["source"] = row.get("source", "")
        out["lookback"] = row.get("lookback", "")
        out["computation"] = row.get("computation_summary", "")
        out["stability_rho"] = row.get("stability_rho", "")
        out["stability_n"] = row.get("stability_n", "")
        out["stability_p"] = row.get("stability_p", "")
        out["expensive_flag"] = row.get("expensive_flag", "")
    elif family == "time_session":
        out["feature_name"] = row.get("feature", "")
        out["subfamily"] = row.get("subfamily", "")
        out["source"] = row.get("source", "")
        out["lookback"] = row.get("lookback", "")
        out["computation"] = row.get("computation", "") or row.get("description", "")
        out["stability_rho"] = row.get("stability_spearman_rho", "")
        out["stability_n"] = row.get("stability_n", "")
        bits = []
        if row.get("dtype"):
            bits.append("dtype=" + row["dtype"])
        if row.get("leakage_check"):
            bits.append("leakage_check=" + row["leakage_check"])
        if row.get("stability_note"):
            bits.append(row["stability_note"])
        out["notes"] = "; ".join(bits)
    elif family == "liquidity":
        out["feature_name"] = row.get("feature_name", "")
        out["subfamily"] = row.get("sub_family", "")
        out["source"] = row.get("source", "")
        out["lookback"] = row.get("lookback", "")
        out["computation"] = row.get("comment", "")
        out["stability_rho"] = row.get("spearman_rho", "")
        out["stability_n"] = row.get("n", "")
        bits = []
        if row.get("abs_rho"):
            bits.append("abs_rho=" + row["abs_rho"])
        if row.get("tied_pct"):
            bits.append("tied_pct=" + row["tied_pct"])
        out["notes"] = "; ".join(bits)
    elif family == "regime":
        out["feature_name"] = row.get("feature_name", "")
        out["subfamily"] = row.get("group", "")
        out["source"] = row.get("source", "")
        out["lookback"] = row.get("lookback", "")
        out["computation"] = row.get("description", "")
        # Patch 3 (catalog_health_audit Section 3 soft-fail): regime CSV emits
        # literal "NA" strings for missing stability values; map to empty cell so
        # downstream readers see consistent type semantics across families.
        rho_raw = row.get("stability_spearman_pre_2026_04", "")
        out["stability_rho"] = "" if rho_raw == "NA" else rho_raw
        if row.get("dtype"):
            out["notes"] = "dtype=" + row["dtype"]

    return out


def safe_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def main():
    all_rows = []
    counts = {}
    for fam in FAMILIES:
        path = CATALOGS / (fam + ".csv")
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            family_rows = [normalize_row(fam, r) for r in reader]
        all_rows.extend(family_rows)
        counts[fam] = len(family_rows)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CANONICAL)
        writer.writeheader()
        writer.writerows(all_rows)

    print("Wrote " + str(len(all_rows)) + " rows to " + str(OUT_CSV))
    for fam, n in counts.items():
        print("  " + fam.ljust(15) + " " + str(n).rjust(4))

    scored = []
    for r in all_rows:
        rho = safe_float(r["stability_rho"])
        if rho is not None:
            scored.append((abs(rho), rho, r))
    scored.sort(key=lambda t: t[0], reverse=True)

    print("\nTop 20 features by |stability_rho| across all families:")
    print("  " + "family".ljust(15) + " " + "feature_name".ljust(50) + " " + "rho".rjust(8) + " " + "n".rjust(6))
    for abs_rho, rho, r in scored[:20]:
        n = r["stability_n"] or "-"
        print(
            "  "
            + r["family"].ljust(15)
            + " "
            + r["feature_name"].ljust(50)
            + " "
            + ("%+0.3f" % rho).rjust(8)
            + " "
            + str(n).rjust(6)
        )

    by_family_top = {}
    for fam in FAMILIES:
        fam_scored = [(abs_rho, rho, r) for (abs_rho, rho, r) in scored if r["family"] == fam]
        by_family_top[fam] = fam_scored[:5]

    print("\nTop 5 per family:")
    for fam, rows in by_family_top.items():
        print("  " + fam + ":")
        for abs_rho, rho, r in rows:
            print("    " + r["feature_name"].ljust(50) + " " + ("%+0.3f" % rho))


if __name__ == "__main__":
    main()

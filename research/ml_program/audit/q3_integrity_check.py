"""Q3 — Catalog integrity verification.

Checks:
1. CATALOG_v2.csv has exactly 1219 rows + header.
2. Per-family counts match the brief: structure 432, volatility 270,
   microstructure 187, time_session 138, liquidity 129, regime 63.
3. All 11 canonical columns present.
4. stability_rho values are valid floats or empty (no NaN/string).
5. Spot-check 5 random rows against original family CSVs.
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "feature_catalogs"
UNIFIED = CATALOG_DIR / "CATALOG_v2.csv"

EXPECTED_COUNTS = {
    "structure": 432,
    "volatility": 270,
    "microstructure": 187,
    "time_session": 138,
    "liquidity": 129,
    "regime": 63,
}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())  # 1219

CANONICAL_COLS = [
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


def load_unified():
    with open(UNIFIED, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        rows = list(reader)
    return cols, rows


def safe_float(s):
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return "INVALID"


def main():
    findings = {
        "expected_total": EXPECTED_TOTAL,
        "expected_per_family": EXPECTED_COUNTS,
    }

    cols, rows = load_unified()

    # Check 1: row count
    findings["actual_total_rows"] = len(rows)
    findings["row_count_pass"] = len(rows) == EXPECTED_TOTAL

    # Check 2: canonical columns
    findings["actual_columns"] = cols
    findings["columns_match"] = cols == CANONICAL_COLS
    findings["missing_columns"] = [c for c in CANONICAL_COLS if c not in cols]
    findings["extra_columns"] = [c for c in cols if c not in CANONICAL_COLS]

    # Check 3: per-family counts
    family_counts = {}
    for r in rows:
        fam = r.get("family", "")
        family_counts[fam] = family_counts.get(fam, 0) + 1
    findings["actual_family_counts"] = family_counts
    findings["per_family_pass"] = family_counts == EXPECTED_COUNTS

    # Check 4: stability_rho validity
    rho_invalid = []
    rho_nan = []
    rho_empty = 0
    rho_valid = 0
    for i, r in enumerate(rows):
        v = safe_float(r.get("stability_rho", ""))
        if v is None:
            rho_empty += 1
        elif v == "INVALID":
            rho_invalid.append((i + 2, r["family"], r["feature_name"], r["stability_rho"]))
        elif isinstance(v, float):
            if math.isnan(v):
                rho_nan.append((i + 2, r["family"], r["feature_name"]))
            else:
                rho_valid += 1
    findings["stability_rho_valid_floats"] = rho_valid
    findings["stability_rho_empty"] = rho_empty
    findings["stability_rho_nan_in_csv"] = rho_nan[:10]
    findings["stability_rho_invalid_strings"] = rho_invalid[:10]
    findings["stability_rho_pass"] = (
        len(rho_invalid) == 0 and len(rho_nan) == 0
    )

    # Check 5: feature_name uniqueness within family + globally
    name_globally = {}
    name_within_family = {}
    for r in rows:
        fam = r["family"]
        nm = r["feature_name"]
        name_globally.setdefault(nm, []).append(fam)
        name_within_family.setdefault((fam, nm), 0)
        name_within_family[(fam, nm)] += 1
    dup_within = [(fam, nm, n) for (fam, nm), n in name_within_family.items() if n > 1]
    cross_family = [
        (nm, fams) for nm, fams in name_globally.items() if len(set(fams)) > 1
    ]
    findings["dup_within_family"] = dup_within[:10]
    findings["cross_family_name_collisions"] = cross_family[:10]
    findings["dup_within_family_count"] = len(dup_within)
    findings["cross_family_collision_count"] = len(cross_family)

    # Check 6: spot-check 5 random rows against per-family CSV
    random.seed(42)
    indices = sorted(random.sample(range(len(rows)), 5))
    spot = []
    family_csvs = {}
    for fam in EXPECTED_COUNTS:
        path = CATALOG_DIR / f"{fam}.csv"
        with open(path, newline="", encoding="utf-8") as fh:
            family_csvs[fam] = list(csv.DictReader(fh))

    for i in indices:
        u = rows[i]
        fam = u["family"]
        nm = u["feature_name"]
        # find row in original family CSV
        orig_rows = family_csvs[fam]
        # original csv uses different name keys; our normalizer maps
        # them. Just look up by feature column heuristically.
        candidate_keys = ["feature_name", "feature"]
        match = None
        for r in orig_rows:
            for k in candidate_keys:
                if r.get(k, "") == nm:
                    match = r
                    break
            if match is not None:
                break
        spot.append({
            "row_idx_in_unified": i + 2,
            "family": fam,
            "feature_name": nm,
            "found_in_family_csv": match is not None,
            "unified_stability_rho": u.get("stability_rho", ""),
            "original_stability_rho": (
                (match or {}).get("stability_rho")
                or (match or {}).get("stability_spearman_rho")
                or (match or {}).get("spearman_rho")
                or (match or {}).get("stability_spearman_pre_2026_04")
                or ""
            ),
        })
    findings["spot_check_5_random"] = spot

    # Final pass-fail
    findings["overall_pass"] = (
        findings["row_count_pass"]
        and findings["columns_match"]
        and findings["per_family_pass"]
        and findings["stability_rho_pass"]
    )

    out_path = Path(__file__).parent / "q3_integrity_findings.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=2)
    print("WROTE", out_path)
    print(json.dumps(findings, indent=2)[:4000])


if __name__ == "__main__":
    main()

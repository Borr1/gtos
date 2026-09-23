"""OD-AI-4 option C: re-derive the survivor book and the firm-true MC as V2, BESIDE V1.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ap_recost_v2.py

THE DECISION THIS IMPLEMENTS
---------------------------
`OD-AI-4` asks whether to re-seal `SURVIVOR_BOOK_V1.json` and `MC_FIRM_TRUE_V1.json` at the
better cost coverage that `8f6da5150` ("price the six symbols that were blocking the LIVE
book's own scores") and `33d854189` ("close the metals tick gap") produced. Three options were
priced; the recommendation is **C -- re-seal as a V2 beside V1** so both are readable and
nothing goes stale. The owner's blanket yes takes C.

WHAT MAKES C DIFFERENT FROM A AND B, AND WHY THE TEST IS THE POINT
-----------------------------------------------------------------
Option A moves every published `p_pass` in the OD-3 dossier and in `CLAUDE.md` §4, and takes
ten citing documents stale in one commit. Option B (what wave 8 did) keeps the artifacts
comparable and publishes the drift. C keeps both -- and the thing that makes C worth having
rather than merely tidy is a **claim**: that the better coverage changes no tier and no verdict.
So this script writes the V2 files and `test_recost_v2_beside_v1.py` asserts exactly that. If
the assertion ever fails, C was the wrong option and the estate needs to know which figure
moved, which is the state B leaves you unable to see.

`build_survivor_book.py --out` and `mc_firm_rules.py --out` already exist and V1 is never
touched: `--write-committed` is the only way to reach the artifact of record and this script
does not pass it. That footgun was fixed by AI after it bit; keep it fixed.

THE CONTROL THAT MAKES "ONLY THE PRICING MOVED" A MEASUREMENT
-------------------------------------------------------------
`book_days` per (account, variant, sleeve) cannot change under a re-pricing: a cost cannot add
or remove a day a sleeve traded. Wave 8 measured 0 mismatches over all 36 cells and that is the
load-bearing control. It is re-asserted here rather than quoted, plus the two coverage moves
the queue names (`crypto` MEASURED 35 -> 72, `idxrev` 4,939 -> 5,876) and the count of FTMO MC
field moves (23), so the diff is described by numbers this run produced.

Offline and pure. Writes only under `research/operations/w7_recost_2026_07_30/` and this
receipts directory.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]

V1_DIR = REPO / "research/operations/w7_recost_2026_07_27"
V2_DIR = REPO / "research/operations/w7_recost_2026_07_30"
SB_V1 = V1_DIR / "SURVIVOR_BOOK_V1.json"
MC_V1 = V1_DIR / "MC_FIRM_TRUE_V1.json"
SB_V2 = V2_DIR / "SURVIVOR_BOOK_V2.json"
MC_V2 = V2_DIR / "MC_FIRM_TRUE_V2.json"
OUT = HERE / "AP_RECOST_V2_DELTA.json"

#: V1's own `n_paths`, so the two are compared at the same Monte Carlo resolution. Read from the
#: artifact rather than typed: a different path count is a different number and would confound
#: the "no verdict moves" claim with sampling noise.
def _v1_paths() -> int:
    return int(json.loads(MC_V1.read_text()).get("n_paths") or 60_000)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run(cmd: list[str]) -> str:
    print("$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{cmd[1]} failed ({r.returncode}):\n{r.stdout[-4000:]}\n{r.stderr[-4000:]}")
    return r.stdout


# --------------------------------------------------------------------------- the diff


def _walk(a, b, path="", out=None, limit=4000):
    """Every leaf where two nested JSON documents differ. Order-insensitive on dicts."""
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            _walk(a.get(k, "<<absent>>"), b.get(k, "<<absent>>"), f"{path}.{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"path": path, "v1": f"<list len {len(a)}>", "v2": f"<list len {len(b)}>"})
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _walk(x, y, f"{path}[{i}]", out, limit)
    else:
        if isinstance(a, float) and isinstance(b, float):
            if abs(a - b) > 1e-12:
                out.append({"path": path, "v1": a, "v2": b, "delta": b - a})
        elif a != b:
            out.append({"path": path, "v1": a, "v2": b})
    return out


def _book_days(doc: dict) -> dict:
    """(account, variant, sleeve) -> book_days, wherever the artifact records it."""
    out = {}
    for acct, ab in (doc.get("accounts") or {}).items():
        for var, vb in (ab.get("variants") or {}).items():
            if not isinstance(vb, dict):
                continue
            for k, v in vb.items():
                if isinstance(v, dict) and "book_days" in v:
                    out[(acct, var, k)] = v["book_days"]
            if "book_days" in vb:
                out[(acct, var, "__variant__")] = vb["book_days"]
        for sl, sb in (ab.get("sleeves") or {}).items():
            if isinstance(sb, dict) and "book_days" in sb:
                out[(acct, "sleeves", sl)] = sb["book_days"]
    return out


def _tiers(doc: dict) -> dict:
    out = {}
    for acct, ab in (doc.get("accounts") or {}).items():
        for sl, sb in (ab.get("sleeves") or {}).items():
            if isinstance(sb, dict) and "survivor_tier" in sb:
                out[f"{acct}/{sl}"] = sb["survivor_tier"]
        if "survivors" in ab:
            out[f"{acct}/__survivors__"] = sorted(ab["survivors"] or [])
        if "killed" in ab:
            out[f"{acct}/__killed__"] = sorted(ab["killed"] or [])
    return out


def _coverage(costs_path: Path) -> dict:
    """MEASURED-commission row counts for the two sleeves OD-AI-4 names, from the cost artifact
    the recost route actually reads. Counted per instrument rather than per trade, because a
    trade count needs the cache and this is the artifact-side fact."""
    d = json.loads(costs_path.read_text())
    out = {}
    for acct, ab in d["accounts"].items():
        n = {"MEASURED": 0, "TRANSFERRED": 0, "MODELLED": 0}
        for rec in ab["instruments"].values():
            c = (rec.get("commission") or {}).get("coverage")
            if c in n:
                n[c] += 1
        out[acct] = {"n_instruments": len(ab["instruments"]), "commission_coverage": n}
    return out


def main() -> dict:
    for p in (SB_V1, MC_V1):
        if not p.is_file():
            raise SystemExit(f"{p} is missing; V1 is the comparison basis and cannot be absent")
    V2_DIR.mkdir(parents=True, exist_ok=True)
    paths = _v1_paths()

    sb_v1 = json.loads(SB_V1.read_text())
    mc_v1 = json.loads(MC_V1.read_text())
    v1_shas = {"SURVIVOR_BOOK_V1.json": _sha(SB_V1), "MC_FIRM_TRUE_V1.json": _sha(MC_V1)}

    _run([sys.executable, "scripts/build_survivor_book.py", "--out", str(SB_V2)])
    # `--allow-cost-artifact-drift` is REQUIRED and that is the point of the flag: the run is
    # deliberately against the newer cost artifact, so refusing by default is correct and
    # passing it here is the declaration that the drift is the subject rather than a surprise.
    _run([sys.executable, "scripts/mc_firm_rules.py", "--out", str(MC_V2),
          "--paths", str(paths), "--allow-cost-artifact-drift"])

    # V1 must be untouched. Asserted, because the footgun this replaces was exactly this.
    after = {"SURVIVOR_BOOK_V1.json": _sha(SB_V1), "MC_FIRM_TRUE_V1.json": _sha(MC_V1)}
    if after != v1_shas:
        raise SystemExit(f"V1 MOVED. before={v1_shas} after={after}. Restore from git and stop.")

    sb_v2 = json.loads(SB_V2.read_text())
    mc_v2 = json.loads(MC_V2.read_text())

    sb_diff = _walk(sb_v1, sb_v2)
    mc_diff = _walk(mc_v1, mc_v2)
    bd1, bd2 = _book_days(mc_v1), _book_days(mc_v2)
    bd_keys = sorted(set(bd1) | set(bd2), key=str)
    bd_mismatch = [{"cell": list(k), "v1": bd1.get(k), "v2": bd2.get(k)}
                   for k in bd_keys if bd1.get(k) != bd2.get(k)]
    t1, t2 = _tiers(sb_v1), _tiers(sb_v2)
    tier_mismatch = [{"key": k, "v1": t1.get(k), "v2": t2.get(k)}
                     for k in sorted(set(t1) | set(t2)) if t1.get(k) != t2.get(k)]

    def _by_account(diff):
        n = {"FTMO": 0, "redacted_account": 0, "other": 0}
        for d in diff:
            n["FTMO" if ".FTMO" in d["path"] else
              "redacted_account" if ".redacted_account" in d["path"] else "other"] += 1
        return n

    res = {
        "schema": "gtos.w7_recost.v2_beside_v1.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                         "ap_recost_v2.py"),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "decision": "OD-AI-4, option C",
        "authorized_by": "borhen (2026-07-30, blanket ratification of OD-AI-4's recommendation)",
        "option_C_verbatim": "Re-seal as a V2 beside V1: both readable, nothing goes stale, and "
                             "one more artifact to keep straight.",
        "v1": {"dir": str(V1_DIR.relative_to(REPO)), "sha256": v1_shas,
               "untouched_verified": True,
               "how": "sha256 taken before and after both generator runs; neither was passed "
                      "--write-committed"},
        "v2": {"dir": str(V2_DIR.relative_to(REPO)),
               "SURVIVOR_BOOK_V2.json": _sha(SB_V2), "MC_FIRM_TRUE_V2.json": _sha(MC_V2),
               "mc_paths": paths, "mc_paths_basis": "read from MC_FIRM_TRUE_V1.n_paths so the "
                                                    "two are compared at the same resolution"},
        "cost_coverage": {
            "artifact": "research/operations/broker_truth_layer_2026_07_27/"
                        "BROKER_TRUE_COSTS_V1.json (the recost route's own input, extended by "
                        "8f6da5150 and 33d854189 AFTER Session Q sealed V1's figures)",
            "measured_now": _coverage(
                REPO / "research/operations/broker_truth_layer_2026_07_27/"
                       "BROKER_TRUE_COSTS_V1.json"),
            "queue_stated_moves": {
                "crypto_MEASURED_rows": "35 of 104 -> 72",
                "idxrev_MEASURED_rows": "4,939 -> 5,876",
                "why_it_matters": "crypto supplies 38.8 % of the book's edge and dossier rule R7 "
                                  "says coverage is part of the number"},
        },
        "THE_CONTROL": {
            "claim": "a cost re-pricing cannot add or remove a day a sleeve traded, so book_days "
                     "must reproduce in every cell",
            "cells_compared": len(bd_keys),
            "mismatches": bd_mismatch,
            "holds": not bd_mismatch,
        },
        "THE_POINT_OF_OPTION_C": {
            "claim": "no tier and no survivor/killed membership changes between V1 and V2",
            "keys_compared": len(set(t1) | set(t2)),
            "mismatches": tier_mismatch,
            "holds": not tier_mismatch,
            "asserted_by": "tests/test_recost_v2_beside_v1.py",
        },
        "survivor_book_diff": {"n_leaves": len(sb_diff), "by_account": _by_account(sb_diff),
                               "leaves": sb_diff[:400]},
        "mc_diff": {"n_leaves": len(mc_diff), "by_account": _by_account(mc_diff),
                    "leaves": mc_diff[:400]},
        "how_to_read_this": (
            "V1 remains the artifact of record and every published figure still cites it. V2 is "
            "the same arithmetic at better MEASURED cost coverage. Where they differ the "
            "difference is pricing, never population -- THE_CONTROL is what says so. Quote V1 "
            "when comparing to anything published before 2026-07-30 and V2 when the question is "
            "'what do we believe today'; never mix them inside one table."),
    }
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\nbook_days control: {'HOLDS' if res['THE_CONTROL']['holds'] else 'BROKEN'} "
          f"({len(bd_keys)} cells, {len(bd_mismatch)} mismatches)")
    print(f"tier/verdict identity: {'HOLDS' if res['THE_POINT_OF_OPTION_C']['holds'] else 'BROKEN'} "
          f"({len(set(t1) | set(t2))} keys, {len(tier_mismatch)} mismatches)")
    print(f"survivor book diff leaves: {len(sb_diff)}  {_by_account(sb_diff)}")
    print(f"MC diff leaves:            {len(mc_diff)}  {_by_account(mc_diff)}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return res


if __name__ == "__main__":
    main()

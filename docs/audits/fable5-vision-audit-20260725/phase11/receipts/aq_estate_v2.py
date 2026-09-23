"""Session AQ — the estate artifact of record, on the repaired clock (AQ-3, B1416-B1421).

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_estate_v2.py

WHY THIS FILE EXISTS
--------------------
`substrate._session_hour` read the raw UTC hour and compared it against BROKER-hour
session constants. `sub_mid_dn_revert`'s cell carries `session: "ny"` as one of its seven
firing conditions, so the defect changed **which trades exist**, not their pricing:
50.04 % of archive H4 bars are mis-bucketed, and `session=ny` moves from server-hour
{20, 00} to {16, 20}. Session AM repaired the code and measured the A/B (B1200-B1241).

What AM did **not** do — and says so — is regenerate the artifact everything downstream
reads. `AA_ESTATE_TRADES.json.gz` still holds the defect-clock 503, and so, through it, do
`AA_ESTATE_WALK.json`, `EXIT_FRONTIER_V1.json` and `SURVIVOR_BOOK_V1.json`. Every session
since has had to remember to substitute AM's rows by hand; AN did, and said so; anything
that forgets is judging the defect.

This file closes that. It publishes `AQ_ESTATE_TRADES_V2.json.gz` — AA's artifact with one
sleeve's population replaced — so the substitution is a file rather than a habit.

WHY IT REUSES AM'S ROWS INSTEAD OF RE-RUNNING GENERATION, AND THE CONTROL THAT MAKES THAT LEGAL
-------------------------------------------------------------------------------------------------
AM's driver replicated AA's grid exactly and ran BOTH clocks through it. Its authored-clock
arm is therefore a reproduction of AA's own labelling, and if that reproduction is exact
then its repaired arm is a correct regeneration of the same generator on the fixed clock —
re-running AA's ~30-machine-minute H4 generation would produce the same rows.

That "if" is not taken on trust here. `control_am_reproduces_aa` re-derives it from the two
artifacts on disk: same trade keys, same count, same `r_gross` to the bit, same sum. If it
fails, this file refuses to write.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AM_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AM_SUBMID_TRADES.json.gz"
AM_RECLOCK = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/SUBMID_RECLOCK_V1.json"
OUT = HERE / "AQ_ESTATE_TRADES_V2.json.gz"
OUT_RECEIPT = HERE / "AQ_ESTATE_V2_RECEIPT.json"

SUBMID = "sub_mid_dn_revert"


def _key(r: dict) -> tuple:
    return (r.get("symbol_canonical") or r.get("symbol"), r["decision_bar_iso"],
            int(r["direction"]))


def control_am_reproduces_aa(aa_rows: list[dict], am_authored: list[dict]) -> dict:
    """AM's authored-clock arm must BE AA's labelling. The whole reuse rests on this."""
    a = {_key(r): r for r in aa_rows}
    b = {_key(r): r for r in am_authored}
    shared = sorted(set(a) & set(b))
    r_mismatch = [k for k in shared if a[k]["r_gross"] != b[k]["r_gross"]]
    out = {
        "what": ("AM's `authored_utc` arm re-labelled through AA's own grid must reproduce "
                 "AA's `sub_mid_dn_revert` rows exactly; if it does, AM's `server_repaired` "
                 "arm is a correct regeneration of the same generator on the fixed clock"),
        "n_aa": len(a), "n_am_authored": len(b), "n_shared": len(shared),
        "only_in_aa": sorted(str(k) for k in (set(a) - set(b)))[:20],
        "only_in_am": sorted(str(k) for k in (set(b) - set(a)))[:20],
        "n_r_gross_mismatched": len(r_mismatch),
        "sum_r_aa": round(sum(r["r_gross"] for r in aa_rows), 10),
        "sum_r_am_authored": round(sum(r["r_gross"] for r in am_authored), 10),
    }
    out["pass"] = (out["n_aa"] == out["n_am_authored"] == out["n_shared"]
                   and out["n_r_gross_mismatched"] == 0
                   and out["sum_r_aa"] == out["sum_r_am_authored"])
    return out


def main() -> None:
    t0 = time.time()
    HERE.mkdir(parents=True, exist_ok=True)
    aa = json.load(gzip.open(AA_IN, "rt"))
    am = json.load(gzip.open(AM_IN, "rt"))
    reclock = json.load(open(AM_RECLOCK))

    aa_rows = aa["trades"][SUBMID]
    rep = am["trades"]["server_repaired"]
    ctl = control_am_reproduces_aa(aa_rows, am["trades"]["authored_utc"])
    if not ctl["pass"]:
        raise SystemExit(f"CONTROL FAILED — AM does not reproduce AA, refusing to write: {ctl}")

    # --- what actually moves ----------------------------------------------------------
    a = {_key(r) for r in aa_rows}
    b = {_key(r) for r in rep}
    moved = {
        "n_before": len(aa_rows), "n_after": len(rep),
        "n_shared": len(a & b), "n_dropped_by_the_repair": len(a - b),
        "n_added_by_the_repair": len(b - a),
        "jaccard": round(len(a & b) / len(a | b), 5),
        "sum_r_before": round(sum(r["r_gross"] for r in aa_rows), 10),
        "sum_r_after": round(sum(r["r_gross"] for r in rep), 10),
        "mean_r_before": round(sum(r["r_gross"] for r in aa_rows) / len(aa_rows), 6),
        "mean_r_after": round(sum(r["r_gross"] for r in rep) / len(rep), 6),
        "decision_server_hours_before": _hist(aa_rows, "decision_bar_server_hour"),
        "decision_server_hours_after": _hist(rep, "decision_bar_server_hour"),
    }

    doc = dict(aa)
    doc["trades"] = {s: (rep if s == SUBMID else rows) for s, rows in aa["trades"].items()}
    doc["n_trades_by_sleeve"] = {s: len(r) for s, r in doc["trades"].items()}
    doc["schema"] = "gtos.walkforward.estate_trades.v3"
    doc["generated_by"] = ("docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                           "aq_estate_v2.py")
    doc["supersedes"] = {
        "artifact": str(AA_IN.relative_to(REPO)),
        "sleeve_replaced": SUBMID,
        "why": ("AA's population for this sleeve was produced by a clock defect: "
                "`substrate._session_hour` returned the raw UTC hour and "
                "`substrate_engine._bucket_session` cut it against BROKER-hour constants. "
                "`session=ny` is one of the sleeve's seven firing conditions, so the defect "
                "decided which trades exist. Repaired at HEAD via `_server_clock.server_hour`; "
                "measured by Session AM (B1200-B1241)."),
        "repaired_rows_from": str(AM_IN.relative_to(REPO)) + " -> trades.server_repaired",
        "clock_defect_reach": {
            "bars_mis_bucketed_frac": 0.5004,
            "session_ny_server_hours_before": [20, 0],
            "session_ny_server_hours_after": [16, 20],
            "source": str(AM_RECLOCK.relative_to(REPO)),
        },
        "every_other_sleeve": "byte-identical to AA; only this key's list is replaced",
        "control": ctl,
        "what_moved": moved,
    }
    doc["still_stale_downstream"] = {
        "what": ("these artifacts were built from AA's defect-clock rows for this sleeve and "
                 "have NOT been rebuilt. Read this note before quoting any "
                 "`sub_mid_dn_revert` number out of them."),
        "artifacts": [
            "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_WALK.json",
            "docs/audits/fable5-vision-audit-20260725/phase7/receipts/EXIT_FRONTIER_V1.json",
            "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json",
            "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json",
        ],
        "cost_to_rebuild": ("AA_ESTATE_WALK ~2 min from this artifact; EXIT_FRONTIER ~27 min; "
                            "the carry tiers and survivor book are arithmetic on top"),
        "who_is_already_correct": [
            "docs/audits/fable5-vision-audit-20260725/phase10/receipts/POPULATION_RULE_V1.json",
            "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_CONTRACT_TRUTH_V1.json",
        ],
    }

    payload = json.dumps(doc, sort_keys=True, default=str).encode()
    with gzip.open(OUT, "wb") as fh:
        fh.write(payload)
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()

    receipt = {
        "schema": "gtos.wave11.aq.estate_v2_receipt.v1",
        "generated_by": doc["generated_by"], "session": "AQ", "blocks": "B1416-B1421",
        "artifact": str(OUT.relative_to(REPO)), "sha256": sha,
        "bytes": OUT.stat().st_size,
        "n_sleeves": len(doc["trades"]),
        "n_trades_total": sum(len(r) for r in doc["trades"].values()),
        "n_trades_total_before": sum(len(r) for r in aa["trades"].values()),
        "control_am_reproduces_aa": ctl,
        "what_moved": moved,
        "am_published_clock_ab": reclock.get("clock_ab", {}).get("summary")
        or {k: v for k, v in (reclock.get("clock_ab") or {}).items()
            if not isinstance(v, (list, dict))},
        "seconds": round(time.time() - t0, 1),
    }
    OUT_RECEIPT.write_text(json.dumps(receipt, indent=1, sort_keys=True, default=str))
    print(f"control: AM reproduces AA -> {ctl['pass']} "
          f"(n {ctl['n_aa']}/{ctl['n_am_authored']}, r mismatches {ctl['n_r_gross_mismatched']})")
    print(f"{SUBMID}: {moved['n_before']} -> {moved['n_after']} "
          f"(shared {moved['n_shared']}, jaccard {moved['jaccard']}), "
          f"mean R {moved['mean_r_before']} -> {moved['mean_r_after']}")
    print(f"wrote {OUT.relative_to(REPO)} ({receipt['bytes']} B, sha {sha[:12]})")


def _hist(rows: list[dict], field: str) -> dict:
    h: dict = {}
    for r in rows:
        v = r.get(field)
        if v is not None:
            h[str(v)] = h.get(str(v), 0) + 1
    return dict(sorted(h.items(), key=lambda kv: int(kv[0])))


if __name__ == "__main__":
    main()

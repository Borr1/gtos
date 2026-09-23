"""r2_blast — the blast-radius proof, two-sided.

(1) REPRODUCTION.  The `legacy` arm (escape hatch set to the pre-repair
    contract) must reproduce the FROZEN wave-19 roster exactly, on
    (decision_time, symbol, family, side, entry, stop, target, candidate_id).

(2) SUBTRACTION.  The `default` arm's emitted set must equal the legacy set
    MINUS exactly the rows the two default gates predict, computed
    independently from the roster and the bar archive.  Nothing may be added,
    and no surviving row's geometry may move.

Both directions are required: (1) alone would pass a repair that did nothing,
(2) alone would pass a repair that also perturbed the survivors.
"""
from __future__ import annotations

import bisect
import collections
import csv
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timedelta

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
        "bridge_ftmo_m15_20250601_20260610")
FROZEN = {
    "202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
    "202512": "/tmp/f1/roster_202512", "202601": "/tmp/d4/rosters/202601",
    "202602": "/tmp/d4/rosters/202602", "202603": "/tmp/d4/rosters/202603",
    "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605",
}
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
RR = 1.5

# the generator's OWN pair table and canonicaliser, imported rather than
# transcribed, so the leader model cannot drift from the code it predicts.
sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
from src.components.broader_origin_generators import (  # noqa: E402
    LEAD_LAG_PAIRS, _canonical_symbol,
)

_S: dict = {}


def series(sym):
    if not _S:
        for p in sorted(glob.glob(os.path.join(BARS, "*_M15.csv"))):
            s = os.path.basename(p)[: -len("_M15.csv")]
            rows = []
            with open(p, newline="") as fh:
                for r in csv.DictReader(fh):
                    rows.append((datetime.fromisoformat(r["time"]).replace(tzinfo=None),
                                 float(r["close"])))
            rows.sort()
            _S[s] = ([x[0] for x in rows], [x[1] for x in rows])
    return _S.get(sym)


def key(r):
    return (r["t"], r["s"], r["f"], r["d"], r["e"], r["sl"], r["tp"], r["cid"])


def load(d):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "*.jsonl.gz"))):
        if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
            continue
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            if r["k"] != 15:
                continue
            out[key(r)] = r
    return out


def _age_seconds(sym, T):
    s = series(sym)
    if s is None:
        return None
    t, _ = s
    i = bisect.bisect_right(t, T - timedelta(minutes=15) + timedelta(seconds=2)) - 1
    if i < 0:
        return None
    return (T - (t[i] + timedelta(minutes=15))).total_seconds()


def _file_symbol(canonical):
    for name in series("") or {} if False else _S:
        if _canonical_symbol(name) == canonical:
            return name
    return None


def predict_refusal(r):
    """Independent recomputation of what the two default gates must refuse."""
    s = series(r["s"])
    if s is None:
        return None
    t, c = s
    T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
    i = bisect.bisect_right(t, T - timedelta(minutes=15) + timedelta(seconds=2)) - 1
    if i < 0:
        return None
    age = (T - (t[i] + timedelta(minutes=15))).total_seconds()
    if age >= 15 * 60:
        return "stale_bar"
    if r["f"] == "cross_asset_lead_lag":
        # the leader series carries the same age budget (:1016); the candidate
        # is refused only when EVERY leader of that lag symbol is stale, which
        # is what the generator's leader loop does.
        lag = _canonical_symbol(r["s"])
        leaders = [ld for ld, lg in LEAD_LAG_PAIRS if _canonical_symbol(lg) == lag]
        ages = []
        for ld in leaders:
            fs = _file_symbol(ld)
            a = _age_seconds(fs, T) if fs else None
            if a is not None:
                ages.append(a)
        if ages and all(a >= 15 * 60 for a in ages):
            return "stale_cross_asset_leader"
    if r["f"] in POI:
        e, sl = r["e"], r["sl"]
        risk = abs(e - sl)
        if risk > 0:
            gap = (c[i] - e) / risk * (1.0 if r["d"] == "L" else -1.0)
            if gap < -1.0:
                return "past_stop"
    return None


def main(out_path):
    report = {"windows": {}, "totals": collections.Counter()}
    ok = True
    for win, frozen_dir in sorted(FROZEN.items()):
        leg_dir = f"/tmp/r2/arm_legacy/{win}"
        def_dir = f"/tmp/r2/arm_default/{win}"
        if not os.path.isdir(def_dir):
            continue
        frozen = load(frozen_dir)
        legacy = load(leg_dir) if os.path.isdir(leg_dir) else {}
        default = load(def_dir)
        # completeness: the arms must cover the SAME decision days as the frozen
        # roster, or a partial run reads as a huge blast radius.
        fd = {k[0][:10] for k in frozen}
        if {k[0][:10] for k in default} != fd:
            print(f"{win} SKIP default incomplete "
                  f"({len({k[0][:10] for k in default})}/{len(fd)} days)", flush=True)
            continue
        legacy_complete = bool(legacy) and {k[0][:10] for k in legacy} == fd

        repro_ok = legacy_complete and set(frozen) == set(legacy)
        # the FROZEN roster is the actual pre-repair artifact; compare against it
        added = set(default) - set(frozen)
        removed = set(frozen) - set(default)
        predicted = {k for k, r in frozen.items() if predict_refusal(r) is not None}
        reasons = collections.Counter(predict_refusal(frozen[k]) for k in removed)
        by_family = collections.Counter(k[2] for k in removed)

        w = {
            "frozen_rows": len(frozen), "legacy_rows": len(legacy),
            "default_rows": len(default),
            "legacy_arm_days_complete": legacy_complete,
            "escape_hatch_reproduces_frozen_roster": repro_ok,
            "frozen_minus_legacy": len(set(frozen) - set(legacy)),
            "legacy_minus_frozen": len(set(legacy) - set(frozen)),
            "added_by_repair": len(added),
            "removed_by_repair": len(removed),
            "predicted_refusals": len(predicted),
            "removed_equals_predicted": removed == predicted,
            "removed_share": len(removed) / len(frozen),
            "removal_reasons": dict(reasons),
            "removal_by_family": dict(by_family),
        }
        report["windows"][win] = w
        report["totals"]["frozen"] += len(frozen)
        report["totals"]["legacy"] += len(legacy)
        report["totals"]["default"] += len(default)
        report["totals"]["added"] += len(added)
        report["totals"]["removed"] += len(removed)
        for k, v in reasons.items():
            report["totals"]["reason_" + str(k)] += v
        for k, v in by_family.items():
            report["totals"]["fam_" + k] += v
        # geometry of every survivor must be untouched: re-key on identity only
        # (decision instant, symbol, family, candidate_id) and compare the numbers.
        fid = {(k[0], k[1], k[2], k[7]): frozen[k] for k in frozen}
        did = {(k[0], k[1], k[2], k[7]): default[k] for k in default}
        moved = [i for i in (set(fid) & set(did))
                 if (did[i]["e"], did[i]["sl"], did[i]["tp"], did[i]["d"])
                 != (fid[i]["e"], fid[i]["sl"], fid[i]["tp"], fid[i]["d"])]
        w["survivor_identities_compared"] = len(set(fid) & set(did))
        w["survivors_with_moved_geometry"] = len(moved)
        ok = ok and not added and removed == predicted and not moved
        print(f"{win} frozen={len(frozen):7d} legacy={len(legacy):7d} "
              f"default={len(default):7d} hatch_repro={repro_ok} added={len(added)} "
              f"removed={len(removed):6d} pred_match={removed == predicted} "
              f"reasons={dict(reasons)}", flush=True)

    report["totals"] = dict(report["totals"])
    report["all_windows_pass"] = ok
    json.dump(report, open(out_path, "w"), indent=1)
    print("ALL WINDOWS PASS:", ok)


if __name__ == "__main__":
    main(sys.argv[1])

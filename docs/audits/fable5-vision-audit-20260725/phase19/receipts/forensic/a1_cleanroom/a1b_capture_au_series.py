#!/usr/bin/env python3
"""A1-OPEN (a1b), step 1: capture the daily series behind the estate's STANDING ADMISSION.

The clean-room (A1_CLEANROOM_NULL_DERIVATION.md) proved the gate's significance predicate —
``stats.combined_null_p`` = max(circular-block bootstrap, fixed-phase block sign-flip) — is not
rotation-invariant, mixes signal into its own null variance, and is anti-conservative at short
block lengths under the dependence class it assumes.  The re-issue job (this script's caller)
must therefore recompute every family member whose PUBLISHED verdict consumed that predicate.

Across the wave18/19 named receipts exactly ONE member carries a computed null (the breaker, CS).
The only OTHER standing publications through the same code path that can BIND are the estate's one
live ADMIT and the one armed-sleeve frontier REJECT, both published by Session AU
(``AU_EXIT_WIRING_V1.json``, phase12): ``mx_btcusd_d1_donchian_20_breakout @ target_5R`` (ADMIT at
flat/low/mid — the standing admission, armed on FTMO) and ``sub_xvol_pullback @ target_4R``
(REJECT everywhere, armed sleeve).  This script reconstructs the exact daily series those sixteen
arms tested, the same way the clean-room did for CS: run the committed receipt script IN PROCESS
with capture hooks, and accept the capture ONLY if the receipt reproduces float-exactly.

Sparse-worktree note: this worktree is a sparse checkout and two of AU's inputs are skip-worktree
('S' in ``git ls-files -v``).  They are materialized from the git object store byte-exactly before
the run (skip-worktree paths are invisible to ``git status``, so this leaves no dirt), and their
sha256s are recorded in the output.

Writes A1B_AU_CAPTURED_SERIES.json next to this script.  Ledger: stage_gate(sub, ledger=None) —
no TrialLedger/IterationLedger append happens.  Read-only otherwise.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
AU_TOOL = WT / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_exit_contract_wiring.py"
RECEIPT = WT / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AU_EXIT_WIRING_V1.json"
OUT = HERE / "A1B_AU_CAPTURED_SERIES.json"

#: skip-worktree inputs the committed AU tool reads by absolute-in-repo path.
MATERIALIZE = (
    "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json",
    "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json",
)


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def materialize_skip_worktree() -> dict:
    out = {}
    for rel in MATERIALIZE:
        dst = WT / rel
        blob = subprocess.run(
            ["git", "-C", str(WT), "cat-file", "blob", f"HEAD:{rel}"],
            check=True, capture_output=True).stdout
        if blob.startswith(b"version https://git-lfs"):
            blob = subprocess.run(["git", "-C", str(WT), "lfs", "smudge"],
                                  input=blob, check=True, capture_output=True).stdout
        if dst.is_file() and dst.read_bytes() == blob:
            out[rel] = {"sha256": _sha256_bytes(blob), "action": "already_present_identical"}
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(blob)
        out[rel] = {"sha256": _sha256_bytes(blob), "action": "materialized_from_object_store"}
    return out


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    t0 = time.time()
    materialized = materialize_skip_worktree()

    au = _load_module(AU_TOOL, "gtos_a1b_au_exit_contract_wiring")

    from src.research_infra.walkforward import gate as gate_mod
    from src.research_infra.walkforward import stats as stats_mod

    buckets: list[dict] = []

    orig_pooled = gate_mod._pooled_oos

    def pooled_hook(slices, spec):
        xs, ws = orig_pooled(slices, spec)
        slices = list(slices)
        buckets[-1]["pooled_calls"].append({
            "folds": [
                {
                    "fold_id": s.fold.fold_id,
                    "oos_start": s.fold.oos_start.isoformat(),
                    "oos_end": s.fold.oos_end.isoformat(),
                    "status": s.status,
                    "n_test_trades": s.n_test_trades,
                    "n_test_days": len(s.test_days),
                }
                for s in slices
            ],
            "xs": [float(v) for v in xs],
            "ws": [float(v) for v in ws],
        })
        return xs, ws

    orig_null = stats_mod.combined_null_p

    def null_hook(x, *, block, mode="both_conservative", n_boot=10000,
                  n_perm=10000, seed=20260729):
        res = orig_null(x, block=block, mode=mode, n_boot=n_boot, n_perm=n_perm, seed=seed)
        buckets[-1]["null_calls"].append({
            "series_floats": [float(v) for v in x],
            "n": len(list(x)),
            "block": int(block), "mode": mode,
            "n_boot": int(n_boot), "n_perm": int(n_perm), "seed": int(seed),
            "p_value": res.get("p_value"),
            "p_basis": res.get("p_basis"),
        })
        return res

    real_run_gate = au.run_gate

    def run_gate_bracket(recs, spec, **kw):
        buckets.append({"pooled_calls": [], "null_calls": [], "sleeve_pvalues": {}})
        res = real_run_gate(recs, spec, **kw)
        # co-judged p-set of this run, for BH-substitution later
        for name, sv in res.verdicts.items():
            buckets[-1]["sleeve_pvalues"][name] = {
                "p_raw": sv.p_raw,
                "verdict": sv.verdict.value,
                "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                "q_value": sv.q_value,
            }
        return res

    gate_mod._pooled_oos = pooled_hook
    stats_mod.combined_null_p = null_hook
    au.run_gate = run_gate_bracket

    sub = au.build_substrate()
    rows = au.stage_gate(sub, None)          # ledger=None: no ledger append

    receipt = json.loads(RECEIPT.read_text())

    # ---- associate arm rows <-> buckets (deterministic order), then validate ------------
    order = []
    for sleeve in au.CELLS:
        order.extend((sleeve, i) for i in range(8))
    assert len(buckets) == len(order) == 16, (len(buckets), len(order))

    arms_out = []
    checks_all = []
    for (sleeve, idx), bucket in zip(order, buckets):
        got = rows[sleeve]["arms"][idx]
        want = receipt["gate_rows"][sleeve]["arms"][idx]
        fields = ("arm", "band", "p_raw", "q_value", "verdict", "n_trades",
                  "pooled_oos_mean_r", "fold_means", "spec_sha256",
                  "declared_family_size", "p_floor", "n_blocks")
        checks = {f: got.get(f) == want.get(f) for f in fields}
        checks_all.append(all(checks.values()))

        # the target sleeve's null call: series mean == pooled_oos_mean_r (float-exact)
        import numpy as _np
        target_null = None
        for c in bucket["null_calls"]:
            vals = c["series_floats"]
            if vals and float(_np.asarray(vals).mean()) == want["pooled_oos_mean_r"]:
                target_null = c
                break
        if target_null is None:   # fall back to exact p match (unique in practice)
            cands = [c for c in bucket["null_calls"] if c["p_value"] == want["p_raw"]]
            target_null = cands[0] if len(cands) == 1 else None
        assert target_null is not None, (sleeve, idx, "no null call matched")

        # the target sleeve's pooled call: weighted mean matches the same statistic
        target_pooled = None
        for c in bucket["pooled_calls"]:
            xs, ws = c["xs"], c["ws"]
            if xs and abs(sum(x * w for x, w in zip(xs, ws)) / sum(ws)
                          - want["pooled_oos_mean_r"]) < 1e-9:
                target_pooled = c
                break
        assert target_pooled is not None, (sleeve, idx, "no pooled call matched")

        seg_lens = [f["n_test_days"] for f in target_pooled["folds"]
                    if f["status"] == "evaluable"]
        assert sum(seg_lens) == target_null["n"], (sleeve, idx, seg_lens, target_null["n"])

        arms_out.append({
            "sleeve": sleeve,
            "arm_index": idx,
            "arm": want["arm"],
            "band": want["band"],
            "published": {k: want.get(k) for k in
                          ("p_raw", "q_value", "verdict", "n_trades",
                           "pooled_oos_mean_r", "fold_means", "declared_family_size",
                           "declared_family_id", "spec_sha256", "p_floor", "n_blocks")},
            "reproduction_checks": checks,
            "reproduced_p_raw": got.get("p_raw"),
            "null_call": {
                "series": [repr(v) for v in target_null["series_floats"]],
                "n": target_null["n"], "block": target_null["block"],
                "mode": target_null["mode"], "n_boot": target_null["n_boot"],
                "n_perm": target_null["n_perm"], "seed": target_null["seed"],
                "p_value": target_null["p_value"], "p_basis": target_null["p_basis"],
            },
            "fold_segment_day_counts": seg_lens,
            "fold_calendar": [
                {k: f[k] for k in ("fold_id", "oos_start", "oos_end", "status",
                                    "n_test_days")}
                for f in target_pooled["folds"]
            ],
            "co_judged_pvalues": bucket["sleeve_pvalues"],
        })
        print(f"{sleeve:36s} arm[{idx}] {want['arm']:10s} {want['band']:20s} "
              f"repro={'PASS' if all(checks.values()) else 'FAIL: ' + str([k for k, v in checks.items() if not v])}",
              flush=True)

    out = {
        "schema": "gtos-a1b-au-captured-series-v1",
        "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "elapsed_seconds": round(time.time() - t0, 1),
        "inputs": {
            "au_tool": str(AU_TOOL),
            "au_tool_sha256": _sha256_bytes(AU_TOOL.read_bytes()),
            "receipt": str(RECEIPT),
            "receipt_sha256": _sha256_bytes(RECEIPT.read_bytes()),
            "materialized_skip_worktree": materialized,
            "numpy": __import__("numpy").__version__,
            "python": sys.version,
        },
        "reproduction_all_pass": all(checks_all),
        "n_arms": len(arms_out),
        "arms": arms_out,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({"all_pass": out["reproduction_all_pass"],
                      "n_arms": len(arms_out),
                      "elapsed_s": out["elapsed_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

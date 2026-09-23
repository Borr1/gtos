#!/usr/bin/env python3
"""A1 clean-room, step 1: reconstruct the gate's fold-concatenated OOS daily series.

Runs the CS-era gate pipeline IN PROCESS (wave19-breaker-folds worktree, the exact
code + artifacts the ratified gate receipt was produced from) with two capture
hooks, so the daily series the significance predicate actually tested is extracted
at the exact call site rather than re-derived by hand:

  * ``gate._pooled_oos``      -> per-fold OOS day calendar + day values + weights
  * ``stats.combined_null_p`` -> the weighted ("scaled") series, block, seed, mode

Validation: the returned gate dict must reproduce the committed receipt
(CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json) on p_raw, q, fold n_test_trades, fold
means, null telemetry (null_mean/null_std/p), pooling leverage and lag-1 autocorrs.
Exact float equality is the target: same code, same inputs, same seed, same numpy.

Writes A1_CAPTURED_SERIES.json next to this script. Read-only w.r.t. everything
else: run_gate is pure (verified by inspection) and no ledger-writing code path is
invoked.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CS_REPO = Path("/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801")
CS_TOOL = (
    CS_REPO
    / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/cs_breaker_folds.py"
)
RECEIPT = (
    CS_REPO
    / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json"
)
JAN_POOL_GIVEN = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-path-pools-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/pools/"
    "CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz"
)
OUT = HERE / "A1_CAPTURED_SERIES.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    # cs_breaker_folds inserts CS_REPO into sys.path itself on import.
    cs = _load_module(CS_TOOL, "gtos_a1_cs_breaker_folds")

    # The task hands the January fold from the wave18-path-pools worktree; the CS
    # tool reads its own committed copy. Prove they are the same bytes before use.
    jan_local = cs.CQ_GATE.REPAIR_TRADES
    given_sha = _sha256(JAN_POOL_GIVEN)
    local_sha = _sha256(Path(jan_local))
    assert given_sha == local_sha, (given_sha, local_sha)

    from src.research_infra.walkforward import gate as gate_mod
    from src.research_infra.walkforward import stats as stats_mod
    from src.research_infra.walkforward import era_population
    from src.research_infra.walkforward.candidate_family import (
        ALL_DECLARED,
        load_candidate_family,
        with_declared_family,
    )
    from src.research_infra.walkforward.options import OPTIONS
    from src.costs import load_broker_true_costs

    captured: dict = {"pooled_oos_calls": [], "combined_null_calls": []}

    orig_pooled = gate_mod._pooled_oos

    def pooled_hook(slices, spec):
        xs, ws = orig_pooled(slices, spec)
        captured["pooled_oos_calls"].append(
            {
                "n_slices": len(list(slices)),
                "folds": [
                    {
                        "fold_id": s.fold.fold_id,
                        "oos_start": s.fold.oos_start.isoformat(),
                        "oos_end": s.fold.oos_end.isoformat(),
                        "is_initial_train": s.fold.is_initial_train,
                        "status": s.status,
                        "n_test_trades": s.n_test_trades,
                        "n_train_trades": s.n_train_trades,
                        "test_days": [d.isoformat() for d in s.test_days],
                        "test_r": [repr(v) for v in s.test_r],
                    }
                    for s in slices
                ],
                "xs": [repr(v) for v in xs],
                "ws": [repr(v) for v in ws],
            }
        )
        return xs, ws

    orig_null = stats_mod.combined_null_p

    def null_hook(x, *, block, mode="both_conservative", n_boot=10000,
                  n_perm=10000, seed=20260729):
        captured["combined_null_calls"].append(
            {
                "series": [repr(v) for v in x],
                "n": len(list(x)),
                "block": int(block),
                "mode": mode,
                "n_boot": int(n_boot),
                "n_perm": int(n_perm),
                "seed": int(seed),
            }
        )
        return orig_null(x, block=block, mode=mode, n_boot=n_boot,
                         n_perm=n_perm, seed=seed)

    gate_mod._pooled_oos = pooled_hook
    stats_mod.combined_null_p = null_hook

    # ---- replicate run_ratified_gate()'s gate section (no ledger validation) ----
    jan_records, _ = cs.CQ_GATE._load_repair_trades()
    apr_records, _ = cs._load_cs_trade_records(cs.WINDOWS["april_2026"])
    may_records, _ = cs._load_cs_trade_records(cs.WINDOWS["may_2026"])
    records = [*jan_records, *apr_records, *may_records]
    assert not any(
        r.entry_utc.month in (2, 3) or r.exit_utc.month in (2, 3) for r in records
    )

    costs_sha = _sha256(cs.PHASE17_COSTS)
    assert costs_sha == cs.EXPECTED_COST_SHA256
    v27_sha = _sha256(cs.V27)
    assert v27_sha == cs.EXPECTED_V27_SHA256
    family = load_candidate_family(cs.V27)
    costs = load_broker_true_costs(cs.PHASE17_COSTS)
    broker_symbols = sorted({r.symbol for r in records})
    base = OPTIONS["B_balanced"].with_(
        spec_id="wf_gate_option_B_balanced_cq_current_breaker_repair_mid",
        account="FTMO",
        cost_artifact_sha256=costs_sha,
        spread_band="mid",
        sleeve_symbol_allowlist={cs.SLEEVE: tuple(broker_symbols)},
    )
    spec = with_declared_family(base, "CANDIDATE_BOOK_V1", basis=ALL_DECLARED,
                                loaded=family)
    population, spec, population_mix = era_population.apply(
        "RECORDED", {cs.SLEEVE: records}, spec, account="FTMO", band="mid",
    )
    captures = (
        ("2026-01-01", "2026-01-30"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-30"),
    )
    gate = gate_mod.run_gate(
        population, spec, costs=costs, diagnose=True,
        server="FTMO-Server3", capture_windows=captures,
    )
    result = gate.as_dict()
    verdict = result["sleeves"][cs.SLEEVE]

    receipt = json.loads(RECEIPT.read_text())
    want = receipt["gate_result"]["sleeves"][cs.SLEEVE]

    def eq(a, b):
        return a == b

    checks = {
        "p_raw": eq(verdict["p_raw"], want["p_raw"]),
        "q_value": eq(verdict["q_value"], want["q_value"]),
        "verdict": eq(verdict["verdict"], want["verdict"]),
        "pooled_oos_mean_r": eq(verdict["pooled_oos_mean_r"], want["pooled_oos_mean_r"]),
        "null_telemetry": eq(verdict["telemetry"]["null"], want["telemetry"]["null"]),
        "p_floor": eq(verdict["telemetry"]["p_floor"], want["telemetry"]["p_floor"]),
        "dependence": eq(verdict["telemetry"]["dependence"], want["telemetry"]["dependence"]),
        "pooling_leverage": eq(
            verdict["telemetry"]["pooling_leverage"], want["telemetry"]["pooling_leverage"]
        ),
        "folds": eq(verdict["folds"], want["folds"]),
        "n_trades": eq(verdict["n_trades"], want["n_trades"]),
        "population_mix": eq(
            population_mix, receipt["gate_contract"]["population_mix"]
        ),
        "spec_sha256": eq(spec.seal(), receipt["gate_contract"]["spec_sha256"]),
    }

    out = {
        "schema": "gtos-a1-cleanroom-captured-series-v1",
        "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "inputs": {
            "cs_tool": str(CS_TOOL),
            "cs_tool_sha256": _sha256(CS_TOOL),
            "receipt": str(RECEIPT),
            "receipt_self_sha256": receipt.get("self_sha256"),
            "january_pool_given": str(JAN_POOL_GIVEN),
            "january_pool_sha256": given_sha,
            "january_pool_local_identical": True,
            "costs_sha256": costs_sha,
            "v27_sha256": v27_sha,
            "numpy": __import__("numpy").__version__,
            "python": sys.version,
        },
        "reproduction_checks": checks,
        "reproduction_all_pass": all(checks.values()),
        "verdict_reproduced": {
            "p_raw": verdict["p_raw"],
            "q_value": verdict["q_value"],
            "verdict": verdict["verdict"],
            "null": verdict["telemetry"]["null"],
        },
        "captured": captured,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({"all_pass": out["reproduction_all_pass"],
                      "checks": checks,
                      "n_pooled_calls": len(captured["pooled_oos_calls"]),
                      "n_null_calls": len(captured["combined_null_calls"])},
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

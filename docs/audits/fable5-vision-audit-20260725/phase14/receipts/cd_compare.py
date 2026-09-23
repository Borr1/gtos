"""Session CD -- the comparator: two `*_ECONOMICS.json` payloads -> one verdict.

`train_engine.accept` refuses any baseline whose row counts are not the published
2-day fixture (8,812 / 10 / 5 / 96 / 8,807). That guard is right for CB's
acceptance claim and wrong for this session: a REPAIRED arm is supposed to have
different counts, and a month arm has different counts by construction. So this
reads the same payloads through the same `identity.compare_economics` and adds
the economic delta table CD-3 needs.

Usage:
    python3 cd_compare.py --baseline A_ECONOMICS.json --candidate B_ECONOMICS.json \
        --label "projection inertness" --out CD_X.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.train_engine import identity  # noqa: E402


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def trade_economics(payload: dict[str, Any]) -> dict[str, Any]:
    """The arm-level economics a delta table quotes, off the pruned trade rows."""

    rows = payload.get("trades") or []
    out: dict[str, Any] = {"n_trades": len(rows)}
    for field in ("final_r", "cost_r", "net_r", "risk_cash", "approved_risk_pct"):
        values = [v for v in (_num(r.get(field)) for r in rows) if v is not None]
        out[f"sum_{field}"] = round(sum(values), 8) if values else None
        out[f"mean_{field}"] = (
            round(sum(values) / len(values), 8) if values else None
        )
        out[f"n_{field}"] = len(values)
    wins = [r for r in rows if (_num(r.get("net_r")) or 0.0) > 0]
    out["win_rate"] = round(len(wins) / len(rows), 6) if rows else None
    reasons: dict[str, int] = {}
    for row in rows:
        key = str(row.get("close_reason") or "")
        reasons[key] = reasons.get(key, 0) + 1
    out["close_reasons"] = dict(sorted(reasons.items()))
    return out


def pool_economics(payload: dict[str, Any]) -> dict[str, Any]:
    pool = dict(payload.get("missed_digest") or {})
    scoreable = pool.get("diagnostic_scoreable_rows") or 0
    net = (pool.get("positive_net_r") or 0.0) + (pool.get("negative_net_r") or 0.0)
    pool["net_r"] = round(net, 8)
    pool["mean_r_per_scoreable_row"] = (
        round(net / scoreable, 8) if scoreable else None
    )
    pool["base_rate_positive"] = (
        round((pool.get("positive_rows") or 0) / scoreable, 6) if scoreable else None
    )
    return pool


def delta(base: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in sorted(set(base) | set(cand)):
        b, c = base.get(key), cand.get(key)
        bn, cn = _num(b), _num(c)
        if bn is not None and cn is not None:
            out[key] = {
                "baseline": bn,
                "candidate": cn,
                "delta": round(cn - bn, 8),
                "pct": (round((cn - bn) / abs(bn) * 100, 4) if bn else None),
            }
        elif b != c:
            out[key] = {"baseline": b, "candidate": c, "delta": "non_numeric_change"}
    return out


def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    verdict = identity.compare_economics(baseline, candidate)
    base_tr, cand_tr = trade_economics(baseline), trade_economics(candidate)
    base_pool, cand_pool = pool_economics(baseline), pool_economics(candidate)
    return {
        "schema": "gtos.session_cd.economics_comparison.v1",
        "identity_verdict": verdict["verdict"],
        "identity_failures": verdict["failures"],
        "identity": {
            "trades": {
                k: v for k, v in verdict["trades"].items() if not k.startswith("only_in_")
            },
            "orders": {
                k: v for k, v in verdict["orders"].items() if not k.startswith("only_in_")
            },
            "counts": verdict["counts"],
            "missed_pool_identical": verdict["missed_opportunity_pool"]["identical"],
        },
        "trade_field_divergence": verdict.get("trade_field_divergence"),
        "trade_economics": {"baseline": base_tr, "candidate": cand_tr,
                            "delta": delta(base_tr, cand_tr)},
        "diagnostic_pool": {"baseline": base_pool, "candidate": cand_pool,
                            "delta": delta(base_pool, cand_pool)},
        "ledger_digests": {
            "baseline": baseline.get("ledger_digests"),
            "candidate": candidate.get("ledger_digests"),
            "moved": sorted(
                k
                for k in (baseline.get("ledger_digests") or {})
                if (baseline.get("ledger_digests") or {}).get(k)
                != (candidate.get("ledger_digests") or {}).get(k)
            ),
        },
        "summary_economics": {
            "baseline": baseline.get("summary_economics"),
            "candidate": candidate.get("summary_economics"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--out", default="")
    ns = ap.parse_args()

    baseline = json.loads(Path(ns.baseline).read_text())
    candidate = json.loads(Path(ns.candidate).read_text())
    result = compare(baseline, candidate)
    result["label"] = ns.label
    result["baseline_path"] = ns.baseline
    result["candidate_path"] = ns.candidate
    if ns.out:
        Path(ns.out).write_text(json.dumps(result, indent=1, default=str))
    print(
        json.dumps(
            {
                "label": ns.label,
                "verdict": result["identity_verdict"],
                "failures": result["identity_failures"],
                "counts": result["identity"]["counts"],
                "trades": {
                    k: v
                    for k, v in result["trade_economics"]["delta"].items()
                    if k in ("n_trades", "sum_net_r", "mean_net_r", "sum_cost_r",
                             "mean_cost_r", "sum_final_r", "win_rate")
                },
                "pool": {
                    k: v
                    for k, v in result["diagnostic_pool"]["delta"].items()
                    if k in ("diagnostic_scoreable_rows", "net_r",
                             "mean_r_per_scoreable_row", "base_rate_positive",
                             "positive_rows", "negative_rows")
                },
            },
            indent=1,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

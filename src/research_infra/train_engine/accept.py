"""CB-3 -- assemble the acceptance receipt from two measured runs.

Reads a frozen-baseline bench report + economics and a train-lane report +
economics, applies `identity.compare_economics`, and refuses to mark the receipt
accepted on anything short of outcome identity.

`accepted` is computed, never passed in. The three ways a receipt can look green
while meaning nothing are all closed here:

* either run errored -> refused;
* the trade/order sets, ledger counts or the missed-opportunity pool moved ->
  refused;
* the baseline's own row counts do not reproduce the published fixture
  (8,812 / 10 / 5 / 96 / 8,807) -> refused, because a baseline that is not the
  fixture cannot license a comparison against it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.research_infra.train_engine import TRAIN_ENGINE_VERSION, identity

#: The 2-day January S1R1 fixture's published row counts. Reproduced by 1's
#: run, by Session G's three, by AX's baseline and control, and by this
#: session's frozen baseline. A baseline that misses them is not the fixture.
PUBLISHED_FIXTURE_COUNTS = {
    "candidate_rows": 8812,
    "order_rows": 10,
    "trade_rows": 5,
    "scorecard_rows": 96,
    "missed_opportunity_rows": 8807,
}


def speed_table(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Wall, RSS and the day-2 hot path, plus the ratios, computed not quoted."""

    def hot_path(report: dict[str, Any]) -> float | None:
        rows = report.get("progress_rows") or []
        values = [
            row.get("economic_hot_path_seconds")
            for row in rows
            if isinstance(row, dict) and row.get("economic_hot_path_seconds")
        ]
        return max(values) if values else None

    base_wall = float(baseline.get("wall_seconds") or 0.0)
    cand_wall = float(candidate.get("wall_seconds") or 0.0)
    base_rss = float((baseline.get("rusage") or {}).get("maxrss_bytes") or 0.0)
    cand_rss = float((candidate.get("rusage") or {}).get("maxrss_bytes") or 0.0)
    base_hot, cand_hot = hot_path(baseline), hot_path(candidate)

    return {
        "baseline_wall_seconds": round(base_wall, 3),
        "candidate_wall_seconds": round(cand_wall, 3),
        "wall_speedup_x": round(base_wall / cand_wall, 4) if cand_wall else None,
        "baseline_maxrss_bytes": int(base_rss),
        "candidate_maxrss_bytes": int(cand_rss),
        "maxrss_ratio": round(cand_rss / base_rss, 4) if base_rss else None,
        "baseline_day2_hot_path_seconds": base_hot,
        "candidate_day2_hot_path_seconds": cand_hot,
        "hot_path_speedup_x": (
            round(base_hot / cand_hot, 4) if base_hot and cand_hot else None
        ),
        "candidate_profiled": bool(candidate.get("profile")),
        "profiler_overhead_note": (
            "the candidate carries the sampling profiler and the baseline does "
            "not, so the measured speedup is a LOWER bound"
            if candidate.get("profile") and not baseline.get("profile")
            else ""
        ),
    }


def residual_map(candidate: dict[str, Any], *, top: int = 22) -> dict[str, Any]:
    """Where the time that is LEFT lives. The commission asks for this by name."""

    profile = candidate.get("profile") or {}
    self_time = profile.get("self_seconds") or {}
    cumulative = profile.get("cumulative_seconds") or {}
    wall = float(candidate.get("wall_seconds") or 0.0)

    def share(seconds: Any) -> float | None:
        try:
            return round(float(seconds) / wall, 4) if wall else None
        except (TypeError, ValueError):
            return None

    return {
        "wall_seconds": wall,
        "samples": profile.get("samples"),
        "top_self_time": [
            {"node": node, "seconds": seconds, "share_of_wall": share(seconds)}
            for node, seconds in list(self_time.items())[:top]
        ],
        "top_cumulative": [
            {"node": node, "seconds": seconds, "share_of_wall": share(seconds)}
            for node, seconds in list(cumulative.items())[:top]
        ],
    }


def build_receipt(
    *,
    baseline: dict[str, Any],
    baseline_economics: dict[str, Any],
    candidate: dict[str, Any],
    candidate_economics: dict[str, Any],
) -> dict[str, Any]:
    refusals: list[str] = []

    if baseline.get("error"):
        refusals.append("baseline_run_errored")
    if candidate.get("error"):
        refusals.append("candidate_run_errored")

    counts = baseline.get("receipt_counts") or {}
    if {k: counts.get(k) for k in PUBLISHED_FIXTURE_COUNTS} != PUBLISHED_FIXTURE_COUNTS:
        refusals.append("baseline_is_not_the_published_fixture")

    comparison = identity.compare_economics(baseline_economics, candidate_economics)
    if comparison["verdict"] != "OUTCOME_IDENTICAL":
        refusals.append("outcome_identity_failed")

    return {
        "receipt_kind": "gtos.train_engine.acceptance.v1",
        "train_engine_version": TRAIN_ENGINE_VERSION,
        "evidence_class": (
            "TRAINING_EVIDENCE - never admission-grade. This receipt establishes "
            "that the train lane reproduces the frozen engine's TRADES on a "
            "bounded fixture. It is not a sealed arm of record and makes no "
            "claim about any strategy family."
        ),
        "fixture": {
            "arm": candidate.get("arm"),
            "window_start": candidate.get("window_start"),
            "stop_after_day": candidate.get("stop_after_day"),
            "is_sealed_arm_of_record": False,
            "bounded_fixture_note": (
                "--days/--stop-after-day sets engineering_stop_after_day, which "
                "the sealed path hardcodes to None (CLAUDE.md H5). No number "
                "here is an arm of record."
            ),
            "published_counts_reproduced": {
                k: counts.get(k) for k in PUBLISHED_FIXTURE_COUNTS
            },
        },
        "cuts_applied": candidate.get("patches_applied"),
        "cut_report": candidate.get("cut_report"),
        "verify_report": candidate.get("verify_report"),
        "memo_report": candidate.get("memo_report"),
        "partition_authorization": candidate.get("partition_authorization"),
        "fingerprint": candidate.get("fingerprint"),
        "speed": speed_table(baseline, candidate),
        "outcome_identity": comparison,
        "residual_map": residual_map(candidate),
        "refusals": refusals,
        "accepted": not refusals,
    }


def _load(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _economics_for(path: Path) -> dict[str, Any]:
    """The bench writes `<stem>_ECONOMICS.json` beside its slim report."""

    candidate = Path(path).parent / f"{Path(path).stem}_ECONOMICS.json"
    if not candidate.is_file():
        raise FileNotFoundError(f"economics_sidecar_absent:{candidate}")
    return _load(candidate)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="frozen bench report json")
    parser.add_argument("--candidate", required=True, help="train-lane report json")
    parser.add_argument("--out", required=True)
    ns = parser.parse_args()

    receipt = build_receipt(
        baseline=_load(Path(ns.baseline)),
        baseline_economics=_economics_for(Path(ns.baseline)),
        candidate=_load(Path(ns.candidate)),
        candidate_economics=_economics_for(Path(ns.candidate)),
    )
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=1, default=str))

    speed = receipt["speed"]
    print(
        f"[accept] accepted={receipt['accepted']} "
        f"verdict={receipt['outcome_identity']['verdict']} "
        f"speedup={speed['wall_speedup_x']}x "
        f"rss={speed['maxrss_ratio']}x -> {out}"
    )
    if receipt["refusals"]:
        print("  refusals: " + ", ".join(receipt["refusals"]))
    return 0 if receipt["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

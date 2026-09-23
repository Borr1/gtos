"""Relabel a training frame's outcomes under per-segment winning exit policies.

For every frame row whose candidate has a replayable post-fill path, replays
the segment-resolved winning policy (frozen segment table) over the M1 path
and rewrites the outcome labels:

- ``label_net_r``  = simulate_policy(final_r) - expected_cost_r_config/scale
- ``label_target_before_stop`` = 1 if relabeled net > 0 else 0  (under trail
  exits the policy-relevant binary is net-positivity, not fixed-target touch)
- ``label_relabel_policy_id`` / ``label_relabel_source`` provenance fields.

Rows without a path keep their incumbent labels with
``label_relabel_source='incumbent_no_path'`` and zero outcome-head weight.
Research-only; replay/proxy evidence; boundary stamps preserved from rows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.dynamic_execution_policy import PolicySpec, simulate_policy  # noqa: E402
from src.research.moonshot_segment_exit_policy_table import (  # noqa: E402
    load_segment_policy_table,
    resolve_segment_policy,
)
from src.research_infra.learned_edge_dataset_builder import (  # noqa: E402
    NET_R_WINSOR_HIGH,
    NET_R_WINSOR_LOW,
)
from src.research_infra.ultimate_exit_policy_segment_tournament import (  # noqa: E402
    build_path_dataset,
)

POLICY_SPEC_FIELDS = (
    "final_target_r", "stop_r", "tp1_r", "partial_close_ratio",
    "move_stop_to_be_on_tp1", "time_stop_bars", "trailing_trigger_r",
    "trailing_gap_r", "giveback_close_r", "abort_adverse_r",
    "abort_adverse_max_mfe_r", "abort_stop_r", "abort_no_progress_bars",
    "abort_min_mfe_r", "abort_close_below_r", "abort_consecutive_bars",
)


def _spec_from_params(policy_id: str, params: dict) -> PolicySpec:
    kwargs = {}
    for field_name in POLICY_SPEC_FIELDS:
        if field_name in (params or {}) and params[field_name] is not None:
            kwargs[field_name] = params[field_name]
    if "move_stop_to_be_on_tp1" in kwargs:
        kwargs["move_stop_to_be_on_tp1"] = bool(kwargs["move_stop_to_be_on_tp1"])
    return PolicySpec(name=str(policy_id), **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--route-dir", required=True, help="Ledger dir with oracle paths.")
    parser.add_argument("--cost-scale", type=float, required=True,
                        help="Divide configured expected_cost_r by this (geometry scale).")
    parser.add_argument("--mined-family-cost-scale", type=float, default=None,
                        help="Override cost scale for range_extreme_reversion rows (mixed-geometry universes: legacy 4.0, mined 1.0).")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    table = load_segment_policy_table(args.table)
    spec_cache: dict[str, PolicySpec] = {}

    # Month-chunked path reconstruction: the full-universe path dataset
    # (~600k paths x hundreds of observations) exceeds RAM in one shot.
    months: dict[str, set[str]] = {}
    with open(args.frame, encoding="utf-8") as src:
        src.readline()
        for line in src:
            row = json.loads(line)
            day = str(row.get("trading_day") or "")
            if len(day) == 10:
                months.setdefault(day[:7], set()).add(day)

    stats = {"rows": 0, "relabeled": 0, "no_path": 0, "sim_failed": 0}
    with open(args.frame, encoding="utf-8") as src, open(args.out, "w", encoding="utf-8") as dst:
        header_line = src.readline()
        header = json.loads(header_line)
        header["relabel"] = {
            "segment_table": str(args.table),
            "cost_scale": args.cost_scale,
            "outcome_binary_definition": "relabeled_net_r_positive",
        }
        dst.write(json.dumps(header, sort_keys=True, default=str) + "\n")
        current_month = None
        paths_by_id: dict[str, object] = {}
        for line in src:
            row = json.loads(line)
            stats["rows"] += 1
            month = str(row.get("trading_day") or "")[:7]
            if month != current_month:
                current_month = month
                dataset = build_path_dataset(
                    [args.route_dir],
                    include_missed=True,
                    day_filter=months.get(month, set()),
                )
                paths_by_id = {p.candidate_id: p for p in dataset.rows}
                print(f"[relabel] month {month}: {len(paths_by_id)} paths", flush=True)
            path = paths_by_id.get(str(row.get("candidate_id")))
            if path is None:
                row["label_relabel_source"] = "incumbent_no_path"
                row["weight_outcome_head"] = 0.0
                stats["no_path"] += 1
                dst.write(json.dumps(row, sort_keys=True, default=str) + "\n")
                continue
            resolution = resolve_segment_policy(
                table,
                asset_class=path.asset_class,
                origin_family=path.origin_family,
                session_bucket=path.session_bucket,
            )
            policy_id = str(resolution.get("policy_id"))
            spec = spec_cache.get(policy_id)
            if spec is None:
                spec = _spec_from_params(policy_id, resolution.get("params") or {})
                spec_cache[policy_id] = spec
            try:
                result = simulate_policy(spec, path.observations)
                final_r = float(getattr(result, "final_r"))
            except Exception:
                row["label_relabel_source"] = "incumbent_sim_failed"
                row["weight_outcome_head"] = 0.0
                stats["sim_failed"] += 1
                dst.write(json.dumps(row, sort_keys=True, default=str) + "\n")
                continue
            cost_scale = args.cost_scale
            if (
                args.mined_family_cost_scale is not None
                and str(row.get("f_origin_family")) == "range_extreme_reversion"
            ):
                cost_scale = args.mined_family_cost_scale
            cost = float(row.get("f_expected_cost_r") or 0.17) / cost_scale
            net = final_r - cost
            row["label_net_r_raw"] = net
            row["label_net_r"] = max(NET_R_WINSOR_LOW, min(NET_R_WINSOR_HIGH, net))
            row["label_target_before_stop"] = 1 if net > 0 else 0
            row["label_fill"] = 1
            row["label_outcome_valid"] = True
            row["label_relabel_policy_id"] = policy_id
            row["label_relabel_source"] = "segment_winner_replay"
            # restore outcome weight for rows the incumbent labeling zeroed
            if float(row.get("weight_outcome_head") or 0.0) <= 0.0:
                tier_w = 0.7  # m1_proxy_clean tier weight
                row["weight_outcome_head"] = float(row.get("weight_duplicate_group") or 1.0) * tier_w
            stats["relabeled"] += 1
            dst.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    print(json.dumps({**stats, "out": args.out}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

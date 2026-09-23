"""Pool-level census for the March confirm: P5's breaker gate and S2's cost ratio.

Reads the MISSED_OPPORTUNITY ledger, which carries every candidate the engine
considered and refused, with the pre-trade cost packet's own verdict
(`pretrade_cost_packet_status`, `broker_pretrade_cost_executable`) and the
R-denominated `cost_r` that decided it.

Two numbers come out, both frozen in `MARCH_PREREG_V1`:

* **P5 second clause** -- breaker cost-refusal rate in arm (v). The claim under
  test is that the R-denominated gate structurally excludes the transformed
  high-RR geometry, so the refusal rate should be ~100 %.
* **S2** -- median `cost_r` of transformed breaker candidates over median `cost_r`
  of untransformed ones, band [2, 8] (January 3.7x). The untransformed side must
  come from the arm that is the transform's own control (arm (iii) = arm (v)
  minus the transform), never from a differently-composed arm.

Validated against January before use: arm (v) 12,668/12,668 refused, arm (iii)
12,514/12,668, medians 0.701 vs 0.191.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
from pathlib import Path
from typing import Any, Iterator

BREAKER_FAMILY = "current_breaker_re_entry"


def _rows(route: Path, suffix: str) -> Iterator[dict[str, Any]]:
    prefix = route.name
    gz = route / f"{prefix}_{suffix}.jsonl.gz"
    plain = route / f"{prefix}_{suffix}.jsonl"
    if gz.is_file():
        handle = gzip.open(gz, "rt", encoding="utf-8")
    elif plain.is_file():
        handle = plain.open("r", encoding="utf-8")
    else:
        raise FileNotFoundError(f"{route}/{prefix}_{suffix}.jsonl[.gz]")
    with handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def census(route: Path) -> dict[str, Any]:
    total = 0
    breaker = 0
    refused = 0
    executable = 0
    costs: list[float] = []
    families: dict[str, int] = {}
    for row in _rows(route, "MISSED_OPPORTUNITY_LEDGER"):
        total += 1
        family = str(row.get("origin_family") or row.get("route_family") or "")
        families[family] = families.get(family, 0) + 1
        if family != BREAKER_FAMILY:
            continue
        breaker += 1
        if str(row.get("pretrade_cost_packet_status") or "").upper() == "REFUSED":
            refused += 1
        if row.get("broker_pretrade_cost_executable") is True:
            executable += 1
        value = row.get("cost_r")
        if value is None:
            value = row.get("expected_cost_r")
        if value is not None:
            costs.append(float(value))
    costs.sort()
    return {
        "route": route.name,
        "missed_rows_total": total,
        "breaker_candidates": breaker,
        "breaker_cost_refused": refused,
        "breaker_cost_refusal_rate": (round(refused / breaker, 6) if breaker else None),
        "breaker_cost_executable": executable,
        "breaker_cost_r_median": (round(statistics.median(costs), 6) if costs else None),
        "breaker_cost_r_mean": (round(statistics.fmean(costs), 6) if costs else None),
        "breaker_cost_r_n": len(costs),
        "family_counts_top": dict(
            sorted(families.items(), key=lambda kv: -kv[1])[:12]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--transformed-route", type=Path, required=True, help="arm (v)"
    )
    parser.add_argument(
        "--untransformed-route",
        type=Path,
        required=True,
        help="arm (iii) -- arm (v)'s composition WITHOUT the transform",
    )
    parser.add_argument("--out", type=Path)
    ns = parser.parse_args()

    transformed = census(ns.transformed_route)
    untransformed = census(ns.untransformed_route)
    t_med = transformed["breaker_cost_r_median"]
    u_med = untransformed["breaker_cost_r_median"]
    ratio = round(t_med / u_med, 4) if (t_med and u_med) else None
    payload = {
        "schema": "gtos.march.pool_census.v1",
        "transformed": transformed,
        "untransformed": untransformed,
        "S2_transformed_over_untransformed_median_cost_r": ratio,
        "S2_band": [2, 8],
        "S2_in_band": (None if ratio is None else bool(2 <= ratio <= 8)),
        "P5_breaker_cost_refusal_rate_transformed": transformed[
            "breaker_cost_refusal_rate"
        ],
        "P5_refusal_threshold": 0.99,
        "P5_refusal_clause_pass": (
            None
            if transformed["breaker_cost_refusal_rate"] is None
            else bool(transformed["breaker_cost_refusal_rate"] >= 0.99)
        ),
    }
    text = json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n"
    if ns.out:
        ns.out.parent.mkdir(parents=True, exist_ok=True)
        ns.out.write_text(text, encoding="utf-8")
        print(f"written: {ns.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline end-to-end: the REAL shadow runner over frozen February sources.

Constructs ``ForwardShadowRunner`` with a fake MetaTrader5 module that serves
broker-epoch rates derived from the frozen lane CSVs (the exact inverse of the
adapter's broker-clock conversion), runs one or more full decision cycles into
a throwaway namespace, then executes the shadow-packets parity harness against
the produced logs in a subprocess.  Zero network, zero MT5, zero mutation —
this is the complete acceptance loop run on the research Mac before any VPS
deploy.

    python3 offline_e2e_cycle.py [--asof 2026-02-03T12:15:00+00:00] [--cycles 2]
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
MY_REPO = HERE.parents[7]
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST = (
    HOLD
    / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/"
    "manifests/february_2026.json"
)

sys.path.insert(0, str(MY_REPO))

from src.research_infra import v4_timewarp_simulated_live_research_loop as tw  # noqa: E402
from src.research_infra.wave21_forward_shadow.mt5_read_only import (  # noqa: E402
    aggregate_h1_rows_from_m15_rows,
)
from src.research_infra.wave21_forward_shadow.runner_config import (  # noqa: E402
    ShadowRunnerConfig,
)
from src.research_infra.wave21_forward_shadow_runner import (  # noqa: E402
    ForwardShadowRunner,
)
from src.utils import broker_clock  # noqa: E402


class FakeRate(dict):
    def __getitem__(self, key):
        return dict.__getitem__(self, key)


class FakeManifestMT5:
    """MetaTrader5-module-shaped reader over the frozen lane CSVs."""

    def __init__(self, frames_by_broker_symbol, clock_rule):
        self.frames = frames_by_broker_symbol
        self.rule = clock_rule
        self.asof: datetime | None = None

    def _epoch(self, iso_text: str) -> float:
        parsed = datetime.fromisoformat(iso_text)
        broker_wall = broker_clock.utc_to_broker_naive(parsed, self.rule)
        return broker_wall.replace(tzinfo=timezone.utc).timestamp()

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        tf_name = {1: "M1", 15: "M15", 16385: "H1", 16388: "H4", 16408: "D1"}[
            int(timeframe)
        ]
        rows = self.frames.get(symbol, {}).get(tf_name, [])
        # Serve only bars OPENED at or before asof (the live buffer never
        # contains future bars; the forming bar appears with its open time).
        cutoff = self.asof
        visible = [
            row
            for row in rows
            if datetime.fromisoformat(row["time_utc"]) <= cutoff
        ]
        out = []
        for row in visible[-int(count):]:
            out.append(
                FakeRate(
                    time=self._epoch(row["time_utc"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    tick_volume=float(row.get("volume") or 0.0),
                )
            )
        return out

    def symbol_info_tick(self, symbol):
        # No live tick offline: the cost chain falls to the era/hour-aware
        # spread model — the replay-exact fallback.
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asof", default="2026-02-03T12:15:00+00:00")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--keep", action="store_true", help="keep the namespace")
    parser.add_argument(
        "--inject-outcome",
        action="store_true",
        help=(
            "after cycle 1, append a synthetic RESOLVED outcome for one of its "
            "eligible candidates and run the NEXT cycle on the next trading "
            "day — asserting the daily refit consumed it (row count +1, new "
            "artifact sha on the day's decisions)"
        ),
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    frames_by_symbol: dict[str, dict[str, list[dict]]] = {}
    for entry in manifest["bar_sources"]:
        tf = entry["timeframe"]
        if tf not in {"D1", "H4", "M15", "M1"}:
            continue
        path = HOLD / entry["repo_relpath"]
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [
                {
                    "time_utc": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
                for row in csv.DictReader(handle)
            ]
        frames_by_symbol.setdefault(entry["symbol"], {})[tf] = rows
    frames_by_broker: dict[str, dict[str, list[dict]]] = {}
    for symbol, by_tf in frames_by_symbol.items():
        by_tf = dict(by_tf)
        by_tf["H1"] = aggregate_h1_rows_from_m15_rows(by_tf["M15"], symbol=symbol)
        frames_by_broker[tw.ftmo_symbol(symbol)] = by_tf

    rule = broker_clock.resolve_rule("FTMO-Server3")
    fake_mt5 = FakeManifestMT5(frames_by_broker, rule)

    workdir = Path(tempfile.mkdtemp(prefix="w21-shadow-e2e-"))
    namespace = workdir / "funnel_shadow"
    runner_config = ShadowRunnerConfig(
        repo_root=MY_REPO,
        namespace_dir=namespace,
        model_artifact_path=HERE.parent / "SHADOW_RIDGE_MODEL_V1.json",
    )
    asof = datetime.fromisoformat(args.asof)
    fake_mt5.asof = asof
    runner = ForwardShadowRunner(
        runner_config,
        mt5_module=fake_mt5,
        clock=lambda: datetime.now(timezone.utc),
    )
    summaries = []
    refit_check: dict | None = None
    cycle_times = [asof + timedelta(minutes=15 * cycle) for cycle in range(int(args.cycles))]
    if args.inject_outcome:
        # cycle 1 on day D, remaining cycles at the next day's first windows
        next_day = (asof + timedelta(days=1)).replace(hour=0, minute=15)
        cycle_times = [asof] + [
            next_day + timedelta(minutes=15 * cycle)
            for cycle in range(max(1, int(args.cycles) - 1))
        ]
    for index, cycle_asof in enumerate(cycle_times):
        fake_mt5.asof = cycle_asof
        packet = runner.run_cycle(cycle_asof)
        summaries.append(
            {
                "window": packet.get("decision_window_id"),
                "candidates": packet.get("candidate_count"),
                "eligible": packet.get("eligible_count"),
                "dispositions": packet.get("dispositions"),
                "selection": packet.get("selection"),
                "model": packet.get("model"),
                "model_artifact_sha256": packet.get("model_artifact_sha256"),
            }
        )
        print("E2E_CYCLE=" + json.dumps(summaries[-1], sort_keys=True, default=str), flush=True)
        if args.inject_outcome and index == 0:
            day_file = namespace / "decision_packets" / f"{cycle_asof.date().isoformat()}.jsonl"
            packet_row = json.loads(day_file.read_text(encoding="utf-8").splitlines()[0])
            eligible = [
                candidate
                for candidate in packet_row.get("candidates") or ()
                if candidate.get("eligible")
            ]
            if not eligible:
                raise SystemExit("inject-outcome: no eligible candidate in cycle 1")
            key = eligible[0]["features"]["candidate_occurrence_key"]
            with (namespace / "order_outcomes.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "schema": "gtos.wave21.forward_shadow.order_outcome.v1",
                            "candidate_occurrence_key": key,
                            "final": True,
                            "lifecycle_label_status": "RESOLVED_FILLED_TARGET",
                            "terminal_net_r": 1.5,
                            "occupancy_end_utc": (
                                cycle_asof + timedelta(minutes=10)
                            ).isoformat(),
                            "resolved_at_utc": (
                                cycle_asof + timedelta(minutes=10)
                            ).isoformat(),
                            "synthetic_e2e_injection": True,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
            print(f"E2E_INJECTED_OUTCOME={key}", flush=True)
    if args.inject_outcome and len(summaries) >= 2:
        first, second = summaries[0], summaries[1]
        refit_check = {
            "day1_model_mode": (first.get("model") or {}).get("mode"),
            "day1_sha": str(first.get("model_artifact_sha256"))[:16],
            "day2_model": second.get("model"),
            "day2_sha": str(second.get("model_artifact_sha256"))[:16],
            "sha_changed": first.get("model_artifact_sha256")
            != second.get("model_artifact_sha256"),
            "forward_rows_consumed": (second.get("model") or {}).get("forward_rows") == 1,
            "training_rows_plus_one": (second.get("model") or {}).get("training_rows")
            == ((runner._frozen_corpus.row_count if runner._frozen_corpus else 284652) + 1),
        }
        print("E2E_REFIT_CHECK=" + json.dumps(refit_check, sort_keys=True), flush=True)
        if not (
            refit_check["sha_changed"]
            and refit_check["forward_rows_consumed"]
            and refit_check["training_rows_plus_one"]
        ):
            raise SystemExit("refit day-boundary check FAILED")

    harness = subprocess.run(
        [
            sys.executable,
            str(HERE.parent / "shadow_parity_harness.py"),
            "--mode",
            "shadow-packets",
            "--packets",
            str(namespace),
        ],
        text=True,
        capture_output=True,
    )
    print(harness.stdout.strip()[-3000:])
    if harness.returncode != 0:
        print(harness.stderr.strip()[-2000:], file=sys.stderr)
    if not args.keep:
        shutil.rmtree(workdir, ignore_errors=True)
    else:
        print(f"E2E_NAMESPACE={namespace}")
    print(
        "E2E_RESULT="
        + json.dumps(
            {"cycles": len(summaries), "parity_exit": harness.returncode},
            sort_keys=True,
        )
    )
    return harness.returncode


if __name__ == "__main__":
    raise SystemExit(main())

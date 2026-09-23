"""AX-3: measure concurrent arms rather than assume them.

H3 banned parallel replays on this machine. The stated reason -- the source
layer's 5x materialisation -- was refuted (Session G, B84/B85), and
``THIRD_REVIEW.md`` A1 relocated the real cause: ~6.4 GB of per-day evidence
accumulation in the timewarp loop. A window is four independent arms, so if the
footprint fits, the window's wall-clock is the slowest arm rather than the sum
of four.

This module launches N arms as separate processes, samples each one's RSS and
the machine's swap, and reports the **measured** net cost. It prints a number,
not a hope; if the machine cannot hold N arms it says so with the swap reading
that proves it.

Nothing here runs a sealed window. It runs whichever arms and day-bound the
caller asks for, and a day-bounded run is a fixture, never an arm of record.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def _swap_used_bytes() -> int:
    try:
        out = subprocess.run(
            ["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, check=False
        ).stdout
        used = out.split("used =")[1].split()[0]
        return int(float(used.rstrip("MG")) * (1024**2 if used.endswith("M") else 1024**3))
    except Exception:
        return 0


def _rss_bytes(pid: int) -> int:
    try:
        out = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        return int(out) * 1024 if out else 0
    except Exception:
        return 0


class _Watcher(threading.Thread):
    daemon = True

    def __init__(self, procs: dict[str, subprocess.Popen], interval: float = 2.0):
        super().__init__(name="fast-engine-campaign-watch")
        self.procs = procs
        self.interval = interval
        self.stop_flag = threading.Event()
        self.peak_rss: dict[str, int] = {name: 0 for name in procs}
        self.peak_total_rss = 0
        self.peak_swap = 0
        self.samples = 0

    def run(self) -> None:
        while not self.stop_flag.is_set():
            total = 0
            for name, proc in self.procs.items():
                if proc.poll() is None:
                    rss = _rss_bytes(proc.pid)
                    self.peak_rss[name] = max(self.peak_rss[name], rss)
                    total += rss
            self.peak_total_rss = max(self.peak_total_rss, total)
            self.peak_swap = max(self.peak_swap, _swap_used_bytes())
            self.samples += 1
            time.sleep(self.interval)


def run_arms(
    *,
    arms: list[str],
    stop_after_day: str | None,
    prefix_stem: str,
    patches: str | None,
    scratch: Path,
    profile_interval_ms: float = 0.0,
) -> dict[str, Any]:
    """Launch one process per arm, concurrently, and measure what it costs."""

    scratch.mkdir(parents=True, exist_ok=True)
    procs: dict[str, subprocess.Popen] = {}
    logs: dict[str, Path] = {}
    reports: dict[str, Path] = {}

    swap_before = _swap_used_bytes()
    started = time.perf_counter()
    for arm in arms:
        prefix = f"{prefix_stem}_B7_5_{arm}"
        report = scratch / f"{prefix}.json"
        log = scratch / f"{prefix}.log"
        cmd = [
            sys.executable,
            "-m",
            "src.research_infra.fast_engine.bench",
            "--arm",
            arm,
            "--prefix",
            prefix,
            "--out",
            str(report),
            "--profile-interval-ms",
            str(profile_interval_ms),
        ]
        if stop_after_day:
            cmd += ["--stop-after-day", stop_after_day]
        if patches is not None:
            cmd += ["--patches", patches]
        handle = log.open("w")
        procs[arm] = subprocess.Popen(
            cmd, cwd=str(REPO_ROOT), stdout=handle, stderr=subprocess.STDOUT
        )
        logs[arm] = log
        reports[arm] = report

    watcher = _Watcher(procs)
    watcher.start()
    exit_codes = {arm: proc.wait() for arm, proc in procs.items()}
    wall = time.perf_counter() - started
    watcher.stop_flag.set()
    watcher.join(timeout=5)

    per_arm: dict[str, Any] = {}
    for arm in arms:
        entry: dict[str, Any] = {
            "exit_code": exit_codes[arm],
            "peak_rss_bytes": watcher.peak_rss[arm],
            "log": str(logs[arm]),
        }
        if reports[arm].is_file():
            data = json.loads(reports[arm].read_text())
            entry["wall_seconds"] = data.get("wall_seconds")
            entry["maxrss_bytes"] = data.get("rusage", {}).get("maxrss_bytes")
            entry["receipt_counts"] = data.get("receipt_counts")
            entry["error"] = (data.get("error") or "")[:400] or None
        per_arm[arm] = entry

    contended_seconds = sum(
        float(entry.get("wall_seconds") or 0.0) for entry in per_arm.values()
    )
    return {
        "arms": arms,
        "stop_after_day": stop_after_day,
        "patches": patches,
        "concurrent_wall_seconds": round(wall, 3),
        "sum_of_CONTENDED_arm_wall_seconds": round(contended_seconds, 3),
        # NOT a benefit measure. Dividing the sum of the CONTENDED arm walls by
        # the concurrent wall is close to len(arms) whenever the processes
        # overlap at all -- it measures overlap, not speedup. The honest
        # reference is each arm's SOLO wall, which this harness cannot know, so
        # it is named rather than reported.
        "overlap_ratio_not_speedup": (
            round(contended_seconds / wall, 3) if wall > 0 and contended_seconds else None
        ),
        "honest_speedup_note": (
            "true throughput gain = (len(arms) * SOLO_wall) / concurrent_wall. "
            "Supply the solo wall from a separate single-arm bench run; this "
            "harness deliberately does not guess it."
        ),
        "peak_total_rss_bytes": watcher.peak_total_rss,
        "peak_swap_used_bytes": watcher.peak_swap,
        "swap_used_before_bytes": swap_before,
        "swap_growth_bytes": max(0, watcher.peak_swap - swap_before),
        "watch_samples": watcher.samples,
        "cpu_count": os.cpu_count(),
        "per_arm": per_arm,
        "all_ok": all(code == 0 for code in exit_codes.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arms", default="S0R0,S1R1")
    parser.add_argument("--stop-after-day", default=None)
    parser.add_argument("--prefix-stem", default="AX_CONC")
    parser.add_argument("--patches", default=None)
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--out", required=True)
    ns = parser.parse_args()

    report = run_arms(
        arms=[a.strip() for a in ns.arms.split(",") if a.strip()],
        stop_after_day=ns.stop_after_day,
        prefix_stem=ns.prefix_stem,
        patches=ns.patches,
        scratch=Path(ns.scratch),
    )
    Path(ns.out).write_text(json.dumps(report, indent=1, default=str))
    print(
        f"[campaign] arms={report['arms']} concurrent={report['concurrent_wall_seconds']:.1f}s "
        f"serial_sum={report['sum_of_arm_wall_seconds']:.1f}s "
        f"speedup={report['speedup_vs_serial']} "
        f"peak_total_rss={report['peak_total_rss_bytes'] / 1e9:.2f}GB "
        f"swap_growth={report['swap_growth_bytes'] / 1e9:.2f}GB",
        file=sys.stderr,
    )
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

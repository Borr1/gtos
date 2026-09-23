"""Low-overhead statistical wall-clock sampler.

Runs a target module's main() in the main thread while a daemon thread samples
sys._current_frames() at a fixed interval. Overhead is ~1-2% and it does not
distort per-call costs the way cProfile does.

Usage:
  python3 wallsampler.py --out PROFILE.json --interval-ms 5 -- <module> <args...>
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import runpy
import sys
import threading
import time
import traceback


class Sampler(threading.Thread):
    daemon = True

    def __init__(self, main_tid: int, interval: float, repo_root: str) -> None:
        super().__init__(name="wallsampler")
        self.main_tid = main_tid
        self.interval = interval
        self.repo_root = repo_root
        self.stop_flag = threading.Event()
        self.self_time: collections.Counter[str] = collections.Counter()
        self.total_time: collections.Counter[str] = collections.Counter()
        self.stacks: collections.Counter[str] = collections.Counter()
        self.samples = 0
        self.missed = 0
        self.started_at = time.perf_counter()

    def _frame_key(self, frame) -> str:
        code = frame.f_code
        fn = code.co_filename
        if fn.startswith(self.repo_root):
            fn = fn[len(self.repo_root) :].lstrip("/")
        return f"{fn}:{code.co_name}:{code.co_firstlineno}"

    def run(self) -> None:
        while not self.stop_flag.is_set():
            frames = sys._current_frames()
            frame = frames.get(self.main_tid)
            if frame is None:
                self.missed += 1
            else:
                self.samples += 1
                leaf = self._frame_key(frame)
                self.self_time[leaf] += 1
                seen = set()
                chain = []
                f = frame
                depth = 0
                while f is not None and depth < 220:
                    k = self._frame_key(f)
                    chain.append(k)
                    if k not in seen:
                        seen.add(k)
                        self.total_time[k] += 1
                    f = f.f_back
                    depth += 1
                # keep a bounded stack signature for hot-path reconstruction
                self.stacks[";".join(reversed(chain[:40]))] += 1
            del frames
            time.sleep(self.interval)

    def report(self, wall: float) -> dict:
        n = max(1, self.samples)
        return {
            "wall_seconds": wall,
            "samples": self.samples,
            "missed": self.missed,
            "interval_seconds": self.interval,
            "self_seconds": {
                k: round(v / n * wall, 4)
                for k, v in self.self_time.most_common(220)
            },
            "cumulative_seconds": {
                k: round(v / n * wall, 4)
                for k, v in self.total_time.most_common(220)
            },
            "top_stacks": [
                {"count": c, "seconds": round(c / n * wall, 3), "stack": s.split(";")}
                for s, c in self.stacks.most_common(25)
            ],
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval-ms", type=float, default=5.0)
    ap.add_argument("--repo-root", default=os.getcwd())
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    ns = ap.parse_args()

    rest = ns.rest
    if rest and rest[0] == "--":
        rest = rest[1:]
    if not rest:
        print("no target module given", file=sys.stderr)
        return 2

    module = rest[0]
    sys.argv = [module] + rest[1:]

    sampler = Sampler(
        main_tid=threading.get_ident(),
        interval=ns.interval_ms / 1000.0,
        repo_root=os.path.abspath(ns.repo_root),
    )
    sampler.start()
    t0 = time.perf_counter()
    rc = 0
    err = None
    try:
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit as exc:
        rc = int(exc.code or 0)
    except BaseException:
        err = traceback.format_exc()
        rc = 1
    wall = time.perf_counter() - t0
    sampler.stop_flag.set()
    sampler.join(timeout=5)

    rep = sampler.report(wall)
    rep["exit_code"] = rc
    rep["error"] = err
    with open(ns.out, "w") as fh:
        json.dump(rep, fh, indent=1)
    print(
        f"\n[wallsampler] wall={wall:.2f}s samples={sampler.samples} "
        f"-> {ns.out} rc={rc}",
        file=sys.stderr,
    )
    if err:
        print(err, file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

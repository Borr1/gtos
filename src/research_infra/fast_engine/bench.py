"""Run the sealed engine on a January window and measure it honestly.

One process, one arm. Captures wall-clock, peak RSS, a low-overhead statistical
profile (optional), and the economic outputs the reproduction comparator reads.

The baseline and the fast lane go through *this same harness*, so the A/B
difference is the patch set and nothing else -- no harness-shaped bias.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import gc
import hashlib
import json
import os
import resource
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# sampling
# ---------------------------------------------------------------------------


class WallSampler(threading.Thread):
    """Statistical wall-clock sampler over the main thread's Python frames.

    Same design as the first audit's ``wallsampler.py`` so the two profiles are
    directly comparable; ~1-2 % overhead, and it does not distort per-call cost
    the way cProfile does.
    """

    daemon = True

    def __init__(self, main_tid: int, interval: float, repo_root: str) -> None:
        super().__init__(name="fast-engine-sampler")
        self.main_tid = main_tid
        self.interval = interval
        self.repo_root = repo_root
        self.stop_flag = threading.Event()
        self.self_time: collections.Counter[str] = collections.Counter()
        self.total_time: collections.Counter[str] = collections.Counter()
        self.samples = 0
        self.missed = 0

    def _frame_key(self, frame: Any) -> str:
        code = frame.f_code
        name = code.co_filename
        if name.startswith(self.repo_root):
            name = name[len(self.repo_root) :].lstrip("/")
        return f"{name}:{code.co_name}:{code.co_firstlineno}"

    def run(self) -> None:
        while not self.stop_flag.is_set():
            frames = sys._current_frames()
            frame = frames.get(self.main_tid)
            if frame is None:
                self.missed += 1
            else:
                self.samples += 1
                self.self_time[self._frame_key(frame)] += 1
                seen = set()
                current = frame
                depth = 0
                while current is not None and depth < 220:
                    key = self._frame_key(current)
                    if key not in seen:
                        seen.add(key)
                        self.total_time[key] += 1
                    current = current.f_back
                    depth += 1
            del frames
            time.sleep(self.interval)

    def report(self, wall: float) -> dict[str, Any]:
        n = max(1, self.samples)
        return {
            "samples": self.samples,
            "missed": self.missed,
            "interval_seconds": self.interval,
            "self_seconds": {
                key: round(count / n * wall, 4)
                for key, count in self.self_time.most_common(160)
            },
            "cumulative_seconds": {
                key: round(count / n * wall, 4)
                for key, count in self.total_time.most_common(120)
            },
        }


class RssSampler(threading.Thread):
    """1 Hz peak-RSS timeline. ``ru_maxrss`` alone hides the shape."""

    daemon = True

    def __init__(self, interval: float = 1.0) -> None:
        super().__init__(name="fast-engine-rss")
        self.interval = interval
        self.stop_flag = threading.Event()
        self.timeline: list[tuple[float, int]] = []
        self.peak_bytes = 0
        self._t0 = time.perf_counter()

    def run(self) -> None:
        while not self.stop_flag.is_set():
            rss = _current_rss_bytes()
            if rss:
                self.peak_bytes = max(self.peak_bytes, rss)
                self.timeline.append((round(time.perf_counter() - self._t0, 2), rss))
            time.sleep(self.interval)


def _current_rss_bytes() -> int:
    """Resident set size of this process, in bytes, without external deps."""

    try:
        import ctypes

        class _TaskBasicInfo(ctypes.Structure):
            _fields_ = [
                ("suspend_count", ctypes.c_int),
                ("virtual_size", ctypes.c_ulong),
                ("resident_size", ctypes.c_ulong),
                ("user_time", ctypes.c_ulonglong),
                ("system_time", ctypes.c_ulonglong),
                ("policy", ctypes.c_int),
            ]

        libc = ctypes.CDLL("/usr/lib/libSystem.dylib", use_errno=True)
        info = _TaskBasicInfo()
        count = ctypes.c_uint(ctypes.sizeof(info) // ctypes.sizeof(ctypes.c_uint))
        task = libc.mach_task_self()
        # MACH_TASK_BASIC_INFO == 20
        if libc.task_info(task, 20, ctypes.byref(info), ctypes.byref(count)) == 0:
            return int(info.resident_size)
    except Exception:
        pass
    try:
        import subprocess

        out = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(os.getpid())],
            capture_output=True,
            text=True,
            check=False,
        )
        return int(out.stdout.strip()) * 1024
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# economics extraction
# ---------------------------------------------------------------------------

# Fields that carry the arm's economics. Everything else in a trade row is
# provenance. The comparator compares these, nan-aware, plus the full ordered
# key set, so a dropped field is a failure rather than a silent pass.
TRADE_ECONOMIC_FIELDS = (
    "order_id",
    "symbol",
    "direction",
    "entry_price",
    "exit_price",
    "stop_price",
    "target_price",
    "risk_cash",
    "net_cash",
    "gross_cash",
    "exact_r",
    "final_r",
    "net_r",
    "r_multiple",
    "exit_reason",
    "entry_time_utc",
    "exit_time_utc",
    "lots",
    "volume",
)


def extract_economics(route: Path, prefix: str) -> dict[str, Any]:
    """Read the arm's economic ledgers back off disk into a comparable shape.

    The three small ledgers are kept whole and compared field by field. The
    missed-opportunity ledger is 8,807 rows on the 2-day fixture alone, so it is
    reduced two ways instead: the analyzer's own diagnostic aggregate (so the
    comparison is against the quantity `JANUARY_BANK.md` 3 quotes) **and** a
    canonical SHA-256 over every row with the volatile fields stripped, which is
    field-agnostic and catches a divergence the aggregate could cancel out.
    """

    if not Path(route).is_dir():
        # Absence must be loud. The bench deletes its own route after
        # extracting, so a later re-extraction against the same path silently
        # produced an empty payload -- four digests of the empty string and zero
        # rows -- which then OVERWROTE a good comparison file. An empty
        # extraction is never a valid economics payload; refuse to make one.
        raise FileNotFoundError(f"economics_route_absent:{route}")

    def rows(name: str) -> list[dict[str, Any]]:
        path = route / f"{prefix}_{name}.jsonl"
        if not path.is_file():
            return []
        out: list[dict[str, Any]] = []
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    trades = rows("TRADE_LEDGER")
    orders = rows("ORDER_LEDGER")
    scorecards = rows("SCORECARD_LEDGER")
    missed = rows("MISSED_OPPORTUNITY_LEDGER")

    summary_path = route / f"{prefix}_SUMMARY.json"
    summary = json.loads(summary_path.read_text()) if summary_path.is_file() else {}

    return {
        # Recorded so the comparator can normalise this run's namespace out of
        # the row VALUES it is stamped into. Without it, two runs of the same arm
        # differ on every id field for purely naming reasons.
        "output_prefix": prefix,
        "counts": {
            "trade": len(trades),
            "order": len(orders),
            "scorecard": len(scorecards),
            "missed": len(missed),
        },
        # Scalars only. A whole trade row is ~1.9 MB of nested provenance, so
        # keeping 111 of them whole made a 206 MB comparison file. The nested
        # structure is not dropped from the CLAIM -- it is covered by the
        # per-ledger digest below, which hashes every field. What the pruned
        # rows buy is the ability to say WHICH field moved when one does.
        "trades": [_prune_row(row) for row in trades],
        "orders": [_prune_row(row) for row in orders],
        "scorecards": [_prune_row(row) for row in scorecards],
        "missed_digest": _missed_digest(missed),
        "ledger_digests": {
            "trade": _ledger_digest(trades, prefix),
            "order": _ledger_digest(orders, prefix),
            "scorecard": _ledger_digest(scorecards, prefix),
            "missed": _ledger_digest(missed, prefix),
        },
        "summary_economics": _summary_economics(summary),
    }


# The analyzer's own gate and field (`analyze_b7_5_selection_sizing_matrix.py`
# :742-770). Mirrored exactly so the fast lane's diagnostic pool is comparable
# to the sealed artifact's, not to a lookalike.
def _missed_digest(missed: list[dict[str, Any]]) -> dict[str, Any]:
    """Diagnostic-pool economics: the aggregate JANUARY_BANK 3 quotes."""

    positive = 0.0
    negative = 0.0
    positive_rows = 0
    negative_rows = 0
    flat_rows = 0
    scoreable_rows = 0
    unreadable_rows = 0
    for row in missed:
        status = str(row.get("missed_opportunity_r_scoreability_status") or "")
        diagnostic = bool(
            row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
            or status == "diagnostic_opportunity_r_scoreable"
        )
        if not diagnostic:
            continue
        scoreable_rows += 1
        try:
            number = float(row.get("opportunity_net_proxy_r"))
        except (TypeError, ValueError):
            # A silent null here would understate the pool; count it loudly.
            unreadable_rows += 1
            continue
        if number > 0:
            positive += number
            positive_rows += 1
        elif number < 0:
            negative += number
            negative_rows += 1
        else:
            flat_rows += 1
    return {
        "rows": len(missed),
        "diagnostic_scoreable_rows": scoreable_rows,
        "unreadable_proxy_rows": unreadable_rows,
        "positive_net_r": round(positive, 8),
        "negative_net_r": round(negative, 8),
        "positive_rows": positive_rows,
        "negative_rows": negative_rows,
        "flat_rows": flat_rows,
    }


def _prune_row(row: dict[str, Any]) -> dict[str, Any]:
    """Keep scalar fields; nested containers are covered by the ledger digest."""

    return {
        key: value
        for key, value in row.items()
        if not isinstance(value, (dict, list, tuple))
    }


def _ledger_digest(rows: list[dict[str, Any]], prefix: str = "") -> str:
    """Canonical SHA-256 over a ledger, minus the fields that may legitimately
    differ between the frozen lane and the fast lane, and with this run's own
    output namespace normalised out of the row VALUES it is stamped into."""

    from src.research_infra.fast_engine.reproduction import (
        RUN_NAMESPACE_PLACEHOLDER,
        is_excluded,
    )

    token = (prefix or "").lower()
    hasher = hashlib.sha256()
    for row in rows:
        pruned = {key: value for key, value in row.items() if not is_excluded(key)}
        text = json.dumps(pruned, sort_keys=True, default=str)
        if token:
            lowered = text.lower()
            if token in lowered:
                out: list[str] = []
                index = 0
                while True:
                    found = lowered.find(token, index)
                    if found < 0:
                        out.append(text[index:])
                        break
                    out.append(text[index:found])
                    out.append(RUN_NAMESPACE_PLACEHOLDER)
                    index = found + len(token)
                text = "".join(out)
        hasher.update(text.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _summary_economics(summary: dict[str, Any]) -> dict[str, Any]:
    """Pull the arm-level economic scalars out of the run summary."""

    wanted = (
        "scoreable_net_cash",
        "total_accepted_risk_cash",
        "max_drawdown_cash",
        "physical_net_r",
        "net_cash",
        "accepted_risk_cash",
    )
    found: dict[str, Any] = {}

    def walk(node: Any, path: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in wanted and isinstance(value, (int, float)):
                    found[f"{path}.{key}".lstrip(".")] = value
                elif isinstance(value, (dict, list)):
                    walk(value, f"{path}.{key}".lstrip("."))
        elif isinstance(node, list):
            for index, item in enumerate(node[:50]):
                walk(item, f"{path}[{index}]")

    walk(summary)
    return found


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------


def run_window(
    *,
    arm: str,
    stop_after_day: str | None,
    output_prefix: str,
    patches: "list[str] | None",
    abc_symbols: "tuple[str, ...]",
    verify: bool,
    profile_interval_ms: float,
    keep_outputs: bool,
    evidence: str = "full",
    installer_factory: "Any | None" = None,
    extra_report: "dict[str, Any] | None" = None,
    input_provider: "Any | None" = None,
) -> dict[str, Any]:
    """Run one arm through the harness.

    ``installer_factory`` lets a caller supply a patch registry that is a
    SUPERSET of this module's -- the train lane (Session CB) registers its own
    cuts and reuses this harness rather than forking it, so the A/B stays
    harness-identical, which is the whole reason this function exists.
    """

    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )
    from src.research_infra.fast_engine import accel, sealed_inputs

    route = attempt5.ATTEMPT5_NAMESPACE_ROOT / output_prefix
    if input_provider is None:
        sealed = sealed_inputs.resolve_sealed_january(REPO_ROOT)
        args = sealed_inputs.build_january_args(
            repo_root=REPO_ROOT,
            arm_id=arm,
            output_dir=route,
            output_prefix=output_prefix,
            stop_after_day=stop_after_day,
            sealed=sealed,
        )
        sealed_inputs.prelude(args)
        runtime_bindings = contextlib.nullcontext()
        input_authority = None
    else:
        sealed = input_provider
        args = input_provider.build_args(
            arm_id=arm,
            output_dir=route,
            output_prefix=output_prefix,
            stop_after_day=stop_after_day,
        )
        runtime_bindings = input_provider.runtime_bindings()
        input_authority = input_provider.input_authority()

    build = installer_factory or accel.build_installer
    installer = build(abc_symbols=abc_symbols, verify=verify, strict=False)
    applied = installer.install(patches) if patches != [] else []

    sampler = None
    if profile_interval_ms > 0:
        sampler = WallSampler(
            main_tid=threading.get_ident(),
            interval=profile_interval_ms / 1000.0,
            repo_root=str(REPO_ROOT),
        )
        sampler.start()
    rss = RssSampler()
    rss.start()

    gc.collect()
    started = time.perf_counter()
    error = None
    receipt: Any = None
    try:
        with runtime_bindings:
            receipt = attempt5.run_replay_engine(args)
    except BaseException:
        error = traceback.format_exc()
    wall = time.perf_counter() - started

    if sampler is not None:
        sampler.stop_flag.set()
        sampler.join(timeout=5)
    rss.stop_flag.set()
    rss.join(timeout=5)

    usage = resource.getrusage(resource.RUSAGE_SELF)
    report: dict[str, Any] = {
        "arm": arm,
        "window_start": sealed.window_start,
        "stop_after_day": stop_after_day,
        "source_prewarm_workers": getattr(args, "source_prewarm_workers", None),
        "bounded_prewarm_previous_workers": getattr(
            args, "bounded_prewarm_previous_workers", None
        ),
        "bounded_prewarm_policy": getattr(args, "bounded_prewarm_policy", None),
        # The execution-seal digest THIS run bound, taken off the args object
        # `prelude` stamped it on. Surfaced because it identifies the config the
        # arm ran under, and rebuilding a second args object to read it later
        # yields None -- `bind_fresh_source` stamps the first one, not the copy.
        "expected_shared_execution_contract_sha256": getattr(
            args, "expected_shared_execution_contract_sha256", None
        ),
        "output_prefix": output_prefix,
        "route": str(route),
        "wall_seconds": round(wall, 3),
        "evidence_level": evidence,
        "patches_applied": applied,
        "patch_manifest": installer.manifest(),
        "verify_mode": verify,
        # Memo hit rates are the explanation for whatever speedup the wall-clock
        # shows, so they are always reported -- not only under --verify.
        "memo_report": accel.memo_report(),
        "verify_report": accel.verify_report() if verify else None,
        "rusage": {
            "utime": usage.ru_utime,
            "stime": usage.ru_stime,
            "maxrss_bytes": usage.ru_maxrss,
            "majflt": usage.ru_majflt,
            "minflt": usage.ru_minflt,
            "inblock": usage.ru_inblock,
            "oublock": usage.ru_oublock,
        },
        "rss_peak_bytes": rss.peak_bytes,
        "rss_timeline": rss.timeline,
        "error": error,
    }
    if input_authority is not None:
        report["lane_input_authority"] = input_authority
    if sampler is not None:
        report["profile"] = sampler.report(wall)
    if isinstance(receipt, dict):
        report["receipt_counts"] = {
            key: receipt.get(key)
            for key in (
                "candidate_rows",
                "missed_opportunity_rows",
                "order_rows",
                "trade_rows",
                "scorecard_rows",
            )
        }
        report["progress_rows"] = [
            {
                field: row.get(field)
                for field in (
                    "start_day",
                    "economic_hot_path_seconds",
                    "proof_finalization_seconds",
                    "selected_order_sequence",
                )
            }
            for row in receipt.get("progress_rows", [])
            if isinstance(row, dict)
        ]
    if error is None:
        report["economics"] = extract_economics(route, output_prefix)
    report["outputs_retained"] = bool(keep_outputs)
    if not keep_outputs:
        report["outputs_removed"] = _remove_route(route)
    if extra_report:
        report.update(extra_report)
    return report


def _remove_route(route: Path) -> list[str]:
    """Delete this run's own output namespace, by explicit path only.

    B88's rule for the denominator-to-deployment route: never ``git clean``
    anywhere near it -- two ``REPLAY_EXTENSION_*`` paths there are load-bearing
    by their ABSENCE. So this removes exactly the two directories this run
    created, refuses anything that is not strictly below the attempt-5
    namespace root, and reports what it removed.
    """

    import shutil

    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as attempt5,
    )

    root = attempt5.ATTEMPT5_NAMESPACE_ROOT.resolve()
    removed: list[str] = []
    for target in (route, attempt5.semantic_diagnostic_root(route)):
        resolved = Path(target).resolve()
        if resolved == root or not resolved.is_relative_to(root):
            continue
        if resolved.is_dir() and not resolved.is_symlink():
            shutil.rmtree(resolved)
            removed.append(str(resolved))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", default="S1R1")
    parser.add_argument(
        "--stop-after-day",
        default=None,
        help="bounded fixture end day (YYYY-MM-DD); omit for the full sealed arm",
    )
    parser.add_argument("--prefix", required=True)
    parser.add_argument(
        "--patches",
        default=None,
        help="comma-separated patch ids; 'none' for the frozen baseline",
    )
    parser.add_argument(
        "--evidence",
        default="full",
        choices=sorted(("full", "decision", "off")),
        help=(
            "evidence level: 'full' reproduces the frozen engine's evidence "
            "behaviour; 'decision'/'off' additionally skip the post-hoc re-proof "
            "of already-written ledger rows"
        ),
    )
    parser.add_argument("--abc-symbols", default=",".join(("Mapping", "MutableMapping")))
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--profile-interval-ms", type=float, default=0.0)
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep-outputs", action="store_true")
    ns = parser.parse_args()

    from src.research_infra.fast_engine import accel

    if ns.patches is None:
        patches = accel.patches_for(evidence=ns.evidence)
    elif ns.patches.strip().lower() in {"none", ""}:
        # The frozen baseline. An evidence level other than 'full' would still
        # change behaviour, so refuse the combination rather than quietly
        # producing a baseline that is not one.
        if ns.evidence != "full":
            parser.error("--patches none requires --evidence full")
        patches = []
    else:
        patches = accel.patches_for(
            evidence=ns.evidence,
            extra=tuple(p.strip() for p in ns.patches.split(",") if p.strip()),
        )

    report = run_window(
        arm=ns.arm,
        stop_after_day=ns.stop_after_day,
        output_prefix=ns.prefix,
        patches=patches,
        evidence=ns.evidence,
        abc_symbols=tuple(s.strip() for s in ns.abc_symbols.split(",") if s.strip()),
        verify=ns.verify,
        profile_interval_ms=ns.profile_interval_ms,
        keep_outputs=ns.keep_outputs,
    )
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in report.items() if k != "economics"}
    if "economics" in report:
        slim["economics_counts"] = report["economics"]["counts"]
        slim["missed_digest"] = report["economics"]["missed_digest"]
    out.write_text(json.dumps(slim, indent=1, default=str))
    if "economics" in report:
        (out.parent / f"{out.stem}_ECONOMICS.json").write_text(
            json.dumps(report["economics"], indent=1, default=str)
        )
    print(
        f"[fast-engine] arm={ns.arm} wall={report['wall_seconds']:.1f}s "
        f"maxrss={report['rusage']['maxrss_bytes'] / 1e9:.2f}GB "
        f"patches={report['patches_applied']} -> {out}",
        file=sys.stderr,
    )
    if report["error"]:
        print(report["error"][-4000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

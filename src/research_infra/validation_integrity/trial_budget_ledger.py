"""Trial-Budget Ledger builder (Validation-Integrity Gauntlet).

Purpose
-------
Ground the Deflated-Sharpe-Ratio (DSR) ``n_trials`` parameter HONESTLY.

The reality-check audit (``AUDIT_VERDICT.md``) found that the 2025-26 forward
window was the *selection surface* for ~101 of 126 evaluations: the same window
used to pick sleeves / confidence dials / configs was then re-used as the
"out-of-sample" gate. When that happens, DSR must be deflated by the FULL number
of strategy configurations that were tried against that window -- not by 1, and
not by the number of edges that survived.

This module scans every ``*RESULT*.json`` in a route directory and produces a
committed, machine-readable ledger that records, per file:

  * filename, mtime (ISO date), size in bytes
  * whether the file *scored against the contaminated forward window*
    (forward / 2025 / 2026 / holdout / validation token present), and
  * any embedded count of candidates / configs / setups / grid cells the file
    evaluated (a per-file LOWER BOUND on the trials that file consumed).

It then writes a summary whose ``recommended_n_trials_for_dsr`` is the max of:
  - ``n_scored_against_forward`` (each forward-scored file == >=1 trial against
    the contaminated window),
  - ``sum_embedded_trial_counts`` (lower bound on configs actually swept), and
  - a hard floor of 128 (>= the number of RESULT files in the route).

Honesty notes (why certain keys are / are not counted as "trials")
------------------------------------------------------------------
DSR's ``n_trials`` is the number of strategy CONFIGURATIONS tried during the
search, NOT the number of trades. In this corpus the bare key ``"n"`` almost
always denotes a *trade / signal sample size* (e.g. ``{"n": 530, "ev": ...}``),
so counting it as a trial would inflate ``n_trials`` by orders of magnitude and
CORRUPT the deflation. We therefore do NOT treat bare ``"n"`` as a trial count.
Likewise ``"n_cells"`` in the sub-period stability audit denotes analysis time
buckets, not search configs, and is excluded. Only keys that genuinely denote a
swept candidate/config population are counted (see ``_CONFIG_COUNT_KEYS`` and
``_CONFIG_LIST_KEYS``). This keeps ``sum_embedded_trial_counts`` an honest LOWER
BOUND rather than an inflated guess.

THE PROSPECTIVE HALF (added 2026-07-29, wave 6, B600)
-----------------------------------------------------
Everything above is RETROSPECTIVE: it reconstructs a lower bound on trials already spent
by scanning artifacts that survived. That was the only thing available when it was
written, and it has a floor it cannot get under — a variant that was evaluated and not
written to a ``*RESULT*.json`` is invisible to it, and in a repair campaign most variants
are exactly that (a sweep cell, a re-walk, a parameter neighbourhood).

``WAVE_6_WORKING_AGREEMENT.md`` §3 makes logging every evaluated variant mandatory, so
this module grows the other half: ``TrialLedger``, an append-only JSONL that sessions
write to AS THEY EVALUATE, and ``measured_n_trials`` which combines the two sources.
``gate.py:47-48`` says the DSR currently deflates "on a number nobody measured"; this is
the artifact that replaces it.

**It is not a brake.** Nothing here forbids, gates, throttles, or waits. It records. The
difference it buys is between *"we tried 400 things and the survivor still clears
deflation"* and *"we tried 400 things and reported the best one"* — and the second is how
this programme admitted a candidate book that failed its own placebo at p = 0.59.

Concurrency: several sessions run at once in separate worktrees and may share a ledger
path. Rows are appended with ``O_APPEND`` one line at a time, which POSIX makes atomic
for writes under ``PIPE_BUF``; a row is ~300 bytes. No locking, no read-modify-write, so
a crashed session loses at most its own last line and can never corrupt another's.

Public API
----------
    build_trial_budget_ledger(route_dir, out_path, *, dsr_floor=128,
                              summary_path=None) -> dict     # retrospective scan
    TrialLedger(path).record(...) / .rows() / .summary()      # prospective log
    measured_n_trials(ledger_paths=..., scan_summary=...)     # what DSR should use
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "build_trial_budget_ledger",
    "scan_result_file",
    "DSR_TRIAL_FLOOR",
    "TrialLedger",
    "TrialRow",
    "measured_n_trials",
    "variant_hash",
]

# Floor on DSR n_trials. >= the number of RESULT files in the route (~128).
DSR_TRIAL_FLOOR = 128

# --- forward-window contamination tokens ---------------------------------
# Presence of any of these (in a JSON key, a string value, or the raw text)
# marks a file as having scored against the contaminated 2025-26 forward
# window. Matched case-insensitively as substrings.
_FORWARD_TOKENS: Tuple[str, ...] = (
    "forward",
    "fwd",
    "2025",
    "2026",
    "holdout",
    "hold_out",
    "validation",
    "mc_forward",
    "mean_fwd",
    "y2025",
    "y2026",
    "oos",
    "out_of_sample",
    "out-of-sample",
)
_FORWARD_RE = re.compile("|".join(re.escape(t) for t in _FORWARD_TOKENS), re.IGNORECASE)

# --- embedded trial-count signals ----------------------------------------
# Keys whose INTEGER value is a genuine count of configs/candidates/trials
# swept during a search. Deliberately EXCLUDES bare "n" (trade sample size)
# and "n_cells" (analysis time buckets). See module docstring.
_CONFIG_COUNT_KEYS: Tuple[str, ...] = (
    "n_candidates",
    "n_trials",
    "n_setups",
    "n_configs",
    "n_cfgs",
    "n_combos",
    "n_combinations",
    "n_variants",
    "n_grid",
    "n_grids",
    "n_grid_points",
    "n_param_sets",
    "n_params",
    "n_sweep",
    "n_evals",
    "n_evaluated",
    "grid_size",
    "num_candidates",
    "num_configs",
    "num_trials",
    "num_setups",
    "total_configs",
    "total_candidates",
)

# Keys whose value is a COLLECTION of candidates/configs (use len), or, for a
# dict-of-lists describing a parameter grid, the product of the list lengths.
_CONFIG_LIST_KEYS: Tuple[str, ...] = (
    "candidates",
    "trials",
    "setups",
    "configs",
    "grid",
    "candidate_ledger",
    "candidate_list",
    "variants",
    "param_grid",
)


def _iso_date(epoch: float) -> str:
    """File mtime epoch -> ISO date (UTC, YYYY-MM-DD)."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")


def _grid_dict_size(d: dict) -> int:
    """Estimate config count of a dict-of-lists parameter grid as the product
    of the per-axis list lengths. Returns 0 if it is not a clean grid spec."""
    if not d:
        return 0
    prod = 1
    saw_list = False
    for v in d.values():
        if isinstance(v, list) and v:
            prod *= len(v)
            saw_list = True
        else:
            # not a pure axis-of-values grid; bail out conservatively
            return 0
    return prod if saw_list else 0


def _candidate_count_from_value(key: str, value: Any) -> int:
    """Best-effort trial count contributed by a single (key, value) pair."""
    kl = key.lower()
    # explicit integer config-count keys
    if kl in _CONFIG_COUNT_KEYS and isinstance(value, bool) is False and isinstance(value, int):
        return int(value) if value >= 0 else 0
    if kl in _CONFIG_COUNT_KEYS and isinstance(value, float) and float(value).is_integer():
        return int(value) if value >= 0 else 0
    # collection-valued candidate keys
    if kl in _CONFIG_LIST_KEYS:
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            return _grid_dict_size(value)
        if isinstance(value, bool) is False and isinstance(value, int) and value >= 0:
            return int(value)
    return 0


def _walk(obj: Any) -> Tuple[bool, set, int, Optional[str]]:
    """Recursively walk a parsed JSON object.

    Returns (forward_hit, matched_tokens, max_trial_count, trial_source_key).
    ``max_trial_count`` is the per-file MAX over every detected config-count
    signal -- a conservative lower bound that avoids double-counting the same
    grid size repeated across nested train/forward sub-dicts.
    """
    forward_hit = False
    tokens: set = set()
    best_count = 0
    best_src: Optional[str] = None

    def _note_tokens(text: str) -> None:
        nonlocal forward_hit
        for m in _FORWARD_RE.finditer(text):
            forward_hit = True
            tokens.add(m.group(0).lower())

    stack: List[Any] = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if isinstance(k, str):
                    _note_tokens(k)
                    cnt = _candidate_count_from_value(k, v)
                    if cnt > best_count:
                        best_count = cnt
                        best_src = k
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, str):
            _note_tokens(cur)
        # ints/floats: years would only matter as values of forward-ish keys,
        # which are already captured via the key name; skip numeric scanning to
        # avoid false-positive substring hits inside unrelated magnitudes.
    return forward_hit, tokens, best_count, best_src


def scan_result_file(path: str) -> Dict[str, Any]:
    """Scan a single RESULT json file and return its ledger row dict."""
    p = Path(path)
    st = p.stat()
    row: Dict[str, Any] = {
        "filename": p.name,
        "relpath": str(p),
        "mtime_iso": _iso_date(st.st_mtime),
        "size_bytes": int(st.st_size),
        "parseable": True,
        "parse_error": None,
        "scored_against_forward": False,
        "forward_tokens": [],
        "embedded_trial_count": 0,
        "trial_count_source": None,
    }

    raw = ""
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover - unreadable file
        row["parseable"] = False
        row["parse_error"] = f"read_error: {exc}"
        return row

    try:
        data = json.loads(raw)
    except Exception as exc:
        # Tolerate large/odd/unparseable files: still detect forward tokens
        # from the raw text so contamination is not silently dropped.
        row["parseable"] = False
        row["parse_error"] = f"json_error: {type(exc).__name__}: {exc}"
        fwd = bool(_FORWARD_RE.search(raw))
        row["scored_against_forward"] = fwd
        if fwd:
            row["forward_tokens"] = sorted(
                {m.group(0).lower() for m in _FORWARD_RE.finditer(raw)}
            )
        return row

    fwd, tokens, count, src = _walk(data)
    row["scored_against_forward"] = bool(fwd)
    row["forward_tokens"] = sorted(tokens)
    row["embedded_trial_count"] = int(count)
    row["trial_count_source"] = src
    return row


def _find_result_files(route_dir: str) -> List[Path]:
    """All *RESULT*.json under route_dir (recursive), sorted, deterministic."""
    root = Path(route_dir)
    files = [
        p
        for p in root.rglob("*.json")
        if "RESULT" in p.name and p.is_file()
    ]
    return sorted(files, key=lambda p: str(p).lower())


def build_trial_budget_ledger(
    route_dir: str,
    out_path: str,
    *,
    dsr_floor: int = DSR_TRIAL_FLOOR,
    summary_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the committed Trial-Budget Ledger.

    Scans every ``*RESULT*.json`` under ``route_dir``, writes one JSONL row per
    file to ``out_path`` (NO top-N truncation -- every file is listed), writes a
    summary JSON next to it (or to ``summary_path``), and returns the summary
    dict.

    Parameters
    ----------
    route_dir : str
        Route directory to scan recursively for ``*RESULT*.json``.
    out_path : str
        Destination for the JSONL ledger (one line per RESULT file).
    dsr_floor : int, keyword-only, default 128
        Hard floor for ``recommended_n_trials_for_dsr``.
    summary_path : str, optional
        Destination for the summary JSON. Defaults to ``TRIAL_BUDGET_SUMMARY.json``
        in the same directory as ``out_path``.

    Returns
    -------
    dict
        The summary (also written to ``summary_path``).
    """
    files = _find_result_files(route_dir)

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    if summary_path is None:
        summary_p = out_p.parent / "TRIAL_BUDGET_SUMMARY.json"
    else:
        summary_p = Path(summary_path)
    summary_p.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    n_forward = 0
    n_unparseable = 0
    sum_embedded = 0
    for fp in files:
        row = scan_result_file(str(fp))
        rows.append(row)
        if row["scored_against_forward"]:
            n_forward += 1
        if not row["parseable"]:
            n_unparseable += 1
        sum_embedded += int(row["embedded_trial_count"])

    total = len(rows)
    recommended = max(int(n_forward), int(sum_embedded), int(dsr_floor))

    # write JSONL (ALL files, deterministic order, no truncation)
    with out_p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary: Dict[str, Any] = {
        "schema": "gtos.validation_integrity.trial_budget_ledger.v1",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "route_dir": str(Path(route_dir)),
        "ledger_path": str(out_p),
        "summary_path": str(summary_p),
        "total_result_files": total,
        "n_scored_against_forward": int(n_forward),
        "n_unparseable": int(n_unparseable),
        "sum_embedded_trial_counts": int(sum_embedded),
        "dsr_floor": int(dsr_floor),
        "recommended_n_trials_for_dsr": int(recommended),
        "recommended_n_trials_basis": (
            "max(n_scored_against_forward, sum_embedded_trial_counts, dsr_floor)"
        ),
        "method_notes": (
            "Each forward-scored RESULT file is >=1 strategy configuration tried "
            "against the contaminated 2025-26 selection window. "
            "sum_embedded_trial_counts is a LOWER BOUND: per file we take the MAX "
            "config-count signal (n_configs / grid_size / candidate-list len / "
            "param-grid product), excluding bare 'n' (trade sample size) and "
            "'n_cells' (analysis time buckets), which are NOT search trials. "
            "Use recommended_n_trials_for_dsr as the DSR n_trials so the deflation "
            "reflects the true search effort, not the number of survivors."
        ),
    }

    with summary_p.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")

    return summary


# =========================================================================
# The prospective ledger. See the module docstring, "THE PROSPECTIVE HALF".
# =========================================================================

TRIAL_LEDGER_SCHEMA = "gtos.validation_integrity.trial_ledger_row.v1"

#: The default shared artifact. One file, append-only, committed.
DEFAULT_TRIAL_LEDGER = "research/operations/trial_budget/TRIAL_LEDGER.jsonl"

#: Outcomes a row may carry. `evaluated` is the honest default for a swept cell that
#: produced a number nobody acted on -- which is the majority of a repair campaign and
#: exactly the population the retrospective scan cannot see.
_OUTCOMES = ("evaluated", "admitted", "rejected", "not_evaluable", "abandoned", "error")


def variant_hash(payload: Any) -> str:
    """Stable short hash of a variant's parameters.

    Sorted-key JSON so the same variant hashes the same across sessions and machines;
    12 hex chars, which at campaign scale (10^3 variants) has a collision probability
    around 10^-9 and keeps the ledger readable.
    """
    blob = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


class TrialRow(Dict[str, Any]):
    """A ledger row. A dict subclass so it serialises without a codec."""


class TrialLedger:
    """Append-only trial log.

    >>> led = TrialLedger("/tmp/x/TRIAL_LEDGER.jsonl", session="AA")
    >>> _ = led.record(mechanism="donchian_20", sleeve="mx_btcusd_d1_donchian_20_breakout",
    ...                variant={"stop_atr": 1.5}, window="1992-2026", outcome="evaluated")
    >>> led.summary()["n_trials"]
    1

    Nothing here can fail a caller's run: a write error is swallowed and counted, because
    a ledger that raises would become a brake, and §3 of the wave-6 agreement is explicit
    that it must not be one. `write_errors` in the summary makes any loss visible.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        session: str = "",
        run_id: str = "",
        autocreate: bool = True,
    ) -> None:
        self.path = Path(path)
        self.session = session
        self.run_id = run_id or datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.n_written = 0
        self.write_errors = 0
        if autocreate:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    # -- writing -----------------------------------------------------------
    def record(
        self,
        *,
        mechanism: str,
        sleeve: str = "",
        variant: Any = None,
        window: str = "",
        outcome: str = "evaluated",
        metric: Optional[float] = None,
        metric_name: str = "",
        spec_sha256: str = "",
        note: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> TrialRow:
        """Log one evaluated variant. Returns the row (also appended to the file)."""
        if outcome not in _OUTCOMES:
            outcome = "evaluated"
        row = TrialRow(
            schema=TRIAL_LEDGER_SCHEMA,
            ts=datetime.now(tz=timezone.utc).isoformat(),
            session=self.session,
            run_id=self.run_id,
            mechanism=str(mechanism),
            sleeve=str(sleeve),
            variant=variant if variant is not None else {},
            variant_hash=variant_hash({"mechanism": mechanism, "sleeve": sleeve,
                                       "variant": variant, "window": window}),
            window=str(window),
            outcome=outcome,
            metric=(float(metric) if metric is not None else None),
            metric_name=str(metric_name),
            spec_sha256=str(spec_sha256),
            note=str(note),
        )
        if extra:
            row["extra"] = extra
        self._append(row)
        return row

    def record_many(self, rows: Iterable[Dict[str, Any]]) -> int:
        n = 0
        for r in rows:
            self.record(**r)
            n += 1
        return n

    def _append(self, row: Dict[str, Any]) -> None:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        try:
            # O_APPEND + one write per row: POSIX-atomic under PIPE_BUF, so concurrent
            # sessions sharing a ledger cannot interleave a line.
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                os.write(fd, line.encode("utf-8"))
            finally:
                os.close(fd)
            self.n_written += 1
        except OSError:
            # Never raise into a caller's measurement. See the class docstring.
            self.write_errors += 1

    # -- reading -----------------------------------------------------------
    def rows(self) -> List[Dict[str, Any]]:
        if not self.path.is_file():
            return []
        out: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    # A torn line from a killed process is dropped, and counted below.
                    out.append({"_unparseable": line[:200]})
        return out

    def summary(self) -> Dict[str, Any]:
        rows = self.rows()
        good = [r for r in rows if "_unparseable" not in r]
        by_mech: Dict[str, int] = {}
        by_sess: Dict[str, int] = {}
        by_outcome: Dict[str, int] = {}
        distinct = set()
        for r in good:
            by_mech[r.get("mechanism", "")] = by_mech.get(r.get("mechanism", ""), 0) + 1
            by_sess[r.get("session", "")] = by_sess.get(r.get("session", ""), 0) + 1
            by_outcome[r.get("outcome", "")] = by_outcome.get(r.get("outcome", ""), 0) + 1
            distinct.add(r.get("variant_hash", ""))
        return {
            "schema": "gtos.validation_integrity.trial_ledger_summary.v1",
            "path": str(self.path),
            "n_trials": len(good),
            "n_distinct_variants": len(distinct),
            "n_unparseable_rows": len(rows) - len(good),
            "by_mechanism": dict(sorted(by_mech.items())),
            "by_session": dict(sorted(by_sess.items())),
            "by_outcome": dict(sorted(by_outcome.items())),
            "written_this_process": self.n_written,
            "write_errors_this_process": self.write_errors,
            "note": (
                "n_trials counts LOOK EVENTS, not distinct hypotheses. A second look at "
                "the same variant is a second chance to be wrong about it, which is the "
                "quantity DSR deflation needs. n_distinct_variants is reported beside it "
                "so the two are never confused."
            ),
        }


def measured_n_trials(
    *,
    ledger_paths: Sequence[str | Path] = (),
    scan_summary: Optional[Dict[str, Any]] = None,
    floor: int = DSR_TRIAL_FLOOR,
) -> Dict[str, Any]:
    """The n_trials DSR should use, and where each component came from.

    ``max(prospective look events, retrospective lower bound, floor)``. The floor stays
    because the retrospective scan is a lower bound and the prospective ledger only
    starts counting from the day it was wired — dropping it would let a fresh ledger with
    three rows deflate less than the estate's actual history warrants.
    """
    n_prospective = 0
    per_ledger: Dict[str, int] = {}
    for p in ledger_paths:
        led = TrialLedger(p, autocreate=False)
        n = led.summary()["n_trials"]
        per_ledger[str(p)] = n
        n_prospective += n
    n_retro = int((scan_summary or {}).get("recommended_n_trials_for_dsr", 0) or 0)
    chosen = max(int(n_prospective), n_retro, int(floor))
    basis = (
        "prospective_ledger" if chosen == n_prospective and n_prospective >= max(n_retro, floor)
        else ("retrospective_scan" if chosen == n_retro and n_retro >= floor else "floor")
    )
    return {
        "n_trials": chosen,
        "basis": basis,
        "n_prospective_look_events": int(n_prospective),
        "per_ledger": per_ledger,
        "n_retrospective_lower_bound": n_retro,
        "floor": int(floor),
        "note": (
            "max(prospective, retrospective, floor). The floor survives because the scan "
            "is a lower bound and the prospective ledger only counts from the day it was "
            "wired (2026-07-29, wave 6)."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description="Build the Trial-Budget Ledger.")
    ap.add_argument("route_dir")
    ap.add_argument("out_path")
    ap.add_argument("--dsr-floor", type=int, default=DSR_TRIAL_FLOOR)
    ap.add_argument("--summary-path", default=None)
    args = ap.parse_args()
    s = build_trial_budget_ledger(
        args.route_dir,
        args.out_path,
        dsr_floor=args.dsr_floor,
        summary_path=args.summary_path,
    )
    print(json.dumps(s, indent=2, sort_keys=True))

"""The trial-budget appender — the spine of `WAVE_6_WORKING_AGREEMENT.md` section 3.

WHY THIS EXISTS WHEN `trial_budget_ledger.py` ALREADY DOES
-----------------------------------------------------------
`validation_integrity/trial_budget_ledger.py` is a **retrospective scanner**: it walks a
route directory for `*RESULT*.json` and infers a trial count from what those files happen
to have recorded. That is the right instrument for auditing work already done, and it
cannot see a variant a live session evaluates and does not write down. A repair campaign
evaluates hundreds of variants that never become a RESULT file each — sweep points,
re-walks, neighborhood cells — and those are exactly the trials the deflation needs.

So this module is the *write* half the scanner never had: an append-only JSONL the
session writes one row to per variant, plus `write_summary`, which emits a file the
existing scanner reads without modification (`n_trials` is already in its
`_CONFIG_COUNT_KEYS`). Nothing in `trial_budget_ledger.py` is edited — Session AA owns
that module this wave, and two sessions editing one instrument is a failure mode this
programme has already paid for (`WAVE_6_WORKING_AGREEMENT.md` section 4, item 3).

WHAT COUNTS AS A TRIAL
-----------------------
One evaluation of one strategy configuration against data used for a published claim.
A sweep of 5 stop widths x 4 targets is 20 trials, not 1. Re-walking the same
configuration on a different era is a **new** trial, because it is a new opportunity to
report the better of the two. Building a frame, computing a distribution, or counting
bars is **not** a trial — nothing is selected on it.

Deliberately generous at the margin: over-counting deflates a survivor's statistics and
under-counting inflates them, and only one of those errors can put money on a rule that
is not there.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

__all__ = ["TrialLedger", "TrialRow"]

SCHEMA = "gtos.wave6.trial_budget_appender.v1"


@dataclass
class TrialRow:
    family: str
    sleeve: str
    variant_id: str
    params: dict[str, Any]
    #: What the variant scored — free-form, but always include the number that could be
    #: selected on, because a trial nobody could have selected on is not a trial.
    metrics: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def to_json(self, session: str, seq: int) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "session": session,
            "seq": seq,
            "logged_utc": datetime.now(tz=timezone.utc).isoformat(),
            "family": self.family,
            "sleeve": self.sleeve,
            "variant_id": self.variant_id,
            "params": self.params,
            "metrics": self.metrics,
            "note": self.note,
        }


class TrialLedger:
    """Append-only variant log for one session.

    Usage is deliberately trivial so that logging is never the reason a sweep is skipped::

        led = TrialLedger(path, session="AB")
        for k in grid:
            r = evaluate(k)
            led.log("xvol_neighborhood", "sub_xvol_pullback", variant_id(k), k,
                    {"n": r.n, "mean_r": r.mean})
        led.write_summary(summary_path)
    """

    def __init__(self, path: str | os.PathLike, *, session: str,
                 append: bool = False) -> None:
        self.path = Path(path)
        self.session = session
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._n = 0
        self._families: dict[str, int] = {}
        self._sleeves: dict[str, int] = {}
        if not append and self.path.exists():
            self.path.unlink()
        elif append and self.path.exists():
            with self.path.open() as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    self._n += 1
                    row = json.loads(line)
                    self._families[row.get("family", "?")] = (
                        self._families.get(row.get("family", "?"), 0) + 1)
                    self._sleeves[row.get("sleeve", "?")] = (
                        self._sleeves.get(row.get("sleeve", "?"), 0) + 1)
        self._fh = self.path.open("a", encoding="utf-8")

    def log(self, family: str, sleeve: str, variant_id: str,
            params: dict[str, Any], metrics: Optional[dict[str, Any]] = None,
            note: str = "") -> int:
        self._n += 1
        row = TrialRow(family, sleeve, variant_id, dict(params),
                       dict(metrics or {}), note)
        self._fh.write(json.dumps(row.to_json(self.session, self._n),
                                  ensure_ascii=False, sort_keys=True) + "\n")
        self._fh.flush()
        self._families[family] = self._families.get(family, 0) + 1
        self._sleeves[sleeve] = self._sleeves.get(sleeve, 0) + 1
        return self._n

    def log_many(self, family: str, sleeve: str,
                 rows: Iterable[tuple[str, dict, dict]]) -> int:
        for vid, params, metrics in rows:
            self.log(family, sleeve, vid, params, metrics)
        return self._n

    @property
    def n_trials(self) -> int:
        return self._n

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()

    def write_summary(self, out_path: str | os.PathLike, *,
                      extra: Optional[dict] = None) -> dict[str, Any]:
        """Emit a `*RESULT*.json` the existing scanner counts without modification.

        `n_trials` is one of `trial_budget_ledger._CONFIG_COUNT_KEYS`, so
        `build_trial_budget_ledger(<this dir>, ...)` folds this session's measured count
        into `recommended_n_trials_for_dsr` with no change to that module.
        """
        s: dict[str, Any] = {
            "schema": SCHEMA + ".summary",
            "session": self.session,
            "ledger_path": str(self.path),
            "n_trials": self._n,
            "n_variants": self._n,
            "trials_by_family": dict(sorted(self._families.items())),
            "trials_by_sleeve": dict(sorted(self._sleeves.items())),
            "counting_rule": (
                "One row per (configuration, evaluation) pair that could have been "
                "selected on. Frame builds, distribution summaries and bar counts are "
                "not trials. Re-walking one configuration on a second era counts twice."),
            "why_this_matters": (
                "gate.py:47-48 deflates DSR against an assumed floor of 128 it calls "
                "'a number nobody measured'. This is the measurement, for this session."),
        }
        if extra:
            s.update(extra)
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            json.dump(s, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        return s

    def __enter__(self) -> "TrialLedger":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

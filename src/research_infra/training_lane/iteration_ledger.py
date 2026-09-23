"""CC-2 — the iteration ledger: every train/val look, logged, append-only, and UNBILLED.

THE INVARIANT THIS FILE EXISTS FOR
-----------------------------------
**The family ratchet moves only on graduation events, and a reader can always separate
exploration looks from billed looks.** Everything below is in service of that sentence.

    exploration look  ->  a row HERE. `billed: false`, always, structurally.
    billed look       ->  a member row in a CANDIDATE_FAMILY declaration, written by
                          `graduation.graduate()` and by nothing else.

Two artifacts, two vocabularies, no overlap. A reader who wants "how hard did we search"
counts rows here; a reader who wants "what does the multiplicity correction cost" reads the
declaration. Neither number can contaminate the other, because neither file can produce the
other's.

SIBLING LEDGER, NOT A `surface` FIELD ON THE TRIAL LEDGER — AND WHY
-------------------------------------------------------------------
The commission left the mechanics open. A `surface` field on
`validation_integrity.trial_budget_ledger.TrialLedger` would have been less code. It is the
wrong answer for one measurable reason: `measured_n_trials()` is
`max(prospective look events, retrospective lower bound, floor)` and feeds the **DSR
deflation**. Every lane iteration written into that ledger raises the estate's DSR bill. That
is billing leaking backward into exploration — the exact defect
`TRAINING_LANE_RATIFICATION.md` section 1.2 names, where AW paid a 486-look family bill for
what was research triage. A field cannot fix it, because `measured_n_trials` would have to
learn to *subtract*, and a bill you can subtract from is not a ratchet.

The obvious objection: a sibling ledger is a cheap place to hide a real look. It is not,
because **you cannot graduate without having logged here** — `graduate()` reads its provenance
out of this file and refuses a candidate with none. The sibling is a prerequisite for billing,
not an alternative to it.

The two ledgers stay wired to each other in the one direction that is safe: `summary()`
reports the trial-ledger figure beside its own so a reader never has to guess which bill a
number came from.

THE THREE THINGS A CALLER CANNOT FORGE
--------------------------------------
1. **The surface stamp.** `record()` takes DATES and classifies them through
   `trainer_partitions.DEFAULT_SURFACE_MAP` itself. A caller cannot pass `surface="TRAIN"` for
   a span that touches March.
2. **The verdict vocabulary.** `admitted` and `rejected` are NOT in it. Those are the sealed
   gate's words and a TRAIN/VAL look cannot produce them; attempting one raises. An
   exploration look that reports an admission is the honesty failure this lane was ratified to
   end, and it is cheaper to refuse the word than to audit the prose later.
3. **`billed`.** The field is written `false` by this module and is not a parameter.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..trainer_partitions import DEFAULT_SURFACE_MAP, SurfaceMap, as_date
from .append_only import append_row, read_rows

__all__ = [
    "DEFAULT_ITERATION_LEDGER",
    "ITERATION_LEDGER_SCHEMA",
    "ITERATION_VERDICTS",
    "IterationLedger",
    "IterationLedgerRefusal",
    "candidate_id",
    "spec_digest",
]

ITERATION_LEDGER_SCHEMA = "gtos.training_lane.iteration_row.v1"

REPO = Path(__file__).resolve().parents[3]
#: Under `docs/` rather than `research/operations/`, which sparse checkout excludes — an
#: artifact there can be committed, absent from a working tree, and leave `git status` clean
#: (WAVE_8 section 4, "sparse-checkout lies"). Same reason `candidate_family.DECLARATION_V1`
#: lives where it does.
DEFAULT_ITERATION_LEDGER = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
    / "TRAINING_LANE_ITERATION_LEDGER.jsonl"
)

#: What a TRAIN/VAL look may conclude.
#:
#: `admitted` and `rejected` are deliberately ABSENT. They are the sealed gate's verdicts and
#: the gate consumes TEST, not TRAIN/VAL; a look that reports one has either mislabelled itself
#: or has run the gate without billing it. Both are refused here rather than discovered in a
#: result doc three weeks later.
ITERATION_VERDICTS = (
    "evaluated",        # a number came out; nobody acted on it. The honest majority.
    "improved",         # better than the incumbent variant on this surface
    "regressed",        # worse
    "no_change",        # measurably identical — worth logging, it closes a hypothesis
    "not_evaluable",    # no trades / no null / resolution floor
    "abandoned",        # stopped before a number existed
    "error",
)

#: Verdicts that belong to the sealed gate. Named so the refusal can say what to do instead.
_GATE_VERDICTS = ("admitted", "admit", "rejected", "reject", "graduated")


class IterationLedgerRefusal(RuntimeError):
    """A look was refused. The ledger never *fails* a measurement; it refuses to RECORD one
    that would be a lie about which surface it touched."""


def spec_digest(spec: Any) -> str:
    """Stable sha256 over a variant/spec payload. Sorted keys so two sessions on two machines
    hash the same object identically."""
    if isinstance(spec, str) and len(spec) == 64:
        try:
            int(spec, 16)
            return spec  # already a digest; do not re-hash it
        except ValueError:
            pass
    blob = json.dumps(spec, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def candidate_id(*, mechanism: str, sleeve: str, spec: Any, surface_stamp_digest: str = "") -> str:
    """The key `graduate()` joins provenance on.

    It includes the SURFACE STAMP DIGEST when one is given, on purpose: the same spec evaluated
    over a different window is a different hypothesis and must bill separately. Omitting it
    yields the mechanism-level id a session uses while iterating, before a window is fixed.
    """
    payload = {"mechanism": mechanism, "sleeve": sleeve, "spec": spec_digest(spec)}
    if surface_stamp_digest:
        payload["surface"] = surface_stamp_digest
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


class IterationLedger:
    """Append-only log of TRAIN/VAL looks. Bills nothing, ever.

    >>> led = IterationLedger("/tmp/x/ITER.jsonl", session="CC")
    >>> row = led.record(mechanism="donchian_20", sleeve="mx_btcusd",
    ...                  spec={"target_r": 5.0}, start="2026-01-01", end="2026-01-31",
    ...                  engine_version="train-engine-v0", verdict="evaluated")
    >>> row["surface"], row["billed"]
    ('VAL', False)
    """

    def __init__(
        self,
        path: str | Path = DEFAULT_ITERATION_LEDGER,
        *,
        session: str = "",
        run_id: str = "",
        surfaces: SurfaceMap | None = None,
        now_utc: str = "",
    ) -> None:
        self.path = Path(path)
        self.session = session
        self.surfaces = surfaces if surfaces is not None else DEFAULT_SURFACE_MAP
        self._now = now_utc
        self.run_id = run_id or self._timestamp().replace("-", "").replace(":", "")[:15] + "Z"
        self.n_written = 0

    def _timestamp(self) -> str:
        return self._now or dt.datetime.now(tz=dt.timezone.utc).isoformat()

    # -- writing ---------------------------------------------------------------------------
    def record(
        self,
        *,
        mechanism: str,
        spec: Any,
        engine_version: str,
        sleeve: str = "",
        start: Any = None,
        end: Any = None,
        days: Iterable[Any] | None = None,
        verdict: str = "evaluated",
        metric: float | None = None,
        metric_name: str = "",
        note: str = "",
        receipt: str = "",
        acknowledge_uncovered: Sequence[str] = (),
        engine_reserved_blackout: Sequence[Sequence[str]] = (),
        extra: dict | None = None,
        strict: bool = True,
    ) -> dict:
        """Log one look. Returns the row that was appended.

        Either `(start, end)` or `days` must be given — the ledger classifies the surface from
        the dates rather than trusting a caller's label, so a look with no dates has no
        stampable surface and is refused.

        `engine_reserved_blackout` is how a full-history walk declares what its own engine
        already drops. The estate's gate walks span `GateSpec.global_span` =
        1992-02-18..2026-07-27, which CONTAINS March 2026 — and they do not consume it:
        `panel.py:249` drops every trade whose label span touches a blackout range before
        pricing, and `folds.py:125` pushes fold boundaries out of one. Spanning is not
        consuming, so a span-based stamp that ignored the engine's blackout would refuse the
        estate's own standard walk for a leak that did not happen.

        This is NOT a bypass, because the declared ranges are checked both ways: they must
        COVER every blackout day inside the span (an engine with a narrower blackout than the
        lane's is a real divergence and is refused), and they must contain nothing BUT
        blackout days (excluding an inconvenient window is a filter, not a blackout). The
        TEST surface proper — the live forward stream — has no such parameter and never will:
        no engine setting makes a live day un-consumed.

        `acknowledge_uncovered` is the one loosening this module allows, and it must NAME the
        gaps it crosses (e.g. `("gap_2026H1_tail_pre_arming",)`). The estate's standard
        full-history gate walk spans `GateSpec.global_span` = 1992-02-18..2026-07-27 and
        therefore crosses the one declared gap by default; refusing it outright would make this
        ledger unusable for the estate's own walk while protecting nothing (the gap is measured
        already-consumed, not virgin). Requiring the gap to be named keeps it from happening by
        accident and puts the acknowledgement in the row where a reader sees it — the same
        shape as `candidate_family.Member.look_taken` requiring `no_look_evidence`.

        TEST has no such escape hatch and never will.
        """
        if verdict in _GATE_VERDICTS:
            raise IterationLedgerRefusal(
                f"verdict {verdict!r} belongs to the sealed gate, not to a TRAIN/VAL look. The "
                f"lane logs exploration; admission happens at graduation, through "
                f"`training_lane.graduation.graduate()`, which bills one look to the family "
                f"ratchet. Use one of {ITERATION_VERDICTS} to record what the look measured."
            )
        if verdict not in ITERATION_VERDICTS:
            raise IterationLedgerRefusal(
                f"unknown verdict {verdict!r}; expected one of {ITERATION_VERDICTS}"
            )

        if days is not None:
            day_list = [as_date(d) for d in days]
            if not day_list:
                raise IterationLedgerRefusal("`days` is empty; a look with no dates has no surface")
            span = [min(day_list).isoformat(), max(day_list).isoformat()]
        elif start is not None and end is not None:
            day_list = self.surfaces._days(start, end)
            span = [as_date(start).isoformat(), as_date(end).isoformat()]
        else:
            raise IterationLedgerRefusal(
                "a look must carry its dates: pass `start`/`end` or `days`. The surface stamp "
                "is computed from them, never accepted from the caller."
            )

        dropped = self._engine_blackout_days(engine_reserved_blackout, day_list, span)
        if dropped:
            day_list = [d for d in day_list if d not in dropped]
            if not day_list:
                raise IterationLedgerRefusal(
                    f"every day in {span[0]}..{span[1]} is inside the engine's reserved "
                    f"blackout; there is no look here to record."
                )
        stamp = self.surfaces.classify_days(day_list, span=(span[0], span[1]))

        if stamp["test_days"]:
            shown = ", ".join(stamp["test_days"][:5])
            raise IterationLedgerRefusal(
                f"look on {span[0]}..{span[1]} touches {len(stamp['test_days'])} TEST day(s) "
                f"({shown}{'...' if len(stamp['test_days']) > 5 else ''}). TEST is March 2026, "
                f"every blackout, and the live forward stream from 2026-07-29 — consumed by the "
                f"sealed gate and by live monitoring, never by the lane. Bound the window and "
                f"look again."
            )

        acked = tuple(sorted(set(acknowledge_uncovered)))
        if stamp["uncovered_days"] and not acked:
            gaps = sorted({
                (self.surfaces.surface_for_day(d).band_id or "").split(":", 1)[-1]
                for d in stamp["uncovered_days"]
            })
            raise IterationLedgerRefusal(
                f"look on {span[0]}..{span[1]} crosses {len(stamp['uncovered_days'])} day(s) "
                f"covered by no declared surface (gaps: {gaps}). Uncovered is refused by "
                f"default. If the crossing is intended — the estate's standard full-history "
                f"walk crosses `gap_2026H1_tail_pre_arming` by construction — pass "
                f"`acknowledge_uncovered={tuple(gaps)}` so the acknowledgement lands in the row."
            )

        sid = candidate_id(mechanism=mechanism, sleeve=sleeve, spec=spec)
        sid_windowed = candidate_id(
            mechanism=mechanism, sleeve=sleeve, spec=spec,
            surface_stamp_digest=_stamp_digest(stamp),
        )
        row = {
            "schema": ITERATION_LEDGER_SCHEMA,
            "ts": self._timestamp(),
            "session": self.session,
            "run_id": self.run_id,
            # The invariant, written into the data rather than asserted about it.
            "billed": False,
            "billing_note": "iteration is unbilled; the family ratchet moves only at graduation",
            "mechanism": str(mechanism),
            "sleeve": str(sleeve),
            "candidate_id": sid,
            "candidate_id_windowed": sid_windowed,
            "spec_digest": spec_digest(spec),
            "spec": spec if not isinstance(spec, (bytes, bytearray)) else None,
            "engine_version": str(engine_version),
            "date_span": span,
            "surface": stamp["dominant_surface"],
            "surface_stamp": stamp,
            "disclosures": stamp["disclosures"],
            "acknowledged_gaps": list(acked),
            "verdict": verdict,
            "metric": (float(metric) if metric is not None else None),
            "metric_name": str(metric_name),
            "note": str(note),
            "receipt": str(receipt),
            "engine_reserved_blackout": [list(r) for r in engine_reserved_blackout],
            "blackout_days_excluded": len(dropped),
        }
        if extra:
            row["extra"] = extra
        if append_row(self.path, row, strict=strict):
            self.n_written += 1
        return row

    def _engine_blackout_days(
        self,
        declared: Sequence[Sequence[str]],
        day_list: Sequence[dt.date],
        span: Sequence[str],
    ) -> set[dt.date]:
        """The days the caller's engine drops, validated BOTH ways. See `record`'s docstring.

        Returns the set to subtract. Refuses a declaration that is narrower than the lane's
        blackout (a real divergence) or wider than it (a filter wearing a blackout's name).
        """
        if not declared:
            return set()
        covered: set[dt.date] = set()
        for rng in declared:
            if len(tuple(rng)) != 2:
                raise IterationLedgerRefusal(
                    f"engine_reserved_blackout entry {rng!r} is not a (start, end) pair"
                )
            lo, hi = as_date(rng[0]), as_date(rng[1])
            if hi < lo:
                raise IterationLedgerRefusal(f"engine_reserved_blackout range reversed: {rng!r}")
            covered |= {lo + dt.timedelta(days=k) for k in range((hi - lo).days + 1)}

        in_span = set(day_list)
        lane_blackout = {d for d in in_span if self.surfaces.blackout_hit(d) is not None}

        missed = sorted(d.isoformat() for d in (lane_blackout - covered))
        if missed:
            raise IterationLedgerRefusal(
                f"engine_reserved_blackout does not cover {len(missed)} lane-blackout day(s) "
                f"inside {span[0]}..{span[1]} (e.g. {missed[:5]}). The engine's blackout is "
                f"NARROWER than the lane's, which means one of the two lanes has stopped "
                f"protecting those days — the exact divergence "
                f"test_trainer_partitions.py::test_blackout_agrees_with_gate_spec exists to "
                f"catch. Fix the engine, do not widen the declaration."
            )
        extra = sorted(d.isoformat() for d in ((covered & in_span) - lane_blackout))
        if extra:
            raise IterationLedgerRefusal(
                f"engine_reserved_blackout claims {len(extra)} day(s) that are NOT lane "
                f"blackout (e.g. {extra[:5]}). Excluding a window the lane does not black out "
                f"is a filter, not a blackout, and a filter belongs in the spec where the gate "
                f"can see it — not in the surface stamp where it would silently shrink the "
                f"window a look is recorded against."
            )
        return lane_blackout

    # -- reading ---------------------------------------------------------------------------
    def rows(self) -> list[dict]:
        return read_rows(self.path)

    def provenance_for(self, candidate_key: str) -> list[dict]:
        """Every row whose `candidate_id` OR `candidate_id_windowed` matches. This is what
        `graduate()` reads."""
        return [
            r for r in self.rows()
            if "_unparseable" not in r
            and candidate_key in (r.get("candidate_id"), r.get("candidate_id_windowed"))
        ]

    def summary(self, *, trial_ledger_paths: Sequence[str | Path] = ()) -> dict:
        """Exploration volume, and the billed bill beside it so the two are never confused."""
        rows = self.rows()
        good = [r for r in rows if "_unparseable" not in r]
        by: dict[str, dict[str, int]] = {"surface": {}, "verdict": {}, "session": {}, "mechanism": {}}
        distinct_specs: set[str] = set()
        distinct_candidates: set[str] = set()
        billed_rows = 0
        for r in good:
            for field, key in (("surface", "surface"), ("verdict", "verdict"),
                               ("session", "session"), ("mechanism", "mechanism")):
                v = str(r.get(key, ""))
                by[field][v] = by[field].get(v, 0) + 1
            distinct_specs.add(str(r.get("spec_digest", "")))
            distinct_candidates.add(str(r.get("candidate_id", "")))
            if r.get("billed"):
                billed_rows += 1
        out = {
            "schema": "gtos.training_lane.iteration_summary.v1",
            "path": str(self.path),
            "n_looks": len(good),
            "n_unparseable_rows": len(rows) - len(good),
            "n_distinct_specs": len(distinct_specs),
            "n_distinct_candidates": len(distinct_candidates),
            "n_rows_claiming_billed": billed_rows,
            "by_surface": dict(sorted(by["surface"].items())),
            "by_verdict": dict(sorted(by["verdict"].items())),
            "by_session": dict(sorted(by["session"].items())),
            "by_mechanism": dict(sorted(by["mechanism"].items())),
            "billed_here": 0,
            "note": (
                "n_looks is EXPLORATION volume and bills nothing. The multiplicity bill is the "
                "declared family size in the CANDIDATE_FAMILY declaration, which moves only "
                "through training_lane.graduation.graduate(). n_rows_claiming_billed must be 0 "
                "— a nonzero value means someone hand-edited this ledger."
            ),
        }
        if trial_ledger_paths:
            # Reported, never merged: the DSR trial ledger counts a different population for a
            # different correction, and adding them would be the leak this lane exists to stop.
            from ..validation_integrity.trial_budget_ledger import TrialLedger

            out["dsr_trial_ledger"] = {
                str(p): TrialLedger(p, autocreate=False).summary()["n_trials"]
                for p in trial_ledger_paths
            }
            out["dsr_trial_ledger_note"] = (
                "Reported beside, never summed. That ledger deflates the DSR; this one records "
                "exploration. Adding them is the backward leak the ratification's section 1.2 "
                "names."
            )
        return out


def _stamp_digest(stamp: dict) -> str:
    """Identity of a surface stamp: the map it came from and the span it covers."""
    return hashlib.sha256(
        json.dumps(
            {
                "map": stamp.get("surface_map_digest"),
                "span": stamp.get("span"),
                "n_by_surface": stamp.get("n_by_surface"),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()[:16]

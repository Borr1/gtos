#!/usr/bin/env python3
"""Session AV — prove a bar file's clock from its own bytes, per FILE (AV-1, B1600-B1612).

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_timebase_verify.py
    ... --paths data/historical/GBPJPY_H1.csv     # classify specific files
    ... --data-dir data/historical                # classify a whole directory
    ... --apply                                   # write sidecars for files that PROVE a clock

WHY THIS EXISTS AND WHY IT IS PER-FILE
--------------------------------------
`scripts/declare_research_timebase.py` declares a **directory** from **one** exchange
anchor and then stamps every CSV in it. That is the right tool for an export written in
one pass by one script. It is the wrong tool for `data/historical/` and
`data/historical_2022_2023/`, which are accretions: `src/utils/research_timebase.py:96`
already refuses to register `historical` for exactly that reason ("copies of that tree
disagree with each other"), and this session measured that its *tail* disagrees with its
own *body* (see AV_TIMEBASE_VERIFY_V1.json -> `data/historical/US30_cash_H1.csv`).

So every file is classified on its own bytes, and a file that cannot prove its clock is
refused by name. That is the F7 rule applied one level finer than the tool that exists.

THE METHOD
----------
Two probes, both anchored to a fact about the **market** rather than about the broker:

* **W (weekly rollover).** The spot FX/CFD week begins at the New York 17:00 interbank
  rollover, whatever clock the file is written in. So for every week, map the week's
  first bar stamp to UTC under a candidate hypothesis and subtract the true-UTC instant
  of that week's NY-17:00 Sunday. Under the CORRECT hypothesis the residual is a
  **constant** --- the instrument's own session convention (0 h for spot FX, +1 h for an
  index CFD that opens an hour into the week, and so on). Under a wrong one it moves,
  because every wrong hypothesis is wrong by a DST-shaped amount.
* **C (weekly close).** The same, on the Friday NY-17:00 close and the week's last bar.

The discriminating statistic is therefore **the number of seams in the residual, not the
level of the residual** --- which is what lets the probe run on FX, where there is no
hard open and the exchange-anchor estimator in
`scripts/measure_broker_clock_offset.py` returns noise (that tool says so at its
`ANCHORS` table). A file that passes has a residual with ZERO seams over its whole life.

HYPOTHESES, AND THE THIRD ONE THAT CANNOT BE STAMPED
----------------------------------------------------
* ``true_utc`` --- the stamps are already UTC. Identity map.
* ``broker_local`` --- the stamps are broker wall clock under a named rule
  (default FTMO-Server3 = America/New_York + 7 h, `src/utils/broker_clock.py`).
* ``eu_calendar_corrected`` --- **diagnosed, never stamped.** The stamps are broker wall
  clock that has already had a *European*-calendar offset subtracted. Such a file is
  correct outside the US/EU DST disagreement windows and exactly one hour wrong inside
  them, roughly 5 weeks a year. `research_timebase.py:99-101` names this defect on the
  VPS copy of `data/historical/`; this session measured it on THIS repo's copy too.
  There is no `time_column_basis` that expresses it, so the honest answer is to refuse
  and say which weeks are wrong --- not to invent a repair at the end of a session.

The disagreement windows are COMPUTED, not tabulated: a date is inside one when
``Europe/Berlin - America/New_York`` is 5 h instead of its usual 6 h. Hardcoding the
transition dates is how a calendar claim goes stale.

Read-only unless ``--apply``. Touches no broker. Rewrites no data byte --- a sidecar is a
declaration beside the file, per `src/utils/research_timebase.py`'s "declare, don't
rewrite".
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.utils.broker_clock import (  # noqa: E402
    NEW_YORK_PLUS_7,
    BrokerClockRule,
    broker_naive_to_utc,
    resolve_rule,
)
from src.utils.research_timebase import (  # noqa: E402
    BROKER_LOCAL,
    BROKER_LOCAL_EU_CORRECTED,
    TRUE_UTC,
    sidecar_path,
    write_sidecar,
)

NY = ZoneInfo("America/New_York")
EU = ZoneInfo("Europe/Berlin")

TRUE_UTC_H = "true_utc"
BROKER_LOCAL_H = "broker_local"
EU_CORRECTED = "eu_calendar_corrected"

# A week needs this fraction of the file's OWN modal week length before its boundary means
# anything. Christmas and New Year weeks run short and their "first bar" is a holiday
# artifact, not a rollover. Expressed as a fraction rather than a constant because the same
# probe has to run on D1 (5 bars/week) and M5 (~2,000).
MIN_WEEK_COMPLETENESS = 0.60
# The week's first bar must land within this many hours of the NY-17:00 rollover to be a
# rollover observation at all. Wide enough for an index CFD that opens hours late,
# narrow enough to drop a capture that starts mid-week.
OPEN_WINDOW_H = (-6.0, 30.0)
CLOSE_WINDOW_H = (-30.0, 6.0)
# A quarter of weeks, so one holiday cannot carry a verdict. This is a sanity floor, NOT
# the discriminability test --- that is `SPAN_MIN_WEEKS_EACH_SIDE` below, and it is the one
# that matters: `data/historical_2026/` is a KNOWN broker-local export that this probe must
# reproduce, and an arbitrary 30-week floor refused it on 29 evaluable weeks.
MIN_WEEKS = 12
MIN_MODAL_SHARE = 0.95
# The three hypotheses differ ONLY inside a US/EU DST disagreement window (true_utc vs
# eu_calendar_corrected) or across a US DST transition (true_utc vs broker_local). A file
# whose span contains neither cannot separate them, and a verdict on such a file would be a
# preference dressed as a measurement. Both bounds of a window must be observed, so weeks
# are required on each side.
SPAN_MIN_WEEKS_EACH_SIDE = 2
# A residual further than this from the file's own modal residual is not clock evidence:
# no two candidate clocks in play differ by more than 3 h, so a 24 h displacement is a
# market holiday (Christmas Monday, Boxing Day, New Year) moving the week's first PRINT,
# not the week's rollover moving. Such weeks are excluded and counted, never smoothed ---
# smoothing a multi-week run is how a real seam would get erased.
MAX_CLOCK_DEVIATION_H = 4.0


def in_disagreement_window(day: dt.date) -> bool:
    """True when the US and EU DST calendars disagree on this date.

    Computed from the two zones rather than tabulated, so it cannot go stale. Berlin is
    normally 6 h ahead of New York; in a disagreement window it is 5 h ahead.
    """
    noon = dt.datetime.combine(day, dt.time(12, 0))
    ny = noon.replace(tzinfo=NY).utcoffset()
    eu = noon.replace(tzinfo=EU).utcoffset()
    assert ny is not None and eu is not None
    return round((eu - ny).total_seconds() / 3600.0) != 6


def ny_1700_utc(day: dt.date) -> dt.datetime:
    """The true-UTC instant of 17:00 New York on ``day`` (naive UTC)."""
    return (
        dt.datetime.combine(day, dt.time(17, 0), tzinfo=NY)
        .astimezone(dt.timezone.utc)
        .replace(tzinfo=None)
    )


def read_stamps(path: Path, *, time_column: str = "time") -> tuple[list[dt.datetime], int]:
    """``(stamps, n_date_only)`` from a bar CSV, sorted, in the file's own clock.

    ``n_date_only`` counts rows whose ``time`` was a bare ``YYYY-MM-DD``. Such a row
    carries **no time of day**, so it carries no clock, and a file made entirely of them
    cannot prove anything --- see the D1 pair in ``data/historical/``, where the two
    conventions sit side by side and only one of them is evidence.
    """
    out: list[dt.datetime] = []
    date_only = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get(time_column) or "").strip()
            if not raw:
                continue
            try:
                out.append(dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S"))
                continue
            except ValueError:
                pass
            try:
                out.append(dt.datetime.strptime(raw, "%Y-%m-%d"))
                date_only += 1
                continue
            except ValueError:
                pass
            try:
                # A "+00:00"/"Z" suffix is NOT evidence of UTC --- it is exactly what
                # fromtimestamp(broker_epoch, tz=utc).isoformat() emits, i.e. F7's own
                # output. Strip it and let the probe decide.
                out.append(dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None))
            except ValueError:
                continue
    out.sort()
    return out, date_only


def group_weeks(stamps: list[dt.datetime]) -> dict[dt.date, list[dt.datetime]]:
    """Bucket stamps by the Saturday that precedes their trading week.

    Saturday-anchored so a Sunday-evening rollover bar groups with the Mon-Fri it opens,
    under every candidate clock --- no clock in play moves a bar across a Saturday.
    """
    weeks: dict[dt.date, list[dt.datetime]] = collections.defaultdict(list)
    for stamp in stamps:
        saturday = (stamp - dt.timedelta(days=(stamp.weekday() + 2) % 7)).date()
        weeks[saturday].append(stamp)
    return {k: sorted(v) for k, v in weeks.items()}


HYPOTHESES = (TRUE_UTC_H, BROKER_LOCAL_H, EU_CORRECTED)


def _to_utc(stamp: dt.datetime, hypothesis: str, rule: BrokerClockRule) -> dt.datetime:
    if hypothesis == TRUE_UTC_H:
        return stamp
    if hypothesis == EU_CORRECTED:
        # Broker wall clock that has already had an EET/EEST offset subtracted. Outside a
        # US/EU disagreement window the assumed and actual offsets coincide and the stamp
        # is true UTC; inside one the broker is at NY+7 (+3) while EET was assumed (+2),
        # so the stamp runs exactly one hour fast. That is F7's own arithmetic, one layer
        # up: the correction was applied with the wrong calendar rather than not at all.
        return stamp - dt.timedelta(hours=1) if in_disagreement_window(stamp.date()) else stamp
    return broker_naive_to_utc(stamp, rule).replace(tzinfo=None)


def _smooth(series: dict[dt.date, float]) -> dict[dt.date, float]:
    """Collapse lone single-week excursions --- a holiday, not a clock change.

    Same treatment `scripts/measure_broker_clock_offset.py:_transitions` gives its daily
    series, for the same reason and with the same justification.
    """
    keys = sorted(series)
    out = dict(series)
    for i in range(1, len(keys) - 1):
        prev, cur, nxt = keys[i - 1], keys[i], keys[i + 1]
        if series[prev] == series[nxt] != series[cur]:
            out[cur] = series[prev]
    return out


def _seams(series: dict[dt.date, float]) -> list[dict[str, object]]:
    keys = sorted(series)
    out = []
    for prev, cur in zip(keys, keys[1:]):
        if series[prev] != series[cur]:
            out.append({
                "between_weeks": [prev.isoformat(), cur.isoformat()],
                "change_hours": [series[prev], series[cur]],
                "after_week_in_disagreement_window": in_disagreement_window(cur + dt.timedelta(days=3)),
            })
    return out


@dataclass
class ProbeResult:
    probe: str
    hypothesis: str
    n_weeks: int
    modal_residual_h: float | None
    modal_share: float
    n_seams: int
    seams: list[dict[str, object]] = field(default_factory=list)
    deviating_weeks: list[str] = field(default_factory=list)
    deviating_in_window: int = 0
    deviating_out_window: int = 0
    holiday_displaced_weeks: list[str] = field(default_factory=list)

    @property
    def passes(self) -> bool:
        return (
            self.n_weeks >= MIN_WEEKS
            and self.modal_share >= MIN_MODAL_SHARE
            and self.n_seams == 0
        )

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["passes"] = self.passes
        return d


def probe_boundary(
    weeks: dict[dt.date, list[dt.datetime]],
    hypothesis: str,
    rule: BrokerClockRule,
    *,
    side: str,
) -> ProbeResult:
    """Residual of the week's open (or close) against the NY-17:00 rollover, per week."""
    lo, hi = OPEN_WINDOW_H if side == "open" else CLOSE_WINDOW_H
    lengths = sorted(len(b) for b in weeks.values())
    modal_len = statistics.median_high(lengths) if lengths else 0
    min_bars = max(3, int(modal_len * MIN_WEEK_COMPLETENESS))
    residuals: dict[dt.date, float] = {}
    for saturday, bars in sorted(weeks.items()):
        if len(bars) < min_bars:
            continue
        if side == "open":
            stamp = bars[0]
            anchor = ny_1700_utc(saturday + dt.timedelta(days=1))  # Sunday
        else:
            stamp = bars[-1]
            anchor = ny_1700_utc(saturday + dt.timedelta(days=6))  # the following Friday
        delta = (_to_utc(stamp, hypothesis, rule) - anchor).total_seconds() / 3600.0
        if not (lo <= delta <= hi):
            continue
        residuals[saturday] = round(delta, 3)

    # A capture boundary is not a market boundary: the first week of a file that starts
    # mid-week has no rollover in it, and the last week of a file cut on a Wednesday has no
    # close. Both print as seams and both are artifacts of where the export stopped.
    for edge in (min(residuals, default=None), max(residuals, default=None)):
        if edge is not None:
            residuals.pop(edge, None)

    if not residuals:
        return ProbeResult(f"weekly_{side}", hypothesis, 0, None, 0.0, 0)

    # Pass 1 fixes the level; pass 2 drops the weeks whose displacement is too large to be
    # a clock at all. Two passes because the modal is what defines "too large".
    provisional = collections.Counter(residuals.values()).most_common(1)[0][0]
    displaced = [d for d, v in sorted(residuals.items()) if abs(v - provisional) > MAX_CLOCK_DEVIATION_H]
    for d in displaced:
        residuals.pop(d)
    if not residuals:
        return ProbeResult(f"weekly_{side}", hypothesis, 0, None, 0.0, 0,
                           holiday_displaced_weeks=[d.isoformat() for d in displaced])

    counts = collections.Counter(residuals.values())
    modal, n_modal = counts.most_common(1)[0]
    smoothed = _smooth(residuals)
    seams = _seams(smoothed)
    deviating = [d for d, v in sorted(residuals.items()) if v != modal]
    return ProbeResult(
        probe=f"weekly_{side}",
        hypothesis=hypothesis,
        n_weeks=len(residuals),
        modal_residual_h=modal,
        modal_share=round(n_modal / len(residuals), 4),
        n_seams=len(seams),
        seams=seams[:12],
        deviating_weeks=[d.isoformat() for d in deviating[:20]],
        deviating_in_window=sum(1 for d in deviating if in_disagreement_window(d + dt.timedelta(days=3))),
        deviating_out_window=sum(1 for d in deviating if not in_disagreement_window(d + dt.timedelta(days=3))),
        holiday_displaced_weeks=[d.isoformat() for d in displaced],
    )


def ambiguous_bars(stamps: list[dt.datetime]) -> list[str]:
    """Bars an ``eu_calendar_corrected`` file could not be un-corrected without guessing.

    The correction switches on and off at a DST transition instant, but
    :func:`in_disagreement_window` resolves to a whole DATE. That is exact only where no
    bar prints between the earlier of the two transitions and the market's next open ---
    both transitions land on a Sunday morning (US 07:00 UTC, EU 01:00 UTC) and spot FX is
    shut from Friday 17:00 New York until Sunday 17:00 New York, so for a 24/5 instrument
    the set is empty. It is NOT empty for a 24/7 one, and asserting emptiness rather than
    measuring it is how the original defect happened. Any bar returned here is a reason to
    refuse the file.
    """
    out = []
    for s in stamps:
        if s.weekday() != 6:  # Sunday
            continue
        if in_disagreement_window(s.date()) != in_disagreement_window(s.date() - dt.timedelta(days=1)):
            if s.hour < 12:  # before the rollover, inside the switch's own ambiguity
                out.append(s.isoformat())
    return out


def classify(path: Path, *, rule: BrokerClockRule = NEW_YORK_PLUS_7) -> dict:
    stamps, n_date_only = read_stamps(path)
    return classify_stamps(stamps, n_date_only, path, rule=rule)


def classify_stamps(
    stamps: list[dt.datetime],
    n_date_only: int,
    path: Path,
    *,
    rule: BrokerClockRule = NEW_YORK_PLUS_7,
) -> dict:

    def refusal(verdict: str, reason: str) -> dict:
        return {
            "path": str(path),
            "verdict": verdict,
            "reason": reason,
            "n_bars": len(stamps),
            "first_stamp": stamps[0].isoformat() if stamps else None,
            "last_stamp": stamps[-1].isoformat() if stamps else None,
            "n_weeks_evaluated": 0,
            "rule_tested": rule.name,
            "hypotheses_passing": [],
            "eu_correction_ambiguous_bars": [],
            "probes": [],
        }

    if not stamps:
        return refusal("REFUSE_NO_PARSEABLE_STAMPS",
                       "no row carries a parseable value in the 'time' column")
    if n_date_only == len(stamps):
        return refusal(
            "REFUSE_DATE_ONLY_STAMPS",
            f"all {n_date_only} stamps are bare dates with no time of day, so the column "
            "carries no clock at all; reading them as midnight-in-some-zone would be an "
            "assumption of exactly the kind F7 is",
        )
    weeks = group_weeks(stamps)
    probes = [
        probe_boundary(weeks, h, rule, side=side)
        for h in HYPOTHESES
        for side in ("open", "close")
    ]
    by_hyp: dict[str, list[ProbeResult]] = collections.defaultdict(list)
    for p in probes:
        by_hyp[p.hypothesis].append(p)

    passing = [h for h in HYPOTHESES if by_hyp[h] and all(p.passes for p in by_hyp[h])]
    ambiguous = ambiguous_bars(stamps)

    evaluated = max(by_hyp[h][0].n_weeks for h in HYPOTHESES) if by_hyp else 0
    in_window = sum(1 for sat in weeks if in_disagreement_window(sat + dt.timedelta(days=3)))
    out_window = len(weeks) - in_window
    if min(in_window, out_window) < SPAN_MIN_WEEKS_EACH_SIDE:
        return {
            **refusal(
                "REFUSE_SPAN_TOO_SHORT_TO_DISCRIMINATE",
                f"the span covers {in_window} week(s) inside a US/EU DST disagreement window and "
                f"{out_window} outside; the three hypotheses are identical elsewhere, so these "
                "bytes cannot separate them and any verdict would be a preference, not a measurement",
            ),
            "n_weeks_evaluated": evaluated,
            "probes": [p.as_dict() for p in probes],
        }

    verdict_for = {
        TRUE_UTC_H: "STAMP_TRUE_UTC",
        BROKER_LOCAL_H: "STAMP_BROKER_LOCAL",
        EU_CORRECTED: "STAMP_EU_CALENDAR_CORRECTED",
    }
    if len(passing) == 1:
        hyp = passing[0]
        verdict = verdict_for[hyp]
        reason = (
            f"weekly open and close residuals are constant under {hyp} over "
            f"{by_hyp[hyp][0].n_weeks} weeks (0 seams, modal share "
            f"{min(p.modal_share for p in by_hyp[hyp]):.4f}); every competing hypothesis is refuted"
        )
        if hyp == EU_CORRECTED and ambiguous:
            verdict = "REFUSE_EU_CORRECTED_AMBIGUOUS_BARS"
            reason = (
                f"the eu_calendar_corrected map fits, but {len(ambiguous)} bar(s) print inside the "
                "transition Sunday's own ambiguity, where the correction's on/off date is not exact"
            )
    elif len(passing) > 1:
        verdict, reason = "REFUSE_AMBIGUOUS", f"more than one hypothesis survives: {sorted(passing)}"
    else:
        verdict, reason = "REFUSE_UNRESOLVED", "no hypothesis has a seam-free residual on both boundaries"

    n_weeks_eval = max((p.n_weeks for p in probes), default=0)
    return {
        "path": str(path),
        "n_bars": len(stamps),
        "first_stamp": stamps[0].isoformat(),
        "last_stamp": stamps[-1].isoformat(),
        "n_weeks_evaluated": n_weeks_eval,
        "verdict": verdict,
        "reason": reason,
        "rule_tested": rule.name,
        "hypotheses_passing": passing,
        "eu_correction_ambiguous_bars": ambiguous[:10],
        "probes": [p.as_dict() for p in probes],
    }


def classify_bounded(path: Path, *, rule: BrokerClockRule = NEW_YORK_PLUS_7) -> dict:
    """Classify the whole file; if that fails, find the longest PREFIX that proves a clock.

    ``data/historical/`` is two captures spliced: its body through 2026-04-03 and a tail
    on a different clock. Refusing such a file whole discards three years of measured
    bytes for the sake of three weeks of unmeasured ones. So when the whole file is
    unresolved, bisect for the latest week boundary at which the prefix resolves and
    declare THAT, with the bound written into the sidecar --- which
    `CsvBarSource._declared_window` then honours by dropping the tail and counting the
    drop. The bound is what makes the declaration honest; without it the sidecar would be
    asserting a clock over bytes it never measured.
    """
    stamps, n_date_only = read_stamps(path)
    full = classify_stamps(stamps, n_date_only, path, rule=rule)
    if full["verdict"].startswith("STAMP_") or not stamps:
        full["valid_from"] = stamps[0].date().isoformat() if stamps else None
        full["valid_through"] = stamps[-1].date().isoformat() if stamps else None
        full["bounded"] = False
        return full
    if full["verdict"] in ("REFUSE_NO_PARSEABLE_STAMPS", "REFUSE_DATE_ONLY_STAMPS"):
        return full

    cuts = sorted({s.date() for s in stamps})
    lo, hi, best = 0, len(cuts) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        cut = cuts[mid]
        prefix = [s for s in stamps if s.date() <= cut]
        res = classify_stamps(prefix, n_date_only, path, rule=rule)
        if res["verdict"].startswith("STAMP_"):
            best = (cut, res)
            lo = mid + 1
        else:
            hi = mid - 1
    if best is None:
        full["bounded"] = False
        full["prefix_search"] = "no prefix of this file proves a clock"
        return full
    cut, res = best
    # The bisect assumes the predicate is monotone in the cut date and it is not: a few
    # contaminated tail weeks can sit inside a passing prefix without yet moving the modal
    # share. So the bound is tightened to the FIRST seam the winning hypothesis shows over
    # the WHOLE file --- a direct observation that needs no monotonicity --- and the bisect
    # is used only to choose the hypothesis. Found by checking my own bisect's endpoint
    # against the hand truncation that motivated it (2026-04-08 vs 2026-04-03).
    hyp = {"STAMP_TRUE_UTC": TRUE_UTC_H, "STAMP_BROKER_LOCAL": BROKER_LOCAL_H,
           "STAMP_EU_CALENDAR_CORRECTED": EU_CORRECTED}[res["verdict"]]
    weeks_all = group_weeks(stamps)
    first_seam: dt.date | None = None
    for side in ("open", "close"):
        pr = probe_boundary(weeks_all, hyp, rule, side=side)
        for s in pr.seams:
            wk = dt.date.fromisoformat(s["between_weeks"][1])  # type: ignore[index]
            if first_seam is None or wk < first_seam:
                first_seam = wk
    if first_seam is not None:
        cut = min(cut, first_seam - dt.timedelta(days=1))

    res["verdict_over_whole_file"] = full["verdict"]
    res["bounded"] = True
    res["valid_from"] = stamps[0].date().isoformat()
    res["valid_through"] = cut.isoformat()
    res["first_seam_week_over_whole_file"] = first_seam.isoformat() if first_seam else None
    res["rows_outside_bound"] = sum(1 for s in stamps if s.date() > cut)
    res["reason"] = (
        f"the whole file is {full['verdict']}, but its prefix through {cut.isoformat()} proves "
        f"a clock and the {res['rows_outside_bound']} row(s) after it are a different capture; "
        "the sidecar is written with that bound and the reader drops the tail"
    )
    return res


EVIDENCE_TEMPLATE = (
    "Measured per FILE by {tool} on {n_bars} bars over {n_weeks} trading weeks "
    "({first} .. {last}). The spot week begins at the New York 17:00 rollover whatever clock "
    "the file is written in, so the residual of the week's first and last bar against that "
    "instant is constant under the correct hypothesis and DST-shaped under a wrong one. Under "
    "{hypothesis} both residuals are constant (open {r_open:+g} h, close {r_close:+g} h) with "
    "ZERO seams and modal share {share:.4f}; the competing hypothesis is refuted. Exchange-anchor "
    "verification (scripts/measure_broker_clock_offset.py) is NOT used here: it needs a cash-equity "
    "open, which spot FX does not have. Reproduce with: python3 {tool} --paths {path}"
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paths", nargs="*", default=[], help="Specific CSVs to classify.")
    ap.add_argument("--data-dir", nargs="*", default=[], help="Directories whose *.csv to classify.")
    ap.add_argument("--server", default="FTMO-Server3")
    ap.add_argument("--apply", action="store_true", help="Write sidecars for files that PROVE a clock.")
    ap.add_argument("--bounded", action="store_true",
                    help="When the whole file is unresolved, find the longest prefix that proves a "
                         "clock and declare it with a valid_through bound.")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--out", default=None, help="Write the full JSON receipt here.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    rule = resolve_rule(args.server)
    targets: list[Path] = [Path(p) for p in args.paths]
    for d in args.data_dir:
        targets.extend(sorted(Path(d).glob("*.csv")))
    targets = [t for t in targets if t.is_file()]
    if not targets:
        print("ERROR: no target files", file=sys.stderr)
        return 2

    basis_of = {
        "STAMP_TRUE_UTC": (TRUE_UTC_H, TRUE_UTC),
        "STAMP_BROKER_LOCAL": (BROKER_LOCAL_H, BROKER_LOCAL),
        "STAMP_EU_CALENDAR_CORRECTED": (EU_CORRECTED, BROKER_LOCAL_EU_CORRECTED),
    }
    classifier = classify_bounded if args.bounded else classify
    results = []
    written = []
    for path in targets:
        res = classifier(path, rule=rule)
        res["sidecar_present_before"] = sidecar_path(path).is_file()
        if args.apply and res["verdict"] in basis_of:
            if sidecar_path(path).is_file() and not args.overwrite:
                res["sidecar_action"] = "skipped_exists"
            else:
                hyp, basis = basis_of[res["verdict"]]
                ps = {p["probe"]: p for p in res["probes"] if p["hypothesis"] == hyp}
                evidence = EVIDENCE_TEMPLATE.format(
                    tool="docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_timebase_verify.py",
                    n_bars=res["n_bars"],
                    n_weeks=res["n_weeks_evaluated"],
                    first=res["first_stamp"],
                    last=res["last_stamp"],
                    hypothesis=hyp,
                    r_open=ps["weekly_open"]["modal_residual_h"],
                    r_close=ps["weekly_close"]["modal_residual_h"],
                    share=min(ps["weekly_open"]["modal_share"], ps["weekly_close"]["modal_share"]),
                    path=path,
                )
                if res.get("bounded"):
                    evidence += (
                        f" BOUNDED: over the whole file the verdict is "
                        f"{res['verdict_over_whole_file']}; this basis is measured over "
                        f"{res['valid_from']}..{res['valid_through']} and the "
                        f"{res['rows_outside_bound']} row(s) after it are a different capture."
                    )
                write_sidecar(
                    path,
                    basis=basis,
                    rule=rule if hyp == BROKER_LOCAL_H else None,
                    evidence=evidence,
                    server=args.server if hyp == BROKER_LOCAL_H else None,
                    valid_from=dt.date.fromisoformat(res["valid_from"]) if res.get("valid_from") else None,
                    valid_through=dt.date.fromisoformat(res["valid_through"]) if res.get("valid_through") else None,
                    extra={
                        "declared_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_timebase_verify.py",
                        "declared_session": "AV",
                        "declared_blocks": "B1600-B1613",
                    },
                )
                res["sidecar_action"] = "written"
                written.append(str(sidecar_path(path)))
        results.append(res)

    summary = collections.Counter(r["verdict"] for r in results)
    payload = {
        "schema": "gtos.wave12.av.timebase_verify.v1",
        "session": "AV",
        "blocks": "B1600-B1612",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_timebase_verify.py",
        "rule_tested": rule.name,
        "n_files": len(results),
        "summary": dict(summary),
        "sidecars_written": written,
        "files": results,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if not args.quiet:
        for r in results:
            print(f"{r['verdict']:32s} {r['path']}")
            if not r["verdict"].startswith("STAMP_"):
                print(f"    {r['reason']}")
        print()
        for verdict, n in sorted(summary.items()):
            print(f"  {verdict:32s} {n}")
        if written:
            print(f"\nwrote {len(written)} sidecar(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

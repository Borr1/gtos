"""The forward half: turn live shadow decisions into the same paired substrate.

WHAT THIS DOES AND DOES NOT DO
-------------------------------
It does **not** deploy, connect, or place anything.  It defines the on-disk contract between
the already-deployed read-only forward-shadow lane
(`C:\\Users\\Administrator\\gtos-shadow\\`, `FORWARD_SHADOW_DEPLOYED_20260811.md`) and this
harness, plus the preflight that makes a broken deployment fail LOUDLY.

The deployed lane already writes one JSONL row per decision cycle.  This module reads those
rows, projects each into an :class:`~substrate.Intent`, and appends it to the same store the
sealed-history questions run on -- so a question's sequential monitor keeps accumulating
information across the seam instead of restarting at it.

THE PREFLIGHT IS THE POINT
---------------------------
`FORWARD_SHADOW_DEPLOYED_20260811.md` records three deploys on three different missing data
artifacts, and the expensive one was deploy 2: `BROKER_TRUE_COSTS_V1.json` was absent, the
commission path returned `None` **by contract**, and the lane refused 88 candidates every
cycle with a healthy feed and a green log.  It measured nothing, indefinitely, and looked
fine.  :func:`preflight` converts that class of failure into a startup refusal that names the
missing path.

Every check here is a **read**.  The preflight fetches nothing and repairs nothing: it
answers "can this lane measure?" and, when the answer is no, which path made it no.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .substrate import NAME_TF, REPO, Intent

#: Artifacts the paired harness itself needs on the host.  The forward-shadow lane's own
#: required set is in its runbook; this is the ADDITIONAL set B8 introduces.
REQUIRED_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json",
     "AG's era/hour spread model -- every cost band and both selection gates resolve "
     "through it; absent, `spread_for` raises SpreadUnavailable on EVERY decision and the "
     "harness drops the entire population as unavailable (silent, per Q4/Q7)"),
    ("research/operations/spread_model_2026_07_29/BAR_SPREAD_ERAS.json.gz",
     "the era table the model multiplies; absent, the model loads and mis-prices"),
    ("src/components/ultimate_book/execution_packets.py",
     "SLEEVE_EXIT_PROFILES -- the published contract every control arm replays"),
    ("src/research_infra/walkforward/exits.py",
     "the sanctioned labeller; without it there is no fill authority"),
    ("src/research_infra/walkforward/quote_side.py",
     "replay_anchor + spread_for, the cost seam"),
    ("config/profiles/operator_profile.yaml",
     "the broker symbol resolver's source; a wrong resolver silently drops symbols"),
)


class PreflightFailed(RuntimeError):
    """The lane cannot measure.  Refuse to start and say which path."""


def preflight(repo: Path = REPO, *, strict: bool = True) -> dict[str, Any]:
    """Answer 'can this lane measure?' before it runs, and name the path when it cannot."""
    checks: list[dict[str, Any]] = []
    for rel, why in REQUIRED_ARTIFACTS:
        p = repo / rel
        ok = p.is_file()
        size = p.stat().st_size if ok else 0
        # An un-hydrated LFS pointer is ~131 bytes and reads as present. It is not.
        pointer = False
        if ok and size < 400:
            head = p.read_bytes()[:40]
            pointer = head.startswith(b"version https://git-lfs")
        checks.append({"path": rel, "present": ok, "bytes": size,
                       "unhydrated_lfs_pointer": pointer,
                       "ok": ok and not pointer, "why_it_matters": why})

    # A live probe of the cost seam: resolving one spread proves the model LOADS, not just
    # that its file exists. Deploy 2's failure was a resolvable file and an unresolvable
    # VALUE, which a file-existence check cannot see.
    probe: dict[str, Any] = {}
    try:
        from src.research_infra.walkforward.quote_side import SpreadUnavailable, spread_for

        at = dt.datetime(2026, 7, 1, 12, 0, tzinfo=dt.timezone.utc)
        try:
            probe = {"symbol": "EURUSD", "spread": spread_for("EURUSD", at, account="FTMO",
                                                             band="mid"), "ok": True}
        except SpreadUnavailable as exc:
            probe = {"symbol": "EURUSD", "ok": False,
                     "error": f"SpreadUnavailable: {exc}",
                     "meaning": "the model is present and cannot price. This is deploy 2's "
                                "failure mode: healthy feed, green log, zero measurement."}
    except Exception as exc:
        probe = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    failed = [c["path"] for c in checks if not c["ok"]]
    ok = not failed and bool(probe.get("ok"))
    out = {"preflight": "b8_paired_shadow", "artifact_checks": checks,
           "cost_seam_probe": probe, "missing_or_unhydrated": failed, "ok": ok,
           "generated": dt.datetime.now(dt.timezone.utc).isoformat()}
    if strict and not ok:
        raise PreflightFailed(
            "b8 paired-shadow preflight FAILED. "
            + (f"missing/unhydrated: {failed}. " if failed else "")
            + (f"cost seam: {probe.get('error')}. " if not probe.get("ok") else "")
            + "Refusing to start rather than measuring nothing.")
    return out


# ------------------------------------------------------------------ live decision intake ---
@dataclass(frozen=True)
class ShadowDecisionSchema:
    """The fields a live shadow row must carry to become a paired decision.

    Deliberately the SAME held tuple the sealed store carries.  A live row that cannot
    supply all of it is not a decision this harness can pair, and it is dropped with a named
    reason rather than defaulted.
    """

    sleeve: str = "sleeve"
    symbol: str = "symbol"
    timeframe: str = "timeframe"          # "M15" | "H4" | "D1"
    decision_bar_iso: str = "decision_bar_iso"
    direction: str = "direction"
    stop_dist: str = "sl_distance_price"
    target_dist: str = "target_dist"
    entry_utc: str = "entry_utc"
    decision_day: str = "decision_day"


def intents_from_shadow_log(path: Path, schema: ShadowDecisionSchema = ShadowDecisionSchema(),
                            ) -> tuple[list[Intent], dict[str, int]]:
    """Project a live shadow JSONL into paired decisions.

    Live rows carry no outcome yet, so `published_r_gross` is NaN and the label-identity
    control (C1) does not apply to them -- correctly: there is nothing to reproduce.  The
    harness's other controls do, and the receipt must state how many decisions in a run are
    forward rather than sealed, because a sequential monitor crossing its boundary on forward
    data is a different claim from one crossing on history.
    """
    rows: list[Intent] = []
    drops: dict[str, int] = {}
    if not path.is_file():
        return rows, {"log_absent": 1}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            drops["unparseable_json"] = drops.get("unparseable_json", 0) + 1
            continue
        try:
            tf = r[schema.timeframe]
            tf_int = NAME_TF[tf] if isinstance(tf, str) else int(tf)
            rows.append(Intent(
                sleeve=r[schema.sleeve], symbol=r[schema.symbol], timeframe=tf_int,
                decision_bar_iso=r[schema.decision_bar_iso],
                direction=int(r[schema.direction]),
                stop_dist=float(r[schema.stop_dist]),
                target_dist=(float(r[schema.target_dist]) if r.get(schema.target_dist) else None),
                decision_day=r.get(schema.decision_day, r[schema.entry_utc][:10]),
                entry_utc=r[schema.entry_utc],
                published_r_gross=float("nan"), published_exit_reason="forward_unresolved"))
        except (KeyError, TypeError, ValueError) as exc:
            k = f"incomplete_held_tuple:{type(exc).__name__}"
            drops[k] = drops.get(k, 0) + 1
    return rows, drops


def merge_forward(sealed: Sequence[Intent], forward: Iterable[Intent]) -> list[Intent]:
    """Append forward decisions to the sealed store, refusing duplicates on the pairing key.

    A restarted lane re-emitting yesterday's decisions must not double-count them: the
    sequential monitor's information fraction is the whole basis of its alpha spending, and
    a duplicated day inflates it silently.
    """
    seen = {i.key for i in sealed}
    out = list(sealed)
    for i in forward:
        if i.key in seen:
            continue
        seen.add(i.key)
        out.append(i)
    return out


def daily_read_summary(questions_receipt: Path) -> str:
    """The one-screen daily read: what moved, what crossed, what is still open."""
    if not questions_receipt.is_file():
        return f"NO RECEIPT AT {questions_receipt} -- the run did not complete."
    doc = json.loads(questions_receipt.read_text())
    lines = [f"B8 paired shadow -- {doc.get('generated', '?')}", ""]
    for qid, q in doc.get("questions", {}).items():
        if "paired_summary" not in q:
            lines.append(f"  {qid:52s} ERROR {q.get('error', '')}")
            continue
        s = q["paired_summary"]
        seq = q.get("sequential", {}).get("look", {})
        ci = s.get("ci95_block") or [float("nan")] * 2
        lines.append(
            f"  {qid:52s} n={s['n']:6d} mean={s['mean']:+.4f} "
            f"CI[{ci[0]:+.4f},{ci[1]:+.4f}] disc={s['discordance']:.1%} "
            f"t={seq.get('information_fraction', 0):.2f} {seq.get('decision', '?')} "
            f"-> {q.get('verdict_against_own_bar', '?')}")
    m = doc.get("multiplicity", {})
    lines += ["", f"  declared family: {m.get('declared_family_size')} arms, "
                  f"{m.get('n_admitting')} admitting at BH alpha {m.get('alpha')}"]
    c = doc.get("causality", {})
    if c.get("arms_with_same_day_aggregates"):
        lines.append(f"  SAME-DAY AGGREGATE ARMS (temporal companions mandatory): "
                     f"{c['arms_with_same_day_aggregates']}")
    return "\n".join(lines)

"""CD-1 -- the lane-iteration purpose: the wiring that makes a replay arm a LOOK.

Session CD, B2250. Sessions CB and CC built two halves that had never been
connected. CB's runner knows how to run a January arm cheaply and authorizes it
for `TRAINING` or `ACCEPTANCE_REPRODUCTION`. CC's protocol knows what a *look* is
-- which surface it touched, what disclosure travels with it, what verdict words
it may use, and that it bills nothing. Session CD's runs are neither of CB's
purposes: they are lane ITERATION on a `VAL`-surface window, and until this
module existed there was no way to say so.

## What this module adds, and what it deliberately does not

* **`PURPOSE_LANE_ITERATION`** (in `guard`) -- authorizes a window on the SURFACE
  axis without ever consulting the fitting axis. That is what makes the sealed
  January window legal to iterate on: it is role `SEALED` (not trainable) and
  surface `VAL` (iterable).
* **`write_iteration_outputs`** -- the same compact trade table CB's
  `write_training_outputs` writes, under a different stamp, gated on a different
  authorization property. A lane look can never produce a *training* artifact and
  a training run can never produce a *lane* one. Two emitters, two stamps, two
  gates; no flag decides which.
* **`log_look`** -- one call per arm into CC's `IterationLedger`. The ledger
  computes the surface from the DATES the guard enumerated, so a caller cannot
  mislabel what it read.

It does **not** re-declare a boundary, and it does not touch
`trainer_partitions.py` (Session CC owns that module; this session's commission
forbids editing it). Every surface answer here comes from
`lane_disposition_for_day` and `SurfaceMap.classify_days`.

## The verdict vocabulary, and the one word this lane may not say

`IterationLedger` refuses `admitted` / `rejected` / `graduated`. That refusal is
load-bearing for THIS session in particular: Session CD re-generates the broad V4
family, and the temptation to write down "the family is rejected" at the end of it
is exactly what the training lane was ratified to stop. A regeneration on a VAL
surface produces `improved` / `regressed` / `no_change` / `evaluated`, plus prose
that carries the used-once disclosure. The sealed gate's words are not available
here, and `verdict_for` will not translate one into the other.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra.train_engine import (
    TRAIN_ENGINE_VERSION,
    guard,
    identity,
    march_one_shot,
)

#: Every artifact a LANE_ITERATION run writes carries this. It is deliberately
#: NOT `TRAINING_EVIDENCE`: a training artifact asserts the fitting axis was
#: checked, and a lane look never checks it.
LANE_EVIDENCE_STAMP = (
    "LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade"
)

#: The mechanism name every broad-family look is logged under, so a later reader
#: can pull the whole regeneration out of the shared ledger with one filter.
BROAD_FAMILY_MECHANISM = "b7_5_broad_v4"


class IterationOutputRefused(RuntimeError):
    """A run tried to emit lane evidence it is not authorized to emit."""


def run_spec(
    *,
    arm: str,
    authorization: guard.WindowAuthorization,
    patches: Sequence[str],
    repairs: Sequence[str],
    engine_version: str = TRAIN_ENGINE_VERSION,
    contract_sha256: str | None = None,
    shared_execution_contract_sha256: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The identity of one variant, as the iteration ledger's `spec`.

    Everything that could make two runs of "the same arm" different economics
    belongs in here, because `spec_digest` over it is what `graduate()` joins on
    later. The repair set is the whole point of Session CD, so it is first-class
    rather than buried in a note; `patches` are the speed cuts and are included
    because a cut that changed an outcome would be a different variant even
    though nobody intended one.
    """

    spec: dict[str, Any] = {
        "family": "broad_v4_b7_5_selection_sizing",
        "arm": arm,
        "window": [authorization.start, authorization.end],
        "n_days": len(authorization.days),
        "engine": engine_version,
        "identity_tuple": identity.TUPLE_VERSION,
        "speed_cuts": sorted(patches),
        "repairs": sorted(repairs),
        "decision_contract_sha256": contract_sha256,
        "shared_execution_contract_sha256": shared_execution_contract_sha256,
    }
    if extra:
        spec.update(dict(extra))
    return spec


def write_iteration_outputs(
    *,
    out_dir: Path,
    authorization: guard.WindowAuthorization,
    economics: Mapping[str, Any],
    run_fingerprint: Mapping[str, Any],
    measurements: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Path]:
    """Emit the compact trade table + receipt for a LANE_ITERATION run.

    Refuses any authorization that is not a lane look, for the same structural
    reason CB's twin refuses a non-training one: the emitter checks the
    AUTHORIZATION OBJECT, never the caller's intent, so the stamp on the file
    cannot outrun the gate that was actually run.
    """

    if not authorization.may_emit_iteration_evidence:
        raise IterationOutputRefused(
            "lane outputs refused: window authorized for "
            f"{authorization.purpose!r} (surface_checked="
            f"{authorization.surface_checked}). Only a LANE_ITERATION window "
            "whose days are all on an iterable surface may emit a lane trade "
            "table."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    table = out_dir / "LANE_TRADE_TABLE.jsonl"
    header = {
        "row_kind": "header",
        "evidence_class": LANE_EVIDENCE_STAMP,
        "identity_tuple_version": identity.TUPLE_VERSION,
        "identity_fields": list(identity.TRADE_IDENTITY_FIELDS),
        "fingerprint": dict(run_fingerprint),
        "partition_authorization": authorization.as_dict(),
        "spec": dict(spec),
        "counts": economics.get("counts"),
        "disclosures": list(authorization.disclosures),
    }
    lines = [json.dumps(header, sort_keys=True, default=str)]
    for row in economics.get("trades") or ():
        lines.append(
            json.dumps(
                {
                    "row_kind": "trade",
                    "evidence_class": LANE_EVIDENCE_STAMP,
                    **{
                        field: row.get(field)
                        for field in identity.TRADE_IDENTITY_FIELDS
                    },
                },
                sort_keys=True,
                default=str,
            )
        )
    table.write_text("\n".join(lines) + "\n")

    receipt = out_dir / "LANE_RUN_RECEIPT.json"
    receipt.write_text(
        json.dumps(
            {
                "evidence_class": LANE_EVIDENCE_STAMP,
                "spec": dict(spec),
                "fingerprint": dict(run_fingerprint),
                "partition_authorization": authorization.as_dict(),
                "measurements": dict(measurements),
                "counts": economics.get("counts"),
                "missed_opportunity_pool": economics.get("missed_digest"),
                "ledger_digests": economics.get("ledger_digests"),
                "summary_economics": economics.get("summary_economics"),
                "trade_table": str(table),
                "disclosures": list(authorization.disclosures),
            },
            indent=1,
            sort_keys=True,
            default=str,
        )
    )
    return {"trade_table": table, "receipt": receipt}


def log_look(
    *,
    authorization: guard.WindowAuthorization,
    spec: Mapping[str, Any],
    session: str,
    verdict: str = "evaluated",
    metric: float | None = None,
    metric_name: str = "",
    note: str = "",
    receipt: str = "",
    ledger_path: str | Path | None = None,
    engine_version: str = TRAIN_ENGINE_VERSION,
    mechanism: str = BROAD_FAMILY_MECHANISM,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Record one arm as a look in CC's shared iteration ledger.

    `days` is passed rather than `(start, end)` on purpose: the guard already
    enumerated the calendar the ENGINE will replay, and handing the ledger that
    same list means the surface stamp is computed over exactly the days that were
    read. Passing a span would let a caller widen or narrow the recorded window
    relative to what ran.

    No `engine_reserved_blackout` is declared, and that is a claim rather than an
    omission: the guard refuses the blackout on every path, so a window that
    reached this function contains no blackout day to drop. Declaring one would
    be refused by the ledger anyway ("a filter, not a blackout").
    """

    from src.research_infra.training_lane import IterationLedger

    # The ledger classifies from the DATES, so under the March one-shot it must
    # be handed the same authorized surface map the guard used -- otherwise a
    # window the guard legitimately authorized would be refused at the point of
    # recording it, and the honest record of the one-shot is exactly the row we
    # would lose. Unarmed this is `None` and the ledger takes its own default.
    one_shot = march_one_shot.current()
    surfaces = (
        march_one_shot.authorized_surfaces(one_shot) if one_shot is not None else None
    )
    ledger = (
        IterationLedger(ledger_path, session=session, surfaces=surfaces)
        if ledger_path is not None
        else IterationLedger(session=session, surfaces=surfaces)
    )
    return ledger.record(
        mechanism=mechanism,
        sleeve="",
        spec=dict(spec),
        days=list(authorization.days),
        engine_version=engine_version,
        verdict=verdict,
        metric=metric,
        metric_name=metric_name,
        note=note,
        receipt=receipt,
        extra=dict(extra) if extra else None,
    )

"""path_scorecard SHADOW emitter stub — Dig absorb of STEAL-QSX-PATH-SCORECARD.

Upstream cite only: https://github.com/jianweiweng05/qsx-strategy-score (MIT)
Patterns absorb — do NOT vendor QSX wholesale.

Laws: place=False always; promote_grade_to_admit=False; affinity instrument×sleeve.
Writes sidecar JSONL only. Never edits live_armed_set. Never places.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Mapping

ICT = timezone(timedelta(hours=7))

GRADE_ENUM = (
    "PROVISIONAL",
    "GOLD",
    "SILVER",
    "BRONZE",
    "NEEDS_WORK",
    "FLAGGED",
)


@dataclass
class PathScorecard:
    score: float
    grade: str
    random_timing_p: float
    beta: float
    maxdd: float

    def validate(self) -> None:
        if not (0.0 <= float(self.score) <= 100.0):
            raise ValueError("score must be in [0, 100]")
        if self.grade not in GRADE_ENUM:
            raise ValueError(f"grade must be one of {GRADE_ENUM}")
        p = float(self.random_timing_p)
        if not (0.0 <= p <= 1.0):
            raise ValueError("random_timing_p must be in [0, 1]")


@dataclass
class SidecarRow:
    as_of_ict: str
    symbol: str
    sleeve_id: str
    affinity_cell: str
    path_scorecard: dict[str, Any]
    ticket: int | None = None
    wire_site_hint: str = "CL-JEV-CONF-SHADOW"
    place: bool = False
    promote_grade_to_admit: bool = False
    apply: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # hard const — never promote / place from Dig
        self.place = False
        self.promote_grade_to_admit = False
        self.apply = False


def accept_path_scorecard(payload: Mapping[str, Any]) -> PathScorecard:
    """Accept a typed path_scorecard dict (precomputed or foreign-tool output)."""
    card = PathScorecard(
        score=float(payload["score"]),
        grade=str(payload["grade"]),
        random_timing_p=float(payload["random_timing_p"]),
        beta=float(payload["beta"]),
        maxdd=float(payload["maxdd"]),
    )
    card.validate()
    return card


def compute_stub_path_scorecard(
    *,
    score: float,
    grade: str = "PROVISIONAL",
    random_timing_p: float = 0.5,
    beta: float = 0.0,
    maxdd: float = 0.0,
) -> PathScorecard:
    """Minimal local stub — placeholders only; real metrics come from research fold."""
    card = PathScorecard(
        score=score,
        grade=grade,
        random_timing_p=random_timing_p,
        beta=beta,
        maxdd=maxdd,
    )
    card.validate()
    return card


def fanout_fields(card: PathScorecard, *, symbol: str, sleeve_id: str) -> dict[str, Any]:
    """Map to proposed warroom_shadow fanout field names (SHADOW log only)."""
    cell = f"{symbol}|{sleeve_id}"
    return {
        "shadow.jev.path_scorecard.score": card.score,
        "shadow.jev.path_scorecard.grade": card.grade,
        "shadow.jev.path_scorecard.random_timing_p": card.random_timing_p,
        "shadow.jev.path_scorecard.beta": card.beta,
        "shadow.jev.path_scorecard.maxdd": card.maxdd,
        "shadow.jev.path_scorecard.instrument": symbol,
        "shadow.jev.path_scorecard.sleeve_id": sleeve_id,
        "shadow.jev.path_scorecard.affinity_cell": cell,
        "shadow.jev.path_scorecard.place": False,
        "shadow.jev.path_scorecard.promote_grade_to_admit": False,
        "shadow.jev.path_scorecard.apply": False,
    }


def write_sidecar_jsonl(
    path: Path,
    *,
    symbol: str,
    sleeve_id: str,
    card: PathScorecard,
    ticket: int | None = None,
    wire_site_hint: str = "CL-JEV-CONF-SHADOW",
    meta: Mapping[str, Any] | None = None,
) -> SidecarRow:
    """Append one SHADOW sidecar line. place/promote/apply forced false."""
    now = datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00")
    row = SidecarRow(
        as_of_ict=now,
        symbol=symbol,
        sleeve_id=sleeve_id,
        affinity_cell=f"{symbol}|{sleeve_id}",
        ticket=ticket,
        path_scorecard=asdict(card),
        wire_site_hint=wire_site_hint,
        meta=dict(meta or {}),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
    return row



def provisional_null_card() -> PathScorecard:
    """Stub when no fold metrics — fields EXIST; score null-ish via 0+PROVISIONAL.

    Note: PathScorecard.score is float; callers that need JSON null should use
    emit_path_scorecard_into(..., card=None) which stamps score=None.
    """
    return PathScorecard(
        score=0.0,
        grade="PROVISIONAL",
        random_timing_p=0.5,
        beta=0.0,
        maxdd=0.0,
    )


def emit_path_scorecard_into(
    bits: dict[str, Any],
    *,
    symbol: str,
    sleeve_id: str,
    card_or_none: PathScorecard | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge path_scorecard fanout into bits dict (SHADOW only). Mutates and returns bits.

    When card_or_none is None: stamp score=None, grade=PROVISIONAL, place/promote/apply False.
    Never invent NEWS. Never admit.
    """
    if card_or_none is None:
        cell = f"{symbol}|{sleeve_id}"
        fields = {
            "shadow.jev.path_scorecard.score": None,
            "shadow.jev.path_scorecard.grade": "PROVISIONAL",
            "shadow.jev.path_scorecard.random_timing_p": None,
            "shadow.jev.path_scorecard.beta": None,
            "shadow.jev.path_scorecard.maxdd": None,
            "shadow.jev.path_scorecard.instrument": symbol,
            "shadow.jev.path_scorecard.sleeve_id": sleeve_id,
            "shadow.jev.path_scorecard.affinity_cell": cell,
            "shadow.jev.path_scorecard.place": False,
            "shadow.jev.path_scorecard.promote_grade_to_admit": False,
            "shadow.jev.path_scorecard.apply": False,
        }
    elif isinstance(card_or_none, PathScorecard):
        fields = fanout_fields(card_or_none, symbol=symbol, sleeve_id=sleeve_id)
    else:
        card = accept_path_scorecard(card_or_none)
        fields = fanout_fields(card, symbol=symbol, sleeve_id=sleeve_id)
    bits.update(fields)
    return bits

if __name__ == "__main__":
    # smoke: accept dict → fanout → sidecar (workspace scratch only)
    demo = accept_path_scorecard(
        {
            "score": 61.0,
            "grade": "PROVISIONAL",
            "random_timing_p": 0.22,
            "beta": 0.35,
            "maxdd": -0.09,
        }
    )
    fields = fanout_fields(demo, symbol="XAGUSD", sleeve_id="metal_sleeve")
    assert fields["shadow.jev.path_scorecard.place"] is False
    assert fields["shadow.jev.path_scorecard.promote_grade_to_admit"] is False
    out = Path("/tmp/path_scorecard_shadow_demo.jsonl")
    write_sidecar_jsonl(out, symbol="XAGUSD", sleeve_id="metal_sleeve", card=demo)
    print("ok", fields["shadow.jev.path_scorecard.affinity_cell"], "→", out)

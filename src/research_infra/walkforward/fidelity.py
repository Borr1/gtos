"""The gate's own fidelity ceiling — what the generator can and cannot support a claim about.

A gate result is bounded above by the fidelity of the thing that generated its trades. If
the generation port reproduces only 19% of a sleeve's live decisions, then a gate score for
that sleeve measures the port's defect, not the sleeve. This module makes that bound
explicit, per sleeve, and refuses rather than reporting a number nobody should trust.

THE 19 % WAS A CODE-LINEAGE ARTEFACT, NOT A PORT DEFECT — SESSION Y, 2026-07-29
-------------------------------------------------------------------------------
`phase3/K1_GATE_RECEIPT.md` section 3.5 reported:

    class            agreed  live-only   live-recall
    per-bar             160          7          96 %
    first-of-day         40        175          19 %

and attributed the gap to path dependence — a per-day latch amplifying a bar difference
the live record does not preserve. Its section 6 concluded that "no amount of replay work
moves the second number".

**Measured otherwise (B482-B489).** K1-b compared two different *programs*. The live FTMO
book ran commit `redacted_host` (byte-identical to the 2026-07-25 read-only VPS export), which
has no `sleeves/_server_clock.py`; mainline routes nine sleeves' session hour through it.
The deployed sleeves compare **raw UTC** hours against constants that are FTMO **server**
hours, so in the K1-b window every session window in those nine sits 3 h later in UTC than
mainline's. Replaying the same port over the same bars with the deployed helpers restored
(`research_infra.replay_policy.generation_lineage`) recovers **175 of the 175** missing
intents, adds **0** new misses, and takes count agreement over the 2,640 live cycles from
**86.44 % to 98.86 %**:

    class                agreed  live-only   live-recall
    per-bar                 160          7        95.8 %   (source identical in both lineages)
    first-of-day (latch)    199          0       100.0 %   (5 sleeves)
    fixed-decision-bar       16          0       100.0 %   (2 sleeves)

Two controls, and a refuter was right that only the second one is worth much:

* Sleeves whose **source is identical** across the lineages (`idxrev` 49/5/41,
  `vol_compression` 3/0/2, the `mx_*` family) are byte-identical in both arms. The shim does
  not touch them, so this is near-tautological — it proves determinism and that no state
  leaks between arms, not specificity.
* Sleeves the shim **does** swap but whose change is inert in this window — `fx_jpy`
  54/0/102 and `fx_jpy_ny` 45/0/12, whose only diff is the EU-vs-US DST calendar, and the
  two calendars coincide on every day of 2026-06-18..07-24 — are also byte-identical. That
  is a falsifiable prediction, it was checked by re-running the whole arm after `fx_jpy` was
  added to the register, and it held over all 2,640 cycles.

The over-fit control is stronger than either. A refuter ran deliberately wrong shims — the
same instrument with the effective clock set to UTC+K for K in {+3 (mainline), +2, +1, 0
(correct), -1} over the same 800 cycles. The result is a **delta function**, not a broad
optimum: seven-sleeve live-recall 21.8 / 37.6 / 52.5 / **100.0** / 40.6 %, and the four
narrow-window or exact-`(hour, minute)` sleeves score **exactly zero under every wrong shim**
and 100 % only at K=0. Only `asia_pdl_fade` is partly rescuable by a wrong clock (76 % at
K=+1), because its ASIA window is hours wide — so a single-sleeve headline would have been
fittable and the seven-sleeve one is not.

Receipt: `phase5/SESSION_Y_FIRST_OF_DAY_RESULT.md`, machine-readable
`phase5/receipts/Y_K1B_LINEAGE.json`.

TWO OF K'S SEVEN WERE NOT FIRST-OF-DAY AT ALL
----------------------------------------------
`ny_crypto_momentum` (`:88-89`) and `kz_london_crypto_low` (`:88-90`) fire only when the
decision bar's `(hour, minute)` equals a fixed constant. There is no scan of earlier bars
and no per-day latch: one differing bar costs exactly one bar. K's table put them in the
first-of-day class and this register inherited it, so `_CLASS_TOTALS`' 19 % was computed
over a mixed population. They are `FIXED_DECISION_BAR` now. The five with a genuine latch
are `asian_fade` (`:101`,`:115`), `asia_pdl_fade` (`:99`,`:107`), `orb_crypto_london`
(`:107`,`:114`), `metal_session_reversion` (`:98`,`:106`,`:108`) and
`liq_asia_up_low_metal` (`_already_fired_today`, `:139`, called `:191`,`:204`).

WHAT 100 % LIVE-RECALL DOES AND DOES NOT ENTITLE A GATE TO
-----------------------------------------------------------
It says the port's **machinery** — bar ingestion, the canonical/broker crossing, the replay
clock, warmup, session location, the latch itself, the engine's DF-1 filter and decision-bar
selection — reproduces the live book exactly when it runs the code the live book ran. That
is a machinery verification and it is what a gate needs.

It does **not** say mainline generation is correct. A gate scores **mainline** semantics,
which no live record exists for; the residual is the correctness of the F7/B29 clock repair
itself, which is measured elsewhere (`src/utils/broker_clock.py`, 81 weekly session
boundaries per broker; `CLOCK_TRUTH_IMPACT_NOTE.md`) and is not a port property.

It does **not** cover the whole clock. `_SCOPE_STAMP` states the limit and it travels with
every raised row: 38 summer days at a constant +3 h, never at the winter +2 h, never on a
transition day, and never under mainline's 21:00 UTC latch reset.

It says nothing about **precision** on its own — `live_recall` has no precision term. See
`Fidelity.precision`, which is now carried: 72 % across the seven, and it is a LOWER BOUND
rather than a false-positive rate, because live's *naming* rate collapses 96.9 % -> 40.7 %
across the window while its complete counter stays flat and the port keeps tracking it. The
count-level statement is the honest one: 687 port candidate-instances against live's 706.

**Recommendation to Session W and to Borhen, not a change made here:** `scoreable()` still
gates on recall alone. A generator that emitted 40 % junk would pass it. A precision floor
belongs in `GateSpec` beside `fidelity_floor` — but the admission standard is W's design and
Borhen's decision, so Session Y carried the measurement and did not move the gate.

THE CLASS RATE IS STILL NOT THE SLEEVE RATE
--------------------------------------------
**Transferring a class rate is the error K's own B171 warns against** ("do not transfer a
rate and defend the transfer"). The 160 agreed per-bar intents decompose as:

    fx_jpy                             54   (100 %)
    idxrev                             49   ( 91 %)
    fx_jpy_ny                          45   (100 %)
    mx_nzdjpy_d1_donchian_20_breakout   5   (100 %)
    vol_compression                     3   (100 %)
    mx_avausd / mx_btcusd / mx_cadjpy / mx_ethusd   1 each

So **148 of the 160 come from three core-book sleeves, and the whole `mx_*` family
contributes 9 intents across five sleeves.** The 96 % figure is real and it is the right
class rate; it is not a measurement of `mx_btcusd_d1_donchian_20_breakout`. Those four
one-intent sleeves are deliberately left on the class rate rather than promoted to
`MEASURED_DIRECT`: a point estimate on n=1 is a worse basis than a class rate on n=167.

THREE DIFFERENT `mx_*` COUNTS ARE ALL CORRECT, AND THEY MUST NOT BE CONFLATED
-----------------------------------------------------------------------------
An earlier revision of this file said "14-sleeve family" in one place while listing 15
names in another, which is how a count drifts. Measured through the production resolvers on
2026-07-29:

  **16** — `candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES`, every spec authored.
  **14** — `MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES`, i.e. the `all14_swap_adjusted`
           reference policy. Excludes `mx_aus200_cash_d1_atr_mean_reversion` and
           `mx_ger40_cash_d1_atr_mean_reversion` (lost their symbol collision).
  **12** — what `admission.effective_registry` ACTUALLY resolves under the live config,
           because `agent_config.yaml:1286` selects the policy `positive_weighted12_after_swap`.
           Excludes `mx_aus200_cash_d1_volume_surge_reversal` and
           `mx_spn35_cash_d1_volume_surge_reversal`.

`WAVE_5_PLAN.md`'s "14 `mx_*` sleeves" is the collision-winner set, not the live book. This
register deliberately carries **all 16**, so that a sleeve promoted into the live policy
later already has a fidelity record rather than failing closed as UNMEASURED on the day it
matters. It is a superset of the live registry ON PURPOSE — never a claim about what is
live. For that, call `book_engine._active_sleeve_names()`.

This module therefore distinguishes three things the prompt for this session, and
`WAVE_5_PLAN.md`'s table, collapse into one:

  MEASURED_DIRECT     K measured this sleeve. Use its own recall.
  TRANSFERRED_CLASS   K measured this sleeve's structural class but not this sleeve. Use
                      the class rate, stamped TRANSFERRED, with the basis n attached so it
                      cannot be quoted without it.
  UNMEASURED          K never saw it. No recall claim exists.

REFUSAL
-------
`fidelity_for(sleeve)` returns a `Fidelity`; `GateSpec.fidelity_floor` (default 0.50) is
Session W's, and Session Y did not move it — only the measurements underneath it. Gate-spec
v2 also seals the reference policy and an optional precision floor. With the lineage artefact
removed, the recall floor no longer separates per-bar from first-of-day, because there is no
longer a gap there to separate: it now separates *measured* from *unmeasured*.
Sleeves with no observation still fail closed, and that is the property worth keeping —
`ny_index_momentum` is deliberately absent from this register (dormant, not in the deployed
allowlist at `config/agent_config.yaml:1274-1283`, and zero rows on either namespace), so it
refuses rather than inheriting a 100 % class rate it did nothing to earn.

K's section 6 recommendations are **narrowed, not retired**: recording the bars read and the
latch set would still close the 7 remaining live-only intents and the 30 disagreeing cycles,
and would still be the only way to verify a first-of-day sleeve on a window where the archive
and the live terminal disagree about bar availability. What is retired is the claim that "no
amount of replay work moves the 19 %".
"""

from __future__ import annotations

import enum
import hashlib
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

RECEIPT = "docs/audits/fable5-vision-audit-20260725/phase3/K1_GATE_RECEIPT.md"
YS_RECEIPT = "docs/audits/fable5-vision-audit-20260725/phase5/SESSION_Y_FIRST_OF_DAY_RESULT.md"
REPO = Path(__file__).resolve().parents[3]

# Historical direct measurements accepted aggregate counts supplied by their caller.  Keep
# that schema name attached to those records so old receipts remain readable, but never let
# them acquire the authority of the structured comparison below merely because the gate was
# upgraded.  A v2 measurement has no count arguments: it recomputes every verdict-moving
# count from two hash-bound JSONL identity populations.
AUTHORED_MEASUREMENT_SCHEMA = "gtos.walkforward.fidelity_measurement.authored.v1"
LEGACY_CALLER_COUNTS_SCHEMA = "gtos.walkforward.fidelity_measurement.caller_counts.v1"
STRUCTURED_MEASUREMENT_SCHEMA = "gtos.walkforward.fidelity_measurement.v2"
STRUCTURED_EVIDENCE_SCHEMA = "gtos.walkforward.fidelity_evidence.v2"


class FidelityClass(str, enum.Enum):
    """How the sleeve's generation reproduces its live decisions."""

    #: Each bar judged on its own. One differing bar costs exactly one bar.
    PER_BAR = "per_bar"
    #: Emits only on the session's first qualifying event. A latch: one differing bar early
    #: flips which bar is "first" and live/port never re-sync for the rest of that day.
    #: The latch is real (see the module docstring for the line that implements each), but
    #: it was NOT what drove K1-b's 19 % — that was the clock lineage.
    FIRST_OF_DAY = "first_of_day"
    #: Exactly one bar per day is eligible — the generator gates on `(hour, minute) ==
    #: const` and returns None otherwise. No scan of earlier bars, no latch, so one
    #: differing bar costs exactly one bar, as for PER_BAR. Kept distinct because a
    #: *clock* error costs such a sleeve every day rather than occasionally.
    FIXED_DECISION_BAR = "fixed_decision_bar"
    #: Structure not established from code or measurement.
    UNKNOWN = "unknown"


class FidelityBasis(str, enum.Enum):
    MEASURED_DIRECT = "measured_direct"
    #: Measured directly on this sleeve, with the port running the code generation the live
    #: record was produced by (`replay_policy.generation_lineage`). Strictly more evidence
    #: than MEASURED_DIRECT, and it carries one more caveat: a gate scores mainline
    #: semantics, which the live book never ran.
    MEASURED_LINEAGE_MATCHED = "measured_lineage_matched"
    TRANSFERRED_CLASS = "transferred_class"
    UNMEASURED = "unmeasured"


class FidelityReference(str, enum.Enum):
    """The record against which generator recall was measured.

    The original K1 register has a live-decision reference.  Structured research evidence
    distinguishes same-lineage replay consistency from an independently generated replay;
    neither kind is ever printed as live recall.  ``REPLAY_REFERENCE`` is the deliberately
    ambiguous historical-v1 value.
    """

    LIVE_RECORD = "live_record"
    SAME_LINEAGE_REPLAY = "same_lineage_replay"
    INDEPENDENT_REPLAY = "independent_replay"
    #: Historical receipts used this ambiguous value.  It deliberately does not assert
    #: whether the two generators were independent and no v2 policy accepts it.
    REPLAY_REFERENCE = "replay_reference"


class FidelityReferencePolicy(str, enum.Enum):
    """Which reference population may authorize the fidelity gate.

    ``LEGACY_ANY_REFERENCE`` exists only to reproduce gate-spec v1 behavior.  New gate
    specifications must choose one of the three explicit policies.
    """

    INDEPENDENT_OR_LIVE = "independent_or_live"
    REPLAY_CONSISTENCY = "replay_consistency"
    LIVE_RECORD_ONLY = "live_record_only"
    LEGACY_ANY_REFERENCE = "legacy_any_reference"


class FidelityEvidenceAuthority(str, enum.Enum):
    """How the counts in a fidelity record became authoritative."""

    AUTHORED_REGISTER = "authored_register"
    STRUCTURED_IDENTITY_COMPARISON = "structured_identity_comparison"
    CALLER_COUNTS = "caller_counts"


@dataclass(frozen=True)
class Fidelity:
    sleeve: str
    cls: FidelityClass
    basis: FidelityBasis
    #: Compatibility storage for recall = agreed / (agreed + reference_only).  Existing
    #: authored records use a live reference; `reference_kind` tells consumers when a
    #: direct research measurement instead uses an independently emitted replay reference.
    live_recall: float | None
    #: The (agreed, live_only) pair the recall was computed from — for a TRANSFERRED_CLASS
    #: entry this is the CLASS total, and `basis_sleeves` names what it actually covers.
    basis_agreed: int | None
    basis_live_only: int | None
    basis_note: str
    source: str = RECEIPT
    #: Intents the port produced that the live record does not NAME. Carried because
    #: `live_recall` has no precision term and a refuter was right that publishing recall
    #: alone is not honest. Read `precision`'s docstring before using it: at identity level
    #: it is uninterpretable on its own.
    basis_port_only: int | None = None
    reference_kind: FidelityReference = FidelityReference.LIVE_RECORD
    measurement_schema: str = AUTHORED_MEASUREMENT_SCHEMA
    evidence_authority: FidelityEvidenceAuthority = FidelityEvidenceAuthority.AUTHORED_REGISTER
    reference_lineage_sha256: str | None = None
    generated_lineage_sha256: str | None = None

    @property
    def reference_recall(self) -> float | None:
        """Recall against the explicitly named reference population."""
        return self.live_recall

    @property
    def recall_label(self) -> str:
        if self.reference_kind is FidelityReference.LIVE_RECORD:
            return "live-recall"
        return "replay-reference recall"

    @property
    def basis_n(self) -> int | None:
        if self.basis_agreed is None or self.basis_live_only is None:
            return None
        return self.basis_agreed + self.basis_live_only

    @property
    def precision(self) -> float | None:
        """`agreed / (agreed + port_only)` — and it is a LOWER BOUND, not a false-positive
        rate.

        Live names only ~54 % of its own candidates (`K1_GATE_RECEIPT.md` section 3.2), and
        Session Y measured that the naming rate *collapses* across the K1-b window —
        **96.9 % -> 44.1 % -> 40.7 %** by thirds — while live's complete counter
        (`bridge.n_candidates_in`) stays flat and the port keeps tracking it (279/288,
        197/202, 211/216). So identity precision falls from 99 % to 53 % over the same
        window in which recall is pinned at 100 %, and that fall is a property of the
        RECORD, not of the port.

        The give-away is that `fx_jpy` — the sleeve with the best recall in K's table, 100 %
        on 54 intents, and identical source in both lineages — has the WORST identity
        precision here, 34.6 % on 102 port-only. Nothing about `fx_jpy` degraded; live
        stopped naming.

        The honest precision statement is at COUNT level, where live's counter has no
        attribution gap: over 2,640 cycles the port produced **687** candidate-instances
        against live's **706**, over-generating on 9 cycles (+13) and under-generating on 21
        (-32). Use that, and use this property only with the caveat attached.
        """
        if self.basis_agreed is None or self.basis_port_only is None:
            return None
        denom = self.basis_agreed + self.basis_port_only
        return (self.basis_agreed / denom) if denom else None

    @property
    def precision_supported(self) -> bool:
        """Whether the evidence attests a complete generated comparison population."""
        return self.basis_port_only is not None

    def scoreable(
        self,
        floor: float,
        *,
        reference_policy: FidelityReferencePolicy | str = (
            FidelityReferencePolicy.LEGACY_ANY_REFERENCE
        ),
        precision_floor: float | None = None,
    ) -> bool:
        """False when the generator cannot support any claim about this sleeve."""
        return self.refusal_reason(
            floor,
            reference_policy=reference_policy,
            precision_floor=precision_floor,
        ) is None

    def refusal_reason(
        self,
        floor: float,
        *,
        reference_policy: FidelityReferencePolicy | str = (
            FidelityReferencePolicy.LEGACY_ANY_REFERENCE
        ),
        precision_floor: float | None = None,
    ) -> str | None:
        try:
            policy = FidelityReferencePolicy(reference_policy)
        except ValueError as exc:
            raise ValueError(f"unknown fidelity reference policy {reference_policy!r}") from exc

        if (
            policy is not FidelityReferencePolicy.LEGACY_ANY_REFERENCE
            and self.evidence_authority is FidelityEvidenceAuthority.CALLER_COUNTS
        ):
            return (
                "fidelity_evidence_unstructured: the measurement uses caller-supplied "
                f"aggregate counts ({self.measurement_schema}); gate policy {policy.value} "
                "requires counts recomputed from hash-bound structured identity evidence. "
                "The receipt remains historical v1 evidence but cannot authorize this gate."
            )

        allowed = {
            FidelityReferencePolicy.INDEPENDENT_OR_LIVE: {
                FidelityReference.LIVE_RECORD,
                FidelityReference.INDEPENDENT_REPLAY,
            },
            FidelityReferencePolicy.REPLAY_CONSISTENCY: {
                FidelityReference.SAME_LINEAGE_REPLAY,
            },
            FidelityReferencePolicy.LIVE_RECORD_ONLY: {
                FidelityReference.LIVE_RECORD,
            },
        }
        if policy is not FidelityReferencePolicy.LEGACY_ANY_REFERENCE:
            accepted = allowed[policy]
            if self.reference_kind not in accepted:
                return (
                    "fidelity_reference_policy_mismatch: reference kind "
                    f"{self.reference_kind.value} cannot satisfy sealed policy {policy.value}; "
                    f"accepted kinds are {sorted(kind.value for kind in accepted)}."
                )
        if self.live_recall is None:
            return (
                f"port_fidelity_unmeasured: {self.sleeve} was not in K1's measured set "
                f"({RECEIPT} section 3.5) and no live-recall figure exists for it or its "
                f"structural class. Structure inferred as {self.cls.value}."
            )
        if self.live_recall < floor:
            return (
                f"port_fidelity_below_floor: {self.recall_label} "
                f"{self.live_recall:.0%} < floor "
                f"{floor:.0%}. {self.sleeve} is a {self.cls.value} sleeve; a gate score for "
                f"it would measure the port, not the sleeve. Before concluding the port is "
                f"at fault, check that it ran the same code generation the live record was "
                f"made by — that mistake produced K1-b's whole first-of-day gap "
                f"(replay_policy.generation_lineage). Basis: {self.basis_note}"
            )
        if precision_floor is not None:
            if self.precision is None:
                return (
                    "fidelity_precision_unmeasured: sealed precision floor "
                    f"{precision_floor:.0%} requires a complete generated population, but "
                    f"{self.sleeve}'s evidence reports precision as null. Null is not pass."
                )
            if self.precision < precision_floor:
                return (
                    "fidelity_precision_below_floor: reference precision "
                    f"{self.precision:.0%} < sealed floor {precision_floor:.0%}."
                )
        return None

    def ceiling_stamp(self, floor: float) -> str:
        """The sentence that must travel with any score for this sleeve."""
        if self.live_recall is None:
            return f"FIDELITY UNMEASURED for {self.sleeve}."
        head = (
            f"FIDELITY CEILING {self.live_recall:.0%} {self.recall_label} "
            f"({self.basis.value}, {self.cls.value})"
        )
        if self.precision is not None:
            if self.reference_kind is FidelityReference.LIVE_RECORD:
                head += (
                    f", identity precision {self.precision:.0%} on {self.basis_port_only} "
                    f"port-only — a LOWER BOUND, live names ~54 % of its own candidates and "
                    f"its naming rate falls 97 %->41 % across the window"
                )
            else:
                head += (
                    f", replay-reference precision {self.precision:.0%} on "
                    f"{self.basis_port_only} generated-only identities"
                )
        if self.basis is FidelityBasis.MEASURED_LINEAGE_MATCHED:
            head += f". SCOPE: {_SCOPE_STAMP}"
        return f"{head}. {self.basis_note}"


# ======================================================================================
# The measured set. Every row here is transcribed from K1_GATE_RECEIPT.md section 3.5's
# per-sleeve table; the class totals are its class table.
# ======================================================================================
#: `k1_mainline` is the figure K published, kept so the correction is visible rather than
#: overwritten: it is what the sleeve scored when the port ran MAINLINE against a live
#: record made by the deployed lineage. `agreed`/`live_only` are the lineage-matched
#: measurement. For every sleeve whose source is identical across the two lineages the two
#: are the same numbers, and that is the control.
_MEASURED: dict[
    str, tuple[FidelityClass, FidelityBasis, int, int, tuple[int, int] | None, int]
] = {
    # sleeve                    class          basis          agreed live_only k1_mainline port_only
    "fx_jpy":
        (FidelityClass.PER_BAR, FidelityBasis.MEASURED_DIRECT, 54, 0, None, 102),
    "fx_jpy_ny":
        (FidelityClass.PER_BAR, FidelityBasis.MEASURED_DIRECT, 45, 0, None, 12),
    "idxrev":
        (FidelityClass.PER_BAR, FidelityBasis.MEASURED_DIRECT, 49, 5, None, 41),
    "mx_nzdjpy_d1_donchian_20_breakout":
        (FidelityClass.PER_BAR, FidelityBasis.MEASURED_DIRECT, 5, 0, None, 0),
    "vol_compression":
        (FidelityClass.PER_BAR, FidelityBasis.MEASURED_DIRECT, 3, 0, None, 2),
    "asia_pdl_fade":
        (FidelityClass.FIRST_OF_DAY, FidelityBasis.MEASURED_LINEAGE_MATCHED, 116, 0, (35, 81), 51),
    "asian_fade":
        (FidelityClass.FIRST_OF_DAY, FidelityBasis.MEASURED_LINEAGE_MATCHED, 41, 0, (3, 38), 8),
    "metal_session_reversion":
        (FidelityClass.FIRST_OF_DAY, FidelityBasis.MEASURED_LINEAGE_MATCHED, 24, 0, (2, 22), 4),
    "orb_crypto_london":
        (FidelityClass.FIRST_OF_DAY, FidelityBasis.MEASURED_LINEAGE_MATCHED, 13, 0, (0, 13), 1),
    "liq_asia_up_low_metal":
        (FidelityClass.FIRST_OF_DAY, FidelityBasis.MEASURED_LINEAGE_MATCHED, 5, 0, (0, 5), 0),
    "ny_crypto_momentum":
        (FidelityClass.FIXED_DECISION_BAR, FidelityBasis.MEASURED_LINEAGE_MATCHED, 11, 0, (0, 11), 12),
    "kz_london_crypto_low":
        (FidelityClass.FIXED_DECISION_BAR, FidelityBasis.MEASURED_LINEAGE_MATCHED, 5, 0, (0, 5), 7),
}

#: Class totals. PER_BAR is K's, unchanged and lineage-invariant (identical source in both
#: lineages). The other two are the lineage-matched measurement; K's mixed
#: FIRST_OF_DAY (40, 175) is superseded — it pooled two fixed-decision-bar sleeves into the
#: latch class and was computed against the wrong code generation.
_CLASS_TOTALS: dict[FidelityClass, tuple[int, int]] = {
    FidelityClass.PER_BAR: (160, 7),
    FidelityClass.FIRST_OF_DAY: (199, 0),
    FidelityClass.FIXED_DECISION_BAR: (16, 0),
}

#: Classes whose rate was measured with the port running the DEPLOYED code generation.
#: Any stamp built on them has to say so.
_LINEAGE_MATCHED_CLASSES = frozenset(
    {FidelityClass.FIRST_OF_DAY, FidelityClass.FIXED_DECISION_BAR})

_LINEAGE_CAVEAT = (
    "measured with the port running the deployed generation (redacted_host) that produced the "
    "live record; a gate scores MAINLINE semantics, which the live book never ran, so the "
    "residual is the F7/B29 clock repair's own correctness (measured separately in "
    "src/utils/broker_clock.py, not a port property)"
)

#: The scope limit a refuter identified as the largest unstated one, and it belongs on every
#: raised row. Three parts, all real:
#:   * 38 SUMMER days at a constant +3 h. Mainline routes through
#:     `broker_clock.NEW_YORK_PLUS_7`, which is +2 in winter, and a walk-forward gate scores
#:     multi-year history across every transition. Nothing here measures the port at +2 or
#:     on a transition day.
#:   * Under MAINLINE the latch resets on `server_day`, i.e. at 21:00 UTC — the Sunday open
#:     and Friday close land inside a day rather than on its boundary. The deployed arm
#:     (`_day` = UTC) never exercises that partition.
#:   * The arm is not the deployed PROGRAM. `git diff redacted_host HEAD --
#:     src/components/ultimate_book/` is +3,710/-247 across 25 files. Ten sleeve clock
#:     helpers are swapped; everything else is mainline. It reproduces the deployed CLOCK
#:     inside mainline everything-else — which is sound here only because the one
#:     generation-path engine difference, the bar-time repair, was measured inert: over a
#:     220-cycle stratified sample `_resolve_repair_offset_seconds` was called 12,325 times
#:     and returned None every time.
_SCOPE_STAMP = (
    "measured on 2026-06-18..07-24 only — 38 summer days at a constant +3 h broker offset, "
    "under the deployed clock, with the latch resetting at 00:00 UTC. NOT measured at the "
    "winter +2 h offset, NOT on a DST transition day, and NOT under mainline's 21:00 UTC "
    "latch reset. The arm swaps ten sleeve clock helpers into an otherwise-mainline engine"
)

#: What the per-bar class rate ACTUALLY rests on, per sleeve. Quoted in every transferred
#: stamp so the 96% can never be quoted bare.
_PER_BAR_DECOMPOSITION = (
    "the 96% per-bar class rate decomposes as fx_jpy 54, idxrev 49, fx_jpy_ny 45, "
    "mx_nzdjpy_d1_donchian_20_breakout 5, vol_compression 3, and 1 each from "
    "mx_avausd/mx_btcusd/mx_cadjpy/mx_ethusd — so 148 of 160 come from three core-book "
    "sleeves and the whole mx_* family contributes NINE intents across FIVE sleeves"
)

#: Structure established by reading the generator, where K did not measure the sleeve.
#: Citations are to the file that establishes the structure.
_STRUCTURE_BY_CODE: dict[str, tuple[FidelityClass, str]] = {
    # All 16 authored mx_* specs decide on one closed D1 bar and stamp the NEXT D1 open
    # (`sleeves/market_expansion_d1.py:5-8`, `next_open_decision_day` at :147-177).
    # One bar per day makes per-bar and per-day the same thing: no intra-day latch exists.
    **{
        name: (
            FidelityClass.PER_BAR,
            "sleeves/market_expansion_d1.py:5-8 — decides on one closed D1 bar; at D1 "
            "there is one bar per day so no intra-day first-of-day latch can exist",
        )
        for name in (
            "mx_aus200_cash_d1_atr_mean_reversion",
            "mx_aus200_cash_d1_volume_surge_reversal",
            "mx_avausd_d1_donchian_20_breakout",
            "mx_btcusd_d1_donchian_20_breakout",
            "mx_cadjpy_d1_volume_surge_reversal",
            "mx_ethusd_d1_donchian_20_breakout",
            "mx_eu50_cash_d1_volume_surge_reversal",
            "mx_fra40_cash_d1_volume_surge_reversal",
            "mx_ger40_cash_d1_atr_mean_reversion",
            "mx_ger40_cash_d1_volume_surge_reversal",
            "mx_jp225_cash_d1_volume_surge_reversal",
            "mx_spn35_cash_d1_volume_surge_reversal",
            "mx_us100_cash_d1_atr_mean_reversion",
            "mx_us30_cash_d1_volume_surge_reversal",
            "mx_us500_cash_d1_atr_mean_reversion",
        )
    },
    "vss_fxcross_london_up_low": (
        FidelityClass.PER_BAR,
        "sleeves/vss_fxcross_london_up_low.py:34-35,121-122 — session-windowed "
        "(LONDON_LO=7..LONDON_HI=13) but carries no per-day latch. ITS MIXED CLOCK IS "
        "CORRECT, and Session Y first said otherwise: `_hour` (:58-61) is server-local via "
        "_server_clock while `_daystr` (:64-70) is raw UTC, which reads as an "
        "inconsistency. It is not. `_daystr`'s only consumer is `_d1_up_regime` (:73-88), "
        "which filters aux D1 bars by `day < decision_day` — and `decision_day` is "
        "`bar_provider.decision_day_of`, the signal bar's UTC date (bar_provider.py:86-88, "
        "sole caller book_engine.py:531). The two are deliberately on the SAME calendar; "
        "converting `_daystr` to server_day would CREATE the mismatch. `_hour` is a "
        "different quantity — a session test against mined server constants — so two "
        "clocks in one file is right here. (Moving the correlated-unit day boundary is a "
        "separate owner-gated question, _server_clock.py's B54 Part 2.) Refuted Session "
        "Y's first rationale, B499. SEPARATE CAVEAT that does stand: this sleeve has NO "
        "identity-level measurement at all — all 55 of its FTMO live rows are "
        "`unit_skipped / future_decision_bar_time`, i.e. generation-side refusals, so it "
        "is 0 agreed / 0 live-only on both arms and its 96 % transferred stamp rests on "
        "nothing observed for it in 38 days",
    ),
    # Core H4 book: each evaluates the latest CLOSED bar.
    "metals_core": (FidelityClass.PER_BAR, "sleeves/metals.py:16 — latest CLOSED H4 bar"),
    "metals_softband": (FidelityClass.PER_BAR, "sleeves/metals.py:8-9"),
    "metals_ob_micro": (FidelityClass.PER_BAR, "sleeves/metals_ob_micro.py:1-20"),
    "crypto": (FidelityClass.PER_BAR, "sleeves/crypto.py:3-5 — latest CLOSED H4 bar i"),
    "energy_agri": (FidelityClass.PER_BAR, "sleeves/energy_agri.py:12"),
    "sub_xvol_pullback": (FidelityClass.PER_BAR, "sleeves/substrate.py:21-22"),
    "sub_mid_dn_revert": (FidelityClass.PER_BAR, "sleeves/substrate.py:19-22"),
    "vp_euidx_pocgrav": (FidelityClass.PER_BAR, "sleeves/vp_euidx.py:24-25"),
    # ---- the four sleeves with a generator and NO SleeveSpec (Session AK, B951) ----------
    # These are in `_NO_LIVE_PATH` below, which appends the harder caveat their absence earns.
    "vol_squeeze": (
        FidelityClass.PER_BAR,
        "sleeves/vol_squeeze.py:12-14,52 — decides on the latest CLOSED H4 bar i with no time "
        "gate of any kind, so no session latch can exist",
    ),
    "ny_index_momentum": (
        FidelityClass.FIXED_DECISION_BAR,
        "sleeves/ny_index_momentum.py:16,78 — gates on (server hour, minute) == (17, 0) and "
        "returns None otherwise, with no scan of earlier bars. Structurally identical to "
        "ny_crypto_momentum, which is MEASURED_DIRECT in this class",
    ),
    "structural_retest": (
        FidelityClass.PER_BAR,
        "sleeves/structural_retest.py:159-181 — session-BUCKETED (Asian/London/NY) but carries "
        "no per-day latch: any bar in the bucket whose vol-state, HTF regime and detector all "
        "fire emits, and nothing records that the day already fired. Same shape as "
        "vss_fxcross_london_up_low",
    ),
    "session_leadlag_genuine": (
        FidelityClass.PER_BAR,
        "sleeves/session_leadlag.py:generate — session-windowed with no latch. `mine_pair`'s "
        "min_gap=4 is NOT in the generator (it is per-series state and would make the generator "
        "impure), so nothing here makes it first-of-day",
    ),
    "cq_current_breaker_re_entry_inverted_5d_stop_0p25d": (
        FidelityClass.PER_BAR,
        "src/components/broader_origin_generators.py:331-354 — every generator call finalizes "
        "the current-bar candidates and applies the repair once, with no day latch or prior-call "
        "state; src/components/current_breaker_re_entry_repair.py:57-169 is a pure geometry "
        "transform that preserves entry/decision time and changes only identity, side, target "
        "and stop. DEFAULT-OFF AND NOT MEASURED DIRECTLY: the repaired identity has no live "
        "record of its own, so this grants only the measured per-bar CLASS rate, never a "
        "claim about this candidate's own live recall",
    ),
}

#: Sleeves whose generator exists and which **no production registry can reach**.
#:
#: This is a harder absence than `vss_fxcross_london_up_low`'s ("registered, but all 55 of its
#: live rows are generation-side refusals, so 0 agreed / 0 live-only"). These four have no
#: `SleeveSpec` at all, so there was never a cycle in which the live engine could have called
#: them: their live record is not thin, it is structurally empty, and no amount of replay can
#: change that until a registry entry exists.
#:
#: They are still given their structural class rate, for the same reason the fifteen authored
#: `mx_*` specs and every `register_surface_expansion` member are: the class rate is a claim
#: about how faithfully a code path of that SHAPE reproduces live decisions, and that claim
#: transfers. What does not transfer is any statement about this sleeve's own live behaviour,
#: and the sentence below travels into every verdict so a reader cannot mistake one for the other.
_NO_LIVE_PATH: dict[str, str] = {
    "vol_squeeze": "sleeves/registry.py — absent from BUILT, CANDIDATE_BUILT and "
                   "MARKET_EXPANSION_BUILT",
    "ny_index_momentum": "sleeves/registry.py — absent from all three spec tables",
    "structural_retest": "sleeves/registry.py — absent from all three spec tables; also absent "
                         "from candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES, pinned by "
                         "tests/ultimate_book/test_candidate_promotion_plumbing.py:74",
    "session_leadlag_genuine": "registered for SIZING (admission.py:267-277, CLEAN4_REGISTRY, "
                               "conf 0.15) and absent from every GENERATION spec table — the "
                               "one sleeve in the estate that can be sized and cannot fire. Its "
                               "generator was written in B960; the generation path still has no "
                               "cross-symbol channel to feed it (walkforward/supply.py "
                               "LIVE_WIRING_GAP)",
}

_NO_LIVE_PATH_STAMP = (
    "THIS SLEEVE HAS NO LIVE PATH: it is reachable from no production generation registry, so "
    "there has never been a cycle in which the live engine could call it and its live record is "
    "structurally EMPTY rather than thin. The class rate below is a property of the code path's "
    "SHAPE and is the only fidelity claim available; it is NOT a measurement of this sleeve. "
    "Where: {where}."
)


def _build_register() -> dict[str, Fidelity]:
    reg: dict[str, Fidelity] = {}
    for sleeve, (cls, basis, agreed, live_only, k1, port_only) in _MEASURED.items():
        denom = agreed + live_only
        note = (
            f"measured directly on this sleeve: {agreed} agreed / {live_only} live-only "
            f"(n={denom}) / {port_only} port-only"
        )
        if basis is FidelityBasis.MEASURED_LINEAGE_MATCHED:
            note += f", {_LINEAGE_CAVEAT}. {YS_RECEIPT}"
            if k1 is not None:
                k_agreed, k_live_only = k1
                k_denom = k_agreed + k_live_only
                note += (
                    f". SUPERSEDES {RECEIPT} section 3.5, which measured "
                    f"{k_agreed}/{k_denom} = {100 * k_agreed / k_denom:.0f}% for this "
                    f"sleeve by replaying mainline against a deployed-lineage record"
                )
        else:
            note += f", {RECEIPT} section 3.5"
        reg[sleeve] = Fidelity(
            sleeve=sleeve,
            cls=cls,
            basis=basis,
            live_recall=(agreed / denom) if denom else None,
            basis_agreed=agreed,
            basis_live_only=live_only,
            basis_note=note,
            basis_port_only=port_only,
        )
    for sleeve, (cls, why) in _STRUCTURE_BY_CODE.items():
        if sleeve in reg:
            continue
        totals = _CLASS_TOTALS.get(cls)
        if totals is None:
            reg[sleeve] = Fidelity(
                sleeve, cls, FidelityBasis.UNMEASURED, None, None, None,
                f"structure from code ({why}); no class rate exists",
            )
            continue
        agreed, live_only = totals
        note = (
            f"TRANSFERRED from the {cls.value} class rate ({agreed} agreed / {live_only} "
            f"live-only). This sleeve was NOT itself measured. Structure from code: {why}. "
        )
        if sleeve in _NO_LIVE_PATH:
            note = _NO_LIVE_PATH_STAMP.format(where=_NO_LIVE_PATH[sleeve]) + " " + note
        if cls is FidelityClass.PER_BAR:
            note += _PER_BAR_DECOMPOSITION + "."
        if cls in _LINEAGE_MATCHED_CLASSES:
            note += f" The class rate is {_LINEAGE_CAVEAT}."
        reg[sleeve] = Fidelity(
            sleeve=sleeve,
            cls=cls,
            basis=FidelityBasis.TRANSFERRED_CLASS,
            live_recall=agreed / (agreed + live_only),
            basis_agreed=agreed,
            basis_live_only=live_only,
            basis_note=note,
        )
    return reg


_AUTHORED_FIDELITY_REGISTER: dict[str, Fidelity] = _build_register()
# Public consumers need iteration and lookup, not write authority.  A mutable exported dict let
# any caller mint a perfect LIVE_RECORD object under an arbitrary sleeve name and thereby bypass
# every registrar and the v2 evidence-authority check.  Keep the authored backing private and
# expose a live read-only view so internal tests can still prove the authored-overwrite guards.
FIDELITY_REGISTER: Mapping[str, Fidelity] = MappingProxyType(_AUTHORED_FIDELITY_REGISTER)

#: Members registered by `register_surface_expansion`. Held apart from the authored register
#: so `clear_surface_expansions()` can never delete an authored entry, and so an artifact can
#: report which rows in a run were expansions rather than authored sleeves.
_SURFACE_EXPANSIONS: dict[str, Fidelity] = {}

# Direct, receipt-bound research measurements live outside the authored K1 register.  They
# are intentionally process-local: a caller must authenticate and register its receipt in
# the same run that invokes the gate, so an old measurement cannot silently become global
# authority for a later candidate.
_DIRECT_MEASUREMENTS: dict[str, Fidelity] = {}

#: The prefix a surface-expansion member name must carry. A research sweep must not be able
#: to mint a fidelity record under a name that could be mistaken for a production sleeve.
#: `mxf_` is one expanded member (one mechanism on one symbol); `fam_` is a pooled family.
#: No sleeve in any production registry starts with either.
EXPANSION_PREFIX = "mxf_"
#: What `register_surface_expansion` may mint: one expanded member, or a pooled family.
SURFACE_EXPANSION_PREFIXES: tuple[str, ...] = ("mxf_", "fam_")
#: What `register_threshold_variant` may mint: a parent rule at different constants (Session AL).
THRESHOLD_VARIANT_PREFIX = "thr_"
#: Every prefix a research sweep may mint a fidelity record under. Each registrar checks only
#: its OWN prefixes -- this union is for consumers asking "is this a research member at all",
#: and widening it must never widen what a registrar accepts.
EXPANSION_PREFIXES: tuple[str, ...] = SURFACE_EXPANSION_PREFIXES + (THRESHOLD_VARIANT_PREFIX,)


def _check_process_local_measurement_slot(member: str) -> None:
    """Give every process-local registrar one shared, non-shadowable namespace."""
    if not member or not member.strip():
        raise ValueError("direct-fidelity member must be non-empty")
    if member in FIDELITY_REGISTER:
        raise ValueError(
            f"{member!r} is an AUTHORED sleeve in the fidelity register; a direct "
            "measurement may not overwrite one"
        )
    if member in _SURFACE_EXPANSIONS:
        raise ValueError(
            f"{member!r} already has a temporary surface-expansion record; direct "
            "measurement authority may not shadow it"
        )
    if member in _DIRECT_MEASUREMENTS:
        raise ValueError(
            f"{member!r} already has a direct measurement in this process; clear it "
            "before authenticating another receipt"
        )


def _validated_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        c not in "009abcdef" for c in value
    ):
        raise ValueError(f"{label} must be 64 lowercase hex characters")
    return value


def _resolve_source_path(source: str, *, relative_to: Path = REPO) -> Path:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("direct fidelity requires a source path")
    path = Path(source)
    return path if path.is_absolute() else relative_to / path


def _verify_source(
    source: str, source_sha256: str, *, relative_to: Path = REPO
) -> tuple[Path, str]:
    digest = _validated_sha256(source_sha256, label="direct fidelity source_sha256")
    path = _resolve_source_path(source, relative_to=relative_to)
    if not path.is_file():
        raise ValueError(f"direct fidelity source path does not exist: {source}")
    observed = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            observed.update(block)
    if observed.hexdigest() != digest:
        raise ValueError(
            f"direct fidelity source hash mismatch for {source}: "
            f"{observed.hexdigest()} != {digest}"
        )
    return path, digest


def _verified_source_bytes(
    source: str, source_sha256: str, *, relative_to: Path = REPO
) -> tuple[Path, str, bytes, tuple[int, int]]:
    """Read and hash one immutable snapshot, then return those exact bytes.

    Verification and parsing must consume the same open file description.  Hashing a path and
    reopening it later leaves a replacement window in which different bytes can acquire the
    earlier digest's authority.
    """

    digest = _validated_sha256(source_sha256, label="direct fidelity source_sha256")
    path = _resolve_source_path(source, relative_to=relative_to)
    if not path.is_file():
        raise ValueError(f"direct fidelity source path does not exist: {source}")
    with path.open("rb") as handle:
        stat = os.fstat(handle.fileno())
        payload = handle.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != digest:
        raise ValueError(
            f"direct fidelity source hash mismatch for {source}: {observed} != {digest}"
        )
    return path, digest, payload, (stat.st_dev, stat.st_ino)


def _verify_authority_descriptor(
    descriptor: Any,
    *,
    label: str,
    evidence_dir: Path,
) -> tuple[Path, str]:
    """Verify one path-and-hash authority artifact named by a structured manifest.

    The artifact remains an auditable attestation: bytes cannot prove that two teams are
    organizationally independent, or that a capture is genuinely broker-live.  They do prevent
    a reference label or a free-form 64-character string from acquiring that authority by itself.
    """
    if not isinstance(descriptor, Mapping):
        raise ValueError(
            f"structured fidelity {label} must be a hash-bound object with source_path and "
            "source_sha256"
        )
    source = descriptor.get("source_path")
    source_sha256 = descriptor.get("source_sha256")
    if not isinstance(source, str) or not isinstance(source_sha256, str):
        raise ValueError(
            f"structured fidelity {label} requires source_path and source_sha256"
        )
    return _verify_source(source, source_sha256, relative_to=evidence_dir)


def _reject_nonstandard_json_constant(token: str) -> None:
    # Python's json module accepts NaN/Infinity by default even though they are not JSON.  They
    # would otherwise become stable identity strings and silently enlarge an evidence population.
    raise ValueError(f"non-standard JSON constant {token}")


def _identity_population(
    descriptor: Mapping[str, Any],
    *,
    label: str,
    identity_fields: tuple[str, ...],
    evidence_dir: Path,
) -> tuple[set[tuple[str, ...]], Path, str, tuple[int, int]]:
    """Load and hash one JSONL stream, returning identities from those exact bytes."""
    raw_source = descriptor.get("source_path")
    raw_sha256 = descriptor.get("source_sha256")
    if not isinstance(raw_source, str) or not isinstance(raw_sha256, str):
        raise ValueError(
            f"structured fidelity {label} requires source_path and source_sha256"
        )
    path, digest, payload, file_identity = _verified_source_bytes(
        raw_source,
        raw_sha256,
        relative_to=evidence_dir,
    )
    identities: set[tuple[str, ...]] = set()
    with io.StringIO(payload.decode("utf-8"), newline=None) as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw, parse_constant=_reject_nonstandard_json_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(
                    f"structured fidelity {label} source {raw_source}:{line_number} is not JSON"
                ) from exc
            if not isinstance(row, dict):
                raise ValueError(
                    f"structured fidelity {label} source {raw_source}:{line_number} must be "
                    "an object"
                )
            missing = [field for field in identity_fields if row.get(field) is None]
            if missing:
                raise ValueError(
                    f"structured fidelity {label} source {raw_source}:{line_number} misses "
                    f"identity fields {missing}"
                )
            unsupported = [
                field
                for field in identity_fields
                if isinstance(row[field], (dict, list))
            ]
            if unsupported:
                raise ValueError(
                    f"structured fidelity {label} source {raw_source}:{line_number} has "
                    f"non-scalar identity fields {unsupported}"
                )
            identity = tuple(
                json.dumps(
                    row[field],
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                for field in identity_fields
            )
            if identity in identities:
                raise ValueError(
                    f"structured fidelity {label} source {raw_source}:{line_number} repeats "
                    "an identity; duplicate collapse would make the denominator ambiguous"
                )
            identities.add(identity)
    return identities, path, digest, file_identity


def register_structured_fidelity_measurement(
    member: str,
    *,
    source: str,
    source_sha256: str,
    cls: FidelityClass = FidelityClass.UNKNOWN,
    note: str = "",
) -> Fidelity:
    """Register a v2 fidelity measurement derived from hash-bound identity populations.

    ``source`` is a JSON manifest with schema ``STRUCTURED_EVIDENCE_SCHEMA``.  It names a
    reference JSONL and a generated JSONL, binds both by sha256, fixes the identity fields,
    and attests whether the generated population is complete enough to support precision.
    Replay lineages are themselves path-and-hash-bound under ``lineage_authority``; a live
    reference likewise binds ``recording_authority`` plus its capture id.  Those artifacts make
    provenance claims reviewable and drift-detectable; they cannot prove organizational
    independence or broker-live origin without a human/source audit.  No numerator or denominator
    enters this API; intersection and both set differences are computed here.
    """
    _check_process_local_measurement_slot(member)
    manifest_path, manifest_digest, manifest_bytes, _ = _verified_source_bytes(
        source, source_sha256
    )
    try:
        document = json.loads(
            manifest_bytes.decode("utf-8"),
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"structured fidelity evidence is not valid JSON: {source}") from exc
    if not isinstance(document, dict):
        raise ValueError("structured fidelity evidence must be a JSON object")
    if document.get("schema") != STRUCTURED_EVIDENCE_SCHEMA:
        raise ValueError(
            "missing structured fidelity evidence: expected schema "
            f"{STRUCTURED_EVIDENCE_SCHEMA!r}, got {document.get('schema')!r}"
        )
    if document.get("member") != member:
        raise ValueError(
            f"structured fidelity member mismatch: manifest names {document.get('member')!r}, "
            f"registrar was asked for {member!r}"
        )
    raw_fields = document.get("identity_fields")
    if (
        not isinstance(raw_fields, list)
        or not raw_fields
        or any(not isinstance(field, str) or not field.strip() for field in raw_fields)
        or len(set(raw_fields)) != len(raw_fields)
    ):
        raise ValueError("structured fidelity identity_fields must be unique non-empty strings")
    identity_fields = tuple(raw_fields)
    reference = document.get("reference")
    generated = document.get("generated")
    if not isinstance(reference, dict) or not isinstance(generated, dict):
        raise ValueError("structured fidelity evidence requires reference and generated objects")
    try:
        reference_kind = FidelityReference(reference.get("kind"))
    except ValueError as exc:
        raise ValueError(
            f"unknown fidelity reference kind {reference.get('kind')!r}"
        ) from exc
    if reference_kind is FidelityReference.REPLAY_REFERENCE:
        raise ValueError(
            "structured fidelity v2 refuses ambiguous replay_reference; attest "
            "same_lineage_replay or independent_replay explicitly"
        )

    generated_lineage_path, generated_lineage = _verify_authority_descriptor(
        generated.get("lineage_authority"),
        label="generated.lineage_authority",
        evidence_dir=manifest_path.parent,
    )
    reference_lineage: str | None = None
    reference_authority_note = ""
    if reference_kind in {
        FidelityReference.SAME_LINEAGE_REPLAY,
        FidelityReference.INDEPENDENT_REPLAY,
    }:
        reference_lineage_path, reference_lineage = _verify_authority_descriptor(
            reference.get("lineage_authority"),
            label="reference.lineage_authority",
            evidence_dir=manifest_path.parent,
        )
        same = reference_lineage == generated_lineage
        if reference_kind is FidelityReference.SAME_LINEAGE_REPLAY and not same:
            raise ValueError(
                "same_lineage_replay requires identical hash-bound reference/generated "
                "lineage authority"
            )
        if reference_kind is FidelityReference.INDEPENDENT_REPLAY and same:
            raise ValueError(
                "independent_replay requires different hash-bound reference/generated "
                "lineage authority"
            )
        reference_authority_note = (
            f" Reference lineage authority: {reference_lineage_path} "
            f"sha256={reference_lineage}."
        )
    else:
        recording_authority = reference.get("recording_authority")
        if not isinstance(recording_authority, dict) or not recording_authority:
            raise ValueError(
                "live_record reference requires a non-empty recording_authority object"
            )
        if not isinstance(recording_authority.get("capture_id"), str) or not recording_authority[
            "capture_id"
        ].strip():
            raise ValueError("live_record recording_authority requires a non-empty capture_id")
        recording_path, recording_digest = _verify_authority_descriptor(
            recording_authority,
            label="reference.recording_authority",
            evidence_dir=manifest_path.parent,
        )
        reference_authority_note = (
            f" Recording authority {recording_authority['capture_id']!r}: {recording_path} "
            f"sha256={recording_digest}."
        )

    population_complete = generated.get("population_complete")
    if not isinstance(population_complete, bool):
        raise ValueError("generated.population_complete must be explicitly true or false")
    (
        reference_ids,
        reference_path,
        reference_digest,
        reference_file_identity,
    ) = _identity_population(
        reference,
        label="reference",
        identity_fields=identity_fields,
        evidence_dir=manifest_path.parent,
    )
    (
        generated_ids,
        generated_path,
        generated_digest,
        generated_file_identity,
    ) = _identity_population(
        generated,
        label="generated",
        identity_fields=identity_fields,
        evidence_dir=manifest_path.parent,
    )
    if (
        reference_path.resolve() == generated_path.resolve()
        or reference_file_identity == generated_file_identity
    ):
        raise ValueError(
            "structured fidelity reference and generated sources resolve to the same canonical "
            "population; path aliases and symlinks cannot establish a comparison"
        )
    if not reference_ids:
        raise ValueError("structured fidelity needs at least one reference identity")

    agreed = len(reference_ids & generated_ids)
    reference_only = len(reference_ids - generated_ids)
    generated_only = len(generated_ids - reference_ids) if population_complete else None
    denominator = len(reference_ids)
    precision_note = (
        f" / {generated_only} generated-only"
        if generated_only is not None
        else "; generated population marked incomplete, precision is null and not imputed"
    )
    basis_note = (
        f"MEASURED DIRECTLY from structured identity evidence: {agreed} agreed / "
        f"{reference_only} reference-only (n={denominator}){precision_note}. Identity fields: "
        f"{list(identity_fields)}. Reference: {reference_path} sha256={reference_digest}; "
        f"generated: {generated_path} sha256={generated_digest}; evidence manifest: {source} "
        f"sha256={manifest_digest}. Generated lineage authority: {generated_lineage_path} "
        f"sha256={generated_lineage}.{reference_authority_note}"
        + ((" " + note.strip()) if note.strip() else "")
    )
    rec = Fidelity(
        sleeve=member,
        cls=cls,
        basis=FidelityBasis.MEASURED_DIRECT,
        live_recall=agreed / denominator,
        basis_agreed=agreed,
        basis_live_only=reference_only,
        basis_note=basis_note,
        source=f"{source}#sha256={manifest_digest}",
        basis_port_only=generated_only,
        reference_kind=reference_kind,
        measurement_schema=STRUCTURED_MEASUREMENT_SCHEMA,
        evidence_authority=FidelityEvidenceAuthority.STRUCTURED_IDENTITY_COMPARISON,
        reference_lineage_sha256=reference_lineage,
        generated_lineage_sha256=generated_lineage,
    )
    _DIRECT_MEASUREMENTS[member] = rec
    return rec


def register_direct_fidelity_measurement(
    member: str,
    *,
    agreed: int,
    reference_only: int,
    generated_only: int | None,
    reference_kind: FidelityReference | str,
    source: str,
    source_sha256: str,
    cls: FidelityClass = FidelityClass.UNKNOWN,
    note: str = "",
) -> Fidelity:
    """Register a historical v1 caller-count measurement for one run.

    This API remains so committed receipts can be reproduced without rewriting history.  It
    content-binds the receipt but cannot prove that its supplied numerator/denominators were
    derived from that receipt.  Records from it therefore carry ``CALLER_COUNTS`` authority
    and are refused by every v2 gate policy.  New work must use
    :func:`register_structured_fidelity_measurement`.
    """
    _check_process_local_measurement_slot(member)
    for label, value in (("agreed", agreed), ("reference_only", reference_only)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label} must be a non-negative integer; got {value!r}")
    if generated_only is not None and (
        isinstance(generated_only, bool)
        or not isinstance(generated_only, int)
        or generated_only < 0
    ):
        raise ValueError(
            f"generated_only must be a non-negative integer or None; got {generated_only!r}"
        )
    denominator = agreed + reference_only
    if denominator <= 0:
        raise ValueError("direct fidelity needs at least one reference identity")
    try:
        reference_kind = FidelityReference(reference_kind)
    except ValueError as exc:
        raise ValueError(f"unknown fidelity reference kind {reference_kind!r}") from exc
    _, digest = _verify_source(source, source_sha256)

    label = (
        "live record"
        if reference_kind is FidelityReference.LIVE_RECORD
        else "replay reference whose lineage independence was not attested by this v1 schema"
    )
    precision_note = (
        f" / {generated_only} generated-only"
        if generated_only is not None
        else "; generated-only precision unavailable and not imputed"
    )
    basis_note = (
        f"MEASURED DIRECTLY against {label}: {agreed} agreed / {reference_only} "
        f"reference-only (n={denominator}){precision_note}. Content-bound source: "
        f"{source} sha256={digest}."
        + ((" " + note.strip()) if note.strip() else "")
    )
    rec = Fidelity(
        sleeve=member,
        cls=cls,
        basis=FidelityBasis.MEASURED_DIRECT,
        live_recall=agreed / denominator,
        basis_agreed=agreed,
        basis_live_only=reference_only,
        basis_note=basis_note,
        source=f"{source}#sha256={digest}",
        basis_port_only=generated_only,
        reference_kind=reference_kind,
        measurement_schema=LEGACY_CALLER_COUNTS_SCHEMA,
        evidence_authority=FidelityEvidenceAuthority.CALLER_COUNTS,
    )
    _DIRECT_MEASUREMENTS[member] = rec
    return rec


def clear_direct_fidelity_measurements() -> int:
    """Drop process-local direct measurements. Returns how many went."""
    n = len(_DIRECT_MEASUREMENTS)
    _DIRECT_MEASUREMENTS.clear()
    return n


def direct_fidelity_measurements() -> dict[str, Fidelity]:
    """Return a copy of the process-local direct-measurement register."""
    return dict(_DIRECT_MEASUREMENTS)


def register_threshold_variant(
    member: str,
    *,
    parent: str,
    params: dict,
    production_params: dict,
    note: str = "",
) -> Fidelity:
    """Give a THRESHOLD variant of `parent`'s rule a fidelity record. Session AL (B1152).

    WHY A SECOND REGISTRAR RATHER THAN REUSING `register_surface_expansion`
    ----------------------------------------------------------------------
    A surface expansion is *the parent's generator on a different symbol*; a threshold variant
    is *the parent's generator on the parent's own symbols with different discretizer
    constants*. `register_surface_expansion` demands a `symbol` and a `timeframe` and writes a
    `basis_note` saying "the book has never traded <symbol> on this rule" — both of which are
    false for a threshold variant, whose surface is exactly the parent's.

    WHY THE STAMP IS STILL `TRANSFERRED_CLASS` AND NOT THE PARENT'S OWN RECALL
    -------------------------------------------------------------------------
    This is the part that matters and it is the conservative direction. A relaxed threshold
    fires on a SUPERSET of the parent's bars, and the extra bars were never observed live — so
    a parent's `MEASURED_DIRECT` / `MEASURED_LINEAGE_MATCHED` recall, which is a statement
    about the parent's own live decisions, does not cover them. What transfers is the
    structural CLASS rate: a claim about the code path, which the variant shares byte for byte
    apart from the constants.

    For a parent already stamped `TRANSFERRED_CLASS` this grants numerically the same record it
    already has, so there is no relaxation of any kind — which is the case for the sleeve this
    was written for (`sub_xvol_pullback`, `per_bar` / `transferred_class`, recall 0.9581).

    Three guards, the same three the surface registrar uses:

      * the parent must be in the AUTHORED register, so a variant cannot inherit from nothing;
      * `member` must carry `THRESHOLD_VARIANT_PREFIX`, so it can never shadow a production
        sleeve;
      * an authored entry is never overwritten.

    And one more, specific to this registrar: `params` must actually DIFFER from
    `production_params`. A "variant" identical to production is not a variant, and minting a
    second fidelity record under a second name for the same rule would let one hypothesis be
    counted as two — the mirror image of the double-count `CANDIDATE_FAMILY_V1.json` closed.
    """
    if not member.startswith(THRESHOLD_VARIANT_PREFIX):
        raise ValueError(
            f"threshold-variant member names must start with "
            f"{THRESHOLD_VARIANT_PREFIX!r} so they cannot be confused with a production "
            f"sleeve; got {member!r}"
        )
    _check_process_local_measurement_slot(member)
    par = FIDELITY_REGISTER.get(parent)
    if par is None:
        raise ValueError(
            f"unknown parent sleeve {parent!r}: a threshold variant inherits a structural "
            f"class from an authored sleeve and there is no record for that one"
        )
    totals = _CLASS_TOTALS.get(par.cls)
    if totals is None:
        raise ValueError(
            f"parent {parent!r} is class {par.cls.value}, which has no measured class rate; "
            f"nothing to transfer"
        )
    moved = {k: (production_params.get(k), v) for k, v in sorted(params.items())
             if production_params.get(k) != v}
    if not moved:
        raise ValueError(
            f"threshold variant {member!r} carries params identical to {parent!r}'s "
            f"production params. That is not a variant; registering it would let one "
            f"hypothesis be counted as two."
        )
    agreed, live_only = totals
    full = (
        f"THRESHOLD VARIANT of {parent} on {parent}'s OWN symbol surface. The generator is "
        f"{parent}'s own function with discretizer constants moved: "
        + ", ".join(f"{k} {a!r}->{b!r}" for k, (a, b) in moved.items())
        + f". Fidelity is TRANSFERRED from the {par.cls.value} class rate "
          f"({agreed} agreed / {live_only} live-only) and NOT from {parent}'s own live recall: "
          f"a relaxed threshold fires on a SUPERSET of the parent's bars and the extra bars "
          f"were never observed live, so the parent's own recall does not cover them. "
          f"Parent's own basis: {par.basis_note}"
        + ((" " + note) if note else "")
    )
    if par.cls in _LINEAGE_MATCHED_CLASSES:
        full += f" The class rate is {_LINEAGE_CAVEAT}."
    if par.cls is FidelityClass.PER_BAR:
        full += " " + _PER_BAR_DECOMPOSITION + "."
    rec = Fidelity(
        sleeve=member,
        cls=par.cls,
        basis=FidelityBasis.TRANSFERRED_CLASS,
        live_recall=agreed / (agreed + live_only),
        basis_agreed=agreed,
        basis_live_only=live_only,
        basis_note=full,
    )
    _SURFACE_EXPANSIONS[member] = rec
    return rec


def register_surface_expansion(
    member: str,
    *,
    parent: str,
    symbol: str,
    timeframe: str,
    surface_note: str = "",
) -> Fidelity:
    """Give a symbol-expanded member of `parent`'s rule a fidelity record. Session AF.

    WHY THIS EXISTS, AND WHY IT IS NOT A RELAXATION
    ------------------------------------------------
    `FOURTH_REVIEW.md` §5.4 asks that every mechanism surviving anywhere be run across the
    whole archive surface, judged as a family. Every such member is generated by *literally
    the parent's generator function* on a different symbol (and sometimes a different
    timeframe) — no new code, no new rule. `fidelity_for` keys on the sleeve NAME, so those
    members fail closed as UNKNOWN and the gate refuses them, which would make the family
    question unanswerable for a reason that has nothing to do with fidelity.

    What this function grants is exactly the treatment the fifteen authored `mx_*` sleeves
    already get from `_STRUCTURE_BY_CODE`: **the parent's structural CLASS rate, stamped
    TRANSFERRED_CLASS**, with the parent named. It never grants a parent's own
    MEASURED_DIRECT recall — that measurement is about the parent's symbol on the parent's
    38 live days, and a symbol this book has never traded has no live record to be measured
    against. Three guards keep it from becoming a back door:

      * the parent must already be in the authored register, so a member cannot inherit
        from nothing;
      * the member name must carry `EXPANSION_PREFIX`, so an expansion can never be
        mistaken for — or silently shadow — a production sleeve;
      * an authored entry is never overwritten.

    The residual honestly stated: **a surface-expanded member has no live record at all.**
    Its ceiling is the class rate, which is a statement about the code path's structure, not
    about this symbol. That sentence is put in `basis_note` so it travels into every verdict.
    """
    if not member.startswith(SURFACE_EXPANSION_PREFIXES):
        raise ValueError(
            f"surface-expansion member names must start with one of "
            f"{SURFACE_EXPANSION_PREFIXES} so they cannot be confused with a production sleeve "
            f"— nor with a threshold variant, which is a different claim and has its own "
            f"registrar; got {member!r}"
        )
    _check_process_local_measurement_slot(member)
    par = FIDELITY_REGISTER.get(parent)
    if par is None:
        raise ValueError(
            f"unknown parent sleeve {parent!r}: a surface expansion inherits a structural "
            f"class from an authored sleeve and there is no record for that one"
        )
    totals = _CLASS_TOTALS.get(par.cls)
    if totals is None:
        raise ValueError(
            f"parent {parent!r} is class {par.cls.value}, which has no measured class rate; "
            f"nothing to transfer"
        )
    agreed, live_only = totals
    note = (
        f"SURFACE EXPANSION of {parent} onto {symbol} at {timeframe}. The generator is "
        f"{parent}'s own function, unchanged; only the symbol surface differs"
        f"{(' — ' + surface_note) if surface_note else ''}. Fidelity is TRANSFERRED from the "
        f"{par.cls.value} class rate ({agreed} agreed / {live_only} live-only). "
        f"THIS MEMBER HAS NO LIVE RECORD OF ITS OWN: the book has never traded {symbol} on "
        f"this rule, so no live-recall figure for it can exist and the class rate is a claim "
        f"about the code path's structure, not about this symbol. Parent's own basis: "
        f"{par.basis_note}"
    )
    if par.cls in _LINEAGE_MATCHED_CLASSES:
        note += f" The class rate is {_LINEAGE_CAVEAT}."
    if par.cls is FidelityClass.PER_BAR:
        note += " " + _PER_BAR_DECOMPOSITION + "."
    rec = Fidelity(
        sleeve=member,
        cls=par.cls,
        basis=FidelityBasis.TRANSFERRED_CLASS,
        live_recall=agreed / (agreed + live_only),
        basis_agreed=agreed,
        basis_live_only=live_only,
        basis_note=note,
    )
    _SURFACE_EXPANSIONS[member] = rec
    return rec


def clear_surface_expansions() -> int:
    """Drop every registered surface expansion. Returns how many went."""
    n = len(_SURFACE_EXPANSIONS)
    _SURFACE_EXPANSIONS.clear()
    return n


def surface_expansions() -> dict[str, Fidelity]:
    """The registered surface expansions, by member name."""
    return dict(_SURFACE_EXPANSIONS)


def fidelity_for(sleeve: str) -> Fidelity:
    """The fidelity record for a sleeve. Unknown sleeves fail closed as UNMEASURED."""
    hit = (
        FIDELITY_REGISTER.get(sleeve)
        or _DIRECT_MEASUREMENTS.get(sleeve)
        or _SURFACE_EXPANSIONS.get(sleeve)
    )
    if hit is not None:
        return hit
    return Fidelity(
        sleeve=sleeve,
        cls=FidelityClass.UNKNOWN,
        basis=FidelityBasis.UNMEASURED,
        live_recall=None,
        basis_agreed=None,
        basis_live_only=None,
        basis_note=(
            "not in K1's measured set and its generator structure has not been read into "
            "this register. Add it here, with a file:line citation, before scoring it."
        ),
    )

"""The acceptance test: is the fast lane's answer the frozen lane's answer?

"R-identical" means the per-trade R series, the order/trade/scorecard ledgers
and the missed-outcome diagnostic aggregates reproduce to the artifact's own
precision. Timing fields and evidence-layer internals may differ, and every
field excluded on that ground is **named in the receipt** -- an exclusion list
you cannot read is indistinguishable from a comparator that passes everything.

Two lessons from earlier sessions are wired in rather than remembered:

* **nan-aware** (AN, AQ): ``float('nan') != float('nan')``, so a naive ``==``
  reports two identical NaN-bearing series as different, and a naive
  ``a != b -> fail`` reports a NaN that appeared out of nowhere as a pass.
  Both directions are handled explicitly.
* **silent nulls fall loudly** (wave-10 rule): a key present on one side and
  absent on the other is a DIFFERENCE, never a skip; and a comparison that
  finds zero rows on both sides reports ``EMPTY``, never ``IDENTICAL``.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Fields whose divergence is expected and economically inert. Everything here
# is either a clock reading or an evidence-layer internal that the fast lane is
# allowed to produce differently.
EXCLUDED_FIELD_SUFFIXES = (
    "_seconds",
    "_elapsed",
    "_wall_clock",
    "_generated_at",
    "_run_id",
)
EXCLUDED_FIELDS = frozenset(
    {
        "economic_hot_path_seconds",
        "proof_finalization_seconds",
        "run_started_at_utc",
        "run_completed_at_utc",
        "elapsed_seconds",
        "host",
        "pid",
    }
)

_MISSING = object()

# The output prefix is stamped INSIDE row values, not only into filenames:
# `campaign`, `package_replay_order_executable_bound_order_id`, and every id
# derived from them carry it. Two runs cannot share a prefix -- the engine
# requires a fresh output namespace (`configure_output_namespace`, "must_be_new")
# -- so a literal comparison of two runs of the same arm reports hundreds of
# differences that are pure naming. Normalising the prefix to a placeholder is
# what makes the comparison about economics; NOT normalising it would make the
# comparator useless, and normalising too much would make it dishonest, so the
# substitution is exact, case-insensitive, and reported in the receipt.
RUN_NAMESPACE_PLACEHOLDER = "<RUN_NAMESPACE>"

# A short prefix is a substring of everything. Normalising `"a"` would rewrite
# every `a` in every 64-hex digest and make two different digests compare EQUAL
# -- the comparator masking exactly what it exists to find. The engine's own
# prefix rule requires `_B7_5_` in the name, so a real prefix is always long;
# anything shorter than this is refused and the refusal is reported.
MIN_RUN_NAMESPACE_PREFIX_LEN = 8


def usable_run_namespace_prefixes(
    prefixes: "tuple[str, ...]",
) -> "tuple[tuple[str, ...], tuple[str, ...]]":
    """Split candidate prefixes into (usable, too_short_to_be_safe)."""

    usable = tuple(p for p in prefixes if len(p) >= MIN_RUN_NAMESPACE_PREFIX_LEN)
    rejected = tuple(p for p in prefixes if len(p) < MIN_RUN_NAMESPACE_PREFIX_LEN)
    return usable, rejected


def normalise_run_namespace(value: Any, prefixes: "tuple[str, ...]") -> Any:
    """Replace each run's own output prefix with a fixed placeholder."""

    if not prefixes or not isinstance(value, str):
        return value
    lowered = value.lower()
    for prefix in prefixes:
        if prefix and prefix in lowered:
            # Rebuild case-insensitively without regex so no metacharacter in a
            # prefix can change what is matched.
            out: list[str] = []
            index = 0
            while True:
                found = lowered.find(prefix, index)
                if found < 0:
                    out.append(value[index:])
                    break
                out.append(value[index:found])
                out.append(RUN_NAMESPACE_PLACEHOLDER)
                index = found + len(prefix)
            value = "".join(out)
            lowered = value.lower()
    return value


@dataclass
class Difference:
    path: str
    left: Any
    right: Any
    kind: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "left": _safe(self.left),
            "right": _safe(self.right),
            "kind": self.kind,
        }


def _safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if value is _MISSING:
        return "<absent>"
    if isinstance(value, (dict, list)) and len(value) > 12:
        return f"<{type(value).__name__} len={len(value)}>"
    return value


_SHA256_TEXT = re.compile(r"^[0-9a-f]{64}$")


def is_digest_difference(difference: Difference) -> bool:
    """Both sides are 64-hex, i.e. a provenance digest rather than a quantity.

    A digest whose preimage embeds the run's own output namespace CANNOT match
    across two runs, because the engine refuses to reuse an output namespace.
    Classifying these separately is only honest if the classification is
    *verified by a control* -- frozen-vs-frozen under two prefixes -- which is
    why the receipt carries the control's signature next to the fast lane's.
    """

    return (
        isinstance(difference.left, str)
        and isinstance(difference.right, str)
        and bool(_SHA256_TEXT.match(difference.left))
        and bool(_SHA256_TEXT.match(difference.right))
    )


@dataclass
class ComparisonResult:
    verdict: str
    compared_rows: int
    differences: list[Difference] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def digest_differences(self) -> list[Difference]:
        return [d for d in self.differences if is_digest_difference(d)]

    @property
    def quantity_differences(self) -> list[Difference]:
        return [d for d in self.differences if not is_digest_difference(d)]

    def signature(self) -> dict[str, int]:
        """Which field names differ, and how often -- the comparable fingerprint."""

        counts: dict[str, int] = {}
        for difference in self.differences:
            field_name = difference.path.split(".", 1)[-1]
            counts[field_name] = counts.get(field_name, 0) + 1
        return dict(sorted(counts.items()))

    def as_dict(self, max_differences: int = 40) -> dict[str, Any]:
        quantities = self.quantity_differences
        return {
            "verdict": self.verdict,
            "compared_rows": self.compared_rows,
            "difference_count": len(self.differences),
            "provenance_digest_difference_count": len(self.digest_differences),
            "quantity_difference_count": len(quantities),
            "difference_signature": self.signature(),
            "differences": [d.as_dict() for d in self.differences[:max_differences]],
            "quantity_differences": [d.as_dict() for d in quantities[:max_differences]],
            "notes": self.notes,
            "excluded_fields": sorted(EXCLUDED_FIELDS),
            "excluded_field_suffixes": list(EXCLUDED_FIELD_SUFFIXES),
        }


def is_excluded(key: str) -> bool:
    return key in EXCLUDED_FIELDS or key.endswith(EXCLUDED_FIELD_SUFFIXES)


def values_equal(left: Any, right: Any, *, rel_tol: float = 0.0) -> bool:
    """Exact by default; nan-aware in both directions.

    ``rel_tol`` of 0.0 means bit-for-bit for floats, which is what an identity
    claim needs. A non-zero tolerance downgrades the verdict to
    ECONOMICALLY_IDENTICAL and is reported as such.
    """

    if left is _MISSING or right is _MISSING:
        return False
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, float) or isinstance(right, float):
        try:
            left_f = float(left)
            right_f = float(right)
        except (TypeError, ValueError):
            return left == right
        left_nan = math.isnan(left_f)
        right_nan = math.isnan(right_f)
        if left_nan or right_nan:
            # Both NaN is equality; exactly one NaN is a real difference and
            # must not be swallowed.
            return left_nan and right_nan
        if math.isinf(left_f) or math.isinf(right_f):
            return left_f == right_f
        if rel_tol <= 0.0:
            return left_f == right_f
        return math.isclose(left_f, right_f, rel_tol=rel_tol, abs_tol=0.0)
    return left == right


def _compare_value(
    left: Any,
    right: Any,
    path: str,
    out: list[Difference],
    rel_tol: float,
    limit: int,
) -> None:
    if len(out) >= limit:
        return
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            if is_excluded(key):
                continue
            _compare_value(
                left.get(key, _MISSING),
                right.get(key, _MISSING),
                f"{path}.{key}" if path else key,
                out,
                rel_tol,
                limit,
            )
        return
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            out.append(
                Difference(path, f"len={len(left)}", f"len={len(right)}", "length")
            )
            return
        for index, (l_item, r_item) in enumerate(zip(left, right)):
            _compare_value(l_item, r_item, f"{path}[{index}]", out, rel_tol, limit)
        return
    if left is _MISSING or right is _MISSING:
        out.append(Difference(path, left, right, "absent_on_one_side"))
        return
    if not values_equal(left, right, rel_tol=rel_tol):
        out.append(Difference(path, left, right, "value"))


def compare_ledger(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    *,
    name: str,
    rel_tol: float = 0.0,
    limit: int = 200,
) -> list[Difference]:
    out: list[Difference] = []
    if len(left_rows) != len(right_rows):
        out.append(
            Difference(
                name, f"rows={len(left_rows)}", f"rows={len(right_rows)}", "row_count"
            )
        )
        return out
    for index, (left, right) in enumerate(zip(left_rows, right_rows)):
        _compare_value(left, right, f"{name}[{index}]", out, rel_tol, limit)
        if len(out) >= limit:
            break
    return out


def _normalise_payload(node: Any, prefixes: "tuple[str, ...]") -> Any:
    if isinstance(node, dict):
        return {key: _normalise_payload(value, prefixes) for key, value in node.items()}
    if isinstance(node, list):
        return [_normalise_payload(item, prefixes) for item in node]
    return normalise_run_namespace(node, prefixes)


def compare_economics(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    rel_tol: float = 0.0,
) -> ComparisonResult:
    """Compare two ``bench.extract_economics`` payloads."""

    differences: list[Difference] = []
    notes: list[str] = []

    declared = tuple(
        str(side.get("output_prefix") or "").lower()
        for side in (left, right)
        if str(side.get("output_prefix") or "").strip()
    )
    prefixes, too_short = usable_run_namespace_prefixes(declared)
    if too_short:
        notes.append(
            f"run-namespace prefixes {sorted(set(too_short))} are shorter than "
            f"{MIN_RUN_NAMESPACE_PREFIX_LEN} chars and were NOT normalised -- a "
            "short prefix is a substring of every digest and would mask real "
            "differences"
        )
    if prefixes:
        notes.append(
            "run-namespace prefixes normalised to "
            f"{RUN_NAMESPACE_PLACEHOLDER}: {sorted(set(prefixes))}"
        )
        left = _normalise_payload(left, prefixes)
        right = _normalise_payload(right, prefixes)
    elif not declared:
        notes.append(
            "no output_prefix recorded on either side -- run-namespace tokens "
            "embedded in row values were NOT normalised"
        )

    left_counts = left.get("counts", {})
    right_counts = right.get("counts", {})
    for key in sorted(set(left_counts) | set(right_counts)):
        if left_counts.get(key) != right_counts.get(key):
            differences.append(
                Difference(
                    f"counts.{key}",
                    left_counts.get(key, _MISSING),
                    right_counts.get(key, _MISSING),
                    "row_count",
                )
            )

    # The digests cover every field of every row, including the nested
    # provenance the pruned rows drop. Compare them FIRST: a digest mismatch is
    # the strongest possible statement that something moved, even when the
    # pruned scalar comparison below finds nothing.
    left_digests = left.get("ledger_digests", {})
    right_digests = right.get("ledger_digests", {})
    if left_digests or right_digests:
        for key in sorted(set(left_digests) | set(right_digests)):
            if left_digests.get(key) != right_digests.get(key):
                differences.append(
                    Difference(
                        f"ledger_digests.{key}",
                        left_digests.get(key, _MISSING),
                        right_digests.get(key, _MISSING),
                        "ledger_digest",
                    )
                )
    else:
        notes.append(
            "no ledger digests on either side -- nested fields were NOT compared"
        )

    _compare_value(
        left.get("summary_economics", {}),
        right.get("summary_economics", {}),
        "summary_economics",
        differences,
        rel_tol,
        200,
    )

    compared = 0
    for ledger in ("trades", "orders", "scorecards"):
        left_rows = left.get(ledger, [])
        right_rows = right.get(ledger, [])
        compared += max(len(left_rows), len(right_rows))
        differences.extend(
            compare_ledger(left_rows, right_rows, name=ledger, rel_tol=rel_tol)
        )

    left_missed = left.get("missed_digest", {})
    right_missed = right.get("missed_digest", {})
    _compare_value(left_missed, right_missed, "missed_digest", differences, rel_tol, 200)

    if compared == 0 and not left_missed.get("rows") and not right_missed.get("rows"):
        return ComparisonResult(
            verdict="EMPTY",
            compared_rows=0,
            differences=differences,
            notes=["both sides produced no economic rows -- nothing was proved"],
        )

    if differences and all(is_digest_difference(d) for d in differences):
        # Every difference is a 64-hex provenance digest and no quantity moved.
        # This is NOT an acceptance on its own: it is only meaningful against a
        # frozen-vs-frozen control that produces the same signature.
        verdict = "PROVENANCE_DIGESTS_ONLY"
        notes.append(
            f"{len(differences)} differences, all 64-hex provenance digests; "
            "0 quantities moved. Requires a frozen-vs-frozen control with the "
            "same signature before it counts as reproduction."
        )
    elif differences:
        verdict = "DIVERGENT"
    elif rel_tol > 0.0:
        verdict = "ECONOMICALLY_IDENTICAL"
        notes.append(f"compared with rel_tol={rel_tol}, not bit-for-bit")
    else:
        verdict = "R_IDENTICAL"

    return ComparisonResult(
        verdict=verdict,
        compared_rows=compared,
        differences=differences,
        notes=notes,
    )


def compare_files(left_path: Path, right_path: Path, *, rel_tol: float = 0.0) -> dict[str, Any]:
    left = json.loads(Path(left_path).read_text())
    right = json.loads(Path(right_path).read_text())
    result = compare_economics(left, right, rel_tol=rel_tol)
    return {
        "left": str(left_path),
        "right": str(right_path),
        **result.as_dict(),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--rel-tol", type=float, default=0.0)
    parser.add_argument("--out", default=None)
    ns = parser.parse_args()

    report = compare_files(Path(ns.left), Path(ns.right), rel_tol=ns.rel_tol)
    text = json.dumps(report, indent=1, default=str)
    if ns.out:
        Path(ns.out).write_text(text)
    print(text)
    return 0 if report["verdict"] in {"R_IDENTICAL", "ECONOMICALLY_IDENTICAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

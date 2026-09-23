"""Account/symbol entry slippage in price units from reconciled broker fills."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.costs.artifact_authority import (
    CostInputAuthorityError,
    DEFAULT_COST_INPUTS_MANIFEST,
    read_current_file_bytes,
    verify_cost_input,
)
from src.costs.coverage import Coverage
from src.costs.symbols import PROFILE_PATHS, canonical_symbol_for_account

__all__ = [
    "DEFAULT_SLIPPAGE_ARTIFACT",
    "SlippageEstimate",
    "SlippageModel",
    "SlippageModelError",
    "load_slippage_model",
]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SLIPPAGE_ARTIFACT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/cost/SLIPPAGE_PRICE_V1.json"
)


class SlippageModelError(RuntimeError):
    """No same-account, same-profile-symbol slippage sample can decide the cost."""


@dataclass(frozen=True)
class SlippageEstimate:
    account: str
    canonical_symbol: str
    expected_adverse_price: float
    coverage: Coverage
    n: int
    provenance: str
    detail: dict
    artifact_sha256: str | None = None
    manifest_sha256: str | None = None


class SlippageModel:
    def __init__(
        self,
        doc: dict,
        source: Path | None = None,
        *,
        artifact_sha256: str | None = None,
        manifest_path: Path | None = None,
        manifest_sha256: str | None = None,
    ):
        if doc.get("schema") != "gtos.costs.slippage_price.v1":
            raise SlippageModelError(f"unsupported slippage schema {doc.get('schema')!r}")
        self.doc = doc
        self.source = source
        self.artifact_sha256 = artifact_sha256
        self.manifest_path = manifest_path
        self.manifest_sha256 = manifest_sha256
        self._verify_profile_authority()

    def _verify_profile_authority(self) -> None:
        bound = self.doc.get("profile_symbol_authority") or {}
        if set(bound) != set(PROFILE_PATHS):
            raise SlippageModelError(
                "slippage symbol authority must bind exactly both live profiles; "
                f"declared={sorted(bound)}, runtime={sorted(PROFILE_PATHS)}"
            )
        for account, path in PROFILE_PATHS.items():
            binding = bound.get(account) or {}
            expected = binding.get("sha256")
            declared = binding.get("path")
            if (
                not isinstance(declared, str)
                or not declared
                or "\\" in declared
                or Path(declared).is_absolute()
                or ".." in Path(declared).parts
                or (REPO / declared).resolve() != path.resolve()
            ):
                raise SlippageModelError(
                    f"slippage symbol authority path mismatch for {account}: artifact "
                    f"binds {declared!r}, runtime profile is {path}"
                )
            try:
                actual = read_current_file_bytes(
                    path, label=f"slippage profile authority for {account}"
                ).sha256
            except CostInputAuthorityError as exc:
                raise SlippageModelError(str(exc)) from exc
            if expected != actual:
                raise SlippageModelError(
                    f"slippage symbol authority drift for {account}: artifact binds "
                    f"{expected!r}, current profile is {actual}; rebuild the offline input "
                    "before resolving aliases"
                )

    def estimate(self, account: str, symbol: str) -> SlippageEstimate:
        # The parsed artifact may be cached by its verified bytes.  Recheck its
        # separately bound live-profile inputs before every lookup so an accepted model
        # cannot survive later profile drift.
        self._verify_profile_authority()
        canonical = canonical_symbol_for_account(account, symbol)
        if canonical is None:
            raise SlippageModelError(
                f"{symbol!r} is not an exact symbol in either authoritative live profile; "
                "NOT_EVALUABLE"
            )
        rec = ((self.doc.get("records") or {}).get(account) or {}).get(canonical)
        if rec is None:
            raise SlippageModelError(
                f"no reconciled price-domain slippage sample for {canonical} on {account}; "
                f"NOT_EVALUABLE. Capture requirement: {self.doc.get('capture_requirement')}"
            )
        value = float(rec["expected_adverse_price"])
        n = int(rec["n"])
        if not math.isfinite(value) or value < 0 or n <= 0:
            raise SlippageModelError(
                f"invalid slippage record for {canonical} on {account}: value={value!r}, n={n}"
            )
        coverage = Coverage(rec["coverage"])
        return SlippageEstimate(
            account=account,
            canonical_symbol=canonical,
            expected_adverse_price=value,
            coverage=coverage,
            n=n,
            provenance=(
                f"{self.source or DEFAULT_SLIPPAGE_ARTIFACT}:{account}/{canonical}; "
                f"source sha256 {self.doc['source_sha256']}"
                + (
                    f"; compact artifact sha256 {self.artifact_sha256}; manifest "
                    f"{self.manifest_path} sha256 {self.manifest_sha256}"
                    if self.artifact_sha256 is not None
                    else ""
                )
            ),
            detail={k: v for k, v in rec.items() if k not in {"coverage", "expected_adverse_price"}},
            artifact_sha256=self.artifact_sha256,
            manifest_sha256=self.manifest_sha256,
        )


@lru_cache(maxsize=4)
def _parse_verified(
    path_str: str,
    manifest_path_str: str,
    manifest_sha256: str,
    artifact_sha256: str,
    data: bytes,
) -> SlippageModel:
    try:
        doc = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SlippageModelError(
            f"manifest-bound slippage input at {path_str} is not valid JSON"
        ) from exc
    return SlippageModel(
        doc,
        source=Path(path_str),
        artifact_sha256=artifact_sha256,
        manifest_path=Path(manifest_path_str),
        manifest_sha256=manifest_sha256,
    )


def load_slippage_model(
    path: Path | str | None = None,
    *,
    manifest_path: Path | str | None = None,
    authority_root: Path | str | None = None,
) -> SlippageModel:
    """Load only current bytes matching the cost-input manifest."""

    try:
        verified = verify_cost_input(
            "slippage_price",
            path=path,
            manifest_path=manifest_path or DEFAULT_COST_INPUTS_MANIFEST,
            authority_root=authority_root,
        )
    except CostInputAuthorityError as exc:
        raise SlippageModelError(str(exc)) from exc
    model = _parse_verified(
        str(verified.path),
        str(verified.manifest_path),
        verified.manifest_sha256,
        verified.sha256,
        verified.data,
    )
    # Also run on a cache hit.  The artifact bytes may be unchanged while one of its
    # separately bound profile inputs has drifted.
    model._verify_profile_authority()
    return model

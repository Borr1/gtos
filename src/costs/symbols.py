"""Hash-bound, profile-owned symbol equivalence for cost evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection, Mapping
from functools import lru_cache
from pathlib import Path

import yaml
from yaml.constructor import ConstructorError
from yaml.resolver import BaseResolver

from src.costs.artifact_authority import (
    CostInputAuthorityError,
    read_current_file_bytes,
    verify_cost_input,
)

__all__ = [
    "DEFAULT_SYMBOL_AUTHORITY_MANIFEST",
    "PROFILE_PATHS",
    "ProfileSymbolAuthority",
    "SymbolAuthorityError",
    "canonical_symbol",
    "canonical_symbol_for_account",
    "profile_broker_symbols",
    "resolve_account_symbol",
]

REPO = Path(__file__).resolve().parents[2]
PROFILE_PATHS = {
    "FTMO": REPO / "config/profiles/operator_profile.yaml",
    "redacted_account": REPO / "config/profiles/redacted_account.yaml",
}
DEFAULT_SYMBOL_AUTHORITY_MANIFEST = Path(__file__).with_name("SYMBOL_AUTHORITY_V1.json")


class SymbolAuthorityError(RuntimeError):
    """The live profile bytes no longer match the authority used by cost evidence."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses duplicate mapping keys before overwrite."""


def _construct_unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    seen = set()
    for key_node, _value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in seen
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


class ProfileSymbolAuthority:
    """Verified live-profile mappings, with injectable paths for adversarial tests."""

    def __init__(
        self,
        manifest_path: Path | str | None = None,
        profile_paths: Mapping[str, Path | str] = PROFILE_PATHS,
        *,
        profile_root: Path | str | None = None,
    ):
        # ``None`` means production authority: the symbol manifest itself must first
        # match COST_INPUTS_MANIFEST_V1.  A path is an explicit injected authority,
        # used by focused adversarial tests/offline construction.
        self.manifest_path = Path(manifest_path) if manifest_path is not None else None
        self.profile_paths = {k: Path(v) for k, v in profile_paths.items()}
        self.profile_root = Path(profile_root) if profile_root is not None else None
        self._mappings: dict[str, dict[str, str]] | None = None
        self._fingerprint: tuple[str, tuple[tuple[str, str], ...]] | None = None

    def mappings(self) -> dict[str, dict[str, str]]:
        if self.manifest_path is None:
            try:
                verified = verify_cost_input("symbol_authority")
            except CostInputAuthorityError as exc:
                raise SymbolAuthorityError(str(exc)) from exc
            manifest_bytes = verified.data
            manifest_source = verified.path
            declared_root = REPO
            outer_profiles = (
                (verified.manifest.get("source_scope") or {}).get(
                    "profile_symbol_authority"
                )
                or {}
            )
        else:
            manifest_source = self.manifest_path
            declared_root = self.profile_root or manifest_source.parent
            outer_profiles = None
            if not manifest_source.is_file():
                raise SymbolAuthorityError(
                    f"symbol authority manifest missing at {manifest_source}; alias "
                    "resolution is NOT_EVALUABLE"
                )
            try:
                manifest_bytes = read_current_file_bytes(
                    manifest_source, label="injected symbol authority manifest"
                ).data
            except CostInputAuthorityError as exc:
                raise SymbolAuthorityError(str(exc)) from exc
        try:
            manifest = json.loads(manifest_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SymbolAuthorityError(
                f"symbol authority manifest is not valid JSON at {manifest_source}"
            ) from exc
        if not isinstance(manifest, dict) or manifest.get(
            "schema"
        ) != "gtos.costs.symbol_authority.v1":
            got = manifest.get("schema") if isinstance(manifest, dict) else type(manifest).__name__
            raise SymbolAuthorityError(
                f"unsupported symbol authority schema {got!r}"
            )
        bound = manifest.get("profiles") or {}
        if not isinstance(bound, dict):
            raise SymbolAuthorityError("symbol authority profiles must be a mapping")
        if set(bound) != set(self.profile_paths):
            raise SymbolAuthorityError(
                "symbol authority must declare exactly the injected account profiles; "
                f"declared={sorted(bound)}, runtime={sorted(self.profile_paths)}"
            )
        if outer_profiles is not None and bound != outer_profiles:
            raise SymbolAuthorityError(
                "symbol authority profile rows do not exactly equal the profile rows in "
                "COST_INPUTS_MANIFEST_V1; NOT_EVALUABLE"
            )
        profile_payloads: dict[str, bytes] = {}
        actual_hashes: list[tuple[str, str]] = []
        out: dict[str, dict[str, str]] = {}
        for account, path in self.profile_paths.items():
            binding = bound.get(account) or {}
            expected = binding.get("sha256")
            declared = binding.get("path")
            if (
                not isinstance(declared, str)
                or not declared
                or "\\" in declared
                or Path(declared).is_absolute()
                or ".." in Path(declared).parts
            ):
                raise SymbolAuthorityError(
                    f"profile symbol authority has unsafe path for {account}: {declared!r}"
                )
            try:
                declared_path = (declared_root / declared).resolve(strict=True)
                actual_path = path.resolve(strict=True)
            except (FileNotFoundError, OSError) as exc:
                raise SymbolAuthorityError(
                    f"profile authority missing for {account}: {path}"
                ) from exc
            try:
                declared_path.relative_to(declared_root.resolve(strict=True))
            except ValueError:
                raise SymbolAuthorityError(
                    f"profile authority path escapes its declared root for {account}: "
                    f"{declared_path}"
                ) from None
            if actual_path != declared_path:
                raise SymbolAuthorityError(
                    f"runtime profile path for {account} is {actual_path}, but symbol "
                    f"authority declares {declared_path}; NOT_EVALUABLE"
                )
            if not path.is_file():
                raise SymbolAuthorityError(f"profile authority missing for {account}: {path}")
            try:
                current = read_current_file_bytes(
                    path, label=f"profile authority for {account}"
                )
            except CostInputAuthorityError as exc:
                raise SymbolAuthorityError(str(exc)) from exc
            payload = current.data
            actual = current.sha256
            if expected != actual:
                raise SymbolAuthorityError(
                    f"profile symbol authority drift for {account}: manifest binds "
                    f"{expected!r}, current profile is {actual}; rebuild the offline cost "
                    "inputs before resolving aliases"
                )
            profile_payloads[account] = payload
            actual_hashes.append((account, actual))

        fingerprint = (
            hashlib.sha256(manifest_bytes).hexdigest(), tuple(sorted(actual_hashes))
        )
        # Hash every current byte before consulting the retained parse.  This gives
        # repeated calls the speed of a cache without allowing pathname-only cache keys
        # to survive profile or manifest drift.
        if self._mappings is not None and self._fingerprint == fingerprint:
            return self._mappings
        canonical_case_owner: dict[str, str] = {}
        alias_owner: dict[str, dict[str, str]] = {}
        for account, payload in profile_payloads.items():
            try:
                doc = yaml.load(payload, Loader=_UniqueKeyLoader) or {}
            except yaml.YAMLError as exc:
                raise SymbolAuthorityError(
                    f"profile authority YAML is ambiguous or invalid for {account}: {exc}"
                ) from exc
            for canonical, block in (doc.get("instruments") or {}).items():
                canonical = str(canonical)
                folded = canonical.casefold()
                prior_canonical = canonical_case_owner.get(folded)
                if prior_canonical is not None and prior_canonical != canonical:
                    raise SymbolAuthorityError(
                        "case-normalized canonical ambiguity across live profiles: "
                        f"{prior_canonical!r} and {canonical!r}"
                    )
                canonical_case_owner[folded] = canonical
                symbol = ((block or {}).get("market") or {}).get("mt5_symbol")
                if isinstance(symbol, str) and symbol.strip():
                    alias = symbol.strip()
                    prior_alias = alias_owner.setdefault(account, {}).get(alias)
                    if prior_alias is not None and prior_alias != canonical:
                        raise SymbolAuthorityError(
                            f"within-account broker alias ambiguity in {account}: "
                            f"{alias!r} maps to both {prior_alias!r} and {canonical!r}"
                        )
                    alias_owner[account][alias] = canonical
                    out.setdefault(canonical, {})[account] = alias
        self._mappings = out
        self._fingerprint = fingerprint
        return out


@lru_cache(maxsize=1)
def _default_authority() -> ProfileSymbolAuthority:
    return ProfileSymbolAuthority()


def profile_broker_symbols(
    authority: ProfileSymbolAuthority | None = None,
) -> dict[str, dict[str, str]]:
    """``canonical -> account -> mt5_symbol`` after hash verification."""
    return (authority or _default_authority()).mappings()


def canonical_symbol(
    symbol: str,
    authority: ProfileSymbolAuthority | None = None,
) -> str | None:
    """Return the profile canonical name for an exact declared alias."""
    mappings = profile_broker_symbols(authority)
    if symbol in mappings:
        return symbol
    matches = {
        canonical
        for canonical, by_account in mappings.items()
        if symbol in by_account.values()
    }
    # The same broker spelling can legitimately name different canonicals on two
    # accounts, because account is part of the authoritative lookup.  A global lookup
    # has no such discriminator and therefore must refuse instead of taking YAML order.
    return next(iter(matches)) if len(matches) == 1 else None


def canonical_symbol_for_account(
    account: str,
    symbol: str,
    authority: ProfileSymbolAuthority | None = None,
) -> str | None:
    """Canonical identity for a canonical name or this account's exact broker alias."""
    mappings = profile_broker_symbols(authority)
    if symbol in mappings and account in mappings[symbol]:
        return symbol
    for canonical, by_account in mappings.items():
        if by_account.get(account) == symbol:
            return canonical
    return None


def resolve_account_symbol(
    account: str,
    symbol: str,
    available: Collection[str],
    authority: ProfileSymbolAuthority | None = None,
) -> str | None:
    """Resolve an exact declared alias to an available account key, or ``None``."""
    # There is deliberately no direct-membership or punctuation shortcut here. An
    # artifact may contain many historical symbols; membership in it does not grant a
    # symbol live-profile identity, and spelling similarity is not authority.
    mappings = profile_broker_symbols(authority)
    canonical = canonical_symbol_for_account(account, symbol, authority)
    if canonical is None:
        return None
    target = mappings[canonical].get(account)
    for candidate in (target, canonical):
        if candidate and candidate in available:
            return candidate
    return None

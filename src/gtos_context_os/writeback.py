"""Writeback proposal helpers for GTOS Context OS."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Sequence

from src.gtos_context_os.catalog import utc_now


DEFAULT_WRITEBACK_DIR = Path(".context/context_os/writeback_proposals")


def create_writeback_proposal(
    title: str,
    body: str,
    *,
    sources: Sequence[str] = (),
    repo: Path | str = ".",
    out_dir: Path | str = DEFAULT_WRITEBACK_DIR,
) -> Path:
    """Create a source-backed proposal, not an automatic memory mutation."""

    repo_path = Path(repo).resolve()
    target_dir = repo_path / out_dir if not Path(out_dir).is_absolute() else Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    payload: dict[str, Any] = {
        "schema_version": "gtos_context_writeback_proposal_v1",
        "generated_at_utc": generated_at,
        "title": title,
        "body": body,
        "sources": list(sources),
        "status": "proposal_only_not_canonical_memory",
        "promotion_rule": "human_or_route_owner_acceptance_required_before_memory_or_canonical_doc_update",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    name = f"{generated_at.replace(':', '').replace('-', '')}-{_slug(title)}-{digest}.json"
    path = target_dir / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:60] or "proposal"

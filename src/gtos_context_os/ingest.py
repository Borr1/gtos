"""Structured finding ingestion for Context OS continuity."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from src.gtos_context_os.second_brain import DEFAULT_SECOND_BRAIN_ROOT, capture_idea, distill_idea
from src.gtos_context_os.session import create_session_capsule


def ingest_finding(
    title: str,
    body: str,
    *,
    task: str = "",
    sources: Sequence[str] = (),
    commands: Sequence[str] = (),
    decisions: Sequence[str] = (),
    tags: Sequence[str] = (),
    repo: Path | str = ".",
    to_second_brain: bool = False,
    second_brain_root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
    reviewed: bool = False,
) -> dict[str, Any]:
    """Capture a subagent or session finding as bounded continuity intelligence."""

    capsule = create_session_capsule(
        title,
        body,
        task=task,
        sources=sources,
        commands=commands,
        decisions=decisions,
        repo=repo,
    )
    result: dict[str, Any] = {
        "schema_version": "gtos_context_ingested_finding_v1",
        "title": title,
        "task": task,
        "session_capsule": capsule.as_posix(),
        "second_brain_raw": None,
        "second_brain_card": None,
        "use_boundary": "ingested_finding_is_continuity_intelligence_verify_against_current_disk",
    }
    if to_second_brain:
        raw = capture_idea(
            body,
            title=title,
            tags=tags,
            source="context_os_ingest_finding",
            root=second_brain_root,
        )
        card = distill_idea(raw, root=second_brain_root, reviewed=reviewed)
        result["second_brain_raw"] = raw.as_posix()
        result["second_brain_card"] = card.as_posix()
    return result

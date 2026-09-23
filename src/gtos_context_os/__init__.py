"""GTOS Context OS sidecar utilities.

This package builds a local, read-only context catalog for GTOS agents.  It is
deliberately separate from replay/runtime code: the tools index files, search
them, and produce compact context packs, but they do not mutate trading state.
"""

from src.gtos_context_os.catalog import (
    CatalogBuildResult,
    StaleCatalogError,
    build_catalog,
    catalog_freshness,
    search_catalog,
)
from src.gtos_context_os.classifier import classify_path
from src.gtos_context_os.doctrine import doctrine_checklist
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.ingest import ingest_finding
from src.gtos_context_os.memory import search_memory
from src.gtos_context_os.pack import build_context_pack
from src.gtos_context_os.route import route_overview
from src.gtos_context_os.second_brain import (
    DEFAULT_SECOND_BRAIN_ROOT,
    capture_idea,
    distill_idea,
    generate_second_brain_graph,
    init_second_brain,
    search_second_brain,
    second_brain_distillation_queue,
    second_brain_status,
)
from src.gtos_context_os.resume import build_resume_bundle
from src.gtos_context_os.session import list_session_capsules, session_capsule_status
from src.gtos_context_os.session_state import (
    load_continuation_cursor,
    load_active_session_state,
    summarize_active_state_payload,
    summarize_continuation_cursor_payload,
    write_context_checkpoint,
    write_continuation_cursor,
    write_active_session_state,
)
from src.gtos_context_os.starter import build_starter_prompt

__all__ = [
    "CatalogBuildResult",
    "StaleCatalogError",
    "DEFAULT_SECOND_BRAIN_ROOT",
    "build_catalog",
    "build_context_pack",
    "build_starter_prompt",
    "catalog_freshness",
    "capture_idea",
    "classify_path",
    "context_intelligence_health",
    "distill_idea",
    "ingest_finding",
    "build_resume_bundle",
    "generate_second_brain_graph",
    "init_second_brain",
    "doctrine_checklist",
    "route_overview",
    "search_catalog",
    "search_memory",
    "search_second_brain",
    "second_brain_distillation_queue",
    "second_brain_status",
    "list_session_capsules",
    "load_continuation_cursor",
    "load_active_session_state",
    "session_capsule_status",
    "summarize_active_state_payload",
    "summarize_continuation_cursor_payload",
    "write_context_checkpoint",
    "write_continuation_cursor",
    "write_active_session_state",
]

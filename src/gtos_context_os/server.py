"""Read-only HTTP sidecar for GTOS Context OS."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from src.gtos_context_os.catalog import DEFAULT_DB_PATH, catalog_stats, search_catalog
from src.gtos_context_os.catalog import StaleCatalogError
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.memory import search_memory
from src.gtos_context_os.pack import build_context_pack, render_markdown_pack
from src.gtos_context_os.resume import build_resume_bundle
from src.gtos_context_os.route import route_overview
from src.gtos_context_os.second_brain import search_second_brain, second_brain_status
from src.gtos_context_os.session import list_session_capsules, session_capsule_status
from src.gtos_context_os.session_state import load_active_session_state, load_continuation_cursor
from src.gtos_context_os.symbols import search_symbols


def serve_context_os(
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Run a read-only local HTTP context sidecar."""

    repo_path = Path(repo).resolve()

    class Handler(ContextOSRequestHandler):
        context_repo = repo_path
        context_db_path = Path(db_path)

    server = ThreadingHTTPServer((host, port), Handler)
    server.serve_forever()


class ContextOSRequestHandler(BaseHTTPRequestHandler):
    context_repo = Path(".").resolve()
    context_db_path = DEFAULT_DB_PATH

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        status, content_type, body = handle_request(
            self.path,
            repo=self.context_repo,
            db_path=self.context_db_path,
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib API
        return


def handle_request(
    raw_path: str,
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
) -> tuple[int, str, bytes]:
    parsed = urlparse(raw_path)
    params = {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}
    try:
        if parsed.path == "/ping":
            return json_response({"status": "ok", "service": "gtos_context_os"})
        if parsed.path == "/stats":
            return json_response(catalog_stats(db_path=db_path, repo=repo))
        if parsed.path == "/health":
            return json_response(
                context_intelligence_health(
                    repo=repo,
                    db_path=db_path,
                    second_brain_root=params.get("second_brain_root"),
                    session_capsule_limit=int(params.get("session_capsule_limit", "5")),
                )
            )
        if parsed.path == "/search":
            query = required(params, "q")
            limit = int(params.get("limit", "12"))
            return json_response(search_catalog(query, db_path=db_path, repo=repo, limit=limit))
        if parsed.path == "/route":
            route = required(params, "route")
            limit = int(params.get("limit", "25"))
            return json_response(route_overview(route, db_path=db_path, repo=repo, limit=limit))
        if parsed.path == "/memory":
            query = required(params, "q")
            limit = int(params.get("limit", "8"))
            memory_root = params.get("memory_root")
            return json_response(search_memory(query, memory_root=memory_root, limit=limit))
        if parsed.path == "/second-brain/status":
            return json_response(second_brain_status(root=params.get("root")))
        if parsed.path == "/second-brain/search":
            query = required(params, "q")
            limit = int(params.get("limit", "10"))
            include_raw = params.get("include_raw", "").lower() in {"1", "true", "yes"}
            return json_response(
                search_second_brain(
                    query,
                    root=params.get("root"),
                    limit=limit,
                    include_raw=include_raw,
                )
            )
        if parsed.path == "/session-capsules":
            limit = int(params.get("limit", "5"))
            if params.get("status", "").lower() in {"1", "true", "yes"}:
                return json_response(session_capsule_status(repo=repo, limit=limit))
            return json_response(
                list_session_capsules(
                    repo=repo,
                    limit=limit,
                    task_query=params.get("task_query"),
                )
            )
        if parsed.path == "/active-state":
            return json_response(load_active_session_state(repo=repo))
        if parsed.path == "/cursor":
            return json_response(load_continuation_cursor(repo=repo))
        if parsed.path == "/symbols":
            query = required(params, "q")
            limit = int(params.get("limit", "20"))
            roots = tuple(params.get("roots", "src,scripts,tests").split(","))
            max_files = int(params.get("max_files", "5000"))
            max_file_bytes = int(params.get("max_file_bytes", "750000"))
            max_elapsed_seconds = float(params.get("max_elapsed_seconds", "5"))
            return json_response(
                search_symbols(
                    query,
                    repo=repo,
                    roots=roots,
                    limit=limit,
                    max_files=max_files,
                    max_file_bytes=max_file_bytes,
                    max_elapsed_seconds=max_elapsed_seconds,
                )
            )
        if parsed.path == "/resume":
            task = required(params, "task")
            profile = params.get("profile", "ultimate")
            route = params.get("route") or None
            limit = int(params.get("limit", "10"))
            include_memory = params.get("include_memory", "1").lower() in {"1", "true", "yes"}
            include_second_brain = params.get("include_second_brain", "1").lower() in {"1", "true", "yes"}
            second_brain_root = params.get("second_brain_root")
            write_capsule = params.get("write_capsule", "").lower() in {"1", "true", "yes"}
            return json_response(
                build_resume_bundle(
                    task,
                    repo=repo,
                    db_path=db_path,
                    limit=limit,
                    profile=profile,
                    route=route,
                    include_memory=include_memory,
                    include_second_brain=include_second_brain,
                    second_brain_root=second_brain_root,
                    write_capsule=write_capsule,
                )
            )
        if parsed.path == "/pack":
            task = required(params, "task")
            profile = params.get("profile", "standard")
            route = params.get("route") or None
            limit = int(params.get("limit", "10"))
            include_memory = params.get("include_memory", "").lower() in {"1", "true", "yes"}
            include_second_brain = params.get("include_second_brain", "").lower() in {"1", "true", "yes"}
            allow_stale = params.get("allow_stale", "1").lower() in {"1", "true", "yes"}
            auto_rebuild_stale = params.get("auto_rebuild_stale", "").lower() in {"1", "true", "yes"}
            include_health = params.get("include_health", "1").lower() in {"1", "true", "yes"}
            memory_root = params.get("memory_root")
            second_brain_root = params.get("second_brain_root")
            second_brain_query = params.get("second_brain_query")
            section_timeout_seconds = float(params.get("section_timeout_seconds", "8"))
            pack = build_context_pack(
                task,
                repo=repo,
                db_path=db_path,
                limit=limit,
                profile=profile,
                route=route,
                include_memory=include_memory,
                memory_root=memory_root,
                include_second_brain=include_second_brain,
                second_brain_root=second_brain_root,
                second_brain_query=second_brain_query,
                allow_stale=allow_stale,
                auto_rebuild_stale=auto_rebuild_stale,
                include_health=include_health,
                section_timeout_seconds=section_timeout_seconds,
            )
            if params.get("format") == "markdown":
                return 200, "text/markdown; charset=utf-8", render_markdown_pack(pack).encode("utf-8")
            return json_response(pack)
        if parsed.path == "/fast-pack":
            task = required(params, "task")
            profile = params.get("profile", "ultimate")
            route = params.get("route") or None
            limit = int(params.get("limit", "8"))
            include_memory = params.get("include_memory", "1").lower() in {"1", "true", "yes"}
            include_second_brain = params.get("include_second_brain", "").lower() in {"1", "true", "yes"}
            allow_stale = params.get("allow_stale", "1").lower() in {"1", "true", "yes"}
            section_timeout_seconds = float(params.get("section_timeout_seconds", "3"))
            pack = build_context_pack(
                task,
                repo=repo,
                db_path=db_path,
                limit=limit,
                profile=profile,
                route=route,
                include_memory=include_memory,
                memory_root=params.get("memory_root"),
                include_second_brain=include_second_brain,
                second_brain_root=params.get("second_brain_root"),
                second_brain_query=params.get("second_brain_query"),
                include_health=False,
                include_recent_capsules=True,
                allow_stale=allow_stale,
                auto_rebuild_stale=False,
                auto_build=False,
                section_timeout_seconds=section_timeout_seconds,
            )
            if params.get("format") == "markdown":
                return 200, "text/markdown; charset=utf-8", render_markdown_pack(pack).encode("utf-8")
            return json_response(pack)
        return json_response({"error": "not_found", "path": parsed.path}, status=404)
    except ValueError as exc:
        return json_response({"error": "bad_request", "message": str(exc)}, status=400)
    except StaleCatalogError as exc:
        return json_response({"error": "stale_catalog", "message": str(exc)}, status=409)


def required(params: dict[str, str], key: str) -> str:
    value = params.get(key)
    if not value:
        raise ValueError(f"missing required query parameter: {key}")
    return value


def json_response(payload: Any, *, status: int = 200) -> tuple[int, str, bytes]:
    return status, "application/json; charset=utf-8", json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")

"""GTOS second-brain vault helpers.

The second brain is intentionally outside the repo by default.  Raw owner ideas
are preserved as an inbox, then distilled into labeled cards before agents use
them as retrieval intelligence.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

from src.gtos_context_os.catalog import utc_now


DEFAULT_SECOND_BRAIN_ROOT = Path.home() / "Documents/gtos/second-brain"
RAW_STATUS = "raw_inbox_not_agent_authority"
DISTILLED_STATUS = "candidate_distillation_needs_review"
REVIEWED_STATUS = "reviewed_retrieval_intelligence"
SECOND_BRAIN_DIRS = (
    "inbox",
    "distilled",
    "doctrine",
    "hypotheses",
    "route-intelligence",
    "implementation-ideas",
    "agent-methodology",
    "decisions",
    "templates",
    "graph",
    "archive",
)


def init_second_brain(root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT, *, repo: Path | str = ".") -> dict[str, Any]:
    """Create a graph-friendly second-brain vault scaffold."""

    vault = _vault_root(root)
    vault.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for rel in SECOND_BRAIN_DIRS:
        path = vault / rel
        path.mkdir(parents=True, exist_ok=True)
        created.append(path.as_posix())

    files = {
        "README.md": _vault_readme(repo=repo),
        "00_START_HERE.md": _start_here(),
        "inbox/README.md": _inbox_readme(),
        "distilled/README.md": _distilled_readme(),
        "doctrine/README.md": _typed_readme("Doctrine", "stable principles and working doctrine"),
        "hypotheses/README.md": _typed_readme("Hypotheses", "testable ideas that need evidence"),
        "route-intelligence/README.md": _typed_readme("Route Intelligence", "route-specific observations and evidence pointers"),
        "implementation-ideas/README.md": _typed_readme("Implementation Ideas", "build ideas and code-level repair concepts"),
        "agent-methodology/README.md": _typed_readme("Agent Methodology", "how agents should work, reason, and avoid past mistakes"),
        "decisions/README.md": _typed_readme("Decisions", "owner or implementation decisions with dates and sources"),
        "templates/raw_idea.md": _raw_template(),
        "templates/distilled_card.md": _distilled_template(),
    }
    for rel, text in files.items():
        path = vault / rel
        if not path.exists():
            path.write_text(text, encoding="utf-8")
            created.append(path.as_posix())

    graph = generate_second_brain_graph(root=vault)
    return {
        "root": vault.as_posix(),
        "status": "ready",
        "created_paths": created,
        "graph": graph,
        "pour_ideas_here": (vault / "inbox").as_posix(),
        "open_in_obsidian": vault.as_posix(),
    }


def capture_idea(
    body: str,
    *,
    title: str | None = None,
    tags: Sequence[str] = (),
    source: str = "manual",
    root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
) -> Path:
    """Write one raw idea to the inbox without promoting it to agent authority."""

    vault = _vault_root(root)
    (vault / "inbox").mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    clean_title = title or _title_from_body(body)
    normalized_tags = sorted({"raw-idea", "gtos", *(_clean_tag(tag) for tag in tags if tag.strip())})
    payload = {
        "schema": "gtos_second_brain_raw_v1",
        "status": RAW_STATUS,
        "created_at_utc": created_at,
        "title": clean_title,
        "source": source,
        "tags": normalized_tags,
    }
    digest = hashlib.sha256(f"{created_at}\n{clean_title}\n{body}".encode("utf-8")).hexdigest()[:10]
    path = vault / "inbox" / f"{_compact_timestamp(created_at)}-{_slug(clean_title)}-{digest}.md"
    text = _frontmatter(payload)
    text += f"# {clean_title}\n\n"
    text += "## Raw Idea\n\n"
    text += body.strip() + "\n\n"
    text += "## Use Boundary\n\n"
    text += "- This is raw owner thinking, not direct agent authority.\n"
    text += "- Distill and label it before using it in a Context OS pack.\n"
    text += "- Verify actionable claims against current disk/source evidence.\n"
    path.write_text(text, encoding="utf-8")
    return path


def distill_idea(
    source_path: Path | str | None = None,
    *,
    root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
    reviewed: bool = False,
) -> Path:
    """Create a structured distillation card from a raw inbox note.

    This is deterministic.  It does not pretend to be final judgment; it creates
    a reviewable card with extracted signals and a strict use boundary.
    """

    vault = _vault_root(root)
    source = _resolve_source(vault, source_path)
    meta, body = _read_markdown(source)
    idea_body = _section_body(body, "Raw Idea") or body
    title = str(meta.get("title") or _title_from_body(body))
    created_at = utc_now()
    status = REVIEWED_STATUS if reviewed else DISTILLED_STATUS
    source_tags = [str(tag) for tag in meta.get("tags", []) if str(tag) != "raw-idea"]
    tags = sorted({"distilled", "gtos", *source_tags})
    signals = _extract_signals(idea_body)
    target_dir = vault / _target_dir_from_signals(signals)
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "gtos_second_brain_card_v1",
        "status": status,
        "created_at_utc": created_at,
        "title": title,
        "source": _obsidian_link(source, vault),
        "source_path": source.as_posix(),
        "tags": tags,
        "evidence_boundary": "retrieval_intelligence_verify_against_current_disk",
    }
    digest = hashlib.sha256(f"{source.as_posix()}\n{created_at}".encode("utf-8")).hexdigest()[:10]
    path = target_dir / f"{_compact_timestamp(created_at)}-{_slug(title)}-{digest}.md"
    text = _frontmatter(payload)
    text += f"# {title}\n\n"
    text += "## Distilled Meaning\n\n"
    text += _bulletize(signals["meaning"] or [idea_body.strip()[:700] or "No body text found."])
    text += "\n## Actionable Threads\n\n"
    text += _bulletize(signals["actions"] or ["No explicit action extracted. Review manually."])
    text += "\n## Hypotheses To Test\n\n"
    text += _bulletize(signals["hypotheses"] or ["No explicit hypothesis extracted."])
    text += "\n## Guardrails And Risks\n\n"
    text += _bulletize(signals["guardrails"] or ["Do not treat this card as current source proof."])
    text += "\n## Links\n\n"
    text += f"- Raw source: {_obsidian_link(source, vault)}\n"
    text += "- Agent use: retrieval intelligence only; verify before acting.\n"
    path.write_text(text, encoding="utf-8")
    generate_second_brain_graph(root=vault)
    return path


def search_second_brain(
    query: str,
    *,
    root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
    limit: int = 10,
    include_raw: bool = False,
) -> list[dict[str, Any]]:
    """Search distilled second-brain notes with raw inbox excluded by default."""

    vault = _vault_root(root)
    if not vault.exists():
        return []
    terms = [term for term in re.findall(r"[a-zA-Z0-9_./-]+", query.lower()) if len(term) > 1]
    hits: list[dict[str, Any]] = []
    for path in _markdown_files(vault):
        rel = path.relative_to(vault).as_posix()
        if _is_infrastructure_note(rel):
            continue
        if rel.startswith("context-packs/"):
            continue
        if rel.startswith("inbox/") and not include_raw:
            continue
        meta, body = _read_markdown(path)
        score = _second_brain_score(rel, meta, body, terms)
        if score <= 0:
            continue
        hits.append(_brain_hit(path, vault, meta, body, score))
    hits.sort(key=lambda hit: (hit["authority_weight"], hit["score"], hit["mtime_ns"]), reverse=True)
    return hits[:limit]


def second_brain_status(root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT) -> dict[str, Any]:
    vault = _vault_root(root)
    counts_by_dir: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    total = 0
    infrastructure = 0
    if vault.exists():
        for path in _markdown_files(vault):
            rel = path.relative_to(vault).as_posix()
            top = rel.split("/", 1)[0] if "/" in rel else "_root"
            if _is_infrastructure_note(rel):
                infrastructure += 1
                continue
            meta, _ = _read_markdown(path)
            status = str(meta.get("status") or "unlabeled")
            counts_by_dir[top] = counts_by_dir.get(top, 0) + 1
            counts_by_status[status] = counts_by_status.get(status, 0) + 1
            total += 1
    return {
        "root": vault.as_posix(),
        "exists": vault.exists(),
        "active_markdown": total,
        "infrastructure_markdown": infrastructure,
        "total_markdown": total + infrastructure,
        "counts_by_dir": counts_by_dir,
        "counts_by_status": counts_by_status,
        "distillation_queue": second_brain_distillation_queue(root=vault, limit=5),
        "pour_ideas_here": (vault / "inbox").as_posix(),
        "obsidian_open_path": vault.as_posix(),
    }


def second_brain_distillation_queue(
    *,
    root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return raw inbox notes that have not yet been distilled."""

    vault = _vault_root(root)
    inbox = vault / "inbox"
    if not inbox.exists():
        return []
    queue: list[dict[str, Any]] = []
    for path in sorted(inbox.glob("*.md"), reverse=True):
        rel = path.relative_to(vault).as_posix()
        if _is_infrastructure_note(rel):
            continue
        meta, body = _read_markdown(path)
        status = str(meta.get("status") or "")
        if status != RAW_STATUS:
            continue
        stat = path.stat()
        queue.append(
            {
                "path": rel,
                "abs_path": path.as_posix(),
                "title": str(meta.get("title") or path.stem),
                "created_at_utc": meta.get("created_at_utc"),
                "mtime_ns": stat.st_mtime_ns,
                "tags": list(meta.get("tags", [])),
                "freshness": "raw_inbox_not_agent_authority_distill_before_use",
                "snippet": re.sub(r"\s+", " ", body).strip()[:700],
            }
        )
        if len(queue) >= limit:
            break
    return queue


def generate_second_brain_graph(root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT) -> dict[str, Any]:
    vault = _vault_root(root)
    graph_dir = vault / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str, str]] = set()
    if vault.exists():
        for path in _markdown_files(vault):
            rel = path.relative_to(vault).as_posix()
            if rel.startswith("graph/"):
                continue
            meta, body = _read_markdown(path)
            node_id = _node_id(rel)
            nodes[node_id] = {
                "id": node_id,
                "path": rel,
                "title": str(meta.get("title") or path.stem),
                "status": str(meta.get("status") or "unlabeled"),
                "tags": list(meta.get("tags", [])),
                "directory": rel.split("/", 1)[0],
            }
            for link in _wikilinks(body):
                target = _resolve_wikilink(vault, link)
                if target:
                    edges.add((node_id, _node_id(target.relative_to(vault).as_posix()), "links"))
            for tag in meta.get("tags", []):
                tag_id = f"tag_{_slug(str(tag))}"
                nodes.setdefault(
                    tag_id,
                    {
                        "id": tag_id,
                        "path": f"tag/{tag}",
                        "title": f"#{tag}",
                        "status": "tag",
                        "tags": [],
                        "directory": "tag",
                    },
                )
                edges.add((node_id, tag_id, "tagged"))

    graph = {
        "schema": "gtos_second_brain_graph_v1",
        "generated_at_utc": utc_now(),
        "root": vault.as_posix(),
        "nodes": list(nodes.values()),
        "edges": [{"source": a, "target": b, "kind": kind} for a, b, kind in sorted(edges)],
    }
    json_path = graph_dir / "SECOND_BRAIN_GRAPH.json"
    mermaid_path = graph_dir / "SECOND_BRAIN_GRAPH.mmd"
    index_path = graph_dir / "SECOND_BRAIN_INDEX.md"
    json_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mermaid_path.write_text(_render_mermaid(graph), encoding="utf-8")
    index_path.write_text(_render_index(graph), encoding="utf-8")
    return {
        "json": json_path.as_posix(),
        "mermaid": mermaid_path.as_posix(),
        "index": index_path.as_posix(),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
    }


def second_brain_pack(
    query: str,
    *,
    root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
    limit: int = 8,
    include_raw: bool = False,
) -> dict[str, Any]:
    return {
        "status": second_brain_status(root=root),
        "hits": search_second_brain(query, root=root, limit=limit, include_raw=include_raw),
        "rules": {
            "raw_inbox": "raw notes are preserved but not direct agent authority",
            "distilled_cards": "distilled cards are retrieval intelligence, not proof",
            "agent_action": "verify claims against current repo/source artifacts before acting",
        },
    }


def _vault_root(root: Path | str | None) -> Path:
    return Path(root or DEFAULT_SECOND_BRAIN_ROOT).expanduser().resolve()


def _vault_readme(*, repo: Path | str) -> str:
    return """# GTOS Second Brain

This is the owner idea vault for GTOS.  It is designed for Obsidian graph view
and Context OS retrieval.

Use `inbox/` for raw idea pours.  Raw notes are never direct agent authority.
Agents should use distilled cards and still verify actionable claims against
current repo/source evidence.

Primary commands:

```bash
python3 scripts/gtos_context.py brain capture --title "Idea" --body "..."
python3 scripts/gtos_context.py brain distill --latest
python3 scripts/gtos_context.py brain graph
python3 scripts/gtos_context.py pack --task "<task>" --profile ultimate --include-second-brain
```
"""


def _start_here() -> str:
    return """# Start Here

Open this folder as an Obsidian vault.

- Pour unfiltered ideas into [[inbox/README]] or use `brain capture`.
- Distilled cards live in [[distilled/README]], [[hypotheses/README]],
  [[implementation-ideas/README]], [[agent-methodology/README]], and related folders.
- Use Obsidian's Graph View for the visual brain map.
- Use `graph/SECOND_BRAIN_INDEX.md` for the generated machine map.

Authority rule: raw thoughts are preserved, not obeyed literally.  The useful
thing is the distilled method, hypothesis, warning, or implementation idea.
"""


def _inbox_readme() -> str:
    return """# Inbox

Pour raw ideas here.  Do not worry about formatting.

Status of this folder: `raw_inbox_not_agent_authority`.

Agents must distill and label these notes before using them in work.
"""


def _distilled_readme() -> str:
    return """# Distilled

Distilled idea cards live here when they do not fit a more specific folder.
These are retrieval intelligence, not source proof.
"""


def _typed_readme(title: str, description: str) -> str:
    return f"""# {title}

Purpose: {description}.

Use boundary: these notes guide retrieval and reasoning.  Agents must verify
actionable claims against current disk/source evidence before implementing.
"""


def _raw_template() -> str:
    return """---
schema: gtos_second_brain_raw_v1
status: raw_inbox_not_agent_authority
tags:
  - raw-idea
---
# Raw Idea Title

## Raw Idea

Write anything here.

## Use Boundary

- Raw owner thinking, not direct agent authority.
- Distill before use.
"""


def _distilled_template() -> str:
    return """---
schema: gtos_second_brain_card_v1
status: candidate_distillation_needs_review
tags:
  - distilled
---
# Distilled Card Title

## Distilled Meaning

- Add the distilled meaning here.

## Actionable Threads

- Add buildable or testable action threads here.

## Hypotheses To Test

- Add hypotheses that need evidence here.

## Guardrails And Risks

- Add boundaries, stale-context risks, or anti-patterns here.

## Links

- Raw source:
"""


def _frontmatter(payload: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw_meta = text[4:end].strip().splitlines()
    body = text[end + 4 :].lstrip()
    meta: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in raw_meta:
        if line.startswith("  - ") and current_list_key:
            meta.setdefault(current_list_key, []).append(line[4:].strip())
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            meta[key] = value
        else:
            meta[key] = []
            current_list_key = key
    return meta, body


def _markdown_files(vault: Path) -> Iterable[Path]:
    return sorted(path for path in vault.rglob("*.md") if ".obsidian" not in path.parts)


def _is_infrastructure_note(relative_path: str) -> bool:
    path = Path(relative_path)
    parts = path.parts
    if not parts:
        return False
    if parts[0] in {"templates", "graph"}:
        return True
    if path.name == "README.md":
        return True
    return relative_path == "00_START_HERE.md"


def _brain_hit(path: Path, vault: Path, meta: dict[str, Any], body: str, score: int) -> dict[str, Any]:
    rel = path.relative_to(vault).as_posix()
    status = str(meta.get("status") or "unlabeled")
    if status == RAW_STATUS:
        authority_weight = 10
        authority_tier = "second_brain_raw_inbox"
        evidence_class = "human_idea_raw"
        freshness = "raw_do_not_execute_literally"
    elif status == DISTILLED_STATUS:
        authority_weight = 45
        authority_tier = "second_brain_distilled_intelligence"
        evidence_class = "human_idea_distilled"
        freshness = "verify_against_current_disk"
    elif status == REVIEWED_STATUS:
        authority_weight = 60
        authority_tier = "second_brain_reviewed_intelligence"
        evidence_class = "human_idea_reviewed"
        freshness = "reviewed_still_verify_against_current_disk"
    else:
        authority_weight = 25
        authority_tier = "second_brain_reference"
        evidence_class = "second_brain_reference"
        freshness = "unlabeled_verify_before_use"
    stat = path.stat()
    return {
        "score": score,
        "authority_weight": authority_weight,
        "path": rel,
        "abs_path": path.as_posix(),
        "title": str(meta.get("title") or path.stem),
        "status": status,
        "authority_tier": authority_tier,
        "evidence_class": evidence_class,
        "freshness": freshness,
        "tags": list(meta.get("tags", [])),
        "snippet": _snippet(body),
        "mtime_ns": stat.st_mtime_ns,
        "sha256": _sha256_text(path.read_text(encoding="utf-8", errors="replace")),
    }


def _second_brain_score(
    relative_path: str,
    meta: dict[str, Any],
    body: str,
    terms: Sequence[str],
) -> int:
    if not terms:
        return 1
    title = str(meta.get("title") or "")
    tags = " ".join(str(tag) for tag in meta.get("tags", []))
    path_lower = relative_path.lower()
    title_lower = title.lower()
    tags_lower = tags.lower()
    body_lower = body.lower()
    score = 0
    for term in terms:
        path_hits = path_lower.count(term)
        title_hits = title_lower.count(term)
        tag_hits = tags_lower.count(term)
        body_hits = min(body_lower.count(term), 5)
        score += 12 * title_hits + 8 * path_hits + 6 * tag_hits + body_hits
    if all(term in f"{path_lower}\n{title_lower}\n{tags_lower}\n{body_lower}" for term in terms):
        score += 15
    if any(token in path_lower for token in ("component-flow/", "repair-intelligence/", "route-intelligence/")):
        score += 5
    return score


def _extract_signals(body: str) -> dict[str, list[str]]:
    lines = [line.strip("- ").strip() for line in body.splitlines() if line.strip()]
    sentences: list[str] = []
    for line in lines:
        if line.startswith("#") or line.startswith("---"):
            continue
        parts = re.split(r"(?<=[.!?])\s+", line)
        sentences.extend(part.strip() for part in parts if part.strip())
    buckets = {"meaning": [], "actions": [], "hypotheses": [], "guardrails": []}
    for sentence in sentences:
        lowered = sentence.lower()
        if any(token in lowered for token in ("must", "need", "should", "build", "fix", "implement", "link")):
            buckets["actions"].append(sentence)
        elif any(token in lowered for token in ("maybe", "hypothesis", "what if", "i think", "could", "might")):
            buckets["hypotheses"].append(sentence)
        elif any(token in lowered for token in ("do not", "don't", "dont", "stale", "pollute", "risk", "wrong", "confusing")):
            buckets["guardrails"].append(sentence)
        else:
            buckets["meaning"].append(sentence)
    for key, values in buckets.items():
        buckets[key] = values[:8]
    return buckets


def _section_body(body: str, heading: str) -> str:
    lines = body.splitlines()
    start: int | None = None
    collected: list[str] = []
    target = heading.strip().lower()
    for idx, line in enumerate(lines):
        normalized = line.strip("# ").strip().lower()
        if line.lstrip().startswith("#") and normalized == target:
            start = idx + 1
            continue
        if start is not None:
            if line.lstrip().startswith("#"):
                break
            collected.append(line)
    return "\n".join(collected).strip()


def _target_dir_from_signals(signals: dict[str, list[str]]) -> str:
    combined = " ".join(value for values in signals.values() for value in values).lower()
    if any(token in combined for token in ("agent", "context", "memory", "stale", "doctrine", "methodology")):
        return "agent-methodology"
    if any(token in combined for token in ("implement", "code", "build", "wire", "fix")):
        return "implementation-ideas"
    if any(token in combined for token in ("hypothesis", "test", "maybe", "what if")):
        return "hypotheses"
    return "distilled"


def _resolve_source(vault: Path, source_path: Path | str | None) -> Path:
    if source_path:
        path = Path(source_path).expanduser()
        if not path.is_absolute():
            path = vault / path
        return path.resolve()
    inbox = sorted((vault / "inbox").glob("*.md"), key=lambda path: path.stat().st_mtime_ns, reverse=True)
    if not inbox:
        raise FileNotFoundError(f"no inbox notes found under {vault / 'inbox'}")
    return inbox[0].resolve()


def _wikilinks(text: str) -> list[str]:
    return [match.split("|", 1)[0].strip() for match in re.findall(r"\[\[([^\]]+)\]\]", text)]


def _resolve_wikilink(vault: Path, link: str) -> Path | None:
    clean = link.removesuffix(".md")
    candidates = [vault / f"{clean}.md"]
    candidates.extend(vault.glob(f"**/{Path(clean).name}.md"))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _obsidian_link(path: Path, vault: Path) -> str:
    try:
        rel = path.relative_to(vault).with_suffix("").as_posix()
    except ValueError:
        rel = path.with_suffix("").as_posix()
    return f"[[{rel}]]"


def _render_mermaid(graph: dict[str, Any]) -> str:
    lines = ["graph TD"]
    node_lookup = {node["id"]: node for node in graph["nodes"]}
    for node in graph["nodes"][:250]:
        label = str(node["title"]).replace('"', "'")[:80]
        lines.append(f'  {node["id"]}["{label}"]')
    for edge in graph["edges"][:500]:
        if edge["source"] in node_lookup and edge["target"] in node_lookup:
            lines.append(f'  {edge["source"]} -->|{edge["kind"]}| {edge["target"]}')
    return "\n".join(lines) + "\n"


def _render_index(graph: dict[str, Any]) -> str:
    lines = [
        "---",
        "schema: gtos_second_brain_graph_index_v1",
        "status: generated_human_snapshot",
        "evidence_class: generated_graph_index",
        f"generated_at_utc: \"{graph['generated_at_utc']}\"",
        "tags:",
        "  - gtos",
        "  - second_brain",
        "  - graph",
        "  - index",
        "---",
        "",
        "# Second Brain Index",
        "",
        f"generated_at_utc: `{graph['generated_at_utc']}`",
        f"nodes: `{len(graph['nodes'])}`",
        f"edges: `{len(graph['edges'])}`",
        "",
        "Open the vault root in Obsidian, then use Graph View for the visual map.",
        "",
        "## Nodes",
    ]
    for node in sorted(graph["nodes"], key=lambda item: (item["directory"], item["title"]))[:300]:
        if node.get("status") == "tag":
            lines.append(f"- `{node['title']}` `tag`")
            continue
        lines.append(f"- [[{Path(node['path']).with_suffix('').as_posix()}|{node['title']}]] `{node['status']}`")
    return "\n".join(lines) + "\n"


def _bulletize(items: Sequence[str]) -> str:
    return "".join(f"- {item.strip()}\n" for item in items if item.strip())


def _snippet(text: str, max_chars: int = 700) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:max_chars]


def _title_from_body(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip(" #\t")
        if stripped:
            return stripped[:90]
    return "Untitled idea"


def _clean_tag(tag: str) -> str:
    return _slug(tag).replace("-", "_")


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")[:80] or "idea"


def _compact_timestamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("Z", "Z")


def _node_id(value: str) -> str:
    return "n_" + re.sub(r"[^a-zA-Z0-9_]", "_", value)[:96]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

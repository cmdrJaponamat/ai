from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re

from db_runtime import DBRepository


REPOSITORY = DBRepository()


def list_projects() -> list[dict[str, str | int | bool]]:
    rows = REPOSITORY.fetch_all(
        """
        select id, name, path, repo_root, coalesce(recovery_file, '') as recovery_file, active
        from projects
        order by id
        """
    )
    return [
        {
            "id": int(row["id"]),
            "name": row["name"],
            "path": row["path"],
            "repo_root": row["repo_root"],
            "recovery_file": row["recovery_file"],
            "active": bool(row["active"]),
        }
        for row in rows
    ]


def get_project(project_name: str) -> dict[str, str | int | bool]:
    row = REPOSITORY.fetch_one(
        """
        select id, name, path, repo_root, coalesce(recovery_file, '') as recovery_file, active
        from projects
        where lower(name) = lower(%s)
        limit 1
        """,
        (project_name,),
    )
    if row is None:
        raise ValueError(f"Project not found in ai_context: {project_name}")
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "path": row["path"],
        "repo_root": row["repo_root"],
        "recovery_file": row["recovery_file"],
        "active": bool(row["active"]),
    }


def list_snapshots(project_name: str, snapshot_type: str | None = None, limit: int = 10) -> list[dict]:
    project = get_project(project_name)
    params: list[object] = [project["id"]]
    snapshot_filter = ""
    if snapshot_type:
        snapshot_filter = "and snapshot_type = %s"
        params.append(snapshot_type)
    params.append(int(limit))

    rows = REPOSITORY.fetch_all(
        f"""
        select id, snapshot_type, coalesce(title, '') as title, payload, created_at::text as created_at
        from snapshots
        where project_id = %s
          {snapshot_filter}
        order by id desc
        limit %s
        """,
        tuple(params),
    )

    return [
        {
            "id": int(row["id"]),
            "project_name": project["name"],
            "snapshot_type": row["snapshot_type"],
            "title": row["title"],
            "payload": row["payload"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def record_snapshot(
    project_name: str,
    snapshot_type: str,
    payload: dict,
    title: str | None = None,
) -> dict[str, str | int]:
    project = get_project(project_name)
    row = REPOSITORY.fetch_one(
        """
        insert into snapshots (project_id, snapshot_type, title, payload)
        values (%s, %s, %s, %s::jsonb)
        returning id
        """,
        (
            project["id"],
            snapshot_type,
            title,
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    if row is None:
        raise RuntimeError("Snapshot insert returned no id")
    return {
        "id": int(row["id"]),
        "project_name": str(project["name"]),
        "snapshot_type": snapshot_type,
    }


def _project_root(project_name: str) -> Path:
    project = get_project(project_name)
    return Path(str(project["repo_root"]))


def _bundle_sources(project_name: str) -> list[dict[str, str]]:
    project = get_project(project_name)
    root = Path(str(project["repo_root"]))
    sources: list[Path] = []

    recovery_file = Path(str(project["recovery_file"]))
    if recovery_file.is_file():
        sources.append(recovery_file)

    for relative_path in ("docs/TODO.md", "docs/ARCHITECTURE.md", "README.md"):
        candidate = root / relative_path
        if candidate.is_file():
            sources.append(candidate)

    bundle: list[dict[str, str]] = []
    for path in sources:
        bundle.append(
            {
                "path": str(path),
                "title": path.name,
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return bundle


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _upsert_document(project_id: int, source_type: str, path: str, title: str, content: str) -> None:
    REPOSITORY.execute(
        """
        insert into documents (project_id, source_type, path, title, content, content_hash, metadata, updated_at)
        values (%s, %s, %s, %s, %s, %s, '{}'::jsonb, now())
        on conflict (path, content_hash) do update set
            title = excluded.title,
            updated_at = now()
        """,
        (project_id, source_type, path, title, content, _content_hash(content)),
    )


def _markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def _extract_bullets(section_text: str, limit: int = 8) -> list[str]:
    bullets = []
    for raw_line in section_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            bullets.append(re.sub(r"^\d+\.\s+", "", stripped))
        if len(bullets) >= limit:
            break
    return bullets


def _trim_paragraph(section_text: str, max_lines: int = 8) -> str:
    lines = [line.rstrip() for line in section_text.splitlines() if line.strip()]
    return "\n".join(lines[:max_lines]).strip()


def kb_capture_project_bundle(project_name: str) -> dict:
    project = get_project(project_name)
    bundle = _bundle_sources(project_name)
    for item in bundle:
        path = item["path"]
        title = item["title"]
        content = item["content"]
        if path.endswith(".ai-recovery.md"):
            source_type = "recovery"
        elif path.endswith("TODO.md"):
            source_type = "todo"
        elif path.endswith("ARCHITECTURE.md"):
            source_type = "architecture"
        else:
            source_type = "doc"
        _upsert_document(int(project["id"]), source_type, path, title, content)

    bundle_hash = _content_hash(
        "".join(f"{item['path']}::{_content_hash(item['content'])}\n" for item in bundle)
    )
    return {
        "project_name": project["name"],
        "project_id": project["id"],
        "document_count": len(bundle),
        "bundle_hash": bundle_hash,
        "source_refs": [item["path"] for item in bundle],
    }


def _build_projection(project_name: str) -> dict:
    bundle = _bundle_sources(project_name)
    by_name = {Path(item["path"]).name: item["content"] for item in bundle}
    recovery = by_name.get(".ai-recovery.md", "")
    todo = by_name.get("TODO.md", "")
    architecture = by_name.get("ARCHITECTURE.md", "")

    purpose = _trim_paragraph(_markdown_section(recovery, "purpose"), max_lines=4)
    current_state = _trim_paragraph(_markdown_section(recovery, "current_state"), max_lines=8)
    current_risks = _extract_bullets(_markdown_section(recovery, "current_risks"), limit=6)
    current_next_steps = _extract_bullets(_markdown_section(recovery, "current_next_steps"), limit=6)
    architecture_state = _trim_paragraph(_markdown_section(recovery, "architecture_state"), max_lines=6)
    testing_rule = _trim_paragraph(_markdown_section(recovery, "testing_rule_now"), max_lines=6)
    todo_p0 = _extract_bullets(_markdown_section(todo, "P0"), limit=6)
    near_term = _extract_bullets(_markdown_section(architecture, "Near-Term Milestones"), limit=6)
    hotspots = _extract_bullets(_markdown_section(architecture, "Current Hotspots"), limit=6)

    overview_parts = [part for part in (purpose, current_state.splitlines()[0] if current_state else "") if part]
    overview = "\n".join(overview_parts).strip()
    state_summary = "\n".join(part for part in (current_state, architecture_state) if part).strip()

    next_steps = current_next_steps or near_term or todo_p0
    decisions = []
    if architecture_state:
        decisions.append("Архитектурный source of truth и текущие boundaries опираются на .ai-recovery.md.")
    if "strict quota" in recovery.lower():
        decisions.append("Strict quota/storage safety признан обязательным redesign до следующего публичного релиза.")
    if "manual test" in testing_rule.lower() or "ручное тестирование" in testing_rule.lower():
        decisions.append("Перед заметными runtime/media изменениями обязателен device regression pass.")

    constraints = current_risks[:]
    if hotspots:
        constraints.extend(hotspots[:3])
    if testing_rule:
        constraints.append("Есть обязательный device regression перед следующими заметными изменениями.")

    source_refs = [item["path"] for item in bundle]
    bundle_hash = _content_hash(
        "".join(f"{item['path']}::{_content_hash(item['content'])}\n" for item in bundle)
    )

    return {
        "bundle_hash": bundle_hash,
        "overview": overview,
        "state_summary": state_summary,
        "next_steps": next_steps,
        "decisions": decisions,
        "constraints": constraints,
        "source_refs": source_refs,
    }


def kb_bootstrap_projection(project_name: str) -> dict:
    project = get_project(project_name)
    bundle_info = kb_capture_project_bundle(project_name)
    projection = _build_projection(project_name)
    REPOSITORY.execute(
        """
        insert into kb_projections (
            project_id, bundle_hash, overview, state_summary, next_steps, decisions, constraints, source_refs, updated_at
        ) values (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, now())
        on conflict (project_id) do update set
            bundle_hash = excluded.bundle_hash,
            overview = excluded.overview,
            state_summary = excluded.state_summary,
            next_steps = excluded.next_steps,
            decisions = excluded.decisions,
            constraints = excluded.constraints,
            source_refs = excluded.source_refs,
            updated_at = now()
        """,
        (
            project["id"],
            projection["bundle_hash"],
            projection["overview"],
            projection["state_summary"],
            json.dumps(projection["next_steps"], ensure_ascii=False),
            json.dumps(projection["decisions"], ensure_ascii=False),
            json.dumps(projection["constraints"], ensure_ascii=False),
            json.dumps(projection["source_refs"], ensure_ascii=False),
        ),
    )
    return {
        "project_name": project["name"],
        "bundle_hash": projection["bundle_hash"],
        "document_count": bundle_info["document_count"],
        "next_steps_count": len(projection["next_steps"]),
        "decisions_count": len(projection["decisions"]),
        "constraints_count": len(projection["constraints"]),
    }


def kb_rebuild_project_projection(project_name: str) -> dict:
    return kb_bootstrap_projection(project_name)


def _load_projection(project_name: str) -> dict:
    project = get_project(project_name)
    row = REPOSITORY.fetch_one(
        """
        select
            bundle_hash,
            overview,
            state_summary,
            next_steps,
            decisions,
            constraints,
            source_refs,
            updated_at::text as updated_at
        from kb_projections
        where project_id = %s
        limit 1
        """,
        (project["id"],),
    )
    if not row:
        raise ValueError(f"No kb_projection found for project: {project_name}")
    return {
        "project_name": project["name"],
        "bundle_hash": row["bundle_hash"],
        "overview": row["overview"],
        "state_summary": row["state_summary"],
        "next_steps": row["next_steps"],
        "decisions": row["decisions"],
        "constraints": row["constraints"],
        "source_refs": row["source_refs"],
        "updated_at": row["updated_at"],
    }


def kb_get_project_overview(project_name: str) -> dict:
    projection = _load_projection(project_name)
    return {
        "project_name": projection["project_name"],
        "overview": projection["overview"],
        "source_refs": projection["source_refs"],
        "updated_at": projection["updated_at"],
    }


def kb_project_status(project_name: str, snapshot_limit: int = 5) -> dict:
    project = get_project(project_name)
    projection = _load_projection(project_name)
    recent_snapshots = list_snapshots(project_name, limit=snapshot_limit)
    return {
        "project_name": str(project["name"]),
        "project_id": int(project["id"]),
        "active": bool(project["active"]),
        "repo_root": str(project["repo_root"]),
        "recovery_file": str(project["recovery_file"]),
        "overview": projection["overview"],
        "state_summary": projection["state_summary"],
        "next_steps": projection["next_steps"],
        "constraints": projection["constraints"],
        "source_refs": projection["source_refs"],
        "projection_updated_at": projection["updated_at"],
        "recent_snapshots": recent_snapshots,
        "recent_snapshot_types": [item["snapshot_type"] for item in recent_snapshots],
    }


def kb_get_project_state(project_name: str) -> dict:
    projection = _load_projection(project_name)
    return {
        "project_name": projection["project_name"],
        "state_summary": projection["state_summary"],
        "constraints": projection["constraints"],
        "updated_at": projection["updated_at"],
    }


def kb_get_next_steps(project_name: str) -> dict:
    projection = _load_projection(project_name)
    return {
        "project_name": projection["project_name"],
        "next_steps": projection["next_steps"],
        "updated_at": projection["updated_at"],
    }


def kb_get_decisions(project_name: str) -> dict:
    projection = _load_projection(project_name)
    return {
        "project_name": projection["project_name"],
        "decisions": projection["decisions"],
        "updated_at": projection["updated_at"],
    }


def kb_get_constraints(project_name: str) -> dict:
    projection = _load_projection(project_name)
    return {
        "project_name": projection["project_name"],
        "constraints": projection["constraints"],
        "updated_at": projection["updated_at"],
    }


def kb_get_source_refs(project_name: str) -> dict:
    projection = _load_projection(project_name)
    return {
        "project_name": projection["project_name"],
        "source_refs": projection["source_refs"],
        "updated_at": projection["updated_at"],
    }


def kb_validate_projection(project_name: str) -> dict:
    projection = _load_projection(project_name)
    checks = {
        "has_overview": bool(projection["overview"].strip()),
        "has_state_summary": bool(projection["state_summary"].strip()),
        "has_next_steps": bool(projection["next_steps"]),
        "has_source_refs": bool(projection["source_refs"]),
    }
    return {
        "project_name": projection["project_name"],
        "valid": all(checks.values()),
        "checks": checks,
        "updated_at": projection["updated_at"],
    }

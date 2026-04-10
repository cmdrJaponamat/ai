from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess
import re


PG_DSN = ["psql", "-h", "127.0.0.1", "-U", "japonamat", "ai_context"]


def _run_sql(sql: str) -> str:
    completed = subprocess.run(
        PG_DSN + ["-AtF", "\t", "-c", sql],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "psql query failed")
    return completed.stdout.strip()


def _run_sql_json(sql: str) -> dict | list:
    output = _run_sql(sql)
    line = _first_data_line(output)
    if not line:
        raise ValueError("SQL query returned no JSON payload")
    return json.loads(line)


def _first_data_line(output: str) -> str:
    for line in output.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        if normalized.startswith(("INSERT ", "UPDATE ", "DELETE ")):
            continue
        return normalized
    return ""


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


def list_projects() -> list[dict[str, str | int | bool]]:
    output = _run_sql(
        """
        select id, name, path, repo_root, coalesce(recovery_file, ''), active
        from projects
        order by id;
        """
    )
    rows = []
    for line in output.splitlines():
        if not line:
            continue
        project_id, name, path, repo_root, recovery_file, active = line.split("\t", 5)
        rows.append(
            {
                "id": int(project_id),
                "name": name,
                "path": path,
                "repo_root": repo_root,
                "recovery_file": recovery_file,
                "active": active == "t",
            }
        )
    return rows


def get_project(project_name: str) -> dict[str, str | int | bool]:
    escaped = _sql_escape(project_name)
    output = _run_sql(
        f"""
        select id, name, path, repo_root, coalesce(recovery_file, ''), active
        from projects
        where lower(name) = lower('{escaped}')
        limit 1;
        """
    )
    if not output:
        raise ValueError(f"Project not found in ai_context: {project_name}")
    project_id, name, path, repo_root, recovery_file, active = output.split("\t", 5)
    return {
        "id": int(project_id),
        "name": name,
        "path": path,
        "repo_root": repo_root,
        "recovery_file": recovery_file,
        "active": active == "t",
    }


def list_snapshots(project_name: str, snapshot_type: str | None = None, limit: int = 10) -> list[dict]:
    project = get_project(project_name)
    snapshot_filter = ""
    if snapshot_type:
        snapshot_filter = f"and snapshot_type = '{_sql_escape(snapshot_type)}'"

    output = _run_sql(
        f"""
        select id, snapshot_type, coalesce(title, ''), payload::text, created_at::text
        from snapshots
        where project_id = {project["id"]}
          {snapshot_filter}
        order by id desc
        limit {int(limit)};
        """
    )

    rows = []
    for line in output.splitlines():
        if not line:
            continue
        snapshot_id, kind, title, payload_text, created_at = line.split("\t", 4)
        rows.append(
            {
                "id": int(snapshot_id),
                "project_name": project["name"],
                "snapshot_type": kind,
                "title": title,
                "payload": json.loads(payload_text),
                "created_at": created_at,
            }
        )
    return rows


def record_snapshot(
    project_name: str,
    snapshot_type: str,
    payload: dict,
    title: str | None = None,
) -> dict[str, str | int]:
    project = get_project(project_name)
    payload_json = json.dumps(payload, ensure_ascii=False)
    title_sql = "NULL" if title is None else f"'{_sql_escape(title)}'"

    snapshot_output = _run_sql(
        f"""
        insert into snapshots (project_id, snapshot_type, title, payload)
        values (
            {project["id"]},
            '{_sql_escape(snapshot_type)}',
            {title_sql},
            '{_sql_escape(payload_json)}'::jsonb
        )
        returning id;
        """
    )
    snapshot_id = _first_data_line(snapshot_output)
    if not snapshot_id:
        raise RuntimeError("Snapshot insert returned no id")
    return {
        "id": int(snapshot_id),
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
    payload = _sql_escape(content)
    _run_sql(
        f"""
        insert into documents (project_id, source_type, path, title, content, content_hash, metadata, updated_at)
        values (
            {project_id},
            '{_sql_escape(source_type)}',
            '{_sql_escape(path)}',
            '{_sql_escape(title)}',
            '{payload}',
            '{_content_hash(content)}',
            '{{}}'::jsonb,
            now()
        )
        on conflict (path, content_hash) do update set
            title = excluded.title,
            updated_at = now();
        """
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
    _run_sql(
        f"""
        insert into kb_projections (
            project_id, bundle_hash, overview, state_summary, next_steps, decisions, constraints, source_refs, updated_at
        ) values (
            {project["id"]},
            '{_sql_escape(projection["bundle_hash"])}',
            '{_sql_escape(projection["overview"])}',
            '{_sql_escape(projection["state_summary"])}',
            '{_sql_escape(json.dumps(projection["next_steps"], ensure_ascii=False))}'::jsonb,
            '{_sql_escape(json.dumps(projection["decisions"], ensure_ascii=False))}'::jsonb,
            '{_sql_escape(json.dumps(projection["constraints"], ensure_ascii=False))}'::jsonb,
            '{_sql_escape(json.dumps(projection["source_refs"], ensure_ascii=False))}'::jsonb,
            now()
        )
        on conflict (project_id) do update set
            bundle_hash = excluded.bundle_hash,
            overview = excluded.overview,
            state_summary = excluded.state_summary,
            next_steps = excluded.next_steps,
            decisions = excluded.decisions,
            constraints = excluded.constraints,
            source_refs = excluded.source_refs,
            updated_at = now();
        """
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
    row = _run_sql_json(
        f"""
        select row_to_json(projection_row)
        from kb_projections
        cross join lateral (
            select
                bundle_hash,
                overview,
                state_summary,
                next_steps,
                decisions,
                constraints,
                source_refs,
                updated_at::text as updated_at
        ) as projection_row
        where project_id = {project["id"]}
        limit 1;
        """
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

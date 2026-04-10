from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import re


PROJECT_ROOT = Path("/home/japonamat/pet/projects/Photo_Trap")
RECOVERY_FILE = PROJECT_ROOT / ".ai-recovery.md"
KT_LIMIT = 700


@dataclass(frozen=True)
class CodeSearchHit:
    path: Path
    line_number: int
    line: str


@dataclass(frozen=True)
class KotlinFileStat:
    path: Path
    line_count: int


def read_recovery() -> str:
    return RECOVERY_FILE.read_text(encoding="utf-8")


def read_file(relative_path: str) -> str:
    target = (PROJECT_ROOT / relative_path).resolve()
    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {relative_path}") from exc
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    return target.read_text(encoding="utf-8")


def project_status() -> dict[str, str]:
    branch = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "status", "--short", "--branch"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "project_root": str(PROJECT_ROOT),
        "status": branch,
    }


def search_code(query: str, limit: int = 10) -> list[CodeSearchHit]:
    command = [
        "rg",
        "-n",
        "--no-heading",
        "--color",
        "never",
        "--glob",
        "!.git",
        "--glob",
        "!build",
        "--glob",
        "!.gradle",
        "--glob",
        "!.kotlin",
        query,
        str(PROJECT_ROOT),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr.strip() or "rg search failed")

    hits: list[CodeSearchHit] = []
    for raw_line in completed.stdout.splitlines():
        parts = raw_line.split(":", 2)
        if len(parts) != 3:
            continue
        path_text, line_number_text, line = parts
        hits.append(
            CodeSearchHit(
                path=Path(path_text),
                line_number=int(line_number_text),
                line=line.strip(),
            )
        )
        if len(hits) >= limit:
            break
    return hits


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _collect_kotlin_file_stats() -> list[KotlinFileStat]:
    completed = _run_command(
        [
            "rg",
            "--files",
            str(PROJECT_ROOT),
            "-g",
            "*.kt",
            "-g",
            "!**/build/**",
            "-g",
            "!**/.gradle/**",
            "-g",
            "!**/.kotlin/**",
        ]
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to list Kotlin files")

    stats: list[KotlinFileStat] = []
    for raw_path in completed.stdout.splitlines():
        path = Path(raw_path)
        if not path.is_file():
            continue
        line_count = sum(1 for _ in path.open("r", encoding="utf-8"))
        stats.append(KotlinFileStat(path=path, line_count=line_count))
    stats.sort(key=lambda item: item.line_count, reverse=True)
    return stats


def _normalize_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def safe_split_audit(top_n: int = 15, line_limit: int = KT_LIMIT) -> dict:
    stats = _collect_kotlin_file_stats()
    top_files = [
        {
            "path": _normalize_path(item.path),
            "line_count": item.line_count,
            "over_limit": item.line_count > line_limit,
        }
        for item in stats[:top_n]
    ]
    over_limit = [
        {
            "path": _normalize_path(item.path),
            "line_count": item.line_count,
        }
        for item in stats
        if item.line_count > line_limit
    ]
    within_limit = [
        {
            "path": _normalize_path(item.path),
            "line_count": item.line_count,
        }
        for item in stats
        if item.line_count <= line_limit
    ]
    return {
        "project_root": str(PROJECT_ROOT),
        "line_limit": line_limit,
        "top_files": top_files,
        "over_limit_count": len(over_limit),
        "within_limit_count": len(within_limit),
        "over_limit_files": over_limit,
        "largest_within_limit_files": within_limit[:top_n],
    }


def _parse_branch_name(status_text: str) -> str:
    first_line = status_text.splitlines()[0] if status_text else ""
    match = re.match(r"^## ([^. ]+)", first_line)
    return match.group(1) if match else "unknown"


def refactor_checkpoint(top_n: int = 10, line_limit: int = KT_LIMIT) -> dict:
    status_payload = project_status()
    audit_payload = safe_split_audit(top_n=top_n, line_limit=line_limit)

    assemble = _run_command(["./gradlew", "assembleDebug"])
    assemble_output = (assemble.stdout + "\n" + assemble.stderr).strip()
    if len(assemble_output) > 4000:
        assemble_output = assemble_output[-4000:]

    return {
        "project_root": str(PROJECT_ROOT),
        "branch": _parse_branch_name(status_payload["status"]),
        "git_status": status_payload["status"],
        "top_kotlin_files": audit_payload["top_files"],
        "files_over_limit": audit_payload["over_limit_files"],
        "line_limit": line_limit,
        "assemble_debug": {
            "success": assemble.returncode == 0,
            "exit_code": assemble.returncode,
            "output_tail": assemble_output,
        },
    }

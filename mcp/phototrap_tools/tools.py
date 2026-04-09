from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


PROJECT_ROOT = Path("/home/japonamat/pet/projects/Photo_Trap")
RECOVERY_FILE = PROJECT_ROOT / ".ai-recovery.md"


@dataclass(frozen=True)
class CodeSearchHit:
    path: Path
    line_number: int
    line: str


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

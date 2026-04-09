from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re


AI_ROOT = Path("/home/japonamat/ai")
PROJECT_REGISTRY = AI_ROOT / "PROJECT_CONTEXTS.md"
ACTIONS_LOG = AI_ROOT / "actions.log"

PROJECT_LINE_RE = re.compile(
    r"^- `(?P<name>[^`]+)` \| path: `(?P<path>[^`]+)` \| recovery: `(?P<recovery>[^`]+)`$"
)


@dataclass(frozen=True)
class ProjectEntry:
    name: str
    path: Path
    recovery: Path


def list_projects() -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    for raw_line in PROJECT_REGISTRY.read_text(encoding="utf-8").splitlines():
        match = PROJECT_LINE_RE.match(raw_line.strip())
        if not match:
            continue
        entries.append(
            ProjectEntry(
                name=match.group("name"),
                path=Path(match.group("path")),
                recovery=Path(match.group("recovery")),
            )
        )
    return entries


def get_project(name: str) -> ProjectEntry:
    normalized = name.casefold()
    for entry in list_projects():
        if entry.name.casefold() == normalized:
            return entry
    raise ValueError(f"Project not found: {name}")


def read_project_recovery(name: str) -> str:
    entry = get_project(name)
    return entry.recovery.read_text(encoding="utf-8")


def append_actions_log(
    *,
    what_changed: str,
    why_changed: str,
    verification_status: str,
    rollback_strategy_or_note: str = "not specified",
    relogin_or_reboot_requirement: str = "not required",
) -> str:
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    line = (
        f"{timestamp} | Changed {what_changed} | Why: {why_changed} | "
        f"Verification: {verification_status} | Rollback: {rollback_strategy_or_note} | "
        f"Relogin/Reboot: {relogin_or_reboot_requirement}"
    )
    with ACTIONS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return line

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import re
from collections import Counter


PROJECT_ROOT = Path("/home/japonamat/pet/projects/Photo_Trap")
RECOVERY_FILE = PROJECT_ROOT / ".ai-recovery.md"
TODO_FILE = PROJECT_ROOT / "docs" / "TODO.md"
SOURCE_ROOT = PROJECT_ROOT / "app" / "src" / "main" / "java" / "com" / "cmdrjaponamat" / "phototrap"
KT_LIMIT = 700
SEAM_SUFFIXES = ("Policy", "Repository", "Controller", "Coordinator", "Resolver")
STOPWORDS = {
    "refactor",
    "extract",
    "split",
    "remove",
    "after",
    "main",
    "state",
    "runtime",
    "photo",
    "trap",
    "with",
    "from",
    "into",
    "update",
    "refresh",
    "docs",
    "seam",
}


@dataclass(frozen=True)
class CodeSearchHit:
    path: Path
    line_number: int
    line: str


@dataclass(frozen=True)
class KotlinFileStat:
    path: Path
    line_count: int


@dataclass(frozen=True)
class KotlinTypeDef:
    name: str
    kind: str
    path: Path
    seam_like: bool


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


def _list_kotlin_files() -> list[Path]:
    return [item.path for item in _collect_kotlin_file_stats()]


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


def _collect_type_definitions() -> tuple[dict[str, KotlinTypeDef], dict[Path, list[str]]]:
    type_defs: dict[str, KotlinTypeDef] = {}
    file_types: dict[Path, list[str]] = {}
    pattern = re.compile(r"^\s*(class|interface|object|data class)\s+([A-Za-z_][A-Za-z0-9_]*)")
    for path in _list_kotlin_files():
        names: list[str] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            match = pattern.match(raw_line)
            if not match:
                continue
            kind = match.group(1)
            name = match.group(2)
            seam_like = kind == "interface" or name.endswith(SEAM_SUFFIXES)
            type_defs[name] = KotlinTypeDef(
                name=name,
                kind=kind,
                path=path,
                seam_like=seam_like,
            )
            names.append(name)
        file_types[path] = names
    return type_defs, file_types


def _internal_imports(path: Path) -> list[str]:
    imports: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.strip()
        if not raw_line.startswith("import com.cmdrjaponamat.phototrap."):
            continue
        imported_name = raw_line.rsplit(".", 1)[-1]
        imports.append(imported_name)
    return imports


def module_seam_check(top_n: int = 12) -> dict:
    type_defs, _ = _collect_type_definitions()
    seam_types = [item for item in type_defs.values() if item.seam_like]
    seam_types.sort(key=lambda item: (_normalize_path(item.path), item.name))

    aligned_files: list[dict] = []
    hard_dependency_files: list[dict] = []
    hard_dependency_counter: Counter[str] = Counter()

    for path in _list_kotlin_files():
        imports = _internal_imports(path)
        seam_deps: list[str] = []
        hard_deps: list[str] = []
        for imported_name in imports:
            type_def = type_defs.get(imported_name)
            if type_def is None:
                hard_deps.append(imported_name)
                hard_dependency_counter[imported_name] += 1
                continue
            if type_def.seam_like:
                seam_deps.append(imported_name)
            else:
                hard_deps.append(imported_name)
                hard_dependency_counter[imported_name] += 1

        if seam_deps and not hard_deps:
            aligned_files.append(
                {
                    "path": _normalize_path(path),
                    "seam_dependencies": sorted(set(seam_deps)),
                }
            )
        elif hard_deps:
            hard_dependency_files.append(
                {
                    "path": _normalize_path(path),
                    "hard_dependencies": sorted(set(hard_deps)),
                    "seam_dependencies": sorted(set(seam_deps)),
                }
            )

    aligned_files.sort(key=lambda item: item["path"])
    hard_dependency_files.sort(
        key=lambda item: (-len(item["hard_dependencies"]), item["path"])
    )

    top_hard_dependencies = [
        {"name": name, "count": count}
        for name, count in hard_dependency_counter.most_common(top_n)
    ]

    return {
        "project_root": str(PROJECT_ROOT),
        "seam_type_count": len(seam_types),
        "seam_types": [
            {
                "name": item.name,
                "kind": item.kind,
                "path": _normalize_path(item.path),
            }
            for item in seam_types[:top_n]
        ],
        "files_with_only_seam_dependencies": aligned_files[:top_n],
        "files_with_hard_dependencies": hard_dependency_files[:top_n],
        "top_hard_dependencies": top_hard_dependencies,
    }


def _recent_architecture_commits(limit: int = 20) -> list[tuple[str, str]]:
    completed = _run_command(
        ["git", "log", "--no-merges", f"-n{limit}", "--pretty=format:%H\t%s"]
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git log failed")
    commits: list[tuple[str, str]] = []
    for raw_line in completed.stdout.splitlines():
        if "\t" not in raw_line:
            continue
        commit_hash, subject = raw_line.split("\t", 1)
        lowered = subject.lower()
        if lowered.startswith("docs:"):
            continue
        if not any(
            marker in lowered
            for marker in ("refactor:", "split", "extract", "isolate", "seam", "controller", "policy")
        ):
            continue
        commits.append((commit_hash, subject))
    return commits


def _normalized_commit_subject(subject: str) -> str:
    lowered = subject.lower()
    return re.sub(r"^[a-z]+:\s*", "", lowered).strip()


def _subject_keywords(subject: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-zа-я0-9_]+", _normalized_commit_subject(subject))
        if len(token) >= 4 and token not in STOPWORDS
    }
    return tokens


def _looks_reflected(subject: str, document_text: str) -> bool:
    normalized_doc = document_text.lower()
    normalized_subject = _normalized_commit_subject(subject)
    if normalized_subject and normalized_subject in normalized_doc:
        return True
    keywords = _subject_keywords(subject)
    if len(keywords) >= 2:
        matched = sum(1 for token in keywords if token in normalized_doc)
        return matched >= 2
    return False


def recovery_sync_audit(limit: int = 20) -> dict:
    recovery_text = read_recovery()
    todo_text = TODO_FILE.read_text(encoding="utf-8")
    commits = _recent_architecture_commits(limit=limit)

    rows = []
    recovery_missing = 0
    todo_missing = 0
    for commit_hash, subject in commits:
        in_recovery = _looks_reflected(subject, recovery_text)
        in_todo = _looks_reflected(subject, todo_text)
        if not in_recovery:
            recovery_missing += 1
        if not in_todo:
            todo_missing += 1
        rows.append(
            {
                "hash": commit_hash[:7],
                "subject": subject,
                "reflected_in_recovery": in_recovery,
                "reflected_in_todo": in_todo,
            }
        )

    return {
        "project_root": str(PROJECT_ROOT),
        "commit_count": len(rows),
        "recovery_missing_count": recovery_missing,
        "todo_missing_count": todo_missing,
        "commits": rows,
    }


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

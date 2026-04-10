from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row


_ENV_KEYS = {
    "AI_CONTEXT_DSN",
    "AI_CONTEXT_CONNECT_TIMEOUT",
}


@dataclass(frozen=True)
class DBSettings:
    dsn: str
    connect_timeout_seconds: int

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "DBSettings":
        if environ is None:
            env = dict(os.environ)
            env = _merge_env_file_defaults(env)
        else:
            env = dict(environ)

        dsn = (env.get("AI_CONTEXT_DSN") or "postgresql://japonamat@127.0.0.1/ai_context").strip()
        connect_timeout = int((env.get("AI_CONTEXT_CONNECT_TIMEOUT") or "10").strip())
        if connect_timeout <= 0:
            raise ValueError("AI_CONTEXT_CONNECT_TIMEOUT must be > 0")
        return cls(dsn=dsn, connect_timeout_seconds=connect_timeout)


def _merge_env_file_defaults(env: dict[str, str]) -> dict[str, str]:
    merged = dict(env)
    for candidate in _candidate_env_paths():
        values = _read_env_file(candidate)
        for key, value in values.items():
            if key in _ENV_KEYS and not (merged.get(key) or "").strip():
                merged[key] = value
    return merged


def _candidate_env_paths() -> list[Path]:
    project_root = Path(__file__).resolve().parents[1]
    return [
        Path.cwd() / ".env",
        project_root / ".env",
        Path.home() / ".ai_context.env",
    ]


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class DBRepository:
    def __init__(self, settings: DBSettings | None = None) -> None:
        self.settings = settings or DBSettings.from_env()

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection[Any]]:
        conn = psycopg.connect(
            self.settings.dsn,
            connect_timeout=self.settings.connect_timeout_seconds,
            row_factory=dict_row,
        )
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[psycopg.Connection[Any]]:
        with self.connect() as conn:
            with conn.transaction():
                yield conn

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)

    def execute_returning_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row is not None else None

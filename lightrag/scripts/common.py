from __future__ import annotations

from functools import partial
from pathlib import Path
import json
import shutil
import urllib.error
import urllib.request

from lightrag import LightRAG
from lightrag.base import QueryParam
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc


ROOT = Path("/home/japonamat/ai/lightrag")
AI_INDEX_DIR = ROOT / "ai_index"
CONFIG_PATH = AI_INDEX_DIR / "config.json"
SOURCES_PATH = AI_INDEX_DIR / "sources.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict:
    return load_json(CONFIG_PATH)


def load_sources() -> list[Path]:
    payload = load_json(SOURCES_PATH)
    resolved: list[Path] = []

    for file_path in payload.get("files", []):
        path = Path(file_path)
        if path.is_file():
            resolved.append(path)

    for pattern in payload.get("globs", []):
        for path in sorted(Path("/").glob(pattern.lstrip("/"))):
            if path.is_file():
                resolved.append(path)

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in resolved:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def check_ollama_server(host: str) -> None:
    url = host.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            if response.status != 200:
                raise RuntimeError(f"Ollama server returned HTTP {response.status}")
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama server is not reachable at {host}. Start it with `ollama serve`."
        ) from exc


def fetch_ollama_models(host: str) -> set[str]:
    url = host.rstrip("/") + "/api/tags"
    with urllib.request.urlopen(url, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {model["name"] for model in payload.get("models", [])}


def validate_ollama_models(host: str, llm_model: str, embedding_model: str) -> None:
    models = fetch_ollama_models(host)
    missing = [model for model in (llm_model, embedding_model) if model not in models]
    if missing:
        quoted = ", ".join(missing)
        raise RuntimeError(
            "Missing Ollama model(s): "
            f"{quoted}. Pull them first with `ollama pull <model>`."
        )


def build_rag(config: dict) -> LightRAG:
    host = config["ollama_host"]
    llm_model = config["llm_model"]
    embedding_model = config["embedding_model"]
    embedding_dim = config["embedding_dim"]

    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,
        model_name=embedding_model,
        func=partial(ollama_embed.func, embed_model=embedding_model, host=host),
    )

    return LightRAG(
        working_dir=config["working_dir"],
        llm_model_name=llm_model,
        llm_model_func=partial(ollama_model_complete, host=host),
        embedding_func=embedding_func,
        auto_manage_storages_states=True,
    )


def read_documents(paths: list[Path]) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    file_paths: list[str] = []
    for path in paths:
        texts.append(path.read_text(encoding="utf-8"))
        file_paths.append(str(path))
    return texts, file_paths


def reset_working_dir(path_text: str) -> None:
    path = Path(path_text)
    if path.exists():
        shutil.rmtree(path)


def build_query_param(config: dict) -> QueryParam:
    return QueryParam(mode=config.get("query_mode", "mix"))

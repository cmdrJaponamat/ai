from __future__ import annotations

import argparse
import json
import sys

from common import (
    build_rag,
    check_ollama_server,
    load_config,
    load_sources,
    read_documents,
    reset_working_dir,
    validate_ollama_models,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build ~/ai LightRAG index")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config()
    sources = load_sources()

    if not sources:
        raise RuntimeError("No sources resolved for ai_index")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "config": config,
                    "source_count": len(sources),
                    "sources": [str(path) for path in sources],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    check_ollama_server(config["ollama_host"])
    validate_ollama_models(
        config["ollama_host"],
        config["llm_model"],
        config["embedding_model"],
    )

    if args.rebuild:
        reset_working_dir(config["working_dir"])

    rag = build_rag(config)
    texts, file_paths = read_documents(sources)
    track_id = rag.insert(texts, file_paths=file_paths)

    print(
        json.dumps(
            {
                "status": "ok",
                "track_id": track_id,
                "working_dir": config["working_dir"],
                "source_count": len(sources),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

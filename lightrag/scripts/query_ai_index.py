from __future__ import annotations

import argparse
import sys

from common import (
    build_query_param,
    build_rag,
    check_ollama_server,
    load_config,
    validate_ollama_models,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query ~/ai LightRAG index")
    parser.add_argument("query")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config()

    check_ollama_server(config["ollama_host"])
    validate_ollama_models(
        config["ollama_host"],
        config["llm_model"],
        config["embedding_model"],
    )

    rag = build_rag(config)
    result = rag.query(args.query, param=build_query_param(config))
    print(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

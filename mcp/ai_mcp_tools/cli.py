from __future__ import annotations

import argparse
import json
import sys

from tools import (
    read_file,
    read_recovery,
    search,
    snapshot_audit,
    status,
    tooling_audit,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local ai-mcp-tools CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ai-mcp-status")
    subparsers.add_parser("ai-mcp-read-recovery")
    subparsers.add_parser("ai-mcp-snapshot-audit")
    subparsers.add_parser("ai-mcp-tooling-audit")

    read_file_parser = subparsers.add_parser("ai-mcp-read-file")
    read_file_parser.add_argument("relative_path")

    search_parser = subparsers.add_parser("ai-mcp-search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ai-mcp-status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "ai-mcp-read-recovery":
        print(read_recovery())
        return 0

    if args.command == "ai-mcp-snapshot-audit":
        print(json.dumps(snapshot_audit(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "ai-mcp-tooling-audit":
        print(json.dumps(tooling_audit(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "ai-mcp-read-file":
        print(read_file(args.relative_path))
        return 0

    if args.command == "ai-mcp-search":
        print(json.dumps(search(args.query, limit=args.limit), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())


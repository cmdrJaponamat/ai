from __future__ import annotations

import argparse
import json
import sys

from tools import project_status, read_file, read_recovery, search_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local phototrap-tools CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("phototrap-status")
    subparsers.add_parser("phototrap-read-recovery")

    read_file_parser = subparsers.add_parser("phototrap-read-file")
    read_file_parser.add_argument("relative_path")

    search_parser = subparsers.add_parser("phototrap-search-code")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "phototrap-status":
        print(json.dumps(project_status(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "phototrap-read-recovery":
        print(read_recovery())
        return 0

    if args.command == "phototrap-read-file":
        print(read_file(args.relative_path))
        return 0

    if args.command == "phototrap-search-code":
        payload = [
            {
                "path": str(hit.path),
                "line_number": hit.line_number,
                "line": hit.line,
            }
            for hit in search_code(args.query, limit=args.limit)
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

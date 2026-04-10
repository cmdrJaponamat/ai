from __future__ import annotations

import argparse
import json
import sys

from tools import (
    module_seam_check,
    project_status,
    read_file,
    read_recovery,
    recovery_sync_audit,
    refactor_checkpoint,
    safe_split_audit,
    search_code,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local phototrap-tools CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("phototrap-status")
    subparsers.add_parser("phototrap-read-recovery")

    split_audit_parser = subparsers.add_parser("phototrap-safe-split-audit")
    split_audit_parser.add_argument("--top-n", type=int, default=15)
    split_audit_parser.add_argument("--line-limit", type=int, default=700)

    checkpoint_parser = subparsers.add_parser("phototrap-refactor-checkpoint")
    checkpoint_parser.add_argument("--top-n", type=int, default=10)
    checkpoint_parser.add_argument("--line-limit", type=int, default=700)

    recovery_sync_parser = subparsers.add_parser("phototrap-recovery-sync-audit")
    recovery_sync_parser.add_argument("--limit", type=int, default=20)

    seam_parser = subparsers.add_parser("phototrap-module-seam-check")
    seam_parser.add_argument("--top-n", type=int, default=12)

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

    if args.command == "phototrap-safe-split-audit":
        print(
            json.dumps(
                safe_split_audit(top_n=args.top_n, line_limit=args.line_limit),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "phototrap-refactor-checkpoint":
        print(
            json.dumps(
                refactor_checkpoint(top_n=args.top_n, line_limit=args.line_limit),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "phototrap-recovery-sync-audit":
        print(
            json.dumps(
                recovery_sync_audit(limit=args.limit),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "phototrap-module-seam-check":
        print(
            json.dumps(
                module_seam_check(top_n=args.top_n),
                ensure_ascii=False,
                indent=2,
            )
        )
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

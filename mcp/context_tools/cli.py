from __future__ import annotations

import argparse
import json
import sys

from tools import get_project, list_projects, list_snapshots, record_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local context-tools CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("context-list-projects")

    get_project_parser = subparsers.add_parser("context-get-project")
    get_project_parser.add_argument("project_name")

    list_snapshots_parser = subparsers.add_parser("context-list-snapshots")
    list_snapshots_parser.add_argument("project_name")
    list_snapshots_parser.add_argument("--snapshot-type")
    list_snapshots_parser.add_argument("--limit", type=int, default=10)

    record_snapshot_parser = subparsers.add_parser("context-record-snapshot")
    record_snapshot_parser.add_argument("project_name")
    record_snapshot_parser.add_argument("snapshot_type")
    record_snapshot_parser.add_argument("payload_json")
    record_snapshot_parser.add_argument("--title")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "context-list-projects":
        print(json.dumps(list_projects(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "context-get-project":
        print(json.dumps(get_project(args.project_name), ensure_ascii=False, indent=2))
        return 0

    if args.command == "context-list-snapshots":
        print(
            json.dumps(
                list_snapshots(
                    args.project_name,
                    snapshot_type=args.snapshot_type,
                    limit=args.limit,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "context-record-snapshot":
        print(
            json.dumps(
                record_snapshot(
                    args.project_name,
                    args.snapshot_type,
                    json.loads(args.payload_json),
                    title=args.title,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

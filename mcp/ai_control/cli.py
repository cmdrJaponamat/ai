from __future__ import annotations

import argparse
import json
import sys

from tools import append_actions_log, list_projects, read_project_recovery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local ai-control CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-projects")

    recovery_parser = subparsers.add_parser("read-project-recovery")
    recovery_parser.add_argument("project_name")

    log_parser = subparsers.add_parser("append-actions-log")
    log_parser.add_argument("--what", required=True)
    log_parser.add_argument("--why", required=True)
    log_parser.add_argument("--verification", required=True)
    log_parser.add_argument("--rollback", default="not specified")
    log_parser.add_argument("--relogin", default="not required")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list-projects":
        payload = [
            {
                "name": entry.name,
                "path": str(entry.path),
                "recovery": str(entry.recovery),
            }
            for entry in list_projects()
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "read-project-recovery":
        print(read_project_recovery(args.project_name))
        return 0

    if args.command == "append-actions-log":
        print(
            append_actions_log(
                what_changed=args.what,
                why_changed=args.why,
                verification_status=args.verification,
                rollback_strategy_or_note=args.rollback,
                relogin_or_reboot_requirement=args.relogin,
            )
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

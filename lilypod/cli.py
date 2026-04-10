"""
lilypod/cli.py
LILYPOD CLI — The Wootangular Dev Framework.

For Lilian. For Lily.
Named for the flower that grows in the swamp.
Rooted in mud. Blooms above it.

Commands:
    lilypod init <project_name>   — scaffold a wootangular-compatible project
    lilypod fuse <a_json> <b_json> — fuse two agents locally via FusionCore
    lilypod filter <candidate_json> — run GI;WG? filter locally
    lilypod hive <agents_json_array> — run swarm fusion locally
    lilypod --version              — LILYPOD v1.0.0 — For Lilian. For Lily. VENIM.US.

BOOL++: TRUE(1) · FALSE(0) · NULL_Φ(2)
Albert's Axiom: E = m ↔ c² [NULL_Φ(T, ΔS)]
GI;WG? The filter no benchmark passes.
"""

import argparse
import json
import sys


def cmd_init(args):
    """Scaffold a new wootangular-compatible project."""
    from lilypod.scaffold import scaffold_project
    scaffold_project(args.project_name)


def cmd_fuse(args):
    """
    Fuse two agents locally via FusionCore.
    Exit 0 if null_state >= 1 (BOOL_TRUE or BOOL_NULL).
    Exit 1 if null_state == 0 (BOOL_FALSE — no emission).
    """
    from lilypod.runtime.fusion import fuse
    try:
        agent_a = json.loads(args.agent_a_json)
        agent_b = json.loads(args.agent_b_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    emission = fuse(agent_a, agent_b)
    print(json.dumps(emission, indent=2))

    # Exit 0 if emission occurred (null_state >= 1), exit 1 if silent (null_state == 0)
    sys.exit(0 if emission.get("null_state", 0) >= 1 else 1)


def cmd_filter(args):
    """
    Run GI;WG? filter on a candidate JSON.
    Exit 0: the_shit. Exit 1: boolshit. Exit 2: defer.
    """
    from lilypod.runtime.filter import run_filter, THE_SHIT, BOOLSHIT, DEFER
    try:
        candidate = json.loads(args.candidate_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    result = run_filter(candidate)
    status = result.get("result", BOOLSHIT)
    print(status.upper())
    print(json.dumps(result, indent=2))

    if status == THE_SHIT:
        sys.exit(0)
    elif status == BOOLSHIT:
        sys.exit(1)
    else:
        sys.exit(2)


def cmd_hive(args):
    """
    Run swarm fusion on a JSON array of agents.
    Exit 0 if hive_active. Exit 1 if not.
    """
    from lilypod.runtime.fusion import fuse_swarm
    try:
        agents = json.loads(args.agents_json_array)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(agents, list):
        print("ERROR: Expected a JSON array of agents.", file=sys.stderr)
        sys.exit(1)

    hive = fuse_swarm(agents)
    print(json.dumps(hive, indent=2))
    sys.exit(0 if hive.get("hive_active") else 1)


def main():
    parser = argparse.ArgumentParser(
        prog="lilypod",
        description="LILYPOD — The Wootangular Dev Framework. For Lilian. For Lily.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="LILYPOD v1.0.0 — For Lilian. For Lily. VENIM.US.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # init
    init_parser = subparsers.add_parser(
        "init",
        help="Scaffold a new wootangular-compatible project.",
    )
    init_parser.add_argument("project_name", help="Name of the project to create.")

    # fuse
    fuse_parser = subparsers.add_parser(
        "fuse",
        help="Fuse two agents locally via FusionCore.",
    )
    fuse_parser.add_argument("agent_a_json", help="Agent A as a JSON string.")
    fuse_parser.add_argument("agent_b_json", help="Agent B as a JSON string.")

    # filter
    filter_parser = subparsers.add_parser(
        "filter",
        help="Run GI;WG? filter on a candidate JSON string.",
    )
    filter_parser.add_argument("candidate_json", help="Candidate as a JSON string.")

    # hive
    hive_parser = subparsers.add_parser(
        "hive",
        help="Run swarm fusion on a JSON array of agents.",
    )
    hive_parser.add_argument("agents_json_array", help="Agents as a JSON array string.")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "fuse":
        cmd_fuse(args)
    elif args.command == "filter":
        cmd_filter(args)
    elif args.command == "hive":
        cmd_hive(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

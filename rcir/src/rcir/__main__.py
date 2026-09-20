"""RCIR CLI entry point — python -m rcir."""

import sys


def main():
    """Route to the appropriate subcommand."""
    if len(sys.argv) < 2:
        print("Usage: python -m rcir <command> [args]")
        print()
        print("Commands:")
        print("  extract    Extract dependency graph from a Python repository")
        print("  hierarchy  Build hierarchy view from a dependency graph")
        print("  diff       Compute state-split diffs between code versions")
        print("  retrieve   Hybrid context retrieval with token budget")
        sys.exit(1)

    command = sys.argv[1]
    # Remove the subcommand from argv so sub-modules see clean args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "extract":
        from rcir.graph.extractor import main as extract_main
        extract_main()
    elif command == "hierarchy":
        from rcir.hierarchy.builder import main as hierarchy_main
        hierarchy_main()
    elif command == "diff":
        from rcir.state.diff import main as diff_main
        diff_main()
    elif command == "retrieve":
        from rcir.retrieval.hybrid import main as retrieve_main
        retrieve_main()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

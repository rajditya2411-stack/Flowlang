"""FlowLang CLI & Interactive REPL.

Entry point for running FlowLang source files or launching an interactive session.
Usage:
  python main.py run <path_to_file.flow>
  python main.py repl
"""

import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from flowlang.engine import execute
from flowlang.runtime import Environment, stringify_value
from flowlang import __version__


def run_file(file_path: str) -> int:
    """Read and execute a FlowLang file."""
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
        return 1

    result = execute(source)

    if result.output:
        print(result.output)

    if result.error:
        print(result.formatted_error, file=sys.stderr)
        return 1

    return 0


def run_repl() -> None:
    """Start interactive FlowLang REPL session."""
    print(f"FlowLang REPL (v{__version__})")
    print("Type 'exit' or press Ctrl+C to exit.\n")

    # Persistent global environment across REPL commands
    repl_env = Environment()

    while True:
        try:
            line = input("flow> ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        line = line.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        res = execute(line, environment=repl_env)

        if res.output:
            print(res.output)

        if res.error:
            print(res.formatted_error)
        elif res.value is not None:
            print(stringify_value(res.value))


def print_usage() -> None:
    print(f"FlowLang v{__version__}")
    print("Usage:")
    print("  python main.py run <filename.flow>   Run a FlowLang program file")
    print("  python main.py repl                  Start an interactive REPL session")
    print("  python main.py <filename.flow>       Shorthand to run a file")


def main() -> int:
    if len(sys.argv) < 2:
        print_usage()
        return 0

    command = sys.argv[1]

    if command == "repl":
        run_repl()
        return 0
    elif command == "run":
        if len(sys.argv) < 3:
            print("Error: No input file specified for 'run'.", file=sys.stderr)
            print("Usage: python main.py run <filename.flow>", file=sys.stderr)
            return 1
        return run_file(sys.argv[2])
    elif command in ("-h", "--help", "help"):
        print_usage()
        return 0
    elif command.endswith(".flow") or os.path.isfile(command):
        return run_file(command)
    else:
        print(f"Unknown command: '{command}'\n", file=sys.stderr)
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())

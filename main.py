import sys
import importlib

COMMANDS = {
    "play": "src.entrypoint",
    "monte-carlo": "scripts.monte_carlo",
    "train": "scripts.train_rl",
    "pbt-train": "scripts.pbt_train_rl",
    "evaluate": "scripts.evaluate_rl",
}


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS:
        command = sys.argv[1]
        sys.argv = [sys.argv[0]] + sys.argv[2:]
    elif len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        _print_help()
        return
    else:
        command = "play"

    module = importlib.import_module(COMMANDS[command])
    module.main()


def _print_help() -> None:
    print("Usage: python main.py <command> [options]\n")
    print("Commands:")
    for cmd in COMMANDS:
        print(f"  {cmd}")
    print("\nRun 'python main.py <command> --help' for command-specific options.")


if __name__ == "__main__":
    main()

# run_defipilot_v6_launcher3.py – V6.0

import sys


def detect_mode(argv: list[str]) -> str:
    if "--help" in argv or "-h" in argv:
        return "help"
    if "--gui" in argv:
        return "gui"
    if "--simulate" in argv:
        return "simulate"
    if "--cli" in argv:
        return "cli"
    return "gui"


def print_help() -> None:
    print("DeFiPilot V6.0")
    print("Modes disponibles :")
    print("--gui")
    print("--cli")
    print("--simulate")
    print("--help")


def run_gui() -> int:
    from gui.main_window import MainWindow

    app = MainWindow()
    app.mainloop()
    return 0


def run_cli(argv: list[str]) -> int:
    from main import main

    full_argv = ["main.py", *argv]
    return int(main(full_argv))


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = detect_mode(args)

    if mode == "help":
        print_help()
        raise SystemExit(0)
    if mode == "gui":
        raise SystemExit(run_gui())
    if mode == "cli" or mode == "simulate":
        raise SystemExit(run_cli(args))
    raise SystemExit(run_gui())
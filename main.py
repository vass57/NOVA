"""Backward-compatible command-line entry point for CorroborIA."""

from corroboria.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

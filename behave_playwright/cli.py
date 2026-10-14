"""Command line interface for behave-playwright."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from behave_playwright import __version__


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``behave-playwright`` command."""
    parser = argparse.ArgumentParser(
        prog="behave-playwright",
        description="Behave + Playwright BDD helpers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

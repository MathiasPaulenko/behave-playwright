"""Command line interface for behave-playwright."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from behave_playwright import __version__

_SCAFFOLD_FILES = {
    "behave.ini": """\
[behave]
format = pretty
stdout_capture = true
stderr_capture = true
""",
    "features/environment.py": """\
from behave_playwright.environment import *  # noqa: F401,F403
""",
    "features/steps/behave_playwright_steps.py": """\
import behave_playwright.steps  # noqa: F401 — registers the bundled steps
""",
    "features/example.feature": """\
Feature: Example
  A first scenario to check the behave-playwright wiring.

  Scenario: Example Domain
    Given I navigate to "https://example.com"
    Then the title should contain "Example"
    And the "Learn more" element should be visible
""",
}


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``behave-playwright`` command."""
    parser = argparse.ArgumentParser(
        prog="behave-playwright",
        description="Behave + Playwright BDD helpers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser(
        "init", help="Scaffold a behave project wired for behave-playwright."
    )
    init.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Where to create the scaffold (default: current directory).",
    )
    init.add_argument("-f", "--force", action="store_true", help="Overwrite existing files.")

    args = parser.parse_args(argv)
    if args.command == "init":
        return _cmd_init(Path(args.directory), force=args.force)
    parser.print_help()
    return 0


def _cmd_init(directory: Path, force: bool = False) -> int:
    if directory.exists() and not directory.is_dir():
        print(f"error: {directory} exists and is not a directory")
        return 1
    created, skipped = [], []
    for rel_path, content in _SCAFFOLD_FILES.items():
        path = directory / rel_path
        if path.exists() and not force:
            skipped.append(rel_path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        created.append(rel_path)

    for rel_path in created:
        print(f"  created  {rel_path}")
    for rel_path in skipped:
        print(f"  skipped  {rel_path} (exists — use --force to overwrite)")

    if created:
        print("\nDone. Run `playwright install` once, then `behave` to try it out.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

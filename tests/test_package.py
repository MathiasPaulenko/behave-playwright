"""Smoke tests for the package scaffold."""

import pytest

import behave_playwright
from behave_playwright.cli import main


def test_version() -> None:
    assert behave_playwright.__version__


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert behave_playwright.__version__ in capsys.readouterr().out


def test_cli_no_args() -> None:
    assert main([]) == 0

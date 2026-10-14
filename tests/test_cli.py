"""Tests for the behave-playwright CLI."""

from pathlib import Path

import pytest

from behave_playwright.cli import main


def test_init_creates_scaffold(tmp_path: Path) -> None:
    assert main(["init", "-d", str(tmp_path)]) == 0
    assert (tmp_path / "behave.ini").is_file()
    assert (tmp_path / "features/environment.py").is_file()
    assert (tmp_path / "features/steps/behave_playwright_steps.py").is_file()
    assert (tmp_path / "features/example.feature").is_file()
    assert "navigate to" in (tmp_path / "features/example.feature").read_text()


def test_init_does_not_overwrite(tmp_path: Path) -> None:
    main(["init", "-d", str(tmp_path)])
    env_file = tmp_path / "features/environment.py"
    env_file.write_text("# custom")
    main(["init", "-d", str(tmp_path)])
    assert env_file.read_text() == "# custom"


def test_init_force_overwrites(tmp_path: Path) -> None:
    main(["init", "-d", str(tmp_path)])
    env_file = tmp_path / "features/environment.py"
    env_file.write_text("# custom")
    main(["init", "-d", str(tmp_path), "--force"])
    assert "behave_playwright.environment" in env_file.read_text()


def test_init_missing_directory_created(tmp_path: Path) -> None:
    target = tmp_path / "new-project"
    assert main(["init", "-d", str(target)]) == 0
    assert (target / "features/example.feature").is_file()


def test_unknown_command_is_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["bogus"])
    assert exc_info.value.code != 0


def test_init_rejects_file_as_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    existing = tmp_path / "afile"
    existing.write_text("x")
    assert main(["init", "-d", str(existing)]) == 1
    assert "not a directory" in capsys.readouterr().out

"""Tests for session steps: device emulation, storage state, tracing."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from behave.model import Status

from behave_playwright import BrowserConfig, environment
from behave_playwright.steps import session


def test_emulate_device_recreates_context(env_context: SimpleNamespace) -> None:
    old_page = env_context.page
    session.step_emulate_device(env_context, "iPhone 12")
    assert env_context.page is not old_page
    assert "iPhone" in env_context.page.evaluate("navigator.userAgent")


def test_emulate_unknown_device(env_context: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="Unknown Playwright device"):
        session.step_emulate_device(env_context, "Nokia 3310")


def test_save_and_use_storage_state(env_context: SimpleNamespace, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    session.step_save_storage_state(env_context, str(state_path))
    assert state_path.is_file()

    old_page = env_context.page
    session.step_use_storage_state(env_context, str(state_path))
    assert env_context.page is not old_page


def test_use_missing_storage_state(env_context: SimpleNamespace) -> None:
    with pytest.raises(FileNotFoundError, match="storage state"):
        session.step_use_storage_state(env_context, "nope.json")


def test_logged_in_as(
    env_context: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    auth = tmp_path / "auth"
    auth.mkdir()
    (auth / "ada.json").write_text('{"cookies": [], "origins": []}')

    session.step_logged_in_as(env_context, "ada")
    assert env_context.page is not None


def test_logged_in_as_missing_file(
    env_context: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="stored session"):
        session.step_logged_in_as(env_context, "ghost")


@pytest.mark.parametrize("user", ["../evil", "a/b", "..", "a\\b", ""])
def test_logged_in_as_rejects_path_traversal(
    env_context: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, user: str
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "auth").mkdir()
    with pytest.raises(ValueError, match="invalid user name"):
        session.step_logged_in_as(env_context, user)


def test_tracing_saved_on_failure(env_context: SimpleNamespace, tmp_path: Path) -> None:
    env_context.bp_config = BrowserConfig(traces_dir=str(tmp_path), screenshots_dir=str(tmp_path))
    session.step_enable_tracing(env_context)
    env_context.page.goto("about:blank")

    environment.after_scenario(env_context, SimpleNamespace(name="boom", status=Status.failed))

    traces = list(tmp_path.glob("*.trace.zip"))
    assert len(traces) == 1
    assert env_context.bp_trace == traces[0]


def test_tracing_not_saved_on_pass(env_context: SimpleNamespace, tmp_path: Path) -> None:
    env_context.bp_config = BrowserConfig(traces_dir=str(tmp_path))
    session.step_enable_tracing(env_context)

    environment.after_scenario(env_context, SimpleNamespace(name="ok", status=Status.passed))

    assert list(tmp_path.glob("*.trace.zip")) == []
    assert not hasattr(env_context, "bp_trace")


@pytest.mark.parametrize("path", ["", "   "])
def test_storage_state_empty_path_fails(env_context: SimpleNamespace, path: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        session.step_save_storage_state(env_context, path)
    with pytest.raises(ValueError, match="empty"):
        session.step_use_storage_state(env_context, path)

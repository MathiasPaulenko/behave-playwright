"""Tests for browser-level steps: tabs, iframes, dialogs, downloads."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from behave.model import Status

from behave_playwright import BrowserConfig, environment
from behave_playwright.steps import assertions, browser


def test_open_new_tab_and_switch(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url)
    env_context.page.goto(base_url)
    browser.step_open_new_tab(env_context, "/next")
    assert env_context.page.url == f"{base_url}/next"
    assert len(env_context.browser_context.pages) == 2

    browser.step_switch_tab(env_context, 1)
    assert env_context.page.url == base_url or env_context.page.url == base_url + "/"


def test_switch_tab_out_of_range(env_context: SimpleNamespace) -> None:
    with pytest.raises(IndexError, match="does not exist"):
        browser.step_switch_tab(env_context, 5)


def test_close_current_tab(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url)
    browser.step_open_new_tab(env_context, "/")
    assert len(env_context.browser_context.pages) == 2
    browser.step_close_tab(env_context)
    assert len(env_context.browser_context.pages) == 1


def test_close_last_tab_fails(env_context: SimpleNamespace) -> None:
    with pytest.raises(RuntimeError, match="last open tab"):
        browser.step_close_tab(env_context)


def test_switch_to_iframe_and_back(env_context: SimpleNamespace) -> None:
    env_context.page.set_content('<iframe name="fr" srcdoc="<p>inside frame</p>"></iframe>')
    env_context.page.wait_for_selector("iframe")
    browser.step_switch_to_iframe(env_context, "fr")
    assertions.step_see_text(env_context, "inside frame")
    browser.step_switch_to_main_frame(env_context)
    assert env_context.page.url == "about:blank"


def test_switch_to_missing_iframe(env_context: SimpleNamespace) -> None:
    env_context.page.set_content("<p>no frames</p>")
    with pytest.raises(LookupError, match="no iframe matches"):
        browser.step_switch_to_iframe(env_context, "nope")


def test_accept_dialog(env_context: SimpleNamespace) -> None:
    browser.step_accept_dialog(env_context)
    env_context.page.evaluate("alert('hello')")  # would block if not handled


def test_dismiss_dialog(env_context: SimpleNamespace) -> None:
    browser.step_dismiss_dialog(env_context)
    result = env_context.page.evaluate("confirm('ok?')")
    assert result is False


def test_answer_dialog(env_context: SimpleNamespace) -> None:
    browser.step_answer_dialog(env_context, "42")
    result = env_context.page.evaluate("prompt('number?')")
    assert result == "42"


def test_click_and_download(env_context: SimpleNamespace, base_url: str, tmp_path: Path) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url, downloads_dir=str(tmp_path))
    env_context.page.goto(base_url)
    browser.step_click_and_download(env_context, "Get file")
    assertions.step_file_downloaded(env_context, "file.txt")
    assert (tmp_path / "file.txt").read_text() == "file contents"


def test_file_not_downloaded_fails(env_context: SimpleNamespace) -> None:
    with pytest.raises(AssertionError, match="no downloaded file"):
        assertions.step_file_downloaded(env_context, "missing.zip")


def test_tab_switch_does_not_duplicate_requests(
    env_context: SimpleNamespace, base_url: str
) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url)
    browser.step_open_new_tab(env_context, "/")
    browser.step_switch_tab(env_context, 1)
    browser.step_switch_tab(env_context, 2)  # back to an already-wired page
    env_context.page.goto(base_url + "/next")
    doc_requests = [r for r in env_context.bp_requests if r.url.endswith("/next")]
    assert len(doc_requests) == 1


def test_nested_iframe_switch_returns_to_main_page(
    env_context: SimpleNamespace,
) -> None:
    env_context.page.set_content(
        '<iframe name="outer" srcdoc="<p>outer</p>"></iframe>'
        '<iframe name="inner2" srcdoc="<p>inner</p>"></iframe>'
    )
    env_context.page.wait_for_selector("iframe")
    original_page = env_context.page
    browser.step_switch_to_iframe(env_context, "outer")
    browser.step_switch_to_iframe(env_context, "inner2")  # second switch
    browser.step_switch_to_main_frame(env_context)
    assert env_context.page is original_page


def test_url_and_title_assertions_inside_iframe(
    env_context: SimpleNamespace, base_url: str
) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url)
    env_context.page.goto(base_url)
    env_context.page.set_content(
        '<html><head><title>Framed</title></head>'
        '<body><iframe name="fr" srcdoc="<p>x</p>"></iframe></body></html>'
    )
    env_context.page.wait_for_selector("iframe")
    browser.step_switch_to_iframe(env_context, "fr")
    assertions.step_url_contains(env_context, "127.0.0.1")
    assertions.step_title_contains(env_context, "Framed")


def test_dialog_steps_work_while_inside_iframe(env_context: SimpleNamespace) -> None:
    env_context.page.set_content('<iframe name="fr" srcdoc="<p>x</p>"></iframe>')
    env_context.page.wait_for_selector("iframe")
    browser.step_switch_to_iframe(env_context, "fr")
    browser.step_accept_dialog(env_context)  # must attach to the real Page
    env_context.page.evaluate("alert('hi')")


def test_failure_inside_iframe_still_captures_screenshot(
    env_context: SimpleNamespace, tmp_path: Path
) -> None:
    env_context.bp_config = BrowserConfig(screenshots_dir=str(tmp_path))
    env_context.page.set_content('<iframe name="fr" srcdoc="<p>x</p>"></iframe>')
    env_context.page.wait_for_selector("iframe")
    browser.step_switch_to_iframe(env_context, "fr")
    # context.page is now a Frame — after_scenario must not crash on it
    env_context.attach = lambda *args: None
    environment.after_scenario(env_context, SimpleNamespace(name="f", status=Status.failed))
    assert list(tmp_path.glob("*.png"))

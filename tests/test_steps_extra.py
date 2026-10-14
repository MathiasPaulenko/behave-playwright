"""Tests for extra interaction steps, cookies, console errors and video."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from behave.model import Status, Table
from playwright.sync_api import Page

from behave_playwright import BrowserConfig, environment
from behave_playwright.steps import assertions, interaction


def test_type_characters(context: SimpleNamespace, page: Page) -> None:
    interaction.step_type(context, "abc", "Email")
    assert page.locator("#email").input_value() == "abc"


def test_fill_form_with_table(context: SimpleNamespace, page: Page) -> None:
    context.table = Table(["field", "value"], [["Email", "a@b.c"], ["Search", "q"]], 0)
    interaction.step_fill_form(context)
    assert page.locator("#email").input_value() == "a@b.c"
    assert page.locator("#search").input_value() == "q"


def test_fill_form_other_headings(context: SimpleNamespace, page: Page) -> None:
    context.table = Table(["input", "text"], [["Email", "x@y.z"]], 0)
    interaction.step_fill_form(context)
    assert page.locator("#email").input_value() == "x@y.z"


def test_fill_form_without_table_fails(context: SimpleNamespace) -> None:
    context.table = None
    with pytest.raises(RuntimeError, match="data table"):
        interaction.step_fill_form(context)


def test_fill_form_single_column_row_fails(context: SimpleNamespace, page: Page) -> None:
    context.table = Table(["field"], [["Email"]], 0)
    with pytest.raises(RuntimeError, match="2 columns"):
        interaction.step_fill_form(context)


def test_select_by_label_not_value(context: SimpleNamespace, page: Page) -> None:
    page.set_content(
        '<select aria-label="Sort"><option value="lohi">Price (low to high)</option></select>'
    )
    interaction.step_select(context, "Sort", "Price (low to high)")
    assert page.locator("select").input_value() == "lohi"


def test_empty_target_rejected(context: SimpleNamespace, page: Page) -> None:
    with pytest.raises(ValueError, match="empty element target"):
        interaction.step_click(context, "  ")


def test_press_key_on_placeholder_target(context: SimpleNamespace, page: Page) -> None:
    # "press on" must resolve fields too, not just clickable roles
    page.set_content('<input placeholder="Type here">')
    interaction.step_press_key_on(context, "a", "Type here")
    assert page.locator("input").input_value() == "a"


def test_scroll_to(context: SimpleNamespace, page: Page) -> None:
    page.set_content('<div style="height:5000px"></div><p id="bottom">down here</p>')
    interaction.step_scroll_to(context, "css=#bottom")
    assert page.evaluate("window.scrollY") > 0


def test_drag_to(context: SimpleNamespace, page: Page) -> None:
    page.set_content(
        """
        <div id="src" draggable="true" style="width:50px;height:50px"></div>
        <div id="dst" style="width:100px;height:100px"
             ondrop="this.textContent='dropped'"
             ondragover="event.preventDefault()"></div>
        """
    )
    interaction.step_drag(context, "css=#src", "css=#dst")
    assert "dropped" in (page.locator("#dst").text_content() or "")


def test_take_screenshot(context: SimpleNamespace, page: Page, tmp_path: Path) -> None:
    context.bp_config = BrowserConfig(screenshots_dir=str(tmp_path))
    context.attach = lambda *args: None
    interaction.step_take_screenshot(context)
    assert list(tmp_path.glob("*.png"))


def test_take_element_screenshot(context: SimpleNamespace, page: Page, tmp_path: Path) -> None:
    context.bp_config = BrowserConfig(screenshots_dir=str(tmp_path))
    context.attach = lambda *args: None
    interaction.step_take_element_screenshot(context, "css=#btn")
    assert list(tmp_path.glob("*.png"))


def test_cookie_assertions(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.page.goto(base_url)
    env_context.browser_context.add_cookies(
        [{"name": "session", "value": "abc123", "url": base_url}]
    )
    assertions.step_cookie_exists(env_context, "session")
    assertions.step_cookie_value(env_context, "session", "abc123")
    with pytest.raises(AssertionError, match="not found"):
        assertions.step_cookie_exists(env_context, "missing")


def test_no_console_errors(env_context: SimpleNamespace) -> None:
    env_context.page.set_content("<p>ok</p>")
    assertions.step_no_console_errors(env_context)


def test_console_error_detected(env_context: SimpleNamespace) -> None:
    env_context.page.evaluate("console.error('boom')")
    with pytest.raises(AssertionError, match="console error"):
        assertions.step_no_console_errors(env_context)


def test_console_error_except_pattern(env_context: SimpleNamespace) -> None:
    env_context.page.evaluate("console.error('boom')")
    assertions.step_no_console_errors_except(env_context, "boo.")


def test_page_error_captured(env_context: SimpleNamespace) -> None:
    env_context.page.evaluate("setTimeout(() => { throw new Error('kaboom') })")
    env_context.page.wait_for_timeout(200)
    with pytest.raises(AssertionError, match="kaboom"):
        assertions.step_no_console_errors(env_context)


def test_video_saved_on_failure(env_context: SimpleNamespace, tmp_path: Path) -> None:
    env_context.bp_config = BrowserConfig(
        record_video=True, video_dir=str(tmp_path), screenshots_dir=str(tmp_path)
    )
    environment.new_browser_context(env_context)
    env_context.page.goto("about:blank")
    environment.after_scenario(env_context, SimpleNamespace(name="boom", status=Status.failed))
    videos = [p for p in tmp_path.glob("*.webm")]
    assert len(videos) == 1
    assert env_context.bp_video == videos[0]


def test_resolve_url_special_schemes() -> None:
    from behave_playwright._context import resolve_url

    ctx = SimpleNamespace(bp_config=BrowserConfig(base_url="http://x"))
    assert resolve_url(ctx, "about:blank") == "about:blank"
    assert resolve_url(ctx, "data:text/html,<p>hi</p>").startswith("data:")
    assert resolve_url(ctx, "https://a.com/x") == "https://a.com/x"
    assert resolve_url(ctx, "/path") == "http://x/path"


def test_video_deleted_on_pass(env_context: SimpleNamespace, tmp_path: Path) -> None:
    env_context.bp_config = BrowserConfig(record_video=True, video_dir=str(tmp_path))
    environment.new_browser_context(env_context)
    env_context.page.goto("about:blank")
    environment.after_scenario(env_context, SimpleNamespace(name="ok", status=Status.passed))
    assert list(tmp_path.glob("*.webm")) == []
    assert not hasattr(env_context, "bp_video")


def test_upload_missing_file_fails(context: SimpleNamespace, page: Page) -> None:
    page.set_content('<input type="file">')
    with pytest.raises(FileNotFoundError, match="file not found"):
        interaction.step_upload(context, "input", "does-not-exist.xyz")


def test_screenshot_without_attach_still_saves(
    context: SimpleNamespace, page: Page, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # context has no .attach (non-behave context) — file must still be saved
    monkeypatch.delattr(context, "attach", raising=False)
    context.bp_config = BrowserConfig(screenshots_dir=str(tmp_path))
    context.scenario = SimpleNamespace(name="shot")
    interaction.step_take_screenshot(context)
    assert list(tmp_path.glob("*.png"))

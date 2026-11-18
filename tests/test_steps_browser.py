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
        "<html><head><title>Framed</title></head>"
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


def test_steps_act_on_main_page_inside_iframe(
    env_context: SimpleNamespace, base_url: str, tmp_path: Path
) -> None:
    from behave_playwright.steps import interaction, navigation, network

    env_context.bp_config = BrowserConfig(base_url=base_url, screenshots_dir=str(tmp_path))
    env_context.page.goto(base_url)
    env_context.page.set_content('<iframe name="fr" srcdoc="<p>x</p>"></iframe>')
    env_context.page.wait_for_selector("iframe")
    browser.step_switch_to_iframe(env_context, "fr")

    network.step_intercept_abort(env_context, "**/nothing")
    env_context.attach = lambda *a: None
    interaction.step_take_screenshot(env_context)
    interaction.step_press_key(env_context, "Tab")
    navigation.step_go_back(env_context)
    navigation.step_reload(env_context)


def test_empty_iframe_name_rejected(env_context: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="empty"):
        browser.step_switch_to_iframe(env_context, "  ")


def test_after_scenario_with_frame_as_page_does_not_crash(
    env_context: SimpleNamespace, tmp_path: Path
) -> None:
    # a custom step left a Frame on context.page without _bp_main_page —
    # teardown must survive it (no artifacts, just cleanup)
    env_context.bp_config = BrowserConfig(screenshots_dir=str(tmp_path))
    env_context.page.set_content('<iframe srcdoc="<p>x</p>"></iframe>')
    env_context.page.wait_for_selector("iframe")
    env_context.page = env_context.page.frames[1]
    environment.after_scenario(env_context, SimpleNamespace(name="f", status=Status.failed))
    assert list(tmp_path.glob("*.png")) == []


def test_popup_initial_request_is_captured(env_context: SimpleNamespace, base_url: str) -> None:
    # the popup's own navigation request fires before wire_page runs —
    # context-level capture must still see it
    from behave_playwright.steps import network

    env_context.bp_config = BrowserConfig(base_url=base_url, timeout=5000)
    env_context.page.goto(base_url)
    env_context.page.set_content('<a href="/next" target="_blank">Go</a>')
    browser.step_click_in_new_tab(env_context, "Go")
    network.step_request_made(env_context, "**/next")


def test_popup_console_errors_are_captured(env_context: SimpleNamespace) -> None:
    env_context.page.set_content('<a href="about:blank" target="_blank">Go</a>')
    browser.step_click_in_new_tab(env_context, "Go")
    env_context.page.evaluate("console.error('popup-boom')")
    env_context.page.wait_for_timeout(100)
    assert "popup-boom" in env_context.bp_console_errors


def test_navigate_to_inside_iframe_uses_main_page(
    env_context: SimpleNamespace, base_url: str
) -> None:
    from behave_playwright.steps import navigation

    env_context.bp_config = BrowserConfig(base_url=base_url)
    env_context.page.goto(base_url)
    env_context.page.set_content('<iframe name="fr" srcdoc="<p>x</p>"></iframe>')
    env_context.page.wait_for_selector("iframe")
    browser.step_switch_to_iframe(env_context, "fr")
    navigation.step_navigate_to(env_context, "/next")  # Frame has no .goto
    assert env_context._bp_main_page.url == f"{base_url}/next"


def test_iframe_exact_name_beats_url_substring(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url)
    env_context.page.goto(base_url)
    # first frame's URL contains "named" — but the second frame is actually
    # named "named": an exact name match must win
    env_context.page.set_content(
        f'<iframe src="{base_url}/next#named"></iframe>'
        '<iframe name="named" srcdoc="<p>the named one</p>"></iframe>'
    )
    env_context.page.wait_for_selector("iframe")
    env_context.page.wait_for_timeout(200)  # let the src iframe load
    browser.step_switch_to_iframe(env_context, "named")
    assertions.step_see_text(env_context, "the named one")


def test_console_listener_recreates_missing_list(env_context: SimpleNamespace) -> None:
    env_context.bp_console_errors = None  # damaged externally between steps
    env_context.page.evaluate("console.error('still-seen')")
    env_context.page.wait_for_timeout(100)
    assert "still-seen" in env_context.bp_console_errors


def test_switch_to_iframe_recovers_stray_frame_page(env_context: SimpleNamespace) -> None:
    # a custom step left a Frame on context.page without _bp_main_page —
    # switching must remember the owning Page, not the Frame (Frame has no
    # .frames and dialogs/downloads need the real Page)
    env_context.page.set_content(
        '<iframe name="outer" srcdoc="<p>x</p>"></iframe>'
        '<iframe name="inner" srcdoc="<p>y</p>"></iframe>'
    )
    env_context.page.wait_for_selector("iframe")
    env_context.page = env_context.page.frames[1]  # stray Frame, no _bp_main_page
    env_context._bp_main_page = None

    browser.step_switch_to_iframe(env_context, "inner")
    browser.step_switch_to_main_frame(env_context)

    from playwright.sync_api import Page

    assert isinstance(env_context.page, Page)


def test_empty_text_assertions_rejected(env_context: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="empty text"):
        assertions.step_see_text(env_context, "")
    with pytest.raises(ValueError, match="empty text"):
        assertions.step_not_see_text(env_context, "")
    with pytest.raises(ValueError, match="empty url fragment"):
        assertions.step_url_contains(env_context, "")
    with pytest.raises(ValueError, match="empty title fragment"):
        assertions.step_title_contains(env_context, "")


def test_wait_text_empty_rejected(env_context: SimpleNamespace) -> None:
    from behave_playwright.steps import waiting

    with pytest.raises(ValueError, match="empty text"):
        waiting.step_wait_text(env_context, "")

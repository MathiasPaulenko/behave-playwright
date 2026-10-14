"""Integration tests for bundled steps against a real Chromium + local server."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from playwright.sync_api import Page

from behave_playwright import BrowserConfig
from behave_playwright._context import resolve_url
from behave_playwright.steps import assertions, interaction, navigation, waiting


def ctx_with_url(context: SimpleNamespace, base_url: str) -> None:
    context.bp_config = BrowserConfig(base_url=base_url)


def test_navigate_absolute(context: SimpleNamespace, page: Page, base_url: str) -> None:
    navigation.step_navigate_to(context, base_url)
    assert page.title() == "Test Site"


def test_navigate_relative_uses_base_url(
    context: SimpleNamespace, page: Page, base_url: str
) -> None:
    ctx_with_url(context, base_url)
    navigation.step_navigate_to(context, "/next")
    assert page.url == f"{base_url}/next"


def test_resolve_url_without_base_url_fails(context: SimpleNamespace) -> None:
    with pytest.raises(RuntimeError, match="base_url"):
        resolve_url(context, "/login")


def test_go_back_and_forward(context: SimpleNamespace, base_url: str) -> None:
    ctx_with_url(context, base_url)
    navigation.step_navigate_to(context, "/")
    navigation.step_navigate_to(context, "/next")
    navigation.step_go_back(context)
    assert context.page.url == f"{base_url}/"
    navigation.step_go_forward(context)
    assert context.page.url == f"{base_url}/next"


def test_reload(context: SimpleNamespace, base_url: str) -> None:
    ctx_with_url(context, base_url)
    navigation.step_navigate_to(context, "/")
    navigation.step_reload(context)
    assert context.page.title() == "Test Site"


def test_click_by_role(context: SimpleNamespace, page: Page) -> None:
    interaction.step_click(context, "Sign in")
    assert page.url.endswith("#clicked")


def test_click_by_testid(context: SimpleNamespace, page: Page) -> None:
    interaction.step_click(context, "testid=greeting")
    assert page.locator("[data-testid='greeting']").count() == 1


def test_click_by_css(context: SimpleNamespace, page: Page) -> None:
    interaction.step_click(context, "css=#btn")
    assert page.url.endswith("#clicked")


def test_fill_by_label(context: SimpleNamespace, page: Page) -> None:
    interaction.step_fill(context, "Email", "user@test.com")
    assert page.locator("#email").input_value() == "user@test.com"


def test_fill_by_placeholder(context: SimpleNamespace, page: Page) -> None:
    interaction.step_fill(context, "Search", "query")
    assert page.locator("#search").input_value() == "query"


def test_clear(context: SimpleNamespace, page: Page) -> None:
    interaction.step_fill(context, "Email", "x")
    interaction.step_clear(context, "Email")
    assert page.locator("#email").input_value() == ""


def test_select_by_label(context: SimpleNamespace, page: Page) -> None:
    interaction.step_select(context, "Fruit", "Banana")
    assert page.locator("#sel").input_value() == "b"


def test_check_and_uncheck(context: SimpleNamespace, page: Page) -> None:
    interaction.step_check(context, "Accept terms")
    assert page.locator("#cb").is_checked()
    interaction.step_uncheck(context, "Accept terms")
    assert not page.locator("#cb").is_checked()


def test_press_key_on_target(context: SimpleNamespace, page: Page) -> None:
    interaction.step_fill(context, "Email", "a")
    interaction.step_press_key_on(context, "Backspace", "Email")
    assert page.locator("#email").input_value() == ""


def test_upload_file(context: SimpleNamespace, page: Page, tmp_path: Path) -> None:
    file = tmp_path / "data.txt"
    file.write_text("content")
    interaction.step_upload(context, "css=#file", str(file))
    assert page.locator("#file").evaluate("el => el.files.length") == 1


def test_see_text(context: SimpleNamespace) -> None:
    assertions.step_see_text(context, "hello from testid")


def test_not_see_hidden_text(context: SimpleNamespace) -> None:
    assertions.step_not_see_text(context, "hidden text")


def test_element_visible_and_hidden(context: SimpleNamespace) -> None:
    assertions.step_element_visible(context, "css=#btn")
    assertions.step_element_hidden(context, "css=#secret")


def test_element_enabled_disabled_checked(context: SimpleNamespace, page: Page) -> None:
    assertions.step_element_enabled(context, "css=#btn")
    page.locator("#btn").evaluate("el => el.disabled = true")
    assertions.step_element_disabled(context, "css=#btn")
    page.locator("#cb").check()
    assertions.step_element_checked(context, "Accept terms")


def test_url_assertions(context: SimpleNamespace, base_url: str) -> None:
    ctx_with_url(context, base_url)
    navigation.step_navigate_to(context, "/")
    assertions.step_url_is(context, "/")
    assertions.step_url_contains(context, "127.0.0.1")


def test_title_assertions(context: SimpleNamespace, base_url: str) -> None:
    navigation.step_navigate_to(context, base_url)
    assertions.step_title_is(context, "Test Site")
    assertions.step_title_contains(context, "Test")


def test_element_count(context: SimpleNamespace) -> None:
    assertions.step_element_count(context, 2, "css=.dup")


def test_element_contains_and_has_text(context: SimpleNamespace) -> None:
    assertions.step_element_contains_text(context, "css=h1", "Hom")
    assertions.step_element_has_text(context, "css=h1", "Home")


def test_element_attribute(context: SimpleNamespace) -> None:
    assertions.step_element_attribute(context, "css=#btn", "id", "btn")


def test_field_value(context: SimpleNamespace) -> None:
    interaction.step_fill(context, "Email", "user@test.com")
    assertions.step_field_value(context, "Email", "user@test.com")


def test_failed_assertion_raises(context: SimpleNamespace) -> None:
    with pytest.raises(AssertionError):
        assertions.step_see_text(context, "no such text")


def test_wait_for_visible_and_hidden(context: SimpleNamespace) -> None:
    waiting.step_wait_visible(context, "css=#btn")
    waiting.step_wait_hidden(context, "css=#secret")


def test_wait_for_text(context: SimpleNamespace) -> None:
    waiting.step_wait_text(context, "hello from testid")


def test_wait_seconds(context: SimpleNamespace) -> None:
    waiting.step_wait_seconds(context, "0")


def test_wait_for_load_state(context: SimpleNamespace, base_url: str) -> None:
    navigation.step_navigate_to(context, base_url)
    waiting.step_wait_load(context)
    waiting.step_wait_network_idle(context)


def test_missing_page_raises() -> None:
    context = SimpleNamespace(bp_config=BrowserConfig())
    with pytest.raises(RuntimeError, match=r"context\.page"):
        navigation.step_navigate_to(context, "http://x.test")

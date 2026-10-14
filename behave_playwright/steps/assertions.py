"""Assertion steps (Playwright web-first auto-retrying assertions)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from behave import then
from playwright.sync_api import expect

from behave_playwright._context import require_page, resolve_url
from behave_playwright.locators import resolve, resolve_first

if TYPE_CHECKING:
    from behave.runner import Context


@then('I should see "{text}"')
@then('I should see the text "{text}"')
def step_see_text(context: Context, text: str) -> None:
    expect(require_page(context).get_by_text(text).first).to_be_visible()


@then('I should not see "{text}"')
@then('I should not see the text "{text}"')
def step_not_see_text(context: Context, text: str) -> None:
    expect(require_page(context).get_by_text(text).first).not_to_be_visible()


@then('the "{target}" element should be visible')
@then('I should see the "{target}" element')
def step_element_visible(context: Context, target: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_be_visible()


@then('the "{target}" element should not be visible')
@then('the "{target}" element should be hidden')
def step_element_hidden(context: Context, target: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_be_hidden()


@then('the "{target}" element should be enabled')
def step_element_enabled(context: Context, target: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_be_enabled()


@then('the "{target}" element should be disabled')
def step_element_disabled(context: Context, target: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_be_disabled()


@then('the "{target}" element should be checked')
def step_element_checked(context: Context, target: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_be_checked()


@then('the "{target}" element should not be checked')
def step_element_not_checked(context: Context, target: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).not_to_be_checked()


@then('the url should be "{url}"')
@then('the page url should be "{url}"')
def step_url_is(context: Context, url: str) -> None:
    expect(require_page(context)).to_have_url(resolve_url(context, url))


@then('the url should contain "{fragment}"')
@then('the page url should contain "{fragment}"')
def step_url_contains(context: Context, fragment: str) -> None:
    expect(require_page(context)).to_have_url(re.compile(re.escape(fragment)))


@then('the title should be "{title}"')
@then('the page title should be "{title}"')
def step_title_is(context: Context, title: str) -> None:
    expect(require_page(context)).to_have_title(re.compile(f"^{re.escape(title)}$"))


@then('the title should contain "{text}"')
@then('the page title should contain "{text}"')
def step_title_contains(context: Context, text: str) -> None:
    expect(require_page(context)).to_have_title(re.compile(re.escape(text)))


@then('I should see {count:d} "{target}" elements')
def step_element_count(context: Context, count: int, target: str) -> None:
    expect(resolve(require_page(context), target, "any")).to_have_count(count)


@then('the "{target}" element should contain "{text}"')
def step_element_contains_text(context: Context, target: str, text: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_contain_text(text)


@then('the "{target}" element should have text "{text}"')
def step_element_has_text(context: Context, target: str, text: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_have_text(text)


@then('the "{target}" element should have attribute "{name}" with value "{value}"')
def step_element_attribute(context: Context, target: str, name: str, value: str) -> None:
    expect(resolve_first(require_page(context), target, "any")).to_have_attribute(name, value)


@then('the "{field}" field should have value "{value}"')
@then('the "{field}" field should contain "{value}"')
def step_field_value(context: Context, field: str, value: str) -> None:
    expect(resolve_first(require_page(context), field, "field")).to_have_value(value)


@then('the "{name}" cookie should exist')
def step_cookie_exists(context: Context, name: str) -> None:
    if _cookie(context, name) is None:
        raise AssertionError(f"cookie {name!r} not found")


@then('the "{name}" cookie should have value "{value}"')
def step_cookie_value(context: Context, name: str, value: str) -> None:
    cookie = _cookie(context, name)
    if cookie is None:
        raise AssertionError(f"cookie {name!r} not found")
    if cookie.get("value") != value:
        raise AssertionError(
            f"cookie {name!r}: expected value {value!r}, got {cookie.get('value')!r}"
        )


@then("there should be no console errors")
def step_no_console_errors(context: Context) -> None:
    _assert_no_console_errors(context)


@then('there should be no console errors except "{pattern}"')
def step_no_console_errors_except(context: Context, pattern: str) -> None:
    _assert_no_console_errors(context, ignored=pattern)


@then('the file "{name}" was downloaded')
def step_file_downloaded(context: Context, name: str) -> None:
    downloads = getattr(context, "bp_downloads", [])
    if not any(path.name == name for path in downloads):
        raise AssertionError(
            f"no downloaded file named {name!r}; seen: {[p.name for p in downloads] or 'none'}"
        )


def _cookie(context: Context, name: str) -> dict[str, Any] | None:
    cookies: list[dict[str, Any]] = context.browser_context.cookies()
    for cookie in cookies:
        if cookie.get("name") == name:
            return cookie
    return None


def _assert_no_console_errors(context: Context, ignored: str | None = None) -> None:
    errors: list[str] = getattr(context, "bp_console_errors", [])
    if ignored is not None:
        errors = [e for e in errors if re.search(ignored, e) is None]
    if errors:
        raise AssertionError(f"{len(errors)} console error(s): " + "; ".join(errors[:5]))

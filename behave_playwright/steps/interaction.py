"""Element interaction steps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import when

from behave_playwright._context import require_page
from behave_playwright.locators import resolve_first

if TYPE_CHECKING:
    from behave.runner import Context


@when('I click "{target}"')
@when('I click on "{target}"')
def step_click(context: Context, target: str) -> None:
    resolve_first(require_page(context), target).click()


@when('I double click "{target}"')
@when('I double-click "{target}"')
@when('I double click on "{target}"')
def step_double_click(context: Context, target: str) -> None:
    resolve_first(require_page(context), target).dblclick()


@when('I right click "{target}"')
@when('I right click on "{target}"')
def step_right_click(context: Context, target: str) -> None:
    resolve_first(require_page(context), target).click(button="right")


@when('I hover over "{target}"')
@when('I hover "{target}"')
def step_hover(context: Context, target: str) -> None:
    resolve_first(require_page(context), target).hover()


@when('I fill "{field}" with "{value}"')
@when('I fill in "{field}" with "{value}"')
@when('I enter "{value}" in "{field}"')
@when('I enter "{value}" into "{field}"')
def step_fill(context: Context, field: str, value: str) -> None:
    resolve_first(require_page(context), field, "field").fill(value)


@when('I clear "{field}"')
def step_clear(context: Context, field: str) -> None:
    resolve_first(require_page(context), field, "field").clear()


@when('I select "{value}" from "{field}"')
@when('I select "{value}" in "{field}"')
def step_select(context: Context, field: str, value: str) -> None:
    resolve_first(require_page(context), field, "field").select_option(label=value)


@when('I check "{target}"')
def step_check(context: Context, target: str) -> None:
    resolve_first(require_page(context), target, "field").set_checked(True)


@when('I uncheck "{target}"')
def step_uncheck(context: Context, target: str) -> None:
    resolve_first(require_page(context), target, "field").set_checked(False)


@when('I press the "{key}" key')
def step_press_key(context: Context, key: str) -> None:
    require_page(context).keyboard.press(key)


@when('I press "{key}" on "{target}"')
@when('I press "{key}" in "{target}"')
def step_press_key_on(context: Context, key: str, target: str) -> None:
    resolve_first(require_page(context), target).press(key)


@when('I upload "{path}" to "{field}"')
@when('I upload the file "{path}" to "{field}"')
def step_upload(context: Context, field: str, path: str) -> None:
    resolve_first(require_page(context), field, "field").set_input_files(path)

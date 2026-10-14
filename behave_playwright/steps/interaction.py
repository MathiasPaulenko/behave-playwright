"""Element interaction steps."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from behave import when

from behave_playwright._context import main_page, require_page
from behave_playwright.environment import _artifact_path
from behave_playwright.locators import resolve, resolve_first

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


@when('I type "{text}" in "{field}"')
@when('I type "{text}" into "{field}"')
def step_type(context: Context, text: str, field: str) -> None:
    """Type character by character (triggers per-key events, unlike fill)."""
    resolve_first(require_page(context), field, "field").press_sequentially(text)


@when("I fill the form:")
def step_fill_form(context: Context) -> None:
    table = getattr(context, "table", None)
    if table is None:
        raise RuntimeError("I fill the form: requires a data table (| field | value |)")
    headings = getattr(table, "headings", None) or []
    page = require_page(context)
    for row in table:
        if len(row.cells) < 2:
            raise RuntimeError("I fill the form: each row needs at least 2 columns (field, value)")
        field = row["field"] if "field" in headings else row.cells[0]
        value = row["value"] if "value" in headings else row.cells[1]
        resolve_first(page, field, "field").fill(value)


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
    main_page(context).keyboard.press(key)


@when('I press "{key}" on "{target}"')
@when('I press "{key}" in "{target}"')
def step_press_key_on(context: Context, key: str, target: str) -> None:
    page = require_page(context)
    locator = resolve(page, target, "field").or_(resolve(page, target, "action"))
    locator.first.press(key)


@when('I upload "{path}" to "{field}"')
@when('I upload the file "{path}" to "{field}"')
def step_upload(context: Context, field: str, path: str) -> None:
    file_path = Path(path)
    if not path.strip() or not file_path.is_file():
        raise FileNotFoundError(f"cannot upload — file not found: {path!r}")
    resolve_first(require_page(context), field, "field").set_input_files(str(file_path))


@when('I scroll to "{target}"')
def step_scroll_to(context: Context, target: str) -> None:
    resolve_first(require_page(context), target, "any").scroll_into_view_if_needed()


@when('I drag "{source}" to "{target}"')
@when('I drag "{source}" onto "{target}"')
def step_drag(context: Context, source: str, target: str) -> None:
    page = require_page(context)
    resolve_first(page, source, "any").drag_to(resolve_first(page, target, "any"))


@when("I take a screenshot")
def step_take_screenshot(context: Context) -> None:
    path = _manual_screenshot_path(context, "screenshot")
    main_page(context).screenshot(path=str(path), full_page=True)
    _attach_png(context, path)


@when('I take a screenshot of "{target}"')
def step_take_element_screenshot(context: Context, target: str) -> None:
    path = _manual_screenshot_path(context, "element")
    resolve_first(require_page(context), target, "any").screenshot(path=str(path))
    _attach_png(context, path)


def _attach_png(context: Context, path: Path) -> None:
    attach = getattr(context, "attach", None)
    if attach is not None:
        attach("image/png", path.read_bytes())


def _manual_screenshot_path(context: Context, fallback_name: str) -> Path:
    config: Any = getattr(context, "bp_config", None)
    screenshots_dir = getattr(config, "screenshots_dir", "screenshots")
    scenario = getattr(context, "scenario", None) or SimpleNamespace(name=fallback_name)
    return _artifact_path(scenario, screenshots_dir, ".png")

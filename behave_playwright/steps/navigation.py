"""Navigation steps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import step, when

from behave_playwright._context import require_page, resolve_url

if TYPE_CHECKING:
    from behave.runner import Context


@step('I navigate to "{url}"')
@step('I go to "{url}"')
@step('I open "{url}"')
def step_navigate_to(context: Context, url: str) -> None:
    require_page(context).goto(resolve_url(context, url))


@when("I go back")
def step_go_back(context: Context) -> None:
    require_page(context).go_back()


@when("I go forward")
def step_go_forward(context: Context) -> None:
    require_page(context).go_forward()


@when("I reload the page")
@when("I refresh the page")
def step_reload(context: Context) -> None:
    require_page(context).reload()

"""Explicit wait steps.

Playwright auto-waits on every action and assertion, so most scenarios never
need these — they exist for the cases where an explicit wait is the honest
expression of the expected behavior.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from behave import when

from behave_playwright._context import require_page
from behave_playwright.locators import resolve_first

if TYPE_CHECKING:
    from behave.runner import Context


@when('I wait for "{target}" to be visible')
@when('I wait for the "{target}" element')
def step_wait_visible(context: Context, target: str) -> None:
    resolve_first(require_page(context), target, "any").wait_for(state="visible")


@when('I wait for "{target}" to be hidden')
@when('I wait for "{target}" to disappear')
def step_wait_hidden(context: Context, target: str) -> None:
    resolve_first(require_page(context), target, "any").wait_for(state="hidden")


@when('I wait for text "{text}"')
@when('I wait for the text "{text}"')
def step_wait_text(context: Context, text: str) -> None:
    require_page(context).get_by_text(text).first.wait_for(state="visible")


@when("I wait for the page to load")
@when("I wait for navigation")
def step_wait_load(context: Context) -> None:
    require_page(context).wait_for_load_state("load")


@when("I wait for the network to be idle")
@when("I wait for network to be idle")
def step_wait_network_idle(context: Context) -> None:
    require_page(context).wait_for_load_state("networkidle")


@when("I wait {seconds} seconds")
def step_wait_seconds(context: Context, seconds: str) -> None:
    require_page(context)  # wiring check — Frame has no wait_for_timeout
    time.sleep(float(seconds))

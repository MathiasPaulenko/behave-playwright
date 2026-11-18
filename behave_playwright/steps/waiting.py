"""Explicit wait steps.

Playwright auto-waits on every action and assertion, so most scenarios never
need these — they exist for the cases where an explicit wait is the honest
expression of the expected behavior.
"""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from behave import when

from behave_playwright._context import main_page, require_page
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
    if not text:
        raise ValueError("empty text")
    require_page(context).get_by_text(text).first.wait_for(state="visible")


@when("I wait for the page to load")
@when("I wait for navigation")
def step_wait_load(context: Context) -> None:
    # main_page: inside an iframe context.page is a Frame — "the page" is
    # the real Page, same semantics as the navigation steps
    main_page(context).wait_for_load_state("load")


@when("I wait for the network to be idle")
@when("I wait for network to be idle")
def step_wait_network_idle(context: Context) -> None:
    main_page(context).wait_for_load_state("networkidle")


@when("I wait {seconds} seconds")
def step_wait_seconds(context: Context, seconds: str) -> None:
    require_page(context)  # wiring check — Frame has no wait_for_timeout
    try:
        delay = float(seconds)
    except ValueError:
        raise ValueError(f"invalid wait duration {seconds!r}") from None
    if not math.isfinite(delay) or delay < 0:
        raise ValueError(f"invalid wait duration {seconds!r} (must be a finite number >= 0)")
    time.sleep(delay)

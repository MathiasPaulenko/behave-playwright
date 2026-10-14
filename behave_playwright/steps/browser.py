"""Browser-level steps: tabs, iframes, dialogs and downloads."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from behave import step

from behave_playwright._context import (
    main_page,
    require_browser_context,
    require_page,
    resolve_url,
)
from behave_playwright.environment import wire_page
from behave_playwright.locators import resolve_first

if TYPE_CHECKING:
    from behave.runner import Context


@step('I open a new tab with "{url}"')
def step_open_new_tab(context: Context, url: str) -> None:
    page = require_browser_context(context).new_page()
    wire_page(context, page)
    page.goto(resolve_url(context, url))


@step('I click "{target}" in a new tab')
def step_click_in_new_tab(context: Context, target: str) -> None:
    """Click something that opens a popup/tab and switch to it."""
    with require_browser_context(context).expect_page() as new_page_info:
        resolve_first(require_page(context), target).click()
    page = new_page_info.value
    wire_page(context, page)
    page.wait_for_load_state()


@step("I switch to tab {index:d}")
def step_switch_tab(context: Context, index: int) -> None:
    pages = require_browser_context(context).pages
    if not 1 <= index <= len(pages):
        raise IndexError(f"tab {index} does not exist — {len(pages)} tab(s) open")
    wire_page(context, pages[index - 1])


@step("I close the current tab")
def step_close_tab(context: Context) -> None:
    pages = require_browser_context(context).pages
    if len(pages) <= 1:
        raise RuntimeError("cannot close the last open tab")
    main_page(context).close()
    wire_page(context, require_browser_context(context).pages[-1])


@step('I switch to the "{name}" iframe')
def step_switch_to_iframe(context: Context, name: str) -> None:
    top = getattr(context, "_bp_main_page", None)
    if top is None:
        top = require_page(context)
        context._bp_main_page = top
    frame = next((f for f in top.frames if f.name == name or name in f.url), None)
    if frame is None:
        available = [f"{f.name or '(unnamed)'}" for f in top.frames]
        raise LookupError(f"no iframe matches {name!r}; frames: {available}")
    context.page = frame


@step("I switch back to the main frame")
def step_switch_to_main_frame(context: Context) -> None:
    top = getattr(context, "_bp_main_page", None)
    if top is None:
        raise RuntimeError("not inside an iframe")
    context.page = top
    context._bp_main_page = None


@step("I accept the next dialog")
def step_accept_dialog(context: Context) -> None:
    main_page(context).once("dialog", lambda dialog: dialog.accept())


@step('I answer the next dialog with "{text}"')
def step_answer_dialog(context: Context, text: str) -> None:
    main_page(context).once("dialog", lambda dialog: dialog.accept(prompt_text=text))


@step("I dismiss the next dialog")
def step_dismiss_dialog(context: Context) -> None:
    main_page(context).once("dialog", lambda dialog: dialog.dismiss())


@step('I click "{target}" and download the file')
def step_click_and_download(context: Context, target: str) -> None:
    # expect_download lives on the real Page, but the clicked element may
    # live inside the current iframe — resolve it on context.page.
    with main_page(context).expect_download() as download_info:
        resolve_first(require_page(context), target).click()
    download = download_info.value
    downloads_dir = Path(getattr(getattr(context, "bp_config", None), "downloads_dir", "downloads"))
    downloads_dir.mkdir(parents=True, exist_ok=True)
    destination = downloads_dir / (download.suggested_filename or "download")
    download.save_as(str(destination))
    downloads = getattr(context, "bp_downloads", None)
    if downloads is None:
        downloads = context.bp_downloads = []
    downloads.append(destination)

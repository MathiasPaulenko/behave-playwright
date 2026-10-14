"""Session-level steps: device emulation, tracing, and storage state.

Steps that swap the browser context (emulate device, storage state) recreate
``context.browser_context`` and ``context.page`` — any prior page state,
listeners or in-flight tracing on the old context is discarded.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from behave import step

from behave_playwright.environment import _device_descriptor, new_browser_context

if TYPE_CHECKING:
    from behave.runner import Context

logger = logging.getLogger(__name__)

AUTH_DIR = "auth"


@step('I emulate device "{name}"')
def step_emulate_device(context: Context, name: str) -> None:
    new_browser_context(context, _device_descriptor(context, name))


@step('I use the storage state "{path}"')
def step_use_storage_state(context: Context, path: str) -> None:
    storage_path = Path(path)
    if not storage_path.is_file():
        raise FileNotFoundError(
            f"Storage state file not found: {storage_path} — "
            'create it with `I save the storage state to "{path}"`'
        )
    new_browser_context(context, {"storage_state": str(storage_path)})


@step('I am logged in as "{user}"')
def step_logged_in_as(context: Context, user: str) -> None:
    if not re.fullmatch(r"[\w.-]+", user) or user in (".", ".."):
        raise ValueError(f"invalid user name {user!r} — auth lookup stays inside {AUTH_DIR}/")
    storage_path = Path(AUTH_DIR) / f"{user}.json"
    if not storage_path.is_file():
        raise FileNotFoundError(
            f"No stored session for {user!r} at {storage_path} — "
            'create it with `I save the storage state to "auth/{user}.json"`'
        )
    new_browser_context(context, {"storage_state": str(storage_path)})


@step('I save the storage state to "{path}"')
def step_save_storage_state(context: Context, path: str) -> None:
    storage_path = Path(path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    context.browser_context.storage_state(path=str(storage_path))
    logger.info("Storage state saved to %s", storage_path)


@step("I enable tracing")
def step_enable_tracing(context: Context) -> None:
    """Record a Playwright trace; on scenario failure it's saved as
    ``<traces_dir>/<scenario>.trace.zip`` (open with `playwright show-trace`).
    """
    browser_context = context.browser_context
    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context._bp_tracing = browser_context

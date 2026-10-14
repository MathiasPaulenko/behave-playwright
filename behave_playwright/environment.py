"""Behave environment hooks managing the Playwright browser lifecycle.

Use them from your project's ``features/environment.py``::

    from behave_playwright.environment import *  # noqa: F401,F403

or delegate explicitly if you also need custom hooks::

    from behave_playwright import environment as bp

    def before_all(context):
        bp.before_all(context)

Lifecycle: one browser per test run, one fresh browser context and page per
scenario. Exposed on the behave ``Context``:

- ``context.page`` — Playwright ``Page`` for the current scenario
- ``context.browser_context`` — Playwright ``BrowserContext``
- ``context.browser`` — shared Playwright ``Browser``
- ``context.bp_config`` — resolved :class:`BrowserConfig`
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from behave.model import Scenario, Status
from behave.runner import Context
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from behave_playwright.config import BrowserConfig

__all__ = [
    "after_all",
    "after_scenario",
    "before_all",
    "before_scenario",
]

logger = logging.getLogger(__name__)


def before_all(context: Context) -> None:
    """Start Playwright and launch the browser for the whole test run."""
    config = BrowserConfig.from_context(context)
    context.bp_config = config

    playwright = sync_playwright().start()
    context._bp_playwright = playwright

    launch_kwargs: dict[str, Any] = {"headless": config.headless}
    if config.slow_mo:
        launch_kwargs["slow_mo"] = config.slow_mo
    if config.channel:
        launch_kwargs["channel"] = config.channel

    context.browser = getattr(playwright, config.browser).launch(**launch_kwargs)


def before_scenario(context: Context, scenario: Scenario) -> None:
    """Create a fresh browser context and page for the scenario."""
    config: BrowserConfig = context.bp_config

    context_args: dict[str, Any] = {}
    if config.device:
        try:
            context_args.update(context._bp_playwright.devices[config.device])
        except KeyError:
            raise ValueError(
                f"Unknown Playwright device {config.device!r}; "
                "see playwright.dev/python/docs/emulation#devices"
            ) from None
    if config.viewport_width and config.viewport_height:
        context_args["viewport"] = {
            "width": config.viewport_width,
            "height": config.viewport_height,
        }
    if config.locale:
        context_args["locale"] = config.locale
    if config.base_url:
        context_args["base_url"] = config.base_url

    browser_context = context.browser.new_context(**context_args)
    page = browser_context.new_page()
    if config.timeout:
        page.set_default_timeout(config.timeout)
        page.set_default_navigation_timeout(config.timeout)

    context.browser_context = browser_context
    context.page = page


def after_scenario(context: Context, scenario: Scenario) -> None:
    """Capture a screenshot on failure, then tear down the browser context."""
    config = getattr(context, "bp_config", BrowserConfig())
    page = getattr(context, "page", None)

    if (
        config.screenshots_on_failure
        and scenario.status == Status.failed
        and page is not None
        and not page.is_closed()
    ):
        path = _save_screenshot(page, scenario, config.screenshots_dir)
        if path is not None:
            context.bp_screenshot = path
            try:
                context.attach("image/png", path.read_bytes())
            except Exception:
                logger.debug("Could not attach screenshot to behave report")
            logger.info("Screenshot saved to %s", path)

    browser_context = getattr(context, "browser_context", None)
    if browser_context is not None:
        browser_context.close()


def after_all(context: Context) -> None:
    """Close the browser and stop Playwright."""
    browser = getattr(context, "browser", None)
    if browser is not None:
        browser.close()
    playwright = getattr(context, "_bp_playwright", None)
    if playwright is not None:
        playwright.stop()


def _save_screenshot(page: Page, scenario: Scenario, directory: str) -> Path | None:
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", scenario.name.lower()).strip("-") or "scenario"
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    path = out_dir / f"{slug}-{timestamp}.png"
    try:
        page.screenshot(path=str(path), full_page=True, timeout=5_000)
    except PlaywrightError:
        logger.warning("Could not capture screenshot for failed scenario %r", scenario.name)
        return None
    return path

"""Behave environment hooks managing the Playwright browser lifecycle.

Use them from your project's ``features/environment.py``::

    from behave_playwright.environment import *  # noqa: F401,F403

or delegate explicitly if you also need custom hooks::

    from behave_playwright import environment as bp

    def before_all(context):
        bp.before_all(context)

Lifecycle: one browser per test run, one fresh browser context and page per
scenario. Exposed on the behave ``Context``:

- ``context.page`` — Playwright ``Page`` (or ``Frame`` inside an iframe)
- ``context.browser_context`` — Playwright ``BrowserContext``
- ``context.browser`` — shared Playwright ``Browser``
- ``context.bp_config`` — resolved :class:`BrowserConfig`
- ``context.bp_requests`` — requests seen by the scenario's browser context
  (every page, including popups and tabs opened mid-scenario)
- ``context.bp_console_errors`` — ``console.error`` + uncaught page errors
- ``context.bp_downloads`` — files saved by download steps
- ``context.bp_screenshot`` / ``bp_trace`` / ``bp_video`` — artifacts on failure
"""

from __future__ import annotations

import contextlib
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
    "new_browser_context",
    "wire_page",
]

logger = logging.getLogger(__name__)


def before_all(context: Context) -> None:
    """Start Playwright and launch the browser for the whole test run."""
    config = BrowserConfig.from_context(context)
    context.bp_config = config
    # Idempotent: a second call must not leak the previous browser/driver.
    after_all(context)

    playwright = sync_playwright().start()
    context._bp_playwright = playwright

    launch_kwargs: dict[str, Any] = {"headless": config.headless}
    if config.slow_mo:
        launch_kwargs["slow_mo"] = config.slow_mo
    if config.channel:
        launch_kwargs["channel"] = config.channel

    try:
        context.browser = getattr(playwright, config.browser).launch(**launch_kwargs)
    except Exception:
        playwright.stop()
        raise


def before_scenario(context: Context, scenario: Scenario) -> None:
    """Create a fresh browser context and page for the scenario."""
    config = getattr(context, "bp_config", None)
    if config is None:
        raise RuntimeError(
            "behave-playwright is not wired — call before_all(context) first "
            "(or `from behave_playwright.environment import *`)"
        )
    extra_args: dict[str, Any] = {}
    if config.device:
        extra_args.update(_device_descriptor(context, config.device))
    new_browser_context(context, extra_args)


def new_browser_context(context: Context, extra_args: dict[str, Any] | None = None) -> None:
    """(Re)create ``context.browser_context`` and ``context.page``.

    Shared by ``before_scenario`` and by steps that need a fresh context
    mid-scenario (device emulation, storage state). Options explicitly set in
    the config override the values carried by ``extra_args`` (e.g. a device
    descriptor).
    """
    config = getattr(context, "bp_config", None)
    if config is None:
        raise RuntimeError(
            "behave-playwright is not wired — call before_all(context) first "
            "(or `from behave_playwright.environment import *`)"
        )
    browser = getattr(context, "browser", None)
    if browser is None:
        raise RuntimeError(
            "context.browser is not set — wire the hooks first: "
            "`from behave_playwright.environment import *` in features/environment.py"
        )

    old_context = getattr(context, "browser_context", None)
    old_page = getattr(context, "_bp_main_page", None) or getattr(context, "page", None)
    if old_context is not None:
        with contextlib.suppress(PlaywrightError):
            old_context.close()
        # drop the stale page/context so a failure below leaves actionable
        # wiring errors instead of "already closed" Playwright errors
        context.browser_context = None
        context.page = None
        context._bp_main_page = None
        # video of the replaced context would linger as a stray uuid.webm;
        # a locked/missing file is cleanup noise, not a step failure
        if config.record_video and old_page is not None and hasattr(old_page, "video"):
            with contextlib.suppress(PlaywrightError, AttributeError, OSError):
                Path(old_page.video.path()).unlink(missing_ok=True)

    for artifact in ("bp_screenshot", "bp_trace", "bp_video"):
        # behave's Context.__delattr__ only deletes in the current frame —
        # an attribute inherited from an outer layer raises AttributeError
        with contextlib.suppress(AttributeError):
            delattr(context, artifact)

    args: dict[str, Any] = dict(extra_args or {})
    if config.viewport_width and config.viewport_height:
        args["viewport"] = {
            "width": config.viewport_width,
            "height": config.viewport_height,
        }
    if config.locale:
        args["locale"] = config.locale
    if config.base_url:
        args["base_url"] = config.base_url

    if config.record_video:
        Path(config.video_dir).mkdir(parents=True, exist_ok=True)
        args["record_video_dir"] = config.video_dir

    context.bp_requests = []
    context.bp_console_errors = []
    context.bp_downloads = []
    context._bp_wired_pages = set()
    context._bp_tracing = None

    browser_context = browser.new_context(**args)
    # timeout is always a float >= 0; 0 disables timeouts (Playwright semantic).
    browser_context.set_default_timeout(config.timeout)
    browser_context.set_default_navigation_timeout(config.timeout)
    # Context-level capture covers every page — including popups whose first
    # requests would fire before a page-level listener could be attached.
    browser_context.on("request", lambda request: _record_request(context, request))
    browser_context.on("page", lambda new_page: _attach_page_listeners(context, new_page))
    try:
        page = browser_context.new_page()
    except Exception:
        # an unassigned context would otherwise leak until the browser dies
        browser_context.close()
        raise

    context.browser_context = browser_context
    wire_page(context, page)


def _record_request(context: Context, request: Any) -> None:
    requests = getattr(context, "bp_requests", None)
    if requests is None:
        requests = context.bp_requests = []
    requests.append(request)


def _record_console_error(context: Context, text: str) -> None:
    errors = getattr(context, "bp_console_errors", None)
    if errors is None:
        errors = context.bp_console_errors = []
    errors.append(text)


def wire_page(context: Context, page: Page) -> None:
    """Make ``page`` the scenario page: timeouts, captures and frame reset.

    Requests are recorded at browser-context level; console/pageerror
    listeners are attached per page the first time it is wired, so switching
    back and forth between tabs never duplicates ``bp_console_errors``.
    """
    config: BrowserConfig = getattr(context, "bp_config", None) or BrowserConfig()
    page.set_default_timeout(config.timeout)
    page.set_default_navigation_timeout(config.timeout)

    if getattr(context, "bp_requests", None) is None:
        context.bp_requests = []
    if getattr(context, "bp_console_errors", None) is None:
        context.bp_console_errors = []

    _attach_page_listeners(context, page)

    context.page = page
    context._bp_main_page = None


def _attach_page_listeners(context: Context, page: Page) -> None:
    """Attach console/pageerror capture to ``page`` once (dedup by identity).

    Requests are captured at context level in ``new_browser_context`` — pages
    only need per-page events here.
    """
    wired: set[Any] = getattr(context, "_bp_wired_pages", None) or set()
    context._bp_wired_pages = wired

    if page in wired:
        return
    wired.add(page)
    page.on(
        "console",
        lambda message: (
            _record_console_error(context, message.text) if message.type == "error" else None
        ),
    )
    page.on("pageerror", lambda error: _record_console_error(context, str(error)))


def after_scenario(context: Context, scenario: Scenario) -> None:
    """Capture a screenshot and trace on failure, then tear down the context."""
    config = getattr(context, "bp_config", None) or BrowserConfig()
    # context.page may be a Frame while inside an iframe — artifacts belong
    # to the real Page, which also holds .video and .is_closed.
    page = getattr(context, "_bp_main_page", None) or getattr(context, "page", None)

    # .video keeps working on a closed page — the file only exists once the
    # context closes — so keep a raw reference before nulling closed pages.
    video_page = page if page is not None and hasattr(page, "video") else None

    # A stray Frame here (custom steps can leave one) can't screenshot or
    # expose video — treat non-pages and closed pages as absent.
    if page is not None and (not hasattr(page, "is_closed") or page.is_closed()):
        page = None

    if config.screenshots_on_failure and scenario.status == Status.failed and page is not None:
        try:
            path = _artifact_path(scenario, config.screenshots_dir, ".png")
            page.screenshot(path=str(path), full_page=True, timeout=5_000)
        except (PlaywrightError, OSError):
            logger.warning("Could not capture screenshot for failed scenario %r", scenario.name)
        else:
            context.bp_screenshot = path
            try:
                context.attach("image/png", path.read_bytes())
            except Exception:
                logger.debug("Could not attach screenshot to behave report")
            logger.info("Screenshot saved to %s", path)

    _stop_tracing(context, scenario, config)

    video = None
    if config.record_video and video_page is not None:
        try:
            video = video_page.video
        except PlaywrightError:
            video = None

    browser_context = getattr(context, "browser_context", None)
    if browser_context is not None:
        # may already be closed by user code — teardown must not mask the
        # scenario result
        with contextlib.suppress(PlaywrightError):
            browser_context.close()

    # drop dead references — custom after_scenario hooks should see None
    # instead of closed objects (same contract as new_browser_context)
    context.browser_context = None
    context.page = None
    context._bp_main_page = None

    if video is not None:
        _handle_video(video, context, scenario, config)


def after_all(context: Context) -> None:
    """Close the browser and stop Playwright.

    Idempotent and fault-tolerant: a browser or driver already closed
    externally must not prevent the remaining resource from being released.
    """
    browser = getattr(context, "browser", None)
    context.browser = None
    if browser is not None:
        with contextlib.suppress(PlaywrightError):
            browser.close()
    playwright = getattr(context, "_bp_playwright", None)
    context._bp_playwright = None
    if playwright is not None:
        with contextlib.suppress(PlaywrightError):
            playwright.stop()


def _handle_video(video: Any, context: Context, scenario: Scenario, config: BrowserConfig) -> None:
    try:
        raw_path = Path(video.path())
    except PlaywrightError:
        logger.warning("Could not resolve recorded video for %r", scenario.name)
        return
    if scenario.status == Status.failed:
        try:
            dest = _artifact_path(scenario, config.video_dir, ".webm")
            raw_path.replace(dest)
        except OSError:
            logger.warning("Could not save video for %r", scenario.name)
            return
        context.bp_video = dest
        logger.info("Video saved to %s", dest)
    else:
        with contextlib.suppress(OSError):
            raw_path.unlink(missing_ok=True)


def _device_descriptor(context: Context, name: str) -> dict[str, Any]:
    playwright = getattr(context, "_bp_playwright", None)
    if playwright is None:
        raise RuntimeError(
            "Playwright is not running — wire the hooks first: "
            "`from behave_playwright.environment import *` in features/environment.py"
        )
    try:
        return dict(playwright.devices[name])
    except KeyError:
        raise ValueError(
            f"Unknown Playwright device {name!r}; see playwright.dev/python/docs/emulation#devices"
        ) from None


def _stop_tracing(context: Context, scenario: Scenario, config: BrowserConfig) -> None:
    tracing_context = getattr(context, "_bp_tracing", None)
    if tracing_context is None:
        return
    context._bp_tracing = None
    try:
        if scenario.status == Status.failed:
            path = _artifact_path(scenario, config.traces_dir, ".trace.zip")
            tracing_context.tracing.stop(path=str(path))
            context.bp_trace = path
            logger.info("Trace saved to %s", path)
        else:
            tracing_context.tracing.stop()
    except (PlaywrightError, OSError):
        logger.warning("Could not stop tracing for scenario %r", scenario.name)


def _artifact_path(scenario: Scenario, directory: str, suffix: str) -> Path:
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    # cap the slug so very long scenario names can't blow past path limits
    slug = re.sub(r"[^a-z0-9]+", "-", scenario.name.lower()).strip("-")[:80].rstrip("-")
    slug = slug or "scenario"
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    return out_dir / f"{slug}-{timestamp}{suffix}"

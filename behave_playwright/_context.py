"""Internal helpers shared by step modules."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

from playwright.sync_api import Page

if TYPE_CHECKING:
    from behave.runner import Context

_ABSOLUTE_URL_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*://|data:|about:|blob:)", re.IGNORECASE)


def require_page(context: Context) -> Page:
    """Return ``context.page`` or fail with an actionable error."""
    page = getattr(context, "page", None)
    if page is None:
        raise RuntimeError(
            "context.page is not set — wire the hooks first: "
            "`from behave_playwright.environment import *` in features/environment.py"
        )
    return cast(Page, page)


def main_page(context: Context) -> Page:
    """Return the real ``Page`` — ``context.page`` may be a ``Frame``
    while inside an iframe; the true page is remembered there."""
    return cast(Page, getattr(context, "_bp_main_page", None) or require_page(context))


def require_browser_context(context: Context) -> Any:
    """Return ``context.browser_context`` or fail with an actionable error."""
    browser_context = getattr(context, "browser_context", None)
    if browser_context is None:
        raise RuntimeError(
            "context.browser_context is not set — wire the hooks first: "
            "`from behave_playwright.environment import *` in features/environment.py"
        )
    return browser_context


def resolve_url(context: Context, url: str) -> str:
    """Resolve ``url`` against ``base_url`` when relative."""
    if _ABSOLUTE_URL_RE.match(url):
        return url
    config = getattr(context, "bp_config", None)
    base_url = getattr(config, "base_url", None)
    if not base_url:
        raise RuntimeError(
            f"Cannot resolve relative URL {url!r}: set base_url "
            "(-D base_url=... or BEHAVE_PW_BASE_URL) or use an absolute URL"
        )
    return f"{base_url.rstrip('/')}/{url.lstrip('/')}"

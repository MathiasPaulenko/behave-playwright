"""Internal helpers shared by step modules."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from playwright.sync_api import Page

if TYPE_CHECKING:
    from behave.runner import Context

_ABSOLUTE_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def require_page(context: Context) -> Page:
    """Return ``context.page`` or fail with an actionable error."""
    page = getattr(context, "page", None)
    if page is None:
        raise RuntimeError(
            "context.page is not set — wire the hooks first: "
            "`from behave_playwright.environment import *` in features/environment.py"
        )
    return cast(Page, page)


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

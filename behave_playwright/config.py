"""Configuration resolution for the behave-playwright browser lifecycle.

Values are resolved in order of precedence:

1. behave ``userdata`` (``behave -D key=value`` or ``userdata`` in ``behave.ini``).
   Both plain keys (``browser``) and namespaced keys (``behave_playwright.browser``)
   are accepted.
2. Environment variables prefixed with ``BEHAVE_PW_`` (e.g. ``BEHAVE_PW_HEADLESS``).
3. Built-in defaults.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from behave.runner import Context

ENV_PREFIX = "BEHAVE_PW_"
USERDATA_PREFIX = "behave_playwright."

VALID_BROWSERS = ("chromium", "firefox", "webkit")

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class BrowserConfig:
    """Resolved configuration for the browser lifecycle hooks.

    ``viewport_width``/``viewport_height`` left as ``None`` means Playwright's
    default (1280x720) or the emulated ``device``'s viewport applies.
    """

    browser: str = "chromium"
    headless: bool = True
    channel: str | None = None
    base_url: str | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    device: str | None = None
    locale: str | None = None
    slow_mo: float = 0.0
    timeout: float = 30_000.0
    screenshots_on_failure: bool = True
    screenshots_dir: str = "screenshots"
    traces_dir: str = "traces"
    video_dir: str = "videos"
    record_video: bool = False
    downloads_dir: str = "downloads"

    @classmethod
    def from_context(cls, context: Context) -> BrowserConfig:
        """Build a config from a behave ``Context`` (userdata + environment)."""
        userdata = getattr(getattr(context, "config", None), "userdata", None) or {}
        return cls.from_sources(userdata, os.environ)

    @classmethod
    def from_sources(cls, userdata: Mapping[str, object], env: Mapping[str, str]) -> BrowserConfig:
        """Build a config from explicit ``userdata`` and ``env`` mappings."""

        def get(key: str, default: str | None = None) -> str | None:
            if key in userdata:
                return str(userdata[key])
            prefixed = USERDATA_PREFIX + key
            if prefixed in userdata:
                return str(userdata[prefixed])
            return env.get(ENV_PREFIX + key.upper(), default)

        browser = (get("browser", "chromium") or "chromium").lower()
        if browser not in VALID_BROWSERS:
            raise ValueError(
                f"Invalid browser {browser!r}; expected one of: {', '.join(VALID_BROWSERS)}"
            )

        viewport = _parse_viewport(get("viewport"))
        slow_mo = _parse_float("slow_mo", get("slow_mo", "0") or "0")
        timeout = _parse_float("timeout", get("timeout", "30000") or "30000")
        if not math.isfinite(slow_mo) or slow_mo < 0:
            raise ValueError(f"Invalid slow_mo: {slow_mo} (must be a finite number >= 0)")
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError(f"Invalid timeout: {timeout} (must be a finite number >= 0)")

        return cls(
            browser=browser,
            headless=_parse_bool("headless", get("headless", "true") or "true"),
            channel=_parse_optional_str(get("channel")),
            base_url=_parse_optional_str(get("base_url")),
            viewport_width=viewport[0] if viewport else None,
            viewport_height=viewport[1] if viewport else None,
            device=_parse_optional_str(get("device")),
            locale=_parse_optional_str(get("locale")),
            slow_mo=slow_mo,
            timeout=timeout,
            screenshots_on_failure=_parse_bool("screenshots", get("screenshots", "true") or "true"),
            screenshots_dir=get("screenshots_dir", "screenshots") or "screenshots",
            traces_dir=get("traces_dir", "traces") or "traces",
            video_dir=get("video_dir", "videos") or "videos",
            record_video=_parse_bool(
                "record_video",
                get("record_video") or get("video") or "false",
            ),
            downloads_dir=get("downloads_dir", "downloads") or "downloads",
        )


def _parse_bool(key: str, raw: str) -> bool:
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ValueError(f"Invalid boolean for {key!r}: {raw!r} (use true/false)")


def _parse_float(key: str, raw: str) -> float:
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"Invalid number for {key!r}: {raw!r}") from None


def _parse_viewport(raw: str | None) -> tuple[int, int] | None:
    if raw is None:
        return None
    parts = raw.lower().split("x")
    if len(parts) != 2 or not all(p.strip().isdigit() for p in parts):
        raise ValueError(f"Invalid viewport {raw!r}; expected 'WIDTHxHEIGHT' (e.g. 1920x1080)")
    width, height = int(parts[0]), int(parts[1])
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid viewport {raw!r}; width and height must be positive")
    return width, height


def _parse_optional_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    return value or None

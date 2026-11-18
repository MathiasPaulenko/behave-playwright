"""Network interception and request assertion steps.

Intercept patterns follow Playwright URL matching:

- glob (``**/api/users``, ``*status=200*``) — ``*`` stays within a path
  segment, ``**`` crosses segments
- a bare absolute path (``/api/users``) is expanded to ``**/api/users``
- ``/regex/`` — a slash-wrapped string containing regex metachars is
  treated as a regular expression (``/api/`` without metachars is a
  literal path, not a regex)
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from re import Pattern
from typing import TYPE_CHECKING, Any

from behave import step, then

from behave_playwright._context import require_browser_context, require_page

if TYPE_CHECKING:
    from behave.runner import Context


@step('I intercept "{pattern}" and return:')
def step_intercept_return(context: Context, pattern: str) -> None:
    _fulfill_route(context, pattern, body=getattr(context, "text", "") or "")


@step('I intercept "{pattern}" and respond with status {code:d}')
def step_intercept_status(context: Context, pattern: str, code: int) -> None:
    _fulfill_route(context, pattern, status=code, body=getattr(context, "text", "") or "")


@step('I intercept "{pattern}" and abort')
def step_intercept_abort(context: Context, pattern: str) -> None:
    require_browser_context(context).route(_url_pattern(pattern), lambda route: route.abort())


@then('a request was made to "{pattern}"')
def step_request_made(context: Context, pattern: str) -> None:
    _wait_for_request(context, pattern)


@then('a "{method}" request was made to "{pattern}"')
def step_request_made_method(context: Context, method: str, pattern: str) -> None:
    _wait_for_request(context, pattern, method=method.upper())


def _fulfill_route(context: Context, pattern: str, status: int = 200, body: str = "") -> None:
    content_type = "application/json" if _is_json(body) else "text/plain"
    require_browser_context(context).route(
        _url_pattern(pattern),
        lambda route: route.fulfill(status=status, body=body, content_type=content_type),
    )


def _url_pattern(raw: str) -> str | Pattern[str]:
    raw = raw.strip()
    if not raw:
        raise ValueError("empty intercept pattern")
    body = _slash_regex_body(raw)
    if body is not None:
        try:
            return re.compile(body)
        except re.error as exc:
            raise ValueError(f"invalid intercept pattern {raw!r}: {exc}") from exc
    if raw.startswith("/"):
        return f"**{raw}"
    return raw


_REGEX_META_RE = re.compile(r"[\\^$*+?{}\[\]|().]")


def _slash_regex_body(raw: str) -> str | None:
    """Return the inner regex of a ``/re/`` pattern — only when the body
    actually uses regex metachars, so ``/api/`` stays a literal path."""
    if raw.startswith("/") and raw.endswith("/") and len(raw) > 2:
        inner = raw[1:-1]
        if _REGEX_META_RE.search(inner):
            return inner
    return None


def _is_json(body: str) -> bool:
    try:
        json.loads(body)
    except ValueError:
        return False
    return True


def _wait_for_request(context: Context, pattern: str, method: str | None = None) -> Any:
    require_page(context)
    matcher = _request_matcher(pattern)  # validates/compiles once, before polling
    timeout = getattr(getattr(context, "bp_config", None), "timeout", 30_000) / 1000
    # Playwright semantic: timeout <= 0 means "no deadline" — poll until found.
    deadline = None if timeout <= 0 else time.monotonic() + timeout
    while True:
        requests = getattr(context, "bp_requests", None) or []
        for request in requests:
            if matcher(request.url) and (method is None or request.method.upper() == method):
                return request
        if deadline is not None and time.monotonic() >= deadline:
            raise AssertionError(
                f"no {method or 'ANY'} request matched {pattern!r}; "
                f"seen: {[r.url for r in requests] or 'none'}"
            )
        time.sleep(0.05)


def _request_matcher(pattern: str) -> Callable[[str], bool]:
    """Compile ``pattern`` (regex/glob/substring) into a url matcher — once."""
    if not pattern.strip():
        raise ValueError("empty request pattern")
    body = _slash_regex_body(pattern)
    if body is not None:
        try:
            regex = re.compile(body)
        except re.error as exc:
            raise ValueError(f"invalid request pattern {pattern!r}: {exc}") from exc
    elif "*" in pattern:
        regex = re.compile(re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*"))
    else:
        return lambda url: pattern in url
    return lambda url: regex.search(url) is not None


def _matches(url: str, pattern: str) -> bool:
    return _request_matcher(pattern)(url)

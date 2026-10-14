"""Network interception and request assertion steps.

Intercept patterns follow Playwright URL matching:

- glob (``**/api/users``, ``*status=200*``) — ``*`` stays within a path
  segment, ``**`` crosses segments
- a bare absolute path (``/api/users``) is expanded to ``**/api/users``
- ``/regex/`` — a slash-wrapped string is treated as a regular expression
"""

from __future__ import annotations

import json
import re
import time
from re import Pattern
from typing import TYPE_CHECKING, Any

from behave import step, then

from behave_playwright._context import require_page

if TYPE_CHECKING:
    from behave.runner import Context


@step('I intercept "{pattern}" and return:')
def step_intercept_return(context: Context, pattern: str) -> None:
    _fulfill_route(context, pattern, body=context.text or "")


@step('I intercept "{pattern}" and respond with status {code:d}')
def step_intercept_status(context: Context, pattern: str, code: int) -> None:
    _fulfill_route(context, pattern, status=code, body=getattr(context, "text", "") or "")


@step('I intercept "{pattern}" and abort')
def step_intercept_abort(context: Context, pattern: str) -> None:
    require_page(context).route(_url_pattern(pattern), lambda route: route.abort())


@then('a request was made to "{pattern}"')
def step_request_made(context: Context, pattern: str) -> None:
    _wait_for_request(context, pattern)


@then('a "{method}" request was made to "{pattern}"')
def step_request_made_method(context: Context, method: str, pattern: str) -> None:
    _wait_for_request(context, pattern, method=method.upper())


def _fulfill_route(context: Context, pattern: str, status: int = 200, body: str = "") -> None:
    content_type = "application/json" if _is_json(body) else "text/plain"
    require_page(context).route(
        _url_pattern(pattern),
        lambda route: route.fulfill(status=status, body=body, content_type=content_type),
    )


def _url_pattern(raw: str) -> str | Pattern[str]:
    if raw.startswith("/") and raw.endswith("/") and len(raw) > 2:
        return re.compile(raw[1:-1])
    if raw.startswith("/"):
        return f"**{raw}"
    return raw


def _is_json(body: str) -> bool:
    try:
        json.loads(body)
    except ValueError:
        return False
    return True


def _wait_for_request(context: Context, pattern: str, method: str | None = None) -> Any:
    page = require_page(context)
    timeout = getattr(getattr(context, "bp_config", None), "timeout", 30_000) / 1000
    deadline = time.monotonic() + timeout
    requests = getattr(context, "bp_requests", [])
    while True:
        for request in requests:
            if _matches(request.url, pattern) and (
                method is None or request.method.upper() == method
            ):
                return request
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"no {method or 'ANY'} request matched {pattern!r}; "
                f"seen: {[r.url for r in requests] or 'none'}"
            )
        page.wait_for_timeout(50)


def _matches(url: str, pattern: str) -> bool:
    if pattern.startswith("/") and pattern.endswith("/") and len(pattern) > 2:
        return re.search(pattern[1:-1], url) is not None
    if "*" in pattern:
        regex = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
        return re.search(regex, url) is not None
    return pattern in url

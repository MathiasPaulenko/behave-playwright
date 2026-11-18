"""Tests for network interception and request assertion steps."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from behave_playwright import BrowserConfig
from behave_playwright.steps import network


def test_intercept_returns_json(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.text = '[{"name": "Ada"}]'
    network.step_intercept_return(env_context, "/api/users")
    response = env_context.page.goto(f"{base_url}/api/users")
    assert response is not None
    assert response.headers.get("content-type", "").startswith("application/json")
    assert "Ada" in env_context.page.content()


def test_intercept_with_status(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.text = "backend is down"
    network.step_intercept_status(env_context, "**/api/health", 503)
    response = env_context.page.goto(f"{base_url}/api/health")
    assert response is not None
    assert response.status == 503
    assert "backend is down" in env_context.page.text_content("body")


def test_intercept_abort(env_context: SimpleNamespace, base_url: str) -> None:
    network.step_intercept_abort(env_context, "**/api/x")
    with pytest.raises(Exception, match=r"ERR_FAILED|failed"):
        env_context.page.goto(f"{base_url}/api/x")


def test_request_was_made(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.page.goto(base_url)
    network.step_request_made(env_context, base_url)
    network.step_request_made_method(env_context, "GET", base_url)


def test_request_was_made_with_glob(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.page.goto(f"{base_url}/next")
    network.step_request_made(env_context, "**/next")


def test_request_was_made_with_regex(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.page.goto(f"{base_url}/next")
    network.step_request_made(env_context, r"/nex./")


def test_request_not_made_fails(env_context: SimpleNamespace) -> None:
    env_context.bp_config = BrowserConfig(timeout=300)
    with pytest.raises(AssertionError, match="no ANY request"):
        network.step_request_made(env_context, "**/never-called")


def test_slash_wrapped_literal_path_is_not_regex() -> None:
    # "/api/" is a literal path, not the regex "api"
    assert network._matches("http://x/api/", "/api/") is True
    assert network._matches("http://x/apis/", "/api/") is False
    assert network._matches("http://x/api/v1", "/api/v\\d+/") is True


def test_url_pattern_literal_path() -> None:
    from behave_playwright.steps.network import _url_pattern

    assert _url_pattern("/api/") == "**/api/"
    assert _url_pattern("/api/x") == "**/api/x"
    assert _url_pattern("**/a*") == "**/a*"
    assert _url_pattern("/re\\d+/").pattern == r"re\d+"


def test_wrong_method_fails(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.page.goto(base_url)
    env_context.bp_config = BrowserConfig(timeout=300)
    with pytest.raises(AssertionError, match="no POST request"):
        network.step_request_made_method(env_context, "POST", base_url)


def test_intercept_applies_to_new_tabs(env_context: SimpleNamespace, base_url: str) -> None:
    from behave_playwright.steps import browser

    env_context.bp_config = BrowserConfig(base_url=base_url)
    network.step_intercept_abort(env_context, "**/next")
    browser.step_open_new_tab(env_context, "/")
    # route registered on the context must intercept the new tab too
    with pytest.raises(Exception, match=r"ERR_FAILED|failed"):
        env_context.page.goto(f"{base_url}/next")


def test_request_from_new_tab_is_captured(env_context: SimpleNamespace, base_url: str) -> None:
    from behave_playwright.steps import browser

    env_context.bp_config = BrowserConfig(base_url=base_url, timeout=5000)
    browser.step_open_new_tab(env_context, "/next")
    # the new tab's initial navigation must appear in bp_requests even though
    # it fired before/while the page was wired
    network.step_request_made(env_context, "**/next")


def test_request_wait_with_none_requests_list(env_context: SimpleNamespace) -> None:
    env_context.bp_config = BrowserConfig(timeout=100)
    env_context.bp_requests = None
    with pytest.raises(AssertionError, match="no ANY request"):
        network.step_request_made(env_context, "**/x")


def test_request_wait_timeout_zero_finds_existing(
    env_context: SimpleNamespace, base_url: str
) -> None:
    env_context.bp_config = BrowserConfig(timeout=0)
    env_context.page.goto(base_url)
    # timeout=0 means "no deadline" — an already-seen request returns at once
    network.step_request_made(env_context, base_url)


def test_intercept_invalid_regex_pattern_rejected(env_context: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="invalid intercept pattern"):
        network.step_intercept_abort(env_context, "/[broken/")


def test_intercept_empty_pattern_rejected(env_context: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="empty intercept pattern"):
        network.step_intercept_abort(env_context, "   ")


def test_request_made_empty_pattern_rejected(env_context: SimpleNamespace) -> None:
    with pytest.raises(ValueError, match="empty request pattern"):
        network.step_request_made(env_context, "")


def test_request_made_invalid_regex_pattern_rejected(
    env_context: SimpleNamespace,
) -> None:
    with pytest.raises(ValueError, match="invalid request pattern"):
        network.step_request_made(env_context, "/[broken/")


def test_request_capture_recreates_none_list(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.bp_config = BrowserConfig(base_url=base_url, timeout=5000)
    env_context.bp_requests = None  # damaged externally between steps
    env_context.page.goto(base_url)
    network.step_request_made(env_context, base_url)

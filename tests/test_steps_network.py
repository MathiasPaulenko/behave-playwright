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


def test_wrong_method_fails(env_context: SimpleNamespace, base_url: str) -> None:
    env_context.page.goto(base_url)
    env_context.bp_config = BrowserConfig(timeout=300)
    with pytest.raises(AssertionError, match="no POST request"):
        network.step_request_made_method(env_context, "POST", base_url)

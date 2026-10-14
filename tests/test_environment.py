"""Tests for the environment lifecycle hooks using fake Playwright objects."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from behave.model import Status

from behave_playwright import environment


class FakePage:
    def __init__(self) -> None:
        self.closed = False
        self.timeout: float | None = None
        self.screenshots: list[str] = []

    def is_closed(self) -> bool:
        return self.closed

    def screenshot(self, path: str, full_page: bool = True, timeout: float = 0) -> None:
        self.screenshots.append(path)
        Path(path).write_bytes(b"fake-png")

    def set_default_timeout(self, timeout: float) -> None:
        self.timeout = timeout

    def set_default_navigation_timeout(self, timeout: float) -> None:
        pass


class FakeBrowserContext:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.pages: list[FakePage] = []
        self.closed = False

    def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        return page

    def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self) -> None:
        self.contexts: list[FakeBrowserContext] = []
        self.launch_kwargs: dict[str, Any] = {}
        self.closed = False

    def new_context(self, **kwargs: Any) -> FakeBrowserContext:
        ctx = FakeBrowserContext(**kwargs)
        self.contexts.append(ctx)
        return ctx

    def close(self) -> None:
        self.closed = True


class FakeBrowserType:
    def __init__(self, browser: FakeBrowser) -> None:
        self.browser = browser

    def launch(self, **kwargs: Any) -> FakeBrowser:
        self.browser.launch_kwargs = kwargs
        return self.browser


class FakePlaywright:
    def __init__(self, browser: FakeBrowser) -> None:
        self.browser = browser
        self.chromium = FakeBrowserType(browser)
        self.firefox = FakeBrowserType(browser)
        self.webkit = FakeBrowserType(browser)
        self.devices = {"Phone": {"viewport": {"width": 390, "height": 844}, "is_mobile": True}}
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class FakeSyncPlaywright:
    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright

    def start(self) -> FakePlaywright:
        return self.playwright


def make_context(
    userdata: dict[str, str] | None = None,
    playwright: FakePlaywright | None = None,
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> SimpleNamespace:
    """Build a fake behave Context with a patched sync_playwright."""
    attached: list[tuple[str, bytes]] = []
    context = SimpleNamespace(
        config=SimpleNamespace(userdata=userdata or {}),
        attach=lambda mime, data: attached.append((mime, data)),
        attached=attached,
    )
    if playwright is not None and monkeypatch is not None:
        monkeypatch.setattr(environment, "sync_playwright", lambda: FakeSyncPlaywright(playwright))
    return context


def make_scenario(name: str = "My scenario", status: Status = Status.passed) -> SimpleNamespace:
    return SimpleNamespace(name=name, status=status)


def test_before_all_launches_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"browser": "firefox", "slow_mo": "100"}, playwright, monkeypatch)

    environment.before_all(context)

    assert context.browser is playwright.browser
    assert context.browser.launch_kwargs == {"headless": True, "slow_mo": 100.0}
    assert context.bp_config.browser == "firefox"


def test_before_scenario_creates_context_and_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context(
        {"base_url": "http://localhost:8000", "viewport": "800x600", "timeout": "7000"},
        playwright,
        monkeypatch,
    )
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    ctx_kwargs = playwright.browser.contexts[0].kwargs
    assert ctx_kwargs["base_url"] == "http://localhost:8000"
    assert ctx_kwargs["viewport"] == {"width": 800, "height": 600}
    assert context.page.timeout == 7000.0
    assert context.browser_context is playwright.browser.contexts[0]


def test_before_scenario_uses_device_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"device": "Phone"}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    ctx_kwargs = playwright.browser.contexts[0].kwargs
    assert ctx_kwargs["is_mobile"] is True
    assert ctx_kwargs["viewport"] == {"width": 390, "height": 844}


def test_before_scenario_unknown_device(monkeypatch: pytest.MonkeyPatch) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"device": "Nokia 3310"}, playwright, monkeypatch)
    environment.before_all(context)
    with pytest.raises(ValueError, match="Nokia 3310"):
        environment.before_scenario(context, make_scenario())


def test_after_scenario_closes_context(monkeypatch: pytest.MonkeyPatch) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    environment.after_scenario(context, make_scenario())

    assert playwright.browser.contexts[0].closed is True


def test_after_scenario_screenshot_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"screenshots_dir": str(tmp_path)}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())
    scenario = make_scenario(name="It fails!", status=Status.failed)

    environment.after_scenario(context, scenario)

    page = context.page
    assert len(page.screenshots) == 1
    saved = Path(page.screenshots[0])
    assert saved.exists()
    assert saved.name.startswith("it-fails-")
    assert context.attached == [("image/png", b"fake-png")]
    assert context.bp_screenshot == saved


def test_after_scenario_no_screenshot_on_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"screenshots_dir": str(tmp_path)}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    environment.after_scenario(context, make_scenario(status=Status.passed))

    assert context.page.screenshots == []
    assert context.attached == []


def test_after_scenario_without_page_does_not_crash() -> None:
    context = SimpleNamespace(config=SimpleNamespace(userdata={}))
    environment.after_scenario(context, make_scenario(status=Status.failed))


def test_after_all_closes_browser_and_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)

    environment.after_all(context)

    assert playwright.browser.closed is True
    assert playwright.stopped is True

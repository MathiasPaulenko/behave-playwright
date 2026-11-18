"""Tests for the environment lifecycle hooks using fake Playwright objects."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from behave.model import Status
from playwright.sync_api import Error as PlaywrightError

from behave_playwright import environment


class FakePage:
    def __init__(self) -> None:
        self.closed = False
        self.timeout: float | None = None
        self.screenshots: list[str] = []

    def is_closed(self) -> bool:
        return self.closed

    def on(self, event: str, handler: Any) -> None:
        pass

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
        self.handlers: dict[str, list[Any]] = {}

    def on(self, event: str, handler: Any) -> None:
        self.handlers.setdefault(event, []).append(handler)

    def _emit(self, event: str, *args: Any) -> None:
        for handler in self.handlers.get(event, []):
            handler(*args)

    def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        self._emit("page", page)
        return page

    def set_default_timeout(self, timeout: float) -> None:
        self.timeout = timeout

    def set_default_navigation_timeout(self, timeout: float) -> None:
        self.navigation_timeout = timeout

    def close(self) -> None:
        if self.closed:
            raise PlaywrightError("Context has been closed")
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
        if self.closed:
            raise PlaywrightError("Browser has been closed")
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
    page = context.page

    environment.after_scenario(context, scenario)

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
    page = context.page

    environment.after_scenario(context, make_scenario(status=Status.passed))

    assert page.screenshots == []
    assert context.attached == []


def test_after_scenario_without_page_does_not_crash() -> None:
    context = SimpleNamespace(config=SimpleNamespace(userdata={}))
    environment.after_scenario(context, make_scenario(status=Status.failed))


def test_after_scenario_drops_dead_page_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    environment.after_scenario(context, make_scenario())

    # custom after_scenario hooks see None, not closed objects
    assert context.page is None
    assert context.browser_context is None
    assert context._bp_main_page is None


def test_after_all_closes_browser_and_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)

    environment.after_all(context)

    assert playwright.browser.closed is True
    assert playwright.stopped is True


def test_before_all_restart_releases_previous_browser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = FakePlaywright(FakeBrowser()), FakePlaywright(FakeBrowser())
    playwrights = iter([first, second])
    context = make_context({}, first, monkeypatch)
    monkeypatch.setattr(
        environment, "sync_playwright", lambda: FakeSyncPlaywright(next(playwrights))
    )

    environment.before_all(context)
    environment.before_all(context)

    assert first.stopped is True
    assert first.browser.closed is True
    assert context.browser is second.browser


def test_before_all_launch_failure_stops_playwright(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())

    def broken_launch(**kwargs: Any) -> FakeBrowser:
        raise PlaywrightError("browser binary missing")

    playwright.chromium = FakeBrowserType(playwright.browser)
    playwright.chromium.launch = broken_launch  # type: ignore[method-assign]
    context = make_context({}, playwright, monkeypatch)

    with pytest.raises(PlaywrightError, match="browser binary missing"):
        environment.before_all(context)

    assert playwright.stopped is True


def test_new_browser_context_requires_wiring() -> None:
    context = SimpleNamespace()
    with pytest.raises(RuntimeError, match="before_all"):
        environment.new_browser_context(context)


def test_timeout_zero_is_applied_not_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"timeout": "0"}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    # timeout=0 must reach Playwright (0 disables the timeout there) —
    # silently skipping the call would fall back to the 30s default.
    assert playwright.browser.contexts[0].timeout == 0.0


def test_new_browser_context_survives_already_closed_old(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    context.browser_context.close()  # closed by user code behind the lib's back
    environment.new_browser_context(context)  # must not raise

    assert len(playwright.browser.contexts) == 2


def test_after_scenario_survives_already_closed_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    context.browser_context.close()
    environment.after_scenario(context, make_scenario(status=Status.failed))


def test_context_level_request_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    request = SimpleNamespace(url="http://x/api", method="GET")
    playwright.browser.contexts[0]._emit("request", request)

    assert context.bp_requests == [request]


def test_artifact_path_slug_is_capped(tmp_path: Path) -> None:
    scenario = SimpleNamespace(name="x" * 500)
    path = environment._artifact_path(scenario, str(tmp_path), ".png")
    assert len(path.name) < 120


def test_handle_video_missing_file_does_not_crash(tmp_path: Path) -> None:
    video = SimpleNamespace(path=lambda: str(tmp_path / "gone.webm"))
    context = SimpleNamespace()
    scenario = SimpleNamespace(name="s", status=Status.failed)
    config = environment.BrowserConfig(video_dir=str(tmp_path))

    environment._handle_video(video, context, scenario, config)

    assert not hasattr(context, "bp_video")


def test_after_all_survives_already_closed_browser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)

    context.browser.close()  # closed behind the lib's back
    environment.after_all(context)  # must not raise

    assert playwright.stopped is True  # driver is still released
    assert context.browser is None


def test_after_all_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)

    environment.after_all(context)
    environment.after_all(context)  # second call must not raise


def test_new_browser_context_closes_orphan_on_page_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    made: list[FakeBrowserContext] = []

    def broken_new_context(**kwargs: Any) -> FakeBrowserContext:
        ctx = FakeBrowserContext(**kwargs)

        def explode() -> FakePage:
            raise PlaywrightError("new_page exploded")

        ctx.new_page = explode  # type: ignore[method-assign]
        made.append(ctx)
        return ctx

    monkeypatch.setattr(playwright.browser, "new_context", broken_new_context)

    with pytest.raises(PlaywrightError, match="new_page exploded"):
        environment.new_browser_context(context)

    # the context that could not produce a page must not leak
    assert made[0].closed is True
    assert context.browser_context is None


def test_after_scenario_survives_unwritable_artifact_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # screenshots_dir exists as a *file* — _artifact_path mkdir raises OSError,
    # which must not mask the scenario result during teardown
    blocker = tmp_path / "shots"
    blocker.write_text("not a dir")
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({"screenshots_dir": str(blocker)}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    environment.after_scenario(context, make_scenario(status=Status.failed))

    assert playwright.browser.contexts[0].closed is True


def test_after_scenario_video_survives_page_closed_mid_scenario(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context(
        {"record_video": "true", "video_dir": str(tmp_path)}, playwright, monkeypatch
    )
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    raw_video = tmp_path / "raw-uuid.webm"
    raw_video.write_bytes(b"vid")
    context.page.closed = True  # page died mid-scenario
    context.page.video = SimpleNamespace(path=lambda: str(raw_video))

    environment.after_scenario(context, make_scenario(status=Status.failed))

    assert Path(context.bp_video).exists()
    assert context.bp_video.parent == tmp_path
    assert not raw_video.exists()  # moved, not left as a stray uuid file


def test_new_browser_context_survives_locked_old_video(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context(
        {"record_video": "true", "video_dir": str(tmp_path)}, playwright, monkeypatch
    )
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    raw_video = tmp_path / "old.webm"
    raw_video.write_bytes(b"vid")
    context.page.video = SimpleNamespace(path=lambda: str(raw_video))

    def locked_unlink(self: Path, **kwargs: object) -> None:
        raise PermissionError("file locked")

    monkeypatch.setattr(Path, "unlink", locked_unlink)
    # the old video can't be removed — that must not mask the step
    environment.new_browser_context(context)

    assert context.page is not None


def test_new_browser_context_tolerates_inherited_artifact_attrs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """behave Context: getattr walks the layer stack but delattr only removes
    from the current one — an inherited bp_screenshot must not break setup."""

    class LayeredContext:
        def __init__(self) -> None:
            object.__setattr__(self, "_current", {"config": SimpleNamespace(userdata={})})
            object.__setattr__(self, "_outer", {"bp_screenshot": "stale.png"})

        def __getattr__(self, name: str) -> Any:
            for layer in (self._current, self._outer):
                if name in layer:
                    return layer[name]
            raise AttributeError(name)

        def __setattr__(self, name: str, value: Any) -> None:
            if name.startswith("_") and name != "_current":
                object.__setattr__(self, name, value)
            else:
                self._current[name] = value

        def __delattr__(self, name: str) -> None:
            if name in self._current:
                del self._current[name]
            else:
                raise AttributeError(name)

    playwright = FakePlaywright(FakeBrowser())
    context = LayeredContext()
    monkeypatch.setattr(environment, "sync_playwright", lambda: FakeSyncPlaywright(playwright))

    environment.before_all(context)  # type: ignore[arg-type]
    environment.before_scenario(context, make_scenario())  # type: ignore[arg-type]

    assert context.page is not None


def test_request_listener_recreates_missing_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    playwright = FakePlaywright(FakeBrowser())
    context = make_context({}, playwright, monkeypatch)
    environment.before_all(context)
    environment.before_scenario(context, make_scenario())

    context.bp_requests = None  # damaged externally between steps
    request = SimpleNamespace(url="http://x/api", method="GET")
    playwright.browser.contexts[0]._emit("request", request)

    assert context.bp_requests == [request]

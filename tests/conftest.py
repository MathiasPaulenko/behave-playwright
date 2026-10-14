"""Shared fixtures: real Chromium browser + a local HTTP test server."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from typing import Any

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from behave_playwright import BrowserConfig, environment

INDEX_HTML = """<!doctype html>
<html>
<head><title>Test Site</title></head>
<body>
  <h1>Home</h1>
  <button id="btn" onclick="location.hash='clicked'">Sign in</button>
  <a href="/next" id="lnk">Next page</a>
  <label>Email <input id="email" type="text"></label>
  <input placeholder="Search" id="search">
  <label><input type="checkbox" id="cb"> Accept terms</label>
  <select id="sel" aria-label="Fruit">
    <option value="a">Apple</option>
    <option value="b">Banana</option>
  </select>
  <input type="file" id="file">
  <div id="secret" style="display:none">hidden text</div>
  <span class="dup">one</span><span class="dup">two</span>
  <p data-testid="greeting">hello from testid</p>
</body>
</html>
"""

NEXT_HTML = """<!doctype html>
<html><head><title>Next Page</title></head>
<body><h1>You landed</h1></body></html>
"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = NEXT_HTML if self.path.startswith("/next") else INDEX_HTML
        payload = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    pw = sync_playwright().start()
    yield pw
    pw.stop()


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Iterator[Browser]:
    browser = playwright_instance.chromium.launch()
    yield browser
    browser.close()


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(2_000)
    page.set_content(INDEX_HTML)
    yield page
    context.close()


@pytest.fixture
def context(page: Page) -> SimpleNamespace:
    return SimpleNamespace(page=page, bp_config=BrowserConfig())


@pytest.fixture
def env_context(browser: Browser, playwright_instance: Playwright) -> Iterator[SimpleNamespace]:
    """Fake behave Context wired the way the real hooks wire it."""
    ctx = SimpleNamespace(
        browser=browser,
        bp_config=BrowserConfig(),
        _bp_playwright=playwright_instance,
        attach=lambda *args: None,
        text=None,
        table=None,
    )
    environment.new_browser_context(ctx)
    yield ctx
    ctx.browser_context.close()

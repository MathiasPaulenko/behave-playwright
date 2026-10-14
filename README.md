# behave-playwright

[![PyPI](https://img.shields.io/pypi/v/behave-playwright)](https://pypi.org/project/behave-playwright/)
[![CI](https://github.com/MathiasPaulenko/behave-playwright/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-playwright/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

BDD web testing with [Behave](https://behave.readthedocs.io/) and [Playwright](https://playwright.dev/python/) — reusable Gherkin step definitions plus browser lifecycle hooks, so you write features, not boilerplate.

```gherkin
Feature: Login
  Scenario: Successful login
    Given I navigate to "/login"
    When I fill "Email" with "user@test.com"
    And I fill "Password" with "secret"
    And I click "Sign in"
    Then I should see "Welcome back"
```

## Quickstart

```bash
pip install behave-playwright
playwright install          # one-time browser download
behave-playwright init      # scaffold behave.ini + features/
behave
```

`init` creates (use `-d DIR` to pick the target, `--force` to overwrite):

```text
behave.ini
features/
├── environment.py                  # from behave_playwright.environment import *
├── steps/behave_playwright_steps.py  # import behave_playwright.steps
└── example.feature
```

Already have a behave project? Add the two imports yourself:

```python
# features/environment.py
from behave_playwright.environment import *  # noqa: F401,F403
```

```python
# features/steps/behave_playwright_steps.py
import behave_playwright.steps  # noqa: F401
```

That's it — one browser per run, fresh context + page per scenario, screenshot captured and attached on failure.

## The context

`context` (behave's) is wired automatically per scenario:

| Attribute | Contents |
|---|---|
| `context.page` | Playwright `Page` (or the active `Frame` after `I switch to ... iframe`) |
| `context.browser_context` | Playwright `BrowserContext` |
| `context.browser` | Shared Playwright `Browser` (one per run) |
| `context.bp_config` | Resolved `BrowserConfig` |
| `context.bp_requests` | All requests seen by the scenario's page(s) |
| `context.bp_console_errors` | `console.error` + uncaught page errors |
| `context.bp_downloads` | Files downloaded via download steps |
| `context.bp_screenshot` / `bp_trace` / `bp_video` | Artifact paths on failure |

## Custom hooks

The lifecycle hooks are plain functions — delegate when you need your own setup:

```python
# features/environment.py
from behave_playwright import environment as bp


def before_all(context):
    my_app.start()
    context.config.userdata.setdefault("base_url", "http://localhost:8000")
    bp.before_all(context)


def before_scenario(context, scenario):
    my_app.reset_db()
    bp.before_scenario(context, scenario)


def after_scenario(context, scenario):
    bp.after_scenario(context, scenario)


def after_all(context):
    bp.after_all(context)
    my_app.stop()
```

Steps register on import — `import behave_playwright.steps` in a step file, or `behave_playwright.steps.use_steps()` from `environment.py` to make it explicit.

## Element targeting

Steps take a plain string and resolve it the way Playwright recommends — accessible selectors first:

1. `get_by_role` (accessible name)
2. `get_by_label` / `get_by_placeholder` (form fields)
3. `get_by_text`
4. `get_by_test_id`
5. CSS selector

Force a strategy with a prefix:

| Prefix | Maps to |
|---|---|
| `css=#id .cls` | `page.locator()` |
| `xpath=//div` or `//div` | XPath |
| `text=Submit` | `get_by_text` |
| `testid=submit-btn` | `get_by_test_id` |
| `label=Email` | `get_by_label` |
| `placeholder=Search` | `get_by_placeholder` |
| `title=Logo` | `get_by_title` |
| `alt=Avatar` | `get_by_alt_text` |
| `role=button:Save` | `get_by_role("button", name="Save")` |

## Step catalog

**Navigation**

```gherkin
Given I navigate to "/login"        # aliases: I go to, I open — resolves against base_url
When I go back / forward
When I reload the page              # alias: I refresh the page
```

**Interaction**

```gherkin
When I click "Sign in"              # aliases: click on, double click, right click, hover
When I fill "Email" with "a@b.c"    # aliases: fill in ... with, I enter "x" in/into "Email"
When I type "hello" in "Search"     # per-key events (fill is instant)
When I fill the form:               # data table: columns | field | value |
  | field    | value   |
  | Email    | a@b.c   |
When I clear "Email"
When I select "Banana" from "Fruit" # by label; alias: in
When I check "Accept terms" / I uncheck "Accept terms"
When I press the "Enter" key        # or: I press "Enter" on/in "Search"
When I upload the file "data.csv" to "Upload"
When I scroll to "css=#footer"
When I drag "css=#src" to "css=#dst"
When I take a screenshot / I take a screenshot of "css=#modal"
```

**Assertions** (auto-retrying — Playwright `expect` under the hood)

```gherkin
Then I should see "Welcome back" / I should not see "Error"
Then the "css=.modal" element should be visible / hidden / enabled / disabled / checked / not checked
Then I should see the "css=.modal" element
Then the url should be "/dashboard" / the url should contain "dashboard"
Then the title should be "Home" / the title should contain "Hom"
Then I should see 3 "css=.item" elements
Then the "css=.banner" element should contain "Sale ends today"   # substring
Then the "css=.banner" element should have text "Sale: 50%"       # exact
Then the "css=.logo" element should have attribute "src" with value "/logo.png"
Then the "Email" field should have value "user@test.com"
Then the "session" cookie should exist / have value "abc123"
Then there should be no console errors / except "favicon"
Then the file "report.pdf" was downloaded
```

**Waits** — Playwright auto-waits everywhere; these exist for when an explicit wait is the honest expression of intent

```gherkin
When I wait for "css=.spinner" to be hidden   # also: to disappear / the "x" element
When I wait for text "Loaded"                 # also: for the text "Loaded"
When I wait for the page to load / I wait for navigation
When I wait for the network to be idle
When I wait 2 seconds                         # only wait_for_timeout in the lib
```

**Network** — interception patterns: glob (`**/api/*`, `*` within a segment, `**` across), bare path (`/api/x` → `**/api/x`), or `/regex/`. Intercept steps register routes — use them *before* navigation.

```gherkin
Given I intercept "/api/users" and return:     # docstring is required
  """[{"name": "Ada"}]"""                       # served as application/json
When I intercept "**/api/health" and respond with status 503:
  """backend is down"""                         # optional docstring body
When I intercept "**/analytics" and abort
Then a request was made to "**/api/login"       # waits up to `timeout` for it
Then a "POST" request was made to "**/api/login"
```

**Session** — device emulation, tracing, storage state (these recreate `browser_context` + `page`)

```gherkin
When I emulate device "iPhone 12"
When I enable tracing          # on failure → <traces_dir>/<scenario>.trace.zip (view: playwright show-trace)
Given I am logged in as "ada"  # loads auth/ada.json (convention)
When I save the storage state to "auth/ada.json"
Given I use the storage state "auth/ada.json"
```

**Tabs, frames, dialogs, downloads**

```gherkin
When I open a new tab with "/docs"
When I click "Help" in a new tab       # popup capture + switch
When I switch to tab 2                    # 1-based
When I close the current tab
When I switch to the "payment" iframe  # steps now act on the frame…
When I switch back to the main frame   # …until you switch back
When I accept the next dialog          # must precede the action that opens it
When I dismiss the next dialog / I answer the next dialog with "42"
When I click "Export" and download the file  # saved to downloads_dir
```

## Configuration

Via `behave -D key=value`, `behave.ini` `userdata`, or `BEHAVE_PW_*` env vars:

| Key | Env var | Default | Notes |
|---|---|---|---|
| `browser` | `BEHAVE_PW_BROWSER` | `chromium` | `chromium`, `firefox`, `webkit` |
| `headless` | `BEHAVE_PW_HEADLESS` | `true` | |
| `channel` | `BEHAVE_PW_CHANNEL` | — | e.g. `chrome`, `msedge` |
| `base_url` | `BEHAVE_PW_BASE_URL` | — | enables relative paths in `I navigate to` |
| `viewport` | `BEHAVE_PW_VIEWPORT` | `1280x720` | `WIDTHxHEIGHT` |
| `device` | `BEHAVE_PW_DEVICE` | — | Playwright device name, e.g. `iPhone 12` |
| `locale` | `BEHAVE_PW_LOCALE` | — | e.g. `es-ES` |
| `slow_mo` | `BEHAVE_PW_SLOW_MO` | `0` | ms between actions (debugging) |
| `timeout` | `BEHAVE_PW_TIMEOUT` | `30000` | default timeout in ms |
| `screenshots` | `BEHAVE_PW_SCREENSHOTS` | `true` | screenshot on scenario failure |
| `screenshots_dir` | `BEHAVE_PW_SCREENSHOTS_DIR` | `screenshots` | |
| `traces_dir` | `BEHAVE_PW_TRACES_DIR` | `traces` | where failure traces are saved |
| `record_video` | `BEHAVE_PW_RECORD_VIDEO` | `false` | record every scenario, keep `.webm` on failure |
| `video_dir` | `BEHAVE_PW_VIDEO_DIR` | `videos` | |
| `downloads_dir` | `BEHAVE_PW_DOWNLOADS_DIR` | `downloads` | where download steps save files |

```bash
behave -D browser=firefox -D headless=false -D base_url=http://localhost:8000
```

Keys can also be namespaced to avoid collisions with other `-D` values: `-D behave_playwright.browser=firefox` works too.

## Examples

- [`examples/saucedemo`](examples/saucedemo) — a complete project against the classic [saucedemo.com](https://www.saucedemo.com) test site: login, inventory, cart flow and network mocking, plus a custom step composed via `execute_steps`. `cd examples/saucedemo && behave` (needs internet).
- [`examples/playground`](examples/playground) — a self-contained testbed: local app + API covering **every** feature (forms, tabs, iframes, dialogs, downloads, storage state, device emulation, network, console errors, artifacts). `cd examples/playground && behave` — no internet needed.

## Custom steps and the page object

The bundled steps cover the common cases; write your own on top of `context.page`:

```python
@then("the cart badge shows {count:d} items")
def step_cart_badge(context, count):
    expect(context.page.locator(".cart-badge")).to_have_text(str(count))
```

If a step creates a page itself (custom popup handling, extra tabs), call `wire_page(context, page)` from `behave_playwright.environment` so it inherits timeouts and request/console captures.

Or compose bundled steps with `execute_steps`:

```python
@given("I am logged in")
def step_logged_in(context):
    context.execute_steps("""
        Given I navigate to "/"
        When I fill "Email" with "a@b.c"
        And I fill "Password" with "secret"
        And I click "Sign in"
        """)
```

## Philosophy

- **Auto-wait by default** — no `sleep`/`wait_for_timeout` except the explicit `I wait N seconds` step. If a step is flaky, the fix is a better locator, not a longer sleep.
- **Sync API only** — behave is synchronous; Playwright's sync API is the right fit.
- **Steps + hooks, not a runner** — behave stays the runner; this library removes the boilerplate.

## Development

```bash
pip install -e ".[dev]"
pytest          # unit + integration tests (real Chromium + local server)
ruff check      # lint
mypy            # type check
behave --dry-run  # validate step registration
```

## License

MIT

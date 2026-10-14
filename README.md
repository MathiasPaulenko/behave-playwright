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

`init` creates:

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

That's it — `context.page`, `context.browser_context` and `context.browser` are managed automatically (one browser per run, fresh context + page per scenario) and a screenshot is captured and attached on scenario failure.

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
Given I navigate to "/login"        # resolves against base_url
When I go back / forward
When I reload the page
```

**Interaction**

```gherkin
When I click "Sign in"              # also: double click, right click, hover
When I fill "Email" with "a@b.c"    # also: I enter "x" in "Email"
When I clear "Email"
When I select "Banana" from "Fruit"
When I check "Accept terms" / I uncheck "Accept terms"
When I press the "Enter" key        # or: I press "Enter" on "Search"
When I upload the file "data.csv" to "Upload"
```

**Assertions** (auto-retrying — Playwright `expect` under the hood)

```gherkin
Then I should see "Welcome back" / I should not see "Error"
Then the "css=.modal" element should be visible / hidden / enabled / disabled / checked
Then the url should be "/dashboard" / the url should contain "dashboard"
Then the title should be "Home" / the title should contain "Hom"
Then I should see 3 "css=.item" elements
Then the "css=.banner" element should contain "Sale ends today"
Then the "css=.logo" element should have attribute "src" with value "/logo.png"
Then the "Email" field should have value "user@test.com"
```

**Waits** — Playwright auto-waits everywhere; these exist for when an explicit wait is the honest expression of intent

```gherkin
When I wait for "css=.spinner" to be hidden
When I wait for text "Loaded"
When I wait for the page to load / I wait for the network to be idle
When I wait 2 seconds
```

**Network** — interception patterns: glob (`**/api/*`, `*` within a segment, `**` across), bare path (`/api/x` → `**/api/x`), or `/regex/`

```gherkin
When I intercept "/api/users" and return:
  """[{"name": "Ada"}]"""
When I intercept "**/api/health" and respond with status 503:
  """backend is down"""
When I intercept "**/analytics" and abort
Then a request was made to "**/api/login"
Then a "POST" request was made to "**/api/login"
```

**Session** — device emulation, tracing, storage state (these recreate `browser_context` + `page`)

```gherkin
When I emulate device "iPhone 12"
When I enable tracing          # on failure → <traces_dir>/<scenario>.trace.zip
Given I am logged in as "ada"  # loads auth/ada.json
When I save the storage state to "auth/ada.json"
Given I use the storage state "auth/ada.json"
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

```bash
behave -D browser=firefox -D headless=false -D base_url=http://localhost:8000
```

## Examples

[`examples/saucedemo`](examples/saucedemo) is a complete project against the classic [saucedemo.com](https://www.saucedemo.com) test site: login, inventory, cart flow and network mocking — all with bundled steps plus one custom step composed via `execute_steps`. `cd examples/saucedemo && behave` (needs internet).

## Custom steps and the page object

The bundled steps cover the common cases; write your own on top of `context.page`:

```python
@then("the cart badge shows {count:d} items")
def step_cart_badge(context, count):
    expect(context.page.locator(".cart-badge")).to_have_text(str(count))
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

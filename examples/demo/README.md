# Demo — behave-playwright

A self-contained example: the bundled `app/index.html` is a tiny login + todo
SPA. `features/environment.py` starts a local HTTP server on a free port and
points `base_url` at it — no internet needed, just `behave`.

## Run it

```bash
pip install behave-playwright
playwright install
cd examples/demo
behave
```

See the browser while it runs:

```bash
behave -D headless=false -D slow_mo=500
```

## What's inside

```text
app/index.html                  # the app under test (login → todo list)
behave.ini
features/
├── environment.py              # local app server + base_url + lifecycle hooks
├── steps/behave_playwright_steps.py  # registers the bundled steps
├── login.feature               # navigation, fill, click, text assertions
├── todos.feature               # check, element count/text assertions
└── network.feature             # intercept/mocking + request assertions
```

The app fetches `api/todos` on login. Under `file://` that fetch fails and the
app falls back to built-in items — which is exactly what `network.feature`
exploits: intercepting the request returns mocked todos instead.

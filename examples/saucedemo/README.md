# Example — behave-playwright against saucedemo.com

A real-world example: BDD end-to-end scenarios against the classic
[Swag Labs](https://www.saucedemo.com) test site, written entirely with the
bundled steps. Requires an internet connection.

## Run it

```bash
pip install behave-playwright
playwright install
cd examples/saucedemo
behave
```

See the browser while it runs:

```bash
behave -D headless=false -D slow_mo=500
```

Trigger the failure-artifacts demo (deliberate failure → screenshot in
`screenshots/`):

```bash
behave --tags=@wip
```

## What's inside

```text
behave.ini                      # base_url via [behave.userdata], @wip excluded
features/
├── environment.py              # behave_playwright lifecycle hooks
├── steps/
│   ├── behave_playwright_steps.py  # registers the bundled steps
│   └── custom_steps.py             # "I am logged in" via execute_steps
├── login.feature               # fill/click, url + text assertions
├── inventory.feature           # select, check, counts, cart flow
├── network.feature             # intercept/mocking + request assertions
└── failure.feature             # @wip: screenshot-on-failure demo
```

Credentials used (`standard_user` / `locked_out_user`, password
`secret_sauce`) are saucedemo's public test accounts.

## Point it at your own app

`base_url` is just config — override it instead of editing features:

```bash
behave -D base_url=http://localhost:8000
```

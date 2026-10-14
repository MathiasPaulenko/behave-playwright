# Contributing

Thanks for your interest in contributing. This guide covers local setup,
testing and the contribution workflow.

## Setup

```bash
git clone https://github.com/MathiasPaulenko/behave-playwright.git
cd behave-playwright
python -m venv .venv
source .venv/bin/activate    # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
playwright install chromium
pre-commit install
```

## Running checks

```bash
ruff check && ruff format --check   # lint + formatting
mypy                               # strict type checking
pytest                             # unit + integration tests (real Chromium)
```

## Running the examples

The examples double as end-to-end tests:

```bash
cd examples/playground && behave   # local app — offline, covers all steps
cd examples/saucedemo && behave    # real site — needs internet
```

## Conventions

- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `docs:` ...).
- **Type hints**: required — `mypy --strict` is enforced.
- **Step definitions**: prefer auto-waiting Playwright APIs (`expect`,
  `locator` methods). `wait_for_timeout`/`time.sleep` only where the step
  itself is an explicit wait.
- **New steps**: add a feature-level regression test using the test suite's
  `env_context`/`page` fixtures, plus a playground scenario in
  `examples/playground` when the step interacts with a real page.
- **Patterns**: register with `@step` when both Given and When make sense
  (setup-style steps), `@when` for actions, `@then` for assertions.

## Pull requests

1. Fork and create a feature branch.
2. Keep changes focused — one concern per PR.
3. Make sure `pytest`, `ruff` and `mypy` pass locally.
4. Update `CHANGELOG.md` under *Unreleased* and the README if the public
   API changed.
5. PRs run the same checks in CI across Python 3.11–3.13.

## Releasing (maintainer)

Publishing is automated through GitHub Actions + PyPI trusted publishing:

1. Bump `version` in `pyproject.toml` and rename the `Unreleased`
   CHANGELOG section to `0.x.y — YYYY-MM-DD`.
2. Push, then `git tag v0.x.y && git push --tags`.
3. `tag.yml` creates the GitHub Release, which triggers `release.yml` —
   the package is built and published to PyPI via OIDC (no tokens).

## Reporting bugs

Open an issue with a minimal reproduction — a small `.feature` file or a
code snippet, the behave-playwright/playwright versions and the expected
vs. actual behavior.

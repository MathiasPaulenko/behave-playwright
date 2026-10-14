# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Browser lifecycle hooks (`environment.py`): one browser per run, fresh context
  + page per scenario, screenshot captured and attached on failure.
- `BrowserConfig`: resolves `userdata` (`-D`/behave.ini), `BEHAVE_PW_*` env vars
  and defaults — browser, headless, channel, base_url, viewport, device, locale,
  slow_mo, timeout, screenshots.
- Bundled step definitions (`import behave_playwright.steps`): navigation,
  interaction, assertions and explicit waits, with smart element resolution
  (accessible selectors first, `css=`/`text=`/`testid=`/`role=`/`label=` prefixes
  supported).
- `behave-playwright init` CLI: scaffolds `behave.ini` + `features/`.

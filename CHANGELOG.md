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
- Playwright-exclusive steps: network interception (`I intercept ... and
  return/respond/abort`), request assertions (`a request was made to`),
  device emulation (`I emulate device`), tracing (`I enable tracing` →
  `.trace.zip` on failure), and storage state (`I use/save the storage state`,
  `I am logged in as`).
- More steps: form fill from data table, `I type`, scroll, drag & drop,
  manual screenshots, cookies + console-error + download assertions, tabs,
  iframes, dialogs, and downloads (`downloads/`).
- Optional video recording (`record_video`) — `.webm` kept on failure.
- `wire_page(context, page)` — public helper to wire custom pages with
  timeouts and request/console captures.

### Fixed

- `I press "<key>" on "<target>"` now resolves form fields too (not only
  clickable roles).
- `after_scenario` no longer crashes when a scenario fails inside an
  iframe — artifacts capture the real page.
- Switching tabs no longer duplicates request/console captures or loses
  the configured timeout on newly opened pages.
- Dialogs, downloads and tab-closing work from inside an iframe (they act
  on the real page).
- `I switch to the "x" iframe` from inside an iframe keeps the true main
  page for `I switch back to the main frame`.
- `I am logged in as "<user>"` rejects path traversal in the user name.
- `role=BUTTON` (uppercase) resolves correctly.
- `data:`/`about:`/`blob:` URLs are treated as absolute.
- `/api/` style patterns only become regexes when they contain metachars.
- `I fill the form:` reports a clear error on 1-column rows.
- Stale trace/artifact state and orphaned video files from mid-scenario
  context recreation are cleaned up.

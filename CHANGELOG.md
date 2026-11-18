# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-11-18

### Fixed

- Requests are captured at browser-context level, so requests fired by new
  tabs and popups (including their initial navigation) are recorded in
  `context.bp_requests`; console/pageerror capture attaches to popup pages.
- `I intercept ... and abort/return/respond` now registers routes on the
  browser context, so interceptions apply to every tab — not just the main page.
- `before_all` is idempotent (re-calling releases the previous browser and
  Playwright driver) and stops the driver if the browser launch fails.
- `after_all` tolerates externally-closed browsers/drivers and is idempotent.
- `new_browser_context` requires `before_all` wiring (actionable error instead
  of `AttributeError`), tolerates already-closed contexts, clears stale page
  state, and closes the new context if page creation fails.
- `after_scenario` tolerates already-closed contexts and artifact-dir
  filesystem errors, and `_handle_video` tolerates missing video files.
- `timeout = 0` is now honored as "no timeout" everywhere (context, page,
  `expect_page`, `expect_download`, request waits) instead of falling back
  to the default.
- Artifact filenames are capped at 80 chars of slug so long scenario names
  can't exceed filesystem path limits.
- `I navigate to` works while inside an iframe (Frame has no `.goto`).
- Absolute URLs are detected for any `scheme:` (mailto:, tel:, file:, ...),
  and `base_url` without a scheme is rejected at config time.
- `browser` config values tolerate surrounding whitespace.
- `resolve(..., kind)` validates its kind; empty `prefix=` values are
  rejected (an empty `text=` matched `<body>`); targets that aren't valid
  CSS no longer poison the whole resolution cascade.
- `I intercept` / `a request was made to` reject empty patterns and invalid
  regexes with clear errors; request matching compiles the pattern once.
- `I switch to the "x" iframe` prefers an exact frame-name match over a
  url-substring match, and recovers correctly when `context.page` is a
  stray Frame.
- `I wait N seconds` rejects invalid, negative and non-finite durations.
- `there should be no console errors except "re"` validates the regex.
- `I enable tracing` is idempotent on the same browser context.
- `I upload`, `I use the storage state` and `I save the storage state`
  expand `~` to the user home.
- Download destinations are sanitized to a bare filename so a hostile
  `suggested_filename` can't escape `downloads_dir`.
- Empty text/fragment assertions (`I should see ""`, url/title contains)
  are rejected instead of asserting vacuously.
- `init` returns a clean error when a scaffold path is blocked by a file.
- `behave-playwright` no longer records duplicate entries when switching
  between already-wired tabs.
- `I wait for the page to load` / `I wait for the network to be idle` wait
  on the real page while inside an iframe, matching the navigation steps.
- `after_scenario` clears `context.page`, `context.browser_context` and
  `context._bp_main_page` after teardown, so custom hooks see `None`
  instead of closed objects.
- Videos are still captured when the page was closed mid-scenario, and
  a locked leftover video can't abort `new_browser_context`.
- `new_browser_context` tolerates artifact attributes inherited from an
  outer behave context layer (their `delattr` raises `AttributeError`).
- The package ships `py.typed`, so downstream type checkers see the
  inline type annotations.

## [1.0.0] - 2026-10-14

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
- `I select "<x>" from "<field>"` matches option labels (visible text),
  not raw values.
- Steps that act at page level (navigate back/reload, intercept,
  screenshot, waits) keep working while inside an iframe.
- Empty element targets are rejected with a clear error.
- Config rejects negative `timeout`/`slow_mo` and non-positive viewports.
- `init -d <path>` fails cleanly when the target is an existing file.
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

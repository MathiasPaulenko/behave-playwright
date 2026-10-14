# Playground — every feature of behave-playwright

A self-contained testbed exercising the whole library against a bundled app
(`app/`) served on `http://127.0.0.1:8123` by `features/environment.py`. No
internet needed.

```bash
cd examples/playground
behave
```

Failure-artifact demo (screenshot + Playwright trace + video):

```bash
behave --tags=@wip -D record_video=true
```

| Feature file | Covers |
|---|---|
| `core.feature` | fill, type, form table, select, check, press, click/dbl/hover, scroll, drag, screenshots, all assertions, back/forward/reload, waits |
| `tabs_frames_dialogs.feature` | new tabs, popups, tab switching, iframes, alert/confirm/prompt |
| `files.feature` | upload, download + file assertion |
| `session.feature` | storage state save/use, `I am logged in as`, device emulation, cookies, console errors |
| `network.feature` | intercept return/status/abort, request assertions |
| `artifacts.feature` | `@wip`: deliberate failure → screenshot + `.trace.zip` + `.webm` |

Notes:

- `environment.py` shows the delegation pattern — a custom `before_all`
  starting the app server, then calling the library hooks.
- `auth/admin.json` is a static Playwright storage-state file (localStorage
  token for `http://127.0.0.1:8123`) used by `I am logged in as`.

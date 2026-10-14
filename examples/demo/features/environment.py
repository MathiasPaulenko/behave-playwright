"""Demo wiring: serve the bundled app over a local HTTP server.

Shows the delegation pattern: behave-playwright hooks are called from custom
hooks, so project-specific setup (here, the test server) can live alongside.
"""

import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from behave_playwright import environment as bp

APP_DIR = Path(__file__).resolve().parent.parent / "app"

_server: ThreadingHTTPServer | None = None


def before_all(context):
    """Start the local app server, then the browser."""
    global _server
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(APP_DIR))
    _server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    port = _server.server_address[1]
    context.config.userdata.setdefault("base_url", f"http://127.0.0.1:{port}")
    bp.before_all(context)


def before_scenario(context, scenario):
    bp.before_scenario(context, scenario)


def after_scenario(context, scenario):
    bp.after_scenario(context, scenario)


def after_all(context):
    bp.after_all(context)
    if _server is not None:
        _server.shutdown()

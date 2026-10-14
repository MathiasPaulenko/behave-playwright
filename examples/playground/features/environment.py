"""Wires a local test server (app/ + fake API) and the behave-playwright hooks."""

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from behave_playwright import environment as bp

APP_DIR = Path(__file__).resolve().parent.parent / "app"
PORT = 8123

_server: ThreadingHTTPServer | None = None


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/items"):
            return self._send_json(["Item one", "Item two", "Item three"])
        if self.path.startswith("/files/report.txt"):
            return self._send_file("report contents", "report.txt")
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/submit"):
            return self._send_json({"ok": True})
        self.send_error(404)

    def _send_json(self, data):
        payload = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, text: str, filename: str):
        payload = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


def before_all(context):
    global _server
    _server = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    context.config.userdata.setdefault("base_url", f"http://127.0.0.1:{PORT}")
    bp.before_all(context)


def before_scenario(context, scenario):
    bp.before_scenario(context, scenario)


def after_scenario(context, scenario):
    bp.after_scenario(context, scenario)


def after_all(context):
    bp.after_all(context)
    if _server is not None:
        _server.shutdown()

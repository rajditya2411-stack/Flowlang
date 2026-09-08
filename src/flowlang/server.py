"""FlowLang Playground Local HTTP Server.

Serves the browser playground UI and provides the /api/run endpoint for executing FlowLang code.
Built entirely on Python standard libraries (http.server, json, os, urllib).
"""

import http.server
import json
import os
import sys
import webbrowser
from typing import Optional
from flowlang.engine import execute


class PlaygroundRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles static files for playground and the /api/run API endpoint."""

    playground_dir: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "playground")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.playground_dir, **kwargs)

    def do_POST(self) -> None:
        """Handle FlowLang execution requests."""
        if self.path == "/api/run":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body) if body else {}
                code = data.get("code", "")
            except Exception as e:
                self._send_json({"error": {"message": f"Invalid JSON payload: {e}"}}, status=400)
                return

            result = execute(code)

            response_data = {
                "output": result.output,
                "value": result.value,
                "error": result.error,
                "formatted_error": result.formatted_error,
            }
            self._send_json(response_data, status=200)
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data: dict, status: int = 200) -> None:
        """Send JSON response with CORS and proper content type headers."""
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        """Quiet default logging unless needed."""
        pass


def run_server(port: int = 8500, open_browser: bool = True) -> None:
    """Launch the FlowLang Playground server with port fallback."""
    ports_to_try = [port, 8500, 8080, 8888, 5000] if port not in (8500, 8080, 8888, 5000) else [port, 8080, 8888, 5000]
    httpd = None
    active_port = port

    for p in ports_to_try:
        try:
            server_address = ("", p)
            httpd = http.server.ThreadingHTTPServer(server_address, PlaygroundRequestHandler)
            active_port = p
            break
        except Exception:
            continue

    if httpd is None:
        print("Error: Could not bind Playground server to any available port.", file=sys.stderr)
        sys.exit(1)

    url = f"http://localhost:{active_port}"
    print("=" * 60)
    print("  FLOWLANG PLAYGROUND")
    print(f"  Server running at: {url}")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping FlowLang Playground server. Goodbye!")
    finally:
        httpd.server_close()

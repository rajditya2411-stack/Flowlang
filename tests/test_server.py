"""Tests for FlowLang Playground HTTP Server & Execution API."""

import unittest
import sys
import os
import threading
import json
import urllib.request
import urllib.error
import http.server

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.server import PlaygroundRequestHandler


class TestPlaygroundServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start test HTTP server on an OS-assigned ephemeral port
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), PlaygroundRequestHandler)
        cls.port = cls.httpd.server_port
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_get_index_html(self):
        req = urllib.request.Request(self.base_url + "/")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("FlowLang Playground", content)

    def test_get_style_css(self):
        req = urllib.request.Request(self.base_url + "/style.css")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("--bg-dark", content)

    def test_api_run_calculator_variables(self):
        code = "a = 4\nb = 4\nprint(a + b)"
        payload = json.dumps({"code": code}).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsNone(data["error"])
            self.assertEqual(data["output"], "8")

    def test_api_run_while_loop(self):
        code = "count = 0\nwhile count < 3:\n    count = count + 1\n    print(count)"
        payload = json.dumps({"code": code}).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsNone(data["error"])
            self.assertEqual(data["output"], "1\n2\n3")

    def test_api_run_syntax_error(self):
        code = "if x > 0\n    print(1)"
        payload = json.dumps({"code": code}).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsNotNone(data["error"])
            self.assertEqual(data["error"]["type"], "ParserError")
            self.assertIn("Expected ':' after condition", data["formatted_error"])


if __name__ == "__main__":
    unittest.main()

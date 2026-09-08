"""Tests for FlowLang Engine Pipeline (CORE 7)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute
from flowlang.runtime import Environment


class TestEngine(unittest.TestCase):
    def test_execute_success(self):
        res = execute("let a = 10; let b = 20; say(a + b); a * b")
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "30")
        self.assertEqual(res.value, 200)

    def test_execute_with_persistent_environment(self):
        env = Environment()
        res1 = execute("let x = 42", environment=env)
        self.assertIsNone(res1.error)

        res2 = execute("x + 8", environment=env)
        self.assertIsNone(res2.error)
        self.assertEqual(res2.value, 50)

    def test_execute_structured_lexer_error(self):
        res = execute('let s = "bad')
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "LexerError")
        self.assertEqual(res.error["line"], 1)
        self.assertEqual(res.error["column"], 9)
        self.assertIn("Unterminated string literal", res.formatted_error)

    def test_execute_structured_parser_error(self):
        res = execute("let = 5")
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "ParserError")
        self.assertEqual(res.error["line"], 1)
        self.assertEqual(res.error["column"], 5)

    def test_execute_structured_runtime_error(self):
        res = execute("10 / 0")
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "RuntimeError")
        self.assertIn("Division by zero", res.error["message"])


if __name__ == "__main__":
    unittest.main()

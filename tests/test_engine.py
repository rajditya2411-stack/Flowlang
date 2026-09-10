"""Tests for FlowLang Engine Pipeline (FlowLang V1 syntax)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute
from flowlang.runtime import Environment


class TestEngine(unittest.TestCase):
    def test_execute_success(self):
        res = execute("lit a = 10\nlit b = 20\nsay(a + b)\na * b")
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "30")
        self.assertEqual(res.value, 200)

    def test_execute_with_persistent_environment(self):
        env = Environment()
        res1 = execute("lit x = 42", environment=env)
        self.assertIsNone(res1.error)

        res2 = execute("x + 8", environment=env)
        self.assertIsNone(res2.error)
        self.assertEqual(res2.value, 50)

    def test_execute_structured_lexer_error(self):
        res = execute('lit s = "bad')
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "LexerError")
        self.assertEqual(res.error["line"], 1)

    def test_execute_structured_parser_error(self):
        res = execute("if x > 0 y = 5")
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "ParserError")
        self.assertEqual(res.error["line"], 1)

    def test_execute_structured_runtime_error(self):
        res = execute("10 / 0")
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "RuntimeError")
        self.assertIn("Division by zero", res.error["message"])


if __name__ == "__main__":
    unittest.main()


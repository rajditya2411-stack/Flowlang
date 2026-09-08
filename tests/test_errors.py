"""Tests for FlowLang Error System (Python-style syntax)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.parser import Parser
from flowlang.interpreter import Interpreter
from flowlang.errors import LexerError, ParserError, FlowRuntimeError


def execute_flow(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens, source_code=source).parse()
    interpreter = Interpreter(source_code=source)
    return interpreter.interpret(program)


class TestErrorSystem(unittest.TestCase):
    def test_lexer_error_formatting(self):
        source = 'x = "unterminated'
        try:
            execute_flow(source)
            self.fail("Expected LexerError")
        except LexerError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 1)
            self.assertIn("FlowLang LexerError: Unterminated string literal", formatted)
            self.assertIn('1 | x = "unterminated', formatted)

    def test_parser_error_formatting(self):
        source = "if x > 0\n    y = 1"
        try:
            execute_flow(source)
            self.fail("Expected ParserError")
        except ParserError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 1)
            self.assertIn("FlowLang ParserError: Expected ':' after condition", formatted)
            self.assertIn("1 | if x > 0", formatted)

    def test_runtime_undefined_variable_formatting(self):
        source = "x = 10\nprint(username)"
        try:
            execute_flow(source)
            self.fail("Expected FlowRuntimeError")
        except FlowRuntimeError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 2)
            self.assertIn("FlowLang RuntimeError: Undefined variable 'username'", formatted)
            self.assertIn("2 | print(username)", formatted)

    def test_runtime_division_by_zero_formatting(self):
        source = "a = 10\nb = 0\nc = a / b"
        try:
            execute_flow(source)
            self.fail("Expected FlowRuntimeError")
        except FlowRuntimeError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 3)
            self.assertIn("Division by zero", formatted)
            self.assertIn("3 | c = a / b", formatted)


if __name__ == "__main__":
    unittest.main()

"""Tests for FlowLang Error System (CORE 6)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.parser import Parser
from flowlang.interpreter import Interpreter
from flowlang.errors import FlowLangError, LexerError, ParserError, FlowRuntimeError


def execute_flow(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens, source_code=source).parse()
    interpreter = Interpreter(source_code=source)
    return interpreter.interpret(program)


class TestErrorSystem(unittest.TestCase):
    def test_lexer_error_formatting(self):
        source = 'let x = "unterminated'
        try:
            execute_flow(source)
            self.fail("Expected LexerError")
        except LexerError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 1)
            self.assertEqual(err.column, 9)
            self.assertIn("FlowLang LexerError: Unterminated string literal", formatted)
            self.assertIn("at line 1, column 9", formatted)
            self.assertIn('1 | let x = "unterminated', formatted)
            self.assertIn("^", formatted)

    def test_parser_error_formatting(self):
        source = "let = 10"
        try:
            execute_flow(source)
            self.fail("Expected ParserError")
        except ParserError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 1)
            self.assertEqual(err.column, 5)
            self.assertIn("FlowLang ParserError: Expected variable name after 'let'", formatted)
            self.assertIn("at line 1, column 5", formatted)
            self.assertIn("1 | let = 10", formatted)
            self.assertIn("^", formatted)

    def test_runtime_undefined_variable_formatting(self):
        source = "let x = 10\nsay(username)"
        try:
            execute_flow(source)
            self.fail("Expected FlowRuntimeError")
        except FlowRuntimeError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 2)
            self.assertEqual(err.column, 5)
            self.assertIn("FlowLang RuntimeError: Undefined variable 'username'", formatted)
            self.assertIn("at line 2, column 5", formatted)
            self.assertIn("2 | say(username)", formatted)
            self.assertIn("^", formatted)

    def test_runtime_division_by_zero_formatting(self):
        source = "let a = 10\nlet b = 0\nlet c = a / b"
        try:
            execute_flow(source)
            self.fail("Expected FlowRuntimeError")
        except FlowRuntimeError as err:
            formatted = err.format_error(source)
            self.assertEqual(err.line, 3)
            self.assertIn("Division by zero", formatted)
            self.assertIn("3 | let c = a / b", formatted)


if __name__ == "__main__":
    unittest.main()

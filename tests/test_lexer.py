"""Tests for FlowLang Lexer (Python-style syntax)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.tokens import TokenType
from flowlang.errors import LexerError


class TestLexer(unittest.TestCase):
    def test_variable_assignment_int(self):
        source = "x = 10"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.NUMBER,
            TokenType.NEWLINE,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)
        self.assertEqual(tokens[0].value, "x")
        self.assertEqual(tokens[2].value, 10)

    def test_variable_assignment_string(self):
        source = 'name = "Raj"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.STRING,
            TokenType.NEWLINE,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)
        self.assertEqual(tokens[2].value, "Raj")

    def test_arithmetic_expression(self):
        source = "x + 10 * 2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected = [
            (TokenType.IDENTIFIER, "x"),
            (TokenType.PLUS, "+"),
            (TokenType.NUMBER, 10),
            (TokenType.STAR, "*"),
            (TokenType.NUMBER, 2),
            (TokenType.NEWLINE, "\n"),
            (TokenType.EOF, None),
        ]
        self.assertEqual([(t.type, t.value) for t in tokens], expected)

    def test_indentation_and_dedentation(self):
        source = "if x >= 10:\n    y = 20\nelse:\n    y = 30"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        self.assertIn(TokenType.IF, types)
        self.assertIn(TokenType.COLON, types)
        self.assertIn(TokenType.INDENT, types)
        self.assertIn(TokenType.DEDENT, types)
        self.assertIn(TokenType.ELSE, types)

    def test_decimal_numbers(self):
        source = "3.14 + 0.05"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].value, 3.14)
        self.assertEqual(tokens[2].value, 0.05)

    def test_boolean_and_none_literals(self):
        source = "True False None"
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].type, TokenType.TRUE)
        self.assertEqual(tokens[0].value, True)
        self.assertEqual(tokens[1].type, TokenType.FALSE)
        self.assertEqual(tokens[1].value, False)
        self.assertEqual(tokens[2].type, TokenType.NONE)
        self.assertIsNone(tokens[2].value)

    def test_logical_keywords(self):
        source = "and or not"
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].type, TokenType.AND)
        self.assertEqual(tokens[1].type, TokenType.OR)
        self.assertEqual(tokens[2].type, TokenType.NOT)

    def test_comments(self):
        source = "a = 5 # this is a comment\nb = 10"
        tokens = Lexer(source).tokenize()
        values = [t.value for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertEqual(values, ["a", "=", 5, "b", "=", 10])

    def test_source_location_tracking(self):
        source = "x = 10\ny = 20"
        tokens = Lexer(source).tokenize()

        tok_x = tokens[0]
        self.assertEqual(tok_x.value, "x")
        self.assertEqual(tok_x.line, 1)
        self.assertEqual(tok_x.column, 1)

        tok_y = [t for t in tokens if t.line == 2 and t.type == TokenType.IDENTIFIER][0]
        self.assertEqual(tok_y.value, "y")
        self.assertEqual(tok_y.line, 2)
        self.assertEqual(tok_y.column, 1)

    def test_unterminated_string_error(self):
        source = 'x = "unterminated'
        with self.assertRaises(LexerError) as ctx:
            Lexer(source).tokenize()
        err = ctx.exception
        self.assertIn("Unterminated string literal", str(err))
        self.assertEqual(err.line, 1)

    def test_unexpected_character_error(self):
        source = "x = @10"
        with self.assertRaises(LexerError) as ctx:
            Lexer(source).tokenize()
        err = ctx.exception
        self.assertIn("Unexpected character '@'", str(err))

    def test_string_escapes(self):
        source = r'"hello\nworld\t\"quoted\""'
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].value, 'hello\nworld\t"quoted"')


if __name__ == "__main__":
    unittest.main()

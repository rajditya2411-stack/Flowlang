"""Tests for FlowLang Lexer (CORE 1)."""

import unittest
import sys
import os

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.tokens import TokenType
from flowlang.errors import LexerError


class TestLexer(unittest.TestCase):
    def test_variable_declaration_int(self):
        source = "let x = 10"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.LET,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.NUMBER,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)
        self.assertEqual(tokens[1].value, "x")
        self.assertEqual(tokens[3].value, 10)

    def test_variable_declaration_string(self):
        source = 'let name = "Raj"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.LET,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.STRING,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)
        self.assertEqual(tokens[3].value, "Raj")

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
            (TokenType.EOF, None),
        ]
        self.assertEqual([(t.type, t.value) for t in tokens], expected)

    def test_if_condition_and_braces(self):
        source = "if x >= 10 {\n    let y = 20\n}"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        self.assertIn(TokenType.IF, types)
        self.assertIn(TokenType.GREATER_EQUAL, types)
        self.assertIn(TokenType.LBRACE, types)
        self.assertIn(TokenType.RBRACE, types)

    def test_decimal_numbers(self):
        source = "3.14 + 0.05"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].value, 3.14)
        self.assertEqual(tokens[2].value, 0.05)

    def test_boolean_literals(self):
        source = "true false"
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].type, TokenType.TRUE)
        self.assertEqual(tokens[0].value, True)
        self.assertEqual(tokens[1].type, TokenType.FALSE)
        self.assertEqual(tokens[1].value, False)

    def test_comparison_and_logical_operators(self):
        source = "== != < <= > >= !"
        tokens = Lexer(source).tokenize()
        expected = [
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.BANG,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected)

    def test_comments(self):
        source = "let a = 5 // this is a comment\nlet b = 10"
        tokens = Lexer(source).tokenize()
        values = [t.value for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertEqual(values, ["let", "a", "=", 5, "let", "b", "=", 10])

    def test_source_location_tracking(self):
        source = "let x = 10\nlet y = 20"
        tokens = Lexer(source).tokenize()

        # Token 'x' is at line 1, column 5
        tok_x = tokens[1]
        self.assertEqual(tok_x.value, "x")
        self.assertEqual(tok_x.line, 1)
        self.assertEqual(tok_x.column, 5)

        # Token 'let' on line 2
        tok_let2 = [t for t in tokens if t.line == 2 and t.type == TokenType.LET][0]
        self.assertEqual(tok_let2.line, 2)
        self.assertEqual(tok_let2.column, 1)

    def test_unterminated_string_error(self):
        source = 'let x = "unterminated'
        with self.assertRaises(LexerError) as ctx:
            Lexer(source).tokenize()
        err = ctx.exception
        self.assertIn("Unterminated string literal", str(err))
        self.assertEqual(err.line, 1)
        self.assertEqual(err.column, 9)

    def test_unexpected_character_error(self):
        source = "let x = @10"
        with self.assertRaises(LexerError) as ctx:
            Lexer(source).tokenize()
        err = ctx.exception
        self.assertIn("Unexpected character '@'", str(err))
        self.assertEqual(err.line, 1)
        self.assertEqual(err.column, 9)

    def test_malformed_number_error(self):
        source = "let x = 12.34.56"
        with self.assertRaises(LexerError) as ctx:
            Lexer(source).tokenize()
        err = ctx.exception
        self.assertIn("Malformed number", str(err))
        self.assertEqual(err.line, 1)
        self.assertEqual(err.column, 14)

    def test_string_escapes(self):
        source = r'"hello\nworld\t\"quoted\""'
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].value, 'hello\nworld\t"quoted"')


if __name__ == "__main__":
    unittest.main()

"""Tests for FlowLang Lexer (FlowLang V1 syntax)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.tokens import TokenType
from flowlang.errors import LexerError


class TestLexer(unittest.TestCase):
    def test_variable_declaration_lit(self):
        source = "lit x = 10"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.LIT,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.NUMBER,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)
        self.assertEqual(tokens[1].value, "x")
        self.assertEqual(tokens[3].value, 10)

    def test_variable_declaration_string(self):
        source = 'str name = "Raj"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.STR,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.STRING,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)
        self.assertEqual(tokens[3].value, "Raj")

    def test_character_literal(self):
        source = "char c = 'A'"
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].type, TokenType.CHAR_TYPE)
        self.assertEqual(tokens[1].value, "c")
        self.assertEqual(tokens[3].type, TokenType.CHAR)
        self.assertEqual(tokens[3].value, "A")

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

    def test_brace_blocks(self):
        source = "if x >= 10 {\n    lit y = 20\n} else {\n    lit y = 30\n}"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        self.assertIn(TokenType.IF, types)
        self.assertIn(TokenType.LBRACE, types)
        self.assertIn(TokenType.RBRACE, types)
        self.assertIn(TokenType.ELSE, types)

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

    def test_logical_keywords(self):
        source = "and or not"
        tokens = Lexer(source).tokenize()
        self.assertEqual(tokens[0].type, TokenType.AND)
        self.assertEqual(tokens[1].type, TokenType.OR)
        self.assertEqual(tokens[2].type, TokenType.NOT)

    def test_comments(self):
        source = "lit a = 5 # this is a comment\nlit b = 10 /* block */"
        tokens = Lexer(source).tokenize()
        values = [t.value for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertEqual(values, ["lit", "a", "=", 5, "lit", "b", "=", 10])

    def test_source_location_tracking(self):
        source = "lit x = 10\nlit y = 20"
        tokens = Lexer(source).tokenize()

        tok_x = tokens[1]
        self.assertEqual(tok_x.value, "x")
        self.assertEqual(tok_x.line, 1)

        tok_y = [t for t in tokens if t.line == 2 and t.type == TokenType.IDENTIFIER][0]
        self.assertEqual(tok_y.value, "y")
        self.assertEqual(tok_y.line, 2)

    def test_unterminated_string_error(self):
        source = 'lit x = "unterminated'
        with self.assertRaises(LexerError) as ctx:
            Lexer(source).tokenize()
        err = ctx.exception
        self.assertIn("Unterminated string literal", str(err))

    def test_unexpected_character_error(self):
        source = "lit x = @10"
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


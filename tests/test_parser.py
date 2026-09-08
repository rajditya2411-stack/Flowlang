"""Tests for FlowLang Parser & AST (Python-style syntax)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.parser import Parser
from flowlang.ast import (
    Program,
    ExpressionStatement,
    VariableDeclaration,
    BinaryOp,
    LogicalOp,
    UnaryOp,
    Grouping,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    NoneLiteral,
    Identifier,
    Assignment,
    Block,
    IfStatement,
    WhileStatement,
    CallExpression,
)
from flowlang.errors import ParserError


def parse_source(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens, source_code=source).parse()


class TestParser(unittest.TestCase):
    def test_number_literal(self):
        program = parse_source("42")
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ExpressionStatement)
        self.assertIsInstance(stmt.expression, NumberLiteral)
        self.assertEqual(stmt.expression.value, 42)

    def test_operator_precedence(self):
        program = parse_source("2 + 3 * 4")
        stmt = program.statements[0]
        expr = stmt.expression
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "+")
        self.assertEqual(expr.left.value, 2)
        self.assertIsInstance(expr.right, BinaryOp)
        self.assertEqual(expr.right.operator, "*")
        self.assertEqual(expr.right.left.value, 3)
        self.assertEqual(expr.right.right.value, 4)

    def test_parenthesized_grouping(self):
        program = parse_source("(2 + 3) * 4")
        stmt = program.statements[0]
        expr = stmt.expression
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "*")
        self.assertIsInstance(expr.left, Grouping)
        self.assertIsInstance(expr.left.expression, BinaryOp)
        self.assertEqual(expr.left.expression.operator, "+")
        self.assertEqual(expr.right.value, 4)

    def test_logical_operators(self):
        program = parse_source("x > 0 and y < 10 or z == 5")
        expr = program.statements[0].expression
        self.assertIsInstance(expr, LogicalOp)
        self.assertEqual(expr.operator, "or")
        self.assertIsInstance(expr.left, LogicalOp)
        self.assertEqual(expr.left.operator, "and")

    def test_assignment(self):
        program = parse_source("x = 50")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ExpressionStatement)
        self.assertIsInstance(stmt.expression, Assignment)
        self.assertEqual(stmt.expression.name, "x")
        self.assertEqual(stmt.expression.value.value, 50)

    def test_call_expression(self):
        program = parse_source("print(x, 10)")
        expr = program.statements[0].expression
        self.assertIsInstance(expr, CallExpression)
        self.assertEqual(expr.callee.name, "print")
        self.assertEqual(len(expr.arguments), 2)
        self.assertEqual(expr.arguments[0].name, "x")
        self.assertEqual(expr.arguments[1].value, 10)

    def test_if_elif_else_statement(self):
        source = """
if x > 0:
    y = 1
elif x == 0:
    y = 0
else:
    y = -1
"""
        program = parse_source(source)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, IfStatement)
        self.assertEqual(stmt.condition.operator, ">")
        self.assertIsInstance(stmt.then_branch, Block)
        self.assertIsInstance(stmt.else_branch, IfStatement)
        self.assertIsInstance(stmt.else_branch.else_branch, Block)

    def test_while_statement(self):
        source = """
while x < 10:
    x = x + 1
"""
        program = parse_source(source)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, WhileStatement)
        self.assertEqual(stmt.condition.operator, "<")
        self.assertIsInstance(stmt.body, Block)

    def test_missing_colon_error(self):
        with self.assertRaises(ParserError) as ctx:
            parse_source("if x > 0\n    y = 1")
        self.assertIn("Expected ':'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

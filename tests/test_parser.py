"""Tests for FlowLang Parser & AST (CORE 2 & CORE 3)."""

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
    UnaryOp,
    Grouping,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
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
        # 2 + 3 * 4 should be 2 + (3 * 4)
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
        # (2 + 3) * 4 should be ((2 + 3)) * 4
        program = parse_source("(2 + 3) * 4")
        stmt = program.statements[0]
        expr = stmt.expression
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "*")
        self.assertIsInstance(expr.left, Grouping)
        self.assertIsInstance(expr.left.expression, BinaryOp)
        self.assertEqual(expr.left.expression.operator, "+")
        self.assertEqual(expr.right.value, 4)

    def test_left_associativity(self):
        # 10 - 5 - 2 should be (10 - 5) - 2
        program = parse_source("10 - 5 - 2")
        expr = program.statements[0].expression
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "-")
        self.assertEqual(expr.right.value, 2)
        self.assertIsInstance(expr.left, BinaryOp)
        self.assertEqual(expr.left.operator, "-")
        self.assertEqual(expr.left.left.value, 10)
        self.assertEqual(expr.left.right.value, 5)

    def test_unary_operator(self):
        program = parse_source("-5")
        expr = program.statements[0].expression
        self.assertIsInstance(expr, UnaryOp)
        self.assertEqual(expr.operator, "-")
        self.assertEqual(expr.operand.value, 5)

        program2 = parse_source("!true")
        expr2 = program2.statements[0].expression
        self.assertIsInstance(expr2, UnaryOp)
        self.assertEqual(expr2.operator, "!")
        self.assertEqual(expr2.operand.value, True)

    def test_comparisons(self):
        program = parse_source("x >= 10")
        expr = program.statements[0].expression
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, ">=")
        self.assertEqual(expr.left.name, "x")
        self.assertEqual(expr.right.value, 10)

    def test_variable_declaration(self):
        program = parse_source("let x = 10 + 20")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, VariableDeclaration)
        self.assertEqual(stmt.name, "x")
        self.assertIsInstance(stmt.initializer, BinaryOp)

    def test_assignment(self):
        program = parse_source("x = 50")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ExpressionStatement)
        self.assertIsInstance(stmt.expression, Assignment)
        self.assertEqual(stmt.expression.name, "x")
        self.assertEqual(stmt.expression.value.value, 50)

    def test_call_expression(self):
        program = parse_source("say(x, 10)")
        expr = program.statements[0].expression
        self.assertIsInstance(expr, CallExpression)
        self.assertEqual(expr.callee.name, "say")
        self.assertEqual(len(expr.arguments), 2)
        self.assertEqual(expr.arguments[0].name, "x")
        self.assertEqual(expr.arguments[1].value, 10)

    def test_if_else_statement(self):
        source = """
        if x > 0 {
            y = 1
        } else {
            y = 2
        }
        """
        program = parse_source(source)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, IfStatement)
        self.assertEqual(stmt.condition.operator, ">")
        self.assertIsInstance(stmt.then_branch, Block)
        self.assertIsInstance(stmt.else_branch, Block)

    def test_while_statement(self):
        source = """
        while x < 10 {
            x = x + 1
        }
        """
        program = parse_source(source)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, WhileStatement)
        self.assertEqual(stmt.condition.operator, "<")
        self.assertIsInstance(stmt.body, Block)

    # ---------------- Error cases ----------------

    def test_missing_closing_parenthesis(self):
        with self.assertRaises(ParserError) as ctx:
            parse_source("(2 + 3")
        self.assertIn("Expected ')'", str(ctx.exception))

    def test_invalid_assignment_target(self):
        with self.assertRaises(ParserError) as ctx:
            parse_source("10 = 20")
        self.assertIn("Invalid assignment target", str(ctx.exception))

    def test_missing_variable_name(self):
        with self.assertRaises(ParserError) as ctx:
            parse_source("let = 10")
        self.assertIn("Expected variable name after 'let'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

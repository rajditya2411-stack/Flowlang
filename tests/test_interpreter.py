"""Tests for FlowLang Interpreter & Runtime (Python-style syntax)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.lexer import Lexer
from flowlang.parser import Parser
from flowlang.interpreter import Interpreter
from flowlang.errors import FlowRuntimeError


def run_code(source: str, output_collector: list = None):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens, source_code=source).parse()
    output_fn = output_collector.append if output_collector is not None else None
    interpreter = Interpreter(output_handler=output_fn, source_code=source)
    return interpreter.interpret(program)


class TestInterpreter(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(run_code("2 + 3"), 5)
        self.assertEqual(run_code("10 * 5"), 50)
        self.assertEqual(run_code("(2 + 3) * 4"), 20)
        self.assertEqual(run_code("2 + 3 * 4"), 14)
        self.assertEqual(run_code("10 - 4 - 2"), 4)
        self.assertEqual(run_code("20 / 4"), 5)
        self.assertEqual(run_code("7 % 3"), 1)

    def test_calculator_variables(self):
        # Specific user requirement: a = 4; b = 4; a + b -> 8
        source = """
a = 4
b = 4
a + b
"""
        self.assertEqual(run_code(source), 8)

    def test_float_arithmetic(self):
        self.assertAlmostEqual(run_code("2.5 + 1.25"), 3.75)

    def test_string_concatenation(self):
        self.assertEqual(run_code('"Hello, " + "FlowLang!"'), "Hello, FlowLang!")

    def test_unary_operations(self):
        self.assertEqual(run_code("-42"), -42)
        self.assertEqual(run_code("not True"), False)
        self.assertEqual(run_code("not False"), True)

    def test_logical_operators_and_or(self):
        self.assertEqual(run_code("True and False"), False)
        self.assertEqual(run_code("True or False"), True)
        self.assertEqual(run_code("10 > 5 and 2 < 4"), True)

    def test_comparisons(self):
        self.assertEqual(run_code("10 > 5"), True)
        self.assertEqual(run_code("10 < 5"), False)
        self.assertEqual(run_code("5 >= 5"), True)
        self.assertEqual(run_code("5 <= 4"), False)
        self.assertEqual(run_code("10 == 10"), True)
        self.assertEqual(run_code("10 != 5"), True)

    def test_variables_and_reassignment(self):
        source = """
x = 10
y = 20
x = x + y
x
"""
        self.assertEqual(run_code(source), 30)

    def test_if_elif_else(self):
        source1 = """
x = 10
res = 0
if x > 5:
    res = 100
else:
    res = 200
res
"""
        self.assertEqual(run_code(source1), 100)

        source2 = """
x = 0
res = 0
if x > 0:
    res = 1
elif x == 0:
    res = 42
else:
    res = -1
res
"""
        self.assertEqual(run_code(source2), 42)

    def test_while_loop(self):
        source = """
count = 0
while count < 5:
    count = count + 1
count
"""
        self.assertEqual(run_code(source), 5)

    def test_builtin_print(self):
        output = []
        source = """
name = "FlowLang"
print("Hello", name)
print(10 + 20)
"""
        run_code(source, output_collector=output)
        self.assertEqual(output, ["Hello FlowLang", "30"])

    def test_division_by_zero(self):
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code("10 / 0")
        self.assertIn("Division by zero", str(ctx.exception))

    def test_type_mismatch_in_addition(self):
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code('10 + "hello"')
        self.assertIn("Operands for '+' must both be numbers or both be strings", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

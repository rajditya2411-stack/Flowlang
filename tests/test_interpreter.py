"""Tests for FlowLang Interpreter & Runtime (CORE 4 & CORE 5)."""

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

    def test_float_arithmetic(self):
        self.assertAlmostEqual(run_code("2.5 + 1.25"), 3.75)

    def test_string_concatenation(self):
        self.assertEqual(run_code('"Hello, " + "FlowLang!"'), "Hello, FlowLang!")

    def test_unary_operations(self):
        self.assertEqual(run_code("-42"), -42)
        self.assertEqual(run_code("!true"), False)
        self.assertEqual(run_code("!false"), True)

    def test_comparisons(self):
        self.assertEqual(run_code("10 > 5"), True)
        self.assertEqual(run_code("10 < 5"), False)
        self.assertEqual(run_code("5 >= 5"), True)
        self.assertEqual(run_code("5 <= 4"), False)
        self.assertEqual(run_code("10 == 10"), True)
        self.assertEqual(run_code("10 != 5"), True)
        self.assertEqual(run_code('"abc" == "abc"'), True)
        self.assertEqual(run_code('"abc" == "xyz"'), False)

    def test_variables(self):
        source = """
        let x = 10
        let y = 20
        x + y
        """
        self.assertEqual(run_code(source), 30)

    def test_variable_reassignment(self):
        source = """
        let x = 10
        x = 25
        x
        """
        self.assertEqual(run_code(source), 25)

    def test_scoping_and_blocks(self):
        source = """
        let x = 10
        {
            let y = 20
            x = x + y
        }
        x
        """
        self.assertEqual(run_code(source), 30)

    def test_variable_not_accessible_outside_scope(self):
        source = """
        {
            let inner = 123
        }
        inner
        """
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code(source)
        self.assertIn("Undefined variable 'inner'", str(ctx.exception))

    def test_if_else(self):
        source1 = """
        let x = 10
        let res = 0
        if x > 5 {
            res = 100
        } else {
            res = 200
        }
        res
        """
        self.assertEqual(run_code(source1), 100)

        source2 = """
        let x = 2
        let res = 0
        if x > 5 {
            res = 100
        } else {
            res = 200
        }
        res
        """
        self.assertEqual(run_code(source2), 200)

    def test_while_loop(self):
        source = """
        let count = 0
        while count < 5 {
            count = count + 1
        }
        count
        """
        self.assertEqual(run_code(source), 5)

    def test_builtin_say(self):
        output = []
        source = """
        let name = "FlowLang"
        say("Hello", name)
        say(10 + 20)
        """
        run_code(source, output_collector=output)
        self.assertEqual(output, ["Hello FlowLang", "30"])

    # ---------------- Error cases ----------------

    def test_division_by_zero(self):
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code("10 / 0")
        self.assertIn("Division by zero", str(ctx.exception))

    def test_modulo_by_zero(self):
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code("10 % 0")
        self.assertIn("Modulo by zero", str(ctx.exception))

    def test_type_mismatch_in_addition(self):
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code('10 + "hello"')
        self.assertIn("Operands for '+' must both be numbers or both be strings", str(ctx.exception))

    def test_call_non_function(self):
        with self.assertRaises(FlowRuntimeError) as ctx:
            run_code("let a = 10; a(1, 2)")
        self.assertIn("'a' is not callable", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

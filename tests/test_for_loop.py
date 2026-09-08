"""Tests for FlowLang 'for' loops, augmented assignments, and built-ins."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute
from flowlang.errors import FlowRuntimeError


class TestForLoopAndBuiltins(unittest.TestCase):
    def test_for_range_single_arg(self):
        source = """
output = ""
for i in range(4):
    print("i:", i)
"""
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "i: 0\ni: 1\ni: 2\ni: 3")

    def test_for_range_start_stop(self):
        source = """
for i in range(2, 5):
    print(i)
"""
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "2\n3\n4")

    def test_for_range_step_countdown(self):
        source = """
for i in range(5, 0, -1):
    print(i)
"""
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "5\n4\n3\n2\n1")

    def test_for_string_iteration(self):
        source = """
for c in "Flow":
    print(c)
"""
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "F\nl\no\nw")

    def test_augmented_assignment_in_while_countdown(self):
        # The user's exact countdown scenario
        source = """
i = 5
while i > 0:
    print("Countdown:", i)
    i -= 1
"""
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(
            res.output,
            "Countdown: 5\nCountdown: 4\nCountdown: 3\nCountdown: 2\nCountdown: 1"
        )

    def test_augmented_assignments(self):
        source = """
a = 10
a += 5
a -= 3
a *= 2
a /= 4
a
"""
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.value, 6)

    def test_builtins_len_abs_type_casts(self):
        source = """
print("len:", len("hello"))
print("abs:", abs(-42))
print("type_int:", type(10))
print("type_str:", type("abc"))
print("int_cast:", int("100") + 5)
print("float_cast:", float("3.5") + 1.5)
print("str_cast:", str(123) + "xyz")
print("bool_true:", bool(1))
print("bool_false:", bool(0))
"""
        res = execute(source)
        self.assertIsNone(res.error)
        expected = "\n".join([
            "len: 5",
            "abs: 42",
            "type_int: int",
            "type_str: str",
            "int_cast: 105",
            "float_cast: 5.0",
            "str_cast: 123xyz",
            "bool_true: True",
            "bool_false: False",
        ])
        self.assertEqual(res.output, expected)

    def test_non_iterable_error(self):
        source = """
for x in 123:
    print(x)
"""
        res = execute(source)
        self.assertIsNotNone(res.error)
        self.assertEqual(res.error["type"], "RuntimeError")
        self.assertIn("'int' object is not iterable", res.formatted_error)


if __name__ == "__main__":
    unittest.main()

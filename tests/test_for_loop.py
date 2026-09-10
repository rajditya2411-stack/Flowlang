"""Tests for FlowLang V1 'for' loops, while loops, and built-ins."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flowlang.engine import execute


class TestForLoopAndBuiltins(unittest.TestCase):
    def test_for_loop_counting_up(self):
        source = """
        for i in (0; i < 4; i = i + 1) {
            say("i:", i)
        }
        """
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "i: 0\ni: 1\ni: 2\ni: 3")

    def test_for_loop_start_stop(self):
        source = """
        for i in (2; i <= 4; i = i + 1) {
            say(i)
        }
        """
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "2\n3\n4")

    def test_for_loop_step_countdown(self):
        source = """
        for i in (5; i >= 1; i = i - 1) {
            say(i)
        }
        """
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "5\n4\n3\n2\n1")

    def test_for_loop_step_by_two(self):
        source = """
        for i in (1; i <= 5; i = i + 2) {
            say(i)
        }
        """
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "1\n3\n5")

    def test_while_countdown(self):
        source = """
        lit i = 5
        while i > 0 {
            say("Countdown:", i)
            i = i - 1
        }
        """
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(
            res.output,
            "Countdown: 5\nCountdown: 4\nCountdown: 3\nCountdown: 2\nCountdown: 1"
        )

    def test_do_while(self):
        source = """
        lit i = 0
        do {
            say("step:", i)
            i = i + 1
        } while i < 3
        """
        res = execute(source)
        self.assertIsNone(res.error)
        self.assertEqual(res.output, "step: 0\nstep: 1\nstep: 2")

    def test_builtins_type_casts(self):
        source = """
        say("int_cast:", int("100") + 5)
        say("flt_cast:", flt("3.5") + 1.5)
        say("str_cast:", str(123) + "xyz")
        say("bool_true:", bool("true"))
        say("bool_false:", bool("false"))
        say("pow:", pow_(2, 4))
        """
        res = execute(source)
        self.assertIsNone(res.error)
        expected = "\n".join([
            "int_cast: 105",
            "flt_cast: 5.0",
            "str_cast: 123xyz",
            "bool_true: true",
            "bool_false: false",
            "pow: 16",
        ])
        self.assertEqual(res.output, expected)


if __name__ == "__main__":
    unittest.main()

